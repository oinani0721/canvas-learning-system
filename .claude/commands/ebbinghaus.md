---
name: ebbinghaus
description: Enable Ebbinghaus forgetting curve-based intelligent review system
---

# Ebbinghaus Forgetting Curve Review System

## Metadata
- **Command**: /ebbinghaus
- **Description**: Enable Ebbinghaus forgetting curve-based intelligent review system
- **Bmad Pattern**: Spaced repetition with adaptive scheduling
- **Keywords**: *review, *ebbinghaus, *memory

## Usage

### Review Operations
```bash
/ebbinghaus               # Start review session
/ebbinghaus *daily        # Enable daily review mode
/ebbinghaus schedule      # View review schedule
/ebbinghaus today         # Show today's review items
```

### Configuration
```bash
/ebbinghaus config        # Configure review parameters
/ebbinghaus reset         # Reset review schedule
/ebbinghaus export        # Export review data
/ebbinghaus stats         # Show review statistics
```

## Implementation

基于Py-FSRS算法的艾宾浩斯遗忘曲线复习系统，智能安排最佳复习时机。

**复习算法**: Py-FSRS (Trust Score: 9.4/10)
- 初始复习间隔: 1天, 3天, 7天, 15天, 30天
- 动态调整: 基于遗忘曲线和个人表现
- 智能提醒: 在最佳时机推送复习任务

**激活时机**:
1. **手动激活**: `/ebbinghaus` 或 `*review`
2. **自动激活**: 学习后24小时首次提醒
3. **智能激活**: 检测到知识遗忘风险时

**复习内容**:
- 红色节点: 基础概念复习
- 紫色节点: 深度理解检验
- 历史错误: 重点复习区域
- Agent建议: 个性化复习策略

**数据追踪**:
- 复习准确率: ≥85%
- 遗忘曲线拟合: R² ≥ 0.9
- 知识保持率: 提升40%

与Canvas学习系统无缝集成，实现长期记忆强化。
