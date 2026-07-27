from dataclasses import dataclass, field
from dotenv import load_dotenv
import os

load_dotenv()


@dataclass
class RAGConfig:
    # ── Groq LLM ──────────────────────────────
    GROQ_API_KEY: str = field(default_factory=lambda: os.getenv("GROQ_API_KEY", ""))
    LLM_MODEL: str = field(
        default_factory=lambda: os.getenv("LLM_MODEL", "llama-3.1-8b-instant")
    )
    LLM_TEMPERATURE: float = 0.1
    MAX_TOKENS: int = 1024

    # ── Jina AI Embeddings (API, no download) ──
    JINA_API_KEY: str = field(default_factory=lambda: os.getenv("JINA_API_KEY", ""))
    JINA_EMBEDDING_MODEL: str = "jina-embeddings-v2-base-en"
    JINA_API_URL: str = "https://api.jina.ai/v1/embeddings"
    EMBEDDING_DIMENSION: int = 768  # jina-embeddings-v2-base-en produces 768-dim vectors

    # ── ChromaDB ──────────────────────────────
    VECTORSTORE_PATH: str = "vectorstore/chroma_db"
    COLLECTION_NAME: str = "financial_docs"

    # ── Chunking ──────────────────────────────
    CHUNK_SIZE: int = 400
    CHUNK_OVERLAP: int = 50

    # ── Retrieval ─────────────────────────────
    TOP_K: int = 5

    # ── Paths ─────────────────────────────────
    RAW_DOCS_PATH: str = "data/raw"
    SAMPLE_DOCS_PATH: str = "sample_docs"


config = RAGConfig()
