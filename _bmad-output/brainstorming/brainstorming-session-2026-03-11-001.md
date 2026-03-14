---
stepsCompleted: [1, 2, 3]
inputDocuments: []
session_topic: 'Canvas Learning System 记忆系统 2 深入 — 学习情况跟踪'
session_goals: 'Graphiti 实体关系设计、理解程度量化、Agent 生成闭环、FSRS 协作、出题机制、Claude Code 记忆同步'
selected_approach: 'ai-recommended'
techniques_used: ['Question Storming', 'Five Whys + Assumption Reversal', 'Cross-Pollination', 'Deep Explore (社区/论文验证)', 'Morphological Analysis']
ideas_generated: []
context_file: ''
---

# Brainstorming Session Results

**Facilitator:** ROG
**Date:** 2026-03-11 ~ 2026-03-13（跨 3 session 完成）

## Session Overview

**Topic:** Canvas Learning System 记忆系统 2 深入 — 学习情况跟踪

**Goals:**
1. Graphiti 实体和关系设计 — 具体要记录什么实体及其关系
2. 理解程度判断 — 如何量化"真正理解了"
3. Agent 生成闭环 — 学习历史如何反馈到 Agent 回复
4. FSRS 复习调度配合 — FSRS 与 Graphiti 的协作分工
5. 出题/检验白板机制 — 收藏复习点的交互与出题逻辑
6. Claude Code 记忆同步 — Graphiti 与 .claude/memory 的同步机制

### Context Guidance

_已有上下文（来自 Graphiti 搜索和代码探索）：_
- Graphiti canvas-dev 中无学习跟踪相关记录，已有知识均为检索管道（bge-m3、混合搜索、chunking）
- FSRS 已实现于 `src/memory/temporal/fsrs_manager.py`，使用 py-fsrs，有 score→rating 转换，但与主流程断开
- Graphiti Bridge Service 定义了 Misconception/ProblemTrap/GuidedThinking 等实体类型
- LearningMemoryClient 以 JSON 存储学习 episodes
- 15 个 Agent 类型，React Agent 模式，Gemini 驱动
- Context Enrichment 存在但默认禁用

---

## 已完成讨论记录（2026-03-11 session，因 context 压缩恢复）

### 议题 0：Graphiti 技术选型验证 ✅

**结论：合理，但需混合使用策略**
- 5 个天然匹配点（Episode/Custom Entity/Edge/Temporal/Semantic Search）
- 2 个 Gap（精确查询需 Cypher、LLM 成本需 Gemini Flash）
- **三层分工**：Graphiti（语义搜索）+ Cypher（精确/聚合查询）+ FSRS（复习调度）

### 议题 0.5：FIRe 模型调研 ✅（是否采纳待决）

**发现：Math Academy 的 FIRe (Fractional Implicit Repetition)**
- Prerequisite Graph + Encompassing Graph 双图结构
- 隐式 credit 传播 + 复习压缩 + 失败向前传播
- FSRS 管"什么时候"，KG 管"什么和为什么"
- 对比方案：KARL(2024)、LECTOR(2025)、Obsidian SR Recall、ZKMemo
- **⚠️ 未决：FIRe 是否正式采纳 — 影响整个复习引擎架构**

### 议题 1：当前代码 Gap 分析 ✅

**8 个 Gap 按优先级：**
- P0：概念依赖图不存在 + Canvas Node→Concept 映射缺失
- P1：CardState 无依赖感知 + 隐式 credit + 复习压缩
- P2：Agent 不读学习历史 + 失败传播 + CanvasAssociation 未连接
- 好消息：CanvasAssociation schema 已有 prerequisite 类型（Story 36.5）

### 议题 2a：概念粒度与自动化 ✅

**纠正：Canvas Node = Concept 已是系统现状**
- node.id = concept_id, node.text = 概念描述, node.color = 理解状态
- 手动标注不可扩展（插件是多学科通用工具）
- 自动化策略：Wikilink 分析 + Canvas edge 分类 + LLM 辅助

### 议题 3a：产品形态重新审视 ✅ ⭐ 重大方向变更

**用户反馈：当前 Canvas 架构不符合核心需求**

核心工作流重新定义：
1. 丢不懂内容 → AI 拆分解释 → 理解
2. 关键误区 → 保存为卡片（有熟练度）
3. 出题 + 检验白板 → 针对弱点考察
4. 记忆系统 1 = 全局笔记索引 RAG
5. 记忆系统 2 = Graphiti 学生弱点画像

**技术发现：**
- Canvas API 是只读的，当前 JSON hack 是技术债务
- 后端核心引擎（BKT+FSRS+Agent）已完全不依赖 Canvas
- ~2000 行文件 IO + 颜色监控需替换，核心引擎完全可复用
- **架构决策方向：Canvas 降级为输入源 + 自建 React 面板（card-centric）**

### 议题 3b：Agent 闭环 — 学习历史读取方案 ✅

**调研结论：7 大经社区/论文验证的成熟模式**

1. **RAG 混合搜索**（Graphiti 94.8% DMR）— GraphRAG 多跳胜 Naive RAG
2. **ITS 经典模式**：LPITutor 双层 Prompt + OLM 掌握度向量 + KT→Prompt 管道
3. **Prompt 三层架构**：L1 角色(不变) / L2 学生上下文(每轮更新,靠前) / L3 当次请求
4. **Lost in the Middle**（Liu 2023）：学生模型放 prompt 靠前位置
5. **Token 预算**：student 2-3K + RAG 2-4K = 总 5-10K tokens
6. **Blackboard 架构** → LangGraph State TypedDict，Agent 专属 context 配置
7. **真实系统验证**：OATutor 完成率 +23%，Math Academy 复习效率 +40%+

**推荐实现架构：**
- **Context Builder Node**（新增）→ Router → Agent → **Observer Node**（新增）
- Context Builder：启用 context_enrichment + Graphiti search + Cypher mastery + FSRS due
- Observer：提取学习事件 → Graphiti add_memory + 更新 FSRS + 更新 mastery
- **结论：不需重写，核心 = 2 个新节点 + prompt 模板改造**

### 综合路线图 ✅

**Phase 0（最高优先 1-2 周）**：解决"Agent 不读历史"
- 0.1 Mastery 向量序列化注入 ~100 行
- 0.2 Context Builder 逻辑 ~300 行
- 0.3 Prompt 3 层改造
- 0.4 Observer 逻辑 ~200 行

**Phase 1（高优先 2-3 周）**：Agent 精细化
**Phase 2（中优先 3-4 周）**：FIRe 相关（阻塞于采纳决策）
**Phase 3（低优先 4-6 周）**：FIRe 高级功能
**Phase 4（可选并行）**：LangGraph 升级

### 议题 2b：理解程度量化 — 两阶段五类弱点模型 ✅

**核心方案：两阶段评估**

- **Phase 1（被动观察）**：Observer 分析用户与 Agent 的对话历史，提取初步掌握度判断
- **Phase 2（主动检验）**：基于弱点画像，生成针对性题目进行点对点突破

**五类弱点分类（经 Deep Explore 修订）：**

| 弱点类型 | 通俗解释 | 检测方式 | 复习策略 |
|---------|---------|---------|---------|
| 1. 概念误解 Misconception | "记错了/理解反了" | 关键概念复述对比 | 多角度呈现同一概念 |
| 2. 推理错误 Reasoning Error | "每步都对但推不到终点" | 多步推理链检验 | 相似结构不同内容练习 |
| 3. 前置知识缺口 Prerequisite Gap | "基础没打好" | 依赖链回溯测试 | 顺序解锁前置知识 |
| 4. 理解深度 Understanding Depth | "懂了一点但不透彻" | SOLO 5 级量表 | 逐级提升难度 |
| 5. 元认知偏差 Metacognitive Gap | "以为自己懂了其实没懂" | 预估 vs 实际得分差距 | 先自我解释再验证 |

**推理错误子类型**：程序性错误（步骤遗漏）、策略性错误（方法选择）、推断性错误（逻辑跳跃）、累积性错误（多步偏移）

**度量维度（横切所有类型，非独立类别）**：答题时间、错误率、求助频率

**Deep Explore 验证**：搜索 25+ 篇论文，发现 3 个结构问题后修订——难度从独立类别改为度量维度、理解深度映射 SOLO 5 级、新增元认知偏差类别

**已确认决策**：[Decision-Review] PENDING

---

### 议题 4：FSRS + Graphiti + 策略适配器 三角协作 ✅

**核心模型：三个"老师"各司其职**

| 角色 | 负责什么 | 类比 |
|------|---------|------|
| **FSRS**（日程表老师） | **什么时候**复习 | 根据遗忘曲线安排下次复习时间 |
| **Graphiti**（档案老师） | **哪里薄弱** | 维护五类弱点画像，追踪历史表现 |
| **策略适配器** | **怎么复习** | 根据弱点类型选择最有效的复习方法 |

**五种策略适配器（对应五类弱点）：**

1. **误解矫正器** → 多角度呈现，打破错误理解
2. **推理训练器** → 相似结构不同内容，强化推理链
3. **前置解锁器** → 按依赖链顺序补足基础
4. **深度提升器** → 从简到难逐级深入（SOLO 级别）
5. **元认知校准器** → 先自我评估再看真实结果

**Karpicke Trap 警告**：设计时必须确保"主动回忆"（d=1.50 效应量）优先于"精细编码"（d=0.75），避免用户只看不练

**已确认决策**：[Decision-Review] PENDING

---

### 议题 5：出题/检验白板机制 ✅

**与 Session D 前端设计衔接**

两种检验模式（来自 Canvas UI.pen 设计）：
1. **节点内检验** — 在知识节点上下文中考察
2. **独立检验空间（检验白板）** — 画布式思维发散验证

**检验白板核心设计：**
- 画布左侧：颜色编码的题目节点（红=未答/错误、紫=部分理解、青=基本正确、绿=完全掌握）
- 画布右侧：AI Q&A 侧边栏 + Pin to Canvas
- 支持从 AI 回复中选取内容 → 拖出为新节点（发散式学习）

**个人理解模式（Personal Understanding Mode）：**
- AI 引导自我解释 → 文本编辑器 → AI 理解评估（如 73/100）→ 维度打分反馈

**Deep Explore 验证（评级 B+）+ 4 项改进（已确认）：**

| # | 改进 | 原因 | 方案 |
|---|------|------|------|
| 1 | AI 打分加追问验证 | LLM 评分系统性偏宽松 | 加 follow-up probing + 多维度分别展示 |
| 2 | 辅助渐隐机制 | 防止认知卸载/依赖 | 基于 FSRS/SOLO 定义渐隐阶段和自动触发 |
| 3 | 校准反馈 | 测量元认知偏差 | 用户先预估分数再看 AI 评分，差距 = 偏差 |
| 4 | 检验顺序调整 | 2024 Frontiers 实证 | 先概念图后自由回忆效果更好 |

**差异化确认**：竞品分析证实无现有产品同时整合 canvas + retrieval practice + self-explanation + AI scoring + metacognitive monitoring

**已确认决策**：[Decision-Review] PENDING

---

### 议题 6：Claude Code 记忆同步 — 双系统单向同步 ✅

**双系统分工：**

| 系统 | 角色 | 类比 |
|------|------|------|
| **Graphiti**（graphiti-canvas MCP） | 长期档案 — 所有历史完整存储，精确搜索 | 档案室 |
| **Claude Code Memory**（.claude/memory/） | 当前摘要 — 每次对话自动加载的关键提醒 | 桌面便签 |

**同步机制：Graphiti → Memory 单向同步**

- **同步时机**：Session 结束时（记录 `[Session-End]` 的同时）
- **同步内容**：
  1. `project_active_work.md` — 当前进度和下一步（覆盖更新）
  2. `project_decisions.md` — 已确认的方向性决策（只增不删）
  3. `user_profile.md` — 用户画像（长期积累）
- **责任方**：每个 session 的 AI 自己负责

**Deep Explore 验证（评级 A-）+ 4 项改进（已确认）：**

| # | 改进 | 来源验证 | 方案 |
|---|------|---------|------|
| 1 | 矛盾检测 | OpenAI Cookbook 警告"最敏感环节" | 同步时检查新旧信息是否冲突 |
| 2 | 中间检查点 | 多 agent 并发研究 | 长 session 每 N 轮轻量同步，不只依赖结束时 |
| 3 | 相关度衰减 | Claude Code"每行消耗 context 预算" | 已完成工作自动降级/归档，控制 200 行 |
| 4 | 并发冲突兜底 | Multi-Agent Memory 综述 | last-writer-wins + 版本标记 |

**社区验证**：Mem0（YC，26% 准确率提升）、OpenAI Agents SDK（session notes→global notes 同模式）、MAGMA 多图架构（2026 论文）

**已确认决策**：[Decision-Review] PENDING

---

## 已确认决策汇总

- [x] **Phase 0 优先策略** — 先解决 Agent 闭环（Context Builder + Observer + Prompt 3 层），不依赖 FIRe
- [x] **FIRe 推迟决策** — 等 Phase 0 完成后再决定是否采纳
- [x] **议题 2b** — 两阶段五类弱点模型 + 度量维度
- [x] **议题 4** — FSRS + Graphiti + 策略适配器三角协作
- [x] **议题 5** — 检验白板 + 个人理解模式 + 4 项改进
- [x] **议题 6** — 双系统单向同步 + 4 项改进

## 独立验证审查结果（2026-03-14 Review Session）

### 审查总览

| # | 决策 | 审查结论 | 风险等级 |
|---|------|---------|---------|
| 1 | Phase 0 优先策略 | **有条件通过** — 需增加最小依赖图 | 高 |
| 2 | FIRe 推迟 | **有条件通过** — 需确保架构兼容性 | 高 |
| 3 | 五类弱点模型 | **需修改** — 降为 3 类 + 降级元认知检测 | 严重 |
| 4 | 三角协作 | **需修改** — 解决 FSRS-Graphiti 假设矛盾 | 严重 |
| 5 | 检验白板 4 项改进 | **需修改** — 追问机制+校准反馈有根本缺陷 | 高 |
| 6 | 记忆同步 4 项改进 | **需修改** — LWW 应升级 + 单向同步风险 | 严重 |

---

### 决策 1+2：Phase 0 优先策略 + FIRe 推迟

**审查结论：有条件通过**

**核心风险：**
1. ITS 学术共识：Domain Model（概念依赖图）是四模型架构的第一个必须实现的组件，没有它 mastery 向量没有结构支撑
2. Justin Skycak 原文确认 FIRe 需要两张图（前置图+包含图），缺少包含图导致复习信用错误下传
3. COMMAND 算法（EDM 2016）证明前置知识图和学生模型是耦合的，分开实现后续需大改
4. Phase 0 本质是"有记忆的 chatbot"，效果提升估计 10-20%（完整 ITS 为 40-60%）
5. **最大风险：Phase 0 验证的是"记忆有用"而非"结构化教学有用"** — 得到虚假的方向确认

**被忽略的方案：**
- 最小依赖图（20-50 个核心概念的小型前置图），比完整 FIRe 低 90% 工作量但解决结构缺失
- LLM 自动生成初始依赖图（已有成熟 pipeline，Frontiers 2026）

**修改建议：Phase 0 同时构建最小概念依赖图（~300 行），确保 mastery 有结构支撑**

**验收标准：**
- AC1.1: Phase 0 Agent 输出质量 vs 纯 chatbot A/B 测试，5 个真实学习场景，盲评差异显著性 p<0.05
- AC1.2: mastery 向量数据结构兼容图结构扩展（代码审查确认无需重写核心数据模型）
- AC1.3: Context Builder 的 Graphiti 查询延迟 < 500ms（P95）
- AC1.4: Observer 事件提取准确率 > 80%（人工标注 50 个对话回合对照）

**测试用例：**
- 正常：学生学习 gradient descent，Agent 能引用之前学过的 linear regression 知识
- 边界：学生跳过前置知识直接学高级主题，Agent 是否能检测并引导回退
- 刁难：学生连续 3 次同一概念答错，Observer 是否正确记录为弱点而非随机失误

**退出条件：如果 Phase 0 Agent 与纯 chatbot 的盲评差距 < 15%，说明架构方向需重新评估**

---

### 决策 3：两阶段五类弱点模型

**审查结论：需修改**

**核心风险：**
1. LLM 检测误解准确率仅在数学代数达 83.9%（Springer 2025），跨领域无验证
2. 推理错误 vs 概念误解区分在实践中极其困难 — F1 > 0.67 仅在代码场景
3. **Nature Communications 2024 直接否定**：所有被测 LLM 存在"重大元认知缺陷"，用无元认知的工具检测学生元认知偏差 = 用瞎子指路
4. Dunning-Kruger 效应在 LLM 中成立（arXiv 2603.09985），LLM 自身有元认知偏差
5. 细粒度分类收益递减：KT 社区警告"更细粒度不一定提供更优质信息"
6. 五类弱点数据稀疏问题：学习时间短时五个桶分散的数据比两个桶更不可靠

**修改建议：**
- 降为 3 类弱点：**知识缺失**（合并 misconception + prerequisite gap）、**推理困难**（reasoning error）、**理解深度不足**（understanding depth）
- 元认知偏差从独立类别**降级为度量维度**（保留"预估 vs 实际"信号，但不作为分类依据）
- SOLO 简化为 3 级（表面/关联/拓展）而非 5 级

**验收标准：**
- AC3.1: LLM 弱点分类准确率 — 人工标注 100 个真实对话片段作为 ground truth，LLM 分类准确率 > 70%
- AC3.2: 分类结果可操作性 — 不同分类是否导致不同且有效的策略（A/B 测试）
- AC3.3: 数据稀疏场景 — 学习 < 5 轮对话时分类结果是否稳定（不频繁翻转）
- AC3.4: 跨学科泛化 — 至少在 2 个不同学科（如 CS + 数学）上验证分类效果

**测试用例：**
- 正常：学生解释错误概念，系统正确分类为"知识缺失"
- 边界：学生概念正确但推理步骤遗漏，系统能否区分为"推理困难"而非"知识缺失"
- 刁难：学生给出部分正确、部分错误的混合回答，系统如何分类

**退出条件：如果 LLM 分类准确率 < 60%（随机基线 33%），降为 2 类（掌握/未掌握）**

---

### 决策 4：FSRS + Graphiti + 策略适配器三角协作

**审查结论：需修改**

**核心风险：**
1. **FSRS 与 Graphiti 基础假设互相矛盾** — FSRS 假设知识项孤立，Graphiti 假设知识项关联（Content-aware SR 论文确认）
2. 没有公开数据集支持 FSRS+KG 集成训练
3. 三系统错误归因无法自诊断 — FSRS 说时机问题，Graphiti 说弱点诊断问题，适配器说策略选择问题
4. AIED 2024 论文"Adaptive Learning is Hard"：多策略组合和优先级排序是根本挑战
5. 59% 的自适应学习研究报告效果提升，41% 无提升或负面效果（PMC 2024 meta-analysis）

**修改建议：**
- 明确分层：FSRS 管"卡片级别"复习时机（保持独立性假设），Graphiti 管"概念级别"弱点追踪（发挥关联优势）
- 策略适配器简化为 3 种（对应 3 类弱点而非 5 类）
- 添加 fallback：当三系统不一致时，默认回退到最简单策略（"再练一次"）

**验收标准：**
- AC4.1: 三系统数据流端到端测试 — 从用户作答到策略输出全链路无断裂
- AC4.2: 策略适配器选择准确率 — 人工判断 50 个案例中适配器选择是否合理，准确率 > 70%
- AC4.3: 错误级联测试 — 故意注入一个系统的误判，观察对另两个系统的影响范围
- AC4.4: FSRS 调度与 Graphiti 弱点信息不冲突 — 不出现"FSRS 说该复习但 Graphiti 说已掌握"的矛盾

**测试用例：**
- 正常：学生某概念 FSRS 到期 + Graphiti 标记为弱点，系统选择正确策略
- 边界：FSRS 说不用复习（stability 高）但 Graphiti 新发现该概念弱点，谁优先？
- 刁难：三个系统给出三个不同建议，fallback 是否正确触发

**退出条件：如果三系统协调开销 > 收益（A/B 测试 vs 简单 FSRS-only 方案），简化为 2 系统**

---

### 决策 5：检验白板 + 个人理解模式 + 4 项改进

**审查结论：需修改**

**核心风险：**
1. **HIGH: LLM 追问无法矫正自身评分偏宽松** — Self-Preference Bias 论文（2024）证实 LLM 对自身生成文本系统性打高分，同一模型追问偏差方向不变
2. **HIGH: 校准反馈公式（用户预估 − AI 评分 = 元认知偏差）** — AI 评分不准时测量的是噪音而非元认知
3. **MEDIUM: FSRS 保留率阈值为闪卡记忆设计**，迁移到"理解力渐隐"缺乏实证；持续支持在概念性知识上优于渐隐
4. **MEDIUM: 画布分屏 5 个并发认知任务** — 认知负荷过高
5. **MEDIUM: 4 色编码超过 3 色有效性下降** + 8% 男性用户色盲适用性问题
6. **LOW: 概念图先于自由回忆对基础薄弱学习者过难**

**修改建议：**
- 改进 1（追问）：追问 LLM 必须是独立的、不同系列的模型（如主评分用 Gemini，追问用 Claude），或引入人类评审
- 改进 3（校准）：需先解决 AI 评分可靠性（与人类评分相关性 > 0.7），才有意义引入校准
- 界面：采用渐进式展示（progressive disclosure），默认简洁模式，高级功能按需展开
- 颜色：3 色（红/黄/绿）+ 形状/图标辅助，兼顾色盲

**验收标准：**
- AC5.1: AI 评分与人类专家评分 Pearson 相关系数 > 0.7（50 个真实自我解释样本）
- AC5.2: 追问后评分变化幅度 — 追问机制应使初始偏高的分数平均下调 > 5 分
- AC5.3: 渐隐触发后用户完成率 — 渐隐后用户独立完成率 > 60%（低于则过早渐隐）
- AC5.4: 界面认知负荷 — 用户首次使用无辅助完成率 > 50%（否则界面过复杂）
- AC5.5: 校准反馈有效性 — 经过 5 轮校准训练后用户预估误差缩小 > 20%

**测试用例：**
- 正常：学生写正确解释，AI 给 80 分，追问验证后维持 78 分
- 边界：学生写流畅但错误的解释，AI 初始给 75 分，追问后是否降至 < 60 分
- 刁难：学生连续 3 次校准差距 > 20 分但方向交替（时高时低），系统如何处理

**退出条件：如果 AI 评分与人类评分相关性 < 0.6，暂停校准反馈功能，先攻克评分可靠性**

---

### 决策 6：双系统单向同步 + 4 项改进

**审查结论：需修改**

**核心风险：**
1. **语义矛盾检测最佳混合系统仅检出 60% 矛盾**，时态矛盾几乎无法自动检测
2. **LWW 并发写入 100% 丢失至少一方数据**，无审计痕迹
3. **36.9% 的多 agent 失败源于不一致共享状态**（arxiv 2603.10062）
4. **图谱→平面文件存在结构性信息降维损失**，关系结构无法在平面文件中表达
5. **Mem0 的 26% 准确率提升为自报数据**，未独立复现，Mem0g 在图谱场景性能更弱
6. **200 行 Memory 限制对活跃项目极紧张**，三文件合计空间有限
7. **用户手动编辑 Memory 文件在下次同步时被覆盖**，无任何警告

**被忽略的更成熟方案：** CRDT（Google Docs/Figma 级）、向量时钟（Dynamo 级）、MVCC

**修改建议：**
- LWW 升级为 append-only log + 定期 merge（保留所有写入，人工裁决冲突）
- 添加用户编辑保护：同步前 diff 检查，如用户有手动编辑则提示而非覆盖
- 矛盾检测降级为"变更日志"（记录什么变了）而非"自动裁决"
- 添加 session 崩溃恢复机制（中间检查点 + WAL 模式）

**验收标准：**
- AC6.1: 并发 session 写入测试 — 2 个 session 同时结束，数据完整性 > 95%
- AC6.2: session 崩溃恢复 — session 中途 kill -9 后，已产生知识丢失率 < 10%
- AC6.3: 用户手动编辑保护 — 手动编辑内容在下次同步后仍保留
- AC6.4: 200 行 Memory 承载量 — 经过 20 个 session 后 Memory 文件仍在 200 行内且信息密度合理
- AC6.5: 矛盾检测准确率 — 注入 20 条已知矛盾信息，检出率 > 50%

**测试用例：**
- 正常：单 session 正常结束，三个 Memory 文件正确更新
- 边界：用户手动在 project_decisions.md 中添加一条备注，下次同步后是否保留
- 刁难：2 个 session 同时写入不同决策到同一文件 + 第 3 个 session 立即读取，读到的内容是否一致

**退出条件：如果并发数据丢失率 > 5%，必须引入 CRDT 或至少 MVCC**
