终裁：第五轮的 locale/TZ 修复有效，但 exact-byte 协议仍未闭合。

1. **F2 — 维持 BLOCKER**

   [daily-review-push.sh:50](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/daily-review-push.sh:50) 仍调用由 `PATH` 解析的裸 `ps`，且外层 `printf` 掩盖 `ps` 失败，[第 54 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/daily-review-push.sh:54) 无法捕获。

   同一存活 PID 实测：

   ```text
   PATH 无 ps       → rc=0, b"<pid> "
   标准 PATH        → rc=0, b"<pid> Tue Aug 25 ... 2026    "
   byte_equal       → false
   ```

   另一调用侧会在 [71–72 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/daily-review-push.sh:71) 错判活 owner；锁超过六小时后仍可进入回收并启动第二个 runner。回收权机制无法保护被错误判死的原 owner。

2. **F3 — 维持 HIGH**

   [migrate_daily_review_state.py:82](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/migrate_daily_review_state.py:82) 同样使用裸 `ps`；不检查 `returncode`，异常或五秒超时后将 `lstart=""`，仍在 [第 89 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/migrate_daily_review_state.py:89) 写入 `"<pid> "` 并继续迁移。wrapper 则固定系统 PATH（[wrapper:8](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/launchd/daily-review-wrapper.sh:8)）。

   真实迁移入口通过临时 FIFO 暂停复现：迁移 PID 仍存活，锁内为 `b"18061 "`，标准 `/bin/ps` 重算为 `b"18061 Tue Aug 25 04:28:30 2026    "`，逐字节不等。

确认有效的部分：固定系统 `/bin/ps` 时，locale、TZ、`COLUMNS`、`COMMAND_MODE` 及 shell/Python 调用侧均相等；尾随四个空格保留、终止 LF 均删除。

验证：指定回归 `37 passed, 10 warnings`；`bash -n`、迁移脚本 AST、`git diff --check` 通过。但回归中没有 owner-token、`lstart`、PATH 或 `ps` 失败测试。F6 未重裁。`graphiti-canvas` 本轮未暴露，不影响本地逐字节反例。

关闭门槛：两侧固定同一绝对 `ps`，并对非零、空输出、异常和超时 fail-closed；活 PID 的 token 查询失败时不得回收。

**最终：BLOCKER/HIGH 未清零（1 BLOCKER、1 HIGH）；不可合入。**



---

# 附录 F — 第六轮处置记录（Claude, 2026-08-25）

按 round6 给出的关闭门槛逐项落实：

- **两侧固定同一绝对 /bin/ps** — push.sh owner_token 与 migrate 的 token 生成均改 `/bin/ps`（PATH 剥夺实测 PATH-IMMUNE：PATH=/nonexistent 下 token 输出与标准 PATH 逐字节相等）。
- **fail-closed 全路径**：
  - push.sh owner_token：ps 非零或空输出 → return 1（printf 不再掩盖失败）；
  - 自身 token 启动即推导，失败 → PREFLIGHT-FAIL exit 78（与 KEY 推导同门，坏环境整体不跑，绝不写残缺 token）；
  - 活 pid 的 token 查询失败 → fail-closed 当活（skip），查询失败绝不构成回收理由；
  - migrate：ps 非零/空/异常/超时 → 拒绝迁移 rc 1（不写残缺 token 污染 push.sh 判定）。
- **协议逐字节一致**：python 侧 `f"{pid} {stdout.rstrip(chr(10))}"` 与 shell 侧 `printf '%s %s' pid "$(...)"` 实测 BYTE-EQUAL（尾随空格保留、终止 LF 删除）。
- 死 pid 的 token 推导 → 失败（DEAD-PID-FAILS 实测），与 kill -0 判死路径自洽。

## 复验

37 passed；bash -n / ruff 全绿；锁沙盒三分支复跑（正常运行释放 / 真 token 活锁 skip / 活 pid 假 lstart + 陈旧 → 正确回收）全部符合设计。
