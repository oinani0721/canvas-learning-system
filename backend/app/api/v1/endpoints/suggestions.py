# Canvas Learning System - Relation Suggestion API
# Story 3.7: LLM Relation Suggestion for Pullout Nodes (AC-2)
#
# POST /api/v1/suggestions/relation - Given two concept contents,
# suggest the most appropriate relationship type via LLM.
#
# Relation types:
#   IS_PREREQUISITE  - 是前置知识 (source -> target)
#   IS_APPLICATION   - 是应用案例 (source -> target)
#   CONTRASTS_WITH   - 是对比概念 (bidirectional)
#   IS_SUBCONCEPT    - 是子概念 (source -> target)
#   SUPPLEMENTS      - 是补充说明 (source -> target)
#
# [Source: _bmad-output/implementation-artifacts/3-7-dialog-pullout-node.md#Task 4]

import asyncio
import json
import logging
import re

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.litellm_config import format_litellm_model, get_runtime_model_config
from app.graphiti.entity_types import (
    RELATION_TYPE_LABELS,
    VALID_RELATION_TYPES,
)

logger = logging.getLogger(__name__)

suggestions_router = APIRouter()


# ═══════════════════════════════════════════════════════════════════════════════
# Request / Response Models
# ═══════════════════════════════════════════════════════════════════════════════


class RelationSuggestionRequest(BaseModel):
    """Request body for relation suggestion."""

    source_content: str = Field(..., min_length=1, description="Content of the source (original) node")
    new_content: str = Field(..., min_length=1, description="Content of the new (pulled-out) node")
    source_node_id: str = Field(default="", description="Source node ID for reference")


class RelationSuggestionResponse(BaseModel):
    """Response with suggested relation type."""

    relation_type: str = Field(..., description="Suggested relation edge label")
    relation_label: str = Field(..., description="Human-readable label for the relation")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score of the suggestion")
    reason: str = Field(default="", description="Brief reason for the suggestion")


# ═══════════════════════════════════════════════════════════════════════════════
# LLM Prompt
# ═══════════════════════════════════════════════════════════════════════════════

RELATION_SUGGESTION_PROMPT = """Given two concepts from a learning knowledge graph, suggest the most appropriate relationship between them.

Source concept (original node): {source_content}

New concept (extracted from dialogue): {new_content}

Available relationship types (pick exactly one):
1. IS_PREREQUISITE - The source is prerequisite knowledge needed to understand the new concept
2. IS_APPLICATION - The new concept is a practical application/example of the source concept
3. CONTRASTS_WITH - The two concepts are contrasting/comparative (bidirectional)
4. IS_SUBCONCEPT - The new concept is a sub-concept or specific instance of the source
5. SUPPLEMENTS - The new concept provides supplementary/additional explanation for the source

Respond with ONLY a JSON object:
{{"relation_type": "<one of the 5 types above>", "confidence": <0.0-1.0>, "reason": "<brief 1-sentence reason>"}}"""


# ═══════════════════════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════════════════════


@suggestions_router.post(
    "/relation",
    response_model=RelationSuggestionResponse,
    summary="Suggest a relationship type between two concepts",
    description="Uses LLM to recommend the most appropriate relationship type "
    "between an original concept node and a newly pulled-out node from dialogue. "
    "Times out after 5 seconds (non-blocking).",
)
async def suggest_relation(
    request: RelationSuggestionRequest,
) -> RelationSuggestionResponse:
    """
    Suggest the best relationship type between two concept nodes.

    Story 3.7 AC-2: LLM auto-suggests relation type after pullout.
    Timeout: 5s. If LLM times out, returns SUPPLEMENTS as default.

    Args:
        request: Source and new node content.

    Returns:
        RelationSuggestionResponse with type, confidence, and reason.
    """
    try:
        result = await asyncio.wait_for(
            _llm_suggest_relation(request.source_content, request.new_content),
            timeout=5.0,
        )
        return result
    except asyncio.TimeoutError:
        logger.warning("[Story 3.7] Relation suggestion LLM timed out (5s)")
        return RelationSuggestionResponse(
            relation_type="SUPPLEMENTS",
            relation_label="是补充说明",
            confidence=0.3,
            reason="LLM suggestion timed out, defaulting to supplements",
        )
    except Exception as e:
        logger.error(f"[Story 3.7] Relation suggestion failed: {e}")
        return RelationSuggestionResponse(
            relation_type="SUPPLEMENTS",
            relation_label="是补充说明",
            confidence=0.3,
            reason=f"Suggestion unavailable: {str(e)[:100]}",
        )


async def _llm_suggest_relation(source_content: str, new_content: str) -> RelationSuggestionResponse:
    """
    Call LLM to suggest a relation type.

    Uses format_litellm_model() for provider-agnostic model string formatting
    and RuntimeModelConfigManager for API key retrieval (Story 1.3 integration).

    Args:
        source_content: The original node content.
        new_content: The pulled-out node content.

    Returns:
        RelationSuggestionResponse with suggested relation.
    """
    try:
        import litellm

        from app.config import settings

        # Build model string using the canonical format_litellm_model utility
        # [Source: Story 1.3 Task 9.4 — LiteLLM model name format mapping]
        model = format_litellm_model(settings.AI_PROVIDER, settings.AI_MODEL_NAME)

        # Retrieve API key from RuntimeModelConfigManager (in-memory, Story 1.3)
        # Falls back to None if not configured (LiteLLM checks env vars)
        runtime_cfg = get_runtime_model_config()
        api_key = runtime_cfg.get_chat_api_key()

        prompt = RELATION_SUGGESTION_PROMPT.format(
            source_content=source_content[:500],
            new_content=new_content[:500],
        )

        kwargs: dict = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 150,
            "temperature": 0.1,
        }
        if api_key:
            kwargs["api_key"] = api_key

        response = await litellm.acompletion(**kwargs)

        content = response.choices[0].message.content.strip()

        # Strip markdown code fences if present (e.g. ```json ... ```)
        fence_match = re.search(r"```(?:json)?\s*(.*?)\s*```", content, re.DOTALL)
        if fence_match:
            content = fence_match.group(1)

        parsed = json.loads(content)

        relation_type = parsed.get("relation_type", "SUPPLEMENTS")

        # Validate relation type
        if relation_type not in VALID_RELATION_TYPES:
            relation_type = "SUPPLEMENTS"

        relation_label = RELATION_TYPE_LABELS.get(relation_type, "是补充说明")
        confidence = min(max(float(parsed.get("confidence", 0.5)), 0.0), 1.0)
        reason = parsed.get("reason", "")

        return RelationSuggestionResponse(
            relation_type=relation_type,
            relation_label=relation_label,
            confidence=confidence,
            reason=reason,
        )

    except ImportError:
        logger.warning("[Story 3.7] litellm not available for relation suggestion")
        return RelationSuggestionResponse(
            relation_type="SUPPLEMENTS",
            relation_label="是补充说明",
            confidence=0.3,
            reason="LLM not available",
        )
    except json.JSONDecodeError:
        logger.warning("[Story 3.7] LLM returned invalid JSON for relation suggestion")
        return RelationSuggestionResponse(
            relation_type="SUPPLEMENTS",
            relation_label="是补充说明",
            confidence=0.3,
            reason="Could not parse LLM response",
        )
