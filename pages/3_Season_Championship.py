import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

st.set_page_config(page_title="Championship · F1 Analytics", page_icon="🏆", layout="wide")

from f1_analysis.visualization.ui_theme import inject_f1_css, page_header, section_label, sidebar_nav
from f1_analysis.core.season import build_driver_standings_progression, build_team_standings_progression
from f1_analysis.visualization.style import apply_f1_style
from f1_analysis.visualization.plots import plot_championship_progression

inject_f1_css()
sidebar_nav()
page_header("🏆", "Season Analysis", "Championship Progression",
            "Round-by-round points accumulation for the Drivers' and Constructors' Championships.")

with st.sidebar:
    st.markdown("### ⚙️ Settings")
    year  = st.number_input("Year", 2018, 2026, 2024)
    top_n = st.slider("Top N Drivers", 3, 20, 8)
    run   = st.button("Build Standings", type="primary")

if run:
    with st.spinner("Fetching standings…"):
        apply_f1_style()
        driver_standings = build_driver_standings_progression(year)
        team_standings   = build_team_standings_progression(year)

    st.markdown('<div style="padding:0 2.5rem;">', unsafe_allow_html=True)
    section_label("Drivers' Championship")
    st.pyplot(plot_championship_progression(
        driver_standings, entity_column="DriverCode",
        top_n=top_n, title=f"{year} Drivers' Championship"
    ), use_container_width=True)

    section_label("Constructors' Championship")
    st.pyplot(plot_championship_progression(
        team_standings, entity_column="Constructor",
        title=f"{year} Constructors' Championship"
    ), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.markdown("""
<div style="padding:4rem 2.5rem; text-align:center; color:#333;
            font-family:'Titillium Web',sans-serif; font-size:0.8rem;
            text-transform:uppercase; letter-spacing:0.15em;">
    Select a season year and press Build Standings
</div>""", unsafe_allow_html=True)