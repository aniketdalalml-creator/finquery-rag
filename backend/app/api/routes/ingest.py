import logging

from fastapi import APIRouter, HTTPException

from app.api.schemas import IngestRequest, IngestResponse
import app.state as state

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/ingest", response_model=IngestResponse)
async def ingest(request: IngestRequest):
    if state.pipeline is None:
        raise HTTPException(500, "Pipeline not initialized")
    try:
        result = state.pipeline.ingest_documents(request.file_paths)
        return IngestResponse(**result)
    except Exception as e:
        logger.error("Ingest error: %s", e)
        raise HTTPException(500, str(e)) from e
