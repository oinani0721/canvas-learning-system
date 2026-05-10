---
title: ChatGPT Deep Research 提示词包 — Phase A/B/C 笔记片段精确返回 设计调研
date: 2026-05-09
plan: EPIC1-BMAD-DEV-ASSESS-2026-04-17
trigger: 用户实测体感"Claude Code grep > LanceDB embedding"，要求 GPT DR 论证整套范式
purpose: 给用户复制粘贴的 ChatGPT DR 工具包
---

# ChatGPT Deep Research 提示词包

> **用户决策**: 不直接选 A/B/C 修复方案，而是用 ChatGPT Deep Research 重新审视"笔记片段精确返回"整套范式（Claude Code grep vs LanceDB embedding vs Hybrid），输出 Phase A/B/C 完整设计报告。

---

## 📋 使用说明

1. 把 `## 提示词全文` 段全文复制到 ChatGPT (启用 Deep Research 模式)
2. ChatGPT 会自己读取 GitHub 仓库的列出文件
3. 期待 ChatGPT 返回设计报告（结构按 `## 期望输出 schema`）
4. 把 ChatGPT 返回的报告 ship 到 `_bmad-output/research/round-23-chatgpt-dr-response-2026-05-09.md`
5. Claude 读 GPT 报告 → 实施

---

## 提示词全文（复制粘贴给 ChatGPT）

```markdown
# Tech Decision: Phase A/B/C 笔记片段精确返回 — 范式选择

## Project Context

**Canvas Learning System** — 一个基于 Obsidian + Claudian (Claude Code 侧栏) 的 PKM 学习系统。
仓库: https://github.com/oinani0721/canvas-learning-system (private worktree branch)
Worktree: feature-obsidian-hybrid-dev

### 当前架构
- **前端**: Obsidian plugin (TypeScript) + Claudian (Claude Code as sidebar)
- **后端**: FastAPI (Python async) + Neo4j (KG) + LanceDB (vector) + Ollama bge-m3 1024d
- **LLM**: Anthropic Claude API (主) + Gemini (仅 Graphiti) + Ollama Qwen3:8b (fallback)
- **Skill 引擎**: Claude Code Skill (Markdown 文件 + frontmatter)
- **vault 结构**: 节点/(扁平概念池) + 原白板/(MOC) + 检验白板/ + raw/(原始材料)

### 当前 Phase A 实现（已 ship 12 commits）
- LanceDB hybrid 检索 (bge-m3 Dense + jieba FTS + 手动 RRF k=60)
- 6 层技术栈：tiktoken/heading 切分 + bge-m3 embed + Tantivy FTS + RRF 融合 +
  source priority + SHA-256 增量索引
- 实际索引 4373 chunks / 126 files
- 用户在 Obsidian 节点页 Cmd+Shift+E → backend 拼 prompt 含 `<supplementary_materials count="N">`
  → Claudian 调 chat-with-context Skill → Claude 基于 prompt 回答

## Question

用户实测体感: **"返回笔记的精确片段，质量甚至不如 claude code 直接进入 vault 路径启动，
然后让它返回我个人需要阅读的相关笔记片段"**。

具体证据:
- Top 5 召回 3 条噪音（管道设计 = RAG 工程文档 / 2 个 Claudian Skill 模板）
- Score 区分度被 RRF k=60 压平到 0.504-0.507 同一带，无法用阈值过滤
- LanceDB 是 frozen embedding，不知道 query 是"AI 规划"还是"管道规划" → 噪音漂移
- Claude Code grep 是 agent-style: LLM 自己拆 query + 同时 grep 多关键字 + 二次判断

### 三个对立设计范式

**方案 X (LanceDB-first，当前实现)**:
- bge-m3 + jieba + RRF + source priority
- 优势: vault > 1000 笔记时 latency ~50ms cached
- 劣势: 噪音密度 60%、frozen embedding 无任务感知、score 区分度差

**方案 Y (Claude-Code-grep-first，用户倾向)**:
- LLM 实时拆 query → Glob/Grep/Read 直接读 vault → LLM 判断相关性
- 优势: query-time reasoning，每条都过 LLM 二次过滤，召回精度高
- 劣势: vault > 1000 笔记 grep 命中爆炸、LLM token 成本高、延迟 1s+

**方案 Z (Hybrid, 业界推荐)**:
- LanceDB 召回 Top 30 (recall layer)
- Cross-encoder reranker (gte-reranker-modernbert-base 149M / Qwen3-4B) 排出 Top 5
- 业界证据: SciRerankBench SSLI 准确率 +27%

## Specific Sub-Questions

请 ChatGPT Deep Research 回答以下 7 个问题:

### Q1: 范式选择
当 vault 规模 < 200 笔记 / 200-1000 笔记 / > 1000 笔记 三档时，
方案 X / Y / Z 各自的检索精度 (Recall@5, Precision@5) 实测对比？
（请引用业界 benchmark / paper / blog 实测数据，不要凭直觉）

### Q2: Claude Code grep 范式实施细节
如果选方案 Y (LLM-driven grep)，具体实施 3-5 步：
- LLM 怎么从用户 query 提取候选关键字（中英文 + 同义词扩展）
- 多关键字 grep 命中后怎么去重 + 排序？
- 单文件命中 N 处时怎么选最相关的 chunk 返回？
- vault 内不同目录权重怎么处理？
- 是否需要 query refinement (failed grep → rephrase → retry)？

### Q3: Hybrid (Z) 的 reranker 具体选择
- gte-reranker-modernbert-base (149M, MIT) vs Qwen3-Reranker-4B (Apache 2.0)
- BGE-Reranker-v2-m3 (568M) 和 cohere/rerank-3.5 (商业) 对比
- Mac M-series Metal GPU 部署可行性
- reranker 单 query 延迟实测 (50-500ms 区间，给具体数据)

### Q4: Obsidian PKM 社区最佳实践
Smart Connections / Copilot for Obsidian / Khoj / Logseq / Notion AI 当前怎么做检索？
他们用 LanceDB / FAISS / Qdrant / 还是直接 grep？为什么？社区用户体感如何？

### Q5: Frontend agent-style RAG 模式
LangChain Agent / LlamaIndex Agent / Haystack Agent 等 "agent-tool-orchestration" 范式
是否本质上就是方案 Y 的实现？最近一年 (2025) 这个范式有哪些 production case？

### Q6: 索引污染（节点池白名单 / 黑名单 / frontmatter override）
用户当前体感的"噪音"主因是路径污染（管道设计 / SKILL.md 进了索引）。
- Smart Connections 用 "Manage excluded folders" UI
- LangChain 的 metadata filter 怎么 schema 化设计？
- frontmatter `index: false` 是否社区标准 contract？
- 推荐 Canvas Learning System 用什么 schema 让 vault 内容可控制索引行为？

### Q7: Phase A/B/C 完整设计建议
基于 Q1-Q6 的回答，请输出:
- Phase A (基础检索) 应该怎么设计？保留 LanceDB 还是切到 grep？
- Phase B (精排) 应该用 cross-encoder reranker 还是 LLM rerank 还是 type-weight？
- Phase C (高级) 应该补什么？block-level 锚点 / Re2G iterative retrieval / agent loop?
- 三个 Phase 的工作量估算（人天）+ 风险清单

## Constraints

- Obsidian plugin (TypeScript) + Claudian Skill (Markdown) — 不能改 Obsidian 内核
- Backend Python FastAPI async + LanceDB 已有 4373 chunks 索引（不希望全废）
- Mac M-series 本地部署优先（含 Metal GPU 加速能力）
- 用户是非技术 PM，最终方案需"用户透明" — 不能要求用户配置复杂参数
- 真实用户场景: 单 vault 规模 ~200 md (节点 + 原白板 + raw)，未来可能扩展到 ~1000 md
- 学习场景: 用户问"X 是什么"/"X 与 Y 的关系"/"举例子"/"出题考我" 4 类查询

## What We Tried (Already Done)

1. **9 个工程根因 + fix** (timeout / tier-2 fallback / docker volume / BGEM3 cold-start /
   external volume / ListTablesResponse / mount nesting / asyncio imports / Ollama env)
2. **Plugin Cmd+Shift+E 真实触发 Phase A** (Gap 1 fix, commit 4ff093c)
3. **Prompt engineering hard anchor** (commit 40f7aa4) — Claude 必须 inline 引用 vault wikilink
4. **3 并行 Explore agent 调研** (污染审计 + 范式对比 + 业界最佳实践)
5. **实测 supplementary 5 条召回** — 60% 噪音 (3/5 是无关材料)

仍不清楚: 应该完全切到方案 Y / 用方案 Z hybrid / 还是 X+Z 混合，
以及方案 Y 在 200-1000 vault 规模下是否真的可行 (token cost / latency 是否爆炸)。

## Desired Output Schema

请按以下结构返回设计报告:

### Executive Summary (200 字)
推荐方案 + 一句话总结收益 + 一句话总结风险

### 1. 范式实测对比矩阵
| 维度 | 方案 X (LanceDB) | 方案 Y (Grep) | 方案 Z (Hybrid) |
|---|---|---|---|
| Recall@5 (200 vault) | ? | ? | ? |
| Recall@5 (1000 vault) | ? | ? | ? |
| Precision@5 (含噪音密度) | ? | ? | ? |
| Latency P50 / P95 | ? | ? | ? |
| Token Cost / query | ? | ? | ? |
| 实施复杂度 | ? | ? | ? |
| (引用具体 benchmark / paper) | | | |

### 2. Phase A/B/C 重新设计
- Phase A (基础检索) - 范式 + 工作量 + AC
- Phase B (精排 / agent loop) - 同上
- Phase C (高级特性: block-level / iterative / multi-vault) - 同上

### 3. 关键技术选型
- Reranker model 推荐 + 理由
- 节点池白名单 / 黑名单 / frontmatter override schema
- 索引粒度 (chunk-level / heading-level / block-level)
- 检索算法 (RRF / weighted fusion / late interaction / ColBERT)

### 4. 实施风险清单
- 工程债 (4373 chunks 现有索引怎么处理)
- 用户体验风险 (latency / 噪音 / 学习曲线)
- LLM 成本风险

### 5. 引用 (References)
- 必须含 5+ 业界来源 (paper / blog / GitHub repo / benchmark)
- 优先 2024-2025 年新内容
- 优先 Obsidian / Khoj / LangChain Agent 等同领域

### 6. Open Questions (留给后续 Claude 实施时澄清)
- 列 3-5 个需要 Canvas 团队再决策的问题

请尽量在 6000-8000 字内完成，重证据 (引用具体数据 + 来源)，少凭直觉。
```

---

## 📂 GitHub 仓库相关文件清单（供 ChatGPT 阅读）

ChatGPT 在 deep research 时应优先读以下文件：

### 🌟 核心设计报告（必读）

| 文件 | 描述 |
|---|---|
| `_bmad-output/research/round-23-phase-a-architecture-report-2026-05-09.md` | Phase A 完整架构 6 层技术栈 + 端到端时序 + 三件套定位 |
| `_bmad-output/research/round-23-phase-a-retrieval-quality-2026-05-09.md` | 检索质量审计 + 索引污染清单 + 三方案对比 + 用户批注 |
| `_bmad-output/implementation-artifacts/epic-2/2-2-supplementary-material-search.md` | Story 2.2 spec (含 Phase A/B/C Task 拆分) |

### Backend 关键代码（次重要）

| 文件 | 描述 |
|---|---|
| `backend/app/services/supplementary_search_service.py` | Phase A 主服务：tier-1/tier-2 双层搜索 + RRF + source priority |
| `backend/app/api/v1/endpoints/chat.py` | enrich-context endpoint，Phase A Step 5 注入点 |
| `backend/lib/agentic_rag/clients/lancedb_client.py` | LanceDB hybrid 实现 + RRF k=60 + 切分 + embed |
| `backend/app/api/v1/endpoints/metadata.py` | skip_dirs 配置入口 (line 475-494) — **glob bug 所在** |
| `backend/app/core/reference_config.py` | Source priority 类型权重定义 |

### Frontend / Skill（用户接入路径）

| 文件 | 描述 |
|---|---|
| `frontend/obsidian-plugin/src/main.ts` | Plugin 主文件 (含 handleChatWithContext + UserQuestionModal) |
| `canvas-vault/.claude/skills/chat-with-context/SKILL.md` | Skill prompt 含硬约束 #9-11 (commit 40f7aa4 anchor) |

### 业界对照（外部参考）

ChatGPT 应主动 web search 以下：
- Smart Connections for Obsidian (https://smartconnections.app/) — 黑名单 + 单文件 excluded
- Copilot for Obsidian — 同类
- Khoj (https://github.com/khoj-ai/khoj) — Obsidian + LLM PKM 开源参考
- LangChain Agent (https://python.langchain.com/docs/concepts/agents/) — agent-tool-orchestration
- LlamaIndex MetadataFilters (https://docs.llamaindex.ai/) — pre-filter
- Pinecone Reranker (https://www.pinecone.io/learn/series/rag/rerankers/) — Two-Stage Retrieval
- SciRerankBench (arXiv 2508.08742) — SSLI rerank benchmark
- BAAI bge-reranker-v2-m3 (https://huggingface.co/BAAI/bge-reranker-v2-m3)
- gte-reranker-modernbert-base (149M, MIT)
- Qwen3-Reranker-4B (https://huggingface.co/Qwen)

---

## 期望输出 schema（ChatGPT 应返回）

按提示词内 "Desired Output Schema" 段格式，预期 6000-8000 字含：

1. Executive Summary (~200 字 - 推荐方案 + 收益 + 风险)
2. 范式实测对比矩阵 (X/Y/Z × Recall/Precision/Latency/Cost/复杂度)
3. Phase A/B/C 重新设计（范式 + 工作量 + AC）
4. 关键技术选型（reranker + 索引粒度 + 检索算法 + 白/黑名单 schema）
5. 实施风险清单
6. References (5+ 来源，2024-2025 优先)
7. Open Questions (3-5 个待 Canvas 团队决策)

---

## 🔄 ChatGPT 返回后的工作流

1. 你把 ChatGPT 返回的报告 ship 到 `_bmad-output/research/round-23-chatgpt-dr-response-2026-05-09.md`
2. 在 Obsidian 内打开通知 Claude
3. Claude 读 GPT 报告 + 验证关键 claims（用并行 Explore agent 跑 cross-check）
4. Claude 综合 GPT + 实测 → 产出 Phase A/B/C 实施 Story spec
5. 用户在 Obsidian 内批注 Story spec
6. Claude 启动 dev → ship → mini-UAT 闭环

---

## 🎯 关键 insight 备忘

| Insight | 来源 |
|---|---|
| 用户原话"提升 claude code grep 检索精度和速率" | 本批注 |
| Frozen embedding 无任务感知是 RAG 通病 | 业界共识 |
| RRF k=60 数学性质压平 score 区分度 | Phase A 实测证据 |
| Agent-style retrieval (LLM 自拆 query) 是 2024-2025 年 RAG 范式升级方向 | LangChain / LlamaIndex Agent |
| Cross-encoder reranker 解 SSLI 问题 +27% | SciRerankBench |
| Smart Connections 默认黑名单 + 单文件 excluded files (社区习惯) | Obsidian 社区 |
| Claude Code 直接 grep 在小 vault (< 500 笔记) 体感优 | 用户实测 |

---

## 文件参考

- 当前批注源: `_bmad-output/research/round-23-phase-a-retrieval-quality-2026-05-09.md` (line 285)
- 架构报告: `_bmad-output/research/round-23-phase-a-architecture-report-2026-05-09.md`
- Story 2.2 spec: `_bmad-output/implementation-artifacts/epic-2/2-2-supplementary-material-search.md`
- _bmad-output CLAUDE.md (DR 模板来源): `_bmad-output/.claude/CLAUDE.md` line 24-58

---

*Generated 2026-05-09 03:01 — V1 prompt 完成。**V2 Round-2 完善版见下方 §V2。***

---

# V2 — Round-2 6 Agent 调研后的对抗性审查 Prompt（2026-05-09 12:43 升级）

> **V2 vs V1 关系**：V1 问"X/Y/Z 范式选哪个"（开放探索）；V2 问"hook 已 ship + 7 根因 + 4 修复方案被你挑战，请重新设计 Phase A/B/C 路线 + 笔记片段精确返回机制"（聚焦执行）。
>
> **V1 ChatGPT 已回了一份**: `_bmad-output/research/round-23-chatgpt-dr-result-and-synthesis-2026-05-08.md`（371 行，作为前次基线 — V2 ChatGPT 应审视此结论是否被 fa814e7 推翻）。
>
> **V2 触发**：commit fa814e7 ship UserPromptSubmit hook 后，用户实测 query "局部最优陷阱" 返回 10 条，rank 1-7 完美 + **rank 8-10 漂移到无关材料** → 6 并行 agent 全管道审查找出 7 根因 + 提出 A+B+C+D[+F] 修复方案 → 需要 ChatGPT 对抗审查 + 重新设计 Phase A/B/C。

## V2 改进点（vs V1）

| 维度 | V1 | V2 |
|---|---|---|
| Branch 提示 | 没说 | ✅ 明确 `worktree-feature-obsidian-hybrid-dev` |
| 文件清单 | 8 个，无行号 | ✅ 18 个，每个含 line 范围 + 一句话用途 |
| GitHub URL 锚点 | 没给 | ✅ URL 模板含 `#L<a>-L<b>` |
| Tier 分层 | 没分 | ✅ T0 必读 6 类 + T1 选读 5 类 |
| Commits 时间线 | 没有 | ✅ 10 commits + Phase A 演进 6 阶段 |
| 焦点 | 范式选择（开放） | 7 根因诊断 + 修复对抗 + Phase A/B/C 重设计 |
| 7 个对抗任务 | 范式 Q1-Q7 | ✅ 5 个 Adversarial Tasks（含"明确要 GPT push back 的 4 个论点"） |

## V2 调研产物（已 ship 进仓库）

- `_bmad-output/research/round-23-phase-a-retrieval-quality-2026-05-09.md` (Round-2 §12-§17 共 346 行追加)
  - §12 6 agent 共识矩阵
  - §13 7 根因 file:line 级诊断
  - §14 修复方案 (A+B+C+D 最小 / +F 完整) 含代码骨架
  - §15 用户决策 4 question callout
  - §16 V2 完整 prompt
  - §17 文件参考

## V2 提示词全文（复制下面整段给 ChatGPT Deep Research）

> 使用方式：
> 1. ChatGPT → 选 Deep Research 模式（GPT-5 / o3）
> 2. 复制下面 `~~~~~~` 包裹的整段（不含外层包裹符）
> 3. 等 5-15 min
> 4. 回填到 `_bmad-output/research/round-23-chatgpt-dr-response-v2-2026-05-09.md`

~~~~~~
# Tech Decision: Phase A 笔记 RAG 召回精度 — 对抗性审查 + 设计完整报告

## Context

我在做一个本地 Obsidian vault 笔记 RAG 系统，给我（学生）解题时辅助召回相关教学笔记。

**仓库**: https://github.com/oinani0721/canvas-learning-system （public）
**Branch**: `worktree-feature-obsidian-hybrid-dev` （⚠️ 本次所有改动在此分支，不是 main。请先在 GitHub UI 切到此 branch 再读文件，或 `git clone -b worktree-feature-obsidian-hybrid-dev`）

**项目背景**:
- 学生用 Obsidian + Claudian sidebar，提问触发 Anthropic Claude Code SDK UserPromptSubmit hook
- Hook curl POST 到 backend `/rag/enrich-hook` → backend 调 `search_supplementary` → 返回 `additionalContext` (XML)
- SDK 自动 prepend additionalContext 到 system context → Claude 拿 vault wikilink 真材料 + Read tool 验证 + 回答
- 当前 stack: Python 3.11 + FastAPI + LanceDB + bge-m3 (1024d) + jieba FTS + RRF k=60 + 无 reranker

---

## 📚 必读文件清单（Tier 0 — 必须全读）

按 RAG 管道顺序排列。GitHub URL 模板：`https://github.com/oinani0721/canvas-learning-system/blob/worktree-feature-obsidian-hybrid-dev/<path>#L<start>-L<end>`

### T0-1. 本次完整调研报告（最高优先，先读这个）
- `_bmad-output/research/round-23-phase-a-retrieval-quality-2026-05-09.md` (629+ 行)
  - L1-243: Round-1（3 agent 找 LanceDB 索引污染 + RAG vs Grep 范式差异）
  - L290+: Round-2（6 agent 全管道审查 — §12 共识 / §13 7 根因 / §14 修复方案 / §15 用户决策 / §16 本 prompt / §17 文件参考）

### T0-2. Hook Endpoint（管道入口，commit fa814e7 主体）
- `backend/app/api/v1/endpoints/chat.py`
  - L570-587: `HookEnrichRequest` / `HookEnrichOutput` Pydantic models（Anthropic hook 协议契约）
  - L594-696: `rag_enrich_hook` — UserPromptSubmit hook 主 endpoint
  - L201-316: `enrich_context` — Cmd+Shift+E 触发的另一路径（参考对比，hook 不走此路）

### T0-3. Supplementary 主管道（hook 调的 service，全文必读）
- `backend/app/services/supplementary_search_service.py` (475 行)
  - L36-170: `search_supplementary` — RAG-as-tool 范式，top_k_max=20 + elbow_cut + Read 验证
  - L178-211: `format_supplementary_xml` — XML 格式化
  - L219-243: `_resolve_chunks_to_source_file` — chunks 派生路径回写（commit 275a201）
  - L246-275: `_is_real_vault_file` — 文件存在性检测（防 ghost ref + 空文档 < 64B）
  - L278-298: `_elbow_cut` — **根因 D 在此**（绝对差 0.05，但 RRF 后 gap 是 0.0005）
  - L301-400: `_two_tier_search` — Tier-1 prefix-resolved + Tier-2 unprefixed legacy fallback
  - L403-475: `_normalize_material` — wikilink heading anchor 字面保留（commit c3c06eb）

### T0-4. LanceDB Client（核心，关键段读这些）
- `backend/lib/agentic_rag/clients/lancedb_client.py` (3500+ 行，**只读关键段**)
  - L85-280: `_chunk_text` + helper — **根因 E 在此**（不丢小段）
  - L1204-1262: `index_vault_notes` — 入库 schema 定义
  - L1248-1279: `skip_dirs` / `skip_files` — **根因 A 在此**（缺 `原白板`）
  - L2098-2222: `_split_md_by_heading` + `_flush_section` — heading 切分（**没 NAV_HEADINGS_BLACKLIST**）
  - L2306-2520: `search` → `_search_internal` — hybrid 入口（embedding + jieba FTS）
  - L2431-2462: `_build_where_filters` — SQL WHERE 子句构建
  - L2629-2653: `_rrf_fuse` — Reciprocal Rank Fusion k=60
  - L2655-2700: `_convert_to_search_results` — **根因 B 在此**（`1/(1+d)` 二次压缩 score 到 [0.503, 0.508]）

### T0-5. Source Priority 配置
- `backend/app/core/reference_config.py`
  - L66-94: `apply_source_priority` — **根因 C 在此**（只 boost 不 demote）
- `backend/data/reference_priority.json` — **缺 `原白板/`/`节点/` 规则**

### T0-6. Vault 配置 + 实证样本
- `canvas-vault/.claude/settings.json` (15 行) — UserPromptSubmit hook 注册
- `canvas-vault/原白板/CS188 lecture 2.md` — 噪音实证：
  - L25-67 `## Concepts`（导航 section，含 dataviewjs）
  - L96-105 `## Recent Activity`（审计日志，**0 学习价值但被向量化**）
- `canvas-vault/raw/CS188/videos/lectures/lecture 4/lecture 4.md` (1456 行) — 命中标杆：
  - L990-1010 `## 6.4 全局/局部最大值`
  - L1020-1040 `## 6.4.1 解决局部最优陷阱的方法`（rank 1-2 命中段）
  - 其它 #6.5 模拟退火 / #6.7 遗传算法 / #6.9 对比表

---

## 📂 选读文件（Tier 1 — context）

### T1-1. 主 RAG pipeline（hook 不走，但 rerank node 在这）
- `backend/app/services/rag_service.py` L120-328
- `backend/lib/agentic_rag/state_graph.py` L66-130 (router) + L530-728 (build_canvas_agentic_rag_graph，**rerank node 在此 build，但 hook pipeline 不调用**)
- `backend/lib/agentic_rag/reranking.py` L57-370 (LocalReranker / CohereReranker — 注意：是 priority-based，**非 cross-encoder**)
- `backend/lib/agentic_rag/config.py` (含 `gte-reranker-modernbert-base` 但 hook 不用)

### T1-2. Index 服务 + skip_dirs 入口
- `backend/app/services/lancedb_index_service.py` L322-374 — 索引重建入口
- `backend/app/api/v1/endpoints/metadata.py` L450-530 — skip_dirs 配置入口（query param / env var）

### T1-3. 3 个 Claudian Skills
- `canvas-vault/.claude/skills/ai-linked-doc/SKILL.md` (322 行) — Cmd+Shift+D 派生新节点（与 RAG 互补）
- `canvas-vault/.claude/skills/node-chat/SKILL.md` (104 行) — Cmd+Shift+C 节点级对话（与 RAG 正交）
- `canvas-vault/.claude/skills/chat-with-context/SKILL.md` — Cmd+Shift+E enrich-context（**与 hook 是替代关系**：skill = manual / hook = auto）

### T1-4. 历史调研报告（理解架构演进）
- `_bmad-output/research/round-23-chatgpt-dr-result-and-synthesis-2026-05-08.md` (371 行) — **前一次 ChatGPT DR 的结论**（你需要审视它是否被本轮 fa814e7 修复方案推翻）
- `_bmad-output/research/round-23-phase-a-architecture-report-2026-05-09.md` (369 行)
- `_bmad-output/research/round-23-phase-abc-implementation-spec-2026-05-09.md` (175 行)
- `_bmad-output/research/round-13-wikilink-vs-graphiti-five-questions-answer-2026-04-29.md` (474 行) — **wikilink vs Graphiti 双轨决策**（hook 是否该跨双轨？）
- `_bmad-output/research/round-12-graphiti-karpathy-5-conjectures-audit-2026-04-21.md` (587 行) — 个人记忆引擎论证

### T1-5. 架构决策
- `_bmad-output/planning-artifacts/architecture.md` L30-40 — 双系统检索 + 后处理 (gte-reranker / Adaptive-k / A-RAG Verify)
- `_bmad-output/planning-artifacts/prd.md` L80-220 — RAG 相关 FR (FR-KG-06 / FR-EXAM-04 / FR-CONV-10)
- `_bmad-output/planning-artifacts/epics.md` Epic 2 — 检索个性化 FR-RETR-01~13

---

## 🕒 关键 Commits 时间线（理解 Phase A 演进）

按时间倒序（仓库 `https://github.com/oinani0721/canvas-learning-system/commit/<hash>`）：

| Commit | 日期 | 主题 | 改动文件 |
|---|---|---|---|
| `2ecf370` | 2026-05-09 | docs: 完善 chatgpt prompt 加 t0/t1 文件清单 + commits 时间线 | round-23 file (+124) |
| `aad0c9a` | 2026-05-09 11:30 | docs: round-2 6 agent 对抗调研（**本调研报告**） | round-23 file (+346) |
| `fa814e7` | 2026-05-09 10:11 | feat: UserPromptSubmit hook 自动 RAG 注入到 Claudian | `chat.py` (+140) + `canvas-vault/.claude/settings.json` (+15) |
| `c3c06eb` | 2026-05-09 | fix: wikilink anchor=raw heading 字面 + display=clean | `supplementary_search_service.py` L403+ |
| `275a201` | 2026-05-09 | fix: chunks 派生路径回写 + heading 不 over-strip | `supplementary_search_service.py` L219+ |
| `98dbc2d` | 2026-05-09 | feat: rag-as-tool 重构 — Read 验证 + 动态 top_k + 空文档过滤 | `supplementary_search_service.py` L36-170 |
| `3001f00` | 2026-05-09 | fix: config.py pydantic skip_dirs 默认值同步 | `lancedb_client.py` L1248-1279 |
| `3b96e49` | 2026-05-08 | feat(agentic-rag): A9 L1 LLM router — Gemini Flash 替规则分类器 | `state_graph.py` L66-130 |
| `b7feefb` | 2026-05-08 | chore: archive fix-rag-faithfulness-and-add-crag-quality-loop | RAG 质量环路 |
| `c229291` | 2026-05-07 | test(crag): one-shot CRAG deep_research integration test | `tests/regression/` |

**Phase A 演进逻辑**：
1. 早期（< 2026-05-07）: 只有主 RAG pipeline (`rag_service.py` + `state_graph.py`)，含 rerank node 但需手动触发
2. `98dbc2d`: 引入 supplementary_search_service.py — 把 RAG 当工具用，让 Claude 大召回 + Read 真验证
3. `275a201` / `c3c06eb`: 修复 wikilink anchor 跳转精度
4. `3001f00`: 修 skip_dirs 配置（但仍缺 `原白板/`）
5. `fa814e7`: **架构突破** — UserPromptSubmit hook 自动注入每次提问
6. `aad0c9a`: 本次 6 agent 对抗调研发现 hook 召回 rank 8-10 仍漂移

**关键 insight**: hook pipeline 是**绕过**主 RAG pipeline 的简化路径 — 没有走 state_graph.py 的 rerank node。这是为什么 Phase A 没 cross-encoder（根因 F）。

---

## The Problem

用户实测案例：
- query: "什么是局部最优陷阱怎么解决"
- 返回 10 条 supplementary，rank 1-7 完美命中 `lecture 4 #6.4.1 解决局部最优陷阱的方法`
- **rank 8-9 漂移到 `原白板/CS188 lecture 2#Recent Activity` 和 `#Concepts`**（白板导航 section，纯审计日志，0 学习价值）
- **rank 10 漂移到 `节点/lecture 2#2.3 规划代理`**（话题完全错位）

噪音密度 30%。

## Our 7 Root Causes Diagnosis

详见仓库 round-23 文件 §13。摘要：
- A. `skip_dirs` 缺 `原白板`，heading 切分把导航 section 当普通 section 入库
- B. RRF 分数被 `1/(1+d)` 二次压缩到 [0.503, 0.508] 全平
- C. `apply_source_priority` 只 boost 不 demote
- D. `_elbow_cut` 用绝对差 0.05，RRF 后 gap 是 0.0005
- E. `_chunk_text` 不丢弃小段
- F. 没有 cross-encoder rerank 接入（hook 绕过主 pipeline rerank node）
- G. Hook endpoint 收 `cwd` 字段但 0 引用

## Our Proposed Fix (Round-2 Plan)

详见仓库 round-23 §14：
- **最小集合**: A+B+C+D (30-50 行) — 预期解决 80%
- **完整集合**: A+B+C+D+F (含 BGE-reranker-v2-m3, +100 行) — 预期 95%+

---

## What I Need From You (Adversarial Review)

请你做 5 件事：

### 1. 验证 7 个根因诊断
- 直接读仓库源码（按 T0 清单），验证每个根因确实存在
- 找出我们 **遗漏的根因**（H, I, J...）
- 找出我们 **过度诊断的根因**

### 2. 对抗性挑战修复方案
- 修复 A 的"白板完全 skip"会不会丢用户在白板写的真知识？
- 修复 B 的 RRF 归一化 [0,1] 会不会破坏 source_priority 乘法权重的语义？
- 修复 C 的 `节点/**` weight=0.85 是否合理？节点是用户主动派生，可能比 raw transcript 更精炼，weight 应该 ≥ 1.0？
- 修复 D 的 30% relative drop 阈值 — 你认为 50% 还是 20% 更稳健？

### 3. 提出 2 套对抗替代方案

**方案 X**: 抛弃 RAG，回归 Claude Code grep 范式
- LLM 自己拆 query → 决定关键词 → ripgrep → Read 文件 → LLM 二次过滤
- 我们 vault 当前 ~126 files / 4373 chunks，是不是还在 grep 占优区间？

**方案 Y**: Anthropic Contextual Retrieval (chunk 前置 LLM 上下文摘要)
- 用 Claude Haiku + prompt cache 给每个 chunk 写课程+章节上下文
- 替代/补充 我们的修复 A+C？

请对比我们的方案 (A+B+C+D[+F]) vs 方案 X vs 方案 Y，给出**决策矩阵 + 推荐**。

### 4. 设计 Phase A/B/C 完整路线

请按业界 RAG 项目的 Phase 划分：
- **Phase A (MVP, 当前)**: 修 7 根因 + 接 reranker，目标"召回精度 80% → 95%"
- **Phase B (深度模式, 解题场景)**: 是否需要新建 skill 显式触发？query rewrite + multi-hop wikilink 图遍历 + 长 context？
- **Phase C (长期演进)**: graph-aware（利用 wikilink + Graphiti KG）？personalization？多模态？

每个 Phase 给出：假设/前提 / 核心 deliverable（具体到代码改动）/ 工作量估算（小时）/ 验收 metric / 风险 + 兜底

### 5. 笔记片段"精确返回"机制设计

用户的核心诉求是 **笔记片段精确返回** — 即用户提问后，返回的 wikilink 必须能精确跳到正确的 heading anchor。

请深度调研 + 设计：
- chunk → wikilink anchor 的精确映射（heading path 怎么编码）
- inline citation 在 LLM 回答里的强制约束（commit 98dbc2d 已强制 Read，是否要进一步约束句子级 citation）
- 用户点击 wikilink 后跳转的 100% 命中率
- "5 句话内必引 1 wikilink" 这种 anti-hallucination 强制约束业界是否有先例

---

## Constraints (你的方案必须满足)

- **本地 macOS M-series**（M1 Max / M3 Max），无 NVIDIA GPU
- **5s hook 总延迟预算**（用户感知）
- **零 fork Claudian**（不动 Obsidian 插件本体）
- **bge-m3 是已锁定 embedding**（不接受换 embedding 的方案）
- **Apache-2.0 / MIT 兼容**，避免 GPL/CC-BY-NC
- **优先 LanceDB 原生 API**，自定义 reranker 也用 LanceDB Reranker subclass

## Desired Output Format

1. 7 根因验证清单（per-root-cause 验证 + 漏诊补充）
2. 4 个修复方案对抗结论（A/B/C/D 各打 0-10 分 + 改进建议）
3. 方案 X / Y 决策矩阵（vs 我们当前方案）
4. Phase A/B/C 完整路线（含工作量 + verification metric）
5. 笔记片段精确返回机制设计
6. 你的最终推荐（按 priority 排）
7. 你认为我们最大的盲点是什么（一段长答）

## What I Specifically Want You to Push Back On

不要只是赞美我们的方案。请尖锐地：
- 找出我们 in-domain 拒绝 HyDE 的论证是否过度
- 挑战 BGE-reranker-v2-m3 在 macOS CPU 上的 ~260ms 延迟是否真的够用
- 我们认为 LightRAG "在已有 wikilink 的 vault 是 anti-pattern" — 但 wikilink 是稀疏的，LLM 抽实体可能补漏？
- 我们 hook 5s 预算 + 30 候选 reranker 是合理的吗？业界 production 是 100 候选 → 10 还是 30 → 5？

## Output Length

不限。Phase A/B/C 的 deliverable 越细越好，工作量估算到具体函数级。
~~~~~~

---

## V2 ChatGPT 返回后工作流

1. 把 ChatGPT 返回的报告 ship 到 `_bmad-output/research/round-23-chatgpt-dr-response-v2-2026-05-09.md`（**v2 后缀**避免覆盖前次响应）
2. 在 Obsidian 内打开通知 Claude
3. Claude 启动 4-6 个并行 Explore agent **cross-check** ChatGPT 关键 claim：
   - 验证它声称的 benchmark 数字是否可信（HyDE 25% failure / BGE 260ms 等）
   - 验证它提的"方案 X / Y"在我们 stack 上的可行性
   - 验证它指出的"漏诊根因"是否在代码中确实存在
4. Claude 综合 6 agent + ChatGPT 反馈 → 产出 Phase A 实施 Story spec
5. 用户在 Obsidian 内批注 §15 4 个 Q（修复优先级 / 白板策略 / skill 是否新建 / scope）
6. Claude 启动 dev → ship → mini-UAT 闭环

## V1 vs V2 关键决策点

| 决策 | V1 立场 | V2 立场 |
|---|---|---|
| 范式选择 | 开放（X/Y/Z 让 GPT 选） | 已定（fa814e7 ship hybrid + 6 agent 验证 hybrid 正确） |
| 主问题 | "范式哪个对" | "已选 hybrid + 7 根因，修复对不对" |
| 用户痛点描述 | "Top 5 召回 60% 噪音" | "Top 10 召回 30% 噪音，rank 8-10 漂移" |
| 修复颗粒度 | 三方案对比（粗） | 7 根因 file:line + 4 修复 + 代码骨架（细） |
| Phase A/B/C | 探索性 | 落地性（含工作量到函数级） |

---

*Generated 2026-05-09 03:01 (V1) + 2026-05-09 12:43 (V2 升级) — V2 已 ChatGPT 回 + cross-check confirmed + Phase A0 已 ship (commit aef95be)*

---

# V3 — Multi-Vault Architecture Adversarial Review (2026-05-09 14:00 升级)

> **V3 vs V1/V2 关系**:
> - V1: 范式选择（X 单 vault LanceDB / Y grep / Z hybrid）
> - V2: 单 vault hook RAG 的 7 根因修复 + 对抗审查
> - **V3: 多 vault 架构演进** — 用户原话"以后 Canvas Learning System 会用到很多其他不同的 vault"
>
> **V3 触发**：Phase A0 修复 ship 后 (rank 8-10 漂移消失)，用户提出未来要支持很多 vault（不同课程一 vault）。需要 ChatGPT 审视架构是否真的 ready，以及 V2 修复方案在多 vault 下是否还成立。
>
> **V3 调研产物**: 4 并行 Explore/general-purpose agent 调研完成（多 vault 隔离 / Phase A0 多 vault 影响 / hardcode 审计 / 业界对照）

## V3 调研关键发现汇总（4 agent 共识）

### 当前 ready 度: **85%**

✅ **已就绪 (5 项)**:
1. LanceDB namespace 隔离 — 单 DB + `{vault_id}_table_name` 前缀（`backend/lib/agentic_rag/clients/lancedb_client.py:394-401`）
2. Graphiti group_id — `vault:<vault_id>:<subject>` 格式 + cypher_with_group_filter 防御（Story 2.5.Y）
3. Backend hot-reload — `reload_settings()` 支持无 restart 切 vault
4. API 端点 vault_id 必填 — `/api/v1/chat/enrich-context` 等
5. migrate_group_ids.py 完整覆盖已弃用格式

❌ **Gap (4 项)**:
1. **`reference_priority.json` 全局单一** — 不同 vault 目录结构不同（CS61B 用 `videos/lectures/` vs 数学课用 `课件/讲座/`），全局 pattern 跨 vault 必失配（Phase A0 修的 J 在多 vault 下问题重现！）
2. **`apply_source_priority(results)` 无 vault_id 参数** — 无法 per-vault 加载 priority config（reference_config.py:66-94）
3. **SQLite `qa_metrics.db` 无 vault 隔离字段** — 跨 vault 数据污染
4. **`.canvas-config.yaml` 缺 `vault_id` 显式字段** — 依赖文件夹名 `sanitize_vault_id()` 推断，易出错

### 业界对照（Agent 4 调研）

**强隔离派系占主流** (NotebookLM / AnythingLLM / Logseq / RagFlow):
- **NotebookLM**: 强物理隔离，**拒绝跨 notebook 搜索**（"isolation = strength" 设计哲学）
- **AnythingLLM**: per-workspace LanceDB collection + 全局 embedder + **per-workspace reranker/LLM/top_k/system_prompt**
- **Logseq**: per-graph 严格隔离，跨 graph FR **4 年悬而未决**
- **RagFlow**: per-dataset 物理隔离 + 可选跨 dataset union（要求同 embedder）

**唯一合并派**: Khoj (pgvector 单一索引 + `file:` filter 过滤，社区评价"次选"方案)

**Pinecone/Weaviate 多租户结论**:
- 小 tenant 数（< 100）+ 强隔离需求 → **per-collection**
- 海量 tenant（10k+）→ metadata filter
- Canvas 课程数预估 < 100 → **per-collection 是正解**

### 业界对教育场景的明确建议

> 1. **Per-vault LanceDB table**（已 ✅）— 强物理隔离符合用户"一门课一个 vault"心智
> 2. **全局 embedder（bge-m3 锁）+ per-vault reranker/top_k/source-priority/system-prompt**
> 3. **MVP 不做跨 vault RAG**；如未来需要"所有课程关于 algorithm" → 走 **LLM 层多 vault attachment**（学 Gemini-NotebookLM）

## V3 提示词全文（复制下面 ~~~~~~ 整段给 ChatGPT Deep Research）

> 使用方式：
> 1. ChatGPT → 选 Deep Research 模式（GPT-5 / o3）
> 2. 复制下面 `~~~~~~` 包裹的整段（不含外层包裹符）
> 3. 等 5-15 min
> 4. 回填到 `_bmad-output/research/round-23-chatgpt-dr-response-v3-multi-vault-2026-05-09.md`

~~~~~~
# Tech Decision: Canvas Learning System Multi-Vault Architecture — Adversarial Review

## Context

我做的是一个本地 Obsidian PKM RAG 系统。**关键演进需求**：未来用户会有**很多不同的 vault**（每门课程一个 vault — CS 61B / 数学 / 英语 / 历史 ...）。现在 Phase A0 修复刚 ship（commit aef95be），单 vault 召回精度从 30% 漂移降到 0%。但需要审视多 vault 下架构是否还成立。

**仓库**: https://github.com/oinani0721/canvas-learning-system
**Branch**: `worktree-feature-obsidian-hybrid-dev` （⚠️ 必须切此分支）

**Tech Stack**:
- Backend: FastAPI + LanceDB (单 DB 多 table 前缀 `{vault_id}_vault_notes`) + Neo4j (group_id 隔离) + bge-m3 1024d
- Frontend: Obsidian plugin + Claudian sidebar
- Hook: Claude Code SDK UserPromptSubmit hook (curl POST 到 `/rag/enrich-hook`)
- 当前 Phase A0 修复: priority pattern 加 `**/` 前缀 + tier-2 fallback rank decay + degraded 标志

---

## 4 并行 Agent 调研发现（你需要审视/挑战）

### 当前架构现状（Agent 1）

**ready 部分**:
- `backend/lib/agentic_rag/clients/lancedb_client.py:394-401` `resolve_table_name()` 单 DB + `{vault_id}_` 前缀
- `backend/app/core/subject_config.py:212-262` `build_vault_group_id(vault_id, subject_id, canvas_path)` Graphiti group_id
- `backend/app/utils/cypher_helpers.py:20-96` `cypher_with_group_filter()` 强制 WHERE 注入防跨 vault 泄漏
- `backend/app/config.py:702-704` `Settings.vault_id` property + `reload_settings()` 支持 hot-reload
- `backend/scripts/migrate_group_ids.py` 完整迁移脚本 (cs188/canvas-dev/cs_61b:main → vault:* 格式)
- `frontend/obsidian-plugin/src/main.ts` plugin 读 `.canvas-config.yaml` + `buildAcceptPayload()` 传 vault_id

**已知 Gap**:
- `backend/data/reference_priority.json` 全局单一文件，跨 vault 目录结构不同（CS 61B 用 `videos/lectures/`，数学课可能用 `课件/讲座/`），Phase A0 修的 `**/videos/lectures/**` 在新 vault 上必失配
- `backend/app/core/reference_config.py:66-94` `apply_source_priority(results)` 函数无 `vault_id` 参数
- `backend/app/services/supplementary_search_service.py:387` Phase A0 修复 I 加了 `is_legacy_fallback=True` 标志，但**没区分哪个 vault 的 legacy**
- SQLite `qa_metrics.db` 表无 vault_id 字段 → 跨 vault 数据污染
- `.canvas-config.yaml` 当前只有 `subject` 字段，**缺 `vault_id` 显式字段**（依赖 `sanitize_vault_id(ACTIVE_VAULT)` 文件夹名推断，易出错）
- DEFAULT_GROUP_ID="cs188" 硬编码 (config.py:471)

### Phase A0 在多 vault 下的兼容性（Agent 2）

我们 Phase A0 (commit aef95be) 修了 `reference_priority.json`：
```json
{
  "source_priorities": [
    {"pattern": "**/*-explanations/**", "weight": 0.5, "label": "..."},
    {"pattern": "原白板/**", "weight": 0.3},
    {"pattern": "节点/**", "weight": 0.9},
    {"pattern": "**/videos/lectures/**", "weight": 1.5},
    ...
  ]
}
```

**Agent 2 警告**：当前 pattern 假设所有 vault 都用相似目录结构。但：
- CS 61B vault: `raw/CS61B/videos/lectures/...` ← 命中 1.5x boost
- 数学课 vault: `课件/微积分/讲座1/...` ← **0 命中**，回到无 boost 状态
- 英语 vault: `articles/...` + `vocabulary/...` ← 0 命中
- 节点/原白板 是 Round-11 锁定的扁平架构（所有 vault 共用），但 demote weight 0.3 / 0.9 是否对所有学科都合理？

### 业界对照（Agent 4）

| 产品 | 隔离策略 | 跨 vault 搜索 | 配置粒度 |
|---|---|---|---|
| NotebookLM | 强物理隔离 | ❌ 拒绝（设计哲学） | per-notebook |
| AnythingLLM | per-workspace LanceDB collection | ❌ 默认 | 全局 embedder + per-workspace reranker/LLM/top_k/prompt |
| Logseq | per-graph Datascript DB | ❌ 4 年 FR 未解 | per-graph |
| RagFlow | per-dataset 物理隔离 | ✅ 可选 union | 跨 dataset 要求**同 embedder** |
| Khoj | 单 pgvector 索引 + `file:` filter | ✅（合并派少数） | per-agent custom KB |

**Pinecone/Weaviate 多租户共识**：
- 小数量 tenant（< 100）+ 强隔离需求 → **per-collection** (clean isolation, custom configs)
- 海量 tenant（10k+）→ metadata filter
- Canvas 课程数预估 < 100 → per-collection 完胜

---

## 必读文件清单（Tier 0 — GitHub URL 模板 `https://github.com/oinani0721/canvas-learning-system/blob/worktree-feature-obsidian-hybrid-dev/<path>#L<a>-L<b>`）

### T0-1. V2 调研产物 + Phase A0 修复
- `_bmad-output/research/round-23-phase-a-retrieval-quality-2026-05-09.md` (1000+ 行) — 完整调研含 §13 7 根因 + §18 cross-check + §19 修复方案
- `_bmad-output/research/round-23-chatgpt-dr-response-v2-2026-05-09.md` — V2 ChatGPT 反馈 (确认 4 致命漏诊)
- `_bmad-output/research/round-23-chatgpt-dr-prompt-2026-05-09.md` §V3 — 本 prompt 来源

### T0-2. 多 vault 隔离机制核心
- `backend/lib/agentic_rag/clients/lancedb_client.py:388-444` — `get_current_vault_id()` + `resolve_table_name()` + `list_vault_tables()` + `drop_vault_tables()`
- `backend/app/config.py:702-704` — `Settings.vault_id` property
- `backend/app/config.py:913-932` — `reload_settings()` hot-reload
- `backend/app/config.py:471` — `DEFAULT_GROUP_ID="cs188"` 硬编码（待修）
- `backend/app/core/subject_config.py:212-262` — `build_vault_group_id()`
- `backend/app/core/subject_config.py:292-354` — `canonical_group_id()` backward compat
- `backend/app/utils/cypher_helpers.py:20-96` — `cypher_with_group_filter()` 防御注入

### T0-3. Phase A0 修复（多 vault 兼容性焦点）
- `backend/data/reference_priority.json` — Phase A0 改后内容（全局单一文件）
- `backend/app/core/reference_config.py:66-94` — `apply_source_priority()` 无 vault_id 参数
- `backend/app/services/supplementary_search_service.py:380-409` — Phase A0 修复 I 后的 tier-2 fallback rank decay + degraded 标志

### T0-4. Vault config 入口
- `canvas-vault/.canvas-config.yaml` — 当前 schema (subject / subject_display / active_board / schema_version / deprecated_paths)
- `frontend/obsidian-plugin/src/main.ts` — `readVaultConfig()` + `buildAcceptPayload()`
- `backend/app/api/v1/endpoints/chat.py:589-696` — `rag_enrich_hook` Hook endpoint（注意 `req.cwd` 当前**未用**，多 vault 下需要解析）

### T0-5. 数据迁移
- `backend/scripts/migrate_group_ids.py` — 已弃用格式映射

---

## 选读文件（Tier 1）

- `backend/app/api/v1/endpoints/chat.py:201-316` `enrich_context` — 另一路径（带 vault_id 必填参数）
- `backend/app/services/lancedb_index_service.py` — 索引服务，文件监听 vault 路径
- `backend/app/services/rag_service.py` — 主 RAG service
- `backend/app/api/v1/endpoints/metadata.py:450-530` — skip_dirs 配置入口
- 历史调研: `_bmad-output/research/round-13-wikilink-vs-graphiti-five-questions-answer-2026-04-29.md` — wikilink vs Graphiti 双轨决策

---

## 关键 Commits 时间线

| Commit | 主题 |
|---|---|
| `aef95be` | **Phase A0**: 修 J pattern 失配 + I tier-2 fallback 0.85 (rank 8-10 漂移消失) |
| `a614af0` | Round-3 ChatGPT V2 反馈 + 4 cross-check（4 致命漏诊确认）|
| `f4d74fc` | chatgpt-dr-prompt md 追加 V2 完善版 |
| `aad0c9a` | Round-2 6 agent 对抗调研 |
| `fa814e7` | UserPromptSubmit hook 自动 RAG 注入 |

---

## What I Need From You (Adversarial Review)

请你做 5 件事：

### 1. 验证 4 agent 调研发现的 Gap

直接读仓库源码（按 T0 清单），对照我列的 4 个 Gap：
- `reference_priority.json` 全局单一是否真的会跨 vault 失配？
- `apply_source_priority` 真的没 vault_id 参数？
- SQLite qa_metrics.db 真的缺 vault 隔离字段？
- `.canvas-config.yaml` 真的缺 vault_id 显式字段？

找出**4 agent 漏诊的多 vault Gap**（H, I, ...）— 比如：是否还有更隐藏的"假设单 vault"硬编码？

### 2. 挑战 Phase A0 修复在多 vault 下的兼容性

Phase A0 (commit aef95be) 修复了 J（pattern 加 `**/`）+ I（tier-2 fallback rank decay）。但：
- 修复 J 假设 vault 用 `videos/lectures/` 这种结构 — **跨 vault 不通用**。修复 J 是否需要降级为 vault 无关 fallback + per-vault override 机制？
- 修复 I 的 `is_legacy_fallback` 标志在多 vault 下如何区分？是否要加 `vault_id` 到 metadata?
- 节点/`原白板/`weight 0.3 / 0.9 是 CS 课程经验值，对数学/英语/历史 vault 是否仍合理？

### 3. 设计 Per-Vault Retrieval Config Schema

业界（AnythingLLM）做法：全局 embedder + per-workspace reranker/top_k/source-priority/system-prompt。请设计 Canvas Learning System 的 per-vault config schema：

**.canvas-config.yaml 升级版应该有哪些字段？**
- vault_id（显式，不依赖文件夹名推断）
- subject（已有）
- 是否加 `retrieval_hints` 段：
  - `source_priorities` per-vault override（覆盖全局 reference_priority.json）
  - `excluded_headings`（默认值 + per-vault 自定义）
  - `excluded_prefixes`
  - `reranker_model`（默认 BGE 全局，per-vault 覆盖）
  - `top_k_max` / `min_relevance` / `elbow_drop_threshold`

**全局 vs per-vault 的拆分原则是什么？业界共识？**

### 4. 设计 Vault CRUD Onboarding 流程

当前 onboarding 是 5 步手工：mkdir 目录 + 写 .canvas-config.yaml + 调 backend init API + 修改 .env ACTIVE_VAULT + 调 vault/switch API（小白友好度 3/5）

请设计 production-ready 的多 vault 流程：

**核心问题**:
- **新建 vault**：用户在 Obsidian 里点一个按钮 → backend 自动创建 vault_id + LanceDB table + Graphiti group_id + 写 .canvas-config.yaml？
- **切换 vault**：plugin 检测当前 active vault → 自动通知 backend reload_settings()？
- **删除 vault**：用户删 Obsidian vault 后 → backend 自动 cleanup LanceDB tables / Neo4j group_id?
- **复制/clone vault**：用户复制一门课的 vault 给新学期 → 是否需要重 index？
- **vault rename**：vault_id 改了之后所有引用如何迁移？

参考业界产品（AnythingLLM、NotebookLM）的 UX 流程。

### 5. 跨 Vault 搜索的决策（Strategic Question）

业界共识是**默认强隔离 + 拒绝跨 vault**（NotebookLM / Logseq / AnythingLLM）。但用户场景：
- 学生在数学课 vault 里问"梯度下降跟 CS 188 lecture 4 的局部搜索算法有什么联系" — 需要跨 vault 检索
- 学生想问"我所有课程里关于 alpha-beta pruning 的笔记" — 需要 union 检索

**请决策**：
- Canvas Learning System 应该支持跨 vault 搜索吗？
- 如果支持：是 RAG 层 union（学 RagFlow）还是 LLM 层 multi-attachment（学 NotebookLM + Gemini）？
- 如果不支持：用户怎么解决"跨课关联"需求？UI 提示？

---

## Constraints (你的方案必须满足)

- **保持 LanceDB 单 DB + per-table 前缀架构**（已锁定，不接受换 DB）
- **bge-m3 是全局 embedder**（不接受 per-vault embedder — 业界共识不接受切 embedder）
- **保持 ACTIVE_VAULT env var + reload_settings hot-reload 机制**
- **`.canvas-config.yaml` 作为单一 truth source**（不引入额外的 backend-side vault registry）
- **保持 zero-fork Claudian / Obsidian**（只能动 plugin + backend）
- **课程数预估 < 100**（per-collection 而非 metadata filter）

---

## Desired Output Format

1. **4 个 Gap 验证**（per-gap confirmed/refuted + 漏诊补充）
2. **Phase A0 多 vault 兼容性挑战**（J / I 在多 vault 下的修复方案重新设计）
3. **Per-Vault Retrieval Config Schema 设计**（.canvas-config.yaml 完整 v2 版本 + 全局 vs per-vault 拆分原则）
4. **Vault CRUD Onboarding 流程**（新建/切换/删除/复制/rename 5 套流程，带 UX wireframe）
5. **跨 Vault 搜索决策**（支持 / 不支持 + 理由 + UX 方案）
6. **Phase B 多 vault 增强路线**（在 Phase A0 ship 后，Phase B 应该做什么 — 含工作量到函数级）
7. **你认为最大的多 vault 盲点**（一段长答）

---

## What I Specifically Want You to Push Back On

不要只赞美我们的方案。请尖锐地：
- 我们说 "85% ready 多 vault" — 但 SQLite 无隔离 + .canvas-config 缺 vault_id 字段 + DEFAULT_GROUP_ID 硬编码，这是 85% 还是 60%？
- AnythingLLM 的"per-workspace reranker"在 macOS 本地 + 我们 5s hook 预算下是否过度（每个 vault 加载独立 reranker model 会 OOM 吗）？
- "MVP 不做跨 vault" — 但学生场景天然有跨课关联需求，业界 NotebookLM 拒绝是否是 enterprise 偏见，教育场景应该不一样？
- 我们的 Phase A0 修复 J（`**/videos/lectures/**`）— 在数学/英语 vault 上不命中 = 退化为无 boost = 漂移可能重现。是否应该立刻把 priority 配置 per-vault 化（不等 Phase B）？

---

## Output Length

不限。Per-Vault Config Schema 越细越好，工作量估算到具体函数级。
~~~~~~

---

## V3 ChatGPT 返回后工作流

1. ChatGPT 报告 ship 到 `_bmad-output/research/round-23-chatgpt-dr-response-v3-multi-vault-2026-05-09.md`
2. Claude 启动 4-6 个并行 Explore agent **cross-check** ChatGPT 关键 claim（特别是漏诊 Gap H+ / Phase B 路线 / per-vault config schema 是否合理）
3. Claude 综合 → 产出 Phase A1 多 vault 增强 Story spec
4. 用户决策 → 启动 dev → ship 多 vault demo（创建第二个 vault 实测）

---

## V1 vs V2 vs V3 关键决策对比

| 决策 | V1 | V2 | V3 |
|---|---|---|---|
| 焦点 | 单 vault 范式选择 (X/Y/Z) | 单 vault 7 根因修复 | **多 vault 架构演进** |
| 假设 | RAG 漂移修不掉 | hook RAG 已 ship 但漂移 | Phase A0 已 ship 0% 漂移 |
| 用户痛点 | "Top 5 60% 噪音" | "Top 10 30% 漂移" | "未来很多 vault" |
| 架构问题 | 范式不对 | side-path 实现 bug | 单 vault 假设到处都是 |
| Output 颗粒度 | 范式对比 | file:line 根因 | per-vault config schema + CRUD 流程 |

---

*Generated 2026-05-09 03:01 (V1) + 2026-05-09 12:43 (V2) + 2026-05-09 14:00 (V3 multi-vault) — V3 已 ChatGPT 回 + cross-check confirmed 4/5 P0 + Phase A0.5 已 ship*

---

# V4 — study-question Skill 对抗审查 + ChatGPT 替用户决定所有 Q（2026-05-10 升级）

> **V4 vs V1/V2/V3 关系**:
> - V1: 单 vault 范式选择（X/Y/Z）
> - V2: 单 vault 7 根因修复
> - V3: 多 vault 架构演进
> - **V4: 解题深度模式 skill 设计 + 决策授权**
>
> **V4 触发**：用户授权 ChatGPT 替她决定 §7 的 4 个 Q（不再让用户勾选）— 因为 ChatGPT 有更广业界视野，能做更专业的设计决策。
>
> **V4 调研产物（已 ship）**: 4 并行 agent deep explore（业界对照 8 产品 + 技术方案 + Skill 机制 + 痛点边界）→ `round-23-study-question-skill-design-2026-05-10.md` 9 章 ~600 行

## V4 调研关键发现汇总

### 当前 hook RAG 边界论
- hook 5s 预算严格 → **永远做不到** query rewrite + multi-hop + Read 完整章节 + 强制结构化
- 这些"不能"不是实现 bug，是 hook 设计哲学
- 用户最早原话"全局搜索教学笔记给我回复"= 解题深度模式，hook 不能满足

### 4 痛点 hook vs skill 分工
| 痛点 | hook 修了？ | study-question 该解？ |
|---|---|---|
| A 召回精度漂移 | ✅ Phase A0 commit aef95be | ❌ 不重复 |
| B 深度不够 (10 条短 snippet) | ❌ 5s 预算 | ✅ 核心 |
| C 缺乏命令触发 | ❌ auto-trigger 设计 | ✅ 必做 |
| D 输出无结构 | ❌ hook 无 LLM 重排 | ✅ prompt 层 |
| E Multi-hop wikilink | ❌ Phase A0.5 明确不做 | ✅ wikilink 2-hop BFS |

### 业界 8 产品共识 (Agent 1)
**解题/学习场景必须 multi-pass** — Perplexity / NotebookLM / Khoj / CausalRAG / StepChain / SocraticLM 全部用 query 拆解 → 多次 retrieve → 合成。**单 pass RAG 必然劣化**。

## V4 提示词全文（复制下面 ~~~~~~ 整段给 ChatGPT Deep Research）

> **使用方式**：
> 1. ChatGPT → 选 Deep Research 模式（GPT-5 / o3）
> 2. 复制下面 `~~~~~~` 包裹的整段（不含外层包裹符）
> 3. **关键差异**：本 prompt **明确授权 ChatGPT 替用户决定** 4 个 Q（不让用户勾选）
> 4. 等 5-15 min
> 5. 回填到 `_bmad-output/research/round-23-chatgpt-dr-response-v4-study-question-2026-05-10.md`

~~~~~~
# Tech Decision: /study-question Claude Code Skill — 设计审查 + 替用户决定所有 Q

## Context

我做的是本地 Obsidian PKM 学习 RAG 系统。用户最早需求：
> "我在解题的时候对待相关内容产生不解...对应的知识点不懂...需要全局搜索相关的教学笔记来给我回复"

我整个 session 焦点偏移到 hook auto-RAG 改进（A0/A0.5/B0），**忘了 hook 是 baseline 不是深度模式**。Hook 解决了召回精度（A），但 4 个核心痛点 hook 架构边界做不到：B 深度不够 / C 缺乏命令触发 / D 输出无结构 / E Multi-hop wikilink。

**仓库**: https://github.com/oinani0721/canvas-learning-system
**Branch**: `worktree-feature-obsidian-hybrid-dev` （⚠️ 必须切此分支，不是 main）

**用户授权**: 我授权你**替用户决定** §最后 4 个 Q + 推荐你认为合理的额外 Q5/Q6。用户原话"把所有 Q 给 ChatGPT 决定"。

---

## 📚 必读文件清单（Tier 0 — 必须全读）

GitHub URL 模板: `https://github.com/oinani0721/canvas-learning-system/blob/worktree-feature-obsidian-hybrid-dev/<path>#L<a>-L<b>`

### T0-1. study-question 设计完整报告（最高优先）
- `_bmad-output/research/round-23-study-question-skill-design-2026-05-10.md` (~600 行) — 我的完整设计，含 9 章节 + 4 类 query 路由 + Phase 1/2 工时 + SKILL.md 骨架

### T0-2. 现有 4 个 Claudian Skill（边界对照）
- `canvas-vault/.claude/skills/chat-with-context/SKILL.md` — 最相关，Cmd+Shift+E 触发，已支持 enrich-context endpoint
- `canvas-vault/.claude/skills/node-chat/SKILL.md` (104 行) — Cmd+Shift+C 节点级对话
- `canvas-vault/.claude/skills/ai-linked-doc/SKILL.md` (322 行) — Cmd+Shift+D 派生新节点
- `canvas-vault/.claude/skills/configure-whiteboard/SKILL.md` (286 行) — 白板创建

### T0-3. Backend RAG 关键 endpoint
- `backend/app/api/v1/endpoints/chat.py:201-316` — `/api/v1/chat/enrich-context` (chat-with-context 调)
- `backend/app/api/v1/endpoints/chat.py:589-696` — `/api/v1/chat/rag/enrich-hook` (hook 主体, Phase A0.5-L 已加鉴权)
- `backend/app/api/v1/endpoints/chat.py:36` — `chat_router` 全局 dependencies (require_internal_api_key, DEBUG 透明)

### T0-4. Supplementary search 主管道
- `backend/app/services/supplementary_search_service.py` (475 行) — 含 search_supplementary + format_supplementary_xml + Phase A0.5-P taint 扫描
- L36-170 search_supplementary, L178-270 format_supplementary_xml, L380-410 tier-2 fallback (Phase A0 修)

### T0-5. Multi-hop / Query rewrite 现有实现（可复用）
- `backend/lib/agentic_rag/mastery_injection.py:296` — `multi_query_rewrite` (Gemini Flash + 3s timeout, 已实现可复用)
- `backend/app/services/wikilink_context_service.py:317` — `enrich_from_wikilink_graph` N-hop
- `backend/app/services/wikilink_graph_service.py` — BFS N-hop 已就绪 (hop=2 默认)

### T0-6. 历史调研（理解演进）
- `_bmad-output/research/round-23-chatgpt-dr-response-v3-multi-vault-2026-05-10.md` — V3 ChatGPT 多 vault 反馈（已 cross-check 4/5 confirmed）
- `_bmad-output/research/round-23-multi-vault-implementation-plan-2026-05-10.md` — 多 vault 完整设计
- `_bmad-output/research/round-23-phase-a-retrieval-quality-2026-05-09.md` — RAG 召回精度调研

---

## 📂 选读文件（Tier 1 — context）

- `backend/lib/agentic_rag/state_graph.py` L530-728 — 主 RAG pipeline（含 rerank node 但 hook 不走）
- `backend/lib/agentic_rag/reranking.py` L57-370 — LocalReranker（priority-based 非 cross-encoder）
- `frontend/obsidian-plugin/src/main.ts` — plugin 主入口（Cmd+Shift+E/C/D 现有快捷键模式）
- `canvas-vault/.canvas-config.yaml` — vault 配置（subject / vault_id 待 Phase B0 加）

---

## 🕒 关键 Commits 时间线

| Commit | 主题 |
|---|---|
| `5deb15a` | docs: study-question skill 设计 + V4 prompt（本议题来源）|
| `93ae117` | fix(phase-b0): m 中文 vault sanitize + 测试反 pattern + 4 preset |
| `ecf16f2` | fix(phase-a0.5): l hook 鉴权 + n 规范 + p taint |
| `aef95be` | fix(phase-a0): 修 j pattern 失配 + i tier-2 fallback 0.85 |
| `fa814e7` | feat: UserPromptSubmit hook 自动 RAG 注入（hook 主体）|

---

## 我们的核心设计假设（请逐一挑战）

### 假设 1: Hook 5s 预算 ≠ 设计 bug，是哲学边界
hook 永远做不到 query rewrite / multi-hop / Read 完整章节 / 强制结构化 — 这些必须放新 skill。**真的吗？**还是其实可以异步预处理 + cache？

### 假设 2: 4 类 query 路由（Definition/Procedure/Causal/Comparison）
解题 query 大致这 4 类，每类 pipeline 不同（Causal 不走 vector，走因果链遍历）。**这 4 类够吗？还是该 6-7 类？边界 case 怎么处理？**

### 假设 3: wikilink 2-hop BFS 足够（不做 3-hop）
2-hop 在 ~30 节点 vault 上 LightRAG 实测 F1 最优。**真的吗？**还是 3-hop 在解题场景必须？

### 假设 4: Phase 1 (4-6h) 单独 ship 可行
Skill 直接调现有 search_supplementary + Claude 200K context 自己 multi-step — 不加新 backend endpoint 就能产出"4 层结构"输出。**真的吗？**还是 Phase 2 backend endpoint 是必须？

### 假设 5: chat-with-context 跟 study-question 边界清晰
chat-with-context 是 plugin 触发的"上下文增强对话"，study-question 是"主动深度解题"。**用户能区分吗？**还是该合并成一个 skill 加 mode flag？

---

## 🎯 我授权你决定的 4 个 Q（必答 — 给推荐选项 + 详细理由）

### Q1: Phase 1 vs Phase 2 实施范围
- 选项 A: 只做 Phase 1 (4-6h, skill + SKILL.md + plugin 快捷键, 复用现有 search_supplementary)
- 选项 B: Phase 1 + Phase 2 (10-14h, 含 backend `/api/v1/study/decompose-search` endpoint)
- 选项 C: 别的方案（你提）

**你的推荐**: ___ + 详细理由 + 业界对照

### Q2: Query intent 分类机制
- 选项 A: 规则关键词（< 1ms 免费但漏分类风险）
- 选项 B: Claude Haiku 3s（精准但延迟高）
- 选项 C: 双层（规则优先 + Haiku 兜底模糊 case）
- 选项 D: 别的方案

**你的推荐**: ___ + 详细理由

### Q3: study-question 触发方式
- 选项 A: Plugin 快捷键 Cmd+Shift+Q（一致性，符合现有 E/C/D pattern）
- 选项 B: 用户在 Claudian 直接打 `/study-question 概念`（无快捷键）
- 选项 C: 双轨（快捷键 + 命令字都支持）
- 选项 D: 别的方案

**你的推荐**: ___ + 详细理由 + UX 业界对照

### Q4: 输出结构强制度
- 选项 A: 强制 4 段（定义/直觉/反例/联系），违反 = Skill 失败
- 选项 B: 推荐 4 段，但 Claude 可根据 query 类型调整
- 选项 C: 完全自由（不强制结构，靠 prompt engineering 引导）
- 选项 D: 别的方案

**你的推荐**: ___ + 详细理由（注意 Causal/Procedure 类需要不同结构）

### Q5/Q6 (额外补充)
你认为我们漏了哪些必须决策的 Q？请补充并给推荐答案。

---

## 对抗性挑战（5 任务）

### 1. 验证我们的痛点诊断
hook 真的不能 multi-hop / 长 context 吗？读 chat.py:589-696 + supplementary_search_service.py 确认。
是否其实可以让 hook **异步**做 multi-hop（hook 返回 partial，后续异步补全）？

### 2. 挑战 4 类 query 路由设计
- "局部最优陷阱"是 Definition 还是 Procedure？分类边界如何处理？
- Causal 走"图遍历不走 vector"会不会丢真相关材料？
- 双层分类（规则 + Haiku）真的比单层稳吗？

### 3. 提出 2 套对抗替代方案

**方案 X**: 不新建 skill，**强化 chat-with-context** 加 query intent 路由。理由：减少 skill 数量，降低用户认知负担。

**方案 Y**: 完全反其道 — 不做 query rewrite，而是**让 Claude Opus 用 200K context 直接读全 vault**。理由：长 context 模型已经 in-context multi-hop。

请对比我们的方案 vs X/Y，给决策矩阵 + 推荐。

### 4. 设计 study-question vs chat-with-context UI 边界
两个 skill 都做 RAG，怎么避免用户混淆？
- 命令字不同（/study-question vs Cmd+Shift+E）够吗？
- 还是 study-question 入口应该提示"你是不是想用 chat-with-context"？

### 5. 评估 Phase 1 (4-6h) 单独 ship 可行性
- 不加 backend endpoint，仅靠 SKILL.md + 现有 search_supplementary，能不能产出"4 层结构"输出？
- 还是 Phase 2 backend endpoint 是必须（query rewrite 必须在 backend）？

---

## Constraints (你的方案必须满足)

- 本地 macOS M-series（M1 Max / M3 Max），无 NVIDIA GPU
- 30-45s study-question 总预算（vs 5s hook）
- bge-m3 embedding 锁定
- 不 fork Claudian / Obsidian
- 跟现有 4 个 skill 边界清晰（chat-with-context / node-chat / ai-linked-doc / configure-whiteboard）
- Apache-2.0 / MIT 兼容

---

## Desired Output Format

1. **Q1-Q4 各自决定**（你的推荐 + 详细理由 + 业界对照）⭐ 这是最重要的产出
2. **Q5/Q6 补充**（你认为我们漏了什么）
3. **5 个核心设计假设挑战结论**（哪些成立 / 哪些不成立）
4. **4 类 query 路由对抗结论**
5. **方案 X / Y 决策矩阵**（vs 我们当前方案）
6. **study-question vs chat-with-context UI 边界设计**
7. **Phase 1 vs Phase 2 必要性评估**
8. **你的最终推荐**（按 priority 排）
9. **你认为我们最大的盲点**（一段长答）

---

## What I Specifically Want You to Push Back On

不要只赞美我们的方案。请尖锐地：
- "Hook 5s 预算是哲学边界" — 真的吗？还是我们图省事？现代 RAG 系统 (Perplexity Lazy Loading) 怎么处理这个？
- "wikilink 2-hop 够" — 业界 GraphRAG / LightRAG 用 2-hop 还是 3-hop？我们 vault 节点数小于 100 是不是该 3-hop？
- "Phase 1 单独 ship 能做出 4 层结构" — 真的吗？还是必须 Phase 2 backend query rewrite 才行？
- "新建 skill 比扩展 chat-with-context 好" — 用户认知负担 + skill 数量 5 个会不会过多？
- 我们 "4 类 query 路由" 是否对应业界（Perplexity Search Intent / NotebookLM Mode）有更成熟分类？

## Output Length

不限。每个 Q 决策详细到工时级 + 业界对照引用。
~~~~~~

---

## V4 ChatGPT 返回后工作流

1. 报告 ship 到 `_bmad-output/research/round-23-chatgpt-dr-response-v4-study-question-2026-05-10.md`
2. Claude 启动 4-6 个并行 cross-check agent 验证 ChatGPT 关键 claim（特别是 Q1-Q4 决策 + 漏诊 Q5/Q6）
3. 综合 → 决定 Phase 1 / Phase 2 实施
4. 启动 dev → ship → mini-UAT 闭环

## V1 vs V2 vs V3 vs V4 关键决策对比

| 决策 | V1 | V2 | V3 | V4 |
|---|---|---|---|---|
| 焦点 | 单 vault 范式 (X/Y/Z) | 单 vault 7 根因修复 | 多 vault 架构 | **解题 skill 设计 + 决策授权** |
| 决策权 | 用户决定 | 用户决定 | 用户决定 | **ChatGPT 决定 (用户授权)** |
| 关键产出 | 范式选择 | 7 根因 file:line | per-vault config schema | **4 个 Q 推荐 + 业界对照** |

---

*Generated 2026-05-09 03:01 (V1) + 2026-05-09 12:43 (V2) + 2026-05-09 14:00 (V3) + 2026-05-10 (V4 study-question 决策授权) — 待用户复制 V4 提示词到 ChatGPT Deep Research，回填响应到 round-23-chatgpt-dr-response-v4-study-question-2026-05-10.md*
