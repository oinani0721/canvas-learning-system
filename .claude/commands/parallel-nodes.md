---
name: parallel-nodes
description: Process specific node IDs in parallel using specified agent
parameters:
  - name: agent_type
    type: string
    description: Type of agent to run
    required: true
  - name: nodes
    type: string
    description: Comma-separated list of node IDs (required)
    required: true
  - name: max
    type: number
    description: Maximum concurrent instances (default: 6)
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

# *parallel-nodes - 指定节点并行处理

## 概述

使用指定Agent并行处理特定的节点ID列表，精确控制处理范围。

## 语法

```
*parallel-nodes <agent_type> --nodes=node1,node2,node3 [options]
```

## 参数说明

### 必需参数
- **agent_type**: Agent类型（同*parallel-agents）
- **--nodes**: 节点ID列表（逗号分隔，必需）

### 可选参数
- **--max**: 最大并发实例数（默认：6）
- **--canvas**: Canvas文件路径
- **--dry-run**: 试运行模式
- **--priority**: 任务优先级

## 使用示例

### 基础用法
```bash
# 处理特定节点
*parallel-nodes clarification-path --nodes=node-abc,node-def,node-ghi

# 使用scoring-agent评分
*parallel-nodes scoring-agent --nodes=yellow1,yellow2,yellow3
```

### 高级选项
```bash
# 限制并发数
*parallel-nodes memory-anchor --nodes=node1,node2,node3,node4 --max=2

# 高优先级处理
*parallel-nodes oral-explanation --nodes=node-123 --priority=urgent

# 试运行预览
*parallel-nodes comparison-table --nodes=node-1,node-2 --dry-run
```

### 批量处理技巧
```bash
# 处理连续编号的节点
*parallel-nodes clarification-path --nodes=node1,node2,node3,node4,node5

# 处理特定章节的所有节点
*parallel-nodes memory-anchor --nodes=ch1-q1,ch1-q2,ch1-q3
```

## 输出示例

```
🎯 目标节点: 3个
📋 节点列表: node-abc, node-def, node-ghi
🔧 Agent类型: clarification-path
⚡ 并发实例: 3个

✅ node-abc: 完成 (2.3s)
✅ node-def: 完成 (2.7s)
✅ node-ghi: 完成 (3.1s)

📊 处理完成: 3成功, 0失败
```

## 注意事项

1. **节点ID**: 节点ID必须存在于Canvas文件中
2. **逗号分隔**: 多个节点ID使用英文逗号分隔，无空格
3. **存在性检查**: 执行前会验证所有节点是否存在

## 相关命令

- `*parallel-agents`: 按数量或自动选择处理节点
- `*parallel-color`: 按颜色筛选处理节点
- `*canvas-status`: 查看Canvas中所有节点ID