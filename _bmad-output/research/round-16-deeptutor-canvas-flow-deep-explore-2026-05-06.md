---
title: Round 16 — 在 HKUDS/DeepTutor 上践行 Canvas Learning System 核心学习流程 Deep Explore
date: 2026-05-06
trigger: round-15 line 155 用户批注（DeepTutor 改造）+ 用户后续指令"聚焦核心学习流程在 DeepTutor 实施"
agents: 3 并行 Explore Agent (Sonnet)
related:
  - _bmad-output/research/round-15-bkt-fsrs-multihop-tauri-prd-deep-explore-2026-05-05.md
  - _bmad-output/research/round-14-graphiti-retrieval-deep-explore-2026-05-05.md
  - _bmad-output/planning-artifacts/epics.md
  - _bmad-output/planning-artifacts/recovered/prd-tauri-original-2ae5897.md
status: 调研报告，待用户审计后决定是否落地
---

# Round 16 — 在 DeepTutor 上践行 Canvas 核心学习流程 Deep Explore

## 元信息

| 字段 | 值 |
|---|---|
| 触发 | `_bmad-output/research/round-15-bkt-fsrs-multihop-tauri-prd-deep-explore-2026-05-05.md:155` 用户批注 + 后续中断指令 |
| 调研方式 | 3 并行 Explore Agent（Sonnet model）|
| 范围 | Canvas 7 Stage 流程清单 + DeepTutor 模块 capability mapping + 3 项额外能力工程方案 |
| 报告字数 | ≈11000 字 |
| 状态 | 初稿，待用户审计 5 个决策点 |

---

## 用户原始指令链

**指令 1（round-15 line 155）**：
> 我们要不要直接 先在这个 https://github.com/HKUDS/DeepTutor 来改造，我觉得额外我需要的能力是：
> 1. **vault 文件夹检索**：AI 讲解时能精确返回笔记片段
> 2. **批注 + 双链拆解链条理解**：agent 理解我的拆解逻辑 → 更合理出闪卡/题目
> 3. **FSRS 配合**：原白板=拆解学习；检验白板=测试考察；FSRS=何时使用检验白板的调度

**指令 2（用户中断后追加）**：
> 聚焦于把 Canvas learning system 所提出的核心学习流程需求 在我们的 DeepTutor 来实施践行。请你启动并行 agent deep explore 来思考可行性

→ 用户已**决定路径**：DeepTutor 作底座，Canvas 核心流程上去践行
→ 调研聚焦"**怎么实施**"（不再讨论"要不要用"）

---

## 一句话核心结论

**架构 B 双后端推荐**：DeepTutor 跑 chat / quiz / RAG / Book Engine / Memory；**保留** Canvas 28 已验证服务（vault sync / error pipeline / mastery BKT+FSRS / Graphiti）。两后端通过 HTTP/MCP 桥接互通。**总工程量 18-26 人天**（约 3-6 周，1 人全职）。整体匹配度 **6/10**：内容辅导层（Stage C/F）直接可用；vault 感知 / 双链 / 错误主权 / FSRS / 结构化 Rubric 五项缺口需 Canvas 桥接或自建。

---

## 第一部分：Canvas 7 Stage 学习流程需求清单（Agent A）

### 1.1 完整学习闭环（一句话）

> 用 Obsidian 原白板拆解知识（打批注 + 双向链接）→ AI 对话加深理解（错误被捕获归档）→ FSRS 确定复习时机 → 触发检验白板考察（信息完全隔离）→ 静默评分更新 BKT/FSRS → 错误闭环 Day 3/7 追踪

每一步围绕**"批注驱动的精确考察"**核心哲学，让学习数据反哺下一次考察。

### 1.2 7 Stage 详细需求 + 实施状态

#### Stage A — 学习内容输入

| 需求 ID | 描述 | PRD 来源 | 状态 |
|---|---|---|---|
| FR-SYS-01 | Templater 自动生成标准 frontmatter（mastery/bkt/fsrs/errors/tips）| `prd.md:481-487` | ⚠️ 模板已定义，部署待验证 |
| FR-ADAPT-01 | wikilink 双链图遍历发现概念邻居 | `prd.md:493-497` | ⚠️ `wikilink_graph_service.py` 已有内存图+BFS，**未写 Neo4j、未与 Graphiti 同步** |
| FR-ADAPT-03 | 文件变更增量热更新（非全量重建）| `prd.md:497` | ⚠️ `metadataCache.on('changed')` 钩子已注册，**只清 masteryCache，未触发 KG 同步** |
| FR-KG-03 | Graphify 自动提取概念关系（71x 压缩）| `prd.md:417` | ❌ 集成未实施（Phase 1 后段）|
| FR-MM-01/02 | 粘贴图片 AI 识别 | `prd.md:513-519` | ❌ Phase 3 |

#### Stage B — 知识拆解（原白板）

| 需求 ID      | 描述                                        | 状态                                           |
| ---------- | ----------------------------------------- | -------------------------------------------- |
| FR-KG-01   | 双向链接创建概念关系 + 链接完整性维护                      | ⚠️ 前端 wikilink 插入已实现，relationships[] 自动维护待验证 |
| FR-KG-06   | frontmatter relationships[] 记录语义关系 + 讨论历史 | ⚠️ schema 已定义，edge 讨论后写入待验证                  |
| FR-KG-05   | 三级置信度（EXTRACTED/INFERRED/AMBIGUOUS）       | ❌ 依赖 Graphify                                |
| FR-KG-08   | KG 健康检查（孤立节点 / 矛盾关系）                      | ❌ Phase 2                                    |
| FR-CONV-05 | `[!tip]+` callout → frontmatter tips[]    | ⚠️ InlineAnnotation 组件存在，端到端未验证              |

**核心哲学**（D14 锁定）：批注 = 答题 = 批注延伸

#### Stage C — AI 辅助理解

| 需求 ID         | 描述                                            | 状态                                             |
| ------------- | --------------------------------------------- | ---------------------------------------------- |
| FR-CONV-01    | 启动对话自动注入相邻概念                                  | ⚠️ chat_with_context Skill 框架存在                |
| FR-CONV-04    | 注入 1-hop 邻居 frontmatter + Tips + 错误 + Edge 理由 | ⚠️ context_enrichment 已重构为图遍历，Paradigm 2 实施待确认 |
| FR-CONV-11    | MCP 按需拉取邻居 + 超窗压缩                             | ❌ 真正 Graphiti 检索未接入（round-14:46-54）            |
| FR-CONV-02    | 基于个人误解主动提醒                                    | 🔴 阻塞：错误"只写不读"                                 |
| FR-CONV-03    | 显示可点击补充材料（语义搜索 ≤5 条）                          | ⚠️ 架构存在，LanceDB 索引未触发，搜索返回空                    |
| FR-EDGE-01/02 | 选两概念 EI+SE 双策略深度讨论                            | ⚠️ EdgeContext 已实现，提示词验证待完成                    |
| FR-CONV-07/09 | 对话归档 Hot/Warm/Cold                            | 🔴 阻塞：Graphiti 假实现                             |

#### Stage D — 错误捕获（progressive_confirmation）

| 需求 ID | 描述 | 状态 |
|---|---|---|
| FR-CONV-06 | AI 4 类分类（概念混淆/推理谬误/粗心/元认知）| ⚠️ ConversationDistiller 已实现，主权确认流程待验证 |
| FR-MEM-01 | 双写：frontmatter errors[] + Graphiti | 🔴 阻塞：用旧 `group_id="cs188"` 写入，无对应读取路径 |
| 主动检测+增量提问（progressive_confirmation 设计）| ❌ 当前 Modal 未显示错误详情 |

错误分 `error_candidates[]`（AI 建议）→ 用户 Dashboard 主权确认 → `errors[]`。4 类分类驱动差异化补救：**推理谬误 → "诱导再犯"策略**（检验白板设置陷阱验证是否真正克服）。

#### Stage E — 掌握度追踪 + 复习调度

| 需求 ID | 描述 | 状态 |
|---|---|---|
| FR-MAST-01 | BKT 实时更新 p_mastery（贝叶斯，先验 0.30）| ⚠️ Story 5.1 AC 已定义，实施待验证 |
| FR-MAST-02 | FSRS 算法计算最优间隔 | ⚠️ `update_fsrs()` MCP 在后端，**BKT mastery 如何影响 FSRS retrievability 公式两版 PRD 均未显式定义** |
| FR-MAST-03 | 5 信号融合（BKT + FSRS + 错误 + 校准 + 自评，r<0.7）| ❌ 仅抽象描述，无数学表达式 |
| FR-MAST-06 | 掌握度仅通过考察更新（不接受自评直接修改）| ⚠️ 架构约束已定义 |
| FR-MAST-04 | 评分操作链 5 步防篡改（pipeline_token）| ⚠️ 设计存在，端到端验证待完成 |
| FR-MAST-05 | 2x2 元认知校准矩阵 | ❌ Phase 2（需 400+ 题）|
| FR-SPACE-01/05 | Dashboard NextReview + Bases 表格提醒 | ⚠️ 框架存在 |

#### Stage F — 检验白板生成

| 需求 ID | 描述 | 状态 |
|---|---|---|
| FR-EXAM-22 | **三重信息隔离**（type 标记 + AI 上下文重置 + Skill prompt 约束）| ⚠️ 设计完整，待 Phase 1 验证 |
| FR-EXAM-10 | 防止嵌套生成 | ⚠️ 逻辑已定义 |
| FR-EXAM-01 | 基于已有白板生成完全空白检验白板 | ⚠️ exam_boards/*.md 架构存在 |
| FR-EXAM-02 | 基于 BKT/FSRS 选薄弱节点 | ⚠️ 选题逻辑待实施 |
| FR-EXAM-03 | **三路融合出题**（Graphiti + Graphify + frontmatter 掌握度）| 🔴 阻塞：Graphiti 错误读取缺失 |
| FR-EXAM-11/12/13 | 3 种考察模式（点对点/综合/混合）| ⚠️ ExamModeSelector 已实现 |
| FR-EXAM-19 | IRT 连续难度匹配（≥70%）| ❌ 未实施 |

**ACP 5 层 prompt 结构**（Tauri PRD 核心）：第 3 层动态注入 Tips/错误/Edge 理由/精通度/对话历史。

#### Stage G — 答题评分反馈

| 需求 ID | 描述 | 状态 |
|---|---|---|
| FR-EXAM-05 | md 编辑器手写 + 手动提交（D14 锁定）| ⚠️ 待验证 |
| FR-EXAM-04/06 | AutoSCORE 两阶段（证据提取 + 4维4分制×3次投票），学习者不感知 | ⚠️ AutoScorer 已实现，前后端管道待验证 |
| FR-EXAM-07/08 | 4 级渐进提示 + 跳过不惩罚 | ⚠️ 组件已实现 |
| FR-EXAM-15/17 | 考后校准投票 + 数据同步回源白板 | ⚠️ 框架存在 |
| FR-SPACE-02/03 | Day 3 注入历史误解 + Day 7 辨析题验证 | ❌ Phase 2 |
| FR-EXAM-14/20 | 书签式概念提取（`[!discussion_later]+` 不切 Tab）| ⚠️ 概念存在 |
| FR-VIZ-01/04 | 全局 Dashboard 三层布局 + 一键考察 | ⚠️ 框架存在 |

### 1.3 MVP 14 项 vs Phase 2 划分

#### MVP Phase 1（当前优先）

| # | 需求 | 状态 |
|---|---|---|
| 1 | vault 初始化 + 扁平架构 | ⚠️ 待 UAT |
| 2 | 三重信息隔离检验白板 | ⚠️ 待 Phase 1 验证 |
| 3 | `/chat_with_context` Skill + wikilink 邻居注入 | ⚠️ 管道待验证 |
| 4 | `/start_exam_board` Skill 完整 10 步 | 🔴 依赖 Graphiti 修复 |
| 5 | `/extract_node` 书签式提取 | ⚠️ 端到端待测试 |
| 6 | Templater 模板 | ⚠️ 已定义 |
| 7 | BKT+FSRS frontmatter 更新 | ⚠️ AC 已定义待实施 |
| 8 | AutoSCORE 4 维评分 | ⚠️ 组件存在 |
| 9 | 错误自动提取 + 双写 | 🔴 Graphiti 读取路径缺失 |
| 10 | md 编辑器手写答案（D14）| ⚠️ 待验证 |
| 11 | callout 批注识别 + Tips 写入 | ⚠️ 端到端待验证 |
| 12 | 后端启动顺序验证 | ⚠️ 14 MCP 工具可用性 |
| 13 | context_enrichment 重构为 wikilink 图遍历 | ⚠️ 降级架构断层修复 |
| 14 | **真正 Graphiti 集成（6-8 天修复）**| 🔴 P2 阻塞项 |

#### 推迟到 Phase 2

- 节点颜色与掌握度自动联动（用户确认：颜色仅个人标记）
- OLM 元认知 2x2 校准矩阵（需 400+ 题）
- 检验白板拖拽（架构转型废弃）
- Edge 对话 EI+SE 完整实施
- Day 3/7 错误复习闭环
- Graphify 71x 压缩集成
- Dashboard 完整三层布局
- 多段推理 over KG（业界无先例，最大 Gap）

### 1.4 用户 7 心头愿景（必须保留到 DeepTutor）

| # | 愿景 | round-14/15 引用 |
|---|---|---|
| 1 | Graphiti 后端记录 ↔ 前端批注内容**高度一致** | round-14:295 #3 |
| 2 | **精确多段推理 + 批注驱动出题** | round-14:207-208 |
| 3 | 原白板 / 检验白板 / FSRS **三位一体** | round-15:155 |
| 4 | **诱导再犯**策略验证错误已纠正 | prd-annotations-2ae5897.md:168-170 |
| 5 | Graphiti 关系 ↔ 用户定义双链关系一致 | round-14:295 #4 |
| 6 | AI 主动检测错误后**增量确认** | round-14:295 #2 |
| 7 | vault 笔记片段精确返回 | round-15:155 能力 1 |

### 1.5 Must-Have / Should-Have / Nice-to-Have

#### Must-Have（缺一不可）
1. 三重信息隔离（FR-EXAM-22）
2. md 编辑器手写答案 + 手动提交（D14）
3. callout 批注识别写入 frontmatter
4. 三路融合出题（Graphiti + Graphify + frontmatter）
5. AutoSCORE 4 维静默评分
6. BKT/FSRS 考后更新
7. 错误 4 类分类双写
8. 防嵌套检查
9. 真正 Graphiti 集成（round-14 4 残缺修复）

#### Should-Have（争取实现，可推迟）
1. wikilink 图遍历邻居注入
2. 4 级渐进提示 + 跳过不惩罚
3. Dashboard 一键考察
4. 书签式考中提取
5. Graphify 71x 压缩
6. Hot/Warm/Cold 归档
7. Day 3/7 错误复习闭环

#### Nice-to-Have（DeepTutor 不支持就放弃）
1. Edge 对话 EI+SE 双策略
2. 元认知 2x2 校准矩阵
3. 多段推理 over KG（最大 Gap，可作 Phase 3 研究项）
4. 节点颜色与掌握度联动
5. IRT 连续难度匹配

---

## 第二部分：DeepTutor 模块 ↔ Canvas 流程对接 mapping（Agent B）

### 2.1 整体匹配度 6/10

DeepTutor v1.3.7 现状：
- 23,400+ stars / Apache 2.0
- Python 72.5% + TypeScript 26.6%（FastAPI + LlamaIndex + Next.js 16）
- 支持 40+ LLM provider + Ollama
- 论文 arxiv 2604.26962（2026-04-10）
- 6 大模块：Chat / **Deep Solve** / Quiz Generation / Deep Research / Math Animator / Visualize
- 加上：**Book Engine** / TutorBot / **Persistent Memory** / RAG Pipeline / 自定义 Skills
- 路线图：**LightRAG 集成**（HKUDS 自家 KG-based RAG，34.8K stars）

### 2.2 7 Stage 对接 mapping 表

| Canvas Stage | Canvas 需求 | DeepTutor 模块 | 直接对接？ | 改造工程量 |
|---|---|---|---|---|
| A. 学习内容输入 | vault 文件夹批量 .md | `knowledge/add_documents.py` + `manager.py::link_folder()` | 基本可用，缺 frontmatter/wikilink 解析 | **低-中** |
| B. 原白板（双链）| md vault + wikilink + 节点层级 | **无原生**（DeepTutor 仅平坦向量索引）| **不能直接对接** | **高** |
| C. AI 辅助理解 | 邻居 + frontmatter + 错误注入 | **`Deep Solve`**（plan→ReAct→write 三阶段）| **高度匹配** | **低** |
| D. 错误主权确认 | AI 检测 → candidates → 用户确认 + 4 型分类 | **无等价**，DeepTutor 仅 Deep Solve 验证步骤 | **不能对接** | **高**（保留 Canvas 自建）|
| E. 掌握度 + 复习调度 | BKT/DKT + FSRS-4.5 + 5 信号融合 | DeepTutor `Persistent Memory` 仅叙述型，**无 FSRS** | **不能直接对接** | **高**（保留 Canvas）|
| F. 检验白板生成 | ACP 5 层 prompt + KG multi-hop | **`Book Engine`**（14 种 block）+ Deep Solve | **部分可对接** | **中** |
| G. 答题评分错误闭环 | 4 维 Rubric + Day 0/3/7 | `Deep Question` 4-stage + TutorBot；**无评分 Rubric** | **部分可对接** | **中-高** |

### 2.3 DeepTutor 3 大优势模块（直接对接 Canvas）

#### 优势 1：Deep Solve → 对接 Stage C

**源**：`deeptutor/capabilities/deep_solve.py`

- 三阶段链路：plan → ReAct（reason-act-observe 循环）→ write
- 底层 `MainSolver` 驱动，支持 RAG / web_search / code_execution / reason 4 工具
- `_trace_bridge()` 归一化为流式 SSE 事件，**与 Canvas WebSocket 推送架构天然兼容**
- `_run_answer_now()` 提供快速路径，evidence 足够时跳过 plan + ReAct

**对接方式**：将 Canvas mastery frontmatter（mastery_score / error_count / FSRS due）和邻居节点内容**预注入** Deep Solve KB context 前缀，RAG 部分改为 Canvas 自有 LanceDB + Graphiti 检索器（`vault_notes_retriever.py` 已存在）。

**工程量**：低

#### 优势 2：Book Engine → 对接 Stage F

**源**：`deeptutor/book/models.py` / `deeptutor/book/blocks/__init__.py` / `deeptutor/book/compiler.py`

**14 种 BlockType**（4 个 Phase）：
- Phase 1: TEXT / CALLOUT / QUIZ / USER_NOTE
- Phase 2: FIGURE / INTERACTIVE / ANIMATION / CODE / TIMELINE / FLASH_CARDS
- Phase 3: DEEP_DIVE
- Phase 4: SECTION / CONCEPT_GRAPH

**Book status 机器**：DRAFT → SPINE_READY → COMPILING → READY
**4 层数据模型**：Page / Chapter / Spine / Book — **与 Canvas 检验白板多段结构高度对齐**

**对接限制**：⚠️ `ConceptGraphGenerator` 是 deterministic renderer（不调 LLM，仅渲染预计算 Mermaid）。Canvas 需要的 multi-hop KG 推理必须在 Book Engine `engine.py` 上游自建 KG query 层，结果作为 `ctx.extra['concept_graph']` 注入。QUIZ / FLASH_CARDS block 可直接映射 Canvas 题目格式，但题目 ACP 数据包（FSRS+BKT+KG 三因子）需 Canvas 自建。

**对接 Canvas Story 6.x**（检验白板生成）：上游接 Canvas ACP question_generator，CONCEPT_GRAPH 接 Canvas Graphiti multi-hop query 结果。

**工程量**：中

#### 优势 3：Persistent Memory（部分）→ 对接 Stage E

**源**：`deeptutor/services/memory/service.py`

- 维护两个 Markdown 文件：**PROFILE.md**（学习者身份/风格/偏好）+ **SUMMARY.md**（学习焦点/已掌握/开放问题）
- 更新触发：`refresh_from_turn()`（每轮对话后）+ `refresh_from_session()`（最近 10 条）
- 底层 `SQLiteSessionStore` 读会话，LLM 流式重写后写入磁盘 markdown

**与 Canvas Graphiti 的差距**：

| 维度 | DeepTutor Memory | Canvas Graphiti |
|---|---|---|
| 存储格式 | Markdown 文件 | Neo4j 图数据库 |
| 数据模型 | 非结构化叙述型 | 强类型 Pydantic（LearningConcept / MasteryRecord / Misconception / LearningTip）|
| 更新触发 | 每轮 + 每会话 LLM 重写 | 学习事件写入 + 去重 |
| 查询能力 | **无结构化查询，只能全文读取** | Cypher + Graphiti 语义搜索 |
| 时序追踪 | 无时间戳，新写覆盖旧 | episode 含 created_at / valid_at / invalid_at |
| 掌握度建模 | 叙述性"已掌握内容"，无量化字段 | MasteryRecord + FSRS CardState（stability / difficulty / due / lapses）|

**结论**：PROFILE.md 学习者画像可作为 Canvas Graphiti learner profile episode **输入补充**，但**两者架构完全异构，无数据层直接复用路径**。

### 2.4 DeepTutor 5 大弱项 + 替换方案

| 弱项                 | 根本原因                                                | Canvas 替换方案                                                                                                         |
| ------------------ | --------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| **Vault 文件夹感知缺失**  | `add_documents.py` 平坦文件索引，无 frontmatter/wikilink 解析 | Canvas `wikilink_graph_service.py` + `vault_notes_retriever.py`（LanceDB）完全替代                                        |
| **无双链关系图**         | 知识库纯向量，无图结构                                         | Canvas Graphiti 维护 5 种关系边（IS_PREREQUISITE / IS_APPLICATION / CONTRASTS_WITH / IS_SUBCONCEPT / SUPPLEMENTS），**无可替代** |
| **无错误主权确认机制**      | DeepTutor 无候选列表 + 用户确认 UX                           | Canvas `error_classifier.py` + `error_aggregator.py` + MCP `error_tools.py` 全栈自建                                    |
| **无 FSRS / 复习调度**  | Question Bank 持久化但无间隔重复算法                           | Canvas `fsrs_manager.py`（py-fsrs 4.5）+ `review_service.py` 已生产运行                                                    |
| **无结构化 Rubric 评分** | Deep Question 仅生成题目                                 | Canvas `autoscore.py`（Stage 1 evidence + Stage 2 4 维 SOLO Rubric × 3 投票）                                            |

### 2.5 LightRAG 路线图评估

**LightRAG 现状**（github.com/HKUDS/LightRAG，v1.4.15，2026-04-19，34.8K stars）：
- HKUDS 自研 KG 增强 RAG（EMNLP 2025 论文）
- 文档索引阶段做实体-关系抽取，构建本地 KG
- 检索时同时走向量路径和图路径

**关键评估**：

| 能力                                | 状态                                                            |
| --------------------------------- | ------------------------------------------------------------- |
| 自定义关系类型（如 Canvas IS_PREREQUISITE） | ⚠️ 关系名由 LLM 在索引时生成，**非预先约束 schema**                           |
| Wikilink 命名关系                     | ❌ 无原生支持，无法感知 `[[node]]` 格式                                    |
| 集成时间表                             | ⚠️ DeepTutor 路线图提及，**当前代码库无任何 LightRAG import 或集成分支，ETA 未公开** |
| 能否替代 Canvas Graphiti              | ❌ **不建议等待**                                                   |

**结论**：LightRAG 是 document-level KG，**不是学习者状态图谱**。即使集成到 DeepTutor，解决的是文档检索质量问题，**不能替代 Canvas Graphiti 在掌握度追踪、错误建档、FSRS 调度中的角色**。值得作为 Stage A/C 的 RAG 检索质量提升手段（与 Canvas LanceDB 双轨），但不值得等待。

### 2.6 Skills 复用可行性

DeepTutor `SKILL.md` 系统是 CLI 使用指南文档（叙述 + 命令表），**无结构化 skill 定义 schema**。与 Claude Code Skill（YAML frontmatter + allowed-tools / triggers / instructions）**不兼容**。

Canvas 6 个 skill（chat-with-context / node-chat / ai-linked-doc / configure-whiteboard / managing-obsidian-annotations / verify-vault）均强依赖 Obsidian vault 结构 + wikilink + node_id，**无直接复用路径**。

DeepTutor TutorBot Soul Template 概念有"角色定义 + 行为约束"设计思想，可作为 Canvas TutorBot persona 模板**参考**，但需完全重写。

---

## 第三部分：3 项额外能力工程方案（Agent C）

### 3.1 一句话推荐

**3 项能力总工程量约 18-26 人天**，推荐**架构 B（双后端）**：DeepTutor 负责 chat/quiz/RAG/Book Engine/Memory，Canvas backend 保留 sync/error/wikilink_graph/BKT-FSRS/Graphiti，通过 HTTP Bridge 或 MCP 互通，**避免重写 28 个已验证服务**。

### 3.2 能力 1 — Vault 文件夹检索（4-5d）

**DeepTutor 现状**：
- `deeptutor/knowledge/manager.py::link_folder(kb_name, folder_path)` 已支持外部目录链接
- 调用 `FileTypeRouter.collect_supported_files()` 递归扫描
- `add_documents.py` 接受 `--docs-dir` 参数 → `rag_service.add_documents()` → LlamaIndex `VectorStoreIndex.from_documents()`
- ⚠️ `document_loader.py` 对 `.md` 不做特殊处理，`[[wikilink]]` 和 frontmatter 都当纯文本，metadata 仅 `file_name` / `file_path`
- ⚠️ `storage.py` 纯向量检索（无 metadata filter，无 BM25）

**改造侵入点**：

1. `deeptutor/services/rag/pipelines/llamaindex/document_loader.py`
   - 新增 `.md` 分支
   - **复用 Canvas `wikilink_context_service.py::_extract_user_callouts()` 80 行 regex**（不引入 obsidiantools 新依赖）
   - 按 H2/H3 标题 section 切片（LlamaIndex `SentenceSplitter`）
   - metadata 附加：`source_type="vault_note"`, `callout_types: list[str]`, `frontmatter_mastery_score`, `wikilinks: list[str]`

2. `deeptutor/knowledge/manager.py`
   - 新增 `add_vault(vault_path, kb_name)` 包装方法

3. Web UI（Next.js `web/`）
   - 新增 `folder_path` 输入表单

**Canvas 复用**：从 `.md` 抽 frontmatter（用 `yaml.safe_load`）和 wikilinks（用 `re.findall(r'\[\[([^\]]+)\]\]', text)`）。**无需移植 WikilinkGraphService 整体**，复用 regex 即可。

**工作量分解**：
- document_loader.py 改造：1.5d
- add_vault 入口 + FileTypeRouter `.md` 路由：0.5d
- Web UI folder_path 表单：1d
- 测试：1d

### 3.3 能力 2.1 — Callout 批注作为 RAG Seed（4-6d）

**DeepTutor 现状**：
- `storage.py` 用 `StorageContext.from_defaults()` + `VectorStoreIndex` 纯语义检索，**无 metadata filter 也无 score boost**
- `smart_retriever.py` 是 `SearchFunc(query, kb_name)` 黑盒注入
- `deep_question.py` prompt 含 `question_type / difficulty`，**无 callout 语义注入**

**改造侵入点**：

1. `deeptutor/services/rag/pipelines/llamaindex/storage.py`
   - `retrieve_nodes()` 加 `callout_filter: list[str] | None = None` 参数
   - 若传入 `["error", "tip"]`，对结果做 post-filter re-rank：命中 `metadata.callout_types` 的 chunk 得分乘以 `CALLOUT_BOOST = 1.5`
   - ⚠️ 注意：LlamaIndex 原生 `MetadataFilters` 需底层 vector store 支持。当前 DeepTutor 用 `SimpleVectorStore`（不支持），**先用 post-filter 不动 vector store**

2. `deeptutor/capabilities/deep_question.py` + prompt template
   - 在 prompt 拼装阶段（"Answer Now" 模式），额外注入 callout 上下文块：
   ```
   [用户批注：以下片段被标记为 [!error]，表示用户易错点]
   {callout_content}
   ```

3. `deeptutor/services/rag/smart_retriever.py`
   - 在 `run()` 中传递 `callout_filter` 到 search_func
   - 让多路查询的其中一路专门做 callout-seeded retrieval

**Canvas 复用**：`wikilink_context_service.py::_extract_user_callouts()` 和 `_extract_body_excerpt()` 共 ~130 行函数可**直接复制到 `document_loader.py`**，零新依赖，已通过 UAT 验证。

**工作量分解**：
- callout metadata 提取（复用 Canvas regex）：1d
- storage.py post-filter re-rank：1d
- prompt template callout 注入：1.5d
- smart_retriever callout 路由：0.5d
- 测试（单元 + prompt 效果）：1.5d

### 3.4 能力 2.2 — 双链 Multi-hop KG（5-6d，路线 A）

**DeepTutor 现状**：
- **没有任何图结构**
- RAG 是纯向量
- `book/models.py` 的 `ConceptGraph` 仅是 Pydantic 数据结构（不写图数据库）
- LightRAG 集成在路线图但 ETA 未公开

**两条路线**：

#### 路线 A — 轻量路线（不依赖 LightRAG）⭐ 推荐

**侵入点**：`deeptutor/knowledge/wikilink_graph.py`（新建）

- 从已索引 `.md` 提取 `[[wikilink]]` 构建 NetworkX `nx.DiGraph`（**复用 Canvas `WikilinkGraphService` BFS 逻辑**）
- 新增 `KGQueryService.get_2hop_subgraph(seed_note) -> list[str]`（BFS，复用 `get_neighbors()`）
- `smart_retriever.py` 加 2-hop 路由：先调 KGQueryService 拿邻居 → 对每个邻居 chunk 做向量检索 → 合并

**工作量分解**：
- wikilink_graph.py（NetworkX BFS）：1.5d
- smart_retriever 2-hop 路由：1d
- 题目生成 prompt 注入子图上下文：1d
- 测试：1.5d
- LightRAG 接入预留接口（抽象 `KGBackend` protocol）：0.5d

#### 路线 B — 等 LightRAG 或自建 Neo4j

- 等 LightRAG：ETA 不确定，~5d
- 自建 Neo4j：~8-10d，且与 DeepTutor 后续 LightRAG 合并产生冲突

**推荐路线 A**（Phase 3 先上轻量版）

### 3.5 能力 3 — FSRS 复习调度（4-5d）

**DeepTutor 现状**：
- `services/notebook/service.py` Record schema 通用 JSON
- `records[]` 仅 `id / type / title / summary / output / metadata / created_at / kb_name`，**无 FSRS 字段**
- `QuizAttempt` 仅 `block_id / question_id / user_answer / is_correct`，**无 next_due / stability / difficulty / reps / lapses**

**Canvas 现成代码**：
- `lib/memory/temporal/fsrs_manager.py` 已实现完整 `py-fsrs` 封装（`FSRSManager`, `CardState`, `get_rating_from_score()`）
- `test_fsrs_manager.py` / `test_review_service_fsrs.py` 测试覆盖完整
- → **可直接复制整个模块**

**改造侵入点**：

1. `deeptutor/services/notebook/service.py` — Record schema 扩展
   ```json
   "metadata": {
     "fsrs": {
       "card_data": "...",
       "due": "2026-05-10T00:00:00Z",
       "stability": 4.2,
       "difficulty": 0.55,
       "state": 2,
       "reps": 3,
       "lapses": 0,
       "last_review": "2026-05-05T00:00:00Z"
     }
   }
   ```
   保持向下兼容，不改 JSON 文件结构

2. 新建 `deeptutor/services/fsrs/service.py`
   - **直接复制 Canvas `FSRSManager`（约 200 行）**
   - 仅需 `pip install fsrs`
   - 新增 `review_record(record_id, rating: int) -> Record`
   - 新增 `get_due_records(kb_name: str) -> list[Record]`

3. `deeptutor/capabilities/deep_question.py` 触发入口
   - 新增 "FSRS 检验模式"：调 `fsrs_service.get_due_records()` → 直接送 prompt 出题（不需 RAG 检索）

4. Web UI（`web/`）— Due Today 面板
   - Next.js component 展示 `GET /api/fsrs/due`
   - 答题后 `POST /api/fsrs/review` 提交 rating（1~4）

**工作量分解**：
- fsrs_manager 复制 + 服务封装：1d
- notebook Record schema 扩展：0.5d
- API endpoint（due / review）：1d
- Web UI due panel：1d（MVP 可先用 CLI `deeptutor fsrs due` 代替延后 UI）
- 测试：0.5d

### 3.6 3 阶段实施路线图

| Phase | 时间 | 内容 | 风险 |
|---|---|---|---|
| **Phase 1** | T+0 ~ T+5d | **能力 1 vault 扫描**：`add_vault()` + document_loader `.md` section 切片 + frontmatter metadata。目标：DeepTutor 能吃 Canvas vault，AI 讲解时能 cite 笔记片段 | 低。link_folder 机制已有，改动局限 document_loader |
| **Phase 2** | T+5 ~ T+12d | **能力 2.1 callout 注入**（4-6d）+ **能力 3 FSRS**（4-5d）**并行**。目标：学习闭环成型 — 讲解时感知 `[!error]`，答题后算 next_due | 中。callout post-filter 需实测 recall 效果；FSRS notebook schema 扩展需保向下兼容 |
| **Phase 3** | T+12 ~ T+20d | **能力 2.2 双链 2-hop**（路线 A NetworkX）。目标：检验白板出题时拉 2-hop 子图，按用户拆解链条出题 | 中。obsidiantools 在 DeepTutor 环境需新增依赖；LightRAG 接入路线预留接口防架构推翻 |

**总工程量**：~18-26 人天（含测试），1 人全职约 4-6 周；若 Phase 1+2.1+3 并行推进，**3 周可完成主要功能**。

### 3.7 3 种集成模式权衡

#### A. 完全迁入 DeepTutor（重写 Canvas 28 服务）

| 维度 | 评估 |
|---|---|
| 工程量 | 60-80d（重写 sync_service, episode_worker, mastery_engine, review_service, exam_service 等核心）|
| 风险 | 🔴 极高。Canvas 80+ 测试覆盖；mastery BKT + FSRS 已验证；重写破坏测试基线；DeepTutor active dev 持续 API 变更 |
| 维护负担 | 单 repo，但 fork DeepTutor 后 upstream 合并代价高 |
| 结论 | ❌ 不推荐 |

#### B. 双后端（推荐）⭐

```
DeepTutor → chat / quiz / RAG / Book Engine / Memory (SUMMARY+PROFILE)
Canvas backend → vault sync / Obsidian plugin / error_candidates / mastery BKT+FSRS / Neo4j Graphiti episode
```

桥接方式：
- Canvas backend 暴露 `/api/v1/vault/notes_context` 给 DeepTutor（返回当前节点 wikilink 邻居 + callout）
- 或通过 Canvas MCP server（`backend/app/mcp/server.py` 已实现）作为工具注入 DeepTutor agent tool chain

| 维度 | 评估 |
|---|---|
| 工程量 | 18-26d（3 项能力改造）+ 约 3d bridge API |
| 风险 | 🟠 中。两套 backend 版本兼容；DeepTutor upstream 改动 capabilities/ 接口需同步适配 |
| 维护负担 | 中。两 repo 但职责清晰；变更隔离 |
| 结论 | ✅ **推荐** |

#### C. DeepTutor as Library（抽取 RAG/memory 模块到 Canvas backend）

| 维度 | 评估 |
|---|---|
| 工程量 | 20-30d。DeepTutor 无 `pip install` 路径（应用而非库），改造解耦量大 |
| 风险 | 🟠 高。内部模块耦合深（book/engine.py → capabilities/ → services/rag），抽取拉入大量依赖；Next.js UI 完全无法复用 |
| 维护负担 | 单 repo，但每次 upstream 更新需手动 cherry-pick |
| 结论 | ❌ 不推荐（除非只需 RAG 部分且愿维护 fork）|

### 3.8 风险清单 + 缓解

| 风险 | 严重度 | 缓解 |
|---|---|---|
| **DeepTutor upstream 冲突**（active dev，昨日 commit）| 🔴 高 | Fork 独立分支改造，定期 rebase；改动集中在 `document_loader.py` + 新增文件，不碰 `capabilities/` 核心流 |
| **LightRAG ETA 未公开** | 🟠 中 | Phase 3 用 NetworkX 轻量版，抽象 `KGBackend` protocol，LightRAG 来时只换实现层 |
| **SimpleVectorStore 无 metadata pre-filter** | 🟠 中 | Phase 2 用 post-rerank（Python 侧）；如效果差升级 ChromaDB（Canvas `tests/test_chromadb_migration.py` 可参考）|
| **Canvas 28 服务无需重写** | 🟢 低 | 架构 B 不动 Canvas 任何已有服务；通过 `mcp/server.py` 已有工具暴露 vault 上下文 |
| **DeepTutor Web UI 改动** | 🟠 中 | 隔离改动在新 route（`/vault-setup`, `/due-today`）；FSRS 面板 MVP 用 CLI 代替延后 UI |
| **obsidiantools 新依赖** | 🟢 低 | Phase 1 纯 Python regex 替代；Phase 3 才考虑引入；如引入设为 optional extra `[obsidian]` |
| **py-fsrs 新依赖** | 🟢 低 | 复制 Canvas `FSRS_AVAILABLE` fallback 机制 |

---

## 第四部分：综合实施方案（基于架构 B）

### 4.1 双后端职责划分

#### Canvas Backend（保留，不动）

- `backend/app/services/sync_service.py`（Outbox + Segment Commit + MERGE Neo4j）
- `backend/app/services/wikilink_graph_service.py`（NetworkX BFS）
- `backend/app/services/candidate_service.py`（error_candidates pipeline）
- `backend/app/services/episode_worker.py`（**Graphiti 唯一真实实例**）
- `backend/lib/memory/temporal/fsrs_manager.py`（py-fsrs 4.5）
- `backend/app/services/autoscore.py`（4 维 SOLO Rubric × 3 投票）
- `backend/app/services/review_service.py`（FSRS 评分 → 复习触发）
- `backend/app/mcp/server.py`（14 工具暴露给 agent）

#### DeepTutor Backend（改造）

- `deeptutor/services/rag/pipelines/llamaindex/document_loader.py`（能力 1+2.1）
- `deeptutor/knowledge/manager.py`（add_vault 入口）
- `deeptutor/services/rag/pipelines/llamaindex/storage.py`（callout post-filter）
- `deeptutor/services/rag/smart_retriever.py`（callout + 2-hop 路由）
- `deeptutor/capabilities/deep_question.py`（callout + 子图 prompt）
- `deeptutor/services/notebook/service.py`（FSRS schema）
- `deeptutor/services/fsrs/service.py`（**新建**，复制 Canvas FSRSManager）
- `deeptutor/knowledge/wikilink_graph.py`（**新建**，NetworkX BFS）
- `deeptutor/api/`（新增 fsrs / vault endpoints）
- `web/`（vault 输入 + Due Today 面板）

### 4.2 新增 Bridge API

| 端点 | 用途 | Owner |
|---|---|---|
| `GET /api/v1/vault/notes_context?node_id=X` | 返回邻居 + frontmatter + 错误历史 | Canvas |
| `POST /api/v1/error/candidate-from-deeptutor` | DeepTutor 检测错误时回调 | Canvas |
| `POST /api/v1/score/autoscore` | DeepTutor 答题后调 4 维评分 | Canvas |
| `GET /api/fsrs/due` | 今日到期题目 | DeepTutor |
| `POST /api/fsrs/review` | 提交答题 rating | DeepTutor |
| `POST /api/vault/add_vault` | 索引 vault 文件夹 | DeepTutor |

### 4.3 端到端集成测试

```
1. 用户在 Obsidian 节点 [[admissibility]] 写 [!error]+ 我把 precedent 当成 holding
2. Cmd+Shift+A → Canvas backend 写入 frontmatter error_candidates[]
3. 用户在 DeepTutor Web 触发 /start_exam → Book Engine 生成检验白板
4. 题目应包含"[[admissibility]] 与 [[holding]] 的辨析"（命中历史错误）
5. 用户答题 → Canvas autoscore 评分（4 维 SOLO Rubric × 3 投票）→ FSRS 更新 next_due
6. 7 天后 Dashboard 显示该节点 due → 用户再次考察
7. 验证"诱导再犯"陷阱是否被识破
```

---

## 第五部分：5 个决策点（请用户审计判断）

### Decision 1：架构 B 双后端 vs 其他路径

**Claude 推荐**：B（双后端）

**选项**：
- A. 完全迁入 DeepTutor（60-80d，🔴 极高风险，重写 28 服务）
- **B. 双后端**（18-26d + 3d bridge API，🟠 中风险）⭐
- C. DeepTutor as Library（20-30d，🟠 高风险，UI 无法复用）

### Decision 2：3 项能力实施顺序

**Claude 推荐**：Phase 1 → Phase 2（2.1+3 并行）→ Phase 3

**选项**：
- 严格 1 → 2.1 → 3 → 2.2（5d → 6d → 5d → 6d = 22d）
- **Phase 2 并行**（2.1+3 同时，团队 2 人则 12d）⭐
- 先做 Phase 3（双链 multi-hop）→ 用户最快看到效果但数据基础残缺

### Decision 3：双链 multi-hop 路线选择

**Claude 推荐**：路线 A（NetworkX 轻量）

**选项**：
- **A. NetworkX 轻量（5-6d）**⭐ 抽象 KGBackend protocol，LightRAG 来时换实现
- B. 等 LightRAG 集成（ETA 不确定，~5d）
- C. 自建 Neo4j（8-10d，与 LightRAG 冲突风险）

### Decision 4：Canvas 错误管理 + BKT/FSRS 是否完全保留

**Claude 推荐**：完全保留（架构 B 核心）

**选项**：
- **完全保留 Canvas 错误 pipeline + FSRS**⭐（DeepTutor 桥接调用）
- 部分迁入 DeepTutor（FSRS 复制，错误 pipeline 重写）→ 工程量增加
- 完全迁入（同 Decision 1 路径 A）

### Decision 5：是否先修 round-14 的 4 残缺再开始 DeepTutor 改造

**背景**：round-14 已确诊 4 个 Graphiti 残缺（只写不读 / group_id 旧格式 / embedding 退化 / 零同步），需 6-8 天修复。架构 B 桥接调用 Canvas backend 时，这 4 残缺是否影响 DeepTutor 学习闭环？

**Claude 推荐**：先修部分（embedding search 接入 + 错误读取路径）

**选项**：
- A. 先修 round-14 全部 4 残缺（6-8d）→ 总工程量 24-34d
- **B. 先修 2 项关键（embedding + 错误读取，~3-4d）**⭐ → 总 21-30d
- C. 不修，直接 DeepTutor 改造（DeepTutor 自有 RAG，可绕过 embedding 残缺）→ 总 18-26d 但错误闭环不完整

---

## 附录 A — 5 Stage 桥接调用示例

### Stage A 调用流（vault 索引）
```
用户 → DeepTutor Web "/vault-setup" 输入 ~/canvas-vault
  → DeepTutor knowledge/manager.py::add_vault()
  → document_loader.py 解析 .md（frontmatter + wikilinks + callouts）
  → LlamaIndex VectorStoreIndex.from_documents()
  → 同时通知 Canvas backend POST /api/v1/sync/vault-indexed（让 Canvas Outbox 也同步）
```

### Stage C 调用流（chat-with-context）
```
用户 → DeepTutor Web "/chat" 提问
  → Deep Solve plan 阶段调 Canvas GET /api/v1/vault/notes_context?node_id=X
  → 拿到邻居 + frontmatter + errors[] + tips[]
  → 注入 Deep Solve KB context 前缀
  → ReAct 推理（含 callout-aware retrieval）
  → write 答案 + cite 笔记片段
```

### Stage F 调用流（检验白板生成）
```
用户 → DeepTutor "/start_exam" 选原白板
  → Book Engine spine generation
  → 上游调 Canvas GET /api/v1/exam/acp-context?board_id=X（拿 ACP 5 层数据）
  → CONCEPT_GRAPH block 调 Canvas GET /api/v1/kg/multi-hop?seed=X&depth=2
  → QUIZ block 用 deep_question.py（注入 callout + 子图）
  → compiler.py 组装为 Book
  → 用户在 DeepTutor Web 答题
```

### Stage G 调用流（评分 + FSRS）
```
用户答题提交 → DeepTutor 触发评分
  → POST Canvas /api/v1/score/autoscore（4 维 SOLO Rubric × 3 投票）
  → Canvas 返回 score
  → DeepTutor POST /api/fsrs/review（更新 next_due）
  → 同时通知 Canvas POST /api/v1/mastery/update（更新 BKT mastery）
  → Canvas episode_worker 写 Graphiti episode
```

---

## 附录 B — DeepTutor v1.3.7 关键事实

- 仓库：https://github.com/HKUDS/DeepTutor
- 中文 README：https://github.com/HKUDS/DeepTutor/blob/main/assets/README/README_CN.md
- 论文：arxiv 2604.26962（2026-04-10）
- License：Apache 2.0（可商用、可改造）
- 最近 commit：2026-05-04（active development）
- Stars：23,400+ / Forks：3,100+
- 部署：CLI / Docker / Web app / Wizard installer
- 6 大 capability：Chat / Deep Solve / Quiz Generation / Deep Research / Math Animator / Visualize
- 加上：Book Engine / TutorBot / Persistent Memory / RAG Pipeline / 自定义 Skills
- 路线图：LightRAG 集成（HKUDS 自家 KG-based RAG，34.8K stars）/ 多用户认证 / UI 主题

---

## 附录 C — 用户批注链 vs 调研发现对照

| 用户批注                                                  | 来源                | 调研发现（本报告）                                                 |
| ----------------------------------------------------- | ----------------- | --------------------------------------------------------- |
| "我们要不要直接 先在这个 https://github.com/HKUDS/DeepTutor 来改造" | round-15:155      | DeepTutor 整体匹配度 6/10，**架构 B 双后端可行**（§2.1 + §3.7）          |
| "vault 文件夹检索精确返回笔记片段"                                 | round-15:155 能力 1 | DeepTutor 已有 link_folder，需扩展 `.md` 解析。**4-5d**（§3.2）      |
| "批注 + 双链拆解链条理解"                                       | round-15:155 能力 2 | 拆为 2.1 callout（4-6d）+ 2.2 双链 multi-hop（5-6d）（§3.3 + §3.4） |
| "FSRS 配合 — 何时使用检验白板"                                  | round-15:155 能力 3 | DeepTutor 无 FSRS，**复制 Canvas FSRSManager**。4-5d（§3.5）     |
| "节点理解程度更倾向批注驱动"                                       | round-15:44       | callout-aware RAG（能力 2.1）+ Canvas BKT+FSRS 桥接（架构 B）       |
| "Graphiti 多段推理在 GraphRAG 优秀，所以选它"                     | round-15:62       | 保留 Canvas Graphiti，DeepTutor LightRAG 不替代（§2.5）           |
| "Anki FSRS 根据答题判断掌握度推算复习时间"                           | round-15:91       | 是的，能力 3 复制此机制；DeepTutor Question Bank 持久化但无 FSRS（§3.5）    |
| "我只是要找到最成熟最稳定的方案"                                     | round-15:92       | 架构 B 利用 DeepTutor 23K stars + Canvas 28 已验证服务，最稳定路径       |

---

## 状态

- **报告生成**：2026-05-06 ≈00:30
- **下一步**：等用户审计 5 个决策点
- **依赖关系**：
  - 架构 B 桥接前提：Canvas 28 服务无需重写（已验证）
  - DeepTutor 改造前提：Apache 2.0 License + active development
  - LightRAG 路线图：不阻塞，作为 Phase 3+ 可选项
- **后续动作**：用户审定后，按 5 个决策结果转 `_decisions/` + 起草 Stage A-G 桥接 spec + DeepTutor fork 计划
