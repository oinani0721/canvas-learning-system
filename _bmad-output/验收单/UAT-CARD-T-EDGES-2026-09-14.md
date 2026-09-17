# UAT — CARD-T-EDGES（BATCH-2026-09-11-第十四批 · 车道 T5-B）

> 卡文：`.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第十四批-goals/T5-B.md`
> 车道：`card-t5-bugs`（分支 `card/t5-bugs`）· 本车道第 2/5 张 · 前一卡 T5-A `CARD-TAIL-CLEANUP-LOOP`
> `PREV`（T5-A 末 commit）= `9b30179a0613f86b74a2b9258660d067a62056f9`
> 本卡 HEAD = **`546b6719`** · 未 push · 地盘 = 恰两文件
> **⚠️ 本卡分两阶段**：09-14 第一阶段按卡文原范围做完并收官（Codex r1~r5，H1 移交）；
> **09-15 用户裁定「增加 codex 的审查轮次继续来修」⇒ 放开 D-15 的 5 轮上限**，
> 第二阶段（r6~）突破卡文 §三 把 H1 修掉，并连带修掉一个**比 H1 更重、且由本卡打通的假绿**。

---

## 1. 🎯 一句话目标

Agent 给白板连线写"为什么这样连"的理由时，系统要把这条理由同时存进两个地方；
**以前只要其中一边写不进去，整次保存就崩掉、连已经存好的那一半也丢了**。
本卡让它改成"存好的那半留着、坏掉的那半标记为失败"——并在第二阶段发现并修掉了
**更糟的一种情况：明明什么都没存进去，系统却报"两边都成功"**。

## 2. 📖 你的视角（Behavior）

作为一个在白板上连线并让 Agent 记录理由的学习者，
我想要**一边存储临时出问题时，另一边已经存下的内容不要跟着一起丢**，
**并且系统不能在什么都没存下的时候告诉我"保存成功"**，
以便我不用因为后台某个存储抽风而把刚讲完的那段理由重讲一遍，也不用担心它悄悄丢掉。

## 3. 🖥️ 交互流程（用户屏幕变化）

1. 我在白板上连一条线 → 和 Agent 聊完这条连线为什么成立
2. Agent 说"已记录" → 这条理由被保存
3. **改动前**：后台两个存放处只要有一个出状况 → 我看到保存失败、整条理由没了，要重讲
4. **改动前（第二阶段发现的更坏情况）**：某个存放处连不上时 → 我看到**"保存成功"**，
   但那条理由其实**一个字都没存进去**
5. **改动后**：情况 3 → 我看到"部分保存成功"，能存的那一半留下；
   情况 4 → 我看到"没能确认存进去"，而不是假的成功

## 4-A. 🤖 Claude 已代验（技术断言全在这段）

> 证据目录：`_bmad-output/审查/evidence-t-edges/`（引用写全文件名，不用 glob；每份末行 `rc=`）

### 第二阶段改了什么（09-15，H1 修复）

| 项 | 内容 |
|---|---|
| **收窄 `try`** | 从"包整个函数体"改成**只包 `await neo4j.run_query(query, **params)` 这一行**。之前 `params` 里 14 次 `rationale.<field>` 取值、`get_neo4j_client()` 的配置缺陷、`to_physical_group_id` 的 punycode 路径，任一出错都被记成"Neo4j 写失败" ⇒ 静默 207 ⇒ 5xx 恒 0 ⇒ 前端 Outbox 把 207 当"部分成功已保留"继续投递 ⇒ 数据永久丢失。收窄是"加宽类型集"能保持安全的**前提**。 |
| **写确认** | Cypher 以 `RETURN er.record_id AS record_id` 收尾 ⇒ 真写成功恒返 **1 行**；返回 0 行 = **未取得写入确认** ⇒ `WriteStatus(success=False)` ⇒ 207，而不是 200 谎报成功。 |
| **`_NEO4J_WRITE_FAILURES`** | 提成模块级常量：原四类内建 + `AttributeError` + 对端四类（`ServiceUnavailable` / `SessionExpired` / `TransientError` / `DatabaseError`）+ tenacity `RetryError`。⛔ **刻意不收 `Neo4jError` / `ClientError` 族**、不收 `ConnectionPoolError`、不收 `ConfigurationError` 族。 |

### ⛔ 第二阶段最重的发现：卡文对 H1 的前提是错的

29-agent 对抗复核（4 视角提案 → 合成裁决 → 3 路反驳 → 4 路残余扫描 → 逐条核验，
3/3 反驳命中、13 条残余存活）推翻了卡文与前五轮的共同前提：

> **H1 描述的伤害在活线路上根本不发生，发生的是更糟的那个。**
> `ServiceUnavailable` 走不到端点的 `except`：重试耗尽 → `RetryError`
> → `_fallback_to_json()` → `_run_query_json_fallback` 对 `CREATE (er:EdgeRationale …)`
> 三个关键词分支全不命中 ⇒ 落 `else:` `logger.warning + return []` —— **不抛异常**
> ⇒ `run_query` 正常返回 `[]` ⇒ 旧代码**丢弃返回值**直接 `WriteStatus(success=True)`
> ⇒ **HTTP 200「双写全部成功」，而这次写连一次确认都没拿到。**
> （措辞边界 r7-L1：说「没拿到确认」不说「图库里什么都没有」——
> 返回空行不能据此断言没有落盘，存在「已提交但确认丢失」的路径。）
> **而这条路是本卡第一阶段打通的**（改前恒死在 `AttributeError`，走不到 `run_query`）。

离线实证（不连任何库）：`fallback-200-falsegreen-20260915T120325.txt`（rc=0）——
`run_query` 返回 `[]`、不抛异常、`_write_neo4j_triplet` 返 `success=True`。

### 裁判结果（绑最终 HEAD `134cf5a4`；标注了更早 SHA 的存档是该判据首次通过时的记录，
其后的改动均为注释 / 措辞，唯一的行为变化是清理语句加回执，已由 NC-H 单独验证）

| # | 裁判 | 结果 | 存档全文件名 |
|---|---|---|---|
| 1 | 第 0 分钟自证 + §〇 五条口径复核 | ✅ 零漂移 | `facts-recheck-20260914T222855.txt`（rc=0） |
| 2 | pyright（绝对路径 + `test -x`，cwd=`backend/`） | ✅ **`0 errors, 81 warnings`**（全程不增） | `pyright-open-20260914T222839.txt` / `pyright-final-20260914T224710.txt` |
| 2b | pyright 逐项诊断改前/改后对照 | ✅ `edges.py` 新增诊断 **0** | `pyright-diag-before-after-20260914T230427.txt` |
| 3 | 门全集（**17 格**） | ✅ `17 passed`，`blocked=0 advisory=0` | `edges-r9-allgates-20260916T003901.txt`（rc=0，绑最终 HEAD） |
| 3a | 降级门 改前红 / 改后绿 | ✅ 改前 `FAILED`（实得 500）→ 改后 `passed` | `edges-207-red-20260914T223158.txt`(rc=1) / `edges-207-green-20260914T223438.txt`(rc=0) |
| 3b | 真库门 7692 改前红 / 改后绿 | ✅ 改前 `AttributeError` → 改后真写并查回，**未 skip** | `edges-7692-red-20260914T223245.txt`(rc=1) / `edges-7692-green-20260914T223508.txt`(rc=0) |
| 3c | 7692 清理核 | ✅ 残留 0，全库 `:EdgeRationale` 0 | `7692-residue-20260914T223531.txt`（rc=0） |
| 4 | **负控 ×9**（见下表） | ✅ **每条精确命中各自的门**，跑前跑后 `shasum` 逐字相同 | `negctl-both-r2-20260914T225441.txt` / `negctl-r6-newgates-20260915T120705.txt` / `negctl-r7-20260915T183450.txt` / `negctl-r8-20260915T234554.txt` / `negctl-r8-cleanup-20260915T235206.txt` |
| 5 | ruff（zsh 数组 + 子 shell） | ✅ `files=2`、`All checks passed!`、rc=0 | `final-judges-20260914T232503.txt` |
| 5b | ruff 验伪锚 | ✅ **F821** probe rc=1（⚠️ 卡文原写 F401 在 `backend/` 下**恒不触发**） | `ruff-and-turf-20260914T224619.txt` |
| 6 | 地盘门 `$PREV..HEAD ':(exclude)_bmad-output'` | ✅ **恰两文件** | `final-judges-20260914T232503.txt` |
| 7 | `tests/unit` 目录级（带 `--ignore`，相对路径） | ✅ base **64** / close **64**，diff **空**，新增 `>` **0** | `unit-final-r8-20260916T001124.txt`（rc=1，既有红）+ `base.nodeids` / `close.nodeids` |
| 7b | `tests/unit` diff 验伪锚 | ✅ 加一行假 nodeid，`diff` 立刻报 `>` | `unit-diff-final-20260914T233101.txt` |
| 8 | **`tests/api` 目录级**（协议 §3：改 `backend/app/**` 要跑对应面） | ✅ `268 passed`（与手册波 0 基线一致） | `api-dir-20260915T183949.txt`（rc=0） |
| 9 | edges 的其余三个消费方 | ✅ `66 passed`（regression prompt 18 + wave5 36 + fallback 12） | `edges-consumers-20260915T183926.txt`（rc=0） |
| 10 | openapi 不变 | ✅ diff 空（Codex 独立核：两端 blob 同为 `a89b8088…`） | `final-judges-20260914T232503.txt` |
| 11 | 全程未碰 7691 / 7687 | ✅ 每一跑末行 `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)` | 所有 pytest 存档 |
| 12 | 写确认判据的行数前提（7692 实测） | ✅ 带 `RETURN` 返 **1 行** / 去掉 `RETURN` 返 **0 行** ⇒ 判据与那句 `RETURN` 绑定 | `write-confirm-rowcount-probe-20260915T182121.txt`（rc=0） |
| 13 | `_write_lancedb` 从不真写（移交项依据） | ✅ 运行期确认 `add_documents` 是协程函数；`to_thread` 拿到协程对象后**函数体零执行、零抛异常** | `lancedb-never-writes-probe-20260915T183820.txt`（rc=0） |
| 14 | **存档自绑 SHA**（按 Codex r9 的存档边界意见新建，r10 意见补记 pyright 调用范围） | ✅ 首部打印 HEAD + 两文件**工作树 sha256** 与 `git show HEAD:` sha256 并逐串标注是否一致；并写明 pyright 命令是 `(cd backend && $P app)`、检查的是 **`backend/app` 这个包不是全仓** —— **该机制首跑即抓出「工作树与 HEAD 不一致」**（当时整改尚未 commit） | `allgates-selfbound-20260916T012207.txt`（rc=0，绑 `546b6719`） |

### 17 格门清单

| 门 | 格数 | 锁的是什么 | DB |
|---|---|---|---|
| 1 降级门 | 1 | `AttributeError` → 207 + sentinel + `run_query` 形态锚 + **`RETURN` 耦合锚** | 零 |
| 1b 白名单 | 1 | scheme + 端口双白名单（路由族 / 省略端口 / `:0` 必拒） | 零 |
| 1c 加宽门 | **5** | 新收的每一类 → 207，且错误串**以生产加的类型名前缀开头** | 零 |
| 1d 反向门 | **5** | 被刻意排除的 5 类（ClientError/AuthError/ConnectionPoolError/TypeError/KeyError）**必须仍 500** | 零 |
| 1d2 边界门 | 1 | **`try` 的范围本身**：getter 抛 `AttributeError` 必须穿透成 500 | 零 |
| 1e 写确认 | 2 | 返 0 行 → 207（+ 返 1 行 → 200 的对照组，防"永远设 False"作弊） | 零 |
| 1f 端到端 | 1 | 真 `Neo4jClient(use_json_fallback=True)` 证明 1e 模拟的形态是真的 | 零网络 |
| 2 真库门 | 1 | 7692 真写并查回 | 7692 |

### 九条负控，每条精确命中各自的门

| 负控 | 变异 | 期望红 | 实测 |
|---|---|---|---|
| NC-1 | 去掉 `AttributeError` | 降级门 | ✅ 1 格，红在"实得 500" |
| NC-2 | except 分支不透出异常消息 | sentinel 锚 | ✅ **status 207 先通过**，红精确落在 sentinel 断言 |
| NC-A | 删掉新收的 5 类 | 门 1c | ✅ 5 格全红 |
| NC-B | 删掉写确认块 | 门 1e/1f | ✅ 2 格红 |
| NC-C | **把 `Neo4jError` 加进元组（泛化）** | 门 1d | ✅ ClientError/AuthError 2 格红 |
| NC-E | 生产把 `error` 类型前缀去掉 | 门 1c | ✅ 5 格全红（证 M2 的假门已变真门） |
| NC-F | `try` 恢复成包整个函数体 | 门 1d2 | ✅ 1 格红 |
| NC-G | 删掉 Cypher 末尾的 `RETURN` | 耦合锚 | ✅ 降级门 + 真库门同时红 |
| NC-H | 清理语句去掉 `RETURN count(er)` | 真库门清理回执 | ✅ 1 格红，红在「清理语句没有回执」；还原后 7692 残留 0 |

> ⚠️ NC-H 第一次跑时锚没命中（`ruff format` 重排了那段字符串，`count=0`），
> 那一跑的 `17 passed` 是**未变异态、不算数**——已用实际文本重做并留档。
> 这正是「变异必须先证明它真的落盘了」的又一次现场教训。

### Codex 复核（`gpt-6-astra` + `ultra`）

| 轮 | 绑定 SHA | B / H / M / L | 关键结论 |
|---|---|---|---|
| r1 | `c9c73f57` | 0 / 1 / 1 / 1 | HIGH：端口黑名单 + 收集期探针 |
| r2 | `9764cceb` | 0 / 2 / 0 / 3 | HIGH-2：路由族 scheme |
| r3 | `c2e3d533` | 0 / 1 / 0 / 3 | 裁「H1 不要求本卡越界修复」 |
| r4 | `caf8180e` | 0 / 1 / 0 / 1 | 确认 H1 披露达标 |
| r5 | `7c63c5eb` | 0 / 1 / 0 / 1 | 第一阶段终审（5 轮用满） |
| **r6** | `8ff37ea5` | **0 / 1 / 3 / 2** | H1 修法有效；报出 **M2 = 本卡自造的假门** |
| **r7** | `a6f68241` | **0 / 1 / 0 / 4** | **MEDIUM 全部关闭**；HIGH 仅剩卡外既有那条，Codex 明确「接受本卡的限定措辞 + client 侧移交」 |
| **r8** | `34935f62` | **本卡 0 / 0 / 0 / 3** | ⭐ **本卡 HIGH 归零**。Codex 原文：「计数：本卡 BLOCKER 0／HIGH 0／MEDIUM 0／LOW 3；若连同已登记的独立卡外缺陷列示，则 HIGH 2，均非本轮新增」。R7-L1/L3/L4 判定关闭，H1 限定措辞判定达标 |
| **r9** | `134cf5a4` | **本卡 0 / 0 / 0 / 1** | r8 三条 LOW 全关闭；回执断言判「恰当、非恒真」；新报一条本卡既有 LOW（失败消息把可能原因写成确定结论） |
| **r10** | `65a5e642` | **本卡 0 / 0 / 0 / 1** | r9 三处措辞判关闭；回执断言判「恰当、无恒真」（拒 `True`/`False`/小数/负数/多行）；自绑存档判「满足 SHA 绑定、无必补项」 |
| **r11** | `546b6719` | *（终审，见文末）* | — |

**⭐ D-15 的「BLOCKER=0 且 HIGH=0」自 r8 起连续达成**（r8 绑 `34935f62`、
r9 绑 `134cf5a4`、r10 绑 `65a5e642` 均为本卡 HIGH=0）——两条 HIGH 被 Codex 明确归为
**「超出本卡改动面、非本轮新增」的独立卡外缺陷**（`initialize()` 吞部署异常 /
`_write_lancedb` 从不真写），两条都已登记移交并建议第十五批立卡。
每轮整改后都再送一轮绑最终 HEAD 复核（本卡每轮都有真实行为变化，不属 D-32 纯注释尾巴）。

**r9 的一条 LOW 与两条附带观察全部采纳**：LOW-1 三处失败消息把**可能原因**写成
**确定结论**（「会真连现网」「500 说明是 AttributeError」）→ 改「可能…」+「需核对异常来源」；
观察① 回执断言 `deleted >= 0` 对 `True`/`0.5` 放行（`True` 是 `int` 子类）→ 补
`isinstance(int) and not isinstance(bool)`；观察② 存档不能自绑 SHA → 新建自绑存档（裁判 14）。

**r7 的四条 LOW 全部按 Codex 给的确切表述处置**：
L1「未确认 ≠ 未落盘」措辞（4 处）、L2 绝对根因归类（3 处）、
L3 覆盖说明过强（1d2 与 RETURN 锚各 1 处）、L4 删掉真库门里一条冗余恒真断言。

**r8 的三条 LOW 同样全部按 Codex 给的表述处置**：
LOW-1 门 1d 的**两条失败消息**仍把处置策略写成根因结论（docstring 上一轮改对了、
消息漏了）；LOW-2 清理失败消息「清理是空转」超出证明范围（无回执只能说「未取得确认」），
并按建议补了回执形态断言 —— ⛔ **刻意不钉 `deleted == 1`**，因为 `finally` 也覆盖
「写本身没成功 ⇒ 合法零删除」的路径，硬钉 1 会把正常情形判红；
LOW-3 漂移的行号引用改符号名（保留 `neo4j_client.py:536`，那是跨文件引用、不随本卡漂移，
已复核仍指向 `def run_query`）。

**Codex 提出并已关闭的**：r1 HIGH（黑名单/收集期探针）、r1 LOW（cleanup 串行）、
r2 HIGH-2（路由族）、r2 LOW-1/2/3、r3 L1/L2、r5 L3、**r6 M1/M2/M3/L1/L2**。

**r6 M2 值得单独记**——这是本卡**自己造的假门**：门 1c 让 stub 抛
`exc_cls(f"{SENTINEL}: {type_name}")`，类型名是**测试自己塞进消息的**，于是
"响应含类型名"恒真；生产把 `error=f"{type(e).__name__}: {e}"` 改回 `error=str(e)`，
五格照样绿。判据的取名面不等于它的主张。已改成断言 `startswith(f"{type_name}:")`，
负控 NC-E 证明它现在会红。

### ⚠️ 卡文口径更正（实测，供主 session 回写）

1. **⛔ 卡文对 H1 的前提不成立**：卡文说"任一次 Neo4j 侧写失败都把整单打成 500"。
   实测在活线路上，Neo4j 宕机的产出是 **200 谎报成功**（见上）。
   ⇒ 卡文 (d)④ 那个"只加 `AttributeError`"的最小修，**修不到真实故障路径**。
2. **裁判 6 的验伪锚用 F401 不成立**：`backend/ruff.toml` `select = ["E9","F63","F7","F82"]`
   不含 F401 ⇒ 实测 rc=0 = 假锚。已改 **F821**（在 F82 组内），probe rc=1。
3. **负控还原源不能用 `git show HEAD:…`**：本卡负控跑在代码 commit 之前，
   那时 HEAD 是未修版 ⇒ 照抄会把修复一起还原掉。已改用**变异前副本**。
4. **`spec-sync-flat`（不是 `spec-sync-root`）** 会把 `backend/openapi.json` 塞进任何
   `backend/app` 的 commit（实测 `spec-sync-root` 反而 skip）。本卡六次 commit 用
   `LEFTHOOK_EXCLUDE=spec-sync-flat`；⛔ **全程未**排除 `python-typecheck` / `python-lint`。
5. **W4 门对本文件只记账不拦**：`EXEMPT_MARKERS` 含 `integration`/`real_neo4j`、
   `EXEMPT_PATH_PREFIXES` 含 `integration` ⇒ 本文件两项都占，属 advisory 面。
   **注入锚是唯一防线**。
6. **卡文 (c) 的「client.uri」**实际字段名是 **`_uri`**（私有）。
7. §〇 五条口径更正实测**零漂移**，全部成立。

---

## 4-B. 👤 你来验（3 分钟，全程在白板里完成）

- [ ] 我在白板上连一条线，和 Agent 讲清楚"为什么 A 是 B 的前提" → 我看到 Agent 回我"已记录"
      → 我感觉**踏实**，讲过的话被接住了。
- [ ] 我接着连第二条线、再讲一段理由 → 我看到两条线的理由都在，没有哪一条莫名其妙消失
      → 我感觉**可以放心往下连**。
- [ ] 我故意在很短时间里连续连三四条线并各讲一小段 → 我看到它们都被记下来了
      → 我感觉**顺畅**，系统跟得上我的节奏。
- [ ] 读一句话确认这次修的是什么：**以前后台两个存放处只要有一个临时出状况，我刚讲完的
      那段理由会整段丢掉；更糟的是有一种情况它明明一个字都没存进去，却告诉我"保存成功"。
      现在能存的那一半会留下，存不进去的那一半会如实标成"没能确认存下来"。**
      → 我感觉这条链**终于诚实了**，它不会再骗我说存好了。
- [ ] ⚠️ 也请知道这次**没修完**的部分：连线理由的**另一半（向量存储那一半）目前根本没
      真正写进去**，但系统一直报它成功——这是别的地方的毛病，本卡不能改，需要你拍板
      单独排一张卡。→ 我感觉**信息是透明的**，知道边界在哪。

## 5. 🚦 验收结果

- **通过** → 回一句"T5-B 通过"，车道继续串 T5-C `CARD-T-SWITCHVAULT`。
- **不通过** → 在下面批注区写 `[!error]+`。
- **⛔ 无论通过与否**，文末"台账待登记条目"里标 ⛔ 的三条需要你或主 session 拍板。

## 6. 📝 批注区

> [!question]+ 你的提问
>

> [!error]+ 你发现的问题
>

---

## 7. 🔗 技术 spec 引用

- 卡文：`…/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第十四批-goals/T5-B.md`
- 源码：`backend/app/api/v1/endpoints/edges.py`（`_NEO4J_WRITE_FAILURES` + `_write_neo4j_triplet`）
- 测试：`backend/tests/integration/test_edges_dual_write_neo4j_t5b.py`（17 格）
- commit 链（12 个）：`c9c73f57` → `9764cceb` → `c2e3d533` → `caf8180e` → `7c63c5eb`
  → `5bffce4f` → `a1147f19` → **`8ff37ea5`**（H1 修复）→ **`a6f68241`**（r6 整改）
  → **`34935f62`**（r7 整改）→ **`134cf5a4`**（r8 整改）→ **`65a5e642`**（r9 整改）
  → **`546b6719`**（r10 整改）
- Codex 存档：`_bmad-output/审查/codex-review-CARD-T-EDGES-r1..r11.md`（11 轮）
- 工作流复核：`wf_638c3d8d-0c4`（29 agents / 320 万 token）

---

## 📌 本卡未证明什么（≥4）

1. **未证明"任何 Neo4j 写失败都会记成 207"**——被刻意排除的那一族（门 1d 的 5 格）
   仍然 500，那是**有意的**：它们不是对端的错。
2. **未证明已覆盖全部逃逸面**：`neo4j._exceptions.BoltError` 族与 packstream 解码层的
   裸 `ValueError` / `struct.error` 仍会逃出元组而 500（驱动自己的连接池写的是
   `except (Neo4jError, DriverError, BoltError)`，但 `BoltError` 在私有模块里）。
3. **未证明"部署错误必然 500"在所有路径上成立**——`initialize()` 对 `AuthError` 与任意
   `Exception` 一律转 fallback，**首次初始化就撞凭据错**的那条路上异常到不了元组，
   由写确认兜成 207。client 侧行为不在本卡可改面。
4. **未证明"返回 0 行 = 确定没写进去"**——`[]` 表达的是**未取得确认**；存在"已提交但
   拿不到确认"的路径（已提交 → 最终响应丢失 → 重试耗尽 → fallback → `[]`）。
   保守记 `success=False` 仍正确，但不能宣称"这条没写进去"。本函数不做幂等重试。
5. **未证明写进去的内容对不对**——门 1e 用 stub 造"返回 1 行"即判成功；
   只有真库门（2）校验字段值。
6. **未证明 `_write_lancedb` 那一半真的写进去了**——实测它**从不真写**（见台账 ⛔②）。
7. **未证明真库门的清理在任何情形下都删干净**——现已带 `RETURN count(er) AS deleted`
   回执断言（去掉它负控 NC-H 会红），但 `finally` 仍只保证"尝试"：写入后断连、
   进程被强杀、或删除发生在提交之前，都可能留数据。
8. **未证明整个 pytest 进程零网络**——`blocked=0, advisory=0` 只说明**账本覆盖的
   7691/7687 两个端口上零次连接尝试**，且 W4 自证探针跳过记账。
9. **未证明 `bolt://host:7692` 就一定是那个指定的测试容器**——白名单只保证端口范围，
   不做身份认证。
10. **未证明本卡两门之外的既有 integration 套件在打桩失效时不会连 7691**。
11. **未证明 `edges.py` 的 `neo4j is None` 守卫可达**——实测 `get_neo4j_client()`
    恒返 `Neo4jClient`，按死守卫处理但**禁碰**。

## 📌 台账待登记条目（≥4）

1. **T-EDGES 缺陷修复**：`execute_query` 恒 `AttributeError` 穿透成 500 →
   修复 commit 链 `c9c73f57`…`a6f68241`（9 个 commit，地盘恰两文件）。
2. **⛔① 本卡引入并已自修的假绿（必须登记，因为它比原缺陷重）**：第一阶段接通
   `run_query` 打通了 JSON fallback 路径，使"Neo4j 宕机"从 500 变成 **200 谎报成功**；
   第二阶段用写确认判据修掉。⇒ **凡是"把一个恒失败的调用改成能跑"的卡，都要检查
   它打通了哪些此前不可达的分支。**
3. **⛔② `_write_lancedb` 从不真写 LanceDB**（实测存档
   `lancedb-never-writes-probe-20260915T183820.txt`）：`LanceDBClient.add_documents`
   是 `async def`，而它用 `await asyncio.to_thread(client.add_documents, ...)` 调 ——
   `to_thread` 只在线程里**调用**它拿到协程对象就返回，函数体一行不执行、也不抛异常
   ⇒ 恒返 `WriteStatus(success=True)` 而零写入。**双写端点的另一半是假的。**
   该函数是卡文 §三 明令禁碰的面 ⇒ **建议第十五批立卡**（正确写法是直接
   `await client.add_documents(...)`，不经 `to_thread`）。
4. **⛔③ `Neo4jClient.initialize()` 吞掉部署错误**：对 `AuthError` 与任意 `Exception`
   一律转 JSON fallback ⇒ 凭据/配置坏了的信号被降级成"写未确认"。建议另立卡。
5. **BoltError 族逃逸面**：`neo4j._exceptions.BoltError` 与 packstream 裸
   `ValueError`/`struct.error` 未覆盖；要覆盖须引私有模块，本卡不引。
6. **`chat.py:344` 的注释不实**：称 `ServiceUnavailable` 是 `RuntimeError` 子类，
   实测它继承 `DriverError ← GqlError ← Exception`。别处的既有假注释，登记。
7. **卡文判据更正三条**（见 §4-A"卡文口径更正" 2/3/4）：F401 验伪锚 → F821；
   负控还原源不得用 `git show HEAD:`；塞 openapi 的是 `spec-sync-flat`。
8. **⛔ 卡文 H1 前提不成立**（§4-A 灰框）：建议回写卡文，免得后人照抄错前提。
9. **W4 豁免面巡检移交**：`tests/integration/**` 默认只记账不拦 ⇒ 任何打桩失效的
   integration 门都可能真连现网。本卡两门已加注入锚；全仓其余是否同风险 = 巡检项。
10. **G-TEST-GAP**：既有 `test_edge_rationale_fallback.py` 实测 9 处整体 patch 掉被测函数
    `_write_neo4j_triplet`，使本缺陷对既有套件不可见；本卡新增 17 格补盲。
    既有 9 处是否改造 = 另立卡（本卡禁碰该文件）。
11. **`ConnectionAcquisitionTimeoutError` 的归属待裁**：现按 500 处置（我方缺陷），
    但它也可能只是正常慢查询占满连接池。Codex r6 L1 点名它最值得重新裁定。
12. **`LEFTHOOK_EXCLUDE=spec-sync-flat` 使用登记**：六次 commit 用了它（仅为挡住 hook
    越界改 `openapi.json`）；⛔ 全程未排除 `python-typecheck` / `python-lint`。
13. **用户裁定登记**：2026-09-15「增加 codex 的审查轮次继续来修」⇒ **D-15 的 5 轮上限
    在本卡被放开**，且授权突破卡文 §三 修 H1。
14. **新文件地盘放行 = 已批**（裁定 R-B14-8，手册 §一 T5 行已列）。
15. **真库门清理曾是静默空转**（本轮自查修复）：裸 `DETACH DELETE` 返回 `[]`，
    与「verifier 中途转 JSON fallback ⇒ 清理落 `else` 分支只 `logger.warning` 就返回 `[]`」
    **完全不可分辨** ⇒ 节点会永久滞留共享 7692 而无信号。已改带 `RETURN count(er)` 回执。
    ⇒ **通则：凡是"清理/删除"类语句，都要带回执并断言，否则它和空转长得一样。**
16. **写确认判据与 Cypher 末尾 `RETURN er.record_id` 绑定**（7692 实测：带 `RETURN` 返
    1 行、去掉返 0 行）⇒ 删掉那句 `RETURN` 会让每一次成功写入都被误判成失败。
    已补耦合锚（NC-G 证其有牙）。
17. **变异必须先证明落盘**：NC-H 首次因 `ruff format` 重排导致锚 `count=0` 未命中，
    那一跑的绿是未变异态。⇒ 变异脚本一律 `assert count==1` 并打印「变异已落盘」+ 前后 shasum。
