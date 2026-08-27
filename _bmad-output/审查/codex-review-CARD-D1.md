审阅对象已冻结为 `91383b1f..d1ebea5f`。审阅期间外部进程将工作树推进到 `efb7dc4d`；后续提交及未跟踪文件均未纳入结论。

## BLOCKER

无。

## HIGH

1. `backend/app/api/v1/endpoints/review_overview.py:87-105,188-214,480-505,567-591` — 合法时间上界导致 HTML 端点 500。

   - 问题：`_due_ts` 接受 `9999-12-31T23:59:59Z`，但 `_humanize_due` 只捕获 `strptime`；其后的 `astimezone(+8)` 溢出。
   - 证据：对目标 blob 复现得到 `_due_ts => ACCEPT`，随后 `OverflowError: date value out of range`。`scripts/daily_review_pick.py:169-179,205-212` 同样允许该值进入真实 `upcoming`。
   - 建议：门禁阶段验证其可转换到上海时区，并让渲染层兜底捕获 `ValueError/OverflowError/OSError`。

2. `backend/app/api/v1/endpoints/review_overview.py:72-75,119-125,239-241,467-469,487-488` — 孤立 Unicode surrogate 可拖垮两个生产端点。

   - 问题：JSON 的 `"board":"\ud800"` 被 `isinstance(str)` 放行。
   - 证据：`/overview` 在 UTF-8 响应序列化时抛 `UnicodeEncodeError`；页面路径在 `quote()` 即抛同类异常，均已对目标 blob 复现。
   - 建议：所有外部字符串统一做严格 UTF-8/Unicode scalar 门禁，失败在 `_vault_entry` 内收敛为 `corrupt`。

3. `backend/app/api/v1/endpoints/review_overview.py:108-134,188-206,491` — 混合板的“最早到期”被新卡空串覆盖。

   - 问题：`g["earliest"] = min(g["earliest"], ts)` 令 `min("", 逾期时间)==""`。
   - 证据：同板一张 new 卡和一张逾期 scheduled 卡，目标实现输出 `earliest=""`，页面显示“现在”而非“逾期 N 天”。
   - 建议：只在非空 scheduled 时间中取最小值；没有非空时间时才回落到 `"" → 现在`。
   - 测试遗漏：`backend/tests/unit/test_review_overview.py:348-380` 已构造混合板，却只断言计数。

4. `backend/app/api/v1/endpoints/review_overview.py:156-185,307-339,355,523-539` — rollup 不验证构造律及跨源一致性。

   - 问题：各计数只验类型；`due` 还被用于决定是否生成零到期行，但不与 `due_nodes/stats` 对齐。
   - 证据：
     - rollup 声称某板 `due=1`、但 `due_nodes` 无该板时，整板静默消失。
     - 扁平 placeholder 为 0、rollup placeholder 为 999 时仍为 `ok`，页面汇总“待剖析 0”、表格“999”。
     - `backend/tests/unit/test_review_overview.py:492-545,558-572` 自身即构造扁平总数 0、板级合计 5，并断言 `ok`。
   - 建议：校验板集合、due/new/scheduled 分区、`future ↔ next_due`、`earliest_overdue`、与 due groups/stats 的一致性，以及 `sum(placeholder) <= flat_total`；不一致即 `corrupt`。

5. `backend/app/api/v1/endpoints/review_overview.py:108-153,265-364` — “严格 v3 门禁”实际仍是局部消费字段门禁。

   - 证据：以下垃圾均可通过并获得 `ok`：显式 `"boards": null`、缺少 `node` 的 due 行、重复 due/upcoming、空或重复 top board、`placeholder=[{}, true, null]`、非法顶层日期。重复 due 行会被直接重复计数；`top_boards=[A,A,B]` 还会让 B 与非 top 板使用相同排序优先级。
   - 建议：用缺键 sentinel 区分旧投影缺省与显式 null；验证完整 v3 必需字段、身份唯一性、非空白字符串和列表唯一性。

6. `backend/app/api/v1/endpoints/review_overview.py:341-343,400-415`；`backend/tests/unit/test_review_overview.py:265-302` — 非法 `generated_at` 被错误归为 stale。

   - 证据：垃圾文本、无时区值、非法日历日期都保留 projection 并返回 stale；测试第 301-302 行还明确锁定该行为。
   - 冲突：基准要求形状垃圾为 `corrupt`；只有合法时间但上海本地日不是今天才应为 stale。
   - 建议：在摘要门禁内完成词形、日历、时区转换验证。此行为在基线已存在，但 CARD-D1 的时间路径仍保留并继续锁定了它。

## MEDIUM

1. `scripts/daily_review_pick.py:111-119`；`backend/app/api/v1/endpoints/review_overview.py:314,324,355,523-539` — 正常未归板 placeholder 会让汇总和表格无法对账。

   - 所有 placeholder 都进入扁平列表，只有带 `source_board` 的进入 rollup。正常投影即可出现汇总 3、板级合计 1，页面无差额说明。
   - 建议：显示“未归板待剖析”数量或专门行；负差额则判 corrupt。

2. `backend/tests/regression/test_daily_review_pick.py:352-373` — “旧字段逐字段等价”测试没有冻结基线。

   - `top_boards == ranked[:3]` 是同源自证；due_nodes 只验节点集合，notification/stats 仅验部分字段，无法发现旧字段同步漂移。
   - 建议：固定 P1 前完整 golden payload，删除新增 `boards` 后做深度全等比较，包括顺序和所有嵌套字段。

3. `backend/tests/unit/test_review_overview.py:271-302,421-467` — 时区测试未真正锁定上海跨午夜。

   - `now ± 整天` 在 UTC 和上海日期算法下通常结果相同；fixture 与 HTTP 请求分别读时钟，恰逢上海午夜还会闪断。
   - 建议：使用固定的上海 `00:xx`/UTC 前一日 `16:xx` 边界，直接锁 `_humanize_due` 和 stale 判定，再保留 HTTP 接线测试。

## LOW

1. `backend/tests/unit/test_review_overview.py:14-19` — 测试模块直接构造 `ZoneInfo("Asia/Shanghai")`；无 tzdata 时收集即失败，无法验证生产代码 `review_overview.py:45-50` 的固定 `+8` 回退。

2. `backend/tests/unit/test_review_overview.py:324-336` — “零 JS”只拒绝 `<script src=`，内联 `<script>` 仍可通过测试。建议对小写化 HTML 直接断言不存在 `<script`，并覆盖 CSS 外链形式。

3. `scripts/daily_review_pick.py:85-86,192` — `scan_nodes` 文档仍声明三元组，实际已返回四元组。仓内唯一解包点 `:250` 已同步，runner 和 monkeypatch 都消费未变的 `build_payload` 二元契约，因此当前仅属文档/API 风险。

## 总体结论

不可合并原始 `d1ebea5f` 快照：消费方 A/B/D 为 FAIL，测试 F 为 PARTIAL，且存在两个已复现的生产 500 路径。

生产器 P1 本身未发现旧字段值漂移：schema 仍为 3，rollup 与 due rows/stats 同源，new/scheduled/malformed 判据正确，仓内调用链未因四元组破坏。普通 `<>&"'/?#%` 的链接 percent-encode 与 HTML 转义正确，未发现常规注入、外部 CDN 或实际 JS。

本次遵守静态只读边界，未运行会创建临时文件的 pytest；执行了固定提交 blob 的内存反例、语法编译和 `git diff --check`。`graphiti-canvas` 在当前会话不可用。

---

## 处置记录（Claude, 2026-08-28, commits b0028b0f / efb7dc4d / b923ff67）

一轮冻结在 `d1ebea5f` 快照；H1/H3 在审查进行期间已被端到端冒烟独立发现并先行修复（efb7dc4d / b0028b0f），其余在 b923ff67 处置。

| # | 处置 | 落点 |
|---|---|---|
| H1 astimezone 极值溢出 500 | **RESOLVED**（efb7dc4d，冒烟先行）：`_humanize_due` 的 astimezone 收进 try，捕获 ValueError/OverflowError/OSError 降级 "—"；`_fmt_projection_time` 同款已在 P0 首轮覆盖。采渲染层兜底而非门禁拒收：日历合法极值仍是"数据可示"，拒收会把整库打成 corrupt 藏起真数据。测试：极值板 case + `test_humanize_due_shanghai_midnight_semantics` 末条 | review_overview.py `_humanize_due` |
| H2 孤立 surrogate 500 | **RESOLVED**（b923ff67）：解析层 `json.dumps(payload, ensure_ascii=False).encode("utf-8")` 就地折断（UnicodeEncodeError ⊂ ValueError → corrupt），两端点全覆盖。测试：`bad-surrogate` | `_vault_entry` |
| H3 混板最早到期被"现在"盖掉 | **RESOLVED**（b0028b0f，冒烟先行）：earliest 仅在非空时间戳内取 min；混板断言补进 `test_board_table_groupby_matches_stats` | `_gate_due_groups` |
| H4 rollup 跨源一致性 | **RESOLVED**（b923ff67）：rollup 到期板集合+逐板计数必须==due_nodes group-by 派生（防"声称 due=1 但明细无此板"整板静默消失）；`sum(placeholder) <= 扁平总数`。不一致 corrupt。测试：`bad-rollup-due-drift` / `bad-rollup-ghost-board` / `bad-rollup-ph-overflow` | `_gate_boards_rollup` |
| H5 门禁盲区 | **RESOLVED**（b923ff67，五处）：显式 `"boards": null` 用 `in payload` sentinel 折断；due 行 `node` 非空字符串门禁 + `(board,node)` 重复折断；`top_boards` 重复板折断；`upcoming` 重复板折断；`ineligible.placeholder` 元素类型门禁。测试：`bad-boards-null`/`bad-dup-due`/`bad-node-empty`/`bad-dup-top`/`bad-dup-upcoming`/`bad-placeholder-elems`。**保留的既有边界**：`date` 等非消费字段仍只做类型门禁——本端点契约自 CARD-C2 起即"只门禁消费字段"，全量 v3 校验属契约变更，不在 D1 范围（如实登记，非疏漏） | `_summarize` 等 |
| H6 非法 generated_at 归 stale 非 corrupt | **NO-CHANGE（by-design 如实入档）**：这是 CARD-C2 轮 Codex（B1/B2）裁定的冻结语义——generated_at 畸形不影响 stats/明细数字的可用性，corrupt 会把整库真数据藏起来；stale 徽标 + 原样时间串是"不装新鲜也不丢数据"的诚实降级，`test_stale_badge_from_generated_at` 锁定。改动=C2 契约变更，超出 D1 范围；D1 仅保证该路径不再 500（H1 修复覆盖其渲染） | 无代码变更 |
| M1 未归板 placeholder 差额 | **RESOLVED**（b923ff67）：rollup 在场且板级合计<扁平总数时，汇总行标注"（含未归板 N）"；负差额已被 H4 门禁折断为 corrupt。测试：`含未归板 1` 断言 | `_card_html` |
| M2 golden 冻结基线 | **RESOLVED**（b923ff67）：`test_boards_rollup_golden_old_fields_frozen` 冻结完整旧 payload 字面量，pop("boards") 后深度全等 + 顶层键序恒等 | test_daily_review_pick.py |
| M3 上海午夜未真锁 | **RESOLVED**（b923ff67）：`test_humanize_due_shanghai_midnight_semantics` 纯函数直测上海/UTC 日错位窗口（三条 UTC 日判定必翻车的边界），零时钟读取零闪断；HTTP 接线测试保留 | test_review_overview.py |
| L1 测试模块 ZoneInfo 硬依赖 | **RESOLVED**（b923ff67）：与生产代码同款 try/except 退化固定 +8 | test_review_overview.py |
| L2 内联 script 可绕过 | **RESOLVED**（b923ff67）：marker 改 `<script`（小写化全文匹配） | test_review_overview.py |
| L3 scan_nodes docstring 三元组 | **RESOLVED**（b923ff67）：docstring 改四元组并注明 placeholder_boards 语义 | daily_review_pick.py |

**BLOCKER/HIGH 清零主张：是**（H1-H5 代码修复 + 测试锁定；H6 为前卡冻结语义的 by-design 登记，非本卡引入、非本卡可改）。待二轮复核确认。

---

## 二轮复核（Codex high, 对象 b923ff67）原文摘录

- H1/H2/H3/H6 + M2/M3 + L1/L2/L3 全 RESOLVED；"新增 500/误杀"RESOLVED（生产器真实产物满足全部新增门禁）
- **H4 STILL-OPEN**：仍放行全零幽灵板、`future=999/next_due=""`、`due_new=due_scheduled=999`（三分越界）；另点名 `stats.due_nodes=999` 与明细脱钩
- **H5 STILL-OPEN**：仍接受空 top board、空 upcoming node、非法顶层 date 并发 ok
- **M1 STILL-OPEN**：纯无主占位符（boards=[]）时差额注记被错误置零
- 终裁：「BLOCKER/HIGH 清零: 否」（完整原文存 session scratchpad codex-round2.md）

## 二轮残留处置（Claude, commit 8d81ff7f）

| 残留 | 处置 | 测试 |
|---|---|---|
| H4 全零幽灵板 | corrupt（板只经成员或占位符进 rollup，五计数全零非生产器产物） | `bad-rollup-allzero` |
| H4 future⟺next_due | 双条件绑定门禁：`(future>0) != bool(next_due)` → corrupt | `bad-rollup-no-nextdue` |
| H4 due 三分越界 | `due_new+due_scheduled > due` → corrupt | `bad-rollup-partition` |
| H4 due_new/due_scheduled 与明细漂移 | `_gate_due_groups` 增 scheduled 计数，rollup 三分逐板与明细 due_reason 同源比对 → corrupt | `bad-rollup-new-drift` |
| H4 stats.due_nodes 与明细脱钩 | **NO-CHANGE（by-design 如实入档）**：CARD-C2 冻结语义"stats 为权威计数、不重数明细"，由存量测试 `test_aggregates_multiple_vaults`（stats=7 vs 明细 1 断言 ok）显式锁定；页面以"（明细 N）"并陈两数不装一致。改动=C2 契约变更，与 H6 同类，超出 D1 范围 | 存量测试锁定 |
| H5 空 top board | 非空字符串门禁（生产器 `_board_name` 恒非空）→ corrupt | `bad-top-empty-board` |
| H5 空 upcoming node | 非空字符串门禁（生产器 node 恒为 stem）→ corrupt | `bad-upcoming-node-empty` |
| H5 非法 date | 词形 `\d{4}-\d{2}-\d{2}` + strptime 日历双验（None 容旧投影）→ corrupt | `bad-date-garbage` / `bad-date-month13` |
| M1 纯无主占位符注记置零 | summary 增 `placeholder_attributed` 字段（rollup 在场时为板级归属合计），渲染层据此算差额，不再从空板行重加 | `vault-unattr` +「含未归板 2」断言 |

复跑：overview 12 + pick 18 + run 22 全绿；端到端冒烟（真实生产器产物过全部新门禁）绿。待三轮定向确认。

---

## 三轮定向确认（Codex high, 对象 8d81ff7f）原文

- 二轮点名旁路逐条 RESOLVED：全零幽灵板 / future⟺next_due / due 三分越界 / due_new 明细漂移 / 空 top board / 空 upcoming node / 非法 date——均 corrupt 收敛，无静默放行、无 500
- 两条 NO-CHANGE 登记**接受**：stats.due_nodes 脱钩与非法 generated_at→stale 经 git 溯源确认均由 CARD-C2 提交 `434141b6` 引入并锁定，非 CARD-D1 引入
- 误杀检查：纯无主占位符 vault / 占位符专属板 / 全新卡板 / malformed fail-open 板 / 空 vault / 其余可达组合——生产器构造律与新门禁逐条对照，**零误杀**
- NEW-ISSUE：未发现 8d81ff7f 引入的新缺陷

**终裁：「BLOCKER/HIGH 清零: 是」**


