"""
Tests for f1_analysis.core.lap_analysis.

These tests use hand-built DataFrames that mimic the shape of FastF1's
``session.laps`` rather than hitting the real API, so they run offline
and fast -- useful for verifying the pandas logic itself, independent
of network access or FastF1's data availability.
"""

import pandas as pd
import pytest

from f1_analysis.core.lap_analysis import (
    clean_lap_times,
    fastest_laps_by_driver,
    laps_to_seconds,
    race_pace_summary,
    stint_summary,
)


@pytest.fixture
def sample_laps() -> pd.DataFrame:
    """Two drivers, three laps each, one lap with missing time (DNF/no time)."""
    return pd.DataFrame(
        {
            "Driver": ["VER", "VER", "VER", "HAM", "HAM", "HAM"],
            "LapNumber": [1, 2, 3, 1, 2, 3],
            "LapTime": pd.to_timedelta(
                ["0:01:32.500", "0:01:31.800", None, "0:01:33.100", "0:01:32.900", "0:01:32.700"]
            ),
            "PitInTime": pd.to_timedelta([None] * 6),
            "PitOutTime": pd.to_timedelta([None] * 6),
            "IsAccurate": [True, True, True, True, True, True],
            "Stint": [1, 1, 1, 1, 1, 1],
            "Compound": ["SOFT", "SOFT", "SOFT", "MEDIUM", "MEDIUM", "MEDIUM"],
            "Team": ["Red Bull", "Red Bull", "Red Bull", "Mercedes", "Mercedes", "Mercedes"],
        }
    )


def test_laps_to_seconds_converts_timedelta(sample_laps):
    seconds = laps_to_seconds(sample_laps)
    assert seconds.iloc[0] == pytest.approx(92.5)
    assert pd.isna(seconds.iloc[2])  # the missing lap stays NaN


def test_clean_lap_times_drops_missing_laptime(sample_laps):
    cleaned = clean_lap_times(sample_laps)
    assert len(cleaned) == 5  # one lap (VER lap 3) had no LapTime
    assert cleaned["LapTime"].notna().all()


def test_clean_lap_times_drops_pit_laps():
    laps = pd.DataFrame(
        {
            "Driver": ["VER", "VER"],
            "LapNumber": [1, 2],
            "LapTime": pd.to_timedelta(["0:01:35.000", "0:01:31.000"]),
            "PitInTime": pd.to_timedelta(["0:01:35.000", None]),
            "PitOutTime": pd.to_timedelta([None, None]),
            "IsAccurate": [True, True],
        }
    )
    cleaned = clean_lap_times(laps)
    assert len(cleaned) == 1
    assert cleaned.iloc[0]["LapNumber"] == 2


def test_clean_lap_times_respects_max_lap_time(sample_laps):
    cleaned = clean_lap_times(sample_laps, max_lap_time_seconds=92.0)
    # Only VER's 91.8s lap should survive a 92.0s cap
    assert len(cleaned) == 1
    assert cleaned.iloc[0]["Driver"] == "VER"


def test_fastest_laps_by_driver_picks_min_per_driver(sample_laps):
    cleaned = clean_lap_times(sample_laps)
    fastest = fastest_laps_by_driver(cleaned)

    assert set(fastest["Driver"]) == {"VER", "HAM"}
    assert len(fastest) == 2
    # VER's fastest (91.8) should be first since the result is sorted
    assert fastest.iloc[0]["Driver"] == "VER"
    assert fastest.iloc[0]["LapTimeSeconds"] == pytest.approx(91.8)


def test_race_pace_summary_stats(sample_laps):
    cleaned = clean_lap_times(sample_laps)
    summary = race_pace_summary(cleaned)

    ver_row = summary[summary["Driver"] == "VER"].iloc[0]
    assert ver_row["Laps"] == 2
    assert ver_row["MeanLapTime"] == pytest.approx((92.5 + 91.8) / 2)

    ham_row = summary[summary["Driver"] == "HAM"].iloc[0]
    assert ham_row["Laps"] == 3


def test_stint_summary_groups_by_stint():
    laps = pd.DataFrame(
        {
            "Driver": ["VER"] * 4,
            "LapNumber": [1, 2, 3, 4],
            "LapTime": pd.to_timedelta(
                ["0:01:32.000", "0:01:32.000", "0:01:31.000", "0:01:31.000"]
            ),
            "Stint": [1, 1, 2, 2],
            "Compound": ["SOFT", "SOFT", "HARD", "HARD"],
        }
    )
    summary = stint_summary(laps)

    assert len(summary) == 2
    first_stint = summary[summary["Stint"] == 1].iloc[0]
    assert first_stint["Compound"] == "SOFT"
    assert first_stint["LapCount"] == 2

    second_stint = summary[summary["Stint"] == 2].iloc[0]
    assert second_stint["Compound"] == "HARD"
    assert second_stint["FirstLap"] == 3
    assert second_stint["LastLap"] == 4


def test_empty_laps_dataframe_handled_gracefully():
    empty = pd.DataFrame(
        columns=["Driver", "LapNumber", "LapTime", "PitInTime", "PitOutTime", "IsAccurate"]
    )
    empty["LapTime"] = pd.to_timedelta(empty["LapTime"])
    empty["PitInTime"] = pd.to_timedelta(empty["PitInTime"])
    empty["PitOutTime"] = pd.to_timedelta(empty["PitOutTime"])

    cleaned = clean_lap_times(empty)
    assert cleaned.empty
