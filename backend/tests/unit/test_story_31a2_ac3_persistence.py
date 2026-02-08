# Canvas Learning System - Story 31.A.2 AC-31.A.2.3 Tests
# Story 31.A.2: 学习历史读取修复
# [Source: docs/stories/31.A.2.story.md]
"""
Tests for AC-31.A.2.3: Cross-session data persistence.

[Source: docs/stories/31.A.2.story.md#AC-31.A.2.3]
"""

from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import AsyncMock

import pytest

from tests.unit.test_story_31a2_helpers import _make_neo4j_mock, _make_service


# =============================================================================
# AC-31.A.2.3: Cross-Session Data Persistence
# [Source: docs/stories/31.A.2.story.md#AC-31.A.2.3]
# =============================================================================

class TestAC31A23_CrossSessionPersistence:
    """AC-31.A.2.3: Data must persist across service restarts."""

    @pytest.fixture
    def persistent_neo4j(self):
        """Neo4j mock with shared persistent storage."""
        storage: List[Dict[str, Any]] = []

        mock = _make_neo4j_mock()

        async def mock_create_rel(user_id, concept, score=None, group_id=None):
            storage.append({
                "user_id": user_id,
                "concept": concept,
                "score": score,
                "group_id": group_id,
                "timestamp": datetime.now().isoformat(),
                "review_count": 0,
            })
            return True

        async def mock_get_history(user_id, start_date=None, end_date=None,
                                   concept=None, group_id=None, limit=100):
            return [
                item for item in storage
                if item.get("user_id") == user_id
            ][:limit]

        mock.create_learning_relationship = AsyncMock(side_effect=mock_create_rel)
        mock.get_learning_history = AsyncMock(side_effect=mock_get_history)
        mock._storage = storage
        return mock

    @pytest.mark.asyncio
    async def test_session1_write_session2_read(self, persistent_neo4j):
        """Data written in session 1 is readable in session 2."""
        # Session 1: Write
        svc1 = _make_service(persistent_neo4j)
        await svc1.initialize()
        await svc1.record_learning_event(
            user_id="u1", canvas_path="test/a.canvas", node_id="n1",
            concept="线性代数", agent_type="scoring", score=85
        )
        await svc1.cleanup()

        # Session 2: Read (fresh instance, empty _episodes)
        svc2 = _make_service(persistent_neo4j)
        await svc2.initialize()
        assert len(svc2._episodes) == 0, "Memory should be empty on new instance"

        result = await svc2.get_learning_history(user_id="u1")

        assert result["total"] >= 1
        found = any(i["concept"] == "线性代数" for i in result["items"])
        assert found, "Session 1 data should be accessible in session 2"

    @pytest.mark.asyncio
    async def test_data_fields_complete(self, persistent_neo4j):
        """All critical fields survive cross-session read."""
        svc1 = _make_service(persistent_neo4j)
        await svc1.initialize()
        await svc1.record_learning_event(
            user_id="u1", canvas_path="test/b.canvas", node_id="n2",
            concept="概率论", agent_type="oral-explanation",
            score=92, subject="数学"
        )
        await svc1.cleanup()

        svc2 = _make_service(persistent_neo4j)
        await svc2.initialize()
        result = await svc2.get_learning_history(user_id="u1")

        item = next(
            (i for i in result["items"] if i["concept"] == "概率论"), None
        )
        assert item is not None
        assert item["score"] == 92
        assert "timestamp" in item

    @pytest.mark.asyncio
    async def test_multiple_events_persist(self, persistent_neo4j):
        """Multiple events from session 1 all persist to session 2."""
        svc1 = _make_service(persistent_neo4j)
        await svc1.initialize()

        concepts = ["微积分", "线性代数", "离散数学"]
        for c in concepts:
            await svc1.record_learning_event(
                user_id="u1", canvas_path="test/c.canvas", node_id="n3",
                concept=c, agent_type="scoring", score=80
            )
        await svc1.cleanup()

        svc2 = _make_service(persistent_neo4j)
        await svc2.initialize()
        result = await svc2.get_learning_history(user_id="u1")

        found_concepts = {i["concept"] for i in result["items"]}
        for c in concepts:
            assert c in found_concepts, f"Missing concept: {c}"
