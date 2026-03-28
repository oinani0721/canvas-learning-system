---
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - Agent
  - mcp__context7__resolve-library-id
  - mcp__context7__query-docs
  - mcp__graphiti-canvas__search_memory_facts
  - mcp__graphiti-canvas__add_memory
description: 技术能力审计 — Context7 查文档 → 枚举能力 → 用户确认 → 记录
argument-hint: <technology-name>
---

# /tech-audit — 技术能力审计

对指定技术执行完整能力审计，防止只用了技术的 20% 能力。

**用法**: `/tech-audit $ARGUMENTS`

---

## Step 1: 查文档

1. 调用 `mcp__context7__resolve-library-id`，libraryName = "$ARGUMENTS"
2. 选择最匹配的库
3. 调用 `mcp__context7__query-docs`，query = "all features capabilities configuration options API"，tokens = 10000

## Step 2: 枚举能力

从文档中提取 **所有** 可用能力，分类列出：

```
## [Technology] vX.Y.Z — 能力清单
来源: Context7 /org/repo
审计日期: [today]

### 核心能力
1. [名称] — [描述] — 配置: [key=default]

### 高级能力
N. [名称] — [描述] — 配置: [key=default]

### 安全能力
...

### 性能能力
...
```

## Step 3: 检查当前使用

用 Grep 搜索代码库中该技术的 import/配置/使用：
- ✅ 已启用并使用
- 🟡 已导入但未配置/调用
- ❌ 未使用

计算利用率: (✅ 数量 / 总能力) × 100%

## Step 4: 向用户展示

```
该技术有 [N] 个能力，当前启用 [M] 个（[X]% 利用率）。
以下能力尚未启用：
[编号列表]

你需要启用哪些？回复编号、'all' 或 'none'。
```

**必须等用户回复后再继续。**

## Step 5: 记录决策

用户回复后：
1. 记录到 Graphiti: `add_memory("[Tech-Audit] $ARGUMENTS — [date]")`
2. 输出实施任务清单（每个选中能力的具体代码改动）
