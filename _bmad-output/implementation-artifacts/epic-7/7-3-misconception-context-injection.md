---
story_id: "7.3"
epic_id: "7"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P1"
estimate_hours: 6
depends_on: ["7.2", "5.7"]
blocks: ["7.4"]
trace:
  - "FR-SPACE-02"
---

# Story 7.3: 复习时误解上下文注入

Status: ready-for-dev

## Story
As a 系统,
I want 复习时自动注入历史误解上下文,
So that AI 能针对性帮助学习者纠正过去的错误理解，而非泛泛复习。

## Acceptance Criteria

1. **Given** 学习者响应 Day 3/Day 7 提醒进入复习流程 **When** 系统准备 AI 对话上下文 **Then** 通过 3 层记忆检索（Story 5.7）获取该概念的历史误解记录 **And** 检索范围包含 Graphiti facts（错误分类 4 类）+ LanceDB 向量（相似错误）+ frontmatter（error_history 数组）

2. **Given** 3 层记忆检索返回了历史误解数据 **When** 系统组装 AI prompt context **Then** 误解信息以结构化格式注入：`[历史误解] 概念: X · 错误类型: Y · 原始回答摘要: Z · 标记日期: D` **And** 每个概念最多注入 3 条最近的误解记录（防止 context 膨胀）

3. **Given** AI 收到注入的误解上下文 **When** AI 生成复习引导对话 **Then** AI 自然地将误解信息融入对话（"上次你提到 X 时有个理解偏差..."）**And** 不生硬地列举错误记录 **And** AI prompt 包含指令"以引导纠正的语气提及历史误解，不要指责"

4. **Given** 该概念没有历史误解记录 **When** 系统检索返回空 **Then** 跳过误解注入环节 **And** AI 按普通复习模式进行（不提及误解）**And** 不显示"无历史误解"的冗余信息

5. **Given** Graphiti 服务不可用 **When** 系统尝试 3 层检索 **Then** 降级到 frontmatter `error_history` 数组作为唯一误解来源 **And** 日志记录降级事件 **And** AI 仍能基于 frontmatter 数据进行有针对性的复习

## Tasks / Subtasks

- [ ] Task 1: 实现复习上下文的 3 层误解检索 (AC: #1)
  - [ ] 在 `backend/app/services/context_enrichment_service.py` 中添加 `retrieve_misconception_context` 方法
  - [ ] Layer 1: Graphiti search_memory_facts 查询该概念的 error_classification facts
  - [ ] Layer 2: LanceDB 向量检索相似错误模式
  - [ ] Layer 3: frontmatter error_history 数组直接读取
  - [ ] 三层结果去重合并，按日期降序排列

- [ ] Task 2: 实现误解数据格式化与注入 (AC: #2)
  - [ ] 将检索结果格式化为结构化 context 块
  - [ ] 截取最近 3 条（防止 context window 膨胀）
  - [ ] 注入位置：system prompt 的 `[REVIEW_CONTEXT]` 占位符
  - [ ] 单元测试：格式化输出正确 + 截取逻辑正确

- [ ] Task 3: 实现 AI prompt 的自然融入指令 (AC: #3)
  - [ ] 在 skill prompt 模板中添加复习模式指令
  - [ ] 指令要求"以引导纠正的语气"、"不指责"、"自然融入对话"
  - [ ] 提供 few-shot 示例：好的融入方式 vs 生硬列举方式

- [ ] Task 4: 实现空数据和降级处理 (AC: #4, #5)
  - [ ] 空检索结果时跳过注入，不影响正常复习流程
  - [ ] Graphiti 不可用时 fallback 到 frontmatter 数据
  - [ ] 单元测试：各种降级路径正常工作

## Dev Notes

### Architecture
- 误解上下文注入是间隔复习闭环的"精准打击"机制，确保复习不是泛泛重读而是针对具体错误
- 3 层检索复用 Story 5.7 的记忆检索架构，此处特化为只检索 error_classification 类型数据
- context 注入在 AI prompt 组装阶段完成，不修改任何持久化数据

### File Paths
- 上下文组装：`backend/app/services/context_enrichment_service.py`
- 错误分类查询：`backend/app/services/error_classification_service.py`
- Graphiti 查询：`backend/app/services/graphiti_service.py`（search_memory_facts）
- LanceDB 向量检索：`backend/app/services/rag_service.py`
- Skill prompt 模板：CLAUDE.md skill 定义（`/start_review` 或 `/review_concept`）
- 概念 frontmatter：`wiki/concepts/*.md`（error_history 数组）

### Testing
- 单元测试：3 层检索各层独立测试 + 合并去重测试
- 单元测试：截取逻辑（0/1/3/10 条误解记录时的行为）
- 集成测试：完整复习流程中 AI 收到的 context 包含误解信息

### References
- **From PRD**: §1.8 间隔复习 (line 2824-2932)
- **From PRD**: §8.3 旅程 3 错误修正闭环 (line 7012-7021)
- FR-MEM-04: 3 层记忆检索
- Story 5.7: 3 层记忆检索架构

## UAT Script

> 1. 在考察中故意答错概念 A，确认错误被分类并存储
> 2. 等待或手动设置 Day 3 复习触发
> 3. 进入概念 A 的复习对话
> 4. 确认 AI 对话中自然提及"上次你对 [概念] 的理解有个偏差..."
> 5. 确认 AI 不是生硬列举错误记录，而是融入对话引导
> 6. 对一个从未答错的概念 B 进入复习
> 7. 确认 AI 不提及任何误解，按普通复习模式进行

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| 3 层误解检索 | unit | `pytest tests/unit/test_misconception_retrieval.py -x` | 0 failures |
| 格式化与截取 | unit | `pytest tests/unit/test_misconception_format.py -x` | 0 failures |
| 空数据处理 | unit | `pytest tests/unit/test_misconception_empty.py -x` | 0 failures |
| 降级策略 | unit | `pytest tests/unit/test_misconception_degradation.py -x` | 0 failures |
| AI context 注入 | integration | `pytest tests/integration/test_review_context_injection.py -x` | 0 failures |

## User Feedback & Changes

### Feedback Log
(to be filled during/after implementation)

### Deviation Notes
(to be filled if implementation deviates from spec)

## Dev Agent Record

### Agent Model Used
(to be filled by Dev agent)

### Debug Log References
(to be filled by Dev agent)

### Completion Notes List
(to be filled by Dev agent)

### File List
(to be filled by Dev agent)
