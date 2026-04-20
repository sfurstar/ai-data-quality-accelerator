"""
engine/unstructured/llm_analyzer.py

Uses an LLM to perform deeper gap analysis on policy/compliance documents.
Phase 1: Anthropic Claude API
Phase 2: Snowflake Cortex COMPLETE()

The LLM is asked to:
  1. Summarize the document's purpose and scope
  2. Identify governance or compliance gaps NOT caught by rule-based scanner
  3. Suggest 3-5 highest-priority remediation actions
"""
from __future__ import annotations

import os
from dotenv import load_dotenv

load_dotenv()

_MAX_CHARS = 12_000   # Truncate to avoid context overflow; ~3000 tokens


def analyze(
    text: str,
    document_name: str = "policy document",
    standards: list[str] | None = None,
) -> dict:
    """
    Run LLM analysis on extracted PDF text.

    Returns dict with:
      - summary: str
      - gaps: list[str]
      - recommendations: list[str]
      - model: str
      - error: str | None
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _fallback_result("ANTHROPIC_API_KEY not set — LLM analysis skipped.")

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        return _run_claude(client, text, document_name, standards or ["HIPAA", "GDPR", "FedRAMP"])
    except ImportError:
        return _fallback_result("anthropic package not installed. Run: pip install anthropic")
    except Exception as e:
        return _fallback_result(f"LLM analysis failed: {str(e)}")


def _build_prompt(text: str, document_name: str, standards: list[str]) -> str:
    truncated = text[:_MAX_CHARS]
    std_list = ", ".join(standards)
    return f"""You are a data governance and regulatory compliance expert reviewing a policy document for a government agency client.

Document: "{document_name}"
Relevant standards: {std_list}

--- BEGIN DOCUMENT TEXT ---
{truncated}
--- END DOCUMENT TEXT ---

Please provide a structured analysis with exactly these three sections:

**SUMMARY**
2-3 sentences describing the document's purpose, scope, and overall governance maturity.

**GAPS**
List 3-6 specific governance or compliance gaps found in this document. Each gap should be one sentence. Focus on missing language, vague commitments, or absent controls that relate to {std_list}.

**RECOMMENDATIONS**
List 3-5 concrete, prioritized actions the organization should take to address the identified gaps. Each recommendation should be one sentence and actionable.

Respond ONLY with these three sections. Do not add preamble or closing remarks."""


def _run_claude(client, text: str, document_name: str, standards: list[str]) -> dict:
    prompt = _build_prompt(text, document_name, standards)

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text
    return _parse_response(raw)


def _parse_response(raw: str) -> dict:
    """Parse the structured LLM response into sections."""
    sections = {"summary": "", "gaps": [], "recommendations": [], "model": "claude", "error": None}

    lines = raw.strip().split("\n")
    current_section = None

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        lower = stripped.lower().replace("*", "").replace("#", "").strip()

        if lower == "summary":
            current_section = "summary"
        elif lower == "gaps":
            current_section = "gaps"
        elif lower == "recommendations":
            current_section = "recommendations"
        elif current_section == "summary":
            sections["summary"] += (" " if sections["summary"] else "") + stripped
        elif current_section in ("gaps", "recommendations"):
            # Strip leading list markers
            item = stripped.lstrip("-•*1234567890. ").strip()
            if item:
                sections[current_section].append(item)

    return sections


def _fallback_result(reason: str) -> dict:
    return {
        "summary": "LLM analysis not available.",
        "gaps": [],
        "recommendations": [],
        "model": "none",
        "error": reason,
    }
