import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
st.set_page_config(page_title="Tyre Degradation · F1 Analytics", page_icon="🛞", layout="wide")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

from f1_analysis.visualization.ui_theme import inject_f1_css, page_header, section_label, metrics_row
from f1_analysis.core.session_loader import load_session
from f1_analysis.core.lap_analysis import clean_lap_times, laps_to_seconds, stint_summary
from f1_analysis.visualization.style import apply_f1_style

inject_f1_css()
page_header(
    "🛞",
    "Strategy Analysis",
    "Tyre Degradation",
    "Real lap-time degradation curves per compound — see cliff laps, stint lengths, and compound delta."
)

EXPLAIN = """<div style="background:#141414;border:1px solid #2A2A2A;border-left:3px solid #E8002D;
padding:.9rem 1.2rem;margin:.8rem 0 1.2rem;color:#aaa;font-size:.88rem;line-height:1.65;
font-family:'Inter',sans-serif;">{text}</div>"""

INSIGHT = """<div style="background:#0D0D0D;border:1px solid #2A2A2A;border-top:2px solid #E8002D;
padding:1rem 1.3rem;margin-top:1rem;font-family:'Inter',sans-serif;">
<div style="font-family:'Titillium Web',sans-serif;font-size:.65rem;font-weight:700;
text-transform:uppercase;letter-spacing:.2em;color:#E8002D;margin-bottom:.6rem;">Key Insights</div>
{text}</div>"""

COMPOUND_COLORS = {
    "SOFT":         "#DA291C",
    "MEDIUM":       "#FFD700",
    "HARD":         "#F0F0F0",
    "INTERMEDIATE": "#43B02A",
    "WET":          "#0067AD",
    "UNKNOWN":      "#888888",
}

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    year    = st.number_input("Year", 2018, 2026, 2025)
    gp      = st.text_input("Grand Prix", "Bahrain")
    drivers_input = st.text_input("Drivers (space-separated, leave blank for all)", "")
    min_laps = st.slider("Min laps on tyre to include", 2, 10, 3,
                         help="Filters out very short stints (in/out laps, SC stints) that skew the curves.")
    show_scatter = st.checkbox("Show individual laps (scatter)", value=True)
    show_trend   = st.checkbox("Show rolling average trend line", value=True)
    run = st.button("Analyse Degradation", type="primary")

# ── Empty state ───────────────────────────────────────────────────────────────
if not run:
    st.markdown(EXPLAIN.format(text="""
    <strong>What this page shows:</strong> For each tyre compound used in a race, this tool plots
    lap times against tyre age (laps on that set). The <strong>slope of the curve</strong> is the degradation
    rate — steeper = compound falls off faster. A sudden jump upward is a <strong>cliff lap</strong>.
    <br><br>
    ◉ <strong>Soft</strong> (red) — fastest but degrades quickest. Typically only viable for 15–25 laps.<br>
    ◉ <strong>Medium</strong> (yellow) — balanced. Usually the strategic baseline.<br>
    ◉ <strong>Hard</strong> (white) — slowest initially but holds pace longest. Used for 30–40+ lap stints.<br>
    <br>
    Enter a year and Grand Prix name in the sidebar and click <strong>Analyse Degradation</strong>.
    """), unsafe_allow_html=True)
    st.stop()

# ── Load data ─────────────────────────────────────────────────────────────────
with st.spinner(f"Loading {year} {gp} Race telemetry…"):
    apply_f1_style()
    try:
        session = load_session(year, gp, "R")
    except Exception as e:
        st.error(f"Could not load session: {e}\n\nCheck the Grand Prix name spelling (e.g. 'Bahrain', 'Monaco', 'Silverstone').")
        st.stop()

laps_raw = session.laps.copy()

# Filter to selected drivers
drivers_list = [d.strip().upper() for d in drivers_input.split() if d.strip()]
if drivers_list:
    laps_raw = laps_raw[laps_raw["Driver"].isin(drivers_list)]
    if laps_raw.empty:
        st.error(f"No data found for drivers: {', '.join(drivers_list)}. Check abbreviations.")
        st.stop()

# Clean laps — exclude pit laps and inaccurate timing
laps_clean = clean_lap_times(laps_raw, exclude_pit_laps=True, exclude_inaccurate=True)

if laps_clean.empty:
    st.error("No clean laps found for this session. Try a different session or year.")
    st.stop()

laps_clean = laps_clean.copy()
laps_clean["LapTimeSeconds"] = laps_to_seconds(laps_clean)
laps_clean["Compound"] = laps_clean["Compound"].fillna("UNKNOWN").str.upper()

# Only keep compounds with enough data
compound_counts = laps_clean.groupby("Compound")["TyreLife"].count()
valid_compounds = compound_counts[compound_counts >= min_laps * 2].index.tolist()
laps_clean = laps_clean[laps_clean["Compound"].isin(valid_compounds)]

compounds_present = sorted(laps_clean["Compound"].unique(),
                           key=lambda c: ["SOFT","MEDIUM","HARD","INTERMEDIATE","WET","UNKNOWN"].index(c)
                           if c in ["SOFT","MEDIUM","HARD","INTERMEDIATE","WET","UNKNOWN"] else 99)

event_name = session.event["EventName"] if hasattr(session, "event") else f"{year} {gp}"

# ── Hero metrics ──────────────────────────────────────────────────────────────
n_drivers = laps_clean["Driver"].nunique()
n_laps    = len(laps_clean)
fastest   = laps_clean["LapTimeSeconds"].min()
slowest   = laps_clean["LapTimeSeconds"].max()

metrics_row([
    {"label": "Compounds Analysed", "value": str(len(compounds_present)), "color": "accent"},
    {"label": "Drivers",            "value": str(n_drivers)},
    {"label": "Clean Laps",         "value": str(n_laps),                 "color": "teal"},
    {"label": "Fastest Clean Lap",  "value": f"{fastest:.3f}s",           "color": "gold"},
    {"label": "Lap Time Spread",    "value": f"{slowest - fastest:.2f}s"},
])

# ── Main degradation chart ────────────────────────────────────────────────────
section_label("Lap Time vs Tyre Age")
st.markdown(EXPLAIN.format(text=
    "Each point is one clean racing lap. The <strong>x-axis is tyre life</strong> (laps on that set, "
    "starting from 1). The <strong>y-axis is lap time in seconds</strong>. The rolling average line "
    "smooths over driver/traffic variation to reveal the compound's underlying degradation trend. "
    "A flat or slightly rising line = low degradation. A steep upward trend = compound falling off fast."
), unsafe_allow_html=True)

fig, ax = plt.subplots(figsize=(12, 6))
fig.patch.set_facecolor("#0D0D0D")
ax.set_facecolor("#141414")

for compound in compounds_present:
    df_c = laps_clean[laps_clean["Compound"] == compound].copy()
    color = COMPOUND_COLORS.get(compound, "#888888")

    if show_scatter:
        ax.scatter(
            df_c["TyreLife"], df_c["LapTimeSeconds"],
            color=color, alpha=0.25, s=18, zorder=2,
            label=f"_{compound} laps"
        )

    if show_trend and len(df_c) >= min_laps:
        # Group by tyre life and take median to remove outliers
        trend = (
            df_c.groupby("TyreLife")["LapTimeSeconds"]
            .median()
            .rolling(window=3, min_periods=1, center=True)
            .mean()
        )
        ax.plot(
            trend.index, trend.values,
            color=color, linewidth=2.5, zorder=3,
            label=f"{compound.capitalize()}"
        )

ax.set_xlabel("Tyre Life (laps on set)", color="#888", fontsize=11)
ax.set_ylabel("Lap Time (seconds)", color="#888", fontsize=11)
ax.set_title(f"{event_name} — Tyre Degradation by Compound", color="#FFFFFF", fontsize=13, pad=14)
ax.tick_params(colors="#666")
ax.spines["bottom"].set_color("#2A2A2A")
ax.spines["left"].set_color("#2A2A2A")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.grid(True, alpha=0.12, color="#444")
ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f"))

legend = ax.legend(
    loc="upper left", framealpha=0.15, labelcolor="white",
    facecolor="#1A1A1A", edgecolor="#2A2A2A", fontsize=10
)
fig.tight_layout()
st.pyplot(fig)
plt.close(fig)

# ── Per-compound breakdown ────────────────────────────────────────────────────
section_label("Per-Compound Breakdown")

cols = st.columns(len(compounds_present))
for col, compound in zip(cols, compounds_present):
    df_c = laps_clean[laps_clean["Compound"] == compound]
    color = COMPOUND_COLORS.get(compound, "#888888")

    median_pace  = df_c["LapTimeSeconds"].median()
    max_life     = int(df_c["TyreLife"].max())
    n_stints     = df_c.groupby(["Driver", "Stint"]).ngroups if "Stint" in df_c.columns else "—"

    # Degradation rate: slope of median lap time per tyre-life lap
    try:
        trend_grp = df_c.groupby("TyreLife")["LapTimeSeconds"].median()
        if len(trend_grp) >= 4:
            slope, _ = np.polyfit(trend_grp.index, trend_grp.values, 1)
            deg_str  = f"+{slope:.3f}s/lap"
        else:
            deg_str = "—"
    except Exception:
        deg_str = "—"

    with col:
        st.markdown(f"""
<div style="background:#141414;border:1px solid #2A2A2A;border-top:3px solid {color};
padding:1rem 1.1rem;border-radius:2px;">
  <div style="font-family:'Titillium Web',sans-serif;font-size:0.7rem;font-weight:700;
              text-transform:uppercase;letter-spacing:0.15em;color:{color};margin-bottom:0.6rem;">
    {compound.capitalize()}
  </div>
  <div style="font-family:'Inter',sans-serif;font-size:0.82rem;color:#ccc;line-height:2;">
    <span style="color:#555;">Median pace</span><br>
    <strong style="font-size:1.1rem;color:#fff;">{median_pace:.3f}s</strong><br>
    <span style="color:#555;">Max tyre life seen</span><br>
    <strong style="color:#fff;">{max_life} laps</strong><br>
    <span style="color:#555;">Degradation rate</span><br>
    <strong style="color:#fff;">{deg_str}</strong><br>
    <span style="color:#555;">Stints in data</span><br>
    <strong style="color:#fff;">{n_stints}</strong>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Stint-level detail ────────────────────────────────────────────────────────
section_label("Stint Detail by Driver")
st.markdown(EXPLAIN.format(text=
    "Each row is one stint. <strong>Avg Lap Time</strong> is the mean of all clean laps in that stint. "
    "Use this to compare how different drivers managed the same compound — a lower average on the same "
    "compound length usually means better tyre management."
), unsafe_allow_html=True)

if "Stint" in laps_raw.columns:
    stint_df = stint_summary(laps_raw)
    stint_df = stint_df[stint_df["Compound"].str.upper().isin(compounds_present)]
    stint_df = stint_df[stint_df["LapCount"] >= min_laps]
    stint_df["Compound"] = stint_df["Compound"].str.upper()
    stint_df["AvgLapTime"] = stint_df["AvgLapTime"].round(3)
    stint_df = stint_df.rename(columns={
        "Driver": "Driver", "Stint": "Stint #", "Compound": "Compound",
        "LapCount": "Laps", "FirstLap": "First Lap", "LastLap": "Last Lap",
        "AvgLapTime": "Avg Lap (s)"
    })
    st.dataframe(
        stint_df[["Driver","Stint #","Compound","Laps","First Lap","Last Lap","Avg Lap (s)"]],
        use_container_width=True, hide_index=True
    )
else:
    st.info("Stint breakdown not available for this session.")

# ── Per-compound degradation mini charts ──────────────────────────────────────
if len(compounds_present) > 1:
    section_label("Compound vs Compound Pace Comparison")
    st.markdown(EXPLAIN.format(text=
        "Overlaid median lap times for all compounds on the same axis. "
        "Compound lines that <strong>converge at high tyre life</strong> indicate the harder compound "
        "eventually catches the softer. Where lines <strong>cross</strong>, the harder tyre is now faster."
    ), unsafe_allow_html=True)

    fig2, ax2 = plt.subplots(figsize=(12, 5))
    fig2.patch.set_facecolor("#0D0D0D")
    ax2.set_facecolor("#141414")

    for compound in compounds_present:
        df_c = laps_clean[laps_clean["Compound"] == compound]
        color = COMPOUND_COLORS.get(compound, "#888888")
        trend = (
            df_c.groupby("TyreLife")["LapTimeSeconds"]
            .median()
            .rolling(window=3, min_periods=1, center=True)
            .mean()
        )
        ax2.plot(trend.index, trend.values, color=color, linewidth=2.5, label=compound.capitalize())

    ax2.set_xlabel("Tyre Life (laps)", color="#888", fontsize=11)
    ax2.set_ylabel("Median Lap Time (s)", color="#888", fontsize=11)
    ax2.set_title("Compound Pace Comparison — Median Lap Time", color="#fff", fontsize=12, pad=12)
    ax2.tick_params(colors="#666")
    for spine in ax2.spines.values():
        spine.set_color("#2A2A2A")
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    ax2.grid(True, alpha=0.12, color="#444")
    ax2.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f"))
    ax2.legend(framealpha=0.15, labelcolor="white", facecolor="#1A1A1A", edgecolor="#2A2A2A", fontsize=10)
    fig2.tight_layout()
    st.pyplot(fig2)
    plt.close(fig2)

# ── Key insights ──────────────────────────────────────────────────────────────
fastest_compound = laps_clean.groupby("Compound")["LapTimeSeconds"].median().idxmin()
longest_compound = laps_clean.groupby("Compound")["TyreLife"].max().idxmax()
try:
    rates = {}
    for c in compounds_present:
        df_c = laps_clean[laps_clean["Compound"] == c]
        trend_grp = df_c.groupby("TyreLife")["LapTimeSeconds"].median()
        if len(trend_grp) >= 4:
            slope, _ = np.polyfit(trend_grp.index, trend_grp.values, 1)
            rates[c] = slope
    slowest_deg = min(rates, key=rates.get) if rates else "—"
    fastest_deg = max(rates, key=rates.get) if rates else "—"
    deg_insight = (f"<li><strong>{slowest_deg.capitalize()}</strong> had the lowest degradation rate "
                   f"({rates[slowest_deg]:+.3f}s/lap) — best for long stints.</li>"
                   f"<li><strong>{fastest_deg.capitalize()}</strong> degraded fastest "
                   f"({rates[fastest_deg]:+.3f}s/lap).</li>") if rates else ""
except Exception:
    deg_insight = ""

st.markdown(INSIGHT.format(text=f"""
<div style="color:#ccc;font-size:.88rem;font-family:'Inter',sans-serif;">
<ul style="margin:0;padding-left:1.2rem;line-height:2;">
  <li><strong>{fastest_compound.capitalize()}</strong> was the fastest compound by median lap time.</li>
  <li><strong>{longest_compound.capitalize()}</strong> saw the longest individual stints in this race.</li>
  {deg_insight}
  <li>A positive degradation rate (e.g. +0.08s/lap) means the tyre loses ~{0.08*10:.1f}s over 10 laps 
      relative to its fresh pace — compounding into significant strategy considerations.</li>
</ul>
</div>
"""), unsafe_allow_html=True)