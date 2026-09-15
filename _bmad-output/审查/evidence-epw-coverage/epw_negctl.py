"""CARD-EPW-COVERAGE 负控验伪锚驱动（形态＝编辑 $NEW 自身的断言期望值）。

对 (c) 的六组核心断言各留一条对照输入，并随 Codex 四轮整改逐条扩充，**当前 18 条**
（r1 定稿 8 → r1 整改 +4 = 12 → r2 整改 +3 = 15 → r3 整改 +1 = 16 → r4 整改 +2 = 18；
另有两条因断言被改写 / 被 `ruff format` 折行而同步更新了变异串，不计入新增）。
⚠️ 这个数字被写错过一次（曾写 17，实为 16）；现按 `MUTATIONS` 的 **AST 实测**与驱动输出里的
`── 负控` 块数**双向核对**得出。
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
        "(2'a) 实际重试的抽样区间下界 = 0（full jitter 未被削半，Codex r2 MEDIUM-1）",
        "test_retry_actually_sleeps_backoff_seconds_series_2_4_8",
        "assert uniform_calls == [(0, 2), (0, 4), (0, 8)], (",
        "assert uniform_calls == [(1, 2), (0, 4), (0, 8)], (",
    ),
    (
        "(2'b) 传给 sleep 的就是 random.uniform 的返回值（哨兵；Codex r1 HIGH-1 + r3 MEDIUM-1）",
        "test_retry_actually_sleeps_backoff_seconds_series_2_4_8",
        "assert slept_with == sentinels, (",
        "assert slept_with == sentinels[::-1], (",
    ),
    (
        "(2'd) 属性不得对抽样结果做下限抬升（Codex r4 LOW-1）",
        "test_backoff_upper_bound_is_monotonic_and_capped_at_60",
        "assert tiny_returned == [0.001, 0.001, 0.001], (",
        "assert tiny_returned == [0.1, 0.1, 0.1], (",
    ),
    (
        "(3') 死信计数精确等于 1（Codex r4 LOW-3）",
        "test_dead_letter_written_on_retry_exhaustion",
        "这里补一条精确计数断言，让矩阵 #2 的「`episodes_dead_lettered == 1`」说法与实测一致。\n    assert w.metrics.episodes_dead_lettered == 1",
        "这里补一条精确计数断言，让矩阵 #2 的「`episodes_dead_lettered == 1`」说法与实测一致。\n    assert w.metrics.episodes_dead_lettered == 2",
    ),
    (
        "(2'c) 属性原样返回抽样值、不得二次截断（Codex r3 LOW-1）",
        "test_backoff_upper_bound_is_monotonic_and_capped_at_60",
        "assert returned == bounds, f\"",
        "assert returned == [b + 1 for b in bounds], f\"",
    ),
    (
        "(G-4) 重试 warning 逐条带 attempt i/3（Codex r2 LOW-4）",
        "test_retry_warning_includes_attempt_number_and_error_message",
        "assert [f\"attempt {i}/3\" in warnings[i - 1] for i in (1, 2, 3)] == [True, True, True], (",
        "assert [f\"attempt {i}/3\" in warnings[i - 1] for i in (1, 2, 3)] == [True, False, True], (",
    ),
    (
        "(F-4) to_dict 对非零 queue_depth / 耗时的序列化（Codex r2 LOW-1）",
        "test_worker_metrics_to_dict_serializes_nonzero_depth_and_times",
        'assert d["avg_processing_time_ms"] == 1000.0, "avg = (0.5+1.5)/2 * 1000"',
        'assert d["avg_processing_time_ms"] == 999.0, "avg = (0.5+1.5)/2 * 1000"',
    ),
    (
        "(1') 重试成功也记 info（Codex r1 MEDIUM-1）",
        "test_success_after_one_retry",
        'assert len(processed_infos) == 1, f"重试成功后必须记一条 info，实测 {infos}"',
        'assert len(processed_infos) == 2, f"重试成功后必须记一条 info，实测 {infos}"',
    ),
    (
        "(I') 死信落的是原对象本身（Codex r1 MEDIUM-2）",
        "test_retry_reuses_same_task_and_preserves_timestamps",
        'assert store_spy.call_args.args[0] is task, "落进死信的必须是**原对象本身**，不是它的副本"',
        'assert store_spy.call_args.args[0] is not task, "落进死信的必须是**原对象本身**，不是它的副本"',
    ),
    (
        "(1'') metrics 的 queue_depth 值（Codex r1 LOW-2）",
        "test_metrics_snapshot_covers_all_counters",
        'assert snapshot["queue_depth"] == 0, "两条都处理完后队列必须排空"',
        'assert snapshot["queue_depth"] == 1, "两条都处理完后队列必须排空"',
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
for idx, (group, testname, old, mutated) in enumerate(MUTATIONS, start=1):
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
    # Codex r5 LOW-4：同一个用例可能被多条负控打中，文件名只带用例名会互相覆盖，
    # 结果「18 个驱动块」只剩 14 份详细红档。加序号使每条负控各留一份现场。
    (ev / f"epw-negctl-{idx:02d}-{testname}-{TS}.txt").write_text(
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
