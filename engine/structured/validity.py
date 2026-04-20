"""
engine/structured/validity.py
Checks type correctness, format patterns, and range bounds.
"""
from __future__ import annotations

import re
import yaml
import pandas as pd
from pathlib import Path

from engine import Dimension, Finding, Severity

_RULES_PATH = Path(__file__).parents[2] / "config" / "rules" / "structured_rules.yaml"


def _load_rules() -> dict:
    with open(_RULES_PATH) as f:
        return yaml.safe_load(f)["validity"]


def run(df: pd.DataFrame) -> list[Finding]:
    findings: list[Finding] = []
    rules = _load_rules()
    total_rows = len(df)
    if total_rows == 0:
        return findings

    column_patterns: dict[str, str] = rules.get("column_patterns", {})
    range_checks: list[dict] = rules.get("range_checks", [])
    date_formats: list[str] = rules.get("date_formats", [])

    for col in df.columns:
        col_lower = col.lower()
        non_null = df[col].dropna()

        # ── Pattern checks ──────────────────────────────────────────────────
        for pattern_name, regex in column_patterns.items():
            if pattern_name in col_lower:
                invalid_mask = ~non_null.astype(str).str.match(regex, na=False)
                invalid_count = invalid_mask.sum()
                if invalid_count > 0:
                    invalid_pct = invalid_count / total_rows
                    severity = Severity.CRITICAL if invalid_pct >= 0.10 else Severity.WARNING
                    sample = non_null[invalid_mask].head(3).tolist()
                    findings.append(Finding(
                        id=f"VAL-FMT-{col[:15].upper().replace(' ', '_')}",
                        dimension=Dimension.VALIDITY,
                        severity=severity,
                        title=f"Format violations in '{col}' ({pattern_name})",
                        description=(
                            f"{invalid_count:,} values ({invalid_pct:.1%}) in '{col}' "
                            f"do not match expected {pattern_name} format."
                        ),
                        column=col,
                        affected_rows=int(invalid_count),
                        affected_pct=float(invalid_pct),
                        recommendation=f"Standardize '{col}' to the expected {pattern_name} format at ingestion.",
                        sample_values=sample,
                    ))

        # ── Date format checks ───────────────────────────────────────────────
        if any(kw in col_lower for kw in ["date", "time", "created", "updated", "closed"]):
            if df[col].dtype == object:
                # Try to parse — count failures
                def _try_parse(val):
                    for fmt in date_formats:
                        try:
                            pd.to_datetime(val, format=fmt)
                            return True
                        except Exception:
                            pass
                    # Fallback: let pandas infer
                    try:
                        pd.to_datetime(val)
                        return True
                    except Exception:
                        return False

                sample_size = min(500, len(non_null))
                sample_series = non_null.sample(n=sample_size, random_state=42) if len(non_null) > sample_size else non_null
                failures = sample_series[~sample_series.astype(str).apply(_try_parse)]
                if len(failures) > 0:
                    fail_pct = len(failures) / sample_size
                    if fail_pct >= 0.01:
                        findings.append(Finding(
                            id=f"VAL-DATE-{col[:15].upper().replace(' ', '_')}",
                            dimension=Dimension.VALIDITY,
                            severity=Severity.WARNING,
                            title=f"Unparseable date values in '{col}'",
                            description=(
                                f"~{fail_pct:.0%} of sampled values in '{col}' "
                                f"could not be parsed as a date/time."
                            ),
                            column=col,
                            affected_pct=float(fail_pct),
                            recommendation=f"Standardize '{col}' to ISO-8601 format (YYYY-MM-DD) at ingestion.",
                            sample_values=failures.head(3).tolist(),
                        ))

        # ── Range checks ─────────────────────────────────────────────────────
        for rc in range_checks:
            pattern = rc["column_pattern"].replace(".*", "")
            if re.search(rc["column_pattern"], col_lower):
                numeric = pd.to_numeric(df[col], errors="coerce")
                out_of_range = numeric[(numeric < rc["min"]) | (numeric > rc["max"])].dropna()
                if len(out_of_range) > 0:
                    pct = len(out_of_range) / total_rows
                    findings.append(Finding(
                        id=f"VAL-RNG-{col[:15].upper().replace(' ', '_')}",
                        dimension=Dimension.VALIDITY,
                        severity=Severity.WARNING,
                        title=f"Out-of-range values in '{col}'",
                        description=(
                            f"{len(out_of_range):,} values ({pct:.1%}) in '{col}' "
                            f"fall outside expected range [{rc['min']}, {rc['max']}]."
                        ),
                        column=col,
                        affected_rows=int(len(out_of_range)),
                        affected_pct=float(pct),
                        recommendation=f"Add range validation at ingestion for '{col}'.",
                        sample_values=out_of_range.head(3).tolist(),
                    ))

    return findings
