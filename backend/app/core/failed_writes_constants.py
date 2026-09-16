# Story 38.6: Shared constants for failed writes fallback mechanism.
#
# Centralised here to avoid DRY violation (previously duplicated in
# agent_service.py and memory_service.py) and to provide a single lock
# that both the writer (_record_failed_write) and reader/recovery
# (recover_failed_writes, load_failed_scores) can share.
import json
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
    - import 不到 / 属性不在（精简部署、测试替身）⇒ 本函数视作「没有回灌」。
      ⚠️ 但**净效果不是「退回有界行为」**（Codex round-3 LOW-5 指出初版这句
      失真，已更正）：同一个 import 失败会让
      :func:`_invalidate_replay_checkpoint` 返回 False，而它是轮转的前置动作，
      于是实际结果是**永不轮转**（满额后一直裸追加）。方向仍然安全——
      宁可越限也不丢数据——但它是「停掉上限」而不是「维持上限」，
      别按字面理解成后者。持续的权限故障同样会让越限无限持续。
    """
    try:
        from app.services.fallback_sync_service import _sync_all_lock
    except Exception:  # noqa: BLE001 — 观测不到回灌状态时退回有界行为
        return False
    try:
        return bool(_sync_all_lock.locked())
    except Exception:  # noqa: BLE001 — 同上
        return False


def _invalidate_replay_checkpoint() -> bool:
    """把 ``failed_writes`` 的回灌游标作废。成功（含本来就没有）返回 True。

    ⛔ **换代与游标失效必须同生共死** —— 这条不变量是
    ``fallback_sync_service._clear_checkpoint`` 的 docstring 自己立的：
    回灌保存的 checkpoint 是**当次快照的下标**，所以任何让活动文件换代的动作
    都必须先把旧游标作废，否则下一轮会按一个指向**上一代文件**的下标跳过记录。

    本卡的写侧轮转是**第二个**让它换代的动作（第一个是回灌自己的
    ``_rotate_file`` / ``_atomic_write_file``），初版只挡了「回灌窗口开着」，
    没管「窗口已关但游标还残留」（Codex round-2 H1，已复现）：

        原文件 51 条、游标 index=50 → finalize 撞 OSError ⇒ 文件与游标都保留、
        锁释放 → 写侧追加 1 条并轮转 ⇒ 新文件只有 1 行 → 下一轮回灌
        ``for i, line in enumerate(lines)`` 全部 ``i < 50`` 被跳过 ⇒ 该条**从未
        重放**，却因 still_pending 为空而被 ``_rotate_file`` 改名 ``.synced.``
        （= 谎称已回灌），30 天后删除。它既没进 overflow 也没走 retention，
        **不属于本卡已披露的那个取舍**。

    实现选择（两处刻意为之）：

    1. **不走 ``get_fallback_sync_service()``** —— 它会 ``get_neo4j_client()``
       构造客户端单例，而这里是「写一条死信」的热路径，不该在上面挂一个
       数据库客户端的构造。改为直接用该模块的**模块级**
       ``SYNC_CHECKPOINT_FILE`` 与 ``_checkpoint_lock``（惰性 import 避免成环）。
       只 ``pop`` 一个顶层键、不依赖条目内部结构，与 ``_clear_checkpoint``
       的漂移面只有「键名」一处。
    2. **失败返回 False 而不是吞掉** —— 调用方据此**放弃本次轮转**，与
       ``_clear_checkpoint``「清不掉就一律上抛、由调用方决定不动文件」
       完全同口径。宁可暂时越限，也不留一个指向上一代文件的游标。

    锁序：调用方持 ``failed_writes_lock``，这里再取 ``_checkpoint_lock``；
    与既有 ``_sync_failed_writes``（``:357`` 持 ``failed_writes_lock`` 后于
    ``:397`` 调 ``_clear_checkpoint``）**同向**，无反序嵌套。
    """
    try:
        from app.services.fallback_sync_service import (
            SYNC_CHECKPOINT_FILE,
            _checkpoint_lock,
        )
    except Exception as e:  # noqa: BLE001 — 见 docstring：观测不到就不换代
        logger.error("[T6-C] 取不到回灌 checkpoint 接口, 本次不轮转: %s", e)
        return False

    try:
        with _checkpoint_lock:
            if not SYNC_CHECKPOINT_FILE.exists():
                return True
            # ⚠️ 捕获面必须含 ``UnicodeDecodeError``（Codex round-3 HIGH-1，已复现）：
            # 它是 ``ValueError`` 的子类，**既不是** ``OSError`` **也不是**
            # ``json.JSONDecodeError`` —— 初版的 ``except (JSONDecodeError, OSError)``
            # 接不住它。checkpoint 文件只要有一个 ``b"\\xff"``，异常就会一路逃出
            # 本函数 → ``before_rotate()`` → ``append_failed_writes_bounded``，
            # 被 ``_flush_pending_failed_writes`` 的 ``except ... ValueError`` 接住，
            # 而它的 ``finally`` 会 ``clear()`` 掉 pending ⇒ **一整批合法待写记录消失**。
            # 单条 outbox 那条路径（只 ``except OSError``）则让异常整个逃逸。
            try:
                data = json.loads(SYNC_CHECKPOINT_FILE.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError, OSError):
                # 文件本身不可信 ⇒ 整个删掉，目的（让旧游标失效）同样达成。
                SYNC_CHECKPOINT_FILE.unlink(missing_ok=True)
                return True
            if not isinstance(data, dict) or "failed_writes" not in data:
                return True
            data.pop("failed_writes", None)
            if data:
                # ⚠️ **别的键**里可能带着不可编码的内容（合法 JSON 的 ``"\\ud800"``
                # 解出来就是孤立代理），``write_text`` 会抛 ``UnicodeEncodeError``
                # —— 同样是 ``ValueError`` 子类、同样会走到上面那条丢批路径。
                # 先按原风格写；编不出来就退回 ``ensure_ascii=True``（把这些码点
                # 转义成 ASCII，**保住其余链的游标**）；再不行才整个删掉。
                tmp = SYNC_CHECKPOINT_FILE.with_suffix(".t6c-tmp")
                try:
                    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                except (UnicodeEncodeError, TypeError, ValueError):
                    try:
                        tmp.write_text(json.dumps(data, ensure_ascii=True, indent=2), encoding="utf-8")
                    except Exception:  # noqa: BLE001 — 见上：宁可全删也不能让异常逃逸
                        SYNC_CHECKPOINT_FILE.unlink(missing_ok=True)
                        return True
                tmp.replace(SYNC_CHECKPOINT_FILE)
            else:
                SYNC_CHECKPOINT_FILE.unlink(missing_ok=True)
            logger.info("[T6-C] 活动文件将换代, 已作废 failed_writes 回灌游标")
            return True
    except Exception as e:  # noqa: BLE001 — 本函数**绝不能抛**：它在追加路径上，
        # 抛出去就会把一整批待写记录连同 pending 一起送进调用方的 finally clear()。
        logger.error("[T6-C] 作废回灌游标失败, 本次不轮转: %s", e)
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
        rotate_if_over_limit(file_path, limit, keep, before_rotate=_invalidate_replay_checkpoint)
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
