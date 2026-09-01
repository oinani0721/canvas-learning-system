# UAT — CARD-G3-6b 板级 why_this_board 与系数版本化（rank_manifest）

> 批次 [BATCH-2026-09-01-第八批 / CARD-G3-6b] · 车道 card/w6-whyboard · 基线 9af18b27
> **复核轮 [BATCH-2026-09-01-第九批 / CARD-G3-6b-R1]（2026-09-02）**：冻结 `c2d2e590` 复核证据真实性 + 取非空终裁。本轮**不扩功能**，只做独立复核、边界收窄与证据当前化；R1 新增内容一律标注 `R1`。
> 验收单按 `templates/uat-sheet-template.md` 七段双段（DoD-3：4-A 全部裁判真实输出 Claude 代验；4-B 零技术词只写你能感知的）。

## 一句话

推荐白板时不再只给你一个冷冰冰的优先分——现在每块推荐板都附一句**用这块板自己的数据拼出来的人话解释**（几个节点到期、最早逾期几天、最该考的那张闲置多久、这块板多久没被推荐过）和一个**预计要花几分钟**；同时把决定「谁排前面」的全部系数登记进一个带版本号的清单文件，谁改了系数、改了什么，指纹立刻变。

## 🎯 这个 Story 要做到什么

- 板级推荐行加性追加 `why_this_board`（由投影内因子复算，禁 LLM、禁 UI 再算）、`estimated_minutes`、`factors`（数值因子全量落盘），排序因子清单显式化并写成书面裁定（S4/S5/S6，在 `scripts/daily_review_pick.py` 模块 docstring，Codex 按它审）。
- 系数版本化：新增 `scripts/review_rank_manifest.json`，payload 顶层加性 `rank_manifest: {version, sha256}`。
- 总览页每块推荐板行下多显示一句「为什么是这块板 · 预计 N 分钟」（缺字段整块不出现）。
- A2/A3/D2 冻结加性：schema_version 仍 3、既有键 byte 级不动、排序金样锁（top_boards 顺序与基线逐字相同）、runner 消费面零变化。

## 📖 用户故事（你的视角）

我早上点开总览页，看到「CS 61B」这块板下面多了一行小字：「为什么是这块板 · 2 个节点到期（其中 1 张新卡） · 最早的已逾期 21 天 · 最该考的已闲置 21 天 · 这块板从未被推荐过 · 预计 8 分钟」。不用再猜它为什么排第一——句子里的每个数字都来自这块板自己的数据，而且我能看到预计今天要花多少时间。手机推送的 Markdown（今日复习.md）末尾也有同样的「为什么是这几块板」清单。

## 🖥️ 你会看到的交互（一步一步）

（本卡无新交互——只在既有页面上多显示两样信息。）

1. 打开总览页 `http://127.0.0.1:8011/api/v1/review/overview/page`（部署合并后）。
2. 每块**推荐榜上**的板，数据行下方多一行灰色小字「为什么是这块板 · …… · 预计 N 分钟」。
3. 榜外板 / 旧投影：不出现这行（不伪造）。
4. Obsidian 里打开 `outputs/今日复习.md`，表格下方多一段「## 为什么是这几块板」。

## 🤖 Claude 已代验（4-A，你不用跑，给你看证据用）

### 裁判 1：测试套件

```
$ cd backend && caffeinate -i .venv/bin/pytest tests/regression/test_daily_review_pick.py \
    tests/unit/test_review_overview.py -q -p no:cacheprovider
======================= 130 passed, 10 warnings in 5.26s =======================
```

= 基线 37+56 全绿 + 新增 37 条（pick 32 + overview 5... 见用例清单）全绿。卡文要求新增 ≥8。
（121 → 126 → 130：Codex round-1/round-2 整改逐步新增门，见「Codex 对抗审查」节。）

**R1 复跑（2026-09-02，开工 `--collect-only` 实收，不照抄历史数字）**：

```
$ PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest … -q -p no:cacheprovider --collect-only
========================= 130 tests collected in 0.06s =========================
$ PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest … -q -p no:cacheprovider
======================= 130 passed, 10 warnings in 4.23s =======================
```

收集数 = 通过数 = 130（pick 69 + overview 61），无 skip/xfail 掩盖。R1 的 docstring
收窄改动落盘后复跑仍 130 passed —— 门全部是自洽/相对断言，不硬编码 sha 字面值。

### 裁判 2：live 只读探针（2026-09-01 实跑，PYTHONDONTWRITEBYTECODE=1、不带 --write；round-1 整改后复跑）

```
$ shasum -a 256 …/canvas-vault/outputs/今日复习.{json,md}   # 前置
$ python3 scripts/daily_review_pick.py --vault …/canvas-vault --now 2026-09-01T23:30:00+08:00 \
    | python3 -c "…assert schema_version==3; assert 'rank_manifest' in p;
                  assert all(b.get('why_this_board') for b in p['top_boards']); print('ok', p['rank_manifest'])"
ok {'version': 1, 'sha256': 'b3ff4b9998b6e336d7531b8a9a442a8e5e3c76f79b566edd593fbfb64f888483'}
$ shasum -a 256 …/canvas-vault/outputs/今日复习.{json,md}   # 后置
→ 前后逐字相同（live vault 零写入）
```

> **sha 演进轨迹 —— 每跳绑定 commit、pick.py 字节、rank sha 三元组**
> （R1 round-3 按 Codex MEDIUM 重排：原表把不同字节状态的数字混在一起，
> 且把「新断言纳入」写成了变化原因——**新断言在测试文件里，不进实现摘要**，
> 指纹只摘 `daily_review_pick.py` 的字节，所以每一跳的**唯一**原因都是它的改动）：
>
> | commit | pick.py sha256 | rank_manifest.sha256 | 这一跳由什么引起 |
> |---|---|---|---|
> | （历史，第八批内） | — | `e3a6c062…` | round-1 版实现 |
> | （历史，第八批内） | — | `b0c77f5c…` | 因子常量改名纳入 |
> | `c2d2e590` | `ad1a38a5…` | `b3ff4b99…` | 实现校验和纳入 |
> | `9e158d82` | `2c8da36c…` | `503fd4b6…` | R1 round-1：`_implementation_sha` 等三处 docstring 收窄 |
> | `66346bce` | `2c8186a1…` | `eb6b6710…` | R1 round-2：HIGH/M4 的 docstring 再收窄（**不含**测试侧新断言） |
> | 本次提交 | `1f5eb882…` | `bc3aa142…` | R1 round-3：M4 两处注释收窄 + 「三条→四条」 |
>
> ⚠ 归因纪律：`pick.py` 的**任何**字节改动都会换一次 rank sha，包括纯注释。
> 所以「指纹变了」不足以说明「排序规则变了」——这正是单向保证的含义。
> 读旧证据文件时必须先看它头部记的 `源码 sha256` 属于哪一行，不能跨行比对。

**R1 复跑（2026-09-02 04:11 +0800，避开 launchd 推送档位 9–20 点；`PYTHONDONTWRITEBYTECODE=1`、不带 `--write`）**：

```
前置 sha  今日复习.json 27d4204c…  今日复习.md c6585d38…
ok {'version': 1, 'sha256': '503fd4b6ac7d035c81df7892ae9e3801067c9c8cb05fd5e90e98559b5721f462'}
truncated {'top_boards': True, 'upcoming': False}
  CS 61B            |  8 分钟 | 2 个节点到期（其中 1 张新卡）· 最早的已逾期 22 天 · 最该考的已闲置 21 天 · 这块板从未被推荐过
  特征值与特征向量  | 10 分钟 | 2 个节点到期（其中 2 张新卡）· 最该考的已闲置 38 天 · 这块板从未被推荐过
  CS188 lecture 2   |  5 分钟 | 1 个节点到期（其中 1 张新卡）· 最该考的从未考察 · 这块板从未被推荐过
后置 sha  今日复习.json 27d4204c…  今日复习.md c6585d38…   → 前后逐字相同（live vault 零写入）
```

两处差异都已归因，均非缺陷：

1. **rank sha `b3ff4b99…` → `503fd4b6…`**：R1 只改了 `_implementation_sha` /
   `effective_rank_config` 的 docstring（零行为改动），指纹随之变化 —— 这正是
   「摘全文件字节、改一个注释也必变」这条声明的**活体验证**，而不是回归。
2. **逾期天数 21 → 22 天**：探针日期从 09-01 变 09-02，数据随时间自然演进
   （与「live 探针是单时刻快照」的既有声明一致）。板序、板名、分钟数、
   `truncated` 全部与前一轮逐字相同。

live 实际产出（现网 4 块到期板截 3，`truncated.top_boards=true` 如实透出）：

```
CS 61B            | 8 分钟 | 2 个节点到期（其中 1 张新卡） · 最早的已逾期 21 天 · 最该考的已闲置 21 天 · 这块板从未被推荐过
特征值与特征向量  | 10 分钟 | 2 个节点到期（其中 2 张新卡） · 最该考的已闲置 38 天 · 这块板从未被推荐过
CS188 lecture 2   | 5 分钟 | 1 个节点到期（其中 1 张新卡） · 最该考的从未考察 · 这块板从未被推荐过
```

### 裁判 3：grep 门 + 禁改门

```
$ grep -n 'why_this_board\|estimated_minutes\|rank_manifest' scripts/daily_review_pick.py
→ 三键均命中（开工基线 0 命中）
$ git log --format= --name-only $(git merge-base HEAD worktree-feature-obsidian-hybrid-dev)..HEAD \
    -- scripts/daily_review_run.py scripts/send_bark.py canvas-vault/.claude/scripts/decay_beta.py \
    canvas-vault/.claude/scripts/fsrs_bridge.py | sort -u
→ 空（禁改文件零触碰）
```

### HEAD 基线排序金样（卡文⑥：本卡只加解释不改序）

```
$ git show 9af18b27:scripts/daily_review_pick.py > /tmp 副本, 对同一 live vault 同 --now 各跑一次:
HEAD 板序: ['CS 61B', '特征值与特征向量', 'CS188 lecture 2']
✅ 板序逐字相同; top_boards 旧七字段 / upcoming / boards / buckets / due_nodes 全部逐字相同
（同款门已固化为常态测试 test_g36b_top_boards_order_matches_head_baseline，走真实 subprocess CLI 链路）
```

### 变异验证（8 条串行，MEMORY 铁律；还原逐字节一致，还原后 130 全绿）

| # | 变异 | 指定门（必须红） | 结果 |
|---|---|---|---|
| M1 | 解耦 factors（why 不再由 factors 复算） | `test_g36b_why_this_board_recomputes_from_factors` + 金样 | ✅ 全红 |
| M2 | sha 不随 decay 系数变（摘 decay 常量出摘要） | `test_g36b_sha_changes_for_every_single_coefficient` | ✅ 红 |
| M3 | 渲染层自算分钟（UI 再算） | `test_g36b_page_renders_explain_row_and_escapes_hostile` | ✅ 红 |
| M4 | 排序倒序（改序） | `test_g36b_top_boards_order_matches_head_baseline` + tiebreak 既有门 | ✅ 全红 |
| M5 | 截断放松（[:3]→[:99]） | `test_g36b_truncated_flags` + 排序金样 len==3 断言 | ✅ 全红 |
| M6 | 消费端门禁失明（分钟不验形） | `test_g36b_garbage_explain_fields_degrade_corrupt_not_ok` | ✅ 红 |
| M7 | `_tie` 派生回退成硬编码（round-1 HIGH 整改回退） | `test_g36b_tie_keys_are_single_source` | ✅ 红 |
| M8 | 渲染原子对回退（why 单边即渲染） | `test_g36b_one_sided_explain_fields_render_nothing` | ✅ 红（修门后，见下） |

> M8 首跑暴露一道**门缺陷**（正是 MEMORY `reference_gate_design_pitfalls` 的活案例）：
> 原门只断言「解释行字样不在页面里」，而 M8 变异下单边渲染抛 TypeError 被全局中间件
> 兜成 500 错误页——错误页恰好不含该字样，断言空转通过。修法：补 200 状态断言
> （单边缺省的正确行为是「200 且整块不出现」，500 本身就该红），修后 M8 变红。

**R1 复跑（2026-09-02，重建脚本独立跑，未沿用上一轮 scratchpad）**：8/8 各杀其指定门，
还原后两个目标文件均**逐字节一致**。脚本按 MEMORY 铁律加了三道防假绿：

- **阶段 0 前置**：先确认 8 道指定门在**未变异**代码下全绿 —— 否则「红」无法归因于变异
  （`reference_gate_design_pitfalls`：不先证绿，红了也不知道是谁造成的）。8/8 全绿通过。
- **锚点唯一性断言**：`old` 在源码中必须恰好命中 1 次，否则判 `INVALID` 而非静默跳过
  （死变异伪装成通过）。8 条全部命中 1 次。
- **`rc=5` 判 INVALID**：pytest 未收集到测试的退出码不算「红」
  （`reference_mutation_script_catches_dead_gates`）。本轮无 rc=5。

| # | 变异 | 指定门 | R1 结果 |
|---|---|---|---|
| M1 | 解耦 factors（why 不再由落盘 factors 复算） | `…why_this_board_recomputes_from_factors` | ✅ 红 rc=1 |
| M2 | decay 常量退出摘要（sha 不随系数变） | `…sha_changes_for_every_single_coefficient` | ✅ 红 rc=1 |
| M3 | 渲染层自算分钟（UI 再算） | `…page_renders_explain_row_and_escapes_hostile` | ✅ 红 rc=1 |
| M4 | 排序倒序 | `…top_boards_order_matches_head_baseline` | ✅ 红 rc=1 |
| M5 | 截断放松 `[:TOP_BOARDS_LIMIT]`→`[:99]` | `…truncated_flags` | ✅ 红 rc=1 |
| M6 | 消费端门禁失明（分钟不验形） | `…garbage_explain_fields_degrade_corrupt_not_ok` | ✅ 红 rc=1 |
| M7 | `_tie` 派生回退成硬编码 | `…tie_keys_are_single_source` | ✅ 红 rc=1 |
| M8 | 渲染原子对回退（单边即渲染） | `…one_sided_explain_fields_render_nothing` | ✅ 红 rc=1 |

还原完整性：`daily_review_pick.py` 与 `review_overview.py` 变异前后 sha256 逐字节一致。

### 格式门（先查 HEAD 基线再处置，零绕过）

- `review_overview.py`：HEAD rc=0 = 现在 rc=0（本次改动未引入漂移）。
- 两个测试文件：HEAD rc=0、改后 rc=1 → 漂移是本次引入 → 已正式 `ruff format`（G3-6a 先例）。
- `scripts/daily_review_pick.py`：存量漂移（HEAD --check 即红），按 G3-6a 先例不动。
- `ruff check` 三个 backend 文件全部 0 告警。

### 新增门的「证明什么 / 不证明什么」清单

| 门 | 证明 | 不证明 |
|---|---|---|
| `test_g36b_why_this_board_recomputes_from_factors` | 解释与数字单通路（factors 代回逐字复现） | factors 本身提取正确（由同源门与 rollup 对账门承担） |
| `test_g36b_why_this_board_char_whitelist_holds` | 句子无白名单外字符、板/节点名不进句 | md/HTML 侧对 board 名的转义（存量面，见「未证明什么」） |
| `test_g36b_factors_three_way_split…` / `…share_source…` | factors 与 rollup/行字段同源、三分完备 | scan_nodes 上游解析正确（既有套件承担） |
| `test_g36b_template_covers_every_branch` | 模板 6 组分支逐条锁定（含「没有 vs 算不出」区分） | 组合数穷举（分支组合非穷举，是分支级锁定） |
| `test_g36b_sha_changes_for_every_single_coefficient` | 任一系数变 → sha 必变（含常量缺失） | sha 的密码学强度（非安全门，是一致性指纹） |
| `test_g36b_sha_digests_effective_values_not_file_bytes` | 摘的是生效值不是文件字节（双向） | manifest 文件本身不被运行时改写（它只被读） |
| `test_g36b_recorded_*_matches_*` | 登记快照与代码/模块实际一致 | 未来 drift 告警的呈现方式（stderr 一行） |
| `test_g36b_authoritative_minutes_actually_take_effect` | 改 manifest 分钟常量真的生效 | 用户改出合理数值（值本身待你裁决） |
| `test_g36b_missing_or_corrupt_manifest_degrades_honestly` / `…usable_payload` | 缺失/损坏 → version=None + stderr 点名 + 默认值继续 | runner 对 stderr 的处置（stderr 只进日志，不影响退出码） |
| `test_g36b_recorded_drift_warns_but_actual_value_wins` | 登记改了不出声改行为 | 漂移告警被日志系统吞掉的可能（进程_stderr 直写） |
| `test_g36b_unassigned_nodes_never_enter_any_board_surface` | 无归属节点不进任何板面、点名在位 | 用户「补 source_board」后的行为（另卡） |
| `test_g36b_yaml_array_source_board_lands_unassigned` / `…comma_multi_board…` | 两种多板写法的实测现状锁定 | 该写法是「正确」的（现状登记，风险见「未证明什么」） |
| `test_g36b_same_name_boards_from_different_paths_merge` | 同名板合并为一块板 | 合并是用户想要的（裁定⑥登记，可推翻） |
| `test_g36b_truncated_flags` | 截断布尔三态真实 | 截断上限值合理（既有 3，本卡不改） |
| `test_g36b_no_board_appears_in_both_ranked_and_upcoming` | ranked/upcoming 板级互斥、无重复 | 未来板级语义变更仍成立 |
| `test_g36b_golden_new_fields_frozen` | 本卡新增字段值+键序逐字冻结 | 旧字段冻结（由 D1/G3-6a 两个累积金样分工） |
| `test_g36b_top_boards_order_matches_head_baseline` | 真实 CLI 链路下排序与基线逐字相同 | 基线 SHA 永远可达（不可达时 skip 并登记） |
| `test_g36b_tie_keys_are_single_source`（round-1 H1 整改门） | 因子序常量同时驱动排序与指纹——交换位置序与 sha 同变 | 取值绑定的字面代码（由实现校验和兜底） |
| `test_g36b_tie_precision_is_versioned`（round-2 H2） | 取整精度登记进指纹，改精度 sha 必变 | 精度之外的字面规则（同上） |
| `test_g36b_tie_removing_min_last_level_flips_order` / `…pick_level_decides`（round-2 M6） | min_last 级与 pick 级各自真实承重（删除后序翻转） | 全部因子组合空间（每级独立 fixture 是可达的最全覆盖） |
| `test_g36b_tie_keys_unique_and_anchored`（round-2 L1） | 因子键无重复、board 恒末位 | 运行时动态改常量（常量是源码，改动即变实现指纹） |
| `test_g36b_implementation_sha_is_registered_and_self_consistent`（round-2 H2） | 实现校验和在场/与源文件自洽/内容变必变 | .pyc 字节码篡改（已声明边界，见「未证明什么」④） |
| `test_g36b_parent_section_missing_warns_not_silent`（round-2 M5） | authoritative 三层缺失/null/错型全部点名 | stderr 在下游日志系统的留存策略 |
| 4 条 overview 门（carry/render/缺省/垃圾） | 消费链路、转义、缺字段不出现、垃圾 corrupt | 页面在真实浏览器的像素级观感（属你 UAT） |

## 👤 你来验（4-B，产品使用体验 — 2 步，2 分钟内全在浏览器/Obsidian 里完成）

### 第 0 步：First 5 seconds

打开复习总览页。跟昨天比：**页面没有变样**（本卡不改布局、不改颜色、不加按钮）。

### 第 1 步：每块推荐板多一句「为什么」和预计分钟

看任意一块有到期节点的白板：数据行下面多了一行灰色小字，以「为什么是这块板」开头，说清几个节点到期、最早逾期几天、最该考的闲置多久、这块板多久没推荐过，末尾有「预计 N 分钟」。**检查点**：这句话里的数字你能否看懂、是否跟板的实际情况对得上（比如它说逾期 21 天，你去板里看最早的到期节点是不是确实二十来天前就该复习了）。

### 第 2 步：今日复习.md 里也有

在 Obsidian 打开 `outputs/今日复习.md`：表格下面多一段「## 为什么是这几块板」，逐板列出同样的解释加预计分钟。**检查点**：手机上收到的推送 md 若已更新，同段也应出现。

### 边界（如果我做错会怎样）

旧投影文件（没重新生成过的库）不会显示这行字——不伪造、不显示假零。

### 主观打分（Felt-sense）

- 这句「为什么」读起来像人话吗？还是像机器拼的？（1-5）
- 「预计分钟」符合你对实际复习时长的感觉吗？（1-5，偏低/偏高都请写下来——这直接决定你要不要改 ④ 的常量）

## 待你裁决（①-⑦ 均为默认执行，非已批；⑧⑨ 为 R1 轮新增）

| # | 事项 | 本卡默认 | 请裁决 |
|---|---|---|---|
| ① | suspended 第五桶 | 不做（归 G6-6 snooze），沿 G3-6a 五桶 | 认可归属？ |
| ② | due_nodes 行结构化 idle_days | 加（G3-6a 移交 #2 按「加」执行，行尾追加 None=从未考察） | 认可？ |
| ③ | manifest 落点与形态 | `scripts/review_rank_manifest.json` v1；authoritative（改了真生效：分钟常量）/ recorded（登记快照：因子序/上限/decay 六常量）两节分离；payload 只透 `{version, sha256}` | 认可「权威 vs 登记」边界？ |
| **④** | **estimated_minutes 常量** | **到期节点 3 分钟/张、新卡 5 分钟/张 = 建议默认，仍待你校准（非已批）**。改法：编辑 manifest 的 `authoritative.estimated_minutes`，下一轮生成即生效（R1 独立实测确认「改了真生效」：version=9 / minutes={11,13}）。⚠ **R1 明确：本卡至今未做真实跨日校准** —— 3/5 这两个数从未与「你实际复习一张卡花了几分钟」对过账，没有计时数据、没有跨日样本，它只是量级占位 | **按你的真实节奏给两个数**（给不出也没关系，默认值会一直用下去，但总览页的「预计 N 分钟」就一直只是量级参考） |
| ⑤ | 上限 | 只登记+透出 truncated 布尔，截断行为零改动（仍 [:3]） | 认可？ |
| ⑥ | 金样锁 | top_boards 排序与 9af18b27 逐字相同（改序另立卡） | 认可？ |
| ⑦ | 一节点多板 | 不支持不发明。实测：YAML 数组写法→视同无归属进 unassigned 点名；逗号串写法→归到最后一个路径段（风险登记「未证明什么」） | 认可「不发明多板语义」？ |
| **⑨** | **卡文裁判 §5-2 与实证冲突（R1 round-2 Codex MEDIUM 提出，需你裁决）** | 卡文 §5-2 写「**源码改动必须使指纹变化**」。实证表明这句话按字面**做不到**：`decay_beta.py` 也是源码，改它的 `pick_score` 函数体（六常量不动）能让板序翻转而指纹恒定——而该文件是卡文 §3 **明令禁改**的，本卡无法把它纳入指纹。两个出路：**A) 把裁判限定为「`daily_review_pick.py` 字节或 `effective_rank_config` 明列的生效值改动必须使指纹变化」**（= 现在代码与文档的实际口径）；**B) 给显式 waiver**，承认该条在本卡范围内不可达并留给 CARD-G6-1b。R1 已按 A 的口径统一了全部源码/测试/验收单措辞，但**卡文本体是只读权威，未改** | **选 A 或 B**（建议 A：它描述的就是实际做到的事；B 会让卡文留一条永远红的裁判） |
| **⑧** | **终裁状态（R1 更新）** | 第八批 round-3 报告被内容过滤器两次拦截 → 无正式裁定。R1 的处置：① 用独立探针把 round-2 五项整改**自己重测**（17/17 PASS，不依赖被拦报告的残片）；② 自查又发现两处并整改（R1-F1 声明过宽 / R1-F2 计数陈旧）；③ 重跑 Codex 取非空终裁 —— **round-1 FAIL 1H/3M/2L → 全整改 → round-2 FAIL 0B/**0H**/5M/3L（HIGH 清零）→ 全整改 → round-3 见「R1 轮 Codex 审查」节末**。残余面（.pyc 字节码篡改）已作为**书面排除项**写进源码 docstring 与威胁模型，不再只是 UAT 里的一句话 | **待你裁决**：合并与否以 R1 轮 Codex 终裁为准；若终裁仍不可得，按卡文「到顶不合并」处理 |

## 🚦 验收结果

- 裁判 1/2/3 + 禁改门 + 金样 + 变异 8 条：全过（见 4-A）。
- Codex 对抗审查：round-1/2 FAIL → 全部整改并经 round-2/3 验证；round-3 无正式终裁（工具侧拦截），按卡文**默认不合并**，改判见「待你裁决」⑧。

## Codex 对抗审查

### Round-1（gpt-5.6-sol / ultra，2026-09-01）：FAIL — 1 HIGH + 4 MEDIUM，全部成立，全部整改

| # | 级别 | 发现 | 整改 |
|---|---|---|---|
| H1 | HIGH | 排序因子序是双真相源：`RANKING_FACTOR_ORDER` 常量与 `_tie` 字面元组互不相干，内存交换 `_tie` 因子 → 板序变了 sha 不变、漂移告警不响（实证复现） | **构造性修复**：新常量 `TIE_FACTOR_KEYS`，`_tie` 排序键改为由它逐键派生，sha 摘同一常量——两份表达各自漂移的形态被消灭。新门 `test_g36b_tie_keys_are_single_source`（交换因子位 → 板序翻转 + sha 同变）；变异 M7 锁回退 |
| M1 | MEDIUM | 排序金样 fixture 只覆盖 blr+board 两级，却声称「任何排序变化都会翻车」 | 补 `test_g36b_tie_pick_level_decides`（pick 级）+ `test_g36b_tie_removing_min_last_level_flips_order`（删除第三因子序翻转，fixture 浮点配平）。数学边界如实声明：min_last 更老 ⟺ 板内存在更老节点 ⟺ pick 更低，故 min_last 级只在 pick 严格平局时可达——每级独立 fixture 是可达的最全覆盖 |
| M2 | MEDIUM | blr 记录晚于今天被 `max(0,…)` 夹成 0 → 解释说「今天已推荐过」（虚构） | 不再夹负；模板新分支「上次推荐日期晚于今天」；新门锁定 gap=-2 原样上抛 |
| M3 | MEDIUM | 消费端 why/分钟独立放行，单边在场仍渲染解释行（违反「缺字段整块不出现」） | 渲染改原子对（双在场才渲染）；新门覆盖两个单边方向（含 200 状态断言，见变异 M8 的门缺陷记录） |
| M4 | MEDIUM | manifest 只写一半分钟常量时缺键静默回落 | 缺键与非法统一点名「缺失或非法」；补半份配置断言 |

Round-1 备注（Codex 如实声明）：untracked 的 prompt/report/UAT 是卡文收尾节明令产物；
live 14 节点单值取值分布由开工 grep 实测（sort|uniq -c）。

### Round-2（gpt-5.6-sol / ultra）：FAIL — 0 BLOCKER / 1 HIGH / 2 MEDIUM / 2 LOW，全部成立，全部整改

| # | 级别 | 发现 | 整改 |
|---|---|---|---|
| H2 | HIGH | 单源只统一了**因子名称序**，没统一**可执行取值规则**：`round(8)→round(7)` 精度收紧 → 近邻 pick 变同分 → 板序翻转而 sha 不变（实证 `879279ff…` 恒定）；取值绑定交换同理 | **双层修复**：a) 精度数据化——新常量 `TIE_PICK_ROUND_DIGITS=8` 进指纹（改精度 → 排序与 sha 同变）；b) **实现校验和兜底**——`effective_rank_config` 新增 `implementation_sha256 = sha256(pick.py 自身字节)`，取值绑定这类无法全部数据化的字面代码，对**源文件**的任何改动都会反映到 sha（粒度从「系数」变「实现+系数」属预期内的保守取舍：宁可指纹变多，不可规则变更漏网）。⚠ R1 收窄：该保证是**单向**的（规则变⟹sha变；反之不成立），且**不覆盖运行时 .pyc**——精确边界见 `_implementation_sha` docstring 三条声明 |
| M5 | MEDIUM | authoritative 父节缺失（`{}`/无节/`null`）仍静默回落 | 三层（节/子节/叶键）缺失/null/形状不符全部点名；门覆盖三种形状 |
| M6 | MEDIUM | pick 级金样不承重（低 pick 恰在字典序早的板，删首因子序不变——门空转） | 低 pick 移到字典序更晚的板 + 断言删首因子后翻转 |
| L1 | LOW | 因子键无唯一性校验（重复键 = sha 变而排序不变） | 门锁定：键唯一 + board 恒末位 |
| L2 | LOW | 验收单两处残留旧计数 121 | 统一为实测数 |

Round-2 同时验证通过：未来推荐日诚实文案、原子渲染、min_last fixture 真实承重、半份叶级配置点名、126 回归、禁改门、live 14/14 单值 wikilink 复核。

### Round-3（gpt-5.6-sol / ultra，同轮跑两次）：⛔ **无正式终裁报告**（内容过滤器两次拦截 final message，详见下）

Round-3 两次运行均在完成全部验证步骤后、输出最终报告时被 Codex 侧内容过滤器拦截
（触发源是**被审内容本身**——pick.py 的自 hash 实现指纹语境稳定触发，与提示词措辞无关，
换措辞重试无效，与 MEMORY `reference_codex_exec_gotchas` 记录一致）。从 stderr 抢救出的验证记录：

- **五步验证全部完成**（两次运行一致）：✓ 锁定基线与边界 ✓ 逐条复核 round-2 五项整改及测试门
  ✓ 构造「排序规则变化而 rank SHA 不变」的残余面 ✓ 运行并核对 pick 69 + overview 61 回归
  ✓ 交叉验证证据（终轮裁决已形成但正文被拦，无法抢救）
- **抢救出的一个真实残余面（Codex 实测复现）**：篡改 `__pycache__` 内的 .pyc 字节码并伪造
  mtime → Python 执行被改字节码 → 板序翻转（`B板,A板 → A板,B板`）而 `implementation_sha256`
  （摘 .py 源文件字节）不变。**技术评估（Claude，供你裁决参考）**：该面需要本地文件系统写权限
  + 主动伪造时间戳，属「主动篡改运行时」威胁模型；本卡的版本化目标是防**善意配置/代码演进**
  的无痕漂移（改 .py 必变 sha 已完备），不是对抗主动攻击者的运行时完整性防护（那是另一套
  机制的地盘）。⚠ **R1 轮收回一句过头话**：此前写「launchd 生产链不存在自然触发路径」，但这一条**本卡从未评估过** —— 实际链路由 `scripts/daily-review-push.sh` 启动、`daily_review_run.py` 普通 `import` picker，启动链也没有钉死无缓存条件。正确表述是：**本卡未评估该路径，按威胁模型排除**，不是「已证明不存在」。
- 当前回归 **130 passed**（pick 69 + overview 61）；live 探针 sha `b3ff4b99…`、板序与 HEAD 逐字相同。

> ⚠️ **显著声明**：round-3 没有产出正式 PASS/FAIL 终裁 → 按卡文「到顶未清零」处理：
> 本卡**不合并**，是否接受下述证据链改判，见「待你裁决」⑧。

### R1 独立复核（CARD-G3-6b-R1，2026-09-02）：不抄自述，逐条重测

卡文 (b) 要求复核 round-2 五项整改是否**真的**闭合。R1 写了一份独立探针，
自己构造输入、自己读结果、自己判定，**不引用上一轮的结论**。结果 **22/22 PASS**
（round-1 17 项 → round-2 补强至 20 → round-3 再补 2，逐轮按 Codex MEDIUM 加固）。

> **证据绑定的字节状态（两份，不混为一谈）** —— 探针跑了两次，每份输出各自归档：
> - **A** `_bmad-output/审查/evidence-g36b-r1/recheck-A-on-c2d2e590-bytes.txt`：对
>   `c2d2e590` **原样字节**（`pick.py` sha `ad1a38a5…`）跑 —— 这才是卡文 (b) 指定的
>   复核对象，下表数字全部出自这一份。**22/22 PASS**。
> - **B** `…/recheck-B-on-r1-narrowed-bytes.txt`：对 **R1 收窄后字节**
>   （round-3 后 sha `1f5eb882…`）复跑，确认历次收窄没有破坏任何被复核的性质。
>   **22/22 PASS**。
>
> 项数 17→20→22 的来历：round-2 按 Codex MEDIUM 补三条（impl_sha 是否真的接入最终
> rank SHA / `build_payload` 生产入口的分钟是否真按 manifest 算 / recorded 漂移时
> **行为**是否以实际为准）；round-3 再补两条（落盘 rank sha 是否与**实际生效的那组
> 分钟**同源 / 仅 recorded 不同的两份 manifest 走四板入口是否产出逐字相同的 payload）。
>
> 分两份是刻意的：R1-F2 批评的就是「证据数字与它绑定的对象对不上」，若把改动前后的
> 数字混在一张表里，等于自己复刻同一个毛病。探针接受路径参数正是为此。



| 复核项 | round-2 记录的原漏网 | R1 独立实测 |
|---|---|---|
| H2-a 精度数据化 | `round(8)→round(7)` 板序翻转而 sha 恒 `879279ff…` | 近邻 pick 差 1e-8 时：序 `[B,A]`→`[A,B]` **且** sha `b3ff4b99…`→`9ca6a0f8…` — 排序与指纹**同变** ✅ |
| H2-b 取值绑定 | 交换 blr/min-last 绑定 → 规则变而 sha 不变 | 副本交换绑定：序 `[B,A]`→`[A,B]`，`implementation_sha256` `ad1a38a5…`→`7f534235…` 同变 ✅ |
| M5 authoritative 三层 | `{"version":1}` / `{...,"authoritative":{}}` / `estimated_minutes:null` 均静默且 stderr 空 | **六种**形状（父节缺失/null、子节 null/错型 list、空 object、半份叶键）全部点名回落，stderr 均非空 ✅ |
| M6 金样承重 | 低 pick 恰在字典序早的板 → 删首因子序不变（门空转） | 低 pick 在字典序**更晚**的 B 板：默认 `[B,A]`，删 `priority_pick` 后 `[A,B]` 翻转 ✅ |
| L1 因子唯一性 | 追加重复末级 `board` → sha 变而排序不变 | 实测方向确认：序不变、sha 变 = **误报方向**（指纹过度敏感），非漏网方向；安全性质「规则变⟹sha变」不受影响 ✅ |

附带复核（非 round-2 条目，R1 自行加测）：`authoritative` 分钟常量改了**真生效**
（version=9 / minutes={11,13}）；`recorded` 与实际不符时逐项出声告警且以实际为准。

#### R1 自己发现并整改的两处（不是抄来的）

| # | 级别 | 发现 | 整改 |
|---|---|---|---|
| **R1-F1** | 声明面 > 证明面 | `_implementation_sha` docstring 写「任何排序规则改动 **必然** 变 sha」、`effective_rank_config` 与测试 docstring 写「兜住…的**整类**攻击」——而 round-3 已实测反例（改 `.pyc` 可让排序变而该 sha 不变）。UAT 侧（第 4 条）早已声明了这个边界，**源码侧没跟上**，同一事实两套说法，后人照抄源码就会把过宽声明复制到下一张卡 | 三处 docstring 收窄为**源文件字节层** + 显式三条声明：①摘的是 .py 字节（改注释也必变）②**单向**保证（规则变⟹sha变，逆命题已刻意放弃）③**不覆盖运行时 .pyc**、不宣称运行时完整性。测试 docstring 另加一句「断言措辞不得回退成『任何改动必变』」防回潮。UAT H2 整改栏同步收窄 |
| **R1-F2** | 证据内部不一致（L2 同型复发） | 「复现命令」段仍写 `# 预期 126 passed` 与 `# 预期 6 条全红`，而正文是 130 与 8 条。round-2 的 L2 修了正文两处，**漏了复现命令段** | 三处当前预期值统一为实测值（130 / 8 条）。`121 → 126 → 130` 轨迹与 round-2 报告里的「126 回归」属**历史 exact evidence，原样保留不改**（纪律 §四.2：不得篡改历史证据制造假绿） |

#### (c) pyc 面：明确写进威胁模型的「排除项」

round-3 抢救出的残余面（篡改 `__pycache__/*.pyc` 并伪造 mtime 使 Python 取旧字节码 →
排序翻转而 `implementation_sha256` 不变）在 R1 **确认为已知且明确排除**，处置是**书面声明**
而非增加防护：

- **本卡指纹的目标**是「善意的配置/代码演进不产生无痕漂移」，但**目标并未完备达成**（R1 轮 Codex HIGH 实测，已复现）：指纹摘的只是 `daily_review_pick.py` 字节 + `effective_rank_config` 明列的生效值。排序真正的 pick 值由 vault 内 `decay_beta.py` 的 `effective()`/`pick_score()` **函数体**算出，而只有它的**六个常量**进了指纹，**函数体没有** —— 只改 `pick_score` 一个符号（六常量逐字不动），板序 `[B板,A板]`→`[A板,B板]` 翻转而 rank sha 恒为 `503fd4b6…`，全程纯源码演进、无 `.pyc` 参与。`decay_beta.py` 归 CARD-G6-1b、本卡禁改，故 R1 只**如实登记**这个缺口、不扩指纹。复现脚本与输出：`_bmad-output/审查/evidence-g36b-r1/g36b_r1_verify_high_decay.py`。
- **pyc 面属另一套机制的地盘**（主动篡改运行时的完整性防护），需要本地文件系统写权限 +
  主动伪造时间戳。**本卡未评估** launchd 生产链上是否存在「改 .pyc 不改 .py」的
  触发路径（R1 round-2 Codex LOW：上一轮只收回了两处同义表述，这一处因措辞不同
  漏网 —— 「改措辞后 grep 全文」要按语义找，不能只 grep 自己写过的那句），按威胁
  模型排除，不宣称它不存在。
- R1 的动作是把这条边界从「只在 UAT 里说」补齐到**源码 docstring 里也说**（见 R1-F1），
  并在此明确：**本卡不宣称运行时完整性**。要防这一面须另立卡。

#### (e) runner 门：结构性 BLOCKED（如实登记，未做）

卡文 (e) 要求「W4+W6 集成候选补跑 runner」。R1 实测前置**未满足**，本车道 session
无权也无路径完成：

```
$ git log -1 card/w4-safety-r2   →  d3fba4e0 test(bark): 关闭 reload/代理首跳/过宽承诺
                                     [CARD-TEST-bark-autostub-R1]   ← 已推进，不再是开工基线
$ git branch --list batch9/integration  →  空（**分支 ref**；手册 §一.4.C 用它建树）
$ git worktree list | grep batch9-integration  →  空（**worktree 目录名**，卡文 §0 写的是这个）
  两者是同一件事的两个名字：分支 ref = `batch9/integration`，目录 = `batch9-integration`；均不存在
```

> **R1 round-2 刷新（Codex LOW 指出锚点已漂移，属实）**：W4-① Bark-R1 已在推进
> （2026-09-02 实测 HEAD `d3fba4e0`，早先记的 `2cacbb0c` 已过期）。所以「W4 尚无 commit」
> 这个**理由失效**，但 **结论不变** —— runner 门依然 BLOCKED，因为解锁要的是「整条 W4
> 清零 + 集成树存在」，而 `batch9/integration` 分支与 `batch9-integration` worktree
> **均仍不存在**，且 W4-② lifespan-R1 按手册须等 W4-① 终审 B/H=0 后才能开。

- 卡文 §0：runner 门「**只**在整条 W4 安全车道清零后，于 `batch9-integration` 的 W4+W6
  candidate 上补跑」，且「**禁止**把 W4 整枝合进旧 W6 车道」。
- 手册 §一.2：集成树由**主 session** 从 CODE_BASE 新建，任何实际 merge 仍等用户授权。

**解锁前置**（三者 AND）：① W4-① Bark-R1 与 W4-② lifespan-R1 各自取得非空终审 B/H=0；
② 主 session 从 `928010b9` 建 `batch9-integration` 并冻结 `W4_V5_CHECKPOINT`；
③ 由该 checkpoint 建 W4+W6 一次性 candidate，在其中跑 `test_daily_review_run.py`
（KEY_FILE/VAULT/外发全指 tmp，要求无真实 socket/osascript）。

在此之前，runner 消费面零变化**只**由「diff 不含 `daily_review_run.py`」+ 禁改门证明，
**未**由 runner 自身测试回归证明 —— 见「本卡未证明什么」第 8 条。

### R1 轮 Codex 审查（gpt-5.6-sol / ultra）

#### R1 round-1（绑定 `9e158d82`）：**FAIL** — 0 BLOCKER / 1 HIGH / 3 MEDIUM / 2 LOW，全部成立，全部整改

**先说最重要的一件事：这一轮拿到了非空正文（7594 bytes）与明确总裁决，没有命中内容过滤器。**
第八批 round-3 两次被拦的真因由 R1 定位为**任务边界**而非措辞：那轮 prompt 写着
「探查是否存在『排序规则变了 sha 不变』的残余遗漏面」，等于主动请审查方构造绕过
完整性校验的 PoC，它照做了（`.pyc` + 伪造 mtime），输出随即被拦。同一 prompt 里还
写着「指纹始终诚实于真正执行的代码」——正是那个反例证伪的对象。R1 按卡文 §4(c)
把该面**书面排除**并写进 prompt，同时**明确请审查方评价「这个排除本身是否正当」**
（允许用文字论证，不需要 PoC）。结果：非空、有裁决，且它确实就该边界提了 LOW。

| # | 级别 | 发现 | 整改 |
|---|---|---|---|
| **H1** | HIGH | 「善意源码演进不会无痕漂移、目标完备」**仍然过宽**。排序的 pick 值由 vault 内 `decay_beta.py` 的 `effective()`/`pick_score()` **函数体**算出，指纹却只取它的**六个常量** + `pick.py` 字节，**不取函数体**。实测：只改 `pick_score` 一个符号（六常量逐字不动）→ 板序翻转、rank sha 恒定、stderr 空，**全程纯源码演进，无 `.pyc` 参与** | **R1 独立复现成立**（`g36b_r1_verify_high_decay.py`：六常量 `True` 相同、板序 `[B板,A板]`→`[A板,B板]`、sha 两边 `503fd4b6…`）。整改取 Codex 两个建议中的**前者**（后者=把 decay_beta 字节纳入摘要 = 改 sha 语义 = 扩功能，与 R1「复核轮不扩功能」定位冲突）：`_implementation_sha` docstring 再收窄一层为「**本文件字节 + 明列生效值**」，并新增第 2 条**如实登记该缺口**（decay_beta.py 归 CARD-G6-1b、本卡禁改）。UAT 侧同步 |
| M1 | MEDIUM | 17 项探针存在**实证假绿**：authoritative 只断言 stderr 非空（不验回落值与告警内容）/ 取值绑定只比裸 `_implementation_sha()`（未证明它接入最终 rank SHA）/「分钟真生效」只验 loader 返回（没走 `build_payload`）/「recorded 以实际为准」只验告警文字（没验行为）。Codex 在副本上同时破坏三处，探针仍报 `17/17 PASS` | 四处全改：精确回落值 + 告警点名词断言；比较**最终 rank SHA** 并核对 `cfg.implementation_sha256` 与裸值一致；走 `build_payload` 生产入口断言落盘分钟等于 `due_new×13+其余×11`；recorded 漂移断言**生效值**未被登记值污染。项数 17→20。**并补了负控**（`g36b_r1_negctl_probe.py`）：复现 Codex 的三重破坏，**逐项单独 + 三处叠加**共四种形态，全部变红 |
| M2 | MEDIUM | R1-F1 **仍漏多处**过宽声明：「增删因子必定排序与 SHA 同变」「排序逻辑任何一处变化都会在此翻车」「反之亦然」；且精度门**自己从头到尾没调用过排序** | 三处 docstring 全改为「本 fixture 上的单向观察」，显式否认逆命题与全空间覆盖。精度门**不只改措辞，补上真实排序断言**（近邻 pick 差 1e-8：8 位可分 `[B,A]`、7 位同分退 blr 级 `[A,B]`）——并**验证该新断言承重**：变异掉精度常量接入点后该门变红，还原逐字节一致 |
| M3 | MEDIUM | 变异脚本三道防假绿仅部分成立：把 `rc=2/3/4` 也算「红」（只有 `rc=1` 能证明断言失败）、丢弃 stderr、`-k` 子串匹配、`finally` ≠ EXIT trap | `rc=1` 才判红，`2/3/4/5` 一律 INVALID；改用精确 nodeid `file::testname`；保留 stderr 尾部；加 SIGINT/SIGTERM 还原 handler，并**如实声明它不等价于 EXIT trap**（SIGKILL 仍会留字节，真正判据是还原后的逐字节比对）。Codex 同时确认「本次 8 条均 rc=1，故本次 8/8 有效」 |
| L1 | LOW | 排除运行时完整性可以接受，但「launchd 不存在自然触发路径」**从未被证明**（链路经 `daily-review-push.sh` → `daily_review_run.py` 普通 import，启动链未钉死无缓存条件） | 两处措辞收回，改为「**本卡未评估该路径，按威胁模型排除**」，不再断言不存在 |
| L2 | LOW | 卡文写 `batch9-integration`、UAT 查 `batch9/integration`，未说明哪个是目录哪个是分支 | 补齐两条检查并注明：分支 ref = `batch9/integration`，worktree 目录 = `batch9-integration`，两者均不存在 |

Codex R1 round-1 同时**核实为真**：HEAD/分支/目标提交准确、tracked diff 为零；重新实跑
`130 collected` / `130 passed`（pick 69 + overview 61，无 skip/xfail）；A/B 两份源 SHA 与
对应字节状态一致；隔离克隆中阶段 0 八门全绿、M1–M8 全部 rc=1、恢复后逐字节一致；
**runner 登记诚实**（「UAT 明确写了『根本没跑』，没有冒充执行」）；`126/6 → 130/8`
已修正而历史 `121→126→130` 保留合理；3/5 分钟明确登记为未跨日校准的建议默认。

> 审查方自报其变异 harness 曾因路径重绑失误短暂触及一个 tracked 目标、随后由 `finally`
> 恢复。**R1 未采信自报，独立复核**：`git status --porcelain` 仅三个审查侧车文件（prompt/
> report/stderr），`git diff HEAD` 为空，三个关键文件 sha 与提交态逐字一致。

#### R1 round-2（绑定 `66346bce`）：**FAIL** — 0 BLOCKER / **0 HIGH** / 5 MEDIUM / 3 LOW

**HIGH 清零**：「收窄声明、不扩指纹」的取舍被判**可接受**。5M/3L 全部成立、全部整改。
其中两条是**实证的假绿**——Codex 各构造一个单变异，让 22 项探针与 130 项正式测试
**同时全绿**，而生产入口的行为已经错了：

| # | 级别 | 发现 | 整改 |
|---|---|---|---|
| M1 | MEDIUM | 探针没绑「实际分钟」与「**同一组分钟**生成的最终 rank SHA」。把 `build_payload` 喂给摘要的 minutes 换成 `DEFAULT_MINUTES`、实际分钟仍用 11/13 → **20/20 与 130 全绿**，但真实入口产出 `estimated_minutes=24`（按 11/13），rank SHA 却是 3/5 那份的 —— 「这份指纹对应这份产出」的绑定断了 | 新增断言：独立复算「用 11/13 的 `effective_rank_config`」的 sha，要求 (a) **等于** payload 落盘的 rank sha、(b) **不等于** 用默认分钟复算的 sha。该变异已加入负控 |
| M2 | MEDIUM | 「recorded 以实际为准」仍只查不接收 `recorded` 的中间对象。让 `recorded.limits.top_boards` 真去控制截断 → **20/20 与 130 全绿**，四板入口一边打「以实际为准」的告警、一边输出 `top_boards=4`（代码常量是 3） | 新增断言：**仅 recorded 不同**的两份 manifest 各走一次**四板生产入口**，要求整份 payload 逐字相同、榜长精确为 3、ranked 总数为 4。该变异已加入负控 |
| M3 | MEDIUM | **负控自己是假的**：把任意非零退出都算「被抓」。空源码让探针 `AttributeError` 崩溃、rc=1，也被记成「✅ 被抓」。原有四次判定碰巧有效，但「不再假绿」这个**结论**无效 | 改三态判定（CAUGHT/MISSED/**INVALID**）：必须 (a) 探针跑完有 summary、(b) stderr 无 Traceback、(c) **指定的那条**断言出现在 FAIL 行里。加**验伪锚**（空源码必须判 INVALID，若判 CAUGHT 则负控本身失效）。结论收窄为「**这 6 种已知破坏**被抓」，并显式写明未枚举形态仍可能漏网 |
| M4 | MEDIUM | 收窄没做全：`pick.py:279` 注释仍称「交换/增删因子…排序与指纹同变」、`TIE_PICK_ROUND_DIGITS` 注释仍称「改此常量 → 排序与 sha 同变」、测试 docstring 开头仍绝对化；且 `_implementation_sha` 已从三条声明扩到四条，引用处仍写「三条」 | 三处注释/docstring 改为单向表述（「改它必变 sha；**排序变不变取决于数据**」），引用改「四条」。**卡文 §5-2 的冲突另列待裁决 ⑨**（见下） |
| M5 | MEDIUM | sha 归因与字节绑定混杂：把「新断言纳入」写成指纹变化的原因（**新断言在测试文件，根本不进实现摘要**）；HIGH 复现输出里是 `eb6b6710…`，UAT 却写 `503fd4b6…` | 改为**三元组表**（commit / pick.py sha / rank sha / 这一跳的原因），并写明归因纪律：`pick.py` 任何字节改动都会换 sha，读旧证据必须先看它头部记的源码 sha 属于哪一行 |
| L1 | LOW | 变异脚本在 clean clone 里阶段 0 `rc=4`（依赖**未跟踪**的 `backend/.env`）；红时不输出 tail；「rc=1 是唯一能证明断言失败的退出码」措辞过强 | 头部显式声明 `.env` 环境依赖与 clean clone 下的表现；**红时也归档 pytest tail**（用来确认失败的是预期那条断言）；措辞改为「rc=1 证明该 nodeid 失败，具体断言见 tail」 |
| L2 | LOW | 「launchd 生产链没有…自然触发路径」**仍残留一处**，与同文件另两处「已收回」自相矛盾 | 已收回。**教训记在该处**：上一轮 grep 的是自己写过的那句措辞，而这处用词不同所以漏网——「改措辞后 grep 全文」要按**语义**找 |
| L3 | LOW | W4 锚点已漂移：`card/w4-safety-r2` 不再是 `2cacbb0c` | 已刷新（2026-09-02 实测 `d3fba4e0`，比 Codex 报的 `6518e5af` 还新）。**结论不变**：runner 仍 BLOCKED，但理由从「W4 无 commit」换成「W4 未清零 + 集成树不存在」 |

Codex round-2 同时**核实为真**：目标 HEAD/分支准确、tracked 字节未漂移；`130 passed`；
探针确为 20/20；**新精度断言真实调用了 `rank_boards`**（8 位 `[B,A]` / 7 位 `[A,B]`，
硬编码掉精度接入点后精确门 `rc=1`）——**不是空转**；本轮未跑 runner、未读 live 节点、
未构造任何 `.pyc`/mtime/运行时验证代码。

#### R1 round-3 复跑（绑定本次提交）

- 裁判 1：**130 passed**。
- 独立探针：A（`c2d2e590` 原样字节 `ad1a38a5…`）**22/22**；B（当前字节 `1f5eb882…`）**22/22**。
- 负控：**6 种已知破坏各被其指定断言抓住**（含 Codex round-2 新提的两种），
  且**验伪锚生效**——空源码崩溃被正确判 `INVALID` 而非「被抓」。
- 变异：**8/8 各杀其指定门**（全 `rc=1`，精确 nodeid，红时归档 tail），还原逐字节一致。
- live 只读探针（05:31，避开推送档位 9–20 点）：前后 sha 逐字相同**零写入**，
  板序与 `truncated` 不变，rank sha `bc3aa142…`（归因见上方三元组表）。

## 本卡未证明什么（必填）

1. **分钟常量 3/5 是拍脑袋值**——没有实测「一张到期卡平均复习几分钟」。这正是 ④ 请你给数的原因；在你说出真实数字前，总览页的「预计分钟」只是量级参考。
2. **多板形态 b 的错归风险**：`source_board: "[[A]], [[B]]"`（无内嵌引号的单串双链）会静默归到最后一个路径段的板名，既不是 A 也不是 B。实测现网 0 例，但若将来 Obsidian 某插件这样写，节点会错归——修它要动 `_board_name` 归一规则、影响全部单值节点的板身份，超出本卡加性边界，未修。
3. **`render_md` 对板名/节点名的转义是存量面**（G3-6a 移交 #9）：本卡新增的「为什么是这几块板」段沿用同一未转义口径（板名与既有表格行同值同面），只转义新段会造成同文件两套规则。统一转义策略待另卡。
4. **指纹防的是配置/源码演进，不防运行时篡改**：`implementation_sha256` 摘 pick.py 源文件字节——改 .py 必变指纹；但 round-3 抢救记录实证：直接篡改 `__pycache__` 的 .pyc 字节码并伪造 mtime 可以让排序变而指纹不变。该面属主动攻击者场景，**本卡未评估其触发路径**（不再宣称「无自然触发路径」——R1 轮 Codex LOW 指出该断言从未被证明），按威胁模型排除，本卡不防（见「待你裁决」⑧）。
5. **sha 指纹不能用来区分「改了什么」**（R1 轮改标题：原标题「不覆盖 why 模板的中文文案」与正文自相矛盾——模板文案就写在 pick.py 里，改它当然会变指纹）：由于 implementation_sha256 摘本文件全部字节，**任何 pick.py 改动（含注释、含 why 模板文案）都会变指纹**，此条与 round-1 版声明相反且更严：指纹粒度是「实现+系数」，不能用它区分「改了什么」，只能证明「变了」。
6. **部署后的真实观感**：130 条测试 + 结构断言不等于像素级好看——375px 窄窗下解释行折行效果需要你按第 1 步亲眼确认。
7. **live 探针是单时刻快照**：2026-09-01 某时刻的数据形态（4 板截 3、句子内容）会随节点增删/复习推进而变，验收的是行为不是这批具体句子。
8. **runner 门至今未跑（R1 复核后仍 BLOCKED）**：本卡不跑 `test_daily_review_run.py`（卡文明令：W4① 合入前该套件会真发 Bark）。runner 消费面零变化只由「diff 不含 `daily_review_run.py`」+ 禁改门证明，**未**由 runner 自身测试回归证明。R1 实测前置仍未满足——`card/w4-safety-r2` HEAD 还停在开工基线 `2cacbb0c`，`batch9/integration` 分支不存在（解锁三前置见「(e) runner 门」节）。这不是「跑了没问题」，是**根本没跑**。
9. **指纹不覆盖 `decay_beta.py` 的函数体**（R1 轮 Codex HIGH，已实证复现）：排序真正
   用的 pick 值由 vault 内 `decay_beta.py` 的 `effective()`/`pick_score()` 函数体算出，
   指纹只摘了它的**六个常量**（改常量必变 sha + 有漂移告警），**函数体没进指纹** ——
   改函数体可让板序翻转而 `rank_manifest.sha256` 纹丝不动，**这条路径不需要任何
   `.pyc` 或运行时手段，就是普通的源码修改**。`decay_beta.py` 归 CARD-G6-1b、本卡
   禁改其本体，R1 只**登记**不扩指纹。所以「改了排序系数一定看得出来」这句话，
   准确说只对**本文件与明列的那几项生效值**成立。

10. **round-3 无正式终裁**（见 Codex 节显著声明）：「五项整改全部通过验证」的判断依据是抢救出的验证 checklist 而非 Codex 签名的 PASS 结论——证据强度低于 round-1/2 的正式报告。**R1 的改善与残余**：R1 用独立探针把这五项**自己重测了一遍**（round-1 17 项 → round-2 补强至 **20/20 PASS**，见「R1 独立复核」节），所以「整改成立」不再只依赖被拦截报告的残片；但**独立复核 ≠ 第三方终裁**——它证明的是「这些性质在 R1 实测下成立」，不能替代 Codex 签名的对抗性结论。**R1 轮已取得非空正式终裁**（round-1 FAIL 1H/3M/2L，全部成立全部整改；见「R1 轮 Codex 审查」节），这是本卡第一次拿到未被拦截的第三方结论。

## 📝 你的批注区

（留白）

## 复现命令（Claude 已跑完，此处只留给技术追溯）

```bash
# 1) 裁判套件
cd LANE/backend && caffeinate -i .venv/bin/pytest tests/regression/test_daily_review_pick.py \
  tests/unit/test_review_overview.py -q -p no:cacheprovider     # 预期 130 passed

# 2) live 只读探针 (避开 launchd 推送时刻; 必带 PYTHONDONTWRITEBYTECODE=1, 不带 --write)
shasum -a 256 /Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault/outputs/今日复习.{json,md}
cd LANE && PYTHONDONTWRITEBYTECODE=1 python3 scripts/daily_review_pick.py \
  --vault /Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault \
  --now 2026-09-01T23:30:00+08:00 | python3 -c "import sys,json; p=json.load(sys.stdin); \
  assert p['schema_version']==3; assert 'rank_manifest' in p; \
  assert all(b.get('why_this_board') for b in p['top_boards']); print('ok', p['rank_manifest'])"
shasum -a 256 …/今日复习.{json,md}   # 与前置逐字相同

# 3) 变异串行
python3 <scratchpad>/g36b_mutations.py   # 预期 8 条全红 + 还原逐字节一致
```
