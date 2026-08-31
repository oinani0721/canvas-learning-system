# UAT — CARD-G3-6b 板级 why_this_board 与系数版本化（rank_manifest）

> 批次 [BATCH-2026-09-01-第八批 / CARD-G3-6b] · 车道 card/w6-whyboard · 基线 9af18b27
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

> sha 演进轨迹（每一跳都对应一次真实的配置/实现变化，指纹如实反映）：
> `e3a6c062…`（round-1 版）→ `b0c77f5c…`（因子常量改名纳入）→ `b3ff4b99…`（实现校验和纳入，终版）。

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

### 变异验证（8 条串行，MEMORY 铁律；还原逐字节一致，还原后 126 全绿）

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

## 待你裁决（①-⑦ 均为默认执行，非已批）

| # | 事项 | 本卡默认 | 请裁决 |
|---|---|---|---|
| ① | suspended 第五桶 | 不做（归 G6-6 snooze），沿 G3-6a 五桶 | 认可归属？ |
| ② | due_nodes 行结构化 idle_days | 加（G3-6a 移交 #2 按「加」执行，行尾追加 None=从未考察） | 认可？ |
| ③ | manifest 落点与形态 | `scripts/review_rank_manifest.json` v1；authoritative（改了真生效：分钟常量）/ recorded（登记快照：因子序/上限/decay 六常量）两节分离；payload 只透 `{version, sha256}` | 认可「权威 vs 登记」边界？ |
| **④** | **estimated_minutes 常量** | **到期节点 3 分钟/张、新卡 5 分钟/张——拍脑袋值，卡文明示请用户改。改法：编辑 manifest 的 authoritative.estimated_minutes，下一轮生成即生效（有测试锁定改了真生效）** | **按你的真实节奏给两个数** |
| ⑤ | 上限 | 只登记+透出 truncated 布尔，截断行为零改动（仍 [:3]） | 认可？ |
| ⑥ | 金样锁 | top_boards 排序与 9af18b27 逐字相同（改序另立卡） | 认可？ |
| ⑦ | 一节点多板 | 不支持不发明。实测：YAML 数组写法→视同无归属进 unassigned 点名；逗号串写法→归到最后一个路径段（风险登记「未证明什么」） | 认可「不发明多板语义」？ |
| **⑧** | **round-3 终裁缺失（Codex 内容过滤器两次拦截报告，验证记录已抢救）** | 证据链：round-3 五步验证全 ✓ + 唯一残余面（.pyc 字节码篡改）属「主动篡改运行时」威胁模型、超出本卡「防配置漂移」范围。**两个选项**：A) 接受证据链 + 残余面登记为已声明边界 → 本卡可合并；B) 不接受 → 本卡留台账 §一 不合并，残余面另立卡（运行时完整性属新机制） | **选 A 或 B**（我的建议：A——残余面无自然触发路径，且拦截是审查工具侧故障而非审查结论） |

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
| H2 | HIGH | 单源只统一了**因子名称序**，没统一**可执行取值规则**：`round(8)→round(7)` 精度收紧 → 近邻 pick 变同分 → 板序翻转而 sha 不变（实证 `879279ff…` 恒定）；取值绑定交换同理 | **双层修复**：a) 精度数据化——新常量 `TIE_PICK_ROUND_DIGITS=8` 进指纹（改精度 → 排序与 sha 同变）；b) **实现校验和兜底**——`effective_rank_config` 新增 `implementation_sha256 = sha256(pick.py 自身字节)`，取值绑定这类无法全部数据化的字面代码，任何改动都会反映到 sha（粒度从「系数」变「实现+系数」属预期内的保守取舍：宁可指纹变多，不可规则变更漏网） |
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
  机制的地盘）。改 .pyc 不改 .py 的场景在 launchd 生产链不存在自然触发路径。
- 当前回归 **130 passed**（pick 69 + overview 61）；live 探针 sha `b3ff4b99…`、板序与 HEAD 逐字相同。

> ⚠️ **显著声明**：round-3 没有产出正式 PASS/FAIL 终裁 → 按卡文「到顶未清零」处理：
> 本卡**不合并**，是否接受下述证据链改判，见「待你裁决」⑧。

## 本卡未证明什么（必填）

1. **分钟常量 3/5 是拍脑袋值**——没有实测「一张到期卡平均复习几分钟」。这正是 ④ 请你给数的原因；在你说出真实数字前，总览页的「预计分钟」只是量级参考。
2. **多板形态 b 的错归风险**：`source_board: "[[A]], [[B]]"`（无内嵌引号的单串双链）会静默归到最后一个路径段的板名，既不是 A 也不是 B。实测现网 0 例，但若将来 Obsidian 某插件这样写，节点会错归——修它要动 `_board_name` 归一规则、影响全部单值节点的板身份，超出本卡加性边界，未修。
3. **`render_md` 对板名/节点名的转义是存量面**（G3-6a 移交 #9）：本卡新增的「为什么是这几块板」段沿用同一未转义口径（板名与既有表格行同值同面），只转义新段会造成同文件两套规则。统一转义策略待另卡。
4. **指纹防的是配置/源码演进，不防运行时篡改**：`implementation_sha256` 摘 pick.py 源文件字节——改 .py 必变指纹；但 round-3 抢救记录实证：直接篡改 `__pycache__` 的 .pyc 字节码并伪造 mtime 可以让排序变而指纹不变。该面属主动攻击者场景、无自然触发路径，本卡不防（见「待你裁决」⑧）。
5. **sha 指纹不覆盖 why 模板的中文文案**：改模板措辞（不改系数/代码）——由于 implementation_sha256 摘全文件，**任何 pick.py 改动（含注释）都会变指纹**，此条与 round-1 版声明相反且更严：指纹粒度是「实现+系数」，不能用它区分「改了什么」，只能证明「变了」。
6. **部署后的真实观感**：130 条测试 + 结构断言不等于像素级好看——375px 窄窗下解释行折行效果需要你按第 1 步亲眼确认。
7. **live 探针是单时刻快照**：2026-09-01 某时刻的数据形态（4 板截 3、句子内容）会随节点增删/复习推进而变，验收的是行为不是这批具体句子。
8. **本卡不跑 `test_daily_review_run.py`**（卡文明令：W4① 合入前该套件会真发 Bark）。runner 消费面零变化由「diff 不含 daily_review_run.py」+ 禁改门证明，未由 runner 自身测试回归证明。
9. **round-3 无正式终裁**（见 Codex 节显著声明）：「五项整改全部通过验证」的判断依据是抢救出的验证 checklist 而非 Codex 签名的 PASS 结论——证据强度低于 round-1/2 的正式报告。

## 📝 你的批注区

（留白）

## 复现命令（Claude 已跑完，此处只留给技术追溯）

```bash
# 1) 裁判套件
cd LANE/backend && caffeinate -i .venv/bin/pytest tests/regression/test_daily_review_pick.py \
  tests/unit/test_review_overview.py -q -p no:cacheprovider     # 预期 126 passed

# 2) live 只读探针 (避开 launchd 推送时刻; 必带 PYTHONDONTWRITEBYTECODE=1, 不带 --write)
shasum -a 256 /Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault/outputs/今日复习.{json,md}
cd LANE && PYTHONDONTWRITEBYTECODE=1 python3 scripts/daily_review_pick.py \
  --vault /Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault \
  --now 2026-09-01T23:30:00+08:00 | python3 -c "import sys,json; p=json.load(sys.stdin); \
  assert p['schema_version']==3; assert 'rank_manifest' in p; \
  assert all(b.get('why_this_board') for b in p['top_boards']); print('ok', p['rank_manifest'])"
shasum -a 256 …/今日复习.{json,md}   # 与前置逐字相同

# 3) 变异串行
python3 <scratchpad>/g36b_mutations.py   # 预期 6 条全红 + 还原逐字节一致
```
