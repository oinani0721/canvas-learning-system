# Story 6.10: 出题难度匹配评估

Status: ready-for-dev

## Story

As a 系统,
I want 评估出题难度与用户掌握度的匹配程度,
So that 考察不会过难也不会过简单。

## Acceptance Criteria

1. **AC-1: 出题难度匹配率计算**
   - **Given** 考察过程中 AI 出题
   - **When** 出题完成并评分后
   - **Then** 系统计算出题难度匹配率（题目难度 vs 用户 BKT p_mastery + FSRS R 的 effective_proficiency）
   - **And** 匹配判定逻辑：题目估计难度落在 effective_proficiency ± 0.2 范围内（clamp 到 [0, 1]）视为匹配
   - **And** 匹配结果记录到结构化日志（node_id / proficiency / estimated_difficulty / is_matched / lower_bound / upper_bound / question_preview / timestamp）

2. **AC-2: 出题难度匹配率 >= 70%**
   - **Given** 系统累积了多次考察的出题记录
   - **When** 查询难度匹配统计
   - **Then** 提供滑动窗口统计（最近 50 题）的匹配率
   - **And** 匹配率 >= 70% 视为健康
   - **And** 匹配率 < 70% 时日志 WARNING 告警

3. **AC-3: 匹配率过低时触发出题策略自动调整**
   - **Given** 滑动窗口匹配率低于 70%
   - **When** 连续 3 题匹配失败
   - **Then** 通过 EventBus 发布 DIFFICULTY_MISMATCH_ALERT 事件（Tier 3 best-effort）
   - **And** 出题 Prompt 注入当前 proficiency 作为难度校准参考
   - **And** 调整建议记录到日志供后续分析

4. **AC-4: 管道健康指标实时可查**
   - **Given** 系统运行中
   - **When** 查询管道健康指标（`GET /api/v1/system/qa-metrics`）
   - **Then** 返回出题难度匹配率统计（window_size / total_in_window / matched_count / match_rate / is_healthy）
   - **And** 可附带最近 10 条匹配记录明细

## Tasks / Subtasks

- [ ] Task 1: 审查并激活现有 DifficultyMatcher 服务 (AC: #1, #2)
  - [ ] 1.1 审查 `backend/app/services/difficulty_matcher.py` — 已有完整实现（来自旧 Story 7.4），确认代码质量和逻辑正确性
  - [ ] 1.2 审查 `backend/app/models/qa_models.py` — 已有 DifficultyMatchRecord、DifficultyMatchStats 模型
  - [ ] 1.3 确认 `compute_difficulty_range()` 逻辑正确：proficiency ± 0.2，clamp [0, 1]
  - [ ] 1.4 确认 `estimate_difficulty()` LLM 调用经过 LiteLLM 统一调用层，few-shot prompt 合理
  - [ ] 1.5 确认 `evaluate()` 方法完整：计算范围→LLM 估计难度→匹配判定→持久化→滑动窗口更新→告警检查
  - [ ] 1.6 确认滑动窗口（deque maxlen=50）和 70% 阈值逻辑正确

- [ ] Task 2: 集成到考察出题流程 (AC: #1, #3)
  - [ ] 2.1 在 `backend/app/mcp/tools/exam_tools.py` 的 `generate_question` 流程末尾异步调用 `DifficultyMatcher.evaluate()`
  - [ ] 2.2 从 `MasteryEngine.effective_proficiency()` 获取当前节点的 proficiency 值传入 evaluate()
  - [ ] 2.3 确保 evaluate() 调用是异步 fire-and-forget（不阻塞题目返回给用户）
  - [ ] 2.4 evaluate() 失败时静默降级（记录 ERROR 日志，不影响出题流程）

- [ ] Task 3: 出题策略自动调整机制 (AC: #3)
  - [ ] 3.1 在 DifficultyMatcher 中添加连续失败计数器（consecutive_mismatches）
  - [ ] 3.2 连续 3 题匹配失败时，通过 EventBus 发布 DIFFICULTY_MISMATCH_ALERT 事件（Tier 3）
  - [ ] 3.3 在 `canvas_events.py` 的 LearningEventType 中注册 DIFFICULTY_MISMATCH_ALERT 事件类型
  - [ ] 3.4 实现调整策略：将当前 effective_proficiency 注入出题 Prompt 的 ACP 数据包（Layer 3）作为 `target_difficulty_hint`
  - [ ] 3.5 调整触发后重置连续失败计数器

- [ ] Task 4: REST API 端点验证 (AC: #4)
  - [ ] 4.1 确认 `GET /api/v1/system/qa-metrics` 端点已存在于 `backend/app/api/v1/system.py`，正确调用 `get_difficulty_matcher()` 返回统计
  - [ ] 4.2 确认 `get_stats_with_recent()` 正确返回最近 10 条记录明细
  - [ ] 4.3 确认管道健康指标中 `_check_difficulty_match_rate()` 正确读取 DifficultyMatcher 滑动窗口

- [ ] Task 5: 测试验证 (AC: #1, #2, #3, #4)
  - [ ] 5.1 单元测试 `compute_difficulty_range()` 边界条件（proficiency=0.0/0.1/0.5/0.9/1.0）
  - [ ] 5.2 单元测试 `is_difficulty_matched()` 匹配/不匹配场景
  - [ ] 5.3 单元测试滑动窗口统计计算和阈值告警
  - [ ] 5.4 集成测试：模拟 generate_question → evaluate 异步调用链
  - [ ] 5.5 集成测试：连续 3 次失配 → EventBus 事件发布验证

## Dev Notes

- **BKT p_mastery context for difficulty calibration**: DifficultyMatcher 依赖 MasteryEngine 的 `effective_proficiency(concept)` 方法获取用户掌握度。该方法结合 BKT p_mastery 和 FSRS retrievability (R)，通过 `min(p_mastery, R)` 或 MasteryFusionEngine（Story 5.6）计算得出。proficiency 值域 [0.0, 1.0]，用于划定可接受难度区间。
- **Depends on Story 5.1 (BKT+FSRS system)**: MasteryEngine 和 ConceptState 由 Story 5.1 建立。effective_proficiency 计算、BKT 参数更新、FSRS 调度均依赖 Story 5.1 的基础设施。
- **Depends on Story 6.3 (AI question generation)**: 出题流程由 Story 6.3 的 ACP 数据包驱动，DifficultyMatcher 在出题完成后异步评估。Story 6.3 的 Prompt 5 层结构中 Layer 3 (ACP) 是注入 target_difficulty_hint 的位置。
- **Existing mastery/difficulty code**: `backend/app/services/difficulty_matcher.py` 已有完整的 DifficultyMatcher 实现（来自旧 Story 7.4 规划）。核心逻辑已实现：difficulty range 计算、LLM difficulty 估计、滑动窗口统计、SQLite 持久化。**但尚未集成到实际考察流程中**（exam_tools.py 和 event_handlers.py 中无调用）。
- **已有但未连通的组件**:
  - `difficulty_matcher.py` — 完整实现，singleton 模式，SQLite 持久化到 `backend/data/qa_metrics.db`
  - `qa_models.py` — DifficultyMatchRecord、DifficultyMatchStats Pydantic 模型已定义
  - `system.py` — `GET /api/v1/system/qa-metrics` 端点已实现，调用 `get_difficulty_matcher()`
  - `health_monitor.py` — `_check_difficulty_match_rate()` 已实现
  - `canvas_events.py` — `DIFFICULTY_EVALUATED` 事件类型已注册
- **关键集成点**: `exam_tools.py:generate_question()` → 异步调用 `DifficultyMatcher.evaluate()` → EventBus DIFFICULTY_EVALUATED (Tier 3)。评估不阻塞出题，失败不影响用户体验。
- **LLM 调用**: difficulty 估计使用 LiteLLM `acompletion()` 统一调用层，few-shot prompt 包含 5 档难度定义和 3 个示例。temperature=0 确保稳定性。fallback 默认 0.5（中等难度）。

### References

- `backend/app/services/difficulty_matcher.py` — DifficultyMatcher 主服务（已有完整实现）
- `backend/app/models/qa_models.py` — DifficultyMatchRecord, DifficultyMatchStats 模型
- `backend/app/services/mastery_engine.py` — MasteryEngine.effective_proficiency() 掌握度计算
- `backend/app/models/mastery_state.py` — ConceptState 数据模型
- `backend/app/mcp/tools/exam_tools.py` — generate_question MCP 工具（集成点）
- `backend/app/api/v1/system.py` — GET /api/v1/system/qa-metrics 端点
- `backend/app/services/health_monitor.py` — _check_difficulty_match_rate() 管道健康检查
- `backend/app/models/canvas_events.py` — DIFFICULTY_EVALUATED 事件类型
- `backend/app/services/event_bus.py` — EventBus 三级优先级事件分发
- `_bmad-output/implementation-artifacts/5-1-bkt-fsrs-mastery-system.md` — Story 5.1 BKT+FSRS 精通度系统
- `_bmad-output/implementation-artifacts/6-3-ai-precise-question-acp.md` — Story 6.3 AI 精准出题
- `_bmad-output/implementation-artifacts/7-4-difficulty-matching-extraction-validation.md` — 旧 Story 7.4（本 Story 的前身，包含更多 QA 内容）
- `_bmad-output/planning-artifacts/epics.md` — Epic 6 检验白板与递归考察
- `_bmad-output/planning-artifacts/architecture.md` — 能力域 9 质量保证 FR-QA-06

## Dev Agent Record

### Agent Model Used


### Debug Log References


### Completion Notes List


### File List

