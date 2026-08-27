"""G4-12 守卫测试 (BATCH-2026-08-27-第四批 / CARD-G4-12): 检索回归门禁指标键完整性.

防的是一个具体事故形态: compare_with_baseline 对缺键 `continue` 静默跳过 —
指标改名 (recall_* → hit_*) 后若键面半迁移 (baseline 未迁 / producer 未迁),
被改名的指标在门禁比对里被静默跳过, 该指标失守而其余指标照常比对 —
门禁"绿灯"对失守指标是假象 (详见 docs/known-gotchas.md G-METRIC-001)。

五类断言 (Codex round-1 HIGH 整改后补齐 producer 侧):
1. METRIC_DIRECTIONS 用名实相符的 hit_* 键 (DD-13: 分母为 query 数的是
   hit rate 不是 recall)。
2. 磁盘上的 baseline/last_run JSON 已迁移为 hit_* 键。
3. 全部门禁指标在真实 baseline 中可解析 (resolve_baseline_metric 非 None)
   — 防缺键静默跳过。
4. 行为级反事实: 拿只含 legacy recall_* 键的旧 baseline 喂
   compare_with_baseline, 指标回退必须被检出 (legacy 别名兼容真的在工作,
   而不是靠 continue 溜走)。
5. producer 输出侧 (AST 静态): run_queries/run_tiers 构造的 metrics 字面量
   键必须覆盖全部门禁键且零 recall_* — 封死"方向表/baseline/测试已迁而
   producer 仍产旧键"的半迁移反事实 (此形态下当前值按 hit_* 取到 None,
   同样触发静默跳过)。
"""

from __future__ import annotations

import ast
import importlib.util
import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = BACKEND_DIR / "scripts"
BASELINE_DIR = BACKEND_DIR / "tests" / "fixtures" / "regression_baselines"

MEMORY_BASELINES = (
    BASELINE_DIR / "memory_retrieval_baseline.json",
    BASELINE_DIR / "memory_retrieval_last_run.json",
)
VAULT_BASELINES = (
    BASELINE_DIR / "vault_retrieval_baseline.json",
    BASELINE_DIR / "vault_retrieval_last_run.json",
)


def _load_script(filename: str):
    """以模块形式加载 scripts/ 下的回归脚本 (模块级只有常量与函数定义)."""
    path = SCRIPTS_DIR / filename
    name = filename.removesuffix(".py")
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _memory_mod():
    return _load_script("run_memory_retrieval_regression.py")


def _vault_mod():
    return _load_script("run_vault_retrieval_regression.py")


# ---------------------------------------------------------------------------
# 1. 指标键名实相符 (DD-13)
# ---------------------------------------------------------------------------


def test_memory_metric_directions_canonical_hit_names():
    mod = _memory_mod()
    keys = set(mod.METRIC_DIRECTIONS)
    assert keys == {
        "hit_at_5",
        "mrr",
        "duplicate_rate",
        "false_positive_rate",
        "leak_rate",
    }, f"memory 门禁指标键应为 hit_* 正名集合, 实际: {sorted(keys)}"
    assert not any(k.startswith("recall_") for k in keys), (
        "分母为 query 数的指标是 hit rate, 不得再叫 recall_* (G4-12 名实修正)"
    )


def test_vault_metric_directions_canonical_hit_names():
    mod = _vault_mod()
    keys = set(mod.METRIC_DIRECTIONS)
    assert "hit_at_10" in keys and "recall_at_10" not in keys, (
        f"vault 门禁指标应为 hit_at_10 (fork 同病同修), 实际: {sorted(keys)}"
    )
    assert len(keys) == 10, f"vault 门禁指标应为 10 项, 实际 {len(keys)}"


# ---------------------------------------------------------------------------
# 2. 磁盘 baseline/last_run 已迁移为 hit_* 键
# ---------------------------------------------------------------------------


def test_memory_baseline_files_migrated_to_hit_keys():
    for path in MEMORY_BASELINES:
        metrics = json.loads(path.read_text(encoding="utf-8"))["metrics"]
        assert "hit_at_5" in metrics, f"{path.name} 未迁移: {sorted(metrics)}"
        # hit_at_5_judged 是非门禁参考指标: --no-judge 运行合法地不产该键
        # (Codex round-1 MEDIUM 整改: 不强制存在, 但存在时必须已是 hit_* 名,
        # 由下面的零 recall_* 断言兜底)
        assert not any(k.startswith("recall_") for k in metrics), f"{path.name} 残留 recall_* 旧键: {sorted(metrics)}"


def test_vault_baseline_files_migrated_to_hit_keys():
    for path in VAULT_BASELINES:
        metrics = json.loads(path.read_text(encoding="utf-8"))["metrics"]
        assert "hit_at_10" in metrics, f"{path.name} 未迁移: {sorted(metrics)}"
        assert not any(k.startswith("recall_") for k in metrics), f"{path.name} 残留 recall_* 旧键: {sorted(metrics)}"


# ---------------------------------------------------------------------------
# 3. 全部门禁指标对真实 baseline 可解析 — 防缺键 continue 静默跳过
# ---------------------------------------------------------------------------


def test_memory_all_gate_metrics_resolvable_from_baseline():
    mod = _memory_mod()
    for path in MEMORY_BASELINES:
        base_metrics = json.loads(path.read_text(encoding="utf-8"))["metrics"]
        for name in mod.METRIC_DIRECTIONS:
            assert mod.resolve_baseline_metric(base_metrics, name) is not None, (
                f"{path.name} 缺门禁指标 {name!r} — compare_with_baseline 会对该键静默 continue, 该指标失守"
            )


def test_vault_all_gate_metrics_resolvable_from_baseline():
    mod = _vault_mod()
    for path in VAULT_BASELINES:
        base_metrics = json.loads(path.read_text(encoding="utf-8"))["metrics"]
        for name in mod.METRIC_DIRECTIONS:
            assert mod.resolve_baseline_metric(base_metrics, name) is not None, (
                f"{path.name} 缺门禁指标 {name!r} — 门禁静默失守"
            )


# ---------------------------------------------------------------------------
# 4. 行为级反事实: legacy 旧键 baseline 上, 回退必须被检出
# ---------------------------------------------------------------------------


def test_memory_regression_detected_against_legacy_baseline():
    """旧 baseline 只有 recall_* 键时, hit_* 门禁仍必须逮住回退 (别名兼容)."""
    mod = _memory_mod()
    report = {
        "metrics": {
            "hit_at_5": 0.0,  # 相比 legacy 1.0 = 灾难级回退
            "mrr": 1.0,
            "duplicate_rate": 0.0,
            "false_positive_rate": 0.0,
            "leak_rate": 0.0,
        }
    }
    legacy_baseline = {
        "metrics": {
            "recall_at_5": 1.0,
            "mrr": 1.0,
            "duplicate_rate": 0.0,
            "false_positive_rate": 0.0,
            "leak_rate": 0.0,
        }
    }
    regressions = mod.compare_with_baseline(report, legacy_baseline, tolerance=0.02)
    assert any("hit_at_5" in r for r in regressions), (
        f"legacy baseline 下 hit_at_5 的回退被静默吞掉 (缺键 continue 陷阱): {regressions}"
    )


def test_vault_regression_detected_against_legacy_baseline():
    mod = _vault_mod()
    zero = dict.fromkeys(mod.METRIC_DIRECTIONS, 0.0)
    report = {"metrics": {**zero, "hit_at_10": 0.0}}
    legacy_baseline = {"metrics": {**zero, "recall_at_10": 1.0}}
    legacy_baseline["metrics"].pop("hit_at_10", None)
    regressions = mod.compare_with_baseline(report, legacy_baseline, tolerance=0.02)
    assert any("hit_at_10" in r for r in regressions), f"legacy baseline 下 hit_at_10 的回退被静默吞掉: {regressions}"


# ---------------------------------------------------------------------------
# 5. producer 输出侧 (AST 静态) — 封死"其余全迁而 producer 仍产旧键"反事实
#    (Codex round-1 HIGH 整改: 不跑 HTTP/LanceDB 管道, 静态解析 metrics
#     字面量键与打印契约, 无 mock)
# ---------------------------------------------------------------------------


def _producer_metric_keys(script_name: str, func_name: str) -> set:
    """解析脚本 AST, 提取 func 内 `metrics = {...}` 字面量的字符串键."""
    tree = ast.parse((SCRIPTS_DIR / script_name).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == func_name:
            for sub in ast.walk(node):
                if not isinstance(sub, ast.Assign) or not isinstance(sub.value, ast.Dict):
                    continue
                if any(isinstance(t, ast.Name) and t.id == "metrics" for t in sub.targets):
                    return {k.value for k in sub.value.keys if isinstance(k, ast.Constant)}
    raise AssertionError(f"{script_name}::{func_name} 内未找到 metrics 字面量 — producer 结构变了, 守卫需同步")


def test_memory_producer_emits_canonical_hit_keys():
    mod = _memory_mod()
    produced = _producer_metric_keys("run_memory_retrieval_regression.py", "run_queries")
    missing = set(mod.METRIC_DIRECTIONS) - produced
    assert not missing, f"producer 不产门禁键 {sorted(missing)} — 比较器当前值取 None 静默跳过"
    assert not any(k.startswith("recall_") for k in produced), f"producer 仍产 recall_* 旧键: {sorted(produced)}"
    src = (SCRIPTS_DIR / "run_memory_retrieval_regression.py").read_text(encoding="utf-8")
    assert 'report["metrics"]["hit_at_5_judged"]' in src and 'report["metrics"]["recall_at_5_judged"]' not in src, (
        "judge 参考指标写入侧未完成 hit_at_5_judged 改名"
    )
    assert "m['hit_at_5']" in src and "m['recall_at_5']" not in src, "打印契约未完成 hit@5 改名"


def test_vault_producer_emits_canonical_hit_keys():
    mod = _vault_mod()
    produced = _producer_metric_keys("run_vault_retrieval_regression.py", "run_tiers")
    missing = set(mod.METRIC_DIRECTIONS) - produced
    assert not missing, f"producer 不产门禁键 {sorted(missing)} — 比较器当前值取 None 静默跳过"
    assert not any(k.startswith("recall_") for k in produced), f"producer 仍产 recall_* 旧键: {sorted(produced)}"
    src = (SCRIPTS_DIR / "run_vault_retrieval_regression.py").read_text(encoding="utf-8")
    assert "m['hit_at_10']" in src and "m['recall_at_10']" not in src, "打印契约未完成 hit@10 改名"
