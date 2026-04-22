"""
app/main.py — Data Quality & Governance Accelerator
Streamlit entry point with CGI EDS branding and sidebar navigation.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from app.theme import apply as apply_theme, sidebar_logo, page_header

st.set_page_config(
    page_title="DQ & Governance Accelerator | CGI",
    page_icon="🔷",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply CGI EDS branding globally
apply_theme()


def _render_home():
    page_header(
        "Data Quality & Governance Accelerator",
        "Identify quality issues, governance gaps, and AI-readiness blockers — automatically.",
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.info(
            "**Structured Data**\n\n"
            "Upload a CSV or connect to a database table. "
            "Assess completeness, validity, PII, governance, and AI readiness."
        )
    with col2:
        st.info(
            "**Unstructured (PDF)**\n\n"
            "Upload policy or compliance documents. "
            "Scan against HIPAA, GDPR, FedRAMP, and governance best practices."
        )
    with col3:
        st.info(
            "**AI-Readiness Score**\n\n"
            "Get a weighted composite score, maturity tier, "
            "and prioritized remediation recommendations."
        )

    st.divider()
    st.markdown("### How it works")
    st.markdown("""
1. **Upload** your structured dataset (CSV) or compliance documents (PDF)
2. **Run** the automated assessment — rules engine + AI-powered gap analysis
3. **Review** your AI-Readiness Index, dimension scores, and findings
4. **Export** an executive summary and detailed findings report
    """)

    st.divider()
    st.caption("Built by CGI · Data Governance & AI Practice · Powered by Snowflake Cortex (Phase 2)")


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    sidebar_logo()

    page = st.radio(
        "Navigate",
        options=[
            "🏠 Home",
            "📋 Structured Assessment",
            "📄 Unstructured Assessment",
            "📈 Report",
            "❄️ Snowflake Setup",
        ],
        label_visibility="collapsed",
    )

    st.divider()
    st.caption("Phase 1 — Local Prototype")
    st.caption("Phase 2 — Snowflake / Cortex")

# ── Page routing ──────────────────────────────────────────────────────────────
if page == "🏠 Home":
    _render_home()
elif page == "📋 Structured Assessment":
    from app.pages import structured_assessment
    structured_assessment.render()
elif page == "📄 Unstructured Assessment":
    from app.pages import unstructured_assessment
    unstructured_assessment.render()
elif page == "📈 Report":
    from app.pages import report
    report.render()
elif page == "❄️ Snowflake Setup":
    from app.pages import snowflake_setup
    snowflake_setup.render()
