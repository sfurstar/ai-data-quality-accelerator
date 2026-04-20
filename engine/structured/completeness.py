"""
engine/structured/completeness.py
Checks null rates and missing required fields.
"""
from __future__ import annotations

import re
import pandas as pd
import yaml
from pathlib import Path

from engine import Dimension, Finding, Severity

_RULES_PATH = Path(__file__).parents[2] / "config" / "rules" / "structured_rules.yaml"


def _load_thresholds() -> dict:
    with open(_RULES_PATH) as f:
        rules = yaml.safe_load(f)
    return rules["completeness"]["thresholds"]


def _load_required_hints() -> list[str]:
    with open(_RULES_PATH) as f:
        rules = yaml.safe_load(f)
    return [p.lower() for p in rules["completeness"].get("required_fields_hint", [])]


def run(df: pd.DataFrame) -> list[Finding]:
    """
    Analyse a DataFrame for completeness issues.
    Returns a list of Finding objects — one per column with null issues.
    """
    findings: list[Finding] = []
    thresholds = _load_thresholds()
    required_hints = _load_required_hints()

    total_rows = len(df)
    if total_rows == 0:
        return findings

    for col in df.columns:
        null_count = df[col].isna().sum()
        null_pct = null_count / total_rows

        col_lower = col.lower()
        is_required_hint = any(hint in col_lower for hint in required_hints)

        if null_pct >= thresholds["critical"]:
            severity = Severity.CRITICAL
        elif null_pct >= thresholds["warning"]:
            severity = Severity.WARNING
        elif null_pct >= thresholds["info"]:
            severity = Severity.INFO
        elif is_required_hint and null_count > 0:
            # Required-hint column with ANY nulls gets at least a warning
            severity = Severity.WARNING
        else:
            continue  # Column is fine

        findings.append(Finding(
            id=f"COMP-{col[:20].upper().replace(' ', '_')}",
            dimension=Dimension.COMPLETENESS,
            severity=severity,
            title=f"Null values in '{col}'",
            description=(
                f"Column '{col}' has {null_count:,} null values "
                f"({null_pct:.1%} of {total_rows:,} rows)."
            ),
            column=col,
            affected_rows=int(null_count),
            affected_pct=float(null_pct),
            recommendation=(
                f"Investigate source system for '{col}'. "
                + ("This appears to be a required field — nulls may indicate upstream data loss." if is_required_hint
                   else "Consider imputation strategy or upstream fix.")
            ),
        ))

    return findings
