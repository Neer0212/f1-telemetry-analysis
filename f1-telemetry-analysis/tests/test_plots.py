"""
Tests for f1_analysis.visualization.plots.

Real FastF1 Session objects require network access to construct, so
these tests use lightweight fakes for the session/style dependencies
and focus on verifying that each plot function runs end-to-end on
correctly-shaped data and returns a Matplotlib Figure. This catches
the most common real-world bugs (wrong column names, shape mismatches,
bad Matplotlib API usage) without needing live data.
"""

import matplotlib

matplotlib.use("Agg")  # headless backend for test environments

import numpy as np
import pandas as pd
import pytest
from matplotlib.figure import Figure

import f1_analysis.visualization.plots as plots_mod
from f1_analysis.core.telemetry import TelemetryComparison


class _FakeEvent(dict):
    year = 2024


class _FakeLaps(pd.DataFrame):
    """Minimal stand-in for FastF1's Laps that supports pick_drivers()."""

    def pick_drivers(self, driver):
        return _FakeLaps(self[self["Driver"] == driver])


class _FakeSession:
    def __init__(self, laps: pd.DataFrame, results: pd.DataFrame | None = None):
        self.laps = _FakeLaps(laps)
        self.event = _FakeEvent({"EventName": "Test Grand Prix", "Location": "Testville", "Country": "Testland"})
        self.name = "Race"
        self.results = results
        self.weather_data = None
        self.date = pd.Timestamp("2024-01-01")


@pytest.fixture(autouse=True)
def stub_style_functions(monkeypatch):
    """Replace FastF1-dependent color/style lookups with fixed test values."""

    def fake_team_color(identifier, session):
        return {"VER": "#3671C6", "HAM": "#27F4D2", "LEC": "#E8002D"}.get(identifier, "#888888")

    def fake_driver_style(identifier, session, style=None):
        colors = {"VER": "#3671C6", "HAM": "#27F4D2", "LEC": "#E8002D"}
        return {"color": colors.get(identifier, "#888888"), "linestyle": "solid"}

    def fake_compound_color(compound, session):
        return {"SOFT": "#DA291C", "MEDIUM": "#FFD700", "HARD": "#FFFFFF"}.get(compound, "#888888")

    monkeypatch.setattr(plots_mod, "get_team_color", fake_team_color)
    monkeypatch.setattr(plots_mod, "get_driver_style", fake_driver_style)
    monkeypatch.setattr(plots_mod, "get_compound_color", fake_compound_color)


@pytest.fixture
def synthetic_session() -> _FakeSession:
    rng = np.random.default_rng(42)
    rows = []
    for driver, base, compound in [("VER", 90.0, "SOFT"), ("HAM", 90.5, "MEDIUM")]:
        for lap in range(1, 11):
            lap_time = base + rng.normal(0, 0.3) + (lap * 0.02)
            rows.append(
                {
                    "Driver": driver,
                    "LapNumber": lap,
                    "LapTime": pd.to_timedelta(lap_time, unit="s"),
                    "PitInTime": pd.NaT,
                    "PitOutTime": pd.NaT,
                    "IsAccurate": True,
                    "Stint": 1 if lap <= 5 else 2,
                    "Compound": compound if lap <= 5 else "HARD",
                    "Team": {"VER": "Red Bull", "HAM": "Mercedes"}[driver],
                }
            )
    return _FakeSession(pd.DataFrame(rows))


@pytest.fixture
def synthetic_comparison() -> TelemetryComparison:
    distance = np.linspace(0, 1000, 100)
    speed_a = 200 + 80 * np.sin(distance / 100)
    speed_b = 200 + 75 * np.sin(distance / 100 + 0.1)
    tel_a = pd.DataFrame(
        {
            "Distance": distance,
            "Speed": speed_a,
            "Throttle": np.clip(50 + 50 * np.sin(distance / 100), 0, 100),
            "Brake": np.sin(distance / 100) < -0.5,
        }
    )
    tel_b = pd.DataFrame(
        {
            "Distance": distance,
            "Speed": speed_b,
            "Throttle": np.clip(48 + 50 * np.sin(distance / 100 + 0.1), 0, 100),
            "Brake": np.sin(distance / 100 + 0.1) < -0.5,
        }
    )
    delta = pd.DataFrame({"Distance": distance, "Delta": np.cumsum(speed_b - speed_a) * 0.001})
    return TelemetryComparison(driver_a="VER", driver_b="HAM", telemetry_a=tel_a, telemetry_b=tel_b, delta_time=delta)


def test_plot_lap_time_distribution_returns_figure(synthetic_session):
    fig = plots_mod.plot_lap_time_distribution(synthetic_session, ["VER", "HAM"])
    assert isinstance(fig, Figure)


def test_plot_race_pace_returns_figure(synthetic_session):
    fig = plots_mod.plot_race_pace(synthetic_session, ["VER", "HAM"])
    assert isinstance(fig, Figure)


def test_plot_tire_strategy_returns_figure(synthetic_session):
    fig = plots_mod.plot_tire_strategy(synthetic_session, drivers=["VER", "HAM"])
    assert isinstance(fig, Figure)


def test_plot_speed_trace_comparison_returns_figure(synthetic_session, synthetic_comparison):
    fig = plots_mod.plot_speed_trace_comparison(synthetic_comparison, synthetic_session)
    assert isinstance(fig, Figure)


def test_plot_telemetry_delta_returns_figure(synthetic_session, synthetic_comparison):
    fig = plots_mod.plot_telemetry_delta(synthetic_comparison, synthetic_session)
    assert isinstance(fig, Figure)


def test_plot_throttle_brake_comparison_returns_figure(synthetic_session, synthetic_comparison):
    fig = plots_mod.plot_throttle_brake_comparison(synthetic_comparison, synthetic_session)
    assert isinstance(fig, Figure)


def test_plot_championship_progression_returns_figure():
    rows = []
    for driver, pace in [("VER", 25), ("HAM", 18)]:
        pts = 0
        for rnd in range(1, 6):
            pts += pace
            rows.append({"Round": rnd, "DriverCode": driver, "Points": pts})
    standings = pd.DataFrame(rows)

    fig = plots_mod.plot_championship_progression(standings, entity_column="DriverCode")
    assert isinstance(fig, Figure)


def test_plot_championship_progression_respects_top_n():
    rows = []
    for driver, final_pts in [("A", 100), ("B", 80), ("C", 10)]:
        rows.append({"Round": 1, "DriverCode": driver, "Points": final_pts})
    standings = pd.DataFrame(rows)

    fig = plots_mod.plot_championship_progression(standings, entity_column="DriverCode", top_n=2)
    legend_labels = [t.get_text() for t in fig.axes[0].get_legend().get_texts()]
    assert "C" not in legend_labels
    assert set(legend_labels) == {"A", "B"}


def test_plot_track_speed_map_returns_figure(synthetic_session):
    n = 50
    theta = np.linspace(0, 2 * np.pi, n)
    telemetry = pd.DataFrame(
        {
            "X": 1000 * np.cos(theta),
            "Y": 1000 * np.sin(theta),
            "Speed": 150 + 100 * np.abs(np.sin(2 * theta)),
        }
    )
    fig = plots_mod.plot_track_speed_map(telemetry, synthetic_session, "VER")
    assert isinstance(fig, Figure)
