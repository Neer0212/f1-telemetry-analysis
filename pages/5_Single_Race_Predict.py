import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import Patch
import numpy as np
import pandas as pd

st.set_page_config(page_title="ML Predictions · F1 Analytics", page_icon="🤖", layout="wide")

from f1_analysis.visualization.ui_theme import inject_f1_css, page_header, section_label, metrics_row
inject_f1_css()
page_header("🤖", "Machine Learning", "Race Predictions",
            "Four trained models: lap time prediction, podium probability, tyre compound classification, and undercut detection.")

from f1_analysis.ml.data_builder import SeasonDataBuilder
from f1_analysis.ml.lap_time import LapTimePredictor
from f1_analysis.ml.race_finish import RaceFinishPredictor
from f1_analysis.ml.tire_compound import TireCompoundClassifier
from f1_analysis.ml.undercut import UndercutDetector
from f1_analysis.visualization.style import apply_f1_style

EXPLAIN = """<div style="background:#141414;border:1px solid #2A2A2A;border-left:3px solid #E8002D;
padding:.9rem 1.2rem;margin:.8rem 0 1.2rem;color:#aaa;font-size:.88rem;line-height:1.65;
font-family:'Inter',sans-serif;">{text}</div>"""

INSIGHT = """<div style="background:#0D0D0D;border:1px solid #2A2A2A;border-top:2px solid #E8002D;
padding:1rem 1.3rem;margin-top:1rem;font-family:'Inter',sans-serif;">
<div style="font-family:'Titillium Web',sans-serif;font-size:.65rem;font-weight:700;
text-transform:uppercase;letter-spacing:.2em;color:#E8002D;margin-bottom:.6rem;">Key Insights</div>
{text}</div>"""

COMPOUND_COLORS = {
    "SOFT":"#DA291C","MEDIUM":"#FFD700","HARD":"#FFFFFF",
    "INTERMEDIATE":"#43B02A","WET":"#0067AD","UNKNOWN":"#888888",
}

with st.sidebar:
    st.markdown("### ⚙️ Settings")
    st.info("Run `scripts/05_ml_season_models.py` first to generate model files.", icon="ℹ️")
    year   = st.number_input("Year", 2018, 2026, 2024)
    gp     = st.text_input("Grand Prix", "Abu Dhabi")
    driver = st.text_input("Driver", "VER").upper()
    run    = st.button("Run Predictions", type="primary")

if run:
    data_path  = Path("outputs/reports") / f"season_{year}_laps.csv"
    models_dir = Path("outputs/models") / f"{year}_{driver}"

    if not data_path.exists():
        st.error(f"Season data not found at `{data_path}`. Run Script 05 first."); st.stop()
    if not models_dir.exists():
        st.error(f"Models not found at `{models_dir}`. Run Script 05 first."); st.stop()

    with st.spinner("Loading models and running all four predictions..."):
        apply_f1_style()
        df_all = SeasonDataBuilder.load_csv(data_path)

        events  = df_all["EventName"].unique()
        matches = [e for e in events if gp.lower() in e.lower()]
        if not matches:
            st.error(f"'{gp}' not found. Available: {', '.join(sorted(events))}"); st.stop()

        event_name = matches[0]
        race_laps  = df_all[(df_all["EventName"] == event_name) & (df_all["Driver"] == driver)].copy()
        if race_laps.empty:
            st.error(f"No laps for {driver} at {event_name}."); st.stop()

        models = {}
        for name, cls in [("lap_time", LapTimePredictor), ("race_finish", RaceFinishPredictor),
                           ("tire_compound", TireCompoundClassifier), ("undercut", UndercutDetector)]:
            p = models_dir / f"{name}.pkl"
            if not p.exists():
                st.error(f"Missing model: `{p}`. Re-run Script 05."); st.stop()
            models[name] = cls.load(p)

        predicted_times = models["lap_time"].predict(race_laps)
        actual_times    = race_laps["LapSeconds"].values
        deltas          = actual_times - predicted_times
        mae             = np.mean(np.abs(deltas))

        proba_df    = models["race_finish"].predict_proba(race_laps)
        pred_cpd    = models["tire_compound"].predict(race_laps)
        actual_cpd  = race_laps["Compound"].fillna("UNKNOWN").str.upper().values
        proba_cpd   = models["tire_compound"].predict_proba(race_laps)
        accuracy    = np.mean(actual_cpd == pred_cpd) * 100
        scored      = models["undercut"].score_laps(race_laps)
        windows     = scored[scored["WindowOpen"]]
        laps_x      = race_laps["LapNumber"].values

        actual_pos  = race_laps["Position"].dropna()
        final_pos   = int(actual_pos.iloc[-1]) if not actual_pos.empty else None

    metrics_row([
        {"label":f"{driver} — {event_name}","value":str(year),"color":"accent"},
        {"label":"Lap Time MAE","value":f"{mae:.3f}s"},
        {"label":"Finish Position","value":f"P{final_pos}" if final_pos else "—","color":"gold"},
        {"label":"Tyre ID Accuracy","value":f"{accuracy:.0f}%","color":"teal"},
        {"label":"Undercut Windows","value":str(len(windows))},
    ])

    st.markdown("<div style='padding:0 2rem'>", unsafe_allow_html=True)

    def _ax(ax, title):
        ax.set_facecolor("#0D0D0D")
        ax.set_title(title, color="#fff", fontsize=10, fontweight="bold")
        ax.tick_params(colors="#888")
        ax.xaxis.label.set_color("#888"); ax.yaxis.label.set_color("#888")
        for sp in ax.spines.values(): sp.set_edgecolor("#2A2A2A")
        ax.grid(True, alpha=0.12, color="#fff", linewidth=0.5)

    # ── CHART 1: LAP TIME ─────────────────────────────────────────────
    section_label("Lap Time — Predicted vs Actual")
    st.markdown(EXPLAIN.format(text="""
<strong>What this shows:</strong> The <strong style="color:#E8002D">red line</strong> is the driver's
actual lap time every lap. The <strong style="color:#27F4D2">teal dashed line</strong> is what the
model predicted based on tyre compound, tyre age, lap number, and weather. The
<strong>yellow shaded area</strong> between them shows where the model was wrong.
<strong>Large gaps upward</strong> (actual much slower than predicted) = safety car, traffic, or error.
<strong>Large gaps downward</strong> (actual faster) = driver pushing harder than expected.
"""), unsafe_allow_html=True)

    fig, ax = plt.subplots(figsize=(14, 4))
    fig.patch.set_facecolor("#0D0D0D")
    ax.plot(laps_x, actual_times, color="#E8002D", linewidth=2, label="Actual")
    ax.plot(laps_x, predicted_times, color="#27F4D2", linewidth=2, linestyle="--", label="Predicted")
    ax.fill_between(laps_x, actual_times, predicted_times, alpha=0.12, color="#FFD700")
    biggest = np.argsort(np.abs(deltas))[-3:]
    for idx in biggest:
        ax.annotate(f"{deltas[idx]:+.1f}s", xy=(laps_x[idx], actual_times[idx]),
                    xytext=(laps_x[idx], actual_times[idx]+2),
                    fontsize=7, color="#fff", ha="center",
                    arrowprops=dict(arrowstyle="->", color="#888", lw=0.7))
    ax.set_xlabel("Lap"); ax.set_ylabel("Lap Time (s)")
    ax.legend(facecolor="#1A1A1A", labelcolor="white", fontsize=9)
    _ax(ax, f"Lap Time: Predicted vs Actual  (MAE = {mae:.3f}s)")
    fig.tight_layout(); st.pyplot(fig, use_container_width=True); plt.close(fig)

    worst_idx = int(np.argmax(np.abs(deltas)))
    st.markdown(INSIGHT.format(text=f"""
<ul style="margin:.4rem 0;padding-left:1.2rem;color:#ccc;font-size:.85rem;line-height:1.8;">
<li><strong style="color:#fff">Average prediction error: {mae:.3f}s per lap</strong>
— within 0.4s is excellent for a model with no real-time data.</li>
<li><strong>Biggest miss:</strong> Lap {int(laps_x[worst_idx])} — predicted
{predicted_times[worst_idx]:.2f}s, actual {actual_times[worst_idx]:.2f}s ({deltas[worst_idx]:+.2f}s).
This is likely a safety car lap, heavy traffic, or an unplanned push lap.</li>
<li>The model uses: tyre compound, tyre age, lap fraction, speed trap readings, and weather data.
It cannot see traffic, incidents, or driver intent — which explains most large errors.</li>
</ul>"""), unsafe_allow_html=True)

    # ── CHART 2: FINISH PROBABILITY ───────────────────────────────────
    section_label("Race Finish Probability")
    st.markdown(EXPLAIN.format(text="""
<strong>What this shows:</strong> The probability (0–100%) that the driver will finish
<strong style="color:#FFD700">on the podium (P1-3)</strong>,
<strong style="color:#27F4D2">in the points (P4-10)</strong>, or
<strong style="color:#E8002D">outside the points (P11+)</strong>, lap by lap through the race.
When the podium line jumps up sharply, the model sees the driver gaining positions or improving pace.
When it drops, something went wrong — safety car lost positions, pit stop, or falling behind rivals.
"""), unsafe_allow_html=True)

    label_map  = {"P(podium)":"Podium (P1–3)","P(points)":"Points (P4–10)","P(outside_points)":"Outside Points"}
    color_map  = {"P(podium)":"#FFD700","P(points)":"#27F4D2","P(outside_points)":"#E8002D"}
    fig, ax = plt.subplots(figsize=(14, 4))
    fig.patch.set_facecolor("#0D0D0D")
    for col in proba_df.columns:
        ax.plot(laps_x, proba_df[col].values, label=label_map.get(col, col),
                color=color_map.get(col, "#888"), linewidth=2)
    ax.set_xlabel("Lap"); ax.set_ylabel("Probability"); ax.set_ylim(0, 1.05)
    ax.legend(facecolor="#1A1A1A", labelcolor="white", fontsize=9)
    finish_label = f"Actual finish: P{final_pos}" if final_pos else ""
    _ax(ax, f"Finish Probability Over Race  {finish_label}")
    fig.tight_layout(); st.pyplot(fig, use_container_width=True); plt.close(fig)

    if final_pos is not None:
        bucket = "Podium" if final_pos <= 3 else ("Points" if final_pos <= 10 else "Outside Points")
        final_proba = proba_df.iloc[-1]
        proba_lines = "".join([
            f"<li>{label_map.get(c,c)}: <strong>{v*100:.1f}%</strong></li>"
            for c, v in final_proba.items()
        ])
        st.markdown(INSIGHT.format(text=f"""
<ul style="margin:.4rem 0;padding-left:1.2rem;color:#ccc;font-size:.85rem;line-height:1.8;">
<li><strong style="color:#fff">Actual finish: P{final_pos} ({bucket})</strong></li>
<li>Final lap probabilities: {proba_lines}</li>
<li>The model classifies into three buckets rather than exact position — F1 races are too chaotic
(retirements, safety cars) for exact position prediction to be reliable.</li>
</ul>"""), unsafe_allow_html=True)

    # ── CHART 3 & 4: TYRE ────────────────────────────────────────────
    section_label("Tyre Compound Classification")
    st.markdown(EXPLAIN.format(text="""
<strong>What this shows:</strong> The model tries to <em>identify which tyre compound the driver is
on</em> just from their speed readings and sector times — without seeing the compound label itself.
This reveals what signals actually distinguish a Soft from a Hard tyre in the data.
<strong>Left chart:</strong> actual compound (top bar) vs model's prediction (bottom bar) per lap — colours match tyre type.
<strong>Right chart:</strong> probability the model assigns to each compound lap by lap.
"""), unsafe_allow_html=True)

    fig, axes = plt.subplots(1, 2, figsize=(14, 4))
    fig.patch.set_facecolor("#0D0D0D")
    ax3, ax4 = axes

    ax3.set_facecolor("#0D0D0D")
    for i, (actual, predicted) in enumerate(zip(actual_cpd, pred_cpd)):
        ax3.barh(i*2+1, 1, color=COMPOUND_COLORS.get(actual,"#888"), height=0.8)
        ax3.barh(i*2,   1, color=COMPOUND_COLORS.get(predicted,"#888"), height=0.8, alpha=0.7)
    ax3.set_yticks([]); ax3.set_xticks([])
    legend_els = [Patch(facecolor=v, label=k) for k, v in COMPOUND_COLORS.items()
                  if k in set(actual_cpd) | set(pred_cpd)]
    ax3.legend(handles=legend_els, fontsize=7, facecolor="#1A1A1A", labelcolor="white")
    ax3.set_title(f"Top=Actual / Bottom=Predicted  (Accuracy: {accuracy:.0f}%)",
                  color="#fff", fontsize=9, fontweight="bold")
    for sp in ax3.spines.values(): sp.set_edgecolor("#2A2A2A")

    for cpd in proba_cpd.columns:
        ax4.plot(laps_x, proba_cpd[cpd].values, label=cpd,
                 color=COMPOUND_COLORS.get(cpd,"#888"), linewidth=1.5)
    ax4.set_xlabel("Lap"); ax4.set_ylabel("Probability")
    ax4.legend(fontsize=8, facecolor="#1A1A1A", labelcolor="white")
    _ax(ax4, "Compound Probability per Lap")

    fig.tight_layout(); st.pyplot(fig, use_container_width=True); plt.close(fig)

    correct   = int(sum(a == p for a, p in zip(actual_cpd, pred_cpd)))
    wrong_laps= [int(laps_x[i]) for i in range(len(actual_cpd)) if actual_cpd[i] != pred_cpd[i]]
    st.markdown(INSIGHT.format(text=f"""
<ul style="margin:.4rem 0;padding-left:1.2rem;color:#ccc;font-size:.85rem;line-height:1.8;">
<li><strong style="color:#fff">Accuracy: {accuracy:.0f}% ({correct}/{len(actual_cpd)} laps correct)</strong></li>
{"<li><strong>Misclassified laps:</strong> " + str(wrong_laps[:10]) + ("..." if len(wrong_laps)>10 else "") + " — these are usually the first 1-2 laps of a stint when the tyre is still being worked in.</li>"
if wrong_laps else "<li>✅ Perfect classification — the compound was correctly identified on every lap.</li>"}
<li>High accuracy means the tyre compound leaves a clear signature in speed and sector time data.</li>
</ul>"""), unsafe_allow_html=True)

    # ── CHART 5: UNDERCUT ────────────────────────────────────────────
    section_label("Undercut Opportunity Detection")
    st.markdown(EXPLAIN.format(text="""
<strong>What this shows:</strong> Every lap gets an <strong>undercut score</strong> (0–1).
The score combines an anomaly detection algorithm (Isolation Forest) with domain rules:
is the driver going faster than expected for their tyre age and compound?
A score above <strong>0.6</strong> (the red dashed threshold) = the model flags this as a
potential undercut window — a lap where pitting and gaining the fresh-tyre speed advantage
could allow overtaking a rival during their pit stop.
"""), unsafe_allow_html=True)

    fig, ax = plt.subplots(figsize=(14, 4))
    fig.patch.set_facecolor("#0D0D0D")
    ax.scatter(scored["LapNumber"], scored["UndercutScore"],
               s=25, alpha=0.5, color="#3671C6", label="All laps")
    if not windows.empty:
        ax.scatter(windows["LapNumber"], windows["UndercutScore"],
                   s=80, color="#FFD700", zorder=5, label=f"Window ({len(windows)} laps)")
        for _, row in windows.iterrows():
            ax.annotate(f"L{int(row['LapNumber'])}",
                        xy=(row["LapNumber"], row["UndercutScore"]),
                        xytext=(row["LapNumber"]+0.5, row["UndercutScore"]+0.03),
                        fontsize=7, color="#fff")
    ax.axhline(0.6, color="#E8002D", linewidth=1.2, linestyle="--", label="Threshold (0.6)")
    ax.set_xlabel("Lap"); ax.set_ylabel("Undercut Score"); ax.set_ylim(0, 1.05)
    ax.legend(facecolor="#1A1A1A", labelcolor="white", fontsize=9)
    _ax(ax, f"Undercut Windows — {len(windows)} laps flagged")
    fig.tight_layout(); st.pyplot(fig, use_container_width=True); plt.close(fig)

    if windows.empty:
        uc_text = "<li>No undercut windows detected — the driver's pace was consistent with tyre age expectations throughout the race.</li>"
    else:
        best_w = windows.loc[windows["UndercutScore"].idxmax()]
        wlaps  = sorted(windows["LapNumber"].astype(int).tolist())
        uc_text = f"""
<li><strong style="color:#fff">{len(windows)} window(s) detected</strong> on laps: {wlaps}</li>
<li><strong>Strongest window:</strong> Lap {int(best_w['LapNumber'])} (score: {best_w['UndercutScore']:.2f})</li>
<li>These are laps where the driver was going <em>anomalously fast</em> for their tyre age —
suggesting a fresh-tyre advantage that a rival could have exploited by pitting just before.</li>"""

    st.markdown(INSIGHT.format(text=f"<ul style='margin:.4rem 0;padding-left:1.2rem;color:#ccc;font-size:.85rem;line-height:1.8;'>{uc_text}</ul>"), unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

else:
    st.markdown("""
<div style="text-align:center;padding:4rem 2rem;color:#333;
font-family:'Titillium Web',sans-serif;font-size:.8rem;font-weight:700;
text-transform:uppercase;letter-spacing:.2em;">
Run scripts/05_ml_season_models.py first, then enter year, grand prix and driver, then press Run Predictions
</div>""", unsafe_allow_html=True)
