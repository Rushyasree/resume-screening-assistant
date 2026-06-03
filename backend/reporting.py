from __future__ import annotations

import csv
from io import BytesIO, StringIO

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def build_candidate_pdf_report(candidate: dict) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, title="Candidate Analysis Report")
    styles = getSampleStyleSheet()
    story = [
        Paragraph("Candidate Analysis Report", styles["Title"]),
        Spacer(1, 14),
        Paragraph(f"<b>Candidate:</b> {candidate.get('original_filename', 'Unknown')}", styles["BodyText"]),
        Paragraph(f"<b>Category:</b> {candidate.get('category', '-')}", styles["BodyText"]),
        Paragraph(f"<b>Confidence:</b> {candidate.get('confidence', 0)}", styles["BodyText"]),
        Paragraph(f"<b>Candidate Score:</b> {candidate.get('overall_score', 0)}%", styles["BodyText"]),
        Paragraph(f"<b>Job Match Score:</b> {candidate.get('job_match_score') or candidate.get('overall_score', 0)}%", styles["BodyText"]),
        Paragraph(f"<b>Status:</b> {candidate.get('status', 'Review')}", styles["BodyText"]),
        Spacer(1, 12),
        Paragraph("<b>Extracted Skills</b>", styles["Heading2"]),
        Paragraph(", ".join(candidate.get("skills") or ["No skills extracted"]), styles["BodyText"]),
        Spacer(1, 12),
        Paragraph("<b>Missing Skills</b>", styles["Heading2"]),
        Paragraph(", ".join(candidate.get("missing_skills") or ["No missing skills recorded"]), styles["BodyText"]),
        Spacer(1, 12),
        Paragraph("<b>AI Explanation</b>", styles["Heading2"]),
        Paragraph(candidate.get("explanation") or candidate.get("reason") or "No explanation available.", styles["BodyText"]),
    ]
    doc.build(story)
    return buffer.getvalue()


def build_candidates_csv(candidates: list[dict]) -> str:
    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "id",
            "candidate",
            "category",
            "confidence",
            "score",
            "job_match_score",
            "status",
            "skills",
            "missing_skills",
            "uploaded_at",
        ],
    )
    writer.writeheader()
    for candidate in candidates:
        writer.writerow(
            {
                "id": candidate.get("id"),
                "candidate": candidate.get("original_filename"),
                "category": candidate.get("category"),
                "confidence": candidate.get("confidence"),
                "score": candidate.get("overall_score"),
                "job_match_score": candidate.get("job_match_score") or candidate.get("overall_score"),
                "status": candidate.get("status"),
                "skills": ", ".join(candidate.get("skills") or []),
                "missing_skills": ", ".join(candidate.get("missing_skills") or []),
                "uploaded_at": candidate.get("created_at"),
            }
        )
    return output.getvalue()
