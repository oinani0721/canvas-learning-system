# Story 7.3: Prompt Regression Test — Shared Fixtures
# [Source: _bmad-output/implementation-artifacts/7-3-prompt-version-regression-test.md]
"""
Shared fixtures for prompt regression tests.

Provides:
  - prompt_registry: Pre-loaded PromptRegistry instance
  - baseline_loader: Helper to load baseline scenario JSON files
  - llm_mode: Dual mode support (replay vs live)
  - regression_report: Collects per-test metrics for report generation
"""

import importlib
import json
import logging
import os
import shutil
import subprocess
import tempfile
import urllib.request
from pathlib import Path
from typing import Any, Dict, List

import pytest
from app.services.prompt_registry import PromptRegistry

logger = logging.getLogger(__name__)

# Directories
_BACKEND_DIR = Path(__file__).parent.parent.parent
_PROMPTS_DIR = _BACKEND_DIR / "app" / "prompts"
_BASELINES_DIR = _BACKEND_DIR / "tests" / "fixtures" / "regression_baselines"


def pytest_addoption(parser):
    """Add --live and --prompt CLI options for regression tests."""
    parser.addoption(
        "--live",
        action="store_true",
        default=False,
        help="Run regression tests with real LLM calls (default: replay mode)",
    )
    parser.addoption(
        "--prompt",
        action="store",
        default=None,
        help="Run regression tests only for a specific prompt name (e.g., autoscore)",
    )


@pytest.fixture(scope="session")
def is_live_mode(request) -> bool:
    """Whether tests should call real LLM (True) or use replay fixtures (False)."""
    return request.config.getoption("--live", default=False)


@pytest.fixture(scope="session")
def prompt_registry() -> PromptRegistry:
    """
    Session-scoped PromptRegistry loaded with all prompt templates.

    This is a real PromptRegistry (no mocking), loaded from the actual
    prompts/ directory.
    """
    PromptRegistry.reset_instance()
    registry = PromptRegistry.get_instance(prompts_dir=_PROMPTS_DIR)
    registry.load_all()
    return registry


@pytest.fixture(scope="session")
def baselines_dir() -> Path:
    """Path to the regression_baselines/ directory."""
    return _BASELINES_DIR


class BaselineLoader:
    """Load baseline scenario JSON files for a specific prompt type."""

    def __init__(self, prompt_name: str, baselines_dir: Path):
        self._dir = baselines_dir / prompt_name
        self._prompt_name = prompt_name

    def load_all(self) -> List[Dict[str, Any]]:
        """Load all scenario JSON files, sorted by filename."""
        if not self._dir.exists():
            raise FileNotFoundError(f"Baseline directory not found: {self._dir}")
        scenarios = list()
        for f in sorted(self._dir.glob("scenario_*.json")):
            data = json.loads(f.read_text(encoding="utf-8"))
            data["_source_file"] = f.name
            scenarios.append(data)
        if not scenarios:
            raise FileNotFoundError(f"No scenario_*.json files found in {self._dir}")
        return scenarios

    def load_one(self, filename: str) -> Dict[str, Any]:
        """Load a specific scenario file."""
        path = self._dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Scenario file not found: {path}")
        data = json.loads(path.read_text(encoding="utf-8"))
        data["_source_file"] = filename
        return data


@pytest.fixture
def autoscore_baselines(baselines_dir) -> BaselineLoader:
    """Loader for AutoSCORE regression baselines."""
    return BaselineLoader("autoscore", baselines_dir)


@pytest.fixture
def question_gen_baselines(baselines_dir) -> BaselineLoader:
    """Loader for question generation regression baselines."""
    return BaselineLoader("question_gen", baselines_dir)


@pytest.fixture
def context_extract_baselines(baselines_dir) -> BaselineLoader:
    """Loader for context extraction regression baselines."""
    return BaselineLoader("context_extract", baselines_dir)


# Story 2.13: New baseline loaders for retrieval pipeline prompts
@pytest.fixture
def query_rewrite_baselines(baselines_dir) -> BaselineLoader:
    """Loader for query rewrite regression baselines."""
    return BaselineLoader("query_rewrite", baselines_dir)


@pytest.fixture
def crag_grading_baselines(baselines_dir) -> BaselineLoader:
    """Loader for CRAG document grading regression baselines."""
    return BaselineLoader("crag_grading", baselines_dir)


@pytest.fixture
def search_intent_baselines(baselines_dir) -> BaselineLoader:
    """Loader for search intent analysis regression baselines."""
    return BaselineLoader("search_intent", baselines_dir)


@pytest.fixture
def query_optimize_baselines(baselines_dir) -> BaselineLoader:
    """Loader for query optimize regression baselines."""
    return BaselineLoader("query_optimize", baselines_dir)


class RegressionMetricsCollector:
    """Collects per-scenario metrics during a regression test run."""

    def __init__(self):
        self.results: List[Dict[str, Any]] = list()

    def record(
        self,
        scenario_id: str,
        prompt_name: str,
        prompt_version: int,
        metrics: Dict[str, Any],
        passed: bool,
        details: str = "",
    ):
        self.results.append(
            {
                "scenario_id": scenario_id,
                "prompt_name": prompt_name,
                "prompt_version": prompt_version,
                "metrics": metrics,
                "passed": passed,
                "details": details,
            }
        )

    def summary(self) -> Dict[str, Any]:
        total = len(self.results)
        passed_count = sum(1 for r in self.results if r["passed"])
        failed_count = total - passed_count
        pass_rate = (passed_count / total * 100) if total > 0 else 0.0
        return {
            "total_scenarios": total,
            "passed": passed_count,
            "failed": failed_count,
            "pass_rate": pass_rate,
            "results": self.results,
        }


@pytest.fixture
def regression_metrics() -> RegressionMetricsCollector:
    """Per-test metrics collector for regression report generation."""
    return RegressionMetricsCollector()


# ── CARD-TEST-bark-autostub: Bark 外发自动打桩守卫 ──────────────────────
# 生产链 daily_review_run.main() → send_bark.send() → _urlopen(POST
# {server}/push) 会真推真机 (--now 10:00+08:00 恒在推送窗内); send 失败还会
# osascript 真弹 macOS 通知。此前全靠每条测试各自记得替换 send — 新增一条
# main() 测试忘替换 = 真推。本 fixture 把「忘了打桩」的默认后果从「真推」
# 翻转为「响亮失败」。

#: 守卫布防面 (按模块名末段判定):
#:   - test_daily_review* 前缀 — 语义化前缀: 叫这个名字的文件几乎必然是
#:     每日复习测试 (含未来的 test_daily_review_push.py 等), 全部布防;
#:     前缀挂在**功能名**上, 不会像 endswith 那样误伤 foo_test_daily_review_run;
#:   - bark_egress_probe / bark_coldstart_probe 精确名 — 本卡的负门探针
#:     与冷启动探针 (都不带 test_ 前缀, 默认收集不到)。
#: 其它命名的新文件 (如 test_review_push.py) 不布防: 要布防就把它加进
#: _BARK_GUARDED_MODULES 或改名进 test_daily_review* 系列 — 这是如实边界
#: (验收单裁决点 5), 不是疏漏。布防 = 该测试期间 import scripts 模块并打
#: 六层桩, 不布防的文件零 import / sys.path 副作用 (卡文 (b) 模块门铁律)。
_BARK_GUARDED_PREFIX = "test_daily_review"
_BARK_GUARDED_MODULES = ("bark_egress_probe", "bark_coldstart_probe")


#: 层⑤a 要清掉哪些 env —— 判据必须与消费方**同口径**。
#: urllib 的 getproxies_environment() 是把 key `.lower()` **之后**再看是不是
#: `*_proxy` 后缀, 所以 Http_Proxy / HTTP_proxy 这类混合大小写它照样认;
#: 原来那份固定的全小写+全大写枚举清单认不出来, 于是混合大小写的代理能活着
#: 穿过布防期 (R1 round-3 审查实测首跳落到机外代理)。
#: 枚举式白名单碰上「归一化后匹配」的消费方必漏 —— 这里改成同样先归一化再判。
#: no_proxy 一并清: 它 lower() 之后也以 `_proxy` 结尾, 会让
#: getproxies_environment() 非空, 从而把 proxy_bypass 切到 environment 分支。
def _bark_proxy_env_names(environ):
    return [k for k in list(environ) if k.lower().endswith("_proxy")]


#: reload 双保险 / teardown 后拒绝所盯的模块 = **守卫打过桩的全部模块**,
#: 不只是业务模块。第八批 round-3 的逃逸链是「先 reload urllib.request 抹掉
#: ④⑤, 再 reload send_bark 让 _urlopen 变回真 urlopen」; R1 round-2 审查又
#: 找到同型的第二条: reload(subprocess) 抹掉层⑥, 预绑定的 osascript 别名
#: 随即抵达真 spawn。教训是名单要照着「patch 了谁」列, 不是照着「哪些是
#: 生产模块」列 —— stdlib 被 patch 了就同样要进名单。
#: importlib 自己也在内 (守卫 patch 了 importlib.reload)。
_BARK_PATCHED_MODULES = (
    "send_bark",
    "daily_review_run",
    "urllib.request",
    "subprocess",
    "_scproxy",
    "importlib",
)


def _is_guarded_module(module_name: str) -> bool:
    last = module_name.rsplit(".", 1)[-1]
    return last.startswith(_BARK_GUARDED_PREFIX) or last in _BARK_GUARDED_MODULES


@pytest.fixture(autouse=True)
def _bark_egress_guard(request):
    """daily_review_run 测试的六层外发防线 (function 级 autouse)。

    ① send_bark.KEY_FILE → tmp 假 key (格式合法且真实存在, server 指向
       loopback discard 端口 http://127.0.0.1:9/): 让 load_key 成功, 忘打桩
       的测试必然走到 ② 拒绝器 — 不存在的 key 会让 send 静默 rc=2
       (send 返回 2 / runner.main 归并为 0), 那恰是假绿通道 (Codex
       round-1 HIGH)。env BARK_KEY_FILE 同步重定向: reload (send_bark)
       重跑模块顶层重新解析时仍落 tmp。
    ② send_bark._urlopen → 抛 AssertionError("Bark egress attempted in
       tests") 的拒绝器 — send_bark 的 except 只吞 HTTPError/URLError/
       TimeoutError/OSError (send_bark.py:138/:140), AssertionError 必然
       穿透 send 与 runner.main 炸红测试。
    ③ daily_review_run.osascript_fallback → 记录并返回 True (不弹真通知)。
    ④ 全局 urllib.request.urlopen → 同一拒绝器: 即便某条逃逸路径把
       send_bark._urlopen 还原成「当时的全局 urlopen」, 那个全局也已换成
       拒绝器 — 逃逸的最坏结果从「真出网」变成「响亮失败」。
    ⑤ 代理中和四件套 (R1 完成条件 (b)) — ①的 loopback 兜底只有在「请求
       真的直连本机」时才成立, 有代理就会被转出机 (round-3 H1):
       a) 清空**所有** lower() 之后以 `_proxy` 结尾的 env (与
          getproxies_environment 的归一化口径一致, 含混合大小写);
       b) urllib.request.getproxies → 恒空;
       c) urllib.request._get_proxies / _get_proxy_settings 与 _scproxy 同名
          函数 (darwin) → 恒空。darwin 分支是 `from _scproxy import
          _get_proxies` — 补丁点因此分裂成两处: patch urllib.request 侧管
          当下, patch _scproxy 侧在 `reload(urllib.request)` 重跑该
          from-import 后仍然生效 (2026-09-02 实测: 只 patch _scproxy 当下
          无效, reload 之后才接管; 只 patch urllib.request 侧则 reload 即失
          效)。存根返回的 proxy settings 语义是「一切主机都绕过代理」
          (exceptions=["*"]), 不是「没有代理配置」—— reload(urllib.request)
          之后 proxy_bypass 回真、env 已被 ⑤a 清空, 它会走 macosx 分支读这份
          settings; 返回空 exceptions 等于告诉它「别 bypass」, 别处握持的
          opener 就又走代理了 (round-2 审查实测)。
          非 darwin 平台这两个名字不存在, 按存在性跳过 —— 那里 proxy_bypass
          只看 env, 已被 ⑤a 清空的 env 让它恒返回 False, 于是「别处握持的
          opener 在 reload 之后仍不走代理」这条在非 darwin 上**不成立**,
          如实登记 (本卡的门只在 darwin 上跑过)。
       d) urllib.request._opener → 无代理 opener: 「已建 opener」把代理烘焙
          在自己的 ProxyHandler 里, 事后改 getproxies 管不着它 — 只能整个
          换掉 (round-3 H1 的第二条向量)。
       e) urllib.request.proxy_bypass → 恒 True。⑤d 只换得掉**模块全局**那个
          引用; 别处已经握着的 opener 对象照旧按自己烘焙好的代理走 (R1
          round-1 审查实测: 布防期内 held.open() 首跳仍落 63128)。可行的注入
          点只有这一个: ProxyHandler.proxy_open 里 `proxy_bypass(req.host)`
          是**调用时**从 urllib.request 模块全局解析的名字, 补丁对一切已存在
          实例即时生效; 而 __init__ 里 `meth=self.proxy_open` 是构造时就捕获
          的绑定方法, 改类属性反而无效 (2026-09-02 读源码 + 实测确认)。
          proxy_open 返回 None 会让 OpenerDirector 继续走链到直连 handler。
    ⑥ subprocess.run → osascript 过滤器 (R1 完成条件 (d)): 层③换的是模块
       属性, 换不掉 collection 期 `from daily_review_run import
       osascript_fallback` 已经绑定的函数对象; 该别名执行时仍按模块全局
       查 subprocess.run, 在这里拦 = 在 subprocess 真 spawn 之前拦。
       判定按 argv 里**任一元素的 basename 全等 osascript** (不是 argv[0] 的
       substring): 前者不误吞 /tmp/not-osascript-helper, 也拦得住
       /usr/bin/env osascript 这种间接形态。非 osascript 的调用原样透传。

    独立 MonkeyPatch 实例 (round-1 HIGH): 测试自己的 monkeypatch.undo()
    只拆测试自己的桩, 波及不到本守卫。
    reload 双保险: importlib.reload 的属性式调用被拦, 对 _BARK_PATCHED_MODULES
    的 reload 完成后自动重打六层; 布防 teardown 后, 留存 wrapper 对受保护
    模块的 reload 一律拒绝, 且拒绝发生在 reload **之前** (round-3 H2: 先
    reload 后 raise 不回滚, 模块已被重载)。

    如实边界 (未承诺拦截的形态):
      - `from importlib import reload` 预绑定后再调用, 绕过属性式拦截。此形
        态下 ⑤a/⑤c 仍然有效 (env 与 _scproxy 不随 urllib.request 的 reload
        复原), 所以「不出机」仍成立; 但 ②④ 会被抹掉, 后果是本机 discard 端
        口连接被拒而不是响亮失败。
      - `del sys.modules[...]` 后重建、测试自建第二个模块实例等故意自解脱
        绑, 一律不在威胁模型内。
      - 代理中和覆盖「通过 urllib 出网」这一条链。不走 urllib 的实现
        (requests / httpx / aiohttp / 裸 socket) 有自己的代理栈, ⑤ 管不到;
        当前生产链只用 urllib (同类扫描门背书), 但那是快照事实不是不变量。
      - 布防面只是命名的 test_daily_review* 与探针精确名, 不是整个目录。

    测试内显式 monkeypatch.setattr 可覆盖任意一层 (守卫 setup 在先, 测试
    的 patch 后设先生效) — _capture_bark_request 即覆盖 ①②。
    imports 在模块门之后惰性执行; scripts 目录只对布防模块进 sys.path。
    非布防模块: 本 fixture 只实例化 request 并加入 fixture closure
    (round-3 L3 如实边界), 但不建临时目录、不 import、不打桩。
    """
    if not _is_guarded_module(request.module.__name__):
        yield None
        return

    scripts_dir = _BACKEND_DIR.parent / "scripts"
    patcher = pytest.MonkeyPatch()
    tmp_dir = Path(tempfile.mkdtemp(prefix="bark-guard-"))
    osascript_calls: List[Dict[str, Any]] = []
    reload_band_active = {"on": True}
    # (c) 冷启动残留: 真实默认值必须在 patcher.setenv **之前**取。setenv 之后
    # os.environ["BARK_KEY_FILE"] 已经是 tmp 路径, 那时再读就等于把临时路径
    # 当成「原值」记进 MonkeyPatch, teardown 恢复的仍是已删 tmp 路径 —
    # round-3 M2 的修法读晚了一步, 形态对而语义空转 (R1 实测确认)。
    env_key_file_before = os.environ.get("BARK_KEY_FILE")
    try:
        import _scproxy  # darwin 专有; 非 darwin 平台无此模块
    except ImportError:
        _scproxy = None
    try:
        key_file = tmp_dir / "bark.key"
        # 整段 URL 形态 (load_key 兼容): server 钉死 loopback discard 端口,
        # 且 ⑤ 中和代理 → 逃逸场景下 send 的最坏后果 = 无代理直连本机
        # discard 端口必被拒, 请求不出机
        key_file.write_text("http://127.0.0.1:9/bark-guard-fake-key-0001\n", encoding="utf-8")
        patcher.setenv("BARK_KEY_FILE", str(key_file))
        patcher.syspath_prepend(str(scripts_dir))
        import daily_review_run
        import send_bark

        # 冷启动时 env 重定向先于 lazy import — 模块此刻的 KEY_FILE 就是 tmp
        # 路径; 先手动复位为本进程真实默认 (复刻 send_bark.py:30-33 判定,
        # 用 setenv 之前的 env 值), 再打桩, teardown 即恢复真实默认。
        real_default_key = Path(env_key_file_before or Path.home() / ".config" / "canvas-review" / "bark.key")
        if send_bark.__dict__.get("KEY_FILE") == key_file:
            send_bark.KEY_FILE = real_default_key

        def _refuse_egress(*args, **kwargs):
            raise AssertionError("Bark egress attempted in tests")

        def _stub_osascript(noti):
            osascript_calls.append(dict(noti))
            return True

        def _no_proxies():
            return {}

        def _no_proxy_settings():
            #: 语义是「一切主机都绕过代理」, 不是「没有代理配置」。
            #: urllib 的 _proxy_bypass_macosx_sysconf 拿这份 settings 判 bypass:
            #: exceptions 里的 "*" 会 fnmatch 命中任何 host → 返回 True → 不走代理。
            #: R1 round-2 审查抓出: 原来返回空 exceptions 等于告诉它「别 bypass」,
            #: 于是 reload(urllib.request) 之后 (proxy_bypass 回真、env 已被⑤a 清空
            #: → 走 macosx 分支 → 读到这份 settings) 别处握持的 opener 又开始走代理。
            return {"exclude_simple": True, "exceptions": ["*"]}

        def _always_bypass_proxy(host):
            return True

        _real_subprocess_run = subprocess.run

        def _basename(x):
            #: bytes argv 也要认 (subprocess 接受 bytes), 故走 os.fsdecode
            try:
                return os.path.basename(os.fsdecode(x))
            except TypeError:
                return os.path.basename(str(x))

        def _is_osascript_argv(argv):
            #: 只认两种形态, 不扫整条 argv:
            #:   - argv[0] 的 basename 全等 osascript (生产形态);
            #:   - argv[0] 是 env 转发, 且它的首个非「VAR=值」参数 basename 全等。
            #: 为什么不扫整条: 扫整条会把 ["/usr/bin/printf", "osascript"] 这种
            #: 拿 osascript 当**数据**的普通命令也吞成 rc=0, 守卫就在悄悄改变无关
            #: 命令的行为 (round-3 审查实测)。为什么要认 env 形态: 只看 argv[0]
            #: 会漏掉 /usr/bin/env osascript ... (round-2 审查实测它抵达真 spawn)。
            #: 如实边界 (登记不修): shell=True 的字符串形态、executable= 指定、
            #: sh -c 转发、以及任何包装脚本转发, 都不在拦截面内 —— 当前生产形态
            #: 是固定的 ["/usr/bin/osascript", ...] (daily_review_run.py:196-204)。
            if not argv:
                return False
            if _basename(argv[0]) == "osascript":
                return True
            if _basename(argv[0]) == "env":
                for x in argv[1:]:
                    token = os.fsdecode(x) if isinstance(x, bytes) else str(x)
                    if "=" in token and not token.startswith("-"):
                        continue  # env 的 VAR=值 前缀
                    return _basename(x) == "osascript"
            return False

        def _guarded_subprocess_run(args, *a, **kw):
            argv = list(args) if isinstance(args, (list, tuple)) else [args]
            if argv and _is_osascript_argv(argv):
                osascript_calls.append({"argv": [str(x) for x in argv]})
                return subprocess.CompletedProcess(args, 0, "", "")
            return _real_subprocess_run(args, *a, **kw)

        _safe_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

        def _reapply():
            patcher.setattr(send_bark, "KEY_FILE", key_file)
            patcher.setattr(send_bark, "_urlopen", _refuse_egress)
            patcher.setattr(daily_review_run, "osascript_fallback", _stub_osascript)
            patcher.setattr(subprocess, "run", _guarded_subprocess_run)
            patcher.setattr(urllib.request, "urlopen", _refuse_egress)
            patcher.setattr(urllib.request, "getproxies", _no_proxies)
            patcher.setattr(urllib.request, "_opener", _safe_opener)
            patcher.setattr(urllib.request, "proxy_bypass", _always_bypass_proxy)
            for var in _bark_proxy_env_names(os.environ):
                patcher.delenv(var, raising=False)
            patcher.setattr(importlib, "reload", _guarded_reload)
            for mod, attr, repl in (
                (urllib.request, "_get_proxies", _no_proxies),
                (urllib.request, "_get_proxy_settings", _no_proxy_settings),
                (_scproxy, "_get_proxies", _no_proxies),
                (_scproxy, "_get_proxy_settings", _no_proxy_settings),
            ):
                if mod is not None and hasattr(mod, attr):
                    patcher.setattr(mod, attr, repl)

        _real_reload = importlib.reload

        #: reload 双保险盯的是「守卫打过桩的模块」— reload 它们会重跑模块
        #: 顶层把生产值写回 (KEY_FILE/_urlopen/osascript_fallback/urlopen/
        #: getproxies/_opener), 完成后重打; 不是盯测试模块名 (round-2 自测
        #: 抓出: 拿测试模块名单判被 reload 的生产模块名, 条件恒假)。
        #: reload_band_active: 布防 teardown 后, 受保护模块处于生产态
        #: (真实 key 在位 + 真 urlopen) — 此时留存的旧 wrapper 若真执行
        #: reload 会把生产态写进模块毒化后续测试 (round-2 HIGH), 而
        #: patcher 已 undo 无处重挂桩; fail-closed 唯一安全动作 = 拒绝,
        #: 且拒绝必须发生在 reload 之前 (round-3 HIGH: 先 reload 后 raise
        #: 不回滚, 模块已被重载)。探针 S 门锁这条语义。
        def _guarded_reload(module):
            if module.__name__ in _BARK_PATCHED_MODULES and not reload_band_active["on"]:
                raise RuntimeError(
                    f"reload({module.__name__}) 仅可在 _bark_egress_guard "
                    "布防的测试内调用 (teardown 后受保护模块处于生产态, "
                    "reload 会把真实 key + 真 urlopen 装回模块)"
                )
            #: 重打必须放在 finally: reload 半途抛异常时, 模块顶层**已经**把
            #: 生产值写回去了 (subprocess.run 变回真实现 / send_bark._urlopen
            #: 变回真 urlopen), 只是没执行完; 把重打挂在「正常返回」上等于让
            #: 这种半途失败留下一个失防的模块 (R1 round-3 审查用 trace 在
            #: subprocess.py 中断 reload 实测到预绑定别名随即抵达真 spawn)。
            #: 与第八批 H2「先 reload 后 raise 不回滚」是同一个形状。
            try:
                return _real_reload(module)
            finally:
                if module.__name__ in _BARK_PATCHED_MODULES:
                    _reapply()

        _reapply()
        yield osascript_calls
    finally:
        reload_band_active["on"] = False
        patcher.undo()
        shutil.rmtree(tmp_dir, ignore_errors=True)
