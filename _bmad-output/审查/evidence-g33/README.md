# CARD-G3-3 证据 — 负控变异 + 并发取证

> 批次 `[BATCH-2026-09-05-第十一批 / CARD-G3-3]`，工作树 `card-z2-cas`。
> 本文是 **Codex 复核 + 内部对抗审查打回后返工**的复跑结果（2026-09-05）。
> 原始 `.log` 被全局 `.gitignore` 的 `*.log` 吞掉，故逐字转录；结构化结果见同目录 `.json`。

## 一 负控变异（14 条，`backend/scripts/g33_mutation_gates.py`）

```
✅ KILLED   M1-per-node-lock: rc=1 failed=['tests/regression/test_g3_3_cas.py::test_concurrent_same_node_no_lost_update[1]', 'tests/regression/test_g3_3_cas.py::test_concurrent_same_node_no_lost_update[2]']
✅ KILLED   M2-cas-guard: rc=1 failed=['tests/regression/test_g3_3_cas.py::test_cas_conflict_refuses_and_rerun_converges']
✅ KILLED   M3-ledger-lock-backend: rc=1 failed=['tests/regression/test_g3_3_cas.py::test_append_event_refuses_when_ledger_locked']
✅ KILLED   M5-cas-revision-only: rc=1 failed=['tests/regression/test_g3_3_cas.py::test_cas_body_only_change_is_a_conflict']
✅ KILLED   M6-ledger-lock-skill: rc=1 failed=['tests/regression/test_g3_3_cas.py::test_writer_waits_for_held_ledger_lock']
✅ KILLED   M8-thread-lock-lifetime: rc=1 failed=['tests/regression/test_g3_3_cas.py::test_thread_critical_sections_do_not_overlap']
✅ KILLED   M9-splitlines-instead-of-lf: rc=1 failed=['tests/regression/test_g3_3_cas.py::test_dedup_scan_splits_only_on_physical_lf']
✅ KILLED   M10-short-write-unchecked: rc=1 failed=['tests/regression/test_g3_3_cas.py::test_short_write_is_not_reported_as_success']
✅ KILLED   M11-out-of-order-auto-guess: rc=1 failed=['tests/regression/test_g3_3_cas.py::test_out_of_order_is_caller_declared_not_auto_guessed']
✅ KILLED   M12-a3-node-lock: rc=1 failed=['tests/regression/test_g3_3_cas.py::test_incremental_block_waits_for_node_lock']
✅ KILLED   M13-a3-cas: rc=1 failed=['tests/regression/test_g3_3_cas.py::test_incremental_block_cas_preserves_racing_edit']
✅ KILLED   M14-exam-board-ledger-lock: rc=1 failed=['tests/regression/test_g3_3_cas.py::test_exam_board_waits_for_held_ledger_lock']
✅ KILLED   M15-post-lock-redup: rc=1 failed=['tests/regression/test_g3_3_cas.py::test_writer_refuses_when_other_writer_took_the_event_id']
✅ KILLED   M7-lock-dropped-by-second-fd: rc=1 failed=['tests/regression/test_g3_3_cas.py::test_append_event_still_holds_lock_at_the_moment_of_write']

── 汇总 ──
还原逐字节相同: 是
MUTANT 新增残留 (基线之外): 无
rc=0
```

## 二 并发取证 `g33_concurrency_evidence.py --rounds 3`

```
round 1: rc=[0, 0] 账本2条 attempt=2 W=2026-08-01T10:00:01Z validator=0 lost_update=False
round 2: rc=[0, 0] 账本2条 attempt=2 W=2026-08-01T10:00:01Z validator=0 lost_update=False
round 3: rc=[0, 0] 账本2条 attempt=2 W=2026-08-01T10:00:01Z validator=0 lost_update=False

lost_update 轮数: 0/3
```

## 三 pyright

```
$ backend/.venv/bin/pyright tests/regression/test_g3_3_cas.py app/services/learning_event_log.py \
      scripts/g33_mutation_gates.py scripts/g33_concurrency_evidence.py
0 errors, 0 warnings, 0 informations
```
