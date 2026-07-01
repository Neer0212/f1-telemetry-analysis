import streamlit as st
import matplotlib.pyplot as plt
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
st.set_page_config(page_title="Multi-Season - F1 Analytics", page_icon="F1", layout="wide", initial_sidebar_state="collapsed")
from f1_analysis.visualization.ui_theme import inject_f1_css, top_nav, page_header, control_panel, section_label, metrics_row, insight_box
inject_f1_css()
top_nav("Multi-Season")
page_header("T", "Historical Analysis", "Multi-Season Comparison",
    "One driver across seasons, head-to-head across years, or a full circuit heatmap.")

mode = st.radio("", ["Single Driver Across Seasons", "Head-to-Head Across Seasons", "Circuit Heatmap"], horizontal=True, label_visibility="collapsed")
st.markdown('<div style="height:1px;background:#2A2A2A;margin:0 0 0;"></div>', unsafe_allow_html=True)

if mode == "Single Driver Across Seasons":
    clicked, vals = control_panel([
        {"type":"text","label":"Driver","key":"ms_driver","default":"VER"},
        {"type":"text","label":"Grand Prix","key":"ms_gp","default":"Monaco"},
        {"type":"text","label":"Years (space-separated)","key":"ms_years","default":"2021 2022 2023 2024"},
        {"type":"select","label":"Session","key":"ms_session","default":"Q","options":["Q","R"]},
    ], button_label="Run Comparison")
elif mode == "Head-to-Head Across Seasons":
    clicked, vals = control_panel([
        {"type":"text","label":"Driver A","key":"ms_a","default":"VER"},
        {"type":"text","label":"Driver B","key":"ms_b","default":"LEC"},
        {"type":"text","label":"Grand Prix","key":"ms_gp","default":"Monaco"},
        {"type":"text","label":"Years","key":"ms_years","default":"2022 2023 2024"},
        {"type":"select","label":"Session","key":"ms_session","default":"Q","options":["Q","R"]},
    ], button_label="Run Comparison", cols_per_row=6)
else:
    clicked, vals = control_panel([
        {"type":"text","label":"Driver","key":"ms_driver","default":"NOR"},
        {"type":"number","label":"Year","key":"ms_year","default":2024,"min":2018,"max":2026},
        {"type":"select","label":"Session","key":"ms_session","default":"Q","options":["Q","R"]},
    ], button_label="Run Comparison")

if clicked:
    from f1_analysis.core.multi_season import compare_driver_across_seasons, compare_two_drivers_across_seasons, driver_circuit_heatmap_data
    from f1_analysis.visualization.style import apply_f1_style
    apply_f1_style()
    st.markdown('<div style="padding:0 2.5rem 4rem;">', unsafe_allow_html=True)
    if mode == "Single Driver Across Seasons":
        years = [int(y) for y in vals["ms_years"].split()]
        with st.spinner("Loading data..."):
            df = compare_driver_across_seasons(vals["ms_driver"], years, vals["ms_gp"], vals["ms_session"])
        section_label("Results")
        st.dataframe(df, use_container_width=True)
        insight_box("S", "Reading This Table",
            "Each row is one season's best lap time for this driver at this circuit. Times naturally get faster "
            "year over year as cars develop, so a downward trend is expected. A year that is noticeably slower than "
            "the trend usually means a wet session, a different tyre allocation, or a regulation change that season.")
    elif mode == "Head-to-Head Across Seasons":
        years = [int(y) for y in vals["ms_years"].split()]
        with st.spinner("Loading data..."):
            df = compare_two_drivers_across_seasons(vals["ms_a"], vals["ms_b"], years, vals["ms_gp"], vals["ms_session"])
        section_label("Results")
        st.dataframe(df, use_container_width=True)
        insight_box("H", "Reading This Table",
            "Compares two drivers' best lap times at the same circuit across multiple seasons. Note that these drivers "
            "may not have been teammates in the same car, so a large gap could reflect car performance rather than "
            "pure driver skill. The clearest comparison is when both drivers were on similar equipment that season.")
    else:
        with st.spinner("Loading data..."):
            df = driver_circuit_heatmap_data(vals["ms_driver"], int(vals["ms_year"]), vals["ms_session"])
        section_label("Circuit Heatmap")
        st.dataframe(df, use_container_width=True)
        insight_box("C", "Reading This Table",
            "Shows the gap to session-fastest at every circuit visited that season. A small or zero gap means pole "
            "or session-best pace at that track. A larger gap points to circuits where the car or driver struggled "
            "that year. This is useful for spotting which track types suit a driver's style.")
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.markdown('<div style="padding:5rem 2.5rem;text-align:center;font-family:Titillium Web,sans-serif;font-size:0.8rem;text-transform:uppercase;letter-spacing:0.15em;color:#2A2A2A;">Configure parameters above and press Run Comparison</div>', unsafe_allow_html=True)