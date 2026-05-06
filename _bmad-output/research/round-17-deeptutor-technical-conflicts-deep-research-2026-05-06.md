---
title: Round 17 — DeepTutor ↔ Canvas 技术冲突 + 有效点针对性 Deep Research
date: 2026-05-06
trigger: round-16 后用户指令"技术的衔接分析需要针对性 deep research，分析冲突点+有效点"
agents: 4 并行 Explore Agent (Sonnet)
related:
  - _bmad-output/research/round-16-deeptutor-canvas-flow-deep-explore-2026-05-06.md
  - _bmad-output/research/round-15-bkt-fsrs-multihop-tauri-prd-deep-explore-2026-05-05.md
  - _bmad-output/research/round-14-graphiti-retrieval-deep-explore-2026-05-05.md
status: 调研报告，待用户审计后决定 Phase 1 启动
---

# Round 17 — DeepTutor ↔ Canvas 技术冲突 + 有效点针对性 Deep Research

## 元信息

| 字段 | 值 |
|---|---|
| 触发 | round-16 后用户指令"技术的衔接分析 — 分析技术的冲突点、有效点，针对性 deep research" |
| 调研方式 | 4 并行 Explore Agent，按技术层面分工 |
| 范围 | RAG 层 / Memory 层 / Book Engine + Question Bank 层 / Capabilities + Skill 层 |
| 报告字数 | ≈12000 字 |
| 状态 | 初稿，待用户审计后决定 Phase 1 实施起点 |

---

## 用户原始指令

> 技术的衔接分析，我的建议是针对性的 deep research，因为你要分析技术的冲突点，有效点，需要你启动相关的 agent deep explore 编写提示词

→ 之前 round-16 偏"用户视角学习方案"，本轮转向**技术冲突 + 有效点针对性分析**
→ 4 Agent 分别聚焦 4 个技术层面，每层独立给冲突维度表 + 有效点 + 路径权衡

---

## 一句话核心结论

**整体兼容度 5.1/10**（4 层加权平均：RAG 6.5 / Memory 4 / Book 6 / Capabilities 4）。两套系统**底层协议层不兼容**（Skill 格式 / Agent 框架 / Skill 协议 / Embedding 维度），但**API 层有 22 个直接对接点**（Canvas MCP server 18 工具 + REST `/api/v1/chat/enrich-context` + `/api/v1/rag/search` 等）。最优策略：**Canvas 作为学习记忆 + 算法 SoT，DeepTutor 仅消费 API**——双方均无需改动核心框架，通过 HTTP/MCP 桥接整合。**总工程量 28-35 天**（4 层联合实施，含 Bridge API 复用去重）。

---

## 第一部分：RAG 层技术冲突 + 有效点（Agent 1）

### 1.1 兼容度评分：6.5/10

DeepTutor 是 2023 年 LlamaIndex 风格的**单体 RAG**，Canvas 是 2026 年 LangGraph **agentic** 风格的多源融合 RAG。**两个完全不同的技术代际**，但核心数据结构（SearchResult dict、512/50 切块参数）高度一致，且 Canvas 已为 LlamaIndex 桥接预留 HTTP API 入口（`/api/v1/rag/search`）。

### 1.2 5 维冲突点

**User：但是我们的后端这些 RAG 测试，没有实际验证，对我来说像一个黑盒，是一个未知的，不一定稳定成熟的框架，所以这是让我十分痛苦的地方。我的 Canvas learning systeam RAG 设计，有什么基准测试可以证明是有效的，而不是无意义的构造，而且这里的 DeepTutor 的 RAG  和 Canvas learning systeam 的 RAG 使用途径是不同的吧，我们现在主要从需求对齐出发，DeepTutor 是否可以实现 Canvas learning systeam 所列出来的学习工作流**

| 维度                  | DeepTutor                                           | Canvas                                                                                                                             | 冲突类型                     | 改造方向                                                                              |
| ------------------- | --------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- | ------------------------ | --------------------------------------------------------------------------------- |
| **向量库实现**           | `SimpleVectorStore`（JSON + 暴力线性扫描）                  | `LanceDBClient` HNSW ANN（`lancedb_client.py:281`，timeout=400ms）                                                                    | **完全不兼容**                | DeepTutor 切 `LanceDBVectorStore`（LlamaIndex 官方支持，0.5d）                            |
| **混合检索**            | 仅向量 cosine + 简单拼接（前 6000 字符）                        | 5 路并行（Graphiti + LanceDB + multimodal + cross_canvas + vault_notes）+ LangGraph Send + LanceDB 内部 jieba BM25 + bge-m3 dense hybrid  | 设计差异（可桥接）                | DeepTutor SmartRetriever 作为 LangGraph 节点接入 Canvas Layered-RRF                     |
| **Reranker**        | 无（Issue #304 未关闭）                                   | `gte-reranker-modernbert-base` fp16（149M，`reranking.py:79`）+ adaptive-K 截断（top_k 3-15）                                             | **完全不兼容**                | DeepTutor 直接 `from agentic_rag.reranking import get_reranker`（0.5d，warm 50-100ms） |
| **Score 阈值 / 质量门控** | 无（top_k=5 全收）                                       | CRAG 质量门控（`check_quality` → `route_after_quality_check` → `rewrite_query` 最多 2 次 → `deep_research_fallback`，quality_threshold=0.7） | 设计差异                     | 路径 C 天然包含；独立引入需 1.5d                                                              |
| **Embedding 模型**    | 多提供商（OpenAI/Cohere/Jina/Ollama），维度 1536/1024/384 混合 | 锁定 `BAAI/bge-m3` **1024d**，`config.py:38-48`，旧 384d 标记 deprecated                                                                  | **部分兼容**（维度不一致 → 完全无法搜索） | DeepTutor 切换 bge-m3（本地 Ollama 或 sentence-transformers）                            |

### 1.3 5 个有效点（直接对接）

| #   | 有效点                                                                                                                           | 工程量           | 风险                            |     |
| --- | ----------------------------------------------------------------------------------------------------------------------------- | ------------- | ----------------------------- | --- |
| 1   | **LlamaIndex 官方 `LanceDBVectorStore`**：`from llama_index.vector_stores.lancedb import LanceDBVectorStore`，db_path 对齐即可读写同一数据库 | 4h（替换 + 重建索引） | upstream 序列化兼容性               |     |
| 2   | DeepTutor `EmbeddingProviderFactory` 复用给 Canvas 做 Ollama 失败时的 OpenAI failover                                                 | 0.5d          | 维度变化检测                        |     |
| 3   | **DeepTutor `EmbeddingSignature` 5 元组**（model_name/dim/provider/version/hash）加到 Canvas 防 embedding 模型变更后向量污染                  | 2-4h          | 极低                            |     |
| 4   | SHA256 去重 与 Canvas MD5 fingerprint 一致（统一为 SHA256 即可互认）                                                                        | 2-3h          | 哈希精度差异                        |     |
| 5   | DeepTutor version-N 增量索引机制 → Canvas `lancedb_index_service.py` 加 dirty file 检测                                                | 0.5d          | LanceDB 表结构需加 `indexed_at` 字段 |     |

### 1.4 3 路径权衡

#### 路径 A：DeepTutor RAG 升级到 Canvas 水准
- 替换 SimpleVectorStore → LanceDB + jieba BM25 hybrid + Reranker + CRAG
- **5-7d**（含测试）
- ⚠️ DeepTutor upstream 高冲突；本地 bge-m3 推理依赖重；增量索引迁移需数据脚本
- 适合：DeepTutor 已 fork 不需回馈上游

#### 路径 B：双 RAG 并存（HTTP 桥接）
- DeepTutor 暴露 `/api/deeptutor/v1/search`；Canvas 暴露 `POST /api/v1/rag/search`
- DeepTutor quiz/chat 走自己 LlamaIndex；Canvas 检验白板走 4 路融合
- **1-2d**
- ⚠️ 数据冗余（同 PDF 双 embedding，存储翻倍）；一致性差；延迟 +HTTP RTT 5ms

#### 路径 C：DeepTutor 调用 Canvas RAG ⭐ 推荐
- DeepTutor `SmartRetriever` 改为 HTTP 调 Canvas `/api/v1/rag/search`
- 返回 `List[SearchResult]` 适配 LlamaIndex `NodeWithScore`（`content`→`text`，`score`→`score`）
- LlamaIndex 其他组件（LLM 调用、Memory 注入）保持不变
- **2-3d**（adapter 层 + 接口测试）
- ✅ DeepTutor 彻底获得 Canvas Reranker + CRAG + 5 路融合，**无 upstream 冲突**

### 1.5 4 关键技术决策（推荐）

| Q | 选项 | 推荐 | 理由 |
|---|---|---|---|
| Q1 | bge-m3 1024d vs OpenAI text-embedding-3-large 3072d | **bge-m3** | 隐私优先（个人 Vault）+ Canvas 已锁定 1024d（零迁移）+ 中文场景实测差距不显著 |
| Q2 | CRAG 质量门控是否引入 DeepTutor | **路径 C 天然包含** | 路径 A 独立引入约 1.5d，但要改 SmartRetriever 同步→异步 |
| Q3 | gte-reranker-modernbert-base 本地跑 vs Cohere API | **本地** | Canvas 已有 singleton（lazy load 3s 后缓存），warm 50-100ms 可接受；Cohere 限额 50 次/月不够 |
| Q4 | LanceDB HNSW vs SimpleVectorStore（100K+ chunk）| **LanceDB** | LanceDB nprobe=64 在 100K 下 P95 < 10ms，SimpleVectorStore 线性 200-800ms |

### 1.6 推荐对接策略 + 工程量

| 阶段 | 事项 | 工程量 |
|---|---|---|
| **立即做（高 ROI）** | DeepTutor 接 Canvas Reranker + 切 LanceDB + 加 EmbeddingSignature | **1.5d** |
| **Phase 1（中 ROI）** | 路径 C HTTP adapter + 增量索引迁移 | **3.5d** |
| Phase 2+ | CRAG 移植 + bge-m3 完全替换 | 5d |

**关键路径**：bge-m3 嵌入对齐（影响立即做 #2 + Phase 1 #4 的正确性），第一天即确认本地 Ollama bge-m3 服务可用（`LANCEDB_EMBEDDING_MODEL=BAAI/bge-m3`）。

---

## 第二部分：Memory 层技术冲突 + 有效点（Agent 2）

### 2.1 兼容度评分：4/10

DeepTutor Persistent Memory（SUMMARY.md + PROFILE.md）与 Canvas Graphiti+BKT+FSRS 在**存储哲学上南辕北辙**（叙述型 Markdown vs 强类型时序图），但存在 5 条可工程化的桥接路径，整合难度属"中等桥接"，不需要推倒重来。

### 2.2 6 维冲突点

| 维度 | DeepTutor Memory | Canvas Graphiti+BKT+FSRS | 冲突类型 | 改造方向 |
|---|---|---|---|---|
| **存储格式** | Markdown 文件（叙述型非结构化）| Neo4j 图数据库（强 Pydantic schema）| **完全不兼容** | 双轨并存：Markdown 服务 chat persona，Neo4j 服务算法 |
| **数据模型** | 自由文本（heading 约束）| 4 类 entity（`LearningConcept/MasteryRecord/Misconception/LearningTip`）+ 5 类 edge | **完全不兼容** | 桥接层：PROFILE.md → 单向解析为 `LearnerProfile` episode |
| **更新触发** | 每轮 LLM 重写整个文件 | 学习事件写入 `episode_worker.py:468`（`enqueue()`），队列去重，指数退避 | 设计差异 | 策略 C（独立）最低风险；策略 B（双向）需去抖动 |
| **查询能力** | `build_memory_context(max_chars=4000)` 字符截断 | Cypher + `search_nodes()`/`search_edges()` + Graphiti 向量语义搜索 | **完全不兼容** | DeepTutor 通过 MCP 调 Canvas `search_memories` 替代截断注入 |
| **时序追踪** | 无时间戳，新写覆盖旧 | Episode `created_at/valid_at/invalid_at` + Graphiti 时序失效机制 | **完全不兼容** | DeepTutor SUMMARY 定位为"近期快照"，Canvas Graphiti 承担完整历史 |
| **掌握度建模** | 叙述性"已掌握内容" | `ConceptState.p_mastery` BKT + `fsrs_stability/difficulty/card_data` FSRS 19 参数（`mastery_state.py:82-92`）| **完全不兼容** | BKT/FSRS 完全留 Canvas；DeepTutor PROFILE 增加 `## Mastery Snapshot` 章节接收推送 |

### 2.3 5 个有效点

| # | 有效点 | 工程量 | 风险 |
|---|---|---|---|
| 1 | PROFILE.md 学习者画像 → Graphiti `LearnerProfile` episode | 1.5d | 自由文本 → 强类型转换可能丢语义；需新增 `LearnerProfile` 类型 |
| 2 | DeepTutor SQLiteSessionStore → Canvas episode 输入 | 0.5d | group_id 需迁到新格式 `vault:<id>` |
| 3 | **Canvas Graphiti 作为 DeepTutor agent "tool"**（MCP 14 工具）| 0.5d | 网络延迟（同机器无问题）；Zod anyOf bug 已修 |
| 4 | DeepTutor SUMMARY.md → Canvas `ACPData.conversation_summary` 字段 | 0.25d | SUMMARY 是近期 10 条摘要，旧记录可能丢 |
| 5 | Canvas BKT/FSRS → DeepTutor PROFILE.md `## Mastery Snapshot` 章节 | 0.5d | DeepTutor LLM 重写需"保留章节"约束 |

### 2.4 3 关键冲突详解

#### 冲突 1：异构数据模型同步策略

| 策略 | 描述 | 工程量 | 一致性风险 | 推荐 |
|---|---|---|---|---|
| **A. Canvas 单向消费** | Canvas SoT，DeepTutor 启动/对话前从 Canvas 拉数据生成 SUMMARY/PROFILE 草稿 + LLM 润色 | 2d | **低**（Canvas 唯一写入者）| ⭐ 推荐 |
| B. 双向同步 | DeepTutor 写 SUMMARY → 触发 Canvas episode；Canvas 学习事件 → 触发 SUMMARY 重写 | 4d | **高**（写冲突 + 循环触发，需"来源标记"防回环）| 不推荐 |
| C. 完全独立 | DeepTutor SUMMARY 仅服务 chat；Canvas Graphiti 仅服务出题 | 0d | **数据孤岛** | MVP 阶段过渡 |

**建议**：先策略 C（零成本验证），有效点 2+4 单向桥接后升级为**策略 A 变体**（Canvas 出题时按需拉 DeepTutor SUMMARY 作补充上下文）。

#### 冲突 2：4000 字符截断 vs Graphiti 完整查询

DeepTutor `max_chars=4000` 硬截断无优先级；Canvas Graphiti 可能返回数十 episode。

**方案**：
- ✅ Canvas 侧 `_get_error_history()` 构建 ≤800 字符结构化摘要（top-3 弱节点 + top-3 错误）→ 作为 `conversation_summary` 注入（与现有 ACPData 3K token 预算一致）
- ✅ 或 DeepTutor 改用 Canvas MCP `search_memories(query=当前话题)` 按需检索 top-3 episode（0.5d）

#### 冲突 3：Temperature 重写 vs Episode 累积

DeepTutor temperature=0.2 每次重写整个 SUMMARY/PROFILE，未被最近 10 条会话覆盖的历史细节会消失。Canvas Graphiti 累积式（`add_episode()` 仅新增，通过 `invalid_at` 标记失效）。

**核心定位分离（推荐）**：

| 系统 | 职责 | 时间范围 |
|---|---|---|
| DeepTutor SUMMARY/PROFILE | Chat persona 近期快照 | 最近 10 条会话 |
| Canvas Graphiti | 完整学习历史 | 全程 |

出题查 Graphiti（细节），对话用 SUMMARY（快速低延迟）。两者不竞争，各司其职。

### 2.5 BKT/FSRS 完全保留 Canvas 的论证

| 维度 | Canvas 现状 | DeepTutor 现状 | 迁入风险 |
|---|---|---|---|
| BKT | `mastery_engine.py:216-270` 贝叶斯 + 3 难度参数 | 无 | 重新实现 ~3d，参数调优需数据 |
| FSRS | `fsrs_manager.py` py-fsrs 4.5 + CardState 19 参数 | 无 | py-fsrs import 一行，schema 改造 ~2d |
| 测试覆盖 | **104 个专项测试**（`test_fsrs_manager.py` 526 行 + `test_review_service_fsrs.py` 598 行 + `test_mastery_engine_bkt.py` + `test_mastery_engine_fsrs.py`）| 零 | 重建测试基线 ~3d，无历史数据验证参数 |
| 端到端 | Canvas Story 5.1/5.2 已部分实施 | 零基础 | UAT 风险高 |
| 依赖复杂度 | `ConceptState` + `MasteryConfig` + Neo4j 存储 | 依赖 SQLite | 迁存储层 ~2d |

**结论**：迁入约 10d 且失去 104 测试安全网。**完全保留 Canvas BKT/FSRS 是唯一理性选择**。DeepTutor 通过 HTTP 调 Canvas `query_mastery` / `update_bkt` / `update_fsrs` API。

### 2.6 推荐对接策略

**总体原则**：Canvas Graphiti+BKT+FSRS 是**学习算法 SoT**，DeepTutor 是 **chat UX 层**。数据流向单向：Canvas → DeepTutor。

**分阶段实施**：

| 阶段 | 内容 | 工程量 |
|---|---|---|
| 阶段 0（立即）| 策略 C 完全独立，验证各自功能 | 0d |
| 阶段 1 | 有效点 3：DeepTutor MCP config 注册 Canvas MCP server（14 工具）→ DeepTutor agent 按需调 `search_memories`/`query_mastery` | 1d |
| 阶段 2 | 有效点 4+5：SUMMARY → ACPData.conversation_summary；Canvas BKT/FSRS → PROFILE Mastery Snapshot | 1d |
| 阶段 3 | 有效点 2：DeepTutor SQLite session → Canvas episode（异步写入）| 1.5d |

**已知残缺（不在桥接范围，需 Canvas 自身修复）**：
- 错误只写不读（round-14 P0 bug）：`record_error` 只写 Graphiti，无按 misconception 类型读取的端点 → 桥接前必须修复
- `cs188` hardcode → 迁到 `vault:<id>` 格式，否则 DeepTutor 按 `vault:default` 查询命中空结果

---

## 第三部分：Book Engine + Question Bank 技术冲突 + 有效点（Agent 3）

### 3.1 兼容度评分：6/10

Book Engine 4 层模型 + QUIZ/FLASH_CARDS block + SSE 流式机制三点与 Canvas 直接对接；但 Question Bank schema 无 FSRS、CONCEPT_GRAPH 纯渲染无推理、is_correct 二元 vs 4 维 SOLO Rubric、deep_question 4-stage vs ACP 5 层 — **4 项核心冲突**必须通过桥接或改造解决后整条学习闭环才能成立。

### 3.2 8 维冲突点

| 维度 | DeepTutor | Canvas | 冲突类型 | 改造方向 |
|---|---|---|---|---|
| **数据结构** | Book→Spine→Chapter→Page→Block 4 层 | `exam_boards/*.md` 单 md（`source_description='exam_session'`）| 设计差异（可映射）| 桥接：Book 作组装容器，md 作输出载体 |
| **block 类型** | 14 种枚举强 schema | 纯 md 多段 | 部分兼容 | 仅激活 8 种 block（见 3.5）|
| **三重隔离** | `Book.type` 字段无等价 | `_get_canvas_type()` 三重隔离（session 内存 + Neo4j source_description + Skill prompt 约束）| **完全不兼容** | Canvas 改：Book 加 `book_type='exam_board'`；桥接层校验防嵌套 |
| **题目生成 prompt** | 4-stage（Ideation→Drafting→Validation→Finalization）序列 | `build_5_layer_prompt()` 单次大 prompt | 部分兼容（层次错位）| **替换：用 Canvas question_generator 整体替换 deep_question**，保留 Drafting 壳子注入 5 层 |
| **难度建模** | 离散 difficulty（Easy/Medium/Hard）| `effective_proficiency` 连续值 + difficulty_level 4 级 | 部分兼容（精度不足）| DeepTutor 用 Canvas `effective_proficiency` 连续值替换 |
| **CONCEPT_GRAPH** | `ConceptGraphGenerator` deterministic renderer，**不调 LLM** | Cypher multi-hop 查询 + LLM 跨节点推理题 | **完全不兼容** | 桥接：Canvas 上游生成子图 JSON → 注入 `ctx.extra` + Layer 3 ACP，CONCEPT_GRAPH block 仅渲染 Mermaid |
| **评分** | `QuizAttempt.is_correct: bool` 二元 | `AutoScoreResult` 4 维 × 0-3 + 3 投票 + faithfulness 校验 + grade 1-4 | **完全不兼容** | 替换：DeepTutor 不评分，POST Canvas `/api/v1/score/autoscore` |
| **复习调度** | Record.metadata 无 FSRS | `FSRSManager` py-fsrs 4.5 完整实现 | **完全不兼容** | DeepTutor 改：Record.metadata 加 fsrs 子 dict + 复制 Canvas FSRSManager 200 行 |

### 3.3 6 个有效点

| #   | 有效点                                                                                        | 工程量                  |
| --- | ------------------------------------------------------------------------------------------ | -------------------- |
| 1   | **QUIZ + FLASH_CARDS block 直接对接**（数据字段同构）                                                  | 1-1.5d（compiler 适配器） |
| 2   | **Spine→Chapter→Page 4 层契合检验白板**（Book=检验白板 / Spine=ACP 选题大纲 / Chapter=Bloom 层分组 / Page=单题） | 1d                   |
| 3   | Book status 机器（DRAFT→SPINE_READY→COMPILING→READY）↔ ExamStatus 直接映射                         | 0.5d                 |
| 4   | DeepTutor `compiler.py` 作 Canvas 题目组装引擎                                                    | 1.5d                 |
| 5   | **CONCEPT_GRAPH block 接 Canvas multi-hop 子图**（Cypher → Mermaid 转换）                         | 2-3d                 |
| 6   | SSE trace_callback ↔ Canvas WebSocket（协议层兼容，事件归一化）                                         | 1d                   |

### 3.4 4 关键冲突详解

#### 冲突 1：deep_question.py 4-stage vs ACP 5 层 prompt

**根本问题**：DeepTutor 4-stage 是**多次 LLM 调用流水线**；Canvas ACP 5 层是**单次大 prompt 结构化注入**（`question_generator.py:417-459`）。

**核心差距**：DeepTutor Validation stage（自我检查）有价值——Canvas question_generator 直接 LLM 输出无等价自检（`question_generator.py:461-533`）。

**推荐方案 B+**：
- 完全用 Canvas question_generator 替换 deep_question 4-stage
- 在 Canvas `_call_llm_for_question()` 内加入 1 次 validation 调用（~20 行，复用 AutoScorer `_extract_evidence()` 逻辑）
- **2-2.5d**

#### 冲突 2：CONCEPT_GRAPH deterministic vs multi-hop LLM 推理

**根本问题**：DeepTutor `ConceptGraphGenerator` 仅渲染（不调 LLM）；Canvas FR-EXAM-03 要求 multi-hop 推理生成题目。**两个完全不同功能层**：渲染 vs 推理。

**桥接方案**：
1. Canvas question_generator 上游 `_get_kg_subgraph(node_id)` → Cypher 2-hop 返回子图 JSON
2. 子图 JSON 注入 ACP Layer 3，LLM 看到完整 KG 上下文出"跨节点推理题"
3. 同一子图 JSON 转 Mermaid（`networkx` → Mermaid converter ~50 行）→ 注入 CONCEPT_GRAPH block
4. DeepTutor CONCEPT_GRAPH 仅做视觉展示

**效果**：题目有 multi-hop 推理；检验白板有概念图；功能层清晰。**2-3d**

#### 冲突 3：is_correct 二元 vs 4 维 SOLO Rubric

**根本问题**：`QuizAttempt.is_correct: bool` 无法表达 `AutoScoreResult` 4 维信息 + faithfulness + evidence。**数据模型范式不同**：二元分类 vs 多维连续评分。

**实际验证**（`autoscore.py:39-44`）：Canvas GRADE_THRESHOLDS 已将 0-12 总分 → 1-4 grade，与 FSRS Rating 1:1 对应。

**推荐方案**：
- DeepTutor 完全不评分，POST Canvas `/api/v1/score/autoscore`
- Canvas 返回 `AutoScoreResult` → DeepTutor 用 grade 触发 FSRS rating
- `QuizAttempt` 扩展：`is_correct` 保留（grade>=3 为 True）+ `autoscore_result: Optional[dict]` 存 4 维详情
- DeepTutor UI 加 4 维 Rubric 展示卡片
- **1-1.5d**

#### 冲突 4：Question Bank Record 无 FSRS 字段

**推荐方案**：Record.metadata 扩展（向下兼容）：

```json
"metadata": {
  "fsrs": {
    "due": "2026-05-10T00:00:00Z",
    "stability": 4.2,
    "difficulty": 0.55,
    "state": 2,
    "reps": 3,
    "lapses": 0,
    "last_review": "2026-05-05T00:00:00Z"
  }
}
```

直接复制 `FSRSManager` 到 `deeptutor/services/fsrs/service.py`（无结构修改）。新增 `review_record(record_id, grade) → Record` + `get_due_records(kb_name) → list[Record]`。**4-5d**（含 API endpoint + UI Due Today 面板）。

### 3.5 ACP 5 层 prompt 在 deep_question.py 注入

**注入位置**：DeepTutor Drafting stage（Stage 2）的 system prompt。

```python
# deeptutor/capabilities/deep_question.py — Stage 2 改造
async def _stage2_drafting(self, kb_name: str, block_id: str) -> str:
    # 1. 从 Canvas 拉 ACP
    acp = await canvas_bridge.get_acp(node_id=block_id)
    # 2. 调 Canvas build_5_layer_prompt（含 5 个 layer*.md 文件）
    question_gen = QuestionGenerator()
    return question_gen.build_5_layer_prompt(acp, exam_mode)
```

5 个 layer prompt 文件（Canvas 已有，DeepTutor 通过 symlink 或复制）：
- `backend/app/prompts/exam/layer1_role.md`
- `backend/app/prompts/exam/layer2_mode.md`
- `backend/app/prompts/exam/layer3.md`（动态模板）
- `backend/app/prompts/exam/layer4_rules.md`（含 4 类 REMEDIATION_STRATEGIES）
- `backend/app/prompts/exam/layer5_scoring_preset.md`

ACPData 通过 Canvas Bridge API `GET /api/v1/vault/notes_context?node_id=X` 获取。**2-2.5d**

### 3.6 Block 映射方案（8 用 / 6 暂不用）

| Canvas 内容        | DeepTutor BlockType | 改造                                                     |
| ---------------- | ------------------- | ------------------------------------------------------ |
| 题目主体             | QUIZ                | 加 `acp_node_id`+`bloom_level`+`target_error_type` 3 字段 |
| 概念回顾闪卡           | FLASH_CARDS         | 直接用                                                    |
| 概念关联图（multi-hop） | CONCEPT_GRAPH       | 接 Cypher → Mermaid（~2-3d）                              |
| 用户笔记 / 批注        | USER_NOTE           | 直接用，映射 [!tip]+                                         |
| 题目背景解释           | TEXT                | 直接用，映射 node_content                                    |
| 历史错误回顾           | CALLOUT             | 直接用，`callout_type='warning'`                           |
| 4 级渐进提示          | DEEP_DIVE           | 直接用，4 级折叠                                              |
| 学习路径时序           | TIMELINE            | 直接用，展示 Day 0/3/7                                       |

暂不激活 6 种：FIGURE / INTERACTIVE / ANIMATION / CODE / Phase 4 SECTION / Phase 4 CONCEPT_GRAPH。

### 3.7 推荐对接策略 + 工程量汇总

| 工作项                                             | 优先级 | 工程量  |
| ----------------------------------------------- | --- | ---- |
| Bridge API（4 端点）                                | P0  | 1.5d |
| QUIZ block 扩展 + ExamSession→Book adapter        | P0  | 1.5d |
| **deep_question 替换为 Canvas question_generator** | P0  | 2d   |
| is_correct → AutoSCORE 桥接 + UI 4 维展示            | P0  | 1.5d |
| FSRSManager 复制到 DeepTutor                       | P1  | 4.5d |
| CONCEPT_GRAPH 接 Cypher 子图                       | P1  | 2.5d |
| SSE→WebSocket 适配器                               | P2  | 1d   |
| TIMELINE block 接 FSRS Day 0/3/7                 | P2  | 1d   |

- **P0 合计 6.5d**（核心闭环）
- **P0+P1 13.5d**（完整 Stage F+G 闭环）
- **全部 15.5d**

**关键风险**：ACP 5 层依赖 Canvas Graphiti 读取路径（round-14/16 4 残缺）。P0 实施前必须先修 Graphiti 读取（6-8d），否则 Layer 3 ACP 数据为空，"诱导再犯"策略无法触发。

---

## 第四部分：Capabilities + Skill 技术冲突 + 有效点（Agent 4）

### 4.1 兼容度评分：4/10

DeepTutor 与 Canvas 在**底层协议层**（Skill 格式、Agent 框架、部署模型）存在 4 处结构性不兼容，但在 **API 层**（MCP 工具、SSE 事件、RAG 管道）存在 6 个直接对接点。

**最高价值路径**：Canvas MCP server（**实测 18 个工具**，`server.py:607` 日志确认 `Registered 18 MCP tool routes`，远超之前调研的 14）作为 DeepTutor 的"学习记忆后端"，Deep Solve 作为 Claudian 的"复杂推理后端"——双方均无需改动核心框架，**通过 HTTP 调用桥接**。

### 4.2 7 维冲突点

| 维度 | DeepTutor | Canvas | 冲突类型 | 改造方向 |
|---|---|---|---|---|
| **入口** | Web app（独立 Next.js）| Obsidian Claudian sidebar | 严重：用户两界面切换 | 桥接：DeepTutor Deep Solve 暴露为 MCP 工具 |
| **触发方式** | Web UI 按钮 / API call | Cmd+Shift+E/C/D hotkey + 剪贴板注入 | 设计差异 | 双轨并存 |
| **Skill 协议** | DeepTutor SKILL.md（叙述）| Claude Code Skill（YAML+MD）| **完全不兼容** | 短期双轨；长期 SkillExecutor 解析 YAML（3-4d）|
| **Agent 框架** | Deep Solve plan→ReAct→write | Claudian + LangGraph agentic RAG + CRAG fallback | 设计差异 | 桥接：Deep Solve 作 Claudian 外部 tool |
| **持久 agent** | TutorBot Soul Template + Heartbeat 主动调度 | 无（每次对话独立）| Canvas 缺失 | TutorBot 通过 Canvas MCP 写 Graphiti 实现跨 session 记忆 |
| **多平台** | Telegram/Discord/Slack | 仅 Obsidian | 范围差异 | DeepTutor 保持多平台，Canvas 短期不扩展 |
| **流式响应** | SSE `_trace_bridge()` | MCP JSON-RPC 同步 | 协议差异 | adapter：SSE → 聚合 → JSON response |

### 4.3 6 个有效点

| # | 有效点 | 工程量 |
|---|---|---|
| 1 | **Deep Solve plan 阶段 → Canvas `enrich-context` 注入**（POST `/api/v1/chat/enrich-context` 返回 `<rag_context>` XML：邻居 + frontmatter + errors + Tips + token 压缩）| 2d |
| 2 | **Canvas MCP 18 工具直接注入 DeepTutor agent**（record_error / update_fsrs / query_mastery / search_memories / get_neighbors / generate_question / score_answer / assemble_acp 等）| 3d |
| 3 | TutorBot Heartbeat + Canvas FSRS due-today | 3d |
| 4 | Deep Research 三源并行 + Canvas 4 路 RAG（增加 `canvas_vault_source` 第 4 源，调 `search_notes` MCP）| 2d |
| 5 | SSE trace_callback ↔ MCP JSON-RPC 桥接（adapter endpoint，无需改 Deep Solve 或 Canvas MCP 内部）| 1.5d |
| 6 | DeepTutor 多平台作为 Canvas 多端入口（手机 Telegram FSRS 提醒）| 2d |

### 4.4 4 关键冲突详解

#### 冲突 1：双对话入口（Obsidian sidebar vs DeepTutor Web）

**推荐方案 A + MCP 桥接**：
- Obsidian Claudian 为主入口（用户工作流单一）
- 简单问题（定义/例子/关系）：Claudian 直接基于 `enrich-context` 返回的 `<rag_context>` 回答（已含邻居+errors）
- 复杂问题（plan→ReAct）：Claudian 调 MCP 工具 `deep_solve(query, canvas_context)`，DeepTutor 后台跑，结果以 MCP response 返回 Obsidian sidebar
- 对话历史通过 Canvas `archive_conversation` + `record_learning_memory` 写 Graphiti

**放弃方案 C（双入口同步）**：需解决"哪个 active session"问题，Canvas `archive_conversation` 是事后归档，不支持实时 session 锁。

#### 冲突 2：Skill 协议不兼容

**短期（Phase 1）**：双轨并存。Canvas Skills 留 `canvas-vault/.claude/skills/`，由 Claudian 引擎执行；DeepTutor 用自己 SKILL.md。两者不互调。

**长期（Phase 3+）**：DeepTutor 加 `SkillExecutor`：
- 解析 YAML frontmatter（`allowed-tools` / `model` / `triggers`）
- Markdown 正文作 system prompt 注入
- `allowed-tools` 映射到 DeepTutor tool registry

工程量约 **3-4d**，仅 Phase 3 做。

#### 冲突 3：TutorBot Soul Template vs Canvas chat-with-context Skill

**对接策略（两层架构）**：
- **TutorBot = 外层人格**：Soul Template 定义 "CS 61B 学习陪伴"，Heartbeat 主动调度
- **chat-with-context = 内层执行**：每次 TutorBot 需回答具体节点问题时，调 Canvas `enrich-context` API 拉上下文，注入 TutorBot 当前对话的 system prompt

#### 冲突 4：Heartbeat 主动调度 vs Obsidian 被动响应

**对接策略**：
- ✅ **Telegram 通道（优先）**：Heartbeat 已支持 → 推送 FSRS due 列表和错误复盘
- ✅ **Obsidian Notice API（次优）**：Canvas plugin 加 `/notify` REST endpoint，Heartbeat 调 `POST http://localhost:27123/notify`（1d）
- ✅ **Dashboard.md 异步写入（最简）**：Heartbeat → `record_learning_memory` → append Dashboard，用户打开 Obsidian 自然看到（0.5d）

### 4.5 MCP 工具暴露 + Deep Solve 集成

**Canvas MCP server 实测 18 工具**（`server.py:607`）：

| 工具组 | 工具 | DeepTutor 调用场景 |
|---|---|---|
| 掌握度 | query_mastery / update_fsrs / update_bkt | TutorBot Heartbeat + 答题后更新 |
| 出题流水线 | generate_question / score_answer / assemble_acp / request_hint / skip_question | Deep Question 完全替换为调这 5 个 |
| 记忆写入 | record_error / record_learning_memory / record_calibration | Deep Solve 检测错误时 |
| 记忆检索 | search_memories / archive_conversation | Deep Solve plan 阶段 |
| 笔记检索 | search_notes / get_neighbors / read_note | Deep Research 第 4 源；Deep Solve plan |
| 对话管理 | archive_conversation / create_exam_node | TutorBot session 结束归档 |
| 基础设施 | check_backend_health / switch_vault | 管理用 |

**Deep Solve 集成接口**（新建 `deeptutor/integrations/canvas_mcp.py`）：

```python
async def planning_with_canvas(query: str, node_path: str) -> dict:
    neighbors = await canvas_mcp.call("get_neighbors", note_path=node_path, hop=2)
    history = await canvas_mcp.call("search_memories", query=query,
                                     node_id=node_path, max_results=5)
    mastery = await canvas_mcp.call("query_mastery", node_id=node_path)
    return {"neighbors": neighbors, "history": history, "mastery": mastery}
```

**或更简单**：直接调 Canvas REST `/api/v1/chat/enrich-context`（一个 POST 拿全部上下文）。Phase 1 用 REST，Phase 2 切 MCP。

⚠️ **pipeline_token 约束**（`server.py:237`）：`generate_question` → `score_answer` → `update_fsrs` 必须遵循 token 传递顺序，不能跳步。

### 4.6 3 阶段推荐对接策略

| 阶段 | 时间 | 内容 | 工程量 |
|---|---|---|---|
| Phase 1 | T+0~T+5d | DeepTutor 调 `enrich-context` + MCP 18 工具 + 错误自动写入 | **5d** |
| Phase 2 | T+5~T+12d | Claudian 调 Deep Solve（MCP 代理工具）+ Deep Question 复用 Canvas 出题流水线 | **6.5d** |
| Phase 3 | T+12d+ | TutorBot Heartbeat + 多平台推送 + SkillExecutor + Deep Research 第 4 源 | **11d** |

**总合计 22.5d**。Phase 1 对用户价值最高（DeepTutor 获得学习记忆后端）且 Canvas 端零风险，**优先启动**。

---

## 第五部分：4 层联合实施综合路线图

### 5.1 4 层兼容度雷达图

```
       RAG (6.5/10)
          │
          │
Memory (4/10) ────●──── Capabilities (4/10)
          │       综合 5.1
          │
       Book (6/10)
```

### 5.2 4 层联合实施（去重 Bridge API）

**Bridge API 复用清单**（4 层共用，避免重复实施）：

| Bridge API | 用途 | Owner | 复用层 |
|---|---|---|---|
| `GET /api/v1/chat/enrich-context` | 邻居 + frontmatter + errors + Tips | Canvas（已有）| RAG / Memory / Capabilities |
| `POST /api/v1/rag/search` | 4 路融合检索 | Canvas（已有）| RAG / Capabilities |
| MCP 18 工具（`server.py`）| 完整学习记忆 + 出题流水线 | Canvas（已有）| Memory / Book / Capabilities |
| `GET /api/v1/vault/notes_context` | 节点上下文（新建）| Canvas（待建 0.5d）| Book / Capabilities |
| `POST /api/v1/score/autoscore` | 4 维 SOLO Rubric | Canvas（已有）| Book |
| `GET /api/v1/fsrs/due-today` | 今日复习汇总（新建）| Canvas（待建 1d）| Book / Capabilities |
| `GET /api/fsrs/due` `POST /api/fsrs/review` | DeepTutor FSRS 端点 | DeepTutor（待建）| Book |

### 5.3 4 阶段实施时间线

#### Stage 0：Canvas 数据基础修复（先决条件，6-8d）

**来自 round-14**，必须完成才能桥接：

| 项 | 工程量 |
|---|---|
| 修 `record_error` 只写不读（加按 misconception 类型读取的端点）| 2-3d |
| 修 group_id 旧格式（cs188 → vault:<id> 全链路迁移）| 1d |
| 修 `search_nodes` Cypher CONTAINS 退化（接入真正 bge-m3 embedding search）| 2-3d |
| 修 wikilink 不写 Neo4j（zero 同步问题）| 1-2d |

#### Stage 1：RAG + Memory 桥接（Phase 1 高 ROI，5-7d）

| 项 | 工程量 | 来源 |
|---|---|---|
| DeepTutor 接 Canvas Reranker（`from agentic_rag.reranking import get_reranker`）| 0.5d | RAG Agent |
| DeepTutor 切 LanceDBVectorStore + bge-m3 对齐 | 0.5d | RAG Agent |
| DeepTutor `EmbeddingSignature` 加到 Canvas 防污染 | 0.25d | RAG Agent |
| Canvas MCP 18 工具注册到 DeepTutor agent（MCP client wrapper）| 1d | Memory Agent + Capabilities Agent |
| DeepTutor SUMMARY → ACPData.conversation_summary | 0.25d | Memory Agent |
| Canvas BKT/FSRS → PROFILE Mastery Snapshot | 0.5d | Memory Agent |
| Deep Solve plan 阶段调 Canvas `/api/v1/chat/enrich-context` | 1d | Capabilities Agent |
| Deep Solve 检测错误 → 调 `record_error` MCP | 0.5d | Capabilities Agent |
| 答题完成 → 调 `update_fsrs` / `update_bkt` MCP | 0.5d | Capabilities Agent |
| 路径 C：DeepTutor SmartRetriever 代理给 Canvas `/api/v1/rag/search`（HTTP adapter）| 2d | RAG Agent |

#### Stage 2：Book Engine + 出题流水线（Phase 2 核心闭环，10-12d）

| 项 | 工程量 |
|---|---|
| Bridge API 4 端点（vault/notes_context + autoscore + error_candidate + fsrs/due）| 1.5d |
| QUIZ block 扩展 + ExamSession→Book adapter（acp_node_id+bloom_level+target_error_type 3 字段）| 1.5d |
| **deep_question 替换为 Canvas question_generator**（Stage 2 Drafting 注入 ACP 5 层）| 2d |
| is_correct → AutoSCORE 桥接 + DeepTutor UI 4 维展示卡片 | 1.5d |
| FSRSManager 复制到 DeepTutor + Record schema 扩展 + CLI/UI Due Today | 4.5d |
| Claudian Skill 调 Deep Solve（MCP 代理工具）| 1d |

#### Stage 3：高级特性（Phase 3 完整闭环，11-15d）

| 项 | 工程量 |
|---|---|
| CONCEPT_GRAPH block 接 Cypher 子图（multi-hop + Mermaid 转换器）| 2.5d |
| TIMELINE block 接 FSRS Day 0/3/7 闭环 | 1d |
| TutorBot Heartbeat + Canvas FSRS due-today | 3d |
| Telegram + Obsidian Notice 双通道推送 | 2d |
| Deep Research 加 `canvas_vault` 第 4 源 | 2d |
| SkillExecutor（YAML frontmatter 解析）| 4d |
| SSE↔WebSocket 适配器 + 节点颜色实时推送 | 1d |

### 5.4 总工程量汇总（4 层联合）

| Stage | 内容 | 工程量 |
|---|---|---|
| **Stage 0** | Canvas 数据基础修复 | **6-8d** |
| **Stage 1** | RAG + Memory 桥接（Phase 1 高 ROI）| **5-7d** |
| **Stage 2** | Book Engine + 出题流水线（核心闭环）| **10-12d** |
| **Stage 3** | 高级特性（完整闭环）| **11-15d** |
| **总计** | | **32-42d**（约 6-9 周，1 人全职）|

**优化后（去重 Bridge API + 并行）**：**28-35d**（约 5-7 周）。

如果 Stage 1+2 由 2 人并行：**3-4 周即可达到核心闭环**（Stage 2 完成）。

### 5.5 关键依赖图

```
Stage 0（Canvas 数据基础）
  │
  ├─► Stage 1 RAG（必须 bge-m3 对齐）
  │     │
  │     └─► Stage 2 Book Engine（必须 ACP 5 层有数据）
  │           │
  │           └─► Stage 3 高级特性
  │
  └─► Stage 1 Memory（必须 group_id 迁移完成）
        │
        └─► Stage 2 出题流水线（必须 search_memories 可读错误）
```

**Stage 0 是硬依赖**，其他 Stage 不能并行启动。

---

## 第六部分：8 个决策点（请用户审计）

### Decision 1：是否先做 Stage 0（Canvas 数据基础修复）？

**Claude 推荐**：✅ 是

**选项**：
- A. **先修 Stage 0（6-8d）**⭐ → 后续桥接稳定，但前 1 周用户看不到 DeepTutor 集成
- B. 跳过 Stage 0，直接 Stage 1（DeepTutor 用 Canvas backend 但忽略错误读取）→ 短期看到 DeepTutor 集成，但"诱导再犯"等核心愿景失效
- C. Stage 0 与 Stage 1 RAG 并行（人力允许的话）→ 节省 3-4d

### Decision 2：DeepTutor RAG 路径选择

**Claude 推荐**：路径 C（DeepTutor 调用 Canvas RAG）

**选项**：
- A. DeepTutor RAG 升级到 Canvas 水准（5-7d）
- B. 双 RAG 并存（HTTP 桥接 1-2d）→ 数据冗余 + 一致性差
- **C. DeepTutor 调用 Canvas RAG（路径 C，2-3d）**⭐ → DeepTutor 彻底获得 5 路融合 + Reranker + CRAG，无 upstream 风险

### Decision 3：Memory 同步策略

**Claude 推荐**：策略 C 起步 → 阶段 1 升级到策略 A 变体

**选项**：
- A. Canvas 单向消费（2d，一致性低风险）
- B. 双向同步（4d，写冲突 + 循环触发风险高）
- **C. 完全独立（0d，MVP 验证）**⭐ → 阶段 1 后升级 A

### Decision 4：deep_question 4-stage 是否替换为 Canvas question_generator

**Claude 推荐**：✅ 替换，但保留 self-check（融合两者优点）

**选项**：
- A. 保留 4-stage，在 Drafting 注入 ACP 5 层（3d）
- B. **完全替换 4-stage，加 1 次 self-check 调用**（2-2.5d）⭐
- C. 双轨并存（简单题用 4-stage，检验白板用 question_generator）

### Decision 5：embedding 模型选择

**Claude 推荐**：bge-m3（与 Canvas 锁定 1024d 一致）

**选项**：
- **A. bge-m3 1024d**（隐私 + 零迁移 + 中文实测差距小）⭐
- B. OpenAI text-embedding-3-large 3072d（需重建索引）
- C. 双轨（敏感数据用 bge-m3，公开数据用 OpenAI）

### Decision 6：Heartbeat 推送通道

**Claude 推荐**：Telegram 优先 + Obsidian Notice 次优 + Dashboard.md 兜底

**选项**：
- **A. Telegram 优先**（已有，2d 改造）⭐
- B. Obsidian Notice API（1d，需 plugin 改造）
- C. Dashboard.md 异步写入（0.5d，最简）
- D. 三通道全做（5d）

### Decision 7：CONCEPT_GRAPH 是否接 multi-hop

**Claude 推荐**：✅ 接（核心愿景 #2 + 用户 Tauri PRD 期望）

**选项**：
- **A. 接 Cypher 子图 → Mermaid 渲染**（2-3d，桥接方案）⭐
- B. 仅做 Mermaid 渲染（0.5d，但失去多段推理出题）
- C. 等 LightRAG 集成（ETA 不确定）

### Decision 8：TutorBot 是否启用

**Claude 推荐**：Phase 3 启用（不阻塞 Phase 1+2）

**选项**：
- **A. Phase 3 启用 TutorBot Heartbeat**（3d + 多平台 2d = 5d）⭐
- B. 不用 TutorBot，仅用 Deep Solve / Deep Question
- C. 替换为 Canvas 自建 archive_scheduler 扩展（2d）

---

## 附录 A：4 Agent 关键发现速查

### Agent 1（RAG）核心发现

- **兼容度 6.5/10** — 数据结构同构但向量库 / Reranker / Embedding 维度不兼容
- **路径 C 最优**：DeepTutor SmartRetriever 代理给 Canvas `/api/v1/rag/search`（2-3d，无 upstream 风险）
- **bge-m3 必须对齐**（1024d）— 维度不一致 = 完全无法搜索
- **Canvas Reranker 立即可接入**（4 行代码）

### Agent 2（Memory）核心发现

- **兼容度 4/10** — 存储哲学南辕北辙（Markdown vs Neo4j）
- **BKT/FSRS 完全保留 Canvas**（迁入 10d + 失去 104 测试 = 不理性）
- **Canvas 是 SoT**，DeepTutor SUMMARY/PROFILE 是派生消费层
- 策略 C → 策略 A 变体渐进升级

### Agent 3（Book Engine + Question Bank）核心发现

- **兼容度 6/10** — 4 层模型 + 8 种 block 直接对接，4 项核心冲突需桥接
- **deep_question 4-stage 替换为 Canvas question_generator + 加 self-check**（2-2.5d，融合两者优点）
- **CONCEPT_GRAPH 桥接方案**：Cypher 子图 → 注入 Layer 3 + Mermaid 渲染
- **FSRSManager 直接复制**（200 行 + Record schema 扩展，4-5d）

### Agent 4（Capabilities + Skill）核心发现

- **兼容度 4/10** — 底层协议 4 处不兼容（Skill 格式 / Agent / 入口 / 流式），API 层 6 个对接点
- **Canvas MCP 实测 18 工具**（不是之前调研的 14）— 完全覆盖 DeepTutor 需求
- **方案 A**：Obsidian Claudian 主入口 + Deep Solve 作为 MCP 代理工具
- **Skill 协议 Phase 3 用 SkillExecutor 兼容**（3-4d，不阻塞 Phase 1-2）

---

## 附录 B：用户 7 心头愿景 ↔ 4 层技术对应

| 愿景 | 实现层 | 当前状态 |
|---|---|---|
| 1. Graphiti 后端 ↔ 前端批注高度一致 | Memory + RAG | Stage 0 修复 + Stage 1 RAG 路径 C |
| 2. 精确多段推理 + 批注驱动出题 | Book Engine（CONCEPT_GRAPH）| Stage 2+3 |
| 3. 原白板 / 检验白板 / FSRS 三位一体 | Book Engine + FSRSManager | Stage 2 |
| 4. 诱导再犯策略 | Book Engine（layer4 REMEDIATION_STRATEGIES）| Stage 2 |
| 5. Graphiti 关系 ↔ wikilink 一致 | Memory + RAG | Stage 0 修复（wikilink 写 Neo4j）|
| 6. AI 主动检测错误 + 增量确认 | Capabilities（TutorBot Heartbeat）| Stage 3 |
| 7. vault 笔记片段精确返回 | RAG（路径 C）| Stage 1 |

---

## 状态

- **报告生成**：2026-05-06 ≈02:30
- **下一步**：等用户审计 8 个决策点
- **建议起点**：Decision 1（Stage 0 是否先做）+ Decision 2（RAG 路径）即可启动 Stage 1
- **依赖关系**：Stage 0 是硬依赖，Stage 1+2 可由 2 人并行
- **后续动作**：用户审定后，转 `_decisions/` + 起草 Stage 0-3 各阶段 Story spec


**User：1，Deeptutor 他难道不是可以阅读本地文件的 CIL 吗？你这里说它 web app ，那么他能不能访问本地的文件；2，最重要的用户批注来进行拆分各个节点内容进行讨论，同时把我用双向链接构建的节点之间的联系，存在后端的 Graphiti 中，这样好让 agent 检测我时知道，我的整一个学习过程的逐步推导过程**