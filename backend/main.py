from __future__ import annotations

import os
import uuid
from io import BytesIO
from pathlib import Path

from flask import Flask, jsonify, make_response, request, send_file, send_from_directory
from flask_cors import CORS
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename

from auth_service import current_user_from_request, login_user, logout_user, register_user, require_auth
from career_guidance import build_student_guidance
from classifier import classify_resume
from config import Config, FRONTEND_DIR, UPLOAD_DIR, ensure_runtime_dirs
from database import (
    analytics_summary,
    create_classification,
    create_job_description,
    create_note,
    create_resume,
    create_score,
    fetch_resume_detail,
    fetch_job_descriptions,
    fetch_resume_file,
    fetch_resumes,
    fetch_notes,
    fetch_status_history,
    init_db,
    log_audit,
    update_candidate_status,
)
from matching import semantic_match_resume_to_job
from reporting import build_candidate_pdf_report, build_candidates_csv
from resume_parser import ResumeParseError, extract_text_from_pdf
from skill_engine import extract_required_skills, score_candidate

app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")
app.config.from_object(Config)
CORS(app, resources={r"/api/*": {"origins": Config.ALLOWED_ORIGINS}}, supports_credentials=True)
ensure_runtime_dirs()
init_db()


def _json_error(message: str, status: int):
    return jsonify({"error": message}), status


def _allowed_file(file) -> bool:
    filename = file.filename or ""
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return extension in Config.ALLOWED_EXTENSIONS and file.mimetype in Config.ALLOWED_MIME_TYPES


def _save_upload(file) -> tuple[str, Path]:
    original = secure_filename(file.filename or "resume.pdf")
    extension = original.rsplit(".", 1)[-1].lower()
    stored = f"{uuid.uuid4().hex}.{extension}"
    path = UPLOAD_DIR / stored
    file.save(path)
    return original, path


def _analyze_saved_resume(original_filename: str, filepath: Path, job_skills: list[str]) -> dict:
    text = extract_text_from_pdf(str(filepath))
    classification = classify_resume(text)
    score = score_candidate(text, classification.get("skills", []), job_skills)

    resume_id = create_resume(original_filename, filepath.name, filepath, os.path.getsize(filepath), text)
    create_classification(resume_id, classification)
    create_score(resume_id, score)
    log_audit("resume_classified", "resume", resume_id, {"filename": original_filename})
    return {"resume_id": resume_id, "classification": classification, "score": score}


def _set_session_cookie(response, token: str, expires_at):
    response.set_cookie(
        "session_token",
        token,
        httponly=True,
        secure=Config.ENV == "production",
        samesite="Lax",
        expires=expires_at,
    )
    return response


@app.errorhandler(RequestEntityTooLarge)
def handle_large_file(_exc):
    return _json_error(f"File too large. Maximum upload size is {Config.MAX_CONTENT_LENGTH // (1024 * 1024)} MB.", 413)


@app.route("/")
def serve_index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/<path:path>")
def serve_static_files(path):
    return send_from_directory(app.static_folder, path)


@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "environment": Config.ENV})


@app.post("/api/auth/register")
def register():
    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "").strip()
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""
    role = payload.get("role") or "recruiter"
    if not name or not email or not password:
        return _json_error("Name, email, and password are required.", 400)
    try:
        user = register_user(name, email, password, role)
        log_audit("user_registered", "user", user["id"], {"role": user["role"]})
        return jsonify({"user": user}), 201
    except Exception as exc:
        return _json_error(str(exc), 400)


@app.post("/api/auth/login")
def login():
    payload = request.get_json(silent=True) or {}
    try:
        user, token, expires_at = login_user(payload.get("email", ""), payload.get("password", ""))
        response = make_response(jsonify({"user": user}))
        return _set_session_cookie(response, token, expires_at)
    except ValueError as exc:
        return _json_error(str(exc), 401)


@app.post("/api/auth/logout")
def logout():
    user = current_user_from_request()
    logout_user(user.get("token") if user else request.cookies.get("session_token"))
    response = make_response(jsonify({"ok": True}))
    response.delete_cookie("session_token")
    return response


@app.get("/api/auth/me")
def me():
    user = current_user_from_request()
    return jsonify({"user": user if user else None})


@app.post("/api/resumes")
@require_auth("admin", "recruiter", "student")
def upload_resume():
    file = request.files.get("resume")
    job_skills = request.form.getlist("required_skills")

    if not file:
        return _json_error("Please upload a PDF resume.", 400)
    if not _allowed_file(file):
        return _json_error("Only valid PDF files are accepted.", 400)

    original_filename, filepath = _save_upload(file)
    try:
        return jsonify(_analyze_saved_resume(original_filename, filepath, job_skills)), 201
    except (ResumeParseError, ValueError) as exc:
        filepath.unlink(missing_ok=True)
        return _json_error(str(exc), 422)
    except Exception as exc:
        filepath.unlink(missing_ok=True)
        return _json_error(f"Classification failed: {exc}", 500)


@app.post("/api/resumes/batch")
@require_auth("admin", "recruiter")
def upload_resumes_batch():
    files = request.files.getlist("resumes")
    job_skills = request.form.getlist("required_skills")
    if not files:
        return _json_error("Please upload at least one PDF resume.", 400)
    if len(files) > 20:
        return _json_error("Batch upload supports a maximum of 20 resumes.", 400)

    results = []
    for file in files:
        if not _allowed_file(file):
            results.append({"filename": file.filename, "ok": False, "error": "Only valid PDF files are accepted."})
            continue
        original_filename, filepath = _save_upload(file)
        try:
            result = _analyze_saved_resume(original_filename, filepath, job_skills)
            results.append({"filename": original_filename, "ok": True, **result})
        except Exception as exc:
            filepath.unlink(missing_ok=True)
            results.append({"filename": original_filename, "ok": False, "error": str(exc)})
    return jsonify({"items": results, "processed": len(results)}), 207 if any(not item["ok"] for item in results) else 201


@app.post("/classify")
def legacy_classify():
    response = upload_resume()
    if isinstance(response, tuple):
        return response
    payload = response.get_json() or {}
    classification = payload.get("classification", {})
    return jsonify({"category": classification.get("category"), **payload}), response.status_code


@app.get("/api/resumes")
@require_auth("admin", "recruiter", "student")
def list_resumes():
    return jsonify({"items": fetch_resumes()})


@app.get("/api/resumes/<int:resume_id>/download")
@require_auth("admin", "recruiter")
def download_resume(resume_id: int):
    row = fetch_resume_file(resume_id)
    if not row:
        return _json_error("Resume not found.", 404)
    return send_from_directory(UPLOAD_DIR, row["stored_filename"], as_attachment=True, download_name=row["original_filename"])


@app.get("/api/resumes/<int:resume_id>")
@require_auth("admin", "recruiter", "student")
def resume_detail(resume_id: int):
    candidate = fetch_resume_detail(resume_id)
    if not candidate:
        return _json_error("Resume not found.", 404)
    candidate.pop("file_path", None)
    candidate.pop("stored_filename", None)
    candidate["notes"] = fetch_notes(resume_id)
    candidate["status_history"] = fetch_status_history(resume_id)
    return jsonify(candidate)


@app.post("/api/resumes/<int:resume_id>/notes")
@require_auth("admin", "recruiter")
def add_candidate_note(resume_id: int):
    payload = request.get_json(silent=True) or {}
    note = (payload.get("note") or "").strip()
    if len(note) < 2:
        return _json_error("Note must contain at least 2 characters.", 400)
    candidate = fetch_resume_detail(resume_id)
    if not candidate:
        return _json_error("Resume not found.", 404)
    note_id = create_note(resume_id, note, candidate.get("status"))
    log_audit("candidate_note_added", "resume", resume_id, {"note_id": note_id})
    return jsonify({"id": note_id, "resume_id": resume_id, "note": note}), 201


@app.patch("/api/resumes/<int:resume_id>/status")
@require_auth("admin", "recruiter")
def set_candidate_status(resume_id: int):
    payload = request.get_json(silent=True) or {}
    status = payload.get("status")
    allowed = {"Shortlist", "Review", "Reject", "Hold", "Needs More Information"}
    if status not in allowed:
        return _json_error("Invalid status.", 400)
    if not update_candidate_status(resume_id, status):
        return _json_error("Candidate score not found.", 404)
    log_audit("candidate_status_updated", "resume", resume_id, {"status": status})
    return jsonify({"id": resume_id, "status": status})


@app.post("/api/resumes/<int:resume_id>/match")
@require_auth("admin", "recruiter", "student")
def match_resume_to_job(resume_id: int):
    candidate = fetch_resume_detail(resume_id)
    if not candidate:
        return _json_error("Resume not found.", 404)
    payload = request.get_json(silent=True) or {}
    description = (payload.get("description") or "").strip()
    if len(description) < 30:
        return _json_error("Job description must contain at least 30 characters.", 400)
    result = semantic_match_resume_to_job(candidate.get("text_excerpt") or "", candidate.get("skills") or [], description)
    return jsonify(result)


@app.get("/api/resumes/<int:resume_id>/guidance")
@require_auth("admin", "recruiter", "student")
def student_guidance(resume_id: int):
    candidate = fetch_resume_detail(resume_id)
    if not candidate:
        return _json_error("Resume not found.", 404)
    return jsonify(build_student_guidance(candidate))


@app.get("/api/resumes/<int:resume_id>/report.pdf")
@require_auth("admin", "recruiter")
def candidate_pdf_report(resume_id: int):
    candidate = fetch_resume_detail(resume_id)
    if not candidate:
        return _json_error("Resume not found.", 404)
    pdf = build_candidate_pdf_report(candidate)
    return send_file(
        BytesIO(pdf),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"candidate-report-{resume_id}.pdf",
    )


@app.get("/api/reports/candidates.csv")
@require_auth("admin", "recruiter")
def candidates_csv_report():
    csv_text = build_candidates_csv(fetch_resumes())
    response = make_response(csv_text)
    response.headers["Content-Type"] = "text/csv"
    response.headers["Content-Disposition"] = "attachment; filename=candidate-report.csv"
    return response


@app.post("/api/job-descriptions")
@require_auth("admin", "recruiter", "student")
def create_job():
    payload = request.get_json(silent=True) or {}
    title = (payload.get("title") or "Untitled Role").strip()
    description = (payload.get("description") or "").strip()
    if len(description) < 30:
        return _json_error("Job description must contain at least 30 characters.", 400)
    required_skills = extract_required_skills(description)
    job_id = create_job_description(title, description, required_skills)
    log_audit("job_description_created", "job_description", job_id, {"title": title})
    return jsonify({"id": job_id, "title": title, "required_skills": required_skills}), 201


@app.get("/api/job-descriptions")
@require_auth("admin", "recruiter", "student")
def list_jobs():
    return jsonify({"items": fetch_job_descriptions()})


@app.get("/api/analytics")
@require_auth("admin", "recruiter")
def analytics():
    return jsonify(analytics_summary())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=Config.ENV == "development")
