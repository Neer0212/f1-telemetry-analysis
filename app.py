import streamlit as st

st.set_page_config(
    page_title="F1 Telemetry Analysis",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Dark F1-themed sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0a0a 0%, #1a1a2e 100%);
    }
    [data-testid="stSidebar"] * { color: #ffffff !important; }

    /* Main background */
    .stApp { background-color: #0f0f0f; }

    /* Hero card */
    .hero {
        background: linear-gradient(135deg, #1a0000 0%, #0a0a1e 50%, #001a0a 100%);
        border: 1px solid #e10600;
        border-radius: 12px;
        padding: 2.5rem 3rem;
        margin-bottom: 2rem;
    }
    .hero h1 { color: #e10600; font-size: 2.8rem; font-weight: 900; margin: 0; }
    .hero p  { color: #cccccc; font-size: 1.1rem; margin-top: 0.5rem; }

    /* Feature cards */
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1rem;
        margin: 1.5rem 0;
    }
    .feature-card {
        background: #1a1a1a;
        border: 1px solid #333;
        border-radius: 8px;
        padding: 1.2rem;
        transition: border-color 0.2s;
    }
    .feature-card:hover { border-color: #e10600; }
    .feature-card .icon  { font-size: 1.8rem; margin-bottom: 0.4rem; }
    .feature-card h3     { color: #ffffff; font-size: 1rem; margin: 0 0 0.3rem; }
    .feature-card p      { color: #888888; font-size: 0.85rem; margin: 0; }

    /* Stat badges */
    .stat-row { display: flex; gap: 1rem; margin: 1.5rem 0; }
    .stat-badge {
        background: #1a1a1a;
        border: 1px solid #e10600;
        border-radius: 8px;
        padding: 0.8rem 1.5rem;
        text-align: center;
        flex: 1;
    }
    .stat-badge .num { color: #e10600; font-size: 2rem; font-weight: 900; }
    .stat-badge .lbl { color: #888; font-size: 0.8rem; }

    /* Section headers */
    .section-header {
        color: #ffffff;
        font-size: 1.3rem;
        font-weight: 700;
        border-left: 4px solid #e10600;
        padding-left: 0.8rem;
        margin: 1.5rem 0 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <h1>🏎️ F1 Telemetry Analysis</h1>
    <p>Professional-grade Formula 1 data analysis — telemetry, strategy, machine learning predictions, and multi-season comparisons. Built on real FastF1 timing data from 2018 onwards.</p>
</div>
""", unsafe_allow_html=True)

# ── Stats row ─────────────────────────────────────────────────────────────────
st.markdown("""
<div class="stat-row">
    <div class="stat-badge"><div class="num">9</div><div class="lbl">Analysis Tools</div></div>
    <div class="stat-badge"><div class="num">4</div><div class="lbl">ML Models</div></div>
    <div class="stat-badge"><div class="num">7+</div><div class="lbl">Seasons of Data</div></div>
    <div class="stat-badge"><div class="num">20</div><div class="lbl">Drivers per Season</div></div>
</div>
""", unsafe_allow_html=True)

# ── Feature grid ──────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">What you can do</div>', unsafe_allow_html=True)
st.markdown("""
<div class="feature-grid">
    <div class="feature-card">
        <div class="icon">📊</div>
        <h3>Session Deep Dive</h3>
        <p>Lap time distributions, race pace consistency, and tire strategy for any session since 2018.</p>
    </div>
    <div class="feature-card">
        <div class="icon">⚔️</div>
        <h3>Head-to-Head Telemetry</h3>
        <p>Speed traces, time deltas, and throttle/brake overlays for any two drivers' fastest laps.</p>
    </div>
    <div class="feature-card">
        <div class="icon">🏆</div>
        <h3>Championship Progression</h3>
        <p>Round-by-round points progression for drivers and constructors across a full season.</p>
    </div>
    <div class="feature-card">
        <div class="icon">🗺️</div>
        <h3>Track Speed Map</h3>
        <p>Circuit outline painted by speed — see exactly where a driver is fastest and slowest.</p>
    </div>
    <div class="feature-card">
        <div class="icon">⏱️</div>
        <h3>Qualifying Delta Map</h3>
        <p>Minisector-by-minisector comparison: green where driver A is faster, red where B is.</p>
    </div>
    <div class="feature-card">
        <div class="icon">🛞</div>
        <h3>Pit Stop Window</h3>
        <p>Optimal pit lap range with undercut threat detection and overcut viability analysis.</p>
    </div>
    <div class="feature-card">
        <div class="icon">📈</div>
        <h3>Multi-Season Comparison</h3>
        <p>One driver across seasons, two drivers head-to-head, or a full circuit heatmap.</p>
    </div>
    <div class="feature-card">
        <div class="icon">📖</div>
        <h3>Race Story</h3>
        <p>Complete lap-by-lap narrative: pit stops, overtakes, incidents, undercut windows.</p>
    </div>
    <div class="feature-card">
        <div class="icon">🤖</div>
        <h3>ML Predictions</h3>
        <p>Lap time prediction, podium probability, tire identification, and undercut detection.</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ── How to use ────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">How to use</div>', unsafe_allow_html=True)
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("**1. Pick a tool** from the sidebar on the left.")
with col2:
    st.markdown("**2. Enter the race details** — year, Grand Prix, session, drivers.")
with col3:
    st.markdown("**3. Hit Run** — data loads from FastF1 and charts appear instantly.")

st.info("💡 First load of a session downloads data from F1's servers (~10-30s). Every repeat load is instant thanks to local caching.", icon="ℹ️")

st.markdown("---")
st.markdown(
    "<p style='color:#555; font-size:0.8rem; text-align:center;'>Built with FastF1 · Matplotlib · Scikit-learn · Streamlit &nbsp;|&nbsp; Data available from 2018 onward</p>",
    unsafe_allow_html=True,
)