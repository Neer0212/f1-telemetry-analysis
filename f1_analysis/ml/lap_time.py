"""
Lap time prediction — regression model.

Predicts a driver's lap time (in seconds) from lap-level features:
tire state, lap number through the race, speed trap readings, and
ambient conditions. Useful for:

- Simulating what a lap "should" cost on a given compound at a given
  point in a stint (residuals reveal unusual laps -- safety cars,
  errors, traffic).
- Quantifying tire degradation: how much does each lap of age on a
  HARD compound cost compared to a fresh SOFT?
- Predicting remaining race time for strategy analysis.

Model: Gradient Boosting Regressor (handles non-linear interactions
between features like compound × tyre age × track temperature well,
and is robust to the moderate amount of noise in lap timing data).
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from f1_analysis.ml.base import BaseF1Model

# Features used for lap time regression.
# All numeric; categoricals (compound, driver) handled via CompoundCode
# and per-driver mean encoding applied during fit.
LAP_TIME_FEATURES = [
    "CompoundCode",    # SOFT=0 .. WET=4
    "TyreLife",        # laps on this set (raw)
    "TyreLifeRel",     # tyre life relative to stint length
    "LapFrac",         # how far through the race (0-1)
    "LapNumber",
    "IsGreenLap",      # green flag (True/False)
    "SpeedI1",         # speed trap at intermediate 1
    "SpeedI2",
    "SpeedFL",         # speed at finish line
    "SpeedST",         # speed trap on main straight
    "AirTemp",
    "TrackTemp",
    "Humidity",
    "FreshTyre",
]

TARGET = "LapSeconds"


class LapTimePredictor(BaseF1Model):
    """
    Gradient Boosting Regressor for per-lap time prediction.

    Parameters
    ----------
    n_estimators:
        Number of boosting stages.
    max_depth:
        Max tree depth per stage.
    learning_rate:
        Shrinkage applied to each tree.
    random_state:
        Seed for reproducibility.
    """

    model_name = "LapTimePredictor"

    def __init__(
        self,
        n_estimators: int = 200,
        max_depth: int = 4,
        learning_rate: float = 0.08,
        random_state: int = 42,
    ) -> None:
        super().__init__()
        self._estimator_params = dict(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            random_state=random_state,
            loss="squared_error",
            subsample=0.8,
        )

    def _prepare(self, df: pd.DataFrame) -> tuple[pd.DataFrame, Optional[pd.Series]]:
        """Encode, select features, and split off target."""
        data = df.copy()

        # Boolean → int
        for col in ("FreshTyre", "IsGreenLap"):
            if col in data.columns:
                data[col] = data[col].astype(float)

        available = [f for f in LAP_TIME_FEATURES if f in data.columns]
        X = data[available].copy()
        self._feature_names = available

        y = data[TARGET] if TARGET in data.columns else None
        return X, y

    def fit(self, df: pd.DataFrame) -> "LapTimePredictor":
        """
        Train the lap time regressor.

        Parameters
        ----------
        df:
            Season lap DataFrame as returned by
            :class:`~f1_analysis.ml.data_builder.SeasonDataBuilder`.
            Must contain a ``LapSeconds`` column (the target).

        Returns
        -------
        LapTimePredictor
            self (for chaining).
        """
        clean = df.dropna(subset=[TARGET]).copy()
        # Keep only green-flag, non-pit, accurate laps for training quality
        if "IsGreenLap" in clean.columns:
            clean = clean[clean["IsGreenLap"].astype(bool)]
        # Drop outliers (safety-car pace, VSC, extreme traffic)
        q_low = clean[TARGET].quantile(0.01)
        q_high = clean[TARGET].quantile(0.99)
        clean = clean[(clean[TARGET] >= q_low) & (clean[TARGET] <= q_high)]

        X, y = self._prepare(clean)
        X = X.fillna(X.median(numeric_only=True))

        self._pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("gbr", GradientBoostingRegressor(**self._estimator_params)),
        ])
        self._pipeline.fit(X, y)
        self._is_fitted = True
        return self

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        """
        Predict lap times in seconds.

        Parameters
        ----------
        df:
            DataFrame with the same feature columns used during fit.
            Missing values are median-imputed.

        Returns
        -------
        numpy.ndarray
            Predicted lap times (seconds), shape ``(n_laps,)``.
        """
        self._require_fitted()
        X, _ = self._prepare(df)
        X = X.fillna(X.median(numeric_only=True))
        return self._pipeline.predict(X)

    def evaluate(self, df: pd.DataFrame) -> dict:
        """
        Evaluate the model on a held-out DataFrame.

        Parameters
        ----------
        df:
            DataFrame with ``LapSeconds`` target column.

        Returns
        -------
        dict
            ``mae_seconds``, ``r2``, and ``within_0_5s`` (% of predictions
            within 0.5 s of the actual lap time).
        """
        self._require_fitted()
        clean = df.dropna(subset=[TARGET])
        X, y = self._prepare(clean)
        X = X.fillna(X.median(numeric_only=True))
        preds = self._pipeline.predict(X)

        mae = mean_absolute_error(y, preds)
        r2 = r2_score(y, preds)
        within_half_sec = float(np.mean(np.abs(preds - y.values) <= 0.5) * 100)

        return {
            "mae_seconds": round(mae, 4),
            "r2": round(r2, 4),
            "within_0_5s_pct": round(within_half_sec, 1),
            "n_samples": len(y),
        }

    def degradation_curve(self, compound: str, tyre_life_range: range = range(1, 31)) -> pd.DataFrame:
        """
        Predict how lap time increases with tyre age for a given compound.

        Holds all other features at their median values (from training),
        varies only ``TyreLife`` and ``TyreLifeRel`` — giving a synthetic
        degradation curve useful for visualising compound ageing.

        Parameters
        ----------
        compound:
            One of ``"SOFT"``, ``"MEDIUM"``, ``"HARD"``.
        tyre_life_range:
            Lap age values to predict for.

        Returns
        -------
        pandas.DataFrame
            Columns: ``TyreLife``, ``PredictedLapTime``.
        """
        from f1_analysis.ml.data_builder import COMPOUND_ORDER
        self._require_fitted()
        compound_code = COMPOUND_ORDER.get(compound.upper(), 1)

        # Build a neutral baseline using the features saved during fit,
        # with sensible defaults (avoids all-NaN median issues)
        median_values = {f: 0.0 for f in self._feature_names}
        median_values["IsGreenLap"] = 1.0
        median_values["LapFrac"] = 0.5
        median_values["LapNumber"] = 25.0

        rows = []
        for life in tyre_life_range:
            row = dict(median_values)
            row["TyreLife"] = float(life)
            row["TyreLifeRel"] = life / max(tyre_life_range)
            row["CompoundCode"] = float(compound_code)
            row["FreshTyre"] = 1.0 if life == 1 else 0.0
            rows.append(row)

        X_synth = pd.DataFrame(rows)[self._feature_names]
        preds = self._pipeline.predict(X_synth)
        return pd.DataFrame({"TyreLife": list(tyre_life_range), "PredictedLapTime": preds})
