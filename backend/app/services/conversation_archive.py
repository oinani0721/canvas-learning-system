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

import asyncio
import logging

import structlog
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

logger = structlog.get_logger(__name__)


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
        self._initialized: bool = False

    async def _restore_archive_markers(self) -> None:
        """Restore archive markers from Graphiti on first use.

        Story 3-8 FIX M1: Prevents re-archiving conversations after restart
        by loading previously written archive_marker episodes from memory.
        """
        if self._initialized:
            return
        self._initialized = True
        try:
            from app.config import DEFAULT_GROUP_ID
            from app.services.memory_service import get_memory_service

            memory_svc = await get_memory_service()
            results = await memory_svc.search_memories(
                query="archive_marker",
                group_id=DEFAULT_GROUP_ID,
                max_results=500,
            )
            if not isinstance(results, list):
                return
            for item in results:
                if not isinstance(item, dict):
                    continue
                if item.get("episode_type") != "archive_marker":
                    continue
                meta = item.get("metadata", {})
                nid = meta.get("node_id", "")
                if not nid or nid in self._archive_log:
                    continue
                tier_str = meta.get("tier", "warm")
                try:
                    tier = ArchiveTier(tier_str)
                except ValueError:
                    tier = ArchiveTier.WARM
                self._archive_log[nid] = ArchiveStatus(
                    node_id=nid,
                    tier=tier,
                    message_count=meta.get("message_count", 0),
                    last_archived_at=meta.get("archived_at"),
                )
            if self._archive_log:
                logger.info(
                    f"[Story 3.8] Restored {len(self._archive_log)} archive markers from Graphiti"
                )
        except (
            RuntimeError,
            ConnectionError,
            asyncio.TimeoutError,
            ValueError,
            KeyError,
        ) as e:
            logger.warning(f"[Story 3.8] Failed to restore archive markers: {e}")

    async def check_and_archive(self, node_id: str) -> Optional[ArchiveStatus]:
        """
        Check if a node's conversation needs archiving and execute if so.

        Called after each conversation ends or on scheduled check.

        Args:
            node_id: The canvas node identifier.

        Returns:
            ArchiveStatus if archiving occurred, None otherwise.
        """
        # Story 3-8 FIX M1: Restore archive markers before first check
        await self._restore_archive_markers()

        try:
            messages = await self._get_node_messages(node_id)
            if not messages:
                return None

            # Check capacity trigger first (more immediate)
            estimated_tokens = self._estimate_tokens(messages)
            oldest_msg_time = self._get_oldest_message_time(messages)

            now = datetime.now(timezone.utc)
            current_tier = self._determine_current_tier(
                oldest_msg_time, estimated_tokens, now
            )

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
            except (
                RuntimeError,
                ConnectionError,
                asyncio.TimeoutError,
                ValueError,
            ) as e:
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

            # Story 5.8 Task 7: Store extraction results for human review
            if has_structured:
                await self._store_extraction_records(
                    node_id=node_id,
                    result=result,
                )

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
                logger.warning(f"[Story 3.8] Distillation for Cold archive failed: {e}")
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

    async def _store_extraction_records(
        self,
        node_id: str,
        result: Any,
    ) -> None:
        """Store distillation results as ExtractionRecords for human review.

        Creates one ExtractionRecord per tip, error, and key QA highlight
        extracted by the conversation distiller. Each record links back to
        the source text for side-by-side comparison.

        [Source: Story 5.8 Task 7.1]

        Args:
            node_id: Canvas node identifier.
            result: DistillationResult from conversation_distiller.
        """
        try:
            from app.services.extraction_validator import get_extraction_validator

            validator = get_extraction_validator()
            session_id = f"archive_{node_id}"

            # Story 3-8 FIX M3: Safe attribute access — DistillationResult models
            # (ExtractedTip, ExtractedError, ExtractedQA) do not have an 'evidence'
            # field. Use known model fields directly instead of fragile getattr.
            for tip in result.tips or []:
                content = tip.content if hasattr(tip, "content") else str(tip)
                title = tip.title if hasattr(tip, "title") else ""
                await validator.store_record(
                    source_session_id=session_id,
                    source_node_id=node_id,
                    original_text=title,
                    extracted_content=content,
                    extraction_type="tip",
                )

            for error in result.errors or []:
                description = (
                    error.description if hasattr(error, "description") else str(error)
                )
                error_type = error.error_type if hasattr(error, "error_type") else None
                await validator.store_record(
                    source_session_id=session_id,
                    source_node_id=node_id,
                    original_text="",
                    extracted_content=description,
                    extraction_type="error",
                    extraction_subtype=error_type,
                )

            for qa in result.qa_highlights or []:
                question = qa.question if hasattr(qa, "question") else ""
                answer = qa.answer if hasattr(qa, "answer") else ""
                content = f"Q: {question}\nA: {answer}" if question else str(qa)
                await validator.store_record(
                    source_session_id=session_id,
                    source_node_id=node_id,
                    original_text=question,
                    extracted_content=content,
                    extraction_type="key_qa",
                )

            total = (
                len(result.tips or [])
                + len(result.errors or [])
                + len(result.qa_highlights or [])
            )
            if total > 0:
                logger.info(
                    f"[Story 5.8] Stored {total} extraction records for node {node_id}"
                )

        except (RuntimeError, ConnectionError, AttributeError, ValueError) as e:
            logger.warning(
                f"[Story 5.8] Failed to store extraction records for {node_id}: {e}"
            )

    async def _get_node_messages(self, node_id: str) -> List[Dict[str, Any]]:
        """
        Get conversation messages for a node from the memory service.

        Searches memory episodes by node_id and filters for conversation-type
        episodes (those with role field or conversation episode_type).

        Args:
            node_id: The canvas node identifier.

        Returns:
            List of message dicts with role, content, timestamp.
        """
        from app.config import DEFAULT_GROUP_ID
        from app.services.memory_service import get_memory_service

        memory_svc = await get_memory_service()

        # Search for episodes related to this node
        results = await memory_svc.search_memories(
            query=node_id,
            group_id=DEFAULT_GROUP_ID,
            max_results=200,
        )

        messages: List[Dict[str, Any]] = []
        if isinstance(results, list):
            for item in results:
                if not isinstance(item, dict):
                    continue
                # Filter for conversation-type episodes by checking node_id match
                ep_node_id = item.get("node_id") or item.get("metadata", {}).get(
                    "node_id", ""
                )
                if ep_node_id != node_id:
                    continue
                # Skip archive markers to avoid re-processing
                if item.get("episode_type") == "archive_marker":
                    continue
                messages.append(
                    {
                        "role": item.get("role", "user"),
                        "content": item.get("content", item.get("fact", "")),
                        "timestamp": item.get("timestamp", item.get("created_at", "")),
                    }
                )

        return messages

    async def _mark_messages_archived(
        self,
        node_id: str,
        messages: List[Dict[str, Any]],
        tier: str = "warm",
    ) -> None:
        """
        Mark messages as archived (non-destructive).

        Records an archive marker in memory with message timestamps
        so that subsequent check_and_archive calls can detect already-archived
        conversations and avoid re-processing.

        Args:
            node_id: The canvas node identifier.
            messages: The messages to mark.
            tier: Archive tier label.
        """
        try:
            from app.config import DEFAULT_GROUP_ID
            from app.services.memory_service import get_memory_service

            memory_svc = await get_memory_service()

            # Collect message timestamps to identify the archived range
            msg_timestamps = [
                msg.get("timestamp", msg.get("created_at", ""))
                for msg in messages
                if msg.get("timestamp") or msg.get("created_at")
            ]
            newest_ts = max(msg_timestamps) if msg_timestamps else ""
            oldest_ts = min(msg_timestamps) if msg_timestamps else ""

            await memory_svc.record_knowledge_entity(
                event_type="archive_marker",
                content=(
                    f"Archived {len(messages)} messages for node {node_id} to {tier} tier"
                ),
                metadata={
                    "node_id": node_id,
                    "tier": tier,
                    "message_count": len(messages),
                    "archived_at": datetime.now(timezone.utc).isoformat(),
                    "oldest_message_ts": oldest_ts,
                    "newest_message_ts": newest_ts,
                },
                group_id=DEFAULT_GROUP_ID,
            )

            # Update internal archive log to prevent re-archiving
            self._archive_log[node_id] = ArchiveStatus(
                node_id=node_id,
                tier=ArchiveTier(tier),
                message_count=len(messages),
                estimated_tokens=self._estimate_tokens(messages),
                last_archived_at=datetime.now(timezone.utc).isoformat(),
            )

        except (RuntimeError, ConnectionError, asyncio.TimeoutError, ValueError) as e:
            logger.warning(f"[Story 3.8] Failed to mark messages archived: {e}")

    def _estimate_tokens(self, messages: List[Dict[str, Any]]) -> int:
        """
        Estimate token count for a list of messages.

        Story 3-8 FIX M2: Uses tiktoken for accurate estimation (especially
        for Chinese text where 4chars/token is very inaccurate — Chinese
        characters often consume 2-3 tokens each).

        Falls back to a conservative 2 chars/token heuristic if tiktoken
        is unavailable.

        Args:
            messages: The messages to estimate.

        Returns:
            Estimated token count.
        """
        full_text = " ".join(msg.get("content", "") for msg in messages)
        if not full_text:
            return 0
        try:
            import tiktoken

            enc = tiktoken.get_encoding("cl100k_base")
            return len(enc.encode(full_text))
        except Exception:
            # Fallback: conservative estimate (2 chars/token for mixed CJK+Latin)
            return len(full_text) // 2

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
