"""Tests for the RAG answer service (fake provider/retriever/LLM)."""

import pytest

from app.core.errors import ValidationError
from app.services.rag_service import FALLBACK_ANSWER, RagAnswerService
from app.services.retrieval_service import RetrievedChunk


class FakeProvider:
    model_name = "fake"

    def __init__(self):
        self.embedded = []

    def generate(self, text: str) -> list[float]:
        self.embedded.append(text)
        return [0.1, 0.2]

    def generate_batch(self, texts):
        return [self.generate(t) for t in texts]


class FakeRetriever:
    def __init__(self, hits=None):
        self.hits = hits or []
        self.searches = []

    def search(self, query_embedding, top_k=None, document_id=None):
        self.searches.append({"top_k": top_k, "document_id": document_id})
        return self.hits


def make_hit(chunk_id=11, document_id=4, page_start=10, page_end=11, score=0.89):
    return RetrievedChunk(
        chunk_id=chunk_id,
        score=score,
        text="Total net sales were $391,035 million.",
        document_id=document_id,
        section_id=3,
        page_start=page_start,
        page_end=page_end,
    )


def test_successful_question_returns_grounded_answer():
    provider, retriever = FakeProvider(), FakeRetriever([make_hit()])
    llm_calls = []

    service = RagAnswerService(
        provider=provider,
        retriever=retriever,
        llm_fn=lambda q, c: (
            llm_calls.append((q, c)) or "Revenue was $391,035 million."
        ),
    )

    result = service.answer("What was total net sales?")

    assert result["answer"] == "Revenue was $391,035 million."
    assert provider.embedded == ["What was total net sales?"]
    # Context passed to the LLM contains the retrieved passage.
    assert "$391,035" in llm_calls[0][1]
    assert "document 4" in llm_calls[0][1]


def test_no_relevant_results_returns_exact_fallback():
    service = RagAnswerService(
        provider=FakeProvider(), retriever=FakeRetriever([]), llm_fn=lambda q, c: "x"
    )

    result = service.answer("What was EBITDA margin on Mars?")

    assert result["answer"] == FALLBACK_ANSWER
    assert result["sources"] == []


def test_llm_failure_falls_back_without_raising():
    def broken_llm(q, c):
        raise RuntimeError("groq unavailable")

    service = RagAnswerService(
        provider=FakeProvider(),
        retriever=FakeRetriever([make_hit()]),
        llm_fn=broken_llm,
    )

    result = service.answer("What was revenue?")

    assert result["answer"] == FALLBACK_ANSWER
    assert len(result["sources"]) == 1


def test_source_metadata_returned():
    service = RagAnswerService(
        provider=FakeProvider(),
        retriever=FakeRetriever([make_hit(score=0.91234)]),
        llm_fn=lambda q, c: "ok",
    )

    result = service.answer("revenue?")

    assert result["sources"] == [
        {
            "document_id": 4,
            "page_start": 10,
            "page_end": 11,
            "score": 0.9123,
        }
    ]


def test_empty_question_rejected():
    service = RagAnswerService(
        provider=FakeProvider(), retriever=FakeRetriever([]), llm_fn=lambda q, c: ""
    )

    for question in ("", "   ", None):
        with pytest.raises(ValidationError):
            service.answer(question)


def test_blank_llm_reply_falls_back():
    service = RagAnswerService(
        provider=FakeProvider(),
        retriever=FakeRetriever([make_hit()]),
        llm_fn=lambda q, c: "   ",
    )
    assert service.answer("q")["answer"] == FALLBACK_ANSWER
