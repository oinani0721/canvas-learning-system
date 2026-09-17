# 独立复核请求 round-8 — CARD-T-EDGES（BATCH-2026-09-11-第十四批 · 车道 T5-B）

## ① 背景 + 最小读取面（只读，不要改任何文件）

仓库树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs`

**用户已裁定放开 D-15 的 5 轮上限。当前 HEAD = `34935f62`**（上一轮你审 `a6f68241`）。

round-7 你给出 BLOCKER 0 / HIGH 1（卡外既有）/ MEDIUM 0 / LOW 4，
并对每条 LOW 给了可直接采用的表述。**本轮把四条 LOW 全部按你给的表述改掉**，
另外自查补了一条你没提到的缺陷。

**最小读取面**：

1. `git --no-pager diff --no-color a6f68241 34935f62 -- . ':(exclude)_bmad-output'`
   （**本轮全部改动**；除清理语句那一处外全是注释 / docstring / 断言消息）
2. `backend/app/api/v1/endpoints/edges.py`：`:42-95`（常量与说明）、`:99-240`（`_write_neo4j_triplet`）
3. `backend/tests/integration/test_edges_dual_write_neo4j_t5b.py` 全文（17 格）
4. 实跑存档 `_bmad-output/审查/evidence-t-edges/`（每份末行 `rc=`）：
   - `negctl-r8-cleanup-20260915T235206.txt`（**本轮新负控 NC-H** + 跑前跑后 `shasum` + 7692 残留复核）
   - `negctl-r8-20260915T234554.txt`（NC-A / NC-C / NC-E / NC-F 回归复核）
   - `edges-r8-allgates-20260915T234321.txt`（17 格全绿）
   - `api-dir-20260915T183949.txt`（`tests/api` 目录级 268 passed）
   - `edges-consumers-20260915T183926.txt`（edges 的其余三个消费方 66 passed）
   - `write-confirm-rowcount-probe-20260915T182121.txt`（7692 实测行数前提）
   - `lancedb-never-writes-probe-20260915T183820.txt`（`_write_lancedb` 从不真写）

## ② round-7 四条 LOW 的处置（均按你给的表述）

- **R7-L1** — `edges.py` 与测试里四处「未确认 = 未落盘」的残留表述已统一为
  「返回空行表示**未取得写入确认，提交结果未知**；不能据此断言没有落盘」。
  自检后仓内只剩**明说「不这么写」的元引用**（两处，都带 r7-L1 标注）。
- **R7-L2** — 「连接池耗尽 = 我方 session 泄漏」「它们不是对端的错」已改为
  「这是 **207/500 的处置策略**，异常类型本身不唯一确定根因」，并点明
  `ConnectionAcquisitionTimeoutError` 也可能只是正常慢查询占满连接池、
  是最值得重新裁定的一类。生产常量说明与测试 docstring 两侧同步。
- **R7-L3** — 两处覆盖说明已收窄：
  1d2 改为「验证 **getter 阶段**的 `AttributeError` 不被降级，防止 `try` 扩大到覆盖
  getter」，并明写「**不等于**锁住 `try` 恰好只包一行 —— 只把 params 组装包进 try 时
  本门仍绿」；RETURN 锚改为「**当真库门被 skip 时**，原有零 DB 门无法发现 RETURN 被
  删除」，并声明它只证明该片段**存在于发出的 query 文本里**、不证明它是有效未被注释
  的 Cypher 子句，执行语义由真库门验。
- **R7-L4** — 已删掉真库门里那条冗余恒真断言，保留 URI 相等断言。
- **H1（卡外）** — 已按你给的表述限定：「`run_query` 原样抛出、且不被本元组捕获的
  异常才会上抛成 500；**初始化阶段被 client 吞掉的异常不受该保证覆盖**」。

## ③ 本轮自查新增的一条（你没提到，请一并复核）

**真库门的清理是静默空转且不可分辨。** 7692 实测：裸
`MATCH … DETACH DELETE er` 返回 `[]`；而「verifier 中途转 JSON fallback ⇒ 清理落进
`_run_query_json_fallback` 的 `else` 分支只 `logger.warning` 就返回 `[]`」产出**完全
一样** ⇒ 节点会永久滞留共享 7692 而没有任何信号。
已改成 `… DETACH DELETE er RETURN count(er) AS deleted` 并断言回执非空
（实测带 RETURN 返 `[{'deleted': 1}]`）。
**负控 NC-H**：去掉 `RETURN count(er)` ⇒ 真库门红在「清理语句没有回执」那条断言；
还原后 shasum 逐字相同、7692 全库 `:EdgeRationale` = 0。

## ④ 请回答

1. R7-L1 / L2 / L3 / L4 是否都可以关闭？若否，哪条、还差什么。
2. H1 的限定措辞是否已达到你 round-7 给的那条表述的要求？
3. 新加的清理回执断言是否真的可证伪、且锁的是它声称锁的那件事？有没有更好的写法？
4. 17 格里还有没有**不可证伪**的断言（恒真 / 恒假）、或**覆盖说明超过实际检测范围**的地方？
5. 本轮 diff 有没有引入回归？（除清理语句外应全是注释 / docstring / 断言消息）
6. 绑定 `34935f62` 的终审：BLOCKER / HIGH / MEDIUM / LOW 各几条、分别是什么？

## ⑤ 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级列出，每条给 `file:line` + 一句话问题 +
一句话说明在什么条件下会显现。没有问题的级别请显式写「无」。
若某条是「缺陷成立但超出本卡改动面」，请明确标注并给建议级别。

## ⑥ 边界

- **只读**：不要修改、创建、删除任何文件。
- **不连库**：不要连接 7691 / 7687；真库面只涉及 7692，你无需实际连接。
- **不评**：「生产是否应默认真连 Neo4j」产品裁定；`_write_lancedb` 与
  `Neo4jClient.initialize()` 的**修法**（两者都已登记移交；但它们导致的**不实陈述**
  在本卡面内，欢迎指出）。
- 请只基于 ① 列出的最小读取面作判断；若需要读别的文件，请写明需要哪一份、为什么。
