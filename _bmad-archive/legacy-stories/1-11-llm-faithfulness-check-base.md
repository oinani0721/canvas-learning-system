# Story 1.11: LLM 忠实度检查基础框架

Status: ready-for-dev

## Story

As a 系统,
I want 建立 LLM 输出忠实度检查的基础管道，
So that 后续各 Epic 的 AI 回答能被自动校验可靠性。

## Acceptance Criteria

1. **Given** LLM 生成回答且有检索上下文作为参考
   **When** 忠实度检查管道执行
   **Then** 通过 RAGAS 框架计算 Faithfulness 分数（claim-level NLI：提取原子声明 -> 逐条 NLI 验证 -> supported_claims / total_claims）

2. **Given** Faithfulness 分数计算完成
   **When** 分数低于 0.85
   **Then** 该回答被标记为低信心（`faithfulness_degraded = True`），附带正面语言的降级提示

3. **Given** 忠实度检查执行
   **When** 检查完成（成功或失败）
   **Then** 检查结果记录在结构化日志中（score、total_claims、supported_claims、degraded、latency_ms），不阻塞用户体验

4. **Given** 系统运行中
   **When** 管理员或开发者设置 `FAITHFULNESS_ENABLED=false`
   **Then** 忠实度检查管道被跳过（返回 score=None, degraded=False），节省 token 消耗

## Tasks / Subtasks

- [ ] Task 1: 验证现有 RAGAS Faithfulness 检查实现完整性 (AC: #1)
  - [ ] 1.1 审查 `src/agentic_rag/faithfulness_check.py` 的两阶段 claim-level NLI 实现是否完整可用（extract_claims -> verify_claims_nli -> calculate_faithfulness）
  - [ ] 1.2 验证 LiteLLM 调用路径正确（model 配置、API key 传递、temperature=0.0 确定性输出）
  - [ ] 1.3 验证 JSON 解析鲁棒性（`_parse_json_response` 对 markdown fence 的处理）
  - [ ] 1.4 验证空输入边界条件处理（无 answer、无 context、无 claims 场景）

- [ ] Task 2: 验证阈值门控与安全降级 (AC: #2)
  - [ ] 2.1 确认双阈值降级策略生效：score >= 0.85 通过、0.5 <= score < 0.85 低信心警告、score < 0.5 完全降级
  - [ ] 2.2 确认降级消息使用正面语言（"信息可能不完整"而非"AI 产生了幻觉"）
  - [ ] 2.3 验证 `apply_degradation()` 函数正确设置 `degraded` 和 `degradation_reason`

- [ ] Task 3: 验证 LangGraph 管道集成 (AC: #1, #3)
  - [ ] 3.1 确认 `faithfulness_check` 节点已注册在 `state_graph.py` 的 StateGraph 中
  - [ ] 3.2 确认管道路由正确：`check_quality -> compress_context -> faithfulness_check -> END`
  - [ ] 3.3 确认 `CanvasRAGState` 包含 faithfulness_score、faithfulness_details、faithfulness_degraded 字段
  - [ ] 3.4 确认 `route_after_quality_check` 将可接受质量路由到 faithfulness_check

- [ ] Task 4: 验证结构化日志与可观测性 (AC: #3)
  - [ ] 4.1 确认 `_log_faithfulness_result()` 通过 structlog 发射 `faithfulness_check_completed` 事件
  - [ ] 4.2 确认 `logging_middleware.py` 中 `FAITHFULNESS_CHECK_LOG_SCHEMA` 定义完整
  - [ ] 4.3 确认 `canvas_events.py` 中 `FAITHFULNESS_CHECKED` 事件枚举已注册
  - [ ] 4.4 确认 `health_monitor.py` 的 `_check_faithfulness_score()` 能正确聚合忠实度健康指标

- [ ] Task 5: 验证开关配置 (AC: #4)
  - [ ] 5.1 确认 `config.py` 中 `FAITHFULNESS_ENABLED` 设置项存在且默认值正确
  - [ ] 5.2 确认 `faithfulness_check()` 节点函数在 `FAITHFULNESS_ENABLED=false` 时正确跳过
  - [ ] 5.3 确认环境变量 `FAITHFULNESS_ENABLED` 可控制开关
  - [ ] 5.4 确认配置项 `FAITHFULNESS_THRESHOLD`、`FAITHFULNESS_THRESHOLD_LOW`、`FAITHFULNESS_MODEL` 可自定义

- [ ] Task 6: 运行并验证测试套件 (AC: #1-#4)
  - [ ] 6.1 运行单元测试 `backend/tests/unit/test_faithfulness_check.py`（calculate_faithfulness、apply_degradation、parse_json、disabled/empty/no-context 场景）
  - [ ] 6.2 运行集成测试 `backend/tests/integration/test_qa_pipeline.py`（E2E 高忠实度通过 + 低忠实度降级）
  - [ ] 6.3 确认所有测试通过且无测试数据泄漏
  - [ ] 6.4 如有失败测试，修复并确保覆盖全部 4 条 AC

- [ ] Task 7: 补充缺失测试用例（如需要）(AC: #1-#4)
  - [ ] 7.1 补充 LiteLLM 不可用时的降级测试（`LITELLM_AVAILABLE=False`）
  - [ ] 7.2 补充 LLM 调用异常时的容错测试（网络超时、JSON 解析失败）
  - [ ] 7.3 补充开关关闭时的跳过测试
  - [ ] 7.4 补充 claim 提取返回空列表时 score=1.0 的边界测试

## Dev Notes

### 现有代码资产（已实现 ~95%，主要工作是验证+激活+补测试）

本 Story 的核心代码已由旧 Story 7.1 实现完毕。Story 1.11 是 Epic 重组后 Story 7.1 忠实度检查部分的重新编号。**主要工作是验证现有实现的完整性和正确性，确保管道端到端可用。**

| 文件 | 路径 | 状态 | 说明 |
|------|------|------|------|
| `faithfulness_check.py` | `src/agentic_rag/faithfulness_check.py` | **已实现** | RAGAS 两阶段 claim-level NLI（586行）。包含 extract_claims、verify_claims_nli、calculate_faithfulness、apply_degradation、faithfulness_check LangGraph 节点 |
| `state.py` | `src/agentic_rag/state.py` | **已实现** | CanvasRAGState 已包含 faithfulness_score、faithfulness_details、faithfulness_degraded 字段 |
| `state_graph.py` | `src/agentic_rag/state_graph.py` | **已实现** | faithfulness_check 节点已注册，路由 check_quality -> compress_context -> faithfulness_check -> END |
| `canvas_events.py` | `backend/app/models/canvas_events.py` | **已实现** | FAITHFULNESS_CHECKED 事件枚举已注册 |
| `logging_middleware.py` | `backend/app/middleware/logging_middleware.py` | **已实现** | FAITHFULNESS_CHECK_LOG_SCHEMA 已定义 |
| `config.py` | `backend/app/config.py` | **已实现** | FAITHFULNESS_ENABLED、FAITHFULNESS_THRESHOLD(0.85)、FAITHFULNESS_THRESHOLD_LOW(0.5)、FAITHFULNESS_MODEL 设置项已定义 |
| `health_monitor.py` | `backend/app/services/health_monitor.py` | **已实现** | _check_faithfulness_score() 健康指标已实现 |
| `llm_call_logger.py` | `backend/app/middleware/llm_call_logger.py` | **已实现** | TaskType.QA_CHECK 枚举覆盖 faithfulness_check 调用 |
| `test_faithfulness_check.py` | `backend/tests/unit/test_faithfulness_check.py` | **已实现** | 7 个单元测试（score 计算、degradation、JSON 解析、节点函数） |
| `test_qa_pipeline.py` | `backend/tests/integration/test_qa_pipeline.py` | **已实现** | 2 个 E2E 集成测试（高忠实度通过 + 低忠实度降级） |

### 与旧 Story 7.1 的关系

旧 Story 7.1 (`7-1-llm-faithfulness-prompt-injection.md`) 同时覆盖了忠实度检查 + Prompt 注入防护。Epic 重组后拆分为：
- **Story 1.11（本 Story）**：忠实度检查基础框架（FR-QA-01 基础部分）
- Prompt 注入防护部分由其他 Story 覆盖（`backend/app/middleware/prompt_injection_guard.py` 已实现）

### 核心算法（RAGAS EACL 2024 -- Claim-Level NLI）

1. **Claim Extraction（声明提取）**：LLM 从生成回答中提取原子声明（atomic claims）
2. **NLI Verification（自然语言推理）**：对每条 claim，LLM 判断是否被检索 context 支持（SUPPORTED / NOT_SUPPORTED）
3. **Score Calculation**：`Faithfulness = |supported claims| / |total claims|`

在 RAG 管道中的位置：
```
retriever -> reranker -> check_quality -> compress_context -> faithfulness_check -> END
```

### Architecture Compliance

- **LLM 调用层**：通过 LiteLLM SDK 统一调用（architecture.md Cross-Cutting #3），支持 100+ 模型
- **非阻塞**：faithfulness_check 是 LangGraph 管道最后一个节点，检查结果附加到 state 返回，不阻塞用户响应流
- **安全降级**：复用 FR-RET-11 降级逻辑，正面语言提示（"信息可能不完整"）
- **可观测性**：structlog 结构化日志 + EventBus FAITHFULNESS_CHECKED 事件（Tier3 fire-and-forget）
- **配置化**：FAITHFULNESS_ENABLED 开关 + 可自定义阈值/模型

### Key Libraries and Versions

| 库 | 版本 | 用途 |
|----|------|------|
| `litellm` | >= 1.40.0 | 统一 LLM SDK，用于 claim extraction 和 NLI verification 的 LLM 调用 |
| `structlog` | >= 23.0.0 | 结构化日志（faithfulness_check_completed 事件） |
| `langgraph` | >= 0.2.0 | StateGraph 管道集成 |

### File Paths Involved

**核心实现：**
- `src/agentic_rag/faithfulness_check.py` -- 忠实度检查节点（两阶段 NLI + 降级）
- `src/agentic_rag/state.py` -- RAG 状态定义（faithfulness 字段）
- `src/agentic_rag/state_graph.py` -- LangGraph 图构建（节点注册 + 路由）

**支撑设施：**
- `backend/app/config.py` -- 开关和阈值配置
- `backend/app/models/canvas_events.py` -- FAITHFULNESS_CHECKED 事件枚举
- `backend/app/middleware/logging_middleware.py` -- 日志 Schema
- `backend/app/services/health_monitor.py` -- 健康指标聚合
- `backend/app/middleware/llm_call_logger.py` -- TaskType.QA_CHECK 分类

**测试文件：**
- `backend/tests/unit/test_faithfulness_check.py` -- 单元测试
- `backend/tests/integration/test_qa_pipeline.py` -- 集成测试

**依赖配置：**
- `backend/requirements.txt` -- litellm>=1.40.0

### Architecture Note

`faithfulness_check.py` 放置在 `src/agentic_rag/` 根目录（非 `nodes/` 子目录），原因是避免与 `nodes.py` 文件的 Python import 冲突。`nodes/__init__.py` 仅作为命名空间占位符，注释说明 faithfulness_check 由 state_graph.py 直接导入。

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.11 -- AC 原始定义]
- [Source: _bmad-output/planning-artifacts/epics.md#Epic 1 -- FR-QA-01(基础)]
- [Source: _bmad-output/planning-artifacts/architecture.md#Cross-Cutting Concerns #3 -- LLM调用管理 + 幻觉检测 Faithfulness>=0.85]
- [Source: _bmad-output/planning-artifacts/architecture.md#Data Flow -- context_compressor -> faithfulness_check]
- [Source: _bmad-output/planning-artifacts/architecture.md#Project Structure -- agentic_rag/faithfulness_check.py]
- [Source: _bmad-output/implementation-artifacts/7-1-llm-faithfulness-prompt-injection.md -- 旧 Story 7.1 实现记录]
- [Reference: RAGAS (EACL 2024) -- Faithfulness claim-level NLI 评估框架](https://docs.ragas.io/en/latest/concepts/metrics/available_metrics/faithfulness/)
- [Reference: Benchmarking LLM Faithfulness in RAG (arXiv 2505.04847)](https://arxiv.org/html/2505.04847v2)

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
