import streamlit as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import pandas as pd
from pathlib import Path
from matplotlib.patches import Patch

from f1_analysis.ml import (
    LapTimePredictor, RaceFinishPredictor,
    TireCompoundClassifier, UndercutDetector,
)
from f1_analysis.ml.data_builder import SeasonDataBuilder
from f1_analysis.visualization.style import apply_f1_style

st.set_page_config(page_title="ML Predictor", page_icon="🤖", layout="wide")
st.title("🤖 Machine Learning Race Predictor")
st.markdown("Applies four ML models — lap time, finish probability, tyre identification, undercut detection — to any race in the season.")
st.info("**Before using this page:** run `py scripts/05_ml_season_models.py --year 2024 --driver VER` in your terminal to train and save the models.", icon="ℹ️")

COMPOUND_COLORS = {
    "SOFT": "#DA291C", "MEDIUM": "#FFD700", "HARD": "#FFFFFF",
    "INTERMEDIATE": "#43B02A", "WET": "#0067AD", "UNKNOWN": "#888888",
}

st.sidebar.header("Settings")
year   = st.sidebar.number_input("Year", 2018, 2026, 2024)
gp     = st.sidebar.text_input("Grand Prix", "Abu Dhabi")
driver = st.sidebar.text_input("Driver", "VER").upper()

if st.sidebar.button("Run Predictions", type="primary"):
    data_path  = Path("outputs/reports") / f"season_{year}_laps.csv"
    models_dir = Path("outputs/models") / f"{year}_{driver}"

    if not data_path.exists():
        st.error(f"Season data not found at `{data_path}`. Run Script 05 first.")
        st.stop()
    if not models_dir.exists():
        st.error(f"Models not found at `{models_dir}`. Run Script 05 first.")
        st.stop()

    with st.spinner("Loading models and running predictions..."):
        apply_f1_style()
        df_all = SeasonDataBuilder.load_csv(data_path)

        # Find the race
        events   = df_all["EventName"].unique()
        matches  = [e for e in events if gp.lower() in e.lower()]
        if not matches:
            st.error(f"'{gp}' not found. Available: {', '.join(sorted(events))}")
            st.stop()
        event_name = matches[0]
        race_laps  = df_all[(df_all["EventName"] == event_name) & (df_all["Driver"] == driver)].copy()
        if race_laps.empty:
            st.error(f"No laps for {driver} at {event_name}.")
            st.stop()

        # Load models
        models = {}
        for name, cls in [("lap_time", LapTimePredictor), ("race_finish", RaceFinishPredictor),
                           ("tire_compound", TireCompoundClassifier), ("undercut", UndercutDetector)]:
            path = models_dir / f"{name}.pkl"
            if not path.exists():
                st.error(f"Missing model: `{path}`. Re-run Script 05.")
                st.stop()
            models[name] = cls.load(path)

        # ── Run all four models ───────────────────────────────────────
        predicted_times   = models["lap_time"].predict(race_laps)
        actual_times      = race_laps["LapSeconds"].values
        deltas            = actual_times - predicted_times
        mae               = np.mean(np.abs(deltas))

        proba_df          = models["race_finish"].predict_proba(race_laps)
        predicted_cpd     = models["tire_compound"].predict(race_laps)
        actual_cpd        = race_laps["Compound"].fillna("UNKNOWN").str.upper().values
        proba_cpd         = models["tire_compound"].predict_proba(race_laps)
        accuracy          = np.mean(actual_cpd == predicted_cpd) * 100
        scored            = models["undercut"].score_laps(race_laps)
        windows           = scored[scored["WindowOpen"]]
        laps_x            = race_laps["LapNumber"].values

        actual_pos = race_laps["Position"].dropna()
        final_pos  = int(actual_pos.iloc[-1]) if not actual_pos.empty else None

    # ── TOP METRICS ROW ───────────────────────────────────────────────
    st.subheader(f"📊 {driver} — {event_name} {year}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Lap Time MAE", f"{mae:.3f}s", help="Average seconds off per lap prediction")
    c2.metric("Finish Position", f"P{final_pos}" if final_pos else "N/A")
    c3.metric("Tyre ID Accuracy", f"{accuracy:.0f}%")
    c4.metric("Undercut Windows", f"{len(windows)} laps")

    # ── CHART: Full dashboard ─────────────────────────────────────────
    fig = plt.figure(figsize=(16, 18))
    fig.patch.set_facecolor("#0f0f0f")
    fig.suptitle(f"{driver} — {event_name} {year} — ML Dashboard", color="white", fontsize=14, y=0.99)
    gs = gridspec.GridSpec(4, 2, figure=fig, hspace=0.55, wspace=0.35)

    def _style_ax(ax, title):
        ax.set_facecolor("#0f0f0f")
        ax.set_title(title, color="white", fontsize=10)
        ax.tick_params(colors="white")
        ax.xaxis.label.set_color("white")
        ax.yaxis.label.set_color("white")
        for sp in ax.spines.values(): sp.set_edgecolor("#333")
        ax.grid(True, alpha=0.25)

    # Panel 1: Lap times
    ax1 = fig.add_subplot(gs[0, :])
    ax1.plot(laps_x, actual_times, color="#E8002D", linewidth=2, label="Actual")
    ax1.plot(laps_x, predicted_times, color="#27F4D2", linewidth=2, linestyle="--", label="Predicted")
    ax1.fill_between(laps_x, actual_times, predicted_times, alpha=0.12, color="#FFD700")
    biggest = np.argsort(np.abs(deltas))[-3:]
    for idx in biggest:
        ax1.annotate(f"{deltas[idx]:+.1f}s", xy=(laps_x[idx], actual_times[idx]),
                     xytext=(laps_x[idx], actual_times[idx]+1.8),
                     fontsize=7, color="white", ha="center",
                     arrowprops=dict(arrowstyle="->", color="white", lw=0.8))
    ax1.set_xlabel("Lap"); ax1.set_ylabel("Lap Time (s)")
    ax1.legend(facecolor="#1a1a1a", labelcolor="white")
    _style_ax(ax1, f"Lap Time: Predicted vs Actual  (MAE = {mae:.3f}s)")

    # Panel 2: Finish probability
    ax2 = fig.add_subplot(gs[1, :])
    label_map = {"P(podium)": "Podium (P1-3)", "P(points)": "Points (P4-10)", "P(outside_points)": "Outside Points"}
    color_map = {"P(podium)": "#FFD700", "P(points)": "#27F4D2", "P(outside_points)": "#E8002D"}
    for col in proba_df.columns:
        ax2.plot(laps_x, proba_df[col].values, label=label_map.get(col, col),
                 color=color_map.get(col, "#888"), linewidth=2)
    ax2.set_xlabel("Lap"); ax2.set_ylabel("Probability"); ax2.set_ylim(0, 1.05)
    ax2.legend(facecolor="#1a1a1a", labelcolor="white")
    finish_label = f"Actual finish: P{final_pos}" if final_pos else ""
    _style_ax(ax2, f"Finish Probability Over Race  {finish_label}")

    # Panel 3: Compound actual vs predicted
    ax3 = fig.add_subplot(gs[2, 0])
    ax3.set_facecolor("#0f0f0f")
    for i, (actual, predicted) in enumerate(zip(actual_cpd, predicted_cpd)):
        ax3.barh(i*2+1, 1, color=COMPOUND_COLORS.get(actual, "#888"), height=0.8)
        ax3.barh(i*2,   1, color=COMPOUND_COLORS.get(predicted, "#888"), height=0.8, alpha=0.7)
    ax3.set_yticks([]); ax3.set_xticks([])
    legend_els = [Patch(facecolor=v, label=k) for k, v in COMPOUND_COLORS.items()
                  if k in set(actual_cpd) | set(predicted_cpd)]
    ax3.legend(handles=legend_els, fontsize=7, facecolor="#1a1a1a", labelcolor="white")
    ax3.set_title(f"Tyre: Top=Actual / Bottom=Predicted\nAccuracy: {accuracy:.0f}%", color="white", fontsize=10)
    for sp in ax3.spines.values(): sp.set_edgecolor("#333")

    # Panel 4: Compound probability
    ax4 = fig.add_subplot(gs[2, 1])
    for cpd in proba_cpd.columns:
        ax4.plot(laps_x, proba_cpd[cpd].values, label=cpd,
                 color=COMPOUND_COLORS.get(cpd, "#888"), linewidth=1.5)
    ax4.set_xlabel("Lap"); ax4.set_ylabel("Probability")
    ax4.legend(fontsize=8, facecolor="#1a1a1a", labelcolor="white")
    _style_ax(ax4, "Compound Probability per Lap")

    # Panel 5: Undercut windows
    ax5 = fig.add_subplot(gs[3, :])
    ax5.scatter(scored["LapNumber"], scored["UndercutScore"], s=25, alpha=0.5, color="#3671C6", label="All laps")
    if not windows.empty:
        ax5.scatter(windows["LapNumber"], windows["UndercutScore"], s=80, color="#FFD700",
                    zorder=5, label=f"Window ({len(windows)} laps)")
        for _, row in windows.iterrows():
            ax5.annotate(f"L{int(row['LapNumber'])}", xy=(row["LapNumber"], row["UndercutScore"]),
                         xytext=(row["LapNumber"]+0.5, row["UndercutScore"]+0.03), fontsize=7, color="white")
    ax5.axhline(0.6, color="#E8002D", linewidth=1.2, linestyle="--", label="Threshold")
    ax5.set_xlabel("Lap"); ax5.set_ylabel("Undercut Score"); ax5.set_ylim(0, 1.05)
    ax5.legend(facecolor="#1a1a1a", labelcolor="white")
    _style_ax(ax5, f"Undercut Windows — {len(windows)} laps flagged")

    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # ── TEXT SUMMARY ──────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("📋 Prediction Summary")

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("#### ⏱️ Lap Time Model")
        worst_idx = int(np.argmax(np.abs(deltas)))
        st.markdown(f"- **Average error:** {mae:.3f}s per lap")
        st.markdown(f"- **Biggest miss:** Lap {int(laps_x[worst_idx])} — predicted {predicted_times[worst_idx]:.2f}s, actual {actual_times[worst_idx]:.2f}s ({deltas[worst_idx]:+.2f}s)")
        st.markdown(f"- Large misses usually indicate safety car laps, traffic, or errors")

        st.markdown("#### 🏁 Finish Predictor")
        if final_pos is not None:
            final_proba = proba_df.iloc[-1]
            bucket = "Podium" if final_pos <= 3 else ("Points" if final_pos <= 10 else "Outside Points")
            st.markdown(f"- **Actual finish:** P{final_pos} ({bucket})")
            for col, prob in final_proba.items():
                label = label_map.get(col, col)
                bar = "█" * int(prob * 20) + "░" * (20 - int(prob * 20))
                st.markdown(f"- **{label}:** {prob*100:.1f}%  `{bar}`")

    with col_b:
        st.markdown("#### 🔴 Tyre Compound Classifier")
        correct = int(sum(a == p for a, p in zip(actual_cpd, predicted_cpd)))
        st.markdown(f"- **Accuracy:** {accuracy:.0f}% ({correct}/{len(actual_cpd)} laps correct)")
        wrong_laps = [int(laps_x[i]) for i in range(len(actual_cpd)) if actual_cpd[i] != predicted_cpd[i]]
        if wrong_laps:
            st.markdown(f"- **Misclassified laps:** {wrong_laps[:10]}{'...' if len(wrong_laps)>10 else ''}")
        else:
            st.markdown("- Perfect classification — no errors!")

        st.markdown("#### ⚡ Undercut Detector")
        if windows.empty:
            st.markdown("- No undercut windows detected this race")
        else:
            window_laps = sorted(windows["LapNumber"].astype(int).tolist())
            st.markdown(f"- **{len(windows)} window(s) detected** on laps: {window_laps}")
            st.markdown("- These are laps where pace was anomalously fast relative to expected compound/tyre-age baseline")
            best_window = windows.loc[windows["UndercutScore"].idxmax()]
            st.markdown(f"- **Strongest window:** Lap {int(best_window['LapNumber'])} (score: {best_window['UndercutScore']:.2f})")