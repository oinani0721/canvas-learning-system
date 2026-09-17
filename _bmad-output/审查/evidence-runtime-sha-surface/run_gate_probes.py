#!/usr/bin/env python3
"""只跑**门相关**的 shell / runtime-glob 探针（Codex r1 LOW「152 passed 不代表探针跑过」的补证）。

背景：`tests/unit/test_live_port_guard_contract.py` 里对 `lifespan_isolation_guard_probes.py`
的两处提及都在 docstring 里（`:8` / `:939`），它**不调用** `probe_shell_injections()`，
所以「契约测试 152 passed」证明不了这些探针还绿。

⚠️ 入口更正（Codex round-2 LOW-3）：本文件初版写「真正驱动方是
`lifespan_isolation_negative_control.py`」——**写反了**。实测聚合调用在
`lifespan_isolation_guard_probes.py` **自己的 `main()`**（`:2155` 起列出各探针，
`:2179` `results.extend(probe_shell_injections())`）；`negative_control.py` 只在
docstring（`:82` / `:190`）里提到它，并不调用。共同点仍成立：那条驱动是
`__main__` 脚本态，**不被任何 pytest 套件收集**。

本驱动只 **import** guard_probes（不改它），并只调用与本门有关的那几支——
⛔ 刻意**不**跑 socket / 端口族探针（其中一条用真实受拦端口号），本批禁连 7691/7687。

用法: python3 run_gate_probes.py
退出码: 0 = 全部门相关探针 ok
"""

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
BACKEND = HERE.parents[3] / "backend"
MOD_PATH = BACKEND / "scripts" / "lifespan_isolation_guard_probes.py"


def load():
    spec = importlib.util.spec_from_file_location("gate_probes_ro", MOD_PATH)
    mod = importlib.util.module_from_spec(spec)
    # dataclass 自省需要模块在 sys.modules 里（Python 3.14）
    sys.modules["gate_probes_ro"] = mod
    spec.loader.exec_module(mod)
    return mod


GATE_PROBES = [
    "probe_shell_selftest_is_load_bearing",
    "probe_shell_can_report_changed",
    "probe_runtime_glob_absent_to_present",
    "probe_runtime_glob_cached_expansion_is_blind",
    "probe_runtime_glob_pattern_neutralized_is_blind",
    "probe_runtime_glob_sidecar_excluded",
    "probe_runtime_glob_expansion_sorted",
    "probe_runtime_legacy_journal_watched",
]


def main() -> int:
    print(f"gate = {MOD_PATH}")
    mod = load()
    results: list[dict] = []

    # 19 条 shell 注入族（返回 list）
    shell = mod.probe_shell_injections()
    results.extend(shell)
    print(f"[probe_shell_injections] 返回 {len(shell)} 条")

    for name in GATE_PROBES:
        fn = getattr(mod, name, None)
        if fn is None:
            print(f"!! 找不到探针 {name} —— 探针与本驱动已脱节")
            return 1
        results.append(fn())

    bad = [r for r in results if not r.get("ok")]
    for r in results:
        flag = "ok " if r.get("ok") else "FAIL"
        print(f"  [{flag}] {r.get('name')}  rc={r.get('rc')}  {r.get('verdict', '')[:70]}")
    print(f"GATE-PROBES total={len(results)} failed={len(bad)}")
    if bad:
        print(json.dumps(bad, ensure_ascii=False, indent=2)[:4000])
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
