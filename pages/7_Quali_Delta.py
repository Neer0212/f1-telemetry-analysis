import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.patches import Patch

from f1_analysis.core.session_loader import load_session
from f1_analysis.core.quali_delta import compute_qualifying_delta, get_lap_time_str
from f1_analysis.visualization.style import apply_f1_style

st.set_page_config(page_title="Quali Delta", page_icon="⏱️", layout="wide")
st.title("⏱️ Qualifying Minisector Delta Map")
st.markdown("Paints the circuit green/red to show where each driver gains or loses time, minisector by minisector.")

st.sidebar.header("Settings")
year        = st.sidebar.number_input("Year", 2018, 2026, 2024)
gp          = st.sidebar.text_input("Grand Prix", "Monaco")
col1, col2  = st.sidebar.columns(2)
driver_a    = col1.text_input("Driver A (green)", "LEC").upper()
driver_b    = col2.text_input("Driver B (red)", "VER").upper()
minisectors = st.sidebar.slider("Minisectors", 10, 50, 25)

if st.sidebar.button("Analyze Delta", type="primary"):
    with st.spinner(f"Loading {year} {gp} Qualifying and computing delta..."):
        apply_f1_style()
        try:
            session = load_session(year, gp, "Q", telemetry=True, weather=False)
        except Exception as e:
            st.error(f"Failed to load session: {e}")
            st.stop()

        available = sorted(session.laps["Driver"].unique())
        for drv in [driver_a, driver_b]:
            if drv not in available:
                st.error(f"Driver '{drv}' not found. Available: {', '.join(available)}")
                st.stop()

        try:
            df = compute_qualifying_delta(session, driver_a, driver_b, n_minisectors=minisectors)
        except Exception as e:
            st.error(f"Could not compute delta: {e}")
            st.stop()

    lap_a = get_lap_time_str(session, driver_a)
    lap_b = get_lap_time_str(session, driver_b)

    # ── Metric row ────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"{driver_a} best lap", lap_a)
    c2.metric(f"{driver_b} best lap", lap_b)
    a_faster = int((df["Faster"] == driver_a).sum())
    b_faster = int((df["Faster"] == driver_b).sum())
    c3.metric(f"{driver_a} faster in", f"{a_faster} sectors")
    c4.metric(f"{driver_b} faster in", f"{b_faster} sectors")

    # ── Map panels ────────────────────────────────────────────────────
    x = df["X"].values
    y = df["Y"].values
    faster = df["Faster"].values
    delta  = df["Delta"].values

    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    fig.patch.set_facecolor("#0f0f0f")

    # Left: green/red per minisector
    ax = axes[0]
    ax.set_facecolor("#0f0f0f")
    ax.set_title(f"Faster driver per sector — green={driver_a}  red={driver_b}",
                 color="white", fontsize=11)
    for i in range(len(x) - 1):
        color = "#27AE60" if faster[i] == driver_a else "#E74C3C"
        ax.plot([x[i], x[i+1]], [y[i], y[i+1]], color=color, linewidth=6,
                solid_capstyle="round")
    legend_elements = [
        Patch(facecolor="#27AE60", label=f"{driver_a} faster"),
        Patch(facecolor="#E74C3C", label=f"{driver_b} faster"),
    ]
    ax.legend(handles=legend_elements, loc="upper left", fontsize=10,
              facecolor="#1a1a1a", labelcolor="white")
    ax.set_aspect("equal"); ax.axis("off")

    # Right: magnitude heatmap
    ax2 = axes[1]
    ax2.set_facecolor("#0f0f0f")
    ax2.set_title("Gap magnitude (darker = bigger difference)", color="white", fontsize=11)
    abs_delta = np.abs(delta)
    points   = np.array([x, y]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    norm = plt.Normalize(abs_delta.min(), abs_delta.max())
    lc   = LineCollection(segments, cmap="RdYlGn_r", norm=norm, linewidth=6)
    lc.set_array(abs_delta[:-1])
    ax2.add_collection(lc)
    cbar = fig.colorbar(lc, ax=ax2, fraction=0.04, pad=0.02)
    cbar.set_label("Time Gap (s)", color="white")
    cbar.ax.yaxis.set_tick_params(color="white")
    plt.setp(cbar.ax.yaxis.get_ticklabels(), color="white")
    ax2.set_xlim(x.min()-200, x.max()+200)
    ax2.set_ylim(y.min()-200, y.max()+200)
    ax2.set_aspect("equal"); ax2.axis("off")

    fig.suptitle(
        f"Qualifying Delta — {session.event['EventName']} {year}\n"
        f"{driver_a} ({lap_a})  vs  {driver_b} ({lap_b})",
        color="white", fontsize=13,
    )
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # ── Bar chart ─────────────────────────────────────────────────────
    fig2, ax3 = plt.subplots(figsize=(14, 3))
    fig2.patch.set_facecolor("#0f0f0f")
    ax3.set_facecolor("#0f0f0f")
    colors = ["#27AE60" if f == driver_a else "#E74C3C" for f in df["Faster"]]
    ax3.bar(df["MiniSector"], -df["Delta"], color=colors, width=0.8)
    ax3.axhline(0, color="white", linewidth=0.8, linestyle="--", alpha=0.5)
    ax3.set_xlabel("Minisector", color="white")
    ax3.set_ylabel(f"← {driver_b} faster  |  {driver_a} faster →", color="white")
    ax3.set_title("Delta by Minisector", color="white")
    ax3.tick_params(colors="white")
    for spine in ax3.spines.values():
        spine.set_edgecolor("#333")
    ax3.grid(True, axis="y", alpha=0.3)
    fig2.tight_layout()
    st.pyplot(fig2)
    plt.close(fig2)