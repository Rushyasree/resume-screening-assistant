# Phase 2 Upgrade Report

## Implemented Features

- Rebuilt and validated the Python environment.
- Added anonymized demo resume PDFs under `data/demo_resumes/`.
- Added bcrypt-backed registration and login.
- Added session-cookie authentication.
- Added roles: `admin`, `recruiter`, and `student`.
- Protected recruiter APIs behind login.
- Added candidate status workflow: `Shortlist`, `Review`, `Hold`, `Reject`.
- Added candidate PDF report export.
- Added candidate CSV report export.
- Added semantic-lite resume-to-job matching endpoint.
- Added dependency validation script and report generation.
- Added live API smoke test script.

## Demo Accounts

Create a local account from the dashboard using the registration form. The smoke test also creates a temporary recruiter account with a timestamped email.

## Demo Resumes

Five fictional PDFs are available:

- `data/demo_resumes/data_science_resume.pdf`
- `data/demo_resumes/software_development_resume.pdf`
- `data/demo_resumes/hr_resume.pdf`
- `data/demo_resumes/marketing_resume.pdf`
- `data/demo_resumes/finance_resume.pdf`

These are safe for GitHub because all identities and content are fictional.

## New API Endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/api/auth/register` | Create a local account |
| `POST` | `/api/auth/login` | Login and set secure session cookie |
| `POST` | `/api/auth/logout` | Logout and clear session |
| `GET` | `/api/auth/me` | Return current session user |
| `PATCH` | `/api/resumes/<id>/status` | Update recruiter status |
| `POST` | `/api/resumes/<id>/match` | Compare resume to a job description |
| `GET` | `/api/resumes/<id>/report.pdf` | Download candidate PDF report |
| `GET` | `/api/reports/candidates.csv` | Download CSV report |

## Validation Commands

```bash
.venv\Scripts\python.exe backend\validation_report.py
.venv\Scripts\python.exe backend\smoke_tests.py
```

## Current Test Result

The smoke test passed for:

- health check
- registration
- login
- analytics access
- resume upload
- classification
- status update
- PDF report export
- CSV report export

## Notes

- The matching engine uses a lightweight local semantic similarity method plus skill overlap, so it runs without downloading large transformer models.
- For research-level accuracy, the next upgrade should add sentence-transformers or Watson embeddings.
- `USE_WATSONX=false` is best for local testing. Set `USE_WATSONX=true` only after adding valid Watsonx credentials.
