"""
engine/unstructured/__init__.py
Convenience runner that wires all unstructured assessment modules.
"""
from __future__ import annotations
from typing import BinaryIO
from pathlib import Path

from engine import AssessmentResult, Dimension
from engine.unstructured.pdf_extractor import extract
from engine.unstructured.compliance_scanner import run as scan_compliance, get_coverage_summary
from engine.unstructured.llm_analyzer import analyze as llm_analyze
from engine.scoring.scorer import build_result


def assess(
    source,  # str path, Path, or file-like
    source_name: str = "document",
    standards: list[str] | None = None,
    use_llm: bool = True,
) -> AssessmentResult:
    """
    Run the full unstructured assessment pipeline and return a scored AssessmentResult.
    """
    standards = standards or ["HIPAA", "GDPR", "FedRAMP", "GOVERNANCE"]

    extraction = extract(source)
    text = extraction["text"]

    findings_by_dim = {
        Dimension.COMPLIANCE: scan_compliance(text, standards),
    }

    result = build_result(source_name, "unstructured", findings_by_dim)
    result.metadata["extraction"] = {
        "page_count": extraction["page_count"],
        "word_count": extraction["word_count"],
        "extractor": extraction["extractor"],
    }
    result.metadata["coverage"] = get_coverage_summary(text, standards)

    if use_llm:
        result.metadata["llm"] = llm_analyze(text, document_name=source_name, standards=standards)

    return result
