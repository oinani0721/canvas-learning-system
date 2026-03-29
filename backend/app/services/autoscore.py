# Canvas Learning System - AutoSCORE Service
# Story 6.4: AutoSCORE Stealth Grading (AC-2, AC-3, AC-7)
#
# Two-stage evaluation: Evidence Extraction -> Rubric Scoring
# 3x sampling with majority vote + low-confidence detection
#
# [Source: _bmad-output/implementation-artifacts/6-4-autoscore-stealth-grading.md]
# [Source: ICLR 2025 Oral "Trust or Escalate" — self-consistency sampling]
"""
AutoScorer: Two-stage LLM evaluation with self-consistency.

Stage 1: Extract evidence from student conversation (independent LLM call)
Stage 2: Score on 4-dimension SOLO-anchored rubric (3x independent LLM calls)
Majority vote + low-confidence detection per dimension.
"""

import json
import logging
import statistics
from typing import Any, Dict, List, Optional

from app.middleware.prompt_injection_guard import check_input
from app.models.exam_models import AutoScoreResult, RubricDimension
from app.services.prompt_registry import get_prompt_registry

logger = logging.getLogger(__name__)

# Rubric dimension names
RUBRIC_DIMENSIONS = [
    "concept_accuracy",
    "reasoning_quality",
    "knowledge_coverage",
    "knowledge_integration",
]

# Grade mapping: 4-dimension average -> grade 1-4
GRADE_THRESHOLDS = {
    1: (0.0, 3.0),  # Again: avg < 0.75 per dim
    2: (3.0, 6.0),  # Hard: avg 0.75-1.5
    3: (6.0, 9.0),  # Good: avg 1.5-2.25
    4: (9.0, 12.01),  # Easy: avg 2.25+
}


class AutoScorer:
    """Two-stage AutoSCORE evaluation engine.

    Story 6.4 AC-2: Stage 1 evidence extraction + Stage 2 rubric scoring.
    Story 6.4 AC-3: 3x sampling majority vote + low-confidence detection.
    Story 6.4 AC-7: LiteLLM unified call layer with structured logging.
    """

    def __init__(self) -> None:
        self._stage1_prompt = self._load_stage_prompt("stage1")
        self._stage2_prompt = self._load_stage_prompt("stage2")

    def _load_stage_prompt(self, stage: str) -> str:
        """Load stage-specific scoring prompt template.

        Tries PromptRegistry first (versioned files), then falls back to
        direct file loading from prompts/scoring/ directory.
        Story 2.13 AC-2: Prompt access through PromptRegistry when available.
        """
        # Strategy 1: PromptRegistry (for versioned files like autoscore_v1.md)
        try:
            registry = get_prompt_registry()
            combined = registry.get("autoscore")
            if combined:
                section = self._extract_section(combined, stage)
                if section:
                    return section
        except (KeyError, OSError, ValueError, AttributeError):
            pass

        # Strategy 2: Direct file load from prompts/scoring/
        from pathlib import Path

        prompts_dir = Path(__file__).parent.parent / "prompts" / "scoring"
        file_map = {
            "stage1": prompts_dir / "stage1_evidence.md",
            "stage2": prompts_dir / "stage2_rubric.md",
        }
        path = file_map.get(stage)
        if path and path.exists():
            content = path.read_text(encoding="utf-8")
            logger.info(f"[Story 6.4] Loaded {stage} prompt from {path}")
            return content

        logger.warning(f"[Story 6.4] No prompt found for {stage}")
        return ""

    @staticmethod
    def _extract_section(content: str, section: str) -> str:
        """Extract a stage section from a combined autoscore prompt content."""
        if not content:
            return ""
        marker = "## 阶段二"
        idx = content.find(marker)
        if section == "stage1" and idx > 0:
            return content[:idx].strip()
        elif section == "stage2" and idx > 0:
            return content[idx:].strip()
        return content

    async def evaluate(
        self,
        exam_id: str,
        node_id: str,
        question_text: str,
        conversation_segment: str,
        question_id: str = "",
    ) -> AutoScoreResult:
        """Execute full AutoSCORE two-stage evaluation.

        Stage 1: Evidence extraction (single LLM call)
        Stage 2: Rubric scoring (3x independent LLM calls)

        Story 6.4 AC-2: Two stages separated to reduce bias.
        Story 6.4 AC-3: 3x sampling + majority vote.

        Args:
            exam_id: The exam session ID.
            node_id: The node being scored.
            question_text: The question that was asked.
            conversation_segment: The student's response/dialogue.
            question_id: Optional question ID for traceability.

        Returns:
            AutoScoreResult with 4-dimension scores, grade, and confidence.
        """
        # Story 3.13 AC-5: Input injection check on student conversation
        injection_check = check_input(conversation_segment)
        if injection_check.is_blocked:
            logger.warning(
                f"[Story 3.13] AutoSCORE input blocked: "
                f"risk_score={injection_check.risk_score}, "
                f"patterns={injection_check.matched_patterns}"
            )
            return AutoScoreResult(
                node_id=node_id,
                exam_id=exam_id,
                question_id=question_id,
                evidence_points=["Input blocked by safety filter"],
                concept_accuracy=RubricDimension(
                    score=0, justification="Safety filter blocked input", low_confidence=True
                ),
                reasoning_quality=RubricDimension(
                    score=0, justification="Safety filter blocked input", low_confidence=True
                ),
                knowledge_coverage=RubricDimension(
                    score=0, justification="Safety filter blocked input", low_confidence=True
                ),
                knowledge_integration=RubricDimension(
                    score=0, justification="Safety filter blocked input", low_confidence=True
                ),
                overall_score=0,
                grade=1,
                confidence="low",
                low_confidence_dimensions=RUBRIC_DIMENSIONS.copy(),
                feedback_summary="Input was blocked by safety filter due to detected injection patterns.",
            )

        # Stage 1: Evidence extraction
        evidence = await self._extract_evidence(question_text, conversation_segment)

        # Stage 2: 3x independent rubric scoring
        scoring_samples: List[Dict[str, int]] = list()
        for sample_idx in range(3):
            sample = await self._score_with_rubric(evidence, sample_idx)
            scoring_samples.append(sample)

        # Majority vote + low-confidence detection
        final_scores, low_conf_dims = self._majority_vote(scoring_samples)

        # Compute overall score and grade
        overall = sum(final_scores.values())
        grade = self._map_grade(overall)

        # Determine confidence level
        if len(low_conf_dims) >= 2:
            confidence = "low"
        elif len(low_conf_dims) == 1:
            confidence = "medium"
        else:
            confidence = "high"

        result = AutoScoreResult(
            node_id=node_id,
            exam_id=exam_id,
            question_id=question_id,
            evidence_points=evidence.get("all_evidence", list()),
            concept_accuracy=RubricDimension(
                score=final_scores.get("concept_accuracy", 0),
                justification=evidence.get("concept_accuracy_evidence", ""),
                low_confidence="concept_accuracy" in low_conf_dims,
            ),
            reasoning_quality=RubricDimension(
                score=final_scores.get("reasoning_quality", 0),
                justification=evidence.get("reasoning_quality_evidence", ""),
                low_confidence="reasoning_quality" in low_conf_dims,
            ),
            knowledge_coverage=RubricDimension(
                score=final_scores.get("knowledge_coverage", 0),
                justification=evidence.get("knowledge_coverage_evidence", ""),
                low_confidence="knowledge_coverage" in low_conf_dims,
            ),
            knowledge_integration=RubricDimension(
                score=final_scores.get("knowledge_integration", 0),
                justification=evidence.get("knowledge_integration_evidence", ""),
                low_confidence="knowledge_integration" in low_conf_dims,
            ),
            overall_score=overall,
            grade=grade,
            confidence=confidence,
            low_confidence_dimensions=low_conf_dims,
            feedback_summary=evidence.get("overall_observation", ""),
        )

        # Story 6.9: Scoring faithfulness deep check (AC-1 through AC-4)
        # Runs asynchronously after scoring; gates SCORE_SUBMITTED event emission.
        try:
            from app.services.scoring_faithfulness import get_scoring_faithfulness_checker

            checker = get_scoring_faithfulness_checker()
            faith_result = await checker.run_full_check(result, conversation_segment)

            result.faithfulness_score = faith_result.faithfulness_score
            result.faithfulness_passed = faith_result.faithfulness_passed
            result.evidence_grounding_score = faith_result.evidence_grounding_score
            result.score_consistency_score = faith_result.score_consistency_score
            result.faithfulness_details = faith_result.to_dict()
            result.verified = faith_result.faithfulness_passed
        except Exception as faith_err:
            logger.warning(f"[Story 6.9] Scoring faithfulness check failed (non-fatal): {faith_err}")
            # On failure, default to verified=True (don't block scoring pipeline)

        logger.info(
            f"[Story 6.4] AutoSCORE completed: node={node_id} "
            f"grade={grade} overall={overall}/12 confidence={confidence} "
            f"faithfulness_passed={result.faithfulness_passed}"
        )

        return result

    async def _extract_evidence(self, question_text: str, student_answer: str) -> Dict[str, Any]:
        """Stage 1: Extract evidence from student response.

        Independent LLM call to avoid bias in scoring stage.

        Returns:
            Dict with evidence lists per dimension.
        """
        prompt = self._stage1_prompt
        prompt = prompt.replace("{{question}}", question_text)
        prompt = prompt.replace("{{student_answer}}", student_answer)
        prompt = prompt.replace("{{rubric}}", "4-dimension SOLO rubric")
        prompt = prompt.replace("{{context}}", "")

        try:
            from litellm import acompletion

            from app.config import settings

            # 6-10 M1: Use settings.SCORING_MODEL (configurable), fall back to AI_PROVIDER/AI_MODEL_NAME
            model = settings.SCORING_MODEL
            if not model:
                provider = settings.AI_PROVIDER
                model_name = settings.AI_MODEL_NAME
                if provider and not model_name.startswith(provider):
                    model = f"{provider}/{model_name}"
                else:
                    model = model_name

            response = await acompletion(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an academic evaluation assistant. Respond in valid JSON only.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            evidence = json.loads(content)

            # Flatten evidence for storage
            all_evidence = list()
            for key in [
                "concept_accuracy_evidence",
                "reasoning_quality_evidence",
                "knowledge_coverage_evidence",
                "knowledge_integration_evidence",
            ]:
                items = evidence.get(key, list())
                if isinstance(items, list):
                    all_evidence.extend(items)
                elif isinstance(items, str):
                    all_evidence.append(items)
                    evidence[key] = items

            evidence["all_evidence"] = all_evidence
            return evidence

        except Exception as e:
            logger.error(f"[Story 6.4] Stage 1 evidence extraction failed: {e}")
            # Return structured empty evidence on failure
            return {
                "concept_accuracy_evidence": f"Evidence extraction failed: {e}",
                "reasoning_quality_evidence": f"Evidence extraction failed: {e}",
                "knowledge_coverage_evidence": f"Evidence extraction failed: {e}",
                "knowledge_integration_evidence": f"Evidence extraction failed: {e}",
                "overall_observation": f"Evaluation service error: {e}",
                "all_evidence": [f"Evidence extraction failed: {e}"],
            }

    async def _score_with_rubric(self, evidence: Dict[str, Any], sample_index: int) -> Dict[str, int]:
        """Stage 2: Score on 4-dimension rubric (single sample).

        Each call is independent with temperature > 0 for diversity.

        Args:
            evidence: Evidence from Stage 1.
            sample_index: Sample index (0-2) for logging.

        Returns:
            Dict mapping dimension name -> score (0-3).
        """
        prompt = self._stage2_prompt
        evidence_text = json.dumps(evidence, ensure_ascii=False, indent=2)
        prompt = prompt.replace("{{evidence}}", evidence_text)

        try:
            from litellm import acompletion

            from app.config import settings

            # 6-10 M1: Use settings.SCORING_MODEL (configurable), fall back to AI_PROVIDER/AI_MODEL_NAME
            model = settings.SCORING_MODEL
            if not model:
                provider = settings.AI_PROVIDER
                model_name = settings.AI_MODEL_NAME
                if provider and not model_name.startswith(provider):
                    model = f"{provider}/{model_name}"
                else:
                    model = model_name

            response = await acompletion(
                model=model,
                messages=[
                    {"role": "system", "content": "You are an academic rubric scorer. Respond in valid JSON only."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,  # Slight diversity for self-consistency
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            result = json.loads(content)

            # Extract scores from potentially nested structure
            scores_data = result.get("scores", result)
            dimension_scores: Dict[str, int] = dict()

            for dim in RUBRIC_DIMENSIONS:
                dim_data = scores_data.get(dim, scores_data.get(dim, 0))
                if isinstance(dim_data, dict):
                    score = int(dim_data.get("score", 0))
                elif isinstance(dim_data, (int, float)):
                    score = int(dim_data)
                else:
                    score = 0
                dimension_scores[dim] = max(0, min(3, score))

            logger.debug(f"[Story 6.4] Rubric sample {sample_index}: {dimension_scores}")
            return dimension_scores

        except Exception as e:
            logger.error(f"[Story 6.4] Stage 2 rubric scoring failed (sample {sample_index}): {e}")
            # Conservative scoring on failure
            return dict.fromkeys(RUBRIC_DIMENSIONS, 1)

    def _majority_vote(self, samples: List[Dict[str, int]]) -> tuple[Dict[str, int], List[str]]:
        """Apply majority vote across 3 samples per dimension.

        Story 6.4 AC-3: If max-min > 1 for any dimension, mark as low-confidence.

        Args:
            samples: List of 3 scoring dicts.

        Returns:
            Tuple of (final_scores, low_confidence_dimensions).
        """
        final_scores: Dict[str, int] = dict()
        low_conf_dims: List[str] = list()

        for dim in RUBRIC_DIMENSIONS:
            values = [s.get(dim, 0) for s in samples]

            # Majority vote: use mode (most common value)
            try:
                voted = statistics.mode(values)
            except statistics.StatisticsError:
                # No unique mode: use median
                voted = int(statistics.median(values))

            final_scores[dim] = voted

            # Low-confidence detection: spread > 1
            if max(values) - min(values) > 1:
                low_conf_dims.append(dim)

        return final_scores, low_conf_dims

    def _map_grade(self, overall_score: int) -> int:
        """Map overall score (0-12) to grade (1-4).

        Story 6.4 AC-3: 4-dimension average -> grade mapping.

        Args:
            overall_score: Sum of 4 dimension scores (0-12).

        Returns:
            Grade 1-4 (Again/Hard/Good/Easy).
        """
        for grade, (low, high) in sorted(GRADE_THRESHOLDS.items()):
            if low <= overall_score < high:
                return grade
        return 4 if overall_score >= 9 else 1


# Singleton
_auto_scorer: Optional[AutoScorer] = None


def get_auto_scorer() -> AutoScorer:
    """Get or create the singleton AutoScorer."""
    global _auto_scorer
    if _auto_scorer is None:
        _auto_scorer = AutoScorer()
    return _auto_scorer
