import streamlit as st

st.set_page_config(page_title="F1 Telemetry Analysis", page_icon="🏎️", layout="wide")

st.title("Formula 1 Telemetry & ML Analysis")
st.markdown("""
Welcome to the F1 Telemetry Toolkit! 

This application provides deep insights into Formula 1 timing data, telemetry, and race strategy using the FastF1 API and custom Machine Learning models.

### Select a tool from the sidebar to begin:
* **📊 Deep Dive:** Lap time distributions and tire strategy.
* **⚔️ Head to Head:** Telemetry overlay for two drivers' fastest laps.
* **🏆 Championship:** Season progression for drivers and constructors.
* **🗺️ Speed Map:** Track outline colored by speed.
* **🤖 Single Race Predictor:** Apply trained ML models to a race.
* **📖 Race Story:** A complete lap-by-lap story for one driver.
* **⏱️ Quali Delta:** Minisector time delta map.
* **🛞 Pit Window:** Live undercut/overcut calculations.
* **📈 Multi-Season:** Compare driver performance across years.
""")