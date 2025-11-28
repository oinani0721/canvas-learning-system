"""
Agents Endpoint Tests for Canvas Learning System API

Tests for Agent invocation endpoints (9 endpoints total).

Story 15.6: API文档和测试框架
✅ Verified from Context7:/websites/fastapi_tiangolo (topic: TestClient testing)
"""

import pytest


@pytest.mark.api
class TestDecomposeBasic:
    """Tests for POST /api/v1/agents/decompose/basic endpoint."""

    def test_decompose_basic_success(self, client, api_v1_prefix, valid_decompose_request):
        """
        Test basic decomposition returns questions and nodes.

        AC: POST /api/v1/agents/decompose/basic returns 200 with DecomposeResponse.
        Source: specs/api/fastapi-backend-api.openapi.yml
        """
        response = client.post(
            f"{api_v1_prefix}/agents/decompose/basic",
            json=valid_decompose_request()
        )

        assert response.status_code == 200
        data = response.json()

        assert "questions" in data
        assert "created_nodes" in data
        assert isinstance(data["questions"], list)
        assert isinstance(data["created_nodes"], list)
        assert len(data["questions"]) > 0

    def test_decompose_basic_validation_error(self, client, api_v1_prefix):
        """
        Test decompose with missing fields returns 422.

        AC: Returns 422 validation error for invalid data.
        """
        invalid_request = {"canvas_name": "test"}  # Missing node_id
        response = client.post(
            f"{api_v1_prefix}/agents/decompose/basic",
            json=invalid_request
        )

        assert response.status_code == 422


@pytest.mark.api
class TestDecomposeDeep:
    """Tests for POST /api/v1/agents/decompose/deep endpoint."""

    def test_decompose_deep_success(self, client, api_v1_prefix, valid_decompose_request):
        """
        Test deep decomposition returns questions and nodes.

        AC: POST /api/v1/agents/decompose/deep returns 200 with DecomposeResponse.
        Source: specs/api/fastapi-backend-api.openapi.yml
        """
        response = client.post(
            f"{api_v1_prefix}/agents/decompose/deep",
            json=valid_decompose_request()
        )

        assert response.status_code == 200
        data = response.json()

        assert "questions" in data
        assert "created_nodes" in data
        assert len(data["questions"]) > 0

    def test_decompose_deep_validation_error(self, client, api_v1_prefix):
        """
        Test decompose with empty body returns 422.

        AC: Returns 422 validation error for invalid data.
        """
        response = client.post(
            f"{api_v1_prefix}/agents/decompose/deep",
            json={}
        )

        assert response.status_code == 422


@pytest.mark.api
class TestScoreUnderstanding:
    """Tests for POST /api/v1/agents/score endpoint."""

    def test_score_success(self, client, api_v1_prefix, valid_score_request):
        """
        Test scoring returns scores for each node.

        AC: POST /api/v1/agents/score returns 200 with ScoreResponse.
        Source: specs/api/fastapi-backend-api.openapi.yml
        """
        request_data = valid_score_request()
        response = client.post(
            f"{api_v1_prefix}/agents/score",
            json=request_data
        )

        assert response.status_code == 200
        data = response.json()

        assert "scores" in data
        assert isinstance(data["scores"], list)
        assert len(data["scores"]) == len(request_data["node_ids"])

        # Verify score structure
        for score in data["scores"]:
            assert "node_id" in score
            assert "accuracy" in score
            assert "imagery" in score
            assert "completeness" in score
            assert "originality" in score
            assert "total" in score
            assert "new_color" in score
            assert 0 <= score["accuracy"] <= 10
            assert 0 <= score["total"] <= 40
            assert score["new_color"] in ["2", "3", "4"]

    def test_score_validation_error(self, client, api_v1_prefix):
        """
        Test scoring with missing fields returns 422.

        AC: Returns 422 validation error for invalid data.
        """
        invalid_request = {"canvas_name": "test"}  # Missing node_ids
        response = client.post(
            f"{api_v1_prefix}/agents/score",
            json=invalid_request
        )

        assert response.status_code == 422


@pytest.mark.api
class TestExplainOral:
    """Tests for POST /api/v1/agents/explain/oral endpoint."""

    def test_explain_oral_success(self, client, api_v1_prefix, valid_explain_request):
        """
        Test oral explanation returns explanation and node.

        AC: POST /api/v1/agents/explain/oral returns 200 with ExplainResponse.
        Source: specs/api/fastapi-backend-api.openapi.yml
        """
        response = client.post(
            f"{api_v1_prefix}/agents/explain/oral",
            json=valid_explain_request()
        )

        assert response.status_code == 200
        data = response.json()

        assert "explanation" in data
        assert "created_node_id" in data
        assert len(data["explanation"]) > 0

    def test_explain_oral_validation_error(self, client, api_v1_prefix):
        """
        Test explain with missing fields returns 422.

        AC: Returns 422 validation error for invalid data.
        """
        response = client.post(
            f"{api_v1_prefix}/agents/explain/oral",
            json={}
        )

        assert response.status_code == 422


@pytest.mark.api
class TestExplainClarification:
    """Tests for POST /api/v1/agents/explain/clarification endpoint."""

    def test_explain_clarification_success(self, client, api_v1_prefix, valid_explain_request):
        """
        Test clarification path returns explanation and node.

        AC: POST /api/v1/agents/explain/clarification returns 200.
        Source: specs/api/fastapi-backend-api.openapi.yml
        """
        response = client.post(
            f"{api_v1_prefix}/agents/explain/clarification",
            json=valid_explain_request()
        )

        assert response.status_code == 200
        data = response.json()

        assert "explanation" in data
        assert "created_node_id" in data

    def test_explain_clarification_validation_error(self, client, api_v1_prefix):
        """
        Test explain with invalid data returns 422.
        """
        response = client.post(
            f"{api_v1_prefix}/agents/explain/clarification",
            json={"invalid": "data"}
        )

        assert response.status_code == 422


@pytest.mark.api
class TestExplainComparison:
    """Tests for POST /api/v1/agents/explain/comparison endpoint."""

    def test_explain_comparison_success(self, client, api_v1_prefix, valid_explain_request):
        """
        Test comparison table returns explanation and node.

        AC: POST /api/v1/agents/explain/comparison returns 200.
        Source: specs/api/fastapi-backend-api.openapi.yml
        """
        response = client.post(
            f"{api_v1_prefix}/agents/explain/comparison",
            json=valid_explain_request()
        )

        assert response.status_code == 200
        data = response.json()

        assert "explanation" in data
        assert "created_node_id" in data

    def test_explain_comparison_validation_error(self, client, api_v1_prefix):
        """
        Test explain with missing node_id returns 422.
        """
        response = client.post(
            f"{api_v1_prefix}/agents/explain/comparison",
            json={"canvas_name": "test"}
        )

        assert response.status_code == 422


@pytest.mark.api
class TestExplainMemory:
    """Tests for POST /api/v1/agents/explain/memory endpoint."""

    def test_explain_memory_success(self, client, api_v1_prefix, valid_explain_request):
        """
        Test memory anchor returns explanation and node.

        AC: POST /api/v1/agents/explain/memory returns 200.
        Source: specs/api/fastapi-backend-api.openapi.yml
        """
        response = client.post(
            f"{api_v1_prefix}/agents/explain/memory",
            json=valid_explain_request()
        )

        assert response.status_code == 200
        data = response.json()

        assert "explanation" in data
        assert "created_node_id" in data

    def test_explain_memory_validation_error(self, client, api_v1_prefix):
        """
        Test explain with empty body returns 422.
        """
        response = client.post(
            f"{api_v1_prefix}/agents/explain/memory",
            json={}
        )

        assert response.status_code == 422


@pytest.mark.api
class TestExplainFourLevel:
    """Tests for POST /api/v1/agents/explain/four-level endpoint."""

    def test_explain_four_level_success(self, client, api_v1_prefix, valid_explain_request):
        """
        Test four-level explanation returns explanation and node.

        AC: POST /api/v1/agents/explain/four-level returns 200.
        Source: specs/api/fastapi-backend-api.openapi.yml
        """
        response = client.post(
            f"{api_v1_prefix}/agents/explain/four-level",
            json=valid_explain_request()
        )

        assert response.status_code == 200
        data = response.json()

        assert "explanation" in data
        assert "created_node_id" in data
        # Verify four levels are mentioned
        assert "Level" in data["explanation"]

    def test_explain_four_level_validation_error(self, client, api_v1_prefix):
        """
        Test explain with invalid data returns 422.
        """
        response = client.post(
            f"{api_v1_prefix}/agents/explain/four-level",
            json={"wrong_field": "value"}
        )

        assert response.status_code == 422


@pytest.mark.api
class TestExplainExample:
    """Tests for POST /api/v1/agents/explain/example endpoint."""

    def test_explain_example_success(self, client, api_v1_prefix, valid_explain_request):
        """
        Test example teaching returns explanation and node.

        AC: POST /api/v1/agents/explain/example returns 200.
        Source: specs/api/fastapi-backend-api.openapi.yml
        """
        response = client.post(
            f"{api_v1_prefix}/agents/explain/example",
            json=valid_explain_request()
        )

        assert response.status_code == 200
        data = response.json()

        assert "explanation" in data
        assert "created_node_id" in data

    def test_explain_example_validation_error(self, client, api_v1_prefix):
        """
        Test explain with missing required fields returns 422.
        """
        response = client.post(
            f"{api_v1_prefix}/agents/explain/example",
            json={}
        )

        assert response.status_code == 422
