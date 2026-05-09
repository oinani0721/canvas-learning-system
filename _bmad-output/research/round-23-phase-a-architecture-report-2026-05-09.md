---
title: Phase A 架构全景报告 — 补充学习材料搜索
date: 2026-05-09
plan: EPIC1-BMAD-DEV-ASSESS-2026-04-17
story: 2.2-Phase-A
status: 实施完成 + 1 个 P0 入口 gap 待修
commits: 9
audit_method: 3 并行 Explore agent deep explore（worktree feature-obsidian-hybrid-dev）
---

# Phase A 架构全景报告

> **一句话定位**：Phase A = Canvas Learning System 的**补充学习材料搜索**功能 — 当 AI 在 Claudian 侧栏回答你笔记问题时，自动从你 vault 里找出 2-5 条最相关的讲义/讨论片段，附带 Obsidian wikilink 让你一键跳到对应章节。

---

## 1. 用户视角：这是什么功能？

### 用户故事

**作为**学习者，
**我想**在 AI 回答完我笔记里的问题后，再看到 2-3 条相关的笔记标题列表，
**以便**我可以一键跳过去看更详细的讲义/讨论，而不用自己手工搜索。

### 在 Canvas Learning System 中的定位

Canvas Learning System 整体由 **9 个 Epic** 构成：

| Epic | 名字 | 涉及 Phase A？ |
|---|---|---|
| Epic 1 v2 | Obsidian + Claudian 基础设施 | ⬜ 间接（提供 vault + plugin 容器） |
| **Epic 2** | **智能学习对话**（含 Story 2.1 邻居注入 / Story 2.2 **本 Phase A** / Story 2.3-2.8） | ✅ **核心** |
| Epic 3 | 节点 AI 对话与交互 | ⬜ 互补（Story 3.1 节点对话用 1-hop） |
| Epic 4 | Edge 连线对话 | ⬜ |
| Epic 5 | 精通度追踪 + Dashboard | ⬜ |
| Epic 6 | 检验白板 + 递归考察 | ⬜ |
| Epic 7 | 错误修正 + 间隔复习 | ⬜ |
| Epic 8 | 全局 Dashboard | ⬜ |
| Epic 9 | 多模态增强 | ⬜ |

**Phase A 的具体功能 = Story 2.2 (`supplementary-material-search`) Phase A（Task 1 MCP 集成 + Task 4 降级处理）**

> 完整的 Story 2.2 含 5 个 Task：本 Phase A 完成 #1+#4，Phase B 含 #2 类型权重精排 + #3 wikilink 三级精度，Phase C 含 #5 测试。

---

## 2. 用户体感的完整流程

```
1. 我在 Obsidian 里打开一个学过的概念笔记（如「节点/Eigenvalues.md」）
       ↓
2. 我按 Cmd+Shift+E 启动 AI 对话（自动跳到 Claudian 侧栏）
       ↓
3. 我输入一个具体问题（例 "X 怎么证明？"）
       ↓
4. AI 给我一段主回答 + 一行 "---" 分隔 + "📚 相关学习材料" 列表
       ↓
5. 我点列表里任意一个蓝色 [[wikilink]]，Obsidian 自动跳到对应笔记
```

**Phase A 实测 happy path（2026-05-09 验证）**：

```xml
<supplementary_materials count="5">
  <material rank="1" score="0.508">
    <title>关键点</title>
    <wikilink>[[节点/Eigenvalues-are-special-vectors-that-sat#关键点|关键点]]</wikilink>
    <snippet>文档：Eigenvalues > 关键点 - ...</snippet>
    <source_path>节点/Eigenvalues-are-special-vectors-that-sat.md</source_path>
  </material>
  <material rank="2" score="0.508">
    <title>Eigenvalues-are-special-vectors-that-sat</title>
    <wikilink>[[节点/Eigenvalues-are-special-vectors-that-sat]]</wikilink>
    <snippet>...Eigenvalues are special vectors that satisfy Av = λv...</snippet>
  </material>
  <material rank="3" score="0.508">
    <title>Linear Algebra Fundamentals</title>
    <wikilink>[[节点/Fundamentals#Linear Algebra Fundamentals|Linear Algebra Fundamentals]]</wikilink>
    ...
  </material>
  <!-- 共 5 条，全部来自当前 active vault 真实笔记 -->
</supplementary_materials>
```

---

## 3. 完整数据流（端到端时序）

```
User                Plugin                    Backend chat.py             Wikilink+Assembler          SupplementarySearch+LanceDB
─────              ──────                    ──────────────             ──────────────────          ─────────────────────────────
Cmd+Shift+E ──┐
              ▼
         handleChatWithContext
         · getActiveFile + frontmatter
         POST /enrich-context ────────► enrich_context()
         {node_path, content,            · validate ─────────────────► enrich_from_wikilink_graph
          frontmatter, max_hops:2}                                       · BFS 1-hop/2-hop (200ms)
                                        ◄── neighbors, trace ───
                                        · ChatContextAssembler ─────► 5-priority budget fill
                                                                       · <rag_context>+<manifest>
                                        ◄── AssembledContext ────
                                        ⚠️ if mode=answer & q:
                                          构造 query=stem+q ──────────────────────────────────────► search_supplementary
                                                                                                     · _two_tier_search:
                                                                                                       Tier-1 hybrid prefix
                                                                                                       Tier-2 unprefixed FTS
                                                                                                     · source_priority + filter
                                        ◄── result{materials} ──────────────────────────────────
                                        format_supplementary_xml
                                        final_text += supp_xml
         ◄── EnrichContextResp ────
         · clipboard.writeText
         · exec claudian:open-view
Cmd+V ────┘
   │
   ▼ Claudian → /chat-with-context Skill 解析 <rag_context>+<supplementary_materials> → 中文开场+回答
```

---

## 4. 核心技术：6 层技术栈

> Phase A 不是单一技术 — 是 LanceDB 之上叠加 6 层组件的协同。

### L0 LanceDB（向量 + 列式存储引擎）

- **角色**：底层向量数据库 + 列式存储（兼具 RDB 性能 + 向量能力）
- **vault 隔离机制**：表名加 `vault_id` 前缀（Story 1.9）：`canvas_vault_vault_notes` / `cs_61b_vault_notes` / `数学_vault_notes` 各自独立
- **关键文件**：`backend/lib/agentic_rag/clients/lancedb_client.py:394-412` (`resolve_table_name`)

### L1 数据生命周期（增量索引）

- **SHA-256 fingerprint**：`file_fingerprints.lance` 表存 `file_path / content_hash / last_indexed / chunk_count`，文件改动通过 hash 比对识别
- **Delete-before-insert**：旧 chunk 先按 `canvas_file` 删除，再插新 chunk（防孤儿）
- **Debounce 500ms**：连续修改自动 batch，不冲爆 backend
- **Tenacity 3× 重试** + **JSONL recovery**：失败任务持久化到 `data/lancedb_pending_index.jsonl`，启动时自动恢复
- **关键文件**：
  - `backend/app/services/lancedb_index_service.py:42-188` (`schedule_index` / `schedule_note_index`)
  - `backend/lib/agentic_rag/clients/lancedb_client.py:514-664` (fingerprint 实现)

### L2 切分器（Chunking — 两级切分）

- **第一级 — heading-aware 切分**：按 H1-H4 切片，frontmatter 保留作元数据
- **第二级 — token-aware 句子切分**：用 `tiktoken cl100k_base` 编码器（Claude 3.5 兼容），按句子边界（中英文标点 + 换行）切分
- **chunk 头部注入面包屑**：`文档：<file> > <h1> > <h2>` 让每个 chunk 自带上下文
- **原子保护**：代码块 / `$$...$$` 数学块 / 表格视为不可分割块
- **限制**：512 token max + 50 token overlap（句子边界回溯）
- **关键文件**：`lancedb_client.py:107-278` (`_chunk_text`) + `:2059-2183` (`_split_md_by_heading`)

### L3 Embedder（向量化）

- **模型**：`BAAI/bge-m3` Dense 1024 维
- **路径**：**Ollama GPU 优先**（`http://ollama:11434/api/embed`，含 batch）→ 失败 fallback 到 **本地 sentence-transformers CPU**（`MultimodalVectorizer`）
- **维度**：cosine 相似度 + 1024d float
- **关键文件**：`lancedb_client.py:319` (常量) + `:994-1054` (Ollama API) + `:1056-1086` (`embed`)

### L4 全文索引（FTS — 跨语言关键词）

- **引擎**：LanceDB 自带 **Tantivy** （Rust 高性能 FTS）
- **中文分词**：**jieba `cut_all=False`**（精确模式），文本入库前预分词为空格分隔词串
- **索引列**：`content_tokenized`（不是 `content`，因 Tantivy 默认按空格切，jieba 预处理后两者兼容）
- **英文处理**：纯英文按空格切（不破坏 token）
- **关键文件**：`lancedb_client.py:73-104` (`_jieba_tokenize`) + `:1439-1452` (`_rebuild_fts_index`)

### L5 融合（Hybrid Search — RRF）

- **不用 LanceDB native hybrid**：因表无 registered embedding function，走**手动 RRF**
- **Dense 分支**：`table.search(query_vec)` 取 `2× num_results`
- **FTS 分支**：`table.search(jieba_q, query_type="fts")` 取 `2× num_results`
- **融合算法**：Reciprocal Rank Fusion（**k=60**，可配 `Story 2.11`）
  $$\text{score}_{\text{RRF}} = \sum_{i \in \{dense, fts\}} \frac{1}{k + \text{rank}_i + 1}$$
- **关键文件**：`lancedb_client.py:2475-2520` (manual hybrid) + `:2589-2614` (`_rrf_fuse`) + `:2278` (`rrf_k=60`)

### L6 后处理（Source Priority + 阈值）

- **Source Priority**：`fnmatch` 模式权重相乘后重排
  - 讲义（`*lecture*`）×1.5
  - 讨论（`*discussion*`）×1.4
  - AI 解释（`*-explanations/*`）×0.5（实际被路径黑名单整体过滤）
- **阈值过滤**：`min_relevance=0.30`（实测调，PRD 原 0.70 因 RRF score 区间漂移）
- **黑名单路径**：`-explanations/` 整体过滤
- **Phase B 才接 cross-encoder reranker**：当前是 pass-through，仅 health monitor 监控
- **关键文件**：`backend/app/core/reference_config.py:66-94` + `supplementary_search_service.py:113-130`

### 架构等式

```
Phase A = LanceDB
        + tiktoken/heading 两级切分
        + bge-m3@Ollama-GPU(1024d, CPU fallback)
        + Tantivy FTS@jieba 中文预分词
        + 手动 RRF(k=60)
        + source priority × min_relevance 0.30 过滤
        + SHA-256 fingerprint 增量索引
```

---

## 5. 实测验证（2026-05-08~05-09）

### Commit 历史（9 个累积 ship）

| Commit | 主题 |
|---|---|
| `3bb746e` | initial ship — service + chat.py + SKILL.md + 验收单 |
| `1a3106c` | timeout + tier-2 fallback hardening |
| `9c8b5bd` | LANCEDB_DATA_PATH env 解耦 |
| `01329e7` | 5+1 hardening — singleton + ListTablesResponse + 顶级 mount |
| `5dfad13` | endpoint 不 acquire singleton init lock |
| `dc24364` | vault selector + 顶级 /vaults mount |
| `f0f8ed5` | port 8001 → 8011 fix（Round-22 后 drift） |
| `ef5865f` | vault status detector — status-first UX 替代端口暴露 |
| `012111d` | 增量索引 hook + RRF-aware 阈值校准 — Phase A 真实可用闭环 |

### LanceDB 实存表

```
canvas_vault_vault_notes: 154 rows  ← Story 1.9 vault_id 隔离首次真实建立 (2026-05-09)
file_fingerprints       :  N rows   ← SHA-256 增量索引元数据
vault_notes              : 5618 rows ← 30 March 老索引（保留作 archive）
```

### Smoke test 真实结果

```
HTTP 200 / 26ms (warm singleton)
supplementary_count: 5
supplementary_degraded: false
supplementary_reason: None  ← Tier-1 命中（不是 fallback）
neighbors_count: 2          ← Story 2.1 邻居发现工作
```

5 条真实 wikilink 命中 `节点/Eigenvalues` + `节点/Fundamentals`（用户当前 vault 真实内容），不是 30 March stale 数据。

### 累积工程成果

| 维度 | 数量 |
|---|---|
| 真实根因找到 + fix | **9** 个（timeout / tier-2 fallback / docker volume precedence / BGEM3 cold-start / external volume / ListTablesResponse / mount nesting / asyncio imports / 端口 8002→8011 drift） |
| 部署层 mount 拓扑独立化 | **3 个顶级 mount** (`/app` 代码 / `/lancedb` 数据 / `/vaults` 内容)，平行无嵌套 |
| 用户体验 UX 改进 | **vault status detector**（绿/黄/红三态状态卡 + 一键修复，零端口暴露） |

---

## 6. 三件套定位（Phase A 在检索体系中的位置）

| 维度 | A. Story 2.1 邻居注入 | **B. Phase A 补充搜索** | C. Phase B 类型权重精排 |
|---|---|---|---|
| **What** | wikilink 1-hop/2-hop 邻居 + frontmatter + callout | **LanceDB hybrid 语义搜索补充材料** | 类型权重 + wikilink 三级精度 |
| **How** | `wikilink_graph_service.get_neighbors()` BFS 图遍历 | **bge-m3 + jieba RRF + source priority + 阈值** | `final_score = relevance × type_weight` + `^block_id` 锚点 |
| **回答类型** | "这个概念的邻居在哪？"（图结构已知边） | **"vault 里其他相关材料在哪？"（语义未知边）** | "哪个最权威？跳到哪段？" |
| **状态** | ✅ done (`dad9ed7`, ChatGPT 8/10) | **✅ done (本次 9 commits)** | ❌ pending (Story 2.2 Task 2+3) |
| **召回类型** | 结构性确定召回 | **语义概率召回** | 精排（重排，不召回） |

### 协同方式（PRD §4.1.1 9-step workflow）

```
Step 3 [A 邻居注入]   → 结构性确定召回 (图边精确,~30 个邻居,frontmatter+callout)
Step 5 [B/C 补充搜索] → 语义概率召回   (向量距离,Top 5,跨 vault 全文)
Step 6 [LLM 主回答]   → 基于 A+B 上下文回答
Step 7 [输出渲染]     → 主回答 + `---` + B/C 补充材料列表
```

**串行依赖**：A 先于 B（A 提供 `node_title` 拼到 B 的 query），都先于 LLM。

**互补不冗余**：
- A 答 _"这个概念的邻居在哪？"_ — 图结构已知边（基于用户手写 wikilink）
- B 答 _"vault 里其他相关材料在哪？"_ — 语义未知边（基于 embedding 相似度）
- 重叠场景（邻居恰好高 score）由 source_priority 去重

---

## 7. 关键 Gap（截至 2026-05-09 实测发现）

> 3 个 deep explore agent 实测 audit 找到的工程债务。

### Gap 1: 🔴 Cmd+Shift+E 入口当前不触发 Phase A（致命）

**症状**：用户日常 Cmd+Shift+E 流程下，supplementary 永远返回 `count=0` 空段。

**根因**：Plugin `main.ts:486-491` 只发 `{node_path, content, frontmatter, max_hops:2}` — **未传 `mode=answer` 也未传 `user_question`** → backend 默认 `mode=preload` → `if req.mode=="answer" and req.user_question` 永远 False。

**影响**：之前 smoke test 用 curl 直接传 `mode=answer + user_question` 才看到 5 条真实结果。**用户从 Obsidian 路径根本走不到 Phase A**。

**修复方向**：
- (a) Plugin 加用户输入框（先填问题再 Cmd+Shift+E）
- (b) 双阶段流程 — 第 1 阶段 preload 邻居，第 2 阶段 user_question 来时 fire 补充搜索（在 Claudian 内监听，二次调 backend）

### Gap 2: 🟡 min_relevance 0.30 vs spec 0.70 漂移

**症状**：代码 `chat.py:255` 用 `min_relevance=0.30`，PRD §4.1.1 写 0.70。

**根因**：PRD 假设 cosine score 在 [0, 1] 单调，但 LanceDB 手动 RRF score 落在 0.3-0.6 区间，0.70 阈值会过滤掉所有真实结果。

**修复方向**：
- 把 RRF fused score 通过 sigmoid/normalize 映射到 [0, 1]，spec 0.70 阈值才能再次有意义
- 或修改 PRD spec 反映 RRF 实际 score 区间

### Gap 3: 🟢 Phase B 未启动（用户当下"列表无差别"问题）

**症状**：所有补充材料无类型差异化排序（讲义 / 讨论 / 考试 / wiki 平起平坐）。

**修复方向**：
- Task 2: `supplementary_reranker.py` 类型权重（lecture 1.0 / discussion 0.9 / exam 0.85 / wiki 0.8 / chat 0.7 / raw 0.6）
- Task 3: wikilink 三级精度（`[[file]]` / `[[file#heading]]` / `[[file#^block_id]]`）

---

## 8. 推荐推进路径

### 选项 A — 修 Cmd+Shift+E 入口（解 Gap 1，让 Phase A 真实可用）

工作量 ~2h，让用户从 Obsidian 流程真正能看到 supplementary。这是 Phase A "实际 ship" 的最后一公里。

### 选项 B — 启动 Phase B（解 Gap 3，类型权重 + 三级精度）

工作量 ~2.5-3h，依赖 Gap 1 已解（否则 Phase B 也走不通用户流程）。

### 选项 C — 整体收尾 Phase A 完整 mini-UAT

让用户在 Obsidian 内验证 6 步全路径（含 happy path 第 3 步），Phase A 通过后 Phase B 启动。需要先解 Gap 1。

**推荐顺序**：A → C → B（Gap 1 修 → mini-UAT 通过 → Phase B 启动）

---

## 9. 文件参考（key code locations）

### Backend

- **chat endpoint**：`backend/app/api/v1/endpoints/chat.py`
- **supplementary search service**：`backend/app/services/supplementary_search_service.py`
- **chat context assembler**：`backend/app/services/chat_context_assembler.py`
- **wikilink context service**：`backend/app/services/wikilink_context_service.py`
- **lancedb client**：`backend/lib/agentic_rag/clients/lancedb_client.py`
- **lancedb index service**：`backend/app/services/lancedb_index_service.py`
- **reference config (source priority)**：`backend/app/core/reference_config.py`
- **vault endpoint**：`backend/app/api/v1/endpoints/vault.py`
- **index endpoint**：`backend/app/api/v1/endpoints/index.py`

### Plugin

- **main.ts**：`frontend/obsidian-plugin/src/main.ts`
- **deployed**：`canvas-vault/.obsidian/plugins/canvas-learning-system/main.js`

### Skill

- **chat-with-context**：`canvas-vault/.claude/skills/chat-with-context/SKILL.md`

### Docker

- **docker-compose.yml**（顶级 mount: `/app` `/lancedb` `/vaults`）
- **canvas-lancedb-data** named volume（external: true）

### 验收单 + Story spec

- `_bmad-output/验收单/Story-2.2-Phase-A-MCP-集成-2026-05-08.md`
- `_bmad-output/implementation-artifacts/epic-2/2-2-supplementary-material-search.md`

---

## 10. 一句话总结

> **Phase A 实现的是"AI 回答时自动列出 vault 内相关学习材料"功能（Story 2.2 的 Task 1+4 子集）。技术核心 = LanceDB + 6 层叠加（两级切分 + bge-m3@Ollama + Tantivy@jieba + 手动 RRF + source priority + SHA-256 增量）+ 9 commits hardening + 部署层三平面独立挂载。当前主要 gap 是 Cmd+Shift+E 入口未传 `user_question` 导致用户 Obsidian 流程走不通 Phase A。**

---

*Generated by 3 parallel Explore agents (LanceDB 6-layer audit + 端到端管道追踪 + 三件套关系) + 9 commits 实测验证 — 2026-05-09*
