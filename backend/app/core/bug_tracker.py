# Canvas Learning System - Bug Tracker Service
# ✅ Verified from Context7:/websites/pydantic_dev (topic: model_dump_json model_validate_json)
"""
Bug tracking service for automatic 500 error logging.

This module provides persistent bug logging to JSONL files for debugging
and issue tracking purposes.

[Source: docs/stories/21.5.3.story.md - AC 1-5]
[Source: docs/prd/EPIC-21.5-AGENT-RELIABILITY-FIX.md#story-21-5-3]
[Source: specs/data/error-response.schema.json]
"""

import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import structlog

# ✅ Verified from Context7:/websites/pydantic_dev (topic: BaseModel)
from pydantic import BaseModel, Field

# Get logger instance
logger = structlog.get_logger(__name__)


class BugRecord(BaseModel):
    """
    Bug record model for storing error information.

    [Source: specs/data/error-response.schema.json]
    [Source: docs/stories/21.5.3.story.md - AC-2]

    Attributes:
        bug_id: Unique identifier (format: BUG-{uuid8})
        timestamp: When the error occurred
        endpoint: API endpoint path where error occurred
        error_type: Exception class name
        error_message: Error message string
        request_params: Request parameters (query params, body)
        stack_trace: Full stack trace (optional)
        user_action: Description of user action (optional)
    """

    bug_id: str = Field(..., description="Unique bug identifier (BUG-{uuid8})")
    timestamp: datetime = Field(..., description="Error occurrence timestamp")
    endpoint: str = Field(..., description="API endpoint path")
    error_type: str = Field(..., description="Exception class name")
    error_message: str = Field(..., description="Error message")
    request_params: dict = Field(default_factory=dict, description="Request parameters")
    stack_trace: Optional[str] = Field(None, description="Full stack trace")
    user_action: Optional[str] = Field(None, description="User action description")


class BugTracker:
    """
    Bug tracking service for automatic error logging.

    Logs all 500 errors to a JSONL file for debugging and issue tracking.
    Provides methods to log new errors and retrieve recent bug records.

    [Source: docs/prd/EPIC-21.5-AGENT-RELIABILITY-FIX.md#story-21-5-3]
    [Source: docs/stories/21.5.3.story.md - AC 1-5]

    Example:
        ```python
        from app.core.bug_tracker import bug_tracker

        # Log an error
        bug_id = bug_tracker.log_error(
            endpoint="/api/v1/agents/scoring",
            error=ValueError("Invalid input"),
            request_params={"canvas_path": "test.canvas"}
        )

        # Get recent bugs
        bugs = bug_tracker.get_recent_bugs(limit=10)
        ```
    """

    def __init__(self, log_path: str = "data/bug_log.jsonl"):
        """
        Initialize BugTracker with specified log file path.

        Args:
            log_path: Path to the JSONL log file (relative to backend directory)
        """
        self.log_path = Path(log_path)
        # Ensure parent directory exists
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log_error(
        self,
        endpoint: str,
        error: Exception,
        request_params: dict,
        user_action: Optional[str] = None
    ) -> str:
        """
        Log an error to the bug log file.

        [Source: docs/stories/21.5.3.story.md - AC-1, AC-2, AC-5]

        Args:
            endpoint: API endpoint path where error occurred
            error: The caught exception object
            request_params: Request parameters dictionary
            user_action: Optional description of user action

        Returns:
            str: Generated bug_id (format: BUG-{uuid8})

        Example:
            ```python
            bug_id = bug_tracker.log_error(
                endpoint="/api/v1/agents/scoring",
                error=ValueError("Test error"),
                request_params={"key": "value"}
            )
            # Returns: "BUG-A1B2C3D4"
            ```
        """
        # Generate unique bug_id
        # ✅ Verified from Python docs: uuid.uuid4().hex returns 32 hex chars
        bug_id = f"BUG-{uuid.uuid4().hex[:8].upper()}"

        # Create bug record
        record = BugRecord(
            bug_id=bug_id,
            timestamp=datetime.now(timezone.utc),
            endpoint=endpoint,
            error_type=type(error).__name__,
            error_message=str(error),
            request_params=request_params,
            stack_trace=traceback.format_exc(),
            user_action=user_action
        )

        # Append to JSONL file
        # ✅ Verified from Context7:/websites/pydantic_dev (topic: model_dump_json)
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(record.model_dump_json() + "\n")

            logger.info(
                "bug_logged",
                bug_id=bug_id,
                endpoint=endpoint,
                error_type=type(error).__name__
            )
        except Exception as write_error:
            # Don't fail the request if bug logging fails
            logger.error(
                "bug_log_write_failed",
                bug_id=bug_id,
                write_error=str(write_error)
            )

        return bug_id

    def get_recent_bugs(self, limit: int = 50) -> List[BugRecord]:
        """
        Get recent bug records from the log file.

        [Source: docs/stories/21.5.3.story.md - AC-3, AC-4]

        Args:
            limit: Maximum number of records to return (default: 50)

        Returns:
            List[BugRecord]: Bug records, newest first

        Example:
            ```python
            bugs = bug_tracker.get_recent_bugs(limit=10)
            for bug in bugs:
                print(f"{bug.bug_id}: {bug.error_message}")
            ```
        """
        if not self.log_path.exists():
            return []

        bugs: List[BugRecord] = []

        try:
            # ✅ Verified from Context7:/websites/pydantic_dev (topic: model_validate_json)
            with open(self.log_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            bugs.append(BugRecord.model_validate_json(line))
                        except Exception as parse_error:
                            # Skip malformed lines
                            logger.warning(
                                "bug_log_parse_error",
                                line_preview=line[:100],
                                error=str(parse_error)
                            )
        except Exception as read_error:
            logger.error(
                "bug_log_read_failed",
                error=str(read_error)
            )
            return []

        # Return last N records in reverse order (newest first)
        return bugs[-limit:][::-1]

    def clear_log(self) -> bool:
        """
        Clear the bug log file (for testing/maintenance).

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if self.log_path.exists():
                self.log_path.unlink()
            return True
        except Exception as e:
            logger.error("bug_log_clear_failed", error=str(e))
            return False


# Global singleton instance
# [Source: docs/stories/21.5.3.story.md - "全局单例"]
bug_tracker = BugTracker()
