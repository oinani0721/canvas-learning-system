---
doc_type: story
story_id: "7.1"
aliases: ["7.1"]
epic_id: "EPIC-7"
prd_id: "PRD14"
status: ready-for-dev
priority: "P0"
estimate_hours: 8
depends_on: []
blocks: []
trace:
  decisions: []
  bugs: []
---
# Story 7.1: 全局 Dashboard — Dataview 三层布局

## Story

As a 学习者,
I want 查看全局 Dashboard 展示我的学习状态,
so that 我可以一目了然地了解自己的整体学习进度和薄弱领域。

## Acceptance Criteria

1. **Given** 学习者打开 Dashboard 笔记
   **When** Dataview 查询执行
   **Then** 展示顶层全局统计：总概念数、已掌握比例（mastery_score ≥ 0.8）、待复习数（due_date ≤ 今天）
   **And** Dashboard 刷新 < 1s（NFR-PERF-2）

2. **Given** Dashboard 顶层统计已展示
   **When** 中层区域加载
   **Then** 展示分领域掌握度热力图：按 frontmatter tag/领域分组，每组显示平均 mastery_score 和概念数量
   **And** 领域按掌握度升序排列（薄弱领域置顶）

3. **Given** Dashboard 中层热力图已展示
   **When** 底层区域加载
   **Then** 展示近期学习活动时间线：列出最近 14 天内有 last_reviewed 更新的笔记，按日期倒序
   **And** 每条记录显示：概念名、复习日期、当时 mastery_score

4. **Given** vault 中没有任何带有标准 frontmatter 的笔记
   **When** Dataview 查询执行
   **Then** 展示空状态提示："尚无学习数据——创建第一个笔记或使用 Templater 模板开始"
   **And** 不抛出 Dataview 错误

## Tasks / Subtasks

- [ ] Task 1: 创建 Dashboard 笔记文件 (AC: #1, #4)
  - [ ] 1.1 在 vault 根目录创建 `wiki/dashboard.md`
  - [ ] 1.2 添加笔记 frontmatter（title: "学习 Dashboard", tags: [system], cssclass: dashboard）
  - [ ] 1.3 编写 Dataview JS 查询块（dv.view 或内联 dataviewjs）读取所有含 mastery_score 的笔记
  - [ ] 1.4 处理空 vault 情况：when `pages.length === 0` 展示引导文案

- [ ] Task 2: 实现顶层全局统计块 (AC: #1)
  - [ ] 2.1 查询所有含 mastery_score 的页面，统计 total_concepts
  - [ ] 2.2 计算 mastered_count（mastery_score >= 0.8）和 mastery_ratio
  - [ ] 2.3 查询 due_date <= dv.date("today") 的页面统计 due_for_review
  - [ ] 2.4 用 dv.table 或 dv.paragraph 渲染三项统计，加粗数字

- [ ] Task 3: 实现中层分领域掌握度热力图 (AC: #2)
  - [ ] 3.1 按 frontmatter tags（或自定义 domain 字段）对页面分组
  - [ ] 3.2 每组计算平均 mastery_score 和概念数
  - [ ] 3.3 按平均 mastery_score 升序排列（薄弱领域置顶）
  - [ ] 3.4 用 dv.table 渲染：领域名 | 概念数 | 平均掌握度 | 状态标签（🔴<0.4, 🟡0.4-0.7, 🟢>0.7）

- [ ] Task 4: 实现底层近期学习活动时间线 (AC: #3)
  - [ ] 4.1 筛选 last_reviewed >= dv.date("today") - dur(14, "days") 的页面
  - [ ] 4.2 按 last_reviewed 倒序排列
  - [ ] 4.3 用 dv.table 渲染：概念名（链接）| 复习日期 | mastery_score

- [ ] Task 5: 性能验证 (AC: #1, NFR-PERF-2)
  - [ ] 5.1 在含 100+ 笔记的 vault 中测量 Dataview 渲染时间
  - [ ] 5.2 若渲染 > 1s，改用 dataviewjs 分批渲染或添加 LIMIT 限制
  - [ ] 5.3 记录实测渲染时间到 Dev Notes

- [ ] Task 6: 编写测试 (AC: #1, #2, #3, #4)
  - [ ] 6.1 后端测试：验证 `/api/v1/dashboard/stats` 返回正确的 total/mastered/due 统计
  - [ ] 6.2 后端测试：验证领域分组接口按掌握度升序返回
  - [ ] 6.3 后端测试：验证空 vault 时接口返回 empty 结构而非 500

## Dev Notes

- **FR28**：`wiki/dashboard.md` 是 Dataview 驱动的 Dashboard 笔记，所有计算由 Dataview JS 在前端完成；后端仅提供补充 API（如需聚合多个 vault 数据）
- **mastery_score 阈值**：≥ 0.8 判定为"已掌握"（与 Story 4.x BKT 阈值保持一致）
- **due_date 字段**：来自 FSRS 参数（fsrs_params.due_date），格式 ISO 8601
- **NFR-PERF-2**：Dashboard 刷新 < 1s。Dataview JS 默认异步渲染，通常满足要求；vault > 200 笔记时需测试
- **领域字段约定**：优先读 frontmatter `domain` 字段；fallback 到 `tags[0]`；两者都没有则归入"未分类"
- **空状态**：Dataview `dv.pages()` 在空 vault 返回空数组，需显式处理

### Project Structure Notes

- Dashboard 笔记：`vault/wiki/dashboard.md`
- 后端 Dashboard API（可选）：`backend/app/api/v1/endpoints/dashboard.py`
- frontmatter schema 参考：`docs/_meta/FRONTMATTER-SPEC.md`

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-7.1] — AC 原始定义
- [Source: _bmad-output/planning-artifacts/prd.md#FR28] — FR28：全局 Dashboard Dataview 三层布局
- [Source: _bmad-output/implementation-artifacts/1-1-vault-init-templater.md] — frontmatter schema（mastery_score/fsrs_params/last_reviewed）
- [Source: docs/_meta/FRONTMATTER-SPEC.md] — frontmatter 字段完整定义

## UAT Script

> Non-technical user validation: no code terminology, only describe what to click and what to see.

1. **验证顶层统计** (AC: #1)
   - 打开 Obsidian，在左侧文件树找到 `wiki/dashboard.md` 并点击打开
   - 等待约 1 秒，页面应该显示三个数字：
     - "总概念数" — vault 中有标准模板的笔记总数
     - "已掌握" — 掌握度高的概念数量和百分比
     - "待复习" — 今天需要复习的概念数量
   - 如果看不到这三个数字，记录 Story 7.1 和实际看到的内容

2. **验证中层领域热力图** (AC: #2)
   - 在同一个 Dashboard 页面向下滚动
   - 应看到一个表格，按领域分组，每行显示：领域名、概念数、平均掌握度、状态图标（🔴/🟡/🟢）
   - 薄弱领域（红色）应该在表格最上方
   - 如果表格顺序不对或图标颜色有误，记录 Story 7.1

3. **验证底层活动时间线** (AC: #3)
   - 继续向下滚动
   - 应看到最近 14 天内复习过的概念列表，最新的在最上方
   - 每条记录包含：概念名（可点击跳转）、复习日期、当时的掌握度分数
   - 如果列表为空但你确实最近复习过，记录 Story 7.1

4. **验证空 vault 提示** (AC: #4)
   - 仅限全新安装测试：如果 vault 中没有任何用模板创建的笔记
   - Dashboard 应显示提示文字，而不是报错
   - 如果页面显示错误代码或红色警告，记录 Story 7.1

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-7.1.1 | pytest | `.venv/bin/pytest tests/unit/test_dashboard_stats.py -x -q` | 0 failed |
| CP-7.1.2 | pytest | `.venv/bin/pytest tests/unit/test_dashboard_domain_grouping.py -x -q` | 0 failed |
| CP-7.1.3 | pytest | `.venv/bin/pytest tests/unit/test_dashboard_empty_vault.py -x -q` | 0 failed |

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
