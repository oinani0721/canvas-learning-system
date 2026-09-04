# UAT · CARD-G8-2b（G8-2 round-12 的 6 MEDIUM + 1 LOW 收口）

> 批次：[BATCH-2026-09-04-第十批 / CARD-G8-2b] · 车道 `card/x5-micro`（从 `1f249b33` 切）
> 改动面：`backend/scripts/vault_lint.py`（一处 key 形态 + 一处注释）· `backend/requirements.txt`（+1 声明）
> · `backend/tests/unit/test_vault_lint.py`（+1 门）· G8-2 验收单五处更正 · evidence-g82 的 MANIFEST 与 harness
> 提交：本卡单 commit，未 push、未合并

---

## ⛔ 先读这段：卡文 C3 的前提被证伪了

卡文 `X5.md:26` 记：*「harness 实有 22 条 `mutate_and_test`，`mutation-transcripts/` 只有 21 份 → MANIFEST 改 21/21 并**登记第 22 条未存证**」*。

**去源头查了，没有第 22 条。** 那个 22 来自判据本身：

```
$ grep -n '^mutate_and_test' g82_mutation_negative_controls.sh | head -1
18:mutate_and_test() {          ← 函数定义，被判据数成了一条变异
```

改用只数调用的判据 `grep -c '^mutate_and_test "'` → **21**，与 21 份 transcript **逐条同名、一一对应、零缺证**（差集为空，已实测）。M13/M16/M21/M22 是**已删除编号**（harness `:136` / `:196` 有记录）。

所以本卡按 M6 的**意图**（让 MANIFEST 诚实）执行，但**没有**照抄「登记第 22 条未存证」——那会把一个不存在的缺口写进档案。MANIFEST 里改写成计数更正 + 误计来源。**卡文与手册里的裁判命令也需同步改成带引号的那条。**

---

## 1. 🎯 一句话目标

把 lint 的 round-12 遗留收干净：孤儿检查的异常清单**不再让同名文件互相遮盖**，档案里几个对不上的数字改成实数，依赖不再靠"碰巧装着"。

## 2. 📖 你的视角

作为看 lint 报告的人，我想相信「盲区清单里列了几条，就真的是几条」，**以便**两个不同文件夹里都叫 `same.md` 的时候，不会有一条问题被另一条悄悄顶掉、我却以为已经看全了。

## 3. 🖥️ 交互流程（你的屏幕变化）

跑 lint 时若两个子目录下的同名文件都有 AUTO 段结构异常，报告里现在会列出**两条**（各带自己的完整路径 `原白板/d1/same.md`、`原白板/d2/same.md`），而不是只剩一条。现网当前没有这种异常，所以你现在看到的报告**一个字都不会变**。

## 4-A. 🤖 Claude 已代验

| # | 项 | 结果 | 证据 |
|---|---|---|---|
| C1 | **先红**：两子目录各一 `same.md`、同行号同因 → 断言 anomaly 2 条 | ✅ 现状 **1 条** | `AssertionError: 实得 ['AUTO 异常 [原白板/same.md] 行 2: …']` / `assert 1 == 2` |
| C2 | **后绿**：anomaly key 含 src **完整相对路径**；测试断数量 + key + blind_detail | ✅ | `blind[f"AUTO 异常 [{src_rel}] {anomaly}"]`，`src_rel = src.relative_to(vault).as_posix()`——与本函数其余 blind 键（blocked / unreadable / own）同口径 |
| C3 | M6 对账：MANIFEST 改诚实 | ✅ 改为 **21/21** + **误计来源登记** | 见上「先读这段」；**未重跑 harness**（它原地改生产源码，且与 X1 互斥） |
| C4 | M1：`requirements.txt` 显式声明 + `:99` DEBT 指向改正 | ✅ | `markdown-it-py>=4.0.0`（计数 = 1）；`:99` 原写「DEBT-1 排第九批补声明」→ 已改（总账 DEBT-1 实为「全量测试超时」，与本依赖无关） |
| C5 | M2/M3：UAT 数字与轮次史 | ✅ 五处 | 顶部 `22 个锚位`→`21 条`＋误计说明；`11 轮`→`12 轮`（存档实数 12 份）；`:49` `19`→`21`；`:111` `19/19`→`21/21`；`:189` `round-3（终轮）`→ 补 r4-r12 续轮史 + r12 PARTIAL |
| C6 | B1/B2 登记文字 | ✅ | B1 改「**部分异常可检测**」（只对四类记 anomalies，其余静默盲化；现网 `anomalies=[]` 从未触发）；B2 泛化为「任意非-`text` raw carrier」+ 点明 **false-negative 方向 = 漏报孤儿**（与 B3 的 fail-closed 相反） |
| C7 | LOW3 去重 | ✅ | harness M23 注释 5 份重复 → 1 份；`bash -n` 语法过；调用数仍 21 |
| C8 | 89 基线 + 新增全绿，不引入新 warn | ✅ **90 passed, 0 failed, 0 skipped** | 10 条 warning 全部来自第三方/无关模块（genai / graphiti_core / jieba / langchain / pydantic / importlib / chat.py / metadata.py），**命中 `vault_lint` 的 warning = 0** |
| C8' | `:851` `test_live_vault_readonly_and_runs` 真跑未 skip | ✅ | 无 skipped（`90 passed` 全量无跳过） |
| C9 | M5 改 key 后 live 对账失效并只读重算 | ✅ | 新增 `live-lint-round14.json`（rc=2）+ rc/window/sha 四件；live sha 前后**逐字相同** `a82e3af0…`（零写）；round-13 在 MANIFEST 中标注失效 |
| C10 | 本卡不引入格式漂移 | ✅ | 两文件 HEAD=CLEAN，改后一度 DRIFT → 已 `ruff format` 归位；`ruff check` 全过；改后重跑仍 90 passed |
| C11 | MANIFEST 可自校验 | ✅ | 被审源码块 **5/5** + evidence 块 **122/122** 逐条 sha 复算一致 |
| C12 | 硬边界 | ✅ | 未动 `wikilink_graph_service.py`（M4 待裁决）；未跑变异 harness；未跑 `test_daily_review_run.py`；`board_manifest_last_run.json` 未进本卡改动面 |

### C9 的诚实结论：M5 在现网**看不出差别**

`live-lint-round14.json` 与 `round13` 的**唯一**差异是日期（`generated_at` / `today`，freshness 的结构性窗口）。orphan 检查两轮都是 `blind_spots: 0` / `blind_detail: {}` ——**现网没有任何 AUTO 段结构异常**，所以 key 形态换了在现网**零可观测差异**。M5 的修复只由 fixture 门证明，见「本卡未证明什么」第 2 条。

### C11 顺带抓出的存量问题（本卡一并收口）

MANIFEST 的「被审源码 sha」块原先钉的是 w9-lint 基线 `9af18b27` 的字节，而 `check_vault_doc_roles.py` 与 `vault_doc_roles.yaml` 已被 **V5（`9e238dc5`）**改过——所以这份「全覆盖」的 MANIFEST 在主干树上**一直有 2/5 条对不上**（正是 G8-2 UAT §5 第 7 条预告的「V5 合入后须复跑」）。本卡未改这两个文件，只把登记值重钉到当前树并在 MANIFEST 里写明来龙去脉。

## 4-B. 👤 你来验

- [ ] 我打开 lint 的孤儿清单 → 我看到**同名文件不再互相遮盖**（两个文件夹里都叫同一个名字时，各自的问题各占一行、各带自己的文件夹名）→ 我感觉这份清单可以放心当作"全部问题"来读。

> 说明：你今天的报告**内容不会变**——现网眼下没有会触发这条的文件。这一条要等真出现同名文件的那天才看得见。

## 5. 🚦 验收结果

- 技术侧（4-A）：**C1-C12 全绿**，90 passed。
- 完成条件 C1-C9：全部满足；**C3 按查证结果作了一处偏离**（不登记「第 22 条未存证」，改登记误计来源）——见顶部说明。
- Codex 审查：按卡文「三张微卡默认不送」——**未送审**。

## 6. 📝 批注区

[!question]+ 你的批注写在这里（Cmd+Shift+A）

[!note]+ 为什么用完整相对路径而不是继续拼 `{src_dir}/{src.name}`
> 同一个函数里其余三种 blind 键（blocked / unreadable / own）本来就用 `src.relative_to(vault).as_posix()`。anomaly 这一条是唯一的例外，也正因为这个例外才会撞键。改成同口径以后，四种键形态统一，不用再记"哪一种是特例"。

[!error]+ r12 M6 的两处措辞过宽（本卡整改）
> B1 写「段内 fence 标记行/异常已显式记 anomalies 披露」，读起来像"任何异常都会被看见"——实际只有四类（fence 标记行 / 疑似 fence info / 嵌套 BEGIN / EOF 未闭合）会记，其余一律静默盲化。B2 只写 `code span`，但 code span 只是"不进 `text` children 却仍在原文裸集合里"的载体之一。两处都已收窄/泛化，并补上 B2 的 false-negative 方向。

## 7. 🔗 技术 spec 引用

- 卡文：`goal-cards/第十批-goals/X5.md` § C（完成条件 C1-C9 + 默认裁决）
- 实现：`backend/scripts/vault_lint.py`（anomaly key + `:99` 注释）
- 依赖：`backend/requirements.txt`（`markdown-it-py>=4.0.0`）
- 测试：`backend/tests/unit/test_vault_lint.py::test_auto_anomaly_keys_disambiguate_same_name_across_subdirs`
- 档案：`_bmad-output/审查/evidence-g82/MANIFEST.txt` · `g82_mutation_negative_controls.sh` · `live-*-round14.*`
- 上游更正：`_bmad-output/验收单/UAT-CARD-G8-2-统一lint骨架与三检查.md`（顶部 / `:49` / `:111` / `:189` / §7 / B1 / B2）

---

## 待你裁决（本卡默认值先行，均可改）

| # | 事项 | 本卡采取的默认 | 备选 |
|---|---|---|---|
| ① | **C4 打破了「本批不动 requirements」约定** | **改了**（卡文默认裁决）：加一行 `markdown-it-py>=4.0.0`。理由——不声明的话，上游换掉 rich、或 rich 放宽下界让 mdit 漂到 3.x，lint 会在干净环境以 rc=3 罢工，而 requirements 里查不到任何线索 | 撤回这一行，继续挂 DEBT 卡（那 `:99` 注释也要跟着回退） |
| ② | C3 的偏离 | **不登记「第 22 条未存证」**，改登记误计来源（因为查证后不存在第 22 条） | 若你要求逐字照卡文执行，我把那句话写回去——但它会是一条与事实不符的档案 |
| ③ | M4（orphan 权威口径） | **不动实现**（卡文明令），只改 B1/B2 登记文字 | 你裁定权威口径后另立卡改实现 |
| ④ | 变异 transcript 已失效 | **不重跑**（卡文明令：harness 原地改生产源码，且与 X1 车道互斥）；已在 MANIFEST 逐条标注失效 | X1 跑完后另起一卡复跑 21 条 |
| ⑤ | MANIFEST 两条存量 sha | **重钉到当前树**并写明来源（V5 `9e238dc5` 改过） | 保持钉在 9af18b27（那 MANIFEST 就永远自校验失败） |

---

## 本卡未证明什么（必填段，如实）

1. **变异负验证一条都没跑**：21 份 transcript 由 round-12 字节生成，本卡改了 `vault_lint.py` 字节 → 按 MANIFEST 自己的失效条款，**它们对当前字节不构成任何负验证**。新增的 M5 门**没有配套变异**——「把 key 改回 `{src_dir}/{src.name}` 会不会让新门变红」本卡**没有实测过**（只有先红记录：改之前它确实是红的，这已是同形态的证据，但不是一次受控变异）。
2. **M5 的修复在现网零可观测差异**：live round-14 与 round-13 的 orphan 部分完全相同（`blind_detail: {}`）。现网从未产生过 AUTO 段结构异常，所以这条修复**只有 fixture 门背书**，没有任何现网证据。
3. **`markdown-it-py` 的声明没做 clean install 验证**：只加了一行声明，**没有**在干净环境 `pip install -r requirements.txt` 跑一遍确认 4.0.0 装得上、lint 跑得通（本车道用的是 `card-v5-lance` 的既有 venv，本来就装着 4.0.0）。G8-2 §7 移交项的另一半仍是 open 债。
4. **G8-1 的 119 条不回归没复跑**：只跑了 `tests/unit/test_vault_lint.py` 单文件（卡文禁目录级 pytest）。G8-2 顶部那个「208 passed」在本卡改字节后**已失效**，本卡没有重建它。
5. **UAT 里被更正的数字是"按存档实数"**，不是重新跑出来的：`21 条变异`来自 harness 与 transcripts 的当场清点，`12 轮`来自 `ls codex-review-CARD-G8-2*.md` 的份数，`r12 PARTIAL 0B/0H/6M/1L` 来自 round12 存档首行。**没有**去复核每一轮审查结论本身。
6. **M4 的口径分歧原样留着**：`wikilink_graph_service` / mdit 渲染 / Obsidian 三方口径差异未做任何比对，B2 的 false-negative 方向是**按代码逻辑推的**，没有构造反例实测。
7. **没验 `blind_spots` 计数在真实多异常场景下的正确性**：新门的 fixture 刻意只触发一条 anomaly（否则 2 vs 1 就不是判据了）；复合异常（一个文件同时 fence + 嵌套 + EOF 未闭合）× 多子目录的组合**没测**。
8. **没测 symlink / 目录别名下的 anomaly key**：`src.relative_to(vault)` 用的是遍历路径而非 realpath，与同函数里 inbound 来源键（用 realpath）口径不同。别名目录下同一物理文件产生两条 anomaly key 是否算重复披露——**本卡没有评估**。

## 移交登记

**台账待登记条目**（本卡按纪律**不动** `未合卡追踪台账.md`）：

1. **CARD-G8-2b 完成，未 push 未合并**，车道 `card/x5-micro`（同车道另有 CARD-DEBT-hook-pyright `e56a9beb`、CARD-G3-6b-R2 `9d1e6f01`）。
2. **⛔ 卡文/手册勘误**：`X5.md` § C 与开跑手册里的裁判 `grep -c '^mutate_and_test'` **数多一条**（把函数定义算进去了），须改成 `grep -c '^mutate_and_test "'`。据此推出的「第 22 条未存证」不成立。
3. **变异 transcript 全部失效待复跑**：21 条，绑 round-12 字节；G8-2b 改字节后失效。X1 变异跑完、互斥解除后另起一卡复跑。
4. **`markdown-it-py` clean install 未验**：G8-2 §7 移交项只收口了「声明」一半。
5. **G8-2 顶部「208 passed」失效**：当前字节的实测只有 `test_vault_lint.py` 单文件 90 passed；G8-1 119 不回归未复跑。
6. **MANIFEST 存量两条 sha 已重钉**（`check_vault_doc_roles.py` / `vault_doc_roles.yaml`，因 V5 `9e238dc5` 改过）。若 G8-2（w9-lint 车道）尚未合并，合并时注意这两条已被本卡改写。
7. **M4 orphan 权威口径仍待你裁决**（本卡只改登记文字，未动实现）。
8. **新债（本卡第 8 条未证明）**：anomaly key 用遍历相对路径、inbound 来源键用 realpath，两者口径不同；目录别名下的重复披露未评估。
