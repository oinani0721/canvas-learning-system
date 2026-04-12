# Story 6.1: 检验白板生成与基础框架

Status: ready-for-dev

## Story

As a 用户,
I want 从 Dashboard 选择原白板生成一个空白的检验白板，继承原白板所有基础功能，
so that 我能在独立空间中被系统考察。

## Acceptance Criteria

1. **AC-1: 检验白板生成入口（FR-EXAM-01, FR-DASH-03）**
   - **Given** 用户在 Dashboard 选择原白板并点击"生成检验白板"
   - **When** 系统执行生成逻辑
   - **Then** 创建一个空白的检验白板，关联到原白板（存储 sourceCanvasId）
   - **And** 检验白板在 IndexedDB 中创建新记录，type 标记为 `exam`
   - **And** 同步到后端 `POST /api/v1/exam/start` 创建 exam_session 记录
   - **And** 检验白板在 Dashboard 的"检验白板列表"中出现（FR-DASH-02）
   - **And** 同一原白板可生成不限数量的检验白板（FR-EXAM-20）

2. **AC-2: 继承原白板所有基础功能（FR-EXAM-07）**
   - **Given** 用户进入生成的检验白板
   - **When** 在检验白板中操作
   - **Then** 支持节点创建（双击空白处）、编辑、删除（Delete 键）
   - **And** 支持从节点边缘拖出连线到另一个节点创建 Edge
   - **And** 支持右键/中键拖拽平移画布，滚轮缩放
   - **And** 支持点击节点打开 AI 对话（ChatPanel 考察模式）
   - **And** 支持 Edge 连线图标 → Agent Q&A（FR-EDGE-01~04 能力继承）
   - **And** 支持 /命令技能系统（FR-SKILL-01~05 能力继承）
   - **And** 白板操作响应 < 16ms（60fps），与原白板一致
   - **And** 操作逻辑与 Obsidian Canvas 保持一致

3. **AC-3: 禁止嵌套检验白板（FR-EXAM-21）**
   - **Given** 用户在检验白板中操作
   - **When** 尝试生成检验白板（UI 中不应出现此选项）
   - **Then** 检验白板上下文中隐藏"生成检验白板"按钮/入口
   - **And** 后端 API `POST /api/v1/exam/start` 检查 source_canvas_type，若为 `exam` 则拒绝并返回 400 错误
   - **And** 如需再次考察，引导用户回到原白板重新生成

4. **AC-4: 检验白板 ExamCanvas Svelte 组件**
   - **Given** 前端渲染检验白板
   - **When** ExamCanvas.svelte 组件挂载
   - **Then** 复用 CanvasView.svelte 核心渲染能力（HTML 节点 + SVG 边混合渲染）
   - **And** 注入考察模式专属 UI 元素（考察状态栏、认知负荷计时器占位）
   - **And** ChatPanel 自动切换为考察模式（props: mode="exam"）
   - **And** CSS 使用 `cl-exam-*` 前缀命名，适配 Light/Dark 主题

5. **AC-5: exam-state Store 创建**
   - **Given** 前端需要管理检验白板状态
   - **When** 检验白板生成/进入/退出
   - **Then** `exam-state.svelte.ts` 管理以下状态：
     - currentExamId: 当前检验白板 ID
     - sourceCanvasId: 原白板 ID
     - examMode: 考察模式（point-by-point / comprehensive / mixed）
     - examStatus: 考察状态（idle / in-progress / paused / completed）
     - startTime: 考察开始时间（供认知负荷计时使用）
     - examinedNodes: 已考察节点列表
     - discoveredNodes: 新发现节点列表
   - **And** Store 状态通过 Dexie liveQuery 响应式绑定 IndexedDB

6. **AC-6: 后端 exam_service 基础框架**
   - **Given** 后端 FastAPI 运行
   - **When** 调用检验白板相关 API
   - **Then** 以下端点正常工作：
     - `POST /api/v1/exam/start` — 创建 exam_session（参数：source_canvas_id, exam_mode）
     - `GET /api/v1/exam/{exam_id}` — 获取 exam_session 详情
     - `GET /api/v1/exam/by-canvas/{canvas_id}` — 获取原白板的所有检验白板列表
     - `PATCH /api/v1/exam/{exam_id}/status` — 更新考察状态
   - **And** exam_session Pydantic Model 包含：id, source_canvas_id, exam_mode, status, start_time, end_time, examined_nodes, discovered_nodes, score_history
   - **And** 端点使用密码学令牌管道（FR-MCP-02）

## Tasks / Subtasks

- [ ] **Task 1: 后端 exam_service 基础框架** (AC: #6)
  - [ ] 1.1 创建 `backend/app/services/exam_service.py`：ExamService 类，管理 exam_session 生命周期
  - [ ] 1.2 创建 `backend/app/models/exam_models.py`：ExamSession / ExamNode / ExamScore Pydantic Models
  - [ ] 1.3 创建 `backend/app/api/v1/endpoints/exam.py`：4 个 REST 端点（start / get / by-canvas / status）
  - [ ] 1.4 在 start 端点中实现嵌套检验白板检查（source_canvas_type == 'exam' → 400）
  - [ ] 1.5 编辑后运行 `ruff check` + `ruff format --check`

- [ ] **Task 2: 前端 exam-state Store** (AC: #5)
  - [ ] 2.1 创建 `src/stores/exam-state.svelte.ts`：ExamState class 管理考察生命周期状态
  - [ ] 2.2 实现 Dexie liveQuery 绑定 IndexedDB exam_sessions 表
  - [ ] 2.3 实现 createExam / enterExam / exitExam / updateStatus 方法

- [ ] **Task 3: ExamCanvas Svelte 组件** (AC: #4)
  - [ ] 3.1 创建 `src/components/exam/ExamCanvas.svelte`：复用 CanvasView 核心渲染
  - [ ] 3.2 注入考察模式专属 UI 元素区域（顶部状态栏、底部计时器占位）
  - [ ] 3.3 ChatPanel 模式切换逻辑（props: mode="exam"）
  - [ ] 3.4 CSS 使用 cl-exam-* 前缀，适配 Light/Dark 主题

- [ ] **Task 4: Dashboard 集成——生成检验白板入口** (AC: #1)
  - [ ] 4.1 在 DashboardView 的 CanvasCard 组件中添加"生成检验白板"按钮
  - [ ] 4.2 点击按钮触发 exam-state.createExam(sourceCanvasId)
  - [ ] 4.3 生成成功后自动跳转到检验白板视图

- [ ] **Task 5: 禁止嵌套检验白板** (AC: #3)
  - [ ] 5.1 ExamCanvas 组件中隐藏"生成检验白板"按钮
  - [ ] 5.2 后端 start 端点添加嵌套检查校验
  - [ ] 5.3 前端检查 canvas type 并显示引导提示（引导回原白板）

- [ ] **Task 6: 继承原白板功能验证** (AC: #2)
  - [ ] 6.1 验证节点 CRUD 在 ExamCanvas 中正常工作
  - [ ] 6.2 验证 Edge 创建、对话图标在 ExamCanvas 中正常工作
  - [ ] 6.3 验证 ChatPanel 考察模式渲染正常
  - [ ] 6.4 验证白板操作 60fps 性能

- [ ] **Task 7: Dexie Schema 扩展** (AC: #1, #5)
  - [ ] 7.1 在 `dexie-db.ts` 中添加 `exam_sessions` 表定义（独立 Story 级 Schema 变更）
  - [ ] 7.2 exam_sessions 表字段：id, sourceCanvasId, examMode, status, startTime, endTime, examinedNodes, discoveredNodes

## Dev Notes

### 架构定位

本 Story 是 Epic 6 的基础框架 Story，建立检验白板的数据模型、前后端通信、Svelte 组件骨架。后续 Story（6.2~6.8）在此基础上添加具体考察功能。

### 依赖关系

- **依赖 Epic 1**：CanvasView / CanvasNode / CanvasEdge（白板基础组件）
- **依赖 Epic 3**：ChatPanel（对话面板，需支持 mode="exam" props）
- **依赖 Story 5.4**：DashboardView（检验白板入口 + 列表展示）
- **被 Story 6.2~6.8 依赖**：所有后续检验白板 Story 依赖本 Story 的 ExamCanvas + exam-state + exam_service

### 关键设计决策

- ExamCanvas 复用 CanvasView 而非重写：通过组合模式注入考察专属 UI，不复制白板渲染逻辑
- ChatPanel 三模式复用（普通/考察/Edge）：通过 Svelte 5 Snippet 注入差异化 UI（[Source: architecture.md#Frontend Architecture]）
- exam_session 存储在 SQLite（后端）+ IndexedDB（前端）双写，Outbox delta sync 保持一致
- 回退策略：检验白板核心框架失败时，退化为普通白板 + 单轮考察对话

### Project Structure Notes

- 前端组件在 `src/components/exam/` 目录（B 组）
- 后端服务在 `backend/app/services/exam_service.py`（新建）
- 后端 API 在 `backend/app/api/v1/endpoints/exam.py`（新建）
- Store 在 `src/stores/exam-state.svelte.ts`（新建）
- CSS 类名前缀 `cl-exam-*`

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story6.1] — AC 原文
- [Source: _bmad-output/planning-artifacts/prd.md#能力域4] — FR-EXAM-01/07/21
- [Source: _bmad-output/planning-artifacts/architecture.md#考察启动流] — 考察启动数据流
- [Source: _bmad-output/planning-artifacts/architecture.md#Structure Patterns] — 前后端目录结构
- [Source: _bmad-output/planning-artifacts/architecture.md#Frontend Architecture] — ChatPanel 三模式复用
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Component Strategy] — B 组检验白板组件清单
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#旅程2] — 检验白板考察用户旅程

## Dev Agent Record

### Agent Model Used

(待开发时填写)

### Debug Log References

(待开发时填写)

### Completion Notes List

(待开发时填写)

### File List

- `backend/app/services/exam_service.py` — 新建
- `backend/app/models/exam_models.py` — 新建
- `backend/app/api/v1/endpoints/exam.py` — 新建
- `src/stores/exam-state.svelte.ts` — 新建
- `src/components/exam/ExamCanvas.svelte` — 新建
- `src/services/dexie-db.ts` — 修改（添加 exam_sessions 表）
- `src/components/dashboard/CanvasCard.svelte` — 修改（添加生成按钮）
