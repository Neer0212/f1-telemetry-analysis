"""
Pit window calculation helpers.

Provides `calculate_pit_window` and `calculate_all_pit_windows` used
by `scripts/09_pit_window.py`. The implementations use conservative
heuristics so scripts can run without depending on external strategy
engines; they are intentionally simple and well-documented so they
can be replaced with more advanced logic later.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import math
import pandas as pd


@dataclass
class PitWindowResult:
    driver: str
    current_lap: int
    total_laps: int
    earliest_lap: int
    optimal_lap: int
    latest_lap: int
    undercut_threat_lap: Optional[int]
    current_compound: str
    tyre_life: int
    current_position: Optional[int]
    gap_ahead_seconds: Optional[float]
    gap_behind_seconds: Optional[float]
    overcut_possible: bool
    reasoning: List[str]


def _get_latest_driver_lap_before(session, driver: str, lap: int) -> pd.Series:
    """Return the driver's most recent lap row at or before `lap`.

    Raises ValueError if the driver has no laps in the session.
    """
    laps = session.laps.pick_drivers(driver)
    if laps.empty:
        raise ValueError(f"No laps for driver {driver}")

    candidate = laps[laps["LapNumber"] <= lap]
    if candidate.empty:
        # driver may have pitted/retired; fallback to last available
        return laps.iloc[-1]
    return candidate.iloc[-1]


def calculate_pit_window(
    session,
    driver: str,
    *,
    current_lap: Optional[int] = None,
    next_compound: str = "MEDIUM",
) -> PitWindowResult:
    """Calculate a simple pit window for a single driver.

    This uses simple heuristics rather than a detailed strategy model:
    - earliest = current_lap + 1 (can't pit retroactively)
    - latest = min(total_laps - 1, current_lap + 10)
    - optimal = midpoint between earliest and latest
    - overcut_possible = True when tyre life is moderate/old

    Returns a `PitWindowResult` used by the plotting script.
    """
    total_laps = int(session.laps["LapNumber"].max())
    if current_lap is None:
        current_lap = total_laps // 2

    # pull the driver's most recent lap row
    try:
        lap_row = _get_latest_driver_lap_before(session, driver, current_lap)
    except ValueError:
        raise

    curr_compound = lap_row.get("Compound", "UNKNOWN") or "UNKNOWN"

    # Tyre life: prefer explicit column, else infer from stint/lap numbers
    if "TyreLife" in lap_row.index and not pd.isna(lap_row["TyreLife"]):
        tyre_life = int(lap_row["TyreLife"]) if not pd.isna(lap_row["TyreLife"]) else 0
    else:
        # infer from Stint if available
        try:
            stint = int(lap_row.get("Stint", 0))
            driver_laps = session.laps.pick_drivers(driver)
            stint_start = driver_laps[driver_laps["Stint"] == stint]["LapNumber"].min()
            tyre_life = int(lap_row["LapNumber"] - stint_start + 1) if not pd.isna(stint_start) else 0
        except Exception:
            tyre_life = 0

    # position if available
    pos = lap_row.get("Position") if "Position" in lap_row.index else None
    try:
        current_position = int(pos) if not pd.isna(pos) else None
    except Exception:
        current_position = None

    # Basic window heuristics
    earliest = max(1, int(current_lap) + 1)
    latest = min(total_laps - 1, earliest + 10)
    optimal = int(math.floor((earliest + latest) / 2))

    # Simple undercut threat detection placeholder: None for now
    undercut_threat_lap = None

    # Gap values: attempt simple lookup from session.results or laps; fall back to None
    gap_ahead = None
    gap_behind = None

    # Overcut heuristic: if tyres are old enough, overcut is plausible
    overcut_possible = tyre_life >= 4

    reasoning: List[str] = []
    reasoning.append(f"Current compound: {curr_compound}")
    reasoning.append(f"Tyre age (laps): {tyre_life}")
    reasoning.append(f"Earliest allowed pit: Lap {earliest}")
    reasoning.append(f"Latest recommended pit: Lap {latest}")
    reasoning.append(f"Optimal (heuristic midpoint): Lap {optimal}")
    if overcut_possible:
        reasoning.append("Overcut appears viable based on tyre age.")
    else:
        reasoning.append("Overcut unlikely due to young tyre age.")

    return PitWindowResult(
        driver=driver,
        current_lap=int(current_lap),
        total_laps=total_laps,
        earliest_lap=earliest,
        optimal_lap=optimal,
        latest_lap=latest,
        undercut_threat_lap=undercut_threat_lap,
        current_compound=curr_compound,
        tyre_life=tyre_life,
        current_position=current_position,
        gap_ahead_seconds=gap_ahead,
        gap_behind_seconds=gap_behind,
        overcut_possible=overcut_possible,
        reasoning=reasoning,
    )


def calculate_all_pit_windows(session, analysis_lap: Optional[int] = None, next_compound: str = "MEDIUM") -> pd.DataFrame:
    """Calculate pit windows for all drivers and return a summary DataFrame.

    The DataFrame contains columns used by the plotting script:
    ``Driver``, ``EarliestPit``, ``LatestPit``, ``OptimalPit``,
    ``UndercutThreatLap``, ``Position``, ``Compound``, ``TyreAge``
    """
    if analysis_lap is None:
        total = int(session.laps["LapNumber"].max())
        analysis_lap = total // 2

    drivers = sorted(session.laps["Driver"].unique())
    rows = []
    for drv in drivers:
        try:
            res = calculate_pit_window(session, drv, current_lap=analysis_lap, next_compound=next_compound)
        except Exception:
            # Skip drivers with no data
            continue

        rows.append({
            "Driver": drv,
            "EarliestPit": res.earliest_lap,
            "LatestPit": res.latest_lap,
            "OptimalPit": res.optimal_lap,
            "UndercutThreatLap": res.undercut_threat_lap,
            "Position": res.current_position or float("nan"),
            "Compound": res.current_compound,
            "TyreAge": res.tyre_life,
        })

    return pd.DataFrame(rows)
