import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

st.set_page_config(page_title="Multi-Season · F1 Analytics", page_icon="📈", layout="wide")

from f1_analysis.visualization.ui_theme import inject_f1_css, page_header, section_label, metrics_row
from f1_analysis.core.multi_season import (
    compare_driver_across_seasons,
    compare_two_drivers_across_seasons,
    driver_circuit_heatmap_data,
)
from f1_analysis.visualization.style import apply_f1_style

inject_f1_css()
page_header("📈", "Historical Analysis", "Multi-Season Comparison",
            "One driver across seasons, head-to-head across years, or a full season circuit performance heatmap.")

with st.sidebar:
    st.markdown("### ⚙️ Settings")
    mode         = st.selectbox("Mode", ["Single Driver Across Seasons","Head-to-Head Across Seasons","Circuit Heatmap"])
    session_type = st.selectbox("Session", ["Q","R"], index=0)

    if mode == "Single Driver Across Seasons":
        driver      = st.text_input("Driver", "VER").upper()
        gp          = st.text_input("Grand Prix", "Monaco")
        years_input = st.text_input("Years (space-separated)", "2021 2022 2023 2024")
    elif mode == "Head-to-Head Across Seasons":
        col1, col2  = st.columns(2)
        driver_a    = col1.text_input("Driver A", "VER").upper()
        driver_b    = col2.text_input("Driver B", "LEC").upper()
        gp          = st.text_input("Grand Prix", "Monaco")
        years_input = st.text_input("Years", "2022 2023 2024")
    else:
        driver      = st.text_input("Driver", "NOR").upper()
        year        = st.number_input("Year", 2018, 2026, 2024)
        max_rounds  = st.number_input("Max Rounds (0 = all)", 0, 24, 0)

    run = st.button("Run Comparison", type="primary")

if run:
    apply_f1_style()
    st.markdown('<div style="padding:0 2.5rem;">', unsafe_allow_html=True)

    if mode == "Single Driver Across Seasons":
        years = [int(y) for y in years_input.split()]
        with st.spinner(f"Loading {driver} at {gp} across {years}…"):
            df = compare_driver_across_seasons(driver, years, gp, session_type)
        if df.empty: st.error("No data found. Check driver code and Grand Prix name."); st.stop()

        section_label("Data Table")
        st.dataframe(df, use_container_width=True)

        section_label("Lap Time Trend & Teammate Gap")
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        fig.patch.set_facecolor("#0D0D0D")
        for ax in axes: ax.set_facecolor("#0D0D0D")

        ax = axes[0]
        ax.plot(df["Year"], df["BestLapSeconds"], marker="o", color="#3671C6",
                linewidth=2.5, markersize=8, label="Best Lap")
        ax.plot(df["Year"], df["MeanLapSeconds"], marker="s", color="#E8002D",
                linewidth=2, markersize=6, linestyle="--", label="Mean Lap")
        for i, row in df.iterrows():
            ax.annotate(f"{row['BestLapSeconds']:.2f}s", (row["Year"], row["BestLapSeconds"]),
                        textcoords="offset points", xytext=(0,10), ha="center",
                        fontsize=7.5, color="white")
        ax.set_xticks(df["Year"])
        ax.set_xlabel("Year", color="#888"); ax.set_ylabel("Lap Time (s)", color="#888")
        ax.set_title(f"{driver} at {gp} — Lap Times", color="white", fontsize=10)
        ax.legend(facecolor="#1A1A1A", labelcolor="white", fontsize=8)
        ax.tick_params(colors="#888"); ax.grid(True, alpha=0.12, color="#FFFFFF")
        for sp in ax.spines.values(): sp.set_edgecolor("#2A2A2A")

        ax2 = axes[1]
        valid = df["TeammateGapSeconds"].notna()
        if valid.any():
            gaps   = df.loc[valid,"TeammateGapSeconds"].values
            yrs    = df.loc[valid,"Year"].values
            colors = ["#27AE60" if g < 0 else "#E8002D" for g in gaps]
            bars   = ax2.bar(yrs, gaps, color=colors, width=0.5)
            ax2.axhline(0, color="white", linewidth=0.8, linestyle="--")
            for bar, val in zip(bars, gaps):
                ax2.text(bar.get_x()+bar.get_width()/2, val+(0.02 if val>=0 else -0.05),
                         f"{val:+.3f}s", ha="center", fontsize=8.5, color="white")
            ax2.set_xticks(yrs)
            ax2.set_xlabel("Year", color="#888"); ax2.set_ylabel("Gap vs Teammate (s)", color="#888")
            ax2.set_title("vs Teammate — green = driver faster", color="white", fontsize=10)
            ax2.tick_params(colors="#888"); ax2.grid(True, axis="y", alpha=0.12, color="#FFFFFF")
            for sp in ax2.spines.values(): sp.set_edgecolor("#2A2A2A")
        else:
            ax2.text(0.5,0.5,"No teammate gap data",ha="center",va="center",
                     transform=ax2.transAxes,color="white"); ax2.axis("off")

        fig.suptitle(f"{driver} at {gp} — Multi-Season", color="white", fontsize=12)
        fig.tight_layout(); st.pyplot(fig, use_container_width=True); plt.close(fig)

    elif mode == "Head-to-Head Across Seasons":
        years = [int(y) for y in years_input.split()]
        with st.spinner(f"Comparing {driver_a} vs {driver_b} at {gp}…"):
            df = compare_two_drivers_across_seasons(driver_a, driver_b, years, gp, session_type)
        if df.empty: st.error("No data found."); st.stop()

        section_label("Data Table")
        st.dataframe(df, use_container_width=True)

        section_label("Best Lap Comparison")
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        fig.patch.set_facecolor("#0D0D0D")
        for ax in axes: ax.set_facecolor("#0D0D0D")

        col_a = f"{driver_a}_BestLap"; col_b = f"{driver_b}_BestLap"
        ax = axes[0]
        ax.plot(df["Year"], df[col_a], marker="o", color="#3671C6", linewidth=2.5, markersize=8, label=driver_a)
        ax.plot(df["Year"], df[col_b], marker="s", color="#E8002D", linewidth=2.5, markersize=8, label=driver_b)
        ax.set_xticks(df["Year"]); ax.set_xlabel("Year", color="#888"); ax.set_ylabel("Best Lap (s)", color="#888")
        ax.set_title(f"{driver_a} vs {driver_b} at {gp}", color="white", fontsize=10)
        ax.legend(facecolor="#1A1A1A", labelcolor="white", fontsize=8)
        ax.tick_params(colors="#888"); ax.grid(True, alpha=0.12, color="#FFFFFF")
        for sp in ax.spines.values(): sp.set_edgecolor("#2A2A2A")

        ax2 = axes[1]
        gaps   = df["Gap_AminusB"].values
        colors = ["#27AE60" if g < 0 else "#E8002D" for g in gaps]
        bars   = ax2.bar(df["Year"], gaps, color=colors, width=0.5)
        ax2.axhline(0, color="white", linewidth=0.8, linestyle="--")
        for bar, val, faster in zip(bars, gaps, df["Faster"]):
            ax2.text(bar.get_x()+bar.get_width()/2, val+(0.02 if val>=0 else -0.06),
                     f"{val:+.3f}s\n({faster})", ha="center", fontsize=7.5, color="white")
        ax2.set_xticks(df["Year"]); ax2.set_xlabel("Year", color="#888")
        ax2.set_ylabel(f"Gap: {driver_a}−{driver_b} (s)", color="#888")
        ax2.set_title(f"green={driver_a} faster  red={driver_b} faster", color="white", fontsize=10)
        ax2.tick_params(colors="#888"); ax2.grid(True, axis="y", alpha=0.12, color="#FFFFFF")
        for sp in ax2.spines.values(): sp.set_edgecolor("#2A2A2A")

        fig.suptitle(f"{driver_a} vs {driver_b} at {gp}", color="white", fontsize=12)
        fig.tight_layout(); st.pyplot(fig, use_container_width=True); plt.close(fig)

    else:
        n_rounds = int(max_rounds) if max_rounds > 0 else None
        with st.spinner(f"Loading {driver}'s {year} season…"):
            df = driver_circuit_heatmap_data(driver, int(year), session_type, n_rounds)
        if df.empty: st.error("No data found."); st.stop()

        section_label("Data Table")
        st.dataframe(df, use_container_width=True)

        section_label("Gap-to-Pole Heatmap")
        df_sorted  = df.sort_values("Round")
        gaps       = df_sorted["GapToSessionBest"].values
        circuits   = [c.replace(" Grand Prix","") for c in df_sorted["Circuit"]]
        bar_colors = ["#27AE60" if g<=0.001 else "#F39C12" if g<=0.3 else "#E8002D" for g in gaps]

        fig, ax = plt.subplots(figsize=(max(12, len(circuits)*0.8), 5))
        fig.patch.set_facecolor("#0D0D0D"); ax.set_facecolor("#0D0D0D")
        bars = ax.bar(range(len(circuits)), gaps, color=bar_colors, width=0.7)
        for bar, val in zip(bars, gaps):
            ax.text(bar.get_x()+bar.get_width()/2, val+0.005,
                    "POLE" if val<=0.001 else f"+{val:.3f}s",
                    ha="center", va="bottom", fontsize=7, color="white", rotation=45)
        ax.set_xticks(range(len(circuits)))
        ax.set_xticklabels(circuits, fontsize=7.5, rotation=45, ha="right", color="#888")
        ax.set_ylabel("Gap to Session Fastest (s)", color="#888", fontsize=8)
        ax.set_title(
            f"{driver} — Gap to Session Best — {year} ({session_type})\n"
            "green = pole/fastest  orange = within 0.3s  red = further back",
            color="white", fontsize=10
        )
        ax.tick_params(colors="#888"); ax.grid(True, axis="y", alpha=0.12, color="#FFFFFF")
        for sp in ax.spines.values(): sp.set_edgecolor("#2A2A2A")
        fig.tight_layout(); st.pyplot(fig, use_container_width=True); plt.close(fig)

    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.markdown("""
<div style="padding:4rem 2.5rem; text-align:center; color:#333;
            font-family:'Titillium Web',sans-serif; font-size:0.8rem;
            text-transform:uppercase; letter-spacing:0.15em;">
    Select a comparison mode and configure settings, then press Run Comparison
</div>""", unsafe_allow_html=True)