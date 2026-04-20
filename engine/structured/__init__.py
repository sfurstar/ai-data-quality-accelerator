"""
engine/structured/__init__.py
Convenience runner that wires all structured assessment modules.
"""
from __future__ import annotations

import pandas as pd

from engine import AssessmentResult, Dimension
from engine.structured import completeness, validity, consistency, pii_detector, ai_readiness
from engine.scoring.scorer import build_result


def assess(df: pd.DataFrame, source_name: str = "dataset") -> AssessmentResult:
    """
    Run the full structured assessment pipeline and return a scored AssessmentResult.
    """
    findings_by_dim = {
        Dimension.COMPLETENESS: completeness.run(df),
        Dimension.VALIDITY:     validity.run(df),
        Dimension.CONSISTENCY:  consistency.run(df),
        Dimension.GOVERNANCE:   pii_detector.run(df),
        Dimension.AI_READINESS: ai_readiness.run(df),
    }
    return build_result(source_name, "structured", findings_by_dim)
