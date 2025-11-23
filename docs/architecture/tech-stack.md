---
document_type: "Architecture"
version: "1.0.0"
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

# 技术栈 - Canvas学习系统

**版本**: v1.0
**最后更新**: 2025-01-14

---

## 📦 核心技术栈

### 运行环境

| 技术 | 版本要求 | 用途 | 备注 |
|------|---------|------|------|
| **Python** | 3.9+ | Canvas操作库 | 推荐使用3.11以获得更好的性能 |
| **Claude Code CLI** | Latest | AI Agent运行环境 | 需要有效的API Key |
| **Obsidian** | 1.4.0+ | Canvas可视化平台 | 必须安装Canvas插件 |
| **JSON Canvas** | 1.0 | Canvas文件格式标准 | 完全兼容 |

### Python库依赖

```python
# requirements.txt
uuid>=1.30          # 用于生成节点ID
json>=2.0           # JSON文件解析
typing>=3.7         # 类型注解
pathlib>=1.0        # 文件路径操作
datetime>=4.0       # 时间戳生成
```

**安装命令**:
```bash
pip install -r requirements.txt
```

---

## 🤖 AI技术栈

### Claude Code Sub-agents

| 组件 | 技术 | 配置位置 |
|------|------|---------|
| **Sub-agent定义** | Markdown + YAML Frontmatter | `.claude/agents/*.md` |
| **Agent调用** | 自然语言 | 通过Claude Code的agent系统 |
| **Model** | claude-sonnet-4.5 | 在YAML frontmatter中指定 |

**Agent配置示例**:
```yaml
---
name: basic-decomposition
description: Decomposes difficult materials into basic guiding questions
tools: Read
model: sonnet
---
```

---

## 📁 文件格式规范

### Canvas文件格式（JSON Canvas 1.0）

```json
{
  "nodes": [
    {
      "id": "string",
      "type": "text" | "file" | "group",
      "text": "string (for type=text)",
      "file": "string (for type=file)",
      "x": number,
      "y": number,
      "width": number,
      "height": number,
      "color": "1" | "2" | "3" | "4" | "5" | "6"
    }
  ],
  "edges": [
    {
      "id": "string",
      "fromNode": "string",
      "toNode": "string",
      "fromSide": "top" | "right" | "bottom" | "left",
      "toSide": "top" | "right" | "bottom" | "left",
      "label": "string (optional)"
    }
  ]
}
```

**关键约束**:
- 节点ID必须唯一（推荐使用UUID v4）
- 颜色值必须是字符串 `"1"`-`"6"`
- 所有坐标为整数（像素单位）

### Markdown笔记格式

生成的解释笔记遵循以下格式：
```markdown
# [概念名称] - [Agent类型]

## 生成信息
- 生成时间: 2025-01-14 15:30:25
- 生成Agent: oral-explanation
- 来源Canvas: 离散数学.canvas
- 来源节点: node-abc123

## 内容部分
[Agent特定的内容结构]

---
**文件位置**: 与Canvas文件同目录
**命名规范**: [主题]-[Agent类型]-[时间戳].md
```

---

## 🎨 颜色系统（Obsidian Canvas标准）

| Canvas Color Code | 视觉颜色 | 含义 | 使用场景 |
|-------------------|---------|------|---------|
| `"1"` | 🔴 红色 | 不理解/未通过 | 难懂的材料、未通过评分的理解 |
| `"2"` | 🟠 橙色 | （未使用） | 保留 |
| `"3"` | 🟡 黄色 | （系统用途不同） | ⚠️ 在我们系统中黄色是`"6"` |
| `"4"` | 🟢 绿色 | 完全理解/已通过 | ⚠️ 实际使用`"2"`表示绿色 |
| `"5"` | 🟣 紫色 | （实际使用`"3"`） | 似懂非懂/待检验 |
| `"6"` | 🔵 蓝色（我们用作黄色） | 个人理解输出区 | 费曼学习法输出板块 |

**⚠️ 重要说明**:
Obsidian Canvas的颜色编码与视觉颜色不完全对应。我们的系统使用：
- `"1"` = 红色（不理解）
- `"2"` = 绿色（完全理解）
- `"3"` = 紫色（似懂非懂）
- `"6"` = 黄色（个人理解）

**验证方法**:
参考文件：`C:/Users/ROG/托福/笔记库/颜色参考样例2.canvas`

---

## 🗂️ 项目结构

```
C:/Users/ROG/托福/
├── .claude/                      # Claude Code配置
│   ├── PROJECT.md                # 项目上下文（自动加载）
│   ├── agents/                   # 13个Sub-agent定义
│   │   ├── canvas-orchestrator.md
│   │   ├── basic-decomposition.md
│   │   ├── deep-decomposition.md
│   │   ├── problem-decomposition.md
│   │   ├── oral-explanation.md
│   │   ├── clarification-path.md
│   │   ├── comparison-table.md
│   │   ├── memory-anchor.md
│   │   ├── four-level-explanation.md
│   │   ├── example-teaching.md
│   │   ├── scoring-agent.md
│   │   ├── review-verification.md
│   │   └── canvas-operations.md
│   └── commands/                 # 自定义命令
│       ├── activate-canvas-mode.md
│       └── list-agents.md
├── .bmad-core/                   # BMad开发框架
│   └── core-config.yaml
├── canvas_utils.py               # ⭐ Canvas操作Python库
├── docs/                         # 文档
│   ├── project-brief.md
│   ├── prd/
│   ├── architecture/
│   └── stories/
└── 笔记库/                        # 用户Canvas文件
    ├── 离散数学/
    │   ├── 离散数学.canvas
    │   ├── 逆否命题-口语化解释-20250114.md
    │   └── ...
    ├── 托福听力/
    └── ...
```

---

## 🧪 开发和测试环境

### 本地开发环境要求

```bash
# 1. 安装Python 3.9+
python --version  # 应输出 3.9.x 或更高

# 2. 安装Claude Code CLI
# 参考：https://docs.anthropic.com/claude-code/

# 3. 验证Obsidian Canvas插件
# 在Obsidian中打开：设置 → 核心插件 → Canvas（应已启用）

# 4. 安装Python依赖
cd C:/Users/ROG/托福
pip install -r requirements.txt

# 5. 验证Sub-agents可用
claude code
/list-agents  # 应列出13个Agent
```

### 测试Canvas文件

使用测试Canvas文件验证系统功能：
```
笔记库/examples/
├── test-basic-decomposition.canvas    # 测试基础拆解
├── test-scoring.canvas                # 测试评分功能
└── test-review-verification.canvas    # 测试检验白板生成
```

### 单元测试（Dev阶段实现）

```bash
# 运行canvas_utils.py的单元测试
pytest tests/test_canvas_utils.py

# 运行特定层的测试
pytest tests/test_canvas_utils.py::TestCanvasJSONOperator
pytest tests/test_canvas_utils.py::TestCanvasBusinessLogic
pytest tests/test_canvas_utils.py::TestCanvasOrchestrator
```

---

## 🔧 工具和辅助脚本

### 颜色验证脚本

```python
# scripts/verify_colors.py
# 用于验证Canvas文件中的颜色编码

import json
import sys

def verify_canvas_colors(canvas_path):
    with open(canvas_path, 'r', encoding='utf-8') as f:
        canvas = json.load(f)

    color_counts = {"1": 0, "2": 0, "3": 0, "6": 0}
    for node in canvas.get("nodes", []):
        color = node.get("color")
        if color in color_counts:
            color_counts[color] += 1

    print(f"颜色统计:")
    print(f"  红色 (\"1\"): {color_counts['1']} 个节点")
    print(f"  绿色 (\"2\"): {color_counts['2']} 个节点")
    print(f"  紫色 (\"3\"): {color_counts['3']} 个节点")
    print(f"  黄色 (\"6\"): {color_counts['6']} 个节点")

if __name__ == "__main__":
    verify_canvas_colors(sys.argv[1])
```

**使用方法**:
```bash
python scripts/verify_colors.py "笔记库/离散数学/离散数学.canvas"
```

---

## 📊 性能要求

### Canvas文件大小限制

| 节点数量 | 文件大小 | 响应时间 | 建议 |
|---------|---------|---------|------|
| < 50 | < 50KB | < 1秒 | ✅ 理想 |
| 50-100 | 50-100KB | 1-3秒 | ✅ 可接受 |
| 100-200 | 100-200KB | 3-5秒 | ⚠️ 考虑分割Canvas |
| > 200 | > 200KB | > 5秒 | ❌ 必须分割Canvas |

### Agent响应时间目标

| Agent类型 | 目标响应时间 | 最大响应时间 |
|----------|-------------|-------------|
| 基础拆解 | 5-10秒 | 20秒 |
| 深度拆解 | 10-15秒 | 30秒 |
| 口语化解释 | 15-20秒 | 40秒 |
| 评分 | 5-8秒 | 15秒 |
| 检验白板生成 | 10-20秒 | 40秒 |

---

## 🔐 安全和隐私

### API Key管理

```bash
# 环境变量配置
export ANTHROPIC_API_KEY="sk-ant-..."

# 或使用.env文件（不提交到Git）
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env
```

### 数据隐私

- ✅ Canvas文件存储在本地（不上传到云端）
- ✅ 笔记内容仅在AI处理时发送到Claude API
- ✅ 不收集用户学习数据
- ⚠️ 建议将笔记库/目录添加到.gitignore

---

## 🚀 BMad Method技术栈 (BMad Integration)

### BMad核心组件

| 组件 | 技术 | 用途 |
|------|------|------|
| **BMad Core** | YAML配置 | 项目配置和上下文管理 |
| **Helper System** | Markdown引用 | Token优化（节省70-85%） |
| **Document Sharding** | Markdown分片 | 超大文档管理 |
| **DevLoadAlwaysFiles** | 自动加载机制 | 关键文档永久可用 |

**配置位置**: `.bmad-core/core-config.yaml`

---

## 📖 Claude Code Skills系统 (离线文档)

### 已安装Skills

| Skill名称 | 内容 | 文档量 | 激活方式 |
|----------|------|-------|---------|
| **langgraph** | LangGraph框架完整文档 | 952页 | `@langgraph` |
| **graphiti** | Graphiti知识图谱框架 | ~200页 | `@graphiti` |
| **obsidian-canvas** | Obsidian Canvas插件开发 | ~150页 | `@obsidian-canvas` |

**Skills位置**: `.claude/skills/`

### Skills激活示例

```bash
# 在Claude Code对话中
"@langgraph 如何创建StateGraph？"
"@graphiti 如何存储概念关系？"
"@obsidian-canvas Canvas JSON格式的节点结构是什么？"
```

**零幻觉开发规则**: 使用LangGraph/Graphiti/Obsidian Canvas相关API前，**必须**先激活对应Skill并验证API参数。

---

## 🌐 Context7 MCP集成 (在线文档)

### Context7配置

未生成Skills的技术栈通过**Context7 MCP**查询：

| 技术栈 | Library ID | Snippets | 用途 |
|--------|-----------|----------|------|
| **FastAPI** | `/websites/fastapi_tiangolo` | 22,734 | Web API框架 |
| **Neo4j Cypher** | `/websites/neo4j_cypher-manual_25` | 2,032 | 图数据库查询语言 |
| **Neo4j Operations** | `/websites/neo4j_operations-manual-current` | 4,940 | Neo4j运维管理 |

**查询方式**:
```python
# 示例：查询FastAPI依赖注入文档
mcp__context7-mcp__get-library-docs(
    context7CompatibleLibraryID="/websites/fastapi_tiangolo",
    topic="Dependency Injection",
    page=1
)
```

**零幻觉开发规则**: 使用FastAPI/Neo4j相关API前，**必须**先查询Context7并标注来源。

---

## 🎯 Specification-Driven Design (SDD)工具栈

### OpenAPI 3.0（API契约）

**工具**: Swagger Editor, OpenAPI Generator

**用途**:
- 定义Canvas API契约（`specs/api/canvas-api.openapi.yml`）
- 定义Agent API契约（`specs/api/agent-api.openapi.yml`）

**示例**:
```yaml
openapi: 3.0.0
info:
  title: Canvas Learning System API
  version: 1.0.0
paths:
  /canvas/{canvasId}/nodes:
    post:
      summary: Add node to canvas
      parameters:
        - name: canvasId
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/NodeCreateRequest'
```

### JSON Schema（数据模型）

**工具**: JSON Schema Validator

**用途**:
- 定义Canvas节点数据模型（`specs/data/canvas-node.schema.json`）
- 定义Agent响应数据模型（`specs/data/agent-response.schema.json`）

**示例**:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "canvas-node.schema.json",
  "title": "Canvas Node",
  "type": "object",
  "required": ["id", "type", "x", "y", "width", "height"],
  "properties": {
    "id": {
      "type": "string",
      "pattern": "^[a-z]+-[a-f0-9]{16}$"
    },
    "type": {
      "type": "string",
      "enum": ["text", "file", "group", "link"]
    },
    "color": {
      "type": "string",
      "enum": ["1", "2", "3", "5", "6"]
    }
  }
}
```

### Gherkin/Cucumber（行为规范）

**工具**: Cucumber, pytest-bdd

**用途**:
- 定义评分工作流（`specs/behavior/scoring-workflow.feature`）
- 定义检验白板生成工作流（`specs/behavior/review-board-workflow.feature`）

**示例**:
```gherkin
# scoring-workflow.feature
Feature: Scoring Agent评分工作流

  Scenario: 评分黄色理解节点
    Given Canvas文件 "离散数学.canvas"
    And 黄色节点 "逆否命题-理解" 存在
    When 调用scoring-agent评分
    Then 返回4维评分结果
    And 准确性分数在0-25之间
    And 具象性分数在0-25之间
    And 完整性分数在0-25之间
    And 原创性分数在0-25之间
    And 总分在0-100之间
```

### Schemathesis（契约测试）

**工具**: Schemathesis

**用途**: 自动化契约测试，验证实现100%符合OpenAPI规范

**使用方式**:
```bash
# 测试Canvas API
schemathesis run specs/api/canvas-api.openapi.yml \
  --base-url http://localhost:8000 \
  --checks all

# 测试Agent API
schemathesis run specs/api/agent-api.openapi.yml \
  --base-url http://localhost:8000 \
  --checks all
```

**集成到pytest**:
```python
# tests/contract/test_canvas_contracts.py
import schemathesis

schema = schemathesis.from_path("specs/api/canvas-api.openapi.yml")

@schema.parametrize()
def test_canvas_api_contract(case):
    response = case.call()
    case.validate_response(response)
```

---

## 📋 Architecture Decision Records (ADR)工具

### ADR格式

**标准**: Michael Nygard ADR格式

**工具**: adr-tools (可选)

**命名规范**: `NNNN-title-with-dashes.md`

**示例**:
```markdown
# ADR 0001: 使用Obsidian Canvas作为可视化平台

**状态**: 已接受

**日期**: 2025-01-14

## 背景

我们需要一个可视化平台来实现费曼学习法的知识图谱。

## 决策

我们将使用Obsidian Canvas作为可视化平台。

## 理由

1. Canvas提供原生的节点-边图谱支持
2. JSON格式易于程序化操作
3. 用户基数大，社区活跃
4. 完全离线，保护用户隐私

## 后果

### 积极后果
- 用户可以直接在Obsidian中学习
- 无需额外安装可视化工具

### 消极后果
- 依赖Obsidian Canvas的JSON格式稳定性
- 需要用户已安装Obsidian
```

**ADR存储位置**: `docs/architecture/decisions/`

---

## 📚 外部依赖文档

### 核心规范

- **JSON Canvas规范**: https://jsoncanvas.org/spec/1.0/
- **Claude Code文档**: https://docs.anthropic.com/claude-code/
- **Obsidian Canvas插件**: https://help.obsidian.md/Plugins/Canvas
- **Python官方文档**: https://docs.python.org/3.9/

### SDD相关文档

- **OpenAPI 3.0规范**: https://swagger.io/specification/
- **JSON Schema规范**: https://json-schema.org/
- **Gherkin语法**: https://cucumber.io/docs/gherkin/reference/
- **Schemathesis文档**: https://schemathesis.readthedocs.io/

### BMad Method文档

- **BMad Core GitHub**: https://github.com/PriNova/Claude-Breakthru-Method-Agentic-Development
- **BMad核心理念**: C.O.R.E. (Collaboration, Optimized, Reflection, Engine)
- **Document Sharding策略**: 按## headings拆分，单文档<20k tokens

---

## ✅ 技术栈验证清单

在开始开发前，确认以下环境已就绪：

**基础环境**:
- [ ] Python 3.9+ 已安装
- [ ] Claude Code CLI 已安装并配置API Key
- [ ] Obsidian 已安装，Canvas插件已启用
- [ ] 项目目录结构已创建
- [ ] `.claude/agents/` 目录存在
- [ ] 颜色参考样例文件可访问
- [ ] 可以创建和编辑.canvas文件

**BMad环境** (新增):
- [ ] `.bmad-core/core-config.yaml` 已配置
- [ ] `.claude/skills/langgraph/` 存在
- [ ] `.claude/skills/graphiti/` 存在
- [ ] `.claude/skills/obsidian-canvas/` 存在
- [ ] Context7 MCP已配置并可用
- [ ] `specs/api/` 目录已创建
- [ ] `specs/data/` 目录已创建
- [ ] `specs/behavior/` 目录已创建
- [ ] `docs/architecture/decisions/` 目录已创建

**验证命令**:
```bash
# 基础验证
python --version
claude --version
ls .claude/agents/
ls "笔记库/颜色参考样例2.canvas"

# BMad验证
ls .bmad-core/core-config.yaml
ls .claude/skills/langgraph/SKILL.md
ls .claude/skills/graphiti/SKILL.md
ls specs/api/
ls specs/data/
ls specs/behavior/
ls docs/architecture/decisions/
```

---

**文档版本**: v2.0 (BMad Integration)
**最后更新**: 2025-11-17
**维护者**: Architect Agent + BMad Framework
