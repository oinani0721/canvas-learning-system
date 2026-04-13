---
story_id: "7.1"
epic_id: "7"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P1"
estimate_hours: 6
depends_on: ["5.2"]
blocks: ["7.2"]
trace:
  - "FR-SPACE-04"
---

# Story 7.1: 复习任务列表

Status: ready-for-dev

## Story
As a 学习者,
I want 查看待完成的复习任务列表,
So that 我知道今天需要复习哪些概念，按优先级合理安排时间。

## Acceptance Criteria

1. **Given** 学习者打开 `wiki/dashboard.md` 或直接打开 `wiki/review-queue.md` **When** Dataview 查询执行 **Then** 显示所有 `fsrs_next_review_at <= date(today) + dur(1 day)` 的概念节点 **And** 每行包含概念名称（wikilink）、截止日期、复习优先级标签

2. **Given** 待复习概念列表已加载 **When** 系统排序 **Then** 按 FSRS `next_review_date` 升序排列（最紧急排最前）**And** 同日内按 `effective_proficiency` 升序二次排序（最薄弱优先）

3. **Given** 概念节点的 frontmatter 包含 `fsrs_next_review_at` 和 `bkt_p_mastery` **When** Dataview DQL 渲染 **Then** 优先级标签根据逾期天数自动计算：逾期 >3 天显示 "紧急"、逾期 1-3 天显示 "建议今日"、未逾期显示 "计划中" **And** 使用处方性措辞（FR-VIZ-02 一致）

4. **Given** 学习者有 0 个待复习概念 **When** 查看任务列表 **Then** 显示鼓励性消息"目前没有待复习的概念，继续保持！" **And** 不显示空表格

5. **Given** 待复习列表中某个概念的 Graphiti 数据不可用 **When** 系统查询掌握度 **Then** 该概念仍显示在列表中，优先级标记为"数据缺失"（NFR-DEG 降级）**And** 不阻塞其他概念的正常显示

## Tasks / Subtasks

- [ ] Task 1: 创建 Dataview DQL 查询模板 (AC: #1, #2)
  - [ ] 编写 `wiki/review-queue.md` 文件，包含 Dataview TABLE 查询
  - [ ] FROM "wiki/concepts" WHERE fsrs_next_review_at 过滤逻辑
  - [ ] SORT fsrs_next_review_at ASC, effective_proficiency ASC
  - [ ] 字段映射：file.link AS "概念"、fsrs_next_review_at AS "复习日期"、priority AS "优先级"

- [ ] Task 2: 实现优先级标签计算 (AC: #3)
  - [ ] 使用 dataviewjs 计算逾期天数：`date(today) - date(fsrs_next_review_at)`
  - [ ] 三级标签：紧急（>3d）/ 建议今日（1-3d）/ 计划中（未逾期）
  - [ ] 处方性措辞对齐：使用"建议优先复习"而非"逾期 N 天"

- [ ] Task 3: 实现空状态和降级处理 (AC: #4, #5)
  - [ ] 空列表时显示 callout 鼓励消息
  - [ ] 数据缺失时的 fallback 显示逻辑
  - [ ] 确保 Dataview 查询在节点缺少 fsrs 字段时不崩溃（default() 兜底）

- [ ] Task 4: 集成到 Dashboard (AC: #1)
  - [ ] 在 `wiki/dashboard.md` 的"今日建议"区域嵌入复习队列链接或内联查询
  - [ ] 确保与 Story 8.1 Dashboard 三层布局兼容

## Dev Notes

### Architecture
- 复习任务列表是 FSRS 间隔复习闭环的入口，学习者从这里开始每日复习流程
- 所有数据来源于概念节点 frontmatter 的 FSRS 字段（fsrs_next_review_at / fsrs_stability / fsrs_retrievability）
- Dataview DQL 是只读查询，不修改任何 frontmatter 数据

### File Paths
- 复习队列页面：`wiki/review-queue.md`
- Dashboard 集成点：`wiki/dashboard.md`（"今日建议"区域）
- 概念节点目录：`wiki/concepts/*.md`（frontmatter 含 fsrs_next_review_at）
- FSRS 数据写入：`backend/app/services/mastery_service.py`（Story 5.2 已实现）

### Testing
- 手动验证 Dataview 查询在 10/50/100+ 节点时 < 500ms
- 验证逾期天数计算跨时区正确
- 验证空 frontmatter 字段的 default() 兜底行为

### References
- **From PRD**: §1.8 间隔复习 (line 2824-2932)
- **From PRD**: §5.1.1 Dashboard 完整设计 (line 4880-5185) — "今日建议"区域
- Cepeda et al. (2006): Spacing Effect d=0.55
- FSRS 算法：open-spaced-repetition/fsrs4anki

## UAT Script

> 1. 确保至少 3 个 wiki/concepts/ 笔记的 frontmatter 有 fsrs_next_review_at 字段
> 2. 将其中 1 个设为昨天日期，1 个设为 4 天前，1 个设为明天
> 3. 打开 wiki/review-queue.md
> 4. 看到 3 行表格，4 天前的排第一（标签"紧急"），昨天的排第二（标签"建议今日"），明天的排第三（标签"计划中"）
> 5. 删除所有 fsrs_next_review_at 字段，刷新页面
> 6. 看到鼓励消息"目前没有待复习的概念"

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| Dataview 查询语法 | manual | 打开 review-queue.md 无报错 | Dataview 表格正常渲染 |
| 排序正确性 | manual | 设置不同 fsrs_next_review_at 验证顺序 | 最紧急排最前 |
| 空状态 | manual | 清空所有 fsrs 字段后刷新 | 显示鼓励消息 |
| 降级处理 | manual | 删除某节点 fsrs 字段后刷新 | 列表不崩溃，显示"数据缺失" |

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
