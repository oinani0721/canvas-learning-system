"""Trace query endpoint: aggregate all logs by request_id.

GET /api/v1/traces/{request_id} returns a timeline of all events
from bug_log, audit, failed_edge_syncs, and dead_letter.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter()

DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"
LOGS_DIR = Path(__file__).parent.parent.parent.parent / "logs"

LOG_FILES = {
    "bug_log": DATA_DIR / "bug_log.jsonl",
    "failed_edge_syncs": DATA_DIR / "failed_edge_syncs.jsonl",
    "dead_letter_episodes": DATA_DIR / "dead_letter_episodes.jsonl",
    "audit": LOGS_DIR / "audit.jsonl",
}


def _search_jsonl(file_path: Path, request_id: str) -> List[Dict[str, Any]]:
    """Search a JSONL file for entries matching request_id."""
    results: List[Dict[str, Any]] = []
    if not file_path.exists():
        return results
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    if entry.get("request_id") == request_id:
                        results.append(entry)
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        logger.warning(f"Failed to read {file_path}: {e}")
    return results


@router.get(
    "/traces/{request_id}",
    summary="Query request trace",
    description="Aggregate all log file entries matching the given request_id",
)
async def get_trace(request_id: str) -> Dict[str, Any]:
    """Return a timeline of all logged events for a given request_id."""
    timeline: List[Dict[str, Any]] = []
    for source_name, file_path in LOG_FILES.items():
        entries = _search_jsonl(file_path, request_id)
        for entry in entries:
            entry["_source"] = source_name
            timeline.append(entry)

    # Sort by timestamp if available
    timeline.sort(key=lambda e: str(e.get("timestamp", "")))

    return {
        "request_id": request_id,
        "total_events": len(timeline),
        "timeline": timeline,
    }
