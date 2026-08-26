## 终裁

**不清零，暂不可合入。** 迁移侧 F3 HIGH 已关闭，但 shell 侧 F2 的“超时 fail-closed”门槛未完整实现。

| 门槛 | 裁定 | 证据 |
|---|---|---|
| ① 两侧固定 `/bin/ps` | PASS | [push.sh:54](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/daily-review-push.sh:54)、[migrate:84](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/migrate_daily_review_state.py:84) |
| ② 非零/空/异常/超时 fail-closed | **PARTIAL** | shell 对非零、零长度及执行失败会 `return 1`；但 [push.sh:54](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/daily-review-push.sh:54) 是无 timeout/watchdog 的同步调用。`/bin/ps` 挂死时只会无限阻塞，不能在有界超时后返回失败，不满足 [round6:27](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/_bmad-output/审查/codex-review-CARD-C1a-round6.md:27) 的逐字门槛 |
| ③ 活 PID 查询失败不回收 | PASS | [push.sh:85](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/daily-review-push.sh:85) 将失败置空并直接 skip |
| ④ 自身 token 失败整体不跑 | PASS | [push.sh:61](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/daily-review-push.sh:61) 预检失败退出 78，早于加锁和 runner |
| ⑤ migrate token 失败拒迁 | PASS | [migrate:84](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/migrate_daily_review_state.py:84) 设置 5 秒超时；非零、空输出、`OSError`、`TimeoutExpired` 四类注入均 `rc=1`，旧 state 字节不变，无 new、`.bak` 或最终锁残留 |
| ⑥ 协议逐字节一致 | PASS | shell 命令替换与 [migrate:89](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/migrate_daily_review_state.py:89) 均删除终止 LF、保留尾随空格；真实同 PID 实测 `shell_python_equal=yes`，双方均保留 4 个尾随空格 |

验证：指定 pytest 为 **37 passed、10 warnings**；`bash -n`、Python AST、`git diff --check` 均通过。现有回归没有直接覆盖 owner-token 失败、活 PID 查询失败、超时或跨语言字节协议。

没有发现新的 BLOCKER/HIGH；这里维持的是 round6 原 F2 BLOCKER 的未满足关闭条件。若门槛只要求“卡住时绝不继续”的安全语义，它属于 fail-stop；但“超时”被明确单列后，不能用无限阻塞替代有界失败。

**BLOCKER/HIGH 未清零（1 BLOCKER、0 HIGH）；不可合入。**



---

# 附录 G — 第七轮处置记录（Claude, 2026-08-25）

- **门槛② 超时子项 → 已修**。owner_token 的 /bin/ps 调用改经 /usr/bin/perl -e 'alarm 5; exec ...'（alarm 跨 exec 保留是 POSIX 语义）：ps 挂死 5s 后被 SIGALRM 终止 → 命令替换失败 → return 1，有界 fail-closed，与 migrate 侧 subprocess timeout=5 对称。exec 直通 stdout，协议字节不变。
- 实测：①逐字节协议 BYTE-EQUAL（perl 包装后与 python 侧仍相等）；②死 pid → DEAD-FAILS；③挂死替身（sleep 100 + alarm 2）→ 2.0s 精确终止 TIMEOUT-KILLED；④锁沙盒正常路径 RUNNER-RAN。

## 复验

37 passed；bash -n 通过。
