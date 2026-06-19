#!/usr/bin/env python3
"""
Train all four ML models on a season's race data and generate analysis charts.

Fetches lap data for every completed race in the season (via FastF1),
trains the four models, evaluates each one, and saves charts plus a
Markdown summary of all model results.

This script is intentionally designed to run end-to-end: run it once
and it produces everything. Subsequent runs are fast because FastF1
caches session data locally.

Usage
-----
    python scripts/05_ml_season_models.py --year 2024
    python scripts/05_ml_season_models.py --year 2023 --max-rounds 10
    python scripts/05_ml_season_models.py --year 2024 --load-data outputs/season_2024_laps.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from f1_analysis.ml import (
    SeasonDataBuilder,
    LapTimePredictor,
    RaceFinishPredictor,
    TireCompoundClassifier,
    UndercutDetector,
)
from f1_analysis.visualization.style import apply_f1_style
from f1_analysis.visualization.plots import (
    plot_feature_importances,
    plot_degradation_curve,
    plot_undercut_windows,
    plot_compound_confusion,
)

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "outputs"


def _section(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, required=True, help="Season year, e.g. 2024")
    parser.add_argument("--max-rounds", type=int, default=None,
                        help="Limit to first N rounds (faster for testing)")
    parser.add_argument("--load-data", type=str, default=None,
                        help="Load pre-built season CSV instead of fetching from FastF1")
    parser.add_argument("--test-size", type=float, default=0.2,
                        help="Fraction of data held out for evaluation (default 0.2)")
    args = parser.parse_args()

    apply_f1_style()

    models_dir = OUTPUT_DIR / "models"
    charts_dir = OUTPUT_DIR / "charts" / f"{args.year}_ml"
    reports_dir = OUTPUT_DIR / "reports"
    for d in (models_dir, charts_dir, reports_dir):
        d.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------------
    # 1. Build or load season lap data
    # -------------------------------------------------------------------
    _section(f"Building season data for {args.year}")

    if args.load_data:
        print(f"Loading from: {args.load_data}")
        df = SeasonDataBuilder.load_csv(args.load_data)
    else:
        data_path = reports_dir / f"season_{args.year}_laps.csv"
        if data_path.exists():
            print(f"Found cached season CSV: {data_path} — loading.")
            df = SeasonDataBuilder.load_csv(data_path)
        else:
            builder = SeasonDataBuilder(args.year)
            df = builder.build(save_path=data_path, max_rounds=args.max_rounds)

    print(f"Total laps: {len(df):,}  |  Rounds: {df['Round'].nunique()}  |  Drivers: {df['Driver'].nunique()}")

    # Train / test split (split by round to avoid data leakage across races)
    rounds = df["Round"].unique()
    n_test_rounds = max(1, int(len(rounds) * args.test_size))
    test_rounds = sorted(rounds)[-n_test_rounds:]
    train_df = df[~df["Round"].isin(test_rounds)]
    test_df = df[df["Round"].isin(test_rounds)]
    print(f"Train: {len(train_df):,} laps ({len(rounds) - n_test_rounds} rounds) | "
          f"Test: {len(test_df):,} laps ({n_test_rounds} rounds)")

    report_lines = [
        f"# ML Model Report — {args.year} Season\n",
        f"Training rounds: {len(rounds) - n_test_rounds} | Test rounds: {n_test_rounds}\n",
        f"Total laps: {len(df):,}\n\n",
    ]

    # -------------------------------------------------------------------
    # 2. Lap Time Predictor
    # -------------------------------------------------------------------
    _section("1/4 — Lap Time Predictor (Regression)")

    lap_model = LapTimePredictor()
    lap_model.fit(train_df)
    lap_eval = lap_model.evaluate(test_df)
    print(f"MAE: {lap_eval['mae_seconds']:.3f}s | R²: {lap_eval['r2']:.4f} | "
          f"Within 0.5s: {lap_eval['within_0_5s_pct']:.1f}%")

    lap_model.save(models_dir / f"lap_time_{args.year}.pkl")

    fi = lap_model.feature_importances()
    fig = plot_feature_importances(fi, title=f"Lap Time Predictor — Feature Importances ({args.year})")
    fig.savefig(charts_dir / "lap_time_feature_importances.png")

    for compound in ("SOFT", "MEDIUM", "HARD"):
        deg = lap_model.degradation_curve(compound)
        fig = plot_degradation_curve(deg, compound,
                                     title=f"{compound} Degradation — {args.year} Season Model")
        fig.savefig(charts_dir / f"degradation_{compound.lower()}.png")

    report_lines += [
        "## 1. Lap Time Predictor\n",
        f"- MAE: **{lap_eval['mae_seconds']} s**\n",
        f"- R²: **{lap_eval['r2']}**\n",
        f"- Within 0.5 s: **{lap_eval['within_0_5s_pct']}%**\n",
        f"- Test samples: {lap_eval['n_samples']:,}\n\n",
    ]

    # -------------------------------------------------------------------
    # 3. Race Finish Predictor
    # -------------------------------------------------------------------
    _section("2/4 — Race Finish Predictor (Classification)")

    finish_model = RaceFinishPredictor()
    finish_model.fit(train_df)
    finish_eval = finish_model.evaluate(test_df)
    print(f"F1 (macro): {finish_eval['f1_macro']:.4f} | F1 (weighted): {finish_eval['f1_weighted']:.4f}")
    print(finish_eval["classification_report"])

    finish_model.save(models_dir / f"race_finish_{args.year}.pkl")

    fi = finish_model.feature_importances()
    fig = plot_feature_importances(fi, title=f"Race Finish Predictor — Feature Importances ({args.year})")
    fig.savefig(charts_dir / "finish_feature_importances.png")

    report_lines += [
        "## 2. Race Finish Predictor\n",
        f"- F1 (macro): **{finish_eval['f1_macro']}**\n",
        f"- F1 (weighted): **{finish_eval['f1_weighted']}**\n",
        "```\n" + finish_eval["classification_report"] + "\n```\n\n",
    ]

    # -------------------------------------------------------------------
    # 4. Tire Compound Classifier
    # -------------------------------------------------------------------
    _section("3/4 — Tire Compound Classifier")

    compound_model = TireCompoundClassifier()
    compound_model.fit(train_df)
    compound_eval = compound_model.evaluate(test_df)
    print(f"F1 (macro): {compound_eval['f1_macro']:.4f} | F1 (weighted): {compound_eval['f1_weighted']:.4f}")
    print(compound_eval["classification_report"])

    compound_model.save(models_dir / f"tire_compound_{args.year}.pkl")

    fi = compound_model.feature_importances()
    fig = plot_feature_importances(fi, title=f"Tire Classifier — Feature Importances ({args.year})")
    fig.savefig(charts_dir / "compound_feature_importances.png")

    # Confusion matrix on test set
    test_clean = test_df.dropna(subset=["Compound", "Sector1Seconds"])
    test_clean = test_clean[test_clean["Compound"].str.upper().isin(
        ["SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET"]
    )]
    if not test_clean.empty:
        y_pred = compound_model.predict(test_clean)
        fig = plot_compound_confusion(test_clean["Compound"].str.upper(), y_pred)
        fig.savefig(charts_dir / "compound_confusion_matrix.png")

    report_lines += [
        "## 3. Tire Compound Classifier\n",
        f"- F1 (macro): **{compound_eval['f1_macro']}**\n",
        f"- F1 (weighted): **{compound_eval['f1_weighted']}**\n",
        "```\n" + compound_eval["classification_report"] + "\n```\n\n",
    ]

    # -------------------------------------------------------------------
    # 5. Undercut Detector
    # -------------------------------------------------------------------
    _section("4/4 — Undercut Window Detector")

    undercut_model = UndercutDetector()
    undercut_model.fit(train_df)
    undercut_eval = undercut_model.evaluate(test_df)
    print(f"Windows flagged: {undercut_eval['windows_flagged']} / {undercut_eval['total_laps']} laps "
          f"({undercut_eval['window_rate_pct']:.1f}%)")
    if undercut_eval["top_rounds_by_windows"]:
        print("Top races by undercut windows:", undercut_eval["top_rounds_by_windows"])

    undercut_model.save(models_dir / f"undercut_{args.year}.pkl")

    # Show undercut map for the last test race
    if "EventName" in test_df.columns:
        last_race = test_df[test_df["Round"] == test_df["Round"].max()]
        event_name = last_race["EventName"].iloc[0]
        scored = undercut_model.score_laps(last_race)
        fig = plot_undercut_windows(scored, event_name=event_name)
        fig.savefig(charts_dir / "undercut_windows_last_race.png")
        print(f"Undercut window chart saved for: {event_name}")

    report_lines += [
        "## 4. Undercut Detector\n",
        f"- Windows flagged: **{undercut_eval['windows_flagged']}** / {undercut_eval['total_laps']} laps\n",
        f"- Window rate: **{undercut_eval['window_rate_pct']}%**\n",
        f"- Mean undercut score: **{undercut_eval['mean_undercut_score']}**\n",
    ]
    if undercut_eval["top_rounds_by_windows"]:
        report_lines.append("- Top races by windows:\n")
        for race, count in undercut_eval["top_rounds_by_windows"].items():
            report_lines.append(f"  - {race}: {count} windows\n")
    report_lines.append("\n")

    # -------------------------------------------------------------------
    # 6. Save report
    # -------------------------------------------------------------------
    report_path = reports_dir / f"ml_report_{args.year}.md"
    report_path.write_text("".join(report_lines), encoding="utf-8")

    _section("Done")
    print(f"Charts: {charts_dir}")
    print(f"Models: {models_dir}")
    print(f"Report: {report_path}")


if __name__ == "__main__":
    main()
