"""
app/components/score_card.py
Reusable score display widgets for the assessment results.
"""
from __future__ import annotations

import streamlit as st
from engine import AssessmentResult, Severity


_TIER_COLORS = {
    "High Risk":  "#E24B4A",
    "Moderate":   "#EF9F27",
    "AI Ready":   "#639922",
}

_TIER_ICONS = {
    "High Risk":  "🔴",
    "Moderate":   "🟡",
    "AI Ready":   "🟢",
}

_DIM_LABELS = {
    "completeness":  "Completeness",
    "validity":      "Validity",
    "consistency":   "Consistency",
    "governance":    "Governance",
    "ai_readiness":  "AI Readiness",
    "compliance":    "Compliance",
}


def render_score_card(result: AssessmentResult):
    """Render the executive score card with AI-Readiness Index and dimension breakdown."""

    tier_color = _TIER_COLORS.get(result.maturity_tier, "#888")
    tier_icon  = _TIER_ICONS.get(result.maturity_tier, "⚪")

    # ── Top metrics row ──────────────────────────────────────────────────────
    col_score, col_tier, col_crit, col_warn, col_info = st.columns([2, 2, 1, 1, 1])

    with col_score:
        st.metric(
            label="AI-Readiness Index",
            value=f"{result.ai_readiness_index:.0f} / 100",
        )

    with col_tier:
        st.markdown(
            f"**Maturity Tier**\n\n"
            f"<span style='color:{tier_color}; font-size:1.3rem; font-weight:600'>"
            f"{tier_icon} {result.maturity_tier}</span>",
            unsafe_allow_html=True,
        )

    with col_crit:
        st.metric("Critical", result.critical_count, delta=None)

    with col_warn:
        st.metric("Warnings", result.warning_count, delta=None)

    with col_info:
        info_count = sum(
            1 for f in result.all_findings if f.severity == Severity.INFO
        )
        st.metric("Info", info_count)

    st.caption(result.summary)
    st.divider()

    # ── Dimension breakdown ──────────────────────────────────────────────────
    st.markdown("#### Dimension scores")

    for ds in result.dimension_scores:
        dim_label = _DIM_LABELS.get(ds.dimension.value, ds.dimension.value.title())
        crit = sum(1 for f in ds.findings if f.severity == Severity.CRITICAL)
        warn = sum(1 for f in ds.findings if f.severity == Severity.WARNING)

        col_name, col_bar, col_score_val, col_issues = st.columns([2, 4, 1, 2])

        with col_name:
            st.markdown(f"**{dim_label}**")

        with col_bar:
            score = ds.score
            color = (
                "#E24B4A" if score < 41
                else "#EF9F27" if score < 71
                else "#639922"
            )
            st.markdown(
                f"""<div style="background:var(--secondary-background-color);
                     border-radius:4px; height:20px; margin-top:6px; overflow:hidden">
                  <div style="background:{color}; width:{score}%; height:100%;
                       border-radius:4px; transition:width .3s"></div>
                </div>""",
                unsafe_allow_html=True,
            )

        with col_score_val:
            st.markdown(f"**{score:.0f}**")

        with col_issues:
            badges = []
            if crit:
                badges.append(f"🔴 {crit} critical")
            if warn:
                badges.append(f"🟡 {warn} warn")
            if not badges:
                badges.append("✅ clean")
            st.caption("  ·  ".join(badges))
