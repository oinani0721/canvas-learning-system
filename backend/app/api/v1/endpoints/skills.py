# Story 3.5: /命令技能集成 — Skills API Endpoint
# [Source: _bmad-output/implementation-artifacts/3-5-skill-command-integration.md]
"""
Skills API endpoints for listing and retrieving skill command templates.

GET /api/v1/skills            — List all available skills (AC-1, AC-3, AC-4)
GET /api/v1/skills/{skill_id} — Get single skill metadata + template content (AC-2, AC-5)
POST /api/v1/skills/refresh   — Rescan commands directory (AC-4: user custom skills)

These endpoints serve the frontend SkillSelector component. The frontend
calls GET /skills on `/` keystroke to display the skill list, then calls
GET /skills/{id} when executing a skill to get the full template content.

Context injection (AC-5) is handled by combining the skill template with
the learning context from GET /context/{node_id} (Story 3.4).
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.skill_registry import get_skill_registry

logger = logging.getLogger(__name__)

skills_router = APIRouter()


# ═══════════════════════════════════════════════════════════════════════════════
# Response Models
# ═══════════════════════════════════════════════════════════════════════════════


class SkillListItem(BaseModel):
    """Single skill in the skills list response."""

    skill_id: str = Field(..., description="Skill identifier (file stem, e.g., 'basic-decompose')")
    name: str = Field(..., description="Display name (e.g., '基础拆解')")
    description: str = Field(..., description="One-line description")
    icon: str = Field(default="file-text", description="Icon identifier")


class SkillListResponse(BaseModel):
    """Response for GET /skills."""

    skills: List[SkillListItem]
    total: int = Field(..., description="Total number of skills")


class SkillDetailResponse(BaseModel):
    """Response for GET /skills/{skill_id}."""

    skill_id: str
    name: str
    description: str
    icon: str
    content: str = Field(..., description="Full .md template content")
    # file_path intentionally excluded from API response to avoid exposing
    # server filesystem paths to the client. The backend uses file_path
    # internally via SkillRegistry but does not surface it in the API.


class SkillRefreshResponse(BaseModel):
    """Response for POST /skills/refresh."""

    refreshed: bool
    total: int = Field(..., description="Total skills after refresh")
    message: str = ""


# ═══════════════════════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════════════════════


@skills_router.get(
    "",
    response_model=SkillListResponse,
    summary="List all available skill commands",
    description=(
        "Returns all registered skill commands from .claude/commands/. "
        "Used by the frontend SkillSelector to populate the skill list "
        "when user types `/` in the chat input. "
        "Story 3.5 AC-1, AC-3."
    ),
)
async def list_skills(
    q: Optional[str] = None,
) -> SkillListResponse:
    """
    List all available skill commands.

    Optionally filter by fuzzy query string (AC-1: fuzzy search support).

    Args:
        q: Optional search query for fuzzy filtering.

    Returns:
        SkillListResponse with skills list and total count.
    """
    registry = get_skill_registry()
    all_skills = registry.list_skills()

    # Apply fuzzy filter if query provided (AC-1: fuzzy search)
    if q and q.strip():
        query = q.strip().lower()
        all_skills = [
            s
            for s in all_skills
            if _fuzzy_match(query, s.name.lower())
            or _fuzzy_match(query, s.description.lower())
            or _fuzzy_match(query, s.skill_id.lower())
        ]

    items = [
        SkillListItem(
            skill_id=s.skill_id,
            name=s.name,
            description=s.description,
            icon=s.icon,
        )
        for s in all_skills
    ]

    return SkillListResponse(skills=items, total=len(items))


@skills_router.get(
    "/{skill_id}",
    response_model=SkillDetailResponse,
    summary="Get skill detail with full template content",
    description=(
        "Returns full skill metadata and .md template content. "
        "Used when executing a skill to inject the prompt template. "
        "Story 3.5 AC-2, AC-5."
    ),
)
async def get_skill(skill_id: str) -> SkillDetailResponse:
    """
    Get a single skill's metadata and full template content.

    Args:
        skill_id: The skill identifier (file stem, e.g., "basic-decompose").

    Returns:
        SkillDetailResponse with full content.

    Raises:
        HTTPException 404: If skill_id not found.
    """
    registry = get_skill_registry()
    skill_content = registry.get_skill_content(skill_id)

    if skill_content is None:
        raise HTTPException(
            status_code=404,
            detail=f"Skill '{skill_id}' not found in .claude/commands/",
        )

    return SkillDetailResponse(
        skill_id=skill_content.skill_id,
        name=skill_content.name,
        description=skill_content.description,
        icon=skill_content.icon,
        content=skill_content.content,
    )


@skills_router.post(
    "/refresh",
    response_model=SkillRefreshResponse,
    summary="Rescan commands directory for new/changed skills",
    description=(
        "Triggers a rescan of .claude/commands/ to pick up newly added "
        "or modified skill template files without restarting the backend. "
        "Story 3.5 AC-4: user custom skills."
    ),
)
async def refresh_skills() -> SkillRefreshResponse:
    """
    Rescan .claude/commands/ directory.

    Returns:
        SkillRefreshResponse with refresh status and new total.
    """
    registry = get_skill_registry()
    total = registry.refresh()

    return SkillRefreshResponse(
        refreshed=True,
        total=total,
        message=f"Rescanned commands directory. {total} skills loaded.",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Fuzzy Match Helper (AC-1)
# ═══════════════════════════════════════════════════════════════════════════════


def _fuzzy_match(query: str, text: str) -> bool:
    """
    Subsequence-based fuzzy match.

    Returns True if all characters in query appear in text in order.
    Example: fuzzy_match("拆", "基础拆解") -> True

    [Source: _bmad-output/implementation-artifacts/3-5-skill-command-integration.md#模糊搜索实现]
    """
    qi = 0
    for ti in range(len(text)):
        if qi < len(query) and text[ti] == query[qi]:
            qi += 1
    return qi == len(query)
