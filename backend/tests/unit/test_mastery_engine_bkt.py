"""
Tests for BKT (Bayesian Knowledge Tracing) update logic in MasteryEngine.

Covers:
- Correct answer raises p_mastery (all difficulty levels)
- Incorrect answer lowers p_mastery (all difficulty levels)
- Grade 4 P_G=0 special path
- Boundary values (p_mastery near 0 and 1, clamping to [0.001, 0.999])
- Denominator-zero protection
- Learning transition P_T application
- Interaction count and fluent_count tracking

Reference: Corbett & Anderson, "Knowledge Tracing", 1994
"""

import pytest
from unittest.mock import patch

from app.models.mastery_state import ConceptState, DEFAULT_BKT_PARAMS, MasteryConfig
from app.services.mastery_engine import MasteryEngine


@pytest.fixture
def engine():
    """MasteryEngine with default config and FSRS disabled."""
    with patch("app.services.mastery_engine.FSRS_ENGINE_AVAILABLE", False):
        return MasteryEngine(MasteryConfig())


@pytest.fixture
def concept():
    """Fresh concept with medium difficulty defaults."""
    return ConceptState(concept_id="test-bkt", topic="Search", name="BFS")


class TestBKTCorrectAnswer:
    """BKT posterior update on correct answers (grade >= 3)."""

    def test_correct_answer_raises_p_mastery_medium(self, engine, concept):
        """Grade 3 (correct) on medium difficulty should increase p_mastery."""
        old_p = concept.p_mastery
        engine.update_on_interaction(concept, grade=3)
        assert concept.p_mastery > old_p

    def test_correct_answer_raises_p_mastery_easy(self, engine):
        """Grade 3 on easy difficulty should increase p_mastery."""
        concept = ConceptState(concept_id="t", topic="t", name="t", bkt_difficulty="easy")
        old_p = concept.p_mastery
        engine.update_on_interaction(concept, grade=3)
        assert concept.p_mastery > old_p

    def test_correct_answer_raises_p_mastery_hard(self, engine):
        """Grade 3 on hard difficulty should increase p_mastery."""
        concept = ConceptState(concept_id="t", topic="t", name="t", bkt_difficulty="hard")
        old_p = concept.p_mastery
        engine.update_on_interaction(concept, grade=3)
        assert concept.p_mastery > old_p

    def test_repeated_correct_converges_high(self, engine, concept):
        """Multiple correct answers converge p_mastery toward 1.0."""
        for _ in range(20):
            engine.update_on_interaction(concept, grade=3)
        assert concept.p_mastery > 0.95

    def test_correct_uses_bkt_formula(self, engine):
        """Verify exact BKT posterior for a known input."""
        concept = ConceptState(concept_id="t", topic="t", name="t", p_mastery=0.5)
        params = DEFAULT_BKT_PARAMS["medium"]
        p_prev = 0.5
        P_S = params["P_S"]
        P_G = params["P_G"]
        P_T = params["P_T"]

        # Manual calculation
        numerator = p_prev * (1 - P_S)
        denominator = p_prev * (1 - P_S) + (1 - p_prev) * P_G
        p_posterior = numerator / denominator
        expected = p_posterior + (1 - p_posterior) * P_T
        expected = max(0.001, min(0.999, expected))

        engine.update_on_interaction(concept, grade=3)
        assert abs(concept.p_mastery - expected) < 1e-10


class TestBKTIncorrectAnswer:
    """BKT posterior update on incorrect answers (grade < 3)."""

    def test_incorrect_answer_lowers_p_mastery_medium(self, engine, concept):
        """Grade 1 (forgot) on medium should lower p_mastery initially,
        but P_T may raise it above initial for very low starting p."""
        # Start from a higher mastery to see clear decrease
        concept.p_mastery = 0.6
        old_p = concept.p_mastery
        engine.update_on_interaction(concept, grade=1)
        assert concept.p_mastery < old_p

    def test_incorrect_answer_grade2_medium(self, engine, concept):
        """Grade 2 (struggled) is also incorrect for BKT."""
        concept.p_mastery = 0.6
        old_p = concept.p_mastery
        engine.update_on_interaction(concept, grade=2)
        assert concept.p_mastery < old_p

    def test_incorrect_answer_easy(self, engine):
        """Incorrect on easy difficulty."""
        concept = ConceptState(concept_id="t", topic="t", name="t", bkt_difficulty="easy", p_mastery=0.6)
        old_p = concept.p_mastery
        engine.update_on_interaction(concept, grade=1)
        assert concept.p_mastery < old_p

    def test_incorrect_answer_hard(self, engine):
        """Incorrect on hard difficulty."""
        concept = ConceptState(concept_id="t", topic="t", name="t", bkt_difficulty="hard", p_mastery=0.6)
        old_p = concept.p_mastery
        engine.update_on_interaction(concept, grade=1)
        assert concept.p_mastery < old_p

    def test_repeated_incorrect_converges_low(self, engine):
        """Multiple incorrect answers push p_mastery toward (but above) 0."""
        concept = ConceptState(concept_id="t", topic="t", name="t", p_mastery=0.8)
        for _ in range(20):
            engine.update_on_interaction(concept, grade=1)
        assert concept.p_mastery < 0.3

    def test_incorrect_uses_bkt_formula(self, engine):
        """Verify exact BKT posterior for incorrect answer."""
        concept = ConceptState(concept_id="t", topic="t", name="t", p_mastery=0.5)
        params = DEFAULT_BKT_PARAMS["medium"]
        p_prev = 0.5
        P_S = params["P_S"]
        P_G = params["P_G"]
        P_T = params["P_T"]

        numerator = p_prev * P_S
        denominator = p_prev * P_S + (1 - p_prev) * (1 - P_G)
        p_posterior = numerator / denominator
        expected = p_posterior + (1 - p_posterior) * P_T
        expected = max(0.001, min(0.999, expected))

        engine.update_on_interaction(concept, grade=1)
        assert abs(concept.p_mastery - expected) < 1e-10


class TestBKTGrade4Special:
    """Grade 4 sets P_G=0 (fluent explanation eliminates guessing)."""

    def test_grade4_sets_pg_zero(self, engine, concept):
        """Grade 4 should use P_G=0 in BKT formula."""
        concept.p_mastery = 0.5
        params = DEFAULT_BKT_PARAMS["medium"]
        P_S = params["P_S"]
        P_T = params["P_T"]
        P_G = 0.0  # Grade 4 special case

        numerator = 0.5 * (1 - P_S)
        denominator = 0.5 * (1 - P_S) + 0.5 * P_G
        p_posterior = numerator / denominator if denominator > 0 else 0.5
        expected = p_posterior + (1 - p_posterior) * P_T
        expected = max(0.001, min(0.999, expected))

        engine.update_on_interaction(concept, grade=4)
        assert abs(concept.p_mastery - expected) < 1e-10

    def test_grade4_raises_more_than_grade3(self, engine):
        """Grade 4 (P_G=0) should raise p_mastery more than grade 3."""
        c3 = ConceptState(concept_id="t", topic="t", name="t", p_mastery=0.3)
        c4 = ConceptState(concept_id="t", topic="t", name="t", p_mastery=0.3)

        engine.update_on_interaction(c3, grade=3)
        engine.update_on_interaction(c4, grade=4)

        assert c4.p_mastery > c3.p_mastery

    def test_grade4_increments_fluent_count(self, engine, concept):
        """Grade 4 should increment fluent_count."""
        assert concept.fluent_count == 0
        engine.update_on_interaction(concept, grade=4)
        assert concept.fluent_count == 1
        engine.update_on_interaction(concept, grade=4)
        assert concept.fluent_count == 2

    def test_grade3_does_not_increment_fluent_count(self, engine, concept):
        """Grade 3 should NOT increment fluent_count."""
        engine.update_on_interaction(concept, grade=3)
        assert concept.fluent_count == 0


class TestBKTBoundaryValues:
    """Boundary value tests for BKT clamping and edge cases."""

    def test_p_mastery_clamped_above_0001(self, engine):
        """p_mastery should never go below 0.001."""
        concept = ConceptState(concept_id="t", topic="t", name="t", p_mastery=0.001)
        for _ in range(10):
            engine.update_on_interaction(concept, grade=1)
        assert concept.p_mastery >= 0.001

    def test_p_mastery_clamped_below_0999(self, engine):
        """p_mastery should never go above 0.999."""
        concept = ConceptState(concept_id="t", topic="t", name="t", p_mastery=0.999)
        for _ in range(10):
            engine.update_on_interaction(concept, grade=4)
        assert concept.p_mastery <= 0.999

    def test_denominator_zero_protection_correct(self, engine):
        """When P_G=0 and p_prev=0.001, denominator may approach 0."""
        concept = ConceptState(concept_id="t", topic="t", name="t", p_mastery=0.001)
        # Grade 4 with P_G=0 and very low p_prev
        engine.update_on_interaction(concept, grade=4)
        assert 0.001 <= concept.p_mastery <= 0.999

    def test_denominator_zero_protection_incorrect(self, engine):
        """When P_S approaches 0 and p_prev=0.999, test denominator safety."""
        concept = ConceptState(
            concept_id="t", topic="t", name="t",
            p_mastery=0.999, bkt_difficulty="easy",
        )
        # easy: P_S=0.05 is not zero, but test the safety path
        engine.update_on_interaction(concept, grade=1)
        assert 0.001 <= concept.p_mastery <= 0.999


class TestBKTLearningTransition:
    """Verify P_T (learning transition) is correctly applied."""

    def test_learning_transition_applied(self, engine):
        """P_T should boost p_mastery even after incorrect answers."""
        concept = ConceptState(concept_id="t", topic="t", name="t", p_mastery=0.1)
        params = DEFAULT_BKT_PARAMS["medium"]
        P_S = params["P_S"]
        P_G = params["P_G"]
        P_T = params["P_T"]

        # Manual: incorrect path WITHOUT P_T
        numerator = 0.1 * P_S
        denominator = 0.1 * P_S + 0.9 * (1 - P_G)
        p_posterior_only = numerator / denominator

        # With P_T
        p_with_transition = p_posterior_only + (1 - p_posterior_only) * P_T
        p_with_transition = max(0.001, min(0.999, p_with_transition))

        engine.update_on_interaction(concept, grade=1)
        assert abs(concept.p_mastery - p_with_transition) < 1e-10
        # p_with_transition > p_posterior_only due to P_T
        assert p_with_transition > p_posterior_only


class TestBKTInteractionTracking:
    """Verify interaction_count and last_interaction_ts tracking."""

    def test_interaction_count_increments(self, engine, concept):
        """Each grade call increments interaction_count."""
        assert concept.interaction_count == 0
        engine.update_on_interaction(concept, grade=3)
        assert concept.interaction_count == 1
        engine.update_on_interaction(concept, grade=1)
        assert concept.interaction_count == 2

    def test_last_interaction_ts_set(self, engine, concept):
        """last_interaction_ts should be set after interaction."""
        assert concept.last_interaction_ts is None
        engine.update_on_interaction(concept, grade=3)
        assert concept.last_interaction_ts is not None

    def test_unknown_difficulty_falls_back_to_medium(self, engine):
        """Unknown bkt_difficulty should use medium params."""
        concept = ConceptState(
            concept_id="t", topic="t", name="t",
            p_mastery=0.5, bkt_difficulty="unknown",
        )
        medium_concept = ConceptState(
            concept_id="t2", topic="t", name="t",
            p_mastery=0.5, bkt_difficulty="medium",
        )
        engine.update_on_interaction(concept, grade=3)
        engine.update_on_interaction(medium_concept, grade=3)
        assert abs(concept.p_mastery - medium_concept.p_mastery) < 1e-10
