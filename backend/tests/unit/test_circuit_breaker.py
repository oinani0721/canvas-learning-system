# EPIC-34 NFR P1: Circuit breaker unit tests
"""
Tests for CircuitBreaker used by ReviewService for Graphiti calls.

Tests cover:
- CLOSED state allows requests
- Opens after consecutive failures
- Blocks requests when OPEN
- Transitions to HALF_OPEN after recovery timeout
- Closes on successful probe
- Reopens on failed probe
- Success resets failure count
- Manual reset
"""

import time
from unittest.mock import patch

import pytest

from app.utils.circuit_breaker import CircuitBreaker, CircuitState


class TestCircuitBreakerStates:
    """Test state transitions of the circuit breaker."""

    def test_initial_state_is_closed(self):
        """Circuit starts in CLOSED state."""
        cb = CircuitBreaker(name="test")
        assert cb.state == CircuitState.CLOSED

    def test_closed_allows_requests(self):
        """CLOSED state allows all requests."""
        cb = CircuitBreaker(name="test")
        assert cb.allow_request() is True

    def test_opens_after_threshold_failures(self):
        """Circuit opens after failure_threshold consecutive failures."""
        cb = CircuitBreaker(name="test", failure_threshold=3)

        cb.record_failure()
        assert cb.state == CircuitState.CLOSED
        cb.record_failure()
        assert cb.state == CircuitState.CLOSED
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

    def test_open_blocks_requests(self):
        """OPEN state blocks requests."""
        cb = CircuitBreaker(name="test", failure_threshold=2)
        cb.record_failure()
        cb.record_failure()

        assert cb.allow_request() is False

    def test_success_resets_failure_count(self):
        """A success resets the consecutive failure counter."""
        cb = CircuitBreaker(name="test", failure_threshold=3)

        cb.record_failure()
        cb.record_failure()
        cb.record_success()  # Reset

        # Need 3 more failures to open (not 1)
        cb.record_failure()
        assert cb.state == CircuitState.CLOSED
        cb.record_failure()
        assert cb.state == CircuitState.CLOSED
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

    def test_transitions_to_half_open_after_timeout(self):
        """OPEN -> HALF_OPEN after recovery timeout."""
        cb = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=0.1)

        cb.record_failure()  # Opens circuit
        assert cb.state == CircuitState.OPEN

        time.sleep(0.15)  # Wait past recovery timeout
        assert cb.state == CircuitState.HALF_OPEN

    def test_half_open_allows_one_request(self):
        """HALF_OPEN allows a probe request."""
        cb = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=0.1)

        cb.record_failure()
        time.sleep(0.15)

        assert cb.allow_request() is True

    def test_half_open_to_closed_on_success(self):
        """HALF_OPEN -> CLOSED when probe succeeds."""
        cb = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=0.1)

        cb.record_failure()
        time.sleep(0.15)

        # Probe (HALF_OPEN)
        assert cb.allow_request() is True
        cb.record_success()

        assert cb.state == CircuitState.CLOSED

    def test_half_open_to_open_on_failure(self):
        """HALF_OPEN -> OPEN when probe fails."""
        cb = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=0.1)

        cb.record_failure()
        time.sleep(0.15)

        # Trigger state transition to HALF_OPEN
        assert cb.state == CircuitState.HALF_OPEN

        # Probe fails
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

    def test_manual_reset(self):
        """Manual reset returns to CLOSED state."""
        cb = CircuitBreaker(name="test", failure_threshold=1)

        cb.record_failure()
        assert cb.state == CircuitState.OPEN

        cb.reset()
        assert cb.state == CircuitState.CLOSED
        assert cb.allow_request() is True


class TestCircuitBreakerIntegrationPattern:
    """Test the usage pattern as it would be in ReviewService."""

    def test_typical_usage_pattern(self):
        """Simulate typical usage: success, then failures, then recovery."""
        cb = CircuitBreaker(name="graphiti", failure_threshold=3, recovery_timeout=0.1)

        # Normal operation
        for _ in range(10):
            assert cb.allow_request() is True
            cb.record_success()

        # Service starts failing
        cb.record_failure()
        cb.record_failure()
        assert cb.allow_request() is True  # Still closed (2 < 3)

        cb.record_failure()
        assert cb.allow_request() is False  # Now open

        # Wait for recovery
        time.sleep(0.15)
        assert cb.allow_request() is True  # Half-open, probe allowed

        # Probe succeeds
        cb.record_success()
        assert cb.allow_request() is True  # Closed again

    def test_custom_thresholds(self):
        """Different thresholds for different use cases."""
        strict = CircuitBreaker(name="strict", failure_threshold=1)
        lenient = CircuitBreaker(name="lenient", failure_threshold=10)

        strict.record_failure()
        assert strict.state == CircuitState.OPEN

        for _ in range(9):
            lenient.record_failure()
        assert lenient.state == CircuitState.CLOSED  # 9 < 10
