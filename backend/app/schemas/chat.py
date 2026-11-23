"""Pydantic schemas for chat API."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)
    conversation_id: UUID | None = Field(
        default=None,
        description="Existing conversation ID. Omit to start a new conversation.",
    )
    system_prompt: str | None = Field(
        default=None,
        max_length=4000,
        description="Optional override for this turn's system prompt.",
    )


class ChatMessageOut(BaseModel):
    id: UUID
    role: str
    content: str
    model: str | None = None
    provider: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatResponse(BaseModel):
    conversation_id: UUID
    message: ChatMessageOut
    reply: str
    model: str
    provider: str


class ConversationOut(BaseModel):
    id: UUID
    title: str | None
    created_at: datetime
    updated_at: datetime
    messages: list[ChatMessageOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}
