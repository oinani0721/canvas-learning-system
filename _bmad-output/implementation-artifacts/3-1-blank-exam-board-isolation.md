---
doc_type: story
story_id: "3.1"
aliases: ["3.1"]
epic_id: "EPIC-3"
prd_id: "PRD14"
status: ready-for-dev
priority: "P0"
estimate_hours: 8
depends_on: []
blocks: []
trace:
  decisions: []
  bugs: []
---
# Story 3.1: 空白检验白板创建 + 信息隔离 + 防嵌套

## Story

As a 学习者,
I want 启动完全空白的检验白板，看不到笔记原文,
so that 我可以在没有参考材料的环境下真正考察自己的理解。

## Acceptance Criteria

1. **Given** 学习者触发考察命令（hotkey 或按钮）
   **When** 系统创建检验白板
   **Then** 白板为完全空白状态，不显示任何笔记原文
   **And** 学习者无法在白板内查看原始笔记（信息隔离）

2. **Given** 学习者已在一个检验白板内
   **When** 学习者尝试再次启动检验白板
   **Then** 系统拒绝创建并提示"不可在检验白板内嵌套考察"（FR14）
   **And** 原有检验白板保持不变，不被关闭

3. **Given** 检验白板已创建
   **When** 白板处于激活状态
   **Then** 白板状态标记持久化到 session storage，防止页面刷新后丢失嵌套检测
   **And** 白板关闭时清除状态标记

## Tasks / Subtasks

- [ ] Task 1: 后端 — 检验白板创建 API (AC: #1)
  - [ ] 1.1 在 `backend/app/api/v1/endpoints/` 新建 `exam_board.py`，实现 `POST /api/v1/exam-board/create` 端点
  - [ ] 1.2 请求体：`{ "canvas_id": str }`；响应体：`{ "exam_board_id": str, "created_at": datetime, "status": "active" }`
  - [ ] 1.3 创建 `backend/app/services/exam_board_service.py`，`create_exam_board()` 生成 UUID、写入 Neo4j ExamBoard 节点（状态 active）
  - [ ] 1.4 确保创建时不向前端返回任何笔记原文内容

- [ ] Task 2: 后端 — 防嵌套检测 (AC: #2)
  - [ ] 2.1 在 `exam_board_service.py` 实现 `check_active_exam_board(canvas_id: str) -> bool`，查询 Neo4j 是否存在 active ExamBoard
  - [ ] 2.2 `create_exam_board()` 调用前先检查；若已有 active 则抛出 `ExamBoardNestingError`（HTTP 409）
  - [ ] 2.3 实现 `POST /api/v1/exam-board/{exam_board_id}/close`，将 ExamBoard 状态改为 closed

- [ ] Task 3: 前端 — 检验白板 UI 组件 (AC: #1, #2)
  - [ ] 3.1 在 `frontend/src/components/` 创建 `ExamBoard.tsx`，渲染完全空白的白板容器（无笔记内容区域）
  - [ ] 3.2 在 `frontend/src/stores/` 创建 `exam-board-store.ts`（Zustand），管理 `isExamBoardActive: boolean`、`examBoardId: string | null`
  - [ ] 3.3 嵌套检测：`useExamBoardStore` 在发起创建请求前检查 `isExamBoardActive`；已激活则 toast 提示"不可在检验白板内嵌套考察"，不发请求
  - [ ] 3.4 将 `isExamBoardActive` 同步到 `sessionStorage`，防刷新丢失

- [ ] Task 4: 前端 — Hotkey + 触发入口 (AC: #1)
  - [ ] 4.1 在 `frontend/src/hooks/useHotkeys.ts` 注册触发检验白板的快捷键（默认 `Cmd/Ctrl+Shift+E`）
  - [ ] 4.2 在主工具栏添加"检验"按钮，点击触发同一流程
  - [ ] 4.3 调用 `POST /api/v1/exam-board/create`，成功后更新 Zustand store、渲染 `ExamBoard` 组件

- [ ] Task 5: 编写测试 (AC: #1, #2, #3)
  - [ ] 5.1 后端单元测试：`tests/unit/test_exam_board_service.py`，覆盖正常创建、嵌套检测 409、关闭白板
  - [ ] 5.2 后端集成测试：`tests/integration/test_exam_board_api.py`，验证 API 响应格式
  - [ ] 5.3 前端单元测试：`frontend/src/__tests__/ExamBoard.test.tsx`，验证嵌套提示渲染、sessionStorage 同步

## Dev Notes

- **信息隔离核心原则**：`ExamBoard` 组件渲染时不挂载任何读取笔记内容的子组件；后端 create API 也不返回笔记内容
- **防嵌套双重保险**：前端 Zustand store 做第一道快速检测（无网络开销）；后端 Neo4j 查询做第二道检测（防多窗口绕过）
- **Neo4j ExamBoard 节点 schema**：`{ exam_board_id: UUID, canvas_id: str, status: "active"|"closed", created_at: datetime, closed_at: datetime|null }`
- **sessionStorage key**：`canvas_exam_board_active` = `"true"/"false"`；`canvas_exam_board_id` = UUID
- **NFR-INT-1 相关**：白板关闭时确保 store 状态和 sessionStorage 同步清除，避免残留导致永久锁死

### Project Structure Notes

- 后端端点：`backend/app/api/v1/endpoints/exam_board.py`
- 后端服务：`backend/app/services/exam_board_service.py`
- 前端组件：`frontend/src/components/ExamBoard.tsx`
- 前端 store：`frontend/src/stores/exam-board-store.ts`
- 路由注册：`backend/app/api/v1/router.py`（需加入 exam_board router）

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-3.1] — AC 和 FR 映射（FR6, FR14）
- [Source: backend/app/api/v1/endpoints/canvas.py] — 后端端点风格参考
- [Source: frontend/src/stores/chat-store.ts] — Zustand store 风格参考
- [Source: frontend/src/components/ChatPanel.tsx] — 前端组件风格参考

## UAT Script

> Non-technical user validation: no code terminology, only describe what to click and what to see.

1. **验证空白白板** (AC: #1)
   - 打开 Canvas Learning System
   - 按 `Cmd+Shift+E`（Mac）或 `Ctrl+Shift+E`（Windows）触发检验
   - 应该看到一个空白页面/面板，没有任何笔记文字
   - 如果看到了笔记内容，记录 Story 3.1 + 截图

2. **验证信息隔离** (AC: #1)
   - 在检验白板激活状态下，检查界面上是否有任何笔记原文
   - 所有笔记内容应该不可见
   - 如果能看到笔记内容，记录 Story 3.1 + 具体位置

3. **验证防嵌套** (AC: #2)
   - 已在检验白板中，再次按 `Cmd+Shift+E` 或点击"检验"按钮
   - 应该看到提示"不可在检验白板内嵌套考察"
   - 当前白板应该保持不变，没有被关闭
   - 如果没有提示或打开了第二个白板，记录 Story 3.1

4. **验证关闭后可重新开启** (AC: #3)
   - 关闭检验白板（点击关闭按钮或按 Esc）
   - 再次按 `Cmd+Shift+E`
   - 应该正常打开新的空白白板，没有报错
   - 如果无法重新打开，记录 Story 3.1

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-3.1.1 | pytest | `.venv/bin/pytest tests/unit/test_exam_board_service.py -x -q` | 0 failed |
| CP-3.1.2 | pytest | `.venv/bin/pytest tests/integration/test_exam_board_api.py -x -q` | 0 failed |
| CP-3.1.3 | vitest | `cd frontend && npx vitest run src/__tests__/ExamBoard.test.tsx` | 0 failed |
| CP-3.1.4 | lint | `cd frontend && npx tsc --noEmit` | 0 errors |

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
