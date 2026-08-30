# UAT — CARD-G3-6a 投影桶位与 why_due 完整化

> **批次**: BATCH-2026-08-29-第六批 / CARD-G3-6a（车道 T6）
> **worktree**: `.claude/worktrees/card-t6-buckets`（分支 `card/t6-buckets`）
> **卡定义**: 总账 v2 §G3-6a（6h · wave 1 · 直接可感）
> **前置**: CARD-D1 已合并（`cbb20afb`），boards rollup 在 `d1ebea5f` 落地并过 3 轮 Codex —— 本卡零自造第二套 rollup 实现
> **执行日**: 2026-08-30

## 一句话

每日复习投影里的节点，过去只有"到期 / 未到期"两种命运；本卡给它们**分了五个桶并各配一句人话理由**——而且是**贴标签，不搬人**：节点仍原地留在 `due_nodes` 里，到期总数一个不多一个不少。

## 用户视角：你会看到什么变化

**复习清单（`outputs/今日复习.md`）末尾会多出一段「分层队列」**，长这样（用你 live 库今天的真实数据）：

```
## 分层队列

新卡 5 · 学习中 1 · 到期待复习 0 · 今天晚些到期 0 · 未来排期 0

**新卡**（5）
- Characteristic-Equation-for-Eigenvalues · 特征值与特征向量 — 新卡未排期，视同即刻到期 · 从未考察
- Fundamentals · 特征值与特征向量 — 新卡未排期，视同即刻到期 · 已闲置 36 天
- cs-61b-csm · CS 61B — 新卡未排期，视同即刻到期 · 从未考察
- lecture 2 · CS188 lecture 2 — 新卡未排期，视同即刻到期 · 从未考察
- my-recursion-notes · 递归与分治 (Recursion & Divide-Conquer) — 新卡未排期，视同即刻到期 · 从未考察

**学习中**（1）
- csm-tutoring-unit-credit · CS 61B — 学习中 · 已逾期 19 天（8月11日到期） · 已闲置 18 天
```

**跨库总览页（`/api/v1/review/overview/page`）的每张 vault 卡片，汇总行下会多一行**：
`分层 · 新卡 5 · 学习中 1 · 到期 0 · 今天晚些 0 · 未来 0`

**你原来看的东西一样都没变**：表格、`到期 N` 大数字、一键开考命令、Bark 推送文案、Dashboard 的数字，全部逐字不动。新东西只是"追加"。

**你需要做的**：现在什么都不用做（本卡不部署、不碰 live vault，只跑了只读验证）。真正需要你的时刻是**合并部署后的第二天早上**——9:05 的自动生成跑完之后，按下面三条看一眼就行。

## 👤 你来验（合并部署后的第二天早上，3 分钟，全程在 Obsidian / 浏览器里）

- [ ] 我在 Obsidian 里打开 `outputs/今日复习.md` → 我看到最上面的表格和「一键开考」和以前**一模一样**，末尾多出一段「分层队列」→ 我感觉这是加东西，不是把我熟悉的东西改掉了。
- [ ] 我看「分层队列」里每一行后面的那句话（比如「已闲置 36 天」「已逾期 19 天（8月11日到期）」）→ 我看到它说的天数和我印象里这张卡片的情况**对得上** → 我感觉它是在讲真话，不是在凑一句好看的文案。
- [ ] 我在浏览器打开跨库复习总览页 → 我看到每个库的大数字下面多了一行「分层 · 新卡 N · 学习中 N · 到期 N · 今天晚些 N · 未来 N」→ 我看到「新卡 + 学习中 + 到期」三个数加起来正好等于上面那个大的「到期」数 → 我感觉这两处数字是同一件事的两种说法，不会互相打架。

如果哪一条对不上，用 `Cmd+Shift+A` 在本文件的批注区写下来即可。

## 三条书面语义裁定（落地前先定，Codex 按此审）

裁定原文写在 `scripts/daily_review_pick.py` 模块 docstring 顶部（spec 头部），此处摘要：

### S1 桶位划分律与优先级（无重叠 · 无遗漏）

**划分域** = 已归板（`source_board` 可解析）且未被 `ineligible` 拦下的节点 —— 与 `stats.due_nodes + stats.future_nodes` 的口径域**完全同一**。未归板节点不进桶（已由 `unassigned_nodes` 点名），占位符 / 测试文件名 / 损坏节点不进桶（已由 `ineligible` 三桶点名）——不重复点名，也不静默吞。

**级联优先级**（自上而下先匹配先归，域内每节点恰好落一桶）：

| # | 桶 | 判据 |
|---|---|---|
| 1 | `new` | `due_reason == "new"` —— 无 `fsrs_due` 且非 fail-open 的真新卡 |
| 2 | `learning_queue` | 已到期 且 `fsrs_state ∈ {0, 1, 3}` |
| 3 | `due_now` | 其余已到期（含 `fsrs_state == 2` Review 与 malformed fail-open） |
| 4 | `due_today` | 未到期 且 `fsrs_due` 落在与 `now` 同一个 **Asia/Shanghai 日** |
| 5 | `future` | 其余未到期 |

**完备性论证**：域内每节点的 `due_now` 布尔恒二分 —— True 侧被 1/2/3 穷尽（3 = 1 的否定 ∧ 2 的否定），False 侧被 4/5 穷尽（同上海日与否）。互斥由级联保证。合计恒等（构造保证 + 契约测试）：

```
|new| + |learning_queue| + |due_now| == stats.due_nodes
|due_today| + |future|              == stats.future_nodes
```

**`fsrs_state` 取值裁定（含对卡面建议的一处明示偏离）**：勘探实测 live 14 节点仅 1 个带该字段、值为 1。py-fsrs v6 的 `State` 枚举**没有 New**（Learning=1 / Review=2 / Relearning=3）；历史哨兵 `0` 已由 `canvas-vault/.claude/scripts/fsrs_bridge.py:106-117` 在读侧归一为 Learning（CARD-C3 裁定）。本卡**同口径把 0 并入 `learning_queue`** —— 卡面建议是 `{1,3}`，本裁定是其**超集**，与评分侧「刚开始学」语义一致，只影响存量 0 值节点（live 实测 0 个），若不认可改一行常量即可回退。非整数 / 无法解析的 `fsrs_state` 按"无状态"落 `due_now` —— 未知值不吞节点，只是不享受分层优待。

### S2 加标签不搬移（R2 高风险面）

新桶只以**字段 / 标签**表达：`due_nodes` 行尾加性追加 `bucket` + `why_due`，顶层加性追加 `buckets` 分组。**节点仍全部留在 `due_nodes` 内，`stats.due_nodes` 口径分毫不动**。

理由（这就是卡里标 R2 的原因）：`review_overview.py` 把 `stats.due_nodes` 当权威计数、并用 `due_nodes` group-by 派生板级到期数；`Dashboard.md:57-72` 直接 `dv.io.load` 消费 `due_nodes` 明细。任何"把 learning/new 搬出 `due_nodes`"的做法都会**同时改动这两个消费方的数字**，属破坏性变更而非加性扩展。

加性的**上界**同样是契约：顶层只加 `buckets` 一个键；boards rollup 行 / `ineligible` / `notification` / `top_boards` / `upcoming` / `stats` **一个字段不加不改**，`schema_version` 保持 3。

### S3 why_due 取值枚举与生成规则

`why_due` 是**恒非空**人话串（桶位是机器枚举，`why_due` 是给人看的那一句），由 **6 个确定性模板**生成，槽位只填投影内已有的真实数据（`fsrs_due` / `fsrs_state` / `last_examined` 派生的闲置天数 / Asia/Shanghai 本地时刻），一律不虚构、不估算：

| 桶（分支） | 模板 |
|---|---|
| `new` | `新卡未排期，视同即刻到期 · <闲置片段>` |
| `learning_queue` | `<学习中\|重学中> · <到期片段> · <闲置片段>` |
| `due_now`（已排期） | `到期待复习 · <到期片段> · <闲置片段>` |
| `due_now`（脏日期） | `到期待复习 · 到期时间无法解析(<原值安全化摘录>)，保守视同到期 · <闲置片段>` |
| `due_today` | `今天 HH:MM 到期（尚未到点）` |
| `future` | `<明天\|N 天后> M月D日 HH:MM 到期` |

片段规则：**闲置片段** = `从未考察` / `已闲置 N 天`（N 取整，源自 `last_examined`）；**到期片段** = `已逾期 N 天（M月D日到期）` / `今天 HH:MM 到期` / 脏日期说明。

**原值安全化摘录**（Codex round-1 MEDIUM 后补入规格）：脏 `fsrs_due` 原值先按 ISO-8601 合法字符白名单过滤（非白名单字符逐个替换为 `?`）再截 40 字 —— `why_due` 会被拼进 `outputs/今日复习.md` 并可能被下游 HTML 渲染，原样透传等于把 frontmatter 里的任意串接进渲染面。摘录保留足以认出原值的形状，但**不再是逐字原值**，此行即其书面定义。

**极值兜底 2 条**（Codex round-1 MEDIUM 后显式纳入规格）：当 `fsrs_due` 或 `now` 的时刻在时区换算中不可表示（年份极值 `astimezone` 溢出）时，六模板的时间槽位无从生成，改用 `到期时刻超出可显示范围`（到期片段兜底）/ `到期时刻超出可显示范围，按未来排期处理`（future 兜底）—— 如实说"算不出"，不猜、不静默丢节点；同一情形下判桶的"今天"基准退化为 UTC 日。

非到期两桶（`due_today` / `future`）的 `why_due` 读作**「何时到期」** —— 同一字段名承载"为什么今天不用做"的诚实说明，**绝不给未到期节点编造到期理由**。时区：人话一律 Asia/Shanghai（与 CARD-D1 总览页同一口径）；落盘的 `fsrs_due` / `next_due` 仍是 UTC-Z 原样，不动。

## Claude 已代跑的技术验证

| 判据（卡定义要求） | 结果 |
|---|---|
| (a) 生产器加性新增桶位标签与 why_due，`schema_version` 保持 3 | ✅ `scripts/daily_review_pick.py`：`due_nodes` 行尾 +`bucket`/`why_due`，顶层 +`buckets`（五桶恒在）；旧字段零改动 |
| (a-硬) **payload 构造代码零删除行** | ✅ 生产器 `scripts/daily_review_pick.py` 全 diff **只有 1 行删除**，且是 `from datetime import ...` 导入行（补 `timedelta`）——`build_payload` / `scan_nodes` / `rank_boards` 区间 **0 删除**（Codex round-4 独立复核确认）。消费端的删除行全为结构性（dict 字面量扩键、返回签名、调用点、`generated_at` 校验上移） |
| (b) 加性契约金样（pop 新字段后深度全等 + 顶层键序恒等） | ✅ 新增 `test_buckets_golden_pre_g36a_fields_frozen`（冻结 G3-6a 引入前含 boards rollup 的完整字面量）；同时把 D1 的 `test_boards_rollup_golden_old_fields_frozen` 扩成**累积冻结**（摘掉两轮加性字段后仍须等于 D1 之前的字面量） |
| (b-2) 加性**上界**闸门 | ✅ `test_projection_v3_purely_additive_keeps_v2_contract` 的顶层键集合恒等断言显式扩为含 `buckets` —— 落地时这两条闸门确实先变红后按规程修改（证明它们不是空断言） |
| (c) 消费端最小接线 | ✅ `review_overview.py`：`_gate_buckets()` 门禁 + JSON `bucket_counts` + 页面卡片「分层」行；板级到期数仍由 `due_nodes` group-by 派生，**不从 buckets 抄** |
| (d) 裁判套件全绿 | ✅ `pytest tests/regression/test_daily_review_pick.py tests/unit/test_review_overview.py -q` → **46 passed**（基线 30 → +16；含 Codex 四轮整改补的 5 条） |
| (d-2) 新增用例覆盖五桶各一 + 边界 | ✅ 见下方用例清单（五桶各一 / malformed fail-open / 跨上海日 / 无 `fsrs_due` / `fsrs_state` 六态 / 同日已过点 / 划分域排除 / 空 vault） |
| (e) live 只读验证 | ✅ 见下方 live 快照；跑完复核 live vault 三处 mtime 未变 |
| 推送链未受影响 | ✅ `test_daily_review_run.py` **22 passed**；`daily_review_run.py` 仅读 `upcoming[0]` 与 state schema，`send_bark.py` 只读 `notification` |
| 扩跑相邻套件 | ✅ 四套件合跑（pick + overview + run + `test_board_manifest_contracts`）**132 passed**；另 `git diff --check` 通过 |
| 全量后端未跑的诚实说明 | `tests/test_routers.py` 有 16 failed —— **实证为存量**：用 `git show HEAD:` 的 `review_overview.py` 覆盖后复跑**同样 16 failed**，且失败全在 `TestCanvasRouter`/`TestAgentsRouter`（与本卡零交集）。全量 7228 项未跑（本地 ~35min 且存量红，非本卡判据） |
| `ruff check` / `ruff format` | ✅ 四个改动文件 lint All checks passed；3 个 backend 文件 `format --check` 亦已 `already formatted`（见移交表 #5：格式门零绕过） |
| 硬边界：`daily_review_run.py` / `send_bark.py` 零接触 | ✅ `git diff --stat` 仅 4 文件，不含二者 |
| 硬边界：live vault 只读 | ✅ 生成器以 `PYTHONDONTWRITEBYTECODE=1` 跑、不带 `--write`，输出重定向到 scratchpad |
| Codex 对抗审查 | **6 轮，round-6 终裁「可验收 / 必须整改项无 / 建议项无」**。累计 **9 HIGH + 6 MEDIUM + 4 LOW**：**7 条 HIGH 改码修满**，2 条判为消费端核验的原理上限并经两轮独立复核确认论证成立；存档 `_bmad-output/审查/codex-review-CARD-G3-6a.md` |

### 新增/改写用例清单（16 条）

**生产器侧（`test_daily_review_pick.py`，+14）**

| 用例 | 锁定什么 |
|---|---|
| `test_buckets_five_way_partition_each_bucket_covered` | 五桶各一 + 键序 + 两两不交 + 并集==已归板 + 两条合计恒等式 |
| `test_buckets_due_today_uses_shanghai_day_not_utc_day` | 跨上海日边界：13:00Z / 15:59:59Z / 16:00Z 同属 UTC 07-30，上海侧前两个仍今天、第三个已明天；并锁 `now` 用 +08:00 表示时判桶逐字不变 |
| `test_buckets_malformed_fail_open_and_new_card_edges` | 脏日期 fail-open 落 `due_now` 且 why_due 点名原值；无 `fsrs_due` 落 `new`；闲置片段源自 `last_examined`；**且四个节点仍全在 `due_nodes` 内** |
| `test_buckets_learning_states_and_unknown_state_fallback` | `fsrs_state` 六态（1/3/0/2/垃圾串/小数）+ 学习态但未到期仍按时间落 `future` |
| `test_buckets_same_day_overdue_reads_as_clock_time` | 到期片段 `delta==0` 分支说"今天 HH:MM 到期"而非"已逾期 0 天" |
| `test_buckets_domain_excludes_unassigned_and_ineligible` | 划分域：未归板与 ineligible 三类一律不进桶 |
| `test_buckets_empty_vault_keys_always_present` | 空 vault 五键恒在（消费方不做存在性分支） |
| `test_buckets_due_rows_mirror_bucket_grouping` | **S2 硬判据**：到期三桶成员逐个仍在 `due_nodes`，行内 `bucket`/`why_due` 与桶分组同源逐字相等 |
| `test_buckets_golden_pre_g36a_fields_frozen` | G3-6a 加性纯度金样 |
| `test_render_md_appends_bucket_section` | 人读清单末尾追加「分层队列」段，原表格/命令段零改动 |
| `test_dirty_fsrs_due_raw_is_sanitized_in_why_due` | **Codex round-1 MEDIUM**：对抗值 `bad\|<img src=x onerror=alert(1)>` 被白名单安全化；200 字超长原值截 40 |
| `test_extreme_now_falls_back_instead_of_crashing` | **Codex round-1 HIGH**：极值 `now` 下判桶不抛异常，今天基准退化 UTC 日，两条极值兜底文案逐字锁定 |
| `test_cli_rejects_unconvertible_now_with_clear_error` | **Codex round-1 HIGH**：真子进程跑 CLI，极值 `--now` 退出码非 0 + 人话原因 + **不吐 traceback**；正常 `--now` 仍 exit 0 |
| `test_today_sh_three_tier_fallback_never_raises` | **Codex round-2 MEDIUM**：上下界双向（year 9999 UTC / year 1 offset +14）—— 三档兜底保证判桶「今天」基准对任何 aware datetime 永不抛 |

**消费端（`test_review_overview.py`，+2 条用例，其中聚合用例内含 20 个降级子场景）**

`test_buckets_layer_counts_and_cross_source_gate`：正常投影出计数与页面分层行；旧投影（无 `buckets` 键）仍 `ok` 且 `bucket_counts=null`（加性不倒逼迁移）；二十类跨源不一致一律 `corrupt` 降级 ——

- **形状层（6）**：显式 `null` / 键集合非五桶 / 行字段垃圾 / 同一节点跨桶重复 / 未到期桶 `fsrs_due` 为空 / 非到期两桶与 `stats.future_nodes` 漂移；
- **到期三桶身份与语义层（5，Codex round-1 HIGH 后补）**：身份被整体替换成 `FAKE-*` 而逐板计数不变 / 行内 `bucket` 与所在桶矛盾 / 行内 `why_due` 与桶内不一致 / `new` 桶成员实为已排期卡 / 合计与 `stats.due_nodes` 权威计数漂移；
- **非到期两桶层（4，Codex round-2 HIGH 后补）**：时刻挪到非同一上海日 / 同板同时刻同 `why_due` 只换节点名 / `upcoming.next_due` 与桶内漂移 / 与 `boards.future` 逐板漂移；另 `generated_at` 非生产器形态、`buckets` 无 `boards`（round-3 HIGH）；
- **`upcoming` 绑定与到期侧时间层（3，Codex round-4 HIGH 后补）**：清空 `upcoming` 想跳过身份对账 / `upcoming` 换成有到期节点的板 / 未来时刻伪装 `due_now`；
- **节点身份全局唯一层（2，Codex round-5 HIGH 后补）**：同名节点跨板各落一桶（rollup/stats/upcoming 全同步造好）/ `due_nodes` 侧同名跨板重复。

`test_buckets_gate_accepts_real_producer_payload`（**门禁假阳性防线**）：不用手搓 fixture —— 直接调真生产器 `build_payload` 造投影、落真文件、过总览端点，断言 `ok` 且分层计数与生产器 `buckets` 逐字相等；库内含 **5 个零到期板**，真跑生产器把 `upcoming` 截断到 3，让"条数 == min(3, 候选数)"与"未选中的板不得更早"两条最易误伤真产物的对账被真正触发。

### live 只读验证快照（2026-08-30 11:29 上海时间）

命令（**不带 `--write`**，输出进 scratchpad）：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/daily_review_pick.py \
  --vault /Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault \
  > <scratchpad>/live-projection.json
```

| 检查 | 实测 |
|---|---|
| 节点文件总数守恒 | 14 = 桶内 6 + ineligible 8（全为 placeholder）+ 未归板 0 ✅ |
| 到期三桶合计 == `stats.due_nodes` | 6 == 6 ✅ |
| 非到期两桶合计 == `stats.future_nodes` | 0 == 0 ✅ |
| 跨桶零重复 | ✅ |
| 五桶分布 | `new` 5 / `learning_queue` 1 / `due_now` 0 / `due_today` 0 / `future` 0 |
| `learning_queue` 归属正确性 | 唯一带 `fsrs_state: 1` 的 `csm-tutoring-unit-credit` 落桶，why_due = `学习中 · 已逾期 19 天（8月11日到期） · 已闲置 18 天`（逾期天数与 `fsrs_due: 2026-08-11T13:56:58Z` 自洽，闲置天数与 `last_examined: 2026-08-11T13:55:58Z` 自洽）✅ |
| live vault 未被写 | `outputs/今日复习.{json,md}` mtime 仍为 Aug 30 09:06（当日 launchd 正常跑的那次）；`.claude/scripts/__pycache__` 无新文件 ✅ |

**分布合理性**：live 库 14 个节点里 8 个仍是未剖析占位符，真正可复习的只有 6 个，其中 5 个从未进入 FSRS 调度（无 `fsrs_due`）→ 全落 `new`；唯一进过调度的那个 8 月 11 日到期至今没做 → `learning_queue`。这与"这个库基本没被真正复习过"的事实吻合，无异常。

## 明示的移交与偏离（如实登记，不代用户决策）

| # | 事项 | 说明 |
|---|---|---|
| 1 | **总账里的第五桶 `suspended` 未实现** | 总账 v2 §G3-6a 原文列的是 `due_now/due_today/learning_queue/new/suspended`；卡面 S1 建议改为 `future`。本卡按卡面落 `future`。理由：live frontmatter **不存在任何挂起/暂停字段**，实现 `suspended` 等于凭空发明一套 snooze 语义（DD-10 功能蔓延），而 snooze 是 **G6-6「snooze 语义与全视图一致」** 的地盘。**待裁决**：确认 `suspended` 归 G6-6，还是要在本卡补一个 frontmatter 字段。 |
| 2 | **总账提到的 per-node `freshness` 字段未单独落字段** | 卡面完成条件 (a) 只点名"桶位标签与 why_due"。freshness 语义已由 why_due 的闲置片段（`从未考察` / `已闲置 N 天`）+ 既有 `last_examined` 承载。**待裁决**：是否要在 `due_nodes` 行再加一个结构化 `idle_days` 字段（下游 G6-5 若要排序会需要）。 |
| 3 | **`fsrs_state: 0` 并入 `learning_queue`（超出卡面建议的 `{1,3}`）** | 依据 `fsrs_bridge.py:106-117` 的读侧归一与 CARD-C3 裁定。live 实测受影响节点 = 0 个。若不认可，改 `LEARNING_STATES` 一行常量即可回退。 |
| 4 | **总览页只展示桶位计数，不展示节点级 why_due** | 卡面 (c) 为"可选"。节点级 why_due 的分区渲染是 **G6-5「队列分层与 why_due 解释展示」**（wave 3，依赖本卡）的明确职责。本卡把字段生产权收在投影侧，消费端只做最小接线并对 buckets 全量验形，避免与 G6-5 双 owner。 |
| 5 | **格式门：3 个 backend 文件已正式格式化，`scripts/daily_review_pick.py` 的漂移是存量故未动** | 提交时 lefthook 的 `python-lint` 格式门拦下了 3 个 backend 文件。**先查基线再处置**：这 3 个文件在 `HEAD` 版本 `ruff format --check` **返回 0**（干净）→ 漂移是本卡新增行引入的 → **正式跑 `ruff format` 修掉，未用任何绕过**（改完 132 passed 仍全绿）。而 `scripts/daily_review_pick.py` 的 `HEAD` 版本 `--check` 就**返回 1**（该文件按 ~100 字符手工排版、ruff 默认 88），且不在该 hook 的 staged 覆盖面内 —— 格式化它会产出与本卡无关的整文件重排，违反「禁止一次修复混合多个不相关变更」，故保持不动（与既有记录 `reference_ruff_format_drift_lefthook` 一致）。**本次提交零绕过**。 |
| 6 | **本批第六批开跑手册未在库中** | 卡面提到"本手册 §二 G3-6a 要点"，但 `_bmad-output/implementation-artifacts/goal-cards/` 下最新为第五批手册，无第六批文件。R2 高风险要点已在卡面正文给出并据此执行（S2 加标签不搬移），无信息缺口。 |
| 7 | **存量缺陷：`payload["date"]` 对极值时刻会 `OverflowError`（本卡未修）** | Codex round-1 报为 HIGH，实测**改动前的 HEAD 版本同样崩溃**（`--now 9999-12-31T23:59:59Z` → 崩在未改动的 `payload["date"] = now.astimezone().date()`）。本卡只做了两件不越界的事：判桶层不新增崩溃路径（`_today_sh` 兜底），入口对不可换算的 `--now` 明确拒绝而非吐 traceback。**没有去改 `payload["date"]`** —— 那是 A2 冻结字段的计算，超出本卡"纯加性"边界。**待裁决**：是否单开一张小卡把 `date`/`generated_at` 的极值换算一并做诚实降级。注：`--now` 是测试用 flag，launchd 生产链不传，现网无触发面。 |
| 8 | **`why_due` 在消费端只验非空 / 两处相等，不验模板**（Codex round-4 MEDIUM） | 消费端重算 S3 模板 = 把生产器逻辑抄第二份，模板一演进两边必漂。现标为**受信生产器字段**。**建议**：真正展示 `why_due` 的 **G6-5** 落地时若需强校验，应由生产器额外导出「模板 id」让消费端对枚举，而不是让消费端反推文案。 |
| 9 | **`render_md` 对 `node`/`board` 从未转义**（Codex round-4 MEDIUM，存量非本卡引入） | 既有表格行、`unassigned_nodes` 行同样直拼节点名；本卡新增的「分层队列」段属同一类同一值。只转义新段会造成同文件两套规则。本卡安全化的是**本卡新引入的面**（脏 `fsrs_due` 原值）。**待裁决**：是否单开一卡统一 `render_md` 的转义策略。 |
| 10 | **`_GENERATED_AT_RE` 不接受 1901 年前的历史秒级偏移**（Codex round-3 MEDIUM，round-4 复核论证成立） | 该正则是 CARD-C2 的反冒充门（本卡零改动），放宽会削弱它；触发前提是 `--now` 传 1900 年及更早，生产链 `datetime.now(utc)` 永不产生。登记备查。 |

## 复现命令（Claude 已跑完，此处只留给技术追溯，你不需要执行）

```bash
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-buckets

# 1) 裁判套件（卡面 (d)）
cd backend && caffeinate -i .venv/bin/pytest \
  tests/regression/test_daily_review_pick.py tests/unit/test_review_overview.py -q
# 预期: 41 passed

# 2) 推送链未受影响
caffeinate -i .venv/bin/pytest tests/regression/test_daily_review_run.py -q
# 预期: 22 passed（与 1) 合并跑为 63 passed）

# 3) live 只读复跑（不写 live）
cd .. && PYTHONDONTWRITEBYTECODE=1 python3 scripts/daily_review_pick.py \
  --vault /Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault | python3 -m json.tool | head -60
```

## Codex 对抗审查

逐轮提示词 + 原文报告 + 整改记录：`_bmad-output/审查/codex-review-CARD-G3-6a.md`。

| 轮 | 判定 | 发现 | 处置 |
|---|---|---|---|
| round-1 | 需整改 | 2 HIGH（消费端只比计数可被身份替换绕过 / 极值 `--now` 崩全轮）+ 2 MEDIUM + 1 LOW | 全部整改；其中极值 `--now` 经实测**是 HEAD 存量缺陷**，按"不新增崩溃路径 + 入口明确拒绝"处理，未越界去改冻结字段 |
| round-2 | 需整改 | 1 HIGH（非到期两桶残留等价旁路）+ 1 MEDIUM（`_today_sh` 兜底不完整）+ 1 条测试质量项（fixture 把旁路固化了 / 缺真生产器集成测试） | 全部整改：新增"以 `generated_at` 重算判据 + 与 boards rollup 逐板对账"双路，三档兜底，真生产器集成测试 |
| round-3 | 需整改 | 3 HIGH（非到期身份无对手盘 / `fsrs_state` 无独立依据 / `buckets` 无 `boards` 时跳过对账）+ 1 MEDIUM + 1 LOW | 1 条修满（`boards` 必须同在）、1 条部分修+论证（新增 `upcoming` 身份对账，其余为原理上限）、2 条如实论证不改码、1 条修（拆分反例） |
| round-4 | 需整改 | 2 HIGH（清空 `upcoming` 可整体跳过身份对账 / 到期桶提前 `continue` 绕过时间判据）+ 2 MEDIUM + 1 LOW | **两条 HIGH 都不是原理上限，全修**：`upcoming` 本身被钉死在 rollup 上（条数/板集合/升序/不漏更早/`next_due` 五验）；到期侧补 `scheduled ⟹ fsrs_due <= 参照时钟`。另 2 MEDIUM 如实论证不改，LOW 扩跑到 132 passed |
| round-5 | 需整改 | 前两条 HIGH 复核 PASS、原理上限论证成立；**新发现 1 HIGH**：节点身份是全局唯一文件名，门禁却用 `(板, 节点)` 复合键去重 → 同名节点跨板各落一桶能拿 `ok` | **已整改**：两处去重键改为节点全局键；另 2 LOW（原理上限表述扩到「凡未被 `upcoming` 点名的非到期节点」、错误消息截断）一并修 |
| **round-6** | **可验收** | **必须整改项「无」、建议项「无」** | 终裁。（首次提示词被 codex 的 cyber 过滤误拦，改中性措辞后重跑；**未改动任何被审代码**，如实记在存档里） |

### 两条「论证而非改码」的如实定性（供你复核，不是搪塞）

1. **未被 `upcoming` 点名的非到期节点，节点名无法被消费端核验。** 因为它在整份投影里**只出现一次**——没有第二个来源可比。A2 的架构裁定本就是"投影是到期口径唯一裁判、消费端只读不重算"。本轮把能做的独立对账做满了（`upcoming` 点名的那些必须对得上身份 + 时刻 + 板内最早）。
2. **`fsrs_state` 不落盘，消费端无法独立验证 learning/due 分类。** 把它加进 payload **不构成独立依据**——同一个生产器同时写两处，伪造者只需多改一个字段。分类正确性由**生产器侧契约测试**保证（五桶划分律 + `fsrs_state` 六态用例）。

两条论证都写进了 `_gate_buckets` 的 docstring，后续审查可以直接对着它反驳。
