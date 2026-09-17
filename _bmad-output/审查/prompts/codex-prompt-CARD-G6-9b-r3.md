# CARD-G6-9b 独立复核请求（BATCH-2026-09-11-第十四批 · 车道 T3 · round-3）

## 一 背景

Canvas Learning System 的跨库复习总览端点 `GET /api/v1/review/overview`（JSON）与
`GET /api/v1/review/overview/page`（零 JS 页面）此前**完全看不出推送有没有失败**：
每日复习 runner（`scripts/daily_review_run.py`）跑完会往 Bark 推一条通知，推失败时它
在自己的 state 文件里记 `last_result="generated_push_failed"` + `last_error="bark-send"`，
但 review 面一个字段都没读 —— 榜单照常生成、页面一片绿，用户以为一切正常，手机上其实
什么都没收到。

本卡是**纯加性**改动：给 `/overview` 的每个 vault 条目加 `push_degraded` + `last_error`
两个键，并在总览页的 vault 卡片上加一枚「推送降级」徽标。数据源只有 runner state，
没有 state 时两字段为 null。不改 runner 侧、不改时区/snooze/board_done 既有语义。

审查绑定 SHA：`baf8a693e7b781bc64fe72d9e153f37b54e65e8a`（分支 `card/t3-review`）。前提 commit `5cdc98439594ea58b427cc5eee61857baad7506b`。

## 二 最小读取面（写死；不必读别处）

1. `git diff 5cdc98439594ea58b427cc5eee61857baad7506b baf8a693e7b781bc64fe72d9e153f37b54e65e8a -- . ':(exclude)_bmad-output'` —— 本卡全部代码改动（2 个文件）。
2. `backend/app/api/v1/endpoints/review_overview.py` 的这些段（行号为 `baf8a693e7b781bc64fe72d9e153f37b54e65e8a` 实测）：
   - `:802` `_PUSH_DEGRADED_LABEL` 常量
   - `:1043-1180` `_vault_entry` 与 `_collect`（含 `_collect` 的单库异常兜底 inline dict）
   - `:1628-1800` `_card_html`（徽标渲染点）与 `review_overview_page`
   - `:2067-2090` `_read_entry`（refresh 读回的 corrupt inline dict）
   - `:2490-2520` `_read_board_done` / `_board_done_today`（本卡照抄的现成只读范式）
   - `:2521-2585` `_read_push_status` / `_push_status`（本卡新增两函数）
   - `:2609-2650` `_read_snoozed`（另一条现成只读范式，含 UTF-8 可编码门）
3. `backend/tests/unit/test_review_overview.py` 的 `:4610-4765`（本卡新增四条门 + 三个 helper）。
4. `scripts/daily_review_run.py` 的 `:735-750` 与 `:81-90` —— state 字段的产生方与
   state 路径派生，**只读其语义**，不评它对不对。

## 三 请按重要性排序，独立核对以下各点

**⓪ 三态映射是否正确，且缺失态与失败态可区分。**
期望语义：`last_result == "pushed"` → `push_degraded is False`；
`last_result == "generated_push_failed"` → `True`；
没有 state 文件 / 读不出 / 不是 dict / 没有 `last_result` 键 → `None`。
重点：`None` 是否可能被 `False` 顶替？`False` 的语义是「推过、成功了」，若「今天根本
没跑过」也显示成 `False`，本卡要消灭的那种「看起来一切正常」就原样保留了。
另请核 `last_error` 非 str 时是否归 `None`，以及此时 `push_degraded` 的取值是否仍合理。

**① 徽标是否仅在 `push_degraded is True` 时渲染。**
`False`（推成功）与 `None`（没推过 / 读不出）都不该出徽标 —— 一枚无条件渲染的徽标零
信息量。请核 `_card_html` 的条件写法，以及门
`test_overview_page_degrade_badge_only_when_failed` 的验伪锚是否真能排除「无条件渲染」
这一形态（它在同一页里同时放了成功态与缺失态两张卡片）。若存在**门未覆盖的路径**能让
徽标出现在不该出现的卡片上而四条门全绿，请指出。

**② 新键是否四态齐带。**
`_vault_entry` 的 entry dict、`_collect` 的单库异常兜底 inline dict、`_read_entry` 的
corrupt inline dict —— 三处是否都带了 `push_degraded` / `last_error`。另：本卡顺带给
`_read_entry` 的 corrupt dict 补了此前缺失的 `board_done` / `snoozed`，请核该处补齐是否
会改变 refresh 端点既有消费方的行为。

**③ 读侧容错是否与 `_read_board_done` / `_read_snoozed` 同款。**
读不出 / 键缺是否一律降级而非 500；是否绝对不写盘、不隔离、不重建。特别请核：
`last_error` 是从外部文件读出的 str，会原样进响应 JSON 与页面 —— JSON 的 `\\ud800`
转义解出的孤立 surrogate 是合格的 str，却在响应做 UTF-8 序列化时才抛 UnicodeEncodeError，
那一刻已出了 `_collect` 的单库兜底。本卡的处置是否与 `_read_snoozed` 逐条同纪律？
是否存在**未被拦下的输入**（state 里的某种形状）仍能让整个 `/overview` 变 500？

**④ 是否误动了既有语义。**
时区族（`_display_tz` / `_display_today` / `_display_now`）、board_done / snooze 的读写、
refresh 去抖与写锁、`_read_board_done` / `_read_snoozed` 本体 —— 本卡应当一个字都没改。
另请核：不降级的 vault 卡片 HTML 是否与改动前逐字节相同（本卡的说法是「只在降级时才多
包一层 flex 容器」）。

**⑤ /overview 加键是否真的不改 openapi 契约。**
该端点声明是 `async def review_overview() -> dict`，无 `response_model`。本卡实测：
lefthook 的 spec-sync 重生 `backend/openapi.json` 后，与前一版除 `x-generated-at` 一行
外逐字相同；该行已由紧随的 commit `baf8a693e7b781bc64fe72d9e153f37b54e65e8a` 写回。请独立判断这一结论是否成立。

**⑥ 四条门自身的强度。**
每条门的断言是否逐值（`is True` / `is False` / `is None`）而非「字段存在即可」；
三段负控输入（degraded 恒 False / 徽标条件恒真 / 缺失态返回 `(False, "")`）是否确实各自
只能红在其对应的那一条断言上。

## 四 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给出：
`file:line` + 一句话说明缺陷 + 一句话说明在什么输入下会显形。
没有问题的检查点请显式写「core 点 N：未发现问题」，不要省略。

## 五 边界

只读审查。不要连任何数据库、不要起服务、不跑 7691 / 7692 端口上的任何东西、不执行测试。
不评 runner 侧（`scripts/daily_review_run.py`）的推送算法与 state 产生逻辑是否正确 ——
本卡只消费它已经写下的字段。不评本仓其它卡的改动。

---

## 六 本轮（round-3）相对 round-2 的改动，请重点复核

round-2 报了 1 项 MEDIUM：`bool(err)` 跑在 `isinstance(err, str)` 门之前，
`{"last_result": null, "last_error": 123}` 这类连类型都不对的值也能让
`push_degraded` 变 `True`（假警报），且四门未覆盖。

本轮的处置是**撤回**那条余量，而不是再加一层判断——它本来就是在 round-1 的建议
（「由 `last_result` 的明确枚举决定三态」）之外多加的，round-1 与 round-2 的 MEDIUM
都长在它身上：

- 三态现在**只**认两个枚举：`"pushed"` → `False`；`"generated_push_failed"` → `True`；
  其余（含 `null` / 未知值 / 任何 `last_error`）一律 `return (None, None)`。
- `last_error` 完全不参与三态判定，只作为给用户看的原因文本，仍过
  `isinstance(str)` + UTF-8 可编码两道门。
- 门仍是四条（未新增第五条），补齐分支覆盖：门② 加「`last_error` 是 `123`」；
  门③ 加「未知结果 + 噪声 `last_error`（字符串与 `123` 两例）」「`state` 不是 dict」
  「JSON 本身是坏的」。
- 新增负控⑤：round-2 指出负控④ 会让门③ 先停在 `null` 那条断言、同次执行到不了
  「未知值」那条。负控⑤ 隔离成「只保住 `null` 那一格、让未知值冒充成功」，门③ 遂
  精确红在 `assert e4["push_degraded"] is None` 上。

请特别判断：
1. `_read_push_status` 现在是否还有**门未覆盖的路径**？请逐条列出该函数的每个出口
   以及守它的那条断言；若有出口没有断言守着，请点名。
2. 撤回那条余量是否引入了新的漏报：某种在**当前 runner**（`scripts/daily_review_run.py`
   只在 `:739` 与 `:745` 写 `last_result`）下真实可达的失败形态，现在会被报成 `None`
   或 `False`？请只就真实可达的形态判断，推测性的未来枚举不算。
3. 门② / 门③ 新增的那几个子例，断言是否仍是逐值（`is True` / `is False` / `is None`），
   有没有被写成「字段存在即可」之类的弱断言。
4. 负控⑤ 的变异形态是否真的隔离出了「未知值」那条断言，还是仍可能红在别的原因上。
