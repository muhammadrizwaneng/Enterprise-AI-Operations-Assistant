"""Tests for RAG same-document neighbor expansion (Phase 4.2 P1 Step 2B)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.core.config import Settings
from app.schemas.search import SemanticSearchResponse, SemanticSearchResult
from app.services.llm.base import LLMResponse
from app.services.neighbor_expansion import (
    ContextRole,
    build_context_blocks,
    format_context_blocks,
    longest_prefix_overlap,
    plan_neighbors,
    strip_prefix_overlap,
)
from app.services.rag import RAGService


def _hit(
    name: str,
    index: int,
    text: str,
    sim: float = 0.6,
) -> SemanticSearchResult:
    return SemanticSearchResult(
        document_name=name,
        chunk_index=index,
        chunk_text=text,
        similarity=sim,
        distance=1.0 - sim,
        metadata=None,
    )


def _settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "rag_top_k": 5,
        "rag_min_similarity": 0.5,
        "rag_temperature": 0.2,
        "semantic_search_max_top_k": 20,
        "rag_neighbor_expansion_enabled": True,
        "rag_neighbor_window": 1,
        "rag_max_expanded_neighbors": 10,
        "rag_system_prompt": "Answer using CONTEXT only.",
    }
    values.update(overrides)
    return Settings(**values)  # type: ignore[arg-type]


def _search(results: list[SemanticSearchResult]) -> SemanticSearchResponse:
    return SemanticSearchResponse(
        query="q",
        top_k=5,
        min_similarity=0.5,
        results=results,
    )


def test_plan_previous_and_next_neighbors():
    hits = [_hit("delivery_policy.md", 4, "overdue section", 0.63)]
    planned = plan_neighbors(hits, window=1, max_expanded=10)
    keys = {(p.document_name, p.chunk_index, p.direction) for p in planned}
    assert ("delivery_policy.md", 3, "previous") in keys
    assert ("delivery_policy.md", 5, "next") in keys


def test_first_chunk_has_no_previous_neighbor():
    hits = [_hit("delivery_policy.md", 0, "intro")]
    planned = plan_neighbors(hits, window=1, max_expanded=10)
    assert all(p.chunk_index != -1 for p in planned)
    assert all(p.direction != "previous" or p.chunk_index >= 0 for p in planned)
    assert [("delivery_policy.md", 1)] == [(p.document_name, p.chunk_index) for p in planned]


def test_last_chunk_next_still_planned_until_lookup_misses():
    """Planner may request index+1; missing DB rows are skipped at load time."""
    hits = [_hit("delivery_policy.md", 6, "damaged")]
    planned = plan_neighbors(hits, window=1, max_expanded=10)
    assert ("delivery_policy.md", 5) in {(p.document_name, p.chunk_index) for p in planned}
    assert ("delivery_policy.md", 7) in {(p.document_name, p.chunk_index) for p in planned}


def test_document_boundary_protection():
    hits = [
        _hit("delivery_policy.md", 6, "end of delivery"),
        _hit("refund_policy.md", 0, "start of refund"),
    ]
    planned = plan_neighbors(hits, window=1, max_expanded=10)
    for item in planned:
        if item.origin_document_name == "delivery_policy.md":
            assert item.document_name == "delivery_policy.md"
        if item.origin_document_name == "refund_policy.md":
            assert item.document_name == "refund_policy.md"
    assert ("refund_policy.md", -1) not in {
        (p.document_name, p.chunk_index) for p in planned
    }


def test_multiple_same_document_hits_dedupe_neighbors():
    hits = [
        _hit("delivery_policy.md", 4, "A"),
        _hit("delivery_policy.md", 5, "B"),
    ]
    planned = plan_neighbors(hits, window=1, max_expanded=10)
    keys = [(p.document_name, p.chunk_index) for p in planned]
    # 4→3,4→5 skipped (already original), 5→4 skipped, 5→6
    assert keys.count(("delivery_policy.md", 5)) == 0
    assert keys.count(("delivery_policy.md", 4)) == 0
    assert ("delivery_policy.md", 3) in keys
    assert ("delivery_policy.md", 6) in keys


def test_duplicate_neighbor_elimination_and_cap():
    hits = [
        _hit("doc.md", 2, "x"),
        _hit("doc.md", 4, "y"),
    ]
    planned = plan_neighbors(hits, window=1, max_expanded=2)
    assert len(planned) == 2
    assert len({p.key() for p in planned}) == 2


def test_overlap_strip_and_no_overlap():
    previous = "AAAA" + ("overlap-text-" * 5)  # shared tail
    shared = previous[-40:]
    current = shared + "UNIQUE_TAIL"
    assert longest_prefix_overlap(previous, current, min_overlap=20, max_overlap=100) == 40
    assert strip_prefix_overlap(previous, current) == "UNIQUE_TAIL"
    assert strip_prefix_overlap("abc", "xyz unique") == "xyz unique"


def test_short_accidental_overlap_not_stripped():
    previous = "hello world ending"
    current = "ending something else"
    # "ending" is only 6 chars < min_overlap 20
    assert strip_prefix_overlap(previous, current, min_overlap=20) == current


def test_build_blocks_marks_neighbors_without_similarity():
    origin = "PREFIX" + ("O" * 30)
    nxt = ("O" * 30) + "COMPLETE_TABLE_ROWS"
    hits = [_hit("delivery_policy.md", 1, origin, 0.58)]
    neighbor_texts = {
        ("delivery_policy.md", 0): "DOC_START",
        ("delivery_policy.md", 2): nxt,
    }
    planned = plan_neighbors(hits, window=1, max_expanded=10)
    blocks = build_context_blocks(hits, neighbor_texts, planned)
    roles = [b.role for b in blocks]
    assert ContextRole.RETRIEVED in roles
    assert ContextRole.NEIGHBOR_PREVIOUS in roles
    assert ContextRole.NEIGHBOR_NEXT in roles
    retrieved = next(b for b in blocks if b.role is ContextRole.RETRIEVED)
    assert retrieved.similarity == pytest.approx(0.58)
    neighbor = next(b for b in blocks if b.role is ContextRole.NEIGHBOR_NEXT)
    assert neighbor.similarity is None
    assert "COMPLETE_TABLE_ROWS" in neighbor.text
    assert neighbor.text.startswith("COMPLETE_TABLE_ROWS") or "COMPLETE_TABLE_ROWS" in neighbor.text


def test_no_neighbor_fallback_when_lookup_empty():
    hits = [_hit("delivery_policy.md", 1, "only hit", 0.5)]
    planned = plan_neighbors(hits, window=1, max_expanded=10)
    blocks = build_context_blocks(hits, {}, planned)
    assert len(blocks) == 1
    assert blocks[0].role is ContextRole.RETRIEVED


def test_empty_hits_plan_empty():
    assert plan_neighbors([], window=1, max_expanded=10) == []


def test_q1_expansion_includes_delivery_chunk_2():
    """When search returns #1, expansion should pull #2 (shipping table)."""
    chunk1 = "processing times and truncated Standard Ground | Defaul"
    chunk2 = "Standard Ground | 3–7 business days | Default domestic | Expedited"
    hits = [_hit("delivery_policy.md", 1, chunk1, 0.5843)]
    store = {
        ("delivery_policy.md", 0): "overview",
        ("delivery_policy.md", 2): chunk2,
    }
    planned = plan_neighbors(hits, window=1, max_expanded=10)
    blocks = build_context_blocks(hits, store, planned)
    rendered = format_context_blocks(blocks)
    assert "chunk_index=2" in rendered
    assert "role=neighbor_next" in rendered
    assert "3–7 business days" in rendered
    assert "similarity=0.5843" in rendered
    assert "not an independent semantic match" in rendered


def test_q3_expansion_includes_delivery_chunk_5():
    """When search returns #4, expansion should pull #5 (7 calendar days)."""
    chunk4 = "Overdue Orders definition and contact the carrier"
    chunk5 = "Offer a replacement or refund if confirmed lost after 7 calendar days."
    hits = [_hit("delivery_policy.md", 4, chunk4, 0.63)]
    store = {
        ("delivery_policy.md", 3): "status defs",
        ("delivery_policy.md", 5): chunk5,
    }
    planned = plan_neighbors(hits, window=1, max_expanded=10)
    blocks = build_context_blocks(hits, store, planned)
    rendered = format_context_blocks(blocks)
    assert "chunk_index=5" in rendered
    assert "7 calendar days" in rendered
    assert "role=neighbor_next" in rendered


def test_rag_sources_preserve_original_ranking_only():
    hits = [
        _hit("delivery_policy.md", 1, "chunk1", 0.58),
        _hit("delivery_policy.md", 4, "chunk4", 0.55),
    ]
    search = MagicMock()
    search.search.return_value = _search(hits)
    llm = MagicMock()
    llm.chat.return_value = LLMResponse(content="ok", model="m", provider="p")

    def loader(keys):
        return {
            ("delivery_policy.md", 0): "prev0",
            ("delivery_policy.md", 2): "next2 table",
            ("delivery_policy.md", 3): "prev3",
            ("delivery_policy.md", 5): "next5 seven days",
        }

    service = RAGService(
        MagicMock(),
        search_service=search,
        llm_provider=llm,
        settings=_settings(),
        neighbor_text_loader=loader,
    )
    response = service.ask("How long does delivery take?")
    assert len(response.sources) == 2
    assert response.sources[0].chunk_index == 1
    assert response.sources[0].similarity == pytest.approx(0.58)
    assert response.sources[1].chunk_index == 4
    assert response.sources[1].similarity == pytest.approx(0.55)
    system = llm.chat.call_args.args[0][0].content
    assert "next2 table" in system
    assert "next5 seven days" in system
    assert "role=neighbor_next" in system
    assert "role=retrieved" in system


def test_context_size_limit_caps_expanded_neighbors():
    hits = [_hit(f"doc{i}.md", 1, f"text{i}") for i in range(5)]
    planned = plan_neighbors(hits, window=1, max_expanded=3)
    assert len(planned) == 3


def test_empty_retrieval_skips_expansion_and_llm():
    search = MagicMock()
    search.search.return_value = _search([])
    llm = MagicMock()
    loader = MagicMock(return_value={})
    service = RAGService(
        MagicMock(),
        search_service=search,
        llm_provider=llm,
        settings=_settings(),
        neighbor_text_loader=loader,
    )
    response = service.ask("nothing")
    assert response.sources == []
    llm.chat.assert_not_called()
    loader.assert_not_called()


def test_expansion_disabled_uses_plain_context():
    search = MagicMock()
    search.search.return_value = _search([_hit("delivery_policy.md", 1, "only")])
    llm = MagicMock()
    llm.chat.return_value = LLMResponse(content="ok", model="m", provider="p")
    loader = MagicMock(return_value={("delivery_policy.md", 2): "SHOULD_NOT_LOAD"})

    service = RAGService(
        MagicMock(),
        search_service=search,
        llm_provider=llm,
        settings=_settings(rag_neighbor_expansion_enabled=False),
        neighbor_text_loader=loader,
    )
    service.ask("q")
    loader.assert_not_called()
    system = llm.chat.call_args.args[0][0].content
    assert "SHOULD_NOT_LOAD" not in system
    assert "only" in system


def test_leave_and_support_expansion_stays_same_document():
    """Irrelevant cross-doc bleed must not occur via expansion."""
    hits = [
        _hit("employee_handbook.md", 5, "PTO 7 days", 0.64),
        _hit("customer_support_guidelines.md", 0, "Ticket Categories", 0.66),
    ]
    planned = plan_neighbors(hits, window=1, max_expanded=10)
    for item in planned:
        assert item.document_name == item.origin_document_name
        assert item.document_name in {
            "employee_handbook.md",
            "customer_support_guidelines.md",
        }
        assert item.document_name != "privacy_policy.md"
