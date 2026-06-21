import streamlit as st
from f1_analysis.core.session_loader import load_session
from f1_analysis.core.telemetry import get_driver_telemetry
from f1_analysis.visualization.style import apply_f1_style
from f1_analysis.visualization.plots import plot_track_speed_map

st.set_page_config(page_title="Speed Map", page_icon="🗺️", layout="wide")
st.title("Track Speed Map")

st.sidebar.header("Settings")
year = st.sidebar.number_input("Year", 2018, 2026, 2024)
gp = st.sidebar.text_input("Grand Prix", "Monaco")
session_type = st.sidebar.selectbox("Session", ["Q", "R", "S", "FP1", "FP2", "FP3"])
driver = st.sidebar.text_input("Driver", "LEC").upper()

if st.sidebar.button("Generate Map"):
    with st.spinner(f"Mapping {driver}'s speed around {gp}..."):
        apply_f1_style()
        session = load_session(year, gp, session_type)
        telemetry = get_driver_telemetry(session, driver)
        
        st.pyplot(plot_track_speed_map(telemetry, session, driver))