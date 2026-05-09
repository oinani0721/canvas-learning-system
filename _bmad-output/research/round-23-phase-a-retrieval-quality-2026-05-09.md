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
