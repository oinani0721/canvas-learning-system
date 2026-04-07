"""Unit tests for VerificationService concept_id propagation.

Verifies that after fix-concept-id-identity-unification:
  1. _get_difficulty_for_concept refuses text fallback when node_id is missing
  2. _get_fsrs_history_for_prompt refuses text fallback when node_id is missing
  3. The chain from _extract_concepts → start_session → mastery_filter
     passes ref.concept_id (UUID) to memory_service.get_concept_score_history
     instead of ref.concept_name (text)

[Source: openspec/changes/fix-concept-id-identity-unification/specs/concept-identity/spec.md
 — Requirement "Difficulty Query Refuses Text Fallback"]
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.concept_ref import ConceptRef
from app.services.verification_service import (
    DifficultyLevel,
    VerificationService,
)


_VALID_NODE_UUID_1 = "f4d10d8b-1234-4abc-89ab-cdef01234567"
_VALID_NODE_UUID_2 = "a1b2c3d4-5678-4def-89ab-cdef01234567"


@pytest.fixture
def mock_memory_service():
    """Mock MemoryService with happy-path get_concept_score_history."""
    svc = MagicMock()
    history = MagicMock()
    history.scores = [85, 90, 88]
    history.average = 87.6
    history.sample_size = 3
    svc.get_concept_score_history = AsyncMock(return_value=history)
    return svc


@pytest.fixture
def empty_memory_service():
    """Mock MemoryService that returns empty history."""
    svc = MagicMock()
    history = MagicMock()
    history.scores = []
    history.average = 0
    history.sample_size = 0
    svc.get_concept_score_history = AsyncMock(return_value=history)
    return svc


class TestDifficultyQueryNodeIdHandling:
    """Scenario: _get_difficulty_for_concept refuses text fallback."""

    @pytest.mark.asyncio
    async def test_node_id_uuid_passed_through_to_memory(self, mock_memory_service):
        service = VerificationService(memory_service=mock_memory_service)
        await service._get_difficulty_for_concept(
            concept="万有引力",
            canvas_name="phys",
            node_id=_VALID_NODE_UUID_1,
        )
        mock_memory_service.get_concept_score_history.assert_called_once()
        kwargs = mock_memory_service.get_concept_score_history.call_args.kwargs
        # The UUID is passed as concept_id; concept text is NEVER substituted
        assert kwargs["concept_id"] == _VALID_NODE_UUID_1
        assert kwargs["concept_id"] != "万有引力"

    @pytest.mark.asyncio
    async def test_missing_node_id_returns_default_without_querying(
        self, mock_memory_service
    ):
        service = VerificationService(memory_service=mock_memory_service)
        result = await service._get_difficulty_for_concept(
            concept="万有引力",
            canvas_name="phys",
            node_id=None,
        )
        # Default difficulty returned, memory NOT consulted with text
        assert result.level == DifficultyLevel.MEDIUM
        assert result.sample_size == 0
        mock_memory_service.get_concept_score_history.assert_not_called()

    @pytest.mark.asyncio
    async def test_non_uuid_node_id_returns_default_without_querying(
        self, mock_memory_service
    ):
        service = VerificationService(memory_service=mock_memory_service)
        result = await service._get_difficulty_for_concept(
            concept="万有引力",
            canvas_name="phys",
            node_id="legacy-string-id",  # not a UUID
        )
        assert result.level == DifficultyLevel.MEDIUM
        mock_memory_service.get_concept_score_history.assert_not_called()


class TestFsrsHistoryNodeIdHandling:
    """Scenario: _get_fsrs_history_for_prompt refuses text fallback."""

    @pytest.mark.asyncio
    async def test_uuid_node_id_passed_through(self, mock_memory_service):
        service = VerificationService(memory_service=mock_memory_service)
        result = await service._get_fsrs_history_for_prompt(
            concept="万有引力",
            canvas_name="phys",
            node_id=_VALID_NODE_UUID_1,
        )
        assert result is not None
        mock_memory_service.get_concept_score_history.assert_called_once()
        # First positional arg is concept_id
        args = mock_memory_service.get_concept_score_history.call_args.args
        assert args[0] == _VALID_NODE_UUID_1

    @pytest.mark.asyncio
    async def test_missing_node_id_skips_query(self, mock_memory_service):
        service = VerificationService(memory_service=mock_memory_service)
        result = await service._get_fsrs_history_for_prompt(
            concept="万有引力",
            canvas_name="phys",
            node_id=None,
        )
        assert result is None
        mock_memory_service.get_concept_score_history.assert_not_called()

    @pytest.mark.asyncio
    async def test_non_uuid_node_id_skips_query(self, mock_memory_service):
        service = VerificationService(memory_service=mock_memory_service)
        result = await service._get_fsrs_history_for_prompt(
            concept="万有引力",
            canvas_name="phys",
            node_id="not-a-uuid",
        )
        assert result is None
        mock_memory_service.get_concept_score_history.assert_not_called()


class TestStartSessionPropagation:
    """End-to-end-ish: start_session must pass UUID concept_id to mastery filter.

    This is the test that, on legacy code, would have caught the
    `concept_id=concept` (text) bug at the unit level.
    """

    @pytest.fixture
    def canvas_file(self, tmp_path: Path) -> Path:
        path = tmp_path / "test.canvas"
        path.write_text(
            json.dumps(
                {
                    "nodes": [
                        {
                            "id": _VALID_NODE_UUID_1,
                            "color": "4",
                            "text": "万有引力",
                            "x": 0,
                            "y": 0,
                            "width": 100,
                            "height": 50,
                            "type": "text",
                        },
                        {
                            "id": _VALID_NODE_UUID_2,
                            "color": "3",
                            "text": "牛顿第三定律",
                            "x": 0,
                            "y": 100,
                            "width": 100,
                            "height": 50,
                            "type": "text",
                        },
                    ],
                    "edges": [],
                }
            ),
            encoding="utf-8",
        )
        return path

    @pytest.mark.asyncio
    async def test_mastery_filter_receives_uuid_not_text(
        self, empty_memory_service, canvas_file
    ):
        service = VerificationService(memory_service=empty_memory_service)
        await service.start_session(
            canvas_name="test",
            canvas_path=str(canvas_file),
            include_mastered=False,
        )
        # Verify mastery filter called for each concept with concept_id=UUID.
        # Some call sites pass concept_id positionally, others as kwarg —
        # collect both forms.
        calls = empty_memory_service.get_concept_score_history.call_args_list
        assert len(calls) >= 2
        seen_ids: set[str] = set()
        for c in calls:
            if "concept_id" in c.kwargs:
                seen_ids.add(c.kwargs["concept_id"])
            elif c.args:
                seen_ids.add(c.args[0])
        assert _VALID_NODE_UUID_1 in seen_ids
        assert _VALID_NODE_UUID_2 in seen_ids
        # Critically: text concept names must NEVER appear in concept_id slot
        assert "万有引力" not in seen_ids
        assert "牛顿第三定律" not in seen_ids

    @pytest.mark.asyncio
    async def test_session_state_stores_concept_ref_queue(
        self, empty_memory_service, canvas_file
    ):
        """Internal state should hold List[ConceptRef] in concept_queue
        and a ConceptRef in current_concept_ref."""
        service = VerificationService(memory_service=empty_memory_service)
        result = await service.start_session(
            canvas_name="test", canvas_path=str(canvas_file)
        )
        session_id = result["session_id"]
        state = service._sessions[session_id]
        queue = state["concept_queue"]
        assert isinstance(queue, list)
        for ref in queue:
            assert isinstance(ref, ConceptRef)
        cur = state["current_concept_ref"]
        assert isinstance(cur, ConceptRef)
        # The display field current_concept stays a string for backward compat
        assert isinstance(state["current_concept"], str)
        assert state["current_concept"] == cur.concept_name
