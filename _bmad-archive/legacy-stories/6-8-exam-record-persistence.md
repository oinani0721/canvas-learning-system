# Story 6.8: 考察记录永久保存

Status: ready-for-dev

## Story

As a 用户,
I want 每次检验白板的完整考察记录永久保存，可在 Dashboard 查看历史，
so that 我能回顾过去的考察表现和进步轨迹。

## Acceptance Criteria

1. **AC-1: 完整考察记录保存（FR-EXAM-20）**
   - **Given** 考察结束（用户选择"休息" / 自然结束 / 手动关闭检验白板）
   - **When** 考察记录保存流程触发
   - **Then** 完整记录永久保存到后端，包含：
     - **考察元数据**：exam_id, source_canvas_id, exam_mode, start_time, end_time, duration（活跃时间）
     - **考察对话**：所有对话消息（问题 + 回答 + 提示 + Agent 反馈）
     - **评分历史**：每个节点的 AutoSCORE 4 维评分 + grade + 信心度 + 提示使用情况
     - **精通度变化**：每个节点考察前后的 effective_proficiency 对比
     - **新发现节点**：discoveredNodes 列表（含递归深度和来源）
     - **跳过的节点**：skipped_nodes 列表
   - **And** 记录存储在 SQLite（exam_records 表）+ Neo4j（ExamSession 节点关联）
   - **And** 记录不可删除（永久保存）

2. **AC-2: Dashboard 历史检验白板列表（FR-DASH-02, FR-DASH-04）**
   - **Given** 用户打开 Dashboard
   - **When** DashboardView 加载
   - **Then** "检验白板"区域展示所有历史检验白板列表
   - **And** 每条记录显示：
     - 原白板名称
     - 考察模式（点对点/综合题/混合）
     - 考察日期
     - 考察时长
     - 考察节点数
     - 整体精通度变化趋势（上升↑ / 下降↓ / 持平-）
   - **And** 列表按时间倒序排列（最近的在前）
   - **And** 点击可展开查看完整考察记录

3. **AC-3: 查看完整考察记录详情（FR-DASH-04）**
   - **Given** 用户在 Dashboard 点击某条历史检验白板
   - **When** 详情展开/面板切换
   - **Then** ExamRecord 组件展示完整考察记录：
     - **概览区**：考察模式、时长、考察节点数、新发现节点数
     - **节点评分列表**：每个考察节点的 4 维评分 + 精通度变化
     - **对话回放区**：可折叠的考察对话（按节点分组）
     - **新发现节点**：递归发现链（节点 A → 发现 B → 发现 C）
     - **进步对比**：与上次同白板考察的精通度对比（如有）
   - **And** 对话回放区默认折叠，点击节点名称展开

4. **AC-4: ExamRecord Svelte 组件**
   - **Given** 需要展示考察记录详情
   - **When** ExamRecord.svelte 渲染
   - **Then** 概览区使用卡片布局（4 个关键指标）
   - **And** 节点评分列表使用表格布局（节点名 | 4 维分数 | grade | 精通度变化）
   - **And** 对话回放区使用折叠列表
   - **And** 新发现节点使用树形/链式布局展示递归关系
   - **And** CSS 使用 `cl-exam-record-*` 前缀，适配 Light/Dark 主题

5. **AC-5: ExamCard Dashboard 组件**
   - **Given** Dashboard 展示检验白板列表
   - **When** ExamCard.svelte 渲染
   - **Then** 每条 ExamCard 展示：原白板名称、模式图标、日期、时长、节点数、趋势箭头
   - **And** 点击展开详情或切换到 ExamRecord 视图
   - **And** CSS 使用 `cl-dash-exam-*` 前缀

6. **AC-6: 原白板历史检验白板关联（FR-DASH-04）**
   - **Given** 用户在 Dashboard 查看某个原白板
   - **When** 展开原白板的详情
   - **Then** 显示该原白板的所有历史检验白板列表
   - **And** 列表包含：时间、考察模式、掌握度变化、考察节点数
   - **And** 可直观看到多次考察的进步轨迹

7. **AC-7: 后端考察记录 API**
   - **Given** 后端 FastAPI 运行
   - **When** 调用考察记录相关 API
   - **Then** 以下端点正常工作：
     - `POST /api/v1/exam/{exam_id}/complete` — 保存完整考察记录
     - `GET /api/v1/exam/records` — 获取所有历史考察记录（分页）
     - `GET /api/v1/exam/records/{exam_id}` — 获取单条考察记录详情
     - `GET /api/v1/exam/records/by-canvas/{canvas_id}` — 获取原白板的考察历史
   - **And** 返回数据包含所有 AC-1 定义的字段
   - **And** 对话回放数据可选按需加载（减少列表查询负担）

8. **AC-8: 考察结束触发流程**
   - **Given** 考察以任何方式结束
   - **When** 结束事件触发
   - **Then** 以下流程自动执行：
     - 1. 对未评分的最后一个节点执行 AutoSCORE（如有未完成的对话）
     - 2. 聚合所有评分数据 + 发现节点 + 跳过节点
     - 3. 计算活跃考察时长
     - 4. 调用 `POST /api/v1/exam/{exam_id}/complete` 保存记录
     - 5. exam-state 更新为 completed
     - 6. 提示用户"考察记录已保存，可在 Dashboard 查看"

## Tasks / Subtasks

- [ ] **Task 1: 后端考察记录保存** (AC: #1, #7)
  - [ ] 1.1 在 `backend/app/services/exam_service.py` 中实现 complete_exam() 方法
  - [ ] 1.2 创建 SQLite exam_records 表 schema（exam_models.py 扩展）
  - [ ] 1.3 实现 4 个 API 端点：complete / records / records/{id} / records/by-canvas/{id}
  - [ ] 1.4 对话回放数据序列化存储
  - [ ] 1.5 编辑后运行 `ruff check` + `ruff format --check`

- [ ] **Task 2: ExamCard Dashboard 组件** (AC: #2, #5)
  - [ ] 2.1 创建 `src/components/dashboard/ExamCard.svelte`
  - [ ] 2.2 展示考察摘要信息（原白板名、模式、日期、时长、节点数、趋势）
  - [ ] 2.3 点击展开详情交互
  - [ ] 2.4 CSS cl-dash-exam-* 前缀

- [ ] **Task 3: ExamRecord 详情组件** (AC: #3, #4)
  - [ ] 3.1 创建 `src/components/exam/ExamRecord.svelte`
  - [ ] 3.2 实现概览区：4 个关键指标卡片
  - [ ] 3.3 实现节点评分列表：表格布局
  - [ ] 3.4 实现对话回放区：折叠列表
  - [ ] 3.5 实现新发现节点：树形/链式布局
  - [ ] 3.6 CSS cl-exam-record-* 前缀 + Light/Dark 适配

- [ ] **Task 4: Dashboard 集成** (AC: #2, #6)
  - [ ] 4.1 在 DashboardView 中添加"检验白板"列表区域
  - [ ] 4.2 从后端加载历史考察记录
  - [ ] 4.3 实现原白板 → 历史检验白板关联展示
  - [ ] 4.4 列表分页加载

- [ ] **Task 5: 考察结束流程** (AC: #8)
  - [ ] 5.1 实现考察结束触发逻辑（休息 / 自然结束 / 手动关闭）
  - [ ] 5.2 最后一个节点未评分时自动触发 AutoSCORE
  - [ ] 5.3 聚合数据 + 计算时长 + 调用 complete API
  - [ ] 5.4 显示保存成功提示

- [ ] **Task 6: 端到端验证** (AC: #1-#8)
  - [ ] 6.1 测试：完整考察流程 → 结束 → 记录保存成功
  - [ ] 6.2 测试：Dashboard 显示历史记录列表
  - [ ] 6.3 测试：点击记录 → 展示完整详情
  - [ ] 6.4 测试：同一原白板多次考察 → 进步轨迹可见

## Dev Notes

### 架构定位

本 Story 是检验白板的收尾层——确保考察数据永久保存可回溯。它是用户"感知进步"的关键支撑。

### 依赖关系

- **依赖 Story 6.1**：exam_service + exam-state 基础框架
- **依赖 Story 6.4**：AutoSCORE 评分数据
- **依赖 Story 6.5**：discoveredNodes 新发现节点数据
- **依赖 Story 6.6**：hint_usage + skipped_nodes 数据
- **依赖 Story 6.7**：考察时长（活跃时间）+ "休息"触发结束
- **依赖 Story 5.4**：DashboardView 基础组件

### 存储策略

- **SQLite**：考察记录主存储（exam_records 表），适合结构化查询和分页
- **Neo4j**：ExamSession 节点关联到 SourceCanvas 和 ExaminedNode，支持图遍历查询
- **IndexedDB**：前端缓存最近 N 条考察记录，支持离线查看

### 数据不可删除原则

考察记录永久保存，不提供删除功能：
- 学习轨迹是长期积累的数据，删除会丢失进步信号
- BKT/FSRS 的历史准确性依赖完整的考察记录链
- Hot-Warm-Cold 归档策略可自动管理存储空间

### Project Structure Notes

- ExamRecord 在 `src/components/exam/` 目录（B 组）
- ExamCard 在 `src/components/dashboard/` 目录（C 组）
- 后端 API 在 `backend/app/api/v1/endpoints/exam.py` 中追加
- CSS 类名前缀 `cl-exam-record-*` / `cl-dash-exam-*`

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story6.8] — AC 原文
- [Source: _bmad-output/planning-artifacts/prd.md#能力域4] — FR-EXAM-20
- [Source: _bmad-output/planning-artifacts/prd.md#能力域10] — FR-DASH-02/04
- [Source: _bmad-output/planning-artifacts/architecture.md#Structure Patterns] — 后端目录结构
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Component Strategy] — B 组 ExamRecord + C 组 ExamCard
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#旅程2] — 考察结束 → 记录保存 → Dashboard 可查
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#情感设计原则] — "进步可见"

## Dev Agent Record

### Agent Model Used

(待开发时填写)

### Debug Log References

(待开发时填写)

### Completion Notes List

(待开发时填写)

### File List

- `src/components/exam/ExamRecord.svelte` — 新建
- `src/components/dashboard/ExamCard.svelte` — 新建
- `backend/app/services/exam_service.py` — 修改（添加 complete_exam + 记录查询）
- `backend/app/api/v1/endpoints/exam.py` — 修改（添加 4 个记录 API 端点）
- `backend/app/models/exam_models.py` — 修改（添加 ExamRecord 完整模型）
- `src/components/dashboard/DashboardView.svelte` — 修改（添加检验白板列表区域）
