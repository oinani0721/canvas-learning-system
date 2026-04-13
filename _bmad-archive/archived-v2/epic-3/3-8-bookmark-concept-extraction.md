---
doc_type: story
story_id: "3.8"
aliases: ["3.8"]
epic_id: "EPIC-3"
prd_id: "PRD14"
status: ready-for-dev
priority: "P1"
estimate_hours: 4
depends_on: ["3.1"]
blocks: []
trace:
  decisions: []
  bugs: []
---
# Story 3.8: 书签式概念提取（不中断考察）

## Story

As a 学习者,
I want 在考察中发现新概念时，以书签方式标记稍后处理,
so that 不中断当前考察流程，考后再深入讨论新概念。

## Acceptance Criteria

1. **Given** 学习者在检验白板答题过程中发现新概念
   **When** 学习者点击"书签"或使用快捷键标记
   **Then** 新概念被添加到临时书签列表（不立即创建笔记）
   **And** 考察流程不中断，继续当前题目

2. **Given** 学习者想要书签标记特定文本内容
   **When** 学习者选中答案编辑器中的文字并点击"书签"
   **Then** 选中的文字内容作为概念名称填入书签输入框
   **And** 学习者可以修改概念名称后确认（避免冗长文本直接成为概念名）

3. **Given** 考察结束（所有题目已提交或跳过）
   **When** 系统展示考察总结
   **Then** 书签列表中的新概念显示在总结页
   **And** 学习者可以选择是否为每个概念创建新笔记
   **And** 选择创建的概念，系统调用 Epic 4 Story 4.1 的创建流程（创建 .md + frontmatter + wikilink）
   **And** 选择忽略的概念从书签列表中移除，不创建笔记

4. **Given** 书签列表中已有同名概念
   **When** 学习者再次书签相同名称
   **Then** 系统提示"该概念已在书签列表中"，不重复添加
   **And** 书签列表不产生重复条目

5. **Given** 白板关闭时书签列表未处理
   **When** 系统关闭检验白板
   **Then** 未处理的书签列表持久化到 Neo4j PendingBookmark 节点（不丢失）
   **And** 下次进入系统时在通知区域提示"你有 N 个未处理书签"

## Tasks / Subtasks

- [ ] Task 1: 后端 — 书签管理 API (AC: #1, #4, #5)
  - [ ] 1.1 在 `exam_board.py` 实现 `POST /api/v1/exam-board/{exam_board_id}/bookmark`：接收 `{ concept_name: str, source_text: str | null }`
  - [ ] 1.2 在 `exam_board_service.py` 实现 `add_bookmark(exam_board_id, concept_name, source_text) -> BookmarkResult`
  - [ ] 1.3 重复检测：查询 Neo4j 同名 PendingBookmark（`concept_name` 精确匹配），存在则返回 `{ status: "duplicate" }`（HTTP 200，非 4xx）
  - [ ] 1.4 非重复时创建 Neo4j PendingBookmark 节点：`{ bookmark_id, concept_name, source_text, exam_board_id, created_at, status: "pending" }`
  - [ ] 1.5 实现 `GET /api/v1/exam-board/{exam_board_id}/bookmarks`：返回当前白板的所有 pending 书签列表

- [ ] Task 2: 后端 — 考察总结与书签处理 (AC: #3, #5)
  - [ ] 2.1 实现 `POST /api/v1/exam-board/{exam_board_id}/bookmark/{bookmark_id}/resolve`：接收 `{ action: "create_note" | "dismiss" }`
  - [ ] 2.2 `action = "create_note"` 时：调用 Epic 4 Story 4.1 的概念创建服务（`concept_creation_service.create_concept_note(concept_name)`）；若该服务尚未实现，返回 `{ status: "deferred", message: "concept creation will be available in Epic 4" }`（此降级不属于 mock，是显式功能边界声明）
  - [ ] 2.3 `action = "dismiss"` 时：将 PendingBookmark 状态改为 `dismissed`
  - [ ] 2.4 白板关闭时（`/close` 端点），`pending` 状态的书签自动保留（不删除）；`GET /api/v1/bookmarks/pending` 全局端点供通知系统使用

- [ ] Task 3: 前端 — 书签按钮与输入框 (AC: #1, #2)
  - [ ] 3.1 在 `ExamBoard.tsx` 添加"书签"按钮（icon 按钮，不占主界面空间）
  - [ ] 3.2 点击书签按钮时：检查答案编辑器是否有选中文字（`window.getSelection().toString()`）；有则预填入输入框
  - [ ] 3.3 弹出轻量 Popover（非全屏 Modal）包含：概念名输入框（可修改预填内容）+ 确认/取消按钮
  - [ ] 3.4 确认后：调用 `POST /bookmark` API；若返回 `duplicate` 则 toast "该概念已在书签列表中"；否则 toast "已添加到书签"
  - [ ] 3.5 添加书签后焦点自动回到答案编辑器，不中断作答流程

- [ ] Task 4: 前端 — 考察总结页书签处理 (AC: #3)
  - [ ] 4.1 考察总结页（考完/全跳过后展示）包含书签列表区域
  - [ ] 4.2 每个书签条目显示：概念名、来源文本预览（截断至 40 字）、"创建笔记"按钮、"忽略"按钮
  - [ ] 4.3 点击"创建笔记"调用 `/resolve?action=create_note`；成功则该条目打勾 + 灰化
  - [ ] 4.4 点击"忽略"调用 `/resolve?action=dismiss`；条目移出列表
  - [ ] 4.5 若书签列表为空，总结页不显示书签区域

- [ ] Task 5: 前端 — Zustand store 书签状态 (AC: #1, #4)
  - [ ] 5.1 在 `exam-board-store.ts` 添加：`bookmarks: BookmarkResult[]`
  - [ ] 5.2 实现 `addBookmark(conceptName, sourceText)` action（调用 API + 更新本地 store）
  - [ ] 5.3 重复检测在前端也做一层（`bookmarks.find(b => b.concept_name === conceptName)`），减少无效 API 请求

- [ ] Task 6: 编写测试 (AC: #1-5)
  - [ ] 6.1 后端单元测试 `tests/unit/test_bookmark.py`：重复检测、书签持久化、resolve 两种 action
  - [ ] 6.2 前端测试 `ExamBoard.test.tsx`：书签 Popover 预填文字、重复提示、总结页渲染

## Dev Notes

- **书签不中断原则**：Popover 组件（非全屏 Modal）是核心设计，避免打断答题心流；参考 Anki 的"标记"功能设计模式
- **与 Epic 4 Story 4.1 的依赖**：Story 3.8 的"创建笔记"功能在 Epic 3 内以降级方式实现（返回 deferred）；Epic 4 实现后自动接入。这是显式功能边界，非 mock
- **书签持久化意义**：学习者在考察中发现的新概念往往是真实知识盲点，不能因为白板关闭而丢失；PendingBookmark 节点在 Neo4j 中长期保留，直到用户主动 resolve
- **快捷键**：书签快捷键为 `Cmd/Ctrl+B`（在检验白板上下文中），不与全局浏览器快捷键冲突
- **source_text 长度限制**：后端 Pydantic `max_length=200`（截断过长选中文字），防止超大文本存入 Neo4j
- **通知系统集成**：`GET /api/v1/bookmarks/pending` 全局端点在 Epic 6 阶段集成到通知面板；本 Story 只需实现端点，不需要 UI 通知

### Project Structure Notes

- 后端书签服务：`backend/app/services/exam_board_service.py`（扩展）
- 后端书签端点：`backend/app/api/v1/endpoints/exam_board.py`（扩展）
- 前端 Popover：`frontend/src/components/ExamBoard.tsx`（内联 Popover）
- 总结页：`frontend/src/components/ExamSummary.tsx`（新建，含书签列表区域）
- store 扩展：`frontend/src/stores/exam-board-store.ts`
- 测试：`backend/tests/unit/test_bookmark.py`

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-3.8] — AC 和 FR 映射（FR16）
- [Source: _bmad-output/planning-artifacts/epics.md#Story-4.1] — 概念创建服务（创建笔记的下游依赖）
- [Source: frontend/src/stores/chat-store.ts] — Zustand store 风格参考
- [Source: frontend/src/components/ChatPanel.tsx] — 前端组件风格参考

## UAT Script

> Non-technical user validation: no code terminology, only describe what to click and what to see.

1. **验证书签不中断考察** (AC: #1)
   - 在检验白板答题时，点击"书签"按钮（或按 `Cmd+B`）
   - 应该出现一个小弹框（不是全屏覆盖），输入概念名
   - 点击确认后弹框消失，答题区域不变，可以继续作答
   - 如果弹框覆盖了整个界面导致无法作答，记录 Story 3.8

2. **验证选中文字预填** (AC: #2)
   - 在答案编辑器中选中几个字（比如一个概念名称）
   - 然后点击"书签"
   - 弹框中的概念名输入框应该自动填入你选中的文字
   - 如果没有预填，记录 Story 3.8

3. **验证重复检测** (AC: #4)
   - 书签同一个概念名两次
   - 第二次应该看到提示"该概念已在书签列表中"
   - 书签列表中该概念不应该出现两条
   - 如果重复添加成功，记录 Story 3.8

4. **验证总结页书签处理** (AC: #3)
   - 考察结束（提交或跳过所有题目）后的总结页
   - 应该能看到本次添加的书签列表
   - 点击"创建笔记"：该条目变为灰色/打勾（稍后 Epic 4 实现后会真正创建笔记）
   - 点击"忽略"：该条目从列表消失
   - 如果总结页看不到书签，记录 Story 3.8

5. **验证关闭后书签不丢失** (AC: #5)
   - 添加几个书签后直接关闭检验白板（不处理书签）
   - 重新打开系统
   - 在通知区域应该看到"你有 N 个未处理书签"的提示
   - 如果书签消失，记录 Story 3.8

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-3.8.1 | pytest | `.venv/bin/pytest tests/unit/test_bookmark.py -x -q` | 0 failed |
| CP-3.8.2 | pytest | `.venv/bin/pytest tests/integration/test_exam_board_api.py::test_bookmark_endpoints -x -q` | 0 failed |
| CP-3.8.3 | vitest | `cd frontend && npx vitest run src/__tests__/ExamBoard.test.tsx -t bookmark` | 0 failed |
| CP-3.8.4 | lint | `cd frontend && npx tsc --noEmit` | 0 errors |

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
