"""
EventBus - Async Event Distribution Engine with Three-Tier Priority

Story 5.7: Connects FSRS, Graphiti, and RAG subsystems via event-driven architecture.

Architecture (~100 lines core):
  Tier 1 (P0) CRITICAL:    await synchronous — mastery computations
  Tier 2 (P1) IMPORTANT:   fire + retry (2s→4s→8s, max 3) + JSONL outbox — graph writes
  Tier 3 (P2) BEST_EFFORT: fire-and-forget — UI pushes, RAG adjustments

Features:
  - subscribe/unsubscribe/publish core API
  - CircuitBreaker integration per subsystem
  - JSONL outbox for failed Tier 2 events
  - Idempotent event deduplication (LRU set, capacity 10000)
  - Structured logging with handler-level timing

[Source: _bmad-output/implementation-artifacts/5-7-eventbus-triconnect.md]
[Source: _bmad-output/planning-artifacts/architecture.md#Cross-Cutting Concerns #10]
"""

import asyncio
import json
import logging
import time

import structlog
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Coroutine, Dict, List, Optional

from app.models.canvas_events import (
    EventTier,
    LearningEvent,
    LearningEventType,
)
from app.core.decision_tracker import log_decision
from app.utils.circuit_breaker import CircuitBreaker

logger = structlog.get_logger(__name__)

# Type alias for async event handlers
EventHandler = Callable[[LearningEvent], Coroutine[Any, Any, None]]

# JSONL outbox path
_BACKEND_DIR = Path(__file__).parent.parent.parent  # backend/
OUTBOX_DIR = _BACKEND_DIR / "data" / "outbox"
OUTBOX_FILE = OUTBOX_DIR / "events.jsonl"

# Tier 2 retry configuration
TIER2_MAX_RETRIES = 3
TIER2_BASE_DELAY_S = 2.0  # Exponential backoff: 2s → 4s → 8s

# Idempotency dedup set capacity
DEDUP_CAPACITY = 10000

# CircuitBreaker defaults for EventBus
CB_FAILURE_THRESHOLD = 5
CB_RECOVERY_TIMEOUT_S = 30.0


class LRUDedup:
    """LRU-based event ID deduplication set with bounded capacity.

    When capacity is reached, oldest entries are evicted to make room.
    """

    def __init__(self, capacity: int = DEDUP_CAPACITY):
        self._capacity = capacity
        self._seen: OrderedDict[str, bool] = OrderedDict()

    def contains(self, event_id: str) -> bool:
        """Check if event_id has been seen (and mark as recently used)."""
        if event_id in self._seen:
            self._seen.move_to_end(event_id)
            return True
        return False

    def add(self, event_id: str) -> None:
        """Mark event_id as processed."""
        if event_id in self._seen:
            self._seen.move_to_end(event_id)
            return
        if len(self._seen) >= self._capacity:
            self._seen.popitem(last=False)  # Evict oldest
        self._seen[event_id] = True

    @property
    def size(self) -> int:
        return len(self._seen)


class EventBus:
    """Async EventBus with three-tier priority and circuit breaker support.

    Global singleton pattern — use get_event_bus() for FastAPI DI.
    """

    def __init__(self):
        self._handlers: Dict[LearningEventType, List[EventHandler]] = {}
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._dedup = LRUDedup(DEDUP_CAPACITY)
        self._stats: Dict[str, int] = {
            "published": 0,
            "handled_success": 0,
            "handled_failed": 0,
            "retried": 0,
            "outbox_written": 0,
            "deduplicated": 0,
        }
        # Ensure outbox directory exists
        OUTBOX_DIR.mkdir(parents=True, exist_ok=True)

    # ═══════════════════════════════════════════════════════════════════════
    # Core API: subscribe / unsubscribe / publish
    # ═══════════════════════════════════════════════════════════════════════

    def subscribe(
        self,
        event_type: LearningEventType,
        handler: EventHandler,
        subsystem: Optional[str] = None,
    ) -> None:
        """Register an async handler for an event type.

        Args:
            event_type: The event type to listen for
            handler: Async callable(LearningEvent) -> None
            subsystem: Optional subsystem name for CircuitBreaker tracking
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

        if subsystem and subsystem not in self._circuit_breakers:
            self._circuit_breakers[subsystem] = CircuitBreaker(
                name=subsystem,
                failure_threshold=CB_FAILURE_THRESHOLD,
                recovery_timeout=CB_RECOVERY_TIMEOUT_S,
            )

        logger.info(
            f"EventBus: subscribed {handler.__name__} to {event_type.value}"
            + (f" (subsystem={subsystem})" if subsystem else "")
        )

    def unsubscribe(
        self,
        event_type: LearningEventType,
        handler: EventHandler,
    ) -> None:
        """Remove a handler from an event type."""
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
                logger.info(
                    f"EventBus: unsubscribed {handler.__name__} from {event_type.value}"
                )
            except ValueError:
                logger.warning(
                    f"EventBus: handler {handler.__name__} not found for {event_type.value}"
                )

    async def publish(self, event: LearningEvent) -> None:
        """Publish an event to all registered handlers.

        Dispatches based on event tier:
          Tier 1: await all handlers sequentially (failure raises)
          Tier 2: asyncio.create_task with retry + outbox
          Tier 3: asyncio.create_task fire-and-forget

        Idempotency: duplicate event_ids are silently skipped.
        """
        # Idempotency check
        if self._dedup.contains(event.event_id):
            self._stats["deduplicated"] += 1
            logger.debug(f"EventBus: deduplicated event {event.event_id}")
            return

        self._dedup.add(event.event_id)
        self._stats["published"] += 1

        handlers = self._handlers.get(event.event_type, [])
        if not handlers:
            logger.debug(f"EventBus: no handlers for {event.event_type.value}")
            return

        logger.info(
            f"EventBus: publishing {event.event_type.value} "
            f"(tier={event.tier.value}, handlers={len(handlers)}, "
            f"event_id={event.event_id[:8]}...)"
        )

        tier = event.tier

        log_decision(
            function="EventBus.publish",
            input_summary={"event_type": event.event_type.value, "tier": tier.value},
            output=f"dispatch_tier{tier.value}",
            reason=f"{len(handlers)} handlers, event_id={event.event_id[:8]}",
        )

        if tier == EventTier.TIER_1_CRITICAL:
            await self._dispatch_tier1(event, handlers)
        elif tier == EventTier.TIER_2_IMPORTANT:
            await self._dispatch_tier2(event, handlers)
        else:
            self._dispatch_tier3(event, handlers)

    # ═══════════════════════════════════════════════════════════════════════
    # Tier Dispatch Logic
    # ═══════════════════════════════════════════════════════════════════════

    async def _dispatch_tier1(
        self, event: LearningEvent, handlers: List[EventHandler]
    ) -> None:
        """Tier 1 CRITICAL: await each handler, failure raises exception."""
        for handler in handlers:
            start = time.monotonic()
            try:
                await handler(event)
                duration_ms = (time.monotonic() - start) * 1000
                self._stats["handled_success"] += 1
                logger.info(
                    f"EventBus[T1]: {handler.__name__} OK ({duration_ms:.1f}ms, event={event.event_type.value})"
                )
            except Exception as exc:
                duration_ms = (time.monotonic() - start) * 1000
                self._stats["handled_failed"] += 1
                logger.error(
                    f"EventBus[T1]: {handler.__name__} FAILED "
                    f"({duration_ms:.1f}ms, event={event.event_type.value}): {exc}"
                )
                raise  # Tier 1 propagates exceptions

    async def _dispatch_tier2(
        self, event: LearningEvent, handlers: List[EventHandler]
    ) -> None:
        """Tier 2 IMPORTANT: fire with retry + JSONL outbox on final failure."""
        for handler in handlers:
            asyncio.create_task(self._tier2_retry_wrapper(event, handler))

    async def _tier2_retry_wrapper(
        self, event: LearningEvent, handler: EventHandler
    ) -> None:
        """Retry wrapper for Tier 2: exponential backoff 2s→4s→8s, then outbox."""
        # Check circuit breaker for the handler's subsystem
        subsystem = self._find_handler_subsystem(handler)
        if subsystem:
            cb = self._circuit_breakers.get(subsystem)
            if cb and not cb.allow_request():
                logger.warning(
                    f"EventBus[T2]: CircuitBreaker OPEN for {subsystem}, writing to outbox: {event.event_type.value}"
                )
                self._write_outbox(event, handler.__name__, "circuit_open")
                return

        for attempt in range(1, TIER2_MAX_RETRIES + 1):
            start = time.monotonic()
            try:
                await handler(event)
                duration_ms = (time.monotonic() - start) * 1000
                self._stats["handled_success"] += 1
                logger.info(
                    f"EventBus[T2]: {handler.__name__} OK "
                    f"(attempt={attempt}, {duration_ms:.1f}ms, "
                    f"event={event.event_type.value})"
                )
                # Record success on circuit breaker
                if subsystem:
                    cb = self._circuit_breakers.get(subsystem)
                    if cb:
                        cb.record_success()
                return
            except Exception as exc:
                duration_ms = (time.monotonic() - start) * 1000
                self._stats["retried"] += 1
                delay = TIER2_BASE_DELAY_S * (2 ** (attempt - 1))
                logger.warning(
                    f"EventBus[T2]: {handler.__name__} FAILED "
                    f"(attempt={attempt}/{TIER2_MAX_RETRIES}, "
                    f"{duration_ms:.1f}ms, retry in {delay}s): {exc}"
                )
                # Record failure on circuit breaker
                if subsystem:
                    cb = self._circuit_breakers.get(subsystem)
                    if cb:
                        cb.record_failure()

                if attempt < TIER2_MAX_RETRIES:
                    await asyncio.sleep(delay)

        # All retries exhausted — write to JSONL outbox
        self._stats["handled_failed"] += 1
        self._write_outbox(event, handler.__name__, "retries_exhausted")

    def _dispatch_tier3(
        self, event: LearningEvent, handlers: List[EventHandler]
    ) -> None:
        """Tier 3 BEST_EFFORT: fire-and-forget, failures only logged."""
        for handler in handlers:
            asyncio.create_task(self._tier3_fire_wrapper(event, handler))

    async def _tier3_fire_wrapper(
        self, event: LearningEvent, handler: EventHandler
    ) -> None:
        """Fire-and-forget wrapper for Tier 3."""
        start = time.monotonic()
        try:
            await handler(event)
            duration_ms = (time.monotonic() - start) * 1000
            self._stats["handled_success"] += 1
            logger.debug(
                f"EventBus[T3]: {handler.__name__} OK ({duration_ms:.1f}ms, event={event.event_type.value})"
            )
        except Exception as exc:
            duration_ms = (time.monotonic() - start) * 1000
            self._stats["handled_failed"] += 1
            logger.warning(
                f"EventBus[T3]: {handler.__name__} FAILED ({duration_ms:.1f}ms, event={event.event_type.value}): {exc}"
            )
            # Tier 3: no retry, no outbox, just log

    # ═══════════════════════════════════════════════════════════════════════
    # JSONL Outbox
    # ═══════════════════════════════════════════════════════════════════════

    def _write_outbox(
        self, event: LearningEvent, handler_name: str, reason: str
    ) -> None:
        """Write failed event to JSONL outbox for later recovery."""
        outbox_entry = {
            "event_id": event.event_id,
            "event_type": event.event_type.value,
            "payload": event.payload,
            "source": event.source,
            "timestamp": event.timestamp.isoformat(),
            "tier": event.tier.value,
            "handler_name": handler_name,
            "failure_reason": reason,
            "outbox_ts": datetime.now(timezone.utc).isoformat(),
            "recovered": False,
        }
        try:
            with open(OUTBOX_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(outbox_entry, ensure_ascii=False) + "\n")
            self._stats["outbox_written"] += 1
            logger.info(
                f"EventBus: wrote to outbox: {event.event_type.value} handler={handler_name} reason={reason}"
            )
        except OSError as exc:
            logger.error(f"EventBus: failed to write outbox: {exc}")

    async def recover_outbox(self) -> int:
        """Read outbox and re-publish unrecovered events.

        Called on startup to retry events that failed during previous run.

        Returns:
            Number of events re-published
        """
        if not OUTBOX_FILE.exists():
            return 0

        recovered = 0
        remaining_lines = []

        try:
            with open(OUTBOX_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    entry = json.loads(line)
                    if entry.get("recovered"):
                        continue  # Already recovered

                    # Re-create the LearningEvent and publish
                    event = LearningEvent(
                        event_type=LearningEventType(entry["event_type"]),
                        payload=entry["payload"],
                        source=entry["source"],
                        event_id=entry["event_id"] + "_recovery",
                        timestamp=datetime.fromisoformat(entry["timestamp"]),
                    )
                    # Reset dedup so recovered events can be processed
                    await self.publish(event)
                    recovered += 1

                    entry["recovered"] = True
                    remaining_lines.append(json.dumps(entry, ensure_ascii=False))

            # Rewrite outbox with recovery status updated
            if remaining_lines:
                with open(OUTBOX_FILE, "w", encoding="utf-8") as f:
                    for rline in remaining_lines:
                        f.write(rline + "\n")

            logger.info(f"EventBus: recovered {recovered} events from outbox")

        except (OSError, json.JSONDecodeError, ValueError, KeyError) as exc:
            logger.error(f"EventBus: outbox recovery failed: {exc}")

        return recovered

    # ═══════════════════════════════════════════════════════════════════════
    # Helpers and Health
    # ═══════════════════════════════════════════════════════════════════════

    def _find_handler_subsystem(self, handler: EventHandler) -> Optional[str]:
        """Find the subsystem name associated with a handler (by name convention)."""
        name = handler.__name__.lower()
        for subsystem in self._circuit_breakers:
            if subsystem.lower() in name:
                return subsystem
        return None

    def get_circuit_breaker_status(self) -> Dict[str, str]:
        """Return circuit breaker states for all tracked subsystems."""
        return {name: cb.state.value for name, cb in self._circuit_breakers.items()}

    def get_stats(self) -> Dict[str, Any]:
        """Return event processing statistics."""
        return {
            **self._stats,
            "dedup_set_size": self._dedup.size,
            "registered_event_types": len(self._handlers),
            "circuit_breakers": self.get_circuit_breaker_status(),
        }

    def get_circuit_breaker(self, subsystem: str) -> Optional[CircuitBreaker]:
        """Get the CircuitBreaker instance for a subsystem."""
        return self._circuit_breakers.get(subsystem)

    def register_circuit_breaker(self, subsystem: str) -> CircuitBreaker:
        """Register a CircuitBreaker for a subsystem (if not already present)."""
        if subsystem not in self._circuit_breakers:
            self._circuit_breakers[subsystem] = CircuitBreaker(
                name=subsystem,
                failure_threshold=CB_FAILURE_THRESHOLD,
                recovery_timeout=CB_RECOVERY_TIMEOUT_S,
            )
        return self._circuit_breakers[subsystem]


# ═══════════════════════════════════════════════════════════════════════════════
# Global Singleton + FastAPI DI
# ═══════════════════════════════════════════════════════════════════════════════

_event_bus_instance: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get or create the global EventBus singleton.

    Use as FastAPI dependency: Depends(get_event_bus)
    """
    global _event_bus_instance
    if _event_bus_instance is None:
        _event_bus_instance = EventBus()
        logger.info("EventBus: global singleton created")
    return _event_bus_instance


def reset_event_bus() -> None:
    """Reset the global EventBus (for testing only)."""
    global _event_bus_instance
    _event_bus_instance = None
