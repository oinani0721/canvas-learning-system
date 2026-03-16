---
stepsCompleted: [1, 2, 3, 4]
inputDocuments: []
session_topic: 'A4 索引管道增量 + Context Enrichment + 触发时机 + 记忆系统交叉'
session_goals: '对 A4 四大任务块进行三方定向 deep explore（社区调研 + Graphiti 审计 + 代码对抗性审查），产出可执行的决策方案'
selected_approach: 'ai-recommended'
techniques_used: ['Deep Explore', 'Adversarial Code Review', 'Community/Paper Validation', 'Graphiti Knowledge Audit']
ideas_generated: ['4组决策 + 4组Decision-Review(PENDING)']
context_file: ''
session_active: false
workflow_completed: true
---

# A4 索引管道增量 — Brainstorming 档案

**Session:** S8-Brainstorming
**主题:** A4 索引管道增量 + Context Enrichment + 触发时机 + 记忆系统交叉
**方法:** 三方定向 Deep Explore（社区/论文调研 × Graphiti 知识审计 × 代码对抗性审查）
**日期:** 2026-03-13
**Agent 总数:** 15 个并行 agent（每方向 3 个 × 4 方向 + 首轮全局 3 个）

---

## 总览

| 方向 | 核心决策 | 代码改动量 | Decision-Review |
|------|---------|-----------|-----------------|
| 1. 增量索引去重 | merge_insert + 双 hash + 去除双触发 | ~55 行 / 3 文件 | PENDING |
| 2. Context Enrichment | 截断 + 去重复 + index/query time 分离 | 7 个低垂果实 | PENDING |
| 3. 触发时机 | changed+resolved 模式 + 2 层 debounce | 前端事件重构 | PENDING |
| 4. 记忆系统交叉 | 修 Bridge + 统一 FSRS + EventBus + 6 步路线 | P0-P2 ~200 行 | PENDING |

**总计发现 bug/问题:** 15 个 CRITICAL/HIGH 级

---

## 方向 1：增量索引去重

### 问题诊断

当前系统每次编辑笔记节点，通过 `_trigger_lancedb_index` 全量重建整个画布索引，且 `add_documents()` 使用 `table.add(data)` 纯 append 无去重，导致索引无限膨胀。

**完整调用链（5 个入口点）：**

```
[1] Canvas CRUD → CanvasService._trigger_lancedb_index() → 500ms debounce → index_canvas() → add_documents() → table.add() [纯APPEND]
[2] Frontend vault.on('modify') → 5s debounce → POST /index → index_canvas() → add_documents() → table.add() [纯APPEND]
[3] Frontend metadataCache.on('changed') → 3s dirty-set → POST /index/vault/incremental → index_single_file() → add_documents() → table.add() [纯APPEND]
[4] Manual vault rebuild → POST /index/vault → drop_table + recreate [全量重建]
[5] Startup recovery → JSONL pending → retry [同路径1]
```

### 代码审查发现

| # | 严重性 | 问题 | 位置 |
|---|--------|------|------|
| 1 | **CRITICAL** | `add_documents()` 纯 append 零去重 | `lancedb_client.py:1218` |
| 2 | **CRITICAL** | `index_canvas()` 无 delete-before-insert | `lancedb_client.py:300-403` |
| 3 | **CRITICAL** | `index_single_file()` 无 delete-before-insert | `lancedb_client.py:556-665` |
| 4 | **HIGH** | 前后端双触发（backend 500ms + frontend 5s 各自独立 append） | `main.ts:547` + `canvas_service.py:392` |
| 5 | **HIGH** | `metadata.py` 每次请求创建新 LanceDBClient（无 singleton） | `metadata.py:60-82` |
| 6 | **HIGH** | `index_single_file` 后 FTS 索引未重建（增量添加的文档 hybrid search 不可见） | `lancedb_client.py` |

### 可复用逻辑

- **LanceDBIndexService**（debounce + retry + JSONL 恢复）— 优秀
- **doc_id 生成**（确定性 ID）— 已有，只需用于去重
- **向量化 pipeline** — 正常工作

### 决策方案

**采用 LanceDB 原生 `merge_insert` API 替代纯 append：**

```python
table.merge_insert("doc_id") \
    .when_matched_update_all() \
    .when_not_matched_insert_all() \
    .when_not_matched_by_source_delete(f"canvas_file = '{path}'") \
    .execute(new_data)
```

**四步实施：**

| 优先级 | 改动 | 效果 |
|--------|------|------|
| P0 | `add_documents()` 改为 `merge_insert` | 解决索引膨胀根本问题 |
| P1 | chunk_id 改为位置稳定 ID（`file_path::heading`） | 支持内容变化检测 |
| P1 | 添加 `content_hash` 列（SHA256）+ embedding 前比对 | 减少 40%+ embedding 成本 |
| P2 | 去除前端 `.canvas` 的 `vault.on(modify)` 监听 | 消除双触发 |

**否决方案：** 引入 LlamaIndex/LangChain 依赖（LanceDB 原生 API 已足够）

**社区验证：** LlamaIndex IngestionPipeline（doc_id + content_hash 双轨检测）、LangChain IndexAPI（RecordManager 三种 cleanup 模式）、CocoIndex（LanceDB 官方推荐）

**注意事项：**
- `when_not_matched_by_source_delete` 必须加 filter 限定范围（否则误删全表）
- 软删除需定期 `table.optimize()` 回收空间
- `merge_insert` 在有索引表上可能失败（已知 Issue#2751）

---

## 方向 2：Context Enrichment

### 根因定位

15K+ 全量 dump 的 #1 根因是 **target_content 完全无截断**——`get_node_content()` 读取整个文件无 limit，FILE 节点可能 10K-50K+ 字符直接注入 `enriched_context`。

**字符量分析（典型 canvas）：**

| 来源 | 字符量 |
|------|--------|
| Target node（UNBOUNDED） | 3,000-50,000+ |
| Target node（decompose 端点重复拼接） | ×2 |
| Adjacent 1-hop（6 nodes × 300） | 1,800 |
| Textbook refs | 800 |
| Cross-canvas（5 × 300） | 1,500 |
| Graphiti memories（双重注入） | 1,000 + 800 |
| Wikilinks（3 resolved） | 1,500 |

### 代码审查发现

| # | 严重性 | 问题 | 位置 |
|---|--------|------|------|
| 1 | **CRITICAL** | Target node 内容完全无截断（根因） | `context_enrichment_service.py:46-126, 1207-1211` |
| 2 | **CRITICAL** | Target content 在 decompose 端点重复拼接（出现两次） | `agents.py:798, 901` |
| 3 | **CRITICAL** | Graphiti memories 双重注入（ContextEnrichmentService + AgentService 各查一次） | `context_enrichment_service.py:990-1018` + `agents.py:2195-2201` |
| 4 | **CRITICAL** | 颜色映射矛盾（同一文件内 1=Red vs 4=Red 两套） | `context_enrichment_service.py:476-483 vs 1255-1262` |
| 5 | **HIGH** | Adjacent nodes 无 `max_neighbors` 限制 | `_find_adjacent_nodes:1088-1174` |
| 6 | **HIGH** | 无全局 context 字符预算/硬上限 | 架构缺失 |
| 7 | **MEDIUM** | Textbook/Graphiti 搜索对 FILE 节点用空 text 字段（永远搜不到） | `context_enrichment_service.py:910, 998` |

### 社区调研关键发现

- **"Context cliff"**：约 2,500 tokens 后检索质量下降。当前 15K+ 远超最优范围。
- **确定性 heading path 前缀**（不需 LLM）可达 LLM 生成摘要 85-90% 效果，零成本零延迟。
- **Late Chunking**：维持先前决策不切换（需替换 embedding model，不兼容 bge-m3）。

### 决策方案

**五步修复 + 架构决策：**

| 优先级 | 改动 | 效果 |
|--------|------|------|
| P0 | Target content 加截断上限（2000 字） | 立即消除 15K+ 问题 |
| P0 | 修复 decompose 端点重复拼接 | 信息更精炼 |
| P0 | 去除 Graphiti memories 双重注入 | 消除冗余 |
| P1 | 添加确定性 heading path 前缀 | 每个片段知道"在书的哪一页" |
| P1 | 设全局字符预算（500-600 tokens） | 确保永远不超标 |

**架构决策：分离 index-time context（static，参与 embedding）和 query-time context（dynamic，不参与 embedding）。**
- Index-time：heading path 前缀
- Query-time：Graphiti memories、FSRS mastery 状态
- 好处：动态数据变化不触发 re-embedding

**附带 bug 修复：** 颜色映射反转、FILE 节点搜索修复、`max_neighbors=10`、五路 enrichment 冗余整合、删除死代码 `build_agent_prompt()`

---

## 方向 3：触发时机

### 当前问题

总延迟 5.5-7.5 秒（Obsidian 内部 2s + 前端 3-5s + 后端 0.5s），三层 debounce 存在冗余。

**完整触发流程（4 个入口）：**

```
[A] .canvas 修改 → vault.on('modify') → 5s debounce → POST /index
[B] .md 修改 → metadataCache.on('changed') → 3s dirty-set → POST /index/vault/incremental
[C] Backend CRUD → _trigger_lancedb_index → 500ms debounce → 直接索引
[D] 手动重索引 → CanvasInfoView → POST /index 或 /index/vault
```

### 代码审查发现

| # | 严重性 | 问题 | 位置 |
|---|--------|------|------|
| 1 | **CRITICAL** | 前后端双索引（frontend 5s + backend 500ms 各自独立触发同一 canvas） | `main.ts:547-554` + `canvas_service.py:392-416` |
| 2 | **HIGH** | SSEConnectionManager.broadcast() 是 stub（无法通知前端索引完成） | `notification_channels.py:370-396` |
| 3 | **HIGH** | `vaultIndexDebounceTimer` 未在 `onunload` 清理 | `main.ts` |
| 4 | **MEDIUM** | 前端无并发限制（20 个 canvas 同时编辑→20 个并行请求） | `main.ts:1805-1823` |
| 5 | **MEDIUM** | 前端触发的索引无错误恢复（静默丢失） | `main.ts:1805-1854` |

**离线场景：** 离线编辑后恢复→变更不会被索引（唯一恢复方式是手动重索引）

### 社区调研关键发现

- **metadataCache 最佳模式：** `changed` → dirty set 收集 + `resolved` → flush（300ms safety debounce）
- **.canvas 文件不触发 metadataCache 事件**（GitHub Issue#156 确认），必须用 `vault.on('modify')`
- **Obsidian 内部 ~2s requestSave debounce** 是天然防抖，在此之上再加 3-5s 导致总延迟过长
- **成熟插件（Omnisearch、Smart Connections、Copilot）均不做激进实时索引**

### 决策方案

**推荐 2 层 debounce 替代当前 3 层：**

```
现在：Obsidian 2s + 前端 3-5s + 后端 0.5s = 5.5-7.5s
改成：Obsidian 2s（天然）+ resolved 300ms safety = ~2.3s
```

| 改动 | 效果 |
|------|------|
| .md 文件改用 `changed→dirtySet + resolved→flush + 300ms safety` | 延迟从 7s 降到 ~2.3s |
| .canvas 保持 `vault.on('modify')` + 3s debounce | canvas 不触发 metadataCache |
| 前端请求后端直接处理（500ms debounce 仅保留给内部 CRUD） | 去掉冗余等待 |
| 单独监听 `vault.on('rename')` | 重命名后索引更新 |
| 清理 `vaultIndexDebounceTimer` 在 `onunload` 中 | 修复泄漏 |
| 通知方案：初期 HTTP response 直接返回，后续可复用已有 WebSocket | 用户可见索引状态 |
| heading path 前缀在前端用 `metadataCache.getFileCache()` 计算 | 前端已有数据，不用后端解析 |

**否决：** Web Worker（不稳定 + 不需要）、激进实时索引

---

## 方向 4：记忆系统交叉

### 当前连接状态

```
LanceDB 索引 ←—[零连接]—→ FSRS/MasteryEngine
MemoryService →—[BROKEN: self._neo4j_client]—→ GraphitiBridge
ReviewService ←—[未调用]—→ AgentService 评分流程
BehaviorTracker ←—[死代码]—→ Backend
MasteryEngine(BKT+FSRS) ←—[WORKING]—→ Neo4j MasteryStore
```

### 代码审查发现

| # | 严重性 | 问题 | 位置 |
|---|--------|------|------|
| 1 | **CRITICAL** | `self._neo4j_client` 不存在（应为 `self.neo4j`）— Graphiti Bridge 永远不工作 | `memory_service.py:660` |
| 2 | **HIGH** | 双 FSRS 状态存储（ReviewService JSON vs MasteryEngine Neo4j 从不同步） | `review_service.py` vs `mastery_engine.py` |
| 3 | **HIGH** | ReviewService 未从评分流程调用（`/review/history` 缺失所有 agent 评分记录） | `agent_service.py` |
| 4 | **HIGH** | `generate_review_canvas()` 返回空 nodes[]（STUB） | `review_service.py:367-374` |
| 5 | **MEDIUM** | `/mastery/graphiti-sync` 依赖外部手动调用，无自动触发 | 架构缺失 |

### 可复用模块（高质量）

| 模块 | 质量 |
|------|------|
| MasteryEngine（BKT+FSRS hybrid） | **优秀** — 数学正确、算法完整 |
| FSRSManager | **优秀** — 正在被使用 |
| GraphitiBridgeService | **优秀** — 修好调用方即可 |
| MasteryStore（Neo4j 持久化） | **优秀** — 完全可用 |

### 社区调研关键发现

- **Math Academy FIRe（Fractional Implicit Repetition）** 是 SRS×KG 融合黄金标准——复习高级主题隐式传播 credit 给先修主题
- **CSEAL（KDD 2019）** 验证了 mastery state 影响内容排序的模式
- **生产级系统普遍采用 query-time injection**——与方向 2 的 index/query time 分离决策一致
- **Canvas 定位：** 比 RemNote 更智能的三系统融合，但不追求 Math Academy 全量深度

### 决策方案

**6 步集成路线 + 轻量 EventBus 架构：**

| 步骤 | 改动 | 代码量 |
|------|------|--------|
| **P0** | 修 `self._neo4j_client` → `self.neo4j` | **1 行** |
| **P1** | 统一 FSRS 状态（ReviewService 委托 MasteryEngine） + 评分流程补调 ReviewService | ~50 行 |
| **P2** | FSRS → RAG Reranking：`final_score = rrf_score * (1 + α * (1 - retrievability))` | ~100 行 |
| **P3** | 先修关系感知复习排序（利用 Graphiti 关系边） | ~150 行 |
| **P4** | 自动先修关系检测（ACE 方法：LLM + embedding 相似度） | 中等 |
| **P5** | FIRe 式隐式复习传播（需成熟图谱） | 较多 |

**架构核心：** 轻量 EventBus（~30 行 Python 回调列表）连接三系统

```
用户答题 → EventBus →
  ├→ FSRS Handler: 更新 retrievability/stability
  ├→ Graphiti Handler: 创建学习事件 episode
  └→ RAG Handler: 失效缓存（可选）
```

**否决：** 复杂消息队列（Kafka 等，个人系统不需要）

---

## 跨方向关联

四个方向形成完整的数据流链条：

```
用户编辑笔记
  → 方向 3：~2.3s 后自动触发（changed+resolved 模式）
  → 方向 1：只处理改动的部分（merge_insert + content hash）
  → 方向 2：附带精炼路径标签（heading path 前缀，非全文 dump）
  → 方向 4：搜索时优先展示弱点内容（FSRS reranking at query-time）
```

**关键架构决策贯穿所有方向：**
- **Index-time context**（static）：heading path 前缀，参与 embedding
- **Query-time context**（dynamic）：Graphiti memories、FSRS mastery 状态，不参与 embedding
- 动态数据变化不触发 re-embedding

---

## 全局 Bug 清单

| # | 严重性 | 模块 | 问题 | 修复难度 |
|---|--------|------|------|---------|
| 1 | CRITICAL | memory_service.py:660 | `self._neo4j_client` 不存在（Graphiti Bridge 断裂） | 1 行 |
| 2 | CRITICAL | lancedb_client.py:1218 | `add_documents()` 纯 append 零去重 | ~20 行 |
| 3 | CRITICAL | context_enrichment_service.py | Target content 完全无截断（15K+ 根因） | ~5 行 |
| 4 | CRITICAL | agents.py:798,901 | Target content 重复拼接 | ~10 行 |
| 5 | CRITICAL | context_enrichment_service.py | Graphiti memories 双重注入 | ~5 行 |
| 6 | CRITICAL | context_enrichment_service.py | 颜色映射矛盾（1=Red vs 4=Red） | ~10 行 |
| 7 | HIGH | main.ts + canvas_service.py | 前后端双触发 | ~3 行 |
| 8 | HIGH | notification_channels.py:370 | SSEConnectionManager.broadcast() 是 stub | 中等 |
| 9 | HIGH | review_service.py | 双 FSRS 状态存储（从不同步） | ~50 行 |
| 10 | HIGH | agent_service.py | ReviewService 未从评分流程调用 | ~10 行 |
| 11 | HIGH | review_service.py:367 | `generate_review_canvas()` 返回空 nodes[] | 中等 |
| 12 | HIGH | behavior_tracker.py | 从未被 backend 导入（死代码） | 设计决策 |
| 13 | HIGH | main.ts | `vaultIndexDebounceTimer` 未在 onunload 清理 | ~3 行 |
| 14 | HIGH | lancedb_client.py | FTS 索引未在增量 append 后重建 | ~8 行 |
| 15 | HIGH | metadata.py:60 | 每请求创建新 LanceDBClient（无 singleton） | ~10 行 |

---

## Decision-Review 汇总（全部 PENDING）

| DR | 决策 | 关键验证维度 | 状态 |
|----|------|------------|------|
| DR-S8-1 | 增量索引：merge_insert + 双 hash | merge_insert 在 FTS 索引表上的兼容性、filter 范围误删风险、大 vault 性能 | PENDING |
| DR-S8-2 | Context Enrichment：截断 + 分离 index/query time | heading path 前缀在无 heading 笔记上的表现、500-600 tokens 预算适用性、检索质量变化 | PENDING |
| DR-S8-3 | 触发时机：changed+resolved 模式 | resolved 事件快速连续编辑行为、300ms safety 是否足够、离线恢复策略 | PENDING |
| DR-S8-4 | 记忆系统交叉：6 步集成路线 + EventBus | Bridge 修复后事件到达验证、FSRS 统一后数据迁移、reranking alpha 参数、假设矛盾解决 | PENDING |

---

## Graphiti 记录汇总

本 session 共记录到 `canvas-dev` group：
- `[Session-Start]` S8-Brainstorming
- `[Research]` × 8（首轮全局 + 4 方向各 1 启动 + 3 审计结果）
- `[Research-Tech]` × 4（4 方向社区调研结果）
- `[Code-Review]` × 4（4 方向代码对抗性审查结果）
- `[Decision]` × 4（4 方向决策确认）
- `[Decision-Review]` × 4（4 方向待验证项）
- `[Session-End]` S8-Brainstorming A4 完成
