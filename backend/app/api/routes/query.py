import logging

from fastapi import APIRouter, HTTPException

from app.api.schemas import QueryRequest, QueryResponse, SourceDocument
import app.state as state

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    try:
        result = state.chat_service.query(request.question)
        sources = [SourceDocument(**s) for s in result.get("sources", [])]
        return QueryResponse(
            question=result["question"],
            answer=result["answer"],
            sources=sources,
            context_chunks=result.get("context_chunks", 0),
            model=result.get("model", "dummy"),
            processing_time_ms=result.get("processing_time_ms", 0),
        )
    except RuntimeError as e:
        raise HTTPException(400, str(e)) from e
    except Exception as e:
        msg = str(e)
        logger.error("Query error: %s", e)
        if "expired_api_key" in msg or "Invalid API Key" in msg:
            raise HTTPException(
                401,
                "Groq API key is invalid or expired. Update GROQ_API_KEY in .env "
                "(https://console.groq.com/keys) and restart the API.",
            ) from e
        raise HTTPException(500, msg) from e
