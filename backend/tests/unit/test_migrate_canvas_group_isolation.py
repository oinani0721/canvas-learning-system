"""P0-SYNC-ISO-2026-08-17 — migrate_canvas_group_isolation.py 单测.

mock session 注入 (group_id_migration_service._DriverLike 同款 pattern),
锁死六条语义:
1. census 扫描必须是 WHERE group_id IS NULL (⚠️ group_id_migration_service
   的扫描器是 IS NOT NULL, 对本次目标完全不可见 — 禁止复用)
2. 回填顺序 board → node → edge (node 从 board 继承 group)
3. 约束替换先建新 (3×CREATE) 后删旧 (2×DROP) — 无保护真空窗口
4. verify gate: NULL 未归零时 census_blockers / 调用方必须能拿到非零残留
5. 歧义检测 (R10 P1-05): node 板继承多候选 / edge 两端点投影 group 不一致
   → census_blockers 必须 block (--apply 中止), 干净数据零 blocker
6. 迁移文档锁 (R10 P1-04): 003 ROLLBACK 先建旧约束后删新约束 (不留零约束
   真空); 004 声明 VaultIdentity + CANVAS_EDGE 约束
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable

import pytest

_SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
_MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "migrations"
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
    """全空图: 计数 0, 清单/重复/歧义检测空 (零行), 回填 0."""
    if "cnt > 1" in query:
        # 分组重复检测: 空图无分组行 (WHERE cnt > 1 过滤后零行, 不是 {c:0})
        return []
    if "updated" in query:
        return [{"updated": 0}]
    if "count(" in query:
        return [{"c": 0}]
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


def _census_dict(
    *,
    duplicates: dict[str, list[dict[str, Any]]] | None = None,
    ambiguities: dict[str, list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    """census 契约骨架 (duplicates + ambiguities 全空, 按需覆写)."""
    base_dup: dict[str, list[dict[str, Any]]] = {
        "node_composite": [],
        "board_composite": [],
        "board_subject_name": [],
    }
    base_amb: dict[str, list[dict[str, Any]]] = {
        "node_multi_board_group": [],
        "edge_endpoint_group_mismatch": [],
    }
    base_dup.update(duplicates or {})
    base_amb.update(ambiguities or {})
    return {"duplicates": base_dup, "ambiguities": base_amb}


class TestCensusBlockers:
    def test_no_dups_no_blockers(self) -> None:
        assert mig.census_blockers(_census_dict()) == []

    def test_dup_hit_produces_blocker(self) -> None:
        census = _census_dict(duplicates={"node_composite": [{"gid": "vault__a", "id": "n1", "cnt": 2}]})
        blockers = mig.census_blockers(census)
        assert len(blockers) == 1
        assert "CanvasNode (group_id, id)" in blockers[0]


# ---------------------------------------------------------------------------
# 1b: 歧义检测 (R10 P1-05) — 命中即 blocker
# ---------------------------------------------------------------------------


class TestAmbiguities:
    @pytest.mark.asyncio
    async def test_census_ambiguity_scans_read_only_and_null_targeted(self) -> None:
        """歧义扫描必须只读 (无 SET/MERGE/CREATE/DELETE), 且只看 NULL-group
        行 (非 NULL 行的归属歧义是已知局限, 不在扫描范围)。edge 扫描的
        default 兜底必须绑定物理格式 default_gid."""
        session = _FakeSession(_empty_responder)
        await mig.run_census(session, "vault__test")

        node_amb = next(c for c in session.calls if "candidate_groups" in c["query"])
        edge_amb = next(c for c in session.calls if "target_group" in c["query"])

        for call in (node_amb, edge_amb):
            for verb in ("SET ", "MERGE ", "CREATE ", "DELETE "):
                assert verb not in call["query"], f"歧义扫描必须只读, 发现 {verb.strip()}"
        assert "n.group_id IS NULL" in node_amb["query"]
        assert "size(candidate_groups) > 1" in node_amb["query"]
        assert "e.group_id IS NULL" in edge_amb["query"]
        assert "source_group <> target_group" in edge_amb["query"]
        assert edge_amb["params"]["default_gid"] == "vault__test"

    @pytest.mark.asyncio
    async def test_census_surfaces_ambiguity_rows(self) -> None:
        """run_census 必须把歧义命中原样带回 (供 --apply 中止时输出人工
        处置清单)."""

        def responder(query: str, params: dict[str, Any]) -> list[dict[str, Any]]:
            if "candidate_groups" in query:
                return [{"id": "n1", "canvas_id": "cv1", "candidate_groups": ["vault__a", "vault__b"]}]
            if "target_group" in query:
                return [
                    {
                        "id": "e1",
                        "source_id": "n1",
                        "target_id": "n2",
                        "source_group": "vault__a",
                        "target_group": "vault__b",
                    }
                ]
            return _empty_responder(query, params)

        session = _FakeSession(responder)
        census = await mig.run_census(session, "vault__test")

        assert census["ambiguities"]["node_multi_board_group"] == [
            {"id": "n1", "canvas_id": "cv1", "candidate_groups": ["vault__a", "vault__b"]}
        ]
        assert len(census["ambiguities"]["edge_endpoint_group_mismatch"]) == 1
        assert census["ambiguities"]["edge_endpoint_group_mismatch"][0]["source_group"] == "vault__a"

    def test_node_multi_candidate_is_blocker(self) -> None:
        """板继承多候选 → head(collect(...)) 会任取一个 (归属随机),
        必须 block --apply."""
        census = _census_dict(
            ambiguities={
                "node_multi_board_group": [
                    {"id": "n1", "canvas_id": "cv1", "candidate_groups": ["vault__a", "vault__b"]}
                ]
            }
        )
        blockers = mig.census_blockers(census)
        assert len(blockers) == 1
        assert "多候选" in blockers[0]
        assert "n1" in blockers[0], "blocker 必须携带命中行 (人工处置清单)"

    def test_edge_endpoint_mismatch_is_blocker(self) -> None:
        """边两端点投影 group 不一致 → 回填产生悬挂脏边, 必须 block --apply."""
        census = _census_dict(
            ambiguities={
                "edge_endpoint_group_mismatch": [
                    {
                        "id": "e1",
                        "source_id": "n1",
                        "target_id": "n2",
                        "source_group": "vault__a",
                        "target_group": "vault__b",
                    }
                ]
            }
        )
        blockers = mig.census_blockers(census)
        assert len(blockers) == 1
        assert "不一致" in blockers[0]
        assert "e1" in blockers[0], "blocker 必须携带命中行 (人工处置清单)"

    @pytest.mark.asyncio
    async def test_clean_graph_zero_blockers(self) -> None:
        """干净数据 (无重复无歧义) → run_census 产物过 census_blockers
        必须零 blocker (--apply 不被误伤)."""
        session = _FakeSession(_empty_responder)
        census = await mig.run_census(session, "vault__test")
        assert mig.census_blockers(census) == []


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

    @pytest.mark.asyncio
    async def test_backfill_edge_inherits_source_group(self) -> None:
        """审查 F2 锁: 边回填必须继承 source 端点 group (兜底 default) —
        边 group ≠ 端点 group 会让 group 限定的 _delete_edge / 幽灵边
        对账永远看不见它 (悬挂脏边)."""
        session = _FakeSession(lambda q, p: [{"updated": 0}])
        await mig.run_backfill(session, "vault__test")
        edge_call = next(c for c in session.calls if "CANVAS_EDGE" in c["query"])
        assert "coalesce(s.group_id, $default_gid)" in edge_call["query"]


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


# ---------------------------------------------------------------------------
# 5: 迁移文档锁 (R10 P1-04 / P2-01, P2-02) — .cypher 是手工执行的唯一
#    真相源文档, 无可执行面, 只能锁文本语义 (语句存在性 + 出现顺序)
# ---------------------------------------------------------------------------


class TestMigrationDocuments:
    def _rollback_section(self, name: str) -> str:
        text = (_MIGRATIONS_DIR / name).read_text(encoding="utf-8")
        parts = text.split("=== ROLLBACK")
        assert len(parts) == 2, f"{name} 必须恰有一个 ROLLBACK 段"
        return parts[1]

    def test_003_rollback_creates_old_before_dropping_new(self) -> None:
        """P1-04 锁: 回滚必须先 CREATE 旧全局约束 (确认能建) 再 DROP 新
        复合约束 — 反序时若旧约束建不起来, 数据库停在零约束真空态."""
        rollback = self._rollback_section("003_canvas_group_isolation.cypher")

        create_positions = [
            rollback.index("CREATE CONSTRAINT canvasnode_id_unique"),
            rollback.index("CREATE CONSTRAINT canvasboard_subject_name_unique"),
        ]
        drop_positions = [
            rollback.index("DROP CONSTRAINT canvasnode_group_id_unique"),
            rollback.index("DROP CONSTRAINT canvasboard_group_id_unique"),
            rollback.index("DROP CONSTRAINT canvasboard_group_subject_name_unique"),
        ]
        assert max(create_positions) < min(drop_positions), "ROLLBACK 顺序必须: 先 CREATE 旧约束, 后 DROP 新约束"

    def test_003_rollback_has_readonly_precheck_before_create(self) -> None:
        """P1-04 锁: 回滚前必须有只读预检 (跨 group 重复裸 id — 命中禁止
        回滚只能备份恢复), 且预检位于 CREATE 之前."""
        rollback = self._rollback_section("003_canvas_group_isolation.cypher")

        node_precheck = rollback.index("WITH n.id AS id, count(*) AS cnt")
        board_precheck = rollback.index("WITH b.id AS id, count(*) AS cnt")
        first_create = rollback.index("CREATE CONSTRAINT")
        assert node_precheck < first_create
        assert board_precheck < first_create
        assert "backup" in rollback, "预检命中的处置路径 (备份恢复) 必须写明"

    def test_004_declares_both_constraints_with_rollback(self) -> None:
        """P2-01/P2-02 锁: 004 必须声明 VaultIdentity physical_gid 唯一 +
        CANVAS_EDGE (group_id, id) 复合唯一, ROLLBACK 段 DROP 两条."""
        path = _MIGRATIONS_DIR / "004_vault_identity_and_edge_constraints.cypher"
        text = path.read_text(encoding="utf-8")

        assert "CREATE CONSTRAINT vault_identity_gid_unique IF NOT EXISTS" in text
        assert "REQUIRE v.physical_gid IS UNIQUE" in text
        assert "CREATE CONSTRAINT canvas_edge_group_id_unique IF NOT EXISTS" in text
        assert "REQUIRE (e.group_id, e.id) IS UNIQUE" in text
        # 关系唯一约束的版本前提必须写明 (Neo4j 5.7+, 不足时跳过 + 替代检测)
        assert "5.7" in text

        rollback = self._rollback_section("004_vault_identity_and_edge_constraints.cypher")
        assert "DROP CONSTRAINT canvas_edge_group_id_unique IF EXISTS" in rollback
        assert "DROP CONSTRAINT vault_identity_gid_unique IF EXISTS" in rollback
