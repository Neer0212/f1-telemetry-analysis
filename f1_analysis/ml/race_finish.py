"""
Race finish position classifier.

Predicts whether a driver will finish in a "podium" (P1-3), "points"
(P4-10), or "outside points" (P11+) category, based on their situation
during the race: current position, tire state, race fraction, and pace.

Target classes:
  0 — outside points (P11+)
  1 — points finish (P4-10)
  2 — podium (P1-3)

This is a classification problem rather than direct position regression
because actual finishing order depends heavily on events outside the
feature space (safety cars, retirements, DRS trains), making ordinal
bucket prediction significantly more reliable and useful.

Model: Random Forest Classifier -- naturally handles class imbalance
(podium laps are rare in multi-race data), captures non-linear feature
interactions, and provides probability estimates via predict_proba.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, f1_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from f1_analysis.ml.base import BaseF1Model

FINISH_FEATURES = [
    "LapFrac",          # how far through the race
    "Position",         # current on-track position
    "CompoundCode",
    "TyreLife",
    "TyreLifeRel",
    "LapNumber",
    "IsGreenLap",
    "SpeedI1",
    "SpeedFL",
    "SpeedST",
    "AirTemp",
    "TrackTemp",
    "JustPitted",
]

TARGET = "FinishClass"

PODIUM_THRESH = 3
POINTS_THRESH = 10


def _assign_finish_class(position_series: pd.Series) -> pd.Series:
    """Map position to 0/1/2 class label."""
    return pd.cut(
        position_series,
        bins=[0, PODIUM_THRESH, POINTS_THRESH, 9999],
        labels=[2, 1, 0],
    ).astype(int)


class RaceFinishPredictor(BaseF1Model):
    """
    Random Forest Classifier for predicting finish category.

    Parameters
    ----------
    n_estimators:
        Number of trees.
    max_depth:
        Maximum tree depth (``None`` = unlimited, may overfit).
    class_weight:
        How to handle class imbalance. ``"balanced"`` is recommended
        since podium laps (~15% of data) are underrepresented.
    random_state:
        Seed for reproducibility.
    """

    model_name = "RaceFinishPredictor"

    CLASS_LABELS = {0: "Outside Points (P11+)", 1: "Points (P4-10)", 2: "Podium (P1-3)"}

    def __init__(
        self,
        n_estimators: int = 200,
        max_depth: int = 12,
        class_weight: str = "balanced",
        random_state: int = 42,
    ) -> None:
        super().__init__()
        self._estimator_params = dict(
            n_estimators=n_estimators,
            max_depth=max_depth,
            class_weight=class_weight,
            random_state=random_state,
            n_jobs=-1,
        )

    def _prepare(self, df: pd.DataFrame):
        data = df.copy()
        for col in ("FreshTyre", "IsGreenLap", "JustPitted"):
            if col in data.columns:
                data[col] = data[col].astype(float)

        available = [f for f in FINISH_FEATURES if f in data.columns]
        X = data[available].copy()
        self._feature_names = available

        y = data[TARGET] if TARGET in data.columns else None
        return X, y

    def fit(self, df: pd.DataFrame) -> "RaceFinishPredictor":
        """
        Train the finish-position classifier.

        Parameters
        ----------
        df:
            Season lap DataFrame from
            :class:`~f1_analysis.ml.data_builder.SeasonDataBuilder`.
            Must contain a ``Position`` column (on-track position per lap).

        Returns
        -------
        RaceFinishPredictor
            self.
        """
        clean = df.dropna(subset=["Position"]).copy()
        clean[TARGET] = _assign_finish_class(clean["Position"])

        X, y = self._prepare(clean)
        X = X.fillna(X.median(numeric_only=True))

        self._pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("rf", RandomForestClassifier(**self._estimator_params)),
        ])
        self._pipeline.fit(X, y)
        self._is_fitted = True
        return self

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        """
        Predict finish class (0=outside points, 1=points, 2=podium).

        Returns
        -------
        numpy.ndarray of int, shape ``(n_rows,)``.
        """
        self._require_fitted()
        X, _ = self._prepare(df)
        X = X.fillna(X.median(numeric_only=True))
        return self._pipeline.predict(X)

    def predict_proba(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Predict class probabilities.

        Returns
        -------
        pandas.DataFrame
            One column per class present in training data.
        """
        self._require_fitted()
        X, _ = self._prepare(df)
        X = X.fillna(X.median(numeric_only=True))
        proba = self._pipeline.predict_proba(X)
        all_labels = ["P(outside_points)", "P(points)", "P(podium)"]
        present_classes = self._pipeline.named_steps["rf"].classes_
        columns = [all_labels[c] for c in present_classes]
        return pd.DataFrame(proba, columns=columns)

    def evaluate(self, df: pd.DataFrame) -> dict:
        """
        Evaluate on a held-out DataFrame with a ``Position`` column.

        Returns
        -------
        dict
            ``f1_macro``, ``f1_weighted``, ``classification_report`` string,
            and per-class accuracy.
        """
        self._require_fitted()
        clean = df.dropna(subset=["Position"]).copy()
        clean[TARGET] = _assign_finish_class(clean["Position"])

        X, y = self._prepare(clean)
        X = X.fillna(X.median(numeric_only=True))
        preds = self._pipeline.predict(X)

        all_class_names = {0: "Outside Points", 1: "Points", 2: "Podium"}
        present_classes = sorted(set(y.tolist()) | set(preds.tolist()))
        target_names = [all_class_names[c] for c in present_classes]

        return {
            "f1_macro": round(f1_score(y, preds, average="macro", labels=present_classes), 4),
            "f1_weighted": round(f1_score(y, preds, average="weighted", labels=present_classes), 4),
            "classification_report": classification_report(
                y, preds,
                labels=present_classes,
                target_names=target_names,
            ),
            "n_samples": len(y),
        }
