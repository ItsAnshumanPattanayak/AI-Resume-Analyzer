FROM python:3.12-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV TOKENIZERS_PARALLELISM=false

WORKDIR /app

COPY requirements-runtime.txt .

RUN python -m pip install --upgrade pip \
    && python -m pip install \
        --index-url https://download.pytorch.org/whl/cpu \
        torch==2.13.0 \
    && python -m pip install \
        -r requirements-runtime.txt

COPY alembic.ini .
COPY migrations ./migrations
COPY app ./app
COPY data ./data

RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --create-home app \
    && mkdir -p /app/model_cache \
    && chown -R app:app /app

USER app

EXPOSE 8000

CMD ["sh", "-c", "exec python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
