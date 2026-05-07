"""Wikilink proxy router (Day 2 staging).

Usage in DeepTutor fork:
  Copy to: deeptutor-fork/backend/app/routers/wikilink_proxy.py
  Register in main app: `app.include_router(wikilink_proxy.router)`

Proxies DeepTutor frontend (:8001 / :3782) wikilink calls to Canvas backend (:8011).
Frontend never hits Canvas directly — keeps single CORS origin.
"""

from fastapi import APIRouter, Depends, HTTPException

from app.clients.canvas_client import CanvasClient, CanvasClientError, get_canvas_client


router = APIRouter(prefix="/api/v1/wikilink", tags=["wikilink"])


@router.get("/neighbors")
async def get_neighbors(
    note_path: str,
    hop: int = 2,
    client: CanvasClient = Depends(get_canvas_client),
):
    """Return wikilink neighbors at given hop distance."""
    try:
        return await client.wikilink_neighbors(note_path, hop=hop)
    except CanvasClientError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/build")
async def build_index(client: CanvasClient = Depends(get_canvas_client)):
    """Trigger full vault scan + wikilink index rebuild."""
    try:
        return await client.wikilink_build()
    except CanvasClientError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/stats")
async def get_stats(client: CanvasClient = Depends(get_canvas_client)):
    """Return graph statistics for global GraphView (Day 9)."""
    try:
        return await client.wikilink_stats()
    except CanvasClientError as e:
        raise HTTPException(status_code=502, detail=str(e))
