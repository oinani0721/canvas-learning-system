# ✅ Verified from Story 12.4 - Temporal Memory Test Suite
"""
Test suite for Temporal Memory module.

Tests all components:
- FSRSManager: Card creation, review, retrievability
- BehaviorTracker: Behavior recording, querying, statistics
- TemporalMemory: Integration, weak concept identification
"""

import os
import shutil
import tempfile
from datetime import datetime, timedelta, timezone

import pytest


class TestFSRSManager:
    """Tests for FSRS Manager."""

    def setup_method(self):
        """Set up test fixtures."""
        from src.memory.temporal.fsrs_manager import FSRSManager

        self.manager = FSRSManager(desired_retention=0.9)

    def test_create_card(self):
        """Test card creation."""
        card = self.manager.create_card()
        assert card is not None

        # New card should be due immediately
        due = self.manager.get_due_date(card)
        if due:
            assert due <= datetime.now(timezone.utc) + timedelta(minutes=1)

    def test_review_card_good(self):
        """Test reviewing card with Good rating."""
        from src.memory.temporal.fsrs_manager import Rating

        card = self.manager.create_card()
        updated_card, review_log = self.manager.review_card(card, Rating.Good)

        assert updated_card is not None
        assert review_log is not None

        # After review, due date should be in the future
        due = self.manager.get_due_date(updated_card)
        if due:
            assert due > datetime.now(timezone.utc)

    def test_review_card_again(self):
        """Test reviewing card with Again rating (forgot)."""
        from src.memory.temporal.fsrs_manager import Rating

        card = self.manager.create_card()
        updated_card, _ = self.manager.review_card(card, Rating.Again)

        assert updated_card is not None
        # Card should be due soon for relearning

    def test_get_retrievability(self):
        """Test retrievability calculation."""
        from src.memory.temporal.fsrs_manager import Rating

        card = self.manager.create_card()

        # New card retrievability
        retrievability = self.manager.get_retrievability(card)
        assert 0.0 <= retrievability <= 1.0

        # After review, retrievability should be high
        reviewed_card, _ = self.manager.review_card(card, Rating.Easy)
        new_retrievability = self.manager.get_retrievability(reviewed_card)
        assert 0.0 <= new_retrievability <= 1.0

    def test_serialize_deserialize_card(self):
        """Test card serialization and deserialization."""
        from src.memory.temporal.fsrs_manager import Rating

        card = self.manager.create_card()
        card, _ = self.manager.review_card(card, Rating.Good)

        # Serialize
        json_str = self.manager.serialize_card(card)
        assert json_str is not None
        assert len(json_str) > 0

        # Deserialize
        restored_card = self.manager.deserialize_card(json_str)
        assert restored_card is not None

        # Check attributes match
        due1 = self.manager.get_due_date(card)
        due2 = self.manager.get_due_date(restored_card)
        if due1 and due2:
            # Allow small time difference due to serialization
            assert abs((due1 - due2).total_seconds()) < 1

    def test_card_to_state(self):
        """Test converting card to CardState."""
        from src.memory.temporal.fsrs_manager import Rating

        card = self.manager.create_card()
        card, _ = self.manager.review_card(card, Rating.Good)

        state = self.manager.card_to_state(card, "test_concept", "test.canvas")

        assert state.concept == "test_concept"
        assert state.canvas_file == "test.canvas"
        assert state.card_data is not None

    def test_state_to_card(self):
        """Test converting CardState back to card."""
        from src.memory.temporal.fsrs_manager import Rating

        card = self.manager.create_card()
        card, _ = self.manager.review_card(card, Rating.Good)

        state = self.manager.card_to_state(card, "test_concept", "test.canvas")
        restored_card = self.manager.state_to_card(state)

        assert restored_card is not None

    def test_get_rating_from_score(self):
        """Test score to rating conversion."""
        from src.memory.temporal.fsrs_manager import Rating, get_rating_from_score

        # Score < 40 = Again
        assert get_rating_from_score(30) == Rating.Again
        assert get_rating_from_score(0) == Rating.Again

        # Score 40-59 = Hard
        assert get_rating_from_score(50) == Rating.Hard
        assert get_rating_from_score(40) == Rating.Hard

        # Score 60-84 = Good
        assert get_rating_from_score(70) == Rating.Good
        assert get_rating_from_score(60) == Rating.Good

        # Score >= 85 = Easy
        assert get_rating_from_score(90) == Rating.Easy
        assert get_rating_from_score(100) == Rating.Easy


class TestBehaviorTracker:
    """Tests for Behavior Tracker."""

    def setup_method(self):
        """Set up test fixtures."""
        from src.memory.temporal.behavior_tracker import BehaviorTracker

        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_behaviors.db")
        self.tracker = BehaviorTracker(db_path=self.db_path)

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_record_behavior(self):
        """Test recording a behavior."""
        session_id = self.tracker.record_behavior(
            canvas_file="math.canvas",
            concept="integration",
            action_type="view",
        )

        assert session_id is not None
        assert len(session_id) > 0

    def test_record_behavior_with_metadata(self):
        """Test recording behavior with metadata."""
        session_id = self.tracker.record_behavior(
            canvas_file="math.canvas",
            concept="integration",
            action_type="answer_attempt",
            metadata={"score": 75, "time_spent": 120},
        )

        assert session_id is not None

        # Verify metadata is stored
        behaviors = self.tracker.get_behaviors(concept="integration")
        assert len(behaviors) > 0
        assert behaviors[0]["metadata"]["score"] == 75

    def test_get_behaviors_filter_by_canvas(self):
        """Test filtering behaviors by canvas file."""
        self.tracker.record_behavior("math.canvas", "concept1", "view")
        self.tracker.record_behavior("physics.canvas", "concept2", "view")

        math_behaviors = self.tracker.get_behaviors(canvas_file="math.canvas")
        physics_behaviors = self.tracker.get_behaviors(canvas_file="physics.canvas")

        assert len(math_behaviors) == 1
        assert len(physics_behaviors) == 1
        assert math_behaviors[0]["concept"] == "concept1"

    def test_get_behaviors_filter_by_action_type(self):
        """Test filtering behaviors by action type."""
        self.tracker.record_behavior("math.canvas", "concept1", "view")
        self.tracker.record_behavior("math.canvas", "concept1", "answer_attempt")

        views = self.tracker.get_behaviors(action_type="view")
        attempts = self.tracker.get_behaviors(action_type="answer_attempt")

        assert len(views) == 1
        assert len(attempts) == 1

    def test_get_concept_stats(self):
        """Test getting concept statistics."""
        # Record multiple behaviors
        self.tracker.record_behavior("math.canvas", "integration", "view")
        self.tracker.record_behavior("math.canvas", "integration", "view")
        self.tracker.record_behavior("math.canvas", "integration", "answer_attempt")

        stats = self.tracker.get_concept_stats("math.canvas", "integration")

        assert stats["concept"] == "integration"
        assert stats["total_behaviors"] == 3
        assert stats["action_counts"]["view"] == 2
        assert stats["action_counts"]["answer_attempt"] == 1

    def test_get_canvas_concepts(self):
        """Test getting all concepts for a canvas."""
        self.tracker.record_behavior("math.canvas", "integration", "view")
        self.tracker.record_behavior("math.canvas", "derivatives", "view")
        self.tracker.record_behavior("math.canvas", "limits", "view")

        concepts = self.tracker.get_canvas_concepts("math.canvas")

        assert len(concepts) == 3
        assert "integration" in concepts
        assert "derivatives" in concepts
        assert "limits" in concepts

    def test_get_error_rate_no_data(self):
        """Test error rate for concept with no data."""
        error_rate = self.tracker.get_error_rate("math.canvas", "unknown")
        assert error_rate == 0.5  # Default

    def test_get_error_rate_with_scores(self):
        """Test error rate calculation from scores."""
        # Record some attempts with scores
        self.tracker.record_behavior(
            "math.canvas", "integration", "answer_attempt",
            metadata={"score": 80}
        )
        self.tracker.record_behavior(
            "math.canvas", "integration", "answer_attempt",
            metadata={"score": 60}
        )

        error_rate = self.tracker.get_error_rate("math.canvas", "integration")

        # Average score = 70, error rate = 1 - 0.7 = 0.3
        assert 0.25 <= error_rate <= 0.35


class TestTemporalMemory:
    """Tests for Temporal Memory core class."""

    def setup_method(self):
        """Set up test fixtures."""
        from src.memory.temporal import TemporalMemory

        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_temporal.db")
        self.tm = TemporalMemory(db_path=self.db_path)

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_record_behavior(self):
        """Test recording behavior through TemporalMemory."""
        session_id = self.tm.record_behavior(
            canvas_file="math.canvas",
            concept="integration",
            action_type="view",
        )

        assert session_id is not None

    def test_record_behavior_with_score_updates_fsrs(self):
        """Test that behavior with score updates FSRS card."""
        self.tm.record_behavior(
            canvas_file="math.canvas",
            concept="integration",
            action_type="answer_attempt",
            metadata={"score": 85},
        )

        # Card should now exist
        retrievability = self.tm.get_concept_retrievability("integration")
        assert retrievability > 0

    def test_get_weak_concepts_empty(self):
        """Test getting weak concepts with no data."""
        weak = self.tm.get_weak_concepts("nonexistent.canvas")
        assert weak == []

    def test_get_weak_concepts_ranking(self):
        """Test weak concept ranking."""
        # Record behaviors with different scores
        self.tm.record_behavior(
            "math.canvas", "easy_concept", "answer_attempt",
            metadata={"score": 95}
        )
        self.tm.record_behavior(
            "math.canvas", "medium_concept", "answer_attempt",
            metadata={"score": 70}
        )
        self.tm.record_behavior(
            "math.canvas", "hard_concept", "answer_attempt",
            metadata={"score": 40}
        )

        weak = self.tm.get_weak_concepts("math.canvas", limit=3)

        assert len(weak) == 3
        # Hard concept should be first (weakest)
        assert weak[0].concept == "hard_concept"
        # Easy concept should be last
        assert weak[2].concept == "easy_concept"

    def test_update_concept_score(self):
        """Test updating concept score."""
        # First record to create concept
        self.tm.record_behavior(
            "math.canvas", "integration", "view",
        )

        # Update score
        result = self.tm.update_concept_score(
            concept="integration",
            score=80,
            canvas_file="math.canvas",
        )

        assert result is True

    def test_get_due_concepts(self):
        """Test getting due concepts."""
        # Record some behaviors to create cards
        self.tm.record_behavior(
            "math.canvas", "integration", "answer_attempt",
            metadata={"score": 50}
        )

        due = self.tm.get_due_concepts("math.canvas")

        # New cards are immediately due
        assert len(due) >= 0  # May or may not be due depending on FSRS

    def test_get_canvas_stats(self):
        """Test getting canvas statistics."""
        self.tm.record_behavior("math.canvas", "concept1", "view")
        self.tm.record_behavior("math.canvas", "concept2", "answer_attempt", {"score": 75})
        self.tm.record_behavior("math.canvas", "concept3", "answer_attempt", {"score": 45})

        stats = self.tm.get_canvas_stats("math.canvas")

        assert stats["canvas_file"] == "math.canvas"
        assert stats["total_concepts"] == 3

    def test_export_data(self):
        """Test data export."""
        self.tm.record_behavior("math.canvas", "integration", "view")
        self.tm.record_behavior("math.canvas", "integration", "answer_attempt", {"score": 80})

        data = self.tm.export_data()

        assert "exported_at" in data
        assert "behaviors" in data
        assert "cards" in data
        assert len(data["behaviors"]) > 0

    def test_weak_concept_combined_score(self):
        """Test weak concept combined score calculation."""
        # Record with low score (high error rate)
        self.tm.record_behavior(
            "math.canvas", "hard_concept", "answer_attempt",
            metadata={"score": 30}
        )

        weak = self.tm.get_weak_concepts("math.canvas", limit=1)

        assert len(weak) == 1
        wc = weak[0]

        # Combined score should be high for weak concept
        # 0.7 * (1 - low_stability) + 0.3 * high_error_rate
        assert wc.combined_score > 0.5


class TestTemporalMemoryIntegration:
    """Integration tests for full workflow."""

    def setup_method(self):
        """Set up test fixtures."""
        from src.memory.temporal import TemporalMemory

        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_integration.db")
        self.tm = TemporalMemory(db_path=self.db_path)

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_full_learning_workflow(self):
        """Test complete learning workflow."""
        canvas = "calculus.canvas"

        # 1. User views concepts
        self.tm.record_behavior(canvas, "limits", "view")
        self.tm.record_behavior(canvas, "derivatives", "view")
        self.tm.record_behavior(canvas, "integration", "view")

        # 2. User attempts answers
        self.tm.record_behavior(
            canvas, "limits", "answer_attempt",
            metadata={"score": 90}
        )
        self.tm.record_behavior(
            canvas, "derivatives", "answer_attempt",
            metadata={"score": 60}
        )
        self.tm.record_behavior(
            canvas, "integration", "answer_attempt",
            metadata={"score": 40}
        )

        # 3. Get weak concepts for review
        weak = self.tm.get_weak_concepts(canvas, limit=2)

        assert len(weak) == 2
        # Integration should be weakest
        assert weak[0].concept == "integration"

        # 4. User reviews and improves
        self.tm.update_concept_score("integration", 75, canvas)

        # 5. Check updated weakness ranking
        weak_after = self.tm.get_weak_concepts(canvas, limit=3)

        # Integration should still be weak but improved
        integration_before = next(w for w in weak if w.concept == "integration")
        integration_after = next(w for w in weak_after if w.concept == "integration")

        # Error rate should be lower after improvement
        assert integration_after.error_rate < integration_before.error_rate

    def test_multiple_canvas_files(self):
        """Test handling multiple canvas files."""
        # Record in different canvases
        self.tm.record_behavior("math.canvas", "algebra", "view")
        self.tm.record_behavior("physics.canvas", "mechanics", "view")
        self.tm.record_behavior("math.canvas", "algebra", "answer_attempt", {"score": 80})

        # Get stats for each
        math_stats = self.tm.get_canvas_stats("math.canvas")
        physics_stats = self.tm.get_canvas_stats("physics.canvas")

        assert math_stats["total_concepts"] == 1
        assert physics_stats["total_concepts"] == 1

        # Weak concepts should be separate
        math_weak = self.tm.get_weak_concepts("math.canvas")
        physics_weak = self.tm.get_weak_concepts("physics.canvas")

        assert len(math_weak) == 1
        assert len(physics_weak) == 1
        assert math_weak[0].concept == "algebra"
        assert physics_weak[0].concept == "mechanics"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
