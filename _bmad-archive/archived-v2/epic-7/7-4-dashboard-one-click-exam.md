---
doc_type: story
story_id: "7.4"
aliases: ["7.4"]
epic_id: "EPIC-7"
prd_id: "PRD14"
status: ready-for-dev
priority: "P1"
estimate_hours: 2
depends_on: ["7.1"]
blocks: []
trace:
  decisions: []
  bugs: []
---
# Story 7.4: Dashboard 一键启动检验白板

## Story

As a 学习者,
I want 从 Dashboard 一键启动检验白板,
so that 我可以快速开始考察而不需要手动切换到笔记页面。

## Acceptance Criteria

1. **Given** 学习者在 Dashboard 页面
   **When** 学习者点击"开始考察"按钮
   **Then** 系统自动根据 Dashboard 显示的薄弱领域选题（优先选 mastery_score 最低的概念）
   **And** 创建检验白板并跳转到白板页面

2. **Given** 系统自动选题
   **When** 选题逻辑执行
   **Then** 选题范围基于 Dashboard 当前显示的数据（不需要学习者手动指定概念）
   **And** 优先选取 due_date ≤ 今天 且 mastery_score < 0.7 的概念（至多 5 个）
   **And** 若无到期概念则选 mastery_score 最低的前 5 个概念

3. **Given** vault 中没有符合条件的待考察概念（所有概念 mastery_score ≥ 0.8 且未到复习时间）
   **When** 学习者点击"开始考察"
   **Then** 显示提示："当前所有概念掌握良好，无需立即考察"
   **And** 提供"随机考察"选项（从全部概念随机选 3 个）

4. **Given** 学习者点击了"开始考察"按钮
   **When** 白板创建中
   **Then** 按钮显示加载状态（禁用 + "创建中…" 文字）
   **And** 完成后自动跳转，不停留在 Dashboard 等待

5. **Given** 检验白板 Skill 调用失败（如后端不可达）
   **When** 创建操作超时或报错
   **Then** 显示错误提示："启动失败，请检查后端服务是否运行"
   **And** 按钮恢复可点击状态，不处于永久加载

## Tasks / Subtasks

- [ ] Task 1: 在 Dashboard 笔记中添加"开始考察"按钮 (AC: #1, #4)
  - [ ] 1.1 在 `vault/wiki/dashboard.md` 使用 Buttons 插件语法或 Dataview JS 渲染按钮
  - [ ] 1.2 按钮标签："开始考察"，点击触发 QuickAdd Macro 或直接调用 MCP Skill
  - [ ] 1.3 点击后按钮文字变为"创建中…"并禁用（通过 Buttons 插件的 templater 模式实现）

- [ ] Task 2: 实现自动选题逻辑 (AC: #2, #3)
  - [ ] 2.1 在 `backend/app/services/dashboard_service.py` 实现 `select_exam_topics(vault_pages, max_count=5)` 函数
  - [ ] 2.2 第一优先级：due_date ≤ today AND mastery_score < 0.7，按 mastery_score 升序取前 max_count 个
  - [ ] 2.3 第二优先级（无到期概念时）：所有概念按 mastery_score 升序取前 max_count 个
  - [ ] 2.4 全部优秀情况（所有 mastery_score ≥ 0.8）：返回 `{topics: [], all_mastered: true}`

- [ ] Task 3: 后端 API 端点 (AC: #1, #2, #3, #5)
  - [ ] 3.1 在 `backend/app/api/v1/endpoints/dashboard.py` 添加 `POST /api/v1/dashboard/start-exam` 端点
  - [ ] 3.2 端点调用 `select_exam_topics` 获取选题列表
  - [ ] 3.3 调用检验白板创建 Skill（参考现有 Skill 调用方式）传入概念列表
  - [ ] 3.4 返回结构：`{exam_created: bool, topic_names: [...], vault_note_path: str, all_mastered: bool}`
  - [ ] 3.5 超时设置 10s，超时返回 503 而非 hang

- [ ] Task 4: Dashboard 前端处理跳转和错误 (AC: #4, #5)
  - [ ] 4.1 接收 API 返回的 `vault_note_path`，用 Obsidian `app.workspace.openLinkText` 跳转
  - [ ] 4.2 `all_mastered: true` 时显示提示并添加"随机考察"次级按钮
  - [ ] 4.3 API 调用失败（网络错误/503）时恢复按钮状态并显示错误文字

- [ ] Task 5: 编写测试 (AC: #1, #2, #3, #5)
  - [ ] 5.1 单元测试：有到期概念时选题返回到期+低掌握度概念（优先级正确）
  - [ ] 5.2 单元测试：无到期概念时选题返回最低掌握度的前 5 个
  - [ ] 5.3 单元测试：全部掌握良好时返回 `all_mastered: true` 且 topics 为空
  - [ ] 5.4 API 测试：`POST /api/v1/dashboard/start-exam` 10s 内响应

## Dev Notes

- **FR31**：Buttons + QuickAdd → Skill 是 PRD 原始技术路径。实际实现视 Buttons 插件版本而定；备选方案是用 Dataview JS 的 `dv.el("button", ...)` 配合 onclick 事件
- **Buttons 插件限制**：Buttons 插件在 Obsidian 0.16+ 后有 API 变化，点击事件的回调方式需验证。优先用 `button` 类型配合 `templater` action 触发 Templater JS
- **选题数量上限**：默认 5 个。考虑到单次考察体验，5 个概念约 15–20 分钟。不做用户配置项（MVP 阶段）
- **跳转方式**：使用 `app.workspace.openLinkText(path, '', true)` 在新标签页打开白板；不关闭 Dashboard
- **超时处理**：Skill 创建白板可能需要 LLM 调用，估计 5–8s。设置 10s 超时足够，避免学习者等待太久

### Project Structure Notes

- 选题服务：`backend/app/services/dashboard_service.py`（追加函数）
- 考察启动 API：`backend/app/api/v1/endpoints/dashboard.py`（追加端点）
- Dashboard 笔记：`vault/wiki/dashboard.md`（添加按钮和跳转逻辑）

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-7.4] — AC 原始定义
- [Source: _bmad-output/planning-artifacts/prd.md#FR31] — FR31：Dashboard 一键启动检验白板
- [Source: _bmad-output/implementation-artifacts/7-1-global-dashboard-dataview.md] — 三层布局（depends_on）
- [Source: backend/app/api/v1/endpoints/canvas.py] — 后端 router 风格参考

## UAT Script

> Non-technical user validation: no code terminology, only describe what to click and what to see.

1. **验证按钮存在** (AC: #1)
   - 打开 Dashboard（`wiki/dashboard.md`）
   - 应在页面顶部或醒目位置看到一个"开始考察"按钮
   - 如果只有文字而没有可点击的按钮，记录 Story 7.4

2. **验证一键启动** (AC: #1, #2)
   - 点击"开始考察"按钮
   - 按钮应短暂显示"创建中…"（1–10 秒）
   - 随后自动跳转到新建的检验白板笔记
   - 检验白板中应预先列出了几个需要考察的概念（基于你的薄弱领域自动选取）
   - 如果点击后没有任何反应，或者需要你手动选概念，记录 Story 7.4

3. **验证选题范围** (AC: #2)
   - 查看检验白板中的概念列表
   - 列表中的概念应是 Dashboard 中标记为薄弱（红色或黄色）的概念
   - 如果列表中出现了你掌握良好（绿色）的概念，记录 Story 7.4

4. **验证全部掌握良好情况** (AC: #3)
   - 此项仅在所有概念都已充分掌握时验证
   - 点击"开始考察"，应看到提示："当前所有概念掌握良好，无需立即考察"
   - 同时应有"随机考察"选项可点击
   - 如果直接报错或无任何提示，记录 Story 7.4

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-7.4.1 | pytest | `.venv/bin/pytest tests/unit/test_exam_topic_selection.py -x -q` | 0 failed |
| CP-7.4.2 | pytest | `.venv/bin/pytest tests/unit/test_exam_all_mastered.py -x -q` | 0 failed |
| CP-7.4.3 | pytest | `.venv/bin/pytest tests/integration/test_start_exam_api.py -x -q` | 0 failed |

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
