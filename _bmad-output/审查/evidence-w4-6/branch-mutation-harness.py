#!/usr/bin/env python
"""CARD-W4-6 —— 逐条证明「本卡新增的判据各自承重」的定向变异 harness。

[BATCH-2026-09-05-第十二批 / CARD-W4-6-shell-bashenv]

用法::

    cd backend
    PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \\
        ../_bmad-output/审查/evidence-w4-6/branch-mutation-harness.py

## 为什么需要它（Codex round-1 MEDIUM-2 / MEDIUM-3 的整改）

`before-after-harness.py` 证明的是「换掉整个门版本，六条新探针全红」。那只说明
**两版之间有差异**，说明不了「哪一条判据在为哪一条探针承重」——尤其两条标记类
探针在 before 侧转红的原因是**旧门不认识 `--w4-reexec` 这个参数**（rc=2 用法错误），
不是旧缺陷显形。

本 harness 换一种做法：**只在 after 基线上动一处**，每次拆掉**一条**判据，然后断言
**指定的那一条**探针（不是「某处失败」）翻红。判据绑定「是被哪一层拒的」。

⛔ 三态判定，防假杀（本仓既有教训 `reference_killed_needs_proof_claimed_assertion_reddened`）：
   * ``SYNTAX-INVALID`` —— 变异体连 `bash -n` 都过不了 ⇒ 探针红是「门导不进来」，
     不是判据承重，记为**无效变异**；
   * ``SURVIVED``       —— 指定探针仍绿 ⇒ 该判据不承重；
   * ``KILLED``         —— 指定探针红**且** `bash -n` 通过。
   另外每条都打印「本轮还有哪些探针红了」，便于人工核对不是别的原因连坐。

⛔ 锚点命中数必须与期望相等，否则记 ANCHOR-DRIFT（不静默变成「没拆」）。
⛔ 只在 tmp 假 backend 上跑，真实 backend/app/data 与 backend/data 一个字节不碰。
"""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[3] / "backend"
PROBES = BACKEND / "scripts/lifespan_isolation_guard_probes.py"
GATE_SRC = BACKEND / "scripts/lifespan_isolation_runtime_sha.sh"

#: (变异名, 期望翻红的探针, [(锚点, 替换, 期望命中数), ...], 说明)
#:
#: ⚠️ 变异必须是**忠实的旧设计**，不能只改一半。M-nul-delimited 初版只把消费端的
#:    `read -r -d ''` 改回 `read -r`，而生产端还在 `env -0` —— NUL 流被按行读，
#:    完成哨兵永远读不到，门死在「枚举未完整产出」而不是「多行变量被误判」。
#:    指定探针确实红了，但**红的原因不是它声称的那条**（假杀）。所以这一条现在
#:    同时改生产端与消费端。
MUTATIONS = [
    (
        "M-exec-collect",
        [
            "shell-bash-env-exec-layer-is-load-bearing",
            "shell-exec-strips-readonly-func",
            "shell-wrapped-cmd-sees-no-injected-func",
        ],
        [('        BASH_FUNC_*) __w4_env_args+=(-u "${__w4_entry%%=*}") ;;\n', "", 1)],
        "退回「exec 层不摘 BASH_FUNC_*」——三条 exec 层探针必须全红",
    ),
    (
        "M-ticket-check",
        ["shell-reexec-sentinel-forged"],
        [
            (
                '''      *)
        builtin printf 'RUNTIME-FILES: GATE-BROKEN — --w4-reexec 标记与本进程 PID 不一致；拒绝在未经清洗的环境里给出结论\\n' >&2
        builtin exit 1
        ;;
''',
                "      *) ;;\n",
                1,
            )
        ],
        "拆掉 PID 一致性比对 —— 标记不匹配那条探针必须红",
    ),
    (
        "M-bashenv-check",
        ["shell-forged-ticket-with-injection-refused"],
        [
            (
                '''      *)
        builtin printf 'RUNTIME-FILES: GATE-BROKEN — 标记声称已清洗，但 BASH_ENV/ENV 仍有值；拒绝给出结论\\n' >&2
        builtin exit 1
        ;;
''',
                "      *) ;;\n",
                1,
            )
        ],
        "拆掉 BASH_ENV/ENV 残留检查 —— 只有那一条探针该红",
    ),
    (
        "M-exported-func-check",
        ["shell-ticket-ok-but-exported-func-refused"],
        [
            (
                '''      *)
        builtin printf 'RUNTIME-FILES: GATE-BROKEN — 标记声称已清洗，但环境里仍有导出函数:%s\\n' "$__w4_stale" >&2
        builtin exit 1
        ;;
''',
                "      *) ;;\n",
                1,
            )
        ],
        "拆掉导出函数残留检查 —— 这是 BASH_ENV 那条探针到不了的分支",
    ),
    (
        "M-trap-clear",
        ["shell-forged-ticket-under-exit-trap"],
        [("    builtin trap - EXIT HUP INT QUIT TERM ERR DEBUG RETURN 2>/dev/null || true\n", "", 1)],
        "拆掉拒绝路径的清 trap —— 注入者的 EXIT trap 会把 rc 改写成 0",
    ),
    (
        "M-nul-delimited",
        ["shell-multiline-env-var-not-mistaken-for-func"],
        [
            (
                "while IFS= builtin read -r -d '' __w4_entry; do",
                "while IFS= builtin read -r __w4_entry; do",
                2,
            ),
            (
                "{ /usr/bin/env -0 && builtin printf '%s\\0' \"$__W4_ENV_SENTINEL\"; }",
                "{ /usr/bin/env && builtin printf '%s\\n' \"$__W4_ENV_SENTINEL\"; }",
                2,
            ),
        ],
        "忠实退回按行扫环境（生产端+消费端同改）—— 值含换行的普通变量会把正常调用弄成假红",
    ),
    (
        "M-enum-sentinel",
        ["shell-env-enum-failure-is-fail-closed"],
        [('    case "$__w4_env_ok" in\n      1) ;;', '    case "1" in\n      1) ;;', 2)],
        "让枚举完成检查恒真 —— 枚举失败就会被当成『没有残留』",
    ),
]


def _load_probes():
    spec = importlib.util.spec_from_file_location("w4_mut_harness", PROBES)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["w4_mut_harness"] = mod
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    base = GATE_SRC.read_text(encoding="utf-8")
    import hashlib

    base_sha = hashlib.sha256(base.encode("utf-8")).hexdigest()
    print("=== CARD-W4-6 定向变异：每条新判据是否承重 ===")
    print(f"    基线门 sha256 = {base_sha}")
    print(f"    变异条数      = {len(MUTATIONS)}")
    print()

    verdicts = []
    for name, expect_red, edits, note in MUTATIONS:
        drift = [(a[:40], base.count(a), w) for a, _, w in edits if base.count(a) != w]
        if drift:
            print(f"[ANCHOR-DRIFT] {name}: 锚点命中数与期望不符 {drift} —— 变异无效，不计击杀")
            verdicts.append((name, "ANCHOR-DRIFT", []))
            print()
            continue
        text = base
        for anchor, repl, _ in edits:
            text = text.replace(anchor, repl)
        if text == base:
            print(f"[NO-OP] {name}: 替换后文本与基线相同 —— 变异没生效，不计击杀")
            verdicts.append((name, "NO-OP", []))
            print()
            continue

        mod = _load_probes()
        tmp, fake = mod._fake_backend(f"w4-6-mut-{name}-", gate_text=text)
        try:
            gate_path = fake / "scripts" / "lifespan_isolation_runtime_sha.sh"
            syn = subprocess.run(["bash", "-n", str(gate_path)], capture_output=True, text=True, timeout=60)
            if syn.returncode != 0:
                print(f"[SYNTAX-INVALID] {name}: 变异体 bash -n 失败 —— 探针红也不算击杀")
                print(f"    {syn.stderr.strip()[:200]}")
                verdicts.append((name, "SYNTAX-INVALID", []))
                print()
                continue
            mod.BACKEND_DIR = fake
            mod.GATE = gate_path
            results = mod.probe_shell_injections()
            red = [r["name"] for r in results if not r["ok"]]
            killed = all(n in red for n in expect_red)
            verdict = "KILLED" if killed else "SURVIVED"
            verdicts.append((name, verdict, red))
            print(f"[{verdict}] {name} —— {note}")
            print(f"    期望翻红: {expect_red}")
            print(f"    本轮实际红: {red or '（无）'}")
            collateral = [n for n in red if n not in expect_red]
            if collateral:
                print(f"    ⚠️ 连坐（非期望但也红了，人工核对是否同源）: {collateral}")
            print()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    after = GATE_SRC.read_text(encoding="utf-8")
    after_sha = hashlib.sha256(after.encode("utf-8")).hexdigest()
    print("=== 汇总 ===")
    for name, v, _ in verdicts:
        print(f"  {v:<15} {name}")
    n_killed = sum(1 for _, v, _ in verdicts if v == "KILLED")
    print(f"KILLED {n_killed}/{len(MUTATIONS)}")
    print(f"跑后基线门 sha256 = {after_sha}  （与跑前{'相同' if after_sha == base_sha else '**不同 —— 生产文件被动过**'}）")
    return 0 if (n_killed == len(MUTATIONS) and after_sha == base_sha) else 1


if __name__ == "__main__":
    raise SystemExit(main())
