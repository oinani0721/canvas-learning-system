---
name: parallel-mixed
description: Execute multiple agent types in parallel with custom distribution
parameters:
  - name: config
    type: string
    description: Agent distribution (e.g., memory-anchor:3,clarification-path:4)
    required: true
  - name: max
    type: number
    description: Maximum total concurrent instances (default: 6)
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

# *parallel-mixed - 混合Agent并行处理

## 概述

同时使用多种类型的Agent并行处理不同节点，实现最优的任务分配和处理效率。

## 语法

```
*parallel-mixed agent1:count1,agent2:count2,agent3:count3 [options]
```

## 参数说明

### 必需参数
- **config**: Agent分布配置
  - 格式：`agent_type:count`
  - 多个配置用逗号分隔
  - 例如：`memory-anchor:3,clarification-path:4`

### 可选参数
- **--max**: 总并发实例数限制（默认：6）
- **--canvas**: Canvas文件路径
- **--dry-run**: 试运行模式
- **--priority**: 任务优先级

## 使用示例

### 基础混合处理
```bash
# 3个memory-anchor和4个clarification-path
*parallel-mixed memory-anchor:3,clarification-path:4

# 2个oral-explanation和3个example-teaching
*parallel-mixed oral-explanation:2,example-teaching:3
```

### 复杂混合策略
```bash
# 综合处理策略
*parallel-mixed basic-decomposition:2,clarification-path:3,memory-anchor:2

# 评分+解释组合
*parallel-mixed scoring-agent:3,oral-explanation:2
```

### 高级选项
```bash
# 限制总并发数
*parallel-mixed memory-anchor:3,clarification-path:4 --max=5

# 高优先级处理
*parallel-mixed oral-explanation:2,comparison-table:2 --priority=high

# 试运行预览
*parallel-mixed memory-anchor:5,scoring-agent:3 --dry-run
```

## 典型使用场景

### 场景1: 新知识学习
```bash
# 拆解 + 深化理解 + 记忆锚点
*parallel-mixed basic-decomposition:2,clarification-path:3,memory-anchor:2
```

### 场景2: 复习巩固
```bash
# 评分 + 生成解释 + 对比分析
*parallel-mixed scoring-agent:3,oral-explanation:2,comparison-table:1
```

### 场景3: 考前冲刺
```bash
# 全面处理
*parallel-mixed deep-decomposition:2,example-teaching:3,verification-question-agent:2
```

## Agent组合建议

### 初学阶段
- `basic-decomposition:3,oral-explanation:2`
  侧重基础拆解和口语化解释

### 进阶阶段
- `clarification-path:3,memory-anchor:2`
  侧重深度理解和记忆强化

### 复习阶段
- `scoring-agent:3,comparison-table:2`
  侧重评估和知识对比

### 综合应用
- `example-teaching:3,verification-question-agent:2`
  侧重实践应用和检验

## 输出示例

```
🎭 混合Agent配置
├── memory-anchor: 3个实例
├── clarification-path: 4个实例
└── 总计: 7个实例

📊 执行计划
🔧 memory-anchor: 处理3个节点
🔧 clarification-path: 处理4个节点
⚡ 并发限制: 6个

⏳ [████████████░░] 85%
✅ memory-anchor: 3/3 完成
✅ clarification-path: 3/4 完成
⏳ clarification-path: 1个处理中...

🎉 混合处理完成！
📈 memory-anchor: 3成功, 0失败
📈 clarification-path: 4成功, 0失败
⏱️ 总耗时: 22.5秒
```

## 高级技巧

### 1. 智能配比
根据学习阶段调整Agent比例：
- **初学**: 更多basic-decomposition
- **进阶**: 更多clarification-path
- **复习**: 更多scoring-agent

### 2. 资源优化
```bash
# 根据API额度调整
*parallel-mixed oral-explanation:2,memory-anchor:2 --max=4
```

### 3. 优先级管理
```bash
# 重要内容使用高优先级
*parallel-mixed clarification-path:3,memory-anchor:2 --priority=urgent
```

## 注意事项

1. **总数限制**: 所有Agent数量之和受--max参数限制
2. **资源消耗**: 多种Agent并行会更快消耗API额度
3. **任务分配**: 系统自动分配节点给不同的Agent

## 故障排除

**问题**: "无效的混合配置格式"
- 解决: 使用`agent:count`格式，多个用逗号分隔

**问题**: "不支持的Agent类型"
- 解决: 检查Agent名称拼写，参考支持列表

## 相关命令

- `*parallel-agents`: 单一Agent类型并行
- `*parallel-nodes`: 指定节点处理
- `*parallel-color`: 按颜色筛选处理
- `*canvas-help agents`: 查看所有可用Agent