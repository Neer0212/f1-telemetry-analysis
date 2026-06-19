"""
Qualifying delta helpers.

Functions to compute minisector-by-minisector time deltas between
two drivers' laps and a small formatter for lap time strings.

This file provides:
- `compute_qualifying_delta(session, driver_a, driver_b, n_minisectors=25)`
- `get_lap_time_str(session, driver)`

These are used by the scripts/08_quali_delta.py plotting helper.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

from f1_analysis.core.telemetry import compare_driver_telemetry


def get_lap_time_str(session, driver: str) -> str:
    """Return a human-friendly lap time (e.g. '1:21.345') for a driver's fastest lap.

    If no lap is available, returns 'N/A'.
    """
    driver_laps = session.laps.pick_drivers(driver)
    if driver_laps.empty:
        return "N/A"

    try:
        lap = driver_laps.pick_fastest()
    except Exception:
        # fallback: pick min LapTime
        if driver_laps['LapTime'].isna().all():
            return "N/A"
        lap = driver_laps.loc[driver_laps['LapTime'].idxmin()]

    lt = lap['LapTime']
    if pd.isna(lt):
        return "N/A"

    total_seconds = lt.total_seconds()
    minutes = int(total_seconds // 60)
    seconds = total_seconds % 60
    return f"{minutes}:{seconds:06.3f}"


def compute_qualifying_delta(session, driver_a: str, driver_b: str, n_minisectors: int = 25) -> pd.DataFrame:
    """Compute minisector-level delta dataframe between two drivers.

    The returned DataFrame contains columns: ``MiniSector``, ``X``, ``Y``,
    ``Delta`` (seconds, positive = driver_a behind / slower), and
    ``Faster`` (the driver who is faster in that minisector).

    Parameters
    ----------
    session:
        Loaded FastF1 session.
    driver_a, driver_b:
        Driver identifiers (three-letter codes or car numbers).
    n_minisectors:
        Number of equal-length segments to split the lap into.
    """
    cmp = compare_driver_telemetry(session, driver_a, driver_b)
    delta_df = cmp.delta_time.copy()

    # Use the reference telemetry (telemetry_a) to get X/Y coordinates
    ref_tel = cmp.telemetry_a
    if ref_tel is None or ref_tel.empty:
        raise ValueError("Reference telemetry is empty; cannot compute minisectors.")

    max_dist = float(delta_df['Distance'].max())
    # Create equal-distance boundaries along the lap
    bounds = np.linspace(0.0, max_dist, n_minisectors + 1)

    minisectors = []
    for idx in range(n_minisectors):
        start = bounds[idx]
        end = bounds[idx + 1]
        mid = (start + end) / 2.0

        # Interpolate X/Y from reference telemetry at the midpoint distance
        x = float(np.interp(mid, ref_tel['Distance'], ref_tel['X']))
        y = float(np.interp(mid, ref_tel['Distance'], ref_tel['Y']))

        # Compute delta for the segment: mean delta within the distance window
        seg = delta_df[(delta_df['Distance'] >= start) & (delta_df['Distance'] <= end)]
        if not seg.empty:
            d = float(seg['Delta'].mean())
        else:
            # fallback: interpolate the delta at the midpoint
            d = float(np.interp(mid, delta_df['Distance'], delta_df['Delta']))

        # According to TelemetryComparison doc: positive => driver_a is behind
        faster = driver_b if d > 0 else driver_a

        minisectors.append({'MiniSector': idx + 1, 'X': x, 'Y': y, 'Delta': d, 'Faster': faster})

    return pd.DataFrame(minisectors)
