---
name: parallel-color
description: Process all nodes of a specific color in parallel
parameters:
  - name: agent_type
    type: string
    description: Type of agent to run
    required: true
  - name: color
    type: string
    description: Node color code (1=red, 2=green, 3=purple, 6=yellow)
    required: true
  - name: limit
    type: number
    description: Limit number of nodes to process
    required: false
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

# *parallel-color - 按颜色并行处理

## 概述

使用指定Agent并行处理特定颜色的所有节点，适合批量处理同类问题。

## 语法

```
*parallel-color <agent_type> --color=<color_code> [options]
```

## 颜色代码

| 颜色代码 | 颜色 | 含义 | 使用场景 |
|---------|------|------|---------|
| **1** | 🔴 红色 | 不理解/未通过 | 需要拆解的难题 |
| **2** | 🟢 绿色 | 完全理解/已通过 | 已掌握的知识点 |
| **3** | 🟣 紫色 | 似懂非懂/待检验 | 需要深度理解 |
| **6** | 🟡 黄色 | 个人理解输出区 | 费曼学习法输出 |

## 参数说明

### 必需参数
- **agent_type**: Agent类型
- **--color**: 颜色代码（1/2/3/6）

### 可选参数
- **--limit**: 限制处理的节点数量
- **--max**: 最大并发实例数
- **--canvas**: Canvas文件路径
- **--dry-run**: 试运行模式
- **--priority**: 任务优先级

## 使用示例

### 处理未理解的节点
```bash
# 使用basic-decomposition处理所有红色节点
*parallel-color basic-decomposition --color=1

# 限制处理数量
*parallel-color memory-anchor --color=1 --limit=5
```

### 深化理解
```bash
# 使用clarification-path处理所有紫色节点
*parallel-color clarification-path --color=3

# 使用deep-decomposition深化理解
*parallel-color deep-decomposition --color=3 --max=4
```

### 评分和验证
```bash
# 评分所有黄色理解输出
*parallel-color scoring-agent --color=6

# 生成检验问题
*parallel-color verification-question-agent --color=1
```

### 批量生成解释
```bash
# 为所有红色节点生成口语化解释
*parallel-color oral-explanation --color=1

# 生成对比表
*parallel-color comparison-table --color=3
```

## 高级用法

### 组合处理工作流
```bash
# Step 1: 拆解红色节点
*parallel-color basic-decomposition --color=1

# Step 2: 深化紫色理解
*parallel-color clarification-path --color=3

# Step 3: 评分黄色输出
*parallel-color scoring-agent --color=6
```

### 试运行预览
```bash
# 预览将要处理的节点
*parallel-color memory-anchor --color=1 --dry-run
```

## 输出示例

```
🎨 筛选颜色: 1 (红色)
📊 匹配节点: 8个
🔧 Agent类型: basic-decomposition
🚀 并发处理: 6个

⏳ [████████░░░░░] 60% (5/8 完成)
✅ node-problem1: 完成
✅ node-problem2: 完成
✅ node-problem3: 完成
✅ node-problem4: 完成
✅ node-problem5: 完成
⏳ node-problem6: 处理中...
⏳ node-problem7: 等待中...
⏳ node-problem8: 等待中...

🎉 处理完成！
📈 成功: 8个, 失败: 0个
⏱️ 耗时: 15.2秒
```

## 最佳实践

1. **分批处理**: 对于大量节点，使用--limit分批
2. **颜色流转**: 按红→紫→绿的顺序逐步提升理解
3. **优先处理**: 优先处理红色节点（不理解的内容）
4. **定期评分**: 定期使用scoring-agent评分黄色节点

## 注意事项

1. **颜色准确性**: 确保Canvas中节点颜色设置正确
2. **节点类型**: 某些Agent可能不适用于特定颜色节点
3. **资源管理**: 大量节点处理时注意API额度消耗

## 相关命令

- `*parallel-agents`: 不限颜色的并行处理
- `*parallel-nodes`: 指定节点ID处理
- `*canvas-status`: 查看各颜色节点统计
