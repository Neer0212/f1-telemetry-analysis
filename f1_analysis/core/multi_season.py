"""
Multi-season comparison helpers.

Provides simple, robust utilities used by `scripts/10_multi_season.py`.

Functions:
- `compare_driver_across_seasons(driver, years, gp, session_type='Q')`
- `compare_two_drivers_across_seasons(driver_a, driver_b, years, gp, session_type='Q')`
- `driver_circuit_heatmap_data(driver, year, session_type='Q', max_rounds=None)`

These use conservative fallbacks and skip missing sessions so the
script remains usable even if some years/events aren't available.
"""

from __future__ import annotations

from typing import List, Optional

import pandas as pd

from f1_analysis.core.session_loader import load_session
from f1_analysis.core.season import get_season_schedule
from f1_analysis.core.lap_analysis import laps_to_seconds


def _best_and_mean_for_driver(session, driver: str) -> Optional[tuple[float, float, str]]:
    """Return (best_seconds, mean_seconds, team) for driver in session, or None if missing."""
    try:
        driver_laps = session.laps.pick_drivers(driver)
    except Exception:
        return None

    if driver_laps.empty:
        return None

    # Best lap
    try:
        best_row = driver_laps.pick_fastest()
        best_seconds = float(best_row["LapTime"].total_seconds()) if best_row["LapTime"] is not None else float("nan")
    except Exception:
        # fallback
        if driver_laps["LapTime"].dropna().empty:
            return None
        best_seconds = float(driver_laps.loc[driver_laps["LapTime"].idxmin()]["LapTime"].total_seconds())

    # Mean lap seconds (ignore NaT)
    mean_seconds = float(laps_to_seconds(driver_laps).dropna().mean()) if not driver_laps.empty else float("nan")

    # Team/constructor if available
    team = None
    if "Team" in driver_laps.columns:
        team = driver_laps.iloc[0].get("Team")
    elif "TeamName" in driver_laps.columns:
        team = driver_laps.iloc[0].get("TeamName")

    return best_seconds, mean_seconds, team


def compare_driver_across_seasons(driver: str, years: List[int], gp: str, session_type: str = "Q") -> pd.DataFrame:
    """Compare one driver's best/mean lap at the same GP across multiple seasons.

    Returns a DataFrame with columns: ``Year``, ``BestLapSeconds``,
    ``MeanLapSeconds``, ``TeammateGapSeconds``, ``Team``.
    """
    rows = []
    for y in years:
        try:
            session = load_session(y, gp, session_type, telemetry=False, weather=False)
        except Exception:
            # skip years that cannot be loaded
            continue

        driver_result = _best_and_mean_for_driver(session, driver)
        if driver_result is None:
            continue
        best, mean, team = driver_result

        # Teammate gap: find any other driver in same team and take their best lap
        teammate_gap = float("nan")
        if team:
            # find other drivers with same team in this session
            try:
                team_laps = session.laps[session.laps.get("Team") == team]
                other_drivers = [d for d in team_laps["Driver"].unique() if d != driver]
                if other_drivers:
                    # take the fastest teammate best lap
                    teammate_bests = []
                    for td in other_drivers:
                        res = _best_and_mean_for_driver(session, td)
                        if res:
                            teammate_bests.append(res[0])
                    if teammate_bests:
                        teammate_best = min(teammate_bests)
                        teammate_gap = best - teammate_best
            except Exception:
                teammate_gap = float("nan")

        rows.append({
            "Year": y,
            "BestLapSeconds": best,
            "MeanLapSeconds": mean,
            "TeammateGapSeconds": teammate_gap,
            "Team": team,
        })

    return pd.DataFrame(rows)


def compare_two_drivers_across_seasons(driver_a: str, driver_b: str, years: List[int], gp: str, session_type: str = "Q") -> pd.DataFrame:
    """Compare two drivers' best lap times at the same GP across seasons.

    Returns a DataFrame with columns: ``Year``, ``{A}_BestLap``, ``{B}_BestLap``,
    ``Gap_AminusB``, ``Faster``.
    """
    rows = []
    for y in years:
        try:
            session = load_session(y, gp, session_type, telemetry=False, weather=False)
        except Exception:
            continue

        res_a = _best_and_mean_for_driver(session, driver_a)
        res_b = _best_and_mean_for_driver(session, driver_b)
        if res_a is None or res_b is None:
            continue

        a_best = res_a[0]
        b_best = res_b[0]
        gap = a_best - b_best
        faster = driver_a if gap < 0 else driver_b

        rows.append({
            "Year": y,
            f"{driver_a}_BestLap": a_best,
            f"{driver_b}_BestLap": b_best,
            "Gap_AminusB": gap,
            "Faster": faster,
        })

    return pd.DataFrame(rows)


def driver_circuit_heatmap_data(driver: str, year: int, session_type: str = "Q", max_rounds: Optional[int] = None) -> pd.DataFrame:
    """Build per-circuit gap-to-session-best for a driver across a season.

    Returns DataFrame with ``Round``, ``Circuit``, ``GapToSessionBest``.
    """
    schedule = get_season_schedule(year)
    if schedule.empty:
        return pd.DataFrame()

    rows = []
    max_round = int(schedule["RoundNumber"].max())
    limit = max_round if max_round is not None else 0
    if max_rounds is not None:
        limit = min(limit, max_rounds)

    for _, ev in schedule.iterrows():
        round_no = int(ev.get("RoundNumber"))
        if max_rounds is not None and round_no > max_rounds:
            continue

        gp_name = ev.get("EventName")
        try:
            session = load_session(year, gp_name, session_type, telemetry=False, weather=False)
        except Exception:
            continue

        # Session best (fastest lap of session)
        try:
            overall_best = float(session.laps["LapTime"].dropna().min().total_seconds())
        except Exception:
            overall_best = float("nan")

        drv_res = _best_and_mean_for_driver(session, driver)
        if drv_res is None:
            # mark as missing
            gap = float("nan")
        else:
            best = drv_res[0]
            gap = best - overall_best

        rows.append({"Round": round_no, "Circuit": gp_name, "GapToSessionBest": gap})

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("Round").reset_index(drop=True)
    return df
