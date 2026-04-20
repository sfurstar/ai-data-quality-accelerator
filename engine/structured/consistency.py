"""
engine/structured/consistency.py
Cross-column rule checks — date ordering, conditional required fields, etc.
Rules are loaded from config/rules/structured_rules.yaml.
Any rule that requires columns NOT present in the DataFrame is silently skipped.
"""
from __future__ import annotations

import yaml
import pandas as pd
from pathlib import Path

from engine import Dimension, Finding, Severity

_RULES_PATH = Path(__file__).parents[2] / "config" / "rules" / "structured_rules.yaml"


def _load_rules() -> list[dict]:
    with open(_RULES_PATH) as f:
        data = yaml.safe_load(f)
    return data.get("consistency", {}).get("rules", [])


def _normalize_col(name: str) -> str:
    return name.lower().replace(" ", "_")


def _find_col(df: pd.DataFrame, target: str) -> str | None:
    """Case/space-insensitive column lookup."""
    norm_target = _normalize_col(target)
    for col in df.columns:
        if _normalize_col(col) == norm_target:
            return col
    return None


def run(df: pd.DataFrame) -> list[Finding]:
    findings: list[Finding] = []
    rules = _load_rules()
    total_rows = len(df)

    if total_rows == 0:
        return findings

    # ── Generic date ordering check ──────────────────────────────────────────
    # Auto-detect created/open date vs closed/resolved date pairs
    date_pairs = _detect_date_pairs(df)
    for open_col, close_col in date_pairs:
        findings.extend(_check_date_order(df, open_col, close_col, total_rows))

    # ── Rule-based checks from config ────────────────────────────────────────
    for rule in rules:
        required_cols = rule.get("applicable_columns", [])
        # Check all required columns exist
        col_map = {}
        missing = False
        for req_col in required_cols:
            actual = _find_col(df, req_col)
            if actual is None:
                missing = True
                break
            col_map[req_col] = actual

        if missing:
            continue

        # Rename to match rule column names for query evaluation
        working = df.rename(columns={v: k for k, v in col_map.items()})

        try:
            # Evaluate the query — rows where query is FALSE are violations
            for col in required_cols:
                if working[col].dtype == object:
                    try:
                        working[col] = pd.to_datetime(working[col], errors="coerce")
                    except Exception:
                        pass

            violated = working.query(f"not ({rule['query']})", engine="python")
            count = len(violated)

            if count > 0:
                pct = count / total_rows
                sev_map = {"critical": Severity.CRITICAL, "warning": Severity.WARNING, "info": Severity.INFO}
                severity = sev_map.get(rule.get("severity", "warning"), Severity.WARNING)

                findings.append(Finding(
                    id=rule["id"],
                    dimension=Dimension.CONSISTENCY,
                    severity=severity,
                    title=f"Consistency violation: {rule['description']}",
                    description=(
                        f"{count:,} rows ({pct:.1%}) violate rule '{rule['id']}': "
                        f"{rule['description']}"
                    ),
                    affected_rows=int(count),
                    affected_pct=float(pct),
                    recommendation=f"Investigate upstream source for rows violating: {rule['description']}",
                ))
        except Exception:
            # Query failed (column type mismatch, etc.) — skip silently
            pass

    return findings


def _detect_date_pairs(df: pd.DataFrame) -> list[tuple[str, str]]:
    """
    Auto-detect likely (created/open, closed/resolved) date column pairs.
    """
    open_hints = ["created", "opened", "open_date", "start_date", "submitted"]
    close_hints = ["closed", "resolved", "close_date", "end_date", "completed"]

    open_cols = [c for c in df.columns if any(h in c.lower() for h in open_hints)]
    close_cols = [c for c in df.columns if any(h in c.lower() for h in close_hints)]

    pairs = []
    for oc in open_cols:
        for cc in close_cols:
            if oc != cc:
                pairs.append((oc, cc))
    return pairs[:3]  # cap at 3 pairs to avoid noise


def _check_date_order(
    df: pd.DataFrame, open_col: str, close_col: str, total_rows: int
) -> list[Finding]:
    findings = []

    open_dt = pd.to_datetime(df[open_col], errors="coerce")
    close_dt = pd.to_datetime(df[close_col], errors="coerce")

    both_present = open_dt.notna() & close_dt.notna()
    violations = both_present & (close_dt < open_dt)
    count = violations.sum()

    if count > 0:
        pct = count / total_rows
        findings.append(Finding(
            id=f"CST-DATE-{open_col[:10].upper()}",
            dimension=Dimension.CONSISTENCY,
            severity=Severity.CRITICAL,
            title=f"Date ordering violation: '{close_col}' before '{open_col}'",
            description=(
                f"{count:,} rows ({pct:.1%}) have '{close_col}' earlier than '{open_col}'. "
                "This indicates data entry errors or ETL issues."
            ),
            affected_rows=int(count),
            affected_pct=float(pct),
            recommendation=(
                f"Audit ETL pipeline for '{open_col}' and '{close_col}'. "
                "Add ingestion-time validation to reject or flag inverted date pairs."
            ),
        ))

    return findings
