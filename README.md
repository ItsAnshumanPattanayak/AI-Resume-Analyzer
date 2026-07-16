<div align="center">

# AI Resume Analyzer

### Explainable resume analysis using NLP, semantic similarity, and rule-based ATS scoring

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python\&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi\&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-Frontend-61DAFB?logo=react\&logoColor=black)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-Build%20Tool-646CFF?logo=vite\&logoColor=white)](https://vite.dev/)
[![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?logo=sqlite\&logoColor=white)](https://www.sqlite.org/)
[![License](https://img.shields.io/github/license/ItsAnshumanPattanayak/AI-Resume-Analyzer)](LICENSE)

A full-stack application that analyzes PDF and DOCX resumes, compares them with job descriptions, calculates explainable compatibility scores, recommends suitable technical roles, identifies resume-writing weaknesses, and stores each user's reports privately.

</div>

---

## Overview

AI Resume Analyzer helps candidates inspect how well their resume aligns with a target job description.

The application combines:

* structured resume information extraction;
* rule-based skill detection;
* TF-IDF content similarity;
* Sentence Transformer semantic similarity;
* section-level semantic matching;
* transparent ATS-style scoring;
* predefined technical-role recommendations;
* rule-based resume-quality feedback;
* JWT authentication and private analysis history.

The system is designed to make its results understandable. Scores are broken into individual components instead of being presented as an unexplained prediction.

> This project provides resume-analysis guidance. Its score is an internal compatibility estimate and is not the score produced by any specific employer or commercial Applicant Tracking System.

---

## Current Implementation Status

The following features are implemented in the repository:

| Feature                                  | Status                |
| ---------------------------------------- | --------------------- |
| PDF resume text extraction               | Implemented           |
| DOCX resume text extraction              | Implemented           |
| Candidate-information extraction         | Implemented           |
| Resume-to-job comparison                 | Implemented           |
| Skill-gap analysis                       | Implemented           |
| TF-IDF similarity                        | Implemented           |
| Sentence Transformer semantic similarity | Implemented           |
| Section/chunk-level matching             | Implemented           |
| Explainable ATS-style scoring            | Implemented           |
| Technical role recommendations           | Implemented           |
| Resume-quality suggestions               | Implemented           |
| User registration and login              | Implemented           |
| JWT-protected API access                 | Implemented           |
| Per-user analysis history                | Implemented           |
| History report deletion                  | Implemented           |
| React dashboard                          | Implemented           |
| Backend automated tests                  | Implemented           |
| Frontend component tests                 | Partially implemented |
| Cloud deployment                         | Not included          |
| OCR for scanned/image-only resumes       | Not implemented       |
| Automatic AI rewriting of the resume     | Not implemented       |
| Recruiter or organization dashboard      | Not implemented       |

---

## Features

### 1. Secure User Accounts

Users can:

* register using a name, email address, and password;
* sign in and receive a JWT access token;
* restore an authenticated frontend session;
* access protected resume-analysis endpoints;
* view only their own analysis history;
* delete their own saved reports.

Passwords are hashed before storage, and protected API requests require bearer-token authentication.

### 2. PDF and DOCX Parsing

The backend accepts:

* `.pdf`
* `.docx`

For PDF documents, text is extracted page by page.

For DOCX documents, the parser reads:

* normal paragraphs;
* text inside tables.

The parser also cleans repeated spaces, tabs, line endings, and excessive blank lines while preserving the resume's line structure.

Scanned PDFs that contain only images are not supported because OCR is not currently implemented.

### 3. Structured Resume Extraction

The analyzer extracts structured information from the resume text, including available fields such as:

* email addresses;
* phone numbers;
* professional links;
* detected skills;
* resume sections;
* candidate-related information recognized by the extraction rules.

Extraction is based on deterministic patterns and the project's internal skill taxonomy.

### 4. Complete Resume-to-Job Analysis

The main analysis mode compares an uploaded resume with a supplied job description.

It combines:

* detected resume skills;
* detected job-description skills;
* matched and missing skills;
* TF-IDF similarity;
* semantic similarity;
* chunk-level matching;
* resume structure and content signals;
* ATS-style component scoring.

The job description must contain at least 50 characters.

### 5. Explainable ATS-Style Score

The ATS module uses transparent, rule-based calculations rather than a hidden employer model.

The analysis returns score components and recommendations based on factors such as:

* skill alignment;
* content similarity;
* resume completeness;
* detected sections;
* contact information;
* resume formatting and content signals.

This makes it possible to understand why a score was assigned and which areas affected it.

### 6. Semantic Matching

The semantic-analysis module uses a Sentence Transformer model to compare meaning beyond exact keyword overlap.

The default model is:

```text
sentence-transformers/all-MiniLM-L6-v2
```

Long text is divided into chunks, embedded, normalized, and compared using similarity calculations.

The semantic model is loaded lazily and cached after its first successful use.

### 7. Skill-Gap Analysis

The application compares skills detected in the resume with skills found in the job description.

Results can include:

* matched skills;
* missing skills;
* resume skills;
* job-description skills;
* skill-match information used by the ATS calculation.

The system only suggests adding skills that genuinely reflect the candidate's experience.

### 8. Technical Role Recommendations

The role-recommendation mode compares the resume against predefined technical career profiles.

Recommendations are based on:

* detected candidate skills;
* skill overlap with each role;
* semantic similarity between the resume and role profile;
* combined ranking logic.

The API accepts a configurable `top_n` value and returns the highest-ranked roles.

These recommendations come from the role profiles included in the repository. They are not generated from live job-market data.

### 9. Resume Improvement Analysis

The improvement mode reviews resume content using rule-based writing and structure checks.

The advisor module evaluates signals such as:

* weak or passive phrases;
* action-verb usage;
* measurable achievements;
* bullet quality;
* section completeness;
* content clarity;
* detected skill gaps when a job description is supplied;
* prioritized improvement suggestions.

This feature generates recommendations but does not rewrite or export a new resume document.

### 10. Private Analysis History

Successful analysis results are saved to the database and associated with the authenticated user.

Users can:

* list previous analyses;
* open a complete saved report;
* identify the analysis type and original filename;
* delete an individual report.

Supported saved analysis types include:

* resume parsing;
* complete resume analysis;
* role recommendations;
* resume improvement analysis.

---

## Analysis Modes

The frontend currently exposes four modes:

### Analyze

Upload a resume and provide a job description to receive the complete comparison report.

### Parse

Extract resume text and structured candidate information without comparing it to a job description.

### Roles

Receive ranked technical-role recommendations based on the resume.

### Improve

Review the resume's structure, language, action verbs, achievements, and other quality signals.

---

## Technology Stack

### Backend

* Python
* FastAPI
* Uvicorn
* Pydantic
* SQLAlchemy
* SQLite
* PyJWT
* Argon2 password hashing
* PyMuPDF
* python-docx
* scikit-learn
* Sentence Transformers
* PyTorch
* NumPy
* pytest
* pytest-cov

### Frontend

* React
* Vite
* Axios
* CSS
* Vitest
* React Testing Library

---

## System Architecture

```text
┌───────────────────────────────┐
│        React Frontend         │
│                               │
│ Authentication               │
│ Resume Upload                │
│ Analysis Modes               │
│ Results Dashboard            │
│ Private History              │
└───────────────┬───────────────┘
                │ HTTP / JSON
                │ Bearer JWT
┌───────────────▼───────────────┐
│        FastAPI Backend        │
│                               │
│ File Validation              │
│ PDF / DOCX Parsing           │
│ Information Extraction       │
│ Skill Comparison             │
│ TF-IDF Similarity            │
│ Semantic Similarity          │
│ ATS Scoring                  │
│ Role Recommendations         │
│ Resume Quality Analysis      │
└───────────────┬───────────────┘
                │ SQLAlchemy
┌───────────────▼───────────────┐
│        SQLite Database        │
│                               │
│ Users                        │
│ Private Analysis History     │
└───────────────────────────────┘
```

---

## Project Structure

```text
AI-Resume-Analyzer/
├── backend/
│   ├── app/
│   │   ├── advisor.py          # Resume-quality and improvement analysis
│   │   ├── ats.py              # Explainable ATS-style scoring
│   │   ├── auth.py             # Password verification and JWT authentication
│   │   ├── config.py           # Environment-based configuration
│   │   ├── database.py         # SQLAlchemy engine and sessions
│   │   ├── error_handlers.py   # Application exception handlers
│   │   ├── extractor.py        # Structured resume information extraction
│   │   ├── history.py          # Analysis-history database operations
│   │   ├── logging_config.py   # Logging configuration
│   │   ├── main.py             # FastAPI application and API endpoints
│   │   ├── models.py           # Database models
│   │   ├── parser.py           # PDF and DOCX text extraction
│   │   ├── recommender.py      # Technical-role recommendations
│   │   ├── schemas.py          # Pydantic request and response schemas
│   │   ├── semantic.py         # Sentence Transformer matching
│   │   ├── similarity.py       # TF-IDF and combined similarity
│   │   ├── skills.py           # Skill extraction and comparison
│   │   ├── users.py            # User database operations
│   │   └── utils.py            # Shared utility functions
│   ├── data/                   # Project datasets and role/skill definitions
│   ├── tests/                  # Backend pytest suite
│   ├── .env.example
│   ├── pytest.ini
│   └── requirements.txt
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/         # Forms, scores, skills, history and result panels
│   │   ├── context/            # Authentication context
│   │   ├── pages/              # Dashboard
│   │   ├── services/           # Backend API client
│   │   ├── test/               # Frontend test configuration
│   │   ├── App.jsx
│   │   ├── index.css
│   │   └── main.jsx
│   ├── .env.example
│   ├── package.json
│   └── vite.config.js
├── LICENSE
└── README.md
```

---

## Getting Started

### Prerequisites

Install:

* Git
* Python
* Node.js and npm

Python 3.11 or a compatible version is recommended. The project has also been developed and tested in a newer Python environment, but dependency compatibility may vary between Python releases.

### 1. Clone the Repository

```bash
git clone https://github.com/ItsAnshumanPattanayak/AI-Resume-Analyzer.git
cd AI-Resume-Analyzer
```

---

## Backend Setup

### 1. Open the Backend Directory

```bash
cd backend
```

### 2. Create a Virtual Environment

Windows PowerShell:

```powershell
python -m venv resume
.\resume\Scripts\Activate.ps1
```

Windows Command Prompt:

```bat
python -m venv resume
resume\Scripts\activate
```

Linux or macOS:

```bash
python3 -m venv resume
source resume/bin/activate
```

### 3. Install Dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Create the Environment File

Windows:

```powershell
Copy-Item .env.example .env
```

Linux or macOS:

```bash
cp .env.example .env
```

Edit `.env` before starting the backend.

A local configuration can look like this:

```env
APP_NAME=AI Resume Analyzer API
APP_VERSION=1.5.0
APP_ENVIRONMENT=development
DEBUG=false

DATABASE_URL=sqlite:///./resume_analyzer.db

JWT_SECRET_KEY=replace-this-with-a-new-long-random-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]
ALLOW_LOCALHOST_ORIGIN_REGEX=true

MAXIMUM_FILE_SIZE_MB=5

SEMANTIC_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
SEMANTIC_MODEL_LOCAL_ONLY=false

LOG_LEVEL=INFO
```

Generate a new JWT secret instead of reusing the example value:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Do not commit your real `.env` file.

### 5. Start the Backend

```bash
uvicorn app.main:app --reload
```

The backend will normally be available at:

```text
http://127.0.0.1:8000
```

Interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
http://127.0.0.1:8000/health
```

---

## Semantic Model Setup

Semantic analysis uses the configured Sentence Transformer model.

### Online Loading

For the simplest first run, use:

```env
SEMANTIC_MODEL_LOCAL_ONLY=false
```

The model can then be downloaded when semantic analysis is first used.

### Offline Loading

After the model is cached locally, use:

```env
SEMANTIC_MODEL_LOCAL_ONLY=true
```

Optional offline environment variables:

Windows PowerShell:

```powershell
$env:HF_HUB_OFFLINE="1"
$env:TRANSFORMERS_OFFLINE="1"
```

Linux or macOS:

```bash
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
```

Semantic operations will fail with a clear error if local-only mode is enabled before the model has been downloaded.

---

## Frontend Setup

Open a second terminal from the repository root.

### 1. Open the Frontend Directory

```bash
cd frontend
```

### 2. Install Dependencies

```bash
npm install
```

### 3. Create the Environment File

Windows:

```powershell
Copy-Item .env.example .env
```

Linux or macOS:

```bash
cp .env.example .env
```

Default frontend configuration:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

### 4. Start the Development Server

```bash
npm run dev
```

Open the address printed by Vite, normally:

```text
http://localhost:5173
```

---

## Running the Tests

### Backend Tests

From the `backend` directory:

```bash
python -m pytest
```

Run tests with coverage:

```bash
python -m pytest --cov=app --cov-report=term-missing
```

Run tests that do not require the real semantic model:

```bash
python -m pytest -m "not semantic"
```

Run only semantic tests:

```bash
python -m pytest -m semantic
```

Semantic tests may require the configured Sentence Transformer model to be available locally or downloadable from the internet.

### Frontend Tests

From the `frontend` directory:

```bash
npm run test
```

Run the frontend suite once:

```bash
npm run test:run
```

Run ESLint:

```bash
npm run lint
```

Create a production frontend build:

```bash
npm run build
```

---

## API Endpoints

All resume and history endpoints require authentication.

### General

| Method | Endpoint  | Purpose                  |
| ------ | --------- | ------------------------ |
| `GET`  | `/`       | API information          |
| `GET`  | `/health` | Backend health status    |
| `GET`  | `/docs`   | Swagger UI documentation |

### Authentication

| Method | Endpoint             | Purpose                         |
| ------ | -------------------- | ------------------------------- |
| `POST` | `/api/auth/register` | Create a user account           |
| `POST` | `/api/auth/login`    | Authenticate and obtain a JWT   |
| `GET`  | `/api/auth/me`       | Retrieve the authenticated user |

### Resume Analysis

| Method | Endpoint                      | Purpose                                 |
| ------ | ----------------------------- | --------------------------------------- |
| `POST` | `/api/resume/parse`           | Parse an uploaded resume                |
| `POST` | `/api/resume/analyze`         | Compare a resume with a job description |
| `POST` | `/api/resume/recommend-roles` | Recommend technical roles               |
| `POST` | `/api/resume/improve`         | Generate resume-quality feedback        |

### History

| Method   | Endpoint                   | Purpose                          |
| -------- | -------------------------- | -------------------------------- |
| `GET`    | `/api/history`             | List the current user's analyses |
| `GET`    | `/api/history/{record_id}` | Retrieve one saved analysis      |
| `DELETE` | `/api/history/{record_id}` | Delete one saved analysis        |

---

## Example API Workflow

### 1. Register

```bash
curl -X POST "http://127.0.0.1:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Example User",
    "email": "user@example.com",
    "password": "replace-with-a-valid-password"
  }'
```

### 2. Log In

```bash
curl -X POST "http://127.0.0.1:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "replace-with-a-valid-password"
  }'
```

Copy the returned access token.

### 3. Analyze a Resume

```bash
curl -X POST "http://127.0.0.1:8000/api/resume/analyze" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@resume.pdf" \
  -F "job_description=We are looking for a Python developer with FastAPI, SQL, machine learning, Git and API development experience."
```

### 4. View History

```bash
curl "http://127.0.0.1:8000/api/history" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## File Validation

Uploaded resumes are checked for:

* a valid filename;
* a supported extension;
* non-empty file content;
* configured maximum file size;
* extractable text.

The default maximum upload size is:

```text
5 MB
```

Unsupported formats return an appropriate API error.

---

## Security Notes

Before using the application outside local development:

1. Replace the example JWT secret.
2. Use a production database configuration.
3. Restrict CORS to trusted frontend domains.
4. Disable debug mode.
5. Serve both frontend and backend over HTTPS.
6. Avoid logging resume content or personal information.
7. Review data-retention requirements for uploaded resume information.
8. Add rate limiting and production monitoring.
9. Store secrets in the deployment platform's secret manager.
10. Review authentication and dependency security before public deployment.

The repository contains development-oriented defaults and is not presented as a production-hardened deployment.

---

## Known Limitations

* Only PDF and DOCX files are accepted.
* Image-only and scanned resumes are not processed because OCR is absent.
* Results depend on successful text extraction from the uploaded document.
* Skill extraction is limited to the project's configured skill vocabulary and matching rules.
* Role recommendations are limited to predefined repository data.
* ATS scoring is an internal explainable approximation, not a commercial ATS result.
* Semantic analysis requires the configured Sentence Transformer model.
* The initial semantic-model download can require an internet connection.
* Resume improvement feedback is rule-based and does not rewrite the resume automatically.
* The project does not fetch current job openings or real-time labour-market information.
* No hosted frontend or backend deployment is included in the repository.
* No CI/CD workflow is currently included.
* Frontend automated test coverage is smaller than the backend test suite.

---

## Responsible Use

Resume analysis should assist human judgment rather than replace it.

Do not use the output to:

* misrepresent experience;
* add skills the candidate does not possess;
* fabricate achievements;
* automatically reject candidates;
* make employment decisions without human review.

Users should verify every recommendation before changing their resume.

---

## Development Roadmap

The following are possible future improvements and are **not currently claimed as completed**:

* OCR for scanned resumes;
* broader frontend test coverage;
* Docker and Docker Compose support;
* continuous integration;
* deployment documentation;
* PostgreSQL production configuration;
* password reset and email verification;
* refresh-token support;
* configurable skill and role administration;
* exportable PDF analysis reports;
* optional AI-assisted rewriting with user review;
* accessibility and mobile-interface improvements;
* expanded observability and rate limiting.

---

## Contributing

Contributions are welcome.

1. Fork the repository.
2. Create a branch:

```bash
git checkout -b feature/your-feature-name
```

3. Make and test your changes.
4. Commit using a clear message:

```bash
git commit -m "Add: description of the change"
```

5. Push the branch:

```bash
git push origin feature/your-feature-name
```

6. Open a pull request describing:

   * the problem addressed;
   * the implementation;
   * tests performed;
   * any configuration changes.

Please avoid documenting planned functionality as though it is already implemented.

---

## License

This project is distributed under the license included in the [`LICENSE`](LICENSE) file.

---

## Author

**Anshuman Pattanayak**

GitHub: [@ItsAnshumanPattanayak](https://github.com/ItsAnshumanPattanayak)

Repository: [AI-Resume-Analyzer](https://github.com/ItsAnshumanPattanayak/AI-Resume-Analyzer)

---

<div align="center">

Built as a practical full-stack NLP and machine-learning project for transparent resume analysis.

⭐ Consider starring the repository if you find it useful.

</div>
