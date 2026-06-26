import streamlit as st
import sys, time, requests
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
st.set_page_config(
    page_title="Live Timing · F1 Analytics",
    page_icon="🔴",
    layout="wide",
)
from f1_analysis.visualization.ui_theme import inject_f1_css
inject_f1_css()

# ── OpenF1 base URL ────────────────────────────────────────────────────────────
BASE = "https://api.openf1.org/v1"

# ── Compound colours ───────────────────────────────────────────────────────────
COMPOUND_COLOR = {
    "SOFT":"#DA291C","MEDIUM":"#FFD700","HARD":"#E8E8E8",
    "INTERMEDIATE":"#43B02A","WET":"#0067AD","UNKNOWN":"#888888",
}
FLAG_COLOR = {
    "GREEN":"#27AE60","YELLOW":"#FFD700","RED":"#E8002D",
    "SC":"#FF8C00","VSC":"#FF8C00","CLEAR":"#27AE60","CHEQUERED":"#FFFFFF",
}

# ── Helpers ────────────────────────────────────────────────────────────────────
def openf1(endpoint: str, **params) -> list:
    try:
        r = requests.get(f"{BASE}/{endpoint}", params=params, timeout=8)
        r.raise_for_status()
        return r.json()
    except Exception:
        return []

def fmt_lap(s) -> str:
    if s is None or pd.isna(s): return "—"
    try:
        s = float(s)
        m = int(s // 60); sec = s % 60
        return f"{m}:{sec:06.3f}"
    except Exception:
        return "—"

def fmt_gap(g) -> str:
    if g is None: return "—"
    try:
        v = float(g)
        return f"+{v:.3f}s" if v > 0 else "Leader"
    except Exception:
        return str(g)[:8]

# ── Page header ────────────────────────────────────────────────────────────────
st.markdown("""
<div style="background:#141414;border-bottom:3px solid #E8002D;padding:1.4rem 2.5rem 1.2rem;">
  <p style="font-family:'Titillium Web',sans-serif;font-size:0.65rem;font-weight:700;
             text-transform:uppercase;letter-spacing:0.25em;color:#E8002D;margin:0 0 0.25rem;">
    Live Timing
  </p>
  <h1 style="font-family:'Titillium Web',sans-serif;font-size:2.2rem;font-weight:900;
              color:#FFFFFF;margin:0;text-transform:uppercase;letter-spacing:-0.01em;">
    Race Control Tower
  </h1>
  <p style="font-family:'Inter',sans-serif;font-size:0.82rem;color:#888;margin:0.3rem 0 0;">
    Live timing during race weekends · Historical replay anytime · Powered by OpenF1 API
  </p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar controls ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔴 Live Timing Settings")

    mode = st.radio("Mode", ["🔴 Live (current session)", "📼 Historical race"],
                    index=0, help="Live uses the current F1 session. Historical lets you pick any 2023+ race.")

    if mode.startswith("📼"):
        hist_year = st.number_input("Year", 2023, 2025, 2024)
        hist_gp   = st.text_input("Grand Prix name", "Abu Dhabi")
        use_live  = False
    else:
        use_live  = True
        hist_year = None; hist_gp = None

    auto_refresh = st.toggle("Auto-refresh (5s)", value=True)
    st.markdown("---")
    st.markdown("""
<div style="font-family:'Inter',sans-serif;font-size:0.72rem;color:#555;line-height:1.6;">
  Data: <b>OpenF1 API</b><br>
  Updates ~3s behind broadcast.<br>
  Historical data: 2023 onward.<br>
  No API key required.
</div>""", unsafe_allow_html=True)

# ── Resolve session key ────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def get_latest_session() -> dict | None:
    sessions = openf1("sessions", session_type="Race")
    if not sessions: return None
    return sessions[-1]

@st.cache_data(ttl=300)
def get_historical_session(year: int, gp_name: str) -> dict | None:
    sessions = openf1("sessions", year=year)
    for s in sessions:
        if gp_name.lower() in str(s.get("circuit_short_name","")).lower() \
        or gp_name.lower() in str(s.get("meeting_name","")).lower():
            if s.get("session_type") == "Race":
                return s
    # fallback: last race session in that year
    races = [s for s in sessions if s.get("session_type") == "Race"]
    return races[-1] if races else None

if use_live:
    session = get_latest_session()
else:
    with st.spinner("Finding session…"):
        session = get_historical_session(hist_year, hist_gp)

if not session:
    st.error("Could not find a session. OpenF1 may be rate-limiting — try again in a moment.")
    st.stop()

session_key = session["session_key"]
meeting_name = session.get("meeting_name","Unknown")
session_type = session.get("session_type","")
circuit      = session.get("circuit_short_name","")
date_start   = session.get("date_start","")[:10]

# ── Session info banner ────────────────────────────────────────────────────────
status_color = "#27AE60" if use_live else "#3671C6"
status_text  = "● LIVE" if use_live else "● HISTORICAL"
st.markdown(f"""
<div style="display:flex;align-items:center;gap:2rem;background:#1C1C1C;
            border-bottom:1px solid #2A2A2A;padding:0.9rem 2.5rem;">
  <div>
    <div style="font-family:'Titillium Web',sans-serif;font-size:0.6rem;font-weight:700;
                text-transform:uppercase;letter-spacing:0.18em;color:#555;">Session</div>
    <div style="font-family:'Titillium Web',sans-serif;font-size:1rem;font-weight:800;
                color:#FFF;">{meeting_name} · {session_type}</div>
  </div>
  <div>
    <div style="font-family:'Titillium Web',sans-serif;font-size:0.6rem;font-weight:700;
                text-transform:uppercase;letter-spacing:0.18em;color:#555;">Circuit</div>
    <div style="font-family:'Titillium Web',sans-serif;font-size:1rem;font-weight:700;
                color:#FFF;">{circuit}</div>
  </div>
  <div>
    <div style="font-family:'Titillium Web',sans-serif;font-size:0.6rem;font-weight:700;
                text-transform:uppercase;letter-spacing:0.18em;color:#555;">Date</div>
    <div style="font-family:'Titillium Web',sans-serif;font-size:1rem;font-weight:700;
                color:#FFF;">{date_start}</div>
  </div>
  <div style="margin-left:auto;">
    <div style="font-family:'Titillium Web',sans-serif;font-size:0.72rem;font-weight:800;
                color:{status_color};letter-spacing:0.12em;">{status_text}</div>
    <div style="font-family:'Inter',sans-serif;font-size:0.65rem;color:#555;">
        Session key: {session_key}
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Fetch live data ────────────────────────────────────────────────────────────
with st.spinner("Fetching timing data…"):
    positions    = openf1("position",      session_key=session_key)
    intervals    = openf1("intervals",     session_key=session_key)
    laps         = openf1("laps",          session_key=session_key)
    pit_stops    = openf1("pit",           session_key=session_key)
    race_control = openf1("race_control",  session_key=session_key)
    drivers      = openf1("drivers",       session_key=session_key)
    stints       = openf1("stints",        session_key=session_key)

# ── Build timing tower data ────────────────────────────────────────────────────
driver_map = {d["driver_number"]: d for d in drivers}

# Latest position per driver
latest_pos: dict[int, dict] = {}
for p in positions:
    dn = p["driver_number"]
    if dn not in latest_pos or p["date"] > latest_pos[dn]["date"]:
        latest_pos[dn] = p

# Latest interval per driver
latest_int: dict[int, dict] = {}
for i in intervals:
    dn = i["driver_number"]
    if dn not in latest_int or i["date"] > latest_int[dn]["date"]:
        latest_int[dn] = i

# Latest lap per driver
latest_lap: dict[int, dict] = {}
for l in laps:
    dn = l["driver_number"]
    if dn not in latest_lap or l.get("lap_number",0) > latest_lap[dn].get("lap_number",0):
        latest_lap[dn] = l

# Latest stint (tyre) per driver
latest_stint: dict[int, dict] = {}
for s in stints:
    dn = s["driver_number"]
    if dn not in latest_stint or s.get("stint_number",0) > latest_stint[dn].get("stint_number",0):
        latest_stint[dn] = s

# Build tower rows
tower_rows = []
for dn, pos in latest_pos.items():
    drv  = driver_map.get(dn, {})
    ivl  = latest_int.get(dn, {})
    lap  = latest_lap.get(dn, {})
    stnt = latest_stint.get(dn, {})
    compound = str(stnt.get("compound","UNKNOWN")).upper()
    tower_rows.append({
        "pos":       pos.get("position", 99),
        "number":    dn,
        "code":      drv.get("name_acronym", str(dn)),
        "name":      drv.get("full_name", str(dn)),
        "team":      drv.get("team_name",""),
        "color":     "#" + drv.get("team_colour","888888"),
        "gap":       ivl.get("gap_to_leader"),
        "interval":  ivl.get("interval"),
        "lap_time":  lap.get("lap_duration"),
        "lap_num":   lap.get("lap_number",0),
        "s1":        lap.get("duration_sector_1"),
        "s2":        lap.get("duration_sector_2"),
        "s3":        lap.get("duration_sector_3"),
        "compound":  compound,
        "tyre_age":  stnt.get("lap_start", 0),
        "pit_count": sum(1 for p in pit_stops if p["driver_number"]==dn),
    })
tower_rows.sort(key=lambda x: x["pos"])

# ── TIMING TOWER ──────────────────────────────────────────────────────────────
st.markdown("""
<div style="font-family:'Titillium Web',sans-serif;font-size:0.65rem;font-weight:700;
            text-transform:uppercase;letter-spacing:0.2em;color:#E8002D;
            border-bottom:1px solid #2A2A2A;padding:1.5rem 2.5rem 0.5rem;">
  Timing Tower
</div>""", unsafe_allow_html=True)

# Header row
st.markdown("""
<div style="display:grid;grid-template-columns:40px 50px 160px 180px 100px 100px 80px 80px 80px 80px 60px;
            gap:0;background:#1C1C1C;border-bottom:2px solid #E8002D;
            padding:0.45rem 2.5rem;font-family:'Titillium Web',sans-serif;
            font-size:0.58rem;font-weight:700;text-transform:uppercase;
            letter-spacing:0.12em;color:#555;">
  <div>POS</div><div>NO</div><div>DRIVER</div><div>TEAM</div>
  <div>GAP</div><div>INTERVAL</div><div>LAST LAP</div>
  <div>S1</div><div>S2</div><div>S3</div><div>TYRE</div>
</div>""", unsafe_allow_html=True)

if not tower_rows:
    st.markdown("""
<div style="padding:3rem 2.5rem;text-align:center;font-family:'Titillium Web',sans-serif;
            font-size:0.8rem;text-transform:uppercase;letter-spacing:0.15em;color:#333;">
    No timing data available for this session yet.
    During a live session this will populate automatically.
</div>""", unsafe_allow_html=True)
else:
    for i, row in enumerate(tower_rows):
        bg    = "#141414" if i % 2 == 0 else "#111111"
        ccolor = COMPOUND_COLOR.get(row["compound"], "#888")
        pos_color = "#FFD700" if row["pos"]==1 else "#FFFFFF"

        st.markdown(f"""
<div style="display:grid;grid-template-columns:40px 50px 160px 180px 100px 100px 80px 80px 80px 80px 60px;
            gap:0;background:{bg};border-bottom:1px solid #1A1A1A;
            padding:0.6rem 2.5rem;align-items:center;
            border-left:3px solid {row['color']};">
  <div style="font-family:'Titillium Web',sans-serif;font-size:1rem;font-weight:900;
               color:{pos_color};">{row['pos']}</div>
  <div style="font-family:'Titillium Web',sans-serif;font-size:0.75rem;font-weight:700;
               color:#555;">{row['number']}</div>
  <div>
    <div style="font-family:'Titillium Web',sans-serif;font-size:0.82rem;font-weight:800;
                 color:#FFFFFF;">{row['code']}</div>
    <div style="font-family:'Inter',sans-serif;font-size:0.65rem;color:#555;">
        Lap {row['lap_num']} · {row['pit_count']} stop(s)
    </div>
  </div>
  <div style="font-family:'Inter',sans-serif;font-size:0.72rem;color:#888;
               white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
    {row['team']}
  </div>
  <div style="font-family:'Titillium Web',sans-serif;font-size:0.8rem;font-weight:700;
               color:#E8002D;">{fmt_gap(row['gap'])}</div>
  <div style="font-family:'Titillium Web',sans-serif;font-size:0.8rem;font-weight:700;
               color:#888;">{fmt_gap(row['interval'])}</div>
  <div style="font-family:'Titillium Web',sans-serif;font-size:0.8rem;font-weight:700;
               color:#27F4D2;">{fmt_lap(row['lap_time'])}</div>
  <div style="font-family:'Titillium Web',sans-serif;font-size:0.75rem;color:#E8002D;">
    {fmt_lap(row['s1'])}</div>
  <div style="font-family:'Titillium Web',sans-serif;font-size:0.75rem;color:#FFD700;">
    {fmt_lap(row['s2'])}</div>
  <div style="font-family:'Titillium Web',sans-serif;font-size:0.75rem;color:#27F4D2;">
    {fmt_lap(row['s3'])}</div>
  <div style="display:flex;align-items:center;gap:4px;">
    <div style="width:10px;height:10px;border-radius:50%;background:{ccolor};flex-shrink:0;"></div>
    <div style="font-family:'Titillium Web',sans-serif;font-size:0.62rem;font-weight:700;
                 color:{ccolor};">{row['compound'][:1]}</div>
  </div>
</div>""", unsafe_allow_html=True)

# ── RACE CONTROL MESSAGES ──────────────────────────────────────────────────────
st.markdown("""
<div style="font-family:'Titillium Web',sans-serif;font-size:0.65rem;font-weight:700;
            text-transform:uppercase;letter-spacing:0.2em;color:#E8002D;
            border-bottom:1px solid #2A2A2A;padding:1.5rem 2.5rem 0.5rem;margin-top:1rem;">
  Race Control Messages
</div>""", unsafe_allow_html=True)

recent_rc = sorted(race_control, key=lambda x: x.get("date",""), reverse=True)[:15]
if not recent_rc:
    st.markdown("""
<div style="padding:1.5rem 2.5rem;font-family:'Inter',sans-serif;
            font-size:0.8rem;color:#333;">No race control messages.</div>""",
        unsafe_allow_html=True)
else:
    for msg in recent_rc:
        flag     = str(msg.get("flag","")).upper()
        category = str(msg.get("category",""))
        message  = str(msg.get("message",""))
        lap_num  = msg.get("lap_number","")
        date_str = str(msg.get("date",""))[:19].replace("T"," ")
        fc       = FLAG_COLOR.get(flag, FLAG_COLOR.get(category.upper(), "#888888"))
        icon     = ("🟡" if flag in ("YELLOW","SC","VSC")
                    else "🔴" if flag=="RED"
                    else "🏁" if flag=="CHEQUERED"
                    else "🟢" if flag in ("GREEN","CLEAR")
                    else "📻")
        st.markdown(f"""
<div style="display:flex;align-items:flex-start;gap:1rem;background:#141414;
            border-left:3px solid {fc};border-bottom:1px solid #1A1A1A;
            padding:0.65rem 2.5rem;">
  <div style="font-size:1rem;flex-shrink:0;margin-top:0.1rem;">{icon}</div>
  <div style="flex:1;">
    <div style="font-family:'Inter',sans-serif;font-size:0.8rem;color:#CCCCCC;">
      {message}
    </div>
    <div style="font-family:'Inter',sans-serif;font-size:0.65rem;color:#555;margin-top:0.2rem;">
      {date_str}{f" · Lap {lap_num}" if lap_num else ""}
      {f" · <b style='color:{fc};'>{flag}</b>" if flag else ""}
    </div>
  </div>
</div>""", unsafe_allow_html=True)

# ── PIT STOP LOG ───────────────────────────────────────────────────────────────
st.markdown("""
<div style="font-family:'Titillium Web',sans-serif;font-size:0.65rem;font-weight:700;
            text-transform:uppercase;letter-spacing:0.2em;color:#E8002D;
            border-bottom:1px solid #2A2A2A;padding:1.5rem 2.5rem 0.5rem;margin-top:1rem;">
  Pit Stop Log
</div>""", unsafe_allow_html=True)

if not pit_stops:
    st.markdown("""
<div style="padding:1.5rem 2.5rem;font-family:'Inter',sans-serif;
            font-size:0.8rem;color:#333;">No pit stops recorded yet.</div>""",
        unsafe_allow_html=True)
else:
    sorted_pits = sorted(pit_stops, key=lambda x: x.get("date",""), reverse=True)
    st.markdown("""
<div style="display:grid;grid-template-columns:40px 80px 1fr 100px 100px;
            gap:0;background:#1C1C1C;border-bottom:1px solid #2A2A2A;
            padding:0.4rem 2.5rem;font-family:'Titillium Web',sans-serif;
            font-size:0.58rem;font-weight:700;text-transform:uppercase;
            letter-spacing:0.12em;color:#555;">
  <div>LAP</div><div>DRIVER</div><div>STOP DURATION</div><div>PIT IN</div><div>PIT OUT</div>
</div>""", unsafe_allow_html=True)
    for pit in sorted_pits[:15]:
        dn       = pit["driver_number"]
        drv      = driver_map.get(dn, {})
        code     = drv.get("name_acronym", str(dn))
        color    = "#" + drv.get("team_colour","888888")
        dur      = pit.get("pit_duration")
        dur_str  = f"{dur:.2f}s" if dur else "—"
        pit_in   = str(pit.get("date",""))[:19].replace("T"," ")[-8:]
        lap      = pit.get("lap_number","—")
        st.markdown(f"""
<div style="display:grid;grid-template-columns:40px 80px 1fr 100px 100px;
            gap:0;background:#141414;border-bottom:1px solid #1A1A1A;
            border-left:3px solid {color};padding:0.55rem 2.5rem;
            font-family:'Titillium Web',sans-serif;">
  <div style="font-size:0.8rem;font-weight:700;color:#888;">L{lap}</div>
  <div style="font-size:0.85rem;font-weight:800;color:#FFF;">{code}</div>
  <div style="font-size:0.85rem;font-weight:700;color:#27F4D2;">{dur_str}</div>
  <div style="font-size:0.72rem;color:#555;">{pit_in}</div>
  <div></div>
</div>""", unsafe_allow_html=True)

# ── INSIGHT BOX ───────────────────────────────────────────────────────────────
st.markdown("""
<div style="margin:1.5rem 2.5rem 0;background:#141414;border:1px solid #2A2A2A;
            border-left:4px solid #E8002D;padding:1.1rem 1.5rem;">
  <div style="font-family:'Titillium Web',sans-serif;font-size:0.65rem;font-weight:700;
              text-transform:uppercase;letter-spacing:0.18em;color:#E8002D;margin-bottom:0.5rem;">
    💡 How to Read the Timing Tower
  </div>
  <div style="font-family:'Inter',sans-serif;font-size:0.83rem;color:#CCCCCC;line-height:1.7;">
    <b>POS</b> = current race position. <b>GAP</b> = total time behind the race leader.
    <b>INTERVAL</b> = gap to the car directly ahead.
    <b>S1/S2/S3</b> = the three sector times of the most recent lap.
    The <b>coloured dot</b> shows tyre compound — 
    <b style="color:#DA291C">■ Soft</b> · 
    <b style="color:#FFD700">■ Medium</b> · 
    <b style="color:#E8E8E8">■ Hard</b> · 
    <b style="color:#43B02A">■ Inter</b> · 
    <b style="color:#0067AD">■ Wet</b>.
    The left-side coloured bar is the driver's <b>team colour</b>.
  </div>
</div>""", unsafe_allow_html=True)

# ── Auto-refresh ───────────────────────────────────────────────────────────────
col1, col2 = st.columns([3,1])
with col2:
    if st.button("🔄 Refresh Now", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.markdown(f"""
<div style="padding:1rem 2.5rem 2rem;font-family:'Inter',sans-serif;
            font-size:0.68rem;color:#333;">
  Last updated: {datetime.now().strftime("%H:%M:%S")} · 
  Data: OpenF1 API (api.openf1.org) · 
  Session key: {session_key}
</div>""", unsafe_allow_html=True)

if auto_refresh:
    time.sleep(5)
    st.rerun()