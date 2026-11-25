"""
Retrieval-Augmented Generation (Phase 4).

Retrieves policy chunks via SemanticSearchService, optionally expands
same-document neighbor chunks into LLM context, then asks the configured
LLMProvider for a grounded answer. Does not use ChatService (no history).

Neighbor expansion does not change semantic search ranking or API source
attribution (sources remain the original ranked hits).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import TypeAlias

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.models.document_embedding import DocumentEmbedding
from app.schemas.rag import (
    RagAskResponse,
    RagRetrievalInfo,
    RagSource,
)
from app.schemas.search import SemanticSearchResult
from app.services.llm.base import ChatMessage, LLMError, LLMProvider
from app.services.llm.factory import get_llm_provider
from app.services.neighbor_expansion import (
    build_context_blocks,
    format_context_blocks,
    plan_neighbors,
)
from app.services.semantic_search import SemanticSearchError, SemanticSearchService

logger = get_logger(__name__)

INSUFFICIENT_RETRIEVAL_ANSWER = (
    "I do not have enough information in the retrieved policy documents "
    "to answer that question."
)

ChunkKey: TypeAlias = tuple[str, int]
NeighborTextLoader: TypeAlias = Callable[[Sequence[ChunkKey]], Mapping[ChunkKey, str]]


class RAGError(RuntimeError):
    """Raised when RAG orchestration fails."""

    def __init__(self, message: str, *, status_code: int = 500) -> None:
        super().__init__(message)
        self.status_code = status_code


class RAGService:
    """Retrieve relevant chunks, then generate a grounded answer."""

    def __init__(
        self,
        db: Session,
        *,
        search_service: SemanticSearchService | None = None,
        llm_provider: LLMProvider | None = None,
        settings: Settings | None = None,
        neighbor_text_loader: NeighborTextLoader | None = None,
    ) -> None:
        self.db = db
        self.settings = settings or get_settings()
        self.search_service = search_service or SemanticSearchService(
            db, settings=self.settings
        )
        self.llm_provider = llm_provider or get_llm_provider()
        self._neighbor_text_loader = neighbor_text_loader

    def ask(
        self,
        question: str,
        *,
        top_k: int | None = None,
        min_similarity: float | None = None,
    ) -> RagAskResponse:
        cleaned = self._validate_question(question)
        limit = self._resolve_top_k(top_k)
        threshold = self._resolve_min_similarity(min_similarity)
        retrieval = RagRetrievalInfo(top_k=limit, min_similarity=threshold)

        try:
            search_response = self.search_service.search(
                cleaned,
                top_k=limit,
                min_similarity=threshold,
            )
        except SemanticSearchError as exc:
            raise RAGError(str(exc), status_code=exc.status_code or 502) from exc

        hits = list(search_response.results)
        # Attribution stays on original ranked search hits only.
        sources = [self._to_source(hit) for hit in hits]

        if not hits:
            logger.info("RAG abstain: no retrieval hits question=%r", cleaned[:80])
            return RagAskResponse(
                question=cleaned,
                answer=INSUFFICIENT_RETRIEVAL_ANSWER,
                model="",
                provider="",
                sources=[],
                retrieval=retrieval,
            )

        context = self._build_context(hits)
        system_content = self._build_system_prompt(context)
        messages = [
            ChatMessage(role="system", content=system_content),
            ChatMessage(role="user", content=cleaned),
        ]

        try:
            llm_response = self.llm_provider.chat(
                messages,
                temperature=self.settings.rag_temperature,
            )
        except LLMError as exc:
            raise RAGError(
                str(exc),
                status_code=exc.status_code or 502,
            ) from exc
        except Exception as exc:
            logger.exception("Unexpected LLM failure during RAG")
            raise RAGError(
                "Failed to generate grounded answer",
                status_code=502,
            ) from exc

        answer = (llm_response.content or "").strip()
        if not answer:
            raise RAGError(
                "LLM returned an empty grounded answer",
                status_code=502,
            )

        return RagAskResponse(
            question=cleaned,
            answer=answer,
            model=llm_response.model,
            provider=llm_response.provider,
            sources=sources,
            retrieval=retrieval,
        )

    def _build_context(self, hits: list[SemanticSearchResult]) -> str:
        if not self.settings.rag_neighbor_expansion_enabled:
            return self._format_context_plain(hits)

        window = max(0, int(self.settings.rag_neighbor_window))
        max_expanded = max(0, int(self.settings.rag_max_expanded_neighbors))
        if window < 1 or max_expanded < 1:
            return self._format_context_plain(hits)

        planned = plan_neighbors(
            hits,
            window=window,
            max_expanded=max_expanded,
        )
        neighbor_texts: dict[ChunkKey, str] = {}
        if planned:
            keys = [item.key() for item in planned]
            neighbor_texts = dict(self._load_neighbor_texts(keys))

        blocks = build_context_blocks(hits, neighbor_texts, planned)
        return format_context_blocks(blocks)

    def _load_neighbor_texts(
        self, keys: Sequence[ChunkKey]
    ) -> Mapping[ChunkKey, str]:
        if self._neighbor_text_loader is not None:
            return self._neighbor_text_loader(keys)
        return self._load_neighbor_texts_from_db(keys)

    def _load_neighbor_texts_from_db(
        self, keys: Sequence[ChunkKey]
    ) -> dict[ChunkKey, str]:
        unique = list(dict.fromkeys(keys))
        if not unique:
            return {}
        conditions = [
            and_(
                DocumentEmbedding.document_name == document_name,
                DocumentEmbedding.chunk_index == chunk_index,
            )
            for document_name, chunk_index in unique
        ]
        stmt = select(
            DocumentEmbedding.document_name,
            DocumentEmbedding.chunk_index,
            DocumentEmbedding.chunk_text,
        ).where(or_(*conditions))
        try:
            rows = self.db.execute(stmt).all()
        except Exception:
            logger.exception("Neighbor chunk lookup failed; continuing without expansion")
            return {}
        return {
            (str(document_name), int(chunk_index)): str(chunk_text)
            for document_name, chunk_index, chunk_text in rows
        }

    def _build_system_prompt(self, context: str) -> str:
        base = self.settings.rag_system_prompt.strip()
        return (
            f"{base}\n\n"
            "CONTEXT (untrusted retrieved document excerpts):\n"
            f"{context}\n"
        )

    @staticmethod
    def _format_context_plain(hits: list[SemanticSearchResult]) -> str:
        """Legacy formatting used when neighbor expansion is disabled."""
        blocks: list[str] = []
        for i, hit in enumerate(hits, start=1):
            blocks.append(
                f"[{i}] role=retrieved "
                f"source={hit.document_name} "
                f"chunk_index={hit.chunk_index} "
                f"similarity={hit.similarity:.4f}\n"
                f"{hit.chunk_text}"
            )
        return "\n\n".join(blocks)

    @staticmethod
    def _to_source(hit: SemanticSearchResult) -> RagSource:
        return RagSource(
            document_name=hit.document_name,
            chunk_index=hit.chunk_index,
            similarity=hit.similarity,
            distance=hit.distance,
            chunk_text=hit.chunk_text,
        )

    def _resolve_top_k(self, top_k: int | None) -> int:
        limit = self.settings.rag_top_k if top_k is None else top_k
        max_k = self.settings.semantic_search_max_top_k
        if limit < 1 or limit > max_k:
            raise RAGError(
                f"top_k must be between 1 and {max_k}",
                status_code=422,
            )
        return limit

    def _resolve_min_similarity(self, value: float | None) -> float:
        threshold = (
            self.settings.rag_min_similarity if value is None else float(value)
        )
        if threshold < 0.0 or threshold > 1.0:
            raise RAGError(
                "min_similarity must be between 0 and 1",
                status_code=422,
            )
        return threshold

    @staticmethod
    def _validate_question(question: str) -> str:
        if not isinstance(question, str) or question.strip() == "":
            raise RAGError(
                "question must not be empty or whitespace-only",
                status_code=422,
            )
        return question.strip()
