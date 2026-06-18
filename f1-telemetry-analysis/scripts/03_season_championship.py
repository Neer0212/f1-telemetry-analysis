#!/usr/bin/env python3
"""
Season analysis: championship progression for drivers and constructors.

Builds round-by-round standings for an entire season and charts how the
championship battle evolved. Also saves the raw standings data to CSV
so repeated runs don't need to re-fetch from Ergast.

Usage
-----
    python scripts/03_season_championship.py --year 2024
    python scripts/03_season_championship.py --year 2023 --top-n 5 --up-to-round 15
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from f1_analysis.core.season import (
    build_driver_standings_progression,
    build_team_standings_progression,
)
from f1_analysis.visualization.style import apply_f1_style
from f1_analysis.visualization.plots import plot_championship_progression

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "outputs"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--up-to-round", type=int, default=None, help="Only build through this round")
    parser.add_argument("--top-n", type=int, default=8, help="Limit driver chart to top N by final points")
    args = parser.parse_args()

    apply_f1_style()

    charts_dir = OUTPUT_DIR / "charts" / f"{args.year}_season"
    data_dir = OUTPUT_DIR / "reports" / f"{args.year}_season_data"
    charts_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    print(f"Fetching driver standings progression for {args.year}... (one request per round)")
    driver_standings = build_driver_standings_progression(args.year, up_to_round=args.up_to_round)
    driver_standings.to_csv(data_dir / "driver_standings.csv", index=False)

    print(f"Fetching constructor standings progression for {args.year}...")
    team_standings = build_team_standings_progression(args.year, up_to_round=args.up_to_round)
    team_standings.to_csv(data_dir / "constructor_standings.csv", index=False)

    print("Generating driver championship chart...")
    fig = plot_championship_progression(
        driver_standings,
        entity_column="DriverCode",
        top_n=args.top_n,
        title=f"{args.year} Drivers' Championship Progression",
    )
    fig.savefig(charts_dir / "driver_championship.png")

    print("Generating constructor championship chart...")
    fig = plot_championship_progression(
        team_standings,
        entity_column="Constructor",
        title=f"{args.year} Constructors' Championship Progression",
    )
    fig.savefig(charts_dir / "constructor_championship.png")

    print(f"\nDone. Charts saved to: {charts_dir}")
    print(f"Raw standings data saved to: {data_dir}")


if __name__ == "__main__":
    main()
