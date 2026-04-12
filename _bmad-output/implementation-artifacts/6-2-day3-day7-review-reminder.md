---
doc_type: story
story_id: "6.2"
epic_id: "EPIC-6"
prd_id: "PRD14"
status: ready-for-dev
priority: "P0"
estimate_hours: 4
depends_on: ["6.1"]
blocks: []
trace:
  decisions: []
  bugs: []
---

# Story 6.2: Day 3 + Day 7 主动复习提醒

## Story

As a 系统,
I want 在 Day 3 和 Day 7 主动提醒复习误解概念,
so that 学习者在记忆衰退的关键时间点得到提醒。

## Acceptance Criteria

1. **Given** 学习者在考察中某概念出现误解（错误类型为 conceptual 或 knowledge_gap）
   **When** 距误解发生恰好 3 天或 7 天
   **Then** 系统在 Obsidian 启动时或 Dashboard 中显示提醒通知
   **And** 提醒包含：概念名称 + 原始误解的简短描述（不超过 50 字）
   **And** 可点击提醒直接进入该概念的复习流程

2. **Given** 提醒已在本次启动中显示过
   **When** 学习者在同一 Obsidian 会话中再次打开 Dashboard
   **Then** 不重复弹出通知（每次启动最多提醒一次）

3. **Given** 多个概念同时到达 Day 3 或 Day 7
   **When** 系统生成提醒
   **Then** 批量显示（最多 5 条，超过 5 条则合并为"X 个概念需要复习"并链接到任务列表）

4. **Given** 学习者点击提醒中的概念链接
   **When** 跳转发生
   **Then** 导航至该概念笔记并高亮显示原始误解描述（Callout 形式：`> [!warning] 复习提醒`）

## Tasks / Subtasks

- [ ] Task 1: 后端 — 提醒计算逻辑 (AC: #1, #3)
  - [ ] 1.1 创建 `backend/app/services/review_reminder_service.py`
  - [ ] 1.2 实现 `get_due_reminders()` — 查询所有 `error_history` 中 resolved=false 且 days_since_error in {3, 7} 的记录
  - [ ] 1.3 从 frontmatter `error_history` 字段读取 `{error_type, description, occurred_at, resolved}`
  - [ ] 1.4 按到期日计算：`today - occurred_at == 3` 或 `today - occurred_at == 7`（精确到天，不含小时）
  - [ ] 1.5 实现批量限制：超过 5 条时返回 `{overflow: true, count: N, items: top5}`

- [ ] Task 2: 后端 — 提醒查询 API (AC: #1)
  - [ ] 2.1 在 `backend/app/api/v1/endpoints/review.py` 添加 `GET /api/v1/review/reminders`
  - [ ] 2.2 返回 schema：`[{concept_id, concept_name, error_type, description_snippet, days_since_error, occurred_at}]`
  - [ ] 2.3 在 MCP server 中注册 `get_review_reminders` tool

- [ ] Task 3: 前端 — 提醒展示 (AC: #1, #2, #3, #4)
  - [ ] 3.1 在 Obsidian 插件启动逻辑（`onload`）中调用 `get_review_reminders` MCP tool
  - [ ] 3.2 使用 Obsidian Notice API 显示提醒（`new Notice(message, 8000)` 持续 8 秒）
  - [ ] 3.3 超过 5 条时 Notice 显示："X 个概念需要复习" + 链接到 `_system/review-tasks`
  - [ ] 3.4 用 plugin session flag 记录本次启动已提醒（`this.reminderShown = true`），避免重复弹出
  - [ ] 3.5 在目标笔记中注入 Callout：`> [!warning] 复习提醒\n> 上次误解：<description_snippet>`（仅复习跳转时注入，不永久写入）

- [ ] Task 4: 编写测试 (AC: #1, #3)
  - [ ] 4.1 `tests/unit/test_review_reminder_service.py` — 验证 Day 3/Day 7 计算逻辑（边界：今天=Day3正好，Day3+1不触发）
  - [ ] 4.2 `tests/unit/test_review_reminder_batch.py` — 验证超 5 条时的 overflow 逻辑
  - [ ] 4.3 `tests/integration/test_review_reminders_api.py` — 端到端验证 API 返回结构

## Dev Notes

- **Day 计算精度**：使用日期（不含时间）比较，避免时区和跨午夜问题。`datetime.date.today() - occurred_at.date() == timedelta(days=3)`
- **error_history 数据源**：frontmatter 的 `error_history` 列表，每条格式 `{error_type, description, occurred_at, resolved}`。同时双写在 Graphiti（FR23 规定双写）
- **Obsidian Notice API**：持续时间 8000ms，消息含 `\n` 可换行。点击链接用 `app.workspace.openLinkText(concept_name, '', false)`
- **提醒不写入 vault**：Notice 是临时 UI，不持久化到任何 .md 文件。只有点击跳转时才注入临时 Callout
- **与 Story 6.1 的关系**：6.1 提供任务列表页（overflow 时链接目标），6.2 依赖此页已存在

### Project Structure Notes

- 提醒服务：`backend/app/services/review_reminder_service.py`（新建）
- endpoint 扩展：`backend/app/api/v1/endpoints/review.py`（Story 6.1 创建，本 Story 添加新路由）
- 插件启动钩子：`frontend/src/` 中 Obsidian 插件 main.ts 的 `onload()` 方法
- 参考启动逻辑：现有插件 `onload()` 中的健康检查调用模式

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-6.2] — AC 原文
- [Source: _bmad-output/planning-artifacts/prd.md#FR33] — FR33 Day 3+7 提醒
- [Source: docs/_meta/FRONTMATTER-SPEC.md] — error_history 字段定义
- [Source: backend/app/services/rag_service.py] — service 层风格参考

## UAT Script

> Non-technical user validation: no code terminology, only describe what to click and what to see.

1. **验证 Day 3 提醒触发** (AC: #1)
   - 在考察中故意答错一道题（系统会记录误解）
   - 3 天后重新启动 Obsidian
   - 应该在右下角看到一个通知气泡，内容类似："复习提醒：「递归」— 上次误解：混淆了基本情况和递归情况"
   - 如果没有看到通知，记录 Story 6.2 和误解发生日期

2. **验证不重复弹出** (AC: #2)
   - 看到通知后，在同一次 Obsidian 会话中导航到 Dashboard
   - 不应该再次弹出同一条通知
   - 如果通知一直反复弹出，记录 Story 6.2

3. **验证批量提醒** (AC: #3)
   - 如果有超过 5 个概念同时需要复习
   - 通知应显示："6 个概念需要复习" 并带有一个链接
   - 点击链接应跳转到复习任务列表页面
   - 如果显示 6 条单独通知而不是合并，记录 Story 6.2

4. **验证点击跳转** (AC: #4)
   - 点击通知中的概念名称
   - 应该打开该概念的笔记
   - 笔记顶部应显示一个黄色警告框，内容是原始误解描述
   - 如果跳转失败或没有警告框，记录 Story 6.2

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-6.2.1 | pytest | `.venv/bin/pytest tests/unit/test_review_reminder_service.py -x -q` | 0 failed |
| CP-6.2.2 | pytest | `.venv/bin/pytest tests/unit/test_review_reminder_batch.py -x -q` | 0 failed |
| CP-6.2.3 | pytest | `.venv/bin/pytest tests/integration/test_review_reminders_api.py -x -q` | 0 failed |

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
- Depends on: [[6.1]]
