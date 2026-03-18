# Story 6.9: 评分忠实度深化检查

Status: ready-for-dev

## Story

As a 系统,
I want 在检验白板评分场景中深化忠实度检查——确保 AutoSCORE 评分基于学生实际回答而非幻觉,
So that 评分可靠，精通度更新准确。

## Acceptance Criteria

1. **AC-1: Stage 1 证据溯源验证（FR-QA-01 深化）**
   - **Given** AutoSCORE 两阶段评分完成（Stage 1 证据提取 → Stage 2 逐维打分）
   - **When** 忠实度校验管道执行
   - **Then** 逐条检查 Stage 1 提取的证据是否能在学生原文（conversation_segment）中找到对应文本
   - **And** 每条证据标记为 GROUNDED（原文可溯源）或 UNGROUNDED（原文中找不到对应）
   - **And** 证据忠实度分数 = |GROUNDED 证据| / |总证据数|

2. **AC-2: Stage 2 评分-证据一致性检查（FR-QA-01 深化）**
   - **Given** Stage 1 证据提取完成且 Stage 2 各维度打分完成
   - **When** 一致性校验执行
   - **Then** 检查 Stage 2 各维度打分是否与 Stage 1 提取的证据一致
   - **And** 使用 LLM 判断每维度的 justification 是否被 Stage 1 证据所支持
   - **And** 评分忠实度 Faithfulness >= 0.85 视为通过
   - **And** Faithfulness < 0.85 标记该次评分为"忠实度不足"

3. **AC-3: 自一致性低信心维度检测（FR-EXAM-04 关联）**
   - **Given** 3 次采样评分结果已产出
   - **When** 分析各维度分差
   - **Then** 任何维度 3 次采样中 max-min > 1 标记为"AI 低信心"
   - **And** 低信心维度在忠实度检查报告中额外标注
   - **And** 整体低信心（2+ 维度低信心）触发评分降级

4. **AC-4: 低信心评分不更新精通度**
   - **Given** 忠实度检查完成
   - **When** 评分被标记为"忠实度不足"或整体"AI 低信心"
   - **Then** 该次评分不触发 SCORE_SUBMITTED 事件
   - **And** BKT/FSRS 精通度不更新（保持当前值等待下次考察）
   - **And** 评分结果仍记录到考察历史（标注为"待验证"）
   - **And** 下次考察该节点时自动重新评分

5. **AC-5: 忠实度检查结构化日志**
   - **Given** 忠实度深化检查执行
   - **When** 检查完成
   - **Then** 结构化日志记录：检查类型（scoring_faithfulness）、证据溯源分数、评分一致性分数、低信心维度列表、是否降级、耗时
   - **And** 日志格式兼容 Story 7.1 已有 FAITHFULNESS_CHECK_LOG_SCHEMA

## Tasks / Subtasks

- [ ] **Task 1: 评分忠实度检查器** (AC: #1, #2)
  - [ ] 1.1 创建 `backend/app/services/scoring_faithfulness.py`：ScoringFaithfulnessChecker 类
  - [ ] 1.2 实现 `verify_evidence_grounding(evidence_points, conversation_segment)` — Stage 1 证据溯源验证
    - 对每条 Stage 1 提取的证据，使用 LLM 判断是否能在学生原文中找到对应
    - 返回每条证据的 GROUNDED/UNGROUNDED 判定及对应原文引用
  - [ ] 1.3 实现 `verify_score_evidence_consistency(rubric_scores, evidence)` — Stage 2 评分-证据一致性
    - 对每个维度，使用 LLM 判断 justification 是否被 Stage 1 证据支持
    - 返回每维度的一致性判定及 Faithfulness 分数
  - [ ] 1.4 实现 `run_full_check(autoscore_result, conversation_segment)` — 完整忠实度检查入口
    - 串联 1.2 和 1.3，合并计算综合 Faithfulness 分数
    - 综合分数 = (证据溯源分数 + 评分一致性分数) / 2
  - [ ] 1.5 编辑后运行 `ruff check` + `ruff format --check`

- [ ] **Task 2: 忠实度检查 Prompt 模板** (AC: #1, #2)
  - [ ] 2.1 创建 `backend/app/prompts/scoring/faithfulness_evidence_grounding.md` — 证据溯源验证 Prompt
    - 输入：证据列表 + 学生原文
    - 输出：每条证据的 GROUNDED/UNGROUNDED + 原文引用位置
  - [ ] 2.2 创建 `backend/app/prompts/scoring/faithfulness_score_consistency.md` — 评分-证据一致性 Prompt
    - 输入：各维度 justification + Stage 1 证据
    - 输出：每维度的一致性判定 + 整体 Faithfulness 分数

- [ ] **Task 3: AutoSCORE 集成——忠实度门控** (AC: #3, #4)
  - [ ] 3.1 修改 `backend/app/services/autoscore.py`：在 `evaluate()` 完成后调用 ScoringFaithfulnessChecker
  - [ ] 3.2 在 AutoScoreResult 模型中追加忠实度检查字段：
    - `faithfulness_score: float` — 综合忠实度分数
    - `faithfulness_passed: bool` — 是否通过忠实度门控 (>= 0.85)
    - `evidence_grounding_score: float` — 证据溯源分数
    - `score_consistency_score: float` — 评分一致性分数
    - `faithfulness_details: dict` — 详细检查结果
  - [ ] 3.3 实现忠实度门控逻辑：
    - 忠实度通过 + 高信心 → 正常发出 SCORE_SUBMITTED 事件
    - 忠实度不通过 或 整体低信心 → 不发出 SCORE_SUBMITTED，标记评分为"待验证"
  - [ ] 3.4 修改 MCP 工具 `score_answer` 返回值：追加 faithfulness 相关字段

- [ ] **Task 4: 低信心评分精通度保护** (AC: #4)
  - [ ] 4.1 在 autoscore.py 的 evaluate 流程末尾，根据忠实度检查结果决定是否发出 SCORE_SUBMITTED
  - [ ] 4.2 不通过时记录评分到 exam_service 的 score_history（标注 `verified: false`）
  - [ ] 4.3 确保下次考察该节点时，exam_service 优先选择上次评分"待验证"的节点

- [ ] **Task 5: 结构化日志** (AC: #5)
  - [ ] 5.1 定义 `SCORING_FAITHFULNESS_LOG_SCHEMA` 日志 schema
  - [ ] 5.2 在 ScoringFaithfulnessChecker 完成后发出 structlog 事件
  - [ ] 5.3 集成到 `logging_middleware.py` 的 QA_LOG_SCHEMAS 字典
  - [ ] 5.4 在 `health_monitor.py` 的 `_check_faithfulness_score` 中纳入评分忠实度数据

- [ ] **Task 6: 单元测试** (AC: #1-#5)
  - [ ] 6.1 测试：证据全部 GROUNDED → 证据溯源分数 = 1.0
  - [ ] 6.2 测试：2/4 证据 UNGROUNDED → 证据溯源分数 = 0.5 → 忠实度不通过
  - [ ] 6.3 测试：评分 justification 与证据不一致 → 评分一致性分数低
  - [ ] 6.4 测试：忠实度不通过 → SCORE_SUBMITTED 事件不发出 → 精通度不变
  - [ ] 6.5 测试：忠实度通过 + 高信心 → SCORE_SUBMITTED 正常发出
  - [ ] 6.6 测试：整体低信心（2+ 维度 max-min > 1）→ 评分降级
  - [ ] 6.7 测试：结构化日志包含所有必要字段

## Dev Notes

### 架构定位

本 Story 是 FR-QA-01 在 Epic 6（检验白板）场景中的深化实现。Story 1.11 建立了 RAG 回答场景的基础忠实度检查框架（RAGAS claim-level NLI），本 Story 将该框架适配到 AutoSCORE 评分场景，确保：

1. **证据不幻觉**：Stage 1 提取的证据确实来自学生原文，而非 LLM 凭空编造
2. **评分有据可查**：Stage 2 各维度打分与证据一致，不存在"证据说 A 但打分说 B"的矛盾
3. **精通度保护**：不可靠的评分不会污染精通度数据（BKT/FSRS 不接收不可信的信号）

### 依赖关系

- **依赖 Story 1.11**：LLM 忠实度检查基础框架（RAGAS claim-level NLI 方法论、FaithfulnessResult 数据结构、降级策略）。本 Story 复用其核心思想但针对评分场景重新设计检查维度
- **依赖 Story 6.4**：AutoSCORE 两阶段实现（autoscore.py、stage1_evidence.md、stage2_rubric.md）。本 Story 在 AutoSCORE 流程末尾追加忠实度校验层
- **依赖 Story 5.7**：EventBus 三系统联通。本 Story 通过控制 SCORE_SUBMITTED 事件的发出来实现精通度保护
- **被 Story 6.10 关联**：出题难度匹配评估（评分质量影响难度匹配准确性）

### 与 Story 1.11（RAG 忠实度）的区别

| 维度 | Story 1.11（RAG 场景） | Story 6.9（评分场景） |
|------|----------------------|---------------------|
| 检查对象 | LLM 回答 vs 检索上下文 | AutoSCORE 证据/评分 vs 学生原文 |
| 检查目标 | AI 回答是否基于检索到的资料 | AI 评分是否基于学生实际表达 |
| 证据来源 | 检索 context（LanceDB/Graphiti） | 学生对话原文（conversation_segment） |
| 降级策略 | 告知用户"信息可能不完整" | 不更新精通度，等待下次考察 |
| 阈值 | Faithfulness >= 0.85 | 同样 >= 0.85 |

### 现有代码参考

- **AutoSCORE 服务**：`backend/app/services/autoscore.py` — AutoScorer 类实现两阶段评分，evaluate() 方法是忠实度检查的集成点
- **RAG 忠实度检查**：`src/agentic_rag/faithfulness_check.py` — RAGAS claim-level NLI 实现，可参考其 `extract_claims()` 和 `verify_claims_nli()` 的设计模式
- **评分模型**：`backend/app/models/exam_models.py` — AutoScoreResult、RubricDimension，需追加忠实度字段
- **事件处理**：`backend/app/services/event_handlers.py` — handle_score_submitted() 是 SCORE_SUBMITTED 事件的处理入口，忠实度门控在事件发出前执行
- **忠实度配置**：`backend/app/config.py` — FAITHFULNESS_ENABLED、FAITHFULNESS_THRESHOLD 等配置项，评分忠实度可复用相同阈值
- **日志模式**：`backend/app/middleware/logging_middleware.py` — FAITHFULNESS_CHECK_LOG_SCHEMA 定义了现有日志格式
- **健康监控**：`backend/app/services/health_monitor.py` — `_check_faithfulness_score()` 聚合忠实度数据
- **审计层**：`backend/app/audit/guardian.py` — AuditGuardian 监控管道完整性，评分忠实度门控是其上游保障

### AutoSCORE 两阶段忠实度检查设计

```
AutoSCORE evaluate() 完成后：

  Stage 1 证据 ──→ [溯源验证] ──→ 每条证据 GROUNDED/UNGROUNDED
       ↓                              ↓
  学生原文 ─────┘                 证据溯源分数 = GROUNDED / total

  Stage 2 打分 ──→ [一致性验证] ──→ 每维度 justification vs 证据
       ↓                              ↓
  Stage 1 证据 ──┘                评分一致性分数

  综合 Faithfulness = (溯源分数 + 一致性分数) / 2
       ↓
  >= 0.85 → SCORE_SUBMITTED → BKT/FSRS 更新 → 颜色变化
  <  0.85 → 不发事件 → 精通度不变 → 标记"待验证"
```

### 性能考量

- 忠实度检查需要额外 1-2 次 LLM 调用（溯源 + 一致性），但评分本身已经有 1+3=4 次调用，因此总调用数为 6 次
- 可通过配置项控制是否启用评分忠实度检查（高成本场景可关闭）
- 忠实度检查应异步执行，不阻塞评分结果返回给 Agent（先返回评分，后决定是否更新精通度）

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story6.9] — AC 原文
- [Source: _bmad-output/planning-artifacts/epics.md#Story1.11] — 忠实度基础框架
- [Source: _bmad-output/planning-artifacts/architecture.md#质量保证] — FR-QA-01 Faithfulness >= 0.85
- [Source: _bmad-output/planning-artifacts/architecture.md#算法管道完整性] — AutoSCORE → BKT/FSRS → 展示 管道不可断裂
- [Source: _bmad-output/planning-artifacts/architecture.md#评分完成流] — SCORE_SUBMITTED → mastery_engine 事件流
- [Source: _bmad-output/implementation-artifacts/6-4-autoscore-stealth-grading.md] — AutoSCORE 两阶段设计
- [Source: _bmad-output/implementation-artifacts/7-1-llm-faithfulness-prompt-injection.md] — RAGAS claim-level NLI 基础框架
- [Source: RAGAS EACL 2024] — Faithfulness claim-level NLI 评估框架
- [Source: ICLR 2025 Oral "Trust or Escalate"] — 自一致性采样与低信心检测

## Dev Agent Record

### Agent Model Used

(待开发时填写)

### Debug Log References

(待开发时填写)

### Completion Notes List

(待开发时填写)

### File List

- `backend/app/services/scoring_faithfulness.py` — 新建：ScoringFaithfulnessChecker
- `backend/app/prompts/scoring/faithfulness_evidence_grounding.md` — 新建：证据溯源验证 Prompt
- `backend/app/prompts/scoring/faithfulness_score_consistency.md` — 新建：评分-证据一致性 Prompt
- `backend/app/services/autoscore.py` — 修改：集成忠实度门控
- `backend/app/models/exam_models.py` — 修改：AutoScoreResult 追加忠实度字段
- `backend/app/mcp/server.py` — 修改：score_answer 返回值追加忠实度字段
- `backend/app/middleware/logging_middleware.py` — 修改：追加 SCORING_FAITHFULNESS_LOG_SCHEMA
- `backend/app/services/health_monitor.py` — 修改：纳入评分忠实度数据
