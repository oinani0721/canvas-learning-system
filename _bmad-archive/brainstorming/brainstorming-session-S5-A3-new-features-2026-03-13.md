---
stepsCompleted: [1, 2, 3, 4]
inputDocuments: []
session_topic: 'S5 A3 新功能实施 — Frontmatter 解析 + Wiki-links 邻居检索 + 渐进 Scope + 跨课程桥接 + Obsidian CLI 融合'
session_goals: '将 A3 brainstorming 的四个方向从"想法"变成"可执行的实施计划"：验证技术可行性、选择具体方案、设计存储 schema、确定实施顺序'
selected_approach: 'Deep Explore + Adversarial Code Review + Community/Paper Validation + Morphological Analysis + Solution Matrix'
techniques_used: ['Constraint Mapping', 'Morphological Analysis', 'Solution Matrix', 'Deep Explore', 'Adversarial Code Review', 'Community Validation', 'Paper Survey']
ideas_generated: ['Metadata-as-text prefix', 'LanceDB List<Utf8> + LABEL_LIST 索引存储 wikilinks', '4阶段 cascade 渐进检索', 'Tag Jaccard 跨课程桥接', 'LanceDB 主力 + CLI 图遍历分层架构', 'Agent CLI 工具扩展(links+tags)']
context_file: ''
related_issues: '#1,#2,#3,#4,#5'
dependencies: 'S5 依赖 S2(Retriever修复) + S3(Pipeline重建) + S4a(Config修复)'
session_active: false
workflow_completed: true
---

# Brainstorming Session Results — S5 A3 新功能实施

**Facilitator:** ROG
**Date:** 2026-03-13
**Session ID:** session-brainstorm-S5-A3-new-features-2026-03-13

---

## Session Overview

**Topic:** 在修复后的管道上实施 A3 四个检索增强功能

**来源:** A3 brainstorming (2026-03-11) 产出了四个方向（Frontmatter/Wiki-links/渐进Scope/跨课程桥接），S5 负责将其转化为可执行的实施计划。

**Goals:**
1. 代码审查验证四个功能的现有代码资产
2. 论文+社区调研验证方案成熟度
3. 选择每个功能的具体实施方案
4. 设计 LanceDB schema 和存储策略
5. 确定实施顺序和依赖关系
6. 验证 Obsidian CLI + RAG 融合的成熟度

**方法论:** 6 轮并行 agent 调研（3 轮代码对抗性审查 + 社区调研 + 论文调研 + 交叉依赖补充调研） + Constraint Mapping + Solution Matrix

---

## 1. 代码对抗性审查总结

> 3 轮独立 agent 审查，覆盖四功能相关代码 + Obsidian CLI 集成代码。

### 四功能现有代码资产盘点

| 功能 | 现有代码状态 | 评级 | 关键文件 |
|------|-------------|------|---------|
| **Frontmatter 解析** | 管道中无解析器。`lancedb_client.py` 索引时跳过 frontmatter。`scripts/lib/planning_utils.py` 有 20 行参考实现。 | 🔴 需构建 | `lancedb_client.py`, `planning_utils.py` |
| **Wiki-links 邻居检索** | `extract_and_resolve_wikilinks()` + `enrich_with_adjacent_nodes()` 完全可用，1-hop/2-hop 已打通，真实 API 调用。 | 🟢 可复用 | `context_enrichment_service.py` |
| **渐进 Scope** | 零实现。`cross_canvas_retriever.py:170-183` 的 `find_related_canvases()` 是纯 TODO stub 返回 `[]`。 | 🔴 需构建 | `cross_canvas_retriever.py` |
| **跨课程桥接** | Subject 隔离基础设施可用（SubjectResolver + subject_config + group_id 过滤）。无跨 subject 桥接逻辑。 | 🟡 隔离可复用，桥接需构建 | `subject_resolver.py`, `subject_config.py` |

### 关键 Stub/Mock 发现

1. `cross_canvas_retriever.py:170-183` — `find_related_canvases()` 纯 TODO 返回 `[]`
2. `subject_config.py:29` — `get_current_subject()` 是 stub 返回 `DEFAULT_SUBJECT`
3. LanceDB 索引流程 — 不解析 frontmatter，tags/course/properties 全部丢失

### Obsidian CLI 集成审查

| 维度 | 现状 |
|------|------|
| CLI 命令使用率 | 3/60+ 命令（search:context, outline, backlinks） |
| 未实现的核心命令 | tags, properties, property:read, links, orphans, deadends, unresolved, aliases |
| LanceDB 索引 | 不解析 frontmatter，元数据全部丢失 |
| metadataCache | 仅用作 change 事件触发器，未读取缓存的 tags/headings/links |
| RAG 融合方式 | LLM（Gemini）自主选择工具，无程序化 RRF 融合 |
| Vault 名 | 硬编码 `CS188`，不可配置 |
| System 1b 实现度 | 约 30%（设计目标：tags+links+properties on-demand 查询） |

---

## 2. 论文调研总结（18 篇）

### 按功能分类的关键论文

#### Metadata-enhanced RAG

| 论文 | 会议 | 核心发现 | 相关性 |
|------|------|---------|--------|
| Utilizing Metadata for Better RAG | ECIR 2026 | Metadata-as-text prefix 在多种指标上一致优于 plain-text baseline | **高** — 直接适用 |
| Metadata-Driven RAG for Financial QA | arXiv 2510 | "Contextual chunks"（嵌入元数据的 chunk）带来的提升超过单纯 reranker | **高** — contextual chunks 可迁移 |
| Query Attribute Modeling (QAM) | SIGIR 2025 | Query 分解为 structured metadata tags + semantic elements 双路径 | **中** — query decomposition 思路可借鉴 |

#### Graph-augmented RAG

| 论文 | 会议 | 核心发现 | 相关性 |
|------|------|---------|--------|
| KG2RAG | NAACL 2025 | seed chunk → KG 图遍历扩展 → KG 组织上下文，HotpotQA 上超越现有 RAG | **高** — 正是我们的 wikilink 场景 |
| Microsoft GraphRAG | arXiv 2024 | Community detection + 预摘要，适合全局问题 | **高** — community summary 思路可参考 |
| GRAG | NAACL 2025 Findings | 双视图 text+graph，线性时间子图检索 | **高** — dual-view 可借鉴 |
| GraphRAG Survey | ACM TOIS 2025 | 1-hop/2-hop 效果对比：1-hop 最佳性价比 | **高** — 确认 1-hop 策略 |

#### Adaptive/Progressive Retrieval

| 论文 | 会议 | 核心发现 | 相关性 |
|------|------|---------|--------|
| Adaptive-RAG | NAACL 2024 | 复杂度分类器 + 三级路由 | **高** — 与 S4b 分诊架构一致 |
| CRAG | arXiv 2024 | 质量门控 correct/ambiguous/incorrect + decompose-then-recompose | **高** — 质量门控核心 |
| Self-RAG | ICLR 2024 Oral | Reflection tokens 按需检索 + 输出质量自检 | **高** — reflection 机制参考 |
| DualRAG | ACL 2025 | RaQ + pKA 渐进知识汇聚 | **高** — progressive aggregation 适合教育场景 |

#### Cross-domain Knowledge Transfer

| 论文 | 会议 | 核心发现 | 相关性 |
|------|------|---------|--------|
| Cross-Data KG for Educational QA (HCMUT) | AIQAM 2024 | 跨数据源 KG 构建 + embedding-based 关系发现 | **高** — 直接对应多课程场景 |
| ACE: AI-Assisted EKG | JEDM 2024 | Prerequisite scoring 减少 70% 专家工作量 | **高** — 先修关系自动检测 |

---

## 3. 社区最佳实践总结

### Frontmatter/Metadata-aware RAG

- **LanceDB pre-filter**：`.where()` SQL 过滤 + 向量搜索组合，原生支持，亚 100ms
- **Metadata-as-text prefix**：将 frontmatter 字段拼到 chunk 前面再 embedding，零成本，ECIR 2026 验证有效
- **python-frontmatter 库**：解析 YAML frontmatter 的成熟工具

### Wiki-links / Graph Retrieval

- **社区共识**：Obsidian wikilinks = 免费知识图谱，不需要 GraphRAG 重量级 LLM 实体提取
- **1-hop 足够**：2-hop 引入过多噪音（社区+论文共识）
- **ObsidianRAG**：开源项目验证 wikilink → graph expansion → reranker 流程

### Progressive Retrieval Scope

- **三层渐进策略**：复杂度分类路由 + 检索质量评估回退 + 迭代增强（最多 2-3 次）
- **轻量实现**：相似度阈值 + 渐进放宽 LanceDB filter + 查询改写

### Cross-course Bridging

- **Pool + metadata filter 模式**：同 table 用 course_id 列过滤，最简单
- **Tag 桥接**：通过共享 tags 实现跨课程发现

### Obsidian CLI + RAG 融合

- **设计模式成熟**："结构化+语义混合检索"在工业界有大量验证（VLDB 2025 综述、RRF SIGIR 2009）
- **Obsidian 生态中是创新**：Smart Connections / Copilot / Khoj 均未实现 metadataCache + vector fusion
- **RRF 是多源融合工业标准**：k=60 默认值，无需调参

---

## 4. 补充调研 — 5 个交叉依赖解决方案

| 问题 | 结论 | 证据 |
|------|------|------|
| **Metadata prefix vs Contextual Retrieval** | 互补不重叠。先做 metadata（零成本），后做 contextual（需 LLM）。前缀控制 30-50 tokens。 | ECIR 2026, Haystack Tutorial #39 |
| **渐进 Scope 工程实现** | 4 阶段 cascade：同笔记+wikilink → 同课程 → 相关课程 → 全库。Score threshold 路由。纯 Python+LanceDB 实现。 | Compass, SIEVE, Haystack ConditionalRouter |
| **跨课程桥接低成本起步** | Tag Jaccard similarity（<50 行代码）。后续可加 bge-m3 tag embedding 同义词匹配。 | TagCDCF 论文, co-occurrence 分析 |
| **Wikilink + LanceDB 存储** | `List<Utf8>` 列 + `LABEL_LIST` 索引，`array_has_any` 查询。不需要图数据库。 | LanceDB 官方文档, ObsidianRAG |
| **bge-m3 metadata prefix 兼容性** | 完全兼容。bge-m3 不需要 instruction prefix（BAAI 官方确认）。8192 token 窗口充裕。 | BAAI/bge-m3 HuggingFace |

---

## 5. 四功能实施方案矩阵

### 功能1：Frontmatter 解析

| 维度 | 方案 |
|------|------|
| **做什么** | 索引时解析 YAML frontmatter → 存为 LanceDB 列 + 拼到 chunk 前面做 embedding |
| **解析工具** | python-frontmatter 库 |
| **存储列** | `course_id` (Utf8, scalar index), `tags` (List<Utf8>, LABEL_LIST index), `difficulty` (Utf8) |
| **前缀格式** | `"Course:{course} Tags:{tags}\n{chunk_content}"` |
| **前缀长度** | 30-50 tokens（bge-m3 完全兼容） |
| **降级策略** | Frontmatter 缺失时从文件路径推断课程名 |
| **后续增强** | Contextual Retrieval（LLM 生成 chunk 语义上下文前缀，与 metadata prefix 互补） |
| **代码现状** | 🔴 需构建（参考 `planning_utils.py` 20 行实现） |

### 功能2：Wiki-links 邻居检索

| 维度 | 方案 |
|------|------|
| **做什么** | 检索到相关笔记后，自动把其链接的邻居笔记的 chunks 也纳入结果 |
| **解析器** | 复用 `extract_and_resolve_wikilinks()`（已完全可用） |
| **存储列** | `outgoing_links` (List<Utf8>, LABEL_LIST index) |
| **扩展策略** | 1-hop 足够（论文+社区共识），2-hop 仅在 L3 Agent 循环按需 |
| **扩展限制** | 最多扩展 top-5 个链接（按与 query 相关度排序） |
| **权重衰减** | 邻居 chunk 权重 = 原始 × 0.7 |
| **Agent 工具** | L3 新增 CLI `links` 命令（出链追踪），`tags`（可选探索） |
| **代码现状** | 🟢 核心可复用，需接入新 LanceDB schema |

### 功能3：渐进 Scope

| 维度 | 方案 |
|------|------|
| **做什么** | 搜索时先在最精确范围找，自动逐步扩大 |
| **4 阶段 cascade** | Stage1: 同笔记+wikilink 邻居 → Stage2: 同课程 → Stage3: 相关课程(tag overlap) → Stage4: 全库 |
| **路由信号** | 结果数量 + 质量分数（top-1 相似度） |
| **初始阈值** | HIGH=0.7, MED=0.5（需真实数据标定） |
| **实现方式** | 纯 Python + LanceDB `.where()` 动态调整，不需额外框架 |
| **代码现状** | 🔴 需从零构建 |

### 功能4：跨课程桥接

| 维度 | 方案 |
|------|------|
| **做什么** | 发现不同课程间的共享概念关联 |
| **起步方案** | Tag Jaccard similarity 计算课程间共享标签（<50 行代码） |
| **输出** | 课程关联表，供渐进 Scope Stage3 使用 |
| **后续增强** | bge-m3 tag embedding 相似度（同义不同词匹配） |
| **代码现状** | 🟡 隔离基础设施可用（SubjectResolver），桥接逻辑需构建 |

---

## 6. Obsidian CLI + RAG 融合架构

### 决策：LanceDB 做主力 + CLI 图遍历补充

| 层级 | 覆盖 | 方式 | 成本 |
|------|------|------|------|
| **Tier 1 (80-90%)** | 课程过滤、标签匹配、属性查询 | LanceDB metadata 列 + pre-filter + hybrid search | $0 |
| **Tier 2 (10-20%)** | 图遍历（backlink 链、出链追踪、多跳查询） | Obsidian CLI backlinks/links 命令 | $0 |
| **融合方式** | 两路结果用 RRF (k=60) 程序化合并 | 替代当前 LLM 自选工具模式 | — |

### Agent CLI 工具扩展

| CLI 命令 | 状态 | 说明 |
|---------|------|------|
| `backlinks` | ✅ 已有 | 保留 |
| `links` | 🔴 需新增 | 出链追踪，图遍历必需 |
| `tags` | 🟡 可选 | 探索性发现 |
| `properties` | ❌ 不需要 | 由 LanceDB metadata 列替代 |
| `search:context` | ✅ 已有 | 保留 |
| `outline` | ✅ 已有 | 保留 |

---

## 7. LanceDB Schema 设计

```python
import pyarrow as pa

schema = pa.schema([
    pa.field("chunk_id", pa.utf8()),
    pa.field("source_path", pa.utf8()),
    pa.field("course_id", pa.utf8()),               # Frontmatter → scalar index
    pa.field("tags", pa.list_(pa.utf8())),            # Frontmatter → LABEL_LIST index
    pa.field("difficulty", pa.utf8()),                # Frontmatter
    pa.field("outgoing_links", pa.list_(pa.utf8())),  # Wikilinks → LABEL_LIST index
    pa.field("text", pa.utf8()),                      # 含 metadata prefix 的 chunk 内容
    pa.field("vector", pa.list_(pa.float32(), 1024)), # bge-m3 dense embedding
    pa.field("date_modified", pa.utf8()),
])
```

---

## 8. Phase 1/2/3 实施路线图

### Phase 1（功能1 + 功能2 并行）

- [ ] 1.1 Frontmatter YAML 解析接入索引流程（python-frontmatter）
- [ ] 1.2 LanceDB 新增 `course_id` / `tags` / `difficulty` 列 + 索引
- [ ] 1.3 Metadata-as-text prefix 拼接到 chunk 再 embedding
- [ ] 1.4 Frontmatter 缺失降级策略
- [ ] 1.5 Vault 重新索引（一次性）
- [ ] 2.1 复用 `extract_and_resolve_wikilinks()` 解析器
- [ ] 2.2 LanceDB 新增 `outgoing_links: List<Utf8>` 列 + LABEL_LIST 索引
- [ ] 2.3 1-hop 邻居扩展（`array_has_any` 查询）
- [ ] 2.4 Agent 新增 `links` CLI 工具
- [ ] 2.5 Agent 新增 `tags` CLI 工具（可选）

### Phase 2（功能3 + 功能4）

- [ ] 4.1 Tag Jaccard similarity 计算课程间共享标签
- [ ] 4.2 生成课程关联表
- [ ] 3.1 4 阶段 cascade 检索逻辑
- [ ] 3.2 Score threshold 路由（初始 HIGH=0.7, MED=0.5）

### Phase 3（增强）

- [ ] 5.1 Contextual Retrieval（Gemini Flash 生成 chunk 上下文前缀）
- [ ] 5.2 CLI vault 名可配置化（去掉硬编码 CS188）
- [ ] 5.3 CLI 降级策略（Obsidian 未运行时 LanceDB 独立工作）
- [ ] 5.4 跨课程桥接升级（bge-m3 tag embedding 同义词匹配）

### 架构层面

- [ ] 6.1 RRF 程序化融合（替代 LLM 自选工具模式）
- [ ] 6.2 与 S3 管道集成（A3 增强检索 → RRF → reranker → CRAG）

---

## 9. 前置依赖

```
S1(死代码清理) → S2(Retriever修复) + S3(Pipeline重建) + S4a(Config修复) → S5(A3新功能)
```

S5 可在 S4a 完成后开工，不需等 S4b（State/Graph 整理）。

---

## 10. Decision-Review 清单（PENDING）

| # | 验证维度 | 验证方式 |
|---|---------|---------|
| 1 | Metadata prefix 对 bge-m3 实际检索质量影响 | 真实 vault 数据 A/B 对比 |
| 2 | LanceDB pre-filter + LABEL_LIST 索引在数百笔记上的性能 | 负载测试 |
| 3 | CLI 图遍历延迟与用户体验 | 端到端延迟测量 |
| 4 | RRF 双路融合 vs LLM 自选的实际效果对比 | 检索质量评估 |
| 5 | 4 阶段渐进 Scope 的 threshold 标定 | 真实查询数据回归 |
| 6 | Tag Jaccard 跨课程桥接的发现质量 | 用户体验验证 |

---

## 关键发现

1. **零新依赖** — 四个功能全部在现有 LanceDB + bge-m3 技术栈上实现
2. **Wiki-links 代码可复用** — 核心解析逻辑已存在，是工作量最小的功能
3. **Obsidian CLI 设计成熟但生态创新** — "结构化+语义融合"是行业标准，但 Obsidian 插件生态无先例
4. **LanceDB 能力被严重低利用** — List 列、LABEL_LIST 索引、SQL WHERE 过滤都是原生支持但未使用
5. **Metadata prefix + Contextual Retrieval 互补** — 分两阶段实施，先零成本后 LLM 增强

---

## 参考论文

1. Utilizing Metadata for Better RAG (ECIR 2026) — arXiv:2601.11863
2. KG2RAG: Knowledge Graph-Guided RAG (NAACL 2025)
3. GRAG: Graph Retrieval-Augmented Generation (NAACL 2025 Findings)
4. GraphRAG Survey (ACM TOIS 2025) — arXiv:2408.08921
5. Microsoft GraphRAG (arXiv 2024) — arXiv:2404.16130
6. Adaptive-RAG (NAACL 2024)
7. CRAG: Corrective RAG (arXiv 2024) — arXiv:2401.15884
8. Self-RAG (ICLR 2024 Oral) — arXiv:2310.11511
9. DualRAG (ACL 2025) — arXiv:2504.18243
10. Cross-Data KG for Educational QA (AIQAM 2024) — arXiv:2404.09296
11. ACE: AI-Assisted EKG Construction (JEDM 2024)
12. TagCDCF: Tags as Bridges between Domains (Springer)
13. Filtered Vector Search Survey (VLDB 2025)
14. ACORN: Predicate-Agnostic Search (SIGMOD 2024)
15. Progressive Searching for RAG (arXiv 2026) — arXiv:2602.07297
16. Metadata-Driven RAG for Financial QA (arXiv 2025) — arXiv:2510.24402
17. HF-RAG: Hierarchical Fusion RAG (arXiv 2025) — arXiv:2509.02837
18. RRF: Reciprocal Rank Fusion (SIGIR 2009)
