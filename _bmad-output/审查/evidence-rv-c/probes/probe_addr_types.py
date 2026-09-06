"""RV-C 只读探针：CPython socket.connect 对 AF_INET 到底接受哪些地址类型。

安全性：本探针自己的 audit hook 对**任何** socket.connect 一律抛异常（抛=连接未发生），
且候选端口一律用 9/65000 这类无害值，绝不出现 7691/7687。
"""
import socket
import sys

SEEN = []


class _Stop(Exception):
    pass


def _hook(event, args):
    if event == "socket.connect":
        addr = args[1] if len(args) > 1 else None
        SEEN.append((type(addr).__name__, repr(addr)))
        raise _Stop("probe: connection blocked before it happened")


sys.addaudithook(_hook)


class FakeAddr(tuple):
    """伪装子类：__getitem__/__len__ 对 Python 层撒谎，底层槽位是真值。"""

    def __getitem__(self, i):
        return "127.0.0.1" if i == 0 else 9

    def __len__(self):
        return 2


class DriverLike(tuple):
    """模拟 neo4j._addressing.IPv4Address：诚实的 tuple 子类。"""


def attempt(label, addr):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect(addr)
        print(f"{label}: CONNECT RETURNED (unexpected)")
    except _Stop:
        t, r = SEEN[-1]
        print(f"{label}: audit FIRED, args[1] type={t} repr={r}")
    except TypeError as exc:
        print(f"{label}: TypeError BEFORE audit -> {exc}")
    except Exception as exc:
        print(f"{label}: {type(exc).__name__} -> {exc}")
    finally:
        s.close()


print("=== does AF_INET accept non-tuple sequences? ===")
attempt("list      ['127.0.0.1', 65000]", ["127.0.0.1", 65000])
attempt("plain tup ('127.0.0.1', 65000)", ("127.0.0.1", 65000))
attempt("tuple-sub DriverLike", DriverLike(("127.0.0.1", 65000)))
attempt("tuple-sub FakeAddr(lying)", FakeAddr(("127.0.0.1", 65000)))

print()
print("=== what do the guard's readers see for the lying subclass? ===")
fake = FakeAddr(("127.0.0.1", 65000))
print(f"  fake[1] (overridden)        = {fake[1]}")
print(f"  tuple.__getitem__(fake, 1)  = {tuple.__getitem__(fake, 1)}")
print(f"  len(fake) (overridden)      = {len(fake)}")
print(f"  tuple.__len__(fake)         = {tuple.__len__(fake)}")

print()
print("=== is a list even constructible as an address at all? ===")
try:
    import _socket
    print("  _socket module present:", _socket.__name__)
except Exception as exc:
    print("  _socket unavailable:", exc)
