# UAT — CARD-RED-HYGIENE（RED 卫生收尾）

> 批次：`BATCH-2026-09-11-第十四批` · 车道 `card-t10-red`（分支 `card/t10-red`）· 本车道第 **5/5**
> 本卡最终代码 SHA：**`ef21be2ca360bf26e918155c0edace193d1db38c`**
> commit 链：`8bfcdfce`（主体）→ `b38e1d04`（只读自审整改）→ `2c740216`（按 Codex r1 整改）
> → `f28c0f4a`（**零代码**）→ `69c99d1a`（按 r2 整改）→ `ef21be2c`（按 r3 整改）
> → 收尾（**纯 docstring + `_bmad-output`**，D-32 不占轮次，等价性已用 AST 证）
> `$PREV`（= 同车道上一卡 CARD-EPW-COVERAGE 的 commit）：`f294878bb677ae54dcbf17277004efa2fa1ef97b`
> 红基线 `$BASE`：feature 主干树 `_bmad-output/审查/evidence-b14/unit-red-baseline-08100483.txt`（`grep -vc '^#'` = 64）
> 证据目录：`_bmad-output/审查/evidence-red-hygiene/`
> **未 push。**

---

## 首段 — 请主 session 裁定 / 补登的三件事

1. **`backend/app/config.py` 与 T5 的声明交集 + 串行次序**
   手册 §一「只 T5」行已写明该交集（T5 只**新增** `TASK_CLEANUP_INTERVAL_SECONDS` 且避开 `MEMORY_RETRY` 段；本卡只**删除** `MEMORY_RETRY` 两字段）。交集本身无需再补登，**仍缺的是 T5 ↔ T10 在该文件上的合并串行次序**，请主 session 在合并队列里定序。
   本卡实测两侧 hunk 不重叠：本卡删的是原 `:640-655`（段注释 + 两个 Field），删后 `ENRICHMENT_CACHE_MAXSIZE` 由 `:678` 上移到 `:662`。

2. **auth 两文件路径更正（设计稿 §3 写错）**
   设计稿 §3 写 `backend/tests/api/.../test_sync_batch_auth.py` 与 `test_system_endpoint_auth.py`，**实测两文件都在 `backend/tests/unit/`**。
   另：UAT-RED-A2 记的「两文件 U10-E 独占」目前只是车道内约定，手册 §一地盘互斥段未列（`grep` = 0），**请主 session 补登**。

3. **两个新增地盘文件（§3 未列、不在 R-B14-4 已批准扩充表内）**
   - `backend/tests/unit/test_cache_configuration.py`
   - `backend/.env.example`
   二者都是 (f) MEMORY_RETRY 退役的**连带必改面**：不同批改就必红（先红证据见 §4-A.6）。实测无其它车道写者（T10-D 硬边界明写「禁碰 test_cache_configuration」）。**请主 session 在 §3 / 手册地盘表补登确认。**

---

## 一、本卡做了什么（对照卡文 (a)~(k)）

| 项 | 内容 | 结论 |
|---|---|---|
| (a) | 第 0 分钟六项自证 | ✅ |
| (b) | agents_health 期望表对齐生产 13（先红后绿）+ 防漂 guard + 负控 | ✅ |
| (c) | auth 两文件头矩阵 200 → 503 改实（纯文案） | ✅ |
| (d) | 「鉴权先于 handler」承重断言 + 单变量对照输入 + 三段负控 | ✅ |
| (e) | 两条 flaky 单跑 ×5 + 顺序对照，只定性未改 | ✅（定性结论**与卡文假设不同**，见 §3） |
| (f) | MEMORY_RETRY 死配置退役（census → 先红 3 → 后绿）+ pyright 保持 0 | ✅ |
| (g) | contract node-id pattern 定性 | ✅（**卡文两处事实有误**，见 §3） |
| (h) | 地盘核：代码面恰好 6 文件 | ✅ |
| (i) | tests/unit 目录级对 `$BASE` | ⚠️ **不自判通过**（D-15）：**十跑**里 `<` 恒 30；`>` 三跑 = 1、七跑 = 0，且 `>` 与 `blocked=` **10/10 同步**；同一 SHA 内部会翻转。Codex r2/r3/r4 均判该条不阻断本卡。裁定权在主 session。见 §四-A.10 |
| (j) | Codex 多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0 | ✅ **达成**：r4 绑最终 SHA `ef21be2c`、diff 空 exit=0、**BLOCKER 0 / HIGH 0**，Codex 明写「不要求继续改代码送第 5 轮」。r2/r3 亦各满足过一次 |
| (k) | 「本卡未证明什么」≥4、「台账待登记条目」≥4 | ✅ 见 §6 / §7 |

---

## 二、⛔ 卡文事实更正（实测与卡文 §〇 不符的地方）

### 更正 ①（(g)）：contract 测试的失败身份不是「pattern 不一致」，是 `FileNotFoundError`

卡文 §〇 写该测试「比对 `specs/data/canvas-node.schema.json` 的 `properties.id.pattern`（`:160`）vs `NodeRead...`（`:163`）」。

实测：测试在 `test_node_id_patterns.py:157` 的 `open()` 就抛 `FileNotFoundError`，**从未跑到 `:160/:163` 的比对逻辑**。`specs/data/` 下根本没有 `canvas-node.schema.json`（该目录实有 7 个 schema 文件，无此项）。

### 更正 ②（(g)）：两侧 pattern **从不分歧**，所以接收卡的范围要改写

git 历史实数（先跑 `wc -l` 再写）：该路径涉及 6 个 commit，其中 1 个是删除型 —— `14f0412d`（2026-02-07，`chore: clean release — remove legacy docs/specs`），已实测是 HEAD 祖先。

从 `14f0412d^` 取回删除前的 schema：

```
14f0412d^ 的 schema properties.id.pattern = ^[a-zA-Z0-9][-a-zA-Z0-9]*$
今天       NodeRead pydantic pattern      = ^[a-zA-Z0-9][-a-zA-Z0-9]*$
逐字相同 = YES
```

⚠️ **收窄（自审 EV-06 + Codex r1 LOW-3）**：上面这条只是**删除那一刻的单点快照**，
不是历史不变量。实测该 schema 的 `properties.id.pattern` 在历史上取过 **3 个不同值**：
`^[a-f0-9]{8}-…$`（eb86275a 2025-11-22）→ `^[a-f0-9]+$`（56395674 / 50e35496 2025-11-25）
→ `^[a-zA-Z0-9][-a-zA-Z0-9]*$`（5e10a260 2025-12-19 起）。
所以「从不存在 pattern 分歧」**不成立**，已撤回；成立的只有「删除那一刻两侧一致」。
对处置建议无影响（二选一不依赖历史不变性）。

⇒ 接收卡的任务**不是**「对齐两个分歧的 pattern」，而是二选一：
(甲) 把 `14f0412d` 连带删掉的 schema 文件补回（内容可从 `14f0412d^` 完整取回）；
(乙) 退役这条自 2026-02-07 起就没跑到过比对逻辑的契约测试。

证据：`contract-nodeid-CORRECTED-20260916T130606.txt`

### 更正 ③（(e)）：flaky ① 的根因不是「同文件内测试相互影响」

卡文 §〇 写 `test_accept_candidate_already_accepted_returns_422` 的根因是「同文件内测试相互影响」。

实测（`flaky-characterization-20260916T125210.txt`）：
- 定向单跑 ×5 → 5/5 passed
- **整文件跑 → 14 passed（全绿）**

⚠️ **本条的原结论已撤回**（自审 RG-3 + EV-02；Codex r1 LOW-3 独立得出同样判断）。

撤回理由三条：
1. **推论结构不成立**：定向单跑按构造就不含同文件前序用例，对「同文件互扰」这一维
   零信息量；能显现它的只有整文件跑，而本卡**各只跑了 1 次**（n=1）。
2. **该 flake 在本卡全部 13 次跑里一次都没红过**（10 次定向 + 2 次整文件 + 1 次目录级）。
   从「没观察到红」推不出「红的成因在哪里」。
3. **漏引了已落盘的机制（关键）**：协议 `.claude/rules/card-batch-protocol.md` §3 第 79 行
   明确记载「W4 哨兵判据绑 `blocked=` 次数 + 失败正文，**不绑 nodeid**（R-08/R-10）：
   同一代码状态下哨兵红会在 nodeid 之间翻转（U10-A r4/r4b 实测：`candidate422` ↔
   `mock_warning`），逐 nodeid diff 自带 flaky」—— `candidate422` / `mock_warning`
   **正是本条定性的这两条**。既有机制比本卡的「跨文件」假设精确得多，本卡未做验证。

**更正后的如实结论**：卡文写的「同文件内测试相互影响」**未被本卡证伪也未被证实**
（n=1，不足以排除）；本卡只能说「在跑过的 13 次里它们都是绿的，成因未定」。
协议 §3 已记载的 W4 哨兵 nodeid 漂移是更可能的既有解释，建议接收卡从那里查起。
对目录级判据的影响不变：本卡收工的红集里这两条都不在，`>` 仍为 0。

### 更正 ④（自查）：本卡自己写出过一份含假陈述的证据，已作废并取代

第一版 contract 证据里我写了两行**硬编码**的「(以上为空 = …)」，而其上方的 `git log` 实际有输出 —— 那是关于证据本身的假陈述。已按实数更正（删除型 1 条 / 总计 6 条），原件保留并加作废横幅：`contract-nodeid-20260916T130232-SUPERSEDED.txt`，取代件见更正 ②。
同类还有一份 `ruff-20260916T130748-SUPERSEDED.txt`：其验伪锚传了不存在的 `--config backend/pyproject.toml`，ruff 以 rc=2「参数错误」退出 —— 那个锚**什么都没证明**，已由带有效锚的 `ruff-with-anchor-*.txt` 取代。

### 更正 ⑤（本卡改动的副作用）：删 `config.py` 16 行使**卡外** 5 个文件 10 处行号锚失实

本卡删除 `config.py` 原 `:640-655`（16 行）后，凡引用 **> 655 行号**的 `config.py:<行号>`
锚点整体上移 16 行。实测受影响 **10 处 / 5 个文件，全部在本卡地盘之外**（禁改）：

| 文件 | 原锚 | 现应为 |
|---|---|---|
| `backend/scripts/validate_learning_events.py` | `config.py:1020` | `config.py:1004` |
| 同上 | `config.py:782-795` | `config.py:766-779` |
| 同上 | `config.py:777` | `config.py:761` |
| `backend/tests/regression/test_learning_events_schema_contract.py` | `config.py:1020` | `config.py:1004` |
| 同上 | `config.py:777` | `config.py:761` |
| `backend/tests/unit/test_lancedb_vault_isolation.py`（×3 处） | `config.py:781-790` | `config.py:765-774` |
| `backend/tests/unit/test_vault_switch.py` | `config.py:781-790` | `config.py:765-774` |
| `docs/learning-events-schema-v1.md` | `config.py:782-795` | `config.py:766-779` |

本卡地盘内的同类引用（`test_cache_configuration.py` 的 4 处 `config.py:678`）已改为符号名
`app/config.py::Settings.ENRICHMENT_CACHE_MAXSIZE`，不再随增删漂移。卡外 10 处**登记移交**。

⚠️ 判据自查：首次统计时我的正则把 `git grep` 的 `<路径>:<行号>` 前缀也当成了引用
（把 `backend/app/config.py:995` 这个 grep 前缀读成了一条引用），得到 11 处。
剥掉前缀后重数为 10 处 —— 与本卡其它两处「判据取名面 ≠ 主张」同型。

### 更正 ⑥：生产 `security.py` 自己的矩阵仍写 P0-2 之前的口径（禁改，登记）

本卡 (c) 把**两个测试文件**的头矩阵改实了，但最权威的那张表没动：
`backend/app/security.py:15` 的模块 docstring 矩阵仍写

    | True  | empty            | any    | allow + structured warning (dev mode) |

而同文件 `:107-140` 的代码早已 fail-closed（P0-2 加固）。该文件在本卡**明确禁改**清单内
（§三），故只登记不改。

⚠️ 同文件 `:191` 的 **WebSocket** 侧矩阵写 `accept + warn (dev mode)`，而 `:228` 的
WS Branch 2 代码**确实仍然放行** —— 那一张表可能是准确的。两张表的状态不同，
接收卡须分开判，不要一并「改实」。

---

## 三、地盘与合规

**代码面恰好 6 文件**（`FINAL-R5-territory-*.txt`，绑**当前** HEAD）：

```
backend/.env.example                                |  16 --
backend/app/config.py                               |  16 --
backend/tests/api/v1/endpoints/test_agents_health.py| 279 +++++++++++++++++++--
backend/tests/unit/test_cache_configuration.py      |  95 +++----
backend/tests/unit/test_sync_batch_auth.py          |  24 +-
backend/tests/unit/test_system_endpoint_auth.py     | 134 +++++++++-
6 files changed, 446 insertions(+), 118 deletions(-)
```

⛔ **本段数字曾经失实，2026-09-16 主 session 复核时更正**（成因与 §七.16 同族，本卡第五次）：
原文贴的是 `286 insertions`，并标注「（`FINAL-territory-*.txt`，绑本卡最终 HEAD）」——
但那份存档首部自写 `HEAD=b38e1d04`，是**第二个 commit**，不是最终 HEAD。
其后车道又跑过两版（`FINAL-R3-territory` 绑 `69c99d1a` = 419、`FINAL-R4-territory` 绑 `ef21be2c` = 429），
**验收单一次都没跟着改**。逐版实测：

| 存档 | 绑定 SHA | insertions | 验收单当时引用 |
|---|---|---:|---|
| `territory-worktree-*` | 工作树（commit 前） | 268 | — |
| `territory-headcommit-*` | `8bfcdfce` | 267 | — |
| `FINAL-territory-*` | `b38e1d04` | **286** | ⛔ 被当成「最终 HEAD」引用 |
| `FINAL-R3-territory-*` | `69c99d1a` | 419 | 未引 |
| `FINAL-R4-territory-*` | `ef21be2c` | 429 | 未引 |
| `FINAL-R5-territory-*` | **当前 HEAD** | **446** | ✅ 现引此份 |

⇒ 「6 个文件」这个**结论**六版全部一致、从未失实；失实的是**行数**与**绑定声明**。
本卡地盘边界没有被突破过，但「绑本卡最终 HEAD」这句话在写下时就是错的。

- 验伪锚①：单查 `config.py` 必命中 → `1 file changed, 16 deletions(-)`
- 验伪锚②：去掉 `':(exclude)_bmad-output'` 后 `_bmad-output` 面 = **36** 文件，带 exclude 时 = **0** ⇒ exclude pathspec 生效
  ⚠️ 该锚在**第一次** commit 之前结构上不可能成立（evidence 当时是 untracked，`git diff` 看不见），
  commit 前那份 `territory-worktree-*.txt` 已加作废说明。
- `backend/openapi.json` 与 `$PREV` **blob 逐字节相同**
- 本卡 commit 新增/改动文件里含 `stderr` 的 = **0**；验伪锚：整棵 HEAD 树含 `stderr` 的 = 3，
  `$PREV` 树同样 = 3 ⇒ 那 3 个非本卡引入
  ⚠️ 首次我把这条判据的取名面写成了整棵树（得 3 却标「须 0」），已更正并在
  `territory-headcommit-*.txt` 内留更正段。

**生产源码零改动**：(d) 全程只用 `app.dependency_overrides`，未动 `system.py` / `security.py` / `main.py` 任何一行。

**`LEFTHOOK_EXCLUDE=python-lint,spec-sync-root`**（依据全文见 `lefthook-exclude-justification-*.txt`）：
- `python-typecheck` **未**跳过（不在 `LEFTHOOK_EXCLUDE` 里）。⚠️ 但**前两个 commit 没有留下它的原始输出** —— 引用过的 `✔️ python-typecheck (3.07 seconds)` 出自第一次**失败**的 commit 尝试，而该 hook 在工具缺席时也会 SKIP 并返回 0，勾号本身不足以证明实跑（Codex r1 MEDIUM-3）。前两个 commit 就此标记 **历史 PARTIAL**；本卡最后一个 commit 落盘了完整 pre-commit 输出，见 `FINAL-precommit-hooks-*.txt`。
- `python-lint`：失败的只有 `ruff format --check`（`ruff check` 全绿）。本卡**自清了自己引入的那一处**（`test_agents_health.py` 在 `$PREV` 格式是干净的 ⇒ 不享受过渡条款），剩余 dirty 集 = `{test_cache_configuration.py}` = 主干既有集，且**实际被改行**（不是 hunk 跨度）在 `$PREV` / 被审 SHA / 当前 HEAD 三版分别是 284-286 / 247-249 / 250-252，都落在本卡全部改动 hunk 之外；该段在 `$PREV` 逐字相同。依协议 §2.3 不顺手修存量。（原先我引的是 hunk 头 `@@ -244,9` 与跨度 244-252，按 Codex r1 LOW-2 收紧为实际被改行。）
- `spec-sync-root`：该 hook 会把 `backend/openapi.json` 塞进任何含 `backend/app/config.py` 的 commit（= 第 7 个文件 = 越界）。实测重生成只改 1 行 `x-generated-at`，`paths=197 schemas=357` 不变 ⇒ 本卡不改变 OpenAPI 面，跳过它并保持快照与 `$PREV` 逐字节相同。

---

## 四、DoD-3 段 4-A：技术 assert（Claude 自跑，逐条贴证据）

> 所有承重裁判 `2>&1 | tee` 落 `_bmad-output/审查/evidence-red-hygiene/`，末行 `rc=$pipestatus[1]`。
> 本段只**引用**路径与关键行，不自述数字。

### 4-A.1 第 0 分钟六项自证 — `minute0-20260916T021417.txt`

pwd / 分支 `card/t10-red` / `$PREV=f294878b`（`git log -1` 含 `CARD-EPW-COVERAGE`）/ venv+env / `pyright app` = `0 errors, 81 warnings, 0 informations` / `$BASE` `grep -vc '^#'` = `64`。

⚠️ **该存档的「工作树干净」一项记为未证实（PARTIAL）**（Codex r1 MEDIUM-2，车道接受）：
存档里 `git status --porcelain | wc -l` 显示 **1** 而标注写「须 0」，且只记了计数、
没留 porcelain 的原始路径。**空目录本身不会被 git 计入脏项**，所以「仅仅 mkdir 了 evidence
目录」这个事后解释并不自动成立，也无法排除当时还有别的脏项。不追认。
可作旁证但不充分：本卡后续每一次 `git status --porcelain`（两份 territory 存档）里的
未跟踪项**全部**是本卡自己的 evidence / codex 产物，未出现第三方脏项。

### 4-A.2 (b) 先红 — `agents-health-RED-20260916T021651.txt`

只改断言未动 mock → `2 failed, 10 passed`，失败身份：
`assert 12 == 13`（`:141` total）与 `assert 10 == 11`（`:172` available）。

### 4-A.3 (b) 后绿 — `agents-health-GREEN-20260916T021719.txt` / `agents-health-GUARD-GREEN-20260916T021816.txt`

mock 补 `hint-generation` → `12 passed`；加防漂 guard 后 → `13 passed`。

### 4-A.4 (b) 防漂 guard 负控 — `agents-health-NEGCTL-rename-20260916T021848.txt`

负控输入 = 把 mock 里 `memory-anchor` 改名（**长度仍 13**）。结果 `1 failed, 12 passed`，红的恰是
`test_mock_expected_templates_match_production_truth_source`，失败文案是 guard 自己那句。
⇒ 证明 guard 抓的是**数量判据抓不到的那一维**（改名 / 换序 / 改名单内容）。
跑前 / 跑后 `shasum -a 256` 同为 `a31efb0c…`，还原后复跑 `13 passed`。

### 4-A.5 (d) 承重 + 对照 + 三段负控 — `auth-GREEN-20260916T022032.txt` / `auth-NEGCTL-3mutants-20260916T124519.txt`

- 正跑：两文件合计 `19 passed`。
- 三段负控（跑前 / 跑后 sha 同为 `289172fb…`，还原后 `12 passed`）：

| 变异 | 改了什么 | 期望红的那条 | 实测 |
|---|---|---|---|
| M1 | 对照用例的断言方向翻成与承重同向 | **对照** | `1 failed, 11 passed`，红的是对照 |
| M2 | 共用谓词 `_handler_was_not_reached` 改恒真 | **对照**（承重仍绿） | 同上，红的是对照 |
| M3 | 共用谓词改恒假 | **承重** | `1 failed, 11 passed`，红的是承重 |

- M1 / M2 的存档里同时留下了 handler 真跑过的日志行：
  `[Story 1.3] LLM connection test passed — model=ollama/qwen2.5:7b`
  ⇒ 直接证明「摘掉鉴权依赖后请求确实进了 handler 正文」，对照输入不是空转。

### 4-A.6 (f) census → 先红 3 → 后绿 → pyright 0

- census：`git grep` 排文档面后，`backend/app` 下只命中 `config.py` 自身两行定义，**生产消费方 = 0**；`backend/.env` 无该键；`Settings.model_config` 是 `extra="ignore"`。
- 先红 — `cachecfg-RED-20260916T124757.txt`：删 Field + 删 `.env.example` 两行、**未动测试** → `3 failed, 7 passed, 5 xfailed`，三条恰是：
  `test_retry_delay_defaults_match_original`（AttributeError）、
  `test_settings_defaults_match_original`（AttributeError）、
  `test_env_example_documents_all_new_settings`（AssertionError）。
  ⇒ **红集恰好等于接下来要改的三处**，无「改了不红」也无「红了不改」。
- 后绿 — `cachecfg-GREEN-20260916T125122.txt`：`9 passed, 4 xfailed`。
  **算术如实说明**：`15 → 13` 是因为**删除**了 2 条用例（`test_retry_delay_reads_settings` 是 `xfail(strict=True)`，`test_retry_delay_defaults_match_original` 原本 passed），不是「2 条转绿」。
  真正**转绿**的是 2 条（`test_settings_defaults_match_original`、`test_env_example_documents_all_new_settings`）：`7 passed + 2 = 9 passed`；xfailed `5 - 1 = 4`。
- pyright — `pyright-after-retire-20260916T125122.txt`：`0 errors, 81 warnings, 0 informations`。

### 4-A.7 (e) flaky 定性 — `flaky-characterization-20260916T125210.txt`

两条各定向单跑 ×5 全 passed；两个整文件跑分别 `14 passed` / `30 passed`。
被测两文件跑前 / 跑后 `shasum -a 256` 逐字节相同（全程只读，一字未改）。

### 4-A.8 (g) contract 定性 — `contract-nodeid-CORRECTED-20260916T130606.txt`

见 §2 更正 ① / ②。验伪锚：同文件 `1 failed, 49 passed` ⇒ 红的是这一条，不是收集期崩。

### 4-A.9 ruff — `ruff-with-anchor-20260916T131102.txt`

本卡 5 个 `.py`：`All checks passed!` rc=0。
验伪锚 = 把 F821 注入**判据自己的文件集**、跑逐字相同的判据命令 → `anchor rc=1` 并指名
`F821 Undefined name`，还原后 sha 一致、判据复跑 rc=0。
（⛔ 不用 F401 当锚：`backend/ruff.toml` 的启用集实测只有 `E902/F63x/F7xx/F82x`，F401 不在其中，拿它当锚会恒不触发。）

### 4-A.10 (i) tests/unit 目录级 —— ⚠️ **当前 HEAD 上 `>` = 1，本卡不声称通过**

跑法（R-B14-3：`cd backend` 后 `--ignore` 用相对路径）：
`cd backend && PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest tests/unit --ignore tests/unit/test_deploy_vault_sh.py -q -p no:cacheprovider`

**十跑对照**（前九跑全表 + 统一 comm 见 `FINAL-sentinel-9runs-*.txt`；第 10 跑见 `FINAL-R5-unit-close-*.txt` / `FINAL-R5-unit-comm-CORRECTED-*.txt`）：

| 跑 | 绑定 SHA | failed | `<` | `>` | W4 哨兵 |
|---|---|---:|---:|---:|---|
| 1 | `8bfcdfce` | 34 | 30 | 0 | `blocked=0` |
| 2 | `b38e1d04` | 34 | 30 | 0 | `blocked=0` |
| 3 | `2c740216` | **35** | 30 | **1** | **`blocked=1`** |
| 4 | `2c740216` | 34 | 30 | 0 | `blocked=0` |
| 5 | `2c740216` | 34 | 30 | 0 | `blocked=0` |
| 6 | `69c99d1a` | 34 | 30 | 0 | `blocked=0` |
| 7 | `69c99d1a` | 34 | 30 | 0 | `blocked=0` |
| 8 | `ef21be2c` | 34 | 30 | 0 | `blocked=0` |
| 9 | `ef21be2c` | **35** | 30 | **1** | **`blocked=1`** |
| 10 | `0bc3baef`（**当前 HEAD**） | **35** | 30 | **1** | **`blocked=1`** |

> 第 10 跑为 2026-09-16 主 session 复核时在**当前 HEAD** 补跑（`FINAL-R5-unit-close-*.txt` 420.66s，
> comm 见 `FINAL-R5-unit-comm-CORRECTED-*.txt`）。它把样本从 9 扩到 10，
> 并把绑定点从 `ef21be2c` 推进到当前 HEAD —— 结论与前九跑同型，不构成新情况。
> ⚠️ 该 comm 首算时用错了 BASE 提取口径（基线 64 行是 `FAILED `/`ERROR ` **两种**前缀，
> 而提取只脱 `FAILED ` 后取字段 1，29 条 ERROR 塌成字面量一条，BASE 被算成 36、`'<'` 被算成 2）。
> **错档保留并标 SUPERSEDED**（`FINAL-R5-unit-comm-20260916T233419.txt`，开头有作废说明），
> 更正档用两侧统一取字段 2 的口径，BASE 复得 64、`'<'` 复得 30，与前九跑一致。
> 值得记一笔：`'>' = 1` 与那条 nodeid 在**两种口径下相同** —— 新增红的判定不受 BASE 塌缩影响，
> 所以「结论看起来对」并没能暴露这个口径错误，是 `'<'` 对不上前九跑的 30 才暴露的。

三条可核的观察（第 10 跑已并入计数）：
1. `>` 与 `blocked=` **10/10 完全同步**；出现 `>` 的三跑，唯一新增 nodeid 都是 `candidate422`，
   失败正文都是协议 §3 的哨兵指纹（连接**被拦下**，现网 7691 未被连上）。
2. **同一 SHA 内部就会翻转**：`2c740216` 三跑 = 35/34/34；`ef21be2c` 两跑 = 34/**35**；
   当前 HEAD 第 10 跑 = **35**（该 SHA 目前仅一跑，不构成同 SHA 内翻转的新证据）。
   ⇒ 目录级结果不由代码状态决定。
3. `<` 十跑恒 **30**；本卡 4 个测试地盘文件在十跑红集里恒 **0** 条。

⛔ **这三条不能推出「它与本卡无关 / 早于本卡」** —— 这正是 Codex 连着三轮（r2/r3/r4）
纠正车道的地方，车道已接受。成立的证据是两份**历史原始日志**，各证一事、不可混引：
* **「现象早于本卡」** ← `$PREV` 已入库的 `evidence-b13-integ/unit-integ5-20260911T010612.txt`
  （**65** 条红），第 597-606 行同一 `candidate422` + 同一指纹，第 1143 行 `blocked=1`；
* **「红集没变」** ← `$PREV` 已入库的 `evidence-epw-coverage/epw-unit-close7.nodeids`
  （**34** 条，与本卡 `blocked=0` 那几跑逐项相同、差集 **0**）。

**第三跑那条 `>` 的身份**（`FINAL-R2-unit-comm-*.txt`）：
`tests/unit/test_candidate_service.py::test_accept_candidate_already_accepted_returns_422`，
失败正文首行逐字是协议 §3 指定的 W4 哨兵指纹：

```
- ('::1', 7691, 0, 0) on thread MainThread (owner=…test_accept_candidate_already_accepted_returns_422)
```

唯一指纹数实测 = 1；`advisory=0 / unaccounted=0`。**连接被拦下（blocked），现网 7691 未被连上**，
随后走 JSON 降级。该测试不是因为自己的业务断言失败，而是承接了哨兵的红。

协议 §3 第 79 行对这种情形有明确口径：判据**绑 `blocked=` 次数 + 失败正文，不绑 nodeid**，
因为「同一代码状态下哨兵红会在 nodeid 之间翻转（`candidate422` ↔ `mock_warning`），
逐 nodeid diff 自带 flaky」—— 而承接哨兵的正是它点名的两条之一。

**与 Codex r1 相互印证**：Codex 在**它自己的环境**、绑 `8bfcdfce` 时也得到 35 failed /
`>`=1 / `blocked=1`（同一条 nodeid），并实测「随后单跑它为 1 passed，blocked=0」。
⇒ 同形出现于两个独立环境、三个不同 SHA，且**同一 SHA 内部就会翻转**（跑 3 vs 跑 4/5）。
本卡三个 commit 都没碰任何与端口 / Neo4j / conftest 相关的文件。

⛔ **本卡不自判通过**（D-15：车道对 HIGH 只能写理由）。验收单**不**声称 `>` = 0。
裁定权在主 session，建议按协议 §3 用「`blocked=` 次数 + 失败正文」判。

**本卡 4 个测试地盘文件在第三跑红集里各 0 条**（同次验伪锚：`test_vault_notes_group_filter` = 4，
证明该 grep 非恒 0）。

**归属**（`attribution-*.txt` + Codex r1 的更强对照）：本卡对那 30 条 `<` 的贡献 = **0**，
30 条全部来自同车道前四卡。Codex 用 `$PREV` 已入库的 `epw-unit-close7.nodeids` 对照，
双方同为完全相同的 34 条红 —— 本卡原先只用「4 个测试文件不在 BASE 红集」论证，
Codex 指出不充分，本卡接受并以其对照为准。

### 4-A.13 (b) guard 形态覆盖 — 绑**当前实现**的是 `FINAL-R4-guard-shapes-*.txt`（26 格）

⛔ **版本对应关系（2026-09-16 主 session 复核补，原文只引 R3 那份，会被读成当前行为的证据）**：
本卡对 guard 的判定方式**换过一次实现**，两份探针绑的不是同一段代码 ——

| 存档 | 绑定 SHA | 被测实现 | 格数 | 是否当前行为 |
|---|---|---|---:|---|
| `FINAL-R3-guard-shapes-*.txt` | `69c99d1a` | `_own_statements` / `_iter_write_targets` / `_assert_not_mutated_after_binding`（**枚举语句类型**） | 19 | ❌ **已被取代** |
| `FINAL-R4-guard-shapes-*.txt` | `ef21be2c` | `_own_nodes` / `_collect_writes`（**按 AST `ctx` 判定**） | 26 | ✅ 是（`0bc3baef` 只改 docstring，AST 等价已证） |

两份的差异不是措辞而是**行为**，实测一例：**「纯注解无右值」**（`expected_templates: list[str]`）——
* 旧实现（R3 格 19）：`binds = 0` ⇒ 红在「找到 0 处绑定」；
* 当前实现（补测格 `F2-only`）：`binds = 1` ⇒ 红在「那处绑定不是普通赋值，取不到字面量」。
两边都红、**都不放过**，但红的身份不同。⇒ 引 R3 的表说明当前行为会失真，故本节改以 R4 为准。
（`FINAL-R4` 存档抬头第 2 行仍写「构造上穷尽」，那是 r4 证伪前写的，**已在该文件开头追加撤回批注**；
其正文 26 格逐格自断言，不受该措辞影响。）

两份的共同做法：import **入库的真 helper**（非副本），只在内存替换 `inspect.getsource` 输入，
**逐格写死预期并由探针自己断言**，退出码反映「预期是否全部兑现」——
不再靠末尾一句人工期望（那正是 Codex r2 LOW-1 点的问题：`rc=0` 只说明探针跑完了）。
`FINAL-R4` 实测 **26 格、预期不符 = 0、`probe_rc=0`**。

下表是 **R3 那 19 格**（保留作历史对照，⛔ **不代表当前行为**，逐格差异以上表口径读）：

| 应通过（2 格） | 应报红（17 格） |
|---|---|
| 01 真实生产源码（13 项，与 mock 逐元素相等）<br>02 带类型注解（无害） | 04 `+= [...]`／05 `[0]="x"`（**r1 报**）<br>06 `[0] += "-x"`／07 `del a[0], b[0]`／08 `a[0]=b[0]="x"`（**r2 报**）<br>09 元组解包写下标／10 `.append`／11 `.remove`／12 `.sort`<br>13 `for` 重绑／14 walrus 重绑<br>15 常量／16 推导／17 两处绑定／18 改名／19 纯声明 |
| 03 嵌套函数内同名局部变量 → **取到外层那张表**（作用域修复生效） | |

**覆盖边界如实声明**（已写进代码 docstring）：本 guard 只认「语法上直接写到这个名字上」的形态。
**别名写入**（`alias = expected_templates` 后改 `alias`）、传进函数由被调方改、
`locals()` / `setattr` 等动态手段 —— **看不见**，需要别名分析，不在能力范围内。

### 4-A.11 (d) 顺序污染判据 — `auth-order-pollution-*.txt`

对照用例结束时只 `pop` 掉 `require_internal_api_key`、保留 `get_settings` 覆盖。三种顺序（默认 / 对照排最前 / 对照 + 另一文件）全绿。

⚠️ **该判据的局限如实写明**：同次验伪锚显示该文件 12 条测试**全部**在进门时自设 `app.dependency_overrides[get_settings]`（`grep -c` 实测 12，`def test_` 实测 12）。所以「残留覆盖」这一维**本身就不可能生效** —— 顺序判据对它不敏感，无污染的真正依据是：
(1) `require_internal_api_key` 在 `finally` 里被 pop；
(2) 12/12 用例进门自设 `get_settings`，残留立即被改写；
(3) fixture teardown 还有一次 `app.dependency_overrides.clear()` 兜底。

### 4-A.12 (b) guard 形态覆盖的**最早一版** — `guard-ast-shapes-*.txt`（⛔ 已被 4-A.13 取代，非独立证据）

⛔ **定性更正（2026-09-16 主 session 复核补）**：本节与 4-A.13 **不是两层独立证据**，是**同一维度的三个版本**，
后者取代前者；并列摆着会被读成互相印证（台账「并列同层判据 ≠ 换了一层」）。本节这一版有两处弱于 4-A.13：
1. 它把 guard 的 AST 逻辑**逐字抄进探针**（逻辑副本），测的是副本不是入库代码 —— 副本与本体一旦分叉，它照样全绿；
2. 它绑的实现比 R3 那版还早，**当前 HEAD 上这段逻辑已不存在**。
保留本节仅作过程记录。**当前行为一律以 4-A.13 表中的 `FINAL-R4`（26 格、import 真 helper）为准。**

把 guard 的 AST 取值逻辑逐字搬到 scratchpad 探针，喂 5 种生产形态：

| 生产形态 | guard 行为 |
|---|---|
| 单个字面量列表（当前） | 正常返回该表 |
| 改成从常量读 | `AssertionError: NOT-A-LITERAL-LIST` → 红 |
| 改成从文件读 | 同上 → 红 |
| 改成列表推导 | 同上 → 红 |
| 出现两处同名赋值 | `AssertionError: FOUND-2` → 红 |
| 变量改名（不再叫该名） | `FOUND-0` → 红 |

⇒ **没有一种形态会让它静默返回空表或错表**。验伪锚：生产里 `expected_templates = [` 实测出现 1 次（正是形态 1 且唯一）。

### 4-A.14 (b) r4 之后写进 docstring 的 6 条主张 —— 补证 `FINAL-R5-docstring-claims-*.txt`

⛔ **为什么要补这一节**：`ef21be2c → 0bc3baef` 按 Codex r4 MEDIUM-1 撤回「构造上穷尽」时，
在 `_collect_writes` 的 docstring 里**新写了 6 条可验证的技术主张**（3 类已知漏面 + 3 类已知误报）。
这 6 条是 r4 **之后**写的，**没有任何一轮 Codex 审过，也没有入库证据** ——
按台账「不入库的复核不作依据」，它们在补证之前只是**未经检验的自述**。
撤回一句过强声明时顺手写下的替代声明，本身同样需要判据，否则只是把一个未证主张换成另一个。

**做法**：import 入库真 helper（`_own_nodes` / `_collect_writes`，非逻辑副本），
复刻 `_production_expected_templates()` 的完整取值三步，逐格喂构造源码，看 guard **实际**怎么裁决，
与 docstring 声称的结果逐条对照。存档首部打 HEAD + 被测文件 **HEAD 侧与工作树侧双 sha256**
（两侧相同 ⇒ 跑的就是已提交内容，不是未提交工作区；台账「存档写了 rc= 不等于它绑定了那次 commit」）。

| 格 | docstring 主张 | 类别 | 实测 | 一致 |
|---|---|---|---|:-:|
| L1 | `case [*expected_templates]`（`MatchStar.name` 是字符串，不产生 `Name(ctx=Store)`） | 漏面，称**不红** | `binds=1` → `PASS(取到 2 项)` | ✅ |
| L2 | `class Helper: expected_templates.pop()`（类体当场执行，但 `_own_nodes` 跳过 `ClassDef` 体） | 漏面，称**不红** | `binds=1` → `PASS(取到 2 项)` | ✅ |
| L3a | `except … as expected_templates` | 漏面，称**不红** | `binds=1` → `PASS(取到 2 项)` | ✅ |
| L3b | `import os as expected_templates` | 漏面，称**不红** | `binds=1` → `PASS(取到 2 项)` | ✅ |
| L3c | `def expected_templates(): …` | 漏面，称**不红** | `binds=1` → `PASS(取到 2 项)` | ✅ |
| F1 | `[x for x in …]` 推导式同名变量算成第二处绑定 | 误报，称**红** | `binds=2` → `RED(binds=2!=1)` | ✅ |
| F2 | `expected_templates: list[str]` 纯注解算成绑定 | 误报，称**红** | `binds=2` → `RED(binds=2!=1)` | ✅ |
| F3 | `x[:][0] = "renamed"` 改切片副本仍算写入 | 误报，称**红** | `others=['写它的下标 / 属性']` → `RED` | ✅ |

**`MISMATCH_COUNT = 0`** —— 6 条主张（L3 拆成 a/b/c 共 8 格）**逐条实测成立**，
docstring 里的漏面与误报清单**不是推测，是实测**。

**验伪锚（同次执行）**：已知必红形态 `.append()` 实测 `RED(others=['调用就地变更方法 .append()'])`
⇒ 本探针的「红」判定不是恒 `False`，上表那 5 个「不红」是真的分辨出来的，不是判据空转的产物。

**补格 `F2-only`（对照，无 docstring 主张）**：只有纯注解、无任何赋值 → `binds=1`，
红在「那处绑定不是普通赋值 / 取不到字面量」。此格正是 4-A.13 表里两版实现**行为分叉**的那一例。

⚠️ **本节未证明什么**：这 8 格证明的是「docstring 说漏的确实漏、说误报的确实误报」，
**不证明这 3 类漏面就是全部漏面** —— 穷尽性正是 r4 证伪、本卡已撤回并登记移交的那一条（§六.16 / §七.14）。

---

## 五、复核（送 Codex 前的自审 + Codex D-15 多轮）

### 5.0 送 Codex 前的只读多维对抗自审（入库记录 `SELF-REVIEW-adversarial-20260916.md`）

Workflow `red-hygiene-self-review`（run `wf_3f3f97db-61a`，29 agents / 489 tool 调用），
5 个维度独立审查 → 每条 finding 交独立反驳式验证（默认立场「不成立」）。

- findings **23** 条；反驳流程判「成立」3 条；**主 session 逐条独立复核后判成立 17 条**。
- ⚠️ **反驳流程本轮偏松**：19 条「不成立」里有 14 条实际成立（多条验证 agent 正文已核实
  「报告者说的属实」却因「严重度只配 LOW」把 `refuted` 置 true = 把严重度混进了成立性）。
  本卡**未采信** `refuted` 字段，全部自核。
- ⚠️ **覆盖缺口**：`verify:red-green-integrity:RG-3` 的验证 agent 六次尝试全部停滞，
  该条**从未经过独立反驳流程**（主 session 自核结论：成立）。

自审直接导致 3 处代码改动 + 15 处存档更正，见 commit `b38e1d04`。

### 5.1 Codex r1 —— 绑 `8bfcdfce`，**不绑最终 HEAD，不作终审**

存档 `_bmad-output/审查/codex-review-CARD-RED-HYGIENE-r1.md`（首部按协议 §2.1 六行
blockquote，会话头三行自证：`OpenAI Codex v0.153.3`（第 2 行）/ `model: gpt-6-astra`（第 5 行）/
`reasoning effort: ultra`（第 9 行））。

计数：**BLOCKER 0 / HIGH 1 / MEDIUM 3 / LOW 4**。
审查期间本 session 提交了 `b38e1d04`，Codex 在报告末尾自行实测并如实声明
「diff 非空：3 files changed, 27 insertions(+), 9 deletions(-)」。

逐条处置见 `RESPONSE-codex-r1-20260916.md`。摘要：

| 条目 | 处置 |
|---|---|
| **HIGH-1** 目录级「不增」 | ⛔ **车道给理由但不自判通过**（D-15），裁定权在主 session。⚠️ **车道随后在最终 HEAD 上自己也跑出了 `>` = 1**（35 failed / `blocked=1` / 同一条 `candidate422`），已撤回原先「车道两跑都是 0」的对照式表述，验收单改为不声称 `>` = 0。现有理由：① Codex 第一跑的 33 条 `>` 是其环境 Node 缺 `libllhttp.9.3.dylib`，Codex 已自行归因；② 承接红的那条正是协议 §3 第 79 行点名的 W4 哨兵载体（`candidate422` ↔ `mock_warning`），协议明令「绑 `blocked=` 次数 + 失败正文，**不绑 nodeid**」，且失败正文逐字就是哨兵指纹、连接被拦未连上现网；③ 同一现象在**两个独立环境、两个不同 SHA** 上同形出现，而本卡三个 commit 未碰任何端口 / Neo4j / conftest 文件；④ 归属侧 Codex 给了更强对照（`$PREV` 已入库的 `epw-unit-close7.nodeids` 与本卡存档同为 34 条红）|
| **MEDIUM-1** guard 漏「绑定后就地改表」 | ✅ 已修（作用域收窄 + 就地改表检测 + 覆盖声明收窄），用 Codex 的方法复验 11 种形态 |
| **MEDIUM-2** 第 0 分钟「工作树干净」证据不足 | ✅ 接受，**记为未证实**（空目录不计脏项，事后解释不能追认），见 §六.9 |
| **MEDIUM-3** 最终 commit 的 `python-typecheck` 未被独立证明 | ✅ 接受，本卡最后一个 commit 落盘完整 pre-commit 输出；前两个 commit 标记历史 PARTIAL |
| **LOW-1** 「零 await = 正文未执行」措辞过宽 | ✅ 已修（收窄为「没走到那一次 LLM 调用」） |
| **LOW-2** 计数/索引/行号三处 | ✅ 全部已修（含 hunk 头 vs 实际被改行的精度更正） |
| **LOW-3** 定性结论超采样 | ✅ 送审前自审已同批修正，两边结论一致 |
| **LOW-4** 地盘证据未进被审提交 | ✅ 已随 `b38e1d04` 入库 |

### 5.2 Codex r2 —— 绑 `2c740216`（当时的最终 HEAD），**代码面 diff 为空**

存档 `codex-review-CARD-RED-HYGIENE-r2.md`（首部按协议 §2.1；会话头三行自证同 r1）。
计数：**BLOCKER 0 / HIGH 0 / MEDIUM 6 / LOW 3**。
Codex 末尾自行实测 `git diff --stat <审SHA> HEAD -- . ':(exclude)_bmad-output'` **输出为空**。

⇒ **D-15 的终审条件（绑最终 HEAD 的一轮 BLOCKER=0 且 HIGH=0）在 r2 这一轮已满足。**

#### 5.2.1 r2 撤销了 r1 的 HIGH-1，依据比车道给的强

Codex 直接去翻 `$PREV` **已入库**的
`evidence-b13-integ/unit-integ5-20260911T010612.txt`：第 **597–606** 行已出现同一条
`candidate422`、同一 `::1:7691 / MainThread` 指纹、同样的 JSON 降级；第 **1143** 行同为
`blocked=1, advisory=0, unaccounted=0`；相关调用链相对 `$PREV` 未被本卡修改。
⇒ **该现象早于本卡，有原始日志为证**，不是推断。

**车道接受其对论证形式的批评**：Codex 明确说「不能仅靠『几个 SHA 都出现过』或
『同 SHA 有时通过』」。车道那套五跑非确定性对照只能说明「与代码状态无关」，
**定位不了它早就存在**。`FINAL-sentinel-5runs-*.txt` 的结论已据此收窄
（并写明它没有复现协议所述的 `candidate422` ↔ `mock_warning` 翻转本身）。

#### 5.2.2 逐条处置（全文见 `RESPONSE-codex-r2-20260916.md`）

| 条目 | 处置 |
|---|---|
| **MEDIUM-1** guard 仍漏三种写法 | ✅ **修**（本可登记不阻断，但那是本卡自己写进去的「多 target 被覆盖」逻辑错误，且它让 docstring 里「门通过时声明与运行时必然一致」成了假话）。三种漏面 `a[0] += "-x"` / `del a[0], b[0]` / `a[0] = b[0] = "x"` 车道逐条复现属实。修法 + 19 格自校验复验见 §四-A.13 |
| **MEDIUM-2** 协议用 `grep -c` 数拦截次数（对 0/1/9 恒得 1） | 登记移交**协议卡**（批级资产非本卡地盘）。并注明这条削弱了车道先前引用该判据的力度 |
| **MEDIUM-3** 自审汇总五项全错 | ✅ 已修：改为脚本解析实数（18 / 2 行 3 条 / 15 / 15 / 3）+ 差异来源说明；**RH-1 的主 session 自核也被证伪**，改判为成立并加「自核不是可靠兜底」 |
| **MEDIUM-4** R2 证据未入库 | ✅ 已随 `f28c0f4a`（零代码）入库 |
| **MEDIUM-5** 第 0 分钟干净仍为 PARTIAL | ✅ 接受，**不追认**；`minute0-*.txt` 加撤回指针 |
| **MEDIUM-6** commit1 的 typecheck 执行历史 | ✅ 接受，保留**历史 PARTIAL 不追认** |
| **LOW-1** FINAL3 期望句与输出矛盾（rc=0 掩盖） | ✅ 已修：新探针**逐格写死预期并自己断言** |
| **LOW-2** 四处更正没同步到原件 | ✅ 四处逐条同步（docstring 过强句撤回 / attribution 撤回不足推理 / minute0 加 PARTIAL 指针 / 五跑结论收窄） |
| **LOW-3** territory 绑旧 SHA、`≤1` 条件与输出不符 | ✅ 已修：`FINAL-R3-territory-*.txt` 绑最终 SHA，工作树判据改为逐项列出 + 归属说明 |

### 5.3 Codex r3 —— 绑 `69c99d1a`，**BLOCKER 0 / HIGH 0 / MEDIUM 2 / LOW 3**，diff 空

维持撤销 r1 HIGH-1。⚠️ **r3 自述未完成独立目录级重跑**（收集前被只读环境的临时目录限制
挡住，`exit=1`），其目录级结论是对入库存档的复核 —— 如实转述，未当作独立验证。

处置全文见 `RESPONSE-codex-r3-20260916.md`。两条 MEDIUM 车道选择修：
**MEDIUM-1** 报出**第四类**漏面（`x = other = [..]` / `x, other = .., ..` / `with as x[0]` /
推导式 target / 默认参数里 `.pop()`）+ 一处新误报（`x[:].reverse()`）。
⇒ 车道判断「枚举语句类型追不完」，**改判定方式**为按 AST 自带的 `ctx=Store/Del` 判定。
**MEDIUM-2** 自审汇总在 RH-1 改判后仍未重算 ⇒ 第三次更正，这次**连计数规则一起写进去**。

---

### 5.4 Codex r4 —— **终审轮**，绑最终 SHA `ef21be2c`，**BLOCKER 0 / HIGH 0 / MEDIUM 1 / LOW 2**

**Codex 末尾自行实测 `git diff --stat <审SHA> HEAD -- . ':(exclude)_bmad-output'`
输出为空、exit=0**，并明写：「其余问题**登记移交，不要求继续改代码送第 5 轮**。」

⇒ **D-15 终审条件达成**。本轮之后车道**不再改代码**。

| 条目 | 处置 |
|---|---|
| **MEDIUM-1** `ctx` 判定仍非穷尽 | ⛔ **登记移交**（不改实现）。r4 实测两种漏面：`match` 的 `case [*name]`（`MatchStar.name` 是**字符串**、不产生 `Name(ctx=Store)`）与**类体定义时立即执行**（`class Helper: x.pop()`）；另注 `import`/`def`/`except as` 的名字绑定也不能只靠 `ctx` 收全。**当前生产源码不含这些形态**，r4 因此不升 HIGH。车道**撤回**了 r3 整改时自己写下的「构造上穷尽」那句话（纯 docstring，D-32） |
| **LOW-1** 新判定新增两种误报 | ⛔ 登记移交。推导式局部同名变量、无右值的纯注解会被算成第二处绑定而误报（**保守拦截**，方向上不放过真问题）。已逐条写进 docstring |
| **LOW-2** 回应声称已收窄、原件其实没改 | ✅ 已修（纯文档）。⚠️ 本卡**第三次**出现「回应声称已改、原件没改」，根因是声称与落地分两处、无对账机制 —— 已登记 |

**轮次账**（终审条件其实在 r2 就满足过，车道两次选择继续修 MEDIUM/LOW 才失绑）：

| 轮 | 绑定 | B/H/M/L | 绑当时最终 HEAD | 之后是否改代码 |
|---|---|---|---|---|
| r1 | `8bfcdfce` | 0/1/3/4 | ❌（审查期间车道提交了 `b38e1d04`） | 是 |
| r2 | `2c740216` | **0/0**/6/3 | ✅ diff 空 | 是 |
| r3 | `69c99d1a` | **0/0**/2/3 | ✅ diff 空 | 是 |
| **r4** | **`ef21be2c`** | **0/0**/1/2 | **✅ diff 空 exit=0** | **否** |

收尾 commit 只含**纯 docstring** 改动（D-32：去 docstring 后 `ast.dump` 与改前**逐字相同**、
非注释行 diff 为空，已实测）与 `_bmad-output`，不占轮次、不重置绑定。

---

## 六、本卡未证明什么

1. **未证 agents_health 端到端**。(b) 全在 mock 层：真 `AgentService.health_check` 对真 prompt 目录逐文件探 13 个 `.md` 的那条路径**没跑过**。防漂 guard 钉的是「mock 的名单 == 生产声明的名单」，**不是**「这 13 个 prompt 文件真的存在」。

2. **未证 MEMORY_RETRY 在运行期配置注入下也无消费方**。census 只覆盖静态 `git grep` + `backend/.env` 实读 + `extra="ignore"` 推理；`getattr(settings, name)` / `model_dump()` 之类的动态访问路径**没有普查**。

3. **未修 contract node-id pattern**，只定性。`specs/**` 与 `backend/app/models/**` 都不是本卡地盘（models 零写者）。补回 schema 文件 or 退役该测试，都要另立卡 + 各自地盘。

4. **未证两条 flaky 的根因**。⚠️ 原文写「只做到『排除同文件内互扰』这一步」——**该表述已撤回**：n=1 的一次整文件跑排除不了同文件互扰（见 §二 更正 ③）。本卡实际做到的只是「在跑过的 13 次里它们都是绿的」，成因未定，也没做隔离修复。

5. **未证 `agents.py:294` 的 docstring「12 expected templates」对任何运行路径有实际影响**。该文件非本卡地盘，只登记不改。

6. **未证 AC1.2 那条 degraded 用例的 fixture 语义与生产一致**。生产 `health_check` 的 `missing_templates` 是遍历 `expected_templates` 生成的 ⇒ 恒 ⊆ 期望表；而 mock 接受任意名字，AC1.2 注入的 `"review-board"` **生产永远不可能产生**。本卡只按卡文改了计数（`10 → 11`），**没有**修这层 fixture 失真。

7. **未证「462 文件格式漂移」这个总数在当前主干仍准确**。§3 用的是「`$PREV` 同文件对照」这个局部口径，不是全仓普查。

8. **未证 `spec-sync-root` 在别的卡上也只产生时间戳差异**。那是本卡改动面（删 Settings 字段、不进任何 request/response 模型）的结论。

9. **未证第 0 分钟工作树干净**（Codex r1 MEDIUM-2，记 PARTIAL）。存档只留计数不留 porcelain 原始路径，而**空目录本身不计脏项** ⇒ 事后解释不能追认。见 §四.1。

10. **未证前两个 commit 的 `python-typecheck` 实跑**（Codex r1 MEDIUM-3，记历史 PARTIAL）。它不在 `LEFTHOOK_EXCLUDE` 里，但没留原始输出，而该 hook 在工具缺席时也会 SKIP 并返回 0。只有本卡最后一个 commit 有完整 pre-commit 输出。

11. **未证防漂 guard 钉住的是运行时名单**。它钉的是「生产在**绑定处声明**的名单」；「声明 ≠ 运行时」的形态（`+=` / 下标赋值 / `.append` 等）被显式挡在门外报红 —— 这是靠**排除**达成的，不是靠读运行时值。
    ⛔ **本条原文末尾曾写「使门通过时两者必然一致」，该措辞已撤回**（2026-09-16 主 session 复核抓出）：
    它与本节第 16 条（Codex r4 MEDIUM-1 证伪穷尽性）和代码 docstring 的最终口径**直接冲突**。
    r4 整改时改了代码 docstring（明写「这**不等于**『门通过时两者必然一致』」），却漏改了本验收单
    —— 这正是本节第 18 条 / §七.16 登记的那个「回应声称已改 vs 原件实际未改」问题的**第四次**出现，
    也印证了台账里「两份手抄清单必然漂移」。准确口径：**排除掉的是本作用域内语法可见的那些写法，
    不含别名 / 传出去改 / 动态手段，也不含 §七.14 登记的 3 类已知漏面**。

12. **未证 Codex 第二跑那条 `>` 一定是哨兵漂移**。车道给的是协议 §3 的口径依据 + 两跑 `blocked=` 状态不同这一事实，**没有**在 Codex 的环境里复现并定位成因。

13. **未证自审的 23 条就是全部**。5 个维度是本 session 自己划的，维度之外没有 agent 看过；且其中 1 条（RG-3）的验证 agent 停滞，从未走完独立反驳流程。

14. **未证两条 flaky 的成因**（本条取代原第 4 条的措辞）。⚠️ 并且「本卡跑里它们一次都没红过」这句话
    在最终 HEAD 的第三跑上**已被自己推翻**：`candidate422` 在那一跑红了，且承接的是 W4 哨兵。
    本卡未定位到「为什么这一跑 `blocked=1` 而前两跑 `blocked=0`」——即哪个测试在什么条件下
    会去尝试连 7691。成因仍未定。

15. **未证任何 SHA 上的目录级「不增」**（措辞已由「最终 SHA」放宽 —— 本卡 HEAD 在写下该条之后
    又推进过，把结论钉在「最终 SHA」这个会移动的位置锚上本身就是错的）。十跑里有三跑 `>` = 1
    （`2c740216` 第 1 跑、`ef21be2c` 第 2 跑、当前 HEAD `0bc3baef` 第 10 跑），
    见 §四-A.10。车道**不自判通过**；Codex r2/r3/r4 均判该条不阻断本卡，依据是
    `$PREV` 的历史原始日志（不是车道那套「非确定性」论证）。裁定权在主 session。

16. **未证防漂 guard 的写入检测是穷尽的**（Codex r4 MEDIUM-1）。⛔ 车道在 r3 整改时写下的
    「按 `ctx` 判定构造上穷尽」**已被证伪并撤回**：`match` 的 `case [*name]`
    （`MatchStar.name` 是字符串、不产生 `Name(ctx=Store)`）与**类体定义时立即执行**
    （`class Helper: x.pop()`）两种形态能改到名单而门不红；`import`/`def`/`except as`
    的名字绑定同样不能只靠 `ctx` 收全。当前生产源码不含这些形态，但**未来不受约束**。

17. **未证该 guard 不会误报**（Codex r4 LOW-1）。推导式局部同名变量、无右值的纯注解、
    `x[:][0] = ...` 会被算成写入而报红（**保守拦截**，方向上不放过真问题，但理由不准确）。

18. **未建立「回应声称 vs 原件实际」的对账机制**。本卡三次出现「回应里写已改、原件其实没改」
    （r1 LOW-4 / r3 LOW-2 / r4 LOW-2），每次都只做了逐次更正。
    ⛔ **更新（2026-09-16 主 session 复核）：这个数字要从「三次」改成「七次」** ——
    本轮在**没有任何外部审查者参与**的情况下，又自查出四处同型失实，全部是「改了 A 没改 B」：
    (i) §六.11 的「使门通过时两者必然一致」（r4 整改改了代码 docstring、漏改验收单）；
    (ii) §三 贴的 `286 insertions` 绑 `b38e1d04` 却标称「最终 HEAD」，其后 R3/R4 两版都没同步；
    (iii) §四-A.13 引绑旧实现的 R3 探针、§四-A.12 引逻辑副本，都没标版本归属；
    (iv) `FINAL-R4-guard-shapes-*.txt` 抬头仍留着已撤回的穷尽性声明。
    ⇒ **频次不是「偶尔」，是每一轮整改都会产生至少一处**。逐次更正治不了它，
    因为漏掉的那一处恰恰是「这次没想到要看」的那一处。见 §七.16 的建议。

19. **未证本轮四处自查已是全部**。⛔ 这一条必须写在前面那条之后 ——
    §六.18 刚刚把「三次」改成「七次」，靠的是主 session 这一轮的人工通读，
    **而人工通读正是前四轮每次都漏掉东西的那个方法**。本轮新找到四处，
    没有任何依据说明第五处不存在；真正的判据（机械对账）仍未建立。
    **本条的存在本身就是 §六.18 的例证**：一个刚被证明不可靠的方法，
    不会因为这次用它找到了东西就变可靠。

20. **未证 `FINAL-R5-docstring-claims-*.txt` 的复刻与真实调用点无偏差**。
    该探针复刻了 `_production_expected_templates()` 的取值三步（`_own_nodes` → `_collect_writes` →
    binds/others 判定），而不是直接调用它 —— 因为后者把源码取自 `AgentService.health_check` 写死了，
    喂不进对照输入。复刻用的是**入库的真 helper**（非逻辑副本），但「复刻的那三步 == 真函数的那三步」
    这件事本身**只经过人工比对，没有机械判据**。若复刻漏了真函数里的某个分支，
    `MISMATCH_COUNT = 0` 就是复刻误差而非真实行为。已列为 r5 请复核项第 7 条。

---

## 七、台账待登记条目

1. **`backend/app/config.py` 与 T5 的声明交集 + 串行次序** —— 交集手册已记，**次序未定**，请主 session 在合并队列定序（本卡只删 `MEMORY_RETRY` 段，T5 只新增一项且避开该段，hunk 不重叠）。

2. **auth 两文件路径更正 + U10-E 独占补登** —— 实测在 `backend/tests/unit/`（设计稿 §3 写成 `backend/tests/api/...`）；「U10-E 独占」目前只是车道内约定，手册 §一地盘互斥段未列。

3. **两个新增地盘文件** —— `backend/tests/unit/test_cache_configuration.py` 与 `backend/.env.example`（§3 未列、不在 R-B14-4 已批准扩充表内），系 (f) 退役的连带必改面。

4. **contract `test_pattern_matches_json_schema` 的处置（范围须按本卡更正改写）** —— 不是「schema/model pattern 对齐」（两侧 pattern 逐字相同），而是：补回 `14f0412d` 连带删除的 `specs/data/canvas-node.schema.json`（内容可从 `14f0412d^` 完整取回），或退役这条自 2026-02-07 起就没跑到过比对逻辑的契约测试。另立卡 + 各自地盘。

5. **两条 flaky 的定性结论与建议（结论已按自审 RG-3 / EV-02 + Codex r1 LOW-3 改写）** ——
   ⚠️ 本卡原先写的「卡文假设不成立、摆动来自跨文件」**已撤回**：n=1 的一次整文件跑
   排除不了同文件互扰，且本卡 13 次跑里该 flake 一次都没红过。
   **关键既有信息**：协议 §3 第 79 行已记载这两条 nodeid（`candidate422` ↔ `mock_warning`）
   正是 W4 哨兵红的载体、会在彼此之间翻转，并明令判据「绑 `blocked=` 次数 + 失败正文，
   不绑 nodeid」。建议接收卡从该机制查起，而不是从「跨文件顺序」查起。

6. **`ENRICHMENT_CACHE_MAXSIZE` 是同族剩余死配置** —— `app/config.py::Settings.ENRICHMENT_CACHE_MAXSIZE` 仍在但 `backend/app` 零消费方，`test_cache_configuration.py` 里 4 处 `xfail(strict=True)` 的 reason 引用它，接收卡仍是 CARD-CONFIG-CLEANUP。本卡只把那 4 处的 `config.py:678` 行号引用改成符号名（本卡删 16 行使其漂到 `:662`），**未退役该字段**（越出本卡 (f) 的点名范围）。

7. **AC1.2 fixture 失真（见 §6.6）** —— `MockAgentService` 允许 `missing_templates` 含期望表之外的名字，生产不可能产生该状态。建议登记进 agents_health 的后续卡。

8. **`agents.py:294` docstring 仍写「12 expected templates」** —— 生产真相表已 13，该文件非本卡地盘，登记不改。

9. **本卡删 `config.py` 16 行使卡外 5 个文件 10 处 `config.py:<行号>` 锚失实** —— 逐条
   新旧映射见 §二 更正 ⑤。涉及 `validate_learning_events.py`(3) /
   `test_learning_events_schema_contract.py`(2) / `test_lancedb_vault_isolation.py`(3) /
   `test_vault_switch.py`(1) / `docs/learning-events-schema-v1.md`(1)，全在本卡地盘外。
   建议接收卡统一改成符号名而不是新行号（否则下次增删再漂一遍）。

10. **生产 `security.py` 的两张矩阵状态不同，须分开判** —— `:15` 的 REST 矩阵已失实
    （代码 fail-closed 而表写 allow）；`:191` 的 WebSocket 矩阵可能仍准确
    （`:228` 的 WS Branch 2 代码确实放行）。该文件本卡禁改，登记移交。见 §二 更正 ⑥。

11. **目录级「不增」的裁定权在主 session**（D-15：车道对 HIGH 可写理由但不能自判通过）。
    ⚠️ **本卡自己在最终 HEAD 上也跑出了 `>` = 1**（不是只有 Codex 那边出现）：
    35 failed / `blocked=1`，那条 `>` = `candidate422`，失败正文是协议 §3 的 W4 哨兵指纹。
    三跑对照 `blocked=` 分别为 0 / 0 / 1。建议主 session 按协议 §3 的口径
    （绑 `blocked=` 次数 + 失败正文，不绑 nodeid）裁定，并考虑是否另立卡处理
    「哨兵归属漂移导致逐 nodeid diff 不可用」这件事本身。
    ⚠️ **最硬的一条**：跑 3/4/5 绑**同一个 commit `2c740216`**，结果 35 / 34 / 34 ——
    同一份代码两种结果，差异与 `blocked=` 严格同步（五跑 5/5）。
    完整证据：`FINAL-sentinel-5runs-*.txt`、`FINAL-R2-unit-comm-*.txt`、`RESPONSE-codex-r1-20260916.md`。

12. **自审流程本身的口径问题**：本轮反驳式验证把严重度判断混进了成立性判断
    （判「不成立」的里面有 16 行实际成立）。若后续批次复用这套自审，`refuted` 字段
    应只回答「是不是真的」，严重度另立字段。
    ⚠️ 附带：该解释**只有摘要、没有保留 verifier 正文**，因而未被独立确认（Codex r2/r3 指出）。

13. **协议 §3 的 W4 判据本身有缺陷，建议另立协议卡**（Codex r2 MEDIUM-2，r3/r4 复核成立）：
    对 `blocked=0` / `blocked=1` / `blocked=9` 三种单行汇总分别跑 `grep -c 'blocked='`
    **结果全是 1** —— 该命令数的是「有几行含这个串」，不是「拦了几次」，
    **证明不了「次数恒定」**。另 `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS` 是输出前缀、
    不是它读的环境开关。判据应解析汇总行里的**数值**并保留失败原因与历史归属证据。

14. **防漂 guard 的两类已知缺口 + 三类已知误报**（Codex r4 MEDIUM-1 / LOW-1）：
    缺口 = `match` 的 `case [*name]`、类体定义时立即执行；
    误报 = 推导式局部同名变量、无右值纯注解、`x[:][0] = ...`。
    后续修复应按 r4 的建议**处理名字绑定与作用域语义**，而不是继续在 `ctx` 上打补丁。

15. **「末次判据存档 ∉ 被审 SHA」是结构性问题**（本卡出现两次：r1 LOW-4 / r3 LOW-3）：
    收工判据必然晚于最后一个 commit，所以这个缺口会在每张卡上重复出现。
    建议批级统一处置（例如允许「判据存档补提交」并在台账写明其与被审 SHA 的先后关系）。

16. **「回应声称已改 vs 原件实际未改」缺对账机制**（本卡**七次**：r1 LOW-4 / r3 LOW-2 / r4 LOW-2
    ＋ 2026-09-16 主 session 自查的四处，逐条见 §六.18）：
    根因是「声称」写在 RESPONSE、「落地」在原件，两处无机制对账。建议批级加一条收工判据。
    ⛔ **本条的严重度请主 session 按「七次」重估，不要按原先的「三次」** ——
    三次像偶发，七次说明它是**流程的默认产出**而不是疏忽。具体建议两条机械判据：
    (甲) **数字类**：验收单里每个引用存档数字的地方都标注来源文件名，收工时脚本逐条回读该文件比对
    （本卡 §三 那处失实，只要有这条就抓得到 —— `286` 在 `FINAL-territory-*.txt` 里，
    而该文件首部自写 `HEAD=b38e1d04` ≠ 最终 HEAD，两个字段一比即红）；
    (乙) **撤回类**：每次撤回一句声明，用被撤回措辞的关键词全仓 `grep`，命中处逐一处置
    （本卡那句穷尽性声明同时躺在代码 docstring、存档抬头、验收单三处，
    改一处漏两处 —— 一条 `grep` 就能列全）。

17. **多版本同名存档缺「哪版是当前」的机器可读标记**（本卡两族共 11 份）：
    `territory` 族 6 份（268 / 267 / 286 / 419 / 429 / 446）、`guard-shapes` 族 5 份
    （其中 3 份绑三种**不同的实现**）。命名只靠 `FINAL` / `FINAL-R3` / `FINAL-R4` 前缀区分，
    **谁绑哪个 SHA、哪版是当前**要打开文件读首部才知道，验收单因此引错了两次（§三、§四-A.13）。
    建议批级规定：存档首部必须有一行机器可读的 `BOUND_SHA=<40 位>`，收工判据据此自动挑最新那份。

18. **`FINAL-sentinel-9runs-*.txt` 的文件名已与内容不符**（本轮新增第 10 跑后）：
    该档仍叫 `9runs`，而目录级样本现为 10 跑。本卡**未改其文件名**（改名会让既有引用断链，
    且它内容确实只含前九跑，没有失实）；第 10 跑另存 `FINAL-R5-unit-close-*` /
    `FINAL-R5-unit-comm-CORRECTED-*`。登记此处命名与样本数的漂移，供主 session 定夺是否统一。

19. **`comm` 类判据的前缀提取口径建议写进协议**：
    红基线文件混有 `FAILED ` 与 `ERROR ` 两种前缀，只脱其一再取字段 1 会让另一类**静默塌成一条**
    （本轮实测：BASE 从 64 塌成 36、`'<'` 从 30 塌成 2）。更麻烦的是这种错**不一定改变结论** ——
    本轮 `'>' = 1` 与那条 nodeid 在两种口径下完全相同，靠看结论发现不了。
    建议协议统一规定：两侧一律 `awk '{print $2}'`，且判据必须**同时**打印 BASE 计数供交叉核对。

---

## 八、DoD-3 段 4-B：用户产品体验

> 句型「我做 X → 我看到 Y → 我感觉 Z」，不写技术词。

1. 我打开学习助手、点开「系统状态」那一页 → 我看到它列出的可用能力条数，和这套系统实际装着的能力条数**对得上**（以前少报了一条）→ 我感觉这个状态页说的话可以信，而不是一个永远显示「都正常」的摆设。

2. 我（作为把这套东西装到自己电脑上的人）忘了填那个内部访问口令、就直接开着「开发模式」把服务跑起来 → 我看到它**直接拒绝**处理请求，而不是悄悄放行 → 我感觉就算我自己配漏了，它也不会在我不知情的时候把门敞开着。

3. 我翻开这两份检查清单想弄明白「开发模式下到底放不放行」→ 我看到清单上写的结论和它实际的行为**一致**（以前清单写「放行」、实际是「拒绝」，两边打架）→ 我感觉我可以照着清单理解这套系统，不用每次都自己去试一遍才敢信。

4. 我在设置文件里翻到两个关于「重试等待多久」的选项，想调调看 → 我看到它们已经**不在**设置清单里了 → 我感觉不用再花时间去试一个根本不起作用的旋钮（它们早就没人读了，只是一直摆在那儿）。

---

## 九、附：本卡自查发现并自行更正的三处

1. 写了两行硬编码的「以上为空」，而其上方命令实际有输出 → 按实数更正并作废原件（§2 更正 ④）。
2. ruff 验伪锚传了不存在的配置路径、ruff 以「参数错误」rc=2 退出却被当成锚 → 换成「把 F821 注入判据自己的文件集」的有效锚（§4-A.9）。
3. `stderr` 入库判据的取名面写成了整棵树（得 3）而非本卡 commit → 更正为本卡 commit（得 0），并实测那 3 个在 `$PREV` 就已存在（§3）。

另有一处**由本卡改动造成的失实**被自查发现并修掉：本卡删 `config.py` 16 行，使 `test_cache_configuration.py` 里 4 处 `config.py:678` 的行号引用漂到 `:662`；已改为符号名 `app/config.py::Settings.ENRICHMENT_CACHE_MAXSIZE`，避免再随增删漂移。
