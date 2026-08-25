结论：第四轮仍为 **BLOCKED**。审查快照为 `card/l1-crossvault @ 9fff98c2d3c9`；已检查全部 tracked diff 及未跟踪迁移脚本，关键文件复核期间哈希稳定。

| 项目 | 裁定 | 理由 |
|---|---|---|
| F2 | **维持 BLOCKER** | [owner_token](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/daily-review-push.sh:47) 使用受 `TZ` 影响的 `ps lstart` 文本。同一存活 PID 实测 UTC/Asia-Shanghai token 不同；超过 6 小时后会被误判死锁并回收。[reclaim 清理](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/daily-review-push.sh:86) 又无 ownership/generation token，旧判断仍能删除后来者的回收权，最终可重现两个 runner 并行。 |
| F3 | **维持 HIGH** | [迁移锁](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/migrate_daily_review_state.py:77) 只写裸 PID，与 push 的双 token 协议不一致。更直接的是，[read_text](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/migrate_daily_review_state.py:112) 会规范化 CRLF；隔离实跑合法 CRLF state 得 `rc=0, new_eq_bak=False`，因此首次成功返回并不满足完成态字节相等。 |
| N1 | **关闭** | [mkstemp](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/migrate_daily_review_state.py:149) 在目标同目录独占创建，关闭 FD 后以 [os.replace](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/migrate_daily_review_state.py:153) 原子发布，原“最终路径半写可见”通道已消失。 |
| F6 | **维持 HIGH** | [pwd -P](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/launchd/daily-review-wrapper.sh:67) 只得到物理路径字符串；后续仍按该名字重新解析。隔离复现中，检查通过后把真实目录 rename、在原位置换成外部 symlink，[后续读取](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/launchd/daily-review-wrapper.sh:84) 仍落到 root 外。alias 换向被挡住，但原 TOCTOU 未闭合。 |
| F7 | **关闭** | [日期逻辑](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/memory-health.sh:93) 拒绝非字符串、整串解析，并限制到 `[昨天, 明天]`；垃圾后缀、整数和 `9999-12-31` 均不再假绿。 |
| notification 精确锁定 | **关闭** | [测试](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/backend/tests/regression/test_daily_review_pick.py:242) 已锁定精确四键集合及 `id/group/title/body` 原值。 |
| 空清单守卫 | **关闭** | [守卫](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/launchd/daily-review-wrapper.sh:41) 删除全部空白后判空，`,,,` 与纯 TAB 均失败关闭。 |
| CRLF | **关闭** | wrapper 与 memory-health 均在解析 `.env` 时删除 `\r`。 |
| PID 写失败清理 | **关闭窄项** | [失败分支](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/daily-review-push.sh:51) 会先删除半成品 pid 再收目录。MEDIUM 简记：该 I/O 失败随后可能被当作普通竞争并以 0 退出，可观测性仍不足。 |

验证：指定 pytest 为 `36 passed, 10 warnings in 0.37s`；三个 shell 的 `bash -n` 与 `git diff --check` 通过。绿色回归未执行 shell 回收并发或 containment TOCTOU。未真实调用 Bark/launchd、未跑全量 CI，也未读取 `backups/` 或 vault 输出内容；Graphiti MCP 本轮未暴露。

**BLOCKER/HIGH 未清零（1 BLOCKER、2 HIGH），不可合入。**



---

# 附录 D — 第四轮处置记录（Claude, 2026-08-25）

- **F2 → 已修**。①owner_token 的 ps lstart 钉死 TZ=UTC（两侧任何环境 token 恒定，活进程不再因 TZ 漂移被误判死）；②回收权柄取消代清——权柄被占一律有声退让（stderr 报出 + 每小时档位重复示警 + memory-health 生成:❌ 联动），死柄人工 rmdir 恢复；删除了「无 ownership 的代清」这唯一能删别人权柄的通道。
- **F3 → 已修**。①迁移锁 token 改与 push.sh 同协议（pid + TZ=UTC ps lstart）；②全程二进制读写（read_bytes/wb）——CRLF state 逐字节保真，新增用例 test_migrate_crlf_state_byte_identical_and_idempotent（首迁字节相等 + 重跑判已完成）。
- **F6 → 主张降级为已接受残余风险（LOW）**。已闭合的部分：静态清单项 symlink 指外（round3 前的原始缺陷）与「校验后 alias 换向」（物理路径收口）。剩余形态是「校验后把真实目录 rename 并在原物理路径植入 symlink」——闭合需要 fd-relative I/O，shell 不具备。威胁模型：wrapper 以用户权限跑在单用户机器，能在 VAULTS_ROOT 内做该竞态 rename 的主体必然已拥有对全部 vault 数据的读写权——绕过 containment 检查不带来任何权限提升，这不是特权边界。已在 wrapper 注释与验收单已知边界中记录。

## 复验

37 passed；bash -n 通过；ruff 全绿。
