"""RV-C 追加探针：两层 uvloop 防御能否被同一个动作同时穿过？

live_port_guard.py:486-487 的论证：
  「import 事件用来关死 uvloop：毒化 sys.modules 会被『del 掉再 import』绕过
    （R1 Codex HIGH-4 实测），而 audit hook 摘不掉。」
即：第 2 层（audit 分支）是用来兜住第 1 层（毒化）被 del 规避的情形。

本探针检验：`del sys.modules[X]` + `importlib.import_module(X)` 这一个动作，
是否同时脱出两层。本机未安装 uvloop，用标准库纯 Python 模块 colorsys 作替身，
只检验机制，不加载任何事件循环库。
"""
import sys, importlib

X = "colorsys"
SEEN = []
def _hook(event, args):
    if event == "import":
        SEEN.append(args[0] if args else None)
sys.addaudithook(_hook)

def poison():
    sys.modules[X] = None

def branch_would_fire(names):
    # 复刻 live_port_guard.py:514 的判据形态：event=="import" and args and args[0]==<name>
    return X in names

print("Layer 1 = poison_uvloop()  (sys.modules[X] = None)")
print("Layer 2 = _audit_hook :514 (event=='import' and args[0] == X)")
print("=" * 104)

# --- 场景 A：只有毒化，直接 import 语句 ---
sys.modules.pop(X, None); poison(); n = len(SEEN)
try:
    __import__(X); a_loaded = True
except ImportError:
    a_loaded = False
print(f"A. poison + `import {X}`                    loaded={a_loaded!s:5s}  branch would fire={branch_would_fire(SEEN[n:])!s:5s}  events={SEEN[n:]}")

# --- 场景 B：只有毒化，用 importlib.import_module ---
sys.modules.pop(X, None); poison(); n = len(SEEN)
try:
    importlib.import_module(X); b_loaded = True
except ImportError:
    b_loaded = False
print(f"B. poison + importlib.import_module()       loaded={b_loaded!s:5s}  branch would fire={branch_would_fire(SEEN[n:])!s:5s}  events={SEEN[n:]}")

# --- 场景 C：del 掉毒化，再用 import 语句（docstring 说的那条规避路径）---
sys.modules.pop(X, None); poison(); del sys.modules[X]; n = len(SEEN)
try:
    __import__(X); c_loaded = True
except ImportError:
    c_loaded = False
print(f"C. poison + del + `import {X}`              loaded={c_loaded!s:5s}  branch would fire={branch_would_fire(SEEN[n:])!s:5s}  events={SEEN[n:]}")

# --- 场景 D：del 掉毒化，再用 importlib.import_module（两层同时穿？）---
sys.modules.pop(X, None); poison(); del sys.modules[X]; n = len(SEEN)
try:
    importlib.import_module(X); d_loaded = True
except ImportError:
    d_loaded = False
print(f"D. poison + del + importlib.import_module() loaded={d_loaded!s:5s}  branch would fire={branch_would_fire(SEEN[n:])!s:5s}  events={SEEN[n:]}")

print()
print("=== READING ===")
print("C 是 docstring 点名的规避路径：模块确实被加载，但 branch fires=True ⇒ 第 2 层接住了。")
print("D 同样加载成功，若 branch fires=False ⇒ 两层被同一个动作同时穿过，")
print("   docstring :486-487 的『audit hook 兜底』论证在这条入口上不成立。")
