# Canvas Learning System - Audit Guardian
# Story 3.2: MCP Tool Exposure (AC-4)
#
# Asynchronous audit layer that detects pipeline violations:
# - Signal loss (scoring without BKT/FSRS update)
# - Step skipping (update without prior scoring)
# - Time anomalies (step interval > 5 minutes)
#
# Audit is non-blocking: uses asyncio.create_task so tool calls are not delayed.
#
# [Source: _bmad-output/implementation-artifacts/3-2-mcp-tool-exposure-backend-api.md#Task 4]
# [Source: architecture.md#6-layer-defense — Layer 4: Audit Guardian]

import asyncio
import json
import logging
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Maximum time between pipeline steps (5 minutes)
MAX_STEP_INTERVAL_SECONDS = 300

# Audit log file path
AUDIT_LOG_DIR = Path(__file__).parent.parent.parent / "logs"
AUDIT_LOG_FILE = AUDIT_LOG_DIR / "audit.jsonl"


@dataclass
class AuditEvent:
    """A single audit event record."""

    timestamp: float
    event_type: str  # "tool_call" | "violation"
    tool_name: str
    session_id: str
    node_id: str
    details: Dict = field(default_factory=dict)
    violation_type: Optional[str] = None  # "signal_loss" | "step_skip" | "time_anomaly"
    request_id: Optional[str] = None  # Correlation ID from logging middleware


@dataclass
class PipelineState:
    """Tracks the state of an active pipeline for a session+node pair."""

    session_id: str
    node_id: str
    last_step: str
    last_step_time: float
    steps_completed: List[str] = field(default_factory=list)


class AuditGuardian:
    """
    Async audit guardian that monitors MCP tool call pipelines.

    Story 3.2 AC-4:
    - Detects pipeline violations (signal loss, step skipping, time anomaly)
    - Writes violations to backend/logs/audit.jsonl
    - Runs asynchronously (does not block tool calls)

    Detection rules:
    1. Signal loss: score_answer completed but no update_fsrs/update_bkt within 5 minutes
    2. Step skip: update_fsrs/update_bkt called without prior score_answer
    3. Time anomaly: interval between pipeline steps exceeds 5 minutes
    """

    def __init__(self) -> None:
        self._active_pipelines: Dict[str, PipelineState] = {}
        self._lock = asyncio.Lock()
        self._ensure_log_directory()

    def _ensure_log_directory(self) -> None:
        """Create the audit log directory if it does not exist."""
        AUDIT_LOG_DIR.mkdir(parents=True, exist_ok=True)

    def _pipeline_key(self, session_id: str, node_id: str) -> str:
        """Generate a unique key for a session+node pair."""
        return f"{session_id}:{node_id}"

    async def record_tool_call(
        self,
        tool_name: str,
        session_id: str,
        node_id: str,
        request_id: Optional[str] = None,
    ) -> None:
        """
        Record a tool call and check for pipeline violations.

        This method is designed to be called via asyncio.create_task()
        so it does not block the tool execution.

        Args:
            tool_name: Name of the MCP tool that was called.
            session_id: The dialogue session identifier.
            node_id: The canvas node identifier.
            request_id: Optional correlation request ID from middleware.
        """
        now = time.time()
        key = self._pipeline_key(session_id, node_id)

        # Record the tool call event
        call_event = AuditEvent(
            timestamp=now,
            event_type="tool_call",
            tool_name=tool_name,
            session_id=session_id,
            node_id=node_id,
            request_id=request_id,
        )
        await self._write_event(call_event)

        async with self._lock:
            # Pipeline-aware tools
            pipeline_tools = {
                "generate_question",
                "score_answer",
                "update_fsrs",
                "update_bkt",
            }

            if tool_name not in pipeline_tools:
                return

            state = self._active_pipelines.get(key)

            # Check for step skipping
            if tool_name in ("update_fsrs", "update_bkt"):
                if state is None or "score_answer" not in state.steps_completed:
                    await self._record_violation(
                        violation_type="step_skip",
                        tool_name=tool_name,
                        session_id=session_id,
                        node_id=node_id,
                        details={
                            "message": f"'{tool_name}' called without prior 'score_answer'",
                            "steps_completed": state.steps_completed if state else [],
                        },
                    )

            # Check for time anomaly
            if state is not None and tool_name != "generate_question":
                interval = now - state.last_step_time
                if interval > MAX_STEP_INTERVAL_SECONDS:
                    await self._record_violation(
                        violation_type="time_anomaly",
                        tool_name=tool_name,
                        session_id=session_id,
                        node_id=node_id,
                        details={
                            "interval_seconds": round(interval, 2),
                            "max_allowed": MAX_STEP_INTERVAL_SECONDS,
                            "previous_step": state.last_step,
                        },
                    )

            # Update pipeline state
            if tool_name == "generate_question":
                # Start a new pipeline
                self._active_pipelines[key] = PipelineState(
                    session_id=session_id,
                    node_id=node_id,
                    last_step=tool_name,
                    last_step_time=now,
                    steps_completed=[tool_name],
                )
            elif state is not None:
                state.last_step = tool_name
                state.last_step_time = now
                state.steps_completed.append(tool_name)

                # Pipeline complete after update step
                if tool_name in ("update_fsrs", "update_bkt"):
                    del self._active_pipelines[key]

    async def check_signal_loss(self) -> None:
        """
        Check for signal loss: pipelines stuck at score_answer without subsequent update.

        Should be called periodically (e.g., every 60 seconds) to detect
        abandoned pipelines where scoring happened but FSRS/BKT was never updated.
        """
        now = time.time()
        expired_keys = []

        async with self._lock:
            for key, state in self._active_pipelines.items():
                if (
                    state.last_step == "score_answer"
                    and now - state.last_step_time > MAX_STEP_INTERVAL_SECONDS
                ):
                    await self._record_violation(
                        violation_type="signal_loss",
                        tool_name="score_answer",
                        session_id=state.session_id,
                        node_id=state.node_id,
                        details={
                            "message": "score_answer completed but no update_fsrs/update_bkt followed",
                            "elapsed_seconds": round(now - state.last_step_time, 2),
                        },
                    )
                    expired_keys.append(key)

            # Clean up expired pipelines
            for key in expired_keys:
                del self._active_pipelines[key]

    async def _record_violation(
        self,
        violation_type: str,
        tool_name: str,
        session_id: str,
        node_id: str,
        details: Dict,
    ) -> None:
        """Record a pipeline violation event."""
        event = AuditEvent(
            timestamp=time.time(),
            event_type="violation",
            tool_name=tool_name,
            session_id=session_id,
            node_id=node_id,
            violation_type=violation_type,
            details=details,
        )
        await self._write_event(event)
        logger.warning(
            f"[Story 3.2] Audit violation: {violation_type} "
            f"tool={tool_name} session={session_id} node={node_id} "
            f"details={details}"
        )

    async def _write_event(self, event: AuditEvent) -> None:
        """Write an audit event to the JSONL log file."""
        try:
            line = json.dumps(asdict(event), ensure_ascii=False) + "\n"
            # Use asyncio to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._append_to_file, line)
        except Exception as e:
            logger.error(f"[Story 3.2] Failed to write audit event: {e}")

    def _append_to_file(self, line: str) -> None:
        """Synchronous file append (run in executor)."""
        with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line)


# Singleton instance
_guardian: Optional[AuditGuardian] = None


def get_audit_guardian() -> AuditGuardian:
    """Get or create the singleton AuditGuardian."""
    global _guardian
    if _guardian is None:
        _guardian = AuditGuardian()
    return _guardian
