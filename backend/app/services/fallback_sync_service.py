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
import hashlib
import json
import os
import threading

import structlog
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from app.clients.neo4j_client import Neo4jClient, get_neo4j_client
from app.core.failed_writes_constants import FAILED_WRITES_FILE, failed_writes_lock
from app.core.failure_counters import overflow_siblings

# T1 统一 (2026-07-10): 物理层 group_id 单一 __ 格式 (graphiti_core validator 拒冒号)
from app.graphiti.group_id_compat import to_physical_group_id

logger = structlog.get_logger(__name__)

# Directory paths
_BACKEND_DIR = Path(__file__).parent.parent.parent  # backend/
_APP_DATA_DIR = Path(__file__).parent.parent / "data"  # backend/app/data/

CANVAS_EVENTS_FALLBACK_FILE = _APP_DATA_DIR / "canvas_events_fallback.json"
LEARNING_MEMORIES_FILE = _BACKEND_DIR / "data" / "learning_memories.json"
SYNC_CHECKPOINT_FILE = _BACKEND_DIR / "data" / "sync_checkpoint.json"

#: CARD-REPLAY-REWRITE (P2-C): **已确认身份日志** ——
#: ``{代际文件名: [record_id, …]}``，与 checkpoint 同一把 ``_checkpoint_lock``、
#: 同一目录、原子写。它是 failed_writes 链的**唯一进度载体**（位置游标退场）：
#: 每条确认（写 + 回执比对通过）后先落这里再进下一条，finalize 按身份从该代
#: 文件里剔除已确认者。崩溃在任一点重启只会重试未确认者。
SYNC_CONFIRMED_IDS_FILE = _BACKEND_DIR / "data" / "sync_confirmed_ids.json"

#: 历史无身份条目（无 vault_id 且无 group_id）的**显式归属点名单**环境变量。
#: 默认不设 ⇒ 默认隔离（留在文件、计 quarantined、不写任何 vault）。
LEGACY_NOSCOPE_VAULT_ENV = "CLS_REPLAY_LEGACY_NOSCOPE_VAULT"

# Lock for checkpoint file access
_checkpoint_lock = threading.Lock()

# Days before .synced files are cleaned up
_SYNCED_FILE_RETENTION_DAYS = 30

# Checkpoint save interval (entries)
_CHECKPOINT_INTERVAL = 50

#: **进度语义版本** —— checkpoint 存的下标只在同一「切行口径 + 游标语义」下有意义。
#: 变更这个值的条件: 改动 :meth:`_sync_failed_writes` 的切行方式**或**游标推进规则。
#: ⚠️ CARD-REPLAY-REWRITE (P2-C) 起: failed_writes 链**不再使用位置游标**
#: （进度载体 = :data:`SYNC_CONFIRMED_IDS_FILE` 的身份日志），本常量自此只影响
#: learning_memories 链的 checkpoint 读取; 完整历史保留以便审计。
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
#:   "identity-v2"                 CARD-REPLAY-REWRITE (P2-C): failed_writes 回灌改
#:                                 「稳定记录身份 + 确认身份日志」，**不再读位置
#:                                 游标** ⇒ 位置游标与文件代际错配这一整类失效面
#:                                 消失; 旧标记（含上一行那版）一律被忽略。
#:
#: ⛔ 读到任何不等于当前值的标记一律**回退到 0**。
#: r8 这一版尤其要紧 (Codex round-8 HIGH-1, 本卡修复遗漏):
#:   负控 —— r7 之前前 50 条 LEARNED 成功、其中一条评分历史失败但**仍被记成成功**,
#:   于是存下 `index=50, progress_version="split-lf+contiguous"`; 升级后该标记
#:   在旧口径下仍"有效", 那条缺历史的条目被跳过并随文件轮转出队。
#:   r7 的 `return False` 只修好**重新执行**的记录, 覆盖不到**已被旧游标跳过**的。
#:   ⇒ 成功条件一变, 按旧条件写下的游标就必须作废。
_PROGRESS_VERSION = "identity-v2"

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


def _canonical_entry_json(entry: Dict[str, Any]) -> str:
    """身份哈希用的规范 JSON（sort_keys 紧凑形态 —— 键序不同 == 同一条）。"""
    return json.dumps(entry, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _legacy_record_id(entry: Dict[str, Any]) -> str:
    """历史无身份条目的稳定身份 = ``sha256(规范 JSON)``。

    内容逐字相同（规范形态相同）的历史条目视为**同一条** ⇒ 只重放一次
    （计 ``deduped``）。取舍已登记待用户裁：内容相同但语义独立的两条会被合并
    —— 与 ``_event_fingerprint`` 同型的已知问题; 对死信回灌而言最坏后果是少记
    一次历史 Episode, 方向可接受（重复重放更糟）。
    """
    return hashlib.sha256(_canonical_entry_json(entry).encode("utf-8")).hexdigest()


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
        """Replay scoring failures from failed_writes.jsonl (+ .overflow.* 代际) to Neo4j.

        CARD-REPLAY-REWRITE (P2-C) 重写 —— 与旧算法的契约差异:

        - **身份代替位置**: 每条按 ``record_id``（新条目）或
          ``sha256(规范 JSON)``（历史条目, identity_source=legacy-hash）识别;
          内容逐字相同的历史条目视为同一条（计 ``deduped``）。
          位置游标退场, ``_load_checkpoint("failed_writes")`` 不再被调用。
        - **确认身份日志**: 每条确认（写 + 回执比对通过）后先把 record_id 落进
          ``SYNC_CONFIRMED_IDS_FILE[代际文件名]`` 再进下一条; finalize 按身份从
          该代文件里剔除已确认者、剩余原子写回, 再清该代日志。崩溃在任一点重启
          只会重试未确认者, 不会跳过、也不会重放已确认者。
        - **来源 vault**: 条目自带 ``group_id`` / ``vault_id`` 优先; 都缺 ⇒
          **默认隔离**（不写图、留在文件、计 ``quarantined``）; 仅当环境变量
          :data:`LEGACY_NOSCOPE_VAULT_ENV` 显式点名目标 vault 时才按该值归属。
        - **overflow 代际扫回**: 回灌集合 = ``overflow_siblings()``（最老先）+
          活动文件; 某代全部确认 ⇒ ``_rotate_file`` 成 ``.synced.<ts>``
          （沿 30 天 retention 清理）。

        返回 ``{"recovered", "pending", "confirmed", "quarantined", "deduped",
        "generations"}``；读异常时额外带 ``"error": str``，``pending`` 可能为
        **-1**（= 数不出来）。键语义:

        - ``recovered``: 本轮新确认条目数; ``confirmed``: recovered + 经日志跳过的
          已确认数（「这一代总共已被确认多少」）;
        - ``pending``: 活动文件 + 各 overflow 代际**重写后剩余行数之和**
          （含被隔离条目与坏行）;
        - ``generations``: 本轮扫回的 overflow 代际数。
        """
        totals = {"recovered": 0, "confirmed_skipped": 0, "quarantined": 0, "deduped": 0}
        remaining_total = 0
        # ⚠️ Codex r1 MEDIUM-1: 「未知」不能被算术吞掉 —— 任一代 remaining<0（数不出来）
        # 或列举/处理中断时，顶层一律 pending=-1 + error（未知不与已知剩余数相加）。
        unknown: Optional[str] = None

        try:
            generations = overflow_siblings(FAILED_WRITES_FILE)
        except OSError as e:
            logger.warning("[P2-C] 列出 .overflow.* 代际失败, 本轮只回灌活动文件: %s", e)
            generations = []
            unknown = f"cannot list overflow generations: {e}"

        for gen_path in generations:
            try:
                gen = await self._replay_failed_writes_generation(gen_path, active=False)
            except OSError as e:
                logger.warning("[P2-C] 代际 %s 处理中断, 留待下轮: %s", gen_path.name, e)
                unknown = unknown or f"generation {gen_path.name} interrupted: {e}"
                continue
            for key in totals:
                totals[key] += gen[key]
            if gen["remaining"] < 0:
                unknown = unknown or f"generation {gen_path.name} unreadable: {gen.get('error', '')}"
            else:
                remaining_total += gen["remaining"]

        active = await self._replay_failed_writes_generation(FAILED_WRITES_FILE, active=True)
        for key in totals:
            totals[key] += active[key]
        if active["remaining"] < 0:
            unknown = unknown or (active.get("error") or "active generation read failed")
        else:
            remaining_total += active["remaining"]

        if totals["quarantined"]:
            logger.warning(
                "[P2-C] %d 条历史条目缺 vault_id 且无 group_id, 默认隔离未回灌"
                "（留在文件; 设 %s=<vault_id> 可显式归属）",
                totals["quarantined"],
                LEGACY_NOSCOPE_VAULT_ENV,
            )

        self._cleanup_old_synced_files(FAILED_WRITES_FILE.parent, FAILED_WRITES_FILE.stem)

        result: Dict[str, Any] = {
            "recovered": totals["recovered"],
            "pending": -1 if unknown else remaining_total,
            "confirmed": totals["recovered"] + totals["confirmed_skipped"],
            "quarantined": totals["quarantined"],
            "deduped": totals["deduped"],
            "generations": len(generations),
        }
        if unknown:
            result["error"] = f"finalize/read failed: {unknown}"
        return result

    async def _replay_failed_writes_generation(self, path: Path, *, active: bool) -> Dict[str, Any]:
        """按身份回灌**一代**文件（活动文件或 .overflow.* 代际）。

        返回 ``{"recovered", "confirmed_skipped", "quarantined", "deduped",
        "remaining"}``（读不出来时 ``remaining == -1`` 且带 ``error``，文件未动）；
        写回/轮转阶段的 OSError **上抛**（崩溃注入门依赖它）。
        """
        generation = path.name
        if active:
            with failed_writes_lock:
                try:
                    raw = path.read_text(encoding="utf-8")
                except FileNotFoundError:
                    raw = ""
                except OSError as e:
                    logger.warning(f"[Story 38.8] Cannot read failed_writes: {e}")
                    return {
                        "recovered": 0,
                        "confirmed_skipped": 0,
                        "quarantined": 0,
                        "deduped": 0,
                        "remaining": -1,
                        "error": f"cannot read: {e}",
                    }
        else:
            try:
                raw = path.read_text(encoding="utf-8")
            except FileNotFoundError:
                return {"recovered": 0, "confirmed_skipped": 0, "quarantined": 0, "deduped": 0, "remaining": 0}
            except OSError as e:
                logger.warning("[P2-C] Cannot read generation %s: %s", generation, e)
                return {
                    "recovered": 0,
                    "confirmed_skipped": 0,
                    "quarantined": 0,
                    "deduped": 0,
                    "remaining": -1,
                    "error": f"cannot read: {e}",
                }

        lines = [line for line in raw.split("\n") if line.strip()]

        items: List[Tuple[Optional[str], str, Optional[Dict[str, Any]], str]] = []
        seen: Set[str] = set()
        deduped = 0
        for line in lines:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                items.append((None, "malformed", None, line))
                continue
            if not isinstance(entry, dict):
                items.append((None, "malformed", None, line))
                continue
            rid = entry.get("record_id")
            if isinstance(rid, str) and rid:
                source = "entry"
            else:
                rid = _legacy_record_id(entry)
                source = "legacy-hash"
            if rid in seen:
                deduped += 1
                continue
            seen.add(rid)
            items.append((rid, source, entry, line))

        confirmed: Set[str] = set(self._load_confirmed_ids(generation))
        confirmed_skipped = 0
        recovered = 0
        quarantined = 0

        for rid, source, entry, line in items:
            if entry is None:
                continue  # 坏行: 无身份可谈, finalize 原样保留
            if rid is not None and rid in confirmed:
                confirmed_skipped += 1
                continue
            group_id, reason = self._resolve_entry_source(entry)
            if group_id is None:
                if reason == "quarantined":
                    quarantined += 1
                else:
                    logger.warning("[P2-C] 条目来源不可解析(%s), 留待: %s", reason, generation)
                continue
            try:
                ok = await self._replay_scoring_entry_to_neo4j(entry, record_id=rid)
            except (RuntimeError, ConnectionError, asyncio.TimeoutError) as e:
                logger.warning(f"[Story 38.8] failed_writes replay error: {e}")
                ok = False
            if ok:
                recovered += 1
                if rid is not None:
                    confirmed.add(rid)
                    # 「先记日志再进下一条」: 崩溃在确认与写回之间只会重试未确认者。
                    self._persist_confirmed_ids(generation, confirmed)
            # 失败/隔离: 不记日志 ⇒ finalize 会把它写回。

        # finalize: 按身份剔除已确认者; 剩余原子写回; 全空则轮转; 再清该代日志。
        if active:
            with failed_writes_lock:
                try:
                    current_raw = path.read_text(encoding="utf-8")
                except FileNotFoundError:
                    current_raw = ""
                except OSError as e:
                    logger.error(
                        "[Story 38.8] failed_writes finalize re-read failed (%s) — "
                        "leaving the file untouched; remaining count unknown.",
                        e,
                    )
                    return {
                        "recovered": recovered,
                        "confirmed_skipped": confirmed_skipped,
                        "quarantined": quarantined,
                        "deduped": deduped,
                        "remaining": -1,
                        "error": f"finalize re-read failed: {e}",
                    }
                current_lines = [line for line in current_raw.split("\n") if line.strip()]
                keep_lines = self._filter_confirmed_lines(current_lines, confirmed)
                if keep_lines:
                    self._atomic_write_file(path, "\n".join(keep_lines) + "\n")
                else:
                    self._rotate_file(path)
                # 旧位置游标 best-effort 清理（身份算法不再读它; 失败不阻断）。
                try:
                    self._clear_checkpoint("failed_writes")
                except OSError as e:
                    logger.warning("[P2-C] 清理旧 failed_writes 位置游标失败(不影响身份日志): %s", e)
                remaining = len(keep_lines)
        else:
            # overflow 代际: 写侧不会再追加; 但 _prune_overflow 可能在本轮处理期间
            # 把它删掉 —— 加锁复查, 已删则不复活。
            with failed_writes_lock:
                try:
                    current_raw = path.read_text(encoding="utf-8")
                except FileNotFoundError:
                    logger.info("[P2-C] overflow 代际 %s 在处理期间已被清理, 跳过写回", generation)
                    self._clear_confirmed_ids(generation)
                    return {
                        "recovered": recovered,
                        "confirmed_skipped": confirmed_skipped,
                        "quarantined": quarantined,
                        "deduped": deduped,
                        "remaining": 0,
                    }
                except OSError as e:
                    logger.warning("[P2-C] overflow 代际 %s 重读失败, 留待下轮: %s", generation, e)
                    return {
                        "recovered": recovered,
                        "confirmed_skipped": confirmed_skipped,
                        "quarantined": quarantined,
                        "deduped": deduped,
                        "remaining": -1,
                    }
                current_lines = [line for line in current_raw.split("\n") if line.strip()]
                keep_lines = self._filter_confirmed_lines(current_lines, confirmed)
                if keep_lines:
                    self._atomic_write_file(path, "\n".join(keep_lines) + "\n")
                else:
                    self._rotate_file(path)
                remaining = len(keep_lines)

        self._clear_confirmed_ids(generation)
        return {
            "recovered": recovered,
            "confirmed_skipped": confirmed_skipped,
            "quarantined": quarantined,
            "deduped": deduped,
            "remaining": remaining,
        }

    @staticmethod
    def _filter_confirmed_lines(current_lines: List[str], confirmed: Set[str]) -> List[str]:
        """从当前文件内容里剔除**已确认身份**的行（坏行原样保留）。"""
        keep: List[str] = []
        for line in current_lines:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                keep.append(line)
                continue
            if not isinstance(entry, dict):
                keep.append(line)
                continue
            rid = entry.get("record_id")
            if not (isinstance(rid, str) and rid):
                rid = _legacy_record_id(entry)
            if rid in confirmed:
                continue
            keep.append(line)
        return keep

    def _resolve_entry_source(self, entry: Dict[str, Any]) -> Tuple[Optional[str], str]:
        """条目来源组解析: 自带 ``group_id`` > 自带 ``vault_id`` > env 点名。

        返回 ``(逻辑组 id 或 None, reason)``; reason ∈
        ``{"entry-group", "entry-vault", "env-vault", "quarantined", "unresolvable"}``。
        ``quarantined`` = 无任何来源线索（默认隔离）; ``unresolvable`` = 有线索
        但解析不出组（如缺 canvas_name）⇒ 留待。
        """
        entry_group = entry.get("group_id")
        if isinstance(entry_group, str) and entry_group.strip():
            return entry_group.strip(), "entry-group"
        vault_id = entry.get("vault_id")
        reason = "entry-vault"
        if not (isinstance(vault_id, str) and vault_id.strip()):
            env_vault = os.environ.get(LEGACY_NOSCOPE_VAULT_ENV, "").strip()
            if not env_vault:
                return None, "quarantined"
            vault_id = env_vault
            reason = "env-vault"
        canvas_name = entry.get("canvas_name") or entry.get("canvas_path") or ""
        if not canvas_name:
            return None, "unresolvable"
        try:
            from app.core.subject_config import build_vault_group_id

            return build_vault_group_id(vault_id, canvas_path=canvas_name), reason
        except (ImportError, AttributeError, ValueError):
            return None, "unresolvable"

    def _load_confirmed_ids(self, generation: str) -> List[str]:
        """读某代际的已确认身份列表（读不到/坏文件按空处理 = 多一次幂等重放）。"""
        with _checkpoint_lock:
            try:
                raw = SYNC_CONFIRMED_IDS_FILE.read_text(encoding="utf-8")
            except FileNotFoundError:
                return []
            except (OSError, ValueError) as e:
                logger.warning("[P2-C] 读确认身份日志失败, 按空处理: %s", e)
                return []
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            return []
        if not isinstance(data, dict):
            return []
        ids = data.get(generation, [])
        return [i for i in ids if isinstance(i, str)] if isinstance(ids, list) else []

    def _persist_confirmed_ids(self, generation: str, ids: Set[str]) -> None:
        """把该代的已确认身份集合原子落盘（每条确认后调用 = 「先记日志再进下一条」）。

        写失败**不阻断**回放（记 error）: 最坏后果 = 崩溃后多一次幂等重放
        （Episode 按 record_id MERGE ⇒ 不产生重复）。
        """
        with _checkpoint_lock:
            data: Dict[str, Any] = {}
            try:
                loaded = json.loads(SYNC_CONFIRMED_IDS_FILE.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    data = loaded
            except FileNotFoundError:
                pass
            except (OSError, ValueError):
                data = {}  # 读不出 ⇒ 重写（别的代际最多多一次幂等重放）
            data[generation] = sorted(ids)
            try:
                SYNC_CONFIRMED_IDS_FILE.parent.mkdir(parents=True, exist_ok=True)
                self._atomic_write_file(SYNC_CONFIRMED_IDS_FILE, json.dumps(data, ensure_ascii=False, indent=2))
            except OSError as e:
                logger.error("[P2-C] 确认身份日志落盘失败(不阻断, 崩溃后多一次幂等重放): %s", e)

    def _clear_confirmed_ids(self, generation: str) -> None:
        """清掉某代际的确认日志（finalize 写回后调用; 失败不阻断）。"""
        with _checkpoint_lock:
            data: Dict[str, Any] = {}
            try:
                loaded = json.loads(SYNC_CONFIRMED_IDS_FILE.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    data = loaded
            except FileNotFoundError:
                return
            except (OSError, ValueError):
                data = {}
            data.pop(generation, None)
            try:
                if data:
                    self._atomic_write_file(SYNC_CONFIRMED_IDS_FILE, json.dumps(data, ensure_ascii=False, indent=2))
                else:
                    SYNC_CONFIRMED_IDS_FILE.unlink(missing_ok=True)
            except OSError as e:
                logger.warning("[P2-C] 清确认身份日志失败(残留条目无害): %s", e)

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

        # CARD-REPLAY-REWRITE (P2-C): 本链的**位置游标一并退场**（结构判据要求
        # 全文件不再出现位置游标符号）。旧游标只服务「三条链语义统一」这个摆设
        # （旧注释历史保留在 git），且它与 canvas 链 round-7 HIGH-1 同型：重放前
        # ``sort(key=timestamp)`` 后「第 i 条」不是稳定身份，晚到的时间戳更早条目
        # 会落到游标之前被跳过。本链重放幂等（MERGE + last-write-wins）、
        # 不写回不轮转 ⇒ 每轮全量重放是安全方向（条目永不丢）。
        recovered = 0
        failed = 0
        for mem in memories:
            try:
                success = await self._replay_learning_memory_to_neo4j(mem)
                if success:
                    recovered += 1
                else:
                    failed += 1
            except (RuntimeError, ConnectionError, asyncio.TimeoutError) as e:
                logger.warning(f"[Story 38.8] learning_memory replay error: {e}")
                failed += 1

        # NOTE: learning_memories.json is NOT rotated - still needed by
        # LearningMemoryClient for runtime queries.
        # 旧版本写下的位置游标 best-effort 清理（本链已不读游标）。
        self._clear_checkpoint("learning_memories")

        return {"recovered": recovered, "pending": failed}

    # ─────────────────────────────────────────────────────────────────────
    # Replay helpers
    # ─────────────────────────────────────────────────────────────────────

    async def _replay_scoring_entry_to_neo4j(
        self,
        entry: Dict[str, Any],
        record_id: Optional[str] = None,
    ) -> bool:
        """回灌单条评分失败条目 —— **写完读回执才算成功**（P2-C 重写）。

        与旧实现的差异:

        - **组来源**: 条目自带 ``group_id`` / ``vault_id`` 优先（缺则 env 点名;
          都无 ⇒ 拒写, 由调用方计 quarantined）—— 不看进程 active vault。
        - **回执**: MERGE 语句 RETURN 写后属性, 与送入值逐字段比对;
          ``should_update=false`` 时要求图上 ``r.timestamp`` 确实更新（让位成功）,
          任一不符判失败留待。
        - **时间**: 缺 ``timestamp`` 用 ``recorded_at``; 两者都缺 ⇒ 只在图上无值
          时写入（不取 ``now()`` 覆盖图上更新的分数 —— 裁定书 §1.5 A 方向）。
        - **Episode**: 走 :meth:`Neo4jClient.record_score_history_by_record_id`
          （``record_id`` 幂等）; 二次写失败/拒写整条判失败（沿 r7 HIGH-4 口径）。
          ⚠️ 缺时间戳且带 score 的条目**整条留待**（无可靠事件时间, 不取 ``now()``;
          跳过二次写却确认 = 静默丢历史 —— Codex r1 HIGH-1）。
        """
        concept = entry.get("concept") or entry.get("concept_id", "")
        canvas_name = entry.get("canvas_name", "")
        score = entry.get("score")

        if not concept:
            logger.warning("[Story 38.8] Skipping entry with no concept")
            return False

        if score is not None:
            # Codex r1 MEDIUM-2: score 不可转 int 是**确定性坏输入** —— 在网络异常
            # 捕获之前就拒掉, 否则 int() 的 ValueError 会中断整代回灌、后续条目被
            # 同一条永久挡住（且 LEARNED 已被写成脏值）。整条留待、其余照常。
            try:
                int(score)
            except (TypeError, ValueError, OverflowError):
                logger.warning(
                    "[P2-C] scoring replay: score 不可转 int, 整条留待 (concept=%r, score=%r)",
                    concept,
                    score,
                )
                return False

        group_id, reason = self._resolve_entry_source(entry)
        if group_id is None:
            logger.error(
                "[P2-C] scoring replay refused: unresolved entry source (reason=%s, concept=%r, canvas_name=%r)",
                reason,
                concept,
                canvas_name,
            )
            return False

        if record_id is None:
            rid = entry.get("record_id")
            record_id = rid if isinstance(rid, str) and rid else _legacy_record_id(entry)

        ts = entry.get("timestamp") or entry.get("recorded_at")
        physical_group = to_physical_group_id(group_id)

        if ts is None:
            ok = await self._replay_scoring_entry_no_ts(entry, concept, score, physical_group)
        else:
            ok = await self._replay_scoring_entry_with_ts(entry, concept, score, ts, physical_group)
        if not ok:
            return False

        if score is not None and ts is None:
            # CARD-REPLAY-REWRITE (Codex r1 HIGH-1): 缺 timestamp 且带 score ⇒ 写不出
            # 带事件时间的评分历史（⛔ 不取 now()）⇒ **整条不确认**（留在文件、计 pending）。
            # 裁定书 §1.8④ 把「二次写」列为成功确认条件之一；跳过它却确认 = 静默丢历史。
            logger.warning(
                "[P2-C] scoring replay: 缺 timestamp 且带 score, 无可靠事件时间, 整条留待 (concept=%r)",
                concept,
            )
            return False
        if score is not None:
            try:
                concept_id = entry.get("concept_id", concept)
                ok2 = await self._neo4j.record_score_history_by_record_id(
                    record_id=record_id,
                    concept_id=concept_id,
                    canvas_name=canvas_name,
                    score=int(score),
                    timestamp=ts,
                    group_id=group_id,
                )
            except (RuntimeError, ConnectionError, asyncio.TimeoutError) as e:
                logger.warning(f"[Story 38.8] Score history record failed: {e} — entry stays pending")
                return False
            if ok2 is False:
                logger.warning(
                    "[Story 38.8] Score history record refused (record_id=%r) — entry stays pending",
                    record_id,
                )
                return False

        return True

    async def _replay_scoring_entry_with_ts(
        self,
        entry: Dict[str, Any],
        concept: str,
        score: Any,
        ts: str,
        physical_group: str,
    ) -> bool:
        """有时间戳分支: last-write-wins + 写后回执比对。"""
        query = """
        MERGE (u:User {id: $userId})
        MERGE (c:Concept {name: $concept, group_id: $groupId})
        MERGE (u)-[r:LEARNED {group_id: $groupId}]->(c)
        WITH r, c,
             CASE WHEN r.timestamp IS NULL OR r.timestamp <= datetime($ts)
                  THEN true ELSE false END AS should_update
        SET r.score = CASE WHEN should_update THEN $score ELSE r.score END,
            r.timestamp = CASE WHEN should_update THEN datetime($ts) ELSE r.timestamp END
        RETURN should_update,
               r.score AS score_after,
               c.group_id AS group_after,
               (r.timestamp = datetime($ts)) AS ts_equal,
               (r.timestamp > datetime($ts)) AS ts_after_ts
        """
        try:
            results = await self._neo4j.run_query(
                query,
                userId="default_user",
                concept=concept,
                score=score,
                ts=ts,
                groupId=physical_group,
            )
        except (RuntimeError, ConnectionError, asyncio.TimeoutError) as e:
            logger.warning(f"[Story 38.8] Neo4j scoring replay failed: {e}")
            return False
        row = results[0] if results else None
        if not row:
            logger.warning("[P2-C] scoring replay: 空回执, 不能确认 (concept=%r)", concept)
            return False
        if row.get("should_update") is False:
            if row.get("ts_after_ts") is True:
                logger.info(f"[Story 38.8] Conflict: Neo4j has newer data for '{concept}', fallback timestamp={ts}")
                return True
            logger.warning("[P2-C] scoring replay: should_update=False 但图上时间戳并不更新 (concept=%r)", concept)
            return False
        if row.get("should_update") is not True:
            logger.warning("[P2-C] scoring replay: 回执缺 should_update (concept=%r)", concept)
            return False
        if score is not None and row.get("score_after") != score:
            logger.warning(
                "[P2-C] scoring replay: 回执分数不符 (concept=%r, want=%r, got=%r)",
                concept,
                score,
                row.get("score_after"),
            )
            return False
        if row.get("group_after") != physical_group:
            logger.warning("[P2-C] scoring replay: 回执组不符 (concept=%r)", concept)
            return False
        if row.get("ts_equal") is not True:
            logger.warning("[P2-C] scoring replay: 回执时间戳不符 (concept=%r)", concept)
            return False
        return True

    async def _replay_scoring_entry_no_ts(
        self,
        entry: Dict[str, Any],
        concept: str,
        score: Any,
        physical_group: str,
    ) -> bool:
        """无时间戳分支: 只在图上**无值**时写入; 有值一律不覆盖（不取 now()）。

        图上有值（``r.timestamp`` 非空）⇒ 本条的分数不应用, 但条目**已被正确处理**
        （让位）⇒ 判成功; 图上无值 ⇒ 写入分数（不写 timestamp —— 没有可靠事件时间）。
        """
        query = """
        MERGE (u:User {id: $userId})
        MERGE (c:Concept {name: $concept, group_id: $groupId})
        MERGE (u)-[r:LEARNED {group_id: $groupId}]->(c)
        WITH r, c,
             CASE WHEN r.timestamp IS NULL THEN true ELSE false END AS should_update
        SET r.score = CASE WHEN should_update THEN $score ELSE r.score END
        RETURN should_update,
               r.score AS score_after,
               c.group_id AS group_after,
               (r.timestamp IS NULL) AS graph_ts_absent
        """
        try:
            results = await self._neo4j.run_query(
                query,
                userId="default_user",
                concept=concept,
                score=score,
                groupId=physical_group,
            )
        except (RuntimeError, ConnectionError, asyncio.TimeoutError) as e:
            logger.warning(f"[Story 38.8] Neo4j scoring replay failed: {e}")
            return False
        row = results[0] if results else None
        if not row:
            logger.warning("[P2-C] no-ts replay: 空回执, 不能确认 (concept=%r)", concept)
            return False
        if row.get("should_update") is False:
            if row.get("graph_ts_absent") is False:
                return True
            logger.warning("[P2-C] no-ts replay: should_update=False 但图上无值 (concept=%r)", concept)
            return False
        if row.get("should_update") is not True:
            logger.warning("[P2-C] no-ts replay: 回执缺 should_update (concept=%r)", concept)
            return False
        if score is not None and row.get("score_after") != score:
            logger.warning(
                "[P2-C] no-ts replay: 回执分数不符 (concept=%r, want=%r, got=%r)",
                concept,
                score,
                row.get("score_after"),
            )
            return False
        if row.get("group_after") != physical_group:
            logger.warning("[P2-C] no-ts replay: 回执组不符 (concept=%r)", concept)
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
