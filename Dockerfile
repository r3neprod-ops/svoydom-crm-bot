FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    APP_HOST=0.0.0.0 \
    APP_PORT=8000

WORKDIR /app

RUN useradd --create-home --uid 10001 appuser

COPY pyproject.toml README.md ./
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./

RUN pip install --upgrade pip && pip install .

USER appuser

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host \"${APP_HOST:-0.0.0.0}\" --port \"${PORT:-${APP_PORT:-8000}}\""]
