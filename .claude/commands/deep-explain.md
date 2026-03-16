---
allowed-tools:
  - Read
  - Glob
  - Grep
---

# 深度澄清路径

生成1500+字的深度系统性讲解，严格按照4步骤流程彻底讲清楚一个概念。

**用法**: `/deep-explain <概念名称或材料内容>`

请先读取 Agent 定义获取完整指导：

```
Read .claude/agents/clarification-path.md
```

读取后，严格按照定义中的 System Prompt 执行任务。

## 输入适配

用户提供的材料/概念如下：

$ARGUMENTS

请将上述内容解析为：
- 如果是简短的概念名，作为 `topic` 和 `concept`
- 如果是较长的材料文本，作为 `material_content`，并从中提取 `topic`
- 如果用户包含"我的理解是..."或类似表述，提取为 `user_understanding`
- 否则 `user_understanding` 为 null

## 输出适配

直接输出 Markdown 格式的澄清路径文本（1500+字），包含4个步骤：
1. 步骤1：概念澄清（300-400字）
2. 步骤2：深层分析（500-600字）
3. 步骤3：关联网络（400-500字）
4. 步骤4：应用场景（300-400字）

不要输出 JSON，直接输出 Markdown 文本。
