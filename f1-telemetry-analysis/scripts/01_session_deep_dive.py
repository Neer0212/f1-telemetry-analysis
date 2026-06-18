#!/usr/bin/env python3
"""
Single-session deep dive: lap times, race pace, and tire strategy.

Loads one session and produces a set of charts plus a Markdown report
covering fastest laps, race pace consistency, and tire strategy.

Usage
-----
    python scripts/01_session_deep_dive.py --year 2024 --gp Monza --session R
    python scripts/01_session_deep_dive.py --year 2023 --gp "Abu Dhabi" --session Q --drivers VER LEC HAM

If --drivers is omitted, the 6 drivers with the fastest single lap in the
session are used (use --top-n to change the count).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from f1_analysis.core.session_loader import load_session
from f1_analysis.core.lap_analysis import fastest_laps_by_driver, clean_lap_times
from f1_analysis.reports.session_report import generate_session_report
from f1_analysis.visualization.style import apply_f1_style
from f1_analysis.visualization.plots import (
    plot_lap_time_distribution,
    plot_race_pace,
    plot_tire_strategy,
)

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "outputs"


def pick_default_drivers(session, n: int = 6) -> list[str]:
    """Pick a sensible default set of drivers: fastest n by best lap time."""
    clean = clean_lap_times(session.laps)
    fastest = fastest_laps_by_driver(clean)
    return fastest["Driver"].head(n).tolist()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, required=True, help="Season year, e.g. 2024")
    parser.add_argument("--gp", type=str, required=True, help="Grand Prix name or round number")
    parser.add_argument("--session", type=str, default="R", help="Session identifier: FP1/FP2/FP3/Q/S/R")
    parser.add_argument("--drivers", type=str, nargs="*", default=None, help="Driver codes, e.g. VER HAM LEC")
    parser.add_argument(
        "--top-n", type=int, default=6, help="Number of drivers to auto-select if --drivers is omitted"
    )
    args = parser.parse_args()

    apply_f1_style()

    print(f"Loading {args.year} {args.gp} ({args.session})...")
    session = load_session(args.year, args.gp, args.session)

    drivers = args.drivers or pick_default_drivers(session, n=args.top_n)
    print(f"Analyzing drivers: {', '.join(drivers)}")

    event_slug = session.event["EventName"].replace(" ", "_")
    charts_dir = OUTPUT_DIR / "charts" / f"{args.year}_{event_slug}_{args.session}"
    charts_dir.mkdir(parents=True, exist_ok=True)

    print("Generating lap time distribution chart...")
    fig = plot_lap_time_distribution(session, drivers)
    fig.savefig(charts_dir / "lap_time_distribution.png")

    print("Generating race pace chart...")
    fig = plot_race_pace(session, drivers)
    fig.savefig(charts_dir / "race_pace.png")

    print("Generating tire strategy chart...")
    fig = plot_tire_strategy(session, drivers=drivers)
    fig.savefig(charts_dir / "tire_strategy.png")

    print("Generating Markdown report...")
    reports_dir = OUTPUT_DIR / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / f"{args.year}_{event_slug}_{args.session}_report.md"
    generate_session_report(session, output_path=report_path)

    print(f"\nDone. Charts saved to: {charts_dir}")
    print(f"Report saved to: {report_path}")


if __name__ == "__main__":
    main()
