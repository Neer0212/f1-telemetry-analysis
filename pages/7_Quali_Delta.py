import streamlit as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.patches import Patch

from f1_analysis.core.session_loader import load_session
from f1_analysis.core.quali_delta import compute_qualifying_delta, get_lap_time_str
from f1_analysis.visualization.style import apply_f1_style

st.set_page_config(page_title="Quali Delta", page_icon="⏱️", layout="wide")
st.markdown("""<style>
.page-header{background:linear-gradient(90deg,#1a0000,#0a0a1e);border-left:4px solid #e10600;
  padding:1.2rem 1.5rem;border-radius:0 8px 8px 0;margin-bottom:1.5rem;}
.page-header h1{color:#fff;margin:0;font-size:1.8rem;}
.page-header p{color:#aaa;margin:.3rem 0 0;font-size:.95rem;}
.explain-box{background:#111827;border:1px solid #1f2937;border-left:3px solid #e10600;
  border-radius:6px;padding:.9rem 1.2rem;margin:.8rem 0 1.2rem;color:#d1d5db;font-size:.9rem;line-height:1.6;}
.insight-box{background:#0d1117;border:1px solid #21262d;border-radius:8px;padding:1rem 1.3rem;margin-top:1rem;}
.insight-box h4{color:#e10600;margin:0 0 .6rem;font-size:1rem;}
</style>
<div class="page-header">
    <h1>⏱️ Qualifying Delta Map</h1>
    <p>See exactly where on circuit one driver is faster than another — painted green and red, minisector by minisector.</p>
</div>""", unsafe_allow_html=True)

st.sidebar.header("Settings")
year        = st.sidebar.number_input("Year", 2018, 2026, 2024)
gp          = st.sidebar.text_input("Grand Prix", "Monaco")
col1, col2  = st.sidebar.columns(2)
driver_a    = col1.text_input("Driver A (green)", "LEC").upper()
driver_b    = col2.text_input("Driver B (red)",   "VER").upper()
minisectors = st.sidebar.slider("Detail level (minisectors)", 10, 50, 25)
st.sidebar.caption("More minisectors = finer detail but can get noisy. 25 is the sweet spot.")

if st.sidebar.button("Analyze Delta", type="primary"):
    with st.spinner(f"Loading qualifying telemetry for {gp} {year}..."):
        apply_f1_style()
        try:
            session = load_session(year, gp, "Q", telemetry=True, weather=False)
        except Exception as e:
            st.error(f"Could not load session: {e}"); st.stop()
        available = sorted(session.laps["Driver"].unique())
        for drv in [driver_a, driver_b]:
            if drv not in available:
                st.error(f"'{drv}' not in session. Available: {', '.join(available)}"); st.stop()
        try:
            df = compute_qualifying_delta(session, driver_a, driver_b, n_minisectors=minisectors)
        except Exception as e:
            st.error(f"Could not compute delta: {e}"); st.stop()

    lap_a = get_lap_time_str(session, driver_a)
    lap_b = get_lap_time_str(session, driver_b)
    a_faster = int((df["Faster"] == driver_a).sum())
    b_faster = int((df["Faster"] == driver_b).sum())
    overall_gap = abs(df["Delta"].iloc[-1])
    winner = driver_a if df["Delta"].iloc[-1] < 0 else driver_b

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric(f"{driver_a} lap", lap_a)
    c2.metric(f"{driver_b} lap", lap_b)
    c3.metric(f"{driver_a} faster sectors", a_faster)
    c4.metric(f"{driver_b} faster sectors", b_faster)
    c5.metric("Overall faster", winner)

    # ════════════════════════════════════════════════════════════
    # CHART 1: TRACK MAP
    # ════════════════════════════════════════════════════════════
    st.markdown("---")
    st.subheader("🗺️ Track Map — Faster Driver per Sector")
    st.markdown(f"""<div class="explain-box">
    <strong>What this chart shows (left):</strong> The circuit is split into {minisectors} segments.
    Each segment is coloured <strong style="color:#27ae60">green</strong> if {driver_a} was faster
    through that part, or <strong style="color:#e74c3c">red</strong> if {driver_b} was faster.
    This is exactly the same analysis F1 TV uses during qualifying broadcasts.
    <br><br>
    <strong>Right map — magnitude:</strong> Shows HOW MUCH faster one driver is in each sector.
    Darker red/orange = bigger gap. A big red cluster in one corner means one driver has found
    a very different — and faster — approach through that part of the circuit.
    </div>""", unsafe_allow_html=True)

    x, y   = df["X"].values, df["Y"].values
    faster = df["Faster"].values
    delta  = df["Delta"].values

    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    fig.patch.set_facecolor("#0f0f0f")
    ax, ax2 = axes

    ax.set_facecolor("#0f0f0f")
    ax.set_title(f"Faster driver — green={driver_a}  red={driver_b}", color="white", fontsize=11)
    for i in range(len(x)-1):
        c = "#27AE60" if faster[i] == driver_a else "#E74C3C"
        ax.plot([x[i],x[i+1]], [y[i],y[i+1]], color=c, linewidth=6, solid_capstyle="round")
    ax.legend(handles=[Patch(facecolor="#27AE60",label=f"{driver_a} faster"),
                        Patch(facecolor="#E74C3C",label=f"{driver_b} faster")],
              loc="upper left", fontsize=10, facecolor="#1a1a1a", labelcolor="white")
    ax.set_aspect("equal"); ax.axis("off")

    ax2.set_facecolor("#0f0f0f")
    ax2.set_title("Gap magnitude (darker = bigger time difference)", color="white", fontsize=11)
    abs_delta = np.abs(delta)
    points    = np.array([x,y]).T.reshape(-1,1,2)
    segments  = np.concatenate([points[:-1],points[1:]],axis=1)
    norm = plt.Normalize(abs_delta.min(), abs_delta.max())
    lc   = LineCollection(segments, cmap="RdYlGn_r", norm=norm, linewidth=6)
    lc.set_array(abs_delta[:-1])
    ax2.add_collection(lc)
    cbar = fig.colorbar(lc, ax=ax2, fraction=0.04, pad=0.02)
    cbar.set_label("Time Gap (s)", color="white")
    cbar.ax.yaxis.set_tick_params(color="white")
    plt.setp(cbar.ax.yaxis.get_ticklabels(), color="white")
    ax2.set_xlim(x.min()-200, x.max()+200); ax2.set_ylim(y.min()-200, y.max()+200)
    ax2.set_aspect("equal"); ax2.axis("off")
    fig.suptitle(f"Qualifying Delta — {session.event['EventName']} {year}\n{driver_a} ({lap_a}) vs {driver_b} ({lap_b})",
                 color="white", fontsize=13)
    fig.tight_layout()
    st.pyplot(fig); plt.close(fig)

    # ════════════════════════════════════════════════════════════
    # CHART 2: BAR CHART
    # ════════════════════════════════════════════════════════════
    st.markdown("---")
    st.subheader("📊 Delta by Minisector")
    st.markdown(f"""<div class="explain-box">
    <strong>What this chart shows:</strong> Each bar represents one minisector of the lap.
    Bars pointing <strong style="color:#27ae60">upward (green)</strong> = {driver_a} gained time here.
    Bars pointing <strong style="color:#e74c3c">downward (red)</strong> = {driver_b} gained time.
    The <strong>height of the bar</strong> = how many milliseconds were gained or lost in that sector.
    Tall bars = big differences. A series of tall bars in the same direction = one driver dominates
    that whole section of the circuit.
    </div>""", unsafe_allow_html=True)

    fig2, ax3 = plt.subplots(figsize=(14, 3.5))
    fig2.patch.set_facecolor("#0f0f0f"); ax3.set_facecolor("#0f0f0f")
    colors = ["#27AE60" if f == driver_a else "#E74C3C" for f in df["Faster"]]
    ax3.bar(df["MiniSector"], -df["Delta"], color=colors, width=0.8)
    ax3.axhline(0, color="white", linewidth=0.8, linestyle="--", alpha=0.5)
    ax3.set_xlabel("Minisector", color="white")
    ax3.set_ylabel(f"← {driver_b} faster  |  {driver_a} faster →", color="white")
    ax3.set_title("Delta per Minisector", color="white")
    ax3.tick_params(colors="white")
    for sp in ax3.spines.values(): sp.set_edgecolor("#333")
    ax3.grid(True, axis="y", alpha=0.3)
    fig2.tight_layout()
    st.pyplot(fig2); plt.close(fig2)

    # ── Insights ──────────────────────────────────────────────────
    biggest_gain_idx = df["Delta"].idxmin()
    biggest_loss_idx = df["Delta"].idxmax()
    st.markdown(f"""<div class="insight-box"><h4>🔍 Key findings</h4>
    <ul>
    <li><strong>{winner}</strong> was faster overall by <strong>{overall_gap:.3f}s</strong></li>
    <li><strong>{driver_a}</strong> was faster in <strong>{a_faster}</strong> of {minisectors} sectors.
        <strong>{driver_b}</strong> was faster in <strong>{b_faster}</strong> sectors.</li>
    <li><strong>{driver_a}'s biggest gain:</strong> Minisector {int(df.loc[biggest_gain_idx,'MiniSector'])}
        — {abs(df.loc[biggest_gain_idx,'Delta']):.3f}s advantage</li>
    <li><strong>{driver_b}'s biggest gain:</strong> Minisector {int(df.loc[biggest_loss_idx,'MiniSector'])}
        — {abs(df.loc[biggest_loss_idx,'Delta']):.3f}s advantage</li>
    <li>A driver can be slower overall yet win more individual sectors — this means they have a concentrated
        weakness in one or two high-value sectors that costs more than the sectors they win.</li>
    </ul></div>""", unsafe_allow_html=True)