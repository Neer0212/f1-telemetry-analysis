import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from f1_analysis.core.multi_season import (
    compare_driver_across_seasons,
    compare_two_drivers_across_seasons,
    driver_circuit_heatmap_data,
)
from f1_analysis.visualization.style import apply_f1_style

st.set_page_config(page_title="Multi-Season", page_icon="📈", layout="wide")
st.title("📈 Multi-Season Comparison")
st.markdown("Compare driver performance across multiple seasons at the same circuit, or across all circuits in a season.")

st.sidebar.header("Settings")
mode = st.sidebar.selectbox("Mode", ["Single Driver Across Seasons", "Head-to-Head Across Seasons", "Circuit Heatmap"])
session_type = st.sidebar.selectbox("Session", ["Q", "R"], index=0)

if mode == "Single Driver Across Seasons":
    driver = st.sidebar.text_input("Driver", "VER").upper()
    gp     = st.sidebar.text_input("Grand Prix", "Monaco")
    years_input = st.sidebar.text_input("Years (space separated)", "2021 2022 2023 2024")

elif mode == "Head-to-Head Across Seasons":
    col1, col2 = st.sidebar.columns(2)
    driver_a = col1.text_input("Driver A", "VER").upper()
    driver_b = col2.text_input("Driver B", "LEC").upper()
    gp       = st.sidebar.text_input("Grand Prix", "Monaco")
    years_input = st.sidebar.text_input("Years", "2022 2023 2024")

else:
    driver      = st.sidebar.text_input("Driver", "NOR").upper()
    year        = st.sidebar.number_input("Year", 2018, 2026, 2024)
    max_rounds  = st.sidebar.number_input("Max Rounds (0 = all)", 0, 24, 0)

if st.sidebar.button("Run Comparison", type="primary"):
    apply_f1_style()

    # ── Mode 1: Single driver ─────────────────────────────────────────
    if mode == "Single Driver Across Seasons":
        years = [int(y) for y in years_input.split()]
        with st.spinner(f"Loading {driver} at {gp} for {years}..."):
            df = compare_driver_across_seasons(driver, years, gp, session_type)

        if df.empty:
            st.error("No data found. Check driver code and Grand Prix name.")
            st.stop()

        st.dataframe(df, use_container_width=True)

        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        fig.patch.set_facecolor("#0f0f0f")
        for ax in axes: ax.set_facecolor("#0f0f0f")

        # Lap time trend
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
        ax.set_xticks(df["Year"])
        ax.set_xlabel("Year", color="white"); ax.set_ylabel("Lap Time (s)", color="white")
        ax.set_title(f"{driver} at {gp} — Lap Times by Season", color="white")
        ax.legend(facecolor="#1a1a1a", labelcolor="white")
        ax.tick_params(colors="white"); ax.grid(True, alpha=0.3)

        # Teammate gap
        ax2 = axes[1]
        valid = df["TeammateGapSeconds"].notna()
        if valid.any():
            gaps = df.loc[valid, "TeammateGapSeconds"].values
            yrs  = df.loc[valid, "Year"].values
            colors = ["#27AE60" if g < 0 else "#E74C3C" for g in gaps]
            bars = ax2.bar(yrs, gaps, color=colors, width=0.5)
            ax2.axhline(0, color="white", linewidth=1, linestyle="--")
            for bar, val in zip(bars, gaps):
                ax2.text(bar.get_x() + bar.get_width()/2,
                         val + (0.02 if val >= 0 else -0.05),
                         f"{val:+.3f}s", ha="center", fontsize=9, color="white")
            ax2.set_xticks(yrs)
            ax2.set_xlabel("Year", color="white")
            ax2.set_ylabel("Gap vs Teammate (s)", color="white")
            ax2.set_title("vs Teammate — green=driver faster", color="white")
            ax2.tick_params(colors="white"); ax2.grid(True, axis="y", alpha=0.3)
        else:
            ax2.text(0.5, 0.5, "No teammate gap data", ha="center", va="center",
                     transform=ax2.transAxes, color="white")
            ax2.axis("off")

        fig.suptitle(f"{driver} at {gp} — Multi-Season", color="white", fontsize=13)
        fig.tight_layout()
        st.pyplot(fig); plt.close(fig)

    # ── Mode 2: Head-to-head ──────────────────────────────────────────
    elif mode == "Head-to-Head Across Seasons":
        years = [int(y) for y in years_input.split()]
        with st.spinner(f"Comparing {driver_a} vs {driver_b} at {gp}..."):
            df = compare_two_drivers_across_seasons(driver_a, driver_b, years, gp, session_type)

        if df.empty:
            st.error("No data found.")
            st.stop()

        st.dataframe(df, use_container_width=True)

        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        fig.patch.set_facecolor("#0f0f0f")
        for ax in axes: ax.set_facecolor("#0f0f0f")

        col_a = f"{driver_a}_BestLap"
        col_b = f"{driver_b}_BestLap"
        ax = axes[0]
        ax.plot(df["Year"], df[col_a], marker="o", color="#3671C6", linewidth=2.5,
                markersize=8, label=driver_a)
        ax.plot(df["Year"], df[col_b], marker="s", color="#E8002D", linewidth=2.5,
                markersize=8, label=driver_b)
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
            ax2.text(bar.get_x() + bar.get_width()/2,
                     val + (0.02 if val >= 0 else -0.06),
                     f"{val:+.3f}s\n({faster})", ha="center", fontsize=8, color="white")
        ax2.set_xticks(df["Year"]); ax2.set_xlabel("Year", color="white")
        ax2.set_ylabel(f"Gap: {driver_a} − {driver_b} (s)", color="white")
        ax2.set_title(f"green={driver_a} faster  red={driver_b} faster", color="white")
        ax2.tick_params(colors="white"); ax2.grid(True, axis="y", alpha=0.3)

        fig.suptitle(f"{driver_a} vs {driver_b} at {gp}", color="white", fontsize=13)
        fig.tight_layout()
        st.pyplot(fig); plt.close(fig)

    # ── Mode 3: Circuit heatmap ───────────────────────────────────────
    else:
        n_rounds = int(max_rounds) if max_rounds > 0 else None
        with st.spinner(f"Loading {driver}'s {year} season ({session_type})..."):
            df = driver_circuit_heatmap_data(driver, int(year), session_type, n_rounds)

        if df.empty:
            st.error("No data found.")
            st.stop()

        st.dataframe(df, use_container_width=True)

        df_sorted  = df.sort_values("Round")
        gaps       = df_sorted["GapToSessionBest"].values
        circuits   = [c.replace(" Grand Prix", "") for c in df_sorted["Circuit"]]
        bar_colors = ["#27AE60" if g <= 0.001 else "#F39C12" if g <= 0.3 else "#E74C3C"
                      for g in gaps]

        fig, ax = plt.subplots(figsize=(max(12, len(circuits) * 0.75), 5))
        fig.patch.set_facecolor("#0f0f0f"); ax.set_facecolor("#0f0f0f")
        bars = ax.bar(range(len(circuits)), gaps, color=bar_colors, width=0.7)
        for bar, val in zip(bars, gaps):
            ax.text(bar.get_x() + bar.get_width()/2, val + 0.005,
                    "POLE" if val <= 0.001 else f"+{val:.3f}s",
                    ha="center", va="bottom", fontsize=7, color="white", rotation=45)
        ax.set_xticks(range(len(circuits)))
        ax.set_xticklabels(circuits, fontsize=8, rotation=45, ha="right", color="white")
        ax.set_ylabel("Gap to Session Fastest (s)", color="white")
        ax.set_title(
            f"{driver} — Gap to Session Best — {year} ({session_type})\n"
            "green = pole/fastest  orange = within 0.3s  red = further back",
            color="white",
        )
        ax.tick_params(colors="white"); ax.grid(True, axis="y", alpha=0.3)
        fig.tight_layout()
        st.pyplot(fig); plt.close(fig)