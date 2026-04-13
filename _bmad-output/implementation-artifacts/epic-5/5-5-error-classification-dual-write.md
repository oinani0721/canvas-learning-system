---
story_id: "5.5"
epic_id: "5"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P0"
estimate_hours: 8
depends_on: ["4.6"]
blocks: ["5.7", "5.8"]
trace:
  - "FR-MEM-01"
---

# Story 5.5: 错误 4 类分类双写

Status: ready-for-dev

## Story
As a 系统,
I want 记录学习者的错误并按 4 类分类存储到 frontmatter errors[] 和 Graphiti 知识图谱（双写）,
So that 个人化出题能基于错误模式差异化补救（AR3 差异化补救路由）。

## Acceptance Criteria

1. **Given** 对话或考察中 Agent 检测到学习者理解错误 **When** 调用 `record_error` MCP 工具 **Then** 错误自动分类为 4 主类之一：`problem_framing`（破题错误）/ `reasoning_fallacy`（推理谬误）/ `knowledge_gap`（知识点缺失）/ `superficial`（似懂非懂）**And** 分类置信度 >= 0.6 时记录，< 0.6 时标记为 "uncertain" 并仍记录

2. **Given** 错误分类完成 **When** 系统执行双写 **Then** 写入路径 1：frontmatter `errors[]` 数组追加 `{error_type, description, session_id, timestamp, confidence}` **And** 写入路径 2：Graphiti 知识图谱创建 Misconception entity（关联 node_id）**And** 两个写入在同一事务中执行

3. **Given** 双写过程中 Graphiti 写入失败 **When** frontmatter 写入已成功 **Then** 回滚 frontmatter 写入（恢复到写入前状态）**And** 整体标记为失败 **And** 记录到 `FAILED_WRITES_FILE` 审计日志 **And** 不产生半截数据（NFR-INT 原子性）

4. **Given** 双写过程中 frontmatter 写入失败 **When** Graphiti 尚未写入 **Then** 跳过 Graphiti 写入 **And** 整体标记为失败 **And** 返回 `{"recorded": false, "status": "error", "message": "frontmatter write failed"}`

5. **Given** 错误已记录 **When** 下游出题系统（Story 4.3）读取错误历史 **Then** 按 4 类差异化补救路由（AR3）：`problem_framing` → 强调审题策略，`reasoning_fallacy` → 逻辑链练习，`knowledge_gap` → 前置知识复习，`superficial` → 应用场景变式题

6. **Given** 同一概念多次记录同类型错误 **When** 系统查询错误历史 **Then** 返回按时间排序的错误列表 **And** 包含每类错误的出现次数统计 **And** 支持按 error_type 过滤

## Tasks / Subtasks

- [ ] Task 1: 验证 ErrorClassifier 4 类分类准确性 (AC: #1)
  - [ ] 确认 `backend/app/services/error_classifier.py` 的 4 类分类逻辑
  - [ ] 分类器支持 LLM 分类（主路径）+ 关键词回退（降级路径）
  - [ ] 置信度 < 0.6 标记 "uncertain" 但仍记录
  - [ ] 单元测试：每类错误各 3 个样本，验证分类正确

- [ ] Task 2: 实现 frontmatter errors[] 双写 (AC: #2)
  - [ ] 在 `record_error` 工具中添加 frontmatter 写入逻辑
  - [ ] errors[] 数组元素 schema：`{error_type: str, description: str, session_id: str, timestamp: str, confidence: float}`
  - [ ] 使用原子写入模式（读 → 修改 → 写临时文件 → rename）
  - [ ] 单元测试：写入后 errors[] 正确追加

- [ ] Task 3: 实现原子性双写事务 (AC: #2, #3, #4)
  - [ ] 实现 `dual_write_error(node_id, error_data)` 协调函数
  - [ ] 步骤 1：frontmatter 写入（保存回滚快照）
  - [ ] 步骤 2：Graphiti Misconception entity 写入
  - [ ] 步骤 2 失败时：回滚步骤 1（恢复 frontmatter 快照）
  - [ ] 步骤 1 失败时：跳过步骤 2
  - [ ] 失败记录到 `FAILED_WRITES_FILE`（`backend/app/core/failed_writes_constants.py`）
  - [ ] 集成测试：模拟 Graphiti 失败 → frontmatter 回滚

- [ ] Task 4: 实现错误历史查询 + AR3 补救路由 (AC: #5, #6)
  - [ ] 在 `record_error` 返回值中添加 `remedy_strategy` 和 `remedy_description`
  - [ ] 验证 `question_generator.py` 的 MathCCS 4-type 补救映射（line 329-394）
  - [ ] 实现 `get_error_history(node_id, error_type=None)` 查询函数
  - [ ] 返回按时间排序的错误列表 + 各类型计数统计
  - [ ] 单元测试：多次记录后查询正确

- [ ] Task 5: MCP 工具集成 + 端到端测试 (AC: #1-#6)
  - [ ] 验证 `record_error` 已在 `backend/app/mcp/server.py` 注册
  - [ ] 端到端测试：Agent 检测错误 → 分类 → 双写 → 查询 → 补救路由
  - [ ] 测试 Graphiti 不可用时的降级行为

## Dev Notes

### Architecture
- 错误分类使用 MathCCS 框架的 4 类分类法：problem_framing / reasoning_fallacy / knowledge_gap / superficial
- 现有 `ErrorClassifier`（error_classifier.py）已实现 LLM 分类 + 关键词回退
- 现有 `record_error` MCP 工具（error_tools.py）已实现 Graphiti 写入——本 Story 新增 frontmatter 双写
- 原子性双写是 NFR-INT 的核心要求：Graphiti 和 frontmatter 必须同时成功或同时失败
- AR3 差异化补救路由在 `question_generator.py` 的 `_build_remediation_prompt()` 中已有映射

### File Paths
- 错误分类器：`backend/app/services/error_classifier.py` (ErrorClassifier)
- 错误工具：`backend/app/mcp/tools/error_tools.py` (record_error)
- 错误类型定义：`backend/app/graphiti/entity_types.py` (ErrorType enum)
- 补救路由：`backend/app/services/question_generator.py` (line 329-394, _build_remediation_prompt)
- 失败写入审计：`backend/app/core/failed_writes_constants.py` (FAILED_WRITES_FILE)
- MCP server：`backend/app/mcp/server.py` (line 437-448)

### Testing
- 单元测试：4 类分类准确性、frontmatter 写入、原子性回滚
- 集成测试：双写事务（成功/Graphiti 失败/frontmatter 失败）
- 端到端测试：完整的错误检测 → 分类 → 存储 → 查询 → 补救链路

### References
- **From PRD**: FR-MEM-01 错误 4 类分类双写
- MathCCS 框架：4 类错误分类法
- `backend/app/services/error_classifier.py`: LLM 分类 prompt (line 43-50)
- `backend/app/services/question_generator.py`: AR3 补救路由映射

## UAT Script

> 1. 在对话中故意给出一个概念混淆的回答
> 2. 观察 Agent 调用 record_error
> 3. 检查笔记 frontmatter，确认 errors[] 新增一条记录
> 4. 检查记录的 error_type 是否为 4 类之一
> 5. 触发考察，确认出题时考虑了错误历史（题目针对该类错误）
> 6. 在另一个概念上重复步骤 1-4，确认错误独立记录

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| 4 类分类 | unit | `pytest tests/unit/test_error_classifier.py -x` | 0 failures |
| frontmatter errors[] | unit | `pytest tests/unit/test_error_frontmatter.py -x` | 0 failures |
| 原子性双写 | integration | `pytest tests/integration/test_error_dual_write.py -x` | 0 failures |
| Graphiti 失败回滚 | integration | `pytest tests/integration/test_error_rollback.py -x` | 0 failures |
| AR3 补救路由 | unit | `pytest tests/unit/test_remedy_routing.py -x` | 0 failures |

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
