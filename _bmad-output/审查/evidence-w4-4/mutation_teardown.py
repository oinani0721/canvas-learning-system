#!/usr/bin/env python
"""CARD-W4-4 的**拆门实测**：逐条把修复拆掉，看**指定的那道门**是不是当场转红。

[BATCH-2026-09-05-第十二批 / CARD-W4-4-settle-atomic]

## 判据（照抄前几批的教训，别放宽）

* **必须串行**：原地改生产文件，并发跑会互踩，「还原后字节相同」这道自检就没了意义。
* **判据绑定失败身份**：不是「某处失败了」，而是**点名的那条探针 / 那条 nodeid**
  必须从 PASS 变 FAIL。被更早的防线喂饱、被 import 错误喂饱，都算 SURVIVED。
* **还原无条件**：``try/finally`` + 进程级 ``atexit``，任何退出路径都还原；
  跑前对**每一个会被变异的文件**记 sha，跑完逐个复核。
* **执行块包在 ``__main__`` 里**：import 本模块不得改任何生产文件。
* 变异必须**拆掉被测的那条防线本身**，不是改个参数——改参数常常连门的期望值一起改了，
  于是变异不可见。

## 变异清单与它们各自钉的是什么

============  ==========================================================
M1            结算判定搬回 hook 的**锁外读**（= 主干 03ac8bf8 的形状）
M2            ``_final_accounting`` 不再把快照传给 ``write_ledger``（双快照回归）
M3            ``install()`` 里把装 hook 挪回预检**之后**（T-14 回归）
M4            ``assert_guard_live`` 不再复核注入点身份（seam 变成一条旁路）
M5            预检从 ``pytest_configure`` 挪回 session fixture（T-10 回归）
M6            ``begin_item`` 不再因「预检未完成」收回豁免票（T-10 的闩被拆）
M7            迟到路径不再重写账本（账本与 rc 又能打脸）
M8            拆掉注入点的 try/except（seam 抛异常即可跳过记账，Codex r1 HIGH-1）
M9            迟到报告块移出 try（stderr 坏掉时 print 抛异常越过 os._exit，Codex r1 HIGH-3）
============  ==========================================================

## 三态判定（Codex round-1 MEDIUM-6 收紧）

``FAILED`` 才算击杀；``PASS`` 是存活；``NOTRUN`` / ``SYNTAX-INVALID`` 是 harness 自身
没跑起来，**一律不计击杀**——否则 import 错误、collection 错误、语法不合法的变异体
都能「杀掉」变异，判据就比它声称的宽。

用法：``python mutation_teardown.py``（cwd 任意）。
"""

from __future__ import annotations

import ast
import atexit
import hashlib
import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BACKEND = ROOT / "backend"
PY = str(BACKEND / ".venv" / "bin" / "python")

GUARD = BACKEND / "tests" / "support" / "live_port_guard.py"
CONFTEST = BACKEND / "tests" / "conftest.py"
PLUGIN = BACKEND / "tests" / "support" / "guard_plugin.py"

#: 所有可能被变异的文件 —— 跑前记 sha、跑完逐个复核（不是只盯自己改的那一个）。
TOUCHED = [GUARD, CONFTEST, PLUGIN]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


BASELINE: dict[Path, str] = {}
ORIGINAL: dict[Path, bytes] = {}


def _restore_all() -> None:
    """无条件还原。注册进 atexit，也在每条变异的 finally 里调 —— 两道都要。"""
    for path, blob in ORIGINAL.items():
        if path.read_bytes() != blob:
            path.write_bytes(blob)


# ═══════════════════════════════════════════════════════════════════════════
# 判据执行器
# ═══════════════════════════════════════════════════════════════════════════


def run_probe(names: list[str]) -> dict[str, tuple[bool, str]]:
    """只跑点名的那几条探针（不跑全量：判据要绑定身份，也省时间）。"""
    script = textwrap.dedent(
        """
        import importlib.util, json, sys
        spec = importlib.util.spec_from_file_location("gp", %r)
        m = importlib.util.module_from_spec(spec)
        sys.modules["gp"] = m
        spec.loader.exec_module(m)
        out = {}
        for fn_name, probe_name in %r:
            res = getattr(m, fn_name)()
            out[probe_name] = [bool(res["ok"]), str(res["reason"])[:200]]
        print("PROBE-JSON:" + json.dumps(out, ensure_ascii=False))
        """
    ) % (
        str(BACKEND / "scripts" / "lifespan_isolation_guard_probes.py"),
        [(PROBE_FN[n], n) for n in names],
    )
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = str(BACKEND) + os.pathsep + env.get("PYTHONPATH", "")
    proc = subprocess.run([PY, "-c", script], cwd=BACKEND, env=env, capture_output=True, text=True, timeout=900)
    for line in proc.stdout.splitlines():
        if line.startswith("PROBE-JSON:"):
            raw = json.loads(line[len("PROBE-JSON:") :])
            # 探针自己给出了裁定：PASS = 变异活下来，FAIL = 这条探针把它杀了
            return {k: ("PASS" if v[0] else "FAILED", v[1]) for k, v in raw.items()}
    # ⛔ 拿不到裁定 ≠ 变异被杀（Codex round-1 MEDIUM-6）：那说明探针进程自己没跑起来，
    #    属于 harness 故障，必须与「指定探针翻红」区分开，否则 import 错误也能算击杀。
    return {n: ("NOTRUN", f"探针进程没给出结果 rc={proc.returncode}: {proc.stderr[-300:]}") for n in names}


PROBE_FN = {
    "guard-finalize-race-loses-record": "probe_finalize_race_loses_record",
    "guard-ledger-matches-verdict": "probe_ledger_matches_verdict",
    "guard-install-order-precheck-is-guarded": "probe_install_order_precheck_is_guarded",
    "guard-finalize-seam-inert-when-unset": "probe_finalize_seam_inert_when_unset",
    "guard-late-exit-survives-broken-stderr": "probe_late_exit_survives_broken_stderr",
}

CONTRACT = "tests/unit/test_live_port_guard_contract.py"


def run_tests(nodeids: list[str]) -> dict[str, tuple[str, str]]:
    """按**完整 nodeid** 跑点名的用例。返回每条的 (状态, 摘要)。

    状态三分（Codex round-1 MEDIUM-6 的处置）：

    * ``PASS``   —— 用例通过（变异没被这条门抓到）；
    * ``FAILED`` —— 用例**真的跑起来并失败了**，且 ``-rf`` 短摘要里点名了这条 nodeid；
    * ``NOTRUN`` —— 收集/import/configure 期就崩了、或一条都没收集到。

    ⛔ 只有 ``FAILED`` 算「被这道门杀掉」。初版把 ``rc != 0`` 一律当 KILLED，于是
    import 错误、collection 错误、configure 崩溃都能「杀掉变异」——那与本脚本
    §判据 里写的「被更早防线喂饱算 SURVIVED」自相矛盾（判据比声称的宽）。
    """
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    out: dict[str, tuple[str, str]] = {}
    for nodeid in nodeids:
        full = f"{CONTRACT}::{nodeid}"
        proc = subprocess.run(
            [PY, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--tb=line", "-rf", "-o", "addopts=", full],
            cwd=BACKEND,
            env=env,
            capture_output=True,
            text=True,
            timeout=600,
        )
        stdout = proc.stdout
        lines = [ln for ln in stdout.splitlines() if ln.strip()]
        tail = lines[-1][:160] if lines else "(无输出)"
        # -rf 的短摘要行形如 `FAILED tests/unit/xxx.py::Cls::test_name - AssertionError: ...`
        named_failure = any(ln.startswith("FAILED ") and full.split("::", 1)[1] in ln for ln in lines)
        collected_one = any("1 passed" in ln or "1 failed" in ln for ln in lines)
        if proc.returncode == 0:
            status = "PASS"
        elif named_failure and collected_one:
            status = "FAILED"
        else:
            status = "NOTRUN"
            tail = f"（未跑到指定断言，不计为击杀）{tail}"
        out[nodeid] = (status, tail)
    return out


# ═══════════════════════════════════════════════════════════════════════════
# 变异体
# ═══════════════════════════════════════════════════════════════════════════

M1_OLD_RECORD = """            stale = gen != self.current_gen
            if stale or self.finalizing:"""
M1_NEW_RECORD = """            stale = gen != self.current_gen
            if stale:"""
M1_OLD_LATE = """            if self.finalizing:
                self.late += 1
                self.blocked += 1
                self.pending.setdefault(owner, []).append(rec)
                return RECORD_LATE
            if exempt:"""
M1_NEW_LATE = """            if exempt:"""
#: hook 侧搬回「锁外先读一次结算标志，再进另一把锁记账」——主干 03ac8bf8 的形状。
#:
#: ⚠️ 锚点必须包含**整块** try/except，不能只写那行调用：r2 整改把 seam 调用缩进从
#: 12 空格改成了 16（包进了 try），而 12 空格版本恰好是 16 空格版本的**子串** ⇒
#: `str.count` 仍返回 1、替换成功、产出 IndentationError。那一轮里 M1 的探针确实
#: 翻红了，但红的原因是「模块导不进来」，不是「锁外读丢了记录」——旧判据会把它
#: 记成 KILLED（假杀第二形态）。现在由 `_syntax_ok()` + NOTRUN 三态兜住。
M1_OLD_HOOK = """            try:
                _finalize_race_seam_hook()
            except BaseException:  # noqa: BLE001 —— 见上：注入点不得影响控制流
                pass
"""
M1_NEW_HOOK = """            _late_now = STATE.finalizing  # 锁外读（主干形状）
            try:
                _finalize_race_seam_hook()
            except BaseException:  # noqa: BLE001
                pass
"""
M1_OLD_HOOK2 = """            outcome = STATE.record(address)"""
M1_NEW_HOOK2 = """            outcome = RECORD_LATE if _late_now else STATE.record(address)"""

MUTANTS: list[dict] = [
    {
        "id": "M1-lockfree-finalizing-read",
        "why": "把结算判定搬回 hook 的锁外读（= 主干形状）：迟到线程读到「未结算」后落进普通账",
        "edits": [
            (GUARD, M1_OLD_RECORD, M1_NEW_RECORD),
            (GUARD, M1_OLD_LATE, M1_NEW_LATE),
            (GUARD, M1_OLD_HOOK, M1_NEW_HOOK),
            (GUARD, M1_OLD_HOOK2, M1_NEW_HOOK2),
        ],
        "probes": ["guard-finalize-race-loses-record", "guard-ledger-matches-verdict"],
        "tests": [
            "TestSettlementAtomicity::test_record_after_finalize_returns_late",
            "TestSettlementAtomicity::test_finalize_snapshot_is_frozen_against_later_records",
        ],
    },
    {
        "id": "M2-double-snapshot",
        "why": "_final_accounting 不再把快照传给 write_ledger ⇒ 裁定与落盘各取各的",
        "edits": [
            (
                GUARD,
                "            write_ledger(path, ledger)  # ← 同一份快照，不再取第二次",
                "            write_ledger(path)",
            )
        ],
        # ⚠️ probes 里**显式挂上**账本探针（Codex round-1 判「未判定」：初版这里是
        #    `probes: []`，于是「探针杀不掉 M2」是推理出来的、不是跑出来的）。
        #    现在真跑一次；它是 SURVIVED 还是 FAILED，以输出为准，别再替它下结论。
        "probes": ["guard-ledger-matches-verdict"],
        "expect_probe_survives": True,
        "tests": ["TestSingleLedgerSnapshot::test_final_accounting_hands_its_own_snapshot_to_write_ledger"],
    },
    {
        "id": "M3-install-order-reverted",
        "why": "install() 把装 hook 挪回预检之后（T-14 回归）",
        "edits": [
            (
                GUARD,
                """    _install_audit_hook()
    if os.environ.get(ENV_REQUIRE_BLOCKED_TARGET) == "1":
        assert_neo4j_target_blocked()
    register_final_accounting()""",
                """    if os.environ.get(ENV_REQUIRE_BLOCKED_TARGET) == "1":
        assert_neo4j_target_blocked()
    _install_audit_hook()
    register_final_accounting()""",
            )
        ],
        "probes": ["guard-install-order-precheck-is-guarded"],
        "tests": ["TestInstallOrder::test_audit_hook_is_installed_before_the_target_precheck"],
    },
    {
        "id": "M4-seam-drift-check-removed",
        "why": "assert_guard_live 不再复核注入点身份 ⇒ seam 成了一条无人看守的旁路",
        "edits": [
            (
                GUARD,
                """    if _finalize_race_seam_hook is not _finalize_race_seam:
        raise GuardDrift(""",
                """    if False:
        raise GuardDrift(""",
            )
        ],
        "probes": ["guard-finalize-seam-inert-when-unset"],
        "tests": ["TestFinalizeRaceSeam::test_seam_replacement_is_detected_as_drift"],
    },
    {
        "id": "M5-precheck-back-in-session-fixture",
        "why": "预检从 pytest_configure 挪回 session fixture（T-10 回归）",
        "edits": [
            (
                CONFTEST,
                '    live_port_guard.assert_test_uri_not_blocked()\n\n\n@pytest.fixture(scope="session", autouse=True)',
                '\n\n@pytest.fixture(scope="session", autouse=True)',
            ),
            (
                CONFTEST,
                '    live_port_guard.assert_guard_live("session fixture")\n',
                '    live_port_guard.assert_guard_live("session fixture")\n'
                "    live_port_guard.assert_test_uri_not_blocked()\n",
            ),
        ],
        "probes": [],
        "tests": [
            "TestPrecheckBeforeExemption::test_precheck_lives_in_pytest_configure_not_in_a_session_fixture[root-conftest]"
        ],
    },
    {
        "id": "M6-begin-item-latch-removed",
        "why": "begin_item 不再因「预检未完成」收回豁免票（T-10 的闩被拆）",
        "edits": [
            (
                GUARD,
                """        if not STATE.precheck_done:
            exempt = False
""",
                "",
            )
        ],
        "probes": [],
        "tests": ["TestPrecheckBeforeExemption::test_begin_item_refuses_exemption_before_the_precheck"],
    },
    {
        "id": "M7-late-ledger-rewrite-removed",
        "why": "迟到路径不再重写账本 ⇒ 文件停在结算那一刻的空账，而进程 rc=3",
        "edits": [
            (
                GUARD,
                "                    _rewrite_ledger_after_late_record()\n",
                "",
            )
        ],
        "probes": ["guard-ledger-matches-verdict"],
        "tests": [],
    },
    {
        "id": "M8-seam-exception-can-skip-accounting",
        "why": "拆掉注入点的 try/except ⇒ seam 抛异常就能跳过记账（Codex round-1 HIGH-1 的形态）",
        "edits": [
            (
                GUARD,
                """            try:
                _finalize_race_seam_hook()
            except BaseException:  # noqa: BLE001 —— 见上：注入点不得影响控制流
                pass
""",
                """            _finalize_race_seam_hook()
""",
            )
        ],
        "probes": [],
        "tests": ["TestFinalizeRaceSeam::test_throwing_seam_cannot_skip_accounting"],
    },
    {
        "id": "M9-late-report-not-guarded",
        "why": "把迟到路径的报告块移出 try ⇒ stderr 坏掉时 print 抛异常越过 os._exit(3)",
        "edits": [
            (
                GUARD,
                """                try:
                    # 退出前把**含这条记录**的账本重写一次 —— 否则文件里是结算那一刻的
                    # 空账而进程 rc=3，父进程复核与子进程裁定互相打脸。
                    _rewrite_ledger_after_late_record()
                    print(
                        f"\\n*** {BLOCK_REASON}（最终结算之后）: {address!r} —— "
                        f"进程被强制以退出码 {FINAL_EXIT_CODE} 结束 ***",
                        file=sys.stderr,
                    )
                    sys.stdout.flush()
                    sys.stderr.flush()
                except BaseException:  # noqa: BLE001 —— 见上：绝不阻断 os._exit
                    pass
""",
                """                _rewrite_ledger_after_late_record()
                print(
                    f"\\n*** {BLOCK_REASON}（最终结算之后）: {address!r} —— "
                    f"进程被强制以退出码 {FINAL_EXIT_CODE} 结束 ***",
                    file=sys.stderr,
                )
                try:
                    sys.stdout.flush()
                    sys.stderr.flush()
                except Exception:  # noqa: BLE001
                    pass
""",
            )
        ],
        "probes": ["guard-late-exit-survives-broken-stderr"],
        "tests": [],
    },
]


def _syntax_ok(path: Path) -> tuple[bool, str]:
    """变异体必须仍是**合法 Python**。

    ⛔ 语法不合法的变异体是「假杀第二形态」：模块编译期就死，被测的那件坏事根本没机会
    发生，而门会因为「导不进来」翻红 —— 记成 KILLED 就是自己骗自己。2026-09-05 本卡
    r2 实测撞到一次（M1 锚点缩进漂移，见 ``M1_OLD_HOOK`` 上方说明）。
    """
    try:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as exc:
        return False, f"{path.name}:{exc.lineno} {exc.msg}"
    return True, ""


def apply_mutant(mutant: dict) -> tuple[bool, str]:
    """打变异体。返回 (是否可用于判定, 原因)。

    锚点匹配**锁到行首**（``"\\n" + old``）：只写片段会让缩进更深的同名代码成为
    「包含」关系而误匹配（r2 实测的 12 空格 ⊂ 16 空格）。
    """
    for path, old, new in mutant["edits"]:
        src = path.read_text(encoding="utf-8")
        anchor = "\n" + old
        count = src.count(anchor)
        if count != 1:
            return False, f"ANCHOR-MISS: 锚点在 {path.name} 里按行首匹配到 {count} 次（必须恰好 1 次）：{old[:70]!r}"
        path.write_text(src.replace(anchor, "\n" + new, 1), encoding="utf-8")
    for path in TOUCHED:
        ok, why = _syntax_ok(path)
        if not ok:
            return False, f"变异体语法不合法（SYNTAX-INVALID）：{why}"
    return True, ""


def main() -> int:
    for path in TOUCHED:
        ORIGINAL[path] = path.read_bytes()
        BASELINE[path] = _sha(path)
    atexit.register(_restore_all)

    print("=== CARD-W4-4 拆门实测（变异 → 指定的门必须转红）===")
    print(f"    backend: {BACKEND}")
    for path in TOUCHED:
        print(f"    baseline sha  {path.name:<22} {BASELINE[path][:16]}")

    # ── 第 0 步：未变异时，全部被点名的门必须是绿的（否则「转红」毫无意义）──
    all_probes = sorted({p for m in MUTANTS for p in m["probes"]})
    all_tests = sorted({t for m in MUTANTS for t in m["tests"]})
    print("\n───── baseline（未变异）─────")
    base_probe = run_probe(all_probes) if all_probes else {}
    base_test = run_tests(all_tests) if all_tests else {}
    baseline_bad = []
    for name, (status, why) in base_probe.items():
        print(f"  probe {name:<42} {status}")
        if status != "PASS":
            baseline_bad.append(f"probe {name}: {why}")
    for name, (status, why) in base_test.items():
        print(f"  test  {name:<78} {status}")
        if status != "PASS":
            baseline_bad.append(f"test {name}: {why}")
    if baseline_bad:
        print("BASELINE-NOT-GREEN — 变异结果不可解读：")
        for line in baseline_bad:
            print(f"    {line}")
        _restore_all()
        return 2

    # ── 逐条变异（串行）──────────────────────────────────────────────
    verdicts: list[tuple[str, str, str]] = []
    for mutant in MUTANTS:
        print(f"\n───── {mutant['id']} ─────")
        print(f"  拆的是：{mutant['why']}")
        try:
            usable, why = apply_mutant(mutant)
            if not usable:
                print(f"  ⛔ {why}")
                # 两种 harness 故障分开报：锚点没命中 ≠ 变异体语法不合法，原因不同、修法也不同。
                verdicts.append(
                    (mutant["id"], "ANCHOR-MISS" if why.startswith("ANCHOR-MISS") else "SYNTAX-INVALID", why)
                )
                continue
            probe_res = run_probe(mutant["probes"]) if mutant["probes"] else {}
            test_res = run_tests(mutant["tests"]) if mutant["tests"] else {}
        finally:
            _restore_all()
        # 判据（Codex round-1 MEDIUM-6 收紧）：
        #   FAILED = 指定的那道门真的跑起来并翻红 ⇒ 击杀成立
        #   PASS   = 门没抓到 ⇒ 变异存活
        #   NOTRUN = harness 自己没跑起来 ⇒ **不算击杀**，单独报出来
        killers, survivors, notrun = [], [], []
        expect_survive = bool(mutant.get("expect_probe_survives"))
        for kind, res, width in (("probe", probe_res, 42), ("test", test_res, 78)):
            for name, (status, why) in res.items():
                label = {"FAILED": "FAIL(KILLED)", "PASS": "PASS(SURVIVED)", "NOTRUN": "NOTRUN(不计击杀)"}[status]
                print(f"  {kind:<5} {name:<{width}} {label}  {why[:110]}")
                target = f"{kind} {name}"
                (killers if status == "FAILED" else survivors if status == "PASS" else notrun).append(target)
        # ``expect_probe_survives``：本卡**事先声明**「探针侧杀不掉这条变异」（M2 —— (a)
        # 落地后，双快照的可观测分叉被 (a) 吸收了）。声明只免除**探针**这一侧，
        # 仍然要求至少有一道被点名的门真的翻红；而且它必须由实跑输出支持，
        # 不能只写在验收单里（Codex round-1 判「未判定」的正是「没挂探针就下结论」）。
        unexpected = [s for s in survivors if not (expect_survive and s.startswith("probe "))]
        if notrun:
            status = "HARNESS-ERROR"
        elif killers and not unexpected:
            status = "KILLED"
        else:
            status = "SURVIVED"
        detail = "; ".join(
            ([f"意外存活: {', '.join(unexpected)}"] if unexpected else [])
            + (
                [f"已声明的预期存活: {', '.join(set(survivors) - set(unexpected))}"]
                if expect_survive and survivors
                else []
            )
            + ([f"harness 未跑起来: {', '.join(notrun)}"] if notrun else [])
        )
        verdicts.append((mutant["id"], status, detail))
        for path in TOUCHED:
            if _sha(path) != BASELINE[path]:
                print(f"  ⛔ 还原失败：{path} 的 sha 与基线不同")
                return 3

    print("\n=== 汇总 ===")
    for mid, status, detail in verdicts:
        print(f"  [{status:<13}] {mid}" + (f"  —— {detail}" if detail else ""))
    for path in TOUCHED:
        same = _sha(path) == BASELINE[path]
        print(f"  restore-check {path.name:<22} {'BYTE-IDENTICAL' if same else '⛔ DIFFERS'}")
    bad = [v for v in verdicts if v[1] != "KILLED"]
    if bad:
        print(f"MUTATION-TEARDOWN: FAIL — {len(bad)}/{len(verdicts)} 条变异未被点名的门杀掉")
        return 1
    print(f"MUTATION-TEARDOWN: PASS — {len(verdicts)}/{len(verdicts)} 条变异均被点名的门当场杀掉")
    return 0


if __name__ == "__main__":
    sys.exit(main())
