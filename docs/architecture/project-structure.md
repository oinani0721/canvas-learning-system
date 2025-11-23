---
document_type: "Architecture"
version: "2.0.0"
last_modified: "2025-11-19"
status: "approved"
iteration: 1

authors:
  - name: "Architect Agent"
    role: "Solution Architect"

reviewers:
  - name: "PO Agent"
    role: "Product Owner"
    approved: true

compatible_with:
  prd: "v1.0"
  api_spec: "v1.0"

api_spec_hash: "0dc1d3610d28bf99"

changes_from_previous:
  - "Initial Architecture with frontmatter metadata"

git:
  commit_sha: ""
  tag: ""

metadata:
  components_count: 0
  external_services: []
  technology_stack:
    frontend: []
    backend: ["Python 3.11", "asyncio"]
    database: []
    infrastructure: []
---

# 统一项目结构 - Canvas学习系统 (BMad Integration)

**版本**: v2.0 (BMad Integration)
**最后更新**: 2025-11-17
**维护者**: Architect Agent + BMad Framework

---

## 📁 完整目录结构 (含BMad集成)

```
C:/Users/ROG/托福/
│
├── .claude/                                    # Claude Code配置根目录
│   ├── PROJECT.md                              # 项目上下文（自动加载）
│   │
│   ├── agents/                                 # Sub-agent定义（14个：12学习型 + 2系统级）
│   │   ├── canvas-orchestrator.md              # 主控Agent
│   │   ├── basic-decomposition.md              # 基础拆解Agent
│   │   ├── deep-decomposition.md               # 深度拆解Agent
│   │   ├── question-decomposition.md           # 问题拆解Agent
│   │   ├── oral-explanation.md                 # 口语化解释Agent
│   │   ├── clarification-path.md               # 澄清路径Agent
│   │   ├── comparison-table.md                 # 对比表Agent
│   │   ├── memory-anchor.md                    # 记忆锚点Agent
│   │   ├── four-level-explanation.md           # 四层次解答Agent
│   │   ├── example-teaching.md                 # 例题教学Agent
│   │   ├── scoring-agent.md                    # 评分Agent
│   │   ├── verification-question-agent.md      # 检验问题生成Agent (Epic 4)
│   │   ├── review-board-agent-selector.md      # ⭐ 智能Agent调度器（系统级）
│   │   └── graphiti-memory-agent.md            # ⭐ Graphiti记忆管理Agent（系统级）
│   │
│   ├── commands/                               # 自定义Slash命令
│   │   ├── canvas-*.md                         # Canvas相关命令
│   │   ├── parallel-*.md                       # 并行处理命令
│   │   ├── memory-*.md                         # 记忆系统命令
│   │   └── ...
│   │
│   └── skills/                                 # ⭐ Claude Code Skills（离线文档）
│       ├── langgraph/                          # LangGraph框架文档（952页）
│       │   ├── SKILL.md                        # Skills主文档
│       │   └── references/                     # 参考文档
│       ├── graphiti/                           # Graphiti知识图谱文档（~200页）
│       │   ├── SKILL.md
│       │   └── references/
│       └── obsidian-canvas/                    # Obsidian Canvas插件文档（~150页）
│           ├── SKILL.md
│           └── references/
│
├── .bmad-core/                                 # ⭐ BMad开发框架配置
│   ├── core-config.yaml                        # ⭐ BMad核心配置文件（v2.0）
│   │   # 包含：devLoadAlwaysFiles, Helper System, SDD, ADR配置
│   │
│   ├── data/                                   # ⭐ BMad数据和辅助文件
│   │   └── helpers.md                          # ⭐ Helper System主文件
│   │       # 5个Sections: Story-Development-Workflow, Testing-Checklist,
│   │       # Agent-Calling-Protocol, Canvas-Color-System, BMad-4-Phase-Workflow
│   │
│   ├── templates/                              # ⭐ BMad模板文件
│   │   ├── prd-template.md                     # PRD模板
│   │   ├── story-template.md                   # Story模板
│   │   ├── adr-template.md                     # ADR模板
│   │   ├── test-suite-template.py              # 测试套件模板
│   │   └── agent-template.md                   # Agent定义模板
│   │
│   ├── tasks/                                  # BMad任务定义
│   └── checklists/                             # BMad检查清单
│
├── specs/                                      # ⭐ Specification-Driven Design (SDD)
│   ├── api/                                    # ⭐ OpenAPI 3.0规范
│   │   ├── canvas-api.openapi.yml              # Canvas API契约
│   │   └── agent-api.openapi.yml               # Agent API契约
│   │
│   ├── data/                                   # ⭐ JSON Schema数据模型
│   │   ├── canvas-node.schema.json             # Canvas节点数据模型
│   │   ├── canvas-edge.schema.json             # Canvas边数据模型
│   │   ├── agent-response.schema.json          # Agent响应数据模型
│   │   └── scoring-response.schema.json        # 评分响应数据模型
│   │
│   └── behavior/                               # ⭐ Gherkin行为规范
│       ├── scoring-workflow.feature            # 评分工作流
│       └── review-board-workflow.feature       # 检验白板生成工作流
│
├── canvas_utils.py                             # ⭐ Canvas操作Python库
│   # 包含3层架构：
│   # - CanvasJSONOperator（Layer 1）
│   # - CanvasBusinessLogic（Layer 2）
│   # - CanvasOrchestrator（Layer 3）
│
├── requirements.txt                            # Python依赖
├── .gitignore                                  # Git忽略规则
├── README.md                                   # 项目README
│
├── docs/                                       # 文档根目录
│   ├── project-brief.md                        # 项目简报
│   ├── RESEARCH_REPORT_BMAD_INTEGRATION.md     # ⭐ BMad集成调研报告（80KB+）
│   │
│   ├── prd/                                    # PRD文档（分片）
│   │   ├── index.md                            # PRD索引
│   │   ├── epic-1-core-infrastructure.md       # Epic 1
│   │   ├── epic-2-decomposition-agents.md      # Epic 2
│   │   ├── epic-3-explanation-agents.md        # Epic 3
│   │   ├── epic-4-scoring-review.md            # Epic 4
│   │   ├── epic-5-integration.md               # Epic 5
│   │   └── epic-10-intelligent-parallel.md     # Epic 10
│   │
│   ├── architecture/                           # 技术架构文档（分片）
│   │   ├── index.md                            # 架构索引
│   │   ├── tech-stack.md                       # ⭐ 技术栈（v2.0含BMad）
│   │   ├── project-structure.md                # ⭐ 本文档（v2.0含BMad）
│   │   ├── coding-standards.md                 # ⭐ 编码规范（v2.0含BMad）
│   │   ├── canvas-layer-architecture.md        # ⭐ 4层架构设计（v2.0）
│   │   ├── canvas-layout-v1.1.md               # v1.1布局算法
│   │   ├── sub-agent-templates.md              # Agent模板
│   │   ├── sub-agent-calling-protocol.md       # Agent调用协议
│   │   │
│   │   └── decisions/                          # ⭐ Architecture Decision Records (ADR)
│   │       ├── 0001-use-obsidian-canvas.md     # ADR 1: 使用Obsidian Canvas
│   │       ├── 0002-langgraph-agents.md        # ADR 2: 使用LangGraph构建Agents
│   │       ├── 0003-graphiti-memory.md         # ADR 3: 使用Graphiti记忆系统
│   │       └── 0004-async-execution-engine.md  # ADR 4: 异步并行执行引擎
│   │
│   └── stories/                                # User Story文件
│       ├── 1.1.story.md                        # Epic 1, Story 1
│       ├── 1.2.story.md
│       └── ...
│
├── tests/                                      # 测试文件（Dev阶段创建）
│   ├── test_canvas_utils.py                   # canvas_utils.py单元测试
│   ├── test_agents/                            # Agent集成测试
│   ├── fixtures/                               # 测试数据
│   │   ├── test-canvas-basic.canvas
│   │   └── test-canvas-complex.canvas
│   │
│   └── contract/                               # ⭐ Contract Testing（Schemathesis）
│       ├── test_canvas_contracts.py            # Canvas API契约测试
│       ├── test_agent_contracts.py             # Agent API契约测试
│       └── conftest.py                         # pytest配置
│
├── scripts/                                    # ⭐ 辅助脚本和重组工具
│   ├── reorganize_to_canvas_dir.sh             # ⭐ BMad重组脚本（Bash）
│   ├── reorganize_to_canvas_dir.ps1            # ⭐ BMad重组脚本（PowerShell）
│   ├── README.md                               # ⭐ 脚本使用说明
│   ├── verify_colors.py                        # 颜色验证脚本
│   └── analyze_canvas.py                       # Canvas分析脚本
│
└── 笔记库/                                      # 用户Canvas和笔记
    ├── 离散数学/
    │   ├── 离散数学.canvas                     # 主Canvas白板
    │   ├── 离散数学-检验白板-20250114.canvas   # 检验白板
    │   ├── 逆否命题-口语化解释-20250114.md     # 生成的笔记
    │   └── ...
    ├── 托福听力/
    │   ├── 托福听力.canvas
    │   └── ...
    ├── 微积分/
    │   └── ...
    └── examples/                               # 示例Canvas文件
        ├── test-basic-decomposition.canvas
        ├── test-scoring.canvas
        └── README.md
```

**⭐ 图例说明**:
- ⭐ 标记的目录/文件为BMad集成新增或增强的内容
- 其他为Canvas Learning System原有结构

---

## 📝 关键文件说明

### `.claude/PROJECT.md`
**用途**: 项目上下文文件，Claude Code启动时自动加载
**重要性**: ⭐⭐⭐⭐⭐
**内容**:
- 项目简介和目标
- 13个Sub-agent清单
- 颜色系统说明
- 常用工作流
- 快速命令参考

**何时更新**: 添加新Agent或修改核心工作流时

---

### `.claude/agents/*.md`
**用途**: Sub-agent定义文件（14个Agent：12学习型 + 2系统级）
**重要性**: ⭐⭐⭐⭐⭐
**命名规范**: `{agent-name}.md`（kebab-case）

**12个学习型Agents**:
- canvas-orchestrator.md - 主控Agent
- basic-decomposition.md - 基础拆解
- deep-decomposition.md - 深度拆解
- question-decomposition.md - 问题拆解
- oral-explanation.md - 口语化解释
- clarification-path.md - 澄清路径
- comparison-table.md - 对比表
- memory-anchor.md - 记忆锚点
- four-level-explanation.md - 四层次解答
- example-teaching.md - 例题教学
- scoring-agent.md - 评分
- verification-question-agent.md - 检验问题生成

**2个系统级Agents** (BMad Integration):
- review-board-agent-selector.md - ⭐ 智能Agent调度器（Epic 10）
- graphiti-memory-agent.md - ⭐ Graphiti记忆管理（Epic 12）

**文件结构**:
```markdown
---
name: agent-name
description: One-line description
tools: Read, Write, Edit  # 可用工具
model: sonnet             # 使用的模型
---

# Agent名称

## Role
[Agent角色描述]

## Input Format
[输入JSON格式]

## Output Format
[输出JSON格式]

## System Prompt
[详细的提示词]
```

**何时更新**: 添加新Agent或修改Agent行为时

---

### `canvas_utils.py`
**用途**: Canvas操作Python库（3层架构）
**重要性**: ⭐⭐⭐⭐⭐
**位置**: 项目根目录

**文件结构**:
```python
# Layer 1: CanvasJSONOperator
class CanvasJSONOperator:
    @staticmethod
    def read_canvas(canvas_path: str) -> Dict: ...
    @staticmethod
    def write_canvas(canvas_path: str, canvas_data: Dict): ...
    @staticmethod
    def create_node(...) -> str: ...
    # ... 其他CRUD操作

# Layer 2: CanvasBusinessLogic
class CanvasBusinessLogic:
    def __init__(self, canvas_path: str): ...
    def add_sub_question_with_yellow_node(...): ...
    def update_node_color(...): ...
    def generate_review_canvas(...): ...
    # ... 业务逻辑方法

# Layer 3: CanvasOrchestrator
class CanvasOrchestrator:
    def __init__(self, canvas_path: str): ...
    def handle_basic_decomposition(...): ...
    def handle_scoring(...): ...
    def handle_review_verification(...): ...
    # ... 高级接口方法
```

**何时更新**: 添加新的Canvas操作或修改布局算法时

---

### `.bmad-core/core-config.yaml` ⭐
**用途**: BMad核心配置文件（BMad Integration）
**重要性**: ⭐⭐⭐⭐⭐
**版本**: v2.0

**配置内容**:
```yaml
# devLoadAlwaysFiles: 5个关键文档（~15k tokens）
devLoadAlwaysFiles:
  - docs/architecture/coding-standards.md
  - docs/architecture/tech-stack.md
  - docs/architecture/project-structure.md
  - docs/architecture/canvas-layer-architecture.md
  - CANVAS_ERROR_LOG.md

# Helper System: Token优化（节省70-85%）
helpers:
  enabled: true
  main_file: .bmad-core/data/helpers.md
  sections:
    story_workflow: "Story-Development-Workflow"
    testing: "Testing-Checklist"
    agent_protocol: "Agent-Calling-Protocol"
    canvas_colors: "Canvas-Color-System"
    bmad_phases: "BMad-4-Phase-Workflow"

# SDD规范
specifications:
  enabled: true
  api:
    canvas: specs/api/canvas-api.openapi.yml
    agent: specs/api/agent-api.openapi.yml
  schemas:
    node: specs/data/canvas-node.schema.json
    edge: specs/data/canvas-edge.schema.json
    agent_response: specs/data/agent-response.schema.json
    scoring: specs/data/scoring-response.schema.json

# Skills集成
skills:
  - name: langgraph
    path: .claude/skills/langgraph
    pages: 952
  - name: graphiti
    path: .claude/skills/graphiti
  - name: obsidian-canvas
    path: .claude/skills/obsidian-canvas

# Context7 MCP
context7:
  enabled: true
  libraries:
    - id: "/websites/fastapi_tiangolo"
      name: "FastAPI"
      snippets: 22734
    - id: "/websites/neo4j_cypher-manual_25"
      name: "Neo4j Cypher"
      snippets: 2032
```

**何时更新**: 添加新Skills、修改devLoadAlwaysFiles、调整Helper引用时

---

### `.bmad-core/data/helpers.md` ⭐
**用途**: Helper System主文件（Token优化）
**重要性**: ⭐⭐⭐⭐⭐
**Token节省**: 70-85%

**5个Helper Sections**:
1. **Story-Development-Workflow**: Story开发完整流程（SM使用）
2. **Testing-Checklist**: 测试检查清单（QA使用）
3. **Agent-Calling-Protocol**: Agent调用协议（Dev使用）
4. **Canvas-Color-System**: Canvas颜色系统规范（所有角色使用）
5. **BMad-4-Phase-Workflow**: BMad四阶段工作流（项目管理使用）

**引用语法**:
```markdown
参见: @helpers.md#Story-Development-Workflow
参见: @helpers.md#Testing-Checklist
参见: @helpers.md#Canvas-Color-System
```

**优势**:
- 不在文档中嵌入完整内容（节省token）
- Claude Code自动加载对应section
- 集中维护，一处修改处处生效

**何时更新**: 修改工作流程、更新检查清单时

---

### `.claude/skills/` ⭐
**用途**: Claude Code Skills离线文档（BMad Integration）
**重要性**: ⭐⭐⭐⭐⭐
**零幻觉开发**: 第一优先级文档来源

**3个已安装Skills**:

#### 1. `langgraph/` (952页)
- **内容**: LangGraph框架完整文档
- **激活方式**: 在对话中使用 `@langgraph`
- **适用场景**: 开发Agent系统、StateGraph、Tool调用

#### 2. `graphiti/` (~200页)
- **内容**: Graphiti知识图谱框架文档
- **激活方式**: 在对话中使用 `@graphiti`
- **适用场景**: 记忆系统集成、概念关系管理

#### 3. `obsidian-canvas/` (~150页)
- **内容**: Obsidian Canvas插件开发文档
- **激活方式**: 在对话中使用 `@obsidian-canvas`
- **适用场景**: Canvas JSON操作、节点/边数据结构

**文件结构**:
```
.claude/skills/langgraph/
├── SKILL.md              # Skills主文档（Quick Reference + 完整目录）
└── references/           # 参考文档片段
    ├── reference-1.md
    ├── reference-2.md
    └── ...
```

**使用示例**:
```
开发者: "@langgraph 如何创建StateGraph？"
Claude: [自动加载langgraph skill，查阅SKILL.md]
        根据LangGraph文档，创建StateGraph使用以下API...
```

**何时更新**: 技术栈版本升级时重新生成Skills

---

### `specs/` ⭐
**用途**: Specification-Driven Design (SDD) 规范文件（BMad Integration）
**重要性**: ⭐⭐⭐⭐⭐
**零幻觉开发**: API契约和数据模型的唯一真实来源

#### `specs/api/` - OpenAPI 3.0规范
**文件**:
- `canvas-api.openapi.yml` - Canvas API契约（CRUD操作、查询接口）
- `agent-api.openapi.yml` - Agent API契约（调用、响应格式）

**用途**:
- 定义所有API端点的请求/响应格式
- 作为Contract Testing的测试基准
- 自动生成API文档和Mock Server

#### `specs/data/` - JSON Schema数据模型
**文件**:
- `canvas-node.schema.json` - Canvas节点数据模型
- `canvas-edge.schema.json` - Canvas边数据模型
- `agent-response.schema.json` - Agent响应数据模型
- `scoring-response.schema.json` - 评分响应数据模型

**用途**:
- 验证数据结构的正确性
- 作为代码生成的输入
- 确保跨模块数据一致性

#### `specs/behavior/` - Gherkin行为规范
**文件**:
- `scoring-workflow.feature` - 评分工作流（Given-When-Then）
- `review-board-workflow.feature` - 检验白板生成工作流

**示例**:
```gherkin
Feature: Scoring Agent评分工作流

  Scenario: 评分黄色理解节点
    Given Canvas文件 "离散数学.canvas"
    And 黄色节点 "逆否命题-理解" 存在
    When 调用scoring-agent评分
    Then 返回4维评分结果
    And 总分在0-100之间
```

**何时更新**: 添加新API、修改数据结构、新增业务流程时

---

### `docs/architecture/decisions/` ⭐
**用途**: Architecture Decision Records (ADR)（BMad Integration）
**重要性**: ⭐⭐⭐⭐
**不可变性**: ADR一旦创建不可修改，只能新增

**ADR格式**: Michael Nygard格式
**命名规范**: `NNNN-title-with-dashes.md`

**4个历史ADR**:

#### ADR 0001: 使用Obsidian Canvas作为可视化平台
**决策**: 使用Obsidian Canvas而非自研可视化工具
**理由**: JSON格式易于操作、用户基数大、完全离线

#### ADR 0002: 使用LangGraph构建Agent系统
**决策**: 使用LangGraph而非LangChain
**理由**: StateGraph原生支持、更好的状态管理、简化Agent编排

#### ADR 0003: 使用Graphiti管理记忆系统
**决策**: 使用Graphiti而非自研图数据库抽象
**理由**: Neo4j集成、时序知识图谱、API成本优化

#### ADR 0004: 采用异步并行执行引擎
**决策**: 使用asyncio实现Agent并行调用
**理由**: 8倍性能提升、支持12个Agent并发、非阻塞执行

**文件结构**:
```markdown
# ADR NNNN: 决策标题

**状态**: 已接受 / 已废弃 / 已替代
**日期**: YYYY-MM-DD

## 背景
[问题描述]

## 决策
[采用的方案]

## 理由
[为什么选择此方案]

## 后果
### 积极后果
- [优势1]

### 消极后果
- [代价1]
```

**何时创建**: 做出重大技术决策时（技术栈选型、架构模式、数据结构设计）

**不可变性规则**:
- ❌ **不能**修改已有ADR的内容
- ✅ **可以**新增ADR标记旧ADR为"已废弃"
- ✅ **可以**在新ADR中引用旧ADR

---

### `docs/architecture/*.md`
**用途**: 技术架构文档（分片）
**重要性**: ⭐⭐⭐⭐
**读者**: Scrum Master（生成Story）、Developer（实现Story）

**阅读顺序**（对于Developer）:
1. `index.md` - 了解整体架构
2. `tech-stack.md` - 配置开发环境
3. `unified-project-structure.md` - 了解项目组织（本文档）
4. `coding-standards.md` - 遵循编码规范
5. 根据Story类型阅读特定文档（如`canvas-3-layer-architecture.md`）

---

### `docs/stories/*.story.md`
**用途**: User Story文件
**重要性**: ⭐⭐⭐⭐⭐
**命名规范**: `{epicNum}.{storyNum}.story.md`

**文件结构**:
```markdown
# Story {epicNum}.{storyNum}: {Title}

## Story
作为...，我希望...，以便...

## Acceptance Criteria
- [ ] AC 1
- [ ] AC 2
...

## Dev Notes
### Previous Story Insights
[从上一个Story中学到的经验]

### Data Models
[相关数据模型，带来源引用]

### API Specifications
[API细节，带来源引用]

### Component Specifications
[组件规格，带来源引用]
[Source: architecture/canvas-layout-v1.1.md#布局参数]

### Testing Requirements
[测试要求]

## Tasks / Subtasks
- [ ] Task 1 (AC: 1, 3)
  - [ ] Subtask 1.1
  - [ ] Subtask 1.2
...
```

**何时更新**: SM生成新Story时自动创建

---

### `笔记库/` 目录
**用途**: 用户的Canvas白板和生成的笔记
**重要性**: ⭐⭐⭐⭐⭐（用户数据）

**组织原则**:
- 按学科/主题分文件夹（如`离散数学/`、`托福听力/`）
- 每个主题一个主Canvas文件（如`离散数学.canvas`）
- 检验白板使用命名规范：`{主题}-检验白板-{日期}.canvas`
- 生成的笔记使用命名规范：`{概念}-{Agent类型}-{时间戳}.md`

**示例**:
```
笔记库/离散数学/
├── 离散数学.canvas                        # 主白板
├── 离散数学-检验白板-20250114.canvas       # 1月14日生成的检验白板
├── 逆否命题-口语化解释-20250114153025.md   # 口语化解释笔记
├── 命题逻辑-对比表-20250114160012.md       # 对比表笔记
└── 布尔代数-例题教学-20250115093045.md     # 例题教学笔记
```

**⚠️ 重要**: 此目录应添加到`.gitignore`，不提交到版本控制

---

## 🔄 文件生命周期

### 开发阶段文件创建顺序

#### Phase 1: 项目初始化（Architect完成）
```
✅ docs/project-brief.md
✅ docs/prd/*.md
✅ docs/architecture/*.md
✅ .bmad-core/core-config.yaml
✅ .claude/PROJECT.md
✅ .claude/commands/*.md
```

#### Phase 2: Story生成（SM执行）
```
→ SM运行 /BMad-create-next-story
→ 生成 docs/stories/1.1.story.md
→ 生成 docs/stories/1.2.story.md
→ ...
```

#### Phase 3: 实现（Dev执行）
```
→ Dev读取 docs/stories/1.1.story.md
→ 创建 canvas_utils.py
→ 创建 .claude/agents/canvas-orchestrator.md
→ 创建 .claude/agents/basic-decomposition.md
→ ...
```

#### Phase 4: 测试（QA执行）
```
→ 创建 tests/test_canvas_utils.py
→ 创建 tests/fixtures/*.canvas
→ 运行测试并验证
```

---

## 📊 文件大小和性能考虑

### 预期文件大小

| 文件类型 | 典型大小 | 最大建议大小 | 备注 |
|---------|---------|------------|------|
| `.claude/agents/*.md` | 2-5KB | 10KB | 保持Prompt简洁 |
| `canvas_utils.py` | 15-25KB | 50KB | 如超过50KB考虑拆分模块 |
| `docs/architecture/*.md` | 5-15KB | 30KB | 分片文档，每个文档聚焦 |
| `docs/stories/*.story.md` | 3-8KB | 15KB | 复杂Story可能更大 |
| `.canvas` 文件 | 10-50KB | 200KB | 超过200KB考虑拆分Canvas |
| 生成的.md笔记 | 1-5KB | 10KB | 根据Agent类型不同 |

### 性能优化建议

**Canvas文件过大时**:
- 将大Canvas拆分为多个子Canvas
- 使用group节点组织内容
- 定期归档已完成的内容

**Story文件过大时**:
- 考虑将Story拆分为多个更小的Story
- 减少不必要的技术细节（让Dev回溯架构文档）

---

## 🔒 .gitignore 配置

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/

# IDE
.vscode/
.idea/
*.swp
*.swo

# 用户数据（不提交）
笔记库/*.canvas
笔记库/**/*.md
!笔记库/examples/

# BMad工作文件
.ai/debug-log.md

# 临时文件
*.tmp
*.bak
.DS_Store

# 环境配置
.env
.env.local

# 测试覆盖率
.coverage
htmlcov/
```

**保留提交的内容**:
- ✅ `.claude/agents/*.md` - Agent定义
- ✅ `.claude/PROJECT.md` - 项目上下文
- ✅ `canvas_utils.py` - 核心代码
- ✅ `docs/` - 所有文档
- ✅ `tests/` - 测试代码
- ✅ `笔记库/examples/` - 示例Canvas文件
- ❌ `笔记库/` 其他内容 - 用户个人学习数据

---

## 🚀 快速导航命令

### 常用目录跳转

```bash
# 跳转到项目根目录
cd "C:/Users/ROG/托福"

# 跳转到Agent定义目录
cd .claude/agents

# 跳转到架构文档目录
cd docs/architecture

# 跳转到Story目录
cd docs/stories

# 跳转到用户笔记库
cd 笔记库
```

### 常用文件打开

```bash
# 查看项目上下文
cat .claude/PROJECT.md

# 查看核心配置
cat .bmad-core/core-config.yaml

# 查看架构索引
cat docs/architecture/index.md

# 列出所有Agent
ls .claude/agents/
```

---

## ✅ 项目结构验证清单 (含BMad验证)

在开始开发前，确认以下结构已就绪：

**目录结构**:
- [ ] `.claude/agents/` 目录存在（14个Agent）
- [ ] `.claude/commands/` 目录存在
- [ ] `.claude/skills/` 目录存在（langgraph, graphiti, obsidian-canvas）⭐
- [ ] `.bmad-core/data/` 目录存在 ⭐
- [ ] `.bmad-core/templates/` 目录存在 ⭐
- [ ] `specs/api/` 目录存在 ⭐
- [ ] `specs/data/` 目录存在 ⭐
- [ ] `specs/behavior/` 目录存在 ⭐
- [ ] `docs/prd/` 目录存在
- [ ] `docs/architecture/` 目录存在（包含8个文档）
- [ ] `docs/architecture/decisions/` 目录存在（4个ADR）⭐
- [ ] `docs/stories/` 目录存在
- [ ] `tests/contract/` 目录存在 ⭐
- [ ] `scripts/` 目录存在（含重组脚本）⭐
- [ ] `笔记库/` 目录存在

**关键文件**:
- [ ] `.claude/PROJECT.md` 存在
- [ ] `.bmad-core/core-config.yaml` 存在（v2.0）⭐
- [ ] `.bmad-core/data/helpers.md` 存在 ⭐
- [ ] `docs/project-brief.md` 存在
- [ ] `docs/RESEARCH_REPORT_BMAD_INTEGRATION.md` 存在 ⭐
- [ ] `docs/architecture/index.md` 存在
- [ ] `docs/architecture/tech-stack.md` 存在（v2.0含BMad）⭐
- [ ] `docs/architecture/coding-standards.md` 存在（v2.0含BMad）⭐
- [ ] `docs/architecture/project-structure.md` 存在（v2.0含BMad）⭐
- [ ] `docs/architecture/canvas-layer-architecture.md` 存在（v2.0）⭐
- [ ] `.gitignore` 已配置

**Skills验证** ⭐:
- [ ] `.claude/skills/langgraph/SKILL.md` 存在
- [ ] `.claude/skills/graphiti/SKILL.md` 存在
- [ ] `.claude/skills/obsidian-canvas/SKILL.md` 存在

**ADR验证** ⭐:
- [ ] `docs/architecture/decisions/0001-use-obsidian-canvas.md` 存在
- [ ] `docs/architecture/decisions/0002-langgraph-agents.md` 存在
- [ ] `docs/architecture/decisions/0003-graphiti-memory.md` 存在
- [ ] `docs/architecture/decisions/0004-async-execution-engine.md` 存在

**验证命令**:
```bash
cd "C:/Users/ROG/托福"

# Canvas原有结构验证
test -d .claude/agents && echo "✅ agents目录存在"
test -f .claude/PROJECT.md && echo "✅ PROJECT.md存在"
test -d docs/architecture && echo "✅ architecture目录存在"
test -f docs/project-brief.md && echo "✅ project-brief.md存在"

# BMad集成验证 ⭐
test -f .bmad-core/core-config.yaml && echo "✅ BMad core-config.yaml存在"
test -f .bmad-core/data/helpers.md && echo "✅ Helper System存在"
test -d .claude/skills/langgraph && echo "✅ LangGraph Skill存在"
test -d .claude/skills/graphiti && echo "✅ Graphiti Skill存在"
test -d .claude/skills/obsidian-canvas && echo "✅ Obsidian Canvas Skill存在"
test -d specs/api && echo "✅ OpenAPI规范目录存在"
test -d specs/data && echo "✅ JSON Schema目录存在"
test -d specs/behavior && echo "✅ Gherkin规范目录存在"
test -d docs/architecture/decisions && echo "✅ ADR目录存在"
test -d tests/contract && echo "✅ Contract Testing目录存在"

# 验证Agent数量（应该是14个）
AGENT_COUNT=$(ls .claude/agents/*.md 2>/dev/null | wc -l)
if [ "$AGENT_COUNT" -eq 14 ]; then
  echo "✅ Agent数量正确: 14个"
else
  echo "⚠️ Agent数量异常: $AGENT_COUNT 个（预期14个）"
fi

# 验证ADR数量（应该是4个）
ADR_COUNT=$(ls docs/architecture/decisions/*.md 2>/dev/null | wc -l)
if [ "$ADR_COUNT" -eq 4 ]; then
  echo "✅ ADR数量正确: 4个"
else
  echo "⚠️ ADR数量异常: $ADR_COUNT 个（预期4个）"
fi
```

---

## 📞 项目结构问题

如果遇到路径或结构问题：
1. 检查 `.bmad-core/core-config.yaml` 的路径配置
2. 确保使用绝对路径或正确的相对路径
3. 验证文件权限（确保可读写）
4. 参考本文档的标准结构

---

**文档版本**: v2.0 (BMad Integration)
**最后更新**: 2025-11-17
**维护者**: Architect Agent + BMad Framework
