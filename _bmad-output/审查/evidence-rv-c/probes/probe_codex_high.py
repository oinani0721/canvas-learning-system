"""RV-C：独立验证 Codex p1 的 HIGH —— 记账前的不可信调用抛异常 ⇒ 「已阻断、零账本」。

方式：import 真模块（不修改文件、不装 audit hook、不建 socket），直接调用
guard._audit_hook(...) 这个纯函数，观察 STATE 账本。
"""
import importlib.util
import pathlib
import sys

# 直接从 e06009bc 落盘副本加载，绑定审查对象而不是工作区
SPEC_PATH = pathlib.Path(__file__).with_name("lpg.py")
spec = importlib.util.spec_from_file_location("lpg_e06009bc", SPEC_PATH)
g = importlib.util.module_from_spec(spec)
sys.modules["lpg_e06009bc"] = g          # dataclass 自省需要先注册
spec.loader.exec_module(g)

LIVE = sorted(g.BLOCKED_PORTS)[0]
print(f"loaded from {SPEC_PATH.name}; BLOCKED_PORTS={sorted(g.BLOCKED_PORTS)}; probe port={LIVE}")
print()


def ledger():
    return (g.STATE.total, g.STATE.blocked, len(g.STATE.records))


def run(label, address):
    before = ledger()
    outcome = "returned None (allowed)"
    try:
        r = g._audit_hook("socket.connect", (None, address))
        outcome = f"returned {r!r} (ALLOWED)"
    except g._SelfTestBlocked:
        outcome = "_SelfTestBlocked (selftest branch)"
    except RuntimeError as e:
        outcome = f"RuntimeError (blocked+billed): {str(e)[:40]}..."
    except BaseException as e:
        outcome = f"{type(e).__name__} ESCAPED: {e}"
    after = ledger()
    d = tuple(a - b for a, b in zip(after, before))
    print(f"{label:46s} | {outcome:52s} | Δtotal/blocked/records = {d}")
    return d


print("=== baseline: a plain live-port address must be blocked AND billed ===")
run("plain ('127.0.0.1', LIVE)", ("127.0.0.1", LIVE))

print()
print("=== Codex HIGH path 1: __index__ raises ValueError (extract_port only catches TypeError) ===")


class IndexRaises:
    def __index__(self):
        raise ValueError("second evaluation explodes")


run("(host, IndexRaises())", ("127.0.0.1", IndexRaises()))


class IndexRaisesRuntime:
    def __index__(self):
        raise RuntimeError("second evaluation explodes")


run("(host, IndexRaisesRuntime())", ("127.0.0.1", IndexRaisesRuntime()))

print()
print("=== control: __index__ raises TypeError (the ONE caught type) ===")


class IndexTypeError:
    def __index__(self):
        raise TypeError("caught by extract_port")


run("(host, IndexTypeError())", ("127.0.0.1", IndexTypeError()))

print()
print("=== Codex HIGH path 2: tuple subclass whose __repr__ raises (STATE.record does repr first) ===")


class ReprRaises(tuple):
    def __repr__(self):
        raise ValueError("repr explodes")


run("ReprRaises(('127.0.0.1', LIVE))", ReprRaises(("127.0.0.1", LIVE)))

print()
print("=== final ledger ===")
print(f"  STATE.total={g.STATE.total} blocked={g.STATE.blocked} advisory={g.STATE.advisory} records={len(g.STATE.records)}")
print()
print("=== control: tuple shorter than 2 slots (the diff-set row I originally missed) ===")
run("('127.0.0.1',) - single slot", ("127.0.0.1",))

print()
print("=== where exactly does record() do repr vs increment? ===")
import inspect
src = inspect.getsource(g._GuardState.record).splitlines()
for i, line in enumerate(src):
    if "repr(" in line or "total" in line or "with self._lock" in line:
        print(f"   record()+{i:2d}: {line.rstrip()}")
