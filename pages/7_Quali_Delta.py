import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
st.set_page_config(page_title="Qualifying Delta - F1 Analytics", page_icon="F1", layout="wide", initial_sidebar_state="collapsed")
from f1_analysis.visualization.ui_theme import inject_f1_css, top_nav, page_header, control_panel, section_label, metrics_row, insight_box
inject_f1_css()
top_nav("Qualifying")
page_header("Q", "Qualifying Analysis", "Qualifying Delta Map",
    "Minisector-by-minisector comparison. Green where Driver A is faster, red where Driver B is faster.")

clicked, vals = control_panel([
    {"type":"number","label":"Year","key":"qd_year","default":2024,"min":2018,"max":2026},
    {"type":"text",  "label":"Grand Prix","key":"qd_gp","default":"Monza"},
    {"type":"text",  "label":"Driver A","key":"qd_a","default":"VER"},
    {"type":"text",  "label":"Driver B","key":"qd_b","default":"LEC"},
], button_label="Generate Delta Map", cols_per_row=5)

if clicked:
    from f1_analysis.core.session_loader import load_session
    from f1_analysis.core.quali_delta import compute_quali_delta
    from f1_analysis.visualization.style import apply_f1_style
    driver_a = vals["qd_a"].upper(); driver_b = vals["qd_b"].upper()
    with st.spinner("Loading qualifying telemetry..."):
        apply_f1_style()
        session = load_session(vals["qd_year"], vals["qd_gp"], "Q")
        result  = compute_quali_delta(session, driver_a, driver_b)
    st.markdown('<div style="padding:0 2.5rem 4rem;">', unsafe_allow_html=True)
    section_label("Delta Map")
    if hasattr(result, "fig"):
        st.pyplot(result.fig, use_container_width=True)
    elif hasattr(result, "plot"):
        st.pyplot(result.plot(), use_container_width=True)
    insight_box("Q", "Reading the Qualifying Delta Map",
        "Green sections = Driver A was faster. Red sections = Driver B was faster. "
        "The length of each coloured section shows how long that advantage was maintained. "
        "Steep changes through a corner complex reveal where the lap is won or lost.")
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.markdown('<div style="padding:5rem 2.5rem;text-align:center;font-family:Titillium Web,sans-serif;font-size:0.8rem;text-transform:uppercase;letter-spacing:0.15em;color:#2A2A2A;">Select two drivers above and press Generate Delta Map</div>', unsafe_allow_html=True)