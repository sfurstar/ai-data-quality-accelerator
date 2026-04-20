"""
engine/unstructured/compliance_scanner.py

Rule-based compliance scanner for extracted PDF text.
Maps text against HIPAA, GDPR, FedRAMP, and Governance rules
from config/rules/compliance_rules.yaml.

Each rule specifies required_keywords as a list of keyword groups.
A rule PASSES if ANY keyword group (list of words) all appear in the text.
"""
from __future__ import annotations

import re
import yaml
from pathlib import Path

from engine import Dimension, Finding, Severity

_RULES_PATH = Path(__file__).parents[2] / "config" / "rules" / "compliance_rules.yaml"

_SEVERITY_MAP = {
    "critical": Severity.CRITICAL,
    "warning": Severity.WARNING,
    "info": Severity.INFO,
}


def _load_rules() -> dict:
    with open(_RULES_PATH) as f:
        return yaml.safe_load(f)["standards"]


def _rule_passes(text_lower: str, required_keywords: list[list[str]]) -> bool:
    """
    Returns True if ANY keyword group is fully present in text.
    A keyword group is a list of words that must ALL appear.
    """
    for keyword_group in required_keywords:
        if all(kw.lower() in text_lower for kw in keyword_group):
            return True
    return False


def run(text: str, standards: list[str] | None = None) -> list[Finding]:
    """
    Scan extracted PDF text against compliance rules.

    Args:
        text: Full extracted text from PDF
        standards: List of standard keys to check (default: all)
                   Options: HIPAA, GDPR, FedRAMP, GOVERNANCE

    Returns:
        List of Finding objects for each failed rule.
    """
    findings: list[Finding] = []
    all_standards = _load_rules()
    text_lower = text.lower()

    target_standards = standards or list(all_standards.keys())

    for std_key in target_standards:
        if std_key not in all_standards:
            continue
        std = all_standards[std_key]

        for rule in std["rules"]:
            passed = _rule_passes(text_lower, rule["required_keywords"])
            if not passed:
                findings.append(Finding(
                    id=rule["id"],
                    dimension=Dimension.COMPLIANCE,
                    severity=_SEVERITY_MAP.get(rule["severity"], Severity.WARNING),
                    title=f"[{std_key}] {rule['clause']}",
                    description=rule["description"],
                    rule_ref=f"{std['full_name']} — {rule['clause']}",
                    recommendation=rule["missing_message"],
                ))

    return findings


def get_coverage_summary(text: str, standards: list[str] | None = None) -> dict:
    """
    Returns per-standard pass/fail counts for a quick coverage overview.
    """
    all_standards = _load_rules()
    text_lower = text.lower()
    target_standards = standards or list(all_standards.keys())
    summary = {}

    for std_key in target_standards:
        if std_key not in all_standards:
            continue
        std = all_standards[std_key]
        total = len(std["rules"])
        passed = sum(
            1 for rule in std["rules"]
            if _rule_passes(text_lower, rule["required_keywords"])
        )
        summary[std_key] = {
            "full_name": std["full_name"],
            "total_rules": total,
            "passed": passed,
            "failed": total - passed,
            "score": round((passed / total) * 100) if total > 0 else 0,
        }

    return summary
