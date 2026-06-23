"""
Global F1-branded UI theme for Streamlit pages.
Import and call inject_f1_css() at the top of every page.
"""
import streamlit as st

# ── Palette constants (also used in matplotlib charts) ────────────────────────
F1_RED       = "#E8002D"
F1_BLACK     = "#0D0D0D"
F1_CARD      = "#141414"
F1_CARD2     = "#1C1C1C"
F1_BORDER    = "#2A2A2A"
F1_WHITE     = "#FFFFFF"
F1_GREY      = "#888888"
F1_GOLD      = "#FFD700"
F1_TEAL      = "#27F4D2"
F1_BLUE      = "#3671C6"
F1_GREEN     = "#27AE60"

COMPOUND_COLORS = {
    "SOFT":         "#DA291C",
    "MEDIUM":       "#FFD700",
    "HARD":         "#E8E8E8",
    "INTERMEDIATE": "#43B02A",
    "WET":          "#0067AD",
    "UNKNOWN":      "#888888",
}

TEAM_COLORS = {
    "Red Bull":     "#3671C6",
    "Ferrari":      "#E8002D",
    "Mercedes":     "#27F4D2",
    "McLaren":      "#FF8000",
    "Aston Martin": "#358C75",
    "Alpine":       "#FF87BC",
    "Williams":     "#64C4FF",
    "RB":           "#6692FF",
    "Haas":         "#B6BABD",
    "Sauber":       "#52E252",
}


def inject_f1_css() -> None:
    """Inject the full F1-branded stylesheet into the Streamlit app."""
    st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Titillium+Web:wght@300;400;600;700;900&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">

<style>
/* ── Instant base — applied before anything else renders ─────────────── */
html { background: #0D0D0D !important; }
body { background: #0D0D0D !important; }
[data-testid="stAppViewContainer"] { background: #0D0D0D !important; }
[data-testid="stApp"] { background: #0D0D0D !important; }

/* ── Reset & base ─────────────────────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; }

html, body, .stApp {
    background-color: #0D0D0D !important;
    color: #FFFFFF;
    font-family: 'Inter', system-ui, sans-serif;
}

/* ── Hide Streamlit chrome we don't want ─────────────────────────────── */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
/* Keep header visible so the sidebar collapse arrow remains accessible */
header[data-testid="stHeader"] { background: transparent !important; }
.stDeployButton { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }

/* ── Sidebar ─────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: #0D0D0D !important;
    border-right: 1px solid #2A2A2A !important;
    padding-top: 0 !important;
}
[data-testid="stSidebar"] > div:first-child {
    padding-top: 1rem;
}
/* ── Sidebar nav links — styled, NOT hidden ──────────────────────────── */
[data-testid="stSidebarNav"] {
    padding-top: 0.5rem;
    padding-bottom: 0.5rem;
}
[data-testid="stSidebarNav"] a {
    display: flex !important;
    align-items: center !important;
    padding: 0.45rem 0.8rem !important;
    border-left: 3px solid transparent !important;
    border-radius: 0 !important;
    text-decoration: none !important;
    transition: all 0.12s !important;
    margin: 1px 0 !important;
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
    font-size: 0.75rem !important;
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
    font-size: 0.6rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.2em;
    color: #444;
    padding: 0 0.8rem 0.5rem;
    border-bottom: 1px solid #2A2A2A;
    margin-bottom: 0.3rem;
}
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stMarkdown p {
    color: #CCCCCC !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.82rem !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #FFFFFF !important;
    font-family: 'Titillium Web', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.9rem !important;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    border-bottom: 1px solid #2A2A2A;
    padding-bottom: 0.5rem;
    margin-bottom: 0.8rem;
}
[data-testid="stSidebar"] .stButton > button {
    width: 100%;
    background: #E8002D !important;
    color: #FFFFFF !important;
    font-family: 'Titillium Web', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.85rem !important;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    border: none !important;
    border-radius: 2px !important;
    padding: 0.6rem 1rem !important;
    cursor: pointer;
    transition: background 0.15s;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: #C0001F !important;
}
[data-testid="stSidebar"] .stSelectbox > div > div,
[data-testid="stSidebar"] .stTextInput > div > div > input,
[data-testid="stSidebar"] .stNumberInput > div > div > input {
    background: #1A1A1A !important;
    border: 1px solid #2A2A2A !important;
    color: #FFFFFF !important;
    border-radius: 2px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.85rem !important;
}
[data-testid="stSidebar"] .stSelectbox > div > div:hover,
[data-testid="stSidebar"] .stTextInput > div > div > input:focus {
    border-color: #E8002D !important;
}

/* ── Main content area ───────────────────────────────────────────────── */
.main .block-container {
    padding: 0 !important;
    max-width: 100% !important;
}

/* ── Page header bar ─────────────────────────────────────────────────── */
.f1-page-header {
    background: #141414;
    border-bottom: 3px solid #E8002D;
    padding: 1.4rem 2.5rem 1.2rem;
    margin-bottom: 0;
    display: flex;
    align-items: flex-end;
    gap: 1.5rem;
}
.f1-page-header .page-icon {
    font-size: 2rem;
    line-height: 1;
}
.f1-page-header .page-title-block {}
.f1-page-header .page-eyebrow {
    font-family: 'Titillium Web', sans-serif;
    font-size: 0.65rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.2em;
    color: #E8002D;
    margin: 0 0 0.15rem;
}
.f1-page-header h1 {
    font-family: 'Titillium Web', sans-serif !important;
    font-size: 2rem !important;
    font-weight: 900 !important;
    color: #FFFFFF !important;
    margin: 0 !important;
    padding: 0 !important;
    line-height: 1.1 !important;
    text-transform: uppercase;
    letter-spacing: -0.01em;
}
.f1-page-header .page-desc {
    font-size: 0.82rem;
    color: #888888;
    margin: 0.3rem 0 0;
    font-family: 'Inter', sans-serif;
    max-width: 60ch;
}

/* ── Section labels ──────────────────────────────────────────────────── */
.f1-section {
    font-family: 'Titillium Web', sans-serif;
    font-size: 0.65rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.2em;
    color: #E8002D;
    margin: 2rem 2.5rem 0.6rem;
    padding-bottom: 0.4rem;
    border-bottom: 1px solid #2A2A2A;
}

/* ── Metric cards row ────────────────────────────────────────────────── */
.f1-metrics {
    display: flex;
    gap: 1px;
    background: #2A2A2A;
    border-top: 1px solid #2A2A2A;
    border-bottom: 1px solid #2A2A2A;
    margin-bottom: 0;
}
.f1-metric {
    flex: 1;
    background: #141414;
    padding: 1.1rem 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
}
.f1-metric .m-label {
    font-family: 'Titillium Web', sans-serif;
    font-size: 0.6rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    color: #666666;
}
.f1-metric .m-value {
    font-family: 'Titillium Web', sans-serif;
    font-size: 1.9rem;
    font-weight: 900;
    color: #FFFFFF;
    line-height: 1;
}
.f1-metric .m-value.accent { color: #E8002D; }
.f1-metric .m-value.gold   { color: #FFD700; }
.f1-metric .m-value.teal   { color: #27F4D2; }
.f1-metric .m-delta {
    font-family: 'Inter', sans-serif;
    font-size: 0.72rem;
    color: #888888;
}
.f1-metric .m-delta.pos { color: #27AE60; }
.f1-metric .m-delta.neg { color: #E8002D; }

/* ── Content panels ──────────────────────────────────────────────────── */
.f1-panel {
    background: #141414;
    border: 1px solid #2A2A2A;
    margin: 1.5rem 2rem;
    border-radius: 0;
}
.f1-panel-header {
    background: #1C1C1C;
    border-bottom: 1px solid #2A2A2A;
    padding: 0.7rem 1.2rem;
    font-family: 'Titillium Web', sans-serif;
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    color: #CCCCCC;
    display: flex;
    align-items: center;
    gap: 0.6rem;
}
.f1-panel-header::before {
    content: '';
    display: inline-block;
    width: 3px;
    height: 0.85em;
    background: #E8002D;
}
.f1-panel-body {
    padding: 1.2rem;
}

/* ── Data table override ─────────────────────────────────────────────── */
.stDataFrame {
    border: 1px solid #2A2A2A !important;
    border-radius: 0 !important;
}
.stDataFrame table {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.8rem !important;
}
.stDataFrame thead tr th {
    background: #1C1C1C !important;
    color: #888888 !important;
    font-family: 'Titillium Web', sans-serif !important;
    font-size: 0.65rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
    border-bottom: 2px solid #E8002D !important;
}
.stDataFrame tbody tr:nth-child(even) td { background: #161616 !important; }
.stDataFrame tbody tr:hover td { background: #1C1C1C !important; }

/* ── st.metric override ──────────────────────────────────────────────── */
[data-testid="stMetric"] {
    background: #141414 !important;
    border: 1px solid #2A2A2A !important;
    border-top: 2px solid #E8002D !important;
    padding: 1rem 1.2rem !important;
    border-radius: 0 !important;
}
[data-testid="stMetricLabel"] {
    font-family: 'Titillium Web', sans-serif !important;
    font-size: 0.62rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.15em !important;
    color: #666666 !important;
}
[data-testid="stMetricValue"] {
    font-family: 'Titillium Web', sans-serif !important;
    font-size: 1.7rem !important;
    font-weight: 900 !important;
    color: #FFFFFF !important;
}
[data-testid="stMetricDelta"] {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.75rem !important;
}

/* ── Alert/info boxes ────────────────────────────────────────────────── */
.stAlert {
    border-radius: 0 !important;
    border-left-width: 3px !important;
    background: #141414 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.83rem !important;
}

/* ── Tabs ────────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    background: #141414 !important;
    border-bottom: 2px solid #2A2A2A !important;
    gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'Titillium Web', sans-serif !important;
    font-size: 0.72rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.12em !important;
    color: #666666 !important;
    padding: 0.8rem 1.5rem !important;
    border-bottom: 3px solid transparent !important;
    background: transparent !important;
}
.stTabs [aria-selected="true"] {
    color: #FFFFFF !important;
    border-bottom: 3px solid #E8002D !important;
}

/* ── Spinner ─────────────────────────────────────────────────────────── */
.stSpinner > div {
    border-top-color: #E8002D !important;
}

/* ── Scrollbar ───────────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0D0D0D; }
::-webkit-scrollbar-thumb { background: #2A2A2A; border-radius: 0; }
::-webkit-scrollbar-thumb:hover { background: #E8002D; }

/* ── Sidebar nav links ───────────────────────────────────────────────── */
.f1-nav {
    padding: 0.5rem 0;
    border-bottom: 1px solid #2A2A2A;
    margin-bottom: 1rem;
}
.f1-nav-item {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.45rem 0.8rem;
    text-decoration: none !important;
    border-left: 3px solid transparent;
    cursor: pointer;
    transition: all 0.1s;
    margin: 1px 0;
}
.f1-nav-item:hover {
    background: #1A1A1A;
    border-left-color: #E8002D;
}
.f1-nav-item.active {
    background: #1A1A1A;
    border-left-color: #E8002D;
}
.f1-nav-item .nav-icon { font-size: 0.9rem; }
.f1-nav-item .nav-label {
    font-family: 'Titillium Web', sans-serif;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #CCCCCC;
}

/* ── Chart containers ────────────────────────────────────────────────── */
.stPlotlyChart, .stImage, [data-testid="stImage"] {
    border: 1px solid #2A2A2A !important;
    background: #0D0D0D !important;
}

/* ── Divider ─────────────────────────────────────────────────────────── */
hr { border-color: #2A2A2A !important; margin: 0 !important; }

/* ── Global padding for page content ────────────────────────────────── */
.f1-content {
    padding: 0 2.5rem 3rem;
}

/* ── Status badge ────────────────────────────────────────────────────── */
.f1-badge {
    display: inline-block;
    font-family: 'Titillium Web', sans-serif;
    font-size: 0.62rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    padding: 0.2rem 0.6rem;
    border-radius: 1px;
}
.f1-badge.red   { background: #E8002D; color: white; }
.f1-badge.grey  { background: #2A2A2A; color: #888; }
.f1-badge.gold  { background: #FFD700; color: #0D0D0D; }
.f1-badge.green { background: #27AE60; color: white; }
.f1-badge.teal  { background: #27F4D2; color: #0D0D0D; }

/* ── Compound pill ───────────────────────────────────────────────────── */
.compound-soft  { color: #DA291C; font-weight: 700; }
.compound-med   { color: #FFD700; font-weight: 700; }
.compound-hard  { color: #E8E8E8; font-weight: 700; }
.compound-inter { color: #43B02A; font-weight: 700; }
.compound-wet   { color: #0067AD; font-weight: 700; }

/* ── Success/error states ────────────────────────────────────────────── */
.stSuccess { border-left-color: #27AE60 !important; }
.stError   { border-left-color: #E8002D !important; }
.stWarning { border-left-color: #FFD700 !important; }
.stInfo    { border-left-color: #3671C6 !important; }

/* ── Radio buttons ───────────────────────────────────────────────────── */
[data-testid="stRadio"] label {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.82rem !important;
    color: #CCCCCC !important;
}

/* ── Slider ──────────────────────────────────────────────────────────── */
[data-testid="stSlider"] > div > div > div > div {
    background: #E8002D !important;
}

/* ── Checkbox ────────────────────────────────────────────────────────── */
[data-testid="stCheckbox"] label {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.82rem !important;
    color: #CCCCCC !important;
}
</style>
""", unsafe_allow_html=True)


def page_header(icon: str, eyebrow: str, title: str, description: str = "") -> None:
    """Render the standard F1-style page header bar."""
    desc_html = f'<p class="page-desc">{description}</p>' if description else ""
    st.markdown(f"""
<div class="f1-page-header">
    <div class="page-icon">{icon}</div>
    <div class="page-title-block">
        <p class="page-eyebrow">{eyebrow}</p>
        <h1>{title}</h1>
        {desc_html}
    </div>
</div>
""", unsafe_allow_html=True)


def section_label(text: str) -> None:
    """Render a red uppercase section divider label."""
    st.markdown(f'<div class="f1-section">{text}</div>', unsafe_allow_html=True)


def metrics_row(metrics: list[dict]) -> None:
    """
    Render a horizontal metrics strip.
    Each dict: { label, value, delta="", color="" }
    color options: "accent", "gold", "teal" (default = white)
    """
    items_html = ""
    for m in metrics:
        color_cls = m.get("color", "")
        delta     = m.get("delta", "")
        delta_cls = ""
        if delta:
            if str(delta).startswith("+") or str(delta).startswith("▲"):
                delta_cls = "pos"
            elif str(delta).startswith("-") or str(delta).startswith("▼"):
                delta_cls = "neg"
        delta_html = f'<div class="m-delta {delta_cls}">{delta}</div>' if delta else ""
        items_html += f"""
<div class="f1-metric">
    <div class="m-label">{m["label"]}</div>
    <div class="m-value {color_cls}">{m["value"]}</div>
    {delta_html}
</div>"""
    st.markdown(f'<div class="f1-metrics">{items_html}</div>', unsafe_allow_html=True)


def panel(title: str, content_fn, *args, **kwargs) -> None:
    """Render a titled panel card and call content_fn() inside it."""
    st.markdown(f"""
<div class="f1-panel">
    <div class="f1-panel-header">{title}</div>
    <div class="f1-panel-body">
""", unsafe_allow_html=True)
    content_fn(*args, **kwargs)
    st.markdown("</div></div>", unsafe_allow_html=True)


def sidebar_nav(current_page: str = "") -> None:
    """Render a custom nav menu in the sidebar."""
    pages = [
        ("🏠", "Home",               "app"),
        ("📊", "Session Deep Dive",  "1_Deep_Dive"),
        ("⚔️",  "Head-to-Head",       "2_Head_to_Head"),
        ("🏆", "Championship",       "3_Season_Championship"),
        ("🗺️",  "Track Speed Map",    "4_Track_Speed_Map"),
        ("🤖", "ML Predictions",     "5_Single_Race_Predict"),
        ("📖", "Race Story",         "6_Race_Story"),
        ("⏱️",  "Quali Delta",        "7_Quali_Delta"),
        ("🛞", "Pit Window",         "8_Pit_Window"),
        ("📈", "Multi-Season",       "9_Multi_Season"),
    ]
    nav_html = '<div class="f1-nav">'
    for icon, label, key in pages:
        active = "active" if key == current_page else ""
        nav_html += f"""
<div class="f1-nav-item {active}">
    <span class="nav-icon">{icon}</span>
    <span class="nav-label">{label}</span>
</div>"""
    nav_html += "</div>"
    st.sidebar.markdown(nav_html, unsafe_allow_html=True)


def apply_chart_style(fig, ax_or_axes=None) -> None:
    """Apply F1 dark theme to a matplotlib figure."""
    import matplotlib.pyplot as plt
    fig.patch.set_facecolor("#0D0D0D")
    axes = ax_or_axes if ax_or_axes is not None else fig.get_axes()
    if not hasattr(axes, "__iter__"):
        axes = [axes]
    for ax in axes:
        ax.set_facecolor("#0D0D0D")
        ax.tick_params(colors="#888888", labelsize=8)
        ax.xaxis.label.set_color("#888888")
        ax.yaxis.label.set_color("#888888")
        ax.xaxis.label.set_fontsize(8)
        ax.yaxis.label.set_fontsize(8)
        for spine in ax.spines.values():
            spine.set_edgecolor("#2A2A2A")
        ax.grid(True, alpha=0.12, color="#FFFFFF", linewidth=0.5)
        ax.set_title(ax.get_title(), color="#FFFFFF", fontsize=10,
                     fontfamily="sans-serif", fontweight="bold")