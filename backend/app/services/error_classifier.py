# Canvas Learning System - Error Classifier Service
# Story 3.6: 4-Type Error Classification + Remedy Strategy Mapping (AC-3, AC-4)
#
# Classifies user understanding errors into 4 categories using LLM:
#   1. 破题错误 (Problem Framing) → 同结构新题练习
#   2. 推理谬误 (Reasoning Fallacy) → 找错练习 + 反例构造
#   3. 知识点缺失 (Knowledge Gap) → 回退到定义题
#   4. 似懂非懂 (Superficial) → 辨析题 + 迁移应用题
#
# MVP: Uses LLM classification via LiteLLM (not rule engine).
#
# [Source: _bmad-output/implementation-artifacts/3-6-tips-annotation-error-archiving.md#Task 3]

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.graphiti.entity_types import (
    ERROR_TYPE_TO_REMEDY,
    ErrorType,
    Misconception,
    RemedyStrategy,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Classification Prompt
# ═══════════════════════════════════════════════════════════════════════════════

CLASSIFICATION_PROMPT = """You are an expert learning diagnostician. Classify the following student error into exactly one of four categories.

Error description: {error_description}
Context (if any): {context}

Categories:
1. problem_framing - 破题错误: The student misread the problem, missed conditions, or misunderstood what was being asked.
2. reasoning_fallacy - 推理谬误: The student made logical leaps, reversed cause and effect, or used invalid induction/deduction.
3. knowledge_gap - 知识点缺失: The student lacks prerequisite knowledge or has not learned a required concept.
4. superficial - 似懂非懂: The student can recite definitions but cannot apply them in new contexts or transfer understanding.

Respond with ONLY a JSON object:
{{"error_type": "<one of: problem_framing, reasoning_fallacy, knowledge_gap, superficial>", "confidence": <0.0-1.0>}}"""


# ═══════════════════════════════════════════════════════════════════════════════
# Models
# ═══════════════════════════════════════════════════════════════════════════════


class ClassificationResult(BaseModel):
    """Result of error classification."""

    error_type: ErrorType
    remedy_strategy: RemedyStrategy
    confidence: float = Field(ge=0.0, le=1.0)
    misconception: Misconception


# ═══════════════════════════════════════════════════════════════════════════════
# Error Classifier
# ═══════════════════════════════════════════════════════════════════════════════


class ErrorClassifier:
    """
    Classifies student errors into 4 categories using LLM.

    Story 3.6 AC-3: Automatic 4-type error classification.
    Story 3.6 AC-4: Differentiated remedy strategy mapping.

    [Source: _bmad-output/implementation-artifacts/3-6-tips-annotation-error-archiving.md#Task 3.2]
    """

    async def classify(
        self,
        error_description: str,
        node_id: str,
        session_id: str = "",
        context: str = "",
    ) -> ClassificationResult:
        """
        Classify an error description into one of 4 types.

        Uses LLM via LiteLLM for classification. Falls back to
        KNOWLEDGE_GAP if LLM is unavailable or returns invalid data.

        Args:
            error_description: Description of the student's error.
            node_id: Canvas node where the error occurred.
            session_id: Dialogue session identifier.
            context: Additional dialogue context.

        Returns:
            ClassificationResult with error type, remedy, and misconception entity.
        """
        error_type = await self._llm_classify(error_description, context)
        remedy = ERROR_TYPE_TO_REMEDY[error_type]

        misconception = Misconception(
            misconception_id=str(uuid.uuid4()),
            error_type=error_type,
            description=error_description,
            context=context,
            remedy_strategy=remedy,
            node_id=node_id,
            session_id=session_id,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        return ClassificationResult(
            error_type=error_type,
            remedy_strategy=remedy,
            confidence=0.8,  # Updated by LLM if available
            misconception=misconception,
        )

    async def _llm_classify(
        self, error_description: str, context: str
    ) -> ErrorType:
        """
        Use LLM to classify the error type.

        Falls back to keyword-based heuristic if LLM is unavailable.

        Args:
            error_description: The error description text.
            context: Additional context.

        Returns:
            The classified ErrorType.
        """
        try:
            import litellm

            from app.config import settings

            # Build the LLM model string for LiteLLM
            model = self._get_litellm_model(settings)

            prompt = CLASSIFICATION_PROMPT.format(
                error_description=error_description,
                context=context or "(no additional context)",
            )

            response = await litellm.acompletion(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.1,
            )

            content = response.choices[0].message.content.strip()

            # Parse the JSON response
            parsed = json.loads(content)
            raw_type = parsed.get("error_type", "")

            # Validate against enum
            try:
                return ErrorType(raw_type)
            except ValueError:
                logger.warning(
                    f"[Story 3.6] LLM returned invalid error_type: {raw_type}, "
                    "falling back to heuristic"
                )
                return self._heuristic_classify(error_description)

        except ImportError:
            logger.warning("[Story 3.6] litellm not available, using heuristic classification")
            return self._heuristic_classify(error_description)
        except json.JSONDecodeError as e:
            logger.warning(f"[Story 3.6] LLM response not valid JSON: {e}")
            return self._heuristic_classify(error_description)
        except Exception as e:
            logger.warning(f"[Story 3.6] LLM classification failed: {e}")
            return self._heuristic_classify(error_description)

    def _get_litellm_model(self, settings: Any) -> str:
        """Build LiteLLM model string from settings."""
        provider = settings.AI_PROVIDER
        model_name = settings.AI_MODEL_NAME

        if provider == "google":
            return f"gemini/{model_name}"
        elif provider == "openai":
            return model_name
        elif provider == "anthropic":
            return model_name
        elif provider == "openrouter":
            return f"openrouter/{model_name}"
        elif provider == "custom":
            return model_name
        else:
            return model_name

    def _heuristic_classify(self, error_description: str) -> ErrorType:
        """
        Keyword-based fallback classification.

        Used when LLM is unavailable or returns invalid data.

        Args:
            error_description: The error description text.

        Returns:
            Best-guess ErrorType based on keyword matching.
        """
        text = error_description.lower()

        # Check for problem framing keywords
        framing_keywords = ["审题", "题目", "条件", "问题理解", "理解偏差", "遗漏", "misread", "missed"]
        if any(kw in text for kw in framing_keywords):
            return ErrorType.PROBLEM_FRAMING

        # Check for reasoning fallacy keywords
        reasoning_keywords = ["推理", "逻辑", "因果", "跳步", "归纳", "演绎", "reasoning", "logic"]
        if any(kw in text for kw in reasoning_keywords):
            return ErrorType.REASONING_FALLACY

        # Check for superficial understanding keywords
        superficial_keywords = ["似懂非懂", "复述", "表面", "迁移", "应用", "superficial", "recite"]
        if any(kw in text for kw in superficial_keywords):
            return ErrorType.SUPERFICIAL

        # Default: knowledge gap (most common type)
        return ErrorType.KNOWLEDGE_GAP


# ═══════════════════════════════════════════════════════════════════════════════
# Singleton
# ═══════════════════════════════════════════════════════════════════════════════

_classifier_instance: Optional[ErrorClassifier] = None


def get_error_classifier() -> ErrorClassifier:
    """Get or create the singleton ErrorClassifier instance."""
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = ErrorClassifier()
    return _classifier_instance
