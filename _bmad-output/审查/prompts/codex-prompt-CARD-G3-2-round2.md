# CARD-G3-2 对抗性审查 round-2（第八批 W7 · per-vault 复习事件账本 write-ahead 落地）

你是独立对抗审查者。这是第 **2** 轮；round-1 裁定「需整改」（3 BLOCKER + 3 HIGH + 3 MEDIUM + 1 LOW + 1 验证限制 + 1 环境误报），全部整改完毕，本轮专核整改与残留。

被审工作全部在这个 git worktree（未 commit 到主干）：

    WT=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w7-ledger

## round-1 一条 BLOCKER 的勘误

round-1 的 BLOCKER「`WT/_bmad-output/implementation-artifacts/goal-cards/第八批-goals/W7.md` ENOENT」是**环境误报**：卡文在编排 worktree，不在本车道。正确路径：
`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第八批-goals/W7.md`（只读）。

## 你只读以下文件

1. `WT/canvas-vault/.claude/skills/quiz-answer/SKILL.md` — 主写点（Step 4c 的主 PYEOF 块）
2. `WT/canvas-vault/.claude/scripts/fsrs_bridge.py`
3. `WT/backend/app/services/learning_event_log.py`
4. `WT/backend/tests/regression/test_g3_2_review_ledger.py` — 现 20 门
5. `WT/backend/tests/regression/test_learning_events_schema_contract.py` 的 `test_real_producer_quiz_answer_writer`
6. `WT/docs/learning-events-schema-v1.md` §6.1-§6.3（契约判据唯一真相源）
7. 上面的 W7.md 卡文路径（只读）

## round-1 发现 → 整改对照（逐条复核）

| # | round-1 发现 | 整改方式 |
|---|---|---|
| B-1 | 既有 pending 重放失败后仍追加 degraded 事件 | 重放循环失败即 `SystemExit` fail-closed 零写；删除 degraded 分支的 replay_failed 重置逻辑。degraded 落账仅当 pending 空或全部重放成功。新门⑰（含 pending 行 rating=1.5 变体）锁定 |
| B-2 | dup restore 重放失败仍发布 calibration → F1 把半态当完整应用 | 同上——重放失败在循环内直接退出，restore 到达时重放必然已成功；restore 分支 fsrs_ok 恒 True |
| B-3 | envelope 只比五局部字段 | restore 分支改为 **canonical envelope 全等比较**：`{event_version,event_type,node_id,effective_at,payload}` 双方 canonical JSON（sort_keys+separators），时刻字段采纳 durable 行，其余任何差异 fail-closed。门⑧补 exam_board 篡改 / event_version 篡改两变体 + 原样回写后 restore 成功对照 |
| H-1 | partial-JSON 短写在 LF 守卫前退出，自愈不可达 | 账本读取区分：**最后一行**解析失败 = 截断尾行 → 跳过+stdout 留痕（不阻塞）；**中间行**坏 = fail-closed。追加前 LF 守卫照旧隔离。门⑦改用真实 partial JSON（`{"event_id"...截断`）+ 校验器如实报坏行 |
| H-2 | append_event 坏尾行 continue 后连坐拼接 | append_event 查重循环坏行留 warning；追加前 LF 守卫（补 `\n` 隔离）。新门⑳：partial 尾行后 append_event → 新行独立可解析 + 幂等不破坏 |
| H-3 | degraded 本地 A3 推进缺 A7 上界 | degraded 分支 bump 后查 `>= 9000-01-01Z` → SystemExit 零写。新门⑱：W=8999-12-31T23:59:59Z + 同秒 + REEXEC 阻断 → 零写 |
| M-1 | 显式 rating int() 强转静默收非法值 | bridge 改严格 `isinstance(rating, int)`（bool 显式排除）；门⑰变体验证 rating=1.5 的 pending 行被拒 |
| M-2 | 单写者未明示 +「并发」措辞误导 | 静态块头注声明单写者前提（G3-3 前无锁）；`_again` 分支改「防御性二次查重（单写者下不可达）」 |
| M-3 | 门⑯陷阱杀不掉旧子串实现 | 陷阱改 **ASCII event_id + payload 键名载体**（键名引号不转义）；门内含验伪断言 `trap_needle in line_text`。注意：首版「值内嵌引号」陷阱被该验伪断言自己抓出（值内引号恒转义 `\\"`，needle 尾引号匹配不上）——这正是验伪断言的价值 |
| M-4 | fixture 声称 tmp candidate 实际命中 WT venv | fixture docstring 如实改写：bridge symlink resolve 穿回 WT，re-exec 命中 WT venv（同一解释器，结果等价）；tmp 目录 symlink 不参与选路（保留理由写明） |
| LOW | fixture 无既存 calibration_log（live 规范化形态） | 新门⑲：写入成功 → 模拟 Obsidian 剥引号 → 重跑必须「幂等跳过」零写（解析层 F1 在裸词形态命中——旧 json.dumps 子串守卫在此形态恒不命中的 live 实证缺陷被正面覆盖） |
| 限制 | spy dir_count≥2 未绑定 inode | 门⑬补：dir fsync inode 集合 ⊇ {VAULT 根 inode, 节点父目录 inode} |
| B-4(误报) | 卡文 ENOENT | 本轮已给正确路径（见上） |

## 本轮审查要求

1. **逐条复核上表**：整改是否真的落地（引用整改后代码行），有没有改出新问题。
2. **重点扫整改的连带面**：B-1 的 fail-closed 退出发生在什么阶段？（append 前/发布前）是否存在「重放失败已退出但部分写入已发生」的窗口？B-3 的 canonical envelope 比较在「合法 restore」路径上会不会误拒（保守误拒口径 §6.2:186）？
3. **正常路径回归**：门①-⑳ 有没有哪个被整改改坏（你有 worktree 只读权，可运行 pytest 定向验证）。
4. 六项审查重点（写序真 write-ahead / A2 不重复应用 / 查重正确 / 哨兵成对 / G3-3 边界诚实 / fixture 同源）给出最终结论。

## 输出格式

逐条 finding：

    [BLOCKER|HIGH|MEDIUM|LOW] <文件>:<函数或行> — <问题一句话>
    依据: <引用契约条款或代码原文>
    建议: <一句话>

最后一行给总裁定：`VERDICT: PASS` 或 `VERDICT: 需整改`。没有 finding 的项写「未发现」。
