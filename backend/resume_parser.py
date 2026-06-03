from __future__ import annotations

import PyPDF2


class ResumeParseError(Exception):
    """Raised when a PDF cannot be parsed into usable resume text."""


def extract_text_from_pdf(filepath: str) -> str:
    try:
        with open(filepath, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            text_parts = [(page.extract_text() or "").strip() for page in reader.pages]
    except Exception as exc:
        raise ResumeParseError(f"Unable to read PDF: {exc}") from exc

    text = "\n".join(part for part in text_parts if part).strip()
    if not text:
        raise ResumeParseError("No readable text was found. Try a text-based PDF instead of a scanned image PDF.")
    return text
