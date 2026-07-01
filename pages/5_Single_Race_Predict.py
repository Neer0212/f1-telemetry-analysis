import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
st.set_page_config(page_title="ML Predictions - F1 Analytics", page_icon="F1", layout="wide", initial_sidebar_state="collapsed")
from f1_analysis.visualization.ui_theme import inject_f1_css, top_nav, page_header, control_panel, section_label, metrics_row, insight_box
inject_f1_css()
top_nav("Predictions")
page_header("A", "Machine Learning", "Race Predictions",
    "Four trained models: lap time prediction, podium probability, tyre compound classification, and undercut detection.")

clicked, vals = control_panel([
    {"type":"number","label":"Year","key":"ml_year","default":2023,"min":2018,"max":2025},
    {"type":"text",  "label":"Grand Prix","key":"ml_gp","default":"Bahrain"},
    {"type":"text",  "label":"Driver","key":"ml_driver","default":"VER"},
], button_label="Run Models", cols_per_row=4)

if clicked:
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    from f1_analysis.core.session_loader import load_session
    from f1_analysis.ml.data_builder import SeasonDataBuilder
    from f1_analysis.ml.lap_time import LapTimePredictor
    from f1_analysis.ml.race_finish import RaceFinishPredictor
    from f1_analysis.ml.tire_compound import TireCompoundClassifier
    from f1_analysis.ml.undercut import UndercutDetector
    from f1_analysis.visualization.style import apply_f1_style
    driver = vals["ml_driver"].upper()
    with st.spinner("Loading race data..."):
        apply_f1_style()
        try:
            session = load_session(vals["ml_year"], vals["ml_gp"], "R", telemetry=False, weather=True)
        except Exception as e:
            st.error("Failed to load session: " + str(e)); st.stop()
    with st.spinner("Building features..."):
        try:
            builder = SeasonDataBuilder(year=vals["ml_year"])
            laps = session.laps.copy()
            if laps.empty:
                st.error("No lap data available."); st.stop()
            features = builder._extract_laps(session, round_num=1, event_name=session.event["EventName"])
            if features is None or features.empty:
                st.error("Could not extract features."); st.stop()
            features = SeasonDataBuilder._engineer_features(features)
        except Exception as e:
            st.error("Feature building failed: " + str(e)); st.stop()
    driver_feats = features[features["Driver"] == driver].copy() if "Driver" in features.columns else features.copy()
    if driver_feats.empty:
        available = sorted(features["Driver"].unique()) if "Driver" in features.columns else []
        st.error("Driver " + driver + " not found. Available: " + str(available)); st.stop()
    event_name = session.event["EventName"]
    metrics_row([
        {"label":"Driver","value":driver,"color":"accent"},
        {"label":"Grand Prix","value":event_name},
        {"label":"Year","value":str(vals["ml_year"])},
        {"label":"Laps","value":str(len(driver_feats))},
    ])
    st.markdown('<div style="padding:0 2.5rem 4rem;">', unsafe_allow_html=True)
    tabs = st.tabs(["Lap Time", "Race Finish", "Tyre Compound", "Undercut"])
    with tabs[0]:
        section_label("Lap Time Predictor")
        try:
            model = LapTimePredictor(); model.train(features)
            preds = model.predict(driver_feats)
            lap_col = "LapSeconds" if "LapSeconds" in driver_feats.columns else None
            actual  = driver_feats[lap_col].dropna() if lap_col else None
            fig, ax = plt.subplots(figsize=(13, 4))
            fig.patch.set_facecolor("#0D0D0D"); ax.set_facecolor("#0D0D0D")
            ax.plot(range(len(preds)), preds, color="#E8002D", linewidth=2, label="Predicted")
            if actual is not None and len(actual) == len(preds):
                ax.plot(range(len(actual)), actual.values, color="#27F4D2", linewidth=1.5, linestyle="--", label="Actual")
            ax.legend(facecolor="#1A1A1A", labelcolor="white", fontsize=8)
            ax.set_xlabel("Lap", color="#888"); ax.set_ylabel("Lap Time (s)", color="#888")
            ax.tick_params(colors="#888"); ax.grid(True, alpha=0.1, color="#FFF")
            for sp in ax.spines.values(): sp.set_edgecolor("#2A2A2A")
            fig.tight_layout(); st.pyplot(fig, use_container_width=True); plt.close(fig)
            insight_box("M", "Reading the Lap Time Prediction",
                "The red line shows what the model predicted each lap time would be, based on tyre age, stint number, "
                "and track conditions. The teal dashed line is the actual recorded lap time. Where they closely match, "
                "the model understood the conditions well. Big gaps usually mean a safety car, an out-lap after a pit stop, "
                "or an unusual event the model could not account for.")
        except Exception as e:
            st.error("Lap time model error: " + str(e))
    with tabs[1]:
        section_label("Race Finish Predictor")
        try:
            model = RaceFinishPredictor(); model.train(features)
            proba = model.predict_proba(driver_feats)
            if proba is not None:
                podium_prob = float(np.max(proba))
                metrics_row([{"label":"Podium Probability","value":"{:.1%}".format(podium_prob),"color":"teal" if podium_prob>0.5 else "accent"}])
                insight_box("P", "Reading the Podium Probability",
                    "This estimates the probability of a podium finish based on lap pace, position changes, and tyre life "
                    "seen during this race. Above 50 percent means the model sees a podium as the expected outcome. "
                    "Below 25 percent means a podium would be a surprise result given the data.")
        except Exception as e:
            st.error("Race finish model error: " + str(e))
    with tabs[2]:
        section_label("Tyre Compound Classifier")
        try:
            model = TireCompoundClassifier(); model.train(features)
            preds = model.predict(driver_feats)
            compound_map = {0:"SOFT",1:"MEDIUM",2:"HARD",3:"INTERMEDIATE",4:"WET",5:"UNKNOWN"}
            pred_labels = [compound_map.get(int(p), str(p)) if str(p).isdigit() else str(p) for p in preds]
            st.dataframe(pd.DataFrame({"Lap": range(1, len(pred_labels)+1), "Predicted Compound": pred_labels}), use_container_width=True)
            insight_box("C", "Reading the Tyre Compound Classifier",
                "This model tries to identify which tyre compound was fitted based purely on pace patterns, not by "
                "reading the compound label directly. It learns that Soft tyres are fast early but degrade quickly, "
                "while Hard tyres are slower initially but hold pace longer. Mismatches often happen when a compound "
                "is pushed well beyond its normal expected life.")
        except Exception as e:
            st.error("Tyre model error: " + str(e))
    with tabs[3]:
        section_label("Undercut Detector")
        try:
            model = UndercutDetector(); model.train(features)
            flags = model.predict(driver_feats)
            windows = [i+1 for i, f in enumerate(flags) if f]
            if windows:
                metrics_row([{"label":"Undercut Windows","value":str(len(windows)),"color":"accent"}])
                st.write("Laps: " + str(windows))
                insight_box("U", "Reading Undercut Windows",
                    "An undercut is when a driver pits before a rival, fits fresh tyres, and uses the pace advantage "
                    "to jump ahead once the rival also stops. These laps show significantly better pace than the recent "
                    "average, suggesting fresh tyre grip. An undercut works best when the gap to the car ahead is under "
                    "roughly two seconds.")
            else:
                st.info("No undercut windows detected.")
                insight_box("U", "Undercut Analysis",
                    "No undercut windows were found for this driver in this race. This usually means gaps to nearby "
                    "cars were too large for an undercut to work, or the driver's strategy was already close to optimal.")
        except Exception as e:
            st.error("Undercut model error: " + str(e))
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.markdown('<div style="padding:5rem 2.5rem;text-align:center;font-family:Titillium Web,sans-serif;font-size:0.8rem;text-transform:uppercase;letter-spacing:0.15em;color:#2A2A2A;">Configure parameters above and press Run Models</div>', unsafe_allow_html=True)