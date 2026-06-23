import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

st.set_page_config(
    page_title="F1 Analytics Hub",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded",
)

from f1_analysis.visualization.ui_theme import inject_f1_css, section_label, metrics_row

inject_f1_css()

# ── Sidebar — logo only; Streamlit renders the real nav automatically ─────────
with st.sidebar:
    st.markdown("""
<div style="padding: 1rem 0.5rem 1.2rem; border-bottom: 1px solid #2A2A2A; margin-bottom: 0.5rem;">
    <div style="font-family: 'Titillium Web', sans-serif; font-size: 1.3rem; font-weight: 900;
                color: #E8002D; text-transform: uppercase; letter-spacing: 0.05em; line-height: 1;">
        F1 Analytics
    </div>
    <div style="font-family: 'Inter', sans-serif; font-size: 0.68rem; color: #555;
                text-transform: uppercase; letter-spacing: 0.15em; margin-top: 0.2rem;">
        Hub · FastF1 Powered
    </div>
</div>
""", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="background: #141414; border-bottom: 3px solid #E8002D; padding: 3rem 2.5rem 2.5rem;">
    <div style="font-family:'Titillium Web',sans-serif; font-size:0.65rem; font-weight:700;
                text-transform:uppercase; letter-spacing:0.25em; color:#E8002D; margin-bottom:0.6rem;">
        Formula 1 · Data & Telemetry Platform
    </div>
    <h1 style="font-family:'Titillium Web',sans-serif; font-size:3.5rem; font-weight:900;
               color:#FFFFFF; margin:0; line-height:1; text-transform:uppercase; letter-spacing:-0.02em;">
        F1 Analytics Hub
    </h1>
    <p style="font-family:'Inter',sans-serif; font-size:1rem; color:#777; margin:0.8rem 0 2rem;
              max-width:55ch; line-height:1.6;">
        Professional-grade Formula 1 data analysis. Telemetry, race strategy, 
        championship trends, machine learning predictions — built on real FastF1 timing data.
    </p>
    <div style="display:flex; gap:0.5rem; flex-wrap:wrap;">
        <span style="font-family:'Titillium Web',sans-serif; font-size:0.65rem; font-weight:700;
                     text-transform:uppercase; letter-spacing:0.1em; padding:0.3rem 0.8rem;
                     background:#E8002D; color:white;">Live Data</span>
        <span style="font-family:'Titillium Web',sans-serif; font-size:0.65rem; font-weight:700;
                     text-transform:uppercase; letter-spacing:0.1em; padding:0.3rem 0.8rem;
                     background:#2A2A2A; color:#888;">2018 — 2026</span>
        <span style="font-family:'Titillium Web',sans-serif; font-size:0.65rem; font-weight:700;
                     text-transform:uppercase; letter-spacing:0.1em; padding:0.3rem 0.8rem;
                     background:#2A2A2A; color:#888;">FastF1 Powered</span>
        <span style="font-family:'Titillium Web',sans-serif; font-size:0.65rem; font-weight:700;
                     text-transform:uppercase; letter-spacing:0.1em; padding:0.3rem 0.8rem;
                     background:#2A2A2A; color:#888;">4 ML Models</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Stats strip ───────────────────────────────────────────────────────────────
metrics_row([
    {"label": "Analysis Tools",     "value": "9",    "color": "accent"},
    {"label": "Seasons of Data",    "value": "8+"},
    {"label": "ML Models",          "value": "4",    "color": "teal"},
    {"label": "Drivers per Season", "value": "20"},
    {"label": "Data Points / Race", "value": "100K+","color": "gold"},
])

# ── Tools grid ────────────────────────────────────────────────────────────────
section_label("Analysis Tools")

st.markdown("""
<div style="padding: 0 2.5rem;">
<div style="display:grid; grid-template-columns:repeat(3,1fr); gap:1px; background:#2A2A2A;
            border:1px solid #2A2A2A;">

  <div style="background:#141414; padding:1.5rem;">
    <div style="font-size:1.4rem; margin-bottom:0.7rem;">📊</div>
    <div style="font-family:'Titillium Web',sans-serif; font-size:0.85rem; font-weight:700;
                text-transform:uppercase; letter-spacing:0.08em; color:#FFFFFF; margin-bottom:0.4rem;">
        Session Deep Dive
    </div>
    <div style="font-family:'Inter',sans-serif; font-size:0.78rem; color:#666; line-height:1.5;">
        Lap time distributions, race pace consistency, and tire strategy for any session since 2018.
        Supports Race, Qualifying, Sprint and all Free Practice sessions.
    </div>
    <div style="margin-top:0.8rem; font-family:'Titillium Web',sans-serif; font-size:0.6rem;
                font-weight:700; text-transform:uppercase; letter-spacing:0.12em; color:#E8002D;">
        → Page 1
    </div>
  </div>

  <div style="background:#141414; padding:1.5rem;">
    <div style="font-size:1.4rem; margin-bottom:0.7rem;">⚔️</div>
    <div style="font-family:'Titillium Web',sans-serif; font-size:0.85rem; font-weight:700;
                text-transform:uppercase; letter-spacing:0.08em; color:#FFFFFF; margin-bottom:0.4rem;">
        Head-to-Head Telemetry
    </div>
    <div style="font-family:'Inter',sans-serif; font-size:0.78rem; color:#666; line-height:1.5;">
        Speed traces, time deltas, and throttle/brake overlays. See exactly where one driver 
        gains or loses time on every corner of the lap.
    </div>
    <div style="margin-top:0.8rem; font-family:'Titillium Web',sans-serif; font-size:0.6rem;
                font-weight:700; text-transform:uppercase; letter-spacing:0.12em; color:#E8002D;">
        → Page 2
    </div>
  </div>

  <div style="background:#141414; padding:1.5rem;">
    <div style="font-size:1.4rem; margin-bottom:0.7rem;">🏆</div>
    <div style="font-family:'Titillium Web',sans-serif; font-size:0.85rem; font-weight:700;
                text-transform:uppercase; letter-spacing:0.08em; color:#FFFFFF; margin-bottom:0.4rem;">
        Championship Progression
    </div>
    <div style="font-family:'Inter',sans-serif; font-size:0.78rem; color:#666; line-height:1.5;">
        Round-by-round points progression for Drivers' and Constructors' Championships. 
        Watch any season unfold race by race.
    </div>
    <div style="margin-top:0.8rem; font-family:'Titillium Web',sans-serif; font-size:0.6rem;
                font-weight:700; text-transform:uppercase; letter-spacing:0.12em; color:#E8002D;">
        → Page 3
    </div>
  </div>

  <div style="background:#141414; padding:1.5rem;">
    <div style="font-size:1.4rem; margin-bottom:0.7rem;">🗺️</div>
    <div style="font-family:'Titillium Web',sans-serif; font-size:0.85rem; font-weight:700;
                text-transform:uppercase; letter-spacing:0.08em; color:#FFFFFF; margin-bottom:0.4rem;">
        Track Speed Map
    </div>
    <div style="font-family:'Inter',sans-serif; font-size:0.78rem; color:#666; line-height:1.5;">
        Circuit outline painted by speed — every sector, corner, and straight coloured 
        from slowest to fastest. Understand a track at a glance.
    </div>
    <div style="margin-top:0.8rem; font-family:'Titillium Web',sans-serif; font-size:0.6rem;
                font-weight:700; text-transform:uppercase; letter-spacing:0.12em; color:#E8002D;">
        → Page 4
    </div>
  </div>

  <div style="background:#141414; padding:1.5rem;">
    <div style="font-size:1.4rem; margin-bottom:0.7rem;">📖</div>
    <div style="font-family:'Titillium Web',sans-serif; font-size:0.85rem; font-weight:700;
                text-transform:uppercase; letter-spacing:0.08em; color:#FFFFFF; margin-bottom:0.4rem;">
        Race Story
    </div>
    <div style="font-family:'Inter',sans-serif; font-size:0.78rem; color:#666; line-height:1.5;">
        Lap-by-lap narrative of any driver's race: pit stops, overtakes, safety cars, 
        undercut windows, and sector-by-sector pace breakdown.
    </div>
    <div style="margin-top:0.8rem; font-family:'Titillium Web',sans-serif; font-size:0.6rem;
                font-weight:700; text-transform:uppercase; letter-spacing:0.12em; color:#E8002D;">
        → Page 6
    </div>
  </div>

  <div style="background:#141414; padding:1.5rem;">
    <div style="font-size:1.4rem; margin-bottom:0.7rem;">⏱️</div>
    <div style="font-family:'Titillium Web',sans-serif; font-size:0.85rem; font-weight:700;
                text-transform:uppercase; letter-spacing:0.08em; color:#FFFFFF; margin-bottom:0.4rem;">
        Qualifying Delta Map
    </div>
    <div style="font-family:'Inter',sans-serif; font-size:0.78rem; color:#666; line-height:1.5;">
        Minisector-by-minisector comparison. Green where driver A is faster, red where B 
        is. Identify the exact corners deciding a lap.
    </div>
    <div style="margin-top:0.8rem; font-family:'Titillium Web',sans-serif; font-size:0.6rem;
                font-weight:700; text-transform:uppercase; letter-spacing:0.12em; color:#E8002D;">
        → Page 7
    </div>
  </div>

  <div style="background:#141414; padding:1.5rem;">
    <div style="font-size:1.4rem; margin-bottom:0.7rem;">🛞</div>
    <div style="font-family:'Titillium Web',sans-serif; font-size:0.85rem; font-weight:700;
                text-transform:uppercase; letter-spacing:0.08em; color:#FFFFFF; margin-bottom:0.4rem;">
        Pit Stop Window
    </div>
    <div style="font-family:'Inter',sans-serif; font-size:0.78rem; color:#666; line-height:1.5;">
        Optimal pit lap range, undercut threat detection, and overcut viability analysis. 
        For one driver or the entire field simultaneously.
    </div>
    <div style="margin-top:0.8rem; font-family:'Titillium Web',sans-serif; font-size:0.6rem;
                font-weight:700; text-transform:uppercase; letter-spacing:0.12em; color:#E8002D;">
        → Page 8
    </div>
  </div>

  <div style="background:#141414; padding:1.5rem;">
    <div style="font-size:1.4rem; margin-bottom:0.7rem;">📈</div>
    <div style="font-family:'Titillium Web',sans-serif; font-size:0.85rem; font-weight:700;
                text-transform:uppercase; letter-spacing:0.08em; color:#FFFFFF; margin-bottom:0.4rem;">
        Multi-Season Comparison
    </div>
    <div style="font-family:'Inter',sans-serif; font-size:0.78rem; color:#666; line-height:1.5;">
        One driver across seasons, head-to-head across years, or a full season circuit heatmap 
        showing gap-to-pole at every round.
    </div>
    <div style="margin-top:0.8rem; font-family:'Titillium Web',sans-serif; font-size:0.6rem;
                font-weight:700; text-transform:uppercase; letter-spacing:0.12em; color:#E8002D;">
        → Page 9
    </div>
  </div>

  <div style="background:#141414; padding:1.5rem; border-left: 3px solid #E8002D;">
    <div style="font-size:1.4rem; margin-bottom:0.7rem;">🤖</div>
    <div style="font-family:'Titillium Web',sans-serif; font-size:0.85rem; font-weight:700;
                text-transform:uppercase; letter-spacing:0.08em; color:#FFFFFF; margin-bottom:0.4rem;">
        ML Predictions
    </div>
    <div style="font-family:'Inter',sans-serif; font-size:0.78rem; color:#666; line-height:1.5;">
        Four trained models: lap time prediction, podium probability, tyre compound 
        classification, and undercut opportunity detection.
    </div>
    <div style="margin-top:0.8rem; font-family:'Titillium Web',sans-serif; font-size:0.6rem;
                font-weight:700; text-transform:uppercase; letter-spacing:0.12em; color:#E8002D;">
        → Page 5
    </div>
  </div>

</div>
</div>
""", unsafe_allow_html=True)

# ── How to use ────────────────────────────────────────────────────────────────
section_label("How It Works")

st.markdown("""
<div style="padding: 0 2.5rem;">
<div style="display:grid; grid-template-columns:repeat(3,1fr); gap:1px; background:#2A2A2A;
            border:1px solid #2A2A2A; margin-bottom:1.5rem;">
  <div style="background:#141414; padding:1.5rem; display:flex; gap:1rem; align-items:flex-start;">
    <div style="font-family:'Titillium Web',sans-serif; font-size:2rem; font-weight:900;
                color:#2A2A2A; line-height:1; flex-shrink:0;">01</div>
    <div>
      <div style="font-family:'Titillium Web',sans-serif; font-size:0.78rem; font-weight:700;
                  text-transform:uppercase; letter-spacing:0.1em; color:#FFFFFF; margin-bottom:0.3rem;">
        Pick a Tool
      </div>
      <div style="font-family:'Inter',sans-serif; font-size:0.75rem; color:#555; line-height:1.5;">
        Select any analysis from the sidebar navigation on the left.
      </div>
    </div>
  </div>
  <div style="background:#141414; padding:1.5rem; display:flex; gap:1rem; align-items:flex-start;">
    <div style="font-family:'Titillium Web',sans-serif; font-size:2rem; font-weight:900;
                color:#2A2A2A; line-height:1; flex-shrink:0;">02</div>
    <div>
      <div style="font-family:'Titillium Web',sans-serif; font-size:0.78rem; font-weight:700;
                  text-transform:uppercase; letter-spacing:0.1em; color:#FFFFFF; margin-bottom:0.3rem;">
        Enter Parameters
      </div>
      <div style="font-family:'Inter',sans-serif; font-size:0.75rem; color:#555; line-height:1.5;">
        Set year, Grand Prix name, session type, and driver abbreviations.
      </div>
    </div>
  </div>
  <div style="background:#141414; padding:1.5rem; display:flex; gap:1rem; align-items:flex-start;">
    <div style="font-family:'Titillium Web',sans-serif; font-size:2rem; font-weight:900;
                color:#E8002D; line-height:1; flex-shrink:0;">03</div>
    <div>
      <div style="font-family:'Titillium Web',sans-serif; font-size:0.78rem; font-weight:700;
                  text-transform:uppercase; letter-spacing:0.1em; color:#FFFFFF; margin-bottom:0.3rem;">
        Run Analysis
      </div>
      <div style="font-family:'Inter',sans-serif; font-size:0.75rem; color:#555; line-height:1.5;">
        Hit the red button. First load fetches from F1 servers (10–30s). Every repeat load is instant.
      </div>
    </div>
  </div>
</div>
</div>
""", unsafe_allow_html=True)

# ── Driver reference ──────────────────────────────────────────────────────────
section_label("2024 Driver Reference")

st.markdown("""
<div style="padding: 0 2.5rem 3rem;">
<div style="display:grid; grid-template-columns:repeat(5,1fr); gap:1px; background:#2A2A2A;
            border:1px solid #2A2A2A;">
""" + "".join([
    f"""<div style="background:#141414; padding:0.8rem 1rem;">
    <div style="font-family:'Titillium Web',sans-serif; font-size:1rem; font-weight:900;
                color:#FFFFFF;">{code}</div>
    <div style="font-family:'Inter',sans-serif; font-size:0.68rem; color:#555;">{name}</div>
    <div style="font-family:'Titillium Web',sans-serif; font-size:0.6rem; font-weight:700;
                color:{tcolor}; text-transform:uppercase; letter-spacing:0.05em; margin-top:0.15rem;">{team}</div>
</div>"""
    for code, name, team, tcolor in [
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
]) + """
</div>
</div>
""", unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="border-top:1px solid #2A2A2A; padding:1.5rem 2.5rem;
            display:flex; justify-content:space-between; align-items:center; margin-top:2rem;">
    <div style="font-family:'Titillium Web',sans-serif; font-size:0.6rem; font-weight:700;
                text-transform:uppercase; letter-spacing:0.15em; color:#E8002D;">
        F1 Analytics Hub
    </div>
    <div style="font-family:'Inter',sans-serif; font-size:0.7rem; color:#333;">
        Built with FastF1 · Matplotlib · Scikit-learn · Streamlit
    </div>
    <div style="font-family:'Inter',sans-serif; font-size:0.7rem; color:#333;">
        Data: 2018 — 2026
    </div>
</div>
""", unsafe_allow_html=True)