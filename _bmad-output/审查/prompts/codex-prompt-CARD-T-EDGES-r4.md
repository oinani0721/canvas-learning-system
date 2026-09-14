# 独立复核请求 round-4（终审） — CARD-T-EDGES（BATCH-2026-09-11-第十四批 · 车道 T5-B）

## ① 背景 + 最小读取面（只读，不要改任何文件）

仓库树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs`

**当前 HEAD = `caf8180e`**，本卡代码 commit 链：
`c9c73f57`(r1 审) → `9764cceb`(r2 审) → `c2e3d533`(r3 审) → `caf8180e`(本轮，**纯注释 /
docstring**，`edges.py` 非注释行 diff 为空)。

round-3 你给出 BLOCKER 0 / HIGH 1（标注「缺陷成立但超出本卡改动面」）/ LOW 3。
本轮请核对三条 LOW 的处置并给出绑定 `caf8180e` 的终审判断。

**最小读取面**：

1. `git --no-pager diff --no-color c2e3d533 caf8180e -- . ':(exclude)_bmad-output'`
   （**只看 round-3 之后的整改**；应只有注释与 docstring）
2. `git --no-pager diff --no-color 9b30179a caf8180e -- . ':(exclude)_bmad-output'`
   （本卡全量 diff；`9b30179a` = 前一卡末 commit）
3. `backend/app/api/v1/endpoints/edges.py` 的 `_write_neo4j_triplet` 全文
4. `backend/tests/integration/test_edges_dual_write_neo4j_t5b.py` 全文
5. `backend/tests/support/live_port_guard.py` 的 `EXEMPT_MARKERS` / `EXEMPT_PATH_PREFIXES`
   及其周边（核对 L3 的新表述是否准确）
6. 实跑存档 `_bmad-output/审查/evidence-t-edges/`：
   - `edges-r4-allgates-20260914T231348.txt`（三门 3 passed，末行 pytest 真 rc）
   - `pyright-diag-before-after-20260914T230427.txt`（逐项对照，新增 0 条）
   - `neo4j-exception-mro-20260914T230328.txt`
   - `negctl-both-r2-20260914T225441.txt`
   - `unit-close-20260914T223701.txt` + `base.nodeids` / `close.nodeids`

## ② round-3 三条 LOW 的处置

- **L3（W4 表述过强）— 已整改，且方向与你指出的一致：** 本文件同时占 `integration`
  marker 与 `tests/integration/` 路径前缀，落在 `EXEMPT_MARKERS` / `EXEMPT_PATH_PREFIXES`
  内 ⇒ W4 对本文件的用例是 **advisory：只记账不拦**。模块 docstring 里那句
  「未注入时真客户端连 7691 会被 W4 门拦下抛 `RuntimeError`」**本来就是写反的**，
  已改为：打桩失效时到 7691 的连接会**真的建立并真写现网**，故注入锚是唯一防线、
  因而承重；并补注 `blocked=0, advisory=0` 的正确读法（该账本覆盖的 7691/7687 上零次
  连接尝试，不等于整进程零网络）。**请核对这段新表述是否仍有不准确处。**
- **L1（把「不被捕获」推成「必然 500」）— 已整改**：`edges.py` 与测试 docstring 均改为
  「只说明不被本函数捕获；`ServiceUnavailable` / `SessionExpired` / `TransientError`
  先经 `run_query` 的重试与 JSON fallback，最终状态取决于那条链路；**若穿透了客户端
  内部的重试与回退，端点就会 500**，权限 / 约束类 `ClientError` 存在该路径」。
- **L2（两段 `except ValueError` 注释错位）— 已整改**：第一段注明「`urlsplit` 本身失败：
  坏 IPv6 括号、非法 netloc」，第二段注明「读 `.port` 时才抛：非整数或越界」。

## ③ H1 的状态（不请你改判，只请你确认记录无误）

你在 round-3 ① 已裁：「**不要求本卡越界修复**……与 round-2 的 MEDIUM 应采用同一范围
口径：可以接受明确披露并移交，但不能把缺陷记为已关闭」。车道照此办理——H1 保留为
移交项，不自判通过，由主 session 按 D-15 裁定；披露措辞已按你给的最小表述改写。
**请确认**：现在的披露措辞是否达到了你说的那条最小表述要求。

## ④ 请回答

1. 三条 LOW 是否都可以关闭？若否，哪条、为什么。
2. `c2e3d533..caf8180e` 这一段是否确实只有注释 / docstring，没有运行代码变动？
3. 绑定 `caf8180e` 的终审：BLOCKER / HIGH / MEDIUM / LOW 各几条、分别是什么？
   H1 请继续按「缺陷成立但超出本卡改动面」标注。

## ⑤ 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级列出，每条给 `file:line` + 一句话问题 +
一句话说明在什么条件下会显现。没有问题的级别请显式写「无」。

## ⑥ 边界

- **只读**：不要修改、创建、删除任何文件。
- **不连库**：不要连接 7691 / 7687；真库面只涉及 7692，你无需实际连接。
- **不评这两项**：`_write_lancedb` 里三处 `# pyright: ignore[reportAttributeAccessIssue]`；
  「生产是否应默认真连 Neo4j」这个产品裁定（已登记移交）。
- 请只基于 ① 列出的最小读取面作判断；若需要读别的文件，请写明需要哪一份、为什么。
