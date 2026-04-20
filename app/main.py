"""
app/main.py — Data Quality & Governance Accelerator
Streamlit entry point with sidebar navigation.
"""
import streamlit as st

st.set_page_config(
    page_title="DQ & Governance Accelerator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _render_home():
    st.title("Data Quality & Governance Accelerator")
    st.markdown(
        "An automated data readiness tool that identifies quality issues, "
        "governance gaps, and AI-readiness blockers — and tells you exactly how to fix them."
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("**Structured Data**\n\nUpload a CSV or connect to a database table. "
                "Assess completeness, validity, PII, governance, and AI readiness.")
    with col2:
        st.info("**Unstructured (PDF)**\n\nUpload policy or compliance documents. "
                "Scan against HIPAA, GDPR, FedRAMP, and governance best practices.")
    with col3:
        st.info("**AI-Readiness Score**\n\nGet a weighted composite score, maturity tier, "
                "and prioritized remediation recommendations.")

    st.divider()
    st.markdown("### How it works")
    st.markdown("""
1. **Upload** your structured dataset (CSV) or compliance documents (PDF)
2. **Run** the automated assessment — rules engine + AI-powered gap analysis
3. **Review** your AI-Readiness Index, dimension scores, and findings
4. **Export** an executive summary and detailed findings report
    """)

    st.divider()
    st.caption("Built by CGI · Powered by Snowflake Cortex (Phase 2)")


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📊 DQ Accelerator")
    st.markdown("*AI starts with data.*")
    st.divider()

    page = st.radio(
        "Navigate",
        options=[
            "🏠 Home",
            "📋 Structured Assessment",
            "📄 Unstructured Assessment",
            "📈 Report",
        ],
        label_visibility="collapsed",
    )

    st.divider()
    st.caption("Phase 1 — Local Prototype")
    st.caption("Phase 2 — Snowflake / Cortex")

# ── Pages ─────────────────────────────────────────────────────────────────────
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
