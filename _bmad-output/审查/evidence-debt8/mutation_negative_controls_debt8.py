#!/usr/bin/env python3
"""CARD-DEBT-8 变异负控制（机械变异，严格串行）。

判据纪律（沿第七批教训）:
  - 判据是「**指定的那道门**必须变红」, 不是「某处有失败」——每条变异
    显式声明 expect_red 的测试 node id, 只有它红才算杀掉。
  - 变异期间必须同时禁掉该缺陷的**全部**防线, 否则纵深防御会让门仍绿,
    误判「门非承重」。本卡新增逻辑各点独立, 逐点变异即可。
  - 还原后与备份**逐字节** sha256 比对, 防「还原没执行」把变异留在源码。
  - 串行：脚本原地改被测文件, 并发会让 B 的还原把 A 的变异写回。

用法: .venv/bin/python ../_bmad-output/审查/evidence-debt8/mutation_negative_controls_debt8.py
（cwd 须为 backend/）
"""

import hashlib
import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[3] / "backend"
RS = BACKEND / "app" / "services" / "review_service.py"
FM = BACKEND / "lib" / "memory" / "temporal" / "fsrs_manager.py"
PROBE = "tests/regression/test_debt8_fsrs_fallback_honest.py"

T_RECORD = f"{PROBE}::test_fallback_record_review_result_reports_honest_algorithm"
T_D3 = f"{PROBE}::test_fallback_record_review_result_keeps_persistence_signal"
T_SCHED = f"{PROBE}::test_fallback_schedule_review_reports_honest_algorithm"
T_STATE = f"{PROBE}::test_fallback_get_fsrs_state_reports_honest_algorithm"
T_REAL = f"{PROBE}::test_real_library_responses_unchanged"

# (id, 目标文件, old, new, 必须变红的门)
MUTATIONS = [
    (
        "M1-schedule-algorithm-恒fsrs45",
        RS,
        '"algorithm": "fsrs-4.5" if lib_ok else "fsrs-fallback-scheduler",\n                }\n                if not lib_ok:',
        '"algorithm": "fsrs-4.5",\n                }\n                if not lib_ok:',
        T_SCHED,
    ),
    (
        "M2-schedule-去degraded_reason键",
        RS,
        'if not lib_ok:\n                    response["degraded_reason"] = "fsrs_library_missing"\n                return response',
        "if not lib_ok:\n                    pass\n                return response",
        T_SCHED,
    ),
    (
        "M3-record-algorithm-恒fsrs45",
        RS,
        '"status": "recorded",\n                    "algorithm": "fsrs-4.5" if lib_ok else "fsrs-fallback-scheduler",',
        '"status": "recorded",\n                    "algorithm": "fsrs-4.5",',
        T_RECORD,
    ),
    (
        "M4-record-去degraded_reason拼接",
        RS,
        'if not lib_ok:\n                    degraded_reason = (\n                        "fsrs_library_missing"\n                        if degraded_reason is None\n                        else f"fsrs_library_missing,{degraded_reason}"\n                    )',
        "if not lib_ok:\n                    pass",
        T_RECORD,
    ),
    (
        "M5-record-degraded覆盖而非拼接（丢D3信号）",
        RS,
        '"fsrs_library_missing"\n                        if degraded_reason is None\n                        else f"fsrs_library_missing,{degraded_reason}"',
        '"fsrs_library_missing"\n                        if degraded_reason is None\n                        else "fsrs_library_missing"',
        T_D3,
    ),
    (
        "M6-get_fsrs_state-去加性块",
        RS,
        'if not self._fsrs_library_ok():\n                result["algorithm"] = "fsrs-fallback-scheduler"\n                result["degraded_reason"] = "fsrs_library_missing"',
        "if not self._fsrs_library_ok():\n                pass",
        T_STATE,
    ),
    (
        "M7-_fsrs_library_ok-恒True（谎报复活）",
        RS,
        'return bool(getattr(self._fsrs_manager, "library_available", True))',
        'return True or bool(getattr(self._fsrs_manager, "library_available", True))',
        T_RECORD,
    ),
    (
        "M8-_fsrs_library_ok-恒False（反向：污染真实库路径）",
        RS,
        'return bool(getattr(self._fsrs_manager, "library_available", True))',
        'return False and bool(getattr(self._fsrs_manager, "library_available", True))',
        T_REAL,
    ),
    (
        "M9-manager实例属性-恒True（底层说谎）",
        FM,
        "self.library_available = FSRS_AVAILABLE",
        "self.library_available = True",
        T_STATE,
    ),
    (
        "M10-log_decision-reason恒FSRS-4.5（决策日志说谎）",
        RS,
        "reason=f\"{'FSRS-4.5' if self._fsrs_library_ok() else 'fallback'} scheduling, \"",
        'reason=f"FSRS-4.5 scheduling, "',
        T_SCHED,
    ),
]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run_gate(node_id: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [".venv/bin/pytest", node_id, "-q", "-p", "no:cacheprovider", "--no-header"],
        cwd=str(BACKEND),
        capture_output=True,
        text=True,
        timeout=300,
    )


def main() -> int:
    # 0. 前置：未变异时指定的门必须全绿（否则「变红」无意义）
    baseline = run_gate(PROBE)
    if baseline.returncode != 0:
        print("ABORT: 变异前探针本身不绿，负控制无意义")
        print(baseline.stdout[-1500:])
        return 2
    print(f"[baseline] {PROBE} 全绿 ✓\n")

    results = []
    for mid, target, old, new, gate in MUTATIONS:
        orig_bytes = target.read_bytes()
        orig_sha = sha(target)
        text = orig_bytes.decode("utf-8")

        occurrences = text.count(old)
        if occurrences != 1:
            print(f"[{mid}] SKIP-ERROR: 锚点命中 {occurrences} 次（须恰好 1）")
            results.append((mid, "ANCHOR-FAIL", occurrences))
            continue

        try:
            target.write_text(text.replace(old, new, 1), encoding="utf-8")
            assert sha(target) != orig_sha, "变异未真正落盘"
            r = run_gate(gate)
            killed = r.returncode != 0
            status = "KILLED(门变红✓)" if killed else "SURVIVED(门仍绿✗=死门)"
            print(f"[{mid}] {gate.split('::')[-1]} → {status}")
            if not killed:
                print(f"    ⚠️ 该门未依赖被变异的逻辑\n{r.stdout[-400:]}")
            results.append((mid, status, r.returncode))
        finally:
            target.write_bytes(orig_bytes)
            restored = sha(target)
            assert restored == orig_sha, (
                f"还原失败! {target} sha {restored} != {orig_sha}"
            )

    print("\n" + "=" * 60)
    killed_n = sum(1 for _, s, _ in results if s.startswith("KILLED"))
    print(f"变异总数 {len(MUTATIONS)} / 杀掉 {killed_n}")
    for mid, status, code in results:
        print(f"  {mid}: {status}")
    # 收尾复核：所有源文件与开跑时一致
    print(f"\n还原复核 review_service.py sha256 = {sha(RS)}")
    print(f"还原复核 fsrs_manager.py   sha256 = {sha(FM)}")
    return 0 if killed_n == len(MUTATIONS) else 1


if __name__ == "__main__":
    sys.exit(main())
