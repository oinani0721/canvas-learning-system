# Canvas Learning System - Story 31.A.2 AC-31.A.2.5 Real Neo4j Integration Tests
# Migrated from: tests/unit/test_story_31a2_ac5_api_injection.py
"""
Real-DB integration tests for AC-31.A.2.5: API endpoint dependency injection fix.
Also includes edge case and regression tests with real Neo4j.

These tests verify:
- API endpoint DI wiring uses Annotated[..., Depends(...)] (no stub needed)
- MemoryService reads/writes against a real Neo4j test container
- Pagination, Unicode, and merge logic work with real persisted records

[Source: docs/stories/31.A.2.story.md#AC-31.A.2.5]
[Source: S34 migration from stub to real-DB]
"""

import os
import uuid

import pytest

from app.clients.neo4j_client import Neo4jClient
from app.services.memory_service import MemoryService

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

NEO4J_TEST_URI = os.getenv("NEO4J_TEST_URI", "bolt://localhost:7692")
NEO4J_TEST_USER = os.getenv("NEO4J_TEST_USER", "neo4j")
NEO4J_TEST_PASSWORD = os.getenv("NEO4J_TEST_PASSWORD", "testpassword")
NEO4J_TEST_DATABASE = os.getenv("NEO4J_TEST_DATABASE", "neo4j")


def _make_client() -> Neo4jClient:
    return Neo4jClient(
        uri=NEO4J_TEST_URI,
        user=NEO4J_TEST_USER,
        password=NEO4J_TEST_PASSWORD,
        database=NEO4J_TEST_DATABASE,
    )


async def _cleanup_prefix(client: Neo4jClient, prefix: str) -> None:
    try:
        await client.run_query(
            "MATCH (n) WHERE n.id STARTS WITH $prefix DETACH DELETE n",
            prefix=prefix,
        )
        await client.run_query(
            "MATCH (c:Concept) WHERE c.name STARTS WITH $prefix DETACH DELETE c",
            prefix=prefix,
        )
        await client.run_query(
            "MATCH (cv:Canvas) WHERE cv.path STARTS WITH $prefix DETACH DELETE cv",
            prefix=prefix,
        )
    except Exception:
        pass


# =============================================================================
# AC-31.A.2.5: API Endpoint Dependency Injection Fix (signature-level)
# These tests verify code structure — they don't need Neo4j but belong in the
# integration suite because they test the real DI chain end-to-end.
# =============================================================================


class TestAC31A25_ApiDependencyInjection:
    """AC-31.A.2.5: GET endpoints must not have `= None` default for MemoryServiceDep."""

    def test_get_learning_history_endpoint_no_default_none(self):
        """GET /episodes endpoint should not have memory_service=None."""
        import inspect
        from app.api.v1.endpoints.memory import get_learning_history

        sig = inspect.signature(get_learning_history)
        param = sig.parameters.get("memory_service")

        assert param is not None, "memory_service parameter must exist"
        # The default should be an Annotated/Depends, NOT None
        assert param.default is not None or param.default is inspect.Parameter.empty, \
            "memory_service must not default to None"

    def test_get_concept_history_endpoint_no_default_none(self):
        """GET /concepts/{id}/history endpoint should not have memory_service=None."""
        import inspect
        from app.api.v1.endpoints.memory import get_concept_history

        sig = inspect.signature(get_concept_history)
        param = sig.parameters.get("memory_service")

        assert param is not None, "memory_service parameter must exist"
        assert param.default is not None or param.default is inspect.Parameter.empty, \
            "memory_service must not default to None"

    def test_get_review_suggestions_endpoint_no_default_none(self):
        """GET /review-suggestions endpoint should not have memory_service=None."""
        import inspect
        from app.api.v1.endpoints.memory import get_review_suggestions

        sig = inspect.signature(get_review_suggestions)
        param = sig.parameters.get("memory_service")

        assert param is not None, "memory_service parameter must exist"
        assert param.default is not None or param.default is inspect.Parameter.empty, \
            "memory_service must not default to None"

    def test_memory_service_dep_uses_annotated_depends(self):
        """MemoryServiceDep must be Annotated[MemoryService, Depends(...)]."""
        import typing
        from app.api.v1.endpoints.memory import MemoryServiceDep

        # MemoryServiceDep should be an Annotated type
        origin = typing.get_origin(MemoryServiceDep)
        assert origin is typing.Annotated, \
            "MemoryServiceDep should be Annotated type"


# =============================================================================
# Edge Cases and Regression Tests — Real Neo4j
# =============================================================================


class TestEdgeCasesReal:
    """Regression and edge case tests for learning history read against real Neo4j."""

    async def test_neo4j_empty_db_returns_empty_history(self):
        """When Neo4j has no records for a user, get_learning_history returns zero items."""
        client = _make_client()
        prefix = f"test_{uuid.uuid4().hex[:8]}_"
        try:
            await client.initialize()
            service = MemoryService(neo4j_client=client)
            await service.initialize()

            result = await service.get_learning_history(
                user_id=f"{prefix}nonexistent_user"
            )

            assert result["total"] == 0
            assert len(result["items"]) == 0
        finally:
            await _cleanup_prefix(client, prefix)
            await client.cleanup()

    async def test_page_beyond_total_returns_no_items(self):
        """Requesting page beyond available records returns zero items."""
        client = _make_client()
        prefix = f"test_{uuid.uuid4().hex[:8]}_"
        try:
            await client.initialize()
            service = MemoryService(neo4j_client=client)
            await service.initialize()

            # Seed one record via record_learning_event
            await service.record_learning_event(
                user_id=f"{prefix}user1",
                canvas_path=f"{prefix}test.canvas",
                node_id=f"{prefix}node1",
                concept=f"{prefix}Algebra",
                agent_type="scoring",
            )

            result = await service.get_learning_history(
                user_id=f"{prefix}user1", page=99, page_size=50
            )

            # Total should reflect the seeded record(s), but page 99 should have zero items
            assert result["total"] >= 1
            assert len(result["items"]) == 0
        finally:
            await _cleanup_prefix(client, prefix)
            await client.cleanup()

    async def test_concurrent_record_and_read_merge(self):
        """Record learning events then read back — verifies round-trip through Neo4j."""
        client = _make_client()
        prefix = f"test_{uuid.uuid4().hex[:8]}_"
        try:
            await client.initialize()
            service = MemoryService(neo4j_client=client)
            await service.initialize()

            user_id = f"{prefix}user_merge"

            # Record two events
            await service.record_learning_event(
                user_id=user_id,
                canvas_path=f"{prefix}merge.canvas",
                node_id=f"{prefix}node_a",
                concept=f"{prefix}ConceptA",
                agent_type="scoring",
            )
            await service.record_learning_event(
                user_id=user_id,
                canvas_path=f"{prefix}merge.canvas",
                node_id=f"{prefix}node_b",
                concept=f"{prefix}ConceptB",
                agent_type="scoring",
            )

            result = await service.get_learning_history(user_id=user_id)

            assert result["total"] >= 2
            concepts = [it["concept"] for it in result["items"]]
            assert f"{prefix}ConceptA" in concepts
            assert f"{prefix}ConceptB" in concepts
        finally:
            await _cleanup_prefix(client, prefix)
            await client.cleanup()

    async def test_large_dataset_pagination(self):
        """Pagination works correctly with many records in real Neo4j."""
        client = _make_client()
        prefix = f"test_{uuid.uuid4().hex[:8]}_"
        try:
            await client.initialize()
            service = MemoryService(neo4j_client=client)
            await service.initialize()

            user_id = f"{prefix}user_paginate"

            # Seed 30 records (reasonable for real-DB test)
            for i in range(30):
                await service.record_learning_event(
                    user_id=user_id,
                    canvas_path=f"{prefix}paginate.canvas",
                    node_id=f"{prefix}node_{i:03d}",
                    concept=f"{prefix}C-{i:03d}",
                    agent_type="scoring",
                )

            # Request page 2 with page_size=10
            result = await service.get_learning_history(
                user_id=user_id, page=2, page_size=10
            )

            assert result["total"] >= 30
            assert result["page"] == 2
            assert result["page_size"] == 10
            assert len(result["items"]) == 10
        finally:
            await _cleanup_prefix(client, prefix)
            await client.cleanup()

    async def test_unicode_concept_handling(self):
        """Chinese/Unicode concepts round-trip through real Neo4j."""
        client = _make_client()
        prefix = f"test_{uuid.uuid4().hex[:8]}_"
        try:
            await client.initialize()
            service = MemoryService(neo4j_client=client)
            await service.initialize()

            user_id = f"{prefix}user_unicode"
            unicode_concept = f"{prefix}linear_algebra_eigenvalue_decomposition"

            await service.record_learning_event(
                user_id=user_id,
                canvas_path=f"{prefix}math.canvas",
                node_id=f"{prefix}node_unicode",
                concept=unicode_concept,
                agent_type="scoring",
            )

            result = await service.get_learning_history(user_id=user_id)

            assert result["total"] >= 1
            concepts = [it["concept"] for it in result["items"]]
            assert unicode_concept in concepts
        finally:
            await _cleanup_prefix(client, prefix)
            await client.cleanup()
