# Story 5.3: 学习档案面板

Status: ready-for-dev

## Story

As a 用户,
I want 点击节点时查看该节点的学习档案——掌握度、Tips、薄弱方向、关键问答,
so that 我能回顾和追踪每个知识点的学习历程。

## Acceptance Criteria

1. **AC-1: L1 聚合精通度指示器与学习摘要（FR-TRACE-01）**
   - **Given** 用户点击节点并切换到学习档案视图
   - **When** LearningProfile 面板加载
   - **Then** 顶部显示聚合精通度指示器（复用 Story 5.1 AC-7 的 5 级精通度分级与颜色映射）
   - **And** 精通度指示器包含：精通度等级文字（如"掌握中"）、颜色色条、effective_proficiency 的语义描述（处方性语言，如"建议复习"而非"你只有 40%"）
   - **And** 学习摘要显示：交互次数、考察次数、最近考察日期
   - **And** 精通度数据从 `mastery-state` Store 响应式读取（复用 Story 5.2 已建立的 Store）
   - **And** 面板加载时间 < 500ms

2. **AC-2: L2 Tips 列表可追溯（FR-TRACE-02）**
   - **Given** 节点有用户标注的 Tips 数据（来自 Story 3.6 Tips 标注功能写入 Graphiti）
   - **When** 面板展示 Tips 区域
   - **Then** 列出该节点所有 Tips，每条 Tip 显示：内容摘要、标注时间、分类标签
   - **And** 每条 Tip 可展开查看来源对话上下文（显示标注时的前后 2-3 条对话消息）
   - **And** 展开使用折叠动画（CSS transition 200ms）
   - **And** 无 Tips 时显示空状态引导文字："对话中选中文字即可标记 Tips"
   - **And** Tips 数据从后端 `/api/v1/profile/{node_id}/tips` 接口获取

3. **AC-3: L2 需要加强方向——正面语言（FR-TRACE-03）**
   - **Given** 节点有考察历史和错误记录（来自 Graphiti 三通道写入的误解/错误数据）
   - **When** 面板展示"需要加强的方向"区域
   - **Then** 聚合该节点的误解模式，按频次排序展示
   - **And** 使用正面支持性语言框架：标题为"需要加强的方向"而非"错误列表"
   - **And** 每条方向显示：方向描述、出现频次（如"3 次考察中涉及"）、最近出现时间
   - **And** 每条方向可展开查看关联的考察记录摘要
   - **And** 无薄弱方向时显示正面空状态："目前表现不错，继续保持！"
   - **And** 数据从后端 `/api/v1/profile/{node_id}/weaknesses` 接口获取

4. **AC-4: L3 关键问答精选折叠展示（FR-TRACE-04）**
   - **Given** 节点有关键问答数据（来自对话归档 Hot-Warm-Cold 管道自动提取）
   - **When** 面板展示"关键问答"区域
   - **Then** 问答按主题聚类展示，每个主题为一个折叠组
   - **And** 默认全部折叠，用户点击主题标题展开查看该主题下的问答对
   - **And** 每个问答对显示：问题摘要、回答摘要、提取时间
   - **And** 无关键问答时显示空状态引导："和 AI 对话后，精彩问答会自动整理到这里"
   - **And** 数据从后端 `/api/v1/profile/{node_id}/qa-highlights` 接口获取

5. **AC-5: FSRS 下次复习日期展示（FR-MAST-03/04）**
   - **Given** 节点有 FSRS 复习调度数据（来自 Story 5.1 AC-2 FSRS Card）
   - **When** 面板渲染底部区域
   - **Then** 显示"下次复习"日期，格式为用户 locale 友好格式（如"3 天后"、"明天"、"2026-03-20"）
   - **And** 已到期的复习显示为紧急状态（黄色高亮 + "建议今天复习"）
   - **And** 未被考察过的节点不显示复习日期（显示"完成首次考察后安排复习"）
   - **And** 复习日期从 `mastery-state` Store 中 FSRS Card 的 due date 字段读取

6. **AC-6: 开始考察按钮——单节点考察入口（FR-EXAM-17）**
   - **Given** 学习档案面板底部
   - **When** 用户点击"开始考察"按钮
   - **Then** 触发单节点考察流程：弹出 ExamModeSelector（复用 Story 6.2 组件），考察范围限于当前节点
   - **And** 按钮使用主操作样式（紫色/渐变填充，UX 规范按钮层级）
   - **And** 按钮状态：后端不可达时禁用 + 灰色 + tooltip "后端服务不可用"
   - **And** 点击后面板切换到检验白板考察视图（右侧面板切换模式，不叠加）
   - **And** 考察操作流程与 Dashboard 启动考察一致（FR-DASH-03 同规范）

7. **AC-7: 面板视图切换集成**
   - **Given** 用户点击白板上的节点
   - **When** 右侧面板显示该节点内容
   - **Then** 面板提供"对话"和"学习档案"两个 Tab 切换
   - **And** 切换即替换不叠加（UX 规范：右侧面板永远只显示一个视图）
   - **And** Tab 切换使用 Obsidian 风格的 tab 样式，CSS 类名前缀 `cl-profile-`
   - **And** 从对话 Tab 切换到档案 Tab 时，对话状态不丢失（后台保持）

8. **AC-8: Light/Dark 主题适配**
   - **Given** 用户使用 Obsidian Light 或 Dark 主题
   - **When** 面板渲染
   - **Then** 所有组件颜色通过 Obsidian CSS 变量（`--background-primary`、`--text-normal`、`--interactive-accent` 等）适配
   - **And** 精通度颜色复用 Story 5.2 AC-4 的 `--cl-mastery-*` CSS 变量
   - **And** 切换主题时面板颜色即时更新，无需重新打开

## Tasks / Subtasks

- [ ] Task 1: 后端 Profile API 端点实现 (AC: #1, #2, #3, #4, #5)
  - [ ] 1.1 创建 `backend/app/api/v1/profile.py`，实现 4 个 REST 端点：
    - `GET /api/v1/profile/{node_id}/summary` — 精通度摘要+学习统计
    - `GET /api/v1/profile/{node_id}/tips` — Tips 列表+来源对话上下文
    - `GET /api/v1/profile/{node_id}/weaknesses` — 薄弱方向聚合（正面语言框架）
    - `GET /api/v1/profile/{node_id}/qa-highlights` — 关键问答按主题聚类
  - [ ] 1.2 创建 Pydantic 响应模型：`ProfileSummary`、`TipItem`、`WeaknessItem`、`QAHighlightCluster`
  - [ ] 1.3 实现 Graphiti 查询逻辑：从 Graphiti 个人记忆引擎检索节点关联的 Tips/错误/问答实体
  - [ ] 1.4 实现误解模式聚合算法：按错误类型+频次排序，转换为正面语言描述
  - [ ] 1.5 在 FastAPI 路由注册 profile router

- [ ] Task 2: 前端 profile-state Store (AC: #1, #2, #3, #4, #5)
  - [ ] 2.1 创建 `src/stores/profile-state.svelte.ts`，管理当前节点的学习档案数据
  - [ ] 2.2 实现 `loadProfile(nodeId)` 异步方法，调用后端 4 个 profile 端点
  - [ ] 2.3 集成 `mastery-state` Store 读取精通度和 FSRS 数据（复用 Story 5.1/5.2）
  - [ ] 2.4 实现加载状态管理（loading/loaded/error）
  - [ ] 2.5 实现节点切换时的数据清理和重新加载

- [ ] Task 3: LearningProfile 主组件 (AC: #1, #7, #8)
  - [ ] 3.1 创建 `src/components/profile/LearningProfile.svelte`，作为学习档案面板容器
  - [ ] 3.2 实现 L1 精通度指示器区域：颜色色条 + 等级文字 + 处方性描述 + 学习摘要统计
  - [ ] 3.3 实现 Tab 切换逻辑（对话/学习档案），集成到右侧面板视图管理
  - [ ] 3.4 实现加载/空状态/错误状态的 UI 展示
  - [ ] 3.5 CSS 使用 `cl-profile-*` 前缀 + Obsidian CSS 变量 + Svelte scoped

- [ ] Task 4: TipCard 子组件 (AC: #2)
  - [ ] 4.1 创建 `src/components/profile/TipCard.svelte`
  - [ ] 4.2 实现折叠/展开交互：默认显示摘要，点击展开来源对话上下文
  - [ ] 4.3 实现折叠动画（CSS transition 200ms）
  - [ ] 4.4 展示 Tip 内容、标注时间、分类标签
  - [ ] 4.5 空状态处理

- [ ] Task 5: WeaknessPanel 子组件 (AC: #3)
  - [ ] 5.1 创建 `src/components/profile/WeaknessPanel.svelte`
  - [ ] 5.2 实现正面语言展示框架（标题、描述措辞）
  - [ ] 5.3 实现频次排序展示 + 折叠查看关联考察记录
  - [ ] 5.4 正面空状态文案

- [ ] Task 6: QACluster 子组件 (AC: #4)
  - [ ] 6.1 创建 `src/components/profile/QACluster.svelte`
  - [ ] 6.2 实现按主题聚类的折叠组展示（默认全部折叠）
  - [ ] 6.3 实现问答对展示格式（问题摘要 + 回答摘要 + 时间）
  - [ ] 6.4 空状态引导文案

- [ ] Task 7: FSRS 复习日期展示 + 开始考察按钮 (AC: #5, #6)
  - [ ] 7.1 实现 FSRS 下次复习日期的 locale 友好格式化（"3 天后"/"明天"/具体日期）
  - [ ] 7.2 实现到期紧急状态高亮样式
  - [ ] 7.3 实现"开始考察"按钮（`StartExamButton` 或内置于 LearningProfile）
  - [ ] 7.4 按钮点击触发考察流程（emit 事件 → 面板切换到检验白板流程）
  - [ ] 7.5 实现按钮禁用状态（后端不可达检测）

- [ ] Task 8: API Client 集成 (AC: #2, #3, #4)
  - [ ] 8.1 在 `src/services/api-client.ts` 中添加 profile 相关方法（snake→camelCase 转换）
  - [ ] 8.2 实现错误处理和超时重试

## Dev Notes

### Architecture Alignment

- **前端组件层级**：D 组学习档案，CSS 前缀 `cl-profile-*`
- **前端文件位置**：`src/components/profile/` 目录，包含 LearningProfile.svelte、TipCard.svelte、WeaknessPanel.svelte、QACluster.svelte
- **后端 API**：`backend/app/api/v1/profile.py`，REST `/api/v1/profile/` 路径
- **状态管理**：`src/stores/profile-state.svelte.ts`（新建）+ 复用 `mastery-state.svelte.ts`（Story 5.2 已建立）
- **数据来源**：Graphiti 个人记忆引擎（Tips/错误/问答实体）+ mastery-state Store（精通度/FSRS）

### Dependencies

- **Story 5.1** (BKT+FSRS 双引擎)：精通度数据 ConceptState、5 级分级、FSRS Card due date
- **Story 5.2** (节点颜色可视化)：mastery-state Store、`--cl-mastery-*` CSS 变量、`getMasteryColor()` 纯函数

### Data Flow

```
Graphiti (Tips/Errors/QA) ──→ profile.py REST API ──→ api-client.ts ──→ profile-state Store ──→ LearningProfile.svelte
                                                                                                  ├── TipCard.svelte
                                                                                                  ├── WeaknessPanel.svelte
                                                                                                  └── QACluster.svelte
mastery-state Store (5.1/5.2) ──────────────────────────────────────────→ LearningProfile.svelte (L1 指示器 + FSRS 日期)
```

### UX Design Constraints

- **右侧面板模式**：永远只显示一个视图，切换即替换不叠加（UX 规范）
- **精通度不展示原始数值**：处方性语言，"建议复习 X"而非"你只有 40%"
- **正面框架原则**：所有反馈使用正面语言，"需要加强的方向"而非"错误列表"
- **渐进展示**：L1 始终可见 → L2 默认可见可折叠 → L3 默认折叠按需展开
- **Pencil UI 范式 #8**：节点学习档案面板已有 Pencil 验证（FR-TRACE-01~04, FR-EXAM-17）

### CSS Isolation

- Svelte scoped CSS + `cl-profile-*` 类名前缀
- 颜色/字体/间距全部使用 Obsidian CSS 变量
- Light/Dark 通过 `.theme-light` / `.theme-dark` 选择器适配
- 精通度颜色复用 `--cl-mastery-*` 变量（Story 5.2 定义）

### Testing Standards

- 前端：vitest + @testing-library/svelte + fake-indexeddb + jsdom
- 后端：pytest + httpx AsyncClient
- 后端 profile API 端点：单元测试覆盖 4 个端点的正常/空数据/错误场景
- 前端组件：测试各子组件的渲染、折叠/展开交互、空状态展示、主题适配

### FR Coverage

| FR ID | AC | 说明 |
|-------|-----|------|
| FR-TRACE-01 | AC-1 | 节点学习档案面板（精通度指示器+学习摘要） |
| FR-TRACE-02 | AC-2 | Tips 列表，可展开查看来源对话上下文 |
| FR-TRACE-03 | AC-3 | "需要加强方向"展示（正面语言） |
| FR-TRACE-04 | AC-4 | 关键问答精选（按主题聚类，默认折叠） |
| FR-EXAM-17 | AC-6 | 用户可从节点学习档案面板启动单节点考察（第二考察入口） |
| FR-MAST-03 | AC-1, AC-5 | MVP 精通度通过学习档案面板传达 |
| FR-MAST-04 | AC-5 | FSRS 算法安排复习时机提醒 |

### Project Structure Notes

- 前端 D 组组件路径与 architecture.md 一致：`src/components/profile/`
- 后端 profile API 路径与 architecture.md 一致：`backend/app/api/v1/profile.py`
- Store 路径与 architecture.md 一致：`src/stores/profile-state.svelte.ts`
- UX 规范组件命名差异：UX 规范中 D 组列出 `WeakPointItem`，architecture.md 中为 `WeaknessPanel.svelte`——以 architecture.md 为准（WeaknessPanel 包含多个 weakness items）

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 5.3] — Story 定义与 AC
- [Source: _bmad-output/planning-artifacts/architecture.md#Requirements Overview, 能力域 8] — L1/L2/L3 层级定义
- [Source: _bmad-output/planning-artifacts/architecture.md#Directory Structure] — D 组文件结构
- [Source: _bmad-output/planning-artifacts/architecture.md#API Communication Patterns] — `/api/v1/profile/` REST API
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Component Strategy] — D 组组件清单
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Design Direction] — Pencil 范式 #8 节点学习档案面板
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#User Journey Flows, 旅程 6] — 查看学习档案用户旅程
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#UX Consistency Patterns] — 面板切换/按钮层级/空状态
- [Source: _bmad-output/planning-artifacts/prd.md#FR-TRACE-01~05] — FR 定义
- [Source: _bmad-output/planning-artifacts/prd.md#FR-EXAM-17] — 单节点考察入口
- [Source: _bmad-output/planning-artifacts/prd.md#FR-MAST-03] — 处方性精通度展示
- [Source: _bmad-output/implementation-artifacts/5-1-bkt-fsrs-mastery-system.md] — ConceptState、5 级分级、FSRS Card 数据结构
- [Source: _bmad-output/implementation-artifacts/5-2-node-color-mastery-visualization.md] — mastery-state Store、CSS 变量、NodeColorIndicator

## Dev Agent Record

### Agent Model Used

(to be filled during implementation)

### Debug Log References

### Completion Notes List

### File List
