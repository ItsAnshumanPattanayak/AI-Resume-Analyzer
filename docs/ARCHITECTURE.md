# Architecture

## Overview

AI Resume Analyzer is a React/Vite client backed by a FastAPI service. The
browser uploads PDF or DOCX files to authenticated endpoints. The API validates
the upload, extracts text, runs deterministic extraction and scoring services,
and stores the resulting report for the authenticated owner.

See the [system architecture diagram](images/diagrams/system-architecture.svg)
and [analysis workflow](images/diagrams/analysis-workflow.svg).

## Frontend modules

- `frontend/src/App.jsx` coordinates authentication, analysis modes, requests,
  results, history, and the developer/footer presentation.
- `frontend/src/context/` restores the current user and manages the JWT session.
- `frontend/src/services/api.js` is the Axios API client.
- `frontend/src/components/` contains the upload form, mode tabs, result panels,
  history UI, role explanations, improvement feedback, and branding.
- `frontend/src/index.css` defines the shared dark glass-card visual system and
  responsive layout.

The four user-facing modes are Analyze, Parse, Roles, and Improve. There is no
client-side router; the application is a single authenticated dashboard.

## Backend modules

- `backend/app/main.py` defines the FastAPI application, health check, auth,
  resume, recommendation, improvement, and history routes.
- `parser.py` validates and extracts PDF/DOCX text; `extractor.py` identifies
  candidate information, sections, links, and skills.
- `skills.py`, `similarity.py`, and `ats.py` provide deterministic skill,
  TF-IDF, combined-similarity, and ATS-style calculations.
- `semantic.py` performs Sentence Transformer analysis when the configured model
  is available.
- `recommender.py` ranks repository-maintained technical roles with explainable
  exact-skill and semantic components.
- `advisor.py` produces deterministic, rule-based resume feedback.
- `schemas.py` defines typed Pydantic responses; `config.py` loads environment
  settings; `database.py`, `models.py`, `users.py`, and `history.py` provide the
  SQLAlchemy persistence layer.

## Request lifecycle

1. The frontend authenticates or restores a JWT access token.
2. Axios sends the token as a bearer header with an uploaded file.
3. FastAPI validates authentication, rate limits, file type/signature, and size.
4. PDF/DOCX text is extracted and passed to structured extraction.
5. The selected mode runs the relevant scoring, semantic, recommendation, or
   feedback services. Expensive blocking analysis is run through a threadpool.
6. Results are serialized, stored in analysis history, and rendered by React.

## Data and persistence

SQLite is supported for local development and CI. PostgreSQL is supported by
SQLAlchemy and is used by the Docker Compose setup. Alembic applies migrations;
the application does not use metadata creation as its production migration
strategy. History queries are scoped by authenticated user ID.

## Authentication and security

Passwords are hashed with Argon2 through `pwdlib`. Login issues a JWT access
token. The frontend stores that token in `localStorage`, which is convenient for
this client but remains exposed to JavaScript running in the origin. Protected
routes use the authenticated-user dependency and ownership-aware history queries.

Uploads are limited to validated PDF/DOCX containers and a configured size.
The in-process fixed-window rate limiter covers registration, login, and resume
operations. It is not shared across multiple backend replicas. CORS, JWT keys,
database URLs, and other deployment settings come from environment variables.

## AI/NLP lifecycle and caching

The Sentence Transformer is loaded lazily once per process. Static role
embeddings are reused and a bounded process-local embedding cache avoids repeated
work. The model can require a first-run download unless local-only mode is
enabled with an already-populated cache. No raw resume text is used as a
persistent cache artifact.

## Docker and CI

Compose runs PostgreSQL, the FastAPI backend, and the Nginx-served Vite build.
The backend image uses a non-root user; the frontend is multi-stage and uses
`nginxinc/nginx-unprivileged`. GitHub Actions runs backend tests and coverage,
frontend lint/tests/build, and Docker image validation. A separate manually
triggered workflow can publish images, but CI does not deploy the application.

## Testing strategy

Backend pytest tests cover API behavior, auth and ownership, migrations,
parsing, scoring, rate limiting, semantic lifecycle, and performance helpers.
Semantic tests are marked separately so normal CI does not download a model.
Frontend Vitest and React Testing Library cover forms, result components,
recommendations, feedback, and branding.

## Scalability and limitations

The service is suitable for local and modest single-process use. The in-process
rate limiter and model/cache state are not distributed. Sentence Transformers
and PyTorch can require substantial memory, and first semantic use can be slow.
SQLite is not an appropriate shared multi-instance production database. OCR for
image-only scanned resumes, generative rewriting, recruiter decisions, and
official employer ATS results are not implemented.
