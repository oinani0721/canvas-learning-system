---
story_id: "8.1"
epic_id: "8"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P1"
estimate_hours: 10
depends_on: ["5.3"]
blocks: ["8.2", "8.3", "8.4"]
trace:
  - "FR-VIZ-01"
---

# Story 8.1: 全局 Dashboard Dataview 三层布局

Status: ready-for-dev

## Story
As a 学习者,
I want 查看全局 Dashboard 了解学习全貌,
So that 我知道哪些白板需要复习、考察历史如何、知识链路长什么样。

## Acceptance Criteria

1. **Given** 学习者打开 `wiki/dashboard.md` **When** Dataview 查询执行 **Then** Layer 1 显示所有原白板卡片（FROM "wiki/canvases"）**And** 每张卡片包含：白板名称（wikilink）、节点数（`length(file.outlinks)`）、平均掌握度（`round(default(avg_mastery, 0) * 100) + "%"`）、最近编辑时间 **And** 每张卡片旁有"开始考察"按钮（Buttons 插件，触发 QuickAdd macro）

2. **Given** Layer 1 正常渲染 **When** 学习者查看某个原白板的考察历史 **Then** Layer 2 以 Obsidian callout 折叠分组显示：`> [!check]+ 已完成考察 (N)` 和 `> [!info]+ 待剖析节点 (M)` **And** 每条考察历史包含日期、平均分、新节点数 **And** callout 使用 `+`（默认展开最近白板）和 `-`（默认折叠其他白板）标记

3. **Given** Layer 2 中某个概念被点击 **When** 学习者导航到该概念 **Then** Layer 3 在 concept.md 中呈现：Dataview 显示 extracted_from 链路、backlinks pane 自动展示引用关系、Graph View 局部视图 **And** 最活跃知识点表格按 `length(file.inlinks)` 降序排列 **And** Edge 对话理由表格显示 from/to/relation/confidence

4. **Given** Dashboard 包含 50+ 概念节点 **When** 所有 Dataview 查询执行 **Then** 完整渲染时间 < 1s（NFR-PERF）**And** 如果超过 1s，使用 dataviewjs 缓存优化

5. **Given** vault 中尚无任何白板或考察记录 **When** 学习者打开 Dashboard **Then** 显示引导消息"还没有学习记录，从创建第一个原白板开始吧！" **And** 不显示空表格

6. **Given** 某个白板的 frontmatter 缺少 avg_mastery 字段 **When** Dataview 查询渲染 **Then** 使用 `default(avg_mastery, 0)` 兜底显示 "0%" **And** 不导致整个 Dashboard 渲染失败

## Tasks / Subtasks

- [ ] Task 1: 创建 Layer 1 — 原白板卡片列表 (AC: #1)
  - [ ] 编写 `wiki/dashboard.md` 文件，frontmatter 含 `type: dashboard`
  - [ ] Dataview TABLE 查询：FROM "wiki/canvases" WHERE type = "canvas"
  - [ ] 字段：file.link / length(file.outlinks) / round(avg_mastery * 100)% / dateformat(file.mtime)
  - [ ] SORT file.mtime DESC
  - [ ] Buttons 插件：每个白板一个"开始考察"按钮，action 为 QuickAdd macro

- [ ] Task 2: 创建 Layer 2 — 考察历史折叠分组 (AC: #2)
  - [ ] 为每个原白板创建 callout 区域：`> [!check]+ 白板名 考察历史`
  - [ ] 内嵌 Dataview TABLE：FROM "exam_boards" WHERE source_canvas = "slug"
  - [ ] 字段：file.link / dateformat(created_at) / avg_score / new_nodes_pulled / status
  - [ ] SORT created_at DESC LIMIT 5
  - [ ] 待剖析节点 callout：FROM "wiki/concepts" WHERE extracted_from.type = "exam_board" AND body_status = "placeholder"

- [ ] Task 3: 创建 Layer 3 — 剖析链路与活跃知识点 (AC: #3)
  - [ ] 最活跃知识点 TABLE：FROM "wiki/concepts" SORT length(file.inlinks) DESC LIMIT 10
  - [ ] 字段：file.link / inlinks 数 / outlinks 数 / bkt_p_mastery / confidence
  - [ ] Edge 对话理由 TABLE：FROM "edges" SORT file.mtime DESC LIMIT 10
  - [ ] 字段：file.link / from / to / relation / confidence

- [ ] Task 4: 实现 Buttons + QuickAdd 集成 (AC: #1)
  - [ ] 配置 QuickAdd macro "Exam - Start Exam Board"
  - [ ] Buttons 插件 button 块格式正确：name / type / action
  - [ ] 测试按钮点击触发 QuickAdd

- [ ] Task 5: 实现性能优化与空状态 (AC: #4, #5, #6)
  - [ ] 测量 50+ 节点时的渲染时间
  - [ ] 如超过 1s 则改用 dataviewjs 缓存查询结果
  - [ ] 空状态引导消息
  - [ ] default() 兜底所有可选 frontmatter 字段

## Dev Notes

### Architecture
- Dashboard 是学习者的"控制台"，三层布局直接对应用户批注 #3 的诉求
- 纯 Dataview DQL + Buttons + Callouts 方案（用户锁定方案 B，anchor PRD §5.1.1）
- 所有数据来源于 frontmatter，Dataview 只读不写
- Layer 3 利用 Obsidian 原生能力（Backlinks pane + Graph View），无需额外插件

### Dataview DQL Reference

Layer 1 核心查询：
```dataview
TABLE WITHOUT ID
  file.link AS "原白板",
  length(file.outlinks) AS "节点数",
  round(default(avg_mastery, 0) * 100) + "%" AS "平均进度",
  dateformat(file.mtime, "yyyy-MM-dd HH:mm") AS "最近编辑"
FROM "wiki/canvases"
WHERE type = "canvas"
SORT file.mtime DESC
```

Layer 2 考察历史查询（每个白板一个）：
```dataview
TABLE WITHOUT ID
  file.link AS "考察",
  dateformat(date(created_at), "yyyy-MM-dd") AS "日期",
  round(default(avg_score, 0) * 100) / 25 + "/4" AS "平均分",
  length(default(new_nodes_pulled, [])) AS "新节点"
FROM "exam_boards"
WHERE source_canvas = "search-algorithms"
SORT created_at DESC
LIMIT 5
```

### File Paths
- Dashboard 文件：`wiki/dashboard.md`
- 原白板目录：`wiki/canvases/*.md`（frontmatter: type=canvas, avg_mastery）
- 考察记录目录：`exam_boards/*.md`（frontmatter: source_canvas, avg_score, new_nodes_pulled）
- 概念节点目录：`wiki/concepts/*.md`（frontmatter: bkt_p_mastery, extracted_from）
- Edge 文件目录：`edges/*.md`（frontmatter: from, to, relation, confidence）
- Buttons 插件配置：`.obsidian/plugins/buttons/`
- QuickAdd 配置：`.obsidian/plugins/quickadd/`

### Testing
- 手动验证三层布局在空 vault / 3 白板 / 10+ 白板时正常渲染
- 性能测试：50+ 节点时渲染 < 1s
- Buttons 点击测试：触发 QuickAdd macro

### References
- **From PRD**: §5.1.1 Dashboard 完整设计 (line 4880-5185)
- **From PRD**: §8.6 旅程 6 档案浏览 (line 7083-7116)
- 用户批注 #3: Dashboard 三层信息需求
- 方案 B 锁定：Buttons + Dataview + Callouts（社区 top 20 插件）

## UAT Script

> 1. 确保 vault 中有至少 2 个 wiki/canvases/ 白板文件（frontmatter 含 type: canvas）
> 2. 确保有至少 3 个 exam_boards/ 考察记录（frontmatter 含 source_canvas）
> 3. 确保有至少 5 个 wiki/concepts/ 概念节点（部分含 extracted_from）
> 4. 打开 wiki/dashboard.md
> 5. Layer 1: 看到原白板卡片列表，含节点数、平均进度、最近编辑时间
> 6. 看到每个白板旁有"开始考察"按钮
> 7. Layer 2: 看到考察历史 callout 折叠分组（最近白板默认展开）
> 8. Layer 2: 看到待剖析节点列表
> 9. 点击某个概念 wikilink，导航到 concept.md
> 10. Layer 3: 看到 backlinks pane、Graph View、extracted_from 链路
> 11. 删除所有白板文件，刷新 Dashboard，看到引导消息

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| Dataview 语法 | manual | 打开 dashboard.md 无 DQL 报错 | 三层表格正常渲染 |
| Buttons 触发 | manual | 点击"开始考察"按钮 | QuickAdd macro 被触发 |
| Callout 折叠 | manual | 点击 callout 展开/折叠 | 交互正常 |
| 性能 | manual | 50+ 节点时计时 | < 1s 渲染 |
| 空状态 | manual | 清空所有白板后刷新 | 引导消息显示 |
| 字段兜底 | manual | 删除某白板 avg_mastery 后刷新 | 显示 "0%" 不崩溃 |

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
