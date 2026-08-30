"""mastery_injection.retrieve_learning_memories — 检索契约与降级信号锁。

演进史
------
**v1（2026-08-15）**：锁「方法名必须是 search_memories 不是 search」。
`retrieve_learning_memories` 曾调 `graphiti_client.search(...)`，而 GraphitiClient
只暴露 `search_nodes` / `search_memories` —— AttributeError 被宽 except 吞成 ""，
与「真的没有记忆」无法区分，该缺陷自 Story 2.10 起潜伏三个月。

**v2（2026-08-19，Codex 对抗审查 P1-03）**：核验发现方法名只是表层。

  Codex 指出唯一生产调用传的是 `canvas_file` 而非 Canvas node ID。独立核验进一步
  证明 **改对 node_id 也修不好**：

    - 结构化主图上 node 身份只存在于 `uuid5(node_id:group_id)` 的
      source/target_node_uuid 与边的 `attributes["node_id"]` 里；边的 `fact`
      文本只有批注正文 —— 语义检索 fact 永远筛不出特定 node
    - 唯一把 `Node: {node_id}` 写成可检索文本的 add_episode 路径，被
      episode_worker 强制落到 `vault__x__semantic` 影子组；而读侧
      `GraphitiClient._resolve_group_ids(None)` 只返回 `["vault__x"]` 单组
    - 即：**没有任何字符串形态能命中**

  用户裁定改走 MemoryService 范式（node_id 当语义提示词 + 三组同查 + 关键词过滤），
  并把「检索失败」与「真的没有记忆」显式区分开。

本文件锁的是 v2 语义。

⛔ 关于 mock 的说明（回应审查对 DD-03 的质疑）
--------------------------------------------
`create_autospec` 在此**不是**用来假装功能可用，而是**契约锁的检测能力来源**：
普通 `AsyncMock` 对任意属性名都应答，`mock.search(...)` 与 `mock.search_memories(...)`
一样成功 —— 那样根本抓不到 v1 那个 bug。autospec 只允许调用类上真实存在的方法。

真实服务的端到端验收属于另一层（需要 Neo4j + Graphiti 实例），不在单测范围。
本文件不声称「召回有效」，只声称「调用形状、分组传递与降级信号符合契约」。
"""

from __future__ import annotations

from unittest.mock import AsyncMock, create_autospec

import pytest

from agentic_rag.clients.graphiti_client import GraphitiClient
from agentic_rag.mastery_injection import (
    MEMORY_DEGRADED_ERROR,
    MEMORY_DEGRADED_NO_CLIENT,
    MEMORY_DEGRADED_TIMEOUT,
    retrieve_learning_memories,
)


@pytest.fixture
def no_memory_service(monkeypatch):
    """强制 MemoryService 路径不可用，让测试走 GraphitiClient 降级路径。"""

    async def _unavailable(*_a, **_kw):
        return None

    monkeypatch.setattr("agentic_rag.mastery_injection._search_via_memory_service", _unavailable)


def _strict_client(return_value):
    client = create_autospec(GraphitiClient, instance=True)
    client.search_memories.return_value = return_value
    return client


# ── 返回值契约：(text, degraded_reason) ───────────────────────────────────


class TestReturnShape:
    pytestmark = pytest.mark.asyncio

    async def test_returns_tuple_of_text_and_reason(self, no_memory_service):
        client = _strict_client([{"content": "提示: 先看基线再下结论"}])

        result = await retrieve_learning_memories("n", graphiti_client=client)

        assert isinstance(result, tuple) and len(result) == 2, (
            "必须返回 (text, degraded_reason) —— 单个 str 无法区分失败与无数据"
        )

    async def test_success_carries_none_reason(self, no_memory_service):
        client = _strict_client([{"content": "提示: 先看基线再下结论"}])

        text, reason = await retrieve_learning_memories("n", graphiti_client=client)

        assert "先看基线再下结论" in text
        assert reason is None, "检索成功时 reason 必须是 None"

    async def test_genuinely_empty_is_not_degraded(self, no_memory_service):
        """⛔ 核心区分：检索成功但零命中 → 空串 + reason=None。"""
        client = _strict_client([])

        text, reason = await retrieve_learning_memories("n", graphiti_client=client)

        assert text == ""
        assert reason is None, "「真的没有记忆」不得被标记为降级"


# ── 降级信号：三种失败各有其因 ─────────────────────────────────────────────


class TestDegradedSignals:
    pytestmark = pytest.mark.asyncio

    async def test_no_client_reports_degraded(self, no_memory_service):
        """MemoryService 与 Graphiti 都没有 → 显式 no_client，而非静默空串。"""
        text, reason = await retrieve_learning_memories("n", graphiti_client=None)

        assert text == ""
        assert reason == MEMORY_DEGRADED_NO_CLIENT

    async def test_client_exception_reports_degraded(self, no_memory_service):
        """⛔ 这正是 v1 那个 bug 的表现形式 —— 现在它必须可见。"""
        client = create_autospec(GraphitiClient, instance=True)
        client.search_memories.side_effect = RuntimeError("graphiti down")

        text, reason = await retrieve_learning_memories("n", graphiti_client=client)

        assert text == ""
        assert reason == MEMORY_DEGRADED_ERROR, (
            "客户端抛异常必须返回 degraded —— 与「没有记忆」返回同样的值正是该缺陷潜伏三个月的机制"
        )

    async def test_timeout_reports_degraded(self, no_memory_service):
        import asyncio

        client = create_autospec(GraphitiClient, instance=True)

        async def _hang(*_a, **_kw):
            await asyncio.sleep(10)

        client.search_memories.side_effect = _hang

        text, reason = await retrieve_learning_memories("n", graphiti_client=client)

        assert text == ""
        assert reason == MEMORY_DEGRADED_TIMEOUT


# ── MemoryService 优先路径 ─────────────────────────────────────────────────


class TestMemoryServicePreferred:
    pytestmark = pytest.mark.asyncio

    async def test_memory_service_result_is_used_without_touching_graphiti(self, monkeypatch):
        """MemoryService 可用时不应再直连 Graphiti（后者召回面窄一层）。"""

        async def _hits(node_id, group_id, limit=10):
            # CARD-G4-2: helper 契约改为 (条目, 降级原因) — 无降级时 reason=None
            return [{"content": "提示: 来自 MemoryService 的三组同查"}], None

        monkeypatch.setattr("agentic_rag.mastery_injection._search_via_memory_service", _hits)
        client = _strict_client([{"content": "不该被用到"}])

        text, reason = await retrieve_learning_memories("n", graphiti_client=client, group_id="vault__x")

        assert "三组同查" in text
        assert reason is None
        client.search_memories.assert_not_awaited()

    async def test_group_id_is_forwarded(self, monkeypatch):
        """⛔ group_id 必须透传 —— MemoryService 在 group_id=None 时会跨 vault 全组检索。"""
        seen = {}

        async def _capture(node_id, group_id, limit=10):
            seen["group_id"] = group_id
            seen["node_id"] = node_id
            return [], None

        monkeypatch.setattr("agentic_rag.mastery_injection._search_via_memory_service", _capture)

        await retrieve_learning_memories("node-a", graphiti_client=None, group_id="vault__cs_61b")

        assert seen["group_id"] == "vault__cs_61b", "group_id 未透传 —— MemoryService 会退化成跨 vault 全组检索"
        assert seen["node_id"] == "node-a"


# ── 内容分栏（沿用 v1，行为未变） ──────────────────────────────────────────


class TestContentRouting:
    pytestmark = pytest.mark.asyncio

    async def test_tips_errors_qa_routed_to_separate_sections(self, no_memory_service):
        client = _strict_client(
            [
                {"content": "提示: 遍历前先判空"},
                {"content": "错误: 把 basename 当稳定 ID"},
                {"content": "什么是摊还分析"},
            ]
        )

        text, reason = await retrieve_learning_memories("n", graphiti_client=client)

        assert reason is None
        assert "[历史 Tips]" in text and "遍历前先判空" in text
        assert "[历史错误]" in text and "把 basename 当稳定 ID" in text
        assert "[相关问答]" in text and "什么是摊还分析" in text

    async def test_reads_fact_key_when_content_absent(self, no_memory_service):
        """Graphiti 边结果用 `fact` 承载文本（降级路径仍可能遇到）。"""
        client = _strict_client([{"fact": "提示: 边也有正文"}])

        text, _ = await retrieve_learning_memories("n", graphiti_client=client)

        assert "边也有正文" in text


# ── 类方法面（v1 契约锁，继续保留） ────────────────────────────────────────


class TestClientSurface:
    """同步用例，刻意与上面的 asyncio class 分开。"""

    def test_graphiti_client_surface_has_no_bare_search(self):
        assert not hasattr(GraphitiClient, "search"), (
            "GraphitiClient 新增了 search 方法——请复核降级路径该调哪个，并更新本锁"
        )
        assert hasattr(GraphitiClient, "search_memories")
        assert hasattr(GraphitiClient, "search_nodes")

    def test_plain_mock_would_not_catch_method_name_bug(self):
        """自证本文件为何必须用 autospec —— 普通 Mock 对错误方法名照样应答。

        这条锁的是**测试方法论**：若将来有人把 create_autospec 换成 AsyncMock，
        方法名契约就失去检测能力，而测试仍会全绿。
        """
        loose = AsyncMock()
        assert loose.search is not None, "普通 Mock 对任意属性名都应答（这正是问题）"

        strict = create_autospec(GraphitiClient, instance=True)
        with pytest.raises(AttributeError):
            _ = strict.search
