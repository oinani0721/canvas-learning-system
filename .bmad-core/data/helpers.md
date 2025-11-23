# Canvas Learning System - Helper Documentation

**Version**: v1.0
**Created**: 2025-11-17
**Purpose**: BMad Helper System - 可通过`@helpers.md#Section-Name`引用的详细文档

**使用方式**: 在CLAUDE.md中使用`详见: @helpers.md#Section-Name`引用本文档对应章节

---

## 目录

1. [14 Agents详细说明](#section-1-14-agents详细说明)
2. [Canvas颜色系统和工作流规则](#section-2-canvas颜色系统和工作流规则)
3. [8步学习循环详解](#section-3-8步学习循环详解)
4. [技术验证检查清单](#section-4-技术验证检查清单)
5. [技术架构详解](#section-5-技术架构详解)
6. [项目结构和资源](#section-6-项目结构和资源)

---

## Section 1: 14 Agents详细说明

### 🤖 Canvas学习系统Agent架构

系统包含**14个专项Agents**，分为**2大类型**：

### 🎓 学习型Agents (12个) - 面向用户学习过程

直接支持用户的学习活动，包括拆解、解释、评分和检验功能。

#### 1. 主控Agent (1个)

#### **canvas-orchestrator**
Orchestrates all Canvas learning system operations, coordinating 11 specialized sub-agents through natural language calling protocol. Supports 21 command variants across 11 operation types (decomposition, explanation, scoring, verification). Handles complete workflow: intent recognition → canvas reading → sub-agent delegation → result integration → reporting.

**位置**: `.claude/agents/canvas-orchestrator.md`

**使用场景**: 所有Canvas操作的统一入口,自动识别用户意图并调度相应的Sub-agent

---

#### 2. 拆解系列Agent (3个)

#### **basic-decomposition**
Decomposes difficult materials into 3-7 basic guiding questions using 4 question types (定义型/实例型/对比型/探索型). Helps transition from 'completely lost' (red nodes) to 'partial understanding' (purple nodes) through structured questioning.

**位置**: `.claude/agents/basic-decomposition.md`

**使用场景**: 面对完全看不懂的材料(红色节点),将其拆解为简单的引导性问题

**示例命令**:
- "拆解这个红色节点"
- "@离散数学.canvas 对'逆否命题'进行基础拆解"

#### **deep-decomposition**
Creates 3-10 deep verification questions to test true understanding and expose blind spots. Uses 4 question types (对比型/原因型/应用型/边界型). Requires user's existing understanding as input. Helps transition from partial understanding (purple nodes) to complete mastery (green nodes).

**位置**: `.claude/agents/deep-decomposition.md**

**使用场景**: 对"似懂非懂"的概念(紫色节点)进行深度拆解,暴露理解盲区

**关键区别**: 需要用户已有的理解作为输入 (vs basic-decomposition不需要)

**示例命令**:
- "深度拆解这个紫色节点"
- "@线性代数.canvas 深度拆解'特征向量',我的理解是:..."

#### **question-decomposition** (未实现)
Generates problem-solving breakthrough questions specifically for purple nodes (partial understanding). Helps students transition from 'seems to understand' to 'truly understands' through targeted questioning.

**位置**: `.claude/agents/question-decomposition.md`

**使用场景**: 针对应用题或问题求解场景的突破性问题生成

---

#### 3. 解释系列Agent (6个)

所有解释Agent都创建带emoji的markdown文件 (`.md`),文件命名格式: `{concept}-{type}-{YYYYMMDDHHmmss}.md`

#### **oral-explanation** 🗣️
Generates 800-1200 word oral-style explanations like a professor teaching, with 4-element structure: background context, core explanation, vivid examples, and common misconceptions. Creates .md files with emoji 🗣️.

**位置**: `.claude/agents/oral-explanation.md`

**结构**:
1. 背景铺垫
2. 核心解释
3. 生动举例
4. 常见误区

**使用场景**: 需要像教授那样口语化、系统化的解释

**示例命令**: "生成口语化解释'布尔代数'"

#### **clarification-path** 🔍
Generates 1500+ word in-depth explanations following 4-step process: problem clarification, concept decomposition, deep explanation, and verification summary. Creates .md files with emoji 🔍. Ideal for systematic clarification of complex concepts.

**位置**: `.claude/agents/clarification-path.md`

**结构**:
1. 问题澄清
2. 概念拆解
3. 深度解释
4. 验证总结

**使用场景**: 对复杂概念需要系统化、分步骤的深度澄清

**示例命令**: "生成澄清路径'范式'"

#### **comparison-table** 📊
Generates structured comparison tables in markdown format for distinguishing similar/confusing concepts. Compares across multiple dimensions: definitions, characteristics, use cases, examples, and common errors. Creates .md files with emoji 📊.

**位置**: `.claude/agents/comparison-table.md`

**对比维度**:
- 定义
- 特征
- 使用场景
- 示例
- 常见错误

**使用场景**: 区分易混淆的概念

**示例命令**: "生成对比表:逆否命题 vs 否命题"

#### **memory-anchor** ⚓
Generates vivid analogies, stories, and mnemonics to aid long-term memory retention. Creates .md files with emoji ⚓. Ideal for concepts that are understood but hard to remember.

**位置**: `.claude/agents/memory-anchor.md`

**内容类型**:
- 生动类比
- 故事记忆
- 记忆口诀

**使用场景**: 理解了但记不住的概念

**示例命令**: "生成记忆锚点'逆否命题'"

#### **four-level-explanation** 🎯
Generates progressive 4-level explanations (新手→进阶→专家→创新), 300-400 words per level, total 1200-1600 words. Each level builds on the previous, allowing learners to choose their starting point. Creates .md files with emoji 🎯.

**位置**: `.claude/agents/four-level-explanation.md`

**4个层次**:
1. **新手层** (Beginner) - 300-400词
2. **进阶层** (Intermediate) - 300-400词
3. **专家层** (Expert) - 300-400词
4. **创新层** (Innovation) - 300-400词

**使用场景**: 需要渐进式理解,从浅入深

**示例命令**: "生成四层次答案'逆否命题'"

#### **example-teaching** 📝
Generates complete problem-solving tutorials (~1000 words) with 6 sections: 题目, 思路分析, 分步求解, 易错点提醒, 变式练习, 答案提示. Creates .md files with emoji 📝. Ideal for learning through worked examples.

**位置**: `.claude/agents/example-teaching.md`

**6个section**:
1. 题目
2. 思路分析
3. 分步求解
4. 易错点提醒
5. 变式练习
6. 答案提示

**使用场景**: 通过例题学习,需要完整的解题教程

**示例命令**: "生成例题教学'逆否命题在证明中的应用'"

---

#### 4. 评分和检验Agent (2个)

#### **scoring-agent**
Evaluates user's understanding in yellow nodes using 4-dimension scoring: Accuracy, Imagery, Completeness, Originality (25 points each, total 100). Generates intelligent agent recommendations based on dimension weaknesses. Determines color transitions: ≥80=green, 60-79=purple, <60=red.

**位置**: `.claude/agents/scoring-agent.md`

**4个维度** (每个25分,总分100):
1. **Accuracy** (准确性)
2. **Imagery** (具象性)
3. **Completeness** (完整性)
4. **Originality** (原创性)

**颜色流转规则**:
- ≥80分 → 绿色 (完全理解)
- 60-79分 → 紫色 (似懂非懂)
- <60分 → 保持红色 (不理解)

**智能推荐** (Story 2.9创新):
- Accuracy低 → 推荐clarification-path, oral-explanation
- Imagery低 → 推荐memory-anchor, comparison-table
- Completeness低 → 推荐clarification-path, four-level-answer
- Originality低 → 推荐oral-explanation, memory-anchor

**使用场景**: 对黄色理解节点进行评分,自动流转颜色

**示例命令**:
- "评分这个黄色节点"
- "@数学分析.canvas 对所有黄色节点批量评分"

#### **verification-question-agent** (Epic 4核心)
Generates deep verification questions from red/purple nodes to reveal understanding gaps. Red nodes: 1-2 突破型/基础型 questions; Purple nodes: 2-3 检验型/应用型 questions. Core agent for Epic 4 paperless review system. Analyzes user's yellow node understanding to identify blind spots.

**位置**: `.claude/agents/verification-question-agent.md`

**输出数量**:
- 红色节点: 1-2个问题 (突破型/基础型)
- 紫色节点: 2-3个问题 (检验型/应用型)

**问题类型**:
- **突破型**: 换角度帮助理解
- **基础型**: 降低门槛的简单问题
- **检验型**: 测试是否真正理解
- **应用型**: 能否迁移到新场景

**Epic 4地位**: 无纸化回顾检验系统的核心智能引擎

**使用场景**: 生成检验白板时自动调用,为每个红色/紫色节点生成检验问题

---

### ⚙️ 系统级Agents (2个) - 支撑系统基础设施

负责智能调度、记忆管理等系统级功能，间接支持学习流程。

#### 1. review-board-agent-selector (智能Agent调度器)

**功能**: 智能分析黄色理解节点质量，推荐最合适的学习型agents并支持并行执行

**位置**: `.claude/agents/review-board-agent-selector.md`

**所属Epic**: Epic 10 (智能并行处理系统)

**核心能力**:
- **四维质量分析**: 准确性、完整性、清晰度、原创性
- **多Agent推荐**: 1-5个agents，基于置信度评分（0.5-1.0阈值）
- **并行执行支持**: 最多20个agents并发，8倍性能提升
- **Agent组合优化**: 互补组合建议（complementary/sequential）
- **执行时间估算**: 预测单个agent和总体执行时间

**使用场景**:
- **自动场景**: 在`/intelligent-parallel`命令中自动调用
- **手动场景**: 用户请求"推荐适合的agents"时调用
- **批量处理**: 对Canvas所有黄色节点进行智能分组和批量Agent调用

**关键区别**:
- **学习型agents**: 生成学习内容（解释文档、检验问题等）
- **此agent**: 决策调用哪些学习型agents（调度层、元层）

**数据流向**:
```
黄色节点 → review-board-agent-selector (质量分析)
         → 推荐agents列表 (oral-explanation, clarification-path等)
         → AsyncExecutionEngine (并行执行)
         → 生成解释文档 + 更新Canvas
```

**配置参数**:
- `max_recommendations`: 5 (最大推荐Agent数量)
- `default_confidence_threshold`: 0.7 (默认置信度阈值)
- `max_agents_per_node`: 20 (单节点最大并发数)
- `parallel_execution_timeout`: 300秒

---

#### 2. graphiti-memory-agent (Graphiti知识图谱记忆服务)

**功能**: 管理学习会话记录到时序知识图谱，提供智能学习建议和薄弱环节分析

**位置**: `.claude/agents/graphiti-memory-agent.md`

**所属Epic**: Epic 12 (3层记忆系统集成), Epic 14 (艾宾浩斯复习系统)

**核心能力**:
- **学习会话记录**: 自动提取Canvas中的概念和关系到Neo4j/Graphiti
- **概念网络分析**: 识别薄弱环节、关联概念、学习路径
- **检验白板生成支持**: 基于历史学习数据智能生成检验题（检验历史关联功能，PRD v1.1.8）
- **API成本优化**: 智能缓存、批处理、多级缓存策略
- **艾宾浩斯集成**: 支持复习历史查询、权重计算（70%薄弱点 + 30%已掌握概念）

**使用场景**:
- **后台自动**: 学习会话结束后自动记录到知识图谱（decomposition/explanation/scoring/review）
- **主动查询**: 生成检验白板时查询历史薄弱点和相关概念
- **复习推荐**: 艾宾浩斯系统查询需要复习的概念（Epic 14触发点4：薄弱点聚类，由Neo4j GDS Leiden算法实现）
- **学习分析**: 提供可视化的概念网络和学习路径建议

**关键区别**:
- **学习型agents**: 生成即时的学习内容（当前会话）
- **此agent**: 管理长期学习记忆（跨会话、跨Canvas、跨时间）

**数据流向**:
```
学习会话 → graphiti-memory-agent (会话记录)
         → Neo4j/Graphiti (概念+关系存储)
         → 检验白板生成 (查询薄弱点)
         → 艾宾浩斯系统 (复习推荐)
```

**集成系统**:
- **Temporal Memory**: 学习行为时序数据（Neo4j DirectNeo4jStorage）
- **Graphiti**: 概念关系网络（Neo4j Graphiti Layer）
- **Semantic Memory**: 文档语义向量（LanceDB + CUDA加速）
- **Neo4j GDS**: 社区检测与图算法（Leiden聚类，支持艾宾浩斯触发点4）
- **艾宾浩斯系统**: 复习调度和间隔重复（Py-FSRS算法）

**API使用策略**:
- 批量处理相似请求
- 使用gpt-3.5-turbo处理基础任务，gpt-4处理复杂分析
- 实现结果缓存（内存+磁盘+Graphiti三级缓存）
- 指数退避重试机制处理API限流

---

## Section 2: Canvas颜色系统和工作流规则

### 🎨 Canvas颜色系统

| Canvas Color Code | 视觉颜色 | 含义 | 使用场景 |
|-------------------|---------|------|---------|
| `"1"` | 🔴 红色 | 不理解/未通过 | 学生完全不懂的问题节点 |
| `"2"` | 🟢 绿色 | 完全理解/已通过 | 评分≥80分的问题 |
| `"3"` | 🟣 紫色 | 似懂非懂/待检验 | 评分60-79分,需要深度检验 |
| `"5"` | 🔵 蓝色 | AI补充解释 | AI生成的解释文档节点 |
| `"6"` | 🟡 黄色 | 个人理解输出区 | 学生用自己话的解释 |

### 颜色流转路径

```
🔴 红色 (完全不懂)
  ↓ 基础拆解 + 填写理解
🟣 紫色 (似懂非懂,评分60-79)
  ↓ 深度拆解 + 补充解释 + 优化理解
🟢 绿色 (完全理解,评分≥80)
```

### 费曼学习法实现

**核心**: "如果你不能简单地解释一个概念,说明你还没有真正理解它"

**在本系统中的实现**:
1. **黄色节点 = 输出区**: 强制用户用自己的话解释
2. **4维评分**: 量化评估理解质量 (准确性、具象性、完整性、原创性)
3. **颜色流转**: 可视化学习进度 (红→紫→绿)

### 检验白板 vs 原白板

**原白板** (Learning Canvas):
- 有AI辅助 (拆解、解释、评分)
- 边学边填写
- 复杂的知识网络

**检验白板** (Review Canvas):
- 初始无辅助 (只有检验问题)
- 从头复现知识
- 暴露理解盲区
- **支持所有Agent操作** (动态学习白板)
- 持续扩展直到接近原白板

### 检验白板迭代停止条件

满足以下至少3个条件时可停止迭代：
- ✅ 绿色占比 ≥ 80%
- ✅ 节点数量接近原白板的50-70%
- ✅ 至少生成3个解释文档
- ✅ 至少添加2个原创节点
- ✅ 无红色节点

---

## Section 3: 8步学习循环详解

### 8步学习循环 (检验白板核心流程)

1. **填写个人理解** (黄色节点,不看资料)
2. **发现不足**
3. **继续拆解** (basic/deep-decomposition)
4. **补充解释** (6种解释Agent)
5. **评分验证** (scoring-agent)
6. **颜色流转** (红→紫→绿)
7. **添加自己的节点**
8. **构建完整知识网络**

### 原白板学习循环

**完全不懂 (红色节点)**:
1. 调用basic-decomposition拆解
2. 填写黄色节点理解
3. 评分 → 如果<60分,重新拆解更细
4. 如果60-79分 → 转紫色,继续深度学习

**似懂非懂 (紫色节点)**:
1. 调用deep-decomposition深度拆解
2. 补充AI解释 (clarification-path, oral-explanation)
3. 优化黄色节点理解
4. 再次评分 → 如果≥80分,转绿色

### 检验白板推荐流程

1. **生成检验白板**: 从原白板提取红/紫节点
2. **初次填写** (不看资料): 暴露盲区
3. **评分**: 识别弱项
4. **针对性拆解和解释**:
   - 完全不懂 → basic-decomposition
   - 似懂非懂 → deep-decomposition + clarification-path
   - 易混淆 → comparison-table
   - 记不住 → memory-anchor
5. **重新填写**: 优化理解
6. **再次评分**: 验证进步
7. **重复2-6**: 直到80%绿色

### 常见场景Agent推荐

| 症状 | 推荐Agent | 目标 |
|------|----------|------|
| 完全不懂 | basic-decomposition | 拆解降难度 |
| 似懂非懂(紫色) | clarification-path | 深度理解 |
| 易混淆概念 | comparison-table | 结构化对比 |
| 需要记忆 | memory-anchor | 生动类比 |
| 需要练习 | example-teaching | 例题巩固 |

---

## Section 4: 技术验证检查清单

### 核心原则
**"所有技术细节必须可追溯到官方文档"**

### Skills 系统

项目使用**Claude Code Skills**提供离线技术文档访问：

| Skill | 位置 | 内容 |
|-------|------|------|
| langgraph | `.claude/skills/langgraph/` | 952页LangGraph完整文档 |
| graphiti | `.claude/skills/graphiti/` | Graphiti知识图谱框架文档 |
| obsidian-canvas | `.claude/skills/obsidian-canvas/` | Obsidian Canvas插件开发文档 |

**激活方式**: 在对话中使用 `@skill-name` (例如: `@langgraph`)

### Context7 MCP 集成

未生成Skills的技术栈通过**Context7 MCP**查询：

| 技术栈 | Library ID | Snippets |
|--------|-----------|----------|
| FastAPI | `/websites/fastapi_tiangolo` | 22,734 |
| Neo4j Cypher | `/websites/neo4j_cypher-manual_25` | 2,032 |
| Neo4j Operations | `/websites/neo4j_operations-manual-current` | 4,940 |

**查询方式**:
```bash
mcp__context7-mcp__get-library-docs(
    context7CompatibleLibraryID="/websites/fastapi_tiangolo",
    topic="your-topic",
    tokens=5000
)
```

### Story开发前检查清单

在开发任何Story前，必须完成：
1. ✅ 识别涉及的技术栈
2. ✅ 激活相关Skills或查询Context7
3. ✅ 验证所有API和参数
4. ✅ 标注文档来源

**详细清单**: 参见 `.bmad-core/checklists/technical-verification-checklist.md`

### 🔴 零幻觉开发强制规则

**适用范围**: Story开发、Code Review、架构设计的所有环节

#### 规则1: 提到什么技术，立即查看对应Skill或Context 7
- **触发词**: 任何技术栈名称、API名称、库名称、框架名称
- **示例**:
  - 提到`create_react_agent` → 立即执行 `@langgraph` 并搜索SKILL.md
  - 提到`Depends()` → 立即查询Context 7 FastAPI文档

#### 规则2: 开发时必须持续查阅Skills/Context7，不能仅依赖记忆
- 每个函数调用前：查阅参数列表
- 每个类实例化前：查阅构造函数签名
- 每个配置项前：查阅配置文档
- **质量门禁**: 无文档引用的代码应被拒绝

#### 规则3: 每个API调用必须标注文档来源
```python
# ✅ 正确示例
# ✅ Verified from LangGraph Skill (SKILL.md - Pattern: Agent with Tools)
agent = create_react_agent(
    model=llm,
    tools=[search_tool, calculator_tool],
    state_modifier="You are a helpful AI assistant."
)
```

#### 规则4: 未验证的API不允许进入代码
- 如果Skills中找不到 → 查询Context 7
- 如果Context 7也找不到 → 查询官方文档
- 如果都找不到 → **明确告知用户，不能臆测**

### 技术文档来源优先级

1. **Skills** (优先级最高) - 离线本地文档，速度快，准确性高
2. **Context 7** (优先级次之) - 在线文档，覆盖广
3. **官方网站** (最后手段) - WebFetch工具，速度慢

---

## Section 5: 技术架构详解

### 3层Python架构

**Layer 1: CanvasJSONOperator** (底层JSON操作)
- 原子化Canvas文件读写 (read_canvas, write_canvas)
- 节点/边的CRUD操作 (add_node, find_node_by_id, add_edge)
- 颜色常量 (COLOR_RED="1", COLOR_GREEN="2"...)

**Layer 2: CanvasBusinessLogic** (业务逻辑层)
- v1.1布局算法 (黄色节点在问题正下方,垂直对齐)
- 上下文提取 (extract_verification_nodes)
- 问题聚类 (cluster_questions_by_topic)
- 检验白板生成 (generate_review_canvas_file)

**Layer 3: CanvasOrchestrator** (高级API)
- Sub-agent调用接口 (generate_verification_questions_with_agent)
- 完整操作工作流 (分析白板 → 拆解问题 → 创建节点)
- 自然语言调用协议

**Layer 4: 系统级Agent调度** (Epic 10/12扩展)
- 智能Agent选择器 (review-board-agent-selector)
- Graphiti记忆管理 (graphiti-memory-agent)
- 并行执行引擎 (AsyncExecutionEngine, 支持最多12个agents并发)
- 3层记忆系统集成 (Temporal + Graphiti + Semantic)

**文件位置**:
- Layer 1-3: `canvas_utils.py` (~100KB, 3层架构)
- Layer 4: `.claude/agents/review-board-agent-selector.md` + `graphiti-memory-agent.md`

### v1.1布局算法

**黄色节点定位**:
- 位置: 问题节点正下方 (垂直对齐)
- x坐标: `question_x + 50px` (右移50px)
- y坐标: `question_y + question_height + 30px` (下移30px间隔)

**聚类布局**:
- 主题间间隔: 100px (CLUSTER_GAP)
- 问题+黄色组合高度: 380px (VERTICAL_SPACING_BASE)
- 聚类总高度 = 问题数 × 380px

### Sub-agent调用协议

**自然语言调用** (不是函数调用):
```python
call_statement = f"""
Use the {agent-name} subagent to {task description}

Input: {输入数据JSON}

Expected output: {输出格式说明}

⚠️ IMPORTANT: Return ONLY the raw JSON. Do NOT wrap it in markdown code blocks.
"""
```

**关键约束**:
- 必须返回纯JSON,不能用markdown code fence
- 必须包含Expected output说明
- Input使用`ensure_ascii=False`保持中文可读

### 性能指标

- 节点提取: <200ms (100节点)
- 问题生成: <5秒 (20节点)
- 聚类: <1秒 (60问题)
- 检验白板生成: <8秒 (完整流程)

### Epic 10.2性能提升 (异步并行执行引擎)

| 节点数 | 旧版本（串行） | 新版本（异步并行） | 性能提升 |
|-------|--------------|-------------------|---------|
| 10节点 | ~100秒 | **12秒** | **8.3倍** ⚡ |
| 20节点 | ~200秒 | **25秒** | **8.0倍** ⚡ |
| 50节点 | ~500秒 | **58秒** | **8.6倍** ⚡ |

---

## Section 6: 项目结构和资源

### 📂 完整目录结构

```
C:/Users/ROG/托福/
├── .claude/
│   ├── PROJECT.md              ✅ 项目上下文(CLAUDE.md的简化版)
│   ├── agents/                 ✅ 14个Agent定义 (12个学习型 + 2个系统级)
│   │   ├── canvas-orchestrator.md
│   │   ├── basic-decomposition.md
│   │   ├── deep-decomposition.md
│   │   ├── question-decomposition.md
│   │   ├── oral-explanation.md
│   │   ├── clarification-path.md
│   │   ├── comparison-table.md
│   │   ├── memory-anchor.md
│   │   ├── four-level-explanation.md
│   │   ├── example-teaching.md
│   │   ├── scoring-agent.md
│   │   ├── verification-question-agent.md
│   │   ├── review-board-agent-selector.md    ⚙️ 系统级: 智能调度
│   │   └── graphiti-memory-agent.md          ⚙️ 系统级: 记忆管理
│   ├── settings.local.json     ✅ 权限配置
│   ├── commands/               ✅ 自定义斜杠命令
│   └── skills/                 ✅ Claude Code Skills（离线文档）
│       ├── langgraph/          # LangGraph框架文档（952页）
│       ├── graphiti/           # Graphiti知识图谱文档
│       └── obsidian-canvas/    # Obsidian Canvas插件文档
│
├── .bmad-core/                 ✅ BMad开发框架配置
│   ├── core-config.yaml        # BMad核心配置文件（v2.0）
│   ├── data/                   # BMad数据和辅助文件
│   │   └── helpers.md          # Helper System主文件（本文件）
│   └── templates/              # BMad模板文件
│
├── specs/                      ✅ Specification-Driven Design (SDD)
│   ├── api/                    # OpenAPI 3.0规范
│   │   ├── canvas-api.openapi.yml
│   │   └── agent-api.openapi.yml
│   ├── data/                   # JSON Schema数据模型
│   │   ├── canvas-node.schema.json
│   │   ├── canvas-edge.schema.json
│   │   ├── agent-response.schema.json
│   │   └── scoring-response.schema.json
│   └── behavior/               # Gherkin行为规范
│       ├── scoring-workflow.feature
│       └── review-board-workflow.feature
│
├── docs/                       ✅ 完整文档
│   ├── project-brief.md        # 项目简报(615行)
│   ├── agent-descriptions-comparison.md  # Agent描述对比
│   ├── prd/                    # PRD分片(5个Epic)
│   ├── architecture/           # 架构文档
│   │   ├── canvas-layer-architecture.md
│   │   ├── coding-standards.md
│   │   ├── tech-stack.md
│   │   ├── project-structure.md
│   │   └── decisions/          # ADR决策记录
│   │       ├── 0001-use-obsidian-canvas.md
│   │       ├── 0002-langgraph-agents.md
│   │       ├── 0003-graphiti-memory.md
│   │       └── 0004-async-execution-engine.md
│   └── stories/                # 26个Story文件(Epic 1-3)
│
├── tests/                      ✅ 测试文件
│   ├── test_canvas_utils.py
│   ├── test_canvas_utils_clustering.py
│   ├── test_story_2_9_suggestions.py
│   └── contract/               # Contract Testing
│       ├── conftest.py
│       ├── test_canvas_contracts.py
│       └── test_agent_contracts.py
│
├── canvas_utils.py             ✅ Python工具库(3层架构,~100KB)
├── requirements.txt            ✅ Python依赖
├── .gitignore                  ✅ Git忽略规则
├── CANVAS_ERROR_LOG.md         ✅ Canvas操作错误日志和标准流程
│
├── 笔记库/                     ✅ Canvas白板文件(.canvas)
│   ├── 离散数学/
│   │   └── 离散数学.canvas
│   └── ...
│
├── CLAUDE.md                   ✅ Claude Code主配置文件 (BMad优化版)
└── README.md                   ⏳ 项目README (待创建)
```

### 核心文档资源

**核心文档**:
- **项目简报**: `docs/project-brief.md` (615行,完整项目概述)
- **PRD**: `docs/prd/FULL-PRD-REFERENCE.md` (v1.0, 97%质量分)
- **架构文档**: `docs/architecture/` (8个文档)
- **Agent对比**: `docs/agent-descriptions-comparison.md` (详细agent规格)

**Story文件** (了解实现细节):
- `docs/stories/1.*.story.md` - Epic 1: Canvas核心操作
- `docs/stories/2.*.story.md` - Epic 2: 问题拆解系统
- `docs/stories/3.*.story.md` - Epic 3: 补充解释系统
- `docs/stories/4.*.story.md` - Epic 4: 无纸化检验系统

### Canvas操作规范

**在执行任何Canvas操作前，必须先阅读**: `CANVAS_ERROR_LOG.md`

该文档包含：
- ✅ **错误记录**: 历史错误案例和避免方法
- ✅ **颜色系统完整规则**: 红/绿/紫/蓝/黄的使用场景和判断标准
- ✅ **标准操作流程(SOP)**: 每种Canvas操作的详细步骤清单
- ✅ **检查清单**: 操作前/操作后的必查项
- ✅ **核心原则**: 费曼学习法、可视化知识图谱、颜色一致性

**核心要点**:
1. 🟡 **每个问题/解释节点必须配套空白黄色节点**（个人理解输出区）
2. 💾 **所有操作必须实际修改Canvas文件**（不能只展示）
3. 🎨 **严格遵守颜色判断标准**（红色=基础问题，紫色=进阶问题，等）

---

**文档结束**

**使用提示**: 在CLAUDE.md中使用`详见: @helpers.md#Section-1-14-agents详细说明`等格式引用本文档章节
