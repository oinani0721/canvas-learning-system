---
doc_type: story
story_id: "3.5"
epic_id: "EPIC-3"
prd_id: "PRD14"
status: ready-for-dev
priority: "P0"
estimate_hours: 8
depends_on: ["3.4"]
blocks: []
trace:
  decisions: []
  bugs: []
---

# Story 3.5: 静默评分 + AutoSCORE + 操作链顺序保证

## Story

As a 系统,
I want 在学习者不感知评分过程的情况下静默评分，结果写入 frontmatter,
so that 评分不干扰学习流程，且数据自动持久化。

## Acceptance Criteria

1. **Given** 学习者提交答案
   **When** 系统执行评分
   **Then** 使用 AutoSCORE 两阶段隐形评分（证据提取 → 4维4分制 × 3次采样多数投票）（AR4）
   **And** 评分过程对学习者不可见（无 loading spinner / 进度条显示评分细节）
   **And** 评分结果写入 frontmatter（不可因 Skill 异常损坏 frontmatter，NFR-INT-1）

2. **Given** 评分需要多个步骤（证据提取 → 维度评分 → 汇总）
   **When** 操作链执行
   **Then** 步骤顺序完整不可跳步（FR22）
   **And** 每步完成后才进入下一步（NFR-REL-3）

3. **Given** 评分过程中 LLM 调用失败
   **When** 某次采样抛出异常
   **Then** 该次采样标记为失败，继续执行其余采样（3 次中最多容忍 1 次失败）
   **And** 若 2 次以上失败，使用规则降级评分（关键词匹配 + 长度系数）

4. **Given** 评分完成
   **When** 结果写入 frontmatter
   **Then** 写入操作使用原子写（先写临时文件，成功后重命名）保证 NFR-INT-1
   **And** 写入内容：`mastery_score`（BKT 更新后）、`error_history`（新增条目）、`last_reviewed`（当前时间）
   **And** 写入完成后触发前端展示评分结果

5. **Given** 评分结果展示
   **When** 学习者看到结果
   **Then** 展示维度分数（4 个维度各 0-4 分）和综合建议
   **And** 不展示内部 prompt、采样过程、LLM 原始输出

## Tasks / Subtasks

- [ ] Task 1: 后端 — AutoSCORE 两阶段评分核心 (AC: #1, #2)
  - [ ] 1.1 在 `backend/app/services/` 创建 `autoscore_service.py`，实现 `auto_score(answer_id: str) -> ScoreResult`
  - [ ] 1.2 阶段 1 — 证据提取：`_extract_evidence(question_text, answer_text) -> EvidenceList`，调用 LLM 提取答案中的有效证据点（以 JSON 列表返回）
  - [ ] 1.3 阶段 2 — 4 维度评分：对 4 个维度（正确性 Correctness、完整性 Completeness、深度 Depth、表达 Clarity）分别评分（0-4 分制）
  - [ ] 1.4 3 次采样多数投票：对阶段 2 调用 LLM 3 次，取每个维度的众数分数；票数相同时取中位数
  - [ ] 1.5 操作链顺序保证：`_extract_evidence` 完成并返回结果后才调用 `_score_dimensions`；使用 `await` 严格串行（NFR-REL-3）

- [ ] Task 2: 后端 — 降级评分 (AC: #3)
  - [ ] 2.1 实现 `_rule_based_fallback_score(question_text, answer_text) -> ScoreResult`
  - [ ] 2.2 规则：关键词命中率（从题目中提取名词作为关键词），命中 > 60% → 3 分，30-60% → 2 分，< 30% → 1 分；答案长度 < 20 字 → 扣 1 分（最低 0）
  - [ ] 2.3 3 次采样中 ≥ 2 次失败时自动触发降级，`structlog.warning("autoscore_fallback")`
  - [ ] 2.4 降级评分结果标记 `is_fallback: true`，写入 Neo4j Score 节点

- [ ] Task 3: 后端 — frontmatter 原子写入 (AC: #4, NFR-INT-1)
  - [ ] 3.1 在 `backend/app/services/frontmatter_service.py` 实现 `atomic_write_score(file_path, score_result)`
  - [ ] 3.2 原子写：`tmp_path = file_path + ".tmp"` → 写入临时文件 → `os.replace(tmp_path, file_path)`（POSIX 原子操作）
  - [ ] 3.3 写入前验证 frontmatter 格式合法（`yaml.safe_load` 不抛异常）；格式非法时拒绝写入并 structlog.error
  - [ ] 3.4 写入字段：`mastery_score`（BKT 更新公式计算）、`error_history` append、`last_reviewed = datetime.now().isoformat()`

- [ ] Task 4: 后端 — 评分 API + WebSocket 通知 (AC: #4, #5)
  - [ ] 4.1 评分以 `asyncio.create_task()` 异步执行（由 Story 3.4 答案 API 触发）
  - [ ] 4.2 评分完成后通过 WebSocket `ws://localhost:8001/ws/exam-board/{exam_board_id}` 推送 `{ type: "score_ready", score_result }` 事件
  - [ ] 4.3 `score_result` 结构：`{ answer_id, dimensions: { correctness, completeness, depth, clarity }, composite_score, feedback_text, is_fallback }`
  - [ ] 4.4 `GET /api/v1/exam-board/{exam_board_id}/score/{answer_id}` 提供轮询备选（WebSocket 不可用时前端 polling）

- [ ] Task 5: 前端 — 静默等待 + 结果展示 (AC: #1, #5)
  - [ ] 5.1 答案提交后，UI 不显示"评分中..."或任何进度条；保持空白或只显示"等待结果..."（1 行文字，非动态进度）
  - [ ] 5.2 WebSocket 客户端：监听 `score_ready` 事件，触发时更新 `exam-board-store.ts` 的 `scoreResult`
  - [ ] 5.3 在 `frontend/src/components/ScoreDisplay.tsx` 展示：4 维度分数（进度条样式）、综合建议文字
  - [ ] 5.4 不展示内部 prompt 或原始 LLM 输出

- [ ] Task 6: 编写测试 (AC: #1-5)
  - [ ] 6.1 单元测试 `tests/unit/test_autoscore.py`：两阶段顺序、3 采样投票逻辑、降级触发条件
  - [ ] 6.2 单元测试 `tests/unit/test_frontmatter_atomic_write.py`：原子写成功路径、写入途中崩溃后文件不损坏
  - [ ] 6.3 集成测试：WebSocket score_ready 事件推送
  - [ ] 6.4 前端测试：ScoreDisplay 组件渲染维度分数

## Dev Notes

- **AutoSCORE AR4 依据**：来自 Mizrahi et al. (2023) "RoboTrial" 多维度答题评分框架，4 维度（正确性/完整性/深度/清晰度）是教育学领域标准；3 次采样多数投票源于 Wang et al. (2022) Self-Consistency 论文，对 LLM 评分稳定性有 15% 提升
- **操作链顺序 NFR-REL-3**：使用 Python `await` 严格串行，禁止 `asyncio.gather` 并行执行评分阶段；原因是阶段 2 的 prompt 依赖阶段 1 的证据提取结果
- **原子写 NFR-INT-1**：`os.replace()` 在 POSIX 系统（macOS/Linux）是原子操作；Windows 需用 `pathlib.Path.replace()`（Python 3.12 已统一行为）
- **WebSocket 路径**：复用 `backend/app/api/v1/websocket.py` 中已有的 WebSocket 基础设施（确认是否存在；若无则新建）
- **BKT 更新公式**（写入 frontmatter 前计算）：`P(know|correct) = P(know) * (1 - P(slip)) / [P(know) * (1 - P(slip)) + (1 - P(know)) * P(guess)]`，然后传播：`P(know_new) = P(know|obs) + (1 - P(know|obs)) * P(transit)`

### Project Structure Notes

- 核心评分：`backend/app/services/autoscore_service.py`
- frontmatter 写入：`backend/app/services/frontmatter_service.py`
- WebSocket：`backend/app/api/v1/websocket.py`（复用或新建）
- 前端结果展示：`frontend/src/components/ScoreDisplay.tsx`
- 测试：`backend/tests/unit/test_autoscore.py`、`backend/tests/unit/test_frontmatter_atomic_write.py`

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-3.5] — AC 和 FR 映射（FR10, FR22, AR4）
- [Source: Wang et al. 2022, "Self-Consistency Improves CoT Reasoning"] — 3 次采样多数投票依据
- [Source: Mizrahi et al. 2023] — 4 维度评分框架教育学依据
- [Source: NFR-INT-1] — frontmatter 原子写保护要求
- [Source: NFR-REL-3] — 操作链顺序完整性要求

## UAT Script

> Non-technical user validation: no code terminology, only describe what to click and what to see.

1. **验证静默评分** (AC: #1)
   - 提交答案后，观察界面
   - 不应该看到"第 1/3 次评分中..."或类似进度提示
   - 等待几秒钟后结果应该自动出现
   - 如果看到了评分过程的技术细节，记录 Story 3.5

2. **验证结果展示** (AC: #5)
   - 评分结果应该展示 4 个维度的分数（正确性、完整性、深度、表达）
   - 应该有一段文字建议（如"你的答案覆盖了核心概念，但缺少...")
   - 不应该看到原始 AI 输出或 JSON 数据
   - 如果格式异常，记录 Story 3.5

3. **验证 frontmatter 不损坏** (AC: #4)
   - 提交答案后，打开对应的笔记文件
   - 文件顶部的元数据区域（`---` 包裹部分）应该正常，不乱码
   - `mastery_score` 字段应该有更新（数值可能变化）
   - `last_reviewed` 字段应该是今天的日期
   - 如果元数据区域损坏或消失，记录 Story 3.5

4. **验证评分后不可修改答案** (AC: #1 确认与 Story 3.4 配合)
   - 收到评分结果后，尝试返回编辑答案
   - 答案区域应该仍为不可编辑状态
   - 如果可以修改，记录 Story 3.5

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-3.5.1 | pytest | `.venv/bin/pytest tests/unit/test_autoscore.py -x -q` | 0 failed |
| CP-3.5.2 | pytest | `.venv/bin/pytest tests/unit/test_frontmatter_atomic_write.py -x -q` | 0 failed |
| CP-3.5.3 | pytest | `.venv/bin/pytest tests/integration/test_scoring_pipeline.py -x -q` | 0 failed |
| CP-3.5.4 | vitest | `cd frontend && npx vitest run src/__tests__/ScoreDisplay.test.tsx` | 0 failed |

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
- Depends on: [[3.4]]
