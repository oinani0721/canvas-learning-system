"""CARD-G4-1a Codex round-1 整改门 — 调用链侧 (B-3 / H-1 / H-3).

三条整改各自的行为锁:

  B-3  ``/api/v1/exam/quick`` 请求体强制带 ``vault_id``, 却既不解析也不下传,
       于是 A vault 的进程收到 ``vault_id=B`` 的请求时读 **A** 的批注、把题目
       记成 B 的 (canvas node id 非全局唯一 → A/B 同名节点直接串库)。
  H-1  ``archive_scheduler`` 的本地解析链: ContextVar 默认值 ``"general"`` 恒
       truthy ⇒ 那句"回落 DEFAULT_GROUP_ID"的 WARNING 是死代码, 实际稳定落
       ``canonical_group_id("general") == "vault:default"`` 污染桶, 该调度器
       每 24h 真实运行。
  H-3  ``VaultScopeUnresolved`` 若继承 RuntimeError, 会被两处
       ``except (RuntimeError, ConnectionError, asyncio.TimeoutError)`` 的
       依赖降级 handler 吞成空结果 = 静默断读。
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.core.subject_config import _current_subject_id
from app.core.vault_scope import VaultScopeUnresolved

VAULT = "vault:g41a_callers"


@pytest.fixture
def in_vault():
    token = _current_subject_id.set(VAULT)
    try:
        yield VAULT
    finally:
        _current_subject_id.reset(token)


# ---------------------------------------------------------------------------
# H-3 — 异常不得被"依赖故障降级"handler 吞掉
# ---------------------------------------------------------------------------


def test_scope_exception_is_not_a_runtime_error():
    """继承关系本身就是契约: 继承 RuntimeError 会被既有降级 handler 吞掉。"""
    assert not issubclass(VaultScopeUnresolved, RuntimeError), (
        "VaultScopeUnresolved 不得继承 RuntimeError —— "
        "conversation_inheritance / learning_context_service 的 "
        "`except (RuntimeError, ConnectionError, asyncio.TimeoutError)` "
        "会把配置故障吞成空结果 (静默断读)"
    )
    assert issubclass(VaultScopeUnresolved, Exception)


@pytest.mark.asyncio
async def test_inheritance_neighbors_raise_not_swallow(monkeypatch):
    """作用域不可信时, 邻居查询必须抛 —— 不得返回 [] 伪装成"没有邻居"。"""
    from app.services.conversation_inheritance import (
        _fetch_neighbor_records_for_inheritance,
    )

    monkeypatch.setattr("app.config.get_current_vault_id", lambda: "default")
    token = _current_subject_id.set("general")
    try:
        with pytest.raises(VaultScopeUnresolved):
            await _fetch_neighbor_records_for_inheritance("node-1")
    finally:
        _current_subject_id.reset(token)


@pytest.mark.asyncio
async def test_tips_and_errors_raise_not_swallow(monkeypatch):
    """同上: tips/errors 这一路也不得把配置故障吞成"这个节点没有批注"。"""
    from app.services import learning_context_service as lcs

    class _Svc:
        async def search_memories(self, **kwargs):
            raise VaultScopeUnresolved("simulated unresolved scope")

    async def _fake_get_memory_service():
        return _Svc()

    monkeypatch.setattr(
        "app.services.memory_service.get_memory_service", _fake_get_memory_service
    )
    with pytest.raises(VaultScopeUnresolved):
        await lcs._fetch_tips_and_errors("node-1", VAULT)


# ---------------------------------------------------------------------------
# H-1 — archive_scheduler 不再自建解析链落污染桶
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_archive_scheduler_uses_read_scope_not_default_bucket(monkeypatch, in_vault):
    """调度器必须按真实 vault 作用域查, 而不是 canonical('general')=vault:default。"""
    from app.services.archive_scheduler import ArchiveScheduler

    seen = {}

    class _Mem:
        async def search_memories(self, **kwargs):
            seen.update(kwargs)
            return []

    async def _fake_get_memory_service():
        return _Mem()

    monkeypatch.setattr(
        "app.services.memory_service.get_memory_service", _fake_get_memory_service
    )
    await ArchiveScheduler()._get_active_node_ids()

    assert seen.get("group_id") == VAULT, seen
    assert seen.get("group_id") != "vault:default", (
        "调度器又落回污染桶 —— 它每 24h 真实运行, 落桶 = 长期认为'没有活跃对话'"
    )


@pytest.mark.asyncio
async def test_archive_scheduler_surfaces_unresolved_scope(monkeypatch):
    """作用域推导不出时, 调度器上层必须给出显式 error, 不是"没有活跃节点"。"""
    from app.services.archive_scheduler import ArchiveScheduler

    monkeypatch.setattr("app.config.get_current_vault_id", lambda: "default")
    token = _current_subject_id.set("general")
    try:
        with pytest.raises(VaultScopeUnresolved):
            await ArchiveScheduler()._get_active_node_ids()
    finally:
        _current_subject_id.reset(token)


# ---------------------------------------------------------------------------
# B-3 — exam/quick 解析并下传 vault
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_exam_quick_forwards_resolved_scope(monkeypatch):
    """请求体里的 vault_id 必须被解析并下传给 tips/errors 那一路。"""
    from app.api.v1.endpoints import exam_quick as eq

    captured = {}

    async def _fake_fetch(node_id, group_id=None):
        captured["node_id"] = node_id
        captured["group_id"] = group_id
        return ([], [])

    monkeypatch.setattr(eq, "_fetch_tips_and_errors", _fake_fetch)
    monkeypatch.setattr(eq, "_read_node_markdown", lambda nid: "body")

    class _Gen:
        async def generate_question(self, **kwargs):
            return {"question_text": "Q?", "tips_used": []}

    monkeypatch.setattr(eq, "QuestionGenerator", _Gen)

    from app.config import get_current_vault_id

    active = get_current_vault_id()
    resp = await eq.exam_quick(eq.ExamQuickRequest(node_id="n1", vault_id=active))

    assert resp.question_text == "Q?"
    assert captured["group_id"], "group 未下传 —— tips/errors 这一路仍会串库"
    assert captured["group_id"].startswith("vault:"), captured


@pytest.mark.asyncio
async def test_exam_quick_rejects_other_vault(monkeypatch):
    """请求指向**另一个** vault 时 409 fail-closed, 不得静默读 active vault
    的批注再把题目标成请求 vault (canvas node id 非全局唯一, 会直接串库)。"""
    from fastapi import HTTPException

    from app.api.v1.endpoints import exam_quick as eq

    called = {"fetch": False}

    async def _fake_fetch(node_id, group_id=None):
        called["fetch"] = True
        return ([], [])

    monkeypatch.setattr(eq, "_fetch_tips_and_errors", _fake_fetch)

    with pytest.raises(HTTPException) as exc:
        await eq.exam_quick(
            eq.ExamQuickRequest(node_id="n1", vault_id="g41a_definitely_other_vault")
        )
    assert exc.value.status_code == 409
    assert called["fetch"] is False, "409 必须发生在任何读取之前"


@pytest.mark.asyncio
async def test_exam_quick_scope_failure_is_not_downgraded_to_empty_tips(monkeypatch):
    """作用域不可信 ≠ "上下文暂时取不到" —— 不得走 tips=[] 的降级路径。"""
    from app.api.v1.endpoints import exam_quick as eq

    async def _raising(node_id, group_id=None):
        raise VaultScopeUnresolved("simulated")

    monkeypatch.setattr(eq, "_fetch_tips_and_errors", _raising)
    monkeypatch.setattr(eq, "_read_node_markdown", lambda nid: "body")

    from app.config import get_current_vault_id

    with pytest.raises(VaultScopeUnresolved):
        await eq.exam_quick(
            eq.ExamQuickRequest(node_id="n1", vault_id=get_current_vault_id())
        )


# ---------------------------------------------------------------------------
# B-2 — client 无 group 全库分支已不存在
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Codex round-2 — JSON 降级模式不得成为封堵的旁路
# ---------------------------------------------------------------------------


def _rel(group_id, concept, *, due=True, score=80):
    from datetime import datetime, timedelta

    ts = datetime.now() - timedelta(days=1)
    return {
        "user_id": "u1",
        "concept_name": concept,
        "concept_id": concept,
        "node_id": concept,
        "group_id": group_id,
        "last_score": score,
        "review_count": 1,
        "timestamp": ts.isoformat(),
        "next_review": (ts if due else datetime.now() + timedelta(days=7)).isoformat(),
    }


@pytest.mark.asyncio
async def test_json_fallback_review_suggestions_is_scoped(in_vault):
    """降级模式下的复习建议必须按 scope 过滤。

    Codex round-2 反证: 该路径此前完全忽略 group 参数 —— **把 Neo4j 弄挂就能
    绕过封堵**, 等于没封。
    """
    from app.clients.neo4j_client import Neo4jClient

    client = Neo4jClient(use_json_fallback=True)
    await client.initialize()
    client._data["relationships"] = [
        _rel(VAULT, "mine"),
        _rel(f"{VAULT}:board_x", "mine_subgroup"),  # 子组仍可见 (保召回)
        _rel("vault:g41a_other", "theirs"),
    ]
    client._data.setdefault("concepts", [])

    rows = await client.get_review_suggestions(user_id="u1", limit=50)

    names = {r["concept"] for r in rows}
    assert names == {"mine", "mine_subgroup"}, names


@pytest.mark.asyncio
async def test_json_fallback_review_concept_id_is_scoped(in_vault):
    """Codex round-3: concept 反查也要过 scope。

    关系过滤住了, 但 concept_id 曾按 **name 全库匹配** —— 两个 vault 有同名
    概念时会取到他 vault 那条的 id (标识符级串读)。
    """
    from app.clients.neo4j_client import Neo4jClient

    client = Neo4jClient(use_json_fallback=True)
    await client.initialize()
    client._data["relationships"] = [_rel(VAULT, "同名概念")]
    client._data["concepts"] = [
        # 他 vault 的同名概念排在前面 —— 全库匹配会先撞上它
        {"id": "concept-THEIRS", "name": "同名概念", "group_id": "vault:g41a_other"},
        {"id": "concept-MINE", "name": "同名概念", "group_id": VAULT},
    ]

    rows = await client.get_review_suggestions(user_id="u1", limit=10)

    assert [r["concept_id"] for r in rows] == ["concept-MINE"], rows


def test_contextvar_injected_deprecated_group_still_readable():
    """Codex round-3 回归锁: ContextVar 里的值 = 有人显式设过, 不是"推导落桶"。

    `resolve_vault_scope(legacy_group_id='cs188')` 会把归一化产物
    `vault:default` 注入 ContextVar (G2-2 契约 4 的 deprecated 兼容层)。若读侧
    把它当成"配置断裂"抛错, 整条 legacy 路径在读侧就断了 —— 本卡不推翻兼容层。
    """
    from app.core.vault_scope import require_read_group

    token = _current_subject_id.set("vault:default")
    try:
        assert require_read_group(context="unit.legacy_ctx") == "vault:default"
    finally:
        _current_subject_id.reset(token)


@pytest.mark.asyncio
async def test_json_fallback_score_history_is_scoped(in_vault):
    """降级模式下的历史分数同理: 两 vault 同名节点不得互读。"""
    from app.clients.neo4j_client import Neo4jClient

    client = Neo4jClient(use_json_fallback=True)
    await client.initialize()
    client._data["relationships"] = []
    client._data["score_history"] = [
        {"concept_id": "n1", "score": 11, "timestamp": "2026-08-30T01:00:00", "group_id": VAULT},
        {"concept_id": "n1", "score": 99, "timestamp": "2026-08-30T02:00:00", "group_id": "vault:g41a_other"},
    ]

    rows = await client.get_concept_score_history(
        concept_id="n1", canvas_name="board.canvas", limit=10
    )

    assert [r["score"] for r in rows] == [11], rows


# ---------------------------------------------------------------------------
# Codex round-2 — 物理 ID 碰撞
# ---------------------------------------------------------------------------


def test_segment_with_double_underscore_is_rejected(in_vault):
    """`vault:a__board` 与 `vault:a:board` 物理化后同名 ⇒ 两个 vault 共用可见面。

    标准 sanitize 链会折叠连续下划线, 产不出这种值; 出现即配置有误, 必须拒绝
    而不是带着歧义继续读。
    """
    from app.core.vault_scope import read_scope_params, require_read_group

    with pytest.raises(VaultScopeUnresolved):
        require_read_group("vault:a__board", context="unit.collision")
    with pytest.raises(VaultScopeUnresolved):
        read_scope_params("vault:a__board", context="unit.collision")


def test_vault_literally_named_default_is_allowed(monkeypatch):
    """反向: vault **真的叫** default 时是合法作用域, 不能与"没配置"混为一谈。"""
    import app.config as config_mod
    from app.core.vault_scope import require_read_group

    class _S:
        ACTIVE_VAULT = "default"

    monkeypatch.setattr(config_mod, "get_settings", lambda: _S())
    monkeypatch.setattr(config_mod, "get_current_vault_id", lambda: "default")
    token = _current_subject_id.set("general")
    try:
        assert require_read_group(context="unit.real_default") == "vault:default"
    finally:
        _current_subject_id.reset(token)


@pytest.mark.asyncio
async def test_client_review_suggestions_has_no_unscoped_branch(in_vault):
    """不传 group_id 也必须带作用域过滤 (审计 §5 #3 的分支已删除)。"""
    from app.clients.neo4j_client import Neo4jClient

    client = Neo4jClient(use_json_fallback=False)
    captured = {}

    async def _capture(query, **params):
        captured["query"] = query
        captured["params"] = params
        return []

    client.run_query = AsyncMock(side_effect=_capture)
    await client.get_review_suggestions(user_id="u1", limit=5)

    q = captured["query"]
    assert "$group_id" in q and "$group_prefix" in q, q
    assert captured["params"]["group_prefix"].endswith("__")
    # 反向: 不存在"只有 next_review 条件"的裸查询
    assert "c.group_id" in q and "r.group_id" in q, q
