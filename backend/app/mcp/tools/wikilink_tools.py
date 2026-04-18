"""Wikilink MCP tools — Story 1.3.

get_neighbors: Query N-hop wikilink neighbors of a note.
read_note: Read a vault .md file content.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class GetNeighborsInput(BaseModel):
    note_path: str = Field(
        ...,
        description="Note filename or path (e.g., 'decision-tree' or 'wiki/concepts/decision-tree.md')",
    )
    hop: int = Field(2, ge=1, le=5, description="N-hop neighbor depth (default 2)")


class NeighborItem(BaseModel):
    title: str
    path: str
    hop_distance: int
    frontmatter: Dict[str, Any] = {}


class GetNeighborsOutput(BaseModel):
    note_path: str
    count: int
    neighbors: List[NeighborItem]


class ReadNoteInput(BaseModel):
    note_path: str = Field(
        ...,
        description="Relative path to the .md file within the vault (e.g., 'wiki/concepts/decision-tree.md')",
    )


class ReadNoteOutput(BaseModel):
    path: str
    content: str
    exists: bool


async def get_neighbors(input: GetNeighborsInput) -> Dict[str, Any]:
    from app.services.wikilink_graph_service import get_wikilink_graph_service

    svc = get_wikilink_graph_service()
    if not svc.is_built:
        from app.config import get_settings

        await svc.build(get_settings().CANVAS_BASE_PATH)

    neighbors = svc.get_neighbors(input.note_path, hop=input.hop)
    return GetNeighborsOutput(
        note_path=input.note_path,
        count=len(neighbors),
        neighbors=[
            NeighborItem(
                title=n.title,
                path=n.path,
                hop_distance=n.hop_distance,
                frontmatter=n.frontmatter,
            )
            for n in neighbors
        ],
    ).model_dump()


async def read_note(input: ReadNoteInput) -> Dict[str, Any]:
    from app.config import get_settings

    vault = Path(get_settings().CANVAS_BASE_PATH)
    note = vault / input.note_path
    if not note.is_file():
        stem = input.note_path
        if not stem.endswith(".md"):
            stem += ".md"
        note = vault / stem

    if note.is_file():
        content = note.read_text(encoding="utf-8")
        return ReadNoteOutput(path=str(note), content=content, exists=True).model_dump()

    return ReadNoteOutput(path=input.note_path, content="", exists=False).model_dump()
