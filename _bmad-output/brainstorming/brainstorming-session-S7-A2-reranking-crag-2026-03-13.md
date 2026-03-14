---
stepsCompleted: [1, 2, 3, 4]
inputDocuments: ['session-prompts-memory-system-1.md', 'brainstorming-session-S4b-rag-architecture-deep-explore-2026-03-13.md']
session_topic: 'S7-A2 检索结果组织 + Reranking + Phase 迁移 + CRAG 闭环'
session_goals: '设计从暴力拼接15K token到精准检索+质量门控的完整迁移方案'
selected_approach: 'AI-Recommended: 约束地图→形态分析→反向风暴'
techniques_used: ['Constraint Mapping', 'Morphological Analysis', 'Reverse Brainstorming', 'Deep Explore', 'Adversarial Code Review', 'Community/Paper Validation']
ideas_generated: ['三批9项实施方案', '5个Prompt模板设计', '3项教育专项改善', '5项部署陷阱防护', '3项跨session冲突解决']
context_file: ''
related_issues: 'A1依赖, S3 pipeline, S4 Config统一, Session C 验收'
dependencies: 'S7-A2承接S4b(RAG深度调研)和session-prompts-memory-system-1(A2定义)'
session_active: false
workflow_completed: true
---

# Brainstorming Session Results — S7-A2 检索结果组织 + Reranking + CRAG 闭环

**Facilitator:** ROG
**Date:** 2026-03-13
**Session ID:** session-brainstorm-s7-a2-reranking-crag-2026-03-13

---

## Session Overview

**Topic:** Canvas Learning System 的"检索结果组织 + Reranking + Phase 迁移 + CRAG 质量闭环"全面 brainstorming

**Goals:**
1. 设计 5 大任务块的完整实施方案
2. 通过代码对抗性审查确认可复用/需重写的代码
3. 调研社区最佳实践和教育 RAG 专项适配
4. 设计 5 个 Prompt 模板
5. 解决跨 session 冲突

**方法论:** AI 推荐三阶段技法（约束地图→形态分析→反向风暴）+ Deep Explore（多个并行 agent：代码审查 + 社区调研 + 教育 RAG + 补充查漏）

**承接关系:** S4b RAG 深度调研 → S7-A2 具体实施方案设计

---

## 1. 代码对抗性审查 — A2 涉及模块真实状态

> 独立 agent 审查 nodes.py、fusion/、state_graph.py、agent_graph.py、agent_service.py

### LIVE 管道数据流真相

```
用户提问 → 6源并行检索 → inline RRF 融合 → Reranking(❌ 空壳) → 质量检查(⚠️ 评估未排序分数) → 重写(❌ 空壳) → 暴力拼接上下文
```

### 各模块评级

| 模块 | 评级 | 关键发现 |
|------|------|---------|
| **Reranking** (`nodes.py:673-696`) | ❌ 0% 纯 stub | `_rerank_local()` 和 `_rerank_cohere()` 直接 `return results`，每次查询 reranking 都是 no-op |
| **结果融合** (`nodes.py` inline + `fusion/`) | ⚠️ 双实现冲突 | `nodes.py` 有 inline 6 源 RRF（活跃），`fusion/` 有正式 2 源实现（死代码），默认权重数值不一致 |
| **质量门控** (`nodes.py` check_quality) | ⚠️ 半废 | `check_quality()` 真实实现，但评分的数据未经 reranking；`rewrite_query` 只 prepend "请详细解释:" |
| **上下文组装** (`agent_service.py`) | ❌ 暴力拼接 | 无 token 预算、无压缩、无摘要、无排序 |
| **CRAG 闭环** (`agent_graph.py`) | ✅ 存在但禁用 | grade_documents + CRAG 路由 + query rewrite 都是真实 LLM 实现，`ENABLE_AGENT_GRAPH=false` |
| **融合模块** (`fusion/` 6 文件) | ✅ 算法正确 | unified_result, rrf_fusion, weighted_fusion, cascade_retrieval, strategy_selector, evaluator 全部可用，只需扩展到 6 源 |

### Config 权重分歧

```
nodes.py:    graphiti=0.20, lancedb=0.20, textbook=0.15, cross_canvas=0.10, multimodal=0.15, vault_notes=0.20 (6源)
config.py:   graphiti=0.25, lancedb=0.25, textbook=0.20, cross_canvas=0.15, multimodal=0.15 (5源，无vault_notes)
```

---

## 2. 社区+论文调研 — 5 主题成熟方案

### 2.1 Reranking 最佳实践

| 维度 | 社区共识 | 来源 |
|------|---------|------|
| **模型** | bge-reranker-v2-m3（278M 参数，中英文最佳开源 reranker） | HuggingFace BAAI |
| **范式** | 两阶段：bi-encoder 召回 20-30 → cross-encoder 精排 → top-5 | Pinecone, Databricks |
| **截断** | 优先 top-K 截断而非绝对分数阈值 | HuggingFace 社区讨论 |
| **效果** | +33% 准确率，+120ms 延迟 | Pinecone 研究 |
| **normalize** | `normalize=True`（sigmoid 归一化到 [0,1]） | bge-reranker 文档 |

### 2.2 CRAG 质量闭环

| 维度 | 社区共识 | 来源 |
|------|---------|------|
| **分类** | 三元：Correct / Incorrect / Ambiguous | CRAG 论文 (ICLR 2024) |
| **评分器** | LLM-as-judge（社区简化版，替代 T5-large 微调） | DataCamp, LangChain |
| **循环上限** | 最多 2-3 次 rewrite | 社区共识 |
| **Canvas 适配** | 禁止 web fallback（个人笔记优先），超限降级为"信息不足" | 教育场景定制 |
| **小知识库** | ~120 文件简化为二级路由（去掉 AMBIGUOUS web search） | 补充调研发现 |

### 2.3 上下文压缩 (15K → 3K)

| 维度 | 社区共识 | 来源 |
|------|---------|------|
| **推荐方案** | 三阶段：信号提取（top-5 各取关键句）→ 证据排列（首尾放最相关）→ 约束模板 | RECOMP (ICLR 2024), Stanford Lost-in-the-Middle |
| **不用 LongLLMLingua** | 教育笔记结构化程度高，提取式压缩足够 | 性价比分析 |
| **公式/代码** | 跳过压缩，完整保留 | ACC-RAG (EMNLP 2025) |
| **自适应压缩** | 简单查询多压缩，复杂查询少压缩 | EXIT (ACL 2025) |

### 2.4 多源融合权重

| 维度 | 社区共识 | 来源 |
|------|---------|------|
| **RRF k 值** | k=60 起步，后续根据评估数据微调 | Cormack et al. 2009 |
| **Weighted RRF** | 比无权重版 +6.4% nDCG@10 | HF-RAG 论文 |
| **动态权重** | query 类型分类器可达 nDCG 0.75→0.82 | Adaptive-RAG |

### 2.5 Phase 迁移

| 维度 | 社区共识 | 来源 |
|------|---------|------|
| **策略** | 渐进式迁移（先包装后重构） | LangChain 官方 |
| **LangGraph** | 已达 1.0 稳定版，API 稳定 | LangChain Blog |
| **循环防护** | state 中 retry_count + recursion_limit=10 | LangGraph 文档 |

---

## 3. 教育 RAG 专项调研 — 12+ 篇论文

### 3.1 Mastery-Aware Reranking

- 文献中 mastery **未**作为 reranking 信号，而是作为**生成阶段** prompt 上下文（TutorLLM +10% 满意度）
- **推荐**：标准 cross-encoder reranking 处理相关性 → rerank 后叠加 mastery 教学过滤器（gap-aware：boost 低掌握度 chunks）

### 3.2 教育 CRAG 适配

| 标准 CRAG | 教育适配 |
|-----------|---------|
| Correct 阈值 ~0.7 | 提高到 ~0.85（教育零容忍幻觉） |
| Incorrect → web search | Incorrect → "笔记中没有足够信息" |
| 单一质量检查 | 8 种 agent 模式可设不同 faithfulness 标准 |

### 3.3 教育上下文三层组装

```
Layer 1: 事实知识层（检索到的 chunks）— ground truth
Layer 2: 学生状态层（BKT+FSRS mastery + 交互历史 + 知识缺口）
Layer 3: 教学框架层（agent 模式 + Bloom 目标 + 脚手架深度）
```

### 3.4 新发现的 3 项改善点

| 改善点 | 论文来源 | 优先级 |
|--------|---------|--------|
| 学生查询上下文化（检索前注入主题+mastery+mode） | LC-RAG (Stanford) | 立即做 |
| 先修知识检测（mastery<0.5 补先修摘要） | KA-RAG (MDPI 2025) | 中期 |
| 模式专属质量标准 | MCP+ACP (MDPI 2025) | 中期 |

### 核心论文清单

| 论文 | 来源 | 核心发现 |
|------|------|---------|
| TutorLLM | arXiv 2502.15709 | KT+RAG 组合，mastery→prompt 上下文 |
| LC-RAG | arXiv 2505.17238 | 交互日志上下文化检索 |
| PAGE | arXiv 2509.15068 | Profile-aware，2.7x 个性化 |
| RankRAG | NeurIPS 2024 | 统一 rerank+generate |
| MIND-RAG | ICCV 2025 | 多模态教育 RAG |
| Adaptive Scaffolding | arXiv 2508.01503 | ZPD 估计 + 自适应脚手架 |
| CRAG | ICLR 2024 | 三级置信度路由 |
| RECOMP | ICLR 2024 | 提取式上下文压缩 |
| ACC-RAG | EMNLP 2025 | 自适应压缩率 |
| EXIT | ACL 2025 | 上下文感知提取式压缩 |

---

## 4. 确认方案 — 三批九项实施计划

### ✅ 用户已确认

**第 1 批（核心）：**
1. Reranking 重写 — bge-reranker-v2-m3 接入，lazy singleton + asyncio.to_thread + fp16
2. CRAG 激活 — grade_documents + 二级路由 + 阈值 0.85 + 禁 web fallback + 2 次循环
3. 融合统一 — 扩展 fusion/ 到 6 源 + nodes.py 改为调用 fusion/ + 修 config 权重分歧
4. Mastery-as-context — 提前到第一批末尾（轻量：prompt 加一行 mastery 信息）

**第 2 批（上下文）：**
5. 上下文压缩 — 三阶段组装 + token 预算（15K→3K）
6. 学生查询上下文化 — 检索前 query 改写（注入主题+mastery+mode）
7. Mastery 教学过滤层 — rerank 后 gap-aware 过滤

**第 3 批（迁移+高级）：**
8. Phase 迁移 — 渐进式 LangGraph StateGraph
9. 先修知识检测 + 模式专属质量标准

---

## 5. 补充调研 — 部署陷阱与可观测性

### 必须关注（5 项）

| # | 发现 | 行动 |
|---|------|------|
| 1 | bge-m3 + bge-reranker 同时加载仅需 ~1.8GB VRAM，RTX 4060 够用 | 确认为架构基准 |
| 2 | 启动时必须做 warmup 推理（首次慢 2-5x） | 加入服务启动流程 |
| 3 | CRAG 在 ~120 文件上简化为二级路由 | 调整路由设计 |
| 4 | Query rewrite 应与原始查询并行检索取并集 | 修改 INCORRECT 分支 |
| 5 | Langfuse 是最适合的可观测性方案（开源+自托管+原生 LangGraph 集成） | Phase 迁移时同步集成 |

### 值得注意（3 项）

| # | 发现 | 行动 |
|---|------|------|
| 6 | 压缩时数学/代码 chunk 跳过压缩 | 实现压缩时注意 |
| 7 | FlashRank 可作为 GPU 不可用时 CPU 降级 reranker | 记录为降级方案 |
| 8 | Speculative RAG "多视角验证"思想可借鉴 | 后续优化考虑 |

---

## 6. 实施 Gap 分析 — 7 个 Gap 全部解决

| Gap | 结论 |
|-----|------|
| **A1 依赖** | A1 未完成但不阻塞 A2 代码编写，只阻塞最终验收 |
| **代码接线** | reranker: lazy singleton + asyncio.to_thread; rewrite: 提取共享 query_rewriter.py; fusion: 扩展 fusion/ 让 nodes.py 调用 |
| **State 统一** | CanvasRAGState 加 4 个 Optional 字段（relevance_grades, compressed_context, compression_metadata, grade_prompt_used） |
| **fusion/ 命运** | 全部保留+扩展到 6 源（~2-3 小时），evaluator MRR_TARGET 从 0.35→0.70 |
| **其他 session 接口** | A3/A4 设计为 no-op fallback，验收测试等 Session C |
| **Prompt 模板** | 5 个模板已设计（见第 7 节） |
| **验收标准** | 原 4 项 + 新增 4 项 = 8 项验收标准 |

### 实施顺序

```
① 融合模块统一（扩展 fusion/ + 接入管道）
② 排序模型接入（加载 bge-reranker + 接线）
③ State 字段扩展（4 个新字段）
④ 设计 Prompt 模板（质量评分 + 查询改写）
⑤ 提取共享改写工具（query_rewriter.py）
⑥ 准备 5-10 个临时测试用例
⑦ 接口设计 + 验收测试骨架
```

### 关键修改文件

**修改：**
- `src/agentic_rag/nodes.py` — reranker 实现 + fusion 调用
- `src/agentic_rag/state.py` — 新 CanvasRAGState 字段
- `src/agentic_rag/fusion/unified_result.py` — 新 SearchSource 值
- `src/agentic_rag/fusion/rrf_fusion.py` — 6 源扩展
- `src/agentic_rag/fusion/strategy_selector.py` — 多源 execute_fusion
- `src/agentic_rag/fusion/evaluator.py` — MRR_TARGET 更新

**新建：**
- `src/agentic_rag/query_rewriter.py` — 共享改写工具
- `src/agentic_rag/prompts/` — prompt 模板目录

---

## 7. Prompt 模板设计

### 现有 Prompt 审查

| 现有 prompt | 质量 | 操作 |
|------------|------|------|
| analyze_intent (agent_graph.py:82-97) | 极简，缺分类和策略 | **替换** |
| grade_documents (agent_graph.py:265-275) | 极简，只有二元分类 | **替换** |
| rewrite_query (agent_graph.py:350-358) | 极简，缺失败分析 | **替换** |
| tool_instruction (agent_service.py:1538-1573) | ✅ 高质量，30 条规则 | **直接复用** |
| context_instruction (agent_service.py:1584-1591) | ✅ 高质量 | **直接复用** |
| 8 种 Agent 教学模板 (.claude/agents/*.md) | ✅ 结构成熟 | **包装增强** |

### 5 个新模板设计

#### 模板 1: grade_documents（质量评分）— 替换

- **分类**：三元 correct / incorrect / ambiguous
- **评判标准**：宽松过滤（目标是去掉明显无关的，不是只保留完美匹配）
- **思维链**：对每个文档先给一句话理由再分类
- **few-shot**：6 个示例（2 例/类）+ Grading Notes 领域规则
- **输出**：Gemini response_schema 强制 JSON

#### 模板 2: rewrite_query（查询改写）— 替换

- **改写策略**：4 种（同义词扩展 / 抽象层次变换 / 中英文切换 / 关键词简化）
- **失败分析**：先分析为什么之前没搜到好结果
- **并行检索**：改写后与原始查询同时搜索取并集
- **输出**：2-3 个互补查询（非同义）

#### 模板 3: context_compression（证据提取）— 新增

- **提取式**：选原文关键句，不改写（避免引入幻觉）
- **特殊处理**：数学公式/代码完整保留
- **压缩限制**：每个文档最多提取 40%
- **输出**：JSON（relevant_extracts + key_concepts + contains_formula/code 标记）

#### 模板 4: educational_answer_generation（教学回答增强）— 包装

- **不替换**已有 8 种 agent 模板，在外层包装
- **mastery 适配**：根据掌握度调整解释深度（shaky→零基础 / developing→标准 / proficient→深层 / mastered→创新应用）
- **证据约束**：回答必须基于检索到的内容
- **苏格拉底模式**（可选）：引导提问而非直接给答案

#### 模板 5: intent_analysis（意图分析）— 替换

- **intent_type 分类**：explain / decompose / score / compare / list_notes / clarify
- **搜索策略规划**：broad_then_narrow / synonym_expansion / cross_language
- **reasoning 字段**：一句话说明为什么需要/不需要搜索

### Prompt 实施规则

| 规则 | 说明 |
|------|------|
| **Langfuse 管理** | 5 个模板通过 Langfuse Prompt Management 管理，不硬编码 |
| **Gemini response_schema** | 全部使用 Pydantic 强制 JSON 输出，字段不设 default |
| **Few-shot** | grade_documents 6 个示例 + Grading Notes；其他模板 1-2 个 |
| **超时保护** | 每个 LLM 调用 30s timeout + 2 次自动重试 |
| **注入防护** | 用户内容用 `<student_note>` delimiter 包裹 + 指令重申 |

---

## 8. 跨 Session 冲突解决

### ✅ 用户已确认

| 冲突 | 解决方案 |
|------|---------|
| **S4 拒绝合并 config vs A2 需统一权重** | nodes.py 改为读取 config.py 的值（不自定义默认值），不改 config 架构 |
| **教育调研"立即实施" mastery vs A2 放第二批** | mastery-as-context 提前到第一批末尾（轻量操作仅需 prompt 加一行） |
| **Contextual Retrieval 归属不清** | 属于 A1（索引时加上下文前缀），不属于 A2 范畴 |

---

## 9. 验收标准

### 原始 4 项

| # | 标准 | 测量方法 |
|---|------|---------|
| 1 | 上下文 token 数 15K → ≤3K | tiktoken 计数 |
| 2 | Faithfulness ≥ 0.85 | RAGAS / LLM-judge |
| 3 | Reranker 提升 MRR ≥ +0.10 | evaluator.py（需基线数据） |
| 4 | CRAG 质量闭环触发率 < 20% | CRAG 节点计数器 |

### 新增 4 项

| # | 标准 | 测量方法 |
|---|------|---------|
| 5 | Reranker 延迟 < 500ms | per-request timing |
| 6 | 压缩后回答质量保持 ≥ 90% | golden test 对比 |
| 7 | CRAG 循环终止（max 2 次，无死循环） | 对抗性查询测试 |
| 8 | 融合统一后无回归 | 相同输入 → 输出一致 |

**关键依赖**：所有量化验收标准依赖 Session C 的 Golden Test Set（目前不存在）。

---

## 10. 决策记录汇总

### Decision 记录（4 条）

| 决策 | 内容 |
|------|------|
| [Decision] 完整实施方案 | 三批九项 + 教育专项 |
| [Decision] 补充发现 5 项 | warmup / CRAG 二级 / 并行检索 / Langfuse / VRAM |
| [Decision] 七大 Gap 方案 | lazy singleton / 共享 rewriter / fusion 扩展 / State 4 字段 / 接口 no-op / 5 prompt / 8 项验收 |
| [Decision] 冲突解决 + Prompt 规则 | config 读取统一 / mastery 提前 / CR 归 A1 / Langfuse 管理 / Gemini schema / few-shot / timeout / 防注入 |

### Decision-Review（4 条，全部 PENDING）

所有决策的验证状态为 **PENDING**，需独立 session 制定严格验收标准并在真实数据上测试。

### Code-Review（1 条）

5 大任务块代码质量审查 — Reranking 0% / fusion 双实现 / quality gate 半废 / 上下文暴力拼接 / CRAG 可激活

### Research-Tech（4 条）

- 社区+论文 5 主题调研
- 教育 RAG 专项调研
- 补充调研（部署陷阱 + 可观测性）
- Prompt 社区补充（Langfuse 管理 + Gemini schema + few-shot + 注入防护）

---

## 11. 下一步行动

1. **独立验证 session** — 获取所有 PENDING 的 Decision-Review，制定具体验收标准
2. **Session C** — 构建 Golden Test Set（50+ query，覆盖 6 类），为 A2 验收提供数据
3. **A1 完成** — bge-m3 + 分块策略实施，解除 A2 最终验收的阻塞
4. **A2 实施** — 按 ①-⑦ 顺序执行，估计 2-3 个 sprint
