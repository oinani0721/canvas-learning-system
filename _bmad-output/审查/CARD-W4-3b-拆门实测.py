#!/usr/bin/env python
# ⛔ 本文件是 CARD-W4-3b 的**拆门实测**脚本，入库作为证据附件（round-1 Codex 指出
#    「KILLED 记录没有完整变异源码，无法独立认证」）。它会**原地改生产源码**再还原，
#    只应在干净工作树上手动跑；不是常设门，任何自动化流程都不要调用它。
"""CARD-W4-3b 拆门实测 —— 每条新门配一次「拆了必须红」。

⛔ 设计约束（本仓历史教训，逐条对应记忆里的坑）：
  * **串行**：原地改生产文件，并发跑会互踩。
  * **还原无条件**：try/finally，且不带任何「先判断再还原」的防护条件。
  * **全文件 sha 基线**：跑前对每个会被变异的文件记 sha，跑完逐个复核 ——
    不靠脚本自己的「我还原过了」自证。
  * **判据绑定被哪一条门拒的**：断言「**指定的那一条**探针/反例翻红」，
    不是「某处失败了」。
  * 变异只打**生产源码**（真被门保护的那份），不打副本。
"""

from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import subprocess
import sys
from contextlib import redirect_stdout
from pathlib import Path

BACKEND = Path("/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z3-w4/backend")
GATE_SH = BACKEND / "scripts/lifespan_isolation_runtime_sha.sh"
NEGCTL = BACKEND / "scripts/lifespan_isolation_negative_control.py"
PROBES = BACKEND / "scripts/lifespan_isolation_guard_probes.py"
PY = BACKEND / ".venv/bin/python"

MUTATED_FILES = [GATE_SH, NEGCTL, PROBES]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


BASELINE = {p: sha(p) for p in MUTATED_FILES}


def load_probes():
    spec = importlib.util.spec_from_file_location("w4probes", PROBES)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["w4probes"] = mod
    spec.loader.exec_module(mod)
    return mod


PROBE_MOD = load_probes()


def run_one_probe(fn_name: str) -> dict:
    """只跑一条探针（生产 shell 脚本已被就地变异）。"""
    buf = io.StringIO()
    with redirect_stdout(buf):
        res = getattr(PROBE_MOD, fn_name)()
    return res


def run_ast_negctl() -> str:
    proc = subprocess.run(
        [str(PY), str(NEGCTL), "--ast-negative-control"],
        cwd=BACKEND,
        capture_output=True,
        text=True,
        env={"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin", "HOME": str(Path.home())},
        timeout=300,
    )
    return proc.stdout + proc.stderr


def run_selftest() -> str:
    proc = subprocess.run(
        [str(PY), str(NEGCTL), "--ast-only"],
        cwd=BACKEND,
        capture_output=True,
        text=True,
        env={"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin", "HOME": str(Path.home())},
        timeout=300,
    )
    return proc.stdout + proc.stderr


# ── 变异体定义 ────────────────────────────────────────────────────────────
GLOB_EXPAND_REAL = PROBE_MOD._GLOB_EXPAND_ANCHOR
GLOB_EXPAND_CACHED = PROBE_MOD._GLOB_EXPAND_CACHED
GLOB_CACHE_PRELUDE = PROBE_MOD._GLOB_CACHE_PRELUDE


def mut_cache_glob(text: str) -> str:
    assert GLOB_EXPAND_REAL in text
    out = text.replace(GLOB_EXPAND_REAL, GLOB_EXPAND_CACHED)
    assert "\nsnapshot() {" in out
    return out.replace("\nsnapshot() {", "\n" + GLOB_CACHE_PRELUDE, 1)


def mut_widen_glob_sh(text: str) -> str:
    old = '"${BACKEND_DIR}/app/data/vault_index_pending__*.jsonl"'
    assert old in text
    return text.replace(old, '"${BACKEND_DIR}/app/data/vault_index_pending*.jsonl"')


def mut_drop_legacy_fixed_sh(text: str) -> str:
    old = '  "${BACKEND_DIR}/app/data/vault_index_pending.jsonl"\n'
    assert old in text
    out = text.replace(old, "")
    assert "EXPECTED_FIXED_COUNT=3" in out
    return out.replace("EXPECTED_FIXED_COUNT=3", "EXPECTED_FIXED_COUNT=2")


def mut_drop_sort_sh(text: str) -> str:
    old = '    __sorted="$(builtin printf \'%s\\n\' "$__raw" | LC_ALL=C "$SORT_BIN")" || {'
    assert old in text, "sort 锚点不在脚本里"
    return text.replace(old, '    __sorted="$__raw" || {')


def mut_drop_disq_subtract(text: str) -> str:
    old = "            self.fastapi_returning_funcs -= self.disqualified_factory_keys"
    assert old in text
    return text.replace(old, "            pass  # MUTANT: 差集被拆掉")


def mut_accumulate_disq(text: str) -> str:
    """回退成「跨迭代累积失格」（M16 的原缺陷）。"""
    old = """            frozen = set(self.fastapi_returning_funcs)
            self.fastapi_returning_funcs = frozen
            self._factory_verdicts = {}"""
    assert old in text, "冻结锚点不在文件里"
    new = """            self._factory_verdicts = getattr(self, "_factory_verdicts", {})  # MUTANT: 不清空 ⇒ 跨迭代累积"""
    return text.replace(old, new)


def mut_transient_publish(text: str) -> str:
    """把 M16 修复**完整回退**成 round-1 Codex HIGH-1 抓到的那一版。

    ⚠️ 第一版变异只在 `_mark_fastapi_returning` 末尾追加一句 `funcs.add(key)`，
    结果 **SURVIVED** —— 因为轮末的 `funcs = set(verdicts)` 会把它整个覆盖掉，
    变异根本没生效。忠实复现必须三处联动：可信集 add-only + 失格集每轮重算 +
    差集在轮末。这一条属「拆掉被测防线」，不是「拆别的层」。
    """
    old_block = """        for _ in range(2):
            # (1) 冻结：本轮求值只看上一轮结束时的知识。`_is_local_app_factory_call`
            #     读的是 self.fastapi_returning_funcs，所以直接把它按住不动，
            #     裁定写进独立的 verdicts，轮末才发布。
            frozen = set(self.fastapi_returning_funcs)
            self.fastapi_returning_funcs = frozen
            self._factory_verdicts = {}
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    self._mark_fastapi_returning(node)"""
    assert old_block in text, "_mark_all 的执行块锚点不在文件里"
    new_block = """        for _ in range(2):
            # MUTANT: 回退成 HIGH-1 的那一版（可信集 add-only、失格集每轮重算）
            self.disqualified_factory_keys = set()
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    self._mark_fastapi_returning(node)"""
    out = text.replace(old_block, new_block)

    old_publish = """            # (3) 发布：两个集合一起重建。先全放进可信集，再减掉失格的那些 ——
            #     ⛔ 下面这个差集**承重**：注释掉它，E 的两条反例当场 MISSED
            #     ⇒ AST-NEGATIVE-CONTROL: FAIL（LOW#18 的常设门）。
            verdicts = self._factory_verdicts
            self.fastapi_returning_funcs = set(verdicts)
            self.disqualified_factory_keys = {k for k, ok in verdicts.items() if not ok}
            self.fastapi_returning_funcs -= self.disqualified_factory_keys"""
    assert old_publish in out, "发布块锚点不在文件里"
    out = out.replace(old_publish, "        self.fastapi_returning_funcs -= self.disqualified_factory_keys")

    old_verdict = "        self._factory_verdicts[key] = self._factory_verdicts.get(key, True) and ok"
    assert old_verdict in out
    new_verdict = """        if ok:
            self.fastapi_returning_funcs.add(key)  # MUTANT: 直接 add，暂态资格立刻可见
        else:
            self.disqualified_factory_keys.add(key)"""
    return out.replace(old_verdict, new_verdict)


def mut_last_definition_wins(text: str) -> str:
    """把按 key 的 `and` 聚合改成覆盖（「最后一个定义说了算」）。"""
    old = "        self._factory_verdicts[key] = self._factory_verdicts.get(key, True) and ok"
    assert old in text
    return text.replace(old, "        self._factory_verdicts[key] = ok  # MUTANT: 覆盖式，不聚合")


def mut_drop_sorted_globbed(text: str) -> str:
    """去掉 runtime_files 的排序（MEDIUM-2 要求这条能被抓）。"""
    old = "    return fixed + sorted(globbed)"
    assert old in text
    return text.replace(old, "    return fixed + globbed  # MUTANT: 不排序")


def mut_cache_runtime_files(text: str) -> str:
    old = """    fixed = [backend_dir / rel for rel in RUNTIME_FILE_RELPATHS]
    globbed: list[Path] = []
    for pattern in RUNTIME_FILE_GLOBS:
        globbed.extend(backend_dir.glob(pattern))
    return fixed + sorted(globbed)"""
    assert old in text
    new = """    fixed = [backend_dir / rel for rel in RUNTIME_FILE_RELPATHS]
    key = str(backend_dir)
    cache = globals().setdefault("_MUTANT_CACHE", {})
    if key not in cache:
        globbed: list[Path] = []
        for pattern in RUNTIME_FILE_GLOBS:
            globbed.extend(backend_dir.glob(pattern))
        cache[key] = sorted(globbed)
    return fixed + cache[key]"""
    return text.replace(old, new)


def mut_widen_glob_py(text: str) -> str:
    old = '    "app/data/vault_index_pending__*.jsonl",'
    assert old in text
    return text.replace(old, '    "app/data/vault_index_pending*.jsonl",')


def mut_drop_legacy_relpath_py(text: str) -> str:
    old = '    "app/data/vault_index_pending.jsonl",\n'
    assert old in text
    return text.replace(old, "")


# ── 用例表：(编号, 说明, 被变异文件, 变异函数, 裁判, 判据) ─────────────────
def judge_probe(fn_name: str):
    def _j():
        res = run_one_probe(fn_name)
        return (not res["ok"]), f"{fn_name} ok={res['ok']} rc={res['rc']} reason={res['reason'][:200]}"

    return _j


def judge_ast_missed(labels: list[str]):
    def _j():
        out = run_ast_negctl()
        missed = [lab for lab in labels if f"*** MISSED ***: {lab}" in out]
        failed = "AST-NEGATIVE-CONTROL: FAIL" in out
        ok = failed and len(missed) == len(labels)
        return ok, f"FAIL={failed} MISSED={missed}"

    return _j


def judge_ast_false_positive(labels: list[str]):
    def _j():
        out = run_ast_negctl()
        fps = [lab for lab in labels if f"*** FALSE POSITIVE ***: {lab}" in out]
        failed = "AST-NEGATIVE-CONTROL: FAIL" in out
        ok = failed and len(fps) == len(labels)
        return ok, f"FAIL={failed} FALSE_POSITIVE={fps}"

    return _j


def judge_selftest(substr: str):
    def _j():
        out = run_selftest()
        failed = "RUNTIME-FILES-SELFTEST: FAIL" in out
        hit = substr in out
        return (failed and hit), f"SELFTEST_FAIL={failed} 判据串命中={hit}"

    return _j


CASES = [
    ("T1", "runtime_sha.sh：glob 展开提到快照外（缓存）", GATE_SH, mut_cache_glob,
     judge_probe("probe_runtime_glob_absent_to_present")),
    ("T2", "runtime_sha.sh：glob 放宽回 vault_index_pending*", GATE_SH, mut_widen_glob_sh,
     judge_probe("probe_runtime_glob_sidecar_excluded")),
    ("T3", "runtime_sha.sh：删掉旧固定名精确项", GATE_SH, mut_drop_legacy_fixed_sh,
     judge_probe("probe_runtime_legacy_journal_watched")),
    ("T4", "runtime_sha.sh：去掉 LC_ALL=C sort", GATE_SH, mut_drop_sort_sh,
     judge_probe("probe_runtime_glob_expansion_sorted")),
    ("T5", "negative_control.py：注释掉失格差集（LOW#18）", NEGCTL, mut_drop_disq_subtract,
     judge_ast_missed([
         "同名工厂重定义：安全版在前，不安全版在后（阻断项 E 的原始形态）",
         "同名工厂重定义：不安全版在前，安全版在后（顺序反过来同样不算数）",
     ])),
    ("T6", "negative_control.py：失格名单回退成跨迭代累积（M16）", NEGCTL, mut_accumulate_disq,
     judge_ast_false_positive(["验伪锚 12：转调工厂，被调者定义在**后**（前向引用，合法）"])),
    ("T10", "negative_control.py：恢复暂态资格传播（round-1 HIGH-1 的那一版）", NEGCTL, mut_transient_publish,
     judge_ast_missed(["转调一个同名重定义过的工厂（round-1 Codex HIGH-1 的组合形态）"])),
    ("T11", "negative_control.py：按 key 聚合改成覆盖（最后一个定义说了算）", NEGCTL, mut_last_definition_wins,
     judge_ast_missed(["同名工厂重定义：不安全版在前，安全版在后（顺序反过来同样不算数）"])),
    ("T12", "negative_control.py：去掉 runtime_files 的 sorted(globbed)", NEGCTL, mut_drop_sorted_globbed,
     judge_selftest("glob 项没有按字节序排列")),
    ("T7", "negative_control.py：runtime_files 缓存 glob 展开", NEGCTL, mut_cache_runtime_files,
     judge_selftest("glob 没有每次重新展开")),
    ("T8", "negative_control.py：glob 放宽回 vault_index_pending*", NEGCTL, mut_widen_glob_py,
     judge_selftest("进了监视面")),
    ("T9", "negative_control.py：删掉旧固定名精确项", NEGCTL, mut_drop_legacy_relpath_py,
     judge_selftest("不在监视清单里")),
]


def main() -> int:
    results = []
    for tag, desc, target, mutate, judge in CASES:
        original = target.read_text(encoding="utf-8")
        try:
            target.write_text(mutate(original), encoding="utf-8")
            killed, detail = judge()
        finally:
            target.write_text(original, encoding="utf-8")
        results.append({"tag": tag, "desc": desc, "file": target.name, "killed": killed, "detail": detail})
        print(f"[{'KILLED' if killed else '*** SURVIVED ***'}] {tag} {desc}\n        {detail}", flush=True)

    print("\n=== 还原复核（全文件 sha 与跑前基线逐个比对）===")
    drift = []
    for p, expect in BASELINE.items():
        actual = sha(p)
        same = actual == expect
        print(f"  {'OK ' if same else 'DRIFT'} {p.name} {actual[:16]}")
        if not same:
            drift.append(p.name)
    survived = [r["tag"] for r in results if not r["killed"]]
    print(json.dumps({"survived": survived, "drift": drift}, ensure_ascii=False))
    return 1 if (survived or drift) else 0


if __name__ == "__main__":
    sys.exit(main())
