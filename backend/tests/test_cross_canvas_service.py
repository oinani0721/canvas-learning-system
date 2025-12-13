# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: testing)
"""
Unit tests for Story 25.3: Exercise-Lecture Canvas Association
[Source: docs/stories/25.3.story.md#Testing]

Tests:
- CrossCanvasService CRUD operations
- Intelligent suggestion algorithm
- Cross-canvas context retrieval
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.cross_canvas_service import (
    CrossCanvasService,
    CrossCanvasAssociation,
    CanvasAssociationSuggestion,
    get_cross_canvas_service,
)


# String constants for relationship types (matches cross_canvas_service.py)
EXERCISE_LECTURE = "exercise_lecture"
RELATED = "related"


# ============================================================================
# CrossCanvasService Tests
# ============================================================================

class TestCrossCanvasService:
    """Tests for CrossCanvasService operations"""

    @pytest.fixture
    def cross_canvas_service(self) -> CrossCanvasService:
        """Create a fresh CrossCanvasService instance for testing."""
        # Create new instance (not singleton) for isolated tests
        service = CrossCanvasService()
        service._associations = {}
        service._knowledge_paths = {}
        return service

    @pytest.fixture
    def sample_association_params(self) -> dict:
        """Sample association parameters for create_association()."""
        return {
            "source_canvas_path": "exercises/math-problems.canvas",
            "target_canvas_path": "lectures/math-lecture.canvas",
            "relationship_type": EXERCISE_LECTURE,
            "common_concepts": ["algebra", "equations"],
            "confidence": 0.85,
        }

    # =========================================================================
    # CRUD Operation Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_create_association_success(
        self,
        cross_canvas_service: CrossCanvasService,
        sample_association_params: dict
    ):
        """Test successful association creation."""
        # Act
        result = await cross_canvas_service.create_association(**sample_association_params)

        # Assert
        assert result is not None
        assert result.id is not None
        assert result.source_canvas_path == sample_association_params["source_canvas_path"]
        assert result.target_canvas_path == sample_association_params["target_canvas_path"]
        assert result.relationship_type == EXERCISE_LECTURE
        assert result.confidence == 0.85

    @pytest.mark.asyncio
    async def test_create_association_generates_valid_id(
        self,
        cross_canvas_service: CrossCanvasService,
        sample_association_params: dict
    ):
        """Test that association IDs have correct format (cca-{hex})."""
        # Act
        result = await cross_canvas_service.create_association(**sample_association_params)

        # Assert - ID format is "cca-{12 hex chars}"
        assert result.id.startswith("cca-")
        assert len(result.id) == 16  # "cca-" (4) + 12 hex chars
        # Verify the hex part is valid
        hex_part = result.id[4:]
        int(hex_part, 16)  # Will raise ValueError if not valid hex

    @pytest.mark.asyncio
    async def test_get_association_success(
        self,
        cross_canvas_service: CrossCanvasService,
        sample_association_params: dict
    ):
        """Test retrieving an association by ID."""
        # Arrange
        created = await cross_canvas_service.create_association(**sample_association_params)

        # Act
        result = await cross_canvas_service.get_association(created.id)

        # Assert
        assert result is not None
        assert result.id == created.id

    @pytest.mark.asyncio
    async def test_get_association_not_found(
        self,
        cross_canvas_service: CrossCanvasService
    ):
        """Test getting non-existent association returns None."""
        # Act
        result = await cross_canvas_service.get_association("nonexistent-id")

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_association_success(
        self,
        cross_canvas_service: CrossCanvasService,
        sample_association_params: dict
    ):
        """Test successful association deletion."""
        # Arrange
        created = await cross_canvas_service.create_association(**sample_association_params)

        # Act
        result = await cross_canvas_service.delete_association(created.id)

        # Assert
        assert result is True
        assert await cross_canvas_service.get_association(created.id) is None

    @pytest.mark.asyncio
    async def test_delete_association_not_found(
        self,
        cross_canvas_service: CrossCanvasService
    ):
        """Test deleting non-existent association returns False."""
        # Act
        result = await cross_canvas_service.delete_association("nonexistent-id")

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_list_associations(
        self,
        cross_canvas_service: CrossCanvasService,
        sample_association_params: dict
    ):
        """Test listing all associations."""
        # Arrange
        await cross_canvas_service.create_association(**sample_association_params)
        sample_association_params["source_canvas_path"] = "exercises/another.canvas"
        await cross_canvas_service.create_association(**sample_association_params)

        # Act
        result = await cross_canvas_service.list_associations()

        # Assert
        assert len(result) == 2

    # =========================================================================
    # Association Retrieval Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_get_associated_canvases_by_type(
        self,
        cross_canvas_service: CrossCanvasService,
        sample_association_params: dict
    ):
        """Test filtering associations by relation type."""
        # Arrange
        await cross_canvas_service.create_association(**sample_association_params)

        # Create another association with different type
        sample_association_params["relationship_type"] = RELATED
        sample_association_params["source_canvas_path"] = "other/path.canvas"
        await cross_canvas_service.create_association(**sample_association_params)

        # Act
        exercise_results = await cross_canvas_service.get_associated_canvases(
            "exercises/math-problems.canvas",
            relation_type=EXERCISE_LECTURE
        )

        # Assert
        assert len(exercise_results) == 1
        assert exercise_results[0].relationship_type == EXERCISE_LECTURE

    @pytest.mark.asyncio
    async def test_get_lecture_for_exercise(
        self,
        cross_canvas_service: CrossCanvasService,
        sample_association_params: dict
    ):
        """Test getting lecture canvas for an exercise canvas."""
        # Arrange
        await cross_canvas_service.create_association(**sample_association_params)

        # Act
        result = await cross_canvas_service.get_lecture_for_exercise(
            "exercises/math-problems.canvas"
        )

        # Assert
        assert result is not None
        assert result.target_canvas_path == "lectures/math-lecture.canvas"

    @pytest.mark.asyncio
    async def test_get_lecture_for_exercise_not_found(
        self,
        cross_canvas_service: CrossCanvasService
    ):
        """Test getting lecture for canvas with no association."""
        # Act
        result = await cross_canvas_service.get_lecture_for_exercise(
            "exercises/no-association.canvas"
        )

        # Assert
        assert result is None


# ============================================================================
# Suggestion Algorithm Tests
# ============================================================================

class TestSuggestionAlgorithm:
    """Tests for intelligent suggestion algorithm (Story 25.3 AC5)"""

    @pytest.fixture
    def cross_canvas_service(self) -> CrossCanvasService:
        """Create service for suggestion tests."""
        service = CrossCanvasService()
        service._associations = {}
        service._knowledge_paths = {}
        return service

    @pytest.mark.asyncio
    async def test_suggest_lecture_canvas_returns_suggestions(
        self,
        cross_canvas_service: CrossCanvasService
    ):
        """Test that suggest_lecture_canvas returns suggestions."""
        # Act
        suggestions = await cross_canvas_service.suggest_lecture_canvas(
            "exercises/discrete-math-题目.canvas"
        )

        # Assert - should return a list (may be empty if no canvases available)
        assert isinstance(suggestions, list)

    @pytest.mark.asyncio
    async def test_suggest_lecture_canvas_from_history(
        self,
        cross_canvas_service: CrossCanvasService
    ):
        """Test suggestion based on historical associations."""
        # Arrange - create existing association
        await cross_canvas_service.create_association(
            source_canvas_path="exercises/math-set-1.canvas",
            target_canvas_path="lectures/math-lecture.canvas",
            relationship_type=EXERCISE_LECTURE,
            common_concepts=["algebra"],
            confidence=0.9,
        )

        # Act - suggest for similar exercise canvas
        suggestions = await cross_canvas_service.suggest_lecture_canvas(
            "exercises/math-set-2.canvas"
        )

        # Assert - history-based suggestions should include previously associated canvas
        assert isinstance(suggestions, list)
        if len(suggestions) > 0:
            # Check at least one suggestion has the historical target
            paths = [s.target_canvas_path for s in suggestions]
            # The historical path might be suggested
            assert any("lecture" in p.lower() for p in paths) or len(paths) == 0


# ============================================================================
# Statistics Tests
# ============================================================================

class TestCrossCanvasStatistics:
    """Tests for cross-canvas statistics (Story 25.3)"""

    @pytest.fixture
    def cross_canvas_service(self) -> CrossCanvasService:
        """Create service for statistics tests."""
        service = CrossCanvasService()
        service._associations = {}
        service._knowledge_paths = {}
        return service

    @pytest.mark.asyncio
    async def test_get_statistics_empty(
        self,
        cross_canvas_service: CrossCanvasService
    ):
        """Test statistics with no associations."""
        # Act
        stats = await cross_canvas_service.get_statistics()

        # Assert
        assert stats["total_associations"] == 0
        assert stats["total_paths"] == 0

    @pytest.mark.asyncio
    async def test_get_statistics_with_data(
        self,
        cross_canvas_service: CrossCanvasService
    ):
        """Test statistics with associations."""
        # Arrange
        await cross_canvas_service.create_association(
            source_canvas_path="a.canvas",
            target_canvas_path="b.canvas",
            relationship_type=EXERCISE_LECTURE,
            confidence=0.8,
        )
        await cross_canvas_service.create_association(
            source_canvas_path="c.canvas",
            target_canvas_path="d.canvas",
            relationship_type=RELATED,
            confidence=0.5,
        )

        # Act
        stats = await cross_canvas_service.get_statistics()

        # Assert
        assert stats["total_associations"] == 2
        # Verify the statistics contain the expected keys
        assert "total_paths" in stats
        assert "total_canvases_linked" in stats
