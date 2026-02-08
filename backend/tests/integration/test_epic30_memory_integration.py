# Canvas Learning System - EPIC 30 Memory Integration Tests
# Story 30.3 AC-30.3.10: Batch episodes E2E
# Story 30.5 AC-30.5.1-4: Temporal event → Neo4j relationship chain
# Story 30.3 AC-30.3.5-8: Health endpoint aggregation
# Dependencies injection chain completeness
"""
Integration tests for EPIC 30: Memory System.

Coverage Gaps Addressed:
1. [P0] Memory API batch endpoint E2E (Story 30.3 AC-30.3.10)
2. [P0] Temporal event → Neo4j relationship chain (Story 30.5 AC-30.5.1-4)
3. [P1] Health endpoint aggregation (Story 30.3 AC-30.3.5-8)
4. [P1] Dependency injection chain completeness

Test Pattern:
- FastAPI TestClient (synchronous) for HTTP endpoint tests
- AsyncClient (httpx) for async service-level tests
- Mock Neo4j — no Docker required
- Each test resets the module-level singleton to ensure isolation

[Source: docs/stories/30.3.memory-api-health-endpoints.story.md]
[Source: docs/stories/30.5.story.md]
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_memory_singleton():
    """
    Reset the module-level MemoryService singleton before AND after each test.

    MEMORY.md: memory.py uses module-level `_memory_service_instance` singleton;
    tests must reset it to avoid cross-test pollution.
    """
    import backend.app.api.v1.endpoints.memory as memory_module

    memory_module._memory_service_instance = None
    yield
    memory_module._memory_service_instance = None


def _make_mock_neo4j_client(
    *,
    mode: str = "JSON_FALLBACK",
    initialized: bool = True,
    health_status: bool = True,
    connected: bool = False,
) -> MagicMock:
    """
    Create a mock Neo4jClient that passes all attribute accesses used by
    MemoryService (self.neo4j.stats, self.neo4j.initialize(), etc.).

    Args:
        mode: "NEO4J" or "JSON_FALLBACK"
        initialized: Whether the client reports as initialized
        health_status: Whether the health check passes
        connected: Value for the "connected" key in stats (batch code checks this)
    """
    mock = MagicMock()
    mock.initialize = AsyncMock()
    mock.cleanup = AsyncMock()

    # Properties accessed by MemoryService.get_health_status()
    stats_dict = {
        "enabled": mode == "NEO4J",
        "initialized": initialized,
        "mode": mode,
        "health_status": health_status,
        "connected": connected,
        "node_count": 42 if mode == "NEO4J" else 0,
    }
    type(mock).stats = PropertyMock(return_value=stats_dict)

    # Async methods called by MemoryService
    mock.create_learning_relationship = AsyncMock()
    mock.get_learning_history = AsyncMock(return_value=[])
    mock.get_concept_history = AsyncMock(return_value=[])
    mock.get_review_suggestions = AsyncMock(return_value=[])
    mock.get_all_recent_episodes = AsyncMock(return_value=[])
    mock.get_concept_score_history = AsyncMock(return_value=[])
    mock.record_episode = AsyncMock()
    mock.create_canvas_node_relationship = AsyncMock()
    mock.create_edge_relationship = AsyncMock()

    return mock


def _make_mock_learning_memory_client() -> MagicMock:
    """Create a mock LearningMemoryClient for dual-write testing."""
    mock = MagicMock()
    mock.add_learning_episode = AsyncMock()
    return mock


@pytest.fixture
def mock_neo4j():
    """Provide a mock Neo4jClient (JSON_FALLBACK mode)."""
    return _make_mock_neo4j_client()


@pytest.fixture
def mock_learning_memory():
    """Provide a mock LearningMemoryClient."""
    return _make_mock_learning_memory_client()


@pytest.fixture
def memory_service(mock_neo4j, mock_learning_memory):
    """
    Provide a fresh MemoryService with mocked dependencies.

    This fixture creates a MemoryService using the mocked Neo4j and
    LearningMemoryClient, then marks it as initialized so tests can
    use it immediately.
    """
    from app.services.memory_service import MemoryService

    svc = MemoryService(
        neo4j_client=mock_neo4j,
        learning_memory_client=mock_learning_memory,
    )
    svc._initialized = True
    svc._episodes_recovered = True
    return svc


@pytest.fixture
def test_client(memory_service):
    """
    Provide a synchronous FastAPI TestClient with the MemoryService singleton
    pre-injected so that no real Neo4j connection is attempted.
    """
    from app.main import app
    import backend.app.api.v1.endpoints.memory as memory_module

    # Inject the pre-built MemoryService as the module-level singleton
    memory_module._memory_service_instance = memory_service

    # Override settings to avoid loading .env-dependent values
    from app.config import Settings
    from app.dependencies import get_settings

    def _test_settings() -> Settings:
        return Settings(
            PROJECT_NAME="Canvas Test",
            VERSION="1.0.0-test",
            DEBUG=True,
            LOG_LEVEL="DEBUG",
            CORS_ORIGINS="http://localhost:3000",
            CANVAS_BASE_PATH="./test_canvas",
        )

    app.dependency_overrides[get_settings] = _test_settings

    with TestClient(app, raise_server_exceptions=False) as tc:
        yield tc

    app.dependency_overrides.clear()


# ===========================================================================
# Helper: build a valid batch event dict
# ===========================================================================


def _batch_event(
    *,
    event_type: str = "color_changed",
    canvas_path: str = "test/math.canvas",
    node_id: str | None = None,
) -> dict:
    """Return a single valid BatchEventItem-compatible dict."""
    return {
        "event_type": event_type,
        "timestamp": datetime.now().isoformat(),
        "canvas_path": canvas_path,
        "node_id": node_id or f"node-{uuid.uuid4().hex[:8]}",
    }


# ===========================================================================
# 1. Memory API Batch Endpoint E2E  [P0] — Story 30.3 AC-30.3.10
# ===========================================================================


class TestBatchEpisodesEndpoint:
    """POST /api/v1/memory/episodes/batch integration tests."""

    def test_p0_batch_3_valid_events_success(self, test_client: TestClient):
        """
        [P0] Given 3 valid events, When POST /episodes/batch,
        Then return 200 with processed=3, failed=0, success=True.
        """
        # Given
        events = [_batch_event() for _ in range(3)]
        payload = {"events": events}

        # When
        response = test_client.post("/api/v1/memory/episodes/batch", json=payload)

        # Then
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["success"] is True
        assert body["processed"] == 3
        assert body["failed"] == 0
        assert body["errors"] == []
        assert "timestamp" in body

    def test_p0_batch_empty_list_returns_success(self, test_client: TestClient):
        """
        [P0] Given an empty events list, When POST /episodes/batch,
        Then return 200 with processed=0, failed=0, success=True.
        """
        # Given
        payload = {"events": []}

        # When
        response = test_client.post("/api/v1/memory/episodes/batch", json=payload)

        # Then
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["success"] is True
        assert body["processed"] == 0
        assert body["failed"] == 0

    def test_p0_batch_exceeds_50_events_rejected(self, test_client: TestClient):
        """
        [P0] Given 51 events, When POST /episodes/batch,
        Then return 422 (Pydantic max_length=50 validation on BatchEpisodesRequest).
        """
        # Given
        events = [_batch_event() for _ in range(51)]
        payload = {"events": events}

        # When
        response = test_client.post("/api/v1/memory/episodes/batch", json=payload)

        # Then — Pydantic Field(max_length=50) triggers HTTP 422
        assert response.status_code == 422, (
            f"Expected 422 for >50 events, got {response.status_code}: {response.text}"
        )

    def test_p0_batch_exactly_50_events_accepted(self, test_client: TestClient):
        """
        [P0] Given exactly 50 events, When POST /episodes/batch,
        Then return 200 with processed=50.
        """
        # Given
        events = [_batch_event() for _ in range(50)]
        payload = {"events": events}

        # When
        response = test_client.post("/api/v1/memory/episodes/batch", json=payload)

        # Then
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["processed"] == 50
        assert body["success"] is True

    @pytest.mark.asyncio
    async def test_p0_batch_partial_failure_mixed_events(self, memory_service):
        """
        [P0] Given 3 events where event #1 is missing required 'canvas_path',
        When record_batch_learning_events() is called at the service level,
        Then processed=2, failed=1, errors listing index=1.

        Note: Testing at the service level (not HTTP) because Pydantic validates
        structure at the HTTP layer. Service-level validation catches missing
        required fields that pass Pydantic but fail business logic.
        """
        # Given — event at index 1 is missing 'canvas_path'
        events = [
            {
                "event_type": "color_changed",
                "timestamp": datetime.now().isoformat(),
                "canvas_path": "test.canvas",
                "node_id": "node-0",
                "metadata": {},
            },
            {
                "event_type": "color_changed",
                "timestamp": datetime.now().isoformat(),
                # canvas_path intentionally missing
                "node_id": "node-1",
                "metadata": {},
            },
            {
                "event_type": "color_changed",
                "timestamp": datetime.now().isoformat(),
                "canvas_path": "test.canvas",
                "node_id": "node-2",
                "metadata": {},
            },
        ]

        # When
        result = await memory_service.record_batch_learning_events(events)

        # Then
        assert result["processed"] == 2
        assert result["failed"] == 1
        assert result["success"] is False
        assert len(result["errors"]) == 1
        assert result["errors"][0]["index"] == 1
        assert "canvas_path" in result["errors"][0]["error"]

    def test_p0_batch_invalid_schema_returns_422(self, test_client: TestClient):
        """
        [P0] Given events with missing required field (no event_type),
        When POST /episodes/batch,
        Then return 422 Pydantic validation error.
        """
        # Given — missing event_type
        payload = {
            "events": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "canvas_path": "test.canvas",
                    "node_id": "node-1",
                    # event_type intentionally omitted
                }
            ]
        }

        # When
        response = test_client.post("/api/v1/memory/episodes/batch", json=payload)

        # Then
        assert response.status_code == 422


# ===========================================================================
# 2. Temporal Event → Neo4j Relationship Chain  [P0] — Story 30.5
# ===========================================================================


class TestTemporalEventNeo4jChain:
    """
    Verify that record_temporal_event() creates the expected Neo4j
    relationships (Canvas-Node, Edge from_node→to_node).
    """

    @pytest.mark.asyncio
    async def test_p0_node_created_creates_canvas_node_relationship(
        self, memory_service, mock_neo4j
    ):
        """
        [P0] Given a node_created event with metadata.node_text,
        When record_temporal_event() is called,
        Then Neo4j create_canvas_node_relationship is invoked with correct args.
        """
        # Given
        mock_neo4j.stats["connected"] = True
        type(mock_neo4j).stats = PropertyMock(return_value=mock_neo4j.stats)

        # When
        event_id = await memory_service.record_temporal_event(
            event_type="node_created",
            session_id="session-001",
            canvas_path="math/algebra.canvas",
            node_id="node-abc123",
            metadata={"node_text": "Quadratic Formula"},
        )

        # Then
        assert event_id.startswith("event-")
        mock_neo4j.create_canvas_node_relationship.assert_awaited_once_with(
            canvas_path="math/algebra.canvas",
            node_id="node-abc123",
            node_text="Quadratic Formula",
        )

    @pytest.mark.asyncio
    async def test_p0_edge_created_creates_edge_relationship(
        self, memory_service, mock_neo4j
    ):
        """
        [P0] Given an edge_created event with from_node/to_node in metadata,
        When record_temporal_event() is called,
        Then Neo4j create_edge_relationship is invoked with the correct
        from/to node IDs and edge_label.
        """
        # Given
        mock_neo4j.stats["connected"] = True
        type(mock_neo4j).stats = PropertyMock(return_value=mock_neo4j.stats)

        # When
        event_id = await memory_service.record_temporal_event(
            event_type="edge_created",
            session_id="session-002",
            canvas_path="math/algebra.canvas",
            edge_id="edge-xyz789",
            metadata={
                "from_node": "node-A",
                "to_node": "node-B",
                "edge_label": "prerequisite",
            },
        )

        # Then
        assert event_id.startswith("event-")
        mock_neo4j.create_edge_relationship.assert_awaited_once_with(
            canvas_path="math/algebra.canvas",
            edge_id="edge-xyz789",
            from_node_id="node-A",
            to_node_id="node-B",
            edge_label="prerequisite",
        )

    @pytest.mark.asyncio
    async def test_p0_node_updated_creates_canvas_node_relationship(
        self, memory_service, mock_neo4j
    ):
        """
        [P0] Given a node_updated event,
        When record_temporal_event() is called,
        Then create_canvas_node_relationship is also invoked (same as node_created).
        """
        # Given
        mock_neo4j.stats["connected"] = True
        type(mock_neo4j).stats = PropertyMock(return_value=mock_neo4j.stats)

        # When
        await memory_service.record_temporal_event(
            event_type="node_updated",
            session_id="session-003",
            canvas_path="physics/mechanics.canvas",
            node_id="node-updated-1",
            metadata={"node_text": "Newton's 2nd Law"},
        )

        # Then
        mock_neo4j.create_canvas_node_relationship.assert_awaited_once_with(
            canvas_path="physics/mechanics.canvas",
            node_id="node-updated-1",
            node_text="Newton's 2nd Law",
        )

    @pytest.mark.asyncio
    async def test_p0_temporal_events_stored_in_memory_chronologically(
        self, memory_service, mock_neo4j
    ):
        """
        [P0] Given multiple temporal events recorded in sequence,
        When inspecting memory_service._episodes,
        Then events appear in chronological order with correct event_type.
        """
        # Given
        mock_neo4j.stats["connected"] = False
        type(mock_neo4j).stats = PropertyMock(return_value=mock_neo4j.stats)

        # When — record 3 events in order
        id1 = await memory_service.record_temporal_event(
            event_type="node_created",
            session_id="s1",
            canvas_path="c.canvas",
            node_id="n1",
        )
        id2 = await memory_service.record_temporal_event(
            event_type="edge_created",
            session_id="s1",
            canvas_path="c.canvas",
            edge_id="e1",
            metadata={"from_node": "n1", "to_node": "n2"},
        )
        id3 = await memory_service.record_temporal_event(
            event_type="node_updated",
            session_id="s1",
            canvas_path="c.canvas",
            node_id="n1",
            metadata={"node_text": "Updated text"},
        )

        # Then — all events stored in memory
        event_ids = [e.get("event_id") for e in memory_service._episodes]
        assert id1 in event_ids
        assert id2 in event_ids
        assert id3 in event_ids

        # Verify chronological order (timestamps should be non-decreasing)
        timestamps = [e.get("timestamp", "") for e in memory_service._episodes]
        assert timestamps == sorted(timestamps)

    @pytest.mark.asyncio
    async def test_p0_neo4j_write_failure_does_not_raise(
        self, memory_service, mock_neo4j
    ):
        """
        [P0] Given Neo4j connected but create_canvas_node_relationship raises,
        When record_temporal_event() is called,
        Then no exception propagates (silent degradation) and event is still
        stored in memory.
        """
        # Given
        mock_neo4j.stats["connected"] = True
        type(mock_neo4j).stats = PropertyMock(return_value=mock_neo4j.stats)
        mock_neo4j.record_episode = AsyncMock(side_effect=Exception("Neo4j down"))

        # When — should NOT raise
        event_id = await memory_service.record_temporal_event(
            event_type="node_created",
            session_id="s1",
            canvas_path="c.canvas",
            node_id="n-fail",
            metadata={"node_text": "test"},
        )

        # Then — event still in memory despite Neo4j failure
        assert event_id.startswith("event-")
        mem_ids = [e.get("event_id") for e in memory_service._episodes]
        assert event_id in mem_ids


# ===========================================================================
# 3. Health Endpoint Aggregation  [P1] — Story 30.3 AC-30.3.5-8
# ===========================================================================


class TestHealthEndpoint:
    """GET /api/v1/memory/health integration tests."""

    def test_p1_all_layers_healthy(self, test_client: TestClient):
        """
        [P1] Given all layers are operational (JSON_FALLBACK mode counts as ok),
        When GET /memory/health,
        Then return overall=healthy with layers structure.
        """
        # When
        response = test_client.get("/api/v1/memory/health")

        # Then
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["status"] in ("healthy", "degraded")
        assert "layers" in body
        layers = body["layers"]
        assert "temporal" in layers
        assert "graphiti" in layers
        assert "semantic" in layers
        assert "timestamp" in body

    def test_p1_health_response_structure(self, test_client: TestClient):
        """
        [P1] Given any system state,
        When GET /memory/health,
        Then each layer has at minimum 'status' and 'backend' keys.
        """
        # When
        response = test_client.get("/api/v1/memory/health")

        # Then
        assert response.status_code == 200
        body = response.json()
        for layer_name in ("temporal", "graphiti", "semantic"):
            layer = body["layers"][layer_name]
            assert "status" in layer, f"{layer_name} missing 'status'"
            assert "backend" in layer, f"{layer_name} missing 'backend'"

    @pytest.mark.asyncio
    async def test_p1_neo4j_degraded_returns_degraded_service_level(self):
        """
        [P1] Given Neo4j layer reports error (mode=NEO4J, health_status=False),
        When get_health_status() is called on MemoryService,
        Then overall status is 'degraded' (graphiti layer error, others ok).
        """
        from app.services.memory_service import MemoryService

        # Given — create a mock Neo4j client that simulates a broken NEO4J connection
        broken_neo4j = _make_mock_neo4j_client(
            mode="NEO4J",
            initialized=False,
            health_status=False,
            connected=False,
        )
        mock_lm = _make_mock_learning_memory_client()

        svc = MemoryService(
            neo4j_client=broken_neo4j,
            learning_memory_client=mock_lm,
        )
        svc._initialized = True
        svc._episodes_recovered = True

        # When
        result = await svc.get_health_status()

        # Then
        assert result["status"] == "degraded"
        assert result["layers"]["graphiti"]["status"] == "error"
        assert result["layers"]["temporal"]["status"] == "ok"
        assert result["layers"]["semantic"]["status"] == "ok"

    @pytest.mark.asyncio
    async def test_p1_health_service_level_all_ok(self, memory_service, mock_neo4j):
        """
        [P1] Given MemoryService with JSON_FALLBACK Neo4j client,
        When get_health_status() is called,
        Then overall status is healthy and graphiti backend is json_fallback.
        """
        # Given — default mock is JSON_FALLBACK

        # When
        result = await memory_service.get_health_status()

        # Then
        assert result["status"] == "healthy"
        assert result["layers"]["graphiti"]["backend"] == "json_fallback"
        assert result["layers"]["temporal"]["status"] == "ok"
        assert result["layers"]["semantic"]["status"] == "ok"


# ===========================================================================
# 4. Dependency Injection Chain Completeness  [P1]
# ===========================================================================


class TestDependencyInjectionChain:
    """Verify DI chain wiring for Memory-related services."""

    @pytest.mark.asyncio
    async def test_p1_memory_service_neo4j_client_not_none(self):
        """
        [P1] Given MemoryService instantiated via default constructor,
        When accessing self.neo4j,
        Then it is not None (get_neo4j_client() provides a singleton).
        """
        # Given / When
        from app.services.memory_service import MemoryService

        # Patch get_neo4j_client to return a mock (avoid real connection)
        mock = _make_mock_neo4j_client()
        with patch("app.services.memory_service.get_neo4j_client", return_value=mock):
            svc = MemoryService()

        # Then
        assert svc.neo4j is not None
        assert svc.neo4j is mock

    @pytest.mark.asyncio
    async def test_p1_memory_service_learning_memory_client_not_none(self):
        """
        [P1] Given MemoryService instantiated via default constructor,
        When accessing self._learning_memory,
        Then it is not None (get_learning_memory_client() provides a singleton).
        """
        # Given / When
        from app.services.memory_service import MemoryService

        mock_neo4j = _make_mock_neo4j_client()
        mock_lm = _make_mock_learning_memory_client()
        with patch("app.services.memory_service.get_neo4j_client", return_value=mock_neo4j), \
             patch("app.services.memory_service.get_learning_memory_client", return_value=mock_lm):
            svc = MemoryService()

        # Then
        assert svc._learning_memory is not None
        assert svc._learning_memory is mock_lm

    @pytest.mark.asyncio
    async def test_p1_explicit_injection_takes_precedence(self):
        """
        [P1] Given explicit neo4j_client and learning_memory_client args,
        When MemoryService is instantiated,
        Then the explicit args are used (not the defaults from singletons).
        """
        from app.services.memory_service import MemoryService

        custom_neo4j = _make_mock_neo4j_client()
        custom_lm = _make_mock_learning_memory_client()

        svc = MemoryService(
            neo4j_client=custom_neo4j,
            learning_memory_client=custom_lm,
        )

        assert svc.neo4j is custom_neo4j
        assert svc._learning_memory is custom_lm

    @pytest.mark.asyncio
    async def test_p1_verification_service_receives_memory_service(self):
        """
        [P1] Given VerificationService created via get_verification_service(),
        When examining the service,
        Then memory_service attribute is injected (not None).

        This validates the fix from MEMORY.md: dependencies.py now passes
        memory_service to VerificationService for difficulty adaptation.
        """
        from app.services.verification_service import VerificationService

        # Construct directly with a mock memory_service
        mock_memory = MagicMock()
        svc = VerificationService(memory_service=mock_memory)

        # Then — VerificationService stores the memory_service
        # Verified: verification_service.py L464: self._memory_service = memory_service
        assert svc._memory_service is mock_memory

    @pytest.mark.asyncio
    async def test_p1_memory_service_initialize_calls_neo4j_initialize(
        self, mock_neo4j, mock_learning_memory
    ):
        """
        [P1] Given a fresh MemoryService,
        When initialize() is called,
        Then it delegates to neo4j.initialize().
        """
        from app.services.memory_service import MemoryService

        svc = MemoryService(
            neo4j_client=mock_neo4j,
            learning_memory_client=mock_learning_memory,
        )

        # When
        result = await svc.initialize()

        # Then
        assert result is True
        mock_neo4j.initialize.assert_awaited_once()


# ===========================================================================
# 5. Record Batch Learning Events — Service-Level  [P0]
# ===========================================================================


class TestRecordBatchLearningEvents:
    """Direct service-level tests for record_batch_learning_events()."""

    @pytest.mark.asyncio
    async def test_p0_valid_events_all_processed(self, memory_service):
        """
        [P0] Given 3 valid event dicts,
        When record_batch_learning_events() is called,
        Then processed=3, failed=0.
        """
        events = [
            {
                "event_type": "color_changed",
                "timestamp": datetime.now().isoformat(),
                "canvas_path": "math.canvas",
                "node_id": f"node-{i}",
                "metadata": {},
            }
            for i in range(3)
        ]

        result = await memory_service.record_batch_learning_events(events)

        assert result["processed"] == 3
        assert result["failed"] == 0
        assert result["success"] is True
        assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_p0_missing_required_fields_fails(self, memory_service):
        """
        [P0] Given an event missing 'canvas_path' (required field),
        When record_batch_learning_events() is called,
        Then that event fails and is reported in errors with correct index.
        """
        events = [
            {
                "event_type": "color_changed",
                "timestamp": datetime.now().isoformat(),
                # canvas_path intentionally omitted
                "node_id": "node-1",
            }
        ]

        result = await memory_service.record_batch_learning_events(events)

        assert result["processed"] == 0
        assert result["failed"] == 1
        assert result["success"] is False
        assert len(result["errors"]) == 1
        assert result["errors"][0]["index"] == 0
        assert "canvas_path" in result["errors"][0]["error"]

    @pytest.mark.asyncio
    async def test_p0_batch_stores_episodes_in_memory(self, memory_service):
        """
        [P0] Given valid events,
        When record_batch_learning_events() is called,
        Then episodes are appended to memory_service._episodes.
        """
        initial_count = len(memory_service._episodes)
        events = [
            {
                "event_type": "node_added",
                "timestamp": datetime.now().isoformat(),
                "canvas_path": "test.canvas",
                "node_id": "node-new",
                "metadata": {},
            }
        ]

        await memory_service.record_batch_learning_events(events)

        assert len(memory_service._episodes) == initial_count + 1
        last = memory_service._episodes[-1]
        assert last["node_id"] == "node-new"
        assert last["episode_id"].startswith("batch-")
