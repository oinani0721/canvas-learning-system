"""Tests for miscellaneous MasteryEngine features."""

from datetime import datetime, timedelta, timezone

import pytest

from app.models.mastery_state import ConceptState, MasteryConfig
from app.services.mastery_engine import MasteryEngine


@pytest.fixture
def engine():
    engine = MasteryEngine.__new__(MasteryEngine)
    engine.config = MasteryConfig()
    engine.fsrs_manager = None
    engine._fusion_engine = None
    return engine


def _concept(**kwargs):
    defaults = dict(
        concept_id="t", topic="Search", name="BFS",
        p_mastery=0.5, interaction_count=5,
        last_interaction_ts=datetime.now(timezone.utc),
        fsrs_stability=100.0,
    )
    defaults.update(kwargs)
    return ConceptState(**defaults)


class TestFreshness:

    def test_fresh_r_above_090(self, engine):
        concept = _concept(
            last_interaction_ts=datetime.now(timezone.utc),
            fsrs_stability=100.0,
        )
        assert engine.freshness(concept) == "fresh"

    def test_recent_r_070_090(self, engine):
        import math
        stability = 10.0
        days = -math.log(0.80) * stability
        concept = _concept(
            last_interaction_ts=datetime.now(timezone.utc) - timedelta(days=days),
            fsrs_stability=stability,
        )
        assert engine.freshness(concept) == "recent"

    def test_due_r_050_070(self, engine):
        import math
        stability = 10.0
        days = -math.log(0.60) * stability
        concept = _concept(
            last_interaction_ts=datetime.now(timezone.utc) - timedelta(days=days),
            fsrs_stability=stability,
        )
        assert engine.freshness(concept) == "due"

    def test_overdue_r_below_050(self, engine):
        concept = _concept(
            last_interaction_ts=datetime.now(timezone.utc) - timedelta(days=100),
            fsrs_stability=1.0,
        )
        assert engine.freshness(concept) == "overdue"


class TestFalseMasteryRisk:

    def test_low_interaction_returns_zero(self, engine):
        concept = _concept(interaction_count=2)
        assert engine.false_mastery_risk(concept) == 0.0

    def test_surprise_failures_factor(self, engine):
        concept = _concept(surprise_failures=3, p_mastery=0.5)
        risk = engine.false_mastery_risk(concept)
        assert risk > 0.0

    def test_stale_factor(self, engine):
        concept = _concept(
            p_mastery=0.9,
            last_interaction_ts=datetime.now(timezone.utc) - timedelta(days=30),
            fsrs_stability=1.0,
        )
        risk = engine.false_mastery_risk(concept)
        assert risk > 0.0

    def test_unverified_factor(self, engine):
        concept = _concept(p_mastery=0.90, fluent_count=0)
        risk = engine.false_mastery_risk(concept)
        assert risk > 0.0

    def test_capped_at_1(self, engine):
        concept = _concept(
            surprise_failures=10, p_mastery=0.95,
            fluent_count=0,
            last_interaction_ts=datetime.now(timezone.utc) - timedelta(days=100),
            fsrs_stability=1.0,
        )
        risk = engine.false_mastery_risk(concept)
        assert risk <= 1.0

    def test_no_risk_when_verified(self, engine):
        concept = _concept(
            p_mastery=0.5, fluent_count=3, surprise_failures=0,
        )
        risk = engine.false_mastery_risk(concept)
        assert risk == 0.0


class TestOverrideManagement:

    def test_set_override_valid_level(self, engine):
        concept = _concept()
        engine.set_override(concept, "proficient", "manual")
        assert concept.override_value == 0.80
        assert concept.override_ts is not None

    def test_set_override_mastered(self, engine):
        concept = _concept()
        engine.set_override(concept, "mastered")
        assert concept.override_value == 0.95

    def test_set_override_not_assessed_clears(self, engine):
        concept = _concept(override_value=0.8, override_ts=datetime.now(timezone.utc))
        engine.set_override(concept, "not_assessed")
        assert concept.override_value is None
        assert concept.override_ts is None

    def test_set_override_invalid_clears(self, engine):
        concept = _concept(override_value=0.8, override_ts=datetime.now(timezone.utc))
        engine.set_override(concept, "invalid_level")
        assert concept.override_value is None

    def test_clear_override(self, engine):
        concept = _concept(override_value=0.8, override_ts=datetime.now(timezone.utc))
        engine.clear_override(concept)
        assert concept.override_value is None
        assert concept.override_ts is None

    def test_set_self_assess_valid_color(self, engine):
        concept = _concept()
        engine.set_self_assess(concept, "1")
        assert concept.self_assess_value == 0.20
        assert concept.self_assess_ts is not None

    def test_set_self_assess_all_colors(self, engine):
        expected = {"1": 0.20, "2": 0.85, "3": 0.55, "4": 0.85, "5": 0.90, "6": 0.40}
        for color, value in expected.items():
            concept = _concept()
            engine.set_self_assess(concept, color)
            assert concept.self_assess_value == value, f"Color {color}"

    def test_set_self_assess_invalid_color_noop(self, engine):
        concept = _concept()
        engine.set_self_assess(concept, "99")
        assert concept.self_assess_value is None


class TestConceptToResponse:

    def test_all_keys_present(self, engine):
        concept = _concept()
        resp = engine.concept_to_response(concept)
        expected_keys = {
            "concept_id", "name", "topic", "effective_proficiency",
            "mastery_level", "mastery_label", "mastery_color",
            "retrievability", "freshness", "fsrs_due_date",
            "override_active", "override_value", "self_assess_value",
            "false_mastery_risk", "interaction_count", "fluent_count",
            "p_mastery", "last_interaction_ts", "fusion_details",
        }
        assert set(resp.keys()) == expected_keys

    def test_values_are_rounded(self, engine):
        concept = _concept(p_mastery=0.12345678)
        resp = engine.concept_to_response(concept)
        assert resp["p_mastery"] == 0.123

    def test_override_active_flag(self, engine):
        concept = _concept(override_value=0.8, override_ts=datetime.now(timezone.utc))
        resp = engine.concept_to_response(concept)
        assert resp["override_active"] is True

    def test_no_override_flag(self, engine):
        concept = _concept()
        resp = engine.concept_to_response(concept)
        assert resp["override_active"] is False


class TestGetReviewCandidates:

    def test_low_proficiency_included(self, engine):
        concepts = [
            _concept(concept_id="low", p_mastery=0.3),
            _concept(concept_id="high", p_mastery=0.9),
        ]
        candidates = engine.get_review_candidates(concepts)
        ids = [c.concept_id for c in candidates]
        assert "low" in ids

    def test_due_freshness_included(self, engine):
        concept = _concept(
            concept_id="stale", p_mastery=0.85,
            last_interaction_ts=datetime.now(timezone.utc) - timedelta(days=50),
            fsrs_stability=1.0,
        )
        candidates = engine.get_review_candidates([concept])
        assert len(candidates) == 1

    def test_fresh_high_proficiency_excluded(self, engine):
        concept = _concept(concept_id="good", p_mastery=0.85)
        candidates = engine.get_review_candidates([concept])
        assert len(candidates) == 0


class TestApplyExternalSignal:

    def test_misconception_penalizes(self, engine):
        concept = _concept(p_mastery=0.8)
        engine.apply_external_signal(concept, "misconception", 0.2)
        assert concept.p_mastery == pytest.approx(0.6, abs=0.01)
        assert concept.false_mastery_flags == 1

    def test_problem_trap_softer_penalty(self, engine):
        concept = _concept(p_mastery=0.8)
        engine.apply_external_signal(concept, "problem_trap", 0.2)
        assert concept.p_mastery == pytest.approx(0.7, abs=0.01)

    def test_guided_thinking_boosts(self, engine):
        concept = _concept(p_mastery=0.5)
        engine.apply_external_signal(concept, "guided_thinking_correct", 0.1)
        assert concept.p_mastery == pytest.approx(0.6, abs=0.01)

    def test_unknown_signal_no_change(self, engine):
        concept = _concept(p_mastery=0.5)
        engine.apply_external_signal(concept, "unknown_signal", 0.5)
        assert concept.p_mastery == 0.5

    def test_misconception_clamped_above_005(self, engine):
        concept = _concept(p_mastery=0.1)
        engine.apply_external_signal(concept, "misconception", 0.5)
        assert concept.p_mastery >= 0.05

    def test_guided_thinking_clamped_below_099(self, engine):
        concept = _concept(p_mastery=0.95)
        engine.apply_external_signal(concept, "guided_thinking_correct", 0.5)
        assert concept.p_mastery <= 0.99
