"""Trace query endpoint: aggregate all logs by request_id.

GET /api/v1/traces/{request_id} returns a timeline of all events
from bug_log, audit, failed_edge_syncs, and dead_letter.

POST /api/v1/traces/replay-fallbacks (鉴权) 手动触发 Neo4j 降级暂存链回灌
—— CARD-NEO4J-REPLAY-WIRE (BATCH-2026-09-11-第十四批)。
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, Depends

from app.security import require_internal_api_key
from app.services.fallback_sync_service import get_fallback_sync_service

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


@router.post(
    "/traces/replay-fallbacks",
    summary="Replay Neo4j fallback backlog",
    description=(
        "Manually trigger replay of the Neo4j degradation fallback files "
        "(failed_writes / canvas_events / learning_memories) back into Neo4j. "
        "Startup already replays automatically when Neo4j is up (app/main.py); "
        "this endpoint covers recovery that happens mid-run, when the process "
        "is past its startup window. "
        "failed_writes and canvas_events entries are removed from their file "
        "once replayed, so a second call reports recovered=0 for those two. "
        "learning_memories is deliberately NOT rotated (the runtime still "
        "queries it), so that chain is replayed in full on every call — "
        "idempotent in the graph (MERGE + SET only) but its recovered count "
        "does not drop to zero. "
        "NOTE: a chain's `pending` may be -1, meaning the remaining count is "
        "UNKNOWN (the file could not be read, or finalize could not complete); "
        "such a chain also carries an `error` field. Clients aggregating "
        "`pending` must skip negative values instead of summing them. "
        "Requires the X-CLS-Internal-Key header."
    ),
    # 端点级鉴权 — 本 router 是裸 ``APIRouter()`` (无路由级依赖), 与
    # ``/system/*`` (api/v1/system.py:35) 逐字同口径: 缺/错 key → 403,
    # 生产态未配置 key → 503。⛔ 不改 app/security.py (T5-D 地盘), 只 import。
    dependencies=[Depends(require_internal_api_key)],
    # 必须同批声明, 否则 tests/contract/test_openapi_contract.py 的
    # schemathesis status_code_conformance 会因「返回了 schema 里没声明的 403」
    # 把本端点打红。文案与 endpoints/sync.py:64-72 同形。
    responses={
        403: {"description": "Invalid or missing internal API key"},
        503: {"description": "Internal API key not configured (production fail-closed)"},
    },
)
async def replay_fallbacks() -> Dict[str, Any]:
    """Replay the Neo4j fallback backlog and return the sync stats verbatim.

    CARD-NEO4J-REPLAY-WIRE: ``FallbackSyncService.sync_all_fallbacks`` was a
    fully implemented replayer with **zero production callers** — four offline
    staging chains kept accumulating writes with nothing ever draining them.
    This endpoint is one of its two production call sites (the other is the
    startup backfill gate in ``app/main.py``).

    ``sync_all_fallbacks`` self-checks Neo4j availability first
    (``is_fallback_mode`` / ``health_check``) and returns
    ``{"skipped": True, "reason": ...}`` when it is still down — so calling
    this while Neo4j is unreachable is a no-op, not an error.

    Returns:
        The stats dict from ``sync_all_fallbacks`` verbatim: per-file
        ``{"recovered": int, "pending": int}`` (plus ``"error"`` when that
        file's replay raised), or ``{"skipped": True, "reason": str}``.

        ⚠️ ``pending`` may be **-1**, which means *unknown* — not "minus one
        entry". It is returned when the chain could not be read or its finalize
        step could not complete, so the number of remaining entries cannot be
        counted. Such a chain always carries ``error`` as well. Callers that
        aggregate ``pending`` must skip negative values rather than summing
        them (summing turns "unknown" into a number that cancels out other
        chains' real backlog). See ``fallback_sync_service._PROGRESS_VERSION``
        area for the same rule applied internally.

        ⚠️ The happy path is counts only, but the ``error`` and ``reason``
        fields carry ``str(e)`` of the underlying exception — an ``OSError``
        there will typically embed an absolute path, and a driver error may
        embed a host/port. This endpoint is behind ``require_internal_api_key``,
        so the audience is limited, but the text itself is **not** filtered.
        Do not widen the audience without adding redaction.
        (Codex round-1 ③ — an earlier version of this docstring claimed no
        paths were echoed back, which was not true of those two fields.)
    """
    stats = await get_fallback_sync_service().sync_all_fallbacks()
    logger.info("[T6-B] manual fallback replay via admin endpoint: %s", stats)
    return stats
