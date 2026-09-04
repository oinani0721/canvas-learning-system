审查对象：WT `card/w5-reviewapp`，HEAD `24912aa6ac78612247b6398d3b736f5851318e24`。结论为 **FAIL**：1 个 BLOCKER、3 个 HIGH 未清零。

## BLOCKER

1. [CLAUDE.md:8](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/CLAUDE.md:8)、[CLAUDE.md:13](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/CLAUDE.md:13) — DD-14 追踪链不满足。

   - 问题：三笔功能提交 `b984f1e2`、`a9410c9f`、`24912aa6` 的完整 commit message 均无强制的 `PLAN-NNN`。
   - 失败场景：无法把代码提交绑定到已勾选计划节点；规则明定“违反 = 阻断”。
   - 建议：由主 session 补齐真实 plan/CURRENT_TASK 证据，并决定采用合规补救提交还是经授权重建提交历史；当前不能声明 merge-ready。

## HIGH

1. [review_app.py:379](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/backend/app/api/v1/endpoints/review_app.py:379)、[review_app.py:406](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/backend/app/api/v1/endpoints/review_app.py:406)、[review_app.py:411](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/backend/app/api/v1/endpoints/review_app.py:411)、[review_app.py:452](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/backend/app/api/v1/endpoints/review_app.py:452) — HIGH-1 的成功结算仍未绑定目标 vault、版本和真实落屏。

   - 问题：`settlePendingSync(..., true)` 会把所有 pending 库结算成功，不检查 GET 是否包含目标库、目标库是否为可用 projection，也不比对 POST 返回的 `entry`。同时 `lastData` 和成功提示在渲染前提交。
   - 实测场景一：目标库 GET 返回合法四态 `corrupt`；页面同时显示“投影文件无法解析”和绿色“数字已更新”。
   - 实测场景二：`vaults` 是数组但成员不可渲染；坏数据先写入、pending 先删除并显示“数字已更新”，随后渲染异常才显示 unavailable。
   - 建议：完整验证并预渲染候选数据，成功后原子提交；pending 按 vault 保存 POST `entry` 或版本标识，只有目标条目存在、可用且版本匹配才结算成功。

2. [test_review_app.py:363](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/backend/tests/unit/test_review_app.py:363)、[test_review_app.py:379](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/backend/tests/unit/test_review_app.py:379)、[test_review_app.py:397](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/backend/tests/unit/test_review_app.py:397)、[test_review_app.py:1045](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/backend/tests/unit/test_review_app.py:1045) — HIGH-3 提取器仍小于浏览器 HTML tokenizer 的结束标签语言。

   - 问题：正则只计数空白后直接闭合的 script 结束标签；浏览器还会接受 solidus 分隔及携带属性的结束标签。
   - 实测：同一 marker 页面得到 `extractor_end_count=1`、提取器保留后半字节，而 HTML parser 已在 marker 处结束脚本。
   - 失败场景：Node 门执行浏览器不会执行的后半段代码，真实页面健全性门仍可假绿。
   - 建议：对最终规范结束符之前出现的任意大小写 script 结束前缀 fail-closed，或改用真实 HTML5 tokenizer；补两种分隔形态的负门。

3. [test_review_app.py:254](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/backend/tests/unit/test_review_app.py:254)、[test_review_app.py:267](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/backend/tests/unit/test_review_app.py:267) — HIGH-4b AST 门锁定的是调用拼写，不是实际绑定。

   - 问题：允许名可以先被重绑定到非允许 callable；Attribute 也只检查尾部方法名，不检查 receiver。
   - 实测：无新增 import、所有 Call 节点仍只显示白名单名字/属性，门判接受，但 harmless 反例成功读取并返回工作区 `backend/pytest.ini` 内容。
   - 建议：禁止允许名的重新赋值、参数遮蔽和 import alias；校验完整调用表达式及 receiver，增加“允许名重绑定”和“错误 receiver”变异。

## MEDIUM

1. [review_app.py:306](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/backend/app/api/v1/endpoints/review_app.py:306)、[review_app.py:369](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/backend/app/api/v1/endpoints/review_app.py:369) — M1 修复未贯穿重绘链。`state.notes` 是 null-prototype，但 `freshNotes()` 又返回普通 `{}`；`__proto__` 库重绘后提示变成 `[object Object]`。建议同样使用 null-prototype，并用 own-key 读取。

2. [review_app.py:399](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/backend/app/api/v1/endpoints/review_app.py:399)、[review_app.py:426](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/backend/app/api/v1/endpoints/review_app.py:426) — 最新代 GET 永不 settle 时轮询永久停摆。下一次 `schedule()` 仅在当前 await 完成后建立。建议加入 `AbortController` 超时或独立的代际 watchdog。

3. [test_review_app.py:93](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/backend/tests/unit/test_review_app.py:93)、[test_review_app.py:112](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/backend/tests/unit/test_review_app.py:112) — M5 外链门仍可绕过。非 text 的 `data:`、scheme/标签/CSS 的大小写变体、未加引号的协议相对链接及 CSS `@import` 均未完整覆盖。建议解析所有 URL-bearing 属性，统一解码和大小写，并整体拒绝 `data:`。

4. [UAT:3](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/_bmad-output/验收单/UAT-CARD-G6-2-交互复习壳-2026-09-01.md:3)、[UAT:29](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/_bmad-output/验收单/UAT-CARD-G6-2-交互复习壳-2026-09-01.md:29)、[UAT:40](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/_bmad-output/验收单/UAT-CARD-G6-2-交互复习壳-2026-09-01.md:40)、[UAT:61](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/_bmad-output/验收单/UAT-CARD-G6-2-交互复习壳-2026-09-01.md:61) — 验收单证据陈旧。仍锚旧提交、`80=56+24`、`35/35`，且 round-2 结论未回填；当前事实是 `87=56+31`、`42/42`、round-2 FAIL。建议按当前 HEAD 和本轮裁决重写。

## LOW

1. [review_app.py:428](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/backend/app/api/v1/endpoints/review_app.py:428)、[review_app.py:455](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/backend/app/api/v1/endpoints/review_app.py:455) — POST 在飞期间切到后台后，POST 成功仍无条件启动一个新 GET。这不属于已接受的“隐藏态首轮 GET”。建议隐藏时保留 pending，回前台再结算。

2. [review_app.py:273](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/backend/app/api/v1/endpoints/review_app.py:273) — 未知状态防御对 `constructor`/`__proto__` 会命中继承属性而非灰色 fallback。建议用 own-key 访问 `STATUS_META`。

## Round-2 整改逐项裁决

| 声明 | 裁决 | 理由 |
|---|---|---|
| HIGH-1 因果一致性 | **NOT VERIFIED** | `pollGen` 的旧成功/旧失败丢弃正确，但成功结算未绑定目标 vault/版本，且发生在渲染成功前。 |
| HIGH-3 提取同源 | **NOT VERIFIED** | 仍漏浏览器认可的其他 script 结束标签分隔形态。 |
| HIGH-4a 变异判据 | **VERIFIED（限定）** | 按本轮指定证据口径，[日志:45](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/_bmad-output/审查/evidence-g62/mutation-run-final.log:45) 与[裁判输出:11](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/_bmad-output/审查/evidence-g62/裁判命令输出-r3.txt:11)记录 42/42 和 `rc==1` 判据；因读面限制，未独立检查脚本实现或逐 mutant 原始 pytest 输出。 |
| HIGH-4b AST 门 | **NOT VERIFIED** | 允许名重绑定可绕过。 |
| M1 null-prototype | **NOT VERIFIED** | `freshNotes()` 重新引入普通对象。 |
| M2 200 坏形状 | **NOT VERIFIED** | 只验证 `vaults` 为数组；坏成员仍先提交并可造成成功提示与 unavailable 并存。 |
| M3 inflight disabled | **VERIFIED** | 点击、重绘、finally 解锁三段均落实。 |
| M4 上海本地日 | **VERIFIED** | 跨日时间经 `parseDueMs()`、`shDay()` 显示为 09-03。 |
| M5 外链门 | **NOT VERIFIED** | 当前页面无外链，但门存在上述大小写与覆盖绕过。 |

## 未发现与验证边界

- 未发现当前生产页面存在外部 URL 或第三个 fetch；两个 API 均由 `url_for(...).path` 注入，同源约束成立。
- clamp 5–60 秒、常规隐藏暂停/回前台 GET、自动路径不 POST、旧代际不重排程：未发现问题。
- 已知四态、休息日仅 `ok && due_count===0`、JS 不重算 due：未发现问题。
- `/overview/app` 与零 JS `/overview/page` 共存；`review_overview.py` 相对基点无改动。
- W6 三字段缺省渲染正确；真实 GET 透传仍须按卡文在 W6 先合后复核。
- 当前 HEAD 独立实跑：`87 passed, 10 warnings`；`pyright` 0 错误；`ruff check/format` 通过。这是定向套件，不代表全量 CI 或部署验收。
- 未读取两处受限攻击样本正文；Graphiti MCP 本会话未暴露；未做 live 浏览器写侧操作。

总结论：**FAIL（存在 DD-14 BLOCKER，且 HIGH-1、HIGH-3、HIGH-4b 未清零）。**


