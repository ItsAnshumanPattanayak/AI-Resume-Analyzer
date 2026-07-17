# Portfolio material

## Project title

**AI Resume Analyzer — Full-Stack AI/NLP Application**

## Two-line resume description

Built a React/Vite and FastAPI platform that parses PDF/DOCX resumes, compares
them with job descriptions, and produces ATS-style, semantic, role, and writing
feedback with explainable results.

## Resume bullets

- Built a full-stack React and FastAPI application for authenticated resume
  parsing, structured extraction, and analysis history.
- Implemented PDF/DOCX validation, candidate information extraction, skill-gap
  comparison, and transparent ATS-style scoring.
- Integrated Sentence Transformer semantic matching and repository-defined role
  profiles with deterministic, explainable recommendations.
- Added rule-based resume feedback for sections, bullets, action verbs,
  quantification opportunities, repetition, readability, and privacy-safe evidence.
- Used SQLAlchemy/Alembic with SQLite and PostgreSQL support, Docker Compose,
  GitHub Actions CI, pytest, Vitest, and React Testing Library.
- Optimized lazy model lifecycle, static role embeddings, bounded embedding
  caching, blocking-work isolation, rate limiting, upload validation, and health
  checks.

## LinkedIn description

AI Resume Analyzer is a full-stack AI/NLP project that helps job seekers inspect
resume structure, compare skills and content with a job description, explore
technical role recommendations, and receive actionable writing feedback. It
combines deterministic extraction and ATS-style signals with Sentence Transformer
semantic matching, explainable score components, JWT authentication, private
history, PostgreSQL/SQLite persistence, Docker Compose, and automated testing.
The results are advisory and intentionally do not claim hiring probability.

## GitHub About recommendation

**An explainable React + FastAPI resume analyzer with PDF/DOCX parsing, ATS-style scoring, semantic matching, role recommendations, and private history.**

Suggested topics: `resume-analyzer`, `fastapi`, `react`, `python`, `nlp`,
`machine-learning`, `sentence-transformers`, `postgresql`, `docker`, `ats`,
`job-matching`, `resume-parser`.

Suggested social preview: a clean crop of the authenticated dashboard or
architecture diagram, using fictional data and no credentials. Configure About
text, topics, and social preview manually in GitHub; this repository does not
modify GitHub settings.

## Interview introductions

### 30 seconds

“AI Resume Analyzer is a React and FastAPI application that parses PDF and DOCX
resumes, compares them with job descriptions, and explains ATS-style scores,
semantic similarity, missing skills, role recommendations, and writing feedback.
It uses JWT authentication, private history, SQLAlchemy persistence, and a
Sentence Transformer that loads lazily.”

### 90 seconds

“The frontend offers Analyze, Parse, Roles, and Improve modes. An authenticated
upload is validated and extracted into structured candidate data. Analyze mode
combines skill comparison, TF-IDF, Sentence Transformer similarity, ATS-style
components, role recommendations, and rule-based improvement feedback. Roles
use repository-maintained profiles and expose exact-skill and semantic scores.
Reports are stored per user through SQLAlchemy and Alembic, with SQLite for
local/CI use and PostgreSQL in Compose. Docker and GitHub Actions provide
repeatable runtime and validation.”

### Architecture explanation

The React/Vite client sends bearer-token requests to FastAPI. `main.py`
coordinates validation and threadpool execution of parser, extractor, skills,
similarity, ATS, semantic, recommender, and advisor modules. Pydantic schemas
serialize responses; SQLAlchemy sessions persist users and history. The semantic
model is lazy and process-local, while role embeddings and bounded text cache
reduce repeated work. Nginx serves the frontend image and proxies `/api` in
Compose.

## Interview questions and answers

**Why combine traditional and semantic matching?** Exact skill matching makes
technical coverage auditable, while TF-IDF and semantic similarity capture
related wording. Neither is presented as an employer decision.

**How is the ATS-style score calculated?** `ats.py` combines bounded, documented
signals such as skills, similarity, contact information, sections, and resume
content. The API exposes component recommendations rather than a hidden score.

**Why Sentence Transformers?** The configured model compares meaning beyond exact
keywords and is reused after lazy initialization. Model availability remains an
operational dependency.

**How are long resumes processed?** Semantic text is cleaned, split into bounded
chunks, embedded, and compared; parsing and other blocking operations run via a
threadpool from the async endpoints.

**How are recommendations explained?** Each role exposes exact skill coverage,
semantic similarity, matched/missing skills, strengths, improvement areas, and
the weighted values used for ranking.

**How is user data isolated?** JWT authentication identifies the user and every
history read/delete query includes that user ID.

**How is model loading optimized?** Loading is lazy and thread-safe, static role
embeddings are reused, and a bounded process-local embedding cache avoids raw
resume persistence.

**Why Alembic?** Schema changes are explicit, reviewable, and repeatable across
SQLite and PostgreSQL rather than being silently created at runtime.

**How does Compose organize the app?** PostgreSQL, the FastAPI backend, and the
Nginx frontend are separate services with health/dependency ordering.

**What would you improve next?** A distributed limiter and shared model/cache
strategy would be needed for horizontal scale; OCR, stronger privacy controls,
and measured production observability are also possible future work.

## Challenges and solutions

- Mixed PDF/DOCX formats: validated signatures and used format-specific parsers.
- Explainability: kept skill, semantic, ATS, and role components explicit.
- Model cost: lazy loading, reuse, bounded cache, and isolated blocking work.
- Privacy: user-scoped history, safe logging, redacted feedback evidence, and
  environment-based secrets.
- Test reliability: separated semantic tests and used deterministic doubles for
  normal unit tests.

## Future scope

Potential enhancements include OCR for image-only resumes, distributed rate
limiting, persistent model infrastructure, richer role-profile maintenance,
stronger PII handling, and measured deployment observability. None is claimed as
implemented here.
