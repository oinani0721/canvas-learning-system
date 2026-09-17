# 独立复核请求 round-2 — CARD-T-EDGES（BATCH-2026-09-11-第十四批 · 车道 T5-B）

## ① 背景 + 最小读取面（只读，不要改任何文件）

仓库树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs`

**round-1 你提了 1 HIGH / 1 MEDIUM / 1 LOW，作者已处置，本轮请复核处置本身 + 重新整体判断。**

被改的生产缺陷：`backend/app/api/v1/endpoints/edges.py` 的 `_write_neo4j_triplet` 原先调
`neo4j.execute_query(query, {…位置 dict…})`，而 `Neo4jClient` 上**没有** `execute_query`，
只有 `run_query(self, query: str, **params)`。每次调用抛 `AttributeError`；该函数 `except`
元组原不含 `AttributeError`，异常经无 `return_exceptions=True` 的 `asyncio.gather` 与无 try
的 handler 上抛，FastAPI 兜成 **500**——LanceDB 侧已写成功的一半也一并丢失，而不是按
Story 4.4 AC-4 记成半成功 **207**。

**最小读取面（就这六项）**：

1. `git --no-pager diff --no-color 9b30179a 9764cceb -- . ':(exclude)_bmad-output'`
   （`9b30179a` = 前一卡末 commit；`9764cceb` = 本卡第二个也是最后一个代码 commit = 当前 HEAD；
   中间的 `c9c73f57` 是 round-1 审的那版）
2. `git --no-pager diff --no-color c9c73f57 9764cceb -- . ':(exclude)_bmad-output'`
   （**只看 round-1 之后的整改**）
3. `backend/app/api/v1/endpoints/edges.py` 的 **:44-154**（`_write_neo4j_triplet`）与
   **:296-370**（handler `record_edge_rationale`）
4. `backend/app/clients/neo4j_client.py` 的 **:57**（`RETRYABLE_EXCEPTIONS` 定义）、
   **:351-433**（`initialize` / `_initialize_neo4j_driver` / `_fallback_to_json`）、
   **:536-641**（`run_query` 全函数 + `_run_query_neo4j` 全函数含重试与异常转换）
   —— round-1 你指出 `:536-560` 截断导致问题 ① 无法定论，本轮已给全。
5. `backend/tests/integration/test_edges_dual_write_neo4j_t5b.py` 全文（454 行）
6. 实跑存档目录 `_bmad-output/审查/evidence-t-edges/`（round-1 你指出「实跑声明未验证」，
   本轮给出落盘证据供你核对；每份末行是 `rc=`）：
   - `pyright-final-20260914T224710.txt`（`0 errors, 81 warnings`，cwd=backend 绝对路径 pyright）
   - `edges-207-red-20260914T223158.txt`（改前：降级门 FAILED，红在 `status_code == 207` 实得 500）
   - `edges-7692-red-20260914T223245.txt`（改前：真库门 FAILED，`AttributeError`）
   - `edges-r2-allgates-20260914T225401.txt`（改后：三门 3 passed）
   - `negctl-both-r2-20260914T225441.txt`（两条负控 + 跑前跑后 `shasum -a 256` 逐字相同）
   - `whitelist-vs-blacklist-20260914T225429.txt`（驱动层实测：neo4j 6.1.0 把
     `bolt://localhost` 与 `bolt://localhost:0` 都归一成 `localhost:7687`）
   - `unit-close-20260914T223701.txt` + `base.nodeids` / `close.nodeids`
     （`tests/unit` 对 64 条基线 diff 为空）
   - `edges-7692-red-20260914T223216.txt` 是**已作废**存档（文件首部自述作废理由：
     那次命令多接了一条 grep 管道，末行 `rc=` 取到的是 grep 的退出码而非 pytest 的）。
     不要把它当依据，列在这里只是为了不让你以为它被藏起来了。

## ② round-1 三条的处置，请独立核对（不要采信下列自述）

- **HIGH（端口白名单 + 惰性探针）**：`_test_uri_port_is_allowed()` 改为 `urlsplit(uri).port`
  必须**恰好等于 7692**，解析失败/端口缺省一律拒绝；模块级 `_REAL_DB_REACHABLE` 与
  `@pytest.mark.skipif` 已删，skip 判定挪进真库门函数体（降级门那一跑零网络动作）；前置注入锚
  与 verifier 断言也从 `":7692" in uri` 子串判定改成同一条解析白名单；新增门
  `test_test_uri_port_whitelist_rejects_everything_but_7692`（纯逻辑零网络）钉死
  省略端口 / `:0` / 主机名含 7692 但端口是现网 三类必须被拒。
  **请核对**：这条白名单还有没有漏面（例如 IPv6 括号形态、`neo4j+s://`、带 user-info、
  大小写、尾随空白、非 ASCII 数字），以及惰性化之后是否仍有别的收集期动作会建连。
- **MEDIUM（`AttributeError` 覆盖过宽 + 注释不实）**：注释已改为如实声明覆盖边界——明写
  签名错配抛 `TypeError` **不在**元组内仍会上抛，且明写本 `except` 覆盖整个函数体、params
  组装期的 `AttributeError` 也会被记成写失败；**收窄 try 范围未做**，理由是那属行为变更、
  超出本卡允许改动面（本卡只许改调用形态、ignore、except 元组、注释四项），已登记移交。
  **请判断**：这个「注释如实 + 登记移交」的处置在本卡范围内是否可接受；若你认为必须在本卡
  收窄，请说明理由与你建议的最小收窄形态。
- **LOW（cleanup 串行）**：两个客户端的 `cleanup()` 已改嵌套 `finally`。

## ③ 请按重要性排序回答的问题

- **①（round-1 未能定论，本轮给全了读取面）** `run_query` 在真 7692 上失败（连接断开 /
  超时 / 重试耗尽 / 驱动内部转换后的异常类型）时，是否仍落在 `_write_neo4j_triplet` 的
  `except (RuntimeError, ConnectionError, asyncio.TimeoutError, OSError, AttributeError)`
  里记 `WriteStatus(success=False)`？有哪些异常类型会漏出这个元组从而让端点回到 500？
  请对照 `:57` 的 `RETRYABLE_EXCEPTIONS`、`:536-641` 的重试与 `_fallback_to_json` 分支作答。
- **②** 整改后的端口白名单与惰性探针，是否真的让「只选降级门」的那一跑零网络动作？
  有没有别的路径（import 期、fixture、conftest）仍会在该跑中建连？
- **③** 真库门的 per-test uuid 隔离与嵌套 `finally` 清理，在哪些情形下仍会给共享 7692
  留下数据？
- **④** `backend/openapi.json` 在 `9b30179a..9764cceb` 是否真未变？
- **⑤（round-1 未能定论）** 对照第 6 项的 pyright 存档，`:112` 那条 ignore 删除后是否确实
  没有新诊断被放出来、汇总仍是 `0 errors, 81 warnings`？
- **⑥** 参数 14 个键在整改后是否仍与原位置 dict 逐一对应、`group_id` 仍经
  `to_physical_group_id()`；`except` 元组是否仍只多了 `AttributeError` 一类。

## ④ 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级列出，每条给：
- `file:line`
- 一句话说明问题是什么
- 一句话说明在什么条件下会显现（走哪条路径、什么输入形态会让它出现）

没有问题的级别请显式写「无」。若 round-1 的某条你认为处置不充分，请重新按级别列出。

## ⑤ 边界

- **只读**：不要修改、创建、删除任何文件。
- **不连库**：不要连接 7691 / 7687（现网 Neo4j）；真库面只涉及 7692 测试容器，你无需实际连接。
- **不评这两项**：`_write_lancedb` 里三处 `# pyright: ignore[reportAttributeAccessIssue]`
  （另一张卡的死分支面，本卡禁碰）；以及「生产是否应默认真连 Neo4j」这个产品裁定（已登记移交）。
- 请只基于 ① 列出的最小读取面作判断；若需要读别的文件才能下结论，请写明需要哪一份、为什么。
