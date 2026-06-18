"""
Tests for f1_analysis.reports.session_report.

Uses a lightweight fake session (no network/FastF1 dependency) to
verify the generated Markdown contains the expected sections and that
file output works correctly.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from f1_analysis.reports.session_report import generate_session_report


class _FakeEvent(dict):
    year = 2024


class _FakeLaps(pd.DataFrame):
    def pick_drivers(self, driver):
        return _FakeLaps(self[self["Driver"] == driver])


class _FakeSession:
    def __init__(self, laps: pd.DataFrame, weather_data=None):
        self.laps = _FakeLaps(laps)
        self.event = _FakeEvent({"EventName": "Test Grand Prix", "Location": "Testville", "Country": "Testland"})
        self.name = "Race"
        self.weather_data = weather_data
        self.date = pd.Timestamp("2024-01-01")


@pytest.fixture
def fake_session() -> _FakeSession:
    rng = np.random.default_rng(7)
    rows = []
    for driver, team, base, compound in [
        ("VER", "Red Bull", 90.0, "SOFT"),
        ("HAM", "Mercedes", 90.5, "MEDIUM"),
    ]:
        for lap in range(1, 6):
            rows.append(
                {
                    "Driver": driver,
                    "Team": team,
                    "LapNumber": lap,
                    "LapTime": pd.to_timedelta(base + rng.normal(0, 0.2), unit="s"),
                    "PitInTime": pd.NaT,
                    "PitOutTime": pd.NaT,
                    "IsAccurate": True,
                    "Stint": 1,
                    "Compound": compound,
                }
            )
    laps = pd.DataFrame(rows)

    weather = pd.DataFrame(
        {
            "AirTemp": [22.0, 23.0],
            "TrackTemp": [35.0, 36.0],
            "Humidity": [50.0, 52.0],
            "Rainfall": [False, False],
        }
    )
    return _FakeSession(laps, weather_data=weather)


def test_report_contains_key_sections(fake_session):
    report = generate_session_report(fake_session)

    assert "# Session Report" in report
    assert "Test Grand Prix" in report
    assert "## Fastest Laps" in report
    assert "## Race Pace Summary" in report
    assert "## Tire Strategy" in report
    assert "VER" in report
    assert "HAM" in report


def test_report_includes_weather_when_available(fake_session):
    report = generate_session_report(fake_session)
    assert "Air temperature" in report
    assert "Track temperature" in report


def test_report_handles_missing_weather(fake_session):
    fake_session.weather_data = pd.DataFrame()
    report = generate_session_report(fake_session)
    assert "Weather data not available" in report


def test_report_writes_to_file(fake_session, tmp_path):
    output_path = tmp_path / "subdir" / "report.md"
    report = generate_session_report(fake_session, output_path=output_path)

    assert output_path.exists()
    assert output_path.read_text(encoding="utf-8") == report
