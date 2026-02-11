# Canvas Learning System - E2E Tests for POST /api/v1/review/generate
# Story 31.A.10 AC-3: Review Generate E2E Coverage
"""
E2E tests for POST /api/v1/review/generate (Story 31.2).

Verifies the endpoint from HTTP request → review generation → response
through the complete chain, including degraded mode without agent services.

[Source: docs/stories/31.A.10.story.md#AC-31.A.10.3]
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def review_canvas_dir(tmp_path: Path) -> Path:
    """Create a temp directory with a canvas file containing red+purple nodes."""
    canvas_data = {
        "nodes": [
            {
                "id": "node-red-1",
                "type": "text",
                "text": "递归：一个函数调用自身的编程技术",
                "x": 0, "y": 0,
                "width": 250, "height": 60,
                "color": "4"  # Red
            },
            {
                "id": "node-purple-1",
                "type": "text",
                "text": "动态规划：将问题分解为子问题的算法策略",
                "x": 300, "y": 0,
                "width": 250, "height": 60,
                "color": "3"  # Purple
            },
            {
                "id": "node-green-1",
                "type": "text",
                "text": "变量：存储数据的容器",
                "x": 600, "y": 0,
                "width": 250, "height": 60,
                "color": "5"  # Green (should be excluded from review)
            },
        ],
        "edges": [
            {"id": "edge1", "fromNode": "node-red-1", "toNode": "node-purple-1"}
        ]
    }

    canvas_file = tmp_path / "test-algo.canvas"
    canvas_file.write_text(json.dumps(canvas_data, ensure_ascii=False), encoding="utf-8")
    return tmp_path


class TestReviewGenerateE2E:
    """E2E tests for POST /api/v1/review/generate (Story 31.2).

    Verifies the endpoint from HTTP request → review generation → response.

    [Source: docs/stories/31.A.10.story.md#AC-31.A.10.3]
    """

    def test_generate_returns_201_with_valid_canvas(self, client: TestClient, review_canvas_dir: Path):
        """Normal request with valid canvas returns 201 and verification data.

        [Source: docs/stories/31.A.10.story.md#AC-31.A.10.3 - test 1]
        """
        with patch("app.api.v1.endpoints.review._canvas_base_path", review_canvas_dir):
            response = client.post(
                "/api/v1/review/generate",
                json={"source_canvas": "test-algo"}
            )

        assert response.status_code == 201
        data = response.json()
        assert "verification_canvas_name" in data
        assert "node_count" in data
        assert data["node_count"] >= 1  # At least red+purple nodes
        assert "mode_used" in data
        assert data["mode_used"] == "fresh"  # Default mode

    def test_generate_returns_422_with_missing_params(self, client: TestClient):
        """Missing required source_canvas parameter returns 422.

        [Source: docs/stories/31.A.10.story.md#AC-31.A.10.3 - test 2]
        """
        response = client.post(
            "/api/v1/review/generate",
            json={}  # Missing source_canvas (required field)
        )
        assert response.status_code == 422

    def test_generate_degrades_gracefully_without_agent(self, client: TestClient, review_canvas_dir: Path):
        """Agent unavailable still returns 201 with template questions (degraded mode).

        [Source: docs/stories/31.A.10.story.md#AC-31.A.10.3 - test 3]
        """
        with patch("app.api.v1.endpoints.review._canvas_base_path", review_canvas_dir), \
             patch("app.api.v1.endpoints.review._ai_question_available", False), \
             patch("app.api.v1.endpoints.review._services_available", False), \
             patch("app.api.v1.endpoints.review._difficulty_available", False):
            response = client.post(
                "/api/v1/review/generate",
                json={"source_canvas": "test-algo"}
            )

        assert response.status_code == 201
        data = response.json()
        assert data["node_count"] >= 1  # Template questions still generated
        assert "verification_canvas_name" in data

    def test_generate_returns_zero_nodes_for_nonexistent_canvas(self, client: TestClient, review_canvas_dir: Path):
        """Nonexistent canvas returns 201 with node_count=0 (graceful handling).

        [Source: docs/stories/31.A.10.story.md#AC-31.A.10.3 - test 4]
        """
        with patch("app.api.v1.endpoints.review._canvas_base_path", review_canvas_dir):
            response = client.post(
                "/api/v1/review/generate",
                json={"source_canvas": "nonexistent-canvas"}
            )

        assert response.status_code == 201
        data = response.json()
        assert data["node_count"] == 0

    def test_generate_targeted_mode(self, client: TestClient, review_canvas_dir: Path):
        """Targeted mode request returns correct mode_used in response.

        [Source: docs/stories/31.A.10.story.md#AC-31.A.10.3 - test 5]
        """
        with patch("app.api.v1.endpoints.review._canvas_base_path", review_canvas_dir), \
             patch("app.api.v1.endpoints.review._ai_question_available", False), \
             patch("app.api.v1.endpoints.review._services_available", False), \
             patch("app.api.v1.endpoints.review._difficulty_available", False):
            response = client.post(
                "/api/v1/review/generate",
                json={
                    "source_canvas": "test-algo",
                    "mode": "targeted"
                }
            )

        assert response.status_code == 201
        data = response.json()
        assert data["mode_used"] == "targeted"
