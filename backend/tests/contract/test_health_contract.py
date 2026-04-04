"""Contract tests for health endpoints using Schemathesis.

Verifies API behavior matches OpenAPI specification.
Uses from_asgi for in-process testing (no server needed).
"""

import pytest

schemathesis = pytest.importorskip("schemathesis", reason="schemathesis not installed")

from hypothesis import Phase, settings

from app.main import app

# Load schema filtered to health endpoint only
schema = schemathesis.openapi.from_asgi("/api/v1/openapi.json", app).include(
    path="/api/v1/health"
)


@schema.parametrize()
@settings(
    max_examples=5,
    phases=[Phase.explicit, Phase.generate],
    deadline=10000,
)
def test_health_contract(case):
    """Health endpoint matches its OpenAPI spec."""
    case.call_and_validate(
        checks=(
            schemathesis.checks.status_code_conformance,
            schemathesis.checks.content_type_conformance,
            schemathesis.checks.response_headers_conformance,
            schemathesis.checks.response_schema_conformance,
        )
    )
