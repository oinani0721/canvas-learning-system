# UAT — CARD-RED-TRIAGE（tests/unit 既有红 247 条逐 nodeid 定性）

> `[BATCH-2026-09-05-第十二批 / CARD-RED-TRIAGE]`
> 车道 `card-y6-testhygiene`（分支 `card/y6-testhygiene`），
> 开工 HEAD = Y6-B 末 commit `368b145a`。**纯分析卡，一行代码不改。**
> 证据目录 `_bmad-output/审查/evidence-red-triage/`。日期 2026-09-06。
> 用户已裁（2026-09-05，D-10 按默认 = 甲：一张定性卡，零修复）。

## 〇 这张卡在干什么（一句话）

后端单元测试里有 247 个测试**一直是红的**（不是今天坏的，是历史欠账）。
本卡把它们逐个贴上标签——**分清哪些是「灯坏了」（测试自己过时/写错），
哪些是「真有问题」（实现真的回归了）**——并据此产出第十三批的修复卡草案。
**一行代码都不改**，改法留给第十三批。

---

## 一 (a) 钉分母

**不自建基线**，用设计稿 §0 文件：
`.../feature-obsidian-hybrid-dev/_bmad-output/审查/evidence-b12/unit-red-baseline-03ac8bf8.txt`

| 项 | 值 |
|---|---|
| 分母 | **247 nodeid**（FAILED **209** / ERROR **38**）/ 63 文件 |
| 口径 | 只收 `^(FAILED\|ERROR) tests/` 行，剥 ` - <消息>` 尾巴，sort |
| 勘误 | 复核报告的「298 / 289」是**含 42 行日志噪音的行数**，不是分母 |

### 卡文 §〇 的假设分类在 247 基线上逐项复算 —— **全部对上**

| 类 | 卡文声称 | 本卡实测 | |
|---|---|---|---|
| A1 裸 TestClient | 41 / 6 文件 | **41** | ✅ |
| A2 鉴权负控 | 9 / 3 | **9** | ✅ |
| B vault 作用域 | 41 / 5 | **41** | ✅ |
| C1 dual-write 退役 | 49 / 8 | **49** | ✅ |
| C2 契约演进 | 24 / 3 | **24** | ✅ |
| E agents 模板 | 9 / 1 | **9** | ✅ |
| 残余 | 74 / 37 | **74 / 37** | ✅ |
| **合计** | 247 | **247** | ✅ |

其余复算同样对上：
- **B 类的 3 条 FAILED**（非 ERROR，卡文要求单独定性）精确命中卡文点名的三条：
  `test_agent_service_extraction.py::TestDebugAgentResponseLogging::test_config_has_debug_agent_response_field`、
  `test_story_30_10_idempotency.py::{TestBatchDeterministicEpisodeId::test_batch_id_format,
  TestDeterministicEpisodeId::test_id_format}`
- **残余 37 文件**的条数分布逐项对上（多条文件 15 个全中，各 1 条的 22 个文件数也对）
- **vault/group_id 簇 9 条 / 5 文件**对上；`test_lancedb_vault_isolation` 在基线中 **0 条**
  （已由 Z4-A `c7799298` 清）✅

（下列各节在裁判跑完后补齐）

## 二 (b) 247 条四元组分诊表

**`_bmad-output/审查/2026-09-05-第十二批-tests-unit-红基线分诊-247.md`**（501 行）

机器判据：表体 **247** 行；表内 nodeid 集合与基线 `diff` **为空**；
**实现位置「未定位」= 0 条**；**真实现回归 22 条全部带嫌疑 sha**。

列序按卡文：`kind nodeid | 测试 file:line | 断言原文摘要 | 现行实现 file:line |
类别 | 失败身份 | 依据 sha`。改类的行标 `⟳`。

## 三 (c) 假设逐条核实 —— **勘探的分类只有约一半成立，247 条里 119 条改类**

| 勘探假设 | 实测 | 判定 |
|---|---|---|
| A1 单一根因 41 | **拆两类**：A1-auth 31（+A2 改归 6 = 37）/ A1-sentinel 10（+残余 2 = 12） | **不成立** |
| A2 鉴权负控 9 | **3 条**；嫌疑 commit 更正 `c9bb6c9a` → **`f718d040`** | **部分成立** |
| B vault 作用域 41 | **整类证伪，归零** | **不成立** |
| C1 dual-write 49 | **42 条**（7 改类）；「引用已删 API」实测 **25** 非 28 | **大体成立** |
| C2 契约演进 24 | **109 条**（B 38 + 残余 43 + C1 4 涌入） | **成立但会膨胀** |
| E agents 模板 9 | 9 条维持，但**须拆三档**（1 条真生产缺陷） | **成立需修正** |
| 残余 74「根因未明」 | **无一条落「根因未明」** | **不成立（好的方向）** |

### 三处最重要的推翻

**① B 类整类证伪（41 条）** —— 卡文 §〇.17 的根因锚错了，我先前的判断也错了。

```
grep -c VaultScopeUnresolved  <整份 3.9MB 日志>  =  0
36 条 setup ERROR 的 traceback 都走到 memory_service.py:381
而 :369-373 的 Context().run(require_read_group, None, …) 在 :378 之前
⇒ 能走到 :381 恰恰**反证**作用域解析成功返回了
```

真根因：`803793c5` 给 `initialize():282` 加了
`await self.neo4j.get_all_recent_episodes()`，10 个 `mock_neo4j` fixture 的
`MagicMock()` 只桩了三个方法 ⇒ 新方法的自动属性**不可 await** → `TypeError`；
生产 `except` 只捕 `(RuntimeError, ConnectionError, TimeoutError)`（`:431` 注释明写
**刻意不放宽**）⇒ 穿透。**真实 `Neo4jClient` 有该 async 方法，生产无缺陷。**

> **我错在哪**：只读代码结构（`Context().run` 在 try 之外、注释说会抛）就推断
> 「它就是这样红的」。**代码能那样失败 ≠ 它就是那样失败的。**
> 读代码得到的是**可能的机制**，读日志得到的才是**发生的事实**。

**② A1 拆两类（41 条）** —— 见 §十.3；日志里 `security.py:126` 拒因
vs `live Neo4j port connect attempted`，两族泾渭分明。

**③ A2 的 6 条改归 A1-auth + 嫌疑 commit 更正** —— 见 §十.10。
卡文「空 key 是故意的负控、塞 key = 毁负控」对那 6 条不成立：
真负控是另外三条，**本次全部 PASSED、根本不在红基线里**。

### E 类须拆三档（否则会把真缺陷一起抹掉）

| 档 | 模板 | 依据 |
|---|---|---|
| **真生产缺陷** | `hint-generation.md` | `git log --all --diff-filter=A` **零命中** ⇒ **全部 git 历史中从未存在**；而调用点已上线（`verification_service.py:3032` → … → `gemini_client.py:225` 真读盘 → `FileNotFoundError` → 被 `:3057` 吞成 warning → 写死兜底）⇒ **AI 分级提示自诞生起就永久静默降级** |
| 真但轻 | `canvas-orchestrator.md` | 无调用点；只让 `/agents/health` 恒报 degraded（探针如实报告） |
| 灯坏 | 其余 5 个 | 不在 `AgentType` 枚举、不在 health 期望表；只被指标标签白名单/映射表键当字符串引用 |

**同组假绿**：`test_agent_template_not_empty` 18 项全 PASSED，其中 7 个缺失文件是
**真空通过** —— `:79` 的 `if filepath.exists():` 让文件不存在时**一条断言都不执行**。
⇒「非空」这道门对它最该管的 7 个文件**完全失明**。

### ⛔ 三条会让下批「修错地方」的事实修正（分诊 agent 实测）

**① 哨兵文案与实况不符（A1-sentinel 12/12 都不符）**
文案硬编码「异常被 `app/main.py` 的 lifespan try/except 吞掉了」
（`tests/support/live_port_guard.py:1088`），但那些 fixture 是**裸 `TestClient(app)`、
没用 `with`** ⇒ **starlette 根本不跑 lifespan**。
真正吞异常的是端点自己的 `except`（`system.py:72-75` / `kg_health.py:72-77`）。
⇒ **照文案去关 lifespan 会修错地方。**

**② 「哪个 nodeid 红」是收集顺序的函数，不是用例性质**
`get_neo4j_client()` / `get_mastery_store()` 都是**进程级单例**：
第一个走到该路径的用例付掉那唯一一次真连接，其余复用已进 fallback 的实例故全绿。
日志进度条印证：`test_mock_degradation_transparency.py F......................`、
`test_review_mode_support.py F..............` —— **两文件都只红第一条**。
⇒ 按 nodeid 逐条修会「换个顺序又红到别人头上」。
**这解释了本批另一处实测到的「W4 哨兵归属随时序漂移」的机制。**

**③ A1-auth 的 31 条不是「修一处清 31」**
这些断言的**业务逻辑一次都没执行过**（请求止于 `chat.py:48` 的 router 级依赖），
所以「A1-auth 是唯一根因」只对**当前这次红**成立。
`test_enrich_context_vault_isolation` 的 7 条从命名看是 vault 隔离面，
**auth 解开后可能翻出第二层红**。下批应预期「修完 auth 需重跑再分类」。

> 附带登记（文档与实现自相矛盾）：`chat.py:42-43` 的旧矩阵注释、
> 以及 **`security.py:13-22` 的模块 docstring 矩阵表**
> （`| True | empty | any | allow + structured warning |`）
> **与它下面 60 行的实现自相矛盾**。两处均为注释，登记不阻断。

## 四 (d) 真实现回归 —— **22 条**，全部带嫌疑 sha 与实现位置

嫌疑 sha **高度集中**，说明这不是零散问题，而是**几次「收窄异常捕获」改动的共同后果**：

| 嫌疑 sha | 条数 | 形态 |
|---|---|---|
| `a9304c69` | 多数 | 把多处 `except Exception` **收窄成具体异常元组**，测试注入的裸 `Exception` 逃逸 ⇒ 降级路径不再兜底 |
| `3d10a02b` + `d4823ef9` | 5 | `search_error_memories` / `search_memories` 的形参与字段被删后**重写未恢复**（`node_id` 过滤、排序、metadata） |
| `e6fbd337` | 3 | 给 `get_learning_history` 的 fallback 合并加了 `user_id` 等值过滤，而写侧 `_record_failed_write` **从不写 `user_id`** ⇒ Story 38.6 AC-4「用户永远看不到断档」在生产上**恒失效**（端点 `user_id` 是必填 Query） |
| `4867dd09` / `1768c19d` / `4236b12e` | 其余 | 见分诊表逐条 |

⚠️ 本卡**只有嫌疑 sha、无 bisect 实证**（见 §九.3）。
RED-R 卡的任务就是逐条确认，确认后再分派修复。

## 五 (e) vault/group_id 簇 9 条 —— **8 条「都不是」+ 1 条真事**

卡文要求三选一（与 B 同源 / 与 C2-d 同源 / 都不是），实测：

| 文件 | 条数 | 结论 |
|---|---|---|
| `test_vault_notes_group_filter` | 4 | **都不是** —— `43294c38` 把隔离**下沉到表名层**并删掉了 metadata 过滤块；不碰 `require_read_group`（是 LanceDB 检索器不是 Cypher 读侧），也不涉 D16 冒号格式 |
| `test_context_enrichment_2hop` | 2 | **都不是** —— `5d2b95ba`（S34 / G-FAKE-001 改名治理）把形参 `include_graphiti` 更名为 `include_learning_memory`，全仓 `app/` 下前者 0 命中 |
| `test_subject_isolation` | 1 | **都不是** —— 虽然 `subject_config.py` 正是 D16 的 `build_vault_group_id` 所在，但这条不涉冒号格式 |
| `test_wave5_stageb_continued_vault_id_injection` | 1 | **都不是** —— `d14b50ab`（第十批 CARD-G4-4a）把 helper 符号取代了 |
| `test_vault_doc_roles` | 1 | **⛔ 都不是，且这条红是真事** —— 见下 |

`test_lancedb_vault_isolation` 3 条：**已由 Z4-A 清，基线中 0 条**（表外单列，见分诊表附录）。

### ⛔ `test_live_vault_enforce_clean` —— 门是对的，红的是真事

live vault 的 `canvas-vault/backups/` 目录**建于 2026-09-05 10:52**，
内含 `fsrs_bridge.py.pre-deploy-2026-09-05T1052.b…`
—— 即**有人在那个时刻部署了 `fsrs_bridge`**（与本批「Y1-A 合入 = 当场授权部署」那条线对上）；
而 `backend/scripts/vault_doc_roles.yaml` 的角色表里**没有任何匹配 `backups/` 的
`dir_glob` 条目**（`:79 total_files: 324`）。

⇒ 这**不是灯坏了**，是 live vault 出现了角色表未登记的新目录。
**归「新」类，转本批部署线处置**，不进 RED 系列。
## 六 (f) 第十三批卡草案 —— **10 张**（卡文要求 ≥7）

**`_bmad-output/审查/2026-09-05-第十二批-RED-第十三批卡草案.md`**（约 300 行）

| 卡 | 条数 | 要点 |
|---|---|---|
| `CARD-RED-A1-auth` | 37 | 原 31 + A2 改归 6 |
| `CARD-RED-A1-sentinel` | 12 | **本次新拆**；合成会拿 auth 修法去修哨兵的红 |
| `CARD-RED-A2` | 3 | 红在**配置层**不在鉴权层；嫌疑 commit 更正 `f718d040` |
| `CARD-RED-B` | 0 | **前提已证伪**，本节说明为什么不要按原计划开 |
| `CARD-RED-MOCKFIX` | 36 | 取代 RED-B：fixture 桩没跟上 `initialize()` 的依赖演进 |
| `CARD-RED-ENVDEP` | 3 | **新设一类**：pytest-mock 未声明 + 测试读真 `.env` |
| `CARD-RED-C1` | 43 | 三子类分开（引用已删 API 25 / 桩值矛盾 3 / 锁废弃契约 14） |
| `CARD-RED-C2` | 109 | **建议再拆五张**，否则一张卡要处理四种不相干的东西 |
| `CARD-RED-E` | 9 | 拆三档；含 1 条真生产缺陷 + 1 处假绿 |
| `CARD-RED-R` | 22 | 真实现回归的**逐条确认**（本次只有嫌疑 sha、无 bisect） |

机器判据（卡文裁判 6）：`^### CARD-RED-` **10** ≥7；
`card_id` 8 / `完成条件` 10 / `裁判命令` 9 / `禁做` 9 / `估时` 9，**各 ≥7**；
三条硬约束（`authed_client` / `__unit_fixture__` / `strict=True`）**在场** ✅

> **三条硬约束按卡文原样保留**，并各自加了实测依据：
> RED-A1 的「禁 autouse / 禁 `os.environ` 全局注入」、
> RED-B（现为 MOCKFIX）的「不得放宽生产 `except` 元组去吞 `TypeError`」、
> RED-C1 的「无替代覆盖不许删，改 `xfail(strict=True)` 作跨卡交接」。

## 七 裁判输出

原始输出全部落 `_bmad-output/审查/evidence-red-triage/`。

| # | 裁判 | 结果 |
|---|---|---|
| 1 | 开工目录级 + 失败身份 | `209 failed / 4609 passed / 38 errors`，rc=1；log 3.97 MB（`unit-run-open-20260906T104910.txt`） |
| 1b | 开工 vs 基线 nodeid diff | **完全为空**（`<` 0 行、`>` 0 行）✅ |
| 2 | 分诊表机器判据 | 表体 **247** 行；表内 nodeid 集合与基线 `diff` **为空** ✅ |
| 4 | 纯分析门 | `git diff --stat 368b145a HEAD -- . ':(exclude)_bmad-output'` **空**、rc=0；`git status --porcelain -- backend` = **0** ✅ |
| 3 | 失败身份可追溯（随机抽 10 条） | **10/10** 能在日志里定位到 traceback 块 + summary 行；agent 给的 identity 均带具体日志行号（如 `日志 L2592-2596`）。种子固定 `20260906`，可复算 ✅ |
| 5 | 收工目录级 + 开工/收工 diff | 收工红 **247** 条；`diff red-open.txt red-close.txt` **为空** ⇒ 本卡未动树 ✅ |
| 7 | Z4-A 差集 9 条对账 | `c7799298` 确实改了三文件；三文件在 247 基线中**全为 0 条** ✅ |

### 失败身份提取（卡文硬要求：必须来自 `-rA --tb=short`，不得读代码推断）

分类器写了三版，**两次被自己的判据坑到**，如实记录：

| 版本 | 问题 | 后果 | 修法 |
|---|---|---|---|
| v1 | 块头正则写 `_{4,}` | **静默漏 61/247 条** —— 测试名长时 pytest 把填充下划线压到只剩 **1 个**（`_ TestX.test_y _`） | 改 `_+ … _+` 并要求名字非空 |
| v2 | HTTP 状态码判据是裸 `\b503\b` / `\b403\b` | 在 traceback 别处误命中 —— 把一条**时间戳断言**判成了 403 | 绑定状态码上下文（`status_code == N` / `assert N ==` / `[N]` / `HTTP N`） |
| v3 | — | **247 条全部找到 traceback 块** ✅；14 条未提取到 `test file:line`（多为 setup ERROR，traceback 在 fixture 里） | — |

> v2 收窄后 503 从 40 降到 35，我一度怀疑**误拒**（A1-auth 31 + A2 9 = 40）。
> 双向验证后确认**不是误拒**：那 5 条的真实身份确实不是裸 503 ——
> 2 条是 `KeyError`（测试没先断言状态码就取键，但日志里有 503）、
> 3 条是 `assert 'Internal API…' == 'Neo4j unavailable'`（状态码对、detail 变了）。
> ⇒ 这恰恰印证了本卡的**两维度设计**：失败身份 ≠ 根因类别。

### 卡文六类假设的复算（全部对上）

| 类 | 卡文 | 实测 | | 类 | 卡文 | 实测 | |
|---|---|---|---|---|---|---|---|
| A1 | 41/6 | **41** | ✅ | C1 | 49/8 | **49** | ✅ |
| A2 | 9/3 | **9** | ✅ | C2 | 24/3 | **24** | ✅ |
| B | 41/5 | **41** | ✅ | E | 9/1 | **9** | ✅ |
| 残余 | 74/37 | **74/37** | ✅ | 合计 | 247 | **247** | ✅ |

B 类的 3 条 FAILED（非 ERROR）精确命中卡文点名的三条；
残余 37 文件的条数分布逐项对上；vault 簇 9 条/5 文件对上；
`test_lancedb_vault_isolation` 在基线中 0 条（已由 Z4-A 清）。

## 八 DoD-3

### 4-A Claude 已代验（技术项）

| # | 项 | 结果 |
|---|---|---|
| 1 | 钉分母（不自建基线） | ✅ 用设计稿 §0 文件，247 nodeid |
| 2 | 卡文六类假设复算 | ✅ A1 41 / A2 9 / B 41 / C1 49 / C2 24 / E 9 / 残余 74 **逐项对上** |
| 3 | 开工目录级 vs 基线 diff | ✅ **完全为空**（247 = 247 逐 nodeid 相同） |
| 4 | 失败身份来自 `-rA --tb=short` | ✅ 247 条**全部**找到 traceback 块 |
| 5 | 分诊表机器判据 | ✅ 表体 247 行；nodeid 集合与基线 diff 为空 |
| 6 | Z4-A 清掉 9 条对账 | ✅ 三文件确在 `c7799298` 中，基线里全 0 条 |
| 7 | 纯分析门 | ✅ `git diff 368b145a HEAD -- . ':(exclude)_bmad-output'` 空、rc=0；`status -- backend` = 0 |
| 8 | 六类根因锚交叉验证 | ✅ 我本人逐个核过（见 `独立核实-*.md`），与分诊 agent 独立 |
| 9 | A1 拆分的实测依据 | ✅ 日志里 `security.py:126` 拒因 vs `live Neo4j port connect attempted` |
| 10 | E 类数字疑问解开 | ✅ 9 = 7 参数化 + 2 独立断言；AST 精确计数 18 项 |
| 11 | 第十三批草案 | ✅ **8 张**（因 A1 拆分，多于卡文要求的 ≥7） |

### 4-B 你来验（一句话，零技术词）

> **无变化 —— 把一直亮着的旧红灯逐个贴上标签，分清哪些是灯坏了、哪些是真有问题。**
>
> 你不需要做任何操作，这张卡一行代码都没改。
>
> 后台的自动检查里有 **247 项一直是红的**，已经红了很久 —— 不是今天坏的，
> 是过去改东西时留下的欠账。红灯太多，就没人看得出哪盏是真警报了。
>
> 本卡把这 247 项**逐个查了一遍**，按「为什么红」分成几堆：有些是检查项自己过时了
> （被检查的功能早就改了名或退休了，检查还照着老样子找）；有些是检查方式的问题
> （它连的是正在运行的真数据库，被安全拦截挡住了）；也有一小部分**可能是功能真的坏了**。
>
> 分完之后，下一批要修什么、按什么顺序修、每堆该用什么改法，就都有依据了。
>
> 感觉上应该是「什么都没发生」—— 这正是一张纯梳理卡该有的样子。
> 真正的变化会在下一批出现。

## 八.5 Codex round-1 逐条处置

存档 `_bmad-output/审查/codex-review-CARD-RED-TRIAGE.md`。
**BLOCKER = 0**（2 HIGH + 3 MEDIUM + 1 LOW）。
Codex 独立复算确认：**基线、日志、分诊表三个集合完全一致**（247 唯一 nodeid /
209 FAILED / 38 ERROR / 63 文件），247 条均找到失败块，改类实测 **119** 条。

| # | 级别 | 处置 |
|---|---|---|
| 1 | HIGH | **至少 5 条残余归 C2 但证据不足以排除回归** → **接受，已改判** |
| 2 | HIGH | **分派未闭合（新 9 条无接收卡 + C1 漏计 1）** → **接受，已补** |
| 3 | MEDIUM | nodeid 裁判缺运行完整性条件 → **接受，已改裁判命令** |
| 4 | MEDIUM | 三条硬约束不能判「全部在场」（B 已撤销） → **接受，见下** |
| 5 | MEDIUM | 开工→收工证据链未在读取面内 → **接受，已补路径** |
| 6 | LOW | 日志行号晚标 3 行 + 草案前后冲突 → **接受，已修冲突；行号见下** |

### HIGH-1 处置：5 条从 C2 降级为「回归候选」

Codex 指出这 5 条的「依据 sha」栏是 `—`，却直接归了契约演进：

- `test_vault_notes_group_filter` **4 条**（分诊表 277–280 行）——
  实际失败包括 **physics 查询仍返回 math、无匹配仍返回记录**，
  表内实现指向 `vault_notes_retriever.py:227` 但无历史依据；
- `test_strip_whiteboard_removes_admonition_callouts`（179 行）——
  日志证实**正文未被剥离**，指向现行 API 却无契约演进依据。

**按本卡自己定的硬约束**（「被测 API 仍在生产代码里而断言失败的，
默认先按真实现回归/新写，不得默认测试过时」），这 5 条**本就该是回归候选**。
⇒ **改判为回归候选，移交 `CARD-RED-R` 逐条确认**（RED-R 由 22 条 → **27 条**）。

> ⚠️ Codex 明确声明：它认定的是**分类证据不足**，
> 「这些条目是否确为生产回归，**未验证**」。本卡照此措辞登记，不夸大。

### MEDIUM-4 处置：B 撤销后那条硬约束的归属

| 约束 | 状态 |
|---|---|
| A1：opt-in `authed_client`；禁 autouse／全局注入 key | **在场** |
| C1：无替代覆盖不许删；`xfail(strict=True)` + reason | **在场** |
| **B：纯虚构 vault id；禁 ACTIVE_VAULT；禁 tests/unit 级 autouse** | **⛔ 不在场** —— B 分类已被证伪撤销 |

**处置**：不恢复已证伪的 B 分类，但**这条约束本身仍然有效**，
移交给**任何后继涉及 vault fixture 的卡**继承
（当前最可能是 `CARD-RED-C2` 里 `test_vault_notes_group_filter` 那一族，
以及改判后进入 `CARD-RED-R` 的那 4 条）。
在草案里已就近标注，避免它随 B 一起消失。

### LOW-6：行号偏差登记（未逐条改表）

Codex 实测分诊表 **133 / 165 / 180 行**引用的 sentinel 块头**晚标 3 行**
（实际是日志 1643 / 1967 / 2119）；另 4 条 `test_graphiti_json_dual_write` 的
表内测试行与日志调用帧不同（264→290、146→176、424→458、391→415）——
**表内数字可能是定义行、日志是调用帧**，两者本就不同，Codex 也标了「未验证」。
本卡**如实登记不逐条改**：这些偏差不影响类别判定，
但下批引用行号时应注明「定义行 vs 调用帧」。

## 九 本卡未证明什么（必填）

1. **未修任何一条**；未在任何树验证任何修法。247 条红**全部原样留着**。
2. **分类依据 = 静态阅读 + 失败身份输出，未做变异/翻转实验**。
   没有对任何一条做「改掉根因看它是否转绿」的验证。
3. **「真实现回归」只有嫌疑 sha，无 bisect 实证**。嫌疑 sha 由
   `git log -S'<断言里的关键字面>'` 得出，没有实际 checkout 到那个 commit 复现过。
4. **残余里被判「新」的未追根因** —— 只做到「前六类都不是」，没有继续挖。
5. **未证明第十三批草案的估时**。估时是拍的，没有依据。
6. **不复跑 g32b 全量 138 条**（Y1-B 面），本卡只跑 `tests/unit` 目录级一次。
7. **失败身份的提取是机械分类，抽样核对而非逐条人工复核**。
   分类器本身在本卡内被修过两次（块头正则漏 61 条、HTTP 状态码判据误判 1 条），
   最终版对 247 条全部找到 traceback 块，但仍有 **14 条未提取到 `test file:line`**
   （多为 setup ERROR，traceback 在 fixture 里）。
8. **未验证 E 类的历史 commit**（`abf1d585` 删 → 恢复 → `f425d7b7` 再删）——
   那是卡文 §〇.20 的陈述，本卡只核了「现在缺哪 7 个」，没核删除历史。
9. **Workflow 分诊结果与我本人的交叉验证覆盖面不同**：我逐个核了六类的**根因锚**
   （见 `独立核实-*.md`），但没有逐条核 247 行里每一行的「现行实现 file:line」。
10. **⚠️ 送审 prompt 与最终文件不同步（我的瑕疵，如实登记）**：
    `codex-prompt-CARD-RED-TRIAGE.md` 的 §二「作者自述」写于**分诊完成前**，
    用的是当时的假设值（A1 31/12、C1 49 三子类、B 41 条等）；
    而分诊表与草案在其后被更新为最终结论（**B 归零、C1 42、C2 109、新增卡**）。
    卡文要求的顺序「表与草案定稿 → 跑裁判 → 送 Codex」在**文件**层面满足了
    （送审时两份文件已是最终版），但 **prompt 的自述段没有同步更新**。
    Codex 自己发现了这一点并声明「以当前文件为复核对象，区分旧自述与现行结论」，
    未造成误判 —— 但这属于运气，不是流程保证。
    **下次应在送审前重跑一遍「prompt 自述 vs 文件实际」的一致性检查。**

## 十 台账待登记条目（必填，车道不改台账）

1. **⛔ 分母勘误**：复核报告的「298 / 289」是**含 42 行日志噪音的行数**
   （37×`security.py:126` + 3×`main.py:730` + 1×`health.py:883` + 1×`verification_service.py:1444`），
   **不是分母**。分母是 **247 nodeid**（FAILED 209 / ERROR 38 / 63 文件）。
2. **⛔ 各类计数勘误**（Z4-A `c7799298` 已清 9 条所致）：
   A1 42→**41**、C2 29→**24**（C2-d 归零）、残余 86→**74**；
   `test_lancedb_vault_isolation` 在基线中 **0 条**。
   已清的 9 条清单见分诊表附录（`test_lancedb_vault_isolation` ×3 /
   `test_subject_resolver` ×5 / `test_vault_switch` ×1）。
3. **⛔⛔ A1 必须拆成两张卡**（本卡最重要的结构性发现）：
   勘探的「A1 单一根因 `c9bb6c9a`」在 41 条上**不成立**。
   实测失败身份把它劈成 `A1-auth` **31 条**（503×29 + KeyError×2，
   日志里有 `security.py:126` 拒因）与 `A1-sentinel` **10 条**
   （system 端点族，失败身份是 W4 哨兵偷连，**与 auth 无关**）；
   再加从残余改归的 2 条，`A1-sentinel` 共 **12 条**。
   **合成一张卡会拿 auth 的修法去修哨兵的红。**
4. **7+ 张第十三批卡草案路径**：
   `_bmad-output/审查/2026-09-05-第十二批-RED-第十三批卡草案.md`
   （因 A1 拆分，实际 **8 张**：RED-A1-auth / RED-A1-sentinel / RED-A2 / RED-B /
   RED-C1 / RED-C2 / RED-E / RED-R）。
5. **「真实现回归」条数与嫌疑 sha 清单** → 转 backlog（见分诊表）。
6. **`.claude/agents` 保护门裁决请求**：该目录被删过两次
   （`abf1d585` → 恢复 → `f425d7b7` 再删）。RED-E 附此裁决请求。
   附带发现：`EXPECTED_AGENT_TEMPLATES` 是 **18** 项，而
   `test_minimum_template_count` 的阈值是 **17**（docstring 说那是"删除前的原始数量"）
   ⇒ 表加了 1 项而阈值没同步；补回 7 个模板后，那道阈值门会**永远宽 1**。
7. **Y6-A 转来的 `system.py:28` 无鉴权线索，处置结论**：**成立且是 A1 拆分的根因**。
   该 router 没有 router 级鉴权（只有 `:757`/`:824` 两端点挂
   `require_internal_api_key`）⇒ 请求走不到 auth 就先连了 7691，
   所以那 12 条的失败身份是哨兵而不是 503。
   ⇒ 「给 system router 补鉴权」是**独立的产品决策**，不在 RED 系列卡内，
   需单独裁（补了会改变这 12 条的失败形态）。
8. **⛔⛔ B 类整类被证伪 —— 41 条全部改类，B 归零**（本卡最重大的发现，
   也推翻了我自己先前写的判断）：
   - **硬证据**：`grep -c VaultScopeUnresolved` 对整份 3.9 MB 日志 = **0**；
     36 条 setup ERROR 的 traceback 都走到 `memory_service.py:381`，
     而 `:369-373` 的 `Context().run(...)` 在 `:378` 之前
     ⇒ **能走到 :381 恰恰反证作用域解析成功返回了**。
   - **真根因**：`803793c5`（Story 38.2）给 `initialize():282` 加了一行
     `await self.neo4j.get_all_recent_episodes()`，而 10 个 `mock_neo4j` fixture 的
     `MagicMock()` 只桩了三个方法 ⇒ 新方法的自动属性**不可 await** → `TypeError`；
     生产 `except` 只捕 `(RuntimeError, ConnectionError, TimeoutError)`
     （`:431` 注释明写**刻意不放宽**）⇒ TypeError 穿透。
     **真实 `Neo4jClient` 有该 async 方法，生产无缺陷。**
   - 改类结果：**C2 38 条 + 「新」3 条**。
   - ⇒ **卡文 §〇.17 的 B 根因锚错了；RED-B 这张卡的前提没了，第十三批要重排。**
   - **我先前写的「这是有意 fail-closed 设计的副作用」同样错了** —— 我只读代码结构
     就推断它「就是这样红的」。**代码能那样失败 ≠ 它就是那样失败的。**
     读代码得到的是可能的机制，读日志得到的才是发生的事实。
8b. **建议新设「测试环境/依赖缺失」一类**（那 3 条「新」的归宿）：
   ① `fixture 'mocker' not found` —— **pytest-mock 从未在 requirements 里声明过**
   （`git log -S pytest-mock -- requirements.txt` **零 commit**）⇒ **出生即红**；
   ② `默认值应为 False` —— 测试写「默认值」却实例化了会读盘的 `Settings()`
   （`config.py:943 env_file=".env"`），量到的是本机 gitignored 的
   `backend/.env:17 DEBUG_AGENT_RESPONSE=true`；代码默认值确实是 `False`。
   这两个子形态都不该硬塞进 C2。
8c. **⛔ 3 条 Neo4j 降级路径当前无覆盖**（事实登记，非修法）：
   `test_neo4j_disconnected_still_stores_in_memory` /
   `test_neo4j_unavailable_still_processes_to_memory` /
   `test_neo4j_unavailable_fallback` —— 按名字它们该覆盖 Neo4j 降级，
   但**死在 setup、断言体一次都没跑到**。第十三批修好 fixture 后要重新看这三条。
9. **C1 的 49 条必须按三种子类分开处置**（合成一张卡会用错修法）：
   ① 引用已删 API（AttributeError，28 条）② 桩值 vs 断言自相矛盾
   （`test_story_38_6` 补了本地桩 `=0.5` 却仍 `assert >= 2.0` ⇒ **恒红**）
   ③ 锁被废弃的契约（`test_story_38_4` 锁 `default is True`，
   而 `config.py:477` 已是 `default=False` + `[DEPRECATED]`）。
10. **⛔ A2 的嫌疑 commit 须更正 + 6 条改类**（分诊 agent 推翻了卡文与我的读法）：
    - 3 条 `assert 500 == 503`（`test_sync_batch_auth.py:117` +
      `test_system_endpoint_auth.py:112/:161`）**红在配置层不在鉴权层** ——
      `_settings_factory(debug=False, key="")` 构造 `Settings` 时就被
      `config.py:286-298 validate_security_defaults` 抛 `ValidationError`，
      被 `CORSExceptionMiddleware` 兜成 500。
      **嫌疑 commit 更正为 `f718d040`（2026-05-08）**，
      不是卡文点名的 `c9bb6c9a`（2026-05-13，只动 `security.py` + 两个 auth 测试）。
    - 6 条 `test_sync_exception_classification` **改类 A2 → A1-auth**：
      该文件测的是 `/sync/batch` 的异常分类，`_dev_settings()` 的空 key 是
      「让 auth 放行」的**手段**、不是被断言的对象。
      **卡文 §〇.16「塞 key = 毁负控」对这 6 条不成立** ——
      真正的空 key 负控是 `test_dev_mode_no_key_now_fails_closed_503_p0_2` 等三条，
      **本次运行全部 PASSED、根本不在红基线里**。
11. **⛔ `security.py:94-105` 的 Branch 1 已成死路**（A2 组附带发现）：
    prod + 空 key → 503 这一行，在任何**经 pydantic 校验**的 Settings 上不可达
    —— 因为 `validate_security_defaults` 会先抛。
    那张 fail-closed 矩阵里的 `False|empty|any→503` 是**死分支**，
    值得单独登记（门/矩阵声称覆盖的面比实际宽）。
12. **RED-A2/A1-auth 的修法不能只「塞 key」**：`sync.py:106-110` 在分类 try 之前
    先调 `block_reason()`（`schema_gate.py:96-108` 未知态会 `verify()` **真连**
    `NEO4J_URI`），`:117-131` 还有 vault 身份注册表 `assert_identity` 与 409 一致性面
    ⇒ 过了鉴权墙后**极可能撞第二道 503/409**，甚至在无 W4 门的树上触发真连端口。
    第十三批须一并补桩。
13. **C2 的三个锚各自处置不同**：`config.py:274-298` 安全默认值 /
    reranker 权重表演进（作者已把测试重写推给 FU-2）/
    `test_story_30_24_boundary` 指向**已归档**的 `verify-vault.mjs`
    （唯一副本在 `_archive/` 下）。
