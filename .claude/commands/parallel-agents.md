---
name: parallel-agents
description: Execute multiple instances of the same agent type in parallel
parameters:
  - name: agent_type
    type: string
    description: Type of agent to run (e.g., clarification-path, memory-anchor)
    required: true
  - name: count
    type: number
    description: Number of nodes to process (optional)
    required: false
  - name: max
    type: number
    description: Maximum concurrent instances (default: 6)
    required: false
  - name: nodes
    type: string
    description: Comma-separated list of node IDs to process
    required: false
  - name: canvas
    type: string
    description: Canvas file path
    required: false
  - name: dry-run
    type: boolean
    description: Preview execution without actually running
    required: false
  - name: priority
    type: string
    description: Task priority (low/normal/high/urgent)
    required: false
---

# *parallel-agents - 并行Agent执行器

## 概述

使用指定类型的Agent并行处理多个Canvas节点，大幅提升处理效率。

## 语法

```
*parallel-agents <agent_type> [count] [options]
```

## 参数说明

### 必需参数
- **agent_type**: Agent类型
  - 支持的类型：`basic-decomposition`, `deep-decomposition`, `oral-explanation`,
    `clarification-path`, `comparison-table`, `memory-anchor`,
    `four-level-explanation`, `example-teaching`, `scoring-agent`,
    `verification-question-agent`

### 可选参数
- **count**: 要处理的节点数量（默认：所有问题节点）
- **--nodes**: 指定特定节点ID列表（逗号分隔）
- **--max**: 最大并发实例数（默认：6）
- **--canvas**: Canvas文件路径（默认：当前目录下的第一个.canvas文件）
- **--dry-run**: 试运行模式，只显示执行计划
- **--priority**: 任务优先级（low/normal/high/urgent，默认：normal）

## 使用示例

### 基础用法
```bash
# 使用clarification-path处理4个节点
*parallel-agents clarification-path 4

# 使用memory-anchor处理所有问题节点
*parallel-agents memory-anchor
```

### 指定节点
```bash
# 处理特定节点
*parallel-agents clarification-path --nodes=node1,node2,node3

# 处理特定节点并限制并发数
*parallel-agents oral-explanation --nodes=node-abc,node-def --max=3
```

### 试运行
```bash
# 预览执行计划
*parallel-agents memory-anchor 5 --dry-run
```

### 高级选项
```bash
# 高优先级处理
*parallel-agents clarification-path --priority=high

# 指定Canvas文件
*parallel-agents memory-anchor --canvas=离散数学.canvas
```

## 输出格式

命令执行时会显示：
- 执行计划摘要
- 实时进度（进度条和百分比）
- 每个节点的处理状态
- 最终统计信息

### 示例输出
```
🚀 启动并行处理: clarification-path
📊 目标节点: 4个
🔧 并发实例: 3个

⏳ [████████████░░░░] 75% (3/4 完成)
✅ node-abc: 完成
✅ node-def: 完成
✅ node-ghi: 完成
⏳ node-jkl: 处理中...

✅ 执行完成
📈 处理统计: 4成功, 0失败
⏱️ 总耗时: 12.3秒
```

## 注意事项

1. **并发限制**: 系统默认最大6个并发实例，可通过--max调整
2. **资源消耗**: 每个实例会消耗一定的API额度，请合理规划
3. **节点筛选**: 默认只处理问题节点（红色或紫色）
4. **错误处理**: 单个节点失败不会影响其他节点的处理

## 相关命令

- `*parallel-nodes`: 处理指定节点列表
- `*parallel-color`: 按颜色筛选处理节点
- `*parallel-mixed`: 混合使用多种Agent

## 故障排除

**问题**: "无法识别的Agent类型"
- 解决: 检查Agent类型拼写，使用`*canvas-help agents`查看支持的类型

**问题**: "没有找到需要处理的节点"
- 解决: 确保Canvas中有问题节点（红色或紫色），或使用--nodes指定节点

**问题**: "并发实例超限"
- 解决: 降低--max参数值，或等待当前任务完成

## 最佳实践

1. **批量处理**: 对于大量节点，分批次处理而非一次性全部
2. **优先级设置**: 重要任务使用--priority=high
3. **试运行**: 执行前先使用--dry-run确认计划
4. **监控进度**: 关注实时进度输出，及时发现问题