# Story 5.4: FSRS 复习提醒与完整 Dashboard

Status: ready-for-dev

## Story

As a 用户,
I want 在 Dashboard 中浏览所有原白板和检验白板、查看 FSRS 待复习节点列表（按紧急程度排序）、一键启动考察、查看历史检验白板详情,
so that 每天打开就知道该复习什么，能管理所有白板和考察记录。

## Acceptance Criteria

1. **AC-1: 原白板列表（FR-DASH-01）**
   - **Given** 用户打开 Dashboard（右侧面板 DashboardView）
   - **When** Dashboard 加载
   - **Then** 显示所有原白板列表（名称 + 创建时间 + 节点数量 + 精通度概览）
   - **And** 点击白板卡片可打开对应白板（切换到 CanvasView）
   - **And** 提供"新建白板"按钮（复用 Story 1.4 已有逻辑）
   - **And** 无白板时显示空状态引导文字 + 新建按钮

2. **AC-2: 检验白板列表（FR-DASH-02）**
   - **Given** Dashboard 加载完成
   - **When** 用户切换到检验白板 Tab
   - **Then** 显示所有检验白板列表，每个卡片展示：
     - 关联的原白板名称
     - 考察时间（创建时间）
     - 考察状态（进行中 / 已完成）
     - 考察节点数
     - 掌握度变化摘要（如 "+3 节点掌握提升"）
   - **And** 点击检验白板卡片可打开查看完整考察记录

3. **AC-3: FSRS 待复习节点列表（FR-MAST-04）**
   - **Given** Dashboard 加载完成
   - **When** 用户查看待复习区域
   - **Then** 显示 FSRS 待复习节点列表，按紧急程度排序（overdue 优先 → due 其次 → 薄弱节点最后）
   - **And** 每个待复习项显示：节点名称 + 所属白板 + 精通度级别（颜色标识） + 上次复习时间 + 紧急程度标签
   - **And** 排序逻辑：overdue 节点按逾期天数降序 → due 节点按到期时间升序 → effective_proficiency < 0.70 的薄弱节点按 proficiency 升序
   - **And** 无待复习节点时显示正面语言空状态："所有知识点都在掌握中，继续保持！"

4. **AC-4: 启动考察入口（FR-DASH-03）**
   - **Given** 用户在 Dashboard 浏览原白板列表
   - **When** 用户点击白板卡片上的"开始考察"按钮
   - **Then** 弹出考察模式选择面板（ExamModeSelector — 本 Story 仅渲染入口按钮和占位 Modal，模式选择和考察启动的完整实现在 Story 6.1/6.2）
   - **And** 考察入口按钮仅在白板有 3 个以上知识节点时可点击（否则 disabled + tooltip 提示"至少需要 3 个知识节点才能开始考察"）

5. **AC-5: 历史检验白板详情（FR-DASH-04 + FR-EXAM-20）**
   - **Given** 用户在 Dashboard 点击某个原白板
   - **When** 展开该白板的详情区域
   - **Then** 显示该原白板的所有历史检验白板列表（时间倒序）
   - **And** 每条记录显示：考察时间 + 考察模式 + 考察节点数 + 掌握度变化
   - **And** 点击可打开查看完整考察记录（切换到该检验白板视图）

6. **AC-6: Dashboard 升级兼容**
   - **Given** Story 1.4 已实现最小化 Dashboard（仅白板列表 + 新建白板）
   - **When** 本 Story 升级 DashboardView 为完整版
   - **Then** 保持原有白板列表和新建白板功能不变
   - **And** 新增 Tab 切换：原白板 / 检验白板 / 待复习
   - **And** 新增 ReviewItem 和 ExamCard 子组件
   - **And** 新增 ExamLauncher 占位组件（考察入口按钮 + 占位 Modal）
   - **And** 不破坏 Story 1.4 已有的 CanvasCard 组件和 DashboardView 基础结构

7. **AC-7: 后端 API 集成**
   - **Given** 后端 FastAPI 运行中
   - **When** Dashboard 请求数据
   - **Then** 原白板列表从 IndexedDB `canvas_boards` 读取（本地优先，已有）
   - **And** 检验白板列表从后端 `GET /api/v1/exam_sessions` 读取（SQLite 存储）
   - **And** FSRS 待复习节点从后端 `GET /mastery/batch` 读取并前端排序
   - **And** 后端不可达时 Dashboard 仍可显示原白板列表（降级模式），检验白板和待复习区域显示"后端离线"提示

## Tasks / Subtasks

- [ ] **Task 1: 审查已有 Dashboard 代码** (AC: #6)
  - [ ] 1.1 对抗性审查 `obsidian-canvas-learning/src/components/dashboard/DashboardView.svelte`（Story 1.4 产物）：验证现有结构、props、事件处理
  - [ ] 1.2 审查 `obsidian-canvas-learning/src/components/dashboard/CanvasCard.svelte`（Story 1.4 产物）：验证卡片组件接口
  - [ ] 1.3 审查 `obsidian-canvas-learning/src/stores/canvas-state.svelte.ts`：验证 boards 列表数据流
  - [ ] 1.4 审查后端 `backend/app/services/mastery_engine.py` 中 `get_review_candidates()` 和 `concept_to_response()` 方法：验证可复用性
  - [ ] 1.5 审查后端 `backend/app/api/v1/endpoints/mastery.py` 中 `/mastery/batch` 端点：验证返回数据格式
  - [ ] 1.6 产出 `[Code-Review]` 结果，记录到 Graphiti

- [ ] **Task 2: 扩展 IndexedDB Schema 和 TypeScript 类型** (AC: #2, #5, #7)
  - [ ] 2.1 扩展 `obsidian-canvas-learning/src/types/canvas.d.ts`（仅追加，不修改已有类型）：
    - `ExamSession`：`{ id: string; sourceBoardId: string; sourceBoardName: string; mode: 'point-to-point' | 'comprehensive' | 'mixed'; status: 'in-progress' | 'completed'; nodesExamined: number; masteryChangeSummary: string; createdAt: string; completedAt?: string }`
    - `ReviewNode`：`{ conceptId: string; name: string; boardId: string; boardName: string; masteryLevel: number; masteryColor: string; effectiveProficiency: number; freshness: 'fresh' | 'due' | 'overdue' | 'stale'; lastReviewedAt?: string; dueDate?: string; overdueDays?: number }`
  - [ ] 2.2 扩展 `obsidian-canvas-learning/src/services/api-client.ts`（仅追加方法）：
    - `getExamSessions(boardId?: string): Promise<ExamSession[]>` — 调用 `GET /api/v1/exam_sessions`
    - `getMasteryBatch(): Promise<MasteryBatchResponse>` — 调用 `GET /mastery/batch`

- [ ] **Task 3: Dashboard Store 扩展** (AC: #1, #2, #3, #7)
  - [ ] 3.1 创建 `obsidian-canvas-learning/src/stores/dashboard-state.svelte.ts`：
    - `activeTab: 'boards' | 'exams' | 'review'` — 当前活动 Tab
    - `examSessions: ExamSession[]` — 检验白板列表
    - `reviewNodes: ReviewNode[]` — 待复习节点列表
    - `isLoading: boolean` — 加载状态
    - `backendOffline: boolean` — 后端离线标志
  - [ ] 3.2 实现数据加载方法：
    - `loadExamSessions()` — 从后端加载检验白板列表，失败时设置 `backendOffline = true`
    - `loadReviewNodes()` — 从后端 `/mastery/batch` 加载全量精通度数据，前端排序计算待复习列表
    - `refreshAll()` — 并行加载所有 Dashboard 数据
  - [ ] 3.3 实现 FSRS 排序逻辑（前端纯计算，不依赖后端排序）：
    - 从 `/mastery/batch` 响应中提取所有 ConceptState
    - 按 freshness 分组：overdue → due → weak（proficiency < 0.70）
    - overdue 按逾期天数降序，due 按到期时间升序，weak 按 proficiency 升序
    - 映射为 `ReviewNode[]` 类型
  - [ ] 3.4 导出 singleton `export const dashboardState = new DashboardState()`

- [ ] **Task 4: 升级 DashboardView 组件** (AC: #1, #2, #3, #6)
  - [ ] 4.1 修改 `obsidian-canvas-learning/src/components/dashboard/DashboardView.svelte`：
    - 添加 Tab 栏：原白板 | 检验白板 | 待复习
    - Tab 切换驱动内容区域切换
    - 保持原有白板列表和新建白板功能不变
  - [ ] 4.2 原白板 Tab：
    - 复用已有 CanvasCard 组件
    - 为 CanvasCard 追加精通度概览（节点颜色分布饼图或简单统计文字）
    - 为 CanvasCard 追加"开始考察"按钮
    - 点击卡片展开历史检验白板列表（可折叠）
  - [ ] 4.3 检验白板 Tab：
    - 使用 ExamCard 组件渲染列表
    - 按时间倒序排列
    - 支持按原白板过滤
  - [ ] 4.4 待复习 Tab：
    - 使用 ReviewItem 组件渲染列表
    - 顶部显示统计摘要：X 个 overdue + Y 个 due + Z 个薄弱
    - 空状态正面语言引导
  - [ ] 4.5 加载状态和离线降级：
    - 数据加载中显示 skeleton 占位（不用 spinner）
    - 后端离线时原白板 Tab 正常（本地数据），其他 Tab 显示离线提示

- [ ] **Task 5: CanvasCard 组件升级** (AC: #1, #4, #5)
  - [ ] 5.1 修改 `obsidian-canvas-learning/src/components/dashboard/CanvasCard.svelte`：
    - 追加精通度概览区域（保持现有字段不变）
    - 追加"开始考察"按钮（ExamLauncher 触发器）
    - 追加历史检验白板折叠列表
  - [ ] 5.2 精通度概览实现：
    - 显示简单文字统计："X 掌握 / Y 学习中 / Z 薄弱"（颜色对应精通度色系）
    - 数据来源：`/mastery/batch` 响应按白板节点聚合
  - [ ] 5.3 "开始考察"按钮：
    - 白板节点数 >= 3 时可点击（`disabled` 否则）
    - disabled 时 tooltip："至少需要 3 个知识节点才能开始考察"
    - 点击触发 ExamLauncher Modal

- [ ] **Task 6: 创建 ReviewItem 组件** (AC: #3)
  - [ ] 6.1 创建 `obsidian-canvas-learning/src/components/dashboard/ReviewItem.svelte`
  - [ ] 6.2 实现待复习节点卡片：
    ```html
    <div class="cl-dash-review-item" class:cl-dash-review-item--overdue={isOverdue}>
      <div class="cl-dash-review-item-color" style="background: {masteryColor}" />
      <div class="cl-dash-review-item-content">
        <span class="cl-dash-review-item-name">{node.name}</span>
        <span class="cl-dash-review-item-board">{node.boardName}</span>
      </div>
      <div class="cl-dash-review-item-meta">
        <span class="cl-dash-review-item-freshness">{freshnessLabel}</span>
        {#if node.lastReviewedAt}
          <span class="cl-dash-review-item-last-review">{relativeTime}</span>
        {/if}
      </div>
    </div>
    ```
  - [ ] 6.3 紧急程度视觉标识：
    - overdue：左侧边框红色 + 标签"已逾期 X 天"
    - due：左侧边框黄色 + 标签"建议今天复习"
    - weak：左侧边框橙色 + 标签"需要加强"（正面语言）
  - [ ] 6.4 点击事件：点击 ReviewItem → 打开该节点所在的白板并选中该节点

- [ ] **Task 7: 创建 ExamCard 组件** (AC: #2, #5)
  - [ ] 7.1 创建 `obsidian-canvas-learning/src/components/dashboard/ExamCard.svelte`
  - [ ] 7.2 实现检验白板卡片：
    - 显示关联原白板名称 + 考察时间 + 考察状态 + 考察节点数 + 掌握度变化摘要
    - 进行中状态显示"考察进行中"徽标（蓝色）
    - 已完成状态显示"已完成"徽标（绿色）
  - [ ] 7.3 点击事件：点击 ExamCard → 切换到该检验白板视图

- [ ] **Task 8: 创建 ExamLauncher 占位组件** (AC: #4)
  - [ ] 8.1 创建 `obsidian-canvas-learning/src/components/dashboard/ExamLauncher.svelte`
  - [ ] 8.2 实现考察入口占位 Modal：
    - 使用 Obsidian `Modal` API
    - 显示三种考察模式选项（点对点 / 综合题 / 混合）— 视觉占位，点击显示"考察功能将在后续版本启用"
    - 完整的模式选择和考察启动逻辑在 Story 6.1/6.2 实现
  - [ ] 8.3 Modal 内显示选中白板名称 + 节点数量 + 推荐模式提示

- [ ] **Task 9: 后端 API 端点** (AC: #2, #5, #7)
  - [ ] 9.1 审查后端是否已有 exam_sessions 列表端点，如无则创建：
    - `GET /api/v1/exam_sessions` — 列出所有检验白板 sessions
    - `GET /api/v1/exam_sessions?board_id={id}` — 按原白板过滤
    - 返回格式：`{ sessions: ExamSessionResponse[], total: int }`
  - [ ] 9.2 确认 `/mastery/batch` 端点返回完整 volatile 字段（freshness, due_date, effective_proficiency）
  - [ ] 9.3 如有需要修复 `/mastery/batch` 响应中的 FSRS due_date 字段（确保 FSRS Card 的 due 日期在响应中可用）
  - [ ] 9.4 编辑后运行 `ruff check` + `ruff format --check` 确认 lint 通过

- [ ] **Task 10: CSS 样式** (AC: #1-#6)
  - [ ] 10.1 在各 Svelte 组件中使用 scoped CSS + Obsidian CSS 变量 + `cl-dash-*` 前缀
  - [ ] 10.2 Tab 栏样式：
    - 使用 Obsidian `--tab-*` 相关 CSS 变量（如有）或自建简洁 Tab
    - 活动 Tab 底部线 `var(--interactive-accent)`
  - [ ] 10.3 ReviewItem 样式：
    - 紧急程度左边框颜色映射（overdue=#dc3545 / due=#ffc107 / weak=#fd7e14）
    - hover 背景 `var(--background-modifier-hover)`
  - [ ] 10.4 ExamCard 样式：
    - 状态徽标颜色（进行中=蓝 / 已完成=绿）
    - 时间显示使用 `var(--text-muted)`
  - [ ] 10.5 统计摘要区域：
    - 精通度颜色统计使用 Story 5.1 定义的颜色映射（灰/红/橙/蓝/绿）
  - [ ] 10.6 适配 Light/Dark 主题：全部使用 Obsidian CSS 变量，无硬编码颜色
  - [ ] 10.7 Dashboard 整体布局：填满右侧面板宽度（`width: fill_container`）

- [ ] **Task 11: 集成验证** (AC: #1-#7)
  - [ ] 11.1 验证 Tab 切换功能：原白板/检验白板/待复习三个 Tab 正确切换内容
  - [ ] 11.2 验证原白板列表：与 Story 1.4 行为一致 + 新增精通度概览和考察入口
  - [ ] 11.3 验证 FSRS 排序：创建测试数据（overdue/due/weak 节点），确认排序正确
  - [ ] 11.4 验证后端离线降级：断开后端，确认原白板 Tab 正常，其他 Tab 显示离线提示
  - [ ] 11.5 验证 ExamLauncher Modal：点击开始考察 → Modal 弹出 → 占位提示正确显示
  - [ ] 11.6 验证 ReviewItem 点击跳转：点击待复习节点 → 打开对应白板
  - [ ] 11.7 验证响应式更新：精通度数据变化后 Dashboard 自动刷新（通过 store 订阅）

## Dev Notes

### Brownfield 上下文——升级非重写

本 Story 是 **升级** Story 1.4 的最小化 Dashboard 为完整版。Story 1.4 已实现：
- `DashboardView.svelte` — 白板列表 + 新建白板
- `CanvasCard.svelte` — 白板卡片（名称 + 创建时间 + 节点数量）
- `canvas-state.svelte.ts` — boards 数据管理

本 Story 新增：
- Tab 切换机制
- ReviewItem / ExamCard / ExamLauncher 三个新组件
- dashboard-state.svelte.ts 独立 Store（管理非白板数据）
- 后端 API 集成（/mastery/batch + /exam_sessions）

**核心原则**：保持 Story 1.4 已有逻辑不变，仅追加新功能。修改 DashboardView 和 CanvasCard 时确保向后兼容。

### 依赖关系

| 依赖 | 状态 | 说明 |
|------|------|------|
| Story 5.1: BKT+FSRS 双引擎 | ✅ ready-for-dev | 提供 `/mastery/batch` 端点 + `get_review_candidates()` + `concept_to_response()` |
| Story 1.4: 白板 CRUD + 最小化 Dashboard | ✅ ready-for-dev | 提供 DashboardView/CanvasCard 基础组件 + canvas-state Store |
| Story 5.2: 节点颜色可视化 | ✅ ready-for-dev | 提供精通度颜色映射常量（5 级颜色系统） |

### FSRS 待复习排序算法

```
输入: /mastery/batch 返回的所有 ConceptState 数据

排序规则:
1. overdue 节点: FSRS due date 已过期
   - 按逾期天数降序（最紧急的在前）
   - 紧急标签: "已逾期 X 天"
2. due 节点: FSRS due date 是今天或即将到期
   - 按到期时间升序（最快到期的在前）
   - 紧急标签: "建议今天复习"
3. weak 节点: effective_proficiency < 0.70 但 FSRS 未到期
   - 按 proficiency 升序（最薄弱的在前）
   - 紧急标签: "需要加强"

输出: ReviewNode[] 有序列表
```

数据来源：`/mastery/batch` 端点返回的 volatile 字段包含 `freshness`（fresh/due/overdue/stale）和 `effective_proficiency`。排序逻辑在前端 `dashboard-state.svelte.ts` 中纯计算实现，不增加后端负担。

### Dashboard Tab 设计

```
┌─────────────────────────────────┐
│  原白板  │  检验白板  │  待复习   │  ← Tab 栏
├─────────────────────────────────┤
│                                 │
│  （根据 Tab 切换内容）            │
│                                 │
│  原白板 Tab:                     │
│    CanvasCard (带精通度+考察入口)  │
│    └─ 折叠: 历史检验白板列表       │
│                                 │
│  检验白板 Tab:                   │
│    ExamCard 列表（时间倒序）       │
│                                 │
│  待复习 Tab:                     │
│    统计摘要 (X overdue/Y due)    │
│    ReviewItem 列表（紧急程度排序） │
│                                 │
└─────────────────────────────────┘
```

### 精通度颜色系统（复用 Story 5.1 定义）

| Level | 状态 | 颜色 | 说明 |
|-------|------|------|------|
| 0 | Not Assessed | #6c757d（灰） | 未考察 |
| 1 | Shaky | #dc3545（红） | effective_proficiency < 0.40 |
| 2 | Developing | #fd7e14（橙） | 0.40 ~ 0.70 |
| 3 | Proficient | #0d6efd（蓝） | 0.70 ~ 0.90 |
| 4 | Mastered | #198754（绿） | >= 0.90 且 fluent_count >= 2 |

### 考察入口策略（防蔓延 DD-10）

本 Story 的考察入口是**占位入口**（ExamLauncher），仅渲染 UI 和 Modal：
- 按钮可点击 → 弹出 Modal → 显示考察模式选项
- 点击任何模式 → 显示"考察功能将在后续版本启用"
- **完整的考察启动逻辑**（创建检验白板、选择薄弱节点、启动 Agent 出题）在 Story 6.1/6.2 实现
- 这避免了在没有检验白板基础设施（Story 6.1）的情况下过早实现启动流程

### 不做的事项（防蔓延 DD-10）

- 不实现完整考察启动流程（Story 6.1/6.2）
- 不实现考察对话面板（Story 6.3）
- 不实现 Token 成本展示 CostTracker（Story 7.2）
- 不实现 OLM 三层面板（Phase 2）
- 不实现 WebSocket 实时推送（后续 Story）
- 不修改 IndexedDB Schema version（本 Story 不需要新的 IndexedDB 表，检验白板数据从后端 SQLite 读取）
- 不实现学习档案面板中的考察入口（Story 5.3 的 FR-EXAM-17）
- 不实现考察记录详情页面完整展示（Story 6.8）

### 共享文件编辑规则

| 文件 | 规则 |
|------|------|
| `DashboardView.svelte` | 修改已有文件：追加 Tab 机制 + 新区域，保持原有白板列表逻辑 |
| `CanvasCard.svelte` | 修改已有文件：追加精通度概览 + 考察入口按钮 + 历史折叠列表，保持原有展示字段 |
| `types/canvas.d.ts` | 仅追加 ExamSession / ReviewNode 类型，不修改已有类型 |
| `services/api-client.ts` | 仅追加 getExamSessions / getMasteryBatch 方法，不修改已有方法 |

### 命名规范速查（本 Story 涉及）

- Svelte 组件文件：`PascalCase.svelte`（如 `ReviewItem.svelte`）
- Store 文件：`kebab-case.svelte.ts`（如 `dashboard-state.svelte.ts`）
- CSS 类名：`cl-dash-*`（C 组 Dashboard）
- TypeScript 变量/函数：`camelCase`
- 后端 API 端点：`snake_case` 复数（如 `/api/v1/exam_sessions`）

### Project Structure Notes

```
obsidian-canvas-learning/
├── src/
│   ├── components/
│   │   └── dashboard/
│   │       ├── DashboardView.svelte    # [修改] 添加 Tab 切换 + 新区域
│   │       ├── CanvasCard.svelte       # [修改] 追加精通度+考察入口+历史
│   │       ├── ReviewItem.svelte       # [新建] 待复习节点卡片
│   │       ├── ExamCard.svelte         # [新建] 检验白板卡片
│   │       └── ExamLauncher.svelte     # [新建] 考察入口占位 Modal
│   ├── stores/
│   │   └── dashboard-state.svelte.ts   # [新建] Dashboard 数据 Store
│   ├── services/
│   │   └── api-client.ts              # [修改] 追加 getExamSessions/getMasteryBatch
│   └── types/
│       └── canvas.d.ts                # [修改] 追加 ExamSession/ReviewNode 类型

backend/
├── app/
│   └── api/v1/endpoints/
│       └── exam_sessions.py           # [新建或修改] 检验白板列表端点（如不存在）
```

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 5.4] — Story 需求和 AC 原文
- [Source: _bmad-output/planning-artifacts/architecture.md#能力域10 Dashboard] — FR-DASH-01~04 架构含义
- [Source: _bmad-output/planning-artifacts/architecture.md#能力域5 精通度追踪] — FSRS 复习提醒、effective_proficiency 定义
- [Source: _bmad-output/planning-artifacts/architecture.md#Project Structure] — C 组 Dashboard 组件目录（DashboardView/CanvasCard/ExamCard/ExamLauncher/CostTracker）
- [Source: _bmad-output/planning-artifacts/architecture.md#Frontend Architecture] — 右侧面板单视图切换模式
- [Source: _bmad-output/planning-artifacts/architecture.md#FR Coverage Map] — Dashboard: `dashboard/*` + `api/exam`(列表) + `api/canvas`(列表) + IndexedDB + SQLite
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Component Strategy] — C 组 Dashboard 组件：DashboardView, CanvasCard, ReviewItem
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#面板切换模式] — 右侧面板永远只显示一个视图，切换即替换不叠加
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#UX Pattern Analysis] — Anki 模式迁移："每天打开就知道做什么" → Dashboard 待复习列表
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#空状态] — 所有空状态提供引导文字 + 操作建议
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#反馈模式] — 颜色、持续时间、样式规范
- [Source: _bmad-output/planning-artifacts/prd.md#能力域10] — FR-DASH-01~04 需求
- [Source: _bmad-output/planning-artifacts/prd.md#能力域5] — FR-MAST-04 FSRS 复习时机提醒
- [Source: _bmad-output/implementation-artifacts/5-1-bkt-fsrs-mastery-system.md] — AC-7 精通度颜色映射、AC-9 /mastery/batch 端点
- [Source: _bmad-output/implementation-artifacts/1-4-canvas-core-crud-mini-dashboard.md] — AC-7 最小化 Dashboard、Task 6/7 DashboardView/CanvasCard 组件
- [Source: backend/app/services/mastery_engine.py#get_review_candidates] — 待复习节点筛选逻辑（effective_proficiency < 0.70 OR freshness due/overdue）

## Dev Agent Record

### Agent Model Used

(待开发时填写)

### Debug Log References

(待开发时填写)

### Completion Notes List

(待开发时填写)

### File List

- `obsidian-canvas-learning/src/components/dashboard/DashboardView.svelte` — 修改（Tab 切换 + 新区域）
- `obsidian-canvas-learning/src/components/dashboard/CanvasCard.svelte` — 修改（精通度 + 考察入口 + 历史）
- `obsidian-canvas-learning/src/components/dashboard/ReviewItem.svelte` — 新建
- `obsidian-canvas-learning/src/components/dashboard/ExamCard.svelte` — 新建
- `obsidian-canvas-learning/src/components/dashboard/ExamLauncher.svelte` — 新建
- `obsidian-canvas-learning/src/stores/dashboard-state.svelte.ts` — 新建
- `obsidian-canvas-learning/src/services/api-client.ts` — 修改（追加方法）
- `obsidian-canvas-learning/src/types/canvas.d.ts` — 修改（追加类型）
- `backend/app/api/v1/endpoints/exam_sessions.py` — 新建或修改（检验白板列表端点）
