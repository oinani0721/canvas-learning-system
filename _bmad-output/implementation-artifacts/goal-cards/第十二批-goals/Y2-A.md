> ⚠️ 本文件是 CARD-G6-5-R 的完整卡文——车道开工后必读并逐条执行；它不是 /goal 粘贴文本。/goal 在第十二批手册 §三 Y2-A 块。
> 批次标记 `[BATCH-2026-09-05-第十二批 / CARD-G6-5-R]`。车道：`card-x2-g62b`（分支 `card/x2-g62b`，HEAD `f78bb548`，主 session 已预合主干 03ac8bf8，venv symlink 已建），**无前提**（本车道首卡；独立 commit 后同车道继续 Y2-B）。**用户已裁（2026-09-05）：D-11 = 丙——不做乙-2′，也不做「答题后触发重建」，维持 G6-3 甲案目标句「下一次定时重算后可见」；D-12 = 按更正后卡文开工——不新增 `queue_layers`，复用投影已产出的 `buckets` 五桶节点行**。勘探 2026-09-05 于主干 03ac8bf8。协议：`.claude/rules/card-batch-protocol.md`（§2.1 存档首部 / §2.2 裁判落盘 / §2.3 环境通告）。

# CARD-G6-5-R — 队列分层视图收口（复用既有 buckets 五桶节点行做两页分区渲染；不新增 queue_layers，daily_review_pick.py 零改动）

## 〇 事实
| 事实 | 位置 |
|---|---|
| 车道基点 `f78bb548` = `Merge commit '03ac8bf8' into card/x2-g62b`；`git -C card-x2-g62b diff --stat 03ac8bf8 HEAD` 输出为空（车道树与主干树逐字节相同）。本卡全部 diff 判据以 `f78bb548` 为基点；**禁用 Z1-B commit（22003dd8）作基准**——Z7-A 已对 daily_review_pick.py 做纯格式重排，拿旧 commit 比会必红 | `git log` / `git diff`（2026-09-05 实测） |
| 投影**早已生产**顶层 `buckets` = 五桶 × 节点行，每行恰为 `{node, board, why_due, fsrs_due}`；桶序常量 `BUCKET_ORDER = (new, learning_queue, due_now, due_today, future)` | `scripts/daily_review_pick.py:1003-1014`、`:252` |
| **勘误**：上一批 Z1-C 卡文 (a) 要「新增顶层 queue_layers」——与上一行同形状，等于给同一批数据开第二条链路、给 `_gate_buckets` 造两个真相源；本卡删去该前提 | 第十一批 `Z1-C.md` (a) |
| `_gate_buckets(buckets, due_groups, stats, generated_at, future_map, up_gated) -> dict[str, int]`（:348-356）已对五桶节点行做完整门禁：:429-489 逐行验形（数组 / 桶名白名单 / bucket-due_reason 自洽 / why_due 非空 / 节点互斥 / :487-489 时间语义逆检查）；:490-499 三方计数硬断言（到期三桶合计 ≠ `stats.due_nodes` → ValueError；`due_today+future` ≠ `stats.future_nodes` → ValueError）；:500-508 与 boards rollup 逐板对账。docstring :357-358 自述「why_due 的节点级展示属 G6-5 地盘，这里只门禁不渲染」——**节点行验完即丢**。唯一调用点 :714；顶层只出 `"bucket_counts": bucket_counts`（:799） | `backend/app/api/v1/endpoints/review_overview.py` |
| 旧投影无 `buckets` 键 → `bucket_counts = None`（:708）；「有 buckets 无 boards」→ ValueError（:711-713）。常量 `_BUCKET_ORDER` :325、`_DUE_BUCKETS` :327；due_nodes 只放行到期三桶且 bucket/due_reason 自洽逆检查 :192-196 | 同上 |
| 三方计数**反例已存在且已绿**：`test_buckets_layer_counts_and_cross_source_gate`（:813）内 `bad-buckets-future-drift`（:897-898）与 `bad-buckets-stats-drift`（:927-928，`st={"due_nodes": 9, "future_nodes": 2}`）。本卡不得再造同型反例冒充「先红」 | `backend/tests/unit/test_review_overview.py` |
| 消费侧现状：/overview/app 只把五桶渲染成一行计数（:285-287，`bc == null` 整行不出现）；/overview/page 同（:1109-1116，`bc is None` 整行不出现）。节点级 bucket 徽标 + why_due 已渲染 :227-229；estimated_minutes :243-244；why_this_board :250-251。JS 常量 `BUCKET_CN` / `BUCKET_ORDER` 由服务端注入 :157-158 | `review_app.py` / `review_overview.py` |
| 两页路由：`/overview/page`（review_overview.py:1152-1155，零 JS，服务端拼 HTML）；`/overview/app`（review_app.py:529-530，交互壳）；聚合 JSON `/overview`（review_overview.py:938-940） | 路由 |
| 用例数（`grep -c 'def test_'`）：test_review_app.py = 40（含 `test_js_poll_contract_wiring_g63` :2071）；test_review_overview.py = 61；tests/regression/test_daily_review_pick.py = 74（无 parametrize） | 实测 |
| `_assert_node_green`（test_review_app.py:851）挂在**每一个** node JS 门上：`len(counts)==3 / tests>0 / fail==0 / pass==tests`——内嵌 JS 若让沙箱 boot 抛错，全部 JS 门同红 | `test_review_app.py` |
| Z1-A 移交 HIGH-1：连点两次刷新时 pendingSync 结算段 :398-406 与 inflight 段 :491-500（:497 注释「手动按钮是唯一的 POST 路径 (默认裁决②: 自动轮询绝不 POST)」） | `review_app.py` |
| **勘误**：上一批 〇 表「X5-B rank 指纹覆盖 assign_bucket 函数体」不成立——`build_rank_manifest`（:756-765）只 hash `effective_rank_config(...)` 的 JSON blob，不摘任何函数体字节。本卡对 pick 零改动，此事实不再作为任何判据的依据 | `scripts/daily_review_pick.py:756-765` |
| 参照系句出处（逐字）：「本断言的参照系是 `generated_at`，不是 `now`。读侧到点标记不并入本等式的任何一个被加数。」 | `_bmad-output/研究/2026-09-05-乙2-读时重判到期-可行性设计.md:108-110`（§三） |

## 一 完成条件（AND）
- (a) **零新增投影字段**：不新增 `queue_layers` 或任何与 `buckets` 语义重叠的第二套字段；只消费既有顶层 `buckets`。裁判：`git diff f78bb548 HEAD -- scripts/daily_review_pick.py` **输出为空**（零改动，不是「只加不改」）。
- (b) **门只改返回形状不改判据**：`_gate_buckets`（:348）改为同时回传已验的五桶节点行（形态自定，例如 `(counts, rows)` 或 dict 加键；:714 调用点与 :799 输出同步改）。:429-489 验形与 :490-508 对账**逐字节不动**——裁判：`git diff f78bb548 HEAD -- backend/app/api/v1/endpoints/review_overview.py` 中该行段（按基点行号）只允许签名 / return 语句 / 新增行，判据文本行删改 = 0，逐行人核贴验收单。旧投影无 buckets 仍走 :708 None 路径，新顶层字段（如 `bucket_rows`）为 null；「有 buckets 无 boards」仍 ValueError（:711-713）。
- (c) **三方计数硬断言**：确认 :490-499 已实现，**不重写**；已有反例 `bad-buckets-stats-drift`（:927-928）/ `bad-buckets-future-drift`（:897-898）已绿，**不再造同型**。本卡新增的先红后绿只落在本卡新增面：① 透传行的逐桶 `len` 与 `bucket_counts` 不相等 → 该 vault 降级 corrupt、区块不渲染（红在「透传实现从别处取行 / 取行后被改」这条断言）；② 旧投影（无 buckets）→ 两页 HTML 中队列区块容器标记出现次数 = 0。参照系句写进 `_gate_buckets` docstring 或 :490 上方注释 + 卡文 + 验收单，逐字：「本断言的参照系是 generated_at，不是 now；读侧到点标记不并入本等式的任何被加数」（出处 乙2 设计 §三 :108-110）。**禁**把参照系改成 now——会让 :487-489 时间语义逆检查对合法投影抛 ValueError → 整库 corrupt 降级。
- (d) **两页各出一个按 new / learning_queue / due_now / due_today / future 分区的队列区块**：/overview/page（:1152）服务端拼 HTML；/overview/app（review_app.py:529）JS 渲染，复用 :157-158 注入的 `BUCKET_CN` / `BUCKET_ORDER`。缺省整块不出现——与 :285 `bc == null` / :1109 `bc is None` 同一条纪律；节点名走 `obsidian://` 深链（复用两页现有深链拼接，不新造）；零 CDN 零外部 URL：`grep -nE 'https?://' backend/app/api/v1/endpoints/review_app.py backend/app/api/v1/endpoints/review_overview.py | grep -vE 'obsidian://|localhost|127\.0\.0\.1|#|"""'` 为空。
- (e) **不重复造轮子书面登记**（验收单 file:line 逐条，本卡对以下零改动）：节点级 bucket + why_due = review_app.py:227-229；why_this_board = :250-251；estimated_minutes = :243-244；一行分层计数 = review_app.py:285-287 与 review_overview.py:1109-1116；五桶节点行 = daily_review_pick.py:1003-1014；五桶门禁与三方计数 = review_overview.py:348 / :429-499。
- (f) **Z1-A 移交 HIGH-1**（pendingSync 连点覆盖失败提示，review_app.py:398-406 / :491-500）：**修或如实登记不修，二选一**写进验收单，不得沉默。若修：改 JS 后必跑 `test_js_poll_contract_wiring_g63` 与全部 node 门；十几条门同时红 = 沙箱 boot 炸（`_assert_node_green` :851），**不得归因环境**，回退到上一个绿的 JS 状态再改。
- (g) **一轮 Codex**（gpt-6-astra ultra），审查面 = `git diff f78bb548..HEAD`（含测试）；prompt 第五节「已裁决」写入：不新增 queue_layers；daily_review_pick.py 零改动；不做万节点性能（G6-11）；(c) 参照系 = generated_at；D-11 丙（不做乙-2′ / 不做答题后触发重建）。存档首部按协议 §2.1。
- (h) **「本卡未证明什么」必填**：未做万节点规模下的分区渲染性能（G6-11）；未改任何 pick 侧语义；未验证 obsidian:// 深链在 Obsidian 端的真实打开行为（只验 HTML 文本）；HIGH-1 若选「登记不修」则该缺陷仍在。**「台账待登记条目」必填**：G6-5 → G6-5-R 改名 + 上一批卡文两处勘误（queue_layers / rank 指纹）；HIGH-1 处置结论；Codex 结论原文与模型名；用例数 40+61 → 收工实测值。

## 二 裁判命令
0. 第 0 分钟：`cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x2-g62b && git rev-parse --short=8 HEAD`（= f78bb548）`; git status --porcelain | wc -l`（= 0）`; git diff --stat 03ac8bf8 HEAD | wc -l`（= 0）；`PYTEST=$(pwd)/backend/.venv/bin/pytest`；`mkdir -p _bmad-output/审查/evidence-g65`。
1. `cd backend && set -o pipefail; PYTHONDONTWRITEBYTECODE=1 $PYTEST -q -p no:cacheprovider tests/unit/test_review_app.py tests/unit/test_review_overview.py 2>&1 | tee ../_bmad-output/审查/evidence-g65/unit-review-$(date +%Y%m%dT%H%M%S).txt; echo rc=$?` → 全绿；`grep -c 'def test_' tests/unit/test_review_app.py tests/unit/test_review_overview.py` 之和 > 101（基点 40 + 61）。
2. `… $PYTEST -q -p no:cacheprovider tests/unit/test_review_app.py::test_js_poll_contract_wiring_g63` → 绿。
3. `git diff f78bb548 HEAD -- scripts/daily_review_pick.py | wc -c` → 0。
4. `… $PYTEST -q -p no:cacheprovider tests/regression/test_daily_review_pick.py 2>&1 | tail -3` → `74 passed`。
5. (c) 先红后绿：两条新反例先在**渲染未接入前**红（贴红输出）、接入后绿；两份都 `tee` 进 evidence-g65/（文件名带 red/green + 时间戳，末行 rc）。
6. (d) 外部 URL grep → 空；旧投影 fixture 下两页 HTML 队列区块容器标记 `grep -c` = 0。
7. 门下目录级 `… $PYTEST -q -p no:cacheprovider tests/api 2>&1 | tail -3` → 摘要 `blocked=0`；红若有，在主干 03ac8bf8 复现的 = 既有，登记不算本卡。

## 三 禁改与隔离
- 禁新增 `queue_layers` / 任何 buckets 语义重叠字段；禁改 `scripts/daily_review_pick.py`（含 `assign_bucket` :425、why_due 模板、buckets 组装 :1003-1014）——判据 3 必须为空。
- 禁改 `review_overview.py:429-508` 的验形与对账判据本体（只允许改 `_gate_buckets` 返回形状 / 签名与 :714 / :799 的调用与输出）；禁把 (c) 参照系改成 now。
- 禁改 `scripts/review_rank_manifest.json` 与 rank 指纹口径（X5-B 面）。
- 禁改 `backend/app/services/learning_event_log.py` / `canvas-vault/.claude/scripts/fsrs_bridge.py` / `decay_beta.py`（Y1-A 面）；禁改 `scripts/daily_review_run.py`、禁新增任何写侧动作 / POST 端点（Y2-B 面，同车道下一卡）。
- 禁改 `backend/tests/support/live_port_guard.py` / `backend/tests/conftest.py`（Y7-A）；禁改 `lefthook.yml`（Y4）；禁改 `backend/app/services/review_service.py`（Y9-B）。
- live vault `/Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault/` 只读；禁连 7691/7687；测试 VAULTS_ROOT 走 tmp（沿 `test_review_overview.py:155 overview_env` 形态）。
- 台账只有主 session 改；不 push；`*.stderr*` 不入库；本卡改 `backend/app/**` → **不得** `LEFTHOOK_EXCLUDE=python-typecheck`（D-14）。

## 四 Codex / 验收单
命令同协议 §2；prompt `_bmad-output/审查/prompts/codex-prompt-CARD-G6-5-R.md`（五分节：一 背景 + 最小读取面写死 = review_overview.py / review_app.py / 两测试文件 + `daily_review_pick.py:1003-1014` 只读参照；二 作者自述请独立核对；三 按重要性排序的问题：① 透传行是否与 :490-499 的计数同源、能否被别处改写 ② 旧投影 None 路径与「有 buckets 无 boards」ValueError 是否仍成立 ③ JS 改动是否触及轮询 / visibilitychange / POST 路径 ④ HIGH-1 处置是否如实 ⑤ 参照系句是否落在代码注释；四 输出格式；五 边界 + 已裁决）。存档 `_bmad-output/审查/codex-review-CARD-G6-5-R.md` 首部按协议 §2.1 六行 blockquote；顺序固定「代码与门全部定稿 → 跑全部裁判 → 送 Codex → 之后只改 _bmad-output」，审后再改代码 = 失绑须登记。0 字节重发一次，再 0 字节 → 主 session 人审替代。验收单 `_bmad-output/验收单/UAT-CARD-G6-5-R-<日期>.md`：DoD-3 双段（4-A Claude 已代验 / 4-B 你来验，4-B 零技术词）；4-B「复习页把卡按『新学 / 学习中 / 现在到期 / 今天到期 / 以后』分成五块，每块下面能看到具体是哪些卡，点卡名能跳到 Obsidian 里那一页」+ felt-sense；「本卡未证明什么」「台账待登记条目」必填。commit header ≤100 含批次标记，body 行 ≤100（`wc -m`）；不 push；**独立 commit 后同车道继续 Y2-B**；跑完说「复核第十二批 Y2」。
