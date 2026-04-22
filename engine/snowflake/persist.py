"""
engine/snowflake/persist.py

Persists assessment results to Snowflake after every run.
Writes to:
  - DQ_ACCELERATOR.ASSESSMENTS.ASSESSMENT_RESULTS   (one row per run)
  - DQ_ACCELERATOR.ASSESSMENTS.DIMENSION_SCORES     (one row per dimension per run)

Phase 1: Called optionally if Snowflake is configured.
Phase 2: Called automatically after every assessment.
"""
from __future__ import annotations

import json
import os
from datetime import datetime

from engine import AssessmentResult, Severity


def _is_configured() -> bool:
    """Returns True if Snowflake env vars are set."""
    return bool(os.environ.get("SNOWFLAKE_ACCOUNT") and os.environ.get("SNOWFLAKE_USER"))


def save_result(result: AssessmentResult) -> dict:
    """
    Persist an AssessmentResult to Snowflake.
    Returns dict with status, assessment_id, and any error.
    Silently skips if Snowflake is not configured.
    """
    if not _is_configured():
        return {"status": "skipped", "reason": "Snowflake not configured"}

    try:
        from engine.snowflake.connection import get_session
        session = get_session()
        return _write(session, result)
    except Exception as e:
        return {"status": "error", "error": str(e)}


def _write(session, result: AssessmentResult) -> dict:
    """Write result and dimension scores to Snowflake."""

    # Build findings JSON — safe serialization
    findings_list = [
        {
            "id":              f.id,
            "dimension":       f.dimension.value,
            "severity":        f.severity.value,
            "title":           f.title,
            "description":     f.description,
            "column":          f.column,
            "rule_ref":        f.rule_ref,
            "affected_rows":   f.affected_rows,
            "affected_pct":    f.affected_pct,
            "recommendation":  f.recommendation,
        }
        for f in result.all_findings
    ]

    findings_json  = json.dumps(findings_list).replace("'", "\\'")
    metadata_json  = json.dumps(result.metadata).replace("'", "\\'")

    # ── Insert into ASSESSMENT_RESULTS ────────────────────────────────────────
    insert_sql = f"""
    INSERT INTO DQ_ACCELERATOR.ASSESSMENTS.ASSESSMENT_RESULTS
        (SOURCE_NAME, TRACK, AI_READINESS_INDEX, MATURITY_TIER,
         SUMMARY, CRITICAL_COUNT, WARNING_COUNT, FINDINGS_JSON, METADATA_JSON)
    SELECT
        '{_esc(result.source_name)}',
        '{_esc(result.track)}',
        {result.ai_readiness_index},
        '{_esc(result.maturity_tier)}',
        '{_esc(result.summary)}',
        {result.critical_count},
        {result.warning_count},
        PARSE_JSON('{findings_json}'),
        PARSE_JSON('{metadata_json}')
    """
    session.sql(insert_sql).collect()

    # Get the assessment_id just inserted
    id_result = session.sql(
        "SELECT MAX(ASSESSMENT_ID) FROM DQ_ACCELERATOR.ASSESSMENTS.ASSESSMENT_RESULTS "
        f"WHERE SOURCE_NAME = '{_esc(result.source_name)}'"
    ).collect()
    assessment_id = id_result[0][0] if id_result else "unknown"

    # ── Insert dimension scores ───────────────────────────────────────────────
    for ds in result.dimension_scores:
        session.sql(f"""
        INSERT INTO DQ_ACCELERATOR.ASSESSMENTS.DIMENSION_SCORES
            (ASSESSMENT_ID, DIMENSION, SCORE, WEIGHT, FINDING_COUNT)
        VALUES (
            '{assessment_id}',
            '{ds.dimension.value}',
            {ds.score},
            {ds.weight},
            {len(ds.findings)}
        )
        """).collect()

    return {
        "status":        "saved",
        "assessment_id": assessment_id,
        "source_name":   result.source_name,
        "track":         result.track,
        "index":         result.ai_readiness_index,
    }


def _esc(val: str) -> str:
    """Escape single quotes for SQL strings."""
    return str(val).replace("'", "\\'") if val else ""


def get_recent_results(limit: int = 20) -> list[dict]:
    """
    Fetch recent assessment results from Snowflake for the history view.
    Returns list of dicts with summary info.
    """
    if not _is_configured():
        return []
    try:
        from engine.snowflake.connection import get_session
        session = get_session()
        rows = session.sql(f"""
            SELECT
                ASSESSMENT_ID,
                SOURCE_NAME,
                TRACK,
                RUN_TIMESTAMP,
                AI_READINESS_INDEX,
                MATURITY_TIER,
                CRITICAL_COUNT,
                WARNING_COUNT
            FROM DQ_ACCELERATOR.ASSESSMENTS.ASSESSMENT_RESULTS
            ORDER BY RUN_TIMESTAMP DESC
            LIMIT {limit}
        """).collect()
        return [
            {
                "assessment_id":     r[0],
                "source_name":       r[1],
                "track":             r[2],
                "run_timestamp":     str(r[3]),
                "ai_readiness_index": r[4],
                "maturity_tier":     r[5],
                "critical_count":    r[6],
                "warning_count":     r[7],
            }
            for r in rows
        ]
    except Exception as e:
        return []
