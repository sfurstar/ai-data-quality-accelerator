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

_SIDEBAR_LOGO = (
    '<div style="padding:16px 16px 12px 16px;border-bottom:1px solid rgba(0,0,0,0.12);margin-bottom:8px;">' +
    '<img src="data:image/png;base64,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" style="height:30px;width:auto;display:block;margin-bottom:8px;" alt="CGI">' +
    '<div style="font-family:Source Sans Pro,sans-serif;font-size:13px;font-weight:600;color:#991F3D;line-height:1.2;">DQ Accelerator</div>' +
    '<div style="font-family:Source Sans Pro,sans-serif;font-size:11px;font-weight:400;color:rgba(0,0,0,0.60);">AI starts with data</div>' +
    '</div>'
)


def apply():
    """
    Apply CGI EDS branding to the Streamlit app.
    Call once at the top of main.py, before any page rendering.
    """
    st.markdown(_CSS, unsafe_allow_html=True)


def sidebar_logo():
    """
    Render the CGI logo + app name in the sidebar.
    Call inside a `with st.sidebar:` block.
    """
    st.markdown(_SIDEBAR_LOGO, unsafe_allow_html=True)


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
        f"""<div style="background-color:#E6E3F3;border-radius:4px;padding:16px;
                        box-shadow:0px 1px 2px 0px rgba(21,21,21,0.25);margin-bottom:16px;">
            <div style="display:flex;flex-wrap:wrap;gap:48px;
                        font-family:'Source Sans Pro',Helvetica,Arial,sans-serif;">
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
