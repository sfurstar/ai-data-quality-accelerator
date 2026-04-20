"""
app/components/score_card.py
EDS-styled score display using CGI brand colors and headstone pattern.
"""
from __future__ import annotations

import streamlit as st
from engine import AssessmentResult, Severity
from app.theme import headstone, maturity_badge

_DIM_LABELS = {
    "completeness": "Completeness",
    "validity":     "Validity",
    "consistency":  "Consistency",
    "governance":   "Governance & Compliance",
    "ai_readiness": "AI Readiness",
    "compliance":   "Compliance",
}

# EDS semantic colors
_SCORE_COLORS = {
    "high":     "#B00020",   # eds-color-error
    "moderate": "#F1A425",   # eds-color-warning
    "good":     "#1AB977",   # eds-color-success
}


def _score_color(score: float) -> str:
    if score < 41:
        return _SCORE_COLORS["high"]
    if score < 71:
        return _SCORE_COLORS["moderate"]
    return _SCORE_COLORS["good"]


def render_score_card(result: AssessmentResult):
    """Render the executive score card with EDS headstone + dimension breakdown."""

    info_count = sum(1 for f in result.all_findings if f.severity == Severity.INFO)

    # ── EDS headstone — key metrics ──────────────────────────────────────────
    headstone([
        {"label": "AI-Readiness Index", "value": f"{result.ai_readiness_index:.0f} / 100",
         "footer": result.maturity_tier},
        {"label": "Critical findings",  "value": str(result.critical_count),
         "footer": "Requires immediate action"},
        {"label": "Warnings",           "value": str(result.warning_count),
         "footer": "Recommended fixes"},
        {"label": "Informational",      "value": str(info_count),
         "footer": "Low priority"},
        {"label": "Source",             "value": result.source_name[:28],
         "footer": result.track.title()},
    ])

    # Maturity badge
    st.markdown(maturity_badge(result.maturity_tier, result.ai_readiness_index),
                unsafe_allow_html=True)
    st.caption(result.summary)
    st.divider()

    # ── Dimension breakdown ───────────────────────────────────────────────────
    st.markdown("#### Dimension scores")

    for ds in result.dimension_scores:
        dim_label = _DIM_LABELS.get(ds.dimension.value, ds.dimension.value.title())
        crit  = sum(1 for f in ds.findings if f.severity == Severity.CRITICAL)
        warn  = sum(1 for f in ds.findings if f.severity == Severity.WARNING)
        color = _score_color(ds.score)

        col_name, col_bar, col_score_val, col_issues = st.columns([2, 4, 1, 2])

        with col_name:
            st.markdown(f"**{dim_label}**")

        with col_bar:
            st.markdown(
                f"""<div style="background:#EFEFEF; border-radius:0px; height:18px;
                     margin-top:8px; overflow:hidden;">
                  <div style="background:{color}; width:{ds.score}%; height:100%;
                       transition:width .3s;"></div>
                </div>""",
                unsafe_allow_html=True,
            )

        with col_score_val:
            st.markdown(
                f"<span style='font-weight:700; color:{color}; "
                f"font-family:var(--eds-font-family);'>{ds.score:.0f}</span>",
                unsafe_allow_html=True,
            )

        with col_issues:
            badges = []
            if crit:
                badges.append(
                    f"<span class='eds-badge-critical'>🔴 {crit} critical</span>"
                )
            if warn:
                badges.append(
                    f"<span class='eds-badge-warning'>🟡 {warn} warn</span>"
                )
            if not badges:
                badges.append(
                    "<span class='eds-badge-info'>✅ clean</span>"
                )
            st.markdown(" ".join(badges), unsafe_allow_html=True)
