---
story_id: "5.4"
epic_id: "5"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P0"
estimate_hours: 8
depends_on: ["5.3"]
blocks: []
trace:
  - "FR-MAST-04"
---

# Story 5.4: 评分操作链完整性（Pipeline Token 5 步链）

Status: ready-for-dev

## Story
As a 系统,
I want 保证评分操作链的 5 步顺序不可跳步（generate → score → BKT → FSRS → calibration）,
So that 算法管道不被篡改、每次考察数据完整流经全部处理环节（AR8 架构规则）。

## Acceptance Criteria

1. **Given** `generate_question` MCP 工具被调用 **When** 成功生成题目 **Then** 返回 `pipeline_token_A`（HMAC-SHA256 签名，step="generate_question"）**And** token 包含 session_id、node_id、question_id、timestamp、expires_at **And** token 有效期 300 秒

2. **Given** `score_answer` MCP 工具被调用 **When** 携带 `pipeline_token_A` **Then** 验证 token 合法且未过期 **And** 验证 step="generate_question" 是 score_answer 的合法前驱 **And** 返回评分结果 + `pipeline_token_B`（step="score_answer"）

3. **Given** `update_bkt` 被调用 **When** 携带 `pipeline_token_B` **Then** 验证 step="score_answer" 是 update_bkt 的合法前驱 **And** 执行 BKT 更新 **And** 返回 `pipeline_token_C`（step="update_bkt"，供 update_fsrs 使用）

4. **Given** `update_fsrs` 被调用 **When** 携带 `pipeline_token_B` 或 `pipeline_token_C` **Then** 验证合法前驱 **And** 执行 FSRS 更新 **And** 返回 `pipeline_token_D`（step="update_fsrs"，供 record_calibration 使用）

5. **Given** `record_calibration` 被调用 **When** 携带 `pipeline_token_D` **Then** 验证合法前驱 **And** 记录校准数据 **And** pipeline 完成（无下游 token）

6. **Given** 任何步骤被调用但 pipeline_token 缺失、过期或不匹配 **When** 后端验证 **Then** 返回 `{"status": "error", "code": "PIPELINE_TOKEN_INVALID"}` **And** 拒绝执行 **And** 审计日志记录跳步尝试（包含 session_id、attempted_step、expected_step）

7. **Given** EventBus 已配置 **When** score_answer 完成 **Then** 发布 `SCORE_SUBMITTED` 事件 **And** EventBus 级联自动触发 BKT_UPDATED → FSRS_UPDATED → CALIBRATION_RECORDED 事件链 **And** 每个事件携带前一步的 pipeline_token

## Tasks / Subtasks

- [ ] Task 1: 扩展 PIPELINE_STEPS 为 5 步链 (AC: #1-#5)
  - [ ] 修改 `backend/app/mcp/pipeline_token.py` 的 PIPELINE_STEPS 字典
  - [ ] 新增步骤定义：`"update_bkt": ["update_fsrs"]`，`"update_fsrs": ["record_calibration"]`
  - [ ] 验证完整链：generate_question → score_answer → update_bkt → update_fsrs → record_calibration
  - [ ] 单元测试：每个合法转移都通过、每个非法转移都拒绝

- [ ] Task 2: 为 update_bkt / update_fsrs / record_calibration 添加 token 生成 (AC: #3, #4, #5)
  - [ ] 各 MCP 工具在成功执行后调用 `PipelineTokenManager.generate_token(step_name)`
  - [ ] 返回新 token 供下游工具使用
  - [ ] record_calibration 作为末端步骤不产生新 token
  - [ ] 单元测试：token 生成和验证的完整链路

- [ ] Task 3: 实现跳步拒绝 + 审计日志 (AC: #6)
  - [ ] 在每个需要 token 的 MCP 工具入口调用 `PipelineTokenManager.validate_token()`
  - [ ] 验证失败时返回标准错误格式 `{"status": "error", "code": "PIPELINE_TOKEN_INVALID"}`
  - [ ] 记录审计日志：`guardian.record_pipeline_violation(session_id, attempted_step, reason)`
  - [ ] 单元测试：伪造 token、过期 token、错误步骤 token 全部拒绝

- [ ] Task 4: EventBus 级联触发 (AC: #7)
  - [ ] 在 `backend/app/services/event_bus.py` 注册级联事件
  - [ ] SCORE_SUBMITTED（Tier1 await）→ 触发 BKT 更新
  - [ ] BKT_UPDATED（Tier2 fire+retry）→ 触发 FSRS 更新 + Graphiti 写入
  - [ ] FSRS_UPDATED → 触发 record_calibration（如有校准数据）
  - [ ] 每个事件 handler 自动传递 pipeline_token
  - [ ] 集成测试：模拟完整的 5 步级联

- [ ] Task 5: 端到端集成测试 (AC: #1-#7)
  - [ ] 测试完整链路：generate_question → 用户答题 → score_answer → BKT → FSRS → calibration
  - [ ] 测试中断场景：在步骤 3 跳到步骤 5（应拒绝）
  - [ ] 测试 token 过期场景：等待 >300s 后使用 token（应拒绝）
  - [ ] 测试 EventBus 级联：仅触发 score_answer，验证后续步骤自动完成

## Dev Notes

### Architecture
- Pipeline Token 是 AR8 架构规则的实现，确保评分链不可篡改
- 现有 `PipelineTokenManager` 已实现 HMAC-SHA256 签名和 3 步链（generate → score → [fsrs, bkt]）
- 本 Story 扩展为 5 步链，增加 update_bkt → update_fsrs → record_calibration 的顺序约束
- BKT 和 FSRS 在现有代码中是 score_answer 的并行后继（`"score_answer": ["update_fsrs", "update_bkt"]`）——本 Story 将其改为串行链以确保数据一致性
- EventBus 级联保证即使 skill 没有显式调用后续步骤，系统也会自动完成

### File Paths
- Pipeline token 管理：`backend/app/mcp/pipeline_token.py` (PipelineTokenManager, PIPELINE_STEPS)
- EventBus：`backend/app/services/event_bus.py` (EventBus)
- MCP 工具：`backend/app/mcp/tools/mastery_tools.py`（update_bkt, update_fsrs）
- MCP 工具：`backend/app/mcp/tools/memory_tools.py`（record_calibration）
- MCP 工具：`backend/app/mcp/tools/exam_tools.py`（generate_question, score_answer）
- 审计守卫：`backend/app/audit/guardian.py`

### Testing
- 单元测试：PIPELINE_STEPS 合法/非法转移矩阵
- 单元测试：token 生成 → 验证 → 过期
- 集成测试：完整 5 步链端到端
- 集成测试：EventBus 级联自动触发
- 安全测试：伪造 token、重放 token

### References
- **From PRD**: FR-MAST-04 评分操作链不可跳步
- `backend/app/mcp/pipeline_token.py`: 现有 3 步链实现
- `backend/app/services/event_bus.py`: EventBus 三层优先级（Tier1 await/Tier2 fire+retry/Tier3 fire-and-forget）
- Architecture doc: 评分完成流（line 902-910）

## UAT Script

> 1. 触发考察，确认 generate_question 返回 pipeline_token
> 2. 提交答案，确认 score_answer 消费 token 并返回新 token
> 3. 观察后端日志，确认 BKT → FSRS → calibration 自动触发
> 4. 尝试直接调用 update_bkt 不带 token，确认被拒绝
> 5. 等待 6 分钟后尝试使用旧 token，确认过期拒绝
> 6. 检查审计日志中记录了跳步/过期尝试

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| PIPELINE_STEPS 5 步链 | unit | `pytest tests/unit/test_pipeline_steps.py -x` | 0 failures |
| Token 生成验证 | unit | `pytest tests/unit/test_pipeline_token.py -x` | 0 failures |
| 跳步拒绝 | unit | `pytest tests/unit/test_pipeline_rejection.py -x` | 0 failures |
| EventBus 级联 | integration | `pytest tests/integration/test_scoring_chain_cascade.py -x` | 0 failures |
| 端到端 5 步链 | integration | `pytest tests/integration/test_pipeline_e2e.py -x` | 0 failures |

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
