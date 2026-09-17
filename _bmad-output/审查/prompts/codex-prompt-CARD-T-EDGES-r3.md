# 独立复核请求 round-3 — CARD-T-EDGES（BATCH-2026-09-11-第十四批 · 车道 T5-B）

## ① 背景 + 最小读取面（只读，不要改任何文件）

仓库树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs`

round-2 你给出 BLOCKER 0 / HIGH 2 / MEDIUM 0 / LOW 3。本轮请复核处置并重新整体判断。
**当前 HEAD = `c2e3d533`**（本卡第三个也是最后一个代码 commit）。

**最小读取面**：

1. `git --no-pager diff --no-color 9b30179a c2e3d533 -- . ':(exclude)_bmad-output'`
   （`9b30179a` = 前一卡末 commit；本卡代码 commit 链 `c9c73f57`(r1 审) → `9764cceb`(r2 审)
   → `c2e3d533`(本轮)）
2. `git --no-pager diff --no-color 9764cceb c2e3d533 -- . ':(exclude)_bmad-output'`
   （**只看 round-2 之后的整改**）
3. `backend/app/api/v1/endpoints/edges.py` 的 `_write_neo4j_triplet` 与
   handler `record_edge_rationale` 两个函数全文
4. `backend/tests/integration/test_edges_dual_write_neo4j_t5b.py` 全文
5. `backend/app/clients/neo4j_client.py` 的 `:57`、`:351-433`、`:536-641`
6. **为闭合 round-2 问题 ②「整次 pytest 零网络尚不能确认」新加入读取面**：
   `backend/pytest.ini`、`backend/tests/conftest.py`、`backend/tests/integration/conftest.py`、
   `backend/tests/support/live_port_guard.py`
7. 实跑存档 `_bmad-output/审查/evidence-t-edges/`（每份末行 `rc=`），本轮新增/更新：
   - `edges-r3-allgates-20260914T230444.txt`（三门 3 passed，**末行带 pytest 真 rc**，闭 r2 LOW-1）
   - `pyright-diag-before-after-20260914T230427.txt`（`pyright app --outputjson` 逐项对照：
     `edges.py` 改前 0 条 / 改后 0 条 / 新增 0 条，两态汇总均 `0 errors, 81 warnings`，闭 r2 LOW-2）
   - `neo4j-exception-mro-20260914T230328.txt`（驱动 6.1.0 七类异常 MRO 实测，HIGH-1 依据）
   - `whitelist-vs-blacklist-20260914T225429.txt`（驱动把 `bolt://localhost` 与
     `bolt://localhost:0` 都归一成 `localhost:7687`）
   - `negctl-both-r2-20260914T225441.txt`（两条负控 + 跑前跑后 `shasum -a 256` 逐字相同）
   - `unit-close-20260914T223701.txt` + `base.nodeids` / `close.nodeids`
   - `edges-7692-red-20260914T223216.txt` 是**已作废**存档（首部自述理由：那次命令多接一条
     grep 管道，末行 rc 取到的是 grep 的退出码）。不要当依据。

## ② round-2 两条 HIGH / 三条 LOW 的处置

### HIGH-2（端口白名单挡不住路由族）— **已整改**

`ALLOWED_TEST_SCHEMES = {"bolt", "bolt+s", "bolt+ssc"}`，`_test_uri_port_is_allowed()` 先卡
scheme（小写比较）再卡端口；路由族 `neo4j://` / `neo4j+s://` / `neo4j+ssc://` 整族拒绝。
门 1b 补了 4 条路由族必拒断言 + IPv6 括号 / scheme 大小写 / 尾随空格三条边界。
**请核对**：这条 scheme + 端口双白名单还有没有漏面；以及连同第 6 项读取面，
「只选降级门的那一跑」是否真的零网络动作。

### HIGH-1（真实驱动异常仍穿透为 500）— **确认成立，但车道驳回「在本卡修」，不自判通过**

你的判断经实测确认，且比你描述的更重：驱动 6.1.0 实测 MRO（存档
`neo4j-exception-mro-*.txt`）——`Neo4jError` / `ClientError` / `AuthError` /
`TransientError` / `DriverError` / `ServiceUnavailable` / `SessionExpired` **七类全部**
继承 `GqlError -> Exception`，与 `RuntimeError` / `ConnectionError` / `OSError` 无继承关系，
**全部不在** except 元组内。即「Neo4j 连不上」（`ServiceUnavailable`）也会回到 500。

车道不在本卡修，理由是**本卡的改动面由卡文硬性框死**，原文两处：

> （卡文 一·(d)④）**:140 except 元组补 `AttributeError`**：
> `except (RuntimeError, ConnectionError, asyncio.TimeoutError, OSError, AttributeError) as e:`

> （卡文 三·禁放宽判据）……`except` 元组不得把 `Exception` 泛化吞掉
> （**只加 `AttributeError` 一个类型**，保留其余四类的原义）。

往元组里加第六类（`Neo4jError` / `DriverError` 族）= 违反上面第二条。该缺口在本卡之前
就存在（改前每次调用都死在 `AttributeError`，根本走不到驱动异常），不是本卡引入。
车道的处置是：在 `_write_neo4j_triplet` 注释与测试文件模块 docstring 里**如实声明
「本卡未覆盖真实驱动失败」**，并登记移交由主 session 裁定是否另立卡收口。

**请你判断（这是本轮最重要的一问）**：在「改动面被卡文框死为四项、且明令不得给 except
元组加第二个类型」的前提下，上述「注释如实声明 + 登记移交」是否是本卡范围内可接受的处置？
如果你认为必须在本卡内修，请说明为什么它压过卡文的硬边界，以及你建议的最小改法。
（你在 round-2 对同族的 MEDIUM 已给过「本卡限定改动面内可接受注释整改并移交」的判断，
本条与它的差别只在严重度，请说明两者是否应同口径处理。）

### LOW 三条 — 全部已处置

- **LOW-1**：三门存档改为不经附加管道落盘，末行是 pytest 真 rc（见第 7 项第一份）。
- **LOW-2**：新增 `--outputjson` 逐项对照存档（第 7 项第二份），`edges.py` 诊断改前 0 条、
  改后 0 条、新增 0 条，两态汇总均 `0 errors, 81 warnings`；命令、cwd、两态 `shasum` 均在档内。
- **LOW-3**：门 1b 注释已更正——旧黑名单放行的是**两种**（省略端口、`:0`），
  `bolt://host-7692.example:7687` 含字面 `:7687` 黑名单也会拒；该条断言防的是子串式端口判定。

## ③ 请按重要性排序回答的问题

- **①** HIGH-1 的范围判断（见上，本轮最重要）。
- **②** HIGH-2 的 scheme + 端口双白名单是否仍有漏面；结合第 6 项读取面，
  「只选降级门」的那一跑是否零网络动作。
- **③** round-2 问题 ③ 你指出「`finally` 保证尝试不保证删除成功」——车道接受并已写进
  「本卡未证明什么」。除你已列的三种，还有别的会给共享 7692 留数据的情形吗？
- **④** 本轮 diff（`9764cceb..c2e3d533`）有没有引入新问题？特别是 `_test_uri_port_is_allowed`
  的两段 `try/except ValueError` 是否都有意义、`parsed.scheme.lower()` 是否够。
- **⑤** 参数 14 键、`to_physical_group_id`、except 元组只多 `AttributeError` 这三点在本轮
  是否仍成立。

## ④ 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级列出，每条给 `file:line` + 一句话问题 +
一句话说明在什么条件下会显现。没有问题的级别请显式写「无」。
若某条你认为是「缺陷成立但超出本卡改动面」，请**明确标注**，并给出你建议的级别。

## ⑤ 边界

- **只读**：不要修改、创建、删除任何文件。
- **不连库**：不要连接 7691 / 7687；真库面只涉及 7692，你无需实际连接。
- **不评这两项**：`_write_lancedb` 里三处 `# pyright: ignore[reportAttributeAccessIssue]`
  （另一张卡的死分支面）；「生产是否应默认真连 Neo4j」这个产品裁定（已登记移交）。
- 请只基于 ① 列出的最小读取面作判断；若需要读别的文件，请写明需要哪一份、为什么。
