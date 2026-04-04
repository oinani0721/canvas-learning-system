"""Tests for AuditGuardian pipeline violation detection.

Tests the three violation types:
- step_skip: update_fsrs/update_bkt called without prior score_answer
- time_anomaly: interval between steps > 5 minutes
- signal_loss: score_answer without subsequent update within timeout
"""

import time

import pytest

from app.audit.guardian import AuditGuardian, AUDIT_LOG_FILE


@pytest.fixture
def guardian(tmp_path, monkeypatch):
    """Create a fresh AuditGuardian with log directed to tmp_path."""
    log_file = tmp_path / "audit.jsonl"
    monkeypatch.setattr("app.audit.guardian.AUDIT_LOG_FILE", log_file)
    monkeypatch.setattr("app.audit.guardian.AUDIT_LOG_DIR", tmp_path)
    g = AuditGuardian()
    return g


@pytest.fixture
def read_log(tmp_path):
    """Helper to read audit log entries."""
    import json

    def _read():
        log_file = tmp_path / "audit.jsonl"
        if not log_file.exists():
            return []
        lines = log_file.read_text().strip().split("\n")
        return [json.loads(line) for line in lines if line]

    return _read


@pytest.mark.asyncio
class TestHappyPath:
    """Normal pipeline: generate_question → score_answer → update_fsrs."""

    async def test_complete_pipeline_no_violations(self, guardian, read_log):
        await guardian.record_tool_call("generate_question", "sess1", "node1")
        await guardian.record_tool_call("score_answer", "sess1", "node1")
        await guardian.record_tool_call("update_fsrs", "sess1", "node1")

        events = read_log()
        violations = [e for e in events if e["event_type"] == "violation"]
        assert len(violations) == 0

    async def test_pipeline_clears_after_completion(self, guardian):
        await guardian.record_tool_call("generate_question", "sess1", "node1")
        await guardian.record_tool_call("score_answer", "sess1", "node1")
        await guardian.record_tool_call("update_fsrs", "sess1", "node1")

        assert len(guardian._active_pipelines) == 0

    async def test_non_pipeline_tools_ignored(self, guardian, read_log):
        await guardian.record_tool_call("get_canvas_data", "sess1", "node1")
        await guardian.record_tool_call("search_memory", "sess1", "node1")

        events = read_log()
        violations = [e for e in events if e["event_type"] == "violation"]
        assert len(violations) == 0


@pytest.mark.asyncio
class TestStepSkipDetection:
    """Detect update called without prior score_answer."""

    async def test_update_fsrs_without_score(self, guardian, read_log):
        await guardian.record_tool_call("update_fsrs", "sess1", "node1")

        events = read_log()
        violations = [e for e in events if e["violation_type"] == "step_skip"]
        assert len(violations) == 1
        assert "without prior 'score_answer'" in violations[0]["details"]["message"]

    async def test_update_bkt_without_score(self, guardian, read_log):
        await guardian.record_tool_call("update_bkt", "sess1", "node1")

        events = read_log()
        violations = [e for e in events if e["violation_type"] == "step_skip"]
        assert len(violations) == 1

    async def test_update_after_generate_but_no_score(self, guardian, read_log):
        await guardian.record_tool_call("generate_question", "sess1", "node1")
        await guardian.record_tool_call("update_fsrs", "sess1", "node1")

        events = read_log()
        violations = [e for e in events if e["violation_type"] == "step_skip"]
        assert len(violations) == 1


@pytest.mark.asyncio
class TestTimeAnomalyDetection:
    """Detect interval between steps > 5 minutes."""

    async def test_time_anomaly_detected(self, guardian, read_log):
        await guardian.record_tool_call("generate_question", "sess1", "node1")

        key = guardian._pipeline_key("sess1", "node1")
        guardian._active_pipelines[key].last_step_time -= 400  # simulate 400s ago

        await guardian.record_tool_call("score_answer", "sess1", "node1")

        events = read_log()
        violations = [e for e in events if e["violation_type"] == "time_anomaly"]
        assert len(violations) == 1
        assert violations[0]["details"]["interval_seconds"] > 300


@pytest.mark.asyncio
class TestSignalLossDetection:
    """Detect score_answer without subsequent update within timeout."""

    async def test_signal_loss_detected(self, guardian, read_log):
        await guardian.record_tool_call("generate_question", "sess1", "node1")
        await guardian.record_tool_call("score_answer", "sess1", "node1")

        key = guardian._pipeline_key("sess1", "node1")
        guardian._active_pipelines[key].last_step_time -= 400  # simulate timeout

        await guardian.check_signal_loss()

        events = read_log()
        violations = [e for e in events if e["violation_type"] == "signal_loss"]
        assert len(violations) == 1
        assert (
            "no update_fsrs/update_bkt followed" in violations[0]["details"]["message"]
        )

    async def test_signal_loss_cleans_expired_pipelines(self, guardian):
        await guardian.record_tool_call("generate_question", "sess1", "node1")
        await guardian.record_tool_call("score_answer", "sess1", "node1")

        key = guardian._pipeline_key("sess1", "node1")
        guardian._active_pipelines[key].last_step_time -= 400

        await guardian.check_signal_loss()
        assert len(guardian._active_pipelines) == 0

    async def test_no_signal_loss_if_within_timeout(self, guardian, read_log):
        await guardian.record_tool_call("generate_question", "sess1", "node1")
        await guardian.record_tool_call("score_answer", "sess1", "node1")

        await guardian.check_signal_loss()

        events = read_log()
        violations = [e for e in events if e["violation_type"] == "signal_loss"]
        assert len(violations) == 0


@pytest.mark.asyncio
class TestMultipleSessions:
    """Guardian tracks multiple sessions independently."""

    async def test_separate_sessions_independent(self, guardian, read_log):
        await guardian.record_tool_call("generate_question", "sess1", "node1")
        await guardian.record_tool_call("generate_question", "sess2", "node2")
        await guardian.record_tool_call("score_answer", "sess1", "node1")
        await guardian.record_tool_call("update_fsrs", "sess1", "node1")

        assert "sess2:node2" in guardian._active_pipelines
        assert "sess1:node1" not in guardian._active_pipelines
