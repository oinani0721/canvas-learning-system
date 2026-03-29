"""
Tests for effective_proficiency computation in MasteryEngine.

Covers:
- effective_proficiency = min(p_mastery, R) core logic
- interaction_count == 0 base = 0.0
- Override exponential decay
- Self-assess exponential decay (2x speed)
- Override + self-assess combined
"""

import math
from datetime import datetime, timedelta, timezone

import pytest

from app.models.mastery_state import ConceptState, MasteryConfig
from app.services.mastery_engine import MasteryEngine


@pytest.fixture
def engine():
    """MasteryEngine with no FSRS (pure computation tests)."""
    engine = MasteryEngine.__new__(MasteryEngine)
    engine.config = MasteryConfig()
    engine.fsrs_manager = None
    engine._fusion_engine = None
    return engine


class TestEffectiveProficiencyCore:
    """Core min(p_mastery, R) logic."""

    def test_min_of_p_and_r(self, engine):
        concept = ConceptState(
            concept_id="t", topic="t", name="t",
            p_mastery=0.8, interaction_count=5,
            last_interaction_ts=datetime.now(timezone.utc),
            fsrs_stability=100.0,
        )
        eff = engine.effective_proficiency(concept)
        assert abs(eff - 0.8) < 0.05

    def test_r_lower_than_p(self, engine):
        concept = ConceptState(
            concept_id="t", topic="t", name="t",
            p_mastery=0.9, interaction_count=5,
            last_interaction_ts=datetime.now(timezone.utc) - timedelta(days=10),
            fsrs_stability=1.0,
        )
        eff = engine.effective_proficiency(concept)
        assert eff < 0.5

    def test_not_assessed_returns_zero(self, engine):
        concept = ConceptState(concept_id="t", topic="t", name="t")
        assert concept.interaction_count == 0
        eff = engine.effective_proficiency(concept)
        assert eff == 0.0

    def test_clamped_to_0_1(self, engine):
        concept = ConceptState(
            concept_id="t", topic="t", name="t",
            p_mastery=0.999, interaction_count=1,
            last_interaction_ts=datetime.now(timezone.utc),
            fsrs_stability=100.0,
        )
        eff = engine.effective_proficiency(concept)
        assert 0.0 <= eff <= 1.0


class TestOverrideDecay:
    """Override exponential decay with weight cap."""

    def test_fresh_override_blends(self, engine):
        concept = ConceptState(
            concept_id="t", topic="t", name="t",
            p_mastery=0.5, interaction_count=5,
            last_interaction_ts=datetime.now(timezone.utc),
            fsrs_stability=100.0,
            override_value=0.95,
            override_ts=datetime.now(timezone.utc),
        )
        eff = engine.effective_proficiency(concept)
        assert abs(eff - 0.86) < 0.05

    def test_old_override_decays(self, engine):
        concept = ConceptState(
            concept_id="t", topic="t", name="t",
            p_mastery=0.5, interaction_count=5,
            last_interaction_ts=datetime.now(timezone.utc),
            fsrs_stability=100.0,
            override_value=0.95,
            override_ts=datetime.now(timezone.utc) - timedelta(days=100),
        )
        eff = engine.effective_proficiency(concept)
        assert abs(eff - 0.5) < 0.05

    def test_no_override_returns_base(self, engine):
        concept = ConceptState(
            concept_id="t", topic="t", name="t",
            p_mastery=0.7, interaction_count=5,
            last_interaction_ts=datetime.now(timezone.utc),
            fsrs_stability=100.0,
        )
        eff = engine.effective_proficiency(concept)
        assert abs(eff - 0.7) < 0.05


class TestSelfAssessDecay:
    """Self-assess exponential decay (2x faster than override)."""

    def test_fresh_self_assess_blends(self, engine):
        concept = ConceptState(
            concept_id="t", topic="t", name="t",
            p_mastery=0.5, interaction_count=5,
            last_interaction_ts=datetime.now(timezone.utc),
            fsrs_stability=100.0,
            self_assess_value=0.9,
            self_assess_ts=datetime.now(timezone.utc),
        )
        eff = engine.effective_proficiency(concept)
        assert abs(eff - 0.70) < 0.05

    def test_self_assess_decays_faster_than_override(self, engine):
        now = datetime.now(timezone.utc)
        days_ago = now - timedelta(days=10)
        c_override = ConceptState(
            concept_id="t", topic="t", name="t",
            p_mastery=0.5, interaction_count=5,
            last_interaction_ts=now, fsrs_stability=100.0,
            override_value=0.9, override_ts=days_ago,
        )
        c_self = ConceptState(
            concept_id="t2", topic="t", name="t",
            p_mastery=0.5, interaction_count=5,
            last_interaction_ts=now, fsrs_stability=100.0,
            self_assess_value=0.9, self_assess_ts=days_ago,
        )
        eff_override = engine.effective_proficiency(c_override)
        eff_self = engine.effective_proficiency(c_self)
        assert eff_override > eff_self

    def test_no_self_assess_returns_current(self, engine):
        concept = ConceptState(
            concept_id="t", topic="t", name="t",
            p_mastery=0.6, interaction_count=3,
            last_interaction_ts=datetime.now(timezone.utc),
            fsrs_stability=100.0,
        )
        eff = engine.effective_proficiency(concept)
        assert abs(eff - 0.6) < 0.05


class TestOverridePlusSelfAssess:
    """Override + self-assess combined."""

    def test_both_applied(self, engine):
        concept = ConceptState(
            concept_id="t", topic="t", name="t",
            p_mastery=0.3, interaction_count=5,
            last_interaction_ts=datetime.now(timezone.utc),
            fsrs_stability=100.0,
            override_value=0.9, override_ts=datetime.now(timezone.utc),
            self_assess_value=0.8, self_assess_ts=datetime.now(timezone.utc),
        )
        eff = engine.effective_proficiency(concept)
        assert eff > 0.5

    def test_not_assessed_with_override(self, engine):
        concept = ConceptState(
            concept_id="t", topic="t", name="t",
            override_value=0.8, override_ts=datetime.now(timezone.utc),
        )
        eff = engine.effective_proficiency(concept)
        assert eff > 0.5
