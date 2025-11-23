---
name: parallel-help
description: Complete guide for parallel command system
parameters:
  - name: topic
    type: string
    description: Help topic (overview/agents/examples/best-practices)
    required: false
---

# 并行命令系统 - 完整指南

## 📖 目录

1. [系统概述](#系统概述)
2. [快速开始](#快速开始)
3. [命令详解](#命令详解)
4. [使用示例](#使用示例)
5. [最佳实践](#最佳实践)
6. [常见问题](#常见问题)

## 系统概述

并行命令系统允许你同时运行多个Agent实例，大幅提升Canvas处理效率。

### 核心优势
- ⚡ **效率提升**: 6倍并行处理能力
- 🎯 **灵活控制**: 支持节点、颜色、混合多种模式
- 📊 **实时监控**: 进度跟踪和状态反馈
- 🛡️ **智能管理**: 自动负载均衡和错误恢复

### 四种并行命令

| 命令 | 用途 | 适用场景 |
|------|------|---------|
| `*parallel-agents` | 同类型Agent批量处理 | 大量相似任务 |
| `*parallel-nodes` | 指定节点精确处理 | 特定问题解决 |
| `*parallel-color` | 按颜色筛选处理 | 批量处理同类节点 |
| `*parallel-mixed` | 多种Agent混合处理 | 综合学习场景 |

## 快速开始

### 1. 处理红色节点（不理解的内容）
```bash
*parallel-color basic-decomposition --color=1 --limit=5
```

### 2. 评分所有理解输出
```bash
*parallel-nodes scoring-agent --nodes=yellow1,yellow2,yellow3
```

### 3. 综合学习处理
```bash
*parallel-mixed basic-decomposition:2,clarification-path:3 --max=5
```

## 命令详解

### *parallel-agents
```bash
*parallel-agents <agent_type> [count] [options]
```
最基础的并行命令，使用同类型Agent处理多个节点。

### *parallel-nodes
```bash
*parallel-nodes <agent_type> --nodes=node1,node2,node3 [options]
```
精确控制要处理的节点ID。

### *parallel-color
```bash
*parallel-color <agent_type> --color=<1|2|3|6> [options]
```
按颜色批量筛选处理。

### *parallel-mixed
```bash
*parallel-mixed agent1:count1,agent2:count2 [options]
``
多种Agent协同工作。

## 使用示例

### 学习新概念
```bash
# Step 1: 拆解难点
*parallel-color basic-decomposition --color=1

# Step 2: 深入理解
*parallel-color clarification-path --color=3

# Step 3: 强化记忆
*parallel-color memory-anchor --color=1 --limit=3
```

### 复习巩固
```bash
# 评分当前理解
*parallel-color scoring-agent --color=6

# 生成对比分析
*parallel-nodes comparison-table --nodes=node1,node2,node3

# 创建例题练习
*parallel-mixed example-teaching:2,verification-question-agent:2
```

### 高效工作流
```bash
# 试运行预览
*parallel-agents clarification-path 5 --dry-run

# 确认后执行
*parallel-agents clarification-path 5

# 监控进度
# 系统会自动显示实时进度条
```

## 最佳实践

### 1. 合理规划并发数
- **小任务**: 3-4个实例
- **中型任务**: 5-6个实例
- **大型任务**: 分批处理

```bash
# 好的做法：分批
*parallel-color basic-decomposition --color=1 --limit=10
*parallel-color basic-decomposition --color=1 --limit=10

# 避免：一次性过多
*parallel-color basic-decomposition --color=1 --limit=50
```

### 2. 优化Agent选择
| 学习阶段 | 推荐Agent | 命令示例 |
|---------|-----------|----------|
| 初学 | basic-decomposition | `*parallel-color basic-decomposition --color=1` |
| 理解 | clarification-path | `*parallel-color clarification-path --color=3` |
| 记忆 | memory-anchor | `*parallel-color memory-anchor --color=1` |
| 应用 | example-teaching | `*parallel-mixed example-teaching:3` |
| 评估 | scoring-agent | `*parallel-color scoring-agent --color=6` |

### 3. 使用优先级
```bash
# 重要任务
*parallel-agents clarification-path --priority=high

# 常规任务
*parallel-agents oral-explanation --priority=normal

# 低优先级
*parallel-agents comparison-table --priority=low
```

### 4. 试运行验证
```bash
# 总是先试运行
*parallel-mixed memory-anchor:3,clarification-path:4 --dry-run

# 查看预览输出确认计划
# 然后再执行实际命令
```

### 5. 监控和日志
- 关注实时进度输出
- 记录执行时间和结果
- 根据错误信息调整策略

## 常见问题

### Q: 如何查看所有可用的Agent类型？
A: 使用 `*canvas-help agents` 查看完整列表。

### Q: 如何获取节点ID？
A: 使用 `*canvas-status` 查看Canvas中所有节点的ID和状态。

### Q: 并发处理会不会消耗更多API额度？
A: 是的，多个实例并行会更快消耗额度。建议合理规划并使用--limit限制。

### Q: 如果某个节点处理失败怎么办？
A: 单个节点失败不会影响其他节点。检查错误信息，可单独重试失败节点。

### Q: 如何停止正在执行的并行命令？
A: 使用Ctrl+C中断，系统会优雅停止并显示已完成进度。

### Q: 可以同时运行多个并行命令吗？
A: 不建议。等待当前命令完成后再执行下一个，以避免资源竞争。

### Q: dry-run模式会消耗API额度吗？
A: 不会。dry-run只预览执行计划，不实际调用Agent。

### Q: 如何处理大量节点？
A: 建议分批处理，每批10-20个节点，避免系统负载过高。

```bash
# 示例：分批处理
*parallel-color basic-decomposition --color=1 --limit=20
# 等待完成
*parallel-color basic-decomposition --color=1 --limit=20
```

## 进阶技巧

### 1. 自定义工作流
创建命令别名或脚本，组合多个并行命令：
```bash
# 学习新概念工作流
alias learn-concept='*parallel-color basic-decomposition --color=1 --limit=5 && *parallel-color clarification-path --color=3'
```

### 2. 智能节点选择
结合节点颜色和ID进行精确处理：
```bash
# 处理特定章节的所有红色节点
*parallel-nodes basic-decomposition --nodes=ch1-1,ch1-2,ch1-3
```

### 3. 性能优化
- 根据系统性能调整并发数
- 网络慢时降低并发
- API额度紧张时使用--limit

---

## 相关命令

- `*canvas-help`: Canvas系统完整帮助
- `*canvas-status`: 查看Canvas状态
- `*health-check`: 系统健康检查
- 各Agent专用命令（如`/口语化解释`）