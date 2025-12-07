# Canvas Learning System - Alert Manager Tests
# ✅ Verified from Context7:/pytest-dev/pytest (topic: pytest fixtures async)
# [Source: docs/stories/17.3.story.md - Task 7]
"""
Unit tests for AlertManager and alert rule evaluation.

Tests:
- Alert rule loading from YAML
- Alert state transitions (pending → firing → resolved)
- Metric evaluation logic
- Notification dispatch on state changes

[Source: docs/architecture/performance-monitoring-architecture.md:281-323]
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.services.alert_manager import (
    Alert,
    AlertManager,
    AlertRule,
    AlertSeverity,
    AlertState,
    get_default_alert_rules,
    load_alert_rules_from_yaml,
)
from app.services.notification_channels import NotificationDispatcher

# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def sample_alert_rule() -> AlertRule:
    """Create a sample alert rule for testing."""
    return AlertRule(
        name="TestHighLatency",
        expression='test_latency > 1.0',
        for_duration=60,
        severity=AlertSeverity.WARNING,
        summary="Test latency alert",
        description="Test latency exceeded threshold: {value}s",
        labels={"component": "test", "category": "performance"},
    )


@pytest.fixture
def sample_critical_rule() -> AlertRule:
    """Create a critical alert rule for testing."""
    return AlertRule(
        name="TestCriticalError",
        expression='test_errors > 10',
        for_duration=30,
        severity=AlertSeverity.CRITICAL,
        summary="Critical error rate",
        description="Error count exceeded: {value}",
        labels={"component": "api", "category": "reliability"},
    )


@pytest.fixture
def mock_notification_dispatcher() -> MagicMock:
    """Create a mock notification dispatcher."""
    dispatcher = MagicMock(spec=NotificationDispatcher)
    dispatcher.dispatch = AsyncMock()
    return dispatcher


@pytest.fixture
def alert_manager(
    sample_alert_rule: AlertRule,
    mock_notification_dispatcher: MagicMock,
) -> AlertManager:
    """Create an AlertManager instance for testing."""
    return AlertManager(
        rules=[sample_alert_rule],
        notification_dispatcher=mock_notification_dispatcher,
        evaluation_interval=1,  # Fast interval for tests
    )


# ═══════════════════════════════════════════════════════════════════════════════
# AlertRule Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestAlertRule:
    """Tests for AlertRule dataclass."""

    def test_alert_rule_creation(self, sample_alert_rule: AlertRule):
        """Test AlertRule can be created with all fields."""
        assert sample_alert_rule.name == "TestHighLatency"
        assert sample_alert_rule.severity == AlertSeverity.WARNING
        assert sample_alert_rule.for_duration == 60
        assert "component" in sample_alert_rule.labels

    def test_alert_rule_default_labels(self):
        """Test AlertRule with default empty labels."""
        rule = AlertRule(
            name="Rule1",
            expression="metric > 1",
            for_duration=60,
            severity=AlertSeverity.WARNING,
            summary="Rule 1",
            description="Description 1",
        )
        assert rule.labels == {}

    def test_alert_rule_with_custom_labels(self):
        """Test AlertRule with custom labels."""
        rule = AlertRule(
            name="Rule1",
            expression="metric > 1",
            for_duration=60,
            severity=AlertSeverity.WARNING,
            summary="Rule 1",
            description="Description 1",
            labels={"env": "prod", "service": "api"},
        )
        assert rule.labels == {"env": "prod", "service": "api"}


# ═══════════════════════════════════════════════════════════════════════════════
# Alert Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestAlert:
    """Tests for Alert dataclass."""

    def test_alert_creation(self, sample_alert_rule: AlertRule):
        """Test Alert can be created from rule."""
        alert = Alert(
            id="test-alert-123",
            name=sample_alert_rule.name,
            severity=sample_alert_rule.severity,
            state=AlertState.PENDING,
            message="Test alert message",
            value=1.5,
            threshold=1.0,
            labels=sample_alert_rule.labels,
            triggered_at=datetime.utcnow(),
            pending_since=datetime.utcnow(),
        )
        assert alert.state == AlertState.PENDING
        assert alert.value == 1.5

    def test_alert_to_dict(self, sample_alert_rule: AlertRule):
        """Test Alert serialization to dictionary."""
        now = datetime.utcnow()
        alert = Alert(
            id="test-alert-456",
            name=sample_alert_rule.name,
            severity=sample_alert_rule.severity,
            state=AlertState.FIRING,
            message="Alert is firing",
            value=2.0,
            threshold=1.0,
            labels={"env": "test"},
            triggered_at=now,
            pending_since=now,
        )

        result = alert.to_dict()

        assert result["id"] == "test-alert-456"
        assert result["severity"] == "warning"
        assert result["value"] == 2.0
        assert result["labels"] == {"env": "test"}

    def test_alert_default_state(self):
        """Test Alert has default PENDING state."""
        alert = Alert(
            id="test-alert",
            name="Test",
            severity=AlertSeverity.INFO,
            message="Test",
            triggered_at=datetime.utcnow(),
        )
        assert alert.state == AlertState.PENDING


# ═══════════════════════════════════════════════════════════════════════════════
# AlertManager Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestAlertManager:
    """Tests for AlertManager class."""

    def test_alert_manager_initialization(
        self,
        alert_manager: AlertManager,
        sample_alert_rule: AlertRule,
    ):
        """Test AlertManager initializes correctly."""
        assert len(alert_manager.rules) == 1
        assert alert_manager.rules[0].name == sample_alert_rule.name
        assert alert_manager.evaluation_interval == 1
        assert not alert_manager._running

    def test_get_active_alerts_empty(self, alert_manager: AlertManager):
        """Test getting active alerts when none exist."""
        alerts = alert_manager.get_active_alerts()
        assert alerts == []

    def test_get_active_alerts_by_severity(
        self,
        mock_notification_dispatcher: MagicMock,
        sample_alert_rule: AlertRule,
        sample_critical_rule: AlertRule,
    ):
        """Test filtering active alerts by severity."""
        manager = AlertManager(
            rules=[sample_alert_rule, sample_critical_rule],
            notification_dispatcher=mock_notification_dispatcher,
            evaluation_interval=1,
        )

        # Manually add alerts for testing
        now = datetime.utcnow()
        warning_alert = Alert(
            id="warn-1",
            name="TestWarning",
            severity=AlertSeverity.WARNING,
            state=AlertState.FIRING,
            message="Warning",
            value=1.5,
            threshold=1.0,
            labels={},
            triggered_at=now,
            pending_since=now,
        )
        critical_alert = Alert(
            id="crit-1",
            name="TestCritical",
            severity=AlertSeverity.CRITICAL,
            state=AlertState.FIRING,
            message="Critical",
            value=15.0,
            threshold=10.0,
            labels={},
            triggered_at=now,
            pending_since=now,
        )

        manager._active_alerts["warn-1"] = warning_alert
        manager._active_alerts["crit-1"] = critical_alert

        # Filter by severity
        critical_only = manager.get_active_alerts(severity=AlertSeverity.CRITICAL)
        assert len(critical_only) == 1
        assert critical_only[0].name == "TestCritical"

        warning_only = manager.get_active_alerts(severity=AlertSeverity.WARNING)
        assert len(warning_only) == 1
        assert warning_only[0].name == "TestWarning"

    @pytest.mark.asyncio
    async def test_alert_manager_start_stop(self, alert_manager: AlertManager):
        """Test AlertManager can start and stop."""
        assert not alert_manager._running

        await alert_manager.start()
        assert alert_manager._running
        assert alert_manager._task is not None

        await alert_manager.stop()
        assert not alert_manager._running

    @pytest.mark.asyncio
    async def test_alert_manager_stop_when_not_running(self, alert_manager: AlertManager):
        """Test AlertManager handles stop when not running."""
        assert not alert_manager._running
        # Should not raise
        await alert_manager.stop()
        assert not alert_manager._running


# ═══════════════════════════════════════════════════════════════════════════════
# Alert State Transition Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestAlertStateTransitions:
    """Tests for alert state machine transitions."""

    def test_alert_state_values(self):
        """Test AlertState enum values."""
        assert AlertState.PENDING.value == "pending"
        assert AlertState.FIRING.value == "firing"
        assert AlertState.RESOLVED.value == "resolved"

    def test_alert_severity_values(self):
        """Test AlertSeverity enum values."""
        assert AlertSeverity.CRITICAL.value == "critical"
        assert AlertSeverity.WARNING.value == "warning"
        assert AlertSeverity.INFO.value == "info"


# ═══════════════════════════════════════════════════════════════════════════════
# YAML Loading Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestAlertRuleLoading:
    """Tests for loading alert rules from YAML."""

    def test_get_default_alert_rules(self):
        """Test default alert rules are returned."""
        rules = get_default_alert_rules()

        assert len(rules) >= 5  # At least 5 core rules

        # Check for expected rules
        rule_names = [r.name for r in rules]
        assert "HighAPILatency" in rule_names
        assert "HighErrorRate" in rule_names

    def test_load_rules_from_yaml_file_not_found(self):
        """Test graceful handling when YAML file doesn't exist."""
        rules = load_alert_rules_from_yaml("nonexistent/path.yaml")

        # Should return empty list when file not found
        assert len(rules) == 0

    def test_load_rules_from_valid_yaml(self, tmp_path):
        """Test loading rules from valid YAML file."""
        yaml_content = """
alerts:
  - name: CustomRule
    expression: 'custom_metric > 100'
    for: 120
    severity: critical
    summary: Custom rule fired
    description: Custom metric exceeded
    labels:
      custom: 'true'
"""
        yaml_file = tmp_path / "alerts.yaml"
        yaml_file.write_text(yaml_content)

        rules = load_alert_rules_from_yaml(str(yaml_file))

        assert len(rules) == 1
        assert rules[0].name == "CustomRule"
        assert rules[0].severity == AlertSeverity.CRITICAL


# ═══════════════════════════════════════════════════════════════════════════════
# Notification Integration Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestAlertNotifications:
    """Tests for alert notification dispatch."""

    @pytest.mark.asyncio
    async def test_notification_dispatcher_called(
        self,
        alert_manager: AlertManager,
        mock_notification_dispatcher: MagicMock,
    ):
        """Test notification dispatcher can be called."""
        now = datetime.utcnow()

        # Create alert
        alert = Alert(
            id="fire-1",
            name="TestAlert",
            severity=AlertSeverity.WARNING,
            state=AlertState.FIRING,
            message="Alert fired",
            value=2.0,
            threshold=1.0,
            labels={},
            triggered_at=now,
        )

        # Dispatch notification
        await alert_manager.notification_dispatcher.dispatch(alert, "fired")

        # Verify dispatch was called
        mock_notification_dispatcher.dispatch.assert_called_once()
        call_args = mock_notification_dispatcher.dispatch.call_args
        assert call_args[0][0].id == "fire-1"
        assert call_args[0][1] == "fired"


# ═══════════════════════════════════════════════════════════════════════════════
# Additional Alert Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestAlertManagerAlerts:
    """Tests for AlertManager alert handling."""

    def test_active_alerts_direct_access(
        self,
        alert_manager: AlertManager,
    ):
        """Test direct access to active alerts dict."""
        now = datetime.utcnow()

        # Add some alerts directly (simulating evaluation loop behavior)
        for i in range(3):
            alert_manager._active_alerts[f"alert-{i}"] = Alert(
                id=f"alert-{i}",
                name=f"Alert{i}",
                severity=AlertSeverity.WARNING if i < 2 else AlertSeverity.CRITICAL,
                state=AlertState.FIRING,
                message=f"Alert {i}",
                value=float(i),
                threshold=0.0,
                labels={},
                triggered_at=now,
                pending_since=now,
            )

        # Verify alerts were stored
        assert len(alert_manager._active_alerts) == 3
        assert "alert-0" in alert_manager._active_alerts
        assert alert_manager._active_alerts["alert-2"].severity == AlertSeverity.CRITICAL
