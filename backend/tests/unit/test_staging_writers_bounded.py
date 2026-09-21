"""CARD-STAGING-WRITERS-BOUNDED (P2-B, BATCH-2026-09-18-第十五批) — 暂存 JSONL 剩余无界写者收口。

先红后绿门。改前的五个缺陷面：

1. ``agent_service._record_failed_write`` 是 ``failed_writes.jsonl`` 的**第三个**写者，
   裸 ``open(..., "a")`` 追加，不经 ``append_failed_writes_bounded``（T6-C 只切了
   memory_service 两处）⇒ 只要这条路径在写，上限就形同虚设。
2. ``failed_writes_constants._replay_in_flight`` 只读 ``_sync_all_lock.locked()``，
   **无时间维度** ⇒ 回灌协程被 cancel 不干净 / 某条 await 永不返回时，锁恒 locked，
   写侧上限**无限期**关闭。
3. ``MemoryService._pending_failed_writes`` 只在 ``cleanup()`` 刷盘 ⇒ 进程被 kill
   或崩溃 = 从未调 cleanup = 整批失败记录消失。
4. ``DeadLetterStore.store`` 裸追加 ⇒ 无上限、无轮转。（``EventBus._write_outbox``
   同型，但 e3 子项已按卡文退回第十六批，见本卡验收单；本文件不再覆盖它。）
5. ``Path.exists()`` 在 Python 3.14 把 ``PermissionError`` **吞成 False** ⇒
   「读不到」与「不存在」不可区分：``overflow_siblings`` 静默返回空、
   ``_unique_overflow_target`` 交出一个可能已被占用的名字（``rename`` POSIX 下静默
   覆盖 = 丢整份 overflow）、``DeadLetterStore.count`` 把读不到压成 0。

⛔ 硬边界：本文件**所有**路径一律 ``monkeypatch`` / ``tmp_path``，不触碰现网
``backend/data/**``，不连 7691/7687（本文件零连库）。**被测写者本身不打桩**（DD-03）
—— 唯一的替身在 Neo4j 客户端边界（``record_episode``），被测对象是刷盘时机与文件 IO。

⚠️ 计数口径：本文件数行一律 ``read_bytes().count(b"\\n")``，与生产 ``count_lines``
逐字节同口径。**不用 ``splitlines()``** —— 它会在 U+2028 / U+2029 处额外切行，
与生产计数不同口径，会让门的真值随条目内容漂移。
"""

from __future__ import annotations

import ast
import json
import os
import pathlib
import time
from typing import Any, Dict, List, Set
from unittest.mock import AsyncMock, MagicMock

import pytest

import app.core.failed_writes_constants as fwc
import app.core.failure_counters as fc

# 与生产默认值无关的小值：门只验「阈值触发」这个行为，不验具体默认值。
MAX_LINES = 5
MAX_ROTATIONS = 3
# 守卫超时门用的窗口上限（秒）。同样与生产默认 1800 无关。
REPLAY_WINDOW = 60


# ═══════════════════════════════════════════════════════════════════════════
# 计数 / 枚举工具（与生产同口径）
# ═══════════════════════════════════════════════════════════════════════════


def _nlines(path) -> int:
    """按 b"\\n" 数行——与生产 ``count_lines`` 同口径。"""
    if not path.exists():
        return 0
    return path.read_bytes().count(b"\n")


def _overflow_siblings(path):
    """活动文件的 ``.overflow.*`` 兄弟（按名字排序 == 按时间排序）。"""
    if not path.parent.exists():
        return []
    return sorted(p for p in path.parent.iterdir() if p.name.startswith(path.stem) and ".overflow." in p.name)


def _records(path) -> List[Dict[str, Any]]:
    """读一份 JSONL 的全部记录（文件不在 ⇒ 空）。"""
    if not path.exists():
        return []
    out: List[Dict[str, Any]] = []
    for raw in path.read_bytes().decode("utf-8").split("\n"):
        if raw.strip():
            out.append(json.loads(raw))
    return out


def _identity_union(path, field: str) -> Set[str]:
    """活动文件 + 全部 overflow 兄弟里该字段的取值并集。

    ⚠️ 有界门必须按**身份**判「一条不丢」，不是按数量：等长替换（丢一条、
    重复另一条）在数量判据下恒绿。
    """
    seen: Set[str] = set()
    for f in [path, *_overflow_siblings(path)]:
        for rec in _records(f):
            seen.add(str(rec[field]))
    return seen


# ═══════════════════════════════════════════════════════════════════════════
# fixtures —— 每条链各自把路径与上限指向 tmp_path
# ═══════════════════════════════════════════════════════════════════════════


def _isolate_live_checkpoint(monkeypatch, tmp_path):
    """⛔ 隔离现网回灌 checkpoint。

    failed_writes 轮转的**前置动作**（``_invalidate_replay_checkpoint``）会
    删/改 ``SYNC_CHECKPOINT_FILE``。只隔离数据文件的话，任何触发轮转的用例都会
    去动现网 ``backend/data/sync_checkpoint.json``，而且该文件不存在时测试照样绿
    —— 结果悄悄依赖真实磁盘状态（T6-C Codex round-3 HIGH-2 的同型坑）。
    """
    import app.services.fallback_sync_service as _fss

    monkeypatch.setattr(_fss, "SYNC_CHECKPOINT_FILE", tmp_path / "sync_checkpoint.json")


@pytest.fixture
def bounded_agent_writes(monkeypatch, tmp_path):
    """第三写者（agent_service）侧的上限与路径全指向 tmp_path。

    ⚠️ 打桩 ``app.services.agent_service.FAILED_WRITES_FILE``（**导入方**的模块级
    绑定副本）而不是 ``fwc.FAILED_WRITES_FILE``：既有测试
    （test_story_38_7_ac4_degraded_mode.py:95 / test_story_38_7_qa_supplement.py:233,275
    / test_qa_38_6_scoring_reliability_extra.py:58,83）打的就是这一侧，生产实现必须
    继续从这一侧取路径，否则那些测试会静默写进现网 backend/data/failed_writes.jsonl
    且仍然显示绿（假绿）。

    ``raising=False`` 用于上限常量：让改前的红落在行为断言上，而不是 AttributeError
    （否则负控把实现改回裸追加时会红在同一个 AttributeError 上，负控失去鉴别力）。
    """
    import app.services.agent_service as _ags

    monkeypatch.setattr(fwc, "FAILED_WRITES_MAX_LINES", MAX_LINES, raising=False)
    monkeypatch.setattr(fwc, "FAILED_WRITES_MAX_ROTATIONS", MAX_ROTATIONS, raising=False)
    path = tmp_path / "failed_writes.jsonl"
    monkeypatch.setattr(_ags, "FAILED_WRITES_FILE", path)
    _isolate_live_checkpoint(monkeypatch, tmp_path)
    return path


@pytest.fixture
def bounded_memory_writes(monkeypatch, tmp_path):
    """memory_service 侧的 failed_writes 上限与路径指向 tmp_path（同 T6-C 口径）。"""
    import app.services.memory_service as _ms

    monkeypatch.setattr(fwc, "FAILED_WRITES_MAX_LINES", MAX_LINES, raising=False)
    monkeypatch.setattr(fwc, "FAILED_WRITES_MAX_ROTATIONS", MAX_ROTATIONS, raising=False)
    path = tmp_path / "failed_writes.jsonl"
    monkeypatch.setattr(_ms, "FAILED_WRITES_FILE", path)
    _isolate_live_checkpoint(monkeypatch, tmp_path)
    return path


@pytest.fixture
def bounded_dead_letter_episodes(monkeypatch, tmp_path):
    """episode 死信上限指向小值，路径由调用方显式传 tmp_path。"""
    monkeypatch.setattr(fc, "DEAD_LETTER_MAX_LINES", MAX_LINES, raising=False)
    monkeypatch.setattr(fc, "DEAD_LETTER_MAX_ROTATIONS", MAX_ROTATIONS, raising=False)
    _isolate_live_checkpoint(monkeypatch, tmp_path)
    return tmp_path / "dead_letter_episodes.jsonl"


@pytest.fixture
def service():
    """不跑 ``__init__`` 的 MemoryService 壳 —— 只用来驱动同步写者（同 T6-C）。"""
    import app.services.memory_service as _ms

    svc = _ms.MemoryService.__new__(_ms.MemoryService)
    svc._initialized = True
    svc._episodes = []
    svc._pending_failed_writes = []
    return svc


# ═══════════════════════════════════════════════════════════════════════════
# (c) 第三写者 —— agent_service._record_failed_write 切有界 helper
# ═══════════════════════════════════════════════════════════════════════════


def test_agent_service_third_writer_is_bounded(bounded_agent_writes):
    """改前必红：agent_service 裸追加 ⇒ 活动文件 8 行、零 overflow。

    断言按**身份**核「一条不丢」：8 个 concept_id 必须全部在
    「活动文件 ∪ overflow 兄弟」里。
    """
    import app.services.agent_service as _ags

    path = bounded_agent_writes
    total = MAX_LINES + 3

    for i in range(total):
        _ags._record_failed_write(
            event_type="score_recorded",
            concept_id=f"c{i}",
            canvas_name="Math/test.canvas",
            score=float(i),
            error_reason="neo4j down",
        )

    assert _nlines(path) <= MAX_LINES, (
        f"活动文件超行数：{_nlines(path)} > {MAX_LINES} —— 第三写者仍是裸追加，写侧上限对它无效"
    )
    assert _overflow_siblings(path), "没有 .overflow.* —— 从未发生轮转"
    assert _identity_union(path, "concept_id") == {f"c{i}" for i in range(total)}, "轮转丢了条目"


def test_third_writer_does_not_concatenate_onto_dangling_tail(bounded_agent_writes):
    """别人留下的半行不得把**第三写者**的新记录吞掉（Codex r3 HIGH 的第二半）。

    ``agent_service._record_failed_write`` 没有重试缓冲：它写出去就删不回来，
    所以粘连对它等于**直接丢**。行边界修复必须在三个写者共用的入口
    （``append_failed_writes_bounded``）上，而不是只在会重试的那个调用方里。
    """
    import app.services.agent_service as _ags

    path = bounded_agent_writes
    path.write_bytes(b'{"episo')  # 上一个写者写到一半就失败了

    _ags._record_failed_write(
        event_type="score_recorded",
        concept_id="after-dangling",
        canvas_name="Math/test.canvas",
        score=1.0,
        error_reason="neo4j down",
    )

    raw_lines = [ln for ln in path.read_bytes().decode("utf-8").split("\n") if ln.strip()]
    parsed = []
    for ln in raw_lines:
        try:
            parsed.append(json.loads(ln))
        except json.JSONDecodeError:
            pass

    assert raw_lines[0] == '{"episo', f"残缺尾巴没有自成一行 —— 和第三写者的新记录粘在一起了: {raw_lines[0]!r}"
    assert any(r.get("concept_id") == "after-dangling" for r in parsed), (
        f"第三写者的记录被半行尾巴吞掉了（它没有重试缓冲 = 直接丢）: {path.read_bytes()!r}"
    )


# ═══════════════════════════════════════════════════════════════════════════
# (d) 回灌窗口守卫超时 —— 三态：unlocked / 直接持锁(None) / stale
#
# 全部用**真实的** ``_sync_all_lock``，不打桩 ``locked()`` —— 打桩只能证明
# 「我写的判断会被调用」，证明不了它读的是回灌侧真正在用的那把锁。
# 驱动写者用 ``_record_structured_outbox``（memory_service 侧，T6-C 已切 helper），
# 这样负控①（把 agent_service 换回裸追加）对这三条门**不产生影响**，
# 负控①的鉴别力才只绑第三写者。
# ═══════════════════════════════════════════════════════════════════════════


async def test_replay_guard_times_out_when_lock_stuck(service, bounded_memory_writes, monkeypatch):
    """改前必红：锁被挂住（持锁时刻远早于上限）时仍判「窗口开着」⇒ 永不轮转。

    ``raising=False``：改前 ``REPLAY_WINDOW_MAX_SECONDS`` / ``_sync_all_started_at``
    都还不存在，先设上去，红才会落在「未轮转」这个行为断言而不是 AttributeError。
    """
    import app.services.fallback_sync_service as fss

    path = bounded_memory_writes
    monkeypatch.setattr(fwc, "REPLAY_WINDOW_MAX_SECONDS", REPLAY_WINDOW, raising=False)

    async with fss._sync_all_lock:
        monkeypatch.setattr(
            fss,
            "_sync_all_started_at",
            time.monotonic() - (fwc.REPLAY_WINDOW_MAX_SECONDS + 5),
            raising=False,
        )
        for i in range(MAX_LINES + 3):
            assert service._record_structured_outbox({"kind": "knowledge_entity", "i": i})

    assert _overflow_siblings(path), "锁挂住超过上限后仍未轮转 —— 守卫没有时间维度，写侧上限被无限期关闭"


async def test_replay_guard_respects_fresh_window(service, bounded_memory_writes, monkeypatch):
    """对照输入：同样持锁，但持锁时刻是**刚刚** ⇒ 仍在窗口内，绝不轮转。

    没有这条，上面那条门用「永远轮转」也能变绿。
    """
    import app.services.fallback_sync_service as fss

    path = bounded_memory_writes
    total = MAX_LINES + 3
    monkeypatch.setattr(fwc, "REPLAY_WINDOW_MAX_SECONDS", REPLAY_WINDOW, raising=False)

    async with fss._sync_all_lock:
        monkeypatch.setattr(fss, "_sync_all_started_at", time.monotonic(), raising=False)
        for i in range(total):
            assert service._record_structured_outbox({"kind": "knowledge_entity", "i": i})

    assert _overflow_siblings(path) == [], "窗口新鲜却发生了轮转 —— finalize 的「只增不减」判据会被打破"
    assert _nlines(path) == total, "窗口内的条目丢了"


async def test_replay_guard_treats_direct_lock_holder_as_in_flight(service, bounded_memory_writes, monkeypatch):
    """对照输入：**直接持锁**（没有经过 ``sync_all_fallbacks``，无时间戳）仍判窗口内。

    这是既有真锁门 test_dead_letter_bounded_t6c.py::test_no_rotation_while_replay_window_open
    的语义 —— 超时设计不得把它翻红：没有时间戳就没有「超时」可言，只能保守地
    认为窗口开着（宁可越限也不丢数据，方向不可反转）。
    """
    import app.services.fallback_sync_service as fss

    path = bounded_memory_writes
    total = MAX_LINES + 3
    monkeypatch.setattr(fwc, "REPLAY_WINDOW_MAX_SECONDS", REPLAY_WINDOW, raising=False)
    monkeypatch.setattr(fss, "_sync_all_started_at", None, raising=False)

    async with fss._sync_all_lock:
        for i in range(total):
            assert service._record_structured_outbox({"kind": "knowledge_entity", "i": i})

    assert _overflow_siblings(path) == [], "直接持锁者被误判成超时 —— 既有真锁门会随之翻红"
    assert _nlines(path) == total, "窗口内的条目丢了"


async def test_sync_all_fallbacks_stamps_and_clears_started_at(monkeypatch):
    """``sync_all_fallbacks`` 必须在**持锁期间**打上时间戳、退出时清空，且用的是
    **守卫读的那口时钟**。

    只测守卫读的那一侧不够：时间戳如果没人写，超时分支永远等不到 stale 值，
    整条超时语义在生产路径上是死的（门绿在「另一条路径」上）。

    ⚠️ 只断言 ``isinstance(float)`` 不够：``time.time()`` 同样是 float，但它与守卫用的
    ``time.monotonic()`` **不是同一口时钟**（在本机相差数十年）。写侧一旦换成 ``time.time()``，
    守卫算出的 ``elapsed = monotonic() - stamp`` 会变成一个巨大的**负数** ⇒ **恒不超时**，
    超时分支彻底变成死代码（Codex r4 更正：初版注释把方向写反成「恒判超时」）。
    所以要把戳和**当下的 monotonic** 对一次。
    """
    import app.services.fallback_sync_service as fss

    seen: List[Any] = []

    class _Neo4j:
        is_fallback_mode = True

    svc = fss.FallbackSyncService.__new__(fss.FallbackSyncService)
    svc._neo4j = _Neo4j()

    real_locked = fss.FallbackSyncService._sync_all_fallbacks_locked

    async def _spy(self):
        seen.append(
            {
                "stamp": getattr(fss, "_sync_all_started_at", "missing"),
                "locked": fss._sync_all_lock.locked(),
                "now": time.monotonic(),
            }
        )
        return await real_locked(self)

    monkeypatch.setattr(fss.FallbackSyncService, "_sync_all_fallbacks_locked", _spy)
    await svc.sync_all_fallbacks()

    assert seen, "spy 没被调到"
    rec = seen[0]
    assert isinstance(rec["stamp"], float), f"持锁期间没有打时间戳: {rec['stamp']!r}"
    assert rec["locked"] is True, "打戳时锁并没有被持有 —— 戳可能打在取锁之前"
    # 同一口时钟：与当下 monotonic 的差必须是「刚刚」量级。换成 time.time() 会差数十年。
    assert abs(rec["now"] - rec["stamp"]) < 5.0, (
        f"时间戳与守卫用的 time.monotonic() 不是同一口时钟: 差 {rec['now'] - rec['stamp']:.0f} s"
    )
    assert getattr(fss, "_sync_all_started_at", "missing") is None, "退出后时间戳没清空"


async def test_started_at_is_not_stamped_while_waiting_for_the_lock(monkeypatch):
    """时间戳必须在**取到锁之后**才打（Codex r4 MEDIUM 指出上一条门证不了这件事）。

    上一条门的 spy 跑在 ``_sync_all_fallbacks_locked`` **内部** —— 那时锁必然已经到手，
    所以「float / locked / 同一口时钟 / 退出清空」四项在「赋值被挪到 ``async with`` **之前**」
    的实现下**照样全绿**。这条门把前提反过来：先由别人占住锁，再启动调用，
    正确实现应当在**等锁期间一动不动**。

    这不是吹毛求疵：排队等锁的那段若也算进窗口时长，高并发下第二个等待者会把第一个的
    时间戳冲掉，守卫读到的就是一个偏早的时刻 ⇒ 提前判超时 ⇒ 提前放行轮转。
    """
    import asyncio

    import app.services.fallback_sync_service as fss

    class _Neo4j:
        is_fallback_mode = True

    svc = fss.FallbackSyncService.__new__(fss.FallbackSyncService)
    svc._neo4j = _Neo4j()

    SENTINEL = -12345.0
    monkeypatch.setattr(fss, "_sync_all_started_at", SENTINEL, raising=False)

    async with fss._sync_all_lock:
        task = asyncio.create_task(svc.sync_all_fallbacks())
        # 让它真的排到「等锁」这一步上
        for _ in range(20):
            await asyncio.sleep(0)
        await asyncio.sleep(0.05)
        assert fss._sync_all_started_at == SENTINEL, (
            f"等锁期间时间戳就被改了 —— 赋值发生在取锁之前: {fss._sync_all_started_at!r}"
        )

    await task
    assert fss._sync_all_started_at is None, "退出后时间戳没清空"


def test_no_glue_when_probe_fails_on_a_dangling_tail(service, bounded_memory_writes, monkeypatch):
    """**探测读不出来 + 实际有半行 + 追加成功** 这条组合也不得粘连（Codex r4 MEDIUM）。

    这是「不知道有没有半行」的那一支：探测失败时若按「没有半行」处理（sep 为空），
    记录就直接接在残缺尾巴后面。正确做法是按「不能确定」处理 —— 加上分隔符再写，
    代价只是文件可读时会多一个空行（读侧按行解析时跳过）。

    注入：只让该路径的**读**失败（``"b"`` 模式），写照常成功。
    """
    import app.core.failed_writes_constants as _fwc

    path = bounded_memory_writes
    path.write_bytes(b'{"episo')  # 实际有半行，但探测读不出来

    real_open = open
    probed = []

    def _boom(file, mode="r", *a, **kw):
        if str(file) == str(path) and "b" in mode:
            probed.append(1)
            raise PermissionError("EACCES")
        return real_open(file, mode, *a, **kw)

    monkeypatch.setattr(_fwc, "open", _boom, raising=False)

    service._pending_failed_writes = [{"episode_id": "blind-glue-A"}]
    service._flush_pending_failed_writes()

    assert probed, "前置不成立：探测那次读没有被注入失败"
    raw_lines = [ln for ln in path.read_bytes().decode("utf-8").split("\n") if ln.strip()]
    parsed = []
    for ln in raw_lines:
        try:
            parsed.append(json.loads(ln))
        except json.JSONDecodeError:
            pass

    assert raw_lines[0] == '{"episo', f"探测读不出来时把记录粘在了残缺尾巴上: {raw_lines[0]!r}"
    assert any(r.get("episode_id") == "blind-glue-A" for r in parsed), (
        f"记录没有成为一条可解析的行: {path.read_bytes()!r}"
    )


def test_sep_is_dropped_after_a_real_rotation(service, monkeypatch, tmp_path):
    """补换行失败后若**真的轮转了**，遗留的分隔符不得写进新空文件（Codex r4 LOW）。

    新活动文件是空的，不需要任何分隔符；不清掉的话首段会变成 ``max_lines + 1`` 行
    （多一个空行），有界的那条不变量就差一行。
    """
    import app.core.failed_writes_constants as _fwc
    import app.services.fallback_sync_service as _fss
    import app.services.memory_service as _ms

    monkeypatch.setattr(fwc, "FAILED_WRITES_MAX_LINES", 1, raising=False)
    monkeypatch.setattr(fwc, "FAILED_WRITES_MAX_ROTATIONS", 3, raising=False)
    path = tmp_path / "failed_writes.jsonl"
    monkeypatch.setattr(_ms, "FAILED_WRITES_FILE", path)
    monkeypatch.setattr(_fss, "SYNC_CHECKPOINT_FILE", tmp_path / "sync_checkpoint.json")
    path.write_bytes(b'{"episo')  # 1 行（按 b"\n" 口径，末行无换行也算一行）⇒ 达到上限 1

    real_open = open
    failed_once = []

    def _boom(file, mode="r", *a, **kw):
        # 只让补换行那次追加失败 ⇒ sep 变成 "\n"；随后的轮转与追加照常成功
        if str(file) == str(path) and "a" in mode and not failed_once:
            failed_once.append(1)
            raise OSError("EIO")
        return real_open(file, mode, *a, **kw)

    monkeypatch.setattr(_fwc, "open", _boom, raising=False)

    service._pending_failed_writes = [{"episode_id": "after-rot-A"}]
    service._flush_pending_failed_writes()

    assert failed_once, "前置不成立：补换行那次写没有被注入失败"
    assert _overflow_siblings(path), "前置不成立：没有发生轮转"
    assert _nlines(path) <= 1, f"轮转后的新文件多了一个空行 —— 首段 {_nlines(path)} 行 > 上限 1: {path.read_bytes()!r}"
    assert any(r.get("episode_id") == "after-rot-A" for r in _records(path)), "记录没落进新文件"


async def test_replay_window_open_keeps_whole_multiline_batch_unrotated(service, bounded_memory_writes, monkeypatch):
    """窗口开着时，**一次多行**的批次也必须整批落盘且不轮转（车道自审 2026-09-19）。

    覆盖 ``append_failed_writes_bounded`` 的「窗口开着 ⇒ 只追加不轮转」分支里的
    ``for line in lines`` 循环。既有三条门（含 T6-C 的真锁门）都是一次一行地调
    ``_record_structured_outbox``，那个循环从没被喂过多行批次 —— 判据只要
    「行数 == 总数」，一次写一行和一次写 N 行分不出来。
    """
    import app.services.fallback_sync_service as fss

    path = bounded_memory_writes
    total = MAX_LINES + 3
    monkeypatch.setattr(fwc, "REPLAY_WINDOW_MAX_SECONDS", REPLAY_WINDOW, raising=False)

    async with fss._sync_all_lock:
        monkeypatch.setattr(fss, "_sync_all_started_at", time.monotonic(), raising=False)
        # 一次交来 total 条（> 上限），走的是批量路径而不是逐条路径
        service._pending_failed_writes = [{"episode_id": f"batch-{i}"} for i in range(total)]
        service._flush_pending_failed_writes()

    assert _overflow_siblings(path) == [], "窗口开着却轮转了 —— finalize 的「只增不减」判据会被打破"
    assert _identity_union(path, "episode_id") == {f"batch-{i}" for i in range(total)}, "窗口内的多行批次没有整批落盘"
    assert service._pending_failed_writes == [], "落盘后 pending 没清"


async def test_unobservable_replay_state_is_false_even_while_locked(monkeypatch):
    """观测不到回灌状态时判 False —— 而且要在**锁确实被占着**时验（车道自审 2026-09-19）。

    既有两条常驻门（t6c 的 ``test_replay_probe_falls_back_to_bounded_when_unobservable``
    与 ``test_unobservable_replay_state_stops_rotation_not_bounding_claim``）靠拦
    ``builtins.__import__`` 里 ``name == "app.services.fallback_sync_service"`` 来模拟
    「观测不到」。它们在**锁没被占**的前提下跑，所以守卫无论走哪条分支都返回 False ——
    一旦生产侧把 import 改成 ``from app.services import fallback_sync_service``
    （``name`` 变成 ``"app.services"``，拦不住了），那两条门照样绿，只是绿在
    「锁本来就没被占」这条完全不同的判据上。

    这条门把前提反过来：**先真持锁**（此时正常路径必然返回 True），再断言
    「观测不到 ⇒ False」。只有拦截真的生效，它才可能绿。
    """
    import builtins

    import app.services.fallback_sync_service as fss

    real_import = builtins.__import__

    def _no_fss(name, *a, **kw):
        if name == "app.services.fallback_sync_service":
            raise ImportError("simulated")
        return real_import(name, *a, **kw)

    async with fss._sync_all_lock:
        assert fss._sync_all_lock.locked(), "前置不成立：锁没拿到"
        # 不打桩时：锁被占 + 无时间戳 ⇒ True（保守判窗口开着）
        monkeypatch.setattr(fss, "_sync_all_started_at", None, raising=False)
        assert fwc._replay_in_flight() is True, "前置不成立：正常路径下应判窗口开着"

        monkeypatch.setattr(builtins, "__import__", _no_fss)
        assert fwc._replay_in_flight() is False, (
            "观测不到回灌状态却没判 False —— 生产侧的 import 形式可能已让既有拦截失效"
        )


async def test_replay_guard_logs_error_when_window_times_out(service, bounded_memory_writes, monkeypatch, caplog):
    """超时分支必须**留下 error 日志**（卡文 (d) 三态规格里写明的那一半）。

    三条守卫门原先只验「返回值导致的轮转行为」，没有一条断言这条 error ——
    而它是运维唯一能看见「窗口被判挂住」的信号。
    """
    import app.services.fallback_sync_service as fss

    monkeypatch.setattr(fwc, "REPLAY_WINDOW_MAX_SECONDS", REPLAY_WINDOW, raising=False)

    with caplog.at_level("ERROR", logger="app.core.failed_writes_constants"):
        async with fss._sync_all_lock:
            monkeypatch.setattr(
                fss,
                "_sync_all_started_at",
                time.monotonic() - (fwc.REPLAY_WINDOW_MAX_SECONDS + 5),
                raising=False,
            )
            assert fwc._replay_in_flight() is False

    assert any("[C2-01]" in r.getMessage() for r in caplog.records), (
        f"超时判定没有留下 [C2-01] error 日志: {[r.getMessage() for r in caplog.records]}"
    )


# ═══════════════════════════════════════════════════════════════════════════
# (e1) _pending_failed_writes 批次失败即时落盘
# ═══════════════════════════════════════════════════════════════════════════


async def test_batch_failed_writes_hit_disk_before_cleanup(bounded_memory_writes):
    """改前必红：批次 Neo4j 写失败后条目只留在内存，不调 ``cleanup()`` 就不落盘。

    Neo4j 客户端是**边界替身**（``record_episode`` 抛 RuntimeError）—— 被测对象是
    刷盘时机与文件 IO，两者全真。
    """
    import app.services.memory_service as _ms

    path = bounded_memory_writes

    neo4j = MagicMock()
    neo4j.initialize = AsyncMock()
    neo4j.stats = {"initialized": True, "connected": True}
    neo4j.record_episode = AsyncMock(side_effect=RuntimeError("neo4j down"))
    neo4j.get_all_recent_episodes = AsyncMock(return_value=[])

    svc = _ms.MemoryService(neo4j_client=neo4j)
    await svc.initialize()

    result = await svc.record_batch_learning_events(
        [
            {
                "event_type": "color_changed",
                "timestamp": "2026-01-20T10:00:00Z",
                "canvas_path": "Math/test.canvas",
                "node_id": "node_001",
                "metadata": {"concept": "导数"},
            }
        ]
    )

    episode_ids = result["episode_ids"]
    assert episode_ids, "前置不成立：批次没有产出 episode_id"

    on_disk = "\n".join(json.dumps(r, ensure_ascii=False) for r in _records(path))
    assert episode_ids[0] in on_disk, (
        "未调 cleanup() 前文件里找不到该 episode_id —— 批次失败只攒在内存，进程被 kill 就整批丢失"
    )
    assert svc._pending_failed_writes == [], "刷盘后 pending 没清空"


def test_flush_keeps_pending_when_disk_write_fails(service, monkeypatch, tmp_path):
    """磁盘写失败时**不清空** pending —— 请求期一次瞬时 IO 故障不得等于永久丢记录。

    改前是 ``finally: clear()`` 无条件清。在「只有 cleanup() 刷盘」的年代那只是
    进程退出时的最后一搏；本卡把刷盘提前到每个失败批次之后，无条件清就变成
    「请求期间盘一抖，这批记录永久消失，cleanup() 兜底也没内容可写」。

    故障是**真的**：把 ``FAILED_WRITES_FILE`` 的父目录指向一个普通文件，
    ``parent.mkdir(parents=True, exist_ok=True)`` 抛 ``FileExistsError``（OSError 子类）。
    不打桩被测方法，也不打桩 append helper（DD-03）。
    """
    import app.services.memory_service as _ms

    blocker = tmp_path / "blocker"
    blocker.write_bytes(b"not a directory\n")
    monkeypatch.setattr(_ms, "FAILED_WRITES_FILE", blocker / "failed_writes.jsonl")
    monkeypatch.setattr(fwc, "FAILED_WRITES_MAX_LINES", MAX_LINES, raising=False)
    _isolate_live_checkpoint(monkeypatch, tmp_path)

    service._pending_failed_writes = [{"episode_id": "e1"}, {"episode_id": "e2"}]
    service._flush_pending_failed_writes()

    assert [e["episode_id"] for e in service._pending_failed_writes] == ["e1", "e2"], (
        "磁盘写失败后 pending 被清空 —— 这批记录再也没有第二次机会落盘"
    )


def test_flush_drops_unserializable_pending_writes(service, bounded_memory_writes):
    """序列化失败时**丢弃** —— 它是确定性的，留着只会让 pending 无限增长。

    与上一条成对：两类失败必须分流，任何一边写反都会退化成「丢数据」或「内存泄漏」。
    """
    service._pending_failed_writes = [{"episode_id": "e1", "reason": object()}]
    service._flush_pending_failed_writes()

    assert service._pending_failed_writes == [], "不可序列化的条目被留在 pending ⇒ 每个批次都会重试同一条、列表只增不减"


def test_flush_repairs_dangling_tail_before_retry(service, bounded_memory_writes):
    """半行尾巴不得吞掉重试的记录（Codex r2 HIGH）。

    场景：上一次追加写到一半就抛了 ``OSError``，活动文件以残缺 JSON 结尾。
    若重试时直接追加，新记录会和残缺尾巴粘成一行 —— 记录被吞掉，而调用方以为
    「这次成功了」并把它从 pending 里删掉 = **表面重试成功、实则丢失**。
    """
    path = bounded_memory_writes
    path.write_bytes(b'{"episo')  # 上一次写到一半

    service._pending_failed_writes = [{"episode_id": "retried-A"}]
    service._flush_pending_failed_writes()

    # 按行宽容解析：残缺尾巴本身解析不了（回灌侧同样会跳过它），
    # 判据是**重试的那条**必须自成一条可解析的行。
    raw_lines = [ln for ln in path.read_bytes().decode("utf-8").split("\n") if ln.strip()]
    parsed = []
    for ln in raw_lines:
        try:
            parsed.append(json.loads(ln))
        except json.JSONDecodeError:
            pass

    assert raw_lines[0] == '{"episo', f"残缺尾巴没有自成一行 —— 和重试记录粘在一起了: {raw_lines[0]!r}"
    assert any(r.get("episode_id") == "retried-A" for r in parsed), (
        f"重试的记录没有成为一条可解析的行 —— 被半行尾巴吞掉了: {path.read_bytes()!r}"
    )
    assert service._pending_failed_writes == [], "落盘成功后 pending 没清"


def test_flush_keeps_good_entries_when_one_is_unserializable(service, bounded_memory_writes):
    """混合批次里只丢坏的那条，好条目照常落盘（Codex r2 MEDIUM）。

    改前是一句列表推导：任何一条坏条目都会让整批走进 TypeError 分支被丢掉。
    """
    path = bounded_memory_writes
    service._pending_failed_writes = [
        {"episode_id": "good-1"},
        {"episode_id": "bad", "reason": object()},
        {"episode_id": "good-2"},
    ]
    service._flush_pending_failed_writes()

    ids = {r.get("episode_id") for r in _records(path)}
    assert {"good-1", "good-2"} <= ids, f"好条目跟着坏条目一起被丢了: {ids}"
    assert "bad" not in ids, "不可序列化的条目不该出现在文件里"
    assert service._pending_failed_writes == [], "本批应已处理完"


def test_flush_does_not_glue_when_boundary_repair_fails(service, bounded_memory_writes, monkeypatch):
    """补换行那次写**失败**时也不得粘连（车道自审 2026-09-19）。

    ``ensure_line_boundary`` 返回 False 只代表「确认有半行、且补不上」。此时**不能拒写**
    （agent_service / _record_structured_outbox 没有重试缓冲，拒写 = 直接丢），
    正确做法是把分隔符并进本次写入的第一行 —— 一次 open 写完，不粘连。

    注入只让**第一次**追加（= 补换行那次）失败，之后的追加照常成功。
    """
    import app.core.failed_writes_constants as _fwc

    path = bounded_memory_writes
    path.write_bytes(b'{"episo')  # 半行尾巴 ⇒ 必然触发补换行

    real_open = open
    failed_once = []

    def _boom(file, mode="r", *a, **kw):
        if str(file) == str(path) and "a" in mode and not failed_once:
            failed_once.append(1)
            raise OSError("EIO")
        return real_open(file, mode, *a, **kw)

    monkeypatch.setattr(_fwc, "open", _boom, raising=False)

    service._pending_failed_writes = [{"episode_id": "sep-A"}]
    service._flush_pending_failed_writes()

    assert failed_once, "前置不成立：补换行那次写没有被注入失败"
    raw_lines = [ln for ln in path.read_bytes().decode("utf-8").split("\n") if ln.strip()]
    parsed = []
    for ln in raw_lines:
        try:
            parsed.append(json.loads(ln))
        except json.JSONDecodeError:
            pass

    assert raw_lines[0] == '{"episo', f"补换行失败后记录粘在了残缺尾巴上: {raw_lines[0]!r}"
    assert any(r.get("episode_id") == "sep-A" for r in parsed), f"记录没有成为一条可解析的行: {path.read_bytes()!r}"
    assert service._pending_failed_writes == [], "已落盘却没清 pending"


def test_flush_still_writes_when_boundary_probe_is_unreadable(service, bounded_memory_writes, monkeypatch):
    """探测**读不出来**时必须照常落盘 —— 「不知道有没有半行」不等于「有半行」。

    活动文件可写但不可读（``chmod 0222`` / ACL / EIO）时 ``ensure_line_boundary`` 的
    探测恒失败。若把它当作「有半行且补不上」并据此拒写，本方法就会**永远**刷不出去、
    ``_pending_failed_writes`` 无界增长、连 ``cleanup()`` 也再写不掉 —— 而**改动前**
    同样的批次是能落盘的（下层 ``rotate_if_over_limit`` / room 计算都刻意吞掉那次读失败）。
    不能为了防一个假想的粘连，把一条本来能落盘的路径改成永不落盘。
    """
    import app.core.failed_writes_constants as _fwc

    path = bounded_memory_writes
    path.write_bytes(b'{"ok": 1}\n')  # 正常收尾，没有半行

    real_open = open
    probed = []

    def _boom(file, mode="r", *a, **kw):
        if str(file) == str(path) and "b" in mode:
            probed.append(1)
            raise PermissionError("EACCES")  # 可写不可读
        return real_open(file, mode, *a, **kw)

    monkeypatch.setattr(_fwc, "open", _boom, raising=False)

    service._pending_failed_writes = [{"episode_id": "probe-blind-A"}]
    service._flush_pending_failed_writes()

    assert probed, "前置不成立：探测那次读没有被注入失败"
    ids = {r.get("episode_id") for r in _records(path)}
    assert "probe-blind-A" in ids, f"探测读不出来就拒写了 —— 这批记录永远刷不出去、pending 会无界增长: {ids}"
    assert service._pending_failed_writes == [], "已落盘却没清 pending"


def test_flush_drops_unencodable_entry_without_raising(service, bounded_memory_writes):
    """孤立代理这类**编码**失败不得逃出本方法（Codex r3 MEDIUM）。

    ``json.dumps(ensure_ascii=False)`` 对 ``"\\ud800"`` 会成功，真正炸的是写盘那一刻的
    ``UnicodeEncodeError``（属 ``ValueError`` 不属 ``OSError``）。它若逃出去，
    ``record_batch_learning_events`` 就从「返回 errors/failed」变成「整个请求抛异常」。
    """
    path = bounded_memory_writes
    # ⚠️ 坏条目必须排在**前面**：排在后面时好条目已经在异常抛出前落了盘，
    # 「删掉预验」这个负控输入就分不出差别（实测段⑧ SURVIVED 即因此）。
    service._pending_failed_writes = [
        # 用 chr() 在运行期造孤立代理：写成源码字面量会让读取/重写这份源文件的工具
        # （pytest 的断言改写、ruff 等）自己在 UTF-8 编码时炸掉。
        {"episode_id": "surrogate", "reason": chr(0xD800)},
        {"episode_id": "ok-1"},
    ]

    service._flush_pending_failed_writes()  # 不得抛

    ids = {r.get("episode_id") for r in _records(path)}
    assert "ok-1" in ids, f"好条目没落盘: {ids}"
    assert "surrogate" not in ids, "不可编码的条目不该出现在文件里"
    assert service._pending_failed_writes == [], "本批应已处理完"


# ═══════════════════════════════════════════════════════════════════════════
# (e2) 新有界链 —— dead_letter_episodes.jsonl（e3 outbox 子项已退，见验收单）
# ═══════════════════════════════════════════════════════════════════════════


def _episode_task(i: int):
    import app.services.episode_worker as _ew

    return _ew.EpisodeTask(
        name=f"batch_learning:concept-{i}",
        episode_body=f"episode body #{i}",
        group_id="vault__test",
        source_description="canvas_batch:test",
    )


def test_dead_letter_episodes_is_bounded(bounded_dead_letter_episodes):
    """改前必红：``DeadLetterStore.store`` 裸追加 ⇒ 活动文件 8 行、零 overflow。"""
    import app.services.episode_worker as _ew

    path = bounded_dead_letter_episodes
    total = MAX_LINES + 3
    store = _ew.DeadLetterStore(str(path))

    for i in range(total):
        store.store(_episode_task(i), RuntimeError(f"boom-{i}"))

    assert _nlines(path) <= MAX_LINES, (
        f"活动文件超行数：{_nlines(path)} > {MAX_LINES} —— dead_letter_episodes.jsonl 仍无界"
    )
    assert _overflow_siblings(path), "没有 .overflow.* —— 从未发生轮转"
    assert len(_identity_union(path, "episode_body_sha256")) == total, "轮转丢了死信条目"


# ── H1 整改（zcode r6 HIGH）：死信链行边界防护 ─────────────────────────────


def test_dead_letter_store_does_not_concatenate_onto_dangling_tail(bounded_dead_letter_episodes):
    """负控输入：半行尾巴后 store 一条 ⇒ 新记录自成可解析行（H1 整改）。

    zcode r6 HIGH：上次 store 在 ENOSPC/EIO 下写到半行（``b'{"epi'``）后，裸追加会让
    下一条死信粘在残缺尾巴后成不可解析行；死信**无重试缓冲** ⇒ 该条静默丢失
    （与 failed_writes 链已修缺陷同类）。
    """
    import app.services.episode_worker as _ew

    path = bounded_dead_letter_episodes
    path.write_bytes(b'{"epi')  # 预置半行尾巴

    store = _ew.DeadLetterStore(str(path))
    store.store(_episode_task(0), RuntimeError("down"))

    raw = path.read_bytes()
    assert b'{"epi{"' not in raw, f"新记录粘在半行尾巴后（H1 未修）: {raw!r}"
    lines = [ln for ln in raw.decode("utf-8").split("\n") if ln.strip()]
    assert lines[0] == '{"epi', f"残缺尾巴应原样保留、自成一行: {lines[0]!r}"
    parsed = []
    for ln in lines:
        try:
            parsed.append(json.loads(ln))
        except json.JSONDecodeError:
            pass
    assert len(parsed) == 1 and parsed[0].get("episode_body_sha256"), f"新记录没有成为一条可解析的行: {raw!r}"


def test_write_dead_letter_does_not_concatenate_onto_dangling_tail(tmp_path):
    """H1 同型残留（``failure_counters.write_dead_letter``）负控输入：同上口径。"""
    path = tmp_path / "edge_dead_letters.jsonl"
    path.write_bytes(b'{"epi')

    fc.write_dead_letter(path, "edge_sync", "boom", edge_id="e-1")

    raw = path.read_bytes()
    assert b'{"epi{"' not in raw, f"新记录粘在半行尾巴后: {raw!r}"
    lines = [ln for ln in raw.decode("utf-8").split("\n") if ln.strip()]
    assert lines[0] == '{"epi', f"残缺尾巴应原样保留、自成一行: {lines[0]!r}"
    parsed = []
    for ln in lines:
        try:
            parsed.append(json.loads(ln))
        except json.JSONDecodeError:
            pass
    assert len(parsed) == 1 and parsed[0].get("edge_id") == "e-1", f"新记录未成可解析行: {raw!r}"


def test_failed_writes_chain_repairs_dangling_tail_control(bounded_memory_writes):
    """对照输入：同输入走 failed_writes 链会先补换行（与上面两条负控成对）。"""
    import app.core.failed_writes_constants as _fwc

    path = bounded_memory_writes
    path.write_bytes(b'{"epi')

    with _fwc.failed_writes_lock:
        _fwc.append_failed_writes_bounded(path, ['{"k": 1}'])

    raw = path.read_bytes()
    assert b'{"epi{"' not in raw, f"对照链也粘连了（原语回归）: {raw!r}"
    lines = [ln for ln in raw.decode("utf-8").split("\n") if ln.strip()]
    assert lines[0] == '{"epi', f"残缺尾巴应原样保留: {lines[0]!r}"
    parsed = []
    for ln in lines:
        try:
            parsed.append(json.loads(ln))
        except json.JSONDecodeError:
            pass
    assert any(r.get("k") == 1 for r in parsed), f"对照链的记录未成可解析行: {raw!r}"


# ═══════════════════════════════════════════════════════════════════════════
# (e4) Path.exists 吞异常残余 3 处 —— 「读不到」不得被压成「不存在」
#
# ⚠️ 注入点必须是 ``os.stat``，**不是** ``type(path).stat``（2026-09-18 于本车道
# Python 3.14.4 实测）：
#
#     pathlib.Path.exists()  →  os.path.exists(self)  →  genericpath.exists
#         →  try: os.stat(path) / except (OSError, ValueError): return False
#
# 3.14 的 ``Path.exists()`` **不经过** ``Path.stat()``，所以打桩 ``type(path).stat``
# 对它完全无效 —— 那样注入的故障改前代码根本看不见，门的红绿都不是它声称的原因
# （T6-C::test_count_lines_does_not_swallow_permission_error 打 ``type(path).stat``
# 是对的，因为 ``count_lines`` 调的就是 ``path.stat()``；这里被测的是 ``exists()``，
# 层不同）。吞异常发生在 ``genericpath.exists`` 的 ``except OSError`` 里。
# 打 ``os.stat`` 一次即同时喂到改前（``exists()`` → False）与改后
# （``Path.stat()`` → 上抛）两条路径；``Path.iterdir()`` 用 ``os.scandir``，另打。
# 一律**不打桩被测函数本身**（DD-03）。
# ═══════════════════════════════════════════════════════════════════════════


def _deny_os_stat(monkeypatch, denied, exc=PermissionError("no access")):
    """让 ``os.stat`` 对 ``denied(path)`` 为真的路径抛 ``exc``，其余原样放行。"""
    real_stat = os.stat

    def _stat(path, *a, **kw):
        if denied(str(path)):
            raise exc
        return real_stat(path, *a, **kw)

    monkeypatch.setattr(os, "stat", _stat)


def test_overflow_siblings_does_not_swallow_permission_error(monkeypatch, tmp_path):
    """``overflow_siblings`` 不得把「目录读不到」压成「没有兄弟」。

    压成空列表 ⇒ ``_prune_overflow`` 认为没有可删的档案，retention 静默失效。
    父目录既 stat 不到也列不出 = 真实的 EACCES 形态（父目录的父目录缺 +x）。
    """
    parent = tmp_path / "data"
    parent.mkdir()
    path = parent / "failed_writes.jsonl"
    path.write_bytes(b'{"a":1}\n')

    _deny_os_stat(monkeypatch, lambda p: p == str(parent))
    real_scandir = os.scandir

    def _scandir(p=".", *a, **kw):
        if str(p) == str(parent):
            raise PermissionError("no access")
        return real_scandir(p, *a, **kw)

    monkeypatch.setattr(os, "scandir", _scandir)

    try:
        result = fc.overflow_siblings(path)
    except PermissionError:
        return
    raise AssertionError(f"权限错误被吞成了空列表: {result!r}")


def test_unique_overflow_target_does_not_swallow_stat_error(monkeypatch, tmp_path):
    """``_unique_overflow_target`` 不得交出一个「探测不出来」的名字。

    ``Path.rename`` 在 POSIX 下静默覆盖已存在的目标 —— 探测被 PermissionError
    拦下时若当作「不存在」，轮转就会吃掉整份 overflow。正确反应是换下一个序号。
    只拦 ``-00`` 那一个候选名：改前 ``exists()`` 把它压成 False 于是照交不误，
    改后 ``stat()`` 上抛被 ``except OSError: continue`` 接住，换到 ``-01``。
    """
    path = tmp_path / "failed_writes.jsonl"
    path.write_bytes(b'{"a":1}\n')

    # ⚠️ 只能按「序号后缀」精确匹配，不能写 `"-00" in name`（Codex r1 LOW）：
    # 时间戳是 `%Y-%m-%d-%H%M%S%f`，UTC 0 点（`00xxxx`）时 `-00` 会命中时间戳本身
    # ⇒ 100 个候选**全部**被注入权限错误 ⇒ 正确实现也拿不到名字 = 门按时刻随机误红。
    serial_00 = f"-00{path.suffix}"

    def _denied(p: str) -> bool:
        name = p.rsplit("/", 1)[-1]
        return fc.OVERFLOW_SUFFIX in name and name.endswith(serial_00)

    _deny_os_stat(monkeypatch, _denied, PermissionError("probe blocked"))

    target = fc._unique_overflow_target(path)
    assert not target.name.endswith(serial_00), (
        f"探测被权限错误拦下的名字仍被交了出去: {target.name} —— rename 会静默覆盖它"
    )


def test_dead_letter_store_count_does_not_swallow_permission_error(monkeypatch, tmp_path):
    """``DeadLetterStore.count`` 不得把「读不到」压成「0 条」。"""
    import app.services.episode_worker as _ew

    path = tmp_path / "dead_letter_episodes.jsonl"
    path.write_bytes(b'{"a":1}\n')
    store = _ew.DeadLetterStore(str(path))

    _deny_os_stat(monkeypatch, lambda p: p == str(path))

    try:
        result = store.count()
    except PermissionError:
        return
    raise AssertionError(f"权限错误被吞成了行数: {result!r}")


# ═══════════════════════════════════════════════════════════════════════════
# 常驻硬边界门（文件本地 AST）—— 新增测试忘了隔离现网文件就当场红
# ═══════════════════════════════════════════════════════════════════════════

#: 触到这些名字 = 会走到 failed_writes 链（轮转前置动作会删/改现网 checkpoint）
_FAILED_WRITES_CHAIN = {
    "_record_failed_write",
    "_record_structured_outbox",
    "_flush_pending_failed_writes",
    "append_failed_writes_bounded",
    "record_batch_learning_events",
}
_OUTBOX_CHAIN = {"_write_outbox"}
_DEAD_LETTER_CHAIN = {"DeadLetterStore"}

#: fixture / helper 名 → 它已经替调用方隔离掉的东西
_ISOLATORS = {
    "bounded_agent_writes": {"FAILED_WRITES_FILE", "SYNC_CHECKPOINT_FILE", "tmp_path"},
    "bounded_memory_writes": {"FAILED_WRITES_FILE", "SYNC_CHECKPOINT_FILE", "tmp_path"},
    "bounded_dead_letter_episodes": {"SYNC_CHECKPOINT_FILE", "tmp_path"},
    "_isolate_live_checkpoint": {"SYNC_CHECKPOINT_FILE"},
}


def _iter_test_defs(tree):
    """产出 (函数节点, 展示名)：模块级 ``test_*`` **与** ``Test*`` 类里的方法。

    ⚠️ 必须连类方法一起扫（Codex r1 MEDIUM）：``pytest.ini`` 的
    ``python_classes = Test*`` 意味着类里的 ``test_*`` 方法同样会被收集执行，
    只扫模块级 = 把「写进类里」变成一条**门未覆盖的路径**。
    """

    def _walk(body, prefix: str):
        for node in body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("test_"):
                    yield node, f"{prefix}{node.name}"
            elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
                # ⚠️ 递归，不是只看一层（Codex r2 MEDIUM）：``TestOuter.TestInner`` 这种
                # 嵌套类里的 ``test_*`` 同样会被 pytest 收集，只扫一层 = 留一条门未覆盖的路径。
                yield from _walk(node.body, f"{prefix}{node.name}::")

    yield from _walk(tree.body, "")


def _isolation_offenders(src: str) -> List[str]:
    """扫一份测试源码，返回「碰了现网链却没隔离」的 ``test_`` 函数名。

    ⚠️ 「碰了什么」只数 **Name / Attribute 标识符**，不数字符串字面量 ——
    否则本函数自己的这几个名单常量（纯字符串）会把自己判成违规，门就得靠
    「恰好也提到 SYNC_CHECKPOINT_FILE」这种巧合豁免自己（不可靠）。
    「有没有隔离」则必须连字符串字面量一起看：``monkeypatch.setattr(m, "X", …)``
    里的 X 本来就是字符串。

    ⚠️ **这是名字层的必要条件，不是充分条件**（Codex r1 MEDIUM，如实登记）：
    它只能证明「该出现的隔离名字出现了」，证明不了路径**真的**指向了 ``tmp_path``。
    例如 ``def test_x(tmp_path): DeadLetterStore().store(...)``（拿了 tmp_path 却
    没把它传给被测对象）本门放行；经 fixture / helper 间接写入同样看不出来。
    ⚠️ 兜底也**不能**用 ``git status --porcelain backend/data/``（Codex r2 更正初版
    这句失实）：``backend/data/.gitignore`` 的 ``*.jsonl`` 把这些文件连同
    ``*.overflow.*.jsonl`` 一起忽略，普通 status 根本看不见它们被写过。
    真正能看见的兜底是对 ``backend/data/`` 做**跑前 / 跑后 sha256 快照**逐行比对
    （见本卡验收单 (m)）。本门的作用是把「整类忘记」在写的时候就挡住，不替代那道兜底。
    """
    offenders: List[str] = []
    for node, label in _iter_test_defs(ast.parse(src)):
        identifiers: Set[str] = set()
        literals: Set[str] = set()
        for sub in ast.walk(node):
            if isinstance(sub, ast.Name):
                identifiers.add(sub.id)
            elif isinstance(sub, ast.Attribute):
                identifiers.add(sub.attr)
            elif isinstance(sub, ast.Constant) and isinstance(sub.value, str):
                literals.add(sub.value)

        args = {a.arg for a in node.args.args}
        evidence = literals | identifiers | args
        for name in args | identifiers:
            evidence |= _ISOLATORS.get(name, set())

        required: Set[str] = set()
        if identifiers & _FAILED_WRITES_CHAIN:
            required |= {"FAILED_WRITES_FILE", "SYNC_CHECKPOINT_FILE"}
        if identifiers & _OUTBOX_CHAIN:
            required |= {"OUTBOX_FILE"}
        if identifiers & _DEAD_LETTER_CHAIN:
            required |= {"tmp_path"}

        missing = sorted(required - evidence)
        if missing:
            offenders.append(f"{label} (:{node.lineno}) 缺 {missing}")
    return offenders


def test_every_staging_test_isolates_live_files():
    """⛔ 常驻硬边界门：本文件里任何碰到落盘链的测试都必须把路径指向 tmp_path。

    逐条等审查告诉我「这条忘了隔离」是不可收敛的（T6-C 被 Codex 两轮各抓一条
    同型漏网）—— 把规则本身钉成 AST 门，新增测试忘了隔离就当场红。
    """
    src = pathlib.Path(__file__).read_text(encoding="utf-8")
    offenders = _isolation_offenders(src)
    assert not offenders, "这些测试会碰到现网落盘链却没隔离：\n  " + "\n  ".join(offenders)


def test_isolation_scanner_can_actually_detect_an_offender():
    """验伪锚：上面那条扫描器必须真能抓到人，否则它是个恒绿的摆设。

    三类各喂一段「碰了链但没隔离」的源码，再喂一段合规的 —— 前三段必须命中、
    第四段必须放行。只验「扫出 0 个」的门自己永远绿。
    """
    bad_failed_writes = "def test_x(service):\n    service._record_structured_outbox({'a': 1})\n"
    bad_outbox = "def test_y(bus):\n    bus._write_outbox(e, 'h', 'r')\n"
    bad_dead_letter = "def test_z():\n    store = DeadLetterStore('/live/dl.jsonl')\n"
    bad_in_class = (
        "class TestSomething:\n    def test_m(self, service):\n        service._record_structured_outbox({'a': 1})\n"
    )
    good = "def test_ok(bounded_memory_writes, service):\n    service._record_structured_outbox({'a': 1})\n"

    assert _isolation_offenders(bad_failed_writes), "扫描器漏掉了 failed_writes 链的违规"
    assert _isolation_offenders(bad_outbox), "扫描器漏掉了 outbox 链的违规"
    assert _isolation_offenders(bad_dead_letter), "扫描器漏掉了 dead-letter 链的违规"
    assert _isolation_offenders(bad_in_class), "扫描器漏掉了 Test* 类方法里的违规"
    bad_nested = (
        "class TestOuter:\n"
        "    class TestInner:\n"
        "        def test_n(self, service):\n"
        "            service._record_structured_outbox({'a': 1})\n"
    )
    assert _isolation_offenders(bad_nested), "扫描器漏掉了嵌套 Test* 类里的违规"
    assert _isolation_offenders(good) == [], "扫描器把合规用例误判成违规"
