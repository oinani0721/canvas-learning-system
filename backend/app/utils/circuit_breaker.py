# EPIC-34 NFR P1: Circuit breaker for Graphiti client
# Prevents repeated timeout failures when Graphiti becomes unavailable.
#
# States:
#   CLOSED   — normal operation, calls pass through
#   OPEN     — after N consecutive failures, skip calls for recovery_timeout
#   HALF_OPEN — after recovery timeout, allow one probe call
"""
Simple circuit breaker for external service calls.

Usage:
    breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60.0)

    if breaker.allow_request():
        try:
            result = await external_call()
            breaker.record_success()
        except Exception:
            breaker.record_failure()
            # fallback
"""

import logging
import time
from enum import Enum
from threading import Lock

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Thread-safe circuit breaker for external service calls.

    Args:
        name: Human-readable name for logging
        failure_threshold: Consecutive failures before opening circuit
        recovery_timeout: Seconds to wait before allowing a probe call
    """

    def __init__(
        self,
        name: str = "default",
        failure_threshold: int = 3,
        recovery_timeout: float = 60.0,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: float = 0.0
        self._lock = Lock()

    @property
    def state(self) -> CircuitState:
        with self._lock:
            if self._state == CircuitState.OPEN:
                if time.monotonic() - self._last_failure_time >= self.recovery_timeout:
                    self._state = CircuitState.HALF_OPEN
                    logger.info(
                        f"CircuitBreaker[{self.name}]: OPEN -> HALF_OPEN "
                        f"(recovery timeout {self.recovery_timeout}s elapsed)"
                    )
            return self._state

    def allow_request(self) -> bool:
        """Check if a request should be allowed through.

        Returns True for CLOSED and HALF_OPEN states, False for OPEN.
        """
        current = self.state
        if current == CircuitState.OPEN:
            logger.debug(
                f"CircuitBreaker[{self.name}]: request blocked (OPEN, "
                f"{self._failure_count} consecutive failures)"
            )
            return False
        return True

    def record_success(self) -> None:
        """Record a successful call. Resets failure count and closes circuit."""
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                logger.info(
                    f"CircuitBreaker[{self.name}]: HALF_OPEN -> CLOSED (probe succeeded)"
                )
            self._failure_count = 0
            self._state = CircuitState.CLOSED

    def record_failure(self) -> None:
        """Record a failed call. Opens circuit after threshold consecutive failures."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.monotonic()

            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
                logger.warning(
                    f"CircuitBreaker[{self.name}]: HALF_OPEN -> OPEN "
                    f"(probe failed, waiting {self.recovery_timeout}s)"
                )
            elif self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                logger.warning(
                    f"CircuitBreaker[{self.name}]: CLOSED -> OPEN "
                    f"({self._failure_count} consecutive failures, "
                    f"waiting {self.recovery_timeout}s)"
                )

    def reset(self) -> None:
        """Manually reset the circuit breaker to closed state."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._last_failure_time = 0.0
            logger.info(f"CircuitBreaker[{self.name}]: manually reset to CLOSED")
