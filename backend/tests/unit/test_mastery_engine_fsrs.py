"""
Tests for FSRS integration in MasteryEngine.

Covers:
- FSRS new card creation and first review
- 4 rating types (Again/Hard/Good/Easy)
- Card serialization -> deserialization -> review chain
- Retrievability computation (with FSRS / fallback)
- FSRS unavailable degradation path

Reference: py-fsrs library (FSRS-4.5 algorithm)
"""

import math
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from app.models.mastery_state import ConceptState, MasteryConfig
from app.services.mastery_engine import MasteryEngine


@pytest.fixture
def stub_fsrs():
    """Create a stub FSRSManager with standard behavior."""
    mgr = MagicMock()

    created_card = MagicMock()
    created_card.stability = 1.0
    created_card.difficulty = 5.0
    created_card.state = MagicMock(value=1)
    created_card.reps = 0
    created_card.lapses = 0
    mgr.create_card.return_value = created_card

    reviewed_card = MagicMock()
    reviewed_card.stability = 3.5
    reviewed_card.difficulty = 4.8
    reviewed_card.state = MagicMock(value=2)
    reviewed_card.reps = 1
    reviewed_card.lapses = 0
    review_log = MagicMock()
    mgr.review_card.return_value = (reviewed_card, review_log)

    mgr.serialize_card.return_value = '{"stability": 3.5, "difficulty": 4.8}'
    mgr.deserialize_card.return_value = reviewed_card
    mgr.get_retrievability.return_value = 0.85

    return mgr


@pytest.fixture
def engine_with_fsrs(stub_fsrs):
    """MasteryEngine with a stubbed FSRSManager."""
    engine = MasteryEngine.__new__(MasteryEngine)
    engine.config = MasteryConfig()
    engine.fsrs_manager = stub_fsrs
    return engine


@pytest.fixture
def engine_no_fsrs():
    """MasteryEngine with FSRS disabled."""
    engine = MasteryEngine.__new__(MasteryEngine)
    engine.config = MasteryConfig()
    engine.fsrs_manager = None
    return engine


class TestFSRSNewCard:
    """FSRS new card creation on first interaction."""

    def test_first_review_creates_card(self, engine_with_fsrs, stub_fsrs):
        concept = ConceptState(concept_id="t", topic="t", name="t")
        assert concept.fsrs_card_data is None
        engine_with_fsrs.update_on_interaction(concept, grade=3)
        stub_fsrs.create_card.assert_called_once()
        stub_fsrs.review_card.assert_called_once()

    def test_subsequent_review_deserializes(self, engine_with_fsrs, stub_fsrs):
        concept = ConceptState(
            concept_id="t", topic="t", name="t",
            fsrs_card_data='{"stability": 1.0}',
        )
        engine_with_fsrs.update_on_interaction(concept, grade=3)
        stub_fsrs.deserialize_card.assert_called_once()
        stub_fsrs.create_card.assert_not_called()

    def test_fsrs_state_fields_updated(self, engine_with_fsrs):
        concept = ConceptState(concept_id="t", topic="t", name="t")
        engine_with_fsrs.update_on_interaction(concept, grade=3)
        assert concept.fsrs_stability == 3.5
        assert concept.fsrs_difficulty == 4.8
        assert concept.fsrs_state == 2
        assert concept.fsrs_reps == 1
        assert concept.fsrs_lapses == 0
        assert concept.fsrs_card_data is not None


class TestFSRSRatings:
    """Test all 4 FSRS ratings."""

    @pytest.mark.parametrize("grade", [1, 2, 3, 4])
    def test_all_grades_call_review(self, engine_with_fsrs, stub_fsrs, grade):
        concept = ConceptState(concept_id="t", topic="t", name="t")
        engine_with_fsrs.update_on_interaction(concept, grade=grade)
        stub_fsrs.review_card.assert_called_once()

    def test_grade1_is_again(self, engine_with_fsrs, stub_fsrs):
        concept = ConceptState(concept_id="t", topic="t", name="t")
        engine_with_fsrs.update_on_interaction(concept, grade=1)
        call_args = stub_fsrs.review_card.call_args
        assert call_args[0][1] == 1

    def test_grade4_is_easy(self, engine_with_fsrs, stub_fsrs):
        concept = ConceptState(concept_id="t", topic="t", name="t")
        engine_with_fsrs.update_on_interaction(concept, grade=4)
        call_args = stub_fsrs.review_card.call_args
        assert call_args[0][1] == 4


class TestFSRSSerializationChain:
    """Card serialization -> deserialization -> review complete chain."""

    def test_serialize_called_after_review(self, engine_with_fsrs, stub_fsrs):
        concept = ConceptState(concept_id="t", topic="t", name="t")
        engine_with_fsrs.update_on_interaction(concept, grade=3)
        stub_fsrs.serialize_card.assert_called_once()

    def test_card_json_stored_on_concept(self, engine_with_fsrs):
        concept = ConceptState(concept_id="t", topic="t", name="t")
        engine_with_fsrs.update_on_interaction(concept, grade=3)
        assert concept.fsrs_card_data is not None


class TestRetrievability:
    """Retrievability computation tests."""

    def test_retrievability_with_fsrs(self, engine_with_fsrs, stub_fsrs):
        concept = ConceptState(
            concept_id="t", topic="t", name="t",
            fsrs_card_data='{"stability": 3.5}',
        )
        R = engine_with_fsrs._get_retrievability(concept)
        assert R == 0.85
        stub_fsrs.get_retrievability.assert_called_once()

    def test_retrievability_no_fsrs_no_interaction(self, engine_no_fsrs):
        concept = ConceptState(concept_id="t", topic="t", name="t")
        R = engine_no_fsrs._get_retrievability(concept)
        assert R == 1.0

    def test_retrievability_no_fsrs_with_interaction(self, engine_no_fsrs):
        concept = ConceptState(
            concept_id="t", topic="t", name="t",
            last_interaction_ts=datetime.now(timezone.utc) - timedelta(days=3),
            fsrs_stability=2.0,
        )
        R = engine_no_fsrs._get_retrievability(concept)
        expected = math.exp(-3.0 / 2.0)
        assert abs(R - expected) < 0.05

    def test_retrievability_fallback_stability_min_1(self, engine_no_fsrs):
        concept = ConceptState(
            concept_id="t", topic="t", name="t",
            last_interaction_ts=datetime.now(timezone.utc) - timedelta(days=1),
            fsrs_stability=0.0,
        )
        R = engine_no_fsrs._get_retrievability(concept)
        expected = math.exp(-1.0 / 1.0)
        assert abs(R - expected) < 0.05

    def test_retrievability_no_card_json_but_has_manager(self, engine_with_fsrs):
        concept = ConceptState(
            concept_id="t", topic="t", name="t",
            fsrs_card_data=None,
            last_interaction_ts=datetime.now(timezone.utc) - timedelta(days=1),
            fsrs_stability=5.0,
        )
        R = engine_with_fsrs._get_retrievability(concept)
        expected = math.exp(-1.0 / 5.0)
        assert abs(R - expected) < 0.05


class TestFSRSDisabled:
    """FSRS degradation when unavailable."""

    def test_no_fsrs_manager_skips_update(self, engine_no_fsrs):
        concept = ConceptState(concept_id="t", topic="t", name="t")
        old_card_json = concept.fsrs_card_data
        engine_no_fsrs.update_on_interaction(concept, grade=3)
        assert concept.fsrs_card_data == old_card_json
        assert concept.fsrs_stability == 0.0

    def test_bkt_still_works_without_fsrs(self, engine_no_fsrs):
        concept = ConceptState(concept_id="t", topic="t", name="t", p_mastery=0.5)
        engine_no_fsrs.update_on_interaction(concept, grade=3)
        assert concept.p_mastery > 0.5
        assert concept.interaction_count == 1
