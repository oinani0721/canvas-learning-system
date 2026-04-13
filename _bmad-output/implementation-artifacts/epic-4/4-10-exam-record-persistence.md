---
story_id: "4.10"
epic_id: "4"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P1"
estimate_hours: 4
depends_on: ["4.6"]
blocks: []
trace:
  - "FR-EXAM-18"
  - "FR-EXAM-21"
---

# Story 4.10: 考察记录持久化

Status: ready-for-dev

## Story
As a 学习者,
I want 每次考察的完整记录永久保存,
So that 我可以回顾历史考察并追踪学习进度。

## Acceptance Criteria

1. **Given** 考察结束（所有题目完成或学习者主动结束）**When** /start_exam_board Step 9 执行 **Then** 系统计算考察摘要：
   - total_questions（总题数）
   - answered_questions（已答题数，排除 skipped）
   - average_score（平均分，4 维取平均）
   - mastery_delta（考前 vs 考后掌握度变化）
   - new_nodes_count（新发现节点数量）
   - duration_seconds（总时长）
   **And** 摘要写入 exam_boards/*.md body 的 `## 本次考察摘要` 段落

2. **Given** 考察摘要写入完成 **When** 更新 frontmatter **Then** `status` 从 `in_progress` 更新为 `completed` **And** `completed_at` 填入完成时间戳 **And** `duration_seconds` 计算并填入

3. **Given** 考察记录保存完成 **When** 学习者在 Dashboard 查看 **Then** 所有历史考察记录可通过 Dataview 查询列出 **And** 查询格式：`FROM "exam_boards" WHERE status = "completed" SORT completed_at DESC` **And** 每条记录显示源白板、日期、平均分、节点数、时长

4. **Given** 完整考察记录 **When** 学习者点击某条记录 **Then** 可查看完整对话（所有题目 + 答案的 callout 序列）**And** 可查看每题的评分（frontmatter questions[].score）**And** 可查看掌握度变化（canvas_writebacks[]）**And** 可查看新发现节点（new_nodes_pulled[]）

5. **Given** 同一知识白板 **When** 学习者多次考察 **Then** 可生成不限数量的检验白板 **And** 每个检验白板文件名通过时间戳区分 **And** Dashboard 可按源白板分组展示历史考察

6. **Given** 考察中途学习者主动放弃 **When** 状态更新 **Then** `status` 更新为 `abandoned` **And** 已答题目的评分仍然保留 **And** 部分完成的考察记录同样永久保存

## Tasks / Subtasks

- [ ] Task 1: 实现考察摘要计算 (AC: #1)
  - [ ] 计算 total_questions / answered_questions / average_score
  - [ ] 计算 mastery_delta（对比 questions[0].asked_at 前后的掌握度变化）
  - [ ] 计算 new_nodes_count / duration_seconds
  - [ ] 写入 md body `## 本次考察摘要` 段落
  - [ ] 单元测试：各种考察场景的摘要计算正确性

- [ ] Task 2: 实现 frontmatter 状态更新 (AC: #2)
  - [ ] status: completed
  - [ ] completed_at 时间戳
  - [ ] duration_seconds 计算

- [ ] Task 3: 实现 Dashboard Dataview 查询 (AC: #3)
  - [ ] 编写 Dataview DQL 查询模板
  - [ ] 按 completed_at 降序排列
  - [ ] 显示关键指标：源白板 / 日期 / 平均分 / 节点数 / 时长
  - [ ] 集成测试：Dataview 查询返回正确结果

- [ ] Task 4: 实现完整记录查看 (AC: #4)
  - [ ] exam_boards/*.md 本身就是完整记录（callout 序列 + frontmatter）
  - [ ] 验证所有数据可读取（对话 / 评分 / 掌握度变化 / 新节点）

- [ ] Task 5: 实现多次考察支持 (AC: #5)
  - [ ] 时间戳命名保证唯一性
  - [ ] Dashboard 按源白板分组
  - [ ] 验证不限数量创建不冲突

- [ ] Task 6: 实现中途放弃处理 (AC: #6)
  - [ ] status: abandoned 更新
  - [ ] 已答题目评分保留
  - [ ] ExamService.complete_exam 支持 abandoned 状态

## Dev Notes

### Architecture
- exam_boards/*.md 文件本身就是持久化记录（md 文件永久保存在 vault 中）
- frontmatter 提供结构化元数据供 Dataview 查询
- body 中的 callout 序列提供人类可读的完整对话记录
- ExamService.complete_exam 方法已有基础框架（Story 6.8）
- ExamService.get_exam_records 方法已有基础框架（Story 6.8）

### File Paths
- 考察文件：`exam_boards/<slug>-<timestamp>.md`
- Dashboard：`wiki/dashboard.md`（Dataview 查询）
- ExamService：`backend/app/services/exam_service.py` (complete_exam, get_exam_records)
- Exam models：`backend/app/models/exam_models.py` (ExamStatus)

### Testing
- 单元测试：摘要计算、状态更新、放弃处理
- 集成测试：完整考察 → 摘要生成 → Dashboard 查询

### Project Structure Notes
- ExamStatus 枚举：IN_PROGRESS / COMPLETED / ABANDONED
- 命名格式：`<source_canvas_slug>-<yyyy-mm-dd>-<hh-mm>.md`
- Dashboard Dataview 查询按源白板分组

### References
- **From PRD**: §2.3 Step 9 — 生成考察摘要 (line 1172-1192)
- **From PRD**: §2.3 Step 10 — 提示返回原白板 (line 1194-1206)
- **From PRD**: §2.2 frontmatter Schema (line 940-1016)
- `backend/app/services/exam_service.py`: complete_exam, get_exam_records

## UAT Script

> 1. 完成一次完整考察（3+ 题）
> 2. 看到考察摘要（平均分、掌握度变化、新节点数）
> 3. 查看 frontmatter，确认 status=completed 和 completed_at
> 4. 打开 Dashboard，确认历史考察记录可查看
> 5. 对同一白板再触发一次考察
> 6. 确认生成了新的 exam_boards 文件（时间戳不同）
> 7. Dashboard 可看到两条记录
> 8. 开始一次考察但中途放弃
> 9. 确认 status=abandoned，已答部分评分保留

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| 摘要计算 | unit | `pytest tests/unit/test_exam_summary.py -x` | 0 failures |
| 状态更新 | unit | `pytest tests/unit/test_exam_status_update.py -x` | 0 failures |
| Dashboard 查询 | integration | `pytest tests/integration/test_exam_dashboard.py -x` | 0 failures |
| 多次考察 | integration | `pytest tests/integration/test_exam_multi_session.py -x` | 0 failures |
| 放弃处理 | unit | `pytest tests/unit/test_exam_abandon.py -x` | 0 failures |

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
