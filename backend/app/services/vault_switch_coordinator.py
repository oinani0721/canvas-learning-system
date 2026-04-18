"""Vault switch coordinator — graceful request handling during vault transitions.

Story 1.8 AC #6, #7: State machine ensures in-flight requests complete before
switching, and new requests get 503 during the transition window.
"""

import asyncio
import time
from enum import Enum
from typing import Any, Awaitable, Callable, Optional

import structlog

logger = structlog.get_logger(__name__)


class SwitchState(str, Enum):
    IDLE = "idle"
    SWITCHING = "switching"


class VaultSwitchCoordinator:
    """Coordinates vault switching with graceful request handling."""

    def __init__(self) -> None:
        self._state = SwitchState.IDLE
        self._active_requests = 0
        self._lock = asyncio.Lock()
        self._previous_vault: Optional[str] = None
        self._current_vault: Optional[str] = None
        self._switched_at: Optional[float] = None

    @property
    def state(self) -> SwitchState:
        return self._state

    @property
    def is_switching(self) -> bool:
        return self._state == SwitchState.SWITCHING

    @property
    def current_vault(self) -> Optional[str]:
        return self._current_vault

    @property
    def previous_vault(self) -> Optional[str]:
        return self._previous_vault

    @property
    def switched_at(self) -> Optional[float]:
        return self._switched_at

    def track_request_start(self) -> None:
        self._active_requests += 1

    def track_request_end(self) -> None:
        self._active_requests = max(0, self._active_requests - 1)

    async def switch(
        self,
        new_vault_path: str,
        new_vault_name: str,
        perform_switch: Callable[[], Awaitable[Any]],
    ) -> dict:
        """Execute vault switch with coordination.

        Waits for active requests to drain (max 5s), then calls perform_switch.
        """
        async with self._lock:
            if self._state == SwitchState.SWITCHING:
                raise RuntimeError("Another vault switch is already in progress")
            self._previous_vault = self._current_vault
            self._state = SwitchState.SWITCHING

        start_time = time.monotonic()

        try:
            deadline = time.monotonic() + 5.0
            while self._active_requests > 0 and time.monotonic() < deadline:
                await asyncio.sleep(0.05)

            await perform_switch()

            self._current_vault = new_vault_name
            self._switched_at = time.time()
            self._state = SwitchState.IDLE

            duration_ms = (time.monotonic() - start_time) * 1000
            logger.info(
                "vault.switched",
                from_vault=self._previous_vault or "(none)",
                to_vault=new_vault_name,
                duration_ms=round(duration_ms, 1),
            )

            return {
                "vault_path": new_vault_path,
                "vault_name": new_vault_name,
                "switched_at": self._switched_at,
                "previous_vault": self._previous_vault,
                "duration_ms": round(duration_ms, 1),
            }
        except Exception:
            self._state = SwitchState.IDLE
            raise


vault_switch_coordinator = VaultSwitchCoordinator()
