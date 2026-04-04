"""BDD tests for health check feature.

Uses pytest-bdd to execute Gherkin scenarios.
"""

import pytest
from pytest_bdd import given, parsers, scenario, then, when

pytestmark = pytest.mark.bdd


@scenario("features/health.feature", "Basic health check")
def test_basic_health():
    pass


@scenario("features/health.feature", "Health check includes components")
def test_health_components():
    pass


@given("the API server is running", target_fixture="api_client")
def api_running(client):
    return client


@when("I request the health endpoint", target_fixture="response")
def request_health(api_client):
    return api_client.get("/api/v1/health")


@then(parsers.parse("the response status is {status:d}"))
def check_status(response, status):
    assert response.status_code == status


@then(parsers.parse('the response contains status "{expected_status}"'))
def check_health_status(response, expected_status):
    data = response.json()
    assert data["status"] == expected_status


@then("the response contains component status")
def check_components(response):
    data = response.json()
    if "components" in data:
        assert isinstance(data["components"], dict)
