"""Boundary tests for scoring_faithfulness vacuous-true fix.

Validates Phase 1 of fix-rag-faithfulness-and-add-crag-quality-loop:
the not_applicable contract for `EvidenceGroundingResult`,
`ScoreConsistencyResult`, and `ScoringFaithfulnessChecker.run_full_check`.

Three scenarios where the legacy code returned `score=1.0` (vacuous true)
must now return `score=None` (not_applicable):

1. EvidenceGroundingResult with total_count=0
2. ScoreConsistencyResult with total_count=0
3. run_full_check aggregates only non-None sub-scores
"""

from unittest import mock as _mock

import pytest

from app.services.scoring_faithfulness import (
    EvidenceGroundingResult,
    ScoreConsistencyResult,
    ScoringFaithfulnessChecker,
    ScoringFaithfulnessResult,
)


# ───────────────────────────────────────────────────────────────────────────────
# EvidenceGroundingResult: empty -> score=None, status=not_applicable
# ───────────────────────────────────────────────────────────────────────────────


def test_grounding_score_is_none_when_no_evidence():
    """Empty evidence list must NOT produce vacuous 1.0."""
    result = EvidenceGroundingResult(
        verifications=list(), grounded_count=0, total_count=0
    )

    assert result.score is None
    assert result.status == "not_applicable"
    assert result.total_count == 0


def test_grounding_score_when_partial_match():
    """Sanity: partial match still computes the fraction correctly."""
    result = EvidenceGroundingResult(
        verifications=[
            {"evidence": "a", "verdict": "GROUNDED"},
            {"evidence": "b", "verdict": "UNGROUNDED"},
        ],
        grounded_count=1,
        total_count=2,
    )

    assert result.score == 0.5
    assert result.status == "ok"


def test_grounding_score_when_all_grounded():
    result = EvidenceGroundingResult(
        verifications=[{"evidence": "x", "verdict": "GROUNDED"}],
        grounded_count=1,
        total_count=1,
    )

    assert result.score == 1.0
    assert result.status == "ok"


# ───────────────────────────────────────────────────────────────────────────────
# ScoreConsistencyResult: empty -> score=None, status=not_applicable
# ───────────────────────────────────────────────────────────────────────────────


def test_consistency_score_is_none_when_no_rubric():
    """Empty rubric_scores must NOT produce vacuous 1.0."""
    result = ScoreConsistencyResult(checks=list(), consistent_count=0, total_count=0)

    assert result.score is None
    assert result.status == "not_applicable"


def test_consistency_score_partial_match():
    result = ScoreConsistencyResult(
        checks=[
            {"dimension": "concept", "verdict": "CONSISTENT"},
            {"dimension": "reasoning", "verdict": "INCONSISTENT"},
        ],
        consistent_count=1,
        total_count=2,
    )

    assert result.score == 0.5
    assert result.status == "ok"


# ───────────────────────────────────────────────────────────────────────────────
# run_full_check: aggregates only non-None sub-scores
# ───────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_full_check_excludes_not_applicable_from_combined():
    """When grounding is not_applicable, combined = consistency only."""
    checker = ScoringFaithfulnessChecker()

    grounding_na = EvidenceGroundingResult(
        verifications=list(), grounded_count=0, total_count=0
    )  # score=None
    consistency_ok = ScoreConsistencyResult(
        checks=[{"dimension": "concept", "verdict": "CONSISTENT"}],
        consistent_count=1,
        total_count=1,
    )  # score=1.0

    autoscore_result = _mock.MagicMock()
    autoscore_result.evidence_points = list()  # triggers grounding not_applicable
    autoscore_result.low_confidence_dimensions = list()
    autoscore_result.concept_accuracy = _mock.MagicMock(score=4, justification="ok")
    autoscore_result.reasoning_quality = None
    autoscore_result.knowledge_coverage = None
    autoscore_result.knowledge_integration = None

    with _mock.patch("app.config.get_settings") as mock_settings:
        mock_settings.return_value.FAITHFULNESS_ENABLED = True
        with _mock.patch.object(
            checker,
            "verify_evidence_grounding",
            new_callable=_mock.AsyncMock,
            return_value=grounding_na,
        ):
            with _mock.patch.object(
                checker,
                "verify_score_evidence_consistency",
                new_callable=_mock.AsyncMock,
                return_value=consistency_ok,
            ):
                result = await checker.run_full_check(
                    autoscore_result, "Student response text"
                )

    assert result.faithfulness_score == 1.0  # average of [1.0] (None excluded)
    assert result.evidence_grounding_score is None
    assert result.score_consistency_score == 1.0
    assert "evidence_grounding" in result.not_applicable_checks
    assert "score_consistency" not in result.not_applicable_checks
    assert result.faithfulness_passed is True


@pytest.mark.asyncio
async def test_full_check_both_not_applicable_returns_none():
    """When BOTH sub-checks are not_applicable, combined = None and passed=True."""
    checker = ScoringFaithfulnessChecker()

    grounding_na = EvidenceGroundingResult(
        verifications=list(), grounded_count=0, total_count=0
    )
    consistency_na = ScoreConsistencyResult(
        checks=list(), consistent_count=0, total_count=0
    )

    autoscore_result = _mock.MagicMock()
    autoscore_result.evidence_points = list()
    autoscore_result.low_confidence_dimensions = list()
    autoscore_result.concept_accuracy = None
    autoscore_result.reasoning_quality = None
    autoscore_result.knowledge_coverage = None
    autoscore_result.knowledge_integration = None

    with _mock.patch("app.config.get_settings") as mock_settings:
        mock_settings.return_value.FAITHFULNESS_ENABLED = True
        with _mock.patch.object(
            checker,
            "verify_evidence_grounding",
            new_callable=_mock.AsyncMock,
            return_value=grounding_na,
        ):
            with _mock.patch.object(
                checker,
                "verify_score_evidence_consistency",
                new_callable=_mock.AsyncMock,
                return_value=consistency_na,
            ):
                result = await checker.run_full_check(autoscore_result, "")

    assert result.faithfulness_score is None
    assert result.evidence_grounding_score is None
    assert result.score_consistency_score is None
    assert result.not_applicable_checks == [
        "evidence_grounding",
        "score_consistency",
    ]
    # Neither check could verify anything, so we don't block scoring
    assert result.faithfulness_passed is True


@pytest.mark.asyncio
async def test_full_check_both_ok_averages_correctly():
    """Sanity: when both sub-checks are valid, combined = average."""
    checker = ScoringFaithfulnessChecker()

    grounding = EvidenceGroundingResult(
        verifications=[{"evidence": "x", "verdict": "GROUNDED"}],
        grounded_count=1,
        total_count=1,
    )  # score=1.0
    consistency = ScoreConsistencyResult(
        checks=[
            {"dimension": "a", "verdict": "CONSISTENT"},
            {"dimension": "b", "verdict": "INCONSISTENT"},
        ],
        consistent_count=1,
        total_count=2,
    )  # score=0.5

    autoscore_result = _mock.MagicMock()
    autoscore_result.evidence_points = ["x"]
    autoscore_result.low_confidence_dimensions = list()
    autoscore_result.concept_accuracy = _mock.MagicMock(score=3, justification="meh")
    autoscore_result.reasoning_quality = None
    autoscore_result.knowledge_coverage = None
    autoscore_result.knowledge_integration = None

    with _mock.patch("app.config.get_settings") as mock_settings:
        mock_settings.return_value.FAITHFULNESS_ENABLED = True
        with _mock.patch.object(
            checker,
            "verify_evidence_grounding",
            new_callable=_mock.AsyncMock,
            return_value=grounding,
        ):
            with _mock.patch.object(
                checker,
                "verify_score_evidence_consistency",
                new_callable=_mock.AsyncMock,
                return_value=consistency,
            ):
                result = await checker.run_full_check(autoscore_result, "text")

    assert result.faithfulness_score == 0.75  # (1.0 + 0.5) / 2
    assert result.not_applicable_checks == []
    # 0.75 < 0.85 threshold -> not passed
    assert result.faithfulness_passed is False


# ───────────────────────────────────────────────────────────────────────────────
# ScoringFaithfulnessResult.to_dict: handles None gracefully
# ───────────────────────────────────────────────────────────────────────────────


def test_result_to_dict_handles_none_scores():
    """to_dict must not crash when scores are None."""
    result = ScoringFaithfulnessResult(
        evidence_grounding_score=None,
        score_consistency_score=None,
        faithfulness_score=None,
        faithfulness_passed=True,
        not_applicable_checks=["evidence_grounding", "score_consistency"],
    )

    d = result.to_dict()

    assert d["evidence_grounding_score"] is None
    assert d["score_consistency_score"] is None
    assert d["faithfulness_score"] is None
    assert d["not_applicable_checks"] == [
        "evidence_grounding",
        "score_consistency",
    ]


def test_result_to_dict_rounds_valid_scores():
    """Sanity: valid scores still get rounded to 4 digits."""
    result = ScoringFaithfulnessResult(
        evidence_grounding_score=0.987654321,
        score_consistency_score=0.5,
        faithfulness_score=0.7438271605,
        faithfulness_passed=False,
    )

    d = result.to_dict()

    assert d["evidence_grounding_score"] == 0.9877
    assert d["score_consistency_score"] == 0.5
    assert d["faithfulness_score"] == 0.7438
