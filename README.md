# FinQuery RAG

A **lightweight** Retrieval-Augmented Generation (RAG) service for financial documents.

- **LLM:** Groq (LLaMA 3) — cloud API
- **Embeddings:** Jina AI — cloud API (no local model downloads)
- **Vector store:** ChromaDB (persistent, local)
- **API:** FastAPI
- **UI:** Streamlit

Zero `torch`, zero `transformers`, zero `sentence-transformers` — install in under a minute.

**Python:** **3.10–3.13** (tested on 3.13 + Windows with wheel-only installs). Prefer a **virtual environment** (`python -m venv .venv`) so this project’s pins do not fight other global packages (Gradio, LangGraph, etc.). Docker uses **Python 3.11**.

**Windows / `pip install`:** Older pins used `chromadb<1` + `langchain==0.1.x`, which pulled **NumPy 1.x** and **`chroma-hnswlib` source builds** (needs **Microsoft C++ Build Tools**). Current `requirements.txt` uses **LangChain 0.3.x**, **NumPy 2.x**, and **ChromaDB 1.5.x** so normal installs use **prebuilt wheels** without MSVC.

---

## Quickstart

**Windows (recommended — isolated venv):**

```powershell
.\scripts\setup.ps1
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = "."
```

**Linux / macOS:**

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=.
cp .env.example .env
# fill in GROQ_API_KEY and JINA_API_KEY
```

Then (any OS, with venv active and `PYTHONPATH=.` set):

```bash
cp .env.example .env   # if not done yet
# fill in GROQ_API_KEY and JINA_API_KEY

pip install -r requirements.txt   # skip if setup.ps1 already ran

# 1. Ingest: uses `data/raw/` if it contains .pdf / .txt files, else `sample_docs/`
PYTHONPATH=. python src/pipeline.py

# 2. Start the API
PYTHONPATH=. uvicorn api.main:app --reload --port 8000

# 3. Start the UI (in another terminal)
streamlit run app/streamlit_app.py
```

Then open <http://localhost:8501>.

---

## Project layout

```
finquery-rag/
├── api/              # FastAPI service (main.py, schemas.py)
├── app/              # Streamlit chat UI
├── src/              # RAG components (loader, chunker, embedder, retriever, generator, pipeline)
├── config/           # Configuration dataclass
├── sample_docs/      # Bundled Apple 10-K excerpt
├── data/raw/         # Place your own PDFs / TXTs here
├── vectorstore/      # ChromaDB persistence dir (gitignored)
└── tests/            # pytest suite
```

---

## API endpoints

| Method | Path         | Purpose                                |
|--------|--------------|----------------------------------------|
| GET    | `/health`    | Health + readiness + key configuration |
| POST   | `/ingest`    | Load + chunk + embed documents         |
| POST   | `/query`     | Retrieve + generate grounded answer    |
| GET    | `/documents` | Vector-store stats                     |
| DELETE | `/reset`     | Clear the vector store                 |

---

## Tests

```bash
PYTHONPATH=. pytest -v
```

External API calls are mocked, so the test suite runs offline.

---

## Docker

```bash
docker compose up --build
```

Brings up the API on `:8000` and the Streamlit UI on `:8501`. The UI container sets `FINQUERY_API_URL=http://api:8000` so server-side requests reach the API service by Docker DNS name.

---

## Configuration

| Variable | Purpose |
|----------|---------|
| `GROQ_API_KEY` | Groq LLM |
| `JINA_API_KEY` | Jina embeddings API |
| `FINQUERY_API_URL` | Optional; default API base for Streamlit (`http://localhost:8000` locally; set automatically in Compose for the UI service) |
