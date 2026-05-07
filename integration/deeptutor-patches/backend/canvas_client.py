"""Canvas backend HTTP client (Day 2 staging file).

Usage in DeepTutor fork:
  Copy this file to: deeptutor-fork/backend/app/clients/canvas_client.py

Provides typed async access to Canvas backend (port 8011) for:
  - wikilink graph (search/neighbors/build)
  - exam ACP flow (start/answer/submit/score)
  - mastery (BKT/FSRS query/update)
  - notes search (4-fusion RAG)
  - Graphiti memories search
"""

from __future__ import annotations

import os
from typing import Any

import httpx
from pydantic import BaseModel


CANVAS_BASE_URL = os.getenv("CANVAS_BASE_URL", "http://canvas-backend:8011")
CANVAS_TIMEOUT = float(os.getenv("CANVAS_TIMEOUT_SECONDS", "30"))


class CanvasClientError(Exception):
    """Raised when Canvas backend returns non-2xx or times out."""


class CanvasClient:
    """Async HTTP client for Canvas backend on :8011.

    Designed to be created once per request (FastAPI dependency) and reused.
    All methods raise CanvasClientError on HTTP failure.
    """

    def __init__(self, base_url: str = CANVAS_BASE_URL, timeout: float = CANVAS_TIMEOUT):
        self.base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=timeout)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self._client.aclose()

    async def _request(self, method: str, path: str, **kwargs) -> Any:
        try:
            r = await self._client.request(method, path, **kwargs)
            r.raise_for_status()
            return r.json()
        except httpx.HTTPStatusError as e:
            raise CanvasClientError(f"Canvas {method} {path} -> {e.response.status_code}: {e.response.text[:200]}") from e
        except httpx.RequestError as e:
            raise CanvasClientError(f"Canvas {method} {path} network error: {e}") from e

    # ── Health ──────────────────────────────────────────────────────────────
    async def health(self) -> dict:
        return await self._request("GET", "/api/v1/health")

    # ── Wikilink (Day 1-2 S1 scenario) ──────────────────────────────────────
    async def wikilink_neighbors(self, note_path: str, hop: int = 2) -> dict:
        """Return wikilink neighbors of a note (NetworkX graph traversal)."""
        return await self._request("GET", f"/api/v1/wikilink/neighbors", params={"note_path": note_path, "hop": hop})

    async def wikilink_build(self) -> dict:
        """Trigger full vault scan + index rebuild."""
        return await self._request("POST", "/api/v1/wikilink/build")

    async def wikilink_stats(self) -> dict:
        """Return graph stats (nodes / edges / orphan count)."""
        return await self._request("GET", "/api/v1/wikilink/stats")

    async def search_notes(self, query: str, subject_id: str | None = None, max_results: int = 10) -> dict:
        """Search notes via Canvas 4-fusion RAG (LanceDB + BM25 + wikilink + Graphify)."""
        body = {"query": query, "max_results": max_results}
        if subject_id:
            body["subject_id"] = subject_id
        return await self._request("POST", "/api/v1/notes/search", json=body)

    async def read_note(self, note_path: str) -> dict:
        """Read full markdown content + metadata of a note."""
        return await self._request("GET", "/api/v1/notes/read", params={"note_path": note_path})

    # ── Exam ACP (Day 4 S2 scenario) ────────────────────────────────────────
    async def exam_start(self, node_id: str, session_id: str | None = None) -> dict:
        """Generate question via ACP 5-layer prompt assembly. Returns pipeline_token."""
        body = {"node_id": node_id}
        if session_id:
            body["session_id"] = session_id
        return await self._request("POST", "/api/v1/exam/start", json=body)

    async def exam_score(self, node_id: str, question_id: str, student_answer: str, pipeline_token: str) -> dict:
        """Submit answer for AutoSCORE (4-dim grading). Returns grade(1-4) + new pipeline_token."""
        body = {
            "node_id": node_id,
            "question_id": question_id,
            "student_answer": student_answer,
            "pipeline_token": pipeline_token,
        }
        return await self._request("POST", "/api/v1/exam/score", json=body)

    async def assemble_acp(self, node_id: str, include_related: bool = True) -> dict:
        """Get assembled context package (concept + content + related + mastery)."""
        return await self._request("POST", "/api/v1/exam/assemble_acp", json={"node_id": node_id, "include_related": include_related})

    # ── Mastery (Day 7 S3 scenario) ─────────────────────────────────────────
    async def query_mastery(self, node_id: str) -> dict:
        """Get current BKT + FSRS state of a node."""
        return await self._request("GET", f"/api/v1/mastery/{node_id}")

    async def update_fsrs(self, node_id: str, grade: int, session_id: str, pipeline_token: str) -> dict:
        """Update FSRS difficulty/stability/retrievability after answer."""
        body = {"node_id": node_id, "grade": grade, "session_id": session_id, "pipeline_token": pipeline_token}
        return await self._request("POST", "/api/v1/mastery/update_fsrs", json=body)

    async def update_bkt(self, node_id: str, is_correct: bool, session_id: str, pipeline_token: str) -> dict:
        """Update BKT mastery probability after answer."""
        body = {"node_id": node_id, "is_correct": is_correct, "session_id": session_id, "pipeline_token": pipeline_token}
        return await self._request("POST", "/api/v1/mastery/update_bkt", json=body)

    # ── Memories (Day 8 review loop) ────────────────────────────────────────
    async def search_memories(self, query: str, group_id: str | None = None, max_results: int = 10) -> dict:
        """Search Graphiti episodic memory (errors / successes / journeys)."""
        body = {"query": query, "max_results": max_results}
        if group_id:
            body["group_id"] = group_id
        return await self._request("POST", "/api/v1/memory/search", json=body)

    async def review_due(self) -> dict:
        """Get FSRS due items (Day 0/3/7 schedule)."""
        return await self._request("GET", "/api/v1/review/due")


# ── FastAPI dependency helper ──────────────────────────────────────────────
async def get_canvas_client():
    """Use as: `client: CanvasClient = Depends(get_canvas_client)`"""
    async with CanvasClient() as client:
        yield client
