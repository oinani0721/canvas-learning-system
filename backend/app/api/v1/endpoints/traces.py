"""Trace query endpoint: aggregate all logs by request_id.

GET /api/v1/traces/{request_id} returns a timeline of all events
from bug_log, audit, failed_edge_syncs, and dead_letter.

POST /api/v1/traces/replay-fallbacks (鉴权) 手动触发 Neo4j 降级暂存链回灌
—— CARD-NEO4J-REPLAY-WIRE (BATCH-2026-09-11-第十四批)。
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends

from app.clients.neo4j_client import DEFAULT_STORAGE_PATH as NEO4J_MEMORY_FILE
from app.core.failed_writes_constants import FAILED_WRITES_FILE
from app.core.failure_counters import (
    DUAL_WRITE_DEAD_LETTER_PATH,
    EDGE_SYNC_DEAD_LETTER_PATH,
    bound_from_env,
    count_lines,
    overflow_siblings,
)
from app.security import require_internal_api_key
from app.services.event_bus import OUTBOX_FILE
from app.services.fallback_sync_service import (
    CANVAS_EVENTS_FALLBACK_FILE,
    LEARNING_MEMORIES_FILE,
    get_fallback_sync_service,
)

logger = logging.getLogger(__name__)
router = APIRouter()

# ⚠️ CARD-NEO4J-REPLAY-BOUND (T6-C): 本文件在 backend/app/api/v1/endpoints/，
# 原先的 4 层 ``.parent`` 只走到 **backend/app** ⇒ DATA_DIR 解析成
# ``backend/app/data``（实测该目录根本不存在），而全部死信文件写在
# ``backend/data``（写侧 failure_counters.py / failed_writes_constants.py 从
# ``backend/app/core/`` 走 3 层 ``.parent`` 恰好到 backend）。LOGS_DIR 同错
# （``audit.jsonl`` 在 backend/logs）。于是 ``/traces/{request_id}`` 的 summary
# 宣称聚合 bug_log / failed_edge_syncs / dead_letter_episodes / audit，实际读的
# 是空目录，**恒查不到** —— DD-13 名实不符。``parents[4]`` == backend。
#
# ⚠️ 但**别把这处修复说得比它实际管用**（独立复核 2026-09-15 MEDIUM 更正了
# 初版注释的过强表述）：四个源里只有 ``failed_edge_syncs``（写侧
# ``failure_counters.py`` 的 ``parent.parent.parent/"data"``）与 ``audit``
# 是绝对锚，改对目录就真读得到。``bug_log`` 与 ``dead_letter_episodes`` 的
# 写侧是 **cwd 相对**路径（``episode_worker.py:224`` 的默认参数
# ``"data/dead_letter_episodes.jsonl"``），只有在 cwd=backend 时才与这里一致；
# cwd 不是 backend 时它们仍然对不上，而那不是本卡能在读侧修的。
_BACKEND_DIR = Path(__file__).resolve().parents[4]

DATA_DIR = _BACKEND_DIR / "data"
LOGS_DIR = _BACKEND_DIR / "logs"

LOG_FILES = {
    "bug_log": DATA_DIR / "bug_log.jsonl",
    "failed_edge_syncs": DATA_DIR / "failed_edge_syncs.jsonl",
    "dead_letter_episodes": DATA_DIR / "dead_letter_episodes.jsonl",
    "audit": LOGS_DIR / "audit.jsonl",
}

# Neo4j 离线降级时的全部暂存链。
#
# ⚠️ 每条链的路径**按它自己的写侧锚点取**，不统一套 DATA_DIR：
# ``canvas_events_fallback.json`` 的写侧（canvas_service.py:96）用的是
# ``Path(__file__).parent.parent / "data"``，落 **backend/app/data**，与其余
# 六条（backend/data）不是同一个目录。统一套 DATA_DIR 会让它恒 exists=False
# —— 报「不存在」而其实一直在写，又是一处 DD-13。
#
# 能 import 到常量的一律直接 import，不手抄路径（手抄的两份清单必然漂移）。
# 唯一的例外是 ``dead_letter_episodes.jsonl``：它的写侧
# （episode_worker.py:224）是**函数参数默认值** ``"data/dead_letter_episodes.jsonl"``，
# 相对 cwd 解析，没有模块常量可 import。运行时 cwd=backend 时与下面一致；
# cwd 不是 backend 时实际落点会不同，本表报的就会是另一个位置。
BACKLOG_FILES: Dict[str, Path] = {
    "failed_writes.jsonl": FAILED_WRITES_FILE,
    "failed_edge_syncs.jsonl": EDGE_SYNC_DEAD_LETTER_PATH,
    "failed_dual_writes.jsonl": DUAL_WRITE_DEAD_LETTER_PATH,
    "dead_letter_episodes.jsonl": DATA_DIR / "dead_letter_episodes.jsonl",
    "neo4j_memory.json": NEO4J_MEMORY_FILE,
    "learning_memories.json": LEARNING_MEMORIES_FILE,
    "canvas_events_fallback.json": CANVAS_EVENTS_FALLBACK_FILE,
    # Tier-2 事件 outbox（event_bus.py:49）：图写入重试耗尽后落这里。它同样是
    # 一条 Neo4j 降级暂存链，初版漏了它，而本端点的 description 写的是
    # 「every Neo4j-degradation staging file」⇒ 少报一处积压 = DD-13
    # （独立复核 2026-09-15 指出）。本卡只读它，写侧有界属 event_bus 地盘。
    "outbox/events.jsonl": OUTBOX_FILE,
}

# backlog 扫时间戳的尺寸闸（Codex round-1 M3）。超过它就只报行数与尺寸、不扫
# 时间戳，并在该条目上标 degraded —— 按行迭代会把一整行读进内存，一条没有换行
# 的超长记录足以撑爆它。8 MiB ≈ 上限 10000 行 × 每行 ~800 B 的两倍余量。
# env 覆盖：CLS_BACKLOG_SCAN_MAX_BYTES。
BACKLOG_SCAN_MAX_BYTES: int = bound_from_env("CLS_BACKLOG_SCAN_MAX_BYTES", 8 * 1024 * 1024, minimum=1)


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


def _display_path(path: Path) -> str:
    """相对仓根的路径；算不出来就只给文件名。

    本路由与兄弟 ``/traces/{request_id}`` 一样**无鉴权**，所以不回绝对路径
    （那会把文件系统布局暴露给任何能打到端口的人）。

    ⚠️ 锚点是 ``_BACKEND_DIR`` 而不是仓根（独立复核 2026-09-15 MEDIUM）。
    初版用 ``parents[5]`` 当仓根，在容器等「backend 不在第 5 层」的布局里会
    退化：若仓根解析成 ``/``，``relative_to`` **不会**失败，而是原样回整条
    绝对路径（只少一个前导斜杠）—— 脱敏静默失效，门还全绿。
    七条链全部位于 ``backend/`` 之下，所以按 backend 锚是部署无关的。

    ⚠️ 捕获面是 ``Exception`` 而不是 ``(ValueError, OSError)``（Codex round-1
    L2）：符号链接成环时 ``Path.resolve()`` 在 Python < 3.13 抛的是
    ``RuntimeError``，两者都不是它的子类。而 ``_safe_backlog_entry`` 的降级
    分支**又会调用本函数**，于是这一处漏网会让异常逃出整条路由变成 500 ——
    降级路径上的函数自己必须不可抛。``path.name`` 是纯字符串运算，安全。
    """
    try:
        return "backend/" + str(path.resolve().relative_to(_BACKEND_DIR))
    except Exception:  # noqa: BLE001 — 见 docstring：降级路径不得成为新的失败点
        return path.name


def _first_last_timestamp(path: Path, *, max_bytes: int) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """单趟扫出首/末条**可解析且带 timestamp** 的条目时间戳。

    坏行 / 空行 / 非 dict 一律跳过——死信文件正是在系统出问题时写的，
    里面有半截行很正常，不该让只读端点 500。

    ⚠️ 内存不是无条件 O(1)（Codex round-1 M3 更正了初版这处过强的说法）：
    按行迭代会把**一整行**读进内存，一条没有换行的超长记录就能撑爆它。
    所以按 ``max_bytes`` 设闸：文件超过这个尺寸就**完全不扫**，直接返回
    ``truncated=True``，由调用方如实标记，而不是报一个扫了一半的时间戳。

    Returns:
        ``(oldest, newest, reason)``。``reason`` 为 ``None`` 表示完整扫完；
        非 ``None`` 时 oldest/newest 不可信，值是**机器可读的原因**：
        ``size_capped``（尺寸超闸，没扫）/ ``stat:<ExcName>``（量尺寸就失败）/
        ``read:<ExcName>``（扫到一半失败）。
        ⚠️ 「跳过」与「失败」必须分开报：合成一个 ``truncated=True`` 会让
        「文件太大所以没看」和「看了但读坏了」在响应里无法区分。
    """
    first: Optional[str] = None
    last: Optional[str] = None
    try:
        if path.stat().st_size > max_bytes:
            logger.info("[T6-C] %s 超过扫描上限 %d B, 跳过时间戳扫描", path.name, max_bytes)
            return None, None, "size_capped"
    except OSError as e:
        logger.warning(f"Failed to size {path} before scan: {e}")
        return None, None, f"stat:{type(e).__name__}"
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(entry, dict):
                    continue
                ts = entry.get("timestamp")
                if ts is None:
                    continue
                if first is None:
                    first = str(ts)
                last = str(ts)
    except OSError as e:
        logger.warning(f"Failed to scan timestamps in {path}: {e}")
        return first, last, f"read:{type(e).__name__}"
    return first, last, None


def _backlog_entry(name: str, path: Path) -> Dict[str, Any]:
    """一条暂存链的积压快照。

    ⚠️ ``backlog`` 只对 JSONL 有意义（= 行数）。``neo4j_memory.json`` /
    ``canvas_events_fallback.json`` 是整块 JSON，没有「第几条」可言 ⇒
    ``backlog`` / ``oldest`` / ``newest`` 一律 ``None``，改看 ``size_bytes``
    与 ``mtime``。**不**把 mtime 塞进 ``newest`` 冒充条目时间戳——那是
    DD-13 名实不符，读的人会以为那是最后一条记录的时间。

    ⚠️ ``backlog`` 只数**活动文件**。写侧上限触发后，真正的积压在
    ``.overflow.*`` 兄弟里，所以必须同时报 ``overflow_files`` /
    ``overflow_bytes``，否则轮转一次就会把「积压 10000 条」报成「积压 3 条」。

    ⚠️ **部分失败必须留痕**（Codex round-1 M2）。初版把每一处 ``except OSError``
    都写成「记个日志然后接着走」，于是「归档目录列不出来」和「真的一个归档都
    没有」在响应里**长得一模一样**（``overflow_files=0``、无 ``error``）——
    读的人会把「没测到」当成「没积压」，正是本卡要修的那类 DD-13。
    现在每一处降级都往 ``degraded`` 里追加一个**机器可读的原因标签**，并置
    ``partial=True``；顶层再据此给出 ``incomplete``。
    标签只放原因名（如 ``overflow_scan:PermissionError``），**不放 ``str(e)``**
    —— 本路由无鉴权，而 ``OSError`` 的消息通常内嵌绝对路径。
    """
    entry: Dict[str, Any] = {
        "name": name,
        "path": _display_path(path),
        "kind": "jsonl" if path.suffix == ".jsonl" else "json",
        "exists": False,
        "backlog": None,
        "oldest": None,
        "newest": None,
        "size_bytes": 0,
        "mtime": None,
        "overflow_files": 0,
        "overflow_bytes": 0,
        "partial": False,
        "degraded": [],
    }

    def _degrade(reason: str) -> None:
        entry["partial"] = True
        entry["degraded"].append(reason)

    try:
        siblings = overflow_siblings(path)
        entry["overflow_files"] = len(siblings)
        entry["overflow_bytes"] = sum(p.stat().st_size for p in siblings if p.exists())
    except OSError as e:
        logger.warning(f"Failed to stat overflow siblings of {path}: {e}")
        _degrade(f"overflow_scan:{type(e).__name__}")

    if not path.exists():
        if entry["kind"] == "jsonl":
            entry["backlog"] = 0
        return entry

    entry["exists"] = True
    try:
        stat = path.stat()
        entry["size_bytes"] = stat.st_size
        entry["mtime"] = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
    except OSError as e:
        logger.warning(f"Failed to stat {path}: {e}")
        _degrade(f"stat:{type(e).__name__}")

    if entry["kind"] == "jsonl":
        try:
            entry["backlog"] = count_lines(path)
        except OSError as e:
            logger.warning(f"Failed to count lines in {path}: {e}")
            _degrade(f"count_lines:{type(e).__name__}")
        oldest, newest, scan_reason = _first_last_timestamp(path, max_bytes=BACKLOG_SCAN_MAX_BYTES)
        entry["oldest"], entry["newest"] = oldest, newest
        if scan_reason is not None:
            _degrade(f"timestamp_scan:{scan_reason}")
    return entry


def _safe_backlog_entry(name: str, path: Path) -> Dict[str, Any]:
    """一条链读失败不得让另外六条也看不见。

    ⚠️ 只回 ``type(e).__name__``，**不回 ``str(e)``**：本路由无鉴权，而
    ``OSError`` 的消息通常内嵌绝对路径。完整信息只进服务端日志。
    （兄弟端点 ``/traces/replay-fallbacks`` 回了 ``str(e)``，但它在
    ``require_internal_api_key`` 后面，受众不同。）
    """
    try:
        return _backlog_entry(name, path)
    except Exception as e:  # noqa: BLE001 — 观测端点对单链故障必须降级而非整体 500
        logger.exception(f"Failed to read backlog for {name} ({path})")
        return {
            "name": name,
            "path": _display_path(path),
            "kind": "jsonl" if path.suffix == ".jsonl" else "json",
            "exists": None,
            "backlog": None,
            "oldest": None,
            "newest": None,
            "size_bytes": None,
            "mtime": None,
            "overflow_files": 0,
            "overflow_bytes": 0,
            "partial": True,
            "degraded": [f"entry:{type(e).__name__}"],
            "error": type(e).__name__,
        }


@router.get(
    # ⛔ 必须声明在 ``/traces/{request_id}`` **之前**。FastAPI/Starlette 按
    # 声明序匹配路径，放在后面会被动态段吃掉（request_id="dead-letter-backlog"，
    # 返回空 timeline 而不是 backlog）。实测改前正是这个形态。
    "/traces/dead-letter-backlog",
    summary="Neo4j fallback backlog snapshot",
    description=(
        "Read-only snapshot of every Neo4j-degradation staging file: how many "
        "entries are waiting, how old the oldest one is, and how much has been "
        "rotated out to .overflow.* siblings by the write-side bound. "
        "`backlog` is a line count and only applies to JSONL chains; the two "
        "whole-JSON chains report `size_bytes`/`mtime` instead and leave "
        "`backlog`/`oldest`/`newest` null. `oldest`/`newest` are the "
        "`timestamp` fields of the first/last parsable entry, not file mtimes. "
        "`backlog` counts the ACTIVE file only — rotated entries are counted "
        "separately as `overflow_files`/`overflow_bytes`. "
        "PARTIAL READS ARE FLAGGED, NOT SILENTLY ZEROED: any chain whose "
        "overflow scan, stat, line count, or timestamp scan degraded carries "
        "`partial: true` plus machine-readable reasons in `degraded` (e.g. "
        "`overflow_scan:PermissionError`, `timestamp_scan:size_capped`). The "
        "top level then reports `incomplete: true` and lists `degraded_chains`. "
        "When `incomplete` is true, `total_backlog` is a LOWER BOUND, not the "
        "real figure — do not render it as 'nothing is queued'. Files larger "
        "than CLS_BACKLOG_SCAN_MAX_BYTES skip the timestamp scan entirely. "
        "Purely read-only: this endpoint never rotates, deletes, or replays "
        "anything."
    ),
)
async def get_dead_letter_backlog() -> Dict[str, Any]:
    """Return per-chain backlog for all Neo4j offline staging files.

    ⚠️ 整段文件 I/O 走 ``asyncio.to_thread``（Codex round-1 M3）。数行与时间戳
    解析都是同步阻塞调用，直接写在 ``async def`` 里会在大文件上把事件循环按住，
    连累同进程的其他请求。观测端点尤其不该在系统出问题（= 文件最大）时拖垮它
    要观测的那个系统。
    """
    files = await asyncio.to_thread(lambda: [_safe_backlog_entry(name, path) for name, path in BACKLOG_FILES.items()])
    incomplete = any(f.get("partial") or f.get("error") for f in files)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "files": files,
        # 只把 JSONL 的行数求和；None 跳过而不是当 0 —— 「未知」不该被算成
        # 「空」（同 /traces/replay-fallbacks 对 pending=-1 的口径）。
        "total_backlog": sum(f["backlog"] or 0 for f in files),
        "total_overflow_files": sum(f["overflow_files"] for f in files),
        # ⛔ 有任何一条链降级，合计数就是**下界**而不是真值。不给这个标记的话
        # 「读不到」会和「真的没有」在响应里无法区分（Codex round-1 M2）。
        "incomplete": incomplete,
        "degraded_chains": [f["name"] for f in files if f.get("partial") or f.get("error")],
    }


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
