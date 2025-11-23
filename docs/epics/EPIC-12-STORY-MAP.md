# Epic 12 Story Map: 3层记忆系统 + Agentic RAG集成

**Epic ID**: EPIC-12
**Story Map版本**: v1.0
**创建日期**: 2025-11-14
**PM Owner**: Sarah
**SM Owner**: Bob
**总Story数**: 16个
**MVP Story数**: 11个 (P0)
**总工期**: 15.5人天 (MVP: 10.5天)

---

## 📋 目录

1. [Story Overview](#1-story-overview)
2. [Story Priority Matrix](#2-story-priority-matrix)
3. [MVP Definition](#3-mvp-definition)
4. [Story Dependency Graph](#4-story-dependency-graph)
5. [Story Point Estimates](#5-story-point-estimates)
6. [Story Details](#6-story-details)
7. [Acceptance Criteria Summary](#7-acceptance-criteria-summary)
8. [Risk-Story Mapping](#8-risk-story-mapping)

---

## 1. Story Overview

### 1.1 Story分组

Epic 12包含**4个Story组**：

| Story组 | Story ID | Story数 | 总工期 | 优先级 | 目标 |
|---------|----------|---------|--------|--------|------|
| **Infrastructure** | 12.1-12.4 | 4 | 5.5天 | P0 | 3层记忆系统基础设施搭建 |
| **Agentic RAG Core** | 12.5-12.9 | 5 | 9天 | P0 | 智能检索编排核心实现 |
| **Integration & Testing** | 12.10-12.16 | 7 | 5天 | P0/P1 | Canvas集成 + 测试验收 |
| **Enhancement** | 12.17 | 1 | 2天 | P2 | 多模态支持 (Optional) |

### 1.2 全部Story列表

| Story ID | Story名称 | 优先级 | 工期 | 依赖 | 状态 |
|----------|----------|--------|------|------|------|
| **12.1** | Graphiti时序知识图谱集成 | P0 | 2天 | - | 🔴 待开发 |
| **12.2** | LanceDB POC验证 | P0 | 1天 | - | 🔴 待开发 |
| **12.3** | ChromaDB → LanceDB数据迁移 | P0 | 1.5天 | 12.2 | 🔴 待开发 |
| **12.4** | Temporal Memory实现 | P0 | 1天 | - | 🔴 待开发 |
| **12.5** | LangGraph StateGraph构建 | P0 | 2天 | 12.1 | 🔴 待开发 |
| **12.6** | 并行检索实现 (Send模式) | P0 | 1.5天 | 12.5 | 🔴 待开发 |
| **12.7** | 3种融合算法实现 | P0 | 2天 | 12.6 | 🔴 待开发 |
| **12.8** | 混合Reranking策略 | P0 | 2天 | 12.6 | 🔴 待开发 |
| **12.9** | 质量控制循环 | P0 | 1.5天 | 12.7, 12.8 | 🔴 待开发 |
| **12.10** | Canvas检验白板生成集成 | P0 | 1天 | 12.9 | 🔴 待开发 |
| **12.11** | graphiti-memory-agent调用接口 | P1 | 0.5天 | 12.1 | 🔴 待开发 |
| **12.12** | LangSmith可观测性集成 | P1 | 1天 | 12.5 | 🔴 待开发 |
| **12.13** | 回归测试 | P1 | 0.5天 | 12.10 | 🔴 待开发 |
| **12.14** | 性能基准测试 | P1 | 1天 | 12.10 | 🔴 待开发 |
| **12.15** | E2E集成测试 | P0 | 1天 | 12.10 | 🔴 待开发 |
| **12.16** | 文档和部署 | P0 | 0.5天 | 12.15 | 🔴 待开发 |
| **12.17** | 多模态支持 (ImageBind集成) | P2 | 2天 | 12.3 | 🔴 待开发 |

**总计**: 16个Story, 19.5人天 (MVP: 11个Story, 10.5人天)

---

## 2. Story Priority Matrix

### 2.1 优先级定义

| 优先级 | 定义 | Story数 | 工期 | 里程碑 |
|--------|------|---------|------|--------|
| **P0** (Must-Have) | MVP核心功能，阻塞上线 | 11 | 10.5天 | M4: Production Ready |
| **P1** (Should-Have) | 增强功能，提升质量 | 4 | 3天 | - |
| **P2** (Nice-to-Have) | 可选功能，未来迭代 | 1 | 2天 | - |

### 2.2 P0 (MVP) Stories

**11个P0 Story** (按时间顺序):

```
Week 1: Infrastructure (4个Story, 5.5天)
├─ 12.1: Graphiti集成 (2天)
├─ 12.2: LanceDB POC (1天)
├─ 12.3: LanceDB迁移 (1.5天)
└─ 12.4: Temporal Memory (1天)

Week 2: Agentic RAG Core (5个Story, 7天)
├─ 12.5: StateGraph构建 (2天)
├─ 12.6: 并行检索 (1.5天)
├─ 12.7: 融合算法 (2天)
├─ 12.8: Reranking (2天)  [可与12.7部分并行]
└─ 12.9: 质量控制循环 (1.5天)

Week 3: Integration (2个Story, 1.5天)
├─ 12.10: Canvas集成 (1天)
└─ 12.15: E2E测试 (1天)  [部分并行]
└─ 12.16: 文档部署 (0.5天)
```

**关键路径** (Critical Path, 串行依赖):
```
12.1 (2d) → 12.5 (2d) → 12.6 (1.5d) → 12.7 (2d) → 12.10 (1d) → 12.15 (1d) → 12.16 (0.5d)
= 10天
```

**并行优化空间**:
- 12.2-12.4可并行 (节省1天)
- 12.8可与12.7部分并行 (节省0.5天)
- 12.11-12.12可并行 (P1 stories)

**实际最短工期**: 10.5天 (含buffer)

### 2.3 P1 Stories (Enhancement)

**4个P1 Story** (可并行开发):

| Story ID | Story名称 | 工期 | 依赖 | 可并行性 |
|----------|----------|------|------|----------|
| 12.11 | graphiti-memory-agent接口 | 0.5天 | 12.1 | 可与12.5-12.9并行 |
| 12.12 | LangSmith可观测性 | 1天 | 12.5 | 可与12.6-12.9并行 |
| 12.13 | 回归测试 | 0.5天 | 12.10 | 可与12.15并行 |
| 12.14 | 性能基准测试 | 1天 | 12.10 | 可与12.15并行 |

**说明**: P1 stories不在关键路径上，可作为buffer或并行开发

### 2.4 P2 Stories (Optional)

**1个P2 Story**:

- **12.17: 多模态支持 (ImageBind)** - 2天
  - 依赖: 12.3 (LanceDB迁移完成)
  - 风险: 高（ImageBind模型依赖，CUDA环境）
  - 决策: Epic 12不包含，推迟到Phase 5独立Epic

---

## 3. MVP Definition

### 3.1 MVP范围

**MVP = P0 Stories (11个, 10.5天)**

**MVP目标**: 实现完整的3层记忆系统 + Agentic RAG核心能力，达到Epic-level AC标准

**MVP包含**:
- ✅ Graphiti时序知识图谱 (Layer 1)
- ✅ LanceDB向量数据库 (Layer 2, 文本模态only)
- ✅ Temporal Memory (Layer 3, FSRS + 学习行为)
- ✅ LangGraph StateGraph编排
- ✅ 并行检索 (Send模式)
- ✅ 3种融合算法 (RRF/Weighted/Cascade)
- ✅ 混合Reranking (Local + Cohere自动选择)
- ✅ 质量控制循环 (Query重写)
- ✅ Canvas检验白板生成集成
- ✅ E2E测试通过
- ✅ 基础文档 (ADRs + API docs + 用户指南)

**MVP不包含**:
- ❌ 多模态支持 (ImageBind) → 推迟Phase 5
- ❌ LangSmith深度集成 → P1, 可后补
- ❌ 完整回归测试套件 → P1, 可后补
- ❌ 性能基准自动化 → P1, 可后补
- ❌ graphiti-memory-agent完整封装 → P1, 可后补

### 3.2 MVP验收标准 (Must Pass)

**质量指标** (直接影响用户体验):
- ✅ **检验白板生成准确率 ≥ 85%** (当前60%, +25%)
- ✅ **MRR@10 ≥ 0.380** (当前0.280, +36%)
- ✅ **薄弱点聚类F1 ≥ 0.77** (当前0.55, +40%)

**性能指标**:
- ✅ **P95检索延迟 < 400ms** (不含LLM)
- ✅ **向量扩展支持 ≥ 1M** (当前100K)

**功能完整性**:
- ✅ **E2E场景1通过**: 检验白板生成 (端到端无报错)
- ✅ **E2E场景2通过**: 艾宾浩斯复习调度 (触发点4)
- ✅ **Epic 1-10回归测试**: 360+测试不退化

**成本控制**:
- ✅ **年度运营成本 ≤ $60** (目标$49)

**文档完整性**:
- ✅ **ADRs完成**: ADR-002, ADR-003, ADR-004
- ✅ **API文档**: 所有public接口有docstring
- ✅ **用户指南**: 配置 + 使用 + troubleshooting

### 3.3 MVP vs Full Epic对比

| 维度 | MVP (P0) | Full Epic (P0+P1+P2) | 差异 |
|------|----------|---------------------|------|
| **Story数** | 11 | 16 | +5 |
| **工期** | 10.5天 | 15.5天 | +5天 |
| **质量目标** | 达标 (85%, MRR 0.38) | 达标 + 可观测性 + 自动化 | 监控增强 |
| **功能覆盖** | 文本检索 + Canvas集成 | + 多模态 + Agent封装 | 多模态支持 |
| **测试覆盖** | E2E + 核心回归 | + 完整回归 + 性能基准 | 测试全面性 |
| **上线风险** | 低 (核心功能完整) | 极低 (全面保障) | 风险降低 |

**推荐策略**: **先上线MVP (10.5天), 后续迭代P1 (3天), P2独立Epic**

---

## 4. Story Dependency Graph

### 4.1 完整依赖图 (Visual)

```
┌────────────────────────────────────────────────────────────────────┐
│                         Week 1: Infrastructure                     │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌──────────────┐                                                 │
│  │  12.1        │                                                 │
│  │  Graphiti    │─────────┐                                       │
│  │  集成 (2d)   │         │                                       │
│  └──────────────┘         │                                       │
│        │                  │                                       │
│        │ (并行)           │                                       │
│  ┌──────────────┐         │        ┌──────────────┐              │
│  │  12.2        │         │        │  12.4        │              │
│  │  LanceDB POC │────┐    │        │  Temporal    │              │
│  │  (1d)        │    │    │        │  Memory (1d) │              │
│  └──────────────┘    │    │        └──────────────┘              │
│                      │    │                                       │
│                      ▼    │                                       │
│  ┌──────────────┐         │                                       │
│  │  12.3        │         │                                       │
│  │  LanceDB     │         │                                       │
│  │  迁移 (1.5d) │         │                                       │
│  └──────────────┘         │                                       │
│                            │                                       │
└────────────────────────────┼───────────────────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────────────────┐
│                      Week 2: Agentic RAG Core                      │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌──────────────┐                                                 │
│  │  12.5        │                                                 │
│  │  StateGraph  │───────┐                                         │
│  │  构建 (2d)   │       │                                         │
│  └──────────────┘       │                                         │
│        │                │ (可并行)                                │
│        │                │  ┌──────────────┐                       │
│        │                └─▶│  12.11 (P1)  │                       │
│        │                   │  Agent接口   │                       │
│        │                   │  (0.5d)      │                       │
│        │                   └──────────────┘                       │
│        │                                                           │
│        │                   ┌──────────────┐                       │
│        └──────────────────▶│  12.12 (P1)  │                       │
│                            │  LangSmith   │                       │
│                            │  (1d)        │                       │
│                            └──────────────┘                       │
│        ▼                                                           │
│  ┌──────────────┐                                                 │
│  │  12.6        │                                                 │
│  │  并行检索    │───────┬────────────────────┐                    │
│  │  (1.5d)      │       │                    │                    │
│  └──────────────┘       │                    │                    │
│                         ▼                    ▼                    │
│  ┌──────────────┐  ┌──────────────┐    ┌──────────────┐          │
│  │  12.7        │  │  12.8        │    │  12.9        │          │
│  │  融合算法    │  │  Reranking   │───▶│  质量控制    │          │
│  │  (2d)        │  │  (2d)        │    │  循环 (1.5d) │          │
│  └──────────────┘  └──────────────┘    └──────────────┘          │
│        │                                       │                  │
│        └───────────────┬───────────────────────┘                  │
│                        │                                          │
└────────────────────────┼──────────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────────────┐
│                 Week 3: Integration & Testing                      │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌──────────────┐                                                 │
│  │  12.10       │                                                 │
│  │  Canvas集成  │───────┬──────────────────┬────────────┐         │
│  │  (1d)        │       │                  │            │         │
│  └──────────────┘       │                  │            │         │
│                         │                  │            │         │
│                         ▼                  ▼            ▼         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │  12.13 (P1)  │  │  12.14 (P1)  │  │  12.15       │            │
│  │  回归测试    │  │  性能基准    │  │  E2E测试     │            │
│  │  (0.5d)      │  │  (1d)        │  │  (1d)        │            │
│  └──────────────┘  └──────────────┘  └──────┬───────┘            │
│                                              │                    │
│                                              ▼                    │
│                                       ┌──────────────┐            │
│                                       │  12.16       │            │
│                                       │  文档部署    │            │
│                                       │  (0.5d)      │            │
│                                       └──────────────┘            │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
                         │ (Optional)
                         ▼
                  ┌──────────────┐
                  │  12.17 (P2)  │
                  │  多模态      │
                  │  (2d)        │
                  └──────────────┘
```

### 4.2 依赖关系表

| Story | 直接依赖 (Depends On) | 被依赖 (Blocks) | 并行可能性 |
|-------|----------------------|----------------|-----------|
| **12.1** | - | 12.5, 12.11 | 可与12.2-12.4并行 |
| **12.2** | - | 12.3 | 可与12.1, 12.4并行 |
| **12.3** | 12.2 | 12.17 | - |
| **12.4** | - | - | 可与12.1-12.3并行 |
| **12.5** | 12.1 | 12.6, 12.11, 12.12 | - |
| **12.6** | 12.5 | 12.7, 12.8 | - |
| **12.7** | 12.6 | 12.9 | 可与12.8部分并行 |
| **12.8** | 12.6 | 12.9 | 可与12.7部分并行 |
| **12.9** | 12.7, 12.8 | 12.10 | - |
| **12.10** | 12.9 | 12.13, 12.14, 12.15 | - |
| **12.11** | 12.1 | - | 可与12.5-12.9并行 |
| **12.12** | 12.5 | - | 可与12.6-12.9并行 |
| **12.13** | 12.10 | - | 可与12.14-12.15并行 |
| **12.14** | 12.10 | - | 可与12.13, 12.15并行 |
| **12.15** | 12.10 | 12.16 | 可与12.13-12.14并行 |
| **12.16** | 12.15 | - | - |
| **12.17** | 12.3 | - | 独立Epic, 不阻塞MVP |

### 4.3 关键路径 (Critical Path)

**定义**: 串行依赖链，决定最短工期

```
Critical Path (10天):
12.1 (2d) → 12.5 (2d) → 12.6 (1.5d) → 12.7 (2d) → 12.10 (1d) → 12.15 (1d) → 12.16 (0.5d)

说明:
- 12.1是关键起点 (Graphiti是StateGraph的基础)
- 12.9不在关键路径 (12.7完成后可直接12.10, 质量控制可后补)
- 12.8可与12.7并行 (Reranking独立于Fusion)
```

**优化策略**:
- **并行开发**: 12.2-12.4与12.1并行 (节省1天)
- **部分并行**: 12.8与12.7后0.5天并行 (节省0.5天)
- **实际最短**: 10 - 1 - 0.5 = 8.5天 (理论值)
- **MVP保守估算**: 10.5天 (含20% buffer)

---

## 5. Story Point Estimates

### 5.1 Story Points定义

**1 Story Point = 1人天**

**复杂度因子**:
- **Low** (0.5-1天): 简单配置、文档、测试脚本
- **Medium** (1-2天): 标准功能开发、集成
- **High** (2-3天): 复杂算法、多组件集成

### 5.2 Story Point明细表

| Story ID | Story名称 | 复杂度 | Story Points | 工期 (天) | 理由 |
|----------|----------|--------|--------------|----------|------|
| **12.1** | Graphiti集成 | High | 2 | 2 | Neo4j部署 + Graphiti配置 + 测试 |
| **12.2** | LanceDB POC | Medium | 1 | 1 | 性能测试 + 多模态验证 |
| **12.3** | LanceDB迁移 | Medium | 1.5 | 1.5 | 数据导出 + 导入 + 一致性校验 + 双写 |
| **12.4** | Temporal Memory | Medium | 1 | 1 | FSRS集成 + SQLite schema + API |
| **12.5** | StateGraph构建 | High | 2 | 2 | StateGraph定义 + 5个节点实现 |
| **12.6** | 并行检索 | Medium | 1.5 | 1.5 | Send模式 + RetryPolicy + 3层并行 |
| **12.7** | 融合算法 | High | 2 | 2 | RRF/Weighted/Cascade 3种算法 + 自适应选择 |
| **12.8** | Reranking | High | 2 | 2 | Local Cross-Encoder + Cohere API + 自动切换 |
| **12.9** | 质量控制循环 | Medium | 1.5 | 1.5 | Quality checker + Query rewriter + 循环逻辑 |
| **12.10** | Canvas集成 | Medium | 1 | 1 | Adapter + Epic 4集成 + 测试 |
| **12.11** | Agent接口 | Low | 0.5 | 0.5 | Wrapper封装 |
| **12.12** | LangSmith | Medium | 1 | 1 | Trace + 成本监控 + 仪表盘 |
| **12.13** | 回归测试 | Low | 0.5 | 0.5 | 运行Epic 1-10测试套件 |
| **12.14** | 性能基准 | Medium | 1 | 1 | MRR/Recall/F1自动化测试 |
| **12.15** | E2E测试 | Medium | 1 | 1 | 2个场景端到端测试 |
| **12.16** | 文档部署 | Low | 0.5 | 0.5 | 用户指南 + 运维手册 |
| **12.17** | 多模态 | High | 2 | 2 | ImageBind集成 + 跨模态检索 |
| **总计** | - | - | **19.5** | **19.5天** | - |
| **MVP (P0)** | - | - | **10.5** | **10.5天** | - |

### 5.3 Story Point分布

**按复杂度分布**:
- **Low** (0.5-1天): 3个Story (12.11, 12.13, 12.16) = 1.5天
- **Medium** (1-2天): 9个Story (12.2-12.4, 12.6, 12.9-12.10, 12.12, 12.14-12.15) = 11天
- **High** (2天): 4个Story (12.1, 12.5, 12.7-12.8, 12.17) = 8天

**按优先级分布**:
- **P0**: 11个Story = 10.5天
- **P1**: 4个Story = 3天
- **P2**: 1个Story = 2天

### 5.4 Velocity估算

**假设**: 1个全职开发者 (Dev Agent: James)

**理论Velocity**:
- **理想情况** (无并行): 19.5天
- **并行优化后**: 15.5天 (节省4天)
- **MVP最短**: 10.5天 (关键路径 + buffer)

**实际Velocity考虑**:
- **开发效率**: 80% (1天实际产出0.8天工作量)
- **调试时间**: 每个Story +10% buffer
- **集成问题**: 高风险Story (12.1, 12.5, 12.7) +20% buffer

**保守估算**:
- **MVP**: 10.5天 × 1.2 = **12.6天** (约2.5周)
- **Full Epic**: 15.5天 × 1.2 = **18.6天** (约4周)

---

## 6. Story Details

### 6.1 Infrastructure Stories (12.1-12.4)

---

#### **Story 12.1: Graphiti时序知识图谱集成**

**优先级**: P0
**Story Points**: 2
**工期**: 2天
**依赖**: 无
**Assignee**: Dev Agent (James)

**User Story**:
> As a **Canvas学习系统开发者**, I want to **集成Graphiti时序知识图谱**, so that **系统能追踪概念关系和学习历史，支持跨会话的知识网络检索**。

**Acceptance Criteria**:
1. ✅ **AC 1.1**: Neo4j Community Edition 5.0+成功安装并运行
   - Docker Compose一键部署或Windows本地安装
   - Neo4j Browser可访问 (http://localhost:7474)
   - 默认数据库`neo4j`创建成功

2. ✅ **AC 1.2**: Graphiti Python客户端连接成功
   - `graphiti` Python库安装 (pip install graphiti-core)
   - GraphitiClient初始化成功，连接到Neo4j
   - 健康检查通过 (`client.health_check()`)

3. ✅ **AC 1.3**: `add_episode()`正确提取概念和关系
   - 输入: 学习会话文本 (例如: "用户学习了逆否命题的定义和证明方法")
   - 输出: Entity节点 (逆否命题, 证明方法) + Relationship (逆否命题 USED_IN 证明方法)
   - 时序边: valid_at timestamp正确记录

4. ✅ **AC 1.4**: `hybrid_search()`返回Graph + Semantic + BM25结果
   - 输入query: "逆否命题的应用场景"
   - 返回: List[SearchResult]，包含至少5个结果
   - 结果包含: Graph匹配 + 语义相似 + 关键词匹配
   - 验证: 人工检查Top-5相关性 ≥ 80%

5. ✅ **AC 1.5**: 数据持久化和查询性能
   - 100个Episode添加成功，无数据丢失
   - `hybrid_search()`延迟 < 100ms (100个概念，P95)
   - Neo4j数据库大小 < 50MB (100个概念场景)

**Technical Details**:
```python
# ✅ Verified from Graphiti Skill (add_episode + hybrid_search API)

from graphiti_core import GraphitiClient
from graphiti_core.neo4j_config import Neo4jConfig

# 1. Neo4j配置
neo4j_config = Neo4jConfig(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="your-password",
    database="neo4j"
)

# 2. Graphiti Client初始化
client = GraphitiClient(neo4j_config)

# 3. 添加学习会话
await client.add_episode(
    content="用户在离散数学Canvas中学习了逆否命题的定义: 如果原命题是'如果p则q'，逆否命题是'如果非q则非p'。逆否命题与原命题等价。",
    source_description="离散数学.canvas - 逆否命题章节",
    group_id="canvas-discrete-math"
)

# 4. 混合搜索
results = await client.hybrid_search(
    query="逆否命题的应用场景",
    num_results=10,
    group_ids=["canvas-discrete-math"]
)

# 返回示例:
# [
#   SearchResult(
#       content="逆否命题常用于数学证明，特别是反证法",
#       score=0.92,
#       metadata={"type": "fact", "source": "离散数学.canvas"}
#   ),
#   ...
# ]
```

**Dependencies**:
- Neo4j Community Edition 5.0+
- Python graphiti-core库
- Docker (optional, for containerized deployment)

**Risks**:
- **R2**: Neo4j性能瓶颈 (详见Epic PRD Section 8.1)
  - **缓解**: 预先性能测试，索引优化

**DoD (Definition of Done)**:
- [ ] Neo4j运行，可通过Browser访问
- [ ] Graphiti client连接成功，health check通过
- [ ] AC 1.3-1.5全部通过
- [ ] 单元测试: `test_graphiti_integration.py` (10个测试)
- [ ] 文档: `docs/architecture/GRAPHITI-SETUP-GUIDE.md`

---

#### **Story 12.2: LanceDB POC验证**

**优先级**: P0
**Story Points**: 1
**工期**: 1天
**依赖**: 无
**Assignee**: Dev Agent (James)

**User Story**:
> As a **Canvas学习系统架构师**, I want to **验证LanceDB性能和多模态能力**, so that **确认LanceDB是ChromaDB的可行替代方案**。

**Acceptance Criteria**:
1. ✅ **AC 2.1**: 10K向量检索延迟 < 20ms (P95)
   - 创建10K条文档向量 (OpenAI text-embedding-3-small, 1536维)
   - 执行100次随机查询，计算P95延迟
   - 验证: P95 < 20ms

2. ✅ **AC 2.2**: 100K向量检索延迟 < 50ms (P95)
   - 创建100K条文档向量
   - 执行100次随机查询，计算P95延迟
   - 验证: P95 < 50ms

3. ✅ **AC 2.3**: OpenAI embedding集成成功
   - 使用LanceDB内置`openai` embedding function
   - 自动调用OpenAI API生成向量
   - 验证: 100条文档embedding成功, 无API错误

4. ✅ **AC 2.4**: 多模态能力验证 (ImageBind, Optional)
   - 安装ImageBind embedding (如果CUDA可用)
   - 测试文本 + 图像统一向量空间
   - 验证: 文本查询 → 检索图像文档 (跨模态检索成功)

5. ✅ **AC 2.5**: 性能对比报告
   - 对比LanceDB vs ChromaDB (10K, 100K, 1M向量)
   - 指标: P50/P95延迟, 内存占用, 磁盘占用
   - 输出: `docs/architecture/LANCEDB-POC-REPORT.md`

**Technical Details**:
```python
# ✅ Verified from LanceDB Documentation

import lancedb
from lancedb.embeddings import get_registry
import time
import numpy as np

# 1. 创建LanceDB连接
db = lancedb.connect("~/.lancedb")

# 2. 配置OpenAI embedding
registry = get_registry()
openai_emb = registry.get("openai").create(
    name="text-embedding-3-small",
    api_key=os.getenv("OPENAI_API_KEY")
)

# 3. 创建表 (10K文档)
data = [
    {"doc_id": f"doc_{i}", "content": f"Sample document {i}"}
    for i in range(10000)
]

table = db.create_table(
    "poc_test",
    data=data,
    embedding=openai_emb,
    mode="overwrite"
)

# 4. 性能测试
latencies = []
for i in range(100):
    start = time.perf_counter()
    results = table.search("sample query").limit(10).to_pandas()
    end = time.perf_counter()
    latencies.append((end - start) * 1000)  # ms

p95_latency = np.percentile(latencies, 95)
print(f"P95 Latency: {p95_latency:.2f} ms")
assert p95_latency < 20, "P95延迟超过20ms"

# 5. 多模态测试 (Optional)
if torch.cuda.is_available():
    imagebind = registry.get("imagebind").create()
    multimodal_table = db.create_table(
        "multimodal_test",
        data=[
            {"text": "A cat sitting on a table", "type": "text"},
            {"image": "cat.jpg", "type": "image"}
        ],
        embedding=imagebind
    )
    results = multimodal_table.search("cat").limit(5).to_pandas()
    assert len(results) > 0, "跨模态检索失败"
```

**Dependencies**:
- LanceDB Python库
- OpenAI API (text-embedding-3-small)
- CUDA (optional, for ImageBind)

**Risks**:
- **R1**: LanceDB性能不达标
  - **缓解**: 如P95 > 50ms (100K), 考虑保留ChromaDB

**DoD**:
- [ ] AC 2.1-2.3全部通过
- [ ] 性能对比报告完成 (`LANCEDB-POC-REPORT.md`)
- [ ] 测试脚本: `tests/test_lancedb_poc.py`

---

#### **Story 12.3: ChromaDB → LanceDB数据迁移**

**优先级**: P0
**Story Points**: 1.5
**工期**: 1.5天
**依赖**: Story 12.2 (LanceDB POC通过)
**Assignee**: Dev Agent (James)

**User Story**:
> As a **Canvas学习系统运维人员**, I want to **零数据丢失地迁移ChromaDB数据到LanceDB**, so that **保留所有历史解释文档向量，用户无感知切换**。

**Acceptance Criteria**:
1. ✅ **AC 3.1**: ChromaDB数据完整导出
   - 导出所有collection: `canvas_explanations`, `canvas_concepts`
   - 导出格式: JSON Lines (每行一个文档 + metadata + embedding)
   - 验证: 记录数与ChromaDB一致 (例如: 5000条文档)

2. ✅ **AC 3.2**: LanceDB数据完整导入
   - 导入JSON Lines到LanceDB table
   - Schema映射: ChromaDB metadata → LanceDB columns
   - 验证: 记录数100%对齐 (5000条)

3. ✅ **AC 3.3**: 数据一致性校验
   - 随机抽样100条文档，对比ChromaDB vs LanceDB
   - 验证: doc_id, content, metadata完全一致
   - 向量相似度 > 0.99 (余弦相似度)

4. ✅ **AC 3.4**: 双写模式运行1周
   - DualWriteAdapter: 同时写入ChromaDB + LanceDB
   - 验证: 新增文档在两个数据库都存在
   - 监控: 无写入失败错误

5. ✅ **AC 3.5**: Rollback plan验证
   - 备份ChromaDB数据 (tar.gz格式)
   - 模拟迁移失败，执行rollback
   - 验证: ChromaDB恢复到迁移前状态，无数据丢失

**Technical Details**:
```python
# 迁移脚本示例

import chromadb
import lancedb
import json

# 1. 导出ChromaDB
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_collection("canvas_explanations")

# 获取所有数据
results = collection.get(include=["documents", "metadatas", "embeddings"])

# 导出为JSON Lines
with open("chromadb_export.jsonl", "w") as f:
    for i in range(len(results["ids"])):
        doc = {
            "doc_id": results["ids"][i],
            "content": results["documents"][i],
            "metadata": results["metadatas"][i],
            "embedding": results["embeddings"][i]
        }
        f.write(json.dumps(doc) + "\n")

# 2. 导入到LanceDB
db = lancedb.connect("~/.lancedb")

# 读取JSON Lines
data = []
with open("chromadb_export.jsonl") as f:
    for line in f:
        data.append(json.loads(line))

# 创建表
table = db.create_table(
    "canvas_explanations",
    data=data,
    mode="overwrite"
)

# 3. 一致性校验
sample_ids = random.sample(results["ids"], 100)
for doc_id in sample_ids:
    # ChromaDB查询
    chroma_result = collection.get(ids=[doc_id])

    # LanceDB查询
    lance_result = table.search("").where(f"doc_id = '{doc_id}'").limit(1).to_pandas()

    # 对比
    assert chroma_result["documents"][0] == lance_result["content"].iloc[0]
    assert chroma_result["metadatas"][0] == lance_result["metadata"].iloc[0]

    # 向量相似度
    chroma_vec = np.array(chroma_result["embeddings"][0])
    lance_vec = np.array(lance_result["vector"].iloc[0])
    cosine_sim = np.dot(chroma_vec, lance_vec) / (np.linalg.norm(chroma_vec) * np.linalg.norm(lance_vec))
    assert cosine_sim > 0.99, f"向量相似度不足: {cosine_sim}"

print("✅ 数据一致性校验通过!")
```

**Dependencies**:
- ChromaDB (现有数据库)
- LanceDB (Story 12.2完成)
- 迁移脚本

**Risks**:
- **R1**: 数据丢失
  - **缓解**: 完整备份 + 一致性校验 + 双写模式

**DoD**:
- [ ] AC 3.1-3.5全部通过
- [ ] 迁移脚本: `scripts/migrate_chromadb_to_lancedb.py`
- [ ] 备份文件: `chromadb_backup_20251114.tar.gz`
- [ ] 文档: `docs/operations/LANCEDB-MIGRATION-GUIDE.md`

---

#### **Story 12.4: Temporal Memory实现**

**优先级**: P0
**Story Points**: 1
**工期**: 1天
**依赖**: 无
**Assignee**: Dev Agent (James)

**User Story**:
> As a **Canvas学习系统**, I want to **追踪学习行为时序和FSRS遗忘曲线**, so that **支持艾宾浩斯复习系统的薄弱点智能推荐**。

**Acceptance Criteria**:
1. ✅ **AC 4.1**: FSRS库集成成功
   - 安装`py-fsrs`库 (pip install fsrs)
   - FSRS卡片创建: `Card()`对象
   - FSRS算法调用: `FSRS().repeat(card, rating)`

2. ✅ **AC 4.2**: 学习行为时序追踪
   - SQLite数据库: `learning_behavior.db`
   - Schema: session_id, canvas_file, concept, action_type, timestamp, metadata
   - API: `record_behavior(canvas_file, concept, action_type, metadata)`

3. ✅ **AC 4.3**: `get_weak_concepts()`返回低稳定性概念
   - 输入: canvas_file="离散数学.canvas", limit=10
   - 输出: List[概念名称]，按FSRS stability升序排列
   - 权重: 70%低稳定性 + 30%高错误率

4. ✅ **AC 4.4**: `update_behavior()`更新FSRS卡片
   - 输入: concept, rating (1-4分)
   - 更新: Card.difficulty, Card.stability, Card.due
   - 验证: due日期正确计算 (基于FSRS-4.5算法)

5. ✅ **AC 4.5**: 性能和数据持久化
   - 1000个概念FSRS卡片存储成功
   - `get_weak_concepts()`延迟 < 50ms
   - 数据库大小 < 10MB (1000概念场景)

**Technical Details**:
```python
# ✅ Verified from FSRS Algorithm Documentation

from fsrs import FSRS, Card, Rating
from datetime import datetime, timedelta
import sqlite3

# 1. FSRS卡片管理
class TemporalMemory:
    def __init__(self, db_path="learning_behavior.db"):
        self.conn = sqlite3.connect(db_path)
        self.fsrs = FSRS()
        self._init_schema()

    def _init_schema(self):
        # FSRS卡片表
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS fsrs_cards (
                concept TEXT PRIMARY KEY,
                canvas_file TEXT,
                difficulty REAL,
                stability REAL,
                due TIMESTAMP,
                state TEXT,
                last_review TIMESTAMP,
                reps INTEGER
            )
        """)

        # 学习行为表
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS learning_behavior (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                canvas_file TEXT,
                concept TEXT,
                action_type TEXT,  -- decomposition, explanation, scoring, review
                timestamp TIMESTAMP,
                metadata TEXT  -- JSON
            )
        """)
        self.conn.commit()

    def get_weak_concepts(self, canvas_file: str, limit: int = 10) -> List[str]:
        """
        查询薄弱概念

        权重:
        - 70%: 低稳定性 (stability < 7天 或 difficulty > 7)
        - 30%: 高错误率 (最近评分<60分的概念)
        """
        # 1. 低稳定性概念 (70%权重)
        weak_stability = self.conn.execute("""
            SELECT concept, stability, difficulty
            FROM fsrs_cards
            WHERE canvas_file = ? AND (stability < 7 OR difficulty > 7)
            ORDER BY stability ASC
            LIMIT ?
        """, (canvas_file, int(limit * 0.7))).fetchall()

        # 2. 高错误率概念 (30%权重)
        high_error = self.conn.execute("""
            SELECT concept, COUNT(*) as error_count
            FROM learning_behavior
            WHERE canvas_file = ? AND action_type = 'scoring'
              AND json_extract(metadata, '$.score') < 60
            GROUP BY concept
            ORDER BY error_count DESC
            LIMIT ?
        """, (canvas_file, int(limit * 0.3))).fetchall()

        # 3. 组合并去重
        weak_concepts = [c[0] for c in weak_stability] + [c[0] for c in high_error]
        return list(dict.fromkeys(weak_concepts))[:limit]  # 去重保序

    def update_behavior(self, concept: str, rating: Rating, canvas_file: str):
        """
        更新FSRS卡片

        rating: 1 (Again), 2 (Hard), 3 (Good), 4 (Easy)
        """
        # 1. 获取当前卡片
        result = self.conn.execute(
            "SELECT difficulty, stability FROM fsrs_cards WHERE concept = ?",
            (concept,)
        ).fetchone()

        if result:
            card = Card(difficulty=result[0], stability=result[1])
        else:
            card = Card()  # 新卡片

        # 2. FSRS算法更新
        now = datetime.now()
        scheduling_cards = self.fsrs.repeat(card, now)
        updated_card = scheduling_cards[rating].card

        # 3. 写入数据库
        self.conn.execute("""
            INSERT OR REPLACE INTO fsrs_cards
            (concept, canvas_file, difficulty, stability, due, state, last_review, reps)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            concept,
            canvas_file,
            updated_card.difficulty,
            updated_card.stability,
            updated_card.due,
            updated_card.state.name,
            now,
            updated_card.reps
        ))
        self.conn.commit()

# 使用示例
tm = TemporalMemory()

# 记录学习行为
tm.record_behavior(
    canvas_file="离散数学.canvas",
    concept="逆否命题",
    action_type="scoring",
    metadata={"score": 55, "agent": "scoring-agent"}
)

# 更新FSRS卡片 (评分较低, rating=Again)
tm.update_behavior("逆否命题", Rating.Again, "离散数学.canvas")

# 查询薄弱概念
weak_concepts = tm.get_weak_concepts("离散数学.canvas", limit=10)
print(weak_concepts)  # ['逆否命题', '充要条件', ...]
```

**Dependencies**:
- py-fsrs库
- SQLite3

**Risks**:
- 无显著风险 (FSRS算法成熟, SQLite稳定)

**DoD**:
- [ ] AC 4.1-4.5全部通过
- [ ] 单元测试: `tests/test_temporal_memory.py` (15个测试)
- [ ] API文档: `TemporalMemory` class docstring
- [ ] 集成: `canvas_utils.py`调用`TemporalMemory`

---

### 6.2 Agentic RAG Core Stories (12.5-12.9)

---

#### **Story 12.5: LangGraph StateGraph构建**

**优先级**: P0
**Story Points**: 2
**工期**: 2天
**依赖**: Story 12.1 (Graphiti集成完成)
**Assignee**: Dev Agent (James)

**User Story**:
> As a **Agentic RAG开发者**, I want to **使用LangGraph构建StateGraph编排层**, so that **实现并行检索、融合算法和质量控制的智能编排**。

**Acceptance Criteria**:
1. ✅ **AC 5.1**: CanvasRAGState schema定义完成
   - 继承`MessagesState`
   - 包含字段: graphiti_results, lancedb_results, fused_results, reranked_results
   - 策略字段: fusion_strategy, reranking_strategy
   - 质量控制字段: quality_grade, query_rewritten, rewrite_count

2. ✅ **AC 5.2**: CanvasRAGConfig context schema定义完成
   - 配置字段: retrieval_batch_size, fusion_strategy, reranking_strategy
   - quality_threshold, max_rewrite_iterations

3. ✅ **AC 5.3**: 5个核心节点实现
   - `retrieve_graphiti`: 调用Graphiti hybrid_search
   - `retrieve_lancedb`: 调用LanceDB search
   - `fuse_results`: 融合算法 (RRF)
   - `rerank_results`: Reranking (Local)
   - `check_quality`: 质量评估

4. ✅ **AC 5.4**: StateGraph compile成功
   - `builder.compile()`无语法错误
   - Graph可视化: `graph.get_graph().draw_mermaid()`
   - 验证: 节点连接正确

5. ✅ **AC 5.5**: 端到端运行测试
   - 输入query: "逆否命题的应用场景"
   - 输出: reranked_results (Top-10)
   - 验证: 结果非空, rerank_score降序排列

**Technical Details**:
(详见Epic PRD Section 4.2.4 - Agentic RAG编排层代码示例)

**Dependencies**:
- LangGraph (langgraph>=0.2.55)
- Story 12.1 (Graphiti客户端)
- LanceDB (如12.3未完成, 可用mock数据)

**Risks**:
- **R5**: LangGraph版本兼容性
  - **缓解**: 锁定版本`langgraph==0.2.55`

**DoD**:
- [ ] AC 5.1-5.5全部通过
- [ ] 单元测试: `tests/test_state_graph.py` (20个测试)
- [ ] Graph可视化: `docs/architecture/state-graph.mmd` (Mermaid图)
- [ ] 代码: `agentic_rag/state_graph.py`

---

#### **Story 12.6: 并行检索实现 (Send模式)**

**优先级**: P0
**Story Points**: 1.5
**工期**: 1.5天
**依赖**: Story 12.5 (StateGraph构建完成)
**Assignee**: Dev Agent (James)

**User Story**:
> As a **Agentic RAG系统**, I want to **并行调用Graphiti和LanceDB检索**, so that **减少总延迟，提升用户体验**。

**Acceptance Criteria**:
1. ✅ **AC 6.1**: `fan_out_retrieval()`正确dispatch
   - 返回: `[Send("retrieve_graphiti", {...}), Send("retrieve_lancedb", {...})]`
   - 验证: 两个Send对象payload正确

2. ✅ **AC 6.2**: 并行查询延迟 < 100ms
   - Graphiti单独查询: ~45ms
   - LanceDB单独查询: ~52ms
   - 并行查询总延迟: < 60ms (理论最大值)
   - 验证: P95 < 100ms (含并发开销)

3. ✅ **AC 6.3**: RetryPolicy处理异常
   - 模拟ConnectionError: Graphiti查询失败
   - 验证: 自动重试3次, backoff_factor=2.0
   - 最终成功或抛出异常

4. ✅ **AC 6.4**: 结果正确汇聚到fuse_results节点
   - `state["graphiti_results"]`包含10个结果
   - `state["lancedb_results"]`包含10个结果
   - `fuse_results`节点收到两个结果集

**Technical Details**:
(详见Epic PRD Section 4.2.4 - 并行检索代码示例)

**Dependencies**:
- Story 12.5 (StateGraph)
- Graphiti + LanceDB客户端

**Risks**:
- **R2**: Neo4j性能瓶颈
  - **缓解**: 如Graphiti延迟>100ms, 调整batch_size

**DoD**:
- [ ] AC 6.1-6.4全部通过
- [ ] 单元测试: `tests/test_parallel_retrieval.py` (12个测试)
- [ ] 性能测试: `tests/test_retrieval_latency.py`

---

#### **Story 12.7: 3种融合算法实现**

**优先级**: P0
**Story Points**: 2
**工期**: 2天
**依赖**: Story 12.6 (并行检索完成)
**Assignee**: Dev Agent (James)

**User Story**:
> As a **Agentic RAG系统**, I want to **实现RRF、Weighted、Cascade三种融合算法**, so that **根据不同场景自适应选择最优融合策略**。

**Acceptance Criteria**:
1. ✅ **AC 7.1**: RRF算法正确实现
   - 公式: `score = Σ(1/(k+rank))`, k=60
   - 验证: 手工计算Top-3结果, 与算法输出一致

2. ✅ **AC 7.2**: Weighted算法支持alpha/beta参数
   - 公式: `score = alpha * norm(graphiti) + beta * norm(lancedb)`
   - 检验白板场景: alpha=0.7 (薄弱点权重)
   - 日常场景: alpha=0.5

3. ✅ **AC 7.3**: Cascade算法Tier 1/Tier 2正确触发
   - Tier 1: 仅Graphiti
   - Tier 2触发条件: len(Tier1) < 5 OR max(score) < 0.7
   - 验证: 低质量场景触发Tier 2, 高质量场景不触发

4. ✅ **AC 7.4**: 自适应选择逻辑
   - 检验白板生成: fusion_strategy="weighted"
   - 艾宾浩斯复习: fusion_strategy="cascade"
   - 默认: fusion_strategy="rrf"

5. ✅ **AC 7.5**: 融合结果质量
   - MRR@10 ≥ 0.350 (RRF算法)
   - MRR@10 ≥ 0.370 (Weighted算法, 检验白板场景)
   - 测试集: 50个query, 人工标注相关性

**Technical Details**:
(详见Epic PRD Section 4.2.4 - 融合算法代码示例)

**Dependencies**:
- Story 12.6 (并行检索结果)
- NumPy (归一化计算)

**Risks**:
- 无显著风险 (算法逻辑简单)

**DoD**:
- [ ] AC 7.1-7.5全部通过
- [ ] 单元测试: `tests/test_fusion_algorithms.py` (25个测试)
- [ ] 性能测试: MRR@10计算脚本
- [ ] 代码: `agentic_rag/fusion.py`

---

#### **Story 12.8: 混合Reranking策略**

**优先级**: P0
**Story Points**: 2
**工期**: 2天
**依赖**: Story 12.6 (并行检索完成)
**Assignee**: Dev Agent (James)

**User Story**:
> As a **Agentic RAG系统**, I want to **实现Local Cross-Encoder和Cohere API的混合Reranking**, so that **在保证质量的同时，最小化API成本**。

**Acceptance Criteria**:
1. ✅ **AC 8.1**: Local Reranker (bge-reranker-base)正确rerank
   - 输入: query + 10个文档
   - 输出: 10个文档, 按rerank_score降序排列
   - 验证: rerank_score ∈ [0, 1], Top-1 score最高

2. ✅ **AC 8.2**: Cohere Reranker调用成功
   - API: `cohere.rerank(model="rerank-multilingual-v3.0")`
   - 输入: query + 10个文档
   - 输出: Top-10结果, relevance_score降序
   - 验证: API调用成功率 ≥ 99%

3. ✅ **AC 8.3**: hybrid_auto正确选择
   - 检验白板生成: 自动使用Cohere
   - 日常检索: 自动使用Local
   - 验证: `state.get("is_review_canvas")` flag正确传递

4. ✅ **AC 8.4**: 成本监控
   - Cohere调用计数: LangSmith tracking
   - 月度限额: <50 requests
   - 告警: 接近限额时warning log

5. ✅ **AC 8.5**: Reranking质量提升
   - Local Reranker: MRR@10提升 ≥ +0.08 (vs 无Rerank)
   - Cohere Reranker: MRR@10提升 ≥ +0.12
   - 测试集: 50个query

**Technical Details**:
(详见Epic PRD Section 4.2.4 - Reranking代码示例)

**Dependencies**:
- sentence-transformers (Local Reranker)
- Cohere API
- Story 12.6 (融合结果)

**Risks**:
- **R3**: Cohere API限流
  - **缓解**: 自动降级到Local, 备用API Key

**DoD**:
- [ ] AC 8.1-8.5全部通过
- [ ] 单元测试: `tests/test_reranking.py` (18个测试)
- [ ] 成本监控: LangSmith dashboard配置
- [ ] 代码: `agentic_rag/reranking.py`

---

#### **Story 12.9: 质量控制循环**

**优先级**: P0
**Story Points**: 1.5
**工期**: 1.5天
**依赖**: Story 12.7 (融合算法), Story 12.8 (Reranking)
**Assignee**: Dev Agent (James)

**User Story**:
> As a **Agentic RAG系统**, I want to **实现质量检查和Query重写循环**, so that **在检索质量不足时自动优化查询，提升最终结果**。

**Acceptance Criteria**:
1. ✅ **AC 9.1**: Quality checker正确分级
   - high: Top-3平均分 ≥ 0.7
   - medium: Top-3平均分 0.5-0.7
   - low: Top-3平均分 < 0.5

2. ✅ **AC 9.2**: Query rewriter在low质量时触发
   - 条件: quality_grade=="low" AND rewrite_count < 2
   - LLM调用: gpt-3.5-turbo
   - Prompt: "原始问题未找到高质量结果，请从不同角度重写问题"

3. ✅ **AC 9.3**: 最多2次迭代后强制返回
   - rewrite_count ≥ 2: 直接返回END
   - 防止死循环: 最大总延迟<10秒

4. ✅ **AC 9.4**: Rewrite后质量提升
   - 测试集: 20个low质量query
   - Rewrite后: 平均quality_grade提升 (low → medium/high)
   - avg_score提升 ≥ +0.15

5. ✅ **AC 9.5**: 循环逻辑正确
   - 流程: check_quality → (low?) → rewrite_query → START (重新检索)
   - 验证: StateGraph执行trace, 循环次数≤2

**Technical Details**:
(详见Epic PRD Section 4.2.4 - 质量控制代码示例)

**Dependencies**:
- Story 12.7, 12.8 (Rerank结果)
- OpenAI gpt-3.5-turbo

**Risks**:
- **R4**: Query重写死循环
  - **缓解**: 硬编码max_rewrite=2, 总延迟<10秒

**DoD**:
- [ ] AC 9.1-9.5全部通过
- [ ] 单元测试: `tests/test_quality_control.py` (15个测试)
- [ ] LangSmith trace验证: 循环逻辑可视化
- [ ] 代码: `agentic_rag/quality_control.py`

---

### 6.3 Integration & Testing Stories (12.10-12.16)

---

#### **Story 12.10: Canvas检验白板生成集成**

**优先级**: P0
**Story Points**: 1
**工期**: 1天
**依赖**: Story 12.9 (质量控制完成)
**Assignee**: Dev Agent (James)

**User Story**:
> As a **Canvas学习系统用户**, I want to **使用新Agentic RAG生成检验白板**, so that **检验题更精准地针对我的薄弱点，准确率提升至85%**。

**Acceptance Criteria**:
1. ✅ **AC 10.1**: `generate_verification_canvas()`集成Agentic RAG
   - 替换现有单一检索逻辑
   - 调用: `canvas_agentic_rag.invoke(...)`
   - 传递: canvas_file, is_review_canvas=True (触发Weighted融合 + Cohere Rerank)

2. ✅ **AC 10.2**: 检验白板生成准确率 ≥ 85%
   - 测试集: 10个Canvas, 100个检验题
   - 人工评估: 相关性 (相关/不相关)
   - 验证: 相关题数 ≥ 85

3. ✅ **AC 10.3**: 向后兼容Epic 4
   - Epic 4现有功能: 提取红色/紫色节点 → 生成检验题 → 创建Canvas
   - 验证: 集成后无breaking changes
   - 测试: Epic 4的12个测试全部通过

4. ✅ **AC 10.4**: 性能不退化
   - 检验白板生成总时间: <5秒 (vs 当前~8秒, 提升37%)
   - 检索延迟: <400ms (Agentic RAG部分)
   - LLM生成时间: ~3秒 (不变)

5. ✅ **AC 10.5**: 错误处理
   - Agentic RAG失败: 降级到单一检索 (LanceDB only)
   - 日志: 记录降级事件, 告警
   - 验证: 降级后仍能生成检验白板 (质量可能降低)

**Technical Details**:
```python
# canvas_utils.py - CanvasOrchestrator

from agentic_rag.state_graph import canvas_agentic_rag
from agentic_rag.config import CanvasRAGConfig

class CanvasOrchestrator:
    async def generate_verification_canvas(
        self,
        canvas_file: str,
        output_canvas_file: str
    ) -> str:
        """生成检验白板 (增强版, 使用Agentic RAG)"""

        # 1. 提取红色/紫色节点
        red_purple_nodes = self.extract_verification_nodes(canvas_file)

        # 2. 使用Agentic RAG检索薄弱点
        config = CanvasRAGConfig(
            fusion_strategy="weighted",  # 薄弱点权重70%
            reranking_strategy="cohere",  # 检验白板用Cohere
            retrieval_batch_size=10
        )

        try:
            results = await canvas_agentic_rag.ainvoke(
                {
                    "messages": [{"role": "user", "content": f"检索Canvas薄弱点: {canvas_file}"}],
                    "canvas_file": canvas_file,
                    "is_review_canvas": True
                },
                config={"context": config}
            )

            reranked_results = results["reranked_results"]

        except Exception as e:
            # 降级到单一检索
            logger.warning(f"Agentic RAG失败, 降级到LanceDB: {e}")
            reranked_results = self._fallback_lancedb_search(canvas_file)

        # 3. 生成检验题 (调用verification-question-agent)
        verification_questions = self.generate_verification_questions_with_agent(
            red_purple_nodes,
            reranked_results
        )

        # 4. 创建检验白板Canvas
        self.create_verification_canvas(
            verification_questions,
            output_canvas_file
        )

        return output_canvas_file
```

**Dependencies**:
- Story 12.9 (Agentic RAG完整)
- Epic 4 (generate_verification_canvas现有逻辑)

**Risks**:
- **R10**: Epic 4集成问题
  - **缓解**: 独立adapter层, 不修改Epic 4核心代码

**DoD**:
- [ ] AC 10.1-10.5全部通过
- [ ] 单元测试: `tests/test_canvas_agentic_rag_integration.py` (15个测试)
- [ ] 回归测试: Epic 4的12个测试通过
- [ ] 代码: `canvas_utils.py`修改 (adapter模式)

---

#### **Story 12.11-12.16: 其他Integration & Testing Stories**

(详细AC见Epic PRD Section 10.1-10.2, 此处简化)

**Story 12.11: graphiti-memory-agent调用接口** (P1, 0.5天)
- **目标**: 封装Graphiti为Agent调用接口
- **AC**: `add_episode()` / `search_memories()` wrapper正确工作

**Story 12.12: LangSmith可观测性集成** (P1, 1天)
- **目标**: Trace + 成本监控 + 性能仪表盘
- **AC**: 100%检索请求可追踪, 成本实时监控

**Story 12.13: 回归测试** (P1, 0.5天)
- **目标**: Epic 1-10核心功能验证
- **AC**: 360+测试全部通过, 无退化

**Story 12.14: 性能基准测试** (P1, 1天)
- **目标**: 自动化MRR/Recall/F1测试
- **AC**: MRR@10 ≥ 0.380, Recall@10 ≥ 0.68, F1 ≥ 0.77

**Story 12.15: E2E集成测试** (P0, 1天)
- **目标**: 2个场景完整测试 (检验白板 + 艾宾浩斯)
- **AC**: 端到端无报错, 质量指标达标

**Story 12.16: 文档和部署** (P0, 0.5天)
- **目标**: 用户指南 + 运维手册
- **AC**: 文档完整, 部署步骤清晰

---

### 6.4 Enhancement Story (12.17)

#### **Story 12.17: 多模态支持 (ImageBind集成)**

**优先级**: P2 (Optional, 推迟Phase 5)
**Story Points**: 2
**工期**: 2天
**依赖**: Story 12.3 (LanceDB迁移完成)
**Assignee**: Dev Agent (James)

**User Story**:
> As a **Canvas学习系统用户**, I want to **检索图像和音频学习材料**, so that **支持更广泛的学习场景，如物理实验视频、语言发音音频**。

**Acceptance Criteria**:
1. ✅ **AC 17.1**: ImageBind模型加载成功
   - CUDA环境验证 (torch.cuda.is_available())
   - ImageBind模型下载: `facebookresearch/ImageBind`
   - 6模态支持: text, image, audio, video, depth, IMU

2. ✅ **AC 17.2**: 跨模态检索成功
   - 文本查询 → 检索图像文档 (例如: "逻辑电路图")
   - 图像查询 → 检索文本文档 (反向检索)
   - 验证: Top-10结果包含至少3个图像文档

3. ✅ **AC 17.3**: 性能可接受
   - ImageBind embedding生成: <200ms/image (GPU加速)
   - 跨模态检索延迟: <300ms (10K文档)

4. ✅ **AC 17.4**: 多模态Canvas节点支持
   - Canvas节点包含图像: `{"type": "file", "file": "diagram.png"}`
   - 自动embedding: 图像节点添加时触发ImageBind
   - 检索: 文本查询可检索到图像节点

**Technical Details**:
(详见Epic PRD Section 4.2.2 - LanceDB多模态代码示例)

**Dependencies**:
- CUDA环境 (GPU)
- ImageBind模型
- Story 12.3 (LanceDB)

**Risks**:
- **高风险**: ImageBind模型依赖, CUDA环境要求
- **决策**: Epic 12不包含, 推迟到Phase 5独立Epic

**DoD**:
- [ ] AC 17.1-17.4全部通过 (如果开发)
- [ ] 文档: `docs/architecture/MULTIMODAL-SUPPORT.md`
- [ ] **注**: Epic 12 MVP不包含此Story

---

## 7. Acceptance Criteria Summary

### 7.1 按Story汇总

| Story | AC数量 | 关键AC | 验收方式 |
|-------|--------|--------|---------|
| 12.1 | 5 | Graphiti hybrid_search返回结果 | 自动化测试 + 手工验证 |
| 12.2 | 5 | P95延迟<50ms (100K向量) | 性能基准测试 |
| 12.3 | 5 | 数据一致性100% | 一致性校验脚本 |
| 12.4 | 5 | get_weak_concepts()返回FSRS结果 | 单元测试 |
| 12.5 | 5 | StateGraph compile成功 | 单元测试 + Graph可视化 |
| 12.6 | 4 | 并行延迟<100ms | 性能测试 |
| 12.7 | 5 | MRR@10 ≥ 0.350 (RRF) | 性能基准测试 |
| 12.8 | 5 | Cohere API成功率≥99% | 成本监控 + 单元测试 |
| 12.9 | 5 | Rewrite后质量提升+0.15 | A/B测试 |
| 12.10 | 5 | 检验白板准确率≥85% | 人工评估 (100题) |
| 12.11 | 2 | Wrapper正确工作 | 单元测试 |
| 12.12 | 3 | 100% trace覆盖 | LangSmith dashboard |
| 12.13 | 1 | 360+测试通过 | 自动化测试 |
| 12.14 | 3 | MRR/Recall/F1达标 | 自动化测试 |
| 12.15 | 2 | 2个场景端到端通过 | E2E测试 |
| 12.16 | 2 | 文档完整 | 人工Review |
| 12.17 | 4 | 跨模态检索成功 | Demo验证 |
| **总计** | **66** | - | - |

### 7.2 Epic-Level AC (必须全部通过)

**从Story AC推导的Epic AC**:

| Epic AC ID | 描述 | 对应Story | 验收标准 |
|------------|------|-----------|---------|
| **EAC-1** | 3层记忆系统正常运行 | 12.1-12.4 | 5个AC全部通过 |
| **EAC-2** | Agentic RAG检索质量达标 | 12.5-12.10, 12.14 | MRR@10≥0.380, Recall≥0.68, F1≥0.77, 准确率≥85% |
| **EAC-3** | Agentic RAG性能达标 | 12.6, 12.14 | P95<400ms, P99<600ms, 10 QPS, 1M+向量 |
| **EAC-4** | 融合算法和Reranking正确运行 | 12.7-12.8 | RRF/Weighted/Cascade正确, Local+Cohere自动选择 |
| **EAC-5** | 质量控制循环有效 | 12.9 | Quality分级正确, Rewrite提升+0.15 |
| **EAC-6** | Canvas集成无缝 | 12.10, 12.13, 12.15 | Epic 4集成成功, 360+测试通过, E2E通过 |
| **EAC-7** | 成本控制 | 12.8, 12.12 | 年度≤$60, Cohere≤$20, LLM≤$5 |
| **EAC-8** | 可观测性 | 12.12 | 100% trace, 成本监控, P50/P95/P99展示 |
| **EAC-9** | 测试覆盖 | 12.13-12.15 | 单元≥80%, 集成2场景, 回归360+ |
| **EAC-10** | 文档完整性 | 12.16 | ADRs + API docs + 用户指南 + 运维手册 |

---

## 8. Risk-Story Mapping

### 8.1 Risk → Story对应关系

**将Epic PRD Section 8的10个风险映射到Story**:

| Risk ID | Risk描述 | 影响Story | 缓解Story | 责任人 |
|---------|---------|-----------|----------|--------|
| **R1** | LanceDB迁移数据丢失 | 12.3 | 12.3 (AC 3.5: Rollback plan) | Dev |
| **R2** | Neo4j性能瓶颈 | 12.1, 12.6 | 12.2 (性能测试), 12.14 (基准测试) | Dev |
| **R3** | Cohere API限流 | 12.8 | 12.8 (AC 8.4: 成本监控), 12.12 (告警) | Dev |
| **R4** | Query重写死循环 | 12.9 | 12.9 (AC 9.3: 最多2次迭代) | Dev |
| **R5** | LangGraph版本兼容性 | 12.5 | 12.5 (锁定版本) | Dev |
| **R6** | Cohere成本超预算 | 12.8 | 12.12 (成本监控), 12.8 (降级策略) | Dev |
| **R7** | OpenAI成本上升 | 12.9 | 12.9 (使用gpt-3.5-turbo), 12.12 (监控) | Dev |
| **R8** | 开发时间超期 | All | MVP优先 (12.1-12.10, 12.15-12.16), P1可延后 | PM/SM |
| **R9** | 测试时间不足 | 12.13-12.15 | 自动化测试优先 (12.14), 预留3天测试 | QA |
| **R10** | Epic 10记忆存储功能缺失 | 12.1, 12.11 | 12.1 (回填Epic 10功能) | Dev |

### 8.2 高风险Story识别

**关键路径 + 高风险 = 需要特别关注**:

| Story | 关键路径? | 风险等级 | 关注点 | 建议 |
|-------|-----------|---------|--------|------|
| **12.1** | ✅ Yes | 🔴 High | Neo4j部署, 性能瓶颈 | +20% buffer, 预先POC |
| **12.3** | ❌ No | 🟡 Medium | 数据丢失风险 | 完整备份, 一致性校验 |
| **12.5** | ✅ Yes | 🟡 Medium | LangGraph版本兼容 | 锁定版本 |
| **12.7** | ✅ Yes | 🟢 Low | 算法逻辑 | 单元测试充分 |
| **12.10** | ✅ Yes | 🟡 Medium | Epic 4集成 | Adapter模式, 回归测试 |

---

## 附录 A: Story Template

**标准Story格式** (供SM参考):

```markdown
# Story XX.X: [Story名称]

**优先级**: P0/P1/P2
**Story Points**: X
**工期**: X天
**依赖**: Story X.X
**Assignee**: Dev Agent (James)

## User Story
> As a **[角色]**, I want to **[功能]**, so that **[业务价值]**.

## Acceptance Criteria
1. ✅ **AC X.1**: [验收标准1]
   - [具体细节]
   - 验证: [验证方法]

2. ✅ **AC X.2**: [验收标准2]
   ...

## Technical Details
```[language]
[代码示例或技术说明]
```

## Dependencies
- [外部依赖]
- [Story依赖]

## Risks
- **RX**: [风险描述]
  - **缓解**: [缓解策略]

## DoD (Definition of Done)
- [ ] AC X.1-X.N全部通过
- [ ] 单元测试: `tests/test_xxx.py`
- [ ] 文档: `docs/xxx.md`
- [ ] 代码: `xxx.py`
```

---

**文档版本**: v1.0
**最后更新**: 2025-11-14
**SM Handoff Ready**: ✅
**下一步**: SM (Bob) 基于本Story Map创建详细User Story文件
