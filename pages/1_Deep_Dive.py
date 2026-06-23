import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

st.set_page_config(page_title="Session Deep Dive · F1 Analytics", page_icon="📊", layout="wide")

from f1_analysis.visualization.ui_theme import inject_f1_css, page_header, section_label, metrics_row
from f1_analysis.core.session_loader import load_session
from f1_analysis.core.lap_analysis import (
    fastest_laps_by_driver, clean_lap_times, laps_to_seconds,
    race_pace_summary, stint_summary,
)
from f1_analysis.visualization.style import apply_f1_style
from f1_analysis.visualization.plots import (
    plot_lap_time_distribution, plot_race_pace, plot_tire_strategy,
)

inject_f1_css()
page_header("📊", "Session Analysis", "Session Deep Dive",
            "Complete lap time, race pace and tyre strategy breakdown for any F1 session since 2018.")

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
{text}
</div>"""

SESSION_LABELS = {"R":"Race","Q":"Qualifying","S":"Sprint","FP1":"Free Practice 1","FP2":"Free Practice 2","FP3":"Free Practice 3"}

with st.sidebar:
    st.markdown("### ⚙️ Settings")
    year          = st.number_input("Year", 2018, 2026, 2024)
    gp            = st.text_input("Grand Prix", "Monza")
    session_type  = st.selectbox("Session", ["R","Q","S","FP1","FP2","FP3"])
    drivers_input = st.text_input("Drivers (space-separated)", "VER LEC NOR HAM RUS")
    run = st.button("Run Analysis", type="primary")

if run:
    drivers = [d.strip().upper() for d in drivers_input.split() if d.strip()]
    with st.spinner(f"Loading {year} {gp} — {SESSION_LABELS.get(session_type,session_type)}..."):
        apply_f1_style()
        try:
            session = load_session(year, gp, session_type)
        except Exception as e:
            st.error(f"Could not load session: {e}"); st.stop()

    available = sorted(session.laps["Driver"].unique())
    drivers   = [d for d in drivers if d in available]
    if not drivers:
        clean   = clean_lap_times(session.laps)
        fastest = fastest_laps_by_driver(clean)
        drivers = fastest["Driver"].head(6).tolist()

    clean   = clean_lap_times(session.laps)
    fastest = fastest_laps_by_driver(clean)
    pace_df = race_pace_summary(clean[clean["Driver"].isin(drivers)])
    stints  = stint_summary(session.laps)

    pole    = fastest.iloc[0]
    p2      = fastest.iloc[1] if len(fastest) > 1 else None
    gap     = (fastest.iloc[1]["LapTimeSeconds"] - pole["LapTimeSeconds"]) if p2 is not None else 0

    metrics_row([
        {"label":"Fastest Driver","value":pole["Driver"],"color":"accent"},
        {"label":"Fastest Lap","value":f"{pole['LapTimeSeconds']:.3f}s"},
        {"label":"Gap P1→P2","value":f"+{gap:.3f}s" if gap else "—","color":"gold"},
        {"label":"Drivers Analyzed","value":str(len(drivers))},
        {"label":"Session","value":SESSION_LABELS.get(session_type,session_type)},
    ])

    st.markdown("<div style='padding:0 2rem'>", unsafe_allow_html=True)

    # ── CHART 1: LAP TIME DISTRIBUTION ───────────────────────────────
    section_label("Lap Time Distribution")
    st.markdown(EXPLAIN.format(text="""
<strong>What this chart shows:</strong> Each "violin" shape represents one driver's full set of lap times.
The <strong>width</strong> at any height shows how many laps were done at that time —
a fat middle means the driver consistently hit that pace. The <strong>horizontal line</strong> is the median.
A <strong>narrow violin</strong> = very consistent. A <strong>wide, tall violin</strong> = pace varied a lot
(safety cars, traffic, tyre management). Use this to judge who had the most reliable rhythm all race.
"""), unsafe_allow_html=True)

    fig = plot_lap_time_distribution(session, drivers)
    st.pyplot(fig, use_container_width=True); plt.close(fig)

    if not pace_df.empty and "StdLapTime" in pace_df.columns:
        best_con  = pace_df.loc[pace_df["StdLapTime"].idxmin()]
        worst_con = pace_df.loc[pace_df["StdLapTime"].idxmax()]
        st.markdown(INSIGHT.format(text=f"""
<ul style="margin:.4rem 0;padding-left:1.2rem;color:#ccc;font-size:.85rem;line-height:1.8;">
<li><strong style="color:#fff">{best_con['Driver']}</strong> was the most consistent driver —
lap times varied by only <strong>±{best_con['StdLapTime']:.2f}s</strong> from lap to lap.</li>
<li><strong style="color:#fff">{worst_con['Driver']}</strong> showed the most variation
(±{worst_con['StdLapTime']:.2f}s) — likely traffic, tyre management, or safety car laps.</li>
<li>In a <strong>race</strong>, a tight distribution means the driver found a consistent rhythm every lap.
In <strong>qualifying</strong>, only the single fastest lap matters.</li>
</ul>"""), unsafe_allow_html=True)

    # ── CHART 2: RACE PACE ────────────────────────────────────────────
    if session_type == "R":
        section_label("Race Pace Over Laps")
        st.markdown(EXPLAIN.format(text="""
<strong>What this chart shows:</strong> Each driver's lap time across every lap of the race,
smoothed with a 3-lap rolling average to remove noise. A <strong>rising line</strong> = tyre degradation
(getting slower). A <strong>sudden drop</strong> after a pit stop = fresh tyres. The
<strong>scattered dots</strong> behind each line are raw lap times — spikes up = safety car or traffic.
"""), unsafe_allow_html=True)

        fig = plot_race_pace(session, drivers)
        st.pyplot(fig, use_container_width=True); plt.close(fig)

        if not pace_df.empty:
            fastest_avg = pace_df.iloc[0]
            st.markdown(INSIGHT.format(text=f"""
<ul style="margin:.4rem 0;padding-left:1.2rem;color:#ccc;font-size:.85rem;line-height:1.8;">
<li><strong style="color:#fff">{fastest_avg['Driver']}</strong> had the best average race pace:
<strong>{fastest_avg['MeanLapTime']:.3f}s</strong> per lap.</li>
<li>Tyre degradation appears as a gradual upward drift each stint — steeper drift means the
compound or car balance is struggling more with wear.</li>
<li>Gaps between drivers on this chart = raw pace difference when both are on the same strategy.</li>
</ul>"""), unsafe_allow_html=True)

    # ── CHART 3: TYRE STRATEGY ────────────────────────────────────────
    section_label("Tyre Strategy")
    st.markdown(EXPLAIN.format(text="""
<strong>What this chart shows:</strong> Each row = one driver. Coloured blocks show which tyre
compound they were using in each stint. <strong style="color:#DA291C">Red = Soft</strong>
(fastest, wears quickly), <strong style="color:#FFD700">Yellow = Medium</strong> (balanced),
<strong style="color:#E8E8E8">White = Hard</strong> (slowest, most durable).
Block length = how many laps they stayed on that set. A very long soft stint = risky strategy.
A long hard stint = conservative one-stop approach.
"""), unsafe_allow_html=True)

    fig = plot_tire_strategy(session, drivers=drivers)
    st.pyplot(fig, use_container_width=True); plt.close(fig)

    if not stints.empty:
        sel = stints[stints["Driver"].isin(drivers)].copy()
        if not sel.empty:
            longest = sel.loc[sel["LapCount"].idxmax()]
            st.markdown(INSIGHT.format(text=f"""
<ul style="margin:.4rem 0;padding-left:1.2rem;color:#ccc;font-size:.85rem;line-height:1.8;">
<li><strong style="color:#fff">Longest stint:</strong> {longest['Driver']} ran
<strong>{int(longest['LapCount'])} laps</strong> on <strong>{longest['Compound']}</strong> tyres
— averaging <strong>{longest['AvgLapTime']:.3f}s</strong> per lap.</li>
<li>Drivers who pit earlier sacrifice track position short-term but gain in tyre performance.
Those who stay out longer (overcut) bet on fresh-tyre opponents getting stuck in traffic.</li>
</ul>"""), unsafe_allow_html=True)
            sel["AvgLapTime"] = sel["AvgLapTime"].round(3)
            st.dataframe(sel[["Driver","Stint","Compound","LapCount","AvgLapTime"]],
                         use_container_width=True, hide_index=True)

    # ── SUMMARY TABLE ─────────────────────────────────────────────────
    section_label("Full Session Summary")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("##### ⚡ Fastest Laps")
        top = fastest[["Driver","LapTimeSeconds","Compound"]].head(10).copy()
        top["LapTimeSeconds"] = top["LapTimeSeconds"].round(3)
        top.insert(0,"Pos",range(1,len(top)+1))
        st.dataframe(top, use_container_width=True, hide_index=True)
    with col_b:
        st.markdown("##### 📊 Pace Summary (selected drivers)")
        if not pace_df.empty:
            disp = pace_df.round(3).copy()
            disp.insert(0,"Rank",range(1,len(disp)+1))
            st.dataframe(disp, use_container_width=True, hide_index=True)
            st.caption("MeanLapTime = average lap (seconds). StdLapTime = consistency — lower is better.")

    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.markdown("""
<div style="text-align:center;padding:4rem 2rem;color:#333;
font-family:'Titillium Web',sans-serif;font-size:.8rem;font-weight:700;
text-transform:uppercase;letter-spacing:.2em;">
Enter year, grand prix and session type, then press Run Analysis
</div>""", unsafe_allow_html=True)
