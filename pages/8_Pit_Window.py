import streamlit as st
from f1_analysis.core.session_loader import load_session
from f1_analysis.core.pit_window import calculate_pit_window, calculate_all_pit_windows
from f1_analysis.visualization.style import apply_f1_style

st.set_page_config(page_title="Pit Window", page_icon="🛞", layout="wide")
st.title("Pit Stop Window Calculator")

st.sidebar.header("Settings")
year = st.sidebar.number_input("Year", 2018, 2026, 2024)
gp = st.sidebar.text_input("Grand Prix", "Bahrain")
analysis_type = st.sidebar.radio("Analysis Type", ["Single Driver", "All Drivers"])
lap = st.sidebar.number_input("Lap to Analyze", min_value=1, value=25)
next_compound = st.sidebar.selectbox("Next Compound", ["HARD", "MEDIUM", "SOFT"])

if analysis_type == "Single Driver":
    driver = st.sidebar.text_input("Driver", "VER").upper()

if st.sidebar.button("Calculate Pit Window"):
    with st.spinner("Analyzing live pace and gaps..."):
        apply_f1_style()
        session = load_session(year, gp, "R", telemetry=False, weather=False)
        
        if analysis_type == "Single Driver":
            result = calculate_pit_window(session, driver, current_lap=lap, next_compound=next_compound)
            st.write(f"**Optimal Pit:** Lap {result.optimal_lap}")
            st.write(f"**Earliest Pit:** Lap {result.earliest_lap}")
            st.write(f"**Latest Pit:** Lap {result.latest_lap}")
            st.write(f"**Undercut Threat:** Lap {result.undercut_threat_lap}")
            # st.pyplot(plot_pit_window_single(...))
        else:
            df = calculate_all_pit_windows(session, analysis_lap=lap, next_compound=next_compound)
            st.dataframe(df)
            # st.pyplot(plot_pit_window_all(...))