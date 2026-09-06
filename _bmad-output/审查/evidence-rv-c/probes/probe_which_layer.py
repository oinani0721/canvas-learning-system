"""RV-C 追加探针：AF_UNIX 的哨兵 str 地址，究竟是被哪一层挡住的？

审查提出：它在 :493 的判据处就短路，_is_selftest_address 根本不会被调用；
若属实，报告「D1 承担实际防守职责」这个加粗结论是错的（归因给了错误的层）。
"""
import importlib.util, pathlib, sys

P = pathlib.Path(__file__).with_name("lpg.py")
spec = importlib.util.spec_from_file_location("lpg_layer", P)
g = importlib.util.module_from_spec(spec); sys.modules["lpg_layer"] = g
spec.loader.exec_module(g)

CALLS = []
_orig = g._is_selftest_address
def traced(addr):
    r = _orig(addr)
    CALLS.append((repr(addr)[:48], r))
    return r
g._is_selftest_address = traced

LIVE = sorted(g.BLOCKED_PORTS)[0]
S = g._SELFTEST_HOST

def probe(label, address):
    n = len(CALLS)
    port = g.extract_port(address)
    trust = g.port_is_trustworthy(address)
    guard_493 = (port in g.BLOCKED_PORTS) or (not trust)
    outcome = "no exception"
    try:
        g._audit_hook("socket.connect", (None, address))
    except g._SelfTestBlocked:
        outcome = "_SelfTestBlocked"
    except RuntimeError as e:
        outcome = "RuntimeError(blocked)"
    except BaseException as e:
        outcome = f"{type(e).__name__}"
    called = len(CALLS) > n
    print(f"{label:34s} extract_port={str(port):6s} trust={str(trust):5s} "
          f":493 guard={str(guard_493):5s} | _is_selftest called? {str(called):5s} | {outcome}")

print("Q: for each address shape, does execution even REACH _is_selftest_address (D1)?")
print("-" * 124)
probe("AF_UNIX str (sentinel)", S)
probe("AF_UNIX str (ordinary path)", "/tmp/some.sock")
probe("AF_UNIX bytes", b"/tmp/some.sock")
probe("genuine selftest tuple", (S, LIVE))
probe("plain live-port tuple", ("127.0.0.1", LIVE))
probe("safe tuple (11434)", ("127.0.0.1", 11434))

print()
print("=== _is_selftest_address invocation log ===")
if not CALLS:
    print("  (never called)")
for a, r in CALLS:
    print(f"  called with {a:50s} -> {r}")

print()
print("=== VERDICT ===")
print("If AF_UNIX rows show ':493 guard=False' and '_is_selftest called? False',")
print("then AF_UNIX is stopped by the :493 branch guard, NOT by D1 (type(address) is tuple).")
