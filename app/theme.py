"""
app/theme.py
Injects CGI Experience Design System branding into Streamlit via st.markdown.
Call apply() once at the top of main.py before any other rendering.

Applies:
  - Source Sans Pro font (Google Fonts)
  - CGI EDS color tokens as CSS custom properties
  - Sidebar branding (header bar with CGI gradient accent)
  - EDS-styled metric cards, buttons, alerts, progress bars
  - CGI severity colors (critical/warning/info/success)
"""

import streamlit as st

# ── CGI logo as inline SVG (wordmark, 65.9×30.7px) ───────────────────────────
# Official CGI red wordmark — rendered as inline SVG so no file dependency
CGI_LOGO_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 132 61.4" width="66" height="31" aria-label="CGI">
  <path fill="#E31937" d="M0 30.7C0 13.7 13.7 0 30.7 0s30.7 13.7 30.7 30.7-13.7 30.7-30.7 30.7S0 47.7 0 30.7z"/>
  <path fill="#FFFFFF" d="M30.7 15.3c-8.5 0-15.4 6.9-15.4 15.4s6.9 15.4 15.4 15.4c4.3 0 8.1-1.7 10.9-4.5l-5.5-5.5c-1.4 1.4-3.3 2.3-5.4 2.3-4.2 0-7.7-3.4-7.7-7.7s3.4-7.7 7.7-7.7c2.1 0 4 .9 5.4 2.3l5.5-5.5c-2.8-2.8-6.6-4.5-10.9-4.5z"/>
  <text x="72" y="44" font-family="'Source Sans Pro', Arial, sans-serif" font-weight="700" font-size="38" fill="#3A2679">CGI</text>
</svg>
"""

_CSS = """
<style>
/* ── Google Fonts ─────────────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@400;600;700&display=swap');

/* ── EDS Tokens ───────────────────────────────────────────────────────────── */
:root {
    --eds-color-primary:          #3A2679;
    --eds-color-primary-hover:    #5236AB;
    --eds-color-primary-light:    #AFA3D8;
    --eds-color-primary-bg:       #E6E3F3;
    --eds-color-secondary:        #A21127;
    --eds-color-secondary-hover:  #E31937;
    --eds-color-error:            #B00020;
    --eds-color-error-bg:         #F7E6E9;
    --eds-color-success:          #1AB977;
    --eds-color-success-bg:       #E8F8F1;
    --eds-color-warning:          #F1A425;
    --eds-color-warning-bg:       #FEF6E9;
    --eds-color-surface:          #FFFFFF;
    --eds-color-background:       #FAFAFA;
    --eds-color-divider:          rgba(0,0,0,0.12);
    --eds-gradient-primary:       linear-gradient(90deg, #E31937 0%, #A82465 60%, #5236AB 100%);
    --eds-gradient-vertical:      linear-gradient(180deg, #E31937 0%, #A82465 40%, #5236AB 100%);
    --eds-elevation-1:            0px 2px 1px -1px rgba(0,0,0,0.2), 0px 1px 1px 0px rgba(0,0,0,0.14), 0px 1px 3px 0px rgba(0,0,0,0.12);
    --eds-radius-md:              4px;
    --eds-radius-lg:              8px;
    --eds-font-family:            'Source Sans Pro', Helvetica, Arial, sans-serif;
}

/* ── Global font ──────────────────────────────────────────────────────────── */
html, body, [class*="css"], .stApp {
    font-family: var(--eds-font-family) !important;
}

/* ── Sidebar: CGI brand treatment ────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background-color: #FFFFFF !important;
    border-right: 1px solid var(--eds-color-divider);
}

/* Gradient accent bar at top of sidebar (active nav indicator per EDS) */
[data-testid="stSidebar"]::before {
    content: "";
    display: block;
    height: 4px;
    background: var(--eds-gradient-primary);
    width: 100%;
}

[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    font-family: var(--eds-font-family) !important;
    color: rgba(0,0,0,0.87);
}

/* Radio nav items — EDS side nav item style */
[data-testid="stSidebar"] .stRadio label {
    font-family: var(--eds-font-family) !important;
    font-size: 14px;
    font-weight: 400;
    color: rgba(0,0,0,0.87);
    padding: 8px 12px;
    border-radius: 0;
    transition: background 200ms;
}

[data-testid="stSidebar"] .stRadio label:hover {
    background-color: var(--eds-color-primary-bg);
}

[data-testid="stSidebar"] .stRadio [aria-checked="true"] + div label,
[data-testid="stSidebar"] .stRadio input:checked ~ label {
    color: var(--eds-color-primary-hover);
    font-weight: 600;
}

/* ── Main content area ────────────────────────────────────────────────────── */
.main .block-container {
    padding-top: 1.5rem;
    max-width: 1200px;
}

/* ── Headings ─────────────────────────────────────────────────────────────── */
h1 {
    font-family: var(--eds-font-family) !important;
    font-size: 32px !important;
    font-weight: 700 !important;
    color: var(--eds-color-primary) !important;
    border-bottom: 3px solid;
    border-image: var(--eds-gradient-primary) 1;
    padding-bottom: 8px;
    margin-bottom: 16px;
}

h2 {
    font-family: var(--eds-font-family) !important;
    font-size: 24px !important;
    font-weight: 600 !important;
    color: var(--eds-color-primary) !important;
}

h3 {
    font-family: var(--eds-font-family) !important;
    font-size: 20px !important;
    font-weight: 600 !important;
    color: rgba(0,0,0,0.87) !important;
}

h4 {
    font-family: var(--eds-font-family) !important;
    font-size: 16px !important;
    font-weight: 600 !important;
    color: rgba(0,0,0,0.87) !important;
}

/* ── Primary button — EDS style (sharp corners per CGD-007) ──────────────── */
.stButton > button[kind="primary"],
.stButton > button {
    font-family: var(--eds-font-family) !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    border-radius: 0 !important;               /* CGD-007: sharp corners */
    background-color: var(--eds-color-primary) !important;
    color: #FFFFFF !important;
    border: none !important;
    padding: 8px 24px !important;
    transition: background-color 200ms !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}

.stButton > button:hover {
    background-color: var(--eds-color-primary-hover) !important;
}

.stButton > button:active {
    background-color: #200A58 !important;
}

/* ── Metric cards — EDS cgi-counter style ────────────────────────────────── */
[data-testid="stMetric"] {
    background-color: var(--eds-color-surface);
    border: 1px solid var(--eds-color-divider);
    border-top: 3px solid var(--eds-color-primary);
    border-radius: var(--eds-radius-md);
    padding: 16px !important;
    box-shadow: var(--eds-elevation-1);
}

[data-testid="stMetricLabel"] {
    font-family: var(--eds-font-family) !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    color: rgba(0,0,0,0.60) !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}

[data-testid="stMetricValue"] {
    font-family: var(--eds-font-family) !important;
    font-size: 28px !important;
    font-weight: 700 !important;
    color: var(--eds-color-primary) !important;
}

/* ── Info / warning / error / success alerts — EDS cgi-alert style ───────── */
[data-testid="stAlert"] {
    border-radius: var(--eds-radius-md) !important;
    font-family: var(--eds-font-family) !important;
    border-left-width: 4px !important;
}

/* st.info → EDS info (primary purple) */
[data-testid="stAlert"][data-baseweb="notification"] div[class*="Info"] {
    border-left-color: var(--eds-color-primary) !important;
    background-color: var(--eds-color-primary-bg) !important;
}

/* st.success → EDS success green */
[data-testid="stAlert"][data-baseweb="notification"] div[class*="Positive"] {
    border-left-color: var(--eds-color-success) !important;
    background-color: var(--eds-color-success-bg) !important;
}

/* st.warning → EDS warning pumpkin */
[data-testid="stAlert"][data-baseweb="notification"] div[class*="Warning"] {
    border-left-color: var(--eds-color-warning) !important;
    background-color: var(--eds-color-warning-bg) !important;
}

/* st.error → EDS error red */
[data-testid="stAlert"][data-baseweb="notification"] div[class*="Negative"] {
    border-left-color: var(--eds-color-error) !important;
    background-color: var(--eds-color-error-bg) !important;
}

/* ── Expander — EDS mat-card style ───────────────────────────────────────── */
[data-testid="stExpander"] {
    border: 1px solid var(--eds-color-divider) !important;
    border-radius: var(--eds-radius-md) !important;
    box-shadow: var(--eds-elevation-1) !important;
    margin-bottom: 8px !important;
}

[data-testid="stExpander"] summary {
    font-family: var(--eds-font-family) !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    padding: 12px 16px !important;
}

[data-testid="stExpander"]:has(summary[aria-expanded="true"]) {
    border-left: 3px solid var(--eds-color-primary) !important;
}

/* ── Dataframe / table — EDS mat-table style ─────────────────────────────── */
[data-testid="stDataFrame"] {
    border-radius: var(--eds-radius-md) !important;
    box-shadow: var(--eds-elevation-1) !important;
    overflow: hidden;
}

/* ── Progress bar — EDS gradient style ───────────────────────────────────── */
[data-testid="stProgress"] > div > div {
    background: var(--eds-gradient-primary) !important;
    border-radius: 0 !important;
}

/* ── Divider ──────────────────────────────────────────────────────────────── */
hr {
    border-color: var(--eds-color-divider) !important;
    margin: 24px 0 !important;
}

/* ── Caption / helper text ────────────────────────────────────────────────── */
[data-testid="stCaptionContainer"] {
    font-family: var(--eds-font-family) !important;
    font-size: 12px !important;
    color: rgba(0,0,0,0.60) !important;
}

/* ── Select / multiselect ─────────────────────────────────────────────────── */
[data-testid="stSelectbox"] label,
[data-testid="stMultiSelect"] label,
[data-testid="stTextInput"] label,
[data-testid="stRadio"] label {
    font-family: var(--eds-font-family) !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    color: rgba(0,0,0,0.87) !important;
}

/* ── File uploader ────────────────────────────────────────────────────────── */
[data-testid="stFileUploader"] {
    border: 2px dashed var(--eds-color-primary-light) !important;
    border-radius: var(--eds-radius-md) !important;
    padding: 16px !important;
}

/* ── Headstone card (EDS cgi-headstone) — used in score card ─────────────── */
.eds-headstone {
    background-color: var(--eds-color-primary-bg);
    border-radius: var(--eds-radius-md);
    padding: 16px;
    box-shadow: 0px 1px 2px 0px rgba(21,21,21,0.25);
    margin-bottom: 16px;
}

/* ── Severity badge chips ─────────────────────────────────────────────────── */
.eds-badge-critical {
    background-color: var(--eds-color-error-bg);
    color: var(--eds-color-error);
    border: 1px solid var(--eds-color-error);
    border-radius: var(--eds-radius-md);
    padding: 2px 8px;
    font-size: 12px;
    font-weight: 600;
    font-family: var(--eds-font-family);
}

.eds-badge-warning {
    background-color: var(--eds-color-warning-bg);
    color: #7A520A;
    border: 1px solid var(--eds-color-warning);
    border-radius: var(--eds-radius-md);
    padding: 2px 8px;
    font-size: 12px;
    font-weight: 600;
    font-family: var(--eds-font-family);
}

.eds-badge-info {
    background-color: var(--eds-color-primary-bg);
    color: var(--eds-color-primary);
    border: 1px solid var(--eds-color-primary-light);
    border-radius: var(--eds-radius-md);
    padding: 2px 8px;
    font-size: 12px;
    font-weight: 600;
    font-family: var(--eds-font-family);
}
</style>
"""

_SIDEBAR_LOGO = f"""
<div style="
    padding: 16px 16px 8px 16px;
    display: flex;
    align-items: center;
    gap: 10px;
    border-bottom: 1px solid rgba(0,0,0,0.12);
    margin-bottom: 8px;
">
    {CGI_LOGO_SVG}
    <div>
        <div style="
            font-family: 'Source Sans Pro', sans-serif;
            font-size: 13px;
            font-weight: 600;
            color: #991F3D;
            line-height: 1.2;
        ">DQ Accelerator</div>
        <div style="
            font-family: 'Source Sans Pro', sans-serif;
            font-size: 11px;
            font-weight: 400;
            color: rgba(0,0,0,0.60);
        ">AI starts with data</div>
    </div>
</div>
"""


def apply():
    """
    Apply CGI EDS branding to the Streamlit app.
    Call once at the top of main.py, before any page rendering.
    """
    st.markdown(_CSS, unsafe_allow_html=True)


def sidebar_logo():
    st.markdown("""
<div style="padding:16px 16px 8px 16px; border-bottom:1px solid rgba(0,0,0,0.12); margin-bottom:8px; display:flex; align-items:center; gap:10px;">
    <div style="width:32px; height:32px; background:#E31937; border-radius:50%; display:flex; align-items:center; justify-content:center;">
        <span style="color:white; font-weight:700; font-size:11px; font-family:sans-serif;">CGI</span>
    </div>
    <div>
        <div style="font-family:'Source Sans Pro',sans-serif; font-size:13px; font-weight:600; color:#991F3D; line-height:1.2;">DQ Accelerator</div>
        <div style="font-family:'Source Sans Pro',sans-serif; font-size:11px; font-weight:400; color:rgba(0,0,0,0.60);">AI starts with data</div>
    </div>
</div>
""", unsafe_allow_html=True)


def page_header(title: str, subtitle: str = ""):
    """
    Render an EDS-styled page header with the gradient underline.
    """
    st.markdown(f"# {title}")
    if subtitle:
        st.markdown(
            f"<p style='font-family:var(--eds-font-family); font-size:16px; "
            f"color:rgba(0,0,0,0.60); margin-top:-8px; margin-bottom:16px;'>"
            f"{subtitle}</p>",
            unsafe_allow_html=True,
        )


def headstone(items: list[dict]):
    """
    Render an EDS cgi-headstone card.
    items: list of {"label": str, "value": str, "footer": str (optional)}
    """
    items_html = ""
    for item in items:
        footer_html = (
            f"<div style='font-size:12px;color:rgba(0,0,0,0.60);margin-top:2px;'>"
            f"{item.get('footer','')}</div>"
            if item.get("footer") else ""
        )
        items_html += f"""
        <div style="min-width:120px;">
            <div style="font-size:12px;font-weight:600;color:rgba(0,0,0,0.60);
                        text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;">
                {item['label']}
            </div>
            <div style="font-size:20px;font-weight:700;color:#212121;">
                {item['value']}
            </div>
            {footer_html}
        </div>
        """

    st.markdown(
        f"""<div class="eds-headstone">
            <div style="display:flex;flex-wrap:wrap;gap:48px;font-family:var(--eds-font-family);">
                {items_html}
            </div>
        </div>""",
        unsafe_allow_html=True,
    )


def maturity_badge(tier: str, index: float) -> str:
    """Return an HTML badge string for the maturity tier."""
    colors = {
        "High Risk": ("var(--eds-color-error-bg)", "var(--eds-color-error)", "#7D0017"),
        "Moderate":  ("var(--eds-color-warning-bg)", "var(--eds-color-warning)", "#7A520A"),
        "AI Ready":  ("var(--eds-color-success-bg)", "var(--eds-color-success)", "#0E6641"),
    }
    bg, border, text = colors.get(tier, ("#F2F1F9", "#3A2679", "#200A58"))
    return (
        f"<span style='background:{bg};color:{text};border:1px solid {border};"
        f"border-radius:4px;padding:4px 12px;font-size:14px;font-weight:600;"
        f"font-family:var(--eds-font-family);'>{tier} — {index:.0f}/100</span>"
    )
