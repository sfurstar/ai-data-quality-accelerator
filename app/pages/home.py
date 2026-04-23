"""
app/pages/home.py
Product landing page for the CGI DQ & Governance Accelerator.
"""
from __future__ import annotations
import os
import streamlit as st
from app.theme import page_header


def render():
    page_header(
        "Data Quality & Governance Accelerator",
        "Identify quality issues, governance gaps, and AI-readiness blockers — automatically."
    )

    # ── Phase 2 status banner ─────────────────────────────────────────────────
    sf_active = bool(os.environ.get("SNOWFLAKE_ACCOUNT"))
    if sf_active:
        st.success(
            "✅ **Phase 2 active** — Connected to Snowflake · Cortex LLM enabled · "
            "Results persisted to DQ_ACCELERATOR.ASSESSMENTS",
            icon=None,
        )

    st.markdown("<div style='margin-top:8px'></div>", unsafe_allow_html=True)

    # ── Capability cards ──────────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div style="background:#F2F1F9;border-radius:8px;padding:24px;height:160px;
                    border-left:4px solid #3A2679;">
            <div style="font-size:22px;margin-bottom:8px;">📋</div>
            <div style="font-family:Source Sans Pro,sans-serif;font-size:16px;
                        font-weight:700;color:#3A2679;margin-bottom:6px;">Structured Data</div>
            <div style="font-family:Source Sans Pro,sans-serif;font-size:13px;
                        color:rgba(0,0,0,0.65);line-height:1.5;">
                Upload a CSV or connect to a Snowflake table. Assess completeness,
                validity, PII, governance, and AI readiness.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="background:#F2F1F9;border-radius:8px;padding:24px;height:160px;
                    border-left:4px solid #E31937;">
            <div style="font-size:22px;margin-bottom:8px;">📄</div>
            <div style="font-family:Source Sans Pro,sans-serif;font-size:16px;
                        font-weight:700;color:#3A2679;margin-bottom:6px;">Unstructured (PDF)</div>
            <div style="font-family:Source Sans Pro,sans-serif;font-size:13px;
                        color:rgba(0,0,0,0.65);line-height:1.5;">
                Upload policy or compliance documents. Scan against HIPAA, GDPR,
                FedRAMP, and governance best practices.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div style="background:#F2F1F9;border-radius:8px;padding:24px;height:160px;
                    border-left:4px solid #128354;">
            <div style="font-size:22px;margin-bottom:8px;">✨</div>
            <div style="font-family:Source Sans Pro,sans-serif;font-size:16px;
                        font-weight:700;color:#3A2679;margin-bottom:6px;">AI-Readiness Score</div>
            <div style="font-family:Source Sans Pro,sans-serif;font-size:13px;
                        color:rgba(0,0,0,0.65);line-height:1.5;">
                Get a weighted composite score, maturity tier, and prioritized
                remediation recommendations powered by Cortex.
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-top:32px'></div>", unsafe_allow_html=True)

    # ── How it works ─────────────────────────────────────────────────────────
    st.markdown("### How it works")

    steps = [
        ("1", "#3A2679", "Upload or connect",
         "Upload a CSV, point to a Snowflake table, or load a PDF from your S3 stage."),
        ("2", "#E31937", "Run the assessment",
         "The rules engine checks quality dimensions and compliance standards automatically."),
        ("3", "#854F0B", "Review AI findings",
         "Cortex LLM adds narrative gap analysis and prioritized recommendations beyond rules."),
        ("4", "#128354", "Export & act",
         "Download findings as CSV, Excel, or JSON. Save results to Snowflake for tracking."),
    ]

    cols = st.columns(4)
    for col, (num, color, title, desc) in zip(cols, steps):
        with col:
            st.markdown(f"""
            <div style="text-align:center;padding:16px 8px;">
                <div style="width:40px;height:40px;border-radius:50%;background:{color};
                            display:flex;align-items:center;justify-content:center;
                            margin:0 auto 12px auto;">
                    <span style="color:white;font-weight:700;font-size:16px;">{num}</span>
                </div>
                <div style="font-family:Source Sans Pro,sans-serif;font-size:14px;
                            font-weight:700;color:#3A2679;margin-bottom:6px;">{title}</div>
                <div style="font-family:Source Sans Pro,sans-serif;font-size:12px;
                            color:rgba(0,0,0,0.60);line-height:1.5;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='margin-top:24px'></div>", unsafe_allow_html=True)

    # ── Maturity scale reference ──────────────────────────────────────────────
    st.markdown("### AI-Readiness maturity tiers")

    tiers = [
        ("#B00020", "High Risk", "0–40", "Critical gaps — not ready for AI workloads"),
        ("#854F0B", "Moderate",  "41–70", "Significant gaps — remediation required"),
        ("#128354", "AI Ready",  "71–100", "Meets governance and quality thresholds for AI"),
    ]

    tier_html = '<div style="display:flex;gap:12px;margin-top:8px;flex-wrap:wrap;">'
    for color, label, range_, desc in tiers:
        tier_html += f"""
        <div style="flex:1;min-width:180px;background:white;border:1px solid {color};
                    border-left:5px solid {color};border-radius:6px;padding:14px 16px;">
            <div style="font-family:Source Sans Pro,sans-serif;font-size:15px;
                        font-weight:700;color:{color};">{label}</div>
            <div style="font-family:Source Sans Pro,sans-serif;font-size:20px;
                        font-weight:700;color:{color};margin:2px 0;">{range_}</div>
            <div style="font-family:Source Sans Pro,sans-serif;font-size:12px;
                        color:rgba(0,0,0,0.60);">{desc}</div>
        </div>"""
    tier_html += '</div>'
    st.markdown(tier_html, unsafe_allow_html=True)

    st.markdown("<div style='margin-top:40px'></div>", unsafe_allow_html=True)

    # ── Footer ────────────────────────────────────────────────────────────────
    st.markdown(
        "<p style='font-family:Source Sans Pro,sans-serif;font-size:12px;"
        "color:rgba(0,0,0,0.40);text-align:center;'>"
        "Built by CGI · Data Governance & AI Practice · "
        "Powered by Snowflake Cortex (Phase 2)"
        "</p>",
        unsafe_allow_html=True,
    )
