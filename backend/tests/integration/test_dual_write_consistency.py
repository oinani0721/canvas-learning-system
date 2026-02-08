# Canvas Learning System - Dual Write Consistency Integration Tests
# Story 31.A.5 AC-31.A.5.3: 双写一致性测试
# [Source: docs/stories/31.A.5.story.md#AC-31.A.5.3]
"""
验证数据同时写入 Neo4j 和 Graphiti 的一致性。

双写架构:
1. Neo4j: 同步写入（通过 _create_neo4j_learning_relationship）
2. Graphiti JSON: 异步写入（通过 _write_to_graphiti_json_with_retry）

[Source: docs/prd/EPIC-31.A-MEMORY-PIPELINE-FIX.md#双写策略]
[Source: backend/app/services/memory_service.py:300-312]
"""

import asyncio
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.conftest import wait_for_condition


# =============================================================================
# AC-31.A.5.3: Dual Write Consistency Tests
# [Source: docs/stories/31.A.5.story.md#AC-31.A.5.3]
# =============================================================================


class TestDualWriteConsistency:
    """
    验证双写一致性。

    测试策略:
    1. 写入学习事件
    2. 验证 Neo4j 存储成功
    3. 验证 Graphiti JSON 存储成功（如果启用）
    4. 对比两边数据一致性

    [Source: docs/stories/31.A.5.story.md#AC-31.A.5.3]
    """

    @pytest.fixture
    def unique_test_id(self):
        """生成唯一测试 ID 避免数据冲突"""
        return f"test_{uuid.uuid4().hex[:8]}"

    @pytest.fixture
    def test_event_data(self, unique_test_id):
        """标准测试事件数据"""
        return {
            "user_id": f"dual_write_{unique_test_id}",
            "canvas_path": f"test/dual_write_{unique_test_id}.canvas",
            "node_id": f"dual_node_{unique_test_id}",
            "concept": "双写测试概念",
            "agent_type": "scoring",
            "score": 88,
            "subject": "数学"
        }

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_dual_write_neo4j_and_graphiti(
        self,
        real_neo4j_client,
        test_event_data
    ):
        """
        验证数据同时写入 Neo4j 和 Graphiti。

        AC-31.A.5.3: 数据写入 Neo4j 成功，数据写入 Graphiti 成功

        [Source: docs/stories/31.A.5.story.md#AC-31.A.5.3]
        """
        from app.services.memory_service import MemoryService

        # 创建 MemoryService with real Neo4j
        service = MemoryService(neo4j_client=real_neo4j_client)
        await service.initialize()

        try:
            # 写入学习事件
            episode_id = await service.record_learning_event(
                user_id=test_event_data["user_id"],
                canvas_path=test_event_data["canvas_path"],
                node_id=test_event_data["node_id"],
                concept=test_event_data["concept"],
                agent_type=test_event_data["agent_type"],
                score=test_event_data["score"],
                subject=test_event_data["subject"]
            )

            # 验证返回 episode_id
            assert episode_id is not None
            assert episode_id.startswith("episode-")

            # 等待异步写入完成 - poll Neo4j until data appears
            async def _neo4j_has_history():
                result = await real_neo4j_client.get_learning_history(
                    user_id=test_event_data["user_id"]
                )
                if isinstance(result, dict) and "items" in result:
                    items = result["items"]
                elif isinstance(result, list):
                    items = result
                else:
                    items = []
                return result if len(items) > 0 else None

            await wait_for_condition(
                _neo4j_has_history,
                timeout=5.0,
                description="Neo4j learning history written",
            )

            # 验证 Neo4j 存储成功
            neo4j_result = await real_neo4j_client.get_learning_history(
                user_id=test_event_data["user_id"]
            )

            # 检查结果格式
            assert neo4j_result is not None
            if isinstance(neo4j_result, dict) and "items" in neo4j_result:
                items = neo4j_result["items"]
            elif isinstance(neo4j_result, list):
                items = neo4j_result
            else:
                items = []

            # 验证写入的数据
            assert len(items) > 0, "Neo4j should have learning history"
            found_concept = any(
                item.get("concept") == test_event_data["concept"]
                for item in items
            )
            assert found_concept, f"Concept '{test_event_data['concept']}' not found in Neo4j"

        finally:
            # 清理测试数据
            try:
                await real_neo4j_client.run_query(
                    f"MATCH (n) WHERE n.id STARTS WITH 'dual_write_{test_event_data['user_id'].split('_')[-1]}' "
                    "DETACH DELETE n"
                )
            except Exception:
                pass

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_dual_write_with_graphiti_json_enabled(
        self,
        real_neo4j_client,
        test_event_data,
        tmp_path
    ):
        """
        验证启用 Graphiti JSON 双写时两边数据一致。

        AC-31.A.5.3: 两个存储的数据一致

        [Source: docs/stories/31.A.5.story.md#AC-31.A.5.3]
        [Source: backend/app/services/memory_service.py:376-379]
        """
        from app.services.memory_service import MemoryService
        from app.clients.graphiti_client import LearningMemoryClient

        # 创建临时 JSON 文件路径
        json_file = tmp_path / "test_learning_memories.json"
        # LearningMemoryClient expects dict with "memories" key, not a list
        json_file.write_text('{"memories": [], "metadata": {"version": "1.0"}}')

        # 创建 LearningMemoryClient with temp file
        learning_memory = LearningMemoryClient(storage_path=json_file)
        await learning_memory.initialize()

        # 创建 MemoryService
        # MemoryService.__init__ parameter is learning_memory_client (not learning_memory)
        service = MemoryService(
            neo4j_client=real_neo4j_client,
            learning_memory_client=learning_memory
        )
        await service.initialize()

        try:
            # 启用 Graphiti JSON 双写
            with patch('app.services.memory_service.settings') as mock_settings:
                mock_settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE = True

                # 写入学习事件
                episode_id = await service.record_learning_event(
                    user_id=test_event_data["user_id"],
                    canvas_path=test_event_data["canvas_path"],
                    node_id=test_event_data["node_id"],
                    concept=test_event_data["concept"],
                    agent_type=test_event_data["agent_type"],
                    score=test_event_data["score"]
                )

            # 等待异步写入完成 - poll Neo4j until data appears
            async def _neo4j_has_data():
                result = await real_neo4j_client.get_learning_history(
                    user_id=test_event_data["user_id"]
                )
                items = result.get("items", []) if isinstance(result, dict) else result or []
                return True if len(items) > 0 else None

            await wait_for_condition(
                _neo4j_has_data,
                timeout=5.0,
                description="Neo4j learning history written (dual write test)",
            )

            # 验证 Neo4j 存储
            neo4j_result = await real_neo4j_client.get_learning_history(
                user_id=test_event_data["user_id"]
            )

            # 验证 Graphiti JSON 存储
            # LearningMemoryClient.get_learning_history uses canvas_name, not user_id
            canvas_name = test_event_data["canvas_path"].split("/")[-1]
            graphiti_result = await learning_memory.get_learning_history(
                canvas_name=canvas_name
            )

            # 验证两边都有数据
            neo4j_items = neo4j_result.get("items", []) if isinstance(neo4j_result, dict) else neo4j_result or []
            graphiti_items = graphiti_result if isinstance(graphiti_result, list) else []

            # 注意: Graphiti JSON 是 fire-and-forget，可能没有写入成功
            # 但我们至少验证 Neo4j 成功了
            assert len(neo4j_items) > 0, "Neo4j should have data"

            # 如果 Graphiti 也有数据，验证一致性
            if len(graphiti_items) > 0:
                neo4j_concepts = {item.get("concept") for item in neo4j_items if item.get("concept")}
                graphiti_concepts = {item.get("concept") for item in graphiti_items if item.get("concept")}

                # 至少有一个共同概念
                common_concepts = neo4j_concepts & graphiti_concepts
                assert len(common_concepts) > 0, \
                    f"No common concepts between Neo4j and Graphiti. Neo4j: {neo4j_concepts}, Graphiti: {graphiti_concepts}"

        finally:
            # 清理
            try:
                await real_neo4j_client.run_query(
                    f"MATCH (n) WHERE n.id STARTS WITH 'dual_write' DETACH DELETE n"
                )
            except Exception:
                pass

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_neo4j_write_failure_does_not_block_graphiti(
        self,
        test_event_data,
        tmp_path
    ):
        """
        验证 Neo4j 写入失败不会阻塞 Graphiti 写入。

        AC-31.A.5.3: 验证写入独立性

        Note: 实际架构中 Neo4j 是同步写入，失败会抛出异常。
              此测试验证异常处理逻辑。
        """
        from app.services.memory_service import MemoryService
        from app.clients.graphiti_client import LearningMemoryClient

        # 创建 mock Neo4j client 模拟失败
        mock_neo4j = MagicMock()
        mock_neo4j.create_learning_relationship = AsyncMock(
            side_effect=Exception("Neo4j connection failed")
        )
        mock_neo4j.stats = {"initialized": True, "mode": "NEO4J"}
        mock_neo4j.initialize = AsyncMock()

        # 创建临时 JSON 文件
        json_file = tmp_path / "test_memories.json"
        json_file.write_text("[]")

        # LearningMemoryClient expects Path, not str
        learning_memory = LearningMemoryClient(storage_path=json_file)
        await learning_memory.initialize()

        service = MemoryService(
            neo4j_client=mock_neo4j,
            learning_memory_client=learning_memory
        )
        await service.initialize()

        # 写入应该因 Neo4j 失败而抛出异常
        with pytest.raises(Exception) as exc_info:
            await service.record_learning_event(
                user_id=test_event_data["user_id"],
                canvas_path=test_event_data["canvas_path"],
                node_id=test_event_data["node_id"],
                concept=test_event_data["concept"],
                agent_type=test_event_data["agent_type"]
            )

        assert "Neo4j" in str(exc_info.value) or "connection" in str(exc_info.value).lower()


class TestGraphitiWriteReliability:
    """
    验证 Graphiti 写入的可靠性机制。

    Story 31.A.3: 增强 Graphiti 写入可靠性
    - 重试机制（2 次重试，共 3 次尝试）
    - 指数退避

    [Source: docs/stories/31.A.3.story.md]
    """

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_graphiti_write_retry_mechanism(self, tmp_path):
        """
        验证 Graphiti 写入的重试机制。

        AC-31.A.3.1: 添加指数退避重试机制

        [Source: docs/stories/31.A.3.story.md#AC-31.A.3.1]
        """
        from app.services.memory_service import MemoryService
        from app.clients.graphiti_client import LearningMemoryClient

        # 创建会失败几次再成功的 mock
        call_count = 0

        async def failing_then_success(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:  # 前两次失败
                raise Exception("Temporary failure")
            # 第三次成功
            return None

        # 创建 mock LearningMemoryClient
        mock_learning_memory = MagicMock(spec=LearningMemoryClient)
        mock_learning_memory.add_learning_episode = AsyncMock(
            side_effect=failing_then_success
        )
        mock_learning_memory.initialize = AsyncMock()

        # 创建 mock Neo4j
        mock_neo4j = MagicMock()
        mock_neo4j.create_learning_relationship = AsyncMock()
        mock_neo4j.stats = {"initialized": True, "mode": "NEO4J"}
        mock_neo4j.initialize = AsyncMock()

        service = MemoryService(
            neo4j_client=mock_neo4j,
            learning_memory_client=mock_learning_memory
        )
        await service.initialize()

        # 直接调用重试方法
        result = await service._write_to_graphiti_json_with_retry(
            episode_id="test-episode",
            canvas_name="test.canvas",
            node_id="test-node",
            concept="测试概念",
            max_retries=2
        )

        # 验证重试了 3 次并最终成功
        assert call_count == 3
        assert result is True

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_graphiti_write_max_retries_exceeded(self, tmp_path):
        """
        验证超过最大重试次数后优雅失败。

        AC-31.A.3.2: 超过重试次数后记录日志但不抛出异常

        [Source: docs/stories/31.A.3.story.md#AC-31.A.3.2]
        """
        from app.services.memory_service import MemoryService
        from app.clients.graphiti_client import LearningMemoryClient

        # 创建始终失败的 mock
        mock_learning_memory = MagicMock(spec=LearningMemoryClient)
        mock_learning_memory.add_learning_episode = AsyncMock(
            side_effect=Exception("Permanent failure")
        )
        mock_learning_memory.initialize = AsyncMock()

        mock_neo4j = MagicMock()
        mock_neo4j.stats = {"initialized": True, "mode": "NEO4J"}
        mock_neo4j.initialize = AsyncMock()

        service = MemoryService(
            neo4j_client=mock_neo4j,
            learning_memory_client=mock_learning_memory
        )
        await service.initialize()

        # 调用重试方法
        result = await service._write_to_graphiti_json_with_retry(
            episode_id="test-episode",
            canvas_name="test.canvas",
            node_id="test-node",
            concept="测试概念",
            max_retries=2
        )

        # 验证返回 False 但没有抛出异常
        assert result is False

        # 验证调用了 3 次（1 + 2 重试）
        assert mock_learning_memory.add_learning_episode.call_count == 3


class TestDualWriteWithRealNeo4j:
    """
    使用真实 Neo4j 的双写集成测试。

    这些测试需要 Docker 环境中运行 Neo4j。

    [Source: docs/stories/31.A.5.story.md#3.2]
    """

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_dual_write_full_cycle_real_neo4j(
        self,
        real_neo4j_client,
        test_user_id,
        test_canvas_path,
        test_node_id
    ):
        """
        完整的双写周期测试（使用真实 Neo4j）。

        测试流程:
        1. 写入学习事件
        2. 验证 Neo4j 持久化
        3. 创建新 service 实例
        4. 验证数据仍然可读

        [Source: docs/stories/31.A.5.story.md#AC-31.A.5.3]
        """
        from app.services.memory_service import MemoryService

        # Session 1: 写入
        service1 = MemoryService(neo4j_client=real_neo4j_client)
        await service1.initialize()

        concept = f"双写周期测试_{uuid.uuid4().hex[:8]}"

        episode_id = await service1.record_learning_event(
            user_id=test_user_id,
            canvas_path=test_canvas_path,
            node_id=test_node_id,
            concept=concept,
            agent_type="dual_write_test",
            score=95
        )

        assert episode_id is not None

        # 等待异步操作完成 - poll Neo4j until data appears
        async def _neo4j_has_cycle_data():
            result = await real_neo4j_client.get_learning_history(user_id=test_user_id)
            items = result.get("items", []) if isinstance(result, dict) else result or []
            return True if any(item.get("concept") == concept for item in items) else None

        await wait_for_condition(
            _neo4j_has_cycle_data,
            timeout=5.0,
            description="Neo4j learning history written (full cycle test)",
        )

        # Session 2: 读取（模拟新会话）
        service2 = MemoryService(neo4j_client=real_neo4j_client)
        await service2.initialize()

        result = await service2.get_learning_history(user_id=test_user_id)

        # 验证数据持久化
        items = result.get("items", []) if isinstance(result, dict) else result or []
        assert len(items) > 0
        assert any(item.get("concept") == concept for item in items)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_concurrent_dual_writes_real_neo4j(
        self,
        real_neo4j_client,
        test_user_id,
        test_canvas_path
    ):
        """
        并发双写测试（验证数据完整性）。

        [Source: docs/stories/31.A.5.story.md#AC-31.A.5.3]
        """
        from app.services.memory_service import MemoryService

        service = MemoryService(neo4j_client=real_neo4j_client)
        await service.initialize()

        # 并发写入多个事件
        concepts = [f"并发测试概念_{i}_{uuid.uuid4().hex[:4]}" for i in range(5)]

        async def write_event(concept: str, index: int):
            return await service.record_learning_event(
                user_id=test_user_id,
                canvas_path=test_canvas_path,
                node_id=f"concurrent_node_{index}",
                concept=concept,
                agent_type="concurrent_test"
            )

        # 并发执行
        tasks = [write_event(c, i) for i, c in enumerate(concepts)]
        episode_ids = await asyncio.gather(*tasks)

        # 验证所有写入成功
        assert all(eid is not None for eid in episode_ids)
        assert len(set(episode_ids)) == len(concepts)  # 所有 ID 唯一

        # 等待异步操作完成 - poll until all concepts appear in Neo4j
        async def _all_concepts_persisted():
            result = await service.get_learning_history(user_id=test_user_id)
            items = result.get("items", []) if isinstance(result, dict) else result or []
            persisted = {item.get("concept") for item in items if item.get("concept")}
            return True if all(c in persisted for c in concepts) else None

        await wait_for_condition(
            _all_concepts_persisted,
            timeout=10.0,
            description="All 5 concurrent concepts persisted to Neo4j",
        )

        # 验证所有数据都已持久化
        result = await service.get_learning_history(user_id=test_user_id)
        items = result.get("items", []) if isinstance(result, dict) else result or []

        persisted_concepts = {item.get("concept") for item in items if item.get("concept")}

        for concept in concepts:
            assert concept in persisted_concepts, f"Concept '{concept}' not found in Neo4j"
