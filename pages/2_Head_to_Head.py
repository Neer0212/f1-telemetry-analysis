import sys
from pathlib import Path
import streamlit as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# 1. Setup & Imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
st.set_page_config(page_title="Head to Head · F1 Analytics", page_icon="⚔️", layout="wide", initial_sidebar_state="collapsed")

from f1_analysis.visualization.ui_theme import inject_f1_css, top_nav, page_header, control_panel, section_label, metrics_row
from f1_analysis.core.session_loader import load_session
from f1_analysis.core.telemetry import compare_driver_telemetry
from f1_analysis.visualization.style import apply_f1_style
from f1_analysis.visualization.plots import (
    plot_speed_trace_comparison, plot_telemetry_delta, plot_throttle_brake_comparison
)

inject_f1_css()
top_nav("Head to Head")
page_header("⚔️", "Telemetry Comparison", "Head-to-Head",
            "Speed traces, time deltas, and throttle/brake overlays. See exactly where one driver gains or loses time.")

# Custom HTML for explanations and dynamic insights (from Code 2)
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

# 2. UI Control Panel (from Code 1)
clicked, vals = control_panel([
    {"type":"number","label":"Year","key":"h2h_year","default":2024,"min":2018,"max":2026},
    {"type":"text",  "label":"Grand Prix","key":"h2h_gp","default":"Monza"},
    {"type":"select","label":"Session","key":"h2h_session","default":"Q","options":["Q","R","S","FP1","FP2","FP3"]},
    {"type":"text",  "label":"Driver A","key":"h2h_a","default":"VER"},
    {"type":"text",  "label":"Driver B","key":"h2h_b","default":"LEC"},
], button_label="Compare Drivers", cols_per_row=5)

if clicked:
    driver_a = vals["h2h_a"].upper()
    driver_b = vals["h2h_b"].upper()
    
    with st.spinner(f"Loading telemetry - {driver_a} vs {driver_b}..."):
        apply_f1_style()
        try:
            session = load_session(vals["h2h_year"], vals["h2h_gp"], vals["h2h_session"])
            comparison = compare_driver_telemetry(session, driver_a, driver_b)
        except Exception as e:
            st.error(f"Could not load comparison: {e}")
            st.stop()

    # Data Processing
    final_delta = comparison.delta_time["Delta"].iloc[-1]
    winner = driver_a if final_delta > 0 else driver_b
    loser = driver_b if winner == driver_a else driver_a
    gap_str = f"{abs(final_delta):.3f}s"
    
    lap_a_t = session.laps.pick_drivers(driver_a).pick_fastest()["LapTime"].total_seconds()
    lap_b_t = session.laps.pick_drivers(driver_b).pick_fastest()["LapTime"].total_seconds()

    # Winner Banner
    st.markdown(f"""
    <div style="background:linear-gradient(90deg,#1a2a0a,#0a1a0a);border:1px solid #27ae60;border-radius:4px;
    padding:1rem 1.5rem;color:#27ae60;font-size:1.1rem;font-weight:700;text-align:center;margin:.8rem 0;">
    🏆 {winner} was faster by {gap_str} over the lap — {loser} needs to find {gap_str} somewhere on track
    </div>
    """, unsafe_allow_html=True)

    # 3. Dynamic Metrics Row
    metrics_row([
        {"label": f"{driver_a} Best Lap", "value": f"{lap_a_t:.3f}s"},
        {"label": f"{driver_b} Best Lap", "value": f"{lap_b_t:.3f}s"},
        {"label": "Gap", "value": gap_str, "color": "gold"},
        {"label": "Faster Driver", "value": winner, "color": "accent"},
        {"label": "Grand Prix", "value": session.event["EventName"]},
    ])

    st.markdown('<div style="padding:0 2.5rem 4rem;">', unsafe_allow_html=True)

    # ── CHART 1: SPEED TRACE ──
    section_label("🚀 Speed Trace")
    st.markdown(EXPLAIN.format(text=f"""
    <strong>What this chart shows:</strong> Both drivers' speed (km/h) plotted against their distance around the lap (metres). 
    Where the two lines <strong>overlap</strong> — identical pace. Where one line is <strong>above the other</strong> — 
    that driver is going faster at that point. Peaks = straights. Troughs = corners (braking zones). The deepest dips are 
    the slowest corners where braking is heaviest and lap time can be won or lost most easily.
    """), unsafe_allow_html=True)

    fig1 = plot_speed_trace_comparison(comparison, session)
    st.pyplot(fig1, use_container_width=True)
    plt.close(fig1)

    # Dynamic Insight: Speed
    max_a = comparison.telemetry_a["Speed"].max()
    max_b = comparison.telemetry_b["Speed"].max()
    faster_top = driver_a if max_a > max_b else driver_b
    
    st.markdown(INSIGHT.format(text=f"""
    <h4 style="color:#fff;margin:.3rem 0;">🔍 Speed analysis</h4>
    <ul style="margin:.4rem 0;padding-left:1.2rem;line-height:1.8;">
        <li><strong>{driver_a}</strong> top speed: <strong>{max_a:.0f} km/h</strong></li>
        <li><strong>{driver_b}</strong> top speed: <strong>{max_b:.0f} km/h</strong></li>
        <li><strong>{faster_top}</strong> reaches higher top speed — could indicate better straight-line pace, earlier corner exit, or more aggressive DRS use.</li>
        <li>Look for where the lines <em>diverge in corners</em> — that's where driving style differences are most visible. Carrying more speed through a corner without losing the rear is the hardest skill in F1.</li>
    </ul>
    """), unsafe_allow_html=True)

    # ── CHART 2: TIME DELTA ──
    section_label("⏱️ Time Delta — Where the Lap Is Won and Lost")
    st.markdown(EXPLAIN.format(text=f"""
    <strong>What this chart shows:</strong> The <strong>cumulative time gap</strong> between {driver_a} and {driver_b} at every metre of the lap. 
    When the line moves <strong>downward</strong>, {driver_a} is gaining time. When it moves <strong>upward</strong>, {driver_b} is gaining time. 
    The final value at the end of the lap is the overall gap between the two fastest laps. 
    The steepest sections — where the line moves fastest — are the most critical parts of the circuit for this comparison.
    """), unsafe_allow_html=True)

    fig2 = plot_telemetry_delta(comparison, session)
    st.pyplot(fig2, use_container_width=True)
    plt.close(fig2)

    # Dynamic Insight: Time Delta
    delta_df = comparison.delta_time
    max_gain_idx = delta_df["Delta"].idxmax()
    max_loss_idx = delta_df["Delta"].idxmin()
    
    st.markdown(INSIGHT.format(text=f"""
    <h4 style="color:#fff;margin:.3rem 0;">🔍 Time delta breakdown</h4>
    <ul style="margin:.4rem 0;padding-left:1.2rem;line-height:1.8;">
        <li>Overall gap: <strong>{winner}</strong> faster by <strong>{gap_str}</strong></li>
        <li>Peak advantage for {driver_a}: at {delta_df.loc[max_loss_idx,'Distance']:.0f}m ({abs(delta_df.loc[max_loss_idx,'Delta']):.3f}s ahead)</li>
        <li>Peak advantage for {driver_b}: at {delta_df.loc[max_gain_idx,'Distance']:.0f}m ({abs(delta_df.loc[max_gain_idx,'Delta']):.3f}s ahead)</li>
        <li>The flatter sections of the chart = drivers are evenly matched there. Steep sections = one driver is significantly faster through that part of the circuit.</li>
    </ul>
    """), unsafe_allow_html=True)

    # ── CHART 3: THROTTLE & BRAKE ──
    section_label("🎮 Throttle & Brake Application")
    st.markdown(EXPLAIN.format(text=f"""
    <strong>What this chart shows:</strong> <em>Top panel</em> — throttle application (0% = fully off throttle, 100% = flat out). 
    <em>Bottom panel</em> — braking (100% = full brake, 0% = no brake). Where one driver is at 100% throttle and the other is not yet there — 
    the one at 100% is getting on the power earlier, which builds up a speed advantage down the following straight. 
    Earlier braking = more cautious or a different car setup. Later braking = aggressive, higher risk.
    """), unsafe_allow_html=True)

    fig3 = plot_throttle_brake_comparison(comparison, session)
    st.pyplot(fig3, use_container_width=True)
    plt.close(fig3)

    # Dynamic Insight: Throttle/Brake
    avg_throttle_a = comparison.telemetry_a["Throttle"].mean()
    avg_throttle_b = comparison.telemetry_b["Throttle"].mean()
    more_throttle = driver_a if avg_throttle_a > avg_throttle_b else driver_b
    
    st.markdown(INSIGHT.format(text=f"""
    <h4 style="color:#fff;margin:.3rem 0;">🔍 Driving style</h4>
    <ul style="margin:.4rem 0;padding-left:1.2rem;line-height:1.8;">
        <li><strong>{driver_a}</strong> average throttle: <strong>{avg_throttle_a:.1f}%</strong></li>
        <li><strong>{driver_b}</strong> average throttle: <strong>{avg_throttle_b:.1f}%</strong></li>
        <li><strong>{more_throttle}</strong> spends more time at full throttle — indicating either a more aggressive driving style, better car balance through corners, or a different setup allowing earlier power application.</li>
        <li>Look at corners where the throttle traces diverge significantly — these are where driving technique and car setup are creating meaningful lap time differences.</li>
    </ul>
    """), unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

else:
    st.markdown('<div style="padding:5rem 2.5rem;text-align:center;font-family:\'Titillium Web\',sans-serif;font-size:0.8rem;text-transform:uppercase;letter-spacing:0.15em;color:#2A2A2A;">Select two drivers above and press Compare Drivers</div>', unsafe_allow_html=True)