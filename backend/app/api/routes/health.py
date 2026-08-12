from fastapi import APIRouter

from app.api.schemas import HealthResponse
from app.core.config import config
import app.state as state

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health():
    ready = False
    docs = 0
    if state.pipeline is not None:
        try:
            ready = state.pipeline.is_ready()
            docs = state.pipeline.get_stats().get("total_documents", 0)
        except Exception:
            ready = False
    if state.chat_service.mode == "dummy":
        ready = True
    return HealthResponse(
        status="ok",
        pipeline_ready=ready,
        total_chunks=docs,
        llm_model=config.LLM_MODEL if state.chat_service.mode == "rag" else "dummy",
        groq_configured=bool(config.GROQ_API_KEY),
        jina_configured=bool(config.JINA_API_KEY),
        chat_mode=state.chat_service.mode,
    )
