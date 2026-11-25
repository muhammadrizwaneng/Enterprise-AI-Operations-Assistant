"""Tests for held-out dataset integrity and leakage barriers (Step 9)."""

from __future__ import annotations

import ast
import hashlib
import inspect
from pathlib import Path

import pytest

from experiments.retrieval_eval.dataset import EVAL_QUERIES, get_eval_queries
from experiments.retrieval_eval.heldout_answer_key import ANSWER_KEYS, get_answer_key
from experiments.retrieval_eval.heldout_annotations import annotation_rows, by_category
from experiments.retrieval_eval.heldout_dataset import (
    HELDOUT_QUERIES,
    get_heldout_eval_queries,
    get_heldout_queries,
)
from experiments.retrieval_eval.run_heldout_eval import EXPECTED_GUARD_SHA256


ROOT = Path(__file__).resolve().parents[2]
GUARD = ROOT / "experiments" / "retrieval_eval" / "evidence_guard.py"
STEP8 = (
    ROOT
    / "experiments"
    / "retrieval_eval"
    / "step8_guarded_hybrid"
    / "guarded_hybrid_results.json"
)


def test_exactly_twenty_heldout_questions():
    qs = get_heldout_queries()
    assert len(qs) == 20
    assert [q.query_id for q in qs] == [f"Q{i}" for i in range(8, 28)]


def test_unique_question_ids_and_text():
    qs = get_heldout_queries()
    ids = [q.query_id for q in qs]
    texts = [q.question for q in qs]
    assert len(set(ids)) == 20
    assert len(set(texts)) == 20


def test_no_overlap_with_dev_questions():
    dev_texts = {q.question.lower() for q in get_eval_queries()}
    for h in get_heldout_queries():
        assert h.question.lower() not in dev_texts
        assert h.query_id not in {q.query_id for q in EVAL_QUERIES}


def test_primary_chunk_refs_look_valid():
    allowed_docs = {
        "delivery_policy.md",
        "refund_policy.md",
        "customer_support_guidelines.md",
        "employee_handbook.md",
        "privacy_policy.md",
        "product_documentation.md",
    }
    for h in get_heldout_queries():
        assert h.query.primary_relevant
        for c in h.query.primary_relevant:
            assert c.document_name in allowed_docs
            assert c.chunk_index >= 0


def test_answer_keys_cover_all_heldout_ids():
    for h in get_heldout_queries():
        key = get_answer_key(h.query_id)
        assert key.expected_facts
        assert key.summary


def test_annotations_count():
    rows = annotation_rows()
    assert len(rows) == 20
    assert by_category()


def test_eval_query_view_has_no_answer_key_fields():
    for q in get_heldout_eval_queries():
        assert not hasattr(q, "expected_facts")
        assert q.question
        assert q.primary_relevant


def test_guard_source_does_not_import_heldout_answer_key():
    src = GUARD.read_text(encoding="utf-8")
    assert "heldout_answer_key" not in src
    assert "ANSWER_KEYS" not in src
    assert "primary_relevant" not in src
    assert "Q8" not in src and "Q27" not in src


def test_guard_hash_matches_frozen_step8_implementation():
    digest = hashlib.sha256(GUARD.read_bytes()).hexdigest()
    assert digest == EXPECTED_GUARD_SHA256


def test_step8_results_untouched_exist():
    assert STEP8.is_file()
    # Ensure runner constant still points at existing artifact path name.
    assert "step8_guarded_hybrid" in str(STEP8)


def test_heldout_runner_does_not_pass_answer_key_to_guard():
    runner = (
        ROOT / "experiments" / "retrieval_eval" / "run_heldout_eval.py"
    ).read_text(encoding="utf-8")
    # Runtime path imports guard + dataset, scoring uses answer key separately.
    assert "assess_evidence_sufficiency(query.question, hits)" in runner
    assert "score_heldout_answer" in runner
    # Guard call must not include answer key / primary labels as args.
    assert "assess_evidence_sufficiency(query.question, hits, " not in runner


def test_configs_and_seeds_constants():
    from experiments.retrieval_eval import run_heldout_eval as rh

    assert rh.CONFIG_ORDER == (
        "OFF",
        "BLIND",
        "HYBRID_CAP2",
        "GUARDED_HYBRID_CAP2",
    )
    assert rh.DEFAULT_SEEDS == (101, 202, 303, 404, 505)
