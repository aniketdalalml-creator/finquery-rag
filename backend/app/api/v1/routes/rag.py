"""RAG question-answering endpoint (grounded on indexed chunks)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.repositories.document import DocumentRepository
from app.security import get_current_user
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
def rag_query(
    payload: RagQueryRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    document_ids = DocumentRepository(db).list_ids_for_user(user.id)
    service = RagAnswerService()
    return service.answer(
        payload.question.strip(),
        document_ids=document_ids,
    )
