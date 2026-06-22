import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

st.set_page_config(page_title="Session Deep Dive · F1 Analytics", page_icon="📊", layout="wide")

from f1_analysis.visualization.ui_theme import inject_f1_css, page_header, section_label, metrics_row
from f1_analysis.core.session_loader import load_session
from f1_analysis.core.lap_analysis import fastest_laps_by_driver, clean_lap_times
from f1_analysis.visualization.style import apply_f1_style
from f1_analysis.visualization.plots import plot_lap_time_distribution, plot_race_pace, plot_tire_strategy

inject_f1_css()
page_header("📊", "Analysis Tool", "Session Deep Dive",
            "Lap time distributions, race pace consistency, and tyre strategy for any session from 2018 onward.")

with st.sidebar:
    st.markdown("### ⚙️ Session Settings")
    year         = st.number_input("Year", 2018, 2026, 2024)
    gp           = st.text_input("Grand Prix", "Monza")
    session_type = st.selectbox("Session", ["R","Q","S","FP1","FP2","FP3"])
    drivers_input= st.text_input("Drivers (space-separated)", "VER LEC NOR")
    run = st.button("Run Analysis", type="primary")

if run:
    drivers = drivers_input.upper().split()
    with st.spinner(f"Loading {year} {gp} ({session_type})…"):
        apply_f1_style()
        session = load_session(year, gp, session_type)
        if not drivers:
            clean = clean_lap_times(session.laps)
            drivers = fastest_laps_by_driver(clean)["Driver"].head(6).tolist()

    event_name = session.event["EventName"]
    total_laps = int(session.laps["LapNumber"].max()) if not session.laps.empty else 0
    n_drivers  = len(session.laps["Driver"].unique())

    metrics_row([
        {"label": "Event",       "value": event_name},
        {"label": "Session",     "value": session_type, "color": "accent"},
        {"label": "Year",        "value": str(year)},
        {"label": "Total Laps",  "value": str(total_laps)},
        {"label": "Drivers",     "value": str(n_drivers)},
    ])

    st.markdown('<div style="padding:0 2.5rem;">', unsafe_allow_html=True)

    section_label("Lap Time Distribution")
    fig = plot_lap_time_distribution(session, drivers)
    if fig:
        st.pyplot(fig, use_container_width=True)

    section_label("Race Pace")
    fig2 = plot_race_pace(session, drivers)
    if fig2:
        st.pyplot(fig2, use_container_width=True)

    section_label("Tyre Strategy")
    fig3 = plot_tire_strategy(session, drivers)
    if fig3:
        st.pyplot(fig3, use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.markdown("""
<div style="padding:4rem 2.5rem; text-align:center; color:#333;
            font-family:'Titillium Web',sans-serif; font-size:0.8rem;
            text-transform:uppercase; letter-spacing:0.15em;">
    Configure session parameters in the sidebar and press Run Analysis
</div>""", unsafe_allow_html=True)