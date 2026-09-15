"""CARD-NEO4J-REPLAY-BOUND (T6-C, BATCH-2026-09-11-第十四批) — 死信坟场写侧有界。

先红后绿门。改前 ``write_dead_letter`` (failure_counters.py) 与
``_record_structured_outbox`` / ``_flush_pending_failed_writes``
(memory_service.py) 都是**裸追加**——无行数上限、无轮转 ⇒ Neo4j 永久离线时
三个 JSONL 单调增长直到占满磁盘。本文件的 (b)(c) 门在改前必红。

⛔ 硬边界：本文件所有路径一律 ``monkeypatch`` / ``tmp_path``，
**不触碰现网 ``backend/data/*.jsonl``**，不连 7691/7687。

⚠️ 计数口径：本文件数行一律用 ``read_bytes().count(b"\\n")``，与生产侧
``count_lines`` 逐字节同口径。**不用 ``splitlines()``**——它会在 U+2028 /
U+2029 处额外切行，与生产计数不同口径，会让门的真值随条目内容漂移。
"""

from __future__ import annotations

import json

import pytest

import app.core.failed_writes_constants as fwc
import app.core.failure_counters as fc
import app.services.memory_service as ms

# 与生产默认值无关的小值：门只验「阈值触发」这个行为，不验具体默认值。
MAX_LINES = 5
MAX_ROTATIONS = 3


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


def _synced_siblings(path):
    """既有回灌侧的 ``.synced.*`` 兄弟——本卡 retention 不得碰它们。"""
    if not path.parent.exists():
        return []
    return sorted(p for p in path.parent.iterdir() if p.name.startswith(path.stem) and ".synced." in p.name)


@pytest.fixture
def bounded_dead_letter(monkeypatch, tmp_path):
    """把 dead-letter 上限常量与两条路径全指向 tmp_path。

    ``raising=False`` 是**故意**的：改前 ``DEAD_LETTER_MAX_LINES`` 这个属性
    还不存在，若用默认的 ``raising=True``，先红会红在 ``AttributeError``
    而不是红在「活动文件超行数 / 无 overflow」——那样负控①（删掉上限核查
    一行）也会红在同一个 AttributeError 上，负控就失去鉴别力。
    """
    monkeypatch.setattr(fc, "DEAD_LETTER_MAX_LINES", MAX_LINES, raising=False)
    monkeypatch.setattr(fc, "DEAD_LETTER_MAX_ROTATIONS", MAX_ROTATIONS, raising=False)
    edge = tmp_path / "failed_edge_syncs.jsonl"
    dual = tmp_path / "failed_dual_writes.jsonl"
    monkeypatch.setattr(fc, "EDGE_SYNC_DEAD_LETTER_PATH", edge)
    monkeypatch.setattr(fc, "DUAL_WRITE_DEAD_LETTER_PATH", dual)
    return edge, dual


# ═══════════════════════════════════════════════════════════════════════════
# (b) 写侧有界 —— edge_sync / dual_write 两条 dead-letter 链
# ═══════════════════════════════════════════════════════════════════════════


def test_edge_sync_dead_letter_is_bounded(bounded_dead_letter):
    """改前必红：write_dead_letter 裸追加 ⇒ 活动文件 8 行、零 overflow。"""
    edge, _ = bounded_dead_letter
    total = MAX_LINES + 3
    for i in range(total):
        fc.write_dead_letter(fc.EDGE_SYNC_DEAD_LETTER_PATH, "edge_sync", f"err{i}", edge_id=f"e{i}")

    active = _nlines(edge)
    overflow = _overflow_siblings(edge)
    assert active <= MAX_LINES, f"活动文件超行数: {active} > 上限 {MAX_LINES} (追加了 {total} 条)"
    assert overflow, f"无 .overflow.* 兄弟文件 (目录: {sorted(edge.parent.iterdir())})"


def test_dual_write_dead_letter_is_bounded(bounded_dead_letter):
    """改前必红：dual_write 链与 edge_sync 共用 write_dead_letter，同样无上限。"""
    _, dual = bounded_dead_letter
    total = MAX_LINES + 3
    for i in range(total):
        fc.write_dead_letter(fc.DUAL_WRITE_DEAD_LETTER_PATH, "dual_write", f"err{i}", episode_id=f"ep{i}")

    active = _nlines(dual)
    overflow = _overflow_siblings(dual)
    assert active <= MAX_LINES, f"活动文件超行数: {active} > 上限 {MAX_LINES} (追加了 {total} 条)"
    assert overflow, f"无 .overflow.* 兄弟文件 (目录: {sorted(dual.parent.iterdir())})"


def test_no_rotation_below_limit(bounded_dead_letter):
    """验伪锚（承重）：未超限不得轮转 —— 改前改后都须绿。

    证明上限是**阈值触发**，不是恒触发。若实现写成「每次追加都轮转」，
    (b) 的两条门照样绿，只有这条会红。
    """
    edge, _ = bounded_dead_letter
    below = MAX_LINES - 1
    for i in range(below):
        fc.write_dead_letter(edge, "edge_sync", f"err{i}", edge_id=f"e{i}")

    assert _nlines(edge) == below
    assert _overflow_siblings(edge) == [], "未超限却轮转了"


def test_dead_letter_entry_fields_survive_bounding(bounded_dead_letter):
    """有界化不得改 write_dead_letter 的条目语义（test_failure_observability 依赖）。"""
    edge, _ = bounded_dead_letter
    fc.write_dead_letter(edge, "edge_sync", "boom", edge_id="e1", canvas_name="c", request_id="r1")
    entry = json.loads(edge.read_text(encoding="utf-8").splitlines()[0])
    assert entry["type"] == "edge_sync"
    assert entry["error"] == "boom"
    assert entry["edge_id"] == "e1"
    assert entry["canvas_name"] == "c"
    assert entry["request_id"] == "r1"
    assert "timestamp" in entry


# ═══════════════════════════════════════════════════════════════════════════
# 轮转的身份性质：不丢条目、retention 删的是最老那个、不碰 .synced.
# ═══════════════════════════════════════════════════════════════════════════


def test_rotation_preserves_every_entry(monkeypatch, tmp_path):
    """轮转目标必须唯一：同一秒内多次轮转不得静默互相覆盖。

    ``Path.rename`` 在 POSIX 下覆盖同名目标而不报错；若轮转后缀只精确到秒
    （既有 ``_rotate_file:918`` 的 ``%Y-%m-%d-%H%M%S`` 就是），高频轮转会
    无声吃掉整份 overflow。本门按**条目守恒**判，不按文件数判。
    """
    monkeypatch.setattr(fc, "DEAD_LETTER_MAX_LINES", 1, raising=False)
    monkeypatch.setattr(fc, "DEAD_LETTER_MAX_ROTATIONS", 99, raising=False)
    path = tmp_path / "failed_edge_syncs.jsonl"

    total = 6
    for i in range(total):
        fc.write_dead_letter(path, "edge_sync", f"err{i}", edge_id=f"e{i}")

    # 前置：轮转必须真的发生过，否则「守恒」是平凡成立的（零轮转当然不丢）。
    assert _overflow_siblings(path), "轮转未发生，本门的守恒判据无意义"
    seen = _nlines(path) + sum(_nlines(p) for p in _overflow_siblings(path))
    assert seen == total, (
        f"轮转丢条目: 追加 {total} 条, 活动+overflow 共 {seen} 条 "
        f"(overflow 文件: {[p.name for p in _overflow_siblings(path)]})"
    )


def test_retention_drops_the_oldest_overflow(monkeypatch, tmp_path):
    """保留上限生效，且删掉的是**最老**那个（身份判据，不只是数量判据）。"""
    monkeypatch.setattr(fc, "DEAD_LETTER_MAX_LINES", 1, raising=False)
    monkeypatch.setattr(fc, "DEAD_LETTER_MAX_ROTATIONS", 2, raising=False)
    path = tmp_path / "failed_edge_syncs.jsonl"

    for i in range(6):
        fc.write_dead_letter(path, "edge_sync", f"err{i}", edge_id=f"e{i}")

    overflow = _overflow_siblings(path)
    # 前置：恰好卡在上限上 —— 既证明轮转发生过（不是零轮转的平凡绿），
    # 也证明 retention 真的删过（5 次轮转只剩 2 个）。
    assert len(overflow) == 2, f"保留上限未生效: {len(overflow)} 个 overflow"
    # 名字含定宽时间戳 ⇒ 字典序 == 时序；活下来的必须是最新的那些，
    # 即最老条目 err0 不得还在。
    bodies = "".join(p.read_text(encoding="utf-8") for p in overflow)
    assert '"err0"' not in bodies, "retention 删的不是最老的那个 overflow"


def test_retention_does_not_touch_synced_siblings(monkeypatch, tmp_path):
    """负控②的承重断言：本卡 retention 只清 ``.overflow.*``，不碰 ``.synced.*``。

    ``.synced.`` 是回灌侧（fallback_sync_service ``_rotate_file:919``）标记
    「已回灌」的后缀，按 30 天 retention 清理。若本卡写侧轮转也用
    ``.synced.``，未回灌的溢出数据会被误当已回灌处理，且会落进本卡的
    MAX_ROTATIONS 计数里被提前删掉。本门不依赖 30 天 cutoff——它验的是
    「本卡 retention 的作用面恰好等于 .overflow.」。
    """
    monkeypatch.setattr(fc, "DEAD_LETTER_MAX_LINES", 1, raising=False)
    monkeypatch.setattr(fc, "DEAD_LETTER_MAX_ROTATIONS", 1, raising=False)
    path = tmp_path / "failed_edge_syncs.jsonl"
    # 预置一个回灌侧留下的 .synced. 兄弟（与 _rotate_file 同形命名）
    synced = tmp_path / "failed_edge_syncs.synced.2020-01-01-000000"
    synced.write_text('{"type":"edge_sync","error":"old-synced"}\n', encoding="utf-8")

    for i in range(6):
        fc.write_dead_letter(path, "edge_sync", f"err{i}", edge_id=f"e{i}")

    # 前置：轮转 + retention 必须真的跑过（零轮转下「没误删」是平凡成立的）。
    assert _nlines(path) <= 1, "轮转未发生，本门的隔离判据无意义"
    assert synced.exists(), ".synced. 兄弟被本卡 retention 误删"
    assert _synced_siblings(path) == [synced]


# ═══════════════════════════════════════════════════════════════════════════
# (c) 写侧有界 —— failed_writes.jsonl 的两个 T6 地盘内追加点
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture
def bounded_failed_writes(monkeypatch, tmp_path):
    """把 failed_writes 上限常量与路径指向 tmp_path。

    ⚠️ 打桩 ``ms.FAILED_WRITES_FILE``（memory_service 的模块级绑定副本）而不是
    ``fwc.FAILED_WRITES_FILE``——既有 test_a7_honest_failure.py:108/142、
    test_story_30_24_boundary.py:551/583/622 打的就是这一侧，生产实现必须继续
    从这一侧取路径，否则那些测试会静默写进现网 backend/data/failed_writes.jsonl。
    """
    monkeypatch.setattr(fwc, "FAILED_WRITES_MAX_LINES", MAX_LINES, raising=False)
    monkeypatch.setattr(fwc, "FAILED_WRITES_MAX_ROTATIONS", MAX_ROTATIONS, raising=False)
    path = tmp_path / "failed_writes.jsonl"
    monkeypatch.setattr(ms, "FAILED_WRITES_FILE", path)
    return path


@pytest.fixture
def service():
    svc = ms.MemoryService.__new__(ms.MemoryService)
    svc._initialized = True
    svc._episodes = []
    svc._pending_failed_writes = []
    return svc


def test_record_structured_outbox_is_bounded(service, bounded_failed_writes):
    """改前必红：memory_service:516 裸追加 ⇒ 活动文件 8 行、零 overflow。"""
    path = bounded_failed_writes
    total = MAX_LINES + 3
    for i in range(total):
        assert service._record_structured_outbox(
            {"kind": "knowledge_entity", "event_type": "callout_annotation", "i": i}
        )

    active = _nlines(path)
    assert active <= MAX_LINES, f"活动文件超行数: {active} > 上限 {MAX_LINES} (追加了 {total} 条)"
    assert _overflow_siblings(path), "无 .overflow.* 兄弟文件"


def test_flush_pending_failed_writes_is_bounded(service, bounded_failed_writes):
    """改前必红：memory_service:2872 是第二个裸追加点，同样无上限。

    ⚠️ 这里是**单批就超限**：一次 flush 交来 8 条而上限是 5。只在「追加前」
    核一次行数挡不住它（核的时候文件是空的 ⇒ 不轮转 ⇒ 一口气写 8 条）。
    有界实现必须边写边腾空间。
    """
    path = bounded_failed_writes
    total = MAX_LINES + 3
    service._pending_failed_writes = [{"episode_id": f"ep{i}", "reason": "Neo4j unreachable"} for i in range(total)]
    service._flush_pending_failed_writes()

    active = _nlines(path)
    assert active <= MAX_LINES, f"活动文件超行数: {active} > 上限 {MAX_LINES} (一次 flush {total} 条)"
    assert _overflow_siblings(path), "无 .overflow.* 兄弟文件"
    # 有界不等于可以丢：8 条必须原封不动地分布在活动文件 + overflow 里。
    seen = active + sum(_nlines(p) for p in _overflow_siblings(path))
    assert seen == total, f"批量 flush 丢条目: 交来 {total} 条, 落盘 {seen} 条"
    assert service._pending_failed_writes == []


def test_record_structured_outbox_still_returns_false_on_oserror(service, bounded_failed_writes, monkeypatch, tmp_path):
    """有界化不得改 _record_structured_outbox 的诚实失败语义（返回 False）。

    用「父目录其实是个普通文件」制造 OSError（NotADirectoryError ⊂ OSError），
    不去 monkeypatch 全局 ``pathlib.Path.mkdir``——那会波及同进程里的所有测试。
    """
    blocker = tmp_path / "blocker"
    blocker.write_text("not a directory\n", encoding="utf-8")
    monkeypatch.setattr(ms, "FAILED_WRITES_FILE", blocker / "failed_writes.jsonl")
    assert service._record_structured_outbox({"kind": "knowledge_entity"}) is False
