---
stepsCompleted: [1, 2, 3, 4]
inputDocuments: []
session_topic: 'A3验证策略重设计 — 基于深度探索发现大量功能未实施的前提下'
session_goals: '发现验证策略盲点、重设计验证方法论、确保策略与代码实际状态匹配'
selected_approach: 'ai-recommended'
techniques_used: ['question-storming', 'reverse-brainstorming', 'chaos-engineering']
ideas_generated: ['gate-based-validation', 'walking-skeleton', 'failure-path-observability', 'test-data-isolation', 'contract-testing', 'resilience-patterns']
context_file: ''
technique_execution_complete: true
session_active: false
workflow_completed: true
---

# Brainstorming Session Results

**Facilitator:** ROG
**Date:** 2026-03-14

## Session Overview

**Topic:** A3 四方向验证策略重设计 — 基于四路深度探索的新发现
**Goals:**
- 发现当前 14 项验收标准的盲点和遗漏
- 重设计验证方法论以匹配代码实际状态（大量功能未实施）
- 确保验证策略覆盖系统性风险（静默错误吞噬、基础设施断裂、无评估框架）

### Context Guidance

_四路深度探索关键发现：_
1. 代码审查：A3 四方向中多数功能未实施（frontmatter 解析不存在、progressive scope 不存在、cross_canvas_router 未注册、reranker 是 no-op）
2. 社区调研：7 个遗漏维度（LanceDB Bug #2439、8 种 wikilink 边界、Golden dataset 方法论等）
3. Graphiti 挖掘：3 大系统性盲点（错误静默吞噬、基础设施断裂连锁、无评估框架）
4. 文档交叉：A3 在 Phase 2A（依赖 Phase 0+1），S9 发现 9 个 P0 indexing bug 需先修

### Session Setup

_Session 主题从"验证已实施功能的质量"调整为"在大量功能未实施的前提下，重新设计验证策略"_

## Technique Selection

**Approach:** AI-Recommended Techniques
**Analysis Context:** 验证策略重设计（策略审查型任务）

**Recommended Techniques:**

- **Question Storming（提问风暴）:** 穷举"应问但没问的问题"，暴露隐藏假设
- **Reverse Brainstorming（反向风暴）:** "如何让验证给出假的 PASS"，找出所有可能溜过 bug 的路径
- **Chaos Engineering（混沌工程）:** 注入极端情况压力测试验证策略

**AI Rationale:** 三层递进（找盲点→找漏洞→压力测试），确保验证策略本身可靠

## Technique Execution Results

### Phase 1: 提问风暴（Question Storming）

**产出：60+ 高质量问题**，经两轮深度探索（7 路并行 agent）

**关键发现主题：**

**A 类 — 前提假设崩塌：**
- 14 项 AC 假设功能已实施，但代码审查显示大量功能不存在
- A3 的 6 个上游依赖只有 1/6 就绪（chunking），4/6 未就绪
- bge-m3 未切换（仍用 MiniLM），验收标准基于错误模型制定

**B 类 — 依赖链和执行顺序：**
- 五层验证优先级已定义但未执行
- S4 Config 统一、S2 hybrid search 激活均未完成
- Contextual Retrieval 归属不清（A1 还是 A3）

**C 类 — "成功的假象"：**
- 代码库系统性 try/except 错误吞噬
- Reranker 是 no-op，FTS 索引存在但从未使用
- Index 无去重（纯 append），指标失真

**D 类 — 方法论缺失：**
- 无 Walking Skeleton 验证基本管道能否走通
- 无 Smoke Test 层
- 无 Golden Query Set 和回归基线

---

### Phase 2: 反向风暴（Reverse Brainstorming）

**产出：55 个假 PASS 攻击路径**，经两轮深度探索

**代码级攻击面（31 个）：**

| 严重度 | 数量 | 代表性攻击 |
|--------|------|----------|
| CRITICAL | 5 | stub/passthrough 伪装为真实实现 |
| HIGH | 10 | 静默 `return []` 无错误信号 |
| MEDIUM | 10 | 异常吞噬后继续执行 |
| LOW | 6 | 装饰性安全机制（如 RetryPolicy 从不触发） |

**Top 5 最危险：**
1. Pipeline 全部 retriever 返回空但正常完成
2. Reranker passthrough stub
3. LanceDB 初始化失败级联（`_initialized=True` 但 `_db=None`）
4. Broken Singleton 永久缓存 `Service(None)`
5. TODO stub 伪装正常运行（cross-canvas + textbook）

**社区调研攻击面（18 个）：**

| 严重度 | 攻击路径 |
|--------|---------|
| CRITICAL | Happy Path 测试集（只测简单查询） |
| CRITICAL | 测试查询-源文档泄漏（同源匹配） |
| CRITICAL | LLM 预训练记忆绕过 RAG |
| CRITICAL | 阈值调参过拟合（Goodhart's Law） |
| HIGH | 聚合分数粉饰、自我评判循环、Recall@K 膨胀 |

---

### Phase 3: 混沌工程（Chaos Engineering）

**产出：25 个多故障叠加极端场景**，经两轮深度探索

**代码级联传播链（5 条）：**

| 级联 | 传播路径 | 最终影响 |
|------|---------|---------|
| 初始化级联 | `initialize()` 失败 → `_db=None` → 5 个 singleton 全坏 | 5/6 检索路永久失效 |
| Config 定时炸弹 | 3 处模型声明碰巧相同 → 任何改动引爆 | 向量空间污染不报错 |
| FTS 空转 | FTS 索引创建但 hybrid 从未触发 | 功能空转 |
| Rewrite 死循环 | stub rewriter → 3 轮 18 次无效检索 | 6 秒浪费零增益 |
| 竞态覆盖 | 并发初始化 → 成功被失败覆盖 | 永久坏 singleton |

**最危险三重组合：** 初始化级联 + Rewrite 死循环 + 竞态覆盖 = 启动时永久缓存坏 singleton → 3 轮无效检索 → 零结果无日志

**社区生产级场景（14 个，P0 标注）：**
- Hub Note 爆炸（40+ 邻居无限制）— P0
- 三层渐进 Thundering Herd — P0
- 指标全绿但答案错误（可观测性盲区）— P0
- 幽灵文档（并发写入数据不一致）— P0
- 索引写入阻塞查询 — P0

---

## Idea Organization and Prioritization

### 五大主题整理

**主题 1: 分层门禁（Gate-based Validation）— 替代扁平 AC 列表**

核心洞察：当前 14 项 AC 全是"验收级"测试，但系统基础管道都不工作时跑验收测试毫无意义。

**重设计方案：**

```
Gate 0: Smoke Test（系统活着吗？）
  ├─ 发送查询，得到非空响应
  ├─ 响应包含真实 vault 内容（非 mock）
  ├─ 相似度分数非零且非均匀
  ├─ Reranker 改变了结果顺序（非 no-op）
  └─ Cross-canvas router 已注册且响应

Gate 1: Component Test（零件能单独工作吗？）
  ├─ Frontmatter parser 正确解析 YAML
  ├─ Wikilink parser 处理 8 种边界情况
  ├─ Progressive scope 模块可调用
  └─ LanceDB WHERE 过滤无注入

Gate 2: Integration Test（零件连在一起能工作吗？）
  ├─ Frontmatter metadata 流入 LanceDB 索引
  ├─ Wikilink 数据可被检索层查询
  ├─ Scope 过滤端到端生效
  └─ Cross-canvas 路由连通 RAG retriever

Gate 3: Acceptance Test（原 14 项 AC，仅在 Gate 0-2 全通过后执行）
```

**优先级：最高** — 这是整个验证策略的骨架

---

**主题 2: 失败路径可观测性 — 消灭"假 PASS"**

核心洞察：代码库有 31 个静默失败点，任何 AC 只检查"有结果"而不检查"数据源健康"都会被骗过。

**重设计方案：**

| 防御层 | 措施 | 覆盖的假 PASS |
|--------|------|-------------|
| **Source Health Assert** | 每个 AC 必须检查 `retrieval_error == None` + `len(results) > 0` for each source | #1-#2, #8-#14 |
| **Init Health Check** | 测试前验证 `client._db is not None` + `_vectorizer is not None` | #8-#12 |
| **Stub Detection** | 断言 reranker 修改了顺序、cross-canvas 结果来自不同 canvas | #3, #29-#30 |
| **Quality Termination** | 最终 `quality_grade` 不能是 "low" | #15-#16 |
| **Known-Data Anchor** | 预索引特定内容，断言它出现在结果中 | #10-#11 |

**优先级：最高** — 没有这层防御，所有 AC 都可能被静默失败骗过

---

**主题 3: 测试数据工程 — 消灭数据泄漏和 gaming**

核心洞察：测试查询从源文档提取 = 数据泄漏；LLM 预训练记忆 CS188 = 绕过 RAG；只测简单查询 = happy path。

**重设计方案：**

| 防御 | 具体措施 |
|------|---------|
| **物理隔离** | ≥50% 测试查询来自人工撰写或凭记忆复述，禁止从 chunk 直接改写 |
| **RAG 断开对照** | 每个查询先无 context 让 LLM 回答，能答对的查询对 RAG 验证无效 |
| **困难查询 ≥30%** | 歧义、否定、跨概念、口语化表述 |
| **Train/Test 分离** | 50 查询分 30 标定 + 20 验证，阈值不可全集调 |
| **多次运行取最差** | 涉及 embedding 的 AC 至少 3 次，取 worst-case |
| **禁止纯 LLM 评判** | 必须有人工 ground truth，LLM 仅辅助 |

**优先级：高** — 没有好的测试数据，所有 AC 结果都不可信

---

**主题 4: 依赖就绪检查（Definition of Ready）— 验证前的前置条件**

核心洞察：A3 的 6 个上游依赖只有 1/6 就绪。在依赖未就绪时执行验证产出不可靠结果需丢弃重做。

**DoR 检查清单：**

| # | 前置条件 | 当前状态 | 阻塞的 AC |
|---|---------|---------|----------|
| 1 | Embedding model 统一为 bge-m3 | ❌ 未切换 | AC-S5-01/02 |
| 2 | Config 统一（消除 4 套冲突） | ❌ 未完成 | 全部（不可复现） |
| 3 | Index 去重逻辑 | ❌ 纯 append | AC-S5-06/11 |
| 4 | Hybrid search 接入主管线 | ❌ 默认 vector-only | AC-S5-11 |
| 5 | Reranker 激活（非 no-op） | ❌ placeholder | 全部 reranking 相关 |
| 6 | Cross-canvas router 注册 | ❌ 未注册 | AC-S5-10/12/13 |
| 7 | S9 的 9 个 P0 indexing bug 修复 | ❓ 未确认 | AC-S5-14 |

**规则：DoR 检查不通过 → 禁止执行 Gate 3 AC → 只允许执行 Gate 0 Smoke Test**

**优先级：高** — 决定了 AC 何时可以开始执行

---

**主题 5: 韧性防护 — 防止级联故障和极端场景**

核心洞察：初始化级联可毁掉 5/6 检索路径；竞态可永久缓存坏 singleton；hub note 可导致 context 溢出。

**韧性措施：**

| 防护 | 措施 | 覆盖的炸弹 |
|------|------|----------|
| **Init 不缓存失败** | `initialize()` 失败不设 `_initialized=True` | 级联 #1 |
| **asyncio.Lock 保护 singleton** | 防止竞态覆盖 | 级联 #5 |
| **Hub Node 限制器** | `max_neighbors=5` + hub 检测（链接>20） | 社区 #4 |
| **Scope Circuit Breaker** | 三层渐进展开有并发控制 | 社区 #7 |
| **数据一致性验证** | 索引后验证 metadata+向量+文本三者一致 | 社区 #12 |
| **Embedding 版本固定** | 记录模型版本+checkpoint hash | 社区 #1/#9 |

**优先级：中** — 实施阶段需要同步建设，不阻塞验证策略本身

---

### 突破性概念

1. **Walking Skeleton 前置验证** — 在任何 AC 之前，先验证 "query→embed→search→return top-1" 这条最小路径能走通。如果 skeleton 不能走，一切免谈。

2. **Contract Testing 替代 Mock 检测** — 定义模块间接口契约，自动检测 no-op/空返回/stub 实现。比人工审查可持续。

3. **30 天回归机制** — 验收不是终点。30 天后用同一测试集重新验收，退化>5% 触发告警。

---

## Action Plan

### 立即可执行（本周）

1. **创建 Gate 0 Smoke Test**（~2 小时）
   - 5 个最小化测试验证管道存活性
   - 不依赖任何 A3 功能，测试当前系统基线

2. **创建 DoR 检查清单脚本**（~1 小时）
   - 自动检查 7 项前置条件
   - 输出"N/7 就绪，阻塞 AC: [列表]"

3. **创建 Golden Query Set v0**（~3 小时）
   - 20-30 个人工撰写的 CS188 查询
   - 包含 30% 困难查询
   - 附手工标注的期望文档 ID

### 实施阶段同步建设

4. **Gate 1-2 测试框架**（随各功能实施）
5. **Contract Test 定义**（模块接口确定后）
6. **韧性防护措施**（代码修改时同步加入）

### 实施后执行

7. **Gate 3 验收测试**（全部 DoR 通过后）
8. **30 天回归首轮**（验收后 30 天）

---

## Session Summary and Insights

**Session 成就：**
- **140+ 发现项**（60+ 问题 + 55 假 PASS + 25 极端场景）
- **颠覆性发现**：验证策略的前提假设不成立（大量功能未实施）
- **系统性问题**：代码库有 31 个静默失败点，几乎每个模块都有 `except Exception: return []`
- **可执行方案**：分层门禁 + 失败路径可观测性 + 测试数据工程 + DoR + 韧性防护

**关键教训：**
- 验证策略本身需要被验证——"谁来验证验证者"
- 代码存在不等于功能打通——函数签名存在 ≠ 管道连通
- 静默失败是最危险的失败——系统"看起来正常"比"崩溃"更难发现
- 测试数据质量 > 测试数量——20 个泄漏的查询不如 5 个物理隔离的查询

**深度探索统计：**
- 总计启动 **12 个并行 agent**（7 路 Phase 1 + 2 路 Phase 2 + 3 路 Phase 3 探索）
- 覆盖：社区调研 × 3 轮 + 代码审查 × 4 轮 + Graphiti 搜索 × 2 轮 + 文档分析 × 1 轮
- 社区来源：RAGAS, DeepEval, TruLens, ECIR 2026, Netflix FIT, Pact, obsidiantools, LanceDB issues 等

### Creative Facilitation Narrative

_本次 brainstorming 从"优化验证策略"出发，在第一轮深度探索中发现了颠覆性事实——大量功能尚未实施。这一发现彻底改变了 session 方向，从"优化已有方案"转为"重新设计验证策略"。三阶段技法（提问风暴→反向风暴→混沌工程）形成了递进式的发现过程：先找到不知道自己不知道的问题，再系统性地攻击验证策略的漏洞，最后在极端场景下压力测试。每一轮深度探索都产出了超出预期的发现，最终 140+ 发现项远超目标。_
