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

# 编码规范 - Canvas学习系统

**版本**: v1.0
**最后更新**: 2025-01-14

---

## 🎯 编码规范概述

本文档定义Canvas学习系统的编码标准和最佳实践，适用于：
- Python代码（`canvas_utils.py`）
- Sub-agent定义文件（`.claude/agents/*.md`）
- 文档编写

---

## 🐍 Python编码规范

### 基础规范：PEP 8

遵循 [PEP 8 - Style Guide for Python Code](https://peps.python.org/pep-0008/)

**关键要点**:
- 使用4个空格缩进（不使用Tab）
- 每行最多79字符（文档字符串和注释最多72字符）
- 使用UTF-8编码
- 导入语句放在文件顶部

### 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| **类名** | PascalCase | `CanvasJSONOperator`, `CanvasOrchestrator` |
| **函数名** | snake_case | `read_canvas()`, `add_sub_question()` |
| **变量名** | snake_case | `canvas_data`, `node_id`, `yellow_pos` |
| **常量** | UPPER_SNAKE_CASE | `HORIZONTAL_SPACING`, `DEFAULT_NODE_WIDTH` |
| **私有方法** | _leading_underscore | `_calculate_position()`, `_validate_node()` |
| **模块名** | snake_case | `canvas_utils.py` |

### 类型注解（Type Hints）

**强制使用**类型注解，提高代码可读性和可维护性：

```python
from typing import Dict, List, Tuple, Optional, Union

def read_canvas(canvas_path: str) -> Dict:
    """读取Canvas文件并返回JSON数据"""
    pass

def create_node(
    canvas_data: Dict,
    node_type: str,
    x: int,
    y: int,
    width: int = 400,
    height: int = 300,
    color: Optional[str] = None
) -> str:
    """创建节点并返回节点ID"""
    pass

def add_sub_question_with_yellow_node(
    material_node_id: str,
    question_text: str,
    guidance: str = ""
) -> Tuple[str, str]:
    """
    添加问题节点和黄色理解节点

    Returns:
        Tuple[str, str]: (question_node_id, yellow_node_id)
    """
    pass
```

### 文档字符串（Docstrings）

使用 Google Style Docstrings：

```python
def add_sub_question_with_yellow_node(
    self,
    material_node_id: str,
    question_text: str,
    guidance: str = ""
) -> Tuple[str, str]:
    """添加子问题和黄色理解节点（使用v1.1布局）

    Args:
        material_node_id: 材料节点的ID
        question_text: 问题文本内容
        guidance: 可选的引导性提示（如"💡 提示：..."）

    Returns:
        Tuple[str, str]: (问题节点ID, 黄色理解节点ID)

    Raises:
        ValueError: 如果material_node_id不存在
        FileNotFoundError: 如果Canvas文件不存在

    Example:
        >>> orchestrator = CanvasOrchestrator("test.canvas")
        >>> q_id, y_id = orchestrator.add_sub_question_with_yellow_node(
        ...     "node-abc123",
        ...     "什么是逆否命题？",
        ...     "💡 提示：从定义出发思考"
        ... )
        >>> print(f"创建了问题节点 {q_id} 和理解节点 {y_id}")
    """
    pass
```

### 错误处理

**原则**: 明确的错误类型 + 有意义的错误消息

```python
# ✅ 好的做法
def read_canvas(canvas_path: str) -> Dict:
    if not os.path.exists(canvas_path):
        raise FileNotFoundError(
            f"Canvas文件不存在: {canvas_path}"
        )

    try:
        with open(canvas_path, 'r', encoding='utf-8') as f:
            canvas_data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Canvas文件JSON格式错误: {canvas_path}\n"
            f"错误详情: {e}"
        )

    if "nodes" not in canvas_data:
        raise ValueError(
            f"Canvas文件缺少'nodes'字段: {canvas_path}"
        )

    return canvas_data

# ❌ 不好的做法
def read_canvas(canvas_path: str) -> Dict:
    with open(canvas_path) as f:  # 没有错误处理
        return json.load(f)  # 错误消息不明确
```

### 常量定义

将布局参数定义为常量：

```python
# canvas_utils.py 顶部

# ========== 布局参数常量 ==========
# v1.1布局算法参数（黄色节点在问题下方）

# 节点尺寸
DEFAULT_NODE_WIDTH = 400
DEFAULT_NODE_HEIGHT = 300
YELLOW_NODE_WIDTH = 350
YELLOW_NODE_HEIGHT = 150

# 间距参数
HORIZONTAL_SPACING = 450  # 材料到问题的水平间距
VERTICAL_SPACING_BASE = 380  # 问题+黄色组合的垂直间距
YELLOW_OFFSET_X = 0  # 黄色节点水平偏移（相对问题节点）
YELLOW_OFFSET_Y = 30  # 黄色节点垂直偏移（相对问题节点底部）
EXPLANATION_CHAIN_SPACING = 80  # 解释节点链式展开间距

# 颜色代码
COLOR_RED = "1"      # 不理解/未通过
COLOR_GREEN = "2"    # 完全理解/已通过
COLOR_PURPLE = "3"   # 似懂非懂/待检验
COLOR_YELLOW = "6"   # 个人理解输出区

# ========== 类定义开始 ==========
```

### 代码组织

**canvas_utils.py 文件结构**:

```python
"""
Canvas学习系统 - Canvas操作工具库

本模块实现3层架构的Canvas操作功能：
- Layer 1: CanvasJSONOperator - 底层JSON CRUD操作
- Layer 2: CanvasBusinessLogic - 业务逻辑和布局算法
- Layer 3: CanvasOrchestrator - 高级接口供Sub-agents调用

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-14
"""

import json
import uuid
import os
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from datetime import datetime

# ========== 常量定义 ==========
# [如上节所示]

# ========== Layer 1: CanvasJSONOperator ==========
class CanvasJSONOperator:
    """Canvas JSON文件的底层操作

    提供读写、节点CRUD、边CRUD等基础操作，不包含业务逻辑。
    """

    @staticmethod
    def read_canvas(canvas_path: str) -> Dict:
        """读取Canvas文件"""
        pass

    @staticmethod
    def write_canvas(canvas_path: str, canvas_data: Dict) -> None:
        """写入Canvas文件"""
        pass

    # ... 其他方法

# ========== Layer 2: CanvasBusinessLogic ==========
class CanvasBusinessLogic:
    """Canvas业务逻辑层

    实现v1.1布局算法、节点关系管理等业务逻辑。
    """

    def __init__(self, canvas_path: str):
        """初始化业务逻辑层"""
        pass

    def add_sub_question_with_yellow_node(self, ...) -> Tuple[str, str]:
        """添加问题+黄色理解组合"""
        pass

    # ... 其他方法

# ========== Layer 3: CanvasOrchestrator ==========
class CanvasOrchestrator:
    """Canvas操作的高级接口

    供Sub-agents调用的高级接口，封装完整的业务流程。
    """

    def __init__(self, canvas_path: str):
        """初始化Orchestrator"""
        pass

    def handle_basic_decomposition(self, ...) -> None:
        """处理基础拆解结果"""
        pass

    # ... 其他方法
```

---

## 📝 Markdown编码规范

### Agent定义文件（.claude/agents/*.md）

**文件模板**:

```markdown
---
name: agent-name
description: One-line description (less than 80 chars)
tools: Read, Write, Edit
model: sonnet
---

# Agent名称

## Role
[简短的角色描述，2-3句话]

## Input Format
你将接收以下JSON格式的输入：
```json
{
  "key1": "value1",
  "key2": "value2"
}
```

## Output Format
你必须返回以下JSON格式的输出：
```json
{
  "key1": "value1",
  "key2": ["item1", "item2"]
}
```

**⚠️ 重要**:
- 只返回JSON，不要包含任何其他文本
- 不要使用Markdown代码块（```json）包裹JSON
- 确保JSON格式正确

## System Prompt

### 你的任务
[详细描述Agent的任务]

### 规则
1. [规则1]
2. [规则2]
...

### 示例

**输入示例**:
```json
{...}
```

**输出示例**:
```json
{...}
```

### 质量标准
- [标准1]
- [标准2]
...
```

### 架构文档（docs/architecture/*.md）

**文件头部**:
```markdown
# 文档标题

**版本**: v1.0
**最后更新**: 2025-01-14

---
```

**章节结构**:
- 使用 `##` 表示主要章节
- 使用 `###` 表示子章节
- 使用 `####` 表示细节章节（最多到4级）

**代码块**:
````markdown
```python
# 使用语法高亮
def example():
    pass
```
````

**表格对齐**:
```markdown
| 列1 | 列2 | 列3 |
|-----|-----|-----|
| 值1 | 值2 | 值3 |
```

---

## 📐 JSON格式规范

### Canvas JSON格式

**节点定义**:
```json
{
  "id": "node-{uuid16}",
  "type": "text",
  "text": "节点文本内容",
  "x": 100,
  "y": 200,
  "width": 400,
  "height": 300,
  "color": "1"
}
```

**规范要求**:
- `id`: 使用 `{prefix}-{uuid16}` 格式（如 `question-a1b2c3d4e5f67890`）
- `type`: 只能是 `"text"`, `"file"`, `"group"`
- `color`: 必须是字符串 `"1"` 到 `"6"`，不能是数字
- 坐标和尺寸: 必须是整数，不能是浮点数

### Agent输入/输出JSON

**一致性原则**:
- 使用snake_case命名（如 `sub_questions`, `user_understanding`）
- 布尔值使用true/false（小写）
- 字符串使用双引号
- 不使用尾部逗号

**示例**:
```json
{
  "sub_questions": [
    {
      "text": "问题文本",
      "type": "定义型",
      "difficulty": "基础",
      "guidance": "💡 提示文字"
    }
  ],
  "total_count": 3,
  "has_guidance": true
}
```

---

## ✅ 代码审查清单

### Python代码审查

- [ ] 遵循PEP 8规范
- [ ] 所有函数有类型注解
- [ ] 所有公共函数有Docstring
- [ ] 错误处理明确且有意义
- [ ] 使用常量而非魔法数字
- [ ] 变量命名清晰易懂
- [ ] 代码复杂度合理（单个函数不超过50行）
- [ ] 没有硬编码路径（使用配置或参数）

### Agent定义审查

- [ ] YAML frontmatter格式正确
- [ ] `name`与文件名一致（kebab-case）
- [ ] `description`简洁明了（<80字符）
- [ ] 输入/输出格式有JSON示例
- [ ] System prompt清晰具体
- [ ] 包含至少一个完整的输入/输出示例
- [ ] 特别强调只返回JSON（如果适用）

### 文档审查

- [ ] 有版本号和更新日期
- [ ] 章节结构清晰
- [ ] 代码示例语法正确
- [ ] 表格对齐整齐
- [ ] 没有拼写错误
- [ ] 链接有效

---

## 🧪 测试规范

### 单元测试

**文件命名**: `test_{module_name}.py`

**测试函数命名**: `test_{function_name}_{scenario}`

**示例**:
```python
# tests/test_canvas_utils.py

import pytest
from canvas_utils import CanvasJSONOperator, CanvasBusinessLogic

class TestCanvasJSONOperator:
    """测试CanvasJSONOperator类"""

    def test_read_canvas_success(self):
        """测试成功读取Canvas文件"""
        # Arrange
        canvas_path = "tests/fixtures/test-basic.canvas"

        # Act
        canvas_data = CanvasJSONOperator.read_canvas(canvas_path)

        # Assert
        assert "nodes" in canvas_data
        assert "edges" in canvas_data

    def test_read_canvas_file_not_found(self):
        """测试读取不存在的Canvas文件抛出异常"""
        with pytest.raises(FileNotFoundError):
            CanvasJSONOperator.read_canvas("nonexistent.canvas")

    def test_create_node_with_default_params(self):
        """测试使用默认参数创建节点"""
        canvas_data = {"nodes": [], "edges": []}
        node_id = CanvasJSONOperator.create_node(
            canvas_data,
            node_type="text",
            x=100,
            y=200
        )

        assert node_id.startswith("text-")
        assert len(canvas_data["nodes"]) == 1
        assert canvas_data["nodes"][0]["width"] == 400  # 默认值
```

### 测试覆盖率目标

| 层级 | 目标覆盖率 |
|------|----------|
| Layer 1 (CanvasJSONOperator) | ≥ 90% |
| Layer 2 (CanvasBusinessLogic) | ≥ 85% |
| Layer 3 (CanvasOrchestrator) | ≥ 80% |
| 整体 | ≥ 85% |

---

## 🚀 性能最佳实践

### 避免重复读取Canvas文件

```python
# ❌ 不好的做法（每次调用都读取文件）
def add_multiple_nodes(canvas_path, nodes):
    for node_data in nodes:
        canvas_data = read_canvas(canvas_path)  # 重复读取！
        create_node(canvas_data, **node_data)
        write_canvas(canvas_path, canvas_data)

# ✅ 好的做法（读取一次，批量操作）
def add_multiple_nodes(canvas_path, nodes):
    canvas_data = read_canvas(canvas_path)  # 只读取一次
    for node_data in nodes:
        create_node(canvas_data, **node_data)
    write_canvas(canvas_path, canvas_data)  # 只写入一次
```

### 使用with语句管理资源

```python
# ✅ 好的做法
def read_canvas(canvas_path: str) -> Dict:
    with open(canvas_path, 'r', encoding='utf-8') as f:
        return json.load(f)
```

---

## 📚 推荐工具

### Python工具

| 工具 | 用途 | 安装命令 |
|------|------|---------|
| **black** | 代码格式化 | `pip install black` |
| **pylint** | 静态代码分析 | `pip install pylint` |
| **mypy** | 类型检查 | `pip install mypy` |
| **pytest** | 单元测试 | `pip install pytest` |
| **pytest-cov** | 测试覆盖率 | `pip install pytest-cov` |

### 使用示例

```bash
# 格式化代码
black canvas_utils.py

# 静态分析
pylint canvas_utils.py

# 类型检查
mypy canvas_utils.py

# 运行测试并生成覆盖率报告
pytest --cov=canvas_utils tests/
```

---

## 🔴 零幻觉开发规范 (BMad Integration)

### 核心原则

**"提到什么技术，立即查阅Skills或Context7"**

### 适用范围

- ✅ Story开发时
- ✅ Code Review时
- ✅ 架构设计时
- ✅ 回答技术问题时

### 强制规则

#### 规则1: 提到技术栈，立即验证文档

**触发词**: 任何技术栈名称、API名称、库名称、框架名称

**示例**:
```python
# ❌ 错误示例（无文档验证）
from langgraph.prebuilt import create_react_agent

agent = create_react_agent(model, tools)

# ✅ 正确示例（已验证文档）
# ✅ Verified from LangGraph Skill (SKILL.md - Pattern: Agent with Tools)
from langgraph.prebuilt import create_react_agent

agent = create_react_agent(
    model=llm,
    tools=[search_tool, calculator_tool],
    state_modifier="You are a helpful AI assistant."
)
```

#### 规则2: 每个API调用必须标注文档来源

**强制标注格式**:
```python
# ✅ Verified from [来源] ([具体位置])
[代码行]
```

**来源优先级**:
1. **Skills** (优先级最高) - 离线本地文档，速度快，准确性高
2. **Context7** (优先级次之) - 在线文档，覆盖广
3. **Official Docs** (最后手段) - WebFetch工具，速度慢

**示例**:
```python
# ✅ Verified from Neo4j Cypher Skill (SKILL.md #Cypher-Query-Syntax)
result = session.run(
    "MATCH (n:Concept {name: $name}) RETURN n",
    name=concept_name
)

# ✅ Verified from Context7: /websites/fastapi_tiangolo (topic: "Dependency Injection")
from fastapi import Depends

@app.get("/items/")
async def read_items(token: str = Depends(oauth2_scheme)):
    return {"token": token}
```

#### 规则3: 未验证的API不允许进入代码

**处理流程**:
1. 如果Skills中找不到 → 查询Context7
2. 如果Context7也找不到 → 查询官方文档
3. 如果都找不到 → **明确告知用户，不能臆测**

#### 规则4: Skills激活方式

在开发前激活相关Skills：
```bash
# 对话中激活Skills
"@langgraph 如何创建StateGraph？"
"@graphiti 如何存储概念关系？"
"@obsidian-canvas Canvas JSON格式是什么？"
```

---

## 📚 Helper System引用规范 (BMad Integration)

### 什么是Helper System？

Helper System是BMad方法的核心优化，通过引用模式节省70-85%的token。

**原理**:
- 不在文档中嵌入完整内容
- 使用`@helpers.md#Section-Name`引用
- Claude Code自动加载对应section

### 引用语法

```markdown
参见: @helpers.md#Story-Development-Workflow
参见: @helpers.md#Testing-Checklist
参见: @helpers.md#Agent-Calling-Protocol
参见: @helpers.md#Canvas-Color-System
参见: @helpers.md#BMad-4-Phase-Workflow
```

### 可用Helper Sections

| Section名称 | 内容 | 使用场景 |
|------------|------|---------|
| `Story-Development-Workflow` | Story开发完整流程 | SM生成Story时参考 |
| `Testing-Checklist` | 测试检查清单 | QA测试时使用 |
| `Agent-Calling-Protocol` | Agent调用协议 | 实现Agent调用时参考 |
| `Canvas-Color-System` | Canvas颜色系统规范 | 操作Canvas时查阅 |
| `BMad-4-Phase-Workflow` | BMad四阶段工作流 | 项目开发整体流程 |

### 示例

```markdown
# ❌ 不好的做法（嵌入完整内容，消耗大量token）
## Story开发流程

1. SM读取Epic
2. SM调用Analysis Agent
3. SM生成Story文件
4. Dev读取Story
5. Dev实现功能
6. QA测试验证
...（完整流程50行）

# ✅ 好的做法（引用Helper，节省token）
## Story开发流程

参见: @helpers.md#Story-Development-Workflow
```

---

## 📐 Document Sharding规范 (BMad Integration)

### 何时需要Sharding？

| Token数 | 触发级别 | 行动 |
|--------|---------|------|
| < 20,000 | ✅ 安全 | 无需Sharding |
| 20,000 - 40,000 | ⚠️ 考虑 | 建议Sharding |
| 40,000 - 60,000 | 🟠 推荐 | 强烈推荐Sharding |
| > 60,000 | 🔴 必须 | 必须立即Sharding |

### Sharding方法

**按## 标题拆分**:
```markdown
# 原文档: docs/architecture/system-architecture.md (80KB)

# 拆分后:
docs/architecture/
├── system-architecture-overview.md      # 概览 (10KB)
├── system-architecture-layer1.md        # Layer 1详细 (15KB)
├── system-architecture-layer2.md        # Layer 2详细 (18KB)
├── system-architecture-layer3.md        # Layer 3详细 (20KB)
└── system-architecture-performance.md   # 性能指标 (12KB)
```

**Index文件模式**:
```markdown
# system-architecture.md (索引文件)

参见详细文档:
- @system-architecture-layer1.md - Layer 1: CanvasJSONOperator
- @system-architecture-layer2.md - Layer 2: CanvasBusinessLogic
- @system-architecture-layer3.md - Layer 3: CanvasOrchestrator
```

---

## 🎯 提交前检查清单

在提交代码前，确认：

**代码质量**:
- [ ] 代码已通过black格式化
- [ ] 代码已通过pylint检查（评分≥8.0）
- [ ] 代码已通过mypy类型检查
- [ ] 所有测试通过
- [ ] 测试覆盖率达标（≥85%）

**文档完整性**:
- [ ] 所有公共函数有Docstring
- [ ] README已更新（如果添加新功能）
- [ ] 架构文档已更新（如果改变架构）

**BMad规范** (新增):
- [ ] 所有技术API调用已标注文档来源
- [ ] 已激活相关Skills并验证API参数
- [ ] 使用Helper引用替代嵌入完整内容
- [ ] 文档token数未超过20,000（超过则Sharding）
- [ ] 提交的Story文件包含[Source: ...]引用

**提交规范**:
- [ ] Commit message清晰（使用conventional commits格式）
- [ ] 没有提交调试代码或临时文件
- [ ] .gitignore已配置正确

**Commit Message格式**:
```
<type>(<scope>): <subject>

<body>

<footer>
```

示例:
```
feat(canvas-utils): 添加v1.1布局算法

实现黄色节点在问题节点正下方的布局逻辑。
- 添加YELLOW_OFFSET_X和YELLOW_OFFSET_Y常量
- 更新add_sub_question_with_yellow_node方法
- 添加单元测试覆盖新逻辑

[Source: @langgraph Skill (Canvas Layout Algorithms)]
[Source: docs/architecture/canvas-layout-v1.1.md]
```

---

**文档版本**: v2.0 (BMad Integration)
**最后更新**: 2025-11-17
**维护者**: Architect Agent + BMad Framework
