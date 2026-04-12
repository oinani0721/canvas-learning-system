---
doc_type: story
story_id: "3.7"
epic_id: "EPIC-3"
prd_id: "PRD14"
status: ready-for-dev
priority: "P1"
estimate_hours: 2
depends_on: ["3.4"]
blocks: []
trace:
  decisions: []
  bugs: []
---

# Story 3.7: 跳过题目不惩罚

## Story

As a 学习者,
I want 可以跳过题目且不受评分惩罚,
so that 我可以策略性地跳过暂时无法回答的题目，不影响掌握度分数。

## Acceptance Criteria

1. **Given** 学习者正在检验白板中面对一道题目
   **When** 学习者点击"跳过"
   **Then** 该题标记为 `skipped`，不计入掌握度评分
   **And** 跳过事件记录在 frontmatter 中（用于后续分析，但不影响 BKT/FSRS 参数）
   **And** 系统自动展示下一道题目

2. **Given** 当次检验白板所有题目均被跳过
   **When** 学习者跳过最后一道题
   **Then** 系统展示考察总结页，提示"本次所有题目已跳过"
   **And** 不更新任何概念的 BKT/FSRS 参数

3. **Given** 学习者已部分作答（编辑器中有内容）
   **When** 学习者点击"跳过"
   **Then** 系统弹出确认对话框："你已开始作答，确定要跳过吗？"
   **And** 确认后才跳过，取消则回到编辑状态
   **And** 已输入的答案内容丢弃（不保存草稿）

4. **Given** 跳过事件发生
   **When** 系统记录跳过
   **Then** Neo4j SkipEvent 节点记录：`{ question_id, concept_id, skipped_at, had_partial_answer: bool }`
   **And** 对应概念 frontmatter 中新增 `skip_history` 数组条目（不修改 `mastery_score` / `due_date`）

## Tasks / Subtasks

- [ ] Task 1: 后端 — 跳过 API (AC: #1, #4)
  - [ ] 1.1 在 `exam_board.py` 实现 `POST /api/v1/exam-board/{exam_board_id}/skip`：接收 `{ question_id, had_partial_answer: bool }`
  - [ ] 1.2 在 `exam_board_service.py` 实现 `skip_question(exam_board_id, question_id, had_partial_answer) -> SkipResult`
  - [ ] 1.3 创建 Neo4j SkipEvent 节点，关联 Question 和 ExamBoard
  - [ ] 1.4 更新 ExamBoard 节点：`skipped_questions` 数组 append `question_id`
  - [ ] 1.5 返回 `{ next_question: Question | null }`（null 表示所有题目已完成/跳过）

- [ ] Task 2: 后端 — frontmatter skip_history 写入 (AC: #4)
  - [ ] 2.1 复用 `frontmatter_service.py` 中的原子写函数，追加 `skip_history` 条目
  - [ ] 2.2 `skip_history` 条目结构：`{ skipped_at: datetime, question_id: str, had_partial_answer: bool }`
  - [ ] 2.3 明确不修改 `mastery_score`、`bkt_params`、`fsrs_params`、`due_date` 字段

- [ ] Task 3: 前端 — 跳过按钮与确认对话框 (AC: #1, #3)
  - [ ] 3.1 在 `ExamBoard.tsx` 添加"跳过"按钮（secondary 样式，与"提交"并排）
  - [ ] 3.2 点击跳过时检查 `answerText.trim() !== ""`；非空时弹出确认对话框（使用项目已有的 Dialog 组件）
  - [ ] 3.3 确认跳过后：调用 `/skip` API，清空 `answerText`，清空 `hints`，将 `currentHintLevel` 重置为 0
  - [ ] 3.4 API 返回 `next_question` 非 null 时，更新 `exam-board-store.ts` 的 `currentQuestion`；null 时导航到总结页
  - [ ] 3.5 `answerEditorMode === "readonly"` 时隐藏跳过按钮（已提交的题不可跳过）

- [ ] Task 4: 前端 — 所有题目跳过时的总结页 (AC: #2)
  - [ ] 4.1 若 `/skip` 返回 `next_question: null`，展示简单总结卡："本次所有题目已跳过，无掌握度更新"
  - [ ] 4.2 总结页提供"重新开始"按钮（触发新一轮检验）和"关闭白板"按钮

- [ ] Task 5: 编写测试 (AC: #1, #2, #3, #4)
  - [ ] 5.1 后端单元测试 `tests/unit/test_skip.py`：跳过不更新 BKT/FSRS、skip_history 追加、全部跳过返回 null
  - [ ] 5.2 前端测试：有内容时弹出确认、跳过后切换下一题、全跳过展示总结页

## Dev Notes

- **不惩罚设计依据**：Kornell & Bjork (2008) "Learning, memory, and the spacing effect" 指出强制答题会引发测试焦虑，降低学习效果；跳过不惩罚符合自主学习节奏原则（FR12 明确规定）
- **skip_history 的用途**：未来 Epic 5 Story 5.3（5 信号融合）可以利用跳过频率作为辅助信号，但本 Story 只记录不计算
- **草稿不保存**：跳过时丢弃部分答案是有意为之（避免学习者把草稿当答案留存），与 FR12 设计一致
- **与 Story 3.6 的交互**：跳过时同时清除已展示的提示（`hints` 数组重置），避免提示信息污染下一题

### Project Structure Notes

- 后端跳过逻辑：`backend/app/services/exam_board_service.py`（`skip_question` 函数）
- frontmatter 写入：复用 `backend/app/services/frontmatter_service.py`
- 前端跳过按钮：`frontend/src/components/ExamBoard.tsx`
- 测试：`backend/tests/unit/test_skip.py`、`frontend/src/__tests__/ExamBoard.test.tsx`（扩展）

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-3.7] — AC 和 FR 映射（FR12）
- [Source: Kornell & Bjork 2008] — 跳过不惩罚的认知科学依据
- [Source: backend/app/api/v1/endpoints/canvas.py] — 后端端点风格参考

## UAT Script

> Non-technical user validation: no code terminology, only describe what to click and what to see.

1. **验证直接跳过** (AC: #1)
   - 在检验白板中，不输入任何内容，直接点击"跳过"
   - 系统应该立即跳到下一道题，不弹出确认框
   - 如果跳过后仍停在同一道题，记录 Story 3.7

2. **验证有内容时确认** (AC: #3)
   - 在编辑器中输入一些内容（随意几个字）
   - 然后点击"跳过"
   - 应该弹出对话框："你已开始作答，确定要跳过吗？"
   - 点击"取消"应该回到编辑状态，内容保留
   - 点击"确认"应该跳到下一题，内容消失
   - 如果没有弹出确认框直接跳过，记录 Story 3.7

3. **验证掌握度不变** (AC: #1, #4)
   - 记录某个概念当前的掌握度分数
   - 对该概念的题目点击"跳过"
   - 打开对应笔记的元数据
   - `mastery_score` 数值应该与跳过前相同（未发生变化）
   - 如果掌握度降低，记录 Story 3.7

4. **验证全部跳过** (AC: #2)
   - 对当次检验的所有题目都点击"跳过"
   - 最后一题跳过后应该看到总结页："本次所有题目已跳过"
   - 如果总结页显示了掌握度变化，记录 Story 3.7

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-3.7.1 | pytest | `.venv/bin/pytest tests/unit/test_skip.py -x -q` | 0 failed |
| CP-3.7.2 | vitest | `cd frontend && npx vitest run src/__tests__/ExamBoard.test.tsx -t skip` | 0 failed |
| CP-3.7.3 | pytest | `.venv/bin/pytest tests/integration/test_exam_board_api.py::test_skip_endpoint -x -q` | 0 failed |

## User Feedback & Changes

### Feedback Log

<!-- Users write BMAD-ANNO callouts below. Claude scans and dispatches by intent. -->

### Deviation Notes

<!-- Claude auto-fills: summary of historically processed feedback -->

## Dev Agent Record

### Agent Model Used

(to be filled by Dev agent)

### Debug Log References

### Completion Notes List

### File List

## Relations

- EPIC: [[EPIC-3]]
- PRD: [[PRD14]]
- Depends on: [[3.4]]
