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

*Generated 2026-05-09 — 待用户复制提示词到 ChatGPT Deep Research，回填响应到 round-23-chatgpt-dr-response-2026-05-09.md*
