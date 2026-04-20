"""
engine/structured/pii_detector.py

Detects likely PII columns using:
  1. Column name pattern matching (fast, no ML needed)
  2. Sample value regex scanning (catches mislabeled columns)

Returns Governance-dimension findings.
"""
from __future__ import annotations

import re
import yaml
import pandas as pd
from pathlib import Path

from engine import Dimension, Finding, Severity

_RULES_PATH = Path(__file__).parents[2] / "config" / "rules" / "structured_rules.yaml"

# Value-level PII regex patterns (applied to string samples)
_VALUE_PATTERNS: dict[str, tuple[str, str]] = {
    "SSN": (r"\b\d{3}-\d{2}-\d{4}\b", "Social Security Number"),
    "Email": (r"\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}\b", "email address"),
    "Phone": (r"\b(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", "phone number"),
    "ZIP": (r"\b\d{5}(-\d{4})?\b", "ZIP code"),
    "CreditCard": (r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b", "credit card number"),
}


def _load_pii_patterns() -> list[str]:
    with open(_RULES_PATH) as f:
        rules = yaml.safe_load(f)
    return rules["governance"]["pii_column_patterns"]


def _column_name_is_pii(col_lower: str, patterns: list[str]) -> str | None:
    """Returns matched pattern string if column name looks like PII, else None."""
    for pattern in patterns:
        if pattern.startswith(".*") and pattern.endswith("$"):
            suffix = pattern[2:-1]
            if col_lower.endswith(suffix):
                return pattern
        elif re.search(pattern.replace(".*", ""), col_lower):
            return pattern
    return None


def _scan_values_for_pii(series: pd.Series) -> list[str]:
    """Returns list of PII type names detected in a sample of values."""
    sample = series.dropna().astype(str).head(200)
    if sample.empty:
        return []
    combined = " ".join(sample.tolist())
    found = []
    for pii_type, (regex, _) in _VALUE_PATTERNS.items():
        if re.search(regex, combined):
            found.append(pii_type)
    return found


def run(df: pd.DataFrame) -> list[Finding]:
    findings: list[Finding] = []
    pii_patterns = _load_pii_patterns()

    for col in df.columns:
        col_lower = col.lower()
        matched_pattern = _column_name_is_pii(col_lower, pii_patterns)
        value_pii_types = _scan_values_for_pii(df[col])

        if matched_pattern or value_pii_types:
            sources = []
            if matched_pattern:
                sources.append(f"column name matches pattern '{matched_pattern}'")
            if value_pii_types:
                sources.append(f"values contain: {', '.join(value_pii_types)}")

            findings.append(Finding(
                id=f"GOV-PII-{col[:15].upper().replace(' ', '_')}",
                dimension=Dimension.GOVERNANCE,
                severity=Severity.CRITICAL,
                title=f"PII detected in column '{col}'",
                description=(
                    f"Column '{col}' likely contains personally identifiable information. "
                    f"Detection basis: {'; '.join(sources)}."
                ),
                column=col,
                rule_ref="HIPAA §164.514 / GDPR Art. 4(1)",
                recommendation=(
                    "Confirm whether this column requires HIPAA or GDPR controls. "
                    "Apply masking, tokenization, or de-identification before use in AI pipelines. "
                    "Document data owner and access controls."
                ),
                metadata={"value_pii_types": value_pii_types, "name_pattern": matched_pattern},
            ))

    return findings
