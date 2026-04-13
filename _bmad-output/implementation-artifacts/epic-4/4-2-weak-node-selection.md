---
story_id: "4.2"
epic_id: "4"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P0"
estimate_hours: 6
depends_on: ["4.1"]
blocks: ["4.3"]
trace:
  - "FR-EXAM-02"
---

# Story 4.2: 薄弱节点选题

Status: ready-for-dev

## Story
As a 系统,
I want 基于 BKT/FSRS 掌握度自动选出薄弱节点,
So that 考察聚焦学习者最需要强化的知识。

## Acceptance Criteria

1. **Given** 学习者通过 Story 4.1 防嵌套检查后启动考察 **When** 系统调用 `query_mastery` MCP 工具查询源白板关联的所有节点 **Then** 返回每个节点的 `p_mastery`（BKT）和 `fsrs_retrievability`（FSRS）掌握度分数 **And** 查询结果包含 `effective_proficiency` 融合分数

2. **Given** 查询到所有节点的掌握度数据 **When** 系统排序选题 **Then** 按 `effective_proficiency` 升序排列（最薄弱的排最前）**And** 选出 top_k 个节点（默认 k=10，frontmatter `max_questions` 可配置）

3. **Given** 排序后的节点列表 **When** 系统过滤已掌握节点 **Then** 排除 `effective_proficiency >= 0.90` 的节点 **And** 如果 `bkt_threshold` 在 frontmatter 中配置，使用该阈值替代默认 0.90

4. **Given** 过滤后的薄弱节点列表 **When** 节点数量不足（少于 3 个）**Then** 放宽阈值到 0.95 重新选择 **And** 如果仍不足则选择所有可用节点并在日志中记录

5. **Given** 选题完成 **When** 写入 exam_boards/*.md frontmatter **Then** `selected_nodes` 数组包含所有选出节点的 slug **And** `bkt_threshold` 记录实际使用的阈值

6. **Given** 某些节点没有掌握度数据（新创建的节点）**When** 系统处理缺失数据 **Then** 将无数据节点视为 `effective_proficiency = 0.50`（中等，需要考察）**And** 在 `mastery_degraded` 字段标记为 `"concept_not_found"`

## Tasks / Subtasks

- [ ] Task 1: 实现批量掌握度查询 (AC: #1)
  - [ ] 扩展 query_mastery 支持批量查询（接受 canvas_slug 参数，返回该白板下所有节点）
  - [ ] 返回字段：node_id, p_mastery, fsrs_stability, fsrs_retrievability, effective_proficiency, interaction_count
  - [ ] 处理 mastery_degraded 各种状态（concept_not_found / exception / fusion_fallback）

- [ ] Task 2: 实现薄弱节点排序与过滤算法 (AC: #2, #3)
  - [ ] 按 effective_proficiency 升序排序
  - [ ] 过滤 >= 0.90（或自定义 bkt_threshold）的节点
  - [ ] 截取 top_k 个节点
  - [ ] 单元测试：各种分布下的排序和过滤正确性

- [ ] Task 3: 实现节点数量不足时的降级策略 (AC: #4)
  - [ ] 不足 3 个时放宽到 0.95
  - [ ] 仍不足时选择所有可用节点
  - [ ] structlog 记录降级事件

- [ ] Task 4: 写入 frontmatter selected_nodes (AC: #5)
  - [ ] 更新 exam_boards/*.md 的 selected_nodes 数组
  - [ ] 记录 bkt_threshold 实际使用值

- [ ] Task 5: 处理缺失掌握度数据 (AC: #6)
  - [ ] 新节点默认 effective_proficiency = 0.50
  - [ ] mastery_degraded 标记传递

## Dev Notes

### Architecture
- query_mastery MCP 工具已存在于 `backend/app/mcp/tools/mastery_tools.py`
- 当前 QueryMasteryInput 只支持单节点查询（node_id），需扩展支持批量查询或在 skill 层循环调用
- effective_proficiency 是 5 信号融合的结果（BKT + FSRS + 错误历史 + 校准偏差 + 自评置信度）
- mastery_degraded 已有跨层可观测性支持（QueryMasteryOutput 定义中已包含）

### File Paths
- MCP 工具：`backend/app/mcp/tools/mastery_tools.py` (QueryMasteryInput/Output)
- Mastery store：`backend/app/services/mastery_store.py`
- Fusion engine：`backend/app/services/mastery_fusion.py`
- Exam frontmatter schema：anchor PRD §2.2

### Testing
- 单元测试：节点排序、阈值过滤、降级策略
- 集成测试：query_mastery → 排序 → 写入 frontmatter 完整链路

### Project Structure Notes
- FSRS 参数通过 frontmatter 的 `fsrs_overdue_only` 控制是否只考已 overdue 节点
- 掌握度数据存储在 wiki/concepts/<slug>.md 的 frontmatter 中

### References
- **From PRD**: §2.2 exam_boards/*.md frontmatter Schema (line 940-1016)
- **From PRD**: §2.3 Step 4 — query_mastery 选薄弱节点 (line 1063-1075)
- `backend/app/mcp/tools/mastery_tools.py`: QueryMasteryOutput 定义
- FR-MAST-03: 5 信号融合掌握度评估

## UAT Script

> 1. 打开一个有 5+ 个概念节点的知识白板
> 2. 确认部分节点掌握度 >= 0.90（通过之前的考察）
> 3. 触发 `/start_exam_board`
> 4. 查看生成的 exam_boards/*.md 的 frontmatter
> 5. 确认 selected_nodes 不包含掌握度 >= 0.90 的节点
> 6. 确认 selected_nodes 按薄弱程度排序（最薄弱的在前）
> 7. 确认 bkt_threshold 字段值正确

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| 批量查询 | unit | `pytest tests/unit/test_mastery_batch_query.py -x` | 0 failures |
| 排序过滤算法 | unit | `pytest tests/unit/test_weak_node_selection.py -x` | 0 failures |
| 降级策略 | unit | `pytest tests/unit/test_node_selection_fallback.py -x` | 0 failures |
| 缺失数据处理 | unit | `pytest tests/unit/test_mastery_missing_data.py -x` | 0 failures |
| 选题集成 | integration | `pytest tests/integration/test_exam_node_selection.py -x` | 0 failures |

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
