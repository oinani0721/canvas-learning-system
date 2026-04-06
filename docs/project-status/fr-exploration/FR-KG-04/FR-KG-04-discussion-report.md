# FR-KG-04 探索讨论报告

> **探索日期**: 2026-04-04
> **议题**: 节点/连线自动同步后端 KG — 架构全景分析
> **参与者**: 用户 + Claude Opus 4.6

---

## 讨论 1：初始架构探索

**用户问题**: FR-KG-04 的相关设计文件和架构是什么？

**调研结论**:
- 前端使用 **Outbox Pattern**：canvas-store → Dexie sync_outbox → SyncEngine → `POST /api/v1/sync/batch`
- 后端有两条独立的 Neo4j 写入路径
- 涉及 Story 36.3（单条 edge 同步）、36.4（全量同步）、30.5（Memory Event）
- SyncEngine 状态机：IDLE → SYNCING → OFFLINE，debounce 2s，retry 5x

**关键文件**: `canvas_service.py`, `sync_service.py`, `sync-engine.ts`, `canvas-store.ts`

---

## 讨论 2：断裂点 3 深挖 — sync/batch 是否触发 Neo4j 同步？

**用户问题**: 前端发的 sync/batch 请求，后端是否真的调用了 canvas_service.add_edge()？

**调研结论**: **没有调用。** 发现两条完全独立的路径：

| | 路径 A: SyncService | 路径 B: CanvasService |
|---|---|---|
| 触发者 | 前端 SyncEngine（实际在用） | 无人调用（死代码） |
| Neo4j 关系 | `CANVAS_EDGE` | `CONNECTS_TO` |
| Story | 1.5 | 36.3 |

**关键发现**: Story 36.3 精心设计的 `_sync_edge_to_neo4j()` + retry + fire-and-forget 是死代码——前端走的是完全不同的路径。

---

## 讨论 3：两条路径的设计初衷

**用户问题**: deep explore 这两个模块推测一开始的设立意图，用通俗的方式解释。

**调研结论**:
- **路径 A（SyncService）= 数据搬运工**：离线优先 Outbox Pattern，把前端画的东西原样存到后端，断网不丢数据
- **路径 B（CanvasService KG Sync）= 学习感知器**：告诉学习系统"这个学生认为概念 A 和概念 B 有关系"，构建学习知识图谱

设计意图上是**故意分开的**：CANVAS_EDGE = "白板上有这条线"（结构性），CONNECTS_TO = "这两个概念有关联"（学习性）

---

## 讨论 4：下游消费者分析（Q1 决定性问题）

**用户问题**: 下游消费者读的是哪个关系？

**用户追问**: 什么叫"下游消费者"？

**通俗解释**: 下游消费者 = 你的应用里那些需要读取 Neo4j 数据来工作的功能模块（RAG 检索、复习推荐、学习轨迹分析等）。如果它们读的"钥匙"和数据库里存的"锁"不匹配，就查不到任何数据。

**调研结论 — 三层图互不相通**:

| 图层 | 关系类型 | 写入方 | 读取方 | 状态 |
|------|----------|--------|--------|------|
| 图层 1 | `CANVAS_EDGE` | SyncService | 推荐系统 | ✅ 通 |
| 图层 2 | `CONNECTS_TO` | CanvasService（死代码） | 验证服务 | ❌ 断 |
| 图层 3 | `RELATES_TO` | Graphiti LLM 提取 | RAG 检索 | ✅ 通，但跟白板连线无关 |

**核心结论**: 用户在白板上画的连线，**对 RAG 回答质量没有任何影响**。RAG 的知识来源是 Graphiti 从学习对话中自动提取的概念关系。

---

## 讨论 5：验证服务分析

**用户问题**: 验证服务的图查询是否成熟？是只给原白板还是检验白板也用？

**调研结论**:
1. **图查询不成熟** — 只有 1-hop 查询 + LIMIT 8 截断，无排序/权重/时间感知。对比 Graphiti 的向量搜索 + cross-encoder 重排序，差距巨大
2. **只在 Review 模式用** — `/api/v1/review/session/*` 端点，考试系统（exam_service）完全不用验证服务
3. 验证服务内部有三路上下文：RAG 语义检索 ✅ + 图谱 1-hop ❌（空） + FSRS 评分历史 ✅

---

## 讨论 6：Graphiti 记忆提取方式

**用户问题**: Graphiti 的记忆提取是用 Hook 还是自己写的？是云端还是本地模型？

**调研结论**:
- **正规官方 SDK**：`graphiti-core >= 0.28.2`
- **云端 Gemini API**：`gemini-2.5-flash` + `gemini-embedding-001` + GeminiRerankerClient
- **事件驱动触发**：Agent 回答后 → FastAPI background_task → episode_worker.enqueue() → Graphiti add_episode()
- **类型化提取**：Pydantic 模型（LearningConcept, Misconception, LearningTip, MasteryRecord）
- **无本地模型 fallback**：API 挂了 → 静默跳过 + dead letter（`data/dead_letter_episodes.jsonl`）

---

## 讨论 7：两个图谱能否合并？

**用户问题**: 白板连线图谱和 Graphiti 概念图谱能否合并为一个统一图谱？

**调研结论**: **可以，Graphiti SDK 原生支持。**
- `graphiti.add_triplet(source_node, edge, target_node)` 专门用于手动添加关系
- 当前代码绕过 Graphiti 直接写 Neo4j Cypher，应改成走 add_triplet()
- 更新用时间模型（旧边标记失效，创建新边）
- 项目基础设施已 90% 到位，缺的只是把写入路径改一下

---

## 讨论 8：RAG 语义检索

**用户问题**: RAG 语义检索是什么？用了哪个 RAG？是笔记片段精确检索吗？

**调研结论**: 5 路并行检索系统（Canvas Agentic RAG, LangGraph）：
1. **Graphiti** — 知识图谱（RELATES_TO）
2. **LanceDB** — 向量搜索（bge-m3, 512 token 分块, 中文 jieba 分词）→ **返回原文片段** ✅
3. **多模态** — 图片/PDF OCR 内容
4. **跨白板** — 标签匹配（已被 S27-GDA-2 取消）
5. **Vault 笔记** — .md 文件搜索

**发现 bug**: 验证服务期望 RAG 返回 `learning_history`/`related_concepts`/`common_mistakes`，但 RAG 实际返回 `reranked_results`。字段名不匹配 → 验证服务拿到空默认值。

**用户追问**: LanceDB 和 Vault Notes 不应该用同一个检索系统吗？

**回答**: 不是同一个。LanceDB 搜白板节点文本，Vault Notes 搜 .md 笔记文件。都返回原文片段但数据来源不同。

**用户追问**: 为什么用 LanceDB 而不直接用 Graphiti？

**回答**: Graphiti 返回 LLM 提取后的事实/实体名（原文丢失），LanceDB 返回原文片段。两者互补：Graphiti 回答"这个概念跟什么有关"，LanceDB 回答"原文怎么说的"。

---

## 讨论 9：FSRS 评分历史

**用户问题**: FSRS 怎么融入关系图谱？对检验白板有什么影响？

**调研结论**:
- FSRS **存在 Neo4j 节点属性上**（fsrs_stability, fsrs_difficulty, fsrs_state 等）
- FSRS 和关系图谱是**分开存储的**：图谱管"关系"，FSRS 管"时间"，评分管"难度"
- 检验白板影响：根据历史得分决定出题难度（<60 基础题，60-79 验证题，≥80 应用题）
- 调用链：用户回答 → AI 评分 0-100 → 映射 FSRS Grade 1-4 → mastery_engine.update_on_interaction() → fsrs_manager.review_card()

**用户追问**: FSRS 是节点属性吗？出题决策是 AI 还是脚本？

**回答**:
- FSRS 就是存在 Neo4j EntityNode 的属性上
- 验证服务 = "Dumb tool"（节点选择按文件顺序，不看 FSRS）
- 考试系统 = "Clever algorithm"（三因子融合：0.4 BKT + 0.3 FSRS + 0.3 KG）
- 题目生成和评分是 AI 驱动（Gemini API）

---

## 讨论 10：Episode 缓存上限

**用户问题**: 2000 上限是 per 白板还是全局？节点超过 2000 怎么办？

**调研结论**:
- **全局的，但只影响内存缓存**
- Neo4j **无存储上限**，永久保留所有 episode
- 2000 是 `self._episodes` 列表的硬限制（Story 38.2），超过就丢弃最旧的
- 正常查询走 Neo4j，只有超时才 fallback 到内存缓存
- **发现 bug**: 内存缓存查询时没有按 group_id 过滤，可能导致其他白板数据混入

---

## 讨论 11：图片处理

**用户问题**: 图片处理有成熟算法吗？

**调研结论**: 当前用 Gemini 2.0 Flash Vision API（OCR + 摘要 + 概念提取），存入 LanceDB 向量化。

**用户决策**: 改用本地模型（MinerU / DeepSeek OCR / Claude Code 视觉能力），不依赖 Gemini API。

---

## 讨论 12：跨白板关联

**用户问题**: 跨白板关联是自动还是手动？

**调研结论**:
- 原始设计（Story 16.1）是**手动关联**（选目标白板 + 关联类型 + 描述）
- 代码实现用了自动 Tag Jaccard 相似度（不符合原始设计意图）
- 已被 S27-GDA-2 决策取消（"先不做"）
- 用户提出可以用同一 group_id 前缀来跨白板搜索（Graphiti 支持传多个 group_id 列表，但不支持前缀匹配）

---

## 讨论 13：出题决策策略

**用户问题**: 出题应该像 Plan 文件一样有逻辑递进。三因子算法（0.4/0.3/0.3）可信吗？

**调研结论**:
1. **当前验证服务的出题是"傻"的** — 按文件顺序出题，不看 FSRS，不看图谱依赖关系，不做拓扑排序
2. **三因子权重无学术支撑** — 没有引用论文，没有 A/B 测试，权重跟设计文档规格不一致（文档说 40% FSRS / 30% BKT / 20% KG / 10% 交互，代码写 40% BKT / 30% FSRS / 30% KG）
3. BKT 和 FSRS 单独是成熟算法，但加权组合方式是 ad-hoc 的

---

## 汇总：发现的问题清单

| # | 严重度 | 问题 | 位置 |
|---|--------|------|------|
| 1 | CRITICAL | 三层图互不相通，CONNECTS_TO 是死代码 | sync_service.py / canvas_service.py |
| 2 | HIGH | RAG 字段名不匹配，验证服务拿到空默认值 | verification_service.py:1835-1837 |
| 3 | HIGH | 验证服务出题按文件顺序，不看 FSRS/图谱 | verification_service.py:628 |
| 4 | HIGH | 三因子权重无学术支撑（0.4/0.3/0.3 ad-hoc） | question_generator.py:44-47 |
| 5 | MEDIUM | 内存缓存查询缺少 group_id 过滤 | memory_service.py:561 |
| 6 | MEDIUM | 权重跟设计文档规格不一致 | question_generator.py vs deep-research docs |
| 7 | LOW | 图片处理依赖云端 Gemini API 无本地 fallback | index_image.py |

## 用户决策记录

| 决策 | 内容 |
|------|------|
| 图片处理 | 改用本地模型（MinerU/DeepSeek OCR/Claude） |
| 跨白板关联 | 应该是手动选择，不是自动 Jaccard |
| 出题逻辑 | 应该像 Plan 文件逐步递进（Mastery-Based Progression） |
| 图谱合并 | 考虑用 Graphiti add_triplet() 统一管理两层图 |
