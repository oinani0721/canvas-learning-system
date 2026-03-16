---
allowed-tools:
  - Read
  - Glob
  - Grep
---

# 记忆锚点

生成3种记忆辅助（类比、故事、口诀/谐音），帮助长期记忆抽象概念。

**用法**: `/memory-anchor <概念名称>`

请先读取 Agent 定义获取完整指导：

```
Read .claude/agents/memory-anchor.md
```

读取后，严格按照定义中的 System Prompt 执行任务。

## 输入适配

用户提供的概念如下：

$ARGUMENTS

请将上述内容解析为：
- 简短的概念名作为 `concept`
- 如果附带材料内容，作为 `material_content`
- 如果用户包含"我的理解是..."，提取为 `user_understanding`
- 否则 `user_understanding` 为 null

## 输出适配

直接输出 Markdown 格式的记忆锚点，包含3个部分：
1. 类比（50-100字）- 用日常事物类比抽象概念
2. 故事（约100字）- 包含关键信息的小故事
3. 口诀/谐音（1-2句）- 朗朗上口的记忆口诀

不要输出 JSON，直接输出 Markdown 文本。
