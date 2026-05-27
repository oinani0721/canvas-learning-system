---
story_id: "4.9"
epic_id: "4"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P1"
estimate_hours: 6
depends_on: ["4.6"]
blocks: []
trace:
  - "FR-EXAM-15"
  - "FR-EXAM-17"
superseded_by: "_bmad-output/implementation-artifacts/epic-5/LITE-5-6.md"
merged_into: "STORY-LITE-5-6"
sprint_v3_status: "merged-into-lite-5-6"
deprecated_date: "2026-05-24"
deprecated_plan: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
---

> ⛔ **[MERGED] 2026-05-24 Sprint v3 简化决策** — 此 Story 合并入 STORY-LITE-5-6
>
> - **合并位置**: `_bmad-output/implementation-artifacts/epic-5/LITE-5-6.md`（待写）
> - **状态登记**: `sprint-status.yaml::sprint_v3_obsidian_hybrid.STORY-LITE-5-6.merges`
> - **合并原因**: 4.9 校准投票数据回源 + 5.6 评分投票是同一闭环 — Sprint v3 合并简化为 single Lite story (2h)
> - ⚠️ **新 session 警告**: 看到此 marker → 不读下方 AC，改读 LITE-5-6 spec
> - **Plan**: `EPIC1-BMAD-DEV-ASSESS-2026-04-17`

# Story 4.9: 校准投票 + 数据同步回源白板

Status: ready-for-dev

## Story
As a 学习者,
I want 考后对 AI 评分投票反馈并同步数据到源白板,
So that AI 评分越来越准确，且学习数据不孤立在检验白板中。

## Acceptance Criteria

1. **Given** Story 4.6 评分完成后话题切换（从一个节点到下一个节点）**When** 系统询问校准投票 **Then** 提示"对 Q{i} 的 AI 评分你觉得？" **And** 选项：accurate（准确）/ too_high（偏高）/ too_low（偏低）/ skip（跳过）**And** 投票是可选的，不强制

2. **Given** 学习者选择了投票选项 **When** 系统记录投票 **Then** 写入 exam_boards/*.md frontmatter 的 `post_exam_calibration[]` 数组 **And** 记录 question_id / vote / user_note（可选）**And** 调用 `record_calibration` MCP 工具

3. **Given** 学习者投票了 too_high 或 too_low **When** 系统处理反馈 **Then** 标记该样本为 few-shot 校准样本 **And** 用于后续评分模型的 in-context learning **And** 随着校准样本积累，评分准确性逐步提升

4. **Given** 考察中产生数据变更 **When** Tips / 新节点 / 掌握度更新 **Then** 所有变更同步回源知识白板 **And** 具体同步项：
   - Tips（考察中新发现的学习要点）→ 写入源白板对应节点的 frontmatter
   - 新节点（new_nodes_pulled）→ 已在 Story 4.8 中创建，此处确保 wikilink 回连到源白板
   - 掌握度变化（BKT/FSRS 更新）→ 已在 Story 4.6 中写入 wiki/concepts/<slug>.md
   **And** 同步记录在 exam_boards/*.md frontmatter 的 `canvas_writebacks[]` 中

5. **Given** 同步过程 **When** 源白板文件被修改 **Then** 修改是增量式的（不覆盖源白板的非考察内容）**And** 使用 frontmatter 字段级更新而非整文件覆盖

6. **Given** 同步过程中源文件被其他进程修改（并发冲突）**When** 检测到冲突 **Then** 保留源文件的修改并追加考察数据 **And** structlog 记录冲突事件

## Tasks / Subtasks

- [ ] Task 1: 实现校准投票 UI (AC: #1)
  - [ ] 在话题切换时调用 AskUserQuestion
  - [ ] 选项：accurate / too_high / too_low / skip
  - [ ] 可选不强制（skip 默认不影响任何数据）

- [ ] Task 2: 实现投票记录 (AC: #2)
  - [ ] 写入 post_exam_calibration[] 数组
  - [ ] 调用 record_calibration MCP 工具
  - [ ] 记录 question_id / vote / user_note

- [ ] Task 3: 实现 few-shot 校准样本标记 (AC: #3)
  - [ ] too_high / too_low 投票标记为校准样本
  - [ ] 存储到 Graphiti 知识图谱供后续 in-context learning
  - [ ] 单元测试：校准样本正确标记和存储

- [ ] Task 4: 实现数据同步回源白板 (AC: #4)
  - [ ] Tips 同步：考察中新 Tips → 源白板节点 frontmatter
  - [ ] 新节点 wikilink 回连：确保源白板和新节点双向链接
  - [ ] 掌握度同步确认（Story 4.6 已处理，此处验证一致性）
  - [ ] canvas_writebacks[] 记录（node / bkt_before / bkt_after / score_delta）

- [ ] Task 5: 实现增量式同步 (AC: #5)
  - [ ] frontmatter 字段级更新（非整文件覆盖）
  - [ ] 保护源白板的非考察内容
  - [ ] 单元测试：同步后源文件非考察字段不变

- [ ] Task 6: 实现并发冲突处理 (AC: #6)
  - [ ] 检测文件修改时间戳冲突
  - [ ] 冲突时保留源文件修改 + 追加考察数据
  - [ ] structlog 记录冲突

## Dev Notes

### Architecture
- 校准投票是 /start_exam_board Step 8 的一部分
- post_exam_calibration[] 与 FR-MEM-03（考后校准投票）对齐
- 数据同步（FR-EXAM-17）是检验白板的核心特性之一——考察不是孤立行为
- canvas_writebacks[] 提供完整的变更审计轨迹
- ExamService.sync_node_to_source_canvas 已有基础框架（Story 6.5）

### File Paths
- 校准投票：/start_exam_board Step 8
- 同步逻辑：`backend/app/services/exam_service.py` (sync_node_to_source_canvas)
- Calibration 工具：`backend/app/mcp/tools/memory_tools.py` (record_calibration)
- Exam frontmatter：exam_boards/*.md
- 源白板：wiki/concepts/<slug>.md

### Testing
- 单元测试：投票记录、few-shot 标记、增量同步、冲突处理
- 集成测试：评分 → 投票 → 同步 → 源白板验证完整链路

### Project Structure Notes
- canvas_writebacks[] 记录每个节点的 before/after/delta
- record_calibration MCP 工具存储到 Graphiti 知识图谱
- 校准样本的统计可靠性阈值：<100 仅收集 / 100-400 趋势参考 / 400+ 统计可靠（FR-MAST-05）

### References
- **From PRD**: §2.3 Step 8 — 考后校准投票 (line 1157-1170)
- **From PRD**: §2.2 frontmatter 的 post_exam_calibration 和 canvas_writebacks (line 998-1015)
- FR-EXAM-15: 校准投票
- FR-EXAM-17: 数据同步回源白板
- FR-MEM-03: 考后校准投票
- FR-MAST-05: 校准统计可靠性阶段

## UAT Script

> 1. 完成一道考察题的评分
> 2. 看到系统询问"对 Q1 的 AI 评分你觉得？"
> 3. 选择"偏高"
> 4. 查看 frontmatter post_exam_calibration，确认投票记录
> 5. 完成全部考察
> 6. 打开源白板的概念节点
> 7. 确认 frontmatter 中掌握度数据已更新
> 8. 确认新发现的概念节点有 wikilink 回连

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| 投票记录 | unit | `pytest tests/unit/test_calibration_vote.py -x` | 0 failures |
| Few-shot 标记 | unit | `pytest tests/unit/test_calibration_sample.py -x` | 0 failures |
| 数据同步 | unit | `pytest tests/unit/test_exam_data_sync.py -x` | 0 failures |
| 增量更新 | unit | `pytest tests/unit/test_incremental_sync.py -x` | 0 failures |
| 并发冲突 | unit | `pytest tests/unit/test_sync_conflict.py -x` | 0 failures |
| 同步集成 | integration | `pytest tests/integration/test_exam_sync_flow.py -x` | 0 failures |

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
