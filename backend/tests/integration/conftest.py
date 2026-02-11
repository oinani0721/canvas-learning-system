"""
Shared fixtures and helpers for Story 38.7 integration tests.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock


def make_mock_neo4j(*, episodes=None, health_ok=True, fail_write=False):
    """Create a mock Neo4jClient with configurable behavior."""
    mock = AsyncMock()
    mock.initialize = AsyncMock()
    mock.health_check = AsyncMock(return_value=health_ok)
    mock.stats = {"initialized": True, "node_count": 10, "edge_count": 5, "episode_count": 3}
    mock.get_all_recent_episodes = AsyncMock(return_value=episodes or [])
    mock.get_learning_history = AsyncMock(return_value=[])
    if fail_write:
        mock.record_episode_to_neo4j = AsyncMock(side_effect=Exception("Neo4j connection refused"))
    else:
        mock.record_episode_to_neo4j = AsyncMock(return_value=True)
    return mock


def make_mock_learning_memory():
    """Create a mock LearningMemoryClient."""
    mock = MagicMock()
    mock.add_memory = MagicMock()
    mock.save = MagicMock()
    return mock
