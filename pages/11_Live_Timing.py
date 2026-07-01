import streamlit as st
import sys, time, requests
from pathlib import Path
from datetime import datetime
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
st.set_page_config(page_title="Live Timing - F1 Analytics", page_icon="F1", layout="wide", initial_sidebar_state="collapsed")
from f1_analysis.visualization.ui_theme import inject_f1_css, top_nav, page_header, section_label, insight_box
inject_f1_css()
top_nav("Live")

BASE = "https://api.openf1.org/v1"
COMPOUND_COLOR = {"SOFT":"#DA291C","MEDIUM":"#FFD700","HARD":"#E8E8E8","INTERMEDIATE":"#43B02A","WET":"#0067AD","UNKNOWN":"#888888"}
FLAG_COLOR = {"GREEN":"#27AE60","YELLOW":"#FFD700","RED":"#E8002D","SC":"#FF8C00","VSC":"#FF8C00","CLEAR":"#27AE60","CHEQUERED":"#FFFFFF"}

def openf1(endpoint, **params):
    try:
        r = requests.get(BASE + "/" + endpoint, params=params, timeout=8)
        r.raise_for_status()
        return r.json()
    except Exception:
        return []

def fmt_lap(s):
    if s is None or pd.isna(s): return "-"
    try:
        s = float(s); m = int(s // 60); sec = s % 60
        return "{}:{:06.3f}".format(m, sec)
    except Exception:
        return "-"

def fmt_gap(g):
    if g is None: return "-"
    try:
        v = float(g)
        return "+{:.3f}s".format(v) if v > 0 else "Leader"
    except Exception:
        return str(g)[:8]

page_header("L", "Live Timing", "Race Control Tower",
    "Live timing during race weekends. Historical replay anytime. Powered by OpenF1 API.")

# -- Inline control panel --
st.markdown('<div style="background:#1C1C1C;border-bottom:2px solid #2A2A2A;padding:1.5rem 2.5rem;">', unsafe_allow_html=True)
c1, c2, c3, c4, c5 = st.columns([1.3, 1, 1, 1, 1])
with c1:
    mode = st.radio("Mode", ["Live (current session)", "Historical race"], index=0, horizontal=True)
use_live = mode.startswith("Live")
with c2:
    hist_year = st.number_input("Year", 2023, 2025, 2024, disabled=use_live)
with c3:
    hist_gp = st.text_input("Grand Prix name", "Abu Dhabi", disabled=use_live)
with c4:
    auto_refresh = st.toggle("Auto-refresh (5s)", value=True)
with c5:
    manual_key = st.text_input("Session key override (optional)", value="")
st.markdown('</div>', unsafe_allow_html=True)

@st.cache_data(ttl=30)
def get_latest_session():
    sessions = openf1("sessions", year=2026)
    if not sessions:
        sessions = openf1("sessions")
    if not sessions:
        return None
    def parse_date(s):
        d = str(s.get("date_start","1970-01-01"))[:19]
        try: return datetime.fromisoformat(d)
        except Exception: return datetime.min
    return sorted(sessions, key=parse_date, reverse=True)[0]

@st.cache_data(ttl=300)
def get_historical_session(year, gp_name):
    sessions = openf1("sessions", year=year)
    matches = []
    for s in sessions:
        name_match = (
            gp_name.lower() in str(s.get("circuit_short_name","")).lower() or
            gp_name.lower() in str(s.get("meeting_name","")).lower() or
            gp_name.lower() in str(s.get("location","")).lower() or
            gp_name.lower() in str(s.get("country_name","")).lower()
        )
        if name_match and s.get("session_type") == "Race":
            matches.append(s)
    if matches:
        return matches[-1]
    races = [s for s in sessions if s.get("session_type") == "Race"]
    if races:
        def parse_date(s):
            d = str(s.get("date_start","1970-01-01"))[:19]
            try: return datetime.fromisoformat(d)
            except Exception: return datetime.min
        return sorted(races, key=parse_date)[-1]
    return None

if manual_key.strip():
    session = {"session_key": int(manual_key.strip()), "meeting_name": "Manual Session",
               "session_type": "", "circuit_short_name": "", "date_start": ""}
elif use_live:
    session = get_latest_session()
else:
    with st.spinner("Finding session..."):
        session = get_historical_session(hist_year, hist_gp)

if not session:
    st.error("Could not find a session. OpenF1 may be rate-limiting, try again in a moment.")
    st.stop()

session_key  = session["session_key"]
meeting_name = session.get("meeting_name","Unknown")
session_type = session.get("session_type","")
circuit      = session.get("circuit_short_name","")
date_start   = session.get("date_start","")[:10]

status_color = "#27AE60" if use_live else "#3671C6"
status_text  = "LIVE" if use_live else "HISTORICAL"
st.markdown(
    '<div style="display:flex;align-items:center;gap:2rem;background:#1C1C1C;'
    'border-bottom:1px solid #2A2A2A;padding:0.9rem 2.5rem;flex-wrap:wrap;">'
    '<div><div style="font-family:Titillium Web,sans-serif;font-size:0.6rem;font-weight:700;'
    'text-transform:uppercase;letter-spacing:0.18em;color:#555;">Session</div>'
    '<div style="font-family:Titillium Web,sans-serif;font-size:1rem;font-weight:800;color:#FFF;">'
    + meeting_name + ' - ' + session_type + '</div></div>'
    '<div><div style="font-family:Titillium Web,sans-serif;font-size:0.6rem;font-weight:700;'
    'text-transform:uppercase;letter-spacing:0.18em;color:#555;">Circuit</div>'
    '<div style="font-family:Titillium Web,sans-serif;font-size:1rem;font-weight:700;color:#FFF;">' + circuit + '</div></div>'
    '<div><div style="font-family:Titillium Web,sans-serif;font-size:0.6rem;font-weight:700;'
    'text-transform:uppercase;letter-spacing:0.18em;color:#555;">Date</div>'
    '<div style="font-family:Titillium Web,sans-serif;font-size:1rem;font-weight:700;color:#FFF;">' + date_start + '</div></div>'
    '<div style="margin-left:auto;"><div style="font-family:Titillium Web,sans-serif;font-size:0.72rem;font-weight:800;'
    'color:' + status_color + ';letter-spacing:0.12em;">' + status_text + '</div>'
    '<div style="font-family:Inter,sans-serif;font-size:0.65rem;color:#555;">Session key: ' + str(session_key) + '</div></div></div>',
    unsafe_allow_html=True
)

with st.spinner("Fetching timing data..."):
    positions    = openf1("position", session_key=session_key)
    intervals    = openf1("intervals", session_key=session_key)
    laps         = openf1("laps", session_key=session_key)
    pit_stops    = openf1("pit", session_key=session_key)
    race_control = openf1("race_control", session_key=session_key)
    drivers      = openf1("drivers", session_key=session_key)
    stints       = openf1("stints", session_key=session_key)

driver_map = {d["driver_number"]: d for d in drivers}
latest_pos, latest_int, latest_lap, latest_stint = {}, {}, {}, {}
for p in positions:
    dn = p["driver_number"]
    if dn not in latest_pos or p["date"] > latest_pos[dn]["date"]: latest_pos[dn] = p
for i in intervals:
    dn = i["driver_number"]
    if dn not in latest_int or i["date"] > latest_int[dn]["date"]: latest_int[dn] = i
for l in laps:
    dn = l["driver_number"]
    if dn not in latest_lap or l.get("lap_number",0) > latest_lap[dn].get("lap_number",0): latest_lap[dn] = l
for s in stints:
    dn = s["driver_number"]
    if dn not in latest_stint or s.get("stint_number",0) > latest_stint[dn].get("stint_number",0): latest_stint[dn] = s

tower_rows = []
for dn, pos in latest_pos.items():
    drv = driver_map.get(dn, {}); ivl = latest_int.get(dn, {}); lap = latest_lap.get(dn, {}); stnt = latest_stint.get(dn, {})
    compound = str(stnt.get("compound","UNKNOWN")).upper()
    tower_rows.append({
        "pos": pos.get("position", 99), "number": dn, "code": drv.get("name_acronym", str(dn)),
        "team": drv.get("team_name",""), "color": "#" + drv.get("team_colour","888888"),
        "gap": ivl.get("gap_to_leader"), "interval": ivl.get("interval"),
        "lap_time": lap.get("lap_duration"), "lap_num": lap.get("lap_number",0),
        "s1": lap.get("duration_sector_1"), "s2": lap.get("duration_sector_2"), "s3": lap.get("duration_sector_3"),
        "compound": compound, "pit_count": sum(1 for p in pit_stops if p["driver_number"]==dn),
    })
tower_rows.sort(key=lambda x: x["pos"])

section_label("Timing Tower")
st.markdown(
    '<div style="display:grid;grid-template-columns:40px 50px 160px 180px 100px 100px 80px 80px 80px 80px 60px;'
    'gap:0;background:#1C1C1C;border-bottom:2px solid #E8002D;padding:0.45rem 2.5rem;'
    'font-family:Titillium Web,sans-serif;font-size:0.58rem;font-weight:700;text-transform:uppercase;letter-spacing:0.12em;color:#555;">'
    '<div>POS</div><div>NO</div><div>DRIVER</div><div>TEAM</div><div>GAP</div><div>INTERVAL</div>'
    '<div>LAST LAP</div><div>S1</div><div>S2</div><div>S3</div><div>TYRE</div></div>',
    unsafe_allow_html=True
)

if not tower_rows:
    st.markdown('<div style="padding:3rem 2.5rem;text-align:center;font-family:Titillium Web,sans-serif;'
        'font-size:0.8rem;text-transform:uppercase;letter-spacing:0.15em;color:#333;">'
        'No timing data available for this session yet.</div>', unsafe_allow_html=True)
else:
    for i, row in enumerate(tower_rows):
        bg = "#141414" if i % 2 == 0 else "#111111"
        ccolor = COMPOUND_COLOR.get(row["compound"], "#888")
        pos_color = "#FFD700" if row["pos"]==1 else "#FFFFFF"
        st.markdown(
            '<div style="display:grid;grid-template-columns:40px 50px 160px 180px 100px 100px 80px 80px 80px 80px 60px;'
            'gap:0;background:' + bg + ';border-bottom:1px solid #1A1A1A;padding:0.6rem 2.5rem;align-items:center;'
            'border-left:3px solid ' + row["color"] + ';">'
            '<div style="font-family:Titillium Web,sans-serif;font-size:1rem;font-weight:900;color:' + pos_color + ';">' + str(row["pos"]) + '</div>'
            '<div style="font-family:Titillium Web,sans-serif;font-size:0.75rem;font-weight:700;color:#555;">' + str(row["number"]) + '</div>'
            '<div><div style="font-family:Titillium Web,sans-serif;font-size:0.82rem;font-weight:800;color:#FFF;">' + row["code"] + '</div>'
            '<div style="font-family:Inter,sans-serif;font-size:0.65rem;color:#555;">Lap ' + str(row["lap_num"]) + ' - ' + str(row["pit_count"]) + ' stop(s)</div></div>'
            '<div style="font-family:Inter,sans-serif;font-size:0.72rem;color:#888;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">' + row["team"] + '</div>'
            '<div style="font-family:Titillium Web,sans-serif;font-size:0.8rem;font-weight:700;color:#E8002D;">' + fmt_gap(row["gap"]) + '</div>'
            '<div style="font-family:Titillium Web,sans-serif;font-size:0.8rem;font-weight:700;color:#888;">' + fmt_gap(row["interval"]) + '</div>'
            '<div style="font-family:Titillium Web,sans-serif;font-size:0.8rem;font-weight:700;color:#27F4D2;">' + fmt_lap(row["lap_time"]) + '</div>'
            '<div style="font-family:Titillium Web,sans-serif;font-size:0.75rem;color:#E8002D;">' + fmt_lap(row["s1"]) + '</div>'
            '<div style="font-family:Titillium Web,sans-serif;font-size:0.75rem;color:#FFD700;">' + fmt_lap(row["s2"]) + '</div>'
            '<div style="font-family:Titillium Web,sans-serif;font-size:0.75rem;color:#27F4D2;">' + fmt_lap(row["s3"]) + '</div>'
            '<div style="display:flex;align-items:center;gap:4px;"><div style="width:10px;height:10px;border-radius:50%;background:' + ccolor + ';"></div>'
            '<div style="font-family:Titillium Web,sans-serif;font-size:0.62rem;font-weight:700;color:' + ccolor + ';">' + row["compound"][:1] + '</div></div></div>',
            unsafe_allow_html=True
        )

section_label("Race Control Messages")
recent_rc = sorted(race_control, key=lambda x: x.get("date",""), reverse=True)[:15]
if not recent_rc:
    st.markdown('<div style="padding:1.5rem 2.5rem;font-family:Inter,sans-serif;font-size:0.8rem;color:#333;">No race control messages.</div>', unsafe_allow_html=True)
else:
    for msg in recent_rc:
        flag = str(msg.get("flag","")).upper()
        category = str(msg.get("category",""))
        message = str(msg.get("message",""))
        lap_num = msg.get("lap_number","")
        date_str = str(msg.get("date",""))[:19].replace("T"," ")
        fc = FLAG_COLOR.get(flag, FLAG_COLOR.get(category.upper(), "#888888"))
        st.markdown(
            '<div style="display:flex;gap:1rem;background:#141414;border-left:3px solid ' + fc + ';'
            'border-bottom:1px solid #1A1A1A;padding:0.65rem 2.5rem;">'
            '<div style="flex:1;"><div style="font-family:Inter,sans-serif;font-size:0.8rem;color:#CCC;">' + message + '</div>'
            '<div style="font-family:Inter,sans-serif;font-size:0.65rem;color:#555;margin-top:0.2rem;">' + date_str +
            (' - Lap ' + str(lap_num) if lap_num else '') + (' - ' + flag if flag else '') + '</div></div></div>',
            unsafe_allow_html=True
        )

section_label("Pit Stop Log")
if not pit_stops:
    st.markdown('<div style="padding:1.5rem 2.5rem;font-family:Inter,sans-serif;font-size:0.8rem;color:#333;">No pit stops recorded yet.</div>', unsafe_allow_html=True)
else:
    sorted_pits = sorted(pit_stops, key=lambda x: x.get("date",""), reverse=True)
    for pit in sorted_pits[:15]:
        dn = pit["driver_number"]; drv = driver_map.get(dn, {})
        code = drv.get("name_acronym", str(dn)); color = "#" + drv.get("team_colour","888888")
        dur = pit.get("pit_duration"); dur_str = "{:.2f}s".format(dur) if dur else "-"
        lap = pit.get("lap_number","-")
        st.markdown(
            '<div style="display:grid;grid-template-columns:40px 80px 1fr;gap:0;background:#141414;'
            'border-bottom:1px solid #1A1A1A;border-left:3px solid ' + color + ';padding:0.55rem 2.5rem;">'
            '<div style="font-family:Titillium Web,sans-serif;font-size:0.8rem;font-weight:700;color:#888;">L' + str(lap) + '</div>'
            '<div style="font-family:Titillium Web,sans-serif;font-size:0.85rem;font-weight:800;color:#FFF;">' + code + '</div>'
            '<div style="font-family:Titillium Web,sans-serif;font-size:0.85rem;font-weight:700;color:#27F4D2;">' + dur_str + '</div></div>',
            unsafe_allow_html=True
        )

st.markdown('<div style="padding:0 2.5rem;">', unsafe_allow_html=True)
insight_box("I", "How to Read the Timing Tower",
    "POS = current race position. GAP = total time behind the race leader. INTERVAL = gap to the car directly ahead. "
    "S1/S2/S3 = the three sector times of the most recent lap. The coloured dot shows tyre compound. "
    "The left-side coloured bar is the driver's team colour.")
st.markdown('</div>', unsafe_allow_html=True)

col1, col2 = st.columns([3,1])
with col2:
    if st.button("Refresh Now", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.markdown(
    '<div style="padding:1rem 2.5rem 2rem;font-family:Inter,sans-serif;font-size:0.68rem;color:#333;">'
    'Last updated: ' + datetime.now().strftime("%H:%M:%S") + ' - Data: OpenF1 API - Session key: ' + str(session_key) + '</div>',
    unsafe_allow_html=True
)

if auto_refresh:
    time.sleep(5)
    st.rerun()