"""
engine/__init__.py
Shared data structures used across all assessment modules.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Severity(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class Dimension(str, Enum):
    COMPLETENESS = "completeness"
    VALIDITY = "validity"
    CONSISTENCY = "consistency"
    GOVERNANCE = "governance"
    AI_READINESS = "ai_readiness"
    COMPLIANCE = "compliance"   # used by unstructured track


@dataclass
class Finding:
    """A single quality or governance issue found during assessment."""
    id: str                         # e.g. COMP-001, HIPAA-003
    dimension: Dimension
    severity: Severity
    title: str
    description: str
    column: str | None = None       # Structured: affected column name
    rule_ref: str | None = None     # Regulatory reference (e.g. "HIPAA §164.412")
    affected_rows: int | None = None
    affected_pct: float | None = None
    recommendation: str | None = None
    sample_values: list[Any] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DimensionScore:
    dimension: Dimension
    score: float            # 0.0 – 100.0
    weight: float           # from scoring_weights.yaml
    findings: list[Finding] = field(default_factory=list)
    notes: str = ""


@dataclass
class AssessmentResult:
    """Top-level result object returned by both assessment tracks."""
    source_name: str        # filename or table name
    track: str              # "structured" | "unstructured"
    dimension_scores: list[DimensionScore] = field(default_factory=list)
    ai_readiness_index: float = 0.0
    maturity_tier: str = ""
    summary: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def all_findings(self) -> list[Finding]:
        findings = []
        for ds in self.dimension_scores:
            findings.extend(ds.findings)
        return findings

    @property
    def critical_count(self) -> int:
        return sum(1 for f in self.all_findings if f.severity == Severity.CRITICAL)

    @property
    def warning_count(self) -> int:
        return sum(1 for f in self.all_findings if f.severity == Severity.WARNING)
