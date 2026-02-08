# Canvas Learning System - Shared Helpers for Story 31.A.2 Tests
# Story 31.A.2: 学习历史读取修复
# [Source: docs/stories/31.A.2.story.md]
"""
Shared fixtures and helpers for Story 31.A.2 test modules.

NOT a test file — contains only helpers used by:
- test_story_31a2_ac1_neo4j_priority.py
- test_story_31a2_ac2_client_method.py
- test_story_31a2_ac3_persistence.py
- test_story_31a2_ac4_pagination.py
- test_story_31a2_ac5_api_injection.py
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.clients.neo4j_client import Neo4jClient
from app.services.memory_service import MemoryService


# =============================================================================
# Shared Fixtures
# =============================================================================

@pytest.fixture
def mock_graphiti_memory():
    """Mock LearningMemoryClient to prevent side effects."""
    memory = MagicMock()
    memory.add_learning_episode = AsyncMock()
    return memory


def _make_service(neo4j_client, graphiti_memory=None):
    """Helper to create MemoryService with mocked dependencies."""
    service = MemoryService(neo4j_client=neo4j_client)
    if graphiti_memory is None:
        graphiti_memory = MagicMock()
        graphiti_memory.add_learning_episode = AsyncMock()
    service._learning_memory = graphiti_memory
    return service


def _make_neo4j_mock(**overrides) -> MagicMock:
    """Helper to create a standard Neo4jClient mock."""
    client = MagicMock(spec=Neo4jClient)
    client._initialized = True
    client._use_json_fallback = False
    client.initialize = AsyncMock()
    client.cleanup = AsyncMock()
    client.close = AsyncMock()
    client.get_learning_history = AsyncMock(return_value=[])
    client.create_learning_relationship = AsyncMock(return_value=True)
    client.stats = {"initialized": True, "mode": "NEO4J", "health_status": True}
    for key, val in overrides.items():
        setattr(client, key, val)
    return client
