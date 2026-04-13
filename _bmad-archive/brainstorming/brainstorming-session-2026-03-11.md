---
stepsCompleted: [1, 2, 3, 4]
inputDocuments: []
session_topic: 'S2 Retriever 修复 — 4个返回空的retriever根因分析 + 架构改进'
session_goals: '1. 确定每个retriever返回空的根因+修复方案 2. 设计整体retriever架构改进方向'
selected_approach: 'ai-recommended'
techniques_used: ['Five Whys', 'Morphological Analysis', 'Solution Matrix']
ideas_generated: ['T1-T19 + 3补充发现']
context_file: ''
session_active: false
workflow_completed: true
---

# Brainstorming Session Results

**Facilitator:** ROG
**Date:** 2026-03-11 ~ 2026-03-12

## Session Overview

**Topic:** S2 Retriever 修复 — 修复 4 个永远返回空的 retriever（graphiti/multimodal/textbook/cross_canvas）；消除 vault_notes 双重搜索；修复 search() 默认表

**Goals:**
1. 确定每个 retriever 返回空的根因 + 修复方案
2. 设计整体 retriever 架构改进方向

**关联 Issues:** #1, 2, 3, 4, 7, 8, 9, 10

### Context Guidance

_来自 Graphiti 的已知上下文：_
- pipeline post-retriever 处理链 largely fake（fake quality gate、无功能性 reranking）
- vault_notes 缺少 scope 过滤 + cascade 丢弃 bug
- Contextual Retrieval 完全未实现
- 全量 dump 15K+ chars 导致回答太泛
- S5 A3 新功能依赖于 S2 完成

### Session Setup

_Session 类型：技术问题诊断 + 架构设计_
_方法选择：AI-Recommended Techniques_
_执行技法：Five Whys → Morphological Analysis → Solution Matrix_

---

## Phase 1: Five Whys — 根因分析

### Graphiti Retriever（graphiti_client.py）

| 层 | Why | 发现 |
|----|-----|------|
| W1 | 为什么返回空？ | `search_nodes()` 总是返回 `[]` |
| W2 | 为什么返回 []？ | `_mcp_available` 永远是 `False` |
| W3 | 为什么是 False？ | `importlib.util.find_spec("mcp__graphiti_memory__list_memories")` 找不到模块 |
| W4 | 为什么找不到？ | 这是虚假模块名，MCP 工具不能通过 Python import 调用 |
| W5 | 根因 | **整个 GraphitiClient 基于错误的 MCP 调用假设，100% 非功能性** |

**修复方向：** 用 graphiti-core SDK 重写（已有 GraphitiTemporalClient 作为参考实现）

### Multimodal Retriever（multimodal_retriever.py）

| 层 | Why | 发现 |
|----|-----|------|
| W1 | 为什么返回空？ | `raw_results = []`（三重 fallback 全失败） |
| W2 | 为什么 fallback 全失败？ | 调用 `client.search_multimodal()` 和 `client.similarity_search()` — LanceDB 没有这些方法 |
| W3 | 为什么没有？ | 这些是虚构的 API，LanceDB 只有 `search()` |
| W4 | 为什么返回格式也错？ | 返回 `id/media_type/path` 而非 `doc_id/content/score` |
| W5 | 根因 | **调用不存在的 API + 返回不兼容的 schema + multimodal_content 表从未创建** |

**修复方向：** 改用 `lancedb_client.search(table="multimodal_content")` + 修正 SearchResult schema

### Textbook Retriever（textbook_retriever.py）

| 层 | Why | 发现 |
|----|-----|------|
| W1 | 为什么返回空？ | `textbooks` 表不存在 |
| W2 | 为什么表不存在？ | 没有创建逻辑 + `_get_associated_textbooks()` 返回 TODO `[]` |
| W3 | 为什么 db_path 不对？ | 硬编码 `~/.lancedb` 而非项目配置路径 |
| W5 | 根因 | **错误的 DB 路径 + 表从未创建 + 关联逻辑是 TODO** |

**修复方向：** 使用 `LANCEDB_CONFIG["db_path"]` + 在 indexing 流程中创建 textbooks 表

### Cross-Canvas Retriever（cross_canvas_retriever.py）

| 层 | Why | 发现 |
|----|-----|------|
| W1 | 为什么返回空？ | `find_related_canvases()` 返回 `[]` |
| W2 | 为什么返回 []？ | 函数体是 TODO stub |
| W3 | 降级后呢？ | 降级为全局 canvas_nodes 搜索，等于复制 LanceDB retriever |
| W5 | 根因 | **核心逻辑 find_related_canvases() 完全未实现，降级路径与 LanceDB retriever 重复** |

**修复方向：** 实现基于 Graphiti 知识图谱的 canvas 关联查询

### vault_notes 双重搜索

| 层 | Why | 发现 |
|----|-----|------|
| W1 | 为什么被搜索两次？ | 既有专属 `retrieve_vault_notes` 节点，又在 `DEFAULT_TABLES` 中 |
| W2 | `DEFAULT_TABLES` 是什么？ | `["canvas_explanations", "canvas_concepts", "canvas_nodes", "vault_notes"]` |
| W5 | 根因 | **vault_notes 同时出现在专属节点和 DEFAULT_TABLES 中** |

**修复方向：** 从 `DEFAULT_TABLES` 移除 `vault_notes`

---

## Phase 2: Morphological Analysis — 架构维度拆解

### 维度 × 选项矩阵

| 维度 | 选项 A | 选项 B | 选项 C |
|------|--------|--------|--------|
| **接口统一** | 统一 SearchResult TypedDict | 每个 retriever 自定义 schema | Adapter 模式转换 |
| **搜索策略** | 纯 vector search | Hybrid search（vector + FTS + RRF） | 多路独立 → 后融合 |
| **可靠性** | 无保护（当前） | Circuit Breaker 模式 | 降级返回缓存 |
| **调度策略** | 全量 dispatch（当前） | 规则分类器选择性 dispatch | ML 模型动态路由 |
| **融合算法** | 简单 RRF | 加权 RRF + 时间衰减 | Cascade（分层筛选） |
| **去重机制** | index-based doc_id（当前，有碰撞） | content-hash doc_id | 语义去重 |

---

## Phase 3: Solution Matrix — 方案评估与选型

### 最终选型结果

| 维度 | 选定方案 | 理由 |
|------|----------|------|
| 接口统一 | 统一 SearchResult TypedDict | 最简单、最可靠，所有 retriever 强制返回 `{doc_id, content, score, metadata}` |
| 搜索策略 | Hybrid search 激活 | 代码已 90% 实现，只需 FTS indexes + query_type 透传（~28 行改动） |
| 可靠性 | Circuit Breaker | 社区验证成熟模式，与 LangGraph Send() 完美适配 |
| 调度策略 | 规则分类器 MVP | fan_out_retrieval 已返回动态 List[Send]，天然支持条件 dispatch |
| 融合算法 | 保持 RRF + 修复 weighted/cascade bug | RRF 是学术界和工业界默认选择，k=60 |
| 去重机制 | content-hash doc_id | `f"{table}_{hashlib.md5(content[:200]).hexdigest()[:8]}"` 避免碰撞 |

---

## Deep Explore 成果（两轮社区/论文验证）

### 发现 1: Hybrid Search 已 90% 实现

- **代码现状：** `_search_internal()` 有完整 hybrid 分支，`_rrf_fuse()` 完全可用
- **缺失：** FTS index 只为 vault_notes 创建，其他表没有；`search_multiple_tables()` 不传 `query_type`
- **社区验证：** LanceDB 官方推荐 hybrid search，react_agent.py 已在生产使用
- **改动量：** ~28 行代码

### 发现 2: Circuit Breaker 与 LangGraph Send() 天然适配

- **代码现状：** `fan_out_retrieval` 返回 `List[Send]`，只需过滤掉 OPEN 状态的 retriever
- **社区验证：** Microsoft Resilience Patterns、Netflix Hystrix 广泛验证
- **改动量：** 新增 CircuitBreaker 类 + 修改 fan_out_retrieval 过滤逻辑

### 发现 3: Adaptive Source Selection 可做 MVP

- **代码现状：** `fan_out_retrieval` 已支持动态 dispatch，`strategy_selector.py` 有 CanvasOperation 映射
- **社区验证：** LlamaIndex RouterQueryEngine 同类模式
- **MVP 方案：** 关键词规则分类器（5 类查询 → 不同 retriever 组合）

### 发现 4: graphiti-core SDK 直接可用

- **代码现状：** `graphiti_temporal_client.py` 有完整参考实现（SDK 初始化、search、add_episode）
- **改动量：** 复制 GraphitiTemporalClient 的 SDK 连接模式，替换假 MCP 导入

### 发现 5: 接口不匹配是系统性问题

- **multimodal_retriever** 返回 `{id, media_type, path}` 而非 `{doc_id, content, score}`
- **check_quality** 硬访问 `r["score"]`，缺少 key 会 KeyError
- **state.py** 定义了 `add_dicts` reducer 但从未使用

### 发现 6 (CRITICAL): LanceDB FTS 不支持中文分词

- **风险：** Tantivy（LanceDB 内部 FTS 引擎）没有原生中文 tokenizer
- **影响：** T13 hybrid search 对中文查询无效（FTS 分支返回空或噪声）
- **社区验证：** jieba 是 Python 中文分词事实标准（GitHub 32k+ stars）
- **方案：** 索引时 jieba 预分词 → 空格拼接存入 FTS 字段；查询时同样预处理

### 发现 7: 需要 per-retriever 质量指标

- **问题：** 当前无法量化每个 retriever 的贡献度
- **社区验证：** BEIR benchmark、RAGAS 框架均强调 component-level evaluation
- **方案：** 在 T6（SearchResult 统一）中增加 `retriever_metrics` 记录

### 发现 8: content-hash 去重替代 index-based doc_id

- **问题：** 当前 `f"lancedb_{i}"` 导致跨表碰撞；`f"{source}_{rank}"` 同样不可靠
- **社区验证：** LlamaIndex content-hash docstore 模式
- **方案：** `doc_id = f"{table}_{hashlib.md5(content[:200]).hexdigest()[:8]}"`

---

## Idea Organization and Prioritization

### Theme 1: 根因修复 — 让每个 Retriever 真正工作

_核心目标：修复 4 个返回空的 retriever + 消除 vault_notes 双重搜索_

| Task | 描述 | 改动范围 | 优先级 |
|------|------|----------|--------|
| **T1** | Graphiti retriever → graphiti-core SDK 重写 | graphiti_client.py | P0 |
| **T2** | Multimodal retriever → 修复 API + schema + 创建表 | multimodal_retriever.py, lancedb_client.py | P0 |
| **T3** | Textbook retriever → 修复 db_path + 创建表 | textbook_retriever.py | P0 |
| **T4** | Cross-canvas retriever → 实现 find_related_canvases() | cross_canvas_retriever.py | P0 |
| **T5** | vault_notes 从 DEFAULT_TABLES 移除 | lancedb_client.py:112 | P0 |

### Theme 2: 搜索质量 — 从"能用"到"好用"

_核心目标：激活 hybrid search、修复融合算法 bug、解决中文分词问题_

| Task | 描述 | 改动范围 | 优先级 |
|------|------|----------|--------|
| **T12** | search() 默认表修复 | lancedb_client.py | P0 |
| **T13** | Hybrid search 激活（FTS indexes + query_type 透传） | lancedb_client.py (~28行) | P1 |
| **T14** | jieba 中文预分词（FTS 中文支持） | lancedb_client.py, pyproject.toml | P1 |
| **T15** | content-hash doc_id 替代 index-based（去重修复） | lancedb_client.py, nodes.py | P1 |
| **T16** | `_fuse_weighted_multi_source` 等分归零 bug | nodes.py:511-514 | P1 |
| **T17** | `_apply_time_decay` 时间戳永远 = now() 修复 | nodes.py:402-437 | P1 |

### Theme 3: 可靠性架构 — 优雅失败而非静默返空

_核心目标：retriever 出错时系统能感知、降级、恢复_

| Task | 描述 | 改动范围 | 优先级 |
|------|------|----------|--------|
| **T6** | SearchResult 接口统一 + per-retriever metrics | state.py, 所有 retriever | P0 |
| **T7** | Circuit Breaker 模式（CLOSED→OPEN→HALF_OPEN） | 新文件 + state_graph.py | P1 |
| **T8** | RetryPolicy 修复（当前异常被 catch，retry 无效） | nodes.py, state_graph.py | P2 |

### Theme 4: 智能调度 — 按需查询而非全量 Dispatch

_核心目标：根据查询类型选择性调用 retriever_

| Task | 描述 | 改动范围 | 优先级 |
|------|------|----------|--------|
| **T9** | 规则分类器 MVP（5 类查询 → retriever 组合） | state_graph.py:fan_out_retrieval | P2 |
| **T10** | rewrite_query 修复（prefix stacking bug） | state_graph.py:176 | P2 |
| **T11** | cascade fusion 加入 vault_notes | nodes.py:562-606 | P2 |

### Theme 5: 后续扩展

_核心目标：进一步提升检索质量的高级功能_

| Task | 描述 | 优先级 |
|------|------|--------|
| **T18** | Reranker 真实实现（Cohere / cross-encoder） | P3 |
| **T19** | Reranker 本地 fallback（cross-encoder 模型） | P3 |
| **未编号** | Multi-query RAG-Fusion | Post-MVP |
| **未编号** | 可学习融合权重（基于用户反馈） | Post-MVP |

### 突破性发现

- **Hybrid search 几乎免费获得** — 代码已 90% 实现，只需 ~28 行激活
- **graphiti-core SDK 零成本切换** — 项目已有依赖 + 参考实现
- **Adaptive Source Selection 天然适配** — fan_out_retrieval 已返回动态 List[Send]
- **中文 FTS 风险必须提前解决** — 不加 jieba 则 hybrid search 对中文查询无意义

---

## Prioritization Results

### Wave 1（MVP 基础 — 立即执行）

**目标：让所有 retriever 返回真实数据**

1. **T6** SearchResult 接口统一（所有后续任务的基础）
2. **T1** Graphiti retriever SDK 重写
3. **T2** Multimodal retriever 修复
4. **T3** Textbook retriever 修复
5. **T4** Cross-canvas retriever 实现
6. **T5** vault_notes 双重搜索消除
7. **T12** search() 默认表修复

### Wave 2（质量提升 — Wave 1 完成后）

**目标：搜索结果从"有"到"好"**

8. **T13** Hybrid search 激活
9. **T14** jieba 中文预分词
10. **T15** content-hash doc_id
11. **T16** weighted fusion 归零 bug 修复
12. **T17** time decay 时间戳修复

### Wave 3（架构增强 — Wave 2 完成后）

**目标：系统级可靠性与智能调度**

13. **T7** Circuit Breaker
14. **T8** RetryPolicy 修复
15. **T9** 规则分类器 MVP
16. **T10** rewrite_query 修复
17. **T11** cascade fusion 修复

### Post-MVP

18. **T18-T19** Reranker 实现
19. Multi-query RAG-Fusion
20. 可学习融合权重

---

## Action Plan — Wave 1 实施指南

### Step 1: T6 SearchResult 接口统一

- **文件：** `state.py`（修正 TypedDict）+ 所有 retriever
- **关键改动：**
  - 强制所有 retriever 返回 `{doc_id: str, content: str, score: float, metadata: dict}`
  - 为每个 retriever 添加 `source` 字段到 metadata
  - 添加 per-retriever metrics 记录（结果数、延迟、错误率）
- **验收标准：** 任意 retriever 的输出可直接传入 `fuse_results` 无 KeyError

### Step 2: T1 Graphiti Retriever SDK 重写

- **参考实现：** `graphiti_temporal_client.py:333-340`（SDK 初始化模式）
- **关键改动：**
  - 替换假 MCP import 为 `from graphiti_core import Graphiti`
  - 复用 Neo4j 连接配置（`bolt://localhost:7689`）
  - 实现 `search_nodes()` → `self._graphiti.search(query, num_results, group_ids)`
- **验收标准：** 对任意查询返回非空结果（前提：Neo4j 中有数据）

### Step 3: T2-T4 其他三个 Retriever 修复

- **T2 Multimodal：** 替换虚构 API 为 `lancedb_client.search(table="multimodal_content")`
- **T3 Textbook：** 修复 `db_path` → `LANCEDB_CONFIG["db_path"]`，创建 textbooks 表
- **T4 Cross-canvas：** 用 Graphiti SDK 实现 `find_related_canvases()`

### Step 4: T5 + T12 搜索配置修复

- **T5：** `DEFAULT_TABLES` 移除 `vault_notes`
- **T12：** `search()` 默认表对齐实际数据

---

## Session Summary and Insights

### Key Achievements

- 通过 Five Whys 精确定位了 4 个 retriever 返回空的根因（每个原因不同）
- 通过 Morphological Analysis 系统性拆解了 6 个架构维度的改进空间
- 通过 Solution Matrix 在每个维度选定了最成熟的方案
- 两轮 Deep Explore（5 并行 agent + 5 WebSearch）验证了所有方案的社区/论文基础
- 发现了 1 个关键风险（中文 FTS）并制定了缓解方案
- 产出 22 个任务（T1-T19 + 3 补充），按 4 个 Wave 排列

### Session Reflections

- **最大惊喜：** Hybrid search 代码已 90% 存在，只需 ~28 行激活
- **最大风险：** LanceDB/Tantivy 不支持中文分词 → 必须 jieba 预处理
- **架构洞察：** LangGraph Send() 模式天然支持 Circuit Breaker 和 Adaptive Source Selection
- **代码质量警示：** 4 个 retriever 中有 3 个完全是假实现（fake MCP import、虚构 API、TODO stub），验证了代码库的系统性质量问题

### Graphiti 记录汇总

本 session 共记录 16+ 条到 `canvas-dev` group，覆盖：
- `[Session-Start]` / `[Session-End]`
- `[Code-Review]` × 多个模块
- `[Decision]` + `[Decision-Review]`（全部 PENDING 状态待验证）
- `[Research]` 两轮 deep explore 发现
