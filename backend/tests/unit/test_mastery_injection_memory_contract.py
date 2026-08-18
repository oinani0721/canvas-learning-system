"""mastery_injection.retrieve_learning_memories — 客户端方法名契约锁。

背景（2026-08-15 全项目核实发现）
--------------------------------
`retrieve_learning_memories` 曾调用 `graphiti_client.search(...)`，而它唯一的
实参来源 `nodes.py::_get_graphiti_client()` 返回的是
`agentic_rag.clients.graphiti_client.GraphitiClient` —— 该类只暴露
`search_nodes` / `search_memories`，**没有** `search`。

后果链：
    AttributeError
      → 被函数末尾的 `except Exception` 吞掉，降级为一条 logger.warning
      → 返回 ""
      → 调用方无法区分「检索失败」与「真的没有学习记忆」
即学习记忆注入自 Story 2.10 起恒为空字符串，且日志里已实际发生过。

为什么这个 bug 能活这么久 —— 以及本测试为什么必须用 autospec
----------------------------------------------------------
三个条件叠加：
  1. 形参标注是 `Optional[Any]`，静态检查完全放弃方法名校验
  2. 宽 `except Exception` 把编程错误和「无数据」压成同一个返回值
  3. 零测试覆盖

⛔ 关键：用**普通** `AsyncMock()` 写的测试**抓不到这个 bug** —— Mock 会对任意
属性名自动应答，`mock.search(...)` 与 `mock.search_memories(...)` 一样成功。
因此本文件一律用 `create_autospec(GraphitiClient)`：只有真实存在于类上的方法
才可调用，方法名一旦写错立刻 AttributeError。
"""

from __future__ import annotations

from unittest.mock import create_autospec

import pytest

from agentic_rag.clients.graphiti_client import GraphitiClient
from agentic_rag.mastery_injection import retrieve_learning_memories


def _make_strict_client(return_value):
    """严格按 GraphitiClient 真实方法面构造的 mock。

    调用类上不存在的方法（例如已修复的 `.search`）会抛 AttributeError，
    从而被本模块的断言捕获——这正是本测试的检测能力来源。
    """
    client = create_autospec(GraphitiClient, instance=True)
    client.search_memories.return_value = return_value
    return client


class TestClientMethodContract:
    """方法名契约——回归锁的核心。"""

    pytestmark = pytest.mark.asyncio

    async def test_uses_search_memories_not_bare_search(self):
        """严格 mock 下必须拿到内容；若代码调回 `.search()` 则返回空串而失败。"""
        client = _make_strict_client([{"content": "提示: 先看基线再下结论", "score": 0.9}])

        result = await retrieve_learning_memories(node_id="node-a", max_tokens=1000, graphiti_client=client)

        assert result != "", "返回空串说明检索抛异常后被 except 吞掉——极可能是又调用了 GraphitiClient 上不存在的方法"
        assert "先看基线再下结论" in result
        client.search_memories.assert_awaited_once()

    async def test_query_and_num_results_passed_as_expected(self):
        """入参形状锁：位置参数 query + 关键字 num_results=10。"""
        client = _make_strict_client([{"content": "x"}])

        await retrieve_learning_memories(node_id="node-b", max_tokens=1000, graphiti_client=client)

        args, kwargs = client.search_memories.await_args
        assert "node-b" in args[0], "查询串应包含 node_id"
        assert kwargs.get("num_results") == 10


class TestClientSurface:
    """类方法面本身的断言——同步用例，刻意与上面的 asyncio class 分开。

    （合在一起会让同步函数继承 class 级 pytestmark，触发
    "marked with '@pytest.mark.asyncio' but it is not an async function"。）
    """

    def test_graphiti_client_surface_has_no_bare_search(self):
        """钉死类的方法面本身。

        若将来有人给 GraphitiClient 加一个 `search` 别名，本断言会红——
        那时必须显式决定：是收敛到单一方法名，还是接受两个入口并更新本锁。
        """
        assert not hasattr(GraphitiClient, "search"), (
            "GraphitiClient 新增了 search 方法——请复核 retrieve_learning_memories 该调哪个，并更新本契约锁"
        )
        assert hasattr(GraphitiClient, "search_memories")
        assert hasattr(GraphitiClient, "search_nodes")


class TestContentRouting:
    """内容分类：tips / errors / 问答三栏。"""

    pytestmark = pytest.mark.asyncio

    async def test_tips_errors_qa_routed_to_separate_sections(self):
        client = _make_strict_client(
            [
                {"content": "提示: 遍历前先判空"},
                {"content": "错误: 把 basename 当稳定 ID"},
                {"content": "什么是摊还分析"},
            ]
        )

        result = await retrieve_learning_memories(node_id="node-c", max_tokens=1000, graphiti_client=client)

        assert "[历史 Tips]" in result
        assert "[历史错误]" in result
        assert "[相关问答]" in result
        assert "遍历前先判空" in result
        assert "把 basename 当稳定 ID" in result
        assert "什么是摊还分析" in result

    async def test_reads_fact_key_when_content_absent(self):
        """Graphiti 边结果用 `fact` 承载文本，也必须被识别。"""
        client = _make_strict_client([{"fact": "提示: 边也有正文"}])

        result = await retrieve_learning_memories(node_id="node-d", max_tokens=1000, graphiti_client=client)

        assert "边也有正文" in result


class TestDegradedPaths:
    """降级路径——同时记录一个已知的可观测性缺陷。"""

    pytestmark = pytest.mark.asyncio

    async def test_no_client_returns_empty(self):
        assert await retrieve_learning_memories("n", graphiti_client=None) == ""

    async def test_empty_result_returns_empty(self):
        client = _make_strict_client([])
        assert await retrieve_learning_memories("n", graphiti_client=client) == ""

    async def test_client_exception_is_swallowed_into_empty_string(self):
        """⚠️ 记录现状而非认可现状。

        客户端抛异常时函数返回 ""，与「真的没有记忆」**完全无法区分**。
        这正是原 bug 潜伏三个月的机制。此处锁住当前行为，以便将来引入
        显式失败信号（例如返回 None 或带 degraded 标记）时能立刻看到差异。
        """
        client = create_autospec(GraphitiClient, instance=True)
        client.search_memories.side_effect = RuntimeError("graphiti down")

        result = await retrieve_learning_memories("n", graphiti_client=client)

        assert result == ""
