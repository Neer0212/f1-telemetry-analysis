import streamlit as st
from f1_analysis.core.session_loader import load_session
from f1_analysis.visualization.style import apply_f1_style
# Note: Adapt `_build_chart` from script 07 to return the figure instead of saving it

st.set_page_config(page_title="Race Story", page_icon="📖", layout="wide")
st.title("Complete Race Story Timeline")

st.sidebar.header("Settings")
year = st.sidebar.number_input("Year", 2018, 2026, 2024)
gp = st.sidebar.text_input("Grand Prix", "Monaco")
driver = st.sidebar.text_input("Driver", "LEC").upper()

if st.sidebar.button("Generate Timeline"):
    with st.spinner(f"Compiling race events for {driver}..."):
        apply_f1_style()
        session = load_session(year, gp, "R", telemetry=False, weather=False)
        
        # Here you would call your imported `_build_chart` logic.
        # Ensure it returns `fig` so you can call:
        # st.pyplot(fig)
        st.success("Ensure your `_build_chart` function returns the matplotlib figure to render here!")