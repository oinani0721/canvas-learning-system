const fs = require('fs');
const path = 'C:/Users/Heishing/Desktop/canvas/canvas-learning-system/backend/tests/unit/test_event_bus.py';
const content = `"""
Unit tests for Story 5.7: EventBus Three-System Connect

Tests cover:
  - subscribe / unsubscribe / publish basics
  - Tier 1 await execution + failure raises
  - Tier 2 retry logic (1/2/3 failures + outbox)
  - Tier 3 fire-and-forget + failure doesn't block
  - Idempotency (duplicate event_id not reprocessed)
  - LRU eviction in dedup set
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, patch

from app.models.canvas_events import (
    EventTier,
    LearningEvent,
    LearningEventType,
)
from app.services.event_bus import (
    EventBus,
    LRUDedup,
    TIER2_MAX_RETRIES,
)


class TestLRUDedup:
    def test_add_and_contains(self):
        dedup = LRUDedup(capacity=10)
        dedup.add("event_1")
        assert dedup.contains("event_1") is True
        assert dedup.contains("event_2") is False

    def test_capacity_eviction(self):
        dedup = LRUDedup(capacity=3)
        dedup.add("a")
        dedup.add("b")
        dedup.add("c")
        dedup.add("d")
        assert dedup.contains("a") is False
        assert dedup.contains("b") is True
        assert dedup.contains("d") is True
        assert dedup.size == 3

    def test_lru_access_refreshes(self):
        dedup = LRUDedup(capacity=3)
        dedup.add("a")
        dedup.add("b")
        dedup.add("c")
        dedup.contains("a")
        dedup.add("d")
        assert dedup.contains("a") is True
        assert dedup.contains("b") is False


def _make_event(event_type=LearningEventType.SCORE_SUBMITTED, event_id="", node_id="test_node"):
    kwargs = {
        "event_type": event_type,
        "payload": {"node_id": node_id, "session_id": "test_session"},
        "source": "test",
    }
    if event_id:
        kwargs["event_id"] = event_id
    return LearningEvent(**kwargs)


class TestEventBusBasics:
    @pytest.mark.asyncio
    async def test_subscribe_and_publish(self):
        bus = EventBus()
        handler = AsyncMock()
        bus.subscribe(LearningEventType.SCORE_SUBMITTED, handler)
        event = _make_event()
        await bus.publish(event)
        handler.assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_unsubscribe(self):
        bus = EventBus()
        handler = AsyncMock()
        bus.subscribe(LearningEventType.SCORE_SUBMITTED, handler)
        bus.unsubscribe(LearningEventType.SCORE_SUBMITTED, handler)
        await bus.publish(_make_event())
        handler.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_handlers(self):
        bus = EventBus()
        await bus.publish(_make_event())

    @pytest.mark.asyncio
    async def test_multiple_handlers(self):
        bus = EventBus()
        h1 = AsyncMock()
        h2 = AsyncMock()
        bus.subscribe(LearningEventType.SCORE_SUBMITTED, h1)
        bus.subscribe(LearningEventType.SCORE_SUBMITTED, h2)
        event = _make_event()
        await bus.publish(event)
        h1.assert_called_once()
        h2.assert_called_once()


class TestTier1Critical:
    @pytest.mark.asyncio
    async def test_tier1_await_execution(self):
        bus = EventBus()
        call_order = []

        async def handler1(event):
            call_order.append("h1_start")
            await asyncio.sleep(0.01)
            call_order.append("h1_end")

        bus.subscribe(LearningEventType.SCORE_SUBMITTED, handler1)
        await bus.publish(_make_event())
        assert call_order == ["h1_start", "h1_end"]

    @pytest.mark.asyncio
    async def test_tier1_failure_propagates(self):
        bus = EventBus()

        async def failing_handler(event):
            raise ValueError("Tier 1 failure")

        bus.subscribe(LearningEventType.SCORE_SUBMITTED, failing_handler)
        with pytest.raises(ValueError, match="Tier 1 failure"):
            await bus.publish(_make_event())


class TestTier2Important:
    @pytest.mark.asyncio
    async def test_tier2_success(self):
        bus = EventBus()
        handler = AsyncMock()
        bus.subscribe(LearningEventType.BKT_UPDATED, handler)
        await bus.publish(_make_event(LearningEventType.BKT_UPDATED))
        await asyncio.sleep(0.1)
        handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_tier2_retry_then_success(self):
        bus = EventBus()
        call_count = 0

        async def flaky_handler(event):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("Temporary failure")

        bus.subscribe(LearningEventType.BKT_UPDATED, flaky_handler)
        with patch("app.services.event_bus.asyncio.sleep", new_callable=AsyncMock):
            await bus.publish(_make_event(LearningEventType.BKT_UPDATED))
            await asyncio.sleep(0.1)
        assert call_count >= 2

    @pytest.mark.asyncio
    async def test_tier2_all_retries_exhausted_writes_outbox(self):
        bus = EventBus()

        async def always_fail(event):
            raise ConnectionError("Persistent failure")

        bus.subscribe(LearningEventType.BKT_UPDATED, always_fail)
        with patch("app.services.event_bus.asyncio.sleep", new_callable=AsyncMock):
            await bus.publish(_make_event(LearningEventType.BKT_UPDATED))
            await asyncio.sleep(0.2)
        assert bus._stats["outbox_written"] >= 1


class TestTier3BestEffort:
    @pytest.mark.asyncio
    async def test_tier3_success(self):
        bus = EventBus()
        handler = AsyncMock()
        bus.subscribe(LearningEventType.UI_MASTERY_PUSH, handler)
        await bus.publish(_make_event(LearningEventType.UI_MASTERY_PUSH))
        await asyncio.sleep(0.1)
        handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_tier3_failure_doesnt_propagate(self):
        bus = EventBus()

        async def failing_handler(event):
            raise RuntimeError("Tier 3 failure")

        bus.subscribe(LearningEventType.UI_MASTERY_PUSH, failing_handler)
        await bus.publish(_make_event(LearningEventType.UI_MASTERY_PUSH))
        await asyncio.sleep(0.1)
        assert bus._stats["handled_failed"] >= 1


class TestIdempotency:
    @pytest.mark.asyncio
    async def test_duplicate_event_not_reprocessed(self):
        bus = EventBus()
        handler = AsyncMock()
        bus.subscribe(LearningEventType.SCORE_SUBMITTED, handler)
        event = _make_event(event_id="dup_123")
        await bus.publish(event)
        await bus.publish(event)
        handler.assert_called_once()
        assert bus._stats["deduplicated"] >= 1

    @pytest.mark.asyncio
    async def test_different_event_ids_both_processed(self):
        bus = EventBus()
        handler = AsyncMock()
        bus.subscribe(LearningEventType.SCORE_SUBMITTED, handler)
        await bus.publish(_make_event(event_id="event_1"))
        await bus.publish(_make_event(event_id="event_2"))
        assert handler.call_count == 2


class TestEventTierMapping:
    def test_score_submitted_is_tier1(self):
        event = _make_event(LearningEventType.SCORE_SUBMITTED)
        assert event.tier == EventTier.TIER_1_CRITICAL

    def test_bkt_updated_is_tier2(self):
        event = _make_event(LearningEventType.BKT_UPDATED)
        assert event.tier == EventTier.TIER_2_IMPORTANT

    def test_fsrs_updated_is_tier2(self):
        event = _make_event(LearningEventType.FSRS_UPDATED)
        assert event.tier == EventTier.TIER_2_IMPORTANT

    def test_mastery_changed_is_tier2(self):
        event = _make_event(LearningEventType.MASTERY_CHANGED)
        assert event.tier == EventTier.TIER_2_IMPORTANT

    def test_calibration_recorded_is_tier2(self):
        event = _make_event(LearningEventType.CALIBRATION_RECORDED)
        assert event.tier == EventTier.TIER_2_IMPORTANT

    def test_rag_weight_adjust_is_tier3(self):
        event = _make_event(LearningEventType.RAG_WEIGHT_ADJUST)
        assert event.tier == EventTier.TIER_3_BEST_EFFORT

    def test_ui_mastery_push_is_tier3(self):
        event = _make_event(LearningEventType.UI_MASTERY_PUSH)
        assert event.tier == EventTier.TIER_3_BEST_EFFORT


class TestEventBusStats:
    @pytest.mark.asyncio
    async def test_stats_tracking(self):
        bus = EventBus()
        handler = AsyncMock()
        bus.subscribe(LearningEventType.SCORE_SUBMITTED, handler)
        await bus.publish(_make_event())
        stats = bus.get_stats()
        assert stats["published"] >= 1
        assert stats["handled_success"] >= 1

    def test_circuit_breaker_registration(self):
        bus = EventBus()
        cb = bus.register_circuit_breaker("graphiti")
        assert cb is not None
        assert bus.get_circuit_breaker_status()["graphiti"] == "closed"


class TestLearningEvent:
    def test_event_has_uuid(self):
        event = _make_event()
        assert event.event_id is not None
        assert len(event.event_id) > 0

    def test_event_has_timestamp(self):
        event = _make_event()
        assert event.timestamp is not None

    def test_event_payload_access(self):
        event = _make_event(node_id="my_node")
        assert event.node_id == "my_node"
        assert event.session_id == "test_session"

    def test_tier_not_overridable(self):
        event = _make_event(LearningEventType.SCORE_SUBMITTED)
        assert event.tier == EventTier.TIER_1_CRITICAL
`;
fs.writeFileSync(path, content, 'utf-8');
console.log('Written successfully');
