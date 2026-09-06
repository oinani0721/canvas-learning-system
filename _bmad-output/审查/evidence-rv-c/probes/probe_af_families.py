"""RV-C 只读探针：NUL 主机名在 AF_INET6 / AF_UNIX 上是否也在 audit 事件之前被拒。
安全性：端口 65000，hook 一律抛异常；绝不出现 7691/7687。
"""
import socket
import sys

SENTINEL = "\x00w4-live-port-guard-selftest"
EVENTS = []


class _Stop(Exception):
    pass


def _hook(event, args):
    if event == "socket.connect":
        EVENTS.append((type(args[1]).__name__, repr(args[1])))
        raise _Stop("probe blocked")


sys.addaudithook(_hook)


def attempt(label, fam, addr):
    n = len(EVENTS)
    try:
        s = socket.socket(fam, socket.SOCK_STREAM)
    except Exception as exc:
        print(f"{label}: socket() unavailable -> {exc}")
        return
    try:
        s.connect(addr)
        print(f"{label}: RETURNED (unexpected)")
    except _Stop:
        print(f"{label}: audit FIRED FIRST -> {EVENTS[-1]}")
    except Exception as exc:
        print(f"{label}: {type(exc).__name__} (audit fired first? {len(EVENTS) > n}) -> {exc}")
    finally:
        s.close()


print("=== AF_INET6: 4-tuple with NUL host ===")
attempt("INET6 sentinel  ", socket.AF_INET6, (SENTINEL, 65000, 0, 0))
attempt("INET6 normal    ", socket.AF_INET6, ("::1", 65000, 0, 0))

print()
print("=== AF_UNIX: address is str/bytes, not tuple ===")
attempt("UNIX  sentinel  ", socket.AF_UNIX, SENTINEL)

print()
print("=== guard readers on an AF_UNIX-style (non-tuple) address ===")
import operator


def extract_port(address):
    if not isinstance(address, tuple):
        return None
    try:
        if tuple.__len__(address) < 2:
            return None
        raw = tuple.__getitem__(address, 1)
    except Exception:
        return None
    try:
        return operator.index(raw)
    except TypeError:
        return None


def port_is_trustworthy(address):
    if not isinstance(address, tuple):
        return True
    try:
        if tuple.__len__(address) < 2:
            return True
        raw = tuple.__getitem__(address, 1)
    except Exception:
        return False
    return type(raw) is int


for label, addr in [
    ("AF_UNIX str path", "/tmp/some.sock"),
    ("bytes path", b"/tmp/some.sock"),
    ("IPv6 4-tuple to 7691", ("::1", 7691, 0, 0)),
]:
    p = extract_port(addr)
    t = port_is_trustworthy(addr)
    # hook judge at :493 -> `port in BLOCKED_PORTS or not port_is_trustworthy`
    verdict = (p in {7691, 7687}) or (not t)
    print(f"  {label:22s} extract_port={p!r:6s} trustworthy={t!s:5s} -> hook blocks? {verdict}")
