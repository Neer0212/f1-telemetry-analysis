#!/usr/bin/env python3
"""
Single race prediction: load models trained on the season and apply
them to one specific race to see predictions vs actual results.

Requires that you've already run script 05 to build the season CSV
and train the driver models.

Usage
-----
    python scripts/06_single_race_predict.py --year 2024 --driver VER --gp "Abu Dhabi"
    python scripts/06_single_race_predict.py --year 2024 --driver NOR --gp Silverstone
    python scripts/06_single_race_predict.py --year 2025 --driver LEC --gp Monaco
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import pandas as pd

from f1_analysis.ml import (
    LapTimePredictor,
    RaceFinishPredictor,
    TireCompoundClassifier,
    UndercutDetector,
)
from f1_analysis.ml.data_builder import SeasonDataBuilder
from f1_analysis.visualization.style import apply_f1_style

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "outputs"


def _load_race_laps(df_all: pd.DataFrame, gp_name: str, driver: str) -> pd.DataFrame:
    """Find the race in the season CSV by fuzzy-matching the GP name."""
    events = df_all["EventName"].unique()
    gp_lower = gp_name.lower()
    matches = [e for e in events if gp_lower in e.lower()]
    if not matches:
        print(f"\nERROR: '{gp_name}' not found in season data.")
        print(f"Available races: {chr(10).join(sorted(events))}")
        sys.exit(1)
    event_name = matches[0]
    laps = df_all[(df_all["EventName"] == event_name) & (df_all["Driver"] == driver)]
    if laps.empty:
        print(f"\nERROR: No laps found for {driver} at {event_name}.")
        sys.exit(1)
    return laps.copy(), event_name


def _load_models(models_dir: Path) -> dict:
    """Load all four trained models."""
    models = {}
    for name, cls in [
        ("lap_time", LapTimePredictor),
        ("race_finish", RaceFinishPredictor),
        ("tire_compound", TireCompoundClassifier),
        ("undercut", UndercutDetector),
    ]:
        path = models_dir / f"{name}.pkl"
        if not path.exists():
            print(f"ERROR: Model not found: {path}")
            print(f"Run script 05 first: py scripts/05_ml_season_models.py --year <year> --driver <driver>")
            sys.exit(1)
        models[name] = cls.load(path)
    return models


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--driver", type=str, required=True)
    parser.add_argument("--gp", type=str, required=True, help="GP name, e.g. 'Monaco', 'Abu Dhabi', 'Silverstone'")
    args = parser.parse_args()

    driver = args.driver.upper()
    apply_f1_style()

    # -------------------------------------------------------------------
    # Load data and models
    # -------------------------------------------------------------------
    data_path = OUTPUT_DIR / "reports" / f"season_{args.year}_laps.csv"
    if not data_path.exists():
        print(f"ERROR: Season data not found at {data_path}")
        print(f"Run script 05 first: py scripts/05_ml_season_models.py --year {args.year} --driver {driver}")
        sys.exit(1)

    print(f"Loading season data...")
    df_all = SeasonDataBuilder.load_csv(data_path)

    race_laps, event_name = _load_race_laps(df_all, args.gp, driver)
    print(f"Race: {event_name} | Driver: {driver} | Laps: {len(race_laps)}")

    models_dir = OUTPUT_DIR / "models" / f"{args.year}_{driver}"
    print(f"Loading models from {models_dir}...")
    models = _load_models(models_dir)

    charts_dir = OUTPUT_DIR / "charts" / f"{args.year}_{driver}_ml"
    charts_dir.mkdir(parents=True, exist_ok=True)
    safe_gp = event_name.replace(" ", "_")

    # -------------------------------------------------------------------
    # Run all 4 predictions and build one combined dashboard figure
    # -------------------------------------------------------------------
    fig = plt.figure(figsize=(18, 20))
    fig.suptitle(
        f"{driver} — {event_name} {args.year}\nRace Prediction Dashboard",
        fontsize=16, y=0.98
    )
    gs = gridspec.GridSpec(4, 2, figure=fig, hspace=0.5, wspace=0.35)

    # ── Panel 1: Lap time — predicted vs actual ──────────────────────
    ax1 = fig.add_subplot(gs[0, :])  # full width
    predicted_times = models["lap_time"].predict(race_laps)
    actual_times = race_laps["LapSeconds"].values
    laps_x = race_laps["LapNumber"].values

    ax1.plot(laps_x, actual_times, color="#E8002D", linewidth=2, label="Actual lap time", zorder=3)
    ax1.plot(laps_x, predicted_times, color="#27F4D2", linewidth=2,
             linestyle="--", label="Predicted lap time", zorder=3)
    ax1.fill_between(laps_x, actual_times, predicted_times,
                     alpha=0.15, color="#FFD700", label="Gap (predicted vs actual)")

    # Annotate biggest deviations (e.g. SC laps, errors)
    deltas = actual_times - predicted_times
    biggest = np.argsort(np.abs(deltas))[-3:]
    for idx in biggest:
        ax1.annotate(
            f"+{deltas[idx]:+.1f}s",
            xy=(laps_x[idx], actual_times[idx]),
            xytext=(laps_x[idx], actual_times[idx] + 1.5),
            fontsize=7, color="white", ha="center",
            arrowprops=dict(arrowstyle="->", color="white", lw=0.8),
        )

    mae = np.mean(np.abs(deltas))
    ax1.set_xlabel("Lap Number")
    ax1.set_ylabel("Lap Time (s)")
    ax1.set_title(f"Lap Time: Predicted vs Actual  (MAE = {mae:.3f}s)")
    ax1.legend(loc="upper left")
    ax1.grid(True, alpha=0.3)

    # ── Panel 2: Finish probability over the race ─────────────────────
    ax2 = fig.add_subplot(gs[1, :])
    proba_df = models["race_finish"].predict_proba(race_laps)
    for col in proba_df.columns:
        label_map = {
            "P(podium)": "Podium (P1-3)",
            "P(points)": "Points (P4-10)",
            "P(outside_points)": "Outside Points (P11+)",
        }
        color_map = {
            "P(podium)": "#FFD700",
            "P(points)": "#27F4D2",
            "P(outside_points)": "#E8002D",
        }
        ax2.plot(
            race_laps["LapNumber"].values,
            proba_df[col].values,
            label=label_map.get(col, col),
            color=color_map.get(col, "#888888"),
            linewidth=2,
        )

    # Show actual finish position
    actual_pos = race_laps["Position"].dropna()
    if not actual_pos.empty:
        final_pos = int(actual_pos.iloc[-1])
        bucket = "Podium" if final_pos <= 3 else ("Points" if final_pos <= 10 else "Outside Points")
        ax2.set_title(f"Finish Probability Over Race  (Actual finish: P{final_pos} — {bucket})")
    else:
        ax2.set_title("Finish Probability Over Race")

    ax2.set_xlabel("Lap Number")
    ax2.set_ylabel("Probability")
    ax2.set_ylim(0, 1.05)
    ax2.legend(loc="upper right")
    ax2.grid(True, alpha=0.3)

    # ── Panel 3: Tyre compound — predicted vs actual ──────────────────
    ax3 = fig.add_subplot(gs[2, 0])
    predicted_compounds = models["tire_compound"].predict(race_laps)
    actual_compounds = race_laps["Compound"].fillna("UNKNOWN").str.upper().values
    compound_colors = {
        "SOFT": "#DA291C", "MEDIUM": "#FFD700", "HARD": "#FFFFFF",
        "INTERMEDIATE": "#43B02A", "WET": "#0067AD", "UNKNOWN": "#888888",
    }
    laps_list = race_laps["LapNumber"].values
    for i, (lap, actual, predicted) in enumerate(zip(laps_list, actual_compounds, predicted_compounds)):
        ax3.barh(i * 2 + 1, 1, color=compound_colors.get(actual, "#888"), edgecolor="none", height=0.8)
        ax3.barh(i * 2, 1, color=compound_colors.get(predicted, "#888"), edgecolor="none", height=0.8,
                 alpha=0.7)

    accuracy = np.mean(actual_compounds == predicted_compounds) * 100
    ax3.set_yticks([])
    ax3.set_xticks([])
    ax3.set_title(f"Tyre Compound\nTop=Actual / Bottom=Predicted  (Accuracy: {accuracy:.0f}%)")

    # Legend patches
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor=v, label=k) for k, v in compound_colors.items()
                       if k in set(actual_compounds) | set(predicted_compounds)]
    ax3.legend(handles=legend_elements, loc="lower right", fontsize=7)

    # ── Panel 4: Tyre compound probability breakdown ──────────────────
    ax4 = fig.add_subplot(gs[2, 1])
    proba_compound = models["tire_compound"].predict_proba(race_laps)
    for compound in proba_compound.columns:
        ax4.plot(
            race_laps["LapNumber"].values,
            proba_compound[compound].values,
            label=compound,
            color=compound_colors.get(compound, "#888"),
            linewidth=1.5,
        )
    ax4.set_xlabel("Lap Number")
    ax4.set_ylabel("Probability")
    ax4.set_title("Compound Probability\nper Lap")
    ax4.legend(fontsize=8)
    ax4.grid(True, alpha=0.3)

    # ── Panel 5: Undercut windows ─────────────────────────────────────
    ax5 = fig.add_subplot(gs[3, :])
    scored = models["undercut"].score_laps(race_laps)
    windows = scored[scored["WindowOpen"]]

    ax5.scatter(scored["LapNumber"], scored["UndercutScore"],
                s=30, alpha=0.5, color="#3671C6", label="All laps")
    if not windows.empty:
        ax5.scatter(windows["LapNumber"], windows["UndercutScore"],
                    s=80, color="#FFD700", zorder=5, label=f"Undercut window ({len(windows)} laps)")
    ax5.axhline(0.6, color="red", linewidth=1.2, linestyle="--", label="Threshold (0.6)")

    # Annotate window laps
    for _, row in windows.iterrows():
        ax5.annotate(
            f"Lap {int(row['LapNumber'])}",
            xy=(row["LapNumber"], row["UndercutScore"]),
            xytext=(row["LapNumber"] + 0.5, row["UndercutScore"] + 0.03),
            fontsize=7, color="white",
        )

    ax5.set_xlabel("Lap Number")
    ax5.set_ylabel("Undercut Score")
    ax5.set_ylim(0, 1.05)
    ax5.set_title(f"Undercut Windows  ({len(windows)} flagged)")
    ax5.legend()
    ax5.grid(True, alpha=0.3)

    # -------------------------------------------------------------------
    # Save dashboard
    # -------------------------------------------------------------------
    out_path = charts_dir / f"race_dashboard_{safe_gp}.png"
    fig.savefig(out_path, dpi=150)
    plt.close(fig)

    # -------------------------------------------------------------------
    # Print summary to terminal
    # -------------------------------------------------------------------
    print(f"\n{'='*60}")
    print(f"  RACE PREDICTION SUMMARY")
    print(f"  {driver} — {event_name} {args.year}")
    print(f"{'='*60}")

    print(f"\n📊 Lap Time Predictor")
    print(f"   MAE: {mae:.3f}s  (avg error per lap)")
    worst_lap = race_laps.iloc[np.argmax(np.abs(deltas))]
    print(f"   Biggest miss: Lap {int(worst_lap['LapNumber'])} "
          f"(predicted {predicted_times[np.argmax(np.abs(deltas))]:.2f}s, "
          f"actual {actual_times[np.argmax(np.abs(deltas))]:.2f}s)")

    print(f"\n🏁 Finish Predictor")
    if not actual_pos.empty:
        final_pos = int(actual_pos.iloc[-1])
        final_proba = proba_df.iloc[-1]
        print(f"   Actual finish: P{final_pos}")
        for col, prob in final_proba.items():
            print(f"   {col}: {prob*100:.1f}%")

    print(f"\n🟡 Tyre Compound Classifier")
    print(f"   Accuracy this race: {accuracy:.0f}%")
    correct = sum(a == p for a, p in zip(actual_compounds, predicted_compounds))
    print(f"   Correct: {correct}/{len(actual_compounds)} laps")

    print(f"\n⚡ Undercut Detector")
    print(f"   Windows flagged: {len(windows)} laps")
    if not windows.empty:
        print(f"   Lap numbers: {sorted(windows['LapNumber'].astype(int).tolist())}")

    print(f"\n✅ Dashboard saved to: {out_path}")


if __name__ == "__main__":
    main()