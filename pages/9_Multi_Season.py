import streamlit as st
from f1_analysis.core.multi_season import compare_driver_across_seasons, compare_two_drivers_across_seasons, driver_circuit_heatmap_data
from f1_analysis.visualization.style import apply_f1_style

st.set_page_config(page_title="Multi Season", page_icon="📈", layout="wide")
st.title("Multi-Season Comparison")

st.sidebar.header("Settings")
mode = st.sidebar.selectbox("Mode", ["Single Driver", "Head-to-Head", "Circuit Heatmap"])

if mode == "Single Driver":
    driver = st.sidebar.text_input("Driver", "VER").upper()
    gp = st.sidebar.text_input("Grand Prix", "Monaco")
    years = st.sidebar.text_input("Years (space separated)", "2021 2022 2023 2024")
elif mode == "Head-to-Head":
    col1, col2 = st.sidebar.columns(2)
    driver_a = col1.text_input("Driver A", "VER").upper()
    driver_b = col2.text_input("Driver B", "LEC").upper()
    gp = st.sidebar.text_input("Grand Prix", "Monaco")
    years = st.sidebar.text_input("Years", "2022 2023 2024")
else:
    driver = st.sidebar.text_input("Driver", "NOR").upper()
    year = st.sidebar.number_input("Year", 2018, 2026, 2024)

if st.sidebar.button("Run Comparison"):
    with st.spinner("Compiling historical data..."):
        apply_f1_style()
        if mode == "Single Driver":
            df = compare_driver_across_seasons(driver, [int(y) for y in years.split()], gp, "Q")
            st.dataframe(df)
        elif mode == "Head-to-Head":
            df = compare_two_drivers_across_seasons(driver_a, driver_b, [int(y) for y in years.split()], gp, "Q")
            st.dataframe(df)
        else:
            df = driver_circuit_heatmap_data(driver, year, "Q", None)
            st.dataframe(df)
        
        st.success("Data fetched! Ensure plotting logic returns `fig` to render visual charts here.")