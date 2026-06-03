from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import requests

BASE_URL = "http://127.0.0.1:5000"
ROOT = Path(__file__).resolve().parents[1]
DEMO_RESUME = ROOT / "data" / "demo_resumes" / "software_development_resume.pdf"
DEMO_RESUME_2 = ROOT / "data" / "demo_resumes" / "data_science_resume.pdf"


def assert_status(response: requests.Response, expected: int, label: str) -> dict:
    if response.status_code != expected:
        raise AssertionError(f"{label}: expected {expected}, got {response.status_code}: {response.text}")
    if response.headers.get("content-type", "").startswith("application/json"):
        return response.json()
    return {}


def main() -> int:
    session = requests.Session()
    suffix = int(time.time())
    email = f"demo.recruiter.{suffix}@example.com"
    password = "DemoPass123"

    assert_status(session.get(f"{BASE_URL}/api/health"), 200, "health")
    assert_status(
        session.post(
            f"{BASE_URL}/api/auth/register",
            json={"name": "Demo Recruiter", "email": email, "password": password, "role": "recruiter"},
        ),
        201,
        "register",
    )
    assert_status(session.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": password}), 200, "login")
    assert_status(session.get(f"{BASE_URL}/api/analytics"), 200, "analytics")

    with DEMO_RESUME.open("rb") as handle:
        upload = assert_status(
            session.post(
                f"{BASE_URL}/api/resumes",
                files={"resume": ("software_development_resume.pdf", handle, "application/pdf")},
                data={"required_skills": ["Python", "SQL", "Flask", "React"]},
            ),
            201,
            "upload resume",
        )
    resume_id = upload["resume_id"]
    with DEMO_RESUME.open("rb") as first, DEMO_RESUME_2.open("rb") as second:
        batch = assert_status(
            session.post(
                f"{BASE_URL}/api/resumes/batch",
                files=[
                    ("resumes", ("software_development_resume.pdf", first, "application/pdf")),
                    ("resumes", ("data_science_resume.pdf", second, "application/pdf")),
                ],
                data={"required_skills": ["Python", "SQL"]},
            ),
            201,
            "batch upload",
        )
    if batch["processed"] != 2:
        raise AssertionError("batch upload did not process both resumes")
    assert_status(session.patch(f"{BASE_URL}/api/resumes/{resume_id}/status", json={"status": "Hold"}), 200, "status update")
    assert_status(session.post(f"{BASE_URL}/api/resumes/{resume_id}/notes", json={"note": "Strong demo candidate."}), 201, "add note")
    detail = assert_status(session.get(f"{BASE_URL}/api/resumes/{resume_id}"), 200, "candidate detail")
    if not detail.get("notes") or "status_history" not in detail:
        raise AssertionError("candidate detail missing notes or status history")
    match = assert_status(
        session.post(
            f"{BASE_URL}/api/resumes/{resume_id}/match",
            json={"description": "Python Flask SQL React API developer with Git and teamwork skills."},
        ),
        200,
        "job match",
    )
    if "embedding_provider" not in match:
        raise AssertionError("match response missing embedding provider")
    guidance = assert_status(session.get(f"{BASE_URL}/api/resumes/{resume_id}/guidance"), 200, "student guidance")
    if "career_roadmap" not in guidance or "missing_skills" not in guidance:
        raise AssertionError("student guidance response missing expected fields")
    report = session.get(f"{BASE_URL}/api/resumes/{resume_id}/report.pdf")
    if report.status_code != 200 or "application/pdf" not in report.headers.get("content-type", ""):
        raise AssertionError("PDF report failed")
    csv_report = session.get(f"{BASE_URL}/api/reports/candidates.csv")
    if csv_report.status_code != 200 or "candidate" not in csv_report.text:
        raise AssertionError("CSV report failed")
    analytics = assert_status(session.get(f"{BASE_URL}/api/analytics"), 200, "analytics after upload")
    if "upload_trend" not in analytics or "score_buckets" not in analytics:
        raise AssertionError("analytics missing Phase 3 fields")

    print(json.dumps({"ok": True, "resume_id": resume_id}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
