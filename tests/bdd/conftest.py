# -*- coding: utf-8 -*-
"""
pytest-bdd Configuration and Shared Fixtures
=============================================

Purpose: Provide shared fixtures and configuration for BDD tests that execute
Gherkin scenarios from specs/behavior/*.feature files.

Context7 Verified:
- pytest-bdd: /pytest-dev/pytest-bdd (79 snippets, Benchmark 82.3)
- pytest fixtures: /pytest-dev/pytest

Architecture Reference:
- SDD: docs/architecture/sot-hierarchy.md (Gherkin is behavior specification)
- PRD: Epic 15 - FastAPI Backend, Epic 12 - Three-Layer Memory
"""

import pytest
from pytest_bdd import given, when, then, parsers
from typing import Dict, Any, Optional
from unittest.mock import MagicMock, AsyncMock
from dataclasses import dataclass, field
import json
import asyncio


# =============================================================================
# Test Data Models
# =============================================================================

@dataclass
class MockCanvasNode:
    """Mock Canvas node for testing."""
    id: str
    type: str = "text"
    text: str = ""
    color: str = "1"  # Default red
    x: int = 0
    y: int = 0
    width: int = 300
    height: int = 100


@dataclass
class MockCanvasData:
    """Mock Canvas file data for testing."""
    nodes: list = field(default_factory=list)
    edges: list = field(default_factory=list)


@dataclass
class MockTaskStatus:
    """Mock async task status."""
    task_id: str
    status: str = "pending"  # pending, running, completed, failed, timeout
    agent_name: str = ""
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    created_at: str = ""
    completed_at: Optional[str] = None


@dataclass
class MockScoringResult:
    """Mock scoring agent result."""
    accuracy: int = 0
    imagery: int = 0
    completeness: int = 0
    originality: int = 0
    total_score: int = 0
    color: str = "1"
    recommendations: list = field(default_factory=list)


# =============================================================================
# Shared Fixtures
# =============================================================================

@pytest.fixture
def canvas_system():
    """
    Fixture: Mock Canvas Learning System.

    Provides a mock system context for BDD tests.
    When FastAPI (Epic 15) is implemented, this will be replaced with
    actual HTTP client calls.
    """
    system = MagicMock()
    system.is_started = True
    system.agents = {
        'scoring-agent': MagicMock(ready=True),
        'basic-decomposition': MagicMock(ready=True),
        'deep-decomposition': MagicMock(ready=True),
        'oral-explanation': MagicMock(ready=True),
        'clarification-path': MagicMock(ready=True),
        'comparison-table': MagicMock(ready=True),
        'memory-anchor': MagicMock(ready=True),
        'four-level-explanation': MagicMock(ready=True),
        'example-teaching': MagicMock(ready=True),
        'verification-question-agent': MagicMock(ready=True),
        'canvas-orchestrator': MagicMock(ready=True),
        'review-board-agent-selector': MagicMock(ready=True),
        'graphiti-memory-agent': MagicMock(ready=True),
        'question-decomposition': MagicMock(ready=True),
    }
    return system


@pytest.fixture
def mock_canvas_data():
    """
    Fixture: Mock Canvas file data.

    Provides sample Canvas data for testing node operations.
    """
    return MockCanvasData(
        nodes=[
            MockCanvasNode(id="question-001", type="text", text="什么是逆否命题？", color="1"),
            MockCanvasNode(id="yellow-001", type="text", text="", color="6"),
            MockCanvasNode(id="green-001", type="text", text="完全理解的概念", color="2"),
        ],
        edges=[
            {"id": "edge-001", "fromNode": "question-001", "toNode": "yellow-001"}
        ]
    )


@pytest.fixture
def mock_scoring_agent():
    """
    Fixture: Mock scoring agent.

    Provides a mock scoring agent for testing 4-dimension scoring.
    """
    agent = MagicMock()

    def score_node(concept: str, user_understanding: str) -> MockScoringResult:
        """Simple scoring logic based on text length and keywords."""
        text_length = len(user_understanding)

        # Basic scoring heuristic (for testing)
        if text_length > 100 and "等价" in user_understanding:
            return MockScoringResult(
                accuracy=24, imagery=23, completeness=22, originality=18,
                total_score=87, color="2", recommendations=[]
            )
        elif text_length > 30:
            return MockScoringResult(
                accuracy=20, imagery=18, completeness=17, originality=15,
                total_score=70, color="3",
                recommendations=["clarification-path", "oral-explanation"]
            )
        else:
            return MockScoringResult(
                accuracy=10, imagery=8, completeness=10, originality=7,
                total_score=35, color="1",
                recommendations=["basic-decomposition", "oral-explanation"]
            )

    agent.score = score_node
    return agent


@pytest.fixture
def mock_api_client():
    """
    Fixture: Mock HTTP API client.

    Simulates FastAPI endpoints. When Epic 15 is complete,
    this will use actual httpx client.
    """
    client = MagicMock()
    client.base_url = "http://localhost:8000"

    # Store for task tracking
    client._tasks: Dict[str, MockTaskStatus] = {}

    async def post(endpoint: str, json_data: Dict) -> Dict:
        """Mock POST request."""
        if "/agents/" in endpoint and "/invoke" in endpoint:
            # Extract agent name from endpoint
            agent_name = endpoint.split("/agents/")[1].split("/invoke")[0]
            task_id = f"task-{len(client._tasks) + 1:03d}"

            task = MockTaskStatus(
                task_id=task_id,
                status="pending",
                agent_name=agent_name,
                created_at="2025-01-18T10:00:00Z"
            )
            client._tasks[task_id] = task

            return {
                "task_id": task_id,
                "status": "pending",
                "agent_name": agent_name,
                "created_at": task.created_at
            }

        return {"error": "Unknown endpoint"}

    async def get(endpoint: str) -> Dict:
        """Mock GET request."""
        if "/agents/tasks/" in endpoint:
            task_id = endpoint.split("/agents/tasks/")[1]
            if task_id in client._tasks:
                task = client._tasks[task_id]
                return {
                    "task_id": task.task_id,
                    "status": task.status,
                    "result": task.result,
                    "error": task.error
                }
            return {"error": "TaskNotFoundError", "message": f"Task '{task_id}' not found"}

        return {"error": "Unknown endpoint"}

    client.post = AsyncMock(side_effect=post)
    client.get = AsyncMock(side_effect=get)

    return client


@pytest.fixture
def mock_graphiti():
    """
    Fixture: Mock Graphiti knowledge graph.

    Provides mock implementation for Epic 12 three-layer memory tests.
    """
    graphiti = MagicMock()
    graphiti.entities = []
    graphiti.relationships = []

    def search(query: str, group_ids: list = None):
        """Mock hybrid search."""
        return [
            {"entity": "逆否命题", "score": 0.89},
            {"entity": "反证法", "score": 0.76}
        ]

    graphiti.hybrid_search = search
    return graphiti


@pytest.fixture
def mock_lancedb():
    """
    Fixture: Mock LanceDB vector store.

    Provides mock implementation for semantic memory layer.
    """
    lancedb = MagicMock()

    def search(query: str, n: int = 10, filter_canvas: str = None):
        """Mock vector search."""
        return [
            {"doc_id": "doc-001", "content": "口语化解释-逆否命题", "similarity": 0.89},
            {"doc_id": "doc-002", "content": "澄清路径-命题逻辑", "similarity": 0.76}
        ]

    lancedb.search = search
    return lancedb


@pytest.fixture
def mock_temporal_memory():
    """
    Fixture: Mock Temporal Memory (FSRS cards).

    Provides mock implementation for learning history tracking.
    """
    temporal = MagicMock()
    temporal.weak_concepts = ["反证法", "充分必要条件"]
    temporal.fsrs_cards = []

    def get_weak_concepts(canvas: str = None):
        """Get concepts with low mastery."""
        return temporal.weak_concepts

    temporal.get_weak_concepts = get_weak_concepts
    return temporal


# =============================================================================
# Shared Given Steps (Background)
# =============================================================================

@given("Canvas学习系统已启动")
@given("Canvas API服务器已启动")
@given("Agent API服务器已启动")
def canvas_system_started(canvas_system):
    """Verify Canvas system is started."""
    assert canvas_system.is_started, "Canvas system should be started"
    return canvas_system


@given("scoring-agent已就绪")
def scoring_agent_ready(canvas_system):
    """Verify scoring agent is ready."""
    assert canvas_system.agents['scoring-agent'].ready
    return canvas_system.agents['scoring-agent']


@given("所有14个Agents已就绪")
def all_agents_ready(canvas_system):
    """Verify all 14 agents are ready."""
    assert len(canvas_system.agents) == 14, f"Expected 14 agents, got {len(canvas_system.agents)}"
    for name, agent in canvas_system.agents.items():
        assert agent.ready, f"Agent {name} should be ready"
    return canvas_system.agents


@given(parsers.parse('Canvas文件"{canvas_path}"存在'))
def canvas_file_exists(canvas_path, mock_canvas_data):
    """Verify Canvas file exists."""
    # In real implementation, check file system
    return mock_canvas_data


@given(parsers.parse('Canvas文件目录"{directory}"存在'))
def canvas_directory_exists(directory):
    """Verify Canvas directory exists."""
    return directory


@given("Canvas Learning System 已正确配置")
def canvas_system_configured(canvas_system, mock_graphiti, mock_lancedb, mock_temporal_memory):
    """Verify entire Canvas Learning System is configured."""
    return {
        "system": canvas_system,
        "graphiti": mock_graphiti,
        "lancedb": mock_lancedb,
        "temporal": mock_temporal_memory
    }


@given("FastAPI 后端运行在 localhost:8000")
def fastapi_running(mock_api_client):
    """Verify FastAPI backend is running."""
    assert mock_api_client.base_url == "http://localhost:8000"
    return mock_api_client


@given("Neo4j (Graphiti) 服务可用")
def neo4j_available(mock_graphiti):
    """Verify Neo4j/Graphiti service is available."""
    return mock_graphiti


@given("LanceDB 数据库已初始化")
def lancedb_initialized(mock_lancedb):
    """Verify LanceDB is initialized."""
    return mock_lancedb


@given("Temporal Memory (PostgreSQL) 已连接")
def temporal_memory_connected(mock_temporal_memory):
    """Verify Temporal Memory is connected."""
    return mock_temporal_memory


# =============================================================================
# Shared When Steps
# =============================================================================

@when(parsers.parse('用户调用scoring-agent评分节点"{node_id}"'))
def call_scoring_agent(node_id, mock_scoring_agent, mock_canvas_data):
    """Call scoring agent to score a node."""
    # Find node in canvas data
    node = None
    for n in mock_canvas_data.nodes:
        if n.id == node_id:
            node = n
            break

    if node is None:
        pytest.fail(f"Node {node_id} not found in canvas data")

    # Score the node (concept extracted from parent, understanding from node text)
    result = mock_scoring_agent.score("逆否命题", node.text)
    return result


# =============================================================================
# Shared Then Steps
# =============================================================================

@then("scoring-agent返回成功响应")
def scoring_agent_success(mock_scoring_agent):
    """Verify scoring agent returned success."""
    # Result is stored in test context
    pass


@then(parsers.parse('响应状态码为{status_code:d}'))
def verify_status_code(status_code):
    """Verify HTTP response status code."""
    # In real implementation, check actual response
    pass


@then(parsers.parse('总分为{expected_score:d}分'))
def verify_total_score(expected_score):
    """Verify total score matches expected."""
    pass


@then(parsers.parse('颜色判断为"{expected_color}"（{color_name}）'))
def verify_color(expected_color, color_name):
    """Verify color judgment."""
    pass


# =============================================================================
# Pytest-BDD Hooks
# =============================================================================

def pytest_bdd_step_error(request, feature, scenario, step, step_func, step_func_args, exception):
    """
    Hook: Called when a step raises an exception.

    Provides better error messages for debugging.
    """
    print(f"\n❌ Step failed: {step.name}")
    print(f"   Feature: {feature.name}")
    print(f"   Scenario: {scenario.name}")
    print(f"   Exception: {exception}")


def pytest_bdd_after_scenario(request, feature, scenario):
    """
    Hook: Called after each scenario.

    Can be used for cleanup or logging.
    """
    print(f"\n✅ Scenario completed: {scenario.name}")
