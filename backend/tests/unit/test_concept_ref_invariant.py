"""Unit tests for ConceptRef construction invariants.

[Source: openspec/changes/fix-concept-id-identity-unification/specs/concept-identity/spec.md
 — Requirement "ConceptRef Construction Invariant"]
"""

from dataclasses import FrozenInstanceError

import pytest

from app.models.concept_ref import ConceptRef


_VALID_UUID = "f4d10d8b-1234-4abc-89ab-cdef01234567"


class TestValidConstruction:
    """Scenario: Valid construction with UUID v4 and text name."""

    def test_minimal_construction(self):
        ref = ConceptRef(concept_id=_VALID_UUID, concept_name="万有引力")
        assert ref.concept_id == _VALID_UUID
        assert ref.concept_name == "万有引力"
        assert ref.canvas_id is None

    def test_with_canvas_id(self):
        ref = ConceptRef(
            concept_id=_VALID_UUID,
            concept_name="万有引力",
            canvas_id="physics_101",
        )
        assert ref.canvas_id == "physics_101"

    def test_english_name(self):
        ref = ConceptRef(concept_id=_VALID_UUID, concept_name="Gravity")
        assert ref.concept_name == "Gravity"

    def test_uppercase_uuid_accepted(self):
        upper = _VALID_UUID.upper()
        ref = ConceptRef(concept_id=upper, concept_name="x")
        assert ref.concept_id == upper


class TestUuidRejection:
    """Scenario: Reject non-UUID concept_id."""

    def test_rejects_chinese_text(self):
        with pytest.raises(ValueError, match="concept_id must be UUID v4"):
            ConceptRef(concept_id="万有引力", concept_name="万有引力")

    def test_rejects_default_string(self):
        with pytest.raises(ValueError, match="concept_id must be UUID v4"):
            ConceptRef(concept_id="默认概念", concept_name="默认概念")

    def test_rejects_v1_uuid(self):
        with pytest.raises(ValueError, match="concept_id must be UUID v4"):
            ConceptRef(
                concept_id="550e8400-e29b-11d4-a716-446655440000",
                concept_name="legacy",
            )

    def test_rejects_empty_concept_id(self):
        with pytest.raises(ValueError, match="concept_id must be UUID v4"):
            ConceptRef(concept_id="", concept_name="any")

    def test_rejects_none_concept_id(self):
        with pytest.raises(ValueError, match="concept_id must be UUID v4"):
            ConceptRef(concept_id=None, concept_name="any")  # type: ignore[arg-type]


class TestNameRejection:
    """Scenario: Reject empty / path-shaped concept_name."""

    def test_rejects_empty_name(self):
        with pytest.raises(ValueError, match="concept_name must be non-empty"):
            ConceptRef(concept_id=_VALID_UUID, concept_name="")

    def test_rejects_none_name(self):
        with pytest.raises(ValueError, match="concept_name must be non-empty"):
            ConceptRef(concept_id=_VALID_UUID, concept_name=None)  # type: ignore[arg-type]

    def test_rejects_path_shaped_name(self):
        """Scenario: Reject path-shaped concept_name (filesystem leakage)."""
        with pytest.raises(ValueError, match="concept_name must not be a path"):
            ConceptRef(concept_id=_VALID_UUID, concept_name="/path/to/file")

    def test_rejects_absolute_path(self):
        with pytest.raises(ValueError, match="concept_name must not be a path"):
            ConceptRef(
                concept_id=_VALID_UUID,
                concept_name="/Users/x/canvas/test.canvas",
            )


class TestImmutability:
    """frozen=True must prevent post-construction mutation."""

    def test_cannot_reassign_concept_id(self):
        ref = ConceptRef(concept_id=_VALID_UUID, concept_name="x")
        with pytest.raises(FrozenInstanceError):
            ref.concept_id = "00000000-0000-4000-8000-000000000000"  # type: ignore[misc]

    def test_cannot_reassign_concept_name(self):
        ref = ConceptRef(concept_id=_VALID_UUID, concept_name="x")
        with pytest.raises(FrozenInstanceError):
            ref.concept_name = "y"  # type: ignore[misc]

    def test_hashable(self):
        """frozen dataclass should be hashable — usable as dict key."""
        ref1 = ConceptRef(concept_id=_VALID_UUID, concept_name="x")
        ref2 = ConceptRef(concept_id=_VALID_UUID, concept_name="x")
        assert hash(ref1) == hash(ref2)
        d = {ref1: "value"}
        assert d[ref2] == "value"

    def test_equality(self):
        ref1 = ConceptRef(concept_id=_VALID_UUID, concept_name="x", canvas_id="a")
        ref2 = ConceptRef(concept_id=_VALID_UUID, concept_name="x", canvas_id="a")
        ref3 = ConceptRef(concept_id=_VALID_UUID, concept_name="y", canvas_id="a")
        assert ref1 == ref2
        assert ref1 != ref3
