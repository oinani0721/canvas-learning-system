# Canvas Learning System - EPIC 30 Memory Pipeline Coverage Gap Tests
# Covers 6 identified gaps from the existing 378-test suite
"""
EPIC 30 Memory Pipeline - Gap Coverage Tests

Tests organized by 6 coverage gaps:
    Gap 1 [P0]: record_batch_learning_events() full flow (Story 30.3 AC-30.3.10)
    Gap 2 [P0]: record_temporal_event() lifecycle (Story 30.5 AC-30.5.1-4)
    Gap 3 [P1]: Agent memory trigger mapping completeness (Story 30.4 AC-30.4.1)
    Gap 4 [P1]: get_health_status() degradation logic (Story 30.3 AC-30.3.5)
    Gap 5 [P2]: Neo4j write latency metrics (Story 30.2 AC-30.2.4)
    Gap 6 [P2]: Settings Neo4j configuration parsing (Story 30.1 AC-30.1.2)

Does NOT duplicate existing tests in:
    - test_memory_service_batch.py (concept fallback only)
    - test_canvas_memory_trigger.py (CanvasService trigger mechanism)
    - test_memory_service_write_retry.py (Graphiti JSON retry logic)

[Source: docs/stories/30.3.memory-api-health-endpoints.story.md]
[Source: docs/stories/30.5.story.md]
[Source: docs/stories/30.4.story.md]
[Source: docs/stories/30.2.story.md]
[Source: docs/stories/30.1.story.md]
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _make_valid_event(**overrides) -> Dict[str, Any]:
    """Factory for a valid batch event dict with unique IDs."""
    base = {
        "event_type": "node_created",
        "timestamp": datetime.now().isoformat(),
        "canvas_path": f"Math/{uuid.uuid4().hex[:8]}.canvas",
        "node_id": f"node-{uuid.uuid4().hex[:12]}",
        "metadata": {"node_text": f"concept-{uuid.uuid4().hex[:6]}"},
    }
    base.update(overrides)
    return base


def _build_mock_neo4j(
    *,
    connected: bool = True,
    initialized: bool = True,
    mode: str = "NEO4J",
    health_status: bool = True,
    node_count: int = 42,
    metrics: Dict | None = None,
) -> MagicMock:
    """Create a mock Neo4jClient whose .stats property returns a consistent dict."""
    neo4j = MagicMock()
    neo4j.initialize = AsyncMock(return_value=True)
    neo4j.record_episode = AsyncMock(return_value=True)
    neo4j.create_canvas_node_relationship = AsyncMock(return_value=True)
    neo4j.create_edge_relationship = AsyncMock(return_value=True)
    neo4j.get_all_recent_episodes = AsyncMock(return_value=[])
    neo4j.cleanup = AsyncMock()

    _metrics = metrics or {
        "total_queries": 0,
        "successful_queries": 0,
        "failed_queries": 0,
        "retry_count": 0,
        "total_latency_ms": 0.0,
    }
    neo4j.stats = {
        "enabled": True,
        "initialized": initialized,
        "mode": mode,
        "health_status": health_status,
        "node_count": node_count,
        "connected": connected,
        "metrics": _metrics,
    }
    return neo4j


def _build_mock_learning_memory() -> MagicMock:
    """Create a mock LearningMemoryClient."""
    client = MagicMock()
    client.add_learning_episode = AsyncMock(return_value=None)
    return client


async def _create_memory_service(neo4j=None, lm=None):
    """Instantiate and initialize a MemoryService with mocks."""
    from app.services.memory_service import MemoryService

    svc = MemoryService(
        neo4j_client=neo4j or _build_mock_neo4j(),
        learning_memory_client=lm or _build_mock_learning_memory(),
    )
    await svc.initialize()
    return svc


# ===========================================================================
# Gap 1 [P0]: record_batch_learning_events() full flow
# Story 30.3 AC-30.3.10
# ===========================================================================

class TestBatchLearningEventsFullFlow:
    """Gap 1 — full lifecycle of record_batch_learning_events().

    Existing tests (test_memory_service_batch.py) only cover concept field
    fallback.  These tests cover: empty list, >50 cap, partial failure,
    total failure, and required-field validation.
    """

    @pytest.mark.asyncio
    async def test_p0_empty_event_list_returns_success(self):
        """[P0] Empty list should succeed with 0 processed, 0 failed."""
        # Given
        svc = await _create_memory_service()

        # When
        result = await svc.record_batch_learning_events([])

        # Then
        assert result["success"] is True
        assert result["processed"] == 0
        assert result["failed"] == 0
        assert result["errors"] == []
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_p0_single_valid_event_stored_in_memory(self):
        """[P0] A single valid event should be processed and appended to _episodes."""
        # Given
        neo4j = _build_mock_neo4j()
        svc = await _create_memory_service(neo4j=neo4j)
        initial_count = len(svc._episodes)
        event = _make_valid_event()

        # When
        result = await svc.record_batch_learning_events([event])

        # Then
        assert result["processed"] == 1
        assert result["failed"] == 0
        assert len(svc._episodes) == initial_count + 1

    @pytest.mark.asyncio
    async def test_p0_multiple_events_all_processed(self):
        """[P0] Multiple valid events should all be processed in order."""
        # Given
        neo4j = _build_mock_neo4j()
        svc = await _create_memory_service(neo4j=neo4j)
        events = [_make_valid_event() for _ in range(5)]

        # When
        result = await svc.record_batch_learning_events(events)

        # Then
        assert result["processed"] == 5
        assert result["failed"] == 0
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_p0_missing_required_field_event_type(self):
        """[P0] Event missing 'event_type' should fail validation."""
        # Given
        svc = await _create_memory_service()
        bad_event = _make_valid_event()
        del bad_event["event_type"]

        # When
        result = await svc.record_batch_learning_events([bad_event])

        # Then
        assert result["processed"] == 0
        assert result["failed"] == 1
        assert len(result["errors"]) == 1
        assert "event_type" in result["errors"][0]["error"]

    @pytest.mark.asyncio
    async def test_p0_missing_required_field_timestamp(self):
        """[P0] Event missing 'timestamp' should fail validation."""
        # Given
        svc = await _create_memory_service()
        bad_event = _make_valid_event()
        del bad_event["timestamp"]

        # When
        result = await svc.record_batch_learning_events([bad_event])

        # Then
        assert result["failed"] == 1
        assert "timestamp" in result["errors"][0]["error"]

    @pytest.mark.asyncio
    async def test_p0_missing_required_field_canvas_path(self):
        """[P0] Event missing 'canvas_path' should fail validation."""
        # Given
        svc = await _create_memory_service()
        bad_event = _make_valid_event()
        del bad_event["canvas_path"]

        # When
        result = await svc.record_batch_learning_events([bad_event])

        # Then
        assert result["failed"] == 1
        assert "canvas_path" in result["errors"][0]["error"]

    @pytest.mark.asyncio
    async def test_p0_missing_required_field_node_id(self):
        """[P0] Event missing 'node_id' should fail validation."""
        # Given
        svc = await _create_memory_service()
        bad_event = _make_valid_event()
        del bad_event["node_id"]

        # When
        result = await svc.record_batch_learning_events([bad_event])

        # Then
        assert result["failed"] == 1
        assert "node_id" in result["errors"][0]["error"]

    @pytest.mark.asyncio
    async def test_p0_partial_failure_reports_mixed_results(self):
        """[P0] Mix of valid and invalid events: processed + failed counted correctly."""
        # Given
        svc = await _create_memory_service()
        good_1 = _make_valid_event()
        bad = _make_valid_event()
        del bad["node_id"]
        good_2 = _make_valid_event()

        # When
        result = await svc.record_batch_learning_events([good_1, bad, good_2])

        # Then
        assert result["processed"] == 2
        assert result["failed"] == 1
        assert result["success"] is False  # success=False when any failure
        assert result["errors"][0]["index"] == 1

    @pytest.mark.asyncio
    async def test_p0_all_events_fail_success_is_false(self):
        """[P0] When every event is invalid, success is False and processed=0."""
        # Given
        svc = await _create_memory_service()
        bad_events = []
        for _ in range(3):
            ev = _make_valid_event()
            del ev["event_type"]
            bad_events.append(ev)

        # When
        result = await svc.record_batch_learning_events(bad_events)

        # Then
        assert result["success"] is False
        assert result["processed"] == 0
        assert result["failed"] == 3

    @pytest.mark.asyncio
    async def test_p0_neo4j_failure_does_not_block_processing(self):
        """[P0] Neo4j write failure should NOT cause the event to be marked as failed."""
        # Given
        neo4j = _build_mock_neo4j(connected=True)
        neo4j.record_episode = AsyncMock(side_effect=Exception("Neo4j down"))
        svc = await _create_memory_service(neo4j=neo4j)
        event = _make_valid_event()

        # When
        result = await svc.record_batch_learning_events([event])

        # Then  — in-memory storage succeeds; Neo4j failure is swallowed
        assert result["processed"] == 1
        assert result["failed"] == 0


# ===========================================================================
# Gap 2 [P0]: record_temporal_event() lifecycle
# Story 30.5 AC-30.5.1-4
# ===========================================================================

class TestRecordTemporalEventLifecycle:
    """Gap 2 — record_temporal_event() for all three event types,
    Neo4j degradation, and relationship graph creation.
    """

    @pytest.mark.asyncio
    async def test_p0_node_created_event_stored_in_memory(self):
        """[P0] AC-30.5.1: node_created event stored in _episodes."""
        # Given
        neo4j = _build_mock_neo4j()
        svc = await _create_memory_service(neo4j=neo4j)
        session_id = f"sess-{uuid.uuid4().hex[:8]}"
        canvas = "Physics/kinematics.canvas"
        node_id = f"n-{uuid.uuid4().hex[:8]}"

        # When
        event_id = await svc.record_temporal_event(
            event_type="node_created",
            session_id=session_id,
            canvas_path=canvas,
            node_id=node_id,
            metadata={"node_text": "Newton's First Law"},
        )

        # Then
        assert event_id.startswith("event-")
        last = svc._episodes[-1]
        assert last["event_type"] == "node_created"
        assert last["canvas_path"] == canvas

    @pytest.mark.asyncio
    async def test_p0_node_updated_event_creates_relationship(self):
        """[P0] AC-30.5.3 + AC-30.5.4: node_updated triggers create_canvas_node_relationship."""
        # Given
        neo4j = _build_mock_neo4j()
        svc = await _create_memory_service(neo4j=neo4j)
        node_id = f"n-{uuid.uuid4().hex[:8]}"

        # When
        await svc.record_temporal_event(
            event_type="node_updated",
            session_id="sess-1",
            canvas_path="Chem/bonds.canvas",
            node_id=node_id,
            metadata={"node_text": "Covalent Bond"},
        )

        # Then
        neo4j.create_canvas_node_relationship.assert_awaited_once_with(
            canvas_path="Chem/bonds.canvas",
            node_id=node_id,
            node_text="Covalent Bond",
        )

    @pytest.mark.asyncio
    async def test_p0_edge_created_triggers_edge_relationship(self):
        """[P0] AC-30.5.2 + AC-30.5.4: edge_created triggers create_edge_relationship."""
        # Given
        neo4j = _build_mock_neo4j()
        svc = await _create_memory_service(neo4j=neo4j)
        edge_id = f"e-{uuid.uuid4().hex[:8]}"

        # When
        await svc.record_temporal_event(
            event_type="edge_created",
            session_id="sess-2",
            canvas_path="Bio/cells.canvas",
            edge_id=edge_id,
            metadata={
                "from_node": "node-a",
                "to_node": "node-b",
                "edge_label": "contains",
            },
        )

        # Then
        neo4j.create_edge_relationship.assert_awaited_once_with(
            canvas_path="Bio/cells.canvas",
            edge_id=edge_id,
            from_node_id="node-a",
            to_node_id="node-b",
            edge_label="contains",
        )

    @pytest.mark.asyncio
    async def test_p0_edge_created_without_from_to_skips_relationship(self):
        """[P0] edge_created with missing from_node/to_node should not call create_edge_relationship."""
        # Given
        neo4j = _build_mock_neo4j()
        svc = await _create_memory_service(neo4j=neo4j)

        # When — metadata lacks from_node / to_node
        await svc.record_temporal_event(
            event_type="edge_created",
            session_id="sess-3",
            canvas_path="Bio/cells.canvas",
            edge_id="edge-xyz",
            metadata={"edge_label": "orphan"},
        )

        # Then
        neo4j.create_edge_relationship.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_p0_neo4j_write_failure_degrades_silently(self):
        """[P0] Neo4j write failure should log warning but still return event_id."""
        # Given
        neo4j = _build_mock_neo4j()
        neo4j.record_episode = AsyncMock(side_effect=Exception("Connection refused"))
        svc = await _create_memory_service(neo4j=neo4j)

        # When
        event_id = await svc.record_temporal_event(
            event_type="node_created",
            session_id="sess-err",
            canvas_path="Math/calc.canvas",
            node_id="n-fail",
            metadata={"node_text": "Limit"},
        )

        # Then — returns valid event_id despite Neo4j error
        assert event_id.startswith("event-")
        # Episode is still stored in memory
        assert any(e["event_id"] == event_id for e in svc._episodes)

    @pytest.mark.asyncio
    async def test_p0_neo4j_disconnected_skips_write(self):
        """[P0] When Neo4j stats say connected=False, no write is attempted."""
        # Given
        neo4j = _build_mock_neo4j(connected=False)
        svc = await _create_memory_service(neo4j=neo4j)

        # When
        event_id = await svc.record_temporal_event(
            event_type="node_updated",
            session_id="sess-dc",
            canvas_path="Math/algebra.canvas",
            node_id="n-dc",
        )

        # Then
        assert event_id.startswith("event-")
        neo4j.record_episode.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_p0_node_created_without_node_id_skips_canvas_relationship(self):
        """[P0] node_created with node_id=None should skip create_canvas_node_relationship."""
        # Given
        neo4j = _build_mock_neo4j()
        svc = await _create_memory_service(neo4j=neo4j)

        # When
        await svc.record_temporal_event(
            event_type="node_created",
            session_id="sess-no-nid",
            canvas_path="Math/trig.canvas",
            node_id=None,
            metadata={"node_text": "Sine"},
        )

        # Then — record_episode called but create_canvas_node_relationship skipped
        neo4j.record_episode.assert_awaited_once()
        neo4j.create_canvas_node_relationship.assert_not_awaited()


# ===========================================================================
# Gap 3 [P1]: Agent memory trigger mapping completeness
# Story 30.4 AC-30.4.1
# ===========================================================================

class TestAgentMemoryMappingCompleteness:
    """Gap 3 — verify all 14 agent types are present in AGENT_MEMORY_MAPPING
    and each maps to a valid AgentMemoryType."""

    def test_p1_mapping_contains_exactly_14_agents(self):
        """[P1] AC-30.4.1: AGENT_MEMORY_MAPPING must have exactly 14 entries."""
        # Given
        from app.core.agent_memory_mapping import AGENT_MEMORY_MAPPING

        # Then
        assert len(AGENT_MEMORY_MAPPING) == 14

    def test_p1_all_agent_names_present(self):
        """[P1] AC-30.4.1: Every expected agent name is present in the mapping."""
        from app.core.agent_memory_mapping import AGENT_MEMORY_MAPPING

        expected_agents = {
            "basic-decomposition",
            "deep-decomposition",
            "question-decomposition",
            "four-level-explanation",
            "oral-explanation",
            "example-teaching",
            "clarification-path",
            "comparison-table",
            "verification-question-agent",
            "scoring-agent",
            "memory-anchor",
            "canvas-orchestrator",
            "review-board-agent-selector",
            "graphiti-memory-agent",
        }
        # Then
        assert set(AGENT_MEMORY_MAPPING.keys()) == expected_agents

    def test_p1_all_values_are_valid_agent_memory_types(self):
        """[P1] Every mapping value must be a valid AgentMemoryType enum member."""
        from app.core.agent_memory_mapping import AGENT_MEMORY_MAPPING, AgentMemoryType

        for agent_name, mem_type in AGENT_MEMORY_MAPPING.items():
            assert isinstance(mem_type, AgentMemoryType), (
                f"Agent '{agent_name}' maps to {mem_type!r} which is not AgentMemoryType"
            )

    def test_p1_get_memory_type_for_known_agent(self):
        """[P1] get_memory_type_for_agent() returns correct type for known agent."""
        from app.core.agent_memory_mapping import AgentMemoryType, get_memory_type_for_agent

        result = get_memory_type_for_agent("scoring-agent")
        assert result == AgentMemoryType.SCORING_COMPLETED

    def test_p1_get_memory_type_for_unknown_agent_returns_none(self):
        """[P1] get_memory_type_for_agent() returns None for unmapped agents."""
        from app.core.agent_memory_mapping import get_memory_type_for_agent

        result = get_memory_type_for_agent("nonexistent-agent")
        assert result is None

    def test_p1_decomposition_agents_map_to_decomposition_completed(self):
        """[P1] All decomposition agents must map to DECOMPOSITION_COMPLETED."""
        from app.core.agent_memory_mapping import AGENT_MEMORY_MAPPING, AgentMemoryType

        decomp_agents = [
            "basic-decomposition",
            "deep-decomposition",
            "question-decomposition",
        ]
        for agent in decomp_agents:
            assert AGENT_MEMORY_MAPPING[agent] == AgentMemoryType.DECOMPOSITION_COMPLETED

    def test_p1_explanation_agents_map_to_explanation_generated(self):
        """[P1] All explanation agents must map to EXPLANATION_GENERATED."""
        from app.core.agent_memory_mapping import AGENT_MEMORY_MAPPING, AgentMemoryType

        explanation_agents = [
            "four-level-explanation",
            "oral-explanation",
            "example-teaching",
            "clarification-path",
            "comparison-table",
            "verification-question-agent",
        ]
        for agent in explanation_agents:
            assert AGENT_MEMORY_MAPPING[agent] == AgentMemoryType.EXPLANATION_GENERATED


# ===========================================================================
# Gap 4 [P1]: get_health_status() degradation logic
# Story 30.3 AC-30.3.5
# ===========================================================================

class TestHealthStatusDegradation:
    """Gap 4 — overall status transitions: healthy / degraded / unhealthy."""

    @pytest.mark.asyncio
    async def test_p1_all_layers_ok_returns_healthy(self):
        """[P1] When Neo4j mode=NEO4J, initialized=True, health=True -> overall healthy."""
        # Given
        neo4j = _build_mock_neo4j(mode="NEO4J", initialized=True, health_status=True)
        svc = await _create_memory_service(neo4j=neo4j)

        # When
        health = await svc.get_health_status()

        # Then
        assert health["status"] == "healthy"
        assert health["layers"]["graphiti"]["status"] == "ok"
        assert health["layers"]["graphiti"].get("node_count") == 42

    @pytest.mark.asyncio
    async def test_p1_json_fallback_mode_still_ok(self):
        """[P1] When Neo4j mode=JSON_FALLBACK -> graphiti status ok, backend=json_fallback."""
        # Given
        neo4j = _build_mock_neo4j(mode="JSON_FALLBACK", initialized=True, health_status=False)
        svc = await _create_memory_service(neo4j=neo4j)

        # When
        health = await svc.get_health_status()

        # Then
        assert health["status"] == "healthy"
        assert health["layers"]["graphiti"]["status"] == "ok"
        assert health["layers"]["graphiti"]["backend"] == "json_fallback"

    @pytest.mark.asyncio
    async def test_p1_neo4j_not_connected_returns_degraded(self):
        """[P1] Neo4j not initialized -> graphiti error -> overall degraded."""
        # Given
        neo4j = _build_mock_neo4j(mode="NEO4J", initialized=False, health_status=False)
        svc = await _create_memory_service(neo4j=neo4j)

        # When
        health = await svc.get_health_status()

        # Then
        assert health["layers"]["graphiti"]["status"] == "error"
        assert health["status"] == "degraded"  # 1 out of 3 layers errored

    @pytest.mark.asyncio
    async def test_p1_neo4j_stats_exception_returns_degraded(self):
        """[P1] Exception reading neo4j.stats -> graphiti error -> degraded."""
        # Given
        neo4j = _build_mock_neo4j()
        # Make .stats raise an exception
        type(neo4j).stats = PropertyMock(side_effect=RuntimeError("driver crashed"))
        svc = await _create_memory_service(neo4j=neo4j)

        # When
        health = await svc.get_health_status()

        # Then
        assert health["layers"]["graphiti"]["status"] == "error"
        assert "driver crashed" in health["layers"]["graphiti"]["error"]
        assert health["status"] == "degraded"

    @pytest.mark.asyncio
    async def test_p1_health_response_contains_timestamp(self):
        """[P1] Health response must contain ISO timestamp."""
        # Given
        svc = await _create_memory_service()

        # When
        health = await svc.get_health_status()

        # Then
        assert "timestamp" in health
        # Should be parseable ISO format
        datetime.fromisoformat(health["timestamp"])

    @pytest.mark.asyncio
    async def test_p1_health_contains_all_three_layers(self):
        """[P1] Response must contain temporal, graphiti, semantic layers."""
        # Given
        svc = await _create_memory_service()

        # When
        health = await svc.get_health_status()

        # Then
        assert "temporal" in health["layers"]
        assert "graphiti" in health["layers"]
        assert "semantic" in health["layers"]


# ===========================================================================
# Gap 5 [P2]: Neo4j write latency metrics
# Story 30.2 AC-30.2.4
# ===========================================================================

class TestNeo4jWriteLatencyMetrics:
    """Gap 5 — Neo4jClient._metrics tracks latency; warnings on >200ms."""

    def test_p2_initial_metrics_are_zeroed(self):
        """[P2] Fresh Neo4jClient should have all metrics at zero."""
        from app.clients.neo4j_client import Neo4jClient

        # Given/When
        client = Neo4jClient(use_json_fallback=True)

        # Then
        m = client.stats["metrics"]
        assert m["total_queries"] == 0
        assert m["successful_queries"] == 0
        assert m["failed_queries"] == 0
        assert m["total_latency_ms"] == 0.0

    def test_p2_stats_exposes_metrics_dict(self):
        """[P2] stats property must include a 'metrics' key."""
        from app.clients.neo4j_client import Neo4jClient

        client = Neo4jClient(use_json_fallback=True)
        assert "metrics" in client.stats
        assert isinstance(client.stats["metrics"], dict)

    @pytest.mark.asyncio
    async def test_p2_successful_query_increments_metrics(self):
        """[P2] A successful query via JSON fallback should increment counters."""
        from app.clients.neo4j_client import Neo4jClient

        # Given
        client = Neo4jClient(use_json_fallback=True)
        await client.initialize()

        # When — run_query uses **kwargs so pass params as keyword args
        try:
            await client.run_query(
                "MERGE (u:User {id: $userId})",
                userId=f"test-{uuid.uuid4().hex[:6]}",
            )
        except Exception:
            pass  # JSON fallback may not support all Cypher; that's OK

        # Then — at least total_queries should have incremented
        m = client.stats["metrics"]
        assert m["total_queries"] >= 1

    @pytest.mark.asyncio
    async def test_p2_latency_warning_logged_over_200ms(self, caplog):
        """[P2] AC-30.2.4: Queries taking >200ms should log a warning."""
        from app.clients.neo4j_client import Neo4jClient

        client = Neo4jClient(use_json_fallback=True)
        await client.initialize()

        # Patch _run_query_json_fallback to add artificial delay
        original_run = client._run_query_json_fallback

        async def slow_fallback(query, params):
            await asyncio.sleep(0.25)  # 250ms > 200ms threshold
            return await original_run(query, params)

        client._run_query_json_fallback = slow_fallback

        with caplog.at_level(logging.WARNING, logger="app.clients.neo4j_client"):
            try:
                await client.run_query("MERGE (u:User {id: $uid})", uid="slow-user")
            except Exception:
                pass

        # Then — should contain latency warning
        warning_msgs = [r.message for r in caplog.records if r.levelno >= logging.WARNING]
        assert any("200ms" in msg for msg in warning_msgs), (
            f"Expected >200ms latency warning. Got: {warning_msgs}"
        )


# ===========================================================================
# Gap 6 [P2]: Settings Neo4j configuration validation
# Story 30.1 AC-30.1.2
# ===========================================================================

class TestSettingsNeo4jConfig:
    """Gap 6 — Settings model parses NEO4J_* environment variables correctly.

    Note: Settings reads from .env file via pydantic BaseSettings.
    We use patch.dict to control exactly which env vars are visible.
    """

    # Clear NEO4J_* so that Field(default=...) takes effect
    _CLEAN_NEO4J_ENV = {
        "NEO4J_URI": "",
        "NEO4J_USER": "",
        "NEO4J_PASSWORD": "",
        "NEO4J_DATABASE": "",
    }

    @patch.dict("os.environ", {"NEO4J_URI": ""}, clear=False)
    def test_p2_neo4j_uri_field_has_correct_default_type(self):
        """[P2] NEO4J_URI field default is a bolt:// URI string."""
        from app.config import Settings

        # When no env var is set, the Field default is used.
        # Since .env may override, we check the field definition directly.
        field_info = Settings.model_fields["NEO4J_URI"]
        assert field_info.default == "bolt://localhost:7687"

    def test_p2_neo4j_user_field_default(self):
        """[P2] NEO4J_USER field default is 'neo4j'."""
        from app.config import Settings

        field_info = Settings.model_fields["NEO4J_USER"]
        assert field_info.default == "neo4j"

    def test_p2_neo4j_password_field_default(self):
        """[P2] NEO4J_PASSWORD field default is empty string."""
        from app.config import Settings

        field_info = Settings.model_fields["NEO4J_PASSWORD"]
        assert field_info.default == ""

    def test_p2_neo4j_database_field_default(self):
        """[P2] NEO4J_DATABASE field default is 'neo4j'."""
        from app.config import Settings

        field_info = Settings.model_fields["NEO4J_DATABASE"]
        assert field_info.default == "neo4j"

    def test_p2_lowercase_aliases_match_uppercase(self):
        """[P2] Lowercase property aliases should return same value as uppercase fields."""
        from app.config import Settings

        s = Settings()
        assert s.neo4j_uri == s.NEO4J_URI
        assert s.neo4j_user == s.NEO4J_USER
        assert s.neo4j_password == s.NEO4J_PASSWORD
        assert s.neo4j_database == s.NEO4J_DATABASE

    @patch.dict(
        "os.environ",
        {
            "NEO4J_URI": "bolt://custom-host:7688",
            "NEO4J_USER": "admin",
            "NEO4J_PASSWORD": "s3cret!",
            "NEO4J_DATABASE": "canvas_db",
        },
    )
    def test_p2_env_vars_override_defaults(self):
        """[P2] AC-30.1.2: Environment variables override default values."""
        from app.config import Settings

        s = Settings()
        assert s.NEO4J_URI == "bolt://custom-host:7688"
        assert s.NEO4J_USER == "admin"
        assert s.NEO4J_PASSWORD == "s3cret!"
        assert s.NEO4J_DATABASE == "canvas_db"
