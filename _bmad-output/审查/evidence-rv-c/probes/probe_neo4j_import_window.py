"""RV-C 只读探针：install() :604 的 assert_neo4j_target_blocked 早于 :605 装 hook —
窗口内 `from neo4j import Address` 这次延迟 import 能发起什么网络动作？

安全性：探针自己的 audit hook 只**记录**并对受拦端口抛异常；不设 NEO4J_URI，
不构造 driver，不连接任何端口。
"""
import sys

CONNECTS = []
SUBPROCS = []
OPENS = []


def _hook(event, args):
    if event == "socket.connect":
        addr = args[1] if len(args) > 1 else None
        CONNECTS.append(repr(addr))
    elif event in ("subprocess.Popen", "os.exec", "os.system"):
        SUBPROCS.append((event, repr(args)[:200]))
    elif event == "socket.getaddrinfo":
        CONNECTS.append(f"getaddrinfo{args!r}")


sys.addaudithook(_hook)

print("=== before import neo4j ===")
print("  neo4j in sys.modules:", "neo4j" in sys.modules)
print("  connects so far:", len(CONNECTS))

from neo4j import Address  # noqa: E402
from neo4j import api as neo4j_api  # noqa: E402

print()
print("=== after `from neo4j import Address` + `from neo4j import api` ===")
print("  socket.connect / getaddrinfo events during import:", len(CONNECTS))
for c in CONNECTS:
    print("    -", c)
print("  subprocess/exec events during import:", len(SUBPROCS))
for s in SUBPROCS:
    print("    -", s)
print("  Address:", Address)
print("  neo4j version:", __import__("neo4j").__version__)

print()
print("=== does Address.parse() itself resolve/connect? ===")
n_before = len(CONNECTS)
a = Address.parse("127.0.0.1:7692")
print("  Address.parse('127.0.0.1:7692') =", repr(a), "type=", type(a).__name__)
print("  is tuple subclass:", isinstance(a, tuple), "| exact tuple:", type(a) is tuple)
print("  tuple.__getitem__(a, 1) =", tuple.__getitem__(a, 1), "type=", type(tuple.__getitem__(a, 1)).__name__)
print("  new connect/getaddrinfo events from parse:", len(CONNECTS) - n_before)
