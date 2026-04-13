---
story_id: "4.7"
epic_id: "4"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P1"
estimate_hours: 6
depends_on: ["4.5"]
blocks: []
trace:
  - "FR-EXAM-07"
  - "FR-EXAM-08"
---

# Story 4.7: 4 级渐进提示 + 跳过不惩罚

Status: ready-for-dev

## Story
As a 学习者,
I want 答不出时请求渐进提示或跳过,
So that 我既能获得帮助又不被迫回答。

## Acceptance Criteria

1. **Given** 学习者对某题卡壳（评分 < 2 或学习者说"不会"或停留 > 5 分钟未提交）**When** skill 检测到卡壳 **Then** 询问学习者"需要提示吗？" **And** 学习者可选择"是"请求提示或"跳过"或"继续思考"

2. **Given** 学习者请求提示（第 1 次）**When** 系统提供 Level 1 提示 **Then** 给出方向提示（例如："这道题涉及 admissibility 的定义和 optimality"）**And** 提示不包含答案的任何部分 **And** `questions[].hints_used` 更新为 1

3. **Given** 学习者再次请求提示（第 2 次）**When** 系统提供 Level 2 提示 **Then** 给出关键词提示（例如："想想 h(n) 和真实代价的关系"）**And** `hints_used` 更新为 2

4. **Given** 学习者再次请求提示（第 3 次）**When** 系统提供 Level 3 提示 **Then** 给出框架提示（例如："回答的结构应该是：1. 定义 2. 举例 3. 解释为什么"）**And** `hints_used` 更新为 3

5. **Given** 学习者再次请求提示（第 4 次）**When** 系统提供 Level 4 提示 **Then** 给出脚手架提示（例如："填空：admissibility 是指 h(n) __ h*(n)，这保证 A* __"）**And** `hints_used` 更新为 4 **And** 4 级后不再有更多提示

6. **Given** 任何提示级别 **When** 学习者查看提示选项 **Then** 不提供"直接告诉答案"选项 **And** 4 级后仍不会则只能选择"跳过"或"拉出新节点（书签式提取）"

7. **Given** 学习者选择跳过题目 **When** 系统处理跳过 **Then** `questions[].skipped` 标记为 `true` **And** 不更新 BKT/FSRS 掌握度（不惩罚）**And** 直接进入下一题或考察结束流程

8. **Given** 学习者使用了提示后答题 **When** 评分时 **Then** 根据 hints_used 数量适度降低评分权重（但不归零）**And** 鼓励主动求助的设计哲学

## Tasks / Subtasks

- [ ] Task 1: 实现卡壳检测机制 (AC: #1)
  - [ ] 检测条件 1：上一题评分 < 2
  - [ ] 检测条件 2：学习者输入"不会"/"不知道"等关键词
  - [ ] 检测条件 3：5 分钟未提交超时
  - [ ] AskUserQuestion 询问是否需要提示

- [ ] Task 2: 实现 4 级渐进提示引擎 (AC: #2, #3, #4, #5)
  - [ ] Level 1 方向提示：基于节点主题生成宽泛方向
  - [ ] Level 2 关键词提示：提取关键概念词
  - [ ] Level 3 框架提示：给出答案结构框架
  - [ ] Level 4 脚手架提示：填空式引导
  - [ ] 提示 prompt 模板存放在 `backend/app/prompts/exam/` 目录
  - [ ] 每级提示 hints_used +1 写入 frontmatter
  - [ ] 单元测试：每级提示不包含完整答案

- [ ] Task 3: 实现"无直接答案"约束 (AC: #6)
  - [ ] 提示选项中不包含"给我答案"
  - [ ] 4 级后选项仅剩"跳过"和"书签式提取"
  - [ ] prompt 硬约束：禁止在提示中泄漏完整答案

- [ ] Task 4: 实现跳过不惩罚 (AC: #7)
  - [ ] skipped = true 标记
  - [ ] 跳过时不调用 update_bkt / update_fsrs
  - [ ] pipeline_token 链在跳过时正确终止（不传递到 mastery 更新）
  - [ ] 直接进入下一题
  - [ ] 单元测试：跳过后掌握度数据不变

- [ ] Task 5: 实现提示后评分权重调整 (AC: #8)
  - [ ] hints_used 对应的权重调整系数
  - [ ] 1 级提示：权重 0.85
  - [ ] 2 级提示：权重 0.70
  - [ ] 3 级提示：权重 0.55
  - [ ] 4 级提示：权重 0.40（但不归零）
  - [ ] 权重调整在 score_answer 后、update_bkt/fsrs 前应用

## Dev Notes

### Architecture
- 4 级提示基于 Anghileri (2006) Scaffolding in Mathematics Teaching：逐级降低认知负荷
- 比直接给答案保留更多 Generation Effect（d=0.65）
- 提示引擎使用 LLM 生成个性化提示（非模板化），但每级有严格的信息量控制
- ExamService.generate_hint 方法已有基础框架（Story 6.6）
- 跳过逻辑需与 pipeline_token 链协调（跳过时不传递 token 到 mastery 更新）

### File Paths
- Hint 生成：`backend/app/services/exam_service.py` (generate_hint)
- Skip 逻辑：`backend/app/services/exam_service.py` (skip_question)
- Hint prompt 模板：`backend/app/prompts/exam/hints/` 目录（level_1.md ~ level_4.md）
- Pipeline token：`backend/app/mcp/pipeline_token.py`

### Testing
- 单元测试：4 级提示生成、跳过不惩罚、权重调整
- 安全测试：提示不泄漏完整答案
- 集成测试：卡壳 → 提示 → 答题 → 评分（含权重调整）完整链路

### Project Structure Notes
- hints_used 是累计值，不会重置
- 跳过的题目在考察摘要中标记但不计入平均分

### References
- **From PRD**: §2.3 Step 7.7 — 4 级渐进提示 (line 1142-1145)
- **From PRD**: §1.9 设计 9 — 4 级渐进提示详细设计
- Anghileri (2006): Scaffolding in Mathematics Teaching
- `backend/app/services/exam_service.py`: generate_hint, skip_question

## UAT Script

> 1. 答一道题时故意写"不会"
> 2. 看到系统询问是否需要提示
> 3. 选择"是"，看到 Level 1 方向提示
> 4. 确认提示不包含答案
> 5. 再次请求提示，依次看到 Level 2/3/4
> 6. 确认没有"给我答案"选项
> 7. 4 级后选择"跳过"
> 8. 确认 frontmatter 中 skipped=true，掌握度未变化
> 9. 在另一题使用 1 级提示后答题
> 10. 确认评分有轻微降低（但不归零）

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| 卡壳检测 | unit | `pytest tests/unit/test_stuck_detection.py -x` | 0 failures |
| 4 级提示 | unit | `pytest tests/unit/test_progressive_hints.py -x` | 0 failures |
| 答案泄漏检查 | unit | `pytest tests/unit/test_hint_no_answer_leak.py -x` | 0 failures |
| 跳过不惩罚 | unit | `pytest tests/unit/test_skip_no_penalty.py -x` | 0 failures |
| 权重调整 | unit | `pytest tests/unit/test_hint_weight_adjustment.py -x` | 0 failures |
| 提示集成 | integration | `pytest tests/integration/test_exam_hints_flow.py -x` | 0 failures |

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
