# readonly-path-guard — 本会话真实拦截记录（2026-09-14 16:02 本地）

> 接线动作：`~/.claude/settings.json` PreToolUse 追加两条（见 `settings-wiring-20260914T155608.txt`）。
> 预期：hooks 在会话启动时快照 → 本会话不拦。**实测：立即生效，直接拦下。**

## 被拦命令（主 session 发出，设计为无害：`cp` 到 /dev/null）

```
cp "/Users/Heishing/Desktop/spring course 2026/CS 61B/14-scheme-a-implementation-prd.md" /dev/null
```

## 主 session 收到的 hook 错误（逐字）

```
PreToolUse:Bash hook error: [bash ~/.claude/hook-trace.sh node ~/.claude/readonly-path-guard.js]: [readonly-path-guard R1] PRD 锚定文档只读，命令含写入迹象：/Users/Heishing/Desktop/spring course 2026/CS 61B/14-scheme-a-implementation-prd.md
这是 CLAUDE.md「只读锚定」的真实执行层。若确需写入：由用户本人在 Claude 之外的终端执行 `touch /Users/Heishing/.claude/readonly-guard.allow`（20 分钟窗口），Claude 不得自行创建该文件。
```

## 判读

- 规则 R1 命中：命令同时含 PRD 路径与写迹象 token `cp`。这是**设计内的保守误拦**（`cp … /dev/null` 实际是读）——读 PRD 请用 `cat` / `head` / `sed -n` / `grep`，不要用 `cp`/`tee`。
- 整条 Bash 未执行 → 原计划写入的 `live-session-check-*.txt` 不存在，本文件替代。
- 结论：用户级 hook 对**运行中的会话立即生效**，无需重启（与 Claude Code「hooks 快照」的一般说法不同；以本次实测为准）。

rc=2（hook 阻断）

---

## 追记 16:03 — 收窄版守卫（sha256 `c05f03d1…`，单测 8/8）重装后的本会话实测

- `cp "<PRD>" /dev/null`（PRD 仅作源）→ **放行**，`cp rc=0`，PRD sha256 `1ef5f0be…` 不变（`live-session-check-refined-20260914T160330.txt`）。
- `/Applications/Obsidian.app/Contents/MacOS/obsidian-cli vault=0a302bd176301457 eval code=1` → **被拦**，主 session 收到：

```
PreToolUse:Bash hook error: [bash ~/.claude/hook-trace.sh node ~/.claude/readonly-path-guard.js]: [readonly-path-guard R3] Obsidian CLI 写/执行子命令被拦：eval
```

- 审计日志 `~/.claude/hook-audit.jsonl` 含 164 条 `readonly-path-guard` 记录（其中已有其它会话 `cbd47163…`、batch-14 会话经过并放行的条目）。

rc=2（R3 阻断，符合预期）
