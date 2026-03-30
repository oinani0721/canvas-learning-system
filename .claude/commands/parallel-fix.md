---
allowed-tools:
  - Bash
  - Read
  - Edit
  - Write
  - Grep
  - Glob
description: 按Bug类型编排并行修复
argument-hint: [backend|frontend|all] [--dry-run]
---

# /parallel-fix — 并行 Bug 修复编排器

按 Bug 类型将失败分配给专用 Agent，并行修复后综合验证。

**用法**: `/parallel-fix $ARGUMENTS`

---

## Phase 0: 上下文预加载（必须全部执行）

1. 读取持久 Bug 记忆:
```
Read docs/known-gotchas.md
```

2. 读取决策索引:
```
Read _decisions/decision-log.md
```

3. 搜索 Graphiti 历史:
```
search_memory_facts("parallel-fix bug", group_ids:["canvas-dev"], max_facts:30)
```

4. 运行诊断收集当前失败:

**后端:**
```bash
cd backend && python -m pytest tests/ -m "not integration" --tb=line -q --no-header 2>&1 | head -50
```

**前端:**
```bash
cd frontend && npx tsc --noEmit 2>&1 | head -50
```

**Lint:**
```bash
cd backend && ruff check app/ --select E,F,W 2>&1 | head -30
```

---

## Phase 1: Bug 分类与文件分区

将收集到的失败按以下规则分配到专用 Agent:

| 失败模式 | 分配给 Agent | 描述 |
|---------|-------------|------|
| 函数名-实现体不一致 / 空壳端点 / 死代码 | @integrity-auditor | DD-13/DD-11 审计 |
| pytest 断言失败 / 逻辑错误 | @logic-bug-fixer | 根因分析+修复 |
| tsc/pyright 类型错误 / 竞态条件 | @type-async-fixer | 类型+并发修复 |
| 注入/认证/API合同不匹配 | @security-api-reviewer | 安全+合同验证 |
| N+1查询 / 内存 / 重渲染 | @performance-reviewer | 性能优化 |

### 分区规则（铁律）

- **一个文件最多被一个 Agent 修改**。如果某文件涉及多种 Bug 类型，分给最高严重度的 Agent
- 输出分类表，等用户确认后再进入 Phase 2
- 如果 `$ARGUMENTS` 包含 `--dry-run`，到此为止，不执行修复

---

## Phase 2: 并行派发（最多 5 个子 Agent）

对每个分类组，使用 Agent 工具并行派发:

```
Agent(subagent_type="{agent-name}",
  prompt="
  ## 已知问题（来自 known-gotchas.md）
  {相关 gotcha 条目}

  ## 架构约束（来自 decision-log.md）
  {相关决策}

  ## 你的修复范围
  仅修改以下文件: {文件列表}

  ## 需要修复的问题
  {失败列表}

  ## 修复后验证
  运行: pytest {对应测试} -v
  确认: 无新增类型错误

  ## ⛔ 管道打通性 (DD-11)
  你新增的每个函数/方法，必须列出:
  1. 函数名 + 文件路径
  2. 预期调用方
  3. 如被限制不能改调用方，标注 '⚠️ 需要主 Agent 接线'
  ")
```

---

## Phase 3: 综合验证

所有子 Agent 完成后:

1. 收集所有 "⚠️ 需要主 Agent 接线" 标注，逐个在调用方文件中添加调用
2. 运行全量后端测试:
```bash
cd backend && python -m pytest tests/ -m "not integration" -q --tb=short
```

3. 运行全量前端类型检查:
```bash
cd frontend && npx tsc --noEmit
```

4. 对比修复前后失败数量
5. 如有新增失败（回归），识别是哪个 Agent 的修复引入的

---

## Phase 4: 更新持久记忆

1. 将新发现的 Bug 追加到 `docs/known-gotchas.md`（使用对应分类 G-FAKE/G-PIPE/G-TYPE 等）
2. 记录到 Graphiti:
```
add_memory("[Parallel-Fix] {修复数量}个Bug，涉及{文件数}个文件。{分类摘要}",
  group_id: "canvas-dev")
```

3. 生成修复摘要报告:

| 指标 | 值 |
|------|-----|
| 修复前失败数 | {N} |
| 修复后失败数 | {M} |
| 修复成功 | {N-M} |
| 新增 gotcha | {K} |
| 回归（需人工处理） | {R} |

---

## 错误恢复

- Agent 静默失败 → 检查 `.claude/audit/{日期}.jsonl` 审计日志
- Agent 引入新失败 → `git diff` 查看该 Agent 的改动，必要时 revert
- 文件冲突 → 将冲突 Agent 推迟到顺序执行的 Phase 5
