"""
Schemathesis Contract Testing for Canvas Learning System API

This module uses Schemathesis to automatically generate test cases from
the OpenAPI specification and validate API responses against the schema.

Requirements:
- pip install schemathesis hypothesis
- FastAPI server running (Epic 15)

Usage:
- Run all tests: pytest tests/contract/test_schemathesis_api.py -v
- Run with markers: pytest -m contract -v
- CLI: schemathesis run specs/api/canvas-api.openapi.yml --base-url http://localhost:8000

Reference: docs/architecture/sot-hierarchy.md (OpenAPI is Level 4 SoT)
"""

import pytest
from pathlib import Path

# Mark all tests in this module as contract tests
pytestmark = pytest.mark.contract

# OpenAPI spec path
OPENAPI_SPEC_PATH = Path(__file__).parent.parent.parent / "specs" / "api" / "canvas-api.openapi.yml"

# Skip all tests if FastAPI is not available (Epic 15 not yet implemented)
# Remove this skip when Epic 15 is complete
FASTAPI_NOT_READY = True
SKIP_REASON = "FastAPI backend not yet implemented (Epic 15). Enable tests after Epic 15 completion."


@pytest.fixture
def api_schema():
    """Load OpenAPI schema for testing."""
    try:
        import schemathesis
        if not OPENAPI_SPEC_PATH.exists():
            pytest.skip(f"OpenAPI spec not found: {OPENAPI_SPEC_PATH}")
        return schemathesis.openapi.from_path(str(OPENAPI_SPEC_PATH))
    except ImportError:
        pytest.skip("schemathesis not installed. Run: pip install schemathesis")


@pytest.mark.skipif(FASTAPI_NOT_READY, reason=SKIP_REASON)
class TestAPICompliance:
    """
    Test API compliance with OpenAPI specification.

    These tests validate that the FastAPI implementation matches
    the OpenAPI contract defined in specs/api/canvas-api.openapi.yml.

    SoT Hierarchy: Code (Level 6) must comply with OpenAPI (Level 4)
    """

    def test_openapi_spec_exists(self):
        """Verify OpenAPI spec file exists and is valid."""
        assert OPENAPI_SPEC_PATH.exists(), f"OpenAPI spec not found: {OPENAPI_SPEC_PATH}"

        # Basic YAML validation
        import yaml
        with open(OPENAPI_SPEC_PATH, 'r', encoding='utf-8') as f:
            spec = yaml.safe_load(f)

        assert 'openapi' in spec, "Missing 'openapi' version field"
        assert 'info' in spec, "Missing 'info' section"
        assert 'paths' in spec, "Missing 'paths' section"

    def test_all_endpoints_compliance(self, api_schema):
        """
        Test all API endpoints against OpenAPI spec.

        Schemathesis automatically generates test cases for:
        - All defined endpoints
        - All HTTP methods
        - All parameter combinations
        - Edge cases and boundary values
        """
        # This would be used with pytest-schemathesis plugin
        # For now, we'll use a simpler approach
        pass


@pytest.mark.skipif(FASTAPI_NOT_READY, reason=SKIP_REASON)
class TestCriticalEndpoints:
    """
    Manual contract tests for critical API endpoints.

    These tests provide explicit coverage for the most important
    API contracts, complementing Schemathesis auto-generation.
    """

    def test_health_check_endpoint(self):
        """
        Test GET /api/health returns correct schema.

        Expected: 200 OK with health status
        Reference: specs/api/canvas-api.openapi.yml#/paths/~1api~1health
        """
        # TODO: Implement after Epic 15
        # response = client.get("/api/health")
        # assert response.status_code == 200
        # assert "status" in response.json()
        pass

    def test_nodes_endpoint_post(self):
        """
        Test POST /api/nodes creates node with correct response.

        Expected: 201 Created with node data
        Reference: specs/api/canvas-api.openapi.yml#/paths/~1api~1nodes
        """
        # TODO: Implement after Epic 15
        pass

    def test_decompose_endpoint(self):
        """
        Test POST /api/decompose returns decomposition result.

        Expected: 200 OK with decomposed nodes
        Reference: specs/api/canvas-api.openapi.yml#/paths/~1api~1decompose
        """
        # TODO: Implement after Epic 15
        pass


class TestSchemaReferences:
    """
    Test that OpenAPI spec correctly references JSON Schemas.

    SoT Hierarchy: OpenAPI (Level 4) must correctly reference Schema (Level 3)
    """

    def test_schema_refs_valid(self):
        """Verify all $ref in OpenAPI point to existing schema files."""
        if not OPENAPI_SPEC_PATH.exists():
            pytest.skip(f"OpenAPI spec not found: {OPENAPI_SPEC_PATH}")

        import yaml
        import re

        with open(OPENAPI_SPEC_PATH, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find all $ref patterns
        refs = re.findall(r'\$ref:\s*[\'"]?([^\'"}\s]+)[\'"]?', content)

        for ref in refs:
            # Skip internal references
            if ref.startswith('#'):
                continue

            # Check external file references
            if ref.startswith('../data/') or ref.startswith('./'):
                ref_path = OPENAPI_SPEC_PATH.parent / ref
                assert ref_path.exists(), f"Schema reference not found: {ref} -> {ref_path}"

    def test_response_schemas_defined(self):
        """Verify all response schemas are properly defined."""
        if not OPENAPI_SPEC_PATH.exists():
            pytest.skip(f"OpenAPI spec not found: {OPENAPI_SPEC_PATH}")

        import yaml

        with open(OPENAPI_SPEC_PATH, 'r', encoding='utf-8') as f:
            spec = yaml.safe_load(f)

        # Check that paths have response definitions
        for path, methods in spec.get('paths', {}).items():
            for method, details in methods.items():
                if method in ['get', 'post', 'put', 'delete', 'patch']:
                    responses = details.get('responses', {})
                    assert responses, f"No responses defined for {method.upper()} {path}"

                    # Check for success response
                    success_codes = ['200', '201', '204']
                    has_success = any(code in responses for code in success_codes)
                    assert has_success, f"No success response for {method.upper()} {path}"


# Schemathesis parametrized tests (to be enabled after Epic 11)
# Uncomment and modify when FastAPI is ready

"""
import schemathesis

schema = schemathesis.openapi.from_path(str(OPENAPI_SPEC_PATH))

@schema.parametrize()
def test_api(case):
    '''
    Auto-generated test for all API endpoints.

    Schemathesis will:
    1. Generate valid request data based on schema
    2. Send request to API
    3. Validate response matches schema
    4. Check for edge cases and errors
    '''
    response = case.call()
    case.validate_response(response)


@schema.parametrize(endpoint="/api/nodes")
def test_nodes_endpoint(case):
    '''Focused testing on critical nodes endpoint.'''
    response = case.call()
    case.validate_response(response)

    # Additional business logic validation
    if case.method == "POST" and response.status_code == 201:
        data = response.json()
        assert "id" in data, "Created node must have ID"
        assert "type" in data, "Created node must have type"


@schema.parametrize(endpoint="/api/decompose")
def test_decompose_endpoint(case):
    '''Focused testing on decomposition endpoint.'''
    response = case.call()
    case.validate_response(response)


# Stateful testing for multi-step workflows
@schema.as_state_machine()
class APIWorkflows(schemathesis.StatefulTest):
    '''
    Test realistic API workflows:
    - Create node -> Get node -> Update node -> Delete node
    - Create canvas -> Add nodes -> Decompose -> Score
    '''
    pass
"""


if __name__ == "__main__":
    # Quick validation that spec exists
    print(f"OpenAPI spec path: {OPENAPI_SPEC_PATH}")
    print(f"Spec exists: {OPENAPI_SPEC_PATH.exists()}")

    if OPENAPI_SPEC_PATH.exists():
        import yaml
        with open(OPENAPI_SPEC_PATH, 'r', encoding='utf-8') as f:
            spec = yaml.safe_load(f)
        print(f"OpenAPI version: {spec.get('openapi', 'unknown')}")
        print(f"API title: {spec.get('info', {}).get('title', 'unknown')}")
        print(f"Endpoints: {len(spec.get('paths', {}))}")
