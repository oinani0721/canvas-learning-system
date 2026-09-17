# 独立复核请求 round-9（终审） — CARD-T-EDGES（BATCH-2026-09-11-第十四批 · 车道 T5-B）

## ① 背景 + 最小读取面（只读，不要改任何文件）

仓库树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs`

**用户已裁定放开 D-15 的 5 轮上限。当前 HEAD = `134cf5a4`**（上一轮你审 `34935f62`）。

round-8 你给出 **本卡 BLOCKER 0 / HIGH 0 / MEDIUM 0 / LOW 3**（两条 HIGH 明确归为
「超出本卡改动面、非本轮新增」的独立卡外缺陷），并对三条 LOW 给了可直接采用的表述。
**本轮把三条全部按你给的表述改掉**，只动了测试文件（`edges.py` diff 为空）。

**最小读取面**：

1. `git --no-pager diff --no-color 34935f62 134cf5a4 -- . ':(exclude)_bmad-output'`
   （**本轮全部改动**）
2. `backend/tests/integration/test_edges_dual_write_neo4j_t5b.py` 全文（17 格）
3. `backend/app/api/v1/endpoints/edges.py` 的 `:42-95`（常量与说明）、`:99-240`
   （`_write_neo4j_triplet`）—— 本轮未改，供核对措辞一致性
4. 实跑存档 `_bmad-output/审查/evidence-t-edges/`（每份末行 `rc=`）：
   - `edges-r9-allgates-20260916T003901.txt`（17 格全绿）
   - `negctl-r8-cleanup-20260915T235206.txt`（NC-H：去掉 `RETURN count(er)` ⇒ 清理断言红；还原后 7692 残留 0）
   - `unit-final-r8-20260916T001124.txt`（`tests/unit` 目录级绑 `34935f62`，对 64 基线 diff 空）

## ② round-8 三条 LOW 的处置（均按你给的表述）

- **r8-LOW-1** — 门 1d 的**两条失败消息**（身份判据与状态码断言）仍把处置策略写成根因
  结论。已改为「**按当前处置策略应保留 500；异常类型本身不唯一确定根因**」。
  （门 docstring 上一轮已改对，是失败消息漏了。）
- **r8-LOW-2** — 清理断言的失败消息写「清理是空转」超出证明范围。已改为
  「**清理未取得确认，提交结果未知**；verifier 可能已转入 JSON fallback，
  目标 group 的节点可能滞留在共享 7692」。
  另按你的建议补了**回执形态断言**：`len(deleted_rows) == 1 and deleted_rows[0]["deleted"] >= 0`。
  ⛔ 按你的提醒**刻意不钉 `deleted == 1`** —— `finally` 也覆盖「写本身没成功 ⇒ 合法零删除」
  的路径，硬钉 1 会把正常情形判红；这一点已写进代码注释。
- **r8-LOW-3** — 漂移的行号引用（`edges.py:63` / `:66-70` / 「上面 `:435` 的 skip」）
  已改用**符号名与条件表达式**定位。
  ⚠️ 保留了 `neo4j_client.py:536` —— 那是**跨文件**引用、不随本卡改动漂移，
  且已复核它仍指向 `def run_query`。如果你认为跨文件行号也该去掉，请说明。

## ③ 请回答

1. 三条 LOW 是否都可以关闭？若否，哪条、还差什么。
2. 新增的回执形态断言（单行 + `deleted >= 0`）是否恰当？有没有引入恒真？
3. 17 格里还有没有**不可证伪**的断言，或**覆盖说明 / 失败消息超出实际证明范围**的地方？
4. 本轮 diff 有没有引入回归？
5. **绑定 `134cf5a4` 的终审**：本卡的 BLOCKER / HIGH / MEDIUM / LOW 各几条、分别是什么？
   请像 round-8 那样，把「本卡计数」与「连同已登记的卡外缺陷」分开列。

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
