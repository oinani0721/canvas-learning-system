"""
Tests for mastery_level computation in MasteryEngine.

Covers:
- 5-level threshold boundary tests
- Explanation gate (fluent_count >= 2)
- Not-assessed node yields L0
"""

from datetime import datetime, timezone

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


def _concept(p_mastery=0.5, interaction_count=5, fluent_count=0):
    """Helper to create concept with controlled proficiency."""
    return ConceptState(
        concept_id="t",
        topic="t",
        name="t",
        p_mastery=p_mastery,
        interaction_count=interaction_count,
        fluent_count=fluent_count,
        last_interaction_ts=datetime.now(timezone.utc),
        fsrs_stability=100.0,
    )


class TestMasteryLevelThresholds:
    """5-level threshold boundary tests."""

    def test_level0_not_assessed(self, engine):
        concept = ConceptState(concept_id="t", topic="t", name="t")
        assert engine.mastery_level(concept) == 0

    def test_level1_below_040(self, engine):
        assert engine.mastery_level(_concept(p_mastery=0.20)) == 1

    def test_level1_boundary_0399(self, engine):
        assert engine.mastery_level(_concept(p_mastery=0.399)) == 1

    def test_level2_at_040(self, engine):
        assert engine.mastery_level(_concept(p_mastery=0.40)) == 2

    def test_level2_boundary_0699(self, engine):
        assert engine.mastery_level(_concept(p_mastery=0.699)) == 2

    def test_level3_at_070(self, engine):
        assert engine.mastery_level(_concept(p_mastery=0.70)) == 3

    def test_level3_boundary_0899(self, engine):
        assert engine.mastery_level(_concept(p_mastery=0.899)) == 3

    def test_level4_at_090_with_fluent(self, engine):
        assert engine.mastery_level(_concept(p_mastery=0.90, fluent_count=2)) == 4

    def test_level4_at_099_with_fluent(self, engine):
        assert engine.mastery_level(_concept(p_mastery=0.99, fluent_count=3)) == 4


class TestExplanationGate:
    """Level 4 requires fluent_count >= mastered_fluent_min."""

    def test_high_score_low_fluent_yields_level3(self, engine):
        assert engine.mastery_level(_concept(p_mastery=0.95, fluent_count=0)) == 3
        assert engine.mastery_level(_concept(p_mastery=0.95, fluent_count=1)) == 3

    def test_high_score_sufficient_fluent_yields_level4(self, engine):
        assert engine.mastery_level(_concept(p_mastery=0.95, fluent_count=2)) == 4
        assert engine.mastery_level(_concept(p_mastery=0.95, fluent_count=5)) == 4


class TestMasteryLabelAndColor:
    """mastery_label and mastery_color helpers."""

    def test_label_not_assessed(self, engine):
        concept = ConceptState(concept_id="t", topic="t", name="t")
        assert engine.mastery_label(concept) == "Not Assessed"

    def test_label_mastered(self, engine):
        assert (
            engine.mastery_label(_concept(p_mastery=0.95, fluent_count=3)) == "Mastered"
        )

    def test_color_not_assessed(self, engine):
        concept = ConceptState(concept_id="t", topic="t", name="t")
        assert engine.mastery_color(concept) == "#6c757d"

    def test_color_mastered(self, engine):
        assert (
            engine.mastery_color(_concept(p_mastery=0.95, fluent_count=3)) == "#198754"
        )

    def test_color_shaky(self, engine):
        assert engine.mastery_color(_concept(p_mastery=0.20)) == "#dc3545"

    def test_color_developing(self, engine):
        assert engine.mastery_color(_concept(p_mastery=0.55)) == "#fd7e14"

    def test_color_proficient(self, engine):
        assert engine.mastery_color(_concept(p_mastery=0.80)) == "#0d6efd"
