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

审查基线：`git diff 80d2fbb0d594351d606dd0ec95dfe1969a908cda 52bab59e0d43b2fca444a958410a8f07177fab89 -- . ':(exclude)_bmad-output'`

**本轮是 round-3。** round-1 报 BLOCKER 0 / HIGH 2 / MEDIUM 7 / LOW 1，round-2 报 BLOCKER 0 / HIGH 1 / MEDIUM 4 / LOW 1。
round-2 的 HIGH 与三条 MEDIUM 已在 `52bab59e` 落地整改（见 §⑦）。请**独立重审当前 HEAD**，不要采信整改自述。

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

---

## ⑥ round-1 的处置（请核对是否真的修好，以及有没有修出新问题）

| r1 条目 | 处置 |
|---|---|
| HIGH-1 白名单锚点未被验 | 受保护位置改为从 runner **打补丁之前**的 `REPO`/`BACKUPS`/`VAULT` 派生（不抄路径字面量）；新增 `_assert_tempdir_anchor()`，在 `mkdtemp` **之前**验 `gettempdir()`。**并实测发现**：守卫还必须早于 `import app.*` —— 第三方 import 链（jieba/torch）会按 `TMPDIR` 落缓存，抢在 `mkdtemp` 前面。顺序已改为 载 runner → 派生受保护位置 → 验 TMPDIR → import app.* → mkdtemp |
| HIGH-2 读侧负控非单变量 | `_snapshot_raw()` 三条 facet 全部改为手写 Cypher，`group_filtered` 是唯一差别；负控 ② 的写回到与正例逐字相同的 `_review_write(A)`（写是**对的**，只有读少了 scope）。生产读路径的隔离由 `_snapshot_production()` 在正例里单独断言 |
| MEDIUM-1 守卫晚于建目录 | `_plan_vault_pair()` 只算路径不建目录；守卫通过后才 `mkdir` + 落白板；白名单纳入 `vault / SHARED_BOARD` |
| MEDIUM-2 自建 loader 会写 .pyc | `exec_module` 期间 `sys.dont_write_bytecode = True`，无条件恢复 |
| MEDIUM-3 rc=1 语义重合 | `run()` 增 `except Exception` → rc=2，rc=1 只保留「隔离被破坏」一个含义 |
| MEDIUM-4 按名字做键会压掉泄漏行 | 判据键改为含 group_id 的身份元组（LEARNED 用 `(name, c.group_id, r.group_id, score)`，Episode 用 `(nid, n.group_id, r.group_id, score)`） |
| MEDIUM-5 seed 只看返回值 | 新增 `_assert_seed_landed()`：seed 后回读，三个 facet 非空且分数确为 seed 分数 |
| MEDIUM-6 清理语句失效 | Episode 排到 Node 之前；补模板的孤儿 Episode 扫尾 |
| MEDIUM-7 总账 :983 读法 | **未改代码**，登记验收单交主 session 裁 |
| LOW-1 自证门也在 skipif 下 | **未改代码**；该层的独立证据落在 `evidence-g610/gate-7691-selflayer-*.txt`（直接调函数证明 `_test_neo4j_reachable()` 对 7691 返 False） |

请重点核对：整改本身有没有引入新缺陷；`_snapshot_raw` 的手写 Cypher 与生产读的语义差距是否被如实声明；
`_assert_tempdir_anchor` 的判定是否还有未覆盖的落盘入口。

---

## ⑦ round-2 的处置（请核对是否真的修好，以及有没有修出新问题）

| r2 条目 | 处置 |
|---|---|
| HIGH `gettempdir()` 自身就是一次写 | 已核实 CPython `_get_default_tempdir` 确实 `open` → `write(b'blat')` → `unlink`。判定改为**先读环境变量原文**（`TMPDIR`/`TEMP`/`TMP`），全部安全才允许 tempfile 碰盘；之后再复验 `gettempdir()` 的实际结果（覆盖环境变量未设、落平台默认或 cwd 的兜底支）。实测判据用**分数秒** mtime（`stat -f %Fm`）：探针在同一次调用内被 unlink，`ls` 看不见、父目录 mtime 看得见；整秒口径会假阴性 |
| MEDIUM-1 禁写字节码只覆盖 runner | 改为模块顶部 `sys.dont_write_bytecode = True` 进程级常开，不再恢复；`_load_runner` 里留一条回归哨兵（被改回 False 即拒跑） |
| MEDIUM-2 报告输出在异常边界之外 | `main()` 把三行 print 包进 try，失败写 ASCII 到 stderr 并 `rc=2`；`rc=1` 现在只剩「隔离被破坏」一个含义 |
| MEDIUM-3 孤儿 Episode 清理无 scope | **删掉**那条语句（它无法被 `g610gate` 限定），并在原位写明为何不补：判据作用面大于其主张就是越界清理。未覆盖面（无 group 且边已先消失）如实登记 |
| MEDIUM-4 总账 :983 | **仍不改代码**。本卡不自判通过，登记验收单交主 session 裁 |
| LOW-1 自证门在 skipif 下 | **仍不改代码**；该层独立证据在 `evidence-g610/gate-7691-selflayer-*.txt` |

请重点核对：① 环境变量原文判定是否覆盖了 tempfile 选目录的全部来源；② 进程级禁写字节码有没有副作用；
③ 删掉孤儿清理之后，本门自己的写路径是否真的产不出那种残渣；④ 整改有没有引入新的假绿面。
