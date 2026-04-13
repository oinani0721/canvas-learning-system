---
story_id: "8.3"
epic_id: "8"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P1"
estimate_hours: 8
depends_on: ["8.1"]
blocks: []
trace:
  - "FR-VIZ-03"
  - "FR-MAST-05"
---

# Story 8.3: 元认知 2x2 校准矩阵

Status: ready-for-dev

## Story
As a 学习者,
I want 查看元认知校准矩阵,
So that 我能发现"以为会了其实不会"的盲区（元认知偏差），有针对性地调整学习策略。

## Acceptance Criteria

1. **Given** 学习者在 Dashboard 中查看校准矩阵区域 **When** dataviewjs 脚本执行 **Then** 显示 2x2 矩阵表格：行维度为"掌握/待巩固"（基于 bkt_p_mastery 阈值 0.7）· 列维度为"自信/不自信"（基于 self_reported_confidence 阈值 0.7）**And** 四个象限分别标注：🟢 已巩固 / 🟡 建议复习增强信心 / 🔴 元认知偏差·优先考察 / 🟠 按计划学习

2. **Given** 校准矩阵已渲染 **When** 学习者查看各象限 **Then** 每个象限显示节点数量 **And** 🔴 "不会+自信"象限特别高亮（这是最危险的元认知偏差）**And** 处方性行动建议附在每个象限旁（如"建议用辨析题验证理解"）

3. **Given** 学习者的考察总题数 < 100 **When** 渲染校准矩阵 **Then** 矩阵仍显示但标注"数据收集中（已完成 N/100 题）" **And** 象限数值为参考值而非可靠值 **And** 进度条显示距离 100 题的完成度

4. **Given** 学习者的考察总题数在 100-400 之间 **When** 渲染校准矩阵 **Then** 矩阵标注"趋势参考（已完成 N/400 题）" **And** 象限数值开始有统计意义但需谨慎解读

5. **Given** 学习者的考察总题数 >= 400 **When** 渲染校准矩阵 **Then** 矩阵标注"统计可靠" **And** 象限数值可作为学习策略调整的依据

6. **Given** 概念节点缺少 self_reported_confidence 字段 **When** dataviewjs 查询 **Then** 该节点不计入矩阵统计 **And** 在矩阵下方注明"有 N 个概念尚未收集自信度数据" **And** 不显示 N/A 或错误

## Tasks / Subtasks

- [ ] Task 1: 实现 dataviewjs 2x2 矩阵渲染 (AC: #1, #2)
  - [ ] 在 `wiki/dashboard.md` 的校准矩阵区域编写 dataviewjs 代码块
  - [ ] 查询所有 wiki/concepts 中同时有 bkt_p_mastery 和 self_reported_confidence 的页面
  - [ ] 按阈值 0.7 分成四个象限
  - [ ] HTML 表格渲染，含象限标签 + 节点数 + 处方性建议
  - [ ] 🔴 象限特别高亮样式

- [ ] Task 2: 实现三阶段渐进显示 (AC: #3, #4, #5)
  - [ ] 统计总考察题数（遍历 exam_boards 的 questions 数组长度之和）
  - [ ] < 100: "数据收集中" + 进度条
  - [ ] 100-400: "趋势参考"
  - [ ] >= 400: "统计可靠"
  - [ ] 进度条使用 CSS 或 HTML inline 实现

- [ ] Task 3: 实现缺失数据处理 (AC: #6)
  - [ ] 过滤掉缺少 self_reported_confidence 的节点
  - [ ] 在矩阵下方显示排除说明
  - [ ] 确保 dataviewjs 不因缺失字段崩溃

- [ ] Task 4: 编写处方性行动建议文案 (AC: #2)
  - [ ] 🟢 已巩固："保持当前学习节奏"
  - [ ] 🟡 会+不自信："建议复习增强信心，可以尝试 Edge 讨论"
  - [ ] 🔴 不会+自信："建议用辨析题验证理解（最需要关注的盲区）"
  - [ ] 🟠 按计划学习："按照 FSRS 推荐的间隔继续练习"

## Dev Notes

### Architecture
- 元认知校准矩阵是设计 10（2x2 校准）的直接实现
- 三阶段渐进防止学习者在数据不足时过度解读统计结果
- dataviewjs 比 DQL 更适合此场景，因为需要条件分支、HTML 渲染和进度计算

### Dataviewjs Reference

```dataviewjs
const all = dv.pages('"wiki/concepts"')
  .where(p => p.bkt_p_mastery != null && p.self_reported_confidence != null);

const quadrants = {
  "know_and_confident": all.filter(p => p.bkt_p_mastery >= 0.7 && p.self_reported_confidence >= 0.7),
  "know_but_not_confident": all.filter(p => p.bkt_p_mastery >= 0.7 && p.self_reported_confidence < 0.7),
  "dont_know_but_confident": all.filter(p => p.bkt_p_mastery < 0.7 && p.self_reported_confidence >= 0.7),
  "dont_know_and_not_confident": all.filter(p => p.bkt_p_mastery < 0.7 && p.self_reported_confidence < 0.7),
};

// 三阶段判断
const totalQuestions = dv.pages('"exam_boards"')
  .map(p => (p.questions || []).length)
  .reduce((a, b) => a + b, 0);

let stage = "数据收集中";
if (totalQuestions >= 400) stage = "统计可靠";
else if (totalQuestions >= 100) stage = "趋势参考";
```

### File Paths
- Dashboard 文件：`wiki/dashboard.md`（校准矩阵 dataviewjs 区域）
- 概念节点：`wiki/concepts/*.md`（bkt_p_mastery / self_reported_confidence）
- 考察记录：`exam_boards/*.md`（questions 数组用于题数统计）
- CSS snippet（如需）：`.obsidian/snippets/calibration-matrix.css`

### Testing
- 手动验证四象限分类正确性（设置已知 mastery + confidence 值）
- 手动验证三阶段标注（设置不同题数的 exam_boards）
- 验证缺失 confidence 字段时的排除逻辑

### References
- **From PRD**: §5.1.1 Dashboard 设计 — 元认知校准矩阵 (line 5064-5097)
- **From PRD**: §1.10 设计 10 2x2 校准矩阵
- FR-MAST-05: 2x2 元认知校准矩阵追踪
- Kruger & Dunning (1999): Unskilled and Unaware of It — 元认知偏差理论基础

## UAT Script

> 1. 设置 5 个概念节点的 bkt_p_mastery 和 self_reported_confidence 值，覆盖四个象限
> 2. 打开 wiki/dashboard.md 滚动到校准矩阵区域
> 3. 看到 2x2 表格，四个象限节点数正确
> 4. 确认"不会+自信"象限有红色高亮和"建议用辨析题验证理解"
> 5. 设置 exam_boards 中总题数 < 100，看到"数据收集中 (N/100)"和进度条
> 6. 增加 exam_boards 使总题数 >= 100，看到"趋势参考"
> 7. 增加到 >= 400，看到"统计可靠"
> 8. 删除 2 个概念的 self_reported_confidence，看到矩阵下方注明"有 2 个概念尚未收集自信度数据"

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| 四象限分类 | manual | 设置已知值验证归类 | 各象限节点数正确 |
| 三阶段标注 | manual | 调整题数验证阶段切换 | 标注文字正确切换 |
| 🔴高亮 | manual | 检查 DOM/渲染 | 红色高亮可见 |
| 缺失处理 | manual | 删除 confidence 字段后刷新 | 不崩溃 + 排除说明 |
| 处方性建议 | manual | 查看每个象限旁的文案 | 四个建议文案完整 |

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
