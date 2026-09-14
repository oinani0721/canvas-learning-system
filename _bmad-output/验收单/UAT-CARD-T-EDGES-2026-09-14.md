# UAT — CARD-T-EDGES（BATCH-2026-09-11-第十四批 · 车道 T5-B）

> 卡文：`.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第十四批-goals/T5-B.md`
> 车道：`card-t5-bugs`（分支 `card/t5-bugs`）· 本车道第 2/5 张 · 前一卡 T5-A `CARD-TAIL-CLEANUP-LOOP`
> `PREV`（T5-A 末 commit）= `9b30179a0613f86b74a2b9258660d067a62056f9`
> 本卡 HEAD = **`5bffce4f`** · 未 push · 地盘 = 恰两文件

---

## 1. 🎯 一句话目标

Agent 给白板连线写"为什么这样连"的理由时，系统要把这条理由同时存进两个地方；**以前只要其中
一边写不进去，整次保存就崩掉、连已经存好的那一半也丢了**。本卡让它改成"存好的那半留着、坏掉
的那半标记为失败"。

## 2. 📖 你的视角（Behavior）

作为一个在白板上连线并让 Agent 记录理由的学习者，
我想要**一边存储临时出问题时，另一边已经存下的内容不要跟着一起丢**，
以便我不用因为后台某个存储抽风而把刚讲完的那段理由重讲一遍。

## 3. 🖥️ 交互流程（用户屏幕变化）

1. 我在白板上连一条线 → 和 Agent 聊完这条连线为什么成立
2. Agent 说"已记录" → 这条理由被保存
3. **改动前**：后台两个存储只要有一个出状况 → 我看到保存失败、整条理由没了，要重讲
4. **改动后**：同样情况 → 我看到"部分保存成功"，能存的那一半已经留下，只有另一半被标记失败

## 4-A. 🤖 Claude 已代验（技术断言全在这段）

> 证据目录：`_bmad-output/审查/evidence-t-edges/`（引用写全文件名，不用 glob；每份末行 `rc=`）

### 修改内容（(d) 四项，只碰两文件）

| 项 | 内容 |
|---|---|
| (d)① | `edges.py` `_write_neo4j_triplet`：`await neo4j.execute_query(query, {位置 dict})` → `params = {...}` + `await neo4j.run_query(query, **params)`（键名逐字不变，14 键） |
| (d)② | 删该行的 `# pyright: ignore[reportAttributeAccessIssue]`（`run_query` 存在后该 ignore 多余，留着会多一条 warning） |
| (d)③ | 重写上方注释块（去掉"本卡只让类型过门不修(TAIL)"框架，改为如实声明覆盖边界） |
| (d)④ | `except` 元组补 `AttributeError`（**只加这一类**，未泛化 `Exception`，保留原四类语义） |

### 裁判结果

| # | 裁判 | 结果 | 存档全文件名 |
|---|---|---|---|
| 1 | 第 0 分钟自证（pwd / 分支 / HEAD / 干净 / venv / `.env`） | ✅ 分支 `card/t5-bugs`，`git status --porcelain` = 0 行，`08100483` 是 HEAD 祖先 | （见对话；基线自证 `grep -vc '^#' $BASE` = **64**） |
| 1b | §〇 五条口径更正逐条复核 | ✅ **零漂移**：调用 `:112`、except `:140` 含 `asyncio.TimeoutError` 不含 `AttributeError`、`run_query` 在 `:536`、`def execute_query` 命中 0、`get_neo4j_client` `:2754-2808`、`.env` `NEO4J_ENABLED=true` + `:7691` | `facts-recheck-20260914T222855.txt`（rc=0） |
| 2 | pyright（绝对路径 + `test -x`，cwd=`backend/`，R-B14-10） | ✅ 开工 / 收工均 **`0 errors, 81 warnings`**（未变 82 ⇒ ignore 已删） | `pyright-open-20260914T222839.txt`、`pyright-final-20260914T224710.txt`（均 rc=0） |
| 2b | pyright **逐项**诊断改前/改后对照（`--outputjson`，闭 Codex r2 LOW-2） | ✅ `edges.py` 诊断 改前 **0 条** / 改后 **0 条** / **新增 0 条**；两态汇总均 `0 errors, 81 warnings`；跑前跑后 `shasum` 在档 | `pyright-diag-before-after-20260914T230427.txt`（rc=0） |
| 3 | 降级门 改前红 | ✅ `FAILED`，红在 `assert resp.status_code == 207` **实得 500**（注入锚已先通过） | `edges-207-red-20260914T223158.txt`（rc=1） |
| 3 | 降级门 改后绿 | ✅ `1 passed` | `edges-207-green-20260914T223438.txt`（rc=0） |
| 4 | 真库门 7692 改前红 | ✅ `FAILED`：`AttributeError: 'Neo4jClient' object has no attribute 'execute_query'` @ `edges.py:112` | `edges-7692-red-20260914T223245.txt`（rc=1） |
| 4 | 真库门 7692 改后绿 | ✅ `1 passed`——真写入并用独立客户端查回 1 个 `:EdgeRationale` 节点（**未 skip**，7692 容器在跑） | `edges-7692-green-20260914T223508.txt`（rc=0） |
| 4b | 7692 清理核（不滞留共享容器） | ✅ `t5bgate` 前缀残留 **0**，全库 `:EdgeRationale` 共 **0** | `7692-residue-20260914T223531.txt`（rc=0） |
| 5 | 负控①：`except` 去掉 `AttributeError` | ✅ 降级门必回 **500**（窄口径：红在"实得 500"）；跑前跑后 `shasum -a 256` 逐字相同 | `final-judges-20260914T232503.txt`（rc=0）、`negctl-both-r2-20260914T225441.txt` |
| 5b | 负控②：`except` 分支不透出异常消息 | ✅ **status 207 那条先通过**，红精确落在 `assert SENTINEL in graphiti_error` ⇒ 证 sentinel 注入锚承重且**非恒真**；shasum 逐字相同 | 同上 |
| 6 | ruff（zsh 数组 + 子 shell） | ✅ `files=2`，`All checks passed!`，rc=0 | `final-judges-20260914T232503.txt` |
| 6b | ruff 验伪锚 | ✅ **F821** probe rc=**1**（⚠️ 卡文原写 F401，实测在 `backend/` 下**恒不触发**，见下 §更正） | `ruff-and-turf-20260914T224619.txt`、`final-judges-20260914T232503.txt` |
| 7 | 地盘门 `$PREV..HEAD ':(exclude)_bmad-output'` | ✅ **恰两文件**：`backend/app/api/v1/endpoints/edges.py`、`backend/tests/integration/test_edges_dual_write_neo4j_t5b.py` | `final-judges-20260914T232503.txt` |
| 8 | `tests/unit` 目录级（带 `--ignore tests/unit/test_deploy_vault_sh.py`，相对路径，R-B14-3） | ✅ base **64** / close **64**，`diff` **为空**，新增 `>` 行 **0** | `unit-final-20260914T232531.txt`（rc=1，既有红）、`unit-diff-final-20260914T233101.txt`（rc=0） |
| 8b | `tests/unit` diff 验伪锚 | ✅ 往 close 临时加一行假 nodeid，`diff` 立刻报出 `>` 行 ⇒ 证"diff 为空"不是恒真 | `unit-diff-final-20260914T233101.txt`、`.probe.nodeids` |
| 9 | 既有 `test_edge_rationale_fallback.py`（禁碰，改前改后都须绿） | ✅ 改前 `12 passed` / 改后 `12 passed` | `existing-fallback-before-20260914T223010.txt`、`existing-fallback-after-20260914T223642.txt` |
| 10 | openapi 不变 | ✅ `$PREV..HEAD -- backend/openapi.json` diff **为空**（Codex 独立核：两端 blob 同为 `a89b8088…`） | `final-judges-20260914T232503.txt` |
| 11 | 全程未碰 7691 / 7687 | ✅ 每一跑末行 `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)` | 所有 pytest 存档 |

### 注入锚（承重，(b)/(c)/(f)②）

- **行为锚**：用**独立 stub 实例**跑 `pytest.raises(AttributeError, match=SENTINEL)`
  ——⛔ 刻意不用注入用的那个 stub，否则 `stub.calls` 会先被探针自己加成 1，注入锚当场退化成恒真。
- **注入锚（降级门）**：发请求前断言 `stub.calls == 0`、发请求后断言 `stub.calls >= 1`（0→≥1 的**差值**锚）；
  且 207 响应体 `graphiti_status.error` 含 `T5B-STUB-SENTINEL`。
- **前置注入锚（真库门，发写之前）**：源模块属性已被替换 + client 解析出的端口 = 7692 +
  client 不在 JSON fallback 模式；任一不成立即 `pytest.fail` 立即停。
- **口径锚**：断言 `not hasattr(edges_module, "get_neo4j_client")` ⇒ 钉死"局部导入、只能在源模块拦"。
- ⛔ **「改前 500」不作注入证据**：真 `get_neo4j_client()` 恒返真客户端（`neo4j is None` 是死守卫），
  未注入时真客户端同样没有 `execute_query`，照样 500 ⇒ 该判据对注入与否**不可分辨**。

### Codex 复核（`gpt-6-astra` + `ultra`，5 轮，D-15）

| 轮 | 绑定 SHA | B / H / M / L | 存档 |
|---|---|---|---|
| r1 | `c9c73f57` | 0 / 1 / 1 / 1 | `codex-review-CARD-T-EDGES-r1.md` |
| r2 | `9764cceb` | 0 / 2 / 0 / 3 | `codex-review-CARD-T-EDGES-r2.md` |
| r3 | `c2e3d533` | 0 / 1 / 0 / 3 | `codex-review-CARD-T-EDGES-r3.md` |
| r4 | `caf8180e` | 0 / 1 / 0 / 1 | `codex-review-CARD-T-EDGES-r4.md` |
| **r5（终审）** | **`7c63c5eb`** | **0 / 1 / 0 / 1** | `codex-review-CARD-T-EDGES-r5.md` |

**已整改并被 Codex 确认关闭**：r1 HIGH（端口黑名单 + 收集期探针）、r1 LOW（cleanup 串行）、
r2 HIGH-2（路由族 scheme）、r2 LOW-1（存档缺 rc）、r2 LOW-2（pyright 仅汇总）、
r3 L1（"未捕获 ⇒ 必然 500"过强）、r3 L2（两段 `except ValueError` 注释错位）、
r5 L3（docstring 残余"必然真连"表述，本卡最后一个 commit `5bffce4f` 修）。

**⛔ 未关闭且不自判通过 —— 交主 session 按 D-15 裁定**：

> **H1（Codex 连续三轮标注「缺陷成立，但超出本卡改动面」）**：`_write_neo4j_triplet` 的 `except`
> 元组不覆盖 neo4j 驱动异常整族。驱动 6.1.0 实测 MRO（`neo4j-exception-mro-20260914T230328.txt`）：
> `Neo4jError` / `ClientError` / `AuthError` / `TransientError` / `DriverError` /
> `ServiceUnavailable` / `SessionExpired` **七类全部**继承 `GqlError -> Exception`，与
> `RuntimeError` / `ConnectionError` / `OSError` 无继承关系 ⇒ 若穿透客户端内部的重试与回退，
> 端点仍会 500（权限 / 约束类 `ClientError` 存在该路径）。
> **车道不在本卡修的理由**：卡文 (d)④ 写死了元组的确切形态，§三「禁放宽判据」明令
> 「**只加 `AttributeError` 一个类型**」，加第六类 = 越界。该缺口在本卡之前就存在（改前每次调用
> 都死在 `AttributeError`，走不到驱动异常），但**本卡接通 `run_query` 后该路径变得可达**。
> Codex r3 ① 明确裁「不要求本卡越界修复……与 r2 的 MEDIUM 同一范围口径：可以接受明确披露并
> 移交，但不能把缺陷记为已关闭」；r4 确认当前披露"达到最低要求"。
> **终审 r5 因此仍是 HIGH = 1，轮次已用满 5 轮 ⇒ 按 D-15 停下交主 session 人审。**

**D-32 尾巴声明**：终审 r5 绑 `7c63c5eb`，其后的 `5bffce4f` 是**纯 docstring** commit
——去 docstring 后 AST 与 `7c63c5eb` **完全相同**（已 AST 实测，见该 commit message），
非注释行 diff 为空，请主 session 按 D-32 逐行等价核。

### ⚠️ 卡文口径更正（实测，供主 session 回写）

1. **裁判 6 的验伪锚用 F401 不成立**：`backend/ruff.toml` 的 `select = ["E9","F63","F7","F82"]`
   **不含 F401** ⇒ 喂含 F401 的文件 `ruff check` 实测 **rc=0**，该锚**恒不触发 = 假锚**。
   已改用 **F821**（在启用的 F82 组内），probe 实测 rc=1。两者对照落在
   `ruff-and-turf-20260914T224619.txt`。
2. **负控还原源不能用 `git show HEAD:…edges.py`**：卡文 (f)① 这么写，但**本卡负控跑在代码
   commit 之前**，那时 HEAD 是未修版 ⇒ 照抄会把本卡修复一起还原掉。已改用**变异前副本**做
   还原基准（跑前跑后 `shasum` 逐字相同）。口径 = "还原基准是变异前的 sha，不是 HEAD"。
3. **`spec-sync-flat` hook 会把 `backend/openapi.json` 塞进任何 `backend/app` 的 commit**：
   首次 commit 实测被塞入（diff 只有 `x-generated-at` 一行时间戳，`paths=197 schemas=357` 不变），
   造成地盘变三文件。已用 `git show <PREV>:backend/openapi.json > …` 写回 + `git add` 还原，
   后续 commit 一律 `LEFTHOOK_EXCLUDE=spec-sync-flat`（⛔ **未**排除 `python-typecheck` /
   `python-lint`，两者全程正常跑过）。证据 `openapi-restore-amend-20260914T224607.txt`。
   ⚠️ 已有记忆写的是 `spec-sync-root`，本次实测 `spec-sync-root` 反而 **skip**，真正塞入的是
   **`spec-sync-flat`**。
4. **W4 门对本文件不拦，只记账**：`live_port_guard.EXEMPT_MARKERS` 含 `integration` /
   `real_neo4j`，`EXEMPT_PATH_PREFIXES` 含 `integration` ⇒ 本文件两项都占，属 advisory 面。
   本卡两门的注入锚**是唯一防线**（这也是它们承重的理由）。
5. **卡文 (c) 的「client.uri」字段名**：实测 `Neo4jClient.__init__` 存的是 **`self._uri`**（私有）。

---

## 4-B. 👤 你来验（3 分钟，全程在白板里完成）

- [ ] 我在白板上连一条线，和 Agent 讲清楚"为什么 A 是 B 的前提" → 我看到 Agent 回我"已记录"
      → 我感觉**踏实**，讲过的话被接住了。
- [ ] 我接着连第二条线、再讲一段理由 → 我看到两条线的理由都在，没有哪一条莫名其妙消失
      → 我感觉**可以放心往下连**，不用每讲一条就回头确认一次。
- [ ] 我故意在很短时间里连续连三四条线并各讲一小段 → 我看到它们都被记下来了
      → 我感觉**顺畅**，系统跟得上我的节奏。
- [ ] 读一句话确认这次修的是什么：**以前后台两个存放处只要有一个临时出状况，我刚讲完的那段
      理由会整段丢掉；现在能存的那一半会留下，只有另一半被标记为没存成功。**
      → 我感觉这条链**终于稳了**，不会因为一侧出问题就整单丢失。
- [ ] ⚠️ 也请知道这次**没修完**的部分：这次只修好了"某个内部写法写错名字"那一类失败。
      **如果那个存放处本身暂时连不上或没有写入权限，目前仍然可能整次保存失败。**
      这一项需要你拍板要不要单独再排一张卡。→ 我感觉**信息是透明的**，知道边界在哪。

## 5. 🚦 验收结果

- **通过** → 回一句"T5-B 通过"，车道继续串 T5-C `CARD-T-SWITCHVAULT`。
- **不通过** → 在下面批注区写 `[!error]+`，说清哪一步和你预期不一样。
- **⛔ 无论通过与否**，H1 都需要主 session 单独裁一次（见 §4-A 灰框）。

## 6. 📝 批注区

> [!question]+ 你的提问
>

> [!error]+ 你发现的问题
>

---

## 7. 🔗 技术 spec 引用

- 卡文：`…/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第十四批-goals/T5-B.md`
- 源码：`backend/app/api/v1/endpoints/edges.py`（`_write_neo4j_triplet`）
- 测试：`backend/tests/integration/test_edges_dual_write_neo4j_t5b.py`（3 门）
- commit 链：`c9c73f57` → `9764cceb` → `c2e3d533` → `caf8180e` → `7c63c5eb` → `5bffce4f`
- Codex 存档：`_bmad-output/审查/codex-review-CARD-T-EDGES-r1..r5.md`
- 证据：`_bmad-output/审查/evidence-t-edges/`

---

## 📌 本卡未证明什么（≥4）

1. **未证明 Neo4j 真实驱动失败会被记成 207**——七类驱动异常全不在 `except` 元组内（H1）；
   本卡两门覆盖的只有 `AttributeError` 这一条降级路径。
2. **未证明生产默认是否应"真连 Neo4j"**——本卡只修调用形态与降级，取回路仍由
   `get_neo4j_client()` 决定（产品裁定，移交）。
3. **未证明 `_write_lancedb` 侧失败时的 207**——本卡只注入 Neo4j 侧失败，对称路径未测。
4. **未证明双侧同时失败时的 500**——只测了单侧失败 → 207。
5. **未证明 `run_query` 的重试 / 超时语义在真 7692 上的时序**——只验了写成功/失败分流。
6. **未证明 `_write_lancedb` 的三处 TAIL T10 `pyright: ignore` 死分支**（本卡禁碰）。
7. **未证明 `edges.py` 的 `neo4j is None` 守卫在任何运行形态下可达**——实测
   `get_neo4j_client()` 恒返 `Neo4jClient`，按死守卫处理但**禁碰**，是否退役另立卡。
8. **未证明真库门的清理在任何情形下都删干净**——`finally` 保证"尝试"不保证"成功"：写入后
   断连、DELETE 失败、进程被强杀、verifier 转入 JSON fallback、或写入组与清理组不一致时，
   仍可能给共享 7692 留数据（Codex r2 ③ / r3 ③ 列举，车道接受）。
9. **未证明整个 pytest 进程零网络**——根 conftest 仍导入 `app.main` 等模块；
   `blocked=0, advisory=0` 只说明**账本覆盖的 7691/7687 两个端口上零次连接尝试**，
   且 W4 自证探针跳过记账。
10. **未证明本卡两门之外的既有 integration 套件在打桩失效时不会连 7691**——
    本卡只给自己新增的门加了注入锚；全仓同风险巡检 = 移交项。
11. **未证明 `bolt://host:7692` 就一定是那个指定的测试容器**——白名单只保证端口范围，
    不做身份认证（Codex r3 ② 明确）。

## 📌 台账待登记条目（≥4）

1. **T-EDGES 缺陷修复**：`execute_query` 恒 `AttributeError` 穿透成 500 → 修复 commit 链
   `c9c73f57`…`5bffce4f`；门 nodeid = `test_neo4j_attribute_error_degrades_to_207` /
   `test_run_query_writes_edge_rationale_to_7692` / `test_test_uri_port_whitelist_rejects_everything_but_7692`。
2. **⛔ H1 待主 session 裁定（D-15）**：驱动异常整族不在 `except` 元组内 ⇒ 真实写失败仍可能 500。
   Codex 三轮标注"缺陷成立但超出本卡改动面"，车道不自判通过。建议：第十五批立卡，把
   `neo4j.exceptions.Neo4jError` / `DriverError` 纳入降级，或按 Codex 建议只对"确认属于客户端
   缺失方法的属性解析错误"降级 + 收窄 `try` 范围。
3. **口径更正五条**（卡文 §〇 ①~⑤）实测**零漂移**，全部成立，无需回写。
4. **卡文判据更正三条（建议回写卡文/手册）**：① 裁判 6 验伪锚 F401 → **F821**（`backend/ruff.toml`
   `select` 不含 F401，F401 锚恒不触发 = 假锚）；② 负控还原源不得用 `git show HEAD:`（代码未
   commit 时 HEAD 是未修版）→ 用变异前副本；③ `spec-sync-flat`（**不是** `spec-sync-root`）会把
   `backend/openapi.json` 塞进任何 `backend/app` 的 commit。
5. **`:112` 的 `reportAttributeAccessIssue` ignore 已删**，pyright 保持 `0 errors, 81 warnings`
   （逐项对照新增 0 条）。
6. **"生产是否默认真连 Neo4j"产品裁定移交**（U2 §五 T-EDGES 原列；D-39 只裁了测试走 7692）。
7. **真库门已真跑未 skip**（7692 容器在跑），写入并查回成功，残留清零。
8. **Codex 五轮存档路径 / 绑定 SHA / B-H-M-L 计数**见 §4-A 表；终审 r5 绑 `7c63c5eb`，
   其后 `5bffce4f` 为 **D-32 纯 docstring 尾巴**（AST 实测等价），请主 session 逐行等价核。
9. **`tests/unit` 目录级 diff 为空**（base 64 / close 64 / 新增 0），带验伪锚。
10. **G-TEST-GAP**：既有 `test_edge_rationale_fallback.py` 实测 **9 处**整体 patch 掉被测函数
    `_write_neo4j_triplet`（`:65/92/118/144/168/193/218/245/279`），使本缺陷对既有套件不可见；
    本卡新增"不 mock 被测函数"的三门补盲。既有 9 处是否改造 = 另立卡（本卡禁碰该文件）。
11. **W4 豁免面巡检移交**：`EXEMPT_MARKERS` / `EXEMPT_PATH_PREFIXES` 使 `tests/integration/**`
    默认只记账不拦 ⇒ **任何打桩失效的 integration 门都可能真连现网**。本卡两门已加注入锚；
    全仓其余 integration 门是否同风险 = 巡检项。
12. **`LEFTHOOK_EXCLUDE=spec-sync-flat` 使用登记**：本卡四次 commit 用了它（仅为挡住 hook 越界
    改 `openapi.json`）；⛔ **全程未**排除 `python-typecheck` / `python-lint`，两者正常跑过。
13. **新文件地盘放行 = 已批**（裁定 R-B14-8，手册 §一 T5 行已列），按"已批"登记。
