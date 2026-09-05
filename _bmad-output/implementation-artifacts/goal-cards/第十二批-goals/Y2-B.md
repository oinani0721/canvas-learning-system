> ⚠️ 本文件是 CARD-G6-7 的完整卡文——车道开工后必读并逐条执行；它不是 /goal 粘贴文本。/goal 在第十二批手册 §三 Y2-B 块。
> 批次标记 `[BATCH-2026-09-05-第十二批 / CARD-G6-7]`。车道：`card-x2-g62b`（分支 `card/x2-g62b`，基线 HEAD `f78bb548`，主 session 已预合主干 03ac8bf8，venv symlink 已建），**前提 Y2-A（CARD-G6-5-R）已独立 commit 且工作树干净**——开工记下该 commit SHA 为 `BASE`，本卡全部 diff 判据以 `BASE` 为基点。**用户已裁（2026-09-05，D-1~D-7 全按默认）：完成 = 移入『已完成』折叠区（不是隐藏）；允许未答题直接标完成，但页面明示『不影响 FSRS』；D-8 = G6-6 snooze 不排本批（本卡硬边界仍「禁实现 snooze」；D-8 两子项默认 = 板级粒度 / 两档「今晚 + 明天」只写进第十三批卡文）；D-11 = 丙（禁乙-2′ / 禁答题后触发重建）**。勘探 2026-09-05 于主干 03ac8bf8。协议：`.claude/rules/card-batch-protocol.md`（§2.1 存档首部 / §2.2 裁判落盘 / §2.3 环境通告）。

# CARD-G6-7 — 完成本板反馈与当日进度（Web UI 第一个写侧动作，零 FSRS 污染；行锚按主干 03ac8bf8 重取）

## 〇 事实
| 事实 | 位置 |
|---|---|
| 基线 `f78bb548` 与主干 03ac8bf8 树逐字节相同；本卡基点 `BASE` = Y2-A 独立 commit（开工实测记下） | `git diff --stat 03ac8bf8 f78bb548` 为空 |
| per-vault state：`state_path()` :57-61 → `BACKUPS / f"daily-review.{_vault_key()}.state.json"`（:61）；`BACKUPS = REPO / "backups"`（:38，**不在 vault 内**）；`_vault_key()` :52-54 唯一定义点 `send_bark.vault_key(VAULT.resolve().name)`（规则被 test_daily_review_run.py:519 `test_vault_key_slug_rules` 锁死）。`load_state()` :64-84：缺文件返回 `{"schema_version": 1, "board_last_recommended": {}}`（:67）；结构错型 `isinstance` 检查 :72 → ValueError；损坏 / 错型 → quarantine `.corrupt-<ts>` :77-80 → 重建默认 :83。`save_state` :86 原子写（os.replace，docstring :9-12 A4）。**勘误**：上一批卡文 :62-65 / :71 / :180-191 全部因 Z7-A ruff format 漂移 | `scripts/daily_review_run.py` |
| `board_done` 全仓不存在（`grep -rn board_done scripts backend/app` = 0 命中）——纯 greenfield | 实测 |
| credited_today 判定 :171-176（:172 marker `last_recommend_credit_date == today`；:175 `today in board_last_recommended.values()` 兜底）；落账 :182-183。本卡**逐字节不动** | `daily_review_run.py:171-183` |
| runner 进入 pick 的唯一口 :152 `picker.build_payload(VAULT, now, st["board_last_recommended"], picker.load_decay(VAULT))`；pick 侧签名 `build_payload(vault, now, board_last_recommended, decay, manifest_path=None)` :927 | `daily_review_run.py:152` / `daily_review_pick.py:927` |
| runner `today` 口径 :215-216 `local = now.astimezone(); today = local.date().isoformat()`（机器本地时区）；Web 侧 `_sh_day(ts)` :340-346 固定 Asia/Shanghai（`_TZ_SHANGHAI` :85，缺 tzdata 退化 +8 :87）。本卡 Web 侧新逻辑只复用 `_sh_day`，**不改 runner :215-216**（两口径分叉的取证归 Y3-B） | 两文件 |
| 唯一后端 POST：`@review_overview_router.post("/overview/refresh")` :1849-1852，handler `review_overview_refresh(request, vault_id: str = Form(...), redirect: str | None = Form(None))` :1853-1857；:1886 `_assert_same_origin(request)`；`_refresh_target(vault_id)` 内 :1689 `_assert_write_target_contained(match, vaults_root)`；失败回原样 4xx/5xx（:1882-1883「静默假成功的浏览器版本」纪律）。两个 def 各恰 1 处（:1721 / :1605），调用各恰 1 处（:1886 / :1689） | `review_overview.py` |
| 零 JS 表单先例 `_refresh_form_html(vault_id, action)` :1060-1071（hidden `vault_id` + hidden `redirect=page` → 303 PRG） | 同上 |
| 前端唯一 POST：review_app.py:497-498（:497 注释「手动按钮是唯一的 POST 路径 (默认裁决②: 自动轮询绝不 POST)」）；同库 inflight 防抖 :491-492；pendingSync 结算 :398-406 | `review_app.py` |
| G6-3 ④ 门：test_review_app.py:2137 `test("④ 自动轮询绝不 POST: 连跑多轮, 沙箱收到的 POST 次数恒为 0")`，:2141 `assert.equal(b.calls.post, 0)`，驱动 timer 连跑 5 轮；③ :2123-2135 驱动 `document::visibilitychange`。**手动按钮 POST 不在 ④ 的计数面** | `test_review_app.py` |
| 投影层若剔除已完成板会撞 `_gate_buckets` :490-499（到期三桶合计 == `stats.due_nodes`）→ 本卡**不**在投影层压制，只做 Web 渲染层折叠 + pick 侧加性读 | `review_overview.py:490-499` |
| 用例数（`grep -c 'def test_'`）：test_review_app.py 40 / test_review_overview.py 61（Y2-A 收工后重测）/ tests/regression/test_daily_review_pick.py 74 / test_daily_review_run.py 32（含 C1a 双 vault 用例 :386 `test_two_vaults_same_day_push_and_state_isolated`，fixture `_vault` :36、`_patch_runner` :47-52、`monkeypatch.setattr(runner.send_bark, "send", …)` :132） | 实测 |

## 一 完成条件（AND）
- (a) **三项用户裁决抄进验收单头部并标「已裁」**：完成 = 移入『已完成』折叠区；允许未答题直接标完成但页面明示『不影响 FSRS』；D-8 不做 snooze / D-11 丙不做乙-2′。抄录即完成 (a)，直接进 (b)。
- (b) **per-vault state 加性扩展**：新增 `board_done: {<board>: "<YYYY-MM-DD>"}`；`schema_version` 加性升级（当前 1，:67 与 :83 两处默认值同步改；旧文件兼容读——缺 `board_done` 视为 `{}`，**不做迁移器**）；损坏 / 错型仍走 :69-84 隔离重建（:72 isinstance / :77-80 quarantine），不 500；`board_done` 值非 dict 时按错型处置（与 :72 同型**追加**一条 isinstance，:72 原行不动）。Web 侧写点与 runner 同一文件同一 schema：state 路径派生**必须与 :57-61 同源**（import runner 模块或复用 `send_bark.vault_key`），禁手拼第二套 key 规则；写入用 os.replace 原子写（沿 :86 形态）。runner 每小时 :05 档与用户点击的并发窄窗如实登记，不在本卡解。
- (c) **新 POST 端点**（放 review_overview.py，路径自定如 `/overview/board-done`）复用 :1721 `_assert_same_origin` 与 :1605 `_assert_write_target_contained`（经 `_refresh_target` 或同型解析函数），裁判 `grep -c 'def _assert_same_origin'` / `grep -c 'def _assert_write_target_contained'` 各仍恰 1，调用处各 ≥ 2（原 + 新）。零 JS 表单路径（沿 `_refresh_form_html` :1060-1071 形态，`redirect=page` → 303）与交互壳路径（review_app.py 手动按钮，沿 :491-500 inflight 形态）都走通；失败回原样 4xx/5xx。页面文案含「不影响 FSRS」字样（grep 贴证）。
- (d) **FSRS 零触碰硬断言**：完成动作前后，tmp vault 内全部节点 md 的 `fsrs_*` frontmatter 字段逐字节相同 + `learning_events.jsonl`（若存在）行数与 sha 相同。先红后绿：测试内 monkeypatch 一个「顺手写 fsrs_due」的对照实现替换被测写点 → 门红；还原 → 绿。两份输出 `tee` 落 `_bmad-output/审查/evidence-g67/`（red/green + 时间戳 + 末行 rc）。
- (e) **pick 侧加性消费**：`build_payload` 加**可选**参数（默认 None，:927 既有 4 个位置参数语义不变），runner :152 传 `st.get("board_done")`；值 == today 的板不占当日榜首推荐位。credited_today :171-176 与落账 :182-183 逐字节不动（裁判：`git diff BASE HEAD -- scripts/daily_review_run.py` 各 hunk 头 `@@ -a,b` 与 171-183 无交集，逐行人核）；`git diff BASE HEAD -- scripts/daily_review_pick.py | grep -c '^-[^-]'` = 0（只加性），不动 `assign_bucket` :425 / buckets 组装 :1003-1014 / why_this_board。tests/regression/test_daily_review_pick.py 74 不回退。
- (f) **次日自动重置**：Web 侧「今天是否已完成」判定 = `board_done[board] == str(_sh_day(<now 的 UTC-Z 串>))`（复用 :340，不造第二套时区）；隔日值自然失效，不删旧键（加性）；双 vault 互不影响用例（沿 test_daily_review_run.py:386 C1a 形态，两 tmp vault 各自 state 文件）。
- (g) **写侧不撞轮询门的书面证明**：新 POST 只由显式点击 / 表单提交触发，不进 timer / `visibilitychange` 分支；`test_js_poll_contract_wiring_g63` 绿（④ :2141 `calls.post == 0` 未被破坏）；review_app.py 中 `method: "POST"` 出现次数 1 → 2 且两处都在按钮 handler 内（grep -n 贴证）。
- (h) **一轮 Codex**（gpt-6-astra ultra），审查面 = `git diff BASE..HEAD`；prompt 第五节已裁决：(a) 三项；不做 snooze（G6-6 / D-8）；不做跨视图五面比对（G6-8）；不做乙-2′ / 答题后触发重建（D-11 丙）；不写 frontmatter / 不追加 learning_events。存档首部按协议 §2.1。
- (i) **「本卡未证明什么」必填**：未做 snooze；未做跨视图一致性（G6-8）；未解 runner 与 Web 同文件并发写的强一致（窄窗只登记）；未在真实 launchd 档位验证 board_done 对当日推荐的影响（只在 tmp vault 用例）；未做多用户。**「台账待登记条目」必填**：G6-7 = 首个 Web 写侧动作上线；state `schema_version` 1 → 2（旧文件兼容读已覆盖，无迁移器）；runner / Web 并发窄窗；G6-6 前提已备（`board_done` 键空间已定；D-8 默认 = 板级 / 两档）；Codex 结论原文与模型名。

## 二 裁判命令
0. 第 0 分钟：`cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x2-g62b && git log --oneline -1`（Y2-A 的 commit 在顶）`; git status --porcelain | wc -l`（= 0）`; BASE=$(git rev-parse HEAD); echo $BASE`；`PYTEST=$(pwd)/backend/.venv/bin/pytest`；`mkdir -p _bmad-output/审查/evidence-g67`。
1. `cd backend && set -o pipefail; PYTHONDONTWRITEBYTECODE=1 $PYTEST -q -p no:cacheprovider tests/unit/test_review_overview.py tests/unit/test_review_app.py 2>&1 | tee ../_bmad-output/审查/evidence-g67/unit-review-$(date +%Y%m%dT%H%M%S).txt; echo rc=$?` → 全绿，用例数 > Y2-A 收工数；(d) 反例先红后绿两份另 tee。
2. `… $PYTEST -q -p no:cacheprovider tests/unit/test_review_app.py::test_js_poll_contract_wiring_g63` → 绿。
3. `… $PYTEST -q -p no:cacheprovider tests/regression/test_daily_review_pick.py tests/regression/test_daily_review_run.py 2>&1 | tail -3` → 74 + 32 起步、新增 ≥ 3（board_done 兼容读 / 错型隔离 / 已完成板不占榜首）；摘要 `blocked=0`。
4. `git diff $BASE HEAD -- scripts/daily_review_run.py | grep '^@@'` → 每个 hunk 的旧行区间与 171-183 无交集，贴验收单；`git diff $BASE HEAD -- scripts/daily_review_pick.py | grep -c '^-[^-]'` → 0。
5. `grep -c 'def _assert_same_origin' backend/app/api/v1/endpoints/review_overview.py` → 1；`grep -c 'def _assert_write_target_contained' …` → 1；`grep -n '_assert_same_origin(\|_assert_write_target_contained(' …` → 各 ≥ 2 处调用。
6. `git diff --stat $BASE HEAD -- canvas-vault/ | wc -l` → 0；`git status --porcelain -- canvas-vault/ | wc -l` → 0。
7. 门下目录级 `… $PYTEST -q -p no:cacheprovider tests/api 2>&1 | tail -3` → 摘要 `blocked=0`；红若有，在主干 03ac8bf8 复现的 = 既有，登记不算本卡。

## 三 禁改与隔离
- 禁改 FSRS 调度面：`canvas-vault/.claude/scripts/fsrs_bridge.py` / `decay_beta.py`（Y1-A 面；且 wrapper `daily-review-wrapper.sh:98-106` 对这两份做 live↔树 cmp，不一致 exit 78 整链停摆）、`backend/app/services/review_service.py`（Y9-B）、`backend/app/services/learning_event_log.py`（Y1-A）。
- 禁写节点 frontmatter；禁向 `learning_events.jsonl` 追加任何事件（完成反馈不是学习事件）。
- 禁实现 snooze 或任何压制 due 的逻辑（D-8）；禁实现乙-2′ / 「答题后触发重建」（D-11 丙）。
- 禁把新 POST 接进 timer / `visibilitychange` 路径（撞 `test_js_poll_contract_wiring_g63` ④）。
- 禁改 `daily_review_pick.py` 排序律 / why_this_board / `assign_bucket` :425 / buckets 组装 :1003-1014（只允许 `build_payload` 加可选参数 + 榜首过滤的加性 hunk）；禁改 `daily_review_run.py:171-183` 与 :215-216。
- 禁在投影层剔除已完成板（撞 `_gate_buckets` :490-499）；禁改 `review_overview.py:429-508` 判据本体。
- 禁改 `backend/tests/support/live_port_guard.py` / `backend/tests/conftest.py`（Y7-A）；禁改 `lefthook.yml`（Y4）。
- live vault 只读（测试 VAULTS_ROOT / BACKUPS 全走 tmp：`test_review_overview.py:155 overview_env`、`test_daily_review_run.py:47-52 _patch_runner` 形态）；禁连 7691/7687；台账只有主 session 改；不 push；`*.stderr*` 不入库；本卡改 `backend/app/**` → **不得** `LEFTHOOK_EXCLUDE=python-typecheck`（D-14）。

## 四 Codex / 验收单
命令同协议 §2；prompt `_bmad-output/审查/prompts/codex-prompt-CARD-G6-7.md`（五分节：一 背景 + 最小读取面写死 = review_overview.py 新端点与 :1605/:1721/:1849-1890 / review_app.py 按钮 handler 与 :491-500 / daily_review_run.py :57-84、:124-183 / daily_review_pick.py :927 起的 build_payload / 两测试文件；二 作者自述请独立核对；三 按重要性排序的问题：① 新 POST 是否真复用两道门而非复制、失败是否回原样 4xx/5xx ② state 路径派生是否与 runner :57-61 同源、错型是否走 :69-84 ③ 新 POST 有无任何路径能被 timer / visibilitychange 触发 ④ FSRS 零触碰门是否能在对照输入下红 ⑤ :171-183 是否逐字节未动 ⑥ 「已完成」判定是否复用 `_sh_day`；四 输出格式；五 边界 + 已裁决）。存档 `_bmad-output/审查/codex-review-CARD-G6-7.md` 首部按协议 §2.1；顺序固定「代码与门全部定稿 → 跑全部裁判 → 送 Codex → 之后只改 _bmad-output」，审后再改代码 = 失绑须登记。验收单 `_bmad-output/验收单/UAT-CARD-G6-7-<日期>.md`：DoD-3 双段（4-B 零技术词）；头部抄三项已裁；4-B「点一下『这板做完了』，它折到下面的『已完成』区，今天的进度往前走；明天自动回来；页面写着不影响记忆曲线」+ felt-sense；「本卡未证明什么」「台账待登记条目」必填。commit header ≤100 含批次标记，body 行 ≤100（`wc -m`）；不 push；跑完说「复核第十二批 Y2」。
