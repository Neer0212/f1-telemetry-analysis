import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

st.set_page_config(page_title="ML Predictions · F1 Analytics", page_icon="🤖", layout="wide")

from f1_analysis.visualization.ui_theme import inject_f1_css, page_header, section_label, metrics_row
inject_f1_css()
page_header("🤖", "Machine Learning", "Race Predictions",
            "Four trained models: lap time prediction, podium probability, tyre compound classification, and undercut detection.")

# -- original page logic preserved, just wrapped in new theme --
from f1_analysis.core.session_loader import load_session
from f1_analysis.ml.data_builder import build_lap_features
from f1_analysis.ml.lap_time import LapTimePredictor
from f1_analysis.ml.race_finish import RaceFinishPredictor
from f1_analysis.ml.tire_compound import TireCompoundClassifier
from f1_analysis.ml.undercut import UndercutDetector
from f1_analysis.visualization.style import apply_f1_style
import pandas as pd
import matplotlib.pyplot as plt

with st.sidebar:
    st.markdown("### ⚙️ Settings")
    year   = st.number_input("Year", 2018, 2026, 2023)
    gp     = st.text_input("Grand Prix", "Bahrain")
    driver = st.text_input("Driver", "VER").upper()
    run    = st.button("Run Models", type="primary")

if run:
    with st.spinner("Loading session and building features…"):
        apply_f1_style()
        session  = load_session(year, gp, "R", telemetry=False, weather=False)
        features = build_lap_features(session)

    if features.empty:
        st.error("No feature data available for this session.")
        st.stop()

    driver_feats = features[features["Driver"] == driver] if "Driver" in features.columns else features

    st.markdown('<div style="padding:0 2.5rem;">', unsafe_allow_html=True)
    tabs = st.tabs(["⏱ Lap Time", "🏆 Race Finish", "🔵 Tyre Compound", "📉 Undercut"])

    with tabs[0]:
        section_label("Lap Time Predictor")
        try:
            model = LapTimePredictor()
            model.train(features)
            preds = model.predict(driver_feats)
            fig, ax = plt.subplots(figsize=(13, 4))
            fig.patch.set_facecolor("#0D0D0D"); ax.set_facecolor("#0D0D0D")
            ax.plot(preds.index, preds.values, color="#E8002D", linewidth=2, label="Predicted")
            if "LapTime" in driver_feats.columns:
                actual = driver_feats["LapTime"].dt.total_seconds() if hasattr(driver_feats["LapTime"], "dt") else driver_feats["LapTime"]
                ax.plot(actual.index, actual.values, color="#27F4D2", linewidth=1.5, linestyle="--", label="Actual")
            ax.legend(facecolor="#1A1A1A", labelcolor="white", fontsize=8)
            ax.set_xlabel("Lap", color="#888"); ax.set_ylabel("Lap Time (s)", color="#888")
            ax.set_title(f"{driver} — Predicted vs Actual Lap Times", color="white", fontsize=10)
            ax.tick_params(colors="#888"); ax.grid(True, alpha=0.12, color="#FFFFFF")
            for sp in ax.spines.values(): sp.set_edgecolor("#2A2A2A")
            fig.tight_layout(); st.pyplot(fig, use_container_width=True); plt.close(fig)
        except Exception as e:
            st.error(f"Lap time model error: {e}")

    with tabs[1]:
        section_label("Race Finish Predictor")
        try:
            model = RaceFinishPredictor()
            model.train(features)
            proba = model.predict_proba(driver_feats)
            if proba is not None:
                st.metric("Podium Probability", f"{float(proba.max()):.1%}")
        except Exception as e:
            st.error(f"Race finish model error: {e}")

    with tabs[2]:
        section_label("Tyre Compound Classifier")
        try:
            model = TireCompoundClassifier()
            model.train(features)
            preds = model.predict(driver_feats)
            st.dataframe(pd.DataFrame({"Lap": range(len(preds)), "Predicted Compound": preds}),
                         use_container_width=True)
        except Exception as e:
            st.error(f"Tyre model error: {e}")

    with tabs[3]:
        section_label("Undercut Detector")
        try:
            model = UndercutDetector()
            model.train(features)
            flags = model.predict(driver_feats)
            windows = [i for i, f in enumerate(flags) if f]
            if windows:
                metrics_row([{"label": "Undercut Windows Detected", "value": str(len(windows)), "color": "accent"}])
                st.write("Laps with undercut opportunity:", windows)
            else:
                st.info("No undercut windows detected for this driver in this race.")
        except Exception as e:
            st.error(f"Undercut model error: {e}")

    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.markdown("""
<div style="padding:4rem 2.5rem; text-align:center; color:#333;
            font-family:'Titillium Web',sans-serif; font-size:0.8rem;
            text-transform:uppercase; letter-spacing:0.15em;">
    Configure race parameters in the sidebar and press Run Models
</div>""", unsafe_allow_html=True)