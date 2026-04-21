"""
PDF Extractor
─────────────────────────────────────────────────────────────
Pulls raw text from an uploaded PDF file.
Uses pdfplumber for reliable text extraction — handles
multi-column layouts and preserves reading order better
than PyPDF2.

Returns a dict with:
  - text: full extracted text
  - page_count: number of pages
  - char_count: total characters
  - truncated: whether the text was cut off (>60k chars)
"""

import pypdf
import io

MAX_CHARS = 60_000  # Claude's context is large, but we keep it focused


def extract_pdf_text(file_bytes: bytes) -> dict:
    """
    Extract text from a PDF given its raw bytes.
    Uses pypdf — pure Python, no native dependencies.
    Returns a structured dict for the agents to consume.
    """
    reader = pypdf.PdfReader(io.BytesIO(file_bytes))
    page_count = len(reader.pages)
    text_parts = []

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text_parts.append(page_text.strip())

    full_text = "\n\n".join(text_parts)
    truncated = len(full_text) > MAX_CHARS

    return {
        "text": full_text[:MAX_CHARS],
        "page_count": page_count,
        "char_count": len(full_text),
        "truncated": truncated,
    }
