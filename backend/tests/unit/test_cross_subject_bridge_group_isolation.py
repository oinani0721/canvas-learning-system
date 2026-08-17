"""P0-SYNC-ISO-2026-08-17 R10 — cross_subject_bridge 读侧 vault 隔离行为测试.

背景 (外部审查 P1-06): 写侧已完成 {id, group_id} 复合键隔离, 但读侧
cross_subject_bridge 两条查询裸查:
- `MATCH (s:Subject)` 列全局 Subject 注册表 (跨 vault 候选泄漏);
- `MATCH (n:CanvasNode {subjectId: $subject_id})` 不限 vault — 两个 vault
  同名 subjectId 的 tag 集互相污染, Jaccard 在脏集合上计算。

口径: 本服务是 vault 内跨 subject 桥 (Story 1.9 AC-5), 跨 subject ≠ 跨
vault — 过滤按 vault 前缀 (group_id = vault 根 OR STARTS WITH 根 + "__"),
不是全量 group 精确匹配 (会挡掉本 vault 其他 subject 的二级子组)。

教训锁 (同 test_sync_group_isolation.py): 全部**行为断言** — 检查 stub
session.run 实际收到的 Cypher 文本和绑定参数, 禁止 hasattr 式静态断言。
"""

from __future__ import annotations

import re
from typing import Any, Callable, Dict, List

import pytest

from app.services.cross_subject_bridge import (
    expand_search_subjects,
    get_subject_tags_from_neo4j,
)

LOGICAL_GID_A = "vault:vault_a"
LOGICAL_GID_B = "vault:vault_b"
PHYSICAL_GID_A = "vault__vault_a"
PHYSICAL_GID_B = "vault__vault_b"


def _norm(query: str) -> str:
    """折叠空白, 让 Cypher 文本断言不受缩进/换行影响."""
    return re.sub(r"\s+", " ", query).strip()


# ---------------------------------------------------------------------------
# Stub 基建 — 记录 session.run(query, **kwargs) 行为
# ---------------------------------------------------------------------------


class _StubResult:
    def __init__(self, records: List[Dict[str, Any]]) -> None:
        self._records = records

    async def data(self) -> List[Dict[str, Any]]:
        return list(self._records)


class _StubSession:
    """responder(query, kwargs) -> records; 抛异常则透传 (降级路径测试)."""

    def __init__(self, responder: Callable[[str, Dict[str, Any]], List[Dict[str, Any]]]) -> None:
        self._responder = responder
        self.run_calls: List[Dict[str, Any]] = []

    async def run(self, query: str, **kwargs: Any) -> _StubResult:
        self.run_calls.append({"query": query, "kwargs": kwargs})
        return _StubResult(self._responder(query, kwargs))

    async def __aenter__(self) -> "_StubSession":
        return self

    async def __aexit__(self, *exc: Any) -> bool:
        return False


class _StubDriver:
    def __init__(self, session: _StubSession) -> None:
        self._session = session

    def session(self) -> _StubSession:
        return self._session


def _bridge_responder(
    subjects: List[str],
    tags_by_subject: Dict[str, List[str]],
) -> Callable[[str, Dict[str, Any]], List[Dict[str, Any]]]:
    """按查询形状路由: subject 列表查询 → subjects; tag 查询 → titles."""

    def responder(query: str, kwargs: Dict[str, Any]) -> List[Dict[str, Any]]:
        if "DISTINCT n.subjectId" in query:
            return [{"id": sid} for sid in subjects]
        if "subjectId: $subject_id" in query:
            words = tags_by_subject.get(kwargs.get("subject_id", ""), [])
            return [{"title": " ".join(words), "concepts": None}] if words else []
        raise AssertionError(f"unexpected query shape: {query}")

    return responder


def _make_driver(subjects: List[str], tags_by_subject: Dict[str, List[str]]) -> tuple[_StubDriver, _StubSession]:
    session = _StubSession(_bridge_responder(subjects, tags_by_subject))
    return _StubDriver(session), session


# ---------------------------------------------------------------------------
# 1. Subject 候选列表查询 — vault 前缀过滤 + 物理格式绑定
# ---------------------------------------------------------------------------


class TestSubjectListingVaultScoped:
    @pytest.mark.asyncio
    async def test_listing_query_carries_vault_prefix_filter(self) -> None:
        driver, session = _make_driver(subjects=["math"], tags_by_subject={"math": ["algebra", "calculus"]})
        await expand_search_subjects("math", driver, threshold=0.3, group_id=LOGICAL_GID_A)
        listing = _norm(session.run_calls[0]["query"])
        # 旧缺陷形状不得回归: 全局 Subject 注册表无 group_id 属性
        assert "MATCH (s:Subject)" not in listing
        # 候选从 vault 内 CanvasNode 投影推导, 且带前缀过滤
        assert "MATCH (n:CanvasNode)" in listing
        assert "(n.group_id = $vault_group OR n.group_id STARTS WITH $vault_prefix)" in listing
        assert "RETURN DISTINCT n.subjectId AS id" in listing

    @pytest.mark.asyncio
    async def test_listing_binds_physical_vault_format(self) -> None:
        driver, session = _make_driver(subjects=[], tags_by_subject={})
        await expand_search_subjects("math", driver, threshold=0.3, group_id=LOGICAL_GID_A)
        kwargs = session.run_calls[0]["kwargs"]
        assert kwargs["vault_group"] == PHYSICAL_GID_A
        assert kwargs["vault_prefix"] == PHYSICAL_GID_A + "__"
        assert ":" not in kwargs["vault_group"], "逻辑冒号格式直接绑定 = 假过滤"

    @pytest.mark.asyncio
    async def test_subject_level_group_collapses_to_vault_root(self) -> None:
        """vault:x:subject 二级 group 传入 → 过滤仍按 vault 根 — 跨 subject
        桥必须能看到本 vault 其他 subject 的子组."""
        driver, session = _make_driver(subjects=[], tags_by_subject={})
        await expand_search_subjects("math", driver, threshold=0.3, group_id="vault:vault_a:math")
        kwargs = session.run_calls[0]["kwargs"]
        assert kwargs["vault_group"] == PHYSICAL_GID_A
        assert kwargs["vault_prefix"] == PHYSICAL_GID_A + "__"


# ---------------------------------------------------------------------------
# 2. Tag 查询 — vault 前缀过滤 + 物理格式绑定
# ---------------------------------------------------------------------------


class TestTagQueryVaultScoped:
    @pytest.mark.asyncio
    async def test_tag_query_carries_vault_prefix_filter(self) -> None:
        driver, session = _make_driver(subjects=[], tags_by_subject={"math": ["algebra", "calculus"]})
        tags = await get_subject_tags_from_neo4j(driver, "math", group_id=LOGICAL_GID_A)
        assert tags == {"algebra", "calculus"}
        query = _norm(session.run_calls[0]["query"])
        assert "MATCH (n:CanvasNode {subjectId: $subject_id})" in query
        assert "(n.group_id = $vault_group OR n.group_id STARTS WITH $vault_prefix)" in query, (
            "同名 subjectId 跨 vault tag 污染 — tag 查询必须限定 vault 前缀"
        )

    @pytest.mark.asyncio
    async def test_tag_query_binds_physical_vault_format(self) -> None:
        driver, session = _make_driver(subjects=[], tags_by_subject={"math": ["algebra"]})
        await get_subject_tags_from_neo4j(driver, "math", group_id=LOGICAL_GID_A)
        kwargs = session.run_calls[0]["kwargs"]
        assert kwargs["subject_id"] == "math"
        assert kwargs["vault_group"] == PHYSICAL_GID_A
        assert kwargs["vault_prefix"] == PHYSICAL_GID_A + "__"


# ---------------------------------------------------------------------------
# 3. ContextVar 兜底 + 双 vault 隔离
# ---------------------------------------------------------------------------


class TestVaultContextIsolation:
    @pytest.mark.asyncio
    async def test_contextvar_fallback_binds_current_vault(self) -> None:
        """group_id 未显式传时兜底 get_current_subject_id() ContextVar
        (endpoint 层 resolve_vault_group_id 注入的逻辑 group_id)."""
        from app.core.subject_config import (
            get_current_subject_id,
            set_current_subject_id,
        )

        driver, session = _make_driver(subjects=[], tags_by_subject={})
        previous = get_current_subject_id()
        set_current_subject_id(LOGICAL_GID_B)
        try:
            await expand_search_subjects("math", driver, threshold=0.3)
        finally:
            set_current_subject_id(previous)
        kwargs = session.run_calls[0]["kwargs"]
        assert kwargs["vault_group"] == PHYSICAL_GID_B
        assert kwargs["vault_prefix"] == PHYSICAL_GID_B + "__"

    @pytest.mark.asyncio
    async def test_dual_vault_expansions_bind_distinct_groups(self) -> None:
        driver_a, session_a = _make_driver(subjects=[], tags_by_subject={})
        driver_b, session_b = _make_driver(subjects=[], tags_by_subject={})
        await expand_search_subjects("math", driver_a, threshold=0.3, group_id=LOGICAL_GID_A)
        await expand_search_subjects("math", driver_b, threshold=0.3, group_id=LOGICAL_GID_B)
        gid_a = session_a.run_calls[0]["kwargs"]["vault_group"]
        gid_b = session_b.run_calls[0]["kwargs"]["vault_group"]
        assert gid_a != gid_b, "不同 vault 的扩展查询必须绑定不同 vault_group"

    @pytest.mark.asyncio
    async def test_all_tag_queries_share_the_same_vault_pin(self) -> None:
        """expand 内部对每个候选 subject 的 tag 查询必须沿用同一 vault pin —
        防列表和 tag 两步用不同 group 造成半隔离."""
        driver, session = _make_driver(
            subjects=["math", "physics"],
            tags_by_subject={
                "math": ["algebra", "calculus"],
                "physics": ["algebra", "calculus", "forces"],
            },
        )
        result = await expand_search_subjects("math", driver, threshold=0.3, group_id=LOGICAL_GID_A)
        # Jaccard({algebra,calculus}, {algebra,calculus,forces}) = 2/3 ≥ 0.3
        assert result == ["math", "physics"]
        assert len(session.run_calls) == 3  # 1 listing + 2 tag queries
        for call in session.run_calls:
            assert call["kwargs"]["vault_group"] == PHYSICAL_GID_A
            assert call["kwargs"]["vault_prefix"] == PHYSICAL_GID_A + "__"


# ---------------------------------------------------------------------------
# 4. 降级契约不回退
# ---------------------------------------------------------------------------


class TestDegradedPathsPreserved:
    @pytest.mark.asyncio
    async def test_listing_failure_falls_back_to_current_subject(self) -> None:
        def _boom(query: str, kwargs: Dict[str, Any]) -> List[Dict[str, Any]]:
            raise RuntimeError("neo4j down")

        session = _StubSession(_boom)
        driver = _StubDriver(session)
        result = await expand_search_subjects("math", driver, threshold=0.3, group_id=LOGICAL_GID_A)
        assert result == ["math"]

    @pytest.mark.asyncio
    async def test_empty_vault_returns_current_subject_only(self) -> None:
        driver, _session = _make_driver(subjects=[], tags_by_subject={})
        result = await expand_search_subjects("math", driver, threshold=0.3, group_id=LOGICAL_GID_A)
        assert result == ["math"]
