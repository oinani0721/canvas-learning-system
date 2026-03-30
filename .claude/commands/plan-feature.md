---
allowed-tools:
  - Read
  - Grep
  - Glob
  - Agent
  - mcp__graphiti-canvas__search_memory_facts
  - mcp__graphiti-canvas__add_memory
  - mcp__context7__resolve-library-id
  - mcp__context7__query-docs
  - mcp__sequential-thinking__sequentialthinking
description: 设计优先于代码 — 需求澄清 → 方案设计 → 用户确认 → 计划文件
argument-hint: <feature-description>
---

# /plan-feature — 功能规划（设计优先于代码）

在写任何代码前，完成完整的需求澄清和方案设计。替代 SuperPower brainstorming + writing-plans。

**用法**: `/plan-feature $ARGUMENTS`

**铁律: 本命令完成前不得写任何实现代码。**

---

## Phase 1: 需求澄清（一次一个问题）

1. 读取相关架构文档、MVP 清单和已知问题:
   - `docs/architecture.md`
   - `_decisions/mvp-plan.md`
   - `_decisions/decision-log.md`
   - `docs/known-gotchas.md` — ⛔ 必须读取，防止重复已知 Bug

2. 搜索 Graphiti 已有相关决策:
   ```
   search_memory_facts("$ARGUMENTS", group_ids:["canvas-dev"], max_facts:20, exclude_invalidated:true)
   ```

3. **逐个提问**（不要一次问多个）:
   - 这个功能在 MVP 14 项清单中吗？
   - 用户的预期体验是什么？
   - 有哪些约束？（技术栈、性能、安全）
   - 涉及哪些现有模块？

## Phase 2: 方案设计

1. 用 Sequential Thinking 分析需求，产出 2-3 种方案
2. 对每种方案标注:
   - 预期改动文件
   - 复杂度（低/中/高）
   - 风险点
   - 社区参考（Context7 查文档）

3. 用用户能听懂的语言展示方案（不堆术语）:
   ```
   方案 A: [名称]
   做法: [用比喻解释]
   优点: ...
   缺点: ...
   改动范围: [文件列表]
   ```

4. **推荐一个方案并等用户确认。**

## Phase 3: 计划文件

用户确认方案后，进入 Plan Mode 产出计划:
- 每个任务 2-5 分钟粒度
- 每个任务包含: 目标文件 + 具体步骤 + 验证方式
- 禁止 TBD/TODO/待定

## Phase 4: 记录

```
add_memory("[Decision] $ARGUMENTS — 方案选择", group_id:"canvas-dev")
```
