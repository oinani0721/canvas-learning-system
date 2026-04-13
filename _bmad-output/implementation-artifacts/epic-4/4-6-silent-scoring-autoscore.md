---
story_id: "4.6"
epic_id: "4"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P0"
estimate_hours: 12
depends_on: ["4.5"]
blocks: ["4.9", "4.10"]
trace:
  - "FR-EXAM-04"
  - "FR-EXAM-06"
  - "FR-EXAM-16"
---

# Story 4.6: 静默评分 + AutoSCORE 两阶段评分

Status: ready-for-dev

## Story
As a 系统,
I want 对学习者的回答静默评分,
So that 评分过程不打断学习 Flow（§1.6 Flow State 保护）。

## Acceptance Criteria

1. **Given** Story 4.5 提取到学习者答案 **When** `/quiz_answer` sub-skill 调用 `score_answer` MCP 工具 **Then** 执行 AutoSCORE 两阶段评分：
   - 阶段 1: 证据提取（从答案中提取与 expected_elements 对应的证据点）
   - 阶段 2: 4 维 4 分制评分（概念准确 / 推理质量 / 知识覆盖 / 知识整合），每维 0-3 分
   **And** 采用 3 样本多数投票（AR4 机制）确保评分一致性

2. **Given** AutoSCORE 评分完成 **When** 系统处理评分结果 **Then** 学习者完全不感知评分过程（完全静默）**And** Claudian sidebar 不显示分数 **And** exam_boards/*.md body 不追加评分信息 **And** 不弹出 toast 通知 **And** 分数只写入 frontmatter 的 `questions[].score` 字段

3. **Given** 评分结果写入 frontmatter **When** sub-skill 继续 pipeline_token 链 **Then** 调用 `update_bkt(node_id, grade=avg_score, pipeline_token=token_B)` → 获得 token_C **And** 调用 `update_fsrs(node_id, answer_quality, pipeline_token=token_C)` → 获得 token_D **And** 更新 wiki/concepts/<slug>.md 的 frontmatter（bkt_p_mastery / fsrs_stability 等）**And** pipeline_token 链（AR8）完整传递不中断

4. **Given** 学习者在考察中切换节点（从 Q1 节点到 Q2 节点）**When** 切换被检测到 **Then** 系统自动触发后台评分（FR-EXAM-16 隐式评分）**And** 评分完全静默，学习者不感知 **And** 切换前的答案被自动提取并评分

5. **Given** score_answer MCP 工具接收到 pipeline_token **When** 验证 token **Then** token 必须由同一 session 的 generate_question 生成 **And** token 未过期（5 分钟有效窗口）**And** token 步骤顺序正确（generate_question → score_answer）

6. **Given** 评分过程中 LLM 调用失败 **When** 降级处理 **Then** 使用基于关键词匹配的简化评分（非 LLM）**And** 在 frontmatter 的 `questions[].score` 中标记 `scoring_degraded: true` **And** structlog 记录降级事件

7. **Given** 3 样本多数投票 **When** 3 次评分结果不一致 **Then** 取中位数作为最终评分 **And** 记录投票分歧到 structlog 供后续分析

## Tasks / Subtasks

- [ ] Task 1: 实现 AutoSCORE 两阶段评分 (AC: #1)
  - [ ] 阶段 1: 证据提取 prompt 设计（从答案中定位 expected_elements 对应内容）
  - [ ] 阶段 2: 4 维评分 prompt 设计（概念准确 / 推理质量 / 知识覆盖 / 知识整合，0-3 分）
  - [ ] 3 样本多数投票实现（并行调用 3 次 LLM，取多数结果）
  - [ ] 评分 prompt 模板存放在 `backend/app/prompts/exam/` 目录
  - [ ] 单元测试：4 维评分正确性、多数投票逻辑

- [ ] Task 2: 实现完全静默评分 (AC: #2)
  - [ ] score_answer 返回值不传递到 sidebar
  - [ ] 分数只写入 frontmatter questions[].score
  - [ ] 确认无 toast / 无 sidebar 文本 / 无 md body 追加
  - [ ] 集成测试：评分后 sidebar 和 md body 均无评分痕迹

- [ ] Task 3: 实现 pipeline_token 链完整传递 (AC: #3, #5)
  - [ ] score_answer(token_A) → token_B
  - [ ] update_bkt(token_B) → token_C
  - [ ] update_fsrs(token_C) → token_D
  - [ ] 验证 token 有效性（session / 过期 / 步骤顺序）
  - [ ] 更新 wiki/concepts/<slug>.md frontmatter（bkt_p_mastery / fsrs_stability）
  - [ ] 更新 exam_boards/*.md frontmatter canvas_writebacks[]
  - [ ] 单元测试：pipeline_token 链完整性

- [ ] Task 4: 实现节点切换时的隐式评分 (AC: #4)
  - [ ] 检测节点切换事件（从 Q{i} 到 Q{i+1}）
  - [ ] 自动提取当前答案并触发评分
  - [ ] 评分完全静默（与显式提交相同的静默保证）
  - [ ] 边界情况：用户未写答案就切换、快速连续切换

- [ ] Task 5: 实现评分降级策略 (AC: #6)
  - [ ] LLM 失败时使用关键词匹配简化评分
  - [ ] scoring_degraded 标记
  - [ ] structlog 记录

- [ ] Task 6: 实现投票分歧处理 (AC: #7)
  - [ ] 3 次评分不一致时取中位数
  - [ ] structlog 记录分歧详情

## Dev Notes

### Architecture
- score_answer MCP 工具已存在于 `backend/app/mcp/tools/exam_tools.py`
- pipeline_token 由 PipelineTokenManager 管理（HMAC-SHA256 签名）
- PIPELINE_STEPS: generate_question → score_answer → update_fsrs/update_bkt
- 4D x 4-point 评分体系（AR4）：概念准确(correctness) / 推理质量(reasoning) / 知识覆盖(coverage) / 知识整合(integration)
- 3 样本多数投票确保评分一致性（temperature > 0 时的随机性控制）
- 节点切换隐式评分（FR-EXAM-16）是 Flow State 保护的关键组件

### File Paths
- MCP 工具：`backend/app/mcp/tools/exam_tools.py` (ScoreAnswerInput/Output)
- Pipeline token：`backend/app/mcp/pipeline_token.py` (PipelineTokenManager)
- Mastery 更新：`backend/app/mcp/tools/mastery_tools.py` (update_bkt / update_fsrs)
- 评分 prompt：`backend/app/prompts/exam/score_answer.md`
- Exam service：`backend/app/services/exam_service.py`

### Testing
- 单元测试：AutoSCORE 两阶段、多数投票、pipeline_token 验证
- 集成测试：答题 → 评分 → BKT 更新 → FSRS 更新 → frontmatter 写入完整链路
- 静默验证：评分后确认 sidebar/body/toast 无评分痕迹

### Project Structure Notes
- pipeline_token 5 分钟有效窗口（TOKEN_EXPIRY_SECONDS = 300）
- PipelineTokenManager 使用 HMAC-SHA256 签名防篡改
- canvas_writebacks[] 记录每个节点的 bkt_before/bkt_after/score_delta

### References
- **From PRD**: §2.3 Step 7.6 — 完全静默评分 (line 1138-1141)
- **From PRD**: §2.3.1 Step 6 — score_answer MCP 调用 (line 1311-1332)
- **From PRD**: §2.3.1 Step 7 — update_bkt / update_fsrs 链 (line 1334-1348)
- `backend/app/mcp/pipeline_token.py`: PIPELINE_STEPS, TOKEN_EXPIRY_SECONDS
- `backend/app/mcp/tools/exam_tools.py`: ScoreAnswerInput/Output
- `backend/app/mcp/tools/mastery_tools.py`: update_bkt / update_fsrs

## UAT Script

> 1. 完成一题的答案编写
> 2. 按 Cmd+Option+S 提交
> 3. 确认 AI sidebar 没有显示任何分数
> 4. 确认 md 文件 body 没有追加评分信息
> 5. 打开 frontmatter，确认 questions[].score 已有值（4 维评分）
> 6. 打开对应的 wiki/concepts/<slug>.md，确认 bkt_p_mastery 已更新
> 7. 不提交答案直接切换到下一题
> 8. 返回查看上一题的 frontmatter，确认自动评分已执行

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| AutoSCORE 两阶段 | unit | `pytest tests/unit/test_autoscore.py -x` | 0 failures |
| 多数投票 | unit | `pytest tests/unit/test_majority_vote.py -x` | 0 failures |
| Pipeline token 链 | unit | `pytest tests/unit/test_pipeline_token_chain.py -x` | 0 failures |
| 静默评分验证 | integration | `pytest tests/integration/test_silent_scoring.py -x` | 0 failures |
| 隐式评分 | integration | `pytest tests/integration/test_stealth_scoring.py -x` | 0 failures |
| 评分降级 | unit | `pytest tests/unit/test_scoring_fallback.py -x` | 0 failures |

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
