#!/usr/bin/env python3
"""
Driver head-to-head: telemetry overlay for two drivers' fastest laps.

Produces a speed trace overlay, a cumulative time-delta chart, and a
throttle/brake comparison -- the classic "qualifying battle" analysis
showing exactly where on track one driver gains or loses time.

Usage
-----
    python scripts/02_driver_head_to_head.py --year 2024 --gp Monza --session Q --driver-a VER --driver-b LEC
    python scripts/02_driver_head_to_head.py --year 2023 --gp Spa --session R --driver-a HAM --driver-b ALO --lap-a 32 --lap-b 32
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from f1_analysis.core.session_loader import load_session
from f1_analysis.core.telemetry import compare_driver_telemetry
from f1_analysis.visualization.style import apply_f1_style
from f1_analysis.visualization.plots import (
    plot_speed_trace_comparison,
    plot_telemetry_delta,
    plot_throttle_brake_comparison,
)

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "outputs"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--gp", type=str, required=True)
    parser.add_argument("--session", type=str, default="Q")
    parser.add_argument("--driver-a", type=str, required=True)
    parser.add_argument("--driver-b", type=str, required=True)
    parser.add_argument("--lap-a", type=int, default=None, help="Specific lap number for driver A (default: fastest)")
    parser.add_argument("--lap-b", type=int, default=None, help="Specific lap number for driver B (default: fastest)")
    args = parser.parse_args()

    apply_f1_style()

    print(f"Loading {args.year} {args.gp} ({args.session})...")
    session = load_session(args.year, args.gp, args.session)

    print(f"Comparing {args.driver_a} vs {args.driver_b}...")
    comparison = compare_driver_telemetry(
        session, args.driver_a, args.driver_b, lap_a=args.lap_a, lap_b=args.lap_b
    )

    event_slug = session.event["EventName"].replace(" ", "_")
    charts_dir = OUTPUT_DIR / "charts" / f"{args.year}_{event_slug}_{args.session}_h2h_{args.driver_a}_{args.driver_b}"
    charts_dir.mkdir(parents=True, exist_ok=True)

    print("Generating speed trace comparison...")
    fig = plot_speed_trace_comparison(comparison, session)
    fig.savefig(charts_dir / "speed_trace.png")

    print("Generating time delta chart...")
    fig = plot_telemetry_delta(comparison, session)
    fig.savefig(charts_dir / "time_delta.png")

    print("Generating throttle/brake comparison...")
    fig = plot_throttle_brake_comparison(comparison, session)
    fig.savefig(charts_dir / "throttle_brake.png")

    final_delta = comparison.delta_time["Delta"].iloc[-1]
    leader = args.driver_a if final_delta > 0 else args.driver_b
    print(f"\n{leader} was faster by {abs(final_delta):.3f}s over the lap.")
    print(f"Charts saved to: {charts_dir}")


if __name__ == "__main__":
    main()
