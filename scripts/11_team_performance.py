"""
Team performance gap analysis.

Measures how much faster or slower each team's car is relative to the
field average at each circuit and across the season. Useful for answering:
- How big is the gap between McLaren and Ferrari in 2024?
- Which team improved the most across the season?
- Is Red Bull's advantage larger at high-speed or slow circuits?

Uses qualifying pace as the primary measure (removes driver variability
and is not distorted by strategy or safety cars) but race pace is also
supported.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
import fastf1

from f1_analysis.core.session_loader import load_session
from f1_analysis.core.lap_analysis import clean_lap_times, laps_to_seconds


def team_pace_gap_single_session(session) -> pd.DataFrame:
    """
    Calculate each team's pace gap to the session fastest in one session.

    Parameters
    ----------
    session:
        A loaded FastF1 session (qualifying recommended for cleanest comparison).

    Returns
    -------
    pandas.DataFrame
        One row per team with their fastest driver's best lap and gap
        to the session benchmark.
    """
    clean = clean_lap_times(session.laps)
    if clean.empty:
        return pd.DataFrame()

    # Get best lap per driver
    best_per_driver = (
        clean.groupby("Driver")
        .apply(lambda x: laps_to_seconds(x).min())
        .reset_index()
    )
    best_per_driver.columns = ["Driver", "BestLapSeconds"]

    # Add team via results
    try:
        results = session.results[["Abbreviation", "TeamName"]].copy()
        results.columns = ["Driver", "Team"]
        best_per_driver = best_per_driver.merge(results, on="Driver", how="left")
    except Exception:
        best_per_driver["Team"] = "Unknown"

    # Best lap per team = fastest of either driver
    best_per_team = (
        best_per_driver.groupby("Team")["BestLapSeconds"]
        .min()
        .reset_index()
        .rename(columns={"BestLapSeconds": "TeamBestLap"})
    )

    # Gap to overall session fastest
    session_best = best_per_team["TeamBestLap"].min()
    best_per_team["GapToFastest"] = round(best_per_team["TeamBestLap"] - session_best, 3)
    best_per_team["GapPct"] = round((best_per_team["TeamBestLap"] / session_best - 1) * 100, 3)
    best_per_team["EventName"] = session.event["EventName"]
    best_per_team["Year"] = session.event.year

    return best_per_team.sort_values("GapToFastest").reset_index(drop=True)


def team_pace_season_progression(
    year: int,
    session_type: str = "Q",
    max_rounds: Optional[int] = None,
    teams: Optional[list[str]] = None,
) -> pd.DataFrame:
    """
    Build round-by-round team pace gap data for an entire season.

    Downloads qualifying (or race) data for each round and computes
    each team's gap to the session fastest. The result shows how the
    performance order evolved as teams developed their cars.

    Parameters
    ----------
    year:
        Season year.
    session_type:
        "Q" for qualifying (recommended), "R" for race pace.
    max_rounds:
        Limit to first N rounds (useful for testing).
    teams:
        If provided, only include these teams in the output.

    Returns
    -------
    pandas.DataFrame
        Long-format table: one row per team per round.
    """
    schedule = fastf1.get_event_schedule(year, include_testing=False)
    if max_rounds:
        schedule = schedule.head(max_rounds)

    all_rows = []
    for _, event in schedule.iterrows():
        round_num = int(event["RoundNumber"])
        gp = event["EventName"]
        print(f"  Round {round_num}: {gp}...")
        try:
            session = load_session(year, round_num, session_type,
                                   telemetry=False, weather=False)
        except Exception as e:
            print(f"  Skipping: {e}")
            continue

        round_data = team_pace_gap_single_session(session)
        if round_data.empty:
            continue

        round_data["Round"] = round_num
        all_rows.append(round_data)

    if not all_rows:
        return pd.DataFrame()

    df = pd.concat(all_rows, ignore_index=True)

    if teams:
        df = df[df["Team"].isin(teams)]

    return df.sort_values(["Round", "GapToFastest"]).reset_index(drop=True)


def team_gap_summary(season_df: pd.DataFrame) -> pd.DataFrame:
    """
    Summarize each team's average gap to the fastest across all rounds.

    Parameters
    ----------
    season_df:
        Output from :func:`team_pace_season_progression`.

    Returns
    -------
    pandas.DataFrame
        One row per team with mean, best, and worst gap across the season.
    """
    summary = (
        season_df.groupby("Team")["GapToFastest"]
        .agg(
            MeanGap="mean",
            BestGap="min",
            WorstGap="max",
            RoundsAnalyzed="count",
        )
        .round(3)
        .sort_values("MeanGap")
        .reset_index()
    )
    return summary


def inter_team_gap(season_df: pd.DataFrame, team_a: str, team_b: str) -> pd.DataFrame:
    """
    Compute the direct gap between two specific teams round by round.

    Parameters
    ----------
    season_df:
        Output from :func:`team_pace_season_progression`.
    team_a, team_b:
        Team names to compare.

    Returns
    -------
    pandas.DataFrame
        Round-by-round gap between team_a and team_b (negative = team_a faster).
    """
    a = season_df[season_df["Team"] == team_a][["Round", "EventName", "GapToFastest"]].rename(
        columns={"GapToFastest": f"{team_a}_Gap"}
    )
    b = season_df[season_df["Team"] == team_b][["Round", "GapToFastest"]].rename(
        columns={"GapToFastest": f"{team_b}_Gap"}
    )
    merged = a.merge(b, on="Round", how="inner")
    merged["DirectGap"] = round(merged[f"{team_a}_Gap"] - merged[f"{team_b}_Gap"], 3)
    merged["Faster"] = merged["DirectGap"].apply(lambda x: team_a if x < 0 else team_b)
    return merged.sort_values("Round").reset_index(drop=True)