"""F1 Hub - Global UI Theme - Full Width No Sidebar"""
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

NAV_PAGES = [
    ("Home",         "/"),
    ("Live",         "/Live_Timing"),
    ("Deep Dive",    "/Deep_Dive"),
    ("Head to Head", "/Head_to_Head"),
    ("Championship", "/Season_Championship"),
    ("Speed Map",    "/Track_Speed_Map"),
    ("Race Story",   "/Race_Story"),
    ("Qualifying",   "/Quali_Delta"),
    ("Pit Window",   "/Pit_Window"),
    ("Multi-Season", "/Multi_Season"),
    ("Predictions",  "/Single_Race_Predict"),
]


def inject_f1_css():
    css = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Titillium+Web:wght@300;400;600;700;900&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
html, body, [data-testid="stApp"], [data-testid="stAppViewContainer"], [data-testid="stMain"], .main {
    background: #0D0D0D !important;
    font-family: 'Inter', sans-serif;
}

/* Hide ALL sidebar and header chrome */
[data-testid="stSidebar"] { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
[data-testid="stSidebarCollapsedControl"] { display: none !important; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header[data-testid="stHeader"] { display: none !important; }
.stDeployButton { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
section[data-testid="stSidebarContent"] { display: none !important; }
button[kind="header"] { display: none !important; }

/* Full width content */
.main .block-container {
    padding: 0 !important;
    max-width: 100% !important;
    width: 100% !important;
}
.stMainBlockContainer { padding: 0 !important; max-width: 100% !important; }

/* Input styling */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stSelectbox > div > div {
    background: #1A1A1A !important;
    border: 1px solid #2A2A2A !important;
    color: #FFF !important;
    border-radius: 0 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.85rem !important;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus,
.stSelectbox > div > div:focus-within {
    border-color: #E8002D !important;
    box-shadow: none !important;
}
label[data-testid="stWidgetLabel"] p {
    font-family: 'Titillium Web', sans-serif !important;
    font-size: 0.65rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.15em !important;
    color: #666 !important;
}

/* Buttons */
.stButton > button {
    background: #E8002D !important;
    color: #FFF !important;
    font-family: 'Titillium Web', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.78rem !important;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    border: none !important;
    border-radius: 0 !important;
    padding: 0.65rem 2rem !important;
    transition: background 0.15s !important;
}
.stButton > button:hover { background: #C0001F !important; }

/* Metrics */
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

/* Tabs */
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

/* Alerts */
.stAlert {
    border-radius: 0 !important;
    border-left-width: 3px !important;
    background: #141414 !important;
    font-family: 'Inter', sans-serif !important;
}

/* Dataframe */
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

/* Spinner */
.stSpinner > div { border-top-color: #E8002D !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #0D0D0D; }
::-webkit-scrollbar-thumb { background: #2A2A2A; }
::-webkit-scrollbar-thumb:hover { background: #E8002D; }

/* Radio / checkbox */
[data-testid="stRadio"] label,
[data-testid="stCheckbox"] label {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.82rem !important;
    color: #CCC !important;
}

/* Charts */
.stPlotlyChart, [data-testid="stImage"] {
    border: 1px solid #2A2A2A !important;
    background: #0D0D0D !important;
}

hr { border-color: #2A2A2A !important; margin: 0 !important; }

/* Toggle */
[data-testid="stToggle"] label {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.82rem !important;
    color: #CCC !important;
}
</style>
"""
    st.markdown(css, unsafe_allow_html=True)


def top_nav(current=""):
    """Render the top navigation bar."""
    nav_items = ""
    for label, href in NAV_PAGES:
        is_live = label == "Live"
        live_dot = '<span style="width:7px;height:7px;border-radius:50%;background:#E8002D;display:inline-block;margin-right:5px;"></span>' if is_live else ""
        active_style = "color:#FFF;border-bottom:3px solid #E8002D;" if current == label else "color:#666;border-bottom:3px solid transparent;"
        nav_items += (
            '<a href="' + href + '" target="_self" style="'
            'font-family:Titillium Web,sans-serif;font-size:0.68rem;font-weight:700;'
            'text-transform:uppercase;letter-spacing:0.1em;text-decoration:none;'
            'padding:0 1rem;display:flex;align-items:center;height:100%;'
            + active_style + '">'
            + live_dot + label +
            '</a>'
        )
    st.markdown(
        '<div style="background:#141414;border-bottom:1px solid #2A2A2A;'
        'padding:0 2rem;display:flex;align-items:center;height:52px;position:sticky;top:0;z-index:999;">'
        '<a href="/" target="_self" style="font-family:Titillium Web,sans-serif;font-size:0.75rem;'
        'font-weight:900;color:#E8002D;text-transform:uppercase;letter-spacing:0.12em;'
        'text-decoration:none;margin-right:2rem;white-space:nowrap;">F1 Analytics Hub</a>'
        '<div style="display:flex;align-items:stretch;height:100%;gap:0;overflow-x:auto;">'
        + nav_items +
        '</div>'
        '<div style="margin-left:auto;font-family:Inter,sans-serif;font-size:0.65rem;color:#333;white-space:nowrap;">'
        'FastF1 + OpenF1</div>'
        '</div>',
        unsafe_allow_html=True
    )


def page_header(icon, eyebrow, title, description=""):
    desc_html = ""
    if description:
        desc_html = (
            '<p style="font-family:Inter,sans-serif;font-size:0.88rem;color:#666;'
            'margin:0.5rem 0 0;max-width:65ch;line-height:1.65;">' + description + '</p>'
        )
    st.markdown(
        '<div style="background:#141414;border-bottom:3px solid #E8002D;padding:2rem 2.5rem 1.8rem;">'
        '<p style="font-family:Titillium Web,sans-serif;font-size:0.6rem;font-weight:700;'
        'text-transform:uppercase;letter-spacing:0.28em;color:#E8002D;margin:0 0 0.4rem;">'
        + eyebrow + '</p>'
        '<div style="display:flex;align-items:center;gap:0.8rem;">'
        '<span style="font-size:2rem;line-height:1;">' + icon + '</span>'
        '<h1 style="font-family:Titillium Web,sans-serif;font-size:2.6rem;font-weight:900;'
        'color:#FFF;margin:0;text-transform:uppercase;letter-spacing:-0.02em;line-height:1;">'
        + title + '</h1>'
        '</div>'
        + desc_html +
        '</div>',
        unsafe_allow_html=True
    )


def control_panel(fields, button_label="Run Analysis", cols_per_row=4):
    """
    Render an inline control panel with fields and a run button.
    fields: list of dicts with keys: type, label, key, default, [options], [min], [max]
    Returns True when the button is clicked.
    """
    st.markdown(
        '<div style="background:#1C1C1C;border-bottom:2px solid #2A2A2A;padding:1.5rem 2.5rem;">',
        unsafe_allow_html=True
    )
    # Render fields in columns
    n = min(cols_per_row, len(fields) + 1)
    cols = st.columns(n)
    values = {}
    for i, field in enumerate(fields):
        with cols[i % (n - 1)]:
            ftype = field.get("type", "text")
            key   = field["key"]
            label = field["label"]
            if ftype == "number":
                values[key] = st.number_input(
                    label, min_value=field.get("min", 0),
                    max_value=field.get("max", 9999),
                    value=field.get("default", 0), key=key
                )
            elif ftype == "select":
                values[key] = st.selectbox(
                    label, options=field.get("options", []),
                    index=field.get("options", []).index(field["default"])
                    if field.get("default") in field.get("options", []) else 0,
                    key=key
                )
            else:
                values[key] = st.text_input(label, value=field.get("default", ""), key=key)

    with cols[-1]:
        st.markdown('<div style="padding-top:1.55rem;"></div>', unsafe_allow_html=True)
        clicked = st.button(button_label, type="primary", use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)
    return clicked, values


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
            delta_html = (
                '<div style="font-family:Inter,sans-serif;font-size:0.7rem;color:' + delta_color + ';margin-top:0.15rem;">'
                + str(delta) + '</div>'
            )
        items += (
            '<div style="flex:1;background:#141414;padding:1.1rem 1.5rem;">'
            '<div style="font-family:Titillium Web,sans-serif;font-size:0.58rem;font-weight:700;'
            'text-transform:uppercase;letter-spacing:0.16em;color:#444;margin-bottom:0.25rem;">'
            + m["label"] + '</div>'
            '<div style="font-family:Titillium Web,sans-serif;font-size:1.9rem;font-weight:900;'
            'color:' + color + ';line-height:1;">' + str(m["value"]) + '</div>'
            + delta_html +
            '</div>'
        )
    st.markdown(
        '<div style="display:flex;gap:1px;background:#2A2A2A;'
        'border-top:1px solid #2A2A2A;border-bottom:1px solid #2A2A2A;">'
        + items + '</div>',
        unsafe_allow_html=True
    )


def insight_box(icon, title, body, border="#E8002D", bg="#141414"):
    st.markdown(
        '<div style="background:' + bg + ';border:1px solid #2A2A2A;border-left:4px solid ' + border + ';'
        'padding:1.2rem 1.6rem;margin:0.8rem 0 1.4rem;">'
        '<div style="font-family:Titillium Web,sans-serif;font-size:0.62rem;font-weight:700;'
        'text-transform:uppercase;letter-spacing:0.18em;color:' + border + ';margin-bottom:0.5rem;">'
        + icon + '  ' + title + '</div>'
        '<div style="font-family:Inter,sans-serif;font-size:0.83rem;color:#CCC;line-height:1.7;">'
        + body + '</div>'
        '</div>',
        unsafe_allow_html=True
    )


def stat_row(items):
    cells = ""
    for lbl, val in items:
        cells += (
            '<div style="flex:1;min-width:120px;background:#1A1A1A;border:1px solid #2A2A2A;padding:0.8rem 1rem;">'
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


def content_wrap(inner_fn, *args, **kwargs):
    """Wrap page content in padded container."""
    st.markdown('<div style="padding:0 2.5rem 4rem;">', unsafe_allow_html=True)
    inner_fn(*args, **kwargs)
    st.markdown('</div>', unsafe_allow_html=True)