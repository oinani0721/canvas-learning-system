# Canvas Learning System — 实施路线图

> 汇总日期：2026-03-13
> 来源：S1-S7, A2-A5, D, P0, Memory System 2 全部 brainstorming 结论

---

## 一、依赖关系总览

```
┌─────────────────────────────────────────────────────────────────┐
│                        Phase 0: 基础修复                         │
│                                                                 │
│  S1 死代码清理 ──┬──→ S4a Config 修复（Round 1）                  │
│   (~5090行删除)  │                                               │
│                  ├──→ S2 Retriever 修复（Wave 1-2）               │
│                  │                                               │
│                  └──→ S3 Pipeline 重建（Batch 1）                 │
│                       (激活 Reranker + Quality Gate)              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Phase 1: 核心升级                              │
│                                                                 │
│  P0 分块管道升级 ──→ S7/A2 Reranking + CRAG                      │
│  (bge-m3 + 分块重写)  (融合统一 + 质量门控)                        │
│                                                                 │
│  S4 Config 统一 ──→ S2 Retriever（Wave 3-4）                     │
│  (Round 2-3)        (可靠性 + 智能路由)                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Phase 2: 新功能                                │
│                                                                 │
│  A3 检索范围 ─────→ A5 多模态检索                                 │
│  (Scope+Frontmatter    (MinerU + BGE-VL                          │
│   +Wikilinks+Bridge)    + ColQwen2.5)                            │
│                                                                 │
│  Memory System 2 ──→ (依赖完整 RAG 管道)                          │
│  (Context Builder       学习追踪                                  │
│   + Observer)                                                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Phase 3: 前端重构                              │
│                                                                 │
│  D 前端 Canvas 知识图谱 UI                                        │
│  (独立于后端，可部分并行)                                          │
│  + Karpicke 陷阱 5 项缓解措施                                     │
│  + FSRS 对接                                                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 二、分阶段实施计划

### Phase 0: 基础修复（预计 3-5 天）

> **目标：清理技术债、修复断裂管道，让系统从"演示级"变为"可运行"**

| 序号 | 任务 | 来源 | 改动量 | 关键交付 |
|------|------|------|--------|---------|
| 0.1 | **S1 死代码清理** | S1 | 删除 ~5090 行 + 2 测试文件 | 9 个死模块清除、ghost table 修复、rollback 防护 |
| 0.2 | **S4a Config Round 1** | S4 | ~10 行 | 修复 adapter.py config 传递 bug、删除 env_config.py |
| 0.3 | **S3 Batch 1 激活** | S3 | ~50 行 | 激活 reranker (bge-reranker-v2-m3)、质量门控 (CRAG)、查询重写 (LLM) |
| 0.4 | **S2 Wave 1 核心修复** | S2/S6 | ~80 行 | 5 个 retriever 基础修复 (Graphiti SDK、Multimodal接口、Textbook路径、Cross-Canvas TODO、vault_notes去重) |

**验证门控：** 编译通过 → import 通过 → graph 构建 → lint 通过 → pytest 通过

---

### Phase 1: 核心升级（预计 5-8 天）

> **目标：embedding 升级、分块重写、融合统一，让检索质量从"凑合"变为"可用"**

| 序号 | 任务 | 来源 | 改动量 | 关键交付 |
|------|------|------|--------|---------|
| 1.1 | **P0 Sprint 0** | P0 | ~30 行 | 激活已有 reranker + query rewriter（不需索引重建） |
| 1.2 | **P0 Sprint 1** | P0 | ~80 行 | 分块升级 (token-based + 句子边界 + 原子保护) + bge-m3 Dense (1024d) + Contextual Retrieval Phase 1 — **需 1 次索引重建** |
| 1.3 | **P0 Sprint 2** | P0 | ~60 行 | BM25 FTS + jieba 中文分词 + Contextual Retrieval Phase 2 (Gemini Flash) — **需 1 次索引重建** |
| 1.4 | **S7/A2 Batch 1** | S7/A2 | ~200 行 | Reranker 重写 (lazy singleton + fp16) + CRAG 二级路由 + 融合统一 (6源→3组→RRF→rerank) |
| 1.5 | **S4 Config Round 2-3** | S4 | ~100 行 | LangGraph Context API 迁移 + State 字段补全 |
| 1.6 | **S2 Wave 2** | S2 | ~60 行 | Hybrid search 激活 + jieba + content-hash 去重 + fusion bug 修复 |

**验证门控：** 50+ 真实查询 Golden Test Set、MRR ≥ +0.10、reranker 延迟 <500ms

**关键验证修正（A2 Review）：**
- Fusion 保持 inline 代码（不用 fusion/ 模块）
- 三阶段压缩 → 改为 Top-5 截断
- CRAG 阈值统一为 0.5（当前 3 处冲突）

---

### Phase 2: 新功能（预计 8-12 天）

> **目标：新增智能检索功能，让系统从"能搜到"变为"搜得准、搜得智能"**

#### 2A: A3 检索范围增强（4-6 天）

| 序号 | 任务 | 优先级 | 改动量 | 关键交付 |
|------|------|--------|--------|---------|
| 2A.1 | **Frontmatter 解析** | P0 | ~100 行 | YAML 解析 + 剥离 + metadata 存入 LanceDB + prefix embedding |
| 2A.2 | **Scope 范围过滤** | P0 | ~50 行 | course_id/tags WHERE 过滤 + SQL 注入修复 |
| 2A.3 | **Wiki-links 集成** | P1 | ~120 行 | 修复 _extract_heading_section bug + outgoing_links 索引 + 1-hop 邻居扩展 |
| 2A.4 | **渐进范围展开** | P1 | ~80 行 | Canvas→Course→All 三层 + similarity 阈值触发 |
| 2A.5 | **Cross-Canvas 桥接** | P2 | ~150 行 | 注册 API 路由 + 连通 RAG retriever + 修复前端端点 |

#### 2B: A5 多模态检索（6-8 天，可与 2A 部分并行）

| 序号 | 任务 | 阶段 | 关键交付 |
|------|------|------|---------|
| 2B.1 | **修复 5 个断点 + MinerU** | Phase 1 | 向量维度对齐、接口匹配、MinerU 中文解析 (替代 Docling) |
| 2B.2 | **ColQwen2.5 + BGE-VL** | Phase 2 | 多语言视觉检索 + 2-stage retrieval |
| 2B.3 | **Jina Reranker M0** | Phase 3 | 多模态重排优化 |

#### 2C: Memory System 2（3-4 天）

| 序号 | 任务 | 优先级 | 关键交付 |
|------|------|--------|---------|
| 2C.1 | **Context Builder + Observer** | P0 | ~600 行，Agent 闭环：上下文构建 + 学习行为观察 |
| 2C.2 | **Mastery 向量序列化** | P0 | 激活已有代码 |
| 2C.3 | **FSRS + Graphiti + 策略适配** | P1 | 三角协作：时机/弱点/策略 |

---

### Phase 3: 前端重构（预计 10-15 天，可与 Phase 2 部分并行）

> **目标：从插件 UI 升级为 Canvas 知识图谱学习界面**

| 序号 | 任务 | 关键交付 |
|------|------|---------|
| 3.1 | **NodeContextPanel** | 节点级面板：对话历史 + 上下文 + 操作 |
| 3.2 | **NodeInteractionStore** | Svelte Store 状态管理 |
| 3.3 | **NodeRelationshipManager** | 类型化边 (explains/decomposes/questions) |
| 3.4 | **Karpicke 陷阱缓解** | 检索复习队列 + AI 渐隐 + 自我解释优先 |
| 3.5 | **FSRS 前端对接** | 间隔重复调度 UI |

**已有基础设施复用率 ~80%：** CanvasNodeAPI, CanvasEdgeAPI, ContextMenuManager, color system, ApiClient, DAO

---

## 三、跨 Phase 关键任务

| 任务 | 影响范围 | 触发时机 |
|------|---------|---------|
| **bge-m3 Embedding 迁移** | 所有检索功能、需全量索引重建 | Phase 1 Sprint 1 |
| **Golden Test Set 构建** | 所有验收测试 | Phase 1 开始前 |
| **Graphiti 客户端重写** | 知识图谱检索、跨课程桥接 | Phase 0 S2 |
| **LanceDB Schema 演进** | Frontmatter、Wikilinks、多模态 | Phase 1-2 交界 |

---

## 四、已确认的关键决策

| 决策 | 选择 | 否决 | 来源 |
|------|------|------|------|
| Embedding 模型 | bge-m3 (1024d, 中英双语) | OpenAI ada-002, all-MiniLM | S4b |
| Reranker | bge-reranker-v2-m3 (fp16) | Cohere, 无 reranker | S3/S7 |
| LLM | Gemini 2.5 Flash-Lite ($0.10/1M) | GPT-4o, 本地 LLM | S4b |
| 文档解析 | MinerU (中文 SOTA) | Docling (中文 broken) | A5 验证修正 |
| 分块策略 | Token-based + 句子边界 + 原子保护 | 纯字符切分 | P0 |
| Fusion | inline RRF (nodes.py) | fusion/ 模块 (死代码) | A2 Review |
| 压缩策略 | Top-5 截断 | 三阶段压缩 | A2 Review |
| 三层架构 | L1 简单(70%) / L2 中等(25%) / L3 Agent(5%) | 全量 Agent | S4b |
| 跨课程隔离 | 逻辑隔离 (metadata filter) | 物理隔离 (独立表) | A3 验证 |
| 前端框架 | Svelte (1.6KB, 原生 Stores) | React, Vue | D |

---

## 五、风险与待验证项

| 风险 | 严重度 | 缓解方案 | 状态 |
|------|--------|---------|------|
| 中文 metadata prefix 影响 bge-m3 质量 | 高 | 20 个中文查询 A/B 测试 | PENDING |
| 三层渐进范围无论文验证 | 中 | 实测 + 阈值校准 (初始 0.65) | PENDING |
| LanceDB 不支持原生稀疏向量 | 中 | 用 BM25 FTS + jieba 替代 | 已决策 |
| Karpicke 陷阱（前端偏重精细化，忽视检索练习） | 高 | 5 项缓解措施设计 | PENDING |
| 多模态管道 5 个断点 | 高 | Phase 2B.1 修复 | PENDING |
| CRAG 阈值 3 处冲突 | 中 | 统一为 0.5 | PENDING |

---

## 六、验收标准汇总

| 模块 | 验收条数 | 文档位置 |
|------|---------|---------|
| P0 分块管道 | 28 条 (10+11+7) | acceptance-criteria-P0-chunking-pipeline-2026-03-13.md |
| A3 新功能 | 14 条 | acceptance-criteria-S5-A3-new-features-2026-03-14.md |
| A2 Reranking+CRAG | 8 条 | a2-review-verification-report-2026-03-13.md |
| S2 Retriever | 26 条 | brainstorming-session-2026-03-13.md (S6) |
| A5 多模态 | 20 条 | brainstorming-session-A5-multimodal-retrieval-2026-03-12.md |
| Memory System 2 | 4 条 | brainstorming-session-2026-03-11-001.md |
| **合计** | **~100 条** | |
