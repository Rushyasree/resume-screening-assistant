from __future__ import annotations

import json
import re
from functools import lru_cache
from typing import Any

from config import Config, PROMPT_PATH
from skill_engine import ROLE_RECOMMENDATIONS, extract_skills, infer_category, infer_experience_level

ALLOWED_CATEGORIES = {"Data Science", "Software Development", "Human Resources", "Marketing", "Finance"}


def _build_fallback(text: str, raw_response: str | None = None) -> dict[str, Any]:
    skill_data = extract_skills(text)
    category, confidence = infer_category(text, skill_data["skills"])
    return {
        "category": category,
        "confidence": confidence,
        "skills": skill_data["skills"],
        "skill_groups": skill_data["skill_groups"],
        "skill_confidence": skill_data["confidence"],
        "experience_level": infer_experience_level(text),
        "reason": "Classified using keyword and skill evidence because structured LLM output was unavailable or invalid.",
        "recommended_roles": ROLE_RECOMMENDATIONS.get(category, []),
        "raw_response": raw_response,
    }


@lru_cache(maxsize=1)
def _get_model():
    if not Config.USE_WATSONX or not Config.WATSONX_API_KEY or not Config.WATSONX_PROJECT_ID:
        return None
    from ibm_watsonx_ai.foundation_models import ModelInference

    return ModelInference(
        model_id=Config.WATSONX_MODEL_ID,
        credentials={"api_key": Config.WATSONX_API_KEY, "url": Config.WATSONX_URL},
        project_id=Config.WATSONX_PROJECT_ID,
    )


def _load_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def _extract_json(text: str) -> dict[str, Any]:
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    candidate = fenced.group(1) if fenced else text
    if not candidate.strip().startswith("{"):
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start >= 0 and end > start:
            candidate = candidate[start : end + 1]
    return json.loads(candidate)


def _validate_result(result: dict[str, Any], resume_text: str, raw_response: str | None) -> dict[str, Any]:
    category = result.get("category")
    if category not in ALLOWED_CATEGORIES:
        return _build_fallback(resume_text, raw_response)

    skill_data = extract_skills(resume_text)
    llm_skills = [str(skill).strip() for skill in result.get("skills", []) if str(skill).strip()]
    merged_skills = sorted(set(llm_skills + skill_data["skills"]))

    confidence = result.get("confidence", 0.5)
    try:
        confidence = max(0, min(1, float(confidence)))
    except (TypeError, ValueError):
        confidence = 0.5

    return {
        "category": category,
        "confidence": round(confidence, 2),
        "skills": merged_skills,
        "skill_groups": skill_data["skill_groups"],
        "skill_confidence": skill_data["confidence"],
        "experience_level": result.get("experience_level") or infer_experience_level(resume_text),
        "reason": str(result.get("reason") or "Classification generated from resume evidence."),
        "recommended_roles": result.get("recommended_roles") or ROLE_RECOMMENDATIONS.get(category, []),
        "raw_response": raw_response,
    }


def classify_resume(text: str) -> dict[str, Any]:
    if not text or len(text.strip()) < 40:
        raise ValueError("Resume text is too short to classify. The PDF may be scanned or unreadable.")

    model = _get_model()
    if model is None:
        return _build_fallback(text)

    prompt = _load_prompt().format(resume_text=text[:12000])
    try:
        response = model.generate(prompt=prompt, params={"temperature": 0, "max_new_tokens": 600})
        raw = response["results"][0]["generated_text"].strip()
        parsed = _extract_json(raw)
        return _validate_result(parsed, text, raw)
    except Exception as exc:
        fallback = _build_fallback(text, str(exc))
        fallback["reason"] = f"Fallback classification used after AI response handling failed: {exc}"
        return fallback
