"""RV-C 追加探针 v2：同一个纯 Python 模块，两种入口，'import' 事件的 args[0] 是否等于模块名？

live_port_guard.py:514 的判据是 `args[0] == "uvloop"` —— 只有当事件为目标模块自身
发出时才命中。目标模块名未出现在事件里 = 该入口对这道分支不可见。
"""
import sys, importlib

SEEN = []
def _hook(event, args):
    if event == "import":
        SEEN.append(args[0] if args else None)
sys.addaudithook(_hook)

TARGET = "colorsys"          # 纯 Python、无 C 扩展依赖、标准库自带

def fresh():
    for m in list(sys.modules):
        if m == TARGET:
            del sys.modules[m]

def trial(label, fn):
    fresh()
    n = len(SEEN)
    fn()
    fired = SEEN[n:]
    hit = TARGET in fired
    print(f"{label:44s} events={len(fired):2d}  contains '{TARGET}'? {str(hit):5s}  {fired}")
    return hit

print(f"target module = {TARGET!r};  guard branch tests `args[0] == <name>`")
print("-" * 104)
a = trial("import statement", lambda: __import__(TARGET))
b = trial("importlib.import_module()", lambda: importlib.import_module(TARGET))

def _spec():
    import importlib.util
    spec = importlib.util.find_spec(TARGET)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[TARGET] = mod
    spec.loader.exec_module(mod)
c = trial("importlib.util + exec_module()", _spec)

print()
print("=== VERDICT for live_port_guard.py:514 (`args[0] == \"uvloop\"`) ===")
for label, hit in (("__import__ / import stmt", a), ("importlib.import_module", b), ("spec + exec_module", c)):
    print(f"  {label:28s}: {'VISIBLE to the branch' if hit else 'INVISIBLE — branch never matches'}")
print()
print("NOTE: uvloop has a SECOND layer — poison_uvloop() sets sys.modules['uvloop']=None,")
print("      which makes every one of these entry points raise ImportError regardless.")
print("      So an invisible row here is a gap in the audit branch, not necessarily an")
print("      end-to-end hole. Verified separately below:")
sys.modules["__rvc_fake_target"] = None
try:
    importlib.import_module("__rvc_fake_target")
    print("  poisoned-module load via importlib.import_module: SUCCEEDED (poison bypassed!)")
except ImportError as e:
    print(f"  poisoned-module load via importlib.import_module: ImportError ({e})")
