"""
AI Configuration Runtime Override Endpoint.

Allows the Obsidian plugin frontend to push AI configuration changes
(provider, model, API key) to the backend at runtime, without requiring
a server restart or manual .env editing.

The override modifies the in-memory Settings singleton. On server restart,
values fall back to .env defaults.
"""

import logging
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.config import get_settings

logger = logging.getLogger(__name__)

config_router = APIRouter()


class AIConfigUpdate(BaseModel):
    """Request body for updating AI configuration at runtime."""
    ai_provider: Optional[str] = Field(None, description="AI provider: google, openai, anthropic, openrouter, custom")
    ai_model_name: Optional[str] = Field(None, description="AI model name")
    ai_api_key: Optional[str] = Field(None, description="AI API key")
    ai_base_url: Optional[str] = Field(None, description="AI API base URL (for custom providers)")


class AIConfigResponse(BaseModel):
    """Response showing current AI configuration (key masked)."""
    ai_provider: str
    ai_model_name: str
    ai_base_url: str
    ai_api_key_set: bool  # True if key is non-empty, never expose actual key


@config_router.post("/ai", response_model=AIConfigResponse)
async def update_ai_config(body: AIConfigUpdate):
    """
    Update AI configuration at runtime.

    Modifies the in-memory Settings singleton. Changes persist until server restart,
    at which point values fall back to .env defaults.
    """
    settings = get_settings()
    updated_fields = []

    if body.ai_provider is not None:
        settings.AI_PROVIDER = body.ai_provider
        updated_fields.append(f"AI_PROVIDER={body.ai_provider}")

    if body.ai_model_name is not None:
        settings.AI_MODEL_NAME = body.ai_model_name
        updated_fields.append(f"AI_MODEL_NAME={body.ai_model_name}")

    if body.ai_api_key is not None:
        settings.AI_API_KEY = body.ai_api_key
        updated_fields.append("AI_API_KEY=***")

    if body.ai_base_url is not None:
        settings.AI_BASE_URL = body.ai_base_url
        updated_fields.append(f"AI_BASE_URL={body.ai_base_url}")

    if updated_fields:
        logger.info(f"AI config updated via API: {', '.join(updated_fields)}")
    else:
        logger.debug("AI config update called with no changes")

    return AIConfigResponse(
        ai_provider=settings.AI_PROVIDER,
        ai_model_name=settings.AI_MODEL_NAME,
        ai_base_url=settings.AI_BASE_URL,
        ai_api_key_set=bool(settings.AI_API_KEY),
    )


@config_router.get("/ai", response_model=AIConfigResponse)
async def get_ai_config():
    """Get current AI configuration (API key is masked)."""
    settings = get_settings()
    return AIConfigResponse(
        ai_provider=settings.AI_PROVIDER,
        ai_model_name=settings.AI_MODEL_NAME,
        ai_base_url=settings.AI_BASE_URL,
        ai_api_key_set=bool(settings.AI_API_KEY),
    )
