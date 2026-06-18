"""
Lap-level analysis utilities.

Helpers for cleaning, filtering, and summarizing lap time data returned
by ``Session.laps``. FastF1 returns lap times as ``pandas.Timedelta``,
which is precise but awkward to plot, so several helpers here convert
to plain seconds (float) for charting and statistics.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd


def laps_to_seconds(laps: pd.DataFrame, column: str = "LapTime") -> pd.Series:
    """
    Convert a Timedelta lap-time column to seconds as floats.

    Parameters
    ----------
    laps:
        A laps DataFrame (e.g. ``session.laps``).
    column:
        Name of the Timedelta column to convert. Defaults to ``"LapTime"``
        but also works for ``"Sector1Time"``, ``"Sector2Time"``, etc.

    Returns
    -------
    pandas.Series
        Lap times in seconds, with NaT entries converted to NaN.
    """
    return laps[column].dt.total_seconds()


def clean_lap_times(
    laps: pd.DataFrame,
    *,
    exclude_pit_laps: bool = True,
    exclude_inaccurate: bool = True,
    max_lap_time_seconds: Optional[float] = None,
) -> pd.DataFrame:
    """
    Filter a laps DataFrame down to "racing" laps suitable for pace analysis.

    Raw lap data includes in/out laps, safety car laps, and laps FastF1
    flags as not accurately timed. Including these skews pace comparisons
    and average lap time calculations, so this is usually the first step
    before any lap-time based analysis.

    Parameters
    ----------
    laps:
        A laps DataFrame (e.g. ``session.laps`` or a subset via
        ``session.laps.pick_drivers(...)``).
    exclude_pit_laps:
        Drop laps where the driver entered or exited the pits.
    exclude_inaccurate:
        Drop laps where FastF1's ``IsAccurate`` flag is False (laps with
        timing inconsistencies, e.g. due to safety cars or red flags).
    max_lap_time_seconds:
        Optional hard cap; laps slower than this are dropped. Useful for
        removing outliers (e.g. laps behind a safety car) when no other
        flag catches them.

    Returns
    -------
    pandas.DataFrame
        The filtered laps DataFrame (a copy, not a view).
    """
    clean = laps.copy()

    if clean.empty:
        return clean

    if exclude_pit_laps:
        clean = clean[clean["PitInTime"].isna() & clean["PitOutTime"].isna()]

    if exclude_inaccurate and "IsAccurate" in clean.columns:
        clean = clean[clean["IsAccurate"].astype(bool)]

    if clean.empty:
        return clean

    clean = clean[clean["LapTime"].notna()]

    if max_lap_time_seconds is not None:
        clean = clean[laps_to_seconds(clean) <= max_lap_time_seconds]

    return clean.reset_index(drop=True)


def fastest_laps_by_driver(laps: pd.DataFrame) -> pd.DataFrame:
    """
    Return each driver's single fastest lap from a laps DataFrame.

    Parameters
    ----------
    laps:
        A laps DataFrame, ideally already passed through
        :func:`clean_lap_times` so the result reflects genuine pace
        rather than an anomalous lap.

    Returns
    -------
    pandas.DataFrame
        One row per driver (``Driver`` column), sorted fastest to
        slowest, with a ``LapTimeSeconds`` column added for convenience.
    """
    result = laps.loc[laps.groupby("Driver")["LapTime"].idxmin()].copy()
    result["LapTimeSeconds"] = laps_to_seconds(result)
    return result.sort_values("LapTimeSeconds").reset_index(drop=True)


def race_pace_summary(laps: pd.DataFrame) -> pd.DataFrame:
    """
    Summarize each driver's race pace: mean, median, and std of lap time.

    Parameters
    ----------
    laps:
        A laps DataFrame, ideally pre-filtered with :func:`clean_lap_times`.

    Returns
    -------
    pandas.DataFrame
        One row per driver with ``MeanLapTime``, ``MedianLapTime``, and
        ``StdLapTime`` (all in seconds), sorted by mean lap time.
    """
    working = laps.copy()
    working["LapTimeSeconds"] = laps_to_seconds(working)

    summary = (
        working.groupby("Driver")["LapTimeSeconds"]
        .agg(MeanLapTime="mean", MedianLapTime="median", StdLapTime="std", Laps="count")
        .sort_values("MeanLapTime")
        .reset_index()
    )
    return summary


def stint_summary(laps: pd.DataFrame) -> pd.DataFrame:
    """
    Summarize tire stints (compound, length, average pace) per driver.

    Uses the ``Stint`` column FastF1 assigns to group consecutive laps on
    the same tire, which is the basis for strategy/degradation analysis.

    Parameters
    ----------
    laps:
        A laps DataFrame containing ``Driver``, ``Stint``, ``Compound``,
        and ``LapTime`` columns (typically the full, unfiltered race laps
        so stint boundaries -- including pit laps -- are correct).

    Returns
    -------
    pandas.DataFrame
        One row per driver/stint with compound, lap count, and the first
        and last lap numbers of the stint.
    """
    working = laps.copy()
    working["LapTimeSeconds"] = laps_to_seconds(working)

    summary = (
        working.groupby(["Driver", "Stint"])
        .agg(
            Compound=("Compound", "first"),
            LapCount=("LapNumber", "count"),
            FirstLap=("LapNumber", "min"),
            LastLap=("LapNumber", "max"),
            AvgLapTime=("LapTimeSeconds", "mean"),
        )
        .reset_index()
        .sort_values(["Driver", "Stint"])
        .reset_index(drop=True)
    )
    return summary
