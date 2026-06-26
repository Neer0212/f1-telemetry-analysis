import streamlit as st
import sys, requests
from pathlib import Path
from datetime import datetime
sys.path.insert(0, str(Path(__file__).resolve().parent))

st.set_page_config(
    page_title="F1 Analytics Hub",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded",
)
from f1_analysis.visualization.ui_theme import inject_f1_css
inject_f1_css()

BASE_OF1 = "https://api.openf1.org/v1"

def openf1(endpoint, **params):
    try:
        r = requests.get(f"{BASE_OF1}/{endpoint}", params=params, timeout=6)
        r.raise_for_status()
        return r.json()
    except Exception:
        return []

# ── Sidebar logo ───────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
<div style="padding:1.2rem 0.8rem 1rem;border-bottom:1px solid #2A2A2A;margin-bottom:0.5rem;">
  <div style="font-family:'Titillium Web',sans-serif;font-size:1.2rem;font-weight:900;
               color:#E8002D;text-transform:uppercase;letter-spacing:0.06em;line-height:1;">
    F1 Analytics
  </div>
  <div style="font-family:Inter,sans-serif;font-size:0.65rem;color:#444;
               text-transform:uppercase;letter-spacing:0.15em;margin-top:0.2rem;">
    Hub · FastF1 + OpenF1
  </div>
</div>""", unsafe_allow_html=True)

# ── TOP NAV BAR ────────────────────────────────────────────────────────────────
st.markdown("""
<div style="background:#141414;border-bottom:1px solid #2A2A2A;
            padding:0 2.5rem;display:flex;align-items:center;gap:0;height:48px;">
  <div style="font-family:'Titillium Web',sans-serif;font-size:0.62rem;font-weight:900;
               color:#E8002D;text-transform:uppercase;letter-spacing:0.12em;margin-right:2rem;">
    F1 Analytics Hub
  </div>
  <div style="display:flex;gap:0;height:100%;align-items:stretch;">
    <a href="/" target="_self" style="font-family:'Titillium Web',sans-serif;font-size:0.7rem;
       font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#FFF;
       text-decoration:none;padding:0 1.2rem;display:flex;align-items:center;
       border-bottom:3px solid #E8002D;">Home</a>
    <a href="/Live_Timing" target="_self" style="font-family:'Titillium Web',sans-serif;font-size:0.7rem;
       font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#888;
       text-decoration:none;padding:0 1.2rem;display:flex;align-items:center;
       border-bottom:3px solid transparent;gap:0.4rem;">
       <span style="width:7px;height:7px;border-radius:50%;background:#E8002D;
                    animation:none;display:inline-block;"></span>Live</a>
    <a href="/Season_Championship" target="_self" style="font-family:'Titillium Web',sans-serif;font-size:0.7rem;
       font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#888;
       text-decoration:none;padding:0 1.2rem;display:flex;align-items:center;
       border-bottom:3px solid transparent;">Standings</a>
    <a href="/Head_to_Head" target="_self" style="font-family:'Titillium Web',sans-serif;font-size:0.7rem;
       font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#888;
       text-decoration:none;padding:0 1.2rem;display:flex;align-items:center;
       border-bottom:3px solid transparent;">Compare</a>
    <a href="/Race_Story" target="_self" style="font-family:'Titillium Web',sans-serif;font-size:0.7rem;
       font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#888;
       text-decoration:none;padding:0 1.2rem;display:flex;align-items:center;
       border-bottom:3px solid transparent;">Race Story</a>
    <a href="/Multi_Season" target="_self" style="font-family:'Titillium Web',sans-serif;font-size:0.7rem;
       font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#888;
       text-decoration:none;padding:0 1.2rem;display:flex;align-items:center;
       border-bottom:3px solid transparent;">Seasons</a>
  </div>
  <div style="margin-left:auto;font-family:Inter,sans-serif;font-size:0.68rem;color:#333;">
    FastF1 · OpenF1 · 2018–2026
  </div>
</div>
""", unsafe_allow_html=True)

# ── HERO ───────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="background:linear-gradient(135deg,#0D0D0D 60%,#1a0005 100%);
            border-bottom:3px solid #E8002D;padding:3.5rem 2.5rem 3rem;
            position:relative;overflow:hidden;">
  <div style="position:absolute;top:0;right:0;width:40%;height:100%;
              background:linear-gradient(90deg,transparent,#E8002D08);pointer-events:none;"></div>
  <div style="font-family:'Titillium Web',sans-serif;font-size:0.65rem;font-weight:700;
               text-transform:uppercase;letter-spacing:0.3em;color:#E8002D;margin-bottom:0.8rem;">
    Real-time F1 Analytics
  </div>
  <h1 style="font-family:'Titillium Web',sans-serif;font-size:3.8rem;font-weight:900;
              color:#FFFFFF;margin:0;line-height:1;text-transform:uppercase;letter-spacing:-0.02em;">
    F1 Analytics<br><span style="color:#E8002D;">Platform</span>
  </h1>
  <p style="font-family:Inter,sans-serif;font-size:1rem;color:#666;
             margin:1rem 0 2rem;max-width:52ch;line-height:1.65;">
    Real-time and historical Formula 1 data. Track live sessions, analyse past races,
    and compare driver performances with FastF1 telemetry.
  </p>
  <div style="display:flex;gap:0.8rem;flex-wrap:wrap;">
    <a href="/Live_Timing" target="_self" style="font-family:'Titillium Web',sans-serif;
       font-size:0.75rem;font-weight:700;text-transform:uppercase;letter-spacing:0.12em;
       background:#E8002D;color:#FFF;text-decoration:none;padding:0.75rem 1.8rem;
       display:inline-block;">
      ● Watch Live Timing
    </a>
    <a href="/Head_to_Head" target="_self" style="font-family:'Titillium Web',sans-serif;
       font-size:0.75rem;font-weight:700;text-transform:uppercase;letter-spacing:0.12em;
       background:transparent;color:#FFF;text-decoration:none;padding:0.75rem 1.8rem;
       border:1px solid #2A2A2A;display:inline-block;">
      Compare Drivers
    </a>
  </div>
</div>
""", unsafe_allow_html=True)

# ── LIVE STATUS STRIP ──────────────────────────────────────────────────────────
@st.cache_data(ttl=120)
def get_latest_session():
    sessions = openf1("sessions")
    return sessions[-1] if sessions else None

session_info = get_latest_session()
if session_info:
    sname = session_info.get("meeting_name","")
    stype = session_info.get("session_type","")
    circuit = session_info.get("circuit_short_name","")
    sdate = str(session_info.get("date_start",""))[:10]
    st.markdown(f"""
<div style="background:#1C1C1C;border-bottom:1px solid #2A2A2A;
            padding:0.7rem 2.5rem;display:flex;align-items:center;gap:2rem;">
  <div style="display:flex;align-items:center;gap:0.5rem;">
    <div style="width:8px;height:8px;border-radius:50%;background:#E8002D;"></div>
    <span style="font-family:'Titillium Web',sans-serif;font-size:0.65rem;font-weight:700;
                 text-transform:uppercase;letter-spacing:0.15em;color:#E8002D;">Latest Session</span>
  </div>
  <span style="font-family:'Titillium Web',sans-serif;font-size:0.82rem;font-weight:700;color:#FFF;">
    {sname} · {stype}
  </span>
  <span style="font-family:Inter,sans-serif;font-size:0.75rem;color:#555;">
    {circuit} · {sdate}
  </span>
  <a href="/Live_Timing" target="_self" style="margin-left:auto;font-family:'Titillium Web',sans-serif;
     font-size:0.62rem;font-weight:700;text-transform:uppercase;letter-spacing:0.12em;
     color:#E8002D;text-decoration:none;">View Timing →</a>
</div>""", unsafe_allow_html=True)

# ── FEATURE CARDS GRID ─────────────────────────────────────────────────────────
FEATURES = [
    ("/Live_Timing",        "Live Timing",          "LIVE",    "#E8002D",
     "Real-time driver positions, gaps, sector times, and pit stops during live F1 sessions."),
    ("/Deep_Dive",          "Session Analysis",     "",        "",
     "Lap time distributions, race pace, and tyre strategy for any session since 2018."),
    ("/Head_to_Head",       "Driver Comparison",    "",        "",
     "Compare speed traces, time deltas, and throttle/brake overlays between any two drivers."),
    ("/Pit_Window",         "Pit Strategy",         "",        "",
     "Optimal pit windows, undercut threat detection, and overcut viability analysis."),
    ("/Track_Speed_Map",    "Circuits",             "",        "",
     "Circuit outline painted by speed — every corner and straight from slowest to fastest."),
    ("/Race_Story",         "Race Recaps",          "NEW",     "#27AE60",
     "Lap-by-lap narrative of any driver's race: pit stops, overtakes, incidents, and pace."),
    ("/Season_Championship","Standings",            "",        "",
     "Round-by-round Drivers' and Constructors' championship points for any season."),
    ("/Multi_Season",       "Seasons",              "",        "",
     "Historical season comparisons, circuit heatmaps, and multi-year driver trends."),
    ("/Single_Race_Predict","ML Predictions",       "AI",      "#3671C6",
     "Four trained models: lap time, podium probability, tyre compound, undercut detection."),
]

st.markdown('<div style="padding:2rem 2.5rem 0;">', unsafe_allow_html=True)
st.markdown("""
<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:1px;
            background:#2A2A2A;border:1px solid #2A2A2A;">
""", unsafe_allow_html=True)

for href, title, badge, badge_color, desc in FEATURES:
    badge_html = ""
    if badge:
        badge_html = f"""<span style="font-family:'Titillium Web',sans-serif;font-size:0.55rem;
            font-weight:700;text-transform:uppercase;letter-spacing:0.1em;
            background:{badge_color};color:{'#0D0D0D' if badge_color in ('#FFD700','#27F4D2') else '#FFF'};
            padding:0.15rem 0.5rem;margin-left:0.5rem;">{badge}</span>"""
    st.markdown(f"""
<a href="{href}" target="_self" style="text-decoration:none;">
<div style="background:#141414;padding:1.6rem;cursor:pointer;
            transition:background 0.15s;display:block;" 
     onmouseover="this.style.background='#1C1C1C'" 
     onmouseout="this.style.background='#141414'">
  <div style="display:flex;align-items:center;margin-bottom:0.6rem;">
    <div style="font-family:'Titillium Web',sans-serif;font-size:0.85rem;font-weight:800;
                 text-transform:uppercase;letter-spacing:0.06em;color:#FFF;">
      {title}
    </div>
    {badge_html}
  </div>
  <div style="font-family:Inter,sans-serif;font-size:0.78rem;color:#555;line-height:1.55;">
    {desc}
  </div>
  <div style="font-family:'Titillium Web',sans-serif;font-size:0.6rem;font-weight:700;
               text-transform:uppercase;letter-spacing:0.15em;color:#E8002D;margin-top:0.8rem;">
    → Open
  </div>
</div>
</a>""", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ── BOTTOM TWO-COLUMN: Recent Seasons + Quick Actions ─────────────────────────
col_a, col_b = st.columns([1, 1], gap="small")

with col_a:
    st.markdown("""
<div style="margin-top:2rem;">
  <div style="font-family:'Titillium Web',sans-serif;font-size:0.62rem;font-weight:700;
               text-transform:uppercase;letter-spacing:0.2em;color:#E8002D;
               border-bottom:1px solid #2A2A2A;padding-bottom:0.5rem;margin-bottom:1rem;">
    Recent Seasons
  </div>
</div>""", unsafe_allow_html=True)
    for year in [2025, 2024, 2023, 2022, 2021, 2020]:
        st.markdown(f"""
<a href="/Season_Championship" target="_self" style="text-decoration:none;">
<div style="background:#141414;border:1px solid #2A2A2A;border-left:3px solid #E8002D;
            padding:0.7rem 1.2rem;margin-bottom:1px;display:flex;align-items:center;
            justify-content:space-between;">
  <span style="font-family:'Titillium Web',sans-serif;font-size:0.9rem;font-weight:800;color:#FFF;">
    {year}
  </span>
  <span style="font-family:'Titillium Web',sans-serif;font-size:0.6rem;font-weight:700;
               text-transform:uppercase;letter-spacing:0.12em;color:#E8002D;">→</span>
</div>
</a>""", unsafe_allow_html=True)

with col_b:
    st.markdown("""
<div style="margin-top:2rem;">
  <div style="font-family:'Titillium Web',sans-serif;font-size:0.62rem;font-weight:700;
               text-transform:uppercase;letter-spacing:0.2em;color:#E8002D;
               border-bottom:1px solid #2A2A2A;padding-bottom:0.5rem;margin-bottom:1rem;">
    Quick Actions
  </div>
</div>""", unsafe_allow_html=True)
    quick = [
        ("/Live_Timing",        "● Watch Live Timing"),
        ("/Head_to_Head",       "Compare Two Drivers"),
        ("/Race_Story",         "Read a Race Story"),
        ("/Season_Championship","View Championship"),
        ("/Multi_Season",       "Browse Seasons"),
        ("/Single_Race_Predict","Run ML Predictions"),
    ]
    for href, label in quick:
        is_live = "●" in label
        color   = "#E8002D" if is_live else "#888"
        st.markdown(f"""
<a href="{href}" target="_self" style="text-decoration:none;">
<div style="background:#141414;border:1px solid #2A2A2A;padding:0.7rem 1.2rem;
            margin-bottom:1px;display:flex;align-items:center;justify-content:space-between;">
  <span style="font-family:'Titillium Web',sans-serif;font-size:0.8rem;font-weight:700;
               color:{color};">{label}</span>
  <span style="font-family:'Titillium Web',sans-serif;font-size:0.6rem;color:#333;">→</span>
</div>
</a>""", unsafe_allow_html=True)

# ── 2024 Driver Grid ───────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-top:2rem;">
  <div style="font-family:'Titillium Web',sans-serif;font-size:0.62rem;font-weight:700;
               text-transform:uppercase;letter-spacing:0.2em;color:#E8002D;
               border-bottom:1px solid #2A2A2A;padding-bottom:0.5rem;margin-bottom:1rem;">
    2024 Driver Reference
  </div>
  <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:1px;
              background:#2A2A2A;border:1px solid #2A2A2A;">
""", unsafe_allow_html=True)

DRIVERS = [
    ("VER","Max Verstappen","Red Bull","#3671C6"),
    ("PER","Sergio Perez","Red Bull","#3671C6"),
    ("LEC","Charles Leclerc","Ferrari","#E8002D"),
    ("SAI","Carlos Sainz","Ferrari","#E8002D"),
    ("NOR","Lando Norris","McLaren","#FF8000"),
    ("PIA","Oscar Piastri","McLaren","#FF8000"),
    ("HAM","Lewis Hamilton","Mercedes","#27F4D2"),
    ("RUS","George Russell","Mercedes","#27F4D2"),
    ("ALO","Fernando Alonso","Aston Martin","#358C75"),
    ("STR","Lance Stroll","Aston Martin","#358C75"),
    ("GAS","Pierre Gasly","Alpine","#FF87BC"),
    ("OCO","Esteban Ocon","Alpine","#FF87BC"),
    ("ALB","Alexander Albon","Williams","#64C4FF"),
    ("SAR","Logan Sargeant","Williams","#64C4FF"),
    ("TSU","Yuki Tsunoda","RB","#6692FF"),
    ("RIC","Daniel Ricciardo","RB","#6692FF"),
    ("HUL","Nico Hulkenberg","Haas","#B6BABD"),
    ("MAG","Kevin Magnussen","Haas","#B6BABD"),
    ("BOT","Valtteri Bottas","Sauber","#52E252"),
    ("ZHO","Guanyu Zhou","Sauber","#52E252"),
]
for code, name, team, color in DRIVERS:
    st.markdown(f"""
<div style="background:#141414;padding:0.85rem 1rem;border-left:3px solid {color};">
  <div style="font-family:'Titillium Web',sans-serif;font-size:1rem;font-weight:900;color:#FFF;">{code}</div>
  <div style="font-family:Inter,sans-serif;font-size:0.65rem;color:#555;">{name}</div>
  <div style="font-family:'Titillium Web',sans-serif;font-size:0.6rem;font-weight:700;
               text-transform:uppercase;letter-spacing:0.05em;color:{color};margin-top:0.15rem;">{team}</div>
</div>""", unsafe_allow_html=True)

st.markdown("</div></div>", unsafe_allow_html=True)

# ── FOOTER ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="border-top:1px solid #2A2A2A;margin-top:2rem;padding:1.5rem 2.5rem;
            display:flex;justify-content:space-between;align-items:center;">
  <div style="font-family:'Titillium Web',sans-serif;font-size:0.65rem;font-weight:700;
               text-transform:uppercase;letter-spacing:0.15em;color:#E8002D;">
    F1 Analytics Hub
  </div>
  <div style="font-family:Inter,sans-serif;font-size:0.68rem;color:#333;text-align:center;">
    Built with FastF1 · OpenF1 · Streamlit · Scikit-learn<br>
    <span style="font-size:0.6rem;color:#222;">
      This project is unofficial and not associated with Formula 1 companies.
    </span>
  </div>
  <div style="font-family:Inter,sans-serif;font-size:0.68rem;color:#333;">
    Data: 2018–2026
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)