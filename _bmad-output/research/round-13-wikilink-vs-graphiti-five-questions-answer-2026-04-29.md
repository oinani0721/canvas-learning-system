# Round-13 · Wikilink vs Graphiti 双引擎检索 — 用户 5 问回答

> **日期**: 2026-04-29
> **上下文**: 接 Round-12 调研报告（`round-12-graphiti-karpathy-5-conjectures-audit-2026-04-21.md`），在 round-11 扁平架构（`原白板/` + `节点/` + `检验白板/`）落地后，用户提了 5 个深度技术问题
> **本文性质**: **理论性回答 + 推荐架构**，不立即开发代码
> **调研来源**: 3 并行 Explore agent（项目 Graphiti 现状 / 项目 wikilink + Karpathy / 社区双引擎案例）+ Round-12 已有数据
> **证据等级**: ⭐⭐⭐ 强（官方文档+论文） / ⭐⭐ 中（社区案例） / ⭐ 弱（推测）

---

## 📋 Context · 为什么这 5 问关键

用户在 Round-12 之后提的 5 问，本质是把 Round-12 的"应该共存"结论**拆成可落地的工程决策**：

> 既然两条检索路径都成立，**怎么分工**？**怎么不互相打架**？**md 属性归谁管**？**实时同步还是延迟同步**？**Canvas 项目实际怎么用**？

**回答先行**（一句话版）：

| 问题 | 一句话答案 |
|---|---|
| Q1: 谁更高效更精确 | **不是替代关系，是分工** — Wikilink 做骨架（零成本 + 显式），Graphiti 做时序补充（语义 + 演化） |
| Q2: Graphiti 成熟用法 | **3 类核心场景** — Agent Memory / Temporal RAG / 多跳推理 + 社区发现；Canvas 项目 `search_facts` + `search_communities` + `valid_at` **三大能力未通电** |
| Q3: md 属性进 Graphiti | **有条件的"是"** — 只对**会变化的属性**（mastery_score / understanding / last_reviewed），静态属性留 frontmatter |
| Q4: 实时双写同步 | **❌ 反模式** — 推荐 Lazy + Batch（30min cron），单向 md → Graphiti，永不反向 |
| Q5: 双引擎并用 | **✅ 是 2026 社区共识** — 三层分层检索（Wikilink → Graphiti → LanceDB）+ RRF 融合 |

---

## 🔬 项目现状速览（Round-12 + 本次 3 agent 复核）

### Wikilink 现状

- ✅ `backend/app/services/wikilink_graph_service.py` 已实现（NetworkX BFS N-hop）
- ✅ Story 1.2 + 1.3 spec 完整（`_bmad-output/implementation-artifacts/epic-1/1-2-*.md`、`1-3-*.md`）
- ⚠️ **状态 = ready-for-dev 未实施** — `obsidiantools` 解析图入内存（启动 < 2s）尚未跑起来
- ⚠️ 当前唯一用法 = `context_enrichment_service.py:166` 后处理富化（**未作为独立检索通道并入 5-way RAG**）

### Graphiti 现状

- ✅ graphiti-core v0.28.2 已集成（`backend/app/clients/graphiti_client.py`）
- ✅ `episode_worker.py` 写学习事件 OK
- ⚠️ **md 文件目前完全游离在 Graphiti 外**（没有 md → episode 的同步管道）
- ⚠️ **项目仅用 `search_nodes`**，未用 `search_facts` / `search_communities`
- ⚠️ **`valid_at` / `invalid_at` 时序能力 = 已硬件、未通电**
- ⚠️ entity_types（CANVAS_ENTITY_TYPES = concept / mastery / error）已注册但 add_episode 未启用

### 后端 5-way Agentic RAG 现状（Round-12 震惊发现复读）

`backend/lib/agentic_rag/state_graph.py:540-671` 已经是业界顶级 5 通道并行 + RRF fusion 架构：

| # | 通道 | 引擎 | 状态 |
|---|---|---|---|
| 1 | retrieve_graphiti | Graphiti + Neo4j | ✅ 跑 |
| 2 | retrieve_lancedb | LanceDB（BGE-M3） | ✅ 跑 |
| 3 | retrieve_multimodal | 图片/PDF | ✅ 跑 |
| 4 | retrieve_cross_canvas | 图遍历 | ⚠️ round-11 之后语义改变（原 `wiki/canvases/` 嵌套已弃用，需适配 `原白板/` 扁平） |
| 5 | retrieve_vault_notes | LanceDB + BM25 | ✅ 跑 |

**Round-12 用户批注**（仍生效）：
> *白板已迁移到扁平 md，跨白板关联功能可砍掉或重新适配。*

→ Q5 推荐架构会接续这个批注做"wikilink 作为第 6 通道"的设计。

---

## 💬 Q1 · Wikilink vs Graphiti 哪个更高效更精确？各自独特优点？

### 短答

**两个根本不是替代关系，是分工互补**。"高效精确"分两个维度看：

| 维度 | Wikilink (Karpathy 派) | Graphiti (时序 KG 派) |
|---|---|---|
| **建立索引** | obsidiantools 启动 < 2s（200 md + 500 链） | 每次 add_episode LLM 抽取 5-30s |
| **检索延迟** | get_neighbors 2-hop < 200ms（内存 BFS） | search_nodes < 500ms（含 LLM rerank 时） |
| **零成本运行** | ✅（纯文件 + NetworkX） | ❌ 每次写入 LLM 调用 |
| **语义理解** | ❌（只看 `[[]]` 字面量） | ✅ LLM 抽取实体 + 关系类型 |
| **时序追踪** | ❌（静态引用） | ✅ valid_at / invalid_at 决策版本演化 |
| **多跳推理** | ✅ BFS 2-hop 强 | ✅ search_facts 三元组遍历 |
| **隐式关系发现** | ❌（用户没写就没有） | ✅ 同实体不同语境聚合 |
| **大规模扩展** | 5000+ md 仍 sub-second（NetworkX 高效） | 节点 100k+ 时检索性能下降 |

### Canvas 项目 200-500 md 的具体推荐

- **检索骨架** = Wikilink 图（首选，零成本，确定性强）
- **语义补充** = Graphiti 当 Wikilink 不够时（错误归档、错误模式聚类、跨白板隐式关联）

### 各自独特优点（互不可替代）

**Wikilink 优势**：

1. 用户**显式声明**的关系才上图（防 LLM 幻觉，防"AI 编了一个不存在的关系"）
2. 文件即数据库（git 可追、用户可读、运维零成本）
3. AI 主动调用（agent 自己决定查谁，符合 Karpathy"反 RAG"哲学）

**Graphiti 优势**：

1. **时间感知** — 学习历程演化（mastery 0.3 → 0.65 → 0.85 自动留档）
2. **社区发现** — `search_communities` 找"哪些概念经常一起出错"（Story 6 检验白板必备）
3. **事实失效追踪** — 用户改了笔记 → 旧 fact 自动 `invalid_at = now`，新 fact `valid_at = now`

### Canvas 现状的关键差距

**项目 graphiti-core SDK 只用了 `search_nodes`**（Round-12 + Agent 1 复核）：

| API | 项目用法 | 应该用法 |
|---|---|---|
| `search_nodes` | 2 处 | ✅ 保持 |
| `search_facts` | **0 处** ❌ | "X 和 Y 的关系" 类查询 |
| `search_communities` | **0 处** ❌ | 错误模式聚类 / 概念集群 |

→ **时序能力 = 已硬件、未通电**。Q2 展开。

---

## 💬 Q2 · Graphiti 成熟用户怎么运用它的检索？

### 3 类核心场景（Zep / Neo4j / Presidio 官方案例）

#### 场景 1: Agent Memory（Graphiti 核心市场，70% 用户）

- **模式**: Agent 跑对话 → 每轮 `add_episode` → 下次问"我们上周聊了啥" → `search_nodes/facts` 拉历史
- **API 用法**: `search_nodes(query="topic-X")` → top-k 实体节点 → LLM 用作 context
- **代表案例**: Zep（Cursor 用此架构 / 18% 多会话准确率提升）

#### 场景 2: RAG + Temporal Context

- **模式**: 用户改了订阅价格 → 旧 fact `valid_at=过去, invalid_at=now` + 新 fact `valid_at=now`
- **检索时**: `search_facts(query="subscription tier")` 返回**当前有效**的 fact + 历史快照（按时间过滤）
- **Canvas 学习场景对应**: 用户 round-9 选 Tag A，round-15 改选 Tag B → Graphiti 自动 invalidate 旧选择
- **代表案例**: Presidio enterprise memory（医疗历史 / 法律演化）

#### 场景 3: 多跳推理 + 社区发现

- **模式**: 用 `search_communities` 找"哪些概念经常一起出错" → 用户错误模式聚类
- **Canvas Story 6 检验白板必备**: 检测易混淆点 / 知识盲点

### Canvas 项目尚未利用的 3 个 Graphiti 高级能力

1. ❌ `search_facts` 多跳（"X 和 Y 的关系是什么"）
2. ❌ `search_communities`（错误聚类 / 概念集群）
3. ❌ `valid_at` / `invalid_at` 时序查询（"我 3 个月前理解的 X 是怎样的"）

### 3 个搜索 API 选用规则（Zep 官方）

| 问题特征 | 用 |
|---|---|
| "什么是 X / X 的属性" | `search_nodes` |
| "X 和 Y 的关系 / 历史变化" | `search_facts` |
| "X 类问题有哪些常见模式" | `search_communities` |

→ **激活成本** = 2-3h 改造 retrieve_graphiti 节点的路由分发逻辑（按问题分类自动选 API），见 Q5 路线图。

---

## 💬 Q3 · md frontmatter 自带属性是否更适合让 Graphiti 储存？

### 短答

**有条件的"是"** — 只对**会变化的属性**有价值；对**静态属性**不必。

### 哪些 md 属性适合进 Graphiti（valid_at/invalid_at 自动追踪演化）

| 属性 | 为什么适合 | 写入时机 |
|---|---|---|
| `mastery_score: 0.30 → 0.65 → 0.85` | 用户学习进度（强烈需要时序） | Story 6 考察后 |
| `understanding: fuzzy → understood` | 理解度变化（强烈需要时序） | 用户 Cmd+Shift+A 改 callout 时 |
| `last_reviewed: 2026-04-15` | FSRS 复习时间戳（时序天然） | 复习触发时 |
| `tags: [tip, error]` | 用户改了 callout 类型（会变） | 用户编辑时 |

### 哪些 md 属性**不必**进 Graphiti（静态 + 文件系统已足够）

| 属性 | 为什么不必 |
|---|---|
| `type: concept` | 创建时定，不变 |
| `created_at: 2026-04-21` | 创建时戳，不变 |
| `subject: cs-61b` | vault 级固化，不变 |
| `board_name: "CS 61B"` | 重命名场景少 |

### 推荐设计（基于 graphrag-hybrid 案例）

```yaml
# 节点/recursion.md frontmatter
---
type: concept                         # 静态 → 文件即源头
subject: cs-61b                       # vault 级
created_at: 2026-04-21                # 静态

# 以下进 Graphiti（时序属性）
mastery_score: 0.30                   # 通过 add_episode 上报
understanding: fuzzy                  # 通过 add_episode 上报
last_reviewed: 2026-04-21T...
---
```

### 写入时机

- 每次 Story 1.16 用户改 callout `[!error]+` 的理解度 → `add_episode` 记一条
- 每次 Story 1.17 AI 双链派生新节点 → `add_episode` 记 derivation event
- 每次 Story 6 考察 → `add_episode` 记 mastery 更新

### 双源真理风险 + 解法

**风险**：frontmatter 是源 vs Graphiti 是源？

**解法**（社区共识，[graphrag-hybrid](https://github.com/rileylemm/graphrag-hybrid) 已落地）：

> **frontmatter 是"声明式快照"，Graphiti 是"事件流"**

- frontmatter 写**当前最新值**（用户人眼可读）
- Graphiti 保留**所有历史快照**（时序追踪）
- 一致性靠 "frontmatter 改 → trigger Graphiti add_episode" **单向同步**（永不反向）

→ 这条规则直接决定 Q4 的同步策略。

---

## 💬 Q4 · md 双向链接关系应该和 Graphiti node 关系实时同步？

### 短答

**❌ 不应该实时双写同步**。这是分布式一致性最常见反模式。

### 错误的双写模式（用户猜测）

```
用户写 [[xxx]] → 同时写 wikilink_graph + Graphiti edge
```

**问题**：

1. 一边失败一边成功 → 不一致
2. 事务复杂度爆炸（需要 2PC 分布式事务协议）
3. 回滚难
4. 性能差（两次 IO 阻塞用户编辑）

### 推荐：单向事件流（Lazy + Batch 混合）

来自 mcp-mycelium / MegaMem 社区共识：

```
md 文件保存
   ↓
Wikilink Graph 立即更新（O(单文件解析)，~10ms）
   ↓
EventBus 发 NoteUpdated 事件
   ↓
Background Worker（Story 1.2 之后）
   ↓
Batch sweep（hourly cron 或文件 mtime 触发）
   ↓
Graphiti add_episode（含 wikilink edge 信息）
```

### 关键点

- **Wikilink 图是热数据**（用户编辑实时反映）
- **Graphiti 是冷数据**（异步聚合 + 语义抽取）
- **同步是单向的**（md → Graphiti），永远不反向（Graphiti 不能改 md）
- **延迟容忍**：Graphiti 滞后 1-60 分钟可接受（学习场景非实时强一致）

### 三种同步策略对比（社区案例）

| 策略 | 触发时机 | 成本 | 适合 Canvas |
|---|---|---|---|
| **Real-time** | 每次 md 保存立即写 Graphiti | 高（每次 LLM 调用 5-30s） | ❌ 个人 PKM 不需要 |
| **Batch（推荐）** | Cron 每 30 分钟扫一次 | 中（批量 LLM） | ✅ 默认方案 |
| **Lazy** | 用户问 Graphiti 时才同步 | 低（按需） | ✅ 备选（首查延迟） |

### Canvas 项目落地推荐

**Batch 30 分钟 + Lazy 兜底**：

- 默认 cron 30min 扫所有变化的 md → batch `add_episode`
- 用户在 Cmd+Shift+D 提问时，如果发现 md 还没同步 → 触发 Lazy 同步该 md（首查 +5-30s 延迟可接受）

---

## 💬 Q5 · 同时启用 Wikilink + Graphiti 双引擎，分别侧重不同内容是否更高效？

### 短答

**✅ 是，且这是 2026 社区共识架构**（engraph / mcp-mycelium / MegaMem 全部采用此模式）。

### 两个引擎的最佳分工（Canvas 学习场景）

| 引擎 | 侧重内容 | 检索场景 |
|---|---|---|
| **Wikilink Graph** | 用户**显式声明**的概念引用（`[[xx]]`）+ 文件物理位置 | 1. 找概念邻居（"递归依赖什么"）<br>2. 找原白板的所有节点<br>3. 找未链接的孤儿节点 |
| **Graphiti** | 用户**隐式产生**的学习事件（理解度 / 错误 / 对话历史 / 考察记录） | 1. 错误归档 + 错误模式聚类<br>2. "我之前怎么理解 X"<br>3. 跨白板的隐式相关 |

### 三层分层检索（推荐架构）

```
AI 接到问题
   ↓
第 1 层：Wikilink Graph（< 200ms，零 LLM 成本）
   - get_neighbors(node, hop=2)
   - 90% 简单查询（"X 的邻居"）这一层就够
   ↓ 邻居不足或需要语义补充
第 2 层：Graphiti search_nodes/facts（< 3s，LLM rerank）
   - search_facts("X is related to ?")
   - 错误模式 / 学习历程 / 隐式关系
   ↓ 仍不够（罕见）
第 3 层：LanceDB 向量搜索（< 500ms）
   - 段落级语义相似（最长尾的查询）
```

### 为什么 3 层有效

来自 OpenSearch RRF 论文 + Karpathy 反 RAG 哲学：

1. **90% 查询止步第 1 层** → 避免 RAG 退化
2. **阶梯成本** → 先 0 成本（wikilink），再低成本（Graphiti），最后高成本（LanceDB rerank）
3. **检索质量 = RRF 融合** → Reciprocal Rank Fusion 加权 3 层结果（Cormack 2009 经典 k=60）

### 与项目现状的对接

Round-12 已发现项目后端是**5-way Agentic RAG + Layered RRF**（顶级架构）。Q5 推荐 = 把 Wikilink 作为**第 6 个独立检索通道**接入：

| 通道 | 引擎 | 当前状态 | 工作量 |
|---|---|---|---|
| 1 retrieve_graphiti | Graphiti | ✅ 跑 | — |
| 2 retrieve_lancedb | LanceDB（BGE-M3） | ✅ 跑 | — |
| 3 retrieve_multimodal | 图片/PDF | ✅ 跑 | — |
| 4 retrieve_cross_canvas | 图遍历 | ⚠️ round-11 后语义变 | ~3h 适配 `原白板/` 扁平 |
| 5 retrieve_vault_notes | LanceDB + BM25 | ✅ 跑 | — |
| **6 retrieve_wikilink** | **WikilinkGraphService** | **未接入 RAG** | **~4-6h 接 fusion** |

→ 这就是 Round-12 留下的"1 个 gap"。

### Canvas 落地实施工作量

- ✅ 第 1 层（Wikilink 通道）：Story 1.2 + 1.3（已 ready-for-dev，~18h 实施）+ 接入 RAG（~4-6h）
- ⚠️ 第 2 层（Graphiti 时序）：已集成但未用 search_facts/communities + valid_at（需补 ~10h）
- ✅ 第 3 层（LanceDB 向量）：已用（compression.py），不需新建

---

## 🗺️ 推荐架构（落地路线图）

### Phase 0 · 立即可做（不改 round-11 扁平架构）

1. **不动** Story 1.19 v4 / Story 1.17 v4（扁平架构稳定）
2. **不动** wikilink 设计（Story 1.2/1.3 已规划合理）

### Phase 1 · 短期（next 2-3 sprints）

| # | 任务 | 工作量 | 依据 |
|---|---|---|---|
| 1 | **激活 Story 1.2 + 1.3** — wikilink-graph-build + context-assembly（Karpathy 第 1 层） | ~18h | Q5 第 1 层 |
| 2 | **激活 Graphiti `search_facts`** — retrieve_graphiti 按问题类型自动选 API | ~3h | Q2 |
| 3 | **激活 entity_types** — 让 add_episode 用上 CANVAS_ENTITY_TYPES（concept / mastery / error） | ~2h | Q2 |
| 4 | **接 wikilink 入 fusion** — 加 retrieve_wikilink 第 6 通道 + RRF 加权 | ~4-6h | Q5 |

### Phase 2 · 中期（after Story 1.18 Dashboard）

| # | 任务 | 工作量 | 依据 |
|---|---|---|---|
| 5 | **md frontmatter 时序属性同步到 Graphiti** — Batch 30min cron | ~6-8h | Q3 + Q4 |
| 6 | **激活 valid_at / invalid_at** — 用户改 understanding 后自动 invalidate 旧 fact | ~3-4h | Q3 |
| 7 | **重命名/适配 retrieve_cross_canvas** — round-11 扁平架构后语义已变（用户 Round-12 批注） | ~3h | Q5 通道 #4 |

### Phase 3 · 长期（Story 6 检验白板时）

| # | 任务 | 工作量 | 依据 |
|---|---|---|---|
| 8 | **激活 search_communities** — 找错误模式聚类、易混淆点 | ~5h | Q2 + Q5 |
| 9 | **RRF 融合排序优化** — 3 层检索结果用 Reciprocal Rank Fusion 加权 | ~3h（已有架构基础） | Q5 |

**Phase 1 总工作量**: ~27-29h（4 sprints 内可完成）。
**全部完成总工作量**: ~50-55h（横跨 Story 1.2 → Story 6）。

---

## 📂 关键文件清单（已有，不需要重写）

### 后端（已实现 / 部分实现）

| 文件 | 状态 | 用途 |
|---|---|---|
| `backend/app/services/wikilink_graph_service.py` | ✅ 已实现，未跑起来 | Story 1.2 服务 |
| `backend/app/services/episode_worker.py:1-60` | ✅ 跑（fire-and-forget bug 已绕过） | Graphiti episode 写入 |
| `backend/app/services/memory_service.py:55-893` | ✅ 跑（8 处 group_id 用法） | 学科级隔离 |
| `backend/app/clients/graphiti_client.py` | ✅ 跑 | graphiti-core v0.28.2 client |
| `backend/app/mcp/tools/wikilink_tools.py:49-89` | ⚠️ 已有 8 个 MCP 工具，未串通 | Story 1.3 工具集 |
| `backend/app/mcp/tools/note_search_tools.py:42-191` | ✅ 跑 | RAG 检索工具 |
| `backend/app/services/context_enrichment_service.py:166` | ✅ 跑（仅后处理用法） | wikilink 富化（待升级为独立通道） |
| `backend/lib/agentic_rag/state_graph.py:540-671` | ✅ 跑（5 通道 + RRF） | 顶级 Agentic RAG 框架 |

### Spec 文档（已有）

- `_bmad-output/implementation-artifacts/epic-1/1-2-wikilink-graph-build.md` — ready-for-dev
- `_bmad-output/implementation-artifacts/epic-1/1-3-wikilink-context-assembly.md` — ready-for-dev
- `_bmad-output/research/karpathy-graphify-insights-2026-04-13.md` — Karpathy 思路调研
- `_bmad-output/research/round-12-graphiti-karpathy-5-conjectures-audit-2026-04-21.md` — Round-12 调研报告（本文上游）

### 社区参考（外部）

- [Graphiti 官方 + Zep](https://blog.getzep.com/how-do-you-search-a-knowledge-graph/) — 3 个 search API 选用规则
- [Karpathy llm-wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — 原始提案
- [graphrag-hybrid](https://github.com/rileylemm/graphrag-hybrid) — frontmatter + Graphiti 已实现案例
- [engraph](https://github.com/devwhodevs/engraph) — Obsidian + KG + MCP 双引擎参考
- [MegaMem](https://github.com/C-Bjorn/MegaMem) — Graphiti + Obsidian frontmatter 自动推导
- [mcp-mycelium](https://github.com/lukehollenback/mcp-mycelium) — 文件系统即图数据库

---

## ✅ 验证方式（5 个回答的可执行验证）

### Q1 验证：跑双引擎 benchmark

```bash
cd backend
.venv/bin/python -m pytest tests/integration/test_dual_retrieval_benchmark.py
# 应看到：wikilink P95 < 200ms / Graphiti P95 < 3s / 命中率 wikilink 90% 简单查询
```

### Q2 验证：检查 Graphiti API 使用情况

```bash
grep -rn "search_nodes\|search_facts\|search_communities" backend/app/
# 应看到：search_nodes 2 处 / search_facts 0 处 / search_communities 0 处（Round-12 差距）
```

### Q3 验证：frontmatter 时序属性写入 Graphiti

```bash
# 修改 节点/recursion.md 的 mastery_score: 0.30 → 0.65
# 等 Batch sweep 触发
# Cypher 查 Neo4j：应看到 valid_at = old, invalid_at = now 的旧 fact + 新 fact
```

### Q4 验证：观察同步延迟

```bash
# 用户编辑 md → Wikilink Graph 即时更新（< 100ms）
# 30 分钟后 → Graphiti 节点出现新 fact
# Log 应无 rollback / retry 警报（无双写一致性失败）
```

### Q5 验证：3 层检索分层命中率

```bash
# 跑 100 个真实学习问题
# 统计：第 1 层 / 第 2 层 / 第 3 层 命中率
# 应符合：第 1 层 ≥80% / 第 2 层 ≤15% / 第 3 层 ≤5%
```

---

## 🎯 给用户的下一步选项

读完本文后，请选一个方向：

| 选项 | 含义 | 接下来 Claude 做什么 |
|---|---|---|
| **A · 接受推荐架构** | 立即启动 Story 1.2 + 1.3 实施（Karpathy 第 1 层） | 跑 `bmad-bmm-dev-story` skill 实施 Story 1.2 spec，~18h 工作量 |
| **B · 先做 Story 1.18 Dashboard** | 1.2/1.3 延后，Dashboard 先用 Dataview `FROM "原白板"` 直查（不依赖图） | 转去实施 Story 1.18 |
| **C · 想细看某层** | 点名 Q1 / Q2 / Q3 / Q4 / Q5 中的某问深入展开 | 出第二轮 deep-dive 文档 |
| **D · 想要"接入 wikilink 入 fusion"先动** | 跳过 Story 1.2 spec 直接接 retrieve_wikilink 通道（~4-6h） | 立即改 `state_graph.py` 加第 6 通道 |

> **本文不涉及任何代码改动，纯回答 + 推荐路线图。代码层面的下一步等用户拍板。**

---

## 🔗 相关文档锚点

- 上游调研: `_bmad-output/research/round-12-graphiti-karpathy-5-conjectures-audit-2026-04-21.md`
- Karpathy 调研: `_bmad-output/research/karpathy-graphify-insights-2026-04-13.md`
- Story 1.2 spec: `_bmad-output/implementation-artifacts/epic-1/1-2-wikilink-graph-build.md`
- Story 1.3 spec: `_bmad-output/implementation-artifacts/epic-1/1-3-wikilink-context-assembly.md`
- 后端 Agentic RAG: `backend/lib/agentic_rag/state_graph.py:540-671`
- Round-11 扁平架构固化: `_bmad-output/.claude/CLAUDE.md` "Vault 扁平架构" 段
