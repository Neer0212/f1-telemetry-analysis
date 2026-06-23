import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
st.set_page_config(page_title="Pit Window", page_icon="🛞", layout="wide")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from f1_analysis.visualization.ui_theme import inject_f1_css, page_header, section_label, metrics_row
inject_f1_css()

EXPLAIN = """<div style="background:#141414;border:1px solid #2A2A2A;border-left:3px solid #E8002D;
padding:.9rem 1.2rem;margin:.8rem 0 1.2rem;color:#aaa;font-size:.88rem;line-height:1.65;
font-family:'Inter',sans-serif;">{text}</div>"""

INSIGHT = """<div style="background:#0D0D0D;border:1px solid #2A2A2A;border-top:2px solid #E8002D;
padding:1rem 1.3rem;margin-top:1rem;font-family:'Inter',sans-serif;">
<div style="font-family:'Titillium Web',sans-serif;font-size:.65rem;font-weight:700;
text-transform:uppercase;letter-spacing:.2em;color:#E8002D;margin-bottom:.6rem;">Key Insights</div>
{text}</div>"""

import pandas as pd

from f1_analysis.core.session_loader import load_session
from f1_analysis.core.pit_window import calculate_pit_window, calculate_all_pit_windows
from f1_analysis.visualization.style import apply_f1_style, get_driver_color


# ── Explainer ─────────────────────────────────────────────────────────────────
with st.expander("📖 How does pit strategy work? (click to learn)"):
    st.markdown("""
**The pit stop dilemma** is one of the most exciting parts of F1 strategy. Every pit stop costs roughly 20–25 seconds of track time. To make a pit stop worthwhile, a driver needs to gain back that time through faster laps on fresh tyres.

**Undercut:** You pit *before* your rival. Your fresh tyres are faster, so you lap quicker while they're still on worn tyres. When *they* pit, you've built enough of a gap that you emerge in front of them. This is the most common overtaking method in modern F1.

**Overcut:** You stay out *longer* than your rival. If they're stuck in traffic after their pit stop, or if your worn tyres are still competitive (because the circuit naturally degrades gently), you can build a gap and emerge ahead when you finally do pit.

**Tyre degradation** is how much slower the car gets each lap as the tyre wears. High degradation = urgent need to pit. Low degradation = viable to stay out longer.

The calculator below applies real race data to estimate these windows for any driver at any lap of any race.
    """)

st.sidebar.header("Settings")
year          = st.sidebar.number_input("Year", 2018, 2026, 2024)
gp            = st.sidebar.text_input("Grand Prix", "Bahrain")
analysis_type = st.sidebar.radio("Mode", ["Single Driver", "All Drivers"])
lap           = st.sidebar.number_input("Analyze at Lap", min_value=1, value=25)
next_compound = st.sidebar.selectbox("Planned next compound", ["MEDIUM", "HARD", "SOFT"])
driver = None
if analysis_type == "Single Driver":
    driver = st.sidebar.text_input("Driver", "VER").upper()

if st.sidebar.button("Calculate Pit Window", type="primary"):
    with st.spinner("Loading race data..."):
        apply_f1_style()
        try:
            session    = load_session(year, gp, "R", telemetry=False, weather=False)
        except Exception as e:
            st.error(f"Could not load session: {e}"); st.stop()
        total_laps = int(session.laps["LapNumber"].max())

    if analysis_type == "Single Driver":
        driver = driver.upper()
        if driver not in session.laps["Driver"].unique():
            st.error(f"Driver '{driver}' not found."); st.stop()
        result = calculate_pit_window(session, driver, current_lap=int(lap), next_compound=next_compound)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Earliest viable pit", f"Lap {result.earliest_lap}")
        c2.metric("✅ Optimal pit lap", f"Lap {result.optimal_lap}")
        c3.metric("Latest before losing out", f"Lap {result.latest_lap}")
        c4.metric("Undercut threat", f"Lap {result.undercut_threat_lap}" if result.undercut_threat_lap else "None")

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"""
| Detail | Value |
|---|---|
| **Current compound** | {result.current_compound} |
| **Tyre age** | {result.tyre_life} laps |
| **Current position** | P{result.current_position} |
| **Gap to car ahead** | {f"{result.gap_ahead_seconds:.2f}s" if result.gap_ahead_seconds else "N/A"} |
| **Gap to car behind** | {f"{result.gap_behind_seconds:.2f}s" if result.gap_behind_seconds else "N/A"} |
| **Overcut viable** | {"✅ Yes" if result.overcut_possible else "❌ No"} |
""")
        with col_b:
            st.markdown("**Strategy reasoning:**")
            for r in result.reasoning:
                st.markdown(f"- {r}")

        # ── Visual ─────────────────────────────────────────────────
        st.markdown("---")
        st.subheader("📊 Pit Window Visualisation")
        st.markdown("""<div style="background:#141414;border:1px solid #2A2A2A;border-left:3px solid #E8002D;padding:.9rem 1.2rem;margin:.8rem 0 1.2rem;color:#aaa;font-size:.88rem;line-height:1.65;font-family:'Inter',sans-serif;">
        <strong>How to read this chart:</strong> The coloured bar shows the
        <strong>viable pit window</strong> — laps where pitting makes strategic sense.
        The <strong>gold vertical line</strong> is the recommended optimal lap.
        The <strong>red dashed line</strong> (if shown) is when an undercut from the car
        behind becomes a serious threat — you should ideally pit before this point.
        The <strong>white dotted line</strong> is your current lap position.
        </div>""", unsafe_allow_html=True)

        try: color = get_driver_color(driver, session)
        except: color = "#3671C6"

        fig, ax = plt.subplots(figsize=(13, 2.5))
        fig.patch.set_facecolor("#0f0f0f"); ax.set_facecolor("#0f0f0f")
        ax.barh(0, total_laps, left=0, height=0.4, color="#2C2C2C", alpha=0.6)
        ax.barh(0, result.latest_lap-result.earliest_lap, left=result.earliest_lap,
                height=0.4, color=color, alpha=0.85,
                label=f"Window: Lap {result.earliest_lap}–{result.latest_lap}")
        ax.axvline(result.optimal_lap, color="#FFD700", linewidth=2.5,
                   label=f"Optimal: Lap {result.optimal_lap}")
        if result.undercut_threat_lap:
            ax.axvline(result.undercut_threat_lap, color="#E74C3C", linewidth=2, linestyle="--",
                       label=f"Undercut threat: Lap {result.undercut_threat_lap}")
        ax.axvline(int(lap), color="white", linewidth=1.5, linestyle=":",
                   label=f"Current: Lap {lap}")
        ax.set_xlim(0, total_laps+2); ax.set_ylim(-0.5, 0.5); ax.set_yticks([])
        ax.set_xlabel("Lap Number", color="white"); ax.tick_params(colors="white")
        ax.legend(loc="upper left", fontsize=9, facecolor="#1a1a1a", labelcolor="white")
        ax.grid(True, axis="x", alpha=0.3)
        ax.set_title(f"Pit Window — {driver} — {session.event['EventName']} {year}", color="white")
        fig.tight_layout(); st.pyplot(fig); plt.close(fig)

        st.markdown(f"""<div style="background:#0D0D0D;border:1px solid #2A2A2A;border-top:2px solid #E8002D;padding:1rem 1.3rem;margin-top:1rem;font-family:'Inter',sans-serif;"><div style="font-family:'Titillium Web',sans-serif;font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.2em;color:#E8002D;margin-bottom:.6rem;">Key Insights</div><div style="color:#ccc;font-size:.88rem;font-family:'Inter',sans-serif;"><h4 style="color:#fff;margin:.3rem 0;">🔍 What to do</h4>
        <ul>
        <li>The <strong>ideal pit lap is {result.optimal_lap}</strong>. Pitting here balances
        recovering the pit stop time loss with the fresh tyre advantage.</li>
        <li>{"⚠️ <strong>Undercut risk:</strong> The car behind could undercut by Lap " + str(result.undercut_threat_lap) + ". Consider pitting on Lap " + str(result.optimal_lap) + " or earlier." if result.undercut_threat_lap else "✅ No immediate undercut threat from behind."}</li>
        <li>{"✅ <strong>Overcut viable</strong> — low tyre degradation means staying out longer is a realistic option if track position is more valuable than fresh rubber." if result.overcut_possible else "❌ Overcut not recommended — degradation is too high to benefit from staying out longer."}</li>
        </ul></div></div>""", unsafe_allow_html=True)

    else:
        with st.spinner("Calculating all drivers..."):
            df = calculate_all_pit_windows(session, analysis_lap=int(lap), next_compound=next_compound)
        if df.empty:
            st.warning("No data."); st.stop()

        st.markdown("""<div style="background:#141414;border:1px solid #2A2A2A;border-left:3px solid #E8002D;padding:.9rem 1.2rem;margin:.8rem 0 1.2rem;color:#aaa;font-size:.88rem;line-height:1.65;font-family:'Inter',sans-serif;">
        <strong>What this shows:</strong> Each row is one driver. The coloured bar = their viable pit window.
        The gold marker = recommended optimal lap. Red ✕ = undercut threat from behind.
        Drivers whose windows overlap each other are the most likely to be involved in
        strategic pit stop battles.
        </div>""", unsafe_allow_html=True)

        st.dataframe(df, use_container_width=True)

        fig, ax = plt.subplots(figsize=(14, max(5, len(df)*0.5)))
        fig.patch.set_facecolor("#0f0f0f"); ax.set_facecolor("#0f0f0f")
        for i, row in df.iterrows():
            drv = row["Driver"]
            try: c = get_driver_color(drv, session)
            except: c = "#888"
            ax.barh(i, row["LatestPit"]-row["EarliestPit"], left=row["EarliestPit"], height=0.6, color=c, alpha=0.8)
            ax.plot(row["OptimalPit"], i, marker="|", color="#FFD700", markersize=16, markeredgewidth=2.5)
            if pd.notna(row.get("UndercutThreatLap")):
                ax.plot(row["UndercutThreatLap"], i, marker="x", color="#E74C3C", markersize=10, markeredgewidth=2)
            ax.text(row["EarliestPit"]-0.5, i,
                    f"P{int(row['Position'])} {drv} ({row['Compound'][:1]}+{int(row['TyreAge'])})",
                    va="center", ha="right", fontsize=8, color="white")
        ax.set_xlim(0, total_laps+2); ax.set_yticks([])
        ax.set_xlabel("Lap Number", color="white"); ax.tick_params(colors="white")
        ax.set_title(f"Pit Windows — All Drivers — {session.event['EventName']} {year}\n│=optimal  ✕=undercut threat",
                     color="white")
        ax.grid(True, axis="x", alpha=0.3); fig.tight_layout()
        st.pyplot(fig); plt.close(fig)