import streamlit as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from f1_analysis.core.session_loader import load_session
from f1_analysis.core.telemetry import get_driver_telemetry
from f1_analysis.visualization.style import apply_f1_style
from f1_analysis.visualization.plots import plot_track_speed_map

st.set_page_config(page_title="Speed Map", page_icon="🗺️", layout="wide")
st.markdown("""<style>
.page-header{background:linear-gradient(90deg,#1a0000,#0a0a1e);border-left:4px solid #e10600;
  padding:1.2rem 1.5rem;border-radius:0 8px 8px 0;margin-bottom:1.5rem;}
.page-header h1{color:#fff;margin:0;font-size:1.8rem;}
.page-header p{color:#aaa;margin:.3rem 0 0;font-size:.95rem;}
.explain-box{background:#111827;border:1px solid #1f2937;border-left:3px solid #e10600;
  border-radius:6px;padding:.9rem 1.2rem;margin:.8rem 0 1.2rem;color:#d1d5db;font-size:.9rem;line-height:1.6;}
.insight-box{background:#0d1117;border:1px solid #21262d;border-radius:8px;padding:1rem 1.3rem;margin-top:1rem;}
.insight-box h4{color:#e10600;margin:0 0 .6rem;font-size:1rem;}
</style>
<div class="page-header">
    <h1>🗺️ Track Speed Map</h1>
    <p>The circuit outline painted by speed — see instantly where the car is fastest and where it brakes hardest.</p>
</div>""", unsafe_allow_html=True)

st.sidebar.header("Settings")
year         = st.sidebar.number_input("Year", 2018, 2026, 2024)
gp           = st.sidebar.text_input("Grand Prix", "Monaco")
session_type = st.sidebar.selectbox("Session", ["Q", "R", "FP1", "FP2", "FP3"])
driver       = st.sidebar.text_input("Driver", "LEC").upper()
lap_num      = st.sidebar.number_input("Specific Lap (0 = fastest)", min_value=0, value=0)
st.sidebar.caption("Fastest lap is used by default. Enter a lap number to view a specific race lap.")

if st.sidebar.button("Generate Map", type="primary"):
    with st.spinner(f"Loading {driver}'s telemetry at {gp}..."):
        apply_f1_style()
        try:
            session    = load_session(year, gp, session_type)
            telemetry  = get_driver_telemetry(session, driver, lap_number=int(lap_num) if lap_num > 0 else None)
        except Exception as e:
            st.error(f"Could not load telemetry: {e}")
            st.stop()

    # ── Explain the chart ─────────────────────────────────────────
    st.markdown("""<div class="explain-box">
    <strong>What this chart shows:</strong> The circuit is drawn as a line that follows the
    actual GPS coordinates of the car. The colour of the line changes based on how fast the
    car was going at that exact point — using a <strong>plasma colour scale</strong>:
    <strong style="color:#6200ea">dark purple = slow</strong> (braking into a corner),
    <strong style="color:#ff9800">orange</strong> = medium speed,
    <strong style="color:#ffff00">bright yellow = maximum speed</strong> (DRS straights).
    Tight corners show as sharp kinks with dark colours. Long straights appear as straight
    bright yellow sections.
    </div>""", unsafe_allow_html=True)

    fig = plot_track_speed_map(telemetry, session, driver)
    st.pyplot(fig); plt.close(fig)

    # ── Insights ──────────────────────────────────────────────────
    max_speed   = telemetry["Speed"].max()
    min_speed   = telemetry["Speed"].min()
    avg_speed   = telemetry["Speed"].mean()
    max_dist    = telemetry.loc[telemetry["Speed"].idxmax(), "Distance"]
    min_dist    = telemetry.loc[telemetry["Speed"].idxmin(), "Distance"]
    full_throttle_pct = (telemetry["Throttle"] >= 99).mean() * 100 if "Throttle" in telemetry.columns else None

    st.markdown(f"""<div class="insight-box"><h4>🔍 Speed analysis — {driver} at {session.event['EventName']} {year}</h4>
    <ul>
    <li><strong>Top speed:</strong> {max_speed:.0f} km/h at {max_dist:.0f}m around the lap</li>
    <li><strong>Minimum speed:</strong> {min_speed:.0f} km/h at {min_dist:.0f}m (slowest corner)</li>
    <li><strong>Average speed:</strong> {avg_speed:.0f} km/h throughout the lap</li>
    {"<li><strong>Full throttle:</strong> " + f"{full_throttle_pct:.1f}% of the lap spent at 100% throttle</li>" if full_throttle_pct is not None else ""}
    <li>The <strong>speed delta</strong> (top speed minus min speed) of
    <strong>{max_speed-min_speed:.0f} km/h</strong> tells you how demanding the circuit is —
    higher delta = more stop-and-go nature (like Monaco or Hungary).
    Low delta = high-speed flowing circuits (like Spa or Silverstone).</li>
    </ul></div>""", unsafe_allow_html=True)

    # ── Circuit type explainer ─────────────────────────────────────
    speed_delta = max_speed - min_speed
    if speed_delta > 220:
        circuit_type = "**stop-and-go street circuit** — very slow tight corners and fast straights. Tyre wear is typically one-sided (usually fronts), and overtaking is very difficult."
    elif speed_delta > 160:
        circuit_type = "**mixed-speed circuit** — a combination of high-speed and technical sections. Balance between mechanical and aerodynamic grip is critical."
    else:
        circuit_type = "**high-speed flowing circuit** — corners are taken at high speed. Aerodynamic downforce is the most important factor. Qualifying pace differences are usually small."
    st.markdown(f"Based on the speed range, **{gp}** appears to be a {circuit_type}")