import streamlit as st
from pathlib import Path
from f1_analysis.ml.data_builder import SeasonDataBuilder
from f1_analysis.visualization.style import apply_f1_style
# Note: You will need to extract the plotting logic from script 06 into a function
# inside your f1_analysis/visualization/plots.py to import it here easily.

st.set_page_config(page_title="ML Predictor", page_icon="🤖", layout="wide")
st.title("Machine Learning Race Predictor")

st.info("⚠️ Note: You must run `scripts/05_ml_season_models.py` locally first to generate the model `.pkl` files before using this dashboard.")

st.sidebar.header("Settings")
year = st.sidebar.number_input("Year", 2018, 2026, 2024)
gp = st.sidebar.text_input("Grand Prix", "Abu Dhabi")
driver = st.sidebar.text_input("Driver", "VER").upper()

if st.sidebar.button("Run Predictions"):
    data_path = Path("outputs/reports") / f"season_{year}_laps.csv"
    models_dir = Path("outputs/models") / f"{year}_{driver}"
    
    if not data_path.exists() or not models_dir.exists():
        st.error("Model data not found. Please run Script 05 in your terminal first.")
    else:
        with st.spinner("Loading models and applying to race data..."):
            apply_f1_style()
            # Here you would call a refactored function from your plots.py that 
            # returns the `fig` generated in script 06, then:
            # st.pyplot(fig)
            st.success("Models applied successfully! (Ensure plotting logic is imported)")