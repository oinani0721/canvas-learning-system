---
name: generate-review
description: 智能复习计划生成命令，基于学习历史分析生成个性化复习Canvas
tools: Bash, Read, Write
model: sonnet
---

# /generate-review Command

智能复习计划生成命令，基于Canvas学习历史分析、艾宾浩斯算法、Graphiti知识图谱和MCP语义记忆，为用户生成个性化的复习Canvas白板。

## Usage

```bash
/generate-review [canvas_path] [options...]
```

## Parameters

### Required Parameters
- `canvas_path`: 目标Canvas文件路径（如：离散数学.canvas）

### Optional Parameters
- `--plan-type`: 复习计划类型
  - `weakness-focused`: 薄弱环节导向（默认）
  - `comprehensive`: 全面复习
  - `targeted`: 针对性复习
- `--difficulty`: 难度级别
  - `easy`: 简单
  - `medium`: 中等
  - `hard`: 困难
  - `expert`: 专家级
  - `adaptive`: 自适应（默认）
- `--duration`: 预计复习时长（分钟，默认：45）
- `--max-concepts`: 最大概念数量（默认：5）
- `--user-id`: 用户ID（默认：default）
- `--output`: 输出文件路径（可选，自动生成）
- `--include-explanations`: 包含AI解释（true/false，默认：true）
- `--include-examples`: 包含实例（true/false，默认：true）

## Examples

### 基本用法
```bash
/generate-review 离散数学.canvas
```

### 指定计划类型和难度
```bash
/generate-review 离散数学.canvas --plan-type comprehensive --difficulty medium
```

### 针对薄弱环节的深度复习
```bash
/generate-review 离散数学.canvas --plan-type weakness-focused --duration 60 --max-concepts 3
```

### 自定义输出路径
```bash
/generate-review 离散数学.canvas --output 笔记库/我的复习计划.canvas
```

## Process Flow

1. **学习历史分析**: 分析用户最近30天的Canvas学习数据
2. **薄弱环节识别**: 基于评分记录和理解质量识别薄弱概念
3. **知识图谱查询**: 查询Graphiti获取概念关系和语义差距
4. **复习计划生成**: 根据艾宾浩斯算法生成个性化复习计划
5. **Canvas构建**: 创建包含检验问题、提示信息的复习Canvas
6. **个性化适配**: 根据用户学习风格和偏好定制内容

## Output

生成的复习Canvas包含：
- 📋 复习概览和目标
- 📊 进度跟踪表
- 📚 分组复习会话
- ❓ 个性化检验问题
- 💭 个人理解输入区
- 💡 学习建议和提示
- 🎯 总结和反思区域

## Features

### 智能分析
- 🔍 学习历史深度分析
- 📈 薄弱环节精准识别
- 🧠 知识图谱关系分析
- ⏰ 艾宾浩斯最佳复习时机

### 个性化定制
- 🎨 学习风格适配
- ⏱️ 最佳学习时长推荐
- 🏆 动机激励机制
- 📊 难度自适应调整

### 高质量内容
- 📝 多样化检验问题
- 💡 智能提示信息
- 🎯 清晰学习目标
- 📈 进度可视化

## Integration

该命令整合了以下系统组件：
- `learning_analyzer.py`: 学习历史分析
- `intelligent_review_generator.py`: 复习计划生成
- `review_canvas_builder.py`: Canvas构建
- `personalization_engine.py`: 个性化引擎
- `ebbinghaus_review.py`: 艾宾浩斯调度
- `graphiti_integration.py`: 知识图谱
- `mcp_memory_client.py`: 语义记忆

## Error Handling

- 如果Canvas文件不存在，会提示用户检查路径
- 如果学习数据不足，会使用默认配置生成通用复习计划
- 如果外部服务不可用，会降级使用本地算法

## Tips

### 最佳实践
1. **定期使用**: 建议每周生成1-2次复习计划
2. **诚实评估**: 在复习Canvas中诚实填写理解程度
3. **及时复习**: 按照生成的时间安排进行复习
4. **反馈优化**: 根据复习效果调整参数设置

### 参数建议
- **初学者**: 使用 `--plan-type weakness-focused` 和 `--difficulty easy`
- **进阶学习**: 使用 `--plan-type comprehensive` 和 `--difficulty adaptive`
- **考前冲刺**: 使用 `--plan-type targeted` 和增加 `--duration`

## Related Commands

- `/review-progress`: 查看复习进度
- `/review-adapt`: 动态调整复习计划
- `/canvas-help`: Canvas操作帮助

## Example Output

```
🎯 智能复习计划生成完成！

📁 生成文件: 笔记库/离散数学-智能复习-20250123.canvas
📊 分析概念: 12个
🎯 薄弱环节: 3个
⏱️ 预计时长: 45分钟
📚 复习会话: 2个

📋 复习概览:
• 计划类型: 薄弱环节导向复习
• 难度级别: 自适应
• 重点关注: 逻辑等价性、集合运算、证明方法

💡 使用建议:
1. 在Obsidian中打开生成的Canvas文件
2. 按照从上到下的顺序完成复习
3. 在黄色节点中详细记录你的理解
4. 诚实评分，不要查阅资料
```

---

*该命令是Canvas学习系统智能复习功能的核心入口，整合了多项AI技术提供个性化的学习体验。*