"""
Undercut window detector.

An undercut is a pit strategy where a driver pits *before* a rival to
take advantage of the fresh-tire speed boost, aiming to emerge ahead
after the rival pits a lap or two later.

This module uses a two-stage approach:

1. **Pace anomaly detection** (Isolation Forest): identify laps that
   are significantly faster than a driver's "expected" pace given their
   tire age and compound -- these anomalies indicate that fresh tires
   are producing a larger-than-expected gain.

2. **Rule-based window scoring**: combine anomaly scores with explicit
   domain rules (stint length, position delta, gap to car ahead) to
   produce an ``UndercutScore`` (0-1) and a ``WindowOpen`` boolean flag.

The two-stage approach is deliberate: pure anomaly detection would flag
wet-weather laps and safety-car restarts as undercut windows; combining
it with F1 domain rules suppresses those false positives.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from f1_analysis.ml.base import BaseF1Model

# Features for pace anomaly detection
ANOMALY_FEATURES = [
    "TyreLife",
    "TyreLifeRel",
    "CompoundCode",
    "LapFrac",
    "AirTemp",
    "TrackTemp",
]

# Feature used as the residual (deviation from expected pace)
PACE_FEATURE = "LapSeconds"


class UndercutDetector(BaseF1Model):
    """
    Isolation Forest + rule-based undercut window detector.

    Parameters
    ----------
    contamination:
        Expected fraction of anomalous laps in the training data.
        0.05 means ~5% of laps are treated as anomalies.
    random_state:
        Seed for reproducibility.
    min_stint_length:
        Minimum laps on a stint before flagging undercut potential.
        Prevents flagging laps 1-2 of a stint when tires are trivially fast.
    """

    model_name = "UndercutDetector"

    def __init__(
        self,
        contamination: float = 0.05,
        random_state: int = 42,
        min_stint_length: int = 5,
    ) -> None:
        super().__init__()
        self._contamination = contamination
        self._random_state = random_state
        self._min_stint_length = min_stint_length
        self._scaler = StandardScaler()
        self._isolation_forest: IsolationForest | None = None
        # Median pace per (CompoundCode, TyreLife bucket) -- used to compute residuals
        self._pace_baseline: pd.DataFrame | None = None

    def fit(self, df: pd.DataFrame) -> "UndercutDetector":
        """
        Fit the anomaly detector on green-flag racing laps.

        Parameters
        ----------
        df:
            Season lap DataFrame from
            :class:`~f1_analysis.ml.data_builder.SeasonDataBuilder`.

        Returns
        -------
        UndercutDetector
            self.
        """
        clean = df.copy()
        if "IsGreenLap" in clean.columns:
            clean = clean[clean["IsGreenLap"].astype(bool)]
        clean = clean.dropna(subset=ANOMALY_FEATURES + [PACE_FEATURE])

        # Build pace baseline: expected pace for each compound × tyre-age bucket
        clean["TyreLifeBucket"] = pd.cut(clean["TyreLife"], bins=[0, 5, 10, 20, 50, 999], labels=False)
        self._pace_baseline = (
            clean.groupby(["CompoundCode", "TyreLifeBucket"])[PACE_FEATURE]
            .median()
            .reset_index()
            .rename(columns={PACE_FEATURE: "BaselinePace"})
        )

        available = [f for f in ANOMALY_FEATURES if f in clean.columns]
        X = clean[available].fillna(clean[available].median())
        X_scaled = self._scaler.fit_transform(X)
        self._feature_names = available

        self._isolation_forest = IsolationForest(
            contamination=self._contamination,
            random_state=self._random_state,
            n_jobs=-1,
        )
        self._isolation_forest.fit(X_scaled)
        self._is_fitted = True
        return self

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        """
        Return Isolation Forest anomaly labels: -1 (anomaly) or 1 (normal).

        For undercut analysis, use :meth:`score_laps` instead -- it
        combines the anomaly label with domain rules into a richer score.

        Returns
        -------
        numpy.ndarray of int (-1 or 1), shape ``(n_rows,)``.
        """
        self._require_fitted()
        available = [f for f in ANOMALY_FEATURES if f in df.columns]
        X = df[available].fillna(df[available].median())
        X_scaled = self._scaler.transform(X)
        return self._isolation_forest.predict(X_scaled)

    def score_laps(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Score laps for undercut potential and flag open windows.

        Combines the Isolation Forest anomaly score (continuous score from
        the forest, not just -1/1) with domain rules:

        - Laps within ``min_stint_length`` of pitting → capped score
        - SC/VSC laps (``TrackStatus != "1"``) → suppressed
        - Pace delta from compound baseline → amplifies signal

        Parameters
        ----------
        df:
            Lap DataFrame (season data or a single-race subset).

        Returns
        -------
        pandas.DataFrame
            The input with three columns added:

            ``AnomalyScore``
                Raw IF score: more negative = more anomalous.
            ``PaceDeltaSeconds``
                Lap time vs. expected baseline for that compound/age.
            ``UndercutScore``
                0-1 score combining anomaly + domain rules (higher = more
                viable undercut window).
            ``WindowOpen``
                Boolean -- ``True`` if ``UndercutScore > 0.6``.
        """
        self._require_fitted()
        out = df.copy()

        # Anomaly scores from IF
        available = [f for f in ANOMALY_FEATURES if f in out.columns]
        X = out[available].fillna(out[available].median())
        X_scaled = self._scaler.transform(X)
        raw_scores = self._isolation_forest.score_samples(X_scaled)
        out["AnomalyScore"] = raw_scores

        # Pace delta vs. compound baseline
        out["TyreLifeBucket"] = pd.cut(out["TyreLife"], bins=[0, 5, 10, 20, 50, 999], labels=False)
        out = out.merge(self._pace_baseline, on=["CompoundCode", "TyreLifeBucket"], how="left")
        if PACE_FEATURE in out.columns:
            out["PaceDeltaSeconds"] = out["BaselinePace"] - out[PACE_FEATURE]  # positive = faster than expected
        else:
            out["PaceDeltaSeconds"] = 0.0
        out.drop(columns=["BaselinePace", "TyreLifeBucket"], errors="ignore", inplace=True)

        # Normalise anomaly score to 0-1
        anom_min, anom_max = raw_scores.min(), raw_scores.max()
        anom_range = anom_max - anom_min if anom_max != anom_min else 1.0
        norm_anom = 1 - (raw_scores - anom_min) / anom_range  # invert: more anomalous = higher

        # Normalise pace delta (faster-than-expected boost)
        pace_delta = out["PaceDeltaSeconds"].fillna(0).values
        pace_boost = np.clip(pace_delta / 2.0, 0, 1)  # each 2s faster → max contribution

        # Combined score
        undercut_score = 0.6 * norm_anom + 0.4 * pace_boost

        # Suppress VSC/SC laps and early stints
        if "TrackStatus" in out.columns:
            sc_laps = ~out["TrackStatus"].astype(str).str.startswith("1")
            undercut_score[sc_laps] *= 0.1
        if "TyreLife" in out.columns:
            early_stint = out["TyreLife"].fillna(0) < self._min_stint_length
            undercut_score[early_stint.values] *= 0.3

        out["UndercutScore"] = np.clip(undercut_score, 0, 1)
        out["WindowOpen"] = out["UndercutScore"] > 0.6
        return out

    def evaluate(self, df: pd.DataFrame) -> dict:
        """
        Summarise undercut window statistics across the input data.

        Parameters
        ----------
        df:
            Lap DataFrame.

        Returns
        -------
        dict
            ``total_laps``, ``windows_flagged``, ``window_rate_pct``,
            ``mean_undercut_score``, ``top_rounds_by_windows``.
        """
        self._require_fitted()
        scored = self.score_laps(df)
        windows = scored[scored["WindowOpen"]]

        top_rounds: dict = {}
        if "EventName" in scored.columns:
            top_rounds = (
                windows.groupby("EventName").size()
                .sort_values(ascending=False)
                .head(5)
                .to_dict()
            )

        return {
            "total_laps": len(scored),
            "windows_flagged": int(windows["WindowOpen"].sum()),
            "window_rate_pct": round(len(windows) / len(scored) * 100, 2),
            "mean_undercut_score": round(float(scored["UndercutScore"].mean()), 4),
            "top_rounds_by_windows": top_rounds,
        }

    def feature_importances(self, top_n: int = 15) -> pd.DataFrame:
        """
        Isolation Forest does not provide feature importances in the
        traditional sense -- override to return a message.
        """
        return pd.DataFrame({
            "Feature": self._feature_names or ANOMALY_FEATURES,
            "Importance": ["N/A (Isolation Forest)"] * len(self._feature_names or ANOMALY_FEATURES),
        })
