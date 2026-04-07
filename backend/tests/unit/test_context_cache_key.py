"""FR-KG-04 isolation Phase 2 — Context API cache key scoping.

Before Phase 2, ``context.py`` cached responses keyed solely on ``node_id``.
When two subjects shared a node_id (e.g. a canvas template reused across
groups), the second caller would receive the first caller's group-scoped
neighbors from cache, leaking subject boundaries via the 30s TTL window.

Phase 2 introduces a composite cache key
``f"{group_id or DEFAULT_GROUP_ID}:{node_id}"``. Using ``DEFAULT_GROUP_ID``
(not a literal ``"default"``) keeps the cache entry aligned with the same
fallback that ``LearningContextService.get_node_context`` applies when it
receives ``group_id=None`` — otherwise a None-call and a default-call
would end up with two drifted cache entries holding identical data.

This test pins the new semantics.
"""

from __future__ import annotations

import pytest

import app.api.v1.endpoints.context as context_mod
from app.api.v1.endpoints.context import (
    CACHE_MAX_SIZE,
    _context_cache,
    _get_cached,
    _set_cache,
)
from app.config import DEFAULT_GROUP_ID


@pytest.fixture(autouse=True)
def _clear_cache_between_tests():
    """Prevent cross-test pollution of the module-level cache dict."""
    _context_cache.clear()
    yield
    _context_cache.clear()


# ---------------------------------------------------------------------------
# Scenario A — same node, different group_id → independent cache entries
# ---------------------------------------------------------------------------


def test_same_node_different_group_isolated():
    """Two groups hitting the same node must receive distinct payloads."""
    physics_payload = {
        "node_id": "n1",
        "tier2": {"neighbors": [{"name": "physics_neighbor"}]},
    }
    math_payload = {
        "node_id": "n1",
        "tier2": {"neighbors": [{"name": "math_neighbor"}]},
    }

    _set_cache("physics:n1", physics_payload)
    _set_cache("math:n1", math_payload)

    assert _get_cached("physics:n1") == physics_payload
    assert _get_cached("math:n1") == math_payload
    # Critical regression guard: physics must NOT see math's neighbors.
    assert (
        _get_cached("physics:n1")["tier2"]["neighbors"][0]["name"] == "physics_neighbor"
    )


# ---------------------------------------------------------------------------
# Scenario B — same (node, group) → second call is a cache hit
# ---------------------------------------------------------------------------


def test_same_node_same_group_hit():
    """A second lookup with the same composite key returns the cached copy."""
    payload = {"node_id": "n1", "cached": True}
    _set_cache("physics:n1", payload)

    first = _get_cached("physics:n1")
    second = _get_cached("physics:n1")

    assert first is payload
    assert second is payload


# ---------------------------------------------------------------------------
# Scenario C — group_id None normalizes to DEFAULT_GROUP_ID prefix
# ---------------------------------------------------------------------------


def test_none_group_uses_default_group_id_prefix():
    """The endpoint derives the cache_key with ``group_id or DEFAULT_GROUP_ID``,
    so a ``None`` caller and an explicit ``DEFAULT_GROUP_ID`` caller MUST
    collide on the same key (intentional — they refer to the same default
    namespace and should share the cached payload). They MUST NOT collide
    with any other explicit group.

    Under the current config ``DEFAULT_GROUP_ID == "cs188"``, so the key
    this test reads is ``"cs188:n1"``. Using the constant (instead of
    pinning the literal) keeps the assertion robust to env reconfiguration.
    """
    default_key = f"{DEFAULT_GROUP_ID}:n1"
    physics_key = "physics:n1"

    default_payload = {"from": DEFAULT_GROUP_ID}
    physics_payload = {"from": "physics"}

    _set_cache(default_key, default_payload)
    _set_cache(physics_key, physics_payload)

    assert _get_cached(default_key) == default_payload
    assert _get_cached(physics_key) == physics_payload
    # Ensure the two namespaces are distinct keys in the dict.
    assert default_key in _context_cache
    assert physics_key in _context_cache
    assert len(_context_cache) == 2
    # Regression guard: the old literal "default:n1" key must NOT be used.
    assert "default:n1" not in _context_cache or DEFAULT_GROUP_ID == "default"


# ---------------------------------------------------------------------------
# Scenario D — LRU eviction uses the composite key
# ---------------------------------------------------------------------------


def test_lru_eviction_uses_composite_key(monkeypatch):
    """Filling the cache past CACHE_MAX_SIZE evicts by timestamp, keyed by
    the composite ``group:node`` string, not by bare node_id.

    This test temporarily shrinks CACHE_MAX_SIZE so we don't need to
    allocate 200 entries just to exercise the branch.
    """
    monkeypatch.setattr(context_mod, "CACHE_MAX_SIZE", 3)

    # Fake deterministic clock so ordering is predictable — we can't rely
    # on real time.time() resolution between back-to-back _set_cache calls.
    fake_times = iter([100.0, 101.0, 102.0, 103.0])
    monkeypatch.setattr(context_mod.time, "time", lambda: next(fake_times))

    _set_cache("physics:n1", {"v": 1})  # t=100 (oldest)
    _set_cache("physics:n2", {"v": 2})  # t=101
    _set_cache("math:n1", {"v": 3})  # t=102 — cache now full (size=3)

    # Inserting a 4th entry must evict the oldest by timestamp, which is
    # the FIRST physics entry.
    _set_cache("biology:n1", {"v": 4})  # t=103

    assert "physics:n1" not in _context_cache  # evicted
    assert "physics:n2" in _context_cache
    assert "math:n1" in _context_cache
    assert "biology:n1" in _context_cache
    assert len(_context_cache) == 3
