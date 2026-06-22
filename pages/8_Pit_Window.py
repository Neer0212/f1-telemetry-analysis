import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

st.set_page_config(page_title="Pit Window · F1 Analytics", page_icon="🛞", layout="wide")

from f1_analysis.visualization.ui_theme import inject_f1_css, page_header, section_label, metrics_row
from f1_analysis.core.session_loader import load_session
from f1_analysis.core.pit_window import calculate_pit_window, calculate_all_pit_windows
from f1_analysis.visualization.style import apply_f1_style, get_driver_color

inject_f1_css()
page_header("🛞", "Strategy Tool", "Pit Stop Window",
            "Optimal pit lap range, undercut threat detection, and overcut viability. Single driver or full field.")

with st.sidebar:
    st.markdown("### ⚙️ Settings")
    year          = st.number_input("Year", 2018, 2026, 2024)
    gp            = st.text_input("Grand Prix", "Bahrain")
    analysis_type = st.radio("Analysis", ["Single Driver", "All Drivers"])
    lap           = st.number_input("From Lap", min_value=1, value=25)
    next_compound = st.selectbox("Next Compound", ["MEDIUM","HARD","SOFT"])
    driver = None
    if analysis_type == "Single Driver":
        driver = st.text_input("Driver", "VER").upper()
    run = st.button("Calculate", type="primary")

if run:
    with st.spinner("Loading race data…"):
        apply_f1_style()
        try:
            session = load_session(year, gp, "R", telemetry=False, weather=False)
        except Exception as e:
            st.error(f"Failed to load session: {e}"); st.stop()
        total_laps = int(session.laps["LapNumber"].max())

    st.markdown('<div style="padding:0 2.5rem;">', unsafe_allow_html=True)

    if analysis_type == "Single Driver":
        if driver not in session.laps["Driver"].unique():
            st.error(f"Driver '{driver}' not found."); st.stop()
        result = calculate_pit_window(session, driver, current_lap=int(lap), next_compound=next_compound)

        metrics_row([
            {"label": "Earliest Pit",      "value": f"Lap {result.earliest_lap}"},
            {"label": "✅ Optimal Pit",     "value": f"Lap {result.optimal_lap}",      "color": "teal"},
            {"label": "Latest Pit",        "value": f"Lap {result.latest_lap}"},
            {"label": "Undercut Threat",   "value": f"Lap {result.undercut_threat_lap}" if result.undercut_threat_lap else "None",
             "color": "accent" if result.undercut_threat_lap else ""},
            {"label": "Overcut Viable",    "value": "Yes" if result.overcut_possible else "No"},
            {"label": "Compound",          "value": f"{result.current_compound} +{result.tyre_life}L"},
        ])

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**Gap ahead:**", help="")
            st.write(f"{result.gap_ahead_seconds:.2f}s" if result.gap_ahead_seconds else "N/A")
            st.markdown("**Gap behind:**")
            st.write(f"{result.gap_behind_seconds:.2f}s" if result.gap_behind_seconds else "N/A")
        with col_b:
            st.markdown("**Strategy reasoning:**")
            for r in result.reasoning:
                st.markdown(f"- {r}")

        section_label("Pit Window Visualisation")
        try: color = get_driver_color(driver, session)
        except: color = "#3671C6"

        fig, ax = plt.subplots(figsize=(13, 2.8))
        fig.patch.set_facecolor("#0D0D0D"); ax.set_facecolor("#0D0D0D")
        ax.barh(0, total_laps, left=0, height=0.45, color="#1C1C1C", alpha=0.8)
        ax.barh(0, result.latest_lap-result.earliest_lap, left=result.earliest_lap,
                height=0.45, color=color, alpha=0.9,
                label=f"Window L{result.earliest_lap}–L{result.latest_lap}")
        ax.axvline(result.optimal_lap, color="#FFD700", linewidth=2.5,
                   label=f"Optimal: Lap {result.optimal_lap}")
        if result.undercut_threat_lap:
            ax.axvline(result.undercut_threat_lap, color="#E8002D", linewidth=2,
                       linestyle="--", label=f"Undercut threat: Lap {result.undercut_threat_lap}")
        ax.axvline(int(lap), color="white", linewidth=1.5, linestyle=":",
                   label=f"Current: Lap {lap}")
        ax.set_xlim(0, total_laps+2); ax.set_ylim(-0.5, 0.5)
        ax.set_yticks([]); ax.set_xlabel("Lap Number", color="#888", fontsize=8)
        ax.tick_params(colors="#888")
        ax.legend(loc="upper left", fontsize=8.5, facecolor="#1A1A1A", labelcolor="white")
        ax.grid(True, axis="x", alpha=0.12, color="#FFFFFF")
        for sp in ax.spines.values(): sp.set_edgecolor("#2A2A2A")
        ax.set_title(f"{driver} — {session.event['EventName']} {year}", color="white", fontsize=10)
        fig.tight_layout(); st.pyplot(fig, use_container_width=True); plt.close(fig)

    else:
        with st.spinner("Calculating all drivers…"):
            df = calculate_all_pit_windows(session, analysis_lap=int(lap), next_compound=next_compound)
        st.dataframe(df, use_container_width=True)
        if df.empty: st.warning("No data available."); st.stop()

        section_label("Field Pit Windows — Gantt View")
        fig, ax = plt.subplots(figsize=(14, max(5, len(df)*0.5)))
        fig.patch.set_facecolor("#0D0D0D"); ax.set_facecolor("#0D0D0D")
        for i, row in df.iterrows():
            drv = row["Driver"]
            try: color = get_driver_color(drv, session)
            except: color = "#888888"
            ax.barh(i, row["LatestPit"]-row["EarliestPit"], left=row["EarliestPit"],
                    height=0.6, color=color, alpha=0.85)
            ax.plot(row["OptimalPit"], i, marker="|", color="#FFD700",
                    markersize=16, markeredgewidth=2.5)
            if pd.notna(row.get("UndercutThreatLap")):
                ax.plot(row["UndercutThreatLap"], i, marker="x", color="#E8002D",
                        markersize=10, markeredgewidth=2)
            ax.text(row["EarliestPit"]-0.5, i,
                    f"P{int(row['Position'])} {drv} ({row['Compound'][:1]}+{int(row['TyreAge'])})",
                    va="center", ha="right", fontsize=7.5, color="white")
        ax.set_xlim(0, total_laps+2); ax.set_yticks([])
        ax.set_xlabel("Lap Number", color="#888", fontsize=8)
        ax.tick_params(colors="#888")
        ax.set_title(f"Pit Windows — All Drivers — {session.event['EventName']} {year}",
                     color="white", fontsize=10)
        ax.grid(True, axis="x", alpha=0.12, color="#FFFFFF")
        for sp in ax.spines.values(): sp.set_edgecolor("#2A2A2A")
        fig.tight_layout(); st.pyplot(fig, use_container_width=True); plt.close(fig)

    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.markdown("""
<div style="padding:4rem 2.5rem; text-align:center; color:#333;
            font-family:'Titillium Web',sans-serif; font-size:0.8rem;
            text-transform:uppercase; letter-spacing:0.15em;">
    Configure parameters in the sidebar and press Calculate
</div>""", unsafe_allow_html=True)