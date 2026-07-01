import streamlit as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
import sys, importlib, importlib.util
import numpy as np
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
st.set_page_config(page_title="Race Story - F1 Analytics", page_icon="F1", layout="wide", initial_sidebar_state="collapsed")
from f1_analysis.visualization.ui_theme import inject_f1_css, top_nav, page_header, control_panel, section_label, metrics_row, insight_box, COMPOUND_COLORS, F1_RED, F1_GOLD, F1_TEAL
inject_f1_css()
top_nav("Race Story")

from f1_analysis.core.session_loader import load_session
from f1_analysis.visualization.style import apply_f1_style

def _load_race_story_module():
    spec = importlib.util.spec_from_file_location(
        "race_story", Path(__file__).resolve().parent.parent / "scripts" / "07_race_story.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["race_story"] = mod
    spec.loader.exec_module(mod)
    return mod

page_header("R", "Race Analysis", "Race Story",
    "Lap-by-lap breakdown of a driver's race - pit stops, overtakes, safety cars, sector pace and undercut windows.")

clicked, vals = control_panel([
    {"type":"number","label":"Year","key":"rs_year","default":2024,"min":2018,"max":2026},
    {"type":"text",  "label":"Grand Prix","key":"rs_gp","default":"Abu Dhabi"},
    {"type":"text",  "label":"Driver","key":"rs_driver","default":"VER"},
], button_label="Generate Race Story", cols_per_row=4)

def fmt_time(seconds):
    if pd.isna(seconds): return "N/A"
    m = int(seconds // 60); s = seconds % 60
    return "{}:{:06.3f}".format(m, s)

if clicked:
    apply_f1_style()
    driver = vals["rs_driver"].upper()
    with st.spinner("Loading " + str(vals["rs_year"]) + " " + vals["rs_gp"] + " race data for " + driver + "..."):
        try:
            session = load_session(vals["rs_year"], vals["rs_gp"], "R", telemetry=False, weather=False)
        except Exception as e:
            st.error("Failed to load session: " + str(e)); st.stop()
        laps = session.laps.pick_drivers(driver).copy()
        if laps.empty:
            available = sorted(session.laps["Driver"].unique())
            st.error("Driver " + driver + " not found. Available: " + ", ".join(available)); st.stop()
        results = session.results
        driver_row = results[results["Abbreviation"] == driver]
        if driver_row.empty:
            st.error("No results found for " + driver); st.stop()
        result_row = driver_row.iloc[0]

    with st.spinner("Analysing race events..."):
        mod = _load_race_story_module()
        pit_stops = mod._detect_pit_stops(laps)
        overtakes, lost = mod._detect_position_changes(laps)
        incidents = mod._detect_incidents(laps)
        undercut_windows = mod._detect_undercut_windows(laps)
        pb_laps = laps[laps["IsPersonalBest"] == True]["LapNumber"].dropna().astype(int).tolist()
        clean_times = laps["LapTime"].dt.total_seconds().dropna()
        fastest_lap = float(clean_times.min()) if not clean_times.empty else None
        fastest_lap_num = int(laps.loc[clean_times.idxmin(), "LapNumber"]) if fastest_lap else None
        story = mod.RaceStory(
            driver=driver, event_name=session.event["EventName"], year=vals["rs_year"],
            team=str(result_row.get("TeamName", "Unknown")),
            grid_position=int(result_row.get("GridPosition", 0)),
            finish_position=int(result_row.get("Position", 0)),
            finish_status=str(result_row.get("Status", "Unknown")),
            points=float(result_row.get("Points", 0)),
            total_laps=int(laps["LapNumber"].max()),
            pit_stops=pit_stops, overtakes_made=overtakes, places_lost=lost,
            incidents=incidents, personal_best_laps=pb_laps,
            fastest_lap=fastest_lap, fastest_lap_number=fastest_lap_num,
            undercut_windows=undercut_windows,
        )

    net = story.grid_position - story.finish_position
    metrics_row([
        {"label":"Driver","value":driver,"color":"accent"},
        {"label":"Team","value":story.team},
        {"label":"Grid","value":"P" + str(story.grid_position)},
        {"label":"Finish","value":"P" + str(story.finish_position),"color":"teal"},
        {"label":"Net","value":("+" if net>0 else "") + str(net)},
        {"label":"Points","value":"{:.0f}".format(story.points),"color":"gold"},
        {"label":"Status","value":story.finish_status},
        {"label":"Pit Stops","value":str(len(story.pit_stops))},
    ])
    st.markdown('<div style="padding:0 2.5rem 4rem;">', unsafe_allow_html=True)

    section_label("Race Charts")
    laps_s = laps.sort_values("LapNumber")
    lap_nums = laps_s["LapNumber"].values
    lap_t_s = laps_s["LapTime"].dt.total_seconds().values
    positions = laps_s["Position"].values
    compounds = laps_s["Compound"].fillna("UNKNOWN").str.upper().values

    fig = plt.figure(figsize=(16, 22))
    fig.patch.set_facecolor("#0D0D0D")
    fig.suptitle(driver + " (" + story.team + ")  -  " + story.event_name + " " + str(vals["rs_year"]) +
                 "  -  P" + str(story.grid_position) + " to P" + str(story.finish_position) +
                 "  |  " + story.finish_status + "  |  {:.0f} pts".format(story.points),
                 color="white", fontsize=11, y=0.99)
    gs = gridspec.GridSpec(5, 2, figure=fig, hspace=0.6, wspace=0.32)

    def _ax(ax, title):
        ax.set_facecolor("#0D0D0D")
        ax.set_title(title, color="white", fontsize=8.5)
        ax.tick_params(colors="#888888", labelsize=7.5)
        ax.xaxis.label.set_color("#888888"); ax.xaxis.label.set_fontsize(8)
        ax.yaxis.label.set_color("#888888"); ax.yaxis.label.set_fontsize(8)
        for sp in ax.spines.values(): sp.set_edgecolor("#2A2A2A")
        ax.grid(True, alpha=0.1, color="#FFFFFF", linewidth=0.5)

    ax1 = fig.add_subplot(gs[0, :])
    for i in range(len(lap_nums)-1):
        c = COMPOUND_COLORS.get(compounds[i], "#888")
        if not (pd.isna(lap_t_s[i]) or pd.isna(lap_t_s[i+1])):
            ax1.plot([lap_nums[i], lap_nums[i+1]], [lap_t_s[i], lap_t_s[i+1]], color=c, linewidth=2.5)
    for pit in story.pit_stops:
        ax1.axvline(pit.lap, color="#FFFFFF", linewidth=0.8, linestyle="--", alpha=0.5)
    pb = laps_s[laps_s["IsPersonalBest"]==True]
    if not pb.empty:
        ax1.scatter(pb["LapNumber"], pb["LapTime"].dt.total_seconds(), marker="*", color=F1_GOLD, s=90, zorder=5, label="Personal Best")
    seen, patches = [], []
    for c in compounds:
        if c not in seen:
            seen.append(c)
            patches.append(mpatches.Patch(color=COMPOUND_COLORS.get(c,"#888"), label=c.capitalize()))
    ax1.legend(handles=patches, loc="upper left", fontsize=7.5, facecolor="#1A1A1A", labelcolor="white")
    ax1.set_xlabel("Lap"); ax1.set_ylabel("Lap Time (s)")
    _ax(ax1, "Lap Times by Compound (dashed = pit stop)")

    ax2 = fig.add_subplot(gs[1, :])
    valid = ~pd.isna(positions)
    ax2.plot(lap_nums[valid], positions[valid], color=F1_TEAL, linewidth=2.5)
    ax2.invert_yaxis()
    for ov in story.overtakes_made:
        ax2.annotate("+{}".format(ov.places), xy=(ov.lap, ov.to_pos), xytext=(ov.lap+0.5, ov.to_pos-0.3), color=F1_TEAL, fontsize=7, fontweight="bold")
    for lo in story.places_lost:
        ax2.annotate("-{}".format(lo.places), xy=(lo.lap, lo.to_pos), xytext=(lo.lap+0.5, lo.to_pos+0.3), color=F1_RED, fontsize=7, fontweight="bold")
    ax2.set_xlabel("Lap"); ax2.set_ylabel("Position")
    ax2.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
    _ax(ax2, "Race Position Over Time")

    ax3 = fig.add_subplot(gs[2, 0])
    for stint_id, sl in laps_s.groupby("Stint"):
        c = str(sl["Compound"].iloc[0]).upper()
        ax3.plot(sl["LapNumber"], sl["TyreLife"], color=COMPOUND_COLORS.get(c,"#888"), linewidth=2, label="Stint " + str(int(stint_id)) + " (" + c + ")")
    ax3.set_xlabel("Lap"); ax3.set_ylabel("Tyre Age (laps)")
    ax3.legend(fontsize=7.5, facecolor="#1A1A1A", labelcolor="white")
    _ax(ax3, "Tyre Life per Stint")

    ax4 = fig.add_subplot(gs[2, 1])
    s1 = laps_s["Sector1Time"].dt.total_seconds(); s2 = laps_s["Sector2Time"].dt.total_seconds(); s3 = laps_s["Sector3Time"].dt.total_seconds()
    if s1.notna().any(): ax4.plot(lap_nums, s1, label="S1", color="#E8002D", linewidth=1.5)
    if s2.notna().any(): ax4.plot(lap_nums, s2, label="S2", color="#FFD700", linewidth=1.5)
    if s3.notna().any(): ax4.plot(lap_nums, s3, label="S3", color="#27F4D2", linewidth=1.5)
    ax4.set_xlabel("Lap"); ax4.set_ylabel("Sector Time (s)")
    ax4.legend(fontsize=7.5, facecolor="#1A1A1A", labelcolor="white")
    _ax(ax4, "Sector Times")

    ax5 = fig.add_subplot(gs[3, 0])
    if "SpeedST" in laps_s.columns and laps_s["SpeedST"].notna().any():
        ax5.plot(lap_nums, laps_s["SpeedST"], color="#FF8000", linewidth=1.8)
    ax5.set_xlabel("Lap"); ax5.set_ylabel("Speed (km/h)")
    _ax(ax5, "Top Speed per Lap")

    ax6 = fig.add_subplot(gs[3, 1])
    ct = laps_s["LapTime"].dt.total_seconds().dropna()
    if not ct.empty:
        rolling = ct.rolling(5, min_periods=2, center=True).mean()
        delta = ct - rolling
        ax6.plot(laps_s.loc[ct.index, "LapNumber"], delta, color=F1_TEAL, linewidth=1.5)
        ax6.axhline(0, color="white", linewidth=0.7, linestyle="--", alpha=0.4)
    ax6.set_xlabel("Lap"); ax6.set_ylabel("Delta (s)")
    _ax(ax6, "Pace Delta vs 5-Lap Rolling Avg")

    ax7 = fig.add_subplot(gs[4, :])
    ax7.set_facecolor("#0D0D0D")
    ax7.set_xlim(0, story.total_laps+1); ax7.set_ylim(0, 1)
    ax7.set_yticks([]); ax7.set_xlabel("Lap Number", color="#888888", fontsize=8)
    ax7.tick_params(colors="#888888")
    for sp in ax7.spines.values(): sp.set_edgecolor("#2A2A2A")
    for stint_id, sl in laps_s.groupby("Stint"):
        c = str(sl["Compound"].iloc[0]).upper()
        lmin, lmax = sl["LapNumber"].min(), sl["LapNumber"].max()
        ax7.barh(0.5, lmax-lmin, left=lmin, height=0.55, color=COMPOUND_COLORS.get(c,"#888"), alpha=0.3)
        ax7.text((lmin+lmax)/2, 0.5, c[:1], ha="center", va="center", fontsize=8.5, color="white", fontweight="bold")
    for pit in story.pit_stops:
        ax7.axvline(pit.lap, color="white", linewidth=1.8, alpha=0.85)
        ax7.text(pit.lap, 0.93, "PIT", ha="center", fontsize=6.5, color="white", fontweight="bold")
    ax7.set_title("Race Event Timeline", color="white", fontsize=8.5)
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    insight_box("C", "How to Read These Charts",
        "Lap Times: dashed white lines are pit stops, a rising slope within a stint shows tyre degradation. "
        "Position: y-axis is inverted so P1 is at the top, an upward spike is usually a pit stop. "
        "Tyre Life: each stint resets to zero after a pit stop, steeper lines mean more laps run on that set. "
        "Sector Times: a rising sector while others stay flat often points to a specific corner punishing tyre wear. "
        "Pace Delta: bars below zero are laps faster than the recent average, often fresh tyres or a clear track. "
        "Timeline: the full race in one row, PIT markers show stops, yellow zones are undercut windows.")

    section_label("Race Summary")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Result**")
        st.markdown("Grid: P" + str(story.grid_position) + " | Finish: P" + str(story.finish_position) + " | Status: " + story.finish_status + " | Points: {:.0f}".format(story.points))
        st.markdown("**Pit Stops**")
        if story.pit_stops:
            for pit in story.pit_stops:
                st.markdown("- Lap " + str(pit.lap) + " - " + pit.compound_before + " to fresh (tyre " + "{:.0f}".format(pit.tyre_life_before) + " laps old)")
        else:
            st.markdown("- No pit stops recorded")
    with col_b:
        st.markdown("**Incidents**")
        if story.incidents:
            for inc in story.incidents:
                st.markdown("- Lap " + str(inc.lap) + " - " + inc.description)
        else:
            st.markdown("- No safety cars or flags")
        st.markdown("**Lap Time Analysis**")
        if not clean_times.empty:
            st.markdown("- Fastest: " + fmt_time(clean_times.min()) + " | Average: " + fmt_time(clean_times.mean()))
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.markdown('<div style="padding:5rem 2.5rem;text-align:center;font-family:Titillium Web,sans-serif;font-size:0.8rem;text-transform:uppercase;letter-spacing:0.15em;color:#2A2A2A;">Enter year, Grand Prix and driver above, then press Generate Race Story</div>', unsafe_allow_html=True)