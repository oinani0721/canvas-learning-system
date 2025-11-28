# Canvas Learning System - Router Tests
# Story 15.2: Routing System and APIRouter Configuration
"""
Unit tests for API routers.

Tests all 19 endpoints across 4 routers (System, Canvas, Agents, Review).
[Source: specs/api/fastapi-backend-api.openapi.yml]
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: testing)
# TestClient for synchronous testing of FastAPI applications
client = TestClient(app)


# ═══════════════════════════════════════════════════════════════════════════════
# System Router Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check_returns_200(self):
        """Test health check returns 200 OK."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200

    def test_health_check_response_structure(self):
        """Test health check response has correct structure."""
        response = client.get("/api/v1/health")
        data = response.json()

        assert "status" in data
        assert "app_name" in data
        assert "version" in data
        assert "timestamp" in data

    def test_health_check_status_healthy(self):
        """Test health check returns healthy status."""
        response = client.get("/api/v1/health")
        data = response.json()

        assert data["status"] == "healthy"
        assert data["app_name"] == "Canvas Learning System"
        assert data["version"] == "1.0.0"


# ═══════════════════════════════════════════════════════════════════════════════
# Canvas Router Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestCanvasRouter:
    """Tests for Canvas router endpoints."""

    def test_read_canvas(self):
        """Test reading a canvas returns 200."""
        response = client.get("/api/v1/canvas/test-canvas")
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "test-canvas"
        assert "nodes" in data
        assert "edges" in data

    def test_create_node(self):
        """Test creating a node returns 201."""
        node_data = {
            "type": "text",
            "text": "Test node content",
            "x": 100,
            "y": 200,
            "width": 250,
            "height": 60,
        }
        response = client.post("/api/v1/canvas/test-canvas/nodes", json=node_data)
        assert response.status_code == 201

        data = response.json()
        assert "id" in data
        assert data["type"] == "text"
        assert data["text"] == "Test node content"
        assert data["x"] == 100
        assert data["y"] == 200

    def test_create_node_with_color(self):
        """Test creating a node with color."""
        node_data = {
            "type": "text",
            "text": "Red node",
            "x": 0,
            "y": 0,
            "color": "1",  # Red
        }
        response = client.post("/api/v1/canvas/test-canvas/nodes", json=node_data)
        assert response.status_code == 201

        data = response.json()
        assert data["color"] == "1"

    def test_update_node(self):
        """Test updating a node returns 200."""
        update_data = {
            "text": "Updated content",
            "x": 150,
            "y": 250,
        }
        response = client.put(
            "/api/v1/canvas/test-canvas/nodes/abc123",
            json=update_data,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == "abc123"
        assert data["text"] == "Updated content"

    def test_delete_node(self):
        """Test deleting a node returns 204."""
        response = client.delete("/api/v1/canvas/test-canvas/nodes/abc123")
        assert response.status_code == 204

    def test_create_edge(self):
        """Test creating an edge returns 201."""
        edge_data = {
            "fromNode": "node1",
            "toNode": "node2",
            "fromSide": "right",
            "toSide": "left",
            "label": "connects to",
        }
        response = client.post("/api/v1/canvas/test-canvas/edges", json=edge_data)
        assert response.status_code == 201

        data = response.json()
        assert "id" in data
        assert data["fromNode"] == "node1"
        assert data["toNode"] == "node2"

    def test_delete_edge(self):
        """Test deleting an edge returns 204."""
        response = client.delete("/api/v1/canvas/test-canvas/edges/edge123")
        assert response.status_code == 204


# ═══════════════════════════════════════════════════════════════════════════════
# Agents Router Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestAgentsRouter:
    """Tests for Agents router endpoints."""

    def test_decompose_basic(self):
        """Test basic decomposition returns 200."""
        request_data = {
            "canvas_name": "test-canvas",
            "node_id": "node123",
        }
        response = client.post("/api/v1/agents/decompose/basic", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert "questions" in data
        assert "created_nodes" in data
        assert isinstance(data["questions"], list)

    def test_decompose_deep(self):
        """Test deep decomposition returns 200."""
        request_data = {
            "canvas_name": "test-canvas",
            "node_id": "node123",
        }
        response = client.post("/api/v1/agents/decompose/deep", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert "questions" in data
        assert len(data["questions"]) >= 3  # Deep should have more questions

    def test_score_understanding(self):
        """Test scoring understanding returns 200."""
        request_data = {
            "canvas_name": "test-canvas",
            "node_ids": ["node1", "node2"],
        }
        response = client.post("/api/v1/agents/score", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert "scores" in data
        assert len(data["scores"]) == 2

        # Verify score structure
        score = data["scores"][0]
        assert "accuracy" in score
        assert "imagery" in score
        assert "completeness" in score
        assert "originality" in score
        assert "total" in score
        assert "new_color" in score

    def test_explain_oral(self):
        """Test oral explanation returns 200."""
        request_data = {
            "canvas_name": "test-canvas",
            "node_id": "node123",
        }
        response = client.post("/api/v1/agents/explain/oral", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert "explanation" in data
        assert "created_node_id" in data

    def test_explain_clarification(self):
        """Test clarification explanation returns 200."""
        request_data = {
            "canvas_name": "test-canvas",
            "node_id": "node123",
        }
        response = client.post("/api/v1/agents/explain/clarification", json=request_data)
        assert response.status_code == 200

    def test_explain_comparison(self):
        """Test comparison explanation returns 200."""
        request_data = {
            "canvas_name": "test-canvas",
            "node_id": "node123",
        }
        response = client.post("/api/v1/agents/explain/comparison", json=request_data)
        assert response.status_code == 200

    def test_explain_memory(self):
        """Test memory anchor explanation returns 200."""
        request_data = {
            "canvas_name": "test-canvas",
            "node_id": "node123",
        }
        response = client.post("/api/v1/agents/explain/memory", json=request_data)
        assert response.status_code == 200

    def test_explain_four_level(self):
        """Test four-level explanation returns 200."""
        request_data = {
            "canvas_name": "test-canvas",
            "node_id": "node123",
        }
        response = client.post("/api/v1/agents/explain/four-level", json=request_data)
        assert response.status_code == 200

    def test_explain_example(self):
        """Test example-based teaching returns 200."""
        request_data = {
            "canvas_name": "test-canvas",
            "node_id": "node123",
        }
        response = client.post("/api/v1/agents/explain/example", json=request_data)
        assert response.status_code == 200


# ═══════════════════════════════════════════════════════════════════════════════
# Review Router Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestReviewRouter:
    """Tests for Review router endpoints."""

    def test_get_review_schedule(self):
        """Test getting review schedule returns 200."""
        response = client.get("/api/v1/review/schedule")
        assert response.status_code == 200

        data = response.json()
        assert "items" in data
        assert "total_count" in data

    def test_get_review_schedule_with_days(self):
        """Test getting review schedule with custom days parameter."""
        response = client.get("/api/v1/review/schedule?days=14")
        assert response.status_code == 200

    def test_generate_verification_canvas(self):
        """Test generating verification canvas returns 201."""
        request_data = {
            "source_canvas": "test-canvas",
        }
        response = client.post("/api/v1/review/generate", json=request_data)
        assert response.status_code == 201

        data = response.json()
        assert "verification_canvas_name" in data
        assert "node_count" in data
        assert "test-canvas" in data["verification_canvas_name"]

    def test_generate_verification_canvas_with_node_ids(self):
        """Test generating verification canvas with specific nodes."""
        request_data = {
            "source_canvas": "test-canvas",
            "node_ids": ["node1", "node2", "node3"],
        }
        response = client.post("/api/v1/review/generate", json=request_data)
        assert response.status_code == 201

    def test_record_review_result(self):
        """Test recording review result returns 200."""
        request_data = {
            "canvas_name": "test-canvas",
            "node_id": "node123",
            "score": 35.0,
        }
        response = client.put("/api/v1/review/record", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert "next_review_date" in data
        assert "new_interval" in data

    def test_record_review_result_high_score(self):
        """Test recording high score sets 30-day interval."""
        request_data = {
            "canvas_name": "test-canvas",
            "node_id": "node123",
            "score": 35.0,  # High score (>=32)
        }
        response = client.put("/api/v1/review/record", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert data["new_interval"] == 30

    def test_record_review_result_medium_score(self):
        """Test recording medium score sets 7-day interval."""
        request_data = {
            "canvas_name": "test-canvas",
            "node_id": "node123",
            "score": 28.0,  # Medium score (24-31)
        }
        response = client.put("/api/v1/review/record", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert data["new_interval"] == 7

    def test_record_review_result_low_score(self):
        """Test recording low score sets 1-day interval."""
        request_data = {
            "canvas_name": "test-canvas",
            "node_id": "node123",
            "score": 15.0,  # Low score (<24)
        }
        response = client.put("/api/v1/review/record", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert data["new_interval"] == 1


# ═══════════════════════════════════════════════════════════════════════════════
# OpenAPI Schema Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestOpenAPISchema:
    """Tests for OpenAPI schema generation."""

    def test_openapi_schema_available(self):
        """Test OpenAPI schema is available at /openapi.json."""
        response = client.get("/openapi.json")
        assert response.status_code == 200

        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema

    def test_openapi_has_all_tags(self):
        """Test OpenAPI schema has all expected tags."""
        response = client.get("/openapi.json")
        schema = response.json()

        tag_names = [tag["name"] for tag in schema.get("tags", [])]
        assert "System" in tag_names
        assert "Canvas" in tag_names
        assert "Agents" in tag_names
        assert "Review" in tag_names

    def test_openapi_has_health_endpoint(self):
        """Test OpenAPI schema includes health endpoint."""
        response = client.get("/openapi.json")
        schema = response.json()

        assert "/api/v1/health" in schema["paths"]

    def test_openapi_has_canvas_endpoints(self):
        """Test OpenAPI schema includes canvas endpoints."""
        response = client.get("/openapi.json")
        schema = response.json()
        paths = schema["paths"]

        # Check for canvas-related paths
        canvas_paths = [p for p in paths if "/canvas" in p]
        assert len(canvas_paths) >= 4  # At least 4 canvas paths

    def test_openapi_has_agents_endpoints(self):
        """Test OpenAPI schema includes agents endpoints."""
        response = client.get("/openapi.json")
        schema = response.json()
        paths = schema["paths"]

        # Check for agents-related paths
        agents_paths = [p for p in paths if "/agents" in p]
        assert len(agents_paths) >= 8  # At least 8 agents paths

    def test_openapi_has_review_endpoints(self):
        """Test OpenAPI schema includes review endpoints."""
        response = client.get("/openapi.json")
        schema = response.json()
        paths = schema["paths"]

        # Check for review-related paths
        review_paths = [p for p in paths if "/review" in p]
        assert len(review_paths) >= 3  # At least 3 review paths

    def test_swagger_docs_available(self):
        """Test Swagger documentation is available."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_redoc_available(self):
        """Test ReDoc documentation is available."""
        response = client.get("/redoc")
        assert response.status_code == 200
