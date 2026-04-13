---
story_id: "4.5"
epic_id: "4"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P0"
estimate_hours: 8
depends_on: ["4.3"]
blocks: ["4.6", "4.7", "4.8"]
trace:
  - "FR-EXAM-05"
---

# Story 4.5: MD 编辑器答题 + 手动提交（D14 用户哲学锁定）

Status: ready-for-dev

## Story
As a 学习者,
I want 在 markdown 编辑器中手写答案并手动提交,
So that 答题过程就像写批注（D14 用户原话："这样回答问题就好比打批注"）。

## Acceptance Criteria

1. **Given** Story 4.3 生成题目完成 **When** skill Edit exam_boards/*.md **Then** 在 body 末尾追加 `[!exam_question]+` callout 格式：
   ```markdown
   > [!exam_question]+ Q{i} · {concept}
   > {question_text}
   >
   > 答：
   > (在这里写你的回答)
   ```
   **And** callout 的 "+" 标记保证默认展开 **And** Obsidian 自动重新渲染，用户立即看到新题目

2. **Given** 题目 callout 已追加 **When** 学习者在 md 编辑器中写答案 **Then** 学习者可以在 `> 答：` 下方自由编写 **And** 支持反复修改（删除重写、追加内容）**And** 所有修改实时保存在 exam_boards/*.md 中

3. **Given** 学习者完成答案编写 **When** 按下 Cmd+Option+S (Submit) **Then** 触发 `/quiz_answer` sub-skill **And** 提交是手动触发（非文件监听自动触发）**And** 避免思考中被误触发

4. **Given** `/quiz_answer` sub-skill 被触发 **When** sub-skill 读取当前 exam_boards/*.md **Then** 用正则匹配最后一个 `[!exam_question]+` callout **And** 提取 `> 答：` 下方所有连续 `> ` 开头的行作为答案 **And** 过滤占位符"(在这里写你的回答)"——如果答案仍为占位符则提示"请先写答案"

5. **Given** 答案提取成功 **When** sub-skill 准备调用 score_answer **Then** 将 question_id 和 answer_text 传递给 Story 4.6 的评分流程 **And** 更新 frontmatter questions[].user_answer 字段

6. **Given** 答题过程中 **When** AI sidebar 显示内容 **Then** sidebar 不显示题目文本、分数、提示、参考答案等任何实质学习内容 **And** sidebar 仅显示 skill 状态指示（"等待答题"/"提交成功"/"下一题准备中"）**And** 这是 D14 哲学的核心要求

7. **Given** 答案永久保存 **When** 考察结束后任意时间 **Then** 学习者可在 exam_boards/*.md 中回顾所有答案 **And** 可通过 Dataview 搜索"我答过的所有 {concept} 相关问题"

## Tasks / Subtasks

- [ ] Task 1: 实现 callout 追加逻辑 (AC: #1)
  - [ ] 格式化 `[!exam_question]+` callout（question_id / concept / question_text / 答题占位符）
  - [ ] Edit exam_boards/*.md body 末尾追加
  - [ ] 处理多题追加时的格式（题目间空行分隔）
  - [ ] 单元测试：callout 格式正确、多题追加不破坏已有内容

- [ ] Task 2: 实现 `/quiz_answer` sub-skill (AC: #3, #4)
  - [ ] QuickAdd macro 绑定 Cmd+Option+S hotkey
  - [ ] sub-skill 读取当前活动笔记完整内容
  - [ ] 正则提取最后一个 callout 的答案内容（anchor PRD §2.3.1 的 extract_last_answer 逻辑）
  - [ ] 占位符过滤和"请先写答案"提示
  - [ ] 单元测试：各种答案格式（多行、包含代码块、空答案、占位符）的提取正确性

- [ ] Task 3: 实现答案正则提取器 (AC: #4)
  - [ ] 实现 `extract_last_answer(exam_board_content: str) -> tuple[str, str]`
  - [ ] 匹配 `> [!exam_question]+` 标题行抓 Q{id}
  - [ ] 从 `> 答：` 行开始提取所有连续 `> ` 行
  - [ ] 去掉 `> ` 前缀拼接为完整答案
  - [ ] 边界情况：用户在 callout 外写了内容、答案包含嵌套 callout

- [ ] Task 4: 实现 frontmatter user_answer 更新 (AC: #5)
  - [ ] 更新 questions[-1].user_answer 字段
  - [ ] 记录提交时间戳

- [ ] Task 5: 实现 sidebar 内容隔离 (AC: #6)
  - [ ] skill prompt 声明 sidebar 内容限制
  - [ ] 状态指示文案：等待答题 / 提交成功 / 下一题准备中

- [ ] Task 6: 确保答案持久化可检索 (AC: #7)
  - [ ] 验证 exam_boards/*.md 保存完整
  - [ ] Dataview 查询兼容性验证

## Dev Notes

### Architecture
- D14 是用户 2026-04-09 Plan v16 Round 1 锁定的学习哲学选择，不可妥协
- md 编辑器答题 vs Claudian Chat sidebar 对话的关键区别：永久沉淀 vs 切换丢失
- 答题 = 写批注的延伸 → 批注 → 考察 → 答题 → 又是批注（完整闭环）
- Karpathy "write stuff down" 原则 + Donoghue & Hattie (2021) "写式 Retrieval Practice" d=1.55
- `/quiz_answer` sub-skill 是完全静默的（§1.6 Flow State 保护）

### File Paths
- Callout 追加：skill Edit 操作在 exam_boards/*.md
- 答案提取正则：anchor PRD §2.3.1 的 `extract_last_answer` 函数
- QuickAdd macro：Obsidian QuickAdd 配置
- Hotkey：Cmd+Option+S (Submit)

### Testing
- 单元测试：callout 格式、答案提取正则、占位符过滤
- 集成测试：出题 → 写答 → 提交 → 答案提取 → 传递给评分的完整链路
- 边界测试：空答案、超长答案、包含代码块的答案、多行答案

### Project Structure Notes
- exam_boards/*.md 的 callout 格式是 Obsidian 原生支持的
- `[!exam_question]+` 的 "+" 保证默认展开
- 正则需处理 Obsidian 的 blockquote 嵌套语法

### References
- **From PRD**: §2.3.1 md 编辑器为主答题工作流 (line 1211-1456)
- **From PRD**: §12.2 D14 答题媒介决策 (line 7479-7496)
- **From PRD**: §2.3 Step 7 — 出题循环 (line 1107-1155)
- D14 用户原话："我觉得这样回答问题就好比打批注"
- Karpathy "write stuff down" 原则
- Donoghue & Hattie (2021): 写式 Retrieval Practice d=1.55
- Karpicke & Blunt (2011): Retrieval Practice d=1.50

## UAT Script

> 1. 完成 `/start_exam_board` 的出题流程
> 2. 看到 exam_boards/*.md 中出现 `[!exam_question]+` callout
> 3. 点击"答："下方开始写答案
> 4. 反复修改几次答案内容（确认可自由编辑）
> 5. 确认 AI sidebar 没有显示题目/分数/提示
> 6. 按 Cmd+Option+S 提交答案
> 7. 确认 sidebar 显示"提交成功"状态
> 8. 查看 frontmatter，确认 user_answer 已填充
> 9. 关闭文件后重新打开，确认答案仍在

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| Callout 格式 | unit | `pytest tests/unit/test_exam_callout_format.py -x` | 0 failures |
| 答案正则提取 | unit | `pytest tests/unit/test_answer_extraction.py -x` | 0 failures |
| 占位符过滤 | unit | `pytest tests/unit/test_placeholder_filter.py -x` | 0 failures |
| Frontmatter 更新 | unit | `pytest tests/unit/test_answer_frontmatter.py -x` | 0 failures |
| 答题集成 | integration | `pytest tests/integration/test_exam_answer_submit.py -x` | 0 failures |

## User Feedback & Changes

### Feedback Log
(to be filled during/after implementation)

### Deviation Notes
(to be filled if implementation deviates from spec)

## Dev Agent Record

### Agent Model Used
(to be filled by Dev agent)

### Debug Log References
(to be filled by Dev agent)

### Completion Notes List
(to be filled by Dev agent)

### File List
(to be filled by Dev agent)
