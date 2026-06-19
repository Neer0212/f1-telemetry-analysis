#!/usr/bin/env python3
"""
Pit stop window calculator.

Analyzes race data and calculates the optimal pit window for one or all
drivers at a given point in the race — including undercut threat, overcut
potential, and earliest/latest viable pit lap.

Usage
-----
    # Analyze VER's pit window at lap 25 of the 2024 Bahrain race
    py scripts/09_pit_window.py --year 2024 --gp Bahrain --driver VER --lap 25

    # Analyze all drivers at race midpoint
    py scripts/09_pit_window.py --year 2024 --gp Monza --all-drivers

    # Specify the next compound
    py scripts/09_pit_window.py --year 2024 --gp Silverstone --driver HAM --lap 20 --next-compound HARD
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.pyplot as plt
import pandas as pd

from f1_analysis.core.session_loader import load_session
from f1_analysis.core.pit_window import calculate_pit_window, calculate_all_pit_windows
from f1_analysis.visualization.style import apply_f1_style, get_driver_color

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "outputs"


def plot_pit_window_single(result, session, out_path):
    """Visual pit window for one driver."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    color = get_driver_color(result.driver, session)

    # ── Left: window bar ──────────────────────────────────────────────
    ax = axes[0]
    total = result.total_laps

    # Full race bar
    ax.barh(0, total, left=0, height=0.4, color="#2C2C2C", alpha=0.5, label="Full race")

    # Pit window
    window_width = result.latest_lap - result.earliest_lap
    ax.barh(0, window_width, left=result.earliest_lap, height=0.4,
            color=color, alpha=0.8, label=f"Pit window (L{result.earliest_lap}–L{result.latest_lap})")

    # Optimal lap marker
    ax.axvline(result.optimal_lap, color="#FFD700", linewidth=2.5,
               label=f"Optimal: Lap {result.optimal_lap}")

    # Undercut threat
    if result.undercut_threat_lap:
        ax.axvline(result.undercut_threat_lap, color="#E74C3C", linewidth=2,
                   linestyle="--", label=f"Undercut threat: Lap {result.undercut_threat_lap}")

    # Current lap
    ax.axvline(result.current_lap, color="white", linewidth=1.5,
               linestyle=":", label=f"Current: Lap {result.current_lap}")

    ax.set_xlim(0, total + 2)
    ax.set_ylim(-0.5, 0.5)
    ax.set_yticks([])
    ax.set_xlabel("Lap Number")
    ax.set_title(f"Pit Window — {result.driver}")
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(True, axis="x", alpha=0.3)

    # ── Right: reasoning text ─────────────────────────────────────────
    ax2 = axes[1]
    ax2.axis("off")

    info_lines = [
        f"Driver:          {result.driver}",
        f"Current Lap:     {result.current_lap} / {result.total_laps}",
        f"Compound:        {result.current_compound}  (age: {result.tyre_life} laps)",
        f"Position:        P{result.current_position}",
        "",
        f"Earliest Pit:    Lap {result.earliest_lap}",
        f"Optimal Pit:     Lap {result.optimal_lap}  ← recommended",
        f"Latest Pit:      Lap {result.latest_lap}",
        "",
        f"Gap Ahead:       {f'{result.gap_ahead_seconds:.2f}s' if result.gap_ahead_seconds else 'N/A'}",
        f"Gap Behind:      {f'{result.gap_behind_seconds:.2f}s' if result.gap_behind_seconds else 'N/A'}",
        f"Undercut Threat: {'Lap ' + str(result.undercut_threat_lap) if result.undercut_threat_lap else 'None'}",
        f"Overcut Viable:  {'Yes' if result.overcut_possible else 'No'}",
        "",
        "─" * 38,
        "Reasoning:",
    ] + [f"  {r}" for r in result.reasoning]

    ax2.text(0.02, 0.98, "\n".join(info_lines),
             transform=ax2.transAxes, va="top", ha="left",
             fontsize=9, fontfamily="monospace",
             color="white")

    fig.suptitle(
        f"Pit Stop Analysis — {session.event['EventName']} {session.event.year}",
        fontsize=13,
    )
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


def plot_pit_window_all(df, session, out_path):
    """Heatmap-style overview of all drivers' pit windows."""
    if df.empty:
        print("No data to plot.")
        return

    fig, ax = plt.subplots(figsize=(14, max(5, len(df) * 0.45)))

    total_laps = session.laps["LapNumber"].max()

    for i, row in df.iterrows():
        driver = row["Driver"]
        try:
            color = get_driver_color(driver, session)
        except Exception:
            color = "#888888"

        # Window bar
        width = row["LatestPit"] - row["EarliestPit"]
        ax.barh(i, width, left=row["EarliestPit"], height=0.6,
                color=color, alpha=0.7)

        # Optimal lap marker
        ax.plot(row["OptimalPit"], i, marker="|", color="#FFD700",
                markersize=18, markeredgewidth=2.5)

        # Undercut threat
        if pd.notna(row.get("UndercutThreatLap")):
            ax.plot(row["UndercutThreatLap"], i, marker="x", color="#E74C3C",
                    markersize=10, markeredgewidth=2)

        # Label
        ax.text(row["EarliestPit"] - 1, i,
                f"P{int(row['Position'])} {driver} ({row['Compound'][:1]}+{int(row['TyreAge'])})",
                va="center", ha="right", fontsize=8)

    ax.set_xlim(0, total_laps + 2)
    ax.set_yticks([])
    ax.set_xlabel("Lap Number")
    ax.set_title(
        f"Pit Windows — All Drivers — {session.event['EventName']} {session.event.year}\n"
        "│ = optimal  ✕ = undercut threat"
    )
    ax.grid(True, axis="x", alpha=0.3)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--gp", type=str, required=True)
    parser.add_argument("--driver", type=str, default=None, help="Single driver code e.g. VER")
    parser.add_argument("--all-drivers", action="store_true", help="Analyze all drivers")
    parser.add_argument("--lap", type=int, default=None, help="Lap to analyze from (default: midpoint)")
    parser.add_argument("--next-compound", type=str, default="MEDIUM",
                        help="Planned next compound: SOFT, MEDIUM, HARD (default: MEDIUM)")
    args = parser.parse_args()

    if not args.driver and not args.all_drivers:
        print("ERROR: Provide --driver VER or --all-drivers")
        sys.exit(1)

    apply_f1_style()

    print(f"Loading {args.year} {args.gp} (R)...")
    session = load_session(args.year, args.gp, "R", telemetry=False, weather=False)

    event_slug = session.event["EventName"].replace(" ", "_")
    charts_dir = OUTPUT_DIR / "charts" / f"{args.year}_{event_slug}_R"
    charts_dir.mkdir(parents=True, exist_ok=True)

    total_laps = int(session.laps["LapNumber"].max())
    analysis_lap = args.lap or total_laps // 2

    if args.all_drivers:
        print(f"Calculating pit windows for all drivers at Lap {analysis_lap}...")
        df = calculate_all_pit_windows(session, analysis_lap=analysis_lap,
                                       next_compound=args.next_compound.upper())
        print(df.to_string(index=False))

        out_path = charts_dir / f"pit_windows_all_lap{analysis_lap}.png"
        plot_pit_window_all(df, session, out_path)

        csv_path = OUTPUT_DIR / "reports" / f"{args.year}_{event_slug}_pit_windows.csv"
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(csv_path, index=False)
        print(f"\nChart saved to: {out_path}")
        print(f"CSV saved to:   {csv_path}")

    else:
        driver = args.driver.upper()
        print(f"Calculating pit window for {driver} at Lap {analysis_lap}...")
        result = calculate_pit_window(session, driver, current_lap=analysis_lap,
                                      next_compound=args.next_compound.upper())

        print(f"\n  Earliest: Lap {result.earliest_lap}")
        print(f"  Optimal:  Lap {result.optimal_lap}  ← recommended")
        print(f"  Latest:   Lap {result.latest_lap}")
        if result.undercut_threat_lap:
            print(f"  Undercut threat at: Lap {result.undercut_threat_lap}")
        print(f"  Overcut viable: {result.overcut_possible}")
        print("\nReasoning:")
        for r in result.reasoning:
            print(f"  {r}")

        out_path = charts_dir / f"pit_window_{driver}_lap{analysis_lap}.png"
        plot_pit_window_single(result, session, out_path)
        print(f"\nChart saved to: {out_path}")


if __name__ == "__main__":
    main()