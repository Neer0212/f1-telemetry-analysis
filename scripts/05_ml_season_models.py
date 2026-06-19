#!/usr/bin/env python3
"""
Driver-specific ML analysis across a season.

Trains all four models on a specific driver's laps from the season,
so everything is tailored to their pace, tyres, and strategy patterns
rather than averaged across all 20 drivers and 24 circuits.

Usage
-----
    python scripts/05_ml_season_models.py --year 2024 --driver VER
    python scripts/05_ml_season_models.py --year 2024 --driver LEC --max-rounds 15
    python scripts/05_ml_season_models.py --year 2024 --driver NOR --load-data outputs/reports/season_2024_laps.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd

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
    parser.add_argument("--driver", type=str, required=True, help="Driver code e.g. VER, LEC, HAM, NOR")
    parser.add_argument("--max-rounds", type=int, default=None,
                        help="Limit to first N rounds (faster for testing)")
    parser.add_argument("--load-data", type=str, default=None,
                        help="Load pre-built season CSV instead of fetching from FastF1")
    args = parser.parse_args()

    driver = args.driver.upper()
    apply_f1_style()

    models_dir = OUTPUT_DIR / "models" / f"{args.year}_{driver}"
    charts_dir = OUTPUT_DIR / "charts" / f"{args.year}_{driver}_ml"
    reports_dir = OUTPUT_DIR / "reports"
    for d in (models_dir, charts_dir, reports_dir):
        d.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------------
    # 1. Load season data (all drivers — filter to target driver after)
    # -------------------------------------------------------------------
    _section(f"Loading {args.year} season data")

    if args.load_data:
        print(f"Loading from: {args.load_data}")
        df_all = SeasonDataBuilder.load_csv(args.load_data)
    else:
        data_path = reports_dir / f"season_{args.year}_laps.csv"
        if data_path.exists():
            print(f"Found cached season CSV — loading.")
            df_all = SeasonDataBuilder.load_csv(data_path)
        else:
            print("Fetching from FastF1 (this takes a while first time)...")
            builder = SeasonDataBuilder(args.year)
            df_all = builder.build(save_path=data_path, max_rounds=args.max_rounds)

    # Filter to chosen driver
    df = df_all[df_all["Driver"] == driver].copy()
    if df.empty:
        available = sorted(df_all["Driver"].unique())
        print(f"\nERROR: Driver '{driver}' not found in season data.")
        print(f"Available drivers: {', '.join(available)}")
        sys.exit(1)

    print(f"\nDriver: {driver}")
    print(f"Laps: {len(df)} across {df['Round'].nunique()} races")
    print(f"Compounds used: {df['Compound'].dropna().unique().tolist()}")
    print(f"Avg lap time: {df['LapSeconds'].mean():.3f}s")

    # Train/test split by round (last 20% of rounds = test)
    rounds = sorted(df["Round"].unique())
    n_test = max(1, int(len(rounds) * 0.2))
    test_rounds = rounds[-n_test:]
    train_df = df[~df["Round"].isin(test_rounds)]
    test_df = df[df["Round"].isin(test_rounds)]
    test_race_names = df[df["Round"].isin(test_rounds)]["EventName"].unique().tolist()

    print(f"Training on {len(rounds) - n_test} races, testing on: {', '.join(test_race_names)}")

    report_lines = [
        f"# ML Driver Report — {driver} — {args.year} Season\n\n",
        f"**Driver:** {driver}  \n",
        f"**Season:** {args.year}  \n",
        f"**Total laps analysed:** {len(df):,}  \n",
        f"**Races trained on:** {len(rounds) - n_test}  \n",
        f"**Test races:** {', '.join(test_race_names)}  \n\n",
    ]

    # -------------------------------------------------------------------
    # 2. Lap Time Predictor
    # -------------------------------------------------------------------
    _section(f"1/4 — Lap Time Predictor for {driver}")

    lap_model = LapTimePredictor()
    lap_model.fit(train_df)
    lap_eval = lap_model.evaluate(test_df)

    print(f"MAE:          {lap_eval['mae_seconds']:.3f} s")
    print(f"R²:           {lap_eval['r2']:.4f}")
    print(f"Within 0.5s:  {lap_eval['within_0_5s_pct']:.1f}%")
    lap_model.save(models_dir / "lap_time.pkl")

    fig = plot_feature_importances(
        lap_model.feature_importances(),
        title=f"Lap Time — What drives {driver}'s pace? ({args.year})"
    )
    fig.savefig(charts_dir / "lap_time_feature_importances.png")

    compounds_used = df["Compound"].dropna().str.upper().unique()
    for compound in ("SOFT", "MEDIUM", "HARD"):
        if compound in compounds_used:
            deg = lap_model.degradation_curve(compound)
            fig = plot_degradation_curve(
                deg, compound,
                title=f"{driver} — {compound} Tyre Degradation ({args.year})"
            )
            fig.savefig(charts_dir / f"degradation_{compound.lower()}.png")

    report_lines += [
        "## 1. Lap Time Predictor\n",
        f"> Predicts {driver}'s lap time from tyre age, track temp, speed traps etc.\n\n",
        f"| Metric | Value |\n|---|---|\n",
        f"| MAE | **{lap_eval['mae_seconds']} s** |\n",
        f"| R² | **{lap_eval['r2']}** |\n",
        f"| Within 0.5s | **{lap_eval['within_0_5s_pct']}%** |\n\n",
    ]

    # -------------------------------------------------------------------
    # 3. Race Finish Predictor
    # -------------------------------------------------------------------
    _section(f"2/4 — Race Finish Predictor for {driver}")

    finish_model = RaceFinishPredictor()
    finish_model.fit(train_df)
    finish_eval = finish_model.evaluate(test_df)

    print(f"F1 (macro):    {finish_eval['f1_macro']:.4f}")
    print(f"F1 (weighted): {finish_eval['f1_weighted']:.4f}")
    print(finish_eval["classification_report"])
    finish_model.save(models_dir / "race_finish.pkl")

    fig = plot_feature_importances(
        finish_model.feature_importances(),
        title=f"Finish Predictor — What predicts {driver}'s result? ({args.year})"
    )
    fig.savefig(charts_dir / "finish_feature_importances.png")

    report_lines += [
        "## 2. Race Finish Predictor\n",
        f"> Predicts whether {driver} will finish Podium / Points / Outside Points.\n\n",
        f"| Metric | Value |\n|---|---|\n",
        f"| F1 (macro) | **{finish_eval['f1_macro']}** |\n",
        f"| F1 (weighted) | **{finish_eval['f1_weighted']}** |\n\n",
        "```\n" + finish_eval["classification_report"] + "\n```\n\n",
    ]

    # -------------------------------------------------------------------
    # 4. Tire Compound Classifier
    # -------------------------------------------------------------------
    _section(f"3/4 — Tire Compound Classifier for {driver}")

    compound_model = TireCompoundClassifier()
    compound_model.fit(train_df)
    compound_eval = compound_model.evaluate(test_df)

    print(f"F1 (macro):    {compound_eval['f1_macro']:.4f}")
    print(f"F1 (weighted): {compound_eval['f1_weighted']:.4f}")
    print(compound_eval["classification_report"])
    compound_model.save(models_dir / "tire_compound.pkl")

    fig = plot_feature_importances(
        compound_model.feature_importances(),
        title=f"Tyre Classifier — How does model identify {driver}'s compound? ({args.year})"
    )
    fig.savefig(charts_dir / "compound_feature_importances.png")

    test_clean = test_df.dropna(subset=["Compound", "Sector1Seconds"])
    test_clean = test_clean[test_clean["Compound"].str.upper().isin(
        ["SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET"]
    )]
    if not test_clean.empty:
        y_pred = compound_model.predict(test_clean)
        fig = plot_compound_confusion(test_clean["Compound"].str.upper(), y_pred)
        fig.axes[0].set_title(f"Tyre Compound Classifier — {driver} ({args.year})")
        fig.savefig(charts_dir / "compound_confusion_matrix.png")

    report_lines += [
        "## 3. Tyre Compound Classifier\n",
        f"> Identifies which tyre {driver} is on from lap data alone.\n\n",
        f"| Metric | Value |\n|---|---|\n",
        f"| F1 (macro) | **{compound_eval['f1_macro']}** |\n",
        f"| F1 (weighted) | **{compound_eval['f1_weighted']}** |\n\n",
        "```\n" + compound_eval["classification_report"] + "\n```\n\n",
    ]

    # -------------------------------------------------------------------
    # 5. Undercut Detector
    # -------------------------------------------------------------------
    _section(f"4/4 — Undercut Detector for {driver}")

    undercut_model = UndercutDetector()
    undercut_model.fit(train_df)
    undercut_eval = undercut_model.evaluate(test_df)

    print(f"Windows flagged: {undercut_eval['windows_flagged']} / {undercut_eval['total_laps']} laps "
          f"({undercut_eval['window_rate_pct']:.1f}%)")
    undercut_model.save(models_dir / "undercut.pkl")

    # Show undercut chart for each test race
    for race_name in test_race_names:
        race_laps = test_df[test_df["EventName"] == race_name]
        scored = undercut_model.score_laps(race_laps)
        fig = plot_undercut_windows(scored, event_name=f"{driver} — {race_name}")
        safe_name = race_name.replace(" ", "_").replace("/", "_")
        fig.savefig(charts_dir / f"undercut_{safe_name}.png")

    report_lines += [
        "## 4. Undercut Detector\n",
        f"> Flags laps where {driver} had an undercut opportunity.\n\n",
        f"| Metric | Value |\n|---|---|\n",
        f"| Windows flagged | **{undercut_eval['windows_flagged']}** / {undercut_eval['total_laps']} laps |\n",
        f"| Window rate | **{undercut_eval['window_rate_pct']}%** |\n",
        f"| Mean undercut score | **{undercut_eval['mean_undercut_score']}** |\n\n",
    ]

    # -------------------------------------------------------------------
    # 6. Save report
    # -------------------------------------------------------------------
    report_path = reports_dir / f"ml_report_{args.year}_{driver}.md"
    report_path.write_text("".join(report_lines), encoding="utf-8")

    _section("Done")
    print(f"Charts: {charts_dir}")
    print(f"Models: {models_dir}")
    print(f"Report: {report_path}")
    print(f"\nTip: Re-run for a different driver using cached data:")
    print(f"  py scripts/05_ml_season_models.py --year {args.year} --driver HAM --load-data outputs/reports/season_{args.year}_laps.csv")


if __name__ == "__main__":
    main()