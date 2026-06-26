"""F1 Hub - Global UI Theme"""
import streamlit as st

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
    "SOFT": "#DA291C",
    "MEDIUM": "#FFD700",
    "HARD": "#E8E8E8",
    "INTERMEDIATE": "#43B02A",
    "WET": "#0067AD",
    "UNKNOWN": "#888888",
}

TEAM_COLORS = {
    "Red Bull": "#3671C6",
    "Ferrari": "#E8002D",
    "Mercedes": "#27F4D2",
    "McLaren": "#FF8000",
    "Aston Martin": "#358C75",
    "Alpine": "#FF87BC",
    "Williams": "#64C4FF",
    "RB": "#6692FF",
    "Haas": "#B6BABD",
    "Sauber": "#52E252",
}


def inject_f1_css():
    css = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Titillium+Web:wght@300;400;600;700;900&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
html,body,[data-testid="stApp"],[data-testid="stAppViewContainer"],[data-testid="stMain"],.main {
    background: #0D0D0D !important;
}
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent !important; }
.stDeployButton { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
.main .block-container { padding: 0 !important; max-width: 100% !important; }
[data-testid="stSidebar"] {
    background: #0D0D0D !important;
    border-right: 1px solid #2A2A2A !important;
}
[data-testid="stSidebarNav"] { padding-top: 0.5rem; }
[data-testid="stSidebarNav"] a {
    display: flex !important;
    align-items: center !important;
    padding: 0.5rem 0.9rem !important;
    border-left: 3px solid transparent !important;
    border-radius: 0 !important;
    margin: 1px 0 !important;
    transition: all 0.1s !important;
}
[data-testid="stSidebarNav"] a:hover {
    background: #1A1A1A !important;
    border-left-color: #E8002D !important;
}
[data-testid="stSidebarNav"] a[aria-current="page"] {
    background: #1A1A1A !important;
    border-left-color: #E8002D !important;
}
[data-testid="stSidebarNav"] a span {
    font-family: 'Titillium Web', sans-serif !important;
    font-size: 0.73rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
    color: #AAAAAA !important;
}
[data-testid="stSidebarNav"] a[aria-current="page"] span {
    color: #FFFFFF !important;
}
[data-testid="stSidebarNav"]::before {
    content: 'Navigation';
    display: block;
    font-family: 'Titillium Web', sans-serif;
    font-size: 0.58rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.2em;
    color: #333;
    padding: 0 0.9rem 0.6rem;
    border-bottom: 1px solid #2A2A2A;
    margin-bottom: 0.3rem;
}
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stMarkdown p {
    color: #CCCCCC !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.78rem !important;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #FFFFFF !important;
    font-family: 'Titillium Web', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.82rem !important;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    border-bottom: 1px solid #2A2A2A;
    padding-bottom: 0.5rem;
    margin-bottom: 0.8rem;
}
[data-testid="stSidebar"] .stButton > button {
    width: 100%;
    background: #E8002D !important;
    color: #FFF !important;
    font-family: 'Titillium Web', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.78rem !important;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    border: none !important;
    border-radius: 0 !important;
    padding: 0.65rem 1rem !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: #C0001F !important;
}
[data-testid="stSidebar"] .stSelectbox > div > div,
[data-testid="stSidebar"] .stTextInput > div > div > input,
[data-testid="stSidebar"] .stNumberInput > div > div > input {
    background: #1A1A1A !important;
    border: 1px solid #2A2A2A !important;
    color: #FFF !important;
    border-radius: 0 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.82rem !important;
}
[data-testid="stSidebar"] .stSelectbox > div > div:focus-within,
[data-testid="stSidebar"] .stTextInput > div > div > input:focus {
    border-color: #E8002D !important;
}
[data-testid="stMetric"] {
    background: #141414 !important;
    border: 1px solid #2A2A2A !important;
    border-top: 2px solid #E8002D !important;
    padding: 1rem 1.2rem !important;
    border-radius: 0 !important;
}
[data-testid="stMetricLabel"] {
    font-family: 'Titillium Web', sans-serif !important;
    font-size: 0.6rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.15em !important;
    color: #555 !important;
}
[data-testid="stMetricValue"] {
    font-family: 'Titillium Web', sans-serif !important;
    font-size: 1.6rem !important;
    font-weight: 900 !important;
    color: #FFF !important;
}
.stTabs [data-baseweb="tab-list"] {
    background: #141414 !important;
    border-bottom: 2px solid #2A2A2A !important;
    gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'Titillium Web', sans-serif !important;
    font-size: 0.7rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.12em !important;
    color: #555 !important;
    padding: 0.75rem 1.4rem !important;
    border-bottom: 3px solid transparent !important;
    background: transparent !important;
}
.stTabs [aria-selected="true"] {
    color: #FFF !important;
    border-bottom: 3px solid #E8002D !important;
}
.stAlert {
    border-radius: 0 !important;
    border-left-width: 3px !important;
    background: #141414 !important;
    font-family: 'Inter', sans-serif !important;
}
.stDataFrame { border: 1px solid #2A2A2A !important; border-radius: 0 !important; }
.stDataFrame thead tr th {
    background: #1C1C1C !important;
    color: #888 !important;
    font-family: 'Titillium Web', sans-serif !important;
    font-size: 0.62rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
    border-bottom: 2px solid #E8002D !important;
}
.stSpinner > div { border-top-color: #E8002D !important; }
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #0D0D0D; }
::-webkit-scrollbar-thumb { background: #2A2A2A; }
::-webkit-scrollbar-thumb:hover { background: #E8002D; }
[data-testid="stRadio"] label,
[data-testid="stCheckbox"] label {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.82rem !important;
    color: #CCC !important;
}
hr { border-color: #2A2A2A !important; margin: 0 !important; }
</style>
"""
    st.markdown(css, unsafe_allow_html=True)


def page_header(icon, eyebrow, title, description=""):
    desc_html = ""
    if description:
        desc_html = '<p style="font-family:Inter,sans-serif;font-size:0.83rem;color:#777;margin:0.4rem 0 0;max-width:60ch;line-height:1.6;">' + description + '</p>'
    html = (
        '<div style="background:#141414;border-bottom:3px solid #E8002D;padding:1.6rem 2.5rem 1.4rem;">'
        '<p style="font-family:Titillium Web,sans-serif;font-size:0.6rem;font-weight:700;'
        'text-transform:uppercase;letter-spacing:0.25em;color:#E8002D;margin:0 0 0.3rem;">'
        + eyebrow +
        '</p>'
        '<div style="display:flex;align-items:center;gap:0.8rem;">'
        '<span style="font-size:1.8rem;line-height:1;">' + icon + '</span>'
        '<h1 style="font-family:Titillium Web,sans-serif;font-size:2.2rem;font-weight:900;'
        'color:#FFF;margin:0;text-transform:uppercase;letter-spacing:-0.01em;line-height:1;">'
        + title +
        '</h1></div>'
        + desc_html +
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def section_label(text):
    st.markdown(
        '<div style="font-family:Titillium Web,sans-serif;font-size:0.62rem;font-weight:700;'
        'text-transform:uppercase;letter-spacing:0.2em;color:#E8002D;'
        'border-bottom:1px solid #2A2A2A;padding:2rem 0 0.5rem;margin-bottom:0.8rem;">'
        + text + '</div>',
        unsafe_allow_html=True
    )


def metrics_row(metrics):
    items = ""
    for m in metrics:
        color = (
            "#E8002D" if m.get("color") == "accent" else
            "#FFD700" if m.get("color") == "gold" else
            "#27F4D2" if m.get("color") == "teal" else
            "#27AE60" if m.get("color") == "green" else
            "#FFFFFF"
        )
        delta = m.get("delta", "")
        delta_color = "#27AE60" if str(delta).startswith("+") else "#E8002D" if str(delta).startswith("-") else "#888"
        delta_html = ""
        if delta:
            delta_html = '<div style="font-family:Inter,sans-serif;font-size:0.7rem;color:' + delta_color + ';margin-top:0.15rem;">' + str(delta) + '</div>'
        items += (
            '<div style="flex:1;background:#141414;padding:1rem 1.3rem;">'
            '<div style="font-family:Titillium Web,sans-serif;font-size:0.58rem;font-weight:700;'
            'text-transform:uppercase;letter-spacing:0.16em;color:#444;margin-bottom:0.2rem;">'
            + m["label"] +
            '</div>'
            '<div style="font-family:Titillium Web,sans-serif;font-size:1.8rem;font-weight:900;'
            'color:' + color + ';line-height:1;">'
            + str(m["value"]) +
            '</div>'
            + delta_html +
            '</div>'
        )
    st.markdown(
        '<div style="display:flex;gap:1px;background:#2A2A2A;'
        'border-top:1px solid #2A2A2A;border-bottom:1px solid #2A2A2A;margin-bottom:0;">'
        + items + '</div>',
        unsafe_allow_html=True
    )


def insight_box(icon, title, body, border="#E8002D", bg="#141414"):
    st.markdown(
        '<div style="background:' + bg + ';border:1px solid #2A2A2A;border-left:4px solid ' + border + ';'
        'padding:1.1rem 1.5rem;margin:0.8rem 0 1.4rem;">'
        '<div style="font-family:Titillium Web,sans-serif;font-size:0.62rem;font-weight:700;'
        'text-transform:uppercase;letter-spacing:0.18em;color:' + border + ';margin-bottom:0.5rem;">'
        + icon + '  ' + title +
        '</div>'
        '<div style="font-family:Inter,sans-serif;font-size:0.83rem;color:#CCC;line-height:1.7;">'
        + body +
        '</div></div>',
        unsafe_allow_html=True
    )


def stat_row(items):
    cells = ""
    for lbl, val in items:
        cells += (
            '<div style="flex:1;min-width:120px;background:#1A1A1A;border:1px solid #2A2A2A;padding:0.7rem 1rem;">'
            '<div style="font-family:Titillium Web,sans-serif;font-size:0.58rem;font-weight:700;'
            'text-transform:uppercase;letter-spacing:0.15em;color:#444;margin-bottom:0.2rem;">' + lbl + '</div>'
            '<div style="font-family:Titillium Web,sans-serif;font-size:1rem;font-weight:800;color:#FFF;">' + val + '</div>'
            '</div>'
        )
    st.markdown(
        '<div style="display:flex;flex-wrap:wrap;gap:1px;background:#2A2A2A;'
        'border:1px solid #2A2A2A;margin:0.6rem 0 1.2rem;">' + cells + '</div>',
        unsafe_allow_html=True
    )