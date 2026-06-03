from __future__ import annotations

import re
from collections import Counter

SKILL_ONTOLOGY = {
    "programming_languages": ["python", "java", "javascript", "typescript", "c++", "c#", "r", "go", "php", "ruby", "swift", "kotlin", "sql"],
    "frameworks": ["react", "angular", "vue", "node", "express", "flask", "django", "fastapi", "spring", "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy"],
    "databases": ["mysql", "postgresql", "mongodb", "sqlite", "oracle", "redis", "firebase", "supabase"],
    "cloud_tools": ["aws", "azure", "gcp", "docker", "kubernetes", "render", "vercel", "git", "github", "linux"],
    "business_tools": ["excel", "power bi", "tableau", "jira", "figma", "canva", "salesforce"],
    "soft_skills": ["leadership", "communication", "teamwork", "problem solving", "critical thinking", "adaptability", "presentation"],
    "certifications": ["aws certified", "azure fundamentals", "google cloud", "ibm", "microsoft certified", "scrum", "pmp"],
}

CATEGORY_KEYWORDS = {
    "Data Science": ["machine learning", "deep learning", "data science", "pandas", "numpy", "tensorflow", "pytorch", "statistics", "analytics", "power bi", "tableau"],
    "Software Development": ["software", "developer", "frontend", "backend", "full stack", "react", "node", "flask", "django", "java", "api"],
    "Human Resources": ["human resources", "recruitment", "talent", "payroll", "employee", "onboarding", "hr"],
    "Marketing": ["marketing", "seo", "social media", "campaign", "branding", "content", "advertising"],
    "Finance": ["finance", "accounting", "audit", "investment", "financial", "tax", "budget"],
}

ROLE_RECOMMENDATIONS = {
    "Data Science": ["Data Analyst", "Junior Data Scientist", "ML Engineer"],
    "Software Development": ["Backend Developer", "Full Stack Developer", "Software Engineer"],
    "Human Resources": ["HR Associate", "Talent Acquisition Coordinator"],
    "Marketing": ["Digital Marketing Associate", "Marketing Analyst"],
    "Finance": ["Financial Analyst", "Accounting Associate"],
}


def normalize_skill(skill: str) -> str:
    skill = skill.strip()
    aliases = {
        "api": "API",
        "aws": "AWS",
        "azure": "Azure",
        "gcp": "GCP",
        "ibm": "IBM",
        "js": "JavaScript",
        "postgres": "PostgreSQL",
        "rest api": "REST API",
        "sql": "SQL",
        "node.js": "Node",
        "react.js": "React",
    }
    return aliases.get(skill.lower(), skill.title() if skill.islower() else skill)


def extract_skills(text: str) -> dict:
    lower = text.lower()
    found: list[str] = []
    by_group: dict[str, list[str]] = {}

    for group, skills in SKILL_ONTOLOGY.items():
        group_matches = []
        for skill in skills:
            pattern = r"(?<![a-z0-9+#.])" + re.escape(skill.lower()) + r"(?![a-z0-9+#.])"
            if re.search(pattern, lower):
                normalized = normalize_skill(skill)
                group_matches.append(normalized)
                found.append(normalized)
        by_group[group] = sorted(set(group_matches))

    counts = Counter(found)
    return {
        "skills": sorted(counts.keys()),
        "skill_frequency": dict(counts),
        "skill_groups": by_group,
        "confidence": round(min(0.95, 0.35 + len(counts) * 0.05), 2) if counts else 0.25,
    }


def infer_category(text: str, skills: list[str] | None = None) -> tuple[str, float]:
    lower = text.lower()
    scores: dict[str, int] = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        scores[category] = sum(1 for keyword in keywords if keyword in lower)

    if skills:
        skill_text = " ".join(skills).lower()
        for category, keywords in CATEGORY_KEYWORDS.items():
            scores[category] += sum(1 for keyword in keywords if keyword in skill_text)

    best_category, best_score = max(scores.items(), key=lambda kv: kv[1])
    confidence = 0.45 if best_score == 0 else min(0.88, 0.5 + best_score * 0.08)
    return best_category, round(confidence, 2)


def infer_experience_level(text: str) -> str:
    lower = text.lower()
    year_matches = [int(match) for match in re.findall(r"(\d+)\+?\s*(?:years|yrs)", lower)]
    max_years = max(year_matches) if year_matches else 0
    if max_years >= 5:
        return "Senior"
    if max_years >= 2 or "internship" in lower or "intern" in lower:
        return "Intermediate"
    return "Entry Level"


def score_candidate(resume_text: str, extracted_skills: list[str], job_required_skills: list[str] | None = None) -> dict:
    required = {normalize_skill(skill).lower() for skill in (job_required_skills or []) if skill.strip()}
    extracted = {skill.lower() for skill in extracted_skills}

    if required:
        matched = sorted(required & extracted)
        missing = sorted(required - extracted)
        skills_match = round((len(matched) / len(required)) * 100, 2)
    else:
        matched = sorted(extracted)
        missing = []
        skills_match = min(100, len(extracted) * 8)

    lower = resume_text.lower()
    experience_match = 80 if any(term in lower for term in ["experience", "intern", "project", "worked"]) else 45
    education_match = 80 if any(term in lower for term in ["b.tech", "bachelor", "degree", "university", "college"]) else 50
    project_relevance = 85 if "project" in lower else 45
    certification_score = 80 if any(term in lower for term in ["certification", "certified", "certificate"]) else 35

    overall = round(
        skills_match * 0.4 + experience_match * 0.2 + education_match * 0.15 + project_relevance * 0.15 + certification_score * 0.1,
        2,
    )
    if overall >= 78:
        status = "Shortlist"
    elif overall >= 58:
        status = "Review"
    elif overall >= 42:
        status = "Needs More Information"
    else:
        status = "Reject"

    explanation = f"Score is driven by {len(matched)} matched skills"
    if missing:
        explanation += f" and {len(missing)} missing required skills."
    else:
        explanation += ", visible project or education signals, and extracted technical keywords."

    return {
        "overall_score": overall,
        "skills_match": skills_match,
        "experience_match": experience_match,
        "education_match": education_match,
        "project_relevance": project_relevance,
        "certification_score": certification_score,
        "matched_skills": [normalize_skill(skill) for skill in matched],
        "missing_skills": [normalize_skill(skill) for skill in missing],
        "status": status,
        "explanation": explanation,
    }


def extract_required_skills(description: str) -> list[str]:
    return extract_skills(description)["skills"]
