"""
engine/unstructured/pdf_extractor.py

Extracts text from PDFs using pdfplumber (preferred — handles columnar layouts)
with pypdf as fallback.

Returns a dict with:
  - text: full extracted text
  - pages: list of per-page text
  - metadata: PDF metadata (author, creation date, etc.)
  - page_count: number of pages
"""
from __future__ import annotations

from pathlib import Path
from typing import BinaryIO


def extract(source: str | Path | BinaryIO) -> dict:
    """
    Extract text from a PDF file or file-like object.
    Returns structured extraction result.
    """
    try:
        import pdfplumber
        return _extract_pdfplumber(source)
    except ImportError:
        pass

    try:
        from pypdf import PdfReader
        return _extract_pypdf(source)
    except ImportError:
        raise RuntimeError("Neither pdfplumber nor pypdf is installed. Run: pip install pdfplumber")


def _extract_pdfplumber(source) -> dict:
    import pdfplumber

    pages_text = []
    metadata = {}

    with pdfplumber.open(source) as pdf:
        metadata = pdf.metadata or {}
        for page in pdf.pages:
            text = page.extract_text() or ""
            pages_text.append(text)

    full_text = "\n\n".join(pages_text)
    return {
        "text": full_text,
        "pages": pages_text,
        "metadata": metadata,
        "page_count": len(pages_text),
        "word_count": len(full_text.split()),
        "extractor": "pdfplumber",
    }


def _extract_pypdf(source) -> dict:
    from pypdf import PdfReader

    reader = PdfReader(source)
    pages_text = []

    for page in reader.pages:
        text = page.extract_text() or ""
        pages_text.append(text)

    metadata = {}
    if reader.metadata:
        metadata = {k.lstrip("/"): v for k, v in reader.metadata.items()}

    full_text = "\n\n".join(pages_text)
    return {
        "text": full_text,
        "pages": pages_text,
        "metadata": metadata,
        "page_count": len(pages_text),
        "word_count": len(full_text.split()),
        "extractor": "pypdf",
    }
