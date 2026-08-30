审阅对象：`HEAD = 8d81ff7fac404316562f4380c225c1326ef946a7`；全程只读，工作树未变。

- RESOLVED — 全零幽灵板：五计数全零命中 `review_overview.py:223-225`，降级为 `corrupt`。
- RESOLVED — `future=999 / next_due=""`：双向绑定检查于 `:220-222` 拒绝。
- RESOLVED — `due_new=due_scheduled=999` 三分越界：`due_new + due_scheduled > due` 于 `:214-219` 拒绝。
- RESOLVED — `due_new/due_scheduled` 与明细漂移：明细分组于 `:139-144` 独立计数，并在 `:232-243` 与 rollup 逐板比对。
- RESOLVED — 空 top board：非空字符串门禁于 `:357-367` 拒绝。
- RESOLVED — 空 upcoming node：非空字符串门禁于 `:150-172` 拒绝。
- RESOLVED — 非法顶层 date：词形及日历双验于 `:416-425` 拒绝垃圾文本和月份 13。
- RESOLVED — 上述异常均由 `_vault_entry` 的 `:476-488` 收敛为单库 `corrupt`，不会静默放行或形成端点 500。
- RESOLVED — 纯无主占位符：`placeholder_attributed=0` 于 `:446-449` 保留，`:620-629` 正确渲染“含未归板 2”。

- RESOLVED（NO-CHANGE 接受）— `stats.due_nodes` 与明细脱钩：实现及 `stats=7、明细=1、status=ok` 测试均由 CARD-C2 提交 `434141b6` 引入并锁定，非 CARD-D1 引入。
- RESOLVED（NO-CHANGE 接受）— 非法 `generated_at → stale`：`review_overview.py:490-504` 与 `test_stale_badge_from_generated_at:318-355` 均源自同一 CARD-C2 提交 `434141b6`。

- RESOLVED — 纯无主占位符 vault：`boards=[]` 通过门禁并正确显示未归板差额。
- RESOLVED — 占位符专属板：`due=future=0、placeholder>0、next_due=""` 不触发全零门禁并正确生成零到期板行。
- RESOLVED — 全新卡板：`due=due_new、due_scheduled=0` 与 `due_reason=new` 明细一致，通过并正确渲染。
- RESOLVED — malformed fail-open 板：生产器清空 `fsrs_due`、写入 `due_reason=malformed`，其计入 `due` 但不计入 new/scheduled，门禁接受。
- RESOLVED — 空 vault：`boards=[] / due_nodes=[] / top_boards=[] / upcoming=[]` 正常通过并渲染空板提示。
- RESOLVED — 其余可达组合：scheduled 到期、future-only、due+future、成员与占位符混合及多板组合均由 `daily_review_pick.py:258-300` 保证三分、future/next_due、板集合和明细同源，新增门禁零误杀。
- NEW-ISSUE 检查 — 未发现 `8d81ff7f` 引入的新缺陷。

BLOCKER/HIGH 清零: 是
