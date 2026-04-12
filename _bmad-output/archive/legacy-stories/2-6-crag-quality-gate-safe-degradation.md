# Story 2.6: Phase 1 — CRAG 质量门控与安全降级

Status: ready-for-dev

## Story

As a 用户,
I want 搜索质量不好时系统自动改写查询重搜，而不是用错误内容回答，
so that AI 不会因为搜索质量差而产生幻觉。

## Acceptance Criteria

1. **AC-1: CRAG 二元评分质量门控**
   - **Given** 精排后的搜索结果（Story 2.5 完成 bge-reranker-v2-m3 精排，reranker 分数域 0-1）
   - **When** check_quality 节点执行质量评估
   - **Then** 使用 LLM 二元评分（"yes"=相关 / "no"=不相关）替代当前的数值阈值方案
   - **And** 二元评分 prompt 发送 query + top-k 文档内容给 LLM，LLM 判断文档是否与查询相关
   - **And** 二元评分结果映射为 quality_grade："yes" → "high"/"medium"，"no" → "low"
   - **And** 评分通过 LiteLLM SDK 调用（不锁定厂商），model 从 runtime config 读取
   - **And** 当 LLM 不可用时，降级为当前的数值阈值方案（reranker 分数 top-3 均值）

2. **AC-2: 查询 LLM 改写（替代 f-string 占位）**
   - **Given** CRAG 评分判定为 "low"（不相关）
   - **When** rewrite_query 节点执行
   - **Then** 通过 LiteLLM SDK 调用 LLM 进行语义改写（非 `f"请详细解释:{query}"` 占位）
   - **And** 第 1 次改写策略：添加澄清性上下文 + 领域关键词 + 明确意图
   - **And** 第 2 次改写策略：完全不同角度重述 + 子问题分解 + 同义词替换
   - **And** 改写有 3 秒超时保护（`asyncio.wait_for`），超时降级为关键词拼接策略
   - **And** LLM 不可用时降级为规则改写（jieba 分词提取关键词 + 同义词扩展）

3. **AC-3: 最多 2 次重试循环**
   - **Given** CRAG 判定 "low" 且 rewrite_count < 2
   - **When** 改写后的查询重新进入检索管道
   - **Then** 完整重走：6 路并行搜索 → RRF 融合 → reranker 精排 → CRAG 评分
   - **And** rewrite_count 递增（0 → 1 → 2）
   - **And** rewrite_count >= 2 时强制结束循环（不再改写），进入安全降级
   - **And** 每次重试的查询和评分结果记录到日志（可追踪）
   - **And** 整个重试循环总延迟 < 10 秒（含 LLM 调用）

4. **AC-4: 安全降级——"信息不足"而非幻觉**
   - **Given** 2 次重试后仍然全部 "low"（不相关）
   - **When** route_after_quality_check 到达 END
   - **Then** state 中标记 `safe_degradation: true` + `degradation_reason: "retrieval_quality_insufficient"`
   - **And** 上层消费方（Agent 对话）根据此标记告知用户"当前笔记中未找到高度相关的内容"，不使用低质量结果生成回答
   - **And** 降级时仍返回已有结果（附带 quality_grade 标记），由上层决定是否使用
   - **And** 降级事件记录结构化日志（query, rewrite_count, quality_grades[], degradation_reason）

5. **AC-5: 智能路由 L1——查询意图选择检索策略**
   - **Given** 用户输入查询
   - **When** 查询进入检索管道入口（fan_out_retrieval 之前）
   - **Then** L1 路由根据查询意图分类选择检索策略：
     - 知识点查询 → 优先 LanceDB Dense + Sparse
     - 学习历史查询 → 优先 Graphiti
     - 文件定位查询 → 优先 Vault Notes + CLI
     - 综合查询 → 全部 6 路
   - **And** L1 路由结果记录到 state 中（`query_intent`, `routing_strategy`）
   - **And** 路由不阻塞——即使路由失败也 fallback 到全部 6 路
   - **And** L1 路由延迟 < 200ms（轻量 LLM 调用或规则分类）

6. **AC-6: 迭代 Retrieve-Verify 循环可追踪**
   - **Given** 检索管道执行过程中可能发生 0-2 次重试
   - **When** 每次重试发生
   - **Then** 结构化日志记录：iteration_number, original_query, rewritten_query, quality_grade, reranker_top3_scores, latency_ms
   - **And** state 中保留完整循环历史：`quality_history: [{iteration: 0, grade: "low", scores: [...]}, ...]`
   - **And** 最终结果附带 `total_iterations` 和 `total_retrieval_latency_ms` 元数据

## Tasks / Subtasks

- [ ] **Task 1: CRAG 二元评分实现——替换数值阈值** (AC: #1)
  - [ ] 1.1 在 `src/agentic_rag/nodes.py` 的 `check_quality` 函数中，新增 LLM 二元评分逻辑：构建 prompt 发送 query + top-k 文档 content 给 LLM，要求回答 "yes"（相关）或 "no"（不相关）
  - [ ] 1.2 使用 LiteLLM SDK (`litellm.acompletion()`) 调用 LLM，model 从 runtime config `quality_check_model` 字段读取（默认 `gemini/gemini-2.0-flash`）
  - [ ] 1.3 解析 LLM 响应：提取 "yes"/"no" 答案，容错处理（LLM 返回非标准格式时 fallback 为 "no"）
  - [ ] 1.4 二元评分到 quality_grade 映射：top-k 中任意一条被判 "yes" → `quality_grade = "medium"`（部分相关），全部 "yes" → `"high"`，全部 "no" → `"low"`
  - [ ] 1.5 LLM 不可用时的降级：catch Exception 后 fallback 到现有数值阈值方案（reranker top-3 均值 vs threshold）
  - [ ] 1.6 添加 `binary_grading_used: bool` 到返回 state，标记实际使用了哪种评分方式

- [ ] **Task 2: 查询 LLM 改写——替换 f-string 占位** (AC: #2)
  - [ ] 2.1 重写 `src/agentic_rag/state_graph.py` 的 `rewrite_query` 函数：替换 `f"请详细解释: {original_query}"` 为 LiteLLM 调用
  - [ ] 2.2 改写 prompt 设计：
    - 第 1 次（rewrite_count=0）：`"你是搜索优化专家。请保持核心意图，添加澄清上下文和领域关键词。只输出改写后的查询。\n原始查询：{query}"`
    - 第 2 次（rewrite_count=1）：`"请从完全不同的角度重述此查询，或将其分解为更具体的子问题。只输出改写后的查询。\n原始查询：{query}"`
  - [ ] 2.3 使用 `asyncio.wait_for(litellm.acompletion(...), timeout=3.0)` 实现 3 秒超时
  - [ ] 2.4 超时/异常降级策略：使用关键词提取拼接（如有 jieba 则用 jieba 分词取 top-5 关键词，否则用原始查询 + "关键概念 定义 解释"）
  - [ ] 2.5 LLM model 从 runtime config `rewrite_model` 字段读取（默认与 quality_check_model 相同）
  - [ ] 2.6 记录改写前后查询到 logger.info，便于后续分析改写质量

- [ ] **Task 3: 重试循环加固与安全降级** (AC: #3, #4)
  - [ ] 3.1 在 `route_after_quality_check` 中增加安全降级标记：当 `rewrite_count >= max_rewrite` 且 `quality_grade == "low"` 时，在 state 中设置 `safe_degradation: True` 和 `degradation_reason: "retrieval_quality_insufficient"`
  - [ ] 3.2 更新 `check_quality` 返回值：追加 `quality_history` 列表，记录每次迭代的 {iteration, grade, top3_scores, query_used}
  - [ ] 3.3 在 `rewrite_query` 返回值中保留 `original_query`（首次改写时记录，后续不覆盖）
  - [ ] 3.4 修改 `route_after_quality_check` 的 "low" + max_rewrite 分支：不只是 `return END`，需先更新 state 中的降级标记
  - [ ] 3.5 注意：LangGraph 条件边函数只返回路由决策，state 更新需在 `check_quality` 节点内完成。将降级判断逻辑移到 `check_quality` 末尾——当 `rewrite_count >= max_rewrite - 1` 且当前 grade 为 "low" 时提前设置 safe_degradation

- [ ] **Task 4: 智能路由 L1 实现** (AC: #5)
  - [ ] 4.1 新增 `classify_query_intent` 函数（放在 `src/agentic_rag/routing/` 或 `nodes.py` 中）：输入 query，输出 intent（knowledge_point / learning_history / file_locate / comprehensive）
  - [ ] 4.2 实现策略：优先规则分类（关键词匹配：包含"笔记/文件/文档"→file_locate，包含"之前/上次/复习"→learning_history），规则未命中则 fallback 全路
  - [ ] 4.3 在 `fan_out_retrieval` 中根据 `query_intent` 调整 Send 列表：
    - knowledge_point: Send 全部 6 路（但 Graphiti 和 Vault 权重降低）
    - learning_history: Send Graphiti + LanceDB（跳过 textbook/cross_canvas）
    - file_locate: Send Vault + CLI + LanceDB（跳过 Graphiti/multimodal）
    - comprehensive: Send 全部 6 路（默认）
  - [ ] 4.4 将 `query_intent` 和 `routing_strategy` 写入 state
  - [ ] 4.5 路由失败（exception）时 fallback 到全部 6 路，记录 warning 日志

- [ ] **Task 5: 循环可追踪性——结构化日志与 state 历史** (AC: #6)
  - [ ] 5.1 在 `check_quality` 返回值中追加 `quality_history` 字段：`[{iteration: int, grade: str, top3_scores: list, query: str, binary_grading: bool}]`
  - [ ] 5.2 在 `rewrite_query` 中添加 logger.info 记录：`[CRAG-RETRY] iteration={count}, original='{orig}', rewritten='{new}'`
  - [ ] 5.3 在 `check_quality` 中添加 logger.info 记录：`[CRAG-GRADE] iteration={count}, grade={grade}, top3_scores={scores}, binary={used_binary}`
  - [ ] 5.4 最终结果（无论是否降级）附带元数据：`total_iterations`, `total_retrieval_latency_ms`, `safe_degradation`, `quality_history`
  - [ ] 5.5 添加 `rewrite_count` 和 `quality_grade` 到 `CanvasRAGState` 的文档注释中（已有字段，只补注释说明用途）

- [ ] **Task 6: State 字段扩展** (AC: #1-#6)
  - [ ] 6.1 在 `src/agentic_rag/state.py` 的 `CanvasRAGState` 中增加字段（TypedDict 扩展）：
    - `safe_degradation: bool` — 是否触发安全降级
    - `degradation_reason: str` — 降级原因
    - `quality_history: list` — 质量评分历史
    - `query_intent: str` — L1 路由识别的查询意图
    - `routing_strategy: str` — 选择的路由策略
    - `original_query: str` — 原始查询（改写前保留）
    - `binary_grading_used: bool` — 是否使用了 LLM 二元评分
  - [ ] 6.2 确保新字段都有合理默认值（safe_degradation=False, quality_history=[], 等）
  - [ ] 6.3 `ruff check` 验证新字段不破坏现有类型检查

- [ ] **Task 7: 端到端验证** (AC: #1-#6)
  - [ ] 7.1 准备 5 个测试查询（含中英文、含应该触发降级的模糊查询），逐个执行管道，验证：
    - CRAG 二元评分被调用（检查日志 `[CRAG-GRADE]`）
    - 改写后的查询不是 `f"请详细解释:{query}"`（检查日志 `[CRAG-RETRY]`）
    - 重试最多 2 次后停止（rewrite_count 不超过 2）
    - 全部 low 时 safe_degradation=True
    - L1 路由正确分类（至少 1 个非 comprehensive）
    - quality_history 包含所有迭代记录
  - [ ] 7.2 验证 LLM 不可用场景：断开 LLM 连接后执行查询，确认降级为数值阈值+关键词拼接
  - [ ] 7.3 `ruff check src/agentic_rag/` 全量 lint 通过
  - [ ] 7.4 `ruff format --check src/agentic_rag/` 格式检查通过
  - [ ] 7.5 确认无 mock 数据、无 TODO 空函数、无假实现（DD-03）

## Dev Notes

### Brownfield 上下文——已有代码资产

这是 **Brownfield 项目**，CRAG 质量循环框架已存在但使用占位实现。以下是各文件的当前状态和升级方案：

#### 关键文件清单

| 文件 | 当前状态 | 本 Story 修改内容 |
|------|---------|-----------------|
| `src/agentic_rag/nodes.py` L703-754 | `check_quality` 使用数值阈值（top-3 均值 vs 0.7），Story 2.2 已修复分数域匹配 | **替换为 LLM 二元评分**（保留数值阈值作为降级） |
| `src/agentic_rag/state_graph.py` L146-188 | `rewrite_query` = `f"请详细解释: {original_query}"` (CRITICAL C4) | **替换为 LiteLLM 调用**（Story 2.2 如已修复则进一步升级） |
| `src/agentic_rag/state_graph.py` L104-139 | `route_after_quality_check` 有三路路由逻辑（low/medium-high/max_rewrite） | **增加安全降级标记逻辑** |
| `src/agentic_rag/state.py` | `CanvasRAGState` TypedDict 已有 quality_grade / rewrite_count | **扩展** safe_degradation / quality_history / query_intent 等字段 |
| `src/agentic_rag/quality_nodes/rewrite_query.py` | 独立的 rewrite 节点实现，使用 OpenAI SDK（硬编码 gpt-3.5-turbo） | **参考但替换为 LiteLLM**（state_graph.py 中的 rewrite_query 是实际使用的，此文件为备用） |
| `src/agentic_rag/quality_nodes/grade_documents.py` | 使用 QualityChecker 4 维评分（独立实现） | **参考**，但 nodes.py 中的 check_quality 是实际被图调用的 |
| `src/agentic_rag/quality/query_rewriter.py` | QueryRewriter 类，使用 OpenAI SDK，有 fallback | **参考改写 prompt 设计**，但替换为 LiteLLM |
| `src/agentic_rag/routing/quality_router.py` | `route_after_quality_check` 独立实现 | **参考**，state_graph.py 中的版本是实际被图使用的 |

#### 双重实现问题说明

当前代码存在两套平行实现：
- **实际被 LangGraph 图调用的**：`state_graph.py` 中的 `rewrite_query` 和 `route_after_quality_check`
- **独立模块中的实现**：`quality_nodes/rewrite_query.py` 和 `routing/quality_router.py`

本 Story 修改 **实际被调用的版本**（`state_graph.py` 和 `nodes.py`），如果后续需要统一可在 refactor Story 中处理。

#### CRAG 二元评分设计（来自后端 PRD）

后端 PRD 选型确认：**CRAG 二元评分（yes/no）优于数值阈值**，理由：
- CRAG 论文 arXiv:2401.15884 证实提升 9.6-20% 准确率
- 二元判断比数值阈值更可靠（不受分数域漂移影响）
- 最多 2 次重试 + 安全降级是 CRAG 论文标准流程

#### 智能路由 L1 设计（来自架构文档）

架构文档确认四层路由 + 六路物理通道：
- L0: 意图分类（本 Story 实现为 L1，MVP 阶段合并 L0+L1）
- L1: 场景路由——根据意图选择检索策略
- L2: Retrieve-Verify 循环——CRAG 质量门控
- L3: A-RAG 回源验证（Agent 侧执行，不在本 Story 范围）

本 Story MVP 实现：**规则分类优先，LLM 分类为远期增强**。规则分类延迟极低（<1ms），满足 L1 < 200ms 要求。

### 依赖关系

- **前置 Story 2.5**（精排与融合升级）：reranker 返回真实分数（0-1），CRAG 评分基于精排后结果
- **前置 Story 2.2**（搜索通道修复）：6 路搜索通道工作，reranker 非空壳，查询改写初步接入 LLM
- **后续 Story 2.10**（上下文压缩与掌握度注入）：使用本 Story 的 quality_grade 和 safe_degradation 决定是否执行压缩
- **后续 Story 2.11**（参数可配置化）：CRAG 阈值、max_rewrite、LLM model 等参数配置化

### 技术决策

1. **二元评分 vs 数值阈值**：优先二元评分（CRAG 论文验证更可靠），数值阈值保留为降级方案。不做多级评分（保持 yes/no 简洁性，CRAG 原论文推荐）。
2. **LLM 调用层**：使用 LiteLLM SDK（与主 PRD 决策一致，不锁定厂商），不使用 quality_nodes/ 中硬编码的 OpenAI SDK。
3. **L1 路由**：MVP 使用规则分类（关键词匹配），不引入额外 LLM 调用。理由：L1 需要极低延迟，规则分类满足需求。
4. **安全降级**：降级信号放在 state 中由上层消费，本 Story 不修改前端/Agent 的降级展示逻辑（那是 Epic 3 的范围）。
5. **state_graph.py vs quality_nodes/**：修改实际被图调用的版本。双重实现的统一是 refactor 范围，不在本 Story 做。

### 关键代码位置

| 组件 | 文件路径 |
|------|---------|
| CRAG 质量检查（实际调用） | `src/agentic_rag/nodes.py` L703-754（`check_quality`） |
| 查询改写（实际调用） | `src/agentic_rag/state_graph.py` L146-188（`rewrite_query`） |
| 质量路由（实际调用） | `src/agentic_rag/state_graph.py` L104-139（`route_after_quality_check`） |
| State 定义 | `src/agentic_rag/state.py`（`CanvasRAGState`） |
| 备用改写实现（参考） | `src/agentic_rag/quality_nodes/rewrite_query.py` |
| 备用评分实现（参考） | `src/agentic_rag/quality_nodes/grade_documents.py` |
| 备用路由实现（参考） | `src/agentic_rag/routing/quality_router.py` |
| 改写 prompt 设计（参考） | `src/agentic_rag/quality/query_rewriter.py` |
| 图构建 | `src/agentic_rag/state_graph.py` L205-371（`build_canvas_agentic_rag_graph`） |
| Config | `src/agentic_rag/config.py` |

### 不做的事项（防蔓延 DD-10）

- 不实现 L3 A-RAG 回源验证（Agent 侧执行，不在后端管道 Story 范围）
- 不实现上下文压缩（Story 2.10 的范围）
- 不实现掌握度注入 prompt（Story 2.10 的范围）
- 不修改前端降级展示逻辑（Epic 3 的范围，本 Story 只在 state 中标记 safe_degradation）
- 不统一 quality_nodes/ 和 state_graph.py 的双重实现（refactor 范围）
- 不实现 Multi-Query Decomposition 高级改写（Story 2.10 / Phase 2 范围，本 Story 只做单查询改写）
- 不修改 LangGraph 图结构（只修改节点实现和 state 字段）
- 不修改融合策略（Story 2.5 已完成分层 RRF）
- 不修改 reranker（Story 2.5 已完成升级）
- 不实现 CRAG 参数可配置化（Story 2.11 的范围，本 Story 用默认值）

### FR 覆盖映射

| FR ID | AC 映射 | 说明 |
|-------|---------|------|
| FR-RET-04 | AC-3, AC-5 | 智能路由 + 迭代 Retrieve-Verify 循环（最多 2 次） |
| FR-RET-11 | AC-1, AC-2, AC-4 | 质量不达标自动改写重搜 + 安全降级 |
| FR-QA-P-01 | AC-1 | CRAG 二元评分质量门控 |
| FR-QA-P-02 | AC-2, AC-3 | 查询自动改写重搜（最多 2 次） |
| FR-QA-P-03 | AC-4 | 安全降级 |

### Project Structure Notes

- 本 Story 修改范围限于 `src/agentic_rag/` 目录
- `state.py` 字段扩展需确保向后兼容（新字段都有默认值）
- `quality_nodes/` 和 `routing/` 目录中的独立实现不修改，但可参考其设计
- LiteLLM SDK 依赖需确认在 `requirements.txt` 或 `pyproject.toml` 中已包含

### References

- [Source: _bmad-output/planning-artifacts/prd-backend-retrieval-pipeline.md#能力域 3：质量保障] — FR-QA-P-01/02/03 定义
- [Source: _bmad-output/planning-artifacts/prd-backend-retrieval-pipeline.md#关键技术选型] — CRAG 二元评分选型依据
- [Source: _bmad-output/planning-artifacts/prd-backend-retrieval-pipeline.md#Phase 1] — 任务 1.7 CRAG 二元评分 + 三路路由
- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.6] — Story 需求和 AC
- [Source: _bmad-output/planning-artifacts/architecture.md#Core Architectural Decisions] — 四层路由 + Agentic RAG L1+L2
- [Source: _bmad-output/planning-artifacts/prd.md#Layer 2] — Agentic RAG Level 1+2 学术依据（CRAG arXiv:2401.15884 + A-RAG arXiv:2602.03442）
- [Source: src/agentic_rag/nodes.py] — check_quality 当前实现（数值阈值）
- [Source: src/agentic_rag/state_graph.py] — rewrite_query 占位实现 + route_after_quality_check
- [Source: src/agentic_rag/state.py] — CanvasRAGState TypedDict
- [Source: src/agentic_rag/quality/query_rewriter.py] — 改写 prompt 设计参考
- [Source: src/agentic_rag/quality_nodes/grade_documents.py] — 评分实现参考

## Dev Agent Record

### Agent Model Used

(to be filled by dev agent)

### Debug Log References

### Completion Notes List

### File List
