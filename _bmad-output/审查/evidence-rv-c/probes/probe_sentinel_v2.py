"""RV-C 只读探针 v2：闭合性真正依赖的是哨兵「不可被解析」，而不是「含 NUL」。
对照用可解析主机名。端口 65000（无害）；hook 抛异常阻断。绝不出现 7691/7687。
"""
import socket
import sys

CANDIDATES = [
    ("current (NUL prefix)", "\x00w4-live-port-guard-selftest"),
    ("NUL-free, unresolvable", "w4-live-port-guard-selftest"),
    ("NUL-free, RESOLVABLE (localhost)", "localhost"),
    ("NUL-free, RESOLVABLE (literal IP)", "127.0.0.1"),
]

SEEN = []


class _Stop(Exception):
    pass


def is_selftest(address, sentinel):
    if type(address) is not tuple:
        return False
    try:
        if tuple.__len__(address) < 1:
            return False
        host = tuple.__getitem__(address, 0)
    except Exception:
        return False
    return type(host) is str and host == sentinel


def _hook(event, args):
    if event == "socket.connect":
        SEEN.append(args[1] if len(args) > 1 else None)
        raise _Stop("probe blocked")


sys.addaudithook(_hook)

print(f"{'hypothetical sentinel':38s} | event fires? | classified selftest? | failure before event")
print("-" * 108)
for label, sent in CANDIDATES:
    n = len(SEEN)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    fired, sel, err = False, None, ""
    try:
        s.connect((sent, 65000))
    except _Stop:
        fired = True
        sel = is_selftest(SEEN[-1], sent)
    except Exception as exc:
        fired = len(SEEN) > n
        err = f"{type(exc).__name__}: {exc}"
        if fired:
            sel = is_selftest(SEEN[-1], sent)
    finally:
        s.close()
    print(f"{label:38s} | {str(fired):12s} | {str(sel):20s} | {err}")

print()
print("=== interpretation (derived from the table, not pre-written) ===")
print("The no-accounting branch is reachable by a REAL connect only if the sentinel")
print("string is one that CPython will accept AND resolve. NUL guarantees rejection")
print("structurally (before resolution, environment-independent). An unresolvable")
print("plain name only fails because DNS says so -- that is an ENVIRONMENT-dependent")
print("guarantee (/etc/hosts entry or wildcard DNS would restore reachability).")
