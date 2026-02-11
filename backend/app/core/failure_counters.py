# Story 36.12: Shared failure counters for observability.
#
# Module-level counters accessible from both services (writers)
# and health endpoint (reader). Thread-safe via threading.Lock.
#
# Dead-letter files: append-mode JSONL for post-mortem analysis.
#
# [Source: docs/stories/36.12.story.md#AC-36.12.4, AC-36.12.5]
import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# --- Counters (thread-safe) ---
_counter_lock = threading.Lock()
_edge_sync_failure_count: int = 0
_dual_write_failure_count: int = 0

# --- Dead-letter file paths ---
EDGE_SYNC_DEAD_LETTER_PATH: Path = (
    Path(__file__).parent.parent.parent / "data" / "failed_edge_syncs.jsonl"
)
DUAL_WRITE_DEAD_LETTER_PATH: Path = (
    Path(__file__).parent.parent.parent / "data" / "failed_dual_writes.jsonl"
)


def increment_edge_sync_failures() -> int:
    """Increment edge sync failure counter. Returns new count."""
    global _edge_sync_failure_count
    with _counter_lock:
        _edge_sync_failure_count += 1
        return _edge_sync_failure_count


def increment_dual_write_failures() -> int:
    """Increment dual-write failure counter. Returns new count."""
    global _dual_write_failure_count
    with _counter_lock:
        _dual_write_failure_count += 1
        return _dual_write_failure_count


def get_edge_sync_failures() -> int:
    """Get current edge sync failure count."""
    with _counter_lock:
        return _edge_sync_failure_count


def get_dual_write_failures() -> int:
    """Get current dual-write failure count."""
    with _counter_lock:
        return _dual_write_failure_count


def reset_counters() -> dict:
    """Reset all failure counters. Returns previous values."""
    global _edge_sync_failure_count, _dual_write_failure_count
    with _counter_lock:
        prev = {
            "edge_sync_failures": _edge_sync_failure_count,
            "dual_write_failures": _dual_write_failure_count,
        }
        _edge_sync_failure_count = 0
        _dual_write_failure_count = 0
        return prev


def write_dead_letter(
    file_path: Path,
    entry_type: str,
    error: str,
    *,
    edge_id: Optional[str] = None,
    canvas_name: Optional[str] = None,
    episode_id: Optional[str] = None,
    retry_count: int = 0,
    timeout_ms: Optional[int] = None,
) -> None:
    """
    Append a failure record to a dead-letter JSONL file.

    AC-36.12.8: Append mode + utf-8 encoding, survives service restarts.

    Args:
        file_path: Path to the dead-letter JSONL file
        entry_type: "edge_sync" or "dual_write"
        error: Error message
        edge_id: Edge ID (for edge_sync failures)
        canvas_name: Canvas name (for edge_sync failures)
        episode_id: Episode ID (for dual_write failures)
        retry_count: Number of retries attempted
        timeout_ms: Timeout in milliseconds (for dual_write timeouts)
    """
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": entry_type,
        "error": error,
        "retry_count": retry_count,
    }
    if edge_id is not None:
        entry["edge_id"] = edge_id
    if canvas_name is not None:
        entry["canvas_name"] = canvas_name
    if episode_id is not None:
        entry["episode_id"] = episode_id
    if timeout_ms is not None:
        entry["timeout_ms"] = timeout_ms

    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        # NOTE: Synchronous file I/O by design — single-line JSONL append is
        # fast enough (~μs) to be acceptable in an async context.  If dead-letter
        # volume grows, consider asyncio.to_thread() or aiofiles.
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.error(f"Failed to write dead-letter entry to {file_path}: {e}")
