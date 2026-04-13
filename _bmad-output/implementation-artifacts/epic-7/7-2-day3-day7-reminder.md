---
story_id: "7.2"
epic_id: "7"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P1"
estimate_hours: 8
depends_on: ["7.1"]
blocks: ["7.3"]
trace:
  - "FR-SPACE-01"
  - "FR-SPACE-05"
---

# Story 7.2: Day 3 + Day 7 定时提醒

Status: ready-for-dev

## Story
As a 系统,
I want 在 Day 3 和 Day 7 主动提醒学习者复习标记的误解,
So that 间隔复习效应得以实现（Cepeda 2006, d=0.55）。

## Acceptance Criteria

1. **Given** 学习者在 Day 0 的考察中标记了错误（frontmatter `error_marked_at` 已写入）**When** Day 3 到来（`date(today) - date(error_marked_at) >= 3`）**Then** Spaced Repetition 插件弹出复习提醒通知 **And** 通知文本为处方性措辞"建议复习：[[concept-name]] — 3 天前标记的理解偏差"

2. **Given** Day 3 复习未完成或学习者忽略了提醒 **When** Day 7 到来 **Then** 第二次复习提醒弹出 **And** 通知优先级提升为"建议尽快复习"**And** 通知中包含该概念当前的 FSRS 记忆保持率

3. **Given** FSRS 算法计算出的最优复习时间与 Day 3/Day 7 固定间隔不同 **When** 系统决定提醒时机 **Then** 采用 FSRS 自适应间隔优先、Day 3/Day 7 作为兜底下限 **And** 如果 FSRS 建议更早复习（如 Day 2），则在 Day 2 就提醒 **And** 如果 FSRS 建议更晚（如 Day 5），仍在 Day 3 提醒（不低于 Day 3 下限）

4. **Given** 学习者在 Day 3 完成了复习且答对 **When** FSRS 更新复习间隔 **Then** Day 7 提醒自动取消（已纠正的误解不需要第二次固定提醒）**And** 新的复习时间由 FSRS 算法决定

5. **Given** 知识图谱服务不可用 **When** 系统尝试获取错误标记数据 **Then** 降级到纯 frontmatter 数据（`error_marked_at` + `fsrs_next_review_at`）**And** 提醒仍正常触发，但缺少详细误解描述

6. **Given** 学习者同一天有多个概念需要复习 **When** 提醒触发 **Then** 合并为一条汇总通知"今日有 N 个概念建议复习" **And** 点击通知跳转到 review-queue.md（Story 7.1）

## Tasks / Subtasks

- [ ] Task 1: 实现 FSRS 自适应间隔计算 (AC: #3)
  - [ ] 在 `backend/app/services/mastery_service.py` 中添加 `calculate_next_review` 方法
  - [ ] FSRS 算法：基于 stability/difficulty/retrievability 计算下次最优复习时间
  - [ ] Day 3/Day 7 兜底逻辑：`max(fsrs_next_review, error_marked_at + 3days)`
  - [ ] 单元测试：各种 stability 值下的间隔计算正确性

- [ ] Task 2: 实现 Spaced Repetition 插件提醒集成 (AC: #1, #2)
  - [ ] 配置 Obsidian Spaced Repetition 插件读取 `fsrs_next_review_at` 字段
  - [ ] 创建复习提醒 callout 模板：`> [!review]+ 建议复习：[[concept]] — N 天前标记`
  - [ ] Day 3 提醒文案：处方性措辞"建议复习"
  - [ ] Day 7 提醒文案：升级措辞"建议尽快复习" + 记忆保持率

- [ ] Task 3: 实现复习完成后的提醒取消逻辑 (AC: #4)
  - [ ] 复习答对后更新 frontmatter：清除 `pending_review_day7` 标记
  - [ ] FSRS 重新计算间隔并写入 `fsrs_next_review_at`
  - [ ] 单元测试：Day 3 答对后 Day 7 提醒不再触发

- [ ] Task 4: 实现多概念合并通知 (AC: #6)
  - [ ] 同日多概念时合并为汇总通知
  - [ ] 通知链接到 review-queue.md
  - [ ] 单条概念时直接链接到该概念笔记

- [ ] Task 5: 实现降级策略 (AC: #5)
  - [ ] Graphiti 不可用时 fallback 到 frontmatter 数据
  - [ ] 降级模式下提醒仍触发但缺少详细误解描述
  - [ ] 日志记录降级事件

## Dev Notes

### Architecture
- 复习提醒是间隔复习闭环的核心驱动力，直接影响 Cepeda (2006) d=0.55 效应量的实现
- FSRS 自适应间隔与 Day 3/Day 7 固定间隔的融合策略：FSRS 优先但不低于固定下限
- Spaced Repetition 插件是 Obsidian 社区 top 20 插件，原生支持 frontmatter 日期字段触发

### File Paths
- FSRS 间隔计算：`backend/app/services/mastery_service.py`
- 复习提醒模板：`templates/review-reminder.md`
- 错误标记写入：`backend/app/services/error_classification_service.py`（Story 5.x）
- 概念节点 frontmatter：`wiki/concepts/*.md`（fsrs_next_review_at / error_marked_at）
- Spaced Repetition 插件配置：`.obsidian/plugins/obsidian-spaced-repetition/`

### Testing
- 单元测试：FSRS 间隔计算的边界情况（stability=0 / very high stability / 新节点）
- 集成测试：Day 0 标记错误 → Day 3 提醒触发 → 答对 → Day 7 不触发
- 手动验证：Spaced Repetition 插件的通知弹出行为

### References
- **From PRD**: §1.8 间隔复习 (line 2824-2932)
- **From PRD**: §8.3 旅程 3 错误修正闭环 (line 7012-7021)
- Cepeda et al. (2006): Distributed practice in verbal recall tasks. Psychological Bulletin, d=0.55
- FSRS 算法：open-spaced-repetition/fsrs4anki (ts-fsrs / py-fsrs)

## UAT Script

> 1. 在考察中故意答错一个概念，确认 frontmatter 中 error_marked_at 被写入
> 2. 手动将 error_marked_at 改为 3 天前的日期
> 3. 重启 Obsidian 或等待 Spaced Repetition 插件刷新
> 4. 看到复习提醒通知"建议复习：[[concept]] — 3 天前标记的理解偏差"
> 5. 完成复习并答对
> 6. 将 error_marked_at 改为 7 天前，确认不再收到 Day 7 提醒（因为已纠正）
> 7. 设置 3 个概念同一天到期，确认收到合并通知"今日有 3 个概念建议复习"

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| FSRS 间隔计算 | unit | `pytest tests/unit/test_fsrs_interval.py -x` | 0 failures |
| Day 3/Day 7 兜底 | unit | `pytest tests/unit/test_review_reminder_floor.py -x` | 0 failures |
| 复习完成取消 | unit | `pytest tests/unit/test_review_cancel.py -x` | 0 failures |
| 降级策略 | unit | `pytest tests/unit/test_review_degradation.py -x` | 0 failures |
| 合并通知 | integration | 手动设置多概念同日到期 | 一条汇总通知 |

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
