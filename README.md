# FinQuery RAG

Financial document Q&A with a React UI and FastAPI RAG backend.

```
rag_finquery/
├── frontend/          # React + Vite (chat UI)
├── backend/           # FastAPI + RAG pipeline
├── docker-compose.yml
└── .env               # GROQ_API_KEY, JINA_API_KEY, CHAT_MODE
```

## Quickstart

**1. Backend (dummy chat by default — no API keys required)**

```powershell
cd backend
..\..\..\.venv\Scripts\Activate.ps1   # or: ..\.venv\Scripts\Activate.ps1 from repo root
# from repo root:
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = "backend"
$env:CHAT_MODE = "dummy"
uvicorn app.main:app --reload --port 8000 --app-dir backend
```

Or from `backend/`:

```powershell
cd backend
$env:PYTHONPATH = "."
$env:CHAT_MODE = "dummy"
uvicorn app.main:app --reload --port 8000
```

**2. Frontend**

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — type a question and send. You get a **dummy reply** while `CHAT_MODE=dummy`.

## Enable real RAG

1. Put docs in `backend/data/raw/` (or use `backend/sample_docs/`)
2. Set in `.env`:
   ```
   CHAT_MODE=rag
   GROQ_API_KEY=...
   JINA_API_KEY=...
   ```
3. Restart API, then `POST /ingest` (or Settings → Re-ingest)

## Backend layout (feature-by-feature RAG)

```
backend/app/
├── main.py              # FastAPI entry
├── api/                 # HTTP routes + schemas
│   └── routes/          # health, query, ingest, documents
├── core/                # config
├── services/            # chat service (dummy | rag)
└── rag/                 # implement one module at a time
    ├── loader.py
    ├── chunker.py
    ├── embeddings.py
    ├── retriever.py
    ├── generator.py
    └── pipeline.py
```

Suggested order: loader → chunker → embeddings → retriever → generator → pipeline.

## Frontend layout

```
frontend/src/
├── app/                 # shell (App, styles, entry)
├── features/chat/       # chat feature (page, hooks, api, components)
└── shared/              # Logo, Header, …
```

## API

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Status + `chat_mode` |
| POST | `/query` | Dummy or RAG answer |
| POST | `/ingest` | Index documents |
| GET | `/documents` | Index stats |
| DELETE | `/reset` | Clear vector store |

## Tests

```powershell
cd backend
$env:PYTHONPATH = "."
pytest -v
```
