from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import os

from dotenv import load_dotenv

# backend/ is the runtime root (parents: core → app → backend)
BACKEND_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_ROOT.parent

# Prefer backend/.env, then repo-root .env (override=True so .env wins over stale shell vars)
load_dotenv(BACKEND_ROOT / ".env", override=True)
load_dotenv(REPO_ROOT / ".env", override=True)


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _as_absolute_path(value: str) -> Path:
    """Anchor relative paths to REPO_ROOT so behaviour never depends on cwd."""
    path = Path(value)
    return path if path.is_absolute() else (REPO_ROOT / path).resolve()


@dataclass
class RAGConfig:
    """Central config. Toggle CHAT_MODE to implement RAG feature-by-feature."""

    # ── Chat mode ─────────────────────────────
    # dummy = fake replies (no LLM keys needed)
    # rag   = full retrieve + generate pipeline
    CHAT_MODE: str = field(
        default_factory=lambda: _env("CHAT_MODE", "dummy").lower()
    )

    # ── Groq LLM ──────────────────────────────
    GROQ_API_KEY: str = field(default_factory=lambda: _env("GROQ_API_KEY"))
    LLM_MODEL: str = field(
        default_factory=lambda: _env("LLM_MODEL", "openai/gpt-oss-120b")
    )
    LLM_TEMPERATURE: float = 0.1
    MAX_TOKENS: int = 1024

    # ── Jina AI Embeddings (API, no download) ──
    JINA_API_KEY: str = field(default_factory=lambda: _env("JINA_API_KEY"))
    JINA_EMBEDDING_MODEL: str = "jina-embeddings-v2-base-en"
    JINA_API_URL: str = "https://api.jina.ai/v1/embeddings"
    EMBEDDING_DIMENSION: int = 768

    # ── ChromaDB ──────────────────────────────
    VECTORSTORE_PATH: str = field(
        default_factory=lambda: str(BACKEND_ROOT / "vectorstore" / "chroma_db")
    )
    COLLECTION_NAME: str = "financial_docs"

    # ── Chunking ──────────────────────────────
    CHUNK_SIZE: int = 400
    CHUNK_OVERLAP: int = 50

    # ── Retrieval ─────────────────────────────
    TOP_K: int = 5

    # ── Paths ─────────────────────────────────
    RAW_DOCS_PATH: str = field(
        default_factory=lambda: str(BACKEND_ROOT / "data" / "raw")
    )
    SAMPLE_DOCS_PATH: str = field(
        default_factory=lambda: str(BACKEND_ROOT / "sample_docs")
    )

    # ── HTTP / CORS ───────────────────────────
    # Comma-separated list of allowed browser origins (override via .env)
    BACKEND_CORS_ORIGINS: list[str] = field(
        default_factory=lambda: [
            origin
            for origin in (
                part.strip()
                for part in _env(
                    "BACKEND_CORS_ORIGINS",
                    "http://localhost:5173,http://127.0.0.1:5173",
                ).split(",")
            )
            if origin
        ]
    )

    # ── Database ──────────────────────────────
    # Default: zero-setup local SQLite file. Examples:
    #   mysql+pymysql://user:password@localhost:3306/llm_db
    #   postgresql+psycopg://user:password@localhost:5432/finance_rag
    DATABASE_URL: str = field(
        default_factory=lambda: _env(
            "DATABASE_URL", f"sqlite:///{(BACKEND_ROOT / 'finance_rag.db').as_posix()}"
        )
    )

    # ── Object storage ────────────────────────
    # local = filesystem storage rooted at STORAGE_PATH (S3/MinIO later)
    STORAGE_BACKEND: str = field(
        default_factory=lambda: _env("STORAGE_BACKEND", "local").lower()
    )
    STORAGE_PATH: str = field(
        default_factory=lambda: str(
            _as_absolute_path(
                _env("STORAGE_PATH", str(BACKEND_ROOT / "storage_data"))
            )
        )
    )


config = RAGConfig()
