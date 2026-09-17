# 独立复核请求 round-10（终审） — CARD-T-EDGES（BATCH-2026-09-11-第十四批 · 车道 T5-B）

## ① 背景 + 最小读取面（只读，不要改任何文件）

仓库树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs`

**用户已裁定放开 D-15 的 5 轮上限。当前 HEAD = `65a5e642`**（上一轮你审 `134cf5a4`）。

round-9 你给出 **本卡 0 / 0 / 0 / 1**（连同两条已登记卡外缺陷则 0/2/0/1），
并对那一条 LOW 给了收口表述，另提了两条附带观察。**三者本轮全部采纳**。
只动了测试文件（`edges.py` diff 为空）。

**最小读取面**：

1. `git --no-pager diff --no-color 134cf5a4 65a5e642 -- . ':(exclude)_bmad-output'`
   （**本轮全部改动**）
2. `backend/tests/integration/test_edges_dual_write_neo4j_t5b.py` 全文（17 格）
3. `backend/app/api/v1/endpoints/edges.py` 的 `:42-95` 与 `:99-240`（本轮未改，供核对措辞一致性）
4. 实跑存档 `_bmad-output/审查/evidence-t-edges/allgates-selfbound-20260916T010656.txt`
   —— **按你 round-9 的存档边界意见新建的「自绑」存档**：首部打印 HEAD、
   非 `_bmad-output` 的工作树改动数、两个代码文件的**工作树 sha256** 与
   `git show HEAD:<path>` 的 sha256 并逐串标注是否一致，然后才是 17 格与 pyright。

## ② round-9 三项的处置

- **r9-LOW-1（三处失败消息把可能原因写成确定结论）— 已按你给的口径整改**：
  - 降级门注入锚：「继续发请求**会**真连 7691 现网」→「继续发请求**可能**连上并写入
    7691 现网（也可能连接/认证/写入本身失败）」；
  - 真库门前置锚：同款改法；
  - 207 断言：「500 **说明** Neo4j 侧的 AttributeError 仍在穿透」→「500 **可能**是…，
    但**任意未捕获异常都会给出 500** —— 需核对异常来源」。
- **附带观察①（回执断言不检查整数类型，`True` / `0.5` 也放行）— 已采纳**：
  改为显式 `isinstance(_deleted, int) and not isinstance(_deleted, bool)` 且 `>= 0`，
  并在注释里写明「Python 里 `True` 是 `int` 子类」。
  ⛔ 仍**不**钉 `deleted == 1` —— 按你 round-8 的提醒，`finally` 也覆盖
  「写本身没成功 ⇒ 合法零删除」的路径。
- **附带观察②（存档不能自绑 SHA）— 已采纳**：见第 4 项。该机制**首跑即抓出**
  「工作树 sha 与 `git show HEAD:` 不一致」（当时整改尚未 commit），commit 后两串一致。

## ③ 请回答

1. r9-LOW-1 是否可以关闭？若否，还差什么。
2. 回执断言改成 `isinstance(int) and not isinstance(bool)` 之后是否恰当？有没有引入恒真？
3. 17 格里还有没有**不可证伪**的断言，或**覆盖说明 / 失败消息超出实际证明范围**的地方？
4. 本轮 diff 有没有引入回归？
5. 自绑存档的形态是否满足你 round-9 提的「日志应能独立绑定本次 SHA」？还差什么？
6. **绑定 `65a5e642` 的终审**：本卡的 BLOCKER / HIGH / MEDIUM / LOW 各几条、分别是什么？
   请像 round-8/9 那样把「本卡计数」与「连同已登记卡外缺陷」分开列。

## ④ 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级列出，每条给 `file:line` + 一句话问题 +
一句话说明在什么条件下会显现。没有问题的级别请显式写「无」。
若某条是「缺陷成立但超出本卡改动面」，请明确标注并给建议级别。

## ⑤ 边界

- **只读**：不要修改、创建、删除任何文件。
- **不连库**：不要连接 7691 / 7687；真库面只涉及 7692，你无需实际连接。
- **不评**：「生产是否应默认真连 Neo4j」产品裁定；`_write_lancedb` 与
  `Neo4jClient.initialize()` 的**修法**（两者都已登记移交，建议第十五批立卡）。
- 请只基于 ① 列出的最小读取面作判断；若需要读别的文件，请写明需要哪一份、为什么。
