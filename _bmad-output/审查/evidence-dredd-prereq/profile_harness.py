"""CARD-TOOL-dredd-prereq —— schemathesis `case.call()` 分段 profile（**临时** harness）。

⚠️ 本文件是一次性探针，跑完从工作树删除；源码原样存档到
``_bmad-output/审查/evidence-dredd-prereq/profile_harness.py``。**不入 commit。**

目的（卡文 (a)）：回答 Z7-C UAT 留下的那个问题——单次 `case.call()` 的 20–50s 里，
除了「app lifespan 一次 7.1s」之外的部分是什么。

为什么放在 ``backend/tests/contract/`` 且名为 ``test_*.py``：
``backend/pytest.ini:8-9`` 的 ``testpaths = tests`` / ``python_files = test_*.py``
决定了只有这样它才被收集；而 ``tests/contract/`` **不在**
``live_port_guard.EXEMPT_PATH_PREFIXES``（:164）的豁免面里，本文件也**不挂**
任何 ``integration``/``e2e``/``real_neo4j`` marker ——
这是卡文 (b) 要的「门下跑」：让 W4 门按真实口径记账，rc 预期 3。

与生产用例 ``test_openapi_contract.py`` 的**已声明差异**（不得当成等价）：
1. 不走 hypothesis：Case 由 ``operation.Case()`` 显式构造，不是 ``@schema.parametrize()``
   生成 ⇒ ``case._meta is None``，``Case.call()`` 里的 ``_check_modifications()`` /
   ``_revalidate_metadata()``（``generation/case.py:366-368``）被跳过。那两步是对
   无参数 GET 的纯 Python 校验，量级 µs，不足以解释 20–50s，但差异如实登记。
2. 用 ``case.call()`` 不是 ``call_and_validate()``：Z7-C 实测 checks 段 0.00s，
   本卡按卡文只测 ``call()``。
3. schema 在**测试函数内**构建（生产在模块级 :27）。理由：模块级构建发生在
   collection 期，那期间的连接尝试没有 owner，会进 ``unaccounted`` 桶而不是
   归属到用例；放进函数体才能把每一次拦截都算到这个用例名下。
"""

from __future__ import annotations

import statistics
import sys
import threading
import time
from collections import Counter
from typing import Any

import pytest

schemathesis = pytest.importorskip("schemathesis", reason="schemathesis not installed")

from app.main import app  # noqa: E402
from schemathesis.generation import case as st_case  # noqa: E402
from schemathesis.python import asgi as st_asgi  # noqa: E402
from schemathesis.transport import requests as st_requests  # noqa: E402
from tests.support import live_port_guard  # noqa: E402

# ── 探针参数 ────────────────────────────────────────────────────────────────
N_ROUNDS = 5  # 卡文要求每段 ≥5 个样本；一次 call() 产出每段各一个样本
TARGET_PATH = "/api/v1/health"
TARGET_METHOD = "GET"
SPEC_PATH = "/api/v1/openapi.json"  # 与 test_openapi_contract.py:27 逐字相同
SAMPLE_INTERVAL = 0.2  # 采样 profiler 周期（秒）

# ── 采样 profiler ───────────────────────────────────────────────────────────
_CURRENT_SEGMENT = "idle"
_APP_MARKER = "/backend/app/"


class _StackSampler(threading.Thread):
    """每 SAMPLE_INTERVAL 秒抓一次全线程栈顶，按当前段落归桶。

    只读 ``sys._current_frames()``，不改任何状态；抓完立刻转成字符串，不留 frame 引用。
    它回答四段表回答不了的那个问题：**这一段的墙钟具体耗在哪个栈帧上**。
    """

    daemon = True

    def __init__(self) -> None:
        super().__init__(name="dredd-prereq-sampler")
        self._stop = threading.Event()
        self.top: Counter[tuple[str, str]] = Counter()  # (segment, innermost frame)
        self.app_frames: Counter[tuple[str, str]] = Counter()  # (segment, 最内的 backend/app 帧)
        self.samples = 0

    def run(self) -> None:
        own = threading.get_ident()
        while not self._stop.is_set():
            seg = _CURRENT_SEGMENT
            self.samples += 1
            for tid, frame in sys._current_frames().items():
                if tid == own:
                    continue
                f = frame
                if f is None:
                    continue
                self.top[(seg, _fmt_frame(f))] += 1
                while f is not None:
                    if _APP_MARKER in (f.f_code.co_filename or ""):
                        self.app_frames[(seg, _fmt_frame(f))] += 1
                        break
                    f = f.f_back
            self._stop.wait(SAMPLE_INTERVAL)

    def stop(self) -> None:
        self._stop.set()


def _fmt_frame(frame: Any) -> str:
    code = frame.f_code
    name = code.co_filename or "?"
    for marker in ("/site-packages/", "/backend/", "/python3.14/"):
        idx = name.find(marker)
        if idx != -1:
            name = name[idx + 1 :]
            break
    return f"{name}:{frame.f_lineno} {code.co_name}"


# ── 分段账 ──────────────────────────────────────────────────────────────────
SEG_KEYS = (
    "1_client_construct",
    "1_lifespan_startup",
    "2_hooks_before_call",
    "2_serialize_case",
    "3_request",
    "4_lifespan_shutdown",
    "x_hooks_after_call",  # 诊断用：属于「未归类」的一部分，单独量出来
)


class _Ledger:
    def __init__(self) -> None:
        self.times: dict[str, list[float]] = {k: [] for k in SEG_KEYS}
        self.blocked: dict[str, list[int]] = {k: [] for k in SEG_KEYS}
        self.total_wall: list[float] = []
        self.total_blocked: list[int] = []


LEDGER = _Ledger()


def _reset_ledger() -> None:
    """每个用例开头重置分段账（两个用例共用 ``_Timed`` 的模块级写入面）。"""
    global LEDGER
    LEDGER = _Ledger()


class _Timed:
    """``with _Timed('seg'):`` —— 记墙钟 + 该段内 W4 门的 blocked 增量。"""

    def __init__(self, key: str) -> None:
        self.key = key

    def __enter__(self) -> _Timed:
        global _CURRENT_SEGMENT
        self._prev_seg = _CURRENT_SEGMENT
        _CURRENT_SEGMENT = self.key
        self._t0 = time.perf_counter()
        self._b0 = live_port_guard.STATE.blocked
        return self

    def __exit__(self, *exc: Any) -> None:
        global _CURRENT_SEGMENT
        LEDGER.times[self.key].append(time.perf_counter() - self._t0)
        LEDGER.blocked[self.key].append(live_port_guard.STATE.blocked - self._b0)
        _CURRENT_SEGMENT = self._prev_seg
        return None


# ── 计时包装器（monkeypatch，仅本进程本用例内生效） ──────────────────────────
class _TimedClientCM:
    """替换 ``schemathesis.python.asgi.get_client`` 的返回值。

    ``transport/asgi.py:21`` 写的是 ``with asgi.get_client(application) as client:``——
    进入 ``with`` = ``starlette_testclient.TestClient.__enter__`` = 跑一遍 app lifespan
    startup；退出 = shutdown。本包装器把这两处各自计时，并把 ``client.request``
    （``transport/requests.py:195`` 的 ``_request = session.request``）也包上，
    于是「startup / 请求本身 / shutdown」三段边界与源码逐行对得上。
    """

    def __init__(self, application: Any, real_get_client: Any) -> None:
        self._app = application
        self._real_get_client = real_get_client
        self._client: Any = None

    def __enter__(self) -> Any:
        with _Timed("1_client_construct"):
            client = self._real_get_client(self._app)
        with _Timed("1_lifespan_startup"):
            client.__enter__()
        orig_request = client.request

        def timed_request(*args: Any, **kwargs: Any) -> Any:
            with _Timed("3_request"):
                return orig_request(*args, **kwargs)

        client.request = timed_request  # 实例属性遮蔽绑定方法；客户端用完即弃
        self._client = client
        return client

    def __exit__(self, *exc: Any) -> Any:
        with _Timed("4_lifespan_shutdown"):
            return self._client.__exit__(*exc)


def _install_probes(monkeypatch: pytest.MonkeyPatch) -> None:
    """装计时探针。**必须在 schema 建好之后调用**。

    ``openapi/loaders.py:43`` 的 ``from_asgi`` 同样调 ``asgi.get_client(app)``，
    但它用**裸** ``client.get(url)``、**不进 ``with``**（⇒ 建 schema 不跑 lifespan）。
    若先装探针，loader 会拿到 ``_TimedClientCM`` 而不是 TestClient，直接炸。
    """
    real_get_client = st_asgi.get_client
    monkeypatch.setattr(
        st_asgi, "get_client", lambda application: _TimedClientCM(application, real_get_client)
    )

    real_dispatch = st_case.dispatch

    def timed_dispatch(name: str, *args: Any, **kwargs: Any) -> Any:
        key = {"before_call": "2_hooks_before_call", "after_call": "x_hooks_after_call"}.get(name)
        if key is None:
            return real_dispatch(name, *args, **kwargs)
        with _Timed(key):
            return real_dispatch(name, *args, **kwargs)

    monkeypatch.setattr(st_case, "dispatch", timed_dispatch)

    real_serialize = st_requests.RequestsTransport.serialize_case

    def timed_serialize(self: Any, case: Any, **kwargs: Any) -> Any:
        with _Timed("2_serialize_case"):
            return real_serialize(self, case, **kwargs)

    monkeypatch.setattr(st_requests.RequestsTransport, "serialize_case", timed_serialize)


# ── 报告 ────────────────────────────────────────────────────────────────────
def _stat(values: list[float]) -> str:
    if not values:
        return "n=0"
    return (
        f"n={len(values)} median={statistics.median(values):8.3f}s "
        f"min={min(values):8.3f}s max={max(values):8.3f}s range={max(values) - min(values):8.3f}s"
    )


def _emit(sampler: _StackSampler, schema_build: dict[str, Any]) -> None:
    out = print
    out("\n" + "=" * 78)
    out("CARD-TOOL-dredd-prereq — schemathesis case.call() 分段 profile")
    out("=" * 78)
    out(f"schemathesis={schemathesis.__version__}  python={sys.version.split()[0]}")
    out(f"target: {TARGET_METHOD} {TARGET_PATH}   spec={SPEC_PATH}   rounds={N_ROUNDS}")
    out(
        f"一次性成本 · from_asgi 建 schema: {schema_build['wall']:.3f}s "
        f"(blocked+{schema_build['blocked']}, paths={schema_build.get('paths', -1)})"
    )
    out("")
    out("── 四段计时（每段 N_ROUNDS 个样本）───────────────────────────────────")
    for key in SEG_KEYS:
        out(f"  {key:24s} {_stat(LEDGER.times[key])}  blocked/round={LEDGER.blocked[key]}")
    out("")
    out("── 对账：四段之和 vs 整次 case.call() 墙钟 ──────────────────────────")
    four = ("1_client_construct", "1_lifespan_startup", "2_hooks_before_call", "2_serialize_case", "3_request", "4_lifespan_shutdown")
    for i, total in enumerate(LEDGER.total_wall):
        s = sum(LEDGER.times[k][i] for k in four if i < len(LEDGER.times[k]))
        after = LEDGER.times["x_hooks_after_call"][i] if i < len(LEDGER.times["x_hooks_after_call"]) else 0.0
        out(
            f"  round {i + 1}: total={total:8.3f}s  四段和={s:8.3f}s  "
            f"未归类={total - s:10.6f}s (其中 after_call hooks={after:.6f}s, "
            f"余 {total - s - after:.6f}s)  blocked={LEDGER.total_blocked[i]}"
        )
    out(f"  total wall 汇总: {_stat(LEDGER.total_wall)}")
    out("")
    out(f"── 采样 profiler（{SAMPLE_INTERVAL}s/次，共 {sampler.samples} 轮采样）──────────────")
    out("  [栈顶 · 按 (段落, 帧) 计数，Top 20]")
    for (seg, frame), n in sampler.top.most_common(20):
        out(f"    {n:5d}  {seg:24s} {frame}")
    out("  [最内的 backend/app 帧 · Top 20]")
    for (seg, frame), n in sampler.app_frames.most_common(20):
        out(f"    {n:5d}  {seg:24s} {frame}")
    out("")
    out(f"W4 门实时账: {live_port_guard.STATE.summary_line()}")
    out("=" * 78 + "\n")
    sys.stdout.flush()


# ── 用例 ────────────────────────────────────────────────────────────────────
def test_dredd_prereq_call_profile(monkeypatch: pytest.MonkeyPatch) -> None:
    """固定 Case 跑 N_ROUNDS 次 `case.call()`，拆四段计时并打采样火焰计数。

    本用例**预期被 W4 门的结账哨兵判红**（app lifespan 会尝试连现网 Neo4j，
    ``conftest.py:141-158`` 把被拦下的尝试转成用例失败，``:200``/``:202`` 再把
    session 退出码改成 3）。报告在判红之前已经打到 stdout（跑时需 ``-s``）。
    """
    _reset_ledger()
    sampler = _StackSampler()
    sampler.start()
    try:
        # 一次性成本：建 schema（与生产 :27 同一调用；此时探针还没装）
        t0 = time.perf_counter()
        b0 = live_port_guard.STATE.blocked
        schema = schemathesis.openapi.from_asgi(SPEC_PATH, app)
        operation = schema[TARGET_PATH][TARGET_METHOD]
        # ⚠️ 不在这里数 operation 总数：Z7-C 实测「收集 206 个 operation」本身 35.8s，
        # 那是另一笔一次性成本，与本卡要拆的单次 call() 无关，跑它只会污染墙钟。
        # 这里只记 path 条数（读已解析的 paths 字典，不驱动 operation 构造）。
        schema_build = {
            "wall": time.perf_counter() - t0,
            "blocked": live_port_guard.STATE.blocked - b0,
            "paths": len(schema.raw_schema.get("paths", {})) if hasattr(schema, "raw_schema") else -1,
        }

        _install_probes(monkeypatch)

        for _ in range(N_ROUNDS):
            case = operation.Case()
            tb = live_port_guard.STATE.blocked
            tw = time.perf_counter()
            try:
                case.call()
            finally:
                LEDGER.total_wall.append(time.perf_counter() - tw)
                LEDGER.total_blocked.append(live_port_guard.STATE.blocked - tb)
    finally:
        sampler.stop()
        sampler.join(timeout=2)
        _emit(sampler, locals().get("schema_build", {"wall": -1.0, "blocked": -1, "operations": -1}))

    for key in SEG_KEYS:
        assert len(LEDGER.times[key]) >= N_ROUNDS, f"{key} 样本不足: {len(LEDGER.times[key])}"


def test_dredd_prereq_no_lifespan_control(monkeypatch: pytest.MonkeyPatch) -> None:
    """对照组 —— 卡文 (c)② 的「其它」那条替代路径的**实测**代价与效果。

    唯一变量：``tests/support/lifespan.py::no_lifespan`` 把
    ``app.router.lifespan_context``（starlette ``Router.__init__`` 存的那个）临时换成
    no-op，于是 ``TestClient.__enter__`` 照常建 portal、路由表照常是真的，
    但 ``app/main.py:83-446`` 的整条启动副作用不跑。其余一切（同一 schema 构造、
    同一 Case、同一 ASGI transport、同一 ``case.call()``）与主用例逐字相同。

    它同时回答两件事：
    - **效果**：``blocked`` 是否降到 0（这决定 ``conftest.py:141-158`` 的结账哨兵
      会不会把用例判红，以及 ``:202`` 的兜底会不会把 rc 改 3）；
    - **代价**：墙钟降到多少，以及被测对象从「已启动的 app」变成「没启动的 app」——
      本用例只测 ``GET /api/v1/health`` 一个 operation，**不足以**说明其余 205 个
      operation 在未启动状态下响应是否仍与 schema 相符。
    """
    from tests.support.lifespan import no_lifespan

    _reset_ledger()
    sampler = _StackSampler()
    sampler.start()
    try:
        t0 = time.perf_counter()
        b0 = live_port_guard.STATE.blocked
        schema = schemathesis.openapi.from_asgi(SPEC_PATH, app)
        operation = schema[TARGET_PATH][TARGET_METHOD]
        schema_build = {
            "wall": time.perf_counter() - t0,
            "blocked": live_port_guard.STATE.blocked - b0,
            "paths": len(schema.raw_schema.get("paths", {})) if hasattr(schema, "raw_schema") else -1,
        }

        _install_probes(monkeypatch)

        with no_lifespan(app):
            for _ in range(N_ROUNDS):
                case = operation.Case()
                tb = live_port_guard.STATE.blocked
                tw = time.perf_counter()
                try:
                    case.call()
                finally:
                    LEDGER.total_wall.append(time.perf_counter() - tw)
                    LEDGER.total_blocked.append(live_port_guard.STATE.blocked - tb)
    finally:
        sampler.stop()
        sampler.join(timeout=2)
        print("\n### 对照组 no_lifespan（app.router.lifespan_context 换 no-op）###")
        _emit(sampler, locals().get("schema_build", {"wall": -1.0, "blocked": -1, "paths": -1}))

    for key in SEG_KEYS:
        assert len(LEDGER.times[key]) >= N_ROUNDS, f"{key} 样本不足: {len(LEDGER.times[key])}"
