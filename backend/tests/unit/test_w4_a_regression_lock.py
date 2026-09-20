"""CARD-W4-A-REGRESSION-LOCK（并入 CARD-W4-GUARD-TAIL-R2）[BATCH-2026-09-18-第十五批]

把 T9-A 的三跑 A/B/C 对照从「只打印、rc 恒 0」的一次性脚本
（``_bmad-output/审查/evidence-w4final/three-run-abc.py`` —— ``grep -c -e 'sys.exit' -e 'assert '``
实测 **0**，脚本自身永远退 0，台账 ⑩ / Codex M1）变成**常驻**回归锁。

⛔ 它锁的是哪一行：``live_port_guard._final_accounting`` 里「账本落盘失败」那条报告路径上的
``print`` 必须被 ``except BaseException`` 护住。不护住时 A 格 —— 账本路径指向**目录**（落盘
当场抛）且 ``sys.stderr`` 已被关闭（报告那一句 ``print`` 再抛 ``ValueError``）—— 的异常会
**越过** ``os._exit(FINAL_EXIT_CODE)``：进程以 rc=0 收场，而账面上明明有一次被拦下的连接。

B / C 两格各只坏一侧，作用是证明三格**可区分**：锁绑在「两侧同时坏」这个交点上，不是恒红。
负控（把那层嵌套 try 删掉，``evidence-w4final/nc-remove-protection.py``）下 A 必红、B/C 必绿。

DD-03（禁 mock）：三格全部走**真子进程** + 真 ``atexit`` + 真文件系统。受拦事件由
``sys.audit("socket.connect", None, ("127.0.0.1", 7691))`` **合成** —— 不建立任何真实连接，
不连 7691 / 7687 / 7692。账本路径一律由 pytest 的 ``tmp_path_factory`` 派生。

⛔ **父进程零账**：本文件不在父进程里触发任何受拦事件。父进程一旦触发，这次拦截会记到本用例
名下（``owner=<nodeid>``），W4 哨兵当场变红 —— 那是门在正常工作，属自伤。

⚠️ 三格是**前提断言**不是 skip：``blocked == 1 and unaccounted == 1`` 不成立时整套对照失去
意义（子进程根本没走到受拦路径），所以判 fail 而不是「测不了就放过」。
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

#: 本树的 ``backend/``：本文件 = ``backend/tests/unit/test_w4_a_regression_lock.py``。
BACKEND = Path(__file__).resolve().parents[2]
GUARD = BACKEND / "tests" / "support" / "live_port_guard.py"

#: ⛔ 逐字搬自 ``evidence-w4final/three-run-abc.py`` 的 CHILD（T9-A 冻结裁判），
#: 只把「从哪棵树 import」改成由 argv 传入**本树** ``backend/``。
CHILD = r"""
import atexit, io, json, os, sys
backend, ledger_path, break_stderr = sys.argv[1], sys.argv[2], sys.argv[3] == "1"
os.environ["W4_GUARD_LEDGER"] = ledger_path
os.environ.pop("W4_GUARD_REQUIRE_BLOCKED_TARGET", None)   # 默认不连库
sys.path.insert(0, backend)
from tests.support import live_port_guard as guard
guard.install()                           # 内部先注册 _final_accounting
if break_stderr:                          # atexit LIFO：后注册→先跑→结账时 stderr 已坏
    def _break():
        b = io.StringIO(); b.close(); sys.stderr = b
    atexit.register(_break)
try:                                      # 合成一条到受拦端口的审计事件（不建真实连接）
    sys.audit("socket.connect", None, ("127.0.0.1", 7691))
except BaseException:
    pass
snap = guard.STATE.late_snapshot()
print("CHILD-JSON: " + json.dumps({"blocked": snap["blocked"], "unaccounted": snap["unaccounted"]}), flush=True)
# 正常返回 —— rc 完全交给 atexit 的 _final_accounting 决定
"""

#: ``(格名, 账本指向目录, stderr 坏掉)``。缺陷恰落 A 格。
CELLS = (
    ("A", True, True),
    ("B", True, False),
    ("C", False, True),
)

#: ``live_port_guard.FINAL_EXIT_CODE`` —— 逐字写在这里而不是 import 守卫本体：
#: 本文件要证的正是「进程真的以 3 收场」，拿被测模块的常量当期望值等于让被测方自己出题。
EXPECTED_EXIT_CODE = 3


def _run_cell(workdir: Path, ledger_is_dir: bool, break_stderr: bool) -> dict:
    """跑一格：真子进程、真 atexit、真文件系统。"""
    child = workdir / "child.py"
    child.write_text(CHILD, encoding="utf-8")
    if ledger_is_dir:
        ledger = workdir / "ledger_as_dir"
        ledger.mkdir()
    else:
        ledger = workdir / "ledger.json"
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    proc = subprocess.run(
        [sys.executable, str(child), str(BACKEND), str(ledger), "1" if break_stderr else "0"],
        capture_output=True,
        text=True,
        env=env,
        timeout=120,
        check=False,
    )
    payload: dict = {}
    for line in proc.stdout.splitlines():
        if line.startswith("CHILD-JSON: "):
            payload = json.loads(line[len("CHILD-JSON: ") :])
    return {"rc": proc.returncode, "acct": payload, "stdout": proc.stdout, "stderr": proc.stderr}


@pytest.fixture(scope="module")
def three_run(tmp_path_factory) -> dict:
    """三格各跑一次，并记下**跑前 / 跑后**的守卫 sha256。

    ⛔ sha 前后比对是「三格读的是同一份源码」的自证：三格若被某一格自己改过的守卫
    喂过，格与格之间就不可比，而那种不可比在 rc 上看不出来。
    """
    before = hashlib.sha256(GUARD.read_bytes()).hexdigest()
    results = {}
    for label, ledger_is_dir, break_stderr in CELLS:
        workdir = tmp_path_factory.mktemp(f"w4lock-{label}-")
        results[label] = _run_cell(workdir, ledger_is_dir, break_stderr)
    after = hashlib.sha256(GUARD.read_bytes()).hexdigest()
    return {"results": results, "sha_before": before, "sha_after": after}


@pytest.mark.parametrize(
    ("label", "what_is_broken"),
    [
        ("A", "账本落盘失败 + stderr 已关闭（缺陷恰落此格）"),
        ("B", "只有账本落盘失败（stderr 正常）"),
        ("C", "只有 stderr 已关闭（账本正常）"),
    ],
)
def test_forced_exit_survives_a_broken_report_path(three_run, label, what_is_broken):
    """三格都必须以 ``rc=3`` 收场 —— 报告路径坏掉不得改变强制退出。"""
    cell = three_run["results"][label]
    acct = cell["acct"]
    # 前提：子进程真的走到了受拦路径。不成立 ⇒ 整套对照没有意义，判 fail 不是 skip。
    assert acct.get("blocked") == 1, (
        f"{label} 格（{what_is_broken}）：子进程账面 blocked={acct.get('blocked')}，"
        f"受拦事件没被记上 —— 三格对照的前提不成立。CHILD stdout={cell['stdout']!r}"
    )
    assert acct.get("unaccounted") == 1, (
        f"{label} 格：子进程账面 unaccounted={acct.get('unaccounted')} —— "
        f"这条拦截被谁结掉了？CHILD stdout={cell['stdout']!r}"
    )
    assert cell["rc"] == EXPECTED_EXIT_CODE, (
        f"{label} 格（{what_is_broken}）：进程 rc={cell['rc']}，期望 {EXPECTED_EXIT_CODE}。"
        "报告路径上的异常越过了 os._exit —— 账面有一次被拦下的连接，进程却正常收场。"
        f"CHILD stdout={cell['stdout']!r} stderr_tail={cell['stderr'][-400:]!r}"
    )


def test_three_cells_share_one_guard_source(three_run):
    """三格跑前跑后守卫源码逐字节相同（格与格之间可比的前提）。"""
    assert three_run["sha_before"] == three_run["sha_after"], (
        "三格跑的过程中 live_port_guard.py 变了 —— 三格读的不是同一份源码，rc 不可比："
        f"before={three_run['sha_before']} after={three_run['sha_after']}"
    )


def test_the_three_cells_are_distinguishable_by_construction(three_run):
    """⛔ 反向锚：三格**坏的是不同的东西**，不是同一个输入跑三遍。

    三格全绿只在「A 与 B/C 坏的面确实不同」时才有信息量。这里不断言 rc 不同
    （修好之后三格 rc 本来就都是 3），只钉住**构造**上的差异：A 两侧都坏、
    B 只坏落盘、C 只坏 stderr。构造塌成一样时这条先红，省得后人对着三格
    等价的「对照」下结论。
    """
    assert {(label, d, s) for label, d, s in CELLS} == {
        ("A", True, True),
        ("B", True, False),
        ("C", False, True),
    }, "三格构造已漂 —— A/B/C 不再是『两侧坏 / 只坏落盘 / 只坏 stderr』三种输入"
    assert len({(d, s) for _, d, s in CELLS}) == 3, "三格里有两格坏的是同一个面"
