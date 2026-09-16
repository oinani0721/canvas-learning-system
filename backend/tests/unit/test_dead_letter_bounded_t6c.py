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


# ═══════════════════════════════════════════════════════════════════════════
# 上限常量的边界分支（Codex round-1 L3：这些分支此前无输入覆盖）
# ═══════════════════════════════════════════════════════════════════════════


def test_max_rotations_zero_keeps_no_overflow(monkeypatch, tmp_path):
    """MAX_ROTATIONS=0 = 轮转后立即全删（纯截断）。

    盯的是 ``_prune_overflow`` 里 ``siblings[:-max_rotations]`` 的陷阱：
    ``lst[:-0]`` == ``lst[:0]`` == 空，会让「保留 0 份」变成「一份都不删」，
    与 docstring 写的语义正好相反。现有其余测试的保留数都是正数，拦不住它。
    """
    monkeypatch.setattr(fc, "DEAD_LETTER_MAX_LINES", 1, raising=False)
    monkeypatch.setattr(fc, "DEAD_LETTER_MAX_ROTATIONS", 0, raising=False)
    path = tmp_path / "failed_edge_syncs.jsonl"
    for i in range(4):
        fc.write_dead_letter(path, "edge_sync", f"err{i}", edge_id=f"e{i}")

    assert _overflow_siblings(path) == [], "MAX_ROTATIONS=0 却留下了 overflow"
    assert _nlines(path) <= 1


def test_max_lines_non_positive_disables_bounding(monkeypatch, tmp_path):
    """MAX_LINES<=0 = 关闭上限（不轮转），留给「宁可涨也别动文件」的部署。"""
    monkeypatch.setattr(fc, "DEAD_LETTER_MAX_LINES", 0, raising=False)
    monkeypatch.setattr(fc, "DEAD_LETTER_MAX_ROTATIONS", 5, raising=False)
    path = tmp_path / "failed_edge_syncs.jsonl"
    for i in range(4):
        fc.write_dead_letter(path, "edge_sync", f"err{i}", edge_id=f"e{i}")

    assert _overflow_siblings(path) == [], "上限已关闭却仍轮转"
    assert _nlines(path) == 4


def test_bound_from_env_never_raises_on_bad_values(monkeypatch):
    """坏 env 值必须退回默认并告警，不得在**模块导入期**抛 ValueError。

    这些常量是模块级求值的：一个 ``CLS_DEAD_LETTER_MAX_LINES=abc``
    就足以让整个后端起不来。
    """
    for raw, expected in [
        ("abc", 10),  # 非整数
        ("-5", 10),  # 负数
        ("0", 10),  # 小于下限
        ("", 10),  # 空串
        ("   ", 10),  # 全空白
        ("  7  ", 7),  # 合法值带空白
    ]:
        monkeypatch.setenv("CLS_PROBE_BOUND_T6C", raw)
        assert fc.bound_from_env("CLS_PROBE_BOUND_T6C", 10, minimum=1) == expected, raw
    monkeypatch.delenv("CLS_PROBE_BOUND_T6C", raising=False)
    assert fc.bound_from_env("CLS_PROBE_BOUND_T6C", 10, minimum=1) == 10


def test_count_lines_counts_unterminated_last_line(tmp_path):
    """末行没有换行符也算一行——否则崩溃期被截断的半行会让上限判定少算。"""
    path = tmp_path / "failed_edge_syncs.jsonl"
    path.write_bytes(b'{"a":1}\n{"a":2}')
    assert fc.count_lines(path) == 2
    assert fc.count_lines(tmp_path / "does-not-exist.jsonl") == 0


# ═══════════════════════════════════════════════════════════════════════════
# Codex round-1 M1：读侧/清理侧失败**不得**阻断追加（旧版裸追加本来能成功）
# ═══════════════════════════════════════════════════════════════════════════


def test_unreadable_active_file_does_not_block_append(service, bounded_failed_writes, monkeypatch):
    """活动文件可写但不可读时仍须落盘。

    ``rotate_if_over_limit`` 已吞下它那次读失败；若 helper 里的第二次
    ``count_lines`` 再抛出去，追加就整个不发生，而批量路径的
    ``finally: pending.clear()`` 会把条目清掉 = 真丢数据。
    """
    path = bounded_failed_writes

    def _boom(_p):
        raise OSError("permission denied")

    monkeypatch.setattr(fwc, "count_lines", _boom)
    assert service._record_structured_outbox({"kind": "knowledge_entity", "i": 1})
    assert _nlines(path) == 1, "数行失败把追加整个挡掉了（旧版裸追加反而能成功）"


def test_unlistable_dir_does_not_block_dead_letter_append(monkeypatch, tmp_path):
    """父目录可写可遍历但不可列时，清理失败不得阻断新死信落盘。

    ``rotate_if_over_limit`` 的 docstring 声称「删不掉旧档案不该阻断新死信
    落盘」，但初版只保护了 ``unlink``，没保护 ``iterdir`` 那一步枚举。
    """
    monkeypatch.setattr(fc, "DEAD_LETTER_MAX_LINES", 1, raising=False)
    monkeypatch.setattr(fc, "DEAD_LETTER_MAX_ROTATIONS", 1, raising=False)
    path = tmp_path / "failed_edge_syncs.jsonl"
    fc.write_dead_letter(path, "edge_sync", "first", edge_id="e0")

    calls = {"n": 0}
    real = fc.overflow_siblings

    def _boom_on_prune(p):
        calls["n"] += 1
        # 第一次是 _unique_overflow_target 之后的 _prune_overflow 调用
        raise OSError("operation not permitted")

    monkeypatch.setattr(fc, "overflow_siblings", _boom_on_prune)
    fc.write_dead_letter(path, "edge_sync", "second", edge_id="e1")
    monkeypatch.setattr(fc, "overflow_siblings", real)

    assert calls["n"] >= 1, "本门没有走到枚举失败的那条路径"
    assert _nlines(path) == 1, "清理失败把新死信的追加挡掉了"
    assert _overflow_siblings(path), "轮转本身应已完成（失败的只是清理）"


# ═══════════════════════════════════════════════════════════════════════════
# Codex round-1 L3：身份守恒（行数守恒挡不住「丢一个 + 重一个」）
# ═══════════════════════════════════════════════════════════════════════════


def _collect_edge_ids(path):
    ids = []
    for p in [path] + _overflow_siblings(path):
        if not p.exists():
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                ids.append(json.loads(line)["edge_id"])
    return ids


def test_rotation_preserves_entry_identity_not_just_count(monkeypatch, tmp_path):
    """条目**身份**守恒：丢一个 e0、重复一个 e1，行数照样守恒，但集合不对。"""
    monkeypatch.setattr(fc, "DEAD_LETTER_MAX_LINES", 1, raising=False)
    monkeypatch.setattr(fc, "DEAD_LETTER_MAX_ROTATIONS", 99, raising=False)
    path = tmp_path / "failed_edge_syncs.jsonl"
    total = 6
    for i in range(total):
        fc.write_dead_letter(path, "edge_sync", f"err{i}", edge_id=f"e{i}")

    assert _overflow_siblings(path), "轮转未发生，本门无意义"
    got = sorted(_collect_edge_ids(path))
    assert got == [f"e{i}" for i in range(total)], f"条目身份不守恒: {got}"


def test_retention_keeps_exactly_the_newest_overflows(monkeypatch, tmp_path):
    """retention 留下的必须**恰好是最新的那两份**。

    只断言「两份且没有 err0」是不够的：保留 e1/e2、删掉更新的 e3/e4
    同样满足它（Codex round-1 L3 给的对照）。这里断言确切集合。
    """
    monkeypatch.setattr(fc, "DEAD_LETTER_MAX_LINES", 1, raising=False)
    monkeypatch.setattr(fc, "DEAD_LETTER_MAX_ROTATIONS", 2, raising=False)
    path = tmp_path / "failed_edge_syncs.jsonl"
    for i in range(6):
        fc.write_dead_letter(path, "edge_sync", f"err{i}", edge_id=f"e{i}")

    overflow = _overflow_siblings(path)
    assert len(overflow) == 2, f"保留上限未生效: {len(overflow)} 个 overflow"
    kept = sorted(json.loads(p.read_text(encoding="utf-8").splitlines()[0])["edge_id"] for p in overflow)
    # 6 次追加 ⇒ 轮转 5 次（e0..e4 各成一份），活动文件留 e5。
    # 保留最新两份 = e3, e4。
    assert kept == ["e3", "e4"], f"retention 留下的不是最新两份: {kept}"
    assert _collect_edge_ids(path).count("e5") == 1


# ═══════════════════════════════════════════════════════════════════════════
# 回灌窗口 × 轮转（内部对抗复核 2026-09-15 的 BLOCKER，Codex round-1 未发现）
#
# fallback_sync_service._sync_failed_writes 的 finalize 用「长度比较 + 位置
# 切片」判断重放期间有没有新追加（:366-367），前提是活动文件**只增不减**。
# 本卡是第一个让它变短的写者 ⇒ 窗口内轮转会让新条目被整份覆盖，或被错标成
# `.synced.`（谎称已回灌）。fallback_sync_service 在本卡是禁改面，所以修在
# 写侧：窗口开着就不轮转。
# ═══════════════════════════════════════════════════════════════════════════


async def test_no_rotation_while_replay_window_open(service, bounded_failed_writes):
    """回灌窗口开着时**绝不轮转**，且一条不丢。

    用的是**真实的** ``_sync_all_lock``，不是打桩 —— 打桩只能证明「我写的
    判断会被调用」，证明不了它读的是回灌侧真正在用的那把锁。
    """
    import app.services.fallback_sync_service as fss

    path = bounded_failed_writes
    total = MAX_LINES + 3

    async with fss._sync_all_lock:
        for i in range(total):
            assert service._record_structured_outbox({"kind": "knowledge_entity", "i": i})

    assert _overflow_siblings(path) == [], (
        "回灌窗口内发生了轮转 —— finalize 的「只增不减」判据会因此把窗口内新写的条目覆盖掉或错标成 .synced."
    )
    assert _nlines(path) == total, "窗口内的条目丢了"


async def test_rotation_resumes_after_replay_window_closes(service, bounded_failed_writes):
    """控制组：同样的输入，窗口**关着**时必须照常轮转。

    没有这条，上面那条门用「永不轮转」也能变绿。
    """
    import app.services.fallback_sync_service as fss

    path = bounded_failed_writes
    assert not fss._sync_all_lock.locked(), "前置不成立：锁本来就被别人占着"

    for i in range(MAX_LINES + 3):
        assert service._record_structured_outbox({"kind": "knowledge_entity", "i": i})

    assert _overflow_siblings(path), "窗口关着却没轮转 —— 上限失效了"
    assert _nlines(path) <= MAX_LINES


def test_replay_probe_falls_back_to_bounded_when_unobservable(monkeypatch):
    """观测不到回灌状态（import 失败 / 属性不在）⇒ 退回有界行为，而不是停掉上限。

    「读不到状态」不该被当成「回灌正在跑」—— 那会让上限被一个 import 错误
    永久关掉，而这正是本卡要防的磁盘占满。
    """
    import builtins

    real_import = builtins.__import__

    def _no_fss(name, *a, **kw):
        if name == "app.services.fallback_sync_service":
            raise ImportError("simulated")
        return real_import(name, *a, **kw)

    monkeypatch.setattr(builtins, "__import__", _no_fss)
    assert fwc._replay_in_flight() is False


def test_failed_writes_retention_keeps_newest_and_drops_oldest(service, monkeypatch, tmp_path):
    """failed_writes 这条链的 retention 此前零覆盖（只测过 dead-letter 侧）。"""
    monkeypatch.setattr(fwc, "FAILED_WRITES_MAX_LINES", 1, raising=False)
    monkeypatch.setattr(fwc, "FAILED_WRITES_MAX_ROTATIONS", 2, raising=False)
    path = tmp_path / "failed_writes.jsonl"
    monkeypatch.setattr(ms, "FAILED_WRITES_FILE", path)

    for i in range(6):
        assert service._record_structured_outbox({"kind": "knowledge_entity", "i": i})

    overflow = _overflow_siblings(path)
    assert len(overflow) == 2, f"failed_writes 的保留上限未生效: {len(overflow)}"
    kept = sorted(json.loads(p.read_text(encoding="utf-8").splitlines()[0])["i"] for p in overflow)
    assert kept == [3, 4], f"留下的不是最新两份: {kept}"


def test_overflow_name_keeps_extension_so_gitignore_covers_it(monkeypatch, tmp_path):
    """轮转产物必须仍以原扩展名结尾。

    ``backend/data/.gitignore`` 忽略的是 ``*.jsonl`` 与 ``*.synced.*``；
    ``with_suffix`` 会把 ``.jsonl`` 吃掉，产出的 ``failed_writes.overflow.<ts>``
    **不被任何规则命中**（实测 git check-ignore 无输出），于是每轮转一次就往
    git status 里多一个未跟踪文件，内容还含错误消息与 id。
    """
    monkeypatch.setattr(fc, "DEAD_LETTER_MAX_LINES", 1, raising=False)
    monkeypatch.setattr(fc, "DEAD_LETTER_MAX_ROTATIONS", 5, raising=False)
    path = tmp_path / "failed_edge_syncs.jsonl"
    for i in range(3):
        fc.write_dead_letter(path, "edge_sync", f"err{i}", edge_id=f"e{i}")

    names = [p.name for p in _overflow_siblings(path)]
    assert names, "轮转未发生"
    for n in names:
        assert n.endswith(".jsonl"), f"轮转产物丢了扩展名, gitignore 盖不住: {n}"
        # ⚠️ 这里**不再**断言 `".overflow." in n` —— n 是 _overflow_siblings 按
        # 该条件筛出来的，那句恒真（Codex round-2 L3）。改为直接核生产常量。
        assert fc.OVERFLOW_SUFFIX == ".overflow."


def test_unique_overflow_target_does_not_overwrite_existing(monkeypatch, tmp_path):
    """防撞段此前零覆盖：目标名已被占用时必须换名，不得覆盖既有归档。

    ⚠️ 必须**把时钟钉死**再测。否则两次调用大概率落在不同微秒上，根本走不到
    防撞分支，测试就成了「只要两次返回不同名字即可」的空壳 —— 覆盖不到
    `Path.rename` 静默覆盖那条真正危险的路径。
    """
    import datetime as _dt

    class _FrozenDateTime(_dt.datetime):
        @classmethod
        def now(cls, tz=None):
            return _dt.datetime(2026, 9, 15, 12, 0, 0, 123456, tzinfo=tz)

    monkeypatch.setattr(fc, "datetime", _FrozenDateTime)

    path = tmp_path / "failed_edge_syncs.jsonl"
    path.write_text('{"a":1}\n', encoding="utf-8")

    first = fc._unique_overflow_target(path)
    first.write_text("occupied\n", encoding="utf-8")

    second = fc._unique_overflow_target(path)
    assert second != first, "同一微秒下防撞失效：返回了已存在的目标（rename 会静默覆盖它）"
    assert second.name.endswith(".jsonl"), second.name
    assert first.read_text(encoding="utf-8") == "occupied\n", "既有归档被覆盖了"
    # 第三次必须继续往后排，且保持字典序 == 时序
    second.write_text("occupied2\n", encoding="utf-8")
    third = fc._unique_overflow_target(path)
    assert third not in (first, second)
    assert sorted([first.name, second.name, third.name]) == [first.name, second.name, third.name]


# ═══════════════════════════════════════════════════════════════════════════
# Codex round-2 H1：换代必须同时作废回灌游标
# ═══════════════════════════════════════════════════════════════════════════


def test_rotation_invalidates_stale_replay_checkpoint(service, bounded_failed_writes, monkeypatch, tmp_path):
    """轮转让文件换代 ⇒ 必须把 failed_writes 的持久化游标一并作废。

    守卫只挡「回灌窗口开着」，挡不住「窗口已关但游标还残留」（finalize 撞
    OSError 就会留下它）。残留游标 + 换代后的新文件 = 下一轮把新条目整段跳过，
    还因 still_pending 为空而被改名 .synced. 谎称已回灌。
    """
    import app.services.fallback_sync_service as fss

    ckpt = tmp_path / "sync_checkpoint.json"
    ckpt.write_text(
        json.dumps({"failed_writes": {"index": 50, "progress_version": "x"}, "canvas_events": {"index": 3}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(fss, "SYNC_CHECKPOINT_FILE", ckpt)

    path = bounded_failed_writes
    for i in range(MAX_LINES + 3):
        assert service._record_structured_outbox({"kind": "knowledge_entity", "i": i})

    assert _overflow_siblings(path), "轮转未发生，本门无意义"
    left = json.loads(ckpt.read_text(encoding="utf-8"))
    assert "failed_writes" not in left, "换代了却留下指向上一代文件的游标"
    assert left.get("canvas_events") == {"index": 3}, "误伤了别的链的游标"


def test_rotation_is_skipped_when_checkpoint_cannot_be_cleared(service, bounded_failed_writes, monkeypatch):
    """作废游标失败 ⇒ **放弃轮转**（宁可越限），与既有「清不掉就不动文件」同口径。"""
    monkeypatch.setattr(fwc, "_invalidate_replay_checkpoint", lambda: False)
    path = bounded_failed_writes
    total = MAX_LINES + 3
    for i in range(total):
        assert service._record_structured_outbox({"kind": "knowledge_entity", "i": i})

    assert _overflow_siblings(path) == [], "游标作废失败却照样换代了"
    assert _nlines(path) == total, "条目丢了"


def test_checkpoint_invalidation_is_noop_without_checkpoint_file(monkeypatch, tmp_path):
    """没有 checkpoint 文件时应视为成功（没有旧游标要作废），不得阻断轮转。"""
    import app.services.fallback_sync_service as fss

    monkeypatch.setattr(fss, "SYNC_CHECKPOINT_FILE", tmp_path / "absent.json")
    assert fwc._invalidate_replay_checkpoint() is True


# ═══════════════════════════════════════════════════════════════════════════
# Codex round-2 M1 / L2：exists() 吞权限、以及负控打错模块
# ═══════════════════════════════════════════════════════════════════════════


def test_count_lines_does_not_swallow_permission_error(monkeypatch, tmp_path):
    """count_lines 不得把「读不到」压成「0 行」。

    Python 3.14 的 Path.exists() 把 PermissionError 吞成 False；若 count_lines
    照用它，上限判定就永远到不了阈值 = 有界静默失效。
    """
    path = tmp_path / "failed_edge_syncs.jsonl"
    path.write_text('{"a":1}\n', encoding="utf-8")

    real_stat = type(path).stat

    def _boom(self, *a, **kw):
        if self == path:
            raise PermissionError("no access")
        return real_stat(self, *a, **kw)

    monkeypatch.setattr(type(path), "stat", _boom)
    try:
        fc.count_lines(path)
    except PermissionError:
        pass
    else:
        raise AssertionError("权限错误被吞成了行数")


def test_rotate_handles_count_lines_failure_in_its_own_module(monkeypatch, tmp_path):
    """负控打桩必须打**轮转函数实际使用的那份绑定**。

    `rotate_if_over_limit` 用的是 `fc.count_lines`；先前只打了 `fwc.count_lines`，
    所以 failure_counters 自己的数行失败分支一直零覆盖（Codex round-2 L2）。
    """
    path = tmp_path / "failed_edge_syncs.jsonl"
    path.write_text('{"a":1}\n{"a":2}\n', encoding="utf-8")

    def _boom(_p):
        raise OSError("cannot read")

    monkeypatch.setattr(fc, "count_lines", _boom)
    assert fc.rotate_if_over_limit(path, 1, 5) is False, "数行失败时不该轮转"
    assert _overflow_siblings(path) == []


def test_rotate_handles_rename_failure(monkeypatch, tmp_path):
    """rename 失败 ⇒ 返回 False、不抛；调用方仍会继续追加（此前零覆盖）。"""
    path = tmp_path / "failed_edge_syncs.jsonl"
    path.write_text('{"a":1}\n{"a":2}\n', encoding="utf-8")

    real_rename = type(path).rename

    def _boom(self, target):
        if self == path:
            raise PermissionError("cannot rename")
        return real_rename(self, target)

    monkeypatch.setattr(type(path), "rename", _boom)
    assert fc.rotate_if_over_limit(path, 1, 5) is False
    assert _nlines(path) == 2, "rename 失败不该动到活动文件"


def test_collision_fallback_still_sorts_last(monkeypatch, tmp_path):
    """第 101 个同微秒兜底名仍须排在 -99 **之后**（Codex round-2 L1）。

    `-`(0x2D) < `.`(0x2E) ⇒ `-99-<uuid>.jsonl` 会排在 `-99.jsonl` 之前，
    「删最老」就会去删这个最新的兜底档。分隔符必须大于 `.`。
    """
    import datetime as _dt

    class _Frozen(_dt.datetime):
        @classmethod
        def now(cls, tz=None):
            return _dt.datetime(2026, 9, 16, 1, 2, 3, 456789, tzinfo=tz)

    monkeypatch.setattr(fc, "datetime", _Frozen)
    path = tmp_path / "failed_edge_syncs.jsonl"
    path.write_text("{}\n", encoding="utf-8")

    taken = []
    for _ in range(100):
        t = fc._unique_overflow_target(path)
        t.write_text("x\n", encoding="utf-8")
        taken.append(t)
    fallback = fc._unique_overflow_target(path)
    assert fallback not in taken
    assert fallback.name > taken[-1].name, f"兜底名排在 -99 之前, 会被当成最老删掉: {fallback.name} < {taken[-1].name}"
