# Canvas Learning System - Conversation Distiller
# Story 3.8: Structured Extraction from Conversations (AC-2)
#
# LLM-based extraction of structured data from conversation history:
#   - Error records (4-type classification, reusing Story 3.6 classifier)
#   - Tips (key knowledge points)
#   - Key Q&A highlights (valuable Q&A pairs, clustered by topic)
#   - Conversation summary (1-3 sentences)
#
# Uses Flash/lite model via LiteLLM for cost efficiency.
#
# [Source: _bmad-output/implementation-artifacts/3-8-dialog-archive-async-generation.md#Task 2]

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Extraction Result Models
# ═══════════════════════════════════════════════════════════════════════════════


class ExtractedTip(BaseModel):
    """A tip extracted from conversation distillation."""

    content: str
    title: str
    tags: List[str] = Field(default_factory=list)


class ExtractedError(BaseModel):
    """An error extracted from conversation distillation."""

    description: str
    error_type: str = ""  # Will be classified by ErrorClassifier


class ExtractedQA(BaseModel):
    """A key Q&A pair extracted from conversation."""

    question: str
    answer: str
    topic: str = ""


class DistillationResult(BaseModel):
    """Complete distillation result from a conversation."""

    summary: str = Field(default="", description="1-3 sentence conversation summary")
    tips: List[ExtractedTip] = Field(default_factory=list)
    errors: List[ExtractedError] = Field(default_factory=list)
    qa_highlights: List[ExtractedQA] = Field(default_factory=list)
    distilled_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Distillation Prompt
# ═══════════════════════════════════════════════════════════════════════════════

DISTILLATION_PROMPT = """You are a learning analytics expert. Extract structured data from the following conversation between a student and a tutor AI.

Conversation:
{conversation_text}

Extract the following (return ONLY a JSON object):
{{
  "summary": "<1-3 sentence summary of the conversation topic and learning outcome>",
  "tips": [
    {{"content": "<key knowledge point text>", "title": "<short title>", "tags": ["important"|"review"]}}
  ],
  "errors": [
    {{"description": "<description of student error/misconception>"}}
  ],
  "qa_highlights": [
    {{"question": "<valuable question>", "answer": "<key answer>", "topic": "<topic label>"}}
  ]
}}

Rules:
- tips: Extract 0-5 most important knowledge points
- errors: Extract 0-3 student errors/misconceptions (if any)
- qa_highlights: Extract 0-5 most valuable Q&A exchanges
- summary: Brief, focus on what was learned
- If no errors found, return empty array
- Return valid JSON only"""


# ═══════════════════════════════════════════════════════════════════════════════
# Conversation Distiller
# ═══════════════════════════════════════════════════════════════════════════════


class ConversationDistiller:
    """
    Extracts structured learning data from conversation history.

    Story 3.8 AC-2: LLM-based distillation for the dialogue
    distillation channel.

    [Source: _bmad-output/implementation-artifacts/3-8-dialog-archive-async-generation.md#Task 2.2]
    """

    async def distill(
        self,
        messages: List[Dict[str, str]],
        node_id: str,
    ) -> DistillationResult:
        """
        Distill a conversation into structured data.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            node_id: The canvas node ID for context.

        Returns:
            DistillationResult with summary, tips, errors, and Q&A highlights.
        """
        if not messages:
            return DistillationResult()

        # Format conversation text
        conversation_text = self._format_messages(messages)

        # Truncate to avoid token limits (keep last ~8000 chars)
        if len(conversation_text) > 8000:
            conversation_text = (
                "...(earlier messages truncated)...\n\n"
                + conversation_text[-8000:]
            )

        try:
            return await self._llm_distill(conversation_text)
        except Exception as e:
            logger.warning(f"[Story 3.8] Distillation failed: {e}")
            # Return empty result on failure (non-blocking)
            return DistillationResult(
                summary=f"Conversation with {len(messages)} messages (distillation failed)"
            )

    async def distill_and_persist(
        self,
        messages: List[Dict[str, str]],
        node_id: str,
        group_id: str,
    ) -> DistillationResult:
        """
        Distill a conversation and persist results to Graphiti.

        Args:
            messages: List of message dicts.
            node_id: Canvas node ID.
            group_id: Graphiti group_id for memory isolation.

        Returns:
            DistillationResult.
        """
        result = await self.distill(messages, node_id)

        # Persist to Graphiti
        await self._persist_to_graphiti(result, node_id, group_id)

        return result

    async def _llm_distill(self, conversation_text: str) -> DistillationResult:
        """
        Use LLM to extract structured data from conversation.

        Uses a cost-efficient model (Flash) via LiteLLM.

        Args:
            conversation_text: Formatted conversation text.

        Returns:
            DistillationResult parsed from LLM response.
        """
        import litellm

        from app.config import settings

        # Use the configured model (ideally a Flash/lite model for cost)
        provider = settings.AI_PROVIDER
        model_name = settings.AI_MODEL_NAME

        if provider == "google":
            model = f"gemini/{model_name}"
        elif provider == "openrouter":
            model = f"openrouter/{model_name}"
        else:
            model = model_name

        prompt = DISTILLATION_PROMPT.format(
            conversation_text=conversation_text
        )

        response = await litellm.acompletion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0.2,
        )

        content = response.choices[0].message.content.strip()

        # Parse JSON response
        parsed = json.loads(content)

        tips = [
            ExtractedTip(
                content=t.get("content", ""),
                title=t.get("title", "Untitled"),
                tags=t.get("tags", []),
            )
            for t in parsed.get("tips", [])
            if t.get("content")
        ]

        errors = [
            ExtractedError(description=e.get("description", ""))
            for e in parsed.get("errors", [])
            if e.get("description")
        ]

        qa_highlights = [
            ExtractedQA(
                question=qa.get("question", ""),
                answer=qa.get("answer", ""),
                topic=qa.get("topic", ""),
            )
            for qa in parsed.get("qa_highlights", [])
            if qa.get("question") and qa.get("answer")
        ]

        return DistillationResult(
            summary=parsed.get("summary", ""),
            tips=tips,
            errors=errors,
            qa_highlights=qa_highlights,
        )

    async def _persist_to_graphiti(
        self,
        result: DistillationResult,
        node_id: str,
        group_id: str,
    ) -> None:
        """
        Persist distillation results to Graphiti.

        Args:
            result: The distillation result to persist.
            node_id: Canvas node ID.
            group_id: Graphiti group_id.
        """
        try:
            from app.services.memory_service import get_memory_service

            memory_svc = await get_memory_service()

            # Persist summary
            if result.summary:
                await memory_svc.record_knowledge_entity(
                    event_type="conversation_distillation",
                    content=f"Distilled summary for node {node_id}: {result.summary}",
                    metadata={
                        "node_id": node_id,
                        "distilled_at": result.distilled_at,
                        "tip_count": len(result.tips),
                        "error_count": len(result.errors),
                        "qa_count": len(result.qa_highlights),
                    },
                    group_id=group_id,
                )

            # Persist tips
            for tip in result.tips:
                await memory_svc.record_knowledge_entity(
                    event_type="learning_tip",
                    content=f"Tip: {tip.title} | Content: {tip.content}",
                    metadata={
                        "tip_id": str(uuid.uuid4()),
                        "title": tip.title,
                        "content": tip.content,
                        "tags": tip.tags,
                        "node_id": node_id,
                        "source": "distillation",
                    },
                    group_id=group_id,
                )

            # Persist errors via error classifier
            if result.errors:
                from app.services.error_classifier import get_error_classifier

                classifier = get_error_classifier()
                for error in result.errors:
                    try:
                        await classifier.classify(
                            error_description=error.description,
                            node_id=node_id,
                            context="(extracted from conversation distillation)",
                        )
                    except Exception as e:
                        logger.warning(
                            f"[Story 3.8] Error classification failed during "
                            f"distillation: {e}"
                        )

            # Persist Q&A highlights
            for qa in result.qa_highlights:
                await memory_svc.record_knowledge_entity(
                    event_type="qa_highlight",
                    content=f"Q: {qa.question} | A: {qa.answer}",
                    metadata={
                        "question": qa.question,
                        "answer": qa.answer,
                        "topic": qa.topic,
                        "node_id": node_id,
                        "source": "distillation",
                    },
                    group_id=group_id,
                )

            logger.info(
                f"[Story 3.8] Distillation persisted: node={node_id} "
                f"tips={len(result.tips)} errors={len(result.errors)} "
                f"qa={len(result.qa_highlights)}"
            )

        except Exception as e:
            logger.warning(
                f"[Story 3.8] Failed to persist distillation results: {e}"
            )

    def _format_messages(self, messages: List[Dict[str, str]]) -> str:
        """Format message list into readable conversation text."""
        lines = []
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            prefix = "Student" if role == "user" else "Tutor"
            lines.append(f"{prefix}: {content}")
        return "\n\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# Singleton
# ═══════════════════════════════════════════════════════════════════════════════

_distiller_instance: Optional[ConversationDistiller] = None


def get_conversation_distiller() -> ConversationDistiller:
    """Get or create the singleton ConversationDistiller instance."""
    global _distiller_instance
    if _distiller_instance is None:
        _distiller_instance = ConversationDistiller()
    return _distiller_instance
