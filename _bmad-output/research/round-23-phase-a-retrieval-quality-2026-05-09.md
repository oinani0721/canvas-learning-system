---
title: Phase A 检索质量调研报告 — 索引污染 + RAG vs Grep + 业界最佳实践
date: 2026-05-09
plan: EPIC1-BMAD-DEV-ASSESS-2026-04-17
story: 2.2-Phase-A-followup
status: 待用户批注后启动修复
audit_method: 3 并行 Explore agent deep explore (污染清单 + 范式对比 + 业界调研)
trigger: 用户实测 5 条召回含 3 噪音 (管道设计 / 2 个 SKILL.md 模板)
---

# Phase A 检索质量调研报告

> **用户原话触发**:
> "你这里返回笔记的精确片段，质量甚至不如 claude code 直接进入 vault 路径启动，然后让它返回我个人需要阅读的相关笔记片段。我们只局限于在我们只放我们笔记文件夹更好一点"

---

## 1. 实测证据（用户截图 ground truth）

用户在节点 `[[节点/规划的分类-1549()]]` 提问"规划分类"，Phase A 召回 Top 5：

| Rank | Score | Title | 用户评价 |
|---|---|---|---|
| 1 | 0.507 | 管道设计 (RAG 系统设计文档) | ❌ **噪音** — 工程文档与"AI 规划"无关 |
| 2 | 0.504 | RS2_MDPs_RL §1.5 总结 | ✅ **强相关** — Planning ≈ Value Iteration |
| 3 | 0.504 | node-chat SKILL 模板 | ❌ **噪音** — Claudian Skill 工具文档 |
| 4 | 0.504 | Disc02 CSPs Course Scheduling | 🔁 **中度相关** — CSP 求解结构与"完全规划"同源 |
| 5 | 0.504 | ai-linked-doc SKILL 关键点 | ❌ **噪音** — Claudian Skill 模板 |

**问题密度: 3/5 = 60% 噪音**。其中 score 0.504 vs 0.507 差仅 0.003 — 用户视角无法区分。

---

## 2. 根因 A: LanceDB 索引污染（实测 4373 chunks / 126 files）

### 2.1 当前真实索引分布

```
4220 chunks / 105 files: raw/  (含 79 video transcripts + 18 explanations + 工程文档)
  55 chunks /   4 files: 根 .md (Dashboard.md / 未命名.md / 2111.md / CLAUDE.md)
  51 chunks /   3 files: .claude/skills/  (3 SKILL.md 模板)
  24 chunks /   4 files: 原白板/
  23 chunks /  10 files: 节点/  (含 TestConceptA-C / UAT-2.5.X-test 测试垃圾)
─────────────────────────────────
4373 chunks / 126 files
```

### 2.2 应跳过但仍在索引内（污染清单）

| 路径 | 文件数 | 原因 | 处理 |
|---|---|---|---|
| `.claude/skills/{node-chat,ai-linked-doc,configure-whiteboard}/SKILL.md` | 3 | `.claude` 不在 skip 列表 | 加黑名单 |
| `*-explanations/` | 41 | **bug**: glob 配置但代码用精确匹配 | 修 glob 或加白名单 |
| `raw/CS188/CLAUDE.md` / `raw/CS188/管道设计.md` | 2 | 工程文档不是学习材料 | 加黑名单 |
| `raw/CS188/Excalidraw/...excalidraw.md` | N | 手绘图，无文字检索价值 | 加黑名单 |
| `raw/CS188/_misc/junk/未命名*.md` | N | 用户自己标注的垃圾 | 加黑名单 |
| `节点/TestConceptA-C` / `UAT-2.5.X-test` | 4 | 测试残留 | 加黑名单 |
| 根 `Dashboard.md` / `未命名.md` / `2111.md` | 3 | 工具文档/未命名 | 加黑名单 |

### 2.3 配置 bug 实证

```python
# backend/app/api/v1/endpoints/metadata.py:481
skip_dirs_str = ".obsidian,.git,.trash,node_modules,outputs,*-explanations"

# backend/lib/agentic_rag/clients/lancedb_client.py:1251
if d not in skip_dirs:  # ⛔ 精确匹配，glob 永不命中
    ...
```

**即 `*-explanations` 这条配置实际不生效**。要么：
- 修代码: 改用 `fnmatch.fnmatch(d, pattern)` 处理 glob
- 或: 改用白名单不需要 glob

---

## 3. 根因 B: RAG semantic vs Claude Code grep 范式差异

### 3.1 三层差异对比

| 维度 | LanceDB (Phase A 当前) | Claude Code 直接 grep |
|---|---|---|
| **召回算法** | bge-m3 1024d Dense + jieba FTS + RRF k=60 | Glob/Grep 字面匹配 + Read |
| **理解层级** | Frozen embedding（不知道 query 是"AI 规划"还是"管道规划"） | LLM 自己拆 query + 决定关键字 + 二次判断相关性 |
| **召回特性** | 近似相似 Top K，必含 1-2 噪音 | 精确匹配窄召回 + LLM 实时过滤 |
| **数学陷阱** | RRF k=60 把 Top 10 vector + Top 10 FTS 压成 0.5 同一带，**失去区分度** | 无（grep 只有命中/不命中） |
| **延迟** | ~50ms cached / ~5s cold | ~100ms-1s 依赖 vault 大小 |
| **Vault 规模** | > 1000 笔记 LanceDB 占优 | < 500 笔记 grep 反而占优 |

### 3.2 用户体感"质量"差异根因

**不是阈值问题，是范式差异**：
- Phase A: 把"判断相关性"外包给 frozen 向量空间（embedding 时编码完）
- Claude Code grep: 把"判断相关性"保留在 LLM 推理回路里（query time 重新评估）

这是 **index-time encoding** vs **query-time reasoning** 的 1 个抽象层差距。

### 3.3 实测证据（Round-23 架构报告 line 65-78）

```
之前 Eigenvalues query 5 条召回 score 全在 0.508 同一带
现在"规划分类" query 5 条召回 score 全在 0.504-0.507 同一带
```

— RRF 数学性质决定 score 区分度被压平，**调阈值无效**。

---

## 4. 根因 C: Skill prompt 已锁死 anchor，但召回 Top K 已含噪音

`commit 40f7aa4` 已加硬约束：Claude 必须 inline 引用 supplementary wikilink。但召回 Top 5 已含 3 噪音 → **Claude 即使 anchor 也只能在噪音里挑** → 用户看到的 wikilink 仍 50%+ 是无关材料。

修 prompt anchor 是必要不充分条件 — 必须配合 **召回阶段的噪音过滤**。

---

## 5. 业界最佳实践（参考 Smart Connections / Copilot for Obsidian / LangChain）

### 5.1 索引范围 (Indexing Scope)

| 做法 | 主流程度 | Canvas 适用 |
|---|---|---|
| **黑名单 (excluded folders)** | ⭐⭐⭐⭐⭐ Smart Connections / Copilot for Obsidian 默认 | ✅ 灵活，新增目录无需配置 |
| **白名单** | ⭐⭐ 较少见 | ⬜ 刚性，新增 vault 子目录要改配置 |
| **Frontmatter `index: false` override** | ⭐⭐⭐ Hack 而非官方契约 | ✅ 单文件精细排除补充 |

**业界默认假设**: vault 内大多数内容应被索引，少数噪音目录排除。

### 5.2 检索质量提升

| 技术 | 业界证据 | Canvas 适用 |
|---|---|---|
| **Metadata pre-filter** | LlamaIndex MetadataFilters 标配 | ✅ Phase A 已有 source_priority，可扩展 |
| **Hybrid retrieval** (语义+BM25+路径) | 显著优于纯 vector | ✅ 已实现 (Dense + FTS) |
| **Cross-encoder Reranker** | SciRerankBench 实测准确率 +27% (SSLI 场景) | ⭐ Phase B 计划用 `gte-reranker-modernbert-base` |
| **LLM rerank** | 把 Top 30 给 Claude 排 Top 5 | ✅ Hybrid 范式 |

### 5.3 关键 insight: SSLI 问题

业界专门为"语义相似但逻辑不相关"问题命名 — **SSLI (Semantically Similar but Logically Irrelevant)**。Reranker 是专治此问题的滤网。

---

## 6. 三个推荐方案对比

### 方案 A — 仅修 skip_dirs（最小可行修复）

```python
# 修 lancedb_client.py:1251 用 fnmatch 处理 glob
import fnmatch
skip = any(fnmatch.fnmatch(d, p) for p in skip_dirs)

# 扩展 metadata.py:481 黑名单
".obsidian,.git,.trash,node_modules,outputs,
 *-explanations,
 .claude,.claudian,
 templates,
 _misc/junk,
 Excalidraw"
```

**工作量**: ~1h
**收益**: 41 个 explanations + 3 个 SKILL.md + 工程文档全部跳过 → 噪音密度从 60% 降到 ~20%
**遗留**: 单文件污染（如 `raw/CS188/管道设计.md`）仍需文件级 pattern

### 方案 B — 白名单 (用户原话支持："我们只放我们笔记文件夹")

```python
# 新增 VAULT_INDEX_INCLUDE_DIRS 配置
include_dirs = "节点,原白板,检验白板,raw"
# 白名单内仍按 skip_dirs 排除（如 raw/_misc/, raw/Excalidraw/）
```

**工作量**: ~1.5h（含 lancedb_client 改造 + index_vault_notes 改造）
**收益**: 杜绝意外暴增（vault 加新目录如 `_drafts/` 不会被索引）
**风险**: 用户加新分类目录（如 `课程/`）需手动加配置

### 方案 C — 黑名单 + frontmatter `rag_index: false` override + LLM rerank（业界推荐）

**核心**: 三层互锁
1. **路径层**: 默认黑名单（同方案 A 扩展）
2. **文件层**: 用户 frontmatter `rag_index: false` 单文件跳过
3. **召回后**: Top 30 给 LLM rerank 出 Top 5（解 SSLI）

**工作量**: ~3-4h（黑名单 ~1h + frontmatter scan ~1h + LLM rerank ~1.5h）
**收益**: 即使有意外索引也被 rerank 过滤；用户对单文件有 override 能力
**业界对齐**: Smart Connections + LangChain MetadataFilters + Pinecone Reranker 三件套

---

## 7. 决策矩阵

| 维度 | 方案 A | 方案 B | 方案 C |
|---|---|---|---|
| 工作量 | 1h | 1.5h | 3-4h |
| 噪音密度降幅 | 60% → 20% | 60% → ~10% | 60% → < 5% |
| 灵活度（加新目录） | ✅ 高 | ❌ 低 | ✅ 高 |
| SSLI 问题（语义相似但无关） | ⬜ 仍有 | ⬜ 仍有 | ✅ 修复 |
| 用户单文件控制 | ❌ 无 | ❌ 无 | ✅ frontmatter |
| 长期可维护性 | 中 | 中 | ⭐⭐⭐ |

---

## 8. 用户批注区（请你在此处批注）

> [!question]+ 你的偏好选择
>
> 在下面写你的决策（或直接用 `Cmd+Shift+A` 批注上面任何段）：
>
> **方案选择**: A / B / C / 混合 = ___
>
> **白名单 vs 黑名单倾向**: ___
>
> **是否接受 frontmatter `rag_index: false` 这种 user 显式 opt-out 机制**: ___
>
> **LLM rerank 是否值得 Phase B 优先做（vs 类型权重精排）**: ___
>
> **其他批注**: ___

### 历史问题追溯（实测发现）

> [!error]+ 2026-05-09 用户实测发现的 RAG 召回噪音
> 用户原批注: "返回笔记的精确片段，质量甚至不如 claude code 直接进入 vault 路径启动"
> 实测 5 条召回中 3 条无关：
> - 管道设计 (RAG 工程文档)
> - node-chat SKILL 模板
> - ai-linked-doc SKILL 模板
> 根因 #1: skip_dirs `*-explanations` glob 不生效（精确匹配 bug）
> 根因 #2: `.claude/` 不在 skip 列表
> 根因 #3: RRF k=60 数学性质压平 score 区分度（0.504-0.507 同一带）

---

## 9. 关键洞察总结

| Insight | 来源 |
|---|---|
| **"工程链路对，但 prompt engineering + 范围控制 + rerank 三层都需要补"** | commit 40f7aa4 已修 prompt anchor，本报告补范围 + rerank |
| **白名单 vs 黑名单的实务最优是混合** | Smart Connections / Copilot 业界共识 |
| **LanceDB 不是"自动好" — 需要黑名单 + rerank 兜底** | SciRerankBench 实测 +27% |
| **Claude Code grep 范式真有优势** — 但仅在小 vault 适用 | < 500 笔记 grep 占优 |
| **Phase A 当前实际索引 4373 chunks / 126 files**（不是早期报告的 2594） | 实测 docker exec 验证 |
| **用户原话"只放笔记文件夹更好"= 白名单意向** | 但业界更推荐黑名单 + override |

---

## 10. 推荐路径（待你批注后启动）

**短期 (P0, 1h)**: 方案 A 修 skip_dirs glob bug + 加黑名单（让噪音降到 20%）

**中期 (P1, 1.5h)**: 选择 B（白名单）或 C 的部分（frontmatter override）

**长期 (Phase B 拓展)**: LLM rerank 解 SSLI 问题，与 Phase B 类型权重精排合并设计

---

## 11. 文件参考

### 关键代码

- 配置入口: `backend/app/api/v1/endpoints/metadata.py:475-494` (skip_dirs 设置)
- 实际过滤逻辑: `backend/lib/agentic_rag/clients/lancedb_client.py:1245-1254` (**glob bug 所在**)
- Source priority: `backend/app/core/reference_config.py` (类型权重)
- Vault notes retriever: `backend/lib/agentic_rag/retrievers/vault_notes_retriever.py` (待加 rerank node)
- Plugin Skill prompt: `canvas-vault/.claude/skills/chat-with-context/SKILL.md` (commit 40f7aa4 已加 anchor)

### 业界来源

- Smart Connections for Obsidian — Local-first semantic search (黑名单 + 单文件 excluded files)
- Pinecone — Rerankers and Two-Stage Retrieval
- LlamaIndex — MetadataFilters
- SciRerankBench (arXiv 2508.08742) — SSLI rerank +27%

### Phase A 累积 commits

```
3bb746e ... 4ff093c (Gap 1 fix Cmd+Shift+E)
40f7aa4 ⭐ prompt engineering hard anchor
```

---

*Generated by 3 parallel Explore agents (索引污染审计 + RAG vs grep 范式对比 + 业界最佳实践调研) — 2026-05-09 持续 ~5 min*

**User：我希望我们的笔记片段精确放回，是进一步提升我们claude code grep 的检索精度和速率，我们的 ChatGPT 可以阅读我们的 gitub 仓库，然后请你指定我们的相关报告和文件，然后给 GPT 提示词，让 ChatGPT 来 deep research 整一个 Phase A ，B，C，以及整一个笔记片段精确返回的设计报告**

---

# 📍 Round-2 调研追加（2026-05-09 11:30 — 6 并行 agent deep explore）

> **触发**：用户在 Claudian 实测 commit fa814e7 hook 自动 RAG 注入后，召回 10 条 supplementary 中 rank 8-10 仍漂移到 `原白板/CS188 lecture 2#Recent Activity / #Concepts` + `节点/lecture 2#2.3 规划代理`（与 query "局部最优陷阱" 完全无关）。
> **6 agent 调研产物已合并到本文件 §12-§17。**

## 12. 6 Agent 调研覆盖矩阵

| Agent | 维度 | 关键产出 |
|---|---|---|
| 1 | Cross-encoder Reranker | **BGE-reranker-v2-m3** (Apache-2.0, 中英双语) + CPU 30 候选 ~260ms + Anthropic 数据 +9 nDCG / -35% 失败率 |
| 2 | Hybrid Search | LanceDB 原生支持 `query_type="hybrid"` + RRFReranker 默认 / 当前代码已 hybrid 但 score 被二次压缩，**问题不在 hybrid 缺失而在 fusion 后处理** |
| 3 | Query Rewrite | HyDE **不值得**（in-domain + BGE-M3 对称编码器原 paper baseline 太弱）；规则剥离意图词 0ms 0token；Anthropic Contextual Retrieval 80% 价值用 frontmatter prepend 即得 |
| 4 | Metadata Filter | LanceDB `where(... prefilter=True)` + heading 黑名单 (`Recent Activity` / `Concepts` / `目录` / `索引`) + source_type 三分类 (`lecture_transcript` / `concept_node` / `whiteboard_section`) |
| 5 | 当前代码根因审查 | **找出 7 个根因**（详见 §13），最致命：白板 heading 没 skip + RRF 分数被 `1/(1+d)` 压缩到 [0.503, 0.508] 全平 |
| 6 | 业界产品对比 | Khoj 两阶段 + Anthropic Contextual + 反例 AnythingLLM 默认 threshold 20% / LightRAG 在已有 wikilink 的 vault 是 anti-pattern |

### 12.1 6 Agent 共识（business-critical）

1. **Hybrid (Dense + BM25 + RRF) 是必修**（Anthropic 数据：失败率 -49%）— 但当前代码已经 hybrid，问题在 **fusion 后处理把分数压平**
2. **Cross-encoder Reranker 是必修**（BGE-reranker-v2-m3，本地 macOS CPU 跑得动）— 加完 +35% 失败率消除（叠加 -67%）
3. **Heading 黑名单 + source_type demote** 是修 rank 8-10 的最直接手段（修复 A + C）
4. **HyDE / MultiQueryRetriever / LightRAG 不要碰**（in-domain BGE-M3 用不上 + wikilink 已是免费高质量人工标注）

---

## 13. 7 个根因（Agent 5 对抗性代码审查）

按致命度排序：

| # | 根因 | 致命度 | 代码位置 | 用户感知现象 |
|---|---|---|---|---|
| **A** | **白板/导航 section 没被 skip** — `skip_dirs` 缺 `原白板`，heading 切分把 `## Recent Activity` `## Concepts` 当普通 section 入库 | 致命 | `lancedb_client.py:1248-1262` + `:2098-2156` | rank 8-9 漂移 |
| **B** | **RRF 分数被 `1/(1+d)` 二次压缩到 [0.503, 0.508]** — `min_relevance=0.30` 完全失效 | 致命 | `lancedb_client.py:2685-2695` + `:2629-2653` | 阈值过滤等于没设 |
| **C** | **`apply_source_priority` 只 boost 不 demote** — `原白板/`/`节点/` 不在 priority 表 → score 保留 0.504 = 跟 lecture 一样高 | 高 | `reference_config.py:66-94` + `data/reference_priority.json` | 无关 source 占位 |
| **D** | **`_elbow_cut` 用绝对差 `0.05`** — RRF 后 gap 实际 0.0005，永远不触发 | 中 | `supplementary_search_service.py:278-298` | 截断失效（兜底 hard_cap 在用） |
| **E** | **`_chunk_text` 不丢弃 < 阈值小段** — `## Recent Activity` 4 行 timestamp 也独立成 chunk | 中 | `lancedb_client.py:147+` | 噪音 chunk 入库 |
| **F** | **没有 cross-encoder rerank 接入** — supplementary 不走 RAGService 主 pipeline 的 rerank 节点 | 致命 | `supplementary_search_service.py:14, 381` | 无二次精排，依赖 RRF 排序 |
| **G** | **Hook endpoint 没用 `cwd` 字段** — `chat.py:575` 定义但 0 引用 → active node 无加权 | 中 | `chat.py:589-696` | 当前节点感知缺失（rank 3-6 命中是巧合） |

---

## 14. 修复方案（按 ROI 排序）

### 14.1 最小修复组合（高 ROI 低风险）— **A + B + C + D**（30-50 行）

**修复 A** — `lancedb_client.py:1248`：扩展 `skip_dirs` + heading 黑名单
```python
skip_dirs = [..., "原白板"]  # 白板 md 不进检索（导航层）
NAV_HEADINGS_BLACKLIST = {"Recent Activity", "Concepts", "目录", "索引", "Tags", "Backlinks"}
# _flush_section 加守卫:
def _flush_section(heading, section_lines, ...):
    if heading.strip() in NAV_HEADINGS_BLACKLIST:
        return
    text = "\n".join(section_lines).strip()
    if "```dataviewjs" in text or len(text) < 50:
        return
```

**修复 B** — `lancedb_client.py:2629`：RRF 后归一化到 [0, 1]，停止 `1/(1+d)` 二次压缩
```python
@staticmethod
def _rrf_fuse(vector_results, fts_results, limit, k=60):
    scores = {}; doc_map = {}
    for rank, r in enumerate(vector_results):
        doc_id = r.get("doc_id", f"v_{rank}")
        scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (k + rank + 1)
        doc_map[doc_id] = r
    for rank, r in enumerate(fts_results):
        doc_id = r.get("doc_id", f"f_{rank}")
        scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (k + rank + 1)
        if doc_id not in doc_map: doc_map[doc_id] = r
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:limit]
    max_score = max((s for _, s in ranked), default=1.0) or 1.0
    results = []
    for doc_id, raw_score in ranked:
        doc = doc_map[doc_id].copy()
        normalized = raw_score / max_score  # ⭐ 归一化 [0, 1]
        doc["_rrf_score"] = normalized
        doc["_distance"] = 1.0 - normalized
        results.append(doc)
    return results
```

**修复 C** — `data/reference_priority.json`：加白板/节点 demote 规则
```json
{
  "source_priorities": [
    {"pattern": "videos/lectures/**",        "weight": 1.5},
    {"pattern": "videos/discussions/**",     "weight": 1.4},
    {"pattern": "节点/**",                   "weight": 0.85, "label": "派生节点（讨论容器，未必详细）"},
    {"pattern": "原白板/**",                 "weight": 0.30, "label": "白板（导航层禁推）"},
    {"pattern": "*-explanations/**",         "weight": 0.50}
  ]
}
```

**修复 D** — `supplementary_search_service.py:278`：elbow 改用相对 drop ratio
```python
def _elbow_cut(materials, drop_threshold: float = 0.30, hard_cap: int = 15):
    if not materials: return materials
    cut_idx = len(materials)
    for i in range(1, len(materials)):
        prev = materials[i-1]["score"]; curr = materials[i]["score"]
        if prev <= 0: continue
        rel_drop = (prev - curr) / prev  # ⭐ 相对降幅
        if rel_drop > drop_threshold:
            cut_idx = i; break
    return materials[: min(cut_idx, hard_cap)]
```

**预期效果**：rank 8-9 不存在（白板 skip）；rank 10 被 elbow 切；剩 7 条全是真 lecture。

### 14.2 完整修复（含 cross-encoder rerank）— **A + B + C + D + F**

新增 `backend/app/services/reranker_service.py`（详见 Agent 1 报告完整代码骨架）。

延迟预算（CPU M-Max）：30 候选 batch=16 ≈ 130-200ms（在 5s hook 预算内余 4s+）

冷启动：FastAPI lifespan 调一次 `_load_reranker()` warm up。

预期效果（Anthropic 数据）：top-20 失败率 5.7% → 1.9%（**-67%**）

### 14.3 不要碰的（业界反例）

- ❌ **HyDE** — in-domain + BGE-M3 对称编码器，原 paper baseline (Contriever 2022) 太弱
- ❌ **MultiQueryRetriever** — 5s hook 预算下 N 次并行检索 + LLM 调用太贵
- ❌ **LightRAG LLM 抽实体** — vault 已有 wikilink 是免费高质量人工标注
- ❌ **AnythingLLM 风格 similarity threshold** — 硬阈值丢答案

---

## 15. 关键决策点（用户批注区 — 4 个 question callout）

> [!question]+ Q1: 修复优先级（最重要）
> - [ ] 选项 1: 先做 **A+B+C+D**（最小集合，30-50 行，预期 80% 解决）→ 验证 → 再决定要不要 reranker
> - [ ] 选项 2: 一次性做 **A+B+C+D+F**（含 cross-encoder reranker，多 ~100 行 + 模型下载）→ 直接拿到 95%+ 解决
> - [ ] 选项 3: 暂不动代码，先 commit 调研 + 给 ChatGPT prompt → 等 ChatGPT 反馈再决定
> 
> **你的选择**: ___

> [!question]+ Q2: 白板是否完全 skip 索引（修复 A 核心争议）
> - [ ] 完全 skip 白板目录（`skip_dirs += ["原白板"]`）— 简单，但用户在白板写的真知识会丢
> - [ ] 只 skip 导航 heading（`Recent Activity` / `Concepts`）— 白板正文仍可索引
> - [ ] 双管齐下（skip 白板目录 + heading 黑名单 双重防御）
> 
> **你的选择**: ___

> [!question]+ Q3: 解题专用 skill 是否要新建
> - [ ] 暂不新建，先把 hook 召回质量修好（baseline 改善后 hook 已够用）
> - [ ] 新建 `/study-question` skill（显式触发深度模式：query rewrite + multi-hop + 长 context + 20 条召回）
> - [ ] hook + skill 双轨：hook 给 baseline 5 条；用户深挖时用 `/study-question` 拿 20 条 + 多 hop
> 
> **你的选择**: ___

> [!question]+ Q4: ChatGPT 对抗性审查的 scope
> - [ ] 仅审查 §13 的 7 个根因 + §14 的修复方案（窄）
> - [ ] 整个 RAG 设计（含 chunking / embedding / Hybrid / rerank / Anthropic Contextual / Khoj 对比）
> - [ ] 让 ChatGPT 提出 2 套替代方案做对抗（如：抛弃 RAG 用 grep + LLM rerank vs 当前 RAG + reranker）
> 
> **你的选择**: ___

---

## 16. ChatGPT Deep Research 对抗性审查 Prompt（完整可复制版）

> **使用方式**：
> 1. 在 ChatGPT 选 `Deep Research` 模式（GPT-5 / o3 都行）
> 2. 把下面整段（含 ``` 代码块）原样复制粘贴
> 3. ChatGPT 会先跑 5-10 分钟 web research + 读 GitHub 仓库，再给报告

```markdown
# Tech Decision: Phase A 笔记 RAG 召回精度 — 对抗性审查 + 设计完整报告

## Context

我在做一个本地 Obsidian vault 笔记 RAG 系统，给我（学生）解题时辅助召回相关教学笔记。

**仓库**: https://github.com/oinani0721/canvas-learning-system （public，请直接 clone 阅读）
**关键调研产物（先读）**:
- `_bmad-output/research/round-23-phase-a-retrieval-quality-2026-05-09.md` — 本次完整调研（Round-1 + Round-2，含 6 agent 报告 + 7 根因 + 4 决策点）
- `backend/app/services/supplementary_search_service.py` — RAG hook 主 pipeline
- `backend/app/api/v1/endpoints/chat.py:589-696` — UserPromptSubmit hook endpoint
- `backend/lib/agentic_rag/clients/lancedb_client.py:1248-2700` — chunker + LanceDB hybrid + RRF fuse
- `backend/app/core/reference_config.py` + `backend/data/reference_priority.json` — source priority
- `canvas-vault/.claude/settings.json` — vault 级 UserPromptSubmit hook 注册
- `canvas-vault/原白板/CS188 lecture 2.md:25-95` — 实证：白板含 ## Concepts + ## Recent Activity 噪音

**项目背景**:
- 学生用 Obsidian + Claudian sidebar，提问触发 Anthropic Claude Code SDK UserPromptSubmit hook
- Hook curl POST 到 backend `/rag/enrich-hook` → backend 调 `search_supplementary` → 返回 `additionalContext` (XML)
- SDK 自动 prepend additionalContext 到 system context → Claude 拿 vault wikilink 真材料 + Read tool 验证 + 回答
- 当前 stack: Python 3.11 + FastAPI + LanceDB + bge-m3 (1024d) + jieba FTS + RRF k=60 + 无 reranker

## The Problem

用户实测案例：
- query: "什么是局部最优陷阱怎么解决"
- 返回 10 条 supplementary，rank 1-7 完美命中 `lecture 4 #6.4.1 解决局部最优陷阱的方法`
- **rank 8-9 漂移到 `原白板/CS188 lecture 2#Recent Activity` 和 `#Concepts`**（白板导航 section，纯审计日志，0 学习价值）
- **rank 10 漂移到 `节点/lecture 2#2.3 规划代理`**（话题完全错位 — 用户问的是 lecture 4 局部搜索，召了 lecture 2 规划代理）

噪音密度 30%（10 条中 3 条无关）。

## Our 7 Root Causes Diagnosis

详见仓库 round-23 文件 §13。摘要：
- A. `skip_dirs` 缺 `原白板`，heading 切分把导航 section 当普通 section 入库
- B. RRF 分数被 `1/(1+d)` 二次压缩到 [0.503, 0.508] 全平，`min_relevance=0.30` 失效
- C. `apply_source_priority` 只 boost 不 demote，`原白板/` `节点/` 不在 priority 表
- D. `_elbow_cut` 用绝对差 0.05，但 RRF 后 gap 是 0.0005
- E. `_chunk_text` 不丢弃小段，4 行 timestamp 也成 chunk
- F. 没有 cross-encoder rerank 接入 (`supplementary_search_service.py:14, 381` 注释 "Phase B 才做"，但 Phase A 已暴露此问题)
- G. Hook endpoint 收 `cwd` 字段但 0 引用，active node 没参与排序

## Our Proposed Fix (Round-2 Plan)

详见仓库 round-23 §14。两套：
- **最小集合**: A+B+C+D (30-50 行) — 预期解决 80%
- **完整集合**: A+B+C+D+F (含 BGE-reranker-v2-m3, +100 行) — 预期 95%+

## What I Need From You (Adversarial Review)

请你做 5 件事：

### 1. 验证 7 个根因诊断
- 直接读仓库源码，验证每个根因确实存在（不要相信我的描述，自己 grep 代码）
- 找出我们 **遗漏的根因**（H, I, J...）
- 找出我们 **过度诊断的根因**（实际不是问题，但被我们当成问题修）

### 2. 对抗性挑战修复方案
- 修复 A 的"白板完全 skip"会不会丢用户在白板写的真知识？
- 修复 B 的 RRF 归一化 [0,1] 会不会破坏 source_priority 乘法权重的语义（boost 1.5 应该让 weight 1.0 的 0.5 → 0.75，而不是被 normalize 抵消）？
- 修复 C 的 `节点/**` weight=0.85 是否合理？节点是用户主动派生，可能比 raw transcript 更精炼，weight 应该 ≥ 1.0？
- 修复 D 的 30% relative drop 阈值 — 你认为 50% 还是 20% 更稳健？

### 3. 提出 2 套对抗替代方案
**方案 X**: 抛弃 RAG，回归 Claude Code grep 范式
- LLM 自己拆 query → 决定关键词 → ripgrep → Read 文件 → LLM 二次过滤
- 优势：query-time reasoning 比 frozen embedding 更准
- 劣势：vault > 1000 文件慢、需要 LLM 介入决定关键词
- 我们 vault 当前 ~126 files / 4373 chunks，是不是还在 grep 占优区间？

**方案 Y**: Anthropic Contextual Retrieval (chunk 前置 LLM 上下文摘要)
- 用 Claude Haiku + prompt cache 给每个 chunk 写课程+章节上下文
- 索引时一次性 $1/M token
- 替代/补充 我们的修复 A+C？

请对比我们的方案 (A+B+C+D[+F]) vs 方案 X vs 方案 Y，给出**决策矩阵 + 推荐**。

### 4. 设计 Phase A/B/C 完整路线（用户原话需求）

用户原话："让 ChatGPT 来 deep research 整一个 Phase A，B，C，以及整一个笔记片段精确返回的设计报告"

请按业界 RAG 项目的 Phase 划分给完整路线：
- **Phase A (MVP, 当前)**: 修 7 根因 + 接 reranker，目标"召回精度 80% → 95%"
- **Phase B (深度模式, 解题场景)**: 是否需要新建 skill 显式触发？query rewrite + multi-hop wikilink 图遍历 + 长 context？
- **Phase C (长期演进)**: graph-aware（利用 wikilink + Graphiti KG）？personalization（学习历史 weight）？多模态（lecture 视频帧+音频）？

每个 Phase 给出：
- 假设/前提
- 核心 deliverable（具体到代码改动）
- 工作量估算（小时）
- 验收 metric（如何量化"成功"）
- 风险 + 兜底

### 5. 笔记片段"精确返回"机制设计

用户的核心诉求是 **笔记片段精确返回** — 即用户提问后，返回的 wikilink 必须能精确跳到正确的 heading anchor，而不是"接近的笔记"。

请深度调研 + 设计：
- chunk → wikilink anchor 的精确映射（heading path 怎么编码）
- inline citation 在 LLM 回答里的强制约束（commit 98dbc2d 已强制 Read，但是否要进一步约束句子级 citation）
- 用户点击 wikilink 后跳转的 100% 命中率（commit 275a201/c3c06eb 修过 wikilink anchor 的 raw vs clean 差异，但仍可能有 edge case）
- "5 句话内必引 1 wikilink" 这种 anti-hallucination 强制约束业界是否有先例

## Constraints (你的方案必须满足)

- **本地 macOS M-series**（M1 Max / M3 Max），无 NVIDIA GPU
- **5s hook 总延迟预算**（用户感知）
- **零 fork Claudian**（不动 Obsidian 插件本体）
- **bge-m3 是已锁定 embedding**（不接受换 embedding 的方案）
- **Apache-2.0 / MIT 兼容**，避免 GPL/CC-BY-NC
- **优先 LanceDB 原生 API**，自定义 reranker 也用 LanceDB Reranker subclass

## Desired Output Format

```
1. 7 根因验证清单（per-root-cause 验证 + 漏诊补充）
2. 4 个修复方案对抗结论（A/B/C/D 各打 0-10 分 + 改进建议）
3. 方案 X / Y 决策矩阵（vs 我们当前方案）
4. Phase A/B/C 完整路线（含工作量 + verification metric）
5. 笔记片段精确返回机制设计（含 anchor 编码 + citation 约束 + edge case 对策）
6. 你的最终推荐（按 priority 排）
7. 你认为我们最大的盲点是什么（一段长答）
```

## What I Specifically Want You to Push Back On

不要只是赞美我们的方案。请尖锐地：
- 找出我们 in-domain 拒绝 HyDE 的论证是否过度（in-domain 数据 + BGE-M3 双语真的就完全免疫 query-doc 空间漂移吗）
- 挑战 BGE-reranker-v2-m3 在 macOS CPU 上的 ~260ms 延迟是否真的够用（M1 Max 实测 vs 报告的 M3 Max？冷启动？）
- 我们认为 LightRAG "在已有 wikilink 的 vault 是 anti-pattern" — 但 wikilink 是稀疏的（用户没标的概念关系无法发现），LLM 抽实体可能补漏？
- 我们 hook 5s 预算 + 30 候选 reranker 是合理的吗？业界 production 是 100 候选 → 10 还是 30 → 5？

## Output Length

不限。Phase A/B/C 的 deliverable 越细越好，工作量估算到具体函数级。
```

---

## 17. 文件参考（修复实施时读这些）

### 关键代码（修复 A-G 涉及）

- chunker / skip_dirs / heading 切分：`backend/lib/agentic_rag/clients/lancedb_client.py:1248-1262, 2098-2222`
- RRF fuse + score 转换：`backend/lib/agentic_rag/clients/lancedb_client.py:2629-2700`
- supplementary 主 pipeline：`backend/app/services/supplementary_search_service.py:36-298`
- hook endpoint（cwd 待用）：`backend/app/api/v1/endpoints/chat.py:589-696`
- source priority 配置：`backend/data/reference_priority.json` + `backend/app/core/reference_config.py:66`
- vault hook 注册：`canvas-vault/.claude/settings.json`

### 实证数据样本

- 噪音 chunk 实证：`canvas-vault/原白板/CS188 lecture 2.md:25-95`（含 ## Concepts + ## Recent Activity）
- 命中标杆：`canvas-vault/raw/CS188/videos/lectures/lecture 4/lecture 4.md` #6.4.1

### 业界来源汇总

- **Reranker**: [BGE-reranker-v2-m3 HF](https://huggingface.co/BAAI/bge-reranker-v2-m3) / [Pinecone Two-Stage](https://www.pinecone.io/learn/series/rag/rerankers/)
- **Hybrid**: [LanceDB Hybrid Docs](https://docs.lancedb.com/search/hybrid-search) / [Anthropic Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval)
- **Query Rewrite**: [HyDE arxiv 2212.10496](https://arxiv.org/abs/2212.10496) / [Adaptive HyDE arxiv 2507.16754](https://arxiv.org/html/2507.16754v1) (25% failure case)
- **教育 RAG**: [Khoj GitHub](https://github.com/khoj-ai/khoj) / [ObsidianRAG GitHub](https://github.com/Vasallo94/ObsidianRAG)
- **反例**: [AnythingLLM Issue #3649](https://github.com/Mintplex-Labs/anything-llm/issues/3649) / [LightRAG arxiv 2410.05779](https://arxiv.org/html/2410.05779v1)

---

*Round-2 generated by 6 parallel general-purpose agents (cross-encoder reranker / hybrid search / query rewrite / metadata filter / 当前代码根因审查 / 业界教育 RAG 案例) — 2026-05-09 持续 ~12 min*

**Plan Anchor**: EPIC1-BMAD-DEV-ASSESS-2026-04-17

