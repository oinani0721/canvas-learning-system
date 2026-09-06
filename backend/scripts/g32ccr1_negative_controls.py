#!/usr/bin/env python3
"""CARD-CX-G3-2c-C-R1 负控：证明本卡新增/强化的门**承重**，不是绿着好看。

与 `g32cb_mutation_gates.py` 同一套防呆纪律（串行 / 无条件还原 / 信号也还原 /
全文件 sha 基线 / KILLED 判据是 `rc == 1` 且失败的是**指定的那一条**）。
分工不同：g32cb 守 §6.1 的四道防线，本脚本守 R1 卡的四个论断——

  E1/E2  emitter 门的**子串包含**判据（`assert _snap_A in nd_after`）挡不住
         「A 行被复制」与「A 行位移」：强化前两条都 SURVIVED，强化后都 KILLED。
         ⚠️ 两个变异都能过生产自身的 `_canon_tree` 逐条比较 —— dict 比较对
         **键序**与**重复键**都不敏感（PyYAML 对重复键取最后一个），所以这
         不是「构造一个不可能的状态」，而是真的会溜过去。
  E3     把 ("payload","question_id") 加进严格表，一致性门当场红（死条目）。
         ⚠️ 本条**只跑那一道指定门**，不能据此说「任何行为门都不变」
         （Codex round-1 MEDIUM）。「行为面不变」是另一次实证：同样的扩表下
         跑四回归文件，红的只有两道**表声明门**（339 → 2 failed/337 passed），
         证据记在 UAT §一.3。那次实证也只覆盖测试套件里的输入 ——
         `learning_event_log.append_event()` 能把这些键写进账本，届时扩表
         **会**改变拒绝面，所以裁定的依据是「当前没有写点写、没有读点读」。
  E4     receipt 侧的字符防线是 `q_()` 的**正面往返自证**，不是字符轴：拆掉
         它的往返判据，(b) 那道门立刻抓到「写得进读不回」。
  E5     (c) 门的 AST 前提（`record` 在 `validate_record_full` 里不重绑）真的
         在守着：插一次重绑就红。
  E6–E11 Codex round-1 逐条打回的「判据太粗」，整改后各自的靶：
         E6 条目末尾追加重复键 / E7 F1-only 成功出口坏掉 / E8 删 ts 词法判据 /
         E9 严格表清空（空真）/ E10 海象重绑 / E11 删字符遍历的 tuple 支持。
         ⚠️ 这六条在整改**前**全部 SURVIVED —— 它们不是补充，是打回项的验收。

用法：
  `python3 backend/scripts/g32ccr1_negative_controls.py`          跑全部
  `python3 backend/scripts/g32ccr1_negative_controls.py --list`   只列变异与锚点命中数（不改任何文件）
  `python3 backend/scripts/g32ccr1_negative_controls.py --only E1,E2`
"""

from __future__ import annotations

import hashlib
import os
import signal
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mutation_kill_identity import (  # noqa: E402  (必须在 sys.path 兜底之后)
    check_expect_msg_unique,
    failed_reasons,
    gate_hit,
    judge_env,
    judge_surface_missing,
    kill_identity_ok,
    syntax_check,
)

WT = Path(__file__).resolve().parents[2]
SKILL = WT / "canvas-vault" / ".claude" / "skills" / "quiz-answer" / "SKILL.md"
VALIDATOR = WT / "backend" / "scripts" / "validate_learning_events.py"
#: ⚠️ 不硬编码别的车道的 venv：先认环境变量，再回落本树 `backend/.venv`。
PYTEST = Path(os.environ.get("G32CCR1_PYTEST") or (WT / "backend" / ".venv" / "bin" / "pytest"))
LEDGER_TEST = "tests/regression/test_g3_2_review_ledger.py"

_EMITTER = "test_g32cc_emitter_rebuild_never_mutates_existing_entries"

#: (id, 说明, 目标文件, 原文本, 变异文本, 必须变红的测试)
MUTATIONS = [
    (
        "E1",
        "A 行被**复制**成两行（重复键，PyYAML 取最后一个 ⇒ 生产自检察觉不到）",
        SKILL,
        '                    _rebuilt.append(f"{_pfx}{_kq(_k)}: {q_(_e[_k])}")',
        '                    _rebuilt.append(f"{_pfx}{_kq(_k)}: {q_(_e[_k])}")\n'
        '                    if _k == "self_confidence_raw":  # MUTANT E1 A 行复制\n'
        '                        _rebuilt.append(f"    {_kq(_k)}: {q_(_e[_k])}")',
        _EMITTER,
    ),
    (
        "E2",
        "A 行**位移**（键序重排，行文本逐字节不变 ⇒ 子串包含判据看不见）",
        SKILL,
        "                _ks = list(_e.keys()) if isinstance(_e, dict) else []",
        '                _ks = ([_x for _x in _e.keys() if _x != "self_confidence_raw"]\n'
        '                       + ["self_confidence_raw"]) if isinstance(_e, dict) and "self_confidence_raw" in _e \\\n'
        "                    else (list(_e.keys()) if isinstance(_e, dict) else [])  # MUTANT E2 A 行位移",
        _EMITTER,
    ),
    (
        "E3",
        "把 receipt-only 字段**扩进**严格字段表（本卡裁定说这是空操作 ⇒ 一致性门必须当场认出死条目）",
        VALIDATOR,
        'CHARSET_STRICT_FIELDS: tuple[tuple[str, ...], ...] = (\n    ("event_id",),',
        "CHARSET_STRICT_FIELDS: tuple[tuple[str, ...], ...] = (  # MUTANT E3 扩表\n"
        '    ("payload", "question_id"),\n    ("event_id",),',
        "test_g32ccr1_charset_scope_is_bounded_by_ledger_record_reality",
    ),
    (
        "E4",
        "拆掉 `q_()` 的正面往返自证（非 ASCII 一律裸嵌 ⇒ receipt 里 U+0085 被 YAML 折成空格）",
        SKILL,
        '            if isinstance(_doc_rt, dict) and _doc_rt.get("v") == v:\n                return _lit',
        "            if True:  # MUTANT E4 拆掉往返自证\n                return _lit",
        "test_g32ccr1_receipt_only_fields_roundtrip_under_hostile_codepoints",
    ),
    (
        "E6",
        "A 条目**末尾追加**一个同值重复键（Codex round-1 MEDIUM：子串包含没有结束边界）",
        SKILL,
        "            _rebuilt.append(entry_)",
        '            if _rebuilt and _rebuilt[-1].strip().startswith("abandoned:"):  # MUTANT E6\n'
        "                _rebuilt.append(_rebuilt[-1])\n"
        "            _rebuilt.append(entry_)",
        _EMITTER,
    ),
    (
        "E7",
        "把 F1-only 的**成功出口**改成异常（Codex round-1 MEDIUM：只比 attempt 不增，拒绝也满足）",
        SKILL,
        '        print(f"[quiz-answer] {NODE}: event={eid} 已完整应用（receipt 事实一致且调度已覆盖）',
        '        raise SystemExit("MUTANT E7 F1-only 出口坏掉")\n'
        '        print(f"[quiz-answer] {NODE}: event={eid} 已完整应用（receipt 事实一致且调度已覆盖）',
        _EMITTER,
    ),
    (
        "E8",
        "删掉**本次输入 ts** 的词法判据（Codex round-1 MEDIUM：门同时污染两字段，被 review_time 那道喂饱）",
        SKILL,
        "if not isinstance(_ts_in, str) or not _TS_RE.fullmatch(_ts_in):",
        "if False:  # MUTANT E8 拆掉 ts 词法判据",
        "test_g32ccr1_timestamp_axis_rejects_hostile_codepoints_before_any_write",
    ),
    (
        "E9",
        "把严格字段表**清空**（Codex round-1 MEDIUM：上一版一致性门在空表上是空真）",
        VALIDATOR,
        "CHARSET_STRICT_FIELDS: tuple[tuple[str, ...], ...] = (\n"
        '    ("event_id",),\n'
        '    ("node_id",),\n'
        '    ("payload", "vault_id"),\n'
        '    ("payload", "concept_id"),\n'
        '    ("payload", "exam_board"),\n'
        ")",
        "CHARSET_STRICT_FIELDS: tuple[tuple[str, ...], ...] = ()  # MUTANT E9 清空严格表",
        "test_g32ccr1_charset_scope_is_bounded_by_ledger_record_reality",
    ),
    (
        "E10",
        "用**海象**重绑 record（Codex round-1 MEDIUM：上一版 AST 扫描漏掉 NamedExpr）",
        VALIDATOR,
        "    shape = value_shape_problems(record)",
        '    shape = value_shape_problems(record := b"x")  # MUTANT E10 海象重绑',
        "test_g32ccr1_nondict_branch_unreachable_from_validate_record_full",
    ),
    (
        "E11",
        "删掉字符遍历的 **tuple** 支持（Codex round-1 LOW：容器门声称覆盖 tuple 却没有 tuple 样本）",
        VALIDATOR,
        "                elif isinstance(cur, (list, tuple)):\n                    stack.extend(cur)",
        "                elif isinstance(cur, (list,)):  # MUTANT E11 删 tuple 支持\n                    stack.extend(cur)",
        "test_g32cc_charset_traverses_all_container_shapes",
    ),
    (
        "E5",
        "在 `validate_record_full` 里**重绑** `record`（(c) 门的不可达性推理前提失效）",
        VALIDATOR,
        "    shape = value_shape_problems(record)",
        "    record = dict(record)  # MUTANT E5 重绑 record\n    shape = value_shape_problems(record)",
        "test_g32ccr1_nondict_branch_unreachable_from_validate_record_full",
    ),
]


#: 每条变异**声称**会打红的那一条断言的消息片段（首行字面，门文件里恰好 1 次）。
#: 判据面 = `-rf` 短摘要的 reason（只取断言消息的第一行）。原判据
#: `rc == 1 and gate in out and "failed" in out` 对「红在别的断言」无免疫
#: —— 本仓已因此吃过两次假杀（CARD-DEBT-mutation-kill-identity）。
#:
#: ⚠️ 逐条绑定依据（先读门源码推出来，再由跑批证实/证伪）：
#:   E1 A 行被复制 ⇒ `nd_after.count(_snap_A) == 1` 那条；
#:   E2 A 行位移 / E6 条目末尾追加重复键 ⇒ 两者都改变**整条**而不改载体行的
#:      出现次数 ⇒ 都落在「整条逐字节，含结束边界」那条（同一条断言，两种形态，
#:      这正是 R1 补强要覆盖的两个盲区）；
#:   E3 扩表 / E9 清空表 ⇒ ⓪「严格表逐项钉死」那条断言排在函数最前面，
#:      **先于** ③ 的死条目检查 ⇒ 两者都落在 ⓪；⚠️ 于是 ③ 那条死条目判据
#:      当前**没有任何变异为它承重**（本卡新暴露，见验收单 §五）；
#:   E4 拆往返自证 ⇒ 裸形落盘 ⇒ YAML 折行 ⇒ 落在「写得进读不回」（question_id
#:      在前，先红）；
#:   E7 F1-only 出口坏掉 ⇒ 落在 ③ 段「恢复没有成功」那条；
#:   E8 删 ts 词法判据 ⇒ 仍被别的层拒但拒因不再点名 ts ⇒ 落在「拒因不是 … 那道门」；
#:   E10/E5 重绑 record ⇒ 落在 AST 前提「`record` 在函数体内被重新绑定」那条；
#:   E11 删 tuple 支持 ⇒ 落在容器遍历「漏检」那条。
EXPECT_MSG: dict[str, str] = {
    "E1": "⛔ A 的 receipt 载体行出现 ",
    "E2": "⛔ 追加 B 之后 A 那一条被改动了",
    "E3": "严格字段表变了 ⇒ 先重做差集再改本门: ",
    "E4": "⛔ question_id 写得进读不回: ",
    "E5": "在函数体内被重新绑定 ⇒ dict 保证失效: ",
    "E6": "⛔ 追加 B 之后 A 那一条被改动了",
    "E7": "⛔ 恢复没有成功（rc=",
    "E8": " 那道门（被更早的判据喂饱了）: ",
    "E9": "严格字段表变了 ⇒ 先重做差集再改本门: ",
    "E10": "在函数体内被重新绑定 ⇒ dict 保证失效: ",
    "E11": " 里的非规范码点漏检: ",
}

#: 显式豁免表 `{id: 具体理由}`。空 = 11 条全绑上了，没有欠账。
EXPECT_MSG_EXEMPT: dict[str, str] = {}


def _check_expect_msg() -> list[str]:
    """`EXPECT_MSG` 完整性 + 唯一性自检（共用实现，见 `mutation_kill_identity`）。

    ⚠️ 「唯一」判的是**这个片段在门文件里出现 1 次**，不是「每条变异各绑一条
    不同的断言」：E2/E6 与 E3/E9 各是两种不同形态打在**同一条**断言上，那是
    门本身的覆盖设计，不是绑重了。
    """
    gate_file = str(WT / "backend" / LEDGER_TEST)
    problems = check_expect_msg_unique(
        [(m[0], gate_file, EXPECT_MSG.get(m[0])) for m in MUTATIONS],
        exempt=EXPECT_MSG_EXEMPT,
        # ⛔ 片段还必须在生产侧命中 0 次（理由同 g32cb）。不收 `backend/scripts/`
        # 整目录：本文件自己在那儿，表里逐字写着这些片段 ⇒ 判据会自指。
        prod_roots=(WT / "canvas-vault", WT / "backend" / "app", VALIDATOR),
    )
    stale = sorted((set(EXPECT_MSG) | set(EXPECT_MSG_EXEMPT)) - {m[0] for m in MUTATIONS})
    if stale:
        problems.append(f"EXPECT_MSG/EXEMPT 里有已不存在的 id: {stale}")
    return problems


class _Terminated(Exception):
    """把 SIGTERM/SIGINT 转成异常，好让 finally 里的还原跑得到。"""


def _install_signal_handlers() -> None:
    def _handler(signum, _frame):
        raise _Terminated(f"收到信号 {signum}")

    for _sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(_sig, _handler)


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _nodeid(test_name: str) -> str:
    """门函数名 → pytest nodeid。判据比的是 nodeid，不是「门名字样在输出里」。"""
    return f"{LEDGER_TEST}::{test_name}"


def _run_gate(test_name: str) -> tuple[int, str]:
    env = dict(os.environ)
    # ⛔ judge_env() 覆盖在后：外层导出的 COLUMNS=80 会把 `-rf` 短摘要的 reason
    # 截成空串 ⇒ expect_msg 恒不命中 ⇒ 全报 SURVIVED（harness 坏了却像门失效）。
    env.update(judge_env())
    r = subprocess.run(
        # ⛔ `-rf` 不可省：击杀身份判据取的就是短摘要行 `FAILED <nodeid> - <reason>`。
        [str(PYTEST), "-q", "-p", "no:cacheprovider", "--tb=line", "-rf", _nodeid(test_name)],
        cwd=WT / "backend",
        capture_output=True,
        text=True,
        env=env,
        timeout=300,
    )
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def _self_heal() -> list[str]:
    healed = []
    for mid, _d, target, old, new, _g in MUTATIONS:
        src = target.read_text(encoding="utf-8")
        if new in src:
            target.write_text(src.replace(new, old, 1), encoding="utf-8")
            healed.append(f"{mid} @ {target.name}")
    return healed


def _anchor_audit() -> tuple[bool, list[tuple[str, int, str, str, str]]]:
    """锚点自检：每条变异的原文本必须在目标文件里**恰好命中 1 次**。

    ⚠️ 返回**逐条记录**而不是拼好的字符串行：锚错时一条变异要多印一行提示，
    拿 `zip(MUTATIONS, lines)` 去配描述就会错位（印到别人头上）。
    """
    rows, ok = [], True
    for mid, desc, target, old, _new, gate in MUTATIONS:
        n = target.read_text(encoding="utf-8").count(old)
        rows.append((mid, n, str(target.relative_to(WT)), gate, desc))
        if n != 1:
            ok = False
    return ok, rows


def _print_anchor_rows(rows, *, with_desc: bool) -> None:
    for mid, n, rel, gate, desc in rows:
        print(f"  [{mid}] 锚命中 {n} 次 @ {rel} → {gate}", flush=True)
        if n != 1:
            print("       ⛔ 须恰好 1 次 —— 锚文本漂了（缩进/改名），变异会静默失配", flush=True)
        if with_desc:
            print(f"       {desc}", flush=True)


def main(argv: list[str]) -> int:
    only = None
    for a in argv[1:]:
        if a == "--list":
            ok, rows = _anchor_audit()
            print("═══ 变异清单与锚点自检 ═══")
            _print_anchor_rows(rows, with_desc=True)
            for p in _check_expect_msg():
                print(f"  ⛔ EXPECT_MSG 自检: {p}")
                ok = False
            return 0 if ok else 4
        if a.startswith("--only"):
            only = set((a.split("=", 1)[1] if "=" in a else argv[argv.index(a) + 1]).split(","))
    muts = [m for m in MUTATIONS if only is None or m[0] in only]
    if not muts:
        print(f"⛔ --only 没选中任何变异: {only}")
        return 4

    # ⛔ EXPECT_MSG 自检**先于**一切慢步骤：绑不唯一 ⇒ 「红在哪一条断言上」不再可证。
    if bad := _check_expect_msg():
        for p in bad:
            print(f"⛔ EXPECT_MSG 自检失败 — {p}", flush=True)
        return 4

    _install_signal_handlers()
    healed = _self_heal()
    if healed:
        print(f"⚠️ 自愈：还原了上一次残留的变异体 {healed}", flush=True)

    ok, rows = _anchor_audit()
    print("═══ 锚点自检（先于一切慢步骤）═══", flush=True)
    _print_anchor_rows(rows, with_desc=False)
    if not ok:
        print("⛔ 锚点自检不通过 —— 中止（不跑变异，避免 8/8 KILLED 式假绿）", flush=True)
        return 4

    touched = sorted({m[2] for m in muts}, key=str)
    baseline = {p: _sha(p) for p in touched}
    print("\n═══ 变异前 sha 基线 ═══", flush=True)
    for p, h in baseline.items():
        print(f"  {h}  {p.relative_to(WT)}", flush=True)

    print("\n═══ 绿态前提（变异前每道门必须绿）═══", flush=True)
    for mid, _d, _f, _o, _n, gate in muts:
        rc, _out = _run_gate(gate)
        print(f"  [{mid}] {gate} → rc={rc} {'✅' if rc == 0 else '❌ 前提不成立'}", flush=True)
        if rc != 0:
            print(f"⛔ {mid} 的门在变异前就不是绿的，变异结果无意义。中止。", flush=True)
            return 2

    results = []
    print("\n═══ 变异（串行）═══", flush=True)
    for mid, desc, target, old, new, gate in muts:
        src = target.read_text(encoding="utf-8")
        if src.count(old) != 1:
            print(f"  [{mid}] ⛔ 锚文本命中 {src.count(old)} 次 — 跳过", flush=True)
            results.append((mid, gate, "ANCHOR-ERROR", desc))
            continue
        mutated_text = src.replace(old, new, 1)
        # ⛔ 先编译自检，再跑门：语法不合法的变异体让被测进程在**编译期**就死，
        # 「防线拆掉后本该发生的坏事」根本没机会发生，门却因**别的断言**红而被记
        # KILLED（Z2 的 M15 形态）。它照出的是负控自己坏了 —— 单列第三种裁决。
        if syn := syntax_check(target, mutated_text):
            print(f"  [{mid}] ⛔ SYNTAX-INVALID 变异体编译不过 — {syn}", flush=True)
            results.append((mid, gate, "SYNTAX-INVALID", desc))
            continue
        try:
            target.write_text(mutated_text, encoding="utf-8")
            rc, out = _run_gate(gate)
            nodeid = _nodeid(gate)
            expect = EXPECT_MSG.get(mid)
            if surface := judge_surface_missing(rc, out):
                print(f"  [{mid}] ⛔ 判据面不成立 — {surface}", flush=True)
                results.append((mid, gate, "JUDGE-SURFACE-MISSING", desc))
                continue
            # KILLED 判据：rc 恰为 1 **且** 失败的是指定的那道门 **且** 红在
            # `EXPECT_MSG[mid]` 声称的那一条断言上。
            killed = kill_identity_ok(rc, out, nodeid, expect)
            verdict = "KILLED" if killed else f"SURVIVED(rc={rc})"
            print(f"  [{mid}] {desc}\n        {gate} → rc={rc} ⇒ {verdict}", flush=True)
            if not killed:
                obs = [r for nid, r in failed_reasons(out) if gate_hit(nodeid, {nid})]
                print(f"        ⚠️ expect={expect!r}", flush=True)
                print(f"        ⚠️ 该门实际拒因: {obs or '(该门没红)'}", flush=True)
                tail = out.strip().splitlines()[-1][:160] if out.strip() else "(空)"
                print(f"        ⚠️ 输出尾部: {tail}", flush=True)
            results.append((mid, gate, verdict, desc))
        finally:
            target.write_text(src, encoding="utf-8")

    print("\n═══ 变异后 sha 复核 ═══", flush=True)
    dirty = []
    for p, h0 in baseline.items():
        h1 = _sha(p)
        print(f"  {'✅' if h0 == h1 else '⛔'} {p.relative_to(WT)}  {h1}", flush=True)
        if h0 != h1:
            dirty.append(p)

    print("\n═══ 汇总 ═══", flush=True)
    for mid, gate, verdict, _d in results:
        print(f"  {mid:4} {verdict:22} {gate}", flush=True)
    n_killed = sum(1 for _, _, v, _ in results if v == "KILLED")
    n_anchor = sum(1 for _, _, v, _ in results if v == "ANCHOR-ERROR")
    n_syntax = sum(1 for _, _, v, _ in results if v == "SYNTAX-INVALID")
    print(f"\n  {n_killed}/{len(muts)} KILLED", flush=True)
    # ⛔ 两者都**不是**关于被测物的结论：ANCHOR-ERROR 是变异没打进去，
    # SYNTAX-INVALID 是负控自己坏了。单列，不并进 KILLED / SURVIVED 任何一边。
    print(f"  ANCHOR-ERROR: {n_anchor} (变异未施加)", flush=True)
    print(f"  SYNTAX-INVALID: {n_syntax} (>0 说明负控自己坏了)", flush=True)
    if dirty:
        print(f"⛔ 有文件未还原：{[str(p) for p in dirty]}", flush=True)
        return 3
    return 0 if n_killed == len(muts) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
