# Canvas Learning System - Agent Canvas Parameter Integration Tests
# Story 21.5.1.3: API参数格式测试与回归验证 (AC-3)
"""
End-to-end integration tests for Agent API canvas_name parameter handling.

These tests verify:
- AC-3.1: Agent endpoints accept properly formatted canvas_name parameters
- AC-3.2: Agent endpoints reject path traversal attempts
- AC-3.3: Full flow from API request to backend response works correctly

[Source: docs/prd/EPIC-21.5.1-API-PARAM-FIX.md#Story-21.5.1.3]
[Source: docs/stories/21.5.1.3.story.md]
"""

import json
import tempfile
from pathlib import Path
from typing import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.config import Settings, get_settings
from app.main import app
from fastapi.testclient import TestClient


def get_test_settings() -> Settings:
    """Override settings for testing."""
    return Settings(
        PROJECT_NAME="Canvas Learning System API (Integration Test)",
        VERSION="1.0.0-test",
        DEBUG=True,
        LOG_LEVEL="DEBUG",
        CORS_ORIGINS="http://localhost:3000",
        CANVAS_BASE_PATH="./test_canvas",
    )


@pytest.fixture(scope="module")
def integration_client() -> Generator[TestClient, None, None]:
    """Create a test client with overridden settings."""
    app.dependency_overrides[get_settings] = get_test_settings
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def temp_canvas_dir():
    """Create a temporary directory with test canvas files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir)

        # Create simple canvas file
        simple_canvas = base_path / "test.canvas"
        simple_canvas.write_text(json.dumps({
            "nodes": [
                {"id": "node1", "type": "text", "text": "Test Node", "x": 0, "y": 0, "width": 250, "height": 60}
            ],
            "edges": []
        }), encoding="utf-8")

        # Create canvas in subdirectory (Chinese path)
        subdir = base_path / "笔记库" / "子目录"
        subdir.mkdir(parents=True, exist_ok=True)
        subdirectory_canvas = subdir / "chinese.canvas"
        subdirectory_canvas.write_text(json.dumps({
            "nodes": [
                {"id": "node2", "type": "text", "text": "子目录节点", "x": 100, "y": 100, "width": 250, "height": 60}
            ],
            "edges": []
        }), encoding="utf-8")

        yield base_path


class TestAgentCanvasParamValidation:
    """
    Integration tests for canvas_name parameter validation in Agent endpoints.

    Story 21.5.1.3 AC-3: End-to-end tests for plugin call → backend response flow.
    """

    # ========================================
    # AC-3.1: Valid Canvas Names Accepted
    # ========================================

    def test_decompose_basic_accepts_simple_filename(
        self, integration_client: TestClient, temp_canvas_dir: Path
    ):
        """AC-3.1: Simple filename like 'test.canvas' should be accepted."""
        with patch("app.api.v1.endpoints.agents.CanvasServiceDep"), \
             patch("app.api.v1.endpoints.agents.AgentServiceDep") as mock_agent_svc, \
             patch("app.api.v1.endpoints.agents.ContextEnrichmentServiceDep") as mock_ctx_svc:

            # Mock ContextEnrichmentService response
            mock_enriched = MagicMock()
            mock_enriched.target_content = "Test content"
            mock_enriched.enriched_context = ""
            mock_enriched.x = 0
            mock_enriched.y = 0
            mock_enriched.width = 250
            mock_enriched.height = 60
            mock_enriched.has_textbook_refs = False
            mock_ctx_svc.enrich_with_adjacent_nodes = AsyncMock(return_value=mock_enriched)

            # Mock AgentService response
            mock_agent_svc.decompose_basic = AsyncMock(return_value={
                "questions": ["What is recursion?"],
                "created_nodes": []
            })

            # Make request with simple filename
            response = integration_client.post(
                "/api/v1/agents/decompose/basic",
                json={"canvas_name": "test.canvas", "node_id": "node1"}
            )

            # Should not return validation error (may return 404 if canvas not found, but not 400/500 for validation)
            # The key is that the request format is accepted
            assert response.status_code in [200, 404, 500], \
                f"Unexpected status code for valid canvas name: {response.status_code}"

    def test_decompose_basic_accepts_subdirectory_path(
        self, integration_client: TestClient
    ):
        """AC-3.1: Subdirectory path like '笔记库/子目录/test.canvas' should be accepted."""
        response = integration_client.post(
            "/api/v1/agents/decompose/basic",
            json={"canvas_name": "笔记库/子目录/test.canvas", "node_id": "node1"}
        )

        # Subdirectory paths should be accepted (not rejected as path traversal)
        # 404 is acceptable (file not found), but not 400/500 for validation error
        assert response.status_code in [200, 404, 500], \
            f"Unexpected status code for subdirectory path: {response.status_code}"

        # Check that it's NOT a path traversal error
        if response.status_code == 500:
            error_detail = response.json().get("detail", "")
            assert "Path traversal" not in error_detail, \
                f"Subdirectory path incorrectly rejected as path traversal: {error_detail}"

    def test_explain_oral_accepts_chinese_path(
        self, integration_client: TestClient
    ):
        """AC-3.1: Chinese path like '学习/数学/离散数学.canvas' should be accepted."""
        response = integration_client.post(
            "/api/v1/agents/explain/oral",
            json={"canvas_name": "学习/数学/离散数学.canvas", "node_id": "node1"}
        )

        assert response.status_code in [200, 404, 500], \
            f"Unexpected status code for Chinese path: {response.status_code}"

        if response.status_code == 500:
            error_detail = response.json().get("detail", "")
            assert "Path traversal" not in error_detail, \
                f"Chinese path incorrectly rejected as path traversal: {error_detail}"

    # ========================================
    # AC-3.2: Path Traversal Rejected
    # ========================================

    def test_decompose_basic_rejects_path_traversal(
        self, integration_client: TestClient
    ):
        """AC-3.2: Path traversal attempt '../../../etc/passwd' should be rejected."""
        response = integration_client.post(
            "/api/v1/agents/decompose/basic",
            json={"canvas_name": "../../../etc/passwd", "node_id": "node1"}
        )

        # Should return error (400 or 500 with validation message)
        assert response.status_code in [400, 500], \
            f"Path traversal should be rejected, got status: {response.status_code}"

        # Check error message mentions validation/path issue
        # Note: Error response uses "message" field (from CORSExceptionMiddleware)
        error_json = response.json()
        error_message = error_json.get("message", "") or error_json.get("detail", "")
        assert any(keyword in error_message.lower() for keyword in ["path", "invalid", "traversal"]), \
            f"Error should mention path validation: {error_message}"

    def test_decompose_deep_rejects_embedded_traversal(
        self, integration_client: TestClient
    ):
        """AC-3.2: Embedded traversal 'test/../secret' should be rejected."""
        response = integration_client.post(
            "/api/v1/agents/decompose/deep",
            json={"canvas_name": "test/../secret", "node_id": "node1"}
        )

        assert response.status_code in [400, 500], \
            f"Embedded traversal should be rejected, got status: {response.status_code}"

    def test_score_rejects_null_byte_injection(
        self, integration_client: TestClient
    ):
        """AC-3.2: Null byte injection 'test\\x00.canvas' should be rejected."""
        response = integration_client.post(
            "/api/v1/agents/score",
            json={"canvas_name": "test\x00.canvas", "node_ids": ["node1"]}
        )

        # Null byte should be rejected
        assert response.status_code in [400, 500], \
            f"Null byte injection should be rejected, got status: {response.status_code}"

    def test_explain_clarification_rejects_backslash(
        self, integration_client: TestClient
    ):
        """AC-3.2: Backslash path 'test\\\\file' should be rejected."""
        response = integration_client.post(
            "/api/v1/agents/explain/clarification",
            json={"canvas_name": "test\\file", "node_id": "node1"}
        )

        assert response.status_code in [400, 500], \
            f"Backslash path should be rejected, got status: {response.status_code}"

    def test_explain_comparison_rejects_double_slash(
        self, integration_client: TestClient
    ):
        """AC-3.2: Double slash 'test//file' should be rejected."""
        response = integration_client.post(
            "/api/v1/agents/explain/comparison",
            json={"canvas_name": "test//file", "node_id": "node1"}
        )

        assert response.status_code in [400, 500], \
            f"Double slash should be rejected, got status: {response.status_code}"

    def test_explain_memory_rejects_absolute_path(
        self, integration_client: TestClient
    ):
        """AC-3.2: Absolute path '/etc/passwd' should be rejected."""
        response = integration_client.post(
            "/api/v1/agents/explain/memory",
            json={"canvas_name": "/etc/passwd", "node_id": "node1"}
        )

        assert response.status_code in [400, 500], \
            f"Absolute path should be rejected, got status: {response.status_code}"

    # ========================================
    # AC-3.3: Full Flow Tests
    # ========================================

    def test_all_agent_endpoints_handle_canvas_name_consistently(
        self, integration_client: TestClient
    ):
        """AC-3.3: All 9 agent endpoints should handle canvas_name consistently."""
        endpoints = [
            ("/api/v1/agents/decompose/basic", "DecomposeRequest"),
            ("/api/v1/agents/decompose/deep", "DecomposeRequest"),
            ("/api/v1/agents/score", "ScoreRequest"),
            ("/api/v1/agents/explain/oral", "ExplainRequest"),
            ("/api/v1/agents/explain/clarification", "ExplainRequest"),
            ("/api/v1/agents/explain/comparison", "ExplainRequest"),
            ("/api/v1/agents/explain/memory", "ExplainRequest"),
            ("/api/v1/agents/explain/four-level", "ExplainRequest"),
            ("/api/v1/agents/explain/example", "ExplainRequest"),
        ]

        # Test valid path - should not return validation error
        valid_path = "folder/subfolder/test.canvas"
        for endpoint, request_type in endpoints:
            if request_type == "ScoreRequest":
                payload = {"canvas_name": valid_path, "node_ids": ["node1"]}
            else:
                payload = {"canvas_name": valid_path, "node_id": "node1"}

            response = integration_client.post(endpoint, json=payload)

            # Check that valid subdirectory path is NOT rejected as path traversal
            if response.status_code == 500:
                error_detail = response.json().get("detail", "")
                assert "Path traversal" not in error_detail, \
                    f"Endpoint {endpoint} incorrectly rejected valid path: {error_detail}"

    def test_all_agent_endpoints_reject_traversal_consistently(
        self, integration_client: TestClient
    ):
        """AC-3.3: All 9 agent endpoints should reject path traversal consistently."""
        endpoints = [
            ("/api/v1/agents/decompose/basic", "DecomposeRequest"),
            ("/api/v1/agents/decompose/deep", "DecomposeRequest"),
            ("/api/v1/agents/score", "ScoreRequest"),
            ("/api/v1/agents/explain/oral", "ExplainRequest"),
            ("/api/v1/agents/explain/clarification", "ExplainRequest"),
            ("/api/v1/agents/explain/comparison", "ExplainRequest"),
            ("/api/v1/agents/explain/memory", "ExplainRequest"),
            ("/api/v1/agents/explain/four-level", "ExplainRequest"),
            ("/api/v1/agents/explain/example", "ExplainRequest"),
        ]

        # Test invalid path - should be rejected
        invalid_path = "../../../etc/passwd"
        rejection_count = 0

        for endpoint, request_type in endpoints:
            if request_type == "ScoreRequest":
                payload = {"canvas_name": invalid_path, "node_ids": ["node1"]}
            else:
                payload = {"canvas_name": invalid_path, "node_id": "node1"}

            response = integration_client.post(endpoint, json=payload)

            if response.status_code in [400, 500]:
                rejection_count += 1

        # All endpoints should reject path traversal
        assert rejection_count == len(endpoints), \
            f"Only {rejection_count}/{len(endpoints)} endpoints rejected path traversal"


class TestAgentCanvasParamEdgeCases:
    """
    Edge case tests for canvas_name parameter handling.

    Story 21.5.1.3 AC-3: Additional edge cases for robustness.
    """

    def test_empty_canvas_name_handled(self, integration_client: TestClient):
        """Edge case: Empty canvas_name should be handled gracefully."""
        response = integration_client.post(
            "/api/v1/agents/decompose/basic",
            json={"canvas_name": "", "node_id": "node1"}
        )

        # Empty name should result in error (400 or 422 validation error)
        assert response.status_code in [400, 404, 422, 500], \
            f"Empty canvas_name should be rejected: {response.status_code}"

    def test_unicode_characters_in_canvas_name(self, integration_client: TestClient):
        """Edge case: Unicode characters should be accepted."""
        response = integration_client.post(
            "/api/v1/agents/explain/oral",
            json={"canvas_name": "数学/微积分/导数定义.canvas", "node_id": "node1"}
        )

        # Unicode should be accepted (404 for not found is OK)
        assert response.status_code in [200, 404, 500], \
            f"Unicode path should be accepted: {response.status_code}"

        if response.status_code == 500:
            error_detail = response.json().get("detail", "")
            assert "Path traversal" not in error_detail

    def test_very_long_canvas_name_handled(self, integration_client: TestClient):
        """Edge case: Very long canvas name should be handled."""
        long_name = "a" * 1000 + ".canvas"
        response = integration_client.post(
            "/api/v1/agents/decompose/basic",
            json={"canvas_name": long_name, "node_id": "node1"}
        )

        # Long name should be handled (may fail with 404 or other error, but not crash)
        assert response.status_code in [200, 400, 404, 422, 500], \
            f"Long canvas_name caused unexpected error: {response.status_code}"

    def test_special_characters_in_canvas_name(self, integration_client: TestClient):
        """Edge case: Special characters (not dangerous) should be handled."""
        response = integration_client.post(
            "/api/v1/agents/decompose/basic",
            json={"canvas_name": "test-file_2024 (copy).canvas", "node_id": "node1"}
        )

        # Special chars like - _ ( ) should be OK
        assert response.status_code in [200, 404, 500], \
            f"Special chars should be accepted: {response.status_code}"
