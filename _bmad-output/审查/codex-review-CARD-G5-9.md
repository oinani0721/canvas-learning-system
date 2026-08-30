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


��。**  
   后端 [board_manifest_service.py:681-700](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/backend/app/services/board_manifest_service.py:681) 完全不看 `recap_kind`，并在 `:843-845` 把阶段回顾板计入 `exam_board_count`；API/Snapshot 模型也没有该字段。隔离实测创建前后：

   - `parse_errors: 0 → 0`
   - `digests: 1 → 1`
   - `exam_history: 1 → 2`
   - 锚板 `exam_board_count: 0 → 1`

   所以 manifest 的窄兼容判据确实通过，但 `/board-recap` 的“检验历史 N 板”、`ai-linked-doc` 的板统计及 start-exam-board 的板级历史仍会把阶段板视作普通检验历史。Dashboard 的过滤当前正确。

6. **消费面证据多为必要前提/静态文本，不是端到端执行证据。**  
   `board_manifest_service.scan_vault`：PASS，已独立实跑。  
   start-exam-board：PARTIAL，仅检查产物的 type/path；未执行消费者拒绝分支。  
   quiz-answer：PARTIAL，仅检查 status/无答题区和 SKILL 字符串；未驱动 done 或无参定位流程。  
   Dashboard：静态 PASS，[Dashboard.md:440-442](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/Dashboard.md:440) 确实读取该键，但未在 Obsidian/Dataview 运行时执行。

7. **`undo_hint` 不能原样执行。**  
   [SKILL.md:382-386](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/SKILL.md:382) 称其“可直接复制执行”；实现 [recap_exam_build.py:526-529](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:526) 只输出 `undo --vault ...`，缺少 `python3 <script>` 前缀。参数 quoting 正确，但普通 zsh 中 `undo` 不存在。

8. **C1/C2/C3 触发与范围解析未闭合。**  
   第二刀称覆盖 C1/C2/C3，但 [SKILL.md:97-100](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/SKILL.md:97) 的 CRITICAL TRIGGER 仍只有 `/board-recap`；[skill_trigger_matrix.yaml:128-151](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/backend/tests/regression/skill_trigger_matrix.yaml:128) 三条仍是 `planned-extension / trigger_today:false`。C1/C2 没给板名，而脚本 [recap_exam_build.py:752-757](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:752) 强制 `--boards`，SKILL 没有章节/阶段到板集合的解析步骤。当前完整的是“已进入 skill 且显式列板”的 C3-like 路径。

## LOW 发现

1. **UAT 测试数陈旧。**  
   [UAT:31](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/_bmad-output/验收单/UAT-CARD-G5-9-阶段回顾检验白板-2026-08-28.md:31) 和 `:61` 写 31；目标 commit 实际收集 **33 tests，33 passed**。这是低估，不是假绿。

2. **拒绝文档枚举/返回形态不完整。**  
   实现拒绝 `# | ^ [ ]`，SKILL `:374/:415` 只列 `# | ^`；这些字符实际返回 `{"error": ...}` + exit 2，不是文档所说的 `refusal_reason`。安全行为更强，属于文档漂移。

## 其余逐项判定

### preview 与零正文复制

- 正式 CLI preview 的 `sys.dont_write_bytecode` 保护有效；在无既有 pycache 的 `/tmp` vault 中，文件数 `65 → 65`、SHA diff 为 0、新 pyc 为 0。
- 当前 `_render_content` 没接收原板/节点正文、标题、callout 或题干字段；只接收板 stem、节点 ID、计数、ghost 标识及固定模板。未找到原节点/原板 prose 正文字节进入输出的反例。
- ghost ID 是明确要求展示的链接标识，anchor 是 CLI stem；二者不构成原板标题或节点定义正文复制。
- 现有测试只用节点正文哨兵，覆盖面偏窄；此处 PASS 主要来自静态数据流核对。

### 时间戳、幽灵链接

- `datetime.strptime` 真校验日历时刻，默认使用 `datetime.now(timezone.utc)`：PASS。
- 静态传入的显式 `--ts` 是否真来自 UTC 只能靠 SKILL 的 `date -u` 约定，脚本无法从无时区字符串自行证明。
- 幽灵链接不计入 members、不输出死 wikilink、单列待修段：PASS。

### UAT 与证据包

- 证据包内部：baseline、两组 preview、两组 undo 均为 69 行且逐字节相同；两份 after-create 均恰多 1 行；preview content 的独立 SHA 与 create/undo 回执一致。
- `/tmp` 隔离链复现了 `69 → 70 → 69` 和留痕 SHA 全等。
- `g2-manifest-compat.txt` 的 `0 parse_errors / question_count=0 / digests 零新增` 属实，但只是窄判据。
- [UAT:71-76](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/_bmad-output/验收单/UAT-CARD-G5-9-阶段回顾检验白板-2026-08-28.md:71) 清楚声明 D5 用户 UAT 未发生、live 验证顺延 G5-11；该边界诚实。

## 未验证与审计完整性说明

- 未访问或写入主仓 live vault。
- 未运行 Obsidian/Dataview UI，也未真实驱动 LLM 执行 start-exam-board/quiz-answer；这些面按 PARTIAL 报告。
- 未做真实断电测试；fsync/崩溃结论来自静态路径和 `/tmp` 故障注入。
- 只运行目标 33 项测试，不宣称全仓 CI 通过。
- Graphiti 工具本会话不可用，未执行记忆写入。
- 审计过程中一名并行代理误用 `importlib` 直接加载了工作树脚本 5 次，改写了一个既有、被 `.gitignore` 忽略的 `canvas-vault/.claude/skills/board-recap/scripts/__pycache__/recap_exam_build.cpython-314.pyc`。baseline SHA 为 `22071dd5…ec57`，当前为 `37f08224…fc9d`。我没有恢复或删除它；tracked diff 仍为 clean，live vault 未触碰。因该审计自身偏差，当前工作树只能确认 baseline **68/69**，不能再宣称当前 69 文件逐字节等于原证据。

## 残留清单

- **BLOCKER：0**
- **HIGH：4**
- **MEDIUM：8**
- **LOW：2**

最终裁决：**CARD-G5-9 需再一轮。**
