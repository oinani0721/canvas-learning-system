---
title: "后端运行机制 + Graphiti 全景 — 用户批注回复"
date: "2026-05-13"
respond_to: "_bmad-output/验收单/Story-2.3-UAT-操作指引-2026-05-13.md (User 批注)"
agents_consulted: 5
methodology: "5 并行 Agent Deep Explore"
---

# 后端运行机制 + Graphiti 全景

> [!question]+ User 批注原文（2026-05-13）
> 你这里关于我在 path B 使用原白板的过程，会在节点打下批注，你举的例子是我标记的这个批注是 error，那么关于批注本身以及批注怎么产出的原因是怎么记录下来的，关于批注的理解程度和熟练程度又是怎么记忆下来的，然后关于节点本身又是怎么记录下来的，然后节点和节点之间的双向链接关系又是怎么记录下来的，我需要明确知道你的后端是怎么运行的，以及你的后端中的 Graphiti 又是怎么运行的

> [!success]+ 调研方法
> 5 并行 Agent 深度扫描了 backend + frontend plugin + canvas-vault + Story spec + 已知 gotchas。每个维度的发现下方都附 `file_path:line` 让你能跳转查证。**诚实标注 7 大架构断层** — 不是所有你以为已存的能力都真存了。

---

## 0️⃣ 一句话总览（先建心智模型）

你的系统由 **6 个独立的"记忆体"** 组成，每个负责存不同的东西。它们目前**没有统一同步**，有些"管道"是断的（已知缺口）：

| 记忆体                              | 存什么                                  | 在哪                                               |
| -------------------------------- | ------------------------------------ | ------------------------------------------------ |
| **文件系统**                         | 节点 .md + 白板 .md + 批注 callout（原文）     | `canvas-vault/节点/*.md` / `canvas-vault/原白板/*.md` |
| **LanceDB**（向量）                  | 节点的语义 chunk 向量（用于 RAG 语义检索）          | `~/.canvas/lancedb/` per-vault 独立表               |
| **WikilinkGraph**（NetworkX dict） | `[[X]]` 双向链接图（用于 1-hop / 2-hop 邻居遍历） | **进程内存**，per-vault dict                          |
| **Graphiti / Neo4j**（图数据库）       | 学习事件 + 误解记录 + LLM 抽出的概念/关系           | bolt://localhost:7691                            |
| **Mastery Store**（在 Neo4j 内）     | BKT 理解度 + FSRS 熟练度的真值                | Neo4j EntityNode                                 |
| **In-memory cache**              | 最近 2000 条 episode 兜底，全挂时救火           | Python list in MemoryService                     |

`★ Insight ─────────────────────────────────────`
**"为什么不是一个数据库？"** — 不同维度的数据有不同检索模式，强行合并性能会爆：向量检索（LanceDB）/ 图遍历（NetworkX）/ 时序事件（Graphiti）/ 全文搜（Neo4j fulltext）四种检索都各自最优解。代价是**架构复杂 + 数据可能不一致**。这是工程权衡，不是设计缺陷。
`─────────────────────────────────────────────────`

---

## 🗺️ 系统全景 ASCII 图

```
┌─────────────────────────────────── Obsidian 客户端（你看到的） ───────────────────────────────────┐
│  你在 节点/recursion.md 写 [[base case]]                                                          │
│  你按 Cmd+Shift+A 标 [!error]+ "忘记 base case 无限循环"                                          │
│  你按 Cmd+Shift+C 触发 AI 对话                                                                    │
│  你按 Cmd+Shift+D 派生新节点                                                                      │
└──────────┬─────────────────────┬─────────────────────────┬───────────────────────────────────────┘
           ↓ vault.modify()       ↓ Cmd+Shift+A             ↓ Cmd+Shift+C/E
    metadataCache.on(changed)   wrapSelection()         POST /api/v1/chat/enrich-context
    debounce 1500ms            (纯本地, 0 backend)       (Story 2.1+2.3 主入口)
           ↓                                                ↓
    POST /api/v1/index/refresh-changed                  3 并行检索:
                                                          ├─ WikilinkGraph 2-hop (Python NetworkX)
                                                          ├─ Graphiti 3-tier search_memories
                                                          │   └─ Tier 1: Graphiti search_() (Gemini reranker)
                                                          │   └─ Tier 2: Neo4j fulltext (Lucene)
                                                          │   └─ Tier 3: In-memory cache (Python list)
                                                          └─ LanceDB supplementary (bge-m3 向量)
                                                                ↓
                                                          chat_context_assembler.assemble_context
                                                          → 输出 <rag_context> 拼接的 system prompt
                                                          → Claude API → 流式回答给你
```

---

## 1️⃣ 维度一：批注本身（Cmd+Shift+A 标的 callout）怎么记录

### 关键事实：**你的批注本身只是 .md 里的纯文本**

> [!error]+ 出乎意料的真相
> 你按 Cmd+Shift+A 标的 `[!error]+ 错误` callout，**只写进 .md 文件**，**不进** backend、**不进** Graphiti、**不进** 任何数据库。它本质上是"给你自己看的笔记标签"。

### 端到端旅程

| Step | 发生了什么 | 代码 |
|---|---|---|
| 1 | 你按 Cmd+Shift+A | `main.ts:117` hotkey 绑 `canvas:annotate-callout` |
| 2 | 弹两步 Modal（Tag + 理解度） | `main.ts:2023-2035 handleAnnotateCallout` |
| 3 | `wrapSelection()` 拼接 callout 文本 | `callout.ts:20-34` |
| 4 | `editor.replaceSelection(...)` 写回 .md | `main.ts:3389-3413` |
| 5 | **没有 fetch / 没有 backend call** | — |

写进 .md 的实际样子（例）：
```markdown
> [!error]+ ❌ 错误
> - [ ] ✅ 已懂
> - [x] 🤔 模糊
> - [ ] ❌ 不懂
>
> 忘记 base case 导致无限循环
```

### 那"AI 提醒你之前的误解"靠什么？

走**另一条完全独立的管道**（AI candidate 路径）：

```
AI 对话进行中
   ↓ 对话结束 (G1 缺口: plugin 当前没自动触发)
   ↓
POST /api/v1/chat/post-turn-extract  (chat.py:626-705)
   ↓
ErrorExtractor.extract_errors_from_dialog (error_extractor.py:115-160)
   ↓ LLM 分析对话, 提取 misconception
   ↓
ErrorClassifier 双标签 (legacy 4 类 + pedagogy 4 类)
   ↓
write_error_dual (error_writer.py)
   ├─→ 写 frontmatter errors[] 或 error_candidates[]
   └─→ write_error_to_graphiti → record_knowledge_entity (memory_service.py:1299-1380)
                                  → Neo4j Episode (episode_type="misconception")
```

### 已知缺口 G1：Cmd+Shift+A 不进库

Story 1.16 `done` 只完成了"包装文本"，spec 里没要求写 backend。要让你按 Cmd+Shift+A 的 callout **真正影响 AI 后续提醒**，需要补：
- plugin 加 post-Cmd+Shift+A hook → POST 到 backend
- backend 把 callout body + 当前活跃 session 一起塞 ErrorExtractor
- 当前 **完全没有此环节**

---

## 2️⃣ 维度二：批注的"产出原因"（为什么标这个误解）怎么记录

### 关键事实：**大部分丢失，只有 AI 自动路径会保留**

| 信息 | Cmd+Shift+A callout 路径 | AI candidate 自动路径 |
|---|---|---|
| 错误本身的文字 | ✅ callout body 原文 | ✅ `description` |
| Tag (error/question/...) | ✅ callout 类型 | ✅ `pedagogy_type` + `legacy_type` |
| 你当时的理解度 | ✅ checkbox `[x] 模糊` | ❌ 不存在此维度 |
| **产生原因 / 为什么标这个** | ❌ **完全没记录** | ⚠️ `context` 字段（10-80 字摘要） |
| **触发对话原文 / 哪几轮** | ❌ **完全没记录** | ⚠️ `raw_dialog_excerpt` + `evidence_turns[]` 字段存在但 **error_extractor.py:154 默认空字符串** — schema 占位但未填 |
| session_id / canvas_path | ❌ **完全没记录** | ✅ candidate.session_id + node_id |
| AI 的判错理由 | ❌ | ⚠️ `ai_reason` 字段（Task 5 升级才填，**当前空**） |

`★ Insight ─────────────────────────────────────`
**你的批注 callout 是"哑数据"**：只有文字 + 情绪标签 + 理解度三选一，没有任何"产生上下文"。这意味系统**没法回答 "你为什么 5 月 10 日突然觉得 base case 难"** 这种因果问题。要支持这种回溯，需要 plugin 端在 Cmd+Shift+A 时把"前 5 轮 AI 对话 + 当前打开的笔记 + 触发时间"作为 metadata 一起送 backend。
`─────────────────────────────────────────────────`

---

## 3️⃣ 维度三：批注的"理解程度 + 熟练程度"怎么记忆

### 两个不同维度，两套算法

| 维度 | 算法 | 比喻 | 数据存哪 |
|---|---|---|---|
| **理解程度** | BKT（Bayesian Knowledge Tracing, Corbett & Anderson 1995） | "AI 心里偷偷记的'你是不是真懂这个'概率" | Neo4j EntityNode.p_mastery（0.001-0.999） |
| **熟练程度** | FSRS（Free Spaced Repetition Scheduler, Ye 2024） | "Anki 卡片：几天后你还能回忆起来的概率" | Neo4j EntityNode.fsrs_stability / fsrs_difficulty |

### BKT 4 参数（medium 难度）

- `P_L0 = 0.10`（先验：还没考过，AI 猜你已经会的概率）
- `P_T = 0.20`（学习转移：做一道题后从不会到会的概率）
- `P_G = 0.20`（猜对率：不会的人蒙对的概率）
- `P_S = 0.10`（失误率：会的人手滑做错的概率）

每次你做对/做错 → 跑贝叶斯后验公式更新 `p_mastery`。

### FSRS 三元组 DSR

- `Difficulty`（这个概念对你来说有多难）
- `Stability`（记忆稳定性，单位"天"）
- `Retrievability` R（**永远不存**，每次按 `exp(-days/stability)` 现算）

### 关键事实：算法 ready，写回管道断

| 组件 | 状态 |
|---|---|
| MasteryEngine BKT/FSRS 算法 | ✅ production-ready (`mastery_engine.py:148-270`) |
| MasteryStore Neo4j 持久化 | ✅ production-ready |
| REST `/mastery/{concept_id}/grade` | ✅ production-ready (`mastery.py:266-491`) |
| MCP `update_bkt` / `update_fsrs` 工具 | ❌ Story 5.1/5.2 ready-for-dev，**未实施** |
| .md frontmatter 写回 | ❌ Templater 模板有 `bkt_p_mastery: null` 占位，**没代码写回** |
| Cmd+Shift+A callout → 触发 mastery 重算 | ❌ **断**（Story 2.5 plugin hook 未集成） |
| 颜色自评 → mastery 衰减 | ✅ `/mastery/{id}/self-assess` 已在（红/绿/黄 映射 0.20/0.85/0.55） |

`★ Insight ─────────────────────────────────────`
**Neo4j 是 mastery 的唯一真相源，.md frontmatter 是死字段**。你在 vault 看到的 `mastery_score: 0.30` 是 ai-linked-doc 创建节点时塞的初始值，**不会随 BKT 更新而变化**。要让你在 Obsidian 直接看到 mastery 变化，必须等 Story 5.1 Task 3（.md 写回）实施。当前要看真实值得调 `GET /mastery/{concept_id}` REST API。
`─────────────────────────────────────────────────`

---

## 4️⃣ 维度四：节点本身（.md 文件）怎么记录

### 节点同时存在于 **4 个地方**（每个负责不同检索模式）

```
canvas-vault/节点/recursion.md
       │
       │ 1. 物理存储（你看见的）
       ├─→ 文件系统 .md：frontmatter + body + callouts
       │
       │ 2. 语义索引（用于 RAG 召回）
       ├─→ LanceDB chunks：按段落分块 → bge-m3 1024d 向量
       │   表名：vault_id_{sanitized_vault}_chunks（per-vault 隔离）
       │
       │ 3. 引用图（用于 1-hop / 2-hop 邻居遍历）
       ├─→ WikilinkGraphService NetworkX DiGraph
       │   节点 key = basename "recursion"（不带 .md / 路径）
       │
       │ 4. 学习事件附着（用于历史追溯）
       └─→ Neo4j Episode.node_id = "recursion"
           （只有当你做过题/产生过 misconception 时才出现）
```

### .md 文件实际结构（举例）

```markdown
---
type: concept
subject: CS 61B
mastery: 0          # 死字段，BKT 不会更新它
relationships:
  - target: "[[base-case]]"
    type: prerequisite
    evidence: "递归终止条件"
---

# Recursion

> [!info]+ 概念
> 函数调用自身的控制流...

> [!error]+ ❌ 错误
> - [x] 🤔 模糊
> 忘记 base case 导致无限循环
```

### 节点同步触发

- **创建/修改 .md** → Obsidian metadataCache → plugin debounce 1500ms → `POST /api/v1/index/refresh-changed` (`index.py:103-154`)
- **backend 收到** → `LanceDBIndexService.schedule_note_index` → 再 debounce → `WikilinkGraphService.refresh()`（**当前内部是全量 rebuild**，Story 8.1 "v1 增量"标但未真增量）
- **LanceDB 重新 chunk + embed** → 写入 per-vault 表
- **生效延迟**：约 **3-5 秒**（plugin 1.5s + backend 数秒 + rebuild 100ms）

`★ Insight ─────────────────────────────────────`
**节点 .md 是"母本"，其他 3 个存储是"派生索引"**。任何时候，如果你想确认数据真值，**查 .md 文件本身**就行 — 其他 3 个是衍生缓存，会过期或被重建。这是 Obsidian-first 架构的关键 — 区别于 Notion 那种"数据库为母本"的产品。**你的笔记永远是你的笔记（.md 文件），系统挂了你也不会丢东西**。
`─────────────────────────────────────────────────`

---

## 5️⃣ 维度五：节点和节点的双向链接关系怎么记录

### 关键事实：**双向链接图与 Graphiti 是完全独立的两套图**

```
你写 [[base case]] 后:
  1. Obsidian 自动维护 metadataCache.resolvedLinks (内置, 不是我们写的)
  2. Plugin 触发 POST /api/v1/index/refresh-changed
  3. Backend 用 obsidiantools.Vault().connect() 重新扫描 vault 构图
  4. 存入 WikilinkGraphService 进程内 NetworkX DiGraph (Python dict)
```

### 数据结构

```python
WikilinkGraphService._graph = networkx.DiGraph()
# 内部存 (Python 代码视角):
edges = [
    ("recursion", "base-case"),         # recursion.md 写 [[base-case]]
    ("base-case", "recursion"),         # base-case.md 写 [[recursion]]
    ("recursion", "factorial-example"),  # 单向
]
# 节点 key 是 basename, 不是路径! ("recursion" 不是 "节点/recursion.md")
```

### 双向是怎么实现的：**DiGraph + predecessors 查询**

底层是**有向**图。A 写 `[[B]]` 只产生 `A → B` 一条**出边**。反向 backlink 不会自动生成边，而是**查询时**用 `graph.predecessors(B)` 反查"谁指向 B"：

```python
def _node_adj(node):
    out = list(self._graph.successors(node))      # 出边（我引用谁）
    if include_backlinks:
        for b in self._graph.predecessors(node):  # 入边（谁引用我）
            if b not in seen: out.append(b)
    return out
```

返回的 `NeighborNote` 带 `is_backlink: bool` 标记来源方向。

### ASCII 双向示意

```
   recursion.md 正文写 [[base-case]] [[factorial-example]]
   base-case.md 正文写 [[recursion]]

  ┌─────────────────┐  outgoing      ┌──────────────────────────┐
  │   recursion     │ ──────────────►│       base-case          │
  │                 │◄────────────── │                          │
  └─────────────────┘  backlink      └──────────────────────────┘
         │ outgoing
         ▼
  ┌──────────────────────────────────┐
  │     factorial-example             │  (单向：recursion 引用它，它没回引)
  └──────────────────────────────────┘
```

### chat 时怎么用

`POST /api/v1/chat/enrich-context` → `enrich_from_wikilink_graph(node_path, max_hops=2)`：
- BFS 2 跳遍历（200ms 硬超时）
- 每个邻居读 .md 全文 → 抽 frontmatter `relationships[]` + callouts + 400 字 prose excerpt
- `path_trace` 累积中间跳点：`["recursion", "base-case", "factorial-example"]` 让 LLM 看到"通过哪个中间节点到达"

### 已知缺口

| # | 缺口 | 影响 |
|---|---|---|
| G2 | 增量 refresh 是假增量（内部 fallthrough 到全量 rebuild） | 大 vault（≥1000 节点）会肉眼可见卡顿 |
| G3 | basename 冲突隐患（不同目录同名 .md 在 NetworkX 合并成同节点） | 当前 vault 没出现，未来要警惕 |
| G4 | metadataCache → backend 不传 wikilink 内容（plugin 只传路径列表，backend 自己再扫一遍） | 双重解析浪费，但 Story 8.1 设计接受 |

---

## 6️⃣ 维度六：Graphiti 怎么运行（你最不懂这块）

### 一句话：**Graphiti 是 AI 的"学习日记本 + 自动概念图谱"**

它记录你每次学了什么 / 做错了什么 / 做对了什么，然后用 LLM 自动从这些日记里抽出"概念"和"概念间的关系"，连成一张能随时间增长的知识图谱。底层是 Neo4j。

### 3 个核心概念

| 概念 | 比喻 | 实际是什么 |
|---|---|---|
| **Episode（事件）** | 一篇日记 | "2026-05-13 我学了递归 base case 出错" — 一条带时间戳的学习事件 |
| **Entity（实体）** | 日记里的"人名/概念名" | "递归" / "base case" / "factorial" — LLM 从 episode 文本里自动抽取 |
| **Fact / Edge（关系）** | 概念之间的连线 | "递归 IS_A 控制流" / "base case PREVENTS 无限循环" — LLM 抽取 |

### Episode 实际结构（真实代码）

```python
{
    "episode_id": "episode-{sha256_hash}",  # 确定性 hash, 写入幂等
    "content": "User student-123 learned 'recursion base case' with score 80",
    "episode_type": "learning",  # "learning" / "misconception" / "node_created" / ...
    "user_id": "student-123",
    "canvas_path": "CS 61B/recursion.canvas",
    "node_id": "节点/base-case",
    "concept": "recursion base case",
    "agent_type": "DeepDecompose",
    "score": 80,
    "timestamp": "2026-05-13T09:42:00",
    "subject": "CS 61B",
    "group_id": "vault:canvas_vault"  # 隔离命名空间
}
```

### 3-Tier 搜索（你问 AI 时背后跑的事）

`memory_service.search_memories(query, group_id)` 入口 (`memory_service.py:1678`)：

```
┌── Tier 1: Graphiti search_() ───────────────────────────┐
│  reranker 高质量 + 语义优先 (Gemini cross-encoder)     │
│  combined_rrf / cross_encoder / edge / node 5 种 recipe │
│  3 秒 timeout, 挂了静默返回空 list                       │
└──────────────────────────────┬──────────────────────────┘
                               ↓
┌── Tier 2: Neo4j fulltext ────┴──────────────────────────┐
│  Lucene 关键词索引兜底                                   │
│  CALL db.index.fulltext.queryNodes('episode_content')    │
│  原始 score 除 10.0 归一化                               │
└──────────────────────────────┬──────────────────────────┘
                               ↓
┌── Tier 3: In-memory cache ───┴──────────────────────────┐
│  Python list 暴力 substring 匹配 (固定 0.1 分)           │
│  Neo4j 都挂了也能用, 召回质量最差                        │
│  容量上限 MAX_EPISODE_CACHE = 2000                       │
└──────────────────────────────┬──────────────────────────┘
                               ↓
       三路合并 + 去重 + 统一评分 + FSRS R-value boost
                               ↓
       按 relevance_score 降序返回, truncate 到 limit
```

### group_id 隔离机制（防止多 vault 串库）

**命名规约**（Story 2.5.Y D16 锁定 2026-05-05）：
- `vault:<vault_id>` — 单 vault（你的 `vault:canvas_vault`）
- `vault:<vault_id>:<subject_id>` — vault 内学科二级
- `vault:<vault_id>:<canvas_name>` — vault 内 canvas 二级

**ContextVar 透传链**：
```
1. HTTP request 进 endpoint → 解析 vault_id
2. 调 set_current_subject_id(group_id) 注入 ContextVar
3. 下游 service 读 ContextVar 加 filter
4. 所有 Cypher 强制 WHERE n.group_id = $group_id (cypher_with_group_filter)
5. pre-commit hook lefthook.yml::cypher-vault-filter-lint gate 防裸 cypher
```

**中文 vault sanitize**：
- NFKC normalize（防 macOS APFS NFC/NFD 冲突）
- casefold（Unicode-aware lower）
- `[^\w]+` → `_`（保留 CJK / 西里尔 / 谚文）
- 截 200 字符
- 例：`"CS 61B"→"cs_61b"` / `"笔记库"→"笔记库"` / `"📚 笔记本"→"笔记本"`

### Gemini Lock（重要冷知识）

`episode_worker.py:287-412` 把 Graphiti 内部硬锁 Gemini：

```python
llm_client = GeminiClient(config=LLMConfig(api_key=google_api_key, model="gemini-2.5-flash"))
embedder = GeminiEmbedder(config=GeminiEmbedderConfig(api_key=..., model="gemini-embedding-001"))
cross_encoder = GeminiRerankerClient(...)

self._graphiti = Graphiti(..., llm_client=llm_client, embedder=embedder, cross_encoder=cross_encoder)
```

**为什么**：
1. **成本最低** — gemini-2.5-flash 用于 episode entity/edge extraction，token 量大但便宜
2. **JSON 结构化输出可靠** — Gemini SDK 的 schema-constrained output 在 graphiti-core 0.28.2 最稳
3. **向量维度匹配 LanceDB** 不可换

**用户视角的关键事实**：
- 主对话 LLM 是 **Claude**（你问 AI 时给你答案的）
- Graphiti **后台 episode 抽取 entity/edge** 用 **Gemini**（你看不见的后台任务）
- 两条 LLM 通路并行，不冲突

### 当前哪些数据进 Graphiti

| 数据类型 | 进 Graphiti? | 入口 |
|---|---|---|
| 学习事件（答题得分） | ✅ | `record_learning_event` → `episode_type="learning"` |
| Canvas 时序事件 | ✅ | `record_temporal_event` → `node_created` / `edge_created` |
| 历史误解 | ✅ | `record_temporal_event(event_type="misconception")` |
| 错误归档 | ✅ | error_writer.py + record_knowledge_entity |
| 节点 .md 内容 | ❌ | 只进 LanceDB（向量）+ 文件系统 |
| 双向链接 | ❌ | 进 WikilinkGraph（独立 NetworkX）|
| Callout 批注 | ❌ | Story 2.5 plugin hook **未集成** — Cmd+Shift+A 不入库 |
| Subject 配置 | ❌ | `.canvas-config.yaml` YAML 文件 |
| FSRS 卡片状态 | ❌（在 Neo4j 但非 Graphiti episode） | MasteryStore EntityNode |

---

## 🚨 当前架构的 7 大断层（诚实告知）

| # | 缺口 | 影响 | 修复在哪 |
|---|---|---|---|
| G1 | Cmd+Shift+A callout **不**进 backend / Graphiti | 你的批注是"哑数据"，AI 看不到 | Story 2.4 callout-annotation-tips（ready-for-dev） |
| G2 | post-turn-extract 在 Obsidian 路径**未触发** | AI 对话错误候选不会自动产生 | Story 2.5 plugin hook（review 状态后端 done，plugin 端缺） |
| G3 | mastery .md 写回**断**（Neo4j 是真值，.md 死字段） | 你在 Obsidian 看不到 BKT 实时更新 | Story 5.1 Task 3（ready-for-dev） |
| G4 | MCP `update_bkt` / `update_fsrs` / `query_mastery` 工具**未实现** | MCP 客户端无法主动调 mastery | Story 5.1 / 5.2 / 5.3（ready-for-dev） |
| G5 | wikilink graph 与 Graphiti 是**两张图**，不互通 | 用户 Cmd+Click 走 wikilink，AI search 走 Graphiti，可能数据不一致 | 架构层债务（无 Story） |
| G6 | 增量 refresh 是**假增量**（内部全量 rebuild） | 大 vault 卡顿（你目前 10 节点没事） | wikilink_graph_service.py:226-230 注释明写"v1 full rebuild" |
| G7 | 30+ 处 **raw Cypher** 待迁移到 cypher_helpers | 跨 vault 泄漏风险（wave-6 backlog） | cypher_helpers.py:13-50 列出 |

---

## 8️⃣ 给学习产品的设计启示

`★ Insight ─────────────────────────────────────`
- **"Obsidian-first" 架构的价值**：.md 文件是母本，所有衍生索引（LanceDB / WikilinkGraph / Graphiti）都是缓存。即使后端全挂，你也不会丢一个字符。这是与 Notion / Anki 类闭源产品的根本区别。
- **"批注的产出原因"是个未解决的产品问题**：当前系统把"做完批注"和"产出批注的对话"完全切割。要回答"5 月 10 日你为什么觉得 base case 难"这种问题，需要 plugin 端在 Cmd+Shift+A 时把前 5 轮 AI 对话 metadata 一起送 backend。这是 Story 2.4/2.5/2.6 三个 Story 才能解决的产品复合能力。
- **"知识图谱"是个工程奢侈品**：Graphiti（Neo4j）每次写都要跑 Gemini extract entity/edge，成本不便宜。当前**没有让 callout body 自动进 Graphiti** 是有意的 — 等 Story 2.5 plugin hook done 后才会真正运转。在那之前，Graphiti 的价值主要是"AI 对话产生 learning_event / misconception"这条窄路径。
- **3-tier 搜索的真正用途不是"找到最相关的笔记"**：而是"保证服务挂一半也能给出有用答案"。Tier 1 挂了有 Tier 2 兜底，Tier 2 挂了有 Tier 3 救火。这是 Boris 工作流"渐进降级"思想在检索层的体现。
- **mastery / FSRS 算法 ready 但写回管道断**是当前最大的体验缺口：用户看不到自己学习进度的实时反馈。Story 5.1 ship 后才会改善（这就是 CURRENT_TASK 8-Session plan 把 S3=5.1 排第三的原因）。
`─────────────────────────────────────────────────`

---

## 9️⃣ 代码引用清单（全 file:line 让你跳转）

### 批注路径
- `frontend/obsidian-plugin/src/main.ts:117` — Cmd+Shift+A hotkey 绑定
- `frontend/obsidian-plugin/src/main.ts:2023-2035` — `handleAnnotateCallout()`
- `frontend/obsidian-plugin/src/callout.ts:1-34` — callout 类型 + wrapSelection
- `backend/app/api/v1/endpoints/chat.py:626-705` — `POST /post-turn-extract`（plugin 不调）
- `backend/app/services/error_extractor.py:115-160` — ErrorExtractor
- `backend/app/services/error_writer.py:487-608` — `write_error_to_graphiti`
- `backend/app/graphiti/entity_types.py:247-270` — Misconception entity schema

### Mastery / BKT / FSRS
- `backend/app/services/mastery_engine.py:148-270` — BKT 公式 + FSRS 更新
- `backend/app/services/mastery_engine.py:715-748` — `apply_external_signal`（misconception → 扣分）
- `backend/app/services/mastery_store.py:38-98` — Neo4j get/save concept
- `backend/app/models/mastery_state.py:25-65` — DEFAULT_BKT_PARAMS
- `backend/app/api/v1/endpoints/mastery.py:266-491` — grade / override / self-assess / graphiti-sync

### 节点 + Wikilink
- `backend/app/services/wikilink_graph_service.py:37-588` — NetworkX 图核心
- `backend/app/services/wikilink_context_service.py:365-544` — `enrich_from_wikilink_graph`
- `backend/app/api/v1/endpoints/wikilink.py:68-167` — 4 个 REST endpoint
- `backend/app/api/v1/endpoints/index.py:103-154` — refresh-changed incremental
- `frontend/obsidian-plugin/src/main.ts:217-229` — metadataCache hook

### Graphiti / Memory
- `backend/app/services/memory_service.py:183-239` — `class MemoryService`
- `backend/app/services/memory_service.py:409-546` — `record_learning_event`
- `backend/app/services/memory_service.py:1411-1521` — `_search_graphiti` Tier 1
- `backend/app/services/memory_service.py:1639-1676` — `_search_neo4j_fulltext` Tier 2
- `backend/app/services/memory_service.py:1678-1792` — `search_memories` 3-tier
- `backend/app/services/memory_service.py:1794-1884` — `search_error_memories` (Story 2.3 just shipped)
- `backend/app/services/episode_worker.py:287-412` — Gemini lock
- `backend/app/core/subject_config.py:212-261` — `build_vault_group_id`
- `backend/app/config.py:935-963` — `sanitize_vault_id`
- `backend/app/utils/cypher_helpers.py:1-200+` — `cypher_with_group_filter`

---

## 🔗 相关文档

- 主验收单：`_bmad-output/验收单/Story-2.3-historical-error-reminder.md`
- UAT 操作指引：`_bmad-output/验收单/Story-2.3-UAT-操作指引-2026-05-13.md`
- 已知缺口清单：`docs/known-gotchas.md`（20 条 G-FAKE / G-PIPE / G-SILENT 等）
- Round-10 架构重设计：`_bmad-output/验收单/批注回复/Round-10-架构重设计.md`
- Round-12 Graphiti vs Wikilink 双轨：`_bmad-output/验收单/批注回复/Round-12-Graphiti-vs-Wikilink-双轨检索.md`

---

跑完这份文档你应该能：
1. 在 Obsidian 内对每个维度都建立**正确的心智模型**（哪些数据自动 / 哪些断 / 哪些是死字段）
2. 看到自己批注后**正确预期** AI 会不会反馈（答：当前 Cmd+Shift+A 不会，需要走 AI candidate 路径）
3. 决定 Story 2.3 UAT 走 Path A / B / C 时**知道你在验证什么**
4. 看后续 Story 5.1 / 5.2 / 2.4 / 2.5 时**知道它们要解决的具体断层**


**User：我个人极其关注的是我的批注，以及我在原白板使用双向链接来拆分和联系节点的整一个探索的过程，批注是核心，我需要用我的个人记忆系统充分的理解我使用原白板的学习过程，这样我使用检验白板的时候，才可以根据我的原白板学习过程来极其针对性的考察我，所以我需要你 deep research 当前的设计**