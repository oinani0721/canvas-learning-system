---
story_id: "7.4"
epic_id: "7"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P1"
estimate_hours: 8
depends_on: ["7.3"]
blocks: []
trace:
  - "FR-SPACE-03"
---

# Story 7.4: 辨析题生成与 FSRS 掌握度更新

Status: ready-for-dev

## Story
As a 系统,
I want 基于历史误解生成辨析题验证纠正效果,
So that 系统能客观确认学习者的误解已被纠正，而非仅凭自报。

## Acceptance Criteria

1. **Given** 学习者完成复习对话（Story 7.3 误解上下文已注入）**When** 系统决定生成辨析题 **Then** 辨析题内容基于该概念的历史误解设计（非随机出题）**And** 题目包含历史误解的"迷惑选项"或"对比场景"**And** 题目格式与 Story 4.3 三路融合出题管道一致

2. **Given** 辨析题基于历史误解生成 **When** 系统构造 prompt **Then** prompt 包含具体的误解记录 + 正确理解 + "生成一道能区分这两者的题目" 指令 **And** 生成的题目需要学习者展示"知道为什么之前的理解是错的"而非简单复述正确答案

3. **Given** 学习者正确回答辨析题 **When** 系统评分 **Then** 更新该概念的 BKT p_mastery（正向更新）**And** 更新 FSRS stability（增加稳定性）**And** 在 frontmatter 的 error_history 中标记该误解为 `corrected: true` **And** 下次复习间隔由 FSRS 算法重新计算

4. **Given** 学习者再次答错辨析题（重复错误）**When** 系统评分 **Then** BKT p_mastery 负向更新 **And** FSRS difficulty 增加 **And** 触发新一轮间隔复习周期（重置到 Day 3 起点）**And** 该误解在 error_history 中标记 `repeated_error_count += 1`

5. **Given** 学习者跳过辨析题 **When** 系统处理跳过 **Then** 掌握度不变（不惩罚，FR-EXAM-08 对齐）**And** 该辨析题保留在下次复习时重新出现 **And** 跳过不计入 repeated_error_count

6. **Given** 历史误解涉及两个概念的混淆（如 BFS vs DFS）**When** 系统生成辨析题 **Then** 题目同时涉及两个概念的对比场景 **And** 评分结果同时影响两个概念的掌握度（但权重不等，主错概念 0.7、关联概念 0.3）

## Tasks / Subtasks

- [ ] Task 1: 实现辨析题 prompt 构造 (AC: #1, #2)
  - [ ] 在 `backend/app/services/question_generation_service.py` 中添加 `generate_discrimination_question` 方法
  - [ ] 接收参数：concept_slug, misconception_record, correct_understanding
  - [ ] prompt 模板：包含误解记录 + 正确理解 + "生成区分题" 指令
  - [ ] 输出格式与 Story 4.3 generate_question 管道一致
  - [ ] 单元测试：prompt 包含误解信息、题目非随机

- [ ] Task 2: 实现辨析题评分与掌握度更新 (AC: #3, #4)
  - [ ] 正确回答：BKT 正向更新 + FSRS stability 增加 + error_history.corrected = true
  - [ ] 错误回答：BKT 负向更新 + FSRS difficulty 增加 + 重置 Day 3 周期 + repeated_error_count += 1
  - [ ] 调用 `mastery_service.update_mastery()` 统一更新
  - [ ] frontmatter 同步写入
  - [ ] 单元测试：正确/错误/跳过三种路径的掌握度变化

- [ ] Task 3: 实现跳过逻辑 (AC: #5)
  - [ ] 跳过不修改掌握度（对齐 FR-EXAM-08）
  - [ ] 跳过的题目标记为 pending，下次复习时重新出现
  - [ ] 单元测试：跳过后掌握度不变 + 题目保留

- [ ] Task 4: 实现多概念混淆辨析 (AC: #6)
  - [ ] 检测 misconception_record 是否涉及第二个概念（confused_with 字段）
  - [ ] 多概念辨析题的评分权重分配（主 0.7 / 关联 0.3）
  - [ ] 两个概念的 frontmatter 都需要更新
  - [ ] 单元测试：多概念评分权重正确分配

- [ ] Task 5: 实现新一轮复习周期触发 (AC: #4)
  - [ ] 重复错误时重置 fsrs_next_review_at 为 today + 3days
  - [ ] 创建新的复习提醒（复用 Story 7.2 逻辑）
  - [ ] 单元测试：重复错误后新周期正确设置

## Dev Notes

### Architecture
- 辨析题是间隔复习闭环的"验证"环节，闭环为：错误标记(4.x) → 提醒(7.2) → 上下文注入(7.3) → 辨析验证(7.4) → 掌握度更新 → 循环
- 辨析题不同于普通考察题：它必须基于具体的历史误解设计，目的是区分"错误理解"和"正确理解"
- 掌握度更新复用 Story 5.2 的 mastery_service，此处增加 error_correction 场景

### File Paths
- 辨析题生成：`backend/app/services/question_generation_service.py`
- 掌握度更新：`backend/app/services/mastery_service.py`
- 评分服务：`backend/app/services/scoring_service.py`
- 概念 frontmatter：`wiki/concepts/*.md`（error_history / bkt_p_mastery / fsrs_*）
- 出题管道：`backend/app/mcp/tools/exam_tools.py`（generate_question 复用）

### Testing
- 单元测试：辨析题 prompt 包含误解信息
- 单元测试：正确/错误/跳过三种评分路径
- 单元测试：多概念权重分配
- 集成测试：完整闭环——错误标记 → Day 3 → 辨析题 → 评分 → 掌握度变化

### References
- **From PRD**: §1.8 间隔复习 (line 2824-2932)
- **From PRD**: §8.3 旅程 3 错误修正闭环 (line 7012-7021)
- Cepeda et al. (2006): Spacing Effect d=0.55
- FR-EXAM-08: 跳过不惩罚
- Story 4.3: 三路融合出题管道
- Story 5.2: 掌握度更新服务

## UAT Script

> 1. 完成 Story 7.3 的复习对话后，系统提示"来做一道辨析题验证一下"
> 2. 看到题目明确涉及之前的误解内容（不是随机题目）
> 3. 正确回答 → 确认 frontmatter 中 bkt_p_mastery 上升、error_history 该条标记 corrected: true
> 4. 重新设置一个误解，在辨析题中故意答错
> 5. 确认 bkt_p_mastery 下降、repeated_error_count 增加、fsrs_next_review_at 重置为 3 天后
> 6. 在辨析题中选择"跳过"
> 7. 确认掌握度不变、该题下次复习时重新出现

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| 辨析题 prompt 构造 | unit | `pytest tests/unit/test_discrimination_question.py -x` | 0 failures |
| 正确回答掌握度更新 | unit | `pytest tests/unit/test_discrimination_correct.py -x` | 0 failures |
| 错误回答重新循环 | unit | `pytest tests/unit/test_discrimination_error_cycle.py -x` | 0 failures |
| 跳过不惩罚 | unit | `pytest tests/unit/test_discrimination_skip.py -x` | 0 failures |
| 多概念权重 | unit | `pytest tests/unit/test_discrimination_multi_concept.py -x` | 0 failures |
| 完整闭环 | integration | `pytest tests/integration/test_review_loop.py -x` | 0 failures |

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
