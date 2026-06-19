#!/usr/bin/env python3
"""
Qualifying lap delta map.

Paints the circuit layout green/red to show where each driver gains
or loses time on their fastest qualifying lap — minisector by minisector.

Usage
-----
    py scripts/08_quali_delta.py --year 2024 --gp Monaco --driver-a LEC --driver-b VER
    py scripts/08_quali_delta.py --year 2024 --gp Silverstone --driver-a HAM --driver-b NOR
    py scripts/08_quali_delta.py --year 2023 --gp Spa --driver-a VER --driver-b PER --minisectors 30
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection

from f1_analysis.core.session_loader import load_session
from f1_analysis.core.quali_delta import compute_qualifying_delta, get_lap_time_str
from f1_analysis.visualization.style import apply_f1_style

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "outputs"


def plot_quali_delta_map(minisector_df, driver_a, driver_b, session, out_path):
    fig, axes = plt.subplots(1, 2, figsize=(18, 8))

    event_name = session.event["EventName"]
    year = session.event.year
    lap_a = get_lap_time_str(session, driver_a)
    lap_b = get_lap_time_str(session, driver_b)

    fig.suptitle(
        f"Qualifying Delta Map — {event_name} {year}\n"
        f"{driver_a} ({lap_a})  vs  {driver_b} ({lap_b})",
        fontsize=14, y=1.01,
    )

    # ── Left panel: who is faster per minisector ──────────────────────
    ax = axes[0]
    ax.set_title(f"Faster Driver per Minisector\n(green = {driver_a}, red = {driver_b})", fontsize=11)

    x = minisector_df["X"].values
    y = minisector_df["Y"].values
    faster = minisector_df["Faster"].values

    for i in range(len(x) - 1):
        color = "#27AE60" if faster[i] == driver_a else "#E74C3C"
        ax.plot([x[i], x[i + 1]], [y[i], y[i + 1]], color=color, linewidth=6, solid_capstyle="round")

    # Legend patches
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor="#27AE60", label=f"{driver_a} faster"),
        Patch(facecolor="#E74C3C", label=f"{driver_b} faster"),
    ]
    ax.legend(handles=legend_elements, loc="upper left", fontsize=10)
    ax.set_aspect("equal")
    ax.axis("off")

    # ── Right panel: delta magnitude heatmap ─────────────────────────
    ax2 = axes[1]
    ax2.set_title("Time Delta Magnitude\n(darker = bigger gap)", fontsize=11)

    delta = minisector_df["Delta"].values
    abs_delta = np.abs(delta)

    points = np.array([x, y]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)

    norm = plt.Normalize(abs_delta.min(), abs_delta.max())
    lc = LineCollection(segments, cmap="RdYlGn_r", norm=norm, linewidth=6)
    lc.set_array(abs_delta[:-1])
    ax2.add_collection(lc)

    cbar = fig.colorbar(lc, ax=ax2, fraction=0.04, pad=0.02)
    cbar.set_label("Time Gap (s)")

    ax2.set_xlim(x.min() - 200, x.max() + 200)
    ax2.set_ylim(y.min() - 200, y.max() + 200)
    ax2.set_aspect("equal")
    ax2.axis("off")

    # ── Delta bar chart below ─────────────────────────────────────────
    fig2, ax3 = plt.subplots(figsize=(14, 4))
    colors = ["#27AE60" if f == driver_a else "#E74C3C" for f in minisector_df["Faster"]]
    ax3.bar(minisector_df["MiniSector"], -minisector_df["Delta"], color=colors, width=0.8)
    ax3.axhline(0, color="white", linewidth=0.8, linestyle="--", alpha=0.5)
    ax3.set_xlabel("Minisector")
    ax3.set_ylabel(f"← {driver_b} faster  |  {driver_a} faster →")
    ax3.set_title(f"Delta by Minisector — {driver_a} vs {driver_b}")
    ax3.grid(True, axis="y", alpha=0.3)
    fig2.tight_layout()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, bbox_inches="tight")
    fig2.savefig(out_path.parent / f"quali_delta_bar_{driver_a}_vs_{driver_b}.png", bbox_inches="tight")
    plt.close("all")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--gp", type=str, required=True, help="e.g. Monaco, Silverstone, 'Abu Dhabi'")
    parser.add_argument("--driver-a", type=str, required=True, help="Reference driver (green = this driver faster)")
    parser.add_argument("--driver-b", type=str, required=True, help="Comparison driver")
    parser.add_argument("--session", type=str, default="Q", help="Session type (default: Q)")
    parser.add_argument("--minisectors", type=int, default=25, help="Number of track segments (default: 25)")
    args = parser.parse_args()

    driver_a = args.driver_a.upper()
    driver_b = args.driver_b.upper()

    apply_f1_style()

    print(f"Loading {args.year} {args.gp} ({args.session})...")
    session = load_session(args.year, args.gp, args.session, telemetry=True, weather=False)

    available = sorted(session.laps["Driver"].unique())
    for drv in [driver_a, driver_b]:
        if drv not in available:
            print(f"ERROR: '{drv}' not found. Available: {', '.join(available)}")
            sys.exit(1)

    print(f"Computing minisector delta: {driver_a} vs {driver_b} ({args.minisectors} sectors)...")
    minisector_df = compute_qualifying_delta(session, driver_a, driver_b, n_minisectors=args.minisectors)

    lap_a = get_lap_time_str(session, driver_a)
    lap_b = get_lap_time_str(session, driver_b)
    print(f"  {driver_a}: {lap_a}")
    print(f"  {driver_b}: {lap_b}")

    event_slug = session.event["EventName"].replace(" ", "_")
    charts_dir = OUTPUT_DIR / "charts" / f"{args.year}_{event_slug}_{args.session}"
    out_path = charts_dir / f"quali_delta_map_{driver_a}_vs_{driver_b}.png"

    print("Generating delta map...")
    plot_quali_delta_map(minisector_df, driver_a, driver_b, session, out_path)

    print(f"\nDone. Charts saved to: {charts_dir}")


if __name__ == "__main__":
    main()