"""RAG question-answering endpoint (grounded on indexed chunks)."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.rag_service import RagAnswerService

router = APIRouter(prefix="/rag", tags=["rag"])


class RagQueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)


class RagSource(BaseModel):
    document_id: int | None = None
    page_start: int | None = None
    page_end: int | None = None
    score: float


class RagQueryResponse(BaseModel):
    answer: str
    sources: list[RagSource]


@router.post("/query", response_model=RagQueryResponse)
def rag_query(payload: RagQueryRequest) -> dict:
    service = RagAnswerService()
    return service.answer(payload.question.strip())
