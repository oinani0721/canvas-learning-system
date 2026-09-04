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


def probe_extract_port_mutation_detected() -> dict:
    """R1 Codex HIGH-3：把 ``extract_port`` 改成恒返 None，自证必须当场翻红。

    旧自证走的是一个**独立私有事件**，只证明「hook 对象还在链上」——
    改坏端口解析之后自证照样通过、真实 loopback 连接照样成功、账本照样全零。
    """
    body = """
    from tests.support import live_port_guard as g
    srv, port = listener()
    g.BLOCKED_PORTS = frozenset(g.BLOCKED_PORTS | {port})
    g.install()
    g.extract_port = lambda address: None      # 把端口解析打断
    try:
        g.assert_guard_live("probe")
        verdict(False, "extract-port-mutation", "extract_port 被打断，自证却通过了")
    except g.GuardDrift:
        verdict(True, "extract-port-mutation")
    finally:
        srv.close()
    """
    return _run("extract-port-mutation", body, expect_rc=0)


def probe_toctou_index_port() -> dict:
    """R1 Codex LOW-17：有状态的 ``__index__``（第一次给受拦端口、第二次给 1）。"""
    body = """
    from tests.support import live_port_guard as g
    srv, port = listener()
    g.BLOCKED_PORTS = frozenset(g.BLOCKED_PORTS | {port})
    g.install()
    class Flaky:
        def __init__(self): self.n = 0
        def __index__(self):
            self.n += 1
            return port if self.n == 1 else 1
    s = socket.socket()
    try:
        s.connect(("127.0.0.1", Flaky()))
        verdict(False, "toctou-index-port", "二次求值端口对象连上了 —— TOCTOU 未关闭")
    except RuntimeError as e:
        if g.BLOCK_REASON in str(e):
            verdict(True, "toctou-index-port")
        else:
            verdict(False, "toctou-index-port", "抛了但不是本门的原因: " + repr(e)[:120])
    finally:
        s.close(); srv.close()
    """
    return _run("toctou-index-port", body, expect_rc=3)


def probe_uvloop_reimport_blocked() -> dict:
    """R1 Codex HIGH-4：删掉毒化条目后重新 import uvloop，必须被 audit 拦下。"""
    body = """
    from tests.support import live_port_guard as g
    g.install()
    del sys.modules["uvloop"]                  # 把毒化条目摘掉
    try:
        import uvloop                          # noqa: F401
        verdict(False, "uvloop-reimport", "毒化被摘掉后 uvloop 成功导入")
    except RuntimeError as e:
        if "uvloop 的 import 被本门拦下" in str(e):
            verdict(True, "uvloop-reimport")
        else:
            verdict(False, "uvloop-reimport", "抛了但不是本门的原因: " + repr(e)[:120])
    except ImportError:
        verdict(False, "uvloop-reimport", "落到 ImportError —— 说明拦的是「装没装」而不是「不许装」")
    """
    return _run("uvloop-reimport", body, expect_rc=0)


def probe_late_after_finalizing() -> dict:
    """R1 Codex HIGH-2：在 import 本门**之前**注册的 atexit 回调里发起连接。

    ``atexit`` 是 LIFO，那个回调排在最终结算**之后**执行 —— 旧实现下它被记账、
    进程却仍 ``exit 0``（Codex 实测 ``LATE_BLOCKED_AFTER_FINAL True``）。
    现在最终结算进入即置不可逆标志，此后命中受拦端口就地 ``os._exit(3)``。
    """
    body = """
    srv, port = listener()
    def very_late():
        s = socket.socket()
        try:
            s.connect(("127.0.0.1", port))
        except Exception:
            pass
        finally:
            s.close()
    atexit.register(very_late)                 # 先注册 ⇒ 最后执行（在最终结算之后）
    from tests.support import live_port_guard as g
    g.BLOCKED_PORTS = frozenset(g.BLOCKED_PORTS | {port})
    g.install()
    g.STATE.reported_status = 0                # 模拟 pytest 已返回 0
    verdict(True, "late-after-finalizing")
    sys.exit(0)
    """
    return _run("late-after-finalizing", body, expect_rc=3)


def probe_ownership_model() -> dict:
    """归属模型的四条声明 —— 本轮之前只是从上一张卡继承来的文字，没被验过。

    A 主线程连接归当前用例；B 裸线程归 ``<unknown>``；
    C 携带 context 副本的线程（anyio portal 的形态）归**发起用例**；
    D **豁免期复制走的 context 在用例结束后必须作废** —— 这条最容易假：
    如果代次机制不生效，一个在豁免用例里复制的 context 就能把「只记不拦」的
    特权无限期带出去，`advisory` 会悄悄涨而没人拦。
    """
    body = """
    import contextvars
    from tests.support import live_port_guard as g
    srv, port = listener()
    g.BLOCKED_PORTS = frozenset(g.BLOCKED_PORTS | {port})
    g.install()
    def attempt():
        s = socket.socket()
        try:
            s.connect(("127.0.0.1", port))
        except RuntimeError:
            pass
        finally:
            s.close()
    problems = []
    g.begin_item("nodeid::A", exempt=False)
    attempt()
    if g.STATE.records[-1]["owner"] != "nodeid::A":
        problems.append("A 主线程归属错: " + g.STATE.records[-1]["owner"])
    t = threading.Thread(target=attempt); t.start(); t.join()
    if g.STATE.records[-1]["owner"] != "<unknown>":
        problems.append("B 裸线程未归 unknown: " + g.STATE.records[-1]["owner"])
    ctx = contextvars.copy_context()
    t2 = threading.Thread(target=lambda: ctx.run(attempt)); t2.start(); t2.join()
    if g.STATE.records[-1]["owner"] != "nodeid::A":
        problems.append("C 带上下文线程归属错: " + g.STATE.records[-1]["owner"])
    g.end_item()
    g.begin_item("nodeid::B", exempt=True)
    stale = contextvars.copy_context()
    g.end_item()
    adv_before = g.STATE.advisory
    t3 = threading.Thread(target=lambda: stale.run(attempt)); t3.start(); t3.join()
    rec = g.STATE.records[-1]
    if rec["exempt"] or rec["owner"] != "<unknown>" or g.STATE.advisory != adv_before:
        problems.append("D 过期豁免票没作废: " + repr(rec) + " advisory+" + str(g.STATE.advisory - adv_before))
    srv.close()
    if problems:
        verdict(False, "ownership-model", "; ".join(problems)[:200])
    else:
        verdict(True, "ownership-model")
    """
    # 四次拦截全部无人结账 ⇒ 最终结算强制 rc=3
    return _run("ownership-model", body, expect_rc=3)


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


def _sh_direct(argv: list[str], env_extra: dict | None = None) -> subprocess.CompletedProcess:
    """直接起门进程，**不**套一层 ``bash -c``。

    控制流类注入必须这样测：``BASH_ENV`` 会被**每一个**非交互 bash 读取，套一层
    ``bash -c`` 的话注入同时污染了外层包装 —— 外层的 EXIT trap 打印什么都跟门无关，
    那是「把自己的 shell 装了炸弹」，不是门的缺陷。这里让门自己就是那个进程。
    """
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    return subprocess.run(argv, cwd=BACKEND_DIR, env=env, capture_output=True, text=True, timeout=180)


def _load_negctl():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "negctl_probe", BACKEND_DIR / "scripts/lifespan_isolation_negative_control.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def probe_drift_in_test_fails_the_session() -> dict:
    """用例里把 belt 拆掉且**不还原** ⇒ 整个 pytest 进程必须 fail-closed。

    这条验的是「每个用例边界都复核身份」这句承诺的**端到端**效果，而不只是
    `assert_guard_live()` 单独调用会抛。在隔离副本里跑（真实树不写）。

    判据是两项而不是一项：rc 非零 **且** 输出里点名了 `GuardDrift` 与那条用例 ——
    只看 rc 的话，「因为别的原因崩了」也会算过。
    """
    import tempfile as _tf

    mod = _load_negctl()
    tmp = Path(_tf.mkdtemp(prefix="w4-drift-"))
    try:
        iso = mod.make_isolated_backend(tmp)
        target = iso / "tests/test_w4_drift_probe.py"
        target.write_text(
            '"""探针用例：拆掉 belt 且不还原。"""\n'
            "import socket\n"
            "from tests.support import live_port_guard as g\n\n\n"
            "def test_removes_the_guard_and_does_not_restore():\n"
            "    socket.socket.connect = g.STATE._orig_connect\n"
            "    assert True\n",
            encoding="utf-8",
        )
        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["PYTHONPATH"] = str(iso)
        proc = subprocess.run(
            [
                PY,
                "-m",
                "pytest",
                "tests/test_w4_drift_probe.py",
                "-q",
                "-p",
                "no:cacheprovider",
                "--override-ini=addopts=",
            ],
            cwd=iso,
            env=env,
            capture_output=True,
            text=True,
            timeout=300,
        )
        blob = proc.stdout + proc.stderr
        ok = proc.returncode != 0 and "GuardDrift" in blob and "test_removes_the_guard_and_does_not_restore" in blob
        reason = (
            ""
            if ok
            else f"rc={proc.returncode} GuardDrift={'GuardDrift' in blob} 点名用例={'test_removes' in blob}: {blob[-300:]}"
        )
    except Exception as exc:  # noqa: BLE001
        ok, proc, reason = False, None, f"探针自身失败: {exc!r}"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return {
        "name": "drift-in-test-fails-session",
        "ok": ok,
        "rc": proc.returncode if proc is not None else -1,
        "expect_rc": "非 0 且点名 GuardDrift",
        "verdict": "用例内拆门让整个会话 fail-closed" if ok else "拆门后会话没有 fail-closed",
        "reason": reason,
        "stderr_tail": "",
    }


def probe_isolated_copy_carries_no_data() -> dict:
    """隔离副本**不得**把运行时数据带进 tmp（.env 必须是软链，不是拷贝）。

    2026-09-03 实测：整目录 `copytree` 会把 `backend/data/` 下 12 个 git-ignored 的
    运行时文件搬进 `/tmp`，含 `llm_call_logs.db`(36KB) / `neo4j_memory.json` /
    `learning_memories.json`。改成 tracked-only 复制之后这一面消失，本探针把它钉成门。
    """
    import importlib.util
    import tempfile as _tf

    spec = importlib.util.spec_from_file_location(
        "negctl_probe", BACKEND_DIR / "scripts/lifespan_isolation_negative_control.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    tmp = Path(_tf.mkdtemp(prefix="w4-isocheck-"))
    problems: list[str] = []
    try:
        iso = mod.make_isolated_backend(tmp)
        if not (iso / ".env").is_symlink():
            problems.append(".env 不是软链（凭据被拷进 tmp）")
        tracked = {
            n
            for n in subprocess.run(
                ["git", "ls-files", "-z", "--", "."],
                cwd=BACKEND_DIR,
                capture_output=True,
                check=True,
                timeout=120,
            )
            .stdout.decode("utf-8")
            .split("\0")
            if n
        }
        for p in iso.rglob("*"):
            if not p.is_file() or p.is_symlink():
                continue
            rel = str(p.relative_to(iso))
            if rel not in tracked:
                problems.append(f"副本含未跟踪文件: {rel}")
        # 副本必须真的完整（不能因为「什么都没复制」而恰好没泄漏）
        if not (iso / "app/main.py").exists() or not (iso / "tests/conftest.py").exists():
            problems.append("副本不完整（缺 app/main.py 或 tests/conftest.py）")
    except Exception as exc:  # noqa: BLE001
        problems.append(f"副本构造失败: {exc!r}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return {
        "name": "isolated-copy-no-data",
        "ok": not problems,
        "rc": 0,
        "expect_rc": 0,
        "verdict": "副本只含 tracked 文件且 .env 为软链" if not problems else "副本把数据带出去了",
        "reason": "" if not problems else "; ".join(problems[:6]),
        "stderr_tail": "",
    }


def probe_shell_injections() -> list[dict]:
    """shell 劫持后，门要么给出**真实**结论，要么明确拒绝 —— 绝不能假绿。

    分两类判据（R1 Codex HIGH-5 新增后三条）：

    * **数据管道类**（假 dirname / 假 printf）：门应当照常工作，且输出里必须出现
      **真实**的受监视路径 —— 说明劫持没改变它在看什么。期望 rc=0。
    * **控制流类**（alias 令 ``[`` 恒假 / readonly 函数 / EXIT trap）：这些能让门
      「跳过判据直接说 unchanged」。判据是**不得出现假绿**：要么正常工作，要么
      带非零 rc 拒绝；绝不允许「没给命令却输出 unchanged 且 rc=0」。
    """
    results: list[dict] = []
    tmp = Path(tempfile.mkdtemp(prefix="w4-bashenv-"))
    fn_inject = tmp / "fn.sh"
    fn_inject.write_text(
        "printf() { builtin printf '%s' '0000000000000000000000000000000000000000000000000000000000000000'; }\n"
        "export -f printf\n"
        "dirname() { builtin printf '%s' '///data/nonexistent'; }\n"
        "export -f dirname\n",
        encoding="utf-8",
    )
    alias_inject = tmp / "alias.sh"
    alias_inject.write_text(
        "shopt -s expand_aliases\nalias [='builtin test x = y ; builtin test'\n",
        encoding="utf-8",
    )
    ro_inject = tmp / "readonly.sh"
    ro_inject.write_text(
        "dirname() { builtin printf '%s' '///data/nonexistent'; }\nreadonly -f dirname\nexport -f dirname\n",
        encoding="utf-8",
    )
    trap_inject = tmp / "trap.sh"
    trap_inject.write_text(
        "trap 'builtin printf \"RUNTIME-FILES: unchanged\\n\"; builtin exit 0' EXIT\n",
        encoding="utf-8",
    )

    expected_marker = str(BACKEND_DIR / "data/bug_log.jsonl")

    # ── 数据管道类：必须照常工作且看的是真实路径 ──────────────────────────
    pipeline_cases = [
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
        ("shell-bash-env", f"bash {GATE} -- /usr/bin/true", {"BASH_ENV": str(fn_inject)}),
        ("shell-readonly-func", f"bash {GATE} -- /usr/bin/true", {"BASH_ENV": str(ro_inject)}),
    ]
    for name, script, env_extra in pipeline_cases:
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

    # ── 控制流类：**不给命令**，门必须拒绝而不是空跑出 unchanged ────────────
    control_cases = [
        ("shell-alias-test-hijack", {"BASH_ENV": str(alias_inject)}),
        ("shell-exit-trap-hijack", {"BASH_ENV": str(trap_inject)}),
    ]
    for name, env_extra in control_cases:
        # 直接起门进程（见 _sh_direct 的说明）；故意不给 `--` 与命令
        proc = _sh_direct(["bash", str(GATE)], env_extra)
        fake_green = "RUNTIME-FILES: unchanged" in proc.stdout
        # 判据不能只是「没假绿」——那样「门因为别的原因崩了」也算过。必须是
        # **门自己认得出来的拒绝**：用法错误(2) 或 GATE-BROKEN(1)，且带对应文案。
        refused = (proc.returncode == 2 and "用法" in proc.stderr) or (
            proc.returncode == 1 and "GATE-BROKEN" in proc.stderr
        )
        ok = refused and not fake_green
        results.append(
            {
                "name": name,
                "ok": ok,
                "rc": proc.returncode,
                "expect_rc": "2(用法) 或 1(GATE-BROKEN)",
                "verdict": "空跑被门自己识别并拒绝"
                if ok
                else ("空跑却输出 unchanged（假绿）" if fake_green else "非门自身的拒绝"),
                "reason": ""
                if ok
                else f"rc={proc.returncode} fake_green={fake_green} stdout={proc.stdout[-200:]} stderr={proc.stderr[-200:]}",
                "stderr_tail": proc.stderr[-300:],
            }
        )

    shutil.rmtree(tmp, ignore_errors=True)
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
# M15 —— runtime 文件 **glob 分支**的探针族（CARD-W4-3b，2026-09-05）
#
# 缺口原文（X4 验收单 §7.9a #15）：`runtime_sha.sh` 在 2026-09-04 修了一个真·假绿
# （journal 改名成 `vault_index_pending__<key>.jsonl` 后，固定文件名锚点落空，
# `absent == absent` 让门恒判 unchanged），但**没有任何一条探针覆盖那条修复**——
# 22 条注册探针里唯一碰运行时文件的 `shell-can-report-changed` 写的是固定项
# `data/bug_log.jsonl`，走的是 WATCHED_FIXED 分支。下一个人把 glob 那几行删掉，
# 29/29 照样全绿。「加门 ≠ 加强度」的教科书形态。
#
# 本族六条，覆盖 glob 分支的可能坏法 + 收窄后的旧名回归 + 展开顺序：
#   1. glob-absent-to-present  —— 正探针：after 才出现的文件必须被抓（rc=1 CHANGED）
#   2. glob-cached-expansion   —— 对照：把展开提到快照外只算一次 ⇒ 必须瞎（unchanged）
#   3. glob-pattern-neutralized—— 对照：模式换成不匹配的 ⇒ 必须瞎（unchanged）
#   4. glob-sidecar-excluded   —— M14 收窄的正证据：单下划线旁文件**不该**进监视面
#   5. glob-expansion-sorted   —— M13：展开必须按字节序，不是 readdir 顺序
#   6. legacy-journal-watched  —— M14 收窄的安全证据：旧固定名仍必须被抓
#
# 2 和 3 是「拆了要瞎」型对照：它们证明 1 的红**来自 glob 分支**，而不是被固定项
# 或别的什么顺带抓到的（判据绑定「被哪一层抓的」，不是「有东西红了」）。
# 全部只在 tmp 假 backend 里造文件，真实工作树一个字节不碰。
# ═══════════════════════════════════════════════════════════════════════════

#: 假 backend 里 glob 分支的目标文件名 —— 必须是**命名空间形态**（双下划线），
#: 与 `vault_state_paths.namespaced_state_path()` 的产出同形。
_GLOB_JOURNAL_NAME = "vault_index_pending__w4probe.jsonl"
#: 单下划线的「旁文件」—— 生产写侧**产不出**这个形态，收窄后不该被监视。
_SIDECAR_NAME = "vault_index_pending_backup.jsonl"
#: G2-5 之前的旧固定名 —— 收窄后由 WATCHED_FIXED 精确项承接。
_LEGACY_JOURNAL_NAME = "vault_index_pending.jsonl"

#: snapshot() 里「每次快照重新展开 glob」那一段的**逐字锚点**。
#: 变异靠它定位；锚点对不上就说明生产代码改了形状，探针必须当场喊脱节而不是静默放过。
_GLOB_EXPAND_ANCHOR = """  local __raw __sorted
  for g in "${WATCHED_GLOBS[@]}"; do
    __raw="$(builtin compgen -G "$g" || true)"
    [ -n "$__raw" ] || continue
    __sorted="$(builtin printf '%s\\n' "$__raw" | LC_ALL=C "$SORT_BIN")" || {
      builtin printf 'RUNTIME-FILES: GATE-BROKEN — glob 展开排序失败（%s），拒绝给出结论\\n' \\
        "$SORT_BIN" >&2
      exit 1
    }
    while IFS= read -r f; do
      [ -n "$f" ] && targets+=("$f")
    done <<<"$__sorted"
  done"""

#: 变异体：把展开**提到 snapshot 之外**只算一次（= 「缓存 glob 展开」）。
#: before/after 共用同一份预展开列表，after 才被创建的文件永远进不来。
_GLOB_EXPAND_CACHED = """  if [ "${#W4_PROBE_CACHED[@]}" -gt 0 ]; then
    targets+=("${W4_PROBE_CACHED[@]}")
  fi"""

_GLOB_CACHE_PRELUDE = """W4_PROBE_CACHED=()
for __pg in "${WATCHED_GLOBS[@]}"; do
  while IFS= read -r __pf; do
    [ -n "$__pf" ] && W4_PROBE_CACHED+=("$__pf")
  done < <(builtin compgen -G "$__pg" || true)
done

snapshot() {"""


def _fake_backend(prefix: str, gate_text: str | None = None) -> tuple[Path, Path]:
    """在 tmp 里搭一棵最小假 backend，返回 ``(tmp_root, fake_backend)``。

    ⛔ 只在 tmp 造文件 —— 卡文隔离条款：真实 ``backend/app/data`` / ``backend/data``
    一个字节都不碰（那两处是**生产运行时数据**，不是测试夹具）。
    ``gate_text`` 不给就原样拷贝生产脚本；给了就写入变异体（对照探针用）。
    """
    tmp = Path(tempfile.mkdtemp(prefix=prefix))
    fake = tmp / "backend"
    (fake / "app" / "data").mkdir(parents=True)
    (fake / "tests").mkdir()
    (fake / "scripts").mkdir()
    (fake / "data" / "outbox").mkdir(parents=True)
    (fake / "app" / "main.py").write_text("# fake\n", encoding="utf-8")
    dst = fake / "scripts" / "lifespan_isolation_runtime_sha.sh"
    if gate_text is None:
        shutil.copy2(GATE, dst)
    else:
        dst.write_text(gate_text, encoding="utf-8")
    return tmp, fake


def _run_gate_creating(fake: Path, filename: str) -> subprocess.CompletedProcess:
    """让被包裹命令在假 backend 的 ``app/data/`` 下**新建** ``filename``。

    快照前该文件不存在 —— 这正是「只有 after 那次展开才看得见」的形态。
    """
    target = fake / "app" / "data" / filename
    assert not target.exists(), f"探针前提被破坏：{target} 在快照前就存在"
    gate = fake / "scripts" / "lifespan_isolation_runtime_sha.sh"
    return _sh(f"bash {gate} -- /bin/sh -c 'printf \"w4probe\\n\" > {target}'")


def _glob_probe_result(
    name: str,
    proc: subprocess.CompletedProcess,
    *,
    expect_changed: bool,
    verdict_ok: str,
    verdict_bad: str,
) -> dict:
    """glob 族的统一判据。

    ⛔ 期望「变绿」的对照探针**必须显式排除 GATE-BROKEN**：变异如果把脚本弄崩了，
    rc 也可能非 0 / 输出里没有 CHANGED —— 那是「门坏了」而不是「门瞎了」，两者
    对本探针是完全不同的结论。判据绑定的是**由哪一条路径给出的哪一句结论**。
    """
    changed = "RUNTIME-FILES: CHANGED" in proc.stdout
    unchanged = "RUNTIME-FILES: unchanged" in proc.stdout
    broken = "GATE-BROKEN" in proc.stdout or "GATE-BROKEN" in proc.stderr
    if expect_changed:
        ok = proc.returncode == 1 and changed and not broken
    else:
        ok = proc.returncode == 0 and unchanged and not broken
    return {
        "name": name,
        "ok": ok,
        "rc": proc.returncode,
        "expect_rc": 1 if expect_changed else 0,
        "verdict": verdict_ok if ok else verdict_bad,
        "reason": ""
        if ok
        else (
            f"rc={proc.returncode} changed={changed} unchanged={unchanged} "
            f"gate_broken={broken} stdout={proc.stdout[-400:]}"
        ),
        "stderr_tail": proc.stderr[-300:],
    }


def probe_runtime_glob_absent_to_present() -> dict:
    """正探针：快照前不存在、被包裹命令新建的 journal 必须让门判 CHANGED。

    这是 M15 缺口的直接补门 —— 覆盖 ``WATCHED_GLOBS`` 的 absent→present 分支。
    """
    tmp, fake = _fake_backend("w4-glob-new-")
    proc = _run_gate_creating(fake, _GLOB_JOURNAL_NAME)
    shutil.rmtree(tmp, ignore_errors=True)
    return _glob_probe_result(
        "runtime-glob-absent-to-present",
        proc,
        expect_changed=True,
        verdict_ok="glob 分支能抓到新建 journal",
        verdict_bad="新建了命名空间 journal 却仍判 unchanged（glob 分支是死的）",
    )


def probe_runtime_glob_cached_expansion_is_blind() -> dict:
    """对照：把 glob 展开提到快照外只算一次 ⇒ 门必须**瞎**（判 unchanged）。

    证明上一条的红**来自「每次快照重新展开」这几行**，不是别处顺带抓到的。
    """
    text = GATE.read_text(encoding="utf-8")
    assert _GLOB_EXPAND_ANCHOR in text, "glob 展开锚点不在脚本里 —— 探针与被测对象已脱节"
    assert "\nsnapshot() {" in text, "snapshot 定义锚点不在脚本里 —— 探针与被测对象已脱节"
    mutated = text.replace(_GLOB_EXPAND_ANCHOR, _GLOB_EXPAND_CACHED)
    mutated = mutated.replace("\nsnapshot() {", "\n" + _GLOB_CACHE_PRELUDE, 1)
    tmp, fake = _fake_backend("w4-glob-cached-", gate_text=mutated)
    proc = _run_gate_creating(fake, _GLOB_JOURNAL_NAME)
    shutil.rmtree(tmp, ignore_errors=True)
    return _glob_probe_result(
        "runtime-glob-cached-expansion",
        proc,
        expect_changed=False,
        verdict_ok="缓存展开后门确实瞎了 ⇒ 「每次重新展开」承重",
        verdict_bad="缓存了展开却仍判 CHANGED —— 上一条的红不来自 glob 分支",
    )


def probe_runtime_glob_pattern_neutralized_is_blind() -> dict:
    """对照：把 glob 模式换成永不匹配的 ⇒ 门必须**瞎**（判 unchanged）。

    刻意**不**删除数组元素：删了会撞上 ``EXPECTED_GLOB_COUNT`` 自检，门喊
    GATE-BROKEN —— 那验的是计数自检，不是 glob 项本身承重。
    """
    text = GATE.read_text(encoding="utf-8")
    real = '"${BACKEND_DIR}/app/data/vault_index_pending__*.jsonl"'
    assert real in text, "WATCHED_GLOBS 的模式不在脚本里 —— 探针与被测对象已脱节"
    mutated = text.replace(real, '"${BACKEND_DIR}/app/data/w4-never-matches__*.jsonl"')
    tmp, fake = _fake_backend("w4-glob-neutral-", gate_text=mutated)
    proc = _run_gate_creating(fake, _GLOB_JOURNAL_NAME)
    shutil.rmtree(tmp, ignore_errors=True)
    return _glob_probe_result(
        "runtime-glob-pattern-neutralized",
        proc,
        expect_changed=False,
        verdict_ok="换掉模式后门确实瞎了 ⇒ 这条 glob 项承重",
        verdict_bad="模式已换成永不匹配却仍判 CHANGED —— 红因不明",
    )


def probe_runtime_glob_sidecar_excluded() -> dict:
    """M14 收窄的正证据：单下划线**旁文件**不该进监视面 ⇒ 门判 unchanged。

    ``vault_index_pending_backup.jsonl`` 是人手放的备份形态，生产写侧
    （``legacy_state_path`` / ``namespaced_state_path``）**产不出**它。收窄前的
    ``vault_index_pending*.jsonl`` 会把它收进来，于是「谁在 app/data 放了个备份」
    就让门判 CHANGED —— 假红。本探针钉住收窄后的行为。
    """
    tmp, fake = _fake_backend("w4-glob-sidecar-")
    proc = _run_gate_creating(fake, _SIDECAR_NAME)
    shutil.rmtree(tmp, ignore_errors=True)
    return _glob_probe_result(
        "runtime-glob-sidecar-excluded",
        proc,
        expect_changed=False,
        verdict_ok="旁文件不在监视面（M14 收窄生效）",
        verdict_bad="单下划线旁文件仍被收进监视面 —— glob 比写侧能产出的形态宽",
    )


def probe_runtime_glob_expansion_sorted() -> dict:
    """M13：glob 项在快照里必须**按字节序排列**，不能是 readdir 顺序。

    2026-09-05 于 GNU bash 3.2.57(1)-release (arm64-apple-darwin25) 实测：
    ``compgen -G`` 返回的是 **readdir 顺序**（六个文件实测得到 alpha, 2, Mid,
    zeta, beta, 10），而 ``for f in glob`` 才排序（10, 2, alpha, beta, Mid, zeta）。
    脚本原注释断言的「compgen -G 展开本身已排序、不必外部 sort」因此不成立。
    顺序不稳定会让 before/after 因**排列不同**而字符串不等 ⇒ 判 CHANGED（假红）。

    本探针用同一组会让 readdir 乱序的文件名，直接从门的 before 段读回实际排列。
    判据是「**glob 项那几行**恰好等于字典序」——不是「跑完没红」。

    ⛔ 还要**验证乱序前提**（round-1 Codex LOW-4）：先直接问一次未经排序的
    ``compgen -G``，确认它在**本次运行的这个文件系统上**确实给出非字节序。前提不
    成立时，「删掉 sort 会翻红」这句话在此环境下不成立 —— 那就判 FAIL 并说清楚
    「承重未验证」，而不是绿着糊过去（探针的价值来自它能失败）。
    """
    tmp, fake = _fake_backend("w4-glob-sorted-")
    data = fake / "app" / "data"
    # 刻意用会让 readdir 顺序偏离字典序的一组名字（创建顺序也打乱）。
    names = [f"vault_index_pending__{k}.jsonl" for k in ("zeta", "alpha", "Mid", "beta", "10", "2")]
    for n in names:
        (data / n).write_text("x\n", encoding="utf-8")
    # 前提探测：未经排序的原始展开顺序。
    raw_proc = _sh(f"/bin/bash --noprofile --norc -c 'builtin compgen -G \"{data}/vault_index_pending__*.jsonl\"'")
    raw = [line.rsplit("/", 1)[-1] for line in raw_proc.stdout.splitlines() if line.strip()]
    expected = sorted(names)
    premise_ok = sorted(raw) == expected and raw != expected

    gate = fake / "scripts" / "lifespan_isolation_runtime_sha.sh"
    proc = _sh(f"bash {gate} -- /usr/bin/true")
    seen: list[str] = []
    for line in proc.stdout.splitlines():
        if line.startswith("=== 执行被包裹命令"):
            break  # 只读 before 段
        for n in names:
            if line.endswith(f"/{n}"):
                seen.append(n)
    sorted_ok = proc.returncode == 0 and seen == expected and "GATE-BROKEN" not in proc.stdout
    ok = sorted_ok and premise_ok
    shutil.rmtree(tmp, ignore_errors=True)
    if not premise_ok:
        reason = (
            f"乱序前提不成立：原始 compgen 展开为 {raw}（排序后 {expected}）—— "
            "本环境下去掉 sort 也会通过，本探针无鉴别力，不能声称排序承重已验证"
        )
    elif not sorted_ok:
        reason = f"rc={proc.returncode} 实得={seen} 期望={expected}"
    else:
        reason = ""
    return {
        "name": "runtime-glob-expansion-sorted",
        "ok": ok,
        "rc": proc.returncode,
        "expect_rc": 0,
        "verdict": "glob 展开按字节序排好（且原始展开确实乱序 ⇒ 排序承重）"
        if ok
        else ("乱序前提不成立，承重未验证" if not premise_ok else "glob 展开顺序不是字节序"),
        "reason": reason,
        "stderr_tail": proc.stderr[-300:],
    }


def probe_runtime_legacy_journal_watched() -> dict:
    """M14 收窄的**安全**证据：旧固定名仍必须被抓 ⇒ 门判 CHANGED。

    收窄是放松方向。旧名 ``vault_index_pending.jsonl`` 以前靠那条过宽 glob 顺带
    收进来，收窄后必须由 ``WATCHED_FIXED`` 的精确项接住 —— 接不住就是监视面变窄。
    """
    tmp, fake = _fake_backend("w4-glob-legacy-")
    proc = _run_gate_creating(fake, _LEGACY_JOURNAL_NAME)
    shutil.rmtree(tmp, ignore_errors=True)
    return _glob_probe_result(
        "runtime-legacy-journal-watched",
        proc,
        expect_changed=True,
        verdict_ok="旧固定名仍在监视面（收窄没让它漏网）",
        verdict_bad="收窄之后旧固定名漏网 —— 监视面实际变窄了",
    )


# ═══════════════════════════════════════════════════════════════════════════


def main() -> int:
    results: list[dict] = [
        probe_no_guard_control(),
        probe_lowlevel("raw", "lowlevel-_socket.socket"),
        probe_lowlevel("sockettype", "lowlevel-SocketType"),
        probe_lowlevel("connect_ex", "lowlevel-connect_ex"),
        probe_lowlevel("index", "lowlevel-__index__-port"),
        probe_real_blocked_port(),
        probe_toctou_index_port(),
        probe_drift_reinstall(),
        probe_extract_port_mutation_detected(),
        probe_uvloop_reimport_blocked(),
        probe_late_after_finalizing(),
        probe_plugin_import_installs(),
        probe_audit_liveness_control(),
        probe_ownership_model(),
        probe_drift_in_test_fails_the_session(),
        probe_require_blocked_target(),
        probe_require_blocked_target_positive(),
        probe_late_connection_forces_rc(),
        probe_late_connection_negative_control(),
        probe_ledger_written(),
        probe_isolated_copy_carries_no_data(),
        probe_shell_selftest_is_load_bearing(),
        probe_shell_can_report_changed(),
        # M15 族：runtime 文件的 **glob 分支**（CARD-W4-3b）。前三条是
        # 「正探针 + 两条拆了要瞎的对照」，后两条钉住 M14 收窄的两个方向。
        probe_runtime_glob_absent_to_present(),
        probe_runtime_glob_cached_expansion_is_blind(),
        probe_runtime_glob_pattern_neutralized_is_blind(),
        probe_runtime_glob_sidecar_excluded(),
        probe_runtime_glob_expansion_sorted(),
        probe_runtime_legacy_journal_watched(),
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
