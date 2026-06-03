# Render Deployment Guide

## Backend Service

Use the included `render.yaml` blueprint.

Required environment variables:

```env
SECRET_KEY=replace-with-strong-secret
FLASK_ENV=production
USE_WATSONX=true
WATSONX_API_KEY=your-key
WATSONX_PROJECT_ID=your-project-id
WATSONX_URL=https://us-south.ml.cloud.ibm.com
ALLOWED_ORIGINS=https://your-render-url.onrender.com
```

Optional real embeddings:

```env
EMBEDDING_PROVIDER=sentence-transformers
SENTENCE_TRANSFORMER_MODEL=all-MiniLM-L6-v2
```

If using Sentence Transformers on Render, install:

```bash
pip install -r backend/requirements-embeddings.txt
```

For free-tier deployments, keep `EMBEDDING_PROVIDER=local` because transformer model downloads can be slow and memory-heavy.

## Demo Screenshots

Recommended screenshots for README:

1. Login/register card.
2. Recruiter dashboard with candidate pipeline.
3. Candidate detail panel with notes.
4. Student guidance panel.
5. Analytics section with charts.

## Demo Video Script

1. Register as recruiter.
2. Upload 5 demo resumes using batch upload.
3. Sort candidates by score.
4. Update one status to Shortlist.
5. Open candidate detail and add a note.
6. Download PDF report.
7. Register/login as student and open Guidance.

## Production Notes

- Move SQLite to PostgreSQL for multi-user deployment.
- Move uploaded resumes to S3-compatible object storage.
- Set `secure=True` cookies in production, already enabled by `FLASK_ENV=production`.
- Restrict `ALLOWED_ORIGINS` to your deployed frontend/backend domain.
