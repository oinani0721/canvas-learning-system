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
#:   - bark_egress_probe 精确名 — 本卡的负门探针。
#: 其它命名的新文件 (如 test_review_push.py) 不布防: 要布防就把它加进
#: _BARK_GUARDED_MODULES 或改名进 test_daily_review* 系列 — 这是如实边界
#: (验收单裁决点 5), 不是疏漏。布防 = 该测试期间 import scripts 模块并打
#: 五层桩, 不布防的文件零 import / sys.path 副作用 (卡文 (b) 模块门铁律)。
_BARK_GUARDED_PREFIX = "test_daily_review"
_BARK_GUARDED_MODULES = ("bark_egress_probe",)


def _is_guarded_module(module_name: str) -> bool:
    last = module_name.rsplit(".", 1)[-1]
    return last.startswith(_BARK_GUARDED_PREFIX) or last in _BARK_GUARDED_MODULES


@pytest.fixture(autouse=True)
def _bark_egress_guard(request):
    """daily_review_run 测试的五层外发防线 (function 级 autouse)。

    ① send_bark.KEY_FILE → tmp 假 key (格式合法且真实存在, server 指向
       loopback discard 端口 http://127.0.0.1:9/): 让 load_key 成功, 忘打桩
       的测试必然走到 ② 拒绝器 — 不存在的 key 会让 send 静默 rc=2
       (send 返回 2 / runner.main 归并为 0), 那恰是假绿通道 (Codex
       round-1 HIGH)。server 用 loopback + ⑤ 禁代理是纵深防御 (round-2/3
       HIGH): 即便某条 reload 逃逸路径让 _urlopen 回到生产 urlopen, 最坏
       后果 = 无代理直连 127.0.0.1:9 必被拒 — 请求不出机、不触真 key、
       不弹通知 (Codex round-3: 无 ⑤ 时系统代理可接管 loopback 请求把它
       转出机, 故 ①+⑤ 成对)。env BARK_KEY_FILE 同步重定向: reload
       (send_bark) 重跑模块顶层重新解析时仍落 tmp。
    ② send_bark._urlopen → 抛 AssertionError("Bark egress attempted in
       tests") 的拒绝器 — send_bark 的 except 只吞 HTTPError/URLError/
       TimeoutError/OSError (send_bark.py:138/:140), AssertionError 必然
       穿透 send 与 runner.main 炸红测试。
    ③ daily_review_run.osascript_fallback → 记录并返回 True (不弹真通知)。
       如实边界: collection 期 `from daily_review_run import
       osascript_fallback` 预绑定的别名不在保护内 (round-3 MEDIUM, 登记
       未修 — 现有 32 条无此形态)。
    ④ 全局 urllib.request.urlopen → 同一拒绝器 (round-2 HIGH): 即便
       `from importlib import reload` 的预绑定形态绕过 reload 拦截、把
       send_bark._urlopen 还原成「当时的全局 urlopen」, 那个全局也已换成
       拒绝器 — 预绑定逃逸的最坏结果从「真出网」变成「响亮失败」。
    ⑤ 全局 urllib.request.getproxies → 恒空 (round-3 HIGH): 布防期内
       urllib 不读 env/系统代理 — ①的 loopback 兜底因此是「直连必拒」,
       不会被代理接管转出机。

    独立 MonkeyPatch 实例 (round-1 HIGH): 测试自己的 monkeypatch.undo()
    只拆测试自己的桩, 波及不到本守卫。
    reload 双保险: importlib.reload 的属性式调用被拦, 对 send_bark /
    daily_review_run 的 reload 完成后自动重打五层; 布防 teardown 后,
    留存 wrapper 对受保护模块的 reload 一律拒绝 (fail-closed, 拒绝发生在
    reload 之前 — round-3 HIGH: 先 reload 后 raise 不回滚)。
    `from importlib import reload` 的预绑定形态绕过重打, 但被 ④+⑤+①
    兜住, 后果是响亮失败或本机必拒连接, 不出机。

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
    try:
        key_file = tmp_dir / "bark.key"
        # 整段 URL 形态 (load_key 兼容): server 钉死 loopback discard 端口,
        # 且 ⑤ 禁代理 → reload 逃逸场景下 send 的最坏后果 = 无代理直连
        # 本机 discard 端口必被拒, 请求不出机
        key_file.write_text("http://127.0.0.1:9/bark-guard-fake-key-0001\n", encoding="utf-8")
        patcher.setenv("BARK_KEY_FILE", str(key_file))
        patcher.syspath_prepend(str(scripts_dir))
        import daily_review_run
        import send_bark

        # round-3 M2: 冷启动时 env 重定向先于 lazy import — 模块此刻的
        # KEY_FILE 是 tmp 路径, 若直接 patcher.setattr 会把「已删的 tmp
        # 路径」记成原值, teardown 残留在 sys.modules 里毒化后续测试。
        # 先手动复位为真实默认 (复刻 send_bark.py:30-33 判定), 再打桩,
        # teardown 即恢复真实默认。仅当本进程首次加载该模块时需要。
        real_default_key = Path(
            os.environ.get("BARK_KEY_FILE") or Path.home() / ".config" / "canvas-review" / "bark.key"
        )
        if send_bark.__dict__.get("KEY_FILE") == key_file:
            send_bark.KEY_FILE = real_default_key

        def _refuse_egress(*args, **kwargs):
            raise AssertionError("Bark egress attempted in tests")

        def _stub_osascript(noti):
            osascript_calls.append(dict(noti))
            return True

        def _reapply():
            patcher.setattr(send_bark, "KEY_FILE", key_file)
            patcher.setattr(send_bark, "_urlopen", _refuse_egress)
            patcher.setattr(daily_review_run, "osascript_fallback", _stub_osascript)
            patcher.setattr(urllib.request, "urlopen", _refuse_egress)
            patcher.setattr(urllib.request, "getproxies", lambda: {})

        _real_reload = importlib.reload

        #: reload 双保险盯的是「守卫打过桩的生产模块」— reload 它们会重跑
        #: 模块顶层把生产值写回 (KEY_FILE/_urlopen/osascript_fallback),
        #: 完成后重打; 不是盯测试模块名 (round-2 自测抓出: 拿
        #: 测试模块名单判被 reload 的生产模块名, 条件恒假)。
        #: reload_band_active: 布防 teardown 后, 受保护模块处于生产态
        #: (真实 key 在位 + 真 urlopen) — 此时留存的旧 wrapper 若真执行
        #: reload 会把生产态写进模块毒化后续测试 (round-2 HIGH), 而
        #: patcher 已 undo 无处重挂桩; fail-closed 唯一安全动作 = 拒绝,
        #: 且拒绝必须发生在 reload 之前 (round-3 HIGH: 先 reload 后 raise
        #: 不回滚, 模块已被重载)。
        _PATCHED_MODULES = ("send_bark", "daily_review_run")

        def _guarded_reload(module):
            if module.__name__ in _PATCHED_MODULES and not reload_band_active["on"]:
                raise RuntimeError(
                    f"reload({module.__name__}) 仅可在 _bark_egress_guard "
                    "布防的测试内调用 (teardown 后受保护模块处于生产态, "
                    "reload 会把真实 key + 真 urlopen 装回模块)"
                )
            result = _real_reload(module)
            if module.__name__ in _PATCHED_MODULES:
                _reapply()
            return result

        patcher.setattr(importlib, "reload", _guarded_reload)
        _reapply()
        yield osascript_calls
    finally:
        reload_band_active["on"] = False
        patcher.undo()
        shutil.rmtree(tmp_dir, ignore_errors=True)
