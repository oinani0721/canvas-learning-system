结论：未发现 BLOCKER/HIGH；发现 3 个 MEDIUM 事实精度问题。零改写、零新能力承诺及 Markdown 结构均通过，但建议修正这 3 处后再批准。

审查范围：`card/n4-readme` @ `b47ebfba351f3eedb496a97961083c5e3b1d5df7`。审查期间 `README.md` 被外部暂存；当前 staged patch 仍是最初看到的同一内容：`19 additions / 0 deletions`，blob `ef20f727…`。本审查未修改文件或索引。

## Findings

1. **MEDIUM — [README.md:5](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/README.md:5)、第 37 行 — “后端枚举为 13 个”口径不准确**

   理由：[AgentType](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/app/services/agent_service.py:141) 实际有 15 个不同字符串值；其中两项虽注释为 Alias，但值不同，不是 Python Enum 真别名。另一个 [VALID_AGENT_TYPES](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/app/middleware/agent_metrics.py:66) 又有 14 项。“13”只能通过人工合并两个兼容值获得。

   建议：改为“`AgentType` 有 15 个值，其中 2 个注释为兼容别名；后端另有 14 项清单，口径待核定”，或删掉后端精确数字。

2. **MEDIUM — [README.md:8](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/README.md:8)、第 147 行 — `8011` 是自指成真**

   理由：`git show HEAD:README.md | rg '8000|8001|8011'` 只得到 `8000/8001`；`8011` 在当前 README 中仅由这次新增的第 8、147 行引入，因此“文中同时出现三种端口”“本文其他处的 8011”均不成立。`8011` 的真实来源是 [.env.example:83](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/.env.example:83)；Compose 再通过 [docker-compose.yml:150](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/docker-compose.yml:150) 映射到容器 8001。

   建议：改为“README 原文同时有 8000/8001；仓库当前 `.env.example` 另使用宿主端口 8011”。

3. **MEDIUM — [README.md:112](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/README.md:112) — “不会被现行插件读取”过度绝对**

   理由：旧目录确实漂移；当前 [manifest.json:2](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/frontend/obsidian-plugin/manifest.json:2) 的 ID 和 [install-vault.sh:66](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/scripts/install-vault.sh:66) 的部署目录都是 `canvas-learning-system`。但仓库不能证明旧目录下插件完全不会加载；[Obsidian 官方 Manifest 文档](https://docs.obsidian.md/Reference/Manifest)只支持“不匹配可能导致部分方法不被调用”。

   建议：改为“与当前 manifest ID 和受支持部署目录不一致，可能导致加载或部分生命周期行为异常”。

## 逐项硬门

1. **零改写：通过。** `git diff --cached --numstat -- README.md` 为 `19 0`；6 个 hunk 均为 `@@ -N,0 +...`，无旧行删除、替换或文件模式变化；`diff --check` 通过。

2. **零新能力承诺：通过。** 对照[计划书 §12.7 L633](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/_bmad-output/审查/2026-08-20-Canvas-Learning-System-生产力化长期Goal计划书.md:633)：

| 禁止声明 | 结果 |
|---|---|
| production-ready | 通过：未出现 |
| 任意 vault 一键可用 | 通过：无安装成功承诺 |
| 完整 multi-vault safe | 通过：未出现 |
| Graphiti 永久且全量可重建 | 通过：未出现 |
| full multi-source RAG 默认主链 | 通过：未出现 |
| hit@k 写成 recall | 通过：无指标声明 |
| FSRS/UI 完全一致 | 通过：只声明尚未重验 |
| Canvas↔Excalidraw 无损双向 | 通过：未出现 |
| 14 个 Agent 协同 | 通过：“14”仅在矛盾警告中出现 |
| 移动端可用 | 通过：未出现 |
| skipped/degraded 等同成功 | 通过：未出现 |

   **Docker 措辞通过。** “相对可信”“部署起点”及后续证据限定没有承诺部署成功、production-ready 或任意 vault 可用。限制：本审查未重跑 live Docker 部署，只裁决措辞边界。

3. **横幅完整性：通过。** [README.md:3](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/README.md:3) 有恰好 1 个 WARNING、5 类漂移点，并在第 11 行指向 Docker 段；数量超过 ≥3 要求。端口和 Agent 两项的事实精度受上述 MEDIUM 影响，但结构完整。

4. **事实抽查：部分通过。**

   - Agent 正文：通过，3 个 Decomposition + 6 个 Explanation + 2 个 Assessment = 11。
   - 后端 13：不通过，见 Finding 1。
   - 旧插件目录不一致：通过；“完全不会读取”不通过，见 Finding 3。
   - `.canvas` 右键 Agent：通过。当前生产构建源 [main.ts:135](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/frontend/obsidian-plugin/src/main.ts:135) 及整个插件源码均无 `canvas-menu/file-menu/contextmenu/Menu` 挂载。
   - 三种 README 端口：不通过，见 Finding 2。
   - standalone `0.0.0.0` 与 P0-0 冲突：通过；当前 Compose 已绑定 loopback。
   - Review Canvas“未重新验证”：通过。后端存在实现片段，但当前插件无对应产品调用闭环，fail-closed 措辞恰当。

5. **Markdown 结构：通过。** `[!WARNING]` 形成单一 blockquote；第 112 行三空格缩进使标注属于编号列表第 3 项，第 4/5 项仍连续；第 147 行位于 bash fence 外；本地 CommonMark 解析确认标题、代码围栏和 HTML block 数量及顺序未被破坏。

**BLOCKER/HIGH 清零: 是**



---

## 附录：二轮复核（MEDIUM 处置验证，high 档）

- **M1 — RESOLVED。** [`AgentType`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/app/services/agent_service.py:141) 确有 15 个不同字符串值，其中 2 个源码注释为 Alias；[`VALID_AGENT_TYPES`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/app/middleware/agent_metrics.py:66) 确为 14 项。新措辞不再误报“13 个”。此处“别名”是兼容称谓，并非 Python Enum 同值别名。

- **M2 — RESOLVED。** HEAD 版 README 只出现 8000、8001；8011 确实来自 [`.env.example`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/.env.example:83)，并由 [`docker-compose.yml`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/docker-compose.yml:150) 用作宿主端口、映射至容器 8001。不存在原先的 8011 自指成真。

- **M3 — RESOLVED。** [`manifest.json`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/frontend/obsidian-plugin/manifest.json:2) 和受支持部署目录均为 `canvas-learning-system`。新措辞改为“可能导致……无法正常加载”，消除了“不会被读取”的绝对断言；该风险限定与 [Obsidian 官方 Manifest 文档](https://docs.obsidian.md/Reference/Manifest)所述目录名不匹配可能造成部分方法不被调用相容。

- **纯新增：通过。** 最终复查 staged blob `060344c8…`；`git diff --cached --numstat -- README.md` 为 `19 0`，全部 6 个 hunk 只有新增行，`diff --check` 通过。

- **新能力承诺/L633：通过。** 相对一轮 blob `ef20f727…` 仅修改上述 5 行措辞，均为事实纠偏或风险 hedge；未新增能力承诺，也未新增 [L633](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/_bmad-output/审查/2026-08-20-Canvas-Learning-System-生产力化长期Goal计划书.md:633) 禁止声明。“14 项清单”是口径说明，不是“14 个 Agent 协同”承诺。

BLOCKER/HIGH 清零: 是

MEDIUM 处置复核: 通过
