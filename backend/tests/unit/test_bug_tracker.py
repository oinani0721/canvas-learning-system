# Canvas Learning System - BugTracker Unit Tests
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: testing)
"""
Unit tests for BugTracker service.

Tests cover:
- BugRecord model validation
- BugTracker.log_error() JSONL writing
- BugTracker.get_recent_bugs() reading
- bug_id format correctness
- Edge cases and error handling

[Source: docs/stories/21.5.3.story.md - Task 4]
[Source: docs/prd/EPIC-21.5-AGENT-RELIABILITY-FIX.md#story-21-5-3]
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from app.core.bug_tracker import BugRecord, BugTracker


class TestBugRecord:
    """Tests for BugRecord Pydantic model."""

    def test_bug_record_required_fields(self):
        """
        Test BugRecord with all required fields.

        [Source: docs/stories/21.5.3.story.md - AC-2]
        """
        record = BugRecord(
            bug_id="BUG-12345678",
            timestamp=datetime.now(timezone.utc),
            endpoint="/api/v1/test",
            error_type="ValueError",
            error_message="Test error",
            request_params={"key": "value"}
        )

        assert record.bug_id == "BUG-12345678"
        assert record.bug_id.startswith("BUG-")
        assert len(record.bug_id) == 12  # BUG- + 8 chars
        assert record.endpoint == "/api/v1/test"
        assert record.error_type == "ValueError"
        assert record.error_message == "Test error"
        assert record.request_params == {"key": "value"}

    def test_bug_record_optional_fields_default(self):
        """
        Test BugRecord optional fields have correct defaults.

        [Source: docs/stories/21.5.3.story.md - AC-2]
        """
        record = BugRecord(
            bug_id="BUG-ABCD1234",
            timestamp=datetime.now(timezone.utc),
            endpoint="/api/v1/test",
            error_type="TypeError",
            error_message="Type error",
            request_params={}
        )

        assert record.stack_trace is None
        assert record.user_action is None

    def test_bug_record_with_optional_fields(self):
        """Test BugRecord with all optional fields provided."""
        record = BugRecord(
            bug_id="BUG-EFGH5678",
            timestamp=datetime.now(timezone.utc),
            endpoint="/api/v1/agents/scoring",
            error_type="RuntimeError",
            error_message="Runtime error occurred",
            request_params={"canvas_path": "test.canvas"},
            stack_trace="Traceback (most recent call last):\n  File ...",
            user_action="User clicked scoring button"
        )

        assert record.stack_trace is not None
        assert "Traceback" in record.stack_trace
        assert record.user_action == "User clicked scoring button"

    def test_bug_record_model_dump_json(self):
        """
        Test BugRecord serialization to JSON.

        ✅ Verified from Context7:/websites/pydantic_dev (topic: model_dump_json)
        """
        record = BugRecord(
            bug_id="BUG-JSON1234",
            timestamp=datetime(2025, 12, 14, 10, 30, 0, tzinfo=timezone.utc),
            endpoint="/api/v1/test",
            error_type="ValueError",
            error_message="Test",
            request_params={"test": True}
        )

        json_str = record.model_dump_json()
        parsed = json.loads(json_str)

        assert parsed["bug_id"] == "BUG-JSON1234"
        assert "2025-12-14" in parsed["timestamp"]
        assert parsed["request_params"] == {"test": True}

    def test_bug_record_model_validate_json(self):
        """
        Test BugRecord deserialization from JSON.

        ✅ Verified from Context7:/websites/pydantic_dev (topic: model_validate_json)
        """
        json_str = json.dumps({
            "bug_id": "BUG-VALID123",
            "timestamp": "2025-12-14T10:30:00Z",
            "endpoint": "/api/v1/test",
            "error_type": "KeyError",
            "error_message": "Key not found",
            "request_params": {}
        })

        record = BugRecord.model_validate_json(json_str)

        assert record.bug_id == "BUG-VALID123"
        assert record.error_type == "KeyError"


class TestBugTracker:
    """Tests for BugTracker service."""

    def test_log_error_creates_directory(self, tmp_path: Path):
        """
        Test log_error automatically creates parent directory.

        [Source: docs/stories/21.5.3.story.md - AC-1]
        """
        log_path = tmp_path / "nested" / "dir" / "bug_log.jsonl"
        tracker = BugTracker(log_path=str(log_path))

        bug_id = tracker.log_error(
            endpoint="/api/v1/test",
            error=ValueError("Test error"),
            request_params={"test": True}
        )

        assert log_path.exists()
        assert bug_id.startswith("BUG-")

    def test_log_error_creates_file(self, tmp_path: Path):
        """
        Test log_error creates JSONL file.

        [Source: docs/stories/21.5.3.story.md - AC-1]
        """
        log_path = tmp_path / "test_bug_log.jsonl"
        tracker = BugTracker(log_path=str(log_path))

        bug_id = tracker.log_error(
            endpoint="/api/v1/test",
            error=ValueError("Test"),
            request_params={}
        )

        assert log_path.exists()
        assert bug_id.startswith("BUG-")
        assert len(bug_id) == 12  # BUG- + 8 hex chars

    def test_log_error_appends_jsonl(self, tmp_path: Path):
        """
        Test log_error appends records in JSONL format.

        [Source: docs/stories/21.5.3.story.md - AC-1]
        """
        log_path = tmp_path / "test.jsonl"
        tracker = BugTracker(log_path=str(log_path))

        # Log multiple errors
        tracker.log_error("/api/v1/a", ValueError("Error A"), {})
        tracker.log_error("/api/v1/b", TypeError("Error B"), {})
        tracker.log_error("/api/v1/c", KeyError("Error C"), {})

        # Read and verify
        lines = log_path.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 3

        # Each line should be valid JSON
        for line in lines:
            record = json.loads(line)
            assert "bug_id" in record
            assert "timestamp" in record
            assert "endpoint" in record

    def test_log_error_bug_id_format(self, tmp_path: Path):
        """
        Test bug_id follows format BUG-{uuid8}.

        [Source: docs/stories/21.5.3.story.md - AC-5]
        """
        log_path = tmp_path / "test.jsonl"
        tracker = BugTracker(log_path=str(log_path))

        bug_ids = set()
        for i in range(10):
            bug_id = tracker.log_error(
                endpoint=f"/api/v1/test/{i}",
                error=ValueError(f"Error {i}"),
                request_params={}
            )

            # Verify format
            assert bug_id.startswith("BUG-")
            assert len(bug_id) == 12
            # Verify hex characters after BUG-
            hex_part = bug_id[4:]
            assert all(c in "0123456789ABCDEF" for c in hex_part)

            bug_ids.add(bug_id)

        # All bug_ids should be unique
        assert len(bug_ids) == 10

    def test_log_error_captures_stack_trace(self, tmp_path: Path):
        """
        Test log_error captures stack trace.

        [Source: docs/stories/21.5.3.story.md - AC-2]
        """
        log_path = tmp_path / "test.jsonl"
        tracker = BugTracker(log_path=str(log_path))

        try:
            raise ValueError("Intentional error for testing")
        except ValueError as e:
            tracker.log_error(
                endpoint="/api/v1/test",
                error=e,
                request_params={}
            )

        content = log_path.read_text(encoding="utf-8")
        record = json.loads(content.strip())

        assert record["stack_trace"] is not None
        assert "Traceback" in record["stack_trace"]
        assert "Intentional error for testing" in record["stack_trace"]

    def test_log_error_captures_request_params(self, tmp_path: Path):
        """
        Test log_error captures request parameters.

        [Source: docs/stories/21.5.3.story.md - AC-2]
        """
        log_path = tmp_path / "test.jsonl"
        tracker = BugTracker(log_path=str(log_path))

        request_params = {
            "canvas_path": "test.canvas",
            "node_id": "node123",
            "query_params": {"limit": 10}
        }

        tracker.log_error(
            endpoint="/api/v1/agents/scoring",
            error=ValueError("Test"),
            request_params=request_params
        )

        content = log_path.read_text(encoding="utf-8")
        record = json.loads(content.strip())

        assert record["request_params"] == request_params

    def test_log_error_with_user_action(self, tmp_path: Path):
        """Test log_error with optional user_action parameter."""
        log_path = tmp_path / "test.jsonl"
        tracker = BugTracker(log_path=str(log_path))

        tracker.log_error(
            endpoint="/api/v1/test",
            error=ValueError("Test"),
            request_params={},
            user_action="User clicked submit button"
        )

        content = log_path.read_text(encoding="utf-8")
        record = json.loads(content.strip())

        assert record["user_action"] == "User clicked submit button"

    def test_get_recent_bugs_empty_file(self, tmp_path: Path):
        """
        Test get_recent_bugs returns empty list when file doesn't exist.

        [Source: docs/stories/21.5.3.story.md - AC-3]
        """
        log_path = tmp_path / "nonexistent.jsonl"
        tracker = BugTracker(log_path=str(log_path))

        bugs = tracker.get_recent_bugs()

        assert bugs == []

    def test_get_recent_bugs_returns_records(self, tmp_path: Path):
        """
        Test get_recent_bugs returns logged records.

        [Source: docs/stories/21.5.3.story.md - AC-3]
        """
        log_path = tmp_path / "test.jsonl"
        tracker = BugTracker(log_path=str(log_path))

        # Log some errors
        tracker.log_error("/api/v1/a", ValueError("A"), {})
        tracker.log_error("/api/v1/b", TypeError("B"), {})

        bugs = tracker.get_recent_bugs()

        assert len(bugs) == 2
        assert all(isinstance(bug, BugRecord) for bug in bugs)

    def test_get_recent_bugs_limit(self, tmp_path: Path):
        """
        Test get_recent_bugs respects limit parameter.

        [Source: docs/stories/21.5.3.story.md - AC-4]
        """
        log_path = tmp_path / "test.jsonl"
        tracker = BugTracker(log_path=str(log_path))

        # Log 10 errors
        for i in range(10):
            tracker.log_error(f"/api/v1/{i}", ValueError(f"Error {i}"), {})

        # Get with limit
        bugs = tracker.get_recent_bugs(limit=3)

        assert len(bugs) == 3

    def test_get_recent_bugs_newest_first(self, tmp_path: Path):
        """
        Test get_recent_bugs returns records in reverse order (newest first).

        [Source: docs/stories/21.5.3.story.md - AC-3]
        """
        log_path = tmp_path / "test.jsonl"
        tracker = BugTracker(log_path=str(log_path))

        # Log errors with distinct messages
        tracker.log_error("/api/v1/first", ValueError("First"), {})
        tracker.log_error("/api/v1/second", ValueError("Second"), {})
        tracker.log_error("/api/v1/third", ValueError("Third"), {})

        bugs = tracker.get_recent_bugs(limit=3)

        # Newest (third) should be first
        assert bugs[0].error_message == "Third"
        assert bugs[1].error_message == "Second"
        assert bugs[2].error_message == "First"

    def test_get_recent_bugs_default_limit(self, tmp_path: Path):
        """
        Test get_recent_bugs has default limit of 50.

        [Source: docs/stories/21.5.3.story.md - AC-4]
        """
        log_path = tmp_path / "test.jsonl"
        tracker = BugTracker(log_path=str(log_path))

        # Log 60 errors
        for i in range(60):
            tracker.log_error(f"/api/v1/{i}", ValueError(f"Error {i}"), {})

        # Get without limit (should use default 50)
        bugs = tracker.get_recent_bugs()

        assert len(bugs) == 50

    def test_get_recent_bugs_handles_malformed_lines(self, tmp_path: Path):
        """Test get_recent_bugs skips malformed JSON lines gracefully."""
        log_path = tmp_path / "test.jsonl"
        tracker = BugTracker(log_path=str(log_path))

        # Log valid error
        tracker.log_error("/api/v1/valid", ValueError("Valid"), {})

        # Manually append malformed line
        with open(log_path, "a", encoding="utf-8") as f:
            f.write("this is not valid json\n")

        # Log another valid error
        tracker.log_error("/api/v1/valid2", ValueError("Valid 2"), {})

        # Should only return valid records
        bugs = tracker.get_recent_bugs()

        assert len(bugs) == 2
        assert bugs[0].error_message == "Valid 2"
        assert bugs[1].error_message == "Valid"

    def test_clear_log(self, tmp_path: Path):
        """Test clear_log removes the log file."""
        log_path = tmp_path / "test.jsonl"
        tracker = BugTracker(log_path=str(log_path))

        # Log some errors
        tracker.log_error("/api/v1/test", ValueError("Test"), {})
        assert log_path.exists()

        # Clear log
        result = tracker.clear_log()

        assert result is True
        assert not log_path.exists()

    def test_clear_log_nonexistent_file(self, tmp_path: Path):
        """Test clear_log succeeds when file doesn't exist."""
        log_path = tmp_path / "nonexistent.jsonl"
        tracker = BugTracker(log_path=str(log_path))

        result = tracker.clear_log()

        assert result is True


class TestBugTrackerGlobalSingleton:
    """Tests for global bug_tracker singleton."""

    def test_global_singleton_exists(self):
        """Test global bug_tracker singleton is available."""
        from app.core.bug_tracker import bug_tracker

        assert bug_tracker is not None
        assert isinstance(bug_tracker, BugTracker)

    def test_global_singleton_default_path(self):
        """Test global singleton uses default path."""
        from app.core.bug_tracker import bug_tracker

        assert bug_tracker.log_path == Path("data/bug_log.jsonl")
