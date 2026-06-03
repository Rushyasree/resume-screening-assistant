from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import DB_PATH, ensure_runtime_dirs
from skill_engine import normalize_skill

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    password_hash TEXT,
    role TEXT DEFAULT 'recruiter',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token TEXT NOT NULL UNIQUE,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS resumes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    original_filename TEXT NOT NULL,
    stored_filename TEXT NOT NULL UNIQUE,
    file_path TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    text_excerpt TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS job_descriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    required_skills TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS classifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resume_id INTEGER NOT NULL,
    category TEXT NOT NULL,
    confidence REAL NOT NULL,
    skills TEXT NOT NULL DEFAULT '[]',
    experience_level TEXT,
    reason TEXT,
    recommended_roles TEXT NOT NULL DEFAULT '[]',
    raw_response TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS candidate_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resume_id INTEGER NOT NULL,
    job_description_id INTEGER,
    overall_score REAL NOT NULL,
    skills_match REAL NOT NULL,
    experience_match REAL NOT NULL,
    education_match REAL NOT NULL,
    project_relevance REAL NOT NULL,
    certification_score REAL NOT NULL,
    matched_skills TEXT NOT NULL DEFAULT '[]',
    missing_skills TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL,
    job_match_score REAL DEFAULT 0,
    explanation TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE,
    FOREIGN KEY (job_description_id) REFERENCES job_descriptions(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resume_id INTEGER NOT NULL,
    note TEXT NOT NULL,
    status TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_name TEXT NOT NULL,
    payload TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    actor TEXT,
    action TEXT NOT NULL,
    entity_type TEXT,
    entity_id INTEGER,
    metadata TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);
"""

MIGRATIONS = [
    ("users", "password_hash", "ALTER TABLE users ADD COLUMN password_hash TEXT"),
    ("candidate_scores", "job_match_score", "ALTER TABLE candidate_scores ADD COLUMN job_match_score REAL DEFAULT 0"),
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def get_db():
    ensure_runtime_dirs()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_db() as conn:
        conn.executescript(SCHEMA)
        _run_migrations(conn)
        for role in ("admin", "recruiter", "student"):
            conn.execute(
                "INSERT OR IGNORE INTO roles (name, description) VALUES (?, ?)",
                (role, f"{role.title()} user role"),
            )


def _run_migrations(conn: sqlite3.Connection) -> None:
    for table, column, sql in MIGRATIONS:
        existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
        if column not in existing:
            conn.execute(sql)


def _json(value: Any) -> str:
    return json.dumps(value or [], ensure_ascii=False)


def create_resume(original_filename: str, stored_filename: str, file_path: Path, file_size: int, text: str) -> int:
    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO resumes (original_filename, stored_filename, file_path, file_size, text_excerpt, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (original_filename, stored_filename, str(file_path), file_size, text[:1200], now_iso()),
        )
        return int(cur.lastrowid)


def create_classification(resume_id: int, result: dict[str, Any]) -> int:
    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO classifications
            (resume_id, category, confidence, skills, experience_level, reason, recommended_roles, raw_response, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                resume_id,
                result["category"],
                float(result.get("confidence", 0)),
                _json(result.get("skills")),
                result.get("experience_level"),
                result.get("reason"),
                _json(result.get("recommended_roles")),
                result.get("raw_response"),
                now_iso(),
            ),
        )
        return int(cur.lastrowid)


def create_score(resume_id: int, score: dict[str, Any], job_description_id: int | None = None) -> int:
    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO candidate_scores
            (resume_id, job_description_id, overall_score, skills_match, experience_match, education_match,
             project_relevance, certification_score, matched_skills, missing_skills, status, job_match_score, explanation, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                resume_id,
                job_description_id,
                score["overall_score"],
                score["skills_match"],
                score["experience_match"],
                score["education_match"],
                score["project_relevance"],
                score["certification_score"],
                _json(score.get("matched_skills")),
                _json(score.get("missing_skills")),
                score["status"],
                score.get("job_match_score", score["overall_score"]),
                score.get("explanation"),
                now_iso(),
            ),
        )
        return int(cur.lastrowid)


def create_job_description(title: str, description: str, required_skills: list[str]) -> int:
    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO job_descriptions (title, description, required_skills, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (title, description, _json(required_skills), now_iso()),
        )
        return int(cur.lastrowid)


def fetch_resumes() -> list[dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT r.*, c.category, c.confidence, c.skills, c.experience_level, c.reason, c.recommended_roles,
                   s.overall_score, s.job_match_score, s.status, s.matched_skills, s.missing_skills, s.explanation
            FROM resumes r
            LEFT JOIN classifications c ON c.resume_id = r.id
            LEFT JOIN candidate_scores s ON s.resume_id = r.id
            ORDER BY r.created_at DESC
            """
        ).fetchall()
    items = [_decode_row(row) for row in rows]
    for item in items:
        item.pop("file_path", None)
        item.pop("stored_filename", None)
        item.pop("text_excerpt", None)
    return items


def fetch_resume_file(resume_id: int) -> sqlite3.Row | None:
    with get_db() as conn:
        return conn.execute("SELECT * FROM resumes WHERE id = ?", (resume_id,)).fetchone()


def fetch_resume_detail(resume_id: int) -> dict[str, Any] | None:
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT r.*, c.category, c.confidence, c.skills, c.experience_level, c.reason, c.recommended_roles,
                   s.overall_score, s.job_match_score, s.status, s.matched_skills, s.missing_skills, s.explanation
            FROM resumes r
            LEFT JOIN classifications c ON c.resume_id = r.id
            LEFT JOIN candidate_scores s ON s.resume_id = r.id
            WHERE r.id = ?
            """,
            (resume_id,),
        ).fetchone()
    return _decode_row(row) if row else None


def update_candidate_status(resume_id: int, status: str) -> bool:
    with get_db() as conn:
        result = conn.execute(
            """
            UPDATE candidate_scores
            SET status = ?
            WHERE id = (
                SELECT id FROM candidate_scores WHERE resume_id = ? ORDER BY created_at DESC LIMIT 1
            )
            """,
            (status, resume_id),
        )
        return result.rowcount > 0


def create_note(resume_id: int, note: str, status: str | None = None) -> int:
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO feedback (resume_id, note, status, created_at) VALUES (?, ?, ?, ?)",
            (resume_id, note, status, now_iso()),
        )
        return int(cur.lastrowid)


def fetch_notes(resume_id: int) -> list[dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM feedback WHERE resume_id = ? ORDER BY created_at DESC",
            (resume_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def fetch_status_history(resume_id: int) -> list[dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT action, metadata, created_at
            FROM audit_logs
            WHERE entity_type = 'resume' AND entity_id = ? AND action IN ('candidate_status_updated', 'resume_classified')
            ORDER BY created_at DESC
            """,
            (resume_id,),
        ).fetchall()
    history = []
    for row in rows:
        item = dict(row)
        try:
            item["metadata"] = json.loads(item.get("metadata") or "{}")
        except json.JSONDecodeError:
            item["metadata"] = {}
        history.append(item)
    return history


def create_user(name: str, email: str, password_hash: str, role: str) -> int:
    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO users (name, email, password_hash, role, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, email.lower(), password_hash, role, now_iso()),
        )
        return int(cur.lastrowid)


def fetch_user_by_email(email: str) -> dict[str, Any] | None:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email.lower(),)).fetchone()
    return dict(row) if row else None


def fetch_user_by_id(user_id: int) -> dict[str, Any] | None:
    with get_db() as conn:
        row = conn.execute("SELECT id, name, email, role, created_at FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(row) if row else None


def create_session(user_id: int, token: str, expires_at: str) -> None:
    with get_db() as conn:
        conn.execute(
            "INSERT INTO sessions (user_id, token, expires_at, created_at) VALUES (?, ?, ?, ?)",
            (user_id, token, expires_at, now_iso()),
        )


def fetch_session(token: str) -> dict[str, Any] | None:
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT s.*, u.name, u.email, u.role
            FROM sessions s
            JOIN users u ON u.id = s.user_id
            WHERE s.token = ?
            """,
            (token,),
        ).fetchone()
    return dict(row) if row else None


def delete_session(token: str) -> None:
    with get_db() as conn:
        conn.execute("DELETE FROM sessions WHERE token = ?", (token,))


def fetch_job_descriptions() -> list[dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM job_descriptions ORDER BY created_at DESC").fetchall()
    return [_decode_row(row) for row in rows]


def analytics_summary() -> dict[str, Any]:
    resumes = fetch_resumes()
    by_category: dict[str, int] = {}
    skill_frequency: dict[str, int] = {}
    status_counts: dict[str, int] = {}
    upload_trend: dict[str, int] = {}
    score_buckets = {"0-39": 0, "40-59": 0, "60-79": 0, "80-100": 0}
    scores: list[float] = []

    for item in resumes:
        category = item.get("category") or "Unclassified"
        by_category[category] = by_category.get(category, 0) + 1
        status = item.get("status") or "Review"
        status_counts[status] = status_counts.get(status, 0) + 1
        day = str(item.get("created_at") or "")[:10] or "Unknown"
        upload_trend[day] = upload_trend.get(day, 0) + 1
        if item.get("overall_score") is not None:
            score = float(item["overall_score"])
            scores.append(score)
            if score < 40:
                score_buckets["0-39"] += 1
            elif score < 60:
                score_buckets["40-59"] += 1
            elif score < 80:
                score_buckets["60-79"] += 1
            else:
                score_buckets["80-100"] += 1
        for skill in item.get("skills") or []:
            skill_frequency[skill] = skill_frequency.get(skill, 0) + 1

    return {
        "total_resumes": len(resumes),
        "average_score": round(sum(scores) / len(scores), 2) if scores else 0,
        "by_category": by_category,
        "skill_frequency": dict(sorted(skill_frequency.items(), key=lambda kv: kv[1], reverse=True)[:12]),
        "status_counts": status_counts,
        "upload_trend": dict(sorted(upload_trend.items())),
        "score_buckets": score_buckets,
        "recent_resumes": resumes[:8],
    }


def log_audit(action: str, entity_type: str | None = None, entity_id: int | None = None, metadata: dict[str, Any] | None = None) -> None:
    with get_db() as conn:
        conn.execute(
            "INSERT INTO audit_logs (action, entity_type, entity_id, metadata, created_at) VALUES (?, ?, ?, ?, ?)",
            (action, entity_type, entity_id, json.dumps(metadata or {}), now_iso()),
        )


def _decode_row(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    for key in ("skills", "recommended_roles", "matched_skills", "missing_skills", "required_skills"):
        if key in item and isinstance(item[key], str):
            try:
                item[key] = json.loads(item[key])
            except json.JSONDecodeError:
                item[key] = []
        if key in item and isinstance(item[key], list) and key != "recommended_roles":
            item[key] = [normalize_skill(str(value)) for value in item[key]]
    return item
