"""Unit tests for VerificationService._extract_concepts_from_canvas.

Verifies that the function returns List[ConceptRef] (not List[str]) and
that each ref carries both UUID identity and human-readable text. Covers
the four scenarios from the spec:

  1. Real Canvas file with red+purple nodes → list of ConceptRef
  2. Mock mode → 3 default ConceptRef with synthetic UUIDs
  3. Canvas missing / unreadable → single fallback ConceptRef
  4. Node missing / non-UUID id → skip with warning, do not raise

[Source: openspec/changes/fix-concept-id-identity-unification/specs/concept-identity/spec.md
 — Requirement "Concept Extraction Returns ConceptRef List"]
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from app.models.concept_ref import ConceptRef
from app.utils.identifier_validators import is_uuid_v4
from app.services.verification_service import (
    _FALLBACK_CONCEPT_UUID,
    _MOCK_CONCEPT_UUIDS,
    VerificationService,
)


_RED_NODE_UUID_1 = "f4d10d8b-1234-4abc-89ab-cdef01234567"
_RED_NODE_UUID_2 = "a1b2c3d4-5678-4def-89ab-cdef01234567"
_PURPLE_NODE_UUID = "11111111-2222-4333-8444-555555555555"


@pytest.fixture
def fresh_service():
    """A VerificationService with no canvas_service / no canvas_base_path
    so we can drive _do_extract_concepts via direct file reads through a
    tmp_path."""
    return VerificationService()


@pytest.fixture
def canvas_with_red_purple(tmp_path: Path) -> Path:
    """Create a real Canvas JSON file with 2 red + 1 purple + 1 green
    node and return its path. Green should be filtered out."""
    file_path = tmp_path / "test.canvas"
    payload = {
        "nodes": [
            {
                "id": _RED_NODE_UUID_1,
                "color": "4",
                "text": "万有引力",
                "x": 0,
                "y": 0,
                "width": 100,
                "height": 50,
                "type": "text",
            },
            {
                "id": _RED_NODE_UUID_2,
                "color": "4",
                "text": "牛顿第三定律",
                "x": 0,
                "y": 100,
                "width": 100,
                "height": 50,
                "type": "text",
            },
            {
                "id": _PURPLE_NODE_UUID,
                "color": "3",
                "text": "动量守恒",
                "x": 0,
                "y": 200,
                "width": 100,
                "height": 50,
                "type": "text",
            },
            {
                "id": "f4d10d8b-9999-4abc-89ab-cdef01234567",
                "color": "1",  # green — should be filtered out
                "text": "速度",
                "x": 0,
                "y": 300,
                "width": 100,
                "height": 50,
                "type": "text",
            },
        ],
        "edges": [],
    }
    file_path.write_text(json.dumps(payload), encoding="utf-8")
    return file_path


class TestRealCanvas:
    """Scenario: Real Canvas file with red and purple nodes."""

    @pytest.mark.asyncio
    async def test_returns_list_of_concept_ref(
        self, fresh_service, canvas_with_red_purple
    ):
        refs = await fresh_service._extract_concepts_from_canvas(
            canvas_name="test", canvas_path=str(canvas_with_red_purple)
        )
        assert isinstance(refs, list)
        assert len(refs) == 3  # 2 red + 1 purple, green filtered out
        for ref in refs:
            assert isinstance(ref, ConceptRef)
            assert is_uuid_v4(ref.concept_id)

    @pytest.mark.asyncio
    async def test_concept_id_matches_node_uuid(
        self, fresh_service, canvas_with_red_purple
    ):
        refs = await fresh_service._extract_concepts_from_canvas(
            canvas_name="test", canvas_path=str(canvas_with_red_purple)
        )
        ids = {ref.concept_id for ref in refs}
        assert _RED_NODE_UUID_1 in ids
        assert _RED_NODE_UUID_2 in ids
        assert _PURPLE_NODE_UUID in ids

    @pytest.mark.asyncio
    async def test_concept_name_matches_node_text(
        self, fresh_service, canvas_with_red_purple
    ):
        refs = await fresh_service._extract_concepts_from_canvas(
            canvas_name="test", canvas_path=str(canvas_with_red_purple)
        )
        names = {ref.concept_name for ref in refs}
        assert "万有引力" in names
        assert "牛顿第三定律" in names
        assert "动量守恒" in names
        # Green node text must NOT leak in
        assert "速度" not in names


class TestMockMode:
    """Scenario: Mock mode degraded fallback returns 3 default refs."""

    @pytest.mark.asyncio
    async def test_mock_mode_returns_three_synthetic_refs(self, fresh_service):
        with patch(
            "app.services.verification_service.USE_MOCK_VERIFICATION", True
        ):
            refs = await fresh_service._extract_concepts_from_canvas(
                canvas_name="any"
            )
        assert len(refs) == 3
        for ref in refs:
            assert isinstance(ref, ConceptRef)
            assert is_uuid_v4(ref.concept_id)
            assert ref.concept_id in _MOCK_CONCEPT_UUIDS


class TestMissingCanvas:
    """Scenario: Canvas file missing or unreadable returns fallback ref."""

    @pytest.mark.asyncio
    async def test_no_canvas_path_returns_fallback_ref(self, fresh_service):
        # No canvas_path, no canvas_service, no canvas_base_path → degraded
        refs = await fresh_service._extract_concepts_from_canvas(
            canvas_name="missing"
        )
        assert len(refs) == 1
        assert isinstance(refs[0], ConceptRef)
        assert refs[0].concept_id == _FALLBACK_CONCEPT_UUID
        assert is_uuid_v4(refs[0].concept_id)
        # The literal text "默认概念" must NEVER be a concept_id
        assert refs[0].concept_id != "默认概念"

    @pytest.mark.asyncio
    async def test_invalid_path_returns_fallback_ref(
        self, fresh_service, tmp_path: Path
    ):
        bogus = tmp_path / "does-not-exist.canvas"
        refs = await fresh_service._extract_concepts_from_canvas(
            canvas_name="bogus", canvas_path=str(bogus)
        )
        assert len(refs) == 1
        assert refs[0].concept_id == _FALLBACK_CONCEPT_UUID

    @pytest.mark.asyncio
    async def test_empty_canvas_returns_fallback_ref(
        self, fresh_service, tmp_path: Path
    ):
        empty = tmp_path / "empty.canvas"
        empty.write_text(json.dumps({"nodes": [], "edges": []}), encoding="utf-8")
        refs = await fresh_service._extract_concepts_from_canvas(
            canvas_name="empty", canvas_path=str(empty)
        )
        assert len(refs) == 1
        assert refs[0].concept_id == _FALLBACK_CONCEPT_UUID


class TestNodeMissingId:
    """Scenario: Node missing id field is skipped with warning."""

    @pytest.mark.asyncio
    async def test_node_without_id_is_skipped(
        self, fresh_service, tmp_path: Path
    ):
        file_path = tmp_path / "no_id.canvas"
        payload = {
            "nodes": [
                {
                    # NOTE: no "id" field
                    "color": "4",
                    "text": "no-id concept",
                    "x": 0,
                    "y": 0,
                    "width": 100,
                    "height": 50,
                    "type": "text",
                },
                {
                    "id": _RED_NODE_UUID_1,
                    "color": "4",
                    "text": "valid concept",
                    "x": 0,
                    "y": 100,
                    "width": 100,
                    "height": 50,
                    "type": "text",
                },
            ],
            "edges": [],
        }
        file_path.write_text(json.dumps(payload), encoding="utf-8")
        refs = await fresh_service._extract_concepts_from_canvas(
            canvas_name="no_id", canvas_path=str(file_path)
        )
        # Only the valid node survives — but note: no_id.canvas has 1 valid
        # node, so refs should be exactly that one.
        assert len(refs) == 1
        assert refs[0].concept_id == _RED_NODE_UUID_1
        assert refs[0].concept_name == "valid concept"

    @pytest.mark.asyncio
    async def test_node_with_non_uuid_id_is_skipped(
        self, fresh_service, tmp_path: Path
    ):
        file_path = tmp_path / "bad_id.canvas"
        payload = {
            "nodes": [
                {
                    "id": "not-a-uuid",  # legacy or corrupt id
                    "color": "4",
                    "text": "bad-id concept",
                    "x": 0,
                    "y": 0,
                    "width": 100,
                    "height": 50,
                    "type": "text",
                },
                {
                    "id": _RED_NODE_UUID_1,
                    "color": "4",
                    "text": "valid concept",
                    "x": 0,
                    "y": 100,
                    "width": 100,
                    "height": 50,
                    "type": "text",
                },
            ],
            "edges": [],
        }
        file_path.write_text(json.dumps(payload), encoding="utf-8")
        refs = await fresh_service._extract_concepts_from_canvas(
            canvas_name="bad_id", canvas_path=str(file_path)
        )
        # bad-id node skipped, valid one kept
        assert len(refs) == 1
        assert refs[0].concept_id == _RED_NODE_UUID_1

    @pytest.mark.asyncio
    async def test_all_nodes_invalid_returns_fallback(
        self, fresh_service, tmp_path: Path
    ):
        """If every node is missing/bad id, the inner _do_extract_concepts
        returns []; the wrapper then falls back to a single default ref."""
        file_path = tmp_path / "all_bad.canvas"
        payload = {
            "nodes": [
                {
                    "color": "4",  # no id
                    "text": "concept a",
                    "x": 0,
                    "y": 0,
                    "width": 100,
                    "height": 50,
                    "type": "text",
                },
                {
                    "id": "万有引力",  # text-id
                    "color": "4",
                    "text": "concept b",
                    "x": 0,
                    "y": 100,
                    "width": 100,
                    "height": 50,
                    "type": "text",
                },
            ],
            "edges": [],
        }
        file_path.write_text(json.dumps(payload), encoding="utf-8")
        refs = await fresh_service._extract_concepts_from_canvas(
            canvas_name="all_bad", canvas_path=str(file_path)
        )
        assert len(refs) == 1
        assert refs[0].concept_id == _FALLBACK_CONCEPT_UUID
