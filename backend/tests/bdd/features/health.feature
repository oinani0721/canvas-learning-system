# [BATCH-2026-09-01-第九批 / CARD-TEST-isolate-lifespan-R1]
# 诚实边界说明见 tests/bdd/test_health_bdd.py 的模块 docstring：
# 这里用的是 lifespan-free 的根 client fixture，只承诺 route-availability。
Feature: Health route contract
  As a backend developer
  I want the health route to be mounted and to answer per its response contract
  So that a broken route table or response schema is caught by the unit suite

  Scenario: Basic health check
    Given the health route is mounted on a lifespan-free test client
    When I request the health endpoint
    Then the response status is 200
    And the response contains status "healthy"

  Scenario: Health check includes components
    Given the health route is mounted on a lifespan-free test client
    When I request the health endpoint
    Then the response contains component status
