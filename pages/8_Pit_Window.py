import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
st.set_page_config(page_title="Pit Window - F1 Analytics", page_icon="F1", layout="wide", initial_sidebar_state="collapsed")
from f1_analysis.visualization.ui_theme import inject_f1_css, top_nav, page_header, control_panel, section_label, metrics_row, insight_box
inject_f1_css()
top_nav("Pit Window")
page_header("P", "Strategy Tool", "Pit Stop Window",
    "Optimal pit lap range, undercut threat detection, and overcut viability for any driver.")

clicked, vals = control_panel([
    {"type":"number","label":"Year","key":"pw_year","default":2024,"min":2018,"max":2026},
    {"type":"text",  "label":"Grand Prix","key":"pw_gp","default":"Bahrain"},
    {"type":"text",  "label":"Driver","key":"pw_driver","default":"VER"},
    {"type":"number","label":"From Lap","key":"pw_lap","default":25,"min":1,"max":70},
    {"type":"select","label":"Next Compound","key":"pw_compound","default":"MEDIUM","options":["MEDIUM","HARD","SOFT"]},
], button_label="Calculate", cols_per_row=6)

if clicked:
    from f1_analysis.core.session_loader import load_session
    from f1_analysis.core.pit_window import calculate_pit_window
    from f1_analysis.visualization.style import apply_f1_style, get_driver_color
    driver = vals["pw_driver"].upper()
    with st.spinner("Loading race data..."):
        apply_f1_style()
        try:
            session = load_session(vals["pw_year"], vals["pw_gp"], "R", telemetry=False, weather=False)
        except Exception as e:
            st.error("Failed to load session: " + str(e)); st.stop()
        total_laps = int(session.laps["LapNumber"].max())
    if driver not in session.laps["Driver"].unique():
        st.error("Driver " + driver + " not found."); st.stop()
    result = calculate_pit_window(session, driver, current_lap=int(vals["pw_lap"]), next_compound=vals["pw_compound"])
    metrics_row([
        {"label":"Earliest Pit","value":"Lap " + str(result.earliest_lap)},
        {"label":"Optimal Pit", "value":"Lap " + str(result.optimal_lap),"color":"teal"},
        {"label":"Latest Pit",  "value":"Lap " + str(result.latest_lap)},
        {"label":"Undercut Threat","value":"Lap " + str(result.undercut_threat_lap) if result.undercut_threat_lap else "None","color":"accent" if result.undercut_threat_lap else ""},
        {"label":"Overcut",     "value":"Yes" if result.overcut_possible else "No","color":"green" if result.overcut_possible else ""},
    ])
    st.markdown('<div style="padding:0 2.5rem 4rem;">', unsafe_allow_html=True)
    section_label("Pit Window Chart")
    try: color = get_driver_color(driver, session)
    except: color = "#3671C6"
    fig, ax = plt.subplots(figsize=(14, 3))
    fig.patch.set_facecolor("#0D0D0D"); ax.set_facecolor("#0D0D0D")
    ax.barh(0, total_laps, left=0, height=0.5, color="#1C1C1C", alpha=0.8)
    ax.barh(0, result.latest_lap-result.earliest_lap, left=result.earliest_lap, height=0.5, color=color, alpha=0.9)
    ax.axvline(result.optimal_lap, color="#FFD700", linewidth=2.5, label="Optimal: Lap " + str(result.optimal_lap))
    if result.undercut_threat_lap:
        ax.axvline(result.undercut_threat_lap, color="#E8002D", linewidth=2, linestyle="--", label="Undercut threat: Lap " + str(result.undercut_threat_lap))
    ax.axvline(int(vals["pw_lap"]), color="white", linewidth=1.5, linestyle=":", label="Current: Lap " + str(vals["pw_lap"]))
    ax.set_xlim(0, total_laps+2); ax.set_ylim(-0.5, 0.5); ax.set_yticks([])
    ax.set_xlabel("Lap Number", color="#888", fontsize=9)
    ax.tick_params(colors="#888")
    ax.legend(loc="upper left", fontsize=9, facecolor="#1A1A1A", labelcolor="white")
    ax.grid(True, axis="x", alpha=0.12, color="#FFF")
    for sp in ax.spines.values(): sp.set_edgecolor("#2A2A2A")
    ax.set_title(driver + " - " + session.event["EventName"] + " " + str(vals["pw_year"]), color="white", fontsize=11)
    fig.tight_layout(); st.pyplot(fig, use_container_width=True); plt.close(fig)
    insight_box("P", "Reading the Pit Window Chart",
        "The coloured bar shows the strategic pit window. "
        "The gold line is the optimal pit lap. "
        "The red dashed line (if shown) is when a rival could undercut you.")
    section_label("Strategy Reasoning")
    for r in result.reasoning:
        st.markdown('- ' + r)
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.markdown('<div style="padding:5rem 2.5rem;text-align:center;font-family:Titillium Web,sans-serif;font-size:0.8rem;text-transform:uppercase;letter-spacing:0.15em;color:#2A2A2A;">Configure parameters above and press Calculate</div>', unsafe_allow_html=True)