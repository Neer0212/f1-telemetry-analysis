import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd

from f1_analysis.core.session_loader import load_session
from f1_analysis.core.pit_window import calculate_pit_window, calculate_all_pit_windows
from f1_analysis.visualization.style import apply_f1_style, get_driver_color

st.set_page_config(page_title="Pit Window", page_icon="🛞", layout="wide")
st.title("🛞 Pit Stop Window Calculator")
st.markdown("Calculates the optimal pit lap range, undercut threat, and overcut viability for any driver at any point in a race.")

st.sidebar.header("Settings")
year            = st.sidebar.number_input("Year", 2018, 2026, 2024)
gp              = st.sidebar.text_input("Grand Prix", "Bahrain")
analysis_type   = st.sidebar.radio("Analysis", ["Single Driver", "All Drivers"])
lap             = st.sidebar.number_input("Analyze from Lap", min_value=1, value=25)
next_compound   = st.sidebar.selectbox("Next Compound", ["MEDIUM", "HARD", "SOFT"])

driver = None
if analysis_type == "Single Driver":
    driver = st.sidebar.text_input("Driver", "VER").upper()

if st.sidebar.button("Calculate", type="primary"):
    with st.spinner("Loading race data and calculating pit windows..."):
        apply_f1_style()
        try:
            session = load_session(year, gp, "R", telemetry=False, weather=False)
        except Exception as e:
            st.error(f"Failed to load session: {e}")
            st.stop()

        total_laps = int(session.laps["LapNumber"].max())

    if analysis_type == "Single Driver":
        if driver not in session.laps["Driver"].unique():
            st.error(f"Driver '{driver}' not found.")
            st.stop()

        result = calculate_pit_window(session, driver, current_lap=int(lap),
                                      next_compound=next_compound)

        # ── Metrics ───────────────────────────────────────────────────
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Earliest Pit", f"Lap {result.earliest_lap}")
        c2.metric("✅ Optimal Pit", f"Lap {result.optimal_lap}")
        c3.metric("Latest Pit", f"Lap {result.latest_lap}")
        c4.metric("Undercut Threat",
                  f"Lap {result.undercut_threat_lap}" if result.undercut_threat_lap else "None")

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"**Gap ahead:** {f'{result.gap_ahead_seconds:.2f}s' if result.gap_ahead_seconds else 'N/A'}")
            st.markdown(f"**Gap behind:** {f'{result.gap_behind_seconds:.2f}s' if result.gap_behind_seconds else 'N/A'}")
            st.markdown(f"**Overcut viable:** {'✅ Yes' if result.overcut_possible else '❌ No'}")
            st.markdown(f"**Compound:** {result.current_compound} (age: {result.tyre_life} laps)")
        with col_b:
            st.markdown("**Reasoning:**")
            for r in result.reasoning:
                st.markdown(f"- {r}")

        # ── Visual window bar ─────────────────────────────────────────
        try:
            color = get_driver_color(driver, session)
        except Exception:
            color = "#3671C6"

        fig, ax = plt.subplots(figsize=(13, 2.5))
        fig.patch.set_facecolor("#0f0f0f")
        ax.set_facecolor("#0f0f0f")

        ax.barh(0, total_laps, left=0, height=0.4, color="#2C2C2C", alpha=0.6)
        window_w = result.latest_lap - result.earliest_lap
        ax.barh(0, window_w, left=result.earliest_lap, height=0.4,
                color=color, alpha=0.85, label=f"Window L{result.earliest_lap}–L{result.latest_lap}")
        ax.axvline(result.optimal_lap, color="#FFD700", linewidth=2.5,
                   label=f"Optimal: Lap {result.optimal_lap}")
        if result.undercut_threat_lap:
            ax.axvline(result.undercut_threat_lap, color="#E74C3C", linewidth=2,
                       linestyle="--", label=f"Undercut threat: Lap {result.undercut_threat_lap}")
        ax.axvline(int(lap), color="white", linewidth=1.5, linestyle=":",
                   label=f"Current: Lap {lap}")

        ax.set_xlim(0, total_laps + 2)
        ax.set_ylim(-0.5, 0.5)
        ax.set_yticks([])
        ax.set_xlabel("Lap Number", color="white")
        ax.tick_params(colors="white")
        ax.legend(loc="upper left", fontsize=9, facecolor="#1a1a1a", labelcolor="white")
        ax.grid(True, axis="x", alpha=0.3)
        ax.set_title(f"Pit Window — {driver} — {session.event['EventName']} {year}",
                     color="white")
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    else:
        # All drivers
        with st.spinner("Calculating windows for all drivers..."):
            df = calculate_all_pit_windows(session, analysis_lap=int(lap),
                                           next_compound=next_compound)

        st.dataframe(df, use_container_width=True)

        # ── Gantt-style chart ─────────────────────────────────────────
        if df.empty:
            st.warning("No data available.")
            st.stop()

        fig, ax = plt.subplots(figsize=(14, max(5, len(df) * 0.5)))
        fig.patch.set_facecolor("#0f0f0f")
        ax.set_facecolor("#0f0f0f")

        for i, row in df.iterrows():
            drv = row["Driver"]
            try:
                color = get_driver_color(drv, session)
            except Exception:
                color = "#888888"
            width = row["LatestPit"] - row["EarliestPit"]
            ax.barh(i, width, left=row["EarliestPit"], height=0.6,
                    color=color, alpha=0.8)
            ax.plot(row["OptimalPit"], i, marker="|", color="#FFD700",
                    markersize=16, markeredgewidth=2.5)
            if pd.notna(row.get("UndercutThreatLap")):
                ax.plot(row["UndercutThreatLap"], i, marker="x", color="#E74C3C",
                        markersize=10, markeredgewidth=2)
            ax.text(row["EarliestPit"] - 0.5, i,
                    f"P{int(row['Position'])} {drv} ({row['Compound'][:1]}+{int(row['TyreAge'])})",
                    va="center", ha="right", fontsize=8, color="white")

        ax.set_xlim(0, total_laps + 2)
        ax.set_yticks([])
        ax.set_xlabel("Lap Number", color="white")
        ax.tick_params(colors="white")
        ax.set_title(
            f"Pit Windows — All Drivers — {session.event['EventName']} {year}\n"
            "│ = optimal  ✕ = undercut threat",
            color="white",
        )
        ax.grid(True, axis="x", alpha=0.3)
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)