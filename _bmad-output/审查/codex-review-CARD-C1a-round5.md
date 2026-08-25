结论：第五轮仍为 **BLOCKED**。

1. **F2 — 维持 BLOCKER**

   `TZ=UTC` 和“回收权被占即有声退让、不再代清”均属实：[push.sh:49](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/daily-review-push.sh:49)、[push.sh:88](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/daily-review-push.sh:88)。

   但 token 没有固定 locale。相同 PID、同为 UTC，本机实测：

   ```text
   LANG=C              → Mon Aug 24 23:04:15 2026
   LANG=zh_CN.UTF-8    → 一  8月/24 23:04:15 2026
   ```

   wrapper 明确设置中文 locale（[wrapper:10](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/launchd/daily-review-wrapper.sh:10)），手工 push 可来自 C locale。活锁超过六小时后，另一 locale 会在 [push.sh:70](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/daily-review-push.sh:70) 误判 owner token 不匹配，继而进入 [回收路径](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/daily-review-push.sh:76)，仍可造成两个 runner 并行。第四轮的 TZ 漂移只是换成了 locale 漂移。

2. **F3 — 维持 HIGH**

   CRLF 修复属实：[migrate:110](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/migrate_daily_review_state.py:110)、[migrate:125](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/migrate_daily_review_state.py:125)、[migrate:164](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/migrate_daily_review_state.py:164)。生产入口实跑得到 input/new/bak 相同 SHA-256：

   ```text
   0aa85f80b38b5b6bdceeb34baa3875e52a9b59fc439d82048c86203927cb0b5f
   ```

   二次执行也正确判定“迁移已完成”。

   但迁移 token 同样只覆盖 `TZ`、继承 locale（[migrate:78](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/migrate_daily_review_state.py:78)）。例如 C locale 的迁移被暂停超过六小时，zh_CN launchd 会错误回收仍存活的迁移锁；恢复后迁移可与 runner 并发。因此“同协议”尚未达到跨实际调用环境的 exact-byte 同协议。

3. **F6 — 关闭原 HIGH，降为 LOW 残余风险**

   静态外指 symlink 已拒绝，alias 校验后换向也因后续使用 `REAL_VAULT` 而关闭：[wrapper:48](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/launchd/daily-review-wrapper.sh:48)、[wrapper:67](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/launchd/daily-review-wrapper.sh:67)、[wrapper:76](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/launchd/daily-review-wrapper.sh:76)。

   按题定“单用户、同一信任域、竞态主体已完全控制 vault 数据”的模型，剩余 rename+symlink 竞态没有新增能力，接受降级。

   两点记录需纠正：

   - “shell 无法闭合”过强；锚定后的工作目录也可避免部分路径重解析，稳健实现才通常需要 dirfd/openat。
   - 附录称风险已写入验收单并不属实；当前[已知边界](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/_bmad-output/验收单/Story-CARD-C1a-复习管道vault命名空间化.md:102)没有 F6。

   若未来把同 UID、但受 App Sandbox/TCC 限权的进程纳入威胁模型，则应重开 F6：本部署给 `/bin/bash` Full Disk Access，而 macOS 文件权限是按 app 授权的；受限 app 可借该竞态让 wrapper 读写其无权访问的外部 vault，形成 confused deputy。[Apple 官方说明](https://support.apple.com/en-mide/guide/security/secddd1d86a6/web)

验证：指定 pytest 为 `37 passed, 10 warnings in 0.50s`；`bash -n`、迁移脚本 AST、`git diff --check` 均通过。关键文件复核前后 SHA-256 稳定，未修改工作树；未调用真实 Bark/launchctl，未读取 backups 或 vault outputs。

**BLOCKER/HIGH 未清零（剩余 1 BLOCKER、1 HIGH）；不可合入。**

---

# 附录 E — 第五轮处置记录（Claude, 2026-08-25）

- **F2 → 已修**。owner_token 补 LC_ALL=C（优先级压过 wrapper 的 zh_CN LANG 与任何 LC_TIME）；migrate 侧 env 同补。实测：zh_CN.UTF-8 环境、C 环境、python subprocess 三侧 lstart 输出一致；shell $() 与 python rstrip("\n") 的 token 逐字节相等（含尾随空格填充, BYTE-EQUAL 实测）。
- **F3 → 已修**（同一修复: migrate token env 加 LC_ALL=C, 与 push.sh 协议逐字节一致）。
- **F6 → 按裁定降 LOW 已接受**。两点记录已纠正：①wrapper 注释改为"稳健闭合需 dirfd/openat 型 fd-relative I/O"并写明重开条件（App Sandbox/TCC 限权进程入模 → confused deputy）；②验收单已知边界补第 5 条 F6 残余风险（含重评估触发条件）。

## 复验

37 passed；bash -n / ruff 全绿；token 跨 locale/TZ/调用侧逐字节恒定实测。
