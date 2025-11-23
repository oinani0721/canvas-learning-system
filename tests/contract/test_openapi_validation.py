"""
OpenAPI Contract Validation Tests

验证Canvas Learning System的OpenAPI规范正确性和一致性。
当FastAPI实现后，这些测试将验证实际API符合规范。

OpenAPI specs tested:
- canvas-api.openapi.yml
- agent-api.openapi.yml
"""

import pytest
import yaml
from pathlib import Path
from openapi_spec_validator import validate_spec
from openapi_spec_validator.exceptions import OpenAPIValidationError

# API spec directory
API_SPEC_DIR = Path(__file__).parent.parent.parent / "specs" / "api"


class TestOpenAPISpecValidity:
    """Test that all OpenAPI specs are valid"""

    def test_canvas_api_spec_is_valid(self):
        """canvas-api.openapi.yml should be valid OpenAPI 3.0"""
        spec_path = API_SPEC_DIR / "canvas-api.openapi.yml"
        with open(spec_path, 'r', encoding='utf-8') as f:
            spec = yaml.safe_load(f)

        # This will raise if invalid
        validate_spec(spec)

    def test_agent_api_spec_is_valid(self):
        """agent-api.openapi.yml should be valid OpenAPI 3.0"""
        spec_path = API_SPEC_DIR / "agent-api.openapi.yml"
        if not spec_path.exists():
            pytest.skip("agent-api.openapi.yml not found")

        with open(spec_path, 'r', encoding='utf-8') as f:
            spec = yaml.safe_load(f)

        validate_spec(spec)


class TestOpenAPIMetadata:
    """Test OpenAPI spec metadata requirements"""

    @pytest.fixture
    def canvas_api_spec(self):
        spec_path = API_SPEC_DIR / "canvas-api.openapi.yml"
        with open(spec_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def test_has_info_section(self, canvas_api_spec):
        """Spec should have info section with title, version, description"""
        assert "info" in canvas_api_spec
        assert "title" in canvas_api_spec["info"]
        assert "version" in canvas_api_spec["info"]
        assert "description" in canvas_api_spec["info"]

    def test_has_servers_section(self, canvas_api_spec):
        """Spec should have servers section"""
        assert "servers" in canvas_api_spec
        assert len(canvas_api_spec["servers"]) > 0

    def test_has_paths_section(self, canvas_api_spec):
        """Spec should have paths section"""
        assert "paths" in canvas_api_spec
        assert len(canvas_api_spec["paths"]) > 0

    def test_version_is_semver(self, canvas_api_spec):
        """Version should follow semantic versioning"""
        version = canvas_api_spec["info"]["version"]
        parts = version.split(".")
        assert len(parts) == 3, f"Version {version} should be MAJOR.MINOR.PATCH"


class TestOpenAPIEndpoints:
    """Test OpenAPI endpoint definitions"""

    @pytest.fixture
    def canvas_api_spec(self):
        spec_path = API_SPEC_DIR / "canvas-api.openapi.yml"
        with open(spec_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def test_all_endpoints_have_operation_id(self, canvas_api_spec):
        """All endpoints should have operationId"""
        paths = canvas_api_spec["paths"]
        for path, methods in paths.items():
            for method, operation in methods.items():
                if method in ["get", "post", "put", "delete", "patch"]:
                    assert "operationId" in operation, \
                        f"{method.upper()} {path} missing operationId"

    def test_all_endpoints_have_responses(self, canvas_api_spec):
        """All endpoints should have responses defined"""
        paths = canvas_api_spec["paths"]
        for path, methods in paths.items():
            for method, operation in methods.items():
                if method in ["get", "post", "put", "delete", "patch"]:
                    assert "responses" in operation, \
                        f"{method.upper()} {path} missing responses"

    def test_all_endpoints_have_tags(self, canvas_api_spec):
        """All endpoints should have at least one tag"""
        paths = canvas_api_spec["paths"]
        for path, methods in paths.items():
            for method, operation in methods.items():
                if method in ["get", "post", "put", "delete", "patch"]:
                    assert "tags" in operation, \
                        f"{method.upper()} {path} missing tags"
                    assert len(operation["tags"]) > 0

    def test_layer_tags_exist(self, canvas_api_spec):
        """All four layer tags should be defined"""
        tags = canvas_api_spec.get("tags", [])
        tag_names = [t["name"] for t in tags]

        expected_layers = ["Layer1-JSON", "Layer2-Business", "Layer3-Orchestrator", "Layer4-Knowledge"]
        for layer in expected_layers:
            assert layer in tag_names, f"Missing tag: {layer}"


class TestOpenAPISchemas:
    """Test OpenAPI component schemas"""

    @pytest.fixture
    def canvas_api_spec(self):
        spec_path = API_SPEC_DIR / "canvas-api.openapi.yml"
        with open(spec_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def test_has_components_section(self, canvas_api_spec):
        """Spec should have components section"""
        assert "components" in canvas_api_spec

    def test_has_schemas_in_components(self, canvas_api_spec):
        """Components should have schemas defined"""
        assert "schemas" in canvas_api_spec.get("components", {})

    def test_core_schemas_exist(self, canvas_api_spec):
        """Core schemas should be defined"""
        schemas = canvas_api_spec.get("components", {}).get("schemas", {})

        core_schemas = ["CanvasData", "CanvasNode", "NodeInput"]
        for schema_name in core_schemas:
            assert schema_name in schemas, f"Missing schema: {schema_name}"

    def test_all_refs_are_valid(self, canvas_api_spec):
        """All $ref references should point to existing schemas"""
        schemas = canvas_api_spec.get("components", {}).get("schemas", {})

        def find_refs(obj, path=""):
            refs = []
            if isinstance(obj, dict):
                if "$ref" in obj:
                    refs.append((path, obj["$ref"]))
                for key, value in obj.items():
                    refs.extend(find_refs(value, f"{path}/{key}"))
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    refs.extend(find_refs(item, f"{path}[{i}]"))
            return refs

        all_refs = find_refs(canvas_api_spec)

        for path, ref in all_refs:
            if ref.startswith("#/components/schemas/"):
                schema_name = ref.split("/")[-1]
                assert schema_name in schemas, \
                    f"Invalid $ref at {path}: {ref} (schema {schema_name} not found)"


class TestOpenAPIColorEnum:
    """Test color enum consistency across specs"""

    @pytest.fixture
    def canvas_api_spec(self):
        spec_path = API_SPEC_DIR / "canvas-api.openapi.yml"
        with open(spec_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def test_color_enum_values(self, canvas_api_spec):
        """Color enum should only contain valid values: 1, 2, 3, 5, 6"""
        valid_colors = ["1", "2", "3", "5", "6"]

        # Find color parameters in paths
        paths = canvas_api_spec["paths"]
        for path, methods in paths.items():
            for method, operation in methods.items():
                if "parameters" in operation:
                    for param in operation["parameters"]:
                        if param.get("name") == "color":
                            if "enum" in param.get("schema", {}):
                                enum_values = param["schema"]["enum"]
                                for val in enum_values:
                                    assert val in valid_colors, \
                                        f"Invalid color value {val} in {method.upper()} {path}"


# ============================================================================
# Schemathesis Tests (for when FastAPI is implemented)
# ============================================================================

class TestSchemathesisReadiness:
    """Tests to verify Schemathesis can be used with this spec"""

    def test_schemathesis_can_load_spec(self):
        """Schemathesis should be able to load the OpenAPI spec"""
        try:
            import schemathesis
        except ImportError:
            pytest.skip("Schemathesis not installed")

        spec_path = API_SPEC_DIR / "canvas-api.openapi.yml"

        # This will raise if spec is incompatible with Schemathesis
        schema = schemathesis.from_path(str(spec_path))
        assert schema is not None


# ============================================================================
# Contract Testing Framework (for FastAPI integration)
# ============================================================================

class TestContractTestingFramework:
    """
    Framework for testing actual API against OpenAPI spec.

    When FastAPI is implemented (Epic 11), uncomment these tests and
    replace BASE_URL with actual server URL.

    Usage:
        1. Start FastAPI server: uvicorn main:app
        2. Run tests: pytest tests/contract/test_openapi_validation.py -k "contract" -v
    """

    # BASE_URL = "http://localhost:8000/api/v2"

    @pytest.mark.skip(reason="FastAPI not implemented yet - Epic 11")
    def test_contract_read_canvas(self):
        """
        Contract test: GET /canvas/{canvas_path}

        Validates that actual API response matches OpenAPI spec schema.
        """
        # import requests
        # from jsonschema import validate
        #
        # response = requests.get(f"{self.BASE_URL}/canvas/test.canvas")
        # assert response.status_code == 200
        #
        # # Load expected schema from OpenAPI spec
        # spec_path = API_SPEC_DIR / "canvas-api.openapi.yml"
        # with open(spec_path, 'r') as f:
        #     spec = yaml.safe_load(f)
        #
        # canvas_schema = spec["components"]["schemas"]["CanvasData"]
        # validate(instance=response.json(), schema=canvas_schema)
        pass

    @pytest.mark.skip(reason="FastAPI not implemented yet - Epic 11")
    def test_contract_add_node(self):
        """
        Contract test: POST /canvas/{canvas_path}/nodes

        Validates request/response against OpenAPI spec.
        """
        pass

    @pytest.mark.skip(reason="FastAPI not implemented yet - Epic 11")
    def test_contract_get_nodes_by_color(self):
        """
        Contract test: GET /canvas/{canvas_path}/nodes/by-color/{color}

        Validates Layer 2 business logic endpoint.
        """
        pass
