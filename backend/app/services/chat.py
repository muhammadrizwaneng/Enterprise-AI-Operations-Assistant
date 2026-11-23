"""Chat orchestration: history persistence + LLM calls."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.models.conversation import Conversation, Message
from app.schemas.chat import ChatRequest, ChatResponse, ChatMessageOut
from app.services.llm.base import ChatMessage, LLMError, LLMProvider
from app.services.llm.factory import get_llm_provider

logger = get_logger(__name__)


class ChatService:
    """Coordinates conversation storage and provider completion."""

    def __init__(
        self,
        db: Session,
        *,
        provider: LLMProvider | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.db = db
        self.settings = settings or get_settings()
        self.provider = provider or get_llm_provider()

    def chat(self, request: ChatRequest) -> ChatResponse:
        conversation = self._get_or_create_conversation(request.conversation_id)
        user_message = Message(
            conversation_id=conversation.id,
            role="user",
            content=request.message.strip(),
        )
        self.db.add(user_message)
        self.db.flush()

        if not conversation.title:
            conversation.title = request.message.strip()[:120]

        llm_messages = self._build_llm_messages(
            conversation.id,
            system_prompt=request.system_prompt,
        )

        try:
            llm_response = self.provider.chat(llm_messages)
        except LLMError:
            self.db.rollback()
            raise
        except Exception as exc:  # unexpected provider failure
            logger.exception("Unexpected LLM failure")
            self.db.rollback()
            raise LLMError(str(exc), status_code=502) from exc

        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=llm_response.content,
            model=llm_response.model,
            provider=llm_response.provider,
        )
        self.db.add(assistant_message)
        self.db.commit()
        self.db.refresh(assistant_message)

        logger.info(
            "Chat completed conversation_id=%s provider=%s model=%s",
            conversation.id,
            llm_response.provider,
            llm_response.model,
        )

        return ChatResponse(
            conversation_id=conversation.id,
            message=ChatMessageOut.model_validate(assistant_message),
            reply=assistant_message.content,
            model=llm_response.model,
            provider=llm_response.provider,
        )

    def get_conversation(self, conversation_id: UUID) -> Conversation | None:
        stmt = (
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .options(selectinload(Conversation.messages))
        )
        return self.db.scalar(stmt)

    def _get_or_create_conversation(
        self, conversation_id: UUID | None
    ) -> Conversation:
        if conversation_id is None:
            conversation = Conversation()
            self.db.add(conversation)
            self.db.flush()
            return conversation

        conversation = self.db.get(Conversation, conversation_id)
        if conversation is None:
            raise LLMError(
                f"Conversation {conversation_id} not found",
                status_code=404,
            )
        return conversation

    def _build_llm_messages(
        self,
        conversation_id: UUID,
        *,
        system_prompt: str | None,
    ) -> list[ChatMessage]:
        system_content = (system_prompt or self.settings.llm_system_prompt).strip()
        messages: list[ChatMessage] = [
            ChatMessage(role="system", content=system_content)
        ]

        history = self.db.scalars(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
        ).all()

        # Keep only the most recent N non-system turns for context window control
        max_history = max(1, self.settings.llm_max_history_messages)
        trimmed = history[-max_history:]
        for msg in trimmed:
            if msg.role not in {"user", "assistant"}:
                continue
            messages.append(ChatMessage(role=msg.role, content=msg.content))  # type: ignore[arg-type]

        return messages
