"""RAG HTTP endpoints (Phase 4)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.session import get_db
from app.schemas.rag import RagAskRequest, RagAskResponse
from app.services.rag import RAGError, RAGService

router = APIRouter(prefix="/api/v1", tags=["rag"])
logger = get_logger(__name__)


@router.post("/rag/ask", response_model=RagAskResponse)
def rag_ask(
    request: RagAskRequest,
    db: Session = Depends(get_db),
) -> RagAskResponse:
    """
    Answer a question using retrieved policy chunks (RAG).

    Stateless: does not persist conversation history.
    Requires prior document ingestion into ``document_embeddings``.
    """
    service = RAGService(db)
    try:
        return service.ask(
            request.question,
            top_k=request.top_k,
            min_similarity=request.min_similarity,
        )
    except RAGError as exc:
        logger.warning("RAG failed status=%s error=%s", exc.status_code, exc)
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected RAG failure")
        raise HTTPException(
            status_code=500,
            detail="RAG request failed",
        ) from exc
