# Canvas Learning System - Neo4j Fulltext Index Tests
# Epic 4: Neo4j Fulltext Index + search_memories Completion
# Feature 4.1: Auto-create episode_content fulltext index on startup
# Feature 4.2: Verify three-tier search with tier logging
"""
Unit tests for Neo4j fulltext index creation and search_memories tier logging.

Feature 4.1: ensure_fulltext_index() creates the episode_content index
Feature 4.2: search_memories logs which tier(s) produced results

Test scenarios:
- ensure_fulltext_index runs correct Cypher CREATE FULLTEXT INDEX
- Graceful handling when Neo4j is unavailable
- Idempotent (IF NOT EXISTS means no error on re-run)
- search_memories logs tier result counts
- search_memories falls through tiers when earlier tiers return empty
"""

import logging
from unittest.mock import AsyncMock, patch

import pytest

from app.services.memory_service import MemoryService


@pytest.fixture
def mock_neo4j_client():
    """Create a mock Neo4jClient with initialized stats."""
    client = AsyncMock()
    client.initialize = AsyncMock(return_value=True)
    client.stats = {"connected": True, "mode": "NEO4J", "initialized": True}
    client.run_query = AsyncMock(return_value=[])
    client.get_all_recent_episodes = AsyncMock(return_value=[])
    return client


@pytest.fixture
def memory_service(mock_neo4j_client):
    """Create MemoryService with mocked Neo4j client."""
    svc = MemoryService(neo4j_client=mock_neo4j_client)
    return svc


class TestEnsureFulltextIndex:
    """Tests for Feature 4.1: ensure_fulltext_index()."""

    @pytest.mark.asyncio
    async def test_ensure_fulltext_index_runs_create_query(
        self, memory_service, mock_neo4j_client
    ):
        """Feature 4.1: Correct Cypher is executed to create the fulltext index."""
        await memory_service.initialize()
        await memory_service.ensure_fulltext_index()

        mock_neo4j_client.run_query.assert_called()
        # Find the call that contains the CREATE FULLTEXT INDEX statement
        calls = mock_neo4j_client.run_query.call_args_list
        create_index_called = False
        for call in calls:
            cypher = call.args[0] if call.args else call.kwargs.get("query", "")
            if "CREATE FULLTEXT INDEX" in cypher and "episode_content" in cypher:
                assert "IF NOT EXISTS" in cypher
                assert "EpisodicNode" in cypher
                assert "n.content" in cypher
                create_index_called = True
                break
        assert create_index_called, (
            "ensure_fulltext_index must run CREATE FULLTEXT INDEX episode_content"
        )

    @pytest.mark.asyncio
    async def test_ensure_fulltext_index_handles_neo4j_unavailable(
        self, memory_service, mock_neo4j_client
    ):
        """Feature 4.1: Graceful degradation when Neo4j is not initialized."""
        await memory_service.initialize()

        # Simulate Neo4j not initialized
        mock_neo4j_client.stats = {"initialized": False}

        # Should not raise, should return gracefully
        await memory_service.ensure_fulltext_index()

        # run_query should NOT be called for index creation when Neo4j is down
        # (it may have been called during initialize, so check specifically for
        # CREATE FULLTEXT INDEX)
        for call in mock_neo4j_client.run_query.call_args_list:
            cypher = call.args[0] if call.args else call.kwargs.get("query", "")
            assert "CREATE FULLTEXT INDEX" not in cypher, (
                "Should not attempt index creation when Neo4j is unavailable"
            )

    @pytest.mark.asyncio
    async def test_ensure_fulltext_index_handles_runtime_error(
        self, memory_service, mock_neo4j_client
    ):
        """Feature 4.1: Graceful handling when run_query raises RuntimeError."""
        await memory_service.initialize()
        mock_neo4j_client.run_query = AsyncMock(
            side_effect=RuntimeError("Connection refused")
        )

        # Should not propagate the exception
        await memory_service.ensure_fulltext_index()

    @pytest.mark.asyncio
    async def test_ensure_fulltext_index_idempotent(
        self, memory_service, mock_neo4j_client
    ):
        """Feature 4.1 + Round-23 Patch 3: IF NOT EXISTS means calling twice is safe.

        After Round-23 Story 7.3 Patch 3, ensure_fulltext_index creates 2 indexes:
        - episode_content (EpisodicNode.content)
        - node_search_unified (Node|EntityNode multi-field)
        So 2 calls × 2 indexes = 4 CREATE statements.
        """
        await memory_service.initialize()

        await memory_service.ensure_fulltext_index()
        await memory_service.ensure_fulltext_index()

        # Both calls should succeed without error
        create_count = 0
        for call in mock_neo4j_client.run_query.call_args_list:
            cypher = call.args[0] if call.args else call.kwargs.get("query", "")
            if "CREATE FULLTEXT INDEX" in cypher:
                create_count += 1
        assert create_count == 4, (
            "Should execute CREATE FULLTEXT INDEX each time × 2 indexes "
            "(IF NOT EXISTS handles idempotency, Round-23 Patch 3 added node_search_unified)"
        )


class TestSearchMemoriesTierLogging:
    """Tests for Feature 4.2: Tier logging in search_memories."""

    @pytest.mark.asyncio
    async def test_search_memories_logs_tier_counts(
        self, memory_service, mock_neo4j_client, caplog
    ):
        """Feature 4.2: search_memories logs tier result counts."""
        await memory_service.initialize()

        with caplog.at_level(logging.INFO, logger="app.services.memory_service"):
            results = await memory_service.search_memories(
                query="test query", group_id="test-group"
            )

        # Should contain tier logging
        tier_log_found = any(
            "Tier 1:" in record.message and "Tier 2:" in record.message
            for record in caplog.records
        )
        assert tier_log_found, (
            f"Expected tier logging in search_memories output. "
            f"Log records: {[r.message for r in caplog.records]}"
        )

    @pytest.mark.asyncio
    async def test_search_memories_falls_through_tiers(
        self, memory_service, mock_neo4j_client
    ):
        """Feature 4.2: When Tier 1 returns empty, Tier 2 is tried."""
        await memory_service.initialize()

        # Tier 2 (Neo4j fulltext) returns results
        mock_neo4j_client.run_query = AsyncMock(
            return_value=[
                {
                    "node": {
                        "episode_id": "ep-from-neo4j",
                        "content": "test content",
                        "episode_type": "learning",
                        "score": 0.9,
                        "timestamp": "2026-01-01",
                        "group_id": "test-group",
                        "node_id": "node-1",
                    },
                    "score": 0.9,
                }
            ]
        )

        # Patch _search_graphiti to return empty (simulating Tier 1 failure)
        with patch.object(
            memory_service, "_search_graphiti", new_callable=AsyncMock, return_value=[]
        ):
            results = await memory_service.search_memories(
                query="test content", group_id="test-group"
            )

        # Should have results from Tier 2
        assert len(results) >= 1
        neo4j_results = [r for r in results if r.get("source") == "neo4j_fulltext"]
        assert len(neo4j_results) >= 1, (
            "Tier 2 (Neo4j fulltext) should provide results when Tier 1 is empty"
        )

    @pytest.mark.asyncio
    async def test_search_memories_tier3_fallback(
        self, memory_service, mock_neo4j_client
    ):
        """Feature 4.2: When Tier 1 and Tier 2 both empty, Tier 3 in-memory works."""
        await memory_service.initialize()

        # Add an episode to in-memory cache
        memory_service._episodes.append(
            {
                "episode_id": "ep-inmemory-1",
                "content": "photosynthesis in plants",
                "episode_type": "learning",
                "node_id": "node-2",
                "concept": "photosynthesis",
                "group_id": "bio-group",
            }
        )

        # Patch Tier 1 and Tier 2 to return empty
        with (
            patch.object(
                memory_service,
                "_search_graphiti",
                new_callable=AsyncMock,
                return_value=[],
            ),
            patch.object(
                memory_service,
                "_search_neo4j_fulltext",
                new_callable=AsyncMock,
                return_value=[],
            ),
        ):
            results = await memory_service.search_memories(
                query="photosynthesis", group_id="bio-group"
            )

        assert len(results) >= 1
        inmem_results = [r for r in results if r.get("source") == "in_memory"]
        assert len(inmem_results) >= 1, (
            "Tier 3 (in-memory) should provide results as fallback"
        )
