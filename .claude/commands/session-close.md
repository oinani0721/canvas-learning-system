---
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - mcp__graphiti-canvas__add_memory
  - mcp__graphiti-canvas__search_memory_facts
description: Session 结束 — 决策记录 + 上下文转储 + 任务状态更新
---

# /session-close — Session 结束

每个 session 结束前执行。确保决策不丢失，下个 session 能无缝接手。

**用法**: `/session-close`

---

## Step 1: 回顾本 session 改动

```bash
git diff --stat HEAD~5 2>/dev/null || git diff --stat
```

## Step 2: 识别未记录的决策

回顾本 session 对话，提取:
- 架构决策（选了什么、否决了什么、为什么）
- 新发现的 Bug 或陷阱
- 改变了的技术方向

对每个决策:
```
add_memory("[Decision] {决策简述}", group_id:"canvas-dev")
```

## Step 3: 更新 CURRENT_TASK.md

```
Write _decisions/CURRENT_TASK.md
```

内容包含:
- 当前进行到哪一步
- 下一步需要做什么
- 阻塞项（如有）
- 相关文件列表

## Step 4: 更新 known-gotchas.md

如果本 session 发现新的 Bug 或陷阱:
```
Edit docs/known-gotchas.md  # 追加新条目
```

## Step 5: 输出接手摘要

```
## Session 结束摘要
- 完成: {本 session 完成的工作}
- 决策: {记录了 N 条决策}
- 下一步: {CURRENT_TASK 中的下一步}
- Gotchas: {新增 N 条已知问题}

## 下个 Session 接手指南
{具体的接手步骤，包括需要先读哪些文件}
```
