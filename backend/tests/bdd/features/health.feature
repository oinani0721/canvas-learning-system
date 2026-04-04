Feature: System Health Check
  As a system operator
  I want to verify the Canvas Learning System is healthy
  So that I can detect failures early

  Scenario: Basic health check
    Given the API server is running
    When I request the health endpoint
    Then the response status is 200
    And the response contains status "healthy"

  Scenario: Health check includes components
    Given the API server is running
    When I request the health endpoint
    Then the response contains component status
