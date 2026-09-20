# Story 38.6: Shared constants for failed writes fallback mechanism.
#
# Centralised here to avoid DRY violation (previously duplicated in
# agent_service.py and memory_service.py) and to provide a single lock
# that both the writer (_record_failed_write) and reader/recovery
# (recover_failed_writes, load_failed_scores) can share.
import json
import logging
import threading
import time
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

# --- 回灌窗口上限（CARD-STAGING-WRITERS-BOUNDED / P2-B）---
#
# 回灌窗口开着时写侧不轮转（见 _replay_in_flight）。原先这个「开着」没有时间
# 上限：回灌协程被 cancel 不干净 / 某条 await 永不返回 ⇒ 锁恒 locked ⇒ 写侧上限
# **无限期**关闭。30 分钟是按 failed_writes 的 10000 行上限逐条 await 重放的量级
# 估的（⚠️ 未在现网实测，见本卡验收单「本卡未证明什么」）；要改用 env 调，
# 不改代码。坏值经 bound_from_env 退回默认并告警，不让进程导入期崩。
REPLAY_WINDOW_MAX_SECONDS: int = bound_from_env("CLS_REPLAY_WINDOW_MAX_SECONDS", 1800, minimum=1)


def _replay_in_flight() -> bool:
    """回灌窗口是否开着（开着就**不许轮转**）。

    ⛔ 这是本卡最危险的一处交互，独立复核（workflow 对抗性复核 2026-09-15，
    Codex round-1 未发现）实地复现：

    ``fallback_sync_service._sync_failed_writes`` 的链是
    「持 ``failed_writes_lock`` 读快照 → **放锁** 逐条 await 重放
    → 重新持锁 finalize」，而 finalize 判断「重放期间有没有新追加」用的是
    **长度比较 + 位置切片**::

        # fallback_sync_service._sync_failed_writes 的 finalize 段
        if len(current_lines) > len(lines):
            new_lines = current_lines[len(lines):]

    ⚠️ 本段一律**按符号名**指位，不写 ``fallback_sync_service.py:NNN``
    （车道自审 2026-09-19）：本卡自己往那个文件插了 26 行，旧 docstring 里的
    行号已整体顶掉、逐条指向不相干的代码。

    该判据的前提是**活动文件只增不减**（``_sync_failed_writes`` 自己的注释写着这条契约）。
    本卡是第一个让它**变短**的写者：窗口内一旦轮转，活动文件被 rename 走、
    新文件只剩刚写的 k 条 ⇒ ``len(current) < len(lines)`` ⇒ ``new_lines=[]`` ⇒
    窗口内新写的条目要么被 ``_atomic_write_file`` 整份覆盖销毁，要么在
    merged 为空时被 ``_rotate_file`` 改名成 ``.synced.<ts>``——**谎称已回灌**，
    再由 30 天 retention 删掉。触发不需要多线程：``_record_structured_outbox``
    的调用方是 async 的 ``record_knowledge_entity``，重放循环里的 await 就是交错点。

    ``fallback_sync_service.py`` 在 T6-C 是**禁改**面，所以修在写侧：回灌窗口
    开着就跳过轮转。上限因此是 best-effort（回灌期间可越限）。
    ⚠️ **「但不丢数据」这句在 P2-B 之后不再无条件成立**（Codex r3 更正）：
    本函数新增的超时分支到期后会放行轮转，那条路径上窗口内的新条目仍可能被
    finalize 覆盖或错标 —— 见下面「超时放行轮转本身带回了一条丢记录的路径」那条 ⚠️。
    没有超时到期时，原来的判断仍然成立。

    实现说明：
    - 惰性 import —— ``fallback_sync_service:22`` 模块级 import 本模块，
      顶层反向 import 会成环。
    - ``asyncio.Lock.locked()`` 只读一个 bool，同步代码里调用不 await、不死锁。
    - **非超时**分支下读到 True/False 的任一竞态都安全：调用方全程持
      ``failed_writes_lock``，而回灌取快照也要先拿这把锁 ⇒ 「看到 False 于是轮转」
      时窗口必然尚未打开或已关闭，没有可被破坏的快照。
      ⚠️ **超时分支不适用这条**（Codex r2 MEDIUM）：那里返回 False 的含义是
      「窗口开着，但开得太久，按挂住处理」—— 快照可能正活着，见下面那条 ⚠️。
    - import 不到 / 属性不在（精简部署、测试替身）⇒ 本函数视作「没有回灌」。
      ⚠️ 但**净效果不是「退回有界行为」**（Codex round-3 LOW-5 指出初版这句
      失真，已更正）：同一个 import 失败会让
      :func:`_invalidate_replay_checkpoint` 返回 False，而它是轮转的前置动作，
      于是实际结果是**永不轮转**（满额后一直裸追加）。方向仍然安全——
      宁可越限也不丢数据——但它是「停掉上限」而不是「维持上限」，
      别按字面理解成后者。持续的权限故障同样会让越限无限持续。

    超时语义（CARD-STAGING-WRITERS-BOUNDED / P2-B）—— 三态：

    ===================================  ==========================================
    ``_sync_all_lock`` / 时间戳           返回
    ===================================  ==========================================
    未 locked                             ``False``（窗口关着，照常轮转）
    locked 且时间戳为 ``None``             ``True``（**直接**持锁者，无时长可比 ⇒ 保守）
    locked 且已超 REPLAY_WINDOW_MAX_SECONDS  ``False`` + ``logger.error``（视作挂住）
    locked 且未超上限                      ``True``
    ===================================  ==========================================

    改前只有 ``locked()`` 这一个布尔位、**没有时间维度**：回灌协程被 cancel 不
    干净、事件循环挂起、某条 ``await`` 永不返回 ⇒ 锁永远 locked ⇒ 每次追加都走
    「只追加不轮转」分支 ⇒ 写侧上限**无限期**关闭。超时给这个布尔位补上时间维度。

    ⚠️ **不要把它读成「上限至多失效 N 秒」**（Codex r1 MEDIUM 指出初版这句过强）。
    超时只覆盖「经 :meth:`sync_all_fallbacks` 打过时间戳」这一种持锁。其余三条
    路径上越限仍可无限持续：① 直接持锁者（时间戳为 ``None``）无论持续多久都判
    窗口开着；② 轮转本身持续失败（权限等）时调用方仍会继续追加；
    ③ import 不到本模块依赖时 :func:`_invalidate_replay_checkpoint` 同样返回 False，
    净效果是**永不轮转**（见上一段）。

    ⚠️ **超时放行轮转本身带回了一条丢记录的路径**（Codex r1 HIGH，如实登记，
    移交 P2-C REPLAY-REWRITE）：超时到期后本函数放行轮转，而此时回灌若**确实**
    还在跑（只是慢，不是挂住），``fallback_sync_service._sync_failed_writes``
    finalize 的「只增不减」判据（``if len(current_lines) > len(lines)``）会因为
    活动文件**变短**而算出 ``new_lines=[]``，于是窗口内新写的条目要么被
    ``_atomic_write_file`` 整份覆盖，要么在 merged 为空时被 ``_rotate_file`` 改名
    成 ``.synced.``（谎称已回灌）。改前的「锁着就永不轮转」把这条路径堵死了，
    本函数为了换回「有界」把它重新打开了一条缝 —— 这是**本卡引入的取舍**，
    不是回灌算法的旧账。``_invalidate_replay_checkpoint`` 只作废游标，**挡不住**
    这次 finalize。真正的修法是让 finalize 变成 generation-aware（或让超时路径把
    新条目写进旁路文件而不缩短活动文件），两者都要动回灌侧，是 P2-C 的面。
    在 P2-C 落地前，调高 ``CLS_REPLAY_WINDOW_MAX_SECONDS`` 可以缩小这条缝。

    ⚠️ **超时还带回了第二条、后果更重的路径：游标复活**（车道自审 2026-09-19，
    与上面那条是**不同**的因果链，一并移交 P2-C）。轮转的前置动作
    :func:`_invalidate_replay_checkpoint` 作废游标，靠的是「换代与游标失效同生共死」
    这条不变量；而改前 ``_replay_in_flight`` 在整次回灌期间恒 True，轮转根本
    不可能与重放循环重叠 —— 这条不变量是**靠构造**保证的。超时把这个前提拿掉了：
    轮转发生后，仍在跑的重放循环**可能**在下一个 checkpoint 间隔重新 ``_save_checkpoint``，
    把一个属于**上一代文件**的下标重新绑到新一代活动文件上。
    ⚠️ 两处限定（Codex r4 更正初版表述过强）：① 重新保存**不是必然**的 ——
    还要满足「连续成功前缀推进过」这个条件；② 若进程在 finalize 的
    ``_clear_checkpoint`` 之前退出（本函数 docstring 自己列为动机的 kill 场景），
    重启后新一代 ``failed_writes.jsonl`` 里**下标小于复活游标**的那些会被
    ``if i < checkpoint_idx: continue`` 跳过 —— 新代行数 ≤ 复活游标时就是**整份**跳过，
    此时还会因 still_pending 为空而被 ``_rotate_file`` 改名成 ``.synced.``。
    写侧挡不住它（游标是回灌侧自己写回的），修法同样在 P2-C。

    ⚠️ 时间戳只有走 :meth:`fallback_sync_service.FallbackSyncService.sync_all_fallbacks`
    才会被打上。直接 ``async with _sync_all_lock:`` 的持锁者（既有真锁门
    test_dead_letter_bounded_t6c.py::test_no_rotation_while_replay_window_open、
    测试替身）看到的是 ``None``，按上表仍判「窗口开着」—— 超时不得把它翻红。
    """
    # ⚠️ 这两处必须写成 ``from app.services.fallback_sync_service import X`` 这种
    # **点分模块名**形式（车道自审 2026-09-19）：既有两条常驻门
    # （test_dead_letter_bounded_t6c.py 的 test_replay_probe_falls_back_to_bounded_when_unobservable
    # 与 test_unobservable_replay_state_stops_rotation_not_bounding_claim）
    # 是靠 ``builtins.__import__`` 拦 ``name == "app.services.fallback_sync_service"``
    # 来模拟「观测不到回灌状态」的。改成 ``from app.services import fallback_sync_service``
    # 之后 ``name`` 变成 ``"app.services"``，两条门就拦不住了 —— 它们会照常变绿，
    # 但绿在「锁本来就没被占」这条完全不同的判据上。
    try:
        from app.services.fallback_sync_service import _sync_all_lock
    except Exception:  # noqa: BLE001 — 观测不到回灌状态时返回 False；净效果见 docstring
        return False
    try:
        if not _sync_all_lock.locked():
            return False
    except Exception:  # noqa: BLE001 — 同上
        return False

    # 锁着 —— 再问「占了多久」。属性不在（精简部署 / 测试替身）当作 None 处理：
    # 没有时间戳就没有「超时」可言，只能保守地认为窗口开着。
    try:
        from app.services.fallback_sync_service import _sync_all_started_at
    except Exception:  # noqa: BLE001 — 属性/模块不在 ⇒ 当作没有时间戳
        started_at = None
    else:
        started_at = _sync_all_started_at
    if started_at is None:
        return True

    elapsed = time.monotonic() - started_at
    if elapsed > REPLAY_WINDOW_MAX_SECONDS:
        logger.error(
            "[C2-01] 回灌窗口已持锁 %.0f s 超过上限 %d s, 视作挂住, 恢复写侧上限",
            elapsed,
            REPLAY_WINDOW_MAX_SECONDS,
        )
        return False
    return True


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
            # ⚠️ 这是本卡**第三处**同型缺陷（Codex round-4 HIGH-1）：前两处
            # （``count_lines`` / ``_backlog_entry``）在 round-2 已经改掉了
            # ``Path.exists()``，这一处漏了 —— 「修完一处没有立刻扫同型第二处」。
            # 3.14 的 ``exists()`` 把 ``PermissionError`` / 瞬时 ``EIO`` 一律吞成
            # False，于是「探测失败」被当成「本来就没有游标」⇒ 直接返回 True ⇒
            # **允许换代，而旧游标原封不动留着** —— 故障恢复后它就会关联到新一代
            # 文件上，正是 round-2 H1 要堵的那个洞从另一个入口回来了。
            # 探测不出来 ⇒ 返回 False（不轮转），与本函数其余失败分支同口径。
            try:
                SYNC_CHECKPOINT_FILE.stat()
            except FileNotFoundError:
                return True
            except OSError as e:
                logger.error("[T6-C] 探测回灌游标失败, 本次不轮转: %s", e)
                return False
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


def ensure_line_boundary(file_path: Path) -> bool:
    """活动文件若以**半行**结尾，补一个换行。补过（或本来就不需要）返回 True。

    CARD-STAGING-WRITERS-BOUNDED (P2-B, Codex r2 HIGH)：追加式 JSONL 在
    ``ENOSPC`` / ``EIO`` 下可能写到一半就抛出去，活动文件因此以残缺 JSON 结尾
    （如 ``{"episo``）。调用方随后**重试**同一批时，新记录会直接接在残缺尾巴
    后面，粘成 ``{"episo{"episode_id":"A"}`` 这样一行 —— 重试的那条记录被吞掉，
    而调用方看到「这次成功了」于是把它从 pending 里删掉：**表面重试成功、实则丢失**。
    先补一个 ``\n``，残缺尾巴就自成一行（回灌侧按行解析时跳过它），重试的记录
    落在下一行、完好可读。

    ⚠️ 调用方必须已持 ``failed_writes_lock``（与 :func:`append_failed_writes_bounded`
    同口径，本函数不取锁）。

    ⚠️ **返回值的含义是「知不知道」，不是「要不要写」**：

    - ``True``  = **已知**落在行边界上（文件不存在 / 空 / 以 ``\n`` 结尾 / 刚补上）。
    - ``False`` = **不能确定**落在行边界上 —— 包含两种：已确认有半行但补不上，
      以及**探测本身失败**（权限 / EIO，此时根本不知道有没有半行）。

    调用方据此只决定**要不要加分隔符**，**绝不据此拒写**（Codex r4 MEDIUM）：
    探测失败时若拒写，活动文件**可写但不可读**（``chmod 0222`` / ACL / EIO）就会让
    ``_flush_pending_failed_writes`` **永远**刷不出去、``_pending_failed_writes``
    无界增长、连 ``cleanup()`` 也再写不掉 —— 而**改动前**同样的批次是能落盘的
    （``rotate_if_over_limit`` 与 ``append_failed_writes_bounded`` 都刻意吞掉了那次读失败，
    见本文件 room 计算处的注释「宁可暂时越限，也不丢死信」）。
    代价是：探测失败时会多写一个空行（读侧按行解析时跳过），换来的是**任何情况下都不粘连**。

    行数口径不受影响：:func:`failure_counters.count_lines` 对「末行没有换行符」本来就按一行计。
    """
    try:
        with open(file_path, "rb") as fh:
            fh.seek(0, 2)
            if fh.tell() == 0:
                return True
            fh.seek(-1, 2)
            if fh.read(1) == b"\n":
                return True
    except FileNotFoundError:
        return True
    except OSError as e:
        # 探不出来 ⇒ 返回 False（= 「不能确定在行边界上」）。调用方会加一个分隔符，
        # 但**照常追加** —— 不拒写。Codex r4 MEDIUM：初版在这里返回 True，于是
        # 「探测失败 + 实际有半行 + 追加成功」这条路径仍会粘连（该缺陷 PREV 也有，
        # 属修复遗漏，不是新增回归）。
        logger.warning("[P2-B] 探测半行尾巴失败, 本次加分隔符后照常追加 %s: %s", file_path, e)
        return False

    try:
        with open(file_path, "a", encoding="utf-8") as fh:
            fh.write("\n")
    except OSError as e:
        logger.warning("[P2-B] 补换行失败, 本次照常追加 %s: %s", file_path, e)
        return False
    logger.warning("[P2-B] 活动文件以半行结尾（上次追加中途失败）, 已补换行: %s", file_path)
    return True


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
    （``memory_service._record_structured_outbox`` /
    ``memory_service._flush_pending_failed_writes`` /
    ``agent_service._record_failed_write``），
    所以「核行数 → 轮转 → 追加」对**进程内**全部写者原子。

    ⚠️ ``file_path`` 是**显式入参**而不是读本模块的 ``FAILED_WRITES_FILE``
    全局。这是必须的：既有测试打桩的是**导入方**的绑定副本
    （``app.services.memory_service.FAILED_WRITES_FILE``，见
    test_a7_honest_failure.py:108/142、test_story_30_24_boundary.py:551/583/622），
    若这里改读本模块全局，那些打桩会全部失效 —— 测试会把条目写进现网
    ``backend/data/failed_writes.jsonl``，而且多半仍然显示绿（假绿）。

    ⚠️ CARD-STAGING-WRITERS-BOUNDED（P2-B）起，``agent_service._record_failed_write``
    这个第三写者**也经本函数**了（T6-C 时它还是裸追加，只持锁、不核上限）。
    ``failed_writes.jsonl`` 的进程内写者因此全部有界。但不变量的准确表述仍然是
    「经本函数的追加，追加后活动文件 ≤ max_lines」，**不是**
    「failed_writes.jsonl 恒 ≤ max_lines」。三条限定（Codex round-1 L1 指出初版
    表述过强，这里逐条收紧；第 1 条在 P2-B 按新事实重述）：

    1. 越限**仍可无限持续**（Codex r2 MEDIUM 更正：初版写「只是不再无限期」过强）——
       超时只覆盖三条路径里的第一条，另外两条没有任何时间上限：
       ① 回灌窗口开着时本函数**只追加不轮转**（见 ``_replay_in_flight``）。
       只有「经 ``sync_all_fallbacks`` 打过时间戳」的那种持锁才受
       ``REPLAY_WINDOW_MAX_SECONDS`` 约束；**直接持锁者**（时间戳为 ``None``，
       如测试替身或未来新增的直接持锁点）无论持续多久都判窗口开着；
       ② 轮转失败（权限等）时调用方仍会继续追加（见
       ``failure_counters.rotate_if_over_limit`` 的 Returns 段）；
       ③ **跨进程**并发写同一文件不在本锁覆盖面内（进程内锁盖不住多进程部署）。
    2. 「每个 ``.overflow.*`` 都 ≤ max_lines」**不成立**：活动文件在进入本函数
       前就已超限时（旁路突发），被**整体**轮转走的那一份就 > max_lines。
       成立的是「本函数**自己写出**的每一段 ≤ max_lines」。
    3. 「一条不丢」的条件是
       **活动文件原有行数 + 单批条数 ≤ max_lines × (max_rotations + 1)**。
       ⚠️ Codex round-4 MEDIUM 更正：初版漏了「原有行数」这一项，只写单批条数。
       实测反例（``L=5, K=1``）：空文件追加 7 条 → 全保留；**原有 4 行**再追加
       同样 7 条 → 本批的 ``new0`` 被删（第一份 overflow 装的是旧 4 行 + ``new0``，
       第二次轮转把它挤掉了）。12 组探针里「原有 + 单批 ≤ L×(K+1)」全部命中，
       只按单批判会在 3 组上给出错误的「不丢」结论。

    Args:
        file_path: 活动 JSONL 文件
        lines: 已序列化好的 JSON 字符串（不带换行）。序列化留在调用方，
            这样 ``json.dumps`` 的 TypeError/ValueError 仍由调用方原有的
            except 子句处理，异常语义不变。
        max_lines / max_rotations: 省略则取模块级常量（**调用时**读取，
            因此 ``monkeypatch.setattr`` 本模块常量对本函数生效）。
    """
    # Codex r3 HIGH: 在**三个写者共用的入口**补行边界，而不是只在会重试的那个调用方
    # 里补 —— 否则「A 写到半行失败 → B（agent_service / _record_structured_outbox，
    # 都不重试）追加」这条路径上，B 的记录会粘在 A 的残缺尾巴后面。
    #
    # 返回 False = 「**不能确定**落在行边界上」（确认有半行且补不上，或探测本身失败）。
    # 此时**不能拒写**（那两个写者没有重试缓冲，拒写 = 直接丢），改成把分隔符并进本次写入
    # 的**第一行** —— 一次 open 写完，既不多一次 IO，也不会粘连。
    sep = "" if ensure_line_boundary(file_path) else "\n"

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
                f.write(sep + line + "\n")
                sep = ""
        return

    # 分批写。``_flush_pending_failed_writes`` 一次可以交来**比上限还多**的条目，
    # 「追加前核一次行数」对这种单批就超限的情况完全无效（核的时候文件是空的，
    # 不轮转，然后一口气写 N 条 > 上限）。所以边写边留出空间：写满一段就轮转，
    # 再接着写下一段 —— 本函数写出的每一段都 ≤ limit（限定见 docstring 三条）。
    pending = list(lines)
    while pending:
        if rotate_if_over_limit(file_path, limit, keep, before_rotate=_invalidate_replay_checkpoint):
            # Codex r4 LOW: 真轮转过 ⇒ 新活动文件是**空的**，分隔符必须清掉。
            # 否则「补换行失败 + 随后轮转成功」这条组合会往新文件先写一个空行，
            # 首段变成 max_lines + 1 行。
            sep = ""
        room = len(pending)
        if limit > 0:
            try:
                room = limit - count_lines(file_path)
            except OSError as e:
                # Codex round-1 M1: 活动文件**可写但不可读**时（父目录 w+x 但文件
                # 不可读），rotate_if_over_limit 已经吞下了它那次读失败并返回
                # False，若这里再让 count_lines 抛出去，追加就整个不发生 ——
                # 比改动前的裸追加更糟，而且批量路径
                # (_flush_pending_failed_writes) 会在成功后删掉本批 pending
                # （P2-B 前是无条件 finally clear()），条目直接消失。
                # 数不出行数就退化成「一次写完」：
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
                f.write(sep + line + "\n")
                sep = ""
