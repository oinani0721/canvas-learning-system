> ⚠️ 本文件是 CARD-G6-5 的完整卡文——车道开工后必读并逐条执行；它不是 /goal 粘贴文本。/goal 在第十一批手册 §三 Z1-C 块。
> 批次标记 `[BATCH-2026-09-05-第十一批 / CARD-G6-5]`。车道：复用 `card-x2-g62b`，**前提 Z1-B 已独立 commit**。勘探 2026-09-05。协议：`.claude/rules/card-batch-protocol.md`。

# CARD-G6-5 — 队列分层视图收口：new / learning / due_now / due_today / future 分区 + 分层自洽硬断言

## 〇 事实
| 事实 | 位置 |
|---|---|
| 依赖全在主干：G3-6a 桶位/why_due = `0e6125b9`；G3-6b-R1 = `d33f8d1f`；G3-6b-R2 = `23275b82`；G6-1+G6-4 = `866778a5`；G6-2 = `626f3c21`；G6-2b = `ced0e215` | git log |
| 投影已生产五字段：bucket / why_due / bucket_counts / why_this_board / estimated_minutes，且有门禁；但消费侧只把五桶渲染成**一行计数**（`review_app.py:285-287`），new / future 两桶在节点级完全不可见（`review_overview.py:192-193` 只允许到期三桶进 due_nodes） | 两文件 |
| G6-5 的一部分交付物已被提前吃掉：节点级 bucket + why_due 已在两页渲染（`review_app.py:227-229`）、板级 why_this_board / estimated_minutes 已渲染（`:243-244` / `:250-251`）、投影新鲜度 stale 四态徽标已有。**真实剩余面 = 按桶分区的队列视图 + new/future 两桶节点级缺失** | review_app.py |
| 桶位判定律与 why_due 模板在 `scripts/daily_review_pick.py`（S1/S3 段），X5-B 的 rank 指纹覆盖其函数体——改函数体即改 sha | daily_review_pick.py + review_rank_manifest.json |
| 两页：`/overview/page`（零 JS）与 `/overview/app`（交互壳）；节点名走 `obsidian://` 深链，零 CDN 零外部 URL | review_overview.py:938 / :1152 |

## 一 完成条件（AND）
- (a) 投影侧**只加不改**：due_nodes 之外新增顶层 `queue_layers`（new / learning_queue / due_now / due_today / future 五桶各给节点行，字段沿用既有 node / bucket / why_due / fsrs_due 形状）；`daily_review_pick.py` 的 S1 判桶与 S3 why_due 模板**函数体逐字节不动**（`git diff <Z1-B commit> HEAD -- scripts/daily_review_pick.py` 只含加性追加，非加性行 0）。
- (b) 门禁先红后绿：`review_overview.py` 为 queue_layers 加独立形状门（桶名白名单、bucket 与 due_reason 自洽、why_due 非空串）；旧投影（无该键）走 None 路径、顶层字段为 null，不伪造分层数字。
- (c) 硬断言：`sum(len(queue_layers[*]))` == bucket_counts 各桶计数 == stats 到期总数，三者任一不等 → 400/降级而非静默渲染；反例 fixture（计数与行数不一致的投影）先红。
- (d) 两页渲染各出一个按桶分区的队列区块，缺省整块不出现（沿 bucket_counts 缺省纪律）；节点名走 obsidian:// 深链；零 CDN 零外部 URL（grep 证明）。
- (e) 不重复造轮子的书面登记：验收单点名 why_due / why_this_board / estimated_minutes / stale 徽标已由 G6-4 / G3-6b / G6-2 交付，本卡零改动（file:line 逐条）。
- (f) 一轮 Codex（gpt-6-astra ultra），审查面 = 本卡 diff（`git diff <Z1-B commit>..HEAD`）；§四 已裁决写入「daily_review_pick.py 只加不改」「不做万节点性能（G6-11）」。

## 二 裁判命令
1. `cd <树>/backend && PYTHONDONTWRITEBYTECODE=1 $PYTEST -q -p no:cacheprovider tests/unit/test_review_app.py tests/unit/test_review_overview.py` → 全绿且用例数 > Z1-B 时。
2. `… $PYTEST -q -p no:cacheprovider tests/regression/test_daily_review_pick.py` → 74 绿不回退（rank sha 不变：`grep -c` manifest 版本未动）。
3. `git diff <Z1-B commit> HEAD -- scripts/daily_review_pick.py | grep -c '^[-][^-]'` → 0（无删除行）；S1/S3 段函数体 sha 前后同。
4. 反例 fixture：计数≠行数的投影 → 400/降级（先红后绿留证）。
5. `grep -rn -E 'https?://' backend/app/api/v1/endpoints/review_app.py backend/app/api/v1/endpoints/review_overview.py | grep -v -E 'obsidian://|localhost|127\.0\.0\.1|#|"""'` → 空。
6. 门下目录级 `… $PYTEST -q -p no:cacheprovider tests/api` → 与基线同（既有红登记）。

## 三 禁改与隔离
禁改 `daily_review_pick.py` 桶位判定律与 why_due / why_this_board 生成函数体（只允许加性追加 queue_layers 输出）；禁改 `scripts/review_rank_manifest.json` 与 rank 指纹口径（X5-B 面）；禁改 `learning_event_log.py` / `fsrs_bridge.py`（Z2 面）；**禁新增任何写侧动作 / POST 端点**（Z1-D 面）；禁改 `tests/support/live_port_guard.py`（Z3 面）；live vault 只读；不连 7691；不改台账；不 push。

## 四 Codex / 验收单
命令同协议（`codex-prompt-CARD-G6-5.md` → `codex-review-CARD-G6-5.md`，1 轮，0 字节重发一次后主 session 人审）。验收单 `…/验收单/UAT-CARD-G6-5-<日期>.md`：DoD-3 双段；4-B「复习页把卡按『新学 / 学习中 / 现在到期 / 今天到期 / 以后』分成五块，每块下面能看到具体是哪些卡」+ felt-sense；「本卡未证明什么」必填：未做万节点规模下的分区渲染性能（G6-11）；「台账待登记条目」必填。commit header ≤100 含批次标记，body 行 ≤100；不 push。**commit 后同车道继续 Z1-D。**
