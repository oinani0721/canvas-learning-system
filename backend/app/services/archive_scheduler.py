# Canvas Learning System - Archive Scheduler
# Story 3.8: Scheduled Archive Task (AC-1)
#
# Registers an asyncio periodic task that runs every 24 hours
# to check all active conversation nodes for archiving needs.
#
# Batch processing: max 10 nodes per check to prevent long blocking.
#
# [Source: _bmad-output/implementation-artifacts/3-8-dialog-archive-async-generation.md#Task 3]

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Default check interval: 24 hours
DEFAULT_CHECK_INTERVAL_SECONDS = 86400  # 24 * 60 * 60


class ArchiveScheduler:
    """
    Periodic scheduler for conversation archiving.

    Story 3.8 AC-1: Runs every 24 hours to check and archive
    conversations that meet Hot-Warm-Cold criteria.

    [Source: _bmad-output/implementation-artifacts/3-8-dialog-archive-async-generation.md#Task 3.2]
    """

    def __init__(
        self,
        check_interval: float = DEFAULT_CHECK_INTERVAL_SECONDS,
    ) -> None:
        self._check_interval = check_interval
        self._task: Optional[asyncio.Task[None]] = None
        self._running = False
        self._last_check: Optional[str] = None
        self._total_archived = 0

    async def start(self) -> None:
        """
        Start the periodic archive check task.

        Called during FastAPI lifespan startup.
        """
        if self._running:
            logger.warning("[Story 3.8] Archive scheduler already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(
            f"[Story 3.8] Archive scheduler started "
            f"(interval={self._check_interval}s)"
        )

    async def stop(self) -> None:
        """
        Stop the periodic archive check task.

        Called during FastAPI lifespan shutdown.
        """
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._task = None
        logger.info("[Story 3.8] Archive scheduler stopped")

    async def trigger_manual_check(self) -> Dict[str, Any]:
        """
        Manually trigger an archive check (for API endpoint).

        Returns:
            Dict with check results.
        """
        return await self._run_check()

    @property
    def status(self) -> Dict[str, Any]:
        """Get scheduler status."""
        return {
            "running": self._running,
            "interval_seconds": self._check_interval,
            "last_check": self._last_check,
            "total_archived": self._total_archived,
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # Internal
    # ═══════════════════════════════════════════════════════════════════════════

    async def _run_loop(self) -> None:
        """Main scheduler loop."""
        while self._running:
            try:
                await asyncio.sleep(self._check_interval)
                if not self._running:
                    break
                await self._run_check()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[Story 3.8] Archive scheduler error: {e}")
                # Continue running despite errors
                await asyncio.sleep(60)  # Brief pause before retry

    async def _run_check(self) -> Dict[str, Any]:
        """
        Execute one archive check cycle.

        Returns:
            Dict with check results.
        """
        logger.info("[Story 3.8] Running archive check...")
        self._last_check = datetime.now(timezone.utc).isoformat()

        try:
            from app.services.conversation_archive import get_archive_manager

            manager = get_archive_manager()

            # Get all active node IDs from memory service
            node_ids = await self._get_active_node_ids()

            if not node_ids:
                logger.info("[Story 3.8] No active nodes to check for archiving")
                return {"checked": 0, "archived": 0}

            results = await manager.batch_check(node_ids)

            archived_count = len(results)
            self._total_archived += archived_count

            logger.info(
                f"[Story 3.8] Archive check complete: "
                f"checked={len(node_ids)} archived={archived_count}"
            )

            return {
                "checked": len(node_ids),
                "archived": archived_count,
                "results": [r.model_dump() for r in results],
            }

        except Exception as e:
            logger.error(f"[Story 3.8] Archive check failed: {e}")
            return {"checked": 0, "archived": 0, "error": str(e)}

    async def _get_active_node_ids(self) -> List[str]:
        """
        Get all node IDs that have active conversations.

        Returns:
            List of node IDs.
        """
        from app.config import DEFAULT_GROUP_ID
        from app.services.memory_service import get_memory_service

        memory_svc = await get_memory_service()

        # Search for all conversation events to find active nodes
        results = await memory_svc.search_memories(
            query="conversation node",
            group_id=DEFAULT_GROUP_ID,
            max_results=50,
        )

        node_ids: set[str] = set()
        if isinstance(results, list):
            for item in results:
                if isinstance(item, dict):
                    nid = item.get("node_id")
                    if not nid:
                        meta = item.get("metadata")
                        if isinstance(meta, dict):
                            nid = meta.get("node_id")
                    if nid:
                        node_ids.add(nid)

        return list(node_ids)


# ═══════════════════════════════════════════════════════════════════════════════
# Singleton
# ═══════════════════════════════════════════════════════════════════════════════

_scheduler_instance: Optional[ArchiveScheduler] = None


def get_archive_scheduler() -> ArchiveScheduler:
    """Get or create the singleton ArchiveScheduler instance."""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = ArchiveScheduler()
    return _scheduler_instance
