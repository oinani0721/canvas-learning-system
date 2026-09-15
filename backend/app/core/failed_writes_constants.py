# Story 38.6: Shared constants for failed writes fallback mechanism.
#
# Centralised here to avoid DRY violation (previously duplicated in
# agent_service.py and memory_service.py) and to provide a single lock
# that both the writer (_record_failed_write) and reader/recovery
# (recover_failed_writes, load_failed_scores) can share.
import logging
import threading
from pathlib import Path
from typing import Optional, Sequence

from app.core.failure_counters import bound_from_env, count_lines, rotate_if_over_limit

logger = logging.getLogger(__name__)

# Fallback JSONL file for writes that failed after all retries.
FAILED_WRITES_FILE: Path = (
    Path(__file__).parent.parent.parent / "data" / "failed_writes.jsonl"
)

# Lock shared across writer (agent_service) and reader (memory_service)
# so that recovery/read never races with concurrent append writes.
failed_writes_lock = threading.Lock()

# --- 写侧有界（CARD-NEO4J-REPLAY-BOUND / T6-C）---
#
# failed_writes 条目比 dead-letter 条目大（内嵌 content / metadata），按 ~1 KB
# 估：10000 行 ≈ 10 MB/文件，(1 活动 + 5 overflow) ≈ 60 MB 上限。
# env 覆盖：CLS_FAILED_WRITES_MAX_LINES / CLS_FAILED_WRITES_MAX_ROTATIONS
# （坏值退回默认并告警，见 failure_counters.bound_from_env）。
FAILED_WRITES_MAX_LINES: int = bound_from_env("CLS_FAILED_WRITES_MAX_LINES", 10000, minimum=1)
FAILED_WRITES_MAX_ROTATIONS: int = bound_from_env("CLS_FAILED_WRITES_MAX_ROTATIONS", 5, minimum=0)


def _replay_in_flight() -> bool:
    """回灌窗口是否开着（开着就**不许轮转**）。

    ⛔ 这是本卡最危险的一处交互，独立复核（workflow 对抗性复核 2026-09-15，
    Codex round-1 未发现）实地复现：

    ``fallback_sync_service._sync_failed_writes`` 的链是
    「持 ``failed_writes_lock`` 读快照(:284) → **放锁** 逐条 await 重放(:337)
    → 重新持锁 finalize(:358)」，而 finalize 判断「重放期间有没有新追加」用的是
    **长度比较 + 位置切片**::

        fallback_sync_service.py:366-367
        if len(current_lines) > len(lines):
            new_lines = current_lines[len(lines):]

    该判据的前提是**活动文件只增不减**（那个文件 :307 的注释自己写着这条契约）。
    本卡是第一个让它**变短**的写者：窗口内一旦轮转，活动文件被 rename 走、
    新文件只剩刚写的 k 条 ⇒ ``len(current) < len(lines)`` ⇒ ``new_lines=[]`` ⇒
    窗口内新写的条目要么被 :417 ``_atomic_write_file`` 整份覆盖销毁，要么在
    merged 为空时被 :422 ``_rotate_file`` 改名成 ``.synced.<ts>``——**谎称已回灌**，
    再由 30 天 retention 删掉。触发不需要多线程：``_record_structured_outbox``
    的调用方是 async 的 ``record_knowledge_entity``，:337 的 await 就是交错点。

    ``fallback_sync_service.py`` 在本卡是**禁改**面，所以修在写侧：回灌窗口
    开着就跳过轮转。上限因此是 best-effort（回灌期间可越限），但**不丢数据**
    —— 这个取舍的方向不可反转。

    实现说明：
    - 惰性 import —— ``fallback_sync_service:22`` 模块级 import 本模块，
      顶层反向 import 会成环。
    - ``asyncio.Lock.locked()`` 只读一个 bool，同步代码里调用不 await、不死锁。
    - 读到 True/False 的任一竞态都安全：调用方全程持 ``failed_writes_lock``，
      而回灌取快照也要先拿这把锁 ⇒ 「看到 False 于是轮转」时窗口必然尚未打开
      或已关闭，没有可被破坏的快照。
    - import 不到 / 属性不在（精简部署、测试替身）⇒ 视作「没有回灌」，
      退回有界行为，不因为观测不到就停掉上限。
    """
    try:
        from app.services.fallback_sync_service import _sync_all_lock
    except Exception:  # noqa: BLE001 — 观测不到回灌状态时退回有界行为
        return False
    try:
        return bool(_sync_all_lock.locked())
    except Exception:  # noqa: BLE001 — 同上
        return False


def append_failed_writes_bounded(
    file_path: Path,
    lines: Sequence[str],
    *,
    max_lines: Optional[int] = None,
    max_rotations: Optional[int] = None,
) -> None:
    """有界追加：核行数 → 超限先轮转 → 再追加。

    ⛔ **本函数不取任何锁**，调用方必须已持 ``failed_writes_lock``。
    ``threading.Lock`` 非重入，在已持锁的调用方里再取同一把 = 死锁。
    实测三个写者都在 ``with failed_writes_lock:`` 里追加
    （memory_service:515 / memory_service:2871 / agent_service:131），
    所以「核行数 → 轮转 → 追加」对**进程内**全部写者原子。

    ⚠️ ``file_path`` 是**显式入参**而不是读本模块的 ``FAILED_WRITES_FILE``
    全局。这是必须的：既有测试打桩的是**导入方**的绑定副本
    （``app.services.memory_service.FAILED_WRITES_FILE``，见
    test_a7_honest_failure.py:108/142、test_story_30_24_boundary.py:551/583/622），
    若这里改读本模块全局，那些打桩会全部失效 —— 测试会把条目写进现网
    ``backend/data/failed_writes.jsonl``，而且多半仍然显示绿（假绿）。

    ⚠️ ``agent_service:130`` 这个第三写者**不经本函数**，它只持锁、不核上限。
    所以不变量的准确表述是「经本函数的追加，追加后活动文件 ≤ max_lines」，
    **不是**「failed_writes.jsonl 恒 ≤ max_lines」。三条限定（Codex round-1 L1
    指出初版表述过强，这里逐条收紧）：

    1. 若**始终**只有 agent_service 写入、再没有经本函数的追加，越限可以
       **无限持续** —— 不是「暂时」。
    2. 「每个 ``.overflow.*`` 都 ≤ max_lines」**不成立**：活动文件在进入本函数
       前就已超限时（旁路突发），被**整体**轮转走的那一份就 > max_lines。
       成立的是「本函数**自己写出**的每一段 ≤ max_lines」。
    3. 「一条不丢」只在**单批条数 ≤ max_lines × (max_rotations + 1)** 时成立。
       单批超过总保留容量时，retention 会删掉**本批**较早的段。

    Args:
        file_path: 活动 JSONL 文件
        lines: 已序列化好的 JSON 字符串（不带换行）。序列化留在调用方，
            这样 ``json.dumps`` 的 TypeError/ValueError 仍由调用方原有的
            except 子句处理，异常语义不变。
        max_lines / max_rotations: 省略则取模块级常量（**调用时**读取，
            因此 ``monkeypatch.setattr`` 本模块常量对本函数生效）。
    """
    limit = FAILED_WRITES_MAX_LINES if max_lines is None else max_lines
    keep = FAILED_WRITES_MAX_ROTATIONS if max_rotations is None else max_rotations

    if _replay_in_flight():
        # 回灌窗口开着 ⇒ 只追加、不轮转（理由见 _replay_in_flight 的 docstring：
        # 轮转会让回灌 finalize 的「只增不减」判据失效，把窗口内新写的条目
        # 覆盖掉或错标成已回灌）。宁可暂时越限，也不丢死信。
        logger.warning(
            "[T6-C] 回灌窗口开着, 本次追加跳过轮转（防 finalize 误判新条目）: %s",
            file_path,
        )
        with open(file_path, "a", encoding="utf-8") as f:
            for line in lines:
                f.write(line + "\n")
        return

    # 分批写。``_flush_pending_failed_writes`` 一次可以交来**比上限还多**的条目，
    # 「追加前核一次行数」对这种单批就超限的情况完全无效（核的时候文件是空的，
    # 不轮转，然后一口气写 N 条 > 上限）。所以边写边留出空间：写满一段就轮转，
    # 再接着写下一段 —— 本函数写出的每一段都 ≤ limit（限定见 docstring 三条）。
    pending = list(lines)
    while pending:
        rotate_if_over_limit(file_path, limit, keep)
        room = len(pending)
        if limit > 0:
            try:
                room = limit - count_lines(file_path)
            except OSError as e:
                # Codex round-1 M1: 活动文件**可写但不可读**时（父目录 w+x 但文件
                # 不可读），rotate_if_over_limit 已经吞下了它那次读失败并返回
                # False，若这里再让 count_lines 抛出去，追加就整个不发生 ——
                # 比改动前的裸追加更糟，而且批量路径
                # (_flush_pending_failed_writes) 的 finally 会 clear() 掉
                # pending，条目直接消失。数不出行数就退化成「一次写完」：
                # 宁可暂时越限，也不丢死信。
                logger.warning("[T6-C] 数行失败, 本次不设上限直接追加 %s: %s", file_path, e)
                room = len(pending)
        if room <= 0:
            # 轮转没能腾出空间（上限关闭，或 rename 失败）⇒ 一次写完。
            # 宁可暂时越限也不丢条目，也避免每轮只写一行的死循环。
            room = len(pending)
        chunk, pending = pending[:room], pending[room:]
        with open(file_path, "a", encoding="utf-8") as f:
            for line in chunk:
                f.write(line + "\n")
