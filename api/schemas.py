from pydantic import BaseModel, Field, field_validator
from typing import List, Optional


class QueryRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        max_length=500,
        json_schema_extra={
            "examples": ["What was Apple's total revenue in 2023?"]
        },
    )

    @field_validator("question")
    @classmethod
    def question_not_blank(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("Question must be at least 3 characters (after trimming spaces).")
        return v


class SourceDocument(BaseModel):
    filename: str
    relevance_score: float
    snippet: str


class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: List[SourceDocument]
    context_chunks: int
    model: str
    processing_time_ms: float


class IngestRequest(BaseModel):
    file_paths: Optional[List[str]] = None


class IngestResponse(BaseModel):
    status: str
    chunks_added: int
    sources: List[str]
    message: str


class HealthResponse(BaseModel):
    status: str
    pipeline_ready: bool
    total_chunks: int
    llm_model: str
    groq_configured: bool
    jina_configured: bool


class ResetResponse(BaseModel):
    status: str
    message: str


class DocumentsResponse(BaseModel):
    total_documents: int
    collection_name: str
    embedding_model: str
    embedding_api: str
