# Canvas Learning System 后端架构调研报告

> **日期**: 2026-03-10
> **来源**: Plan Mode 调研会话 (17 个章节，综合 3 轮并行 Explore Agent 调研)
> **目标**: 分析后端 agent 生成宽泛通用解释的根因，调研社区成熟方案，评估重构方向

---

## 调研背景

Canvas Learning System 后端 agent 生成宽泛、通用的解释，不针对用户具体困惑点。核心问题：

1. **无 intent 分类层** — `agent_routing_engine.py` 纯正则路由（~30 patterns，精度约 60%）
2. **无焦点提取** — `call_explanation()` 不知道用户卡在哪
3. **Context 不分轻重** — `enrich_with_adjacent_nodes()` 全量 dump 15K+ chars
4. **知识图谱记了不用** — Graphiti misconception 数据未参与 context 过滤

---

## 一、社区是否有成熟方案？

### 1.1 Intent Classification（意图分类）— ★★★★★ 非常成熟

#### Semantic Router (aurelio-labs/semantic-router)
- **Stars**: 3.3k | **License**: MIT | **维护**: 活跃 (2025.11 最近更新)
- **原理**: 预编码 intent 示例 → 向量最近邻匹配 → 返回 Route
- **精度**: 92-96% (embedding-based)
- **延迟**: 50ms (本地) / 100-150ms (API)
- **成本**: $0 (本地 intfloat/multilingual-e5-base) 或 $20/百万次 (OpenAI embedding)
- **中文支持**: ✅ 需要 `intfloat/multilingual-e5-base` 或 Cohere Embed 3
- **LangGraph 集成**: ✅ 原生支持，可作为 `add_conditional_edges` 的路由函数
- **代码量**: 15-30 行即可完成基本设置

```python
# 最小示例
from semantic_router import Route
from semantic_router.encoders import HuggingFaceEncoder
from semantic_router.routers import SemanticRouter

misconception = Route(name="misconception_probe", utterances=[
    "我不明白为什么A*这样做", "这不对吧", "我以为应该是这样",
    "看不懂这个推导", "为什么不能直接用贪心",
])
concept = Route(name="concept_explanation", utterances=[
    "解释值迭代算法", "什么是启发式搜索",
    "A*和UCS有什么区别", "介绍一下 Bellman 方程",
])
verification = Route(name="verification", utterances=[
    "这样理解对吗", "我觉得Q-learning就是贪心，对不对",
    "这个答案是不是应该选B",
])
problem = Route(name="problem_solving", utterances=[
    "帮我算这道 MDP 题", "这个搜索树怎么展开", "下一步应该怎么做",
])

encoder = HuggingFaceEncoder(model_name="intfloat/multilingual-e5-base")
router = SemanticRouter(encoder=encoder, routes=[misconception, concept, verification, problem])

result = router("我不理解BFS为什么这样遍历")
# → Route(name="misconception_probe")
```

#### 对比替代方案

| 方案 | 精度 | 延迟 | 成本 | 复杂度 |
|------|:---:|:---:|:---:|:---:|
| **Semantic Router** (推荐) | 92-96% | 50ms | $0 (本地) | 15行 |
| LangChain RouterChain | 95%+ | 500-2000ms | $2.50/百万 | 更多 boilerplate |
| 自建 sentence-transformers | 90%+ | 50ms | $0 | 80行 |
| 纯正则 (当前方案) | ~60% | <1ms | $0 | 已有 |
| LLM 直接路由 | 95%+ | 1000-2000ms | 贵 | 简单 |

**结论**: Semantic Router 是最佳选择 — 精度高、延迟低、免费、有 LangGraph 原生集成。

---

### 1.2 Context Relevance Filtering（上下文相关性过滤）— ★★★★ 成熟

#### CRAG (Corrective RAG) — LangGraph 官方示例

**架构**:
```
检索文档 → LLM 逐条评分(yes/no) → 过滤低分 → 不够则改写 query 重搜 → 只传相关文档
```

**评分方式**: LLM structured output (binary yes/no)
- 精度: 85-92%
- 延迟: 200-500ms/文档
- 成本: $0.01-0.02/次评分

#### 更便宜的替代方案

| 方案 | 精度 | 延迟 | 成本 | 适用场景 |
|------|:---:|:---:|:---:|------|
| **LLM grading** (CRAG 默认) | 85-92% | 200-500ms/doc | $0.01/doc | 高要求场景 |
| **Cross-encoder reranking** | 78-85% | 50-200ms/10docs | $0 | **教育场景推荐** |
| **BM25 关键词** | 60-75% | <10ms/100docs | $0 | 术语精确匹配 |
| **Hybrid: BM25→Cross-encoder** | **82-88%** | **20-100ms** | **$0** | **最佳性价比** |

**Hybrid 方案代码**:
```python
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder

# Stage 1: BM25 快速过滤到 top-20
bm25 = BM25Okapi(corpus)
candidates = bm25.get_top_k(question, k=20)

# Stage 2: Cross-encoder 精排
model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
pairs = [[question, doc] for doc in candidates]
scores = model.predict(pairs)
relevant = [doc for doc, score in zip(candidates, scores) if score > 0.5]
```

#### Context Budget 截断

```python
def select_by_token_budget(documents, budget=2000):
    selected, tokens_used = [], 0
    for doc in sorted_by_relevance(documents):
        doc_tokens = count_tokens(doc)
        if tokens_used + doc_tokens <= budget:
            selected.append(doc)
            tokens_used += doc_tokens
        else:
            break
    return selected
```

**关键原则**: 用 token budget 替代 top-k — top-k 不可预测（5 篇可能 2K 或 10K tokens），budget 保证信息密度最大化。

**结论**: Hybrid BM25→Cross-encoder + token budget 是教育场景最佳方案 — 免费、快速、精度接近 LLM。

---

### 1.3 Student Model & Knowledge Tracing — ★★★★★ 非常成熟

#### OATutor 的 BKT 实现 (CAHLR/OATutor)

**BKT 参数** (每个 Knowledge Component):
```
P(L₀)  — 初始掌握概率
P(G)   — 猜对概率 (不会但猜对)
P(S)   — 失误概率 (会但做错)
P(T)   — 学习转移概率 (不会→会)
```

**Mastery 计算**:
- 每步: `step_mastery = ∏(KC_masteries)`
- 每题: `problem_mastery = ∏(step_masteries)`
- 自适应选题: **最低 mastery 优先**

**你的系统对比**: 你已经有 Graphiti misconception 数据 + mastery endpoint (BKT+FSRS)，但：
- mastery 数据未用于 context 过滤
- misconception 记录未影响下次解释的焦点
- 没有 "最低 mastery 优先" 的自适应逻辑

---

### 1.4 Educational Intent Classification — ★★★ 学术阶段

#### 实用 4 类分类 (适用于本系统场景)

| 意图 | 学生话语示例 | 系统响应 |
|------|------------|---------|
| misconception_probe | "我不明白为什么..." "这不对吧" | Feynman 简化解释 |
| problem_solving | "帮我解这道题" "下一步怎么做" | Hint scaffolding |
| verification | "这样对吗" "我理解得正确吗" | 评价+纠偏 |
| concept_explanation | "什么是 X" "解释 Y" | 结构化概念讲解 |

---

## 二、是否有人做了类似的项目？

### 直接竞品/类似项目

| 项目 | 与你的相似度 | 架构 | 缺什么 |
|------|:---:|------|------|
| **Obsidian Augmented Canvas** | ★★★★ | Canvas 节点→OpenAI→新笔记 | 无 KG、无学生模型、无 context enrichment |
| **Obsidian Chat Stream** | ★★★ | 祖先节点内容作为上下文 | 无 KG、无 intent 分类 |
| **Obsidian Canvas Conversation** | ★★ | Canvas 节点对话流 | 无状态、无记忆 |
| **DeepTutor** (HKUDS) | ★★☆ | LangGraph + 个性化学习路径 | 面向 PDF，非 Canvas |
| **AITutorAgent** | ★★ | LangGraph 4-state + SQLite | 无 Canvas、无 KG |
| **OATutor** | ★★ | React + BKT + Firebase | 无 AI agent、静态内容 |
| **ATLAS** | ★ | LangGraph 4-agent 协调 | 学术任务管理，非辅导 |

### 结论：**没有人做过和你完全一样的东西**

你的系统同时在做 4 件事：
1. 视觉空间组织 (Canvas 节点拓扑)
2. AI agent 生成 (LangGraph React Agent + 7 工具)
3. 知识图谱记忆 (Graphiti/Neo4j)
4. 个性化学生模型 (misconception tracking + mastery)

社区里这 4 件事通常是**分开做的**。最接近的组合是 Augmented Canvas + Chat Stream，但只有 <500 行代码，无后端。

---

## 三、可借鉴的架构模式

### 3.1 从 AITutorAgent 借鉴
- **LangGraph State 持久化**: 用 SQLite 存 conversation history，按 conversation_id 索引
- **消息类型分类**: tutorial / question / evaluation 三类，隐式路由

### 3.2 从 OATutor 借鉴
- **BKT per KC**: 每个 Knowledge Component 独立追踪 P(mastery)
- **最低 mastery 优先选题**: 优先解释学生最薄弱的点

### 3.3 从 Chiron 借鉴
- **70% 理解阈值**: 理解不达标→触发 Feynman 简化→重新验证
- **Checkpoint 模型**: 不允许跳过未掌握的环节

### 3.4 从 CRAG 借鉴
- **检索后评分**: 不盲目传递所有文档，先评分过滤
- **Query 改写**: 检索结果不够好时自动重构搜索词

### 3.5 综合推荐架构

```
学生在 Canvas 节点写内容
    ↓
┌─────────────────────────────────┐
│  1. Intent Classification       │  ← Semantic Router (50ms, $0)
│  输入: 节点文本 + 颜色链         │
│  输出: misconception_probe /     │
│        concept_explanation / ... │
└─────────────┬───────────────────┘
              ↓
┌─────────────────────────────────┐
│  2. Focal Point Extraction      │  ← 规则 + 节点链分析 (<1ms)
│  输入: 节点文本 + 父节点上下文    │
│  输出: 具体困惑点 (1-2句)        │
└─────────────┬───────────────────┘
              ↓
┌─────────────────────────────────┐
│  3. Student Model Query         │  ← Graphiti + Mastery API
│  输入: focal_point 主题词        │
│  输出: 历史 misconception +      │
│        当前 mastery score        │
└─────────────┬───────────────────┘
              ↓
┌─────────────────────────────────┐
│  4. Context Retrieval + Filter  │  ← Hybrid BM25→Cross-encoder
│  输入: focal_point + 邻居节点    │     + token budget (3000 chars)
│  输出: 只保留相关上下文          │
└─────────────┬───────────────────┘
              ↓
┌─────────────────────────────────┐
│  5. Specialized Agent           │  ← 按 intent 分发不同 agent
│  misconception → 纠偏型 agent    │
│  concept → 概念解释型 agent      │
│  verification → 评价型 agent     │
│  problem → 解题引导型 agent      │
└─────────────┬───────────────────┘
              ↓
  输出: 针对性回答 (而非宽泛解释)
```

---

## 四、架构演进分析 (Git History)

### 4.1 演进时间线

```
Epic 15-21 (Nov-Dec 2025): 直接 Gemini API 调用
  agent_service.py → gemini_client.call_agent() → client.aio.models.generate_content()
  本质: single-shot LLM call，system_prompt + context 字符串拼接
  无 LangGraph、无 StateGraph、无 tool calling
    ↓
commit 17b5590 (Mar 8 2026): "Agent architecture rebuild"
  一次性新增 3 个阶段:
    Phase 2: tool_definitions.py + tool_executor.py (手动工具调用) — ❌ 从未启用
    Phase 3: agent_graph.py (StateGraph CRAG 管道, 595行)  — ❌ 从未启用
    Phase 4: react_agent.py (create_react_agent 黑箱, 363行) — ✅ 唯一启用
    ↓
现在: create_react_agent 黑箱运行，Phase 3 StateGraph 代码沉睡
```

### 4.2 关键发现: Phase 3 StateGraph 已实现 CRAG

`src/agentic_rag/agent_graph.py` (595行) 已经包含了调研推荐的 CRAG 架构：

```
START → analyze_intent → retrieve → grade_documents → generate_answer → END
                                          ↓ (文档不相关)
                                    rewrite_query → analyze_intent (循环)
```

5 个节点: `analyze_intent`, `retrieve`, `grade_documents`, `rewrite_query`, `generate_answer`
环境变量: `ENABLE_AGENT_GRAPH=false` (从未开启)

### 4.3 架构审计: 5 个维度对比

| 维度 | 当前实现 | 社区成熟方案 | 差距 |
|------|---------|-------------|------|
| 路由 | 正则 30 patterns (~60%) | Semantic Router (92-96%) | ⚠️ 大 |
| 焦点提取 | ❌ 完全缺失 | 规则+节点链分析 | ❌ 缺失 |
| Context 过滤 | 全量 dump 15K+ | Hybrid BM25→Cross-encoder + budget | ⚠️ 大 |
| 学生模型 | Graphiti 有数据但未用 | BKT + mastery→context 管道 | ⚠️ 中 |
| 检索/搜索 | React Agent + LanceDB | ✅ 可接受 | ✅ OK |

### 4.4 Phase 2/3 从未使用的根因

1. **三个 Phase 在同一个 commit (`17b5590`) 一起写的** — 不存在渐进升级历史
2. `.env` 只设了 `ENABLE_REACT_AGENT=true`，Phase 2/3 被注释
3. Phase 2/3 是"架构蓝图"，实际开发直接跳到了 Phase 4 终态
4. 路由代码完整 (call_explanation 2659-2710行)，Phase 3 方法已实现，只是从未开启

### 4.5 Phase 3 StateGraph 的可复用性

`agent_graph.py` 已实现:
- ✅ analyze_intent, retrieve, grade_documents, rewrite_query, generate_answer
- ✅ 遵循 LangGraph 官方 Agentic RAG 模式
- ❌ 缺少: focal_point 提取、student model 查询、context budget、Semantic Router

---

## 五、算法设计质量审计

### 审计方法

对后端管道中的 **5 个算法环节** 逐一评判：

### 算法 1: Agent 路由 (AgentRoutingEngine) — ❌ 不合格

| 指标 | 你的设计 | 最低有效标准 | 社区最佳实践 |
|------|---------|:---:|:---:|
| 分类精度 | ~60% | 80% | 92-96% |
| 中文语义理解 | 无（关键词匹配） | 需要 | embedding-based |
| 意图粒度 | 6种（按模板分） | 4种（按需求分） | 11种 |
| 上下文感知 | 无（不看节点颜色/位置） | 需要 | intent + context |

**核心问题**: 正则 pattern 不理解语义。"我觉得应该用BFS而不是DFS" 不匹配任何 pattern，但这明显是 `verification` intent。

**论文依据**: ArXiv 2502.15096 (教育场景意图分类), ArXiv 2506.07626 (MathDial 11-point 意图体系)

### 算法 2: Context Enrichment — ❌ 不合格

| 指标 | 你的设计 | 最低有效标准 | 社区最佳实践 |
|------|---------|:---:|:---:|
| 上下文量 | 15K+ chars（全量） | <5K chars | 3K chars (budget-based) |
| 相关性过滤 | 无 | 至少 keyword overlap | Cross-encoder reranking |
| 优先级 | 无（所有节点平等） | parent > child | multi-factor scoring |
| 截断策略 | 无 | top-k | token budget |

**核心问题**: LLM 面对 15K 字的无关上下文，注意力分散，输出宽泛解释。**这是"回答太泛"问题的直接原因。**

**论文依据**: MDPI 2025 multi-factor relevance scoring, LangChain Context Engineering, Pinecone Reranking

### 算法 3: Focal Point — ❌ 缺失

| 指标 | 你的设计 | 最低有效标准 | 社区最佳实践 |
|------|---------|:---:|:---:|
| 焦点提取 | 无 | 从文本提取问句 | 困惑类型分类 + 焦点定位 |
| Agent 输入 | 只有 topic + content | 需要 focal_point | focal_point + confusion_type + parent_context |

**核心问题**: Agent 拿到的 prompt 只有"主题"和"内容"，没有"学生具体卡在哪"。就像医生只知道"患者来内科"，不知道"哪里不舒服"。

**论文依据**: Stanford MOOCPost (29K 标注, 分类后满意度提升 25-35%), Duolingo "Explain My Answer", Chiron 70% 阈值

### 算法 4: Student Model 利用 — ❌ 未完成

| 指标 | 你的设计 | 最低有效标准 | 社区最佳实践 |
|------|---------|:---:|:---:|
| 历史查询 | 不查 | 查 misconception | 查 misconception + mastery + 学习路径 |
| 个性化 | 无 | 已知误解注入 context | student-model-aware filtering |
| 自适应 | 无 | 最低 mastery 优先 | BKT + attention-weighted |

**核心问题**: Graphiti + mastery 系统数据完整，但**从未影响 agent 的输出**。学生第三次问同一个概念，agent 还是给出和第一次一样的通用解释。

**论文依据**: Stanford LC-RAG (个性化 RAG 提升 15-25%), KG-RAG IEEE (分数提升 35%), KGAT KDD 2019

### 算法 5: 检索工具 — ⚠️ 可接受

| 指标 | 你的设计 | 最低有效标准 | 社区最佳实践 |
|------|---------|:---:|:---:|
| 搜索策略 | LLM 自主决定 | 有效但不稳定 | 预路由 + 条件检索 |
| 混合搜索 | LanceDB (向量+关键词) | 达标 | + reranking |
| 多工具 | 7个工具 | 够用 | 工具数量不是关键 |

这是管道中**唯一基本合格的环节**。

### 管道质量评分总结

```
用户输入 → [算法1:路由] → [算法2:Context] → [算法3:焦点] → [算法4:学生模型] → [算法5:检索] → Agent 输出
              ❌ 60%         ❌ 全量dump        ❌ 缺失         ❌ 未使用          ⚠️ 可接受
```

| 算法环节 | 评分 | 核心问题 | 修复优先级 |
|---------|:---:|---------|:---:|
| 1. Agent 路由 | 不合格 | 正则无法理解语义 | P1 |
| 2. Context Enrichment | 不合格 | 全量 dump 是"回答太泛"的直接原因 | **P0** |
| 3. Focal Point | 缺失 | Agent 不知道用户卡在哪 | **P0** |
| 4. Student Model | 未完成 | 有数据但没接入管道 | P1 |
| 5. 检索工具 | 可接受 | 搜索本身没问题 | P2 |

---

## 六、LangGraph 使用分析

### 你用了什么、没用什么

```
层次 1: create_react_agent()    ← 你用的（仅此）— 黑箱
层次 2: StateGraph              ← 你没用 — LangGraph 的核心能力
层次 3: Supervisor / Swarm      ← 你完全没用 — 多 agent 编排
```

**核心认知差距**:

```
你以为你在用 LangGraph:
  create_react_agent() → LLM 自主搜索和回答

你实际在用的:
  LLM + 一堆工具 → 黑箱（你不控制中间过程）

你应该用的:
  StateGraph → 你定义每个步骤 → 每个步骤可以是 LLM 调用、也可以是纯 Python 逻辑
```

### 对比：黑箱 vs 白箱

**当前管道（Phase 4 黑箱）**:
```
用户输入 → [正则路由选模板] → [全量dump上下文] → create_react_agent(黑箱) → 输出
                                                    ↑ LLM自己决定搜什么、怎么回答
                                                    ↑ 你无法控制
```

**应该做的管道（StateGraph 白箱）**:
```
用户输入 → [Node 1: Intent分类]     ← 纯Python或Semantic Router, 不需要LLM
         → [Node 2: 焦点提取]       ← 纯Python, 从文本+节点链提取
         → [Node 3: 学生模型查询]   ← Graphiti查询, 不需要LLM
         → [Node 4: Context过滤]    ← Cross-encoder或规则评分
         → [条件分支: 按intent分发]
              ├─ misconception → create_react_agent(纠偏工具集)
              ├─ concept      → create_react_agent(解释工具集)
              └─ verification → create_react_agent(评价工具集)
         → [Node 5: 输出验证]       ← 检查输出是否回应了focal_point
         → 输出
```

---

## 七、双记忆系统分析

### System 1: 全局笔记检索 (LanceDB + Obsidian CLI)

**当前**: LanceDB hybrid search (vector + FTS), 不提取 Obsidian frontmatter/tags
**Gap**: 加了标签也白加——索引管道不读取

**推荐分工**:

| 检索需求 | 最佳工具 | 原因 |
|---------|---------|------|
| "关于 A* 的所有笔记" | LanceDB 向量搜索 | 语义相似性 |
| "标记为 #search 的笔记" | Obsidian CLI `tags` | 直接访问 Obsidian 索引 |
| "引用了 MDP 笔记的所有笔记" | Obsidian CLI `backlinks` | wikilink 图结构 |
| "Lecture 9-10 范围内的 MDP 内容" | LanceDB + 元数据过滤 | 路径+语义双重过滤 |

### System 2: 学习进度追踪 (Graphiti + BKT+FSRS)

**当前**: Neo4j 写入完整，BKT+FSRS 计算正常
**Gap**: Agent 生成解释时不查 mastery score，只在 scoring 时注入

| 数据流 | 状态 |
|--------|------|
| 写入 Neo4j EntityNode | ✅ 正常 |
| BKT+FSRS 计算 mastery | ✅ 正常 |
| Agent 查询历史 misconception | ⚠️ 部分工作 |
| **Agent 查询 mastery score** | **❌ 断裂** |
| **结构化历史查询** | **❌ 缺失** |

### 推荐: 两个系统各有最佳用途，不应合并

```
┌─────────────────────────────────────────────┐
│  System 1: Knowledge Retrieval              │
│  LanceDB (向量+全文) + Obsidian CLI (标签+链接)│
│  用途: 检索笔记、教材、历年真题片段             │
└─────────────────────────────────────────────┘
              ↓ (检索到相关材料)
┌─────────────────────────────────────────────┐
│  System 2: Student Model (学习画像)           │
│  Graphiti (时序图谱) + BKT+FSRS (mastery)    │
│  用途: 追踪 misconception、mastery、理解进度   │
└─────────────────────────────────────────────┘
              ↓ (知道学生的薄弱点)
┌─────────────────────────────────────────────┐
│  Agent 生成解释                               │
│  输入: 相关材料 + 学生画像 + 用户问题          │
│  输出: 针对性解释                              │
└─────────────────────────────────────────────┘
```

### 统一架构: Adaptive RAG + 三后端检索

```
┌──────────────────────────────────────────────────────────────┐
│                    Adaptive RAG (StateGraph)                  │
│                    = Agentic RAG 的具体实现                    │
│                    = 用 LangGraph 编排的搜索管道               │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  检索层 (3 个后端，StateGraph 路由)                      │  │
│  │                                                        │  │
│  │  LanceDB        Obsidian CLI      Graphiti             │  │
│  │  (System 1a)    (System 1b)       (System 2)           │  │
│  │  语义+全文      标签+链接+属性     时序学生画像           │  │
│  │  按需查询        按需查询          每次必查              │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  质量控制层                                             │  │
│  │  grade_documents → rewrite_query → grade_generation    │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  生成层                                                │  │
│  │  generate_answer (可复用 Phase 4 React Agent)           │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### 路由引擎根本性问题

**发现**: `agent_routing_engine.py` 的 30 个正则 pattern 路由的是**输出格式**（oral/comparison/memory/...），不是**教学意图**。

- 单节点模式: 前端 6 个按钮直接指定 explanation_type，**无需路由**
- 批量模式: 路由引擎试图从内容猜格式，精度 ~60%
- 真正缺失的路由: misconception_probe / concept_explanation / verification / problem_solving

**结论**: 路由引擎解决的是错误的问题。需要的是意图路由（影响回答内容），不是格式路由。

---

## 八、后端服务审计摘要

- 总服务: 36 (backend) + ~25 (src/agentic_rag) = 61 个模块
- 未使用服务: agent_selector.py, rollback_service.py, context_enrichment_service.py (3个)
- 未启用 Phase: Phase 2 (ENABLE_TOOL_CALLING), Phase 3 (ENABLE_AGENT_GRAPH)
- 14 个布尔 Feature Flags + 13 个运行时配置

---

## 九、后端重构评估

### 当前架构 vs 推荐架构

| 环节 | 当前 | 推荐 | 改动量 |
|------|------|------|:---:|
| 路由 | 正则 30 patterns | Semantic Router | **替换** |
| 焦点 | 无 | 规则+节点链分析 | **新增** |
| 学生模型 | Graphiti 有但未用 | Query→过滤→注入 | **新增管道** |
| Context 过滤 | 全量 dump | Hybrid BM25→Cross-encoder + budget | **新增层** |
| Agent 分发 | 统一 template | 按 intent 分发 | **中度改造** |
| Agent prompt | 无 focal_point | focal_point 优先 | **扩展 schema** |

### 三种重构方案

#### 方案 A: 最小增量 (~250行)
- 在现有 create_react_agent 管道中插入 focal_point 字段
- 用规则做简易 intent 分类
- Context 加 keyword overlap 评分+截断
- **效果**: 解决 ~60% 问题
- **风险**: 低

#### 方案 B: 启用并扩展 Phase 3 StateGraph (~600行改造) ← 推荐
- **启用已有的** `agent_graph.py` StateGraph CRAG 管道
- 在 StateGraph 中新增 3 个节点: `extract_focal_point`, `query_student_model`, `filter_context`
- 用 Semantic Router 替换 `analyze_intent` 节点的 LLM 路由
- Context budget 截断 (3000 chars)
- **效果**: 解决 ~85% 问题
- **风险**: 中（已有 StateGraph 基础，改造量可控）

#### 方案 C: 全面重构 (~2000行)
- 全新 StateGraph 设计（不复用 agent_graph.py）
- Supervisor + 专用 Agent 团队
- BKT 集成到 mastery→context 管道
- Checkpoint 进度追踪
- **效果**: 根本性解决
- **风险**: 高（工作量大，可能引入新 bug）

---

## 十、关键参考资源

### 开源项目

| 项目 | 链接 | 借鉴点 |
|------|------|--------|
| semantic-router | github.com/aurelio-labs/semantic-router | Intent 分类 |
| LangGraph CRAG | langchain-ai/langgraph/examples/rag/ | Relevance grading |
| AITutorAgent | github.com/Ebimsv/AITutorAgent | LangGraph 教育状态机 |
| OATutor | github.com/CAHLR/OATutor | BKT 自适应 |
| pyBKT | github.com/CAHLR/pyBKT | BKT Python 实现 |
| Chiron | NirDiamant/GenAI_Agents | Feynman 学习流 |
| Augmented Canvas | github.com/MetaCorp/obsidian-augmented-canvas | Canvas+AI |
| Chat Stream | github.com/rpggio/obsidian-chat-stream | 节点链上下文 |

### 学术论文

| 论文 | 关键贡献 |
|------|---------|
| HybridRAG (BlackRock+NVIDIA, ACM) | vector+KG联合 faithfulness 0.96 vs 0.91/0.89 |
| KG-RAG (IEEE, n=76) | KG增强RAG教学辅导，评估分数提升35% (p<0.001) |
| LC-RAG (Stanford, 2025) | 用学生交互历史加权检索，验证 Graphiti 模式 |
| Personalization Survey (2025) | "可编辑记忆图谱"作为公认架构 |
| MDPI 2025: RAG + ACP/MCP for Adaptive ITS | Multi-factor relevance 加权公式 |
| ArXiv 2502.15096: Student Intent Detection | 教育场景意图分类体系 |
| ArXiv 2506.07626: Fine-Grained Pedagogical Intent | MathDial 11-point 意图体系 |
| pyBKT (ArXiv 2105.00385) | BKT 变体 + EM 参数拟合 |

### Agentic RAG 社区验证 (2025-2026)

| 维度 | 验证状态 | 关键证据 |
|------|---------|---------|
| 多后端 Agentic RAG | ✅ 生产验证 | HybridRAG ACM 论文, Uber/LinkedIn 部署 |
| CRAG → Adaptive RAG | ✅ 官方推荐 | LangGraph 文档已演进到 Adaptive RAG |
| Graphiti + LangGraph | ✅ 模式存在 | 3-node StateGraph: get_memory→agent→update_memory |
| 教育 KG+RAG | ✅ 最强验证 | KG-RAG 分数提升 35%, LC-RAG 验证历史加权 |
| 双记忆分工 | ✅ 社区推荐 | LangGraph checkpoint(短期) + Graphiti(长期) |
