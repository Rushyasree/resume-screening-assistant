from __future__ import annotations

from embedding_service import embedding_similarity
from skill_engine import extract_required_skills, normalize_skill, score_candidate


def semantic_match_resume_to_job(resume_text: str, resume_skills: list[str], job_description: str) -> dict:
    required_skills = extract_required_skills(job_description)
    base_score = score_candidate(resume_text, resume_skills, required_skills)
    similarity, provider = embedding_similarity(resume_text, job_description)
    semantic_score = similarity * 100
    job_match_score = round(base_score["skills_match"] * 0.65 + semantic_score * 0.35, 2)

    if job_match_score >= 78:
        recommendation = "Shortlist"
    elif job_match_score >= 58:
        recommendation = "Review"
    elif job_match_score >= 42:
        recommendation = "Hold"
    else:
        recommendation = "Reject"

    return {
        "job_match_score": job_match_score,
        "matched_skills": base_score["matched_skills"],
        "missing_skills": base_score["missing_skills"],
        "recommendation": recommendation,
        "embedding_provider": provider,
        "semantic_similarity": round(semantic_score, 2),
        "explanation": (
            f"Matched {len(base_score['matched_skills'])} required skills with "
            f"{round(semantic_score, 2)}% semantic similarity to the job description."
        ),
    }
