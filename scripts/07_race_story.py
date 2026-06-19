#!/usr/bin/env python3
"""
Complete race story for a single driver.

Shows everything that happened: pit stops, position changes (overtakes
and lost places), safety car/VSC laps, personal best laps, undercut
windows, sector analysis, and a full lap-by-lap timeline — all in one
combined chart + printed summary.

Does NOT require script 05 to be run first. Loads directly from FastF1.

Usage
-----
    python scripts/07_race_story.py --year 2024 --gp "Abu Dhabi" --driver VER
    python scripts/07_race_story.py --year 2024 --gp Monaco --driver LEC
    python scripts/07_race_story.py --year 2025 --gp Bahrain --driver NOR
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib
matplotlib.use("Agg")
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from f1_analysis.core.session_loader import load_session
from f1_analysis.visualization.style import apply_f1_style

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "outputs"

COMPOUND_COLORS = {
    "SOFT": "#DA291C",
    "MEDIUM": "#FFD700",
    "HARD": "#FFFFFF",
    "INTERMEDIATE": "#43B02A",
    "WET": "#0067AD",
    "UNKNOWN": "#888888",
}

TRACK_STATUS_LABELS = {
    "1": "Green",
    "2": "Yellow",
    "3": "SC deployed",
    "4": "Safety Car",
    "5": "Red Flag",
    "6": "VSC deployed",
    "7": "VSC",
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class PitStop:
    lap: int
    compound_before: str
    compound_after: str
    tyre_life_before: float
    stint_number: int


@dataclass
class PositionChange:
    lap: int
    from_pos: int
    to_pos: int

    @property
    def gained(self) -> bool:
        return self.to_pos < self.from_pos

    @property
    def places(self) -> int:
        return abs(self.to_pos - self.from_pos)


@dataclass
class Incident:
    lap: int
    description: str
    status_code: str


@dataclass
class RaceStory:
    driver: str
    event_name: str
    year: int
    team: str
    grid_position: int
    finish_position: int
    finish_status: str
    points: float
    total_laps: int
    pit_stops: list[PitStop] = field(default_factory=list)
    overtakes_made: list[PositionChange] = field(default_factory=list)
    places_lost: list[PositionChange] = field(default_factory=list)
    incidents: list[Incident] = field(default_factory=list)
    personal_best_laps: list[int] = field(default_factory=list)
    fastest_lap: Optional[float] = None
    fastest_lap_number: Optional[int] = None
    undercut_windows: list[int] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Analysis functions
# ---------------------------------------------------------------------------

def _fmt_time(seconds: float) -> str:
    """Format seconds as M:SS.mmm"""
    if pd.isna(seconds):
        return "N/A"
    m = int(seconds // 60)
    s = seconds % 60
    return f"{m}:{s:06.3f}"


def _detect_pit_stops(laps: pd.DataFrame) -> list[PitStop]:
    pits = []
    pit_in_laps = laps[laps["PitInTime"].notna()]
    for _, row in pit_in_laps.iterrows():
        lap_num = int(row["LapNumber"])
        next_lap = laps[laps["LapNumber"] == lap_num + 1]
        compound_after = next_lap["Compound"].iloc[0] if not next_lap.empty else "UNKNOWN"
        pits.append(PitStop(
            lap=lap_num,
            compound_before=str(row.get("Compound", "UNKNOWN")).upper(),
            compound_after=str(compound_after).upper(),
            tyre_life_before=float(row.get("TyreLife", 0)),
            stint_number=int(row.get("Stint", 0)),
        ))
    return pits


def _detect_position_changes(laps: pd.DataFrame) -> tuple[list[PositionChange], list[PositionChange]]:
    """Detect lap-by-lap position changes, ignoring pit stop laps."""
    overtakes = []
    lost = []

    laps_sorted = laps.sort_values("LapNumber").copy()
    positions = laps_sorted["Position"].dropna()

    if len(positions) < 2:
        return overtakes, lost

    for i in range(1, len(laps_sorted)):
        row = laps_sorted.iloc[i]
        prev = laps_sorted.iloc[i - 1]

        curr_pos = row["Position"]
        prev_pos = prev["Position"]

        if pd.isna(curr_pos) or pd.isna(prev_pos):
            continue

        # Skip pit laps — position changes there aren't overtakes
        if prev["PitInTime"] is not pd.NaT and not pd.isna(prev["PitInTime"]):
            continue
        if row["PitOutTime"] is not pd.NaT and not pd.isna(row["PitOutTime"]):
            continue

        delta = int(prev_pos) - int(curr_pos)  # positive = gained positions
        if delta >= 1:
            overtakes.append(PositionChange(
                lap=int(row["LapNumber"]),
                from_pos=int(prev_pos),
                to_pos=int(curr_pos),
            ))
        elif delta <= -1:
            lost.append(PositionChange(
                lap=int(row["LapNumber"]),
                from_pos=int(prev_pos),
                to_pos=int(curr_pos),
            ))

    return overtakes, lost


def _detect_incidents(laps: pd.DataFrame) -> list[Incident]:
    incidents = []
    if "TrackStatus" not in laps.columns:
        return incidents

    prev_status = "1"
    for _, row in laps.sort_values("LapNumber").iterrows():
        status = str(row.get("TrackStatus", "1"))
        lap = int(row["LapNumber"])
        if status != prev_status and status != "1":
            label = TRACK_STATUS_LABELS.get(status[0], f"Status {status}")
            incidents.append(Incident(
                lap=lap,
                description=label,
                status_code=status,
            ))
        prev_status = status
    return incidents


def _detect_undercut_windows(laps: pd.DataFrame) -> list[int]:
    """
    Simple rule-based undercut detection (no ML model required):
    flag laps where the driver is significantly faster than their
    rolling average pace on that stint — suggesting fresh-tyre pace advantage.
    """
    window_laps = []
    for stint, stint_laps in laps.groupby("Stint"):
        if len(stint_laps) < 5:
            continue
        lap_times = stint_laps["LapTime"].dt.total_seconds().dropna()
        if lap_times.empty:
            continue
        rolling_avg = lap_times.rolling(3, min_periods=2).mean()
        for i, (idx, lt) in enumerate(lap_times.items()):
            if i < 3:
                continue
            avg = rolling_avg.iloc[i]
            if pd.notna(avg) and lt < avg - 0.8:  # >0.8s faster than recent avg
                lap_num = stint_laps.loc[idx, "LapNumber"]
                if not pd.isna(lap_num):
                    window_laps.append(int(lap_num))
    return window_laps


# ---------------------------------------------------------------------------
# Chart builder
# ---------------------------------------------------------------------------

def _build_chart(story: RaceStory, laps: pd.DataFrame, out_path: Path) -> None:
    fig = plt.figure(figsize=(18, 24))
    fig.suptitle(
        f"{story.driver} ({story.team})  —  {story.event_name} {story.year}\n"
        f"Started P{story.grid_position}  →  Finished P{story.finish_position}  "
        f"({story.finish_status})  |  {story.points:.0f} pts",
        fontsize=15, y=0.99,
    )
    gs = gridspec.GridSpec(5, 2, figure=fig, hspace=0.55, wspace=0.3)

    laps_sorted = laps.sort_values("LapNumber")
    lap_nums = laps_sorted["LapNumber"].values
    lap_times_s = laps_sorted["LapTime"].dt.total_seconds().values
    positions = laps_sorted["Position"].values

    # ── 1. Lap times with compound color and events ───────────────────
    ax1 = fig.add_subplot(gs[0, :])
    compounds = laps_sorted["Compound"].fillna("UNKNOWN").str.upper().values
    for i in range(len(lap_nums) - 1):
        color = COMPOUND_COLORS.get(compounds[i], "#888888")
        if not (pd.isna(lap_times_s[i]) or pd.isna(lap_times_s[i + 1])):
            ax1.plot([lap_nums[i], lap_nums[i + 1]],
                     [lap_times_s[i], lap_times_s[i + 1]],
                     color=color, linewidth=2.5)

    # Pit stop markers
    for pit in story.pit_stops:
        ax1.axvline(pit.lap, color="white", linewidth=1.2, linestyle="--", alpha=0.7)
        ax1.text(pit.lap + 0.3,
                 ax1.get_ylim()[1] if ax1.get_ylim()[1] > 0 else np.nanmax(lap_times_s[~np.isnan(lap_times_s)]),
                 f"PIT\n{pit.compound_after[:1]}",
                 color="white", fontsize=7, va="top")

    # SC/VSC shading
    for inc in story.incidents:
        if inc.status_code[0] in ("4", "6", "7"):
            ax1.axvspan(inc.lap, inc.lap + 1,
                        alpha=0.2,
                        color="#FFD700" if "VSC" in inc.description else "#FF8C00")

    # Personal best laps
    pb_laps = laps_sorted[laps_sorted["IsPersonalBest"] == True]
    if not pb_laps.empty:
        pb_times = pb_laps["LapTime"].dt.total_seconds()
        ax1.scatter(pb_laps["LapNumber"], pb_times, marker="*",
                    color="#FFD700", s=120, zorder=5, label="Personal Best")

    # Compound legend
    seen = []
    legend_patches = []
    for c in compounds:
        if c not in seen:
            seen.append(c)
            legend_patches.append(mpatches.Patch(color=COMPOUND_COLORS.get(c, "#888"), label=c.capitalize()))
    if story.personal_best_laps:
        legend_patches.append(plt.Line2D([0], [0], marker="*", color="#FFD700",
                                          markersize=10, label="Personal Best", linestyle="None"))
    ax1.legend(handles=legend_patches, loc="upper left", fontsize=8)
    ax1.set_xlabel("Lap")
    ax1.set_ylabel("Lap Time (s)")
    ax1.set_title("Lap Times by Compound  (— pit stop  |  shaded = SC/VSC)")
    ax1.grid(True, alpha=0.25)

    # ── 2. Race position ──────────────────────────────────────────────
    ax2 = fig.add_subplot(gs[1, :])
    valid = ~pd.isna(positions)
    ax2.plot(lap_nums[valid], positions[valid], color="#3671C6", linewidth=2.5)
    ax2.invert_yaxis()
    ax2.set_ylabel("Position")
    ax2.set_xlabel("Lap")
    ax2.set_title("Race Position Over Time")
    ax2.yaxis.set_major_locator(plt.MaxNLocator(integer=True))

    # Annotate overtakes
    for ov in story.overtakes_made:
        ax2.annotate(
            f"▲P{ov.places}",
            xy=(ov.lap, ov.to_pos),
            xytext=(ov.lap + 0.5, ov.to_pos - 0.3),
            color="#27F4D2", fontsize=7, fontweight="bold",
        )
    for lo in story.places_lost:
        ax2.annotate(
            f"▼P{lo.places}",
            xy=(lo.lap, lo.to_pos),
            xytext=(lo.lap + 0.5, lo.to_pos + 0.3),
            color="#E8002D", fontsize=7, fontweight="bold",
        )
    for pit in story.pit_stops:
        ax2.axvline(pit.lap, color="white", linewidth=1, linestyle="--", alpha=0.5)
    ax2.grid(True, alpha=0.25)

    # ── 3. Tyre life per stint ────────────────────────────────────────
    ax3 = fig.add_subplot(gs[2, 0])
    for stint_id, stint_laps in laps_sorted.groupby("Stint"):
        compound = stint_laps["Compound"].iloc[0]
        color = COMPOUND_COLORS.get(str(compound).upper(), "#888")
        ax3.plot(
            stint_laps["LapNumber"],
            stint_laps["TyreLife"],
            color=color, linewidth=2,
            label=f"Stint {int(stint_id)} ({compound})",
        )
    ax3.set_xlabel("Lap")
    ax3.set_ylabel("Tyre Age (laps)")
    ax3.set_title("Tyre Life per Stint")
    ax3.legend(fontsize=8)
    ax3.grid(True, alpha=0.25)

    # ── 4. Sector times ───────────────────────────────────────────────
    ax4 = fig.add_subplot(gs[2, 1])
    s1 = laps_sorted["Sector1Time"].dt.total_seconds()
    s2 = laps_sorted["Sector2Time"].dt.total_seconds()
    s3 = laps_sorted["Sector3Time"].dt.total_seconds()
    if s1.notna().any():
        ax4.plot(lap_nums, s1, label="S1", color="#E8002D", linewidth=1.5, alpha=0.8)
    if s2.notna().any():
        ax4.plot(lap_nums, s2, label="S2", color="#FFD700", linewidth=1.5, alpha=0.8)
    if s3.notna().any():
        ax4.plot(lap_nums, s3, label="S3", color="#27F4D2", linewidth=1.5, alpha=0.8)
    ax4.set_xlabel("Lap")
    ax4.set_ylabel("Sector Time (s)")
    ax4.set_title("Sector Times")
    ax4.legend(fontsize=8)
    ax4.grid(True, alpha=0.25)

    # ── 5. Speed traps ────────────────────────────────────────────────
    ax5 = fig.add_subplot(gs[3, 0])
    if "SpeedST" in laps_sorted.columns and laps_sorted["SpeedST"].notna().any():
        ax5.plot(lap_nums, laps_sorted["SpeedST"], color="#FF8000",
                 linewidth=1.8, label="Speed Trap (km/h)")
        ax5.axhline(laps_sorted["SpeedST"].max(), color="white",
                    linewidth=0.8, linestyle="--", alpha=0.5,
                    label=f"Max: {laps_sorted['SpeedST'].max():.0f} km/h")
    ax5.set_xlabel("Lap")
    ax5.set_ylabel("Speed (km/h)")
    ax5.set_title("Top Speed per Lap")
    ax5.legend(fontsize=8)
    ax5.grid(True, alpha=0.25)

    # ── 6. Gap chart (undercut windows) ──────────────────────────────
    ax6 = fig.add_subplot(gs[3, 1])
    clean_times = laps_sorted["LapTime"].dt.total_seconds().dropna()
    if not clean_times.empty:
        rolling_avg = clean_times.rolling(5, min_periods=2, center=True).mean()
        delta = clean_times - rolling_avg
        ax6.plot(laps_sorted.loc[clean_times.index, "LapNumber"],
                 delta, color="#3671C6", linewidth=1.5, label="Pace delta vs 5-lap avg")
        ax6.axhline(0, color="white", linewidth=0.8, linestyle="--", alpha=0.5)
        ax6.fill_between(
            laps_sorted.loc[clean_times.index, "LapNumber"],
            delta, 0,
            where=delta < -0.5,
            alpha=0.3, color="#27F4D2", label="Faster than average (undercut zone)"
        )
    for w_lap in story.undercut_windows:
        ax6.axvline(w_lap, color="#FFD700", linewidth=1.2, alpha=0.7)
    ax6.set_xlabel("Lap")
    ax6.set_ylabel("Delta (s)")
    ax6.set_title("Pace Delta vs Rolling Avg\n(dips = undercut potential)")
    ax6.legend(fontsize=7)
    ax6.grid(True, alpha=0.25)

    # ── 7. Lap-by-lap event timeline ─────────────────────────────────
    ax7 = fig.add_subplot(gs[4, :])
    ax7.set_xlim(0, story.total_laps + 1)
    ax7.set_ylim(0, 1)
    ax7.set_yticks([])
    ax7.set_xlabel("Lap Number")
    ax7.set_title("Race Event Timeline")

    # Background compound bands
    for stint_id, stint_laps in laps_sorted.groupby("Stint"):
        compound = str(stint_laps["Compound"].iloc[0]).upper()
        color = COMPOUND_COLORS.get(compound, "#888")
        lmin = stint_laps["LapNumber"].min()
        lmax = stint_laps["LapNumber"].max()
        ax7.barh(0.5, lmax - lmin, left=lmin,
                 height=0.6, color=color, alpha=0.25, edgecolor="none")
        ax7.text((lmin + lmax) / 2, 0.5, compound[:1],
                 ha="center", va="center", fontsize=9, color="white", fontweight="bold")

    # Pit markers
    for pit in story.pit_stops:
        ax7.axvline(pit.lap, color="white", linewidth=2, alpha=0.9)
        ax7.text(pit.lap, 0.92, "PIT", ha="center", fontsize=7, color="white")

    # Overtakes
    for ov in story.overtakes_made:
        ax7.text(ov.lap, 0.75, f"▲{ov.places}", ha="center",
                 fontsize=8, color="#27F4D2", fontweight="bold")

    # Lost places
    for lo in story.places_lost:
        ax7.text(lo.lap, 0.25, f"▼{lo.places}", ha="center",
                 fontsize=8, color="#E8002D", fontweight="bold")

    # Incidents
    for inc in story.incidents:
        color = "#FFD700" if "VSC" in inc.description else "#FF8C00"
        ax7.text(inc.lap, 0.1, inc.description[:3].upper(),
                 ha="center", fontsize=6, color=color)

    # Undercut windows
    for w_lap in story.undercut_windows:
        ax7.axvspan(w_lap - 0.4, w_lap + 0.4, alpha=0.4, color="#FFD700", ymin=0.55, ymax=0.65)

    ax7.grid(True, axis="x", alpha=0.2)

    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Terminal summary printer
# ---------------------------------------------------------------------------

def _print_story(story: RaceStory, laps: pd.DataFrame) -> None:
    laps_sorted = laps.sort_values("LapNumber")
    sep = "─" * 60

    print(f"\n{'═'*60}")
    print(f"  RACE STORY: {story.driver} — {story.event_name} {story.year}")
    print(f"{'═'*60}")

    print(f"\n🏎️  RACE RESULT")
    print(sep)
    print(f"  Grid position:    P{story.grid_position}")
    print(f"  Finish position:  P{story.finish_position}")
    places = story.grid_position - story.finish_position
    arrow = "▲" if places > 0 else ("▼" if places < 0 else "=")
    print(f"  Net positions:    {arrow}{abs(places)} {'gained' if places > 0 else 'lost' if places < 0 else '(no change)'}")
    print(f"  Status:           {story.finish_status}")
    print(f"  Points scored:    {story.points:.0f}")

    print(f"\n🛞  PIT STOPS  ({len(story.pit_stops)} stop{'s' if len(story.pit_stops) != 1 else ''})")
    print(sep)
    if story.pit_stops:
        for pit in story.pit_stops:
            print(f"  Lap {pit.lap:2d}  |  {pit.compound_before} → {pit.compound_after}  "
                  f"(tyre was {pit.tyre_life_before:.0f} laps old)")
    else:
        print("  No pit stops recorded.")

    print(f"\n⚡  OVERTAKES MADE  ({len(story.overtakes_made)})")
    print(sep)
    if story.overtakes_made:
        for ov in story.overtakes_made:
            print(f"  Lap {ov.lap:2d}  |  P{ov.from_pos} → P{ov.to_pos}  (+{ov.places} place{'s' if ov.places > 1 else ''})")
    else:
        print("  No on-track overtakes detected.")

    print(f"\n📉  POSITIONS LOST  ({len(story.places_lost)})")
    print(sep)
    if story.places_lost:
        for lo in story.places_lost:
            print(f"  Lap {lo.lap:2d}  |  P{lo.from_pos} → P{lo.to_pos}  (-{lo.places} place{'s' if lo.places > 1 else ''})")
    else:
        print("  No positions lost on track.")

    print(f"\n⚠️   RACE INCIDENTS")
    print(sep)
    if story.incidents:
        for inc in story.incidents:
            print(f"  Lap {inc.lap:2d}  |  {inc.description}")
    else:
        print("  No safety cars or flags.")

    print(f"\n⏱️   LAP TIME ANALYSIS")
    print(sep)
    lap_times = laps_sorted["LapTime"].dt.total_seconds().dropna()
    if not lap_times.empty:
        best_time = lap_times.min()
        best_lap = int(laps_sorted.loc[lap_times.idxmin(), "LapNumber"])
        worst_time = lap_times.max()
        worst_lap = int(laps_sorted.loc[lap_times.idxmax(), "LapNumber"])
        print(f"  Fastest lap:  {_fmt_time(best_time)}  (Lap {best_lap})")
        print(f"  Slowest lap:  {_fmt_time(worst_time)}  (Lap {worst_lap})")
        print(f"  Average pace: {_fmt_time(lap_times.mean())}")
        print(f"  Personal bests set: {len(story.personal_best_laps)} laps")

    print(f"\n🔵  UNDERCUT WINDOWS")
    print(sep)
    if story.undercut_windows:
        print(f"  {len(story.undercut_windows)} potential window(s) detected")
        print(f"  On laps: {story.undercut_windows}")
        print(f"  (These are laps where pace was >0.8s faster than recent average,")
        print(f"   suggesting a fresh-tyre delta that could have supported an undercut)")
    else:
        print("  No undercut windows detected this race.")

    print(f"\n📊  STINT BREAKDOWN")
    print(sep)
    for stint_id, stint_laps in laps_sorted.groupby("Stint"):
        compound = str(stint_laps["Compound"].iloc[0]).upper()
        stint_times = stint_laps["LapTime"].dt.total_seconds().dropna()
        avg = _fmt_time(stint_times.mean()) if not stint_times.empty else "N/A"
        best = _fmt_time(stint_times.min()) if not stint_times.empty else "N/A"
        print(f"  Stint {int(stint_id)}  |  {compound}  |  "
              f"{len(stint_laps)} laps  |  Avg: {avg}  |  Best: {best}")

    print(f"\n🚀  TOP SPEED")
    print(sep)
    if "SpeedST" in laps_sorted.columns and laps_sorted["SpeedST"].notna().any():
        max_speed = laps_sorted["SpeedST"].max()
        max_speed_lap = int(laps_sorted.loc[laps_sorted["SpeedST"].idxmax(), "LapNumber"])
        print(f"  {max_speed:.0f} km/h on Lap {max_speed_lap}")

    print(f"\n{'═'*60}\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--gp", type=str, required=True, help="e.g. 'Monaco', 'Abu Dhabi', 'Silverstone'")
    parser.add_argument("--driver", type=str, required=True, help="Driver code e.g. VER, LEC, NOR")
    args = parser.parse_args()

    driver = args.driver.upper()
    apply_f1_style()

    print(f"Loading {args.year} {args.gp} Race...")
    session = load_session(args.year, args.gp, "R", telemetry=False, weather=False)

    # Get driver laps
    laps = session.laps.pick_drivers(driver).copy()
    if laps.empty:
        available = sorted(session.laps["Driver"].unique())
        print(f"ERROR: Driver '{driver}' not found. Available: {', '.join(available)}")
        sys.exit(1)

    # Get results row
    results = session.results
    driver_result = results[results["Abbreviation"] == driver]
    if driver_result.empty:
        print(f"ERROR: No results found for {driver}.")
        sys.exit(1)
    result_row = driver_result.iloc[0]

    # Build story
    pit_stops = _detect_pit_stops(laps)
    overtakes, places_lost = _detect_position_changes(laps)
    incidents = _detect_incidents(laps)
    undercut_windows = _detect_undercut_windows(laps)

    pb_laps = laps[laps["IsPersonalBest"] == True]["LapNumber"].dropna().astype(int).tolist()
    clean_times = laps["LapTime"].dt.total_seconds().dropna()
    fastest_lap = float(clean_times.min()) if not clean_times.empty else None
    fastest_lap_num = (
        int(laps.loc[clean_times.idxmin(), "LapNumber"]) if fastest_lap else None
    )

    story = RaceStory(
        driver=driver,
        event_name=session.event["EventName"],
        year=args.year,
        team=str(result_row.get("TeamName", "Unknown")),
        grid_position=int(result_row.get("GridPosition", 0)),
        finish_position=int(result_row.get("Position", 0)),
        finish_status=str(result_row.get("Status", "Unknown")),
        points=float(result_row.get("Points", 0)),
        total_laps=int(laps["LapNumber"].max()),
        pit_stops=pit_stops,
        overtakes_made=overtakes,
        places_lost=places_lost,
        incidents=incidents,
        personal_best_laps=pb_laps,
        fastest_lap=fastest_lap,
        fastest_lap_number=fastest_lap_num,
        undercut_windows=undercut_windows,
    )

    # Print to terminal
    _print_story(story, laps)

    # Build and save chart
    event_slug = story.event_name.replace(" ", "_")
    charts_dir = OUTPUT_DIR / "charts" / f"{args.year}_race_stories"
    charts_dir.mkdir(parents=True, exist_ok=True)
    out_path = charts_dir / f"{driver}_{event_slug}_{args.year}.png"

    print(f"Generating race story chart...")
    _build_chart(story, laps, out_path)
    print(f"Chart saved to: {out_path}")


if __name__ == "__main__":
    main()