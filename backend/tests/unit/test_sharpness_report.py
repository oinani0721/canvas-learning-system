"""Observability tests for sharpness_report from rerank_results.

Phase 3 of fix-rag-faithfulness-and-add-crag-quality-loop:
rerank_results must publish sharpness_report with top_scores / max_gap /
max_gap_idx / is_flat / cut so downstream callers can tell whether
adaptive-k truncation found a real score cliff or not.
"""

from types import SimpleNamespace
from unittest import mock as _mock

import pytest

from agentic_rag._nodes_impl import rerank_results
from agentic_rag.state import create_initial_state


def _make_runtime(context: dict | None) -> SimpleNamespace:
    return SimpleNamespace(context=context)


def _mk_result(doc_id: str, score: float):
    return {
        "doc_id": doc_id,
        "content": f"content-{doc_id}",
        "score": score,
        "metadata": {},
    }


# ───────────────────────────────────────────────────────────────────────────────
# is_flat detection
# ───────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_sharpness_report_is_flat_when_scores_cluster():
    """Nearly identical scores -> is_flat=True, cut=max_k."""
    # All scores within epsilon=0.01 of each other -> flat
    state = create_initial_state(reranking_strategy="local")
    state["fused_results"] = [_mk_result(f"d{i}", 0.5 + i * 0.001) for i in range(20)][
        ::-1
    ]  # descending
    runtime = _make_runtime(
        {"adaptive_k_buffer": 5, "adaptive_k_min": 3, "adaptive_k_max": 15}
    )

    async def _fake_local(results, _state, _runtime):
        return results

    with _mock.patch("agentic_rag._nodes_impl._rerank_local", side_effect=_fake_local):
        result = await rerank_results(state, runtime)

    report = result["sharpness_report"]
    assert report["is_flat"] is True
    assert report["pre_count"] == 20
    assert report["cut"] == 15  # adaptive_k_max when flat
    assert len(report["top_scores"]) == 5


@pytest.mark.asyncio
async def test_sharpness_report_detects_cliff():
    """A real cliff -> is_flat=False and max_gap_idx reflects the drop."""
    state = create_initial_state(reranking_strategy="local")
    # 3 high scores then a cliff then 5 low scores
    high_scores = [0.95, 0.90, 0.88]
    low_scores = [0.20, 0.18, 0.15, 0.10, 0.05]
    state["fused_results"] = [
        _mk_result(f"h{i}", s) for i, s in enumerate(high_scores)
    ] + [_mk_result(f"l{i}", s) for i, s in enumerate(low_scores)]
    runtime = _make_runtime(
        {"adaptive_k_buffer": 2, "adaptive_k_min": 3, "adaptive_k_max": 15}
    )

    async def _fake_local(results, _state, _runtime):
        return results

    with _mock.patch("agentic_rag._nodes_impl._rerank_local", side_effect=_fake_local):
        result = await rerank_results(state, runtime)

    report = result["sharpness_report"]
    assert report["is_flat"] is False
    # cliff is between idx 2 and idx 3 (0.88 -> 0.20, gap=0.68)
    assert report["max_gap_idx"] == 2
    assert report["max_gap"] == pytest.approx(0.88 - 0.20, rel=1e-4)
    # cut = clamp(max_gap_idx+1 + buffer, min_k, max_k) = clamp(5, 3, 15) = 5
    assert report["cut"] == 5


@pytest.mark.asyncio
async def test_sharpness_report_cut_reflects_adaptive_k_truncation():
    """sharpness_report.cut must equal len(reranked_results) after truncation."""
    state = create_initial_state(reranking_strategy="local")
    state["fused_results"] = [_mk_result(f"d{i}", 1.0 - i * 0.05) for i in range(25)]
    runtime = _make_runtime({})

    async def _fake_local(results, _state, _runtime):
        return results

    with _mock.patch("agentic_rag._nodes_impl._rerank_local", side_effect=_fake_local):
        result = await rerank_results(state, runtime)

    report = result["sharpness_report"]
    assert report["cut"] == len(result["reranked_results"])


@pytest.mark.asyncio
async def test_sharpness_report_top_scores_limited_to_five():
    """top_scores field must be top-5 only (not more)."""
    state = create_initial_state(reranking_strategy="local")
    state["fused_results"] = [_mk_result(f"d{i}", 1.0 - i * 0.1) for i in range(10)]
    runtime = _make_runtime({})

    async def _fake_local(results, _state, _runtime):
        return results

    with _mock.patch("agentic_rag._nodes_impl._rerank_local", side_effect=_fake_local):
        result = await rerank_results(state, runtime)

    assert len(result["sharpness_report"]["top_scores"]) == 5


@pytest.mark.asyncio
async def test_sharpness_report_empty_input():
    """Empty fused_results -> empty top_scores, max_gap=0, is_flat=True."""
    state = create_initial_state(reranking_strategy="local")
    state["fused_results"] = []
    runtime = _make_runtime({})

    async def _fake_local(results, _state, _runtime):
        return results

    with _mock.patch("agentic_rag._nodes_impl._rerank_local", side_effect=_fake_local):
        result = await rerank_results(state, runtime)

    report = result["sharpness_report"]
    assert report["top_scores"] == []
    assert report["max_gap"] == 0.0
    assert report["max_gap_idx"] is None
    assert report["is_flat"] is True
    assert report["pre_count"] == 0


@pytest.mark.asyncio
async def test_sharpness_report_single_result():
    """Single fused_result -> max_gap=0 (no gaps to compute)."""
    state = create_initial_state(reranking_strategy="local")
    state["fused_results"] = [_mk_result("only", 0.95)]
    runtime = _make_runtime({})

    async def _fake_local(results, _state, _runtime):
        return results

    with _mock.patch("agentic_rag._nodes_impl._rerank_local", side_effect=_fake_local):
        result = await rerank_results(state, runtime)

    report = result["sharpness_report"]
    assert report["top_scores"] == [0.95]
    assert report["max_gap"] == 0.0
    assert report["max_gap_idx"] is None
    assert report["is_flat"] is True
    assert report["pre_count"] == 1
