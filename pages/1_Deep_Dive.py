import streamlit as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

from f1_analysis.core.session_loader import load_session
from f1_analysis.core.lap_analysis import (
    fastest_laps_by_driver, clean_lap_times, laps_to_seconds,
    race_pace_summary, stint_summary,
)
from f1_analysis.visualization.style import apply_f1_style
from f1_analysis.visualization.plots import (
    plot_lap_time_distribution, plot_race_pace, plot_tire_strategy,
)

st.set_page_config(page_title="Session Deep Dive", page_icon="📊", layout="wide")

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.page-header {
    background: linear-gradient(90deg, #1a0000, #0a0a1e);
    border-left: 4px solid #e10600;
    padding: 1.2rem 1.5rem;
    border-radius: 0 8px 8px 0;
    margin-bottom: 1.5rem;
}
.page-header h1 { color: #fff; margin: 0; font-size: 1.8rem; }
.page-header p  { color: #aaa; margin: 0.3rem 0 0; font-size: 0.95rem; }
.explain-box {
    background: #111827;
    border: 1px solid #1f2937;
    border-left: 3px solid #e10600;
    border-radius: 6px;
    padding: 0.9rem 1.2rem;
    margin: 0.8rem 0 1.2rem;
    color: #d1d5db;
    font-size: 0.9rem;
    line-height: 1.6;
}
.insight-box {
    background: #0d1117;
    border: 1px solid #21262d;
    border-radius: 8px;
    padding: 1rem 1.3rem;
    margin-top: 1rem;
}
.insight-box h4 { color: #e10600; margin: 0 0 0.6rem; font-size: 1rem; }
.stat-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 0.9rem;
    text-align: center;
}
.stat-card .val { color: #e10600; font-size: 1.6rem; font-weight: 900; }
.stat-card .lbl { color: #8b949e; font-size: 0.78rem; margin-top: 2px; }
</style>
<div class="page-header">
    <h1>📊 Session Deep Dive</h1>
    <p>Complete lap time, race pace and tyre strategy breakdown for any F1 session since 2018.</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.header("Select Session")
year          = st.sidebar.number_input("Year", 2018, 2026, 2024)
gp            = st.sidebar.text_input("Grand Prix", "Monza")
session_type  = st.sidebar.selectbox("Session Type", ["R", "Q", "S", "FP1", "FP2", "FP3"])
drivers_input = st.sidebar.text_input("Drivers (space-separated)", "VER LEC NOR HAM RUS")

SESSION_LABELS = {"R": "Race", "Q": "Qualifying", "S": "Sprint",
                  "FP1": "Free Practice 1", "FP2": "Free Practice 2", "FP3": "Free Practice 3"}

if st.sidebar.button("Run Analysis", type="primary"):
    drivers = [d.strip() for d in drivers_input.upper().split() if d.strip()]
    with st.spinner(f"Loading {year} {gp} — {SESSION_LABELS.get(session_type, session_type)}..."):
        apply_f1_style()
        try:
            session = load_session(year, gp, session_type)
        except Exception as e:
            st.error(f"Could not load session: {e}")
            st.stop()

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

    event_name = session.event["EventName"]

    # ── Hero stats ────────────────────────────────────────────────────
    pole = fastest.iloc[0]
    p2   = fastest.iloc[1] if len(fastest) > 1 else None
    gap  = (fastest.iloc[1]["LapTimeSeconds"] - pole["LapTimeSeconds"]) if p2 is not None else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Fastest Driver", pole["Driver"])
    c2.metric("Fastest Lap", f"{pole['LapTimeSeconds']:.3f}s")
    c3.metric("Gap P1 → P2", f"+{gap:.3f}s" if gap else "—")
    c4.metric("Drivers Analyzed", len(drivers))

    # ════════════════════════════════════════════════════════════════
    # CHART 1: LAP TIME DISTRIBUTION
    # ════════════════════════════════════════════════════════════════
    st.markdown("---")
    st.subheader("🎻 Lap Time Distribution")
    st.markdown("""<div class="explain-box">
    <strong>What this chart shows:</strong> Each "violin" shape represents one driver.
    The <strong>width</strong> of the violin shows how many laps were done at that time —
    a wide middle means most laps were clustered at that pace.
    The <strong>horizontal line</strong> inside is the median lap time.
    A tall, narrow violin = very consistent driver. A wide, spread violin = inconsistent or
    the car's pace varied a lot (could be safety cars, traffic, or deliberate tyre management).
    </div>""", unsafe_allow_html=True)

    fig = plot_lap_time_distribution(session, drivers)
    st.pyplot(fig); plt.close(fig)

    # Insight: who was most consistent?
    if not pace_df.empty and "StdLapTime" in pace_df.columns:
        most_consistent = pace_df.loc[pace_df["StdLapTime"].idxmin()]
        least_consistent = pace_df.loc[pace_df["StdLapTime"].idxmax()]
        st.markdown(f"""<div class="insight-box"><h4>🔍 What this tells us</h4>
        <ul>
        <li><strong>{most_consistent['Driver']}</strong> was the most consistent driver —
        their lap times varied by only <strong>±{most_consistent['StdLapTime']:.2f}s</strong> from lap to lap.</li>
        <li><strong>{least_consistent['Driver']}</strong> showed the most variation
        (±{least_consistent['StdLapTime']:.2f}s) — likely due to traffic, tyre
        management, or a safety car period affecting their laps.</li>
        <li>In {'qualifying' if session_type == 'Q' else 'a race'}, a tighter distribution
        means the driver could find a consistent rhythm every lap — a key indicator of
        car and driver confidence.</li>
        </ul></div>""", unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════
    # CHART 2: RACE PACE
    # ════════════════════════════════════════════════════════════════
    if session_type == "R":
        st.markdown("---")
        st.subheader("📈 Race Pace")
        st.markdown("""<div class="explain-box">
        <strong>What this chart shows:</strong> Each driver's lap time across every lap of the race,
        smoothed with a 3-lap rolling average to remove noise. A <strong>rising line</strong> means
        the car is getting slower — classic tyre degradation. A <strong>sudden drop</strong> after a
        pit stop means the driver rejoined with fresh tyres and immediately went faster.
        The <strong>scattered dots</strong> behind each line are the raw lap times — useful for
        spotting safety car laps (big spike upward) or push laps (dip below the average).
        </div>""", unsafe_allow_html=True)

        fig = plot_race_pace(session, drivers)
        st.pyplot(fig); plt.close(fig)

        # Find fastest average pace
        if not pace_df.empty:
            fastest_avg = pace_df.iloc[0]
            st.markdown(f"""<div class="insight-box"><h4>🔍 What this tells us</h4>
            <ul>
            <li><strong>{fastest_avg['Driver']}</strong> had the best average race pace at
            <strong>{fastest_avg['MeanLapTime']:.3f}s</strong> per lap.</li>
            <li>Tyre degradation is visible as a gradual upward drift in each stint.
            Steeper drift = compound or car struggling more with wear.</li>
            <li>Gaps between drivers on this chart represent raw pace differences —
            how fast each car is when both are on the same strategy.</li>
            </ul></div>""", unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════
    # CHART 3: TYRE STRATEGY
    # ════════════════════════════════════════════════════════════════
    st.markdown("---")
    st.subheader("🛞 Tyre Strategy")
    st.markdown("""<div class="explain-box">
    <strong>What this chart shows:</strong> Each row is one driver. The coloured blocks show
    which tyre compound they were using during each stint of the race.
    <strong>Red = Soft</strong> (fastest, wears quickly),
    <strong>Yellow = Medium</strong> (balanced),
    <strong>White = Hard</strong> (slowest, most durable).
    The length of each block = how many laps they stayed on that set.
    A longer block on softs = aggressive strategy risking the tyre.
    Very long hard stints = conservative "one-stop" approach.
    </div>""", unsafe_allow_html=True)

    fig = plot_tire_strategy(session, drivers=drivers)
    st.pyplot(fig); plt.close(fig)

    # Stint summary table with explanation
    if not stints.empty:
        sel_stints = stints[stints["Driver"].isin(drivers)].copy()
        if not sel_stints.empty:
            sel_stints["AvgLapTime"] = sel_stints["AvgLapTime"].round(3)
            st.markdown(f"""<div class="insight-box"><h4>🔍 Strategy breakdown</h4></div>""",
                        unsafe_allow_html=True)
            st.dataframe(
                sel_stints[["Driver","Stint","Compound","LapCount","AvgLapTime"]],
                use_container_width=True,
            )
            # Who ran longest stint?
            longest = sel_stints.loc[sel_stints["LapCount"].idxmax()]
            st.markdown(
                f"**Longest stint:** {longest['Driver']} ran {int(longest['LapCount'])} laps "
                f"on {longest['Compound']} tyres — averaging **{longest['AvgLapTime']:.3f}s** per lap."
            )

    # ════════════════════════════════════════════════════════════════
    # TEXT SUMMARY TABLE
    # ════════════════════════════════════════════════════════════════
    st.markdown("---")
    st.subheader("📋 Full Session Summary")
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("#### ⚡ Fastest Laps — All Drivers")
        top10 = fastest[["Driver","LapTimeSeconds","Compound"]].head(10).copy()
        top10["LapTimeSeconds"] = top10["LapTimeSeconds"].round(3)
        top10.insert(0, "Pos", range(1, len(top10)+1))
        st.dataframe(top10, use_container_width=True, hide_index=True)

    with col_b:
        st.markdown("#### 📊 Race Pace — Selected Drivers")
        if not pace_df.empty:
            display = pace_df.round(3).copy()
            display.insert(0, "Rank", range(1, len(display)+1))
            st.dataframe(display, use_container_width=True, hide_index=True)
            st.caption("MeanLapTime = average lap. MedianLapTime = middle lap (less affected by outliers). StdLapTime = consistency (lower = more consistent).")