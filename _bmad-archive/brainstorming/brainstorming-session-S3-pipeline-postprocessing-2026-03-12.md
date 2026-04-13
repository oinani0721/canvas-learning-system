---
stepsCompleted: [1, 2, 3, 4]
inputDocuments: []
session_topic: 'S3 Pipeline 后处理重建 — Reranking + Quality Gate + Query Rewrite + Fusion 统一'
session_goals: '实现真正的 reranking；替换假 quality gate；替换假 query rewrite；统一重复实现（6源→3组）'
selected_approach: 'AI-Recommended Techniques'
techniques_used: ['Deep Explore', 'Incremental Questioning', 'Community Validation', 'Adversarial Code Review']
ideas_generated: ['bge-reranker-v2-m3 接入', 'CRAG 质量门控模式', 'LLM query rewrite 激活', '6源→3逻辑组重构', 'query-aware 时间衰减']
context_file: ''
related_issues: '#4,#16'
dependencies: 'S3依赖S1(死代码清理)+P0(分块升级)；S5(A3新功能)依赖S3'
---

# Brainstorming Session Results — S3 Pipeline 后处理重建

**Facilitator:** ROG
**Date:** 2026-03-12
**Session ID:** session-brainstorm-s3-pipeline-2026-03-12

---

## Session Overview

**Topic:** RAG Pipeline 后处理链重建 — 从 Basic 级升级到社区验证的成熟架构

**Goals:**
1. 实现真正的 reranking（bge-reranker-v2-m3 cross-encoder）
2. 替换假 quality gate（对齐 CRAG 模式）
3. 替换假 query rewrite（激活已有 LLM 改写模块）
4. 统一重复实现（6 独立源 → 3 逻辑组 + 删除死代码）

**方法论:** Deep Explore（3 个并行 agent：代码对抗性审查 + RAG 前沿算法调研 + 教育场景检索调研） + 增量提问模式

**关键转折:** 初始方案是"保留 nodes.py 6 源融合"，经 3 个 agent 并行调研后发现当前融合代码全面评级 Basic，且无生产教育系统使用 5-6 源 RRF。方案修订为"简化到 3 逻辑组 + cross-encoder reranker + CRAG 质量门控"。

---

## 代码对抗性审查总结

> 独立 agent 审查，非 deep explore agent 完成。

### 整体评级：Basic

| 组件 | 评级 | 关键问题 |
|------|------|---------|
| RRF 融合 (nodes.py L462-505) | **Basic** | Vanilla unweighted RRF，hardcoded top-10，6 源同等权重 |
| Weighted 融合 (nodes.py L508-546) | **Basic** | Min-max normalization，单结果源归零 bug |
| Cascade 检索 (nodes.py L549-606) | **Basic** | Tier2 直接拼接未重排，vault_notes 被丢弃 |
| 时间衰减 (nodes.py L380-438) | **Basic** | 仅应用于 Graphiti，decay_factor=0.05 未经验证 |
| fusion/ 模块 | **Basic-Intermediate（死代码）** | 更成熟但完全未使用 |
| 权重配置 | **Basic** | config.py 和 nodes.py 定义冲突 |

### 发现的具体 Bug

1. **P0: langgraph.runtime ImportError** — nodes.py L39 导入不存在的模块
2. **P0: Reranking 完全禁用** — `_rerank_local()` 和 `_rerank_cohere()` 是 NO-OP stub
3. **P0: Quality gate 永远返回 "low"** — RRF 分数 ~0.016 对比阈值 0.7/0.5
4. **P0: Query rewrite 是假实现** — `f"请详细解释: {query}"`
5. **P1: Cascade 丢失 vault_notes** — Tier1 和 Tier2 都未包含
6. **P1: Weighted fusion 单结果源归零** — min=max 时 normalized score = 0.0
7. **P1: 权重冲突** — config.py graphiti=0.25 vs nodes.py graphiti=0.20

### 缺失的关键能力（vs 社区标准）

- 无 cross-encoder reranking（行业标准第二阶段）
- 无 cross-source score calibration（z-score/Platt scaling）
- 无 query-dependent fusion routing
- 无 source-weighted RRF
- 无评估管线（MRR/NDCG）

---

## 社区调研总结

### RAG 前沿算法调研

| 方案 | 核心创新 | 社区采用度 | 教育场景相关性 |
|------|---------|-----------|-------------|
| **RRF + Cross-encoder Reranker** | 两阶段：RRF 粗排 + cross-encoder 精排 | **生产标准** | 高 — 行业验证最成熟 |
| **CRAG (Corrective RAG)** | 质量评估 + 回退路由（通过/部分/失败） | **生产级** — LangGraph 参考实现 | 高 — 质量门控+回退搜索 |
| **Agentic RAG** | LLM 作为编排者，按 query 路由检索策略 | **生产标准** — 52% 企业已部署 | 很高 — 教育 query 复杂度差异大 |
| **GraphRAG** | 知识图谱 + 社区层级摘要 | **生产标准** — Microsoft 开源 | 很高 — 概念关系/前置知识 |
| **HF-RAG** | 层次化融合 + z-score 跨源标准化 | 研究级 | 高 — 解决异构分数不可比 |
| **RAG-Fusion (Multi-Query)** | 多 query 变体 + RRF | 增长中 | 中 — 2026.03 生产研究显示 reranking 后收益消失 |
| **RAPTOR** | 递归摘要树 | 增长中 | 中 — 适合稳定语料（教材） |
| **Self-RAG** | 自反省检索 | 增长中 | 低 — 需要微调模型 |

### 教育场景检索调研

**核心发现：教育检索的差异化不在融合复杂度，而在学习智能。**

| 验证方案 | 来源 | 效果 |
|---------|------|------|
| **KG-RAG（知识图谱增强检索）** | ICEIT 2025 论文 (n=76) | 成绩提升 35% (p<0.001) |
| **EDU-Graph RAG（mastery-aware）** | arXiv:2506.22303 | 基于掌握度向量个性化检索 |
| **LC-RAG（学习日志上下文化）** | arXiv:2505.17238 | 学习记录弥合语义鸿沟 |
| **Khoj AI（PKM 标杆）** | 生产系统 | bi-encoder + cross-encoder 两阶段标准 |
| **Duolingo** | 生产系统 | 关键洞察：内容选择由掌握度驱动，非搜索驱动 |

**关键结论：无生产教育系统使用 5-6 源 RRF fusion。社区验证的路径是 2-3 核心源 + cross-encoder reranker + 学习感知。**

### 时间衰减调研结论

- 时间衰减在教育场景**需要分类对待**：
  - ✅ 适合衰减：学习记录、对话历史、最近修改的笔记
  - ❌ 不应衰减：教材内容、概念定义、参考资料
- 推荐方案：**query-aware 时间衰减** — 判断查询是否时间敏感后决定是否应用

---

## 主题 1：实现真正的 Reranking

### 代码现状

| 维度 | 现状 | 评级 |
|------|------|------|
| 核心文件 | `src/agentic_rag/reranking.py` (824 行) | 需修复后复用 |
| 已有资产 | LocalReranker (L73-251), CohereReranker (L257-471), HybridReranker (L477-809) | 完整实现 |
| 当前模型 | `bge-reranker-base` | 需升级 |
| 管道接入 | `nodes.py` `_rerank_local()` 和 `_rerank_cohere()` 是 NO-OP stub | **致命问题** |
| 已知缺陷 | deprecated asyncio API、Cohere SDK v1（需升级 v2）、fallback 返回 score=0.5 | 需修复 |

### 确认方案

**升级模型 + 修复已知缺陷 + 接入管道：**

```
当前：nodes.py rerank_results → _rerank_local() → return results  (NO-OP)
  ↓ 修复为
目标：nodes.py rerank_results → reranking.py LocalReranker(bge-reranker-v2-m3) → 真实 cross-encoder 评分
```

核心改动：
1. **升级模型**：`bge-reranker-base` → `bge-reranker-v2-m3`（MIRACL 中文 69.32，~1.1GB VRAM）
2. **修复 nodes.py stub**：`_rerank_local()` 调用 `reranking.py` LocalReranker
3. **修复 deprecated API**：asyncio.get_event_loop() → asyncio.get_running_loop()
4. **FP16 推理**：1.88x 加速
5. **输出 0-1 分数**：供下游 quality gate 使用

**社区验证：** cross-encoder reranker 是行业标准第二阶段（Perplexity、Khoj AI、SurfSense 均使用）。bge-reranker-v2-m3 与 bge-m3 embedding 配对是最佳组合。

**用户确认状态：** ✅ 已确认

---

## 主题 2：替换假 Quality Gate

### 代码现状

| 维度 | 现状 | 评级 |
|------|------|------|
| nodes.py check_quality (L737+) | RRF 分数 (~0.016) 对比阈值 0.7/0.5 → **永远 "low"** | 需重写 |
| quality/quality_checker.py (L41-234) | 完整 4 维加权评分（weak_point 0.40 + relevance 0.30 + diversity 0.20 + sufficiency 0.10） | **可复用（死代码）** |
| quality_nodes/grade_documents.py (L42-94) | 正确包装 QualityChecker，返回详细 metrics | **可复用（死代码）** |
| routing/quality_router.py | 与 state_graph.py 中的 route_after_quality_check 重复 | 需统一 |

### 确认方案：CRAG 模式

**激活已有 quality_checker.py + 对齐 CRAG 质量门控模式：**

```
当前：check_quality → RRF 分数 vs 0.7 → 永远 "low" → 永远重写
  ↓ 修复为
目标：check_quality → reranker 分数(0-1) → CRAG 三路路由：
  - PASS (≥0.7)：高质量，直接给 LLM
  - PARTIAL (0.4-0.7)：部分相关，补充搜索
  - FAIL (<0.4)：不相关，LLM query rewrite → 重新检索
```

核心改动：
1. **分数来源修复**：使用 reranker 输出的 0-1 分数（而非 RRF 的 ~0.016 分数）
2. **激活 quality_checker.py**：将死代码 grade_documents.py 注册到 state_graph
3. **CRAG 三路路由**：替换现有的二元（high/low）判断
4. **统一 router**：消除 state_graph.py 和 quality_router.py 的重复

**社区验证：** CRAG 模式有 LangGraph 官方参考实现（DataCamp tutorial）。Higress-RAG (arXiv:2602.23374) 用 CRAG + dual hybrid retrieval 在企业数据集达到 90%+ recall。

**用户确认状态：** ✅ 已确认

---

## 主题 3：替换假 Query Rewrite

### 代码现状

| 维度 | 现状 | 评级 |
|------|------|------|
| state_graph.py rewrite_query (L148-190) | `f"请详细解释: {query}"` — **无 LLM 参与** | 需重写 |
| quality/query_rewriter.py (L30-244) | 完整 LLM 改写，2 层迭代策略 | **可复用（死代码）** |
| quality_nodes/rewrite_query.py (L42-116) | 真实 LLM 实现，调用 QueryRewriter | **可复用（死代码）** |

### 确认方案

**激活已有 query_rewriter.py，替换 state_graph.py 的假实现：**

```
当前：rewrite_query → f"请详细解释: {query}"  (字符串拼接)
  ↓ 修复为
目标：rewrite_query → quality_nodes/rewrite_query.py → QueryRewriter (LLM 真实改写)
```

核心改动：
1. **替换 state_graph.py 的 rewrite_query**：调用 quality_nodes/rewrite_query.py
2. **LLM 改写**：从不同角度重新措辞查询
3. **最多重试 2 次**：保持现有 max_rewrite 限制
4. **保留 rewrite_count 跟踪**：与现有 state 字段兼容

**用户确认状态：** ✅ 已确认

---

## 主题 4：统一重复实现（修订方案）

### 代码现状

| 维度 | 现状 | 评级 |
|------|------|------|
| nodes.py 内联融合 (L462-606) | 6 源 unweighted RRF，3 种策略（RRF/Weighted/Cascade） | Basic（活跃代码） |
| fusion/ 模块 (7 文件) | UnifiedResult dataclass, Z-score, StrategySelector, MRR evaluator | Basic-Intermediate（死代码） |
| 权重配置 | config.py 5 源 vs nodes.py 6 源，权重数值冲突 | 需统一 |

### 初始方案（已否决）

保留 nodes.py 6 源融合，吸收 fusion/ 模块优点，删除 fusion/ 死代码。

**否决原因：** 3 个并行调研 agent 一致结论 — 当前融合代码全面 Basic 级，无生产教育系统使用 5-6 源 RRF。6 源同等对待的设计浪费了异构数据源的潜力。

### 修订方案：6 独立源 → 3 逻辑组

**将 6 个独立并行搜索重组为 3 个逻辑组：**

```
当前：6 个独立源 → 6-way unweighted RRF → top 10
  ↓ 重构为
目标：3 个逻辑组 → 组内合并 → 3-way RRF → top 20-30 → reranker → top 5-10
```

| 逻辑组 | 包含源 | 组内合并方式 | 理由 |
|--------|-------|------------|------|
| **Group A: Dense Retrieval** | lancedb + textbook + multimodal | 同一分数空间，直接合并排序 | 都是 embedding 向量搜索 |
| **Group B: Graph Retrieval** | graphiti | 单源 | 知识图谱，独立检索机制 |
| **Group C: Personal Notes** | vault_notes + cross_canvas | 同一分数空间，直接合并排序 | 都是用户个人笔记 |

附加改动：
1. **3-way RRF**：3 个逻辑组之间用 RRF 融合（社区验证标准）
2. **query-aware 时间衰减**：只对时间敏感查询应用衰减
3. **统一权重到 config.py**：消除冲突
4. **删除 fusion/ 死代码模块**
5. **修复 cascade 丢失 vault_notes**
6. **修复 weighted fusion 单结果归零 bug**

**社区验证：** 2-3 源 hybrid search + RRF + cross-encoder reranker 是 Perplexity、Khoj AI、SurfSense 等产品验证的标准架构。HF-RAG (arXiv:2509.02837) 验证了 z-score 跨源标准化方案。

**用户确认状态：** ✅ 已确认

---

## 修订后的完整 Pipeline 流程

```
用户提问
  ↓
[检索阶段] 3 个逻辑组并行搜索
  Group A: Dense (lancedb + textbook + multimodal) → 组内合并
  Group B: Graph (graphiti) → 单源
  Group C: Personal (vault_notes + cross_canvas) → 组内合并
  ↓
[融合阶段] 3-way RRF fusion → top 20-30 candidates
  ↓
[重排序] bge-reranker-v2-m3 cross-encoder → top 5-10，输出 0-1 分数
  ↓
[质量检查] CRAG pattern (基于 reranker 分数):
  - PASS (≥0.7) → 直接给 LLM 生成答案
  - PARTIAL (0.4-0.7) → 补充搜索后给 LLM
  - FAIL (<0.4) → LLM query rewrite → 重新检索（最多 2 次）
  ↓
[生成答案] LLM 基于检索结果回答
```

---

## 实施路线图

### 实施批次

```
批次 1（P0 修复致命问题）──────────────────────────────────
  修复 langgraph.runtime + 激活 reranker + 激活 quality gate + 激活 query rewrite
  │  核心工作：接入已有模块（"装配"而非"开发"）
  │
批次 2（P1 架构升级）──────────────────────────────────────
  6源→3组重构 + score semantics 修复 + query-aware 时间衰减 + 统一配置
  │  核心工作：融合层重构
  │
批次 3（P2 清理优化）──────────────────────────────────────
  删除 fusion/ 死代码 + 修复小 bug + state_graph lazy init
     核心工作：代码清理
```

### 批次 1：修复致命问题

**目标：** 让 Pipeline 后处理链从"全假"变成"全真"

| # | 任务 | 文件 | 改动 |
|---|------|------|------|
| 1 | 修复 langgraph.runtime ImportError | nodes.py L39 | `Runtime[CanvasRAGConfig]` → `RunnableConfig` from langchain_core |
| 2 | 激活 Reranking | nodes.py `_rerank_local()` | stub → 调用 reranking.py LocalReranker |
| 3 | 升级 Reranker 模型 | reranking.py | bge-reranker-base → bge-reranker-v2-m3 |
| 4 | 激活 Quality Gate | state_graph.py | 注册 quality_nodes/grade_documents.py 替换 nodes.py check_quality |
| 5 | 修复 Score Semantics | quality gate | 使用 reranker 0-1 分数替代 RRF ~0.016 分数 |
| 6 | 激活 Query Rewrite | state_graph.py | 注册 quality_nodes/rewrite_query.py 替换假实现 |

- **关键发现：** 大部分功能代码已存在但未连接。核心工作是"装配"而非"开发"。
- **前置条件：** 无
- **预期效果：** Pipeline 从 0% 功能覆盖 → ~80% 功能覆盖

### 批次 2：架构升级

**目标：** 从 Basic 级升级到社区验证的成熟架构

| # | 任务 | 文件 | 改动 |
|---|------|------|------|
| 7 | 重构融合为 3 逻辑组 | nodes.py fuse_results | 6 独立源 → 3 组 + 组内合并 + 3-way RRF |
| 8 | query-aware 时间衰减 | nodes.py _apply_time_decay | 仅对时间敏感查询应用 |
| 9 | 统一权重配置 | config.py + nodes.py | 消除冲突，集中到 config.py |
| 10 | CRAG 三路路由 | state_graph.py route_after_quality_check | PASS/PARTIAL/FAIL 替代 high/low |

- **前置条件：** 批次 1 完成
- **预期效果：** 融合质量显著提升，检索结果与用户学习状态关联

### 批次 3：清理优化

**目标：** 消除技术债务

| # | 任务 | 文件 | 改动 |
|---|------|------|------|
| 11 | 删除 fusion/ 死代码 | fusion/ 整个目录 | 删除 7 个未使用文件 |
| 12 | 修复 cascade 丢失 vault_notes | nodes.py _fuse_cascade_multi_source | Tier1/Tier2 加入 vault_notes |
| 13 | 修复 weighted fusion 归零 bug | nodes.py _fuse_weighted_multi_source | 单结果源 normalized score 修复 |
| 14 | state_graph lazy init | state_graph.py | import-time compile → lazy initialization |

- **前置条件：** 批次 2 完成
- **预期效果：** 代码库清洁，消除冲突和死代码

---

## Decision-Review 审查项

### DR-S3-1: Reranking 激活 + 模型升级

- **决策内容：** 激活 reranking.py LocalReranker，升级 bge-reranker-base → bge-reranker-v2-m3
- **涉及模块：** nodes.py, reranking.py
- **审查维度：** 中文学术内容 reranking 质量、推理延迟（FP16）、VRAM 占用、与 bge-m3 embedding 的配合效果
- **验证状态：** PENDING

### DR-S3-2: CRAG Quality Gate 模式

- **决策内容：** 激活 quality_checker.py + CRAG 三路路由（PASS/PARTIAL/FAIL），使用 reranker 分数
- **涉及模块：** state_graph.py, quality_checker.py, quality_nodes/grade_documents.py
- **审查维度：** PASS/PARTIAL/FAIL 阈值 (0.7/0.4) 在真实数据上的表现、PARTIAL 路由的补充搜索策略有效性、与 LangGraph 状态机的集成
- **验证状态：** PENDING

### DR-S3-3: Query Rewrite 激活

- **决策内容：** 激活 query_rewriter.py LLM 改写替换字符串拼接
- **涉及模块：** state_graph.py, quality_nodes/rewrite_query.py, quality/query_rewriter.py
- **审查维度：** LLM 改写质量（中文学术查询）、改写后召回率变化、改写延迟、LLM 调用成本
- **验证状态：** PENDING

### DR-S3-4: 融合架构重构（6源→3组）

- **决策内容：** 6 独立源重组为 3 逻辑组（Dense/Graph/Personal），3-way RRF，删除 fusion/ 死代码
- **否决方案：** 保留 6 源 unweighted RRF
- **否决理由：** 代码审查评级 Basic + 无生产教育系统验证 + 社区标准是 2-3 源 + reranker
- **涉及模块：** nodes.py, fusion/ (删除), config.py
- **审查维度：** 3 组分组是否合理覆盖检索需求、组内合并的分数兼容性、3-way RRF vs weighted fusion 效果对比
- **验证状态：** PENDING

### DR-S3-5: Query-aware 时间衰减

- **决策内容：** 时间衰减从全量应用改为 query-aware（仅时间敏感查询应用）
- **否决方案：** 全量指数衰减 (decay_factor=0.05)
- **否决理由：** 教育内容大部分是"常青"内容（教材、定义），盲目衰减降低检索质量
- **涉及模块：** nodes.py _apply_time_decay
- **审查维度：** 时间敏感判断的准确率、衰减参数的合理性、对不同查询类型的 A/B 效果
- **验证状态：** PENDING

---

## Future（S4+ 学习智能升级）

以下能力在调研中被确认为教育场景高价值方向，但超出 S3 范围：

| 能力 | 社区验证 | 依赖 |
|------|---------|------|
| KG 概念关系检索（前置知识链） | KG-RAG 论文，成绩提升 35% | S3 完成 + Graphiti |
| FSRS 遗忘曲线集成检索 | Duolingo、Anki 验证 | S3 完成 + FSRS 模块激活 |
| Adaptive query routing（按复杂度） | Agentic RAG，52% 企业部署 | S3 完成 |
| RAPTOR 多层摘要索引 | ICLR 2024，QuALITY +20% | 适合教材语料 |

---

## 涉及文件清单

| 文件 | 批次 | 改动类型 |
|------|------|---------|
| `src/agentic_rag/nodes.py` | 1, 2, 3 | 修复 + 重构 |
| `src/agentic_rag/state_graph.py` | 1, 2, 3 | 修复 + 重构 |
| `src/agentic_rag/reranking.py` | 1 | 修复 + 升级 |
| `src/agentic_rag/config.py` | 2 | 统一配置 |
| `src/agentic_rag/quality/quality_checker.py` | 1 | 激活（现为死代码） |
| `src/agentic_rag/quality/query_rewriter.py` | 1 | 激活（现为死代码） |
| `src/agentic_rag/quality_nodes/grade_documents.py` | 1 | 激活（现为死代码） |
| `src/agentic_rag/quality_nodes/rewrite_query.py` | 1 | 激活（现为死代码） |
| `src/agentic_rag/routing/quality_router.py` | 2 | 统一 |
| `src/agentic_rag/fusion/` (整个目录) | 3 | **删除** |

---

## 参考资料

### RAG 前沿算法
- [CRAG: Corrective RAG (arXiv:2401.15884)](https://arxiv.org/abs/2401.15884) — 质量门控 + 回退路由
- [A-RAG: Scaling Agentic RAG (arXiv:2602.03442)](https://arxiv.org/abs/2602.03442) — QA 准确率提升 5-13%
- [Higress-RAG (arXiv:2602.23374)](https://arxiv.org/abs/2602.23374) — CRAG + dual hybrid, 90%+ recall
- [HF-RAG: Hierarchical Fusion (arXiv:2509.02837)](https://arxiv.org/abs/2509.02837) — z-score 跨源标准化
- [RAG-Fusion Production Study (arXiv:2603.02153)](https://arxiv.org/abs/2603.02153) — multi-query 收益被 reranking 抵消
- [Agentic RAG Survey (arXiv:2501.09136)](https://arxiv.org/abs/2501.09136) — 综述

### 教育场景检索
- [KG-RAG (arXiv:2311.17696)](https://arxiv.org/abs/2311.17696) — 知识图谱增强检索，成绩提升 35%
- [EDU-Graph RAG (arXiv:2506.22303)](https://arxiv.org/abs/2506.22303) — 学习路径推荐
- [LC-RAG (arXiv:2505.17238)](https://arxiv.org/abs/2505.17238) — 学习日志上下文化
- [KA-RAG Educational QA](https://www.mdpi.com/2076-3417/15/23/12547) — GraphRAG 教育问答

### 产品参考
- [Khoj AI (GitHub)](https://github.com/khoj-ai/khoj) — PKM AI 标杆，bi-encoder + cross-encoder
- [SurfSense (GitHub)](https://github.com/MODSetter/SurfSense) — 开源 NotebookLM 替代，RRF + reranker
- [Microsoft GraphRAG (GitHub)](https://github.com/microsoft/graphrag) — 知识图谱检索

### Reranking
- [bge-reranker-v2-m3](https://huggingface.co/BAAI/bge-reranker-v2-m3) — MIRACL 中文 69.32
- [Neural Rank Fusion Analysis](https://www.rohan-paul.com/p/neural-based-rank-fusion-for-multi)

### 时间衰减
- [Re3: Relevance & Recency Balance (arXiv:2509.01306)](https://arxiv.org/abs/2509.01306)
- [Content-Aware Spaced Repetition](https://www.giacomoran.com/blog/content-aware-sr/)
- [FSRS Algorithm (GitHub)](https://github.com/open-spaced-repetition/free-spaced-repetition-scheduler)

---

## 独立验证 Session 结果（2026-03-13）

> **验证 Session ID:** session-s3-acceptance-criteria-2026-03-12
> **角色:** 独立验证（非决策 session），对 5 项 Decision-Review 进行对抗性审查、社区调研、验收标准制定
> **状态:** ✅ 全部完成

### 验证总览

| DR | 主题 | 代码评级 | AC 数量 | 状态 | 阻塞性发现 |
|----|------|---------|---------|------|-----------|
| DR-S3-1 | Reranker + CRAG Quality Gate | 需修复 | 12 | READY-FOR-IMPLEMENTATION | 无 |
| DR-S3-2 | CRAG 三路路由 | 需修复 | 8 | PENDING | PARTIAL 路径为全新开发 |
| DR-S3-3 | Query Rewrite 激活 | 需修复 | 12 | PENDING | 5 个 bug 需先修复 |
| DR-S3-4 | Fusion 6→3 Groups | 需修复 | 10 | PENDING | ⚠️ 组-源映射不匹配 |
| DR-S3-5 | Query-aware 时间衰减 | 需修复 | 10 | PENDING | 半衰期 13.86 天破坏教育内容 |

**总验收标准：52 项**

### DR-S3-1 验收标准（12 项）

| # | AC | 通过条件 |
|---|-----|---------|
| 1 | Reranker 真实调用 | `_rerank_local()` 调用 `CrossEncoder.predict()`，非 `return results` |
| 2 | 模型可配置 | 模型名从 config 读取，默认 bge-reranker-v2-m3，支持运行时 API 切换 |
| 3 | Sigmoid 归一化 | `predict()` 输出经 sigmoid → [0,1]，单元测试验证 |
| 4 | Batch 推理 | 支持 N 个文档批量推理，非逐个调用 |
| 5 | FP16 推理 | 模型加载 `torch_dtype=torch.float16`，VRAM < 2GB |
| 6 | 懒加载 | 首次调用时加载模型，非 import 时 |
| 7 | 降级策略 | 模型加载失败时降级为原始分数排序 + 日志警告 |
| 8 | 延迟 SLA | 50 文档 reranking < 500ms (FP16 GPU) |
| 9 | 分数传递 | reranker 分数写入 `metadata["reranker_score"]` 供 quality gate 使用 |
| 10 | 指令感知能力预留 | 接口支持传入 `instruction` 参数（可选，为未来指令感知 reranker 预留） |
| 11 | 日志可观测性 | 记录 reranking 前后排序变化、延迟 |
| 12 | DeepEval ContextualPrecision | 评估 reranker 质量的专用指标，需集成到评估流程 |

**代码审查发现：**
- P0: `CrossEncoder.predict()` 返回 raw logits（范围 [-∞,+∞]），未经 sigmoid 归一化
- P1: 已弃用 asyncio API、Cohere 降级返回 score=0.5 掩盖失败
- P2: 无 FP16 支持、eager loading

### DR-S3-2 验收标准（8 项）

| # | AC | 通过条件 |
|---|-----|---------|
| 1 | 三路路由 | `route_after_quality_check` 返回 "pass"/"partial"/"fail" 三种值 |
| 2 | 阈值可配置 | PASS≥0.7 / PARTIAL≥0.4 从 config 读取，非硬编码 |
| 3 | 分数来源 | 路由基于 reranker sigmoid 分数（非 RRF 分数） |
| 4 | PARTIAL 补充检索 | PARTIAL 路径触发 top-K 保留 + 补充检索（扩大召回） |
| 5 | FAIL 路由 | FAIL 路径触发 query rewrite → 重新检索 |
| 6 | 最大重试 | FAIL→rewrite→re-retrieve 最多 2 次迭代 |
| 7 | 状态传递 | `quality_status` 字段写入 LangGraph State |
| 8 | LangGraph 集成 | 路由函数注册为 conditional_edge，正确连接 3 个目标节点 |

**代码审查发现：**
- 当前只有二路路由（low vs not-low），PARTIAL 路径完全缺失
- PARTIAL 路径是全新开发，非死代码激活

### DR-S3-3 验收标准（12 项）

| # | AC | 通过条件 |
|---|-----|---------|
| 1 | LLM 真实调用 | `rewrite_query` 调用 LLM API，非字符串拼接 |
| 2 | 正确节点注册 | `state_graph.py` 导入 `quality_nodes/rewrite_query.py`，非本地 mock |
| 3 | NoneType 修复 | L115 `.strip()` 前有 None 检查 |
| 4 | API 超时 | LLM 调用有 timeout 设置（≤30s） |
| 5 | 日志替换 | `print()` 替换为 `logging.logger` |
| 6 | 模型可配置 | 模型名从 config 读取，非硬编码 gpt-3.5-turbo |
| 7 | 降级策略 | LLM 失败时返回原始查询 + 日志 |
| 8 | Runtime 签名 | 函数签名 `(state, runtime)` 匹配 LangGraph Runtime API |
| 9 | 2 次迭代策略 | 改写最多 2 次迭代（第 1 次粗改，第 2 次精调） |
| 10 | 改写质量 | 改写后查询保留原始意图但扩展召回 |
| 11 | 中文支持 | 改写 prompt 支持中文学术查询 |
| 12 | 去重路由 | 死代码 `routing/quality_router.py` 删除或统一 |

**代码审查发现：**
- `query_rewriter.py` 有真实 LLM 实现但 5 个 bug
- `state_graph.py` 注册的是本地 mock（`f"请详细解释: {query}"`），不是真实模块
- `routing/quality_router.py` 与 `state_graph.py` 路由逻辑重复

### DR-S3-4 验收标准（10 项）

| # | AC | 通过条件 |
|---|-----|---------|
| 1 | 组配置正确 | 3 组定义，所有 6 源分配到恰好 1 组，无遗漏无重复 |
| 2 | 组内融合 | 每组内部先融合为单一排序列表 |
| 3 | 组间加权融合 | 3 组使用可配置权重合并，权重和=1.0 |
| 4 | 向后兼容 | 每个结果保留 `metadata["source"]` + `metadata["group"]` |
| 5 | 权重从 config 读取 | `group_weights` 定义在 config.py，非硬编码 |
| 6 | 空组处理 | 任意组为空不崩溃，空组贡献 weight=0 |
| 7 | 分数归一化 | 组间归一化，单结果组不归为 0.0 |
| 8 | 性能 | 分组融合额外延迟 ≤5ms |
| 9 | 跨组去重 | 相同文档跨组出现时去重（content-hash 或 doc_id 归一化） |
| 10 | 日志可观测性 | 每组结果数、权重、分数范围均有日志 |

**⚠️ 阻塞性发现：组-源映射不匹配**

S3 设计的分组：
- Dense: embedding + BM25 ← **BM25 不存在为独立检索源**
- Sparse: weak_points + Graphiti ← **weak_points 未接入搜索管道**
- Personal: FSRS + behavior ← **FSRS/behavior 未接入搜索管道**

实际可用的 6 个检索源：graphiti, lancedb, multimodal, textbook, cross_canvas, vault_notes

**建议现实映射（供实施 session 参考）：**
- 语义组 (Dense): lancedb + vault_notes — 同一 LanceDB 分数空间，可直接 concat+sort
- 知识组 (Knowledge): graphiti + textbook + cross_canvas — 结构化知识源
- 媒体组 (Media): multimodal — 独立搜索方式

**社区验证：** HF-RAG 论文 (ACM CIKM 2025) 验证了完全相同的分层融合模式（组内 RRF → z-score 标准化 → 跨组合并）。

**代码审查发现：**
- P0: config.py 定义 5 源权重（无 vault_notes），nodes.py 定义 6 源权重，运行时冲突
- P0: 组-源映射与实际代码不匹配
- P1: Cascade 策略丢弃 vault_notes、单结果源归零 bug、无跨源去重
- fusion/ 目录 ~1400 行 100% 死代码

### DR-S3-5 验收标准（10 项）

| # | AC | 通过条件 |
|---|-----|---------|
| 1 | 查询分类器 | 区分时间敏感查询 vs 知识性查询（LLM 或规则） |
| 2 | 知识性查询零衰减 | 知识性查询的结果不应用时间衰减 |
| 3 | 时间敏感查询衰减 | 时间敏感查询正常应用指数衰减 |
| 4 | 半衰期可配置 | 从 config 读取，默认 ≥30 天（非当前 13.86 天） |
| 5 | 深拷贝 | `copy.deepcopy(results)` 而非浅拷贝 |
| 6 | 负值保护 | 衰减后分数不低于 0.0 |
| 7 | 日期精度 | 使用小时级精度而非天级截断 |
| 8 | 异常不静默 | 异常记录到 logger.warning 而非 `except: pass` |
| 9 | 分类器准确率 | 在测试集上分类准确率 ≥85% |
| 10 | 扩展到 Graphiti 以外 | 衰减可选择性应用于任意检索源 |

**代码审查发现：**
- P0: decay_factor=0.05 → 半衰期 13.86 天，破坏教育内容（基础概念两周后被大幅降权）
- P1: 浅拷贝 bug、整数天截断、无负值保护
- P2: 异常静默吞掉（`except: pass`）

### 用户确认事项

- ✅ **模型不能绑死** — 所有模型选择必须可配置，支持从 dashboard UI 切换（Session D 范围）
- ✅ DR-S3-1 验收标准确认（含 3 项社区 deep explore 改善）
- ✅ DR-S3-2 验收标准确认
- ✅ DR-S3-3/4/5 并行审查确认

---

## Deep Explore 改善建议（2026-03-13）

> 独立验证 session 在完成 5 项 DR 审查后，对社区最新论文和生产实践进行的补充调研。

### 高优先级（建议实施 session 采纳）

| # | 改善方向 | 影响 DR | 来源 | 核心价值 |
|---|---------|---------|------|---------|
| H1 | 指令感知 Reranker | DR-S3-1 | Contextual AI Reranker v2, zerank-2 | 可替换升级，reranker 接受自然语言指令如"优先推荐适合学生水平的内容" |
| H2 | FSRS 遗忘曲线集成检索 | DR-S3-5 | CSEDU 2025 论文 (arXiv:2503.01859) | 激活已有死代码，个性化时间衰减取代一刀切衰减 |
| H3 | Langfuse + RAGAS 评估框架 | 全部 | Langfuse (MIT), RAGAS | 所有改动的验证前提，无参考答案评估 |
| H4 | 自适应查询复杂度路由 | DR-S3-2 | Adaptive RAG (NAACL 2024), Higress-RAG | 先判断问题难度再决定搜索策略，延迟↓35%，准确率↑8% |

**建议实施顺序：** H3 → H1 → H2 → H4

### 中优先级（v2 考虑）

| # | 改善方向 | 影响 DR | 来源 |
|---|---------|---------|------|
| M1 | 查询分解（复杂问题拆子问题） | DR-S3-3 | RQ-RAG (COLM 2024), CoT-RAG (EMNLP 2025) |
| M2 | 加权 RRF（组间差异化权重） | DR-S3-4 | Elasticsearch Weighted RRF, MMLF (NAACL 2025) |
| M3 | 双路查询扩展+融合 | DR-S3-3+4 | Exp4Fuse (ACL 2025), RAG-Fusion |
| M4 | 知识图谱前置知识链检索 | 跨领域 | EDU-GraphRAG, KG-RAG |

### 低优先级（未来考虑）

| # | 改善方向 | 原因 |
|---|---------|------|
| L1 | LLM Listwise Reranking | 延迟 4-6 秒，不适合实时 |
| L2 | Self-RAG 自我反思 | 复杂度高，CRAG 已覆盖核心场景 |
| L3 | ARES 评估框架 | 先用 RAGAS，后续升级 |
| L4 | 语义缓存 | 当前阶段过早优化 |

### 关键协同效应

1. **H1 + H2** → 指令感知 reranker + FSRS = reranker 指令可包含"学生对 X 掌握薄弱，提升 X 内容权重"
2. **H3 是前提** → 没有评估体系，所有改动效果好坏全靠感觉
3. **H4 + M1** → 难度路由 + 查询分解 = 简单问题快速回答，复杂问题深度搜索

---

## 补充参考资料（验证 session 调研）

### 指令感知 Reranking
- [Contextual AI Reranker v2](https://contextual.ai/blog/rerank-v2) — 开源 1B/2B/6B，支持自然语言指令
- [zerank-2](https://www.zeroentropy.dev/articles/zerank-2-advanced-instruction-following-multilingual-reranker) — 指令感知多语言 reranker

### 教育场景 RAG
- [Optimizing RAG for Spaced Repetition (CSEDU 2025)](https://arxiv.org/abs/2503.01859) — RAG + 间隔复习结合
- [Graph RAG for MOOCs](https://arxiv.org/abs/2505.10074) — MOOC 场景知识图谱检索

### 自适应路由
- [Adaptive RAG (NAACL 2024)](https://aclanthology.org/2024.naacl-long.389.pdf) — T5 复杂度分类器
- [Higress-RAG (Feb 2026)](https://arxiv.org/abs/2602.23374) — CRAG + 自适应路由生产验证

### 查询改写与融合
- [RQ-RAG (COLM 2024)](https://arxiv.org/abs/2404.00610) — 动态查询分解
- [CoT-RAG (EMNLP 2025)](https://aclanthology.org/2025.findings-emnlp.168.pdf) — 知识图谱 + 链式思考
- [Exp4Fuse (ACL 2025)](https://aclanthology.org/2025.findings-acl.9/) — 双路扩展融合
- [Elasticsearch Weighted RRF](https://www.elastic.co/search-labs/blog/weighted-reciprocal-rank-fusion-rrf)

### 评估框架
- [Langfuse RAG Observability](https://langfuse.com/blog/2025-10-28-rag-observability-and-evals) — MIT 开源可自托管
- [RAGAS Metrics](https://docs.ragas.io/en/latest/concepts/metrics/) — 无参考答案评估
- [ARES (NAACL 2024)](https://arxiv.org/abs/2311.09476) — 高精度 LM Judge 评估

### 分层融合
- [HF-RAG (ACM CIKM 2025)](https://arxiv.org/abs/2509.02837) — 分层融合 z-score 标准化
