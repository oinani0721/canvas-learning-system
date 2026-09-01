#!/usr/bin/env python3
"""CARD-G3-6b-R1 独立复核探针 — 卡文 (b) 四项，对 c2d2e590 原样字节实测。

不抄 UAT 自述：每项都自己构造输入、自己读结果、自己判定。
隔离：只读车道源码；全部写操作在 TemporaryDirectory；不碰 live vault / 7691。
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

LANE = Path("/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w6-whyboard")
# 被复核的 pick.py 字节：默认车道工作区当前字节；传 argv[1] 可指向任一副本
# （证据必须绑定明确的字节状态 —— R1 分别对 c2d2e590 原样字节与 R1 收窄后
# 字节各跑一次，两份输出各自归档，不混为一谈）。
PICK = Path(sys.argv[1]) if len(sys.argv) > 1 else LANE / "scripts" / "daily_review_pick.py"
MANIFEST = LANE / "scripts" / "review_rank_manifest.json"

RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str) -> None:
    RESULTS.append((name, bool(ok), detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}\n        {detail}")


def load_from(path: Path, modname: str):
    spec = importlib.util.spec_from_file_location(modname, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


FAKE_DECAY = SimpleNamespace(
    BETA_EXPLORE=1.0, FLOOR=0.05, GAMMA=0.9, GAMMA_DAILY=0.99, PRIOR_A=0.9, PRIOR_B=2.1
)
NOW = datetime(2026, 7, 30, 1, 0, tzinfo=timezone.utc)


def node(board: str, name: str, pick: float, last: str = "2026-07-25T01:00:00Z"):
    return {
        "board": board, "node": name, "pick": pick, "due_now": True,
        "idle_days": None, "difficulty": "", "fsrs_due": "",
        "due_fail_open": False, "last_examined": last,
    }


def sha_of(mod, decay=FAKE_DECAY, version=1, minutes=None, recorded=None) -> str:
    minutes = minutes if minutes is not None else dict(mod.DEFAULT_MINUTES)
    return mod.build_rank_manifest(decay, version, minutes, recorded or {})["sha256"]


def order_of(mod, nodes, blr=None):
    return [r["board"] for r in mod.rank_boards(nodes, blr or {}, NOW)[0]]


# ══════════════════════════════════════════════════════════════════════
def b1_precision_is_versioned(picker):
    """(b)-1 精度数据化：TIE_PICK_ROUND_DIGITS 8→7 必须让排序与 sha 同变。

    round-2 HIGH 的原攻击：收紧精度让 8 位可分的近邻 pick 变同分 → 板序翻转
    而 sha 恒为 879279ff…。构造近邻 pick：差值落在 1e-8 与 1e-7 之间。
    """
    # 近邻 pick 差 1e-8：round(_,8) 可分（B 先），round(_,7) 双双落到 0.2 而
    # 同分 → 退到 blr 级。差值取 5e-8 会失败（7 位下仍分成 0.2000001 vs 0.2），
    # 这是探针 fixture 自身的算术门槛，不是被测对象的性质。
    lo, hi = 0.20000000, 0.20000001
    nodes = [node("A板", "A", hi), node("B板", "B", lo)]
    # blr 让 A 板在 blr 级占优（有记录=罚后? 空串排最前 → B 无记录反而先）
    # 用 blr 使得同分时 A 先：给 B 一个 blr 记录，A 不给 → A 空串排前
    blr = {"B板": "2026-07-28"}

    o8 = order_of(picker, nodes, blr)
    s8 = sha_of(picker)
    orig = picker.TIE_PICK_ROUND_DIGITS
    try:
        picker.TIE_PICK_ROUND_DIGITS = 7
        o7 = order_of(picker, nodes, blr)
        s7 = sha_of(picker)
    finally:
        picker.TIE_PICK_ROUND_DIGITS = orig

    order_changed = o8 != o7
    sha_changed = s8 != s7
    check(
        "(b)-1 精度收紧 → 排序变",
        order_changed,
        f"digits=8 序={o8} / digits=7 序={o7}（近邻 pick {lo} vs {hi}）",
    )
    check(
        "(b)-1 精度收紧 → sha 同变（round-2 HIGH 的原漏网面）",
        sha_changed,
        f"sha8={s8[:16]}… sha7={s7[:16]}…",
    )
    check(
        "(b)-1 精度常量已登记进被摘要对象",
        picker.effective_rank_config(FAKE_DECAY, 1, dict(picker.DEFAULT_MINUTES))
        .get("tie_pick_round_digits") == 8,
        f"effective_rank_config.tie_pick_round_digits={picker.effective_rank_config(FAKE_DECAY, 1, dict(picker.DEFAULT_MINUTES)).get('tie_pick_round_digits')!r}",
    )


def b2_authoritative_three_layers(picker, tmp: Path):
    """(b)-2 authoritative 三层缺失/null/错型必须点名回落，不许静默。

    round-2 MEDIUM 的原漏网：{"version":1} / {"version":1,"authoritative":{}} /
    estimated_minutes:null 三种形状都静默返回默认且 stderr 为空。
    """
    import contextlib
    import io

    D = dict(picker.DEFAULT_MINUTES)
    # (label, 文档, 期望的**精确**回落值, 告警里必须点名的关键词)
    # R1 轮 Codex MEDIUM：原版只断言「stderr 非空」，把回落值和告警内容都放过了
    # —— 实现即便回落成错误的数字、或打一条不点名的告警，探针照样 PASS。
    cases = [
        ("父节整个缺失", {"version": 1}, D, ["authoritative", "内置默认"]),
        ("父节为空 object", {"version": 1, "authoritative": {}}, D,
         ["estimated_minutes", "内置默认"]),
        ("父节为 null", {"version": 1, "authoritative": None}, D,
         ["authoritative", "内置默认"]),
        ("子节为 null", {"version": 1, "authoritative": {"estimated_minutes": None}}, D,
         ["estimated_minutes", "内置默认"]),
        ("子节错型(list)", {"version": 1, "authoritative": {"estimated_minutes": []}}, D,
         ["estimated_minutes", "内置默认"]),
        ("半份叶键", {"version": 1, "authoritative": {"estimated_minutes": {"per_due_node": 7}}},
         {"per_due_node": 7, "per_new_node": D["per_new_node"]}, ["per_new_node"]),
    ]
    for label, doc, want_minutes, want_words in cases:
        f = tmp / f"m_{abs(hash(label))}.json"
        f.write_text(json.dumps(doc), encoding="utf-8")
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            version, minutes, _ = picker.load_rank_manifest(f)
        err = buf.getvalue()
        missing = [w for w in want_words if w not in err]
        ok = (minutes == want_minutes) and (version == 1) and not missing
        check(
            f"(b)-2 {label} → 回落值精确 + 告警点名",
            ok,
            f"minutes={minutes}（期望 {want_minutes}）version={version!r} "
            f"告警缺词={missing or '无'} stderr={err.strip()[:110]!r}",
        )


def b3_golden_bears_weight(picker):
    """(b)-3 金样锁承重：删掉首因子后板序必须翻转。

    round-2 MEDIUM 的原缺陷：低 pick 恰在字典序更早的 A板 → 删 pick 因子后
    序不变，门空转。修法是把低 pick 放到字典序更晚的板。
    """
    # 低 pick 在字典序更晚的 B板 → 默认 B 先；删首因子后按板名 A 先
    nodes = [node("A板", "A", 0.9), node("B板", "B", 0.1)]
    default = order_of(picker, nodes)
    orig = picker.TIE_FACTOR_KEYS
    try:
        picker.TIE_FACTOR_KEYS = ("board_last_recommended", "min_last_examined", "board")
        without = order_of(picker, nodes)
    finally:
        picker.TIE_FACTOR_KEYS = orig
    check(
        "(b)-3 pick 级承重：默认低 pick 先（B 板字典序更晚，排除板名碰巧决定）",
        default == ["B板", "A板"],
        f"默认序={default}",
    )
    check(
        "(b)-3 pick 级承重：删首因子后按板名翻转（门不空转）",
        without == ["A板", "B板"] and without != default,
        f"删 priority_pick 后序={without}",
    )


def b4_factor_key_uniqueness(picker):
    """(b)-4 因子唯一性：重复末级 board = 「sha 变而排序不变」。

    判定要点：这是**误报方向**（指纹过度敏感），不是漏网方向。安全性质
    「规则变⟹sha变」不受影响。故契约应写成单向保证；本探针实测该性质的
    实际方向，供契约措辞取据。
    """
    nodes = [node("A板", "A", 0.9), node("B板", "B", 0.1)]
    base_order = order_of(picker, nodes)
    base_sha = sha_of(picker)
    orig = picker.TIE_FACTOR_KEYS
    try:
        picker.TIE_FACTOR_KEYS = orig + ("board",)  # 追加重复末级
        dup_order = order_of(picker, nodes)
        dup_sha = sha_of(picker)
    finally:
        picker.TIE_FACTOR_KEYS = orig
    check(
        "(b)-4 重复键的实际方向 = sha 变而排序不变（误报方向，非漏网）",
        dup_order == base_order and dup_sha != base_sha,
        f"序 {base_order}→{dup_order}（不变={dup_order == base_order}） "
        f"sha {base_sha[:12]}…→{dup_sha[:12]}…（变={dup_sha != base_sha}）",
    )
    keys = orig
    check(
        "(b)-4 现常量本身唯一且 board 恒末位",
        len(set(keys)) == len(keys) and keys[-1] == "board",
        f"TIE_FACTOR_KEYS={keys}",
    )


def b5_value_binding_swap_is_caught(picker, tmp: Path):
    """(b)-附 取值绑定交换（无法数据化的字面代码）是否被 implementation_sha 兜住。

    round-2 HIGH 的第二个攻击面：不动 TIE_FACTOR_KEYS 的顺序，改 tie_parts
    里各键**对应的表达式**（交换 blr 与 min_last 的取值）→ 排序规则变了。
    模拟正常源码演进：改副本字节 → 看排序与 sha 是否同变。
    """
    src = PICK.read_text(encoding="utf-8")
    old = '"board_last_recommended": board_last_recommended.get(board, ""),'
    new_pair_a = '"board_last_recommended": min(n["last_examined"] for n in due),'
    old2 = '"min_last_examined": min(n["last_examined"] for n in due),'
    new_pair_b = '"min_last_examined": board_last_recommended.get(board, ""),'
    if old not in src or old2 not in src:
        check("(b)-附 取值绑定交换", False, "锚点未命中，探针失效（源码已变）")
        return
    mutated = src.replace(old, new_pair_a, 1).replace(old2, new_pair_b, 1)

    d = tmp / "swap"
    d.mkdir()
    p = d / "daily_review_pick.py"
    p.write_text(mutated, encoding="utf-8")
    swapped = load_from(p, "picker_swapped")

    # 构造 pick 平局、blr 与 min_last 优劣相反的输入
    nodes = [
        node("A板", "A", 0.2, last="2026-07-20T01:00:00Z"),  # min_last 更老
        node("B板", "B", 0.2, last="2026-07-28T01:00:00Z"),
    ]
    blr = {"A板": "2026-07-29"}  # A 有记录（排后），B 无记录（空串排前）
    o_base = order_of(picker, nodes, blr)
    o_swap = order_of(swapped, nodes, blr)
    # R1 轮 Codex MEDIUM：原版只比裸 _implementation_sha()，没证明它真的接进了
    # 最终对外的 rank_manifest.sha256 —— 实现即便把 impl_sha 算出来却不放进
    # 摘要对象（或放进去后被覆盖成常量），原探针照样 PASS。
    s_base_impl, s_swap_impl = picker._implementation_sha(), swapped._implementation_sha()
    s_base_rank, s_swap_rank = sha_of(picker), sha_of(swapped)
    cfg_base = picker.effective_rank_config(FAKE_DECAY, 1, dict(picker.DEFAULT_MINUTES))
    check(
        "(b)-附 交换取值绑定 → 排序规则确实改变",
        o_base != o_swap,
        f"原序={o_base} 交换后={o_swap}",
    )
    check(
        "(b)-附 交换取值绑定 → 裸 implementation_sha256 同变",
        s_base_impl != s_swap_impl,
        f"impl_sha {s_base_impl[:16]}… → {s_swap_impl[:16]}…",
    )
    check(
        "(b)-附 impl_sha 真的接入最终 rank_manifest.sha256（不只是算了不用）",
        s_base_rank != s_swap_rank
        and cfg_base.get("implementation_sha256") == s_base_impl,
        f"rank sha {s_base_rank[:16]}… → {s_swap_rank[:16]}…；"
        f"cfg.implementation_sha256 与裸值一致="
        f"{cfg_base.get('implementation_sha256') == s_base_impl}",
    )


def mk_min_vault(tmp: Path, name: str, nodes: dict) -> Path:
    """带 decay_beta 的最小 vault —— 与生产 scan_nodes 读的是同一种目录形态。"""
    import shutil

    vault = tmp / name
    (vault / ".claude" / "scripts").mkdir(parents=True)
    (vault / "节点").mkdir()
    shutil.copy(LANE / "canvas-vault" / ".claude" / "scripts" / "decay_beta.py",
                vault / ".claude" / "scripts")
    for stem, content in nodes.items():
        (vault / "节点" / f"{stem}.md").write_text(content, encoding="utf-8")
    return vault


def md_node(board="普通板", extra="") -> str:
    return f'---\ntype: concept\nsource_board: "[[原白板/{board}]]"\n{extra}---\n真实内容。\n'


def b6_manifest_authoritative_takes_effect(picker, tmp: Path):
    """(b)-附 authoritative「可改生效」/ recorded「只登记告警」——走生产入口。

    R1 轮 Codex MEDIUM：原版两条都只验了中间层（loader 的返回值、告警文字），
    没有走 build_payload —— 实现即便把 minutes 读出来却不往 payload 里传，
    或者 recorded 打完告警就用登记值覆盖实际值，原探针照样 PASS。
    """
    import contextlib
    import io

    vault = mk_min_vault(tmp, "prod_entry", {
        "甲": md_node(board="甲板"),                                   # 新卡
        "乙": md_node(board="甲板", extra="fsrs_due: 2026-07-01T01:00:00Z\n"),  # 已排期到期
    })
    decay = picker.load_decay(vault)

    mf = tmp / "auth_effective.json"
    mf.write_text(json.dumps({
        "version": 9,
        "authoritative": {"estimated_minutes": {"per_due_node": 11, "per_new_node": 13}},
    }), encoding="utf-8")

    version, minutes, _ = picker.load_rank_manifest(mf)
    check(
        "(b)-附 loader 层：authoritative 分钟读出正确",
        version == 9 and minutes == {"per_due_node": 11, "per_new_node": 13},
        f"version={version} minutes={minutes}",
    )

    # ── 生产入口：build_payload 落盘的 estimated_minutes 必须按 manifest 算
    payload, _ranked = picker.build_payload(vault, NOW, {}, decay, manifest_path=mf)
    tb = payload["top_boards"][0]
    f = tb["factors"]
    want = f["due_new"] * 13 + (f["due_total"] - f["due_new"]) * 11
    check(
        "(b)-附 生产入口：build_payload 落盘的分钟真按 manifest 算（不是只读不用）",
        tb["estimated_minutes"] == want and payload["rank_manifest"]["version"] == 9,
        f"落盘 estimated_minutes={tb['estimated_minutes']}（期望 {want}；"
        f"due_total={f['due_total']} due_new={f['due_new']} 用 11/13）"
        f" rank_manifest.version={payload['rank_manifest']['version']}",
    )

    # R1 round-2 Codex MEDIUM：上一条只绑了「实际分钟」，没绑「摘要用的那组分钟」——
    # 把 build_payload 里喂给 build_rank_manifest 的 minutes 换成 DEFAULT_MINUTES 而
    # 实际分钟仍用 11/13，探针照样全绿：payload 说 24 分钟，指纹却是 3/5 那份的。
    # 修法：独立复算「用 11/13 的 effective_rank_config」的 sha，要求它 (a) 等于
    # payload 落盘的 rank sha，(b) 不等于用默认分钟算出来的 sha。
    def _sha_of_cfg(mins: dict) -> str:
        cfg = picker.effective_rank_config(decay, 9, mins)
        blob = json.dumps(cfg, sort_keys=True, ensure_ascii=False, allow_nan=False)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    sha_actual = _sha_of_cfg({"per_due_node": 11, "per_new_node": 13})
    sha_default = _sha_of_cfg(dict(picker.DEFAULT_MINUTES))
    check(
        "(b)-附 落盘的 rank sha 与**实际生效的那组分钟**同源（不是默认分钟的摘要）",
        payload["rank_manifest"]["sha256"] == sha_actual != sha_default,
        f"payload.rank sha={payload['rank_manifest']['sha256'][:16]}… "
        f"用 11/13 复算={sha_actual[:16]}…（应相等）"
        f" 用默认 3/5 复算={sha_default[:16]}…（应不等）",
    )

    # ── recorded 漂移：既要出声，更要**行为以实际为准**
    mf2 = tmp / "recorded_drift.json"
    mf2.write_text(json.dumps({
        "version": 1,
        "authoritative": {"estimated_minutes": {"per_due_node": 3, "per_new_node": 5}},
        "recorded": {"limits": {"top_boards": 999, "upcoming": 999},
                     "ranking_factors": {"order": ["board", "priority_pick"]}},
    }), encoding="utf-8")
    _, m2, rec2 = picker.load_rank_manifest(mf2)
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        cfg = picker.effective_rank_config(decay, 1, m2)
        picker.build_rank_manifest(decay, 1, m2, rec2)
    err = buf.getvalue()
    behaviour_wins = (
        cfg["limits"] == {"top_boards": picker.TOP_BOARDS_LIMIT,
                          "upcoming": picker.UPCOMING_LIMIT}
        and cfg["ranking_factors"] == list(picker.TIE_FACTOR_KEYS)
    )
    check(
        "(b)-附 recorded 漂移 → 出声告警",
        "recorded.limits" in err and "999" in err,
        f"stderr={err.strip()[:140]!r}",
    )
    check(
        "(b)-附 recorded 漂移 → **行为**以实际为准（登记值没被拿去用）",
        behaviour_wins,
        f"生效 limits={cfg['limits']}（登记谎称 999）"
        f" 生效 factors={cfg['ranking_factors']}（登记谎称 ['board','priority_pick']）",
    )

    # R1 round-2 Codex MEDIUM：上一条只看不接收 recorded 的中间对象。让
    # recorded.limits.top_boards 真去控制截断后，探针照样全绿而四板入口输出
    # top_boards=4（代码常量是 3）。修法：**仅 recorded 不同**的两份 manifest
    # 各走一次四板生产入口，要求整份 payload 逐字相同、榜长精确为 3。
    v4 = mk_min_vault(tmp, "four_boards", {
        f"n{i}": md_node(board=f"{ch}板") for i, ch in enumerate("甲乙丙丁")
    })
    d4 = picker.load_decay(v4)
    honest = tmp / "rec_honest.json"
    honest.write_text(json.dumps({
        "version": 1,
        "authoritative": {"estimated_minutes": {"per_due_node": 3, "per_new_node": 5}},
        "recorded": {"limits": {"top_boards": 3, "upcoming": 3}},
    }), encoding="utf-8")
    lying = tmp / "rec_lying.json"
    lying.write_text(json.dumps({
        "version": 1,
        "authoritative": {"estimated_minutes": {"per_due_node": 3, "per_new_node": 5}},
        "recorded": {"limits": {"top_boards": 99, "upcoming": 99},
                     "ranking_factors": {"order": ["board"]}},
    }), encoding="utf-8")
    with contextlib.redirect_stderr(io.StringIO()):
        pay_h, rk_h = picker.build_payload(v4, NOW, {}, d4, manifest_path=honest)
        pay_l, rk_l = picker.build_payload(v4, NOW, {}, d4, manifest_path=lying)
    check(
        "(b)-附 生产入口：仅 recorded 不同 → 整份 payload 逐字相同、榜长恒为 3",
        pay_h == pay_l
        and len(pay_h["top_boards"]) == picker.TOP_BOARDS_LIMIT == 3
        and len(rk_h) == len(rk_l) == 4,
        f"payload 相同={pay_h == pay_l} 榜长={len(pay_h['top_boards'])}（谎称 99）"
        f" ranked 总数={len(rk_h)}（四板全在，截断只作用于榜）"
        f" 板序={[b['board'] for b in pay_h['top_boards']]}",
    )


def main() -> int:
    sys.path.insert(0, str(LANE / "scripts"))
    picker = load_from(PICK, "picker_under_test")
    print(f"复核对象: {PICK}")
    print(f"源码 sha256: {hashlib.sha256(PICK.read_bytes()).hexdigest()}")
    print(f"manifest sha256: {hashlib.sha256(MANIFEST.read_bytes()).hexdigest()}\n")

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        b1_precision_is_versioned(picker)
        b2_authoritative_three_layers(picker, tmp)
        b3_golden_bears_weight(picker)
        b4_factor_key_uniqueness(picker)
        b5_value_binding_swap_is_caught(picker, tmp)
        b6_manifest_authoritative_takes_effect(picker, tmp)

    passed = sum(1 for _, ok, _ in RESULTS if ok)
    total = len(RESULTS)
    print(f"\n{'=' * 60}\n复核结果: {passed}/{total} PASS")
    for name, ok, _ in RESULTS:
        if not ok:
            print(f"  ⛔ FAIL: {name}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
