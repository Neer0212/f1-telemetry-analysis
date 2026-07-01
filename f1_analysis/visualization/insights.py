"""Per-chart insight text generators. Pure ASCII only."""
import pandas as pd
from f1_analysis.visualization.ui_theme import insight_box


def fmt_s(seconds):
    if pd.isna(seconds):
        return "N/A"
    m = int(seconds // 60)
    s = seconds % 60
    return "{}:{:06.3f}".format(m, s)


def lap_distribution_insight(session, drivers, session_type):
    laps = session.laps
    driver_data = []
    for d in drivers:
        dl = laps.pick_drivers(d)
        times = dl["LapTime"].dt.total_seconds().dropna()
        if not times.empty:
            driver_data.append((d, times.min(), times.mean(), times.std()))
    if not driver_data:
        return
    driver_data.sort(key=lambda x: x[1])
    fastest_drv, fastest_t = driver_data[0][0], driver_data[0][1]
    spread = driver_data[-1][1] - driver_data[0][1] if len(driver_data) > 1 else 0

    body = (
        "Each box shows the spread of every lap time for that driver. The narrower and lower the box, "
        "the more consistent and quick they were. Outlier dots above the box are usually slow laps caused "
        "by traffic, pit stops, or safety cars, and do not reflect true race pace.<br><br>"
        "<b>" + fastest_drv + "</b> posted the quickest individual lap at <b>" + fmt_s(fastest_t) + "</b>. "
    )
    if spread > 0:
        desc = ("a razor-thin margin." if spread < 0.3
                else "a tight but meaningful gap." if spread < 0.8
                else "a substantial difference in pace.")
        body += "The gap from fastest to slowest driver in this group is <b>{:.3f}s</b>, {}".format(spread, desc)
    insight_box("D", "Reading the Lap Time Distribution", body)


def race_pace_insight(session, drivers):
    laps = session.laps
    avgs = {}
    for d in drivers:
        times = laps.pick_drivers(d)["LapTime"].dt.total_seconds().dropna()
        if not times.empty:
            avgs[d] = (times.mean(), times.std())
    if not avgs:
        return
    ranked = sorted(avgs.items(), key=lambda x: x[1][0])
    leader_avg = ranked[0][1][0]
    body = (
        "Race pace strips out qualifying heroics and shows who can sustain fast laps consistently over a stint. "
        "A flat line means consistent pace. A rising line means tyre degradation is setting in.<br><br>"
        "<b>Pace ranking (average clean lap):</b><br>"
    )
    for i, (drv, (avg, std)) in enumerate(ranked):
        rank = "1st" if i == 0 else "2nd" if i == 1 else "3rd" if i == 2 else str(i + 1) + "th"
        gap = " (+{:.3f}s)".format(avg - leader_avg) if i > 0 else ""
        body += "&nbsp;&nbsp;<b>{} {}</b> - {} avg, +/-{:.3f}s consistency{}<br>".format(rank, drv, fmt_s(avg), std, gap)
    insight_box("R", "Reading the Race Pace Chart", body)


def tyre_strategy_insight(session, drivers, session_type):
    laps = session.laps
    lines = []
    for d in drivers:
        dl = laps.pick_drivers(d)
        stints = dl.groupby("Stint").agg(Compound=("Compound", "first"), Laps=("LapNumber", "count")).reset_index()
        if stints.empty:
            continue
        parts = []
        for _, row in stints.iterrows():
            c = str(row["Compound"]).upper()
            parts.append("{}({}L)".format(c[:1], row["Laps"]))
        lines.append("<b>{}:</b> {}".format(d, " -> ".join(parts)))

    if session_type == "R":
        body = (
            "Each segment is one tyre stint. S = Soft, M = Medium, H = Hard, I = Intermediate. "
            "The number in brackets is how many laps that set was used. A one-stop strategy saves pit-lane "
            "time but risks more tyre wear late on. A two-stop costs roughly 20 seconds in the pits but gives "
            "fresher rubber each stint.<br><br>" + "<br>".join(lines)
        )
    else:
        body = (
            "In Qualifying, drivers typically run Soft tyres for maximum grip on their fastest lap attempt. "
            "Teams manage how many new sets are saved from Q1 and Q2 for the race start on Sunday."
        )
    insight_box("T", "Reading the Tyre Strategy Chart", body)