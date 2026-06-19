#!/usr/bin/env python3
"""
Multi-season driver comparison.

Three modes:
  1. One driver at the same circuit across multiple seasons
  2. Two drivers head-to-head at the same circuit across multiple seasons
  3. One driver's performance heatmap across all circuits in a season

Usage
-----
    # VER at Monaco across 4 seasons
    py scripts/10_multi_season.py --mode single --driver VER --gp Monaco --years 2021 2022 2023 2024

    # VER vs LEC head-to-head qualifying at Monaco
    py scripts/10_multi_season.py --mode h2h --driver-a VER --driver-b LEC --gp Monaco --years 2022 2023 2024

    # NOR's gap to pole at every circuit in 2024
    py scripts/10_multi_season.py --mode heatmap --driver NOR --year 2024
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from f1_analysis.core.multi_season import (
    compare_driver_across_seasons,
    compare_two_drivers_across_seasons,
    driver_circuit_heatmap_data,
)
from f1_analysis.visualization.style import apply_f1_style

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "outputs"


def plot_single_driver(df, driver, gp, session_type, out_path):
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    years = df["Year"].values
    best_laps = df["BestLapSeconds"].values
    mean_laps = df["MeanLapSeconds"].values
    teammate_gaps = df["TeammateGapSeconds"].values

    # ── Left: best lap trend ──────────────────────────────────────────
    ax = axes[0]
    ax.plot(years, best_laps, marker="o", color="#3671C6", linewidth=2.5,
            markersize=8, label="Best Lap")
    ax.plot(years, mean_laps, marker="s", color="#E8002D", linewidth=2,
            markersize=6, linestyle="--", label="Mean Lap")

    for i, (y, v) in enumerate(zip(years, best_laps)):
        team = df["Team"].iloc[i] or ""
        ax.annotate(f"{v:.2f}s\n{team}", (y, v),
                    textcoords="offset points", xytext=(0, 12),
                    ha="center", fontsize=8)

    ax.set_xticks(years)
    ax.set_xlabel("Year")
    ax.set_ylabel("Lap Time (s)")
    ax.set_title(f"{driver} at {gp} — Lap Times by Season")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # ── Right: teammate gap ───────────────────────────────────────────
    ax2 = axes[1]
    valid = ~pd.isna(teammate_gaps)
    if valid.any():
        colors = ["#27AE60" if g < 0 else "#E74C3C" for g in teammate_gaps[valid]]
        bars = ax2.bar(years[valid], teammate_gaps[valid], color=colors, width=0.5)
        ax2.axhline(0, color="white", linewidth=1, linestyle="--")

        for bar, val in zip(bars, teammate_gaps[valid]):
            ax2.text(bar.get_x() + bar.get_width() / 2,
                     val + (0.03 if val >= 0 else -0.06),
                     f"{val:+.3f}s", ha="center", fontsize=9)

        ax2.set_xticks(years[valid])
        ax2.set_xlabel("Year")
        ax2.set_ylabel("Gap vs Teammate Best Lap (s)")
        ax2.set_title(f"{driver} vs Teammate — Gap by Season\n(green = driver faster)")
        ax2.grid(True, axis="y", alpha=0.3)
    else:
        ax2.axis("off")
        ax2.text(0.5, 0.5, "No teammate gap data available",
                 ha="center", va="center", transform=ax2.transAxes)

    fig.suptitle(f"{driver} at {gp} — Multi-Season Comparison", fontsize=13)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


def plot_h2h(df, driver_a, driver_b, gp, out_path):
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    years = df["Year"].values
    col_a = f"{driver_a}_BestLap"
    col_b = f"{driver_b}_BestLap"

    # ── Left: raw lap times ───────────────────────────────────────────
    ax = axes[0]
    ax.plot(years, df[col_a], marker="o", color="#3671C6", linewidth=2.5,
            markersize=8, label=driver_a)
    ax.plot(years, df[col_b], marker="s", color="#E8002D", linewidth=2.5,
            markersize=8, label=driver_b)
    ax.set_xticks(years)
    ax.set_xlabel("Year")
    ax.set_ylabel("Best Lap (s)")
    ax.set_title(f"Best Lap — {driver_a} vs {driver_b} at {gp}")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # ── Right: gap bar chart ──────────────────────────────────────────
    ax2 = axes[1]
    gaps = df["Gap_AminusB"].values
    colors = ["#27AE60" if g < 0 else "#E74C3C" for g in gaps]
    bars = ax2.bar(years, gaps, color=colors, width=0.5)
    ax2.axhline(0, color="white", linewidth=1, linestyle="--")

    for bar, val, faster in zip(bars, gaps, df["Faster"]):
        ax2.text(bar.get_x() + bar.get_width() / 2,
                 val + (0.02 if val >= 0 else -0.05),
                 f"{val:+.3f}s\n({faster})", ha="center", fontsize=8)

    ax2.set_xticks(years)
    ax2.set_xlabel("Year")
    ax2.set_ylabel(f"Gap: {driver_a} minus {driver_b} (s)")
    ax2.set_title(f"Qualifying Gap — green = {driver_a} faster, red = {driver_b} faster")
    ax2.grid(True, axis="y", alpha=0.3)

    fig.suptitle(f"{driver_a} vs {driver_b} at {gp} — Multi-Season", fontsize=13)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


def plot_heatmap(df, driver, year, out_path):
    if df.empty:
        print("No data to plot.")
        return

    df_sorted = df.sort_values("Round")
    gaps = df_sorted["GapToSessionBest"].values
    circuits = [c.replace(" Grand Prix", "").replace(" ", "\n") for c in df_sorted["Circuit"]]

    colors = ["#27AE60" if g <= 0.001 else
              "#F39C12" if g <= 0.3 else
              "#E74C3C" for g in gaps]

    fig, ax = plt.subplots(figsize=(max(14, len(circuits) * 0.7), 5))
    bars = ax.bar(range(len(circuits)), gaps, color=colors, width=0.7)

    for bar, val in zip(bars, gaps):
        ax.text(bar.get_x() + bar.get_width() / 2,
                val + 0.005,
                f"+{val:.3f}s" if val > 0 else "POLE",
                ha="center", va="bottom", fontsize=7,
                rotation=45)

    ax.set_xticks(range(len(circuits)))
    ax.set_xticklabels(circuits, fontsize=8)
    ax.set_ylabel("Gap to Session Fastest (s)")
    ax.set_title(f"{driver} — Gap to Session Best at Each Circuit — {year}\n"
                 "(green = pole/fastest, orange = within 0.3s, red = further back)")
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["single", "h2h", "heatmap"], required=True)
    parser.add_argument("--driver", type=str, help="Driver code (single/heatmap mode)")
    parser.add_argument("--driver-a", type=str, help="Driver A (h2h mode)")
    parser.add_argument("--driver-b", type=str, help="Driver B (h2h mode)")
    parser.add_argument("--gp", type=str, help="Grand Prix name (single/h2h mode)")
    parser.add_argument("--years", type=int, nargs="+", help="Years e.g. 2021 2022 2023 2024")
    parser.add_argument("--year", type=int, help="Single year (heatmap mode)")
    parser.add_argument("--session", type=str, default="Q", help="Session type (default: Q)")
    parser.add_argument("--max-rounds", type=int, default=None, help="Limit rounds (heatmap mode)")
    args = parser.parse_args()

    apply_f1_style()
    charts_dir = OUTPUT_DIR / "charts" / "multi_season"
    charts_dir.mkdir(parents=True, exist_ok=True)
    reports_dir = OUTPUT_DIR / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    if args.mode == "single":
        if not args.driver or not args.gp or not args.years:
            print("ERROR: --mode single requires --driver, --gp, and --years")
            sys.exit(1)
        driver = args.driver.upper()
        print(f"Comparing {driver} at {args.gp} across {args.years}...")
        df = compare_driver_across_seasons(driver, args.years, args.gp, args.session)
        if df.empty:
            print("No data found.")
            sys.exit(1)
        print(df.to_string(index=False))
        df.to_csv(reports_dir / f"multi_season_{driver}_{args.gp.replace(' ', '_')}.csv", index=False)
        out_path = charts_dir / f"single_{driver}_{args.gp.replace(' ', '_')}.png"
        plot_single_driver(df, driver, args.gp, args.session, out_path)
        print(f"\nChart saved to: {out_path}")

    elif args.mode == "h2h":
        if not args.driver_a or not args.driver_b or not args.gp or not args.years:
            print("ERROR: --mode h2h requires --driver-a, --driver-b, --gp, and --years")
            sys.exit(1)
        da, db = args.driver_a.upper(), args.driver_b.upper()
        print(f"Comparing {da} vs {db} at {args.gp} across {args.years}...")
        df = compare_two_drivers_across_seasons(da, db, args.years, args.gp, args.session)
        if df.empty:
            print("No data found.")
            sys.exit(1)
        print(df.to_string(index=False))
        df.to_csv(reports_dir / f"h2h_{da}_vs_{db}_{args.gp.replace(' ', '_')}.csv", index=False)
        out_path = charts_dir / f"h2h_{da}_vs_{db}_{args.gp.replace(' ', '_')}.png"
        plot_h2h(df, da, db, args.gp, out_path)
        print(f"\nChart saved to: {out_path}")

    elif args.mode == "heatmap":
        if not args.driver or not args.year:
            print("ERROR: --mode heatmap requires --driver and --year")
            sys.exit(1)
        driver = args.driver.upper()
        print(f"Building circuit heatmap for {driver} in {args.year}...")
        df = driver_circuit_heatmap_data(driver, args.year, args.session, args.max_rounds)
        if df.empty:
            print("No data found.")
            sys.exit(1)
        print(df.to_string(index=False))
        df.to_csv(reports_dir / f"heatmap_{driver}_{args.year}.csv", index=False)
        out_path = charts_dir / f"heatmap_{driver}_{args.year}.png"
        plot_heatmap(df, driver, args.year, out_path)
        print(f"\nChart saved to: {out_path}")


if __name__ == "__main__":
    main()