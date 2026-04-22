"""
app/components/findings_table.py
Filterable, sortable findings table for assessment results.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from engine import Finding, Severity, Dimension


_SEVERITY_ICONS = {
    Severity.CRITICAL: "🔴",
    Severity.WARNING:  "🟡",
    Severity.INFO:     "🔵",
}

_DIM_LABELS = {
    "completeness": "Completeness",
    "validity":     "Validity",
    "consistency":  "Consistency",
    "governance":   "Governance",
    "ai_readiness": "AI Readiness",
    "compliance":   "Compliance",
}


def render_findings_table(findings: list[Finding]):
    """Render a filterable findings table with expandable detail rows."""

    if not findings:
        st.success("✅ No issues found.")
        return

    st.markdown(f"#### Findings ({len(findings)} total)")

    # ── Filters ──────────────────────────────────────────────────────────────
    col_sev, col_dim, col_search = st.columns([2, 2, 3])

    with col_sev:
        severity_filter = st.multiselect(
            "Severity",
            options=["Critical", "Warning", "Info"],
            default=["Critical", "Warning"],
            label_visibility="collapsed",
        )

    with col_dim:
        available_dims = sorted({_DIM_LABELS.get(f.dimension.value, f.dimension.value) for f in findings})
        dim_filter = st.multiselect(
            "Dimension",
            options=available_dims,
            default=available_dims,
            label_visibility="collapsed",
        )

    with col_search:
        search = st.text_input("Search findings", placeholder="Search title or description...", label_visibility="collapsed")

    # ── Filter logic ─────────────────────────────────────────────────────────
    sev_map = {"Critical": Severity.CRITICAL, "Warning": Severity.WARNING, "Info": Severity.INFO}
    active_severities = {sev_map[s] for s in severity_filter}
    active_dims = {k for k, v in _DIM_LABELS.items() if v in dim_filter}

    filtered = [
        f for f in findings
        if f.severity in active_severities
        and f.dimension.value in active_dims
        and (
            not search
            or search.lower() in f.title.lower()
            or search.lower() in f.description.lower()
        )
    ]

    # Sort: critical first, then warning, then info
    sev_order = {Severity.CRITICAL: 0, Severity.WARNING: 1, Severity.INFO: 2}
    filtered.sort(key=lambda f: sev_order.get(f.severity, 3))

    if not filtered:
        st.info("No findings match the current filters.")
        return

    st.caption(f"Showing {len(filtered)} of {len(findings)} findings")

    # ── Render each finding as an expander ───────────────────────────────────
    for finding in filtered:
        icon = _SEVERITY_ICONS.get(finding.severity, "⚪")
        dim_label = _DIM_LABELS.get(finding.dimension.value, finding.dimension.value.title())

        header = f"{icon} **{finding.title}**  ·  *{dim_label}*"
        if finding.column:
            header += f"  ·  `{finding.column}`"

        with st.expander(header, expanded=(finding.severity == Severity.CRITICAL)):
            st.markdown(finding.description)

            detail_cols = st.columns(2)
            with detail_cols[0]:
                if finding.affected_rows is not None:
                    st.metric("Affected rows", f"{finding.affected_rows:,}")
                if finding.affected_pct is not None:
                    st.metric("Affected %", f"{finding.affected_pct:.1%}")

            with detail_cols[1]:
                if finding.rule_ref:
                    st.markdown(f"**Regulatory ref:** {finding.rule_ref}")
                if finding.id:
                    st.caption(f"Rule ID: {finding.id}")

            if finding.recommendation:
                st.info(f"💡 **Recommendation:** {finding.recommendation}")

            if finding.sample_values:
                st.markdown("**Sample problematic values:**")
                st.code(", ".join(str(v) for v in finding.sample_values[:5]))
