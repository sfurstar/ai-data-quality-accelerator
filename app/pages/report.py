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
from app.theme import page_header


def render():
    page_header("Assessment Report", "Combined findings across all assessed sources.")

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

    # ── Snowflake history ────────────────────────────────────────────────────
    _render_snowflake_history()

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
        def _sc(s):
            v = int(s)
            return "#B00020" if v < 41 else "#854F0B" if v < 71 else "#128354"
        html = '<table style="width:100%;border-collapse:collapse;font-family:Source Sans Pro,sans-serif;font-size:14px;">'
        html += '<tr style="border-bottom:2px solid #E6E3F3;">'
        for col in ["Dimension", "Score", "Critical", "Warnings", "Findings"]:
            html += f'<th style="text-align:left;padding:8px 12px;font-weight:600;color:rgba(0,0,0,0.60);font-size:12px;text-transform:uppercase;letter-spacing:0.5px;">{col}</th>'
        html += '</tr>'
        for i, row in enumerate(rows):
            bg = "#F2F1F9" if i % 2 == 0 else "#FFFFFF"
            html += f'<tr style="background:{bg};border-bottom:1px solid rgba(0,0,0,0.06);">'
            html += f'<td style="padding:8px 12px;font-weight:600;">{row["Dimension"]}</td>'
            html += f'<td style="padding:8px 12px;font-weight:700;color:{_sc(row["Score"])};">{row["Score"]}</td>'
            html += f'<td style="padding:8px 12px;color:#B00020;font-weight:600;">{row["Critical"] or "—"}</td>'
            html += f'<td style="padding:8px 12px;color:#854F0B;font-weight:600;">{row["Warnings"] or "—"}</td>'
            html += f'<td style="padding:8px 12px;color:rgba(0,0,0,0.60);">{row["Findings"]}</td>'
            html += '</tr>'
        html += '</table>'
        st.markdown(html, unsafe_allow_html=True)


def _render_mini_coverage(coverage: dict):
    rows = []
    for k, v in coverage.items():
        icon = "🟢" if v["score"] >= 70 else "🟡" if v["score"] >= 40 else "🔴"
        rows.append({
            "Standard": f"{icon} {k}",
            "Full name": v["full_name"],
            "Passed": v["passed"],
            "Failed": v["failed"],
            "Score": f"{v['score']}%",
        })
    html = '<table style="width:100%;border-collapse:collapse;font-family:Source Sans Pro,sans-serif;font-size:14px;">'
    html += '<tr style="border-bottom:2px solid #E6E3F3;">'
    for col in ["Standard", "Full name", "Passed", "Failed", "Score"]:
        html += f'<th style="text-align:left;padding:8px 12px;font-weight:600;color:rgba(0,0,0,0.60);font-size:12px;text-transform:uppercase;letter-spacing:0.5px;">{col}</th>'
    html += '</tr>'
    for i, row in enumerate(rows):
        bg = "#F2F1F9" if i % 2 == 0 else "#FFFFFF"
        sv = int(row["Score"].replace("%", ""))
        sc = "#128354" if sv >= 70 else "#854F0B" if sv >= 40 else "#B00020"
        html += f'<tr style="background:{bg};border-bottom:1px solid rgba(0,0,0,0.06);">'
        html += f'<td style="padding:8px 12px;font-weight:600;">{row["Standard"]}</td>'
        html += f'<td style="padding:8px 12px;color:rgba(0,0,0,0.70);">{row["Full name"]}</td>'
        html += f'<td style="padding:8px 12px;color:#128354;font-weight:600;">{row["Passed"]}</td>'
        html += f'<td style="padding:8px 12px;color:#B00020;font-weight:600;">{row["Failed"]}</td>'
        html += f'<td style="padding:8px 12px;font-weight:700;color:{sc};">{row["Score"]}</td>'
        html += '</tr>'
    html += '</table>'
    st.markdown(html, unsafe_allow_html=True)


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


def _render_snowflake_history():
    """Show recent assessment history from Snowflake if connected."""
    try:
        from engine.snowflake.persist import get_recent_results, _is_configured
        if not _is_configured():
            return
        st.markdown("## Assessment history")
        st.caption("Recent runs stored in Snowflake — DQ_ACCELERATOR.ASSESSMENTS.ASSESSMENT_RESULTS")
        results = get_recent_results(limit=10)
        if not results:
            st.info("No assessment history yet. Run an assessment to populate.")
            return
        tier_icon = {"AI Ready": "🟢", "Moderate": "🟡", "High Risk": "🔴"}
        html = '<table style="width:100%;border-collapse:collapse;font-family:Source Sans Pro,sans-serif;font-size:14px;">'
        html += '<tr style="border-bottom:2px solid #E6E3F3;">'
        for col in ["Source", "Track", "Score", "Tier", "Critical", "Warnings", "Run time"]:
            html += f'<th style="text-align:left;padding:8px 12px;font-size:12px;font-weight:600;color:rgba(0,0,0,0.60);text-transform:uppercase;letter-spacing:0.5px;">{col}</th>'
        html += '</tr>'
        for i, r in enumerate(results):
            bg = "#F2F1F9" if i % 2 == 0 else "#FFFFFF"
            score = r["ai_readiness_index"] or 0
            sc = "#128354" if score >= 71 else "#854F0B" if score >= 41 else "#B00020"
            icon = tier_icon.get(r["maturity_tier"], "⚪")
            ts = str(r["run_timestamp"])[:16].replace("T", " ")
            html += f'<tr style="background:{bg};border-bottom:1px solid rgba(0,0,0,0.06);">'
            html += f'<td style="padding:8px 12px;font-weight:600;">{r["source_name"]}</td>'
            html += f'<td style="padding:8px 12px;color:rgba(0,0,0,0.60);">{r["track"].title()}</td>'
            html += f'<td style="padding:8px 12px;font-weight:700;color:{sc};">{score:.0f}/100</td>'
            html += f'<td style="padding:8px 12px;">{icon} {r["maturity_tier"]}</td>'
            html += f'<td style="padding:8px 12px;color:#B00020;font-weight:600;">{r["critical_count"]}</td>'
            html += f'<td style="padding:8px 12px;color:#854F0B;font-weight:600;">{r["warning_count"]}</td>'
            html += f'<td style="padding:8px 12px;color:rgba(0,0,0,0.50);font-size:12px;">{ts}</td>'
            html += '</tr>'
        html += '</table>'
        st.markdown(html, unsafe_allow_html=True)
        st.divider()
    except Exception:
        pass  # Never block report for history failures
