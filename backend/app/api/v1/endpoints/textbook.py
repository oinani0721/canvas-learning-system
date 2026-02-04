# Canvas Learning System - Textbook API Endpoints
# Story: Frontend-Backend Textbook Sync (方案A)
"""
Textbook mounting and synchronization API endpoints.

Enables frontend TextbookMountService to sync mounted textbooks
to backend .canvas-links.json files, bridging the localStorage-to-filesystem gap.

[Source: 计划文件 - 方案A: 前端同步到后端]
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.services.textbook_context_service import get_textbook_context_service

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Request/Response Models
# ═══════════════════════════════════════════════════════════════════════════════

class TextbookSection(BaseModel):
    """Section extracted from a textbook."""
    id: str = Field(..., description="Unique section ID")
    title: str = Field(..., description="Section title")
    level: int = Field(1, description="Heading level (1-6)")
    preview: str = Field("", description="Content preview")
    start_offset: int = Field(0, description="Start offset in file")
    end_offset: int = Field(0, description="End offset in file")
    page_number: Optional[int] = Field(None, description="PDF page number")


class MountedTextbook(BaseModel):
    """Mounted textbook information from frontend."""
    id: str = Field(..., description="Unique textbook ID")
    path: str = Field(..., description="File path in vault")
    name: str = Field(..., description="Display name")
    type: str = Field(..., description="Textbook type: markdown, pdf, canvas")
    sections: List[TextbookSection] = Field(default_factory=list)


class SyncMountRequest(BaseModel):
    """Request to sync a mounted textbook to backend."""
    canvas_path: str = Field(
        ...,
        description="Current Canvas path that the textbook is mounted to"
    )
    textbook: MountedTextbook = Field(
        ...,
        description="Mounted textbook information"
    )


class SyncMountResponse(BaseModel):
    """Response after syncing mounted textbook."""
    success: bool = Field(..., description="Whether sync was successful")
    config_path: str = Field(..., description="Path to .canvas-links.json file")
    message: str = Field("", description="Status message")
    association_id: str = Field("", description="Created association ID")


class UnmountRequest(BaseModel):
    """Request to unmount a textbook."""
    canvas_path: str = Field(..., description="Canvas path")
    textbook_id: str = Field(..., description="Textbook ID to unmount")


class UnmountResponse(BaseModel):
    """Response after unmounting textbook."""
    success: bool
    message: str


class ListMountedResponse(BaseModel):
    """Response listing mounted textbooks for a canvas."""
    canvas_path: str
    associations: List[Dict[str, Any]]
    config_path: str


# ═══════════════════════════════════════════════════════════════════════════════
# Router
# ═══════════════════════════════════════════════════════════════════════════════

textbook_router = APIRouter()


@textbook_router.post(
    "/sync-mount",
    response_model=SyncMountResponse,
    status_code=status.HTTP_200_OK,
    summary="Sync mounted textbook to backend",
    description="""
    Syncs a textbook mounted in the frontend to the backend .canvas-links.json file.

    This bridges the gap between frontend localStorage and backend filesystem,
    enabling Agent services to access textbook context when generating responses.

    [Source: 方案A - 前端同步到后端]
    """
)
async def sync_mount_textbook(request: SyncMountRequest) -> SyncMountResponse:
    """
    Sync a mounted textbook from frontend to backend.

    Creates or updates .canvas-links.json in the same directory as the canvas.
    """
    try:
        service = get_textbook_context_service()

        # Build association data
        association_id = f"mount-{request.textbook.id}"
        association = {
            "association_id": association_id,
            "association_type": "references",
            "target_canvas": request.textbook.path,
            "description": f"{request.textbook.name} ({request.textbook.type})",
            "file_type": request.textbook.type,
            # Include section metadata for PDF page linking
            "sections": [
                {
                    "id": s.id,
                    "title": s.title,
                    "page_number": s.page_number
                }
                for s in request.textbook.sections
                if s.page_number is not None  # Only include if has page number
            ] if request.textbook.type == "pdf" else []
        }

        # Write to .canvas-links.json
        config_path = await service.sync_mounted_textbook(
            canvas_path=request.canvas_path,
            association=association
        )

        # Invalidate cache for this canvas
        service.invalidate_cache(request.canvas_path)

        logger.info(f"[Textbook] Synced mount: {request.textbook.name} -> {request.canvas_path}")

        return SyncMountResponse(
            success=True,
            config_path=config_path,
            message=f"Textbook '{request.textbook.name}' synced successfully",
            association_id=association_id
        )

    except Exception as e:
        logger.error(f"[Textbook] Sync failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync textbook: {str(e)}"
        )


@textbook_router.post(
    "/unmount",
    response_model=UnmountResponse,
    status_code=status.HTTP_200_OK,
    summary="Unmount a textbook",
    description="Removes a textbook association from .canvas-links.json"
)
async def unmount_textbook(request: UnmountRequest) -> UnmountResponse:
    """Remove a textbook association from the canvas."""
    try:
        service = get_textbook_context_service()

        # Remove association
        await service.remove_mounted_textbook(
            canvas_path=request.canvas_path,
            textbook_id=request.textbook_id
        )

        # Invalidate cache
        service.invalidate_cache(request.canvas_path)

        logger.info(f"[Textbook] Unmounted: {request.textbook_id} from {request.canvas_path}")

        return UnmountResponse(
            success=True,
            message="Textbook unmounted successfully"
        )

    except Exception as e:
        logger.error(f"[Textbook] Unmount failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unmount textbook: {str(e)}"
        )


@textbook_router.get(
    "/mounted/{canvas_path:path}",
    response_model=ListMountedResponse,
    status_code=status.HTTP_200_OK,
    summary="List mounted textbooks for a canvas",
    description="Returns all textbook associations from .canvas-links.json"
)
async def list_mounted_textbooks(canvas_path: str) -> ListMountedResponse:
    """Get all mounted textbooks for a canvas."""
    try:
        service = get_textbook_context_service()

        associations = await service._get_associations(canvas_path)
        config_path = service._get_config_path(canvas_path)

        # Filter for 'references' type (mounted textbooks)
        mounted = [
            a for a in associations
            if a.get('association_type') == 'references'
        ]

        return ListMountedResponse(
            canvas_path=canvas_path,
            associations=mounted,
            config_path=config_path
        )

    except Exception as e:
        logger.error(f"[Textbook] List mounted failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list mounted textbooks: {str(e)}"
        )
