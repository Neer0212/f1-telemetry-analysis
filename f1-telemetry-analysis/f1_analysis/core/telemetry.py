"""
Telemetry-level analysis utilities.

FastF1 exposes per-lap car telemetry (speed, throttle, brake, gear, RPM,
DRS) sampled at high frequency along the lap distance. This module
provides helpers to pull a single driver's telemetry for a lap and to
align two drivers' telemetry on a common distance axis for direct
comparison (essential for "where did driver A gain time on driver B"
style analysis).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd
from fastf1.core import Session


def get_driver_telemetry(
    session: Session,
    driver: str,
    lap_number: Optional[int] = None,
) -> pd.DataFrame:
    """
    Get telemetry for one driver's lap, merged with car position data.

    Parameters
    ----------
    session:
        A loaded FastF1 session (see ``load_session``).
    driver:
        Driver identifier as used by FastF1 -- typically a three-letter
        code (e.g. ``"VER"``, ``"HAM"``) or car number string.
    lap_number:
        Which lap to pull telemetry for. If ``None``, the driver's
        fastest lap in the session is used.

    Returns
    -------
    pandas.DataFrame
        Telemetry samples with distance, speed, throttle, brake, gear,
        RPM, and DRS columns, plus a ``Time`` and ``Distance`` axis
        suitable for plotting.
    """
    driver_laps = session.laps.pick_drivers(driver)
    if driver_laps.empty:
        raise ValueError(f"No laps found for driver '{driver}' in this session.")

    if lap_number is None:
        lap = driver_laps.pick_fastest()
    else:
        matching = driver_laps[driver_laps["LapNumber"] == lap_number]
        if matching.empty:
            raise ValueError(f"Driver '{driver}' has no lap numbered {lap_number}.")
        lap = matching.iloc[0]

    telemetry = lap.get_telemetry()
    telemetry = telemetry.add_distance()
    return telemetry


def get_fastest_lap_telemetry(session: Session, driver: str) -> pd.DataFrame:
    """
    Convenience wrapper: telemetry for a driver's single fastest lap.

    Equivalent to ``get_driver_telemetry(session, driver, lap_number=None)``.
    """
    return get_driver_telemetry(session, driver, lap_number=None)


@dataclass
class TelemetryComparison:
    """
    Container for an aligned two-driver telemetry comparison.

    Attributes
    ----------
    driver_a, driver_b:
        Driver identifiers as passed in.
    telemetry_a, telemetry_b:
        Each driver's raw telemetry (with a ``Distance`` column added).
    delta_time:
        DataFrame with columns ``Distance`` and ``Delta`` -- the time gap
        between driver_a and driver_b at each point on track, in seconds.
        Positive values mean driver_a is behind (slower) at that point.
    """

    driver_a: str
    driver_b: str
    telemetry_a: pd.DataFrame
    telemetry_b: pd.DataFrame
    delta_time: pd.DataFrame


def compare_driver_telemetry(
    session: Session,
    driver_a: str,
    driver_b: str,
    *,
    lap_a: Optional[int] = None,
    lap_b: Optional[int] = None,
) -> TelemetryComparison:
    """
    Align two drivers' lap telemetry on distance and compute the time delta.

    This is the core building block behind speed-trace overlays and
    "minisector" delta plots: given two laps, figure out who is ahead/
    behind by how much at every point on the circuit.

    Parameters
    ----------
    session:
        A loaded FastF1 session.
    driver_a, driver_b:
        Driver identifiers to compare.
    lap_a, lap_b:
        Specific lap numbers for each driver. Defaults to each driver's
        fastest lap in the session, which is the most common comparison
        (e.g. qualifying fastest-lap battles).

    Returns
    -------
    TelemetryComparison
        Aligned telemetry for both drivers plus the computed delta-time
        trace along the lap distance.
    """
    from fastf1.utils import delta_time

    laps = session.laps
    lap_a_row = (
        laps.pick_drivers(driver_a).pick_fastest()
        if lap_a is None
        else laps.pick_drivers(driver_a)[laps.pick_drivers(driver_a)["LapNumber"] == lap_a].iloc[0]
    )
    lap_b_row = (
        laps.pick_drivers(driver_b).pick_fastest()
        if lap_b is None
        else laps.pick_drivers(driver_b)[laps.pick_drivers(driver_b)["LapNumber"] == lap_b].iloc[0]
    )

    telemetry_a = lap_a_row.get_telemetry().add_distance()
    telemetry_b = lap_b_row.get_telemetry().add_distance()

    delta, ref_tel, _ = delta_time(lap_a_row, lap_b_row)
    delta_df = pd.DataFrame({"Distance": ref_tel["Distance"], "Delta": delta})

    return TelemetryComparison(
        driver_a=driver_a,
        driver_b=driver_b,
        telemetry_a=telemetry_a,
        telemetry_b=telemetry_b,
        delta_time=delta_df,
    )


def corner_speed_summary(telemetry: pd.DataFrame, speed_threshold: float = 150.0) -> dict:
    """
    Quick summary stats split into "slow corner" vs "high speed" samples.

    A lightweight heuristic (not corner-detection) useful for quickly
    characterizing a lap: what fraction of the lap was spent below a
    speed threshold, and what was the minimum/average speed in that
    regime versus above it.

    Parameters
    ----------
    telemetry:
        A telemetry DataFrame as returned by :func:`get_driver_telemetry`.
    speed_threshold:
        Speed in km/h used to split "corner" vs "straight" samples.

    Returns
    -------
    dict
        Keys: ``min_speed``, ``max_speed``, ``avg_speed_below_threshold``,
        ``avg_speed_above_threshold``, ``pct_time_below_threshold``.
    """
    speed = telemetry["Speed"]
    below = speed[speed < speed_threshold]
    above = speed[speed >= speed_threshold]

    return {
        "min_speed": float(speed.min()),
        "max_speed": float(speed.max()),
        "avg_speed_below_threshold": float(below.mean()) if not below.empty else float("nan"),
        "avg_speed_above_threshold": float(above.mean()) if not above.empty else float("nan"),
        "pct_time_below_threshold": float(len(below) / len(speed) * 100) if len(speed) else 0.0,
    }
