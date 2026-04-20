"""
engine/unstructured/llm_analyzer.py

LLM-powered gap analysis for compliance documents.

Phase 1: Disabled — rule-based scanner handles all checks, no API cost.
Phase 2: Wire in Snowflake Cortex COMPLETE() — see _run_cortex() stub below.
"""
from __future__ import annotations


def analyze(
    text: str,
    document_name: str = "policy document",
    standards: list[str] | None = None,
) -> dict:
    """
    Phase 1: Returns empty result — LLM analysis deferred to Phase 2.
    Phase 2: Call _run_cortex() with a structured prompt for narrative gap analysis.
    """
    return {
        "summary": "",
        "gaps": [],
        "recommendations": [],
        "model": "none",
        "error": "LLM gap analysis will be enabled in Phase 2 (Snowflake Cortex).",
    }


def _run_cortex(prompt: str) -> str:
    """
    Phase 2 stub — replace body with Snowflake Cortex COMPLETE() call.

    Example Phase 2 implementation:
        from snowflake.snowpark.context import get_active_session
        session = get_active_session()
        escaped = prompt.replace("'", "''")
        return session.sql(
            f"SELECT SNOWFLAKE.CORTEX.COMPLETE('mistral-large', '{escaped}')"
        ).collect()[0][0]
    """
    raise NotImplementedError("Cortex not configured — Phase 2 only.")
