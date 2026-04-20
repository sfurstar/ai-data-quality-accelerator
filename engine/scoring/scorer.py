"""
engine/scoring/scorer.py

Aggregates dimension-level findings into scores and a final AI-Readiness Index.

Scoring model:
  - Each dimension starts at 100.
  - Critical finding: -15 points
  - Warning finding:  -5  points
  - Info finding:     -1  point
  - Floor: 0 (dimension score cannot go negative)
  - AI-Readiness Index = weighted sum of dimension scores (weights from config)
"""
from __future__ import annotations

import yaml
from pathlib import Path

from engine import AssessmentResult, Dimension, DimensionScore, Finding, Severity

_WEIGHTS_PATH = Path(__file__).parents[2] / "config" / "scoring_weights.yaml"

_SEVERITY_DEDUCTIONS = {
    Severity.CRITICAL: 15,
    Severity.WARNING: 5,
    Severity.INFO: 1,
}


def _load_config() -> dict:
    with open(_WEIGHTS_PATH) as f:
        return yaml.safe_load(f)


def score_dimension(findings: list[Finding], weight: float, dimension: Dimension) -> DimensionScore:
    score = 100.0
    for f in findings:
        score -= _SEVERITY_DEDUCTIONS.get(f.severity, 0)
    score = max(0.0, score)
    return DimensionScore(dimension=dimension, score=score, weight=weight, findings=findings)


def compute_ai_readiness_index(dimension_scores: list[DimensionScore]) -> float:
    """Weighted average of dimension scores."""
    total_weight = sum(ds.weight for ds in dimension_scores)
    if total_weight == 0:
        return 0.0
    return sum(ds.score * ds.weight for ds in dimension_scores) / total_weight


def get_maturity_tier(index: float, config: dict) -> str:
    for tier_name, tier in config["maturity_tiers"].items():
        if tier["min"] <= index <= tier["max"]:
            return tier["label"]
    return "Unknown"


def build_result(
    source_name: str,
    track: str,
    findings_by_dimension: dict[Dimension, list[Finding]],
) -> AssessmentResult:
    """
    Given a dict of {Dimension: [Finding, ...]}, builds a scored AssessmentResult.
    Dimensions with no findings are still scored (score = 100).
    """
    config = _load_config()
    dim_config = config["dimensions"]

    # Map dimension enum values to config keys
    dim_key_map = {
        Dimension.COMPLETENESS: "completeness",
        Dimension.VALIDITY: "validity",
        Dimension.CONSISTENCY: "consistency",
        Dimension.GOVERNANCE: "governance",
        Dimension.AI_READINESS: "ai_readiness",
        Dimension.COMPLIANCE: "governance",  # unstructured compliance maps to governance weight
    }

    dimension_scores = []
    for dim, findings in findings_by_dimension.items():
        key = dim_key_map.get(dim, "governance")
        weight = dim_config.get(key, {}).get("weight", 0.20)
        dimension_scores.append(score_dimension(findings, weight, dim))

    ai_index = compute_ai_readiness_index(dimension_scores)
    tier = get_maturity_tier(ai_index, config)

    critical = sum(1 for ds in dimension_scores for f in ds.findings if f.severity == Severity.CRITICAL)
    warning = sum(1 for ds in dimension_scores for f in ds.findings if f.severity == Severity.WARNING)

    summary = (
        f"Assessment of '{source_name}' found {critical} critical and {warning} warning issues. "
        f"AI-Readiness Index: {ai_index:.0f}/100 ({tier})."
    )

    return AssessmentResult(
        source_name=source_name,
        track=track,
        dimension_scores=dimension_scores,
        ai_readiness_index=round(ai_index, 1),
        maturity_tier=tier,
        summary=summary,
    )
