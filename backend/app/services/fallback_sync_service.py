# Story 38.8: JSON Fallback → Neo4j Complete Sync Mechanism
#
# When Neo4j is unavailable, three JSON fallback files accumulate data.
# This service syncs them back to Neo4j on startup when it recovers.
#
# Fallback files:
#   1. data/failed_writes.jsonl     (Story 38.6 - scoring failures)
#   2. app/data/canvas_events_fallback.json  (Story 38.5 - Canvas CRUD)
#   3. data/learning_memories.json  (Story 38.4 - dual-write)

import asyncio
import json
import threading

import structlog
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.clients.neo4j_client import Neo4jClient, get_neo4j_client
from app.core.failed_writes_constants import FAILED_WRITES_FILE, failed_writes_lock

# T1 统一 (2026-07-10): 物理层 group_id 单一 __ 格式 (graphiti_core validator 拒冒号)
from app.graphiti.group_id_compat import to_physical_group_id

logger = structlog.get_logger(__name__)

# Directory paths
_BACKEND_DIR = Path(__file__).parent.parent.parent  # backend/
_APP_DATA_DIR = Path(__file__).parent.parent / "data"  # backend/app/data/

CANVAS_EVENTS_FALLBACK_FILE = _APP_DATA_DIR / "canvas_events_fallback.json"
LEARNING_MEMORIES_FILE = _BACKEND_DIR / "data" / "learning_memories.json"
SYNC_CHECKPOINT_FILE = _BACKEND_DIR / "data" / "sync_checkpoint.json"

# Lock for checkpoint file access
_checkpoint_lock = threading.Lock()

# Days before .synced files are cleaned up
_SYNCED_FILE_RETENTION_DAYS = 30

# Checkpoint save interval (entries)
_CHECKPOINT_INTERVAL = 50

#: **进度语义版本** —— checkpoint 存的下标只在同一「切行口径 + 游标语义」下有意义。
#: 变更这个值的条件: 改动 :meth:`_sync_failed_writes` 的切行方式**或**游标推进规则。
#:
#: 变更条件有三类, 缺一不可: 改**切行方式**、改**游标推进规则**、
#: 或改**「什么算一条成功」的判定**。第三类最容易被漏掉 —— 见下面 r8 那一行。
#:
#: 历史:
#:   (无标记)                      本卡之前: splitlines() 切行 + 游标按「已**尝试**」推进
#:   "split-lf"                    CARD-NEO4J-REPLAY-WIRE r3: 改 split("\n") (U+2028 修复)
#:   "split-lf+contiguous"         同卡 r5: 游标只推进到**连续成功前缀**
#:   "split-lf+contiguous+history" 同卡 r8: **成功条件收紧** —— r7 之前
#:                                 `record_score_history` 失败仍算整条成功;
#:                                 现在它失败/拒写则整条判失败 (r7 HIGH-4)。
#:
#: ⛔ 读到任何不等于当前值的标记一律**回退到 0**。
#: r8 这一版尤其要紧 (Codex round-8 HIGH-1, 本卡修复遗漏):
#:   负控 —— r7 之前前 50 条 LEARNED 成功、其中一条评分历史失败但**仍被记成成功**,
#:   于是存下 `index=50, progress_version="split-lf+contiguous"`; 升级后该标记
#:   在旧口径下仍"有效", 那条缺历史的条目被跳过并随文件轮转出队。
#:   r7 的 `return False` 只修好**重新执行**的记录, 覆盖不到**已被旧游标跳过**的。
#:   ⇒ 成功条件一变, 按旧条件写下的游标就必须作废。
_PROGRESS_VERSION = "split-lf+contiguous+history"

#: 整次回灌的互斥锁（Codex round-6 HIGH-2）。
#:
#: 本卡之前 ``sync_all_fallbacks`` **零调用方**，不存在并发；本卡把它接进两处真实
#: 路径（启动钩子 + 可被反复调用的鉴权管理端点）后，**并发成为现实**。
#:
#: 两个既有文件锁（``failed_writes_lock`` / ``_checkpoint_lock``）都是
#: ``threading.Lock``，只护住各自那几行同步 IO，**盖不住重放中间的 await 窗口**。
#: 负控：A、B 都初读 ``[x, y]``；A 成功 x、失败 y，写回 ``[y]``；随后追加 z，文件成为
#: ``[y, z]``；B 仍拿旧快照 ``[x, y]``，两边长度同为 2 ⇒ 判定「没有新追加」，写回
#: ``[y]`` —— **z 从未重放却被删掉**。
#:
#: ⚠️ 必须是 ``asyncio.Lock`` 而非 ``threading.Lock``：整次回灌是协程、中间大量
#: ``await``，线程锁会阻塞整个事件循环。
#: ⚠️ 本锁是**进程内**的；多 worker / 多进程部署下的并发**未覆盖**（需文件级锁或
#: 单飞标志），已如实登记，不在本卡范围。
_sync_all_lock = asyncio.Lock()

#: CARD-STAGING-WRITERS-BOUNDED: 本轮回灌的开始时刻（``time.monotonic()``）。
#:
#: 写侧守卫 ``failed_writes_constants._replay_in_flight`` 原先只读
#: ``_sync_all_lock.locked()`` —— **没有时间维度**。回灌协程被 cancel 不干净、
#: 事件循环挂起、或某条 ``await`` 永不返回时，这把锁会**永远** locked，于是写侧
#: 上限被**无限期**关闭（每次追加都走裸追加分支）。有了开始时刻，守卫至少能问出
#: 「这把锁被占了多久」。
#:
#: ⚠️ 时间戳量的是**耗时**，不是存活性（Codex r1 MEDIUM）：一次又慢又健康的回灌
#: 和一次挂死的回灌在这里长得一模一样。超时只是「久到该按挂住处理」的工程取舍，
#: 不是「区分正在回灌与挂住」的判据 —— 它误判健康长回灌的后果见
#: ``failed_writes_constants._replay_in_flight`` 的 docstring（已移交 P2-C）。
#:
#: ⚠️ ``None`` 本身**不**决定守卫的答案（车道自审 2026-09-19 更正初版这句失实）：
#: 守卫先读 ``_sync_all_lock.locked()``，**没人持锁时直接返回 False（窗口关着）**，
#: 根本读不到这个变量。只有在**已经确认锁被占着**之后，``None`` 才有含义 ——
#: 它表示持锁者是**直接** ``async with _sync_all_lock:`` 的那种（测试替身、
#: 或未经 :meth:`sync_all_fallbacks` 的新持锁点），没有时间戳可比，
#: 于是保守地判「窗口开着」—— 宁可越限也不丢数据。
_sync_all_started_at: Optional[float] = None


class FallbackSyncService:
    """Syncs JSON fallback files back to Neo4j when it recovers."""

    def __init__(self, neo4j_client: Neo4jClient):
        self._neo4j = neo4j_client

    async def sync_all_fallbacks(self) -> Dict[str, Any]:
        """
        Sync all three fallback files to Neo4j.

        Checks Neo4j availability first. If unavailable, skips.
        Syncs in priority order: failed_writes → canvas_events → learning_memories.

        ⚠️ **整次回灌互斥**（Codex round-6 HIGH-2）：全程持有
        :data:`_sync_all_lock`。本卡把这个方法接进两处真实路径后并发成为现实，
        而「初读快照 → 逐条 await 重放 → finalize 写回」这条链在并发下会让
        后完成的那一方用**旧快照**覆盖掉期间新追加的条目。既有的两个
        ``threading.Lock`` 只护住各自那几行同步 IO，盖不住 await 窗口。
        进程内互斥；跨进程并发未覆盖（见该锁的注释）。

        Returns:
            Dict with per-file stats or {"skipped": True, "reason": "..."}
        """
        # CARD-STAGING-WRITERS-BOUNDED: 打上开始时刻，写侧守卫据此判「挂住了没」。
        # 必须在**取到锁之后**打、在 finally 里清 —— 排队等锁的那段不算窗口时长，
        # 否则高并发下第二个等待者会把第一个的时间戳冲掉。
        global _sync_all_started_at
        async with _sync_all_lock:
            _sync_all_started_at = time.monotonic()
            try:
                return await self._sync_all_fallbacks_locked()
            finally:
                _sync_all_started_at = None

    async def _sync_all_fallbacks_locked(self) -> Dict[str, Any]:
        """:meth:`sync_all_fallbacks` 的实际实现（调用方须已持有 :data:`_sync_all_lock`）."""
        # Check Neo4j availability
        if self._neo4j.is_fallback_mode:
            return {"skipped": True, "reason": "Neo4j in fallback mode"}

        try:
            healthy = await self._neo4j.health_check()
        except (RuntimeError, ConnectionError, asyncio.TimeoutError) as e:
            logger.warning(f"[Story 38.8] Neo4j health check failed: {e}")
            return {"skipped": True, "reason": f"health check failed: {e}"}

        if not healthy:
            return {"skipped": True, "reason": "Neo4j unhealthy"}

        result: Dict[str, Any] = {}

        # Priority 1: failed_writes (scoring failures)
        try:
            result["failed_writes"] = await self._sync_failed_writes()
        except (OSError, RuntimeError, ConnectionError) as e:
            logger.warning(f"[Story 38.8] failed_writes sync error: {e}")
            result["failed_writes"] = {"recovered": 0, "pending": -1, "error": str(e)}

        # Priority 2: canvas_events
        try:
            result["canvas_events"] = await self._sync_canvas_events()
        except (OSError, RuntimeError, ConnectionError) as e:
            logger.warning(f"[Story 38.8] canvas_events sync error: {e}")
            result["canvas_events"] = {"recovered": 0, "pending": -1, "error": str(e)}

        # Priority 3: learning_memories
        try:
            result["learning_memories"] = await self._sync_learning_memories()
        except (OSError, RuntimeError, ConnectionError) as e:
            logger.warning(f"[Story 38.8] learning_memories sync error: {e}")
            result["learning_memories"] = {
                "recovered": 0,
                "pending": -1,
                "error": str(e),
            }

        chains = [v for v in result.values() if isinstance(v, dict)]
        total_recovered = sum(v.get("recovered", 0) for v in chains)
        # ⚠️ pending == -1 是「数不出来」的哨兵 (finalize 读不到文件时), **不能直接
        # 累加** —— 那会让它把别的链的真实待回灌数抵消掉, 甚至算出负数。
        # 有任何一条链未知 ⇒ 总数就是未知, 如实打 "unknown" 而不是编一个数字。
        known = [v.get("pending", 0) for v in chains if v.get("pending", 0) >= 0]
        unknown = [k for k, v in result.items() if isinstance(v, dict) and v.get("pending", 0) < 0]
        total_pending: Any = sum(known) if not unknown else f"≥{sum(known)} (+{','.join(unknown)} unknown)"
        logger.info(f"[Story 38.8] Fallback sync complete: {total_recovered} replayed, {total_pending} still pending")

        return result

    def count_fallback_backlog(self) -> Dict[str, int]:
        """只读统计三条暂存链的积压条目数 — 不连 Neo4j, 不改任何文件.

        CARD-NEO4J-REPLAY-WIRE (BATCH-2026-09-11-第十四批): 供 ``app/main.py``
        的启动回填门在 **Neo4j 离线分支**登记「有多少条攒着等回灌」。离线时
        原先整段只打一句「启动回填跳过」, 攒下的条目既不回灌也不出现在任何
        日志里 —— 数据事实上悄悄丢失。

        ⚠️ ``pending_total`` **只累加 failed_writes 与 canvas_events**:
        这两个文件在 :meth:`_sync_failed_writes` / :meth:`_sync_canvas_events`
        回灌成功后会被 ``_rotate_file`` 搬走, 所以「文件里还有几条」= 「还有
        几条没回灌」。``learning_memories.json`` **刻意不轮转**
        (见 :meth:`_sync_learning_memories` 结尾的 NOTE —— 运行时
        ``LearningMemoryClient`` 还要查它), 它的条目数是「本地记录总数」而不是
        「待回灌数」, 计进 total 会虚报。故单列返回、由调用方分开陈述。

        读文件失败 (不存在 / 权限 / 非 UTF-8 字节 / JSON 格式坏) 按该条链 0 条
        计并记一条 warning: 本方法服务于「离线时不静默丢弃」这个目的, 若统计
        本身抛异常, 会被外层回填 ``except`` 吞成一句 "启动回填 failed", 把
        「没统计成」伪装成「回填出问题」—— 比不统计更坏。

        ⚠️ ``UnicodeDecodeError`` 必须显式列进捕获集 (Codex round-1 LOW-④):
        它是 ``ValueError`` 的子类、**不是** ``OSError``, 只捕 OSError 会让
        一个非法字节直接逃到外层, 上面那句承诺当场落空。

        Returns:
            ``{"failed_writes": int, "canvas_events": int,
               "learning_memories": int, "pending_total": int}``
        """
        failed_writes = self._count_jsonl_lines(FAILED_WRITES_FILE)
        canvas_events = self._count_json_list(CANVAS_EVENTS_FALLBACK_FILE)
        learning_memories = self._count_json_list(LEARNING_MEMORIES_FILE, key="memories")

        return {
            "failed_writes": failed_writes,
            "canvas_events": canvas_events,
            "learning_memories": learning_memories,
            "pending_total": failed_writes + canvas_events,
        }

    @staticmethod
    def _count_jsonl_lines(path: Path) -> int:
        """JSONL 文件的非空行数; 读不到记 warning 后按 0 计.

        ⚠️ **直接读, 不先 exists()** (Codex round-3 LOW-3 / round-4 LOW-5):
        `Path.exists()` 对权限类 OSError 是**返回 False 而不是抛出** ——
        「问不出来」被压成「不存在」, 函数直接 return 0 且**不留 warning**,
        于是「目录不可读」与「真的没有积压」在日志里也不可分。
        改为直接 read_text: FileNotFoundError 是「真的没有」(静默 0, 正常情形),
        其余读取异常才是「读不到」(记 warning)。
        """
        try:
            raw = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return 0  # 文件不存在 = 没有积压, 这是正常情形, 不必 warning
        except (OSError, ValueError) as e:
            # ValueError 覆盖 UnicodeDecodeError (其子类) —— 后者不是 OSError,
            # 只捕 OSError 会让一个非法字节逃到外层 (Codex round-1 LOW-④)。
            # OSError 这一支现在真能接到权限错误了 (不再被 exists() 吞掉)。
            logger.warning(f"[T6-B backlog] Cannot read {path.name}: {e}")
            return 0
        # ⚠️ split("\n") 而非 splitlines() (Codex round-3 LOW-4): JSONL 的行
        # 分隔符只有 \n, 而 str.splitlines() 还在 U+2028/U+2029/\x0b/\x0c/
        # \x1c-\x1e/U+0085 处断行 —— 这些字符在 JSON 字符串里是**合法原始字符**
        # (从 PDF / 网页粘来的文本里并不罕见)。负控输入
        # `json.dumps({"concept":"a b"}, ensure_ascii=False)` 是**一条**
        # 合法记录, splitlines() 会把它数成两条。
        return sum(1 for line in raw.split("\n") if line.strip())

    @staticmethod
    def _count_json_list(path: Path, key: Optional[str] = None) -> int:
        """JSON 文件里列表的长度 (``key`` 非空时取该键下的列表); 坏文件按 0 计.

        ⚠️ 坏文件计 0 与「真的空」在返回值上不可区分 —— 这是刻意的取舍
        (见 :meth:`count_fallback_backlog` 的 docstring), 但两者在日志里可分:
        坏文件会留下本方法的 warning, 真空不会。
        **直接读不先 exists()** 的理由同 :meth:`_count_jsonl_lines`。
        """
        try:
            raw = path.read_text(encoding="utf-8").strip()
            if not raw:
                return 0
            data = json.loads(raw)
        except FileNotFoundError:
            return 0  # 文件不存在 = 没有积压, 正常情形
        except (OSError, ValueError) as e:
            # ValueError 一次覆盖三类 (Codex round-2 LOW-5):
            #   json.JSONDecodeError 与 UnicodeDecodeError 都是它的子类;
            #   Python 3.11+ 的**整数字符串转换位数上限**对超长数字字面量
            #   (负控输入 '[' + '1'*5000 + ']') 抛的是**普通** ValueError,
            #   逐个列子类会漏掉它, 让一个坏文件逃到外层被记成「回填失败」。
            logger.warning(f"[T6-B backlog] Cannot parse {path.name}: {e}")
            return 0

        if key:
            # 坏文件可能是任意 JSON (顶层 list / str / null) —— 对非 dict 调
            # .get 会抛 AttributeError, 那是本方法承诺不抛的那类异常。
            items = data.get(key, []) if isinstance(data, dict) else []
        else:
            items = data
        return len(items) if isinstance(items, list) else 0

    # ─────────────────────────────────────────────────────────────────────
    # 1. failed_writes.jsonl sync
    # ─────────────────────────────────────────────────────────────────────

    async def _sync_failed_writes(self) -> Dict[str, Any]:
        """Replay scoring failures from failed_writes.jsonl to Neo4j.

        返回 ``{"recovered": int, "pending": int}``；finalize 无法完成时额外带
        ``"error": str``，且 ``pending`` 可能是 **-1**（= 数不出来，见
        Codex round-8 MEDIUM-4）。故标注是 ``Dict[str, Any]`` 而非 ``Dict[str, int]``。
        """
        if not FAILED_WRITES_FILE.exists():
            return {"recovered": 0, "pending": 0}

        with failed_writes_lock:
            try:
                raw = FAILED_WRITES_FILE.read_text(encoding="utf-8").strip()
            except OSError as e:
                # 带 error 键: 读不到文件不等于「没有待回灌」(Codex round-9 MEDIUM-3)
                logger.warning(f"[Story 38.8] Cannot read failed_writes: {e}")
                return {"recovered": 0, "pending": -1, "error": f"cannot read: {e}"}

        if not raw:
            return {"recovered": 0, "pending": 0}

        # ⚠️ split("\n") 而非 splitlines() (Codex round-3 LOW-4 的连带面):
        # 含 U+2028 等字符的**一条**合法 JSONL 记录会被 splitlines() 切成两半,
        # 两半都不是合法 JSON ⇒ 双双走 still_pending, 写回文件, 下一轮再切再失败
        # —— 该条目**永远回灌不掉**。本卡接的就是这条回灌链, 这是链上的洞。
        #
        # CRLF 不是障碍, 但理由要写对: 保证在**读侧** —— 上面 read_text() 默认
        # newline=None = universal newlines, 实测 b'{"a":1}\r\n' → '{"a":1}\n',
        # 裸 CR 同样被规范化。写成「写侧都用 \n 拼接所以安全」是个**更弱**的前提
        # (存在 Windows 写侧或历史文件就破)。即便尾部真残留 \r, json.loads 也把它
        # 当 JSON 空白接受。
        #
        # ⛔ 下面 finalize 段重读文件时用的是**同一个**切法, 两处口径必须一致:
        # 它们靠 len(current_lines) > len(lines) 判断「重放期间有没有新追加」,
        # 一边 splitlines 一边 split 会让这个比较在含 U+2028 的文件上永远为真。
        lines = raw.split("\n")
        checkpoint_idx = self._load_checkpoint("failed_writes")
        recovered = 0
        still_pending: List[str] = []

        # ⚠️ 游标只推进到**连续成功前缀**（Codex round-5 HIGH）。
        # 原先是 `_save_checkpoint(i + 1)` —— 不管这一条成没成功都推进。失败的
        # 条目只进内存 `still_pending`（此时**尚未**写回文件），若进程在写回前
        # 中断，重启后游标已越过它 ⇒ **该条目被永久跳过**。
        # 负控（Codex 纯内存实测）：51 条，第 1 条失败、2–50 成功，存下 index=50
        # 后在第 51 条的 await 期间中断 ⇒ 重启只试第 51 条，第 1 条从未成功却被跳过。
        # `contiguous_end` 的不变式：lines[checkpoint_idx : contiguous_end] 全部
        # 重放成功。只有当前这条成功**且**它紧接在已证明的前缀之后，前缀才延长一位。
        contiguous_end = checkpoint_idx

        for i, line in enumerate(lines):
            if i < checkpoint_idx:
                # Already synced in a previous partial run
                continue

            entry_ok = False
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                logger.warning("[Story 38.8] Skipping malformed failed_writes entry")
                still_pending.append(line)
            else:
                try:
                    success = await self._replay_scoring_entry_to_neo4j(entry)
                    if success:
                        recovered += 1
                        entry_ok = True
                    else:
                        still_pending.append(line)
                except (RuntimeError, ConnectionError, asyncio.TimeoutError) as e:
                    logger.warning(f"[Story 38.8] failed_writes replay error: {e}")
                    still_pending.append(line)

            if entry_ok and contiguous_end == i:
                contiguous_end = i + 1

            # Checkpoint every N entries —— 存的是**已证明全部成功**的前缀端点,
            # 不是「扫到第几条」。前缀一旦被某条失败卡住, 后续再多成功也不推进,
            # 于是崩溃重启时那条失败记录一定会被重新尝试。
            if (i + 1) % _CHECKPOINT_INTERVAL == 0 and contiguous_end > checkpoint_idx:
                self._save_checkpoint("failed_writes", contiguous_end)

        # Finalize — re-read under lock to preserve entries appended
        # during the async replay window (race condition fix).
        with failed_writes_lock:
            new_lines: List[str] = []
            try:
                if FAILED_WRITES_FILE.exists():
                    current_raw = FAILED_WRITES_FILE.read_text(encoding="utf-8").strip()
                    # 与上面初读的切法逐字一致 (见那里的注释)
                    current_lines = current_raw.split("\n") if current_raw else []
                    # Lines appended after our initial read
                    if len(current_lines) > len(lines):
                        new_lines = current_lines[len(lines) :]
            except OSError as e:
                # ⛔ 重读失败必须**放弃改写** (Codex round-6 HIGH-3):
                # 原先是 `except OSError: current_lines = []` —— 吞掉异常继续往下
                # 写回 `still_pending`。负控: 初始 [x,y], x 成功 y 失败, 重放期间
                # 追加 z; 末尾重读抛 OSError 但随后的文件替换**成功** ⇒ 写回 [y],
                # **z 从未重放却被删掉**。既然读不到当前内容, 就无从判断有没有新
                # 追加, 任何写回都可能抹掉未知记录。
                # 保留原文件 + 保留 checkpoint, 下一轮重来 —— 宁可重复不可丢。
                logger.error(
                    "[Story 38.8] failed_writes finalize re-read failed (%s) — "
                    "leaving the file untouched to avoid clobbering concurrent appends; "
                    "remaining count unknown (file could not be read).",
                    e,
                )
                # ⚠️ 带 error 键 + pending=-1 表「未知」(Codex round-8 MEDIUM-4):
                # main.py 的启动汇总按「有没有 error 键」判这条链出没出问题;
                # 不带的话 finalize 失败会被打成「正常完成、零待回灌」—— 正是本卡
                # r1 整改②消灭的那类伪装在新路径上重现。读不到当前文件就数不出
                # 还剩多少, 报确切数字等于编造。
                return {"recovered": recovered, "pending": -1, "error": f"finalize re-read failed: {e}"}

            merged = still_pending + new_lines
            # ⛔ 先清游标再改写 (Codex round-6 HIGH-1: 文件代际错配):
            # 游标的含义绑在**当次快照的下标**上, 而 `_rotate_file` /
            # `_atomic_write_file` 会让文件换代。原先 `_clear_checkpoint` 在改写
            # **之后**, 中间崩一次就会留下「指向上一代文件的游标」——
            # 负控: 前 50 成功、第 51 失败, 存下 index=50 后文件被压缩成只剩第 51
            # 条, 清游标前中断 ⇒ 重启拿 index=50 跳过唯一记录并直接轮转。
            # 清不掉游标就**不动文件**: 换代与游标失效必须同生共死。
            try:
                self._clear_checkpoint("failed_writes")
            except OSError as e:
                logger.error(
                    "[Story 38.8] cannot clear failed_writes checkpoint (%s) — "
                    "refusing to rewrite/rotate the file (a stale cursor would point "
                    "into the previous file generation); the file still holds every "
                    "entry from this run, remaining count reported as unknown.",
                    e,
                )
                # ⚠️ 文件**没被动过** ⇒ 剩余是**原快照全部**, 不是 merged
                # (Codex round-9 MEDIUM-3): 全部成功时 merged=[] 而原文件仍在,
                # 报 pending=0 会让汇总说「零待回灌」而文件里躺着整份条目。
                return {
                    "recovered": recovered,
                    "pending": -1,
                    "error": f"cannot clear checkpoint, file left untouched: {e}",
                }

            if merged:
                self._atomic_write_file(
                    FAILED_WRITES_FILE,
                    "\n".join(merged) + "\n",
                )
            else:
                self._rotate_file(FAILED_WRITES_FILE)

        self._cleanup_old_synced_files(FAILED_WRITES_FILE.parent, FAILED_WRITES_FILE.stem)

        # pending = 文件里实际剩下几条(含重放期间新追加的), 不是「本轮试过几条失败」
        # —— 与 canvas 链同口径 (Codex round-8 MEDIUM-4)。
        return {"recovered": recovered, "pending": len(merged)}

    # ─────────────────────────────────────────────────────────────────────
    # 2. canvas_events_fallback.json sync
    # ─────────────────────────────────────────────────────────────────────

    async def _sync_canvas_events(self) -> Dict[str, Any]:
        """Replay Canvas CRUD events to Neo4j."""
        if not CANVAS_EVENTS_FALLBACK_FILE.exists():
            return {"recovered": 0, "pending": 0}

        try:
            raw = CANVAS_EVENTS_FALLBACK_FILE.read_text(encoding="utf-8").strip()
            if not raw:
                return {"recovered": 0, "pending": 0}
            events: List[Dict[str, Any]] = json.loads(raw)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"[Story 38.8] Cannot parse canvas_events_fallback: {e}")
            return {"recovered": 0, "pending": -1, "error": f"cannot parse: {e}"}

        if not events:
            return {"recovered": 0, "pending": 0}

        # Sort by timestamp for chronological replay
        events.sort(key=lambda e: e.get("timestamp", ""))

        # ⛔ 本链**不用位置 checkpoint**（Codex round-7 HIGH-1/HIGH-2）。
        # 上面那行 `events.sort(...)` 决定了「第 i 条」不是稳定身份:
        #   负控: 保存连续成功前缀 50 后中断, 随后追加一条**时间戳更早**的 z;
        #   重启先排序 ⇒ z 落到游标之前, 从未重放却随 finalize 出队。
        #   该路径不需要旧版本、也不需要发生压缩, 单靠排序即可触发。
        # 另: 旧版按 `i + 1` 保存的 canvas 游标也带着当前 _PROGRESS_VERSION 标记
        # (保存器是三链共用的), 升级后会被当成可信游标 —— 禁用位置游标一并止住。
        # 代价: 崩溃后本链从头重放。重放走 MERGE 身份键, 图上幂等;
        # 写侧另有上限 (canvas_service.py `_max_fallback_events = 10000`), 不会无界。
        recovered = 0
        still_pending: List[Dict[str, Any]] = []

        for event in events:
            try:
                success = await self._replay_canvas_event_to_neo4j(event)
                if success:
                    recovered += 1
                else:
                    still_pending.append(event)
            except (RuntimeError, ConnectionError, asyncio.TimeoutError) as e:
                logger.warning(f"[Story 38.8] canvas_event replay error: {e}")
                still_pending.append(event)

        # Finalize —— 必须重读并按**内容**核对 (Codex round-7 HIGH-3)。
        # 原先完全不重读, 直接用初读快照算出的 still_pending 覆盖文件:
        #   负控: 初读 [x,y], 重放期间追加 z, x 成功 y 失败 ⇒ 写回 [y], **z 被删**;
        #   全部成功时连 z 一起轮转掉。无需注入任何异常即可复现。
        # ⛔ 不能照搬 failed_writes 的「按长度截取追加后缀」—— 本链会排序,
        # 位置对不上。改用**内容指纹差集**: 当前文件里凡不在初读快照中的, 一律保留。
        seen = {self._event_fingerprint(e) for e in events}
        try:
            current_raw = CANVAS_EVENTS_FALLBACK_FILE.read_text(encoding="utf-8").strip()
            current_events: List[Dict[str, Any]] = json.loads(current_raw) if current_raw else []
        except (OSError, ValueError) as e:
            # 读不到当前内容 ⇒ 无从判断有没有新追加 ⇒ 任何写回都可能抹掉未知记录。
            # 保留原文件, 本轮已重放的条目下轮会被幂等地再放一次。
            logger.error(
                "[Story 38.8] canvas_events finalize re-read failed (%s) — leaving the "
                "file untouched to avoid clobbering concurrent appends; "
                "remaining count unknown (file could not be read).",
                e,
            )
            # ⚠️ 带 error 键 (Codex round-8 MEDIUM-4): main.py 的启动汇总按
            # 「有没有 error 键」判这条链是否出过问题; 不带的话 finalize 失败会被
            # 打成「正常完成」—— 正是本卡 r1 整改②消灭的那类伪装在新路径上重现。
            # pending 用 -1 明确表达「未知」: 读不到当前文件就数不出还剩多少。
            return {"recovered": recovered, "pending": -1, "error": f"finalize re-read failed: {e}"}

        appended = [e for e in current_events if self._event_fingerprint(e) not in seen]
        merged = still_pending + appended
        if merged:
            self._atomic_write_file(
                CANVAS_EVENTS_FALLBACK_FILE,
                json.dumps(merged, ensure_ascii=False, indent=2),
            )
        else:
            self._rotate_file(CANVAS_EVENTS_FALLBACK_FILE)

        self._cleanup_old_synced_files(
            CANVAS_EVENTS_FALLBACK_FILE.parent,
            CANVAS_EVENTS_FALLBACK_FILE.stem,
        )

        # ⚠️ pending 必须含 appended (Codex round-8 MEDIUM-4): 负控 —— x 全部成功、
        # 重放期间追加 z, finalize 正确保留了 [z], 却报 pending=0 ⇒ 启动汇总打成
        # 「回灌 N 条, 0 条待回灌」, 而文件里明明还躺着一条没重放的。
        # 「文件里还剩几条」才是待回灌数, 不是「本轮试过几条失败」。
        return {"recovered": recovered, "pending": len(merged)}

    @staticmethod
    def _event_fingerprint(event: Dict[str, Any]) -> str:
        """canvas 事件的内容指纹 —— finalize 判「这条是不是重放期间新追加的」。

        用 ``sort_keys`` 的紧凑 JSON：同一条事件无论字典键序如何都得到同一指纹。
        ⚠️ 不能用「位置」或「长度」代替：本链在重放前 ``sort(key=timestamp)``，
        期间新追加的条目可能排到任何位置（Codex round-7 HIGH-3）。
        """
        return json.dumps(event, sort_keys=True, ensure_ascii=False, separators=(",", ":"))

    # ─────────────────────────────────────────────────────────────────────
    # 3. learning_memories.json sync
    # ─────────────────────────────────────────────────────────────────────

    async def _sync_learning_memories(self) -> Dict[str, Any]:
        """Replay learning memories to Neo4j using MERGE (idempotent)."""
        if not LEARNING_MEMORIES_FILE.exists():
            return {"recovered": 0, "pending": 0}

        try:
            raw = LEARNING_MEMORIES_FILE.read_text(encoding="utf-8").strip()
            if not raw:
                return {"recovered": 0, "pending": 0}
            data = json.loads(raw)
            memories: List[Dict[str, Any]] = data.get("memories", [])
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"[Story 38.8] Cannot parse learning_memories: {e}")
            return {"recovered": 0, "pending": -1, "error": f"cannot parse: {e}"}

        if not memories:
            return {"recovered": 0, "pending": 0}

        # Sort by timestamp for chronological replay
        memories.sort(key=lambda m: m.get("timestamp", ""))

        checkpoint_idx = self._load_checkpoint("learning_memories")
        recovered = 0
        failed = 0
        # 游标口径与另两条链统一为「连续成功前缀」。
        # ⚠️ 本链的**后果**与另两条不同, 如实写明: 它既不写回也不轮转
        # (见下方 NOTE —— 运行时 LearningMemoryClient 还要查这个文件),
        # 所以被跳过的条目下一轮仍在文件里、**不会丢**, 只是这一轮没重放。
        # 统一口径是为了「三条链的 checkpoint 语义一致」, 不是为了修数据丢失。
        contiguous_end = checkpoint_idx

        for i, mem in enumerate(memories):
            if i < checkpoint_idx:
                continue

            entry_ok = False
            try:
                success = await self._replay_learning_memory_to_neo4j(mem)
                if success:
                    recovered += 1
                    entry_ok = True
                else:
                    failed += 1
            except (RuntimeError, ConnectionError, asyncio.TimeoutError) as e:
                logger.warning(f"[Story 38.8] learning_memory replay error: {e}")
                failed += 1

            if entry_ok and contiguous_end == i:
                contiguous_end = i + 1

            if (i + 1) % _CHECKPOINT_INTERVAL == 0 and contiguous_end > checkpoint_idx:
                self._save_checkpoint("learning_memories", contiguous_end)

        # NOTE: learning_memories.json is NOT rotated - still needed by
        # LearningMemoryClient for runtime queries.
        self._clear_checkpoint("learning_memories")

        return {"recovered": recovered, "pending": failed}

    # ─────────────────────────────────────────────────────────────────────
    # Replay helpers
    # ─────────────────────────────────────────────────────────────────────

    async def _replay_scoring_entry_to_neo4j(self, entry: Dict[str, Any]) -> bool:
        """
        Replay a single failed scoring entry to Neo4j.

        Uses custom Cypher with last-write-wins conflict resolution:
        if Neo4j already has newer data for this relationship, preserve it.
        """
        concept = entry.get("concept") or entry.get("concept_id", "")
        canvas_name = entry.get("canvas_name", "")
        score = entry.get("score")
        ts = entry.get("timestamp", datetime.now().isoformat())

        if not concept:
            logger.warning("[Story 38.8] Skipping entry with no concept")
            return False

        # Build group_id from canvas_name
        group_id = self._build_group_id_from_canvas(canvas_name)
        if not group_id:
            # G2-3 fail-closed (首日观察): _build_group_id_from_canvas 返 None
            # 时拒绝重放 — null 不得进 MERGE 键, 也不静默降级 DEFAULT。
            # 条目计 failed 保持 pending, 下轮 sync 重试。
            logger.error(
                "[G2-3 W1 fail-closed] scoring replay refused: unresolved group_id (concept=%r, canvas_name=%r)",
                concept,
                canvas_name,
            )
            return False

        # G2-3 (W1): Concept/LEARNED 写身份 = {name/端点, group_id} 复合键,
        # 禁事后 SET 归属 — 跨 vault 同名概念在重放时不再合并。
        # Timestamp-preserving MERGE with last-write-wins (仅业务字段)
        query = """
        MERGE (u:User {id: $userId})
        MERGE (c:Concept {name: $concept, group_id: $groupId})
        MERGE (u)-[r:LEARNED {group_id: $groupId}]->(c)
        WITH r,
             CASE WHEN r.timestamp IS NULL OR r.timestamp <= datetime($ts)
                  THEN true ELSE false END AS should_update
        SET r.score = CASE WHEN should_update THEN $score ELSE r.score END,
            r.timestamp = CASE WHEN should_update THEN datetime($ts) ELSE r.timestamp END
        RETURN should_update
        """

        try:
            results = await self._neo4j.run_query(
                query,
                userId="default_user",
                concept=concept,
                score=score,
                ts=ts,
                # T1 统一 (2026-07-10): 物理层 group_id 单一 __ 格式
                groupId=to_physical_group_id(group_id),
            )
            if results and not results[0].get("should_update", True):
                logger.info(f"[Story 38.8] Conflict: Neo4j has newer data for '{concept}', fallback timestamp={ts}")
        except (RuntimeError, ConnectionError, asyncio.TimeoutError) as e:
            logger.warning(f"[Story 38.8] Neo4j scoring replay failed: {e}")
            return False

        # Also record score history if score present.
        # ⛔ 这一步失败必须让**整条**重放判失败 (Codex round-7 HIGH-4)。
        # 原先是 `except ...: logger.warning("(non-fatal)")` 然后照样 `return True`:
        #   负控: LEARNED 写入成功、record_score_history() 抛 ConnectionError ⇒
        #   返回值与「两次写入都成功」的对照输入**完全相同** ⇒ 调用方据此把条目
        #   移出队列并轮转, **缺失的评分历史再也不会自动重试**。
        # 返回 False 让条目留在 pending, 下轮整条重放。代价是 LEARNED 会被重放
        # 一次 —— 它是 MERGE + last-write-wins, 幂等; 而 record_score_history 的
        # Episode 是 CREATE(randomUUID()), 提交结果不确定时可能重复。
        # **重复且可见 远好于 静默缺失**; 可靠去重需要稳定记录身份, 属重写卡范围。
        if score is not None:
            try:
                concept_id = entry.get("concept_id", concept)
                ok = await self._neo4j.record_score_history(
                    concept_id=concept_id,
                    canvas_name=canvas_name,
                    score=int(score),
                    timestamp=ts,
                    group_id=group_id,
                )
            except (RuntimeError, ConnectionError, asyncio.TimeoutError) as e:
                logger.warning(f"[Story 38.8] Score history record failed: {e} — entry stays pending")
                return False
            if ok is False:
                # 客户端也用**返回值**表达失败 (group 解析失败时 fail-closed 返 False,
                # 见 neo4j_client.record_score_history) —— 同样不能算整条成功。
                logger.warning(
                    "[Story 38.8] Score history record refused (concept_id=%r) — entry stays pending",
                    entry.get("concept_id", concept),
                )
                return False

        return True

    async def _replay_canvas_event_to_neo4j(self, event: Dict[str, Any]) -> bool:
        """Replay a single canvas event (node or edge) to Neo4j."""
        event_type = event.get("event_type", "")
        canvas_name = event.get("canvas_name", "")
        node_id = event.get("node_id")
        edge_id = event.get("edge_id")

        # G2-3 (W1): 重放显式携带 group — None 时由 client 端解析链兜底,
        # 仍不可解析则 client fail-closed 拒写 (条目保持 pending)。
        group_id = self._build_group_id_from_canvas(canvas_name)

        try:
            if event_type in ("node_created", "node_updated"):
                if not node_id:
                    return False
                return await self._neo4j.create_canvas_node_relationship(
                    canvas_path=canvas_name,
                    node_id=node_id,
                    node_text=None,
                    group_id=group_id,
                )

            elif event_type == "edge_sync":
                if not edge_id:
                    return False
                from_node = event.get("from_node_id", "")
                to_node = event.get("to_node_id", "")
                if not from_node or not to_node:
                    return False
                return await self._neo4j.create_edge_relationship(
                    canvas_path=canvas_name,
                    edge_id=edge_id,
                    from_node_id=from_node,
                    to_node_id=to_node,
                    group_id=group_id,
                )

            else:
                logger.debug(f"[Story 38.8] Unknown canvas event type: {event_type}")
                return True  # Don't block on unknown types
        except (RuntimeError, ConnectionError, asyncio.TimeoutError) as e:
            logger.warning(f"[Story 38.8] Canvas event replay failed: {e}")
            return False

    async def _replay_learning_memory_to_neo4j(self, mem: Dict[str, Any]) -> bool:
        """Replay a single learning memory entry to Neo4j using MERGE (idempotent).

        Uses last-write-wins conflict resolution: if Neo4j already has newer
        data for this concept, the fallback entry does not overwrite it.
        """
        concept = mem.get("concept", "")
        canvas_name = mem.get("canvas_name", "")
        score = mem.get("score")
        ts = mem.get("timestamp", datetime.now().isoformat())

        if not concept:
            return False

        group_id = self._build_group_id_from_canvas(canvas_name)
        if not group_id:
            # G2-3 fail-closed (首日观察): 同 _replay_scoring_entry_to_neo4j —
            # null 不得进 MERGE 键, 不静默降级 DEFAULT, 条目保持 pending。
            logger.error(
                "[G2-3 W1 fail-closed] learning memory replay refused: "
                "unresolved group_id (concept=%r, canvas_name=%r)",
                concept,
                canvas_name,
            )
            return False

        # G2-3 (W1): 复合写身份, 禁事后 SET 归属 — replay 不跨 vault 合并。
        # Last-write-wins MERGE: only update if fallback timestamp is newer
        query = """
        MERGE (u:User {id: $userId})
        MERGE (c:Concept {name: $concept, group_id: $groupId})
        MERGE (u)-[r:LEARNED {group_id: $groupId}]->(c)
        WITH r,
             CASE WHEN r.timestamp IS NULL OR r.timestamp <= datetime($ts)
                  THEN true ELSE false END AS should_update
        SET r.score = CASE WHEN should_update THEN $score ELSE r.score END,
            r.timestamp = CASE WHEN should_update THEN datetime($ts) ELSE r.timestamp END,
            r.next_review = CASE WHEN should_update THEN datetime($ts) + duration('P1D') ELSE r.next_review END
        RETURN should_update
        """

        try:
            results = await self._neo4j.run_query(
                query,
                userId="default_user",
                concept=concept,
                score=int(score) if score is not None else None,
                ts=ts,
                # T1 统一 (2026-07-10): 物理层 group_id 单一 __ 格式
                groupId=to_physical_group_id(group_id),
            )
            if results and not results[0].get("should_update", True):
                logger.info(f"[Story 38.8] Conflict: Neo4j has newer data for '{concept}', fallback timestamp={ts}")
        except (RuntimeError, ConnectionError, asyncio.TimeoutError) as e:
            logger.warning(f"[Story 38.8] Learning memory replay failed: {e}")
            return False

        return True

    # ─────────────────────────────────────────────────────────────────────
    # Checkpoint management
    # ─────────────────────────────────────────────────────────────────────

    def _load_checkpoint(self, file_key: str) -> int:
        """Load sync progress checkpoint for a file key.

        ⚠️ **进度语义版本校验**（Codex round-4 HIGH + round-5 HIGH）：checkpoint
        存的下标同时依赖两件事 —— 当时那一版的**分行切法**，以及**游标推进规则**。
        本卡两处都改了：

        1. r3 把 :meth:`_sync_failed_writes` 的 ``splitlines()`` 换成 ``split("\\n")``
           （U+2028 修复）⇒ 同一文件在新旧两版下**行数可能不同**，沿用旧下标会让
           「已处理」的边界错位（r4 HIGH 的负控：首条含 U+2028 + 50 条普通记录 ⇒
           旧版 52 片、新版 51 行，``index=50`` 会让**记录 49 被跳过**）。
        2. r5 把游标从「已**尝试**」改为「连续**成功**前缀」⇒ 旧游标即便切法相同
           也**不可信**：它可能越过了一条从未成功的记录（r5 HIGH 的负控：第 1 条
           失败、2–50 成功，存下 ``index=50`` 后中断 ⇒ 重启跳过第 1 条，而它只存在
           于上一进程的内存 ``still_pending`` 里，随 ``_rotate_file`` 消失 = **真丢**）。

        处置：**任何**不等于 :data:`_PROGRESS_VERSION` 的标记（含 ``"split-lf"``
        与无标记的历史 checkpoint）一律**回退到 0 从头重放**并记 warning。

        ⛔ 这里**刻意不再做** r4 那版「实测两种切法行数是否相同就沿用」的宽松判断：
        那只覆盖问题 1。问题 2 是**语义**变更 —— 行数相同的文件，旧游标照样可能
        越过失败条目，没有任何可在本地验证的判据能把它救回来。

        为什么不「转换旧游标」：旧游标对应哪一条记录、其前缀是否全部成功，都**不可
        逆推**（失败条目只存在于上一进程的内存里，文件也已被改写）。
        回退的代价与取舍：重放走 MERGE + last-write-wins，重复处理**不**产生重复的
        Concept/LEARNED；唯一代价是 ``record_score_history`` 会多建几个 Episode
        （它是 ``CREATE randomUUID()``）。**重复且可观测** 远好于 **静默丢记录**。
        ⚠️ 该取舍已被 Codex round-5 标为「须由主 session 裁定迁移取舍」——
        若裁定改为保留旧游标，只需放宽本方法，不必动 :meth:`_sync_failed_writes`。
        """
        with _checkpoint_lock:
            if not SYNC_CHECKPOINT_FILE.exists():
                return 0
            try:
                data = json.loads(SYNC_CHECKPOINT_FILE.read_text(encoding="utf-8"))
                entry = data.get(file_key, {})
                if not isinstance(entry, dict):
                    return 0
                if entry.get("progress_version") == _PROGRESS_VERSION:
                    return entry.get("index", 0)
                logger.warning(
                    "[Story 38.8] checkpoint for %s was written under progress semantics %r "
                    "(current %r) — cannot prove its prefix fully succeeded, replaying from 0. "
                    "Already-synced entries may be replayed again (idempotent for "
                    "Concept/LEARNED; may add duplicate scoring Episodes).",
                    file_key,
                    entry.get("progress_version"),
                    _PROGRESS_VERSION,
                )
                return 0
            except (json.JSONDecodeError, OSError, KeyError):
                return 0

    def _save_checkpoint(self, file_key: str, index: int) -> None:
        """Save sync progress checkpoint (带进度语义标记, 见 :meth:`_load_checkpoint`)."""
        with _checkpoint_lock:
            data: Dict[str, Any] = {}
            if SYNC_CHECKPOINT_FILE.exists():
                try:
                    data = json.loads(SYNC_CHECKPOINT_FILE.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    data = {}

            data[file_key] = {
                "index": index,
                "progress_version": _PROGRESS_VERSION,
                "updated_at": datetime.now().isoformat(),
            }

            SYNC_CHECKPOINT_FILE.parent.mkdir(parents=True, exist_ok=True)
            self._atomic_write_file(
                SYNC_CHECKPOINT_FILE,
                json.dumps(data, ensure_ascii=False, indent=2),
            )

    def _clear_checkpoint(self, file_key: str) -> None:
        """Remove checkpoint entry after full sync.

        ⚠️ **清不掉必须抛出来**（Codex round-6 HIGH-1）：调用方
        :meth:`_sync_failed_writes` 在**改写/轮转文件之前**调本方法，靠它把
        「上一代文件的游标」作废。若这里静默吞掉 OSError（原实现是
        ``except (...): pass``），调用方会以为清干净了、照常换代文件，于是留下
        一个指向**上一代**快照的游标 —— 下次启动按它跳过尚未成功的记录。
        换代与游标失效必须同生共死，故 OSError 一律上抛由调用方决定不动文件。
        JSON 解析失败仍吞掉：那说明 checkpoint 文件本身已不可信，
        下面的 ``unlink`` 会把它整个删掉，目的同样达成。
        """
        with _checkpoint_lock:
            if not SYNC_CHECKPOINT_FILE.exists():
                return
            try:
                data = json.loads(SYNC_CHECKPOINT_FILE.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                # 文件读不出/坏了 —— 整个删掉即可, 目的(让旧游标失效)同样达成。
                # unlink 自己的 OSError 照样上抛。
                SYNC_CHECKPOINT_FILE.unlink(missing_ok=True)
                return

            data.pop(file_key, None)
            if data:
                self._atomic_write_file(
                    SYNC_CHECKPOINT_FILE,
                    json.dumps(data, ensure_ascii=False, indent=2),
                )
            else:
                SYNC_CHECKPOINT_FILE.unlink(missing_ok=True)

    # ─────────────────────────────────────────────────────────────────────
    # File rotation & cleanup
    # ─────────────────────────────────────────────────────────────────────

    @staticmethod
    def _rotate_file(path: Path) -> None:
        """Rename fully-synced file to .synced.YYYY-MM-DD-HHMMSS (Windows-safe)."""
        if not path.exists():
            return
        suffix = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        dest = path.with_suffix(f".synced.{suffix}")
        for attempt in range(3):
            try:
                path.rename(dest)
                logger.info(f"[Story 38.8] Rotated {path.name} → {dest.name}")
                return
            except PermissionError:
                if attempt < 2:
                    time.sleep(0.1)
                else:
                    logger.warning(f"[Story 38.8] Cannot rotate {path.name} (PermissionError)")

    @staticmethod
    def _cleanup_old_synced_files(directory: Path, base_stem: str) -> None:
        """Delete .synced.* files older than retention period."""
        if not directory.exists():
            return
        cutoff = datetime.now() - timedelta(days=_SYNCED_FILE_RETENTION_DAYS)
        for f in directory.iterdir():
            if not f.name.startswith(base_stem) or ".synced." not in f.name:
                continue
            # Extract date from filename: base.synced.YYYY-MM-DD-HHMMSS or legacy YYYY-MM-DD
            try:
                date_str = f.name.rsplit(".synced.", 1)[1]
                # Try full timestamp first, then date-only (backward compat)
                for fmt in ("%Y-%m-%d-%H%M%S", "%Y-%m-%d"):
                    try:
                        file_date = datetime.strptime(date_str, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    continue
                if file_date < cutoff:
                    f.unlink(missing_ok=True)
                    logger.info(f"[Story 38.8] Cleaned up old synced file: {f.name}")
            except (ValueError, IndexError):
                pass

    # ─────────────────────────────────────────────────────────────────────
    # Utilities
    # ─────────────────────────────────────────────────────────────────────

    @staticmethod
    def _atomic_write_file(path: Path, content: str) -> None:
        """Windows-safe atomic write via tmp + rename with 3 retries."""
        tmp = path.with_suffix(".tmp")
        tmp.write_text(content, encoding="utf-8")
        for attempt in range(3):
            try:
                tmp.replace(path)
                return
            except PermissionError:
                if attempt < 2:
                    time.sleep(0.1)
                else:
                    raise

    @staticmethod
    def _build_group_id_from_canvas(canvas_name: str) -> Optional[str]:
        """Build group_id from canvas name using subject_config.

        wave-5 Stage B P0 (2026-05-11): prefer ContextVar (vault: prefix) over
        the legacy Story 1.9 build_group_id which collapses cross-vault
        subject:canvas pairs to the same id (collision risk).

        G2-3 (2026-08-28): 无 ContextVar 的后台重放上下文原本落
        ``build_vault_group_id("default", ...)`` 字面量 — 与主写路径
        (``memory_service._vault_scoped_group_id`` → ``get_current_vault_id()``)
        不同构。复合写身份下这不再 clobber 主概念 (那是 G2-3 前的破坏形态),
        但会把恢复的分数写进主 vault 读不到的平行组 = 恢复静默无效。
        现改为镜像主路径: vault_id 取进程 active vault (D1-A 单 active
        约束), 二级取 canvas (D16 ``vault:<id>:<canvas>`` 规约)。
        ⛔ 移交 G2-2 (VaultScope 统一): 跨 vault 切换后重放旧 vault 的
        待恢复条目仍会归到新 active vault — 条目本身不带 vault 维度,
        根治需 VaultScope + 落盘条目补 vault 字段, 不在本卡范围。
        """
        if not canvas_name:
            return None
        try:
            from app.config import get_current_vault_id
            from app.core.subject_config import (
                build_vault_group_id,
                canonical_group_id,
                get_current_subject_id,
                is_vault_group_id,
            )

            ctx_value = get_current_subject_id()
            if ctx_value and ctx_value != "general":
                return ctx_value if is_vault_group_id(ctx_value) else canonical_group_id(ctx_value)
            vault_id = get_current_vault_id()
            if not vault_id:
                return None
            return build_vault_group_id(vault_id, canvas_path=canvas_name)
        except (ImportError, AttributeError, ValueError):
            return None


# ─────────────────────────────────────────────────────────────────────────
# Module-level singleton
# ─────────────────────────────────────────────────────────────────────────

_fallback_sync_instance: Optional[FallbackSyncService] = None


def get_fallback_sync_service() -> FallbackSyncService:
    """Get or create FallbackSyncService singleton."""
    global _fallback_sync_instance
    if _fallback_sync_instance is None:
        neo4j = get_neo4j_client()
        _fallback_sync_instance = FallbackSyncService(neo4j_client=neo4j)
    return _fallback_sync_instance
