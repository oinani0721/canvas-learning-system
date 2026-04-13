---
story_id: "8.4"
epic_id: "8"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P1"
estimate_hours: 6
depends_on: ["8.1"]
blocks: []
trace:
  - "FR-VIZ-04"
  - "FR-VIZ-05"
---

# Story 8.4: 一键考察 + 概念详细档案

Status: ready-for-dev

## Story
As a 学习者,
I want 从 Dashboard 一键启动考察并查看概念详情,
So that 学习流程无缝衔接，不需要手动导航。

## Acceptance Criteria

1. **Given** Dashboard Layer 1 中的原白板卡片 **When** 学习者点击"开始考察"按钮 **Then** Buttons 插件触发 QuickAdd macro "Exam - Start Exam Board" **And** macro 自动传入该白板的 slug 参数 **And** 直接启动该主题的检验白板创建流程（Story 4.1）**And** 学习者无需手动选择白板

2. **Given** QuickAdd macro 被触发 **When** 系统创建检验白板 **Then** 新建的 `exam_boards/<slug>-<date>.md` 的 frontmatter `source_canvas` 自动填入触发白板的 slug **And** 创建完成后自动打开新文件 **And** Claudian sidebar 自动激活考察 skill

3. **Given** 学习者在 Dashboard 或任何位置点击概念 wikilink **When** 导航到 `wiki/concepts/<concept>.md` **Then** 概念详细档案页面显示 5 信号融合数据：BKT p_mastery、FSRS retrievability、interaction_count、最近评分、self_reported_confidence **And** 5 信号均使用处方性措辞（Story 8.2）而非原始数值

4. **Given** 概念详细档案页面 **When** 渲染 Tips 区域 **Then** 显示该概念相关的所有 callout Tips（从对话中标记的关键知识点，FR-CONV-05）**And** Tips 按标记时间降序排列 **And** 每条 Tip 显示来源对话日期

5. **Given** 概念详细档案页面 **When** 渲染待纠正区域 **Then** 显示该概念的未纠正误解列表（error_history 中 corrected != true 的条目）**And** 每条误解显示标记日期、错误类型、下次复习日期 **And** 使用正面措辞"待加强理解"而非"未纠正错误"

6. **Given** 概念详细档案页面 **When** 渲染相关 Edges 区域 **Then** 显示该概念关联的所有 Edge 文件（通过 Dataview 查询 edges/ 目录 WHERE from = concept OR to = concept）**And** 每条 Edge 显示关系类型、对方概念（wikilink）、置信度

7. **Given** 概念缺少某些信号数据 **When** 渲染档案 **Then** 缺失信号显示"尚未收集" **And** 其他已有信号正常渲染 **And** 不因部分缺失导致整个档案崩溃

## Tasks / Subtasks

- [ ] Task 1: 实现 Buttons 参数化触发 (AC: #1, #2)
  - [ ] 配置 Buttons 插件的 button 块支持传入白板 slug 参数
  - [ ] QuickAdd macro 接收 slug 参数并传给 `/start_exam_board` skill
  - [ ] 测试按钮点击后自动创建正确关联的检验白板
  - [ ] 确认 source_canvas frontmatter 自动填入

- [ ] Task 2: 创建概念档案 Dataview 模板 (AC: #3)
  - [ ] 创建 `templates/concept-profile.md` Templater 模板（或在 concept.md 末尾嵌入）
  - [ ] 5 信号展示区域：使用 dataviewjs 读取当前页面 frontmatter
  - [ ] 每个信号调用 Story 8.2 的措辞映射函数
  - [ ] 布局：表格或 callout 格式展示 5 信号

- [ ] Task 3: 实现 Tips 展示 (AC: #4)
  - [ ] Dataview 查询该概念的 tips 数组（frontmatter 或 inline）
  - [ ] 按标记时间降序排列
  - [ ] 每条 Tip 显示内容 + 来源日期

- [ ] Task 4: 实现待纠正误解展示 (AC: #5)
  - [ ] 从 frontmatter error_history 过滤 corrected != true 的条目
  - [ ] 使用正面措辞"待加强理解"
  - [ ] 每条显示日期、错误类型、下次复习日期

- [ ] Task 5: 实现相关 Edges 展示 (AC: #6)
  - [ ] Dataview TABLE：FROM "edges" WHERE from = this.file.name OR to = this.file.name
  - [ ] 字段：relation、对方概念（wikilink）、confidence

- [ ] Task 6: 实现缺失数据兜底 (AC: #7)
  - [ ] 每个信号区域的 default() 兜底
  - [ ] 缺失时显示"尚未收集"
  - [ ] 确保部分缺失不影响其他区域

## Dev Notes

### Architecture
- 一键考察是 Dashboard 到考察流程的桥梁，减少操作步骤从 3 步到 1 步
- 概念档案是学习者的"概念 X 光片"，集中展示所有维度的学习数据
- 5 信号融合来自 Story 5.3 的 mastery 融合架构
- Tips 来自 FR-CONV-05 的 callout 批注机制

### Concept Profile Layout

```
┌─────────────────────────────────────────┐
│ # [[concept-name]]                       │
│                                          │
│ ## 学习状态（5 信号）                      │
│ | 信号 | 状态 |                           │
│ | BKT 掌握度 | 🟡 建议加强练习 |           │
│ | FSRS 记忆保持 | 🟢 已巩固 |              │
│ | 练习次数 | 12 次 |                       │
│ | 最近评分 | 🟢 3/4 |                     │
│ | 自报自信度 | 🟡 中等 |                   │
│                                          │
│ ## Tips                                  │
│ > [!tip] 2026-04-10: BFS 遍历顺序...     │
│                                          │
│ ## 待加强理解                              │
│ - 混淆 BFS/DFS 时间复杂度 (4/7 复习)      │
│                                          │
│ ## 相关关系                                │
│ | Edge | 关系 | 对方概念 | 置信度 |         │
└─────────────────────────────────────────┘
```

### File Paths
- Dashboard 文件：`wiki/dashboard.md`（Buttons 更新）
- 概念档案模板：`templates/concept-profile.md`（或嵌入 concept.md 末尾）
- Buttons 配置：`.obsidian/plugins/buttons/`
- QuickAdd 配置：`.obsidian/plugins/quickadd/`
- Edge 文件目录：`edges/*.md`（from / to / relation / confidence）
- 概念节点：`wiki/concepts/*.md`（bkt_p_mastery / fsrs_* / tips / error_history）

### Testing
- 按钮点击测试：触发 QuickAdd 并创建正确关联的检验白板
- 概念档案测试：5 信号 + Tips + 待纠正 + Edges 各区域正常渲染
- 缺失数据测试：逐个删除 frontmatter 字段验证兜底

### References
- **From PRD**: §5.1.1 Dashboard 设计 (line 4880-5185)
- **From PRD**: §8.6 旅程 6 档案浏览 (line 7083-7116)
- FR-VIZ-04: Dashboard 一键启动考察
- FR-VIZ-05: 概念详细档案
- FR-CONV-05: callout 批注 Tips
- Story 4.1: 检验白板创建流程
- Story 5.3: 5 信号融合掌握度
- Story 8.2: 处方性措辞映射

## UAT Script

> 1. 打开 wiki/dashboard.md，在 Layer 1 找到某个白板的"开始考察"按钮
> 2. 点击按钮，确认自动创建 exam_boards/ 下的新文件
> 3. 确认新文件 frontmatter 的 source_canvas 自动填入白板 slug
> 4. 返回 Dashboard，点击某个概念 wikilink
> 5. 在概念页面看到 5 信号状态表（处方性措辞）
> 6. 看到 Tips 区域列出该概念的 callout 批注
> 7. 看到"待加强理解"区域列出未纠正的误解
> 8. 看到"相关关系"区域列出关联的 Edge 文件
> 9. 删除某概念的 fsrs_retrievability 字段，刷新看到该信号显示"尚未收集"

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| 一键考察 | manual | 点击 Dashboard 按钮 | 自动创建正确的检验白板 |
| 5 信号渲染 | manual | 查看概念档案 | 5 信号表格正常显示 |
| Tips 展示 | manual | 确认概念有 tips 数据后查看 | Tips 列表降序显示 |
| 待纠正展示 | manual | 确认有未纠正误解后查看 | 正面措辞"待加强理解" |
| Edges 展示 | manual | 确认有关联 Edge 后查看 | Edge 列表正常显示 |
| 缺失兜底 | manual | 删除部分字段后刷新 | "尚未收集" + 不崩溃 |

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
