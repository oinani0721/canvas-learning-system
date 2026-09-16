# UAT — CARD-RED-HYGIENE（RED 卫生收尾）

> 批次：`BATCH-2026-09-11-第十四批` · 车道 `card-t10-red`（分支 `card/t10-red`）· 本车道第 **5/5**
> 本卡 commit：`8bfcdfcea46c8e2c6408fa6ebd85851c7c9cce82`
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
| (i) | tests/unit 目录级对 `$BASE`：`<` = 30 / `>` = 0 | ✅ |
| (j) | Codex 多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0 | 见 §5 |
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

⇒ 接收卡的任务**不是**「对齐两个分歧的 pattern」，而是二选一：
(甲) 把 `14f0412d` 连带删掉的 schema 文件补回（内容可从 `14f0412d^` 完整取回）；
(乙) 退役这条自 2026-02-07 起就没跑到过比对逻辑的契约测试。

证据：`contract-nodeid-CORRECTED-20260916T130606.txt`

### 更正 ③（(e)）：flaky ① 的根因不是「同文件内测试相互影响」

卡文 §〇 写 `test_accept_candidate_already_accepted_returns_422` 的根因是「同文件内测试相互影响」。

实测（`flaky-characterization-20260916T125210.txt`）：
- 定向单跑 ×5 → 5/5 passed
- **整文件跑 → 14 passed（全绿）**

整文件全绿直接排除了「同文件内互扰」。两条 flaky 的摆动只可能来自**跨文件**的目录级顺序 / 跨文件共享状态。本卡目录级跑里两条也都不在红集内。

### 更正 ④（自查）：本卡自己写出过一份含假陈述的证据，已作废并取代

第一版 contract 证据里我写了两行**硬编码**的「(以上为空 = …)」，而其上方的 `git log` 实际有输出 —— 那是关于证据本身的假陈述。已按实数更正（删除型 1 条 / 总计 6 条），原件保留并加作废横幅：`contract-nodeid-20260916T130232-SUPERSEDED.txt`，取代件见更正 ②。
同类还有一份 `ruff-20260916T130748-SUPERSEDED.txt`：其验伪锚传了不存在的 `--config backend/pyproject.toml`，ruff 以 rc=2「参数错误」退出 —— 那个锚**什么都没证明**，已由带有效锚的 `ruff-with-anchor-*.txt` 取代。

---

## 三、地盘与合规

**代码面恰好 6 文件**（`territory-headcommit-*.txt`）：

```
backend/.env.example                                |  16 ---
backend/app/config.py                               |  16 ---
backend/tests/api/v1/endpoints/test_agents_health.py| 115 +++++++++++++---
backend/tests/unit/test_cache_configuration.py      |  90 +++++----------
backend/tests/unit/test_sync_batch_auth.py          |  24 +++-
backend/tests/unit/test_system_endpoint_auth.py     | 123 ++++++++++++++++++-
6 files changed, 267 insertions(+), 117 deletions(-)
```

- 验伪锚①：单查 `config.py` 必命中 → 命中 `1 file changed, 16 deletions(-)`
- 验伪锚②：去掉 `':(exclude)_bmad-output'` 后 `_bmad-output` 面 = 22 文件，带 exclude 时 = 0 ⇒ exclude pathspec 确实在起作用
  ⚠️ 该锚在 commit **之前**结构上不可能成立（evidence 当时是 untracked，`git diff` 看不见），commit 前那份 `territory-worktree-*.txt` 已加作废说明。
- `backend/openapi.json` 与 `$PREV` **blob 逐字节相同**
- 本卡 commit 新增文件里含 `stderr` 的 = **0**
  ⚠️ 首次我把这条判据的取名面写成了整棵树（得 3），已更正：那 3 个是 `$PREV` 就存在的历史存档。

**生产源码零改动**：(d) 全程只用 `app.dependency_overrides`，未动 `system.py` / `security.py` / `main.py` 任何一行。

**`LEFTHOOK_EXCLUDE=python-lint,spec-sync-root`**（依据全文见 `lefthook-exclude-justification-*.txt`）：
- `python-typecheck` **未**跳过，首次 commit 尝试时实跑并通过（`✔️ python-typecheck (3.07 seconds)`）。
- `python-lint`：失败的只有 `ruff format --check`（`ruff check` 全绿）。本卡**自清了自己引入的那一处**（`test_agents_health.py` 在 `$PREV` 格式是干净的 ⇒ 不享受过渡条款），剩余 dirty 集 = `{test_cache_configuration.py}` = 主干既有集，且漂移行 244-252 落在本卡全部改动 hunk 之外（最近的是 210-212 与 257-259），该段在 `$PREV` 逐字相同。依协议 §2.3 不顺手修存量。
- `spec-sync-root`：该 hook 会把 `backend/openapi.json` 塞进任何含 `backend/app/config.py` 的 commit（= 第 7 个文件 = 越界）。实测重生成只改 1 行 `x-generated-at`，`paths=197 schemas=357` 不变 ⇒ 本卡不改变 OpenAPI 面，跳过它并保持快照与 `$PREV` 逐字节相同。

---

## 四、DoD-3 段 4-A：技术 assert（Claude 自跑，逐条贴证据）

> 所有承重裁判 `2>&1 | tee` 落 `_bmad-output/审查/evidence-red-hygiene/`，末行 `rc=$pipestatus[1]`。
> 本段只**引用**路径与关键行，不自述数字。

### 4-A.1 第 0 分钟六项自证 — `minute0-20260916T021417.txt`

pwd / 分支 `card/t10-red` / `$PREV=f294878b`（`git log -1` 含 `CARD-EPW-COVERAGE`）/ venv+env / `pyright app` = `0 errors, 81 warnings, 0 informations` / `$BASE` `grep -vc '^#'` = `64`。

⚠️ 该存档里 `git status --porcelain | wc -l` 显示 **1**：因为落盘前先 `mkdir` 了 evidence 目录，那 1 项就是该目录本身（`?? _bmad-output/审查/evidence-red-hygiene/`）。开工首测（落盘之前）实测为**空**。

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

### 4-A.10 (i) tests/unit 目录级 — `unit-close-20260916T131111.txt` / `unit-comm-20260916T131636.txt`

跑法（R-B14-3：`cd backend` 后 `--ignore` 用相对路径）：
`cd backend && PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest tests/unit --ignore tests/unit/test_deploy_vault_sh.py -q -p no:cacheprovider`

- 汇总行：`34 failed, 5166 passed, 35 skipped, 19 xfailed, 171 warnings in 300.59s`
- nodeid 口径 comm 对 `$BASE`（64）：**`<` = 30，`>` = 0**
- 两条已知 flaky 均**不在**本跑红集中
- W4 哨兵（协议 §3 必贴）：`NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)`，`blocked=` 出现次数 = 1（候选树常态，未设攻击次数）

**归属如实声明** — `attribution-20260916T131649.txt`：
本卡 4 个测试地盘文件在 `$BASE` 里各有 **0** 条红，在本跑红集里也各有 **0** 条。
⇒ **本卡对那 30 条 `<` 的贡献是 0**，30 条全部来自同车道前四卡（T10-A/B/C/D，在 `$PREV` 之前就已转绿）。
本卡在目录级的实际效果是「**不增**」，不是「减 30」。

### 4-A.11 (d) 顺序污染判据 — `auth-order-pollution-*.txt`

对照用例结束时只 `pop` 掉 `require_internal_api_key`、保留 `get_settings` 覆盖。三种顺序（默认 / 对照排最前 / 对照 + 另一文件）全绿。

⚠️ **该判据的局限如实写明**：同次验伪锚显示该文件 12 条测试**全部**在进门时自设 `app.dependency_overrides[get_settings]`（`grep -c` 实测 12，`def test_` 实测 12）。所以「残留覆盖」这一维**本身就不可能生效** —— 顺序判据对它不敏感，无污染的真正依据是：
(1) `require_internal_api_key` 在 `finally` 里被 pop；
(2) 12/12 用例进门自设 `get_settings`，残留立即被改写；
(3) fixture teardown 还有一次 `app.dependency_overrides.clear()` 兜底。

### 4-A.12 (b) guard 的形态覆盖 — `guard-ast-shapes-*.txt`

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

---

## 五、Codex 复核（D-15 多轮）

> 待填：每轮存档 `_bmad-output/审查/codex-review-CARD-RED-HYGIENE-rN.md`，首部按协议 §2.1 六行 blockquote（含 `codex-cli 0.153.3` 实测版本行 + `model:` 行 + `reasoning effort` 行并逐行括注行号）。

---

## 六、本卡未证明什么

1. **未证 agents_health 端到端**。(b) 全在 mock 层：真 `AgentService.health_check` 对真 prompt 目录逐文件探 13 个 `.md` 的那条路径**没跑过**。防漂 guard 钉的是「mock 的名单 == 生产声明的名单」，**不是**「这 13 个 prompt 文件真的存在」。

2. **未证 MEMORY_RETRY 在运行期配置注入下也无消费方**。census 只覆盖静态 `git grep` + `backend/.env` 实读 + `extra="ignore"` 推理；`getattr(settings, name)` / `model_dump()` 之类的动态访问路径**没有普查**。

3. **未修 contract node-id pattern**，只定性。`specs/**` 与 `backend/app/models/**` 都不是本卡地盘（models 零写者）。补回 schema 文件 or 退役该测试，都要另立卡 + 各自地盘。

4. **未证两条 flaky 的根因到行**。只做到「排除同文件内互扰」这一步（整文件全绿），**没有**定位到具体是哪个跨文件前序用例、哪个共享状态导致摆动，也没做隔离修复。

5. **未证 `agents.py:294` 的 docstring「12 expected templates」对任何运行路径有实际影响**。该文件非本卡地盘，只登记不改。

6. **未证 AC1.2 那条 degraded 用例的 fixture 语义与生产一致**。生产 `health_check` 的 `missing_templates` 是遍历 `expected_templates` 生成的 ⇒ 恒 ⊆ 期望表；而 mock 接受任意名字，AC1.2 注入的 `"review-board"` **生产永远不可能产生**。本卡只按卡文改了计数（`10 → 11`），**没有**修这层 fixture 失真。

7. **未证「462 文件格式漂移」这个总数在当前主干仍准确**。§3 用的是「`$PREV` 同文件对照」这个局部口径，不是全仓普查。

8. **未证 `spec-sync-root` 在别的卡上也只产生时间戳差异**。那是本卡改动面（删 Settings 字段、不进任何 request/response 模型）的结论。

---

## 七、台账待登记条目

1. **`backend/app/config.py` 与 T5 的声明交集 + 串行次序** —— 交集手册已记，**次序未定**，请主 session 在合并队列定序（本卡只删 `MEMORY_RETRY` 段，T5 只新增一项且避开该段，hunk 不重叠）。

2. **auth 两文件路径更正 + U10-E 独占补登** —— 实测在 `backend/tests/unit/`（设计稿 §3 写成 `backend/tests/api/...`）；「U10-E 独占」目前只是车道内约定，手册 §一地盘互斥段未列。

3. **两个新增地盘文件** —— `backend/tests/unit/test_cache_configuration.py` 与 `backend/.env.example`（§3 未列、不在 R-B14-4 已批准扩充表内），系 (f) 退役的连带必改面。

4. **contract `test_pattern_matches_json_schema` 的处置（范围须按本卡更正改写）** —— 不是「schema/model pattern 对齐」（两侧 pattern 逐字相同），而是：补回 `14f0412d` 连带删除的 `specs/data/canvas-node.schema.json`（内容可从 `14f0412d^` 完整取回），或退役这条自 2026-02-07 起就没跑到过比对逻辑的契约测试。另立卡 + 各自地盘。

5. **两条 flaky 的定性结论与建议** —— 卡文写的「同文件内测试相互影响」**不成立**（整文件跑全绿）；摆动来自跨文件的目录级顺序 / 共享状态。建议另立卡做跨文件隔离定位，本卡只定性。

6. **`ENRICHMENT_CACHE_MAXSIZE` 是同族剩余死配置** —— `app/config.py::Settings.ENRICHMENT_CACHE_MAXSIZE` 仍在但 `backend/app` 零消费方，`test_cache_configuration.py` 里 4 处 `xfail(strict=True)` 的 reason 引用它，接收卡仍是 CARD-CONFIG-CLEANUP。本卡只把那 4 处的 `config.py:678` 行号引用改成符号名（本卡删 16 行使其漂到 `:662`），**未退役该字段**（越出本卡 (f) 的点名范围）。

7. **AC1.2 fixture 失真（见 §6.6）** —— `MockAgentService` 允许 `missing_templates` 含期望表之外的名字，生产不可能产生该状态。建议登记进 agents_health 的后续卡。

8. **`agents.py:294` docstring 仍写「12 expected templates」** —— 生产真相表已 13，该文件非本卡地盘，登记不改。

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
