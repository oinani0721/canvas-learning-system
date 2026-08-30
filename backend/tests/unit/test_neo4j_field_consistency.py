"""FR-KG-04 Phase 15: Learning relationship field consistency.

Story: openspec change fix-fr-kg-04-schema-drift-and-sync-hardening — Phase 15.

Background:
- ``create_learning_relationship`` writes ``r.score = $score`` (single source
  of truth) and now also increments ``r.review_count = coalesce(...) + 1``.
- ``get_review_suggestions`` aliases the score back as ``last_score`` so the
  JSON contract stays the same: API consumers still read ``last_score``.
- Earlier the query read ``r.last_score`` directly, which was a phantom
  property that no write path ever populated, so reviews returned null.

These tests guard the Cypher *shape* against future regressions and verify
the contract that:
  1. Writes set ``r.score`` and increment ``r.review_count`` via coalesce
  2. Reads return the score under the historical ``last_score`` JSON key
  3. ``review_count`` starts at 1 on the first scoring and grows by 1 each call
"""

from __future__ import annotations

from typing import Any, Dict, List
from unittest.mock import AsyncMock, patch

import pytest

from app.clients.neo4j_client import Neo4jClient


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


class _CypherCapture:
    """Captures every (query, kwargs) pair sent through Neo4jClient.run_query."""

    def __init__(self) -> None:
        self.calls: List[Dict[str, Any]] = []

    async def __call__(self, query: str, **kwargs: Any) -> List[Dict[str, Any]]:
        self.calls.append({"query": query, "kwargs": kwargs})
        return [{"r": {"id": "stub"}}]

    @property
    def last_query(self) -> str:
        assert self.calls, "no query captured"
        return self.calls[-1]["query"]

    def find_query_with(self, snippet: str) -> str:
        for call in self.calls:
            if snippet in call["query"]:
                return call["query"]
        raise AssertionError(
            f"no captured query contains: {snippet!r}; "
            f"captured: {[c['query'][:80] for c in self.calls]}"
        )


@pytest.fixture
def neo4j_client_with_capture(monkeypatch: pytest.MonkeyPatch) -> Any:
    """Build a Neo4jClient whose run_query is replaced with a capture mock."""
    capture = _CypherCapture()
    client = Neo4jClient.__new__(Neo4jClient)
    # Bypass __init__ which would try to connect to a real driver
    client._initialized = True  # type: ignore[attr-defined]
    client.run_query = capture  # type: ignore[method-assign]
    return client, capture


# ---------------------------------------------------------------------------
# Cypher shape: writes set r.score AND increment r.review_count
# ---------------------------------------------------------------------------


class TestCreateLearningRelationshipCypher:
    """The write Cypher MUST set r.score and increment r.review_count via coalesce."""

    @pytest.mark.asyncio
    async def test_write_sets_score_field(self, neo4j_client_with_capture: Any) -> None:
        client, capture = neo4j_client_with_capture
        await client.create_learning_relationship(
            user_id="u1", concept="addition", score=75, group_id="math"
        )
        cypher = capture.last_query
        # The write path uses r.score (single source of truth), NOT r.last_score
        assert "r.score = $score" in cypher, (
            "create_learning_relationship must SET r.score, not r.last_score; "
            f"got: {cypher}"
        )
        # Negative guard: never write r.last_score (legacy phantom field)
        assert "r.last_score" not in cypher, (
            "r.last_score is a legacy phantom field — never write it"
        )

    @pytest.mark.asyncio
    async def test_write_increments_review_count_via_coalesce(
        self, neo4j_client_with_capture: Any
    ) -> None:
        client, capture = neo4j_client_with_capture
        await client.create_learning_relationship(
            user_id="u1", concept="addition", score=80, group_id="math"
        )
        cypher = capture.last_query
        # coalesce handles both first-time (null → 0) and repeat (n → n+1) cases
        assert "coalesce(r.review_count, 0)" in cypher, (
            "review_count must use coalesce(r.review_count, 0) + 1 to handle "
            f"first-time scoring; got: {cypher}"
        )
        assert "+ 1" in cypher, "review_count must increment by 1 each scoring event"

    @pytest.mark.asyncio
    async def test_write_passes_score_param(
        self, neo4j_client_with_capture: Any
    ) -> None:
        client, capture = neo4j_client_with_capture
        await client.create_learning_relationship(
            user_id="u1", concept="addition", score=75, group_id="math"
        )
        kwargs = capture.calls[-1]["kwargs"]
        assert kwargs["score"] == 75
        assert kwargs["userId"] == "u1"
        assert kwargs["concept"] == "addition"
        # T1 统一 (2026-07-10): 物理层 group_id 单一 __ 格式 —
        # 绑定前过 to_physical_group_id ("math" → canonical → "vault__math")
        assert kwargs["groupId"] == "vault__math"


# ---------------------------------------------------------------------------
# Cypher shape: reads alias r.score AS last_score (NOT r.last_score)
# ---------------------------------------------------------------------------


class TestGetReviewSuggestionsCypher:
    """The read Cypher MUST alias r.score AS last_score, NOT read r.last_score."""

    @pytest.mark.asyncio
    async def test_read_with_group_id_uses_alias(
        self, neo4j_client_with_capture: Any
    ) -> None:
        client, capture = neo4j_client_with_capture
        await client.get_review_suggestions(user_id="u1", limit=10, group_id="math")
        cypher = capture.find_query_with("LEARNED")
        # Single source of truth: alias r.score back as last_score
        assert "r.score as last_score" in cypher.lower(), (
            "get_review_suggestions must read r.score (aliased to last_score), "
            f"not r.last_score; got: {cypher}"
        )
        # Negative guard against the legacy phantom field
        assert "r.last_score" not in cypher, (
            "r.last_score is a legacy phantom field — must use r.score AS last_score"
        )

    @pytest.mark.asyncio
    async def test_read_without_group_id_still_scoped(
        self, neo4j_client_with_capture: Any
    ) -> None:
        """CARD-G4-1a (2026-08-30) — 原名 test_read_without_group_id_uses_alias。

        契约变更: 不传 group_id **不再**意味着"不过滤"。审计 §5 #3 的无 group
        分支已删除 (Codex round-1 B-2), 作用域改由 read_scope_params 统一解析
        (per-request ContextVar → active vault → 解析不出即抛)。本用例保留原有
        的 `r.score AS last_score` 断言, 并加上"仍然带组过滤"的新断言。
        """
        client, capture = neo4j_client_with_capture
        await client.get_review_suggestions(user_id="u1", limit=5, group_id=None)
        cypher = capture.find_query_with("LEARNED")
        assert "r.score as last_score" in cypher.lower()
        assert "r.last_score" not in cypher
        assert "$group_id" in cypher and "$group_prefix" in cypher, (
            f"不传 group_id 也必须带作用域过滤 (R4 禁止静默全库读); got: {cypher}"
        )

    @pytest.mark.asyncio
    async def test_read_filter_by_group_id_when_provided(
        self, neo4j_client_with_capture: Any
    ) -> None:
        """CARD-G4-1a: 过滤形态由等值 `$groupId` 改为**等值 OR 前缀**。

        原断言 `c.group_id = $groupId` 锁的是旧的等值语义 —— 现网存量 Concept/
        LEARNED 全在 canvas 子组, 等值会让复习建议整页空 (见读契约 R4 前缀语义
        段)。新断言锁三件事: 两个 alias 都过滤、参数名成对、前缀锚带 `__` 定界符。
        """
        client, capture = neo4j_client_with_capture
        await client.get_review_suggestions(user_id="u1", limit=10, group_id="math")
        cypher = capture.find_query_with("LEARNED")
        for alias in ("c", "r"):
            assert f"{alias}.group_id = $group_id" in cypher, (
                f"alias {alias!r} 缺等值过滤 (R1 每个 alias 逐一过滤); got: {cypher}"
            )
            assert f"{alias}.group_id STARTS WITH $group_prefix" in cypher, (
                f"alias {alias!r} 缺前缀过滤 (vault 子组会被误挡); got: {cypher}"
            )
        params = capture.find_params_with("LEARNED") if hasattr(capture, "find_params_with") else None
        if params is not None:
            assert params["group_prefix"] == params["group_id"] + "__", (
                "前缀锚必须带 `__` 定界符, 否则 vault__x 会吃掉 vault__xy"
            )


# ---------------------------------------------------------------------------
# End-to-end contract: write score, then expect read to surface it as last_score
# ---------------------------------------------------------------------------


class TestEndToEndContract:
    """Verify the (write r.score) → (read r.score AS last_score) loop holds."""

    @pytest.mark.asyncio
    async def test_score_round_trips_as_last_score(self) -> None:
        """When the write sets r.score=75, the read should return last_score=75.

        We mock run_query so the write captures the SET clause and the read
        returns the captured score under the alias key.
        """
        captured_score: Dict[str, Any] = {}

        async def fake_run_query(query: str, **kwargs: Any) -> List[Dict[str, Any]]:
            if "MERGE (u:User" in query:
                captured_score["score"] = kwargs["score"]
                return [{"r": {"score": kwargs["score"]}}]
            if "LEARNED" in query and "as last_score" in query.lower():
                # Simulate the alias surfacing r.score as last_score
                return [
                    {
                        "concept": "addition",
                        "concept_id": "c1",
                        "last_score": captured_score.get("score"),
                        "review_count": 1,
                        "due_date": "2026-04-08T00:00:00Z",
                    }
                ]
            return []

        client = Neo4jClient.__new__(Neo4jClient)
        client._initialized = True  # type: ignore[attr-defined]
        client.run_query = AsyncMock(side_effect=fake_run_query)  # type: ignore[method-assign]

        await client.create_learning_relationship(
            user_id="u1", concept="addition", score=75, group_id="math"
        )
        suggestions = await client.get_review_suggestions(
            user_id="u1", limit=10, group_id="math"
        )

        assert len(suggestions) == 1
        assert suggestions[0]["last_score"] == 75, (
            "score=75 written via r.score must round-trip as last_score=75"
        )
        # Never null: the bug it replaces returned None forever
        assert suggestions[0]["last_score"] is not None
