# Railway Deployment Preparation

This guide prepares the AI Resume Analyzer for Railway. It does not indicate
that any Railway project, service, database, domain, or deployment exists.

## Architecture

The intended production relationship is:

```text
Browser
  -> public frontend service
  -> public backend API
  -> private Railway PostgreSQL service
```

The browser calls the backend through its public HTTPS domain. Browsers cannot
resolve Railway private-network hostnames. PostgreSQL must remain private and
must never be exposed to the frontend.

The frontend Nginx `/api` proxy remains useful for local Docker Compose, where
the backend hostname is `backend`. Railway production builds instead embed the
backend public URL through `VITE_API_BASE_URL`.

## Prerequisites

- A Railway account with GitHub access configured manually.
- This repository available on GitHub.
- Permission to create Railway services and a managed PostgreSQL database.
- A locally generated, unique JWT secret.
- A reviewed database backup and rollback policy.

Do not place credentials in Git, Docker build arguments, deployment logs, or
the production frontend bundle.

## 1. Create the project and PostgreSQL database

1. Create an empty Railway project in the dashboard.
2. Add a Railway-managed PostgreSQL database to the same project and
   environment as the application services.
3. Do not add a public TCP proxy unless external database administration is a
   deliberate requirement. The backend should use private networking.
4. Review the database service's backup and restore facilities before storing
   production data. A code rollback does not roll back database migrations.

Railway provides the database connection variables. Configure the backend's
`DATABASE_URL` as a Railway reference to the PostgreSQL service's private
`DATABASE_URL`, not `DATABASE_PUBLIC_URL`. The application accepts
`postgres://` and `postgresql://` URLs and normalizes them for Psycopg 3.

## 2. Add the backend service

1. Add an empty service named `Backend`.
2. Connect this GitHub repository.
3. Select the intended deployment branch. Use a preparation branch for the
   first manual test; use `main` only after review and merge.
4. Set **Root Directory** to `/backend`.
5. Confirm Railway detects `/backend/Dockerfile`.
6. Keep automatic production deployment disabled during the first setup.

The image starts:

```text
python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

The Docker command defaults to port 8000 only when `PORT` is absent, preserving
local container use. It does not use `--reload`.

### Backend variables

Use `backend/.env.production.example` as a checklist, not as an environment
file to upload. At minimum configure:

```text
APP_ENVIRONMENT=production
DEBUG=false
DATABASE_URL=<reference to the PostgreSQL service's private DATABASE_URL>
JWT_SECRET_KEY=<new generated secret>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
CORS_ORIGINS=https://<final-frontend-domain>
ALLOW_LOCALHOST_ORIGIN_REGEX=false
SEMANTIC_MODEL_LOCAL_ONLY=false
LOG_LEVEL=INFO
```

Generate `JWT_SECRET_KEY` locally:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Store the result only in Railway's backend variables.

### Migrations

The backend's `backend/railway.toml` configures this pre-deploy command:

```text
python -m alembic upgrade head
```

The backend Root Directory makes `/app` the correct image working directory;
`alembic.ini` and `migrations/` are copied there. Railway runs the command in a
separate pre-deploy container with backend variables and private networking.
If migration exits nonzero, deployment must stop before the new application
receives traffic.

Migrations are intentionally absent from the production runtime command to
avoid duplicate execution and migration races during application starts or
horizontal scaling. Local Docker Compose explicitly performs the migration
before starting Uvicorn.

Alembic downgrades are not an automatic rollback strategy. Before applying a
destructive migration, make and verify a database backup and document a
forward-fix or tested downgrade procedure. Rolling application code back may
not be safe after an incompatible schema change.

### Backend health check and domain

The Railway config uses:

```text
Health check path: /health
Timeout: 300 seconds
```

`/health` performs a lightweight database query. It returns HTTP 200 only when
the API and database are reachable, and HTTP 503 without internal exception
details when the database check fails.

After the first backend deployment starts successfully, generate a Railway
public domain and record its HTTPS URL. Confirm that the domain targets the
port detected from Railway's `PORT` variable.

## 3. Add the frontend service

1. Add an empty service named `Frontend`.
2. Connect the same GitHub repository and branch.
3. Set **Root Directory** to `/frontend`.
4. Confirm Railway detects `/frontend/Dockerfile`.
5. Set the service variable `PORT=8080`, or explicitly select container port
   8080 as the generated domain's target port.
6. Set the build variable:

```text
VITE_API_BASE_URL=https://<backend-public-domain>
```

`VITE_API_BASE_URL` is a Vite build-time value. Changing it requires a new
frontend build and redeployment; setting it only in a running container cannot
change the compiled JavaScript.

The multi-stage Dockerfile builds the React application and serves it with
unprivileged Nginx. Nginx listens on 8080 and retains SPA fallback routing. The
Railway frontend health-check path is `/`.

Generate a public frontend domain after the service becomes healthy. Railway
provides HTTPS for its generated domain. For a custom domain, add and verify
the DNS records shown in the Railway dashboard before changing CORS.

## 4. Finalize production CORS

Railway cannot provide the final frontend origin until a domain exists. Use
this two-step setup:

1. Complete the initial frontend deployment and generate its public domain.
2. Set the backend variable to the exact origin, with no path or trailing
   slash:

   ```text
   CORS_ORIGINS=https://<frontend-public-domain>
   ALLOW_LOCALHOST_ORIGIN_REGEX=false
   ```

3. Redeploy the backend so it reads the final origin.
4. Redeploy the frontend if its backend URL changed.
5. Verify that an unapproved origin receives no CORS permission.

Never use `*` for production origins and do not commit a guessed domain.

## 5. Semantic model and resources

The Sentence Transformer model is loaded lazily on the first semantic request,
then cached in memory for that backend process. With
`SEMANTIC_MODEL_LOCAL_ONLY=false`, the first request can download the model and
may be noticeably slower.

The model, PyTorch, NumPy, and embeddings can require significant memory. Do
not assume a free or low-resource plan is sufficient without measuring image
size, idle memory, peak request memory, startup time, and first-request time.

Railway service filesystems are ephemeral. A restart or redeployment may lose
the downloaded cache. A Railway volume mounted at `/app/model_cache` can make
the on-disk Hugging Face cache persistent, but volume lifecycle, backups, and
deployment behavior must be reviewed before relying on it. Never commit the
model cache or bake a large model into Git.

The backend currently uses one Uvicorn worker. Increasing workers multiplies
model memory and creates a separate in-process rate limiter and model cache per
worker. Multiple replicas also have independent rate-limit counters. SQLite is
not appropriate for multi-instance production; use managed PostgreSQL.

The frontend API client timeout is 120 seconds while Nginx's local proxy
timeouts are 300 seconds. Long model downloads or constrained compute can
still exceed the browser timeout. Measure before changing these values.

## 6. First deployment and smoke tests

Keep the first deployment manual. Review build, pre-deploy, deploy, and health
logs without printing environment values. Then run the optional smoke test
from a trusted workstation:

```bash
export FRONTEND_URL="https://<frontend-public-domain>"
export BACKEND_URL="https://<backend-public-domain>"
python scripts/railway_smoke_test.py --confirm-target
```

The script generates test credentials and a small DOCX, then checks frontend
loading, backend readiness, registration, login, current user, unauthenticated
rejection, parsing, history retrieval, and deletion of the history record it
created. It does not delete the generated user because no account-deletion API
exists. Run it only against an environment where creation of that test account
is acceptable.

Also inspect backend logs for migration, database, model, timeout, and memory
errors. Do not log JWTs, database URLs, credentials, or resume content.

## 7. Rollback and backups

For an application-only problem, use Railway's deployment history to redeploy
the last known-good image after confirming its schema compatibility. If a
migration changed the schema, stop and assess compatibility before rolling the
application back.

Database recovery is separate from application rollback. Review Railway's
current PostgreSQL backup and restore behavior, retention, and plan limits in
the dashboard and current documentation. Test restores before depending on
them. Export sensitive data only to approved encrypted storage.

## 8. CI/CD relationship

GitHub Actions remains validation-only for pull requests and normal CI. This
phase does not add Railway tokens, deployment jobs, automatic image publishing,
or pull-request deployments.

After a successful manual deployment and smoke test, Railway GitHub auto-deploy
may be enabled manually for the `main` branch. Pull requests should continue to
run CI without deploying production. Configure service watch paths if desired
so backend-only changes do not rebuild the frontend and vice versa.

## Manual steps that remain

- Connect Railway to GitHub.
- Create the project, managed PostgreSQL database, and two application services.
- Configure service roots, branches, variables, references, and build values.
- Generate and store a production JWT secret.
- Perform the first manual deployments.
- Generate public domains and finish the two-step CORS configuration.
- Decide whether to attach a persistent model-cache volume.
- Measure resource usage and request latency.
- Run smoke tests and inspect logs.
- Configure backups, custom domains, DNS, monitoring, alerts, and rollback policy.
- Enable `main` auto-deploy only after the manual deployment is proven.
