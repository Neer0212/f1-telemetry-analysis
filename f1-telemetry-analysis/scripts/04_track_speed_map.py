#!/usr/bin/env python3
"""
Track speed map: visualize a driver's speed around the full circuit.

Draws the track outline colored by speed at every point on a chosen
lap (default: the driver's fastest lap in the session). A quick,
visually striking way to spot where a driver is fastest/slowest.

Usage
-----
    python scripts/04_track_speed_map.py --year 2024 --gp Monaco --session Q --driver LEC
    python scripts/04_track_speed_map.py --year 2024 --gp Spa --session R --driver VER --lap 10
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from f1_analysis.core.session_loader import load_session
from f1_analysis.core.telemetry import get_driver_telemetry
from f1_analysis.visualization.style import apply_f1_style
from f1_analysis.visualization.plots import plot_track_speed_map

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "outputs"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--gp", type=str, required=True)
    parser.add_argument("--session", type=str, default="Q")
    parser.add_argument("--driver", type=str, required=True)
    parser.add_argument("--lap", type=int, default=None, help="Specific lap number (default: fastest)")
    args = parser.parse_args()

    apply_f1_style()

    print(f"Loading {args.year} {args.gp} ({args.session})...")
    session = load_session(args.year, args.gp, args.session)

    print(f"Pulling telemetry for {args.driver}...")
    telemetry = get_driver_telemetry(session, args.driver, lap_number=args.lap)

    event_slug = session.event["EventName"].replace(" ", "_")
    charts_dir = OUTPUT_DIR / "charts" / f"{args.year}_{event_slug}_{args.session}"
    charts_dir.mkdir(parents=True, exist_ok=True)

    print("Generating speed map...")
    fig = plot_track_speed_map(telemetry, session, args.driver)
    out_path = charts_dir / f"speed_map_{args.driver}.png"
    fig.savefig(out_path)

    print(f"\nDone. Saved to: {out_path}")


if __name__ == "__main__":
    main()
