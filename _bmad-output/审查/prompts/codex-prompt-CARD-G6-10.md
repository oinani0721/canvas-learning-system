# CARD-G6-10 独立复核请求（BATCH-2026-09-11-第十四批 / 车道 T4-B）

你是独立审查者。只读，不改任何文件，不连接任何数据库。

---

## ① 背景与最小读取面

主 goal 的刚需之一是「跨 vault 复习进度 Web UI」。这个需求里的**「跨 vault」**要成立，
必须证明两件事：A 库的操作不会改到 B 库的账，且切换库时不串台。

此前只有**数据面**证据（CARD-G2-9：两个 vault 各写各的，三存储互不可见）。本卡补的是
**交互面**，两维：

- **state 文件维**：snooze（今天先不做）/ board-done（做完了）两笔账既不落 Neo4j 也不落
  LanceDB，而是落在 `backups/daily-review.<vault_key>.state.json` 这**一个文件**上。
  它的隔离全靠 `state_path(vault) = BACKUPS / f"daily-review.{_vault_key(vault)}.state.json"`
  这一条规则，而 `_vault_key` 最终只取 vault 目录的 basename。
- **Neo4j group 维**：复习本身的账（LEARNED 边 + scoring Episode）靠 group_id 隔离。

审查基线：`git diff 80d2fbb0d594351d606dd0ec95dfe1969a908cda 974058e59dc7f93695a75e954262a6b80be45c75 -- . ':(exclude)_bmad-output'`

**最小读取面（写死，请只读这些）**：

1. `backend/scripts/g610_dual_vault_interaction_canary.py`（本卡新文件，全文）
2. `backend/tests/integration/test_g610_dual_vault_isolation.py`（本卡新文件，全文）
3. `scripts/daily_review_run.py`：`:45`（BACKUPS）、`:70-78`（`_vault_key`）、
   `:81-110`（`state_path` / `load_state` / `_fresh_state`）、`:235-300`（锁）、`:443-482`（`save_state`）
4. `backend/app/api/v1/endpoints/review_overview.py`：`:2320-2420`（runner 装载）、
   `:2535-2600`（`_write_board_done`）、`:2686-2728`（`_write_board_snooze`）、
   `:2999`/`:3040`（POST 路由 —— 本卡**不**经过它）
5. `backend/app/core/subject_config.py:215-255`（`build_vault_group_id`）
6. `backend/tests/integration/test_cypher_contract_gate.py:47-170`（本卡门文件照抄的结构模板，对照用）
7. `backend/scripts/g29_dual_vault_canary.py:95-130`（同名攻击用例集的定义点，canary 直接 import 它）

---

## ② 作者自述（请独立核对，不要采信）

1. canary 复用的是 **per-vault state 的生产写路径**（`_write_board_snooze` / `_write_board_done`
   两个辅助函数），不起 FastAPI、不发 HTTP、不经 POST 路由。
2. canary 两态**成对**：`--isolated` rc=0、`--share-state` rc=1；两态之间**只差一个变量**
   ——B 库的目录 basename 是否与 A 相同。
3. `--share-state` 的碰撞由生产 `vault_key` 自己算出（两库同 basename），**没有**改写或替换
   被测机制本身（没有 monkeypatch `_vault_key`）。
4. B 库不变的判据是 **sha256 逐字节**（state 文件）+ 目录树内容指纹，不是「文件还在」之类的弱判据。
5. canary 的**全部**落盘路径在任何写之前都被 `_assert_write_surface_is_tmp` 断言在 tmp 之下；
   逃出即 rc=2（不写任何字节）。真 `backups/` 与 live vault 不在写面内。
6. 7692 门按 **concept 名 / node 名逐个**断言 group B 不变，不使用计数判据。
7. 7692 门两条负控（写侧误标 group 身份键 / 读侧去 group 过滤）与正例**共用同一个断言函数**
   `_assert_group_b_intact`，负控用 `pytest.raises(AssertionError, match="G610-ISOLATION-BREACH")` 捕获。
8. 禁碰现网 7691 有三层：仓库 conftest 的 W4 门（configure 期 rc=3）、门文件自身的
   `_test_neo4j_reachable()` 含 `:7691` 拒跑、以及 `test_g610_never_targets_live_7691` 自证门。
9. 本卡**零** `backend/app/**` 写文件，`scripts/daily_review_run.py` 与 `review_overview.py` 一行未改。

---

## ③ 请按重要性排序回答的问题

**⓪（最重要）** `--share-state` 这条负控，是否真的把两个库逼到了**同一个 state 文件**？
「两库同 basename ⇒ `vault_key` 相等 ⇒ `state_path` 相等」这条路径在代码上是否可信，
还是说作者只是换了一个断言口径、让它看起来红了？请对照 `daily_review_run.py:70-85` 与
`scripts/send_bark.py` 的 `vault_key` 自行判断。

**①** canary 有没有**任何一条**路径会写到真 `backups/` 或 live vault？
`_load_runner` 的补丁（`REPO` / `BACKUPS` / `VAULT`）是否覆盖了全部落盘点？
`state_lock_path`、`save_state` 的临时件、锁文件的 `O_CREAT`，是否都在补丁覆盖面内？
`_assert_write_surface_is_tmp` 的白名单判据有没有漏掉某个落盘点？

**②** 7692 门的两条负控之所以红，是不是红在「group B 读到了 A 的写」**这条隔离断言**上，
而不是红在 import 错误、fixture 失败、连接异常或别的什么地方？
`match="G610-ISOLATION-BREACH"` 这个做法是否足以把两者区分开？

**③** 门在容器不可达或降级 JSON 时整文件 skip。这个 skip 有没有可能被误读成「绿」？
文件里关于「skip ≠ pass」的表述是否清楚到让后来者不会误判？

**④** 本卡对总账 `:983`「强制复用 G2-9 同名攻击用例集、禁止另建 tmp fixture vault」的执行方式是：
canary **直接 import** G2-9 的常量；门文件**不** import 而用自己的 `g610gate` 命名空间承载同一形状
（理由：7692 是共享容器，G2-9 的清理语句按 `g29` 前缀 `DETACH DELETE`，两边并发跑会互删种子）。
这个理由是否成立？两者是否构成对总账要求的实质偏离？

**⑤** 正向对照（canary 的 P1/P2/P3；门里 A 组自己确有复习写）是否真的排除了
「两库都没写所以两边都没变」这类假绿？有没有哪一层的正向对照其实是自证的？

**⑥** canary 在 `--share-state` 下 group 维也被断言为「两库 group 相同」。
这个 group 派生（`sanitize_vault_id(vault.name)` → `build_vault_group_id` → `to_physical_group_id`）
是否与生产真实的 vault_id 派生一致？作者在 docstring 里的声明是否与代码相符？

---

## ④ 输出格式

按 **BLOCKER / HIGH / MEDIUM / LOW** 分级，每条给出：

- `file:line`
- 一句话说明问题
- 一句话说明你会怎么让它显形，措辞用「负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径」这一类

若某级别为空，请明写「无」。结尾请给出 BLOCKER / HIGH / MEDIUM / LOW 的计数。

---

## ⑤ 边界

- 只读，不改文件，不连接任何数据库（含 7691 / 7692）。
- **不评** `review_overview.py` / `daily_review_run.py` 生产逻辑本身的对错——它们是既有代码，本卡只 import 复用。
- **不评** G2-9 的 fixture 数据面设计。
- 只评本卡这两个新文件，以及它们对上述生产代码的**使用方式**是否正确。
