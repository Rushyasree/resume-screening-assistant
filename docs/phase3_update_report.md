# Phase 3 Update Report

## Implemented

- Candidate table sorting:
  - newest first
  - score high to low
  - score low to high
  - name A-Z
- Candidate table pagination.
- Student Assistant guidance endpoint:
  - strengths
  - missing skills
  - resume feedback
  - career roadmap
  - certification recommendations
  - learning resources
- Student guidance panel in dashboard.
- Upload trend analytics.
- Score distribution analytics.
- Additional Chart.js charts:
  - upload trend
  - score buckets
- Smoke test coverage for:
  - student guidance
  - upload trend analytics
  - score bucket analytics

## New Endpoint

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/resumes/<id>/guidance` | Generate student career guidance from resume analysis |

## Notes

This update keeps the system lightweight and runnable without downloading large embedding models. The next research-grade step is replacing semantic-lite matching with sentence-transformers or Watson embeddings.
