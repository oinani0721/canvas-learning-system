---
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - Agent
  - mcp__graphiti-canvas__search_memory_facts
  - mcp__graphiti-canvas__add_memory
description: 对抗性代码审查 — 独立 Agent 审查 → 问题评级 → 修复 → 记录
argument-hint: [file-or-directory] [--scope=recent|full]
---

# /code-review — 对抗性代码审查

启动独立 Agent 对代码进行对抗性审查。替代 bmad-bmm-code-review，保留其核心审查维度。

**用法**: `/code-review $ARGUMENTS`

---

## Step 1: 确定审查范围

- 无参数: 审查最近 git diff 的改动
- 指定文件/目录: 审查该范围
- `--scope=full`: 全量审查

```bash
git diff --name-only HEAD~3  # 最近 3 个 commit 的改动文件
```

## Step 2: 启动独立审查 Agent

**必须使用独立 Agent**（不是当前 Agent 自己审查自己）:

```
Agent(prompt: "你是对抗性代码审查员。审查以下文件: [文件列表]。
审查维度:
1. ⛔ Mock/假实现: mock数据、模拟API、硬编码假返回值、TODO占位
2. ⛔ 管道打通性: 调用链是否连通？函数存在但无人调用？
3. ⛔ 名实一致: 函数名是否匹配实际行为？import 是否匹配调用？
4. 逻辑正确性: 算法正确？边界条件？
5. 安全性: 输入验证？注入风险？敏感数据？
6. 错误处理: 异常捕获？静默失败？
7. 性能: 重复计算？N+1查询？

对每个问题输出:
- 严重性: CRITICAL / HIGH / MEDIUM / LOW
- 文件:行号
- 问题描述
- 修复建议

总结: [可复用/需修复/需重写] + 问题统计")
```

## Step 3: 汇总结果

```
## 代码审查报告
审查范围: [文件列表]
审查日期: [today]

### 统计
| 严重性 | 数量 |
|--------|------|
| CRITICAL | N |
| HIGH | N |
| MEDIUM | N |
| LOW | N |

### CRITICAL 问题（必须修复）
1. [file:line] — [描述] — [修复建议]

### HIGH 问题（应该修复）
...

### 评级: [可复用 / 需修复 / 需重写]
```

## Step 4: 记录

```
add_memory("[Code-Review] [范围] — [评级] [统计]", group_id:"canvas-dev")
```
