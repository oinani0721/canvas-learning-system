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

    # ═══════════════════════════════════════════════════════════════════════
    # CARD-W4-6（2026-09-05）—— exec 层本身是否承重 + 重入票据
    #
    # 上面四条 pipeline 探针**证明不了 exec 层**：注入的导出函数即便原样穿过
    # `exec`，也会被纵深第二层（`unset -f` 循环）清掉，门照样给出正确答案。
    # 本机实测的缺陷正是藏在这个盲区里 —— bash 3.2.57 把导出函数放进名为
    # `BASH_FUNC_f%%` 的环境变量，`compgen -e` 看不见它，于是 exec 那句的 `-u`
    # 列表**恒空**，一个导出函数都没摘。四条探针全绿，缺陷照样在。
    #
    # 要让判据绑定「是被**哪一层**拦下的」，就得**拆掉另一层**：下面三条用
    # `_fake_backend(gate_text=…)` 造一份删去第二层 `unset -f` 循环的门副本，
    # 此时还能挡住注入的就只剩 exec 层。锚点命中数必须恰好 1 —— 生产代码改了
    # 形状时探针要当场喊脱节，而不是静默变成「没拆」（那会让这三条恒绿假通过）。
    # ═══════════════════════════════════════════════════════════════════════
    _LAYER2_ANCHOR = (
        "for __fn in $(builtin compgen -A function 2>/dev/null); do\n"
        '  builtin unset -f "$__fn" 2>/dev/null || true\n'
        "done\n"
    )
    _gate_text = GATE.read_text(encoding="utf-8")
    _anchor_hits = _gate_text.count(_LAYER2_ANCHOR)
    _no_layer2 = _gate_text.replace(_LAYER2_ANCHOR, "# [W4-6 探针] 纵深第二层被拆掉：此处只剩 exec 层\n")

    def _emit(name: str, ok: bool, proc, expect_rc, verdict_ok: str, verdict_bad: str, reason: str) -> None:
        results.append(
            {
                "name": name,
                "ok": ok,
                "rc": proc.returncode if proc is not None else -1,
                "expect_rc": expect_rc,
                "verdict": verdict_ok if ok else verdict_bad,
                "reason": "" if ok else reason,
                "stderr_tail": (proc.stderr[-300:] if proc is not None else ""),
            }
        )

    def _wrapped_output(stdout: str) -> list[str]:
        """切出**被包裹命令自己**的那几行 —— 门的其余输出不算数。

        ⛔ Codex round-1 LOW-5：初版把 `"function" not in proc.stdout` 铺在整个
        stdout 上。门会打印完整的受监视路径，tmp 目录名里只要恰好含 `function`
        就误拒；反过来，阳性词 `builtin` / `file` 也可能来自路径而不是被包裹命令，
        于是「命令真的跑过」这半句判据是假的。改成按门自己的分节标记切片，再逐项
        比对，判据就只看被包裹命令的输出。
        """
        start = stdout.find("=== 执行被包裹命令 ===")
        if start < 0:
            return []
        rest = stdout[start:].split("\n")[1:]  # 去掉分节标题行
        out: list[str] = []
        for line in rest:
            if line.startswith("=== RUNTIME-FILES after"):
                break
            if line.startswith("$ "):  # 门回显的命令行，不是命令的输出
                continue
            if line.strip():
                out.append(line.strip())
        return out

    # ── 拆掉第二层的门副本：三条都要求门**自己**给出正确答案 ────────────────
    #: (探针名, 注入文件, 被包裹命令 argv, 期望的被包裹命令输出)
    #: 第三条的期望值是**精确列表** `["builtin", "file"]`：`printf` 必须仍是
    #: builtin、`dirname` 必须仍是外部命令，两条查询都要有输出 —— 既证明注入的
    #: 函数没进被包裹命令的环境，也证明命令确实跑过（空输出满足不了精确相等）。
    exec_layer_cases = [
        (
            "shell-bash-env-exec-layer-is-load-bearing",
            fn_inject,
            ["/usr/bin/true"],
            None,
        ),
        (
            "shell-exec-strips-readonly-func",
            ro_inject,
            ["/usr/bin/true"],
            None,
        ),
        (
            "shell-wrapped-cmd-sees-no-injected-func",
            fn_inject,
            ["/bin/bash", "-c", "type -t printf; type -t dirname"],
            ["builtin", "file"],
        ),
    ]
    for name, inject, wrapped, expect_wrapped in exec_layer_cases:
        if _anchor_hits != 1:
            _emit(
                name,
                False,
                None,
                0,
                "",
                "第二层锚点与生产代码脱节",
                f"`unset -f` 循环锚点在 runtime_sha.sh 里命中 {_anchor_hits} 次（须恰好 1）——"
                " 探针无法证明 exec 层承重，拒绝报绿",
            )
            continue
        ftmp, fake = _fake_backend("w4-exec-layer-", gate_text=_no_layer2)
        try:
            fgate = fake / "scripts" / "lifespan_isolation_runtime_sha.sh"
            marker = str(fake / "data/bug_log.jsonl")
            proc = _sh_direct(["bash", str(fgate), "--", *wrapped], {"BASH_ENV": str(inject)})
            ok = proc.returncode == 0 and marker in proc.stdout and "RUNTIME-FILES: unchanged" in proc.stdout
            got_wrapped = _wrapped_output(proc.stdout) if expect_wrapped is not None else None
            if ok and expect_wrapped is not None:
                ok = got_wrapped == expect_wrapped
            _emit(
                name,
                ok,
                proc,
                0,
                "exec 层自己摘掉了导出函数",
                "拆掉纵深第二层后导出函数活了下来（exec 层不承重）",
                f"rc={proc.returncode} marker={marker in proc.stdout} "
                f"被包裹输出={got_wrapped!r}（期望 {expect_wrapped!r}） "
                f"stdout={proc.stdout[-300:]} stderr={proc.stderr[-300:]}",
            )
        finally:
            shutil.rmtree(ftmp, ignore_errors=True)

    # ── 票据：旧的 W4_SHA_GATE_REEXEC=1 被照抄，清洗仍必须执行 ──────────────
    # before（开工 SHA）实测：readonly -f 的注入函数活到第二层，`unset -f` 对它
    # 失败 ⇒ `RUNTIME-FILES: GATE-BROKEN — 清不掉的 shell 函数仍在: dirname`、rc=1。
    # 用 fn.sh（非 readonly）做同形对照时第二层会兜住、修复前后同 rc —— 那条
    # **不能**作承重判据，所以这里只用 readonly.sh。
    proc = _sh_direct(
        ["bash", str(GATE), "--", "/usr/bin/true"],
        {"W4_SHA_GATE_REEXEC": "1", "BASH_ENV": str(ro_inject)},
    )
    _emit(
        "shell-reexec-sentinel-preset",
        proc.returncode == 0 and expected_marker in proc.stdout and "RUNTIME-FILES: unchanged" in proc.stdout,
        proc,
        0,
        "预设旧哨兵不再能跳过清洗",
        "调用者预设一个环境变量就跳过了整段清洗",
        f"rc={proc.returncode} stdout={proc.stdout[-300:]} stderr={proc.stderr[-300:]}",
    )

    # ── 三条拒绝分支，**每条绑定自己的文案** ────────────────────────────────
    #
    # ⛔ Codex round-1 MEDIUM-2 的整改：初版三条都只断言 `"GATE-BROKEN" in stderr`。
    # 那是**粗判据** —— 门有三条不同的拒绝分支（标记不匹配 / BASH_ENV 非空 /
    # 环境里有导出函数），任一条都能满足它。于是「PID 一致 + 导出函数」这条分支
    # 实际上从来没被跑到（它带着非空 BASH_ENV，在**更早**的分支就被拒了），把那段
    # 检查删掉探针照样全绿。判据必须绑定「是被**哪一层**拒的」。
    #
    # 每个 case: (探针名, 起法, 环境, 期望的拒绝文案片段, verdict 文案, 说明)
    def _refusal_case(name, run, expect_msg, verdict_ok, verdict_bad):
        try:
            proc = run()
            ok = proc.returncode == 1 and expect_msg in proc.stderr and "RUNTIME-FILES: unchanged" not in proc.stdout
            reason = (
                f"rc={proc.returncode} 期望文案={expect_msg!r} 命中={expect_msg in proc.stderr} "
                f"stdout={proc.stdout[-200:]} stderr={proc.stderr[-300:]}"
            )
        except subprocess.TimeoutExpired:
            proc, ok = None, False
            reason = "门没有在 timeout 内退出 —— 疑似触发了无界重入"
        _emit(name, ok, proc, 1, verdict_ok, verdict_bad, reason)

    # ① 标记不匹配 ⇒ 走「与本进程 PID 不一致」那条分支
    _refusal_case(
        "shell-reexec-sentinel-forged",
        lambda: _sh_direct(["bash", str(GATE), "--w4-reexec", "w4-forged-not-a-real-ticket", "--", "/usr/bin/true"]),
        "与本进程 PID 不一致",
        "标记不匹配被该分支拒绝",
        "标记不匹配没被拒绝（假绿 / 无界重入 / 被别的分支拒的）",
    )

    # ② PID 一致（调用者自己 exec 继承 PID —— 本卡**未关闭**的残余可伪造面）
    #    但 BASH_ENV 非空 ⇒ 走「BASH_ENV/ENV 仍有值」那条分支。
    _refusal_case(
        "shell-forged-ticket-with-injection-refused",
        lambda: _sh(
            f'exec bash {GATE} --w4-reexec "w4-sha-gate-reexec-v1:$$" -- /usr/bin/true',
            {"BASH_ENV": str(fn_inject)},
        ),
        "BASH_ENV/ENV 仍有值",
        "PID 可伪造，但非空 BASH_ENV 被该分支拦下",
        "继承 PID 后带着 BASH_ENV 跑成了结论",
    )

    # ③ PID 一致 **且** 注入文件把 BASH_ENV 自己清掉，只留一个导出函数
    #    ⇒ 必须走「环境里仍有导出函数」那条分支。这才是 ② 到不了的那一段。
    selfunset_inject = tmp / "selfunset.sh"
    selfunset_inject.write_text(
        "unset BASH_ENV\nw4probe_fn() { :; }\nexport -f w4probe_fn\n",
        encoding="utf-8",
    )
    _refusal_case(
        "shell-ticket-ok-but-exported-func-refused",
        lambda: _sh(
            f'exec bash {GATE} --w4-reexec "w4-sha-gate-reexec-v1:$$" -- /usr/bin/true',
            {"BASH_ENV": str(selfunset_inject)},
        ),
        "仍有导出函数",
        "残留导出函数被**导出函数**分支拦下",
        "残留导出函数没被该分支拦下",
    )

    # ── 本卡自己引入的假绿面：拒绝路径落在注入者 EXIT trap 射程里 ──────────
    # 这条分支的 exit 发生在 exec **之前**。2026-09-06 作者自测：不清 trap 时
    # stderr 打了 GATE-BROKEN，注入者的 EXIT trap 随后打印 `RUNTIME-FILES:
    # unchanged` 并把 rc 改写成 **0**。判据同时看 rc 与 stdout —— 只看其一都会
    # 漏：rc 被改写而文案还在，stdout 假绿而 stderr 也还在。
    try:
        proc = _sh_direct(
            ["bash", str(GATE), "--w4-reexec", "w4-forged-not-a-real-ticket", "--", "/usr/bin/true"],
            {"BASH_ENV": str(trap_inject)},
        )
        trap_ok = proc.returncode == 1 and "RUNTIME-FILES: unchanged" not in proc.stdout
        trap_reason = (
            f"rc={proc.returncode}（期望 1；0 = 被 EXIT trap 改写）"
            f" 假绿={'RUNTIME-FILES: unchanged' in proc.stdout} stdout={proc.stdout[-200:]}"
        )
    except subprocess.TimeoutExpired:
        proc, trap_ok = None, False
        trap_reason = "门没有在 timeout 内退出"
    _emit(
        "shell-forged-ticket-under-exit-trap",
        trap_ok,
        proc,
        1,
        "拒绝路径先清 trap，rc 与 stdout 都没被改写",
        "拒绝路径落在 EXIT trap 射程里（rc 被改写成 0 或 stdout 假绿）",
        trap_reason,
    )

    # ── 假红回归门：值含换行的**普通**变量不得被当成导出函数（Codex MEDIUM-1）──
    # 初版按行扫 `env` 输出，无法区分「条目边界」与「值里的换行」。于是一个完全
    # 正常的调用——只要环境里有个多行变量、其中一行以 `BASH_FUNC_` 开头——就会被
    # 判 GATE-BROKEN（**假红**，不需要任何注入）。修法是改用 `env -0`（NUL 分隔）。
    # 这条探针不带任何注入，它证明的是「门没有因为修复而开始误伤正常环境」。
    carrier = "harmless-value\nBASH_FUNC_notafunction%%=this-is-just-text\ntail"
    proc = _sh_direct(["bash", str(GATE), "--", "/usr/bin/true"], {"W4_PROBE_CARRIER": carrier})
    _emit(
        "shell-multiline-env-var-not-mistaken-for-func",
        proc.returncode == 0 and expected_marker in proc.stdout and "RUNTIME-FILES: unchanged" in proc.stdout,
        proc,
        0,
        "多行普通变量没有被误当成导出函数",
        "普通多行变量把正常调用弄成了 GATE-BROKEN（假红）",
        f"rc={proc.returncode} stdout={proc.stdout[-200:]} stderr={proc.stderr[-300:]}",
    )

    # ── 枚举失败必须与「零个匹配」区分（Codex round-1 LOW-4）──────────────────
    # 进程替换拿不到生产者的退出码，`pipefail` 也不覆盖它 —— 「`env -0` 没跑起来 /
    # 输出被截断」会表现成「环境里没有导出函数」而**静默通过**。门靠一个完成哨兵
    # 条目区分两者。这个失败形态从生产输入到不了（`env -0` 在本机可用），所以用
    # 门副本模拟：把哨兵的产出去掉、检查留着 ⇒ 门必须拒绝，而不是当作「没有残留」。
    # ⛔ 两趟各有一段枚举 + 一段完成检查，**必须分开钉**（对抗复核 F1b）：
    # 「环境枚举未完整产出」这个前缀在门里出现两次，只断言它 ⇒ 探针绑定不了是哪一趟
    # 拒的；而且把两处哨兵产出一起删掉时执行必然停在第一趟，**第二趟那段检查根本
    # 到不了 —— 删掉它全部探针照样绿**。这与 Codex round-1 MEDIUM-2 修掉的是同一类
    # 缺陷（判据必须绑定被哪一层拒的），换了个位置复发。
    # 修法：按 `__w4_stale=""`（只出现在第二趟）把脚本切成两半，各自只改自己那半的
    # 哨兵产出，并断言**该趟独有的**文案尾巴。
    _SENTINEL_EMIT = "{ /usr/bin/env -0 && builtin printf '%s\\0' \"$__W4_ENV_SENTINEL\"; }"
    _CHECK_ANCHOR = '    case "$__w4_env_ok" in\n      1) ;;'
    _PASS2_SPLIT = '__w4_stale=""'
    _head, _sep, _tail = _gate_text.partition(_PASS2_SPLIT)
    _enum_cases = [
        # (探针名, 变异后的门文本 or None, 该趟独有的文案尾巴, verdict)
        (
            "shell-env-enum-failure-is-fail-closed-pass1",
            (_head.replace(_SENTINEL_EMIT, "{ /usr/bin/env -0; }") + _sep + _tail) if _sep else None,
            "拒绝在不知道注入面的情况下继续",
            "第一趟枚举不完整时拒绝给结论",
        ),
        (
            "shell-env-enum-failure-is-fail-closed-pass2",
            (_head + _sep + _tail.replace(_SENTINEL_EMIT, "{ /usr/bin/env -0; }")) if _sep else None,
            "拒绝把「没看见残留」当成「没有残留」",
            "第二趟枚举不完整时拒绝给结论",
        ),
    ]
    # 锚点自检：产出站点与**检查**站点都必须各 2 处。只数产出站点的话，把第二趟那段
    # 检查整个删掉，计数仍是 2、探针仍绿（判据不能自指，也不能只盯半边）。
    _emit_hits, _check_hits = _gate_text.count(_SENTINEL_EMIT), _gate_text.count(_CHECK_ANCHOR)
    _split_ok = bool(_sep) and _head.count(_SENTINEL_EMIT) == 1 and _tail.count(_SENTINEL_EMIT) == 1
    for name, mutated, expect_tail, verdict_ok in _enum_cases:
        if _emit_hits != 2 or _check_hits != 2 or not _split_ok or mutated is None:
            _emit(
                name,
                False,
                None,
                1,
                "",
                "枚举哨兵锚点与生产代码脱节",
                f"哨兵产出命中 {_emit_hits}（须 2）、完成检查命中 {_check_hits}（须 2）、"
                f"两趟切分{'成立' if _split_ok else '不成立'} —— 拒绝报绿",
            )
            continue
        stmp, sfake = _fake_backend(f"w4-env-enum-{name[-5:]}-", gate_text=mutated)
        try:
            sgate = sfake / "scripts" / "lifespan_isolation_runtime_sha.sh"
            proc = _sh_direct(["bash", str(sgate), "--", "/usr/bin/true"])
            _emit(
                name,
                proc.returncode == 1 and expect_tail in proc.stderr and "RUNTIME-FILES: unchanged" not in proc.stdout,
                proc,
                1,
                verdict_ok,
                "枚举不完整被当成『没有残留』而放行（或被另一趟拒的）",
                f"rc={proc.returncode} 期望文案={expect_tail!r} 命中={expect_tail in proc.stderr} "
                f"stdout={proc.stdout[-200:]} stderr={proc.stderr[-300:]}",
            )
        finally:
            shutil.rmtree(stmp, ignore_errors=True)

    # ── 调用者导出的 SHELLOPTS 不得把**正常**调用弄成静默 rc=1（存量缺陷）──────
    # bash 启动会导入 SHELLOPTS 并置位选项，而门的 `set -uo pipefail` 只加不减。
    # `errexit` 下：函数表空（正常情形）⇒ `compgen -A function` rc=1 + pipefail
    # ⇒ 第二层 `__leftover=` 赋值 rc=1 ⇒ 静默退出，rc=1 零输出，而 rc=1 正是门文档里
    # 「文件被改」的码。方向是反的：健康才死，留着脏函数反而能把话说完。
    # 修法是在 exec 参数里 `-u SHELLOPTS`。判据要求**完整结论**，不只看 rc。
    proc = _sh_direct(["bash", str(GATE), "--", "/usr/bin/true"], {"SHELLOPTS": "errexit"})
    _emit(
        "shell-shellopts-errexit-does-not-false-red",
        proc.returncode == 0 and expected_marker in proc.stdout and "RUNTIME-FILES: unchanged" in proc.stdout,
        proc,
        0,
        "调用者的 SHELLOPTS 被 exec 摘掉，正常调用仍给出结论",
        "调用者导出 SHELLOPTS=errexit 就让正常调用静默 rc=1（假红）",
        f"rc={proc.returncode} stdout={proc.stdout[-200:]} stderr={proc.stderr[-200:]}",
    )

    # ── 花名册门：门头注释声称的条数与清单，必须与本函数实际产出的探针名对得上 ──
    #
    # ⛔ 「数字与清单不一致」在 runtime_sha.sh 里已被更正**三次**（5→6 / 11 漏一个 /
    # 15 漏一个）。前两次的处置都是「把注释改对」，然后第三次照旧发生 —— 说明
    # **写在注释里的规矩管不住它自己**，得有人跑。这条把那句承重声明变成判据。
    #
    # 判据不自指：它比对的是**两份独立产物** —— 门脚本注释里的声明（文档）与本文件
    # 的 AST（代码），任何一边漂了都红。用 AST 而不是 grep 整个文件：只数
    # `probe_shell_injections()` **函数体内**的 `shell-*` 字符串常量，别处提到的
    # 名字（如本注释、别的函数）不算进来。
    roster_problems: list[str] = []
    try:
        import ast as _ast
        import re as _re

        _self_src = Path(__file__).read_text(encoding="utf-8")
        _fn = next(
            n
            for n in _ast.walk(_ast.parse(_self_src))
            if isinstance(n, _ast.FunctionDef) and n.name == "probe_shell_injections"
        )
        actual = {
            n.value
            for n in _ast.walk(_fn)
            if isinstance(n, _ast.Constant) and isinstance(n.value, str) and _re.fullmatch(r"shell-[a-z0-9-]+", n.value)
        }
        m = _re.search(r"由 \*\*(\d+) 条\*\* shell 探针承重", _gate_text)
        # 清单区 = 从那句声明起，到「数字与清单不一致」那段历史记录为止。
        # ⚠️ 取名面必须**恰好等于清单区**，不能是整个文件：历史记录那几行会点名
        # 「当年漏列的那个探针」，而那个名字今天可能已经被拆掉/改名（本卡就把
        # `shell-env-enum-failure-is-fail-closed` 拆成了 -pass1/-pass2）。拿整份文件
        # 当取名面 ⇒ 历史记录被当成「注释列了但不存在」，判据比它的主张宽（假红）。
        end = _gate_text.find("「数字与清单不一致」")
        if not m:
            roster_problems.append("门头注释里找不到「由 **N 条** shell 探针承重」这句声明")
        elif end < 0 or end <= m.start():
            roster_problems.append("找不到清单区的结束锚点（「数字与清单不一致」那段）——拒绝在划不准范围时下判断")
        else:
            declared = int(m.group(1))
            if declared != len(actual):
                roster_problems.append(f"注释声称 {declared} 条，AST 实测 {len(actual)} 条")
            listed = set(_re.findall(r"`(shell-[a-z0-9-]+)`", _gate_text[m.start() : end]))
            missing = sorted(actual - listed)
            extra = sorted(listed - actual)
            if missing:
                roster_problems.append(f"清单漏列: {missing}")
            if extra:
                roster_problems.append(f"清单列了但不存在: {extra}")
    except Exception as exc:  # noqa: BLE001
        roster_problems.append(f"花名册自检失败: {exc!r}")
    _emit(
        "shell-probe-roster-matches-declared-count",
        not roster_problems,
        None,
        "—（静态比对，不起子进程）",
        "门头声明的探针条数与清单，和实际产出一致",
        "门头承重声明与实际探针对不上（同一种错已犯三次）",
        "; ".join(roster_problems),
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


def probe_allowed_test_ports_cannot_admit_live() -> dict:
    """CARD-W4-3a：往 ``ALLOWED_TEST_PORTS`` 里加现网端口，预检必须**仍拒**。

    `NEO4J_TEST_URI` 的判据从黑名单改成正面白名单之后，最省事的拆门方式就变成了
    「把 7687 加进白名单」——加完之后 ``bolt://…:0``（驱动归一成 7687）就成了
    "白名单内"，判据当场变成恒真，而 X4 那条 BLOCKER 原样复活。

    所以 :func:`assert_test_uri_not_blocked` 开头有一道**无条件**的自检：
    白名单与 :data:`BLOCKED_PORTS` 不得相交。本探针在子进程里把 7687 塞进白名单，
    断言那道自检当场抛。

    三段判据，缺一不可（判据要绑定「被哪一层拒的」）：
      A. 白名单被污染 ⇒ 抛，且拒因是**相交自检**（不是恰好被别的分支拒）；
      B. 对照：白名单干净时同一个 `:0` URI 也要抛，但拒因必须是 **canonical 7687**；
      C. 对照：白名单干净 + 7692 URI ⇒ 不抛（证明整条判据不是恒抛）。
    """
    body = """
    from tests.support import live_port_guard as g
    problems = []

    # A. 白名单被塞进现网端口 ⇒ 相交自检必须当场拒（连 URI 都还没看）
    os.environ.pop("NEO4J_TEST_URI", None)
    g.ALLOWED_TEST_PORTS = frozenset({7692, 7687})
    try:
        g.assert_test_uri_not_blocked()
        problems.append("A 白名单含 7687 却放行了（判据已被拆成恒真）")
    except RuntimeError as e:
        if "相交" not in str(e):
            problems.append("A 拒了但不是因为相交自检: " + str(e)[:160])

    # B. 对照：白名单干净时，:0 必须因 canonical 7687 被拒。
    #    ⛔ 判据不能只查文案里有没有 "7687"（round-1 Codex MEDIUM）：解析失败分支与
    #    普通白名单拒绝分支都会把默认端口 7687 带进文案，于是把 helper 改成返回 0 或
    #    None 这两种**错误实现**照样能让本段通过。要绑定的是 **canonical 复算结果本身**。
    g.ALLOWED_TEST_PORTS = frozenset({7692})
    ports, why = g.canonical_target_ports("bolt://127.0.0.1:0")
    if ports != (7687,):
        problems.append(f"B canonical 复算不是 (7687,)，实得 {ports}（{why}）")
    os.environ["NEO4J_TEST_URI"] = "bolt://127.0.0.1:0"
    try:
        g.assert_test_uri_not_blocked()
        problems.append("B bolt://127.0.0.1:0 被放行（X4 的 BLOCKER 复活）")
    except RuntimeError as e:
        if "白名单" not in str(e):
            problems.append("B 拒了但不是白名单分支: " + str(e)[:160])

    # B2. routing scheme 的多地址陷阱（round-1 Codex BLOCKER）：netloc 按空白拆分，
    #     驱动取 [0]。单值解析会给 7692 而放行，实际连的是 7687。
    ports, why = g.canonical_target_ports("neo4j://127.0.0.1 :7692")
    if ports != (7687, 7692):
        problems.append(f"B2 routing 多地址复算不是 (7687, 7692)，实得 {ports}（{why}）")
    os.environ["NEO4J_TEST_URI"] = "neo4j://127.0.0.1 :7692"
    try:
        g.assert_test_uri_not_blocked()
        problems.append("B2 routing 多地址陷阱被放行（驱动会连 7687）")
    except RuntimeError as e:
        if "白名单" not in str(e):
            problems.append("B2 拒了但不是白名单分支: " + str(e)[:160])

    # C. 对照：白名单干净 + 7692 ⇒ 必须放行（否则整条判据是恒抛，A/B 无意义）
    os.environ["NEO4J_TEST_URI"] = "bolt://127.0.0.1:7692"
    try:
        g.assert_test_uri_not_blocked()
    except Exception as e:
        problems.append("C 合法的 7692 被拒 —— 判据恒抛: " + str(e)[:160])

    # C2. 对照：routing 多地址**全部** 7692 也必须放行（防收紧过头）。
    os.environ["NEO4J_TEST_URI"] = "neo4j://127.0.0.1:7692 localhost:7692"
    try:
        g.assert_test_uri_not_blocked()
    except Exception as e:
        problems.append("C2 全 7692 的 routing 多地址被误拒: " + str(e)[:160])

    verdict(not problems, "allowed-test-ports-cannot-admit-live", "; ".join(problems))
    sys.exit(1 if problems else 0)
    """
    return _run("guard-allowed-test-ports-cannot-admit-live", body, expect_rc=0)


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
# CARD-W4-4：结算原子性 / 账本与裁定一致 / install 顺序 / 注入点惰性
# ═══════════════════════════════════════════════════════════════════════════

#: 制造「hook 已过结算检查、结算已取快照、hook 才记账」这个交错。
#:
#: 唯一的注入点是 ``live_port_guard._finalize_race_seam_hook`` —— 生产里它是一个
#: **默认 no-op**、被 :func:`_audit_hook` 无条件调用、返回值被丢弃的函数（不出现在
#: 任何判据里，见那里的 docstring）。修好之后 hook 里已经没有「先读结算标志、再记账」
#: 这个间隙了（判定进了 ``record()`` 的锁内），所以要证明间隙关上了，只能让 hook 在
#: **即将记账**那一点停住 —— 进程外做不到这件事。
#:
#: ⚠️ ``atexit.unregister`` 那一行**不是拆门**，恰恰相反：生产里 ``_final_accounting``
#: 只跑一次，而本探针手工调了它一次，若不摘掉注册，解释器退出时会**再结算一遍**，
#: 那第二遍会看见迟到记录并 ``os._exit(3)`` —— 于是即便迟到判定完全失效，rc 照样是 3，
#: 判据被更晚的一层喂饱（「判据必须绑定是被哪一层拒的」）。摘掉之后，rc=3 只可能
#: 来自 hook 的迟到路径本身。
_FINALIZE_RACE_BODY = """
    from tests.support import live_port_guard as g
    srv, port = listener()
    g.BLOCKED_PORTS = frozenset(g.BLOCKED_PORTS | {port})   # 只加不减：门的不变量
    g.install()

    reached = threading.Event()
    released = threading.Event()

    def seam():
        reached.set()          # hook 已走到「即将记账」那一点
        released.wait(30)      # 等主线程把结算做完

    g._finalize_race_seam_hook = seam

    def late_connect():
        s = socket.socket()
        try:
            s.connect(("127.0.0.1", port))
        except BaseException:
            pass
        finally:
            s.close()

    t = threading.Thread(target=late_connect, name="w4-late", daemon=True)
    t.start()
    if not reached.wait(30):
        verdict(False, %r, "迟到线程没走到注入点")
        sys.exit(0)
    g._final_accounting()                      # 结算：置位 + 取快照（必须原子）
    atexit.unregister(g._final_accounting)     # 生产里只跑一次；见上面的 ⚠️
    verdict(True, %r)                          # 裁定行必须在放行之前落地
    released.set()
    t.join(30)
    srv.close()
    sys.exit(0)
    """

_CLEAN_LEDGER_BODY = """
    from tests.support import live_port_guard as g
    g.install()
    verdict(True, %r)
    sys.exit(0)
    """


def probe_finalize_race_loses_record() -> dict:
    """结算快照取走之后落地的 blocked 记录，必须让进程 rc=3（不得被整条丢掉）。

    改前（主干 03ac8bf8）同一交错的结果是 **rc=0 且账本 unaccounted=0** —— 记录既不
    进快照、又不触发迟到路径。实测证据：``_bmad-output/审查/evidence-w4-4`` 的
    ``before-1``。
    """
    name = "guard-finalize-race-loses-record"
    return _run(name, _FINALIZE_RACE_BODY % (name, name), expect_rc=3)


def probe_ledger_matches_verdict() -> dict:
    """账本文件与进程 rc 必须互相印证 —— 本探针钉的是**两个特例**，不是等价。

    * 结算之后落地一条 blocked ⇒ rc=3 且账本 ``unaccounted>0``、``blocked>0``；
    * 一次连接都没有 ⇒ rc=0 且账本 ``unaccounted==0``、``blocked==0``。

    ⚠️ 措辞更正（2026-09-08）：这两跑**不构成**「rc=3 与 ``unaccounted>0`` 等价」这个
    双向命题的证明。``_final_accounting`` 的退出判据还有第二个分支（``blocked>0`` 且原
    ``reported_status`` 为 0）能在 ``unaccounted==0`` 时给出 rc=3 —— 那个形态不在
    这两跑的覆盖面里。**判据一字未改**，改的只是这段对它证明了什么的描述。

    两跑合起来仍然承重：只测一个方向会被「恒判 unaccounted=1」这类实现骗过。
    改前第一种形态可以出现
    **账本 unaccounted=1 而 rc=0**（裁定读 ``_final_accounting`` 的快照、落盘读
    ``write_ledger`` 自己再取的那一份）—— 实测证据见 ``before-2``。
    """
    name = "guard-ledger-matches-verdict"
    tmp = Path(tempfile.mkdtemp(prefix="w4-verdict-"))
    late_path = tmp / "late.json"
    clean_path = tmp / "clean.json"
    late = _run(name, _FINALIZE_RACE_BODY % (name, name), expect_rc=3, env_extra={"W4_GUARD_LEDGER": str(late_path)})
    clean = _run(name, _CLEAN_LEDGER_BODY % name, expect_rc=0, env_extra={"W4_GUARD_LEDGER": str(clean_path)})
    problems: list[str] = []
    if not late["ok"]:
        problems.append(f"迟到形态子进程未达标（{late['reason']}）")
    if not clean["ok"]:
        problems.append(f"干净形态子进程未达标（{clean['reason']}）")
    for label, path, rc, want_positive in (
        ("late", late_path, late["rc"], True),
        ("clean", clean_path, clean["rc"], False),
    ):
        if not path.exists():
            problems.append(f"{label}: 账本未落盘")
            continue
        led = json.loads(path.read_text(encoding="utf-8"))
        if want_positive:
            if not (led["unaccounted"] > 0 and led["blocked"] > 0 and rc == 3):
                problems.append(
                    f"{label}: rc={rc} 而账本 blocked={led['blocked']} unaccounted={led['unaccounted']}"
                    " —— 账本与裁定不一致"
                )
        else:
            if not (led["unaccounted"] == 0 and led["blocked"] == 0 and rc == 0):
                problems.append(
                    f"{label}: rc={rc} 而账本 blocked={led['blocked']} unaccounted={led['unaccounted']}"
                    " —— 无连接却不是零账/零 rc"
                )
    shutil.rmtree(tmp, ignore_errors=True)
    return {
        "name": name,
        "ok": not problems,
        "rc": late["rc"],
        "expect_rc": 3,
        "verdict": [late["verdict"], clean["verdict"]],
        "reason": "; ".join(problems),
        "stderr_tail": (late["stderr_tail"] or clean["stderr_tail"])[-400:],
    }


def probe_late_ledger_survives_stale_final_write() -> dict:
    """迟到线程发布的账本，**不得**被结算线程手上的陈旧快照盖回去（round-1 MEDIUM-4）。

    两条写盘路径原来各自「先取快照、后 ``open(path,"w")`` 整写」，没有发布顺序控制。
    本探针把那个交错做成**确定性**的：

    1. 迟到线程在注入点停住（``_finalize_race_seam_hook``）；
    2. 主线程调 ``_final_accounting()``，包过的 ``finalize_and_snapshot`` 取到**零账**
       快照后放行迟到线程，并等它把账本写出去；
    3. 迟到线程 ``record()`` 判 LATE → 包过的 ``_rewrite_ledger_after_late_record``
       写出 ``unaccounted=1`` 后**停住**（这是关键：不停住的话它随即 ``os._exit(3)``，
       主线程那次陈旧回写落不落地就成了竞态，探针结论会飘）；
    4. 主线程拿着第 2 步那份旧快照继续写盘 —— 修好后这一次必须是 no-op；
    5. 主线程落裁定行，放行迟到线程 → ``os._exit(3)``。

    判据是**文件末态** ``unaccounted==1`` 且 rc=3。修前第 4 步会把文件盖回零账，
    于是 rc=3 而文件说「什么都没发生」。

    探针体里不出现 ``_publish_ledger`` 字样 —— 同一份探针在修前修后都跑得动，红绿差异
    只来自生产代码。``atexit.unregister`` 同 ``_FINALIZE_RACE_BODY``：不摘掉的话解释器
    退出时会再结算一遍并 ``os._exit(3)``，rc=3 就被更晚的一层喂饱了。
    """
    name = "guard-late-ledger-survives-stale-final-write"
    tmp = Path(tempfile.mkdtemp(prefix="w4-stale-"))
    ledger = tmp / "ledger.json"
    body = """
    from tests.support import live_port_guard as g
    srv, port = listener()
    g.BLOCKED_PORTS = frozenset(g.BLOCKED_PORTS | {port})   # 只加不减：门的不变量
    g.install()
    g.STATE.reported_status = 0

    reached = threading.Event()
    released = threading.Event()
    late_published = threading.Event()
    final_wrote = threading.Event()
    armed = [True]

    def seam():
        if not armed[0]:
            return
        armed[0] = False
        reached.set()
        released.wait(30)
    g._finalize_race_seam_hook = seam

    real_rewrite = g._rewrite_ledger_after_late_record
    def rewrite_then_park():
        real_rewrite()             # 迟到线程发布含迟到记录的账本
        late_published.set()
        final_wrote.wait(30)       # 停住，让主线程的陈旧回写先跑完
    g._rewrite_ledger_after_late_record = rewrite_then_park

    def late_connect():
        s = socket.socket()
        try:
            s.connect(("127.0.0.1", port))
        except BaseException:
            pass
        finally:
            s.close()

    t = threading.Thread(target=late_connect, name="w4-late", daemon=True)
    t.start()
    if not reached.wait(30):
        verdict(False, %r, "迟到线程没走到注入点")
        sys.exit(0)

    real_finalize = g.STATE.finalize_and_snapshot
    def finalize_then_let_late_run():
        snap = real_finalize()     # 结算取到零账快照，尚未写盘
        released.set()
        if not late_published.wait(30):
            raise RuntimeError("迟到线程没把账本写出去")
        return snap                # 结算线程带着**旧**快照继续去写盘
    g.STATE.finalize_and_snapshot = finalize_then_let_late_run

    atexit.unregister(g._final_accounting)   # rc=3 只能来自迟到路径本身
    g._final_accounting()
    verdict(True, %r)                        # 裁定行必须在放行 os._exit 之前落地
    final_wrote.set()
    t.join(30)
    srv.close()
    sys.exit(0)
    """
    res = _run(name, body % (name, name), expect_rc=3, env_extra={"W4_GUARD_LEDGER": str(ledger)})
    if res["ok"]:
        if not ledger.exists():
            res["ok"] = False
            res["reason"] = "账本未落盘"
        else:
            led = json.loads(ledger.read_text(encoding="utf-8"))
            if led.get("unaccounted") != 1 or led.get("blocked") != 1:
                res["ok"] = False
                res["reason"] = (
                    f"账本末态 blocked={led.get('blocked')} unaccounted={led.get('unaccounted')}"
                    " —— 结算线程用陈旧快照把迟到记录盖掉了"
                )
    shutil.rmtree(tmp, ignore_errors=True)
    return res


def probe_install_order_precheck_is_guarded() -> dict:
    """``install()`` 的目标预检必须跑在**门内**（T-14）。

    ``assert_neo4j_target_blocked()`` 会走 ``canonical_target_ports``，后者在函数体内
    ``from neo4j import Address``。旧顺序把这段放在 ``_install_audit_hook()`` **之前**，
    于是预检期（含那次 import）的任何连接既不被拦、也不进账 —— 实测证据
    ``before-3``：预检内一次到受拦端口的连接结果是 ``connected``、``STATE.blocked=0``。

    这里在 ``canonical_target_ports`` 内部发起一次到受拦端口的连接，要求它**被拦下
    且被记账**。把 (d) 的顺序改回去，本探针当场转红。
    """
    name = "guard-install-order-precheck-is-guarded"
    body = """
    from tests.support import live_port_guard as g
    srv, port = listener()
    os.environ["NEO4J_URI"] = "bolt://127.0.0.1:" + str(port)
    g.BLOCKED_PORTS = frozenset(g.BLOCKED_PORTS | {port})   # 只加不减：门的不变量
    seen = []
    _orig = g.canonical_target_ports

    def wrapped(uri):
        # 模拟「预检期间（含它的延迟 import neo4j）发生了一次到受拦端口的连接」
        s = socket.socket()
        try:
            s.connect(("127.0.0.1", port))
            seen.append("connected")
        except RuntimeError:
            seen.append("blocked")
        except BaseException as exc:
            seen.append("other:" + type(exc).__name__)
        finally:
            s.close()
        return _orig(uri)

    g.canonical_target_ports = wrapped
    g.install()
    ok = seen == ["blocked"] and g.STATE.blocked == 1
    verdict(ok, %r, "" if ok else ("预检内连接=" + repr(seen) + " STATE.blocked=" + str(g.STATE.blocked)))
    srv.close()
    sys.exit(0)
    """
    return _run(
        name,
        body % name,
        expect_rc=3,
        env_extra={"W4_GUARD_REQUIRE_BLOCKED_TARGET": "1"},
    )


def probe_partial_install_settles_late_connection() -> dict:
    """**部分安装态**也必须有人结账（Codex round-1 HIGH-2）。

    ``W4_GUARD_REQUIRE_BLOCKED_TARGET=1`` 而 ``NEO4J_URI`` 未设置 ⇒ 预检抛
    ``RuntimeError``。此刻 ``_install_audit_hook()`` 已经跑过且**摘不掉**：hook 在位、
    照常拦照常记账，而 ``STATE.installed`` 还是 ``False``。旧顺序把
    ``register_final_accounting()`` 排在预检之后 —— 于是这段「门半装」的时间里被拦下的
    连接**无人结账**，进程 ``exit 0``（Codex 实测 ``audit_installed=True /
    final_registered=False / unaccounted=1 / rc=0``）。

    本探针让调用方**吞掉**预检异常（真实调用方完全可能这么写），再手发一条到受拦端口的
    审计事件（**不建立任何真实连接、不碰 7691 的真库**），要求进程以 3 收场。
    判据同时钉住 ``STATE.installed is False``，把「部分安装态」这个前提写死 —— 否则
    「其实装门成功了」的形态也能给出 rc=3，判据就不绑定它声称的那一层了。
    """
    name = "guard-partial-install-settles-late-connection"
    body = """
    from tests.support import live_port_guard as g
    try:
        g.install()
        verdict(False, %r, "预检没抛 —— 前提不成立")
        sys.exit(0)
    except RuntimeError as e:
        if "未设置" not in str(e):
            verdict(False, %r, "抛了但原因不对: " + str(e)[:120])
            sys.exit(0)
    # 调用方吞掉预检异常 —— audit hook 已不可撤销地生效，门处于「半装」状态
    try:
        sys.audit("socket.connect", None, ("127.0.0.1", 7691))
        verdict(False, %r, "受拦端口的审计事件没被拦下 —— hook 不在位，前提不成立")
        sys.exit(0)
    except RuntimeError as e:
        if g.BLOCK_REASON not in str(e):
            verdict(False, %r, "抛了但不是本门的原因: " + repr(e)[:120])
            sys.exit(0)
    ok = g.STATE.blocked == 1 and g.STATE.installed is False
    verdict(ok, %r, "" if ok else ("blocked=" + str(g.STATE.blocked) + " installed=" + str(g.STATE.installed)))
    sys.exit(0)
    """
    return _run(
        name,
        body % (name, name, name, name, name),
        expect_rc=3,
        env_extra={"W4_GUARD_REQUIRE_BLOCKED_TARGET": "1"},
    )


def probe_late_exit_survives_broken_stderr() -> dict:
    """迟到路径的强制退出**不得**被「打印失败」挡住（Codex round-1 HIGH-3）。

    旧结构里 ``print(..., file=sys.stderr)`` 在异常保护之外，只有 ``flush()`` 被 try
    裹着。stderr 若已关闭，``ValueError`` 会越过 ``os._exit(3)`` —— 于是「判迟到就
    必然就地退出 3」这句在那种状态下不成立（Codex 独立实测：``finalizing=True,
    blocked=1, unaccounted=1`` 而进程退出 **0**，且未替换注入点）。

    本探针把 stderr 换成一个写就抛的对象，再走一次真正的迟到路径（连接发生在
    **比本门更早注册**的 atexit 回调里 ⇒ LIFO 下排在最终结算之后）。
    """
    name = "guard-late-exit-survives-broken-stderr"
    body = """
    srv, port = listener()

    class Boom:
        def write(self, *a, **k):
            raise ValueError("I/O operation on closed file")
        def flush(self, *a, **k):
            raise ValueError("I/O operation on closed file")

    def very_late():
        sys.stderr = Boom()          # 迟到连接发生时 stderr 已经坏掉
        s = socket.socket()
        try:
            s.connect(("127.0.0.1", port))
        except BaseException:
            pass                      # 拦下来了，但没人会为它结账
        finally:
            s.close()

    atexit.register(very_late)        # 先注册 ⇒ 最后执行（在最终结算之后）
    from tests.support import live_port_guard as g
    g.BLOCKED_PORTS = frozenset(g.BLOCKED_PORTS | {port})   # 只加不减
    g.install()
    g.STATE.reported_status = 0       # 模拟 pytest 已返回 0
    verdict(True, %r)                 # 裁定行必须在 stderr 被弄坏之前落地
    sys.exit(0)
    """
    return _run(name, body % name, expect_rc=3)


def probe_finalize_seam_inert_when_unset() -> dict:
    """注入点未被替换时必须**完全惰性**；被替换时必须当场算漂移。

    两个方向都钉：默认那个 no-op 不返回任何东西、不动账本、``assert_guard_live``
    照常通过；一旦被换掉，``assert_guard_live`` 必须抛 :class:`GuardDrift` 并点名
    注入点 —— 否则这个 seam 就成了一条新的旁路。
    """
    name = "guard-finalize-seam-inert-when-unset"
    body = """
    import json as _json
    from tests.support import live_port_guard as g
    g.install()
    problems = []
    if g._finalize_race_seam_hook is not g._finalize_race_seam:
        problems.append("默认注入点不是那个 no-op")
    before = _json.dumps(g.STATE.ledger(), sort_keys=True, ensure_ascii=False)
    for _ in range(10):
        if g._finalize_race_seam_hook() is not None:
            problems.append("默认注入点有返回值")
            break
    after = _json.dumps(g.STATE.ledger(), sort_keys=True, ensure_ascii=False)
    if before != after:
        problems.append("默认注入点动了账本")
    g.assert_guard_live("seam 未替换")
    g._finalize_race_seam_hook = lambda: None
    try:
        g.assert_guard_live("seam 已替换")
        problems.append("注入点被替换却没被 assert_guard_live 抓到")
    except g.GuardDrift as exc:
        if "注入点" not in str(exc):
            problems.append("漂移拒因不是注入点: " + str(exc)[:80])
    finally:
        g._finalize_race_seam_hook = g._finalize_race_seam
    verdict(not problems, %r, "; ".join(problems))
    sys.exit(0)
    """
    return _run(name, body % name, expect_rc=0)


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
        # CARD-W4-3a：NEO4J_TEST_URI 的正面白名单不能被「往里加现网端口」拆掉。
        probe_allowed_test_ports_cannot_admit_live(),
        # M15 族：runtime 文件的 **glob 分支**（CARD-W4-3b）。前三条是
        # 「正探针 + 两条拆了要瞎的对照」，后两条钉住 M14 收窄的两个方向。
        probe_runtime_glob_absent_to_present(),
        probe_runtime_glob_cached_expansion_is_blind(),
        probe_runtime_glob_pattern_neutralized_is_blind(),
        probe_runtime_glob_sidecar_excluded(),
        probe_runtime_glob_expansion_sorted(),
        probe_runtime_legacy_journal_watched(),
        # CARD-W4-4：结算原子性（门自己的假绿）+ 账本/裁定一致 + install 顺序 + 注入点惰性。
        probe_finalize_race_loses_record(),
        probe_ledger_matches_verdict(),
        probe_install_order_precheck_is_guarded(),
        probe_finalize_seam_inert_when_unset(),
        # Codex round-1 HIGH-3 的处置门：打印失败不得挡住迟到路径的强制退出。
        probe_late_exit_survives_broken_stderr(),
        # Codex round-1 HIGH-2 的处置门：预检抛出后的部分安装态也必须有人结账。
        probe_partial_install_settles_late_connection(),
        # Codex round-1 MEDIUM-4 的处置门：陈旧快照不得盖掉迟到线程发布的账本。
        probe_late_ledger_survives_stale_final_write(),
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
