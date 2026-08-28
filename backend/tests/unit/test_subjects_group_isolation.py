"""P0-SYNC-ISO-2026-08-17 R10 — subjects endpoint 读侧 vault 隔离行为测试.

背景 (外部对抗审查 P1-06): 写侧 (sync_service 等) 已完成 {id, group_id}
复合键隔离, 但 subjects.py 的两条 CanvasNode 计数查询不带 group 过滤 —
GET /subjects/ 与 PUT /subjects/{id} 的 node_count 把所有 vault 的节点
混在一起数, 跨 vault 数据在读取面泄漏。

教训锁 (同 test_sync_group_isolation.py): 全部是**行为断言** — 检查
stub client 实际收到的 Cypher 文本与绑定参数, 禁止 hasattr 式静态断言。

覆盖矩阵:
1. list_subjects: count join 的 Cypher 含 "等值 OR vault 前缀" 过滤 +
   绑定参数是物理 vault__ 格式
2. update_subject: node_count 查询同上, 且 :Subject 元数据更新本身不受影响
3. fallback 链: vault_id 缺省 → ContextVar group; ContextVar 也是默认值 →
   激活 vault (G-DEFAULT 范式, 防 vault:default 空桶清零计数)
4. 双 vault: 同一查询在两个 vault 下绑定参数互不相同, 前缀带 '__' 定界
5. endpoint 层: vault_id Query 参数 → 物理 group_id 进 Cypher (TestClient)
"""

from __future__ import annotations

import re
from typing import Any

import pytest

import app.api.v1.endpoints.subjects as subjects_module
from app.api.v1.endpoints.subjects import list_subjects, update_subject
from app.models.subject_models import SubjectUpdate

PHYSICAL_GID_A = "vault__vault_a"
PHYSICAL_GID_B = "vault__vault_b"

EXPECTED_FILTER = "(n.group_id = $group_id OR n.group_id STARTS WITH $group_prefix)"


def _norm(query: str) -> str:
    """折叠空白, 让 Cypher 文本断言不受缩进/换行影响."""
    return re.sub(r"\s+", " ", query).strip()


class _StubNeo4jClient:
    """行为记录 stub — 记下每条 run_query 的 Cypher 文本与绑定参数."""

    def __init__(self, results: list[list[dict[str, Any]]] | None = None) -> None:
        self.run_calls: list[dict[str, Any]] = []
        self._results = list(results or [])

    async def run_query(self, query: str, **params: Any) -> list[dict[str, Any]]:
        self.run_calls.append({"query": query, "kwargs": params})
        if self._results:
            return self._results.pop(0)
        return []


def _patch_client(monkeypatch: pytest.MonkeyPatch, stub: _StubNeo4jClient) -> None:
    monkeypatch.setattr(subjects_module, "get_neo4j_client", lambda: stub)


def _activate_vault(monkeypatch: pytest.MonkeyPatch, vault_id: str) -> None:
    """CARD-G2-2 (2026-08-28): 让被请求的 vault 成为进程 active vault。

    409 fail-closed 生效后, 请求显式携带的 vault 必须与进程 active vault
    一致, 否则拒绝 (防跨 vault 串库)。本文件的用例本意是验证「不同 vault
    绑定不同 group 参数」, 不是验证跨 vault 访问 —— 因此每次请求前把目标
    vault 声明为激活态, 保持原测试意图不变。
    """
    import app.config as config_module

    monkeypatch.setattr(config_module, "get_current_vault_id", lambda: vault_id)


# ---------------------------------------------------------------------------
# 1: GET /subjects/ — count join 必须带 vault 过滤
# ---------------------------------------------------------------------------


class TestListSubjectsGroupFilter:
    async def test_count_join_query_carries_group_filter(self, monkeypatch) -> None:
        stub = _StubNeo4jClient()
        _patch_client(monkeypatch, stub)
        _activate_vault(monkeypatch, "vault_a")

        await list_subjects(vault_id="vault_a")

        assert len(stub.run_calls) == 1
        query = _norm(stub.run_calls[0]["query"])
        assert "OPTIONAL MATCH (n:CanvasNode {subjectId: s.id})" in query
        assert f"WHERE {EXPECTED_FILTER}" in query
        # WHERE 必须紧跟 OPTIONAL MATCH (作用于可选匹配, 保住 count=0 的行)
        assert query.index("OPTIONAL MATCH") < query.index("WHERE") < query.index("RETURN")

        kwargs = stub.run_calls[0]["kwargs"]
        assert kwargs["group_id"] == PHYSICAL_GID_A
        assert kwargs["group_id"].startswith("vault__"), "必须是物理格式 (防漏 to_physical_group_id)"
        assert kwargs["group_prefix"] == f"{PHYSICAL_GID_A}__", "前缀必须带 '__' 定界, 防 vault__x 误配 vault__xy"

    async def test_response_parsing_survives_filtered_query(self, monkeypatch) -> None:
        stub = _StubNeo4jClient(
            results=[
                [
                    {
                        "id": "subj_1",
                        "name": "Math",
                        "color": None,
                        "createdAt": "2026-01-01T00:00:00Z",
                        "nodeCount": 2,
                    }
                ]
            ]
        )
        _patch_client(monkeypatch, stub)
        _activate_vault(monkeypatch, "vault_a")

        out = await list_subjects(vault_id="vault_a")

        assert out.total == 1
        assert out.subjects[0].id == "subj_1"
        assert out.subjects[0].node_count == 2


# ---------------------------------------------------------------------------
# 2: PUT /subjects/{id} — node_count 查询必须带 vault 过滤
# ---------------------------------------------------------------------------


class TestUpdateSubjectGroupFilter:
    async def test_node_count_query_carries_group_filter(self, monkeypatch) -> None:
        stub = _StubNeo4jClient(
            results=[
                # call 1: SET update → 返回更新后的 subject record
                [
                    {
                        "id": "subj_1",
                        "name": "Math",
                        "color": "#ffffff",
                        "createdAt": "2026-01-01T00:00:00Z",
                    }
                ],
                # call 2: node count
                [{"c": 3}],
            ]
        )
        _patch_client(monkeypatch, stub)
        _activate_vault(monkeypatch, "vault_a")

        out = await update_subject("subj_1", SubjectUpdate(color="#ffffff"), vault_id="vault_a")

        assert len(stub.run_calls) == 2
        cnt_call = stub.run_calls[1]
        query = _norm(cnt_call["query"])
        assert "MATCH (n:CanvasNode {subjectId: $sid})" in query
        assert f"WHERE {EXPECTED_FILTER}" in query
        assert cnt_call["kwargs"]["sid"] == "subj_1"
        assert cnt_call["kwargs"]["group_id"] == PHYSICAL_GID_A
        assert cnt_call["kwargs"]["group_prefix"] == f"{PHYSICAL_GID_A}__"
        assert out.node_count == 3

    async def test_subject_metadata_update_itself_stays_global(self, monkeypatch) -> None:
        """:Subject 节点无 group_id 属性 (全局用户配置, CROSS-VAULT BY
        DESIGN) — SET 更新查询不得被强加 group 过滤, 否则更新永远 404."""
        stub = _StubNeo4jClient(
            results=[
                [
                    {
                        "id": "subj_1",
                        "name": "Math",
                        "color": "#ffffff",
                        "createdAt": "2026-01-01T00:00:00Z",
                    }
                ],
                [{"c": 0}],
            ]
        )
        _patch_client(monkeypatch, stub)
        _activate_vault(monkeypatch, "vault_a")

        await update_subject("subj_1", SubjectUpdate(color="#ffffff"), vault_id="vault_a")

        set_query = _norm(stub.run_calls[0]["query"])
        assert "MATCH (s:Subject {id: $subject_id})" in set_query
        assert "group_id" not in set_query


# ---------------------------------------------------------------------------
# 3: fallback 链 — ContextVar group → 激活 vault
# ---------------------------------------------------------------------------


class TestGroupSourceFallbacks:
    async def test_missing_vault_id_falls_back_to_contextvar_group(self, monkeypatch) -> None:
        """其他 endpoint 已 resolve_vault_group_id 注入 ContextVar 时,
        本 endpoint 缺省 vault_id 必须沿用同一 group (读写同 namespace)."""
        from app.core.subject_config import set_current_subject_id

        stub = _StubNeo4jClient()
        _patch_client(monkeypatch, stub)
        set_current_subject_id("vault:vault_b")

        await list_subjects(vault_id=None)

        kwargs = stub.run_calls[0]["kwargs"]
        assert kwargs["group_id"] == PHYSICAL_GID_B, "逻辑格式 vault:x 必须转物理 vault__x 再绑定"
        assert kwargs["group_prefix"] == f"{PHYSICAL_GID_B}__"

    async def test_default_context_falls_back_to_active_vault(self, monkeypatch) -> None:
        """ContextVar 无人注入 (默认 'general') → 回退激活 vault, 而不是
        DEFAULT_GROUP_ID 归一化出的 vault:default 空桶 (G-DEFAULT 范式)."""
        import app.config as config_module

        from app.core.subject_config import DEFAULT_SUBJECT_ID, set_current_subject_id

        stub = _StubNeo4jClient()
        _patch_client(monkeypatch, stub)
        set_current_subject_id(DEFAULT_SUBJECT_ID)
        monkeypatch.setattr(config_module, "get_current_vault_id", lambda: "canvas_vault")

        await list_subjects(vault_id=None)

        kwargs = stub.run_calls[0]["kwargs"]
        assert kwargs["group_id"] == "vault__canvas_vault"
        assert kwargs["group_id"] != "vault__default", "不得落 vault:default 空桶把计数清零"


# ---------------------------------------------------------------------------
# 4: 双 vault — 绑定参数互不相同
# ---------------------------------------------------------------------------


class TestDualVaultIsolation:
    async def test_same_query_binds_distinct_groups_per_vault(self, monkeypatch) -> None:
        # 两次请求分别在各自 vault 激活的进程里发出 (409 门下这才是合法
        # 形态: 单进程只服务单 active vault, 隔离由「不同进程不同 group」保证)
        stub_a = _StubNeo4jClient()
        _patch_client(monkeypatch, stub_a)
        _activate_vault(monkeypatch, "vault_a")
        await list_subjects(vault_id="vault_a")

        stub_b = _StubNeo4jClient()
        _patch_client(monkeypatch, stub_b)
        _activate_vault(monkeypatch, "vault_b")
        await list_subjects(vault_id="vault_b")

        kw_a = stub_a.run_calls[0]["kwargs"]
        kw_b = stub_b.run_calls[0]["kwargs"]
        assert kw_a["group_id"] != kw_b["group_id"]
        assert kw_a["group_prefix"] != kw_b["group_prefix"]
        # 定界符守护: 前缀恒等于等值参数 + '__'
        assert kw_a["group_prefix"] == kw_a["group_id"] + "__"
        assert kw_b["group_prefix"] == kw_b["group_id"] + "__"


# ---------------------------------------------------------------------------
# 5: endpoint 层 — vault_id Query 参数 → 物理 group_id 进 Cypher
# ---------------------------------------------------------------------------


class TestEndpointPhysicalGroupInjection:
    def test_vault_id_query_param_reaches_cypher_as_physical_group(self, monkeypatch) -> None:
        from fastapi.testclient import TestClient

        from app.main import app

        stub = _StubNeo4jClient()
        _patch_client(monkeypatch, stub)

        with TestClient(app) as client:
            response = client.get("/api/v1/subjects/", params={"vault_id": "canvas_vault"})

        assert response.status_code == 200
        assert len(stub.run_calls) == 1
        query = _norm(stub.run_calls[0]["query"])
        assert f"WHERE {EXPECTED_FILTER}" in query
        # vault_id=canvas_vault → vault:canvas_vault → 物理 vault__canvas_vault
        assert stub.run_calls[0]["kwargs"]["group_id"] == "vault__canvas_vault"
        assert stub.run_calls[0]["kwargs"]["group_prefix"] == "vault__canvas_vault__"
