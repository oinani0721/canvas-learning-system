---
story_id: "8.0"
epic_id: "8"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P0"
estimate_hours: 6
depends_on: ["1.1"]
blocks: ["8.1", "8.2", "8.3", "8.4"]
trace:
  - "FR-VIZ-01"
  - "FR-SPACE-01"
  - "FR-VIZ-04"
---

# Story 8.0: Dashboard 插件栈 + 数据流配置

Status: ready-for-dev

## Story

As a 学习者,
I want Dashboard 底层插件栈和数据流已配置就绪,
So that Story 8.1-8.4 的四个 Dashboard 区块能正常渲染真实数据，我能像操作 GUI app 一样使用 Dashboard。

## Acceptance Criteria

1. **Given** 4 个社区插件 + Bases 核心插件已启用
   **When** 打开 `wiki/dashboard.md`
   **Then** 页面能渲染 Dataview 查询
   **And** Meta Bind Button 能正常显示为 primary 样式（紫色背景 + 圆角）
   **And** DataviewJS 能成功 `requestUrl()` 后端 API（不因 CORS 报错）

2. **Given** 后端 FastAPI 启动 + Neo4j 有数据
   **When** DataviewJS `requestUrl("/api/v1/mastery/review-queue")`
   **Then** 返回今日待复习概念列表
   **And** 每项含 `effective_proficiency` + `fsrs_next_review` + `prescriptive_label` + `label_color`

3. **Given** canvas index.md 已由 Templater 生成
   **When** 学习者点击 "开始考察" Meta Bind Button
   **Then** QuickAdd choice `StartExamBoard` 被触发
   **And** 在 `outputs/exam_boards/` 生成新文件，frontmatter 含 `source_canvas: <slug>`

4. **Given** 后端未启动
   **When** 打开 Dashboard
   **Then** Section 3/4 显示友好错误（"后端未连接，请先启动 Canvas 后端"）
   **And** Section 1/2（纯 Dataview）仍能正常工作

5. **Given** 移动端 Obsidian App
   **When** 打开 Dashboard
   **Then** Section 1 卡片网格降级为单列
   **And** Meta Bind Button 点击仍可触发 QuickAdd URI

## Tasks / Subtasks

- [ ] Task 1: 后端补齐 REST endpoint (AC: #2)
  - [ ] 1.1 确认 `GET /api/v1/mastery/batch` 存在（`backend/app/api/v1/endpoints/mastery.py`）
  - [ ] 1.2 确认 `GET /api/v1/mastery/board/{board_id}` 存在
  - [ ] 1.3 新增 `GET /api/v1/mastery/review-queue?vault_path=<path>`
        - 返回 `[{concept_id, concept_name, canvas_slug, effective_proficiency, fsrs_next_review, prescriptive_label, label_color}]`
        - 过滤：`fsrs_next_review <= today`
        - label 映射（Story 8.2 阈值）：<0.5 "建议优先复习" red / 0.5-0.7 "建议加强练习" orange / 0.7-0.85 "可以改进" yellow / ≥0.85 "已巩固" green / null "尚未评估" gray
  - [ ] 1.4 CORS 配置确认允许 `app://obsidian.md` 源（Obsidian 默认 origin）

- [ ] Task 2: QuickAdd Macro 配置 (AC: #3)
  - [ ] 2.1 在 Obsidian Settings → QuickAdd 新建 Macro `StartExamBoard`
  - [ ] 2.2 类型 Template Capture，参数 `value-slug` 接收 canvas slug
  - [ ] 2.3 File name: `outputs/exam_boards/{{VALUE:slug}}-{{DATE:YYYY-MM-DD-HHmm}}.md`
  - [ ] 2.4 Template: 调用 Templater `exam-board.md` 模板
  - [ ] 2.5 Capture format: frontmatter 包含 `type: exam_board` + `source_canvas: {{VALUE:slug}}`

- [ ] Task 3: Meta Bind Button 模板 (AC: #1, #3)
  - [ ] 3.1 在 `canvas-vault/.obsidian/templates/canvas-index.md` 新增 `meta-bind-button` 代码块
  - [ ] 3.2 配置：`style: primary`, `icon: book-open`, `class: canvas-exam-btn`
  - [ ] 3.3 action: `type: open`, `link: obsidian://quickadd?choice=StartExamBoard&value-slug=<% tp.file.title %>`

- [ ] Task 4: Dashboard.md 主文件 (AC: #1, #2, #4, #5)
  - [ ] 4.1 创建 `canvas-vault/wiki/dashboard.md` 含 frontmatter `cssclasses: [cards, cls-dashboard]`
  - [ ] 4.2 Section 1 Dataview TABLE（原白板卡片）FROM `wiki/canvases` WHERE type = "canvas"
  - [ ] 4.3 Section 2 Dataview TABLE（检验白板历史）FROM `outputs/exam_boards` SORT file.mtime DESC LIMIT 30
  - [ ] 4.4 Section 3 DataviewJS：用 Obsidian `app.requestUrl({url})` 调 `/mastery/review-queue`，try/catch 处理后端未启动
  - [ ] 4.5 Section 4 DataviewJS：`requestUrl('/mastery/batch')` → 前端按 `canvas_slug` 聚合 avg/due/weak
  - [ ] 4.6 所有 DataviewJS 避免 `fetch()`，改用 `requestUrl()`（Obsidian Electron 环境 CORS 安全）

- [ ] Task 5: CSS 装饰 (AC: #1, #5)
  - [ ] 5.1 创建 `canvas-vault/.obsidian/snippets/dashboard-cards.css`
  - [ ] 5.2 视觉起点 1：从 kepano/obsidian-minimal `src/scss/features/cards.scss` 复用 ~100 行（卡片网格 + 按钮支持）
  - [ ] 5.3 视觉起点 2：从 Rainbell129 `sharetype.css` 抽出徽章思路 ~40 行（.badge-red/orange/yellow/green 配合 Section 3）
  - [ ] 5.4 自定义 ~80 行：Section 2/4 表格样式 + `.canvas-exam-btn` 定制 + `@media (max-width: 768px)` 降级单列
  - [ ] 5.5 作用域用 `.markdown-preview-view.cls-dashboard` 前缀，避免污染普通 concept.md
  - [ ] 5.6 严禁采用：TfTHacker/DashboardPlusPlus（列表布局不适用）/ emisjerry Gist（死资源 404）

- [ ] Task 6: 测试 + UAT
  - [ ] 6.1 `backend/tests/unit/test_mastery_review_queue.py` — label_color 映射正确性
  - [ ] 6.2 手动 UAT 按下方 8 步清单执行

## Dev Notes

- **CORS 陷阱**: Obsidian 的 DataviewJS 运行在 Electron 渲染进程。用 `fetch()` 调 `http://localhost:8001` 可能遇 CORS。必须改用 `app.requestUrl({url})`（Obsidian 内置 API，绕 CORS）
- **Meta Bind 语法严格**: 任何缺 `:` 或缩进错会静默失败。建议先在 Meta Bind playground（官方文档）调试再贴入模板
- **shabegom/buttons 禁用**: 已 2 年未活跃，社区迁移到 Meta Bind。不要因为"轻量"理由退回 Buttons 插件
- **Dataview 非响应性**: 概念级 mastery 变化后 Section 1/2 需 Cmd+R 刷新才能反映。Section 3/4 用 `requestUrl()` 每次打开即最新，避免这个问题
- **CSS 作用域**: 所有 Dashboard 专属 CSS 必须用 `.markdown-preview-view.cls-dashboard` 前缀，避免污染普通 concept.md
- **移动端 Grid 降级**: `auto-fit minmax()` 在 iOS 版 Obsidian 可能失效，写 `@media (max-width: 768px) { grid-template-columns: 1fr }` 兜底
- **CSS 变量**: 优先用 Obsidian 原生 `var(--background-secondary)` 和 `var(--color-border)`，确保主题切换时自适应
- **不能 CSS 的部分**: QuickAdd 弹窗 + Canvas 渲染 + Bases 内部 card 样式 — 这些是插件内部实现，接受原样即可
- **label_color 归后端**: 处方性措辞的颜色映射放后端（Story 8.2 阈值），前端只渲染，保持"单一权威源"

### Project Structure Notes

- 新建文件：`canvas-vault/wiki/dashboard.md`
- 新建文件：`canvas-vault/.obsidian/snippets/dashboard-cards.css`
- 修改文件：`canvas-vault/.obsidian/templates/canvas-index.md`（添加 Meta Bind Button）
- 修改文件：`backend/app/api/v1/endpoints/mastery.py`（如缺 review-queue endpoint）
- 新建测试：`backend/tests/unit/test_mastery_review_queue.py`

### References

- [Source: _bmad-output/planning-artifacts/prd.md#FR-VIZ-01] — 全局 Dashboard 三层布局
- [Source: _bmad-output/planning-artifacts/prd.md#FR-SPACE-01] — 通过 Dashboard NextReview 查询提醒复习
- [Source: _bmad-output/implementation-artifacts/epic-1/1-1-vault-init-templates.md#DECISION-CONFIRMED] — 插件栈 + 数据流决策
- [Source: _bmad-output/implementation-artifacts/epic-8/8-1-global-dashboard-dataview.md] — Dashboard 三层布局规范
- [Source: _bmad-output/implementation-artifacts/epic-8/8-2-prescriptive-positive-wording.md] — 处方性措辞阈值和颜色映射
- [Source: _bmad-output/implementation-artifacts/epic-8/8-4-one-click-exam-concept-profile.md] — 一键考察 QuickAdd macro
- [Community: github.com/kepano/obsidian-minimal] — CSS cards.scss 复用来源
- [Community: github.com/Rainbell129/Obsidian-Homepage] — CSS sharetype.css 徽章思路

## UAT Script

> 非技术用户验收脚本

1. **插件检查**: 打开 Obsidian → Settings → Community Plugins → 确认 4 个插件全部启用（Dataview / Templater / QuickAdd / Meta Bind），Core Plugins 确认 Bases 启用

2. **打开 Dashboard**: 打开 `wiki/dashboard.md` → 看到 4 个区块
   - Section 1: 原白板以卡片网格呈现
   - Section 2: 检验白板历史表格
   - Section 3: 今日复习列表（带彩色徽章）
   - Section 4: 白板掌握度聚合表

3. **Button UX**: 进入任意 canvas 笔记 → 看到紫色 "开始考察" 按钮（primary 样式）
4. **一键考察**: 点按钮 → QuickAdd 弹窗出现 → 回车 → 新 exam_board 文件生成
5. **Dashboard 刷新**: 返回 dashboard → Section 2 出现新 exam_board
6. **处方性措辞**: Section 3 每行带颜色徽章（红/橙/黄/绿）对应掌握度档位
7. **白板聚合**: Section 4 看到按 canvas 分组的平均/到期/薄弱数
8. **离线降级**: 停掉后端 → 刷新 → Section 1/2 仍工作，Section 3/4 显示"后端未连接"友好提示
9. **移动端**: 在手机 Obsidian 打开 dashboard → Section 1 降为单列卡片，按钮仍可点

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-8.0.1 | pytest | `.venv/bin/pytest backend/tests/unit/test_mastery_review_queue.py -x -q` | 0 failed |
| CP-8.0.2 | ruff | `ruff check backend/app/api/v1/endpoints/mastery.py` | exit 0 |
| CP-8.0.3 | manual | 按 UAT 9 步执行 | 全部通过 |

## User Feedback & Changes

### Feedback Log
<!-- Users write BMAD-ANNO callouts below -->

### Deviation Notes

**批注处理记录 (2026-04-13)**

Story 8.0 是经 `[DECISION-CONFIRMED: dashboard-interactive-ui]` 决策后从 Story 1.1 抽出的新 Story。Story 1.1 层面只负责插件检测，真正的 Dashboard 落地细节全部放本 Story。

决策依据：
- Deep Research 报告（12 类社区方案）
- 3 轮并行 Agent 验证（插件对比 / A vs B 最终效果 / 5 CSS 包实读代码）
- 用户 3 次增量回答（Q1 数据流 / Q2 插件组合 / Q3 功能范围）

详见 Plan 文件 DASHBOARD-UI-DECISION-v1。

## Dev Agent Record

### Agent Model Used
(to be filled by Dev agent)

### Debug Log References

### Completion Notes List

### File List
