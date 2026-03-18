# Story 4.4: Edge Dialog Fallback - Dual-Write Partial Failure Tests
# [Source: _bmad-output/implementation-artifacts/4-4-edge-dialog-fallback.md#Task 9.3]
"""
Unit tests for record_edge_rationale dual-write partial failure handling.

Verifies:
  - AC-4: Graphiti success + LanceDB fail => 207 Multi-Status
  - AC-4: LanceDB success + Graphiti fail => 207 Multi-Status
  - AC-4: Both fail => 500
  - AC-4: Both succeed => 200
  - AC-3: Successful part preserved (not rolled back)
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """FastAPI TestClient for edge rationale endpoint."""
    from app.main import app

    return TestClient(app)


@pytest.fixture
def valid_rationale_payload():
    """Minimal valid EdgeRationaleCreate payload."""
    return {
        "edge_id": "edge-test-001",
        "source_node_id": "node-a",
        "target_node_id": "node-b",
        "source_concept": "Concept A",
        "target_concept": "Concept B",
        "relation_type": "is prerequisite for",
        "rationale_text": "A must be understood before B because of X",
        "confidence": 0.85,
        "strategies_applied": ["EI", "SE"],
        "questioning_rounds": 3,
        "explanation_depth_score": 4,
    }


def _ws(success, error=None):
    """Helper: create WriteStatus instance."""
    from app.models.edge_rationale import WriteStatus

    return WriteStatus(success=success, error=error)


def test_both_writes_succeed_returns_200(client, valid_rationale_payload):
    """When both Graphiti and LanceDB writes succeed, return 200."""
    with (
        patch(
            "app.api.v1.endpoints.edges._write_graphiti",
            new_callable=AsyncMock,
            return_value=_ws(True),
        ),
        patch(
            "app.api.v1.endpoints.edges._write_lancedb",
            new_callable=AsyncMock,
            return_value=_ws(True),
        ),
    ):
        resp = client.post(
            "/api/v1/edges/record-rationale",
            json=valid_rationale_payload,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["graphiti_status"]["success"] is True
        assert body["lancedb_status"]["success"] is True
        assert body["edge_id"] == "edge-test-001"
        assert body["relation_type"] == "is prerequisite for"
        assert "record_id" in body


def test_graphiti_ok_lancedb_fail_returns_207(client, valid_rationale_payload):
    """When Graphiti succeeds but LanceDB fails, return 207 Multi-Status."""
    with (
        patch(
            "app.api.v1.endpoints.edges._write_graphiti",
            new_callable=AsyncMock,
            return_value=_ws(True),
        ),
        patch(
            "app.api.v1.endpoints.edges._write_lancedb",
            new_callable=AsyncMock,
            return_value=_ws(False, "LanceDB connection timeout"),
        ),
    ):
        resp = client.post(
            "/api/v1/edges/record-rationale",
            json=valid_rationale_payload,
        )
        assert resp.status_code == 207
        body = resp.json()
        assert body["graphiti_status"]["success"] is True
        assert body["lancedb_status"]["success"] is False
        assert body["lancedb_status"]["error"] == "LanceDB connection timeout"
        assert "record_id" in body


def test_lancedb_ok_graphiti_fail_returns_207(client, valid_rationale_payload):
    """When LanceDB succeeds but Graphiti fails, return 207 Multi-Status."""
    with (
        patch(
            "app.api.v1.endpoints.edges._write_graphiti",
            new_callable=AsyncMock,
            return_value=_ws(False, "Neo4j client not available"),
        ),
        patch(
            "app.api.v1.endpoints.edges._write_lancedb",
            new_callable=AsyncMock,
            return_value=_ws(True),
        ),
    ):
        resp = client.post(
            "/api/v1/edges/record-rationale",
            json=valid_rationale_payload,
        )
        assert resp.status_code == 207
        body = resp.json()
        assert body["graphiti_status"]["success"] is False
        assert body["graphiti_status"]["error"] == "Neo4j client not available"
        assert body["lancedb_status"]["success"] is True
        assert "record_id" in body


def test_both_writes_fail_returns_500(client, valid_rationale_payload):
    """When both Graphiti and LanceDB fail, return 500."""
    with (
        patch(
            "app.api.v1.endpoints.edges._write_graphiti",
            new_callable=AsyncMock,
            return_value=_ws(False, "Neo4j down"),
        ),
        patch(
            "app.api.v1.endpoints.edges._write_lancedb",
            new_callable=AsyncMock,
            return_value=_ws(False, "LanceDB disk full"),
        ),
    ):
        resp = client.post(
            "/api/v1/edges/record-rationale",
            json=valid_rationale_payload,
        )
        assert resp.status_code == 500
        body = resp.json()
        assert body["graphiti_status"]["success"] is False
        assert body["lancedb_status"]["success"] is False


def test_graphiti_exception_does_not_block_lancedb(client, valid_rationale_payload):
    """Graphiti failure should not prevent LanceDB write from completing."""
    with (
        patch(
            "app.api.v1.endpoints.edges._write_graphiti",
            new_callable=AsyncMock,
            return_value=_ws(False, "ConnectionRefusedError"),
        ) as stub_g,
        patch(
            "app.api.v1.endpoints.edges._write_lancedb",
            new_callable=AsyncMock,
            return_value=_ws(True),
        ) as stub_l,
    ):
        resp = client.post(
            "/api/v1/edges/record-rationale",
            json=valid_rationale_payload,
        )
        assert resp.status_code == 207
        body = resp.json()
        assert body["lancedb_status"]["success"] is True
        stub_g.assert_called_once()
        stub_l.assert_called_once()


def test_lancedb_exception_does_not_block_graphiti(client, valid_rationale_payload):
    """LanceDB failure should not prevent Graphiti write from completing."""
    with (
        patch(
            "app.api.v1.endpoints.edges._write_graphiti",
            new_callable=AsyncMock,
            return_value=_ws(True),
        ) as stub_g,
        patch(
            "app.api.v1.endpoints.edges._write_lancedb",
            new_callable=AsyncMock,
            return_value=_ws(False, "ImportError: lancedb not installed"),
        ) as stub_l,
    ):
        resp = client.post(
            "/api/v1/edges/record-rationale",
            json=valid_rationale_payload,
        )
        assert resp.status_code == 207
        body = resp.json()
        assert body["graphiti_status"]["success"] is True
        stub_g.assert_called_once()
        stub_l.assert_called_once()


def test_partial_failure_includes_error_details(client, valid_rationale_payload):
    """207 response includes specific error details for each failed write."""
    with (
        patch(
            "app.api.v1.endpoints.edges._write_graphiti",
            new_callable=AsyncMock,
            return_value=_ws(True),
        ),
        patch(
            "app.api.v1.endpoints.edges._write_lancedb",
            new_callable=AsyncMock,
            return_value=_ws(False, "Table edge_rationales locked by concurrent writer"),
        ),
    ):
        resp = client.post(
            "/api/v1/edges/record-rationale",
            json=valid_rationale_payload,
        )
        assert resp.status_code == 207
        body = resp.json()
        assert "locked" in body["lancedb_status"]["error"]
        assert "timestamp" in body


def test_strategy_fields_accepted(client, valid_rationale_payload):
    """Verify strategies_applied, questioning_rounds, explanation_depth_score
    are accepted in the request and passed to the write functions."""
    with (
        patch(
            "app.api.v1.endpoints.edges._write_graphiti",
            new_callable=AsyncMock,
            return_value=_ws(True),
        ) as stub_g,
        patch(
            "app.api.v1.endpoints.edges._write_lancedb",
            new_callable=AsyncMock,
            return_value=_ws(True),
        ),
    ):
        resp = client.post(
            "/api/v1/edges/record-rationale",
            json=valid_rationale_payload,
        )
        assert resp.status_code == 200
        call_args = stub_g.call_args
        rationale_arg = call_args[0][0]
        assert rationale_arg.strategies_applied == ["EI", "SE"]
        assert rationale_arg.questioning_rounds == 3
        assert rationale_arg.explanation_depth_score == 4


def test_strategy_fields_defaults(client):
    """Verify strategy fields use defaults when not provided."""
    minimal_payload = {
        "edge_id": "edge-min-001",
        "source_node_id": "node-a",
        "target_node_id": "node-b",
        "relation_type": "related",
        "rationale_text": "They are related",
        "confidence": 0.5,
    }
    with (
        patch(
            "app.api.v1.endpoints.edges._write_graphiti",
            new_callable=AsyncMock,
            return_value=_ws(True),
        ) as stub_g,
        patch(
            "app.api.v1.endpoints.edges._write_lancedb",
            new_callable=AsyncMock,
            return_value=_ws(True),
        ),
    ):
        resp = client.post(
            "/api/v1/edges/record-rationale",
            json=minimal_payload,
        )
        assert resp.status_code == 200
        call_args = stub_g.call_args
        rationale_arg = call_args[0][0]
        assert rationale_arg.strategies_applied == ["EI", "SE"]
        assert rationale_arg.questioning_rounds == 0
        assert rationale_arg.explanation_depth_score == 0


def test_response_model_fully_successful():
    """EdgeRationaleResponse.fully_successful is True when both succeed."""
    from app.models.edge_rationale import EdgeRationaleResponse, WriteStatus

    resp = EdgeRationaleResponse(
        record_id="r1",
        edge_id="e1",
        relation_type="test",
        graphiti_status=WriteStatus(success=True),
        lancedb_status=WriteStatus(success=True),
    )
    assert resp.fully_successful is True
    assert resp.partially_successful is False


def test_response_model_partially_successful():
    """EdgeRationaleResponse.partially_successful is True when one fails."""
    from app.models.edge_rationale import EdgeRationaleResponse, WriteStatus

    resp = EdgeRationaleResponse(
        record_id="r1",
        edge_id="e1",
        relation_type="test",
        graphiti_status=WriteStatus(success=True),
        lancedb_status=WriteStatus(success=False, error="fail"),
    )
    assert resp.fully_successful is False
    assert resp.partially_successful is True


def test_response_model_both_failed():
    """Both failed => not fully_successful, not partially_successful."""
    from app.models.edge_rationale import EdgeRationaleResponse, WriteStatus

    resp = EdgeRationaleResponse(
        record_id="r1",
        edge_id="e1",
        relation_type="test",
        graphiti_status=WriteStatus(success=False, error="g-fail"),
        lancedb_status=WriteStatus(success=False, error="l-fail"),
    )
    assert resp.fully_successful is False
    assert resp.partially_successful is False
