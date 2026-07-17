# AGENTS.md

## Scope

These instructions apply to the entire repository.

Work only on the currently assigned phase or task. Do not make unrelated changes.

## Project Architecture

- The backend is a FastAPI application in `backend/`.
- The frontend is a React application built with Vite in `frontend/`.
- The application supports SQLite for local development and PostgreSQL for deployed or containerized environments.
- SQLAlchemy provides database access.
- Alembic manages database migrations.
- JWT authentication protects the resume-analysis and analysis-history endpoints.
- Every analysis-history record belongs to an authenticated user. Preserve the ownership checks that prevent users from reading or deleting another user's records.
- Docker Compose runs the frontend, backend, and PostgreSQL services.
- Backend tests use pytest.
- Frontend tests use Vitest and React Testing Library.

## Repository Rules

1. Never modify the `main` branch directly unless the user explicitly approves it.
2. Make changes only for the currently assigned phase.
3. Do not perform unrelated refactoring.
4. Do not remove, disable, or bypass authentication.
5. Do not weaken analysis-history ownership checks.
6. Do not delete failing tests merely to make CI pass.
7. Do not replace meaningful assertions with weak assertions.
8. Do not commit real `.env` files, secrets, JWT keys, database passwords, tokens, generated databases, virtual environments, `node_modules`, build outputs, or model caches.
9. Use environment variables for deployment-specific settings.
10. Preserve existing API contracts unless a change is necessary and clearly explained.
11. Report every command executed and its result honestly.
12. Never claim that tests passed unless they were actually executed.
13. State clearly when something could not be verified.
14. Before committing, show `git diff` and `git status`.
15. Do not push or create a pull request unless the user explicitly asks.

## Verification Commands

Run only the checks relevant to the current change. Report the exact command, whether it completed, and its result.

### Backend

Run from `backend/`:

```bash
python -m pytest -m "not semantic"
python -m pytest --cov=app --cov-report=term-missing
```

Run semantic tests only when the configured Sentence Transformer model is available:

```bash
python -m pytest -m semantic
```

If the model is unavailable, do not claim that semantic tests passed. Report that they were not verified and explain why.

### Frontend

Run from `frontend/`:

```bash
npm ci
npm run lint
npm run test:run
npm run build
```

Do not run `npm ci` when dependency installation has not been authorized.

### Docker

Run from the repository root:

```bash
docker compose --env-file .env.docker -f compose.yaml config
docker compose --env-file .env.docker -f compose.yaml build
docker compose --env-file .env.docker -f compose.yaml up -d
docker compose --env-file .env.docker -f compose.yaml ps
```

Treat `.env.docker` as a local secret-bearing file. Never commit it or expose its values in logs or reports.

## Change Discipline

- Inspect existing code, tests, configuration, and conventions before editing.
- Keep changes minimal and targeted.
- Add or update meaningful tests when behavior changes.
- Preserve authentication and per-user data isolation.
- Use Alembic migrations for schema changes; do not silently create or alter production schemas through application startup code.
- Do not regenerate lockfiles, build outputs, databases, or caches unless the task requires it and the user has authorized it.
- Before a commit, show the user the complete `git diff` and `git status` and wait for approval when required.

## Completion Report

At the end of every implementation task, report:

- every file changed;
- the reason for each change;
- every command executed;
- the exact test results, including passed, failed, skipped, or deselected counts when available;
- unresolved problems;
- anything that was not verified.

Do not describe work as complete when required checks failed or could not be performed. Clearly distinguish implemented behavior from verified behavior.
