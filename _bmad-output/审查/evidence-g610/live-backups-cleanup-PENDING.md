# 待用户执行：清理本卡探测在 live `backups/` 留下的两个第三方缓存件

- **授权**：用户 2026-09-14 已答「删掉这两个残留（推荐）」。
- **阻断**：用户级 readonly guard hook（`~/.claude/guard-hook.sh`）拦下删除类命令；
  `~/.claude/readonly-guard.allow` 不存在，旁路**只能用户本人**开。
- **结论**：命令交用户本人跑。Claude **不**用 Python/其它途径绕过该守卫——那道守卫
  存在的意义就是「只有用户本人能动这些路径」，口头授权不改变这一点。

## 来源（如实）

验证 Codex r1 HIGH-1 的负控输入 `TMPDIR=<真 backups/>` 时，canary 的落盘守卫确实在
`mkdtemp` 之前就拒了（rc=2，一个 state 文件都没写），但**第三方 import 链**
（jieba / torch）抢在守卫之前按 `TMPDIR` 落了自己的缓存：

| 残留 | 大小 | 时刻 |
|---|---|---|
| `backups/jieba.cache` | 9.2 MB | 2026-09-14 22:57 |
| `backups/torchinductor_Heishing/` | 空目录 | 2026-09-14 22:57 |

探测前 `backups/` 有 **14** 项，探测后 **16** 项 —— 两者都是新增，非原有文件。

## 已修（代码侧）

`_assert_tempdir_anchor()` 前移到 `import app.*` 与 `mkdtemp` **之前**，顺序写进
`_run_inner` 的注释作为契约。复测同一负控输入：条目数 **16 → 16**，零写入。

## 待跑命令（用户在输入框以 `!` 前缀执行）

```
! /bin/rm -f /Users/Heishing/Desktop/canvas/canvas-learning-system/backups/jieba.cache && /bin/rmdir /Users/Heishing/Desktop/canvas/canvas-learning-system/backups/torchinductor_Heishing
```

跑完应回到 14 项。

## 其余 14 项本卡一个字节都没碰

```
com.canvas.daily-review.plist.pre-A3-20260825-034356
daily-review-wrapper.sh.pre-C1a-20260827-053723
daily-review.canvas-vault.state.json
daily-review.canvas-vault.state.lock
daily-review.log
daily-review.state.json.bak
daily-review.vault.state.json
daily-review.vault.state.lock
Dashboard.md.pre-A2-20260825-020229
fsrs_bridge.py.pre-C3-20260827-053749
learning_events.jsonl.pre-s1-cleanup-20260829-061014
memory-health.log
neo4j/
neo4j-s1-polluted-nodes-20260829-061014.txt
```

（`daily-review.canvas-vault.state.json` 的 mtime 仍是 09-14 09:06 = 现网复习链自己写的，
不是本卡；本卡的 state 写全部落在 `tempfile.mkdtemp()` 派生目录里。）
