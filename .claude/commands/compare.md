---
allowed-tools:
  - Read
  - Glob
  - Grep
---

# 概念对比表

生成结构化的 Markdown 对比表，帮助清晰区分易混淆的概念，至少5个对比维度。

**用法**: `/compare <概念A> vs <概念B> [vs <概念C>]`

也可以用"和"、逗号或空格分隔概念：
- `/compare 逆否命题 vs 否命题 vs 逆命题`
- `/compare 栈和队列`
- `/compare TCP, UDP`

请先读取 Agent 定义获取完整指导：

```
Read .claude/agents/comparison-table.md
```

读取后，严格按照定义中的 System Prompt 执行任务。

## 输入适配

用户提供的对比概念如下：

$ARGUMENTS

请从上述内容中解析出要对比的概念列表（2-5个概念）：
- 用 "vs"、"和"、"与"、逗号、空格等分隔符识别多个概念
- 如果只有一个概念，请提示用户需要提供至少2个概念进行对比
- 如果用户附带了材料内容，作为 `material_content` 提供上下文
- 如果用户包含"我的理解是..."，提取为 `user_understanding`

## 输出适配

直接输出 Markdown 格式的对比表，包含至少5个对比维度：
1. 定义
2. 核心特点
3. 适用场景
4. 典型示例
5. 易错点
6. 记忆技巧（推荐）

使用标准 Markdown 表格语法。不要输出 JSON。
