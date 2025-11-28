"""
Canvas Endpoint Tests for Canvas Learning System API

Tests for Canvas operations endpoints (6 endpoints total).

Story 15.6: API文档和测试框架
✅ Verified from Context7:/websites/fastapi_tiangolo (topic: TestClient testing)
"""

import pytest


@pytest.mark.api
class TestReadCanvas:
    """Tests for GET /api/v1/canvas/{canvas_name} endpoint."""

    def test_read_canvas_success(self, client, api_v1_prefix, test_canvas_name):
        """
        Test reading existing canvas returns data.

        AC: GET /api/v1/canvas/{name} returns 200 with canvas data.
        Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1canvas~1{canvas_name}
        """
        response = client.get(f"{api_v1_prefix}/canvas/{test_canvas_name}")

        assert response.status_code == 200
        data = response.json()

        assert "name" in data
        assert "nodes" in data
        assert "edges" in data
        assert data["name"] == test_canvas_name
        assert isinstance(data["nodes"], list)
        assert isinstance(data["edges"], list)

    def test_read_canvas_not_found(self, client, api_v1_prefix, nonexistent_canvas):
        """
        Test reading non-existent canvas returns 404.

        AC: Returns 404 with error message for non-existent canvas.
        """
        response = client.get(f"{api_v1_prefix}/canvas/{nonexistent_canvas}")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data


@pytest.mark.api
class TestCreateNode:
    """Tests for POST /api/v1/canvas/{canvas_name}/nodes endpoint."""

    def test_create_node_success(self, client, api_v1_prefix, test_canvas_name, valid_text_node):
        """
        Test creating a new node returns 201.

        AC: POST /api/v1/canvas/{name}/nodes returns 201 with node data.
        Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1canvas~1{canvas_name}~1nodes
        """
        node_data = valid_text_node()
        response = client.post(
            f"{api_v1_prefix}/canvas/{test_canvas_name}/nodes",
            json=node_data
        )

        assert response.status_code == 201
        data = response.json()

        assert "id" in data
        assert data["type"] == node_data["type"]
        assert data["text"] == node_data["text"]
        assert data["x"] == node_data["x"]
        assert data["y"] == node_data["y"]

    def test_create_node_canvas_not_found(
        self, client, api_v1_prefix, nonexistent_canvas, valid_text_node
    ):
        """
        Test creating node in non-existent canvas returns 404.

        AC: Returns 404 when canvas doesn't exist.
        """
        response = client.post(
            f"{api_v1_prefix}/canvas/{nonexistent_canvas}/nodes",
            json=valid_text_node()
        )

        assert response.status_code == 404

    def test_create_node_validation_error(self, client, api_v1_prefix, test_canvas_name):
        """
        Test creating node with invalid data returns 422.

        AC: Returns 422 validation error for invalid data.
        """
        invalid_node = {"type": "invalid_type", "x": 100}  # Missing required fields
        response = client.post(
            f"{api_v1_prefix}/canvas/{test_canvas_name}/nodes",
            json=invalid_node
        )

        assert response.status_code == 422


@pytest.mark.api
class TestUpdateNode:
    """Tests for PUT /api/v1/canvas/{canvas_name}/nodes/{node_id} endpoint."""

    def test_update_node_success(self, client, api_v1_prefix, test_canvas_name, test_node_id):
        """
        Test updating existing node returns 200.

        AC: PUT /api/v1/canvas/{name}/nodes/{id} returns 200 with updated data.
        Source: specs/api/fastapi-backend-api.openapi.yml
        """
        update_data = {"text": "更新后的文本", "color": "2"}
        response = client.put(
            f"{api_v1_prefix}/canvas/{test_canvas_name}/nodes/{test_node_id}",
            json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["text"] == update_data["text"]
        assert data["color"] == update_data["color"]

    def test_update_node_not_found(self, client, api_v1_prefix, test_canvas_name, nonexistent_node_id):
        """
        Test updating non-existent node returns 404.

        AC: Returns 404 when node doesn't exist.
        """
        response = client.put(
            f"{api_v1_prefix}/canvas/{test_canvas_name}/nodes/{nonexistent_node_id}",
            json={"text": "test"}
        )

        assert response.status_code == 404


@pytest.mark.api
class TestDeleteNode:
    """Tests for DELETE /api/v1/canvas/{canvas_name}/nodes/{node_id} endpoint."""

    def test_delete_node_success(self, client, api_v1_prefix, test_canvas_name, valid_text_node):
        """
        Test deleting existing node returns 204.

        AC: DELETE /api/v1/canvas/{name}/nodes/{id} returns 204 no content.
        Source: specs/api/fastapi-backend-api.openapi.yml
        """
        # First create a node to delete
        node_data = valid_text_node(text="节点待删除")
        create_response = client.post(
            f"{api_v1_prefix}/canvas/{test_canvas_name}/nodes",
            json=node_data
        )
        assert create_response.status_code == 201
        node_id = create_response.json()["id"]

        # Now delete it
        response = client.delete(
            f"{api_v1_prefix}/canvas/{test_canvas_name}/nodes/{node_id}"
        )

        assert response.status_code == 204

    def test_delete_node_not_found(self, client, api_v1_prefix, test_canvas_name, nonexistent_node_id):
        """
        Test deleting non-existent node returns 404.

        AC: Returns 404 when node doesn't exist.
        """
        response = client.delete(
            f"{api_v1_prefix}/canvas/{test_canvas_name}/nodes/{nonexistent_node_id}"
        )

        assert response.status_code == 404


@pytest.mark.api
class TestCreateEdge:
    """Tests for POST /api/v1/canvas/{canvas_name}/edges endpoint."""

    def test_create_edge_success(self, client, api_v1_prefix, test_canvas_name, valid_edge):
        """
        Test creating a new edge returns 201.

        AC: POST /api/v1/canvas/{name}/edges returns 201 with edge data.
        Source: specs/api/fastapi-backend-api.openapi.yml
        """
        edge_data = valid_edge()
        response = client.post(
            f"{api_v1_prefix}/canvas/{test_canvas_name}/edges",
            json=edge_data
        )

        assert response.status_code == 201
        data = response.json()

        assert "id" in data
        assert data["fromNode"] == edge_data["fromNode"]
        assert data["toNode"] == edge_data["toNode"]

    def test_create_edge_validation_error(self, client, api_v1_prefix, test_canvas_name):
        """
        Test creating edge with missing fields returns 422.

        AC: Returns 422 validation error for invalid data.
        """
        invalid_edge = {"fromNode": "node1"}  # Missing toNode
        response = client.post(
            f"{api_v1_prefix}/canvas/{test_canvas_name}/edges",
            json=invalid_edge
        )

        assert response.status_code == 422


@pytest.mark.api
class TestDeleteEdge:
    """Tests for DELETE /api/v1/canvas/{canvas_name}/edges/{edge_id} endpoint."""

    def test_delete_edge_success(self, client, api_v1_prefix, test_canvas_name, valid_edge):
        """
        Test deleting existing edge returns 204.

        AC: DELETE /api/v1/canvas/{name}/edges/{id} returns 204 no content.
        Source: specs/api/fastapi-backend-api.openapi.yml
        """
        # First create an edge to delete
        edge_data = valid_edge()
        create_response = client.post(
            f"{api_v1_prefix}/canvas/{test_canvas_name}/edges",
            json=edge_data
        )
        assert create_response.status_code == 201
        edge_id = create_response.json()["id"]

        # Now delete it
        response = client.delete(
            f"{api_v1_prefix}/canvas/{test_canvas_name}/edges/{edge_id}"
        )

        assert response.status_code == 204

    def test_delete_edge_not_found(self, client, api_v1_prefix, test_canvas_name):
        """
        Test deleting non-existent edge returns 404.

        AC: Returns 404 when edge doesn't exist.
        """
        response = client.delete(
            f"{api_v1_prefix}/canvas/{test_canvas_name}/edges/nonexistent-edge"
        )

        assert response.status_code == 404
