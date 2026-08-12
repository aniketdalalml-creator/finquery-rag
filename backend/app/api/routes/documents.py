from fastapi import APIRouter, HTTPException

from app.api.schemas import DocumentsResponse, ResetResponse
import app.state as state

router = APIRouter()


@router.get("/documents", response_model=DocumentsResponse)
async def documents():
    if state.pipeline is None:
        raise HTTPException(500, "Pipeline not initialized")
    stats = state.pipeline.get_stats()
    return DocumentsResponse(
        total_documents=stats["total_documents"],
        collection_name=stats["collection_name"],
        embedding_model=stats["embedding_model"],
        embedding_api=stats["embedding_api"],
    )


@router.delete("/reset", response_model=ResetResponse)
async def reset():
    if state.pipeline is None:
        raise HTTPException(500, "Pipeline not initialized")
    return ResetResponse(**state.pipeline.reset())
