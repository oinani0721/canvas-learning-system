---
doc_type: story
story_id: "3.2"
epic_id: "EPIC-3"
prd_id: "PRD14"
status: ready-for-dev
priority: "P0"
estimate_hours: 4
depends_on: ["3.1"]
blocks: []
trace:
  decisions: []
  bugs: []
---

# Story 3.2: BKT/FSRS 自动选弱项

## Story

As a 系统,
I want 基于 BKT 掌握概率和 FSRS 复习间隔自动选出薄弱节点作为考察范围,
so that 考察聚焦于学习者最需要强化的概念。

## Acceptance Criteria

1. **Given** 学习者启动检验白板
   **When** 系统确定考察范围
   **Then** 从 vault frontmatter 中读取所有概念的 BKT `mastery_score` 和 FSRS `due_date`
   **And** 优先选择 `mastery_score` 最低的 + 已过 FSRS `due_date` 的概念
   **And** 选出 3-5 个概念作为本次考察范围

2. **Given** Graphiti 不可用
   **When** 系统选择考察范围
   **Then** 退回到仅使用 frontmatter 数据的默认先验模式（NFR-DEG-3）
   **And** 系统不报错，正常返回考察范围

3. **Given** vault 中所有概念的 `mastery_score` 均高（> 0.8）且均未到 `due_date`
   **When** 系统确定考察范围
   **Then** 仍按 `mastery_score` 升序选出 3-5 个概念（不返回空列表）

## Tasks / Subtasks

- [ ] Task 1: 后端 — 弱项选择算法 (AC: #1, #3)
  - [ ] 1.1 在 `backend/app/services/exam_board_service.py` 实现 `select_weak_concepts(canvas_id: str, n: int = 5) -> list[ConceptSelection]`
  - [ ] 1.2 读取逻辑：遍历 canvas 下所有概念节点，从 Neo4j 或 frontmatter 缓存获取 `mastery_score`、`due_date`
  - [ ] 1.3 排序算法：计算综合优先级分数 = `(1 - mastery_score) * 0.7 + is_due * 0.3`（`is_due=1` 表示 `due_date <= today`）
  - [ ] 1.4 按优先级降序取前 `min(n, len(concepts))` 个，最少 3 个、最多 5 个
  - [ ] 1.5 返回 `ConceptSelection` 列表：`{ concept_id, concept_name, mastery_score, due_date, priority_score }`

- [ ] Task 2: 后端 — Graphiti 降级处理 (AC: #2)
  - [ ] 2.1 弱项选择只依赖 frontmatter/Neo4j 本地数据，Graphiti 仅用于富化上下文（Story 3.3 阶段）
  - [ ] 2.2 在 `exam_board_service.py` 中 Graphiti 调用包裹 `try/except`，失败时记录 `structlog` 警告并继续
  - [ ] 2.3 `POST /api/v1/exam-board/{exam_board_id}/select-concepts` 端点返回选中概念列表

- [ ] Task 3: 后端 — 与 ExamBoard 创建流程集成 (AC: #1)
  - [ ] 3.1 `create_exam_board()` 调用完成后，自动触发 `select_weak_concepts()`，将结果存入 ExamBoard 节点
  - [ ] 3.2 ExamBoard 节点新增字段：`selected_concepts: list[str]`（concept_id 数组）、`selection_timestamp: datetime`
  - [ ] 3.3 `GET /api/v1/exam-board/{exam_board_id}` 返回包含 `selected_concepts` 的完整白板状态

- [ ] Task 4: 编写测试 (AC: #1, #2, #3)
  - [ ] 4.1 单元测试 `tests/unit/test_weak_selection.py`：验证排序算法正确性、3-5 个约束、全高分时仍返回概念
  - [ ] 4.2 单元测试：Graphiti 不可用时降级路径正确执行（mock Graphiti 抛异常）
  - [ ] 4.3 集成测试：验证 `/select-concepts` 返回 3-5 个概念且格式正确

## Dev Notes

- **排序权重依据**：`(1 - mastery_score) * 0.7 + is_due * 0.3` — BKT 掌握度权重 0.7，FSRS 过期权重 0.3，基于 Corbett & Anderson (1994) BKT 论文和 Settles & Meeder (2016) 间隔复习研究
- **数据来源优先级**：Neo4j 缓存 > frontmatter 文件读取。Neo4j 中概念节点应有 `mastery_score` 和 `due_date` 属性（由 Epic 5 的故事写入）
- **边界情况**：vault 中概念数 < 3 时，返回全部概念（不填充空位）
- **NFR-DEG-3 降级**：Graphiti 在此 Story 中仅影响 Story 3.3 的出题质量，不影响弱项选择本身。降级只需记录日志，不改变 select_weak_concepts 的行为
- **ConceptSelection schema** 定义在 `backend/app/models/exam_board.py`（Pydantic）

### Project Structure Notes

- 核心逻辑：`backend/app/services/exam_board_service.py`（`select_weak_concepts` 函数）
- Pydantic 模型：`backend/app/models/exam_board.py`
- 测试：`backend/tests/unit/test_weak_selection.py`
- 端点：`backend/app/api/v1/endpoints/exam_board.py`

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-3.2] — AC 和 FR 映射（FR7）
- [Source: backend/app/services/rag_service.py] — 后端 service 风格参考
- [Source: docs/_meta/FRONTMATTER-SPEC.md] — mastery_score / due_date 字段定义
- [Source: Corbett & Anderson 1994] — BKT 算法原始论文（mastery 概率更新）
- [Source: Settles & Meeder 2016, ACL] — FSRS/间隔复习调度依据

## UAT Script

> Non-technical user validation: no code terminology, only describe what to click and what to see.

1. **验证选弱项** (AC: #1)
   - 在 vault 中准备至少 5 个笔记，其中 2-3 个设置较低的掌握度分数
   - 触发检验白板（`Cmd+Shift+E`）
   - 检验白板启动后，在调试面板（或开发者工具）中查看选中的概念列表
   - 应该包含掌握度最低的那些概念，且数量在 3-5 个之间
   - 如果选出了掌握度高的概念而非低的，记录 Story 3.2

2. **验证 3-5 个数量约束** (AC: #1, #3)
   - 无论 vault 中有多少笔记，每次检验应该选出 3-5 个概念
   - 如果选出了 0 个、2 个或 6 个以上，记录 Story 3.2 + 实际数量

3. **验证系统降级** (AC: #2)
   - 在网络断开或 Graphiti 服务不可用时触发检验
   - 系统应该正常启动检验白板，不弹出错误
   - 控制台日志中可能有警告，但不影响用户操作
   - 如果系统报错或无法启动，记录 Story 3.2

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-3.2.1 | pytest | `.venv/bin/pytest tests/unit/test_weak_selection.py -x -q` | 0 failed |
| CP-3.2.2 | pytest | `.venv/bin/pytest tests/integration/test_exam_board_api.py::test_select_concepts -x -q` | 0 failed |
| CP-3.2.3 | pytest | `.venv/bin/pytest tests/unit/test_weak_selection.py::test_graphiti_degradation -x -q` | 0 failed |

## User Feedback & Changes

### Feedback Log

<!-- Users write BMAD-ANNO callouts below. Claude scans and dispatches by intent. -->

### Deviation Notes

<!-- Claude auto-fills: summary of historically processed feedback -->

## Dev Agent Record

### Agent Model Used

(to be filled by Dev agent)

### Debug Log References

### Completion Notes List

### File List

## Relations

- EPIC: [[EPIC-3]]
- PRD: [[PRD14]]
- Depends on: [[3.1]]
