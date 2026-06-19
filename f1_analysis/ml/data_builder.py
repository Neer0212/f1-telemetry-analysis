"""
Season-level training data builder.

Iterates over a season's race calendar, loads each session via FastF1,
and assembles a flat DataFrame of per-lap features that all four ML
models are trained on.

This is intentionally separated from the model classes so the (expensive)
data-fetching step runs once and the result can be saved to disk, letting
you experiment with model parameters without re-downloading sessions.

Example
-------
    builder = SeasonDataBuilder(year=2024)
    df = builder.build(save_path="outputs/season_2024_laps.csv")
    # later:
    df = SeasonDataBuilder.load_csv("outputs/season_2024_laps.csv")
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Union

import numpy as np
import pandas as pd

from f1_analysis.core.session_loader import load_session

logger = logging.getLogger(__name__)

# Compound encoding -- ordinal (harder = more laps, softer = faster peak).
COMPOUND_ORDER = {
    "SOFT": 0,
    "MEDIUM": 1,
    "HARD": 2,
    "INTERMEDIATE": 3,
    "WET": 4,
    "UNKNOWN": 5,
    "TEST_UNKNOWN": 5,
}


class SeasonDataBuilder:
    """
    Fetch and assemble per-lap training data for a full season.

    Parameters
    ----------
    year:
        Championship season (e.g. ``2024``).
    cache_dir:
        Where FastF1's raw session cache lives.
    """

    def __init__(self, year: int, cache_dir: Union[str, Path] = "cache") -> None:
        self.year = year
        self.cache_dir = Path(cache_dir)

    def build(
        self,
        *,
        save_path: Optional[Union[str, Path]] = None,
        max_rounds: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        Fetch every race session in the season and return a merged lap DataFrame.

        Each row is one lap, enriched with:

        - Lap-level timing (``LapTimeSeconds``, sector times, speed traps)
        - Tire state (``Compound``, ``TyreLife``, ``FreshTyre``)
        - Race context (``LapNumber``, ``Position``, ``TrackStatus``)
        - Session metadata added by this builder (``Round``, ``EventName``,
          ``AirTemp``, ``TrackTemp``, ``Humidity``)
        - Engineered features (``TyreLifeRel``, ``LapFrac``, ``IsGreenLap``)

        Parameters
        ----------
        save_path:
            If provided, the assembled DataFrame is written to this CSV path
            before returning, so you can reload it without re-fetching.
        max_rounds:
            Stop after this many rounds (useful for quick tests with partial
            seasons while development / waiting for new sessions).

        Returns
        -------
        pandas.DataFrame
            Ready-to-use training data, with ``LapTimeSeconds`` as the
            regression target and ``CompoundCode`` as the classification
            target for the tire model.
        """
        from fastf1 import get_event_schedule

        schedule = get_event_schedule(self.year, include_testing=False)
        rounds = schedule[schedule["RoundNumber"] > 0]

        if max_rounds:
            rounds = rounds.head(max_rounds)

        all_laps: list[pd.DataFrame] = []

        for _, event in rounds.iterrows():
            round_num = int(event["RoundNumber"])
            event_name = event["EventName"]
            logger.info("Processing round %d: %s", round_num, event_name)

            try:
                session = load_session(
                    self.year, round_num, "R",
                    telemetry=False,   # telemetry not needed for lap-level ML
                    weather=True,
                    cache_dir=self.cache_dir,
                )
            except RuntimeError as exc:
                logger.warning("Skipping %s: %s", event_name, exc)
                continue

            lap_df = self._extract_laps(session, round_num, event_name)
            if lap_df is not None and not lap_df.empty:
                all_laps.append(lap_df)

        if not all_laps:
            raise RuntimeError(
                f"No lap data was collected for the {self.year} season. "
                "Check network access and that the season has at least one completed race."
            )

        combined = pd.concat(all_laps, ignore_index=True)
        combined = self._engineer_features(combined)

        if save_path is not None:
            save_path = Path(save_path)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            combined.to_csv(save_path, index=False)
            logger.info("Saved %d laps to %s", len(combined), save_path)

        logger.info("Season data build complete: %d laps across %d rounds.", len(combined), len(all_laps))
        return combined

    def _extract_laps(
        self, session, round_num: int, event_name: str
    ) -> Optional[pd.DataFrame]:
        """Pull the key columns from a session's laps DataFrame."""
        laps = session.laps.copy()
        if laps.empty:
            return None

        # Sector times to seconds
        for col in ("LapTime", "Sector1Time", "Sector2Time", "Sector3Time"):
            if col in laps.columns:
                laps[col.replace("Time", "Seconds")] = laps[col].dt.total_seconds()

        # Compound encoding
        laps["CompoundCode"] = (
            laps["Compound"]
            .fillna("UNKNOWN")
            .str.upper()
            .map(COMPOUND_ORDER)
            .fillna(5)
            .astype(int)
        )

        # Weather averages for this session
        weather_feats = {"AirTemp": np.nan, "TrackTemp": np.nan, "Humidity": np.nan}
        if session.weather_data is not None and not session.weather_data.empty:
            w = session.weather_data
            weather_feats = {
                "AirTemp": float(w["AirTemp"].mean()),
                "TrackTemp": float(w["TrackTemp"].mean()),
                "Humidity": float(w["Humidity"].mean()),
            }
        for k, v in weather_feats.items():
            laps[k] = v

        # Session / event metadata
        laps["Round"] = round_num
        laps["EventName"] = event_name
        laps["Year"] = self.year

        keep_cols = [
            "Round", "EventName", "Year",
            "Driver", "Team",
            "LapNumber", "LapSeconds", "Sector1Seconds", "Sector2Seconds", "Sector3Seconds",
            "Compound", "CompoundCode", "TyreLife", "FreshTyre",
            "SpeedI1", "SpeedI2", "SpeedFL", "SpeedST",
            "Position", "TrackStatus", "IsPersonalBest",
            "AirTemp", "TrackTemp", "Humidity",
            "Stint",
        ]
        existing = [c for c in keep_cols if c in laps.columns]
        return laps[existing]

    @staticmethod
    def _engineer_features(df: pd.DataFrame) -> pd.DataFrame:
        """Add derived features useful across all four models."""
        out = df.copy()

        # Tyre life relative to the max seen in this stint (0=new, 1=end of stint)
        if "TyreLife" in out.columns:
            stint_max = out.groupby(["Round", "Driver", "Stint"])["TyreLife"].transform("max")
            out["TyreLifeRel"] = out["TyreLife"] / stint_max.replace(0, np.nan)

        # Lap fraction through the race (0=start, 1=finish)
        if "LapNumber" in out.columns:
            race_max = out.groupby(["Round"])["LapNumber"].transform("max")
            out["LapFrac"] = out["LapNumber"] / race_max.replace(0, np.nan)

        # Boolean: lap under green-flag conditions (TrackStatus == "1")
        if "TrackStatus" in out.columns:
            out["IsGreenLap"] = out["TrackStatus"].astype(str).str.startswith("1")

        # Pit flag (any change in Compound or TyreLife reset within a driver's race)
        if "CompoundCode" in out.columns:
            out["JustPitted"] = (
                out.sort_values(["Round", "Driver", "LapNumber"])
                .groupby(["Round", "Driver"])["Stint"]
                .diff()
                .fillna(0)
                .gt(0)
                .astype(int)
            )

        return out

    @staticmethod
    def load_csv(path: Union[str, Path]) -> pd.DataFrame:
        """
        Reload a previously saved season CSV.

        Parameters
        ----------
        path:
            Path written by :meth:`build` with ``save_path`` set.

        Returns
        -------
        pandas.DataFrame
        """
        return pd.read_csv(path)
