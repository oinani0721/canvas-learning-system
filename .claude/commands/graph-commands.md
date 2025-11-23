---
name: graph-commands
description: Graphiti知识图谱命令系统，支持Canvas学习会话记录和知识图谱分析
tools: Read, Write, Edit, Bash
model: sonnet
---

# Graphiti知识图谱命令系统

## System Availability Check (Story 10.11.4)

**IMPORTANT**: Before executing any graph commands, check if Graphiti is available:

```python
from command_handlers.learning_commands import get_mode_info
from memory_system.error_formatters import require_graphiti

mode_info = get_mode_info()
if mode_info and not require_graphiti(mode_info):
    # Graphiti unavailable, degradation message shown, exit
    return

if not mode_info:
    print("Please run /learning start first to initialize the system")
    return
```

## 概述

这个命令系统集成了Graphiti时序知识图谱功能，允许用户：
- 录制Canvas学习会话到知识图谱
- 搜索和分析概念网络
- 获取学习建议和薄弱环节分析
- 查看知识图谱统计信息

## 主要命令

### `/graph start <canvas_path>`
开始录制Canvas学习会话。

**参数:**
- `canvas_path`: Canvas文件路径（必需）

**选项:**
- `--user-id`: 用户ID（默认: default）

**示例:**
```
/graph start "笔记库/离散数学/离散数学.canvas"
/graph start "笔记库/线性代数/线性代数.canvas" --user-id user123
```

### `/graph stop`
停止当前录制的学习会话。

**示例:**
```
/graph stop
```

### `/graph search <query>`
搜索知识图谱中的概念网络。

**参数:**
- `query`: 搜索查询（必需）

**选项:**
- `--depth`: 搜索深度（默认: 2）
- `--user-id`: 用户ID（默认: default）

**示例:**
```
/graph search "逆否命题"
/graph search "矩阵运算" --depth 3
```

### `/graph analyze <canvas_path>`
分析Canvas文件中的概念和关系。

**参数:**
- `canvas_path`: Canvas文件路径（必需）

**选项:**
- `--user-id`: 用户ID（默认: default）

**示例:**
```
/graph analyze "笔记库/离散数学/离散数学.canvas"
```

### `/graph stats`
显示知识图谱统计信息。

**选项:**
- `--user-id`: 用户ID（默认: default）

**示例:**
```
/graph stats
/graph stats --user-id user123
```

### `/graph recommendations`
生成个性化学习建议。

**选项:**
- `--user-id`: 用户ID（默认: default）

**示例:**
```
/graph recommendations
```

### `/graph weaknesses`
识别学习薄弱环节。

**选项:**
- `--user-id`: 用户ID（默认: default）

**示例:**
```
/graph weaknesses
```

### `/graph status`
显示当前录制状态。

**示例:**
```
/graph status
```

## 使用工作流

### 典型的学习会话工作流:

1. **开始学习会话**
   ```
   /graph start "笔记库/数学分析/数学分析.canvas"
   ```

2. **进行Canvas学习活动**
   - 使用各种Sub-agent进行学习
   - 填写黄色理解节点
   - 进行评分和反馈

3. **分析当前学习内容**
   ```
   /graph analyze "笔记库/数学分析/数学分析.canvas"
   ```

4. **搜索相关概念**
   ```
   /graph search "导数概念"
   ```

5. **获取学习建议**
   ```
   /graph recommendations
   ```

6. **检查薄弱环节**
   ```
   /graph weaknesses
   ```

7. **结束学习会话**
   ```
   /graph stop
   ```

## 技术实现

### 核心组件

- **GraphitiKnowledgeGraph**: 主要的知识图谱管理类
- **ConceptExtractor**: 概念和关系自动提取器
- **GraphCommandHandler**: 命令处理器
- **GraphitiContextManager**: 异步上下文管理器

### 数据存储

- **Neo4j数据库**: 存储知识图谱数据
- **时序信息**: 记录学习历史和会话信息
- **关系数据**: 概念间的语义关系

### 集成方式

- 与现有Canvas系统完全兼容
- 支持异步操作，不影响正常学习流程
- 自动提取概念关系，无需手动标注

## 配置

### 配置文件位置: `config/graphiti_config.yaml`

```yaml
neo4j:
  uri: "bolt://localhost:7687"
  username: "neo4j"
  password: "password"
  database: "canvas_learning"

graphiti:
  temporal_resolution: "second"
  session_timeout: 3600
  max_session_duration: 7200
  relationship_extraction:
    min_confidence: 0.7
    max_relationships_per_concept: 50
    relationship_types:
      - "is_prerequisite_for"
      - "is_similar_to"
      - "is_contradictory_of"
      - "is_derived_from"
      - "is_applied_in"
  graph_construction:
    auto_merge_similar_concepts: true
    concept_similarity_threshold: 0.8
    relationship_strength_decay: 0.1
```

## 故障排除

### 常见问题

1. **Neo4j连接失败**
   - 确保Neo4j Docker容器正在运行
   - 检查连接配置是否正确
   - 运行 `python scripts/setup_neo4j_docker.py --start`

2. **概念提取失败**
   - 检查Canvas文件格式是否正确
   - 确保Canvas文件包含文本内容
   - 检查文件编码是否为UTF-8

3. **搜索结果为空**
   - 确保知识图谱中有数据
   - 尝试使用不同的搜索关键词
   - 检查用户ID是否正确

### 调试模式

启用详细日志:
```bash
export LOG_LEVEL=DEBUG
/graph commands status
```

## 扩展性

### 添加新命令

1. 在 `GraphCommandHandler` 中添加新方法
2. 在 `cli` 函数中添加Click命令
3. 更新本命令文档

### 自定义关系类型

在配置文件中添加新的关系类型:
```yaml
relationship_types:
  - "is_prerequisite_for"
  - "is_similar_to"
  - "is_contradictory_of"
  - "is_derived_from"
  - "is_applied_in"
  - "your_custom_type"  # 新增类型
```

### 集成外部AI服务

Graphiti支持多种LLM和嵌入服务:
- Anthropic Claude
- OpenAI GPT
- Voyage AI
- 本地模型

## 版本信息

- **版本**: 1.0
- **最后更新**: 2025-01-22
- **兼容性**: Canvas Learning System v2.0+
- **依赖**: Graphiti Core, Neo4j, Python 3.9+