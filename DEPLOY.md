# Deployment (Docker)

## Architecture

```
browser ──> frontend (nginx :8080)
              ├── static React app (SPA fallback)
              ├── /api/v1/*  ──> backend:8000  (passthrough)
              └── /api/*     ──> backend:8000/*  (prefix stripped, like Vite dev proxy)
backend
  ├── MySQL 8.4   (source of truth; schema via Alembic at startup)
  ├── Qdrant 1.12 (vector index; server mode, persisted volume)
  └── storage_data volume (uploaded PDFs)
```

## Run locally

```bash
cp .env.example .env        # then fill in GROQ_API_KEY + JINA_API_KEY + MySQL passwords
docker compose up -d --build
docker compose logs -f backend     # watch migrations + startup
```

- App: http://localhost:8080
- API docs: http://localhost:8000/docs
- Qdrant dashboard: http://localhost:6333/dashboard

The backend container runs `alembic upgrade head` before every start, so the
MySQL schema is always migrated on boot. Uploaded files persist in the
`uploads` volume; MySQL data in `mysql_data`; vectors in `qdrant_data`.

## Environment variables

| Variable | Used by | Purpose |
|---|---|---|
| `MYSQL_ROOT_PASSWORD` / `MYSQL_PASSWORD` / `MYSQL_USER` / `MYSQL_DATABASE` | compose | Provision the MySQL container |
| `DATABASE_URL` | backend | SQLAlchemy URL (injected automatically inside Docker) |
| `GROQ_API_KEY` | backend | LLM answers (RAG) |
| `JINA_API_KEY` / `EMBEDDING_API_KEY` | backend | Embeddings |
| `EMBEDDING_MODEL` / `EMBEDDING_PROVIDER` | backend | Embedding config |
| `QDRANT_URL` / `QDRANT_COLLECTION` | backend | Vector index location (injected inside Docker) |

Secrets live only in `.env` (git-ignored). `.env.example` documents placeholders.

## CI/CD

- **`.github/workflows/ci.yml`** — every push/PR to main:
  1. Backend pytest suite (scratch SQLite, zero external services)
  2. Frontend lint + production build
  3. Both Docker images build successfully
- **`.github/workflows/cd.yml`** — after merge to main: images are pushed to Docker Hub as
  `aniket691/finquery-backend:{sha,latest}` and `aniket691/finquery-frontend:{sha,latest}`.
  Requires repo secrets `DOCKERHUB_USERNAME` + `DOCKERHUB_TOKEN`.

## Deploying to a server (compose host)

```bash
# on the server
git clone https://github.com/aniketdalalml-creator/finquery-rag.git && cd finquery-rag
cp .env.example .env    # fill secrets
docker compose pull     # or: docker compose up -d --build
docker compose up -d
```

To pin a release instead of `latest`, set `image:` tags to the commit SHA
published by CD, or build on the server from the checked-out SHA.
