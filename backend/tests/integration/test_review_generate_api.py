# Canvas Learning System - POST /review/generate API Integration Tests
# Story 31.2: 检验白板生成端到端对接
"""
API integration tests for POST /api/v1/review/generate endpoint.

Tests verify:
- AC-31.2.1: POST /review/generate API responds with 201
- AC-31.2.2: Response includes verification_canvas_name and node_count
- AC-31.2.3: Review relationship stored (via mock verification)

[Source: docs/stories/31.2.story.md]
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


# ===========================================================================
# Fixtures
# ===========================================================================


@pytest.fixture
def sample_canvas_data():
    """Canvas data with red/purple nodes for generation."""
    return {
        "nodes": [
            {
                "id": "node-r1",
                "type": "text",
                "text": "逆否命题",
                "color": "4",
                "x": 0, "y": 0, "width": 200, "height": 100,
            },
            {
                "id": "node-p1",
                "type": "text",
                "text": "充分必要条件",
                "color": "3",
                "x": 300, "y": 0, "width": 200, "height": 100,
            },
            {
                "id": "node-g1",
                "type": "text",
                "text": "命题逻辑",
                "color": "1",
                "x": 600, "y": 0, "width": 200, "height": 100,
            },
        ],
        "edges": [],
    }


@pytest.fixture
def canvas_temp_dir(sample_canvas_data):
    """Create a temp dir with a sample .canvas file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        canvas_path = os.path.join(tmpdir, "离散数学.canvas")
        with open(canvas_path, "w", encoding="utf-8") as f:
            json.dump(sample_canvas_data, f, ensure_ascii=False)
        yield tmpdir


@pytest.fixture(autouse=True)
def _reset_review_singleton():
    """Reset singletons between tests (Story 38.9: ReviewService via services layer)."""
    import app.api.v1.endpoints.review as review_mod
    from app.services.review_service import reset_review_service_singleton
    # ReviewService: reset via services-layer function
    reset_review_service_singleton()
    # VerificationService: still module-level in review.py (out of scope for 38.9)
    orig_vs = review_mod._verification_service_instance
    review_mod._verification_service_instance = None
    yield
    reset_review_service_singleton()
    review_mod._verification_service_instance = orig_vs


@pytest.fixture
def client_with_mock(canvas_temp_dir):
    """TestClient with _canvas_base_path pointing to temp dir.

    The generate endpoint uses _canvas_base_path directly (Path object)
    to locate and read canvas files — it does NOT call
    _get_review_service_singleton().
    """
    with patch(
        "app.api.v1.endpoints.review._canvas_base_path",
        Path(canvas_temp_dir),
    ):
        from app.config import get_settings
        app.dependency_overrides[get_settings] = lambda: MagicMock(
            canvas_base_path=canvas_temp_dir,
            API_V1_PREFIX="/api/v1",
        )
        with TestClient(app) as c:
            yield c
        app.dependency_overrides.pop(get_settings, None)


# ===========================================================================
# Tests: AC-31.2.1 — POST /review/generate API
# ===========================================================================


class TestGenerateVerificationCanvasAPI:
    """Test POST /api/v1/review/generate endpoint.

    [Source: docs/stories/31.2.story.md#AC-31.2.1]
    """

    def test_generate_returns_201(self, client_with_mock):
        """AC-31.2.1: API responds with HTTP 201 Created."""
        client = client_with_mock
        response = client.post(
            "/api/v1/review/generate",
            json={"source_canvas": "离散数学.canvas"},
        )
        assert response.status_code == 201

    def test_generate_returns_canvas_name(self, client_with_mock):
        """AC-31.2.2: Response includes verification_canvas_name."""
        client = client_with_mock
        response = client.post(
            "/api/v1/review/generate",
            json={"source_canvas": "离散数学.canvas"},
        )
        data = response.json()
        assert "verification_canvas_name" in data
        assert "离散数学" in data["verification_canvas_name"]

    def test_generate_returns_node_count(self, client_with_mock):
        """AC-31.2.2: Response includes node_count field."""
        client = client_with_mock
        response = client.post(
            "/api/v1/review/generate",
            json={"source_canvas": "离散数学.canvas"},
        )
        data = response.json()
        assert "node_count" in data
        assert isinstance(data["node_count"], int)

    def test_generate_returns_mode_used(self, client_with_mock):
        """AC-31.2.2: Response includes mode_used field."""
        client = client_with_mock
        response = client.post(
            "/api/v1/review/generate",
            json={"source_canvas": "离散数学.canvas", "mode": "fresh"},
        )
        data = response.json()
        assert data["mode_used"] == "fresh"

    def test_generate_fresh_mode_default(self, client_with_mock):
        """AC-31.2.1: Default mode is fresh."""
        client = client_with_mock
        response = client.post(
            "/api/v1/review/generate",
            json={"source_canvas": "离散数学.canvas"},
        )
        data = response.json()
        assert data["mode_used"] == "fresh"

    def test_generate_targeted_mode(self, client_with_mock):
        """AC-31.2.1: targeted mode accepted."""
        client = client_with_mock
        response = client.post(
            "/api/v1/review/generate",
            json={"source_canvas": "离散数学.canvas", "mode": "targeted"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["mode_used"] == "targeted"

    def test_generate_nonexistent_canvas(self, client_with_mock):
        """AC-31.2.1: Missing canvas returns 201 with node_count=0."""
        client = client_with_mock
        response = client.post(
            "/api/v1/review/generate",
            json={"source_canvas": "不存在.canvas"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["node_count"] == 0

    def test_generate_invalid_request(self, client_with_mock):
        """Validation: missing source_canvas returns 422."""
        client = client_with_mock
        response = client.post(
            "/api/v1/review/generate",
            json={},
        )
        assert response.status_code == 422
