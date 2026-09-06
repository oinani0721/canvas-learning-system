#!/usr/bin/env python
"""CARD-W4-6 —— 「拆掉本卡修复 ⇒ 探针转红」的 before/after 对照 harness。

[BATCH-2026-09-05-第十二批 / CARD-W4-6-shell-bashenv]

用法::

    cd backend
    PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \\
        ../_bmad-output/审查/evidence-w4-6/before-after-harness.py before|after

**探针代码两侧完全相同**（都是工作树里的 `lifespan_isolation_guard_probes.py`），
唯一的差别是被测的那份 `runtime_sha.sh`：

* ``before`` = ``git show 39407e97:backend/scripts/lifespan_isolation_runtime_sha.sh``
  （开工 SHA，`sha256 = 280cfadb…998a`）；
* ``after``  = 工作树当前版本。

这样「红了」只可能来自门的修复本身，不可能来自探针写法的差异。

⛔ 两侧都在 tmp 假 backend 里跑（`_fake_backend` 造树 + 打补丁把模块级 `GATE` /
`BACKEND_DIR` 指过去），真实 ``backend/app/data`` / ``backend/data`` 一个字节不碰。
"""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[3] / "backend"
PROBES = BACKEND / "scripts/lifespan_isolation_guard_probes.py"
START_SHA = "39407e97"

#: 本卡新增的 10 条 shell 探针（既有 6 条不在此列）。
#:
#: ⚠️ 后四条在 before 侧翻红的**原因**与前六条不同，报告里必须分开说，不能笼统写成
#:    「旧缺陷复现」（Codex round-1 MEDIUM-3）：
#:      * exec 层三条 + `shell-reexec-sentinel-preset` —— 旧门的**真实缺陷显形**
#:        （导出函数没被摘 / 预设环境变量跳过清洗）；
#:      * `shell-reexec-sentinel-forged` / `shell-forged-ticket-with-injection-refused`
#:        / `shell-ticket-ok-but-exported-func-refused` / `shell-forged-ticket-under-exit-trap`
#:        —— 旧门**不认识 `--w4-reexec` 这个参数**，rc=2 用法错误。这是**协议差异**，
#:        只能算新协议回归测试，承重证据来自 `branch-mutation-harness.py`；
#:      * `shell-multiline-env-var-not-mistaken-for-func` / `shell-env-enum-failure-is-fail-closed`
#:        —— 针对的是本卡**自己引入**的两个面（假红、枚举失败静默），旧门没有这两段
#:        代码，同样属协议差异。
SHELL_PROBE_NAMES_NEW = [
    "shell-bash-env-exec-layer-is-load-bearing",
    "shell-exec-strips-readonly-func",
    "shell-wrapped-cmd-sees-no-injected-func",
    "shell-reexec-sentinel-preset",
    "shell-reexec-sentinel-forged",
    "shell-forged-ticket-with-injection-refused",
    "shell-ticket-ok-but-exported-func-refused",
    "shell-forged-ticket-under-exit-trap",
    "shell-multiline-env-var-not-mistaken-for-func",
    "shell-env-enum-failure-is-fail-closed",
]

#: before 侧翻红原因是「旧门真实缺陷显形」的那几条（其余是协议差异）。
DEFECT_DEMONSTRATING = {
    "shell-bash-env-exec-layer-is-load-bearing",
    "shell-exec-strips-readonly-func",
    "shell-wrapped-cmd-sees-no-injected-func",
    "shell-reexec-sentinel-preset",
}


def _load_probes():
    spec = importlib.util.spec_from_file_location("w4_probes_harness", PROBES)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["w4_probes_harness"] = mod  # dataclass/自省安全（见项目 gotcha）
    spec.loader.exec_module(mod)
    return mod


def _gate_text(side: str) -> str:
    if side == "after":
        return (BACKEND / "scripts/lifespan_isolation_runtime_sha.sh").read_text(encoding="utf-8")
    out = subprocess.run(
        ["git", "show", f"{START_SHA}:backend/scripts/lifespan_isolation_runtime_sha.sh"],
        cwd=BACKEND.parent,
        capture_output=True,
        check=True,
        timeout=120,
    )
    return out.stdout.decode("utf-8")


def main() -> int:
    side = sys.argv[1] if len(sys.argv) > 1 else "after"
    if side not in ("before", "after"):
        print("用法: before-after-harness.py before|after", file=sys.stderr)
        return 2

    mod = _load_probes()
    text = _gate_text(side)
    # 先在真实 GATE 下造树，再把模块级常量整体切到假树上。
    tmp, fake = mod._fake_backend(f"w4-6-{side}-", gate_text=text)
    try:
        mod.BACKEND_DIR = fake
        mod.GATE = fake / "scripts" / "lifespan_isolation_runtime_sha.sh"
        import hashlib

        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        print(f"=== CARD-W4-6 before/after harness —— side={side} ===")
        print(f"    被测门 sha256 = {digest}")
        print(f"    假 backend    = {fake}")
        results = mod.probe_shell_injections()
        newly = [r for r in results if r["name"] in SHELL_PROBE_NAMES_NEW]
        for r in results:
            mark = "PASS" if r["ok"] else "FAIL"
            tag = " <本卡新增>" if r["name"] in SHELL_PROBE_NAMES_NEW else ""
            print(f"  [{mark}] {r['name']:<44} rc={r['rc']} (期望 {r['expect_rc']}){tag}")
            if not r["ok"]:
                print(f"         原因: {r['reason'][:400]}")
        red = [r["name"] for r in newly if not r["ok"]]
        print(f"--- 本卡新增 {len(newly)} 条中，红 {len(red)} 条: {red or '（无）'}")
        if side == "before":
            print(f"    其中「旧门真实缺陷显形」: {sorted(set(red) & DEFECT_DEMONSTRATING) or '（无）'}")
            print(f"    其中「协议差异（旧门不认识新参数/没有该段代码）」: {sorted(set(red) - DEFECT_DEMONSTRATING) or '（无）'}")
            print("    ⚠️ 后者只算新协议回归测试；承重证据见 branch-mutation-harness.py")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
