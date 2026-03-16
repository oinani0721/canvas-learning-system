---
allowed-tools:
  - Read
  - Glob
  - Grep
---

# 四层次解释

生成4个渐进式层次的解释（新手→进阶→专家→创新），总字数1200-1600字。

**用法**: `/four-level <概念名称或材料内容>`

请先读取 Agent 定义获取完整指导：

```
Read .claude/agents/four-level-explanation.md
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

直接输出 Markdown 格式的四层次解释，包含：
1. 新手层（Beginner）- 300-400字
2. 进阶层（Intermediate）- 300-400字
3. 专家层（Expert）- 300-400字
4. 创新层（Innovation）- 300-400字

不要输出 JSON，直接输出 Markdown 文本。
