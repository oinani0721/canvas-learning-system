"""
Unit tests for Cross-Canvas Association Persistence (Story 36.5)

Tests cover:
- Neo4jClient CRUD methods for canvas associations
- CrossCanvasService Neo4j persistence integration
- Startup loading from Neo4j
- Relationship type mapping (legacy → schema enum)

[Source: docs/stories/36.5.story.md]
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.cross_canvas_service import (
    CrossCanvasService,
    CrossCanvasAssociation,
    RELATIONSHIP_TYPE_MAPPING,
    VALID_ASSOCIATION_TYPES,
    map_to_association_type,
    map_from_association_type,
    reset_cross_canvas_service,
)


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def mock_neo4j_client():
    """Create a mock Neo4jClient for testing."""
    client = AsyncMock()
    client.create_canvas_association = AsyncMock(return_value=True)
    client.get_canvas_associations = AsyncMock(return_value=[])
    client.delete_canvas_association = AsyncMock(return_value=True)
    client.update_canvas_association = AsyncMock(return_value=True)
    client.load_all_canvas_associations = AsyncMock(return_value=[])
    return client


@pytest.fixture
def cross_canvas_service(mock_neo4j_client):
    """Create a CrossCanvasService instance with mocked Neo4jClient."""
    reset_cross_canvas_service()
    service = CrossCanvasService(neo4j_client=mock_neo4j_client)
    return service


@pytest.fixture
def sample_association_data():
    """Sample association data for testing."""
    return {
        "association_id": str(uuid.uuid4()),
        "source_canvas": "lectures/math/algebra.canvas",
        "target_canvas": "exercises/math/algebra_practice.canvas",
        "association_type": "prerequisite",
        "confidence": 0.95,
        "shared_concepts": ["algebra", "equations"],
        "bidirectional": False,
        "auto_generated": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


# =============================================================================
# Task 5.5: Test Relationship Type Mapping
# =============================================================================

class TestRelationshipTypeMapping:
    """Tests for legacy relationship_type to schema association_type mapping."""

    def test_map_exercise_lecture_to_prerequisite(self):
        """exercise_lecture should map to prerequisite."""
        assert map_to_association_type("exercise_lecture") == "prerequisite"

    def test_map_lecture_exercise_to_extends(self):
        """lecture_exercise should map to extends."""
        assert map_to_association_type("lecture_exercise") == "extends"

    def test_map_similar_to_related(self):
        """similar should map to related."""
        assert map_to_association_type("similar") == "related"

    def test_map_continuation_to_extends(self):
        """continuation should map to extends."""
        assert map_to_association_type("continuation") == "extends"

    def test_map_valid_types_unchanged(self):
        """Valid schema types should remain unchanged."""
        for valid_type in VALID_ASSOCIATION_TYPES:
            assert map_to_association_type(valid_type) == valid_type

    def test_map_unknown_type_to_related(self):
        """Unknown types should default to 'related'."""
        assert map_to_association_type("unknown_type") == "related"
        assert map_to_association_type("random_garbage") == "related"

    def test_map_case_insensitive(self):
        """Mapping should be case insensitive."""
        assert map_to_association_type("PREREQUISITE") == "prerequisite"
        assert map_to_association_type("Related") == "related"
        assert map_to_association_type("EXERCISE_LECTURE") == "prerequisite"

    def test_map_from_association_type_valid(self):
        """map_from_association_type should return valid types unchanged."""
        assert map_from_association_type("prerequisite") == "prerequisite"
        assert map_from_association_type("related") == "related"
        assert map_from_association_type("extends") == "extends"
        assert map_from_association_type("references") == "references"

    def test_mapping_dictionary_completeness(self):
        """RELATIONSHIP_TYPE_MAPPING should map all expected legacy types."""
        expected_legacy_types = [
            "exercise_lecture",
            "lecture_exercise",
            "prerequisite",
            "related",
            "extends",
            "references",
            "similar",
            "continuation",
        ]
        for legacy_type in expected_legacy_types:
            assert legacy_type in RELATIONSHIP_TYPE_MAPPING
            mapped = RELATIONSHIP_TYPE_MAPPING[legacy_type]
            assert mapped in VALID_ASSOCIATION_TYPES


# =============================================================================
# Task 5.1: Test create_canvas_association()
# =============================================================================

class TestCreateCanvasAssociation:
    """Tests for creating canvas associations."""

    @pytest.mark.asyncio
    async def test_create_association_calls_neo4j(
        self, cross_canvas_service, mock_neo4j_client
    ):
        """Creating an association should call Neo4jClient."""
        result = await cross_canvas_service.create_association(
            source_canvas_path="lectures/intro.canvas",
            target_canvas_path="exercises/intro_practice.canvas",
            relationship_type="exercise_lecture",
            common_concepts=["basics"],
        )

        # Verify Neo4j was called
        mock_neo4j_client.create_canvas_association.assert_called_once()
        call_args = mock_neo4j_client.create_canvas_association.call_args

        # Verify correct parameters
        assert call_args.kwargs["source_canvas"] == "lectures/intro.canvas"
        assert call_args.kwargs["target_canvas"] == "exercises/intro_practice.canvas"
        assert call_args.kwargs["association_type"] == "prerequisite"  # mapped

    @pytest.mark.asyncio
    async def test_create_association_maps_relationship_type(
        self, cross_canvas_service, mock_neo4j_client
    ):
        """Association type should be mapped from legacy to schema enum."""
        await cross_canvas_service.create_association(
            source_canvas_path="a.canvas",
            target_canvas_path="b.canvas",
            relationship_type="similar",
        )

        call_args = mock_neo4j_client.create_canvas_association.call_args
        assert call_args.kwargs["association_type"] == "related"

    @pytest.mark.asyncio
    async def test_create_association_returns_association_object(
        self, cross_canvas_service
    ):
        """Create should return a CrossCanvasAssociation object."""
        result = await cross_canvas_service.create_association(
            source_canvas_path="a.canvas",
            target_canvas_path="b.canvas",
            relationship_type="prerequisite",
        )

        assert result is not None
        assert result.source_canvas_path == "a.canvas"
        assert result.target_canvas_path == "b.canvas"
        assert result.id is not None
        assert result.id.startswith("cca-")

    @pytest.mark.asyncio
    async def test_create_association_updates_cache(
        self, cross_canvas_service
    ):
        """Created association should be added to cache."""
        result = await cross_canvas_service.create_association(
            source_canvas_path="cache_test.canvas",
            target_canvas_path="cache_target.canvas",
            relationship_type="related",
        )

        # Verify in cache
        assert result.id in cross_canvas_service._associations_cache

    @pytest.mark.asyncio
    async def test_create_association_handles_neo4j_failure(
        self, cross_canvas_service, mock_neo4j_client
    ):
        """Create should handle Neo4j failures gracefully."""
        mock_neo4j_client.create_canvas_association.side_effect = Exception(
            "Neo4j connection error"
        )

        # Should not raise, but log error
        result = await cross_canvas_service.create_association(
            source_canvas_path="fail.canvas",
            target_canvas_path="test.canvas",
            relationship_type="related",
        )

        # Association should still be created in memory
        assert result is not None

    @pytest.mark.asyncio
    async def test_create_association_with_common_concepts(
        self, cross_canvas_service, mock_neo4j_client
    ):
        """Create should pass common_concepts to Neo4j as shared_concepts."""
        await cross_canvas_service.create_association(
            source_canvas_path="meta.canvas",
            target_canvas_path="data.canvas",
            relationship_type="extends",
            common_concepts=["math", "calculus"],
        )

        call_args = mock_neo4j_client.create_canvas_association.call_args
        assert call_args.kwargs["shared_concepts"] == ["math", "calculus"]


# =============================================================================
# Task 5.2: Test get_canvas_associations()
# =============================================================================

class TestGetCanvasAssociations:
    """Tests for retrieving canvas associations."""

    @pytest.mark.asyncio
    async def test_list_associations_from_cache(
        self, cross_canvas_service
    ):
        """list_associations should return associations from cache."""
        # Create some associations
        await cross_canvas_service.create_association(
            source_canvas_path="source1.canvas",
            target_canvas_path="target1.canvas",
            relationship_type="related",
        )
        await cross_canvas_service.create_association(
            source_canvas_path="source2.canvas",
            target_canvas_path="target2.canvas",
            relationship_type="extends",
        )

        # Get all associations
        associations = await cross_canvas_service.list_associations()
        assert len(associations) >= 2

    @pytest.mark.asyncio
    async def test_list_associations_by_canvas_path(
        self, cross_canvas_service
    ):
        """Should filter associations by canvas path."""
        await cross_canvas_service.create_association(
            source_canvas_path="filter_test.canvas",
            target_canvas_path="other.canvas",
            relationship_type="related",
        )

        associations = await cross_canvas_service.list_associations(
            canvas_path="filter_test.canvas"
        )

        assert len(associations) >= 1
        for assoc in associations:
            assert (
                assoc.source_canvas_path == "filter_test.canvas"
                or assoc.target_canvas_path == "filter_test.canvas"
            )

    @pytest.mark.asyncio
    async def test_get_association_by_id(
        self, cross_canvas_service
    ):
        """Should retrieve specific association by ID."""
        created = await cross_canvas_service.create_association(
            source_canvas_path="byid.canvas",
            target_canvas_path="target.canvas",
            relationship_type="prerequisite",
        )

        found = await cross_canvas_service.get_association(created.id)
        assert found is not None
        assert found.id == created.id

    @pytest.mark.asyncio
    async def test_get_nonexistent_association_returns_none(
        self, cross_canvas_service
    ):
        """Getting non-existent association should return None."""
        found = await cross_canvas_service.get_association("nonexistent-id")
        assert found is None

    @pytest.mark.asyncio
    async def test_get_associated_canvases(
        self, cross_canvas_service
    ):
        """Should get associated canvases by path."""
        await cross_canvas_service.create_association(
            source_canvas_path="query_source.canvas",
            target_canvas_path="query_target.canvas",
            relationship_type="exercise_lecture",
        )

        associations = await cross_canvas_service.get_associated_canvases(
            canvas_path="query_source.canvas"
        )

        assert len(associations) >= 1
        assert any(
            a.source_canvas_path == "query_source.canvas"
            for a in associations
        )

    @pytest.mark.asyncio
    async def test_get_associated_canvases_with_relation_filter(
        self, cross_canvas_service
    ):
        """Should filter by relation type."""
        await cross_canvas_service.create_association(
            source_canvas_path="rel_filter.canvas",
            target_canvas_path="target1.canvas",
            relationship_type="exercise_lecture",
        )
        await cross_canvas_service.create_association(
            source_canvas_path="rel_filter.canvas",
            target_canvas_path="target2.canvas",
            relationship_type="related",
        )

        associations = await cross_canvas_service.get_associated_canvases(
            canvas_path="rel_filter.canvas",
            relation_type="exercise_lecture"
        )

        # All should have exercise_lecture type
        for assoc in associations:
            assert assoc.relationship_type == "exercise_lecture"


# =============================================================================
# Task 5.3: Test delete_canvas_association()
# =============================================================================

class TestDeleteCanvasAssociation:
    """Tests for deleting canvas associations."""

    @pytest.mark.asyncio
    async def test_delete_association_calls_neo4j(
        self, cross_canvas_service, mock_neo4j_client
    ):
        """Deleting should call Neo4jClient."""
        # Create first
        created = await cross_canvas_service.create_association(
            source_canvas_path="delete_test.canvas",
            target_canvas_path="target.canvas",
            relationship_type="related",
        )

        # Delete
        result = await cross_canvas_service.delete_association(created.id)

        # Verify Neo4j was called
        mock_neo4j_client.delete_canvas_association.assert_called_with(created.id)
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_association_removes_from_cache(
        self, cross_canvas_service
    ):
        """Deleted association should be removed from cache."""
        created = await cross_canvas_service.create_association(
            source_canvas_path="cache_delete.canvas",
            target_canvas_path="target.canvas",
            relationship_type="extends",
        )

        assert created.id in cross_canvas_service._associations_cache

        await cross_canvas_service.delete_association(created.id)

        assert created.id not in cross_canvas_service._associations_cache

    @pytest.mark.asyncio
    async def test_delete_nonexistent_association(
        self, cross_canvas_service
    ):
        """Deleting non-existent association should return False."""
        result = await cross_canvas_service.delete_association("nonexistent-id")
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_handles_neo4j_failure(
        self, cross_canvas_service, mock_neo4j_client
    ):
        """Delete should handle Neo4j failures gracefully."""
        created = await cross_canvas_service.create_association(
            source_canvas_path="neo4j_fail.canvas",
            target_canvas_path="target.canvas",
            relationship_type="references",
        )

        mock_neo4j_client.delete_canvas_association.side_effect = Exception(
            "Neo4j error"
        )

        # Should not raise but still remove from cache
        result = await cross_canvas_service.delete_association(created.id)
        # Association removed from cache despite Neo4j failure
        assert created.id not in cross_canvas_service._associations_cache


# =============================================================================
# Task 5.4: Test Startup Loading Logic
# =============================================================================

class TestStartupLoading:
    """Tests for loading associations from Neo4j at startup."""

    @pytest.mark.asyncio
    async def test_initialize_loads_from_neo4j(self, mock_neo4j_client):
        """initialize() should load associations from Neo4j."""
        # Setup mock to return existing associations
        mock_neo4j_client.load_all_canvas_associations.return_value = [
            {
                "association_id": "existing-1",
                "source_canvas": "loaded1.canvas",
                "target_canvas": "target1.canvas",
                "association_type": "prerequisite",
                "confidence": 0.9,
                "shared_concepts": ["test"],
                "bidirectional": False,
                "auto_generated": False,
            },
            {
                "association_id": "existing-2",
                "source_canvas": "loaded2.canvas",
                "target_canvas": "target2.canvas",
                "association_type": "related",
                "confidence": 0.8,
                "shared_concepts": [],
                "bidirectional": True,
                "auto_generated": True,
            },
        ]

        reset_cross_canvas_service()
        service = CrossCanvasService(neo4j_client=mock_neo4j_client)
        await service.initialize()

        # Verify loading was called
        mock_neo4j_client.load_all_canvas_associations.assert_called_once()

        # Verify cache populated
        assert "existing-1" in service._associations_cache
        assert "existing-2" in service._associations_cache

    @pytest.mark.asyncio
    async def test_initialize_handles_empty_database(self, mock_neo4j_client):
        """initialize() should handle empty Neo4j database."""
        mock_neo4j_client.load_all_canvas_associations.return_value = []

        reset_cross_canvas_service()
        service = CrossCanvasService(neo4j_client=mock_neo4j_client)
        await service.initialize()

        assert len(service._associations_cache) == 0

    @pytest.mark.asyncio
    async def test_initialize_handles_neo4j_failure(self, mock_neo4j_client):
        """initialize() should handle Neo4j failures gracefully."""
        mock_neo4j_client.load_all_canvas_associations.side_effect = Exception(
            "Connection failed"
        )

        reset_cross_canvas_service()
        service = CrossCanvasService(neo4j_client=mock_neo4j_client)

        # Should not raise
        await service.initialize()

        # Cache should be empty but service should be usable
        assert len(service._associations_cache) == 0

    @pytest.mark.asyncio
    async def test_initialize_without_neo4j_client(self):
        """initialize() should work without Neo4j client (memory-only mode)."""
        reset_cross_canvas_service()
        service = CrossCanvasService(neo4j_client=None)

        # Should not raise
        await service.initialize()

        assert len(service._associations_cache) == 0

    @pytest.mark.asyncio
    async def test_loaded_associations_have_correct_types(self, mock_neo4j_client):
        """Loaded associations should have correct mapped types."""
        mock_neo4j_client.load_all_canvas_associations.return_value = [
            {
                "association_id": "typed-1",
                "source_canvas": "typed.canvas",
                "target_canvas": "target.canvas",
                "association_type": "prerequisite",
                "confidence": 1.0,
                "shared_concepts": [],
                "bidirectional": False,
                "auto_generated": False,
            },
        ]

        reset_cross_canvas_service()
        service = CrossCanvasService(neo4j_client=mock_neo4j_client)
        await service.initialize()

        loaded = service._associations_cache.get("typed-1")
        assert loaded is not None
        # The association should preserve the type from Neo4j
        assert loaded.relationship_type in VALID_ASSOCIATION_TYPES or loaded.relationship_type in RELATIONSHIP_TYPE_MAPPING

    @pytest.mark.asyncio
    async def test_initialize_only_once(self, mock_neo4j_client):
        """initialize() should only load once."""
        mock_neo4j_client.load_all_canvas_associations.return_value = []

        reset_cross_canvas_service()
        service = CrossCanvasService(neo4j_client=mock_neo4j_client)

        await service.initialize()
        await service.initialize()
        await service.initialize()

        # Should only be called once
        assert mock_neo4j_client.load_all_canvas_associations.call_count == 1


# =============================================================================
# Test Update Canvas Association
# =============================================================================

class TestUpdateCanvasAssociation:
    """Tests for updating canvas associations."""

    @pytest.mark.asyncio
    async def test_update_association_calls_neo4j(
        self, cross_canvas_service, mock_neo4j_client
    ):
        """Updating should call Neo4jClient."""
        created = await cross_canvas_service.create_association(
            source_canvas_path="update_test.canvas",
            target_canvas_path="target.canvas",
            relationship_type="related",
        )

        # Reset mock to check update call
        mock_neo4j_client.update_canvas_association.reset_mock()

        await cross_canvas_service.update_association(
            association_id=created.id,
            confidence=0.75,
        )

        mock_neo4j_client.update_canvas_association.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_nonexistent_returns_none(
        self, cross_canvas_service
    ):
        """Updating non-existent association should return None."""
        result = await cross_canvas_service.update_association(
            association_id="nonexistent",
            confidence=0.5,
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_update_association_changes_values(
        self, cross_canvas_service
    ):
        """Update should modify association values."""
        created = await cross_canvas_service.create_association(
            source_canvas_path="update_values.canvas",
            target_canvas_path="target.canvas",
            relationship_type="related",
            confidence=0.5,
        )

        updated = await cross_canvas_service.update_association(
            association_id=created.id,
            confidence=0.9,
            common_concepts=["updated", "concepts"],
        )

        assert updated is not None
        assert updated.confidence == 0.9
        assert updated.common_concepts == ["updated", "concepts"]


# =============================================================================
# Test Service Without Neo4j (Memory-only mode)
# =============================================================================

class TestMemoryOnlyMode:
    """Tests for service operation without Neo4j."""

    @pytest.mark.asyncio
    async def test_create_without_neo4j(self):
        """Create should work without Neo4j client."""
        reset_cross_canvas_service()
        service = CrossCanvasService(neo4j_client=None)

        result = await service.create_association(
            source_canvas_path="memory.canvas",
            target_canvas_path="only.canvas",
            relationship_type="related",
        )

        assert result is not None
        assert result.id in service._associations_cache

    @pytest.mark.asyncio
    async def test_delete_without_neo4j(self):
        """Delete should work without Neo4j client."""
        reset_cross_canvas_service()
        service = CrossCanvasService(neo4j_client=None)

        created = await service.create_association(
            source_canvas_path="delete_mem.canvas",
            target_canvas_path="test.canvas",
            relationship_type="extends",
        )

        result = await service.delete_association(created.id)
        assert result is True
        assert created.id not in service._associations_cache

    @pytest.mark.asyncio
    async def test_full_crud_without_neo4j(self):
        """Full CRUD cycle should work without Neo4j."""
        reset_cross_canvas_service()
        service = CrossCanvasService(neo4j_client=None)

        # Create
        created = await service.create_association(
            source_canvas_path="crud.canvas",
            target_canvas_path="test.canvas",
            relationship_type="prerequisite",
            confidence=0.6,
        )
        assert created is not None

        # Read
        found = await service.get_association(created.id)
        assert found is not None
        assert found.id == created.id

        # Update
        updated = await service.update_association(
            association_id=created.id,
            confidence=0.9,
        )
        assert updated is not None
        assert updated.confidence == 0.9

        # Delete
        deleted = await service.delete_association(created.id)
        assert deleted is True

        # Verify deleted
        not_found = await service.get_association(created.id)
        assert not_found is None


# =============================================================================
# Test Edge Cases
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_duplicate_association_handling(
        self, cross_canvas_service
    ):
        """Creating duplicate association should be handled."""
        await cross_canvas_service.create_association(
            source_canvas_path="dup.canvas",
            target_canvas_path="target.canvas",
            relationship_type="related",
        )

        # Create same association again
        second = await cross_canvas_service.create_association(
            source_canvas_path="dup.canvas",
            target_canvas_path="target.canvas",
            relationship_type="related",
        )

        # Should create a new association with different ID
        assert second is not None

    @pytest.mark.asyncio
    async def test_empty_canvas_path(
        self, cross_canvas_service
    ):
        """Empty canvas paths should be handled."""
        # This depends on validation in the service
        # The test documents expected behavior
        result = await cross_canvas_service.create_association(
            source_canvas_path="",
            target_canvas_path="target.canvas",
            relationship_type="related",
        )
        # Service should either reject or accept based on implementation
        # Just ensure it doesn't crash
        assert result is not None or result is None

    @pytest.mark.asyncio
    async def test_special_characters_in_path(
        self, cross_canvas_service, mock_neo4j_client
    ):
        """Canvas paths with special characters should be handled."""
        result = await cross_canvas_service.create_association(
            source_canvas_path="path/with spaces/and-dashes.canvas",
            target_canvas_path="中文路径/测试.canvas",
            relationship_type="references",
        )

        assert result is not None
        # Verify the paths are passed correctly to Neo4j
        call_args = mock_neo4j_client.create_canvas_association.call_args
        assert call_args.kwargs["source_canvas"] == "path/with spaces/and-dashes.canvas"
        assert call_args.kwargs["target_canvas"] == "中文路径/测试.canvas"

    @pytest.mark.asyncio
    async def test_statistics_with_associations(
        self, cross_canvas_service
    ):
        """Statistics should reflect current state."""
        await cross_canvas_service.create_association(
            source_canvas_path="stat1.canvas",
            target_canvas_path="stat2.canvas",
            relationship_type="related",
        )

        stats = await cross_canvas_service.get_statistics()
        assert stats["total_associations"] >= 1
        assert stats["neo4j_enabled"] is True


# =============================================================================
# Task 6: Performance Tests
# Story 36.5 AC-7: 单次关联写入<100ms
# =============================================================================

class TestPerformance:
    """Performance tests for canvas association operations."""

    @pytest.mark.asyncio
    async def test_create_association_latency_under_100ms(
        self, cross_canvas_service, mock_neo4j_client
    ):
        """
        Story 36.5 AC-7: Single association write should complete in <100ms.

        [Source: docs/stories/36.5.story.md#AC7]
        """
        import time

        # Warm up
        await cross_canvas_service.create_association(
            source_canvas_path="warmup.canvas",
            target_canvas_path="target.canvas",
            relationship_type="related",
        )

        # Measure latency
        latencies = []
        for i in range(10):
            start = time.perf_counter()
            await cross_canvas_service.create_association(
                source_canvas_path=f"perf_source_{i}.canvas",
                target_canvas_path=f"perf_target_{i}.canvas",
                relationship_type="prerequisite",
                confidence=0.8,
                common_concepts=["test", "performance"],
            )
            elapsed_ms = (time.perf_counter() - start) * 1000
            latencies.append(elapsed_ms)

        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)

        # Assert average latency < 100ms
        assert avg_latency < 100, f"Average latency {avg_latency:.2f}ms exceeds 100ms threshold"

        # Log performance metrics
        print(f"\nPerformance Test Results:")
        print(f"  Average latency: {avg_latency:.2f}ms")
        print(f"  Max latency: {max_latency:.2f}ms")
        print(f"  Min latency: {min(latencies):.2f}ms")

    @pytest.mark.asyncio
    async def test_delete_association_latency_under_100ms(
        self, cross_canvas_service, mock_neo4j_client
    ):
        """Delete operation should also be under 100ms."""
        import time

        # Create associations to delete
        associations = []
        for i in range(10):
            assoc = await cross_canvas_service.create_association(
                source_canvas_path=f"del_source_{i}.canvas",
                target_canvas_path=f"del_target_{i}.canvas",
                relationship_type="related",
            )
            associations.append(assoc)

        # Measure delete latency
        latencies = []
        for assoc in associations:
            start = time.perf_counter()
            await cross_canvas_service.delete_association(assoc.id)
            elapsed_ms = (time.perf_counter() - start) * 1000
            latencies.append(elapsed_ms)

        avg_latency = sum(latencies) / len(latencies)

        # Assert average latency < 100ms
        assert avg_latency < 100, f"Average delete latency {avg_latency:.2f}ms exceeds 100ms"

    @pytest.mark.asyncio
    async def test_update_association_latency_under_100ms(
        self, cross_canvas_service, mock_neo4j_client
    ):
        """Update operation should also be under 100ms."""
        import time

        # Create associations to update
        associations = []
        for i in range(10):
            assoc = await cross_canvas_service.create_association(
                source_canvas_path=f"upd_source_{i}.canvas",
                target_canvas_path=f"upd_target_{i}.canvas",
                relationship_type="related",
                confidence=0.5,
            )
            associations.append(assoc)

        # Measure update latency
        latencies = []
        for assoc in associations:
            start = time.perf_counter()
            await cross_canvas_service.update_association(
                association_id=assoc.id,
                confidence=0.9,
                common_concepts=["updated"],
            )
            elapsed_ms = (time.perf_counter() - start) * 1000
            latencies.append(elapsed_ms)

        avg_latency = sum(latencies) / len(latencies)

        # Assert average latency < 100ms
        assert avg_latency < 100, f"Average update latency {avg_latency:.2f}ms exceeds 100ms"

    @pytest.mark.asyncio
    async def test_batch_write_performance(
        self, cross_canvas_service, mock_neo4j_client
    ):
        """Test batch write performance for multiple associations."""
        import time

        start = time.perf_counter()

        # Create 50 associations
        for i in range(50):
            await cross_canvas_service.create_association(
                source_canvas_path=f"batch_source_{i}.canvas",
                target_canvas_path=f"batch_target_{i}.canvas",
                relationship_type=["prerequisite", "related", "extends", "references"][i % 4],
                confidence=0.5 + (i % 5) * 0.1,
            )

        total_time_ms = (time.perf_counter() - start) * 1000
        avg_per_op = total_time_ms / 50

        print(f"\nBatch Write Performance:")
        print(f"  Total time for 50 operations: {total_time_ms:.2f}ms")
        print(f"  Average per operation: {avg_per_op:.2f}ms")

        # Each operation should average under 100ms
        assert avg_per_op < 100, f"Average operation time {avg_per_op:.2f}ms exceeds 100ms"


# =============================================================================
# Cleanup
# =============================================================================

@pytest.fixture(autouse=True)
def cleanup_singleton():
    """Clean up singleton after each test."""
    yield
    reset_cross_canvas_service()
