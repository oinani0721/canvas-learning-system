"""CARD-G4-1a memory_service 读侧作用域契约门 (BATCH-2026-08-29-第六批).

本文件锁死"封堵后的新契约"本身, 而不是让既有用例改到绿:

  1. 无 subject/canvas 的读**不再**给 Neo4j 传 group_id=None (泄漏面);
  2. 内存兜底与 Cypher 侧同一套可见性规则 —— vault 根组读得见自己的
     canvas/semantic/punycode 子组 (保召回), 读不见他 vault (零泄漏),
     canvas 级读仍读不见兄弟白板 (保隔离);
  3. 无归属 (无 group_id) 的内存 episode fail-closed 不可见 —— 这是
     tests/unit/test_story_31a2_*.py 的 fixture 补 group_id 的**依据**:
     生产写路径现已一律落 group_id, fixture 与之对齐而非放水。

契约: .claude/rules/cypher-read-contract.md R1 / R4
真库那一半: tests/integration/test_cypher_contract_gate.py 门 6
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.core.subject_config import _current_subject_id
from tests.unit.test_story_31a2_helpers import _make_neo4j_mock, _make_service

VAULT = "vault:g41a_mem"
SUB_CANVAS = f"{VAULT}:board_x"
SUB_SEMANTIC = f"{VAULT}:semantic"
SUB_PUNY = "vault__g41a_mem__xn--jhqx6ce6ettpca6420ada2925d"
SIBLING = f"{VAULT}:board_y"
OTHER_VAULT = "vault:g41a_other"


@pytest.fixture
def in_vault():
    """per-request 作用域钉在 vault 根组 (等价于插件带 vault_id 的请求)."""
    token = _current_subject_id.set(VAULT)
    try:
        yield VAULT
    finally:
        _current_subject_id.reset(token)


def _ep(group_id, concept, ts="2026-02-05T10:00:00"):
    """构造一条内存 episode。

    ``node_id`` 用 concept 名: get_learning_history 的合并去重键是
    ``(node_id, timestamp)`` —— 若留空则同一时刻的多条会被去重成一条,
    "子组可见"的断言会假红 (踩过一次)。
    """
    ep = {
        "user_id": "u1",
        "concept": concept,
        "node_id": concept,
        "timestamp": ts,
        "score": 80,
    }
    if group_id is not None:
        ep["group_id"] = group_id
    return ep


async def _history(service, **kw):
    return await service.get_learning_history(user_id="u1", **kw)


# ---------------------------------------------------------------------------
# 1. 封堵本体: 读侧不再出现 group_id=None
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_learning_history_never_passes_none_group(in_vault):
    mock_neo4j = _make_neo4j_mock()
    service = _make_service(mock_neo4j)
    await service.initialize()

    await _history(service)

    assert mock_neo4j.get_learning_history.call_args.kwargs["group_id"] == VAULT


@pytest.mark.asyncio
async def test_review_suggestions_never_passes_none_group(in_vault):
    mock_neo4j = _make_neo4j_mock(get_review_suggestions=AsyncMock(return_value=[]))
    service = _make_service(mock_neo4j)
    await service.initialize()

    await service.get_review_suggestions_with_status(user_id="u1")

    assert mock_neo4j.get_review_suggestions.call_args.kwargs["group_id"] == VAULT


# ---------------------------------------------------------------------------
# 2. 内存兜底: 保召回 / 零泄漏 / 保隔离 三面同时成立
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_memory_fallback_recalls_all_subgroups(in_vault):
    """保召回: vault 根组读得见 canvas / semantic / punycode 三类子组。

    这条红 = 封堵把"学习历史"读空了 (现网存量恰好全在 punycode 子组)。
    """
    mock_neo4j = _make_neo4j_mock(get_learning_history=AsyncMock(return_value=[]))
    service = _make_service(mock_neo4j)
    await service.initialize()
    service._episodes = [
        _ep(VAULT, "root_concept"),
        _ep(SUB_CANVAS, "canvas_concept"),
        _ep(SUB_SEMANTIC, "semantic_concept"),
        _ep(SUB_PUNY, "punycode_concept"),
    ]

    result = await _history(service)

    assert {i["concept"] for i in result["items"]} == {
        "root_concept",
        "canvas_concept",
        "semantic_concept",
        "punycode_concept",
    }


@pytest.mark.asyncio
async def test_memory_fallback_blocks_other_vault(in_vault):
    """零泄漏: 他 vault 的内存 episode 不可见。"""
    mock_neo4j = _make_neo4j_mock(get_learning_history=AsyncMock(return_value=[]))
    service = _make_service(mock_neo4j)
    await service.initialize()
    service._episodes = [_ep(VAULT, "mine"), _ep(OTHER_VAULT, "theirs")]

    result = await _history(service)

    assert [i["concept"] for i in result["items"]] == ["mine"]


@pytest.mark.asyncio
async def test_memory_fallback_canvas_scope_blocks_sibling_board(in_vault):
    """保隔离: canvas 级读只见本板, 兄弟板不可见 —— 前缀语义不得放宽成 vault 级。"""
    mock_neo4j = _make_neo4j_mock(get_learning_history=AsyncMock(return_value=[]))
    service = _make_service(mock_neo4j)
    await service.initialize()
    service._episodes = [
        _ep(SUB_CANVAS, "on_board_x"),
        _ep(SIBLING, "on_board_y"),
        _ep(VAULT, "vault_root_level"),
    ]

    result = await _history(service, canvas_path="board_x.canvas")

    assert [i["concept"] for i in result["items"]] == ["on_board_x"]


@pytest.mark.asyncio
async def test_memory_fallback_drops_unattributed_episode(in_vault):
    """fail-closed: 没有 group_id 的内存 episode 在任何 vault 视角下都不可见。

    ⚠️ 这条正是 tests/unit/test_story_31a2_*.py 的 fixture 补 group_id 的依据 ——
    契约是"内存 episode 必须自带归属", 不是"把断言改到绿"。生产侧对称保证见
    test_write_paths_stamp_group_on_memory_episodes。
    """
    mock_neo4j = _make_neo4j_mock(get_learning_history=AsyncMock(return_value=[]))
    service = _make_service(mock_neo4j)
    await service.initialize()
    service._episodes = [_ep(None, "unattributed"), _ep(VAULT, "attributed")]

    result = await _history(service)

    assert [i["concept"] for i in result["items"]] == ["attributed"]


# ---------------------------------------------------------------------------
# 3. 写侧对称: 内存 episode 一律带 group_id (否则上面的 fail-closed 会吞真数据)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_write_paths_stamp_group_on_memory_episodes(in_vault):
    """record_batch_learning_events / record_temporal_event 落 group_id。

    这两条写路径此前只写 canvas_path 不写 group_id —— 读侧 fail-closed 之后
    它们产出的 episode 会在 Tier 3 内存检索里静默消失。
    """
    mock_neo4j = _make_neo4j_mock()
    mock_neo4j.record_episode = AsyncMock()
    mock_neo4j.create_canvas_node_relationship = AsyncMock(return_value=True)
    service = _make_service(mock_neo4j)
    await service.initialize()
    service._episodes = []

    await service.record_batch_learning_events(
        [
            {
                "event_type": "node_created",
                "timestamp": "2026-02-05T10:00:00",
                "canvas_path": "board_x.canvas",
                "node_id": "n1",
            }
        ]
    )
    await service.record_temporal_event(
        event_type="node_created",
        session_id="s1",
        canvas_path="board_x.canvas",
        node_id="n2",
    )

    assert len(service._episodes) == 2, service._episodes
    for ep in service._episodes:
        assert ep.get("group_id"), f"内存 episode 无归属: {ep}"
        assert ep["group_id"].startswith(VAULT), ep["group_id"]


# ---------------------------------------------------------------------------
# 4. learning_context: group 真的下传到了 tips/errors 那一路
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fetch_tips_and_errors_forwards_group(monkeypatch):
    """G2-2 Codex BLOCKER-5 移交项: 调用方已算出 group 却没给这一路。"""
    from app.services import learning_context_service as lcs

    seen = {}

    class _Svc:
        async def search_memories(self, **kwargs):
            seen.update(kwargs)
            return []

    async def _fake_get_memory_service():
        return _Svc()

    monkeypatch.setattr(
        "app.services.memory_service.get_memory_service", _fake_get_memory_service
    )

    await lcs._fetch_tips_and_errors("node-1", SUB_CANVAS)

    assert seen.get("group_id") == SUB_CANVAS, seen
