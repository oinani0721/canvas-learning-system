# 独立复核请求 round-7 — CARD-T-EDGES（BATCH-2026-09-11-第十四批 · 车道 T5-B）

## ① 背景 + 最小读取面（只读，不要改任何文件）

仓库树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs`

**用户已裁定放开 D-15 的 5 轮上限，本卡继续修到干净。**
**当前 HEAD = `a6f68241`**（上一轮你审的是 `8ff37ea5`）。

round-6 你给出 BLOCKER 0 / HIGH 1（H1，标注「超出本卡改动面」）/ MEDIUM 3 / LOW 2。
本轮把 M1/M2/M3/L1/L2 全部处置，并按你对 H1 的建议在本卡内限定了措辞。

**最小读取面**：

1. `git --no-pager diff --no-color 8ff37ea5 a6f68241 -- . ':(exclude)_bmad-output'`
   （**本轮全部改动**）
2. `backend/app/api/v1/endpoints/edges.py`：`:42-89`（`_NEO4J_WRITE_FAILURES` 与说明）、
   `:99-235`（`_write_neo4j_triplet` 全文）
3. `backend/tests/integration/test_edges_dual_write_neo4j_t5b.py` 全文（17 格）
4. `backend/app/clients/neo4j_client.py`：`:57`、`:351-433`、`:536-669`
5. 实跑存档 `_bmad-output/审查/evidence-t-edges/`（每份末行 `rc=`）：
   - `negctl-r7-20260915T183450.txt`（**本轮三条新负控** NC-E / NC-F / NC-G + 跑前跑后 `shasum`）
   - `edges-r7-allgates-20260915T183330.txt`（17 格全绿，末行 pytest 真 rc）
   - `write-confirm-rowcount-probe-20260915T182121.txt`（7692 实测写确认判据的行数前提）
   - `unit-r6-20260915T182216.txt`（`tests/unit` 目录级）+ `base.nodeids` / `close.nodeids`（diff 空）

## ② round-6 逐条处置

- **M2（本卡自造的假门）— 已整改**。你说得对：门 1c 让 stub 抛
  `exc_cls(f"{SENTINEL}: {type_name}")`，类型名是**测试自己塞进消息的**，于是
  「响应含类型名」恒真。现改为**消息只放 sentinel**、断言
  `error.startswith(f"{type_name}:")`——那个前缀只能由生产加上。
  **负控 NC-E**：把生产 `error=f"{type(e).__name__}: {e}"` 改回 `error=str(e)`
  ⇒ 1c 五格全红（存档第 5 项第一份）。
- **M3（没有门锁住窄 try 边界）— 已整改，新增门 1d2**
  `test_取_client_阶段的异常必须穿透成_500_而不是被降级`：让 **getter** 抛
  `AttributeError`（该类型确实在元组里，所以「没被接住」只可能因为它落在 `try` 之外），
  断言 500。**负控 NC-F**：把 getter 用同款 except 包起来（模拟 try 变宽）⇒ 该门红。
- **M1（「返回 0 行 = 没有落盘」过强）— 已整改**：注释与响应串都改成
  「**未取得写入确认，提交结果未知**」，并写明「已提交但拿不到确认」的那条路径。
  保守记 `success=False` 保留（宁可让调用方重试/告警，不可谎报成功），
  幂等重试属 client 侧，已登记移交。
- **H1（initialize 吞掉部署错误）— 按你的建议在本卡内限定措辞**：
  `_NEO4J_WRITE_FAILURES` 的说明新增一条——「部署错误必然 500」**只在驱动已初始化
  之后成立**；首次初始化就撞凭据/配置错的那条路上，异常被 `initialize()` 转成
  fallback、根本到不了元组，最终由写确认兜成 207，端点给出的是「写未确认」而不是
  「部署坏了」的信号。client 侧行为已登记移交。
- **L1 — 已整改**：明写「这是 207/500 的**处置策略**，不是根因分类器」，
  举 `ConnectionAcquisitionTimeoutError`（正常慢查询也会触发）与
  `ServiceUnavailable`（官方说明可源于配置错误）为例，并点名它是最值得重新裁定的一类。
- **L2 — 已整改**：改成如实说「用例清单是**测试独立维护的预期表**，`issubclass`
  检查的是**继承捕获关系**而非成员身份」，并写明这个组合是有意的（动态生成会让
  「删生产类型」连测试一起删掉）以及它的代价（生产新增类型不会自动多一格）。

## ③ 本轮自查新增的一条（请一并复核）

7692 实测（存档第 5 项第三份）：`CREATE … RETURN er.record_id` 返 **1 行**，
**去掉那句 `RETURN` 返 0 行**。⇒ 写确认判据与 Cypher 末尾那句 `RETURN` 绑定，
谁删了它，**每一次成功写入都会被误判成失败**（假红，且原先没有任何门会发现）。
已在降级门补耦合锚，直接断言实际发给客户端的 query 文本含 `RETURN er.record_id`。
**负控 NC-G**：删掉 `RETURN` ⇒ 降级门的耦合锚与真库门同时红。

## ④ 请回答

1. M1/M2/M3/L1/L2 是否都可以关闭？若否，哪条、还差什么（请给可直接采用的表述或改法）。
2. H1 的「本卡内限定措辞 + client 侧移交」是否是本卡范围内可接受的处置？
3. 新门 1d2 与 `RETURN` 耦合锚是否真的可证伪、且锁的是它声称锁的那件事？
4. 17 格里还有没有**不可证伪**的断言（恒真 / 恒假）？
5. 本轮 diff 有没有引入回归？
6. 绑定 `a6f68241` 的终审：BLOCKER / HIGH / MEDIUM / LOW 各几条、分别是什么？

## ⑤ 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级列出，每条给 `file:line` + 一句话问题 +
一句话说明在什么条件下会显现。没有问题的级别请显式写「无」。
若某条是「缺陷成立但超出本卡改动面」，请明确标注并给建议级别。

## ⑥ 边界

- **只读**：不要修改、创建、删除任何文件。
- **不连库**：不要连接 7691 / 7687；真库面只涉及 7692，你无需实际连接。
- **不评**：「生产是否应默认真连 Neo4j」产品裁定；`_write_lancedb` 的**修法**
  （但它导致的**不实陈述**在本卡面内，欢迎指出）。
- 请只基于 ① 列出的最小读取面作判断；若需要读别的文件，请写明需要哪一份、为什么。
