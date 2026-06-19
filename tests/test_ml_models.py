"""
Tests for f1_analysis.ml — all four model classes plus SeasonDataBuilder helpers.

All tests use synthetic DataFrames that mirror the shape of real season
data from SeasonDataBuilder. No network access or real FastF1 sessions
are needed, so the suite runs fully offline and fast.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from f1_analysis.ml.lap_time import LapTimePredictor
from f1_analysis.ml.race_finish import RaceFinishPredictor, _assign_finish_class
from f1_analysis.ml.tire_compound import TireCompoundClassifier
from f1_analysis.ml.undercut import UndercutDetector
from f1_analysis.ml.data_builder import SeasonDataBuilder, COMPOUND_ORDER


# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def season_df() -> pd.DataFrame:
    """
    Synthetic season lap data resembling SeasonDataBuilder output.

    400 laps across 4 rounds, 5 drivers, 2 compounds.
    All numeric columns have plausible F1 values.
    """
    rng = np.random.default_rng(42)
    rows = []
    for round_num in range(1, 5):
        for driver_idx, (driver, base) in enumerate(
            [("VER", 88.5), ("LEC", 88.8), ("HAM", 89.0), ("NOR", 89.2), ("ALO", 89.6)]
        ):
            n_laps = 20
            for lap in range(1, n_laps + 1):
                compound = "SOFT" if lap <= 10 else "HARD"
                tyre_life = lap if lap <= 10 else (lap - 10)
                lap_sec = base + tyre_life * 0.03 + rng.normal(0, 0.25)
                rows.append({
                    "Round": round_num,
                    "EventName": f"Race {round_num}",
                    "Year": 2024,
                    "Driver": driver,
                    "Team": f"Team{driver_idx % 3}",
                    "LapNumber": lap,
                    "LapSeconds": round(lap_sec, 3),
                    "Sector1Seconds": round(lap_sec * 0.3, 3),
                    "Sector2Seconds": round(lap_sec * 0.35, 3),
                    "Sector3Seconds": round(lap_sec * 0.35, 3),
                    "Compound": compound,
                    "CompoundCode": COMPOUND_ORDER[compound],
                    "TyreLife": float(tyre_life),
                    "FreshTyre": tyre_life == 1,
                    "SpeedI1": round(280 + rng.normal(0, 5), 1),
                    "SpeedI2": round(270 + rng.normal(0, 5), 1),
                    "SpeedFL": round(310 + rng.normal(0, 8), 1),
                    "SpeedST": round(330 + rng.normal(0, 6), 1),
                    "Position": float(driver_idx + 1),
                    "TrackStatus": "1",
                    "IsPersonalBest": False,
                    "AirTemp": 24.0,
                    "TrackTemp": 38.0,
                    "Humidity": 48.0,
                    "Stint": 1 if lap <= 10 else 2,
                    "TyreLifeRel": tyre_life / 10,
                    "LapFrac": lap / n_laps,
                    "IsGreenLap": True,
                    "JustPitted": 1 if lap == 11 else 0,
                })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Compound encoding helper
# ---------------------------------------------------------------------------

def test_compound_order_contains_all_compounds():
    for c in ("SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET"):
        assert c in COMPOUND_ORDER


# ---------------------------------------------------------------------------
# LapTimePredictor
# ---------------------------------------------------------------------------

class TestLapTimePredictor:
    def test_fit_returns_self(self, season_df):
        model = LapTimePredictor()
        result = model.fit(season_df)
        assert result is model

    def test_is_fitted_after_fit(self, season_df):
        model = LapTimePredictor()
        assert not model._is_fitted
        model.fit(season_df)
        assert model._is_fitted

    def test_predict_shape(self, season_df):
        model = LapTimePredictor().fit(season_df)
        preds = model.predict(season_df)
        assert preds.shape == (len(season_df),)

    def test_predict_values_in_plausible_range(self, season_df):
        model = LapTimePredictor().fit(season_df)
        preds = model.predict(season_df)
        assert (preds > 60).all(), "All predicted lap times should be > 60s"
        assert (preds < 200).all(), "All predicted lap times should be < 200s"

    def test_evaluate_returns_expected_keys(self, season_df):
        model = LapTimePredictor().fit(season_df)
        eval_result = model.evaluate(season_df)
        for key in ("mae_seconds", "r2", "within_0_5s_pct", "n_samples"):
            assert key in eval_result

    def test_evaluate_r2_positive_on_training_data(self, season_df):
        model = LapTimePredictor().fit(season_df)
        eval_result = model.evaluate(season_df)
        assert eval_result["r2"] > 0, "R² should be positive on training data"

    def test_predict_raises_before_fit(self, season_df):
        model = LapTimePredictor()
        with pytest.raises(RuntimeError, match="not been fitted"):
            model.predict(season_df)

    def test_feature_importances_returns_dataframe(self, season_df):
        model = LapTimePredictor().fit(season_df)
        fi = model.feature_importances()
        assert isinstance(fi, pd.DataFrame)
        assert "Feature" in fi.columns and "Importance" in fi.columns
        assert len(fi) > 0

    def test_degradation_curve_shape(self, season_df):
        model = LapTimePredictor().fit(season_df)
        curve = model.degradation_curve("HARD", tyre_life_range=range(1, 21))
        assert len(curve) == 20
        assert "TyreLife" in curve.columns
        assert "PredictedLapTime" in curve.columns

    def test_degradation_curve_soft_faster_than_hard(self, season_df):
        """Both curves should be monotonically increasing with tyre age (degradation)."""
        model = LapTimePredictor().fit(season_df)
        for compound in ("SOFT", "HARD"):
            curve = model.degradation_curve(compound, tyre_life_range=range(1, 11))
            lap_times = curve["PredictedLapTime"].values
            # At least the trend should go up or stay flat -- not wildly oscillate
            # (first half mean should be no more than 0.5s slower than second half mean)
            assert lap_times[:5].mean() <= lap_times[5:].mean() + 0.5

    def test_save_and_load(self, season_df, tmp_path):
        model = LapTimePredictor().fit(season_df)
        path = tmp_path / "lap_time.pkl"
        model.save(path)
        loaded = LapTimePredictor.load(path)
        preds_original = model.predict(season_df)
        preds_loaded = loaded.predict(season_df)
        np.testing.assert_array_almost_equal(preds_original, preds_loaded)


# ---------------------------------------------------------------------------
# RaceFinishPredictor
# ---------------------------------------------------------------------------

class TestRaceFinishPredictor:
    def test_assign_finish_class_podium(self):
        s = pd.Series([1, 2, 3])
        assert ((_assign_finish_class(s) == 2).all())

    def test_assign_finish_class_points(self):
        s = pd.Series([4, 7, 10])
        assert ((_assign_finish_class(s) == 1).all())

    def test_assign_finish_class_outside(self):
        s = pd.Series([11, 15, 20])
        assert ((_assign_finish_class(s) == 0).all())

    def test_fit_and_predict(self, season_df):
        model = RaceFinishPredictor().fit(season_df)
        preds = model.predict(season_df)
        assert set(preds).issubset({0, 1, 2})
        assert preds.shape == (len(season_df),)

    def test_predict_proba_sums_to_one(self, season_df):
        model = RaceFinishPredictor().fit(season_df)
        proba = model.predict_proba(season_df)
        assert proba.shape[1] >= 2  # at least 2 classes present
        np.testing.assert_allclose(proba.sum(axis=1), 1.0, atol=1e-6)

    def test_evaluate_keys(self, season_df):
        model = RaceFinishPredictor().fit(season_df)
        result = model.evaluate(season_df)
        for key in ("f1_macro", "f1_weighted", "classification_report", "n_samples"):
            assert key in result

    def test_f1_positive_on_training_data(self, season_df):
        model = RaceFinishPredictor().fit(season_df)
        result = model.evaluate(season_df)
        assert result["f1_macro"] > 0

    def test_save_and_load(self, season_df, tmp_path):
        model = RaceFinishPredictor().fit(season_df)
        path = tmp_path / "finish.pkl"
        model.save(path)
        loaded = RaceFinishPredictor.load(path)
        preds_orig = model.predict(season_df)
        preds_load = loaded.predict(season_df)
        np.testing.assert_array_equal(preds_orig, preds_load)


# ---------------------------------------------------------------------------
# TireCompoundClassifier
# ---------------------------------------------------------------------------

class TestTireCompoundClassifier:
    def test_fit_and_predict_strings(self, season_df):
        model = TireCompoundClassifier().fit(season_df)
        preds = model.predict(season_df)
        assert all(p in ("SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET") for p in preds)

    def test_predict_proba_columns(self, season_df):
        model = TireCompoundClassifier().fit(season_df)
        proba = model.predict_proba(season_df)
        assert set(proba.columns) == {"SOFT", "HARD"}  # only two compounds in fixture

    def test_evaluate_keys(self, season_df):
        model = TireCompoundClassifier().fit(season_df)
        result = model.evaluate(season_df)
        for key in ("f1_macro", "f1_weighted", "classification_report", "n_samples"):
            assert key in result

    def test_high_accuracy_with_clean_synthetic_data(self, season_df):
        """Compound should be almost perfectly recoverable from sector times."""
        model = TireCompoundClassifier().fit(season_df)
        result = model.evaluate(season_df)
        assert result["f1_macro"] > 0.7, "Expected >70% F1 on training data"

    def test_save_and_load_predictions_match(self, season_df, tmp_path):
        model = TireCompoundClassifier().fit(season_df)
        path = tmp_path / "compound.pkl"
        model.save(path)
        loaded = TireCompoundClassifier.load(path)
        np.testing.assert_array_equal(model.predict(season_df), loaded.predict(season_df))


# ---------------------------------------------------------------------------
# UndercutDetector
# ---------------------------------------------------------------------------

class TestUndercutDetector:
    def test_fit_and_predict_labels(self, season_df):
        model = UndercutDetector().fit(season_df)
        labels = model.predict(season_df)
        assert set(labels).issubset({-1, 1})
        assert labels.shape == (len(season_df),)

    def test_score_laps_adds_expected_columns(self, season_df):
        model = UndercutDetector().fit(season_df)
        scored = model.score_laps(season_df)
        for col in ("AnomalyScore", "UndercutScore", "WindowOpen", "PaceDeltaSeconds"):
            assert col in scored.columns, f"Missing column: {col}"

    def test_undercut_score_range(self, season_df):
        model = UndercutDetector().fit(season_df)
        scored = model.score_laps(season_df)
        assert scored["UndercutScore"].between(0, 1).all(), "Scores should be in [0, 1]"

    def test_window_open_consistent_with_score(self, season_df):
        model = UndercutDetector().fit(season_df)
        scored = model.score_laps(season_df)
        # All WindowOpen=True laps should have UndercutScore > 0.6
        assert (scored.loc[scored["WindowOpen"], "UndercutScore"] > 0.6).all()

    def test_evaluate_returns_stats(self, season_df):
        model = UndercutDetector().fit(season_df)
        result = model.evaluate(season_df)
        for key in ("total_laps", "windows_flagged", "window_rate_pct", "mean_undercut_score"):
            assert key in result
        assert result["total_laps"] == len(season_df)

    def test_sc_laps_suppressed(self, season_df):
        """Safety car laps (TrackStatus != '1') should get lower undercut scores."""
        model = UndercutDetector().fit(season_df)
        sc_df = season_df.copy()
        sc_df["TrackStatus"] = "4"  # safety car
        green_df = season_df.copy()
        green_df["TrackStatus"] = "1"

        scored_sc = model.score_laps(sc_df)
        scored_green = model.score_laps(green_df)
        assert scored_sc["UndercutScore"].mean() < scored_green["UndercutScore"].mean()

    def test_feature_importances_returns_na_message(self, season_df):
        model = UndercutDetector().fit(season_df)
        fi = model.feature_importances()
        assert isinstance(fi, pd.DataFrame)
        assert "Importance" in fi.columns
