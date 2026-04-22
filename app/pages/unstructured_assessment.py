"""
app/pages/unstructured_assessment.py
PDF compliance document assessment page.
"""
from __future__ import annotations

import io
from pathlib import Path

import streamlit as st

from engine import AssessmentResult, Dimension
from engine.unstructured.pdf_extractor import extract
from engine.unstructured.compliance_scanner import run as scan_compliance, get_coverage_summary
from engine.unstructured.llm_analyzer import analyze as llm_analyze
from engine.scoring.scorer import build_result
from app.components.score_card import render_score_card
from app.components.findings_table import render_findings_table
from app.theme import page_header

_SAMPLE_DIR = Path(__file__).parents[2] / "data" / "sample" / "unstructured"

_AVAILABLE_STANDARDS = ["HIPAA", "GDPR", "FedRAMP", "GOVERNANCE"]


def render():
    page_header("Unstructured Document Assessment", "Scan compliance and policy documents against HIPAA, GDPR, FedRAMP, and governance standards.")
    st.markdown(
        "Upload one or more policy or compliance documents (PDF) to scan for "
        "regulatory gaps across HIPAA, GDPR, FedRAMP, and data governance best practices."
    )

    # ── Source selection ─────────────────────────────────────────────────────
    source_option = st.radio(
        "Document source",
        ["Upload PDF(s)", "Use sample documents"],
        horizontal=True,
    )

    uploaded_files = []
    source_label = ""

    if source_option == "Upload PDF(s)":
        files = st.file_uploader(
            "Upload PDF documents",
            type=["pdf"],
            accept_multiple_files=True,
            label_visibility="collapsed",
        )
        if files:
            uploaded_files = files
    else:
        uploaded_files, source_label = _load_sample_docs()
        if uploaded_files:
            st.success(f"✅ {len(uploaded_files)} sample document(s) loaded")

    if not uploaded_files:
        st.info("👆 Upload PDF documents or select sample documents to begin.")
        _render_sample_info()
        return

    # ── Standards selection ──────────────────────────────────────────────────
    selected_standards = st.multiselect(
        "Compliance standards to check",
        options=_AVAILABLE_STANDARDS,
        default=_AVAILABLE_STANDARDS,
    )
    use_llm = False  # Phase 2: enable when Snowflake Cortex is configured
    st.caption("AI-powered gap analysis (Cortex COMPLETE) will be enabled in Phase 2 — Snowflake integration.")

    # ── Run ──────────────────────────────────────────────────────────────────
    if st.button("▶ Run Assessment", type="primary", use_container_width=True):
        results = []
        for f in uploaded_files:
            result = _assess_document(f, selected_standards, use_llm)
            if result:
                results.append((f.name if hasattr(f, "name") else str(f), result))

        st.session_state["unstructured_results"] = results

    # ── Display results ──────────────────────────────────────────────────────
    if "unstructured_results" in st.session_state:
        _render_results(st.session_state["unstructured_results"])


def _assess_document(file_obj, standards: list[str], use_llm: bool) -> AssessmentResult | None:
    name = file_obj.name if hasattr(file_obj, "name") else str(file_obj)

    with st.spinner(f"Assessing {name}..."):
        try:
            # 1. Extract text
            extraction = extract(file_obj)
            text = extraction["text"]

            if not text.strip():
                st.warning(f"⚠️ Could not extract text from {name}. File may be scanned/image-only.")
                return None

            # 2. Rule-based compliance scan
            comp_findings = scan_compliance(text, standards)

            # 3. LLM gap analysis
            llm_result = {"summary": "", "gaps": [], "recommendations": [], "error": None}
            if use_llm:
                llm_result = llm_analyze(text, document_name=name, standards=standards)
                if llm_result.get("error"):
                    st.warning(f"LLM analysis note: {llm_result['error']}")

            # 4. Score
            findings_by_dim = {Dimension.COMPLIANCE: comp_findings}
            result = build_result(name, "unstructured", findings_by_dim)

            # Attach extras to metadata
            result.metadata["extraction"] = {
                "page_count": extraction["page_count"],
                "word_count": extraction["word_count"],
                "extractor": extraction["extractor"],
            }
            result.metadata["llm"] = llm_result
            result.metadata["coverage"] = get_coverage_summary(text, standards)

            return result

        except Exception as e:
            st.error(f"Error assessing {name}: {e}")
            return None


def _render_results(results: list[tuple[str, AssessmentResult]]):
    st.divider()

    for name, result in results:
        st.markdown(f"### 📄 {name}")
        meta = result.metadata

        # Extraction info
        if "extraction" in meta:
            ext = meta["extraction"]
            st.caption(
                f"Pages: {ext['page_count']} · Words: {ext['word_count']:,} · "
                f"Extractor: {ext['extractor']}"
            )

        # Score card
        render_score_card(result)

        # Coverage summary table
        if "coverage" in meta:
            st.markdown("#### Standard coverage")
            _render_coverage_table(meta["coverage"])

        # LLM analysis
        if "llm" in meta and not meta["llm"].get("error"):
            llm = meta["llm"]
            if llm.get("summary"):
                st.markdown("#### AI gap analysis")
                st.info(llm["summary"])

            if llm.get("gaps"):
                with st.expander("Identified gaps (AI-powered)", expanded=True):
                    for gap in llm["gaps"]:
                        st.markdown(f"- {gap}")

            if llm.get("recommendations"):
                with st.expander("Recommended actions (AI-powered)", expanded=True):
                    for i, rec in enumerate(llm["recommendations"], 1):
                        st.markdown(f"**{i}.** {rec}")

        # Findings table
        st.markdown("#### Rule-based findings")
        render_findings_table(result.all_findings)
        st.divider()


def _render_coverage_table(coverage: dict):
    import pandas as pd

    rows = []
    for std_key, data in coverage.items():
        score = data["score"]
        status = "🟢" if score >= 70 else "🟡" if score >= 40 else "🔴"
        rows.append({
            "Standard": f"{status} {std_key}",
            "Full name": data["full_name"],
            "Rules passed": data["passed"],
            "Rules failed": data["failed"],
            "Score": f"{score}%",
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)


def _render_sample_info():
    with st.expander("What kinds of documents can be assessed?"):
        st.markdown("""
**Government policy & compliance documents:**
- Data governance policies
- Privacy policies and notices
- Information security policies
- HIPAA compliance plans
- Data retention schedules
- System security plans (SSPs)
- Records management policies

**What we check:**
- HIPAA: breach notification, PHI handling, physical safeguards, de-identification
- GDPR: consent language, right to erasure, retention periods, DPO, cross-border transfers
- FedRAMP: account management, audit logging, patch management, encryption at rest
- Governance: data ownership, classification schemes, lineage documentation
        """)


def _load_sample_docs():
    """Load sample PDF documents from data/sample/unstructured/ if present."""
    if not _SAMPLE_DIR.exists():
        st.warning(
            "No sample documents found. Place PDF files in "
            f"`{_SAMPLE_DIR}` or upload your own."
        )
        return [], ""

    pdfs = list(_SAMPLE_DIR.glob("*.pdf"))
    if not pdfs:
        st.warning(f"No PDF files found in `{_SAMPLE_DIR}`. Upload your own documents.")
        return [], ""

    # Return as file-like objects with .name attribute
    file_objs = []
    for p in pdfs[:3]:  # Limit to 3 for demo
        with open(p, "rb") as f:
            buf = io.BytesIO(f.read())
            buf.name = p.name
            file_objs.append(buf)

    return file_objs, f"{len(file_objs)} sample documents"
