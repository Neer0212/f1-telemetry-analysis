import streamlit as st
from f1_analysis.core.season import build_driver_standings_progression, build_team_standings_progression
from f1_analysis.visualization.style import apply_f1_style
from f1_analysis.visualization.plots import plot_championship_progression

st.set_page_config(page_title="Championship", page_icon="🏆", layout="wide")
st.title("Season Championship Progression")

st.sidebar.header("Settings")
year = st.sidebar.number_input("Year", 2018, 2026, 2024)
top_n = st.sidebar.slider("Top N Drivers to Show", 3, 20, 8)

if st.sidebar.button("Build Standings"):
    with st.spinner("Fetching standings from Ergast API..."):
        apply_f1_style()
        
        driver_standings = build_driver_standings_progression(year)
        team_standings = build_team_standings_progression(year)
        
        st.subheader("Drivers' Championship")
        # FIX: Explicitly name entity_column, top_n, and title
        st.pyplot(plot_championship_progression(
            driver_standings, 
            entity_column="DriverCode", 
            top_n=top_n, 
            title=f"{year} Drivers' Championship"
        ))
        
        st.subheader("Constructors' Championship")
        # FIX: Explicitly name entity_column and title
        st.pyplot(plot_championship_progression(
            team_standings, 
            entity_column="Constructor", 
            title=f"{year} Constructors' Championship"
        ))