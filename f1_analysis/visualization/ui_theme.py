"""
F1 Hub — Global UI Theme
Inspired by f1-analytics.com visual style with Titillium Web fonts.
"""
import streamlit as st

# ── Palette ────────────────────────────────────────────────────────────────────
F1_RED    = "#E8002D"
F1_BLACK  = "#0D0D0D"
F1_CARD   = "#141414"
F1_CARD2  = "#1C1C1C"
F1_BORDER = "#2A2A2A"
F1_WHITE  = "#FFFFFF"
F1_GREY   = "#888888"
F1_GOLD   = "#FFD700"
F1_TEAL   = "#27F4D2"
F1_BLUE   = "#3671C6"
F1_GREEN  = "#27AE60"

COMPOUND_COLORS = {
    "SOFT":"#DA291C","MEDIUM":"#FFD700","HARD":"#E8E8E8",
    "INTERMEDIATE":"#43B02A","WET":"#0067AD","UNKNOWN":"#888888",
}
TEAM_COLORS = {
    "Red Bull":"#3671C6","Ferrari":"#E8002D","Mercedes":"#27F4D2",
    "McLaren":"#FF8000","Aston Martin":"#358C75","Alpine":"#FF87BC",
    "Williams":"#64C4FF","RB":"#6692FF","Haas":"#B6BABD","Sauber":"#52E252",
}


def inject_f1_css() -> None:
    st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Titillium+Web:wght@300;400;600;700;900&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
/* ── Instant base ─────────────────────────────────────────────── */
html,body,[data-testid="stApp"],[data-testid="stAppViewContainer"],[data-testid="stMain"],.main {
    background:#0D0D0D !important; }

/* ── Hide Streamlit chrome ────────────────────────────────────── */
#MainMenu { visibility:hidden; }
footer    { visibility:hidden; }
header[data-testid="stHeader"] { background:transparent !important; }
.stDeployButton,[data-testid="stDecoration"] { display:none !important; }

/* ── Sidebar ──────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background:#0D0D0D !important;
    border-right:1px solid #2A2A2A !important;
}
[data-testid="stSidebarNav"] { padding-top:0.5rem; }
[data-testid="stSidebarNav"] a {
    display:flex !important; align-items:center !important;
    padding:0.5rem 0.9rem !important;
    border-left:3px solid transparent !important;
    border-radius:0 !important;
    margin:1px 0 !important;
    transition:all 0.1s !important;
}
[data-testid="stSidebarNav"] a:hover {
    background:#1A1A1A !important; border-left-color:#E8002D !important; }
[data-testid="stSidebarNav"] a[aria-current="page"] {
    background:#1A1A1A !important; border-left-color:#E8002D !important; }
[data-testid="stSidebarNav"] a span {
    font-family:'Titillium Web',sans-serif !important;
    font-size:0.73rem !important; font-weight:600 !important;
    text-transform:uppercase !important; letter-spacing:0.1em !important;
    color:#AAAAAA !important;
}
[data-testid="stSidebarNav"] a[aria-current="page"] span { color:#FFFFFF !important; }
[data-testid="stSidebarNav"]::before {
    content:'Navigation';
    display:block;
    font-family:'Titillium Web',sans-serif;
    font-size:0.58rem; font-weight:700;
    text-transform:uppercase; letter-spacing:0.2em; color:#333;
    padding:0 0.9rem 0.6rem; border-bottom:1px solid #2A2A2A; margin-bottom:0.3rem;
}

/* ── Sidebar inputs ───────────────────────────────────────────── */
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stMarkdown p {
    color:#CCCCCC !important; font-family:'Inter',sans-serif !important;
    font-size:0.78rem !important;
}
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3 {
    color:#FFFFFF !important; font-family:'Titillium Web',sans-serif !important;
    font-weight:700 !important; font-size:0.82rem !important;
    text-transform:uppercase; letter-spacing:0.1em;
    border-bottom:1px solid #2A2A2A; padding-bottom:0.5rem; margin-bottom:0.8rem;
}
[data-testid="stSidebar"] .stButton > button {
    width:100%; background:#E8002D !important; color:#FFF !important;
    font-family:'Titillium Web',sans-serif !important;
    font-weight:700 !important; font-size:0.78rem !important;
    text-transform:uppercase; letter-spacing:0.12em;
    border:none !important; border-radius:0 !important;
    padding:0.65rem 1rem !important;
}
[data-testid="stSidebar"] .stButton > button:hover { background:#C0001F !important; }
[data-testid="stSidebar"] .stSelectbox > div > div,
[data-testid="stSidebar"] .stTextInput > div > div > input,
[data-testid="stSidebar"] .stNumberInput > div > div > input {
    background:#1A1A1A !important; border:1px solid #2A2A2A !important;
    color:#FFF !important; border-radius:0 !important;
    font-family:'Inter',sans-serif !important; font-size:0.82rem !important;
}
[data-testid="stSidebar"] .stSelectbox > div > div:focus-within,
[data-testid="stSidebar"] .stTextInput > div > div > input:focus {
    border-color:#E8002D !important; }

/* ── Main content ─────────────────────────────────────────────── */
.main .block-container { padding:0 !important; max-width:100% !important; }

/* ── st.metric override ───────────────────────────────────────── */
[data-testid="stMetric"] {
    background:#141414 !important; border:1px solid #2A2A2A !important;
    border-top:2px solid #E8002D !important; padding:1rem 1.2rem !important;
    border-radius:0 !important;
}
[data-testid="stMetricLabel"] {
    font-family:'Titillium Web',sans-serif !important;
    font-size:0.6rem !important; font-weight:700 !important;
    text-transform:uppercase !important; letter-spacing:0.15em !important; color:#555 !important;
}
[data-testid="stMetricValue"] {
    font-family:'Titillium Web',sans-serif !important;
    font-size:1.6rem !important; font-weight:900 !important; color:#FFF !important;
}

/* ── Tabs ─────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    background:#141414 !important; border-bottom:2px solid #2A2A2A !important; gap:0 !important; }
.stTabs [data-baseweb="tab"] {
    font-family:'Titillium Web',sans-serif !important; font-size:0.7rem !important;
    font-weight:700 !important; text-transform:uppercase !important;
    letter-spacing:0.12em !important; color:#555 !important;
    padding:0.75rem 1.4rem !important; border-bottom:3px solid transparent !important;
    background:transparent !important;
}
.stTabs [aria-selected="true"] {
    color:#FFF !important; border-bottom:3px solid #E8002D !important; }

/* ── Alerts ───────────────────────────────────────────────────── */
.stAlert { border-radius:0 !important; border-left-width:3px !important;
           background:#141414 !important; font-family:'Inter',sans-serif !important; }

/* ── Dataframe ────────────────────────────────────────────────── */
.stDataFrame { border:1px solid #2A2A2A !important; border-radius:0 !important; }
.stDataFrame thead tr th {
    background:#1C1C1C !important; color:#888 !important;
    font-family:'Titillium Web',sans-serif !important;
    font-size:0.62rem !important; font-weight:700 !important;
    text-transform:uppercase !important; letter-spacing:0.1em !important;
    border-bottom:2px solid #E8002D !important;
}

/* ── Spinner ──────────────────────────────────────────────────── */
.stSpinner > div { border-top-color:#E8002D !important; }

/* ── Scrollbar ────────────────────────────────────────────────── */
::-webkit-scrollbar { width:5px; height:5px; }
::-webkit-scrollbar-track { background:#0D0D0D; }
::-webkit-scrollbar-thumb { background:#2A2A2A; }
::-webkit-scrollbar-thumb:hover { background:#E8002D; }

/* ── Radio / checkbox ─────────────────────────────────────────── */
[data-testid="stRadio"] label,[data-testid="stCheckbox"] label {
    font-family:'Inter',sans-serif !important; font-size:0.82rem !important; color:#CCC !important; }

/* ── Charts ───────────────────────────────────────────────────── */
.stPlotlyChart,[data-testid="stImage"] {
    border:1px solid #2A2A2A !important; background:#0D0D0D !important; }

/* hr */
hr { border-color:#2A2A2A !important; margin:0 !important; }

/* ── Form cards (used in pages) ───────────────────────────────── */
.f1-card {
    background:#141414; border:1px solid #2A2A2A;
    padding:1.2rem 1.5rem; margin:0.8rem 0;
}

/* ── Status badge ─────────────────────────────────────────────── */
.f1-badge {
    display:inline-block; font-family:'Titillium Web',sans-serif;
    font-size:0.58rem; font-weight:700; text-transform:uppercase;
    letter-spacing:0.1em; padding:0.18rem 0.55rem; border-radius:2px;
}
.f1-badge-red   { background:#E8002D; color:#fff; }
.f1-badge-green { background:#27AE60; color:#fff; }
.f1-badge-gold  { background:#FFD700; color:#0D0D0D; }
.f1-badge-grey  { background:#2A2A2A; color:#888; }
.f1-badge-teal  { background:#27F4D2; color:#0D0D0D; }
.f1-badge-blue  { background:#3671C6; color:#fff; }
</style>
""", unsafe_allow_html=True)


# ── Component helpers ──────────────────────────────────────────────────────────

def page_header(icon: str, eyebrow: str, title: str, description: str = "") -> None:
    desc_html = f'<p style="font-family:Inter,sans-serif;font-size:0.83rem;color:#777;margin:0.4rem 0 0;max-width:60ch;line-height:1.6;">{description}</p>' if description else ""
    st.markdown(f"""
<div style="background:#141414;border-bottom:3px solid #E8002D;padding:1.6rem 2.5rem 1.4rem;">
  <p style="font-family:'Titillium Web',sans-serif;font-size:0.6rem;font-weight:700;
             text-transform:uppercase;letter-spacing:0.25em;color:#E8002D;margin:0 0 0.3rem;">
    {eyebrow}
  </p>
  <div style="display:flex;align-items:center;gap:0.8rem;">
    <span style="font-size:1.8rem;line-height:1;">{icon}</span>
    <h1 style="font-family:'Titillium Web',sans-serif;font-size:2.2rem;font-weight:900;
               color:#FFF;margin:0;text-transform:uppercase;letter-spacing:-0.01em;line-height:1;">
      {title}
    </h1>
  </div>
  {desc_html}
</div>""", unsafe_allow_html=True)


def section_label(text: str) -> None:
    st.markdown(f"""
<div style="font-family:'Titillium Web',sans-serif;font-size:0.62rem;font-weight:700;
            text-transform:uppercase;letter-spacing:0.2em;color:#E8002D;
            border-bottom:1px solid #2A2A2A;padding:2rem 0 0.5rem;margin-bottom:0.8rem;">
  {text}
</div>""", unsafe_allow_html=True)


def metrics_row(metrics: list[dict]) -> None:
    items = ""
    for m in metrics:
        color = ("#E8002D" if m.get("color")=="accent"
                 else "#FFD700" if m.get("color")=="gold"
                 else "#27F4D2" if m.get("color")=="teal"
                 else "#27AE60" if m.get("color")=="green"
                 else "#FFFFFF")
        delta_cls = ("color:#27AE60" if str(m.get("delta","")).startswith("+")
                     else "color:#E8002D" if str(m.get("delta","")).startswith("-")
                     else "color:#888")
        delta_html = f'<div style="font-family:Inter,sans-serif;font-size:0.7rem;{delta_cls};margin-top:0.15rem;">{m["delta"]}</div>' if m.get("delta") else ""
        items += f"""
<div style="flex:1;background:#141414;padding:1rem 1.3rem;">
  <div style="font-family:'Titillium Web',sans-serif;font-size:0.58rem;font-weight:700;
               text-transform:uppercase;letter-spacing:0.16em;color:#444;margin-bottom:0.2rem;">
    {m['label']}</div>
  <div style="font-family:'Titillium Web',sans-serif;font-size:1.8rem;font-weight:900;
               color:{color};line-height:1;">{m['value']}</div>
  {delta_html}
</div>"""
    st.markdown(f"""
<div style="display:flex;gap:1px;background:#2A2A2A;border-top:1px solid #2A2A2A;
            border-bottom:1px solid #2A2A2A;margin-bottom:0;">
  {items}
</div>""", unsafe_allow_html=True)


def insight_box(icon: str, title: str, body: str,
                border: str = "#E8002D", bg: str = "#141414") -> None:
    st.markdown(f"""
<div style="background:{bg};border:1px solid #2A2A2A;border-left:4px solid {border};
            padding:1.1rem 1.5rem;margin:0.8rem 0 1.4rem;">
  <div style="font-family:'Titillium Web',sans-serif;font-size:0.62rem;font-weight:700;
               text-transform:uppercase;letter-spacing:0.18em;color:{border};margin-bottom:0.5rem;">
    {icon}&nbsp;&nbsp;{title}
  </div>
  <div style="font-family:Inter,sans-serif;font-size:0.83rem;color:#CCC;line-height:1.7;">
    {body}
  </div>
</div>""", unsafe_allow_html=True)


def driver_card(code: str, name: str, team: str, team_color: str,
                position: int = 0, points: float = 0, extra: str = "") -> str:
    """Returns HTML for a driver card."""
    medal = "🥇" if position==1 else "🥈" if position==2 else "🥉" if position==3 else f"P{position}"
    return f"""
<div style="background:#141414;border:1px solid #2A2A2A;border-top:3px solid {team_color};
            padding:1rem 1.2rem;display:flex;align-items:center;gap:0.8rem;">
  <div style="font-family:'Titillium Web',sans-serif;font-size:1.5rem;font-weight:900;
               color:#2A2A2A;min-width:2rem;">{medal}</div>
  <div style="flex:1;">
    <div style="font-family:'Titillium Web',sans-serif;font-size:1.1rem;font-weight:900;
                 color:#FFF;">{code}</div>
    <div style="font-family:Inter,sans-serif;font-size:0.72rem;color:#666;">{name}</div>
    <div style="font-family:'Titillium Web',sans-serif;font-size:0.65rem;font-weight:700;
                 text-transform:uppercase;letter-spacing:0.08em;color:{team_color};margin-top:0.15rem;">{team}</div>
  </div>
  <div style="text-align:right;">
    <div style="font-family:'Titillium Web',sans-serif;font-size:1.4rem;font-weight:900;color:#FFF;">
      {points:.0f}</div>
    <div style="font-family:Inter,sans-serif;font-size:0.65rem;color:#555;">pts</div>
    {extra}
  </div>
</div>"""


def stat_row(items: list[tuple[str,str]]) -> None:
    cells = "".join(f"""
<div style="flex:1;min-width:120px;background:#1A1A1A;border:1px solid #2A2A2A;padding:0.7rem 1rem;">
  <div style="font-family:'Titillium Web',sans-serif;font-size:0.58rem;font-weight:700;
               text-transform:uppercase;letter-spacing:0.15em;color:#444;margin-bottom:0.2rem;">{lbl}</div>
  <div style="font-family:'Titillium Web',sans-serif;font-size:1rem;font-weight:800;color:#FFF;">{val}</div>
</div>""" for lbl, val in items)
    st.markdown(f"""
<div style="display:flex;flex-wrap:wrap;gap:1px;background:#2A2A2A;
            border:1px solid #2A2A2A;margin:0.6rem 0 1.2rem;">{cells}</div>""",
        unsafe_allow_html=True)

