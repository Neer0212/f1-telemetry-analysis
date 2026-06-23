import streamlit as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from f1_analysis.core.season import build_driver_standings_progression, build_team_standings_progression
from f1_analysis.visualization.style import apply_f1_style
from f1_analysis.visualization.plots import plot_championship_progression

st.set_page_config(page_title="Championship", page_icon="🏆", layout="wide")
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
    <h1>🏆 Season Championship</h1>
    <p>Round-by-round points progression for drivers and constructors — watch the title fight evolve.</p>
</div>""", unsafe_allow_html=True)

st.sidebar.header("Settings")
year  = st.sidebar.number_input("Year", 2018, 2026, 2024)
top_n = st.sidebar.slider("Top N Drivers to Show", 3, 20, 10)
st.sidebar.caption("Data is fetched from the Ergast API — one call per race round. May take 1–2 minutes for a full season.")

if st.sidebar.button("Build Standings", type="primary"):
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

    # ── Hero stats ────────────────────────────────────────────────
    final_round    = driver_standings["Round"].max()
    final_drivers  = driver_standings[driver_standings["Round"] == final_round].sort_values("Points", ascending=False)
    leader         = final_drivers.iloc[0]
    second         = final_drivers.iloc[1] if len(final_drivers) > 1 else None
    gap_to_second  = (leader["Points"] - second["Points"]) if second is not None else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Championship Leader", leader["DriverCode"] if "DriverCode" in leader else str(leader.iloc[0]))
    c2.metric("Leader's Points", f"{int(leader['Points'])}")
    c3.metric("Gap to P2", f"+{int(gap_to_second)} pts" if gap_to_second else "—")
    c4.metric("Rounds Completed", int(final_round))

    # ════════════════════════════════════════════════════════════
    # DRIVERS' CHAMPIONSHIP
    # ════════════════════════════════════════════════════════════
    st.markdown("---")
    st.subheader("🧑‍🏎️ Drivers' Championship Progression")
    st.markdown("""<div class="explain-box">
    <strong>What this chart shows:</strong> Each line represents one driver's
    <strong>cumulative points total</strong> after each race weekend.
    A <strong>steep upward jump</strong> = a race win or podium (25, 18, 15 points).
    A <strong>flat section</strong> = a retirement, poor result, or points finish just outside the top 10.
    Lines that cross = a driver overtook another in the standings.
    The gap between the top line and the rest shows how dominant the championship leader has been.
    </div>""", unsafe_allow_html=True)

    fig = plot_championship_progression(
        driver_standings, entity_column="DriverCode",
        top_n=top_n, title=f"{year} Drivers' Championship",
    )
    st.pyplot(fig); plt.close(fig)

    # Key insight
    top3 = final_drivers.head(3)
    insight_lines = []
    for i, (_, row) in enumerate(top3.iterrows()):
        code = row.get("DriverCode", row.get("Driver", "?"))
        insight_lines.append(f"<li><strong>P{i+1}: {code}</strong> — {int(row['Points'])} points</li>")

    # Biggest single-round gain
    driver_standings["PointsDiff"] = driver_standings.groupby(
        "DriverCode" if "DriverCode" in driver_standings.columns else "Driver"
    )["Points"].diff().fillna(driver_standings["Points"])
    best_round_row = driver_standings.loc[driver_standings["PointsDiff"].idxmax()]
    best_driver_col = "DriverCode" if "DriverCode" in best_round_row.index else "Driver"

    st.markdown(f"""<div class="insight-box"><h4>🔍 Season story</h4><ul>
    {''.join(insight_lines)}
    <li>Biggest single-round points haul: <strong>{best_round_row[best_driver_col]}</strong>
    scored <strong>{int(best_round_row['PointsDiff'])} points</strong> in Round {int(best_round_row['Round'])}
    — likely a dominant win with fastest lap bonus.</li>
    <li>Points are awarded: 25-18-15-12-10-8-6-4-2-1 for P1 through P10.
    An extra point is awarded for the fastest lap if the driver finishes in the top 10.</li>
    </ul></div>""", unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════
    # CONSTRUCTORS' CHAMPIONSHIP
    # ════════════════════════════════════════════════════════════
    st.markdown("---")
    st.subheader("🏭 Constructors' Championship Progression")
    st.markdown("""<div class="explain-box">
    <strong>What this chart shows:</strong> Same as above but for <strong>teams</strong>
    (constructors). Each team's points are the combined total of both their drivers.
    This is why a team with two strong drivers (like Red Bull in 2023) can dominate
    even if one driver occasionally underperforms — both cars score points.
    The constructors' title determines prize money and prestige for the team.
    </div>""", unsafe_allow_html=True)

    fig = plot_championship_progression(
        team_standings, entity_column="Constructor",
        title=f"{year} Constructors' Championship",
    )
    st.pyplot(fig); plt.close(fig)

    # Team standings table
    final_teams = team_standings[team_standings["Round"] == team_standings["Round"].max()].sort_values("Points", ascending=False)
    st.markdown("---")
    st.subheader("📋 Final Standings Tables")
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("#### Drivers")
        top_drivers = final_drivers[["DriverCode","Points","Position"]].head(top_n).copy() if "DriverCode" in final_drivers.columns else final_drivers.head(top_n)
        st.dataframe(top_drivers, use_container_width=True, hide_index=True)

    with col_b:
        st.markdown("#### Constructors")
        st.dataframe(final_teams[["Constructor","Points","Position"]], use_container_width=True, hide_index=True)