---
doc_type: story
story_id: "6.4"
epic_id: "EPIC-6"
prd_id: "PRD14"
status: ready-for-dev
priority: "P1"
estimate_hours: 4
depends_on: ["6.3"]
blocks: []
trace:
  decisions: []
  bugs: []
---

# Story 6.4: 辨析题生成

## Story

As a 系统,
I want 基于学习者的历史误解自动生成辨析题,
so that 学习者可以通过辨析正确与错误理解来彻底纠正误解。

## Acceptance Criteria

1. **Given** 学习者复习某个有历史误解的概念
   **When** 系统生成辨析题
   **Then** 题目包含正确理解和学习者曾有的错误理解（并排对比形式）
   **And** 要求学习者辨别并解释"为什么 A 正确、B 错误"
   **And** 评分验证学习者是否能准确区分（不只是"A 正确"，还需给出理由）

2. **Given** 辨析题生成
   **When** AI 构造题目文本
   **Then** 题目格式为：
     - 描述段：一句话说明考察背景
     - 选项 A：正确理解（措辞严谨）
     - 选项 B：学习者曾有的错误理解（措辞贴近原始误解）
     - 问题句：请辨析 A 和 B 的区别，说明哪个正确及原因
   **And** 选项 A/B 的顺序随机（不总是 A 正确）

3. **Given** 学习者提交辨析答案
   **When** AutoSCORE 评分（AR4）
   **Then** 评分维度包含：正确选择（binary）+ 理由充分性（0-3 分）
   **And** 满分为 4 分（1 + 3），正确选择必须满足才可得理由分
   **And** 评分结果写入 frontmatter error_history 中对应误解的 `resolved` 字段

4. **Given** 学习者得分 >= 3（满分 4 分的 75%）
   **When** 系统更新误解状态
   **Then** 将对应 Graphiti 误解记录的 `resolved` 设为 true
   **And** 在 frontmatter `error_history` 中同步更新 `resolved: true` 和 `resolved_at: <今日日期>`
   **And** 该误解从任务列表中消失（不再触发 Day 3/Day 7 提醒）

5. **Given** 学习者得分 < 3（未通过）
   **When** 系统处理结果
   **Then** 误解状态保持 unresolved
   **And** 重置 Day 3/Day 7 计时器（从今天重新计算下一次提醒时间）
   **And** 在评分反馈中显示：正确答案解析 + 误解的根本原因说明

## Tasks / Subtasks

- [ ] Task 1: 后端 — 辨析题生成服务 (AC: #1, #2)
  - [ ] 1.1 在 `backend/app/services/quiz_generation_service.py` 添加 `generate_discrimination_question(concept_id: str, misconception: dict)` 方法
  - [ ] 1.2 构造 system prompt，要求 LLM 生成辨析题格式（见 AC #2）
  - [ ] 1.3 实现随机化选项顺序：`random.choice(['AB', 'BA'])` 决定正确选项位置，记录在 question metadata 中
  - [ ] 1.4 输出 schema：`{question_text, option_a, option_b, correct_option, misconception_id, question_type: "discrimination"}`

- [ ] Task 2: 后端 — 辨析题评分逻辑 (AC: #3)
  - [ ] 2.1 在 `backend/app/services/scoring_service.py` 添加 `score_discrimination_answer(answer: str, question: dict)` 方法
  - [ ] 2.2 第一阶段：提取学习者选择的选项（A 或 B），与 `correct_option` 比较得 0 或 1 分
  - [ ] 2.3 第二阶段：仅当第一阶段得 1 分时，用 LLM 评估理由充分性（0-3 分），3 次采样多数投票（AR4 规范）
  - [ ] 2.4 返回 `{selection_score: 0|1, reasoning_score: 0-3, total: 0-4, feedback_text: str}`

- [ ] Task 3: 后端 — 误解状态更新 (AC: #4, #5)
  - [ ] 3.1 在 `backend/app/services/review_reminder_service.py` 添加 `resolve_misconception(concept_id: str, misconception_id: str)` 方法
  - [ ] 3.2 更新 Graphiti 记录：`add_memory` 新 episode 标注 `resolved: true, resolved_at: today`（覆盖原记录）
  - [ ] 3.3 更新 frontmatter：读取 `error_history`，找到对应 `misconception_id`，写入 `resolved: true, resolved_at`
  - [ ] 3.4 未通过时：重置 `occurred_at` 为今天（让 Day 3/Day 7 计时器从今天重新开始）

- [ ] Task 4: 编写测试 (AC: #1, #2, #3, #4, #5)
  - [ ] 4.1 `tests/unit/test_discrimination_generation.py` — 验证题目格式、随机化选项顺序
  - [ ] 4.2 `tests/unit/test_discrimination_scoring.py` — 验证两阶段评分、满分 4 分、正确选择必须满足
  - [ ] 4.3 `tests/unit/test_misconception_resolve.py` — 验证 >= 3 分时 resolved=true，< 3 分时计时器重置
  - [ ] 4.4 `tests/integration/test_discrimination_flow.py` — 端到端验证从生成到评分到状态更新的完整链路

## Dev Notes

- **辨析题是 Epic 6 的核心功能**：它将 Story 6.3 注入的上下文转化为可操作的题目，并在 Story 6.2 的提醒闭环中验证误解是否真正修正
- **选项 A/B 随机化**：在 question metadata 中记录 `correct_option: "A"` 或 `"B"`，不硬编码。评分时从 metadata 读取，不依赖题目文本解析
- **AR4 AutoSCORE 兼容**：辨析题评分使用与普通考察题相同的两阶段隐形评分框架（证据提取→多维评分），但维度特化为"正确选择"和"理由充分性"
- **frontmatter 安全写入**：更新 error_history 时遵循 NFR-INT-1，使用事务式写入：读→修改→原子写，任何异常不部分写入
- **resolved 重置逻辑**：未通过时更新 `occurred_at` 而非删除记录，保留历史误解记录完整性

### Project Structure Notes

- 辨析题生成：`backend/app/services/quiz_generation_service.py`（已有文件，新增方法）
- 辨析题评分：`backend/app/services/scoring_service.py`（已有文件，新增方法）
- 误解状态管理：`backend/app/services/review_reminder_service.py`（Story 6.2 创建，本 Story 扩展）
- 参考评分实现：Story 3.5 AutoSCORE 实现（`tests/unit/test_auto_score.py`）

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-6.4] — AC 原文
- [Source: _bmad-output/planning-artifacts/prd.md#FR35] — FR35 辨析题生成
- [Source: _bmad-output/planning-artifacts/prd.md#AR4] — AutoSCORE 两阶段隐形评分规范
- [Source: _bmad-output/planning-artifacts/prd.md#NFR-INT-1] — frontmatter 安全写入约束
- [Source: backend/app/services/rag_service.py] — service 层风格参考

## UAT Script

> Non-technical user validation: no code terminology, only describe what to click and what to see.

1. **验证辨析题格式** (AC: #1, #2)
   - 进入一个有历史误解的概念的复习考察
   - 应该看到一道特殊格式的题目：有一段描述 + 选项 A + 选项 B + 一个问"哪个正确"的问题
   - 选项 A 和 B 中有一个应该与你之前犯过的错误非常相似
   - 如果题目只有一个选项或格式不对，记录 Story 6.4

2. **验证评分有理由要求** (AC: #3)
   - 只写"选 A"不写任何理由，提交答案
   - 即使选择正确，分数也应该只有 1 分（满分 4 分）而不是满分
   - 再次提交时写上完整理由，分数应该能达到 3-4 分
   - 如果只写选项就能得满分，记录 Story 6.4

3. **验证通过后误解消除** (AC: #4)
   - 答对辨析题（选择正确 + 理由充分，得分 >= 3）
   - 回到复习任务列表，该概念的 ⚠ 标记应该消失
   - 等待后续不应该再收到该误解的 Day 3/Day 7 提醒
   - 如果误解标记没有消失，记录 Story 6.4

4. **验证未通过后重新计时** (AC: #5)
   - 答错辨析题（得分 < 3）
   - 系统应该显示正确答案解析和误解的根本原因
   - 误解标记保持存在
   - 下次提醒的时间应该从今天重新计算（而不是继续之前的计时）
   - 如果没有显示答案解析，记录 Story 6.4

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-6.4.1 | pytest | `.venv/bin/pytest tests/unit/test_discrimination_generation.py -x -q` | 0 failed |
| CP-6.4.2 | pytest | `.venv/bin/pytest tests/unit/test_discrimination_scoring.py -x -q` | 0 failed |
| CP-6.4.3 | pytest | `.venv/bin/pytest tests/unit/test_misconception_resolve.py -x -q` | 0 failed |
| CP-6.4.4 | pytest | `.venv/bin/pytest tests/integration/test_discrimination_flow.py -x -q` | 0 failed |

## User Feedback & Changes

### Feedback Log

<!-- Users write BMAD-ANNO callouts below. Claude scans and dispatches by intent. -->

### Deviation Notes

<!-- Claude auto-fills: summary of historically processed feedback -->

## Dev Agent Record

### Agent Model Used

(to be filled by Dev agent)

### Debug Log References

### Completion Notes List

### File List

## Relations

- EPIC: [[EPIC-6]]
- PRD: [[PRD14]]
- Depends on: [[6.3]]
