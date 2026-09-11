"""CARD-W4-7 (f) M-4 实测：审计 ``import`` 事件对 ``importlib.import_module`` 是否触发。

背景：门对 uvloop 有**两层**防御（模块 docstring 已定性哪一层承重）——

* 承重层：audit hook 的 ``import`` 事件分支 ``elif event == "import" and args[0] == "uvloop"``；
* 非承重层：``poison_uvloop()`` 把 ``sys.modules["uvloop"] = None``（可被 ``del`` 掉再 import，
  所以它**不能**当承重，这一点 docstring 已写明）。

Y8-A 验收单 #13 自述「未实测加载 uvloop 后门是否静默失效」。本脚本就测这一件事：
两条 import 路径（``import uvloop`` 与 ``importlib.import_module("uvloop")``）分别是否
被 audit hook 拦下。

⛔ 只起子进程、只读、不连任何端口、不起事件循环。每条路径一个**全新子进程**——
audit hook 装上就摘不掉，且 ``poison_uvloop`` 会改 ``sys.modules``，同进程内跑两次
第二次的前提就不成立了（降级开关是闩不是事件）。

判据说明：真正要回答的是「**绕过毒化之后**（``del sys.modules['uvloop']``），
audit 的 import 事件还拦不拦得住」——那才是承重层单独的效力。所以每条路径都跑两遍：
一遍带毒化（现状），一遍先 ``del`` 掉毒化条目（只剩承重层）。
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[3] / "backend"

PREAMBLE = """
import json, sys
sys.path.insert(0, %r)

# ⛔ 旁观 hook 必须装在**门之前**：审计 hook 按注册序调用，门的 hook 一抛，
#    后注册的 hook 就跑不到了 —— 装在后面会让事件清单恒为空（第一版实测 []）。
#    它只记录、不拦截、不抛，对被测行为零影响。
_seen_uvloop = []
def _spy(event, args):
    if event == "import" and args and isinstance(args[0], str):
        n = args[0]
        if n == "uvloop" or n.startswith("uvloop."):
            _seen_uvloop.append(n)
sys.addaudithook(_spy)

from tests.support import live_port_guard as g
"""

#: 装门（除无门基线外，所有形态都装）。
_INSTALL = "g.install()\n"

#: 无门基线用的桩：不装门时没有 g.STATE 的账本可读，给一个同形状的空账本。
_NO_GUARD_LEDGER_STUB = """
class _NoLedger:
    @staticmethod
    def ledger():
        return {"total": 0, "blocked": 0, "advisory": 0, "unaccounted": 0, "_no_guard": True}
g.STATE = _NoLedger()
"""

# 四种形态：{import 方式} × {是否先绕过 sys.modules 毒化}
CASES = {
    "plain-import__with-poison": """
try:
    import uvloop
    outcome = "IMPORTED (未被拦)"
except BaseException as e:
    outcome = type(e).__name__ + ": " + str(e)[:80]
""",
    "importlib__with-poison": """
import importlib
try:
    importlib.import_module("uvloop")
    outcome = "IMPORTED (未被拦)"
except BaseException as e:
    outcome = type(e).__name__ + ": " + str(e)[:80]
""",
    "plain-import__poison-removed": """
del sys.modules["uvloop"]          # 绕过非承重的毒化层，只剩 audit hook
try:
    import uvloop
    outcome = "IMPORTED (未被拦)"
except BaseException as e:
    outcome = type(e).__name__ + ": " + str(e)[:80]
""",
    "importlib__poison-removed": """
import importlib
del sys.modules["uvloop"]          # 绕过非承重的毒化层，只剩 audit hook
try:
    importlib.import_module("uvloop")
    outcome = "IMPORTED (未被拦)"
except BaseException as e:
    outcome = type(e).__name__ + ": " + str(e)[:80]
""",
    # ⛔ 无门基线（round-2 Codex MEDIUM）：上面四种形态**都装门**，于是「不装门时
    #    观测到的完整事件序列是四条」这句话在获准证据里**没有出处**。这一条不装门、
    #    只装旁观 hook，把那句话变成可核对的记录。它会真的把 uvloop 导进子进程 ——
    #    独立子进程、不起事件循环、不连任何端口，跑完即退。
    "no-guard__baseline": """
import importlib
_imported = False
try:
    importlib.import_module("uvloop")
    _imported = True
    outcome = "IMPORTED (无门基线：本来就该导进来)"
except BaseException as e:
    outcome = type(e).__name__ + ": " + str(e)[:80]
""",
}

#: 不装门的形态（用于取「无门时的完整事件序列」这条基线）。
_NO_GUARD_CASES = {"no-guard__baseline"}

EPILOGUE = """
led = g.STATE.ledger()
print("PROBE-JSON:" + json.dumps({
    "outcome": outcome,
    "sys_modules_uvloop": repr(sys.modules.get("uvloop")),
    "ledger": {k: led[k] for k in ("total", "blocked", "advisory", "unaccounted")},
    # round-1 Codex MEDIUM：把实际看到的 uvloop 相关 import 事件记下来 ——
    # 「实测触发了 uvloop.includes / uvloop.loop / …」这句话本来只在推理里，
    # 获准证据里没有它，属声明宽于证据。
    "uvloop_import_events": _seen_uvloop,
    "import_succeeded": globals().get("_imported"),
}, ensure_ascii=False))
"""


def main() -> int:
    print("=== M-4：audit `import` 事件 vs importlib.import_module 实测 ===")
    print(f"    interpreter: {sys.executable}")
    print(f"    python: {sys.version.split()[0]}")
    results = {}
    for name, body in CASES.items():
        proc = subprocess.run(
            [sys.executable, "-c", (PREAMBLE % str(BACKEND))
             + (_NO_GUARD_LEDGER_STUB if name in _NO_GUARD_CASES else _INSTALL)
             + body + EPILOGUE],
            cwd=str(BACKEND),
            capture_output=True,
            text=True,
            timeout=120,
            env={"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin"},
        )
        line = next((ln for ln in proc.stdout.splitlines() if ln.startswith("PROBE-JSON:")), "")
        if not line:
            print(f"  [{name}] ⛔ 无裁定行 rc={proc.returncode} stderr={proc.stderr[-300:]}")
            results[name] = None
            continue
        data = json.loads(line[len("PROBE-JSON:") :])
        data["_rc"] = proc.returncode
        results[name] = data
        print(f"  [{name}]")
        print(f"      结果          : {data['outcome']}")
        print(f"      sys.modules   : {data['sys_modules_uvloop']}")
        print(f"      账本          : {data['ledger']}")
        print(f"      uvloop 事件   : {data['uvloop_import_events']}")
        print(f"      子进程 rc     : {proc.returncode}")

    print()
    # ⛔ 完整性先行（round-1 Codex MEDIUM：本跑器原来有**条件性假通过** —— 缺裁定行
    #    只存 None 就继续，最终只看 escaped 是否为空；四条全缺裁定行时照样输出 BLOCKED
    #    并返回 0，且子进程 rc 被打印却不参与判定）。现在三条都当硬前提。
    missing = [n for n, d in results.items() if d is None]
    if missing:
        print(f"M4-VERDICT: INCOMPLETE —— 这些形态没有裁定行，结论不成立: {missing}")
        return 2
    bad_rc = [n for n, d in results.items() if d["_rc"] != 0]
    if bad_rc:
        print(f"M4-VERDICT: INCOMPLETE —— 这些子进程 rc 非 0，裁定不可信: {bad_rc}")
        return 2
    # 「被拦下」必须是**本门**拦的，不能是 ModuleNotFoundError 之类别的原因喂饱判据。
    hook_mark = "uvloop 的 import 被本门拦下"
    removed = {n: d for n, d in results.items() if n.endswith("poison-removed")}
    blocked_by_hook = [n for n, d in removed.items() if hook_mark in d["outcome"]]
    escaped = [n for n, d in removed.items() if "IMPORTED" in d["outcome"]]
    other = [n for n, d in removed.items() if n not in blocked_by_hook and n not in escaped]
    print(f"承重层（毒化被绕过后被**本门**拦下）: {blocked_by_hook}")
    print(f"两层都被越过（IMPORTED）            : {escaped}")
    if other:
        print(f"既非本门拒因也非 IMPORTED（不可归因）: {other}")
    if escaped:
        print("M4-VERDICT: ESCAPED —— 有路径同时越过两层，需要在 audit import 分支上补齐")
        return 1
    if other or len(blocked_by_hook) != len(removed):
        print("M4-VERDICT: INCONCLUSIVE —— 有形态不是被本门拒的，不能据此声称承重层成立")
        return 2
    baseline = results.get("no-guard__baseline")
    if baseline is not None:
        evs = baseline["uvloop_import_events"]
        ok_import = baseline.get("import_succeeded") is True
        print(f"无门基线的完整 uvloop 事件序列: {evs}（导入成功={ok_import}）")
        # ⛔ round-3 Codex MEDIUM-2：只要求「事件列表非空」不够 —— 记下 uvloop.includes
        # 之后加载失败时，子进程照样正常退出，**残缺**序列会被当成「完整序列」。
        # 「完整」这个词要成立，必须同时满足：导入真的成功了 + 确实看到了事件。
        if not ok_import:
            print("M4-VERDICT: INCONCLUSIVE —— 无门基线并未成功导入 uvloop，序列不能算完整")
            return 2
        if not evs:
            print("M4-VERDICT: INCONCLUSIVE —— 无门基线一个 uvloop 事件都没看到，基线不可信")
            return 2
    print("M4-VERDICT: BLOCKED —— 两条 import 路径都被**本门**拦下，承重层单独成立")
    return 0


if __name__ == "__main__":
    sys.exit(main())
