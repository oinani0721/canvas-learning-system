# Story 6.6: 4 级渐进提示与跳过

Status: ready-for-dev

## Story

As a 用户,
I want 答不出来时可以请求提示（从模糊到具体），也可以跳过这题，
so that 考察不会让我卡住。

## Acceptance Criteria

1. **AC-1: 4 级渐进提示（Chain-of-Hints）（FR-EXAM-19）**
   - **Given** 用户在检验白板考察中答不出来
   - **When** 点击"给我提示"按钮
   - **Then** 系统采用 4 级渐进提示（Chain-of-Hints, 2025 验证最优）：
     - **Level 1 方向提示**：指出思考方向，不暴露答案（如"想想这个概念和 X 的关系"）
     - **Level 2 关键词提示**：给出关键术语或概念名称
     - **Level 3 部分框架提示**：给出答案的部分框架或步骤骨架
     - **Level 4 分步脚手架引导**：详细的分步引导，接近完整答案但需用户填补
   - **And** 每次点击"给我提示"升一级
   - **And** 到达 Level 4 后按钮变为不可点击（已用完所有提示）
   - **And** 不提供"直接告诉答案"选项

2. **AC-2: HintButton Svelte 组件**
   - **Given** ChatPanel 处于考察模式
   - **When** 渲染对话输入区域
   - **Then** HintButton 显示在输入框左侧（次操作样式：边框按钮）
   - **And** 按钮文字随级别变化："给我提示 (1/4)" → "继续提示 (2/4)" → ... → "最后提示 (4/4)"
   - **And** Level 4 使用后按钮变为灰色不可点击
   - **And** CSS 使用 `cl-exam-hint-*` 前缀
   - **And** 新题开始时提示级别重置为 Level 1

3. **AC-3: 提示通过 Agent 对话生成**
   - **Given** 用户点击"给我提示"
   - **When** 系统生成提示
   - **Then** 通过 MCP 工具 `request_hint` 调用后端
   - **And** 后端根据当前提示级别 + 题目内容 + ACP 数据包生成对应级别的提示
   - **And** 提示以 Agent 消息形式显示在对话中（融入对话流，不弹窗）
   - **And** 提示生成通过 LLM 调用（使用评分模型配置）
   - **And** 提示级别状态存储在 exam-state 中

4. **AC-4: "跳过这题"选项（FR-EXAM-19）**
   - **Given** 用户在考察中不想回答当前题目
   - **When** 点击"跳过这题"按钮
   - **Then** 标记当前题目为"未作答"（skip 状态）
   - **And** 不惩罚 BKT（p_mastery 不下降——跳过不等于回答错误）
   - **And** FSRS 不更新（不记录评分事件）
   - **And** Agent 切换到下一个考察节点
   - **And** 跳过的节点记录在 exam_session 的 skipped_nodes 中

5. **AC-5: SkipButton Svelte 组件**
   - **Given** ChatPanel 处于考察模式
   - **When** 渲染对话输入区域
   - **Then** SkipButton 显示在输入框左侧，HintButton 旁边（文字操作样式：灰色文字）
   - **And** 按钮文字："跳过这题"
   - **And** 点击后不弹确认框（减少操作摩擦）
   - **And** CSS 使用 `cl-exam-skip-*` 前缀

6. **AC-6: MCP 工具 request_hint 接口**
   - **Given** Agent 需要生成提示
   - **When** 调用 MCP 工具 `request_hint`
   - **Then** 工具参数包含：exam_id, node_id, hint_level (1-4), question_context
   - **And** 返回结果包含：hint_text, current_level, remaining_levels
   - **And** 后端根据 hint_level 选择对应的提示模板 + LLM 生成

7. **AC-7: 提示使用对评分的影响**
   - **Given** 用户使用了提示后回答
   - **When** AutoSCORE 评分
   - **Then** 评分 Prompt 中注入提示使用信息（"学生在回答前使用了 Level X 提示"）
   - **And** 评分考虑提示辅助因素（使用越多提示，同样的回答得分应适当降低）
   - **And** hint_usage 记录在 exam_session 的评分历史中

## Tasks / Subtasks

- [ ] **Task 1: HintButton + SkipButton 组件** (AC: #2, #5)
  - [ ] 1.1 创建 `src/components/exam/HintButton.svelte`：4 级渐进按钮
  - [ ] 1.2 实现按钮文字随级别变化 + Level 4 后不可点击
  - [ ] 1.3 创建 `src/components/exam/SkipButton.svelte`：跳过按钮
  - [ ] 1.4 两个按钮集成到 ChatPanel 考察模式输入区域
  - [ ] 1.5 CSS cl-exam-hint-* / cl-exam-skip-* 前缀 + Light/Dark 适配

- [ ] **Task 2: 后端提示生成服务** (AC: #3, #6)
  - [ ] 2.1 在 `backend/app/services/question_generator.py` 中添加 generate_hint() 方法
  - [ ] 2.2 创建 4 级提示 Prompt 模板：
    - `backend/app/prompts/exam/hint_level1.md` — 方向提示
    - `backend/app/prompts/exam/hint_level2.md` — 关键词提示
    - `backend/app/prompts/exam/hint_level3.md` — 部分框架
    - `backend/app/prompts/exam/hint_level4.md` — 分步脚手架
  - [ ] 2.3 在 MCP Server 中注册 `request_hint` 工具
  - [ ] 2.4 编辑后运行 `ruff check` + `ruff format --check`

- [ ] **Task 3: 跳过逻辑实现** (AC: #4)
  - [ ] 3.1 在 exam_service 中实现 skip_question() 方法
  - [ ] 3.2 跳过时不调用 mastery_engine.record_grade（不惩罚 BKT）
  - [ ] 3.3 记录 skipped_nodes 到 exam_session
  - [ ] 3.4 Agent 切换到下一个考察节点

- [ ] **Task 4: 提示使用与评分关联** (AC: #7)
  - [ ] 4.1 exam-state 记录每个节点的提示使用情况（hint_level_used）
  - [ ] 4.2 AutoSCORE 评分时注入提示使用信息到 Prompt
  - [ ] 4.3 hint_usage 持久化到 exam_session 评分历史

- [ ] **Task 5: 提示级别状态管理** (AC: #1, #3)
  - [ ] 5.1 exam-state 中维护 currentHintLevel 状态（per node）
  - [ ] 5.2 新题开始时重置为 Level 1
  - [ ] 5.3 HintButton 读取 currentHintLevel 更新显示

## Dev Notes

### 架构定位

本 Story 为考察提供辅助交互——提示和跳过。增强用户体验，避免考察因"卡住"而产生挫败感。

### 依赖关系

- **依赖 Story 6.1**：ExamCanvas + exam-state 基础框架
- **依赖 Story 6.3**：出题上下文（提示需要知道题目内容）
- **依赖 Story 6.4**：AutoSCORE（提示使用影响评分）
- **被 Story 6.8 依赖**：提示使用和跳过记录纳入考察记录

### Chain-of-Hints 学术来源

Chain-of-Hints (2025) 验证渐进提示策略最优：
- 从模糊到具体的提示梯度比直接给答案或不给提示效果更好
- 4 级是平衡学习效果和操作负担的最优级数
- 不提供"直接告诉答案"是因为检索练习效应（Karpicke 2011）要求学生主动回忆

### BKT 不惩罚跳过的理据

跳过不等于回答错误：
- 回答错误 → BKT 降低 p_mastery（有证据表明不会）
- 跳过 → 无证据，保持 p_mastery 不变（宁缺毋滥）
- FSRS 同理：无评分事件 → 不更新记忆调度

### Project Structure Notes

- HintButton / SkipButton 在 `src/components/exam/` 目录（B 组）
- 提示 Prompt 模板在 `backend/app/prompts/exam/` 目录
- MCP 工具 request_hint 在 `backend/app/mcp/server.py` 中注册

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story6.6] — AC 原文
- [Source: _bmad-output/planning-artifacts/prd.md#能力域4] — FR-EXAM-19
- [Source: _bmad-output/planning-artifacts/architecture.md#Process Patterns] — 错误处理分层
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Component Strategy] — B 组 HintButton / SkipButton
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#按钮层级] — 次操作/文字操作样式
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#旅程2] — 渐进提示步骤

## Dev Agent Record

### Agent Model Used

(待开发时填写)

### Debug Log References

(待开发时填写)

### Completion Notes List

(待开发时填写)

### File List

- `src/components/exam/HintButton.svelte` — 新建
- `src/components/exam/SkipButton.svelte` — 新建
- `backend/app/services/question_generator.py` — 修改（添加 generate_hint）
- `backend/app/prompts/exam/hint_level1.md` — 新建
- `backend/app/prompts/exam/hint_level2.md` — 新建
- `backend/app/prompts/exam/hint_level3.md` — 新建
- `backend/app/prompts/exam/hint_level4.md` — 新建
- `backend/app/mcp/server.py` — 修改（注册 request_hint 工具）
- `src/stores/exam-state.svelte.ts` — 修改（添加 currentHintLevel / skippedNodes）
- `backend/app/models/exam_models.py` — 修改（添加 hint_usage / skipped_nodes 字段）
