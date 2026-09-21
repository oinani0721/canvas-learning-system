"""批次3' 2-4 统一学习事件日志契约锁定 (MEM-FLYWHEEL-2026-07-22)。

schema 四要素: event_id 幂等键 / event_version / recorded_at+effective_at
双时间戳 / 8 类白名单。写失败永不抛异常 (不炸主链)。
"""

import json

from app.services import learning_event_log as ev


def _patch_path(monkeypatch, tmp_path):
    monkeypatch.setattr(ev, "_log_path", lambda: tmp_path / "learning_events.jsonl")


def test_append_writes_full_schema(monkeypatch, tmp_path):
    _patch_path(monkeypatch, tmp_path)
    ok = ev.append_event(
        "candidate_disputed",
        event_id="dispute:c-1",
        node_id="Eigenvalues",
        payload={"dispute_reason": "这不是我的错误"},
    )
    assert ok
    rec = json.loads((tmp_path / "learning_events.jsonl").read_text().strip())
    for field in (
        "event_id",
        "event_version",
        "event_type",
        "node_id",
        "recorded_at",
        "effective_at",
        "payload",
    ):
        assert field in rec
    assert rec["event_version"] == 1
    assert rec["event_type"] == "candidate_disputed"


def test_idempotent_by_event_id(monkeypatch, tmp_path):
    _patch_path(monkeypatch, tmp_path)
    assert ev.append_event("answer_scored", event_id="quiz:e1")
    assert not ev.append_event("answer_scored", event_id="quiz:e1")  # 重放跳过
    lines = (tmp_path / "learning_events.jsonl").read_text().strip().splitlines()
    assert len(lines) == 1


def test_unknown_event_type_rejected(monkeypatch, tmp_path):
    _patch_path(monkeypatch, tmp_path)
    assert not ev.append_event("random_new_type", event_id="x-1")
    assert not (tmp_path / "learning_events.jsonl").exists()


def test_empty_event_id_rejected(monkeypatch, tmp_path):
    _patch_path(monkeypatch, tmp_path)
    assert not ev.append_event("answer_scored", event_id="")


def test_effective_at_can_backfill(monkeypatch, tmp_path):
    """补录历史事件: effective_at 与 recorded_at 分离。"""
    _patch_path(monkeypatch, tmp_path)
    ev.append_event(
        "session_archived",
        event_id="archive:s1",
        effective_at="2026-07-01T00:00:00+00:00",
    )
    rec = json.loads((tmp_path / "learning_events.jsonl").read_text().strip())
    assert rec["effective_at"] == "2026-07-01T00:00:00+00:00"
    assert rec["recorded_at"] != rec["effective_at"]


def test_io_failure_never_raises(monkeypatch):
    monkeypatch.setattr(ev, "_log_path", lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    assert not ev.append_event("answer_scored", event_id="quiz:e2")


# ── CARD-G3-3-R2-writer-boundary: event_id 字符轴形态门 ──
# ⛔ 放行面与拒绝面必须成对: 单有拒绝面时,「一律拒绝」也能全绿, 而那会让 5 个
# backend 调用点全部写不进账本。放行样本取自 2026-09-08 只读普查
# (_bmad-output/审查/evidence-g33r2/event-id-shapes-*.txt): 既有 regression 实参、
# 5 个生产调用点的拼法、以及 live 账本里真实存在的形态。

import logging

import pytest


@pytest.mark.parametrize(
    ("_eid", "_why"),
    [
        ("quiz:板A#q1", "quiz-answer 主形态 (regression 出现 23 次)"),
        ("x-1", "**无 type: 前缀** — 既有合法输入, 设计稿正则会拒掉它"),
        ("wrong", "同上, 纯字母无前缀"),
        ("exam:板B", "start-exam-board 形态, **无 # 段**"),
        ("derive:节点", "ai-linked-doc 形态, 中文 + 无 # 段"),
        ("archive:s1", "backend memory.py 调用点形态"),
        ("dispute:c-1", "backend errors.py 调用点形态"),
        ("cand:c-2", "backend conversation_distiller.py 调用点形态"),
        ("callout:cb-ms03p2v9bzhb", "live 账本真实值 (tips.py 调用点)"),
        ("archive:2fe93fcc-984a-4ae9-90f9-7fd247e2400f", "live 账本真实值 — uuid4"),
        ("exam:CS 61B-2026-08-11-1349", "live 账本真实值 — **含内部空格**"),
        ("exam:递归与分治 (Recursion & Divide-Conquer)-2026-07-24-0714", "live 真实值 — 中文+括号+&+空格"),
        ("quiz:特征值与特征向量-2026-07-25-0233#q1", "live 账本真实值 — 中文 + # 段"),
        ("derive:规划代理的特点", "live 账本真实值 — 纯中文"),
        ("a" * 512, "长度上边界 512 — 闭区间"),
    ],
)
def test_g33r2_event_id_shape_gate_allows_real_samples(monkeypatch, tmp_path, _eid, _why):
    """真实样本必须**全部放行**并落账 1 行 —— 形态门的验伪锚。"""
    _patch_path(monkeypatch, tmp_path)
    ledger = tmp_path / "learning_events.jsonl"
    assert ev._event_id_shape_problems(_eid) == [], f"⛔ 误拒真实样本 ({_why}): {_eid!r}"
    assert ev.append_event("answer_scored", event_id=_eid), f"⛔ 真实样本写不进去 ({_why}): {_eid!r}"
    assert len(ledger.read_text(encoding="utf-8").strip().splitlines()) == 1, f"须恰落 1 行 ({_why})"


@pytest.mark.parametrize(
    ("_eid", "_needle", "_why"),
    [
        ("quiz:x\n", "U+000A", "尾部换行 — 会把一行 JSONL 撕成两半"),
        (" quiz:x", "首尾含空白", "前导空格 — 与不带的各算一条 (双写账本 + 双吃 mastery)"),
        ("quiz:x ", "首尾含空白", "尾随空格 — 同上"),
        ("quiz:x\t", "U+0009", "尾部制表符 (既是 C0 也是首尾空白)"),
        ("a\x85b", "U+0085", "C1 NEL — 在终端里看起来就是个空格, 不报码点上游没法修"),
        ("a\x7fb", "U+007F", "DEL"),
        ("a\u2028b", "U+2028", "LINE SEPARATOR — 校验器禁止集里有, 窄了就是「写得进读不回」"),
        ("a\ufffeb", "U+FFFE", "Unicode noncharacter"),
        ("\ud800", "U+D800", "孤立代理 — utf-8 编码直接失败"),
        ("a" * 513, "过长", "长度越界 513"),
        (123, "必须是字符串", "非 str: int"),
        (b"quiz:x", "必须是字符串", "非 str: bytes"),
        (["quiz:x"], "必须是字符串", "非 str: list"),
        # ⚠️ `None` **不在**本组: 它是假值, 会被既有空判 `if not event_id` 先拒,
        # 形态门根本跑不到 —— 见下面 test_g33r2_falsy_id_is_rejected_by_the_earlier_gate。
        # 把它留在这里会让「绑定拒绝层」的断言在一个**本就该由别人拒**的输入上报红。
    ],
)
def test_g33r2_event_id_shape_gate_rejects(monkeypatch, tmp_path, caplog, _eid, _needle, _why):
    """形态非法 ⇒ `append_event` 返回 False + 账本**行数不变** + 拒因带码点/理由。

    ⛔ 判据绑定「被哪一层拒的」: `assert not append_event(...)` 是粗判据 ——
    未知 event_type、空 id、取锁超时都返回 False。

    ⚠️ **R1 整改**(Codex round-1 MEDIUM-4): 上一版查的是**另一次直接调用 helper**
    的返回值，那跟 `append_event` 这一次实际走了哪条分支**没有绑定关系**。实测反例:
    传 `None` 时 helper 报「必须是字符串」，而 `append_event` 早在既有空判
    `if not event_id` 就返回了 —— 本门根本没跑，旧断言照样全绿。
    现在改为断言 **`append_event` 自己打出来的那条 warning**（`caplog`）含本门的
    固定前缀与拒因，那句日志只在形态门这一条分支里产生。
    """
    _patch_path(monkeypatch, tmp_path)
    ledger = tmp_path / "learning_events.jsonl"
    # 先放一条合法行, 用「行数不变」而不是「文件不存在」当判据 ——
    # 后者对「先写后删」和「压根没跑到写」不可分辨。
    assert ev.append_event("answer_scored", event_id="quiz:seed-ok")
    _before = ledger.read_bytes()

    _problems = ev._event_id_shape_problems(_eid)
    assert _problems, f"⛔ 形态非法却判合规 ({_why}): {_eid!r}"
    assert any(_needle in p for p in _problems), (
        f"⛔ 拒了, 但拒因不含 {_needle!r} ({_why}) —— 报不出码点/理由上游没法修: {_problems}"
    )

    caplog.clear()
    with caplog.at_level(logging.WARNING, logger="app.services.learning_event_log"):
        _ok = ev.append_event("answer_scored", event_id=_eid)
    assert not _ok, f"⛔ 形态非法却写进去了 ({_why}): {_eid!r}"
    # ⛔ 承重处: 这一句只在形态门那条分支里打; 空判分支打的是「拒绝空 event_id」,
    # 未知类型分支打的是「拒绝未知 event_type」—— 三者互不相同, 故可分辨。
    _gate_logs = [r.getMessage() for r in caplog.records if "拒绝形态非法的 event_id" in r.getMessage()]
    assert _gate_logs, (
        f"⛔ 拒是拒了, 但**不是形态门**拒的 ({_why}) —— `append_event` 没打出形态门那句 warning, "
        f"说明它在更早的分支就返回了。实见日志: {[r.getMessage() for r in caplog.records]}"
    )
    assert any(_needle in m for m in _gate_logs), (
        f"⛔ 形态门跑了, 但它给出的拒因不含 {_needle!r} ({_why}): {_gate_logs}"
    )
    assert ledger.read_bytes() == _before, f"⛔ 拒绝路径动了账本 ({_why})"


@pytest.mark.parametrize("_falsy", [None, "", 0, [], {}, False])
def test_g33r2_falsy_id_is_rejected_by_the_earlier_gate(monkeypatch, tmp_path, caplog, _falsy):
    """假值 `event_id` 由**既有空判**拒（不是形态门）—— 分层如实钉住。

    ⛔ R1 整改（Codex round-1 MEDIUM-4）的另一半：那条意见让我发现，
    「都被拒了」并不等于「被我这道门拒了」。`if not event_id` 在形态门**之前**，
    所有假值都在那里返回，形态门跑不到。把这件事写成断言，而不是让它含混地
    藏在「反正 return False」里 —— 将来谁调换这两道门的顺序，这条会红。
    """
    _patch_path(monkeypatch, tmp_path)
    caplog.clear()
    with caplog.at_level(logging.WARNING, logger="app.services.learning_event_log"):
        assert not ev.append_event("answer_scored", event_id=_falsy), f"假值必须被拒: {_falsy!r}"
    _msgs = [r.getMessage() for r in caplog.records]
    assert any("拒绝空 event_id" in m for m in _msgs), f"应由**空判**拒: {_msgs}"
    assert not any("拒绝形态非法" in m for m in _msgs), (
        f"⛔ 假值走到了形态门 ⇒ 两道门的顺序变了，请同步更新本用例与上一条的分层说明: {_msgs}"
    )
    assert not (tmp_path / "learning_events.jsonl").exists(), "拒绝 ⇒ 零写"


def test_g33r2_event_id_shape_gate_never_raises(monkeypatch, tmp_path):
    """本函数的契约是「永不抛异常」—— 形态门不得把日志问题升级成主链故障。

    ⚠️ 样本更正（2026-09-08 实测）：初稿把 `"𐀀"[:1]` 当孤立代理写进拒绝集，
    实测**放行**。Python 3 的字符串按**码点**切片，`"𐀀"[:1]` 就是完整的 U+10000
    （CJK 扩展 B 的合法字符），门放行它是对的 —— 错的是样本，不是门。
    真正的孤立代理只能写成 `"\\ud800"`。这条更正留在这里，因为「以为切了半个
    代理对」是个很容易复制到下一张卡的误解。
    """
    _patch_path(monkeypatch, tmp_path)
    for _bad in (object(), 1.5, {"a": 1}, ("x",), b"\xff", "\ud800", "a\ud800b"):
        assert ev.append_event("answer_scored", event_id=_bad) is False, f"须返回 False 而不是抛: {_bad!r}"
    # 验伪锚：合法的非 BMP 字符必须**放行** —— 没有这一条，
    # 「凡是非 ASCII 一律拒」也能让上面全绿，而那会拒掉 live 里的中文 id。
    for _ok in ("𐀀", "emoji🎯:id", "derive:规划代理的特点"):
        assert ev._event_id_shape_problems(_ok) == [], f"⛔ 误拒合法非 BMP/中文 id: {_ok!r}"


def test_g33r2_shape_gate_charset_matches_validator():
    """形态门的禁止集与校验器 `FORBIDDEN_CODEPOINT_RANGES` **逐范围相等**。

    ⛔ 这道门是「独立定义 + 一致性门」这个设计的**全部承重处**。
    `backend/app/**` 至今不依赖 `backend/scripts/**`(全仓零先例), 所以
    `_EVENT_ID_FORBIDDEN_RANGES` 是重列的一份而不是 import 本体 —— 重列就必然
    会漂移, 除非有门盯着。

    ⛔ 方向也要钉死: 新门**窄于**校验器就留下「写得进、读不回」——
    一条含 U+2028 的 event_id 能被 append_event 写进账本, 而校验器读侧对该码点
    fail-closed 判的是**整个账本**不合规 ⇒ 那个 vault 从此所有评分都进不来
    (= `value_charset_problems` docstring 记的 round-1 BLOCKER 数据丢失路径)。
    """
    import importlib.util
    from pathlib import Path

    _v_path = Path(__file__).resolve().parents[2] / "scripts" / "validate_learning_events.py"
    assert _v_path.is_file(), f"校验器不在预期位置: {_v_path}"
    _spec = importlib.util.spec_from_file_location("_g33r2_validator", _v_path)
    _mod = importlib.util.module_from_spec(_spec)
    import sys as _sys

    _sys.modules["_g33r2_validator"] = _mod  # dataclass 自省需要 (Py3.14)
    _spec.loader.exec_module(_mod)

    _theirs = tuple(sorted(tuple(r) for r in _mod.FORBIDDEN_CODEPOINT_RANGES))
    _ours = tuple(sorted(tuple(r) for r in ev._EVENT_ID_FORBIDDEN_RANGES))
    assert _ours == _theirs, (
        "⛔ 两侧禁止集漂移了。校验器改了而 learning_event_log 没跟上 ⇒ "
        f"新门比校验器窄的部分就是「写得进读不回」的洞。\n"
        f"仅校验器有: {sorted(set(_theirs) - set(_ours))}\n"
        f"仅本门有:   {sorted(set(_ours) - set(_theirs))}"
    )
    # ⛔ 验伪锚: 上面的相等断言在**两侧都空**时同样成立(空真)。钉住集合非空
    # 且真的覆盖那几个关键码点, 免得「一起被清空」被读成「一致」。
    #
    # ⚠️ **R1 整改**(Codex round-1 MEDIUM-5b): 上一版的关键码点表漏了
    # `0xFDD0-0xFDEF` 这一段, 于是「**两侧同时**删掉那一段」这个变异下,
    # 「范围相等」与「关键码点都在」两条断言**同时**成立 —— 相等断言天生对
    # 「一起改」失明, 唯一的补救就是让这张表**逐段**覆盖禁止集的每一个来源段。
    # 现在按段列全: C0 / DEL / C1 / LS-PS / 代理区 / noncharacters(FDD0 族)
    # / 每平面末两码点(抽头中尾三个平面)。
    assert len(_ours) >= 6, f"禁止集不该这么小: {len(_ours)}"
    for _cp, _seg in (
        (0x0000, "C0 首"),
        (0x001F, "C0 尾"),
        (0x007F, "DEL"),
        (0x0080, "C1 首"),
        (0x0085, "C1/NEL"),
        (0x009F, "C1 尾"),
        (0x2028, "LS"),
        (0x2029, "PS"),
        (0xD800, "代理区首"),
        (0xDFFF, "代理区尾"),
        (0xFDD0, "noncharacter 族首"),
        (0xFDEF, "noncharacter 族尾"),
        (0xFFFE, "平面 0 末"),
        (0xFFFF, "平面 0 末"),
        (0x8FFFE, "平面 8 末"),
        (0x10FFFF, "平面 16 末"),
    ):
        assert any(lo <= _cp <= hi for lo, hi in _ours), (
            f"关键码点 U+{_cp:04X}（{_seg}）不在本门禁止集里 —— 该段整段消失了？"
        )
    # ⛔ 误拒方向的验伪锚: 禁止集不能宽到吃掉正常字符, 否则「一律拒绝」也能让上面全绿。
    for _cp, _why in ((0x0041, "ASCII A"), (0x4E2D, "中文 中"), (0x1F3AF, "emoji 🎯"), (0x20000, "CJK 扩展 B")):
        assert not any(lo <= _cp <= hi for lo, hi in _ours), (
            f"⛔ 正常字符 U+{_cp:04X}（{_why}）落进禁止集 ⇒ 会拒掉真实 id"
        )


def test_g33r2_shape_gate_agrees_with_validator_on_event_id():
    """同一个 event_id, 形态门与校验器 `value_charset_problems` **结论一致**。

    上一条比的是「集合」, 这一条比的是「行为」—— 集合相等而遍历逻辑写错
    (比如只查第一个字符) 时, 上一条照样绿。
    """
    import importlib.util
    import sys as _sys
    from pathlib import Path

    _v_path = Path(__file__).resolve().parents[2] / "scripts" / "validate_learning_events.py"
    _spec = importlib.util.spec_from_file_location("_g33r2_validator2", _v_path)
    _mod = importlib.util.module_from_spec(_spec)
    _sys.modules["_g33r2_validator2"] = _mod
    _spec.loader.exec_module(_mod)

    # ⚠️ **R1 整改**(Codex round-1 MEDIUM-5a): 上一版的非法样本全都把坏码点放在
    # **第 1-2 个字符**, 于是把遍历改成 `for ch in event_id[:7]` 这种截断实现,
    # 整组样本照样绿, 却会漏掉「坏码点在后面」的真实形态。
    # 下面每个非法样本都补一个**深位**孪生体（坏码点在 45 字符之后）。
    # ⛔ 不可见码点一律写 `\uXXXX` 转义而不是字面字符 —— 字面写法在编辑器/工具链
    # 里看不见, 一次无意的重新保存就能把它静默换成普通空格, 而测试依旧全绿。
    _deep = "quiz:" + "板" * 40 + "#q1"
    for _eid in (
        "quiz:板A#q1",
        "x-1",
        "exam:CS 61B-2026-08-11-1349",
        "derive:规划代理的特点",
        "a\u0085b",
        "a\u2028b",
        "a\ufffeb",
        "quiz:x\n",
        "a\u007fb",
        "emoji\U0001f3af",
        "\U00020000扩展",
        # 深位孪生体：坏码点在第 45+ 个字符 —— 截断式遍历会在这里分叉
        _deep + "\u0085tail",
        _deep + "\u2028tail",
        _deep + "\u007ftail",
        _deep + "\ufffetail",
        # 深位**合法**对照：同样长、同样位置放的是正常字符 ⇒ 两侧均须放行
        _deep + "正常tail",
    ):
        _ours = bool([p for p in ev._event_id_shape_problems(_eid) if "码点" in p])
        _theirs = bool(_mod.value_charset_problems({"event_id": _eid}))
        assert _ours == _theirs, (
            f"⛔ 字符轴结论分叉 {_eid!r}: 形态门 {'拒' if _ours else '放行'} / "
            f"校验器 {'拒' if _theirs else '放行'} —— 分叉的方向决定是误拒还是漏网"
        )
