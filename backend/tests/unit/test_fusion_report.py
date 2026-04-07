"""Observability tests for fusion_report + support_sources metadata.

Phase 3 of fix-rag-faithfulness-and-add-crag-quality-loop:
fuse_results must publish a structured fusion_report to state, and every
fused result must carry support_sources / support_count metadata so
downstream observers can distinguish "low recall" from "bad fusion"
from "no multi-source consensus".
"""

from types import SimpleNamespace
from unittest import mock as _mock

import pytest

from agentic_rag._nodes_impl import (
    _fuse_layered_rrf,
    _fuse_rrf_multi_source,
    fuse_results,
)
from agentic_rag.state import create_initial_state


def _make_runtime(context: dict | None) -> SimpleNamespace:
    return SimpleNamespace(context=context)


def _mk_result(doc_id: str, content: str, score: float = 1.0, **meta):
    return {
        "doc_id": doc_id,
        "content": content,
        "score": score,
        "metadata": meta,
    }


# ───────────────────────────────────────────────────────────────────────────────
# _fuse_rrf_multi_source: support_sources metadata
# ───────────────────────────────────────────────────────────────────────────────


def test_rrf_fused_results_have_support_sources_metadata():
    """Single-source result should carry support_sources=[source] + count=1."""
    all_sources = {
        "graphiti": [_mk_result("g1", "alpha", file_path="notes/a.md")],
        "lancedb": [],
        "multimodal": [],
        "cross_canvas": [],
        "vault_notes": [],
    }

    fused = _fuse_rrf_multi_source(all_sources, k=60)

    assert len(fused) == 1
    assert fused[0]["metadata"]["support_sources"] == ["graphiti"]
    assert fused[0]["metadata"]["support_count"] == 1


def test_rrf_multi_source_result_unions_support_sources_via_dedup():
    """Same content from graphiti + lancedb must merge into one result
    with support_sources=['graphiti', 'lancedb']."""
    all_sources = {
        "graphiti": [_mk_result("g1", "alpha", file_path="notes/a.md")],
        "lancedb": [_mk_result("l1", "alpha", file_path="notes/a.md")],
        "multimodal": [],
        "cross_canvas": [],
        "vault_notes": [],
    }

    fused = _fuse_rrf_multi_source(all_sources, k=60)

    # Dedup collapses them into a single row (first-seen doc_id keeps)
    assert len(fused) == 1
    assert fused[0]["metadata"]["support_sources"] == ["graphiti", "lancedb"]
    assert fused[0]["metadata"]["support_count"] == 2


def test_rrf_three_channel_consensus():
    """Three channels contributing same content -> support_count=3."""
    all_sources = {
        "graphiti": [_mk_result("g1", "beta", file_path="b.md")],
        "lancedb": [_mk_result("l1", "beta", file_path="b.md")],
        "multimodal": [],
        "cross_canvas": [_mk_result("c1", "beta", file_path="b.md")],
        "vault_notes": [],
    }

    fused = _fuse_rrf_multi_source(all_sources, k=60)

    assert len(fused) == 1
    assert fused[0]["metadata"]["support_count"] == 3
    assert set(fused[0]["metadata"]["support_sources"]) == {
        "graphiti",
        "lancedb",
        "cross_canvas",
    }


# ───────────────────────────────────────────────────────────────────────────────
# _fuse_layered_rrf: cross-group support_sources union
# ───────────────────────────────────────────────────────────────────────────────


def test_layered_rrf_unions_support_across_groups():
    """Same content in different fusion groups must union support_sources."""
    all_sources = {
        "graphiti": [_mk_result("g1", "gamma", file_path="c.md")],
        "lancedb": [_mk_result("l1", "gamma", file_path="c.md")],
        "multimodal": [],
        "cross_canvas": [],
        "vault_notes": [],
    }
    fusion_groups = {
        "Dense": ["lancedb", "multimodal"],
        "Graph": ["graphiti", "cross_canvas"],
        "Personal": ["vault_notes"],
    }

    fused = _fuse_layered_rrf(all_sources, fusion_groups, k=60)

    # After cross-group dedup, the single content should have its support_sources
    # unioned from both the Dense group (lancedb) and Graph group (graphiti).
    assert len(fused) == 1
    support_sources = fused[0]["metadata"]["support_sources"]
    assert set(support_sources) == {"graphiti", "lancedb"}
    assert fused[0]["metadata"]["support_count"] == 2


# ───────────────────────────────────────────────────────────────────────────────
# fuse_results node: fusion_report state field
# ───────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_fusion_report_exposes_channel_status_and_coverage():
    """fuse_results must emit fusion_report with full channel health detail."""
    state = create_initial_state(fusion_strategy="rrf")
    state["graphiti_results"] = [_mk_result("g1", "A", file_path="a.md")]
    state["lancedb_results"] = [_mk_result("l1", "B", file_path="b.md")]
    state["multimodal_results"] = []
    state["cross_canvas_results"] = []
    state["vault_notes_results"] = []

    runtime = _make_runtime({})
    result = await fuse_results(state, runtime)

    assert "fusion_report" in result
    report = result["fusion_report"]
    assert report["channel_status"] == {
        "graphiti": 1,
        "lancedb": 1,
        "multimodal": 0,
        "cross_canvas": 0,
        "vault_notes": 0,
    }
    assert report["active_channels"] == 2
    assert report["coverage_score"] == pytest.approx(0.4)  # 2/5
    assert report["total_results"] == 2
    assert report["fusion_strategy"] == "rrf"
    assert report["rrf_k"] == 60


@pytest.mark.asyncio
async def test_fusion_report_all_channels_active():
    """coverage_score=1.0 when all 5 channels return results."""
    state = create_initial_state(fusion_strategy="rrf")
    for channel, doc_id, fp in [
        ("graphiti_results", "g1", "g.md"),
        ("lancedb_results", "l1", "l.md"),
        ("multimodal_results", "m1", "m.md"),
        ("cross_canvas_results", "c1", "c.md"),
        ("vault_notes_results", "v1", "v.md"),
    ]:
        state[channel] = [_mk_result(doc_id, doc_id, file_path=fp)]

    runtime = _make_runtime({})
    result = await fuse_results(state, runtime)

    assert result["fusion_report"]["active_channels"] == 5
    assert result["fusion_report"]["coverage_score"] == 1.0
    assert result["fusion_report"]["total_results"] == 5


@pytest.mark.asyncio
async def test_fusion_report_avg_support_topk_for_multi_source_overlap():
    """avg_support_topk reflects multi-source consensus in fused top-k."""
    state = create_initial_state(fusion_strategy="rrf")
    # Same content in 3 channels -> one result with support_count=3
    state["graphiti_results"] = [_mk_result("g1", "hit", file_path="hit.md")]
    state["lancedb_results"] = [_mk_result("l1", "hit", file_path="hit.md")]
    state["multimodal_results"] = []
    state["cross_canvas_results"] = [_mk_result("c1", "hit", file_path="hit.md")]
    state["vault_notes_results"] = []

    runtime = _make_runtime({})
    result = await fuse_results(state, runtime)

    # After dedup only 1 fused result with support_count=3
    assert result["fusion_report"]["avg_support_topk"] == 3.0
    assert result["fusion_report"]["support_ge_2_ratio"] == 1.0


@pytest.mark.asyncio
async def test_fusion_report_zero_support_for_single_source_topk():
    """When top-k is all single-source, support_ge_2_ratio should be 0."""
    state = create_initial_state(fusion_strategy="rrf")
    state["graphiti_results"] = [
        _mk_result(f"g{i}", f"content{i}", file_path=f"{i}.md") for i in range(3)
    ]
    state["lancedb_results"] = []
    state["multimodal_results"] = []
    state["cross_canvas_results"] = []
    state["vault_notes_results"] = []

    runtime = _make_runtime({})
    result = await fuse_results(state, runtime)

    assert result["fusion_report"]["avg_support_topk"] == 1.0
    assert result["fusion_report"]["support_ge_2_ratio"] == 0.0


@pytest.mark.asyncio
async def test_fusion_report_empty_inputs():
    """All-empty inputs produce zeroed coverage + empty top-k."""
    state = create_initial_state(fusion_strategy="rrf")
    # all retrieval channels already empty by default
    runtime = _make_runtime({})

    result = await fuse_results(state, runtime)

    report = result["fusion_report"]
    assert report["active_channels"] == 0
    assert report["coverage_score"] == 0.0
    assert report["total_results"] == 0
    assert report["avg_support_topk"] == 0.0
    assert report["support_ge_2_ratio"] == 0.0
    assert report["topk_size"] == 0
