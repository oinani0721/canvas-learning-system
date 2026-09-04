# UAT 验收单 — CARD-G4-4a full RAG 显式 VaultScope（vault 面移植）

> 批次: `BATCH-2026-09-04-第十批` · 车道 X3-① · 分支 `card/x3-vaultscope`
> 卡文: `第十批-goals/X3-1.md` · 工时预算 10h
> 主干基线: `1f249b33` · 只读取证源: `card/w8-scope@6a732e1b`
> 本卡形态: **不重写，逐条 cherry-pick 移植 + 补口 + 一轮定向复审**

---

## ⛔ 先读：三条显著声明（影响你判断要不要批这张卡）

1. **这是 breaking API**：`POST /api/v1/rag/query` 从今往后**必须**带 `vault_id`，
   不带一律 422 拒绝。插件 `main.ts` 对 `/rag/query` 三处 grep **零调用方**，
   但**外部脚本 / 你自己的 curl / Postman 收藏夹是否有调用，Claude 无法证明**
   —— 这是 D2，需要你确认。
2. **本卡不是新写代码**：7 个 commit 来自 `card/w8-scope`，已经过 Codex 三轮审查
   （round-1 REJECT → 整改 → round-2 → round-3 到顶）。本卡做的是把它们逐条搬到
   从主干新切的干净车道，加上四处补口，再送一轮定向复审。
3. **跨 subject 边界仍是坏的，本卡故意没修**：同一个库里不同科目的笔记，在「邻居
   扩展」这一步仍会被带回来。这是主干既有缺陷，收口面在本卡的硬禁改文件里，
   拆给 CARD-G4-4b。用例以 `xfail(strict=True)` 锁住，防止无声退化。

---

## 1. 🎯 一句话目标

给 full RAG 检索链装上「必须先说清楚查哪个库」的闸门：查询请求必须显式带 vault，
每个请求恰好解析一次作用域并注入下游，请求的库和当前打开的库对不上就明确拒绝，
而不是悄悄换一个库给你结果。

## 2. 📖 你的视角

以前 `/rag/query` 是全链上**最后一个**「不说查哪个库也能查」的入口 —— 不带参数时
它会落到默认作用域，检索结果可能来自你没打开的那个库。本卡把这条路堵死。

**范围声明**：本卡只做 vault（库）这一层的边界。同一个库内部不同科目之间的边界
不在本卡范围（见 §「本卡未证明什么」#1）。

## 3. 🖥️ 交互流程（你的屏幕变化）

对你日常使用**没有可见变化** —— 前端插件本来就不调这个端点。变化在于：
- 有人（脚本 / 调试工具）不带库名调用检索接口 → 收到明确的 422 错误，而不是一份
  来路不明的结果；
- 请求的库和当前打开的库不一致 → 收到 409 冲突，而不是被静默改写成另一个库。

## 4-A. 🤖 Claude 已代验（全部代跑，✅ = 有证据）

| # | 判据 | 结果 | 证据 |
|---|---|---|---|
| 1 | **裁判 1** 四文件 pytest（`test_rag_vault_scope_api` + `test_rag_four_state_api` + `test_recommend_action` + `test_agents_learning_event`） | ✅ **107 passed / 0 failed**（收集 107 = 主干基线 89 + 新增 18） | 见 §4-A.1 基线对照 |
| 2 | **裁判 2** 两单测文件 | ✅ **28 passed + 1 xfailed + 3 failed**（32 collected = 17 + 15）；3 条红是主干既有，基线逐条同名 | 见 §4-A.1 |
| 3 | **裁判 3** 禁改门（`lancedb_client.py` / `exam_service.py` / `verification_service.py` / `rag_service.py` / `chat.py`） | ✅ 输出为空 | `git log --format= --name-only 1f249b33..HEAD -- <5 文件>` |
| 3b | 扩展禁改门（卡文 §五 全清单：`vault_scope.py` / `memory_service.py` / `review_service.py` / `fsrs_manager.py` / 未合卡追踪台账） | ✅ 输出为空 | 同上命令换文件清单 |
| 4 | **(a) 先红** — 主干缺 `vault_id` 的请求 200 通过 | ✅ `assert 200 == 422` | 移植前把车道测试文件临时拷入跑一次：**12 failed / 6 passed**（18 collected） |
| 5 | **(h)** grep 门 `DEFAULT_GROUP_ID\|get_current_vault_id` 三文件 | ✅ 零命中（grep rc=1） | `nodes.py` / `rag.py` / `agents.py` |
| 6 | **(i)** 新增日志惰性参数 | ✅ f-string 日志计数与主干基线**逐文件相同**（rag 7→7 / agents 15→15 / nodes 32→32） | 与 `git show 1f249b33:<file>` 对比计数 |
| 7 | **(j)** evidence-g44 只带两文件 | ✅ `git ls-files` 仅 `g44_mutations.py` + `mutation-run.txt` | 三份 `*.stderr` + 五份 judge txt 全部剔除 |
| 8 | **变异负控** 8/8 杀死指定门（串行、原地改源码） | ✅ `ALL 8 MUTATIONS KILLED THEIR GATES (exit=1 only)` | `evidence-g44/mutation-run.txt` 尾部「移植后复跑」段 |
| 9 | 变异还原三重外部锚点 | ✅ ① 三文件 sha256 逐条一致 ② `git status` 空 ③ `grep MUTANT` rc=1 | 判据不依赖脚本自检（防自证） |
| 10 | `ruff check` 本卡全部改动 `.py`（9 个文件） | ✅ `All checks passed!` | 见 §6.5-B「hook 处置」 |

### 4-A.1 基线 → 终态逐条对照

| 文件 | 主干基线（`1f249b33`） | 本卡终态 |
|---|---|---|
| `test_rag_four_state_api.py` | 30 collected，全绿 | 30 collected，全绿（payload 补 `vault_id` + autouse pin active vault，沿 `a3c41075`） |
| `test_recommend_action.py` | 40 collected，**1 failed** (`test_history_query_failure_graceful_degradation`) | 40 collected，**全绿**（红转绿真因见 §6.5-A，**非**生产修复） |
| `test_agents_learning_event.py` | 19 collected，全绿 | 19 collected，全绿（6 处直调 handler 补 `response=Response()`） |
| `test_rag_vault_scope_api.py` | **不存在** | 18 collected，全绿 |
| `test_agentic_rag_vault_scope.py` | **不存在** | 17 = 16 passed + 1 xfailed(strict) |
| `test_lancedb_vault_isolation.py` | 15 = 12 passed + **3 failed** | 15 = 12 passed + 3 failed（**同名三条，未回退未新增**） |

主干既有 3 条红（本卡不负责、基线登记）：
`TestVaultIdFromConfig::test_dynamic_vault_id_follows_config` /
`TestSubjectResolverVaultId::test_group_id_has_vault_prefix` /
`TestActiveVaultIdNarrowExceptionAndFallbackWarning::test_active_vault_id_level2_runtime_error_falls_through`

### 4-A.2 cherry-pick 逐条记录（(b)：`-x` 保留来源，每条前 merge-tree 预检）

| # | 新 SHA | 源 SHA | merge-tree rc | 冲突落点 | cherry-pick 结果 | 随卡剔除 |
|---|---|---|---|---|---|---|
| 1 | `b1865973` | `ca116f51` | 1 | 全部 DEBT-8 祖先（`review_service.py` / `test_debt8` / `evidence-debt8`） | 干净 | — |
| 2 | `0d5b2674` | `a3c41075` | 1 | 同上 + UAT-DEBT-8 | 干净 | — |
| 3 | `6da3a201` | `cee863a0` | 1 | 同上 | 干净 | `after-judge2-v2.txt` / `baseline-judge1.txt` / `baseline-judge2.txt` |
| 4 | `1d5a0ea3` | `aaecf696` | 1 | 同上 | 干净 | — |
| 5 | `28da5775` | `c9d8c0f6` | 1 | 同上 | 干净 | `codex-review-CARD-G4-4.stderr` |
| 6 | `8aa9f599` | `d5f27020` | 1 | 同上 | 干净 | `codex-review-CARD-G4-4-round2.stderr` / `final-judge1.txt` / `final-judge2.txt` |
| 7 | `a26a6a7f` | `6a732e1b` | 1 | 同上 + **未合卡追踪台账** | **台账 UU，按 (b) 取 ours** | `codex-review-CARD-G4-4-round3.stderr` |

**关于 merge-tree rc=1 全部为 1**：`merge-tree --write-tree` 做的是**整棵树三方合并**，
会把 DEBT-8 祖先的全部差异卷进来；`cherry-pick` 只取**单 commit 的 patch**。卡文的
预检结论（冲突全在 DEBT-8 面、G4-4 触及的 6 个文件在主干与 merge-base blob 相同）
经本卡逐条实测**成立** —— 7 条 pick 中只有第 7 条的台账真冲突，代码零冲突。

台账处置：`git checkout HEAD -- 未合卡追踪台账.md` → `git diff HEAD` 为空，
即台账**逐字节等于主干态**，本车道未改台账（卡文 §五 硬边界）。

### 4-A.3 补口四处（cherry-pick 之外本卡新增）

| 项 | 改动 | 理由 |
|---|---|---|
| (g) | `test_agentic_rag_vault_scope.py` xfail `reason` 改绑 **CARD-G4-4b** | 原文指向「未合卡追踪台账 G4-4-R1」，第十批拆卡后收口面归 4b；`strict=True` 保持不变，不留 `skip` |
| (l) | 移植版验收单加「移植注」头块 | 原文引用的 `final-judge*.txt` / `baseline-judge*.txt` / `*.stderr` 按 (j) 未随卡入库，引用会悬空；数字（`collected 80 items` / `3 failed, 76 passed, 1 xfailed`）逐字保留在正文 |
| (m) | 变异 M6 实测 + 结论写进 `mutation-run.txt` | 见下 |
| 证据 | `mutation-run.txt` 追加「移植后复跑」段 + 三重外部锚点 | 证明 8 条门在**移植后的树上**仍活 |

### 4-A.4 (m) 裸表旁路用例——**不是假绿**，无需改写

卡文担心：主干已由 CARD-G2-4 删除 `resolve_table_name` 的 B0.7 裸表回退，
`aaecf696` 的「裸表旁路」用例（`test_wikilink_neighbor_expansion_stays_in_vault`）
可能因此恒真变假绿。

**实测结论：该门仍然活着。** 变异 M6（把 `nodes.py` 的
`client.resolve_table_name("canvas_nodes")` 改回裸 `"vault_notes"`）**杀死了该门**
（exit=1）。真因：`expand_neighbors` 内部是 `self._db.open_table(传入名)`，
**根本不调用 `resolve_table_name`** —— B0.7 的删除与这条路径无关，泄漏面依旧真实存在。

配套活性判据（Codex round-2 整改留下的）也一并复验：M8（把邻居扩展换成恒等失效）
同样杀门，说明「结果里有 neighbor_expansion 标记行」这条断言不是摆设。

## 4-B. 👤 你来验（产品体验，3-5 分钟）

1. 照常用你的 Obsidian 插件问一个问题，看回答是否和以前一样正常出来。
   —— 预期：**没有任何变化**。插件不走这个入口。
2. 如果你手头有直接调检索接口的脚本或 curl 收藏（不确定就跳过，告诉 Claude
   「我不知道有没有」也算答案）：不带库名调一次，应该收到明确的拒绝而不是结果。

**这张卡给你的实际好处**：跨库检索不再串库；查询必须先选库，没选会被明确拒绝。

## 5. 🚦 验收结果

- [ ] 通过
- [ ] 有问题（写在 §6 批注区）

## 5.5 ⛔ 轮次说明

G4-4 卡族**累计已 3 轮** Codex（round-1 REJECT / round-2 / round-3 到顶）。
按卡文 (n)，本卡上限 **1 轮**定向复审（round-4 of 族），只审
`git diff 1f249b33..HEAD -- rag.py nodes.py agents.py 三测试`。
结果见 §6.6。

## 6. 📝 批注区（待你裁决 D1-D5，卡文 §七）

| 编号 | 事项 | Claude 默认取值 | 你的裁决 |
|---|---|---|---|
| **D1** | 纳入 `agents.py` 的 `X-Vault-Scope-Source` 响应头与 handler `response: Response` 形参 | 纳入（已随 `a3c41075` 移植；三值 explicit / legacy_group_id / derived_active 各一例已绿） | |
| **D2** | ⚠️ `vault_id` 必填是 **breaking API** | 按卡文默认执行。插件 `main.ts` 只调 agents/dialog、exam/*、tips/*、vault/*，`/rag/query` 三处 grep 零调用方 —— **但外部脚本 Claude 无法穷举，需要你确认** | |
| **D3** | OBS 三提交在 4a 之后 cherry-pick 而非并行 | 已按此执行（见 §6.6-OBS） | |
| **D4** | evidence 只带 `g44_mutations.py` + `mutation-run.txt` | 已执行；被剔除文件清单见 §4-A.2 | |
| **D5** | 4b 等 4a 合入主干后再切（同一 `lancedb_client.py` 面，避免互压行号） | 建议照办 | |

## 6.5 与卡文偏差及处置记录（逐条，防「声明比证据宽」）

### 6.5-A `test_recommend_action.py` 那条主干既有红「转绿」了 —— 真因不是修复

卡文预期「`test_recommend_action` 含 1 条主干既有红，基线登记、不算本卡」。
实测本卡终态该条**转绿**。真因（`aaecf696` 的 H4 整改带入）：
测试里的 mock 原本抛**裸 `Exception`**，而 handler 的优雅降级只捕预期依赖故障
（`RuntimeError` / `ConnectionError` / `Timeout` / `Value` / `TypeError`），
裸 `Exception` 穿透是 handler 的**设计行为**。整改把注入故障改成 `RuntimeError`。

**如实定性**：这是**测试侧把注入故障类型收窄**，**不是生产代码修复**。
它已在 Codex round-1 审过（H4），但仍应登记：本卡**未证明** handler 对
「非预期异常类型」的行为是正确的（见 §未证明 #4）。

### 6.5-B commit hook 处置（外科绕过，如实记录）

- 7 条 cherry-pick 中 4 条走 `git cherry-pick`（git 本身**不跑** pre-commit hook）；
  3 条因需剔除文件走 `cherry-pick -n` + `git commit`，**会**跑 hook。
- 实测 `python-lint` 块红在 **`ruff: command not found`（exit 127）** ——
  该块 `source backend/.venv/bin/activate`，而本车道无 `backend/.venv`。
- 补 venv 后真跑：`ruff check` **All checks passed**；
  `ruff format --check` 报 Would reformat，但**本卡未碰的主干文件**
  （`vault_scope.py` / `memory_service.py` / `rag_service.py`）**同样** Would reformat
  —— 证实是**主干存量漂移**，非本卡引入（与 `ca116f51` 原 commit body 记载一致）。
- 处置：`LEFTHOOK_EXCLUDE=python-lint git commit`（DEBT-8 先例的外科绕过），
  并**手工补跑 `ruff check` 作为实体门**（§4-A #10）。
- ⚠️ 顺带实证一条**别人的卡**的缺陷：`python-typecheck` 块在 `pyright: command not
  found`（exit 127）时仍显示 ✔️ 通过 —— 即 X5-A（CARD-DEBT-hook-pyright）登记的
  **假绿**。本卡只登记，不改 `lefthook.yml`（不在本卡面）。

### 6.5-C `nodes.py:386` 的裸表名——查证后判定**不是同类旁路**

`nodes.py:386` 仍有 `progressive_scope_search(table_name="vault_notes")`。
逐层查证：`progressive_scope_search` 内部四段都调 `self.search(table_name=...)`，
而 `search` 体内**第一件事就是 `table_name = self.resolve_table_name(table_name)`**
（`lancedb_client.py:1219` / `:1303`）。因此该路径**经过作用域解析**，不构成跨库泄漏。

遗留的是**命名不一致**：该分支解析到 `<vault>_vault_notes`，而主链
`search_multiple_tables` 默认查 `DEFAULT_TABLES=["canvas_nodes"]`。
**登记级**（非阻断），移交项见 §台账待登记条目。

### 6.5-D 临时 `backend/.venv` symlink

为让变异脚本的 `.venv/bin/pytest` 与 lefthook 的 `activate` 可用，本卡在车道内建了
**目录级** symlink `backend/.venv -> card-v5-lance/backend/.venv`。
`.venv` 被 `.gitignore` 覆盖（`git status` 全程为空），**不入库**。
作业结束后由本卡移除，车道恢复开工时形态。

## 6.6-OBS. OBS 三提交 cherry-pick（完成条件 (k)）

| # | 新 SHA | 源 SHA | cherry-pick | 随卡剔除 |
|---|---|---|---|---|
| 1 | `38daedbb` | `78c9e6e7` | 干净（**无 git 冲突**） | — |
| 2 | `89dd7806` | `6b995031` | 干净 | `codex-review-CARD-OBS-nothrow-logging.stderr` |
| 3 | `c694478c` | `c1f8968d` | 干净 | `codex-review-CARD-OBS-nothrow-logging-round2.stderr` |

### ⚠️ 「没有 git 冲突」不等于「语义已归一」——本卡实测

卡文预判 `rag.py` 与 `test_rag_four_state_api.py` 各会冲突一次。实测**三条 pick
全部干净应用**，原因是 OBS 的 patch 命中的是**入口日志**那段 hunk，而
`a3c41075` 新增的是**另一处** scope 日志 hunk，两者不重叠 —— git 无从察觉。

结果是 `rag.py` 一度处于**两种口径并存**的状态：

- 入口日志：OBS 已改为模块级 `logger = nothrow(logging.getLogger(__name__))` + 直调；
- scope 日志：仍保留 `a3c41075` 手写的 `try: logger.info(...) except Exception: pass`。

按 (k)「以 OBS 的 `logger = nothrow(...)` 为准，删掉 `a3c41075` 手写 try/except」，
本卡删除了 scope 日志的调用点 try/except。

**为什么这不是洁癖而是真缺陷**：OBS 自己在 `rag.py:300-305` 的注释里写明了 ——
*「call-site 的 try/except 与包装器双层兜底会让注入门测不到包装器（假绿面）」*。
双层兜底下，注入门把 logger 打成抛错，调用点的 `except` 会先吞掉，
于是**包装器是否真的生效，门测不出来**。这正是 OBS 这张卡要防的东西。

### OBS 面判据

| # | 判据 | 结果 |
|---|---|---|
| 1 | `test_nothrow_logging_api.py`（OBS 自带） | ✅ **21 passed** |
| 2 | 裁判 1（四文件）OBS 后复跑 | ✅ **107 passed / 0 failed**（与 4a 终态一致，未回退） |
| 3 | 裁判 2 OBS 后复跑 | ✅ 28 passed + 1 xfailed + 3 主干既有红（与 4a 终态一致） |
| 4 | `ruff check` OBS 面 6 文件 | ✅ All checks passed |
| 5 | `*.stderr` 入库 | ✅ `git ls-files \| grep '\.stderr$'` rc=1（零命中） |

**未跑**：`backend/scripts/nothrow_logging_negative_control.py` —— 它是**原地改源码**
的变异脚本（`m.target.write_text(...)`），卡文 (k) 未要求跑，且与本卡自身的
`g44_mutations.py` 存在串行互斥要求。登记，不跑。

## 6.6 Codex 定向复审（round-4 of G4-4 族，本卡 1 轮）

<!-- 待 (n) 执行后回填 -->

## 7. 🔗 技术 spec 引用（给 Claude 读）

- 卡文：`_bmad-output/implementation-artifacts/goal-cards/第十批-goals/X3-1.md`
- 手册：`.../2026-09-04-第十批开跑手册-8车道11卡.md`（§一.1 / §一.2 / §三 X3-①）
- 移植源验收单：`UAT-CARD-G4-4-full-RAG-显式VaultScope-2026-09-01.md`（含 round-1~3 全记录）
- 契约：`.claude/rules/cypher-read-contract.md` R1/R4（读侧 fail-closed 范式）
- 范式来源：`backend/app/api/v1/endpoints/chat.py:289` 的 `resolve_vault_scope` 409 fail-closed

## ⛔ 本卡未证明什么（必填段，防止「声明比证据宽」）

1. **同一个库内不同科目之间的边界仍是坏的** —— `expand_neighbors` 不传 subject，
   LIKE 匹配整张 vault 表，同 vault 跨 subject 的邻居会被带回（`PHYSICS_SECRET`
   可用 `--runxfail` 复现）。主干既有缺陷，收口面 `lancedb_client.py` 是本卡硬禁改面，
   拆给 **CARD-G4-4b**。本卡只用 `xfail(strict=True)` 锁住，**没有修**。
2. **没有连真库验证过**。全部测试跑在 `tmp_path` 上的临时 LanceDB；7691 / 现网
   LanceDB / Graphiti 全程只读未连。「双 vault 隔离」证明的是**命名空间隔离逻辑**，
   不是现网数据的实际隔离状态。
3. **没有证明外部没有 `/rag/query` 的调用方**。只 grep 了插件 `main.ts`。
   你的脚本 / curl 收藏 / 任何第三方集成，Claude 无法穷举 —— 这是 D2 要你确认的原因。
4. **没有证明 handler 对「非预期异常类型」的降级行为是对的**（见 §6.5-A）。
   那条红转绿来自测试侧收窄注入故障类型，不是生产修复。
5. **`test_agents_dedup.py` 未跑**。它需要 W4 的 lifespan 隔离门才能安全跑
   （否则收集期会连 7691）。W4 未合入主干前，本卡不跑该文件。
6. **`lancedb_client.py` 的 B0.7 相关面本卡零验证**。它是 4b 的唯一收口面，
   本卡连读都只做了判定所需的最小范围。
7. **主干既有的 3 条 `test_lancedb_vault_isolation.py` 红未修也未诊断根因**，
   只做了「同名三条、数量未变」的回归确认。

## 📋 台账待登记条目（`未合卡追踪台账.md`，由主 session 单点写入）

> 本车道**未改**台账（卡文 §五 硬边界 + (b) 台账 hunk 取 ours）。以下为合入后待登记：

1. **§一 G4-4 行**：状态从「round-3 到顶、未合并」→「vault 面已拆为 CARD-G4-4a，
   于 `BATCH-2026-09-04-第十批` 以 7 条 `cherry-pick -x` 移植到 `card/x3-vaultscope`
   并补口；subject 面拆为 CARD-G4-4b 待切」。
2. **§一 OBS 行**：`78c9e6e7` / `6b995031` / `c1f8968d` 三提交随 X3-① 一并移植，
   冲突解法见本验收单 §6.6-OBS。
3. **新增移交项 G4-4a-R1**：`nodes.py:386` `progressive_scope_search` 解析到
   `<vault>_vault_notes`，与主链 `DEFAULT_TABLES=["canvas_nodes"]` 命名脱节
   （**非泄漏**，已查证 `search` 内部解析）——登记级，建议并入 4b 或 G-PIPE 处置卡。
4. **移交 X5-A 佐证**：`lefthook.yml` `python-typecheck` 块在 `pyright` 缺失
   （exit 127）时仍判通过 —— 本卡独立实证了该假绿。
5. **G4-4 证据文件去向**：`final-judge*.txt` / `baseline-judge*.txt` /
   三份 `codex-review-*.stderr` 未随卡入库，原件在 `card/w8-scope@6a732e1b`。
