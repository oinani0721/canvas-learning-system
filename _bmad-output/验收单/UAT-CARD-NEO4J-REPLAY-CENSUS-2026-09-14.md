# UAT — CARD-NEO4J-REPLAY-CENSUS（Neo4j 离线暂存链零代码普查）

> 批次 `BATCH-2026-09-11-第十四批` · 车道 T6 第 1/3 张 · 日期 2026-09-14
> 绑定 `HEAD` = `081004834e37b1b0253cf81dc7b44e784646c934`（`08100483` = `B14_BASE`）
> census 文档：`_bmad-output/审查/2026-09-14-NEO4J-REPLAY-CENSUS.md`
> 证据目录：`_bmad-output/审查/evidence-neo4j-replay-census/`

---

## 1. 🎯 一句话目标

把「Neo4j 断线那段时间，系统本来想写进知识图谱、结果只能先堆在本地文件里的数据」逐条清点一遍，弄清楚每一堆数据**谁在写、谁在读、有没有人把它送回去、会不会无限长大**，并给出「哪些要接回去、哪些可以废掉」的清单，交给后面两张卡执行。

## 2. 📖 你的视角

作为一个每天用这套系统学习的人，我想知道**断网/数据库挂掉的那段时间，我的学习记录到底去哪了**，以便我不用担心「有些东西悄悄丢了而我永远不会知道」。

## 3. 🖥️ 交互流程

本卡是纯清点，不改动任何你能操作的界面。你的屏幕上不会有任何变化。
真正会让你看到变化的是后面两张卡：接回去（T6-B）之后，断线期间的记录会在恢复后自动补进知识图谱；封顶（T6-C）之后，这些暂存文件不会再无限长大，而且你能在页面上看到「还有多少条没补回去、最老的一条是什么时候」。

---

## 4-A. 🤖 Claude 已代验（技术证据）

| # | 判据 | 结果 | 证据 |
|---|---|---|---|
| 0 | 第 0 分钟自证：`pwd` / 分支 `card/t6-neo4j` / `HEAD=08100483` / `git status` 空 / venv + `.env` 在位 / pyright 在位 / 红基线 `grep -vc '^#'` = **64** | ✅ | `evidence-…/step0-selfcheck-20260914T195007.txt` |
| 1 | 孤儿 `recover_failed_writes` 非测试 call = **0**（调用形态枚举 stdout 空）；全命中归类 3 行（`failed_writes_constants.py:6` 注释 / `memory_service.py:506` 注释 / `:2687` def）；**验伪锚** `_record_structured_outbox` 命中 `memory_service.py:1665` | ✅ | `judge1-orphan-recover-failed-writes-*.txt` |
| 2 | 孤儿 `sync_all_fallbacks` 非测试 call = **0**（仅 `memory_service.py:2690` docstring）；工厂 `get_fallback_sync_service` 非测试 call = **0**（仅 def `:656`）；**验伪锚** `get_memory_service(` 命中多处 | ✅ | `judge2-orphan-sync-all-fallbacks-*.txt` |
| 2x | 宽枚举补漏：裸形态 / 直接实例化 `FallbackSyncService(` / 反射 `getattr` / 字符串 四路全枚举，非测试 call 仍 = **0**（唯一非测试实例化 `:661` 在工厂内部，而工厂零 call） | ✅ | `judge2x-wide-callform-enum-*.txt` |
| 2y | `domains/canvas/gateway.py` 零 import 者（`-e` 多模式，避开 `\|` 非交替坑）+ **验伪锚** `from app.services.memory_service` 命中；`main.py` 中 `get_fallback_sync_service`/`sync_all_fallbacks`/`recover_failed_writes` **三名全缺席**（rc=1）+ **验伪锚** `backfill_vault` 命中 `:384/:392` | ✅ | `judge2y-gateway-and-red-baseline-*.txt` |
| 3 | `failed_edge_syncs` census = **9 行**（非测试 5 行：`failure_counters.py:25` / `traces.py:4,22` / `generate_regression_tests.py:4,155`；仅测试 4 行），零回灌消费者 | ✅ | `judge3-4-5-…*.txt` |
| 4 | 启动回填门三锚实测：`if _worker_graphiti is not None:` = **`:387`**（勘探稿 `:386` 系其上一行取值语句）、`backfill_vault` 调用 `:392`、跳过日志 `:404` | ✅ | 同上 |
| 5 | 双写开关二态：`config.py:477-479` field `default=False`；`backend/.env:85` 注释态；`backend/.env.example:226` 生效态；消费侧六处 `getattr(…, True)`（`:266/:363/:443/:460/:989/:998`） | ✅ | 同上 |
| 5x | 第三态排查：小写 alias `config.py:928-930` 同值不构成第三态；`model_config` `case_sensitive=True` + `extra="ignore"`（`:943`）⇒ 小写 env 写法静默失效（隐患登记）；e2e 与 unit 两条默认值测试契约分裂 | ✅ | `judge5x-6-…*.txt` |
| 7 | 第六条链 `failed_dual_writes.jsonl`：`DUAL_WRITE_DEAD_LETTER_PATH` 非测试**零使用**；唯一集成测试整类 `@pytest.mark.skip`（`:263`），所测方法已删（判据 13c 非测试 stdout 空） | ✅ | `judge7-8-9-…*.txt` / `judge13-14-…*.txt` |
| 8 | `/traces` 暴露面实测 `LOG_FILES` 仅 4 key；`failed_writes` / `canvas_events_fallback` / `neo4j_memory` / `failed_dual_writes` **四者未暴露**（rc=1）+ **验伪锚** `failed_edge_syncs` 命中 `:4/:22`。⚠️ **已暴露的两条也查不到**——读写路径错位（判据 28） | ✅ | `judge7-8-9-…*.txt` / `judge27-28-*.txt` |
| 10/11/15 | 写侧真实接线与 `request_id`：链 4 `canvas_service.py:508` **传** `request_id`；链 2 `memory_service.py:477` 传、`tips.py:623` **不传**（全文零 `request_id`）；链 3 九字段**无 `request_id`**。⛔ **v2 更正**：链 4 仍不可查——`request_id` 落盘与否不是决定因素，**路径错位**才是（判据 28） | ✅ | `judge10-…` / `judge11-12-…` / `judge15-…*.txt` |
| 16/17/20 | 有界性机制：链 3 清理代码在孤儿体内；链 7 `:297-298` 声明**不轮转**；`sync_all_fallbacks` 早退 `:64-65`/`:70-71`/`:73-74` ⇒ 离线期一行不清。⛔ **v2 更正**：链 5 **写侧本就有 10000 条上限**（`:97` + `:164-166`），v1 判据 16c 因固定行窗切在 `:162` 漏看（判据 27） | ⚠️→✅ | `judge16-…`（已被 `judge27-28-*.txt` 更正） |
| 18/19 | 第七条链 `learning_memories.json` + 全域 `data/` 三形态总扫 + **验伪锚**（应命中已知 5 条，实测 5）。⛔ **v2 更正**：三形态**不完备**——Codex 以 `event_bus.py:47-49` 变量拼接举出第 8 条，故不宣称全集（§8.7） | ⚠️→✅ | `judge18-19-…*.txt` / `judge31-*.txt` |
| 7'(地盘) | 零代码地盘门：非 `_bmad-output` 改动 = **0**；禁改清单六文件改动行数逐个 = 0；**验伪锚** `_bmad-output` 改动 20 行（证明 status 非恒空） | ✅ | `judge7-territory-gate-*.txt` |
| 9'(pyright) | `pyright app` = **`0 errors, 81 warnings, 0 informations`**（本卡零代码，与 `B14_BASE` 同，未带红） | ✅ | `judge9-pyright-and-lancedb-path-*.txt` |
| 10'(只读) | 现网只读门：现网 `backend/data/lancedb` / `backend/data` / `canvas-vault` 三处 `-newer sentinel` = **0**；**验伪锚** 本卡 evidence 目录 = 20（证明 `-newer` 判据非恒零） | ✅ | `judge10-readonly-gate-*.txt` |
| 8'(单测) | `tests/unit` 目录级 nodeid 口径 diff（跑法与基线文件头逐字一致） | 见 §4-A.1 | `unit-close-*.txt` |
| 27–32 | **Codex 12 条意见逐条独立实测复核**：HIGH-1 链5 上限 / HIGH-2 回灌器能力不等价 + UI 不可见 / HIGH-3 跨 vault 归属 / HIGH-4 路径错位 / HIGH-5 回源不可统一断言 / HIGH-6 死信缺三字段 / MEDIUM-7 第8条候选 / 8 装载前提 / 9 地盘不可机械收窄 / 10 链1 有运行时读 / LOW-11,12 —— **全部成立，零误报** | ✅ | `judge27-28-*.txt` / `judge29-30-*.txt` / `judge31-*.txt` / `judge32-*.txt` |
| 25/26 | 孤儿历史（`59586af1` 摘除 / `daa9fd37` 关默认，逐字复证）+ 链 E 活范式（`main.py:216` 真实接线） | ✅ | `judge25-26-*.txt` |
| 21–24 | 链3 三个写者 + 链2 触发前提 + 链1 写侧全路径 + 链5 六门形态 | ✅ | `judge21-22-*.txt` / `judge23-*.txt` / `judge24-*.txt` |
| 7''(commit 后地盘门) | ⛔ **此前该判据两侧同一 commit 恒空、不成立**；commit 后实跑：`diff 08100483 HEAD -- . ':(exclude)_bmad-output'` = **0 行**；36 个变更文件**全部**在 `_bmad-output`（总数=占比数相等）；禁改六文件逐个 = 0；并实证 `':!_bmad-output'` 本机报 `Unimplemented pathspec magic`（协议 §1 教训实证而非照抄） | ✅ | `judge7pp-post-commit-territory-gate-*.txt` |
| 33(存档卫生) | **口径更正**：原判据用 `grep 'stderr'` 匹配子串，与主张「`*.stderr*` 不入库」不等价（历史合规 `.txt` 假阳 3 条）。正确口径下入库 `*.stderr*` = **0**；**验伪锚** = 工作区确有 1 个 `.stderr`（355 KB）被 `.gitignore:264` 拦下 ⇒ 非「无此类文件」的空洞通过 | ✅ | `judge33-*.txt` |
| 11'(Codex) | Codex `gpt-6-astra` + `ultra` 复核（零代码卡 1 轮） | 见 §4-A.2 | `codex-review-CARD-NEO4J-REPLAY-CENSUS.md` |

### §4-A.1 `tests/unit` 目录级结果 ✅ 完全一致

跑法与基线文件头逐字一致（R-B14-3）：
`cd backend && PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/unit --ignore tests/unit/test_deploy_vault_sh.py -q -p no:cacheprovider`

| 项 | 值 |
|---|---|
| **跑成自证**（⛔ 防 127/收集失败假绿） | 汇总行计数 = **1**；原文 `= 35 failed, 5077 passed, 48 skipped, 23 xfailed, 171 warnings, 29 errors in 402.83s (0:06:42) =`；`tail -1` = `rc=1` ∈ {0,1} ✅ |
| `base.nodeids` | **64** 行（= 红基线 `grep -vc '^#'`） |
| `close.nodeids` | **64** 行（35 failed + 29 errors = 64，与基线逐条对应） |
| `diff base close` | **完全一致**（`diff_rc=0`） |
| 新增红 `>` | **0** ✅（任何 `>` = 阻断） |
| 消失红 `<` | **0**（本卡零代码，预期为空，非「只许 `<`」的放行面） |
| 两条 `TestStartupIntegration` | 仍在 `close.nodeids` ✅ —— 与「本卡不改代码」一致；T6-B 接通后应转绿（64 → 62） |

⛔ 口径声明：`close.nodeids` = 64 行非空，因此**不触发**「close 为 0 而 base 为 64 ⇒ 判没跑成」的假绿陷阱。
存档：`unit-close-20260914T195635.txt`（原始输出）/ `judge8-unit-diff-20260914T200343.txt`（diff 判据）/ `base.nodeids` / `close.nodeids`

> 副作用如实记录：目录级测试在**车道树**创建了空目录 `backend/data/lancedb`（实测 mtime `Sep 14 19:57`），
> 属测试副作用、非现网写入，且被 `.gitignore` 覆盖不入库；现网只读门（判据 10'）仍为 0。

### §4-A.2 Codex 复核结果 ✅ 1 轮（零代码卡）

命令（协议 §2 固定）：`codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" …`
存档：`_bmad-output/审查/codex-review-CARD-NEO4J-REPLAY-CENSUS.md`（首部三字段齐，`.stderr` 不入库）

| 项 | 值 |
|---|---|
| 模型 / reasoning / 版本 | `gpt-6-astra` / `ultra` / `codex-cli 0.153.3`（会话头自证 `.stderr:4` / `:7` / `:11`） |
| 审查绑定 | `081004834e37b1b0253cf81dc7b44e784646c934`（= HEAD，本卡零代码 ⇒ 审 SHA = HEAD） |
| 审查对象冻结 | ✅ census mtime `19:57:49` **早于** codex 启动 `19:58:03` ⇒ 审查期间文档逐字未变 |
| 裁定 | **BLOCKER 0 / HIGH 6 / MEDIUM 4 / LOW 2** |
| 本卡复核 | **12 条逐条独立实测（判据 27–32），全部成立，零误报** |
| 整改性质 | 均为 **census 文档事实错误**；本卡零代码 ⇒ 无代码整改（D-32 纯文档尾巴不占轮次、不重置） |
| 落地 | census **v1 → v2** 重写，§九「来源 A」逐条对应 |

**Codex 指出的 6 条 HIGH（全部实测成立，均已修正）**：

1. 链 5 **写侧本就有 10000 条上限**（`canvas_service.py:97` + `:164-166`），v1「有界机制全在孤儿体内」错误 —— 根因是 v1 判据用固定行数窗口读函数体，边界切在 `:162 events.append(event)`
2. 链 3 漏两个写者；且新回灌器 `:314/:319-321` 对无 `concept` 的条目 `return False` ⇒ **结构化 outbox 条目被静默跳过**；「UI 可见」过强（entry 无 `user_id`，`:805-806` 按它过滤）
3. **跨 vault 归属风险**未登记：`fallback_sync_service.py:623-625` 代码自陈「切换 vault 后旧条目归入新 active vault」
4. `/traces` **读路径与死信写路径错位**：写 `backend/data/`（实存 763 B）vs 读 `backend/app/data/`（目录不存在）⇒ 已暴露的两条链也查不到
5. 链 2 死信来源**不限 markdown**（会话归档正文来自请求消息）⇒「回源重生成」不可统一断言
6. 链 4 死信**缺 `from_node_id`/`to_node_id`/`edge_label`** ⇒ 不足以重放

**Codex 给出的 7 项「核对通过」**：两孤儿及工厂零调用（其独立做了全标识符归类 + 只解析不导入的 AST 检查）、枚举正则不具通用完备性但未发现漏网调用、无缺字段第三态、启动三定位点 `:387/:392/:404`、链 7 运行时存储职责成立、离线早退跳过全部清理、链 6 当前无生产写入接线。

> 本卡另有 **11 条自查修正**（对照 U11 审计原文 + 追加判据 21–26），见 census §九「来源 B」；
> 其中最重的一条：**孤儿不是「从未接线」，而是 `59586af1`(2026-03-26 09:30) 摘除、`daa9fd37`(09:35) 关默认** —— T6-B 是还原不是新设计。

---

## 4-B. 👤 你来验

- [ ] 我打开那份清单文件（`_bmad-output/审查/2026-09-14-NEO4J-REPLAY-CENSUS.md`）→ 我看到一张表，把断线期间数据会堆到的**七个地方**一行一行列出来，每行都写清楚「谁在写、谁在读、有没有人送回去、会不会无限长大」→ 我感觉**心里有底**，不再是一团模糊的「可能丢了点东西」。
- [ ] 我往下读到「处置表」→ 我看到每一堆数据都有一句明确建议：哪几堆要接回去、哪一堆已经是废的可以删、哪一堆**千万不能乱清理**（清了会把我正在用的学习记录一起删掉）→ 我感觉**接下来两步该做什么是清楚的**，而不是一个笼统的「以后再说」。
- [ ] 我读到清单里说「有一堆数据，页面上那个查询框其实永远查不到它」→ 我看到它解释了原因（存的地方和找的地方对不上），并且写明这件事要在后面那张卡里先修好 → 我感觉**它没有把「有个查询入口」当成「能查到」来糊弄我**。
- [ ] 我读「本卡未证明什么」那一节 → 我看到它老老实实写着「还没去数你电脑上实际堆了多少条、多久以前的」，也写着「不敢保证这就是全部」→ 我感觉**这份清单没有夸大**，说到哪算到哪，我可以信它。

> 一句话总结（felt-sense）：系统在断网那段时间里，原本想补记的学习数据其实都堆在几个文件里没回灌回知识图谱——我现在有了一份清清楚楚的清单，知道哪些要接回去、哪些要封顶，接下来两步就照这张清单做，我感觉心里有底、不再担心数据悄悄丢掉。

---

## 5. 🚦 验收结果

- **通过** → 说「复核第十四批 T6」，主 session 接手复核后排 T6-B（接通）与 T6-C（有界 + 可观测）。
- **不通过** → 在下方批注区写下你觉得没讲清楚的那条链，我补测并更新清单（本卡零代码，改的只是文档）。

---

## 6. 📝 批注区

> [!question]+ 你的疑问写在这里
>

---

## 7. 🔗 技术 spec 引用

- 卡文：`…/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第十四批-goals/T6-A.md`
- 协议：`…/feature-obsidian-hybrid-dev/.claude/rules/card-batch-protocol.md`（§1 合并门 / §2 Codex / §2.1 存档首部 / §2.2 裁判落盘）
- census 文档：`_bmad-output/审查/2026-09-14-NEO4J-REPLAY-CENSUS.md`
- Codex prompt：`_bmad-output/审查/prompts/codex-prompt-CARD-NEO4J-REPLAY-CENSUS.md`
- 红基线：`…/feature-obsidian-hybrid-dev/_bmad-output/审查/evidence-b14/unit-red-baseline-08100483.txt`（64 条）

---

## 8. 本卡未证明什么（10 条）

1. **未证明现网实例的 `ENABLE_GRAPHITI_JSON_DUAL_WRITE` 真实取值** —— 只读车道树 `backend/.env` 与 `.env.example`，⛔ 未读现网 live vault 的 `.env`。且二态结论须附条件「在实际装载了该 `.env` 且无更高优先级覆盖的前提下」（Codex MEDIUM-8）。
2. **未证明七条暂存文件在现网已积压多少 / 最老多久** —— 只对现网目录做了 `ls` 与 `-newer` 计数，未读文件内容。
3. **未证明孤儿接通后的回灌幂等性与正确性** —— T6-B 的 7692 端到端门面（D-39）。
4. **未证明处置表的「接通」优于「退役」** —— 产品决策由 T6-B/C 落地。
5. **未证明 `getattr(…, True)` 在某配置路径下真会让有效默认变 True** —— 未穷举所有 `Settings` 装载路径。
6. **未证明 `DEAD_LETTER_STORE_FULL_BODY` 开启后全文落盘的隐私面** —— 只 census 开关位置。
7. **未证明这 7(+1) 条是全集** —— 判据 19 只覆盖三种路径拼接形态，**该前提已被 Codex 用第 8 条（`event_bus.py:47-49` 变量拼接）证伪**；更复杂的动态拼接 / 配置注入路径仍未覆盖。
8. **未证明第 8 条候选在单纯 Neo4j 断连时一定被写入** —— 已证生产注册与启动恢复入口存在，未证写入路径必经它（Codex 的限定，本卡采纳）。
9. **未证明 `_pending_failed_writes` 内存队列的实际丢失规模** —— 只证「仅 `cleanup()` 刷盘」这一代码事实，未统计崩溃频次与队列深度。
10. **未证明链 6 历史上从未产生过该文件** —— 结论限于当前源码（Codex 限定）。

## 9. 台账待登记条目（14 条，⛔ 台账只主 session 改，本卡不碰）

1. **R-09 Neo4j 离线暂存链零回灌消费者 + 无界坟场** → census 文档 `_bmad-output/审查/2026-09-14-NEO4J-REPLAY-CENSUS.md` + §六 处置表（接通 = T6-B、有界 = T6-C）。
2. **卡文六条口径更正全部复测通过 + 本卡新增四条更正**（census §七.2 #7-#10：链数 5→7；`sync_all_fallbacks` 同步三文件；链 2 写侧补 `:306`/`:311` 锚；链 4 真实写入点 `canvas_service.py:508`）→ 供 T6-B / T6-C 直接引用。
3. **启动门行号更正 `:386 → :387`** → 设计稿 §3「T6-B 只改 `:386-404`」应改为 **`:387-404`**，交主 session 集成期核 hunk。
4. **`canvas_service.py` 六处 `getattr(settings, …, True)` 与 config `default=False` 方向相反** → 登记隐患，修与否由 T6-B 裁。
5. **仓库已有两条常驻红测试为「孤儿未接线」报警**（红基线第 51/52 行 `TestStartupIntegration` 两条）⇒ T6-B 现成验收锚，接通后基线应 **64 → 62**。
6. **链 6 `failed_dual_writes` 为死代码**（写侧零接线 + 唯一测试 skip 且所测方法已删）→ 建议退役或明确接线，二选一。
7. **`app/domains/*/gateway.py` 门面模块疑似零 import 者**（本卡只实证 `domains/canvas/gateway.py`）→ G-PIPE 型死模块线索，超出本卡范围，仅登记。
8. **Codex 存档 / 绑定 SHA / 计数（1 轮）**：`_bmad-output/审查/codex-review-CARD-NEO4J-REPLAY-CENSUS.md`，绑定 `081004834e…`，**BLOCKER 0 / HIGH 6 / MEDIUM 4 / LOW 2**，12 条经本卡实测全部成立零误报，均为文档修正（零代码）；`tests/unit` diff 与基线完全一致（64/64，新增红 0）；`pyright app` = 0 errors。
9. **⛔ `/traces` 读写路径错位**（`failure_counters:25` → `backend/data/` vs `traces.py:17` → `backend/app/data/`，后者目录实测不存在）→ T6-C 修暴露面前必须先统一路径，否则修了也查不到。
10. **⛔ 跨 vault 归属风险**（`fallback_sync_service.py:623-625` 代码自陈，移交 G2-2）→ T6-B 接通即触发，须先决定：补 vault 字段 / 按 vault 过滤 / 接受并告知。
11. **⛔ 两个回灌器能力不等价** —— 新回灌器跳过 `kind=knowledge_entity` 结构化条目（`:314/:319-321`），只有旧 `recover_failed_writes:2735` 有该分支 ⇒ T6-B 只接 `sync_all_fallbacks` 不足以覆盖链 3。
12. **⛔ 孤儿是被摘除的不是从未接线**（`59586af1` 2026-03-26 09:30 摘 main.py 调用与离线告警；`daa9fd37` 09:35 关 config 默认）→ T6-B 是**还原**，原始形态含 `timeout=60.0` 与三日志分支，可作实现基线。
13. **链 3 写者 3 `_flush_pending_failed_writes:2854` 只在 `cleanup()` 刷盘** → 进程被 kill 即丢，属 T6-B/T6-C 之外的第三类缺口，需单独决策。
14. **第 8 条候选链 `backend/data/outbox/events.jsonl`**（`event_bus.py:47-49`，`main.py:216` 真实接通，实存 383 B）→ 唯一活着的「暂存↔启动重放」闭环，T6-B 可照抄 `main.py:212-219` 形态；其自身缺口：Tier-1 事件（含 `SCORE_SUBMITTED`）结构上永不进 outbox。
