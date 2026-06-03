# Dependency Validation Report

Python: `3.12.13`

| Module | Status | Version / Detail |
| --- | --- | --- |
| `flask` | OK | 3.0.3 |
| `flask_cors` | OK | 4.0.1 |
| `PyPDF2` | OK | 3.0.1 |
| `dotenv` | OK | installed |
| `requests` | OK | 2.32.3 |
| `ibm_watsonx_ai` | OK | 1.1.16 |
| `bcrypt` | OK | 5.0.0 |
| `reportlab` | OK | 4.5.1 |

## Runtime Notes

- Local fallback classification works with `USE_WATSONX=false`.
- Watsonx classification requires valid `WATSONX_API_KEY` and `WATSONX_PROJECT_ID`.
- Recruiter APIs require login via `/api/auth/login`.