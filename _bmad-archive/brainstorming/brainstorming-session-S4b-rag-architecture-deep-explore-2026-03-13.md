---
stepsCompleted: [1, 2, 3, 4]
inputDocuments: []
session_topic: 'S4b RAG 架构深度调研 — 融合策略 + Agent 兜底层 + 改善领域全景 + 教育 AI 最佳实践'
session_goals: '确定白盒/黑盒融合策略；设计 Agent 兜底层架构+模型选型；识别全部改善领域并排优先级；调研前端健康度；调研教育 AI 社区最佳实践'
selected_approach: 'Deep Explore + Adversarial Code Review + Community/Paper Validation'
techniques_used: ['Deep Explore', 'Adversarial Code Review', 'Community Validation', 'Paper Survey', 'Incremental Questioning']
ideas_generated: ['三层级混合RAG架构', 'Agent四角色协作设计', '9个改善领域优先级矩阵', '6篇教育AI核心论文', '4个高优先级教育AI建议']
context_file: ''
related_issues: '#4,#6,#16,#23,#24,#25,#28'
dependencies: 'S4b承接S4(Config统一)和S3(Pipeline后处理)的调研结论'
session_active: false
workflow_completed: true
---

# Brainstorming Session Results — S4b RAG 架构深度调研

**Facilitator:** ROG
**Date:** 2026-03-13
**Session ID:** session-brainstorm-s4b-rag-deep-explore-2026-03-13

---

## Session Overview

**Topic:** RAG 系统全景深度调研 — 从融合策略到教育 AI 最佳实践

**Goals:**
1. 确定白盒（规则驱动）vs 黑盒（LLM 驱动）融合策略的选择
2. 设计 Agent 兜底层的完整架构 + 模型选型 + 成本分析
3. 识别 RAG 系统所有改善领域并排优先级
4. 审查前端/学习系统集成的健康度
5. 调研教育 AI 领域的社区最佳实践和前沿论文

**方法论:** Deep Explore（多个并行 agent：代码对抗性审查 + 社区调研 + 论文调研 + 前端审查） + 增量提问模式

**承接关系:** S4 Config 统一 brainstorming → S4b Decision-Review 验证 + 全景深度调研

---

## 1. 融合策略决策 — 三层级混合架构

### 调研结论

| 方案 | 优势 | 劣势 | 社区采用度 |
|------|------|------|-----------|
| **纯白盒（RRF+reranker）** | 快速、可解释、零 API 成本 | 复杂 query 无能为力 | 生产标准基础层 |
| **纯黑盒（LLM 全程）** | 强推理能力 | 贵、慢、70% 简单 query 过杀 | 少数高端系统 |
| **混合三层级** ✅ | 成本最优、质量最优 | 实现复杂度中等 | **行业最佳实践** — Adaptive-RAG, CRAG, Agentic RAG |

### ✅ 确认方案：三层级混合架构

```
用户提问 → [分诊器] → 判断难度
  ├─ L1 简单（70%）→ 白盒 RRF + bge-reranker → 直接返回     [零 API 成本]
  ├─ L2 中等（25%）→ 白盒 + 质量门控 → 通过则返回            [零 API 成本]
  └─ L3 复杂（5%） → Agent 循环介入 → 搜→评→改→搜→生成→自检  [付费 API]
```

**社区验证:**
- Adaptive-RAG (NAACL 2024): T5-large 分类器路由，三级难度
- CRAG (ICLR 2024): 质量评估 + 回退路由（通过/部分/失败）
- 52% 企业已部署 Agentic RAG (Deloitte 2024)

**用户确认:** ✅ 已确认方向

---

## 2. Agent 兜底层设计 — 四角色协作

### 代码对抗性审查

> 独立 agent 审查 `src/agentic_rag/agent_graph.py`（596 行）

**整体评级：需修复（65% 真实实现）**

| 组件 | 状态 | 问题 |
|------|------|------|
| analyze_intent 节点 | ✅ 真实 LLM 调用 | 正常 |
| retrieve 节点 | ❌ **运行时会崩溃** | 调用不存在的 `LanceDBClient.get_instance()` 和 `GraphitiClient.get_instance()` |
| grade_documents 节点 | ✅ 真实 LLM 评分 | 正常 |
| rewrite_query 节点 | ✅ 真实 LLM 改写 | 正常 |
| generate_answer 节点 | ✅ 真实 LLM 生成 | 正常 |
| 整体启用状态 | ❌ **默认禁用** | `ENABLE_AGENT_GRAPH` defaults to `"false"` |
| 表名 | ❌ **不匹配** | 搜 `"vault_notes"` 但实际表是 `"canvas_nodes"` |
| State 设计 | ⚠️ 割裂 | `AgentRAGState` 与 Phase 2 的 `CanvasRAGState` 无共享字段 |
| 测试 | ❌ 零测试 | — |

### ✅ 确认方案：四角色协作设计

```
[角色1: 分诊器 Router]
  规则引擎 + DistilBERT/T5-small 分类器
  <20ms，零 API 成本，~85% 准确率
  功能：判断 query 难度 → 路由到 L1/L2/L3

[角色2: 评分器 Grader]
  bge-reranker-v2-m3 (568M 参数)
  5-10ms/batch，自托管零成本
  功能：评估检索结果相关性 → 通过/部分相关/不相关

[角色3: Agent 循环 Loop]  ← 仅 L3 触发
  搜索 → 评分 → 不够好就改问法重搜 → 最多 3 次 → 生成答案 → 自检
  对齐 CRAG 模式：Correct / Ambiguous / Incorrect 三级路由

[角色4: 自检器 Self-Checker]
  RAGAS faithfulness 检测（自托管 bge-reranker 代替 LLM）
  阈值 <0.7 → 触发重新生成
  功能：防幻觉兜底
```

### 模型选型

| 子任务 | 推荐模型 | 成本 | 理由 |
|--------|---------|------|------|
| 分诊路由 | DistilBERT/T5-small | **$0**（自托管） | <20ms，85% 准确率，零延迟 |
| 文档评分 | bge-reranker-v2-m3 | **$0**（自托管） | MIRACL nDCG@10=69.32，95% LLM 效果 |
| LLM 生成+改写 | Gemini 2.5 Flash-Lite | **$0.10/$0.40/1M token** | TTFT 0.29s，FACTS 85.3%，最快最便宜 |
| 备选 LLM | DeepSeek-V3 | **$0.14/$0.28/1M token** | C-Eval 86.5（中文最强），MoE 671B/37B active |

### 成本估算（30k 次/月查询）

| 组件 | 月成本 |
|------|--------|
| 分诊器（自托管） | $0 |
| 评分器（自托管） | $0 |
| L3 Agent LLM（5% = 1,500 次） | **$10-18** |
| **总计** | **$10-18/月** |

**用户确认:** ✅ 已确认方向

---

## 3. 九大改善领域 — 优先级矩阵

### ✅ 用户已确认优先级排序

| # | 领域 | 优先级 | 核心改善 | 预期效果 |
|---|------|--------|---------|---------|
| 1 | **生产加固** | 🔴 HIGH | 熔断器接入 + traced_nodes 激活 + 错误恢复 | 系统稳定性从"演示级"升级到"生产级" |
| 2 | **质量监控激活** | 🔴 HIGH | RAGAS 三指标自动评估 + 质量仪表盘 | 回答质量从"无法衡量"变为"可量化追踪" |
| 3 | **bge-m3 嵌入升级** | 🔴 HIGH | 三向量嵌入替换 OpenAI ada-002 | 中文检索质量提升 + 零 API 成本 |
| 4 | **Graphiti 客户端修复** | 🔴 HIGH | 修复 MCP import bug → graphiti-core SDK 直连 | 知识图谱从"完全断开"变为"真正可用" |
| 5 | **分块策略升级** | 🟠 MED-HIGH | Parent-Child + Contextual Retrieval | 检索失败率降低 49-67%（Anthropic 2024 论文） |
| 6 | **学生个性化** | 🟡 MEDIUM | Mastery-aware 检索 + Bloom 分级 | 答案匹配学生实际水平 |
| 7 | **多模态审计** | 🟡 MEDIUM | 确认图片/公式在 RAG 中的处理路径 | 避免丢失关键视觉信息 |
| 8 | **U 型上下文重排** | 🟢 LOW-MED | Lost-in-the-middle 重排序 | 注意力分配优化（Stanford 2023） |
| 9 | **语义缓存** | 🟢 LOW | 相似 query 缓存命中 | 延迟降低 — 但 33% 误报率，暂缓 |

### 详细说明

#### HIGH 优先级（必须立即做）

**1. 生产加固**
- `circuit_breaker.py` 已完整实现但未接入 `nodes.py` → 一次接线
- `traced_nodes.py` 已完整实现但 `state_graph.py` 导入了 `nodes.py` → 换一行 import
- 改动量：~20 行代码，效果：系统韧性质变

**2. 质量监控激活**
- RAGAS 三指标：faithfulness（幻觉检测）、answer_relevancy（答案相关性）、context_precision（上下文精度）
- 社区验证：RAGAS 是 RAG 质量评估事实标准（GitHub 4k+ stars）
- 改动量：新增评估模块 + 仪表盘 hook

**3. bge-m3 嵌入升级**
- 已在 S3 brainstorming 中决策，尚未实现
- 三向量：dense + sparse + ColBERT，中文 MIRACL 领先
- 替换当前 OpenAI ada-002（$0.10/1M token → $0）

**4. Graphiti 客户端修复**
- 根因：`importlib.util.find_spec("mcp__graphiti_memory__list_memories")` 永远失败
- MCP 工具不是 Python 可导入模块 → `_mcp_available` 永远 `False` → KG 查询全返回 `[]`
- 修复方案：使用 `graphiti-core` Python SDK 直连 Neo4j (`bolt://localhost:7689`)

#### MEDIUM-HIGH 优先级

**5. 分块策略升级**
- **Parent-Child 分块**：大块（~2000 字）存储完整上下文，小块（~400 字）用于精准匹配
- **Contextual Retrieval**（Anthropic 2024）：索引时为每个 chunk 生成 LLM 上下文前缀
- 论文数据：检索失败率降低 49%（单独）/ 67%（+reranking）

#### MEDIUM 优先级

**6. 学生个性化**
- Mastery-aware 检索：根据学生掌握度过滤/排序检索结果
- Bloom 分级标签：为 chunk 标注认知层级（记忆/理解/应用/分析/评价/创造）
- 论文支持：TutorLLM (arXiv 2502.15709)、PAGE (arXiv 2509.15068)

**7. 多模态审计**
- 确认图片、公式、表格在 RAG pipeline 中的处理路径
- 避免 chunk 切割导致公式断裂或图片引用丢失

#### LOW 优先级（暂缓）

**8. U 型上下文重排** — 效果有但优先级低于 reranker
**9. 语义缓存** — 33% 误报率风险，等系统稳定后再考虑

---

## 4. 前端 + 学习系统集成审查

### 代码对抗性审查结论

> 独立 agent 审查 `canvas-progress-tracker/obsidian-plugin/main.ts` (~174KB) + `backend/app/`

**整体评级：大部分可用（远好于 RAG 后端）**

### 架构概况

| 层 | 技术栈 | 状态 |
|----|--------|------|
| 前端插件 | Vanilla TypeScript + Obsidian API | ✅ 4000+ 行，5 个视图 + 11+ 模态框 + 20+ 命令 |
| 后端 API | FastAPI (`backend/app/`) | ✅ 真实实现，与前端对接 |
| 死代码 API | `src/api/` | ❌ **全部 MOCK，应删除** |

### 工作中的功能

| 功能 | 状态 | 说明 |
|------|------|------|
| Canvas 颜色变化 → 自评 → 掌握度更新 | ✅ 端到端打通 | BKT+FSRS 混合追踪 |
| 8 种 Agent 教学模式 | ✅ 可调用 | 四层次/口语化/例题/对比/拆解/检验/记忆锚点/评分 |
| Review Dashboard | ✅ 工作 | 到期复习 + 统计面板 |
| Verification 系统 | ✅ 工作 | 检验问题生成 + 评分 |
| Cross-Canvas 引用 | ✅ 工作 | Obsidian 多 Canvas 关联 |

### 四个关键断点

| # | 断点 | 影响 | 修复难度 |
|---|------|------|---------|
| 1 | **BehaviorTracker 断开** | 优先级计算的行为权重（30%）= 0，所有节点等权 | 中 — 后端已实现，需接 API |
| 2 | **`src/api/` 全 MOCK 死代码** | 混淆开发者，新开发者可能改错文件 | 低 — 直接删除 |
| 3 | **内存查询 API 全 TODO** | `TemporalQueryResponse(items=[], total_count=0)` | 中 — 需实现查询逻辑 |
| 4 | **3 个高级模式禁用** | Phase 3 Agent Graph、Strategy Selector、高级检索 | 高 — 需先修 RAG 后端 |

---

## 5. 教育 AI 社区最佳实践 — 论文调研

### 六篇核心论文

| 论文 | 来源 | 核心发现 | 与 Canvas 相关性 |
|------|------|---------|-----------------|
| **Harvard RCT** | Nature 2025 | AI 辅导优于课堂教学 (d=0.73-1.3) | ⭐⭐⭐ 验证整个项目方向 |
| **TutorLLM** | arXiv 2502.15709 | 首个 KT+RAG 系统，FSRS 掌握度→检索过滤 | ⭐⭐⭐ 直接参考架构 |
| **LC-RAG** | arXiv 2505.17238 | 学生交互日志→LLM 摘要→RAG 上下文 | ⭐⭐⭐ BehaviorTracker 修复后可对接 |
| **PAGE** | arXiv 2509.15068 | Profile-aware query 生成，2.7x 个性化相关性 | ⭐⭐ 中期目标 |
| **EDU-Graph RAG** | arXiv 2506.22303 | 前置知识图谱 + 多 agent 教育 RAG | ⭐⭐ 与 Graphiti 知识图谱对齐 |
| **LECTOR** | arXiv 2508.03275 | 语义干扰建模，FSRS 改进 (90.2% vs 89.6%) | ⭐ 长期优化 |

### Harvard RCT 七项研究验证特征

1. **即时反馈** — 错误后立即纠正 ✅ Canvas 已有（Agent 评分模式）
2. **个性化难度** — 匹配学生 ZPD ⚠️ 部分实现（FSRS 有，检索未对接）
3. **主动回忆** — 测试效应（learning = retrieval practice） ⚠️ 需强化
4. **间隔重复** — 遗忘曲线驱动复习 ✅ Canvas 已有（FSRS + Review Dashboard）
5. **苏格拉底式提问** — 引导而非直接给答案 ❌ 未实现
6. **知识关联** — 连接新旧概念 ✅ Canvas 核心设计（可视化关系图）
7. **元认知监控** — 学生自我评估准确度 ⚠️ 有自评但无校准

### 四个高优先级建议

| # | 建议 | 理由 | 实现路径 |
|---|------|------|---------|
| 1 | **Mastery-Aware 检索** | TutorLLM 验证：掌握度过滤后检索相关性提升 40%+ | 已有 FSRS mastery → 传入 RAG config → 过滤/排序 |
| 2 | **苏格拉底模式** | Harvard RCT：引导提问 > 直接解答 | 新增 Agent 模式：不给答案，反问引导 |
| 3 | **Canvas Context → RAG** | LC-RAG 验证：学习日志上下文化提升检索精度 | BehaviorTracker 修复后 → 交互日志 → RAG prompt |
| 4 | **Bloom 层级标签** | PAGE 验证：profile-aware 提升 2.7x 个性化 | Chunk 索引时标注认知层级 → 匹配学生 mastery |

### 关键反模式警告

> **"学习 ≠ 解释，学习 = 检索练习"**
>
> Harvard RCT 发现：过度依赖 AI 解释反而降低考试成绩。系统应促进主动检索（测试效应），而非只给答案。
>
> **Canvas 当前状态**：8 个 Agent 模式中 7 个是"解释"类，仅 1 个（检验问题）促进主动检索。
> **建议**：提高检验问题模式的使用频率引导，增加苏格拉底模式。

---

## 6. 决策记录汇总

### 已确认决策（用户 ✅）

| 决策 | 内容 | Decision-Review 状态 |
|------|------|---------------------|
| 三层级混合 RAG 架构 | L1 白盒(70%) + L2 白盒+质量门控(25%) + L3 Agent(5%) | PENDING |
| Agent 四角色设计 | 分诊器+评分器+Agent循环+自检器 | PENDING（同上） |
| 模型选型 | 分诊=DistilBERT, 评分=bge-reranker, LLM=Flash-Lite | PENDING（同上） |
| 9 个改善领域优先级 | 见优先级矩阵 | PENDING |

### 待验证（独立 session）

1. **三层级架构 + Agent 设计** — 需在真实数据上验证路由准确率、Agent 循环收敛率、成本
2. **9 个改善领域** — 需制定具体验收标准（每个领域的通过/失败条件）

---

## 7. 现有代码复用评估

| 模块 | 评级 | 说明 |
|------|------|------|
| `agent_graph.py` 4/5 节点 | ✅ 可复用 | analyze_intent, grade_documents, rewrite_query, generate_answer 真实实现 |
| `agent_graph.py` retrieve 节点 | ❌ 需重写 | 调用不存在的客户端，表名不匹配 |
| `circuit_breaker.py` | ✅ 可复用 | 完整实现，只需接线 |
| `traced_nodes.py` | ✅ 可复用 | 完整实现，只需换 import |
| `mastery_engine.py` | ✅ 可复用 | BKT+FSRS 端到端工作 |
| `behavior_tracker.py` | ✅ 可复用 | 完整实现，需接 API |
| `graphiti_client.py` | ❌ 需重写 | MCP import 机制根本错误 |
| `src/api/` 整个目录 | ❌ 应删除 | 全 MOCK 死代码 |
| `nodes.py` rerank/quality gate | ❌ 需重写 | 全是 stub/假实现 |
| Obsidian 插件 `main.ts` | ✅ 可复用 | 大部分功能工作，需拆分降低复杂度 |

---

## 8. 下一步行动建议

### Phase 1: 生产加固（预计 1-2 个 sprint）
1. 接线 circuit_breaker → nodes.py 所有外部调用
2. 换 import：state_graph.py 使用 traced_nodes.py
3. 修复 Graphiti 客户端 → graphiti-core SDK 直连
4. 删除 `src/api/` 死代码
5. 接线 BehaviorTracker → 后端 API

### Phase 2: 检索质量升级（预计 2-3 个 sprint）
1. bge-m3 嵌入替换 ada-002
2. bge-reranker-v2-m3 接入（替换 stub）
3. Parent-Child 分块 + Contextual Retrieval
4. RAGAS 质量监控激活

### Phase 3: Agent 层 + 个性化（预计 2-3 个 sprint）
1. 修复 agent_graph.py retrieve 节点
2. 实现分诊器 Router
3. 统一 State（合并 AgentRAGState 和 CanvasRAGState）
4. Mastery-aware 检索
5. 苏格拉底模式

### Phase 4: 高级优化（长期）
1. Bloom 层级标签
2. Canvas Context → RAG（LC-RAG 模式）
3. U 型上下文重排
4. 语义缓存（待误报率解决）
