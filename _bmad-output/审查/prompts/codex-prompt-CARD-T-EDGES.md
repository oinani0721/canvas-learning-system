# 独立复核请求 — CARD-T-EDGES（BATCH-2026-09-11-第十四批 · 车道 T5-B）

## ① 背景 + 最小读取面（只读，不要改任何文件）

仓库树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs`

被改的生产缺陷：`backend/app/api/v1/endpoints/edges.py` 的 `_write_neo4j_triplet` 原先调
`neo4j.execute_query(query, {…位置 dict…})`，而 `Neo4jClient` 上**没有** `execute_query`，
只有 `run_query(self, query: str, **params) -> List[Dict[str, Any]]`。于是每次调用抛
`AttributeError`；该函数的 `except` 元组原为
`(RuntimeError, ConnectionError, asyncio.TimeoutError, OSError)`，不含 `AttributeError`，
异常经 handler 里无 `return_exceptions=True` 的 `asyncio.gather` 与无 try 的 handler 上抛，
FastAPI 兜成 **500**——连 LanceDB 侧已经写成功的那一半也一并丢失，而不是按 Story 4.4 AC-4
记成半成功 **207**。

本卡改动 = 调用改 `run_query(query, **params)`（位置 dict 同步展开）+ 删该行多余的
`# pyright: ignore[reportAttributeAccessIssue]` + `except` 元组补 `AttributeError` + 新增
两道行为门。

**最小读取面（就这四项，不必读别的）**：

1. `git --no-pager diff --no-color 9b30179a c9c73f57 -- . ':(exclude)_bmad-output'`
   （`9b30179a` = 前一卡末 commit，`c9c73f57` = 本卡唯一代码 commit，也是当前 HEAD）
2. `backend/app/api/v1/endpoints/edges.py` 的 **:44-147**（`_write_neo4j_triplet`）与
   **:289-363**（handler `record_edge_rationale`）
3. `backend/app/clients/neo4j_client.py` 的 **:536-560**（`run_query` 签名与分发）
4. `backend/tests/integration/test_edges_dual_write_neo4j_t5b.py` 全文（381 行）

绑定 SHA：审查对象 = `c9c73f57`（本卡唯一代码 commit；其前一个 commit `9b30179a` 是同车道
上一张卡 T5-A 的末 commit）。

## ② 作者自述，请独立核对（不要采信下列任何一条，请自己看代码判断）

1. `run_query(query, **params)` 的 `**params` 展开与原来那个位置 dict 的键名**逐一对应**、
   一个不多一个不少（14 个键），且 `group_id` 仍经 `to_physical_group_id()` 物理化。
2. `except` 元组**只新增了 `AttributeError` 一类**，没有泛化成 `Exception`，原有四类语义未变。
3. 两道门都**没有** mock 被测函数 `_write_neo4j_triplet` 本身——只注入它的依赖
   （`get_neo4j_client` / `_write_lancedb`）。既有 `backend/tests/unit/test_edge_rationale_fallback.py`
   有 9 处整体 patch 掉 `_write_neo4j_triplet`，那使本缺陷对既有套件不可见；本卡不改那个文件。
4. 降级门的 `get_neo4j_client` 打桩落在**源模块** `app.clients.neo4j_client`，不是
   `app.api.v1.endpoints.edges`——后者是函数体内局部 import，edges 模块上无此属性。
5. **注入锚成立**：`stub.calls` 在发请求前断言为 0、发请求后断言 ≥1；且 207 响应体的
   `graphiti_status.error` 含本门独有 sentinel `T5B-STUB-SENTINEL`。
   请特别核对：作者主张「改前 500」对「stub 是否注入」**不可分辨**（真 `get_neo4j_client()`
   恒返 `Neo4jClient`、`neo4j is None` 是死守卫，未注入时真客户端同样没有 `execute_query`，
   照样 500；改后未注入时真客户端连 `.env` 的 7691 会被测试门拦下抛 `RuntimeError`，而
   `RuntimeError` 本就在 except 元组里，照样 207），因此「改前 500 / 改后 207」都不能单独
   作为注入证据。请核对本门确实**没有**把它当注入证据。
6. 两道门**都没有任何一跑在打桩失效的情况下真连 7691/7687 现网**；真库门只连 7692 测试容器，
   并在发写之前过三条前置锚（源模块属性已被替换 / client 的 uri 含 `:7692` / client 不在
   JSON fallback 模式），任一不成立即 `pytest.fail` 立即停。
7. 降级门「改前 500 / 改后 207」、真库门「7692 真写入并查回」均已实跑；`:112` 那处
   `reportAttributeAccessIssue` ignore 已删且 `pyright app` 仍为 `0 errors, 81 warnings`。

## ③ 请按重要性排序回答的问题

- **⓪（最想听你的判断）** 把 `AttributeError` 加进 `except` 元组，是否会**遮住**本该暴露的
  真 bug——例如参数名拼错、模型字段改名导致的 `AttributeError` 也被记成「半成功」而不是报错？
  这个权衡在本处是否站得住？如果不站得住，你建议怎么收窄（例如只在特定条件下降级）？
- **①** `run_query` 在真 7692 上失败（连接断开 / 超时 / 重试耗尽）时，是否仍走该 `except`
  记 `WriteStatus(success=False)`，而不是上抛？请对照 `neo4j_client.py:536-560` 的异常类型判断。
- **②** 降级门用裸 `FastAPI()` + `TestClient(raise_server_exceptions=False)`，它覆盖的是否**就是**
  线上 handler 的那条 500 路径（与真实的、无 `return_exceptions=True` 的 `asyncio.gather` 上抛同构）？
  有没有哪一点使它与线上形态不等价、从而变成一条门未覆盖的路径？
- **③** 真库门的 per-test uuid 隔离与 `finally` 清理，是否可能污染共享的 7692 容器
  （例如断言失败提前返回、清理本身失败、并发跑同一文件）？
- **④** `backend/openapi.json` 是否真未变（本卡只读 handler、未动 `response_model` / 路由 /
  `responses` 声明）？
- **⑤** 删掉 `:112` 那条 ignore 之后，有没有新的 pyright 诊断被放出来而作者没注意到？

## ④ 输出格式

请按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级列出问题，每条给出：
- `file:line`
- 一句话说明问题是什么
- 一句话说明在什么条件下会显现（走哪条路径、什么输入形态会让它出现）

没有问题的级别请显式写「无」。

## ⑤ 边界

- **只读**：不要修改、创建、删除任何文件。
- **不连库**：不要连接 7691 / 7687（现网 Neo4j）；真库面只涉及 7692 测试容器，且你无需实际连接。
- **不评这两项**：`_write_lancedb` 里 `:199 / :217 / :225` 三处
  `# pyright: ignore[reportAttributeAccessIssue]`（那是另一张卡的死分支面，本卡禁碰）；
  以及「生产是否应默认真连 Neo4j」这个产品裁定（不在本卡范围，已登记移交）。
- 请只基于 ① 列出的最小读取面作判断；若你认为需要读别的文件才能下结论，请写明需要哪一份、
  为什么，而不是替作者假定。
