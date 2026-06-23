import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

st.set_page_config(page_title="Head to Head · F1 Analytics", page_icon="⚔️", layout="wide")

from f1_analysis.visualization.ui_theme import inject_f1_css, page_header, section_label, metrics_row, sidebar_nav
from f1_analysis.core.session_loader import load_session
from f1_analysis.core.telemetry import compare_driver_telemetry
from f1_analysis.visualization.style import apply_f1_style
from f1_analysis.visualization.plots import plot_speed_trace_comparison, plot_telemetry_delta, plot_throttle_brake_comparison

inject_f1_css()
sidebar_nav()
page_header("⚔️", "Telemetry Comparison", "Head-to-Head",
            "Speed traces, time deltas, and throttle/brake overlays. See exactly where one driver gains or loses time.")

with st.sidebar:
    st.markdown("### ⚙️ Comparison Settings")
    year         = st.number_input("Year", 2018, 2026, 2024)
    gp           = st.text_input("Grand Prix", "Monza")
    session_type = st.selectbox("Session", ["Q","R","S"])
    col1, col2   = st.columns(2)
    driver_a     = col1.text_input("Driver A", "VER").upper()
    driver_b     = col2.text_input("Driver B", "LEC").upper()
    run = st.button("Compare", type="primary")

if run:
    with st.spinner(f"Loading telemetry — {driver_a} vs {driver_b}…"):
        apply_f1_style()
        session    = load_session(year, gp, session_type)
        comparison = compare_driver_telemetry(session, driver_a, driver_b)

    final_delta = comparison.delta_time["Delta"].iloc[-1]
    faster      = driver_a if final_delta > 0 else driver_b
    slower      = driver_b if final_delta > 0 else driver_a
    gap         = abs(final_delta)

    metrics_row([
        {"label": "Faster Driver",   "value": faster,       "color": "teal"},
        {"label": "Gap",             "value": f"{gap:.3f}s","color": "accent"},
        {"label": "Slower Driver",   "value": slower},
        {"label": "Session",         "value": session_type},
        {"label": "Grand Prix",      "value": session.event["EventName"]},
    ])

    st.markdown('<div style="padding:0 2.5rem;">', unsafe_allow_html=True)
    section_label("Speed Trace Comparison")
    st.pyplot(plot_speed_trace_comparison(comparison, session), use_container_width=True)

    section_label("Time Delta")
    st.pyplot(plot_telemetry_delta(comparison, session), use_container_width=True)

    section_label("Throttle & Brake")
    st.pyplot(plot_throttle_brake_comparison(comparison, session), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.markdown("""
<div style="padding:4rem 2.5rem; text-align:center; color:#333;
            font-family:'Titillium Web',sans-serif; font-size:0.8rem;
            text-transform:uppercase; letter-spacing:0.15em;">
    Select two drivers and a session in the sidebar, then press Compare
</div>""", unsafe_allow_html=True)