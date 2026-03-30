---
allowed-tools:
  - Read
  - Grep
  - Glob
  - mcp__graphiti-canvas__search_memory_facts
  - mcp__graphiti-canvas__search_nodes
description: Session 开始仪式 — 加载上下文 + 已知问题 + 当前任务状态
---

# /daily-start — Session 开始

每个新 session 的第一步。加载关键上下文，防止重复已知错误。

**用法**: `/daily-start`

---

## Step 1: 加载当前任务状态

```
Read _decisions/CURRENT_TASK.md
```

如果文件不存在，说明没有进行中的任务。

## Step 2: 加载已知问题

```
Read docs/known-gotchas.md
```

输出未修复问题的摘要（Pending 条目）。

## Step 3: 搜索 Graphiti 最近决策

```
search_memory_facts("最近决策 recent decisions", group_ids:["canvas-dev"], max_facts:10, exclude_invalidated:true)
```

## Step 4: 检查最近 git 活动

```bash
git log --oneline -10
```

## Step 5: 输出今日上下文摘要

```
## Session 上下文
- 当前任务: {CURRENT_TASK 摘要}
- 未修复 Gotchas: {数量} 条
- 最近决策: {Graphiti 结果摘要}
- 最近 commits: {git log 摘要}

## 今日注意事项
{从 gotchas 和决策中提取的关键提醒}
```
