"""
S02 T01 — Unit tests for entity types, EpisodeTask wiring, and ID widening.

Tests:
  (a) New Pydantic models validate correctly
  (b) CANVAS_ENTITY_TYPES / CANVAS_EDGE_TYPES dicts have correct keys/values
  (c) EpisodeTask accepts entity_types / edge_types fields
  (d) _process_episode passes entity_types / edge_types to add_episode (mock Graphiti)
  (e) Deterministic IDs are 32 hex chars
"""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError

from app.graphiti.entity_types import (
    CANVAS_EDGE_TYPES,
    CANVAS_ENTITY_TYPES,
    LearningConcept,
    LearningTip,
    MasteryRecord,
    Misconception,
    PrerequisiteRelation,
)
from app.services.episode_worker import EpisodeTask, GraphitiEpisodeWorker


# ═══════════════════════════════════════════════════════════════════════════════
# (a) New Pydantic models validate correctly
# ═══════════════════════════════════════════════════════════════════════════════


class TestLearningConcept:
    """LearningConcept validates with required and optional fields."""

    def test_valid_full(self):
        concept = LearningConcept(
            concept_name="Quadratic Formula",
            description="Formula for solving quadratic equations",
            subject_area="数学",
            difficulty_level="intermediate",
            prerequisites=["Algebra Basics", "Square Roots"],
        )
        assert concept.concept_name == "Quadratic Formula"
        assert concept.subject_area == "数学"
        assert len(concept.prerequisites) == 2

    def test_valid_defaults(self):
        concept = LearningConcept(
            concept_name="Newton's Laws",
            description="Three laws of motion",
            subject_area="物理",
        )
        assert concept.difficulty_level == ""
        assert concept.prerequisites == []

    def test_missing_required_field(self):
        with pytest.raises(ValidationError):
            LearningConcept(name="Incomplete")  # missing description, subject_area


class TestMasteryRecord:
    """MasteryRecord validates with required and optional fields."""

    def test_valid_full(self):
        record = MasteryRecord(
            concept_name="Calculus",
            mastery_level="proficient",
            last_reviewed="2025-12-01T10:00:00Z",
            error_count=3,
        )
        assert record.concept_name == "Calculus"
        assert record.error_count == 3

    def test_valid_defaults(self):
        record = MasteryRecord(
            concept_name="Algebra",
            mastery_level="novice",
            last_reviewed="2025-01-01T00:00:00Z",
        )
        assert record.error_count == 0

    def test_missing_required(self):
        with pytest.raises(ValidationError):
            MasteryRecord(concept_name="X")  # missing mastery_level, last_reviewed


class TestPrerequisiteRelation:
    """PrerequisiteRelation validates with required and optional fields."""

    def test_valid_full(self):
        rel = PrerequisiteRelation(
            source_concept="Algebra",
            target_concept="Calculus",
            relation_strength="strong",
        )
        assert rel.source_concept == "Algebra"
        assert rel.target_concept == "Calculus"
        assert rel.relation_strength == "strong"

    def test_valid_defaults(self):
        rel = PrerequisiteRelation(
            source_concept="Addition",
            target_concept="Multiplication",
        )
        assert rel.relation_strength == "strong"  # default

    def test_missing_required(self):
        with pytest.raises(ValidationError):
            PrerequisiteRelation(source_concept="Only one side")


# ═══════════════════════════════════════════════════════════════════════════════
# (b) CANVAS_ENTITY_TYPES / CANVAS_EDGE_TYPES dicts
# ═══════════════════════════════════════════════════════════════════════════════


class TestCanvasTypeDicts:
    """CANVAS_ENTITY_TYPES and CANVAS_EDGE_TYPES have correct keys and values."""

    def test_entity_types_keys(self):
        expected_keys = {
            "LearningConcept",
            "LearningTip",
            "Misconception",
            "MasteryRecord",
        }
        assert set(CANVAS_ENTITY_TYPES.keys()) == expected_keys

    def test_entity_types_values_are_basemodel_subclasses(self):
        from pydantic import BaseModel

        for key, cls in CANVAS_ENTITY_TYPES.items():
            assert issubclass(cls, BaseModel), f"{key} is not a BaseModel subclass"

    def test_entity_types_correct_mapping(self):
        assert CANVAS_ENTITY_TYPES["LearningConcept"] is LearningConcept
        assert CANVAS_ENTITY_TYPES["LearningTip"] is LearningTip
        assert CANVAS_ENTITY_TYPES["Misconception"] is Misconception
        assert CANVAS_ENTITY_TYPES["MasteryRecord"] is MasteryRecord

    def test_edge_types_keys(self):
        assert set(CANVAS_EDGE_TYPES.keys()) == {"PrerequisiteRelation"}

    def test_edge_types_values_are_basemodel_subclasses(self):
        from pydantic import BaseModel

        for key, cls in CANVAS_EDGE_TYPES.items():
            assert issubclass(cls, BaseModel), f"{key} is not a BaseModel subclass"

    def test_edge_types_correct_mapping(self):
        assert CANVAS_EDGE_TYPES["PrerequisiteRelation"] is PrerequisiteRelation


# ═══════════════════════════════════════════════════════════════════════════════
# (c) EpisodeTask accepts entity_types / edge_types fields
# ═══════════════════════════════════════════════════════════════════════════════


class TestEpisodeTaskEntityFields:
    """EpisodeTask dataclass supports optional entity_types and edge_types."""

    def test_defaults_none(self):
        task = EpisodeTask(
            name="test",
            episode_body="body",
            group_id="grp",
            source_description="src",
        )
        assert task.entity_types is None
        assert task.edge_types is None

    def test_with_entity_types(self):
        task = EpisodeTask(
            name="test",
            episode_body="body",
            group_id="grp",
            source_description="src",
            entity_types=CANVAS_ENTITY_TYPES,
        )
        assert task.entity_types is CANVAS_ENTITY_TYPES
        assert task.edge_types is None

    def test_with_both_types(self):
        task = EpisodeTask(
            name="test",
            episode_body="body",
            group_id="grp",
            source_description="src",
            entity_types=CANVAS_ENTITY_TYPES,
            edge_types=CANVAS_EDGE_TYPES,
        )
        assert task.entity_types is CANVAS_ENTITY_TYPES
        assert task.edge_types is CANVAS_EDGE_TYPES

    def test_to_dict_includes_type_names(self):
        task = EpisodeTask(
            name="test",
            episode_body="body",
            group_id="grp",
            source_description="src",
            entity_types=CANVAS_ENTITY_TYPES,
            edge_types=CANVAS_EDGE_TYPES,
        )
        d = task.to_dict()
        assert "entity_type_names" in d
        assert set(d["entity_type_names"]) == {
            "LearningConcept",
            "LearningTip",
            "Misconception",
            "MasteryRecord",
        }
        assert "edge_type_names" in d
        assert set(d["edge_type_names"]) == {"PrerequisiteRelation"}

    def test_to_dict_omits_type_names_when_none(self):
        task = EpisodeTask(
            name="test",
            episode_body="body",
            group_id="grp",
            source_description="src",
        )
        d = task.to_dict()
        assert "entity_type_names" not in d
        assert "edge_type_names" not in d


# ═══════════════════════════════════════════════════════════════════════════════
# (d) _process_episode passes entity_types / edge_types to add_episode
# ═══════════════════════════════════════════════════════════════════════════════


class TestProcessEpisodeForwarding:
    """_process_episode forwards entity_types and edge_types to graphiti.add_episode."""

    @pytest.mark.asyncio
    async def test_forwards_entity_and_edge_types(self):
        mock_graphiti = AsyncMock()
        mock_graphiti.add_episode = AsyncMock()

        worker = GraphitiEpisodeWorker()
        worker._graphiti = mock_graphiti

        task = EpisodeTask(
            name="test-episode",
            episode_body="Student learned calculus",
            group_id="math-group",
            source_description="test",
            entity_types=CANVAS_ENTITY_TYPES,
            edge_types=CANVAS_EDGE_TYPES,
        )

        await worker._process_episode(task)

        mock_graphiti.add_episode.assert_called_once()
        call_kwargs = mock_graphiti.add_episode.call_args.kwargs
        assert call_kwargs["name"] == "test-episode"
        assert call_kwargs["episode_body"] == "Student learned calculus"
        assert call_kwargs["group_id"] == "math-group"
        assert call_kwargs["entity_types"] is CANVAS_ENTITY_TYPES
        assert call_kwargs["edge_types"] is CANVAS_EDGE_TYPES

    @pytest.mark.asyncio
    async def test_omits_types_when_none(self):
        mock_graphiti = AsyncMock()
        mock_graphiti.add_episode = AsyncMock()

        worker = GraphitiEpisodeWorker()
        worker._graphiti = mock_graphiti

        task = EpisodeTask(
            name="test-no-types",
            episode_body="body",
            group_id="grp",
            source_description="test",
        )

        await worker._process_episode(task)

        mock_graphiti.add_episode.assert_called_once()
        call_kwargs = mock_graphiti.add_episode.call_args.kwargs
        assert "entity_types" not in call_kwargs
        assert "edge_types" not in call_kwargs

    @pytest.mark.asyncio
    async def test_raises_without_graphiti(self):
        worker = GraphitiEpisodeWorker()
        worker._graphiti = None

        task = EpisodeTask(
            name="fail", episode_body="b", group_id="g", source_description="s"
        )

        with pytest.raises(RuntimeError, match="Graphiti client not initialized"):
            await worker._process_episode(task)


# ═══════════════════════════════════════════════════════════════════════════════
# (e) Deterministic IDs are 32 hex chars
# ═══════════════════════════════════════════════════════════════════════════════


class TestDeterministicIDWidening:
    """Both ID generation functions produce 32-hex-char hashes."""

    def test_episode_id_length(self):
        from app.services.memory_service import _generate_deterministic_episode_id

        eid = _generate_deterministic_episode_id(
            "user1", "/math/canvas.json", "node-1", "algebra"
        )
        # Format: "episode-" + 32 hex chars
        assert eid.startswith("episode-")
        hex_part = eid[len("episode-") :]
        assert len(hex_part) == 32
        # Verify it's valid hex
        int(hex_part, 16)

    def test_batch_id_length(self):
        from app.services.memory_service import _generate_batch_episode_id

        bid = _generate_batch_episode_id(
            "/math/canvas.json", "node-1", "learning", "2025-01-01T00:00:00"
        )
        assert bid.startswith("batch-")
        hex_part = bid[len("batch-") :]
        assert len(hex_part) == 32
        int(hex_part, 16)

    def test_episode_id_deterministic(self):
        from app.services.memory_service import _generate_deterministic_episode_id

        id1 = _generate_deterministic_episode_id("u", "p", "n", "c")
        id2 = _generate_deterministic_episode_id("u", "p", "n", "c")
        assert id1 == id2

    def test_batch_id_deterministic(self):
        from app.services.memory_service import _generate_batch_episode_id

        id1 = _generate_batch_episode_id("p", "n", "e", "t")
        id2 = _generate_batch_episode_id("p", "n", "e", "t")
        assert id1 == id2

    def test_different_inputs_different_ids(self):
        from app.services.memory_service import _generate_deterministic_episode_id

        id1 = _generate_deterministic_episode_id("u1", "p", "n", "c")
        id2 = _generate_deterministic_episode_id("u2", "p", "n", "c")
        assert id1 != id2
