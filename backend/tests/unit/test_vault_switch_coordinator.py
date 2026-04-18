"""Tests for Story 1.8 AC #6, #7: VaultSwitchCoordinator.

Covers state transitions, 503 during switch, and request tracking.
"""

import asyncio

import pytest

from app.services.vault_switch_coordinator import SwitchState, VaultSwitchCoordinator


@pytest.fixture
def coordinator():
    return VaultSwitchCoordinator()


class TestCoordinatorState:
    def test_initial_state_is_idle(self, coordinator):
        assert coordinator.state == SwitchState.IDLE
        assert not coordinator.is_switching

    @pytest.mark.asyncio
    async def test_switch_transitions_back_to_idle(self, coordinator):
        async def noop():
            pass

        result = await coordinator.switch("/tmp/v", "v", noop)
        assert coordinator.state == SwitchState.IDLE
        assert result["vault_name"] == "v"
        assert result["duration_ms"] >= 0

    @pytest.mark.asyncio
    async def test_switch_records_previous_vault(self, coordinator):
        async def noop():
            pass

        await coordinator.switch("/tmp/a", "a", noop)
        result = await coordinator.switch("/tmp/b", "b", noop)
        assert result["previous_vault"] == "a"
        assert coordinator.current_vault == "b"

    @pytest.mark.asyncio
    async def test_switch_error_restores_idle(self, coordinator):
        async def fail():
            raise ValueError("boom")

        with pytest.raises(ValueError, match="boom"):
            await coordinator.switch("/tmp/x", "x", fail)

        assert coordinator.state == SwitchState.IDLE


class TestRequestTracking:
    def test_track_start_end(self, coordinator):
        coordinator.track_request_start()
        assert coordinator._active_requests == 1
        coordinator.track_request_end()
        assert coordinator._active_requests == 0

    def test_end_never_goes_negative(self, coordinator):
        coordinator.track_request_end()
        assert coordinator._active_requests == 0


class TestConcurrentSwitch:
    @pytest.mark.asyncio
    async def test_concurrent_switch_raises(self, coordinator):
        barrier = asyncio.Event()

        async def slow_switch():
            await barrier.wait()

        task = asyncio.create_task(coordinator.switch("/tmp/a", "a", slow_switch))
        await asyncio.sleep(0.01)

        with pytest.raises(RuntimeError, match="already in progress"):
            await coordinator.switch("/tmp/b", "b", slow_switch)

        barrier.set()
        await task
