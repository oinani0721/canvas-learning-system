"""
Unit Tests for Story 31.A.1: Backend Dependency Injection Fix

Tests for:
- AC-31.A.1.1: get_verification_service() injects graphiti_client
- AC-31.A.1.2: VerificationService constructor validates graphiti_client
- AC-31.A.1.3: search_verification_questions() calls succeed
- AC-31.A.1.4: Unit test coverage for injection chain

[Source: docs/stories/31.A.1.story.md#Testing]
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.services.verification_service import VerificationService


class TestVerificationServiceInjection:
    """
    Test VerificationService dependency injection (Story 31.A.1).

    [Source: docs/stories/31.A.1.story.md#AC-31.A.1.1]
    """

    @pytest.fixture
    def mock_rag_service(self):
        """Create mock RAGService."""
        service = MagicMock()
        service.query = AsyncMock(return_value={"learning_history": "test"})
        return service

    @pytest.mark.asyncio
    async def test_verification_service_receives_graphiti_client(
        self, mock_graphiti_client
    ):
        """
        AC-31.A.1.1: VerificationService correctly receives graphiti_client.

        Verifies that when graphiti_client is passed to constructor,
        it is stored in self._graphiti_client.

        [Source: docs/stories/31.A.1.story.md#AC-31.A.1.1]
        """
        # Arrange & Act
        service = VerificationService(graphiti_client=mock_graphiti_client)

        # Assert
        assert service._graphiti_client is not None
        assert service._graphiti_client is mock_graphiti_client

    @pytest.mark.asyncio
    async def test_verification_service_without_graphiti_client(self):
        """
        AC-31.A.1.2: VerificationService handles graphiti_client=None gracefully.

        Verifies that service can be created without graphiti_client
        (graceful degradation).

        [Source: docs/stories/31.A.1.story.md#AC-31.A.1.2]
        """
        # Arrange & Act
        service = VerificationService(graphiti_client=None)

        # Assert: Service created successfully with None client
        assert service._graphiti_client is None


class TestDependenciesInjection:
    """
    Test get_verification_service dependency injection chain (Story 31.A.1).

    [Source: docs/stories/31.A.1.story.md#AC-31.A.1.1]
    """

    @pytest.mark.asyncio
    async def test_get_verification_service_injects_graphiti_client(self):
        """
        AC-31.A.1.1: get_verification_service() calls get_graphiti_temporal_client().

        Verifies that the dependency function retrieves and injects
        the GraphitiTemporalClient.

        [Source: docs/stories/31.A.1.story.md#AC-31.A.1.1]
        """
        from unittest.mock import AsyncMock, MagicMock

        # Create mock graphiti client
        mock_client = AsyncMock()
        mock_client.search_verification_questions = AsyncMock(return_value=[])

        # Mock all required dependencies
        with (
            patch(
                # 契约演进 5d2b95ba (2026-03-29 S34 G-FAKE-001)：单例 getter 重命名为
                # get_neo4j_temporal_client，旧名仅存为模块级别名（dependencies.py:819）。
                # get_verification_service（dependencies.py:508）调的是**新名**，
                # patch 打在别名上只是重绑了第二个 module global，生产从不读它。
                # [CARD-RED-C2]
                "app.dependencies.get_neo4j_temporal_client",
                return_value=mock_client,
            ) as mock_get_graphiti,
            patch("app.dependencies.get_rag_service", return_value=MagicMock()),
            # 第二根因（与改名无关、基线时即并存）：get_verification_service 自
            # 14f0412d (2026-02-07) 起在同一工厂里 `await _get_memory_svc()`，
            # 真 MemoryService.initialize() 会对现网 7691 发健康检查；32c8e325
            # (2026-09-05 W4 安全底座) 把「测试进程碰现网端口」从静默变成用例失败，
            # 于是这条单测被哨兵判红。按哨兵自身给的处方隔离该依赖——
            # 不放宽下面两条断言，本用例要验的仍是「工厂调了 getter 且把它注进服务」。
            # 实测：只打这一处即可让 NEO4J_LIVE_PORT_CONNECT_ATTEMPTS 由 1 归 0
            # （get_neo4j_client_dep() 只构造不健康检查，不产生连接尝试）。[CARD-RED-C2]
            patch(
                "app.services.memory_service.get_memory_service",
                new=AsyncMock(return_value=MagicMock()),
            ),
        ):
            # Import after patching to get patched version
            from app.dependencies import get_verification_service

            # Create mock settings and canvas_service
            mock_settings = MagicMock()
            mock_settings.canvas_base_path = "/test/path"
            mock_canvas_service = MagicMock()

            # Execute the generator (requires settings + canvas_service)
            gen = get_verification_service(mock_settings, mock_canvas_service)
            service = await gen.__anext__()

            # Assert: get_graphiti_temporal_client was called
            mock_get_graphiti.assert_called_once()

            # Assert: graphiti_client was injected
            assert service._graphiti_client is mock_client

            # Cleanup
            try:
                await gen.aclose()
            except StopAsyncIteration:
                pass


class TestGraphitiClientLogging:
    """
    Test GraphitiTemporalClient initialization logging (AC-31.A.1.2).

    [Source: docs/stories/31.A.1.story.md#AC-31.A.1.2]
    """

    @pytest.mark.asyncio
    async def test_verification_service_logs_graphiti_status_when_present(self, caplog):
        """
        AC-31.A.1.2: Log shows Graphiti: True when client is injected.

        [Source: docs/stories/31.A.1.story.md#AC-31.A.1.2]
        """
        import logging

        # Arrange
        mock_client = AsyncMock()

        # Act
        with caplog.at_level(logging.INFO):
            VerificationService(graphiti_client=mock_client)

        # Assert: Log contains Graphiti: True
        assert "Graphiti: True" in caplog.text

    @pytest.mark.asyncio
    async def test_verification_service_logs_graphiti_status_when_absent(self, caplog):
        """
        AC-31.A.1.2: Log shows Graphiti: False when client is None.

        [Source: docs/stories/31.A.1.story.md#AC-31.A.1.2]
        """
        import logging

        # Act
        with caplog.at_level(logging.INFO):
            VerificationService(graphiti_client=None)

        # Assert: Log contains Graphiti: False
        assert "Graphiti: False" in caplog.text
