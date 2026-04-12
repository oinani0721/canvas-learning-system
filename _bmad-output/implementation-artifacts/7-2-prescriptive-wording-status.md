---
doc_type: story
story_id: "7.2"
epic_id: "EPIC-7"
prd_id: "PRD14"
status: ready-for-dev
priority: "P1"
estimate_hours: 4
depends_on: ["7.1"]
blocks: []
trace:
  decisions: []
  bugs: []
---

# Story 7.2: 处方性措辞展示学习状态

## Story

As a 系统,
I want 使用处方性措辞展示学习状态,
so that 学习者看到的不是冰冷数据而是具有指导意义的建议。

## Acceptance Criteria

1. **Given** Dashboard 展示学习数据
   **When** 系统为某个概念生成状态描述
   **Then** 使用处方性措辞而非纯数据（例："建议优先复习「递归」——上次考察正确率 40%，3 天后到复习窗口"）
   **And** 措辞中包含概念名、量化依据（正确率或 mastery_score）、时间信息（复习窗口或上次复习时间）

2. **Given** 学习者的 mastery_score < 0.4（红区）
   **When** 系统生成该概念状态描述
   **Then** 使用紧迫语气："🔴 需要立即复习「X」——掌握度仅 XX%，建议今天完成"

3. **Given** 学习者的 mastery_score 在 0.4–0.7 之间（黄区）
   **When** 系统生成该概念状态描述
   **Then** 使用提醒语气："🟡 建议尽快复习「X」——掌握度 XX%，复习窗口 N 天后"

4. **Given** 学习者的 mastery_score ≥ 0.7（绿区）
   **When** 系统生成该概念状态描述
   **Then** 使用肯定语气："🟢 「X」掌握良好——下次复习 YYYY-MM-DD"
   **And** 绿区概念在 Dashboard 中不占主要视觉位置（可折叠或置底）

5. **Given** 处方性措辞生成逻辑变更
   **When** 新逻辑部署
   **Then** 所有已展示的措辞自动更新（不需要用户手动刷新）
   **And** 措辞与 Dashboard 顶层统计数据保持一致（同一数据源）

## Tasks / Subtasks

- [ ] Task 1: 定义处方性措辞模板 (AC: #1, #2, #3, #4)
  - [ ] 1.1 在 `backend/app/services/dashboard_service.py` 创建 `generate_prescriptive_label(mastery_score, concept_name, due_date, last_reviewed)` 函数
  - [ ] 1.2 实现红区（< 0.4）措辞模板：包含紧迫语气 + 概念名 + 掌握度百分比
  - [ ] 1.3 实现黄区（0.4–0.7）措辞模板：包含提醒语气 + 概念名 + 掌握度百分比 + 复习窗口天数
  - [ ] 1.4 实现绿区（≥ 0.7）措辞模板：包含肯定语气 + 概念名 + 下次复习日期
  - [ ] 1.5 处理边界：due_date 为 null 时不显示复习窗口；last_reviewed 为 null 时显示"尚未复习"

- [ ] Task 2: 后端 API 端点 (AC: #1, #5)
  - [ ] 2.1 在 `backend/app/api/v1/endpoints/dashboard.py` 添加 `GET /api/v1/dashboard/prescriptive` 端点
  - [ ] 2.2 端点返回结构：`{concepts: [{name, mastery_score, zone, label, due_date}], generated_at}`
  - [ ] 2.3 按 zone 优先级排序：红区 > 黄区 > 绿区
  - [ ] 2.4 支持 `limit` 参数（默认返回前 10 条，避免过长）

- [ ] Task 3: 在 Dashboard 笔记中集成处方性措辞展示 (AC: #1, #4)
  - [ ] 3.1 在 `vault/wiki/dashboard.md` 的 Dataview JS 中调用后端 API 或直接生成措辞
  - [ ] 3.2 红区/黄区概念列表置顶展示，绿区可折叠
  - [ ] 3.3 使用 Obsidian callout（`> [!warning]`）包裹红区措辞，`> [!tip]` 包裹绿区
  - [ ] 3.4 确认措辞与顶层统计数字数据源一致（同一 Dataview 查询或同一 API 调用）

- [ ] Task 4: 编写测试 (AC: #1, #2, #3, #4, #5)
  - [ ] 4.1 单元测试：红区措辞生成（mastery_score=0.2, 预期含"🔴"和"立即"）
  - [ ] 4.2 单元测试：黄区措辞生成（mastery_score=0.55, 预期含"🟡"和"尽快"）
  - [ ] 4.3 单元测试：绿区措辞生成（mastery_score=0.85, 预期含"🟢"和"掌握良好"）
  - [ ] 4.4 单元测试：due_date=null 时不崩溃，措辞降级为无时间信息版本
  - [ ] 4.5 API 测试：`GET /api/v1/dashboard/prescriptive` 返回正确排序（红 > 黄 > 绿）

## Dev Notes

- **FR29**：处方性措辞的核心原则是"指导行动"而非"展示数据"——措辞要让学习者知道"做什么"而不只是"是什么"
- **措辞语气设计依据**：参考 Duolingo 学习提醒和 Anki 紧急度标签的 UX 研究；避免过于焦虑的语气（不用"危险"/"失败"等词）
- **阈值一致性**：红/黄/绿三区阈值（0.4/0.7）必须与 Story 7.1 热力图状态标签阈值完全一致，避免同一概念在不同视图显示不同颜色
- **数据源**：措辞基于 frontmatter 中的 mastery_score、fsrs_params.due_date、last_reviewed 字段，不额外查询 Neo4j
- **绿区折叠**：Obsidian 原生支持 `<details><summary>` HTML 折叠，或用 Dataview JS 动态控制显示

### Project Structure Notes

- 措辞生成服务：`backend/app/services/dashboard_service.py`（新建）
- Dashboard API 端点：`backend/app/api/v1/endpoints/dashboard.py`（新建或追加到 Story 7.1 的端点）
- Dashboard 笔记：`vault/wiki/dashboard.md`（在 Story 7.1 基础上追加措辞区块）

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-7.2] — AC 原始定义
- [Source: _bmad-output/planning-artifacts/prd.md#FR29] — FR29：处方性措辞
- [Source: _bmad-output/implementation-artifacts/7-1-global-dashboard-dataview.md] — 三层布局（depends_on）
- [Source: backend/app/api/v1/endpoints/canvas.py] — 后端 router 风格参考

## UAT Script

> Non-technical user validation: no code terminology, only describe what to click and what to see.

1. **验证红区措辞** (AC: #2)
   - 打开 Dashboard（`wiki/dashboard.md`）
   - 找到掌握度低于 40% 的概念（如有）
   - 它的说明文字应该以🔴开头，包含"需要立即复习"或类似紧迫表述
   - 文字中应包含概念名称和掌握度百分比
   - 如果只看到数字（如"mastery: 0.32"），而没有文字说明，记录 Story 7.2

2. **验证黄区措辞** (AC: #3)
   - 找到掌握度在 40%–70% 之间的概念
   - 它的说明文字应该以🟡开头，包含"建议尽快复习"
   - 文字中应包含复习窗口（X 天后）
   - 如果措辞语气和红区完全相同（都说"立即"），记录 Story 7.2

3. **验证绿区措辞** (AC: #4)
   - 找到掌握度高于 70% 的概念
   - 它的说明文字应该以🟢开头，包含"掌握良好"
   - 绿区概念应该在页面底部或可以折叠
   - 如果绿区概念占据页面主要位置，记录 Story 7.2

4. **验证排序** (AC: #1)
   - 整体检查：红色概念（最需要复习的）应该在最上方
   - 绿色概念（掌握良好的）在最下方或折叠
   - 如果顺序相反（掌握好的在顶部），记录 Story 7.2

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-7.2.1 | pytest | `.venv/bin/pytest tests/unit/test_prescriptive_label_red.py -x -q` | 0 failed |
| CP-7.2.2 | pytest | `.venv/bin/pytest tests/unit/test_prescriptive_label_yellow.py -x -q` | 0 failed |
| CP-7.2.3 | pytest | `.venv/bin/pytest tests/unit/test_prescriptive_label_green.py -x -q` | 0 failed |
| CP-7.2.4 | pytest | `.venv/bin/pytest tests/unit/test_prescriptive_api_ordering.py -x -q` | 0 failed |

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

- EPIC: [[EPIC-7]]
- PRD: [[PRD14]]
- Depends on: [[7.1]]
