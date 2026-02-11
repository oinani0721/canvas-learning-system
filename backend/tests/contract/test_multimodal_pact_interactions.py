"""
Story 35.12 AC 35.12.1: Pact 契约 JSON 结构验证测试

⚠️ 重要：这些测试验证 Pact JSON 文件的结构正确性（静态分析），
而非运行时 Provider 验证。真正的 Pact Provider 验证需要：
1. pact-python 安装
2. FastAPI 测试服务器运行
3. 通过 Verifier 发送 HTTP 请求
参见 test_pact_provider.py::TestPactProviderVerification 的运行时验证。

当前验证范围：
- 10 个多模态端点全部有交互定义
- Provider states 名称与 ProviderStateMiddleware 注册的一致
- 请求/响应 schema 字段与 Pydantic 模型一致
"""

import json
from pathlib import Path

import pytest

PACT_FILE = (
    Path(__file__).parent / "pacts" / "canvas-frontend-canvas-backend-multimodal.json"
)

# ── 预期端点清单 (Story 35.12 AC 35.12.1 表格) ──

EXPECTED_ENDPOINTS = [
    ("POST", "/api/v1/multimodal/upload"),
    ("POST", "/api/v1/multimodal/upload-url"),
    ("DELETE", "/api/v1/multimodal/{content_id}"),
    ("PUT", "/api/v1/multimodal/{content_id}"),
    ("GET", "/api/v1/multimodal/{content_id}"),
    ("GET", "/api/v1/multimodal/"),
    ("GET", "/api/v1/multimodal/health"),
    ("GET", "/api/v1/multimodal/list"),
    ("POST", "/api/v1/multimodal/search"),
    ("GET", "/api/v1/multimodal/by-concept/{concept_id}"),
]

EXPECTED_PROVIDER_STATES = {
    "multimodal storage is ready",
    "multimodal content exists",
    "multimodal content exists with searchable descriptions",
    "multimodal content linked to concept",
    "multimodal service is running",
    "multimodal content does not exist",
}


@pytest.fixture(scope="module")
def pact_data() -> dict:
    """Load and parse the multimodal pact JSON."""
    assert PACT_FILE.exists(), f"Pact file not found: {PACT_FILE}"
    raw = PACT_FILE.read_text(encoding="utf-8")
    return json.loads(raw)


class TestPactFileStructure:
    """Verify pact file structural correctness."""

    def test_pact_has_consumer_and_provider(self, pact_data):
        assert pact_data["consumer"]["name"] == "Canvas-Frontend"
        assert pact_data["provider"]["name"] == "Canvas-Backend"

    def test_pact_has_interactions(self, pact_data):
        assert len(pact_data["interactions"]) >= 10, (
            f"Expected >= 10 interactions, got {len(pact_data['interactions'])}"
        )

    def test_pact_metadata_version(self, pact_data):
        assert pact_data["metadata"]["pactSpecification"]["version"] == "2.0.0"


class TestPactInteractionCoverage:
    """Verify all 10 endpoints have pact interactions."""

    def test_all_provider_states_covered(self, pact_data):
        """AC 35.12.2: Every expected provider state appears in at least one interaction."""
        actual_states = {
            i["providerState"] for i in pact_data["interactions"]
        }
        missing = EXPECTED_PROVIDER_STATES - actual_states
        assert not missing, f"Missing provider states: {missing}"

    def test_health_endpoint_covered(self, pact_data):
        paths = {i["request"]["path"] for i in pact_data["interactions"]}
        assert "/api/v1/multimodal/health" in paths

    def test_list_root_endpoint_covered(self, pact_data):
        interactions = [
            i for i in pact_data["interactions"]
            if i["request"]["method"] == "GET"
            and i["request"]["path"] == "/api/v1/multimodal/"
        ]
        assert len(interactions) >= 1

    def test_list_paginated_endpoint_covered(self, pact_data):
        interactions = [
            i for i in pact_data["interactions"]
            if i["request"]["path"] == "/api/v1/multimodal/list"
        ]
        assert len(interactions) >= 1

    def test_get_by_id_endpoint_covered(self, pact_data):
        """GET /{content_id} — uses UUID path."""
        interactions = [
            i for i in pact_data["interactions"]
            if i["request"]["method"] == "GET"
            and "550e8400" in i["request"]["path"]
        ]
        assert len(interactions) >= 1

    def test_put_update_endpoint_covered(self, pact_data):
        interactions = [
            i for i in pact_data["interactions"]
            if i["request"]["method"] == "PUT"
        ]
        assert len(interactions) >= 1

    def test_delete_endpoint_covered(self, pact_data):
        interactions = [
            i for i in pact_data["interactions"]
            if i["request"]["method"] == "DELETE"
        ]
        assert len(interactions) >= 1

    def test_search_endpoint_covered(self, pact_data):
        interactions = [
            i for i in pact_data["interactions"]
            if i["request"]["method"] == "POST"
            and i["request"]["path"] == "/api/v1/multimodal/search"
        ]
        assert len(interactions) >= 1

    def test_by_concept_endpoint_covered(self, pact_data):
        interactions = [
            i for i in pact_data["interactions"]
            if "by-concept" in i["request"]["path"]
        ]
        assert len(interactions) >= 1

    def test_upload_endpoint_covered(self, pact_data):
        interactions = [
            i for i in pact_data["interactions"]
            if i["request"]["method"] == "POST"
            and i["request"]["path"] == "/api/v1/multimodal/upload"
        ]
        assert len(interactions) >= 1

    def test_upload_url_endpoint_covered(self, pact_data):
        interactions = [
            i for i in pact_data["interactions"]
            if i["request"]["method"] == "POST"
            and i["request"]["path"] == "/api/v1/multimodal/upload-url"
        ]
        assert len(interactions) >= 1

    def test_error_scenario_404_covered(self, pact_data):
        """AC 35.12.1: 错误响应 404 有覆盖."""
        error_interactions = [
            i for i in pact_data["interactions"]
            if i["response"]["status"] == 404
        ]
        assert len(error_interactions) >= 1

    def test_error_scenario_422_covered(self, pact_data):
        """AC 35.12.1: 错误响应 422 (validation) 有覆盖."""
        error_interactions = [
            i for i in pact_data["interactions"]
            if i["response"]["status"] == 422
        ]
        assert len(error_interactions) >= 1


class TestProviderStateHandlerAlignment:
    """Verify provider state names match ProviderStateMiddleware handlers."""

    def test_middleware_handles_all_pact_states(self, pact_data):
        """Every provider state in the pact file is registered in the middleware."""
        import ast

        middleware_file = Path(__file__).parent / "test_pact_provider.py"
        tree = ast.parse(middleware_file.read_text(encoding="utf-8"))

        # Extract handler dict keys from the `handlers = {...}` dict inside setup_state().
        # Only collect string keys of Dict nodes inside a method named `setup_state`.
        registered_states: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "setup_state":
                for child in ast.walk(node):
                    if isinstance(child, ast.Dict):
                        for key in child.keys:
                            if isinstance(key, ast.Constant) and isinstance(key.value, str):
                                registered_states.add(key.value)

        pact_states = {
            i["providerState"] for i in pact_data["interactions"]
        }
        multimodal_pact_states = {
            s for s in pact_states if "multimodal" in s
        }

        missing = multimodal_pact_states - registered_states
        assert not missing, (
            f"Pact states not registered in ProviderStateMiddleware: {missing}"
        )


class TestInteractionResponseSchemas:
    """Verify response bodies match Pydantic model fields."""

    def test_health_response_has_required_fields(self, pact_data):
        health = next(
            i for i in pact_data["interactions"]
            if i["request"]["path"] == "/api/v1/multimodal/health"
        )
        body = health["response"]["body"]
        required = {"status", "lancedb_connected", "neo4j_connected",
                     "storage_path_writable", "total_items"}
        assert required.issubset(body.keys())

    def test_get_content_response_has_required_fields(self, pact_data):
        get_content = next(
            i for i in pact_data["interactions"]
            if i["request"]["method"] == "GET"
            and "550e8400" in i["request"]["path"]
            and i["response"]["status"] == 200
        )
        body = get_content["response"]["body"]
        required = {"id", "media_type", "file_path", "related_concept_id", "created_at"}
        assert required.issubset(body.keys())

    def test_delete_response_is_204_no_content(self, pact_data):
        """Story 35.10 AC 35.10.3: DELETE returns 204 No Content (no body)."""
        delete_interactions = [
            i for i in pact_data["interactions"]
            if i["request"]["method"] == "DELETE"
        ]
        if not delete_interactions:
            pytest.skip("No DELETE interactions in pact data")
        delete = delete_interactions[0]
        assert delete["response"]["status"] == 204

    def test_search_response_has_required_fields(self, pact_data):
        search = next(
            i for i in pact_data["interactions"]
            if i["request"]["method"] == "POST"
            and i["request"]["path"] == "/api/v1/multimodal/search"
            and i["response"]["status"] == 200
        )
        body = search["response"]["body"]
        required = {"items", "total", "query_processed", "search_mode"}
        assert required.issubset(body.keys())

    def test_paginated_list_response_has_pagination(self, pact_data):
        paginated = next(
            i for i in pact_data["interactions"]
            if i["request"]["path"] == "/api/v1/multimodal/list"
        )
        body = paginated["response"]["body"]
        assert "pagination" in body
        pagination = body["pagination"]
        required = {"total", "page", "page_size", "total_pages", "has_next", "has_prev"}
        assert required.issubset(pagination.keys())

    def test_upload_response_has_required_fields(self, pact_data):
        upload = next(
            i for i in pact_data["interactions"]
            if i["request"]["path"] == "/api/v1/multimodal/upload"
        )
        body = upload["response"]["body"]
        assert "content" in body
        content = body["content"]
        required = {"id", "media_type", "file_path", "related_concept_id", "created_at"}
        assert required.issubset(content.keys())
        assert "message" in body
        assert "thumbnail_generated" in body

    def test_upload_url_response_has_required_fields(self, pact_data):
        upload_url = next(
            i for i in pact_data["interactions"]
            if i["request"]["path"] == "/api/v1/multimodal/upload-url"
        )
        body = upload_url["response"]["body"]
        assert "content" in body
        assert "message" in body

    def test_by_concept_response_has_required_fields(self, pact_data):
        by_concept = next(
            i for i in pact_data["interactions"]
            if "by-concept" in i["request"]["path"]
        )
        body = by_concept["response"]["body"]
        required = {"items", "total"}
        assert required.issubset(body.keys())
