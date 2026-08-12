"""
FinQuery API entrypoint.

Run from backend/:
  uvicorn app.main:app --reload --port 8000
"""

from __future__ import annotations

from contextlib import asynccontextmanager
import logging
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import config
from app.services.chat import ChatService
import app.state as state

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        from app.rag.pipeline import RAGPipeline

        state.pipeline = RAGPipeline()
        state.chat_service = ChatService(pipeline=state.pipeline)
        logger.info("Pipeline initialized (CHAT_MODE=%s)", config.CHAT_MODE)
    except Exception as e:
        logger.error("Pipeline init error: %s — falling back to dummy chat", e)
        state.pipeline = None
        state.chat_service = ChatService(pipeline=None)
    yield


app = FastAPI(
    title="FinQuery RAG API",
    description="Financial RAG API. CHAT_MODE=dummy|rag",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8501",
        "http://127.0.0.1:8501",
        "*",
    ],
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


app.include_router(api_router)
