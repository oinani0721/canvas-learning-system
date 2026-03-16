---
stepsCompleted: ['deep-explore', 'code-review', 'academic-validation', 'product-validation', 'design-tracing']
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/brainstorming/brainstorming-session-2026-03-11-001.md
  - docs/canvas-backend-research-report.md
session_topic: 'PRD Review — OLM 五维精通度设计验证'
session_goals: '验证 PRD 中 FR-MAST-03/FR-MAST-06 五维精通度展示设计的学术依据、代码可行性和商业先例'
selected_approach: 'adversarial-deep-explore'
techniques_used: ['对抗性代码审查(15模块)', '学术论文搜索(30+篇)', '成熟产品实践调研(10款)', '设计来源追溯', 'Graphiti跨session知识共享', '深度澄清翻译']
review_status: 'completed'
review_date: '2026-03-15'
review_agents: 7
review_papers: '30+'
review_products: 10
verdict: 'NOT SUPPORTED — 需修改PRD'
---

# PRD Review — OLM 五维精通度设计验证报告

**Session：** PRD-Review New Tab（深潜讨论）
**日期：** 2026-03-15
**调研规模：** 7 个独立 Agent、30+ 篇论文、10 款商业产品、15 个后端模块代码审查
**主 Tab 关联：** PRD Review 工作流 Step 1 完成，本报告供主 Tab 继续验证时引用

---

## 一、验证目标

PRD 中以下设计被质疑：

| PRD 条目 | 原文描述 | 质疑点 |
|---------|---------|--------|
| FR-MAST-03 | 用户可以通过白箱 OLM 查看每个节点的精通度详情（温度计总览→维度详情→趋势证据） | 用户看到温度计"全是疑惑"，数据是否可靠 |
| FR-MAST-06 | 多个信号源通过 Beta-Bayesian 融合为五维精通度 | 算法是否有学术依据，还是"乱编的幻觉" |
| Layer 2 创新 | Beta-Bayesian 五维融合 + 白箱 Inspectable OLM 三层渐进 UI | 是否有成熟案例支撑 |

---

## 二、Pencil UI 设计（本 session 产出）

在验证前，先在 Pencil (`UI 相关设计样式.pen`) 中创建了 OLM 三层展示的可视化 mockup：

- **Layer 1 — 温度计总览**：5 维彩色进度条（记忆强度/概念理解/应用能力/关联理解/元认知）+ 最弱标记
- **Layer 2 — 维度详情**：大字分数 + 4 个贡献信号 + 最近学习事件
- **Layer 3 — 趋势与证据**：柱状图趋势 + 证据溯源 + 算法来源标注

**设计完成后用户提出核心质疑：数据可靠吗？**

---

## 三、代码审查结论

### 审查范围：15 个后端模块

| 模块 | 5 维依赖？ | 评级 |
|------|----------|------|
| mastery_engine.py | 无 — 仅 1D `p_mastery` float | NO DEPENDENCY |
| mastery_state.py | 无 — 无 per-dimension 字段 | NO DEPENDENCY |
| mastery_store.py | 无 — 持久化标量 ConceptState | NO DEPENDENCY |
| mastery API endpoints | 无 — 仅标量接受/返回 | NO DEPENDENCY |
| behavior_tracker.py | 无 — 无 weakness_type 字段 | NO DEPENDENCY |
| fsrs_manager.py | 无 — 纯 FSRS 调度 | NO DEPENDENCY |
| strategy_selector.py | 无 — RAG 融合非精通度融合 | NO DEPENDENCY |
| graphiti_bridge.py | 无 — 学习事件分类，无维度追踪 | NO DEPENDENCY |
| agent_graph.py | 无 — Agentic RAG 管道 | NO DEPENDENCY |
| react_agent.py | 无 — 无精通度维度感知 | NO DEPENDENCY |
| agent_service.py scoring | 无 — 4 维评分 rubric 是**另一个系统** | DIFFERENT SYSTEM |
| canvas_utils.py scoring | 无 — 返回全零的 mock | MOCK/STUB |
| weakness_type references | 无 — 仅出现在测试 fixture | PLANNED NOT IMPL |
| mastery_config.json | 无 — 1D BKT 阈值配置 | NO DEPENDENCY |
| PRD/设计文档 | 仅文字描述 | PLANNED NOT IMPL |

### ⛔ 代码审查结论

**整个精通度系统从头到尾是 1 维的。** 零模块消费多维精通度，零模块生产多维精通度，零数据结构持有多维精通度。

**砍掉 PRD 五维精通度展示对现有代码零影响。**

---

## 四、学术论文验证

### 调研范围：25+ 查询，覆盖 EDM/AIED/LAK 会议、MIRT/CDM 心理测量学、BKT/DKT/SPARFA 知识追踪

### 有支撑的部分

| 设计要素 | 支撑证据 | 论文 |
|---------|---------|------|
| 记忆强度追踪（FSRS） | 数亿用户验证 | FSRS-6 论文、Anki |
| 单维掌握度（BKT） | 30 年学术验证 | Corbett & Anderson 1995 |
| Beta 分布用于单维追踪 | 2025 年论文验证 | PDT arxiv 2501.10050 |
| 知识有不同类型（概念框架） | 经典教育学理论 | Anderson & Krathwohl 2001 修订版 Bloom |
| 白箱展示比黑箱好 | 描述性调查研究 | Bull & Kay 2010/2016/2020 |

### 无支撑的部分

| 设计要素 | 搜索结果 | 关键问题 |
|---------|---------|---------|
| 每个知识点 5 维连续追踪 | **零论文** | 最接近的 CDM 是二值（会/不会），非连续百分比 |
| "Beta-Bayesian Evidence Accumulation" 5 维 | **零论文使用此术语** | 名称自造，PDT 仅验证了 1 维 |
| 单用户数据可行性 | **数学不成立** | MIRT 需 7 题/维度/KC = 35 题/KC 最低；5 维 × 100 KC = 3500 题，用户全课程仅 500-2000 题 |
| 自动估计元认知 | **Nature Communications 2024 直接否定** | 所有 LLM 存在"重大元认知缺陷"，Area9 靠显式自报告 |
| 自动估计关联理解 | **需开放式评估** | 选择题无法推断 |
| AI 评分可靠性 | **Self-Preference Bias 2024** | LLM 系统性偏高，与人类专家 Pearson 相关性未验证 |
| FSRS-BKT 假设兼容 | **Content-aware SR 论文确认矛盾** | FSRS 假设孤立 vs BKT/Graphiti 假设关联 |

### 关键论文引用

| 论文 | 关键发现 | 与本 PRD 的关系 |
|------|---------|---------------|
| PDT (arxiv 2501.10050, 2025) | Beta 分布追踪成功率 per skill | 支撑 1 维 Beta，不支撑 5 维 |
| Liu et al. 2021 KT Survey | 知识追踪全面综述 | 无 per-KC 多维连续追踪先例 |
| Lan et al. JMLR 2014 SPARFA | 稀疏因子分析发现潜在概念 | 维度自动发现 vs 预定义，5 维不适用 |
| Coetzee 2014 Sample Size | BKT 需 25+ 学生/KC 收敛 | 单用户场景致命 |
| MIRT Reckase 2009 | 多维 IRT 需 7 题/因子 | 5 维需 35 题/KC，不可行 |
| Nature Comms 2024 | LLM 存在重大元认知缺陷 | 直接否定自动元认知检测 |
| Self-Preference Bias 2024 | LLM 系统性给自己打高分 | AI 评分不可靠 |
| Gervet JEDM | 简单模型常优于复杂模型 | 反对过度维度化 |
| Shayan 2017 BKT Identifiability | 1D BKT 已有可辨识性问题 | 5D 会严重恶化 |

---

## 五、商业产品验证

### 调研范围：10 款主流自适应学习产品，覆盖 6 亿+ 用户

| 产品 | 用户规模 | 内部维度 | 用户看到的 | Per-KC 多维？ |
|------|---------|---------|----------|-------------|
| Khan Academy | 100M+ | BKT 多参数 | 1 维（3 档标签） | ❌ |
| ALEKS | 百万级 | 知识空间理论 | 1 维（饼图二值） | ❌ |
| Duolingo | 500M+ | Birdbrain 算法 | 1 维（经验值） | ❌ |
| Carnegie Learning | 百万级 | BKT P(known) | 1 维（进度环） | ❌ |
| IXL | 15M+ | 多因子 SmartScore | 1 维（0-100 分） | ❌ |
| Math Academy | 千级 | FIRe + 知识图谱 | 1 维（图谱颜色） | ❌ |
| Area9 Lyceum | 30M（自称） | 4 维框架 | 1 维（能力状态） | ❌ |
| 松鼠 AI | 百万级 | 30+ 标签属性 | 1 维（知识点颜色） | ❌ |
| Realizeit | 数十万 | 200+ 参数 | 1 维（颜色编码） | ❌ |
| Knewton（已关闭） | 百万级 | PGM 多维 | **从未成功展示** | ❌ 失败 |

### ⛔ 商业验证结论

**零产品给用户展示 per-KC 多维精通度。** 唯一激进尝试者 Knewton（$1.8 亿融资）——美国教育部研究发现"无显著学习效果"，最终被收购。

**行业共识：内部复杂，展示简单。**

---

## 六、设计来源追溯

```
2026-03-11  Brainstorming Session B（记忆系统 2）
  └─ 设计了"两阶段五类弱点模型"（5 类弱点）
  └─ 设计了"FSRS+Graphiti+策略适配器三角协作"（5 种策略 × 5 类弱点）

2026-03-15  信号融合算法调研 session
  └─ 设计了"10信号→5维 Beta-Bayesian 融合"

2026-03-14  独立 Review Session（7 Agent、70+ 论文）
  └─ ⛔ 决策 3 评级：CRITICAL — 建议降为 3 类
  └─ ⛔ 决策 4 评级：CRITICAL — FSRS 与 Graphiti 假设矛盾
  └─ ⛔ 决策 5 评级：HIGH — AI 评分不可靠
  └─ 用户选择：保持 5 类，设退出条件

2026-03-15  PRD-Create Session
  └─ ⛔ 直接将 brainstorming 结论写入 PRD
  └─ 未先跑退出条件测试

2026-03-15  PRD-Review New Tab（本 session）
  └─ ⛔ 代码审查：零实现（15 模块全 NO DEPENDENCY）
  └─ ⛔ 学术验证：零先例（30+ 篇论文无 per-KC 5D 连续追踪）
  └─ ⛔ 商业验证：零成功案例（10 款产品全单维展示）
```

### ⛔ 流程缺陷

| 步骤 | 应该做的 | 实际做了吗 |
|------|---------|----------|
| Brainstorming 提出想法 | ✅ 正常 | ✅ 做了 |
| 独立审查提出质疑 | ✅ 正常 | ✅ 做了（评级 CRITICAL） |
| **原型验证：用真实数据验证 5 维是否可分** | **必须做** | **❌ 没做** |
| **学术对标：找到用过类似方案的论文/产品** | **必须做** | **❌ 没做** |
| 写入 PRD | 验证通过后才能写 | ⛔ 直接写了 |

---

## 七、推荐替代方案（有论文+产品支撑）

| 功能 | 方案 | 学术/产品支撑 |
|------|------|-------------|
| 记忆衰减追踪 | FSRS（已实现） | Anki 数亿用户 + FSRS-6 论文 |
| 整体掌握度 | 1 个 Beta 分布 per KC | PDT 2025 论文验证 |
| 知识类型区分 | 给题目打标签（记忆/理解/应用题） | Anderson & Krathwohl 修订版 Bloom |
| 元认知监控 | 答题前问"你觉得自己会吗？"→ 和实际结果对比 | Area9 模式（3000 万用户） |
| 弱点定位 | 哪类标签的题答错率最高 → 弱点提示 | 不需融合算法，纯统计 |
| 白箱展示 | 1 维进度 + 学习证据列表 + 历史趋势 | Khan Academy/ALEKS 模式 |

---

## 八、对 PRD 的影响

### 需要修改的 PRD 条目

| PRD 条目 | 当前描述 | 建议修改 |
|---------|---------|---------|
| FR-MAST-03 | 温度计总览→维度详情→趋势证据（5 维） | 改为：1 维进度 + 学习证据列表 + 历史趋势 |
| FR-MAST-06 | Beta-Bayesian 融合为五维精通度 | 改为：BKT+FSRS 单维掌握度 + 题目标签统计弱点 |
| Layer 2 创新 | Beta-Bayesian 五维融合 | 降级为远期研究目标（Phase 2+），附前提条件 |
| 成功标准 | 融合 > 单信号 | 改为：BKT+FSRS 掌握度与学生实际表现相关性 > 0.6 |
| 创新聚焦 | "零竞品"五维融合 | 标注：零竞品原因是无人验证可行，非技术壁垒 |

### 可保留的 PRD 条目

| PRD 条目 | 原因 |
|---------|------|
| FR-MAST-01（BKT+FSRS 追踪） | 有真实代码 + 学术验证 |
| FR-MAST-02（精通度仅通过考察更新） | 设计合理 |
| FR-MAST-04（FSRS 复习提醒） | 有真实代码 + Anki 验证 |
| FR-MAST-05（Calibration Tracking） | 需降级：改为显式自评对比，非自动检测 |

---

## 九、待用户确认事项

1. **五维精通度**：PRD 改为 1 维（MVP）+ 远期研究目标（Phase 2+）？
2. **元认知维度**：改为 Area9 模式（显式自评"你觉得自己会吗？"）？
3. **Pencil OLM 设计**：重新设计为 1 维进度 + 学习证据列表？
4. **评分 4 维 rubric**：保留（它是评分标准，不是精通度维度，不受影响）？

---

## 十、Graphiti 记录索引

本 session 在 `canvas-dev` group 中的 Graphiti 记录：

| 前缀 | 数量 | 内容 |
|------|------|------|
| `[Session-Start]` | 1 | PRD-Review-续3 启动 |
| `[Progress]` | 1 | OLM 三层 Pencil 设计完成 |
| `[Research]` | 6 | UI 覆盖率 Gap、审查结论确认、五维框架验证、三方汇总、设计来源追溯、学术论文验证 |
| `[Code-Review]` | 1 | 15 模块精通度代码审查 |
| `[Discussion]` | 2 | A/B 组概念区分、1 维 vs 5 维深度澄清 |
| `[Decision-Review]` | 2 | OLM 改为 1 维+证据（PENDING）、五维设计验证不通过（PENDING） |
