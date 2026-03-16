---
allowed-tools:
  - Read
  - Glob
  - Grep
---

# 例题教学

生成完整的例题教学，包含题目、详细解答、易错点提醒和变式练习，约1000字。

**用法**: `/example-teach <概念名称或材料内容>`

请先读取 Agent 定义获取完整指导：

```
Read .claude/agents/example-teaching.md
```

读取后，严格按照定义中的 System Prompt 执行任务。

## 输入适配

用户提供的材料/概念如下：

$ARGUMENTS

请将上述内容解析为：
- 如果是简短的概念名，作为 `concept` 和 `topic`
- 如果是较长的材料文本，作为 `material_content`，并从中提取 `concept`
- 如果用户包含"我的理解是..."或类似表述，提取为 `user_understanding`
- 否则 `user_understanding` 为 null

## 输出适配

直接输出 Markdown 格式的例题教学，包含完整的6个部分：
1. 题目（50-150字）
2. 思路分析（150-250字）
3. 分步求解（300-500字）
4. 易错点提醒（150-250字）
5. 变式练习（150-250字）
6. 答案提示（100-150字）

总字数约1000字（800-1200字范围）。不要输出 JSON。
