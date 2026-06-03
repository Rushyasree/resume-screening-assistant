from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
DB_PATH = DATA_DIR / "recruitment.db"
PROMPT_PATH = BACKEND_DIR / "prompts" / "job_classifier_prompt.txt"

load_dotenv(BASE_DIR / ".env")

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-change-me")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_UPLOAD_MB", "8")) * 1024 * 1024
    ALLOWED_EXTENSIONS = {"pdf"}
    ALLOWED_MIME_TYPES = {"application/pdf", "application/x-pdf"}
    ALLOWED_ORIGINS = [origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:5000,http://127.0.0.1:5000").split(",") if origin.strip()]
    WATSONX_API_KEY = os.getenv("WATSONX_API_KEY")
    WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID")
    WATSONX_URL = os.getenv("WATSONX_URL") or os.getenv("WATSONX_REGION_URL") or "https://us-south.ml.cloud.ibm.com"
    WATSONX_MODEL_ID = os.getenv("WATSONX_MODEL_ID", "ibm/granite-3-3-8b-instruct")
    USE_WATSONX = os.getenv("USE_WATSONX", "true").lower() == "true"
    ENV = os.getenv("FLASK_ENV", "production")


def ensure_runtime_dirs() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
