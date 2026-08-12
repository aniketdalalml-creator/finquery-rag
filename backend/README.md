# Backend

Industry-style FastAPI app for FinQuery RAG.

## Run

```powershell
cd backend
$env:PYTHONPATH = "."
$env:CHAT_MODE = "dummy"   # or rag
uvicorn app.main:app --reload --port 8000
```

## CHAT_MODE

| Value | Behavior |
|-------|----------|
| `dummy` | `/query` returns a local placeholder reply (default) |
| `rag` | Full retrieve + Groq generate (needs keys + ingest) |

## RAG modules (`app/rag/`)

Implement in order — each is independently testable:

1. `loader.py` — documents in
2. `chunker.py` — split text
3. `embeddings.py` — vectors + Chroma
4. `retriever.py` — similarity search
5. `generator.py` — LLM answer
6. `pipeline.py` — wire ingest/query
