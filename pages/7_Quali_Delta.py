import streamlit as st
from f1_analysis.core.session_loader import load_session
from f1_analysis.core.quali_delta import compute_qualifying_delta
from f1_analysis.visualization.style import apply_f1_style
# Note: Ensure plot_quali_delta_map returns the figure

st.set_page_config(page_title="Quali Delta", page_icon="⏱️", layout="wide")
st.title("Qualifying Minisector Delta")

st.sidebar.header("Settings")
year = st.sidebar.number_input("Year", 2018, 2026, 2024)
gp = st.sidebar.text_input("Grand Prix", "Monaco")
col1, col2 = st.sidebar.columns(2)
driver_a = col1.text_input("Driver A", "LEC").upper()
driver_b = col2.text_input("Driver B", "VER").upper()
minisectors = st.sidebar.slider("Minisectors", 10, 50, 25)

if st.sidebar.button("Analyze Delta"):
    with st.spinner("Calculating minisectors..."):
        apply_f1_style()
        session = load_session(year, gp, "Q", telemetry=True, weather=False)
        minisector_df = compute_qualifying_delta(session, driver_a, driver_b, n_minisectors=minisectors)
        
        # st.pyplot(plot_quali_delta_map(minisector_df, driver_a, driver_b, session))
        st.success("Delta computed. Pass the returned figure to st.pyplot(fig).")