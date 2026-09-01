#!/usr/bin/env python3
"""CARD-TEST-bark-autostub 负控裁判 (R1: 二十四跑, 串行子进程)。

每道「放行门」配一道同 nodeid 的「篡改门」(--noconftest 卸下守卫):
门存在 ≠ 门在工作, 只有卸甲必红才证明放行门真的依赖守卫。

  A / B    test_probe            — 拒绝器 (卸甲=真尝试外发被探针双墙挡住)
  C / C'   test_keyfile_guarded  — 层① KEY_FILE 重定向 + loopback 内容
  D / D'   test_osascript_guarded— 层③ osascript 模块属性打桩
  E / E'   test_reload_selfheal  — reload 双保险 (双模块各自重打)
  F / F'   test_proxy_first_hop_stays_loopback — 层⑤d 已建 opener 中和 (行为)
  F2/ F2'  test_proxy_state_neutralized       — 层⑤a/b/c 代理来源哑火 (状态)
  H / H'   test_osascript_prebound_alias_blocked — 层⑥ 预绑定别名在 spawn 前被拦
  S / S'   test_stale_reload_*   — teardown 后 stale wrapper 在 reload **之前**拒绝
  CS/ CS'  bark_coldstart_probe  — 冷启动布防 (残留门 G 的前提)
  R / R'   test_held_opener_after_prebound_reload — 预绑定 reload 绕开双保险后,
           别处握持的 opener 仍不出机 (⑤a+⑤c 独撑; 判据锚机外地址)
  U        bark_unguarded_probe  — 未布防模块零副作用 (无卸甲孪生, 证伪靠变异 M10)
  G        bark_keyfile_residue_check.py — teardown 后 KEY_FILE 无 tmp 残留

(第八批的「八跑」= 这里的 A/B/C/C'/D/D'/E/E'; R1 增 F/F'、F2/F2'、H/H'、
S/S'、CS/CS'、R/R'、X/X'、U、G 共十六跑。)

判据口径 (R1 重写, 完成条件 (e)) —— **不看 stdout**:
被测进程能逐字打印任何一行文本, round-3 已实证「同文件无关失败 + captured
stdout 打印目标 E 行 + 唯一摘要」骗过文本判据, 连 not_conftest.py 都因含子串
`conftest.py` 而满足来源检查。本裁判改从 bark_negctl_report_plugin 落的
结构化 TestReport 取证:
  - 逐 nodeid 的 call 阶段 outcome 必须与期望**集合全等** (多一条少一条都算红);
  - setup/teardown/collect 阶段不得有 failed;
  - 每条期望失败必须同时满足: crash_path (异常抛出点所在 frame 的文件, 由
    解释器 traceback 决定) 与期望文件**路径全等** (realpath 比较, 不是子串),
    且 crash_message 首行与期望字符串全等 (或按显式声明的前缀匹配);
  - 指定跑另需 frame 链穿过指定文件 (B: 必须真的经由生产 send 路径抛出);
  - 进程 rc 与插件记录的 exitstatus 必须一致 (报告缺失/进程崩溃即红);
  - **每一跑**另核插件落的进程级全局还原对账 (布防前 vs 全部 teardown 后):
    urlopen / getproxies / _opener / subprocess.run / importlib.reload /
    _scproxy._get_proxies / 代理 env 必须逐项相同 (sys.path 不在其中: 它不是
    守卫拥有的全局, 生产代码与 pytest 都会动它) —— 守卫一次
    测试里可能反复 _reapply, 任何一层还原不掉都会漏进后续测试。

exit 0 仅当全部按期望。串行、子进程、-p no:cacheprovider 防并行 session 共享
.pytest_cache 踩踏。`--only LABEL[,LABEL...]` 只跑指定跑 (变异负控用)。
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
SCRIPTS = BACKEND / "scripts"
PROBE = "tests/regression/bark_egress_probe.py"
COLD = "tests/regression/bark_coldstart_probe.py"

CONFTEST_FILE = str((BACKEND / "tests/regression/conftest.py").resolve())
PROBE_FILE = str((BACKEND / PROBE).resolve())
COLD_FILE = str((BACKEND / COLD).resolve())

DISARM = ["--noconftest"]


def _c(label, nodeids, extra, expect, crash=None, require_frames=None, globals_drift_allow=()):
    """一条 pytest 跑。expect: {测试函数名: 'passed'|'failed'};
    crash: {测试函数名: (期望文件绝对路径, 期望消息, 是否前缀匹配)}。"""
    return {
        "label": label,
        "nodeids": nodeids,
        "extra": extra,
        "expect": expect,
        "crash": crash or {},
        "require_frames": require_frames or {},
        "globals_drift_allow": tuple(globals_drift_allow),
    }


CASES = [
    _c("A/disarmed-probe-egress-attempted", [f"{PROBE}::test_probe"], DISARM, {"test_probe": "passed"}),
    _c(
        "B/armed-probe-refused",
        [f"{PROBE}::test_probe"],
        [],
        {"test_probe": "failed"},
        {"test_probe": (CONFTEST_FILE, "AssertionError: Bark egress attempted in tests", False)},
        # 拒绝必须发生在**生产 send 路径**上, 不是探针里随手抛的同名异常
        {
            "test_probe": (
                str((BACKEND.parent / "scripts/daily_review_run.py").resolve()),
                str((BACKEND.parent / "scripts/send_bark.py").resolve()),
            )
        },
    ),
    _c("C/armed-keyfile-guarded", [f"{PROBE}::test_keyfile_guarded"], [], {"test_keyfile_guarded": "passed"}),
    _c(
        "C'/disarmed-keyfile-tamper",
        [f"{PROBE}::test_keyfile_guarded"],
        DISARM,
        {"test_keyfile_guarded": "failed"},
        {
            "test_keyfile_guarded": (
                PROBE_FILE,
                "AssertionError: BARK-GATE-C-KEYFILE: 守卫未布防 — send_bark.KEY_FILE 仍指向真实 key 位置",
                False,
            )
        },
    ),
    _c("D/armed-osascript-guarded", [f"{PROBE}::test_osascript_guarded"], [], {"test_osascript_guarded": "passed"}),
    _c(
        "D'/disarmed-osascript-tamper",
        [f"{PROBE}::test_osascript_guarded"],
        DISARM,
        {"test_osascript_guarded": "failed"},
        {
            "test_osascript_guarded": (
                PROBE_FILE,
                "AssertionError: BARK-GATE-D-OSASCRIPT: 守卫未布防 — osascript_fallback 仍是 runner 原始实现",
                False,
            )
        },
    ),
    _c("E/armed-reload-selfheal", [f"{PROBE}::test_reload_selfheal"], [], {"test_reload_selfheal": "passed"}),
    _c(
        "E'/disarmed-reload-tamper",
        [f"{PROBE}::test_reload_selfheal"],
        DISARM,
        {"test_reload_selfheal": "failed"},
        {
            "test_reload_selfheal": (
                PROBE_FILE,
                "AssertionError: BARK-GATE-E-RELOAD-KEYFILE: reload 后 KEY_FILE 回到真实 key 位置",
                False,
            )
        },
    ),
    _c(
        "F/armed-proxy-first-hop-loopback",
        [f"{PROBE}::test_proxy_first_hop_stays_loopback"],
        [],
        {"test_proxy_first_hop_stays_loopback": "passed"},
    ),
    _c(
        "F'/disarmed-proxy-first-hop-hijacked",
        [f"{PROBE}::test_proxy_first_hop_stays_loopback"],
        DISARM,
        {"test_proxy_first_hop_stays_loopback": "failed"},
        {
            "test_proxy_first_hop_stays_loopback": (
                PROBE_FILE,
                "AssertionError: BARK-GATE-F-FIRSTHOP: 代理首跳未被中和 "
                "(首跳 ('127.0.0.1', 63128), 期望 ('127.0.0.1', 9))",
                False,
            )
        },
    ),
    _c(
        "F2/armed-proxy-state-neutralized",
        [f"{PROBE}::test_proxy_state_neutralized"],
        [],
        {"test_proxy_state_neutralized": "passed"},
    ),
    _c(
        "F2'/disarmed-proxy-state-live",
        [f"{PROBE}::test_proxy_state_neutralized"],
        DISARM,
        {"test_proxy_state_neutralized": "failed"},
        {
            "test_proxy_state_neutralized": (
                PROBE_FILE,
                "AssertionError: BARK-GATE-F2-ENVPROXY: 布防期内仍有代理 env 残留 ",
                True,
            )
        },
    ),
    _c(
        "H/armed-osascript-prebound-blocked",
        [f"{PROBE}::test_osascript_prebound_alias_blocked"],
        [],
        {"test_osascript_prebound_alias_blocked": "passed"},
    ),
    _c(
        "H'/disarmed-osascript-prebound-spawns",
        [f"{PROBE}::test_osascript_prebound_alias_blocked"],
        DISARM,
        {"test_osascript_prebound_alias_blocked": "failed"},
        {
            "test_osascript_prebound_alias_blocked": (
                PROBE_FILE,
                "AssertionError: BARK-GATE-H-OSASCRIPT-SPAWN: 真 osascript spawn 已抵达 subprocess.Popen",
                False,
            )
        },
    ),
    _c(
        "S/armed-stale-reload-refused",
        [f"{PROBE}::test_stale_reload_stash", f"{PROBE}::test_stale_reload_refused_before_reload"],
        [],
        {"test_stale_reload_stash": "passed", "test_stale_reload_refused_before_reload": "passed"},
    ),
    _c(
        "S'/disarmed-stale-reload-executes",
        [f"{PROBE}::test_stale_reload_stash", f"{PROBE}::test_stale_reload_refused_before_reload"],
        DISARM,
        {"test_stale_reload_stash": "passed", "test_stale_reload_refused_before_reload": "failed"},
        {
            "test_stale_reload_refused_before_reload": (
                PROBE_FILE,
                "AssertionError: BARK-GATE-S-STALE-RELOAD: stale wrapper 未拒绝对受保护模块的 reload",
                False,
            )
        },
    ),
    _c(
        "R/armed-held-opener-after-prebound-reload",
        [f"{PROBE}::test_held_opener_after_prebound_reload"],
        [],
        {"test_held_opener_after_prebound_reload": "passed"},
    ),
    _c(
        "R'/disarmed-held-opener-proxied",
        [f"{PROBE}::test_held_opener_after_prebound_reload"],
        DISARM,
        {"test_held_opener_after_prebound_reload": "failed"},
        {
            "test_held_opener_after_prebound_reload": (
                PROBE_FILE,
                "AssertionError: BARK-GATE-R-GETPROXIES: 预绑定 reload 之后代理来源复活 "
                "({'http': 'http://127.0.0.1:63128'})",
                False,
            )
        },
        # 卸甲形态下本测试自己会真 reload(urllib.request) —— 那会把 _opener 置回
        # None, 而此时**没有守卫**去还原它。这不是守卫污染, 是「无守卫」的预期
        # 结果。豁免**只给 opener 这一个键**, 其余七项照查 (round-3 审查指出整份
        # 豁免会盖住别的漂移); 同一条测试的 armed 跑 (R) 全项都查。
        globals_drift_allow=("opener",),
    ),
    _c(
        "X/armed-reapply-after-failed-reload",
        [f"{PROBE}::test_reapply_after_failed_reload"],
        [],
        {"test_reapply_after_failed_reload": "passed"},
    ),
    _c(
        "X'/disarmed-failed-reload-leaves-production",
        [f"{PROBE}::test_reapply_after_failed_reload"],
        DISARM,
        {"test_reapply_after_failed_reload": "failed"},
        {
            "test_reapply_after_failed_reload": (
                PROBE_FILE,
                "AssertionError: BARK-GATE-X-REAPPLY-ON-FAILURE: reload 半途失败后层⑥ 未被重打, 模块停在生产态",
                False,
            )
        },
    ),
    _c(
        "U/armed-unguarded-module-untouched",
        ["tests/regression/bark_unguarded_probe.py::test_guard_leaves_unguarded_modules_untouched"],
        [],
        {"test_guard_leaves_unguarded_modules_untouched": "passed"},
    ),
    _c(
        "CS/armed-coldstart-redirected",
        [f"{COLD}::test_coldstart_keyfile_redirected"],
        [],
        {"test_coldstart_keyfile_redirected": "passed"},
    ),
    _c(
        "CS'/disarmed-coldstart-real-key",
        [f"{COLD}::test_coldstart_keyfile_redirected"],
        DISARM,
        {"test_coldstart_keyfile_redirected": "failed"},
        {
            "test_coldstart_keyfile_redirected": (
                COLD_FILE,
                "AssertionError: BARK-GATE-CS-COLDSTART: 冷启动未落在守卫 tmp 目录 (KEY_FILE=",
                True,
            )
        },
    ),
]

#: G 跑不是 pytest nodeid — 判据在 fixture teardown 之后, 只能由独立脚本取。
G_LABEL = "G/keyfile-no-residue-after-teardown"
G_SCRIPT = "scripts/bark_keyfile_residue_check.py"
G_OK_PREFIX = "BARK-KEYFILE-RESIDUE: OK"

ALL_LABELS = [c["label"] for c in CASES] + [G_LABEL]


def _short(nodeid: str) -> str:
    return nodeid.rsplit("::", 1)[-1]


def _run_pytest(case, report_path: Path):
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-p",
        "no:cacheprovider",
        "-p",
        "bark_negctl_report_plugin",
        *case["extra"],
        *case["nodeids"],
    ]
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["BARK_NEGCTL_REPORT"] = str(report_path)
    env["PYTHONPATH"] = os.pathsep.join([str(SCRIPTS)] + ([env["PYTHONPATH"]] if env.get("PYTHONPATH") else []))
    print(f"[{case['label']}] $ {' '.join(cmd)}", flush=True)
    try:
        proc = subprocess.run(cmd, cwd=BACKEND, capture_output=True, text=True, timeout=600, env=env)
    except subprocess.TimeoutExpired as e:
        sys.stdout.write(e.stdout if isinstance(e.stdout, str) else "")
        sys.stderr.write(str(e))
        print(f"[{case['label']}] TIMEOUT after 600s")
        return None, None
    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)
    return proc.returncode, report_path


def _judge_pytest(case) -> bool:
    problems = []
    with tempfile.TemporaryDirectory(prefix="bark-negctl-") as td:
        report_path = Path(td) / "report.json"
        rc, _ = _run_pytest(case, report_path)
        if rc is None:
            return False
        if not report_path.exists():
            print(f"[{case['label']}] MISMATCH: 插件未落报告 (进程可能崩溃) rc={rc}")
            return False
        data = json.loads(report_path.read_text(encoding="utf-8"))

    want_rc = 0 if all(v == "passed" for v in case["expect"].values()) else 1
    if rc != want_rc:
        problems.append(f"进程 rc={rc} 不是本跑期望的 {want_rc} (pytest 正常判定只有 0/1)")
    if data.get("exitstatus") != rc:
        problems.append(f"进程 rc={rc} 与插件 exitstatus={data.get('exitstatus')} 不一致")

    # 进程级全局还原对账 (每一跑都查): 守卫在一次测试里可能反复 _reapply,
    # 任何一层没被 MonkeyPatch 正确还原, 桩就会漏进后续测试。
    gb, ga = data.get("globals_before"), data.get("globals_after")
    if gb is None or ga is None:
        problems.append("插件未落全局快照 (globals_before/after 缺失)")
    else:
        # 豁免按**键**给, 不是整份跳过 (round-3 审查: 整份豁免会连带盖住别的漂移)
        diff = [
            f"{k}: 布防前 {gb.get(k)!r} → teardown 后 {ga.get(k)!r}"
            for k in sorted(set(gb) | set(ga))
            if gb.get(k) != ga.get(k) and k not in case["globals_drift_allow"]
        ]
        if diff:
            problems.append("globals 未还原 (进程级污染): " + "; ".join(diff))

    calls, other_failed = {}, []
    for rep in data["reports"]:
        if rep["when"] == "call":
            calls[_short(rep["nodeid"])] = rep
        elif rep["outcome"] == "failed":
            other_failed.append(f"{rep['when']}:{rep['nodeid']}")
    if other_failed:
        problems.append(f"非 call 阶段出现失败: {other_failed}")

    got = {k: v["outcome"] for k, v in calls.items()}
    if got != case["expect"]:
        problems.append(f"outcome 集合不符: 实测 {got} != 期望 {case['expect']}")

    for name, (want_path, want_msg, is_prefix) in case["crash"].items():
        rep = calls.get(name)
        if rep is None or "crash_path" not in rep:
            problems.append(f"{name}: 无 crash 记录")
            continue
        if os.path.realpath(rep["crash_path"]) != os.path.realpath(want_path):
            problems.append(f"{name}: 异常抛出点文件不符 {rep['crash_path']} != {want_path}")
        first = rep["crash_message"].splitlines()[0]
        ok_msg = first.startswith(want_msg) if is_prefix else first == want_msg
        if not ok_msg:
            problems.append(f"{name}: 异常首行不符\n      实测 {first!r}\n      期望 {want_msg!r}")

    for name, wanted in case["require_frames"].items():
        rep = calls.get(name)
        # frame 里的 path 是相对 rootdir 的, 先还原成绝对再**路径全等**比对 ——
        # 用 endswith 的话同尾巴的别的模块也能满足 (round-2 审查 LOW)。
        chain = {os.path.realpath(os.path.join(BACKEND, f["path"])) for f in (rep or {}).get("frames", [])}
        for want in wanted:
            if os.path.realpath(want) not in chain:
                problems.append(f"{name}: frame 链缺少 {want} (实测 {sorted(chain)})")

    # 把**结构化**的抛出点消息单独打一行 —— 变异裁判据此绑定红因,
    # 被测代码 print 不出这一行 (它来自异常对象, round-3 审查 MEDIUM)。
    for name, rep in sorted(calls.items()):
        if rep.get("outcome") == "failed" and "crash_message" in rep:
            print(f"[{case['label']}] CRASH {name} :: {rep['crash_message'].splitlines()[0]}")
    ok = not problems
    print(f"[{case['label']}] expect {case['expect']} -> ok={ok} rc={rc}")
    for p in problems:
        print(f"    ✗ {p}")
    return ok


def _judge_residue() -> bool:
    cmd = [sys.executable, G_SCRIPT]
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    print(f"[{G_LABEL}] $ {' '.join(cmd)}", flush=True)
    try:
        proc = subprocess.run(cmd, cwd=BACKEND, capture_output=True, text=True, timeout=600, env=env)
    except subprocess.TimeoutExpired as e:
        sys.stderr.write(str(e))
        print(f"[{G_LABEL}] TIMEOUT after 600s")
        return False
    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)
    lines = [ln for ln in proc.stdout.splitlines() if ln.startswith("BARK-KEYFILE-RESIDUE:")]
    ok = proc.returncode == 0 and len(lines) == 1 and lines[0].startswith(G_OK_PREFIX)
    # 把红因复述成裁判自产的 ✗ 行 —— 变异裁判只在 CRASH/✗ 行里找 sentinel,
    # 被测脚本自己的 stdout 不算数 (与 pytest 侧同一条口径)。
    if not ok:
        for ln in lines or ["(无 BARK-KEYFILE-RESIDUE 行)"]:
            print(f"    ✗ {ln}")
    print(f"[{G_LABEL}] expect OK -> ok={ok} rc={proc.returncode} lines={lines}")
    return ok


def main() -> int:
    ap = argparse.ArgumentParser(description="Bark 外发守卫负控裁判 (二十四跑)")
    ap.add_argument("--only", help="逗号分隔的跑标签, 只跑这些 (变异负控用)")
    args = ap.parse_args()

    wanted = None
    if args.only:
        wanted = [w.strip() for w in args.only.split(",") if w.strip()]
        unknown = [w for w in wanted if w not in ALL_LABELS]
        if unknown:
            print(f"未知跑标签 {unknown}; 可用: {ALL_LABELS}")
            return 2

    results = []
    for case in CASES:
        if wanted is not None and case["label"] not in wanted:
            continue
        results.append((case["label"], _judge_pytest(case)))
    if wanted is None or G_LABEL in wanted:
        results.append((G_LABEL, _judge_residue()))

    print()
    for label, ok in results:
        print(f"{label}: {'ok' if ok else 'MISMATCH'}")
    if results and all(ok for _, ok in results):
        print(f"NEGATIVE-CONTROL: PASS ({len(results)}/{len(results)} runs as expected)")
        return 0
    print("NEGATIVE-CONTROL: FAIL")
    return 1


if __name__ == "__main__":
    sys.exit(main())
