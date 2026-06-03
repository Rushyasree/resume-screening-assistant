# Phase 4 Update Report

## Implemented

- Optional real embedding provider using Sentence Transformers.
- `backend/requirements-embeddings.txt` for embedding dependencies.
- Batch resume upload endpoint for recruiters/admins.
- Multi-file upload support in the dashboard.
- Candidate detail API and dashboard panel.
- Recruiter notes API and note form.
- Status history in candidate detail.
- Role-aware dashboard behavior:
  - Recruiter/Admin: pipeline, status, reports, detail, notes, analytics.
  - Student: upload and career guidance.
- Pytest unit tests for matching, guidance, and skill extraction.
- Render deployment guide with screenshot/demo-video checklist.

## New Endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/api/resumes/batch` | Upload 2-20 PDF resumes in one request |
| `GET` | `/api/resumes/<id>` | Candidate detail with notes and status history |
| `POST` | `/api/resumes/<id>/notes` | Add recruiter note |

## Embedding Mode

Default mode stays lightweight:

```env
EMBEDDING_PROVIDER=local
```

Real embeddings:

```env
EMBEDDING_PROVIDER=sentence-transformers
SENTENCE_TRANSFORMER_MODEL=all-MiniLM-L6-v2
```

Install optional dependencies:

```bash
pip install -r backend/requirements-embeddings.txt
```
