# Canvas Learning System - Notification Channels Tests
# ✅ Verified from Context7:/pytest-dev/pytest (topic: pytest fixtures async)
# [Source: docs/stories/17.3.story.md - Task 7]
"""
Unit tests for notification channels.

Tests:
- ConsoleNotificationChannel (structlog)
- FileNotificationChannel (log file)
- ObsidianNotificationChannel (SSE)
- WebhookNotificationChannel (HTTP)
- NotificationDispatcher routing

[Source: docs/architecture/performance-monitoring-architecture.md:325-333]
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.services.alert_manager import Alert, AlertSeverity, AlertState
from app.services.notification_channels import (
    ConsoleNotificationChannel,
    FileNotificationChannel,
    NotificationChannel,
    NotificationDispatcher,
    ObsidianNotificationChannel,
    SSEConnectionManager,
    WebhookNotificationChannel,
    create_default_dispatcher,
)

# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def sample_alert() -> Alert:
    """Create a sample alert for testing."""
    now = datetime.utcnow()
    return Alert(
        id="test-alert-001",
        name="TestAlert",
        severity=AlertSeverity.WARNING,
        state=AlertState.FIRING,
        message="Test alert message",
        value=1.5,
        threshold=1.0,
        labels={"component": "test"},
        triggered_at=now,
        pending_since=now,
    )


@pytest.fixture
def resolved_alert() -> Alert:
    """Create a resolved alert for testing."""
    now = datetime.utcnow()
    return Alert(
        id="test-alert-002",
        name="ResolvedAlert",
        severity=AlertSeverity.CRITICAL,
        state=AlertState.RESOLVED,
        message="Alert has been resolved",
        value=0.5,
        threshold=1.0,
        labels={"component": "api"},
        triggered_at=now,
        pending_since=now,
    )


@pytest.fixture
def temp_log_path(tmp_path: Path) -> Path:
    """Create a temporary log file path."""
    return tmp_path / "alerts.log"


# ═══════════════════════════════════════════════════════════════════════════════
# ConsoleNotificationChannel Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestConsoleNotificationChannel:
    """Tests for console notification channel."""

    @pytest.mark.asyncio
    async def test_send_fired_alert(self, sample_alert: Alert):
        """Test sending fired alert to console."""
        channel = ConsoleNotificationChannel()

        with patch("app.services.notification_channels.logger") as mock_logger:
            result = await channel.send(sample_alert, "fired")

            assert result is True
            mock_logger.warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_resolved_alert(self, resolved_alert: Alert):
        """Test sending resolved alert to console."""
        channel = ConsoleNotificationChannel()

        with patch("app.services.notification_channels.logger") as mock_logger:
            result = await channel.send(resolved_alert, "resolved")

            assert result is True
            mock_logger.info.assert_called_once()

    @pytest.mark.asyncio
    async def test_console_always_returns_true(self, sample_alert: Alert):
        """Test console channel never fails."""
        channel = ConsoleNotificationChannel()

        # Multiple sends should all succeed
        for _ in range(5):
            result = await channel.send(sample_alert, "fired")
            assert result is True


# ═══════════════════════════════════════════════════════════════════════════════
# FileNotificationChannel Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestFileNotificationChannel:
    """Tests for file notification channel."""

    @pytest.mark.asyncio
    async def test_send_creates_log_entry(
        self,
        sample_alert: Alert,
        temp_log_path: Path,
    ):
        """Test alert is written to log file."""
        channel = FileNotificationChannel(log_path=str(temp_log_path))

        result = await channel.send(sample_alert, "fired")

        assert result is True
        assert temp_log_path.exists()

        content = temp_log_path.read_text()
        assert "FIRED" in content
        assert "TestAlert" in content
        assert "WARNING" in content

    @pytest.mark.asyncio
    async def test_send_appends_to_existing_log(
        self,
        sample_alert: Alert,
        resolved_alert: Alert,
        temp_log_path: Path,
    ):
        """Test multiple alerts are appended to same file."""
        channel = FileNotificationChannel(log_path=str(temp_log_path))

        await channel.send(sample_alert, "fired")
        await channel.send(resolved_alert, "resolved")

        content = temp_log_path.read_text()
        lines = content.strip().split("\n")

        assert len(lines) == 2
        assert "FIRED" in lines[0]
        assert "RESOLVED" in lines[1]

    @pytest.mark.asyncio
    async def test_send_creates_parent_directory(
        self,
        sample_alert: Alert,
        tmp_path: Path,
    ):
        """Test parent directories are created if needed."""
        nested_path = tmp_path / "nested" / "dir" / "alerts.log"
        channel = FileNotificationChannel(log_path=str(nested_path))

        result = await channel.send(sample_alert, "fired")

        assert result is True
        assert nested_path.exists()

    @pytest.mark.asyncio
    async def test_send_handles_write_error(self, sample_alert: Alert, tmp_path: Path):
        """Test graceful handling of write errors."""
        # Create a file path and make the parent directory read-only (or use mock)
        log_path = tmp_path / "alerts.log"
        channel = FileNotificationChannel(log_path=str(log_path))

        # Mock open to simulate write error
        with patch("builtins.open", side_effect=PermissionError("Access denied")):
            with patch("app.services.notification_channels.logger") as mock_logger:
                result = await channel.send(sample_alert, "fired")

                # Should return False on error
                assert result is False
                mock_logger.error.assert_called_once()


# ═══════════════════════════════════════════════════════════════════════════════
# ObsidianNotificationChannel Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestObsidianNotificationChannel:
    """Tests for Obsidian SSE notification channel."""

    @pytest.mark.asyncio
    async def test_send_without_sse_manager(self, sample_alert: Alert):
        """Test channel handles missing SSE manager."""
        channel = ObsidianNotificationChannel(sse_manager=None)

        result = await channel.send(sample_alert, "fired")

        assert result is False

    @pytest.mark.asyncio
    async def test_send_with_sse_manager(self, sample_alert: Alert):
        """Test channel broadcasts via SSE manager."""
        mock_sse = MagicMock(spec=SSEConnectionManager)
        mock_sse.broadcast = AsyncMock()

        channel = ObsidianNotificationChannel(sse_manager=mock_sse)

        result = await channel.send(sample_alert, "fired")

        assert result is True
        mock_sse.broadcast.assert_called_once()

        # Verify broadcast message structure
        call_args = mock_sse.broadcast.call_args[0][0]
        assert call_args["type"] == "alert.fired"
        assert "data" in call_args

    @pytest.mark.asyncio
    async def test_send_handles_broadcast_error(self, sample_alert: Alert):
        """Test graceful handling of SSE broadcast errors."""
        mock_sse = MagicMock(spec=SSEConnectionManager)
        mock_sse.broadcast = AsyncMock(side_effect=Exception("Broadcast failed"))

        channel = ObsidianNotificationChannel(sse_manager=mock_sse)

        with patch("app.services.notification_channels.logger"):
            result = await channel.send(sample_alert, "fired")

        assert result is False


# ═══════════════════════════════════════════════════════════════════════════════
# WebhookNotificationChannel Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestWebhookNotificationChannel:
    """Tests for webhook notification channel."""

    @pytest.mark.asyncio
    async def test_send_makes_post_request(self, sample_alert: Alert):
        """Test webhook sends POST request."""
        channel = WebhookNotificationChannel(
            webhook_url="https://example.com/webhook",
            timeout=5,
        )

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client_class.return_value = mock_client

            result = await channel.send(sample_alert, "fired")

            assert result is True
            mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_handles_http_error(self, sample_alert: Alert):
        """Test graceful handling of HTTP errors."""
        channel = WebhookNotificationChannel(
            webhook_url="https://example.com/webhook",
            timeout=5,
        )

        # Create mock httpx module
        import sys
        mock_httpx = MagicMock()
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=Exception("Connection failed"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_httpx.AsyncClient.return_value = mock_client

        # Patch httpx in sys.modules before it's imported inside the method
        with patch.dict(sys.modules, {"httpx": mock_httpx}):
            with patch("app.services.notification_channels.logger"):
                result = await channel.send(sample_alert, "fired")

            assert result is False

    @pytest.mark.asyncio
    async def test_send_handles_missing_httpx(self, sample_alert: Alert):
        """Test graceful handling when httpx not installed."""
        channel = WebhookNotificationChannel(
            webhook_url="https://example.com/webhook",
        )

        with patch.dict("sys.modules", {"httpx": None}):
            with patch("app.services.notification_channels.logger"):
                # Import error is caught internally
                result = await channel.send(sample_alert, "fired")
                # Result depends on import handling


# ═══════════════════════════════════════════════════════════════════════════════
# NotificationDispatcher Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestNotificationDispatcher:
    """Tests for notification dispatcher routing."""

    @pytest.mark.asyncio
    async def test_dispatch_to_all_channels(self, sample_alert: Alert):
        """Test dispatcher sends to all configured channels."""
        channel1 = MagicMock(spec=NotificationChannel)
        channel1.send = AsyncMock(return_value=True)

        channel2 = MagicMock(spec=NotificationChannel)
        channel2.send = AsyncMock(return_value=True)

        dispatcher = NotificationDispatcher(channels=[channel1, channel2])

        await dispatcher.dispatch(sample_alert, "fired")

        channel1.send.assert_called_once_with(sample_alert, "fired")
        channel2.send.assert_called_once_with(sample_alert, "fired")

    @pytest.mark.asyncio
    async def test_dispatch_continues_on_channel_failure(self, sample_alert: Alert):
        """Test dispatcher continues even if one channel fails."""
        channel1 = MagicMock(spec=NotificationChannel)
        channel1.send = AsyncMock(side_effect=Exception("Channel 1 failed"))

        channel2 = MagicMock(spec=NotificationChannel)
        channel2.send = AsyncMock(return_value=True)

        dispatcher = NotificationDispatcher(channels=[channel1, channel2])

        with patch("app.services.notification_channels.logger"):
            await dispatcher.dispatch(sample_alert, "fired")

        # Channel 2 should still be called even though channel 1 failed
        channel2.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_dispatch_with_empty_channels(self, sample_alert: Alert):
        """Test dispatcher handles empty channel list."""
        dispatcher = NotificationDispatcher(channels=[])

        # Should not raise
        await dispatcher.dispatch(sample_alert, "fired")


# ═══════════════════════════════════════════════════════════════════════════════
# Factory Function Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestCreateDefaultDispatcher:
    """Tests for default dispatcher factory function."""

    def test_create_without_sse_manager(self):
        """Test creating dispatcher without SSE manager."""
        dispatcher = create_default_dispatcher()

        assert dispatcher is not None
        assert len(dispatcher.channels) >= 2  # Console + File

    def test_create_with_sse_manager(self):
        """Test creating dispatcher with SSE manager."""
        mock_sse = MagicMock(spec=SSEConnectionManager)

        dispatcher = create_default_dispatcher(sse_manager=mock_sse)

        assert len(dispatcher.channels) >= 3  # Console + File + Obsidian

    def test_create_with_custom_log_path(self, tmp_path: Path):
        """Test creating dispatcher with custom log path."""
        custom_path = str(tmp_path / "custom_alerts.log")

        dispatcher = create_default_dispatcher(log_path=custom_path)

        # Find the file channel
        file_channel = None
        for channel in dispatcher.channels:
            if isinstance(channel, FileNotificationChannel):
                file_channel = channel
                break

        assert file_channel is not None
        assert str(file_channel.log_path) == custom_path


# ═══════════════════════════════════════════════════════════════════════════════
# SSEConnectionManager Stub Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestSSEConnectionManager:
    """Tests for SSE connection manager stub."""

    def test_initialization(self):
        """Test SSE manager initializes correctly."""
        manager = SSEConnectionManager()
        assert manager._connections == []

    @pytest.mark.asyncio
    async def test_broadcast(self):
        """Test broadcast method exists and is callable."""
        manager = SSEConnectionManager()

        # Should not raise
        await manager.broadcast({"type": "test", "data": {}})
