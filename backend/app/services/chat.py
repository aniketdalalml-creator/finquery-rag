"""Chat application service — dummy now, RAG later via CHAT_MODE."""

from __future__ import annotations

import time
from typing import Any

from app.core.config import config


def dummy_answer(question: str) -> dict[str, Any]:
    """Deterministic placeholder reply so UI send/receive works without keys."""
    q = question.strip()
    answer = (
        f'This is a **dummy reply** for: "{q}"\n\n'
        "The chat UI is wired. Next steps for real RAG:\n"
        "1. Ingest documents (`POST /ingest`)\n"
        "2. Set `CHAT_MODE=rag` in `.env`\n"
        "3. Configure valid `GROQ_API_KEY` and `JINA_API_KEY`\n\n"
        "Until then, every send returns a local dummy answer."
    )
    return {
        "question": q,
        "answer": answer,
        "sources": [
            {
                "filename": "dummy://finquery",
                "relevance_score": 1.0,
                "snippet": "Placeholder source while RAG is not enabled.",
            }
        ],
        "context_chunks": 0,
        "model": "dummy",
    }


class ChatService:
    """Facade used by API routes. Swap modes without changing the UI contract."""

    def __init__(self, pipeline: Any | None = None) -> None:
        self.pipeline = pipeline

    @property
    def mode(self) -> str:
        mode = (config.CHAT_MODE or "dummy").strip().lower()
        return mode if mode in {"dummy", "rag"} else "dummy"

    def query(self, question: str) -> dict[str, Any]:
        start = time.perf_counter()
        if self.mode == "rag":
            if self.pipeline is None:
                raise RuntimeError("Pipeline not initialized")
            if not self.pipeline.is_ready():
                raise RuntimeError("No documents ingested. Call POST /ingest first.")
            result = self.pipeline.query(question)
        else:
            # Small delay so the UI loading state is visible
            time.sleep(0.45)
            result = dummy_answer(question)

        ms = round((time.perf_counter() - start) * 1000, 2)
        result["processing_time_ms"] = ms
        return result
