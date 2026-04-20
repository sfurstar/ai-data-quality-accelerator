"""
app/pages/report.py
Combined report view — aggregates structured + unstructured results,
renders executive summary, and provides export options.
"""
from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from engine import AssessmentResult, Severity


def render():
    st.title("📈 Assessment Report")

    structured: AssessmentResult | None = st.session_state.get("structured_result")
    unstructured_list: list[tuple[str, AssessmentResult]] = st.session_state.get("unstructured_results", [])

    if not structured and not unstructured_list:
        st.info("No assessments run yet. Go to **Structured Assessment** or **Unstructured Assessment** to run an assessment first.")
        return

    # ── Executive summary header ─────────────────────────────────────────────
    st.markdown(f"*Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}*")
    st.divider()

    # ── Structured results ───────────────────────────────────────────────────
    if structured:
        st.markdown("## Structured Data Assessment")
        _render_result_summary(structured)
        st.divider()

    # ── Unstructured results ─────────────────────────────────────────────────
    if unstructured_list:
        st.markdown("## Document Compliance Assessment")
        for doc_name, result in unstructured_list:
            st.markdown(f"### {doc_name}")
            _render_result_summary(result)
            if "coverage" in result.metadata:
                _render_mini_coverage(result.metadata["coverage"])
            st.divider()

    # ── Combined finding counts ──────────────────────────────────────────────
    all_results = []
    if structured:
        all_results.append(structured)
    for _, r in unstructured_list:
        all_results.append(r)

    if len(all_results) > 1:
        _render_combined_summary(all_results)

    # ── Export ───────────────────────────────────────────────────────────────
    st.markdown("## Export")
    col_csv, col_excel, col_json = st.columns(3)

    with col_csv:
        csv_data = _build_findings_csv(all_results)
        st.download_button(
            "⬇ Download findings (CSV)",
            data=csv_data,
            file_name=f"dq_findings_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with col_excel:
        excel_data = _build_findings_excel(all_results)
        if excel_data:
            st.download_button(
                "⬇ Download findings (Excel)",
                data=excel_data,
                file_name=f"dq_findings_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

    with col_json:
        import json
        json_data = _build_summary_json(all_results)
        st.download_button(
            "⬇ Download summary (JSON)",
            data=json.dumps(json_data, indent=2),
            file_name=f"dq_summary_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
            use_container_width=True,
        )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _render_result_summary(result: AssessmentResult):
    tier_colors = {"High Risk": "#E24B4A", "Moderate": "#EF9F27", "AI Ready": "#639922"}
    color = tier_colors.get(result.maturity_tier, "#888")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("AI-Readiness Index", f"{result.ai_readiness_index:.0f}/100")
    col2.markdown(
        f"**Maturity**\n\n<span style='color:{color};font-weight:600'>{result.maturity_tier}</span>",
        unsafe_allow_html=True,
    )
    col3.metric("Critical findings", result.critical_count)
    col4.metric("Warnings", result.warning_count)

    if result.summary:
        st.caption(result.summary)

    # Dimension table
    rows = []
    for ds in result.dimension_scores:
        crit = sum(1 for f in ds.findings if f.severity == Severity.CRITICAL)
        warn = sum(1 for f in ds.findings if f.severity == Severity.WARNING)
        rows.append({
            "Dimension": ds.dimension.value.replace("_", " ").title(),
            "Score": f"{ds.score:.0f}",
            "Critical": crit,
            "Warnings": warn,
            "Findings": len(ds.findings),
        })

    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)


def _render_mini_coverage(coverage: dict):
    rows = [
        {
            "Standard": k,
            "Passed": v["passed"],
            "Failed": v["failed"],
            "Score": f"{v['score']}%",
        }
        for k, v in coverage.items()
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def _render_combined_summary(results: list[AssessmentResult]):
    st.markdown("## Overall summary")
    total_critical = sum(r.critical_count for r in results)
    total_warnings = sum(r.warning_count for r in results)
    avg_index = sum(r.ai_readiness_index for r in results) / len(results)

    col1, col2, col3 = st.columns(3)
    col1.metric("Avg AI-Readiness Index", f"{avg_index:.0f}/100")
    col2.metric("Total critical findings", total_critical)
    col3.metric("Total warnings", total_warnings)
    st.divider()


def _build_findings_csv(results: list[AssessmentResult]) -> str:
    rows = []
    for result in results:
        for f in result.all_findings:
            rows.append({
                "source": result.source_name,
                "track": result.track,
                "id": f.id,
                "dimension": f.dimension.value,
                "severity": f.severity.value,
                "title": f.title,
                "description": f.description,
                "column": f.column or "",
                "rule_ref": f.rule_ref or "",
                "affected_rows": f.affected_rows or "",
                "affected_pct": f"{f.affected_pct:.1%}" if f.affected_pct is not None else "",
                "recommendation": f.recommendation or "",
            })
    df = pd.DataFrame(rows)
    return df.to_csv(index=False)


def _build_findings_excel(results: list[AssessmentResult]) -> bytes | None:
    try:
        import io
        import openpyxl

        rows = []
        for result in results:
            for f in result.all_findings:
                rows.append({
                    "Source": result.source_name,
                    "Track": result.track,
                    "ID": f.id,
                    "Dimension": f.dimension.value.replace("_", " ").title(),
                    "Severity": f.severity.value.title(),
                    "Title": f.title,
                    "Description": f.description,
                    "Column / Field": f.column or "",
                    "Regulatory Ref": f.rule_ref or "",
                    "Affected Rows": f.affected_rows or "",
                    "Affected %": f"{f.affected_pct:.1%}" if f.affected_pct is not None else "",
                    "Recommendation": f.recommendation or "",
                })

        df = pd.DataFrame(rows)
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Findings", index=False)
            # Auto-size columns
            ws = writer.sheets["Findings"]
            for col_cells in ws.columns:
                max_len = max((len(str(c.value or "")) for c in col_cells), default=10)
                ws.column_dimensions[col_cells[0].column_letter].width = min(max_len + 4, 60)

        return buf.getvalue()

    except ImportError:
        return None


def _build_summary_json(results: list[AssessmentResult]) -> dict:
    return {
        "generated_at": datetime.now().isoformat(),
        "assessments": [
            {
                "source_name": r.source_name,
                "track": r.track,
                "ai_readiness_index": r.ai_readiness_index,
                "maturity_tier": r.maturity_tier,
                "summary": r.summary,
                "critical_count": r.critical_count,
                "warning_count": r.warning_count,
                "dimension_scores": [
                    {
                        "dimension": ds.dimension.value,
                        "score": ds.score,
                        "finding_count": len(ds.findings),
                    }
                    for ds in r.dimension_scores
                ],
                "findings": [
                    {
                        "id": f.id,
                        "dimension": f.dimension.value,
                        "severity": f.severity.value,
                        "title": f.title,
                        "column": f.column,
                        "rule_ref": f.rule_ref,
                        "recommendation": f.recommendation,
                    }
                    for f in r.all_findings
                ],
            }
            for r in results
        ],
    }
