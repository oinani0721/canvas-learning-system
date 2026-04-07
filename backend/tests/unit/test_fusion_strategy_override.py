"""State-priority tests for fusion_strategy / reranking_strategy.

Validates Phase 2 of fix-rag-faithfulness-and-add-crag-quality-loop:
the per-request override contract.

`fuse_results` and `rerank_results` must read state.get(...) BEFORE falling
back to runtime config. Without this, RAGService.query()'s per-request
override (set in rag_service.py:290-292) is silently ignored.

Test strategy: mock the heavy fusion/rerank backends so the call is fast,
and assert which backend was invoked based on the resolved strategy.
"""

from types import SimpleNamespace
from unittest import mock as _mock

import pytest

# Note: nodes/__init__.py re-exports public names from nodes.py via
# `importlib.util.spec_from_file_location` under the alias _nodes_impl.
# `from ... import *` skips underscore-prefixed names, so _safe_get_config
# (and the _fuse_* / _rerank_* helpers used in mocks) must be addressed
# through the _nodes_impl alias.
from agentic_rag._nodes_impl import _safe_get_config, fuse_results, rerank_results
from agentic_rag.state import create_initial_state


def _make_runtime(context: dict | None) -> SimpleNamespace:
    """Mimic LangGraph Runtime[CanvasRAGConfig] with a `.context` attr."""
    return SimpleNamespace(context=context)


# ───────────────────────────────────────────────────────────────────────────────
# fusion_strategy: state beats runtime
# ───────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_state_fusion_strategy_beats_runtime():
    """When state has fusion_strategy='weighted', the runtime 'rrf' must lose."""
    state = create_initial_state(fusion_strategy="weighted")
    runtime = _make_runtime({"fusion_strategy": "rrf"})

    with _mock.patch(
        "agentic_rag._nodes_impl._fuse_weighted_multi_source", return_value=[]
    ) as mock_weighted:
        with _mock.patch(
            "agentic_rag._nodes_impl._fuse_rrf_multi_source", return_value=[]
        ) as mock_rrf:
            with _mock.patch(
                "agentic_rag._nodes_impl._fuse_layered_rrf", return_value=[]
            ) as mock_layered:
                with _mock.patch(
                    "agentic_rag._nodes_impl._fuse_cascade_multi_source",
                    return_value=[],
                ) as mock_cascade:
                    await fuse_results(state, runtime)

    assert mock_weighted.called, "weighted fusion (state override) must run"
    assert not mock_rrf.called, "rrf fusion (runtime config) must NOT run"
    assert not mock_layered.called
    assert not mock_cascade.called


@pytest.mark.asyncio
async def test_runtime_fusion_strategy_used_when_state_empty():
    """When state has fusion_strategy=None, runtime config wins."""
    state = create_initial_state()
    state["fusion_strategy"] = None  # explicitly None
    runtime = _make_runtime({"fusion_strategy": "rrf"})

    with _mock.patch(
        "agentic_rag._nodes_impl._fuse_rrf_multi_source", return_value=[]
    ) as mock_rrf:
        with _mock.patch(
            "agentic_rag._nodes_impl._fuse_layered_rrf", return_value=[]
        ) as mock_layered:
            with _mock.patch(
                "agentic_rag._nodes_impl._fuse_weighted_multi_source", return_value=[]
            ) as mock_weighted:
                await fuse_results(state, runtime)

    assert mock_rrf.called, "runtime rrf fusion must run"
    assert not mock_layered.called
    assert not mock_weighted.called


@pytest.mark.asyncio
async def test_default_fusion_strategy_when_neither_set():
    """When BOTH state and runtime are silent, fall back to layered_rrf default."""
    state = create_initial_state()
    state["fusion_strategy"] = None
    runtime = _make_runtime({})  # no fusion_strategy key

    with _mock.patch(
        "agentic_rag._nodes_impl._fuse_layered_rrf", return_value=[]
    ) as mock_layered:
        with _mock.patch(
            "agentic_rag._nodes_impl._fuse_rrf_multi_source", return_value=[]
        ) as mock_rrf:
            await fuse_results(state, runtime)

    assert mock_layered.called, "default layered_rrf must run"
    assert not mock_rrf.called


# ───────────────────────────────────────────────────────────────────────────────
# reranking_strategy: state beats runtime
# ───────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_state_reranking_strategy_beats_runtime():
    """When state has reranking_strategy='cohere', runtime 'local' must lose."""
    state = create_initial_state(reranking_strategy="cohere")
    state["fused_results"] = [
        {"doc_id": "d1", "content": "test", "score": 1.0, "metadata": {}}
    ]
    runtime = _make_runtime({"reranking_strategy": "local"})

    async def _fake_cohere(results, _state):
        return results

    async def _fake_local(results, _state, _runtime):
        return results

    with _mock.patch(
        "agentic_rag._nodes_impl._rerank_cohere", side_effect=_fake_cohere
    ) as mock_cohere:
        with _mock.patch(
            "agentic_rag._nodes_impl._rerank_local", side_effect=_fake_local
        ) as mock_local:
            await rerank_results(state, runtime)

    assert mock_cohere.called, "cohere rerank (state override) must run"
    assert not mock_local.called, "local rerank (runtime config) must NOT run"


@pytest.mark.asyncio
async def test_runtime_reranking_strategy_used_when_state_empty():
    """When state has reranking_strategy=None, runtime config wins."""
    state = create_initial_state()
    state["reranking_strategy"] = None
    state["fused_results"] = [
        {"doc_id": "d1", "content": "test", "score": 1.0, "metadata": {}}
    ]
    runtime = _make_runtime({"reranking_strategy": "local"})

    async def _fake_local(results, _state, _runtime):
        return results

    with _mock.patch(
        "agentic_rag._nodes_impl._rerank_local", side_effect=_fake_local
    ) as mock_local:
        with _mock.patch(
            "agentic_rag._nodes_impl._rerank_cohere", side_effect=lambda r, s: r
        ) as mock_cohere:
            await rerank_results(state, runtime)

    assert mock_local.called
    assert not mock_cohere.called


# ───────────────────────────────────────────────────────────────────────────────
# _safe_get_config defensive paths (regression guard)
# ───────────────────────────────────────────────────────────────────────────────


def test_safe_get_config_returns_default_when_runtime_none():
    assert _safe_get_config(None, "fusion_strategy", "layered_rrf") == "layered_rrf"


def test_safe_get_config_returns_default_when_context_none():
    runtime = SimpleNamespace(context=None)
    assert _safe_get_config(runtime, "fusion_strategy", "layered_rrf") == "layered_rrf"


def test_safe_get_config_returns_value_from_context():
    runtime = SimpleNamespace(context={"fusion_strategy": "rrf"})
    assert _safe_get_config(runtime, "fusion_strategy", "layered_rrf") == "rrf"
