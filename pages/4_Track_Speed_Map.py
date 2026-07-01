import sys
from pathlib import Path
import pandas as pd
import streamlit as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# 1. Setup & Imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
st.set_page_config(page_title="Track Speed Map · F1 Analytics", page_icon="🗺️", layout="wide", initial_sidebar_state="collapsed")

from f1_analysis.visualization.ui_theme import inject_f1_css, top_nav, page_header, control_panel, section_label, metrics_row
from f1_analysis.core.session_loader import load_session
from f1_analysis.core.telemetry import get_driver_telemetry
from f1_analysis.visualization.style import apply_f1_style
from f1_analysis.visualization.plots import plot_track_speed_map

inject_f1_css()
top_nav("Speed Map")
page_header("🗺️", "Circuit Visualisation", "Track Speed Map",
            "Circuit outline painted by speed. Visualise car speed across every metre of the circuit layout.")

# Custom HTML for explanations and dynamic insights (from Code 1)
EXPLAIN = """
<div style="background:#141414;border:1px solid #2A2A2A;border-left:3px solid #E8002D;
padding:.9rem 1.2rem;margin:.8rem 0 1.2rem;color:#aaa;font-size:.88rem;line-height:1.65;
font-family:'Inter',sans-serif;">
{text}
</div>"""

INSIGHT = """
<div style="background:#0D0D0D;border:1px solid #2A2A2A;border-top:2px solid #E8002D;
padding:1rem 1.3rem;margin-top:1rem;font-family:'Inter',sans-serif;">
<div style="font-family:'Titillium Web',sans-serif;font-size:.65rem;font-weight:700;
text-transform:uppercase;letter-spacing:.2em;color:#E8002D;margin-bottom:.6rem;">Key Insights</div>
<div style="color:#ccc;font-size:.88rem;font-family:'Inter',sans-serif;">
{text}
</div>
</div>"""

# 2. UI Control Panel (from Code 2, expanded with Code 1's inputs)
clicked, vals = control_panel([
    {"type":"number","label":"Year","key":"sm_year","default":2024,"min":2018,"max":2026},
    {"type":"text",  "label":"Grand Prix","key":"sm_gp","default":"Monza"},
    {"type":"select","label":"Session","key":"sm_session","default":"Q","options":["Q", "R", "FP1", "FP2", "FP3"]},
    {"type":"text",  "label":"Driver","key":"sm_driver","default":"VER"},
    {"type":"number","label":"Lap (0 = Fastest)","key":"sm_lap","default":0,"min":0},
], button_label="Generate Map", cols_per_row=5)

if clicked:
    driver = vals["sm_driver"].upper()
    lap_num = int(vals["sm_lap"])
    
    with st.spinner(f"Loading {driver}'s telemetry at {vals['sm_gp']}..."):
        apply_f1_style()
        try:
            session = load_session(vals["sm_year"], vals["sm_gp"], vals["sm_session"])
            telemetry = get_driver_telemetry(session, driver, lap_number=lap_num if lap_num > 0 else None)
            
            # Fetch lap info for the metrics row
            if lap_num > 0:
                lap_info = session.laps.pick_drivers(driver).pick_laps(lap_num).iloc[0]
            else:
                lap_info = session.laps.pick_drivers(driver).pick_fastest()
                
        except Exception as e:
            st.error(f"Could not load telemetry: {e}")
            st.stop()

    # Data Processing for Insights
    max_speed = telemetry["Speed"].max()
    min_speed = telemetry["Speed"].min()
    avg_speed = telemetry["Speed"].mean()
    max_dist  = telemetry.loc[telemetry["Speed"].idxmax(), "Distance"]
    min_dist  = telemetry.loc[telemetry["Speed"].idxmin(), "Distance"]
    speed_delta = max_speed - min_speed
    
    full_throttle_pct = (telemetry["Throttle"] >= 99).mean() * 100 if "Throttle" in telemetry.columns else None
    lap_time_str = str(lap_info["LapTime"]).split()[-1] if not pd.isna(lap_info.get("LapTime")) else "N/A"

    # Circuit Classifier logic
    if speed_delta > 220:
        circuit_type = "<strong>stop-and-go street circuit</strong> — very slow tight corners and fast straights. Tyre wear is typically one-sided (usually rears due to traction zones), and overtaking is very difficult."
    elif speed_delta > 160:
        circuit_type = "<strong>mixed-speed circuit</strong> — a combination of high-speed and technical sections. Balance between mechanical and aerodynamic grip is critical."
    else:
        circuit_type = "<strong>high-speed flowing circuit</strong> — corners are taken at high speed. Aerodynamic downforce is the most important factor. Qualifying pace differences are usually small."

    # 3. Dynamic Metrics Row
    metrics_row([
        {"label": "Driver", "value": driver, "color": "accent"},
        {"label": "Circuit", "value": session.event["EventName"]},
        {"label": "Lap Time", "value": lap_time_str, "color": "teal"},
        {"label": "Top Speed", "value": f"{max_speed:.0f} km/h"},
        {"label": "Avg Speed", "value": f"{avg_speed:.0f} km/h"},
    ])

    st.markdown('<div style="padding:0 2.5rem 4rem;">', unsafe_allow_html=True)

    # ── CHART: SPEED MAP ──
    section_label("Speed Map")
    st.markdown(EXPLAIN.format(text="""
    <strong>What this chart shows:</strong> The circuit is drawn as a line that follows the actual GPS coordinates of the car. 
    The colour of the line changes based on how fast the car was going at that exact point. 
    Darker colours represent heavy braking zones into tight corners. Brighter/lighter colours represent maximum speed on DRS straights.
    """), unsafe_allow_html=True)

    fig = plot_track_speed_map(telemetry, session, driver)
    if fig:
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)

    # ── DYNAMIC INSIGHTS ──
    throttle_html = f"<li><strong>Full throttle:</strong> {full_throttle_pct:.1f}% of the lap spent at 100% throttle.</li>" if full_throttle_pct is not None else ""

    st.markdown(INSIGHT.format(text=f"""
    <h4 style="color:#fff;margin:.3rem 0;">🔍 Speed analysis — {driver} at {session.event['EventName']} {vals['sm_year']}</h4>
    <ul style="margin:.4rem 0;padding-left:1.2rem;line-height:1.8;">
        <li><strong>Top speed:</strong> {max_speed:.0f} km/h at {max_dist:.0f}m around the lap.</li>
        <li><strong>Minimum speed:</strong> {min_speed:.0f} km/h at {min_dist:.0f}m (slowest corner).</li>
        <li><strong>Average speed:</strong> {avg_speed:.0f} km/h throughout the lap.</li>
        {throttle_html}
        <li>The <strong>speed delta</strong> (top speed minus min speed) of <strong>{speed_delta:.0f} km/h</strong> tells you how demanding the circuit is.</li>
    </ul>
    
    <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #2A2A2A;">
        Based on this speed range, <strong>{session.event['EventName']}</strong> appears to be a {circuit_type}
    </div>
    """), unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

else:
    st.markdown('<div style="padding:5rem 2.5rem;text-align:center;font-family:\'Titillium Web\',sans-serif;font-size:0.8rem;text-transform:uppercase;letter-spacing:0.15em;color:#2A2A2A;">Configure parameters above and press Generate Map</div>', unsafe_allow_html=True)