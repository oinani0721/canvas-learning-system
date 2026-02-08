"""
LanceDB Auto-Index Service — Story 38.1

Automatically triggers LanceDB index updates after Canvas CRUD operations.
Uses per-canvas debouncing to coalesce rapid updates and tenacity retry
for resilience. Failed index operations are persisted to JSONL for
startup recovery.

AC-1: Auto-trigger after add_node/update_node, async non-blocking, <5s
AC-2: Failure does not block CRUD; 3 retries with exponential backoff
AC-3: Pending operations recovered on startup from JSONL file
"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from tenacity import (
    RetryError,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import settings

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# LanceDB Index Service
# ═══════════════════════════════════════════════════════════════════════════════


class LanceDBIndexService:
    """
    Manages automatic LanceDB indexing for Canvas nodes.

    Features:
    - Per-canvas debounce (default 500ms) to coalesce rapid updates
    - 3x retry with exponential backoff on failure
    - JSONL persistence for failed operations (startup recovery)
    - Lazy LanceDB client initialization
    """

    def __init__(self) -> None:
        self._lancedb_client = None
        self._client_unavailable = False  # [Review H1/M2] skip retries when module missing
        self._pending_tasks: Dict[str, asyncio.Task] = {}
        self._indexing_canvases: set[str] = set()  # [Review M1] track active indexing
        self._pending_file: Path = (
            Path(__file__).parent.parent / "data" / "lancedb_pending_index.jsonl"
        )
        self._debounce_seconds: float = settings.LANCEDB_INDEX_DEBOUNCE_MS / 1000.0
        self._index_timeout: float = settings.LANCEDB_INDEX_TIMEOUT

    # ─────────────────────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────────────────────

    def schedule_index(self, canvas_name: str, canvas_base_path: str) -> None:
        """
        Schedule a debounced LanceDB index update for a canvas.

        If a previous debounce task exists for the same canvas, it is cancelled
        and replaced. This ensures only the latest update triggers indexing.

        Args:
            canvas_name: Canvas name (without .canvas extension)
            canvas_base_path: Base directory for canvas files
        """
        if not settings.ENABLE_LANCEDB_AUTO_INDEX:
            return

        # Cancel existing debounce task for this canvas
        existing = self._pending_tasks.get(canvas_name)
        if existing and not existing.done():
            existing.cancel()
            logger.debug(f"[Story 38.1] Cancelled previous debounce for {canvas_name}")

        # Create new debounced task
        task = asyncio.create_task(
            self._debounced_index(canvas_name, canvas_base_path)
        )
        self._pending_tasks[canvas_name] = task

    async def recover_pending(self, canvas_base_path: str) -> Dict[str, int]:
        """
        Recover and retry pending index operations from JSONL file.

        Called during application startup (AC-3).

        Args:
            canvas_base_path: Base directory for canvas files

        Returns:
            Dict with 'recovered' and 'pending' counts
        """
        if not self._pending_file.exists():
            return {"recovered": 0, "pending": 0}

        try:
            lines = self._pending_file.read_text(encoding="utf-8").strip().splitlines()
        except Exception as e:
            logger.warning(f"[Story 38.1] Failed to read pending file: {e}")
            return {"recovered": 0, "pending": 0}

        if not lines:
            return {"recovered": 0, "pending": 0}

        # Deduplicate: keep latest entry per canvas_name
        unique: Dict[str, Dict[str, Any]] = {}
        for line in lines:
            try:
                entry = json.loads(line)
                unique[entry["canvas_name"]] = entry
            except (json.JSONDecodeError, KeyError):
                continue

        logger.info(
            f"[Story 38.1] LanceDB: {len(unique)} pending index updates recovered"
        )

        recovered = 0
        still_pending: list[Dict[str, Any]] = []

        for canvas_name, entry in unique.items():
            try:
                await self._do_index(canvas_name, canvas_base_path)
                recovered += 1
                logger.info(f"[Story 38.1] Recovered index for {canvas_name}")
            except Exception as e:
                logger.warning(
                    f"[Story 38.1] Recovery failed for {canvas_name}: {e}"
                )
                still_pending.append(entry)

        # Rewrite file with only still-pending entries
        if still_pending:
            self._pending_file.write_text(
                "\n".join(json.dumps(e, ensure_ascii=False) for e in still_pending)
                + "\n",
                encoding="utf-8",
            )
        else:
            # All recovered — remove file
            try:
                self._pending_file.unlink()
            except OSError:
                pass

        return {"recovered": recovered, "pending": len(still_pending)}

    async def cleanup(self) -> None:
        """Cancel all pending debounce tasks. Called during shutdown."""
        for canvas_name, task in self._pending_tasks.items():
            if not task.done():
                task.cancel()
        self._pending_tasks.clear()

    # ─────────────────────────────────────────────────────────────────────────
    # Internal
    # ─────────────────────────────────────────────────────────────────────────

    async def _debounced_index(
        self, canvas_name: str, canvas_base_path: str
    ) -> None:
        """Wait for debounce window, then index with retry."""
        try:
            await asyncio.sleep(self._debounce_seconds)
        except asyncio.CancelledError:
            # A newer update superseded this one — expected behavior
            return

        # [Review M1] Skip if this canvas is already being indexed
        if canvas_name in self._indexing_canvases:
            logger.debug(f"[Story 38.1] Skipping duplicate index for {canvas_name}")
            self._pending_tasks.pop(canvas_name, None)
            return

        # Remove from pending tasks map
        self._pending_tasks.pop(canvas_name, None)

        self._indexing_canvases.add(canvas_name)
        try:
            await self._do_index_with_retry(canvas_name, canvas_base_path)
            logger.info(
                f"[Story 38.1] LanceDB auto-index completed for {canvas_name}"
            )
        except (RetryError, Exception) as e:
            # [Review L1] Fix log: say "canvas" not "node"
            logger.warning(
                f"[Story 38.1] LanceDB index update failed for canvas {canvas_name}, "
                f"queued for retry: {e}"
            )
            self._persist_pending(canvas_name, str(e))
        finally:
            self._indexing_canvases.discard(canvas_name)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    async def _do_index_with_retry(
        self, canvas_name: str, canvas_base_path: str
    ) -> int:
        """Index a canvas with retry. Decorated by tenacity."""
        return await self._do_index(canvas_name, canvas_base_path)

    async def _do_index(
        self, canvas_name: str, canvas_base_path: str
    ) -> int:
        """
        Perform actual LanceDB indexing for a canvas.

        Returns:
            Number of nodes indexed
        """
        # [Review M2] Fast-fail when agentic_rag module is unavailable
        if self._client_unavailable:
            raise RuntimeError("LanceDB client permanently unavailable (module not installed)")

        client = self._get_or_init_client()
        if client is None:
            raise RuntimeError("LanceDB client not available")

        # [Review H1] Use try/except instead of accessing private _initialized
        try:
            if hasattr(client, "initialize"):
                await client.initialize()
        except Exception:
            pass  # initialize() should be idempotent

        # Resolve subject metadata
        from app.services.subject_resolver import get_subject_resolver

        resolver = get_subject_resolver()
        canvas_path = f"{canvas_name}.canvas"
        info = resolver.resolve(canvas_path)

        # Read canvas file from disk
        full_path = Path(canvas_base_path) / canvas_path
        if not full_path.exists():
            raise FileNotFoundError(f"Canvas file not found: {full_path}")

        canvas_data = json.loads(full_path.read_text(encoding="utf-8"))
        nodes = canvas_data.get("nodes", [])

        # Index with timeout (AC-1: within 5 seconds)
        node_count: int = await asyncio.wait_for(
            client.index_canvas(
                canvas_path=canvas_path,
                nodes=nodes,
                table_name="canvas_nodes",
                subject=info.subject,
            ),
            timeout=self._index_timeout,
        )

        return node_count

    def _get_or_init_client(self):
        """Lazy-load LanceDB client (same pattern as metadata.py:get_lancedb_client)."""
        if self._lancedb_client is not None:
            return self._lancedb_client

        try:
            from agentic_rag.clients.lancedb_client import LanceDBClient

            self._lancedb_client = LanceDBClient()
            logger.debug("[Story 38.1] LanceDB client created for auto-index")
            return self._lancedb_client
        except ImportError as e:
            # [Review M2] Mark permanently unavailable to avoid 3x retry waste
            self._client_unavailable = True
            logger.warning(f"[Story 38.1] LanceDB client not available: {e}")
            return None
        except Exception as e:
            logger.warning(f"[Story 38.1] LanceDB client init failed: {e}")
            return None

    def _persist_pending(self, canvas_name: str, error: str) -> None:
        """Persist a failed index operation to JSONL for startup recovery (AC-3)."""
        try:
            entry = {
                "canvas_name": canvas_name,
                "timestamp": datetime.now().isoformat(),
                "error": error,
            }
            self._pending_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._pending_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"[Story 38.1] Failed to persist pending index: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# Module-level Singleton
# ═══════════════════════════════════════════════════════════════════════════════

_lancedb_index_service_instance: Optional[LanceDBIndexService] = None


def get_lancedb_index_service() -> Optional[LanceDBIndexService]:
    """Get or create the singleton LanceDBIndexService."""
    global _lancedb_index_service_instance
    if not settings.ENABLE_LANCEDB_AUTO_INDEX:
        return None
    if _lancedb_index_service_instance is None:
        _lancedb_index_service_instance = LanceDBIndexService()
    return _lancedb_index_service_instance
