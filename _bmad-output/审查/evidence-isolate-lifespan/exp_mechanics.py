"""机制验证实验（scratchpad，只读 worktree 代码，不写任何 tracked 文件）。

E1: socket.socket.connect monkeypatch 拦 7691/7687（含线程可见性、asyncio sock_connect 路径）
E2: no_lifespan 换栓 → 真实 app.main.app 起 TestClient 零 connect 尝试
E3: 不换栓 → lifespan 的 connect 被拦 + 被 main.py try/except 吞掉（验证负控必须靠 teardown 哨兵）
"""

import asyncio
import os
import socket as socket_mod
import sys
import threading

# 环境隔离：vault/LanceDB 指 tmp（防 orchestrator 扫 live vault 写 pending 文件）
SCRATCH = os.path.dirname(os.path.abspath(__file__))
os.environ["CANVAS_BASE_PATH"] = os.path.join(SCRATCH, "tmp_vault")
os.environ["LANCEDB_DATA_PATH"] = os.path.join(SCRATCH, "tmp_lancedb")
# NEO4J_URI 故意保持 .env 的 7691 —— E3 验证「拦在 connect 前」

BLOCKED_PORTS = {7691, 7687}
events: list[dict] = []
_orig_connect = socket_mod.socket.connect


def guarded_connect(self, address):
    port = None
    if isinstance(address, tuple) and len(address) >= 2 and isinstance(address[1], int):
        port = address[1]
    if port in BLOCKED_PORTS:
        events.append({"address": address, "thread": threading.current_thread().name})
        raise RuntimeError(f"live Neo4j port connect attempted: {address}")
    return _orig_connect(self, address)


socket_mod.socket.connect = guarded_connect

print("=== E1a: 主线程直接 connect 7691 被拦 ===")
try:
    s = socket_mod.socket()
    s.connect(("127.0.0.1", 7691))
    print("E1a FAIL: connect 没被拦")
except RuntimeError as e:
    print(f"E1a PASS: {e}")

print("=== E1b: 子线程 connect 7687 被拦（线程可见性）===")
result = {}


def _t():
    try:
        s = socket_mod.socket()
        s.connect(("127.0.0.1", 7687))
        result["r"] = "FAIL"
    except RuntimeError as e:
        result["r"] = f"PASS: {e}"


t = threading.Thread(target=_t, name="probe-thread")
t.start()
t.join()
print(f"E1b {result['r']}")

print("=== E1c: asyncio loop.sock_connect 路径被拦 ===")


async def _a():
    loop = asyncio.get_running_loop()
    s = socket_mod.socket()
    s.setblocking(False)
    try:
        await loop.sock_connect(s, ("127.0.0.1", 7691))
        return "FAIL"
    except RuntimeError as e:
        return f"PASS: {e}"
    finally:
        s.close()


print("E1c", asyncio.run(_a()))

print("=== E1d: 非拦截端口 7692 正常放行 ===")
try:
    s = socket_mod.socket()
    s.settimeout(2)
    s.connect(("127.0.0.1", 7692))
    s.close()
    print("E1d PASS: 7692 connect 正常完成")
except Exception as e:
    print(f"E1d FAIL: {type(e).__name__}: {e}")

print(f"--- events so far: {len(events)} ---")

# ============ E2/E3: 真实 app.main ============
sys.path.insert(0, "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/backend")
os.chdir("/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/backend")

from contextlib import asynccontextmanager, contextmanager  # noqa: E402

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@asynccontextmanager
async def _noop_lifespan(app_):
    yield


@contextmanager
def no_lifespan(app_):
    router = app_.router
    original = router.lifespan_context
    router.lifespan_context = _noop_lifespan
    try:
        yield app_
    finally:
        router.lifespan_context = original


print("=== E2: no_lifespan 下真实 app 起 TestClient，期望 0 connect 尝试 ===")
before = len(events)
with no_lifespan(app), TestClient(app) as c:
    r = c.get("/api/v1/system/ping") if any("/ping" in str(rt.path) for rt in app.routes) else c.get("/health")
    print(f"E2 request status={r.status_code}")
e2_delta = len(events) - before
print(f"E2 {'PASS' if e2_delta == 0 else 'FAIL'}: connect 尝试 delta={e2_delta}")
print(f"E2 lifespan_context restored: {app.router.lifespan_context is not _noop_lifespan}")

print("=== E3: 不换栓 → lifespan 连接被拦但被吞（TestClient 是否照常进入？）===")
before = len(events)
try:
    with TestClient(app) as c:
        r2 = c.get("/health")
        print(f"E3 TestClient entered OK (lifespan exceptions swallowed), status={r2.status_code}")
except Exception as e:
    print(f"E3 TestClient enter raised: {type(e).__name__}: {e}")
e3_delta = len(events) - before
print(f"E3 connect 尝试 delta={e3_delta} (期望 >0 = 被拦次数；每次都被 main.py 吞掉)")
for ev in events[before : before + 5]:
    print("   blocked:", ev)
print("=== 结论: E3 delta>0 且 TestClient 正常进入 ⇒ 负控必须靠 teardown 哨兵把吞掉的拦截变成 FAIL ===")
