"""
Tire compound classifier.

Identifies which tire compound a driver is running from lap-level
speed and time signals -- without using the ``Compound`` column itself.

This sounds circular but has real analytical value:
- **Verification**: flag laps where FastF1's compound labelling looks wrong
  (known to happen for older seasons / some circuits).
- **Feature insight**: understand which signals most strongly distinguish
  soft from hard compounds, beyond the obvious (lap time).
- **Historical inference**: for older sessions where compound data is
  incomplete, infer the likely compound from the lap signature.

Features deliberately exclude ``CompoundCode`` and ``Compound`` (the
target), and lap time itself (too directly correlated -- we want to
understand *why* the lap time differs, not predict from it).

Model: Extra Trees Classifier -- faster to train than Random Forest on
large season datasets, still gives good feature importances, and
handles the 5-class imbalance (WET / INTERMEDIATE laps are rare) well
with ``class_weight="balanced"``.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.metrics import classification_report, f1_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler

from f1_analysis.ml.base import BaseF1Model

# Deliberately NO compound column and NO LapSeconds (the target signal).
COMPOUND_FEATURES = [
    "TyreLife",
    "TyreLifeRel",
    "LapFrac",
    "LapNumber",
    "SpeedI1",
    "SpeedI2",
    "SpeedFL",
    "SpeedST",
    "Sector1Seconds",
    "Sector2Seconds",
    "Sector3Seconds",
    "IsGreenLap",
    "AirTemp",
    "TrackTemp",
]

TARGET = "Compound"


class TireCompoundClassifier(BaseF1Model):
    """
    Extra Trees Classifier that identifies tire compound from lap signals.

    Parameters
    ----------
    n_estimators:
        Number of trees.
    min_samples_leaf:
        Minimum samples per leaf (higher = less overfit on rare wet laps).
    random_state:
        Seed for reproducibility.
    """

    model_name = "TireCompoundClassifier"

    def __init__(
        self,
        n_estimators: int = 300,
        min_samples_leaf: int = 5,
        random_state: int = 42,
    ) -> None:
        super().__init__()
        self._estimator_params = dict(
            n_estimators=n_estimators,
            min_samples_leaf=min_samples_leaf,
            class_weight="balanced",
            random_state=random_state,
            n_jobs=-1,
        )
        self._label_encoder = LabelEncoder()

    def _prepare(self, df: pd.DataFrame):
        data = df.copy()
        for col in ("IsGreenLap",):
            if col in data.columns:
                data[col] = data[col].astype(float)

        available = [f for f in COMPOUND_FEATURES if f in data.columns]
        X = data[available].copy()
        self._feature_names = available

        y = data[TARGET].str.upper() if TARGET in data.columns else None
        return X, y

    def fit(self, df: pd.DataFrame) -> "TireCompoundClassifier":
        """
        Train the compound classifier.

        Parameters
        ----------
        df:
            Season lap DataFrame from
            :class:`~f1_analysis.ml.data_builder.SeasonDataBuilder`.
            Must contain a ``Compound`` column.

        Returns
        -------
        TireCompoundClassifier
            self.
        """
        clean = df.dropna(subset=[TARGET, "Sector1Seconds"]).copy()
        clean = clean[clean[TARGET].str.upper().isin(
            ["SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET"]
        )]

        X, y_raw = self._prepare(clean)
        X = X.fillna(X.median(numeric_only=True))
        y = self._label_encoder.fit_transform(y_raw)

        self._pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("et", ExtraTreesClassifier(**self._estimator_params)),
        ])
        self._pipeline.fit(X, y)
        self._is_fitted = True
        return self

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        """
        Predict compound name strings (e.g. ``"SOFT"``, ``"MEDIUM"``).

        Returns
        -------
        numpy.ndarray of str, shape ``(n_rows,)``.
        """
        self._require_fitted()
        X, _ = self._prepare(df)
        X = X.fillna(X.median(numeric_only=True))
        encoded = self._pipeline.predict(X)
        return self._label_encoder.inverse_transform(encoded)

    def predict_proba(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Predict per-compound probabilities.

        Returns
        -------
        pandas.DataFrame
            One column per compound, rows summing to 1.
        """
        self._require_fitted()
        X, _ = self._prepare(df)
        X = X.fillna(X.median(numeric_only=True))
        proba = self._pipeline.predict_proba(X)
        classes = self._label_encoder.classes_
        return pd.DataFrame(proba, columns=classes)

    def evaluate(self, df: pd.DataFrame) -> dict:
        """
        Evaluate on a held-out DataFrame with a ``Compound`` column.

        Returns
        -------
        dict
            ``f1_macro``, ``f1_weighted``, ``classification_report`` string.
        """
        self._require_fitted()
        clean = df.dropna(subset=[TARGET, "Sector1Seconds"]).copy()
        clean = clean[clean[TARGET].str.upper().isin(
            ["SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET"]
        )]

        X, y_raw = self._prepare(clean)
        X = X.fillna(X.median(numeric_only=True))
        y_true = self._label_encoder.transform(y_raw.str.upper())
        y_pred = self._pipeline.predict(X)

        return {
            "f1_macro": round(f1_score(y_true, y_pred, average="macro"), 4),
            "f1_weighted": round(f1_score(y_true, y_pred, average="weighted"), 4),
            "classification_report": classification_report(
                y_true, y_pred,
                target_names=self._label_encoder.classes_,
            ),
            "n_samples": len(y_true),
        }
