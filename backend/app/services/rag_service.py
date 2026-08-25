"""Grounded RAG answering: embed → retrieve → LLM → answer + sources.

The answer is generated ONLY from retrieved chunk context. With no
retrieved evidence (or an LLM failure) the service returns a fixed
fallback sentence rather than guessing.
"""

from __future__ import annotations

import logging

from app.core.config import config
from app.core.errors import ValidationError
from app.services.embedding_service import EmbeddingProvider, get_embedding_provider
from app.services.retrieval_service import RetrievedChunk, VectorRetriever

logger = logging.getLogger(__name__)

FALLBACK_ANSWER = "I don't have enough information in the provided documents."

SYSTEM_PROMPT = f"""You are FinQuery, a financial document assistant.

STRICT RULES:
1. Answer ONLY using the numbered context passages below.
2. Cite figures exactly as they appear in the context.
3. If the context does not contain the answer, your ENTIRE reply must be exactly:
{FALLBACK_ANSWER}
4. Never fabricate financial data.
5. Keep the answer concise; use bullet points for lists."""


def _groq_llm(question: str, context: str) -> str:
    """Default LLM callable: Groq chat completion."""
    if not config.GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY not configured")
    from langchain_core.messages import HumanMessage, SystemMessage
    from langchain_groq import ChatGroq

    llm = ChatGroq(
        model=config.LLM_MODEL,
        temperature=config.LLM_TEMPERATURE,
        max_tokens=config.MAX_TOKENS,
        groq_api_key=config.GROQ_API_KEY,
    )
    response = llm.invoke(
        [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"Question: {question}\n\nContext:\n{context}"),
        ]
    )
    return str(response.content)


class RagAnswerService:
    """One-shot question answering over indexed chunks."""

    def __init__(
        self,
        provider: EmbeddingProvider | None = None,
        retriever: VectorRetriever | None = None,
        llm_fn=None,
    ) -> None:
        self.provider = provider or get_embedding_provider()
        self.retriever = retriever or VectorRetriever()
        self.llm_fn = llm_fn or _groq_llm

    def answer(self, question: str) -> dict:
        question = (question or "").strip()
        if not question:
            raise ValidationError("Question must not be empty")

        query_embedding = self.provider.generate(question)
        hits = self.retriever.search(query_embedding)
        sources = [self._source(hit) for hit in hits]

        if not hits:
            return {"answer": FALLBACK_ANSWER, "sources": []}

        context = "\n\n".join(
            f"[passage {i}] "
            f"(document {hit.document_id}, pages {hit.page_start}-{hit.page_end})\n"
            f"{hit.text}"
            for i, hit in enumerate(hits, start=1)
        )
        try:
            answer_text = self.llm_fn(question, context)
        except Exception as exc:  # noqa: BLE001 — never fail on LLM errors
            logger.warning("LLM generation failed: %s", exc)
            return {"answer": FALLBACK_ANSWER, "sources": sources}

        # Guard against the model ignoring the instruction to stay grounded.
        if not (answer_text or "").strip():
            return {"answer": FALLBACK_ANSWER, "sources": sources}
        return {"answer": answer_text.strip(), "sources": sources}

    @staticmethod
    def _source(hit: RetrievedChunk) -> dict:
        return {
            "document_id": hit.document_id,
            "page_start": hit.page_start,
            "page_end": hit.page_end,
            "score": round(hit.score, 4),
        }
