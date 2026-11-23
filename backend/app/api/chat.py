"""Chat HTTP endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.session import get_db
from app.schemas.chat import ChatRequest, ChatResponse, ConversationOut
from app.services.chat import ChatService
from app.services.llm.base import LLMError

router = APIRouter(prefix="/api/v1", tags=["chat"])
logger = get_logger(__name__)


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    """
    Send a user message and receive an assistant reply.

    Omit `conversation_id` to start a new conversation. Reuse the returned
    conversation_id on subsequent turns to keep history.
    """
    service = ChatService(db)
    try:
        return service.chat(request)
    except LLMError as exc:
        status = exc.status_code or 502
        logger.warning("Chat failed status=%s error=%s", status, exc)
        raise HTTPException(status_code=status, detail=str(exc)) from exc


@router.get("/conversations/{conversation_id}", response_model=ConversationOut)
def get_conversation(
    conversation_id: UUID,
    db: Session = Depends(get_db),
) -> ConversationOut:
    """Fetch a conversation and its persisted messages."""
    service = ChatService(db)
    conversation = service.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return ConversationOut.model_validate(conversation)
