"""CARD-W4-FINAL-ACCOUNTING 判据 2：三跑 A/B/C 对照（子进程合成拦截事件，不建真实连接）。

A = ledger 指向目录（落盘失败）+ stderr 坏  ⇒ 缺陷恰落此格
B = 只落盘失败（ledger=目录 + stderr 正常）
C = 只 stderr 坏（ledger 正常 + stderr 坏）
改前期望 A rc=0 / B rc=3 / C rc=3（A != B,C）；改后期望 A/B/C 全 rc=3。
三跑进程内账本都必须 blocked == 1 且 unaccounted == 1（前提不成立则整套判据无意义）。
现网只读：ledger 路径全部 tempfile.TemporaryDirectory 派生；不设 W4_GUARD_REQUIRE_BLOCKED_TARGET；
受拦事件由 sys.audit 合成，不建真实连接，不连 7691/7687。
从 backend/ 目录跑（BACKEND = Path.cwd()，子进程按 tests.support.live_port_guard 导入）。
"""
import hashlib, json, os, subprocess, sys, tempfile
from pathlib import Path

BACKEND = Path.cwd()                      # 从 backend/ 目录跑
GUARD = BACKEND / "tests/support/live_port_guard.py"
CHILD = r'''
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
'''


def run(label, ledger_is_dir, break_stderr):
    with tempfile.TemporaryDirectory(prefix="w4final-") as td:
        tdp = Path(td); child = tdp / "child.py"; child.write_text(CHILD, encoding="utf-8")
        ledger = tdp / "ledger_as_dir"; ledger.mkdir() if ledger_is_dir else None
        if not ledger_is_dir:
            ledger = tdp / "ledger.json"
        env = dict(os.environ); env["PYTHONDONTWRITEBYTECODE"] = "1"
        p = subprocess.run([sys.executable, str(child), str(BACKEND), str(ledger), "1" if break_stderr else "0"],
                           capture_output=True, text=True, env=env, timeout=120)
        payload = {}
        for line in p.stdout.splitlines():
            if line.startswith("CHILD-JSON: "):
                payload = json.loads(line[len("CHILD-JSON: "):])
        return {"label": label, "rc": p.returncode, "acct": payload}


sha0 = hashlib.sha256(GUARD.read_bytes()).hexdigest()
a = run("A ledger=目录 + stderr 坏", True, True)
b = run("B 只落盘失败（ledger=目录 + stderr 正常）", True, False)
c = run("C 只 stderr 坏（ledger 正常 + stderr 坏）", False, True)
for r in (a, b, c):
    print(f"{r['label']}: rc={r['rc']} acct={r['acct']}")
print("sha-unchanged:", hashlib.sha256(GUARD.read_bytes()).hexdigest() == sha0)
print("PRECOND blocked/unaccounted all 1:", all(r["acct"].get("blocked") == 1 and r["acct"].get("unaccounted") == 1 for r in (a, b, c)))
print("A!=B,C:", a["rc"] != b["rc"] and a["rc"] != c["rc"])
