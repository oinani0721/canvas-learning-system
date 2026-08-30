结论：H1、L1、L2 均已解决；M1 代码层仍未解决，但可降为 LOW 已知限制。未发现 BLOCKER/HIGH/MEDIUM。

## Findings

### BLOCKER

无。

### HIGH

无。

### MEDIUM

无。

### LOW

- **M1 — PARTIAL / UNRESOLVED，但处置可接受。** 日期倒拨反例仍成立：单板状态执行 `D1 → D2 → --now D1 → D2` 时，marker 与 map 值会交替覆盖，门仍会反复开启。[runner 的 `--now`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m3-push/scripts/daily_review_run.py:205)没有隔离/拒绝 live state；两层 wrapper 也会透传参数：[daily-review-wrapper.sh](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m3-push/scripts/launchd/daily-review-wrapper.sh:112)、[daily-review-push.sh](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m3-push/scripts/daily-review-push.sh:149)。但 checked-in launchd `ProgramArguments` 确实不含 `--now`，[plist](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m3-push/scripts/launchd/com.canvas.daily-review.plist:12)，且验收矩阵使用隔离 state，因此可降为 LOW。落档必须明确：手工对生产 vault/state 使用 `--now` 属不支持操作；这不是 RESOLVED。

- **新低风险表面：合法 JSON、错误嵌套类型的空 vault 会提前失败。** [daily_review_run.py:172](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m3-push/scripts/daily_review_run.py:172)在判断 `ranked` 之前无条件调用 `.values()`。若 state 是 `{"board_last_recommended":[]}` 且 vault 无榜，旧实现能够完成空生成，新实现会抛 `AttributeError`。这不影响正常空 dict；迁移器也会拒绝该形态，但 [load_state()](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m3-push/scripts/daily_review_run.py:68)仍未校验嵌套类型，故列为 LOW。

## 一轮 findings 复核

- **H1：RESOLVED。** [兼容门](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m3-push/scripts/daily_review_run.py:172)同时检查 marker 和历史 map 值；[legacy 回归测试](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m3-push/backend/tests/regression/test_daily_review_run.py:337)经真实重扫路径证明同日换榜不二次落账。
- **M1：UNRESOLVED，接受为 LOW 已知限制。** `values()` 仅部分缓解历史日期仍留在其他板值中的情况，无法解决同一板日期被覆盖后的倒拨。
- **L1：RESOLVED。** 测试直接读取磁盘并断言 map、marker 两字段，[随后通过 `load_state()` 重载](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m3-push/backend/tests/regression/test_daily_review_run.py:316)继续第三轮。
- **L2：RESOLVED。** 文件说明、守卫段头及换榜断言注释均已改成“当天首个非空榜首落账一次/已有账后不补写”语义。

marker 缺失但 map 已含 today 时不回填 marker没有坏后果：同日后续运行仍由 map 拦截；下一正常非空日期会同时写入 map 和 marker。空 dict 正常开门；state 按 vault 分文件隔离；`values()` 为 O(板数)，相对于节点扫描没有实质性能风险。

验证：当前测试文件直接导入本工作副本 runner；收集并通过 **25 tests**，结果为 `25 passed, 10 warnings`。`git diff --check` 通过。未宣称整个后端测试套件或已安装的 live wrapper 已验证。

BLOCKER/HIGH 清零: 是


