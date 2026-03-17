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
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.models.exam_models import AutoScoreResult, RubricDimension

logger = logging.getLogger(__name__)

# Prompt template paths
_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

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
        self._stage1_prompt = self._load_prompt("autoscore_v1.md", section="stage1")
        self._stage2_prompt = self._load_prompt("autoscore_v1.md", section="stage2")

    def _load_prompt(self, filename: str, section: str = "") -> str:
        """Load a prompt template from the prompts directory."""
        prompt_path = _PROMPTS_DIR / filename
        if not prompt_path.exists():
            logger.warning(f"[Story 6.4] Prompt template not found: {prompt_path}")
            return ""

        content = prompt_path.read_text(encoding="utf-8")

        if section == "stage1":
            # Extract Stage 1 section
            marker = "## 阶段二"
            idx = content.find(marker)
            if idx > 0:
                return content[:idx].strip()
        elif section == "stage2":
            # Extract Stage 2 section
            marker = "## 阶段二"
            idx = content.find(marker)
            if idx > 0:
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

        logger.info(
            f"[Story 6.4] AutoSCORE completed: node={node_id} "
            f"grade={grade} overall={overall}/12 confidence={confidence}"
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

            model = getattr(settings, "SCORING_MODEL", None) or getattr(
                settings, "LLM_MODEL", "gemini/gemini-2.0-flash"
            )

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

            model = getattr(settings, "SCORING_MODEL", None) or getattr(
                settings, "LLM_MODEL", "gemini/gemini-2.0-flash"
            )

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
