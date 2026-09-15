"""CARD-EPW-COVERAGE 负控验伪锚驱动（形态＝编辑 $NEW 自身的断言期望值）。

对 (c) 的六组核心断言各留一条对照输入（退避与 count/_redact 各两条 ⇒ 共 7 条）：
每条 = 把新文件里一句核心断言的期望值改成与被测语义矛盾的值 ⇒ 单跑该文件必须变红，
**且红的必须是声称的那条用例**（不是「某处失败」）；随后从跑前 `cp` 副本还原并 `shasum`
逐字节比对。⛔ 不用运行时 patch 形态——文件本身不变的话 shasum 判据恒真、等于没做。
⛔ 不用 `git show HEAD:<新文件>` 还原（负控跑在 commit 之前，HEAD 里没有这个对象）。

用法: python3 epw_negctl.py <树根绝对路径> <evidence 目录绝对路径>
rc=0 且打印 `EPW-NEGCTL-GATE: PASS` 为通过。
"""

import hashlib
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

TS = time.strftime("%Y%m%dT%H%M%S")

root = Path(sys.argv[1])
ev = Path(sys.argv[2])
new_rel = "tests/unit/test_episode_worker_coverage_epw.py"
new_abs = root / "backend" / new_rel
pytest_bin = root / "backend" / ".venv" / "bin" / "pytest"

# (组别, 声称会变红的用例名, 原文, 对照输入)
MUTATIONS = [
    (
        "(1) 成功入队→处理 + metrics 计数",
        "test_metrics_snapshot_covers_all_counters",
        'assert snapshot["success_rate"] == 0.2',
        'assert snapshot["success_rate"] == 0.9',
    ),
    (
        "(2) 退避上界序列",
        "test_backoff_upper_bound_series_is_1_2_4",
        'assert observed_bounds == [(0, 1), (0, 2), (0, 4)]',
        'assert observed_bounds == [(0, 1), (0, 2), (0, 8)]',
    ),
    (
        "(2) 退避单调 + 60s 封顶",
        "test_backoff_upper_bound_is_monotonic_and_capped_at_60",
        'assert bounds[:7] == [1, 2, 4, 8, 16, 32, 60]',
        'assert bounds[:7] == [1, 2, 4, 8, 16, 32, 64]',
    ),
    (
        "(3) 重试耗尽 → 落死信",
        "test_all_attempts_timeout_then_dead_letter",
        'assert mock_graphiti.add_episode.await_count == 4, "初次 + 3 次重试"',
        'assert mock_graphiti.add_episode.await_count == 5, "初次 + 3 次重试"',
    ),
    (
        "(4) 确定性校验错跳过重试",
        "test_deterministic_validation_error_skips_retry_and_dead_letters",
        'assert mock_graphiti.add_episode.await_count == 1, "确定性错误不得重试"',
        'assert mock_graphiti.add_episode.await_count == 4, "确定性错误不得重试"',
    ),
    (
        "(5) 死信隐私：默认不落全文",
        "test_dead_letter_omits_full_body_by_default",
        'assert "episode_body_full" not in record',
        'assert "episode_body_full" in record',
    ),
    (
        "(6) DeadLetterStore.count",
        "test_dead_letter_store_count_matches_appended_lines",
        "assert store.count() == 1",
        "assert store.count() == 2",
    ),
    (
        "(6) _redact 脱敏",
        "test_redact_scrubs_known_secret_patterns",
        'assert "***REDACTED***" in scrubbed',
        'assert "***REDACTED***" not in scrubbed',
    ),
]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run_file() -> tuple[int, str]:
    # ⛔ 继承调用者环境（只叠加 PYTHONDONTWRITEBYTECODE）。换 runner 脚本时静默丢 env
    # 会让两跑不可比，红集差异看起来像「本卡引入新红」，实则是判据环境变了。
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    proc = subprocess.run(
        [
            str(pytest_bin),
            "-q",
            "-p",
            "no:cacheprovider",
            "-rfE",
            new_rel,
        ],
        cwd=str(root / "backend"),
        capture_output=True,
        text=True,
        env=env,
    )
    return proc.returncode, proc.stdout + proc.stderr


original = new_abs.read_text(encoding="utf-8")
fd, backup_name = tempfile.mkstemp(prefix="epw-negctl-orig.", dir="/tmp")
backup = Path(backup_name)
with os.fdopen(fd, "w", encoding="utf-8") as fh:
    fh.write(original)
sha_a = sha(new_abs)
print(f"shasum A = {sha_a}")
print(f"跑前副本 = {backup}")

failures = []
for group, testname, old, mutated in MUTATIONS:
    if original.count(old) != 1:
        print(f"❌ 原文在文件中出现 {original.count(old)} 次（需恰好 1 次）: {old!r}")
        failures.append(group)
        continue
    new_abs.write_text(original.replace(old, mutated), encoding="utf-8")
    rc, out = run_file()
    reddened = f"::{testname}" in out and "FAILED" in out
    named_red = any(line.startswith("FAILED") and testname in line for line in out.splitlines())
    print(f"\n── 负控 {group} → {testname}")
    print(f"   对照输入: {old!r} → {mutated!r}")
    print(f"   rc={rc} 该用例出现在 FAILED 行={named_red}")
    (ev / f"epw-negctl-{testname}-{TS}.txt").write_text(
        f"# 负控 {group}\n# 对照输入: {old!r} → {mutated!r}\n{out}\nrc={rc}\n", encoding="utf-8"
    )
    # 还原：从**跑前 cp 副本**回写（⛔ 不用 git show / git checkout / git stash）
    new_abs.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")
    sha_now = sha(new_abs)
    if rc == 0 or not named_red:
        print(f"   ❌ 对照输入未让**声称的那条用例**变红（rc={rc}, named_red={named_red}, reddened_any={reddened}）")
        failures.append(group)
    if sha_now != sha_a:
        print(f"   ❌ 还原后 shasum 不同: {sha_now}")
        failures.append(group + "/restore")

rc_final, out_final = run_file()
(ev / f"epw-negctl-restored-{TS}.txt").write_text(out_final + f"\nrc={rc_final}\n", encoding="utf-8")
sha_b = sha(new_abs)
print(f"\n还原后整跑 rc={rc_final}")
print(f"shasum B = {sha_b}")
if rc_final != 0:
    failures.append("还原后整跑未全绿")
if sha_b != sha_a:
    failures.append("A != B")

print("\nEPW-NEGCTL-GATE:", "FAIL" if failures else "PASS", failures or "")
sys.exit(1 if failures else 0)
