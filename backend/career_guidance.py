from __future__ import annotations

ROLE_SKILL_MAP = {
    "Data Science": ["Python", "SQL", "Statistics", "Pandas", "Machine Learning", "Power BI"],
    "Software Development": ["Python", "JavaScript", "SQL", "Git", "REST API", "React"],
    "Human Resources": ["Recruitment", "Onboarding", "Excel", "Communication", "HR Analytics"],
    "Marketing": ["SEO", "Google Analytics", "Content Marketing", "Campaign Management", "Branding"],
    "Finance": ["Accounting", "Excel", "Financial Analysis", "Budgeting", "Power BI"],
}

CERTIFICATIONS = {
    "Data Science": ["IBM Data Science Professional Certificate", "Google Data Analytics Certificate"],
    "Software Development": ["Meta Front-End Developer Certificate", "AWS Cloud Practitioner"],
    "Human Resources": ["HRCI Associate Professional in HR", "LinkedIn Recruiting Foundations"],
    "Marketing": ["Google Digital Marketing Certificate", "HubSpot Content Marketing"],
    "Finance": ["NISM Foundation Certification", "Microsoft Excel Expert"],
}

LEARNING_RESOURCES = {
    "Data Science": ["Kaggle Learn", "Google Machine Learning Crash Course", "IBM SkillsBuild"],
    "Software Development": ["freeCodeCamp", "Full Stack Open", "Microsoft Learn"],
    "Human Resources": ["AIHR Academy free resources", "LinkedIn Learning HR courses"],
    "Marketing": ["Google Skillshop", "HubSpot Academy", "Meta Blueprint"],
    "Finance": ["Corporate Finance Institute free courses", "Microsoft Learn Excel modules"],
}


def build_student_guidance(candidate: dict) -> dict:
    category = candidate.get("category") or "Software Development"
    current_skills = {skill.lower() for skill in candidate.get("skills") or []}
    target_skills = ROLE_SKILL_MAP.get(category, ROLE_SKILL_MAP["Software Development"])
    missing = [skill for skill in target_skills if skill.lower() not in current_skills]
    strengths = [skill for skill in target_skills if skill.lower() in current_skills]

    roadmap = [
        f"Strengthen fundamentals for {category}.",
        f"Build one portfolio project using {', '.join((missing or target_skills)[:3])}.",
        "Add measurable project outcomes to the resume.",
        "Prepare interview stories using the STAR method.",
    ]

    return {
        "target_role": category,
        "strengths": strengths,
        "missing_skills": missing,
        "resume_feedback": [
            "Add quantified achievements wherever possible.",
            "Keep projects close to the target role.",
            "Move the strongest technical skills near the top.",
        ],
        "career_roadmap": roadmap,
        "certification_recommendations": CERTIFICATIONS.get(category, []),
        "learning_resources": LEARNING_RESOURCES.get(category, []),
    }
