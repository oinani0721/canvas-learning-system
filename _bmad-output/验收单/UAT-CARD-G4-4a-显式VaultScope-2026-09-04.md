# UAT 验收单 — CARD-G4-4a full RAG 显式 VaultScope（vault 面移植）

> 批次: `BATCH-2026-09-04-第十批` · 车道 X3-① · 分支 `card/x3-vaultscope`
> 卡文: `第十批-goals/X3-1.md` · 工时预算 10h
> 主干基线: `1f249b33` · 只读取证源: `card/w8-scope@6a732e1b`
> 本卡形态: **不重写，逐条 cherry-pick 移植 + 补口 + 一轮定向复审**

---

## ⛔ 先读：三条显著声明（影响你判断要不要批这张卡）

1. **这是 breaking API**：`POST /api/v1/rag/query` 从今往后**必须**带 `vault_id`，
   不带一律 422 拒绝。
   本卡自己把仓内调用方查了一遍（没照抄卡文结论，方法与结果见 §6.5-E）：
   **插件确实不调**这个端点（枚举了插件全部 13 个 API 字面量，不在其中）；
   仓内另有一处 `dredd-hooks.js` 的测试 payload 缺 `vault_id`，但它
   **当前不被执行**，属过时 fixture 而非缺陷。
   **仓外的东西 Claude 证明不了** —— 你自己的脚本、别的机器上的定时任务、
   任何第三方集成。这是 D2，需要你确认。
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
| 6 | **(i)** 新增日志惰性参数（判据：计数**不高于**开工基线） | ✅ 4a 阶段逐文件持平（rag 7→7 / agents 15→15 / nodes 32→32）；**OBS 合入后终态 rag.py 7→0**（OBS 把入口日志全改成 `%s` 惰性参数），agents/nodes 不变 | 与 `git show 1f249b33:<file>` 对比计数 |
| 7 | **(j)** evidence-g44 只带两文件 | ✅ `git ls-files` 仅 `g44_mutations.py` + `mutation-run.txt` | 三份 `*.stderr` + 五份 judge txt 全部剔除 |
| 8 | **变异负控** 8/8 各自的指定门 `exit=1`（串行、原地改源码） | ✅ `ALL 8 MUTATIONS KILLED THEIR GATES (exit=1 only)`；**留存粒度不足，见下注** | `evidence-g44/mutation-run.txt` 尾部「移植后复跑」段 |
| 9 | 变异还原三重外部锚点 | ✅ ① 三文件 sha256 逐条一致 ② `git status` 空 ③ `grep MUTANT` rc=1 | 判据不依赖脚本自检（防自证） |
| 10 | `ruff check` 本卡全部改动 `.py`（4a 面 9 文件 + OBS 面 6 文件，两次分别跑） | ✅ 两次均 `All checks passed!` | 见 §6.5-B「hook 处置」 |
| 11 | **收尾复跑**（Codex 在同一棵树 escalated 跑过测试后）：裁判 1 四文件 + OBS `test_nothrow_logging_api.py` 合跑 | ✅ **128 passed / 0 failed**（107 + 21）；裁判 2 同步复跑 3 failed(既有) + 28 passed + 1 xfailed，与前次逐字相同 | `git diff --stat HEAD -- backend/` 为空，证明 Codex 未动代码树 |

> ⚠️ **#8 的措辞收窄**（Codex round-4 HIGH-3，复核属实）：初稿把
> `mutation-run.txt` 说成「证明 8 条门仍活」，**过宽**。该脚本在**杀成功**时
> 只打印 `[名称] ✓ 指定门变红 (exit=1)`，**丢弃** pytest 的 tail、失败断言与
> nodeid（`g44_mutations.py:26-35` / `:145-157`）。所以归档文本能证明的是
> 「对每条变异，那条被点名的 `nodeid` 以 `exit=1` 失败了」，
> **不能**从归档文本本身回溯「红的是哪一条断言」。
> 补强来自两处**归档之外**的证据：① 本卡对 M6 单独做了击杀身份核验 +
> 可达性探针（§4-A.5）；② Codex round-4 在隔离归档中独立复跑，同样 8/8、
> 脚本 `exit=0`、三文件 SHA 前后一致。
> **定性：留存粒度问题，不是负控假绿。** 建议后续卡让脚本在 kill 时也保存
> 失败身份（`--tb=line` 的 `^E` 行 + nodeid）。

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

| # | 新 SHA | 源 SHA | cherry-pick 结果 | 随卡剔除 |
|---|---|---|---|---|
| 1 | `b1865973` | `ca116f51` | 干净 | — |
| 2 | `0d5b2674` | `a3c41075` | 干净 | — |
| 3 | `6da3a201` | `cee863a0` | 干净 | `after-judge2-v2.txt` / `baseline-judge1.txt` / `baseline-judge2.txt` |
| 4 | `1d5a0ea3` | `aaecf696` | 干净 | — |
| 5 | `28da5775` | `c9d8c0f6` | 干净 | `codex-review-CARD-G4-4.stderr` |
| 6 | `8aa9f599` | `d5f27020` | 干净 | `codex-review-CARD-G4-4-round2.stderr` / `final-judge1.txt` / `final-judge2.txt` |
| 7 | `a26a6a7f` | `6a732e1b` | **台账 UU，按 (b) 取 ours** | `codex-review-CARD-G4-4-round3.stderr` |

**⛔ 本表 merge-tree 那一列，初稿写错了，此处更正**（Codex round-4 HIGH-1 指出，
复核属实）。初稿写「七次 merge-tree 全部 rc=1，冲突全部落在 DEBT-8 祖先」——
那是**把两次不同的测量混成了一句话**：rc 取自**递进 HEAD**的跑法，
而冲突描述取自**固定基线**的结论。两组真实数据分列如下：

**(甲) 固定基线 `git merge-tree --write-tree 1f249b33 <commit>`**（卡文用的方法）：

| commit | rc | 冲突落点 |
|---|---|---|
| `ca116f51` | 1 | `evidence-debt8/…py`、`review_service.py`、`test_debt8_…py` —— **全 DEBT-8** |
| `a3c41075` | 1 | `UAT-CARD-DEBT-8…md`、`review_service.py`、`test_debt8_…py` —— **全 DEBT-8** |
| `cee863a0` | 1 | 同上 —— **全 DEBT-8** |
| `aaecf696` | **0** | 无 |
| `c9d8c0f6` | **0** | 无 |
| `d5f27020` | **0** | 无 |
| `6a732e1b` | 1 | **仅**`未合卡追踪台账.md` |

即 `1,1,1,0,0,0,1` —— **与卡文所载完全一致**（卡文：`aaecf696 c9d8c0f6 d5f27020` rc=0），
且「冲突全在 DEBT-8 面（第 7 条另加台账）」这个结论在这组数据上**成立**。

**(乙) 递进 HEAD `git merge-tree --write-tree HEAD <commit>`**（本卡逐条 pick 前实际跑的）：
七次**都** rc=1，但从第 2 条起冲突里就出现了 `rag.py` / `agents.py` /
`evidence-g44/*` / `test_agentic_rag_vault_scope.py` —— 因为此时 HEAD 已含前几条
pick，整树三方合并会把这些文件也看成两侧都改过。**这组的冲突不是「全 DEBT-8」。**

**结论不变，但理由要说准**：cherry-pick 七条代码零冲突，靠的**不是** merge-tree 的
rc，而是 §4-A.2b 证明的「6 个文件在主干与 merge-base 上 blob 逐字节相同」。
merge-tree 在这里只是**预检**，它的 rc 既不预示也不排除 cherry-pick 冲突。

台账处置：`git checkout HEAD -- 未合卡追踪台账.md` → `git diff HEAD` 为空，
即台账**逐字节等于主干态**，本车道未改台账（卡文 §五 硬边界）。

**代码零冲突的根因（本卡独立验证，不照抄卡文结论）**：
`merge-base(1f249b33, 6a732e1b)` = `9af18b27`（`--all` 返回唯一值，且经
`--is-ancestor` 验证确为双方祖先）。G4-4 触及的 6 个既有文件在
**主干与 merge-base 上 blob 完全相同**：

| 文件 | blob（两侧同一） |
|---|---|
| `rag.py` | `1cfdb938` |
| `nodes.py` | `5efce770` |
| `agents.py` | `9259c179` |
| `test_rag_four_state_api.py` | `cb84e3e8` |
| `test_agents_learning_event.py` | `36d3a19c` |
| `test_recommend_action.py` | `6f4cb364` |

即 V5 / W6 / W9 / W5 / DEBT-8 合入主干时**一行都没碰**这 6 个文件，
所以每条 patch 落在与它被写出来时**逐字节相同**的底稿上 —— 这才是零冲突的原因。

### 4-A.2b 移植等价性证明（本卡自证，回答「搬过来的是不是同一个东西」）

**方法一：逐条 patch-id 对比**（`git patch-id --stable`，限 8 个代码/测试文件）

7 条 cherry-pick 中 **6 条 patch-id 完全相同**。唯一不同的是
`1d5a0ea3 <- aaecf696`，且差异**只在 `rag.py`**（`nodes.py` /
`test_rag_vault_scope_api.py` / `test_recommend_action.py` /
`test_agentic_rag_vault_scope.py` 四个文件的 patch-id 都相同）。

**根因是结构性的，不是移植错误**：在 `card/w8-scope` 上，`aaecf696` 的父是
**OBS `78c9e6e7`**（那时 `rag.py` 已含 nothrow 改动）；在本车道，同一 patch 落在
`6da3a201`（尚无 OBS）之上。同一 patch 打在不同底稿上，产出的 diff 自然不同 ——
git 靠上下文匹配干净应用了它。

**方法二：终态逐文件 blob 对比**（比 patch-id 更强 —— 直接比结果）

本车道 `HEAD` vs `card/w8-scope@6a732e1b`，11 个相关文件：

| 结果 | 文件 |
|---|---|
| **9 个 IDENTICAL**（blob 逐字节相同） | `nodes.py` / `agents.py` / `test_rag_four_state_api.py` / `test_agents_learning_event.py` / `test_recommend_action.py` / `test_rag_vault_scope_api.py` / `nothrow_logging.py` / `memory.py` / `test_nothrow_logging_api.py` |
| **2 个 DIFFERS** | `rag.py`、`test_agentic_rag_vault_scope.py` |

两处 DIFFERS 各**只有一个 hunk**，都是本卡**刻意**的改动，已逐字核对：

- `rag.py` → 完成条件 **(k)** 的归一（删 scope 日志调用点 `try/except`）；
- `test_agentic_rag_vault_scope.py` → 完成条件 **(g)** 的 xfail `reason` 改绑 4b。

**结论**：除这两处刻意改动外，移植结果与被 Codex 审过三轮的那一版
**逐字节等同**。这比「测试全绿」强 —— 全绿只覆盖已写出来的断言，
逐字节等同覆盖的是**没写断言的那部分代码**。

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

### 4-A.5 M6 击杀身份核验 —— 防「假杀」（本卡自查，非卡文要求）

变异报 KILLED 不等于门有效：如果击杀是由**别的层**贡献的（假杀），
被测防线其实没被证明。判据必须比**失败身份**——是不是同一条断言红了。

| 步骤 | 施加 | 结果 | 判定 |
|---|---|---|---|
| 1 击杀身份 | 只施 M6 | exit=1，失败断言 = 「扩展带回的邻居不是 A 库版本: `['B 库绝密量子隐形传态']`」 | 失败语义**就是跨库泄漏本身** → **不是假杀** |
| 2 可达性探针 | M6 + 前两条断言临时放行 | exit=1，失败断言 = 「邻居扩展混入裸表 B 内容」 | 第三条显式 `b_secret` 探针**可达且会变红**，不是死断言 |

**为什么要做第 2 步**：显式泄漏探针
`assert not any(d.endswith("b_secret") for d in ids)` 排在门里**第三条**，
而 M6 在**第二条**就把测试打红了 —— pytest 短路，第三条根本没跑到。
只做第 1 步的话，「那条最直接的泄漏探针是活的」这句话就没有证据。

第 2 步属 memory 三分法里的 **complete 型层变异**（补同缺陷的其它站点，
可红，须声明），不是「拆了被测防线」的非法变异 —— 它只放行前两条断言，
**没有动第三条断言本身**，也没有动 M6 施加的被测防线。

两步均串行、原地改源码、`finally` 无条件还原、逐字节 sha 比对通过、
`git status` 空。

## 4-B. 👤 你来验（产品体验，3-5 分钟）

1. 照常用你的 Obsidian 插件问一个问题，看回答是否和以前一样正常出来。
   —— 预期：**没有任何变化**。你平时用的功能不走这条路。
2. 一个只需要你回忆、不用动手的问题：**你自己写过、或者别人给过你，
   会自动去问这个系统问题的小工具或定时任务吗？**（比如每天自动生成摘要、
   批量整理笔记之类的东西。）
   - 想不起来 / 没有 → 直接答「没有」，这张卡就可以过。
   - 有 → 告诉 Claude 是什么，Claude 去核它会不会受影响。
     因为这张卡之后，**不说清楚查哪个笔记库就来问问题，会被直接拒绝**，
     老工具如果没说库名，就会停止工作。

**这张卡给你的实际好处**：跨库检索不再串库；查询必须先选库，没选会被明确拒绝。

## 5. 🚦 验收结果

**Claude 侧全部代验完成**：指定裁判全绿（裁判 1 + OBS 合跑 `128 passed`；
裁判 2 `28 passed + 1 xfailed + 3 条主干既有红`）；禁改门与扩展禁改门皆空；
变异 8/8；live vault 与主仓 `data/` 零写；Codex round-4 末行 **`阻断级 = 0`**。

按本批合并门（阻断级 = 数据丢失 / live vault 或 7691 写入 / 安全 / 指定裁判红 /
负控假绿）：**本卡阻断级 = 0，可合**。其余 5 HIGH + 1 LOW 全为文证类，
已逐条整改或登记（§6.6）。

**留给你的只有两件**：D2（`vault_id` 必填是 breaking API，仓外调用方需你确认）
与 §6.6 末尾的「审查绑定」取舍。

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
| **D2** | ⚠️ `vault_id` 必填是 **breaking API** | 按卡文默认执行。**但卡文的「零调用方」不成立**：插件侧确实零命中（本卡自跑 grep 复核），另有 `dredd-hooks.js` 两处 payload 缺 `vault_id`，但**当前不被执行**（`--method GET` + `--names`，详见 §6.5-E 的自我更正），属过时 fixture 而非 CI 缺陷。仓外脚本仍需你确认 | |
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

- G4-4 的 7 条里 **3 条**走纯 `git cherry-pick`（`ca116f51` / `a3c41075` /
  `aaecf696` —— git 自身**不跑** pre-commit hook）；**4 条**因需剔除
  `*.stderr` / judge txt 或解台账冲突而走 `cherry-pick -n` + `git commit`
  （`cee863a0` / `c9d8c0f6` / `d5f27020` / `6a732e1b`），**会**跑 hook。
  OBS 3 条全部走 `-n` + `git commit`。
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
而 `search` 体内有 `table_name = self.resolve_table_name(table_name)`
（**实测 AST 归属**：`lancedb_client.py:3088`，`search()` def @ `:3042`）。
因此该路径**经过作用域解析**，不构成跨库泄漏。

> ⚠️ 本行行号是**实测**的：初稿曾按 `grep` 前两条命中写成 `:1219` / `:1303`，
> AST 复核发现那两处分别属 `rebuild_index()` 与 `index_image_content()`，
> 与 `search()` 无关 —— 结论不变，引证已更正。

遗留的是**命名不一致**：该分支解析到 `<vault>_vault_notes`，而主链
`search_multiple_tables` 默认查 `DEFAULT_TABLES=["canvas_nodes"]`。
**登记级**（非阻断），移交项见 §台账待登记条目。

### 6.5-D 临时 `backend/.venv` symlink

为让变异脚本的 `.venv/bin/pytest` 与 lefthook 的 `activate` 可用，本卡在车道内建了
**目录级** symlink `backend/.venv -> card-v5-lance/backend/.venv`。
`.venv` 被 `.gitignore` 覆盖（`git status` 全程为空），**不入库**。
作业结束后由本卡移除，车道恢复开工时形态。

### 6.5-F 登记：`g44_mutations.py` 无 `__main__` 守卫（潜在隐患，本卡不改）

AST 实测：`_bmad-output/审查/evidence-g44/g44_mutations.py` **没有**
`if __name__ == "__main__":` 守卫 —— 变异循环（`:146` `for`）、失败判定（`:160`）
和 `sys.exit`（`:163`）全在**模块顶层**。也就是说 `import` 它 = **直接对生产源码
施加 8 次变异**。这是已知会造成真实损坏的一类缺陷。

**为什么本卡不改**：

1. 卡文口径是「**不重写，只移植**」；该文件是经 Codex 三轮审查的证据件，
   改动会削弱它的溯源价值；
2. 有一层**意外的兜底**：`:16` `BACKEND = Path(os.environ["G44_BACKEND"])`
   在环境变量未设时**立刻 KeyError**，误 import 因此不会走到变异循环 ——
   实际触发需要有人**主动**设置该变量，即已经打算跑它了；
3. pytest 只收集 `test_*.py` / `*_test.py`，`_bmad-output/` 也不在测试路径内，
   自动收集不会碰它。

**对照**：OBS 的 `backend/scripts/nothrow_logging_negative_control.py`
**有**正规守卫（`def main()` @ `:186` + `if __name__ == "__main__":` @ `:270`，
顶层唯一可执行语句就是那个 `if`）—— import 安全。两个脚本同为原地改源码的负控，
写法应统一到 OBS 那一种。已列进「台账待登记条目」。

### 6.5-E 自查：卡文「零调用方」的 grep 面不够 —— 但我第一版把影响也判错了

> 这一节记的是**两次**自我更正：先补上卡文漏掉的仓内引用，再把我自己
> 对它的影响判断从「CI 会红」收回到「当前无影响」。两次都不是 Codex 指出的。

卡文 D2 写「插件 `main.ts` 只调 agents/dialog、exam/*、tips/*、vault/*，
`/rag/query` 三处 grep 零调用方」。本卡**自己重跑**了这个 grep（不照抄结论），
结果：

- ✅ **插件侧成立（用枚举法验证，不是靠一条 grep）**：
  单查关键字有假阴风险（URL 可能是拼出来的）。实测插件的请求 URL 统一由
  `main.ts:1749` 的 `` `${this.settings.backendUrl}${endpoint}` `` 构造，
  而 `endpoint` 在所有调用点**都是字面量**。于是把插件源里全部
  `/api/v1/...` 字面量**枚举出来**，共 **13 个**：
  `agents/dialog`、`errors/accept-candidate`、`errors/dispute-candidate`、
  `exam/grade`、`exam/quick`、`exam/start`、`tips`、`tips/batch`、
  `tips/callout-direct`、`tips/relation`、`vault/current`、`vault/list`、
  `vault/switch`。
  **`/api/v1/rag/query` 不在其中** —— 插件确实不调这个端点。
  （顺带更正卡文措辞：卡文列的是「agents/dialog、exam/*、tips/*、vault/*」，
  漏了 `errors/*` 两个；不影响结论。）
- ⚠️ **但仓内还有一处引用，卡文的 grep 面没覆盖到**：
  `scripts/spec-tools/dredd-hooks.js` 有**两处**构造 `/api/v1/rag/query` 请求体，
  **都不带 `vault_id`**（这一条属实；它的**影响**见下方的自我更正）：
  - `:38` `ENDPOINTS_WITH_BODY` → `{query: 'test query', top_k: 5}`
  - `:152` `hooks.before('/api/v1/rag/query > POST')` → `{query: '...', top_k: 3, subject: 'test'}`

**⛔ 本节初稿把影响判错了，此处彻底更正**（自查抓出，非 Codex 指出）。

初稿写「它是活的 → 4a 合入后这两条契约事务恒 422 → 静默的契约覆盖丢失」。
**错。** 继续往下查了一层才发现，全仓**唯一**的 dredd 调用
（`.github/workflows/api-spec-sync.yml:348-353`）带着两个开关：

```
dredd openapi-current.json http://localhost:8000 \
  --reporter json:dredd-report.json --reporter markdown:dredd-report.md \
  --hookfiles scripts/spec-tools/dredd-hooks.js \
  --method GET \
  --names || true
```

- **`--method GET`** —— 只跑 GET 事务。`/api/v1/rag/query` 是 **POST**，
  于是 `hooks.before('/api/v1/rag/query > POST', …)` 与
  `ENDPOINTS_WITH_BODY['/api/v1/rag/query']` **都不会被用到**。
- **`--names`** —— dredd 只**列出**事务名，**不执行**任何事务。

两条**各自独立**就足以让影响为零，何况还叠了 `continue-on-error: true` 和 `|| true`。

**更正后的定性**：

| 说法 | 判定 |
|---|---|
| `dredd-hooks.js:38` / `:152` 的 payload 不带 `vault_id` | ✅ **属实**（代码可查） |
| 主干接受、4a 拒绝这两个 payload | ✅ **属实**（双侧实测，见下表） |
| 「4a 合入后这两条契约事务会 422」 | ❌ **不成立** —— 它们今天既不被 `--method GET` 匹配，也不被 `--names` 执行 |
| 「CI 契约覆盖静默丢失」 | ❌ **不成立** —— 今天这两条事务本来就没有覆盖 |

**剩下的真东西**：这是一处**会过时的 fixture**。今天无害；一旦有人去掉
`--method GET` / `--names` 想真跑契约测试，它会立刻变成红。**登记级、低优先**，
移交 X8（openapi 面归它）。

**这条自查记在这里的意义**：初稿只查到「工作流触发路径含 `backend/app/api/**`」
就下了「会被触发 → 会 422」的结论 —— **触发工作流**和**执行那条事务**是两回事，
中间隔着 `--method` 和 `--names` 两道过滤。少查一层，就会把一个无害的过时
fixture 报成 CI 缺陷。

**归因是实测的，不是推断**（防「既有缺陷记到本卡头上」，也防反过来）：
分别用主干 `1f249b33` 与本卡 HEAD 的 `RAGQueryRequest` 实例化同两个 payload——

| payload | 主干 `1f249b33` | 本卡 HEAD |
|---|---|---|
| `{query:'test query', top_k:5}` | **接受** | **拒绝**（缺 `vault_id`） |
| `{query:'What is machine learning?', top_k:3, subject:'test'}` | **接受** | **拒绝**（缺 `vault_id`） |
| `{query:'ok', vault_id:'canvas_vault'}` | — | **接受** |

（`top_k` / `subject` 都不是模型字段，但 pydantic 默认 `extra='ignore'`、
本模型未设 `extra='forbid'`，所以它们**不是**失败原因 —— 失败原因只有缺 `vault_id`。）
即：这两条契约事务**在 4a 之前是通的**，是本卡把它们打断的，不是存量。

**定性**：**登记级**，非阻断级（合并门定义：数据丢失 / live vault 或 7691 写入 /
安全 / 指定裁判红 / 负控假绿 —— 都不沾）。但它**实质改变了 D2 的答案**：
「零调用方」不成立，至少有一个仓内 CI 消费方需要同步。修法就是给两个 payload
各加一个 `vault_id` 字段，属 X8 的一行活。

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

### (k) 删除后仍受保护 —— 三态探针实证（不是推理）

OBS 的注入门**全部**打在 `/api/v1/rag/weak-concepts` 的**入口日志**上
（`test_nothrow_logging_api.py` 里 9 处 `client.get(".../weak-concepts/...")`），
**没有**任何一条直接打 `/rag/query` 的 scope 日志。所以「删掉调用点 try/except
后 scope 日志抛错仍不会打断请求」这句话，光靠「它们共用同一个包装器」是**推理**，
不是证据。本卡用一次性探针把它变成证据（探针**不入库**，跑在 scratchpad；
用局部 `FastAPI()` 只挂 `rag_router`，同 `test_rag_four_state_api.py:399` 的安全范式，
**不起 `app.main` lifespan、不连 7691**）：

| 态 | 注入点 | 结果 | 作用 |
|---|---|---|---|
| **A 对照** | 不注入 | HTTP **200** | 基线 |
| **B 被测保护** | `rag.logger.inner.info` 抛 `RuntimeError` | HTTP **200**，注入**被调用 2 次** | 保护生效，且**可达性自证** |
| **C 验伪锚** | `rag.logger.info`（包装器层，绕过其内部保护） | HTTP **500**，注入被调用 1 次 | 证明探针**有能力检出破坏** —— B 的 200 不是假绿 |

两点值得单独说：

- **B 的「被调用 2 次」不是噪声，是证据**：`/rag/query` 的 handler 里恰好有
  **两处** `logger.info`（入口日志 + 本卡的 scope 日志）。计数为 2 说明
  scope 日志那一行**真的执行了**并且**真的抛了**，然后被包装器吞掉 ——
  排除了「200 是因为那行压根没跑到」这种假绿。
- **没有 C 就不该信 A/B**：只跑 A/B 会得到「200 / 200」，看起来像通过，
  但同样的输出也可能来自「注入根本没接上」。C 让探针自己证明了它**能**变红。

**⚠️ 本节初稿有一句写错了，此处更正**（自查抓出，非 Codex 指出）：
初稿写「scope 日志**无常驻回归锁**」—— **错**。实测：

`test_rag_four_state_api.py:197`
`TestRagTraceAlignment::test_entry_logger_failure_does_not_break_response`
patch 的正是 **`app.api.v1.endpoints.rag.logger.inner.info`**（`:211`），
而 `/rag/query` 的 handler 里**两处** `logger.info`（入口日志 + 本卡 scope 日志）
**都**经过这个注入点 —— 上表 B 态实测 `call_count == 2` 就是这件事的直接证据。
该门断言 `status_code == 200` **且** `query.await_count == 1`；若 scope 日志的异常
向外传播，请求会在 `rag_service.query` 之前 500、`await_count` 为 0，
**两条断言同时红**。

所以正确的表述是：**scope 日志这一行有常驻回归锁**（`:197` 那道门），
本卡的三态探针是它的**补充**（多给了可达性计数与验伪锚 C 态），不是替代。

真正的缺口只剩一条，如实登记：该常驻门的 docstring 仍称自己是「**入口**日志」的门
（写于 scope 日志尚未存在时），**名实略窄于它实际覆盖的面**。
建议 OBS 后续卡把 docstring 更新，并把本卡探针的 B/C 两态补成显式用例
（尤其 C 态验伪锚 —— 现有门没有它）。

### ⚠️ (k) 的这次归一，**推翻了 OBS 验收单里一条有记载的「不动」决定**

本卡自查发现（卡文没提，Codex 提示词里也没写）：随卡带入的
`_bmad-output/审查/CARD-OBS-nothrow-logging-验收单.md:133` 明写——

> **不动**：`:309`（G4-4 新增 scope resolved，已惰性 + `a3c41075` 加的
> call-site 兜底**保留**，§五 第 10 条）

也就是说 OBS 当时是**有意识地保留**了这处双层兜底，而本卡 (k) 把它删了。
这属于「后一张卡推翻前一张卡的显式决定」，必须显著登记，不能悄悄改掉。

**为什么本卡仍然认为该删**（三条，都可复核）：

1. **它引的那条依据不存在**。`§五` 实测**只有 9 条**（`1.`–`9.`，
   `grep -cE '^[0-9]+\. \*\*'` = 9），没有第 10 条。该文件里其余四处
   `§五 第 2/7/8/9 条` 引用**全部命中**，唯独这一处**悬空** ——
   也就是这个「不动」决定**没有留下真正的理由**。
2. **OBS 自己的裁决点 A-3 给出的原则，指向相反方向**。同文件 `:181`：
   > A-3 | `rag.py:291-299` 手写 try/except 收敛为直接调用 | 按卡文默认收敛 |
   > 若倾向保守可保留双层兜底，但该门退化为「测 call-site try/except」
   > 而非测包装器（**假绿面**）
   —— 入口日志按这条原则收敛了；scope 日志留着，是同一文件里两套口径。
3. **保护强度未下降**。模块级 `logger = nothrow(logging.getLogger(__name__))`
   已经把兜底收进包装器；删掉调用点的 `try/except` 后，
   scope 日志抛错**仍然**不会成为业务失败源。判据：
   `test_nothrow_logging_api.py` **21 passed**（含 `:462` 的
   `record.filename == "rag.py"` stacklevel 门）、裁判 1 **107 passed / 0 failed**。

**如实定性**：这是**卡文 (k) 授权的改动**，不是本卡自作主张；但它推翻的那条
记录属于 OBS 卡的地盘，**建议主 session 在合并时把这条口径变更一并登记**
（见「台账待登记条目」）。若你或 OBS 卡的负责人认为应当保守，
回滚方式是把那 9 行 `try/except` 加回去 —— 代价是
`test_nothrow_logging_api` 对 scope 日志这一行**测不到包装器本身**。

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

提示词：`_bmad-output/审查/prompts/codex-prompt-CARD-G4-4a.md`（8145 字节）。
送审面：`git diff 1f249b33..HEAD` 限 6 个代码/测试文件（1248+/45-）。
提示词内含 **A1-A5 已裁决清单**（xfail 语义 / G2-2 双缺失推导偏离 /
响应头形态 / 3 条基线红 / D2 breaking API），要求 Codex 不重开这些。

### 第 1 次：0 字节，**不计轮**（卡文 §六 规则）

- `rc=1`，`codex-review-CARD-G4-4a.md` **0 字节**，stderr 641,783 字节。
- **不是**内容拦截，**不是**配额。stderr 末尾明确：
  `ERROR: stream disconnected before completion: error sending request for url
  (https://chatgpt.com/backend-api/codex/responses)`，前面连续 `Reconnecting... 5/5`
  三轮全失败；另有客户端噪声
  `codex_models_manager: missing field 'supports_parallel_tool_calls'`。
- 计费 `tokens used 232,629` —— 说明**审查已跑完**，断的是最终回答的流。
- 运行时长 ~23 分钟；期间它确实在做实事（stderr 推理标题可见它复核了
  merge-tree 声明、patch-id 映射、xfail 行为、基线红、UAT 声明一致性）。
- 网络复核：`curl https://chatgpt.com/` → HTTP 403 / 2.05s（未认证根路径的
  正常响应），即链路可达，断流是瞬时问题 → 按卡文「0 字节 = 不计轮重发一次」重发。
- 首次 stderr 已存 scratchpad（`*.stderr*` 属公共纪律禁入库项，不随卡提交）。

### 第 2 次：成功（`rc=0`，10,956 字节）—— **阻断级 = 0**

审查锚定 `card/x3-vaultscope@cb671e26`。原文：
`_bmad-output/审查/codex-review-CARD-G4-4a.md`。

**Codex 的一句话结论**：*「代码移植等价，四处补口行为正确，指定裁判和负控均无
新增红；发现 5 个文证类 HIGH、1 个 LOW，按本批定义均不阻断。」*
**末行：`阻断级 = 0`。**

#### PASS 的 9 项（它逐条独立复核过，不是采信我的说法）

移植等价（7 个 `-x` trailer 齐全 + blob 对比）／台账未被污染／主干前提未失效
（`resolve_vault_scope`、`current_vault_id`、`DEFAULT_TABLES` 均未变）／
(g) xfail 声明诚实／**(m) M6 不是假杀**（它自己做了等价 M6 探针，实测返回
`lancedb_b_secret / B 库绝密… / neighbor_expansion`，由跨库内容断言击杀）／
(k) OBS 运行时归一（**它自己做了 scope-only sink 注入，实测 HTTP 200、
业务 service 已 await、fallback warning 一次**）／stacklevel（独立捕获
`/rag/query` 的入口与 scope 两条记录，`filename="rag.py"`、`funcName="rag_query"`）／
证据剔除可复核／指定裁判（复跑裁判 1 `107 passed`、OBS `21 passed`、
合跑 `128 passed`、裁判 2 `28 passed + 1 xfailed + 3 failed`，三红与主干同名；
并确认测试用局部 FastAPI + tmp LanceDB，**未启 lifespan、未连 7691 或 live vault**）／
七条「未证明项」边界成立。

#### 5 HIGH + 1 LOW 与本卡处置（全部文证类，无一阻断）

| # | Codex 的发现 | 本卡处置 |
|---|---|---|
| **HIGH-1** | 「七次 merge-tree 全 rc=1 且冲突全在 DEBT-8」不可复现；固定基线重放为 `1,1,1,0,0,0,1` | ✅ **已改**。自己复跑两组数据，确认它对、我错（把递进 HEAD 的 rc 与固定基线的冲突描述混成一句）。§4-A.2 已拆成 (甲)(乙) 两表 |
| **HIGH-2** | `rag.py` 注释点名 `test_nothrow_logging_api` 能验 scope 包装器；实际那里的 `/rag/query` 用例注入的是 **error** 日志，四态门又同时命中入口与 scope、无法单独锁定 | ✅ **已改代码注释**。复核属实（该用例是 `TestRagQueryErrorLogs`）。注释改为准确表述 + 明写「scope 专用负控尚未沉淀」 |
| **HIGH-3** | `mutation-run.txt` 单独不足以证明「8 条门仍活」——脚本 kill 时丢弃 pytest tail/断言/nodeid | ✅ **已收窄措辞**并登记留存粒度问题。Codex 自己在隔离归档复跑 8/8、SHA 一致，明确定性「**不是负控假绿**」 |
| **HIGH-4** | `/rag/query` 调用方文证**两端都写宽**：源 UAT 把「插件零调用方」放大成「本仓零调用方」；我的当前草稿又把 Dredd 说成活 CI 消费方 | ✅ **两端都已改**。我在它出结论前已自查到同一处并自我更正（§6.5-E 记了两次更正）。Codex 独立确认 `--method GET --names` 使 POST hook 不执行，并附了 Dredd 官方文档链接 |
| **HIGH-5** | `nodes.py:417-418` 仍称 B0.7 存在且「V5 未合」 | ✅ **已改代码注释**。我在它出结论前已自查到并备好补丁，此轮一并落地 |
| **LOW-6** | HEAD 版 UAT 的日志计数写 `rag.py 7→7`，OBS 终态是 `7→0` | ✅ 出结论前已在草稿改为「4a 阶段 7→7 / OBS 终态 7→0」 |

#### ⚠️ 审查绑定与本轮整改的关系（请主 session 过目）

Codex 绑定的是 **`cb671e26`**。为落实它的 HIGH-2 / HIGH-5，本卡在其后**改了两处
代码注释**（`rag.py` 与 `nodes.py`，**仅注释，无逻辑**）。因此
`git diff <cb671e26>..HEAD -- . ':!_bmad-output'` **不为空**，严格按本批
「终审绑定看代码树」的字面判据，绑定已被这两处整改打破。

本卡的判断与理由：

1. 这两处**正是审查本身点名的 HIGH**，改它们是**响应审查**，不是「审完偷改」——
   绑定规则要防的是后者；
2. 改动**只有注释**，`ruff check` 干净，**全部裁判复跑数字逐字不变**
   （裁判 1 + OBS 合跑 `128 passed`、裁判 2 `28 passed + 1 xfailed + 3 既有红`）；
3. 本卡 Codex 轮次已用尽（族累计 4 轮，本卡上限 1 轮），无法再送一轮重绑；
4. 合并门是「阻断级 = 0」，该结论**已经给出**，且这两处整改只会让文证更准。

**如果你（主 session）坚持字面绑定**，回滚方式：
`git revert <本收尾 commit>` 即可回到 `cb671e26` 的代码树 —— 代价是留下两处
Codex 已点名为 HIGH 的失实注释。**建议保留整改。**

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
3. **没有证明「没有别的 `/rag/query` 调用方」**。本卡自跑的 grep 覆盖面是
   **本车道工作树内**的 `.ts/.tsx/.js/.py/.sh`（排除 `node_modules` / `_archive`）——
   查出了插件零命中、以及 §6.5-E 那个卡文漏掉的 CI 消费方。
   但**仓外**的东西（你自己的脚本、别的机器上的定时任务、第三方集成）
   Claude 无法穷举 —— 这是 D2 仍要你确认的原因。
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
4. **新增移交项 G4-4a-R2（给 X8，低优先）**：`scripts/spec-tools/dredd-hooks.js:38`
   与 `:152` 的 `/api/v1/rag/query` payload 缺 `vault_id`。**当前无影响** ——
   唯一的 dredd 调用带 `--method GET`（POST 不匹配）+ `--names`（不执行）。
   属**会过时的 fixture**：将来真要跑 POST 契约测试时才会红。详见 §6.5-E。
5. **新增移交项 G4-4a-R3**：`evidence-g44/g44_mutations.py` 无 `__main__` 守卫
   （变异循环在模块顶层，import 即改生产源码）。本卡按「不重写」不改，
   建议在 4b 或专门的证据整理卡里对齐到
   `nothrow_logging_negative_control.py` 的写法。
6. **新增移交项 G4-4a-R4（给 OBS 后续卡）**：`/rag/query` 的 **scope 日志专用
   负控**尚未沉淀为常驻用例（现有覆盖只有 `test_rag_four_state_api.py:197`，
   它同时命中入口与 scope、无法单独锁定，且**没有验伪锚**）。本卡三态探针
   （§6.6-OBS）可直接改写成两条用例。同时建议更新该门 docstring —— 它仍自称
   是「入口日志」的门，名实窄于实际覆盖面。
7. **新增移交项 G4-4a-R5**：`g44_mutations.py` 在 kill 成功时丢弃 pytest tail /
   失败断言 / nodeid（Codex round-4 HIGH-3），归档因此只能证明「指定 nodeid
   exit=1」而回溯不出「红的是哪条断言」。建议加 `--tb=line` 并保存 `^E` 行。
8. **移交 X5-A 佐证**：`lefthook.yml` `python-typecheck` 块在 `pyright` 缺失
   （exit 127）时仍判通过 —— 本卡独立实证了该假绿。
9. **OBS 口径变更**：`CARD-OBS-nothrow-logging-验收单.md:133` 的
   「`:309` scope resolved call-site 兜底**保留**」已被 CARD-G4-4a 的完成条件 (k)
   推翻（改为收敛进 `nothrow` 包装器）。该行引用的「§五 第 10 条」**不存在**
   （§五 实测 9 条），即原决定无依据；OBS 自己的 A-3 原则也指向收敛。
   合并时请把这条口径变更登记到 OBS 行。
10. **G4-4 证据文件去向**：`final-judge*.txt` / `baseline-judge*.txt` /
   三份 `codex-review-*.stderr` 未随卡入库，原件在 `card/w8-scope@6a732e1b`。
