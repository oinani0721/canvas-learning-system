# 独立核实：E 类（agents 模板）的三个数字

卡文 §〇.20 说「`EXPECTED_AGENT_TEMPLATES` 18 项、`git ls-files .claude/agents` = 11、缺 7」，
但红是 **9 条**——卡文没解释这个差额。本节查清。

## AST 精确计数（不是 grep）

```
EXPECTED_AGENT_TEMPLATES = 18 项
实存 11 / 缺 7 / 实存但不在期望表 0
缺：canvas-orchestrator, graphiti-memory-agent, hint-generation, iteration-validator,
    parallel-dev-orchestrator, planning-orchestrator, review-board-agent-selector
```

与卡文点名的 7 个**逐字相同** ✅

> ⚠️ 方法记录：我第一次用 `grep -cE '^\s+"'` 数，得到 **30** —— 判据太宽，
> 把 docstring 里的引号行也算进去了。改用 AST 取 `EXPECTED_AGENT_TEMPLATES`
> 的 `elts` 才得到正确的 18。**数清单用 AST，不用 grep。**

## 9 条红的构成（差额解开）

| 构成 | 条数 |
|---|---|
| `test_agent_template_exists[<缺失模板>.md]` 参数化 | **7** |
| `test_hint_generation_template_exists`（单独点名 hint-generation） | 1 |
| `test_minimum_template_count`（`Expected >= 17 …, found 11`） | 1 |
| **合计** | **9** ✅ |

⇒ 「缺 7 个模板」与「红 9 条」不矛盾：有 2 条是**独立断言**，不是参数化。

## 顺带发现的内部不一致（登记，不修）

`test_minimum_template_count` 的阈值是 **17**（`:86`），docstring（`:84`）写
「At least 17 agent templates must exist (**original count before deletion**)」；
而 `EXPECTED_AGENT_TEMPLATES` 是 **18** 项。

⇒ 期望表后来加了 1 项，阈值没同步。当前不影响红（实存 11 < 17 < 18，两者都失败），
但一旦补回 7 个模板到 18，阈值 17 就变成一道**永远宽 1 的门** ——
少一个模板它也不会响。RED-E 卡应当把两处对齐。

## 历史（卡文 §〇.20，本卡未独立验证 commit）

`abf1d585` 删 → Story 31.A.2 恢复 → `f425d7b7`（"ralph-loop: iteration 0"）**再删**。
⇒ 该目录被删过两次，这是 RED-E 卡要附「是否加保护门」裁决请求的由来。
