---
name: review-progress
description: 复习进度跟踪命令，显示用户复习计划完成情况和学习效果统计
tools: Bash, Read
model: sonnet
---

# /review-progress Command

复习进度跟踪命令，用于查看智能复习计划的完成情况、学习效果统计和改进趋势分析。

## Usage

```bash
/review-progress [plan_id] [options...]
```

## Parameters

### Positional Parameters
- `plan_id`: 复习计划ID（可选，默认显示最近的活动计划）

### Optional Parameters
- `--user-id`: 用户ID（默认：default）
- `--format`: 输出格式
  - `summary`: 简要摘要（默认）
  - `detailed`: 详细报告
  - `json`: JSON格式
  - `chart`: 图表可视化
- `--time-range`: 时间范围
  - `today`: 今天
  - `week`: 本周（默认）
  - `month`: 本月
  - `all`: 全部
- `--concepts`: 显示特定概念的进度
- `--compare`: 与历史数据比较
- `--export`: 导出报告到文件

## Examples

### 查看最近计划进度
```bash
/review-progress
```

### 查看特定计划详情
```bash
/review-progress plan-abc123def456 --format detailed
```

### 查看本周进度统计
```bash
/review-progress --time-range week --format summary
```

### 查看特定概念进度
```bash
/review-progress --concepts "逻辑等价性,集合运算"
```

### 导出进度报告
```bash
/review-progress --export progress_report_20250123.md
```

## Progress Metrics

### 完成度指标
- ✅ **整体完成率**: 已完成概念数 / 总概念数
- 📊 **平均理解分数**: 所有已完成概念的平均评分
- ⏱️ **时间效率**: 实际用时 / 预估用时
- 🎯 **目标达成率**: 达成目标数 / 总目标数

### 学习效果指标
- 📈 **掌握度提升**: 复习前后掌握分数对比
- 💪 **薄弱环节改善**: 识别薄弱概念的数量变化
- 🔄 **复习频率**: 符合推荐复习间隔的比例
- 🧠 **记忆保持率**: 基于艾宾浩斯算法的保持率估算

### 趋势分析指标
- 📊 **学习曲线**: 近期表现趋势
- 🎯 **难度适应性**: 难度调整的效果
- ⏰ **时间优化**: 学习时长的优化程度
- 🏆 **动机水平**: 学习积极性和参与度

## Output Formats

### Summary Format
```
📊 复习进度报告 - 2025年01月23日

🎯 当前计划: plan-abc123def456 (离散数学智能复习)
✅ 完成进度: 3/5 概念 (60%)
📈 平均分数: 7.8/10
⏱️ 时间效率: 85%

📈 趋势分析:
• 掌握度提升: +2.3分
• 薄弱环节减少: 2个
• 复习质量: 良好

💡 下步建议:
• 重点复习剩余2个概念
• 巩固已掌握内容
• 准备下次复习计划
```

### Detailed Format
包含完整的统计数据、图表和个性化建议。

### JSON Format
结构化数据，便于程序处理和集成。

## Progress Tracking Features

### 自动进度检测
- 🔍 扫描复习Canvas文件中的完成标记
- 📝 提取黄色节点中的评分信息
- ⏰ 计算实际用时和效率
- 🎯 评估目标达成情况

### 学习效果分析
- 📊 对比复习前后的掌握程度
- 💪 识别薄弱环节的改善情况
- 🧠 基于遗忘曲线分析记忆保持效果
- 🔄 评估复习频率的合理性

### 趋势预测
- 📈 分析学习曲线趋势
- 🎯 预测下次复习的最佳时机
- 💡 提供个性化改进建议
- 🏆 设定阶段性学习目标

## Integration with Other Systems

该命令与以下系统组件集成：
- `intelligent_review_generator.py`: 获取复习计划信息
- `learning_analyzer.py`: 分析学习历史数据
- `personalization_engine.py`: 生成个性化建议
- `ebbinghaus_review.py`: 艾宾浩斯算法分析
- Canvas文件系统: 读取实际完成情况

## Advanced Features

### 多维度分析
- 📊 **时间维度**: 按日/周/月统计进度
- 🎯 **概念维度**: 各概念的掌握情况
- 🏆 **成就维度**: 目标达成和里程碑
- 💪 **努力维度**: 学习时间和频率

### 智能建议
- 🎯 基于进度数据的个性化建议
- 📈 学习策略优化建议
- ⏰ 时间安排调整建议
- 💡 动机激励策略

### 数据可视化
- 📊 进度条和完成率图表
- 📈 学习曲线趋势图
- 🎯 概念掌握度雷达图
- 📅 时间分布热力图

## Error Handling

- 如果找不到指定的计划ID，会显示最近的活动计划
- 如果Canvas文件无法访问，会基于缓存数据显示进度
- 如果数据不足，会提供默认的分析和建议

## Best Practices

### 定期检查
- 📅 建议每完成一个复习会话后检查进度
- 📊 每周查看一次详细的进度报告
- 🎯 每月进行一次全面的趋势分析

### 数据准确性
- ✅ 确保在Canvas中诚实填写评分
- ⏰ 记录实际的学习时间
- 📝 及时更新学习状态

### 持续改进
- 📈 根据进度报告调整学习策略
- 🎯 设定合理的阶段性目标
- 💡 积极响应个性化建议

## Related Commands

- `/generate-review`: 生成新的复习计划
- `/review-adapt`: 动态调整现有计划
- `/canvas-help`: Canvas操作帮助

## Example Usage Scenarios

### 场景1: 日常进度检查
```bash
/review-progress --format summary
```
快速了解当前复习进度，保持学习动力。

### 场景2: 深度分析
```bash
/review-progress plan-abc123 --format detailed --time-range week
```
全面分析本周学习效果，制定改进策略。

### 场景3: 概念专项跟踪
```bash
/review-progress --concepts "微积分,线性代数" --compare
```
重点跟踪特定概念的掌握进展。

### 场景4: 报告导出
```bash
/review-progress --export 学习月报_202501.md --format detailed
```
生成正式的学习报告，便于总结和分享。

## Performance Metrics

该命令的性能指标：
- ⚡ 响应时间: < 3秒
- 📊 数据准确性: > 95%
- 🔍 分析深度: 多维度综合分析
- 💡 建议质量: 个性化且可操作

---

*通过持续跟踪复习进度，你可以更好地了解自己的学习状况，及时调整学习策略，实现高效的知识掌握。*
