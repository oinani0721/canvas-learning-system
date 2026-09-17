---
story: "CARD-U6C-HANDOVER"
title: "u6c-handover-四条移交面收口"
status: "review"
version: "1"
date: "2026-09-17"
developer: "Claude Code (Opus 5 1M context)"
commit: "bbf2a94e + 3fa154ef + r1 后修正"
---

# CARD-U6C-HANDOVER 验收单（给你看的版本）

> [!info]+ 这是什么
> 第十四批 T3 车道第 4/4 张卡。收口上一张卡（每日复习「今晚再说 / 这板做完了」那一批）
> 合入时**记下来但没做**的四件事。这份文档里没有技术术语，只有你能看到、点到的行为。

---

## 🎯 这个卡要做到什么

让**每日复习**这条链在三种以前会出岔子的情形下不再出岔子：库里那份小账本被外部写坏时不再
整轮停摆、跨过当地午夜那一秒点「重新算一遍」时刚标完成的板能正确让位、以及给两处内部
按钮状态的记账补上一道以前只管了一半的防线。

---

## 📖 用户故事（你的视角）

**作为** 每天用这套系统复习的人，
**我想** 不管是半夜十二点整那一刻点刷新，还是那份账本被什么东西写乱了，每日复习都照常给我今天该看的板，
**以便** 我不用去猜「今天怎么没提醒我」或者「我明明标完成了，榜首怎么没换」。

---

## 🖥️ 你会看到的交互（一步一步）

```
1. 我打开复习总览那一页
       ↓
2. 我看到每个库一张卡片，里面有几块板排着队，最上面那块是「今天先看这个」
       ↓
3. 我点某块板上的「✅ 这板做完了」
       ↓
4. 我点「🔄 刷新投影」
       ↓
5. 榜首换成了下一块板，刚标完成的那块折进「已完成」那一格里（还在，没消失）
```

以前这一步在**当地午夜前后那一两秒**会失灵：我 23:59:59 标完成，页面重算时已经是第二天
00:00:00 了，它会认为「这不是今天标的」，于是榜首纹丝不动——看起来就像「标了也没用」。
现在标完成和重算用的是**同一个时刻**，那一秒不再是空档。

---

## 🤖 Claude 已代验（你不用跑，给你看证据用）

> [!success]+ 这一段是 Claude 自动跑完贴证据
> **你不用跑也不用懂**。你只看右边「结果」列是不是 ✅。

| # | 技术验证项 | 结果 |
|---|---|---|
| 1 | 开工第 0 分钟：分支 `card/t3-review`、`git status --porcelain` = 0、`backend/.venv/bin/pytest` + `backend/.env` 就位 | ✅ 开工 commit `PREV=f73dedfe` |
| 2 | 开工 pyright 基线（cwd=`backend/`，R-B14-10） | ✅ `0 errors, 82 warnings`；`evidence-u6c-handover/pyright-baseline-20260917T124633.txt` |
| 3 | 开工红基线自证（R-B14-2 唯一口径 `grep -vc '^#'`） | ✅ **64** |
| 4 | 地盘扩充自证（R-B14-4 身份口径，须恰 1 行） | ✅ `grep -cF 'T3-D +\`scripts/daily_review_run.py\`'` = **1**，命中手册 `:71`「地盘扩充（裁定 R-B14-4，主 session 已跨车道核无冲突）」行；原文附加约束逐字：**「只改 `due_crossed` 判型与父子墙钟传参段」** |
| 5 | 地盘自证的两个验伪锚（同次） | ✅ 锚① `**只 T3**` 命中 `:62`；锚② `T8-F +` 命中 `:71`（证扩充表整行仍在） |
| 6 | §〇 锚点复核（T3-A/B/C 串行后行号漂移） | ✅ 逐条实测，漂移见下方「行号漂移记录」 |
| 7 | item ① 先红 | ✅ 5 个承重档全部红在 `scripts/daily_review_run.py:588` 的 `TypeError`（int/bool/float/list/dict）；`due-crossed-BEFORE-20260917T125004.txt` |
| 8 | item ① 后绿（文件级全量） | ✅ **74 passed**；`due-crossed-AFTER-20260917T125101.txt` |
| 9 | item ① 控制组（合法 ISO 串仍须让缓存失效） | ✅ `..._control_group_still_reads_valid_iso` 绿——退化实现 `due_crossed = False` 会在此红 |
| 10 | item ② 先红 | ✅ 红在身份层「子进程 argv 里没有 --now」；`parent-child-clock-BEFORE-20260917T125229.txt` |
| 11 | item ② 后绿（含既有 g67r 族） | ✅ **12 passed** |
| 12 | item ③ 门（JS 沙箱，真 node 进程） | ✅ `tests/unit/test_review_app.py` **99 passed**；`key-collision-20260917T125621.txt` |
| 13 | item ④ 三颗哑弹拆除后回归 | ✅ 14 passed（三条哑弹 + item② 门 + g67r 族） |
| 14 | 负控 NC-1（item ① 生产面还原成开工态） | ✅ 指定门红在 `:588` TypeError；还原后 `shasum -a 256` 两侧逐字节相同 |
| 15 | 负控 NC-2（item ② 还原 + **临时摘除身份层**） | ✅ 行为层第三条断言**自己**红：「子 2026-09-17 vs 父 2026-09-16」——证它不是被身份层遮住的死判据 |
| 16 | 负控 NC-3（`wall_now` 改走 `datetime.now(_display_tz())`） | ✅ 身份层红出「--now 传的不是父侧那一刻」。⚠ **表述收紧（Codex r1 LOW-1）**：这条变异同时让身份层与行为层都不成立（只是执行停在身份层），所以它证明的是「绕开可钉入口会被门抓住」，**不能**单独证明「只有身份层变红」——那由下面 NC-3b/3c 承担 |
| 16b | 负控 **NC-3b**（Codex r1 指定：`wall_now` 偏移 1 秒，同日不同刻） | ✅ 身份层红在 `'…23:59:58.900000+08:00' vs '…23:59:59.900000+08:00'` —— 同一天、只差 1 秒 ⇒ **身份层有独立作用** |
| 16c | 负控 **NC-3c**（NC-3b 变异 + 临时摘除身份层） | ✅ **1 passed** —— 行为层在该变异下确实绿 ⇒ 与 16b 合起来精确证明「偏移 1 秒只让身份层变红」 |
| 17 | 负控 NC-4（`doneKey` 分隔符 NUL → `\|`） | ✅ **新反向门 ✖ 红、旧正向门 ✔ 绿** —— 精确证明新门补的正是旧门的盲区 |
| 18 | 负控 NC-5（`snoozeKey` 换成 round-5 被打回的实现，卡文点名的验伪锚） | ✅ 正向门红；新反向门同样红 |
| 19 | 负控 NC-6（item ② 还原 ⇒ 哑弹② 必红） | ✅ 红在「已完成的板必须让出榜首」 |
| 20 | 负控 NC-7（哑弹① 引信可达性） | ✅ `assert 2 == 0` —— 与卡文预言的「两个未来节点到期 ⇒ 实为 2」逐字一致 |
| 21 | 负控 NC-8（哑弹③ 引信可达性） | ✅ `assert 'stale' == 'ok'` —— 与卡文预言的「投影成 stale」逐字一致 |
| 22 | 全部 9 条负控的还原自证 | ✅ 每条跑后 `shasum -a 256 <文件> <变异前副本>` 两行相同；全程未用 `git stash` / `git checkout` |
| 23 | 收工 pyright（★app 必须 0） | ✅ `0 errors, 82 warnings` —— warnings 与开工基线**逐字相同** ⇒ 本卡零新增；`pyright-after-20260917T130142.txt` |
| 24 | ruff check / format（6 个改动文件） | ✅ `All checks passed!` + `6 files already formatted`；`ruff-worktree-20260917T130215.txt` |
| 25 | ruff 验伪锚①（pathspec 有牙，须含顶层 `scripts/*.py`） | ✅ 文件集含 `scripts/daily_review_run.py`，计数 = **1** |
| 26 | ruff 验伪锚②（ruff 有牙） | ✅ F821 探针文件 `anchor_rc=1` |
| 27 | `tests/unit` 目录级 + 与 64 条红基线 nodeid diff | ✅ diff **空集**（无 `<` 无 `>`），两侧同口径计数 64 = 64；`unit-reddiff-20260917T130805.txt` |
| 28 | (i) diff 判据的验伪锚 | ✅ 右侧塞一条假 nodeid 时 diff 吐出 `>` 行 —— 证这条判据不是恒空 |
| 29 | `tests/regression` 目录级 | ✅ **1930 passed**（基线 1674 不回退），1 failed 已归因为**既有红**，见下 |
| 30 | 那条 regression 红的归因（NC-9） | ✅ 三重证据：本卡 diff 新增行里四个 runner 专属键计数**全 0**；`$PREV` 版本 grep 已命中 **2** 处；把 `backend/app` 两文件还原成开工态后**仍红** |
| 31 | (h) 地盘核（`--no-color` + `':(exclude)…'`） | ✅ 恰 **6** 个文件，全部 ⊆ 允许面（§三 五文件 + R-B14-4 扩入的 `scripts/daily_review_run.py`） |
| 32 | R-B14-4 附加约束自证（按 hunk） | ✅ `scripts/daily_review_run.py` **只有一个 hunk** `@@ -588 +588,8 @@`，只落 `due_crossed` 判型段；父子墙钟传参段未动（runner 进程内直调 `picker.build_payload(VAULT, now, …)`，本来就在传自己的参照时刻） |
| 33 | `backend/openapi.json` 净变化 | ✅ **0**。`spec-sync-flat` 的 glob 单 `*` 跨目录层级、把重生成的快照塞进了代码 commit；还原前实测全部差异 = `x-generated-at` 一行，schemas/paths 零变化；用 `git show <开工 commit>:` 写回 + 单独 commit `3fa154ef` 还原 |
| 34 | `*.stderr*` 不入库 | ✅ `git diff --cached --name-only \| grep -c stderr` = **0** |
| 35 | lefthook 全套（未用任何 `LEFTHOOK_EXCLUDE`、未用 `--no-verify`） | ✅ python-lint ✔ / python-typecheck ✔（0 errors）/ mutant-residue-scan ✔ / commitlint 0 problems |
| 36 | prompt 与 diff 的禁用措辞核（协议 §2 四词） | ✅ prompt 与代码新增行各自 4 词全 **0**；验伪锚：同一 grep 在同一文件上命中「值域」5 / 「判型」5 / 「墙钟」8 |

### 行号漂移记录（卡文 §〇 → 实测，T3-A/B/C 串行所致）

| 锚点 | 卡文 | 实测 | 漂 |
|---|---|---|---|
| `due_crossed =` | `:588` | `:588` | 0（`scripts/` 未被前序卡改） |
| `doneKey` / `snoozeKey` | `:202` / `:209` | `:202` / `:209` | 0 |
| `_run_pick` 的 `argv = [...]` | `:1887` | **`:1956`** | +69 |
| 哑弹① `def test_refresh_rebuilds_projection_and_response_matches_disk` | `:1353` | **`:1364`** | +11 |
| 哑弹② `def test_g67r_refresh_passes_state_and_done_board_yields_top` | `:3509` | **`:3520`** | +11 |
| 哑弹③ `def test_buckets_gate_accepts_real_producer_payload` | `:1060` | **`:1066`** | +6 |
| pyright warnings 基线 | 卡文 §〇 记 81 | 实测 **82** | +1（前序卡引入，errors 仍 0，不影响判据） |

---

## 👤 你来验（产品使用体验 — 4 步，10 分钟内全在浏览器里完成）

> [!warning]+ 这段只用浏览器，不需要打开任何黑底白字的窗口

### 第 0 步：First 5 seconds（第一印象）

- [ ] 我打开复习总览那一页，5 秒内看到每个库一张卡片，每张卡片里有几块板排着队
- [ ] 5 秒后我感觉这是 (a) 严肃学习工具 (b) 还在调试的玩具 (c) 看不出来 — 选: ___
- [ ] 一眼能看出哪块板是「今天先看这个」吗？(是 / 不能 / 模糊)

### 第 1 步：标一块板做完了

- [ ] 我在榜首那块板上点「✅ 这板做完了」
- [ ] 我看到卡片上冒出一句绿色的「已标记」，那块板折进了「已完成」那一格
- [ ] 我感觉 ______（顺手 / 迟疑「它到底记住没有」/ 别的，写下来）

### 第 2 步：让它重新算一遍

- [ ] 我点这张卡片上的「🔄 刷新投影」
- [ ] 我看到榜首换成了**另一块**板，刚才标完成的那块还在页面上（在「已完成」那一格里），没有凭空消失
- [ ] 我感觉 ______（「它真的听懂了」/ 「换得莫名其妙」/ 别的）

### 第 3 步：连点两次刷新（看它会不会假装成功）

- [ ] 我刚点完刷新，马上再点一次
- [ ] 我看到一句黄色的「几秒内已重建过」，**不是**一个和成功一模一样的绿勾
- [ ] 我感觉 ______（「它没糊弄我」/ 「我以为它坏了」/ 别的）

### 第 N 步：边界（如果我做错会怎样）

- [ ] 我故意去点一个还没配过每日复习的库上的「🔄 刷新投影」
- [ ] 我看到一页说人话的错误提示（比如告诉我这个库还缺什么），**不是**一大段红色英文
- [ ] 不会闪退 / 不会白屏 / 页面其它库的卡片还在

### 主观打分（Felt-sense）

- [ ] **流畅度**（1=卡顿到想关 / 5=如丝般顺滑）：___
- [ ] **易学性**（1=不看教程没法用 / 5=看一眼就会）：___
- [ ] **明天我会再打开它的可能性**（0-10）：___
- [ ] 一句话告诉 Claude，让你打这个分的最主要原因是：___

---

## 🚦 验收结果

**如果所有步骤 ✅**：告诉我「**CARD-U6C-HANDOVER 通过**」。
**如果有任何一步 ❌**：在下面批注区写出具体哪一步 + 你看到的实际现象。

---

## 📝 你的批注区

> [!question]+ 你对这张卡的批注
>
> （空）

### 已知的已批注问题（历史追溯）

无（本卡是 CARD-G6-6/U6-C 的移交项收口，非用户批注驱动）。

---

## ⛔ 本卡未证明什么（必填 ≥4）

1. **item ② 只合上了 `_run_pick` 这一道缝**。残留的「写推迟/完成账那次请求 / 刷新那次请求 /
   之后 GET 渲染那次」**三次独立读钟未消除**，跨午夜时彼此仍可能分叉。本卡**没有**在真实
   刷新链（真浏览器 + 真 launchd）上跨一次午夜验过这条修复——门是单元级的。
   ⚠ **定位更正（Codex r1）**：`_read_entry` 用的 `datetime.now(_display_tz())`（本文件的
   第二个时钟入口，属存量，本卡「禁顺手修存量」不碰）不是「之后 GET 那次」，而是**同一次
   refresh 的回读阶段**——也就是说同一个刷新请求内部仍有两次读钟，返回的 `entry` 仍可能
   是 `stale`。**不得宣称「整次刷新已经统一归日」**；本卡合上的确实只有 `_run_pick` 那一道。
2. **item ③「反向不可达」的前提是取名链快照而非代码不变量**。`doneKey` 自撞需库名或板名
   含 NUL，本卡判其经 `read_text → frontmatter 正则 → _fm_str` 取自 POSIX 文件名/目录名而
   不可达。将来任何非 POSIX 取名源（外部 API / 数据库列 / 用户直填板名）都能打破它。本卡
   **没有**穷举全部取名入口，只核了这一条主链。
3. **item ① 的判型只覆盖 `next_due_utc` 这一个键**。`st` 里其余外部可控字段错型时会不会
   抛出那个 `except (json.JSONDecodeError, OSError)` 接不住的异常，本卡**未测**：其中
   `snooze_wake_utc` 已由 Codex round-1 MEDIUM-4 补过判型、`payload_sha256` 只参与 `==`
   比较（不抛）。
   ⚠ **本条初版写「`board_last_recommended` / `board_done` / `snoozed` 会原样喂进
   `picker.build_payload` / `picker.active_snoozed`」——不准确，Codex r1 更正并经本车道
   复核实测**：`daily_review_run.load_state`（`:122` 起）对这三个键做了**顶层
   `isinstance(..., dict)` 校验**，非 dict 直接返回 None，不会透传。仍然未测的是**内部
   值**的错型（dict 的 value）与绕过 `load_state` 的直接调用边界。本卡「禁顺手修存量」，
   该面如实登记不做。
4. **`pyright app` = 0 errors 只是静态类型核**，不证本卡改动在运行期无缺陷。运行期由
   (c)(d)(f) 的先红后绿门 + 9 条负控覆盖，那不是 pyright 的职责。
5. **launchd runner 路径不受 item ② 影响是静态核结论**。依据是 `daily_review_run.py` 在
   `import daily_review_pick as picker` 后**进程内直调** `picker.build_payload(VAULT, now, …)`
   （`:604` import、`:613` 调用），不起 picker 子进程，本来就在传自己的参照时刻。本卡
   **没有**对真实 launchd :05 档跑一次验证。
6. **`tests/regression` 的 1 failed 归因是「代码维度对照 + 字面量计数」，不是 2×2 四轮**。
   本卡跑的是「同一轮次、两种代码态」的对照（NC-9）配合三重字面量证据，足以定性它非本卡
   引入；但**没有**跑「代码 × 轮次」的完整 2×2 来排除偶发。

---

## 📋 台账待登记条目（必填 ≥4，本卡不改台账，交主 session 登记）

1. **item ① 地盘扩充的约束面自证**：`scripts/daily_review_run.py` 依 **R-B14-4** 扩入 T3-D，
   附加约束原文「只改 `due_crossed` 判型与父子墙钟传参段」。实测本卡对该文件的 diff **只有
   一个 hunk** `@@ -588 +588,8 @@`，**只落判型段**（父子墙钟传参段未动，理由见代验项 #32），
   供集成期主 session 复核。**另**：设计稿 §3 T3 行本身尚未回填本体（只列了它的测试），
   待归档时同步。
2. **item ② 残留三次独立读钟未全消**，且 `_read_entry` 的 `datetime.now(_display_tz())` 是
   `review_overview.py` 的第二个时钟入口（存量，本卡禁顺手修）。launchd runner 路径不起
   picker 子进程、不受本卡影响（静态核）。建议另立卡收敛「全文件单一时钟入口」。
3. **item ③ 反向方向判「不可达」的前提是 POSIX 取名链快照，不是代码不变量**。一旦引入
   非 POSIX 取名源，`doneKey` 需要与 `snoozeKey` 同款的转义（**不是**再加一层前缀——前缀式
   已被 Codex round-2 / round-5 各打回一次）。常驻门「不相交是双向的」的第 ④ 条断言会在
   有人给 `doneKey` 补转义时翻红，届时须**重写定性**而不是删断言。
4. **item ④ 三条哑弹的处置结论 + 行号漂移记录**：①（`:1364`，2099 硬编码）→ **修**，改为
   相对今天的偏移；②（`:3520`，与 item ② 同根）→ **修**，钉父子同一刻；③（`:1066`，取日后
   跨午夜 stale）→ **修**，端点侧时钟钉到与夹具同一刻。三条都配了引信可达性或先红负控。
   行号漂移：勘探 `:1365/:3533/:1093`（assert 行）→ 卡文 `:1353/:3509/:1060`（def 行）→
   本卡实测 **`:1364/:3520/:1066`**。
5. **`2099-01-01` 硬编码在 `test_review_overview.py` 里还有 8 处**（`:961 / :2901 / :2964 /
   :3287 / :3427 / :3676 / :3846 / :3915 / :4396` 等，本卡只拆了 item ④① 点名的 `:1376/:1377`
   两处）。同族定时哑弹，本卡「禁顺手修存量」不碰，建议另立一张「2099 硬编码清零」卡。
6. **`tests/regression` 有 1 条既有红：`test_g6_9_boundary_matrix.py::test_push_failure_is_invisible_to_backend_app`**。
   它是 **T3-C（CARD-G6-9b）** 把 `generated_push_failed` 接进 `review_overview.py:2553/2595`
   造成的**预期翻红**——那条测试的 docstring 自己写着「哪天有人把这些键接进 `backend/app`，
   它会翻红提醒把登记项转正」。**需要 T3-C 或主 session 把那条登记项转正**（要么更新测试的
   登记口径，要么把徽标交付正式收编）。本卡三重证据归因见代验项 #30，不代修。
7. **lefthook `spec-sync-flat` 会把 `openapi.json` 塞进任何改 `backend/app/**/*.py` 的 commit**
   （glob 的单 `*` 跨目录层级，lefthook.yml 注释自述）。本卡用「单独一个还原 commit」化解
   （`3fa154ef`），净变化 0。这是批级模板缺陷，第十四批已有多张卡踩到（T3-C 的
   `baf8a693`、T5-E 同型），建议统一写进协议 §2.3。
8. **pyright warnings 基线从卡文记的 81 漂到 82**（errors 仍 0，不影响任何判据）。漂移由
   T3-A/B/C 串行引入，建议主 session 在集成期重取 warnings 基线。

---

9. **本卡自修了两处「由本卡改动直接造成的失实」（DD-13 名实一致，非顺手修存量）**：
   (a) `test_review_overview.py` 的 `_pin_child_now` docstring 原写「刻意**不**给生产加
   旗标」并列了三条理由——那是 U6-C 当时决定不做的依据，被本卡 item ② 推翻；已逐条更正为
   「仍成立 / 仍成立但不再是不做的理由 / 仍成立」三档，并说明 helper 保留当纵深。
   (b) 该 helper 原先盲目 `argv += ["--now", ...]`；生产加旗标后 argv 会出现**两个**
   `--now`。两处调用点都是 `pinned = _pin_now(...)` 紧接 `_pin_child_now(..., pinned)`
   ⇒ 两值**相同**、零行为差异，但「靠 argparse 取后一个」是隐式前提，已改为**显式替换**。
   (c) `:4527` 指向那段被推翻理由的注释同步更正。改后三文件 290 passed。

10. **Codex r1 结论与本卡处置**：**BLOCKER 0 / HIGH 0 / MEDIUM 0 / LOW 2**，审查范围
    `f73dedfe → 3fa154ef` = 绑当时最终 HEAD ⇒ **D-15 在 r1 即达成**。两条 LOW 车道**主动
    采纳并自修**（LOW-1 → 补 NC-3b/3c 两条负控 + 收紧验收单表述；LOW-2 → `doneKey` 单射
    定性在生产与测试两处逐字更正）。因改了代码，按 D-15 再送 **round-2** 绑新 HEAD。
    ⚠ 协议对 LOW 本是「登记不阻断」，此处选择修而非仅登记的理由：两条都是**本卡新写的
    文字里的事实错误**（不是既有存量），留着会让后人盯错地方——LOW-2 尤其，它既说错了
    「为什么安全」，又编造了一个不存在的未来风险（「用户直填板名即可打破」）。

11. **`doneKey` 单射的正确条件（Codex r1 LOW-2，本车道复核成立）**：单射只需
    **`vaultId` 不含 NUL**——此时 `v+NUL+b` 里第一个 NUL 的位置恒是 `len(v)`，故
    `len(v1)=len(v2) ⇒ v1=v2 ⇒ b1=b2`，**板名不受任何约束**。现状满足：`vault_id` 取自
    `review_overview.py:1070/:1172` 的 `vault_dir.name` / `v.name`（真实目录名）。
    ⇒ **未来要盯的是 `vaultId` 的来源，不是板名**。

## 🔗 技术 spec 参考（给 Claude 读的）

- **卡文**：`_bmad-output/implementation-artifacts/goal-cards/第十四批-goals/T3-D.md`（feature 主干树）
- **源代码**：
  - `scripts/daily_review_run.py`（item ①，单 hunk `@@ -588 +588,8 @@`）
  - `backend/app/api/v1/endpoints/review_overview.py`（item ②：`_run_pick` / `_rebuild_projection`）
  - `backend/app/api/v1/endpoints/review_app.py`（item ③：`doneKey` 定性注释，零代码改动）
- **测试**：
  - `backend/tests/regression/test_daily_review_run.py`（item ① 门 + 控制组，74 用例全过）
  - `backend/tests/unit/test_review_overview.py`（item ② 三层门 + item ④ 三颗哑弹）
  - `backend/tests/unit/test_review_app.py`（item ③ 反向门，99 用例全过）
- **证据目录**：`_bmad-output/审查/evidence-u6c-handover/`（21 份 `.txt`）
- **Git commit**：`bbf2a94e`（代码）+ `3fa154ef`（openapi.json 还原）— 终审绑定 HEAD `3fa154ef`
- **开工 commit**：`f73dedfe`（T3-C CARD-G6-9b 末 commit）

---

## 📅 下一步

1. **全部 ✅** → 说「通过」
2. **部分 ❌** → 在批注区写清楚
