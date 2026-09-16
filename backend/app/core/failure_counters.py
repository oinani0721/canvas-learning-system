# Story 36.12: Shared failure counters for observability.
#
# Module-level counters accessible from both services (writers)
# and health endpoint (reader). Thread-safe via threading.Lock.
#
# Dead-letter files: append-mode JSONL for post-mortem analysis.
#
# [Source: docs/stories/36.12.story.md#AC-36.12.4, AC-36.12.5]
#
# CARD-NEO4J-REPLAY-BOUND (T6-C, BATCH-2026-09-11-第十四批): 写侧有界。
# 死信文件原先是裸追加（无上限、无轮转）——Neo4j 永久离线时单调增长直到占满
# 磁盘。本模块现在额外提供通用的「核行数 → 轮转 → 按保留上限删最老」原语
# (``rotate_if_over_limit``)，``failed_writes_constants`` 也复用它，避免同一段
# 轮转逻辑在两个模块里各抄一份后各自漂移。
import json
import logging
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, List, Optional
from uuid import uuid4

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


def bound_from_env(name: str, default: int, *, minimum: int) -> int:
    """读一个整数上限环境变量，坏值退回 default 而不是让进程导入期崩。

    ``int(os.environ[...])`` 直接用会在 ``CLS_DEAD_LETTER_MAX_LINES=abc``
    这种情况下抛 ``ValueError``——而这是**模块导入期**求值的，等于整个后端
    起不来。上限值坏掉的正确反应是退回默认值并告警，不是让服务死掉。
    """
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        value = int(raw.strip())
    except ValueError:
        logger.warning("%s=%r 不是整数, 退回默认值 %d", name, raw, default)
        return default
    if value < minimum:
        logger.warning("%s=%d 小于下限 %d, 退回默认值 %d", name, value, minimum, default)
        return default
    return value


# --- 写侧有界（CARD-NEO4J-REPLAY-BOUND / T6-C）---
#
# 单条死信记录实测 ~200-400 B（timestamp + type + error + 若干可选 id）。
# 10000 行 ≈ 2-4 MB/文件；(1 活动 + 5 overflow) × 3 个 JSONL ≈ 36-72 MB 上限，
# 对桌面端是可接受的天花板，同时留足够多的历史供事后分析。
DEAD_LETTER_MAX_LINES: int = bound_from_env("CLS_DEAD_LETTER_MAX_LINES", 10000, minimum=1)
DEAD_LETTER_MAX_ROTATIONS: int = bound_from_env("CLS_DEAD_LETTER_MAX_ROTATIONS", 5, minimum=0)

# ⛔ 写侧轮转后缀必须与回灌侧的 ``.synced.``（fallback_sync_service._rotate_file）
# **相异**。``.synced.`` 的语义是「已回灌进 Neo4j，可按 30 天 retention 清理」；
# 写侧溢出的数据**没有**被回灌过，套同一个后缀会让它被误当已回灌处理。
# 改这个常量前先读 test_dead_letter_bounded_t6c.py::
# test_retention_does_not_touch_synced_siblings。
OVERFLOW_SUFFIX = ".overflow."

# 护「核行数 → 轮转 → 追加」这一段的原子性。与 ``_counter_lock`` 是两把独立的
# 锁且不嵌套（write_dead_letter 不调 increment_*），无死锁面。
_dead_letter_io_lock = threading.Lock()


def count_lines(path: Path) -> int:
    """按 b"\\n" 数行。

    口径必须与判据侧一致——用 ``str.splitlines()`` 会在 U+2028 / U+2029 处
    额外切行，于是「多少行」会随条目内容漂移，上限判定跟着漂。
    末行没有换行符时也算一行。
    """
    # ⚠️ 不用 ``path.exists()``（Codex round-2 M1）：Python 3.14 的 ``Path.exists()``
    # 会把 ``PermissionError`` **吞成 False**，于是「读不到」和「文件是空的」在这里
    # 不可区分 —— 对上限判定而言那等于「永远不到阈值、永远不轮转」，有界静默失效。
    # 用 stat 显式分流：真的不在 ⇒ 0；其他 OSError ⇒ 上抛，由调用方（已接住）降级。
    try:
        path.stat()
    except FileNotFoundError:
        return 0
    total = 0
    tail = b""
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            total += chunk.count(b"\n")
            tail = chunk[-1:]
    if tail and tail != b"\n":
        total += 1
    return total


def overflow_siblings(path: Path) -> List[Path]:
    """活动文件轮转出去的 ``<stem>.overflow.<ts>`` 兄弟，按名字（== 按时间）升序。"""
    parent = path.parent
    if not parent.exists():
        return []
    prefix = path.stem + OVERFLOW_SUFFIX
    return sorted((p for p in parent.iterdir() if p.name.startswith(prefix)), key=lambda p: p.name)


def _unique_overflow_target(path: Path) -> Path:
    """生成一个**尚不存在**的轮转目标名。

    ``Path.rename`` 在 POSIX 下静默覆盖已存在的目标。既有回灌侧
    ``_rotate_file:918`` 的时间戳只精确到秒，高频轮转时会无声吃掉整份
    overflow；写侧上限在小 MAX_LINES 下正是高频轮转，所以这里：
    微秒级定宽时间戳（定宽 ⇒ 字典序 == 时序，retention「删最老」才成立）
    + 存在性防撞（跨进程微秒仍可能撞）。
    """
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M%S%f")
    # ⚠️ 结尾保留原扩展名（独立复核 2026-09-15 MEDIUM）。``with_suffix`` 会把
    # ``.jsonl`` 吃掉，而 ``backend/data/.gitignore`` 忽略的是 ``*.jsonl`` 与
    # ``*.synced.*`` —— 都盖不住 ``failed_writes.overflow.<ts>``（实测
    # ``git check-ignore`` 无命中）。那样每轮转一次就往 ``git status`` 里多一个
    # 未跟踪文件，迟早被顺手 commit 进仓库（死信内容含错误消息与 id）。
    # 带上 ``.jsonl`` 后实测被 ``.gitignore:5`` 的 ``*.jsonl`` 命中。
    # 时间戳定宽 + 扩展名是常量后缀 ⇒ 字典序仍 == 时序，retention「删最老」不受影响。
    tail = path.suffix
    # ⚠️ 序号**恒存在**（`-00` 起），不是「撞了才加」。初版是撞了才追加 `-01`，
    # 于是 `<ts>.jsonl` 与 `<ts>-01.jsonl` 之间按 ASCII 比较 `.`(0x2E) > `-`(0x2D)
    # ⇒ **后产生的 `-01` 排在先产生的前面**，直接打破 `_prune_overflow`
    # 赖以「删最老」的「定宽 ⇒ 字典序 == 时序」不变量（本文件自己的测试
    # test_unique_overflow_target_does_not_overwrite_existing 抓到的）。
    # 所有名字同形之后，同微秒内按 `-NN` 递增、跨微秒由时间戳主导，两级都对。
    for n in range(100):
        candidate = path.with_suffix(f"{OVERFLOW_SUFFIX}{stamp}-{n:02d}{tail}")
        if not candidate.exists():
            return candidate
    # 同一微秒连撞 100 次基本不可能；真发生了宁可牺牲族内有序也不覆盖数据。
    # ⚠️ 分隔符用 `~`(0x7E) 不用 `-`(0x2D)：`-` < `.`(0x2E) 会让 `-99-<uuid>.jsonl`
    # 排在 `-99.jsonl` **之前**，于是「删最老」会去删这个最新的兜底档
    # （Codex round-2 L1；与 `-NN` 恒存在那条是同一个 ASCII 陷阱的第二处）。
    # `~` > `.` ⇒ 兜底档在同微秒族内仍排最后。
    logger.warning("轮转目标名连撞 100 次, 退化到随机后缀: %s", path)
    return path.with_suffix(f"{OVERFLOW_SUFFIX}{stamp}-99~{uuid4().hex[:8]}{tail}")


def _prune_overflow(path: Path, max_rotations: int) -> None:
    """只保留最新的 ``max_rotations`` 个 ``.overflow.*``，多余的从最老删起。

    删除失败只记日志不抛——删不掉旧档案不该阻断新死信落盘。
    """
    if max_rotations < 0:
        return
    try:
        siblings = overflow_siblings(path)
    except OSError as e:
        # Codex round-1 M1: 父目录可写可遍历但**不可列**时，数行与 rename 都能
        # 成功，随后 iterdir() 抛错 —— 若不接住，清理失败就会阻断本次追加，
        # 与本函数「删不掉旧档案不该阻断新死信落盘」的声明自相矛盾。
        logger.warning("[T6-C] 枚举溢出文件失败, 跳过清理 %s: %s", path, e)
        return
    victims = siblings if max_rotations == 0 else siblings[:-max_rotations]
    for victim in victims:
        try:
            victim.unlink(missing_ok=True)
            logger.info("[T6-C] 清理超出保留上限的溢出文件: %s", victim.name)
        except OSError as e:
            logger.warning("[T6-C] 清理溢出文件失败 %s: %s", victim, e)


def rotate_if_over_limit(
    path: Path,
    max_lines: int,
    max_rotations: int,
    *,
    before_rotate: Optional[Callable[[], bool]] = None,
) -> bool:
    """活动文件到达 ``max_lines`` 时轮转成 ``<stem>.overflow.<ts>``，并按保留上限删最老。

    ⛔ **调用方必须已持有**保护该文件的锁（本模块的 ``_dead_letter_io_lock``，
    或 failed_writes 侧的 ``failed_writes_lock``）。本函数**不取任何锁**——
    ``threading.Lock`` 非重入，在已持锁的调用方里再取同一把会死锁。

    Args:
        path: 活动文件
        max_lines: 行数上限；``<= 0`` 表示关闭上限（不轮转）
        max_rotations: 保留的 ``.overflow.*`` 个数；``0`` = 轮转后立即全删
        before_rotate: 决定轮转前必须完成的前置动作；返回 False ⇒ **放弃本次轮转**。
            failed_writes 用它作废回灌游标（换代与游标失效必须同生共死，见
            ``failed_writes_constants._invalidate_replay_checkpoint``）。
            两条 dead-letter 链没有游标，不传。

    Returns:
        True 表示本次确实轮转了。

    轮转失败（权限等）只记 error 并返回 False，**调用方仍会继续追加**：
    暂时超过上限比丢掉一条死信记录轻。所以「活动文件 ≤ max_lines」是
    best-effort 不变量，不是绝对保证。

    ⚠️ 被轮转走的条目**没有任何回灌方**：``fallback_sync_service`` 全文无
    glob，只回灌活动文件。溢出条目会在超过保留上限后被删除。这是「有界」
    换来的代价，不是缺陷——但改回灌逻辑前必须知道这件事。
    """
    if max_lines <= 0:
        return False
    try:
        if count_lines(path) < max_lines:
            return False
    except OSError as e:
        logger.warning("[T6-C] 数行失败, 跳过轮转 %s: %s", path, e)
        return False

    if before_rotate is not None and not before_rotate():
        logger.error("[T6-C] 轮转前置动作失败, 本次不轮转（宁可越限）: %s", path)
        return False

    target = _unique_overflow_target(path)
    try:
        path.rename(target)
    except OSError as e:
        logger.error("[T6-C] 轮转失败, 继续追加到活动文件 %s: %s", path, e)
        return False
    logger.info("[T6-C] 写侧上限触发, 轮转 %s → %s", path.name, target.name)
    _prune_overflow(path, max_rotations)
    return True


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
    request_id: Optional[str] = None,
) -> None:
    """
    Append a failure record to a dead-letter JSONL file.

    AC-36.12.8: Append mode + utf-8 encoding, survives service restarts.

    T6-C: 追加**前**先核行数，到达 ``DEAD_LETTER_MAX_LINES`` 就把活动文件轮转成
    ``<stem>.overflow.<ts>``，并只保留最新的 ``DEAD_LETTER_MAX_ROTATIONS`` 份。
    「核行数 → 轮转 → 追加」整段持 ``_dead_letter_io_lock``，对进程内并发写者
    原子；**跨进程仍非原子**（rename 与 append 是两个 syscall）。
    两个上限都可用 ``CLS_DEAD_LETTER_MAX_LINES`` / ``CLS_DEAD_LETTER_MAX_ROTATIONS``
    覆盖（坏值退回默认并告警，见 ``bound_from_env``）。

    Args:
        file_path: Path to the dead-letter JSONL file
        entry_type: "edge_sync" or "dual_write"
        error: Error message
        edge_id: Edge ID (for edge_sync failures)
        canvas_name: Canvas name (for edge_sync failures)
        episode_id: Episode ID (for dual_write failures)
        retry_count: Number of retries attempted
        timeout_ms: Timeout in milliseconds (for dual_write timeouts)
        request_id: Optional correlation request ID from middleware
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
    if request_id is not None:
        entry["request_id"] = request_id

    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        # NOTE: Synchronous file I/O by design — single-line JSONL append is
        # fast enough (~μs) to be acceptable in an async context.  If dead-letter
        # volume grows, consider asyncio.to_thread() or aiofiles.
        with _dead_letter_io_lock:
            rotate_if_over_limit(file_path, DEAD_LETTER_MAX_LINES, DEAD_LETTER_MAX_ROTATIONS)
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError as e:
        logger.error(f"Failed to write dead-letter entry to {file_path}: {e}")
