# API overview

The FastAPI service is available locally at `http://127.0.0.1:8000`. Interactive
Swagger documentation is available at `http://127.0.0.1:8000/docs` while the
backend is running.

All resume and history operations require a bearer JWT unless noted otherwise.
File endpoints use `multipart/form-data`; authentication requests use JSON.

## Service and authentication

| Method | Route | Auth | Purpose |
| --- | --- | --- | --- |
| GET | `/` | No | Service metadata and documentation link. |
| GET | `/health` | No | Readiness check including a lightweight `SELECT 1`. Returns 503 if the database is unavailable. |
| POST | `/api/auth/register` | No | Validates name/email/password and creates a user. |
| POST | `/api/auth/login` | No | Verifies credentials and returns a bearer JWT plus user profile. |
| GET | `/api/auth/me` | Yes | Returns the current authenticated user. |

Registration and login are rate limited. Invalid credentials return a generic
authentication error rather than account details.

## Resume operations

| Method | Route | Auth | Request and response |
| --- | --- | --- | --- |
| POST | `/api/resume/parse` | Yes | Upload a validated PDF/DOCX `file`; returns extracted text, structured candidate data, and a history ID. |
| POST | `/api/resume/analyze` | Yes | Upload `file` plus a job-description form field of at least 50 characters; returns similarity, skill, ATS, role, and improvement results. |
| POST | `/api/resume/recommend-roles` | Yes | Upload `file` and optional `top_n` from 1 to 10; returns ranked, explainable repository-defined roles. |
| POST | `/api/resume/improve` | Yes | Upload `file`; returns deterministic section, bullet, readability, contact, skills, and priority feedback. |

Resume endpoints validate extensions, signatures/containers, empty content, and
the configured maximum file size. Semantic portions may fail safely when the
configured model is unavailable; non-semantic feedback remains rule based.

## History

| Method | Route | Auth | Purpose |
| --- | --- | --- | --- |
| GET | `/api/history` | Yes | Lists the authenticated user's reports. Supports `limit` 1–100 and non-negative `offset`. |
| GET | `/api/history/{record_id}` | Yes | Returns one report only when it belongs to the authenticated user. |
| DELETE | `/api/history/{record_id}` | Yes | Deletes one report only when it belongs to the authenticated user. |

History records are associated with the authenticated user at creation time.
Missing or foreign records return not-found behavior rather than exposing
another user's data.

## Common failures

- `400`: invalid form values, short job description, invalid `top_n`, malformed
  or empty upload, or invalid history pagination.
- `401`: missing/invalid/expired JWT or incorrect credentials.
- `404`: history record is unavailable to the authenticated user.
- `409`: registration conflicts with an existing account.
- `413`: upload exceeds the configured size limit.
- `415`: unsupported or misleading file type.
- `429`: an in-process rate limit was exceeded.
- `503`: database readiness check failed, or a semantic operation is unavailable.

Exact generated schemas and validation details are available in Swagger.
