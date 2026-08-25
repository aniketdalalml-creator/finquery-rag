FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependencies first so source changes don't bust the layer cache.
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Run as non-root; storage_data must be writable by the app.
RUN useradd --create-home appuser \
    && mkdir -p /app/storage_data /app/vectorstore \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Migrations run before every start (idempotent); shell form keeps it simple.
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000"]
