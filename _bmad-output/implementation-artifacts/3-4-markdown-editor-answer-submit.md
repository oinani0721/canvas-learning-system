---
doc_type: story
story_id: "3.4"
epic_id: "EPIC-3"
prd_id: "PRD14"
status: ready-for-dev
priority: "P0"
estimate_hours: 4
depends_on: ["3.1"]
blocks: []
trace:
  decisions: []
  bugs: []
---

# Story 3.4: Markdown 编辑器手写答案 + 手动提交

## Story

As a 学习者,
I want 在检验白板的 markdown 编辑器中手写答案，手动触发提交,
so that 我可以按自己的节奏组织答案，不被自动提交打断。

## Acceptance Criteria

1. **Given** 题目已展示在检验白板中
   **When** 学习者在 markdown 编辑器中编写答案
   **Then** 编辑器支持标准 markdown 语法（标题、列表、代码块、公式）
   **And** 不自动提交，只在学习者手动点击"提交"时触发

2. **Given** 学习者点击"提交"
   **When** 答案被提交
   **Then** 答案内容被发送到评分系统（Story 3.5）
   **And** 编辑器进入只读状态，防止提交后修改
   **And** 答案内容进入评分流程

3. **Given** 学习者尚未在编辑器中输入任何内容
   **When** 学习者点击"提交"
   **Then** 系统提示"请先写下你的答案"，不触发评分
   **And** 编辑器焦点回到输入框

4. **Given** 答案已提交且编辑器处于只读状态
   **When** 评分完成后系统展示结果
   **Then** 答案内容保持可见（只读），供学习者对照评分结果参考

## Tasks / Subtasks

- [ ] Task 1: 前端 — Markdown 编辑器组件 (AC: #1)
  - [ ] 1.1 在 `frontend/src/components/` 创建 `AnswerEditor.tsx`，使用 CodeMirror 6（已在项目中）或 `@uiw/react-md-editor`（检查 package.json 是否存在）实现 markdown 编辑器
  - [ ] 1.2 编辑器配置：启用 GFM（GitHub Flavored Markdown）、数学公式（KaTeX）、代码高亮
  - [ ] 1.3 编辑器状态：`"editing"` | `"readonly"`，由 `exam-board-store.ts` 中 `answerEditorMode` 控制
  - [ ] 1.4 `"editing"` 模式下：全功能可编辑；`"readonly"` 模式下：只显示渲染后的 markdown，禁用输入

- [ ] Task 2: 前端 — 提交按钮与空答案校验 (AC: #1, #2, #3)
  - [ ] 2.1 在 `ExamBoard.tsx` 底部添加"提交"按钮（primary 样式）
  - [ ] 2.2 提交前校验：`answerText.trim() === ""` → toast 提示"请先写下你的答案"，`editor.focus()`，`return`
  - [ ] 2.3 提交成功后：调用 `examBoardStore.setAnswerEditorMode("readonly")`，编辑器切换只读
  - [ ] 2.4 提交按钮在 `"readonly"` 模式下隐藏（替换为"下一题"按钮）

- [ ] Task 3: 前端 — Zustand store 更新 (AC: #2)
  - [ ] 3.1 在 `exam-board-store.ts` 新增字段：`answerText: string`、`answerEditorMode: "editing" | "readonly"`、`currentQuestionId: string | null`
  - [ ] 3.2 实现 `submitAnswer(answerText: string, questionId: string)` action：调用后端 API，成功后切换编辑器为 readonly
  - [ ] 3.3 实现 `resetForNextQuestion()` action：清空 `answerText`，重置 `answerEditorMode` 为 `"editing"`

- [ ] Task 4: 后端 — 答案接收 API (AC: #2)
  - [ ] 4.1 实现 `POST /api/v1/exam-board/{exam_board_id}/answer`：接收 `{ question_id: str, answer_text: str }`
  - [ ] 4.2 将答案存入 Neo4j Answer 节点：`{ answer_id, question_id, answer_text, submitted_at }`
  - [ ] 4.3 返回 `{ answer_id, status: "received" }`；评分异步触发（Story 3.5），不阻塞响应
  - [ ] 4.4 答案写入后触发评分队列（通过 async task 或 EventBus）

- [ ] Task 5: 编写测试 (AC: #1, #2, #3, #4)
  - [ ] 5.1 前端测试 `AnswerEditor.test.tsx`：编辑/只读切换、空答案校验、markdown 渲染
  - [ ] 5.2 后端单元测试 `tests/unit/test_answer_submission.py`：答案存储、空答案拒绝
  - [ ] 5.3 后端集成测试：`/answer` 端点返回 `answer_id` + 格式验证

## Dev Notes

- **Markdown 编辑器选型**：优先检查 `frontend/package.json` 是否已有 `@uiw/react-md-editor` 或 `codemirror`；若有直接复用，若无则用 `@uiw/react-md-editor`（轻量，8KB gzip，无额外系统依赖）
- **只读状态实现**：`@uiw/react-md-editor` 支持 `readOnly` prop；若用 CodeMirror 6 则设置 `EditorState.readOnly.of(true)` extension
- **公式支持**：KaTeX 已在项目中（确认 `package.json`）；`@uiw/react-md-editor` 支持 `rehype-katex` + `remark-math` 插件
- **答案长度限制**：后端 Pydantic 模型设置 `max_length=10000`（约 5000 汉字），防止超大答案拖慢评分
- **评分触发时序**：答案 API 接收后立即返回 `{ answer_id, status: "received" }`；评分作为 `asyncio.create_task()` 后台执行，与 Story 3.5 对接

### Project Structure Notes

- 前端编辑器组件：`frontend/src/components/AnswerEditor.tsx`
- 前端 store：`frontend/src/stores/exam-board-store.ts`（扩展）
- 后端端点：`backend/app/api/v1/endpoints/exam_board.py`（扩展 `/answer` 路由）
- 后端模型：`backend/app/models/exam_board.py`（新增 `Answer` model）
- 测试：`frontend/src/__tests__/AnswerEditor.test.tsx`、`backend/tests/unit/test_answer_submission.py`

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-3.4] — AC 和 FR 映射（FR9）
- [Source: frontend/src/components/ChatPanel.tsx] — 前端组件风格参考
- [Source: frontend/src/stores/chat-store.ts] — Zustand store 风格参考
- [Source: backend/app/api/v1/endpoints/canvas.py] — 后端端点风格参考

## UAT Script

> Non-technical user validation: no code terminology, only describe what to click and what to see.

1. **验证 Markdown 编辑** (AC: #1)
   - 在检验白板答题区域输入以下内容并检查渲染效果：
     - `# 标题` → 应该显示为大标题
     - `- 列表项` → 应该显示为项目符号
     - ` ```代码``` ` → 应该显示为代码框
   - 如果格式不生效，记录 Story 3.4

2. **验证不自动提交** (AC: #1)
   - 开始打字，中途停下来等待 10 秒
   - 内容应该保持不变，不自动提交
   - 如果内容消失或自动跳到下一题，记录 Story 3.4

3. **验证空答案提示** (AC: #3)
   - 不在编辑器中输入任何内容
   - 直接点击"提交"按钮
   - 应该看到提示"请先写下你的答案"
   - 答案框应该获得焦点（光标出现在输入框中）
   - 如果空答案被直接提交，记录 Story 3.4

4. **验证提交后只读** (AC: #2)
   - 写完答案后点击"提交"
   - 提交成功后，答案区域应该变为不可编辑状态
   - 尝试点击答案区域并输入文字，应该无法编辑
   - 答案内容仍然可见（不消失）
   - 如果提交后仍可编辑，记录 Story 3.4

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-3.4.1 | vitest | `cd frontend && npx vitest run src/__tests__/AnswerEditor.test.tsx` | 0 failed |
| CP-3.4.2 | pytest | `.venv/bin/pytest tests/unit/test_answer_submission.py -x -q` | 0 failed |
| CP-3.4.3 | pytest | `.venv/bin/pytest tests/integration/test_exam_board_api.py::test_answer_endpoint -x -q` | 0 failed |
| CP-3.4.4 | lint | `cd frontend && npx tsc --noEmit` | 0 errors |

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
- Depends on: [[3.1]]
