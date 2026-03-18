# Canvas Learning System - Scoring Faithfulness Deep Check
# Story 6.9: Evaluates AutoSCORE evidence grounding + score-evidence consistency
#
# Two-stage verification adapted from RAGAS EACL 2024 claim-level NLI:
#   1. Evidence Grounding: Are Stage 1 evidence points traceable to student text?
#   2. Score Consistency: Do Stage 2 justifications align with Stage 1 evidence?
#
# Combined score >= 0.85 passes; otherwise scoring is flagged and mastery not updated.
#
# [Source: _bmad-output/implementation-artifacts/6-9-scoring-faithfulness-deep-check.md]
# [Source: RAGAS EACL 2024 — Faithfulness claim-level NLI]
# [Source: ICLR 2025 Oral "Trust or Escalate" — self-consistency low-confidence]
"""
ScoringFaithfulnessChecker: Verifies AutoSCORE evaluation reliability.

Stage 1 Grounding: evidence_points vs student conversation_segment
Stage 2 Consistency: rubric justifications vs evidence_points
Low-confidence detection: 3x sampling spread > 1 per dimension
"""

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# 6-9 M1 fix: structlog import with fallback to standard logging
try:
    import structlog

    struct_logger = structlog.get_logger("scoring_faithfulness")
except ImportError:
    struct_logger = logger  # type: ignore[assignment]

_PROMPTS_DIR = Path(__file__).parent.parent / "prompts" / "scoring"

# Faithfulness threshold (same as Story 7.1: >= 0.85)
SCORING_FAITHFULNESS_THRESHOLD = 0.85


# ═══════════════════════════════════════════════════════════════════════════════
# Data structures
# ═══════════════════════════════════════════════════════════════════════════════


class EvidenceGroundingResult:
    """Result of evidence grounding verification (Stage 1 check)."""

    __slots__ = ("verifications", "grounded_count", "total_count", "score")

    def __init__(
        self,
        verifications: List[Dict[str, str]],
        grounded_count: int,
        total_count: int,
    ) -> None:
        self.verifications = verifications
        self.grounded_count = grounded_count
        self.total_count = total_count
        self.score = grounded_count / total_count if total_count > 0 else 1.0


class ScoreConsistencyResult:
    """Result of score-evidence consistency verification (Stage 2 check)."""

    __slots__ = ("checks", "consistent_count", "total_count", "score")

    def __init__(
        self,
        checks: List[Dict[str, str]],
        consistent_count: int,
        total_count: int,
    ) -> None:
        self.checks = checks
        self.consistent_count = consistent_count
        self.total_count = total_count
        self.score = consistent_count / total_count if total_count > 0 else 1.0


class ScoringFaithfulnessResult:
    """Complete scoring faithfulness check result."""

    __slots__ = (
        "evidence_grounding_score",
        "score_consistency_score",
        "faithfulness_score",
        "faithfulness_passed",
        "low_confidence_dimensions",
        "overall_low_confidence",
        "details",
        "latency_ms",
    )

    def __init__(
        self,
        evidence_grounding_score: float = 1.0,
        score_consistency_score: float = 1.0,
        faithfulness_score: float = 1.0,
        faithfulness_passed: bool = True,
        low_confidence_dimensions: Optional[List[str]] = None,
        overall_low_confidence: bool = False,
        details: Optional[Dict[str, Any]] = None,
        latency_ms: float = 0.0,
    ) -> None:
        self.evidence_grounding_score = evidence_grounding_score
        self.score_consistency_score = score_consistency_score
        self.faithfulness_score = faithfulness_score
        self.faithfulness_passed = faithfulness_passed
        self.low_confidence_dimensions = low_confidence_dimensions or list()
        self.overall_low_confidence = overall_low_confidence
        self.details = details or dict()
        self.latency_ms = latency_ms

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_grounding_score": round(self.evidence_grounding_score, 4),
            "score_consistency_score": round(self.score_consistency_score, 4),
            "faithfulness_score": round(self.faithfulness_score, 4),
            "faithfulness_passed": self.faithfulness_passed,
            "low_confidence_dimensions": self.low_confidence_dimensions,
            "overall_low_confidence": self.overall_low_confidence,
            "latency_ms": round(self.latency_ms, 2),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Helper: JSON parsing
# ═══════════════════════════════════════════════════════════════════════════════


def _parse_json_response(text: str) -> dict:
    """Parse JSON from LLM response, handling markdown code fences."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = [line for line in lines if not line.strip().startswith("```")]
        cleaned = "\n".join(lines).strip()
    return json.loads(cleaned)


# ═══════════════════════════════════════════════════════════════════════════════
# ScoringFaithfulnessChecker
# ═══════════════════════════════════════════════════════════════════════════════


class ScoringFaithfulnessChecker:
    """Verifies AutoSCORE evaluation faithfulness.

    Two verification stages:
      1. Evidence Grounding: Are extracted evidence points in the student text?
      2. Score Consistency: Do rubric justifications match the evidence?

    [Source: Story 6.9 Task 1]
    """

    def __init__(self) -> None:
        self._grounding_prompt = self._load_prompt("faithfulness_evidence_grounding.md")
        self._consistency_prompt = self._load_prompt("faithfulness_score_consistency.md")

    @staticmethod
    def _load_prompt(filename: str) -> str:
        """Load a prompt template from the scoring prompts directory."""
        path = _PROMPTS_DIR / filename
        if path.exists():
            return path.read_text(encoding="utf-8")
        logger.warning(f"[Story 6.9] Prompt file not found: {path}")
        return ""

    # ───────────────────────────────────────────────────────────────────────
    # Stage 1: Evidence Grounding Verification (AC-1)
    # ───────────────────────────────────────────────────────────────────────

    async def verify_evidence_grounding(
        self,
        evidence_points: List[str],
        conversation_segment: str,
    ) -> EvidenceGroundingResult:
        """Check if each evidence point can be traced to student's original text.

        [Source: Story 6.9 AC-1, Task 1.2]

        Args:
            evidence_points: Evidence extracted during AutoSCORE Stage 1.
            conversation_segment: Student's original response text.

        Returns:
            EvidenceGroundingResult with per-evidence GROUNDED/UNGROUNDED verdicts.
        """
        if not evidence_points:
            return EvidenceGroundingResult(verifications=list(), grounded_count=0, total_count=0)

        import litellm

        from app.config import get_settings

        settings = get_settings()
        model = settings.FAITHFULNESS_MODEL or settings.AI_MODEL_NAME
        provider = settings.AI_PROVIDER
        if provider and not model.startswith(provider):
            model = f"{provider}/{model}"

        evidence_json = json.dumps(evidence_points, ensure_ascii=False)
        user_content = f"Evidence Points:\n{evidence_json}\n\nStudent Original Text:\n{conversation_segment}"

        try:
            response = await litellm.acompletion(
                model=model,
                messages=[
                    {"role": "system", "content": self._grounding_prompt},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.0,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            parsed = _parse_json_response(content)
            verifications = parsed.get("verifications", list())

            grounded = sum(1 for v in verifications if v.get("verdict", "").upper() == "GROUNDED")

            return EvidenceGroundingResult(
                verifications=verifications,
                grounded_count=grounded,
                total_count=len(evidence_points),
            )

        except Exception as e:
            logger.error(f"[Story 6.9] Evidence grounding verification failed: {e}")
            # Conservative: treat all as ungrounded on failure
            return EvidenceGroundingResult(
                verifications=[
                    {"evidence": ep, "verdict": "UNGROUNDED", "reason": f"Verification failed: {e}"}
                    for ep in evidence_points
                ],
                grounded_count=0,
                total_count=len(evidence_points),
            )

    # ───────────────────────────────────────────────────────────────────────
    # Stage 2: Score-Evidence Consistency (AC-2)
    # ───────────────────────────────────────────────────────────────────────

    async def verify_score_evidence_consistency(
        self,
        rubric_scores: Dict[str, Dict[str, Any]],
        evidence_points: List[str],
    ) -> ScoreConsistencyResult:
        """Check if rubric dimension justifications are supported by evidence.

        [Source: Story 6.9 AC-2, Task 1.3]

        Args:
            rubric_scores: Dict of dimension_name -> {score, justification}.
            evidence_points: Evidence from Stage 1.

        Returns:
            ScoreConsistencyResult with per-dimension CONSISTENT/INCONSISTENT.
        """
        if not rubric_scores:
            return ScoreConsistencyResult(checks=list(), consistent_count=0, total_count=0)

        import litellm

        from app.config import get_settings

        settings = get_settings()
        model = settings.FAITHFULNESS_MODEL or settings.AI_MODEL_NAME
        provider = settings.AI_PROVIDER
        if provider and not model.startswith(provider):
            model = f"{provider}/{model}"

        dimensions_json = json.dumps(rubric_scores, ensure_ascii=False, indent=2)
        evidence_json = json.dumps(evidence_points, ensure_ascii=False)

        user_content = f"Rubric Dimensions:\n{dimensions_json}\n\nStage 1 Evidence:\n{evidence_json}"

        try:
            response = await litellm.acompletion(
                model=model,
                messages=[
                    {"role": "system", "content": self._consistency_prompt},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.0,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            parsed = _parse_json_response(content)
            checks = parsed.get("consistency_checks", list())

            consistent = sum(1 for c in checks if c.get("verdict", "").upper() == "CONSISTENT")

            return ScoreConsistencyResult(
                checks=checks,
                consistent_count=consistent,
                total_count=len(rubric_scores),
            )

        except Exception as e:
            logger.error(f"[Story 6.9] Score-evidence consistency check failed: {e}")
            return ScoreConsistencyResult(
                checks=[
                    {"dimension": dim, "verdict": "INCONSISTENT", "reason": f"Check failed: {e}"}
                    for dim in rubric_scores
                ],
                consistent_count=0,
                total_count=len(rubric_scores),
            )

    # ───────────────────────────────────────────────────────────────────────
    # Full check (AC-1 + AC-2 combined)
    # ───────────────────────────────────────────────────────────────────────

    async def run_full_check(
        self,
        autoscore_result: Any,
        conversation_segment: str,
    ) -> ScoringFaithfulnessResult:
        """Execute complete scoring faithfulness check.

        Runs both evidence grounding and score-evidence consistency,
        then computes combined faithfulness score.

        [Source: Story 6.9 Task 1.4]

        Args:
            autoscore_result: AutoScoreResult from autoscore.py.
            conversation_segment: Student's original response.

        Returns:
            ScoringFaithfulnessResult with pass/fail and detailed breakdown.
        """
        start_time = time.perf_counter()

        # Check if faithfulness checking is enabled
        from app.config import get_settings

        settings = get_settings()
        if not settings.FAITHFULNESS_ENABLED:
            return ScoringFaithfulnessResult(
                faithfulness_passed=True,
                details={"status": "disabled"},
            )

        evidence_points = getattr(autoscore_result, "evidence_points", list())

        # Build rubric_scores dict from autoscore_result
        rubric_scores: Dict[str, Dict[str, Any]] = dict()
        for dim_name in [
            "concept_accuracy",
            "reasoning_quality",
            "knowledge_coverage",
            "knowledge_integration",
        ]:
            dim = getattr(autoscore_result, dim_name, None)
            if dim is not None:
                rubric_scores[dim_name] = {
                    "score": dim.score,
                    "justification": dim.justification,
                }

        # Stage 1: Evidence grounding
        grounding = await self.verify_evidence_grounding(evidence_points, conversation_segment)

        # Stage 2: Score-evidence consistency
        consistency = await self.verify_score_evidence_consistency(rubric_scores, evidence_points)

        # Combined score (AC-1/AC-2: average of both)
        combined_score = (grounding.score + consistency.score) / 2.0
        passed = combined_score >= SCORING_FAITHFULNESS_THRESHOLD

        # Low-confidence detection (AC-3): already tracked in AutoScoreResult
        low_conf_dims = getattr(autoscore_result, "low_confidence_dimensions", list())
        overall_low_conf = len(low_conf_dims) >= 2

        latency_ms = (time.perf_counter() - start_time) * 1000

        result = ScoringFaithfulnessResult(
            evidence_grounding_score=grounding.score,
            score_consistency_score=consistency.score,
            faithfulness_score=combined_score,
            faithfulness_passed=passed and not overall_low_conf,
            low_confidence_dimensions=low_conf_dims,
            overall_low_confidence=overall_low_conf,
            details={
                "grounding_verifications": grounding.verifications,
                "consistency_checks": consistency.checks,
            },
            latency_ms=latency_ms,
        )

        # Structured log (AC-5)
        _log_scoring_faithfulness(result, autoscore_result)

        logger.info(
            f"[Story 6.9] Scoring faithfulness check: "
            f"grounding={grounding.score:.3f} consistency={consistency.score:.3f} "
            f"combined={combined_score:.3f} passed={result.faithfulness_passed} "
            f"low_conf_dims={low_conf_dims} latency={latency_ms:.1f}ms"
        )

        return result


# ═══════════════════════════════════════════════════════════════════════════════
# Structured Logging (AC-5)
# ═══════════════════════════════════════════════════════════════════════════════

# Log schema compatible with Story 7.1 FAITHFULNESS_CHECK_LOG_SCHEMA
SCORING_FAITHFULNESS_LOG_SCHEMA = {
    "event": "scoring_faithfulness_check_completed",
    "fields": [
        "check_type",
        "evidence_grounding_score",
        "score_consistency_score",
        "faithfulness_score",
        "faithfulness_passed",
        "low_confidence_dimensions",
        "overall_low_confidence",
        "node_id",
        "exam_id",
        "latency_ms",
    ],
}


def _log_scoring_faithfulness(
    result: ScoringFaithfulnessResult,
    autoscore_result: Any,
) -> None:
    """Emit structured log for scoring faithfulness check (AC-5)."""
    try:
        struct_logger.info(
            "scoring_faithfulness_check_completed",
            check_type="scoring_faithfulness",
            evidence_grounding_score=round(result.evidence_grounding_score, 4),
            score_consistency_score=round(result.score_consistency_score, 4),
            faithfulness_score=round(result.faithfulness_score, 4),
            faithfulness_passed=result.faithfulness_passed,
            low_confidence_dimensions=result.low_confidence_dimensions,
            overall_low_confidence=result.overall_low_confidence,
            node_id=getattr(autoscore_result, "node_id", ""),
            exam_id=getattr(autoscore_result, "exam_id", ""),
            latency_ms=round(result.latency_ms, 2),
        )
    except Exception as e:
        logger.error(f"[Story 6.9] Failed to emit structured log: {e}")

    # Record for health_monitor aggregation (reuse Story 7.1 pattern)
    try:
        from app.middleware.llm_call_logger import get_llm_call_logger

        get_llm_call_logger().record_faithfulness_score(result.faithfulness_score)
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════════════════
# Module-level singleton
# ═══════════════════════════════════════════════════════════════════════════════

_instance: Optional[ScoringFaithfulnessChecker] = None


def get_scoring_faithfulness_checker() -> ScoringFaithfulnessChecker:
    """Get or create the singleton ScoringFaithfulnessChecker."""
    global _instance
    if _instance is None:
        _instance = ScoringFaithfulnessChecker()
    return _instance
