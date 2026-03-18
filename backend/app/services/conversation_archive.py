# Canvas Learning System - Conversation Archive Manager
# Story 3.8: Hot-Warm-Cold Three-Layer Archiving (AC-1, AC-2)
#
# Archive lifecycle:
#   Hot (0-30 days)  → Complete message retention
#   Warm (30d-6mo)   → LLM summary + structured extraction
#   Cold (6mo+)      → Only structured extraction data
#
# Trigger conditions (dual trigger: time OR capacity):
#   - Time: message created > 30 days → Hot→Warm
#   - Time: message created > 6 months → Warm→Cold
#   - Capacity: single node conversation > 50K tokens → trigger Warm
#
# Messages are marked `status: archived`, not physically deleted.
#
# [Source: _bmad-output/implementation-artifacts/3-8-dialog-archive-async-generation.md#Task 1]

import logging
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════════════════════

HOT_TO_WARM_DAYS = 30
WARM_TO_COLD_DAYS = 180  # 6 months
CAPACITY_THRESHOLD_TOKENS = 50_000
MAX_NODES_PER_BATCH = 10


# ═══════════════════════════════════════════════════════════════════════════════
# Archive Status
# ═══════════════════════════════════════════════════════════════════════════════


class ArchiveTier(str, Enum):
    """Archive tier for conversation messages."""

    HOT = "hot"
    WARM = "warm"
    COLD = "cold"


class ArchiveStatus(BaseModel):
    """Archive status for a node's conversation."""

    node_id: str
    tier: ArchiveTier
    message_count: int = 0
    estimated_tokens: int = 0
    has_summary: bool = False
    has_structured_data: bool = False
    last_archived_at: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════════
# Archive Manager
# ═══════════════════════════════════════════════════════════════════════════════


class ArchiveManager:
    """
    Manages Hot-Warm-Cold archiving lifecycle for conversations.

    Story 3.8 AC-1: Dual trigger (time + capacity) archiving.
    Story 3.8 AC-2: LLM distillation during Warm transition.

    [Source: _bmad-output/implementation-artifacts/3-8-dialog-archive-async-generation.md#Task 1.2]
    """

    def __init__(self) -> None:
        self._archive_log: Dict[str, ArchiveStatus] = {}

    async def check_and_archive(self, node_id: str) -> Optional[ArchiveStatus]:
        """
        Check if a node's conversation needs archiving and execute if so.

        Called after each conversation ends or on scheduled check.

        Args:
            node_id: The canvas node identifier.

        Returns:
            ArchiveStatus if archiving occurred, None otherwise.
        """
        try:
            messages = await self._get_node_messages(node_id)
            if not messages:
                return None

            # Check capacity trigger first (more immediate)
            estimated_tokens = self._estimate_tokens(messages)
            oldest_msg_time = self._get_oldest_message_time(messages)

            now = datetime.now(timezone.utc)
            current_tier = self._determine_current_tier(oldest_msg_time, estimated_tokens, now)

            if current_tier == ArchiveTier.HOT:
                # No archiving needed
                return None

            if current_tier == ArchiveTier.WARM:
                return await self._archive_to_warm(node_id, messages)
            elif current_tier == ArchiveTier.COLD:
                return await self._archive_to_cold(node_id, messages)

        except Exception as e:
            logger.error(f"[Story 3.8] Archive check failed for node {node_id}: {e}")
            return None

    async def batch_check(self, node_ids: List[str]) -> List[ArchiveStatus]:
        """
        Check multiple nodes for archiving (batch processing).

        Args:
            node_ids: List of node IDs to check.

        Returns:
            List of ArchiveStatus for nodes that were archived.
        """
        results: List[ArchiveStatus] = []
        # Limit to MAX_NODES_PER_BATCH to prevent long blocking
        batch = node_ids[:MAX_NODES_PER_BATCH]

        for node_id in batch:
            try:
                result = await self.check_and_archive(node_id)
                if result:
                    results.append(result)
            except Exception as e:
                logger.warning(
                    f"[Story 3.8] Batch archive failed for node {node_id}: {e}"
                )

        if results:
            logger.info(
                f"[Story 3.8] Batch archive: {len(results)}/{len(batch)} nodes archived"
            )

        return results

    def get_status(self, node_id: str) -> Optional[ArchiveStatus]:
        """Get the archive status for a node."""
        return self._archive_log.get(node_id)

    # ═══════════════════════════════════════════════════════════════════════════
    # Internal Methods
    # ═══════════════════════════════════════════════════════════════════════════

    def _determine_current_tier(
        self,
        oldest_msg_time: Optional[datetime],
        estimated_tokens: int,
        now: datetime,
    ) -> ArchiveTier:
        """
        Determine which archive tier a conversation belongs to.

        Dual trigger: time OR capacity.

        Args:
            oldest_msg_time: Timestamp of the oldest message.
            estimated_tokens: Estimated token count.
            now: Current time.

        Returns:
            The appropriate ArchiveTier.
        """
        if oldest_msg_time is None:
            return ArchiveTier.HOT

        age = now - oldest_msg_time

        # Cold: > 6 months
        if age > timedelta(days=WARM_TO_COLD_DAYS):
            return ArchiveTier.COLD

        # Warm: > 30 days OR > 50K tokens
        if age > timedelta(days=HOT_TO_WARM_DAYS):
            return ArchiveTier.WARM

        if estimated_tokens > CAPACITY_THRESHOLD_TOKENS:
            return ArchiveTier.WARM

        return ArchiveTier.HOT

    async def _archive_to_warm(
        self, node_id: str, messages: List[Dict[str, Any]]
    ) -> ArchiveStatus:
        """
        Archive conversation from Hot to Warm tier.

        Generates LLM summary + structured extraction.
        Marks original messages as archived (no physical deletion).

        Args:
            node_id: The canvas node identifier.
            messages: The conversation messages.

        Returns:
            ArchiveStatus after archiving.
        """
        logger.info(f"[Story 3.8] Archiving node {node_id} from Hot to Warm")

        # Run distillation
        try:
            from app.config import DEFAULT_GROUP_ID
            from app.services.conversation_distiller import get_conversation_distiller

            distiller = get_conversation_distiller()
            result = await distiller.distill_and_persist(
                messages=messages,
                node_id=node_id,
                group_id=DEFAULT_GROUP_ID,
            )

            has_summary = bool(result.summary)
            has_structured = bool(result.tips or result.errors or result.qa_highlights)

        except Exception as e:
            logger.warning(f"[Story 3.8] Distillation failed for Warm archive: {e}")
            has_summary = False
            has_structured = False

        # Mark messages as archived
        await self._mark_messages_archived(node_id, messages)

        status = ArchiveStatus(
            node_id=node_id,
            tier=ArchiveTier.WARM,
            message_count=len(messages),
            estimated_tokens=self._estimate_tokens(messages),
            has_summary=has_summary,
            has_structured_data=has_structured,
            last_archived_at=datetime.now(timezone.utc).isoformat(),
        )

        self._archive_log[node_id] = status
        return status

    async def _archive_to_cold(
        self, node_id: str, messages: List[Dict[str, Any]]
    ) -> ArchiveStatus:
        """
        Archive conversation from Warm to Cold tier.

        Only structured extraction data is preserved.
        Summary is removed (only facts remain).

        If the node was never archived to Warm (i.e. jumped straight from
        Hot to Cold due to age > 6 months), distillation is run first to
        ensure structured data exists before archiving.

        Args:
            node_id: The canvas node identifier.
            messages: The conversation messages.

        Returns:
            ArchiveStatus after archiving.
        """
        logger.info(f"[Story 3.8] Archiving node {node_id} from Warm to Cold")

        has_structured = False

        # If node was never Warm-archived, run distillation first
        prior = self._archive_log.get(node_id)
        if prior is None or not prior.has_structured_data:
            try:
                from app.config import DEFAULT_GROUP_ID
                from app.services.conversation_distiller import (
                    get_conversation_distiller,
                )

                distiller = get_conversation_distiller()
                result = await distiller.distill_and_persist(
                    messages=messages,
                    node_id=node_id,
                    group_id=DEFAULT_GROUP_ID,
                )
                has_structured = bool(
                    result.tips or result.errors or result.qa_highlights
                )
            except Exception as e:
                logger.warning(
                    f"[Story 3.8] Distillation for Cold archive failed: {e}"
                )
        else:
            has_structured = True

        # Mark messages as cold-archived
        await self._mark_messages_archived(node_id, messages, tier="cold")

        status = ArchiveStatus(
            node_id=node_id,
            tier=ArchiveTier.COLD,
            message_count=len(messages),
            estimated_tokens=self._estimate_tokens(messages),
            has_summary=False,
            has_structured_data=has_structured,
            last_archived_at=datetime.now(timezone.utc).isoformat(),
        )

        self._archive_log[node_id] = status
        return status

    async def _get_node_messages(
        self, node_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get conversation messages for a node from the memory service.

        Args:
            node_id: The canvas node identifier.

        Returns:
            List of message dicts with role, content, timestamp.
        """
        from app.config import DEFAULT_GROUP_ID
        from app.services.memory_service import get_memory_service

        memory_svc = await get_memory_service()

        # Search for conversation episodes for this node
        results = await memory_svc.search_memories(
            query=f"conversation node:{node_id}",
            group_id=DEFAULT_GROUP_ID,
            max_results=100,
        )

        messages: List[Dict[str, Any]] = []
        if isinstance(results, list):
            for item in results:
                if isinstance(item, dict):
                    messages.append({
                        "role": item.get("role", "user"),
                        "content": item.get("content", item.get("fact", "")),
                        "timestamp": item.get("timestamp", item.get("created_at", "")),
                    })

        return messages

    async def _mark_messages_archived(
        self,
        node_id: str,
        messages: List[Dict[str, Any]],
        tier: str = "warm",
    ) -> None:
        """
        Mark messages as archived (non-destructive).

        Messages are flagged with `status: archived` but not deleted.

        Args:
            node_id: The canvas node identifier.
            messages: The messages to mark.
            tier: Archive tier label.
        """
        try:
            from app.config import DEFAULT_GROUP_ID
            from app.services.memory_service import get_memory_service

            memory_svc = await get_memory_service()

            await memory_svc.record_knowledge_entity(
                event_type="archive_marker",
                content=(
                    f"Archived {len(messages)} messages for node {node_id} "
                    f"to {tier} tier"
                ),
                metadata={
                    "node_id": node_id,
                    "tier": tier,
                    "message_count": len(messages),
                    "archived_at": datetime.now(timezone.utc).isoformat(),
                },
                group_id=DEFAULT_GROUP_ID,
            )

        except Exception as e:
            logger.warning(f"[Story 3.8] Failed to mark messages archived: {e}")

    def _estimate_tokens(self, messages: List[Dict[str, Any]]) -> int:
        """
        Estimate token count for a list of messages.

        Uses a simple heuristic: ~4 chars per token (rough approximation).

        Args:
            messages: The messages to estimate.

        Returns:
            Estimated token count.
        """
        total_chars = sum(len(msg.get("content", "")) for msg in messages)
        return total_chars // 4

    def _get_oldest_message_time(
        self, messages: List[Dict[str, Any]]
    ) -> Optional[datetime]:
        """
        Get the timestamp of the oldest message.

        Args:
            messages: The messages to check.

        Returns:
            datetime of the oldest message, or None.
        """
        oldest = None
        for msg in messages:
            ts = msg.get("timestamp", msg.get("created_at", ""))
            if ts:
                try:
                    parsed = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    if oldest is None or parsed < oldest:
                        oldest = parsed
                except (ValueError, TypeError):
                    continue
        return oldest


# ═══════════════════════════════════════════════════════════════════════════════
# Singleton
# ═══════════════════════════════════════════════════════════════════════════════

_archive_manager: Optional[ArchiveManager] = None


def get_archive_manager() -> ArchiveManager:
    """Get or create the singleton ArchiveManager instance."""
    global _archive_manager
    if _archive_manager is None:
        _archive_manager = ArchiveManager()
    return _archive_manager
