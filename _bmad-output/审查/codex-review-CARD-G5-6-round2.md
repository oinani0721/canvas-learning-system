结论：当前 HEAD `87454e2327ffebf1bc934e30b3df0b898f157d2a` 下，9 条中仅 4 条真实闭合；B3、H1、H2、H3、H4 仍可由真实 CLI/产物路径复现。

| 项 | 判定 | 当前证据与回归门 |
|---|---|---|
| B1 | `CONFIRMED-CLOSED` | [inbox_preview.py:130](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:130) 在真实 `exec_module` 前设置 `sys.dont_write_bytecode=True`，`:151-152` 用 `finally` 恢复。隔离树中合法 CLI 与非法参数拒绝路径均未在 clear-inbox/board-split 生成缓存。回归门 [test:690](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/backend/tests/skills/test_g5_6_clear_inbox.py:690) 有效；移除临时副本中的 guard 后该门准确失败并发现 board-split `.pyc`。 |
| B2 | `CONFIRMED-CLOSED` | [inbox_preview.py:466](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:466) 的 `dup_body()` 只做 `rstrip()`，保留行首缩进；C3 另由 `has_substantive_content()` 处理。回归门 [test:431](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/backend/tests/skills/test_g5_6_clear_inbox.py:431) 经真实 CLI 同时断言“不建议删”及 `exact_duplicate_of is None`，有效。 |
| B3 | `STILL-OPEN` | 已有状态机在 [inbox_preview.py:419](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:419)，但 `:434-443` 只记围栏字符、不记开启长度。真实反例“四反引号开启、三反引号内容行、`# keep`、四反引号关闭”仍输出 `C3_empty_or_skeleton / 建议删`。现有 [test:456](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/backend/tests/skills/test_g5_6_clear_inbox.py:456) 仅覆盖三波浪线，门存在但不足。 |
| H1 | `STILL-OPEN` | [inbox_preview.py:296](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:296) 的正则仍接受 `https://:443/x`；该 URL 实际 `hostname=None`，真实 CLI 却产出 `C1_source_url / primary-record`。现有 [test:478](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/backend/tests/skills/test_g5_6_clear_inbox.py:478) 只测 `https://?`，未证明 host 存在。 |
| H2 | `STILL-OPEN` | 标记表 [inbox_preview.py:196](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:196) 仍含 `AI 生成`，而 [find_ai_marker:534](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:534) 只做子串匹配。手写标题 `# AI 生成内容的版权问题` 被真实 CLI 判为 AI 自述并归档。现有 [test:492](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/backend/tests/skills/test_g5_6_clear_inbox.py:492) 的负例不包含任何剩余 marker，覆盖不足。 |
| H3 | `STILL-OPEN` | [inbox_preview.py:294](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:294) 把普通 URL 的 `http:` 误认成 YAML key。真实输入 `--- / http://example.com/path / ---` 被全部吞作 frontmatter，输出 `C3_empty_or_skeleton / 建议删 / confident=true`。现有 [test:514](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/backend/tests/skills/test_g5_6_clear_inbox.py:514) 只覆盖无冒号正文。 |
| H4 | `STILL-OPEN` | [inbox_preview.py:795](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:795) 的 basis/conflict 虽声明“正本不可判”，但人读产物 [render_md:1253](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:1253) 仍输出“正本 `<字典序首项>`；另有副本…”，与自身声明直接矛盾。现有 [test:526](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/backend/tests/skills/test_g5_6_clear_inbox.py:526) 只验 JSON 局部，不检查 MD。 |
| H5 | `CONFIRMED-CLOSED` | [inbox_preview.py:1397](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:1397) 在构建和发布前用 `realpath` 拒绝 out-dir 等于或位于 inbox 下。回归门 [test:711](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/backend/tests/skills/test_g5_6_clear_inbox.py:711) 有效断言非零退出、目录未创建、严格零产物。 |
| H6 | `CONFIRMED-CLOSED` | [test:690](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/backend/tests/skills/test_g5_6_clear_inbox.py:690) 先清缓存，再经 subprocess 运行真实生产入口，并同时检查两个 scripts 目录；去掉生产 guard 后该门翻红，证明不是假绿。 |

验证边界：

- 字节相同的隔离副本运行指定单文件：`55 passed in 2.79s`。
- 未在原工作树直接跑，因为测试 `:699-700` 会删除审计开始前已存在的 ignored `board-split/scripts/__pycache__`；该缓存及未跟踪 round‑2 报告均原样保留。
- tracked 审计对象相对 HEAD 无 diff；未跑全量 CI。
- Graphiti 工具本轮未挂载，无法执行项目事实搜索。

**BLOCKER/HIGH 清零: 否**


