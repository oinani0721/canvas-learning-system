#!/usr/bin/env python3
"""CARD-G3-2b 裁判 2：Codex round-3 残留 R1-R7 的生产入口反例复现（卡内安全脚本）。

[BATCH-2026-09-01-第九批 / CARD-G3-2b]

与 pytest 门**互为独立证据**：本脚本不经 pytest，直接把逐字提取的生产 PYEOF
写点丢进 tmp fixture 跑，打印每条反例的真实 rc 与判据命中情况。审查者可原样
复跑，不必信任任何绿门的自述。

安全边界（同 g32b_build_fixture.py）：写入面只有
`/private/tmp/card-g3-2b-fixture/counterexamples`；生产文件一律 symlink 只读
引用；无网络、无 DB、不触碰 live vault。
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

FIXTURE_ROOT = Path("/private/tmp/card-g3-2b-fixture")
CE_ROOT = FIXTURE_ROOT / "counterexamples"
MARKER = ".g32b-fixture-marker"
WT = Path(__file__).resolve().parents[2]
SKILL = WT / "canvas-vault" / ".claude" / "skills" / "quiz-answer" / "SKILL.md"
VAULT_SCRIPTS = WT / "canvas-vault" / ".claude" / "scripts"
VALIDATOR = WT / "backend" / "scripts" / "validate_learning_events.py"
SCHEMA_DOC = WT / "docs" / "learning-events-schema-v1.md"

NODE_REL = "节点/测试节点.md"
TS1 = "2026-08-01T10:00:00Z"
EID = "测试检验-2026-08-01-1000#q1"
NODE_V0 = (
    '---\ntype: concept\nmastery_score: 0.5\ntitle: 测试节点\nsource_board: "[[原白板/CS 61B]]"\n---\n测试节点正文。\n'
)
#: 含 idle 状态 + W 远晚于评分时刻（A3 把 review_time 推到 W+1s）
NODE_IDLE_A3 = (
    "---\ntype: concept\nmastery_score: 0.5\nmastery_a: 3.0\nmastery_b: 3.0\n"
    'attempt_count: 2\nlast_examined: "2026-07-01T00:00:00Z"\n'
    "fsrs_due: 2026-12-11T13:56:58Z\nfsrs_state: 2\nfsrs_stability: 10.0\n"
    "fsrs_difficulty: 5.0\nfsrs_last_review: 2026-12-01T10:00:00Z\ntitle: 测试节点\n"
    "---\n测试节点正文。\n"
)
CONFIG = '# CARD-G3-2b fixture\nvault_id: "canvas-vault-测试"\nsubject: cs-61b\n'

_TEXT = SKILL.read_text(encoding="utf-8")
_BLOCKS = [
    b
    for b in re.findall(r"python3 - <<'PYEOF'\n(.*?)\nPYEOF", _TEXT, re.DOTALL)
    if 'P = "/tmp/quiz-answer-payload.json"' in b
]
if len(_BLOCKS) != 1:
    sys.exit(f"[g32b-ce] SKILL.md 应恰有 1 个主写点 PYEOF 块, 实见 {len(_BLOCKS)} — 拒跑")
CODE = _BLOCKS[0]


def new_vault(tag: str, node_text: str = NODE_V0) -> Path:
    vault = CE_ROOT / tag / "repo" / "canvas-vault"
    repo = vault.parent
    (vault / "节点").mkdir(parents=True)
    (vault / ".claude" / "scripts").mkdir(parents=True)
    (repo / "backend" / "scripts").mkdir(parents=True)
    (repo / "backend" / ".venv").symlink_to(WT / "backend" / ".venv", target_is_directory=True)
    (repo / "backend" / "scripts" / "validate_learning_events.py").symlink_to(VALIDATOR)
    (vault / ".claude" / "scripts" / "fsrs_bridge.py").symlink_to(VAULT_SCRIPTS / "fsrs_bridge.py")
    (vault / ".claude" / "scripts" / "decay_beta.py").symlink_to(VAULT_SCRIPTS / "decay_beta.py")
    (vault / ".canvas-config.yaml").write_text(CONFIG, encoding="utf-8")
    (vault / NODE_REL).write_text(node_text, encoding="utf-8")
    return vault


def run(vault: Path, **over):
    payload = {
        "node": NODE_REL,
        "grade_norm": 0.752,
        "ts": TS1,
        "event_id": EID,
        "exam_board": "检验白板/测试检验-2026-08-01-1000.md",
        "question_id": "q1",
        "source_board": "[[原白板/CS 61B]]",
        "self_confidence_raw": "半懂",
        "self_confidence_norm": 0.5,
        "abandoned": False,
        "callout": "",
    }
    payload.update(over)
    pfile = vault.parent / "payload.json"
    pfile.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return subprocess.run(
        [sys.executable, "-c", CODE.replace('"/tmp/quiz-answer-payload.json"', json.dumps(str(pfile)))],
        capture_output=True,
        text=True,
        timeout=180,
        cwd=str(vault),
        env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
    )


def rows(vault: Path):
    p = vault / "learning_events.jsonl"
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []


def write_rows(vault: Path, *recs, trailing_lf=True):
    text = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in recs)
    (vault / "learning_events.jsonl").write_text(text if trailing_lf else text[:-1], encoding="utf-8")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def fsrs_fields(vault: Path) -> dict:
    fm = (vault / NODE_REL).read_text(encoding="utf-8").split("---\n")[1]
    out = {}
    for k in ("fsrs_due", "fsrs_state", "fsrs_stability", "fsrs_difficulty", "fsrs_last_review"):
        m = re.search(rf'^{k}:\s*"?([^"\n]+?)"?\s*$', fm, re.M)
        if m:
            out[k] = m.group(1)
    return out


def last_line(text: str) -> str:
    lines = text.strip().splitlines()
    return lines[-1][:110] if lines else ""


RESULTS: list[tuple[str, bool, str]] = []


def check(tag: str, ok: bool, detail: str) -> None:
    RESULTS.append((tag, ok, detail))
    print(f"  [{'PASS' if ok else 'FAIL'}] {tag}: {detail}")


def r1():
    print("\n── R1 (BLOCKER) durable payload 未知额外键 → 必须 envelope 冲突 ──")
    v = new_vault("r1")
    assert run(v).returncode == 0
    base = rows(v)[0]
    # ⚠️ `out_of_order` 现被更早的语义门接管 (见 n1_n5 的 N1) —— 只有**合法
    # 乱序形态** (review_time ≤ W) 的该键才会走到 envelope 门。保 W 不回滚地
    # 测它, R1 的原始穿透链仍被覆盖: 本次评分事实里没有这个键, 键集不等即冲突。
    base_oo = json.loads(json.dumps(base))
    base_oo["payload"]["out_of_order"] = True  # review_time == W ⇒ 合法乱序
    write_rows(v, base_oo)
    r_oo = run(v, ts="2026-09-01T07:00:00Z")
    check(
        "R1/out_of_order (合法乱序形态, 走 envelope 门)",
        r_oo.returncode != 0 and "envelope 冲突" in r_oo.stderr and len(rows(v)) == 1,
        f"rc={r_oo.returncode} 账本={len(rows(v))}行 | {last_line(r_oo.stderr)}",
    )
    for key, val, desc in (("note", "外部注入", "任意未知键"),):
        (v / NODE_REL).write_text(NODE_V0, encoding="utf-8")  # 崩溃窗口①
        t = json.loads(json.dumps(base))
        t["payload"][key] = val
        write_rows(v, t)
        r = run(v)
        check(
            f"R1/{desc}",
            r.returncode != 0 and "envelope 冲突" in r.stderr,
            f"rc={r.returncode} fsrs_fields={fsrs_fields(v) or '{}'} 账本={len(rows(v))}行 | {last_line(r.stderr)}",
        )
    (v / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    t = json.loads(json.dumps(base))
    t["payload"].pop("exam_board")
    write_rows(v, t)
    r = run(v)
    check("R1/缺固定生产键", r.returncode != 0 and "envelope 冲突" in r.stderr, f"rc={r.returncode}")
    (v / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    write_rows(v, base)
    r = run(v)
    check(
        "R1/验伪-原样行仍可恢复",
        r.returncode == 0 and fsrs_fields(v).get("fsrs_last_review") == TS1,
        f"rc={r.returncode} W={fsrs_fields(v).get('fsrs_last_review')}",
    )


def r2():
    print("\n── R2 (BLOCKER) 小数秒 / 非 UTC durable review_time → 必须 fail-closed ──")
    for bad, why in (("2026-08-01T10:00:00.500Z", "小数秒"), ("2026-08-01T18:00:00+08:00", "非 UTC")):
        v = new_vault(f"r2-{why}")
        assert run(v).returncode == 0
        base = rows(v)[0]
        (v / NODE_REL).write_text(NODE_V0, encoding="utf-8")
        t = json.loads(json.dumps(base))
        t["payload"]["review_time"] = bad
        t["effective_at"] = bad
        write_rows(v, t)
        s = sha(v / NODE_REL)
        r = run(v)
        check(
            f"R2/{why}-dup路径",
            r.returncode != 0 and why in r.stderr and sha(v / NODE_REL) == s,
            f"rc={r.returncode} 节点零写={sha(v / NODE_REL) == s} | {last_line(r.stderr)}",
        )
        rf = run(v, event_id="板B#q1", ts="2026-08-02T10:00:00Z")
        check(
            f"R2/{why}-foreign pending 路径",
            rf.returncode != 0 and why in rf.stderr and len(rows(v)) == 1,
            f"rc={rf.returncode} 账本={len(rows(v))}行",
        )


def r3():
    print("\n── R3 (HIGH) E1→E2→重跑 E1 → 必须 no-op, 不得误报冲突 ──")
    v = new_vault("r3")
    assert run(v).returncode == 0
    assert run(v, event_id="板B#q1", ts="2026-08-02T10:00:00Z", exam_board="检验白板/板B.md").returncode == 0
    atts = [x["payload"]["attempt_count"] for x in rows(v)]
    s = sha(v / NODE_REL)
    r = run(v, ts="2026-09-01T12:00:00Z")  # 原样重跑 E1
    check(
        "R3/历史事件重跑",
        r.returncode == 0 and "幂等跳过" in r.stdout and sha(v / NODE_REL) == s and len(rows(v)) == 2,
        f"durable attempts={atts} rc={r.returncode} 节点未改={sha(v / NODE_REL) == s} "
        f"账本={len(rows(v))}行 | {last_line(r.stdout)[:90]}",
    )
    rf = run(v, ts="2026-09-01T12:00:00Z", abandoned=True)
    check("R3/验伪-换事实仍冲突", rf.returncode != 0 and "envelope 冲突" in rf.stderr, f"rc={rf.returncode}")


def r4():
    print("\n── R4 (HIGH) 含 idle + A3 bump: 正常与恢复产物必须逐字节相同 ──")
    v = new_vault("r4", NODE_IDLE_A3)
    assert run(v).returncode == 0
    golden = (v / NODE_REL).read_bytes()
    rt = rows(v)[0]["payload"]["review_time"]
    (v / NODE_REL).write_text(NODE_IDLE_A3, encoding="utf-8")  # 崩溃窗口①
    r = run(v, ts="2026-09-15T09:30:00Z")
    same = (v / NODE_REL).read_bytes() == golden
    check(
        "R4/字节对拍",
        r.returncode == 0 and same and len(rows(v)) == 1,
        f"review_time={rt} (payload ts={TS1}) rc={r.returncode} 字节相同={same} "
        f"正常sha={hashlib.sha256(golden).hexdigest()[:12]} 恢复sha={sha(v / NODE_REL)[:12]}",
    )


def _pending_row(**over):
    row = {
        "event_id": "quiz:板A#q1",
        "event_version": 1,
        "event_type": "answer_scored",
        "node_id": "测试节点",
        "recorded_at": TS1,
        "effective_at": TS1,
        "payload": {
            "schema_ext": "review/1",
            "vault_id": "canvas_vault_测试",
            "concept_id": "测试节点",
            "rating": 3,
            "grade_norm": 0.75,
            "review_time": TS1,
            "fsrs_library_version": "degraded:historic-run",
            "fsrs_params_hash": "degraded:historic-run",
            "exam_board": "检验白板/板A.md",
            "attempt_count": 1,
        },
    }
    row["payload"].update(over)
    return row


def r5():
    print("\n── R5 (HIGH) scored rating 与 grade_norm 不自洽 → apply 前必须拒绝 ──")
    v = new_vault("r5")
    s = sha(v / NODE_REL)
    for bad in (4, 2):
        write_rows(v, _pending_row(rating=bad))
        r = run(v, event_id="板B#q1", ts="2026-08-02T10:00:00Z")
        check(
            f"R5/rating={bad} vs grade_norm=0.75(契约3)",
            r.returncode != 0 and "不自洽" in r.stderr and sha(v / NODE_REL) == s and len(rows(v)) == 1,
            f"rc={r.returncode} 账本={len(rows(v))}行 零写={sha(v / NODE_REL) == s} | {last_line(r.stderr)}",
        )
    write_rows(v, _pending_row())
    r = run(v, event_id="板B#q1", ts="2026-08-02T10:00:00Z")
    check("R5/验伪-契约值3 照常重放", r.returncode == 0 and len(rows(v)) == 2, f"rc={r.returncode}")


def r6():
    print("\n── R6 (MEDIUM) 身份键归属与 candidate 构造裁决必须回写冻结 schema §6.2 ──")
    doc = SCHEMA_DOC.read_text(encoding="utf-8")
    seg = doc[doc.index("duplicate 命中后的状态推进门") : doc.index("**A5 整秒精度")]
    missing = [
        n
        for n in (
            "fsrs_library_version",
            "fsrs_params_hash",
            "排除出 envelope 等价面",
            "golden manifest 绑定门",
            "candidate 必须独立字面构造",
            "多一键、少一键或值不同",
        )
        if n not in seg
    ]
    check("R6/§6.2 duplicate 门段落", not missing, f"缺失条款={missing or '无'}")
    a5 = doc[doc.index("**A5 整秒精度") : doc.index("**三态语义")]
    check("R6/§6.2 A5 消费侧强制", "A2 消费侧同样机械强制" in a5 and "禁止消费时顺手归一化" in a5, "已回写")
    check("R6/§6.2 A4.5 截断判据", "可容忍的截断 vs 完整损坏" in doc and "不以 LF 结尾" in doc, "已回写")


def r7():
    print("\n── R7 (MEDIUM) 坏末行: 带 LF = 完整损坏(拒) / 无 LF = 截断(容忍) ──")
    v = new_vault("r7")
    good = _pending_row(review_time="2026-07-01T10:00:00Z")
    good["event_id"] = "quiz:旧板"
    good["effective_at"] = "2026-07-01T10:00:00Z"
    good["node_id"] = "别的节点"
    bad = '{"event_id": "quiz:损坏行", "event_version": 1, "event_type": "answer_sc'
    ledger = v / "learning_events.jsonl"
    ledger.write_text(json.dumps(good, ensure_ascii=False) + "\n" + bad + "\n", encoding="utf-8")
    s = sha(v / NODE_REL)
    r = run(v)
    check(
        "R7/坏末行带终止 LF → fail-closed",
        r.returncode != 0 and "完整写入的损坏行" in r.stderr and sha(v / NODE_REL) == s,
        f"rc={r.returncode} 零写={sha(v / NODE_REL) == s} | {last_line(r.stderr)}",
    )
    ledger.write_text(json.dumps(good, ensure_ascii=False) + "\n" + bad, encoding="utf-8")
    rf = run(v)
    lines = [x for x in ledger.read_text(encoding="utf-8").splitlines() if x.strip()]
    check(
        "R7/同一坏行去掉 LF → 仍按截断隔离",
        rf.returncode == 0 and "截断尾行" in rf.stdout and len(lines) == 3,
        f"rc={rf.returncode} 账本={len(lines)}行 (坏行隔离, 新事件独立成行)",
    )


def n1_n5():
    """round-1 后续：Codex 正文被内容过滤器拦下，按 stderr 保留的推理标题线索
    逐条实测出的五个残留面（4 条复现为真缺陷 + 1 条诊断不精确）。"""
    print("\n── N1 (BLOCKER) 标 out_of_order 但 review_time > W：被伪装成乱序的真实后继 ──")
    v = new_vault("n1")
    late = _pending_row(out_of_order=True, review_time="2026-08-05T10:00:00Z")
    late["effective_at"] = "2026-08-05T10:00:00Z"
    write_rows(v, late)
    s = sha(v / NODE_REL)
    r = run(v, event_id="板B#q1", ts="2026-08-02T10:00:00Z")
    check(
        "N1/伪装成乱序的后继",
        r.returncode != 0 and "伪装成乱序的真实后继" in r.stderr and sha(v / NODE_REL) == s,
        f"rc={r.returncode} 零写={sha(v / NODE_REL) == s} | {last_line(r.stderr)}",
    )
    for bad in (False, "true", 1):
        write_rows(v, _pending_row(out_of_order=bad))
        rb = run(v, event_id="板B#q1", ts="2026-08-02T10:00:00Z")
        check(f"N1/形态 {bad!r} 非法", rb.returncode != 0 and "形态非法" in rb.stderr, f"rc={rb.returncode}")
    (v / "learning_events.jsonl").unlink()
    assert run(v).returncode == 0
    early = _pending_row(out_of_order=True, review_time="2026-07-01T10:00:00Z")
    early["effective_at"] = "2026-07-01T10:00:00Z"
    early["event_id"] = "quiz:补录旧事件"
    write_rows(v, rows(v)[0], early)
    ro = run(v, event_id="板C#q1", ts="2026-08-03T10:00:00Z")
    check(
        "N1/验伪-合法乱序 (review_time ≤ W) 放行且不推进 W",
        ro.returncode == 0 and fsrs_fields(v).get("fsrs_last_review") == "2026-08-03T10:00:00Z",
        f"rc={ro.returncode} W={fsrs_fields(v).get('fsrs_last_review')}",
    )

    print("\n── N2 (HIGH) EOF 的 LF 判据必须落在字节上（文本模式会把裸 \\r 读成 \\n）──")
    v = new_vault("n2")
    good = _pending_row(review_time="2026-07-01T10:00:00Z")
    good["event_id"] = "quiz:旧板"
    good["effective_at"] = "2026-07-01T10:00:00Z"
    good["node_id"] = "别的节点"
    torn = '{"event_id": "quiz:损坏行", "event_ty'
    head = (json.dumps(good, ensure_ascii=False) + "\n").encode("utf-8") + torn.encode("utf-8")
    (v / "learning_events.jsonl").write_bytes(head + b"\r")
    r = run(v)
    check(
        "N2/裸 \\r 结尾按字节算截断",
        r.returncode == 0 and "截断尾行" in r.stdout,
        f"rc={r.returncode} | {last_line(r.stdout)[:90]}",
    )
    (v / "learning_events.jsonl").write_bytes(head + b"\r\n")
    rb = run(v, event_id="板D#q1", ts="2026-08-04T10:00:00Z")
    check(
        "N2/对照-真带 LF 仍 fail-closed",
        rb.returncode != 0 and "完整写入的损坏行" in rb.stderr,
        f"rc={rb.returncode}",
    )

    print("\n── N3 (MEDIUM) 账本行 JSON 重复键：loads 静默取最后一个 ──")
    v = new_vault("n3")
    row = _pending_row()
    row["event_id"] = "quiz:" + EID
    text = json.dumps(row, ensure_ascii=False)
    dup = text.replace('"grade_norm": 0.75', '"grade_norm": 0.11, "grade_norm": 0.75', 1)
    assert dup.count('"grade_norm"') == 2
    (v / "learning_events.jsonl").write_text(dup + "\n", encoding="utf-8")
    r = run(v)
    check(
        "N3/重复键歧义",
        r.returncode != 0 and "重复键" in r.stderr and not fsrs_fields(v),
        f"rc={r.returncode} | {last_line(r.stderr)}",
    )

    print("\n── N4 (MEDIUM) 非法 UTF-8 字节须 clean fail-closed，不是 traceback ──")
    v = new_vault("n4")
    (v / "learning_events.jsonl").write_bytes(b'{"event_id": "quiz:x"}\n\xff\xfe bad\n')
    r = run(v)
    check(
        "N4/非 UTF-8 字节",
        r.returncode != 0 and "非 UTF-8 字节" in r.stderr and "Traceback" not in r.stderr,
        f"rc={r.returncode} clean={'Traceback' not in r.stderr} | {last_line(r.stderr)}",
    )

    print("\n── N5 (MEDIUM) 多 pending 并存 → attempt 序数不可从账本边界确证 ──")
    v = new_vault("n5")
    e1 = _pending_row(review_time="2026-08-03T10:00:00Z")
    e1["event_id"] = "quiz:板A#q1"
    e1["effective_at"] = "2026-08-03T10:00:00Z"
    e2 = _pending_row(
        review_time="2026-08-04T10:00:00Z",
        attempt_count=2,
        exam_board="检验白板/测试检验-2026-08-01-1000.md",
    )
    e2["event_id"] = "quiz:" + EID
    e2["effective_at"] = "2026-08-04T10:00:00Z"
    write_rows(v, e1, e2)
    r = run(v)
    check(
        "N5/A2 不变量破坏时报真因",
        r.returncode != 0 and "不变量已被破坏" in r.stderr and not fsrs_fields(v),
        f"rc={r.returncode} | {last_line(r.stderr)}",
    )


def main() -> int:
    resolved = CE_ROOT.resolve() if CE_ROOT.exists() else CE_ROOT
    if not str(resolved).startswith(str(FIXTURE_ROOT)):
        sys.exit(f"[g32b-ce] 目标目录越出约定前缀 ({resolved}) — 拒跑")
    if FIXTURE_ROOT.exists() and not (FIXTURE_ROOT / MARKER).is_file():
        sys.exit(f"[g32b-ce] {FIXTURE_ROOT} 缺标记文件 {MARKER} — 先跑 g32b_build_fixture.py")
    if CE_ROOT.exists():
        shutil.rmtree(CE_ROOT)
    CE_ROOT.mkdir(parents=True)
    print(f"反例 fixture 根: {CE_ROOT}")
    for fn in (r1, r2, r3, r4, r5, r6, r7, n1_n5):
        fn()
    bad = [t for t, ok, _ in RESULTS if not ok]
    print(f"\n{'=' * 70}\n判据 {len(RESULTS) - len(bad)}/{len(RESULTS)} PASS")
    if bad:
        print("FAIL:", bad)
        return 1
    print("R1-R7 + round-1 后续 N1-N5 全部 fail-closed / 幂等 — 裁判 2 PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
