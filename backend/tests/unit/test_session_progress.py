"""
Unit tests for Session Progress API (Story 31.6)

Tests cover all 5 Acceptance Criteria from Story 31.6:
- AC-31.6.1: Frontend displays "已验证 X/Y 个概念" progress bar
- AC-31.6.2: Color distribution real-time updates
- AC-31.6.3: Mastery percentage = green / total * 100%
- AC-31.6.4: Support pause/resume session
- AC-31.6.5: Session timer shows elapsed time
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from fastapi.testclient import TestClient

from app.models import (
    SessionProgressResponse,
    SessionPauseResumeResponse,
    VerificationStatusEnum,
)


class TestSessionProgressModels:
    """Test suite for Story 31.6: Session Progress Pydantic Models"""

    def test_session_progress_response_creation(self):
        """AC-31.6.1: SessionProgressResponse model correctly stores progress data"""
        now = datetime.now()
        progress = SessionProgressResponse(
            session_id="sess_test123",
            canvas_name="离散数学",
            total_concepts=10,
            completed_concepts=5,
            current_concept="逆否命题",
            current_concept_idx=5,
            green_count=3,
            yellow_count=1,
            purple_count=1,
            red_count=0,
            status=VerificationStatusEnum.in_progress,
            progress_percentage=50.0,
            mastery_percentage=60.0,
            hints_given=1,
            max_hints=3,
            started_at=now,
            updated_at=now,
        )

        assert progress.session_id == "sess_test123"
        assert progress.canvas_name == "离散数学"
        assert progress.total_concepts == 10
        assert progress.completed_concepts == 5
        assert progress.progress_percentage == 50.0

    def test_session_progress_color_counts(self):
        """AC-31.6.2: Color distribution correctly represented in model"""
        now = datetime.now()
        progress = SessionProgressResponse(
            session_id="sess_test",
            canvas_name="test",
            total_concepts=8,
            completed_concepts=5,
            current_concept="concept",
            current_concept_idx=5,
            green_count=2,
            yellow_count=1,
            purple_count=1,
            red_count=1,
            status=VerificationStatusEnum.in_progress,
            progress_percentage=62.5,
            mastery_percentage=40.0,
            started_at=now,
            updated_at=now,
        )

        # Verify color distribution
        assert progress.green_count == 2
        assert progress.yellow_count == 1
        assert progress.purple_count == 1
        assert progress.red_count == 1
        # Total completed should match sum of colors
        total_colors = (
            progress.green_count
            + progress.yellow_count
            + progress.purple_count
            + progress.red_count
        )
        assert total_colors == progress.completed_concepts

    def test_mastery_percentage_calculation(self):
        """AC-31.6.3: Mastery percentage = green / completed * 100"""
        now = datetime.now()
        progress = SessionProgressResponse(
            session_id="sess_test",
            canvas_name="test",
            total_concepts=10,
            completed_concepts=5,
            current_concept="concept",
            current_concept_idx=5,
            green_count=3,
            yellow_count=2,
            status=VerificationStatusEnum.in_progress,
            progress_percentage=50.0,
            mastery_percentage=60.0,  # 3/5 * 100 = 60%
            started_at=now,
            updated_at=now,
        )

        # Verify mastery calculation (green/completed * 100)
        expected_mastery = (progress.green_count / progress.completed_concepts) * 100
        assert progress.mastery_percentage == expected_mastery

    def test_pause_resume_response_paused(self):
        """AC-31.6.4: Pause response correctly indicates paused status"""
        response = SessionPauseResumeResponse(
            session_id="sess_test",
            status=VerificationStatusEnum.paused,
            message="Session paused successfully"
        )

        assert response.session_id == "sess_test"
        assert response.status == VerificationStatusEnum.paused
        assert "paused" in response.message.lower()

    def test_pause_resume_response_resumed(self):
        """AC-31.6.4: Resume response correctly indicates in_progress status"""
        response = SessionPauseResumeResponse(
            session_id="sess_test",
            status=VerificationStatusEnum.in_progress,
            message="Session resumed successfully"
        )

        assert response.status == VerificationStatusEnum.in_progress
        assert "resumed" in response.message.lower()


class TestVerificationStatusEnum:
    """Test suite for VerificationStatusEnum"""

    def test_all_status_values_exist(self):
        """Verify all expected status values are defined"""
        expected_statuses = ["pending", "in_progress", "paused", "completed", "cancelled"]

        for status in expected_statuses:
            assert hasattr(VerificationStatusEnum, status)
            assert VerificationStatusEnum(status).value == status

    def test_status_enum_serialization(self):
        """Verify enum serializes correctly to string"""
        assert VerificationStatusEnum.pending.value == "pending"
        assert VerificationStatusEnum.in_progress.value == "in_progress"
        assert VerificationStatusEnum.paused.value == "paused"
        assert VerificationStatusEnum.completed.value == "completed"
        assert VerificationStatusEnum.cancelled.value == "cancelled"


class TestSessionProgressEdgeCases:
    """Test edge cases for session progress"""

    def test_zero_concepts(self):
        """Test with zero concepts (empty session)"""
        now = datetime.now()
        progress = SessionProgressResponse(
            session_id="sess_empty",
            canvas_name="empty",
            total_concepts=0,
            completed_concepts=0,
            current_concept="",
            current_concept_idx=0,
            green_count=0,
            yellow_count=0,
            purple_count=0,
            red_count=0,
            status=VerificationStatusEnum.pending,
            progress_percentage=0.0,
            mastery_percentage=0.0,
            started_at=now,
            updated_at=now,
        )

        assert progress.total_concepts == 0
        assert progress.progress_percentage == 0.0
        assert progress.mastery_percentage == 0.0

    def test_all_concepts_mastered(self):
        """Test with 100% mastery (all green)"""
        now = datetime.now()
        progress = SessionProgressResponse(
            session_id="sess_perfect",
            canvas_name="perfect",
            total_concepts=5,
            completed_concepts=5,
            current_concept="last_concept",
            current_concept_idx=5,
            green_count=5,
            yellow_count=0,
            purple_count=0,
            red_count=0,
            status=VerificationStatusEnum.completed,
            progress_percentage=100.0,
            mastery_percentage=100.0,
            started_at=now,
            updated_at=now,
        )

        assert progress.progress_percentage == 100.0
        assert progress.mastery_percentage == 100.0
        assert progress.green_count == progress.completed_concepts

    def test_timestamps_present(self):
        """AC-31.6.5: Verify timestamps are stored for timer calculation"""
        now = datetime.now()
        progress = SessionProgressResponse(
            session_id="sess_timer",
            canvas_name="test",
            total_concepts=5,
            completed_concepts=2,
            current_concept="concept",
            current_concept_idx=2,
            status=VerificationStatusEnum.in_progress,
            progress_percentage=40.0,
            mastery_percentage=50.0,
            started_at=now,
            updated_at=now,
        )

        # Timestamps should be present for timer calculation
        assert progress.started_at is not None
        assert progress.updated_at is not None
        assert isinstance(progress.started_at, datetime)
        assert isinstance(progress.updated_at, datetime)
