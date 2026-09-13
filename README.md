# FinanceIQ (FinQuery)

**Institutional financial document intelligence** — upload SEC-style filings, ask natural-language questions, and get **grounded answers with page-level citations**.

Each user has an isolated library (companies + documents). Auth is JWT-based; the research UI is a React workspace with dashboard, documents, companies, Q&A, and settings.

---

## Live demo

| | |
|---|---|
| **App** | [http://206.189.235.250:8080](http://206.189.235.250:8080) |
| **API docs** | [http://206.189.235.250:8000/docs](http://206.189.235.250:8000/docs) |

> Register an account on the live app (multi-tenant — you only see your own data).  
> Droplet deploy uses Docker Compose under `/opt/finquery` with a dedicated `deploy` user.

---

## Features

- **Auth** — email/password register & login (JWT Bearer)
- **Per-user isolation** — companies and documents scoped by `user_id`
- **Company directory** — create, search, and edit issuers
- **Document pipeline** — upload PDFs → process → embed → index
- **Grounded RAG Q&A** — retrieve chunks, generate answers, return source citations (document + pages + score)
- **Dashboard** — live stats, quick ask, recent filings
- **Settings** — account + API health (keys never exposed)
- **Production deploy** — Docker Compose (MySQL + Qdrant + backend + nginx frontend), Alembic migrations on boot, CI/CD to Docker Hub

---

## Architecture

```
Browser
  └── Frontend (React + Vite → nginx :8080)
        ├── /api/v1/*  →  FastAPI backend :8000
        └── SPA routes

Backend
  ├── MySQL 8.4          source of truth (users, companies, documents, metrics)
  ├── Qdrant             vector index for chunk embeddings
  ├── Embeddings         Jina (configurable)
  ├── LLM                Groq (grounded generation)
  └── Local volume       uploaded PDFs
```

```
rag_finquery/
├── frontend/                 # React 19 + Tailwind 4 + Vite
├── backend/                  # FastAPI + SQLAlchemy + Alembic + RAG services
├── docker-compose.yml        # mysql · qdrant · backend · frontend
├── .env.example              # secrets template
├── DEPLOY.md                 # deploy deep-dive
└── .github/workflows/        # CI + Docker Hub CD
```

---

## Tech stack

| Layer | Stack |
|---|---|
| Frontend | React 19, TypeScript, Vite, Tailwind CSS 4, Lucide |
| Backend | FastAPI, Pydantic, SQLAlchemy 2, Alembic, PyJWT, bcrypt |
| Data | MySQL 8.4 (prod) / SQLite (tests & local fallback) |
| Vectors | Qdrant |
| AI | Jina embeddings, Groq LLM (LangChain) |
| Ops | Docker Compose, GitHub Actions, nginx |

---

## Quick start

### Option A — Docker (recommended)

Requires [Docker Desktop](https://www.docker.com/products/docker-desktop/).

```bash
cp .env.example .env
# Fill: MYSQL_*, AUTH_SECRET_KEY, GROQ_API_KEY, JINA_API_KEY

docker compose up -d --build
docker compose logs -f backend   # migrations + health
```

| Service | URL |
|---|---|
| App | http://localhost:8080 |
| API / OpenAPI | http://localhost:8000/docs |
| Qdrant (dev) | http://localhost:6333/dashboard |

Schema migrates automatically (`alembic upgrade head` on backend start).

### Option B — Local dev (Vite + uvicorn)

```bash
# 1) Backend (from repo root)
.\.venv\Scripts\Activate.ps1          # Windows
# source .venv/bin/activate            # macOS/Linux

cd backend
python migrate.py up
$env:PYTHONPATH = "."                 # PowerShell
uvicorn app.main:app --reload --port 8000

# 2) Frontend (new terminal)
cd frontend
npm install
npm run dev
```

- UI: http://localhost:5173 (proxies `/api` → `:8000`)
- Ensure root `.env` has `AUTH_SECRET_KEY` (and API keys for real RAG)

---

## Environment

Copy `.env.example` → `.env` (git-ignored). Important variables:

| Variable | Purpose |
|---|---|
| `AUTH_SECRET_KEY` | JWT signing secret (**required**) |
| `MYSQL_*` / `DATABASE_URL` | DB (Compose injects `DATABASE_URL` for containers) |
| `GROQ_API_KEY` | LLM answers |
| `JINA_API_KEY` / `EMBEDDING_API_KEY` | Embeddings |
| `QDRANT_URL` | Vector DB (injected in Compose) |
| `BACKEND_CORS_ORIGINS` | Allowed frontend origins |

See [DEPLOY.md](./DEPLOY.md) for the full matrix.

---

## API (v1)

Authenticated routes expect:

```http
Authorization: Bearer <access_token>
```

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/v1/auth/register` | Create account |
| `POST` | `/api/v1/auth/login` | Get JWT + user |
| `GET` | `/api/v1/companies` | List companies (scoped) |
| `POST` | `/api/v1/companies` | Create company |
| `GET` | `/api/v1/documents` | List documents (scoped) |
| `POST` | `/api/v1/documents/upload` | Upload PDF |
| `POST` | `/api/v1/documents/{id}/process` | Run ingestion |
| `POST` | `/api/v1/rag/query` | Grounded Q&A |
| `GET` | `/api/v1/stats/dashboard` | Workspace counts |
| `GET` | `/health` | Liveness / config flags (no secrets) |

Interactive docs: `/docs` on the API host.

---

## Tests & quality

```bash
# Backend
cd backend
PYTHONPATH=. pytest -q

# Frontend
cd frontend
npm run lint
npm run build
```

CI on `main` / PRs: pytest, frontend lint + build, Docker image builds.  
CD: pushes `aniket691/finquery-backend` and `aniket691/finquery-frontend` to Docker Hub.

---

## Production deploy

Live instance: **[http://206.189.235.250:8080](http://206.189.235.250:8080)**

Typical host layout:

```text
/opt/finquery          # app (owned by deploy)
deploy user + Docker
.env mode 600
```

Update cycle:

```bash
su - deploy
cd /opt/finquery
git pull
docker compose up -d --build
docker compose logs -f backend
```

Full notes: **[DEPLOY.md](./DEPLOY.md)**.

---

## Security notes

- Passwords hashed with bcrypt; sessions via short-lived JWT
- Libraries are **user-scoped** (no shared tenant data)
- Secrets only in `.env` / host env — never committed
- Prefer SSH keys, firewall limited ports, and do not expose MySQL publicly
- Qdrant port `6333` is for debugging; lock it down in hardened prod

---

## License & contact

Private / portfolio project unless otherwise stated.

**Repo:** [github.com/aniketdalalml-creator/finquery-rag](https://github.com/aniketdalalml-creator/finquery-rag)
