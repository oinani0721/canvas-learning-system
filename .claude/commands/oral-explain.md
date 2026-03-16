---
allowed-tools:
  - Read
  - Glob
  - Grep
---

# 口语化解释

像教授讲课一样，用口语化的方式解释概念，生成800-1200字的通俗易懂讲解。

**用法**: `/oral-explain <概念名称或材料内容>`

请先读取 Agent 定义获取完整指导：

```
Read .claude/agents/oral-explanation.md
```

读取后，严格按照定义中的 System Prompt 执行任务。

## 输入适配

用户提供的材料/概念如下：

$ARGUMENTS

请将上述内容解析为：
- 如果是简短的概念名（如"傅里叶变换"），作为 `topic` 和 `concept`
- 如果是较长的材料文本，作为 `material_content`，并从中提取 `topic`
- 如果用户包含"我的理解是..."或类似表述，提取为 `user_understanding`
- 否则 `user_understanding` 为 null

## 输出适配

直接输出 Markdown 格式的口语化解释，包含完整的4个部分：
1. 为什么要学这个？（背景铺垫）
2. 核心讲解（主体内容）
3. 举个例子（生动例子）
4. 常见误区

总字数800-1200字。不要输出 JSON，直接输出 Markdown 文本。
