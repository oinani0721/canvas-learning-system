# A6 Resolution Summary — Deep Research Review 入口

> 本文档是 A6（User 2 的 3 个架构级问题）修复成果的聚合导读。
> ChatGPT Deep Research 请从这里开始，按 Q1/Q2/Q3 顺序审查证据文件，
> 不需要重建上下文。每条引用都附了 commit SHA + 文件 path:line_number。

---

## 1. A6 原始问题（来自 docs/project-status/fr-exploration/A6.md）

User 2 的核心观察：检验白板里其实存在 **两个图谱**：

1. **白板节点联系图谱**：用户在前端白板上画的节点 + 节点间的 edge（用文字解释关系）
2. **概念知识图谱**：从单节点对话里提取的概念 / 疑问 / tips 构成的细粒度知识网络

User 2 由此提出了 3 个问题：

- **Q1（图谱合并）** 这两个关系图谱是否合并为一个？我们真的有成熟方案来构建出这样一个能"读"的关系图谱吗？特别是前端白板上节点间的联系会被增加和修改，这给图谱定义和算法带来什么挑战？
- **Q2（RAG 语义检索是什么）** 项目里的 RAG 是哪一种？是笔记片段精确检索吗？背后的算法是什么？
- **Q3（FSRS 评分历史）** FSRS 怎么融入关系图谱？它在我使用检验白板的时候究竟会带来什么实际影响？这个算法是怎么被调用的？

并附了一个 **验证服务图查询 vs Graphiti 搜索** 的对比表格，结论是：
> 验证服务的图查询 = 🚲 自行车，Graphiti 的搜索 = 🚗 汽车。

---

## 2. 修复成果全景

| 问题 | 状态 | 关键 commit | 一句话总结 |
|---|---|---|---|
| **Q1 图谱合并** | ✅ 已落地（在 `origin/main`） | `a6da4f7`, `9cf6508` | 不合并物理图谱，在查询层加权融合 CANVAS_EDGE (1.0) + RELATES_TO (0.7) |
| **Q2 RAG 语义检索** | ✅ 已落地（在 `origin/main`） | `3b96e49`, `b7feefb`, `08f3499` | Agentic RAG 5 路并行 + LLM 路由 + Faithfulness + CRAG fallback |
| **Q3 FSRS 融入** | ✅ 已落地（在 worktree 分支 `fix-concept-id-identity-unification`） | `d569da0`, `03c8842`, `c154022` | ConceptRef 身份契约统一，让 memory_service 用 UUID 直查 review_service.get_fsrs_state() |

> ⚠️ Q3 的修复在独立分支上（**未 merge 到 main**），但已 push 到 origin。
> 见 Section 5.2 的分支 URL。

---

## 3. Q1 图谱合并：CANVAS_EDGE vs RELATES_TO

### 3.1 解答

**不合并成一个物理图谱**，而是在查询层 **加权融合**：

- `CANVAS_EDGE`（用户在白板上显式画的线）→ 权重 **1.0**（"explicit user intent"）
- `RELATES_TO`（Graphiti 从对话推断的概念关系）→ 权重 **0.7**（"Graphiti-inferred"）
- 同一对邻居节点同时存在两种边时，`MAX(CASE type(r) ...)` 取较大值（即 1.0）

设计逻辑：用户显式画的边总是赢过 LLM 推断的边，但推断的边在缺失显式连接时仍提供有用的语义信号。

### 3.2 关键 commits（已在 origin/main）

| SHA | Title |
|---|---|
| `a6da4f7` | fix(kg-relevance): Phase 1 schema unification + weighted edge formula |
| `9cf6508` | docs(openspec): Phase 7 CONNECTS_TO deprecation schedule + docstring |

### 3.3 关键证据文件（path:line_number）

- **`backend/app/services/question_generator.py:700`** — `_get_kg_relevance(self, node_id, canvas_id) -> tuple[float, Optional[str]]` 函数定义
- **`backend/app/services/question_generator.py:741-753`** — Cypher 查询本体：`MATCH (n:CanvasNode {id: $node_id})-[r:CANVAS_EDGE|RELATES_TO]-(neighbor:CanvasNode) WHERE neighbor.canvasId = $canvas_id WITH neighbor, MAX(CASE type(r) WHEN 'CANVAS_EDGE' THEN 1.0 WHEN 'RELATES_TO' THEN 0.7 END) AS edge_weight RETURN SUM(edge_weight) AS weighted_degree, COUNT(DISTINCT neighbor) AS neighbor_count`
- **`backend/app/services/question_generator.py:763`** — 归一化公式 `min(1.0, float(weighted) / 8.0)`（8 条强连接达满分）
- **`backend/app/models/exam_models.py:241`** — `class NodePriority(BaseModel)`
- **`backend/app/models/exam_models.py:259`** — `kg_relevance_degraded: Optional[str] = None` 字段（empty_graph / neo4j_unavailable / None）
- **`backend/migrations/002_canvasnode_uuid_to_id.cypher`** — schema 迁移脚本（uuid → id），幂等
- **`backend/tests/unit/test_kg_relevance_weighted.py`** — 13 个 unit tests
- **`backend/tests/e2e/test_a11_kg_relevance_e2e.py`** — 7 个 e2e tests（真实 Neo4j 容器，A11 regression suite）
- **`openspec/changes/archive/2026-04-07-fix-fr-kg-04-schema-drift-and-sync-hardening/design.md`** — 决策 D2（为什么权重 1.0 vs 0.7）+ 决策 D3（归一化除数为什么是 8.0）
- **`openspec/changes/archive/2026-04-07-fix-fr-kg-04-schema-drift-and-sync-hardening/deprecation-schedule.md`** — CONNECTS_TO 弃用路线图（Phase 7）

### 3.4 关键决策理由

1. **为什么 1.0 vs 0.7（不是 1.0 vs 1.0 或 1.0 vs 0.5）？**
   - 用户显式画的边代表 "intent"，必须严格大于 LLM 推断
   - 但 RELATES_TO 不能太低，否则 Graphiti 推断的连接对孤立节点没救济
   - 0.7 是经验值，记录在 design.md D2

2. **为什么归一化除数是 8.0？**
   - 直觉：8 条强连接（CANVAS_EDGE × 8 = 8.0）的节点已经是 KG 关键节点，应得满分 1.0
   - 不是从论文里抄的，是实战调出来的（design.md D3 标注 "no academic backing"）

3. **为什么用 `MAX(CASE type(r) ...)` 而不是 `SUM`？**
   - SUM 会让"显式 + 推断"双倍计分（不公平）
   - MAX 让显式胜出，是 [code-review C-1] 的修正路径
   - 见 question_generator.py:731-740 inline comment

### 3.5 已知限制

- `002_canvasnode_uuid_to_id.cypher` 迁移脚本 **未在生产 Neo4j 跑过**（Phase 16 deferred）
- Linter check：`grep -rn "CanvasNode {uuid"` 返回 0 → 残留旧 schema 已清理
- 归一化常数 8.0 没有学术支撑，**A10 ablation study 未完成**

---

## 4. Q2 RAG 语义检索是什么

### 4.1 解答

**不是** 笔记片段的精确检索。是 **Agentic RAG** 架构（基于 LangGraph）：

1. **5 路并行检索**：graphiti / lancedb / multimodal / cross_canvas / vault_notes 同时跑
2. **L1 智能路由**：Gemini Flash LLM 把 query 分类到 4 个 intent（knowledge_point / learning_history / file_locate / comprehensive），决定哪几路上场
3. **三策略 fallback chain**：`hybrid`（默认 LLM → rule） / `llm`（仅 LLM） / `rule`（仅规则）
4. **RRF 融合 + Cross-encoder 重排序**：5 路结果用 Reciprocal Rank Fusion 合并，再用 cross-encoder 精排
5. **Faithfulness check**：LLM 生成答案后做 claim-level NLI 验证，避免幻觉
6. **CRAG one-shot fallback**：Faithfulness 失败时降级到 deep_research 模式

### 4.2 关键 commits（已在 origin/main）

| SHA | Title |
|---|---|
| `3b96e49` | feat(agentic-rag): A9 L1 LLM router — replace rule-based classifier with Gemini Flash |
| `b7feefb` | chore(openspec): archive fix-rag-faithfulness-and-add-crag-quality-loop |
| `08f3499` | feat(agentic-rag): add CRAG one-shot deep_research_fallback (Phase 4) |

### 4.3 关键证据文件

- **`backend/lib/agentic_rag/llm_router.py:140`** — `async def llm_route(query, model, timeout_s, max_tokens) -> LLMRouterResult` LLM 路由主入口（never raises）
- **`backend/lib/agentic_rag/llm_router.py:120-132`** — `_parse_json_response()` markdown 代码栅栏容错（注释明说从 faithfulness_check.py:158 拷过来，避免耦合）
- **`backend/lib/agentic_rag/state_graph.py:66`** — `def classify_query_intent(query: str) -> str` 旧规则分类（保留为 fallback，<1ms 延迟）
- **`backend/lib/agentic_rag/state_graph.py:171`** — `async def _classify_intent_with_strategy(query)` 三策略 fallback chain（hybrid → llm → rule → comprehensive_fallback）
- **`backend/lib/agentic_rag/state_graph.py:232`** — `async def fan_out_retrieval(state)` 5 路并发 fan-out 节点
- **`backend/lib/agentic_rag/state_graph.py:265`** — 调用 `_classify_intent_with_strategy(query)` 拿 intent + strategy_used + metrics
- **`backend/lib/agentic_rag/faithfulness_check.py:380`** — `async def faithfulness_check(state) -> dict` LangGraph 节点
- **`backend/lib/agentic_rag/faithfulness_check.py:442-458`** — vacuous-true fix #1：last_role 不是 assistant 时返回 `score=None` + `not_applicable_no_assistant_answer`
- **`backend/lib/agentic_rag/faithfulness_check.py:460-467`** — vacuous-true fix #2：空 answer 返回 `score=None` + `not_applicable_no_answer`（避免空答案被记成满分）
- **`backend/lib/agentic_rag/deep_research.py`** — CRAG one-shot fallback 实现
- **`backend/lib/agentic_rag/nodes.py`** — RRF 融合 + fusion_report / sharpness_report 观测指标
- **`backend/tests/unit/test_l1_llm_router.py`** — 15 个 unit tests
- **`backend/tests/unit/test_state_graph_l1_routing.py`** — 8 个条件边路由 tests
- **`backend/tests/unit/test_langgraph_async_conditional_edge_smoke.py`** — 2 个 LangGraph 1.x async conditional edge 前置检查
- **`backend/scripts/compare_l1_router_strategies.py`** — benchmark 脚本（10 queries × rule vs LLM，"≥6/10 non-comprehensive" 为通过）
- **`openspec/specs/algo-rag/spec.md`** — 3 个新 contract（Faithfulness / Fusion / CRAG）
- **`openspec/specs/agentic-rag/spec.md`** — L1 路由配置 + 状态契约
- **`openspec/changes/archive/2026-04-07-agentic-rag-l1-llm-router/design.md`** — D1（prompt 设计）/ D2（fallback chain）/ D3（成本分析）
- **`openspec/changes/archive/2026-04-07-fix-rag-faithfulness-and-add-crag-quality-loop/`** — Faithfulness not-applicable 契约 + CRAG fallback proposal/design

### 4.4 关键决策理由

1. **为什么 LLM 路由而不是继续 rule-based？**
   - User feedback A9：rule-based 是 "rigid"，关键词匹配会 miss 语义清晰的 query（例："上周的积分课讲了什么内容" — 没有 'learning_history' 关键词）
   - LLM 能理解语义，但延迟高 / 成本高 → 必须有 fallback
   - 见 commit message of `3b96e49`

2. **为什么用 RRF 融合（而不是 weighted sum）？**
   - RRF 的 rank-based 设计对 score 量纲不敏感（5 路 retriever 的 score 量纲完全不同）
   - 是社区在多路 retrieval 融合时的事实标准

3. **为什么 Cross-encoder 重排序？**
   - bi-encoder（用于初筛）追求速度，精度有限
   - cross-encoder 看 query × doc 全交互，精度高但慢
   - 两段式（粗排 → 精排）是 sentence-transformers 官方推荐的

4. **为什么 Faithfulness 空答案返回 `None` 而不是 `1.0`？**
   - vacuous-true 陷阱：空答案在 NLI 上是"无 claim 可证伪"，传统实现会给 1.0（满分）
   - 这会让 health monitor 误以为系统完美
   - `None` 让 `record_faithfulness_score` 早 return，stats 保持干净
   - 见 faithfulness_check.py:442-467 的两段 vacuous-true fix 注释

5. **为什么 CRAG 是 one-shot（而不是递归）？**
   - 递归 LLM 调用成本爆炸
   - one-shot 提供"质量太差时换条路径"的逃生口，但不会无限重试
   - Phase 4 设计权衡

---

## 5. Q3 FSRS 评分历史如何融入

### 5.1 解答

**不是** 把 FSRS 数据复制进图谱。而是通过 **身份契约统一**（`ConceptRef`）让 memory_service 可以按 UUID 查询 review_service 的 FSRS card_state，把 `fsrs_r_values` 注入到 agentic RAG 的检索结果里。

FSRS 对用户使用检验白板的 **3 个实际影响**：

1. **出题优先级公式**：
   `priority = 0.4 * (1 - p_mastery) + 0.3 * (1 - retrievability) + 0.3 * kg_relevance`
   FSRS 提供其中的 `retrievability`（中间项），让"快忘了"的概念优先被出题
2. **难度分层**：基于 `fsrs_difficulty` 选题型
   - ≥ 80 → 出应用题（hard，深度推理）
   - 60-79 → 出验证题（medium，事实回忆）
   - < 60 → 出基础题（easy，概念辨认）
3. **检索结果重排序**：低 R-value 的概念在 RAG 检索结果里被加权（公式 `final_score = relevance_score * (1.0 + (1.0 - r_value) * 0.5)`，最多 50% 加成）

### 5.2 关键 commits（⚠️ **本次新推到远程的 worktree 分支**）

| SHA | Title |
|---|---|
| `d569da0` | fix(concept-id): unify identity contract across verification/memory/review |
| `03c8842` | fix(concept-id): close residual text-as-uuid leak in fallback_sync_service |
| `c154022` | test(fallback-sync): clear 3 pre-existing test infra debts |

**本分支 GitHub URL**：
`https://github.com/oinani0721/canvas-learning-system/tree/fix-concept-id-identity-unification`

### 5.3 关键证据文件（在 `fix-concept-id-identity-unification` 分支上）

- **`backend/app/models/concept_ref.py:42`** — `@dataclass(frozen=True) class ConceptRef`
- **`backend/app/models/concept_ref.py:72-74`** — 三个字段：`concept_id` (UUID v4 string) / `concept_name` (人类可读) / `canvas_id` (Optional, 预留)
- **`backend/app/models/concept_ref.py:76-86`** — `__post_init__` 三个不变量校验：
  1. `concept_id` 必须是 UUID v4
  2. `concept_name` 非空 string
  3. `concept_name` 不能以 `/` 开头（路径泄漏 guard）
- **`backend/app/utils/identifier_validators.py:28-61`** — `def is_uuid_v4(value: object) -> bool` 严格 UUID v4 校验（regex，比 `uuid.UUID(s, version=4)` 严格 + 快 ~3x）
- **`backend/app/services/verification_service.py`** — 349 lines changed (+279 / -70)：
  - 删除两处 `concept_id = node_id if node_id else concept` 文本回退
  - 重写 `_extract_concepts_from_canvas()` 返回 `List[ConceptRef]`
- **`backend/app/services/memory_service.py:1491`** — `async def _inject_fsrs_r_values(self, results)` 函数定义（修复点）
- **`backend/app/services/memory_service.py:1494-1522`** — docstring 说明 fix 路径（path B）：原实现查 `mastery_engine._concept_cache`（一个**根本不存在**的属性，hasattr always False，整个注入是 silent no-op）；新实现走 `review_service.get_fsrs_state(concept_id)`（真实数据源）
- **`backend/app/services/memory_service.py:1553-1561`** — `is_uuid_v4(concept_id)` guard：legacy 文本 ID 进入 concept_id slot 时打 warning（结构化日志）
- **`backend/app/services/memory_service.py:1564`** — `state = await review_service.get_fsrs_state(concept_id)` 真实查询点
- **`backend/app/services/memory_service.py:1736`** — `await self._inject_fsrs_r_values(merged)` 调用点（注释解释为什么变 async）
- **`backend/app/services/review_service.py`** — 字段拆分：`concept_id` + `concept_name` 显式 + 遗留 `concept` 别名双桶兼容读
- **`backend/app/services/fallback_sync_service.py:380-397`** — `is_uuid_v4(raw_concept_id)` guard 在 `_replay_scoring_entry_to_neo4j()`：legacy `failed_writes.jsonl` 里若 `concept_id` 非 UUID，结构化警告而不是默写文本到 Neo4j
- **`backend/tests/unit/test_concept_ref_invariant.py`** — 17 个 ConceptRef 不变量 tests
- **`backend/tests/unit/test_identifier_validators.py`** — 16 个 is_uuid_v4 边界 tests
- **`backend/tests/unit/test_verification_concept_id_propagation.py`** — 8 个概念 ID 传播链 tests
- **`backend/tests/unit/test_fsrs_rerank_concept_id_keying.py`** — 6 个 FSRS 重排序键控 tests
- **`backend/tests/unit/test_fallback_sync_concept_id_contract.py`** — 5 个 fallback_sync UUID 契约 tests
- **`backend/tests/unit/test_extract_concepts_returns_refs.py`** — 10 个 extract 返回 ConceptRef 契约 tests
- **`backend/tests/unit/test_review_service_field_split.py`** — 6 个 review_service 字段拆分 tests
- **`backend/tests/unit/test_card_states_compat_read.py`** — 9 个双桶兼容读 tests

### 5.4 关键决策理由

1. **为什么必须统一身份契约？**
   - **根因 bug**：原 verification / memory / review / fallback_sync 四个 service 混用 UUID 和文本作为 "concept" 字段。
   - **具体后果**：`memory_service._inject_fsrs_r_values` 查 `mastery_engine._concept_cache`，但这个 `_concept_cache` 属性 **从来不存在** 在 MasteryEngine 上 — `hasattr` 永远 False，整个 FSRS 注入是 silent no-op，**100% miss**。
   - 用户感知：FSRS 数据完全没影响出题 / 重排序，但 health monitor 不报错。

2. **为什么用 `@dataclass(frozen=True)`？**
   - 防止调用方构造后篡改 `concept_id`
   - 原 bug 类涉及同一个 dict 被多次传递，每个函数往 `concept` key 塞不同的东西（有时 UUID，有时文本）
   - 冻结 dataclass 让这种 mutation 在编译期暴露

3. **为什么 `is_uuid_v4` 严格校验，不接受 v1/v3/v5？**
   - Frontend 用 `crypto.randomUUID()`，永远是 v4
   - 如果非 v4 ID 出现在 concept_id slot，那本身就是个 bug 值得 surface
   - `uuid.UUID(s, version=4)` 不真校验（version 是 hint），所以用 regex
   - 见 identifier_validators.py:34-44 注释

4. **为什么保留 `concept` 遗留别名的双桶兼容读？**
   - 数据迁移期：老的 `failed_writes.jsonl` 里只有 `concept`（文本），新的有 `concept_id` (UUID) + `concept_name` (text)
   - review_service 在读取时同时尝试两个 key，写入时只写新 schema
   - 等老数据消化完再删除别名读路径

5. **为什么修复落在 worktree 分支而不是直接进 main？**
   - 修改面广（18 文件，+2397/-225），需要独立 review
   - 之前 Path D' merge 尝试在 docs/known-gotchas.md + verification_service.py 撞过冲突（被并行 session 抢占 abort）
   - 当前策略 Option D：保持分支独立，让 ChatGPT Deep Research 先 review，再决定 merge 策略

---

## 6. 测试覆盖总览

| 问题 | 新增测试数 | 关键文件 |
|---|---|---|
| **Q1** | 13 unit + 7 e2e | `test_kg_relevance_weighted.py`, `test_a11_kg_relevance_e2e.py` |
| **Q2** | 25 unit | `test_l1_llm_router.py` (15), `test_state_graph_l1_routing.py` (8), `test_langgraph_async_conditional_edge_smoke.py` (2) |
| **Q3** | 77 unit (在 worktree 分支) | `test_concept_ref_invariant.py` (17), `test_identifier_validators.py` (16), `test_verification_concept_id_propagation.py` (8), `test_fsrs_rerank_concept_id_keying.py` (6), `test_fallback_sync_concept_id_contract.py` (5), `test_extract_concepts_returns_refs.py` (10), `test_review_service_field_split.py` (6), `test_card_states_compat_read.py` (9) |

总计：**122 个新增测试** 覆盖 A6 三问。

⚠️ Q1/Q2 在 main 上跑 `pytest` 即可；Q3 需要先 `git checkout fix-concept-id-identity-unification` 分支。

---

## 7. OpenSpec 规范化证据

### 已 archive 的 changes（在 `openspec/changes/archive/`）

- **`2026-04-07-fix-fr-kg-04-schema-drift-and-sync-hardening/`** — Q1 主修复（kg_relevance 加权 + schema 统一 + degraded markers）
- **`2026-04-07-agentic-rag-l1-llm-router/`** — Q2 主修复（L1 LLM 路由 + 三策略 fallback）
- **`2026-04-07-fix-rag-faithfulness-and-add-crag-quality-loop/`** — Q2 副修复（Faithfulness not-applicable 契约 + CRAG fallback）
- **`2026-04-07-fix-rag-transform-and-episode-isolation/`** — Q2 副修复（episode 隔离 + transform 契约）

### 已 archive 后合入主 spec 的 contract

- **`openspec/specs/algo-rag/spec.md`** — Q2 (Faithfulness / Fusion / CRAG 三个新 contract)
- **`openspec/specs/agentic-rag/spec.md`** — Q2 (L1 router 配置 + 状态契约)
- **`openspec/specs/algo-question/spec.md`** — Q1 (kg_relevance 契约)
- **`openspec/specs/algo-scoring/spec.md`** — Q1/Q3 (learning relationship field 一致性)
- **`openspec/specs/canvas-sync/spec.md`** — Q1 (CANVAS_EDGE 契约)
- **`openspec/specs/verification-service/spec.md`** — Q3 (verification 相关 + ConceptRef 契约的部分)

### ⚠️ 未 archive 的 change

- **`fix-concept-id-identity-unification`** — Q3 主修复（在 worktree 分支上），proposal/design/specs/tasks 4 件套在分支 URL 内，未走 `npx openspec archive` 流程

---

## 8. 给 ChatGPT Deep Research 的 review 提示

### 建议 review 路径

1. 先读 `docs/project-status/fr-exploration/A6.md`（33 行）理解 User 2 原始问题
2. 再读本文档（A6-resolution-summary.md）拿到全景
3. 按 **Q1 → Q2 → Q3** 顺序展开 review
4. **Q1 / Q2 的证据文件**：直接通过 `main` 分支访问
   `https://github.com/oinani0721/canvas-learning-system/blob/main/<path>`
5. **Q3 的证据文件**：需切到 `fix-concept-id-identity-unification` 分支
   `https://github.com/oinani0721/canvas-learning-system/tree/fix-concept-id-identity-unification`

### 对抗性审查角度（每问的薄弱点）

**Q1 加权融合**

- 1.0 / 0.7 的权重选择是否合理？是否应该是基于用户行为数据训练出来的（非常数）？
- 归一化常数 8.0 是否有学术支撑？（**design.md D3 标注 no academic backing**）
- `MAX(CASE type(r) ...)` 是否在多重边场景下产生正确语义？是否应该 `SUM`？
- 是否考虑过基于学习理论的权重（例如 Kuhlthau 的 ISP 模型对显式 vs 隐式知识的处理）？

**Q2 Agentic RAG**

- 5 路并行检索是否过度？延迟 / 成本是否可接受？是否应该按 intent 只跑 2-3 路？
- L1 LLM 路由的成本（每个 query 一次 Gemini Flash 调用）在大规模下是否合理？
- fallback chain 是否完备？有没有 silent failure 场景（LLM 返回非法 intent 但 success=True）？
- Faithfulness 的 NLI 阈值 0.85 是否经过 ablation？
- CRAG one-shot 的"换条路径"是否在所有 fallback 失败后还能 graceful degrade？
- 与 RAGAS / Self-RAG / GraphRAG 等社区方案对比，本设计的 trade-off 在哪？

**Q3 ConceptRef 身份契约**

- ConceptRef 是否真的覆盖了所有入口？是否存在测试未覆盖的文本 → UUID 泄漏路径？
- 双桶兼容读（concept + concept_id）的退役计划是什么？数据迁移完整性如何验证？
- FSRS 重排序的 50% 加成上限是否合理？低 R-value 是否应该有更陡的曲线？
- 出题优先级公式 `0.4 * (1-p_mastery) + 0.3 * (1-retrievability) + 0.3 * kg_relevance` 的三权重 (0.4/0.3/0.3) **没有学术支撑，无 ablation study**（A10 调研未完成）
- `is_uuid_v4` 严格拒绝 v1/v3/v5 是否对未来兼容性是个负担？
- `_inject_fsrs_r_values` 的 hit/miss/hit_rate 结构化日志是否足以监控生产环境的回退？

### 社区对比维度

- **Agentic RAG vs Vanilla RAG vs GraphRAG**：检索精度 / 延迟 / 成本对比的最佳实践
- **BKT + FSRS + KG 三因子融合**：学术界有没有类似的"知识掌握度 × 遗忘曲线 × 图结构"复合公式？
- **Cross-encoder 重排序**：sentence-transformers vs cohere rerank vs ColBERT 的 trade-off
- **Concept identity contracts**：学术界 / 工业界对"机器 ID vs 人类显示名"的混淆问题有什么标准解？

---

## 9. 后续待解决（本次未覆盖）

| 项目 | 状态 | 备注 |
|---|---|---|
| `fix-concept-id-identity-unification` change archive | 未完成 | OpenSpec change 未走 `npx openspec archive`（worktree 未 merge main） |
| Path D' merge 重试 | 暂停 | 2026-04-06 尝试时撞 docs/known-gotchas.md + verification_service.py 冲突，被并行 session 抢占 abort |
| FSRS 三权重 ablation study | 未完成 | (0.4 / 0.3 / 0.3) 无学术支撑，无 ablation 数据，A10 调研未完成 |
| 002 migration 脚本生产运行 | 未完成 | `002_canvasnode_uuid_to_id.cypher` 未在生产 Neo4j 跑过（Phase 16 deferred） |
| kg_relevance 归一化常数 8.0 学术验证 | 未完成 | design.md D3 标注 "no academic backing" |
| L1 LLM 路由生产监控 | 部分 | benchmark 脚本存在但未进 CI gate；生产 latency / cost / fallback rate 仪表盘未建 |
| Q3 worktree 分支 merge 决策 | 待 review 后定 | Option A merge / Option D 保持独立 — 取决于 Deep Research review 结果 |

---

> **本文档归档说明**：
> 创建于 2026-04-07，作为 A6 修复成果的 Deep Research review 入口。
> ChatGPT Deep Research review 完成后，建议把结论以 `[Decision]` 形式回写到 Graphiti `canvas-dev` group_id。
