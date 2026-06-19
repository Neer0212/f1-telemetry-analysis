"""
Shared base class for all F1 ML models.

Handles serialisation (save/load via joblib), a common feature-importance
interface, and a standard evaluation-report printer, so the four concrete
model classes stay focused on their own feature sets and estimator choices.
"""

from __future__ import annotations

import pickle
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional, Union

import joblib
import numpy as np
import pandas as pd


class BaseF1Model(ABC):
    """
    Abstract base for F1 ML models.

    Subclasses implement :meth:`fit`, :meth:`predict`, and optionally
    :meth:`evaluate`, selecting their own feature columns and
    scikit-learn estimator.
    """

    model_name: str = "BaseF1Model"

    def __init__(self) -> None:
        self._pipeline: Optional[Any] = None  # sklearn Pipeline set by subclass
        self._feature_names: list[str] = []
        self._is_fitted: bool = False

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abstractmethod
    def fit(self, df: pd.DataFrame) -> "BaseF1Model":
        """Train the model on season lap data."""

    @abstractmethod
    def predict(self, df: pd.DataFrame) -> np.ndarray:
        """Return predictions for the rows in *df*."""

    # ------------------------------------------------------------------
    # Common utilities
    # ------------------------------------------------------------------

    def _require_fitted(self) -> None:
        if not self._is_fitted:
            raise RuntimeError(
                f"{self.model_name} has not been fitted yet. Call .fit(df) first."
            )

    def feature_importances(self, top_n: int = 15) -> pd.DataFrame:
        """
        Return the model's feature importances as a sorted DataFrame.

        Works for tree-based models (RandomForest, GradientBoosting,
        ExtraTrees) that expose ``feature_importances_`` on the final
        estimator. For linear models it falls back to ``coef_``.

        Parameters
        ----------
        top_n:
            How many features to return (sorted by importance, descending).

        Returns
        -------
        pandas.DataFrame
            Columns: ``Feature``, ``Importance``.
        """
        self._require_fitted()

        # Dig through Pipeline to the final estimator
        estimator = self._pipeline
        if hasattr(estimator, "named_steps"):
            estimator = list(estimator.named_steps.values())[-1]

        if hasattr(estimator, "feature_importances_"):
            importances = estimator.feature_importances_
        elif hasattr(estimator, "coef_"):
            importances = np.abs(estimator.coef_).flatten()
        else:
            return pd.DataFrame(columns=["Feature", "Importance"])

        names = self._feature_names or [f"feature_{i}" for i in range(len(importances))]
        df = (
            pd.DataFrame({"Feature": names, "Importance": importances})
            .sort_values("Importance", ascending=False)
            .head(top_n)
            .reset_index(drop=True)
        )
        return df

    def save(self, path: Union[str, Path]) -> None:
        """
        Persist the fitted model to disk.

        Parameters
        ----------
        path:
            File path (e.g. ``"outputs/models/lap_time_2024.pkl"``).
            Parent directories are created if needed.
        """
        self._require_fitted()
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)

    @classmethod
    def load(cls, path: Union[str, Path]) -> "BaseF1Model":
        """
        Load a previously saved model.

        Parameters
        ----------
        path:
            Path written by :meth:`save`.

        Returns
        -------
        BaseF1Model
            The loaded model, ready for :meth:`predict`.
        """
        return joblib.load(Path(path))

    def __repr__(self) -> str:
        status = "fitted" if self._is_fitted else "not fitted"
        return f"{self.model_name}({status})"
