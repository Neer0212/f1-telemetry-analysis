import sys
from pathlib import Path
import pandas as pd
import streamlit as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# 1. Setup & Imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
st.set_page_config(page_title="Championship · F1 Analytics", page_icon="🏆", layout="wide", initial_sidebar_state="collapsed")

from f1_analysis.visualization.ui_theme import inject_f1_css, top_nav, page_header, control_panel, section_label, metrics_row
from f1_analysis.core.season import build_driver_standings_progression, build_team_standings_progression
from f1_analysis.visualization.style import apply_f1_style
from f1_analysis.visualization.plots import plot_championship_progression

inject_f1_css()
top_nav("Championship")
page_header("🏆", "Season Analysis", "Championship Progression",
            "Round-by-round points accumulation for the Drivers' and Constructors' Championships.")

# Custom HTML for explanations and dynamic insights (from Code 1)
EXPLAIN = """
<div style="background:#141414;border:1px solid #2A2A2A;border-left:3px solid #E8002D;
padding:.9rem 1.2rem;margin:.8rem 0 1.2rem;color:#aaa;font-size:.88rem;line-height:1.65;
font-family:'Inter',sans-serif;">
{text}
</div>"""

INSIGHT = """
<div style="background:#0D0D0D;border:1px solid #2A2A2A;border-top:2px solid #E8002D;
padding:1rem 1.3rem;margin-top:1rem;font-family:'Inter',sans-serif;">
<div style="font-family:'Titillium Web',sans-serif;font-size:.65rem;font-weight:700;
text-transform:uppercase;letter-spacing:.2em;color:#E8002D;margin-bottom:.6rem;">Key Insights</div>
<div style="color:#ccc;font-size:.88rem;font-family:'Inter',sans-serif;">
{text}
</div>
</div>"""

# 2. UI Control Panel (from Code 2)
clicked, vals = control_panel([
    {"type":"number","label":"Year","key":"champ_year","default":2024,"min":2018,"max":2026},
    {"type":"number","label":"Top N Drivers","key":"champ_topn","default":10,"min":3,"max":20},
], button_label="Build Standings", cols_per_row=3)

if clicked:
    year = vals["champ_year"]
    top_n = vals["champ_topn"]
    
    with st.spinner(f"Fetching {year} season standings — this downloads one round at a time..."):
        apply_f1_style()
        try:
            driver_standings = build_driver_standings_progression(year)
            team_standings   = build_team_standings_progression(year)
        except Exception as e:
            st.error(f"Could not fetch standings: {e}")
            st.stop()

    if driver_standings.empty:
        st.warning("No standings data found for this year.")
        st.stop()

    # Data Processing for Hero Stats
    final_round   = driver_standings["Round"].max()
    final_drivers = driver_standings[driver_standings["Round"] == final_round].sort_values("Points", ascending=False)
    leader        = final_drivers.iloc[0]
    second        = final_drivers.iloc[1] if len(final_drivers) > 1 else None
    gap_to_second = (leader["Points"] - second["Points"]) if second is not None else 0
    leader_name   = leader.get("DriverCode", str(leader.iloc[0]))

    # 3. Dynamic Metrics Row
    metrics_row([
        {"label": "Championship Leader", "value": leader_name, "color": "accent"},
        {"label": "Leader's Points", "value": f"{int(leader['Points'])}"},
        {"label": "Gap to P2", "value": f"+{int(gap_to_second)} pts" if gap_to_second else "—", "color": "gold"},
        {"label": "Rounds Completed", "value": str(int(final_round))},
    ])

    st.markdown('<div style="padding:0 2.5rem 4rem;">', unsafe_allow_html=True)

    # ── CHART 1: DRIVERS' CHAMPIONSHIP ──
    section_label("🧑‍🏎️ Drivers' Championship Progression")
    st.markdown(EXPLAIN.format(text="""
    <strong>What this chart shows:</strong> Each line represents one driver's <strong>cumulative points total</strong> after each race weekend. 
    A <strong>steep upward jump</strong> = a race win or podium (25, 18, 15 points). 
    A <strong>flat section</strong> = a retirement, poor result, or points finish just outside the top 10. 
    Lines that cross = a driver overtook another in the standings.
    """), unsafe_allow_html=True)

    fig1 = plot_championship_progression(
        driver_standings, entity_column="DriverCode", top_n=top_n, title=f"{year} Drivers' Championship"
    )
    if fig1:
        st.pyplot(fig1, use_container_width=True)
        plt.close(fig1)

    # Dynamic Insight: Drivers
    top3 = final_drivers.head(3)
    insight_lines = []
    for i, (_, row) in enumerate(top3.iterrows()):
        code = row.get("DriverCode", row.get("Driver", "?"))
        insight_lines.append(f"<li><strong>P{i+1}: {code}</strong> — {int(row['Points'])} points</li>")

    driver_standings["PointsDiff"] = driver_standings.groupby("DriverCode" if "DriverCode" in driver_standings.columns else "Driver")["Points"].diff().fillna(driver_standings["Points"])
    best_round_row = driver_standings.loc[driver_standings["PointsDiff"].idxmax()]
    best_driver_col = "DriverCode" if "DriverCode" in best_round_row.index else "Driver"

    st.markdown(INSIGHT.format(text=f"""
    <h4 style="color:#fff;margin:.3rem 0;">🔍 Season story</h4>
    <ul style="margin:.4rem 0;padding-left:1.2rem;line-height:1.8;">
        {''.join(insight_lines)}
        <li>Biggest single-round points haul: <strong>{best_round_row[best_driver_col]}</strong> scored <strong>{int(best_round_row['PointsDiff'])} points</strong> in Round {int(best_round_row['Round'])} — likely a dominant win with fastest lap bonus or a Sprint weekend sweep.</li>
        <li>Points are awarded: 25-18-15-12-10-8-6-4-2-1 for P1 through P10. An extra point is awarded for the fastest lap if the driver finishes in the top 10.</li>
    </ul>
    """), unsafe_allow_html=True)

    # ── CHART 2: CONSTRUCTORS' CHAMPIONSHIP ──
    section_label("🏭 Constructors' Championship Progression")
    st.markdown(EXPLAIN.format(text="""
    <strong>What this chart shows:</strong> Same as above but for <strong>teams</strong> (constructors). Each team's points are the combined total of both their drivers. 
    This is why a team with two strong drivers can dominate even if one driver occasionally underperforms — both cars score points. 
    The constructors' title determines prize money and prestige for the team.
    """), unsafe_allow_html=True)

    fig2 = plot_championship_progression(
        team_standings, entity_column="Constructor", title=f"{year} Constructors' Championship"
    )
    if fig2:
        st.pyplot(fig2, use_container_width=True)
        plt.close(fig2)

    # ── FINAL STANDINGS TABLES ──
    final_teams = team_standings[team_standings["Round"] == team_standings["Round"].max()].sort_values("Points", ascending=False)
    
    st.markdown("---")
    section_label("📋 Final Standings Tables")
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("#### Drivers")
        top_drivers = final_drivers[["DriverCode","Points","Position"]].head(top_n).copy() if "DriverCode" in final_drivers.columns else final_drivers.head(top_n)
        st.dataframe(top_drivers, use_container_width=True, hide_index=True)

    with col_b:
        st.markdown("#### Constructors")
        st.dataframe(final_teams[["Constructor","Points","Position"]], use_container_width=True, hide_index=True)

    st.markdown('</div>', unsafe_allow_html=True)

else:
    st.markdown('<div style="padding:5rem 2.5rem;text-align:center;font-family:\'Titillium Web\',sans-serif;font-size:0.8rem;text-transform:uppercase;letter-spacing:0.15em;color:#2A2A2A;">Select a season year above and press Build Standings</div>', unsafe_allow_html=True)