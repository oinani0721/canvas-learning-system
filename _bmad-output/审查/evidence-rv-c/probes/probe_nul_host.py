"""RV-C 只读探针：含 NUL 的主机名 —— socket.connect 事件在失败之前还是之后触发？

安全性：目标端口一律 65000（无害），且探针 hook 一律抛异常阻断。绝不出现 7691/7687。
"""
import socket
import sys

SENTINEL = "\x00w4-live-port-guard-selftest"
EVENTS = []


class _Stop(Exception):
    pass


def _hook(event, args):
    if event == "socket.connect":
        EVENTS.append(repr(args[1] if len(args) > 1 else None))
        raise _Stop("probe blocked")


sys.addaudithook(_hook)


def attempt(label, addr):
    n = len(EVENTS)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect(addr)
        print(f"{label}: RETURNED (unexpected)")
    except _Stop:
        print(f"{label}: audit FIRED FIRST -> event seen, addr={EVENTS[-1]}")
    except Exception as exc:
        fired = len(EVENTS) > n
        print(f"{label}: {type(exc).__name__} (audit fired first? {fired}) -> {exc}")
    finally:
        s.close()


print("=== does a NUL-containing hostname even reach the audit event? ===")
attempt("sentinel host, port 65000", (SENTINEL, 65000))
attempt("plain NUL host,  port 65000", ("\x00evil", 65000))
attempt("normal host,     port 65000", ("127.0.0.1", 65000))

print()
print("=== _is_selftest_address gate arithmetic (exact reimplementation) ===")


class StrSub(str):
    def __eq__(self, other):
        return True

    def __hash__(self):
        return hash(str(self))


class TupSub(tuple):
    def __getitem__(self, i):
        return SENTINEL if i == 0 else 7691


def is_selftest(address):
    if type(address) is not tuple:
        return False
    try:
        if tuple.__len__(address) < 1:
            return False
        host = tuple.__getitem__(address, 0)
    except Exception:
        return False
    return type(host) is str and host == SENTINEL


cases = [
    ("genuine sentinel tuple", (SENTINEL, 7691)),
    ("tuple subclass lying via __getitem__", TupSub(("127.0.0.1", 7691))),
    ("plain tuple + str-subclass host (__eq__ always True)", (StrSub("127.0.0.1"), 7691)),
    ("plain tuple, real live-port host", ("127.0.0.1", 7691)),
    ("empty tuple", ()),
]
for label, addr in cases:
    print(f"  is_selftest({label:52s}) = {is_selftest(addr)}")
