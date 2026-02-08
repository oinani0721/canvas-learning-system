# Canvas Learning System - Integration Tests for Memory Persistence
# Story 31.A.2: 学习历史读取修复 - 跨会话持久化测试
"""
Integration tests for MemoryService cross-session persistence.

Story 31.A.2 AC-31.A.2.3: Cross-session data persistence
- Session 1: Write data via record_learning_event()
- Restart service (clear memory)
- Session 2: Read data via get_learning_history() returns Session 1 data

[Source: docs/stories/31.A.2.story.md#AC-31.A.2.3]
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.memory_service import MemoryService
from app.clients.neo4j_client import Neo4jClient


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def mock_neo4j_client_with_persistence():
    """
    Mock Neo4jClient that simulates persistent storage.

    Data written to this mock persists across "service restarts"
    (new MemoryService instances).
    """
    # Shared storage to simulate Neo4j persistence
    persistent_storage = {
        "learning_history": [],
        "relationships": []
    }

    client = MagicMock(spec=Neo4jClient)
    client._use_json_fallback = False
    client._initialized = True

    async def mock_get_learning_history(
        user_id: str,
        start_date=None,
        end_date=None,
        concept=None,
        group_id=None,
        limit=100
    ):
        """Return persistent data filtered by parameters."""
        results = [
            item for item in persistent_storage["learning_history"]
            if item.get("user_id") == user_id
        ]

        if concept:
            results = [
                r for r in results
                if concept.lower() in r.get("concept", "").lower()
            ]

        if group_id:
            results = [
                r for r in results
                if r.get("group_id") == group_id
            ]

        # Sort by timestamp (newest first)
        results.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        return results[:limit]

    async def mock_create_learning_relationship(
        user_id: str,
        concept: str,
        score=None,
        group_id=None
    ):
        """Simulate persisting learning data."""
        record = {
            "user_id": user_id,
            "concept": concept,
            "score": score,
            "group_id": group_id,
            "timestamp": datetime.now().isoformat(),
            "review_count": 0
        }
        persistent_storage["learning_history"].append(record)
        return True

    client.get_learning_history = AsyncMock(side_effect=mock_get_learning_history)
    client.create_learning_relationship = AsyncMock(side_effect=mock_create_learning_relationship)
    client.initialize = AsyncMock()
    client.close = AsyncMock()

    # Expose storage for verification
    client._test_storage = persistent_storage

    return client


@pytest.fixture
def mock_graphiti_memory():
    """Mock GraphitiLearningMemory for MemoryService."""
    memory = MagicMock()
    memory.add_learning_episode = AsyncMock()
    return memory


# =============================================================================
# AC-31.A.2.3: Cross-Session Persistence Tests
# =============================================================================

class TestCrossSessionPersistence:
    """
    Story 31.A.2 AC-31.A.2.3: Verify data persists across service restarts.

    [Source: docs/stories/31.A.2.story.md#AC-31.A.2.3]
    """

    @pytest.mark.asyncio
    async def test_learning_history_persists_across_sessions(
        self,
        mock_neo4j_client_with_persistence,
        mock_graphiti_memory
    ):
        """
        Verify learning history data persists after service restart.

        Steps:
        1. Session 1: Record learning event
        2. Destroy service (simulate restart)
        3. Session 2: Create new service, query history
        4. Verify data from Session 1 is returned
        """
        # Session 1: Write data
        service1 = MemoryService(neo4j_client=mock_neo4j_client_with_persistence)
        service1._learning_memory = mock_graphiti_memory
        await service1.initialize()

        # Record learning event (this should persist to Neo4j)
        await service1.record_learning_event(
            user_id="test-user-001",
            concept="线性代数-矩阵乘法",
            agent_type="scoring-agent",
            score=85,
            canvas_path="test/canvas.canvas",
            node_id="node-001"
        )

        # Verify data was written
        assert len(mock_neo4j_client_with_persistence._test_storage["learning_history"]) == 1

        # Session 1 cleanup (simulate service shutdown)
        await service1.cleanup()

        # Session 2: Create NEW service instance (simulating restart)
        # This service has empty self._episodes (memory cleared)
        service2 = MemoryService(neo4j_client=mock_neo4j_client_with_persistence)
        service2._learning_memory = mock_graphiti_memory
        await service2.initialize()

        # Verify memory is empty (simulating restart)
        assert len(service2._episodes) == 0

        # Query learning history - should get data from Neo4j
        result = await service2.get_learning_history(user_id="test-user-001")

        # Verify data from Session 1 is returned
        assert result["total"] == 1
        assert len(result["items"]) == 1
        assert result["items"][0]["concept"] == "线性代数-矩阵乘法"

        await service2.cleanup()

    @pytest.mark.asyncio
    async def test_data_fields_complete_after_restart(
        self,
        mock_neo4j_client_with_persistence,
        mock_graphiti_memory
    ):
        """
        Verify all data fields are preserved across restarts.

        AC-31.A.2.3: Data fields complete (concept, score, timestamp, subject)
        """
        # Write with all fields
        service1 = MemoryService(neo4j_client=mock_neo4j_client_with_persistence)
        service1._learning_memory = mock_graphiti_memory
        await service1.initialize()

        await service1.record_learning_event(
            user_id="test-user-002",
            concept="离散数学-逆否命题",
            agent_type="oral-explanation",
            score=90,
            canvas_path="test/discrete.canvas",
            node_id="node-002",
            subject="数学"
        )

        await service1.cleanup()

        # Read with new service
        service2 = MemoryService(neo4j_client=mock_neo4j_client_with_persistence)
        service2._learning_memory = mock_graphiti_memory
        await service2.initialize()

        result = await service2.get_learning_history(user_id="test-user-002")

        # Verify all fields
        assert result["total"] >= 1
        item = next(
            (i for i in result["items"] if i["concept"] == "离散数学-逆否命题"),
            None
        )
        assert item is not None
        assert item["score"] == 90
        assert "timestamp" in item

        await service2.cleanup()


# =============================================================================
# AC-31.A.2.1: Neo4j Query Priority Tests
# =============================================================================

class TestNeo4jQueryPriority:
    """
    Story 31.A.2 AC-31.A.2.1: Verify get_learning_history queries Neo4j first.

    [Source: docs/stories/31.A.2.story.md#AC-31.A.2.1]
    """

    @pytest.mark.asyncio
    async def test_queries_neo4j_first(self, mock_graphiti_memory):
        """Verify Neo4j is queried before falling back to memory."""
        mock_neo4j = MagicMock(spec=Neo4jClient)
        mock_neo4j._initialized = True
        mock_neo4j.get_learning_history = AsyncMock(return_value=[
            {"concept": "From Neo4j", "score": 100, "timestamp": "2026-02-05T10:00:00"}
        ])
        mock_neo4j.initialize = AsyncMock()

        service = MemoryService(neo4j_client=mock_neo4j)
        service._learning_memory = mock_graphiti_memory
        await service.initialize()

        # Add data to memory (should NOT be returned)
        service._episodes.append({
            "user_id": "user1",
            "concept": "From Memory",
            "score": 50
        })

        result = await service.get_learning_history(user_id="user1")

        # Neo4j should be called
        mock_neo4j.get_learning_history.assert_called_once()

        # Result should be from Neo4j, not memory
        assert result["items"][0]["concept"] == "From Neo4j"

        await service.cleanup()

    @pytest.mark.asyncio
    async def test_fallback_to_memory_on_neo4j_failure(self, mock_graphiti_memory):
        """Verify fallback to memory when Neo4j query fails."""
        mock_neo4j = MagicMock(spec=Neo4jClient)
        mock_neo4j._initialized = True
        mock_neo4j.get_learning_history = AsyncMock(
            side_effect=Exception("Neo4j connection lost")
        )
        mock_neo4j.initialize = AsyncMock()

        service = MemoryService(neo4j_client=mock_neo4j)
        service._learning_memory = mock_graphiti_memory
        await service.initialize()

        # Add data to memory (should be returned as fallback)
        service._episodes.append({
            "user_id": "user1",
            "concept": "Fallback Data",
            "score": 75,
            "timestamp": "2026-02-05T09:00:00"
        })

        result = await service.get_learning_history(user_id="user1")

        # Result should be from memory fallback
        assert result["total"] == 1
        assert result["items"][0]["concept"] == "Fallback Data"

        await service.cleanup()

    @pytest.mark.asyncio
    async def test_fallback_when_neo4j_returns_empty(self, mock_graphiti_memory):
        """Verify fallback to memory when Neo4j returns empty."""
        mock_neo4j = MagicMock(spec=Neo4jClient)
        mock_neo4j._initialized = True
        mock_neo4j.get_learning_history = AsyncMock(return_value=[])
        mock_neo4j.initialize = AsyncMock()

        service = MemoryService(neo4j_client=mock_neo4j)
        service._learning_memory = mock_graphiti_memory
        await service.initialize()

        service._episodes.append({
            "user_id": "user1",
            "concept": "Memory Only",
            "score": 60,
            "timestamp": "2026-02-05T08:00:00"
        })

        result = await service.get_learning_history(user_id="user1")

        # Neo4j returned empty, so fallback to memory
        assert result["total"] == 1
        assert result["items"][0]["concept"] == "Memory Only"

        await service.cleanup()


# =============================================================================
# AC-31.A.2.4: Filtering and Pagination Tests
# =============================================================================

class TestFilteringAndPagination:
    """
    Story 31.A.2 AC-31.A.2.4: Verify filtering and pagination work correctly.

    [Source: docs/stories/31.A.2.story.md#AC-31.A.2.4]
    """

    @pytest.mark.asyncio
    async def test_concept_filter(self, mock_graphiti_memory):
        """Verify concept filter works correctly."""
        mock_neo4j = MagicMock(spec=Neo4jClient)
        mock_neo4j._initialized = True
        mock_neo4j.get_learning_history = AsyncMock(return_value=[
            {"concept": "矩阵乘法", "score": 85, "timestamp": "2026-02-05T10:00:00"},
        ])
        mock_neo4j.initialize = AsyncMock()

        service = MemoryService(neo4j_client=mock_neo4j)
        service._learning_memory = mock_graphiti_memory
        await service.initialize()

        result = await service.get_learning_history(
            user_id="user1",
            concept="矩阵"
        )

        # Verify concept filter was passed to Neo4j
        call_args = mock_neo4j.get_learning_history.call_args
        assert call_args.kwargs["concept"] == "矩阵"

        await service.cleanup()

    @pytest.mark.asyncio
    async def test_subject_filter_uses_group_id(self, mock_graphiti_memory):
        """Verify subject filter converts to group_id."""
        mock_neo4j = MagicMock(spec=Neo4jClient)
        mock_neo4j._initialized = True
        mock_neo4j.get_learning_history = AsyncMock(return_value=[])
        mock_neo4j.initialize = AsyncMock()

        service = MemoryService(neo4j_client=mock_neo4j)
        service._learning_memory = mock_graphiti_memory
        await service.initialize()

        await service.get_learning_history(
            user_id="user1",
            subject="数学"
        )

        # Verify group_id was passed (from build_group_id)
        call_args = mock_neo4j.get_learning_history.call_args
        assert call_args.kwargs["group_id"] is not None

        await service.cleanup()

    @pytest.mark.asyncio
    async def test_pagination_parameters(self, mock_graphiti_memory):
        """Verify pagination parameters work correctly."""
        mock_neo4j = MagicMock(spec=Neo4jClient)
        mock_neo4j._initialized = True
        mock_neo4j.get_learning_history = AsyncMock(return_value=[
            {"concept": f"Concept-{i}", "score": 80, "timestamp": f"2026-02-05T{10+i}:00:00"}
            for i in range(5)
        ])
        mock_neo4j.initialize = AsyncMock()

        service = MemoryService(neo4j_client=mock_neo4j)
        service._learning_memory = mock_graphiti_memory
        await service.initialize()

        result = await service.get_learning_history(
            user_id="user1",
            page=1,
            page_size=2
        )

        # Verify pagination
        assert result["page"] == 1
        assert result["page_size"] == 2
        assert len(result["items"]) == 2

        await service.cleanup()


# =============================================================================
# Story 31.A.5 AC-31.A.5.1: REAL Neo4j Integration Tests
# These tests require Docker Neo4j service running
# Run: docker-compose up -d neo4j && pytest -m integration
# [Source: docs/stories/31.A.5.story.md#AC-31.A.5.1]
# =============================================================================

import uuid


class TestRealNeo4jPersistence:
    """
    Story 31.A.5 AC-31.A.5.1: Real Neo4j integration tests.

    Requires Docker Neo4j service:
        docker-compose up -d neo4j
        pytest backend/tests/integration/test_memory_persistence.py -m integration

    [Source: docs/stories/31.A.5.story.md#AC-31.A.5.1]
    """

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_cross_session_persistence_real_neo4j(self, real_neo4j_client):
        """
        验证跨会话数据持久化（真实 Neo4j）。

        Story 31.A.5 AC-31.A.5.1:
        - Session 1 写入数据到真实 Neo4j
        - 模拟服务重启（新建 MemoryService 实例）
        - Session 2 能从 Neo4j 读取 Session 1 的数据

        [Source: docs/stories/31.A.5.story.md#AC-31.A.5.1]
        """
        # Unique identifiers to prevent test collision
        test_user_id = f"test_user_{uuid.uuid4().hex[:8]}"
        test_concept = f"线性代数-矩阵乘法-{uuid.uuid4().hex[:6]}"
        test_node_id = f"test_node_{uuid.uuid4().hex[:8]}"

        # --- Session 1: Write data ---
        service1 = MemoryService(neo4j_client=real_neo4j_client)
        await service1.initialize()

        episode_id = await service1.record_learning_event(
            user_id=test_user_id,
            canvas_path="test/persistence/linear_algebra.canvas",
            node_id=test_node_id,
            concept=test_concept,
            agent_type="scoring",
            score=90,
            subject="数学"
        )

        assert episode_id is not None
        assert episode_id.startswith("episode-")

        # --- Simulate restart: Create new service instance ---
        # Note: service1._episodes is in-memory, service2 will have empty _episodes

        # --- Session 2: Read data with new instance ---
        service2 = MemoryService(neo4j_client=real_neo4j_client)
        await service2.initialize()

        # Verify memory is empty (simulating restart)
        assert len(service2._episodes) == 0

        # Query learning history
        result = await service2.get_learning_history(user_id=test_user_id)

        # Verify
        assert result is not None
        items = result.get("items", [])
        assert len(items) > 0, "Learning history should contain at least one item"

        # Find our specific concept
        found = any(
            item.get("concept") == test_concept
            for item in items
        )
        assert found, f"Concept '{test_concept}' should be in learning history"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_multiple_events_persist_real_neo4j(self, real_neo4j_client):
        """
        验证多个学习事件的持久化（真实 Neo4j）。

        [Source: docs/stories/31.A.5.story.md#AC-31.A.5.1]
        """
        test_user_id = f"test_user_{uuid.uuid4().hex[:8]}"
        concepts = [
            f"微积分-{uuid.uuid4().hex[:4]}",
            f"概率论-{uuid.uuid4().hex[:4]}",
            f"线性代数-{uuid.uuid4().hex[:4]}"
        ]

        # Session 1: Write multiple events
        service1 = MemoryService(neo4j_client=real_neo4j_client)
        await service1.initialize()

        for i, concept in enumerate(concepts):
            await service1.record_learning_event(
                user_id=test_user_id,
                canvas_path=f"test/persistence/canvas_{i}.canvas",
                node_id=f"test_node_{uuid.uuid4().hex[:8]}",
                concept=concept,
                agent_type="basic-decomposition",
                score=70 + i * 10
            )

        # Session 2: Verify all events
        service2 = MemoryService(neo4j_client=real_neo4j_client)
        await service2.initialize()

        result = await service2.get_learning_history(user_id=test_user_id)
        items = result.get("items", [])

        # All concepts should be found
        found_concepts = {item.get("concept") for item in items}
        for concept in concepts:
            assert concept in found_concepts, f"Missing concept: {concept}"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_subject_filter_real_neo4j(self, real_neo4j_client):
        """
        验证带学科过滤的持久化查询（真实 Neo4j）。

        Story 31.A.5 + Story 30.8: 使用 subject 参数过滤学习历史。

        [Source: docs/stories/31.A.5.story.md#AC-31.A.5.1]
        [Source: docs/stories/30.8.story.md#AC-30.8.3]
        """
        test_user_id = f"test_user_{uuid.uuid4().hex[:8]}"
        math_concept = f"微积分-{uuid.uuid4().hex[:4]}"
        physics_concept = f"量子力学-{uuid.uuid4().hex[:4]}"

        # Write events for different subjects
        service1 = MemoryService(neo4j_client=real_neo4j_client)
        await service1.initialize()

        # Math event
        await service1.record_learning_event(
            user_id=test_user_id,
            canvas_path="test/数学/calculus.canvas",
            node_id=f"test_node_{uuid.uuid4().hex[:8]}",
            concept=math_concept,
            agent_type="scoring",
            score=85,
            subject="数学"
        )

        # Physics event
        await service1.record_learning_event(
            user_id=test_user_id,
            canvas_path="test/物理/quantum.canvas",
            node_id=f"test_node_{uuid.uuid4().hex[:8]}",
            concept=physics_concept,
            agent_type="scoring",
            score=78,
            subject="物理"
        )

        # Query with subject filter
        service2 = MemoryService(neo4j_client=real_neo4j_client)
        await service2.initialize()

        # Filter by 数学
        math_result = await service2.get_learning_history(
            user_id=test_user_id,
            subject="数学"
        )
        math_items = math_result.get("items", [])

        # Should find math concept
        math_concepts = {item.get("concept") for item in math_items}
        assert math_concept in math_concepts, "Math concept should be in filtered results"
