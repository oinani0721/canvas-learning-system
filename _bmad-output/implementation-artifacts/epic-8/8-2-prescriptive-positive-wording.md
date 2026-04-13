---
story_id: "8.2"
epic_id: "8"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P1"
estimate_hours: 4
depends_on: ["8.1"]
blocks: []
trace:
  - "FR-VIZ-02"
  - "FR-VIZ-06"
---

# Story 8.2: 处方性措辞 + 正面措辞

Status: ready-for-dev

## Story
As a 学习者,
I want 学习状态用处方性和正面措辞展示,
So that 我收到可行动的建议而非冷冰冰的数字或负面标签。

## Acceptance Criteria

1. **Given** Dashboard 或概念档案展示掌握度状态 **When** 系统渲染文本 **Then** 使用处方性措辞替代数字：`bkt_p_mastery < 0.5` 显示 "建议优先复习"、`0.5-0.7` 显示 "建议加强练习"、`0.7-0.85` 显示 "可以改进"、`>= 0.85` 显示 "已巩固" **And** 不直接暴露 `mastery: 0.62` 等原始数值

2. **Given** 处方性措辞需要颜色标记 **When** 渲染带颜色的状态标签 **Then** 颜色方案为：红色区间（< 0.5）"建议优先复习" · 橙色区间（0.5-0.7）"建议加强练习" · 黄色区间（0.7-0.85）"可以改进" · 绿色区间（>= 0.85）"已巩固" **And** 所有颜色对比度 >= 4.5:1（WCAG AA 标准，NFR-A11Y）

3. **Given** Dashboard 或 AI 对话展示学习历史 **When** 文本涉及错误或弱项 **Then** 使用正面措辞"建议加强" / "可以改进" / "有进步空间" **And** 禁止出现"错误" / "失败" / "不合格" / "差" / "弱"等负面词汇 **And** 所有 Dataview 查询的 AS 别名使用正面措辞

4. **Given** dataviewjs 或 DQL 中需要显示掌握度 **When** 渲染 **Then** 使用 `choice()` 或 dataviewjs 条件表达式将数值转换为措辞 **And** 转换逻辑集中在一个可复用的 dataviewjs 函数中（避免每处重复定义阈值）

5. **Given** 概念的掌握度数据缺失 **When** 渲染措辞 **Then** 显示"尚未评估"而非"N/A"或"0%" **And** 不使用任何暗示能力不足的表述

## Tasks / Subtasks

- [ ] Task 1: 定义措辞映射规则集 (AC: #1, #3)
  - [ ] 创建措辞映射表：数值区间 → 中文处方性标签
  - [ ] 创建禁止词列表：错误/失败/不合格/差/弱/低
  - [ ] 文档化映射规则供所有 Dataview 查询统一引用

- [ ] Task 2: 实现 dataviewjs 可复用转换函数 (AC: #4)
  - [ ] 在 `wiki/dashboard.md` 或独立的 `wiki/_helpers/mastery-label.js` 中定义转换函数
  - [ ] 函数签名：`masteryToLabel(value: number) -> string`
  - [ ] 函数签名：`masteryToColor(value: number) -> string`
  - [ ] 缺失值处理：`value == null -> "尚未评估"`

- [ ] Task 3: 更新 Dashboard 所有 Dataview 查询 (AC: #1, #4)
  - [ ] Layer 1 白板卡片的"平均进度"改用处方性措辞
  - [ ] Layer 2 考察历史的"平均分"改用正面措辞
  - [ ] Layer 3 知识点表格的 mastery 列改用处方性措辞
  - [ ] 复习队列（Story 7.1）的优先级标签对齐

- [ ] Task 4: 实现 WCAG AA 颜色对比验证 (AC: #2)
  - [ ] 选定四色方案（红/橙/黄/绿），在 Obsidian 默认主题和暗色主题下测试
  - [ ] 使用 CSS snippet 或 inline style 应用颜色
  - [ ] 对比度工具验证 >= 4.5:1（WebAIM Contrast Checker）
  - [ ] Obsidian CSS snippet 文件：`.obsidian/snippets/mastery-colors.css`

- [ ] Task 5: 审查并替换所有负面措辞 (AC: #3, #5)
  - [ ] 全局搜索现有文件中的禁止词
  - [ ] 替换为正面等价措辞
  - [ ] AI prompt 模板中添加"使用正面措辞"指令

## Dev Notes

### Architecture
- 处方性措辞是 FR-VIZ-02/06 的核心，所有面向学习者的数值展示都必须经过转换
- 措辞映射集中定义一处，Dashboard/概念档案/复习队列统一引用
- WCAG AA 4.5:1 对比度是硬约束（NFR-A11Y），需同时验证亮色和暗色主题

### Mastery-to-Label Mapping

| 数值区间 | 标签 | 颜色 | Emoji |
|---|---|---|---|
| < 0.5 | 建议优先复习 | 红色 (#dc3545) | 🔴 |
| 0.5 - 0.7 | 建议加强练习 | 橙色 (#fd7e14) | 🟠 |
| 0.7 - 0.85 | 可以改进 | 黄色 (#ffc107) | 🟡 |
| >= 0.85 | 已巩固 | 绿色 (#28a745) | 🟢 |
| null/undefined | 尚未评估 | 灰色 (#6c757d) | ⚪ |

### File Paths
- Dashboard 文件：`wiki/dashboard.md`（更新 Dataview 查询）
- CSS snippet：`.obsidian/snippets/mastery-colors.css`
- 复习队列：`wiki/review-queue.md`（Story 7.1 对齐更新）
- 概念档案：`wiki/concepts/*.md`（frontmatter 不变，展示层转换）
- AI prompt 模板：skill 定义中的措辞指令

### Testing
- 手动验证四个掌握度区间的措辞渲染正确
- WCAG 对比度验证（WebAIM Contrast Checker 工具）
- 暗色主题下的颜色可读性验证
- 全局搜索禁止词确认清除

### References
- **From PRD**: §5.1.1 Dashboard 完整设计 (line 4880-5185)
- **From PRD**: §8.6 旅程 6 档案浏览 (line 7083-7116)
- WCAG 2.1 Success Criterion 1.4.3: Contrast (Minimum) - Level AA
- WebAIM Contrast Checker: https://webaim.org/resources/contrastchecker/

## UAT Script

> 1. 打开 wiki/dashboard.md
> 2. 设置一个概念的 bkt_p_mastery = 0.3，看到"建议优先复习"（红色）
> 3. 设置另一个概念的 bkt_p_mastery = 0.6，看到"建议加强练习"（橙色）
> 4. 设置 bkt_p_mastery = 0.75，看到"可以改进"（黄色）
> 5. 设置 bkt_p_mastery = 0.9，看到"已巩固"（绿色）
> 6. 删除某概念的 bkt_p_mastery 字段，看到"尚未评估"（灰色）
> 7. 全局搜索 Dashboard 文件确认无"错误/失败/不合格"等词汇
> 8. 切换到暗色主题，确认所有颜色仍清晰可读

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| 措辞映射 | manual | 设置不同 mastery 值验证标签 | 四个区间标签正确 |
| 颜色对比度 | manual | WebAIM Contrast Checker 验证 | 全部 >= 4.5:1 |
| 暗色主题 | manual | 切换主题后检查可读性 | 颜色清晰 |
| 禁止词检查 | manual | 全局搜索负面词汇 | 0 匹配 |
| 缺失值 | manual | 删除 mastery 字段后刷新 | 显示"尚未评估" |

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
