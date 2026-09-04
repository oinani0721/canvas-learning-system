> ⚠️ 本文件是 CARD-G6-7 的完整卡文——车道开工后必读并逐条执行；它不是 /goal 粘贴文本。/goal 在第十一批手册 §三 Z1-D 块。
> 批次标记 `[BATCH-2026-09-05-第十一批 / CARD-G6-7]`。车道：复用 `card-x2-g62b`，**前提 Z1-C 已独立 commit**。勘探 2026-09-05。协议：`.claude/rules/card-batch-protocol.md`。

# CARD-G6-7 — 完成本板反馈与当日进度（Web UI 第一个写侧动作，零 FSRS 污染）

## 〇 事实
| 事实 | 位置 |
|---|---|
| 唯一 POST 先例 `/overview/refresh`（`review_overview.py:1849`），配同源门 `:1721 _assert_same_origin` 与路径包容门 `:1605 _assert_write_target_contained`——三块承重件可直接复用 | review_overview.py |
| G6-2/G6-2b 提供持久化反馈状态机（state.notes 15s TTL，`review_app.py`） | `626f3c21` / `ced0e215` |
| per-vault state 文件已存在且带 schema_version：`scripts/daily_review_run.py:62-65`（`BACKUPS/daily-review.<vault_key>.state.json`，CARD-C1a）、`:71 schema_version 1`、`:180-191` last_recommend_credit_date 轮转账语义 | daily_review_run.py |
| 本地日翻转口径 `review_overview.py:340 _sh_day`（Asia/Shanghai），不造第二套 | review_overview.py |
| G6-6（snooze）与本卡抢同一 state 文件与动作面，**本批不排**（需用户拍板板级/节点级与时长档位）；本卡禁实现任何压制 due 的逻辑 | 总账 v2 逐卡档案 |

## 一 完成条件（AND）
- (a) 用户拍板两项写进验收单头部（默认：完成 = 移入「已完成」折叠区而非隐藏；允许未答题直接标完成但页面明示「不影响 FSRS」）。
- (b) per-vault state **加性扩展**：`daily-review.<vault_key>.state.json` 增 `board_done`（board → 本地日）字段，schema_version 加性升级并保留旧文件兼容读；损坏/缺字段按 C1a 既有降级路径处置，不 500。
- (c) 新 POST 端点复用 `:1721 _assert_same_origin` 与 `:1605 _assert_write_target_contained`（grep 证明是 import/调用复用不是复制）；零 JS 表单路径与交互壳路径都能走通。
- (d) FSRS 零触碰硬断言：完成动作前后节点 frontmatter 的 `fsrs_*` 字段与 `learning_events.jsonl` 行数逐字节 / 逐行相同（先红后绿：故意写 fsrs_due 的变异体被门拦）。
- (e) pick 侧加性消费：已完成板不再占当日推荐位；`last_recommend_credit_date` / `board_last_recommended` 的 tie-break 语义回归全绿（`daily_review_run.py:180-191` 口径不变）。
- (f) 次日自动重置：本地日翻转复用 `:340 _sh_day`；双 vault 互不影响用例。
- (g) 一轮 Codex（gpt-6-astra ultra），审查面 = 本卡 diff；§四 已裁决写入 (a) 两项默认、「不做 snooze（G6-6）」「不做跨视图五面比对（G6-8）」。

## 二 裁判命令
1. `cd <树>/backend && PYTHONDONTWRITEBYTECODE=1 $PYTEST -q -p no:cacheprovider tests/unit/test_review_overview.py tests/unit/test_review_app.py` → 全绿且含 (d) 反例先红后绿。
2. `… $PYTEST -q -p no:cacheprovider tests/regression/test_daily_review_pick.py tests/regression/test_daily_review_run.py` → 绿（W4 门下，记 blocked 计数）。
3. `… $PYTEST -q -p no:cacheprovider tests/api` → 门下目录级，与基线同（既有红登记）。
4. `git diff --stat <Z1-C commit> HEAD -- canvas-vault/` → 空（本卡零 vault 改动）。
5. `grep -n '_assert_same_origin\|_assert_write_target_contained' backend/app/api/v1/endpoints/review_overview.py` → 新端点处为调用而非重定义（定义各仍恰 1 处）。

## 三 禁改与隔离
禁改任何 FSRS 调度面：`fsrs_bridge.py`、`review_service.py`、`learning_event_log.py`；禁写节点 frontmatter；禁向 `learning_events.jsonl` 追加任何事件（完成反馈不是学习事件）；禁实现 snooze 或任何压制 due 的逻辑（G6-6 面）；禁改 `daily_review_pick.py` 排序律与 why_this_board（只允许加性读 board_done）；禁改 `tests/support/live_port_guard.py`（Z3 面）；live vault 只读；不连 7691；不改台账；不 push。

## 四 Codex / 验收单
命令同协议（`codex-prompt-CARD-G6-7.md` → `codex-review-CARD-G6-7.md`，1 轮）。验收单 `…/验收单/UAT-CARD-G6-7-<日期>.md`：DoD-3 双段；4-B「复习页上点一下『这板做完了』，它就折到下面去，今天的进度条往前走；明天自动重置；不会碰你的记忆曲线」+ felt-sense；「本卡未证明什么」必填：未做 snooze、未做跨视图比对、未测多用户；「台账待登记条目」必填（含 G6-6 待用户拍板项）。commit header ≤100 含批次标记，body 行 ≤100；不 push；跑完说「复核第十一批 Z1」。
