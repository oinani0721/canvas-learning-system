# Canvas Learning System - MemoryService Singleton Unity Test
# Verifies AC-6: different endpoints get the SAME MemoryService instance
"""
Integration test that verifies all code paths obtain the same
MemoryService singleton from app.services.memory_service.

AC-6: 不同端点拿到的是同一个 MemoryService 实例

Test Strategy:
1. Reset singleton → call get_memory_service() from multiple import paths
2. Verify object identity (id()) is the same
3. Verify no stale references to the old endpoints.memory singleton remain
"""

from unittest.mock import AsyncMock, patch

import pytest

import app.services.memory_service as mem_module


@pytest.fixture(autouse=True)
def _isolate_singleton():
    """Reset the singleton before and after each test."""
    original = mem_module._memory_service_instance
    mem_module._memory_service_instance = None
    yield
    mem_module._memory_service_instance = original


class TestSingletonUnity:
    """All import paths resolve to the same MemoryService instance."""

    @pytest.mark.asyncio
    async def test_services_get_memory_service_returns_singleton(self):
        """get_memory_service() returns the same instance on repeated calls."""
        with patch.object(mem_module, 'MemoryService') as MockCls:
            inst = AsyncMock()
            inst._initialized = False
            inst.initialize = AsyncMock(
                side_effect=lambda: setattr(inst, '_initialized', True)
            )
            MockCls.return_value = inst

            svc1 = await mem_module.get_memory_service()
            svc2 = await mem_module.get_memory_service()

            assert svc1 is svc2, "Must return the same singleton instance"
            assert id(svc1) == id(svc2)
            inst.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_memory_endpoint_dep_uses_service_singleton(self):
        """endpoints/memory.py MemoryServiceDep resolves to service-layer singleton."""
        from app.api.v1.endpoints.memory import get_memory_service as ep_get

        # ep_get IS the service-layer function (re-exported)
        assert ep_get is mem_module.get_memory_service, (
            "endpoints/memory.py must re-export get_memory_service from services"
        )

    @pytest.mark.asyncio
    async def test_agents_endpoint_dep_uses_service_singleton(self):
        """endpoints/agents.py MemoryServiceDep resolves to service-layer singleton."""
        from app.api.v1.endpoints.agents import get_memory_service as ag_get

        # ag_get IS the service-layer function (direct import)
        assert ag_get is mem_module.get_memory_service, (
            "endpoints/agents.py must import get_memory_service from services"
        )

    @pytest.mark.asyncio
    async def test_main_uses_service_singleton(self):
        """main.py imports get_memory_service from service layer."""
        from app.main import get_memory_service as main_get

        assert main_get is mem_module.get_memory_service, (
            "main.py must import get_memory_service from services"
        )

    @pytest.mark.asyncio
    async def test_main_cleanup_uses_service_cleanup(self):
        """main.py imports cleanup_memory_service from service layer."""
        from app.main import cleanup_memory_service as main_cleanup

        assert main_cleanup is mem_module.cleanup_memory_service, (
            "main.py must import cleanup_memory_service from services"
        )

    @pytest.mark.asyncio
    async def test_cross_endpoint_same_instance(self):
        """Calling singleton from different import paths yields identical object."""
        with patch.object(mem_module, 'MemoryService') as MockCls:
            inst = AsyncMock()
            inst._initialized = False
            inst.initialize = AsyncMock(
                side_effect=lambda: setattr(inst, '_initialized', True)
            )
            MockCls.return_value = inst

            # Import from three different paths
            from app.services.memory_service import get_memory_service as svc_get
            from app.api.v1.endpoints.memory import get_memory_service as ep_get
            from app.api.v1.endpoints.agents import get_memory_service as ag_get

            svc = await svc_get()
            ep = await ep_get()
            ag = await ag_get()

            assert svc is ep, "Service and memory endpoint must share instance"
            assert svc is ag, "Service and agents endpoint must share instance"
            assert id(svc) == id(ep) == id(ag)

    def test_no_stale_singleton_in_endpoints_memory(self):
        """endpoints/memory.py must NOT define its own _memory_service_instance."""
        import app.api.v1.endpoints.memory as ep_mod

        assert not hasattr(ep_mod, '_memory_service_instance'), (
            "endpoints/memory.py must not have its own _memory_service_instance; "
            "singleton lives only in services/memory_service.py"
        )

    def test_no_per_request_factory_in_agents(self):
        """endpoints/agents.py must NOT have get_memory_service_for_agents."""
        import app.api.v1.endpoints.agents as ag_mod

        assert not hasattr(ag_mod, 'get_memory_service_for_agents'), (
            "endpoints/agents.py must not have get_memory_service_for_agents; "
            "use get_memory_service from services layer instead"
        )

    @pytest.mark.asyncio
    async def test_reset_clears_singleton(self):
        """reset_memory_service() clears the singleton for test isolation."""
        with patch.object(mem_module, 'MemoryService') as MockCls:
            inst = AsyncMock()
            inst._initialized = False
            inst.initialize = AsyncMock(
                side_effect=lambda: setattr(inst, '_initialized', True)
            )
            MockCls.return_value = inst

            svc1 = await mem_module.get_memory_service()
            assert svc1 is inst

            # Reset
            mem_module.reset_memory_service()
            assert mem_module._memory_service_instance is None

            # New instance should be created
            inst2 = AsyncMock()
            inst2._initialized = False
            inst2.initialize = AsyncMock(
                side_effect=lambda: setattr(inst2, '_initialized', True)
            )
            MockCls.return_value = inst2

            svc2 = await mem_module.get_memory_service()
            assert svc2 is inst2
            assert svc2 is not svc1
