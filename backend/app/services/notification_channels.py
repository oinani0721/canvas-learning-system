# Canvas Learning System - Notification Channels
# ✅ Verified from Architecture Doc (performance-monitoring-architecture.md:325-333)
# ✅ Verified from ADR-010:77-100 (structlog get_logger and bind)
# ✅ Verified from ADR-006:127-158 (SSE EventSourceResponse)
"""
Notification channels for alert distribution.

Provides:
- Console logging (structlog)
- File logging (logs/alerts.log)
- Obsidian SSE notifications

[Source: docs/architecture/performance-monitoring-architecture.md:325-333]
[Source: docs/stories/17.3.story.md - Task 5]
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, List

# ✅ Verified from ADR-010:77-100 (structlog logging)
import structlog

if TYPE_CHECKING:
    from .alert_manager import Alert

logger = structlog.get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Abstract Base Class
# [Source: docs/stories/17.3.story.md - Task 5]
# ═══════════════════════════════════════════════════════════════════════════════

class NotificationChannel(ABC):
    """Abstract base class for notification channels.

    [Source: docs/architecture/performance-monitoring-architecture.md:325-333]

    All notification channels must implement the send() method.
    """

    @abstractmethod
    async def send(self, alert: "Alert", event_type: str) -> bool:
        """Send notification for an alert event.

        Args:
            alert: Alert instance
            event_type: "fired" or "resolved"

        Returns:
            bool: True if notification was sent successfully
        """
        pass


# ═══════════════════════════════════════════════════════════════════════════════
# Console Notification Channel
# [Source: ADR-010-LOGGING-AGGREGATION-STRUCTLOG.md:77-100]
# ═══════════════════════════════════════════════════════════════════════════════

class ConsoleNotificationChannel(NotificationChannel):
    """Console logging notification channel.

    Uses structlog for structured console/log output.

    [Source: ADR-010-LOGGING-AGGREGATION-STRUCTLOG.md:77-100]

    Example output:
        alert.fired alert_id="abc123" name="HighAPILatency" severity="warning"
    """

    async def send(self, alert: "Alert", event_type: str) -> bool:
        """Send notification via structlog.

        Args:
            alert: Alert instance
            event_type: "fired" or "resolved"

        Returns:
            bool: Always True (logging doesn't fail)
        """
        # ✅ Verified from ADR-010:77-100 (structlog structured logging)
        log_method = logger.warning if event_type == "fired" else logger.info

        log_method(
            f"alert.{event_type}",
            alert_id=alert.id,
            name=alert.name,
            severity=alert.severity.value,
            message=alert.message,
            value=alert.value,
            threshold=alert.threshold,
        )
        return True


# ═══════════════════════════════════════════════════════════════════════════════
# File Notification Channel
# [Source: docs/architecture/performance-monitoring-architecture.md:325-333]
# ═══════════════════════════════════════════════════════════════════════════════

class FileNotificationChannel(NotificationChannel):
    """File logging notification channel.

    Writes alert events to a dedicated log file.

    [Source: docs/architecture/performance-monitoring-architecture.md:325-333]

    Default path: logs/alerts.log

    Format:
        2025-12-03T20:15:00 | FIRED | WARNING | HighAPILatency | Message
    """

    def __init__(self, log_path: str = "logs/alerts.log"):
        """Initialize file notification channel.

        Args:
            log_path: Path to alerts log file (default: logs/alerts.log)
        """
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    async def send(self, alert: "Alert", event_type: str) -> bool:
        """Write notification to log file.

        Args:
            alert: Alert instance
            event_type: "fired" or "resolved"

        Returns:
            bool: True if write succeeded, False otherwise
        """
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(
                    f"{alert.triggered_at.isoformat()} | "
                    f"{event_type.upper()} | "
                    f"{alert.severity.value.upper()} | "
                    f"{alert.name} | "
                    f"{alert.message}\n"
                )
            return True
        except Exception as e:
            logger.error(
                "file_notification.failed",
                error=str(e),
                path=str(self.log_path),
            )
            return False


# ═══════════════════════════════════════════════════════════════════════════════
# Obsidian SSE Notification Channel
# [Source: ADR-006-REALTIME-COMMUNICATION-SSE-HTTP.md:127-158]
# ═══════════════════════════════════════════════════════════════════════════════

class ObsidianNotificationChannel(NotificationChannel):
    """Obsidian plugin SSE notification channel.

    Pushes alert events to connected Obsidian clients via Server-Sent Events.

    [Source: ADR-006-REALTIME-COMMUNICATION-SSE-HTTP.md:127-158]

    Dependencies:
        Requires SSEConnectionManager from backend/app/services/sse_manager.py
        (Implemented in Story 15.x)
    """

    def __init__(self, sse_manager: "SSEConnectionManager" = None):
        """Initialize Obsidian notification channel.

        Args:
            sse_manager: SSE connection manager instance (optional)
        """
        self.sse_manager = sse_manager

    async def send(self, alert: "Alert", event_type: str) -> bool:
        """Send notification via SSE broadcast.

        Args:
            alert: Alert instance
            event_type: "fired" or "resolved"

        Returns:
            bool: True if broadcast succeeded, False otherwise
        """
        if self.sse_manager is None:
            logger.debug(
                "obsidian_notification.skipped",
                reason="no_sse_manager",
            )
            return False

        try:
            await self.sse_manager.broadcast({
                "type": f"alert.{event_type}",
                "data": alert.to_dict(),
            })
            return True
        except Exception as e:
            logger.error(
                "obsidian_notification.failed",
                error=str(e),
                alert_id=alert.id,
            )
            return False


# ═══════════════════════════════════════════════════════════════════════════════
# Webhook Notification Channel (Optional - P2)
# [Source: docs/architecture/performance-monitoring-architecture.md:325-333]
# ═══════════════════════════════════════════════════════════════════════════════

class WebhookNotificationChannel(NotificationChannel):
    """Webhook notification channel.

    Sends alert events to configured webhook URLs.

    [Source: docs/architecture/performance-monitoring-architecture.md:325-333]

    Priority: P2 (optional)
    """

    def __init__(self, webhook_url: str, timeout: int = 10):
        """Initialize webhook notification channel.

        Args:
            webhook_url: URL to send webhook POST requests
            timeout: Request timeout in seconds
        """
        self.webhook_url = webhook_url
        self.timeout = timeout

    async def send(self, alert: "Alert", event_type: str) -> bool:
        """Send notification via HTTP POST.

        Args:
            alert: Alert instance
            event_type: "fired" or "resolved"

        Returns:
            bool: True if webhook call succeeded, False otherwise
        """
        try:
            import httpx

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.webhook_url,
                    json={
                        "event_type": event_type,
                        "alert": alert.to_dict(),
                    },
                )
                response.raise_for_status()
                return True

        except ImportError:
            logger.error("webhook_notification.httpx_not_installed")
            return False
        except Exception as e:
            logger.error(
                "webhook_notification.failed",
                error=str(e),
                url=self.webhook_url,
            )
            return False


# ═══════════════════════════════════════════════════════════════════════════════
# Notification Dispatcher
# [Source: docs/stories/17.3.story.md - Task 5]
# ═══════════════════════════════════════════════════════════════════════════════

class NotificationDispatcher:
    """Notification dispatcher.

    Routes alert events to all configured notification channels.

    [Source: docs/architecture/performance-monitoring-architecture.md:325-333]
    [Source: docs/stories/17.3.story.md - Task 5]

    Example:
        >>> channels = [
        ...     ConsoleNotificationChannel(),
        ...     FileNotificationChannel(),
        ... ]
        >>> dispatcher = NotificationDispatcher(channels)
        >>> await dispatcher.dispatch(alert, "fired")
    """

    def __init__(self, channels: List[NotificationChannel]):
        """Initialize notification dispatcher.

        Args:
            channels: List of notification channels to dispatch to
        """
        self.channels = channels

    async def dispatch(self, alert: "Alert", event_type: str):
        """Dispatch alert event to all configured channels.

        Failures in individual channels are logged but don't stop
        dispatch to other channels.

        Args:
            alert: Alert instance to dispatch
            event_type: "fired" or "resolved"
        """
        for channel in self.channels:
            try:
                await channel.send(alert, event_type)
            except Exception as e:
                logger.error(
                    "notification_dispatch.failed",
                    channel=type(channel).__name__,
                    alert_id=alert.id,
                    error=str(e),
                )


# ═══════════════════════════════════════════════════════════════════════════════
# Factory Functions
# [Source: docs/stories/17.3.story.md - Task 5]
# ═══════════════════════════════════════════════════════════════════════════════

def create_default_dispatcher(
    sse_manager: "SSEConnectionManager" = None,
    log_path: str = "logs/alerts.log",
) -> NotificationDispatcher:
    """Create notification dispatcher with default channels.

    [Source: docs/architecture/performance-monitoring-architecture.md:325-333]

    Default channels:
    - ConsoleNotificationChannel (always enabled)
    - FileNotificationChannel (always enabled)
    - ObsidianNotificationChannel (if sse_manager provided)

    Args:
        sse_manager: Optional SSE connection manager for Obsidian notifications
        log_path: Path for file notifications

    Returns:
        NotificationDispatcher with configured channels
    """
    channels: List[NotificationChannel] = [
        ConsoleNotificationChannel(),
        FileNotificationChannel(log_path=log_path),
    ]

    if sse_manager is not None:
        channels.append(ObsidianNotificationChannel(sse_manager=sse_manager))

    logger.info(
        "notification_dispatcher.created",
        channels=[type(c).__name__ for c in channels],
    )

    return NotificationDispatcher(channels)


# ═══════════════════════════════════════════════════════════════════════════════
# SSE Connection Manager Stub
# [Source: ADR-006-REALTIME-COMMUNICATION-SSE-HTTP.md]
# ═══════════════════════════════════════════════════════════════════════════════

class SSEConnectionManager:
    """SSE Connection Manager stub.

    This is a stub/placeholder. The actual implementation should be in
    backend/app/services/sse_manager.py (from Story 15.x).

    [Source: ADR-006-REALTIME-COMMUNICATION-SSE-HTTP.md]
    """

    def __init__(self):
        """Initialize SSE connection manager."""
        self._connections: List = []

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients.

        Args:
            message: Message to broadcast
        """
        logger.debug(
            "sse_manager.broadcast",
            message_type=message.get("type"),
            connections=len(self._connections),
        )
        # Actual implementation would iterate over connections
        # and send message to each
        pass
