import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
st.set_page_config(page_title="Multi-Season", page_icon="📈", layout="wide")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from f1_analysis.visualization.ui_theme import inject_f1_css, page_header, section_label, metrics_row
inject_f1_css()
page_header(
    "📈",
    "Historical Analysis",
    "Multi Season",
    "Compare driver and team performance trends across multiple seasons."
)

EXPLAIN = """<div style="background:#141414;border:1px solid #2A2A2A;border-left:3px solid #E8002D;
padding:.9rem 1.2rem;margin:.8rem 0 1.2rem;color:#aaa;font-size:.88rem;line-height:1.65;
font-family:'Inter',sans-serif;">{text}</div>"""

INSIGHT = """<div style="background:#0D0D0D;border:1px solid #2A2A2A;border-top:2px solid #E8002D;
padding:1rem 1.3rem;margin-top:1rem;font-family:'Inter',sans-serif;">
<div style="font-family:'Titillium Web',sans-serif;font-size:.65rem;font-weight:700;
text-transform:uppercase;letter-spacing:.2em;color:#E8002D;margin-bottom:.6rem;">Key Insights</div>
{text}</div>"""

import numpy as np
import pandas as pd

from f1_analysis.core.multi_season import (
    compare_driver_across_seasons,
    compare_two_drivers_across_seasons,
    driver_circuit_heatmap_data,
)
from f1_analysis.visualization.style import apply_f1_style


st.sidebar.header("Mode")
mode         = st.sidebar.selectbox("Analysis type", ["Single Driver Across Seasons", "Head-to-Head Rivalry", "Circuit Heatmap"])
session_type = st.sidebar.selectbox("Session", ["Q", "R"])

if mode == "Single Driver Across Seasons":
    driver      = st.sidebar.text_input("Driver", "VER").upper()
    gp          = st.sidebar.text_input("Grand Prix", "Monaco")
    years_input = st.sidebar.text_input("Years", "2021 2022 2023 2024")
    st.sidebar.caption("Compares the same driver at the same circuit across multiple seasons — great for seeing how a car or driver has improved.")

elif mode == "Head-to-Head Rivalry":
    c1, c2 = st.sidebar.columns(2)
    driver_a    = c1.text_input("Driver A", "VER").upper()
    driver_b    = c2.text_input("Driver B", "LEC").upper()
    gp          = st.sidebar.text_input("Grand Prix", "Monaco")
    years_input = st.sidebar.text_input("Years", "2022 2023 2024")
    st.sidebar.caption("Who wins this circuit head-to-head, and has the balance shifted over the years?")

else:
    driver     = st.sidebar.text_input("Driver", "NOR").upper()
    year       = st.sidebar.number_input("Year", 2018, 2026, 2024)
    max_rounds = st.sidebar.number_input("Max Rounds (0 = all)", 0, 24, 0)
    st.sidebar.caption("Shows a driver's gap to the session fastest at every circuit — reveals their best and worst tracks.")

if st.sidebar.button("Run Analysis", type="primary"):
    apply_f1_style()

    if mode == "Single Driver Across Seasons":
        years = [int(y) for y in years_input.split()]
        with st.spinner(f"Loading {driver} at {gp} across {years}..."):
            df = compare_driver_across_seasons(driver, years, gp, session_type)
        if df.empty:
            st.error("No data found. Check driver code and Grand Prix name."); st.stop()

        st.markdown(f"""<div style="background:#141414;border:1px solid #2A2A2A;border-left:3px solid #E8002D;padding:.9rem 1.2rem;margin:.8rem 0 1.2rem;color:#aaa;font-size:.88rem;line-height:1.65;font-family:'Inter',sans-serif;">
        <strong>What this shows:</strong> {driver}'s best lap time and average pace at {gp}
        in each of the selected seasons. Year-on-year improvement could reflect a better car,
        better driver understanding of the circuit, or both.
        The teammate gap chart shows how {driver} compared to their teammate in each year —
        green = {driver} was faster, red = teammate was faster. This isolates the
        <strong>driver's contribution</strong> from the car's performance.
        </div>""", unsafe_allow_html=True)

        st.dataframe(df.round(3), use_container_width=True)

        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        fig.patch.set_facecolor("#0f0f0f")
        for ax in axes: ax.set_facecolor("#0f0f0f")

        ax = axes[0]
        ax.plot(df["Year"], df["BestLapSeconds"], marker="o", color="#3671C6",
                linewidth=2.5, markersize=8, label="Best Lap")
        ax.plot(df["Year"], df["MeanLapSeconds"], marker="s", color="#E8002D",
                linewidth=2, markersize=6, linestyle="--", label="Mean Lap")
        for i, row in df.iterrows():
            ax.annotate(f"{row['BestLapSeconds']:.2f}s",
                        (row["Year"], row["BestLapSeconds"]),
                        textcoords="offset points", xytext=(0, 10),
                        ha="center", fontsize=8, color="white")
        ax.set_xticks(df["Year"]); ax.set_xlabel("Year", color="white")
        ax.set_ylabel("Lap Time (s)", color="white")
        ax.set_title(f"{driver} at {gp} — Lap Time Trend", color="white")
        ax.legend(facecolor="#1a1a1a", labelcolor="white")
        ax.tick_params(colors="white"); ax.grid(True, alpha=0.3)

        ax2 = axes[1]
        valid = df["TeammateGapSeconds"].notna()
        if valid.any():
            gaps   = df.loc[valid, "TeammateGapSeconds"].values
            yrs    = df.loc[valid, "Year"].values
            colors = ["#27AE60" if g < 0 else "#E74C3C" for g in gaps]
            bars   = ax2.bar(yrs, gaps, color=colors, width=0.5)
            ax2.axhline(0, color="white", linewidth=1, linestyle="--")
            for bar, val in zip(bars, gaps):
                ax2.text(bar.get_x()+bar.get_width()/2,
                         val+(0.02 if val>=0 else -0.05),
                         f"{val:+.3f}s", ha="center", fontsize=9, color="white")
            ax2.set_xticks(yrs); ax2.set_xlabel("Year", color="white")
            ax2.set_ylabel("Gap vs Teammate (s)", color="white")
            ax2.set_title("vs Teammate — green = driver faster", color="white")
            ax2.tick_params(colors="white"); ax2.grid(True, axis="y", alpha=0.3)
        else:
            ax2.text(0.5, 0.5, "No teammate data", ha="center", va="center",
                     transform=ax2.transAxes, color="white"); ax2.axis("off")
        fig.suptitle(f"{driver} at {gp} — Multi-Season", color="white", fontsize=13)
        fig.tight_layout(); st.pyplot(fig); plt.close(fig)

        # Insight
        best_year = df.loc[df["BestLapSeconds"].idxmin()]
        worst_year = df.loc[df["BestLapSeconds"].idxmax()]
        improvement = worst_year["BestLapSeconds"] - best_year["BestLapSeconds"]
        st.markdown(f"""<div style="background:#0D0D0D;border:1px solid #2A2A2A;border-top:2px solid #E8002D;padding:1rem 1.3rem;margin-top:1rem;font-family:'Inter',sans-serif;"><div style="font-family:'Titillium Web',sans-serif;font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.2em;color:#E8002D;margin-bottom:.6rem;">Key Insights</div><div style="color:#ccc;font-size:.88rem;font-family:'Inter',sans-serif;"><h4 style="color:#fff;margin:.3rem 0;">🔍 Season-over-season story</h4>
        <ul>
        <li><strong>Best performance:</strong> {int(best_year['Year'])} — {best_year['BestLapSeconds']:.3f}s
        {"(with " + str(best_year['Team']) + ")" if best_year.get('Team') else ""}</li>
        <li><strong>Worst performance:</strong> {int(worst_year['Year'])} — {worst_year['BestLapSeconds']:.3f}s</li>
        <li><strong>Overall improvement:</strong> {improvement:.3f}s faster in best year vs worst —
        {"a significant gain suggesting major car or driver development." if improvement > 0.5 else
        "a relatively stable performance level across seasons."}</li>
        </ul></div></div>""", unsafe_allow_html=True)

    elif mode == "Head-to-Head Rivalry":
        years = [int(y) for y in years_input.split()]
        with st.spinner(f"Comparing {driver_a} vs {driver_b} at {gp}..."):
            df = compare_two_drivers_across_seasons(driver_a, driver_b, years, gp, session_type)
        if df.empty:
            st.error("No data found."); st.stop()

        a_wins = int((df["Faster"] == driver_a).sum())
        b_wins = int((df["Faster"] == driver_b).sum())

        st.markdown(f"""<div style="background:#141414;border:1px solid #2A2A2A;border-left:3px solid #E8002D;padding:.9rem 1.2rem;margin:.8rem 0 1.2rem;color:#aaa;font-size:.88rem;line-height:1.65;font-family:'Inter',sans-serif;">
        <strong>Head-to-head at {gp}:</strong>
        <strong>{driver_a}</strong> leads {a_wins}–{b_wins} across the selected seasons.
        The bar chart shows the qualifying/race gap — green bars mean {driver_a} was faster that year,
        red means {driver_b} was. The height of the bar shows how large the gap was.
        A consistently green or red chart = one driver has a structural advantage at this circuit.
        Alternating bars = the circuit suits neither driver particularly, and small setup or
        conditions changes swing the advantage.
        </div>""", unsafe_allow_html=True)

        st.dataframe(df.round(3), use_container_width=True)

        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        fig.patch.set_facecolor("#0f0f0f")
        for ax in axes: ax.set_facecolor("#0f0f0f")

        col_a, col_b = f"{driver_a}_BestLap", f"{driver_b}_BestLap"
        ax = axes[0]
        ax.plot(df["Year"], df[col_a], marker="o", color="#3671C6", linewidth=2.5, markersize=8, label=driver_a)
        ax.plot(df["Year"], df[col_b], marker="s", color="#E8002D", linewidth=2.5, markersize=8, label=driver_b)
        ax.set_xticks(df["Year"]); ax.set_xlabel("Year", color="white")
        ax.set_ylabel("Best Lap (s)", color="white")
        ax.set_title(f"Best Lap — {driver_a} vs {driver_b} at {gp}", color="white")
        ax.legend(facecolor="#1a1a1a", labelcolor="white")
        ax.tick_params(colors="white"); ax.grid(True, alpha=0.3)

        ax2 = axes[1]
        gaps   = df["Gap_AminusB"].values
        colors = ["#27AE60" if g < 0 else "#E74C3C" for g in gaps]
        bars   = ax2.bar(df["Year"], gaps, color=colors, width=0.5)
        ax2.axhline(0, color="white", linewidth=1, linestyle="--")
        for bar, val, faster in zip(bars, gaps, df["Faster"]):
            ax2.text(bar.get_x()+bar.get_width()/2,
                     val+(0.02 if val>=0 else -0.06),
                     f"{val:+.3f}s\n({faster})", ha="center", fontsize=8, color="white")
        ax2.set_xticks(df["Year"]); ax2.set_xlabel("Year", color="white")
        ax2.set_ylabel(f"Gap: {driver_a} − {driver_b} (s)", color="white")
        ax2.set_title(f"green={driver_a} faster  red={driver_b} faster", color="white")
        ax2.tick_params(colors="white"); ax2.grid(True, axis="y", alpha=0.3)
        fig.suptitle(f"{driver_a} vs {driver_b} at {gp}", color="white", fontsize=13)
        fig.tight_layout(); st.pyplot(fig); plt.close(fig)

        avg_gap = df["Gap_AminusB"].mean()
        st.markdown(f"""<div style="background:#0D0D0D;border:1px solid #2A2A2A;border-top:2px solid #E8002D;padding:1rem 1.3rem;margin-top:1rem;font-family:'Inter',sans-serif;"><div style="font-family:'Titillium Web',sans-serif;font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.2em;color:#E8002D;margin-bottom:.6rem;">Key Insights</div><div style="color:#ccc;font-size:.88rem;font-family:'Inter',sans-serif;"><h4 style="color:#fff;margin:.3rem 0;">🔍 Rivalry verdict at {gp}</h4>
        <ul>
        <li><strong>{driver_a}</strong> wins this head-to-head <strong>{a_wins}–{b_wins}</strong>
        across {a_wins+b_wins} seasons.</li>
        <li>Average gap: <strong>{abs(avg_gap):.3f}s</strong> in favour of
        <strong>{"driver_a" if avg_gap < 0 else driver_b}</strong></li>
        <li>{"The gap is very consistent, suggesting a structural car/driver advantage at this circuit." if df["GapAbs"].std() < 0.15
        else "The advantage switches between seasons, suggesting both drivers can win here depending on conditions and car setup."}</li>
        </ul></div></div>""", unsafe_allow_html=True)

    else:
        n_rounds = int(max_rounds) if max_rounds > 0 else None
        with st.spinner(f"Loading {driver}'s {year} season..."):
            df = driver_circuit_heatmap_data(driver, int(year), session_type, n_rounds)
        if df.empty:
            st.error("No data found."); st.stop()

        st.markdown(f"""<div style="background:#141414;border:1px solid #2A2A2A;border-left:3px solid #E8002D;padding:.9rem 1.2rem;margin:.8rem 0 1.2rem;color:#aaa;font-size:.88rem;line-height:1.65;font-family:'Inter',sans-serif;">
        <strong>What this shows:</strong> {driver}'s gap to the session fastest at every circuit
        in the {year} season. <strong style="color:#27ae60">Green = pole/fastest</strong>
        (gap of 0). <strong style="color:#f39c12">Orange = within 0.3s</strong> (strong performance).
        <strong style="color:#e74c3c">Red = more than 0.3s off</strong> (struggling).
        This reveals which circuits suit the driver and car, and where development is needed.
        </div>""", unsafe_allow_html=True)

        st.dataframe(df.round(3), use_container_width=True)

        df_sorted  = df.sort_values("Round")
        gaps       = df_sorted["GapToSessionBest"].values
        circuits   = [c.replace(" Grand Prix","") for c in df_sorted["Circuit"]]
        bar_colors = ["#27AE60" if g<=0.001 else "#F39C12" if g<=0.3 else "#E74C3C" for g in gaps]

        fig, ax = plt.subplots(figsize=(max(12, len(circuits)*0.75), 5))
        fig.patch.set_facecolor("#0f0f0f"); ax.set_facecolor("#0f0f0f")
        bars = ax.bar(range(len(circuits)), gaps, color=bar_colors, width=0.7)
        for bar, val in zip(bars, gaps):
            ax.text(bar.get_x()+bar.get_width()/2, val+0.005,
                    "POLE" if val<=0.001 else f"+{val:.3f}s",
                    ha="center", va="bottom", fontsize=7, color="white", rotation=45)
        ax.set_xticks(range(len(circuits)))
        ax.set_xticklabels(circuits, fontsize=8, rotation=45, ha="right", color="white")
        ax.set_ylabel("Gap to Session Fastest (s)", color="white")
        ax.set_title(f"{driver} — Gap to Session Best per Circuit — {year}", color="white")
        ax.tick_params(colors="white"); ax.grid(True, axis="y", alpha=0.3)
        fig.tight_layout(); st.pyplot(fig); plt.close(fig)

        best_circuit   = df.loc[df["GapToSessionBest"].idxmin()]
        worst_circuit  = df.loc[df["GapToSessionBest"].idxmax()]
        avg_gap        = df["GapToSessionBest"].mean()
        pole_circuits  = df[df["GapToSessionBest"] <= 0.001]

        st.markdown(f"""<div style="background:#0D0D0D;border:1px solid #2A2A2A;border-top:2px solid #E8002D;padding:1rem 1.3rem;margin-top:1rem;font-family:'Inter',sans-serif;"><div style="font-family:'Titillium Web',sans-serif;font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.2em;color:#E8002D;margin-bottom:.6rem;">Key Insights</div><div style="color:#ccc;font-size:.88rem;font-family:'Inter',sans-serif;"><h4 style="color:#fff;margin:.3rem 0;">🔍 {driver}'s {year} circuit strengths</h4>
        <ul>
        {"<li>🏆 <strong>Pole/fastest at:</strong> " + ", ".join(pole_circuits["Circuit"].str.replace(" Grand Prix","").tolist()) + "</li>" if not pole_circuits.empty else ""}
        <li><strong>Best circuit:</strong> {best_circuit['Circuit'].replace(' Grand Prix','')}
        — only <strong>{best_circuit['GapToSessionBest']:.3f}s</strong> off fastest</li>
        <li><strong>Weakest circuit:</strong> {worst_circuit['Circuit'].replace(' Grand Prix','')}
        — <strong>{worst_circuit['GapToSessionBest']:.3f}s</strong> off fastest</li>
        <li><strong>Season average gap:</strong> {avg_gap:.3f}s — 
        {"very competitive across the calendar." if avg_gap < 0.2 else "some circuits clearly suit the car better than others."}</li>
        </ul></div></div>""", unsafe_allow_html=True)