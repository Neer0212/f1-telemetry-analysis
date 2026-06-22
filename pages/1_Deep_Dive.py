import streamlit as st
from f1_analysis.core.session_loader import load_session
from f1_analysis.core.lap_analysis import fastest_laps_by_driver, clean_lap_times
from f1_analysis.visualization.style import apply_f1_style
from f1_analysis.visualization.plots import plot_lap_time_distribution, plot_race_pace, plot_tire_strategy

st.set_page_config(page_title="Session Deep Dive", page_icon="📊", layout="wide")
st.title("Session Deep Dive")

st.sidebar.header("Session Settings")
year = st.sidebar.number_input("Year", min_value=2018, max_value=2026, value=2024)
gp = st.sidebar.text_input("Grand Prix", "Monza")
session_type = st.sidebar.selectbox("Session", ["R", "Q", "S", "FP1", "FP2", "FP3"])
drivers_input = st.sidebar.text_input("Drivers (space separated)", "VER LEC NOR")

if st.sidebar.button("Run Analysis"):
    drivers = drivers_input.upper().split()
    with st.spinner(f"Loading {year} {gp} ({session_type})..."):
        apply_f1_style()
        session = load_session(year, gp, session_type)
        
        if not drivers:
            clean = clean_lap_times(session.laps)
            fastest = fastest_laps_by_driver(clean)
            drivers = fastest["Driver"].head(6).tolist()
            
        st.subheader("Lap Time Distribution")
        st.pyplot(plot_lap_time_distribution(session, drivers))
        
        st.subheader("Race Pace")
        st.pyplot(plot_race_pace(session, drivers))
        
        st.subheader("Tire Strategy")
        st.pyplot(plot_tire_strategy(session, drivers))
        # ── TEXT SUMMARY ──────────────────────────────────────────────
        st.markdown("---")
        st.subheader("📋 Session Summary")

        from f1_analysis.core.lap_analysis import fastest_laps_by_driver, race_pace_summary, stint_summary, clean_lap_times, laps_to_seconds

        clean = clean_lap_times(session.laps)
        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown("#### ⚡ Fastest Laps")
            fastest = fastest_laps_by_driver(clean)[["Driver","LapTimeSeconds","Compound"]].head(10)
            fastest["LapTimeSeconds"] = fastest["LapTimeSeconds"].round(3)
            st.dataframe(fastest, use_container_width=True)

        with col_b:
            st.markdown("#### 📊 Race Pace (selected drivers)")
            pace = race_pace_summary(clean[clean["Driver"].isin(drivers)]).round(3)
            st.dataframe(pace, use_container_width=True)

        st.markdown("#### 🛞 Tire Strategy")
        strategy = stint_summary(session.laps)
        strategy = strategy[strategy["Driver"].isin(drivers)][["Driver","Stint","Compound","LapCount","AvgLapTime"]].round(3)
        st.dataframe(strategy, use_container_width=True)