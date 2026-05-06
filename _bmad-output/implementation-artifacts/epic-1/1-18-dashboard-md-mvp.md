---
story_id: "1.18"
epic_id: "1"
prd_id: "canvas-learning-system"
status: "review"
priority: "P1"
estimate_hours: 6
depends_on: ["1.19"]
blocks: []
trace: ["FR-SYS-07","FR-EXAM-01"]
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
revision: "v1.0-v4-flat-arch-no-buttons-2026-05-01"
uat_sheet: "_bmad-output/验收单/Story-1.18-dashboard-mvp.md"
v1_summary:
  shipped: "canvas-vault/Dashboard.md + plugin 第 11 命令 canvas:start-examination-confirm + ConfirmExamModal"
  v3_spec_diff: "数据源 wiki/canvases → 原白板+节点 (v4 flat); Buttons plugin 替换为 DataviewJS 自渲染 + 命令面板触发"
  d4_decisions: "D4-3 confirm Modal + D4-5 三指标 (mastery 平均 + 节点总数 + FSRS placeholder)"
  not_implemented_v1: "exam_boards section (推迟 Epic 6) / 历史复习数 / Bases 集成"
---

# Story 1.18: Dashboard MD MVP (DRAFT)

**Epic**: 1
**Status**: draft
**Plan**: EPIC1-BMAD-DEV-ASSESS-2026-04-17
**Priority**: P1
**Estimate**: ~6h
**Dependency**: Story 3.6 (原白板配置，提供 index.md 数据源)

---

## Story

作为 学习者，
我想 一个 dashboard.md 显示所有原白板 + 检验白板状态 + 一键启动考察按钮，
以便 不切上下文就看到全部学习状态。

## Behavior

打开 `canvas-vault/dashboard.md`：
- 表 1: 活跃原白板（board_name / subject / doc_count / mastery）
- 表 2: 准备中检验白板（来源 / 创建时间 / 状态）
- Section: 学习历史（最近 5 笔）
- 按钮: 每个原白板一个 "启动考察" 按钮

---

## Acceptance Criteria

### AC #1: Dataview 表渲染活跃原白板
```gherkin
Given 用户在 Obsidian 打开 canvas-vault/dashboard.md
When Dataview 插件处理文件
Then 看到表 "活跃原白板" 含列: board_name / subject / doc_count / doc_mastery_avg
And 数据从 wiki/canvases/*/index.md 取
```

### AC #2: Dataview 表渲染检验白板
```gherkin
Given 有待考察 exam_boards
When 表 "准备中检验白板" 渲染
Then 显示 source_canvas / created_at / status (status != "scored")
```

### AC #3: Buttons 插件触发
```gherkin
Given 每个原白板有按钮
When 用户点 "启动考察: <board_name>"
Then `obsidian://execute?command=canvas-learning-system:canvas:start-examination` 触发
And 新 exam_board.md 在 outputs/exam_boards/ 创建
```

### AC #4: 持久化 pin
- [ ] 用户 pin dashboard.md tab → 重启 Obsidian 仍可见

---

## Tasks

- [ ] 创建 `canvas-vault/dashboard.md`（模板见下）
- [ ] 验证 Dataview DQL 查询语法
- [ ] 验证 Buttons plugin URI scheme（command id 匹配 manifest.json）
- [ ] 添加 6 个原白板按钮（占位，等 3.6 创建实际 board）
- [ ] 在 CLAUDE.md 文档 dashboard.md 用法
- [ ] UAT 5 步

---

## dashboard.md 完整模板（55 行）

```markdown
---
type: dashboard
layout: active-learning-view
created_at: 2026-04-17
version: 1.0
---

# Canvas 仪表盘

## 活跃原白板

\`\`\`dataview
TABLE
  board_name as "白板名称",
  subject as "学科",
  doc_count as "文档数",
  doc_mastery_avg as "掌握度"
FROM "wiki/canvases"
WHERE type = "whiteboard_index" AND doc_count > 0
SORT doc_mastery_avg DESC
\`\`\`

## 准备中检验白板

\`\`\`dataview
TABLE
  source_canvas as "来源白板",
  created_at as "创建时间",
  status as "状态"
FROM "outputs/exam_boards"
WHERE status != "scored"
SORT created_at DESC
\`\`\`

## 学习历史

\`\`\`dataview
LIST "最近更新: " + updated_at
FROM "wiki/canvases"
WHERE type = "whiteboard_index"
SORT updated_at DESC
LIMIT 5
\`\`\`

## 一键操作

### 数学 240 — 线性代数
\`\`\`button
name 启动考察
type command
action obsidian://execute?command=canvas-learning-system:canvas:start-examination
\`\`\`

### CS 61B — 数据结构
\`\`\`button
name 启动考察
type command
action obsidian://execute?command=canvas-learning-system:canvas:start-examination
\`\`\`
```

---

## Dev Notes

| 决策 | 选择 |
|---|---|
| 数据查询 | Dataview DQL (vs JS) |
| 触发命令 | Buttons plugin `obsidian://execute?command=X` |
| 视图 | dashboard.md + Dataview inline (避免 Bases 复杂) |
| WebUI | Phase 1 不做（Hybrid 路线） |

依赖插件:
- Dataview (https://blacksmithgu.github.io/obsidian-dataview/)
- Buttons (https://github.com/shabegom/buttons)

---

## UAT (5 步)

1. **设置**: 安装 Dataview + Buttons plugin，创建 2-3 个原白板（先跑 Story 3.6）
2. **打开 dashboard**: Dataview 渲染表，看到 2-3 行
3. **验证查询**: doc_mastery_avg 显示数字 + 排序正确
4. **测试按钮**: 点 "启动考察: Math 240" → 新 exam_board.md 创建并打开
5. **持久化**: pin tab → 重启 Obsidian → tab 仍在

---

## Pitfalls

| 症状 | 原因 | 修 |
|---|---|---|
| Dataview 表空 | type 字段大小写错 | 统一 lowercase `whiteboard_index` |
| Button 无反应 | URI 编码错 | 用 `&args=...%7B...%7D`（URL 编码）|
| LIMIT 隐藏重要项 | 5 行不够 | 改为分页或更大 LIMIT |
| Dataview 缓存陈旧 | exam 已 scored 但表未更新 | Cmd+Shift+R 重载 |
| Buttons 缺失 | 用户未装插件 | dashboard 顶部 README 提示 |

---

> [!question]+ 用户批注 - Story 1.18 spec
> dashboard.md 模板是否符合预期？4 AC + 5 步 UAT 是否够？
> （批注区）

---

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-1 | build | `cd frontend/obsidian-plugin && npm run build` | exit 0, main.js updated |
| CP-2 | deploy | `cp main.js canvas-vault/.obsidian/plugins/canvas-learning-system/` | file copied |
| CP-3 | reload | Manual: Obsidian Cmd+Shift+P → "Reload app" | no console error (F12) |
| CP-4 | UAT | Run "## UAT Script" steps | all steps pass |

## User Feedback & Changes

### Feedback Log
<!-- 用户在 Obsidian 跑 UAT 后批注 -->

### Deviation Notes
<!-- Dev agent 偏离 spec 时记录原因 -->

## Dev Agent Record

### Agent Model Used
<!-- to be filled by dev-story Skill -->

### Debug Log References
<!-- placeholder -->

### Completion Notes List
<!-- placeholder -->

### File List

<!-- dev-story Skill 实施后填充, e.g.:
- NEW: frontend/obsidian-plugin/src/modals/CalloutTypeModal.ts
- MOD: frontend/obsidian-plugin/src/main.ts (added canvas:annotate-callout)
-->

---

## D4 UX 决策落地 (2026-04-30 · Story 1.19 v4 UAT 通过后)

### D4-3 🎯 UX：Dashboard 一键考察 confirm 弹窗

**用户拍板**: ✅ **B confirm 弹窗**（推荐方案）

**实施细节**（dev 时落地）:
- Dashboard.md 上 Buttons 插件按钮「一键考察」点击后
- **先弹 Obsidian Modal**: `确认进入考察模式？将基于 mastery <0.5 的节点生成 5 题。`
- Modal 含 2 按钮: `✅ 开始考察` / `❌ 取消`
- 用户点 `开始考察` → 触发 `obsidian://execute?command=canvas:exam-start`
- 用户点 `取消` 或 `Esc` → Modal 关闭，无副作用

**spec 影响**: AC #X 一键考察按钮 → 加子句"按钮触发 confirm Modal，确认后才进入考察"

### D4-5 🎯 UX：Dashboard 显示哪些指标（multiSelect）

**用户拍板**: ✅ **3 个核心指标**（推荐方案）

**v1 MVP 必显示的 3 个指标**（按优先级）:

1. **mastery 平均分**（数字 + 颜色编码：>0.7 绿 / 0.4-0.7 黄 / <0.4 红）
   - 数据源: 所有 `节点/*.md` 的 `mastery_score` frontmatter（Story 5 实施后自动更新；当前默认 0.30 无颜色）
   - 显示格式: `📊 平均精通度: 0.42 🟡`

2. **节点总数**（按学科分组）
   - 数据源: Dataview `FROM "节点/"` count
   - 显示格式: `📚 节点总数: 23 (cs-61b: 23)`

3. **FSRS 到期数**（今日 / 本周）
   - 数据源: `节点/*.md` 的 `last_reviewed` + FSRS 调度计算（Story 6 实施后自动）
   - v1 MVP **placeholder**: `⏰ FSRS 到期: 0（Story 6 后自动统计）`

**v1 不做**（推迟到 v2）:
- 错误集中节点 / 上次考察成绩 / 孤儿节点数 / 最近 7 天复习数

**spec 影响**: AC #X dashboard.md schema → 加 3 个固定 section（不让用户自定义指标，简化 v1）

---
