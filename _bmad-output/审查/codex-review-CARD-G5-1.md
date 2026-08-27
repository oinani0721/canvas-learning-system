整体裁决：**不通过（BLOCKER）**。

审查基线：`card/n5-split @ b47ebfba351f3eedb496a97961083c5e3b1d5df7`。当前 `9/9`、`12/12` 的绿灯都可重放，但只能说明“当前样本通过现有弱判据”，不能证明 CARD-G5-1 的验收目标成立。

## BLOCKER

1. **[FAIL] 每类 ≥3 条“真实正例”未满足**

   卡片要求“采集用户真实触发语句”“四类各 ≥3 条真实正例” [goal-card:405-409](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/_bmad-output/implementation-artifacts/goal-cards/2026-08-27-主goal全量分goal总账.md:405)。当前 YAML 分布是：

   - 拆分收集：2 verbatim + 2 constructed
   - 单板回顾：2 constructed + 1 paraphrase
   - 阶段回顾：2 paraphrase + 1 constructed
   - 待处理：1 doc-demo + 1 constructed + 1 错标 paraphrase

   即使把所有合格 paraphrase 都算“真实场景”，四类仍都不足 3 条。T1 只数 `polarity: positive`，constructed 也能填满配额 [checker:170-175](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/backend/scripts/check_skill_trigger_matrix.py:170)。

2. **[FAIL] 当前语料标注已有 3 条身份不实**

   “逐字”被定义为用户原话，“语境改写”须来自真实语料/场景 [矩阵:31-38](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/_bmad-output/研究/2026-08-27-G5-1-信息收集四类触发矩阵.md:31)。

   - N2 被标为用户逐字 [YAML:150-157](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/backend/tests/regression/skill_trigger_matrix.yaml:150)，但出处只是作者说明“说一句「导出思维导图」”，不能证明用户说过 [报告:71-73](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/_bmad-output/研究/语料快照-G5-1/2026-08-16-学生使用场景报告-深度学习与搜集调研的完整旅程.md:71)。
   - D3、N7 标为 paraphrase [YAML:132-139](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/backend/tests/regression/skill_trigger_matrix.yaml:132)、[YAML:190-197](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/backend/tests/regression/skill_trigger_matrix.yaml:190)，但引用的是明确处于设计态的作者流程稿 [R8:7](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/_bmad-output/研究/语料快照-G5-1/2026-08-16-批注回复-R8-清待处理skill详细使用流程.md:7)、[R8:24](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/_bmad-output/研究/语料快照-G5-1/2026-08-16-批注回复-R8-清待处理skill详细使用流程.md:24)、[R8:39](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/_bmad-output/研究/语料快照-G5-1/2026-08-16-批注回复-R8-清待处理skill详细使用流程.md:39)。
   - 特别核对的 D1 标注正确：R8 明确是“真实对话演示”章节中的作者构造 [R8:92-95](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/_bmad-output/研究/语料快照-G5-1/2026-08-16-批注回复-R8-清待处理skill详细使用流程.md:92)，矩阵如实标了 `doc-demo` [矩阵:82](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/_bmad-output/研究/2026-08-27-G5-1-信息收集四类触发矩阵.md:82)。

   23 条逐项结果：**19 PASS / 1 PARTIAL（B3 锚点不完整）/ 3 FAIL**。

3. **[FAIL] 负例裁判可把未执行或损坏日志判成“零 Skill 调用”**

   裁判静默跳过坏 JSON，只解析 `assistant.message.content[].tool_use` [judge:37-57](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/_bmad-output/审查/g5-1-evidence/judge_headless_logs.py:37)，又不要求 `init`、`result success` 或完整终止 [judge:65-83](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/_bmad-output/审查/g5-1-evidence/judge_headless_logs.py:65)；runner 还容忍 Claude 非零退出 [runner:48-50](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/_bmad-output/审查/g5-1-evidence/run_headless_negatives.sh:48)。

   实测向 `parse_log()` 输入坏 JSON 加真实 `user.tool_use_result.commandName=board-recap` 形状，返回：

   ```text
   {'uses': [], 'init_tools': [], 'last_text': ''}
   ```

   该被忽略形状在实际 B2 日志中存在 [B2.jsonl:6](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/_bmad-output/审查/g5-1-evidence/logs/B2.jsonl:6)。此外 judge 只从 TSV 读取 ID，不核 utterance、session、cwd 或成功结果 [judge:144-155](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/_bmad-output/审查/g5-1-evidence/judge_headless_logs.py:144)。复用同一份干净日志和相等 manifest 即可伪造 N1–N10 全绿。

## HIGH

1. **[FAIL] T7 的逐字、行号、paraphrase 和快照完整性均可绕过**

   - `verbatim` 与 `doc-demo` 走完全相同的子串判断 [checker:272-277](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/backend/scripts/check_skill_trigger_matrix.py:272)；D1 改成 `verbatim` 仍 `9/9 PASS`。
   - `norm()` 删除全部空白 [checker:99-101](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/backend/scripts/check_skill_trigger_matrix.py:99)；“导 出 思 维 导 图”仍被判逐字。
   - `line: -10` 会将窗口扩成近乎全文；仍 PASS。
   - paraphrase 分支完全不使用声明行号，也不验证语义关系 [checker:278-281](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/backend/scripts/check_skill_trigger_matrix.py:278)。
   - checker 只读取快照，不核原件路径或 SHA [checker:255-260](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/backend/scripts/check_skill_trigger_matrix.py:255)；追加字节改变 SHA 后仍全绿。

2. **[FAIL] T8 不能防文档/YAML 漂移**

   T8 只要求每条 utterance 在文档任意位置出现，不比较 ID、分类、skill、状态、`trigger_today`、来源、理由或 `headless`，也不做文档→YAML 反向检查 [checker:284-296](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/backend/scripts/check_skill_trigger_matrix.py:284)。

   隔离反例中，单边把 D1“今日触发”从否改是、从 YAML 删除 A4 但保留文档行、或只改来源类型，均仍 `9/9 PASS`。因此矩阵宣称“T8 会强制同步” [矩阵:120-121](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/_bmad-output/研究/2026-08-27-G5-1-信息收集四类触发矩阵.md:120)不成立。

3. **[FAIL] 正例工作流指纹过松，且 B1 精确输入已漂移**

   YAML B1 是 `/board-recap CS188 lecture 2` [YAML:62-69](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/backend/tests/regression/skill_trigger_matrix.yaml:62)，实际 runner/README 的 B1 却是“特征值与特征向量” [runner:39](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/_bmad-output/审查/g5-1-evidence/run_headless_positives.sh:39)、[README:15](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/_bmad-output/审查/g5-1-evidence/README.md:15)。

   judge 只要任意 tool input 含 `.claude/skills/board-recap/` 就算触发 [judge:85-98](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/_bmad-output/审查/g5-1-evidence/judge_headless_logs.py:85)；普通 `Read` 该目录文件即可命中，不要求命令成功或 `VERIFY PASS`。正例任意 manifest 变化也不会失败 [judge:116-133](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/_bmad-output/审查/g5-1-evidence/judge_headless_logs.py:116)。

4. **[FAIL] T0–T2 允许回归集合静默退化**

   T0 不验 polarity 枚举、非空文本、布尔类型或正整数行号 [checker:139-161](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/backend/scripts/check_skill_trigger_matrix.py:139)。实测非法 polarity、字符串型 `trigger_today`、重复 category、10 条完全相同负例均能保持全绿。把某负例 polarity 改成 typo 后，runner 会直接跳过该条。

## MEDIUM / LOW

- **MEDIUM · PARTIAL**：manifest 仅统计 `find ... -type f` [runner:24-31](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/_bmad-output/审查/g5-1-evidence/run_headless_negatives.sh:24)，新增目录、symlink、FIFO/socket 不会被发现。实际 N9 还写了未测量的 `/tmp/lec2.txt` [N9.jsonl:32](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/_bmad-output/审查/g5-1-evidence/logs/N9.jsonl:32)。`.claude/` 排除则在 runner 和 README 中如实披露，**该点 PASS** [README:30-33](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/_bmad-output/审查/g5-1-evidence/README.md:30)。

- **MEDIUM · PARTIAL**：目标 checker 的 T3 不像对照 checker C0 那样拒绝额外 live skill；T4 的 `description:` regex 也未限定 frontmatter [checker:51-96](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/backend/scripts/check_skill_trigger_matrix.py:51)、[routing-checker:231-242](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/backend/scripts/check_skill_routing_block.py:231)。

- **LOW · PASS WITH LIMIT**：两份快照与相邻 worktree 当前原件确实 `cmp=0`：

  - 报告：`b62c6ba1946ddd296c9680bc460bad63c3cb281af17eab9256bd9bc5f97f4734`
  - R8：`9bad2e2a8ee8136b6d0e8a29689e28f53f1d301512cbec6714731fa62b667823`

  但两份“原件”都是未跟踪文件，只能证明审计时当前字节相等，不能证明不可变来源链。

## 独立复算的反证面

当前产物并非全部伪造：

- trigger checker：`9/9 PASS`；routing checker：`66/66 PASS`。
- judge：可重放出与 [final-verdict:1-38](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/_bmad-output/审查/g5-1-evidence/final-verdict.txt:1)相同的 `12/12 PASS`。
- 12 份 JSONL 当前均合法、session 独立且有 `result success`；当前 N1–N10 中确实未找到 `Skill`/`commandName`。
- 10 组普通文件 manifest 均为 28 条，before/after 相等。
- B1 当前确实运行到 `VERIFY PASS` [B1.jsonl:47-48](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/_bmad-output/审查/g5-1-evidence/logs/B1.jsonl:47)，且人工复核只新增三份 outputs 文件 [B1-diff:2-4](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/_bmad-output/审查/g5-1-evidence/manifests/B1-content-diff.txt:2)。

所以准确状态是：**观察样本局部 PASS；语料真实性、同步控制和机械证据闭环 FAIL；CARD-G5-1 不可验收。**

本轮只读，未修改目标文件；审查期间并发出现的 `CURRENT_TASK.md`/G5-2 改动已排除。Graphiti MCP 本会话不可用，未写入审查记忆。


