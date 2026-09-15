# Story 38.6: Shared constants for failed writes fallback mechanism.
#
# Centralised here to avoid DRY violation (previously duplicated in
# agent_service.py and memory_service.py) and to provide a single lock
# that both the writer (_record_failed_write) and reader/recovery
# (recover_failed_writes, load_failed_scores) can share.
import threading
from pathlib import Path
from typing import Optional, Sequence

from app.core.failure_counters import bound_from_env, count_lines, rotate_if_over_limit

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
    **不是**「failed_writes.jsonl 恒 ≤ max_lines」：纯 agent_service 的突发
    可以暂时越限，下一次经本函数的追加会把超出部分整体轮转走。

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

    # 分批写。``_flush_pending_failed_writes`` 一次可以交来**比上限还多**的条目，
    # 「追加前核一次行数」对这种单批就超限的情况完全无效（核的时候文件是空的，
    # 不轮转，然后一口气写 N 条 > 上限）。所以边写边留出空间：写满一段就轮转，
    # 再接着写下一段。这样活动文件与每个 .overflow.* 都 ≤ limit，且一条不丢。
    pending = list(lines)
    while pending:
        rotate_if_over_limit(file_path, limit, keep)
        room = limit - count_lines(file_path) if limit > 0 else len(pending)
        if room <= 0:
            # 轮转没能腾出空间（上限关闭，或 rename 失败）⇒ 一次写完。
            # 宁可暂时越限也不丢条目，也避免每轮只写一行的死循环。
            room = len(pending)
        chunk, pending = pending[:room], pending[room:]
        with open(file_path, "a", encoding="utf-8") as f:
            for line in chunk:
                f.write(line + "\n")
