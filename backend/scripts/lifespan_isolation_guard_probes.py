#!/usr/bin/env python
"""底层旁路探针 —— 逐条证明第八批那批绕过现在都 fail-closed。

[BATCH-2026-09-01-第九批 / CARD-TEST-isolate-lifespan-R1]

卡文 §5「必须另跑」的那一组：``_socket.socket``/``SocketType`` 真实 loopback、
``connect_ex``、``__index__`` 端口、拆 guard 后 reinstall、atexit 晚连接、
dirname/printf/BASH_ENV 劫持。每条都在**独立子进程**里跑，父进程同时核对
**退出码**与**唯一裁定行**（``PROBE-RESULT: PASS|FAIL <name> [:: reason]``）——
只看 rc 会把「因为别的原因崩了」当成通过。

## 为什么每条都配一个负控

只证明「加了防线之后拦住了」不够：还要证明**是这条防线拦住的**。所以关键探针
成对出现——把该层拆掉（``atexit.unregister``、不装门、改期望摘要）后，同一场景
必须变成另一个结果。判据是「**指定的那一条**必须翻转」，不是「某处失败了」。

## 连接目标怎么选（不碰现网库）

* 机制类探针（底层 socket / connect_ex / ``__index__``）连的是**本进程起的
  loopback 监听**，并把 ``BLOCKED_PORTS`` 临时指到那个端口。测的是「这条路径
  会不会经过门」，与具体端口号无关。
* 另有一条用**真实受拦端口 7691** 的探针，目标地址是 ``192.0.2.1``
  （RFC 5737 TEST-NET-1，保证不可路由到任何真库）。门若失效，结果是超时/
  unreachable 而不是连上现网 Neo4j —— 两种结局可区分，且都不产生实害。
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
PY = sys.executable

VERDICT_PREFIX = "PROBE-RESULT:"

_PREAMBLE = textwrap.dedent(
    """
    import os, sys, socket, _socket, threading, atexit
    sys.path.insert(0, %r)
    def verdict(ok, name, reason=""):
        line = "PROBE-RESULT: %%s %%s" %% ("PASS" if ok else "FAIL", name)
        if reason:
            line += " :: " + reason
        print(line, flush=True)
    def listener():
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.bind(("127.0.0.1", 0)); srv.listen(5)
        return srv, srv.getsockname()[1]
    """
) % str(BACKEND_DIR)


def _run(name: str, body: str, *, expect_rc: int, env_extra: dict | None = None) -> dict:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = str(BACKEND_DIR) + os.pathsep + env.get("PYTHONPATH", "")
    # 探针自身不需要 Neo4j；清干净避免任何驱动侧副作用。
    for key in [k for k in env if k.upper().startswith("NEO4J")]:
        env.pop(key, None)
    if env_extra:
        env.update(env_extra)
    proc = subprocess.run(
        [PY, "-c", _PREAMBLE + textwrap.dedent(body)],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
    )
    verdicts = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip().startswith(VERDICT_PREFIX)]
    ok_rc = proc.returncode == expect_rc
    ok_verdict = len(verdicts) == 1 and verdicts[0].split()[1] == "PASS"
    reason = ""
    if not ok_rc:
        reason = f"rc={proc.returncode} 期望 {expect_rc}"
    elif len(verdicts) != 1:
        reason = f"裁定行 {len(verdicts)} 条（期望恰好 1 条）"
    elif not ok_verdict:
        reason = verdicts[0]
    return {
        "name": name,
        "ok": ok_rc and ok_verdict,
        "rc": proc.returncode,
        "expect_rc": expect_rc,
        "verdict": verdicts[0] if len(verdicts) == 1 else verdicts,
        "reason": reason,
        "stderr_tail": proc.stderr[-400:],
    }


# ═══════════════════════════════════════════════════════════════════════════
# 承重层：底层 socket 路径
# ═══════════════════════════════════════════════════════════════════════════

_LOWLEVEL_BODY = """
    from tests.support import live_port_guard as g
    srv, port = listener()
    g.BLOCKED_PORTS = frozenset(g.BLOCKED_PORTS | {port})  # 只加不减（门的不变量）：加一个本地探针端口，不碰现网
    g.install()
    kind = %r
    if kind == "raw":
        s = _socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    elif kind == "sockettype":
        s = socket.SocketType(socket.AF_INET, socket.SOCK_STREAM)
    else:
        s = socket.socket()
    try:
        if kind == "connect_ex":
            s.connect_ex(("127.0.0.1", port))
        elif kind == "index":
            class P:
                def __index__(self): return port
            s.connect(("127.0.0.1", P()))
        else:
            s.connect(("127.0.0.1", port))
        verdict(False, %r, "连接未被拦下 —— 该路径绕过了承重层")
    except RuntimeError as e:
        if g.BLOCK_REASON in str(e):
            verdict(True, %r)
        else:
            verdict(False, %r, "抛了但不是本门的原因: " + repr(e)[:120])
    finally:
        s.close(); srv.close()
    """


def probe_lowlevel(kind: str, name: str) -> dict:
    body = _LOWLEVEL_BODY % (kind, name, name, name)
    # 拦下一次非豁免连接 ⇒ blocked>0 且 reported_status is None ⇒ 最终总账强制 rc=3
    return _run(name, body, expect_rc=3)


def probe_real_blocked_port() -> dict:
    """用**真实受拦端口 7691** 走一遍，目标是不可路由的 TEST-NET-1 地址。"""
    body = """
    from tests.support import live_port_guard as g
    g.install()
    assert 7691 in g.BLOCKED_PORTS, "7691 不在受拦集合里，本探针失去意义"
    s = socket.socket(); s.settimeout(3)
    try:
        s.connect(("192.0.2.1", 7691))   # RFC 5737 TEST-NET-1：不可能是任何真库
        verdict(False, "real-7691", "连接未被拦下（且居然连上了不可路由地址）")
    except RuntimeError as e:
        if g.BLOCK_REASON in str(e):
            verdict(True, "real-7691")
        else:
            verdict(False, "real-7691", "抛了但不是本门的原因: " + repr(e)[:120])
    except OSError as e:
        verdict(False, "real-7691", "门未拦，落到真实网络栈: " + type(e).__name__)
    finally:
        s.close()
    """
    return _run("real-7691", body, expect_rc=3)


def probe_no_guard_control() -> dict:
    """负控：**不装门**时，同一条底层路径必须真的连上（证明探针本身有效）。

    没有这一条，「底层探针 PASS」也可能只是因为探针连不上任何东西。
    """
    body = """
    srv, port = listener()
    s = _socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect(("127.0.0.1", port))
        verdict(True, "no-guard-control")     # 不装门就该连得上
    except Exception as e:
        verdict(False, "no-guard-control", "不装门也连不上，探针形态无效: " + repr(e)[:120])
    finally:
        s.close(); srv.close()
    """
    return _run("no-guard-control", body, expect_rc=0)


# ═══════════════════════════════════════════════════════════════════════════
# 身份漂移 / 门前窗口 / audit 在位性
# ═══════════════════════════════════════════════════════════════════════════


def probe_drift_reinstall() -> dict:
    body = """
    from tests.support import live_port_guard as g
    g.install()
    socket.socket.connect = g.STATE._orig_connect          # 把 belt 拆掉
    caught = []
    try:
        g.assert_guard_live("probe")
    except g.GuardDrift as e:
        caught.append("assert:" + str(e)[:60])
    try:
        g.install()                                        # 重装必须也发现漂移
    except g.GuardDrift as e:
        caught.append("install:" + str(e)[:60])
    if len(caught) == 2:
        verdict(True, "drift-reinstall")
    else:
        verdict(False, "drift-reinstall", "漂移未被发现，caught=" + repr(caught))
    """
    return _run("drift-reinstall", body, expect_rc=0)


def probe_plugin_import_installs() -> dict:
    """门前窗口：**import** guard_plugin 就该装好门，不必等 pytest_configure。"""
    body = """
    import tests.support.guard_plugin  # noqa: F401 —— import 本身应当装门
    from tests.support import live_port_guard as g
    if g.STATE.installed and g.audit_hook_alive():
        verdict(True, "plugin-import-installs")
    else:
        verdict(False, "plugin-import-installs",
                "installed=%s audit_alive=%s" % (g.STATE.installed, g.audit_hook_alive()))
    """
    return _run("plugin-import-installs", body, expect_rc=0)


def probe_audit_liveness_control() -> dict:
    """验伪锚：**没装门**时 audit_hook_alive() 必须为 False（否则这个自证是死的）。"""
    body = """
    from tests.support import live_port_guard as g
    before = g.audit_hook_alive()
    g.install()
    after = g.audit_hook_alive()
    if before is False and after is True:
        verdict(True, "audit-liveness-control")
    else:
        verdict(False, "audit-liveness-control", "before=%s after=%s" % (before, after))
    """
    return _run("audit-liveness-control", body, expect_rc=0)


def probe_require_blocked_target() -> dict:
    """``W4_GUARD_REQUIRE_BLOCKED_TARGET=1`` 且目标不在射程内 ⇒ 拒绝装门。"""
    body = """
    from tests.support import live_port_guard as g
    try:
        g.install()
        verdict(False, "require-blocked-target", "目标 45678 不在射程内却装门成功")
    except RuntimeError as e:
        if "不在受拦集合" in str(e):
            verdict(True, "require-blocked-target")
        else:
            verdict(False, "require-blocked-target", "抛了但原因不对: " + str(e)[:120])
    """
    return _run(
        "require-blocked-target",
        body,
        expect_rc=0,
        env_extra={"W4_GUARD_REQUIRE_BLOCKED_TARGET": "1", "NEO4J_URI": "bolt://127.0.0.1:45678"},
    )


def probe_require_blocked_target_positive() -> dict:
    """验伪锚：目标就是受拦端口时，同一开关下必须**装得上**（不是恒拒绝）。"""
    body = """
    from tests.support import live_port_guard as g
    g.install()
    verdict(True, "require-blocked-target-positive")
    """
    return _run(
        "require-blocked-target-positive",
        body,
        expect_rc=0,
        env_extra={"W4_GUARD_REQUIRE_BLOCKED_TARGET": "1", "NEO4J_URI": "bolt://127.0.0.1:7691"},
    )


# ═══════════════════════════════════════════════════════════════════════════
# 最终总账（atexit 之后的迟到连接）
# ═══════════════════════════════════════════════════════════════════════════

_LATE_BODY = """
    from tests.support import live_port_guard as g
    srv, port = listener()
    g.BLOCKED_PORTS = frozenset(g.BLOCKED_PORTS | {port})  # 只加不减：门的不变量
    g.install()
    g.STATE.reported_status = 0            # 模拟 pytest_cmdline_main 已经返回 0
    %s
    def late():
        s = socket.socket()
        try:
            s.connect(("127.0.0.1", port))
        except RuntimeError:
            pass                            # 门拦下了，但没有任何用例会为它结账
        finally:
            s.close()
    atexit.register(late)                   # LIFO：本处理器先跑，最终总账后跑
    verdict(True, %r)
    sys.exit(0)
    """


def probe_late_connection_forces_rc() -> dict:
    """cleanup/atexit 之后的迟到连接必须让 rc 非零。"""
    return _run("late-connection-rc", _LATE_BODY % ("", "late-connection-rc"), expect_rc=3)


def probe_late_connection_negative_control() -> dict:
    """负控：把最终总账摘掉，**同一场景** rc 必须退回 0。

    这条证明 rc=3 是最终总账挣来的，而不是「反正这个进程也会非零退出」。
    """
    disable = "atexit.unregister(g._final_accounting)"
    return _run("late-connection-negctl", _LATE_BODY % (disable, "late-connection-negctl"), expect_rc=0)


def probe_ledger_written() -> dict:
    """账本必须在最终总账里落盘（父进程独立复核的依据）。"""
    tmp = Path(tempfile.mkdtemp(prefix="w4-ledger-"))
    ledger = tmp / "ledger.json"
    body = """
    from tests.support import live_port_guard as g
    srv, port = listener()
    g.BLOCKED_PORTS = frozenset(g.BLOCKED_PORTS | {port})  # 只加不减：门的不变量
    g.install()
    s = socket.socket()
    try:
        s.connect(("127.0.0.1", port))
    except RuntimeError:
        pass
    finally:
        s.close(); srv.close()
    verdict(True, "ledger-written")
    """
    res = _run("ledger-written", body, expect_rc=3, env_extra={"W4_GUARD_LEDGER": str(ledger)})
    if res["ok"]:
        if not ledger.exists():
            res["ok"] = False
            res["reason"] = "账本未落盘"
        else:
            led = json.loads(ledger.read_text(encoding="utf-8"))
            if not (led["total"] == led["blocked"] == 1 and led["advisory"] == 0 and led["unaccounted"] == 1):
                res["ok"] = False
                res["reason"] = f"账本内容不符: {led}"
    shutil.rmtree(tmp, ignore_errors=True)
    return res


# ═══════════════════════════════════════════════════════════════════════════
# SHA shell 门：注入 + 自证 + 能报 CHANGED
# ═══════════════════════════════════════════════════════════════════════════

GATE = BACKEND_DIR / "scripts/lifespan_isolation_runtime_sha.sh"


def _sh(script: str, env_extra: dict | None = None) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    return subprocess.run(["bash", "-c", script], cwd=BACKEND_DIR, env=env, capture_output=True, text=True, timeout=180)


def probe_shell_injections() -> list[dict]:
    """三类 shell 劫持后，门监视的仍必须是**真实**的 backend 路径。"""
    results: list[dict] = []
    inject_file = Path(tempfile.mkdtemp(prefix="w4-bashenv-")) / "inject.sh"
    inject_file.write_text(
        "printf() { builtin printf '%s' '0000000000000000000000000000000000000000000000000000000000000000'; }\n"
        "export -f printf\n"
        "dirname() { builtin printf '%s' '///data/nonexistent'; }\n"
        "export -f dirname\n",
        encoding="utf-8",
    )
    cases = [
        (
            "shell-fake-dirname",
            f"dirname() {{ builtin printf '%s' '///data/nonexistent'; }}; export -f dirname; "
            f"bash {GATE} -- /usr/bin/true",
            None,
        ),
        (
            "shell-fake-printf",
            "printf() { builtin printf '%s' "
            "'0000000000000000000000000000000000000000000000000000000000000000'; }; export -f printf; "
            f"bash {GATE} -- /usr/bin/true",
            None,
        ),
        ("shell-bash-env", f"bash {GATE} -- /usr/bin/true", {"BASH_ENV": str(inject_file)}),
    ]
    expected_marker = str(BACKEND_DIR / "data/bug_log.jsonl")
    for name, script, env_extra in cases:
        proc = _sh(script, env_extra)
        ok = proc.returncode == 0 and expected_marker in proc.stdout and "RUNTIME-FILES: unchanged" in proc.stdout
        results.append(
            {
                "name": name,
                "ok": ok,
                "rc": proc.returncode,
                "expect_rc": 0,
                "verdict": "监视路径未被劫持" if ok else "监视路径或结论被劫持",
                "reason": "" if ok else f"stdout 未含真实受监视路径或结论异常: {proc.stdout[-300:]}",
                "stderr_tail": proc.stderr[-300:],
            }
        )
    shutil.rmtree(inject_file.parent, ignore_errors=True)
    return results


def probe_shell_selftest_is_load_bearing() -> dict:
    """把门自证的期望摘要改错 ⇒ 必须 GATE-BROKEN（证明自证不是死代码）。"""
    tmp = Path(tempfile.mkdtemp(prefix="w4-sha-selftest-"))
    copy = tmp / "gate.sh"
    text = GATE.read_text(encoding="utf-8")
    real = "82e87819dac824b894684638a188059759c99d793641765853e5c5cae20baa1c"
    assert real in text, "钉死的自证摘要不在脚本里 —— 探针与被测对象已经脱节"
    copy.write_text(text.replace(real, "deadbeef" * 8), encoding="utf-8")
    proc = _sh(f"bash {copy} -- /usr/bin/true")
    ok = proc.returncode == 1 and "门自证失败" in proc.stderr
    shutil.rmtree(tmp, ignore_errors=True)
    return {
        "name": "shell-selftest-load-bearing",
        "ok": ok,
        "rc": proc.returncode,
        "expect_rc": 1,
        "verdict": "自证承重" if ok else "自证是死代码",
        "reason": "" if ok else f"rc={proc.returncode} stderr={proc.stderr[-300:]}",
        "stderr_tail": proc.stderr[-300:],
    }


def probe_shell_can_report_changed() -> dict:
    """验伪锚：门必须**能**判 CHANGED。

    在 tmp 里搭一棵假 backend（``app/main.py`` + ``tests/``），让被包裹命令去写
    受监视文件之一 —— 真实工作树一个字节都不碰（卡文隔离条款：写测试仅 tmp）。
    """
    tmp = Path(tempfile.mkdtemp(prefix="w4-fake-backend-"))
    fake = tmp / "backend"
    (fake / "app").mkdir(parents=True)
    (fake / "tests").mkdir()
    (fake / "scripts").mkdir()
    (fake / "data").mkdir()
    (fake / "app/main.py").write_text("# fake\n", encoding="utf-8")
    shutil.copy2(GATE, fake / "scripts/lifespan_isolation_runtime_sha.sh")
    target = fake / "data/bug_log.jsonl"
    proc = _sh(f"bash {fake}/scripts/lifespan_isolation_runtime_sha.sh -- /bin/sh -c 'printf \"x\\n\" >> {target}'")
    ok = proc.returncode == 1 and "RUNTIME-FILES: CHANGED" in proc.stdout
    shutil.rmtree(tmp, ignore_errors=True)
    return {
        "name": "shell-can-report-changed",
        "ok": ok,
        "rc": proc.returncode,
        "expect_rc": 1,
        "verdict": "能判 CHANGED" if ok else "写了受监视文件却仍判 unchanged",
        "reason": "" if ok else f"rc={proc.returncode} stdout={proc.stdout[-300:]}",
        "stderr_tail": proc.stderr[-300:],
    }


# ═══════════════════════════════════════════════════════════════════════════


def main() -> int:
    results: list[dict] = [
        probe_no_guard_control(),
        probe_lowlevel("raw", "lowlevel-_socket.socket"),
        probe_lowlevel("sockettype", "lowlevel-SocketType"),
        probe_lowlevel("connect_ex", "lowlevel-connect_ex"),
        probe_lowlevel("index", "lowlevel-__index__-port"),
        probe_real_blocked_port(),
        probe_drift_reinstall(),
        probe_plugin_import_installs(),
        probe_audit_liveness_control(),
        probe_require_blocked_target(),
        probe_require_blocked_target_positive(),
        probe_late_connection_forces_rc(),
        probe_late_connection_negative_control(),
        probe_ledger_written(),
        probe_shell_selftest_is_load_bearing(),
        probe_shell_can_report_changed(),
    ]
    results.extend(probe_shell_injections())

    print("=== lifespan isolation GUARD PROBES ===")
    print(f"    interpreter: {PY}")
    failed = [r for r in results if not r["ok"]]
    for r in results:
        mark = "PASS" if r["ok"] else "FAIL"
        print(f"  [{mark}] {r['name']:<34} rc={r['rc']} (期望 {r['expect_rc']})")
        if not r["ok"]:
            print(f"         原因: {r['reason']}")
            if r["stderr_tail"]:
                print(f"         stderr: {r['stderr_tail']}")
    if failed:
        print(f"GUARD-PROBES: FAIL — {len(failed)}/{len(results)} 条未 fail-closed")
        return 1
    print(f"GUARD-PROBES: PASS — {len(results)}/{len(results)} 条全部 fail-closed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
