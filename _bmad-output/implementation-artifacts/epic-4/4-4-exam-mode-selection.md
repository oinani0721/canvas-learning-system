---
story_id: "4.4"
epic_id: "4"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P1"
estimate_hours: 4
depends_on: ["4.3"]
blocks: []
trace:
  - "FR-EXAM-11"
  - "FR-EXAM-12"
---

# Story 4.4: 考察模式选择

Status: ready-for-dev

## Story
As a 学习者,
I want 选择考察模式或接受系统推荐,
So that 考察方式匹配我的学习需求。

## Acceptance Criteria

1. **Given** 学习者启动考察（通过 Story 4.1 防嵌套检查后）**When** 进入模式选择步骤（/start_exam_board Step 3）**Then** 系统展示三种考察模式供选择：
   - `point_to_point`（点对点突破）：逐个节点独立出题，适合知识点白板
   - `comprehensive`（综合题考察）：跨节点综合出题，适合题目白板
   - `mixed`（混合模式）：先点对点再综合，兼顾两种
   **And** 每个模式附带简短说明帮助学习者理解差异

2. **Given** 源白板有明确的 `canvas_type` 字段 **When** 系统自动推荐模式 **Then** 知识点白板（canvas_type: concept）推荐 `point_to_point` **And** 题目白板（canvas_type: problem）推荐 `comprehensive` **And** 混合内容白板推荐 `mixed` **And** 推荐基于 Constructive Alignment (Biggs 1996)

3. **Given** 系统给出推荐 **When** 学习者选择不同模式 **Then** 学习者的手动选择覆盖系统推荐 **And** 覆盖不产生警告或阻碍

4. **Given** 模式选择完成 **When** 写入 exam_boards/*.md frontmatter **Then** `exam_mode` 字段记录最终选择（point_to_point / comprehensive / mixed）**And** 后续 generate_question 调用使用该模式参数

5. **Given** 源白板没有 `canvas_type` 字段 **When** 系统无法推荐 **Then** 默认展示 `mixed` 为推荐 **And** 三个选项同等展示

## Tasks / Subtasks

- [ ] Task 1: 实现模式选择 UI (AC: #1)
  - [ ] 在 /start_exam_board Step 3 调用 AskUserQuestion 展示三种模式
  - [ ] 每个模式附带中文说明
  - [ ] 选项格式清晰，易于理解

- [ ] Task 2: 实现自动推荐逻辑 (AC: #2)
  - [ ] 读取源白板的 canvas_type 字段
  - [ ] concept → point_to_point 推荐
  - [ ] problem → comprehensive 推荐
  - [ ] 混合/未知 → mixed 推荐
  - [ ] 推荐标记在选项中高亮（如"推荐"标签）

- [ ] Task 3: 实现用户覆盖 (AC: #3)
  - [ ] 用户选择直接覆盖推荐
  - [ ] 无警告无阻碍

- [ ] Task 4: 写入 frontmatter (AC: #4, #5)
  - [ ] exam_mode 字段写入
  - [ ] 传递给后续 generate_question 调用
  - [ ] 处理无 canvas_type 时的默认行为

## Dev Notes

### Architecture
- 模式选择是 /start_exam_board 的 Step 3，位于防嵌套检查（Step 1）和选题（Step 4）之间
- exam_mode 影响 Story 4.3 的出题策略分化
- ExamMode 枚举已定义在 `backend/app/models/exam_models.py`
- ExamService.analyze_canvas_content 已有内容分析逻辑（Story 6.2）

### File Paths
- Exam models：`backend/app/models/exam_models.py` (ExamMode enum)
- Exam service：`backend/app/services/exam_service.py` (analyze_canvas_content)
- Skill workflow：/start_exam_board Step 3

### Testing
- 单元测试：各 canvas_type 对应推荐正确、用户覆盖正常
- 集成测试：模式选择 → 出题策略 → 实际题目类型验证

### Project Structure Notes
- ExamMode 有三个值：point_to_point / comprehensive / mixed
- analyze_canvas_content 方法已存在于 ExamService（Story 6.2 AC-2）

### References
- **From PRD**: §2.3 Step 3 — 询问考察模式 (line 1048-1060)
- Biggs (1996): Constructive Alignment
- `backend/app/models/exam_models.py`: ExamMode 枚举

## UAT Script

> 1. 打开一个知识点类型白板，触发 `/start_exam_board`
> 2. 看到模式选择界面，确认 `point_to_point` 被标记为推荐
> 3. 选择 `comprehensive`（覆盖推荐）
> 4. 查看 frontmatter，确认 `exam_mode: comprehensive`
> 5. 对题目类型白板重复，确认 `comprehensive` 被推荐
> 6. 对无 canvas_type 白板重复，确认 `mixed` 被推荐

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| 推荐逻辑 | unit | `pytest tests/unit/test_exam_mode_recommendation.py -x` | 0 failures |
| 用户覆盖 | unit | `pytest tests/unit/test_exam_mode_override.py -x` | 0 failures |
| Frontmatter 写入 | unit | `pytest tests/unit/test_exam_mode_frontmatter.py -x` | 0 failures |

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
