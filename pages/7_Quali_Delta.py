import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

st.set_page_config(page_title="Qualifying Delta · F1 Analytics", page_icon="⏱️", layout="wide")

from f1_analysis.visualization.ui_theme import inject_f1_css, page_header, section_label, metrics_row
from f1_analysis.core.session_loader import load_session
from f1_analysis.core.quali_delta import compute_quali_delta
from f1_analysis.visualization.style import apply_f1_style
import matplotlib.pyplot as plt
import numpy as np

inject_f1_css()
page_header("⏱️", "Qualifying Analysis", "Qualifying Delta Map",
            "Minisector-by-minisector comparison — green where Driver A is faster, red where Driver B is faster.")

with st.sidebar:
    st.markdown("### ⚙️ Settings")
    year   = st.number_input("Year", 2018, 2026, 2024)
    gp     = st.text_input("Grand Prix", "Monza")
    col1, col2 = st.columns(2)
    driver_a = col1.text_input("Driver A", "VER").upper()
    driver_b = col2.text_input("Driver B", "LEC").upper()
    run = st.button("Generate Delta Map", type="primary")

if run:
    with st.spinner(f"Loading qualifying telemetry…"):
        apply_f1_style()
        session = load_session(year, gp, "Q")
        result  = compute_quali_delta(session, driver_a, driver_b)

    metrics_row([
        {"label": "Driver A",       "value": driver_a, "color": "teal"},
        {"label": "Driver B",       "value": driver_b, "color": "accent"},
        {"label": f"{driver_a} Lap","value": result.lap_time_a if hasattr(result, "lap_time_a") else "N/A"},
        {"label": f"{driver_b} Lap","value": result.lap_time_b if hasattr(result, "lap_time_b") else "N/A"},
        {"label": "Gap",            "value": result.gap if hasattr(result, "gap") else "N/A"},
    ])

    st.markdown('<div style="padding:0 2.5rem;">', unsafe_allow_html=True)
    section_label("Delta Map")
    if hasattr(result, "fig"):
        st.pyplot(result.fig, use_container_width=True)
    elif hasattr(result, "plot"):
        st.pyplot(result.plot(), use_container_width=True)
    else:
        st.info("Delta map generated — check result object attributes.")
        st.write(dir(result))
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.markdown("""
<div style="padding:4rem 2.5rem; text-align:center; color:#333;
            font-family:'Titillium Web',sans-serif; font-size:0.8rem;
            text-transform:uppercase; letter-spacing:0.15em;">
    Select two drivers and a Grand Prix, then press Generate Delta Map
</div>""", unsafe_allow_html=True)