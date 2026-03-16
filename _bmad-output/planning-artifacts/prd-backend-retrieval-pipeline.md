---
stepsCompleted:
  - step-01-init
  - step-02-discovery
  - step-03-success
  - step-04-journeys
  - step-05-domain
  - step-06-innovation
  - step-07-project-type
  - step-08-scoping
  - step-09-functional-requirements
  - step-10-nonfunctional-requirements
  - step-11-polish
  - step-12-complete
classification:
  projectType: backend_service
  domain: edtech
  complexity: high
  projectContext: brownfield
inputDocuments:
  - _bmad-output/brainstorming/brainstorming-session-P0-chunking-pipeline-2026-03-11.md
  - _bmad-output/brainstorming/brainstorming-session-S7-A2-reranking-crag-2026-03-13.md
  - _bmad-output/brainstorming/implementation-roadmap-2026-03-13.md
  - _bmad-output/brainstorming/brainstorming-session-S8-A4-indexing-pipeline-2026-03-13.md
  - _bmad-output/brainstorming/brainstorming-session-A5-multimodal-retrieval-2026-03-12.md
  - _bmad-output/brainstorming/brainstorming-session-S1-dead-code-cleanup-2026-03-11.md
  - _bmad-output/brainstorming/brainstorming-session-2026-03-11.md
  - _bmad-output/brainstorming/brainstorming-session-S3-pipeline-postprocessing-2026-03-12.md
  - _bmad-output/brainstorming/brainstorming-session-2026-03-12.md
  - _bmad-output/brainstorming/brainstorming-session-S5-A3-new-features-2026-03-13.md
  - _bmad-output/brainstorming/session-A-end-memory-system-1-2026-03-13.md
  - docs/canvas-backend-research-report.md
  - docs/community-product-research.md
  - docs/architecture/index.md
  - _bmad-output/planning-artifacts/prd.md
documentCounts:
  briefs: 0
  research: 2
  brainstorming: 11
  projectDocs: 60+
projectType: brownfield
workflowType: 'prd'
---

# Product Requirements Document - Canvas 后端检索管道升级

**Author:** ROG
**Date:** 2026-03-15
**Project Type:** Backend Service（FastAPI + LanceDB + Neo4j/Graphiti + LangGraph）
**Domain:** EdTech — AI 学习系统的检索基础设施
**Relation:** 本文档是主 PRD（Canvas Learning System PRD）的专项补充，聚焦后端检索管道的修复和升级。

---

## Executive Summary

本专项 PRD 定义了 Canvas Learning System 后端检索管道的修复和升级方案。经过 10 个 brainstorming session（A1-A5 + S1-S5）的深度讨论、10+ 次独立代码对抗性审查、10+ 次社区/论文调研，以及与用户的逐项审查确认，形成了完整的检索管道升级蓝图。

**核心目标**：让系统能从用户的 Obsidian 笔记中精确检索到相关片段，为主 PRD 中的所有上层功能（节点对话、Edge 对话、检验白板、/命令技能等）提供底层检索能力。

**当前状态**：管道框架存在但严重损坏——6 条搜索通道中 4 条返回空、排序器是空壳、质量检查永远误判、配置传递断裂、中文搜索不工作、索引无去重。

**升级后状态**：6 条搜索通道全部打通、bge-m3 中英双语模型、智能分块、混合搜索、bge-reranker 精排、CRAG 质量门控、文件指纹增量索引、图片 OCR 检索、按课程/标签范围过滤。

**实施策略**：4 Phase 渐进式（Phase 0 基础修复 → Phase 1 核心升级 → Phase 2 新功能 → Phase 3 前端集成），预计 20-28 天（部分并行）。

---

## 成功标准

### 检索质量

| 指标 | 目标值 | 来源 | 说明 |
|------|--------|------|------|
| Precision@5 | >= 0.70 | RAG 生产验收标准（Session A 调研确认） | 搜到的前 5 条结果中，至少 3.5 条是真正相关的 |
| Recall@10 | >= 0.80 | RAG 生产验收标准 | 真正相关的内容，80% 能被搜到 |
| MRR@10 | >= 0.70 | RAG 生产验收标准 | 最相关的结果平均排在前 1-2 位 |
| 中文检索可用 | 中文查询和英文查询效果相当 | 社区验证（LanceDB + jieba） | 解决当前 FTS 不支持中文的问题 |

### 管道打通

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 搜索通道存活率 | 6/6 通道返回真实数据 | 当前仅 2/6 工作 |
| Reranker 生效 | 精排后 MRR 提升 >= +0.10 | 当前是空壳（return results） |
| CRAG 健康触发率 | 15-30% | 当前 100% 误触发（分数域不匹配） |
| Config 传递 | 10/10 配置参数生效 | 当前 0/10（adapter.py L195 bug） |
| 索引无重复 | 修改 N 次笔记后仍只有 1 份 | 当前纯 append 无去重 |

### 性能

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 单次检索延迟 | < 3 秒 | 6 路并行搜索 + RRF + Reranker + CRAG |
| 增量索引延迟 | < 5 秒（改 1-3 个文件） | 文件指纹比对 + 只处理变化文件 |
| 全量重建（120 文件） | < 30 秒（GPU）/ < 2 分钟（CPU） | bge-m3 批量编码 |
| 全量重建（5000 文件） | < 4 分钟（GPU） | 三阶段自动加索引 |

### 可扩展性

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 笔记增长支持 | 120 → 10,000+ 无需改代码 | 文件指纹 + 三阶段自动升级 |
| LanceDB 搜索 | < 100ms（100K 向量以下） | 暴力搜索足够快，无需提前建索引 |
| 多学科支持 | cs188 硬编码清理（20+ 处） | 支持按 subject 隔离和切换 |

---

## 产品范围

### 本 PRD 覆盖的范围

| 模块 | Session 来源 | 说明 |
|------|-------------|------|
| **S1 死代码清理** | S1 | 归档 9 个未使用模块、修复幽灵表/假标记、防回退规则 |
| **S2 检索器修复** | S2 | 修复 4 条断裂搜索通道、统一 SearchResult 格式、激活混合搜索、中文分词 |
| **S3 管道后处理** | S3 | 激活 bge-reranker-v2-m3 精排、CRAG 三路质量门控、LLM 查询改写、分层融合 |
| **S4 Config 统一** | S4 | 修复 adapter.py L195 配置传递 bug、删除废弃 env_config.py、State 字段补全 |
| **A1 分块管道升级** | A1 | bge-m3 1024d 迁移、标题智能分块 512 token、原子保护（代码/公式/表格）、面包屑前缀 |
| **A2 重排序+CRAG+压缩** | A2 | 上下文 15K→3K 压缩、掌握度注入 prompt、查询改写（Multi-Query + Decomposition） |
| **A3 实施路线图** | A3 | 4 Phase 渐进实施、依赖关系管理、验收门控 |
| **A4 索引管道** | A4 | 文件指纹增量索引（delete-before-insert）、防双触发、精炼上下文、连通 FSRS/Graphiti |
| **A5 多模态检索** | A5 | 增强 Gemini OCR（图片→文字+分类+摘要+概念）、向量维度统一、管道断裂修复 |
| **S5 新功能** | S5 | Frontmatter 元数据过滤、Wiki-links 邻居检索、渐进范围搜索、跨课程桥接 |

### 本 PRD 不覆盖的范围（归主 PRD）

| 功能 | 归属 |
|------|------|
| Per-node 对话系统 | 主 PRD — 需新建 |
| Edge 对话三重策略 | 主 PRD — Layer 3 |
| 检验白板递归考察 | 主 PRD — Layer 3 |
| Tips/Edge 理由/错误记录的存储和检索 | 主 PRD — Graphiti 个人记忆 |
| Beta-Bayesian 五维融合 | 主 PRD — Layer 2 算法 |
| Calibration Tracking | 主 PRD — Layer 2 算法 |
| 对话归档 Hot-Warm-Cold | 主 PRD — 数据架构 |
| /命令技能注册系统 | 主 PRD — 新建 |
| 前端 Canvas 知识图谱 UI | 主 PRD — Phase 3 |

### 和主 PRD 的接口

本 PRD 的检索管道通过以下接口为主 PRD 提供能力：

| 接口 | 主 PRD 功能需求 | 本 PRD 提供 |
|------|----------------|-----------|
| FR-RET-01 | 语义+关键词混合检索 | Hybrid Search（bge-m3 Dense+Sparse + RRF） |
| FR-RET-02 | AI 对话自动检索相关上下文 | 6 路并行搜索 + Adaptive-k 动态数量 + 3K 上下文压缩 |
| FR-RET-03 | 利用 Graphiti 学习记忆增强 | Graphiti 作为 6 条搜索通道之一（S2-T1 修复） |
| FR-RET-04 | 智能路由 + 质量检查 + 自动重检索 | Agentic RAG L1（路由）+ L2（CRAG 质量门控） |
| FR-KG-06 | 图片 OCR 识别 | 增强 Gemini OCR + 文本管道索引 |
| FR-SYS-07 | 多学科隔离 | cs188 硬编码清理 + subject 字段 + 跨课程桥接 |

---

## 技术架构

### 完整检索管道

```
═══════════════════ 索引管道（笔记写入时）═══════════════════

笔记变化 → 文件指纹比对（A4）→ 只处理变化的文件
  → 文档解析 + Frontmatter 提取（S5）
  → 标题智能分块 512 token + 原子保护（A1）
  → 面包屑前缀 + Metadata 前缀（A1/S5）
  → bge-m3 Dense+Sparse 双向量化（A1）
  → delete-before-insert 去重存储（A4）
  → 图片节点 → Gemini OCR → 文本管道索引（A5）

═══════════════════ 检索管道（用户提问时）═══════════════════

用户提问
  → 查询理解 + 意图分析（A2）
  → 6 路并行搜索（S2）：
    ├─ LanceDB Dense 向量搜索
    ├─ LanceDB Sparse 关键词搜索（jieba 中文分词）
    ├─ Graphiti 知识图谱搜索（学习记忆）
    ├─ Vault 笔记搜索
    ├─ Obsidian CLI 图遍历（backlinks/links）
    └─ 图片搜索（Gemini OCR 文本匹配）
  → 渐进范围过滤（S5）：同课程 → 相关课程 → 全库
  → 分层 RRF 融合（S3）：3 组 → 跨组归一化
  → Adaptive-k 动态截取（社区调研补充）
  → bge-reranker-v2-m3 精排（S3）
  → CRAG 三路质量门控（S3）：好→通过 / 一般→补充 / 差→改写重搜
  → 上下文压缩 15K→3K（A2）
  → 掌握度注入 prompt 前端（A2）
  → 输出精确笔记片段 → 送给 LLM

═══════════════════ 基础设施层 ═══════════════════

S1 死代码清理 — 清除 5090 行废代码，暴露真实管道状态
S4 Config 修通 — adapter.py L195 一行修复让所有参数生效
A3 实施路线图 — 4 Phase 渐进式实施排期
A4 EventBus — 连接 FSRS/Graphiti/RAG 三系统
```

### 关键技术选型

| 组件 | 选型 | 否决方案 | 来源 |
|------|------|---------|------|
| Embedding 模型 | bge-m3（1024d，中英双语，Dense+Sparse+ColBERT 三合一） | OpenAI ada-002（贵）、all-MiniLM（中文差）、Qwen3-Embedding（不支持 Sparse） | A1 + 社区调研 |
| Reranker | bge-reranker-v2-m3（568M，CPU 可跑） | Cohere（付费）、ColBERT（索引成本高） | S3 + 社区调研 |
| 分块策略 | 标题智能分块 + 512 token 兜底 + 原子保护 | 语义分块（实测差 15%）、500 字符硬切（当前方案，质量差） | A1 + 社区调研 |
| 中文分词 | jieba 预分词（存入前空格分隔） | 无分词（当前方案，中文 FTS 不工作） | S2-T14 + 社区调研 |
| 索引策略 | 文件指纹 + delete-before-insert + 三阶段自动升级 | 全量重建（5000+ 文件时太慢）、merge_insert（会误删其他文件数据） | A4 + 社区调研 |
| 图片检索 | 增强 Gemini OCR（文字+分类+摘要+概念→文本管道） | BGE-VL/ColPali 视觉嵌入（后续阶段） | A5 + 社区调研 |
| 质量门控 | CRAG 二元评分（yes/no）+ 最多 2 次重试 | 数值阈值（不如二元可靠） | S3 + 社区调研 |
| 融合策略 | 3 组分层 RRF（k=60）+ z-score 跨组归一化 | 6 路扁平 RRF（效果差 3%） | S3 + 社区调研 |
| 检索数量 | Adaptive-k（分数断崖自动截取） | 固定 top-5（简单问题太多、复杂问题不够） | 社区调研 |
| LLM 提供商 | 不锁定（用户可配置 Gemini/Claude/GPT/本地） | — | 主 PRD 设计原则 |

---

## 实施计划

### Phase 0：基础修复（3-5 天）

> 目标：清理废代码、修通配置、激活已有功能，让管道从"全假"变"能跑"。

| # | 任务 | 来源 | 改动量 | 关键交付 |
|---|------|------|--------|---------|
| 0.1 | S1 死代码归档 | S1 | 9 模块移至 archive/ | 代码库清爽 |
| 0.2 | S1 幽灵表修复 + 假标记修复 | S1 | ~15 行 | 搜索不再查不存在的表 |
| 0.3 | S4 Config L195 修复 | S4 | 1 行 | 所有配置参数生效 |
| 0.4 | S4 删除 env_config.py | S4 | -283 行 | 消除配置混乱 |
| 0.5 | S3 激活 Reranker + CRAG + 查询改写 | S3 | ~50 行 | 精排+质量检查开始工作 |
| 0.6 | S2 修复 Graphiti 搜索通道（graphiti-core SDK） | S2-T1 | 中等 | 学习记忆可搜索 |
| 0.7 | S2 消除笔记重复搜索 | S2-T5 | 1 行 | 搜索结果不再重复 |
| 0.8 | S2 统一 SearchResult 格式 | S2-T6 | 中等 | 后续融合不再字段名出错 |
| 0.9 | A4 移除前端 canvas 双重触发 | A4 | -7 行 | 索引不再跑两遍 |
| 0.10 | A4 cs188 硬编码清理（20+ 处） | A4 | ~20 处 | 支持多学科 |

**验证门控**：编译通过 → import 通过 → 6/6 搜索通道返回数据 → Config 10/10 参数生效 → lint 通过

### Phase 1：核心升级（5-8 天）

> 目标：换模型、改分块、激活混合搜索，让检索从"能跑"变"好用"。

| # | 任务 | 来源 | 关键交付 |
|---|------|------|---------|
| 1.1 | A1 bge-m3 迁移（Dense 1024d） | A1 Sprint 1 | 中英双语搜索 |
| 1.2 | A1 重写分块算法（标题+句子边界+原子保护） | A1 Sprint 1 | 分块质量提升 |
| 1.3 | A1 面包屑前缀 + 索引路径修复 | A1 Sprint 1 | 每个片段知道自己的位置 |
| 1.4 | A1 bge-m3 Sparse + jieba 中文分词 | A1 Sprint 2 | 关键词搜索 + 中文支持 |
| 1.5 | S2 激活混合搜索（hybrid） | S2-T13 | 语义+关键词双路 |
| 1.6 | S3 Reranker 升级（bge-reranker-v2-m3 fp16） | S3 #3 | 精排质量达标 |
| 1.7 | S3 CRAG 二元评分 + 三路路由 | S3 #10 | 质量门控生效 |
| 1.8 | S3 分层融合（3 组 RRF + z-score） | S3 #7 | 融合质量提升 |
| 1.9 | A4 文件指纹增量索引（delete-before-insert） | A4 方向 1 | 索引无重复、可扩展 |
| 1.10 | S4 State 字段补全 + 初始化工厂 | S4 Round 3 | 数据流不再丢失 |
| 1.11 | 全量重建索引 | — | bge-m3 + 新分块生效 |

**验证门控**：50+ 真实查询 Golden Test Set、MRR >= +0.10、Reranker 延迟 <500ms、中文查询效果达标

### Phase 2：新功能（6-8 天，MVP 调整后缩短）

> 目标：加元数据过滤、图片检索、上下文压缩，让搜索变"聪明"。

| # | 任务 | 来源 | 关键交付 |
|---|------|------|---------|
| 2.1 | S5 Frontmatter 元数据解析 + LanceDB 列 | S5 功能 1 | 按课程/标签过滤 |
| 2.2 | S5 Wiki-links 邻居检索（1-hop 扩展） | S5 功能 2 | 追踪链接关系 |
| 2.3 | S5 渐进范围搜索（4 阶段级联） | S5 功能 3 | 智能扩大搜索范围 |
| 2.4 | S5 跨课程桥接（Tag Jaccard） | S5 功能 4 | 多学科关联 |
| 2.5 | A5 图片管道修复（向量维度+接口+存储） | A5 Phase 1 | 图片搜索管道打通 |
| 2.6 | A5 增强 Gemini OCR（结构化提取） | A5 MVP | 图片→可搜索文本 |
| 2.7 | A2 上下文压缩 15K→3K | A2 #5 | AI 输入精炼 |
| 2.8 | A2 掌握度注入 prompt | A2 #4 | AI 知道用户水平 |
| 2.9 | A2 查询改写（Multi-Query + Decomposition） | A2 #6 | 复杂问题拆分搜索 |
| 2.10 | Adaptive-k 动态检索数量 | 社区调研 | 简单问题少搜、复杂多搜 |
| 2.11 | A4 连通 FSRS/Graphiti EventBus | A4 方向 4 | 学习记忆影响搜索排序 |

### Phase 3：前端集成（和主 PRD Phase 3 并行）

> 目标：让前端插件能使用升级后的检索管道。

| # | 任务 | 说明 |
|---|------|------|
| 3.1 | API 端点适配新前端数据格式 | 主 PRD 的 per-node 对话需要调用检索管道 |
| 3.2 | Obsidian CLI vault 名可配置化 | 去掉 CS188 硬编码 |
| 3.3 | MCP Server 暴露检索工具 | 支持 Claude Code/OpenCode 通过 MCP 调用 |
| 3.4 | 行号引用追踪（heading_path + line range） | 检索结果附带精确位置信息 |

---

## 代码审查发现汇总

本 PRD 的所有技术方案均经过独立 agent 对抗性代码审查验证。以下为关键发现：

### CRITICAL 级（功能完全不工作）

| # | 模块 | 问题 | 修复方案 | Phase |
|---|------|------|---------|-------|
| C1 | adapter.py L195 | Config 传递断裂，10/10 参数无效 | `config={"configurable": config}` → `context=config` | 0.3 |
| C2 | nodes.py rerank | Reranker 空实现（return results） | 接入 bge-reranker-v2-m3 | 0.5 |
| C3 | state_graph.py CRAG | RRF 分数(max 0.098) vs 阈值(0.7) 永远误判 | 改用 reranker 分数 + 二元评分 | 0.5 |
| C4 | state_graph.py rewrite | 查询改写 = `f"请详细解释:{query}"` | 接入 LLM 改写 | 0.5 |
| C5 | graphiti_client.py | GraphitiClient 100% MOCK（MCP import 不工作） | 替换为 GraphitiTemporalClient | 0.6 |
| C6 | lancedb_client.py index | 纯 append 无去重（编辑 N 次 = N 份数据） | delete-before-insert | 1.9 |
| C7 | main.ts + canvas_service | 前后端双重触发索引 | 移除前端 canvas 监听 | 0.9 |
| C8 | lancedb_client.py L595 | index_single_file 丢失目录路径 | basename → relpath | 1.3 |

### HIGH 级

| # | 模块 | 问题 | 修复方案 | Phase |
|---|------|------|---------|-------|
| H1 | FTS | 中文搜索不工作（Tantivy 无中文分词） | jieba 预分词 | 1.4 |
| H2 | nodes.py 分块 | 500 字符硬切不保护代码/公式 | 标题分块+原子保护 | 1.2 |
| H3 | multimodal 管道 | 向量维度 384/768/1024 三处冲突 | 统一为 1024 | 2.5 |
| H4 | multimodal_store.py | 依赖注入无参数（client=None），全部返回空 | 正确注入 LanceDB+Graphiti client | 2.5 |
| H5 | config.py vs nodes.py | 权重定义不一致（5 源 vs 6 源） | 统一到 config.py | 0.3 |
| H6 | memory_service.py L660 | `self._neo4j_client` 拼写错误导致 Graphiti 桥接断裂 | 改为 `self.neo4j` | 2.11 |
| H7 | 全系统 | cs188 硬编码 20+ 处 | 统一改为配置化 | 0.10 |

---

## 功能需求

### 能力域 1：笔记索引

| ID | 功能需求 |
|----|---------|
| FR-IDX-01 | 系统自动检测 Obsidian vault 中 Markdown 文件的变化，通过文件指纹比对只处理修改过的文件 |
| FR-IDX-02 | 笔记按标题智能分块（512 token 上限），保护代码块、数学公式、表格不被切断 |
| FR-IDX-03 | 每个分块自动附带面包屑路径前缀（文档 > 章节 > 小节）和 Frontmatter 元数据前缀 |
| FR-IDX-04 | 使用 bge-m3 模型同时生成 Dense 向量和 Sparse 向量，支持语义搜索和关键词搜索 |
| FR-IDX-05 | 中文笔记在索引时通过 jieba 预分词处理，确保 FTS 索引能正确匹配中文词语 |
| FR-IDX-06 | 图片节点通过 Gemini OCR 提取文字+类型+摘要+概念，走文本索引管道 |
| FR-IDX-07 | 索引使用 delete-before-insert 模式，同一文件修改后旧数据自动清除 |
| FR-IDX-08 | 系统保留全量重建按钮，用于模型迁移或异常恢复 |

### 能力域 2：笔记检索

| ID | 功能需求 |
|----|---------|
| FR-RET-P-01 | 系统支持 6 路并行搜索（LanceDB Dense + Sparse + Graphiti + Vault + Obsidian CLI + 图片） |
| FR-RET-P-02 | 搜索支持按课程（course_id）和标签（tags）过滤范围 |
| FR-RET-P-03 | 搜索支持渐进范围扩展（同课程 → 相关课程 → 全库） |
| FR-RET-P-04 | Wiki-links 邻居自动扩展（搜到的笔记的 1-hop 链接笔记也纳入结果） |
| FR-RET-P-05 | 6 路结果通过 3 组分层 RRF 融合（Dense 组 / Graph 组 / Personal 组） |
| FR-RET-P-06 | 融合后的结果通过 bge-reranker-v2-m3 交叉编码器精排 |
| FR-RET-P-07 | 精排后通过 Adaptive-k 动态决定返回数量（分数断崖自动截取） |
| FR-RET-P-08 | 检索结果附带来源信息：文件路径 + heading 路径 + 起止行号 |

### 能力域 3：质量保障

| ID | 功能需求 |
|----|---------|
| FR-QA-01 | CRAG 质量门控对精排后的结果进行二元评分（相关/不相关） |
| FR-QA-02 | 全部不相关时自动改写查询并重新搜索（最多 2 次重试） |
| FR-QA-03 | 重试耗尽后安全降级（告知"信息不足"而非生成幻觉） |
| FR-QA-04 | 上下文压缩到 3K token（句子级提取，公式/代码整块保护） |
| FR-QA-05 | 掌握度信息注入 prompt 最前端位置（Lost in Middle 效应缓解） |

### 能力域 4：配置与运维

| ID | 功能需求 |
|----|---------|
| FR-OPS-01 | 所有配置参数通过 LangGraph Context API 正确传递到管道每个环节 |
| FR-OPS-02 | 搜索管道参数（融合权重、质量阈值、reranker 策略等）可通过配置文件调整 |
| FR-OPS-03 | 多学科支持：subject 字段隔离 + 跨学科 Tag Jaccard 桥接 |
| FR-OPS-04 | Obsidian CLI vault 名从配置读取（不再硬编码 CS188） |

---

## 非功能需求

### 性能

| 指标 | 目标值 | 场景 |
|------|--------|------|
| 6 路并行搜索 | 全部 asyncio.gather 并行 | 串行 3 秒 → 并行 500ms |
| Reranker 延迟 | < 200ms（CPU，top-20） | bge-reranker-v2-m3 fp16 |
| 增量索引 | < 5 秒（1-3 个文件变化） | 文件指纹 + delete-before-insert |
| 全量重建 | < 30 秒 GPU / < 2 分钟 CPU（120 文件） | bge-m3 batch encoding |

### 可靠性

| 指标 | 目标值 |
|------|--------|
| 搜索通道故障降级 | 单通道故障不影响其他通道，返回部分结果 |
| 索引一致性 | 修改笔记后索引始终只有 1 份最新版本 |
| Config 故障可见 | 配置失效时日志告警，不静默回退默认值 |

### 兼容性

| 维度 | 要求 |
|------|------|
| LangGraph | v1.0.10+（Context API） |
| LanceDB | v0.4+（merge_insert + FTS） |
| bge-m3 | FlagEmbedding >= 1.2 |
| jieba | >= 0.42 |
| Obsidian | v1.4+（Plugin API + CLI） |

---

## 风险与缓解

| 风险 | 严重度 | 缓解方案 |
|------|--------|---------|
| A1 bge-m3 迁移是咽喉（后续全部依赖） | 高 | 迁移前备份现有索引 + 准备回滚方案 |
| LangGraph Context API 有 5 个已知生产 bug | 高 | 分阶段：Phase 0 先修 L195 让旧 API 工作 → Phase 1 再迁移新 API |
| 中文 metadata prefix 影响 bge-m3 质量 | 中 | 20 个中文查询 A/B 测试验证 |
| RRF k=60 需要域调优 | 中 | k=60 起点 + 真实数据上调优 |
| 全系统 cs188 硬编码清理范围大（20+ 处） | 中 | 逐文件搜索替换 + lint 防回退 |

---

## 验收标准来源

本 PRD 的验收标准来自以下社区/论文验证：

| 标准 | 来源 |
|------|------|
| Precision@5 >= 0.70, MRR >= 0.70, Recall@10 >= 0.80 | Session A 调研确认的 RAG 生产验收标准 |
| Hybrid Search 提升 11-16% | LanceDB 官方 SQuAD benchmark |
| Reranker 提升 MRR >= +0.10 | LanceDB 官方 benchmark + Anthropic 数据（减少 67% 检索失败） |
| CRAG 提升 9.6-20% 准确率 | CRAG 论文 arXiv:2401.15884 |
| bge-m3 中文 MIRACL nDCG@10=63.9 | BAAI 官方 benchmark |
| jieba 中文分词 | LanceDB GitHub #2168/#2329 社区公认 workaround |
| 分层融合优于扁平 +3% F1 | HF-RAG 论文 arXiv:2509.02837 |
| 标题分块 + 512 token | Firecrawl 2026 研究报告（85-90% 召回率） |
| Adaptive-k | EMNLP 2025 Megagon Labs（减少 99% 无用 token） |
