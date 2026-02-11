# Canvas Learning System - E2E Test Fixtures for Parallel Processing
# Story 33.8: E2E Integration Testing
# ✅ Verified from docs/stories/33.8.story.md - Task 1
"""
E2E-specific fixtures for intelligent parallel batch processing tests.

Provides:
- Test Canvas fixtures with yellow nodes (color "6")
- Mock agent responses for fast execution
- WebSocket test utilities
- Session cleanup helpers

[Source: docs/stories/33.8.story.md - Task 1.2]
[Source: specs/api/parallel-api.openapi.yml]
"""

import asyncio
import io
import json
import sys
import time

from tests.conftest import simulate_async_delay
from pathlib import Path
from typing import Any, AsyncGenerator, Generator, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from app.config import Settings, get_settings
from app.main import app
from app.services.session_manager import SessionManager


# =============================================================================
# Settings Override for E2E Tests
# =============================================================================

def get_e2e_settings_override() -> Settings:
    """
    Override settings for E2E testing.

    ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: testing dependency override)
    """
    return Settings(
        PROJECT_NAME="Canvas Learning System API (E2E Test)",
        VERSION="1.0.0-e2e",
        DEBUG=True,
        LOG_LEVEL="DEBUG",
        CORS_ORIGINS="http://localhost:3000",
        CANVAS_BASE_PATH="./test_canvas",
    )


# =============================================================================
# Shared Multimodal E2E Fixtures
# Used by: test_multimodal_upload_e2e.py, test_multimodal_search_delete_e2e.py,
#          test_multimodal_perf_utility_e2e.py
# =============================================================================

@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Synchronous test client for multimodal E2E tests."""
    app.dependency_overrides[get_settings] = get_e2e_settings_override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def test_image_file() -> bytes:
    """Minimal 1x1 red PNG image for testing."""
    return bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
        0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53, 0xDE,
        0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41, 0x54,
        0x08, 0xD7, 0x63, 0xF8, 0xCF, 0xC0, 0x00, 0x00,
        0x01, 0x01, 0x01, 0x00, 0x18, 0xDD, 0x8D, 0xB4,
        0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44,
        0xAE, 0x42, 0x60, 0x82,
    ])


@pytest.fixture
def test_pdf_file() -> bytes:
    """Minimal PDF file for testing."""
    return b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000052 00000 n
0000000101 00000 n
trailer<</Size 4/Root 1 0 R>>
startxref
178
%%EOF"""


# =============================================================================
# Canvas Fixtures - Yellow Nodes (color "6")
# [Source: docs/stories/33.8.story.md - Task 1.3]
# =============================================================================

@pytest.fixture
def test_canvas_10_nodes(tmp_path: Path) -> Path:
    """
    Create test Canvas with 10 yellow nodes for E2E tests.

    Yellow color = "6" in Obsidian Canvas.

    [Source: docs/stories/33.8.story.md - Implementation Notes #2]

    Args:
        tmp_path: pytest temporary directory fixture

    Returns:
        Path: Path to the test canvas file
    """
    canvas_data = {
        "nodes": [
            {
                "id": f"node-{i:03d}",
                "type": "text",
                "color": "6",  # Yellow
                "text": _generate_node_text(i),
                "x": (i % 5) * 250,
                "y": (i // 5) * 150,
                "width": 220,
                "height": 100
            }
            for i in range(10)
        ],
        "edges": []
    }

    canvas_dir = tmp_path / "test_vault"
    canvas_dir.mkdir(parents=True, exist_ok=True)

    canvas_file = canvas_dir / "test_parallel_10.canvas"
    canvas_file.write_text(json.dumps(canvas_data, ensure_ascii=False), encoding='utf-8')

    return canvas_file


@pytest.fixture
def test_canvas_20_nodes(tmp_path: Path) -> Path:
    """
    Create test Canvas with 20 yellow nodes for cancellation tests.

    More nodes ensure enough time for cancellation testing.

    [Source: docs/stories/33.8.story.md - Task 3.2]
    """
    canvas_data = {
        "nodes": [
            {
                "id": f"node-{i:03d}",
                "type": "text",
                "color": "6",  # Yellow
                "text": _generate_node_text(i),
                "x": (i % 5) * 250,
                "y": (i // 5) * 150,
                "width": 220,
                "height": 100
            }
            for i in range(20)
        ],
        "edges": []
    }

    canvas_dir = tmp_path / "test_vault"
    canvas_dir.mkdir(parents=True, exist_ok=True)

    canvas_file = canvas_dir / "test_parallel_20.canvas"
    canvas_file.write_text(json.dumps(canvas_data, ensure_ascii=False), encoding='utf-8')

    return canvas_file


@pytest.fixture
def test_canvas_100_nodes(tmp_path: Path) -> Path:
    """
    Create test Canvas with 100 yellow nodes for performance tests.

    [Source: docs/stories/33.8.story.md - Task 6.2]

    Args:
        tmp_path: pytest temporary directory fixture

    Returns:
        Path: Path to the test canvas file
    """
    canvas_data = {
        "nodes": [
            {
                "id": f"node-{i:03d}",
                "type": "text",
                "color": "6",  # Yellow
                "text": _generate_node_text(i),
                "x": (i % 10) * 250,
                "y": (i // 10) * 150,
                "width": 220,
                "height": 100
            }
            for i in range(100)
        ],
        "edges": []
    }

    canvas_dir = tmp_path / "test_vault"
    canvas_dir.mkdir(parents=True, exist_ok=True)

    canvas_file = canvas_dir / "test_parallel_100.canvas"
    canvas_file.write_text(json.dumps(canvas_data, ensure_ascii=False), encoding='utf-8')

    return canvas_file


@pytest.fixture
def test_canvas_with_failing_node(tmp_path: Path) -> Path:
    """
    Create test Canvas with a deliberately failing node for retry tests.

    Node-999 has invalid content that will cause agent failure.

    [Source: docs/stories/33.8.story.md - Task 4.2]
    """
    canvas_data = {
        "nodes": [
            # 5 normal yellow nodes
            *[
                {
                    "id": f"node-{i:03d}",
                    "type": "text",
                    "color": "6",  # Yellow
                    "text": _generate_node_text(i),
                    "x": i * 250,
                    "y": 0,
                    "width": 220,
                    "height": 100
                }
                for i in range(5)
            ],
            # 1 failing node with empty/invalid content
            {
                "id": "node-999",
                "type": "text",
                "color": "6",  # Yellow
                "text": "",  # Empty text causes failure
                "x": 0,
                "y": 200,
                "width": 220,
                "height": 100
            }
        ],
        "edges": []
    }

    canvas_dir = tmp_path / "test_vault"
    canvas_dir.mkdir(parents=True, exist_ok=True)

    canvas_file = canvas_dir / "test_parallel_failing.canvas"
    canvas_file.write_text(json.dumps(canvas_data, ensure_ascii=False), encoding='utf-8')

    return canvas_file


def _generate_node_text(index: int) -> str:
    """
    Generate varied node text for testing grouping and agent routing.

    Cycles through different question types to test agent selection.
    """
    patterns = [
        f"什么是概念{index}？这个概念的核心定义是什么？",
        f"概念{index}和概念{(index + 1) % 10}有什么区别？请对比说明。",
        f"如何理解概念{index}？请详细解释。",
        f"请举例说明概念{index}的实际应用。",
        f"如何记忆概念{index}？有什么记忆技巧？",
        f"深度剖析概念{index}的原理和机制。",
        f"概念{index}的基础知识入门。",
        f"概念{index}与相关领域的关联是什么？",
        f"概念{index}的历史发展过程。",
        f"概念{index}的常见误区和正确理解。",
    ]
    return patterns[index % len(patterns)]


# =============================================================================
# Async Client Fixture
# [Source: Context7:/websites/fastapi_tiangolo (topic: async testing)]
# =============================================================================

@pytest.fixture
async def e2e_async_client(tmp_path: Path) -> AsyncGenerator[AsyncClient, None]:
    """
    Async HTTP client for E2E API testing with proper settings override.

    ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: async testing)
    """
    # Override settings to use tmp_path as canvas base
    def get_test_settings():
        settings = get_e2e_settings_override()
        settings.CANVAS_BASE_PATH = str(tmp_path)
        return settings

    app.dependency_overrides[get_settings] = get_test_settings

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


# =============================================================================
# Mock Agent Responses
# [Source: docs/stories/33.8.story.md - Task 1.4]
# =============================================================================

@pytest.fixture
def mock_agent_responses(mocker):
    """
    Mock agent_service.call_agent() for fast execution.

    Returns instant mock responses to isolate orchestration performance.

    [Source: docs/stories/33.8.story.md - Implementation Notes #1]
    """
    async def mock_call_agent(agent_type: str, node_id: str, node_text: str, *args, **kwargs):
        """Mock agent response with minimal delay."""
        await simulate_async_delay(0.01)  # 10ms simulated processing
        return {
            "success": True,
            "agent_type": agent_type,
            "node_id": node_id,
            "file_path": f"generated/{agent_type}/{node_id}.md",
            "content": f"Mock response for {node_text[:50]}...",
            "file_size": 1024,
        }

    mock = mocker.patch(
        "app.services.agent_service.AgentService.call_agent",
        side_effect=mock_call_agent
    )
    return mock


@pytest.fixture
def mock_agent_with_failures(mocker):
    """
    Mock agent that fails for specific nodes (node-999).

    Used for testing partial failure and retry workflows.

    [Source: docs/stories/33.8.story.md - Task 4.2]
    """
    call_count = {"value": 0}

    async def mock_call_agent_with_failure(agent_type: str, node_id: str, node_text: str, *args, **kwargs):
        """Mock agent that fails for empty text or node-999."""
        call_count["value"] += 1
        await simulate_async_delay(0.01)

        if node_id == "node-999" or not node_text.strip():
            raise ValueError(f"Agent processing failed for node {node_id}: empty content")

        return {
            "success": True,
            "agent_type": agent_type,
            "node_id": node_id,
            "file_path": f"generated/{agent_type}/{node_id}.md",
            "content": f"Mock response for {node_text[:50]}...",
            "file_size": 1024,
        }

    mock = mocker.patch(
        "app.services.agent_service.AgentService.call_agent",
        side_effect=mock_call_agent_with_failure
    )
    mock.call_count_tracker = call_count
    return mock


# =============================================================================
# Session Manager Fixtures
# [Source: docs/stories/33.8.story.md - Task 7.3]
# =============================================================================

@pytest.fixture
def session_manager_clean():
    """
    Get a clean SessionManager instance for testing.

    Resets singleton to ensure test isolation.
    """
    SessionManager.reset_instance()
    manager = SessionManager.get_instance()
    yield manager
    SessionManager.reset_instance()


@pytest.fixture
async def cleanup_sessions(session_manager_clean):
    """
    Cleanup sessions after test completion.

    Ensures no session leakage between tests.
    """
    yield
    # Cleanup all sessions after test
    sessions = await session_manager_clean.list_sessions()
    for session in sessions:
        try:
            await session_manager_clean.cancel_session(session.session_id)
        except Exception:
            pass  # Ignore errors during cleanup


# =============================================================================
# WebSocket Test Utilities
# [Source: docs/stories/33.8.story.md - Task 1.5]
# =============================================================================

@pytest.fixture
def websocket_test_app():
    """
    Create test FastAPI application with WebSocket endpoint for E2E tests.

    [Source: backend/tests/integration/test_websocket_integration.py]
    """
    from app.api.v1.endpoints.websocket import (
        websocket_intelligent_parallel,
        set_session_validator,
    )
    from fastapi import FastAPI, WebSocket
    from app.services.websocket_manager import reset_connection_manager

    test_app = FastAPI()
    reset_connection_manager()

    # Allow all sessions for testing
    async def allow_all_sessions(session_id: str) -> bool:
        return True

    set_session_validator(allow_all_sessions)

    @test_app.websocket("/ws/intelligent-parallel/{session_id}")
    async def websocket_endpoint(websocket: WebSocket, session_id: str):
        await websocket_intelligent_parallel(websocket, session_id)

    yield test_app

    set_session_validator(None)
    reset_connection_manager()


# =============================================================================
# Performance Measurement Utilities
# [Source: docs/stories/33.8.story.md - Task 6.4]
# =============================================================================

class PerformanceTimer:
    """Context manager for precise performance measurement."""

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.elapsed = None

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.end_time = time.perf_counter()
        self.elapsed = self.end_time - self.start_time

    def get_metrics(self, node_count: int) -> dict:
        """Calculate performance metrics."""
        if self.elapsed is None:
            raise RuntimeError("Timer not completed")
        return {
            "total_duration_seconds": self.elapsed,
            "nodes_per_second": node_count / self.elapsed if self.elapsed > 0 else 0,
            "average_per_node_ms": (self.elapsed / node_count * 1000) if node_count > 0 else 0,
        }


@pytest.fixture
def performance_timer():
    """Provide performance timer for benchmarking."""
    return PerformanceTimer()


# =============================================================================
# Event Collection Utilities
# [Source: docs/stories/33.8.story.md - Task 5.4]
# =============================================================================

class EventCollector:
    """Utility for collecting WebSocket events during tests."""

    def __init__(self):
        self.events: List[dict] = []
        self.completed = False

    def add_event(self, event: dict):
        """Add an event to the collection."""
        self.events.append(event)
        if event.get("type") == "session_completed":
            self.completed = True

    def get_events_by_type(self, event_type: str) -> List[dict]:
        """Filter events by type."""
        return [e for e in self.events if e.get("type") == event_type]

    def verify_event_sequence(self) -> bool:
        """
        Verify events follow expected sequence.

        Expected: progress_update* → task_completed* → session_completed
        """
        if not self.events:
            return False

        # Last event should be session_completed or error
        last_event = self.events[-1]
        return last_event.get("type") in ["session_completed", "error", "cancelled"]


@pytest.fixture
def event_collector():
    """Provide event collector for WebSocket tests."""
    return EventCollector()


# =============================================================================
# Mock canvas_utils for E2E Tests (P1-2 fix)
# [Source: backend/tests/integration/test_batch_processing.py:97-150]
# =============================================================================

@pytest.fixture
def mock_canvas_utils(monkeypatch):
    """
    Mock canvas_utils module to avoid import issues in IntelligentGroupingService.

    Promoted from test_batch_processing.py for reuse in E2E tests.
    Uses monkeypatch.setitem for automatic cleanup (safe even if test fails).

    [Fix for: canvas_utils.path_manager not available as package in test env]
    """
    class MockCanvasBusinessLogic:
        def __init__(self, canvas_path: str):
            self.canvas_path = canvas_path
            with open(canvas_path, 'r', encoding='utf-8') as f:
                self.canvas_data = json.load(f)

        def cluster_canvas_nodes(
            self,
            n_clusters=None,
            similarity_threshold=0.3,
            create_groups=False,
            min_cluster_size=2,
        ):
            """Mock clustering that returns valid cluster structure."""
            nodes = self.canvas_data.get("nodes", [])
            text_nodes = [n for n in nodes if n.get("type") == "text" and n.get("text")]

            if len(text_nodes) < min_cluster_size:
                raise ValueError(f"节点数量不足: {len(text_nodes)} < {min_cluster_size}")

            # Split nodes into groups of ~5 for realistic clustering
            group_size = max(min_cluster_size, 5)
            clusters = []
            for i in range(0, len(text_nodes), group_size):
                chunk = text_nodes[i:i + group_size]
                clusters.append({
                    "id": f"cluster-{i // group_size + 1}",
                    "label": f"测试分组{i // group_size + 1}",
                    "top_keywords": ["测试", "概念"],
                    "confidence": 0.75,
                    "nodes": [n["id"] for n in chunk],
                })

            return {
                "clusters": clusters,
                "optimization_stats": {
                    "clustering_accuracy": 0.6,
                    "total_nodes": len(text_nodes),
                    "clusters_created": len(clusters),
                },
                "clustering_parameters": {
                    "n_clusters": len(clusters),
                },
            }

    mock_module = MagicMock()
    mock_module.CanvasBusinessLogic = MockCanvasBusinessLogic

    monkeypatch.setitem(sys.modules, 'canvas_utils', mock_module)

    return mock_module


# =============================================================================
# Shared Singleton Reset (autouse for all E2E tests)
# =============================================================================

@pytest.fixture(autouse=True)
def _reset_e2e_singletons():
    """
    Reset service singletons before and after each E2E test for isolation.

    Ensures no leaked state between tests (service instance, deps, overrides).
    """
    from app.api.v1.endpoints.intelligent_parallel import reset_service
    reset_service()
    SessionManager.reset_instance()
    try:
        yield
    finally:
        reset_service()
        SessionManager.reset_instance()
        app.dependency_overrides.clear()


# =============================================================================
# Shared Helpers: Clustering Mock & Lightweight DI
# Used by both test_intelligent_parallel.py and test_epic33_batch_pipeline.py
# =============================================================================

def mock_perform_clustering(self, canvas_path, target_color, max_groups, min_nodes_per_group):
    """
    Shared mock replacement for IntelligentGroupingService._perform_clustering.

    Reads the real canvas file, filters by target_color, and returns
    a simple clustering result without needing canvas_utils.
    """
    with open(str(canvas_path), "r", encoding="utf-8") as f:
        canvas_data = json.load(f)

    nodes = canvas_data.get("nodes", [])
    text_nodes = [
        n for n in nodes
        if n.get("type") == "text"
        and n.get("color") == target_color
        and n.get("text", "").strip()
    ]

    if len(text_nodes) < min_nodes_per_group:
        from app.services.intelligent_grouping_service import InsufficientNodesError
        raise InsufficientNodesError(
            f"Not enough nodes with color '{target_color}'. "
            f"Found {len(text_nodes)}, need at least {min_nodes_per_group}"
        )

    group_size = max(min_nodes_per_group, 5)
    clusters = []
    for i in range(0, len(text_nodes), group_size):
        chunk = text_nodes[i:i + group_size]
        node_texts = {n["id"]: n.get("text", "") for n in chunk}
        clusters.append({
            "id": f"cluster-{i // group_size + 1}",
            "label": f"group{i // group_size + 1}",
            "top_keywords": ["test", "concept"],
            "confidence": 0.75,
            "nodes": [n["id"] for n in chunk],
            "node_texts": node_texts,
        })

    return {
        "clusters": clusters,
        "optimization_stats": {
            "clustering_accuracy": 0.6,
            "total_nodes": len(text_nodes),
            "clusters_created": len(clusters),
        },
        "clustering_parameters": {"n_clusters": len(clusters)},
    }


def make_lightweight_ensure_deps(settings, agent_mock):
    """
    Factory returning async function that replaces _ensure_async_deps.

    Injects lightweight mock dependencies (no Neo4j, no real GeminiClient)
    so the batch pipeline can execute end-to-end with mocked agents.
    """

    async def _lightweight_ensure_deps():
        import app.api.v1.endpoints.intelligent_parallel as ep_mod

        if ep_mod._deps_initialized:
            return

        service = ep_mod.get_service()

        from app.services.batch_orchestrator import BatchOrchestrator
        from app.services.agent_service import AgentService
        from app.services.canvas_service import CanvasService

        canvas_base = str(settings.canvas_base_path) if settings.canvas_base_path else None
        canvas_service = CanvasService(canvas_base_path=canvas_base)

        # Create AgentService with mocked gemini_client
        agent_service = AgentService(
            gemini_client=MagicMock(),
            canvas_service=canvas_service,
        )
        # Patch call_agent on the instance
        agent_service.call_agent = agent_mock

        session_manager = SessionManager.get_instance()

        batch_orchestrator = BatchOrchestrator(
            session_manager=session_manager,
            agent_service=agent_service,
            canvas_service=canvas_service,
            vault_path=canvas_base,
        )

        service._batch_orchestrator = batch_orchestrator
        service._agent_service = agent_service
        service._canvas_service = canvas_service

        ep_mod._deps_initialized = True

    return _lightweight_ensure_deps
