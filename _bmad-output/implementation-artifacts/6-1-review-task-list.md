---
doc_type: story
story_id: "6.1"
epic_id: "EPIC-6"
prd_id: "PRD14"
status: ready-for-dev
priority: "P0"
estimate_hours: 4
depends_on: []
blocks: []
trace:
  decisions: []
  bugs: []
---

# Story 6.1: 待复习任务列表

## Story

As a 学习者,
I want 查看待复习任务列表,
so that 我知道哪些概念需要复习以及优先级。

## Acceptance Criteria

1. **Given** 学习者打开复习任务页面
   **When** 系统加载任务列表
   **Then** 显示所有已过 FSRS due_date 的概念（按逾期天数降序排列）
   **And** 显示所有有未关闭误解记录的概念
   **And** 每项显示：概念名、上次考察日期、掌握度评分、逾期天数

2. **Given** 任务列表中有多个待复习概念
   **When** 系统排序
   **Then** FSRS 已逾期项排在最前，同等逾期天数内按 mastery_score 升序（最弱优先）
   **And** 有未关闭误解记录的项目用视觉标记区分（例如橙色角标）

3. **Given** 学习者点击列表中某个概念
   **When** 跳转发生
   **Then** 直接导航至该概念的笔记页面
   **And** 当前复习任务状态保持（不清空任务列表）

4. **Given** 没有任何逾期概念和未关闭误解
   **When** 系统加载任务列表
   **Then** 显示空状态提示："当前没有待复习任务，继续保持！"

## Tasks / Subtasks

- [ ] Task 1: 后端 — 任务列表查询 API (AC: #1, #2)
  - [ ] 1.1 在 `backend/app/api/v1/endpoints/` 创建 `review.py` endpoint
  - [ ] 1.2 实现 `GET /api/v1/review/tasks` — 从 frontmatter 中读取所有 due_date 并与当前日期比较
  - [ ] 1.3 查询 Graphiti 获取每个概念的未关闭误解记录（error_type in [conceptual, knowledge_gap]，resolved=false）
  - [ ] 1.4 合并两类数据，按逾期天数降序、mastery_score 升序排列
  - [ ] 1.5 返回 JSON schema：`{concept_id, concept_name, last_reviewed, mastery_score, days_overdue, open_misconceptions_count}`

- [ ] Task 2: 后端 — 前端 MCP Tool 暴露 (AC: #1)
  - [ ] 2.1 在 MCP server 中注册 `get_review_tasks` tool（复用 Task 1 逻辑）
  - [ ] 2.2 验证 MCP tool 返回格式与 REST endpoint 一致

- [ ] Task 3: 前端 — 复习任务列表 UI (AC: #1, #2, #3, #4)
  - [ ] 3.1 在 Dataview 查询中创建 `_system/review-tasks.md` 展示页（Dataview TABLE 布局）
  - [ ] 3.2 TABLE 列：概念名（可点击）、上次考察日期、掌握度分数、逾期天数、误解标记
  - [ ] 3.3 逾期项行背景使用浅红色，未关闭误解项用橙色角标 `⚠`
  - [ ] 3.4 空状态：当 Dataview 查询返回空时显示提示文本

- [ ] Task 4: 编写测试 (AC: #1, #2)
  - [ ] 4.1 `tests/unit/test_review_endpoint.py` — 验证逾期概念正确筛选和排序逻辑
  - [ ] 4.2 `tests/unit/test_review_misconception_query.py` — 验证 Graphiti 未关闭误解查询
  - [ ] 4.3 `tests/integration/test_review_tasks_api.py` — 端到端验证 API 返回结构

## Dev Notes

- **FSRS due_date 存储位置**：每个笔记 frontmatter 的 `fsrs_params.due_date`（ISO 8601 字符串）
- **Graphiti 误解查询**：使用 `search_memory_facts(query="misconception resolved:false concept:<name>")` 获取未关闭误解
- **Dataview TABLE 语法**：使用 `WHERE file.frontmatter.fsrs_params.due_date < date(today)` 过滤逾期项
- **排序**：Dataview 中用 `SORT (date(today) - date(fsrs_params.due_date)) DESC, mastery_score ASC`
- **性能**：预期 vault 约 100 文件，Dataview 刷新需满足 NFR-PERF-2（< 1s）

### Project Structure Notes

- 后端 endpoint：`backend/app/api/v1/endpoints/review.py`（新建）
- MCP tool 注册：`backend/app/mcp_server/tools/review_tools.py`（新建）
- 前端展示页：`vault/_system/review-tasks.md`（vault 内，Dataview 驱动）
- 参考样式：`vault/_system/dashboard.md`（已有 Dataview 展示，参考格式）

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-6.1] — AC 原文
- [Source: _bmad-output/planning-artifacts/prd.md#FR36] — FR36 待复习任务列表
- [Source: docs/_meta/FRONTMATTER-SPEC.md] — fsrs_params.due_date 字段定义
- [Source: backend/app/api/v1/endpoints/canvas.py] — endpoint 风格参考

## UAT Script

> Non-technical user validation: no code terminology, only describe what to click and what to see.

1. **验证任务列表显示** (AC: #1)
   - 打开 Obsidian，导航到 `_system/review-tasks` 页面
   - 应该看到一个表格，列出所有需要复习的概念
   - 表格每行包含：概念名称、上次复习日期、掌握度数字（0-1 之间）、逾期天数
   - 如果没有看到表格或表格是空的，但你确定有些概念很久没复习了，记录 Story 6.1

2. **验证排序顺序** (AC: #2)
   - 在任务列表中，逾期最久的概念应该排在最前面
   - 有误解记录的概念行旁边应该有 ⚠ 符号
   - 如果排序不对或 ⚠ 符号缺失，记录 Story 6.1

3. **验证点击跳转** (AC: #3)
   - 点击任务列表中某个概念名称
   - 应该直接跳转到该概念的笔记页面
   - 返回任务列表页面后，列表应该保持不变（不会刷新消失）
   - 如果点击无反应或列表消失，记录 Story 6.1

4. **验证空状态** (AC: #4)
   - 如果你的所有概念都不逾期且没有未关闭误解，列表区域应显示："当前没有待复习任务，继续保持！"
   - 如果显示空白或报错，记录 Story 6.1

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-6.1.1 | pytest | `.venv/bin/pytest tests/unit/test_review_endpoint.py -x -q` | 0 failed |
| CP-6.1.2 | pytest | `.venv/bin/pytest tests/unit/test_review_misconception_query.py -x -q` | 0 failed |
| CP-6.1.3 | pytest | `.venv/bin/pytest tests/integration/test_review_tasks_api.py -x -q` | 0 failed |

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
