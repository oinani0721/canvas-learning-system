# 对抗性代码审查 — CARD-G6-6（板级 snooze 两档「今晚 / 明天」）

你是独立审查者。只读，不改任何文件，不连任何数据库。

---

## 一 背景与最小读取面

**已裁事项（用户裁定，不要建议改变这些方向）**
- D-8：snooze 粒度 = **板级**（不做节点级）；档位 = **两档「今晚 / 明天」**（不做自定义天数 / 自由时间）。
- 「今晚 = 当日 20:00 显示时区 / 明天 = 次日 00:00 显示时区」是**任务书默认值**，20:00 这个小时阈值**未经用户显式裁定**，已在验收单登记待确认。请不要把「阈值该是几点」当成缺陷提。
- D-18：时区来源由前一张卡（U6-A）落地，本卡只调用 `display_tz()`，不许有第三套时钟。
- 前一张卡（U6-B / CARD-G6-7-R）已落地 state 跨进程锁 + 锁内三方合并 + 取消完成端点，本卡**只复用不改**。

**本卡改动面**（`git diff BASE HEAD -- . ':(exclude)_bmad-output'`，BASE = `72ab01ed9954d4ea7fb56288c2b9828abb46160b`）：

请重点读这些位置：

1. `scripts/daily_review_pick.py`
   - `parse_snooze_until` / `active_snoozed`（新增，让位判定的**唯一定义点**）
   - `build_payload` 的签名与两个分区块（board_done 分区之后紧跟 snoozed 分区）
   - `main()` 里从 `--state` 读 `snoozed` 那一段
2. `scripts/daily_review_run.py`
   - `STATE_SCHEMA_VERSION`（2 → 3）、`_fresh_state` / `_parse_state_file` / `_normalize_state`
   - `ensure_payload` 的缓存门（`snoozed_sig` / `snooze_wake_utc` / `wake_crossed`）与传参
   - `active_snoozed`（转调生产器那一个判定的薄封装）
3. `backend/app/api/v1/endpoints/review_overview.py`
   - `_display_now` / `_SNOOZE_TONIGHT_HOUR` / `_SNOOZE_CHOICES` / `_snooze_until`
   - `_read_snoozed` / `_snoozed_active` / `_snooze_wake_label`
   - `_write_board_snooze` / `_write_board_unsnooze`
   - 两个新端点 `review_overview_board_snooze` / `review_overview_board_unsnooze`
   - `_vault_entry` / `_collect`（加性 `snoozed` 与顶层 `tonight_available`）
   - `_boards_split_html`（第三区「已推迟」）/ `_board_table_html` / `_card_html` / `review_overview_page`
4. `backend/app/api/v1/endpoints/review_app.py`
   - 第 55-62 行的 import 与「共享不复制」纪律注释
   - `activeSnoozed` / `boardSnoozeBtnHtml` / `boardUnsnoozeBtnHtml` / `boardsSplitHtml` / `boardTableHtml`
   - `onBoardSnoozeClick` / `onBoardUnsnoozeClick` / `renderPage` 里的 `tonightAvailable`
   - URL 表
5. 四个测试文件里本卡新增的 33 条用例，外加这些**既有承重门**（本卡对它们的处置是否正当）：
   - `backend/tests/regression/test_daily_review_pick.py` 的两条金样门（`test_boards_rollup_golden_old_fields_frozen` / `test_buckets_golden_pre_g36a_fields_frozen`）
   - `backend/tests/regression/test_daily_review_run.py` 里本卡改过的 5 处 `schema_version` 断言 + 新增的钉实值门 `test_g66_state_schema_version_is_three`
   - `backend/tests/unit/test_review_overview.py` 的 FSRS 写面允许集（`changed == {...}` 三项）与其常驻负控；两条 `page.count("<details")` 计数断言（本卡零改动）
   - `backend/tests/unit/test_review_app.py` 的 AST 白名单两张表（各加一项）与四条枚举合约门（URLS 集合 / handlers 元组）

---

## 二 作者自述（请独立核对，不要采信）

1. **让位只换序**：`snoozed` 只影响板级推荐顺序，不删任何行、不改任何桶、不改任何分。payload 顶层零新键。
2. **不压制 due**：没有任何节点的 `fsrs_due` / frontmatter 被写，学习事件账本不追加。
3. **单一时钟**：`until` 的两档换算、20:00 判定、页面时间人话，全部来自 `_display_now()` 这**一个**入口（它现调 `_display_tz()`，不缓存）；`review_overview.py` 里没有也不许有 `_DISPLAY_TZ*` 模块级常量。
4. **「明天」防 DST 漂移**：用 date 加法 + `datetime.combine`，而不是 `now + timedelta(hours=24)`。
5. **20:00 只在服务端判一次**：以顶层布尔 `tonight_available` 下发，前端直接用它渲染，不做任何小时数比较。
6. **缓存门同律唤醒**：`snoozed_sig` 与既有 `board_done_sig` 逐条同形（含「签名缺席 ≠ 变化」那条收紧）；`snooze_wake_utc` 与 `next_due_utc` 同形，`wake_crossed` 与 `due_crossed` 同律。until 一过，下一档 runner 必重扫。
7. **活跃判定只有一份**：`daily_review_pick.active_snoozed` 是唯一定义点，runner 与 Web 读侧都转调它。
8. **升版处置**：`STATE_SCHEMA_VERSION` 2→3 打红了 5 处既有断言，全部改成 `== runner.STATE_SCHEMA_VERSION`（形态断言），实值另立一条门钉住。
9. **FSRS 零触碰**：写面允许集与前一张卡完全相同（三项），本卡未改动它；常驻负控换到 snooze 写点后红在 `_FSRS_GATE_MSG` 上。

---

## 三 请按重要性排序回答的问题

1. `until` 的两档换算有没有任何一处不经 `_display_now()` / `_display_tz()`（第三套时钟）？DST 切换日的「明天 00:00」是否真是当地 00:00，offset 取的是**次日**那天的值？
2. pick 的 `active_snoozed` 对 naive 串 / 错格式 / 非 str / 键非 str / 已过期，是否**全部**退化为「无 snooze 逐字节同行为」且不抛异常？两条金样门是否真能抓到 payload 顶层新键？
3. 缓存门的 `snoozed_sig` / `snooze_wake_utc` 会不会让「升级当天既有 v2 state」被误判成「账变了」而白重扫一轮？until 一过是否**必然**重扫（而不是要等别的条件配合）？`wake_crossed` 与 `due_crossed` 的短路顺序有没有让其中一个失效？
4. 读侧 `_read_snoozed` / `_snoozed_active` 是否可能写盘（只读契约）？损坏值 / 极值时刻是否会把 GET 或页面打成 500？
5. FSRS 零触碰的负控，红是否绑在 `_FSRS_GATE_MSG` 这一条断言上，而不是「某处失败了」？写面允许集有没有被本卡悄悄放宽？
6. 新的两个 POST 有没有任何路径被 timer / `visibilitychange` 触发？20:00 的判定是否**只在服务端做一次**并以 `tonight_available` 下发（JS 里有没有任何残留的小时数比较）？该布尔与端点 422 的判定是否同一次时钟读数？
7. D-8 甲的两条禁令（节点级 / 自定义时长）在端点与两个页面上是否都无入口？422 有没有在某条路径上被静默夹到最近的档位？
8. 「已推迟」区是否真的条件渲染（活跃集为空时页面上一个 `<details>` 都不多）？两条 `page.count("<details")` 断言有没有被改动，或被新增用例架空？同一块板既完成又被推迟时会不会渲染两次？
9. `_SNOOZE_NOTE` 的注入是否只在 AST 白名单各加一项？检查器本体与探针矩阵有没有被动过？文案有没有被复制成第二份？本卡改动的 4 条枚举合约门（URLS 集合 / handlers 元组）是「登记新端点」还是把门放松了？
10. `STATE_SCHEMA_VERSION` 2→3 之后，那 5 处改成形态断言的地方，有没有哪一处本该保留字面量（例如它守的是「输入夹具就是 v1/v2」这件事而不是「升版结果」）？

---

## 四 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条给出 `file:line`、问题陈述、以及一个**具体的失败场景**（什么输入 / 什么状态 → 什么错误结果）。没有问题的分级写「无」。

---

## 五 边界

- 只读审查：不要修改任何文件。
- 不要连接任何数据库或网络服务。
- 不要建议改动 U6-A 产物（`backend/app/core/display_tz.py` / `scripts/local_tz.py` / `backend/scripts/vault_lint.py` 及其门）或 U6-B 的锁 / 三方合并 / 取消完成端点行为。
- `canvas-vault/.claude/scripts/fsrs_bridge.py` 与 `decay_beta.py` 本卡零触碰，不在审查面内。
- 通知文案（Bark 推送里标注「已推迟」）本卡刻意未做，不要当缺陷提。

---

## 六 round-4 增量说明（本轮相对 round-3 的改动）

round-3（审 `1ccc9711`，绑当时的最终 HEAD）判 BLOCKER 0 / HIGH 0 / MEDIUM 0 + 2 LOW ⇒ D-15 已满足。
**本轮是纯注释改动、零行为变化**，送这一轮只为按协议「审后再改代码必再送一轮」收口。请核这两处
登记本身有没有再写错：

1. **LOW-2 更正**：`test_g66_tomorrow_survives_dst_transitions` 的 docstring 与两条 case 注释里，
   「Nuuk 的切换在 UTC 22:00」已改为「当地午夜，2026 春季 = `2026-03-29T01:00Z`、秋季 =
   `2026-10-25T01:00Z`」。请核这两个 UTC 时刻本身对不对（这已经是我在本卡第四次把推断当事实写下，
   所以这一次请务必实测而不是照读）。

2. **LOW-1 登记（不修）**：`test_review_app.py` 里那条「推迟键不与另一库的完成键碰撞」的门，
   第二条断言上方补了一段注释，明说它**不覆盖**你给的板名侧反向碰撞
   （`snoozeKey("math","A") === doneKey("snooze", "math\u0000A")`），并给出不修的两条理由：
   ① `doneKey` 自身就有同款碰撞（`doneKey("a","b\u0000c") === doneKey("a\u0000b","c")`，已独立实测为真），
      `snoozeKey` 继承的是同一个前提；
   ② 彻底修法要把键编码换成长度前缀 / 转义，会动 board-done / board-undone 的既有形态，
      卡文 §三 禁改 U6-B 产物。
   请核：这两条理由站不站得住；那段注释有没有把覆盖面说大或说小；`doneKey` 同款碰撞这个论断是否成立。

除这两处外，本轮没有任何实现或断言改动。请一并确认：
`git diff 1ccc9711 HEAD -- . ':(exclude)_bmad-output'` 的内容是否**只有注释**。
