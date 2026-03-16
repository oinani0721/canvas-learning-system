---
stepsCompleted: [1, 2, 3, 4]
inputDocuments: ['_bmad-output/planning-artifacts/prd.md']
session_topic: 'PRD Review — Prompt 组装策略与质量保证 Deep Explore'
session_goals: '验证 PRD 中 prompt 组装策略的设计依据、审查代码质量、调研行业最佳实践、起草 PRD 补充条款'
selected_approach: 'deep-explore-with-adversarial-review'
techniques_used: ['4-agent-parallel-deep-explore', 'adversarial-code-review', 'community-research', 'prd-gap-analysis', '3-agent-parallel-deep-explore-round2']
ideas_generated: ['unified-prompt-pipeline', '6-dimension-rubric', 'progressive-quality-roadmap', 'prd-supplement-A-B-C-D', 'token-budget-allocation', 'xml-over-json', 'llmlingua-compression', 'anthropic-5-principles']
context_file: '_bmad-output/planning-artifacts/prd.md'
technique_execution_complete: true
session_active: false
workflow_completed: true
---

# Brainstorming Session Results

**Facilitator:** ROG
**Date:** 2026-03-15
**Session Type:** PRD Review New Tab — Prompt 质量保证 Deep Explore

## Session Overview

**Topic:** PRD 中 Prompt 组装策略的设计依据验证 + 质量保证缺失分析

**Goals:**
- 验证 PRD 中 prompt 组装架构是否符合行业最佳实践
- 审查现有代码中 prompt 组装的实际状态
- 调研教育 AI 领域的 prompt 质量评估方案
- 起草 PRD 缺失条款的补充文本

**触发原因：** 用户质疑 PRD 中 prompt 结构（系统指令→对话历史→相邻知识→检索结果→学习记忆→当前问题）如果是硬编码的，如何证明组合是高质量的。

---

## 一、调研方法论

本 session 采用 **4 路并行 Deep Explore**，每路由独立 agent 执行：

| Agent | 任务 | 方法 |
|-------|------|------|
| Agent 1 | PRD prompt 组装设计分析 | 全文读取 PRD，提取所有 prompt 相关条款 |
| Agent 2 | 社区最佳实践调研 | WebSearch + 论文检索，覆盖 Khanmigo/Duolingo/LearnLM/DSPy/ARES |
| Agent 3 | 代码对抗性审查 | 审查 12 个代码文件，覆盖 mock/管道打通/硬编码/质量保证 |
| Agent 4 | PRD 条款缺失审查 | 逐条审查 PRD 已有质量保证条款，对比行业标准识别缺失 |

第二轮再次启动 **4 路定向 Deep Explore**，深入两个具体方向：

| Agent | 任务 |
|-------|------|
| Agent 5 | Prompt 质量评估框架深度调研（LLM-as-Judge/DSPy/ARES/评估工具对比） |
| Agent 6 | 统一 Prompt 组装管道架构模式调研（设计模式/版本控制/A/B测试） |
| Agent 7 | 4 条 Prompt 路径精确代码审查（行号级定位/BUG发现/矛盾点精确提取） |
| Agent 8 | PRD 已有 vs 缺失质量保证条款精确审查（行号级定位/补充条款起草） |

---

## 二、核心发现

### 发现 1：PRD Prompt 组装方向正确，与行业一致

PRD 设计的三层动态组装架构：
- **Tier 1 全量注入**：当前节点完整对话历史
- **Tier 2 摘要注入**：相邻节点摘要
- **Tier 3 按需检索**：远端节点通过 RAG 检索

**社区验证**：所有成功的教育 AI 生产系统（Khanmigo、Duolingo、LearnLM、TutorLLM）均采用本质相同的三层混合架构：

| 层次 | 内容 | 更新频率 |
|------|------|---------|
| L1 静态教学框架 | 角色定义、教学原则、安全护栏 | 版本发布时 |
| L2 策略模板库 | 苏格拉底提问、纠错、评估等 | 按场景切换 |
| L3 动态上下文 | 学生画像、检索内容、对话历史 | 每次请求 |

**结论**：方向正确。PRD 明确参考了 Aider/Cursor/OpenCode 的上下文管理模式，非拍脑袋设计。FSE 2025 论文（From Prompts to Templates）确认"静态骨架+动态填充"是行业最佳实践。

**来源**：Khan Academy 7-Step Approach | Duolingo AI Lesson Generation | Google LearnLM | FSE 2025 Industry Track

---

### 发现 2：现有代码 4 条分叉路径 — NEEDS REPAIR

代码审查精确定位了 4 条 prompt 组装路径：

| 路径 | 入口方法 | 行号 | 上下文引用规则 | 生产状态 |
|------|---------|------|---------------|---------|
| A: React Agent | `_run_react_agent()` | agent_service.py L1513 | "**不能**作为引用来源" | **活跃** |
| B: Direct | `_call_gemini_api()` | agent_service.py L2152 | "**主动引用**" | 兜底 |
| C: Tool-enabled | `_call_agent_with_tools()` | agent_service.py L2662 | "主动引用" | 禁用 |
| D: Multimodal | `call_agent_with_images()` | agent_service.py L2857 | "主动引用" | 图片时 |

**引用规则矛盾**（精确行号）：
- `agent_service.py` **L1588**：`"此上下文仅供你理解主题背景，**不能作为引用来源**"`
- `gemini_client.py` **L391**（= L535 = L685）：`"**主动引用**：解释中涉及上下文材料时，用方括号标注来源"`
- 实为 intentional 设计差异（React Agent 有搜索工具/Direct 无），但未文档化

**context_instruction 重复 3 次**：gemini_client.py L387-398 / L533-544 / L679-690（byte-identical）

**关键 BUG**：

| 严重度 | 问题 | 位置 |
|--------|------|------|
| **CRITICAL** | React Agent 路径"学习记忆预加载"是**死代码**——查了记忆但结果被丢弃，从未传给 LLM | agent_service.py L1610 |
| HIGH | 2 处 memory 搜索直接用原始 JSON 作为搜索词（应提取 topic） | L2195, L2694 |
| MEDIUM | `context_enrichment_service.build_agent_prompt()` 从未被调用（死代码） | context_enrichment_service.py L1653 |
| MEDIUM | `textbook_context_service.build_agent_prompt()` 从未被调用（死代码） | textbook_context_service.py L428 |

**环境变量控制（生产实际路径）**：
- `ENABLE_REACT_AGENT=true` → 走 Path A（React Agent）
- Path A 失败 → fallback 到 Path B（Direct）
- 图片请求 → 两阶段管道（React gather + Vision call）

---

### 发现 3：PRD 缺失 12 处质量保证条款（G1-G12）

PRD 已有的质量保证集中在 3 层：
1. **检索层**（完善）：P@5 >= 0.70、Recall@10 >= 0.80、MRR@10 >= 0.70
2. **算法层**（完善）：Calibration 偏差 <= 15%、Beta-Bayesian 净正向收益
3. **AI 评分层**（部分）：Pearson > 0.7 前置验证、3 维 rubric（仅限评分场景）

**完全缺失的 12 处**：

| ID | 缺失领域 | 说明 |
|----|---------|------|
| G1 | **LLM 输出端到端质量** | 检索准 ≠ 回答好，中间 prompt 组装+LLM 生成环节零评估 |
| G2 | Faithfulness 指标 | "幻觉零容忍"仅是原则声明，无可衡量指标 |
| G3 | 对话回答质量 | 核心功能（FR-CONV-01~08）无量化评估 |
| G4 | 出题质量 | 检验白板出题（FR-EXAM-03）无难度适配/覆盖率评估 |
| G5 | 知识提取质量 | 对话错误归档（FR-CONV-06）的提取准确性无评估 |
| G6 | Prompt 模板版本管理 | 有注册机制但无版本控制/回归测试 |
| G7 | 上下文利用效率 | 三层注入策略但无评估注入上下文是否被有效利用 |
| G8 | 端到端学习效果 | 有算法层指标但缺用户层学习效果验证 |
| G9 | **零可观测性** | 15 个算法+多次 LLM 调用+多组件，零日志/监控/遥测 |
| G10 | LLM 成本追踪 | 多处 LLM 调用无 token 消耗追踪和预算控制 |
| G11 | Prompt 注入防护 | 安全部分未提及 prompt 注入攻击防护 |
| G12 | 可维护性/可测试性 NFR | NFR 缺少此分类 |

---

### 发现 4：Prompt 质量评估行业调研

**关键学术来源**：
- **MRBench (NAACL 2025)**：8 维度教学评估分类法，实证 LLM-as-Judge 评估教学质量**当前不可靠**
- **TutorBench (2025)**：1,490 个 prompt + 15,220 条 rubric，模型平均仅 47-53% 准确率
- **CEUR Socratic rubric (2024)**：4 维度（错误修复/脚手架引导/指导可操作性/连贯性与语气）
- **DSPy (Stanford)**：程序化 prompt 优化，可比领域提升 10-20%，但教育领域无直接案例
- **RAGAS (EACL 2024)**：RAG 评估事实标准，但有严重 judge 方差问题
- **ARES (NAACL 2024)**：领域自适应微调 judge，需 ~150 条人工标注

**推荐 6 维度评估 Rubric**：

| 维度 | 说明 | 学术来源 |
|------|------|---------|
| 事实忠实度 | 回答是否基于检索上下文，无幻觉 | RAGAS |
| 教学合理性 | 是否引导思考而非直接给答案 | MRBench |
| 错误识别修复 | 是否精准诊断学生误解并修复 | CEUR Socratic |
| 语言适切度 | 语言难度是否匹配学生水平 | TutorBench |
| 知识准确性 | 学科知识是否正确 | MathTutorBench |
| 引导可操作性 | 反馈是否具体可执行 | CEUR Socratic |

**推荐工具**：DeepEval（主评估框架，G-Eval 自定义教学维度）+ Langfuse（追踪/可观测，开源自托管）

---

### 发现 5：统一 Prompt 组装管道架构

**社区调研推荐的四层管道架构**：

```
Registry 层 ──→ 模板存储+版本控制（从 .md 文件加载）
     ↓
Composer 层 ──→ 上下文组装（ContextProvider 接口，每种上下文一个 Provider）
     ↓
Budget 层  ──→ Token 预算分配（优先级分层截断）
     ↓
Renderer 层 ──→ 统一渲染为最终 prompt
```

**4 条路径差异通过配置参数化**：

| 参数维度 | 可选值 |
|---------|-------|
| Context instruction 模式 | `"cite"`（主动引用）vs `"background"`（不可引用） |
| LLM backend | google-genai / openai-compatible / langchain-react |
| Tool 支持 | none / gemini-function-calling / react-agent-tools |
| Multimodal | text-only / with-images / two-phase |
| Memory injection | enabled/disabled，搜索关键词提取策略 |

**改动量估算**：
- Phase 1（~200-400 行）：提取共享 context_instruction，修复 memory 注入 BUG，消除不一致
- Phase 2（~800-1200 行）：完整 prompt 生命周期管理（版本控制、A/B 测试、Canary 部署）

**来源**：LangChain/LlamaIndex/Semantic Kernel 框架抽象 | Humanloop/PromptLayer/Agenta 平台 | FSE 2025 | Microsoft Dynamic Prompt Middleware (CHIWORK'25)

---

## 三、渐进式质量保证路线图

```
Phase 0（第1-2周）：人工评估 + 建立基线
  └─ 构建 50 条 golden dataset（标准问答对）
  └─ 用 6 维度 rubric 人工评分，建立基线
  └─ 成本：~35 小时人力，零基础设施费用

Phase 1（第1-2月）：自动化评估管道
  └─ 集成 DeepEval（开源），配置 faithfulness + 自定义教学指标
  └─ 部署 Langfuse（开源自托管），追踪每次 LLM 调用
  └─ 双模型交叉评估（缓解 judge 偏差）
  └─ 成本：~48 小时开发，LLM API ~$10-50/月

Phase 2（第3-4月）：领域专用评委
  └─ 积累 150 条人工标注后，用 ARES 微调领域 judge
  └─ 用 DSPy BootstrapFewShot 优化核心教学 prompt
  └─ 评估对齐验证：Cohen's kappa > 0.6 方可启用
  └─ 成本：~78 小时，GPU 几小时，DSPy ~$10-30

Phase 3（第5月+）：持续监控
  └─ 生产日志异常自动告警
  └─ A/B 测试新旧 prompt 变体
  └─ 每周人工抽检 20 条
  └─ 每季度 DSPy MIPROv2 重优化
```

---

## 四、PRD 补充条款（已起草，待确认写入）

### 补充 A：7 项新增可衡量指标（插入 PRD 行 96 后）

| 维度 | 指标 | 目标值 | 来源 |
|------|------|--------|------|
| LLM 输出忠实度 | Faithfulness (RAGAS) | >= 0.85 | E2E RAG 生产验收标准 |
| LLM 回答相关性 | Answer Relevancy | >= 0.80 | E2E RAG 生产验收标准 |
| 上下文利用率 | Context Utilization | >= 0.75 | 注入上下文被有效引用的比例 |
| AI 评分一致性 | 自一致性 (3 次同题评分 σ) | σ <= 5 | AI 评分可靠性前提 |
| 出题难度适配 | 难度匹配率 | >= 70% | 出题 vs 学生精通度匹配度 |
| 知识提取准确性 | 结构化提取 F1 | >= 0.80 | 错误/Tips/关键问答提取准确性 |
| LLM 调用成本 | 每 session 平均 token | 监控追踪 | 月度成本可视化 |

### 补充 B：新增"能力域 9：质量保证与可观测性"（插入 PRD 行 703 后）

| ID | 功能需求 |
|----|---------|
| FR-QA-01 | 系统对每次 LLM 输出进行忠实度检查——回答是否忠实于检索上下文 |
| FR-QA-02 | Prompt 模板版本管理，修改需通过 golden dataset 回归测试 |
| FR-QA-03 | 每次 LLM 调用记录结构化日志（类型/token/延迟/模型/缓存命中） |
| FR-QA-04 | 追踪 session/月度 LLM token 消耗，设置面板提供概览 |
| FR-QA-05 | 用户输入基础安全检查，防止 prompt 注入影响 system prompt |
| FR-QA-06 | 出题后评估难度是否匹配学生当前精通度水平 |
| FR-QA-07 | 结构化提取结果定期人工抽样验证准确性 |

### 补充 C：扩展 NFR — 可观测性 + 可维护性/可测试性（插入 PRD 行 749 后）

**可观测性：**

| 维度 | 要求 |
|------|------|
| LLM 调用日志 | 每次调用记录结构化日志，可在设置面板查看 |
| 管道健康指标 | RAG 管道每日自动计算检索质量指标并记录趋势 |
| 算法管道连通性 | 系统启动时自动检测 15 个算法管道的连通性（非 mock/stub） |
| 错误聚合 | 后端异常按类型聚合，高频错误在健康面板展示 |

**可维护性与可测试性：**

| 维度 | 要求 |
|------|------|
| 接口契约测试 | 前后端 API 接口有契约测试 |
| Prompt 回归测试 | 每个模板配 golden dataset (>=5 条)，修改后自动回归 |
| 算法单元测试 | 15 个算法各有独立单元测试 |
| 集成测试 | 核心工作流有端到端集成测试，至少覆盖 2 个用户旅程 |

### 补充 D：扩展安全 NFR — Prompt 注入防护（插入 PRD 行 738 后）

| 维度 | 要求 |
|------|------|
| Prompt 注入防护 | 用户输入注入 prompt 前进行基础安全检查，system/user 严格隔离 |
| LLM 输出安全 | LLM 输出展示前进行基础内容安全检查 |

---

## 五、优先级排序（建议）

| 优先级 | 行动 | 理由 |
|--------|------|------|
| **最高** | 修复 CRITICAL BUG（学习记忆失效） | 核心卖点不工作，修复成本极低（几行代码） |
| **高** | 补充 A+C（指标+监控）写入 PRD | 无指标=盲飞，无监控=出事找不到原因 |
| **中** | 补充 B（质量保证功能模块）写入 PRD | 长期质量持续改进的基础 |
| **中** | 统一 4 条路径为 1 条管道 | 防止路径间不一致继续恶化 |
| **低** | 补充 D（安全防护）写入 PRD | 重要但不紧急（当前用户群体小） |

---

## 六、用户确认状态

| 决策点 | 状态 |
|--------|------|
| PRD prompt 组装方向正确 | ✅ 已通过（社区验证） |
| 4 组补充条款是否写入 PRD | ⏳ 待确认 |
| 优先级排序是否认可 | ⏳ 待确认 |
| 渐进式路线图是否接受 | ⏳ 待确认 |
| 质量保证模块设计方向 | ⏳ 已解释待确认（后台自动质检AI，用户仅需提供Phase0标准答案） |

---

## 七、参考来源

### 学术论文
- MRBench — Unifying AI Tutor Evaluation (NAACL 2025)
- TutorBench (2025) — 1,490 prompts, 15,220 rubrics
- MathTutorBench (EMNLP 2025 Oral) — 数学辅导评估
- CEUR Socratic Tutoring Rubric (2024) — 4 维度教学评估
- RAGAS (EACL 2024) — RAG 评估框架
- ARES (NAACL 2024) — 领域自适应 RAG 评估
- DSPy (Stanford, arXiv 2310.03714) — 程序化 prompt 优化
- Lost in the Middle (TACL 2024) — 上下文位置偏差
- From Prompts to Templates (FSE 2025) — 生产 prompt 模板分析
- Microsoft Dynamic Prompt Middleware (CHIWORK'25)

### 工业实践
- Khan Academy 7-Step Prompt Engineering for Khanmigo
- Duolingo AI Lesson Generation + Agentic Workflows
- Google LearnLM Partner Prompt Guide
- TutorLLM (arXiv 2502.15709)

### 工具与框架
- DeepEval (GitHub) — 开源 LLM 评估框架
- Langfuse — 开源 LLM 可观测性平台
- Promptfoo — Prompt 回归测试工具
- LangChain / LlamaIndex / Semantic Kernel — Prompt 组装抽象参考

---

## 八、Graphiti 记录索引

本 session 已记录以下条目到 Graphiti（group_id: canvas-dev）：

1. `[Session-Start] PRD Review 验证会话`
2. `[Code-Review] Prompt 组装系统对抗性审查 — NEEDS REPAIR`
3. `[Research] Prompt 组装社区最佳实践调研`
4. `[Decision-Review] PRD 需补充 Prompt 质量保证机制 — 待验证`
5. `[Research-Tech] Prompt质量评估深度调研 — 6维度Rubric+渐进式路线图`
6. `[Research-Tech] 统一Prompt组装管道架构调研 — 四层管道+ContextProvider模式`
7. `[Code-Review] 4条Prompt路径精确审查 — 1个CRITICAL BUG + 2处死代码`
8. `[Code-Review] PRD质量保证条款审查 — 12处缺失(G1-G12)`
9. `[Decision-Review] PRD补充4组质量保证条款(A-D) — 待验证`
10. `[Feedback] 用户表示PRD审查技术发现看不懂 — 已用深度澄清翻译`
11. `[Discussion] 质量保证模块设计解释 — 用户理解确认中`

---

## 附录：第二轮深度定向调研补充（2026-03-15 New Tab Session 2）

> **触发原因**：用户在 PRD Review 过程中指出 prompt 组装"纯文本拼接、无算法"是巨大问题，要求深度定向 explore 社区调研+成熟论文+Graphiti 遗漏
> **方法**：3 路并行 agent（Anthropic/OpenAI 实践 + 学术论文 ITS + 代码库已有调研审查）

### 补充 1：Anthropic/OpenAI 官方 Prompt 组装指南

#### Anthropic Context Engineering 核心原则

> **"Find the smallest set of high-signal tokens that maximize the likelihood of your desired outcome"**

| 原则 | 说明 |
|------|------|
| **Minimal Yet Sufficient** | 最少但完整的信息集（最少 ≠ 最短） |
| **Right Altitude** | 不要太硬编码也不要太模糊，找到合适的抽象层次 |
| **Token Efficiency** | 工具返回值要 token 高效，示例选"典型"而非"穷举" |
| **Progressive Autonomy** | 随模型能力提升逐步放权给模型自主决策 |
| **Simplicity Doctrine** | "Do the simplest thing that works" |

**来源**：Anthropic Building Effective Agents / Context Engineering Documentation

#### OpenAI GPT-4.1 Prompting Guide

**推荐 Prompt Section 排序**：
1. Role and Objective
2. Instructions（含子分类）
3. Reasoning Steps
4. Output Format
5. Examples
6. Context
7. Final instructions（提示逐步思考）

**格式选择**（长上下文关键发现）：
- **XML 长上下文表现最优**（支持嵌套+元数据属性）
- **JSON 表现最差**（文档密集场景尤其差）
- **Markdown 为默认推荐**

**Lost in the Middle 缓解**：
> "If you have long context in your prompt, ideally place your instructions at **both the beginning and end** of the provided context."

**来源**：OpenAI GPT-4.1 Prompting Guide (developers.openai.com)

#### Khan Academy 7 步法

1. 理解理想的导师-学生关系（Bloom "2-Sigma Problem"）
2. 参考学习科学文献（自我解释、即时反馈、因材施教）
3. 整合内容库（学生课程/语言/兴趣个性化注入）
4. 精心设计交互（语气/人格/提问方式 + 安全护栏）
5. 多角色测试（不同水平+学科）
6. 安全优先（NIST + 受控测试环境）
7. 基于真实反馈迭代（"economy of language"原则）

**来源**：Khan Academy Blog — 7-Step Approach to Prompt Engineering for Khanmigo

### 补充 2：学术论文 — ITS 教育 AI Prompt 组装

#### 生产级 ITS 系统对比

| 系统 | Prompt 组装方式 | 关键设计 |
|------|---------------|---------|
| **Khan Academy (Khanmigo)** | 5 层固定结构 | 角色→教学规则→学生水平→情感处理→安全护栏；Langfuse 追踪 |
| **Duolingo** | 关注点分离 | Birdbrain ML 管学生模型（750ms→14ms），GPT-4 管生成；"Mad Lib"模板 |
| **LPITutor** | 双层模板 | 静态层（教学模板）+ 动态层（RAG + 学生元数据注入）；意图分类模块自动选模板变体 |
| **DeepTutor (HKUDS)** | 统一 PromptManager | 单例管理所有 prompt 构建；多 agent 架构；混合检索（本地 embedding + 网搜 + 论文发现） |
| **IntelliCode** | StateGraph 编排 | 6 专用 agent（技能评估/学习画像/渐进提示/课程选择/间隔重复/参与监控）；**单写者策略**——仅编排器写持久记录 |
| **GraphMASAL** | LangGraph 三角 | Diagnostician + Planner + Tutor；动态知识图谱基础；两阶段神经 IR；超越 LLM prompting 基线 |
| **GenMentor** | 进化优化 | Goal→Skill 映射 + 学习路径调度 + 内容生成；实时学生画像 |

**来源**：LPITutor (PeerJ CS 2025) | IntelliCode (arXiv:2512.18669) | GraphMASAL (AAMAS 2026, arXiv:2511.11035) | GenMentor (WWW 2025 Oral, arXiv:2501.15749)

#### Prompt 压缩关键论文

| 论文 | 核心结论 | 量化结果 |
|------|---------|---------|
| **LLMLingua** (Microsoft, EMNLP 2023) | 粗到细压缩 + 预算控制器 + 分布对齐 | **20x 压缩，仅 1.5% 性能损失**；1.7-5.7x 延迟加速 |
| **LongLLMLingua** (RAG 专用) | RAG 场景优化 | **4x 压缩，+21.4% 准确率**；2.1x 延迟加速；94% 成本降低 |
| **LLMLingua-2** (ACL 2024) | 数据蒸馏方法，任务无关 | 忠实压缩，跨任务泛化 |
| **Lost in the Middle** (Liu et al., TACL 2024) | LLM 对开头和结尾注意力最强 | 中间位置信息**性能显著下降**（首因+近因偏差） |
| **Found in the Middle** (2024) | 即插即用位置编码缓解 | 降低中间位置损失 |
| **NAACL 2025 Prompt Compression Survey** | 1400+ 篇系统性分析 | 分类：token 级剪枝 / 软 prompt / 知识蒸馏 |
| **Context Engineering Survey** (arXiv:2507.13334) | 1400+ 篇系统性分析 | 四类操作：Write / Select / Compress / Isolate |
| **Token-Budget-Aware LLM Reasoning** (ACL 2025) | 问题复杂度与最优 token 预算正相关 | 平衡正确性 vs token 成本 |
| **RAGO** (ISCA 2025, Google) | RAG 系统性性能优化 | 2x QPS/chip + 55% TTFT 延迟降低 |

**来源**：LLMLingua (arXiv:2310.05736) | LongLLMLingua (arXiv:2310.06839) | LLMLingua-2 (arXiv:2403.12968) | RAGO (arXiv:2503.14649)

#### Context Pruning（上下文裁剪）

- 序列标注式裁剪：保留（甚至提升）QA 性能的同时**裁剪 60-80% 上下文**
- **来源**：Milvus Blog — LLM Context Pruning Developer Guide

### 补充 3：Token Budget 具体分配方案

#### 按任务类型分配（行业最佳实践）

| 任务类型 | 推荐预算 | 场景 |
|---------|---------|------|
| 分类/检索 | 50–200 tokens | 简单意图判断 |
| 创意生成 | 500–1,500 tokens | 内容生成 |
| 多轮推理 | 4,000–8,000 tokens | 深度教学对话 |

**关键原则**：按任务类型分配，不按产品统一分配。

#### 推荐 Section 预算分配

```
总预算 = 模型 context window - 输出预留
分配方案：
  Section 1: System Role        ~2-4K   (REQUIRED, 固定)
  Section 2: Student Model      ~1-2K   (HIGH, 动态/Graphiti)
  Section 3: Retrieved Content  ~4-8K   (HIGH, 动态/RAG, 放开头)
  Section 4: Conversation Hist  ~2-4K   (MEDIUM, 裁剪+摘要)
  Section 5: Current Query      ~0.5-2K (REQUIRED, 放末尾)
  Output Reserved:              ~4-8K   (必须预留)
```

**截断优先级**（预算不够时先砍什么）：
1. 对话历史（最先摘要压缩，2000→200 tokens）
2. 检索内容（reranking 后取 Top-K）
3. 学生模型（压缩为关键弱点摘要）
4. 系统指令（永不截断）
5. 当前问题（永不截断）

**来源**：IBM Token Optimization | Token-Budget-Aware LLM Reasoning (ACL 2025) | Managing Token Budgets (apxml.com)

### 补充 4：LangGraph Context Window 管理模式

#### 三种官方策略

| 策略 | 机制 | 适用场景 |
|------|------|---------|
| **Message Trimming** | `trim_messages` 保留最近 N token，尊重消息边界 | 短对话 |
| **Message Summarization** | `SummarizationNode` 维护 `RunningSummary` | 长对话 |
| **State-based** | 扩展 `MessagesState` 加 summary/context 字段 | 复杂 agent |

#### LangChain "How to Fix Your Context" 6 技术

| 技术 | 说明 | 量化效果 |
|------|------|---------|
| **RAG** | 选择性添加相关信息 | 基线 |
| **Context Pruning** | GPT-4o-mini 剥离无关句 | **25K→11K tokens**，96% 事实保留 |
| **Summarization** | 压缩所有相关但冗长的内容 | 适用于检索内容全部相关的场景 |
| **Context Quarantine** | 多 agent 隔离上下文窗口 | 防止上下文污染/干扰 |
| **Context Offloading** | 工具存储信息（草稿本/持久存储） | 释放 context window 空间 |
| **Multi-agent** | Supervisor + 专用 agent | 每个 agent 仅看到相关子集 |

**来源**：LangGraph Memory Docs | LangChain "How to Fix Your Context" (github.com/langchain-ai/how_to_fix_your_context)

### 补充 5：与主文档发现的交叉验证

| 主文档发现 | 本轮补充证据 | 验证状态 |
|-----------|------------|---------|
| PRD 三层架构方向正确 | Khan Academy 5 层 + LPITutor 双层 + IntelliCode 6-agent 全部采用分层 | ✅ **进一步强化** |
| Token Budget 需要引入 | 具体分配数字（2-4K / 1-2K / 4-8K / 2-4K）+ 截断优先级 | ✅ **已量化** |
| Lost in the Middle 需位置优化 | OpenAI 官方确认"放开头和结尾"+ LongLLMLingua +21.4% | ✅ **官方确认** |
| XML 格式优于 JSON | OpenAI GPT-4.1 Guide 明确"JSON performed particularly poorly" | ✅ **新增关键发现** |
| 统一管道 4 层架构 | DeepTutor 统一 PromptManager + IntelliCode 单写者策略 | ✅ **生产验证** |
| 压缩管道必要性 | LLMLingua 20x/1.5% + Context Pruning 60-80% | ✅ **量化证据** |

### 补充 Graphiti 记录

12. `[Research-Tech] Prompt 组装 Agent 3 代码探索完成 — 4 分叉路径+6 gap`
13. `[Research-Tech] Prompt 组装 Agent 2 学术论文完成 — 4 模式+关键论文`
14. `[Research-Tech] Prompt 组装效率 — 三源交叉整合完成`
