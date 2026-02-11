"""
Unit Tests for Story 31.A.1: Backend Dependency Injection Fix

Tests for:
- AC-31.A.1.1: get_verification_service() injects graphiti_client
- AC-31.A.1.2: VerificationService constructor validates graphiti_client
- AC-31.A.1.3: search_verification_questions() calls succeed
- AC-31.A.1.4: Unit test coverage for injection chain

[Source: docs/stories/31.A.1.story.md#Testing]
"""

import asyncio
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.conftest import simulate_async_delay

from app.services.verification_service import VerificationService


class TestVerificationServiceInjection:
    """
    Test VerificationService dependency injection (Story 31.A.1).

    [Source: docs/stories/31.A.1.story.md#AC-31.A.1.1]
    """

    @pytest.fixture
    def mock_graphiti_client(self):
        """Create mock GraphitiTemporalClient."""
        client = AsyncMock()
        client.search_verification_questions = AsyncMock(return_value=[])
        client.add_verification_question = AsyncMock(return_value="vq_test123")
        return client

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

    @pytest.mark.asyncio
    async def test_get_question_history_from_graphiti_calls_client(
        self, mock_graphiti_client
    ):
        """
        AC-31.A.1.3: search_verification_questions() is called when client exists.

        Verifies that _get_question_history_from_graphiti() actually calls the
        graphiti_client's search_verification_questions method.

        [Source: docs/stories/31.A.1.story.md#AC-31.A.1.3]
        """
        # Arrange
        mock_graphiti_client.search_verification_questions.return_value = [
            {
                "question_id": "vq_001",
                "question_text": "What is the contrapositive?",
                "question_type": "standard",
                "asked_at": "2025-01-01T10:00:00Z",
            }
        ]
        service = VerificationService(graphiti_client=mock_graphiti_client)

        # Act
        history = await service._get_question_history_from_graphiti(
            concept="逆否命题",
            canvas_name="离散数学"
        )

        # Assert
        mock_graphiti_client.search_verification_questions.assert_called_once()
        assert len(history) == 1
        assert history[0]["question_id"] == "vq_001"

    @pytest.mark.asyncio
    async def test_get_question_history_returns_empty_when_no_client(self):
        """
        AC-31.A.1.3: Returns empty list when graphiti_client is None.

        Verifies graceful degradation - no AttributeError thrown.

        [Source: docs/stories/31.A.1.story.md#AC-31.A.1.3]
        """
        # Arrange
        service = VerificationService(graphiti_client=None)

        # Act - should not raise AttributeError
        history = await service._get_question_history_from_graphiti(
            concept="test_concept",
            canvas_name="test_canvas"
        )

        # Assert
        assert history == []

    @pytest.mark.asyncio
    async def test_get_question_history_timeout_graceful_degradation(
        self, mock_graphiti_client
    ):
        """
        AC-31.A.1.3: Timeout results in graceful degradation, not error.

        Verifies that timeout returns empty list instead of raising.

        [Source: docs/stories/31.A.1.story.md#AC-31.A.1.3]
        """
        # Arrange: Make graphiti call hang indefinitely
        async def slow_query(*args, **kwargs):
            await simulate_async_delay(10)  # Longer than timeout
            return []

        mock_graphiti_client.search_verification_questions = slow_query
        service = VerificationService(graphiti_client=mock_graphiti_client)

        # Act - should timeout and return empty list
        history = await service._get_question_history_from_graphiti(
            concept="test_concept",
            canvas_name="test_canvas"
        )

        # Assert
        assert history == []

    @pytest.mark.asyncio
    async def test_get_question_history_exception_graceful_degradation(
        self, mock_graphiti_client
    ):
        """
        AC-31.A.1.3: Exceptions result in graceful degradation, not propagation.

        Verifies that exceptions return empty list instead of raising.

        [Source: docs/stories/31.A.1.story.md#AC-31.A.1.3]
        """
        # Arrange: Make graphiti call raise exception
        mock_graphiti_client.search_verification_questions.side_effect = Exception(
            "Neo4j connection failed"
        )
        service = VerificationService(graphiti_client=mock_graphiti_client)

        # Act - should catch exception and return empty list
        history = await service._get_question_history_from_graphiti(
            concept="test_concept",
            canvas_name="test_canvas"
        )

        # Assert
        assert history == []


class TestSearchVerificationQuestionsArgs:
    """
    Test argument passing to search_verification_questions (Story 31.A.1 gap coverage).

    Verifies that _get_question_history_from_graphiti passes correct kwargs
    to graphiti_client.search_verification_questions.
    """

    @pytest.fixture
    def mock_graphiti_client(self):
        """Create mock GraphitiTemporalClient."""
        client = AsyncMock()
        client.search_verification_questions = AsyncMock(return_value=[])
        return client

    @pytest.mark.asyncio
    async def test_search_receives_correct_arguments(self, mock_graphiti_client):
        """
        Verify exact kwargs passed: concept, canvas_name, group_id, limit=10.

        [Source: docs/stories/31.A.1.story.md#AC-31.A.1.3]
        """
        service = VerificationService(graphiti_client=mock_graphiti_client)

        await service._get_question_history_from_graphiti(
            concept="逆否命题",
            canvas_name="离散数学"
        )

        mock_graphiti_client.search_verification_questions.assert_called_once_with(
            concept="逆否命题",
            canvas_name="离散数学",
            group_id=None,
            limit=10
        )

    @pytest.mark.asyncio
    async def test_search_passes_group_id(self, mock_graphiti_client):
        """
        Verify group_id is correctly passed through to the client.

        [Source: docs/stories/31.A.1.story.md#AC-31.A.1.3]
        """
        service = VerificationService(graphiti_client=mock_graphiti_client)

        await service._get_question_history_from_graphiti(
            concept="test",
            canvas_name="test_canvas",
            group_id="group_abc"
        )

        mock_graphiti_client.search_verification_questions.assert_called_once_with(
            concept="test",
            canvas_name="test_canvas",
            group_id="group_abc",
            limit=10
        )

    @pytest.mark.asyncio
    async def test_returns_empty_when_client_returns_none(self, mock_graphiti_client):
        """
        Verify None return from search_verification_questions is handled as [].

        Code: return history if history else []  (line 1859)

        [Source: docs/stories/31.A.1.story.md#AC-31.A.1.3]
        """
        mock_graphiti_client.search_verification_questions.return_value = None
        service = VerificationService(graphiti_client=mock_graphiti_client)

        history = await service._get_question_history_from_graphiti(
            concept="test", canvas_name="test_canvas"
        )

        assert history == []

    @pytest.mark.asyncio
    async def test_connection_error_graceful_degradation(self, mock_graphiti_client):
        """
        Verify ConnectionError is caught by generic Exception handler.

        [Source: docs/stories/31.A.1.story.md#AC-31.A.1.3]
        """
        mock_graphiti_client.search_verification_questions.side_effect = ConnectionError(
            "Neo4j unreachable"
        )
        service = VerificationService(graphiti_client=mock_graphiti_client)

        history = await service._get_question_history_from_graphiti(
            concept="test", canvas_name="test_canvas"
        )

        assert history == []


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
        from unittest.mock import AsyncMock, MagicMock, patch

        # Create mock graphiti client
        mock_client = AsyncMock()
        mock_client.search_verification_questions = AsyncMock(return_value=[])

        # Mock all required dependencies
        with patch(
            "app.dependencies.get_graphiti_temporal_client",
            return_value=mock_client
        ) as mock_get_graphiti, patch(
            "app.dependencies.get_rag_service",
            return_value=MagicMock()
        ), patch(
            "app.dependencies.get_cross_canvas_service",
            return_value=MagicMock()
        ), patch(
            "app.dependencies.TextbookContextService",
            return_value=MagicMock()
        ), patch(
            "app.dependencies.TextbookContextConfig",
            return_value=MagicMock()
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
    async def test_verification_service_logs_graphiti_status_when_present(
        self, caplog
    ):
        """
        AC-31.A.1.2: Log shows Graphiti: True when client is injected.

        [Source: docs/stories/31.A.1.story.md#AC-31.A.1.2]
        """
        import logging

        # Arrange
        mock_client = AsyncMock()

        # Act
        with caplog.at_level(logging.INFO):
            service = VerificationService(graphiti_client=mock_client)

        # Assert: Log contains Graphiti: True
        assert "Graphiti: True" in caplog.text

    @pytest.mark.asyncio
    async def test_verification_service_logs_graphiti_status_when_absent(
        self, caplog
    ):
        """
        AC-31.A.1.2: Log shows Graphiti: False when client is None.

        [Source: docs/stories/31.A.1.story.md#AC-31.A.1.2]
        """
        import logging

        # Act
        with caplog.at_level(logging.INFO):
            service = VerificationService(graphiti_client=None)

        # Assert: Log contains Graphiti: False
        assert "Graphiti: False" in caplog.text
