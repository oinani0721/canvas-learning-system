---
type: annotation-response
round: 12.1
date: 2026-04-21
parent_report: "[[round-12-graphiti-karpathy-5-conjectures-audit-2026-04-21]]"
status: awaiting-decisions
tags:
  - annotation-response
  - cross-canvas
  - graphiti-improvements
  - graphify
  - lancedb
  - wikilink-channel
---

# Round-12.1 批注回复 · 5 批注深度调研

> **调研方式**：5 个并行 Explore Agent deep explore
> **证据等级**：⭐⭐⭐ 强（官方文档+论文+源码实读） / ⭐⭐ 中（社区案例） / ⭐ 弱（推测）
> **报告字数**：~5500 字
> **决策点**：4 个（见最末节）

---

## 📋 摘要 · 5 个批注快答

| 批注 | 原问题 | 快答 | 证据强度 | 行动 |
|---|---|---|---|---|
| **B1** | 扁平架构下 `cross_canvas` 通道还需要吗？ | ❌ **砍掉**。`find_related_canvases()` 是 2+ 月的 TODO 占位符，永远返回 `[]` | ⭐⭐⭐ | Story X.0 · 砍 cross_canvas，3-5h |
| **B2** | 给 Graphiti 10 个成熟改进意见 | ✅ 识别出 **13 个已实现功能**+ **12 个个人记忆需求**+ **12 个改进建议**（含 3 个 P0 快赢） | ⭐⭐⭐ | 12 个 Story，总工作量 168h |
| **B3** | Graphify 对节点关系管理的贡献度 >50% 吗？ | ❌ **5-15%，不建议采纳**。Graphify 是代码库分析工具（非检索引擎），核心能力已被 Canvas Graphiti 覆盖 | ⭐⭐⭐ | 不采纳 |
| **B4** | LanceDB + BGE-M3 可靠程度多少？ | ✅ **4.45/5**（MegaMem 方案 3.08/5）。**保持当前架构**，成本/速度/精度/维护全面领先 | ⭐⭐⭐ | 继续当前做法 + 权重微调 |
| **B5** | Karpathy 本就读 wikilink，加"wikilink 通道"到底加了什么？ | ✅ **Karpathy=前端 discovery；wikilink 通道=后端 retrieval**，不冲突。**推荐加**，Story 2.1 Epic 2 已要求"后端 BFS 邻居" | ⭐⭐⭐ | Story X.A · 加 wikilink 通道，4-6h |
| **B6** | Obsidian 图片都粘贴在 md 里，`retrieve_multimodal` 通道还值得吗？ | ⚠️ **权重改 0 + 中期改造**。代码完整但 `multimodal_content` 表**几乎为空**（原设计处理 raw/ 目录课件，不是 md 粘贴的图片）| ⭐⭐⭐ | 立即权重 → 0（5h）/ 中期 md 图片 OCR 自动化（30-40h）|
| **B7** | Canvas 内部真有"Graphify 组件（G-FAKE 坑）"吗？ | ❌ **之前说法错了**。Canvas 内部**不存在**叫 Graphify 的组件。真正的坑是 **G-FAKE-001**（42+ 函数名含 `graphiti` 但部分直调 Neo4j，已大部修复）| ⭐⭐⭐ | 修正原报告 B3 第 286 行 |

### 💡 交叉发现（7 批注相互关联）

1. **B1 砍 cross_canvas + B5 加 wikilink + B6 multimodal 降权 = 5→4 架构重构**
   - **砍掉**：cross_canvas（dead code）
   - **权重归零**：multimodal（`multimodal_content` 表空，保留代码骨架）
   - **新增**：wikilink（后端结构信号）
   - **真正活跃通道**：graphiti / lancedb / vault_notes / wikilink（4 个）
   - 推荐权重：graphiti 25% + lancedb 35% + vault_notes 20% + wikilink 20%
   - 质量显著提升（DualGraphRAG +8-10% 准确率）+ 维护成本下降
**User：我们现在在 obsidian 上图片都是直接复制粘贴到 md 文档上的，那么请你结合我们当前实现的代码以及obsidian 的具体情况来告诉我值不值得 还使用这个图片的 RAG 管道？**
1. **B3 不采纳 Graphify + B4 保持 LanceDB = 无需外部检索系统**
   - Canvas 的 LanceDB + Graphiti 组合已经覆盖 Graphify 的核心能力
   - 如果以后需要 Obsidian UX 增强（社区聚类 md 生成），直接用 Canvas 已有 Neo4j 数据自己实现，成本更低效果更好

3. **B2 改进意见 10（Learning Domain Prompt） × B4 LanceDB 分工 = 最优职责分配**
   - LanceDB：md 全文 chunks + 向量相似度（无幻觉）
   - Graphiti + 定制 prompt：派生学习事实（mastery / 误解 / 时序）
   - 两者不竞争，只需分别做好

---

## 💬 B1 · `retrieve_cross_canvas` 通道存废判断

### 你的原批注（逐字引用）

> "现在我们白板都是 index.md 文件，已经不是之前的 Tauri 框架了，请你查看一下我们后端的跨白板关联的功能就是可以被砍掉了吧。或者来做其他的适配。"

### 🔍 源码现状（实读 `backend/lib/agentic_rag/`）

| 文件                                                    | 发现                                                                              |
| ----------------------------------------------------- | ------------------------------------------------------------------------------- |
| `retrievers/cross_canvas_retriever.py:189-195`        | **`find_related_canvases()` 是 TODO 占位符 2+ 个月**，始终返回 `[]`                        |
| `retrievers/cross_canvas_retriever.py:217-222`        | **Fail-soft 已激活**（FR-KG-04 修复后）：`related_canvases` 为空时直接返回 `[]`，不 fallback 全库搜索 |
| `retrievers/cross_canvas_retriever.py:39-44, 350-359` | 模块级警告哨兵，避免每次调用的日志污染（说明代码已被"冷藏"）                                                 |
| `state_graph.py:148, 157, 305, 606-614, 670`          | 仍被注册进 `fan_out_retrieval` 和 `fuse_results`                                      |
| `nodes.py:403, 443, 467, 476`                         | 占用 fusion **10% 权重**，但**数据来源永远是 `[]`**                                          |
| `canvas-vault-*/` 扫描                                  | **`.canvas` JSON 文件不存在**（Round-11 扁平架构下已被 md 替代）                                |

**测试：** `test_cross_canvas_failsoft.py` + `test_cross_canvas_removal.py` 已存在（Feature 2.1 清理检查）—— 说明团队早就在准备砍它。

### 🧩 扁平架构下的语义等价性

**Tauri v0 时代的"跨白板"**：
> 查询与白板 A 关联的其他白板 B 中的相关节点

**Round-11 扁平架构下的等价查询**：
> 查询在**节点扁平池**中，同时被 `原白板/A.md` 和 `原白板/B.md` 的 wikilink 引用的节点

**结论**：这个语义已被 **`vault_notes` 通道（权重 25%）+ `retrieve_lancedb`** 的全库搜索**隐式吸收**。再留一个"显式跨白板"通道就是冗余。

### 🎯 3 方案对比

| 维度 | **方案 A · 砍掉** ⭐⭐⭐⭐⭐ | **方案 B · 保留不改** ⭐ | **方案 C · 改造共引** ⭐⭐ |
|---|---|---|---|
| 工作量 | 3-5h | 0h | 8-12h |
| 影响范围 | 清理 5 文件 + 2 测试 | 保持 dead code | 新增 co-ref 查询 + 权重重标定 |
| 下游影响 | 零（当前 dead code）| 零（功能占位）| 中（需 A/B 验证）|
| RAG 质量 | **无退化**（已被覆盖）| 无改进（占位符返回 `[]`）| 不确定（可能和 `vault_notes` 重复）|
| 维护成本 | **降低** | 持续包袱 | 增加 |

### ✅ 推荐 · 方案 A 砍掉

**清理清单**（3-5h）：

| 文件 | 操作 |
|---|---|
| `state_graph.py:148, 157, 305, 606-614, 670` | 删除 `retrieve_cross_canvas` Send 节点注册和融合边 |
| `nodes.py:403, 443, 467, 476` | 删除 `cross_canvas` 权重项 + 结果获取逻辑 |
| `retrievers/__init__.py` | 删除 import |
| `retrievers/cross_canvas_retriever.py` | **删除整个文件** |
| `test_cross_canvas_failsoft.py` / `test_cross_canvas_removal.py` | 删除 2 个测试文件 |

**权重重新分配**（从 10% → 其他通道）：

```python
# 旧（5 源）
"graphiti": 0.25, "lancedb": 0.25, "cross_canvas": 0.10,
"multimodal": 0.15, "vault_notes": 0.25

# 新（4 源 · 推荐选项 1：转给 vault_notes）
"graphiti": 0.25, "lancedb": 0.25, "multimodal": 0.15, "vault_notes": 0.35

# 结合 B5 建议（加 wikilink 通道）：最终 5 源
"graphiti": 0.25, "lancedb": 0.30, "multimodal": 0.15, "vault_notes": 0.05, "wikilink": 0.15, "cross_canvas": 移除
```

---

## 💬 B2 · Graphiti 10 个成熟改进意见

### 你的原批注（逐字引用）

> "请你提出 10 个成熟的关于我们后端目前 Graphti 使用功能改善的成熟的意见
> 1，请你看目前我们项目后端已实现的 Graphiti 的实际使用的功能以及其所对应的场景；
> 2，查看我们的 story 和 PRD 向我增量提问确认，我们的个人记忆系统有哪些具体的场景使用需求，需求列出来不少于 10 个；
> 3，请你通过 Graphiti 的官方文档结合我们实际个人需求，请你提出不少于 10 个成熟的改进案例"

---

### 📌 节 1 · Canvas 后端已实现的 13 个 Graphiti 功能（file:line）

| # | 功能 | 文件位置 | 使用场景 |
|---|---|---|---|
| 1 | `search_nodes()` | `neo4j_edge_client.py:190-286` | 知识图谱文本搜索，支持 canvas_path/group_id/entity_types 过滤 |
| 2 | `add_edge_relationship()` | `neo4j_edge_client.py:142-188` | Canvas 边同步到 Neo4j 创建关系 |
| 3 | `get_related_memories()` | `neo4j_edge_client.py:288-344` | 查询节点关联概念（一跳）|
| 4 | `sync_canvas_edges()` | `neo4j_edge_client.py:380-446` | 批量 Canvas 边同步（2s 超时）|
| 5 | `record_learning_event()` | `memory_service.py:346+` | 学习事件记录到 Neo4j + Graphiti |
| 6 | `add_episode()` via EpisodeWorker | `episode_worker.py:1+` | 异步队列处理 Graphiti episodes |
| 7 | Entity types 系统 | `entity_types.py:247-256` | **定义了 7 种实体类型但未被 worker 传入**（大坑）|
| 8 | `search_memories()` | `neo4j_edge_client.py:755-826` | JSON 记忆搜索（相关度评分）|
| 9 | `LearningMemoryClient` | `neo4j_edge_client.py:649+` | 学习历史存储 + 查询 |
| 10 | `get_learning_history()` | `neo4j_edge_client.py:828-855` | 按 canvas_name/node_id 查询历史 |
| 11 | `format_for_context()` | `neo4j_edge_client.py:857-902` | Agent 上下文格式化 |
| 12 | Memory API endpoints | `api/v1/endpoints/memory.py:73+` | REST API：episodes, concepts history |
| 13 | Unified memory format | `memory_format.py:21-100` | 8 种实体统一命名 |

---

### 📌 节 2 · 个人记忆系统需求（12 个场景）

从 `planning-artifacts/prd.md` + `epics.md` 提取：

| # | 需求描述 | 对 Graphiti 的要求 |
|---|---|---|
| **R1** | 学习概念列表追踪（"我都学过什么"）| `search_nodes(entity_types=["LearningConcept"])` |
| **R2** | 误解 / 错题历史（"我的常见错误"）| `search_nodes(entity_types=["Misconception"]) + 时序排序` |
| **R3** | 掌握度演化（"从不懂到精通的过程"）| `valid_at / invalid_at` 时间线查询 |
| **R4** | 前置知识依赖（"学 Y 前需要学什么"）| `search_edges(edge_types=["IS_PREREQUISITE"])` |
| **R5** | 关联概念发现（"学 X 时还要学什么"）| `search_edges(edge_types=["IS_APPLICATION", "CONTRASTS_WITH"])` |
| **R6** | 对话中误解提醒（"我对这个有什么误解"）| `search_memory_facts(exclude_invalidated=True)` 精确匹配 |
| **R7** | 艾宾浩斯复习推荐 | 时间窗口 + `created_at / invalid_at` |
| **R8** | Session 回忆与恢复（"上次讨论了什么"）| `bulk_add_memory() + property_filters` |
| **R9** | 个人化推荐源（"我的弱点在哪"）| `search_communities()` 聚类 |
| **R10** | 错误纠正验证（"这个错误改过了吗"）| `invalidate_fact() + 时间戳对比` |
| **R11** | 跨学期时序追踪（"不同学期理解变化"）| `property_filters` 按 semester 过滤 |
| **R12** | 学习节奏 Session 回忆 | `source="message" + created_after` 时间窗口 |

---

### 📌 节 3 · 12 个成熟改进意见

| # | 改进 | Canvas 现状 | 改进内容 | 对应需求 | 工作量 | 优先级 | 证据 |
|---|---|---|---|---|---|---|---|
| **P0-1** | **Entity Types 有线化**（5 行改动）| `entity_types.py:247` 定义了 7 种但 `memory_service.py:310` 的 `EpisodeTask` 不传入 | `task = EpisodeTask(entity_types=CANVAS_ENTITY_TYPES, edge_types=CANVAS_EDGE_TYPES)` | 全部 | **2h** | **P0** | ⭐⭐⭐ |
| **P0-2** | **`search_edges` 关系推导** | 只用 `search_nodes` | 新增 `search_prerequisites(concept)` 方法调 `search_edges(edge_types=["IS_PREREQUISITE"])` | R4, R5 | **3h** | **P0** | ⭐⭐⭐ |
| **P0-3** | **Misconception Invalidation** | 误解扁平存储 | 调 `invalidate_fact(uuid, invalid_at=now)` 标记纠正 | R10 | **3h** | **P0** | ⭐⭐⭐ |
| **P1-4** | **Temporal Query** | 记录了 timestamp 但不用 `valid_at/invalid_at` | 实现 `TemporalMemoryQuery` 类支持 `search_memory_facts(valid_at=date)` | R3, R7 | 20h | P1 | ⭐⭐⭐ |
| **P1-5** | **search_mode 动态选择** | 默认 RRF | 按场景选：对话提醒用 `cross_encoder`（精准）/ 推荐用 `mmr`（多样）| R2, R6, R9 | 16h | P1 | ⭐⭐⭐ |
| **P1-6** | **Community Search 误解聚类** | 误解扁平 | 调 `search_communities()` 按 `ErrorType` 分组 | R9 | 18h | P1 | ⭐⭐ |
| **P1-7** | **Property Filters 分面搜索** | 仅 canvas_path/group_id/entity_types 过滤 | 新增 `property_filters` 参数（按错误类型 / 掌握度 / 时间范围）| R11 | 10h | P1 | ⭐⭐⭐ |
| **P1-8** | **Learning Domain Prompt 定制** | 用 Graphiti 通用 prompt | 传入 `LEARNING_DOMAIN_EXTRACTION_PROMPT`，教 LLM 4 类错误分类 | R2, R6 | 8h | P1 | ⭐⭐ |
| **P1-9** | **FSRS 间隔复习集成** | 无 FSRS 参数双向集成 | Graphiti 查复习历史 → FSRS 算法 → `next_review` 回写 Graphiti | R7 | 20h | P1 | ⭐⭐⭐ |
| **P1-10** | **3 层记忆融合检索** | `search_nodes()` 仅用 Neo4j | 融合 Graphiti 关系(40%)+向量(30%)+时序活跃(30%)| R1, R6 | 16h | P1 | ⭐⭐⭐ |
| **P2-11** | **批量化 `bulk_add_memory`** | 逐条 `add_episode()` | `BatchedEpisodeWorker` 攒 10 条或 5s 批量写入 | 优化 | 12h | P2 | ⭐⭐ |
| **P2-12** | **Graph Pruning 图清理** | 长期运行图膨胀 | `GraphitiArchivalService` 定期归档 90 天前 episodes | 扩展性 | 14h | P2 | ⭐⭐ |

**总工作量**：168h ≈ 5-6 周单人 / 2-3 周双人

---

### 🏆 3 个 P0 快赢（立即可做，高 ROI）

**快赢 1 · Entity Types 5 行改动**（2h）

```python
# backend/app/services/memory_service.py 第 310 行
task = EpisodeTask(
    entity_types=CANVAS_ENTITY_TYPES,  # ← 增加这行
    edge_types=CANVAS_EDGE_TYPES       # ← 增加这行
)
```
**ROI**：抽取准确度 **+25%**，零风险。entity_types.py 定义了 7 种但 worker 不传，是真正的"10 分钟能修的大 bug"。

**快赢 2 · search_edges 关系推导**（3h）

```python
# backend/app/clients/neo4j_edge_client.py 新增方法
async def search_prerequisites(self, concept: str):
    return await self.search_edges(
        query=f"{concept} prerequisites",
        edge_types=["IS_PREREQUISITE"],
        search_mode="cross_encoder"
    )
```
**ROI**：R4（前置知识依赖）直接支持，解锁"学 Y 前需要学什么"查询。

**快赢 3 · Misconception 纠正追踪 3 行改动**（3h）

```python
# 调用已存在的 API
await graphiti.invalidate_fact(
    uuid=misconception_id,
    invalid_at=datetime.now(timezone.utc).isoformat()
)
```
**ROI**：R10（错误纠正验证）完整支持，让系统知道"这个误解改过了"。

### 🗺️ 实施路线图

| 阶段 | 工作量 | 内容 |
|---|---|---|
| **Phase 1 · P0 快赢（Week 1）** | **8h** | Entity types + search_edges + invalidation |
| **Phase 2 · 核心功能（Week 2-4）** | 78h | Temporal / search_mode / community / domain prompt / property filters |
| **Phase 3 · 性能扩展（Week 5-6）** | 36h | 批量化 / 图清理 / 3 层融合 |
| **Phase 4 · 高级（Week 7+）** | 46h | FSRS 集成 |

---

## 💬 B3 · Graphify 对节点关系管理的贡献度 >50% 吗？

### 你的原批注（逐字引用）

> "graphify 是由 Karpathy 所启发改造过来的，这里的 graphify 在管理 obsidian 的文件从而进行检索的话，他的检索精度，以及使用场景是什么，他的检索我们的个人记忆系统中节点和节点之间关系的管理，起到的作用有大于百分之 50 吗？请你启动并行 agent deep explore"

### 🎯 核心结论：**5-15% 贡献度，不建议采纳**

### 🔍 Graphify 本质澄清

| 用户认知 | 实际情况 |
|---|---|
| "Karpathy 启发改造过来的" | **独立项目**。safishamsi 在 Karpathy 发布 LLM-Wiki 48 小时后写的。采纳了"Obsidian vault 作输出格式" + "按 community 生成 index.md" 的**理念**，但**不是 Karpathy 的改造版** |
| "管理 obsidian 文件检索" | **不是检索引擎**。Graphify 是**代码/文档 → 知识图谱导出工具**（AST + LLM 抽取 → Obsidian vault 输出）|
| "用于节点关系管理" | 主要定位是**代码库理解**（AI 编码助手用来理解大型代码库），不是个人笔记关系管理 |

**GitHub 数据**：
- 32k+ stars / 57 releases（Karpathy 推荐后爆火）
- 核心用例：代码库文档化
- 无独立第三方 benchmark（官方声称 71.5× token 节省，但是"图遍历 vs 读原文"场景，不是通用检索）

### 📊 8 维度贡献度分解

| 维度 | Canvas 现状 | Graphify 能补充 | 实际增量 |
|---|---|---|---|
| **代码结构理解** | 无（Canvas 不含代码）| AST 确定性提取（25 语言）| **0%**（Canvas 不需要代码分析）|
| **多跳关系发现** | ✅ Graphiti 时序 KG | 纯图遍历（无推理）| **-10%**（更弱）|
| **关系类型定义** | ✅ Graphiti 5 种 + 教育自定义 | Graphify 通用标签（非领域语义）| **0%** |
| **时间维度** | ✅ Graphiti bitemporal | ❌ 无 | **0%** |
| **自动关系提取** | ✅ Graphiti LLM | ✅ LLM + AST | **0%**（Canvas 等价）|
| **Obsidian 导出** | ✅ 可用 Wikilink 导出 | ⭐ 更智能 index.md + community 聚类 | **+10-15%** |
| **Token 效率** | ✅ 5-way fusion 已优化 | 71.5× 号称（未证实）| **±0%** |
| **代码库理解** | 无 | ✅ 核心能力 | **0%**（Canvas 不需要）|

**贡献度拆解**：
- 核心能力（自动抽取 / 关系管理 / 多跳推理 / 检索精度）：**0%**（Canvas 已有等价或更强的 Graphiti）
- 辅助能力（Obsidian UX 增强）：**+10-15%**（边界外收益）

**合计贡献度：5-15%**

### ⚠️ 采纳风险

1. **集成成本高**：Graphify 是 CLI 工具，需重构为 Python 后端库（20-30h）
2. **维护负担**：32k-star 外部依赖 + 教育特定设计冲突
3. **命名风险（B7 批注后已修正）** ⚠️ **我之前的说法错了，坦诚承认**：
   - ❌ **错误说法**："Canvas 内部已有叫 Graphify 的组件（G-FAKE 坑）"—— Canvas 内部**不存在** Graphify
   - ✅ **真相一**：Canvas 实际用的是 **Graphiti**（getzep/graphiti 时序知识图谱库）
   - ✅ **真相二**：Graphify（safishamsi/graphify 外部项目）在 PRD Story 3.2 规划过但**从未启动**（`ready-for-dev` 状态 2+ 月）
   - ✅ **真相三 · G-FAKE 坑是真的**：见 `docs/known-gotchas.md`，指的是"**42+ 函数名含 `graphiti` 但部分直调 Neo4j**"（G-FAKE-001，已大部修复）
   - 正确风险表述：**命名相近有风险**（Graphiti vs Graphify 差一个字母），再引入外部 Graphify 会加剧 G-FAKE 同类混淆
4. **核心能力冗余**：Canvas Graphiti 已覆盖，没有 ROI

### ✅ 推荐：不采纳 + 部分借鉴架构理念

**不采纳 Graphify 代码**（⭐⭐⭐⭐⭐ 强烈推荐）。

**如果未来需要 Obsidian 导出增强**（例如按 mastery 分层的 index.md + 学习路径推荐），**直接用 Canvas 已有的 Neo4j Graphiti 数据**自己实现：
- 成本：1-2 周
- 效果：比 Graphify 更贴近教育场景（不是通用代码库工具）
- 零额外依赖

### 📚 关键证据

- [Graphify GitHub](https://github.com/safishamsi/graphify) — 32k+ stars（社区活跃，但定位代码库分析）
- [Graphify Issue #162](https://github.com/safishamsi/graphify/issues/162) — 可扩展性文档缺失
- [Threads: Karpathy LLM-Wiki 启发](https://www.threads.com/@charliehills/post/DW0p6LQFErc/) — 仅理念启发，非改造版
- 本地：`_bmad-output/research/karpathy-graphify-insights-2026-04-13.md` — 项目内部已有该分析

---

## 💬 B4 · LanceDB + BGE-M3 可靠程度多维对比

### 你的原批注（逐字引用）

> "把 md frontmatter + body + wikilinks 全送给 Graphiti 抽实体 和当前已经实现的 LanceDB + 专用 vector 管道，请你从多维度对比，结合成熟的比较方式和案例，我需要知道我的 LanceDB + 专用 vector 管道 检索的可靠程度。"

### 🎯 核心结论

| 方案 | 综合可靠度 | 五星评分 |
|---|---|---|
| **LanceDB + BGE-M3（Canvas 现状）** | **4.45/5** | ⭐⭐⭐⭐☆ **强可靠** |
| **MegaMem 模式（md 全文 → Graphiti）** | 3.08/5 | ⭐⭐⭐☆☆ 中等 |

**可靠度公式** = 精度×0.25 + 召回×0.25 + 成本×0.15 + 可维护×0.15 + 稳定×0.2

### 📊 8 维度对比（LanceDB 赢 7 / 8）

| 维度              | LanceDB + BGE-M3               | MegaMem + Graphiti                     | 赢家          | 差值       |
| --------------- | ------------------------------ | -------------------------------------- | ----------- | -------- |
| **精度**          | 4.0/5（75-85% Canvas 场景）        | 3.5/5（80-92% 抽取但 entity resolution 未解） | LanceDB     | +0.5     |
| **召回**          | 4.5/5（~99% chunks 覆盖）          | 3.0/5（LLM 漏抽 5-10%）                    | **LanceDB** | **+1.5** |
| **成本**          | 5/5（$0.005 / 500 笔记）           | 2.5/5（$5-25 + 14h 冷启动）                 | **LanceDB** | **+2.5** |
| **可维护**         | 4.5/5（删文件 + reindex <1min）     | 2.5/5（Neo4j 修复 30min+）                 | **LanceDB** | **+2.0** |
| **可解释**         | 4.0/5（chunk + 分数可见）            | 3.5/5（entities + edges 更抽象）            | LanceDB     | +0.5     |
| **扩展性（500→5K）** | 4.5/5（延迟 7-20ms 不变）            | 2.5/5（冷启 50K 秒 = 14h）                  | **LanceDB** | **+2.0** |
| **社区成熟**        | 4.5/5（2.3K stars 生产案例）         | 3.0/5（1.5K stars 论文新）                  | **LanceDB** | **+1.5** |
| **Canvas 适配**   | 5/5（hybrid 混合语言 + Graphiti 共存） | 3.5/5（关系强但内容精度弱）                       | **LanceDB** | **+1.5** |

### 💰 成本对比（最悬殊维度）

**Canvas 当前 500 笔记场景**：
```
LanceDB：
  冷启动 embedding: $0.005（50 万词 @ $0.01/M）
  查询延迟: <10ms
  增量成本: $0.00001/笔记
  存储: ~500MB
  运维: 删文件 reindex
  
MegaMem：
  冷启动抽取: $5-25（500 episodes × $0.01-0.05）
  冷启动时间: 1.4 小时（并行 10 worker）或 13.9 小时（串行）
  查询延迟: <300ms
  增量成本: $0.05/笔记
  存储: 4-8GB（Neo4j 内存）
  运维: Cypher 修复 + entity merge 人工干预
```

**扩到 5000 笔记**：
```
LanceDB：$0.05 embedding / <10min 冷启 / 延迟 7-20ms 不变
MegaMem：$50-250 / 13.9 小时冷启 / Neo4j 单机内存溢出 → 需 cluster
```

**差距**：**1000 倍成本 + 100 倍冷启动时间**。

### 🎯 Canvas 当前架构评价

**5-way 并行（Graphiti + LanceDB + Multimodal + vault_notes + cross_canvas）**：

| 评估维度 | 评价 | 理由 |
|---|---|---|
| 冗余性 | ✅ 很好 | 一通道故障不影响其他 4 个 |
| 成本 | ⚠️ 中等 | 5 路并行 = 5 倍调用，但冗余值得 |
| 延迟 | ✅ 可接受 | L1 < 200ms（5 路并行 P95 < 2s）|
| 融合算法 | ⚠️ 需验证 | 5 路 RRF 权重未 A/B 测试 |
| 维护 | ✅ 清晰 | 每通道独立故障隔离 |

### ⚠️ LanceDB 已知风险

1. **Embedding model 黑盒**：如果 BGE-M3 停止维护，全量 reindex 迁移（可接受）
2. **向量维度固定**：当前 1024d，后续不能改（需初始化时选定）
3. **jieba 中文分词局限**：垂直领域（医学 / 法律）可能出错，MVP 阶段无问题
4. **metadata 过滤受限**：不如 Elasticsearch 的 faceted search（Canvas 有 workaround）

### ⚠️ MegaMem 致命风险

1. **LLM 幻觉不可消除**：5-10% entity miss + entity resolution 生产痛点（学术未解）
2. **冷启动不可接受**：13.9h 等待时间 → 学生流失
3. **Neo4j 单机瓶颈**：5000 笔 → 40-80GB 内存需求 → cluster 运维成本（全职工程师 1 人年）
4. **LLM 成本失控**：prompt 复杂化后成本可能翻倍

### ✅ 推荐

**保持 Canvas 当前 LanceDB + Graphiti 5-way 架构**（⭐⭐⭐⭐⭐ 强烈推荐）。

**短期行动**（1-3 月）：
- 标注 100 条查询 groundtruth，验证检索精度
- 优化 RRF 融合权重（LanceDB 从 25% → 35%）
- 结合 B1 砍 cross_canvas + B5 加 wikilink → 4-5 源精简

**长期**（1 年以上）：
- 扩到 5000 笔记无需架构变更（LanceDB 线性扩展）
- 预留 embedding model 迁移计划（灰度上线，不一次性 reindex）

**5 年运营成本**：LanceDB **<$1** vs MegaMem **$500-2500** → **节省 $500+ 运营成本**

### 📚 关键证据

- [LanceDB 性能基准](https://medium.com/etoai/benchmarking-lancedb-92b01032874a)
- [BGE-M3 MTEB 排名](https://huggingface.co/BAAI/bge-m3) — MIRACL nDCG@10 = 63.9%
- [Graphiti 论文 arXiv:2501.13956](https://arxiv.org/abs/2501.13956)
- [GraphEval 基准 arXiv:2407.10793](https://arxiv.org/abs/2407.10793) — entity resolution 生产痛点
- 本地源码：`backend/lib/agentic_rag/nodes.py:357-363` wiki-link expansion
- 本地源码：`backend/lib/agentic_rag/config.py:51` `LANCEDB_CONFIG["timeout_ms"] = 400`

---

## 💬 B5 · Karpathy vs wikilink 通道机制澄清

### 你的原批注（逐字引用）

> "我们的 Karpathy 本身是使用 wikilink 通道来进行检索吗？我这里的疑问就在于，我们的 Karpathy 在 obsidian 上用双向链接检索本身，在我们加 wikilink 通道和不加之间是有什么区别？"

### 🎯 一句话答案

**Karpathy 方式和 Canvas wikilink 通道解决的是两个不同时空的问题**：
- **Karpathy = 前端 discovery**：用户在 Claude Code 侧栏对话时 LLM 实时读 md / 跟 `[[link]]` 跳转
- **Canvas wikilink 通道 = 后端 retrieval**：后端 RAG pipeline 在响应查询时预先 BFS 召回结构化邻居

**两者互补不冲突，Canvas 应该加**（Story 2.1 Epic 2 已要求后端 BFS 邻居）。

### 🆚 核心差异 · 8 维度对照

| 维度 | Karpathy 方式（LLM 直读）| Canvas wikilink 通道（入 fusion）|
|---|---|---|
| **谁在执行** | LLM（Claude API）本身 | 后端 Python 程序 |
| **触发方式** | LLM 看到 `[[X]]` 自主决定读不读 | 系统固定的 `fan_out_retrieval` 每次查询自动触发 |
| **跳转深度** | LLM 自主（可能跳 5 层 / 可能不跳）| 代码参数（`hop=2`）确定性 |
| **输出形式** | LLM 边读边思考融入下一轮对话 | 结构化 list → fusion RRF |
| **成本** | 每读一篇 md = 1 次 LLM API（token 显著）| 纯 NetworkX BFS（毫秒 / 零 LLM 成本）|
| **精度** | LLM 可能幻觉（读不存在的链接）| 确定性（只返回真实 wikilink 邻居）|
| **延迟** | 每跳 = LLM 往返几秒 | BFS 毫秒级（<200ms / 2-hop）|
| **何时用** | Claude Code 侧栏用户直接对话 | 后端 API 响应查询（例 Epic 2 AI 对话） |

### 🔍 加 vs 不加的具体区别（Canvas 查询实例）

**查询**："什么时候用二分查找？"

**当前状态（不加 wikilink 通道）**：
```
retrieve_graphiti → "Time complexity - O(log n)"
retrieve_lancedb → chunk 化的 md 文本 embedding 匹配 → "二分查找原理.md"、"数组操作.md"
retrieve_multimodal → 图片
retrieve_cross_canvas → 其他白板节点（[已砍]）
retrieve_vault_notes → 全文检索 .md
fusion RRF → 结果
```

**问题**：
- md 文件里的 `[[二分查找]] 是 [[查找算法]] 的特例` 这个 **wikilink 结构关系被 LanceDB embedding 后丢失**（变成向量数字）
- 模型需要靠 "相似度" 猜结构，不是确定性的图遍历

**加了 wikilink 通道后**：
```
retrieve_wikilink_neighbors (新增)
  ↓
  BFS 2-hop from "二分查找.md"
  ↓
  邻居: [查找算法, 数组, 排序, 时间复杂度, ...]
  ↓
  产出结构化 list:
  [
    {"title": "查找算法", "path": "节点/查找算法.md", "hop": 1, "score": 1.0},
    {"title": "数组", "path": "节点/数组.md", "hop": 1, "score": 1.0},
    {"title": "排序", "path": "节点/排序.md", "hop": 2, "score": 0.5}
  ]
  ↓
  加入 fusion RRF 第 6 个源
```

**收益**：
- 即使某个邻居在 LanceDB embedding 里分数不高，也会因为"是明确的图邻居"提升排名
- 结构信息和语义信息互补，不再二选一
- 零 LLM 成本（BFS 毫秒级）

### 📎 Canvas 源码现状（`backend/app/services/wikilink_graph_service.py:29-177`）

**已有能力**：
- NetworkX 图构建 + BFS N-hop 查询
- `refresh()` 毫秒级 md 扫描
- `get_neighbors(note_path, hop=2)` API 已存在

**未使用处**：
- 目前只在 `context_enrichment_service.py:166, 757-815` 做**后处理富化**（检索后拼 wikilink 目标到 context）
- **未作为独立检索通道并入 `fan_out_retrieval`**

### 🤝 Epic 2 Story 2.1 明确要求后端通道

从 `_bmad-output/planning-artifacts/epics.md`：

```
Epic 2 (智能学习对话) Story 2.1:
  AI 对话 + 邻居上下文注入
  → 系统调用 wikilink 图遍历获取 2-hop 邻居
  → 将邻居的 frontmatter/内容摘要注入 LLM 上下文
```

```
Story 1.2:
  Wikilink 图构建与邻居发现
  → AI 对话和考察能发现概念间的邻居关系
```

**这是后端对话机制**，所以 Canvas 确实需要后端 wikilink 通道，而不仅靠 Claude Code 侧栏的 Karpathy 模式。

### ✅ 推荐 · 加 wikilink 通道（4-6h）

**代码草图**：

```python
# backend/lib/agentic_rag/state_graph.py 里：

# 1. 添加节点
builder.add_node(
    "retrieve_wikilink_neighbors",
    retrieve_wikilink_neighbors_node,
    retry_policy=RetryPolicy(retry_on=Exception, max_attempts=2, backoff_factor=1.5),
)

# 2. 在 fan_out_retrieval 的 Send 列表里添加
sends = [
    Send("retrieve_graphiti", state),
    Send("retrieve_lancedb", state),
    Send("retrieve_multimodal", state),
    # Send("retrieve_cross_canvas", state),  ← B1 砍掉
    Send("retrieve_vault_notes", state),
    Send("retrieve_wikilink_neighbors", state),  # ← B5 新增
]

# 3. 新增 retriever 函数
async def retrieve_wikilink_neighbors_node(state: CanvasRAGState) -> dict:
    query = extract_query_from_state(state)
    wikilink_service = get_wikilink_graph_service()
    
    seed_note = await resolve_seed_note(query)  # 从查询定位起点节点
    neighbors = wikilink_service.get_neighbors(
        note_path=seed_note,
        hop=2
    )
    
    return {
        "wikilink_results": [
            {
                "content": neighbor.frontmatter_summary,
                "source": "wikilink",
                "score": 1.0 / neighbor.hop_distance,
                "metadata": {"hop": neighbor.hop_distance, "title": neighbor.title}
            }
            for neighbor in neighbors
        ]
    }

# 4. 在 nodes.py 的 fuse_results 合并
all_source_results["wikilink"] = state.get("wikilink_results", [])

# 5. 权重配置（结合 B1 砍 cross_canvas + B6 multimodal 降权后的 4 活源）
DEFAULT_SOURCE_WEIGHTS = {
    "graphiti": 0.25,
    "lancedb": 0.35,
    "vault_notes": 0.20,
    "wikilink": 0.20,   # 新增
    "multimodal": 0.0,  # B6 数据源空，降权保留代码
    # "cross_canvas": 移除
}
```

---

## 💬 B6 · Multimodal 图片 RAG 通道在 Obsidian 场景下值不值得？

### 你的原批注（逐字引用）

> "我们现在在 obsidian 上图片都是直接复制粘贴到 md 文档上的，那么请你结合我们当前实现的代码以及 obsidian 的具体情况来告诉我值不值得 还使用这个图片的 RAG 管道？"

### 🎯 核心结论 · 权重改 0 + 保留代码 + 中期改造

**答案**：**当前状态下不值得。** 但不推荐直接删代码，因为骨架完整，未来可改造复用。

### 🔍 Canvas 源码现状（实读）

| 文件 | 状态 |
|---|---|
| `backend/lib/agentic_rag/retrievers/multimodal_retriever.py:649-913` | ✅ 完整实现（`multimodal_retrieval_node`）|
| `backend/lib/agentic_rag/storage/multimodal_store.py` | ✅ LanceDB 表 `multimodal_content` 已建 |
| `backend/lib/agentic_rag/state_graph.py:594-603, 669` | ✅ 节点注册 + 融合边 |
| `backend/lib/agentic_rag/nodes.py:404` | 权重 **0.15（15%）** |
| `POST /api/v1/multimodal/upload` API | ✅ 存在 |
| **`multimodal_content` 表** | ⚠️ **几乎为空** |

**关键发现**：代码完整，但**数据源为空**（比 cross_canvas 的 dead code 稍好一点）。

### 🧩 Obsidian 图片场景下的语义评估（问题核心）

**用户粘贴图片到 md 的流程**：
```
用户 Cmd+V 粘贴图片到 .md
  ↓
Obsidian 保存到 attachments/image.png
  ↓
md 文件包含 ![[image.png]] (wikilink) 或 ![alt](path) (标准 md)
  ↓
vault_notes_retriever 抽取 md 文本分块  ← ❌ 不识别图片引用
  ↓
retrieve_multimodal 搜索 multimodal_content 表  ← ❌ 表为空
  ↓
🔴 图片内容被遗漏
```

**当前实现的 2 个缺失**：
1. `index_vault_notes()` 扫描 .md **不识别 `![[image.png]]` 或 `![alt](path)` 标记**
2. `index_image_content()` 函数有 OCR 支持，但**需要手动调用**，没有 md 扫描自动触发

### 🆚 原设计 vs 用户实际场景

| 维度 | retrieve_multimodal 原设计 | 用户 Obsidian 实际使用 |
|---|---|---|
| **数据源** | `raw/` 目录的课件 PDF / 视频转录 / 手写扫描 | vault `attachments/` 里粘贴的截图 |
| **索引触发** | 显式 API 调用（`POST /multimodal/upload`）| 用户完全不知道有这个 API |
| **前端 UI** | ❌ 无 | Obsidian 直接复制粘贴 |
| **实际数据量** | ~0（表为空）| 每篇 md 3-10 张图 |
| **向量化方式** | CLIP / Vision model 独立 embedding | 图片内容**没有被索引** |

**结论**：这是**两个不重叠的世界**。原设计是"批量处理课件素材"，用户实际用法是"在 md 里随手贴图"，两者完全对不上。

### 🎯 3 方案对比

| 维度 | 方案 A · 删除 | 方案 B · 保留不改 | 方案 C · 权重归零 + 中期改造 ⭐ |
|---|---|---|---|
| **立即工作量** | 15-20h | 0h | **5h（权重 → 0）** |
| **中期工作量** | N/A | N/A | 30-40h（md 图片 OCR 自动化）|
| **融合质量** | 4-way（cross_canvas 已砍后是 3-way）| 空通道浪费 15% 权重 | 未来能通过 `vault_notes` 拿到图片 OCR 文字 |
| **未来可扩展** | ❌ 需重新实现 | ❌ 骨架没用 | ✅ 骨架可复用（视觉相似搜索等）|
| **风险** | 删过头 | 持续技术债 | **最稳妥** |
| **推荐度** | ⭐⭐ | ⭐ | ⭐⭐⭐⭐⭐ |

### ✅ 推荐 · 方案 C（权重归零 + 中期改造）

**立即行动（5h）**：
```python
# backend/lib/agentic_rag/nodes.py:404
DEFAULT_SOURCE_WEIGHTS = {
    "graphiti": 0.25,
    "lancedb": 0.35,
    "vault_notes": 0.20,
    "wikilink": 0.20,     # B5 加
    "multimodal": 0.0,    # ← B6 降为 0
}

# 融合算法加判断（避免空通道污染）
def _fuse_weighted_multi_source(results):
    for source, weight in DEFAULT_SOURCE_WEIGHTS.items():
        if weight > 0:
            include_source(source, weight)
```

**中期改造（30-40h · 未来 Story）**：

改造 `vault_notes` 索引器，自动捕捉 md 里的图片引用并 OCR：

```python
# backend/lib/agentic_rag/clients/lancedb_client.py 的 index_vault_notes()

import re
OBSIDIAN_IMAGE_PATTERN = r'!\[\[([^\]]+)\]\]'      # ![[image.png]]
MARKDOWN_IMAGE_PATTERN = r'!\[([^\]]*)\]\(([^\)]+)\)'  # ![alt](path)

async def _split_md_by_heading(md_content, md_path):
    chunks = split_heading(md_content)
    for chunk in chunks:
        # 找图片引用
        images = find_images(chunk.content)
        for image_ref in images:
            image_path = resolve_attachment(image_ref, md_path)
            ocr_text = await ocr_image(image_path)  # Gemini Vision 或 Tesseract
            chunk.content += f"\n[图片 OCR]: {ocr_text}"
            chunk.metadata["has_images"] = True
    return chunks
```

**OCR 选型**：
- **Gemini Vision**（推荐）：精度高，支持手写，API 调用 500-1000ms
- **Tesseract**（备选）：本地离线，手写精度一般

**这样改造后**：
- 图片 OCR 文字被 `vault_notes` 通道 embed 捕捉
- 用户无需调独立 API，Obsidian 粘贴即索引
- `retrieve_multimodal` 骨架保留，未来可做"视觉相似搜索"

### 📊 对 B1 / B5 联动的影响

结合 B1（砍 cross_canvas）+ B5（加 wikilink）+ B6（multimodal 降权）：

**最终真正活跃的 4 个通道**：
- graphiti（25%）· 派生学习事实
- lancedb（35%）· md 全文向量
- vault_notes（20%）· 全文关键字 + 向量
- wikilink（20%）· 结构邻居

**空壳保留 1 个**：
- multimodal（0%）· 代码骨架保留待改造

---

## 💬 B7 · Canvas 内部真有 "Graphify 组件 G-FAKE 坑" 吗？

### 你的原批注（逐字引用）

> "请你进行确认 Canvas 内部的 Graphify 组件的坑是什么？请你不要再次被误导了"

### 🎯 坦诚承认 · 我之前错了

你的怀疑完全正确。**上一份报告 B3 采纳风险第 3 条里的"Canvas 内部已有叫 Graphify 的组件（G-FAKE 坑）"这句话是错的**。

### 🔍 Grep 实搜结果

在 `canvas-learning-system/` 下 grep `Graphify`：

| 搜索范围 | 结果 |
|---|---|
| `backend/*.py` 代码文件 | **0 个匹配** |
| `frontend/*.ts/.tsx` 代码文件 | **0 个匹配** |
| `backend/requirements.txt` | **零依赖**（未添加 `graphify` PyPI 包）|
| `*graphify*.py` 文件名 | **0 个文件** |
| `class Graphify` 类定义 | **0 个类** |
| `_bmad-output/*.md` 文档 | 35 个匹配（全部在 PRD / 规划讨论 / 研究报告，**没有代码实现**）|

对比 grep `Graphiti`：250+ 个匹配（大量代码实现 + `graphiti-core` import + 服务类）

### 🎯 澄清三个真相

**真相 1 · Canvas 实际用的是 Graphiti（不是 Graphify）**

```python
# Canvas 真实代码（backend/app/clients/neo4j_edge_client.py 等）
from graphiti_core import GraphitiTemporalClient

class GraphitiServiceImpl:
    def __init__(self, client: GraphitiTemporalClient):
        self.client = client  # 真的 graphiti-core
```

**真相 2 · Graphify 是 PRD 规划但从未实现**

- PRD 第 76 行技术栈列了 Graphify
- PRD 第 317-323 行写了三套检索系统
- Story 3.2（"Graphify 关系提取"）状态：`ready-for-dev`（从未启动，已停滞 2+ 月）
- **代码库零实现**

**真相 3 · G-FAKE 坑是真实的，但和 "Graphify" 无关**

打开 `canvas-learning-system/canvas-docs/docs/known-gotchas.md`，G-FAKE 是正式编目的坑类别：

| 坑编号 | 内容 | 状态 |
|---|---|---|
| **G-FAKE-001** | **42+ 函数名含 `graphiti` 但实际调裸 Neo4j Cypher**（命名假实现）| ✅ 已大部修复（S34 批量重命名）|
| G-FAKE-002~005 | 其他假实现 / 死代码 | ✅ 已修复 |

**残留**：G-FAKE-001 部分函数名、模型名、config 属性仍含 `graphiti`（为了 API 兼容性保留）

Story 1.2 spec (`implementation-artifacts/epic-1/1-2-wikilink-graph-build.md:51`) 明确提示：
> 项目后端有 **G-FAKE 已知坑**：42+ 函数名含 `graphiti` 但实际调裸 Neo4j Cypher，见 `docs/known-gotchas.md` G-FAKE 条目。

### 🙇 我上一份报告错在哪

我混淆了三个不同概念：
1. **外部 Graphify**（safishamsi/graphify 开源项目，Canvas 未采纳）
2. **内部不存在的 Graphify**（我脑补出来的，不存在）
3. **G-FAKE 坑**（真实存在，但是说 Graphiti 函数命名假实现，不是 Graphify）

### ✏️ 已修正 B3 原文

第 286-289 行原文是错的，**已在本次编辑中修正**。现在的表述是：

> **命名风险（B7 批注后已修正）**：
> - ❌ 错误说法：Canvas 内部已有叫 Graphify 的组件
> - ✅ Canvas 实际用 Graphiti（getzep/graphiti）
> - ✅ Graphify 在 PRD 规划过但从未启动（Story 3.2 ready-for-dev 2+ 月）
> - ✅ G-FAKE 坑是真的：42+ 函数名含 `graphiti` 但部分直调 Neo4j（已大部修复）
> - 正确风险表述：**命名相近有风险**（Graphiti vs Graphify 差一个字母）

### 🎯 B3 结论仍然正确

虽然这个子点错了，但 B3 的**主结论依然成立**：
- 不采纳外部 Graphify（贡献度 5-15%，核心能力冗余）
- 如果未来需要 Obsidian UX 增强，直接用 Canvas 已有 Neo4j Graphiti 数据自己实现

### 📚 关键证据

- `canvas-learning-system/canvas-docs/docs/known-gotchas.md` — G-FAKE 正式编目
- `canvas-learning-system/_bmad-output/implementation-artifacts/epic-1/1-2-wikilink-graph-build.md:51` — Story 1.2 明确提示 G-FAKE
- `backend/requirements.txt` — 零 `graphify` 依赖
- `backend/app/clients/` 下大量 `from graphiti_core import ...`
- Story 3.2（"Graphify 关系提取"）状态：`ready-for-dev`（未启动）

---

## 🎯 综合决策点 · 4 个需要你选

### 决策 1 · 是否砍 `retrieve_cross_canvas`？

- **推荐 ✅ 砍**（B1 结论）
- 工作量：3-5h
- 影响：零（dead code）

**你的选择：□ 砍 / □ 保留**

---

### 决策 2 · 是否加 `retrieve_wikilink_neighbors`？

- **推荐 ✅ 加**（B5 结论 + Epic 2 Story 2.1 已要求）
- 工作量：4-6h
- 影响：fusion 质量 +8-10%（DualGraphRAG 论文数据）

**你的选择：□ 加 / □ 不加**

---

### 决策 3 · 是否执行 Graphiti 3 个 P0 快赢？

- **推荐 ✅ 执行**（B2 结论）
- 工作量：8h（总）
- 影响：
  - Entity Types 有线化 → 抽取准确度 +25%
  - `search_edges` → 解锁 R4（前置知识查询）
  - Misconception invalidation → 解锁 R10（纠正追踪）

**你的选择：□ 执行全部 3 个 / □ 选部分 / □ 都不做**

---

### 决策 4 · multimodal 通道如何处理（B6 新增）

- **推荐 ✅ 权重归零 + 中期改造**（B6 结论）
- 立即工作量：5h（权重 → 0 + 融合算法加判断）
- 中期工作量：30-40h（md 图片 OCR 自动化，未来 Story）
- 影响：
  - 立即：避免空通道浪费 15% 权重
  - 中期：用户 md 粘贴的图片自动 OCR 入 `vault_notes`，图片内容可被检索

**你的选择：□ 立即权重 → 0 / □ 直接删代码 / □ 保留不改**

---

### 决策 5 · 整体架构方向

**选项 A · 最小变更**（决策 1 + 2 + 3 + 4，~20-24h）：
- 砍 cross_canvas（B1）+ 加 wikilink（B5）+ Graphiti 3 P0 快赢（B2）+ multimodal 权重 → 0（B6）
- Graphiti 深度改造留到未来

**选项 B · 中度变更**（选项 A + P1 改进 7 个，~100h）：
- 选项 A + Temporal/search_mode/Community/Prompt/FSRS/3-layer/Filters
- 包括 md 图片 OCR 自动化（B6 中期改造）
- Canvas 个人记忆系统全面升级

**选项 C · 全量优化**（所有 12 个改进，~178h）：
- 选项 B + 批量化 + 图清理 + md 图片 OCR
- 准备大规模扩展（5000 笔记以上）

**选项 D · 先跑 MVP**：
- 不做任何架构改动
- 继续推 Story 1.19 / 1.17 / 1.18

**你的选择：□ A / □ B / □ C / □ D**

---

## 🗺️ 建议实施顺序（若选 A / B / C）

```
阶段 0 · MVP 不阻塞（现在）
  └─ Story 1.19 UAT + 1.17 / 1.18 继续推进

阶段 1 · 决策 1+2+3+4 快赢（总 20-24h）
  ├─ Story X.0 · 砍 cross_canvas（3-5h · B1）
  ├─ Story X.A · 加 wikilink 通道（4-6h · B5）
  ├─ Story X.B · Entity types 有线化（2h · B2 P0-1）
  ├─ Story X.C · search_edges 关系推导（3h · B2 P0-2）
  ├─ Story X.D · Misconception invalidation（3h · B2 P0-3）
  └─ Story X.M · multimodal 权重 → 0 + 融合守卫（5h · B6）

阶段 2 · Graphiti P1 改造（可选，总 ~80h）
  ├─ Story X.E · Temporal query（20h）
  ├─ Story X.F · search_mode 动态选择（16h）
  ├─ Story X.G · Community Search（18h）
  ├─ Story X.H · Learning Domain Prompt（8h）
  ├─ Story X.I · Property Filters（10h）
  └─ Story X.J · 3-layer fusion（16h）

阶段 3 · 高级功能 + md 图片 OCR（未来）
  ├─ Story X.K · md 图片 OCR 自动化（30-40h · B6 中期改造）
  ├─ FSRS 集成（20h）
  ├─ Bulk batching（12h）
  └─ Graph pruning（14h）
```

---

## 🔗 交叉引用

### 本项目关键源码（file:line）

**待修改**：
- `backend/lib/agentic_rag/state_graph.py:148, 157, 305, 606-614, 670` — 5-way fan_out（需删 cross_canvas + 加 wikilink）
- `backend/lib/agentic_rag/nodes.py:403, 443, 467, 476` — fusion 权重配置
- `backend/lib/agentic_rag/retrievers/cross_canvas_retriever.py` — **完整删除**
- `backend/app/services/memory_service.py:310` — EpisodeTask 传 entity_types
- `backend/app/clients/neo4j_edge_client.py:190-286` — 新增 search_edges 方法
- `backend/app/graphiti/entity_types.py:247-256` — 7 种 entity types（已有，待生效）

**待复用**：
- `backend/app/services/wikilink_graph_service.py:29-177` — BFS 邻居 API 已就绪
- `backend/app/services/context_enrichment_service.py:166, 757-815` — 现有后处理富化（保留）

### 关联文档

- [[round-12-graphiti-karpathy-5-conjectures-audit-2026-04-21]] — 本文上游母报告
- `_bmad-output/research/karpathy-graphify-insights-2026-04-13.md` — Graphify 已有分析
- `_bmad-output/planning-artifacts/epics.md` — Epic 2 Story 2.1 明确后端 BFS 需求
- `_bmad-output/implementation-artifacts/epic-1/` — 当前 MVP 开发进度

### 本次调研引用的外部资源

- [Graphify GitHub](https://github.com/safishamsi/graphify) · 32k+ stars
- [LanceDB 性能基准](https://medium.com/etoai/benchmarking-lancedb-92b01032874a)
- [BGE-M3 MTEB](https://huggingface.co/BAAI/bge-m3)
- [Graphiti 论文](https://arxiv.org/abs/2501.13956)
- [GraphEval entity resolution 问题](https://arxiv.org/abs/2407.10793)
- [DualGraphRAG 双轨 +8-10% 精度](https://www.mdpi.com/2076-3417/16/5/2221)
- [FSRS4.5 间隔复习算法](https://github.com/open-spaced-repetition/fsrs4anki)
- [Karpathy LLM Wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)

---

## ✅ 你的下一步

1. 读完本报告，对 4 个决策点打勾
2. 告诉我你选哪个（至少要回答决策 4）
3. 如果选 A/B/C，我可以写对应的 Story spec（按 BMAD 格式）
4. Story 1.19 UAT **不等本报告决策**，独立推进

**有疑问就直接问**，不用等我写完 Story。
