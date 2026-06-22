import streamlit as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
import sys
import numpy as np
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from f1_analysis.core.session_loader import load_session
from f1_analysis.visualization.style import apply_f1_style

# Import everything from script 07 directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from importlib import import_module
import importlib.util

def _load_race_story_module():
    spec = importlib.util.spec_from_file_location(
        "race_story",
        Path(__file__).resolve().parent.parent / "scripts" / "07_race_story.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["race_story"] = mod
    spec.loader.exec_module(mod)
    return mod

st.set_page_config(page_title="Race Story", page_icon="📖", layout="wide")
st.title("📖 Complete Race Story")
st.markdown("A full lap-by-lap breakdown of one driver's race — pit stops, overtakes, incidents, sector analysis, and undercut windows.")

st.sidebar.header("Settings")
year   = st.sidebar.number_input("Year", 2018, 2026, 2024)
gp     = st.sidebar.text_input("Grand Prix", "Abu Dhabi")
driver = st.sidebar.text_input("Driver", "VER").upper()

COMPOUND_COLORS = {
    "SOFT": "#DA291C", "MEDIUM": "#FFD700", "HARD": "#FFFFFF",
    "INTERMEDIATE": "#43B02A", "WET": "#0067AD", "UNKNOWN": "#888888",
}

def fmt_time(seconds):
    if pd.isna(seconds): return "N/A"
    m = int(seconds // 60)
    s = seconds % 60
    return f"{m}:{s:06.3f}"

if st.sidebar.button("Generate Race Story", type="primary"):
    apply_f1_style()

    with st.spinner(f"Loading {year} {gp} race data for {driver}..."):
        try:
            session = load_session(year, gp, "R", telemetry=False, weather=False)
        except Exception as e:
            st.error(f"Failed to load session: {e}")
            st.stop()

        laps = session.laps.pick_drivers(driver).copy()
        if laps.empty:
            available = sorted(session.laps["Driver"].unique())
            st.error(f"Driver '{driver}' not found. Available: {', '.join(available)}")
            st.stop()

        results = session.results
        driver_result = results[results["Abbreviation"] == driver]
        if driver_result.empty:
            st.error(f"No results found for {driver}.")
            st.stop()
        result_row = driver_result.iloc[0]

    # ── Import and run analysis from script 07 ────────────────────────
    with st.spinner("Analyzing race events..."):
        mod = _load_race_story_module()
        pit_stops        = mod._detect_pit_stops(laps)
        overtakes, lost  = mod._detect_position_changes(laps)
        incidents        = mod._detect_incidents(laps)
        undercut_windows = mod._detect_undercut_windows(laps)

        pb_laps     = laps[laps["IsPersonalBest"] == True]["LapNumber"].dropna().astype(int).tolist()
        clean_times = laps["LapTime"].dt.total_seconds().dropna()
        fastest_lap = float(clean_times.min()) if not clean_times.empty else None
        fastest_lap_num = int(laps.loc[clean_times.idxmin(), "LapNumber"]) if fastest_lap else None

        story = mod.RaceStory(
            driver=driver,
            event_name=session.event["EventName"],
            year=year,
            team=str(result_row.get("TeamName", "Unknown")),
            grid_position=int(result_row.get("GridPosition", 0)),
            finish_position=int(result_row.get("Position", 0)),
            finish_status=str(result_row.get("Status", "Unknown")),
            points=float(result_row.get("Points", 0)),
            total_laps=int(laps["LapNumber"].max()),
            pit_stops=pit_stops,
            overtakes_made=overtakes,
            places_lost=lost,
            incidents=incidents,
            personal_best_laps=pb_laps,
            fastest_lap=fastest_lap,
            fastest_lap_number=fastest_lap_num,
            undercut_windows=undercut_windows,
        )

    # ── TOP METRICS ───────────────────────────────────────────────────
    st.subheader(f"🏎️ {driver} ({story.team}) — {story.event_name} {year}")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Grid", f"P{story.grid_position}")
    c2.metric("Finish", f"P{story.finish_position}")
    net = story.grid_position - story.finish_position
    c3.metric("Net Positions", f"{'▲' if net>0 else '▼' if net<0 else '='}{abs(net)}", delta=net if net != 0 else None)
    c4.metric("Points Scored", f"{story.points:.0f}")
    c5.metric("Status", story.finish_status)

    # ── CHART (7-panel) ───────────────────────────────────────────────
    with st.spinner("Building race story chart..."):
        laps_sorted   = laps.sort_values("LapNumber")
        lap_nums      = laps_sorted["LapNumber"].values
        lap_times_s   = laps_sorted["LapTime"].dt.total_seconds().values
        positions     = laps_sorted["Position"].values
        compounds     = laps_sorted["Compound"].fillna("UNKNOWN").str.upper().values

        fig = plt.figure(figsize=(16, 22))
        fig.patch.set_facecolor("#0f0f0f")
        fig.suptitle(
            f"{driver} ({story.team})  —  {story.event_name} {year}\n"
            f"P{story.grid_position} → P{story.finish_position}  |  {story.finish_status}  |  {story.points:.0f} pts",
            color="white", fontsize=13, y=0.99,
        )
        gs = gridspec.GridSpec(5, 2, figure=fig, hspace=0.55, wspace=0.3)

        def _ax(ax, title):
            ax.set_facecolor("#0f0f0f")
            ax.set_title(title, color="white", fontsize=9)
            ax.tick_params(colors="white")
            ax.xaxis.label.set_color("white")
            ax.yaxis.label.set_color("white")
            for sp in ax.spines.values(): sp.set_edgecolor("#333")
            ax.grid(True, alpha=0.25)

        # 1. Lap times
        ax1 = fig.add_subplot(gs[0, :])
        for i in range(len(lap_nums)-1):
            color = COMPOUND_COLORS.get(compounds[i], "#888")
            if not (pd.isna(lap_times_s[i]) or pd.isna(lap_times_s[i+1])):
                ax1.plot([lap_nums[i], lap_nums[i+1]], [lap_times_s[i], lap_times_s[i+1]],
                         color=color, linewidth=2.5)
        for pit in story.pit_stops:
            ax1.axvline(pit.lap, color="white", linewidth=1, linestyle="--", alpha=0.6)
        for inc in story.incidents:
            if inc.status_code[0] in ("4","6","7"):
                ax1.axvspan(inc.lap, inc.lap+1, alpha=0.15,
                            color="#FFD700" if "VSC" in inc.description else "#FF8C00")
        pb = laps_sorted[laps_sorted["IsPersonalBest"]==True]
        if not pb.empty:
            ax1.scatter(pb["LapNumber"], pb["LapTime"].dt.total_seconds(),
                        marker="*", color="#FFD700", s=100, zorder=5, label="Personal Best")
        seen, patches = [], []
        for c in compounds:
            if c not in seen:
                seen.append(c)
                patches.append(mpatches.Patch(color=COMPOUND_COLORS.get(c,"#888"), label=c.capitalize()))
        ax1.legend(handles=patches, loc="upper left", fontsize=8, facecolor="#1a1a1a", labelcolor="white")
        ax1.set_xlabel("Lap"); ax1.set_ylabel("Lap Time (s)")
        _ax(ax1, "Lap Times by Compound  (— pit  shaded = SC/VSC)")

        # 2. Position
        ax2 = fig.add_subplot(gs[1, :])
        valid = ~pd.isna(positions)
        ax2.plot(lap_nums[valid], positions[valid], color="#3671C6", linewidth=2.5)
        ax2.invert_yaxis()
        for ov in story.overtakes_made:
            ax2.annotate(f"▲{ov.places}", xy=(ov.lap, ov.to_pos),
                         xytext=(ov.lap+0.5, ov.to_pos-0.3), color="#27F4D2", fontsize=7, fontweight="bold")
        for lo in story.places_lost:
            ax2.annotate(f"▼{lo.places}", xy=(lo.lap, lo.to_pos),
                         xytext=(lo.lap+0.5, lo.to_pos+0.3), color="#E8002D", fontsize=7, fontweight="bold")
        for pit in story.pit_stops:
            ax2.axvline(pit.lap, color="white", linewidth=1, linestyle="--", alpha=0.4)
        ax2.set_xlabel("Lap"); ax2.set_ylabel("Position")
        ax2.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
        _ax(ax2, "Race Position Over Time")

        # 3. Tyre life
        ax3 = fig.add_subplot(gs[2, 0])
        for stint_id, sl in laps_sorted.groupby("Stint"):
            c = str(sl["Compound"].iloc[0]).upper()
            ax3.plot(sl["LapNumber"], sl["TyreLife"], color=COMPOUND_COLORS.get(c,"#888"),
                     linewidth=2, label=f"Stint {int(stint_id)} ({c})")
        ax3.set_xlabel("Lap"); ax3.set_ylabel("Tyre Age (laps)")
        ax3.legend(fontsize=8, facecolor="#1a1a1a", labelcolor="white")
        _ax(ax3, "Tyre Life per Stint")

        # 4. Sector times
        ax4 = fig.add_subplot(gs[2, 1])
        s1 = laps_sorted["Sector1Time"].dt.total_seconds()
        s2 = laps_sorted["Sector2Time"].dt.total_seconds()
        s3 = laps_sorted["Sector3Time"].dt.total_seconds()
        if s1.notna().any(): ax4.plot(lap_nums, s1, label="S1", color="#E8002D", linewidth=1.5)
        if s2.notna().any(): ax4.plot(lap_nums, s2, label="S2", color="#FFD700", linewidth=1.5)
        if s3.notna().any(): ax4.plot(lap_nums, s3, label="S3", color="#27F4D2", linewidth=1.5)
        ax4.set_xlabel("Lap"); ax4.set_ylabel("Sector Time (s)")
        ax4.legend(fontsize=8, facecolor="#1a1a1a", labelcolor="white")
        _ax(ax4, "Sector Times")

        # 5. Top speed
        ax5 = fig.add_subplot(gs[3, 0])
        if "SpeedST" in laps_sorted.columns and laps_sorted["SpeedST"].notna().any():
            ax5.plot(lap_nums, laps_sorted["SpeedST"], color="#FF8000", linewidth=1.8)
            ax5.axhline(laps_sorted["SpeedST"].max(), color="white", linewidth=0.8,
                        linestyle="--", alpha=0.5)
        ax5.set_xlabel("Lap"); ax5.set_ylabel("Speed (km/h)")
        _ax(ax5, "Top Speed per Lap")

        # 6. Pace delta
        ax6 = fig.add_subplot(gs[3, 1])
        ct = laps_sorted["LapTime"].dt.total_seconds().dropna()
        if not ct.empty:
            rolling = ct.rolling(5, min_periods=2, center=True).mean()
            delta   = ct - rolling
            ax6.plot(laps_sorted.loc[ct.index, "LapNumber"], delta,
                     color="#3671C6", linewidth=1.5)
            ax6.axhline(0, color="white", linewidth=0.8, linestyle="--", alpha=0.5)
            ax6.fill_between(laps_sorted.loc[ct.index, "LapNumber"], delta, 0,
                             where=delta < -0.5, alpha=0.3, color="#27F4D2")
        ax6.set_xlabel("Lap"); ax6.set_ylabel("Delta (s)")
        _ax(ax6, "Pace Delta vs Rolling Avg")

        # 7. Timeline
        ax7 = fig.add_subplot(gs[4, :])
        ax7.set_facecolor("#0f0f0f")
        ax7.set_xlim(0, story.total_laps+1); ax7.set_ylim(0, 1)
        ax7.set_yticks([]); ax7.set_xlabel("Lap Number", color="white")
        ax7.tick_params(colors="white")
        for sp in ax7.spines.values(): sp.set_edgecolor("#333")
        for stint_id, sl in laps_sorted.groupby("Stint"):
            c = str(sl["Compound"].iloc[0]).upper()
            lmin, lmax = sl["LapNumber"].min(), sl["LapNumber"].max()
            ax7.barh(0.5, lmax-lmin, left=lmin, height=0.6,
                     color=COMPOUND_COLORS.get(c,"#888"), alpha=0.25, edgecolor="none")
            ax7.text((lmin+lmax)/2, 0.5, c[:1], ha="center", va="center",
                     fontsize=9, color="white", fontweight="bold")
        for pit in story.pit_stops:
            ax7.axvline(pit.lap, color="white", linewidth=2, alpha=0.9)
            ax7.text(pit.lap, 0.92, "PIT", ha="center", fontsize=7, color="white")
        for ov in story.overtakes_made:
            ax7.text(ov.lap, 0.75, f"▲{ov.places}", ha="center",
                     fontsize=8, color="#27F4D2", fontweight="bold")
        for lo in story.places_lost:
            ax7.text(lo.lap, 0.25, f"▼{lo.places}", ha="center",
                     fontsize=8, color="#E8002D", fontweight="bold")
        for inc in story.incidents:
            col = "#FFD700" if "VSC" in inc.description else "#FF8C00"
            ax7.text(inc.lap, 0.1, inc.description[:3].upper(), ha="center", fontsize=6, color=col)
        for w in story.undercut_windows:
            ax7.axvspan(w-0.4, w+0.4, alpha=0.4, color="#FFD700", ymin=0.55, ymax=0.65)
        ax7.set_title("Race Event Timeline", color="white", fontsize=9)
        ax7.grid(True, axis="x", alpha=0.2)

        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    # ── RICH TEXT SUMMARY (mirrors terminal output) ───────────────────
    st.markdown("---")
    st.subheader("📋 Race Story Summary")

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("#### 🏎️ Race Result")
        net = story.grid_position - story.finish_position
        direction = "▲ gained" if net > 0 else "▼ lost" if net < 0 else "no change"
        st.markdown(f"""
| | |
|---|---|
| **Grid position** | P{story.grid_position} |
| **Finish position** | P{story.finish_position} |
| **Net positions** | {abs(net)} {direction} |
| **Status** | {story.finish_status} |
| **Points** | {story.points:.0f} |
""")

        st.markdown("#### 🛞 Pit Stops")
        if story.pit_stops:
            for pit in story.pit_stops:
                st.markdown(f"- **Lap {pit.lap}** — {pit.compound_before} → {pit.compound_after} (tyre was {pit.tyre_life_before:.0f} laps old)")
        else:
            st.markdown("- No pit stops recorded")

        st.markdown("#### ⚡ Overtakes Made")
        if story.overtakes_made:
            for ov in story.overtakes_made:
                st.markdown(f"- **Lap {ov.lap}** — P{ov.from_pos} → P{ov.to_pos} (+{ov.places} place{'s' if ov.places > 1 else ''})")
        else:
            st.markdown("- No on-track overtakes detected")

        st.markdown("#### 📉 Positions Lost")
        if story.places_lost:
            for lo in story.places_lost:
                st.markdown(f"- **Lap {lo.lap}** — P{lo.from_pos} → P{lo.to_pos} (-{lo.places} place{'s' if lo.places > 1 else ''})")
        else:
            st.markdown("- No positions lost on track")

    with col_b:
        st.markdown("#### ⚠️ Race Incidents")
        if story.incidents:
            for inc in story.incidents:
                st.markdown(f"- **Lap {inc.lap}** — {inc.description}")
        else:
            st.markdown("- No safety cars or flags")

        st.markdown("#### ⏱️ Lap Time Analysis")
        if not clean_times.empty:
            best_t  = clean_times.min()
            best_l  = int(laps.loc[clean_times.idxmin(), "LapNumber"])
            worst_t = clean_times.max()
            worst_l = int(laps.loc[clean_times.idxmax(), "LapNumber"])
            st.markdown(f"- **Fastest lap:** {fmt_time(best_t)} (Lap {best_l})")
            st.markdown(f"- **Slowest lap:** {fmt_time(worst_t)} (Lap {worst_l})")
            st.markdown(f"- **Average pace:** {fmt_time(clean_times.mean())}")
            st.markdown(f"- **Personal bests set:** {len(story.personal_best_laps)} laps")

        st.markdown("#### 🔵 Undercut Windows")
        if story.undercut_windows:
            st.markdown(f"- **{len(story.undercut_windows)} window(s) detected** on laps: {story.undercut_windows}")
            st.markdown("- These are laps where pace was >0.8s faster than recent average")
        else:
            st.markdown("- No undercut windows detected")

        st.markdown("#### 📊 Stint Breakdown")
        for stint_id, sl in laps.sort_values("LapNumber").groupby("Stint"):
            cpd   = str(sl["Compound"].iloc[0]).upper()
            times = sl["LapTime"].dt.total_seconds().dropna()
            avg   = fmt_time(times.mean()) if not times.empty else "N/A"
            best  = fmt_time(times.min())  if not times.empty else "N/A"
            st.markdown(f"- **Stint {int(stint_id)}** — {cpd} — {len(sl)} laps — Avg: {avg} — Best: {best}")

        st.markdown("#### 🚀 Top Speed")
        if "SpeedST" in laps.columns and laps["SpeedST"].notna().any():
            max_spd = laps["SpeedST"].max()
            max_lap = int(laps.loc[laps["SpeedST"].idxmax(), "LapNumber"])
            st.markdown(f"- **{max_spd:.0f} km/h** on Lap {max_lap}")