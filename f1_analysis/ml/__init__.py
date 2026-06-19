"""
f1_analysis.ml
==============

Machine learning models trained on season-level FastF1 data.

Four models are provided, each solving a distinct prediction task:

- ``LapTimePredictor``      — Regression: predict lap time from lap/car/track features.
- ``RaceFinishPredictor``   — Classification: predict podium / points / no-points finish.
- ``TireCompoundClassifier``— Classification: identify tire compound from telemetry signals.
- ``UndercutDetector``      — Anomaly + rule-based: flag laps that create undercut windows.

All models follow a common interface::

    from f1_analysis.ml import LapTimePredictor, SeasonDataBuilder

    builder = SeasonDataBuilder(year=2024)
    df = builder.build()                    # fetches & caches all races

    model = LapTimePredictor()
    model.fit(df)
    print(model.feature_importances())

    model.save("outputs/models/lap_time_2024.pkl")
    model2 = LapTimePredictor.load("outputs/models/lap_time_2024.pkl")

See ``scripts/05_ml_season_models.py`` for a runnable end-to-end example.
"""

from f1_analysis.ml.data_builder import SeasonDataBuilder
from f1_analysis.ml.lap_time import LapTimePredictor
from f1_analysis.ml.race_finish import RaceFinishPredictor
from f1_analysis.ml.tire_compound import TireCompoundClassifier
from f1_analysis.ml.undercut import UndercutDetector

__all__ = [
    "SeasonDataBuilder",
    "LapTimePredictor",
    "RaceFinishPredictor",
    "TireCompoundClassifier",
    "UndercutDetector",
]
