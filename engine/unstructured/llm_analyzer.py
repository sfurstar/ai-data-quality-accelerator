"""
engine/unstructured/llm_analyzer.py

LLM-powered gap analysis for compliance documents.
Phase 2: Snowflake Cortex COMPLETE() via get_session().
"""
from __future__ import annotations

import os

_MAX_CHARS = 8000  # Cortex has context limits — keep prompt focused


def analyze(
    text: str,
    document_name: str = "policy document",
    standards: list[str] | None = None,
) -> dict:
    """
    Run LLM gap analysis on extracted PDF text using Snowflake Cortex.
    Returns dict with summary, gaps, recommendations, model, error.
    """
    if not os.environ.get("SNOWFLAKE_ACCOUNT"):
        return _empty("Snowflake not configured.")

    try:
        from engine.snowflake.connection import get_session
        session = get_session()
        return _run_cortex(session, text, document_name, standards or ["HIPAA", "GDPR", "FedRAMP"])
    except Exception as e:
        return _empty(str(e))


def _build_prompt(text: str, document_name: str, standards: list[str]) -> str:
    truncated = text[:_MAX_CHARS]
    std_list = ", ".join(standards)
    return f"""You are a data governance and regulatory compliance expert reviewing a policy document for a government agency client.

Document: "{document_name}"
Relevant standards: {std_list}

--- BEGIN DOCUMENT TEXT ---
{truncated}
--- END DOCUMENT TEXT ---

Provide a structured analysis with exactly these three sections:

SUMMARY
2-3 sentences describing the document purpose, scope, and overall governance maturity.

GAPS
List 3-6 specific compliance gaps. Each gap should be one sentence referencing {std_list}.

RECOMMENDATIONS
List 3-5 concrete prioritized actions to address the gaps. Each should be one actionable sentence.

Respond ONLY with these three sections. No preamble or closing remarks."""


def _run_cortex(session, text: str, document_name: str, standards: list[str]) -> dict:
    prompt = _build_prompt(text, document_name, standards)

    # Escape single quotes for SQL
    escaped = prompt.replace("'", "\\'")

    result = session.sql(f"""
        SELECT SNOWFLAKE.CORTEX.COMPLETE(
            'mistral-large2',
            '{escaped}'
        ) AS response
    """).collect()

    if not result or not result[0][0]:
        return _empty("Cortex returned empty response.")

    return _parse(result[0][0])


def _parse(raw: str) -> dict:
    sections = {"summary": "", "gaps": [], "recommendations": [], "model": "cortex/mistral-large2", "error": None}
    current = None

    for line in raw.strip().split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        lower = stripped.lower().replace("*", "").replace("#", "").strip()

        if lower == "summary":
            current = "summary"
        elif lower == "gaps":
            current = "gaps"
        elif lower == "recommendations":
            current = "recommendations"
        elif current == "summary":
            sections["summary"] += (" " if sections["summary"] else "") + stripped
        elif current in ("gaps", "recommendations"):
            item = stripped.lstrip("-•*1234567890. ").strip()
            if item:
                sections[current].append(item)

    return sections


def _empty(reason: str) -> dict:
    return {
        "summary": "",
        "gaps": [],
        "recommendations": [],
        "model": "none",
        "error": reason,
    }
