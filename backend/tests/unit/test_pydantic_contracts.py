"""Pydantic runtime contract tests: verify models reject invalid data.

Tests that Field(ge=0.0, le=1.0) and other constraints actually work.
Catches regressions if someone removes a validator or widens a range.
"""

import pytest
from pydantic import ValidationError

from app.models.mastery_models import (
    CalibrationRecord,
    CalibrationRequest,
    CalibrationSummary,
    FusionResult,
)
from app.models.review_models import ReviewEntry, ReviewMode
from app.models.qa_models import DifficultyMatchRecord


class TestCalibrationRecordContracts:
    """CalibrationRecord: self_confidence and actual_performance must be 0.0-1.0."""

    def test_valid_values_accepted(self):
        r = CalibrationRecord(
            node_id="node1",
            self_confidence=0.5,
            actual_performance=0.8,
        )
        assert r.self_confidence == 0.5

    def test_boundary_zero(self):
        r = CalibrationRecord(node_id="n", self_confidence=0.0, actual_performance=0.0)
        assert r.self_confidence == 0.0

    def test_boundary_one(self):
        r = CalibrationRecord(node_id="n", self_confidence=1.0, actual_performance=1.0)
        assert r.self_confidence == 1.0

    def test_confidence_above_1_rejected(self):
        with pytest.raises(ValidationError):
            CalibrationRecord(node_id="n", self_confidence=1.1, actual_performance=0.5)

    def test_confidence_negative_rejected(self):
        with pytest.raises(ValidationError):
            CalibrationRecord(node_id="n", self_confidence=-0.1, actual_performance=0.5)

    def test_performance_above_1_rejected(self):
        with pytest.raises(ValidationError):
            CalibrationRecord(node_id="n", self_confidence=0.5, actual_performance=1.5)

    def test_performance_negative_rejected(self):
        with pytest.raises(ValidationError):
            CalibrationRecord(
                node_id="n", self_confidence=0.5, actual_performance=-0.01
            )


class TestFusionResultContracts:
    """FusionResult: fused_mastery must be 0.0-1.0."""

    def test_valid_mastery(self):
        r = FusionResult(fused_mastery=0.75)
        assert r.fused_mastery == 0.75

    def test_mastery_above_1_rejected(self):
        with pytest.raises(ValidationError):
            FusionResult(fused_mastery=1.01)

    def test_mastery_negative_rejected(self):
        with pytest.raises(ValidationError):
            FusionResult(fused_mastery=-0.5)


class TestCalibrationSummaryContracts:
    """CalibrationSummary: stage 1-3, record_count >= 0."""

    def test_valid_stage(self):
        s = CalibrationSummary(stage=2, record_count=15)
        assert s.stage == 2

    def test_stage_zero_rejected(self):
        with pytest.raises(ValidationError):
            CalibrationSummary(stage=0, record_count=0)

    def test_stage_four_rejected(self):
        with pytest.raises(ValidationError):
            CalibrationSummary(stage=4, record_count=0)

    def test_negative_record_count_rejected(self):
        with pytest.raises(ValidationError):
            CalibrationSummary(stage=1, record_count=-1)


class TestReviewEntryContracts:
    """ReviewEntry: pass_rate 0-1, total_concepts >= 0, passed_concepts >= 0."""

    def test_valid_entry(self):
        e = ReviewEntry(
            review_canvas_path="test.canvas",
            date="2025-01-15T10:00:00Z",
            mode=ReviewMode.fresh,
            pass_rate=0.75,
            total_concepts=8,
            passed_concepts=6,
        )
        assert e.pass_rate == 0.75

    def test_pass_rate_above_1_rejected(self):
        with pytest.raises(ValidationError):
            ReviewEntry(
                review_canvas_path="t.canvas",
                date="2025-01-15T10:00:00Z",
                mode=ReviewMode.fresh,
                pass_rate=1.5,
                total_concepts=8,
                passed_concepts=6,
            )

    def test_negative_total_concepts_rejected(self):
        with pytest.raises(ValidationError):
            ReviewEntry(
                review_canvas_path="t.canvas",
                date="2025-01-15T10:00:00Z",
                mode=ReviewMode.fresh,
                pass_rate=0.5,
                total_concepts=-1,
                passed_concepts=0,
            )


class TestDifficultyMatchContracts:
    """DifficultyMatchRecord: proficiency and difficulty 0-1."""

    def test_valid_record(self):
        r = DifficultyMatchRecord(
            node_id="n1",
            proficiency=0.6,
            estimated_difficulty=0.7,
            is_matched=True,
            lower_bound=0.4,
            upper_bound=0.8,
        )
        assert r.proficiency == 0.6

    def test_proficiency_above_1_rejected(self):
        with pytest.raises(ValidationError):
            DifficultyMatchRecord(
                node_id="n1",
                proficiency=2.5,
                estimated_difficulty=0.5,
                is_matched=True,
                lower_bound=0.3,
                upper_bound=0.7,
            )

    def test_difficulty_negative_rejected(self):
        with pytest.raises(ValidationError):
            DifficultyMatchRecord(
                node_id="n1",
                proficiency=0.5,
                estimated_difficulty=-0.1,
                is_matched=True,
                lower_bound=0.3,
                upper_bound=0.7,
            )
