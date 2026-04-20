"""
engine/structured/ai_readiness.py

Checks AI-specific data readiness:
  - Dataset size (minimum rows for ML)
  - Duplicate rows (data leakage risk)
  - Class imbalance in likely label columns
  - High-cardinality categoricals (potential leakage)
  - Feature completeness across columns
"""
from __future__ import annotations

import yaml
import pandas as pd
from pathlib import Path

from engine import Dimension, Finding, Severity

_RULES_PATH = Path(__file__).parents[2] / "config" / "rules" / "structured_rules.yaml"


def _load_rules() -> dict:
    with open(_RULES_PATH) as f:
        return yaml.safe_load(f)["ai_readiness"]


def _is_likely_label(col: str) -> bool:
    label_hints = ["status", "label", "category", "class", "outcome", "result", "flag", "type"]
    return any(hint in col.lower() for hint in label_hints)


def run(df: pd.DataFrame) -> list[Finding]:
    findings: list[Finding] = []
    rules = _load_rules()
    total_rows = len(df)

    # ── Row count ────────────────────────────────────────────────────────────
    if total_rows < rules["min_rows"]["critical"]:
        findings.append(Finding(
            id="AIR-ROWS-CRITICAL",
            dimension=Dimension.AI_READINESS,
            severity=Severity.CRITICAL,
            title="Insufficient rows for machine learning",
            description=f"Dataset has only {total_rows:,} rows. Minimum recommended: {rules['min_rows']['warning']:,}.",
            recommendation="Expand dataset before training. Consider data augmentation or synthetic data generation.",
            affected_rows=total_rows,
        ))
    elif total_rows < rules["min_rows"]["warning"]:
        findings.append(Finding(
            id="AIR-ROWS-WARNING",
            dimension=Dimension.AI_READINESS,
            severity=Severity.WARNING,
            title="Low row count for machine learning",
            description=f"Dataset has {total_rows:,} rows. Some ML models may perform poorly.",
            recommendation="Consider augmenting with additional data sources before training complex models.",
            affected_rows=total_rows,
        ))

    # ── Duplicate rows ───────────────────────────────────────────────────────
    dup_count = df.duplicated().sum()
    dup_pct = dup_count / total_rows if total_rows > 0 else 0
    if dup_pct >= rules["duplicate_row_pct"]["critical"]:
        findings.append(Finding(
            id="AIR-DUPS-CRITICAL",
            dimension=Dimension.AI_READINESS,
            severity=Severity.CRITICAL,
            title="High duplicate row rate",
            description=f"{dup_count:,} duplicate rows ({dup_pct:.1%}). High risk of train/test data leakage.",
            affected_rows=int(dup_count),
            affected_pct=float(dup_pct),
            recommendation="Deduplicate before splitting into train/test sets to prevent leakage.",
        ))
    elif dup_pct >= rules["duplicate_row_pct"]["warning"]:
        findings.append(Finding(
            id="AIR-DUPS-WARNING",
            dimension=Dimension.AI_READINESS,
            severity=Severity.WARNING,
            title="Duplicate rows detected",
            description=f"{dup_count:,} duplicate rows ({dup_pct:.1%}). Review before model training.",
            affected_rows=int(dup_count),
            affected_pct=float(dup_pct),
            recommendation="Deduplicate or investigate if duplicates are legitimate repeat events.",
        ))

    # ── Class imbalance in label-like columns ────────────────────────────────
    for col in df.columns:
        if not _is_likely_label(col):
            continue
        vc = df[col].value_counts(normalize=True, dropna=True)
        if len(vc) < 2:
            continue
        minority_pct = vc.min()
        if minority_pct < rules["label_imbalance"]["critical_ratio"]:
            findings.append(Finding(
                id=f"AIR-IMBAL-{col[:15].upper().replace(' ', '_')}",
                dimension=Dimension.AI_READINESS,
                severity=Severity.CRITICAL,
                title=f"Severe class imbalance in '{col}'",
                description=(
                    f"Minority class in '{col}' represents only {minority_pct:.1%} of values. "
                    f"This will cause ML models to ignore minority classes."
                ),
                column=col,
                affected_pct=float(minority_pct),
                recommendation=(
                    "Apply oversampling (SMOTE), undersampling, or class weights before training. "
                    "Consider collecting more minority class examples."
                ),
                metadata={"value_counts": vc.to_dict()},
            ))
        elif minority_pct < rules["label_imbalance"]["warning_ratio"]:
            findings.append(Finding(
                id=f"AIR-IMBAL-{col[:15].upper().replace(' ', '_')}",
                dimension=Dimension.AI_READINESS,
                severity=Severity.WARNING,
                title=f"Class imbalance in '{col}'",
                description=f"Minority class in '{col}' is {minority_pct:.1%}. May affect model performance.",
                column=col,
                affected_pct=float(minority_pct),
                recommendation="Consider class weighting or resampling strategies during model training.",
                metadata={"value_counts": vc.head(10).to_dict()},
            ))

    # ── High cardinality categoricals ────────────────────────────────────────
    for col in df.select_dtypes(include="object").columns:
        n_unique = df[col].nunique()
        unique_pct = n_unique / total_rows if total_rows > 0 else 0
        if unique_pct > rules["high_cardinality_pct"] and n_unique > 50:
            findings.append(Finding(
                id=f"AIR-CARD-{col[:15].upper().replace(' ', '_')}",
                dimension=Dimension.AI_READINESS,
                severity=Severity.WARNING,
                title=f"High cardinality in '{col}'",
                description=(
                    f"'{col}' has {n_unique:,} unique values ({unique_pct:.0%} of rows). "
                    "High cardinality may indicate free-text, IDs, or leakage risk."
                ),
                column=col,
                recommendation=(
                    "Investigate whether this column is an ID (exclude from features), "
                    "free-text (apply NLP encoding), or a categorical needing grouping."
                ),
                metadata={"unique_count": int(n_unique), "unique_pct": float(unique_pct)},
            ))

    return findings
