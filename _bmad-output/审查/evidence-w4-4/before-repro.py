#!/usr/bin/env python
"""CARD-W4-4-settle-atomic 的 **before 证据**：改代码之前，逐条复现今天的缺陷。

[BATCH-2026-09-05-第十二批 / CARD-W4-4-settle-atomic]

⚠️ 本脚本**只在主干 03ac8bf8 的未改代码上有意义**。它不动生产文件，全部注入都
发生在子进程里，且只做「延迟 / 观测」——不改任何判据、不放宽任何拦截。

四条：

* ``before-1`` W-1 丢记录：迟到线程在 ``_audit_hook`` 的 ``if _FINALIZING`` 处读到
  False，主线程走完 ``_FINALIZING = True`` + ``STATE.ledger()``（两步无锁），迟到
  线程才 ``record()``。放行点是一个**比 guard 更早注册的 atexit 回调**（LIFO ⇒ 排在
  ``_final_accounting`` 之后）——完全是生产真实路径，零拆门。
  期望：rc=0，账本 JSON ``unaccounted=0``（记录整个丢掉）。
* ``before-2`` W-2 账本与裁定打脸：放行点挪到 ``write_ledger`` 内部，也就是
  ``_final_accounting:1026`` 的快照 A 与 ``write_ledger:1007`` 的快照 B **之间**。
  期望：rc=0，而账本 JSON ``unaccounted=1`` —— 父进程复核与子进程 rc 互相打脸。
* ``before-3`` T-14 install 顺序：``install()`` 在装 audit hook **之前**先跑
  ``assert_neo4j_target_blocked()``，其 ``canonical_target_ports`` 的延迟 import 与
  该段内的任何连接都在门外。期望：预检内的连接 **connected**、``STATE.blocked=0``。
* ``before-4`` T-10 advisory 窗口：root conftest 的 session fixture（预检所在）跑在
  首个用例的 ``pytest_runtest_protocol`` 之内，也就是 ``begin_item(exempt=True)``
  之后。期望：预检执行时 ``_EXEMPT_CV`` 为 **True**、``_OWNER_CV`` 为该用例 nodeid。

用法：``python before-repro.py``（cwd 任意；BACKEND_DIR 由本文件位置推导）。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[3] / "backend"
PY = sys.executable

_PREAMBLE = textwrap.dedent(
    """
    import atexit, json, os, socket, sys, threading
    sys.path.insert(0, %r)
    def listener():
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.bind(("127.0.0.1", 0)); srv.listen(5)
        return srv, srv.getsockname()[1]
    """
) % str(BACKEND_DIR)


def _run(name: str, body: str, env_extra: dict | None = None) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = str(BACKEND_DIR) + os.pathsep + env.get("PYTHONPATH", "")
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
    print(f"───── {name} ─────")
    print(f"  rc={proc.returncode}")
    for line in proc.stdout.splitlines():
        print(f"  out| {line}")
    for line in proc.stderr.splitlines()[-12:]:
        print(f"  err| {line}")
    return proc


# ═══════════════════════════════════════════════════════════════════════════
# before-1 / before-2：结算竞态的两个观察面
# ═══════════════════════════════════════════════════════════════════════════

#: ``%s`` = 放行点的装法（before-1 走 atexit 回调，before-2 走 write_ledger 包装）。
_RACE_BODY = """
    reached = threading.Event()
    released = threading.Event()
    holder = {}

    %s

    from tests.support import live_port_guard as g
    srv, port = listener()
    g.BLOCKED_PORTS = frozenset(g.BLOCKED_PORTS | {port})   # 只加不减：门的不变量
    g.install()

    # 观测注入：让迟到线程停在「已过 hook 的 `if _FINALIZING`、尚未 record()」那一点。
    # 只延迟、不改判据 —— 原 record 被原样调用。
    _orig_record = g.STATE.record
    def paused_record(address):
        reached.set()
        released.wait(30)
        return _orig_record(address)
    g.STATE.record = paused_record

    def late_connect():
        s = socket.socket()
        try:
            s.connect(("127.0.0.1", port))
        except BaseException:
            pass
        finally:
            s.close()

    t = threading.Thread(target=late_connect, name="w4-late", daemon=True)
    holder["t"] = t
    t.start()
    if not reached.wait(30):
        print("SETUP-FAIL: 迟到线程没走到 record 之前", flush=True)
        sys.exit(9)
    print("STAGE: 迟到线程已停在 record() 之前（它读到的 _FINALIZING 是 False）", flush=True)
    sys.exit(0)
    """

_RELEASE_VIA_ATEXIT = """
    def release_after_final():
        # atexit 是 LIFO：本回调注册在 guard import **之前** ⇒ 排在 _final_accounting
        # **之后**执行。放行点因此落在「快照 A 与快照 B 都已取完」之后。
        released.set()
        holder["t"].join(10)
        # ⛔ join 超时不等于落账（Codex round-1 LOW-9）：必须实测线程已结束**且**
        #    账面真的多了一条，否则这条 before 证据不能证明它复现了那个阶段。
        from tests.support import live_port_guard as _g
        alive = holder["t"].is_alive()
        total = _g.STATE.total
        if alive or total < 1:
            print("STAGE-INVALID: 迟到线程未完成或未落账"
                  " (alive=" + repr(alive) + ", total=" + str(total) + ") —— 本次复现无效", flush=True)
        else:
            print("STAGE: 迟到线程已在最终结算之后落账 (total=" + str(total) + ")", flush=True)
    atexit.register(release_after_final)
    """


def _race_case(name: str, release: str) -> None:
    tmp = Path(tempfile.mkdtemp(prefix="w4-before-"))
    ledger = tmp / "ledger.json"
    proc = _run(name, _RACE_BODY % release, env_extra={"W4_GUARD_LEDGER": str(ledger)})
    if ledger.exists():
        led = json.loads(ledger.read_text(encoding="utf-8"))
        print(
            f"  ledger| total={led['total']} blocked={led['blocked']} "
            f"advisory={led['advisory']} unaccounted={led['unaccounted']}"
        )
        print(f"  ==> 判读：rc={proc.returncode} 而账本 unaccounted={led['unaccounted']}")
    else:
        print("  ledger| （未落盘）")


def before_1() -> None:
    _race_case("before-1 结算竞态丢记录（rc 期望 0 / 账本 unaccounted 期望 0）", _RELEASE_VIA_ATEXIT)


def before_2() -> None:
    """放行点装在 ``write_ledger`` 上，因此必须在 ``install()`` 之后再打补丁。

    before-1 用的 atexit 回调放行点排在 ``_final_accounting`` **之后**（LIFO），太晚，
    落不进「快照 A 与快照 B 之间」这个更窄的窗口 —— 所以这一条改在主体里打补丁。
    """
    body = _RACE_BODY % ""
    body = body.replace(
        "    t = threading.Thread(",
        (
            "    _orig_write = g.write_ledger\n"
            "    def gated_write(*a, **kw):\n"
            "        # 此刻 _final_accounting 的快照 A 已取完，write_ledger 的快照 B 还没取。\n"
            "        released.set()\n"
            "        holder['t'].join(10)\n"
            "        # join 超时不等于落账（Codex round-1 LOW-9）：实测线程状态与账面。\n"
            "        if holder['t'].is_alive() or g.STATE.total < 1:\n"
            "            print('STAGE-INVALID: 迟到线程未完成或未落账 —— 本次复现无效', flush=True)\n"
            "        else:\n"
            "            print('STAGE: 迟到线程已在快照 A 与快照 B 之间落账'\n"
            "                  ' (total=' + str(g.STATE.total) + ')', flush=True)\n"
            "        return _orig_write(*a, **kw)\n"
            "    g.write_ledger = gated_write\n"
            "    t = threading.Thread("
        ),
    )
    tmp = Path(tempfile.mkdtemp(prefix="w4-before-"))
    ledger = tmp / "ledger.json"
    proc = _run(
        "before-2 账本与裁定打脸（rc 期望 0 / 账本 unaccounted 期望 1）",
        body,
        env_extra={"W4_GUARD_LEDGER": str(ledger)},
    )
    if ledger.exists():
        led = json.loads(ledger.read_text(encoding="utf-8"))
        print(
            f"  ledger| total={led['total']} blocked={led['blocked']} "
            f"advisory={led['advisory']} unaccounted={led['unaccounted']}"
        )
        print(f"  ==> 判读：rc={proc.returncode} 而账本 unaccounted={led['unaccounted']}")
    else:
        print("  ledger| （未落盘）")


# ═══════════════════════════════════════════════════════════════════════════
# before-3：install() 顺序 —— 预检跑在门外
# ═══════════════════════════════════════════════════════════════════════════


def before_3() -> None:
    body = """
    from tests.support import live_port_guard as g
    srv, port = listener()
    os.environ["NEO4J_URI"] = "bolt://127.0.0.1:" + str(port)
    g.BLOCKED_PORTS = frozenset(g.BLOCKED_PORTS | {port})   # 只加不减
    seen = []
    _orig = g.canonical_target_ports
    def wrapped(uri):
        # 模拟「预检期间（含它的延迟 import neo4j）发生了一次到受拦端口的连接」
        s = socket.socket()
        try:
            s.connect(("127.0.0.1", port)); seen.append("connected")
        except RuntimeError:
            seen.append("blocked")
        except BaseException as exc:
            seen.append("other:" + type(exc).__name__)
        finally:
            s.close()
        return _orig(uri)
    g.canonical_target_ports = wrapped
    g.install()
    print("RESULT: 预检内连接 = " + repr(seen)
          + ", STATE.blocked=" + str(g.STATE.blocked)
          + ", STATE.total=" + str(g.STATE.total), flush=True)
    srv.close()
    sys.exit(0)
    """
    _run(
        "before-3 install 顺序：预检在门外（期望 connected / blocked=0）",
        body,
        env_extra={"W4_GUARD_REQUIRE_BLOCKED_TARGET": "1"},
    )


# ═══════════════════════════════════════════════════════════════════════════
# before-4：T-10 —— session fixture 的预检落在 begin_item(exempt=True) 之内
# ═══════════════════════════════════════════════════════════════════════════

_MINI_CONFTEST = '''
"""迷你会话：与 root conftest 同构的接线（protocol hook + session autouse fixture）。

只为回答一个机制问题：session fixture 的 setup 是不是跑在首个用例的
``pytest_runtest_protocol``（也就是 ``begin_item(exempt=...)``）**之内**。
"""
import sys
from pathlib import Path

sys.path.insert(0, {backend!r})

import pytest

from tests.support import live_port_guard


def pytest_configure(config):
    print(
        "PROBE configure: exempt=%r owner=%r"
        % (live_port_guard._EXEMPT_CV.get(), live_port_guard._OWNER_CV.get()),
        flush=True,
    )


@pytest.fixture(scope="session", autouse=True)
def _session_precheck():
    # root conftest.py:105-106 就在这个位置调 assert_guard_live + assert_test_uri_not_blocked
    print(
        "PROBE session-fixture: exempt=%r owner=%r"
        % (live_port_guard._EXEMPT_CV.get(), live_port_guard._OWNER_CV.get()),
        flush=True,
    )
    yield


@pytest.hookimpl(wrapper=True)
def pytest_runtest_protocol(item, nextitem):
    # root conftest.py:131-133 同构
    live_port_guard.begin_item(item.nodeid, True)   # 首个用例是 integration ⇒ exempt=True
    try:
        return (yield)
    finally:
        live_port_guard.end_item()
'''

_MINI_TEST = """
import pytest


@pytest.mark.integration
def test_first_is_integration():
    assert True
"""


def before_4() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="w4-before-t10-"))
    (tmp / "conftest.py").write_text(_MINI_CONFTEST.format(backend=str(BACKEND_DIR)), encoding="utf-8")
    (tmp / "test_mini.py").write_text(_MINI_TEST, encoding="utf-8")
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = str(BACKEND_DIR) + os.pathsep + env.get("PYTHONPATH", "")
    for key in [k for k in env if k.upper().startswith("NEO4J")]:
        env.pop(key, None)
    proc = subprocess.run(
        [PY, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-s", "--no-header", "-c", "/dev/null", str(tmp)],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
    )
    print("───── before-4 T-10 advisory 窗口（期望 session-fixture 处 exempt=True）─────")
    print(f"  rc={proc.returncode}")
    for line in proc.stdout.splitlines():
        if line.startswith("PROBE ") or "passed" in line or "error" in line.lower():
            print(f"  out| {line}")
    for line in proc.stderr.splitlines()[-8:]:
        print(f"  err| {line}")


def main() -> int:
    print("=== CARD-W4-4-settle-atomic BEFORE 证据（主干未改代码）===")
    print(f"    backend: {BACKEND_DIR}")
    print(f"    interpreter: {PY}")
    before_1()
    before_2()
    before_3()
    before_4()
    print("=== BEFORE 证据结束 ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
