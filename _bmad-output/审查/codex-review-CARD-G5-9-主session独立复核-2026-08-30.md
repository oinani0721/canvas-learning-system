# Codex 独立复核存档 — CARD-G5-9（主 session 并行复核）

> ⚠️ **本文件是从一次跨 session 文件写入碰撞中恢复出来的**，见同目录
> `codex-review-CARD-G5-9.md` 头部的「碰撞事故说明」。
>
> **来源**: 非 T2 车道产出——本批 T2（CARD-收口A）在 `card/s6-recap` 跑自己的 G5-9 复核期间，
> 另有一个 session（据 trunk 提交 `a9c8b97c docs: update T2 closeout goal with G5-9 review findings`
> 推断为主 session）**并行**对同一 commit `4717a2cd` 做了独立复核，并写入**同一个文件路径**。
> 两个进程各持一个 fd 写同一文件，字节按各自 offset 交错落盘，产生了拼接损坏文件。
>
> **恢复方式**: 损坏文件的字节 `0..9890` 恰为本报告全文（结尾语完整，未截断），逐字节切出，
> 未做任何删改。字节 `9890..16075` 是 T2 车道那份报告的尾段，已由其 transcript 原件重建。
>
> **恢复者**: T2 车道（CARD-收口A ③）· 2026-08-30
> **⛔ 本报告不是 T2 车道的产出，T2 只负责把它完整保存下来并如实转达其发现。**

---

结论：**FAIL，不建议合并 `4717a2cd`。**

发现统计：**BLOCKER 2 / HIGH 4 / MEDIUM 5 / LOW 1**。  
**BLOCKER/HIGH 清零: 否。**

## Findings

1. **BLOCKER / FAIL — 空 SHA 可绕过确认门，未确认也能写入**

   [recap_exam_build.py:484](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:484) 仅在 `expect_content_sha` 为 truthy 时比较；`required=True` 只要求参数出现。真实 CLI 传 `--expect-content-sha ''`，exit 0 且 `created:true`。测试只覆盖“完全省略参数”：[test_g5_9_recap_exam.py:519](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/backend/tests/skills/test_g5_9_recap_exam.py:519)。

   这直接否定“无确认 SHA 即零写侧”。而且 SHA 本身只绑定内容，不是用户确认凭据。

2. **BLOCKER / FAIL — DD-14 追踪链不合规**

   硬规则要求提交含 `PLAN-NNN`：[CLAUDE.md:8](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/CLAUDE.md:8)。目标提交标题只有 `CARD-G5-9`，没有 `PLAN-NNN`；[CURRENT_TASK.md:5](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/CURRENT_TASK.md:5) 仍声明分支 `card/n5-split`，不是当前 `card/s6-recap`。按仓库原文，这是阻断项。

3. **HIGH / FAIL — 回执 SHA 没有绑定最终发布字节**

   [recap_exam_build.py:309](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:309) 写并 fsync 后，只在 [recap_exam_build.py:319](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:319) 按路径 link 并核 inode，没有 same-FD readback hash，也不复算发布目标。并发原地改写同一 tmp inode 时，实测仍返回 `created:true`，但回执 SHA `aa89ab…`、目标 SHA `1f6041…`。

4. **HIGH / FAIL — 父目录 symlink 仍有 check/use 窗口，可写出 vault**

   目录 containment 在 [recap_exam_build.py:357](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:357) 检查，symlink probe 在 [recap_exam_build.py:507](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:507)，实际 `open/link` 仍使用路径，没有可信 `dir_fd`。在 probe 后替换 `检验白板/` 为外部目录 symlink，实测 `created:true`，文件出现在 vault 外。

5. **HIGH / FAIL — undo 校验与最终删除没有原子绑定**

   - [recap_exam_build.py:556](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:556) 先解析 leaf symlink，再执行 `O_NOFOLLOW`；实测传入同目录 alias，回执称移除 alias，实际移走 referent、留下 dangling symlink。
   - [recap_exam_build.py:689](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:689) 最终复核后关闭 FD，到 [recap_exam_build.py:721](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:721) 才按路径 unlink。其间到达的用户编辑实测被删除，留痕中只有旧字节。

6. **HIGH / FAIL — 不是忠实复用 start-exam-board，而是自造第二套 schema**

   生成器在 [recap_exam_build.py:175](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:175) 使用 `status: done`、`recap_kind`、`recap_boards`，并省略 `selected_node/questions`。原模板 [start-exam-board/SKILL.md:383](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/start-exam-board/SKILL.md:383) 明确要求 `in_progress`、`selected_node`、`questions[0]` 等。

   测试反而锁定新 subtype：[test_g5_9_recap_exam.py:689](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/backend/tests/skills/test_g5_9_recap_exam.py:689)，并迫使范围外的 [quiz-answer/SKILL.md:87](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/quiz-answer/SKILL.md:87) 与 [Dashboard.md:436](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/Dashboard.md:436) 增加特判。总账还明确记载该 frontmatter 形状需用户拍板：[总账:471](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/_bmad-output/implementation-artifacts/goal-cards/2026-08-27-主goal全量分goal总账.md:471)。

7. **MEDIUM / FAIL — Unicode 控制字符破坏消费兼容**

   板名过滤只拒绝少数字符：[recap_exam_build.py:383](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:383)。实测：

   - 含 U+007F：create 成功，但 `scan_vault` 对原板与产物均报 `file_parse_failed`。
   - 含 U+0085：`parse_errors=[]`，但 `exam_history.board_id=null`。

   中文、空格、括号和 `&` 的常规样例通过；控制字符及 Unicode 归一化没有锁定。

8. **MEDIUM / FAIL — `undo_hint` 不是可直接执行的命令**

   [recap_exam_build.py:526](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:526) 生成的 hint 从 `undo --vault ...` 开始，缺少 `python3 .../recap_exam_build.py`。原样执行实测 exit 127：`command not found: undo`。测试 [test_g5_9_recap_exam.py:580](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/backend/tests/skills/test_g5_9_recap_exam.py:580) 只做 `shlex.split`，没有执行。

9. **MEDIUM / PARTIAL — 多项安全测试是假绿或只测前提**

   - tmp symlink/普通文件测试在 [test_g5_9_recap_exam.py:360](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/backend/tests/skills/test_g5_9_recap_exam.py:360) 没传必填 SHA，实际因 argparse 提前 exit 2，未到 symlink 防线。
   - “replaced inode”测试 [test_g5_9_recap_exam.py:602](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/backend/tests/skills/test_g5_9_recap_exam.py:602) 没有替换 inode。
   - 防嵌套测试 [test_g5_9_recap_exam.py:227](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/backend/tests/skills/test_g5_9_recap_exam.py:227) 只断言生产者输出的两个字符串/路径前提，不锁真实 start-exam-board Step 1。

10. **MEDIUM / FAIL — undo 指纹不是结构化 provenance**

    [recap_exam_build.py:607](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:607) 只检查任意位置是否包含 `GENERATED_BY` 字节串。手工文件只要正文出现该字符串并提供当前 SHA，也会被 undo 接纳。

11. **MEDIUM / FAIL — 跨板共享节点的批注被重复计数**

    成员总数在 [recap_exam_build.py:168](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:168) 去重，但批注仍在 [recap_exam_build.py:174](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:174) 按板相加。两板共享一个含 1 条批注的节点，实测输出“总成员 1 / 总批注 2”。

12. **LOW / PARTIAL — 缺失 `检验白板/` 时 undo 不回目录拓扑基线**

    create 会在 [recap_exam_build.py:503](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:503) 建目录，undo 只删文件。基线无该目录时，create→undo 后空目录残留；fixture 总是预建目录且 snapshot 只哈希普通文件：[test_g5_9_recap_exam.py:65](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/backend/tests/skills/test_g5_9_recap_exam.py:65)。

## 五项消费面与边界

| 判据 | 当前行为 | 测试锁定 |
|---|---|---|
| `board_manifest` 0 parse errors | 常规板名 PASS；控制字符 FAIL | PARTIAL，仅直调 `scan_vault` |
| `exam_history.question_count=0` | PASS | PASS，仍未覆盖生产投影链 |
| `past_question_digests` 零新增 | PASS | PASS，fixture 为全空基线 |
| start-exam-board 防嵌套 | 静态规则存在 | PARTIAL，未锁真实 Skill 入口 |
| frontmatter 无 `concept:` 行 | PASS | PASS |
| 忠实复用既有模板 | **FAIL** | 测试锁的是新 subtype |
| G5-4 signals 边界 | **PASS**：`recap_scan.py` 与 signals 测试相对父提交零 diff | 两个额外生产消费文件越出题面三交付物范围 |

验证结果：目标测试 **33 passed**；`ruff --no-cache` PASS；`git diff --check` PASS。未跑全量 CI，未执行真实 Claudian Skill；Graphiti MCP 本轮未暴露。仓库未被修改，原有未跟踪审查文件保持不动。

本轮只借用了历史审计规程，所有事实与高严重度反例均已在 `4717a2cd` 上重新验证。


