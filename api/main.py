# FinQuery RAG API — Lightweight (Groq + Jina AI, no local models)
#
# curl http://localhost:8000/health
# curl -X POST http://localhost:8000/ingest
# curl -X POST http://localhost:8000/query \
#      -H "Content-Type: application/json" \
#      -d '{"question": "What was total revenue?"}'
# curl -X DELETE http://localhost:8000/reset

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import time
import logging

from api.schemas import (
    DocumentsResponse,
    HealthResponse,
    IngestRequest,
    IngestResponse,
    QueryRequest,
    QueryResponse,
    ResetResponse,
    SourceDocument,
)
from config.config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
pipeline = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global pipeline
    try:
        from src.pipeline import RAGPipeline

        pipeline = RAGPipeline()
        logger.info("Pipeline initialized")
    except Exception as e:
        logger.error("Pipeline init error: %s", e)
        pipeline = None
    yield


app = FastAPI(
    title="FinQuery RAG API",
    description="Lightweight RAG for financial documents. Uses Groq LLM + Jina AI Embeddings — no local model downloads.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    ms = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s → %s (%.0fms)",
        request.method,
        request.url.path,
        response.status_code,
        ms,
    )
    return response


@app.get("/health", response_model=HealthResponse)
async def health():
    ready = pipeline is not None and pipeline.is_ready()
    docs = 0
    if pipeline:
        try:
            docs = pipeline.get_stats().get("total_documents", 0)
        except Exception:
            pass
    return HealthResponse(
        status="ok",
        pipeline_ready=ready,
        total_chunks=docs,
        llm_model=config.LLM_MODEL,
        groq_configured=bool(config.GROQ_API_KEY),
        jina_configured=bool(config.JINA_API_KEY),
    )


@app.post("/ingest", response_model=IngestResponse)
async def ingest(request: IngestRequest):
    if pipeline is None:
        raise HTTPException(500, "Pipeline not initialized")
    try:
        fps = request.file_paths
        result = pipeline.ingest_documents(fps)
        return IngestResponse(**result)
    except Exception as e:
        logger.error("Ingest error: %s", e)
        raise HTTPException(500, str(e)) from e


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    if pipeline is None:
        raise HTTPException(500, "Pipeline not initialized")
    if not pipeline.is_ready():
        raise HTTPException(400, "No documents ingested. Call POST /ingest first.")
    start = time.perf_counter()
    try:
        result = pipeline.query(request.question)
        ms = round((time.perf_counter() - start) * 1000, 2)
        sources = [SourceDocument(**s) for s in result.get("sources", [])]
        return QueryResponse(
            question=result["question"],
            answer=result["answer"],
            sources=sources,
            context_chunks=result["context_chunks"],
            model=result.get("model", config.LLM_MODEL),
            processing_time_ms=ms,
        )
    except Exception as e:
        logger.error("Query error: %s", e)
        raise HTTPException(500, str(e)) from e


@app.delete("/reset", response_model=ResetResponse)
async def reset():
    if pipeline is None:
        raise HTTPException(500, "Pipeline not initialized")
    return ResetResponse(**pipeline.reset())


@app.get("/documents", response_model=DocumentsResponse)
async def documents():
    if pipeline is None:
        raise HTTPException(500, "Pipeline not initialized")
    stats = pipeline.get_stats()
    return DocumentsResponse(
        total_documents=stats["total_documents"],
        collection_name=stats["collection_name"],
        embedding_model=stats["embedding_model"],
        embedding_api=stats["embedding_api"],
    )
