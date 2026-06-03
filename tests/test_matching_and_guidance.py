from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from career_guidance import build_student_guidance
from matching import semantic_match_resume_to_job
from skill_engine import extract_skills


def test_extract_skills_normalizes_acronyms():
    result = extract_skills("Built Python Flask apps with SQL, IBM AI, Git and React.")
    assert "Python" in result["skills"]
    assert "SQL" in result["skills"]
    assert "IBM" in result["skills"]


def test_semantic_match_returns_recommendation_and_provider():
    result = semantic_match_resume_to_job(
        "Python Flask SQL REST API developer with React project experience",
        ["Python", "Flask", "SQL", "React"],
        "Looking for Python Flask SQL API developer with Git experience",
    )
    assert result["job_match_score"] > 50
    assert result["recommendation"] in {"Shortlist", "Review", "Hold", "Reject"}
    assert result["embedding_provider"] in {"local-token-cosine", "sentence-transformers"}


def test_student_guidance_contains_roadmap():
    guidance = build_student_guidance(
        {
            "category": "Software Development",
            "skills": ["Python", "SQL"],
        }
    )
    assert guidance["target_role"] == "Software Development"
    assert guidance["career_roadmap"]
    assert "React" in guidance["missing_skills"]
