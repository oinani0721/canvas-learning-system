# Story 36.3: Canvas Edge Sync to Neo4j - Integration Tests
"""
Integration tests for Canvas Edge automatic sync to Neo4j.

These tests require a running Neo4j instance.
Skip with: pytest -m "not integration" or set NEO4J_MOCK=true

Tests verify:
- AC-5: Edge relationship appears in Neo4j after Canvas add_edge()
- AC-4: Canvas operation succeeds even if Neo4j is unavailable

[Source: docs/stories/36.3.story.md#Task-4.3-4.4]
"""
import asyncio
import json
import os

import pytest

from tests.conftest import wait_for_condition

# Skip integration tests if Neo4j is mocked
pytestmark = pytest.mark.skipif(
    os.getenv("NEO4J_MOCK", "true").lower() == "true",
    reason="Integration tests require real Neo4j (set NEO4J_MOCK=false)"
)


@pytest.fixture
async def neo4j_client():
    """Get real Neo4j client for integration tests."""
    from app.clients.neo4j_client import get_neo4j_client
    client = get_neo4j_client()
    yield client
    # Cleanup: Close connection after tests
    await client.close()


@pytest.fixture
async def memory_service(neo4j_client):
    """Create MemoryService with real Neo4j client."""
    from app.services.memory_service import MemoryService
    service = MemoryService(neo4j_client=neo4j_client)
    yield service


@pytest.fixture
def canvas_service(memory_service, tmp_path):
    """Create CanvasService with real memory service."""
    from app.services.canvas_service import CanvasService
    return CanvasService(
        canvas_base_path=str(tmp_path),
        memory_client=memory_service
    )


@pytest.fixture
def sample_canvas_file(tmp_path):
    """Create a sample canvas file for testing."""
    canvas_data = {
        "nodes": [
            {"id": "int-node-1", "type": "text", "text": "Integration Test A", "x": 0, "y": 0},
            {"id": "int-node-2", "type": "text", "text": "Integration Test B", "x": 200, "y": 0}
        ],
        "edges": []
    }
    canvas_path = tmp_path / "integration_test.canvas"
    canvas_path.write_text(json.dumps(canvas_data))
    return canvas_path


@pytest.mark.integration
@pytest.mark.asyncio
async def test_edge_appears_in_neo4j_after_add_edge(
    canvas_service, memory_service, sample_canvas_file, neo4j_client
):
    """
    AC-5: Verify edge relationship created in Neo4j after Canvas add_edge().

    This is the primary integration test verifying end-to-end functionality.
    """
    # Act: Add edge via Canvas service
    edge_result = await canvas_service.add_edge(
        canvas_name="integration_test",
        edge_data={
            "fromNode": "int-node-1",
            "toNode": "int-node-2",
            "label": "integration_test_edge"
        }
    )

    # Wait for background sync to complete by polling Neo4j
    edge_id = edge_result["id"]

    async def _edge_in_neo4j():
        query = """
        MATCH (from:Node {id: $fromNodeId})-[r:CONNECTS_TO {edge_id: $edgeId}]->(to:Node {id: $toNodeId})
        RETURN r.edge_id as edge_id, r.label as label
        """
        rows = await neo4j_client.run_query(
            query,
            fromNodeId="int-node-1",
            toNodeId="int-node-2",
            edgeId=edge_id,
        )
        return rows if len(rows) >= 1 else None

    results = await wait_for_condition(
        _edge_in_neo4j,
        timeout=5.0,
        description="Edge relationship appears in Neo4j",
    )

    assert len(results) == 1, f"Expected 1 edge in Neo4j, found {len(results)}"
    assert results[0]["edge_id"] == edge_id
    assert results[0]["label"] == "integration_test_edge"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_canvas_operation_succeeds_without_neo4j(tmp_path):
    """
    AC-4: Verify Canvas add_edge() succeeds even when Neo4j is unavailable.

    Simulates Neo4j being down by using a service without neo4j client.
    """
    from app.services.canvas_service import CanvasService
    from unittest.mock import MagicMock

    # Create memory client with broken Neo4j
    mock_memory = MagicMock()
    mock_memory.neo4j = None  # Simulate Neo4j unavailable
    mock_memory.record_temporal_event = MagicMock()

    # Create canvas file
    canvas_data = {
        "nodes": [
            {"id": "fail-node-1", "type": "text", "text": "Fail Test A", "x": 0, "y": 0},
            {"id": "fail-node-2", "type": "text", "text": "Fail Test B", "x": 100, "y": 0}
        ],
        "edges": []
    }
    canvas_path = tmp_path / "fail_test.canvas"
    canvas_path.write_text(json.dumps(canvas_data))

    # Create service with "broken" Neo4j
    service = CanvasService(
        canvas_base_path=str(tmp_path),
        memory_client=mock_memory
    )

    # Act: add_edge should succeed despite Neo4j being unavailable
    result = await service.add_edge(
        canvas_name="fail_test",
        edge_data={"fromNode": "fail-node-1", "toNode": "fail-node-2"}
    )

    # Assert: Edge was created in Canvas file
    assert result["fromNode"] == "fail-node-1"
    assert result["toNode"] == "fail-node-2"
    assert "id" in result

    # Verify edge saved to file
    updated_canvas = json.loads(canvas_path.read_text())
    assert len(updated_canvas["edges"]) == 1
    assert updated_canvas["edges"][0]["id"] == result["id"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_multiple_edges_sync_concurrently(
    canvas_service, memory_service, sample_canvas_file, neo4j_client
):
    """
    Verify multiple edges can be synced concurrently without issues.
    """
    # Add more nodes to canvas
    canvas_data = json.loads(sample_canvas_file.read_text())
    canvas_data["nodes"].extend([
        {"id": "int-node-3", "type": "text", "text": "Node C", "x": 400, "y": 0},
        {"id": "int-node-4", "type": "text", "text": "Node D", "x": 600, "y": 0}
    ])
    sample_canvas_file.write_text(json.dumps(canvas_data))

    # Act: Add multiple edges concurrently
    edge_tasks = [
        canvas_service.add_edge(
            canvas_name="integration_test",
            edge_data={"fromNode": "int-node-1", "toNode": "int-node-3", "label": "edge_1"}
        ),
        canvas_service.add_edge(
            canvas_name="integration_test",
            edge_data={"fromNode": "int-node-2", "toNode": "int-node-4", "label": "edge_2"}
        ),
        canvas_service.add_edge(
            canvas_name="integration_test",
            edge_data={"fromNode": "int-node-3", "toNode": "int-node-4", "label": "edge_3"}
        )
    ]

    results = await asyncio.gather(*edge_tasks)

    # Wait for all 3 edges to appear in Canvas file
    await wait_for_condition(
        lambda: len(json.loads(sample_canvas_file.read_text()).get("edges", [])) >= 3,
        timeout=5.0,
        description="All 3 edges written to canvas file",
    )

    # Assert: All edges created in Canvas
    assert len(results) == 3
    for result in results:
        assert "id" in result
        assert "fromNode" in result
        assert "toNode" in result

    # Verify edges in Canvas file
    updated_canvas = json.loads(sample_canvas_file.read_text())
    assert len(updated_canvas["edges"]) == 3


@pytest.mark.integration
@pytest.mark.asyncio
async def test_edge_sync_with_chinese_canvas_path(
    memory_service, tmp_path, neo4j_client
):
    """
    Verify edge sync works with Chinese characters in canvas path.
    """
    from app.services.canvas_service import CanvasService

    # Create canvas with Chinese name
    canvas_data = {
        "nodes": [
            {"id": "cn-node-1", "type": "text", "text": "概念A", "x": 0, "y": 0},
            {"id": "cn-node-2", "type": "text", "text": "概念B", "x": 100, "y": 0}
        ],
        "edges": []
    }
    # Create subdirectory with Chinese name
    chinese_dir = tmp_path / "笔记库" / "离散数学"
    chinese_dir.mkdir(parents=True, exist_ok=True)
    canvas_path = chinese_dir / "测试.canvas"
    canvas_path.write_text(json.dumps(canvas_data), encoding="utf-8")

    service = CanvasService(
        canvas_base_path=str(tmp_path),
        memory_client=memory_service
    )

    # Act: Add edge to Chinese-named canvas
    result = await service.add_edge(
        canvas_name="笔记库/离散数学/测试",
        edge_data={"fromNode": "cn-node-1", "toNode": "cn-node-2", "label": "关系"}
    )

    # Wait for edge to be written to canvas file
    await wait_for_condition(
        lambda: len(json.loads(canvas_path.read_text(encoding="utf-8")).get("edges", [])) >= 1,
        timeout=5.0,
        description="Edge written to Chinese-named canvas file",
    )

    # Assert: Edge created successfully
    assert result["fromNode"] == "cn-node-1"
    assert result["toNode"] == "cn-node-2"
    assert result.get("label") == "关系"
