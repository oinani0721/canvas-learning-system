---
title: "Round-23 BKT+FSRS+多段推理 整合方案 2026 成熟度重新评估 — ChatGPT Deep Research 提示词"
type: "deep-research-prompt"
date: "2026-05-08"
trigger: "Round-22 fork mvp 弃用后，重新审视 Round-15 调研结论（4 大机制无生产级先例）是否仍成立"
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
target_research_engine: "ChatGPT Deep Research (GPT-5 Pro 推荐 / o1 备选)"
expected_output_length: "8000-15000 字"
---

# Round-23 BKT+FSRS+多段推理 整合方案 2026 成熟度重新评估

## 使用说明

> 把以下 `### ChatGPT Prompt 起点` 段全选复制，粘贴到 ChatGPT Deep Research（推荐 GPT-5 Pro 或 o1 with browse），让其执行 deep research。预期输出 8000-15000 字综合报告。

---

### ChatGPT Prompt 起点

```
# Deep Research Request: BKT + FSRS + Multi-hop Reasoning + Annotation 整合方案 2026 成熟度重新评估

## Background

我在做一个个人学习系统 "Canvas Learning System"，技术栈是 Obsidian 插件 + FastAPI 后端 + Neo4j + LanceDB + Graphiti（episodic memory）。

我在 2026 年 5 月初做过一轮深度调研（私有 Round-15 报告），结论是：BKT（Bayesian Knowledge Tracing 掌握度建模）+ FSRS（Free Spaced Repetition Scheduler 复习调度）+ 多段推理出题 + 批注/错误整合 这 4 大机制的**联动整合方案在教育产品生产级实现 near-zero**，最接近的开源是 HKUDS/DeepTutor (2025 arXiv 2604.26962)。

我之后基于这个结论 fork DeepTutor 做了 10 天 MVP 集成尝试 (Round-22)，但实测后弃用，原因：

1. 60KB vault 喂 RAG 是 over-engineering（Karpathy LLM Wiki 阈值实证 — Liu 2023 Lost in Middle / Cuconasu SIGIR 2024 Power of Noise / Chroma 2025 Context Rot）
2. DeepTutor 内部 v2 adapter 注入路径有 DEAD-WRITE bug
3. fork 输出内容质量低（章节索引展开 vault md frontmatter 噪音 + AI 自由发挥与 vault 实际内容脱节）

所以我决定回归 Canvas + Obsidian Hybrid 架构，自建 4 大机制。但需要先确认 Round-15 的结论 (2026-05-05) 是否在 2026-05-08 仍然成立 — 这就是本次 Deep Research 的目标。

## My Original Integration Requirement (2026-05-05 原话)

> "我们的个人记忆系统所使用的是 Graphiti，那么我们各个节点之间是有用 BKT 来标记理解程度，然后用到 FSRS 来标记出复习时间，那么我们这里的核心压力点：
>
> 1. 能不能推测出各个原白板精确复习时间；
> 2. 能不能在使用原白板生成检验白板时，是否可以精确的多段推理各个节点之间的关系，然后能理解到我各个节点相关内容所标记的理解程度，各个节点犯下的错误，以及各个节点我自己打下的批注，结合以上节点考察我，让我想起了原白板的内容，并且再次考察我是否会犯下原白板中相似的错误。"

这是**整合诉求**，不是 4 个独立技术问题 — BKT 标记 + FSRS 调度 + 多段推理出题 + 批注/错误整合 必须**联动起来一起做出来才有用**。

## What I Tried (失败/部分成功的方案)

### Round-15 调研结论 (2026-05-05)

- BKT (1995 Corbett & Anderson)：学术成熟，但**生产级 BKT + FSRS 联动**的开源 near-zero
- FSRS：Anki 7 亿条复习数据训练，单独使用成熟，但**与 BKT mastery 联动**未见公开实现
- 多段推理出题（Knowledge Graph CQ）：MDPI 2025 / DeepTutor 2025 学术活跃，**教育场景生产 near-zero**
- 批注/错误整合考察：完全没有公开方案

### Round-22 DeepTutor Fork MVP (2026-05-06~08)

- fork HKUDS/DeepTutor（commit 9389178，v1.3.7）
- 实施 10 天 MVP 集成，路径 B（vault → spine 直注绕过 LLM）
- 实测后弃用（理由见 Background 第 3 段）

## Specific Research Questions

请你 deep research 以下 5 个问题：

### Q1. BKT 在 2025-2026 的生产级新方案

- **2024-2026** 有没有比经典 BKT (Corbett 1995) 更好的开源生产级 mastery tracking 方案？
- 候选关键词：DKT (Deep Knowledge Tracing), AKT (Attention KT), DKVMN, GKT (Graph-based KT), SAKT, SAINT, IRT (Item Response Theory)
- 重点找 **GitHub > 1000 stars + 有真实生产部署案例**的项目（不要纯学术 prototype）
- 是否有与 Anki/SuperMemo 风格 spaced repetition 联动的实证

### Q2. FSRS 与 mastery model 的联动方案

- FSRS-4.5 / FSRS-5（Open Spaced Repetition）是否已有官方支持 "external mastery signal" 输入？
- Anki 21.10+ 是否暴露 FSRS 内部 difficulty/stability/retrievability 字段供外部读写？
- 有没有项目把 BKT/DKT 的 P(mastery) 与 FSRS 的 retrievability 联动调度的开源实现？

### Q3. Knowledge Graph + LLM 多段推理出题（除 DeepTutor 外）

- 2025-2026 有哪些**生产部署的**"读取 KG → 多 hop reasoning → 生成考察题"方案？
- 候选关键词：KG-CQ (MDPI 2025), Educational Question Generation, Multi-hop QG, GraphRAG-based assessment, LightRAG question gen
- 重点关注：**给定一个 atomic concept node，能否多 hop 到相关概念，结合 mastery + error + 用户批注，生成针对性出题**
- DeepTutor 的 IdeationAgent + SpineSynthesizer + BlockGenerator 三阶段管道之外，有没有更轻量的实现（不用 fork 整个 webapp）

### Q4. 批注 + 错误 + 个人记忆 整合到 Canvas/Obsidian 的成熟方案

- Obsidian Spaced Repetition / Obsidian-to-Anki / RemNote 等是否支持把 **callout 批注 + 错题历史 + 概念依赖** 联合喂给 LLM 做考察生成？
- 有没有项目实现 "用户在 PKM 写笔记 → 自动抽取 mistake/confusion → 形成 episodic memory → 复习时调度+多段推理出题"
- Heptabase / Tana / Reflect 的 AI 是否在这条链路上已有实现？

### Q5. 60KB Vault Scale 下的最优架构推荐

- Karpathy llm-wiki Gist (2026-04) 主张 ~100 sources / ~400K words "compile once + inline" 优于 RAG。我 vault 60KB / 14 文件 / ~30-50 chunks 完全在这个范围
- 在这个 scale 下，BKT+FSRS+多段推理+批注 整合的**最佳工程架构**是什么？
- RAG 是否真的没必要？Anthropic Citations API / Long Context (1M) / Karpathy LLM Wiki 模式哪个更适合？
- 4 个机制各自的最低成本生产级实现（Python 库 / Node.js / Obsidian plugin）

## Constraints

- **现有架构**: Obsidian (vault md + plugin) + FastAPI + Neo4j (KG) + LanceDB (向量) + Graphiti (episodic memory) + Ollama (bge-m3 embedding) + Meridian (Anthropic Claude proxy)
- **LLM**: Claude Opus 4.7 (Anthropic Max 订阅 via Meridian) + 本地 bge-m3
- **Scale**: vault 60KB / 14 文件 / 个人单用户 / 单学科 vault
- **不接受**: 重新 fork 大 webapp（已尝试 DeepTutor 失败）/ 强 LLM 依赖（Karpathy 哲学）/ 黑盒 SaaS（要本地可控）
- **接受**: Python/Node 库引入 / Obsidian plugin 扩展 / 单一 sidecar agent 集成

## Files / Resources to Reference

### 我的 GitHub Repo（请你 fetch 阅读）

**主仓 URL**: https://github.com/oinani0721/canvas-learning-system

两个 active branches 含我所有调研 + 代码：

- **`worktree-feature-obsidian-hybrid-dev`**（最新 commit `f8bff1d`，当前主线）— Obsidian Hybrid 路径所有 Epic-1 v2 17/17 + Epic-2/3 部分实现
- **`worktree-feature-deeptutor-canvas-mvp`**（最新 commit `b0c882d`，弃用归档）— Round-22 fork MVP 完整实施记录 + 弃用决策报告

### 必读调研报告（按优先级）

| # | 文件 | branch | 价值 | 字数 |
|---|---|---|---|---|
| 1 | [round-14-graphiti-retrieval-deep-explore-2026-05-05.md](https://github.com/oinani0721/canvas-learning-system/blob/worktree-feature-obsidian-hybrid-dev/_bmad-output/research/round-14-graphiti-retrieval-deep-explore-2026-05-05.md) | obsidian-hybrid | **Graphiti 4 残缺诊断** + 用户原话 5 点批注 | ~8000 |
| 2 | [round-15-bkt-fsrs-multihop-tauri-prd-deep-explore-2026-05-05.md](https://github.com/oinani0721/canvas-learning-system/blob/worktree-feature-obsidian-hybrid-dev/_bmad-output/research/round-15-bkt-fsrs-multihop-tauri-prd-deep-explore-2026-05-05.md) | obsidian-hybrid | **4 大机制学术调研** + 首次提议 fork DeepTutor (line 155) | ~6000 |
| 3 | [round-21-canvas-five-core-deeptutor-integration-2026-05-06.md](https://github.com/oinani0721/canvas-learning-system/blob/worktree-feature-obsidian-hybrid-dev/_bmad-output/research/round-21-canvas-five-core-deeptutor-integration-2026-05-06.md) | obsidian-hybrid | **92KB Canvas 5 大核心 vs DeepTutor 集成对比**（最大调研） | ~92KB |
| 4 | [round-22-rag-degradation-and-paradigm-report-2026-05-08.md](https://github.com/oinani0721/canvas-learning-system/blob/worktree-feature-deeptutor-canvas-mvp/_bmad-output/research/round-22-rag-degradation-and-paradigm-report-2026-05-08.md) | deeptutor archive | **RAG noise + paradigm 分析 + Karpathy LLM Wiki 论证** | ~5000 |
| 5 | [round-22-pivot-to-obsidian-hybrid-2026-05-08.md](https://github.com/oinani0721/canvas-learning-system/blob/worktree-feature-deeptutor-canvas-mvp/_bmad-output/research/round-22-pivot-to-obsidian-hybrid-2026-05-08.md) | deeptutor archive | **fork 弃用综合报告** | ~6000 |
| 6 | [round-12-graphiti-karpathy-5-conjectures-audit-2026-04-21.md](https://github.com/oinani0721/canvas-learning-system/blob/worktree-feature-obsidian-hybrid-dev/_bmad-output/research/round-12-graphiti-karpathy-5-conjectures-audit-2026-04-21.md) | obsidian-hybrid | 用户提出"个人记忆系统 10+ 场景" | ~5000 |
| 7 | [round-13-wikilink-vs-graphiti-five-questions-answer-2026-04-29.md](https://github.com/oinani0721/canvas-learning-system/blob/worktree-feature-obsidian-hybrid-dev/_bmad-output/research/round-13-wikilink-vs-graphiti-five-questions-answer-2026-04-29.md) | obsidian-hybrid | wikilink vs Graphiti 5 大问题 | ~4000 |

### 必读代码文件（评估自建实力）

#### Backend (Canvas FastAPI) — `backend/app/`

| 模块 | 文件 | 与 4 大机制对应 |
|---|---|---|
| **Mastery / BKT** | [services/mastery_engine.py](https://github.com/oinani0721/canvas-learning-system/blob/worktree-feature-obsidian-hybrid-dev/backend/app/services/mastery_engine.py) | BKT/DKT 等 mastery 计算引擎 |
| **Mastery 存储** | [services/mastery_store.py](https://github.com/oinani0721/canvas-learning-system/blob/worktree-feature-obsidian-hybrid-dev/backend/app/services/mastery_store.py) | mastery 持久化 |
| **Mastery 融合** | [services/mastery_fusion.py](https://github.com/oinani0721/canvas-learning-system/blob/worktree-feature-obsidian-hybrid-dev/backend/app/services/mastery_fusion.py) | 多源 mastery 信号融合 |
| **Mastery 模型** | [models/mastery_models.py](https://github.com/oinani0721/canvas-learning-system/blob/worktree-feature-obsidian-hybrid-dev/backend/app/models/mastery_models.py) | mastery state schema |
| **Graphiti SDK 封装** | [clients/graphiti_client.py](https://github.com/oinani0721/canvas-learning-system/blob/worktree-feature-obsidian-hybrid-dev/backend/app/clients/graphiti_client.py) | episodic memory 接入 |
| **Graphiti 时序客户端** | [lib/agentic_rag/clients/graphiti_temporal_client.py](https://github.com/oinani0721/canvas-learning-system/blob/worktree-feature-obsidian-hybrid-dev/backend/lib/agentic_rag/clients/graphiti_temporal_client.py) | Graphiti 时间维度查询（独立 lib） |
| **Memory 服务** | [services/memory_service.py](https://github.com/oinani0721/canvas-learning-system/blob/worktree-feature-obsidian-hybrid-dev/backend/app/services/memory_service.py) | 个人记忆系统主服务 |
| **AutoSCORE 评分** | [services/autoscore.py](https://github.com/oinani0721/canvas-learning-system/blob/worktree-feature-obsidian-hybrid-dev/backend/app/services/autoscore.py) | 4 维评分（含 mastery 反馈） |
| **Calibration Tracker** | [services/calibration_tracker.py](https://github.com/oinani0721/canvas-learning-system/blob/worktree-feature-obsidian-hybrid-dev/backend/app/services/calibration_tracker.py) | 评分校准 |
| **错误管理（Round-14 残缺 #2）** | [tools/error_tools.py](https://github.com/oinani0721/canvas-learning-system/blob/worktree-feature-obsidian-hybrid-dev/backend/app/tools/error_tools.py) | line 132 写入用旧 `cs188` group_id |
| **候选服务（Story 2.5.X）** | [services/candidate_service.py](https://github.com/oinani0721/canvas-learning-system/blob/worktree-feature-obsidian-hybrid-dev/backend/app/services/candidate_service.py) | 错误候选用户主权 |
| **Mastery 注入 RAG** | [lib/agentic_rag/mastery_injection.py](https://github.com/oinani0721/canvas-learning-system/blob/worktree-feature-obsidian-hybrid-dev/backend/lib/agentic_rag/mastery_injection.py) | mastery 注入 retrieval |
| **Wikilink 图建设** | [services/wikilink_graph_service.py](https://github.com/oinani0721/canvas-learning-system/blob/worktree-feature-obsidian-hybrid-dev/backend/app/services/wikilink_graph_service.py) | vault 双链网络建模 |
| **RAG 主服务** | [services/rag_service.py](https://github.com/oinani0721/canvas-learning-system/blob/worktree-feature-obsidian-hybrid-dev/backend/app/services/rag_service.py) | 检索主管道 |
| **Chat 上下文装配** | [services/chat_context_assembler.py](https://github.com/oinani0721/canvas-learning-system/blob/worktree-feature-obsidian-hybrid-dev/backend/app/services/chat_context_assembler.py) | Story 2.1 上下文注入 |
| **Agent 服务** | [services/agent_service.py](https://github.com/oinani0721/canvas-learning-system/blob/worktree-feature-obsidian-hybrid-dev/backend/app/services/agent_service.py) | LangGraph agent 主入口 |

#### Plugin (Obsidian) — `frontend/obsidian-plugin/src/`

| 文件 | 用途 |
|---|---|
| [main.ts](https://github.com/oinani0721/canvas-learning-system/blob/worktree-feature-obsidian-hybrid-dev/frontend/obsidian-plugin/src/main.ts) | plugin 主入口 + 12 命令注册 |
| [ai-linked-doc.ts](https://github.com/oinani0721/canvas-learning-system/blob/worktree-feature-obsidian-hybrid-dev/frontend/obsidian-plugin/src/ai-linked-doc.ts) | Story 1.17 AI 派生节点 |
| [callout.ts](https://github.com/oinani0721/canvas-learning-system/blob/worktree-feature-obsidian-hybrid-dev/frontend/obsidian-plugin/src/callout.ts) | Story 1.16 批注 hotkey |
| [configure-whiteboard.ts](https://github.com/oinani0721/canvas-learning-system/blob/worktree-feature-obsidian-hybrid-dev/frontend/obsidian-plugin/src/configure-whiteboard.ts) | Story 1.19 白板建设 |
| [error-candidate-helpers.ts](https://github.com/oinani0721/canvas-learning-system/blob/worktree-feature-obsidian-hybrid-dev/frontend/obsidian-plugin/src/error-candidate-helpers.ts) | Story 2.5.X 错误候选 |
| [node-chat-context.ts](https://github.com/oinani0721/canvas-learning-system/blob/worktree-feature-obsidian-hybrid-dev/frontend/obsidian-plugin/src/node-chat-context.ts) | Story 3.1 节点对话 |

#### 项目状态文件

| 文件 | 用途 |
|---|---|
| [CURRENT_TASK.md](https://github.com/oinani0721/canvas-learning-system/blob/worktree-feature-obsidian-hybrid-dev/CURRENT_TASK.md) | 当前任务恢复锚点（Round-22 弃用 + Round-14 回归） |
| [_bmad-output/implementation-artifacts/sprint-status.yaml](https://github.com/oinani0721/canvas-learning-system/blob/worktree-feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/sprint-status.yaml) | 全 Epic 状态：Epic-1 v2 17/17 done / Epic-2/3 部分 review |
| [_bmad-output/.claude/CLAUDE.md](https://github.com/oinani0721/canvas-learning-system/blob/worktree-feature-obsidian-hybrid-dev/_bmad-output/.claude/CLAUDE.md) | BMAD 工作流契约 + DoD-3 v3.0 双段铁律 |

#### Vault 样本（用户实际数据）

| 文件 | 用途 |
|---|---|
| [canvas-vault/原白板/CS 61B.md](https://github.com/oinani0721/canvas-learning-system/blob/worktree-feature-obsidian-hybrid-dev/canvas-vault/%E5%8E%9F%E7%99%BD%E6%9D%BF/CS%2061B.md) | 白板 frontmatter 实例 + Recent Activity 段 |
| [canvas-vault/节点/cs-61b-csm.md](https://github.com/oinani0721/canvas-learning-system/blob/worktree-feature-obsidian-hybrid-dev/canvas-vault/%E8%8A%82%E7%82%B9/cs-61b-csm.md) | atomic concept 节点实例 |
| [canvas-vault/节点/Eigenvalues-are-special-vectors-that-sat.md](https://github.com/oinani0721/canvas-learning-system/blob/worktree-feature-obsidian-hybrid-dev/canvas-vault/%E8%8A%82%E7%82%B9/Eigenvalues-are-special-vectors-that-sat.md) | AI 派生节点 frontmatter (含 derived-from / source_board / relationships[]) |

### 公开资源（请你访问验证）

- HKUDS/DeepTutor: https://github.com/HKUDS/DeepTutor (arXiv 2604.26962)
- Open Spaced Repetition / FSRS: https://github.com/open-spaced-repetition
- Karpathy llm-wiki Gist: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
- Anthropic Citations API: https://www.anthropic.com/news/introducing-citations-api
- Lost in the Middle (Liu 2023 TACL): https://arxiv.org/abs/2307.03172
- The Power of Noise (Cuconasu SIGIR 2024): https://arxiv.org/abs/2401.14887
- Context Rot (Chroma 2025): https://research.trychroma.com/context-rot

### 阅读策略建议

如果时间有限（Deep Research mode 可能 token 限制），推荐 ChatGPT 阅读优先级：

1. **必读 (~30K tokens)**: Round-14 + Round-15 + sprint-status.yaml + CURRENT_TASK.md（理解需求 + 当前状态）
2. **强推荐 (~50K tokens)**: + Round-21 92KB（5 大核心愿景）+ Round-22 弃用 2 报告（fork 失败教训）
3. **代码深读 (~20K tokens)**: + mastery_engine.py + graphiti_client.py + error_tools.py + memory_service.py（评估自建实力 + Round-14 残缺位置）

总计约 100K tokens 完整 context。Deep Research 应足够。

## Desired Output Format

输出一份 8000-15000 字综合报告，含：

### Section 1 · 5 问题各自的最新答案 (1500 字 × 5 = 7500 字)

每个问题含：
- 学术 / 工业最新进展 (2024-2026)
- 3-5 个具体工具 / 库 / 论文（含 GitHub URL + stars + last commit + 维护活跃度）
- 生产部署案例（如有）
- 与我现有架构（Obsidian + FastAPI + Neo4j + Graphiti）的契合度评估

### Section 2 · 整合方案推荐 (1500 字)

不要列单独技术，直接给 1-3 个**整合架构推荐**：
- "BKT 用 X 库 + FSRS 用 Y 项目 + 多段推理用 Z 框架 + 批注整合用 W 模式"
- 每个推荐含工程量评估（人天）+ 风险点 + 与 Canvas 现有架构的接入方式

### Section 3 · Round-15 结论 (2026-05-05) 在 2026-05-08 是否仍成立 (500 字)

明确回答：
- **仍成立** — 4 大机制整合 near-zero（如是，给出新的最接近实现 + 距离 production 的 gap）
- **不再成立** — 有新方案出现（如是，详细推荐）
- **部分成立** — 哪些机制已成熟 / 哪些仍 gap

### Section 4 · 5 个具体行动项 (500 字)

直接给我 5 个最高 ROI 的 actionable steps（按工程量排序），假设我从今天开始 5 day full-time 工作，能做到的最大产出。

## 注意事项

- 不要泛论 / 不要列学术综述
- 每个推荐必须有 GitHub URL + 实证（stars / commits / production case）
- 优先 2024-2026 年的方案，2023 之前的只列经典基础
- 优先开源（不要 SaaS）
- 优先 Python / Node / TypeScript 生态（不要 Rust/Go 重写）
- 重点回答"我能不能 5-10 天内做出来"，不是"未来 5 年学术展望"

请开始 deep research。
```

---

## ChatGPT 提交后预期收到的报告结构

ChatGPT Deep Research 通常输出：
1. Section 1: 5 questions answered (~7500 words)
2. Section 2: Integration recommendations (~1500 words)
3. Section 3: 2026-05-08 verdict (~500 words)
4. Section 4: 5 actionable steps (~500 words)
5. Sources cited (50-100 URLs)

预计耗时 5-15 分钟（Deep Research 模式）。

---

## 收到 ChatGPT 报告后回到 Claude Code 的下一步

把 ChatGPT 报告全文 paste 进新 Claude session，让 Claude:
1. 与 Round-14/15/21/22 私有调研对照
2. 识别新发现的工具 / 论文
3. 设计 Canvas Round-23 实施计划（接受/部分接受/拒绝 ChatGPT 推荐）
4. 写到 `_bmad-output/research/round-23-chatgpt-dr-result-2026-05-08.md` 归档

---

## Claude 这边等待

我等你跑完 ChatGPT Deep Research 后回来，paste 报告 → 立即开始对照分析 + Round-23 实施计划设计。

---

*Round-23 deep research 提示词。基于 Round-15 (2026-05-05) 的"4 大机制无生产级先例"结论 + Round-22 fork mvp 弃用 (2026-05-08) 后的重新审视。*
