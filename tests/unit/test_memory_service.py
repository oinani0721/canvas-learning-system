# Canvas Learning System - Memory Service Unit Tests
# Story 22.4: 学习历史存储与查询API (AC-22.4.6)
# ✅ Verified from docs/stories/22.4.story.md#测试要求
"""
Unit tests for MemoryService.

Test Coverage:
- record_learning_event: 记录学习事件
- get_learning_history: 获取学习历史 (分页)
- get_concept_history: 查询概念学习历史
- get_review_suggestions: 获取复习建议

[Source: docs/stories/22.4.story.md#测试要求]
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import structlog

logger = structlog.get_logger(__name__)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def mock_neo4j_client():
    """Mock Neo4jClient for testing."""
    client = MagicMock()
    client._initialized = False
    client.stats = {"queries_executed": 0}

    async def mock_initialize():
        client._initialized = True
        return True

    async def mock_cleanup():
        client._initialized = False

    async def mock_create_learning_relationship(user_id: str, concept: str, score: int = None):
        return True

    async def mock_get_review_suggestions(user_id: str, limit: int = 10):
        return [
            {
                "concept": "逆否命题",
                "concept_id": "concept-001",
                "last_score": 75,
                "review_count": 2,
                "due_date": datetime.now().isoformat(),
                "priority": "high"
            },
            {
                "concept": "命题逻辑",
                "concept_id": "concept-002",
                "last_score": 85,
                "review_count": 4,
                "due_date": datetime.now().isoformat(),
                "priority": "medium"
            }
        ]

    async def mock_get_concept_history(concept_id: str, user_id: str = None, limit: int = 50):
        return [
            {
                "timestamp": datetime.now().isoformat(),
                "score": 85,
                "user_id": user_id or "user-001",
                "concept": "逆否命题",
                "review_count": 3
            },
            {
                "timestamp": (datetime.now() - timedelta(days=1)).isoformat(),
                "score": 75,
                "user_id": user_id or "user-001",
                "concept": "逆否命题",
                "review_count": 2
            }
        ]

    client.initialize = AsyncMock(side_effect=mock_initialize)
    client.cleanup = AsyncMock(side_effect=mock_cleanup)
    client.create_learning_relationship = AsyncMock(side_effect=mock_create_learning_relationship)
    client.get_review_suggestions = AsyncMock(side_effect=mock_get_review_suggestions)
    client.get_concept_history = AsyncMock(side_effect=mock_get_concept_history)

    return client


@pytest.fixture
def memory_service(mock_neo4j_client):
    """Create MemoryService with mocked Neo4j client."""
    from app.services.memory_service import MemoryService
    service = MemoryService(neo4j_client=mock_neo4j_client)
    return service


# =============================================================================
# Test: record_learning_event (AC-22.4.1)
# ✅ Verified from docs/stories/22.4.story.md#record_learning_event
# =============================================================================


class TestRecordLearningEvent:
    """Tests for record_learning_event method."""

    @pytest.mark.asyncio
    async def test_record_learning_event_success(self, memory_service, mock_neo4j_client):
        """Test successful recording of learning event."""
        # Arrange
        user_id = "user-001"
        canvas_path = "数学/离散数学.canvas"
        node_id = "node-abc123"
        concept = "逆否命题"
        agent_type = "scoring-agent"
        score = 85
        duration_seconds = 300

        # Act
        episode_id = await memory_service.record_learning_event(
            user_id=user_id,
            canvas_path=canvas_path,
            node_id=node_id,
            concept=concept,
            agent_type=agent_type,
            score=score,
            duration_seconds=duration_seconds
        )

        # Assert
        assert episode_id is not None
        assert episode_id.startswith("episode-")
        mock_neo4j_client.create_learning_relationship.assert_called_once_with(
            user_id=user_id,
            concept=concept,
            score=score
        )

    @pytest.mark.asyncio
    async def test_record_learning_event_without_score(self, memory_service, mock_neo4j_client):
        """Test recording learning event without score."""
        # Act
        episode_id = await memory_service.record_learning_event(
            user_id="user-001",
            canvas_path="数学/离散数学.canvas",
            node_id="node-abc123",
            concept="命题逻辑",
            agent_type="basic-decomposition"
        )

        # Assert
        assert episode_id is not None
        mock_neo4j_client.create_learning_relationship.assert_called_once()
        call_kwargs = mock_neo4j_client.create_learning_relationship.call_args.kwargs
        assert call_kwargs["score"] is None

    @pytest.mark.asyncio
    async def test_record_learning_event_stores_in_memory(self, memory_service):
        """Test that episode is stored in memory list."""
        # Act
        episode_id = await memory_service.record_learning_event(
            user_id="user-001",
            canvas_path="数学/离散数学.canvas",
            node_id="node-abc123",
            concept="逆否命题",
            agent_type="scoring-agent",
            score=80
        )

        # Assert - Check internal episodes list
        assert len(memory_service._episodes) == 1
        episode = memory_service._episodes[0]
        assert episode["episode_id"] == episode_id
        assert episode["user_id"] == "user-001"
        assert episode["concept"] == "逆否命题"
        assert episode["score"] == 80


# =============================================================================
# Test: get_learning_history (AC-22.4.2, AC-22.4.5)
# ✅ Verified from docs/stories/22.4.story.md#get_learning_history
# =============================================================================


class TestGetLearningHistory:
    """Tests for get_learning_history method."""

    @pytest.mark.asyncio
    async def test_get_learning_history_basic(self, memory_service):
        """Test basic learning history retrieval."""
        # Arrange - Add some episodes first
        await memory_service.record_learning_event(
            user_id="user-001",
            canvas_path="数学/离散数学.canvas",
            node_id="node-001",
            concept="逆否命题",
            agent_type="scoring-agent",
            score=85
        )
        await memory_service.record_learning_event(
            user_id="user-001",
            canvas_path="数学/离散数学.canvas",
            node_id="node-002",
            concept="命题逻辑",
            agent_type="basic-decomposition",
            score=90
        )

        # Act
        result = await memory_service.get_learning_history(user_id="user-001")

        # Assert
        assert "items" in result
        assert "total" in result
        assert "page" in result
        assert "page_size" in result
        assert "pages" in result
        assert result["total"] == 2
        assert len(result["items"]) == 2

    @pytest.mark.asyncio
    async def test_get_learning_history_pagination(self, memory_service):
        """Test pagination support (AC-22.4.5)."""
        # Arrange - Add 5 episodes
        for i in range(5):
            await memory_service.record_learning_event(
                user_id="user-001",
                canvas_path="数学/离散数学.canvas",
                node_id=f"node-{i:03d}",
                concept=f"Concept {i}",
                agent_type="scoring-agent",
                score=70 + i * 5
            )

        # Act - Get page 1 with page_size 2
        result = await memory_service.get_learning_history(
            user_id="user-001",
            page=1,
            page_size=2
        )

        # Assert
        assert result["total"] == 5
        assert len(result["items"]) == 2
        assert result["page"] == 1
        assert result["page_size"] == 2
        assert result["pages"] == 3  # ceil(5/2) = 3

    @pytest.mark.asyncio
    async def test_get_learning_history_concept_filter(self, memory_service):
        """Test concept filtering."""
        # Arrange
        await memory_service.record_learning_event(
            user_id="user-001",
            canvas_path="数学/离散数学.canvas",
            node_id="node-001",
            concept="逆否命题",
            agent_type="scoring-agent"
        )
        await memory_service.record_learning_event(
            user_id="user-001",
            canvas_path="数学/离散数学.canvas",
            node_id="node-002",
            concept="命题逻辑",
            agent_type="scoring-agent"
        )

        # Act
        result = await memory_service.get_learning_history(
            user_id="user-001",
            concept="逆否"
        )

        # Assert
        assert result["total"] == 1
        assert result["items"][0]["concept"] == "逆否命题"

    @pytest.mark.asyncio
    async def test_get_learning_history_empty_for_other_user(self, memory_service):
        """Test that history is filtered by user_id."""
        # Arrange
        await memory_service.record_learning_event(
            user_id="user-001",
            canvas_path="数学/离散数学.canvas",
            node_id="node-001",
            concept="逆否命题",
            agent_type="scoring-agent"
        )

        # Act
        result = await memory_service.get_learning_history(user_id="user-002")

        # Assert
        assert result["total"] == 0
        assert len(result["items"]) == 0


# =============================================================================
# Test: get_concept_history (AC-22.4.3)
# ✅ Verified from AC-22.4.3
# =============================================================================


class TestGetConceptHistory:
    """Tests for get_concept_history method."""

    @pytest.mark.asyncio
    async def test_get_concept_history_success(self, memory_service, mock_neo4j_client):
        """Test successful concept history retrieval."""
        # Act
        result = await memory_service.get_concept_history(
            concept_id="concept-001",
            user_id="user-001"
        )

        # Assert
        assert "concept_id" in result
        assert "timeline" in result
        assert "score_trend" in result
        assert "total_reviews" in result
        assert result["concept_id"] == "concept-001"
        assert len(result["timeline"]) == 2
        mock_neo4j_client.get_concept_history.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_concept_history_score_trend(self, memory_service):
        """Test score trend calculation."""
        # Act
        result = await memory_service.get_concept_history(concept_id="concept-001")

        # Assert
        score_trend = result["score_trend"]
        assert "first" in score_trend
        assert "last" in score_trend
        assert "average" in score_trend
        assert "improvement" in score_trend
        # First score is 75, last is 85, improvement should be 10
        assert score_trend["improvement"] == 10


# =============================================================================
# Test: get_review_suggestions (AC-22.4.4)
# ✅ Verified from docs/stories/22.4.story.md#get_review_suggestions
# =============================================================================


class TestGetReviewSuggestions:
    """Tests for get_review_suggestions method."""

    @pytest.mark.asyncio
    async def test_get_review_suggestions_success(self, memory_service, mock_neo4j_client):
        """Test successful review suggestions retrieval."""
        # Act
        suggestions = await memory_service.get_review_suggestions(
            user_id="user-001",
            limit=10
        )

        # Assert
        assert len(suggestions) == 2
        assert suggestions[0]["concept"] == "逆否命题"
        assert suggestions[0]["priority"] == "high"
        mock_neo4j_client.get_review_suggestions.assert_called_once_with(
            user_id="user-001",
            limit=10
        )

    @pytest.mark.asyncio
    async def test_get_review_suggestions_with_limit(self, memory_service, mock_neo4j_client):
        """Test review suggestions with custom limit."""
        # Act
        await memory_service.get_review_suggestions(
            user_id="user-001",
            limit=5
        )

        # Assert
        mock_neo4j_client.get_review_suggestions.assert_called_once_with(
            user_id="user-001",
            limit=5
        )


# =============================================================================
# Test: Service Lifecycle
# =============================================================================


class TestServiceLifecycle:
    """Tests for service initialization and cleanup."""

    @pytest.mark.asyncio
    async def test_initialize(self, memory_service, mock_neo4j_client):
        """Test service initialization."""
        # Act
        result = await memory_service.initialize()

        # Assert
        assert result is True
        assert memory_service._initialized is True
        mock_neo4j_client.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup(self, memory_service, mock_neo4j_client):
        """Test service cleanup."""
        # Arrange
        await memory_service.initialize()

        # Act
        await memory_service.cleanup()

        # Assert
        assert memory_service._initialized is False
        mock_neo4j_client.cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_stats(self, memory_service):
        """Test get_stats method."""
        # Arrange
        await memory_service.record_learning_event(
            user_id="user-001",
            canvas_path="test.canvas",
            node_id="node-001",
            concept="Test",
            agent_type="test-agent"
        )

        # Act
        stats = memory_service.get_stats()

        # Assert
        assert "initialized" in stats
        assert "total_episodes" in stats
        assert "neo4j_stats" in stats
        assert stats["total_episodes"] == 1


# =============================================================================
# Test: Error Handling
# =============================================================================


class TestErrorHandling:
    """Tests for error handling scenarios."""

    @pytest.mark.asyncio
    async def test_record_learning_event_neo4j_failure(self, memory_service, mock_neo4j_client):
        """Test handling of Neo4j failure during record."""
        # Arrange
        mock_neo4j_client.create_learning_relationship = AsyncMock(
            side_effect=Exception("Neo4j connection failed")
        )

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await memory_service.record_learning_event(
                user_id="user-001",
                canvas_path="test.canvas",
                node_id="node-001",
                concept="Test",
                agent_type="test-agent"
            )

        assert "Neo4j connection failed" in str(exc_info.value)
