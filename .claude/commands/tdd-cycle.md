---
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
  - Agent
description: TDD 红绿重构循环 — 先写失败测试 → 最小实现 → 重构
argument-hint: <feature-or-function-description>
---

# /tdd-cycle — TDD 红绿重构循环

通过子 Agent 隔离实现严格的 RED-GREEN-REFACTOR 循环。
学术验证: AgentCoder 96.3% vs 67% pass@1（隔离 vs 单 Agent）。

**用法**: `/tdd-cycle $ARGUMENTS`

---

## Phase 1: RED — 编写失败测试

先读取已知问题，注入子 Agent:
```
Read docs/known-gotchas.md
```

启动 **test-writer 子 Agent**（独立上下文，防止与实现互相污染）:

```
Agent(prompt: "你是 TDD test-writer。只写测试，不写实现。

## 已知问题（来自 known-gotchas.md，必须覆盖相关条目）
{gotchas 中与当前功能相关的条目}

任务: 为以下功能编写测试: $ARGUMENTS

规则:
1. 后端(.py): 用 pytest + FastAPI TestClient
2. 前端(.ts/.tsx): 用 vitest + @testing-library/react
3. 测试必须描述用户行为，不是实现细节
4. 包含: 正常路径 + 边界条件 + 错误处理
5. 测试文件命名: test_[module].py 或 [module].test.tsx

写完后运行测试，确认全部 FAIL（红色）。
如果有测试意外通过，说明测试写得不对，需要修改测试。

输出: 测试文件路径 + 失败的测试列表")
```

**在确认所有测试都失败之前，不得进入 Phase 2。**

## Phase 2: GREEN — 最小实现

启动 **implementer 子 Agent**（独立上下文）:

```
Agent(prompt: "你是 TDD implementer。只写让测试通过的最小代码。

## 已知问题（避免重蹈覆辙）
{gotchas 中与当前功能相关的条目}

规则:
1. 读取测试文件理解预期行为
2. 写最小代码让所有测试通过
3. 不写额外功能、不优化、不重构
4. 如果测试失败，修改实现，绝不修改测试
5. 运行测试确认全部 PASS（绿色）

输出: 实现文件路径 + 通过的测试列表")
```

**在确认所有测试都通过之前，不得进入 Phase 3。**

## Phase 3: REFACTOR — 改进代码

在当前上下文中（不需要子 Agent）:
1. 读取测试文件和实现文件
2. 改进代码质量（命名、结构、重复消除）
3. 每次改动后运行测试确认仍然全部通过
4. 如果测试失败，撤销改动

## 轻量模式（快速修复）

对于 30 分钟内的小修复，跳过子 Agent:
1. 先写测试（在当前上下文）
2. 运行确认失败
3. 写最小实现
4. 运行确认通过
5. 重构

## 测试命令参考

```bash
# 后端
cd backend && python -m pytest tests/ -x -v
# 前端
cd frontend && npx vitest run --reporter=verbose
```
