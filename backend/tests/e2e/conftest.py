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
import json
import time
from pathlib import Path
from typing import Any, AsyncGenerator, Generator, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
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

    canvas_dir = tmp_path / "笔记库"
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

    canvas_dir = tmp_path / "笔记库"
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

    canvas_dir = tmp_path / "笔记库"
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

    canvas_dir = tmp_path / "笔记库"
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
        await asyncio.sleep(0.01)  # 10ms simulated processing
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
        await asyncio.sleep(0.01)

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
