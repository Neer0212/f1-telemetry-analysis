import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

st.set_page_config(page_title="Track Speed Map · F1 Analytics", page_icon="🗺️", layout="wide")

from f1_analysis.visualization.ui_theme import inject_f1_css, page_header, section_label, metrics_row
from f1_analysis.core.session_loader import load_session
from f1_analysis.visualization.style import apply_f1_style

inject_f1_css()
page_header("🗺️", "Circuit Visualisation", "Track Speed Map",
            "Circuit outline painted by speed — see exactly where a driver is fastest and slowest through every corner.")

with st.sidebar:
    st.markdown("### ⚙️ Settings")
    year   = st.number_input("Year", 2018, 2026, 2024)
    gp     = st.text_input("Grand Prix", "Monza")
    driver = st.text_input("Driver", "VER").upper()
    run    = st.button("Generate Map", type="primary")

if run:
    import matplotlib.pyplot as plt
    import matplotlib as mpl
    import numpy as np

    with st.spinner("Loading telemetry…"):
        apply_f1_style()
        session = load_session(year, gp, "Q")
        lap = session.laps.pick_drivers(driver).pick_fastest()
        tel = lap.get_telemetry().add_distance()

    metrics_row([
        {"label": "Driver",      "value": driver,                            "color": "accent"},
        {"label": "Circuit",     "value": session.event["EventName"]},
        {"label": "Session",     "value": "Qualifying"},
        {"label": "Lap Time",    "value": str(lap["LapTime"]).split()[-1] if lap["LapTime"] else "N/A", "color": "teal"},
    ])

    st.markdown('<div style="padding:0 2.5rem;">', unsafe_allow_html=True)
    section_label("Speed Map")

    x = tel["X"].values
    y = tel["Y"].values
    speed = tel["Speed"].values

    fig, ax = plt.subplots(figsize=(14, 8))
    fig.patch.set_facecolor("#0D0D0D")
    ax.set_facecolor("#0D0D0D")

    points  = np.array([x, y]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    norm    = mpl.colors.Normalize(vmin=speed.min(), vmax=speed.max())
    cmap    = mpl.cm.RdYlGn
    lc      = mpl.collections.LineCollection(segments, cmap=cmap, norm=norm, linewidth=3.5)
    lc.set_array(speed)
    ax.add_collection(lc)
    ax.autoscale()
    ax.set_aspect("equal")
    ax.axis("off")

    cbar = fig.colorbar(lc, ax=ax, orientation="horizontal", fraction=0.03, pad=0.02)
    cbar.set_label("Speed (km/h)", color="white", fontsize=9)
    cbar.ax.xaxis.set_tick_params(color="white")
    plt.setp(cbar.ax.xaxis.get_ticklabels(), color="white", fontsize=8)
    cbar.outline.set_edgecolor("#2A2A2A")

    ax.set_title(f"{driver} — {session.event['EventName']} {year} · Qualifying",
                 color="white", fontsize=11, fontweight="bold", pad=12)
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.markdown("""
<div style="padding:4rem 2.5rem; text-align:center; color:#333;
            font-family:'Titillium Web',sans-serif; font-size:0.8rem;
            text-transform:uppercase; letter-spacing:0.15em;">
    Enter driver and Grand Prix, then press Generate Map
</div>""", unsafe_allow_html=True)