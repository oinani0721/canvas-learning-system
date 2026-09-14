# 独立复核请求 round-5（终审，轮次上限） — CARD-T-EDGES（BATCH-2026-09-11-第十四批 · 车道 T5-B）

## ① 背景 + 最小读取面（只读，不要改任何文件）

仓库树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs`

**当前 HEAD = `7c63c5eb`**。本卡代码 commit 链：
`c9c73f57`(r1 审) → `9764cceb`(r2 审) → `c2e3d533`(r3 审) → `caf8180e`(r4 审)
→ `7c63c5eb`(本轮，**纯 docstring**，去 docstring 后 AST 与 `caf8180e` 完全相同)。

round-4 你给出 BLOCKER 0 / HIGH 1（H1，标注「缺陷成立但超出本卡改动面」，并确认披露
达到最低要求）/ MEDIUM 0 / LOW 1（L3 整改未完整）。本轮只处理 L3，并请给绑定
`7c63c5eb` 的终审。

**最小读取面**：

1. `git --no-pager diff --no-color caf8180e 7c63c5eb -- . ':(exclude)_bmad-output'`
   （**只看本轮**；应只有 docstring）
2. `git --no-pager diff --no-color 9b30179a 7c63c5eb -- . ':(exclude)_bmad-output'`
   （本卡全量 diff）
3. `backend/tests/integration/test_edges_dual_write_neo4j_t5b.py` 的模块 docstring
   与 `_test_uri_port_is_allowed` 的 docstring
4. `backend/tests/support/live_port_guard.py`（核对新表述是否准确）
5. 实跑存档 `_bmad-output/审查/evidence-t-edges/edges-r5-allgates-20260914T231922.txt`（三门 3 passed，末行 pytest 真 rc）

## ② L3 的处置（按你 round-4 给的口径逐条落）

1. 「注入失效 ⇒ 连接会**真的建立**并真写现网」→ 已改为你给的表述：
   「**默认豁免模式下，W4 只记录、不阻止连接尝试；注入失效可能导致真实客户端连接并
   写入 7691**」，并显式写明是「可能」不是「必然」（连接 / 认证 / 写入本身也可能失败），
   以及 `W4_GUARD_NO_EXEMPT=1` 时默认 advisory 结论不适用。
2. 补了你要的两点限定：**发请求前的前置身份检查**才是阻止手段，请求后的
   `stub.calls` 与 sentinel 是**事后证明**；零账的读法是「**账本计入的、受其覆盖的
   连接尝试为零**」，且 W4 自证探针跳过记账，因此不等于整进程零网络。
3. `_test_uri_port_is_allowed` docstring 里那句「该 socket 层门是**第二道防线**」
   （你指出它与新说明矛盾）已**撤回**，改为写明：本文件占 `integration` marker 与
   路径前缀、落在豁免面内，那道门本来就不拦。

## ③ 请回答

1. L3 现在可以关闭吗？若否，还差什么（请给可直接采用的表述）。
2. `caf8180e..7c63c5eb` 是否确实只有 docstring、无运行代码变动？
3. 绑定 `7c63c5eb` 的终审：BLOCKER / HIGH / MEDIUM / LOW 各几条、分别是什么？
   H1 请继续按「缺陷成立但超出本卡改动面」标注（车道不自判通过，交主 session 按 D-15 裁定）。

## ④ 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级列出，每条给 `file:line` + 一句话问题 +
一句话说明在什么条件下会显现。没有问题的级别请显式写「无」。

## ⑤ 边界

- **只读**：不要修改、创建、删除任何文件。
- **不连库**：不要连接 7691 / 7687；真库面只涉及 7692，你无需实际连接。
- **不评这两项**：`_write_lancedb` 里三处 `# pyright: ignore[reportAttributeAccessIssue]`；
  「生产是否应默认真连 Neo4j」这个产品裁定（已登记移交）。
- 请只基于 ① 列出的最小读取面作判断；若需要读别的文件，请写明需要哪一份、为什么。
