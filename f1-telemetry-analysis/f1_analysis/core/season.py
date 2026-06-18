"""
Season-level analysis utilities.

While the rest of the package focuses on a single session's lap and
telemetry data, this module zooms out to a full championship season:
the event calendar (via FastF1's native schedule) and standings
progression race-by-race (via the Ergast API that FastF1 bundles).

Note that standings-progression functions make one network request per
round, so building a full-season progression involves ~20+ requests.
This is intentionally not cached as aggressively as session data --
consider saving the result locally if you'll reuse it (e.g. to CSV).
"""

from __future__ import annotations

import logging
from typing import Optional

import pandas as pd
from fastf1.ergast import Ergast

import fastf1

logger = logging.getLogger(__name__)


def get_season_schedule(year: int, *, include_testing: bool = False) -> pd.DataFrame:
    """
    Get the full event schedule for a season.

    Parameters
    ----------
    year:
        Championship season, e.g. ``2024``.
    include_testing:
        Whether to include pre-season testing entries.

    Returns
    -------
    pandas.DataFrame
        One row per event with columns including ``RoundNumber``,
        ``EventName``, ``Country``, ``Location``, and session dates.
    """
    schedule = fastf1.get_event_schedule(year, include_testing=include_testing)
    return pd.DataFrame(schedule)


def build_driver_standings_progression(
    year: int,
    *,
    up_to_round: Optional[int] = None,
) -> pd.DataFrame:
    """
    Build race-by-race driver championship standings for a season.

    Makes one Ergast request per completed round to reconstruct how the
    championship table evolved, which is the basis for a "championship
    race over time" line chart.

    Parameters
    ----------
    year:
        Championship season, e.g. ``2024``.
    up_to_round:
        Only build the progression through this round number. If
        ``None``, uses every round in the season's schedule that has
        already taken place.

    Returns
    -------
    pandas.DataFrame
        Long-format table with columns ``Round``, ``DriverCode`` (or
        full name if no code is available), ``Points``, and ``Position``
        -- one row per driver per round.
    """
    ergast = Ergast()
    schedule = get_season_schedule(year)
    max_round = up_to_round or int(schedule["RoundNumber"].max())

    rows = []
    for round_number in range(1, max_round + 1):
        try:
            response = ergast.get_driver_standings(season=year, round=round_number)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not fetch standings for round %d: %s", round_number, exc)
            continue

        if not response.content:
            continue

        round_standings = response.content[0]
        for _, row in round_standings.iterrows():
            rows.append(
                {
                    "Round": round_number,
                    "DriverCode": row.get("driverCode", row.get("driverId")),
                    "DriverName": f"{row.get('givenName', '')} {row.get('familyName', '')}".strip(),
                    "Points": row.get("points"),
                    "Position": row.get("position"),
                    "Constructor": (
                        row["constructorNames"][0]
                        if isinstance(row.get("constructorNames"), list) and row.get("constructorNames")
                        else None
                    ),
                }
            )

    return pd.DataFrame(rows)


def build_team_standings_progression(
    year: int,
    *,
    up_to_round: Optional[int] = None,
) -> pd.DataFrame:
    """
    Build race-by-race constructor (team) championship standings for a season.

    Same approach as :func:`build_driver_standings_progression` but for
    the constructors' championship.

    Parameters
    ----------
    year:
        Championship season, e.g. ``2024``.
    up_to_round:
        Only build the progression through this round number. If
        ``None``, uses every round in the season's schedule that has
        already taken place.

    Returns
    -------
    pandas.DataFrame
        Long-format table with columns ``Round``, ``Constructor``,
        ``Points``, and ``Position`` -- one row per team per round.
    """
    ergast = Ergast()
    schedule = get_season_schedule(year)
    max_round = up_to_round or int(schedule["RoundNumber"].max())

    rows = []
    for round_number in range(1, max_round + 1):
        try:
            response = ergast.get_constructor_standings(season=year, round=round_number)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not fetch constructor standings for round %d: %s", round_number, exc)
            continue

        if not response.content:
            continue

        round_standings = response.content[0]
        for _, row in round_standings.iterrows():
            rows.append(
                {
                    "Round": round_number,
                    "Constructor": row.get("constructorName", row.get("constructorId")),
                    "Points": row.get("points"),
                    "Position": row.get("position"),
                }
            )

    return pd.DataFrame(rows)
