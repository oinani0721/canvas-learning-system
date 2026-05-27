---
story_id: "5.6"
epic_id: "5"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P1"
estimate_hours: 6
depends_on: ["5.3"]
blocks: []
trace:
  - "FR-MEM-02"
  - "FR-MEM-03"
superseded_by: "_bmad-output/implementation-artifacts/epic-5/LITE-5-6.md"
merges_in_lite: "_bmad-output/implementation-artifacts/epic-4/4-9-calibration-vote-data-sync.md"
sprint_v3_status: "deprecated-by-lite-simplification"
deprecated_date: "2026-05-24"
deprecated_plan: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
---

> ⛔ **[DEPRECATED] 2026-05-24 Sprint v3 简化决策** — Lite 版替代此完整 spec
>
> - **替代 spec**: `_bmad-output/implementation-artifacts/epic-5/LITE-5-6.md`（待写, 合并 4.9 一起做）
> - **状态登记**: `sprint-status.yaml::sprint_v3_obsidian_hybrid.STORY-LITE-5-6`
> - **简化原因**: 完整 5h 版含 4 选项投票 + 8.3 元认知 2x2 矩阵 — Sprint v3 砍 8.3 矩阵（400+ 题后回头），**只 accurate/too_high/too_low/skip 投票 + 本地回写** (2h)
> - ⚠️ **新 session 警告**: 看到此 marker → 不读下方 AC，改读 Lite spec 或 sprint-status entry
> - **Plan**: `EPIC1-BMAD-DEV-ASSESS-2026-04-17`

# Story 5.6: 校准数据 + 评分投票

Status: ready-for-dev

## Story
As a 系统,
I want 记录学习者的考后校准投票（准确/偏高/偏低）和 few-shot 校准样本标记,
So that 评分精度持续改进，学习者的元认知偏差被追踪（FR-MAST-05 2x2 置信度矩阵）。

## Acceptance Criteria

1. **Given** 考察评分完成后学习者看到 AI 评分结果 **When** 学习者投票 `accurate`（准确）/ `too_high`（偏高）/ `too_low`（偏低）**Then** 调用 `record_calibration` MCP 工具记录投票 **And** 投票数据包含 `{node_id, predicted_score, actual_grade, vote, timestamp}`

2. **Given** 投票被记录 **When** 系统检测到该投票特别有代表性 **Then** 标记为 `few_shot_sample: true` **And** few-shot 样本将被用于后续 AI 评分 prompt 的上下文（提高评分一致性）**And** few-shot 标记由后端基于投票一致性自动判定（非用户手动标记）

3. **Given** 学习者累计答题数 < 100 **When** 校准数据被查询 **Then** 返回 `calibration_stage: "collect_only"` **And** calibration_bias 不参与掌握度融合（仅收集阶段）

4. **Given** 学习者累计答题数在 100-400 之间 **When** 校准数据被查询 **Then** 返回 `calibration_stage: "trend"` **And** calibration_bias 计算为趋势值（移动平均）**And** 可作为参考但不具统计显著性

5. **Given** 学习者累计答题数 > 400 **When** 校准数据被查询 **Then** 返回 `calibration_stage: "reliable"` **And** calibration_bias 具有统计可靠性（置信区间可计算）**And** 全权参与掌握度融合

6. **Given** `record_calibration` 被调用 **When** 携带有效 pipeline_token（来自 update_fsrs 步骤）**Then** 记录成功 **And** 更新 frontmatter `calibration_bias` 字段 **And** pipeline 链完成

7. **Given** 多次投票数据累积 **When** 系统计算 calibration_bias **Then** 偏差 = `mean(predicted - actual)` **And** 负值表示 overconfidence（自我高估）**And** 正值表示 underconfidence（自我低估）**And** 写入 frontmatter `calibration_bias` 字段

## Tasks / Subtasks

- [ ] Task 1: 实现投票记录 + few-shot 标记 (AC: #1, #2)
  - [ ] 验证 `record_calibration` MCP 工具（memory_tools.py）已存在
  - [ ] 添加 `vote` 字段（accurate/too_high/too_low）到 RecordCalibrationInput
  - [ ] 实现 few-shot 自动标记逻辑：连续 3 次投票一致 → 标记最近一次为 few_shot_sample
  - [ ] few-shot 样本存入独立集合，供 AI 评分 prompt 使用
  - [ ] 单元测试：投票记录正确、few-shot 标记逻辑正确

- [ ] Task 2: 实现 3 阶段渐进校准 (AC: #3, #4, #5)
  - [ ] 创建 `get_calibration_stage(total_interactions: int) -> str` 函数
  - [ ] < 100: "collect_only" → calibration_bias 设为 0.0（不参与融合）
  - [ ] 100-400: "trend" → calibration_bias 使用最近 50 次的移动平均
  - [ ] > 400: "reliable" → calibration_bias 使用全量数据 + 置信区间
  - [ ] 在 `CalibrationTracker`（calibration_tracker.py）中集成阶段逻辑
  - [ ] 单元测试：各阶段的阈值判断和计算正确

- [ ] Task 3: calibration_bias 计算 + frontmatter 写回 (AC: #6, #7)
  - [ ] calibration_bias = mean(predicted - actual) over calibration history
  - [ ] 负值 = overconfidence，正值 = underconfidence
  - [ ] 写入 frontmatter `calibration_bias` 字段（原子写入）
  - [ ] 验证 pipeline_token（来自 update_fsrs 步骤，Story 5.4）
  - [ ] 单元测试：偏差计算准确、frontmatter 写回正确

- [ ] Task 4: 查询接口 + 阶段信息返回 (AC: #3, #4, #5)
  - [ ] 在 `record_calibration` 返回值中添加 `calibration_stage` 和 `total_interactions`
  - [ ] 在 `query_mastery` 返回值中包含 calibration_stage 信息
  - [ ] 单元测试：各阶段返回值正确

## Dev Notes

### Architecture
- 校准数据追踪是 FR-MAST-05 的 2x2 置信度矩阵实现
- 现有 `CalibrationTracker`（calibration_tracker.py）已实现元认知校准追踪框架
- 3 阶段渐进（collect → trend → reliable）基于 Area9 Rhapsode 自适应学习平台的校准方法
- few-shot 标记的目的是收集高质量的评分校准样本，用于改进 AI 评分 prompt 的一致性
- calibration_bias 作为 5 信号融合的第 4 个信号（权重 0.15），但仅在 > 400 题后全权参与

### File Paths
- 校准追踪器：`backend/app/services/calibration_tracker.py`
- MCP 工具：`backend/app/mcp/tools/memory_tools.py` (record_calibration, line 249-328)
- RecordCalibrationInput：`backend/app/mcp/tools/memory_tools.py` (line 60-85)
- Pipeline token：`backend/app/mcp/pipeline_token.py` (update_fsrs → record_calibration)
- frontmatter schema：anchor PRD §1.5 (calibration_bias, line 643)

### Testing
- 单元测试：投票记录、few-shot 标记、3 阶段阈值、偏差计算
- 集成测试：完整的投票 → 计算 → frontmatter 写回链路
- 统计测试：100/400 样本阈值的阶段切换

### References
- **From PRD**: §1.5 calibration_bias 字段 (line 643)
- **From PRD**: FR-MAST-05 2x2 置信度矩阵三阶段
- Area9 Rhapsode: 自适应学习平台元认知校准方法
- `backend/app/services/calibration_tracker.py`: 现有校准追踪框架

## UAT Script

> 1. 完成一道考察题，看到 AI 评分结果
> 2. 投票"偏高"（too_high），确认投票被记录
> 3. 重复 10 次考察 + 投票
> 4. 检查 frontmatter calibration_bias 字段出现且为负值（overconfidence 方向）
> 5. 查看返回值中 calibration_stage 为 "collect_only"（不足 100 题）
> 6. 确认 mastery_level 融合中 calibration_bias 权重为 0（collect_only 阶段不参与）

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| 投票记录 | unit | `pytest tests/unit/test_calibration_vote.py -x` | 0 failures |
| few-shot 标记 | unit | `pytest tests/unit/test_fewshot_marking.py -x` | 0 failures |
| 3 阶段渐进 | unit | `pytest tests/unit/test_calibration_stages.py -x` | 0 failures |
| calibration_bias 计算 | unit | `pytest tests/unit/test_calibration_bias.py -x` | 0 failures |
| 校准 MCP 链路 | integration | `pytest tests/integration/test_calibration_mcp.py -x` | 0 failures |

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
