## 第八轮终裁

发现 1 个 BLOCKER，门槛②仍未闭合。

[owner_token:58](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/daily-review-push.sh:58) 的 `alarm 5; exec /bin/ps` 在默认信号环境下有效，实测挂死替身 5 秒后 `function_rc=1`。但代码没有恢复或解除 `SIGALRM` 的继承状态。POSIX 规定 `exec` 不仅继承 alarm 剩余时间，也继承 `SIG_IGN` 和 signal mask；被忽略或阻塞的信号不会终止进程。[POSIX exec](https://pubs.opengroup.org/onlinepubs/9799919799/functions/exec.html)、[POSIX signal semantics](https://pubs.opengroup.org/onlinepubs/9799919799/functions/V2_chap02.html)

直接反例：

```text
父进程 trap '' ALRM
alarm 5 + exec sleep 6
→ function_rc=1, elapsed=6s（不是 5s）
```

这里的 `return 1` 只是替身自行结束且 stdout 为空后触发；若目标永久挂死，命令替换仍会永久等待。因此不满足 [round6:27](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/_bmad-output/审查/codex-review-CARD-C1a-round6.md:27) 和 [round7:8](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/_bmad-output/审查/codex-review-CARD-C1a-round7.md:8) 明确要求的“有界超时”，不能以默认 launchd 环境通常可用作为无条件关闭证明。

其余门槛：

| 门槛 | 裁定 | 证据 |
|---|---|---|
| ① 固定绝对路径 | PASS | shell 固定 `/usr/bin/perl` 与 `/bin/ps`；迁移侧固定 `/bin/ps` |
| ② 非零/空/异常/超时 fail-closed | **PARTIAL** | 非零、空、exec 失败、死 PID 均返回 1；仅超时受继承信号状态影响 |
| ③ 活 PID 查询失败不回收 | PASS | [push.sh:92-95](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/daily-review-push.sh:92) 失败置空并 skip |
| ④ 自身 token 失败整体不跑 | PASS | [push.sh:65-68](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/daily-review-push.sh:65) 退出 78 |
| ⑤ migrate 失败拒迁 | PASS | [migrate:84-95](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/migrate_daily_review_state.py:84) 保持 5 秒 timeout 和失败拒迁 |
| ⑥ exact-byte 协议 | PASS | 真实同 PID 实测 `byte_equal=yes`、长度均 34；受限 PATH 仍相等；`2>/dev/null` 未吞退出码 |

验证：指定 pytest `37 passed, 10 warnings in 0.57s`；`bash -n`、`git diff --check` 通过。现有 37 项没有直接覆盖 shell `owner_token` 的信号继承场景。`graphiti-canvas` 本轮未暴露，不影响上述本地可复现反例。

**最终：BLOCKER/HIGH 未清零（1 BLOCKER、0 HIGH）；不可合入。**

---

# 附录 H — 第八轮处置记录（Claude, 2026-08-25）

- **门槛② 信号继承子项 → 已修**。owner_token 的 perl 包装在 exec 前：①`POSIX::sigprocmask(SIG_UNBLOCK, {ALRM})` 解除阻塞继承；②`$SIG{ALRM}=sub{}` 把 ALRM 置为 caught——按 POSIX exec 语义 caught 信号经 exec 重置为 SIG_DFL（仅 SIG_IGN 保持 ignore）→ exec 后 ALRM 必为可杀的默认处置，alarm(5) 有界终止不再依赖父环境。
- 实测：①round8 原反例（父 `trap '' ALRM` + 挂死替身 alarm 2）→ 2.0s 精确 KILLED（原来 6s 等替身自亡）；②父进程 sigprocmask BLOCK ALRM 场景 → 函数仍正常 fail-closed；③逐字节协议 BYTE-EQUAL 不变；④死 pid FAILS；⑤锁沙盒正常路径 RUNNER-RAN。

## 复验

37 passed；bash -n 通过。
