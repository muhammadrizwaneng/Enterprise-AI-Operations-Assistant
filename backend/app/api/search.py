"""Semantic search HTTP endpoints (Phase 3)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.session import get_db
from app.schemas.search import SemanticSearchRequest, SemanticSearchResponse
from app.services.semantic_search import SemanticSearchError, SemanticSearchService

router = APIRouter(prefix="/api/v1", tags=["search"])
logger = get_logger(__name__)


@router.post("/search/semantic", response_model=SemanticSearchResponse)
def semantic_search(
    request: SemanticSearchRequest,
    db: Session = Depends(get_db),
) -> SemanticSearchResponse:
    """
    Rank document chunks by cosine similarity to the query embedding.

    Requires prior document ingestion into ``document_embeddings``.
    Does not generate an LLM answer (not RAG).
    """
    service = SemanticSearchService(db)
    try:
        return service.search(
            request.query,
            top_k=request.top_k,
            min_similarity=request.min_similarity,
        )
    except SemanticSearchError as exc:
        logger.warning(
            "Semantic search failed status=%s error=%s",
            exc.status_code,
            exc,
        )
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected semantic search failure")
        raise HTTPException(
            status_code=500,
            detail="Semantic search failed",
        ) from exc
