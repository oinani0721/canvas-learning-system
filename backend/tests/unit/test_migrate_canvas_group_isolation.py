"""P0-SYNC-ISO-2026-08-17 — migrate_canvas_group_isolation.py 单测.

mock session 注入 (group_id_migration_service._DriverLike 同款 pattern),
锁死四条语义:
1. census 扫描必须是 WHERE group_id IS NULL (⚠️ group_id_migration_service
   的扫描器是 IS NOT NULL, 对本次目标完全不可见 — 禁止复用)
2. 回填顺序 board → node → edge (node 从 board 继承 group)
3. 约束替换先建新 (3×CREATE) 后删旧 (2×DROP) — 无保护真空窗口
4. verify gate: NULL 未归零时 census_blockers / 调用方必须能拿到非零残留
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable

import pytest

_SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(_SCRIPTS_DIR))

import migrate_canvas_group_isolation as mig  # noqa: E402


# ---------------------------------------------------------------------------
# Fake session (mock 友好 Protocol: run(query, **params) → result.data())
# ---------------------------------------------------------------------------


class _FakeResult:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows

    async def data(self) -> list[dict[str, Any]]:
        return self._rows


class _FakeSession:
    def __init__(self, responder: Callable[[str, dict[str, Any]], list[dict[str, Any]]]) -> None:
        self.calls: list[dict[str, Any]] = []
        self._responder = responder

    async def run(self, query: str, **params: Any) -> _FakeResult:
        self.calls.append({"query": query, "params": params})
        return _FakeResult(self._responder(query, params))


def _empty_responder(query: str, params: dict[str, Any]) -> list[dict[str, Any]]:
    """全空图: 计数 0, 清单空, 回填 0."""
    if "count(" in query:
        return [{"c": 0}]
    if "RETURN count" in query or "updated" in query:
        return [{"updated": 0}]
    return []


# ---------------------------------------------------------------------------
# 1: census — IS NULL 扫描 + 结构
# ---------------------------------------------------------------------------


class TestCensus:
    @pytest.mark.asyncio
    async def test_census_scans_use_is_null(self) -> None:
        """教训锁: 本迁移目标是 NULL 行 — 所有 census 计数/清单查询必须
        WHERE group_id IS NULL, 禁止套用 group_id_migration_service 的
        IS NOT NULL 扫描器。"""
        session = _FakeSession(_empty_responder)
        await mig.run_census(session, "vault__test")

        count_and_list_calls = [c for c in session.calls if "IS NULL" in c["query"] or "IS NOT NULL" in c["query"]]
        assert count_and_list_calls, "census 必须发出 NULL 扫描查询"
        for call in session.calls[:6]:  # 3 计数 + 3 清单
            assert "group_id IS NULL" in call["query"].replace("n.", "").replace("b.", "").replace("e.", "")

    @pytest.mark.asyncio
    async def test_census_counts_and_rows_structure(self) -> None:
        def responder(query: str, params: dict[str, Any]) -> list[dict[str, Any]]:
            if "count(n)" in query:
                return [{"c": 3}]
            if "count(b)" in query:
                return [{"c": 1}]
            if "count(e)" in query:
                return [{"c": 2}]
            if "n.canvasId AS canvas_id" in query:
                return [{"id": f"n{i}", "canvas_id": "cv", "title": "t"} for i in range(3)]
            if "b.name AS name" in query:
                return [{"id": "b1", "name": "板", "subject_id": "s"}]
            if "source_id" in query:
                return [{"id": f"e{i}", "source_id": "a", "target_id": "b"} for i in range(2)]
            return []

        session = _FakeSession(responder)
        census = await mig.run_census(session, "vault__test")

        assert census["null_counts"] == {
            "CanvasNode": 3,
            "CanvasBoard": 1,
            "CANVAS_EDGE": 2,
        }
        assert len(census["null_rows"]["CanvasNode"]) == 3
        assert len(census["null_rows"]["CanvasBoard"]) == 1
        assert len(census["null_rows"]["CANVAS_EDGE"]) == 2
        assert census["duplicates"]["node_composite"] == []

    @pytest.mark.asyncio
    async def test_dup_queries_bind_default_gid(self) -> None:
        """预重复检测按「回填后投影值」判重 — 必须绑定 default_gid 参数."""
        session = _FakeSession(_empty_responder)
        await mig.run_census(session, "vault__proj")

        dup_calls = [c for c in session.calls if "cnt > 1" in c["query"]]
        assert len(dup_calls) == 3
        for call in dup_calls:
            assert call["params"]["default_gid"] == "vault__proj"


class TestCensusBlockers:
    def test_no_dups_no_blockers(self) -> None:
        census = {
            "duplicates": {
                "node_composite": [],
                "board_composite": [],
                "board_subject_name": [],
            }
        }
        assert mig.census_blockers(census) == []

    def test_dup_hit_produces_blocker(self) -> None:
        census = {
            "duplicates": {
                "node_composite": [{"gid": "vault__a", "id": "n1", "cnt": 2}],
                "board_composite": [],
                "board_subject_name": [],
            }
        }
        blockers = mig.census_blockers(census)
        assert len(blockers) == 1
        assert "CanvasNode (group_id, id)" in blockers[0]


# ---------------------------------------------------------------------------
# 2: 回填顺序 board → node → edge
# ---------------------------------------------------------------------------


class TestBackfill:
    @pytest.mark.asyncio
    async def test_backfill_order_board_node_edge(self) -> None:
        def responder(query: str, params: dict[str, Any]) -> list[dict[str, Any]]:
            return [{"updated": 5}]

        session = _FakeSession(responder)
        result = await mig.run_backfill(session, "vault__test")

        assert result == {"CanvasBoard": 5, "CanvasNode": 5, "CANVAS_EDGE": 5}
        labels_in_order = [
            "CanvasBoard"
            if "CanvasBoard)" in c["query"].split("OPTIONAL")[0]
            else ("CANVAS_EDGE" if "CANVAS_EDGE" in c["query"] else "CanvasNode")
            for c in session.calls
        ]
        assert labels_in_order == ["CanvasBoard", "CanvasNode", "CANVAS_EDGE"], (
            "board 必须最先回填 (node 从 board 继承 group), edge 最后"
        )

    @pytest.mark.asyncio
    async def test_backfill_only_touches_null_rows(self) -> None:
        """幂等: 三条回填全部 WHERE group_id IS NULL — 不覆盖
        exam_service_ext / canvas_projection_sync 已写的值."""
        session = _FakeSession(lambda q, p: [{"updated": 0}])
        await mig.run_backfill(session, "vault__test")
        for call in session.calls:
            assert "group_id IS NULL" in call["query"].replace("n.", "").replace("b.", "").replace("e.", "")
            assert call["params"]["default_gid"] == "vault__test"


# ---------------------------------------------------------------------------
# 3: verify + 约束顺序
# ---------------------------------------------------------------------------


class TestVerifyAndConstraints:
    @pytest.mark.asyncio
    async def test_verify_reports_residual(self) -> None:
        def responder(query: str, params: dict[str, Any]) -> list[dict[str, Any]]:
            if "count(b)" in query:
                return [{"c": 2}]
            return [{"c": 0}]

        session = _FakeSession(responder)
        residual = await mig.run_verify(session)
        assert residual["CanvasBoard"] == 2
        assert any(residual.values()), "残留必须能被调用方检测到 (verify gate)"

    @pytest.mark.asyncio
    async def test_constraint_swap_creates_before_drops(self) -> None:
        """先建新复合约束、后删旧全局约束 — 中途失败也不留无约束真空."""
        session = _FakeSession(lambda q, p: [])
        executed = await mig.run_constraint_swap(session)

        assert executed == list(mig.CONSTRAINT_STATEMENTS)
        kinds = ["CREATE" if q.startswith("CREATE") else "DROP" for q in executed]
        assert kinds == ["CREATE", "CREATE", "CREATE", "DROP", "DROP"]
        # 新约束是复合键; 旧全局约束被删
        assert "(n.group_id, n.id) IS UNIQUE" in executed[0]
        assert "(b.group_id, b.id) IS UNIQUE" in executed[1]
        assert "(b.group_id, b.subjectId, b.name) IS UNIQUE" in executed[2]
        assert "DROP CONSTRAINT canvasnode_id_unique" in executed[3]
        assert "DROP CONSTRAINT canvasboard_subject_name_unique" in executed[4]


# ---------------------------------------------------------------------------
# 4: default gid 归一
# ---------------------------------------------------------------------------


class TestResolveDefaultGid:
    def test_override_is_normalized_to_physical(self) -> None:
        assert mig.resolve_default_gid("vault:canvas_vault") == "vault__canvas_vault"

    def test_physical_override_idempotent(self) -> None:
        assert mig.resolve_default_gid("vault__canvas_vault") == "vault__canvas_vault"
