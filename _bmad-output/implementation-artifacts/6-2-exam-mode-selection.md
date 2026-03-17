# Story 6.2: 考察模式选择与智能推荐

Status: ready-for-dev

## Story

As a 用户,
I want 选择考察模式（点对点/综合题/混合），系统根据白板内容类型智能推荐，
so that 考察方式匹配我的学习内容。

## Acceptance Criteria

1. **AC-1: 三种考察模式展示（FR-EXAM-11）**
   - **Given** 用户启动检验白板考察（Story 6.1 AC-1 触发后）
   - **When** ExamModeSelector 面板弹出（Obsidian Modal）
   - **Then** 显示三种模式供选择：
     - **点对点突破**：逐知识点考察，适合检验单个概念的理解深度
     - **综合题考察**：跨概念整合题，适合检验知识间的联系和应用
     - **混合模式**：先点对点找弱点，再综合题验证整合能力
   - **And** 每种模式附带简洁的一句话说明（用户可理解的语言，非术语）
   - **And** 系统推荐的模式高亮标记"推荐"标签

2. **AC-2: 内容类型自动映射与智能推荐（FR-EXAM-12）**
   - **Given** 原白板有节点内容数据
   - **When** ExamModeSelector 加载时分析原白板内容类型
   - **Then** 根据 Constructive Alignment（Biggs 1996）原则自动推荐：
     - 知识点白板（节点内容主要为定义/概念/解释）→ 推荐"点对点突破"
     - 题目白板（节点内容主要为习题/案例/公式推导）→ 推荐"综合题考察"
     - 混合内容白板 → 推荐"混合模式"
   - **And** 内容类型分析通过后端 `POST /api/v1/exam/analyze-canvas` 接口执行
   - **And** 分析结果包含：content_type（knowledge / problem / mixed）、推荐模式、置信度

3. **AC-3: 用户可手动覆盖推荐（FR-EXAM-12）**
   - **Given** 系统已显示推荐模式
   - **When** 用户点击非推荐的模式
   - **Then** 用户选择生效，覆盖系统推荐
   - **And** 不弹出确认对话框（尊重用户选择，不增加操作摩擦）
   - **And** 用户选择后点击"开始考察"按钮确认，进入检验白板

4. **AC-4: ExamModeSelector Svelte 组件**
   - **Given** 前端需要展示模式选择 UI
   - **When** ExamModeSelector.svelte 组件渲染
   - **Then** 使用 Obsidian Modal API 创建模态框
   - **And** 三种模式以卡片形式展示，点击选中高亮
   - **And** 推荐模式带 accent 色"推荐"标签
   - **And** 底部"开始考察"按钮（主操作样式）+ "取消"文字按钮
   - **And** CSS 使用 `cl-exam-mode-*` 前缀，适配 Light/Dark 主题
   - **And** Escape 键关闭 Modal

5. **AC-5: 模式选择结果写入 exam-state**
   - **Given** 用户选择模式并点击"开始考察"
   - **When** 确认操作执行
   - **Then** exam-state.examMode 更新为用户选择的模式
   - **And** 后端 `PATCH /api/v1/exam/{exam_id}/status` 更新 exam_session 的 mode 字段
   - **And** ChatPanel 根据 examMode 调整考察行为（传递给 Agent 的 prompt 层级 2）

6. **AC-6: 学习档案面板考察入口复用（FR-EXAM-17）**
   - **Given** 用户从学习档案面板（Story 5.3 AC-6）点击"开始考察"
   - **When** 单节点考察入口触发
   - **Then** 同样弹出 ExamModeSelector 面板
   - **And** 考察范围限于该节点（exam_session 记录 target_node_id）
   - **And** 内容类型分析基于该单节点内容进行推荐

## Tasks / Subtasks

- [ ] **Task 1: ExamModeSelector Svelte 组件** (AC: #1, #4)
  - [ ] 1.1 创建 `src/components/exam/ExamModeSelector.svelte`：三种模式卡片布局
  - [ ] 1.2 实现模式选中高亮交互（点击切换、推荐标签）
  - [ ] 1.3 使用 Obsidian Modal API 包装为模态框
  - [ ] 1.4 实现"开始考察"确认按钮和"取消"按钮
  - [ ] 1.5 CSS cl-exam-mode-* 前缀 + Light/Dark 适配

- [ ] **Task 2: 后端内容类型分析接口** (AC: #2)
  - [ ] 2.1 在 `backend/app/services/exam_service.py` 中添加 analyze_canvas_content() 方法
  - [ ] 2.2 实现内容类型分类逻辑：分析节点文本特征（定义/公式/题目关键词比例）
  - [ ] 2.3 创建 `POST /api/v1/exam/analyze-canvas` 端点
  - [ ] 2.4 返回 content_type + recommended_mode + confidence
  - [ ] 2.5 编辑后运行 `ruff check` + `ruff format --check`

- [ ] **Task 3: 模式选择结果写入** (AC: #3, #5)
  - [ ] 3.1 ExamModeSelector 选择后调用 exam-state.setExamMode(mode)
  - [ ] 3.2 同步更新后端 exam_session 的 mode 字段
  - [ ] 3.3 examMode 传递给 ChatPanel 作为 prompt 第 2 层模式指令

- [ ] **Task 4: 学习档案面板入口集成** (AC: #6)
  - [ ] 4.1 复用 ExamModeSelector 组件，传入 targetNodeId prop
  - [ ] 4.2 单节点考察时 exam_session 记录 target_node_id
  - [ ] 4.3 内容类型分析基于单节点内容

## Dev Notes

### 架构定位

本 Story 在 Story 6.1 的检验白板框架上添加模式选择层，为后续 Story 6.3（AI 出题）提供模式参数。

### 依赖关系

- **依赖 Story 6.1**：ExamCanvas + exam-state + exam_service 基础框架
- **依赖 Story 5.3**：学习档案面板的"开始考察"按钮（FR-EXAM-17 第二入口）
- **被 Story 6.3 依赖**：AI 出题需要 examMode 参数决定 Prompt 第 2 层策略

### Constructive Alignment 原则

John Biggs (1996) 提出教学设计中学习目标、教学活动和评估方式需一致对齐。应用于此场景：
- 知识点白板的学习目标是"理解概念" → 评估方式应为"逐点考察"
- 题目白板的学习目标是"应用知识" → 评估方式应为"综合整合题"
- 混合白板 → 先找弱点再综合验证

### 内容类型分析策略

后端 analyze_canvas_content() 使用简单关键词+结构特征分析（非 LLM 调用）：
- 定义类信号：包含"是"/"定义为"/"概念"等
- 题目类信号：包含"求"/"证明"/"计算"/"例题"/"解"等
- 公式类信号：LaTeX 标记 `$...$` 占比
- 根据信号比例判断 knowledge / problem / mixed

### Project Structure Notes

- ExamModeSelector 在 `src/components/exam/` 目录（B 组）
- 后端分析接口在 `backend/app/api/v1/endpoints/exam.py` 中追加
- CSS 类名前缀 `cl-exam-mode-*`

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story6.2] — AC 原文
- [Source: _bmad-output/planning-artifacts/prd.md#能力域4] — FR-EXAM-11/12/13/17
- [Source: _bmad-output/planning-artifacts/architecture.md#Frontend Architecture] — ChatPanel 三模式复用
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Component Strategy] — ExamModeSelector B 组组件
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#旅程2] — 考察模式选择步骤
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Pencil范式覆盖] — 场景 15 考察模式选择面板

## Dev Agent Record

### Agent Model Used

(待开发时填写)

### Debug Log References

(待开发时填写)

### Completion Notes List

(待开发时填写)

### File List

- `src/components/exam/ExamModeSelector.svelte` — 新建
- `backend/app/services/exam_service.py` — 修改（添加 analyze_canvas_content）
- `backend/app/api/v1/endpoints/exam.py` — 修改（添加 analyze-canvas 端点）
- `src/stores/exam-state.svelte.ts` — 修改（添加 setExamMode 方法）
