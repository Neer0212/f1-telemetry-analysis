import streamlit as st
from f1_analysis.core.session_loader import load_session
from f1_analysis.core.telemetry import compare_driver_telemetry
from f1_analysis.visualization.style import apply_f1_style
from f1_analysis.visualization.plots import plot_speed_trace_comparison, plot_telemetry_delta, plot_throttle_brake_comparison

st.set_page_config(page_title="Head to Head", page_icon="⚔️", layout="wide")
st.title("Driver Head-to-Head Telemetry")

st.sidebar.header("Settings")
year = st.sidebar.number_input("Year", 2018, 2026, 2024)
gp = st.sidebar.text_input("Grand Prix", "Monza")
session_type = st.sidebar.selectbox("Session", ["Q", "R", "S"])
col1, col2 = st.sidebar.columns(2)
driver_a = col1.text_input("Driver A", "VER").upper()
driver_b = col2.text_input("Driver B", "LEC").upper()

if st.sidebar.button("Compare Drivers"):
    with st.spinner(f"Loading telemetry for {driver_a} vs {driver_b}..."):
        apply_f1_style()
        session = load_session(year, gp, session_type)
        comparison = compare_driver_telemetry(session, driver_a, driver_b)
        
        final_delta = comparison.delta_time["Delta"].iloc[-1]
        leader = driver_a if final_delta > 0 else driver_b
        st.success(f"{leader} was faster by {abs(final_delta):.3f}s over the lap.")
        
        st.pyplot(plot_speed_trace_comparison(comparison, session))
        st.pyplot(plot_telemetry_delta(comparison, session))
        st.pyplot(plot_throttle_brake_comparison(comparison, session))