"""API tests for POST /api/v1/rag/query."""

from app.api.v1.routes import rag as rag_routes_module
from app.services.rag_service import FALLBACK_ANSWER


class StubService:
    def __init__(self, result=None, error=None):
        self._result = result or {"answer": "", "sources": []}
        self._error = error
        self.calls = []

    def answer(self, question):
        self.calls.append(question)
        if self._error:
            raise self._error
        return self._result


def patch_service(monkeypatch, service):
    monkeypatch.setattr(
        rag_routes_module, "RagAnswerService", lambda: service
    )


def test_successful_question(api_client, monkeypatch):
    stub = StubService(
        result={
            "answer": "Total net sales were $391,035 million.",
            "sources": [
                {
                    "document_id": 4,
                    "page_start": 10,
                    "page_end": 11,
                    "score": 0.89,
                }
            ],
        }
    )
    patch_service(monkeypatch, stub)

    response = api_client.post(
        "/api/v1/rag/query", json={"question": "What was revenue?"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["answer"].startswith("Total net sales")
    assert body["sources"] == [
        {"document_id": 4, "page_start": 10, "page_end": 11, "score": 0.89}
    ]
    assert stub.calls == ["What was revenue?"]


def test_no_relevant_results_returns_fallback(api_client, monkeypatch):
    stub = StubService(result={"answer": FALLBACK_ANSWER, "sources": []})
    patch_service(monkeypatch, stub)

    response = api_client.post(
        "/api/v1/rag/query", json={"question": "Quantum earnings?"}
    )

    assert response.status_code == 200
    assert response.json()["answer"] == (
        "I don't have enough information in the provided documents."
    )
    assert response.json()["sources"] == []


def test_llm_failure_maps_to_fallback_answer(api_client, monkeypatch):
    from app.services.rag_service import RagAnswerService as _Real

    class LlmFailService(_Real):
        def __init__(self):
            super().__init__(
                provider=FakeP(),
                retriever=FakeR([_hit()]),
                llm_fn=_boom,
            )

    from types import SimpleNamespace

    def _boom(q, c):
        raise RuntimeError("llm down")

    def _hit():
        return SimpleNamespace(
            chunk_id=1,
            score=0.5,
            text="t",
            document_id=1,
            section_id=None,
            page_start=1,
            page_end=2,
        )

    class FakeP:
        model_name = "fake"

        def generate(self, text):
            return [0.0]

        def generate_batch(self, texts):
            return [[0.0] for _ in texts]

    class FakeR:
        def __init__(self, hits):
            self.hits = hits

        def search(self, embedding, top_k=None, document_id=None):
            return self.hits

    monkeypatch.setattr(rag_routes_module, "RagAnswerService", LlmFailService)

    response = api_client.post(
        "/api/v1/rag/query", json={"question": "Any revenue figures?"}
    )

    assert response.status_code == 200
    assert response.json()["answer"] == FALLBACK_ANSWER


def test_source_metadata_shape(api_client, monkeypatch):
    stub = StubService(
        result={
            "answer": "a",
            "sources": [
                {"document_id": 2, "page_start": None, "page_end": None, "score": 0.5}
            ],
        }
    )
    patch_service(monkeypatch, stub)

    body = api_client.post(
        "/api/v1/rag/query", json={"question": "q"}
    ).json()

    assert set(body["sources"][0]) == {"document_id", "page_start", "page_end", "score"}


def test_empty_question_rejected_with_422(api_client, monkeypatch):
    # {} and "" fail schema validation; "   " must be rejected by the real
    # service (ValidationError → 422), so use the real service with fakes.
    from types import SimpleNamespace

    class FakeP:
        model_name = "fake"

        def generate(self, text):
            return [0.0]

        def generate_batch(self, texts):
            return [[0.0] for _ in texts]

    class FakeR:
        def search(self, embedding, top_k=None, document_id=None):
            return []

    from app.services.rag_service import RagAnswerService as Real

    monkeypatch.setattr(
        rag_routes_module,
        "RagAnswerService",
        lambda: Real(provider=FakeP(), retriever=FakeR(), llm_fn=lambda q, c: ""),
    )

    for payload in ({}, {"question": ""}, {"question": "   "}):
        response = api_client.post("/api/v1/rag/query", json=payload)
        assert response.status_code == 422
