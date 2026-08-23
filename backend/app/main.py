"""
FinQuery API entrypoint.

Run from backend/:
  uvicorn app.main:app --reload --port 8000
"""

from __future__ import annotations

from contextlib import asynccontextmanager
import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.api.v1 import v1_router
from app.core.config import config
from app.core.errors import ConflictError, DomainError, NotFoundError, ValidationError
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
    allow_origins=config.BACKEND_CORS_ORIGINS,
    allow_methods=["GET", "POST", "DELETE"],
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
app.include_router(v1_router, prefix="/api/v1")


# ── Domain error → HTTP mapping (keeps routes free of try/except) ──

def _domain_error_response(request: Request, exc: DomainError, status_code: int):
    return JSONResponse(
        status_code=status_code,
        content={"detail": str(exc), "error": type(exc).__name__},
    )


@app.exception_handler(NotFoundError)
async def _not_found_handler(request: Request, exc: NotFoundError):
    return _domain_error_response(request, exc, 404)


@app.exception_handler(ConflictError)
async def _conflict_handler(request: Request, exc: ConflictError):
    return _domain_error_response(request, exc, 409)


@app.exception_handler(ValidationError)
async def _validation_handler(request: Request, exc: ValidationError):
    return _domain_error_response(request, exc, 422)
