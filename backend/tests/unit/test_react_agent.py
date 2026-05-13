"""Wave-5 Stage B — react_agent.py group_id ContextVar 派生测试.

回归 P0 跨 vault 读泄漏:
``backend/app/services/react_agent.py`` 旧版 5 处硬编码 DEFAULT_GROUP_ID,
导致 ReAct agent 在 vault A 调用时读 ``vault:default`` 桶 (而非 vault:cs_61b).

修复:_resolve_effective_group_id() 优先 ContextVar 派生, 否则 fallback +
logger.warning. 模式参考 backend/app/services/error_writer.py:~520-536.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest


@pytest.fixture
def reset_react_module_state():
    """每个测试 reset module-level _neo4j_client + ContextVar."""
    from app.core.subject_config import _current_subject_id
    from app.services import react_agent as ra_module

    saved_neo4j = ra_module._neo4j_client
    token = _current_subject_id.set("general")  # DEFAULT_SUBJECT_ID
    yield
    _current_subject_id.reset(token)
    ra_module._neo4j_client = saved_neo4j


class TestReactAgentGroupIdContextVar:
    """Wave-5 Stage B P0 — group_id 必须从 ContextVar 派生 (跨 vault 隔离)."""

    @pytest.mark.asyncio
    async def test_react_agent_uses_contextvar_group_id(self, reset_react_module_state):
        """set ContextVar vault:cs_61b → 调 search_knowledge_graph →
        cypher 参数 group_id 必须是 vault:cs_61b 不是 default."""
        from app.core.subject_config import _current_subject_id
        from app.services import react_agent as ra_module
        from app.services.react_agent import search_knowledge_graph

        # mock Neo4j client (records cypher kwargs)
        mock_neo4j = AsyncMock()
        mock_neo4j.run_query = AsyncMock(return_value=[])
        ra_module._neo4j_client = mock_neo4j

        # set ContextVar vault:cs_61b (already canonical, lru_cache idempotent)
        token = _current_subject_id.set("vault:cs_61b")
        try:
            await search_knowledge_graph.ainvoke(
                {"query": "search test", "num_results": 5}
            )
        finally:
            _current_subject_id.reset(token)

        # assert cypher 调用了 + group_id kwarg == vault:cs_61b
        assert mock_neo4j.run_query.called, "search_knowledge_graph 未调用 neo4j"
        call_kwargs = mock_neo4j.run_query.call_args.kwargs
        assert call_kwargs.get("group_id") == "vault:cs_61b", (
            f"P0 violation: cypher group_id={call_kwargs.get('group_id')} "
            f"(预期 vault:cs_61b, 不能是 default)"
        )

    @pytest.mark.asyncio
    async def test_react_agent_fallback_when_no_contextvar(
        self, reset_react_module_state, caplog
    ):
        """ContextVar 未设置 (default) → fallback DEFAULT_GROUP_ID + logger.warning."""
        import logging

        from app.config import DEFAULT_GROUP_ID
        from app.services import react_agent as ra_module
        from app.services.react_agent import search_knowledge_graph

        mock_neo4j = AsyncMock()
        mock_neo4j.run_query = AsyncMock(return_value=[])
        ra_module._neo4j_client = mock_neo4j

        # 不 set ContextVar — fixture 已 reset 到 DEFAULT_SUBJECT_ID ("general")
        with caplog.at_level(logging.WARNING):
            await search_knowledge_graph.ainvoke(
                {"query": "fallback test", "num_results": 3}
            )

        # cypher 收到 DEFAULT_GROUP_ID fallback
        assert mock_neo4j.run_query.called
        call_kwargs = mock_neo4j.run_query.call_args.kwargs
        assert call_kwargs.get("group_id") == DEFAULT_GROUP_ID, (
            f"fallback path 应使用 DEFAULT_GROUP_ID={DEFAULT_GROUP_ID}, "
            f"实际 group_id={call_kwargs.get('group_id')}"
        )

        # logger.warning 必须触发 (结构化日志)
        warning_records = [
            r
            for r in caplog.records
            if "react_agent.group_id_fallback_to_default" in r.getMessage()
            or "react_agent.group_id_fallback_to_default" in str(r.msg)
        ]
        assert warning_records, (
            "fallback path 必须 logger.warning 提示调用方注入 ContextVar"
        )

    @pytest.mark.asyncio
    async def test_record_learning_memory_uses_contextvar_group_id(
        self, reset_react_module_state
    ):
        """写入路径同样必须用 ContextVar — record_learning_memory cypher
        参数 groupId 必须是 vault:数学 不是 default."""
        from app.core.subject_config import _current_subject_id
        from app.services import react_agent as ra_module
        from app.services.react_agent import record_learning_memory

        mock_neo4j = AsyncMock()
        mock_neo4j.run_query = AsyncMock(return_value=[])
        ra_module._neo4j_client = mock_neo4j

        token = _current_subject_id.set("vault:数学")
        try:
            await record_learning_memory.ainvoke(
                {
                    "entity_type": "Misconception",
                    "concept": "ContextVarTest",
                    "topic": "Search",
                    "details": {
                        "error": "学生混淆 A 和 B",
                        "correct": "A 和 B 是不同概念",
                    },
                }
            )
        finally:
            _current_subject_id.reset(token)

        assert mock_neo4j.run_query.called
        call_kwargs = mock_neo4j.run_query.call_args.kwargs
        # record_learning_memory uses groupId (camelCase) not group_id
        assert call_kwargs.get("groupId") == "vault:数学", (
            f"P0 write violation: cypher groupId={call_kwargs.get('groupId')} "
            f"(预期 vault:数学)"
        )
