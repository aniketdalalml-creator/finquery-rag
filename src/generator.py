"""Grounded answer generation via Groq (LLaMA 3)."""

from __future__ import annotations

import logging
from typing import List, Tuple

from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from config.config import config

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are FinQuery, an expert AI financial analyst assistant.

STRICT RULES:
1. Answer ONLY using the document context provided below.
2. Cite specific numbers and figures exactly as they appear in the documents.
3. Treat common financial synonyms as the same concept when the context supports it:
   - "revenue" / "sales" / "total revenue" often means "total net sales" or segment net sales in 10-K filings.
   - "cash" may appear as "cash, cash equivalents, and marketable securities".
   - "R&D" means "research and development" expense.
4. If the context contains the answer under a different but equivalent label (e.g. net sales for revenue),
   answer directly with those figures — do NOT say you cannot find it.
5. If nothing relevant exists after applying rule 3, your entire reply must be only:
   "I cannot find this information in the provided documents."
   Never use that sentence if you also provide figures or facts from the context.
6. Never fabricate financial data, percentages, or figures.
7. Structure your answer clearly — use bullet points for lists.
8. State which source file and section your answer comes from."""


class FinancialAnswerGenerator:
    """Generates grounded answers using Groq LLaMA3 API."""

    def __init__(self) -> None:
        if not config.GROQ_API_KEY:
            logger.warning("GROQ_API_KEY not set — LLM answers will not work")
            self.llm = None
        else:
            self.llm = ChatGroq(
                model=config.LLM_MODEL,
                temperature=config.LLM_TEMPERATURE,
                max_tokens=config.MAX_TOKENS,
                groq_api_key=config.GROQ_API_KEY,
            )
            logger.info("Generator ready: %s via Groq API", config.LLM_MODEL)

    def generate(self, query: str, context: str) -> dict:
        """Generate answer from query + retrieved context."""
        if not self.llm:
            return {
                "answer": "⚠️ GROQ_API_KEY not configured. Add it to your .env file.",
                "model": "none",
                "query": query,
            }
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    f"Context from financial documents:\n\n{context}\n\n"
                    "Note: In 10-K filings, total net sales is the usual label for "
                    "company-wide revenue.\n\n"
                    f"Question: {query}"
                )
            ),
        ]
        response = self.llm.invoke(messages)
        logger.info("Generated answer: %s chars", len(response.content))
        return {
            "answer": response.content,
            "model": config.LLM_MODEL,
            "query": query,
        }

    def generate_with_sources(
        self, query: str, docs_with_scores: List[Tuple[Document, float]]
    ) -> dict:
        """Generate answer and return with formatted source list."""
        docs = [d for d, _ in docs_with_scores]
        context = "\n\n".join(
            [
                f"Source: {d.metadata.get('source', 'unknown')}\n{d.page_content}"
                for d in docs
            ]
        )
        result = self.generate(query, context)
        sources = [
            {
                "filename": doc.metadata.get("source", "unknown"),
                "relevance_score": round(1 - float(score), 3),
                "snippet": doc.page_content[:200],
            }
            for doc, score in docs_with_scores
        ]
        result["sources"] = sources
        return result
