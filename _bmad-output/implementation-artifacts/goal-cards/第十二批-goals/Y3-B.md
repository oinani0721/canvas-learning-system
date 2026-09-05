> ⚠️ 本文件是 CARD-G6-9a 的完整卡文——车道开工后必读并逐条执行；它不是 /goal 粘贴文本。/goal 在第十二批手册 §三 Y3-B 块。
> 批次标记 `[BATCH-2026-09-05-第十二批 / CARD-G6-9a]`。车道：`card-z5-canary`（分支 `card/z5-canary`，基线 HEAD `03ac8bf8` = 主干 ff，venv symlink 已建），**前提 Y3-A（CARD-G2-9）已独立 commit 且工作树干净**——开工记下该 commit SHA 为 `BASE`。无用户裁决项（G6-9b「Bark degraded 徽标」本批不排，已登记）。勘探 2026-09-05 于主干 03ac8bf8。协议：`.claude/rules/card-batch-protocol.md`（§2.1 存档首部 / §2.2 裁判落盘 / §2.3 环境通告 / §3 fsrs_bridge·decay_beta 部署铁律）。

# CARD-G6-9a — 时区 / 午夜 / 唤醒补跑边界矩阵（零产品代码取证卡；只新增一个测试文件，发现真缺陷 = 如实红 + 登记不修）

## 〇 事实
| 事实 | 位置 |
|---|---|
| 基点 `BASE` = Y3-A 独立 commit（开工实测记下）；`backend/tests/regression/test_g6_9_boundary_matrix.py` **不存在** | `git` / `ls` |
| **两套时钟并存（实测）**：runner :215-216 `local = now.astimezone(); today = local.date().isoformat()`（机器本地时区）；pick :1023 `"generated_at": now.astimezone().isoformat(timespec="seconds")`（机器本地）；pick 桶位 due_today 用 `_TZ_SHANGHAI`（:236-243，`ZoneInfo("Asia/Shanghai")`，缺 tzdata 退化 +8）；Web 侧 `_sh_day(ts)` :340-346 固定 Asia/Shanghai（`_TZ_SHANGHAI` :85，退化 :87）。矩阵要暴露的正是「机器时区 ≠ Asia/Shanghai 时 `today` 与 `_sh_day` 是否分叉」——**红了是发现，不是失败** | `scripts/daily_review_run.py` / `scripts/daily_review_pick.py` / `backend/app/api/v1/endpoints/review_overview.py` |
| 唤醒补跑机制已在：A4 时间门 `PUSH_WINDOW = (dtime(9, 5), dtime(21, 0))` :40；`skip-window` 分支 :240-241（RunAtLoad 早触发 / 21:00 后唤醒只落盘）；`ensure_payload` :124-125 docstring「当日 payload: 没有才生成 (生成过则复用 — 补跑只补推送)」；`first_gen_today = st.get("last_generate_date") != today` :136；:162 `st["last_generate_date"] = today` 落账；缓存门 :141-145（payload_sha256 + `next_due_utc` + `_nodes_max_mtime`）。缺的是**实测证据**不是实现 | `scripts/daily_review_run.py` |
| Bark 失败：:245 `rc = send_bark.send(noti, payload.get("vault_id") or VAULT.resolve().name)`；rc ≠ 0 且 ≠ 2 → :257-259 `st["last_result"] = "generated_push_failed"; st["last_error"] = "bark-send"`；md/json 由 `ensure_payload` 先落盘（:152 之后），推送在后 | 同上 |
| `backend/app` 对 runner state 文件零引用（`git grep 'last_error\|last_push' -- backend/app` 与 daily-review 相关命中 0）；`grep -c degraded review_overview.py` = 0 → 「推送失败在 Web UI / /overview JSON 可见」当前**客观不成立**，属可登记的开放面（G6-9b） | 实测 |
| 既有 fixture 形态：`_vault(tmp_path, nodes, name)` :36；`_patch_runner(monkeypatch, vault, tmp_path)` :47-52（setattr `VAULT` / `BACKUPS`）；`monkeypatch.setattr(runner.send_bark, "send", _sentinel)` :132；`monkeypatch.setattr(runner, "PUSH_WINDOW", (dtime(0, 0), dtime(23, 59, 59)))` :401；`--now` 参数 :207 供 12 场景矩阵用。32 def | `backend/tests/regression/test_daily_review_run.py` |
| 现存含 Asia/Shanghai 断言的测试只有 `tests/unit/test_review_overview.py`（Y2 独占）与 `tests/skills/test_g5_6_clear_inbox.py` → TZ 矩阵**必须落新文件** | `git grep -ln 'Asia/Shanghai' -- backend/tests` |
| launchd：plist `scripts/launchd/com.canvas.daily-review.plist`（Label :10-11 `com.canvas.daily-review`，12 个 `Hour` 档；`StandardErrorPath` :20 `/Users/Heishing/Library/Logs/canvas-daily-review.err.log`、`StandardOutPath` :22 `/Users/Heishing/Library/Logs/canvas-daily-review.log`）；wrapper `scripts/launchd/daily-review-wrapper.sh`（:98-106 对 `decay_beta.py` / `fsrs_bridge.py` 逐字节 cmp，不一致 exit 78） | `scripts/launchd/` |
| live 现状（设计稿 §0）：`canvas-vault/outputs/今日复习.json` generated_at 停在 11:08:38 而 12:05 / 13:05 档 wrapper 都跑了——**预期**（:136 每日只生成一次，:162 落账，后续档只可能补推送），不是停摆；本卡 (c) 的用例②正是把这条预期写成门 | 设计稿 §0 |
| 用例数：tests/regression/test_daily_review_pick.py 74 / test_daily_review_run.py 32 | 实测 |

## 一 完成条件（AND）
- (a) **只新增 `backend/tests/regression/test_g6_9_boundary_matrix.py`**；零产品代码硬断言：`git diff --stat BASE HEAD -- backend/app backend/lib scripts canvas-vault` 为空。TZ 参数化 ≥ 3 且含 ≥ 1 个 DST 时区（例 `America/New_York` / `Europe/London` + `Asia/Shanghai` + `UTC`）：用 `TZ=<zone>` 子进程（或 `time.tzset` + monkeypatch）让 runner :215 的 `now.astimezone()` 落在该时区，断言 runner `today` 与 `review_overview._sh_day(<generated_at 换算成 UTC-Z 串>)`（只读 `from app.api.v1.endpoints.review_overview import _sh_day`，零修改）是否同日；同时断言 pick 的 due_today 归日（`_TZ_SHANGHAI` :236-243）与 `_sh_day` 一致。**不一致即如实红**，验收单逐条定性（哪个时区 / 哪个时刻 / 哪两个口径分叉），**不修**。
- (b) **午夜跨界**：23:59（Asia/Shanghai）生成的投影 fixture，用 00:01 参照时钟复算 stale 判定与 due_today / future 归属，断言与 `_sh_day` :340 / `_gate_buckets` :348 口径自洽（`_gate_buckets` 只 import 调用，不改；fixture 形态沿 test_review_overview.py `_mk_vault` :142 但**落新文件**）。
- (c) **唤醒补跑**：tmp VAULT（沿 `_vault` :36 / `_patch_runner` :47）+ `monkeypatch.setattr(runner.send_bark, "send", …)`；三条：① 窗口外（`--now` 落 21:30）→ `push == "skip-window"`（:240-241），md/json 已落盘；② 同日第二次 `main()`（窗口内）→ `ensure_payload` 走 cached（:125 语义，`generated_at` 不变），只补推送不重生成；③ 隔日首档 → 重新生成（`first_gen_today` :136 翻转）。真实 launchd 只做**只读取证**：`launchctl list | grep com.canvas.daily-review` + `tail -n 200 /Users/Heishing/Library/Logs/canvas-daily-review.log`（plist :22）落 evidence-g69/，**不触发任何一档**。
- (d) **Bark 失败注入（runner 侧）**：monkeypatch `send` 返回 1 → 断言 state `last_error == "bark-send"`（:259）、`last_result == "generated_push_failed"`（:258）且 md/json 在推送前已落盘（存在性 / mtime 断言）；用 `git grep -n 'last_error' -- backend/app` = 0 命中 证明 backend/app 不读该 state → 验收单书面登记「推送失败当前在 Web UI 与 /overview JSON 均不可见」，徽标交付移交 CARD-G6-9b（本批不排）。
- (e) **发现真缺陷的处置 = 「如实红 + 登记不修」**：红用例保留（可 `xfail(strict=True)` 并在 reason 写明归哪张卡，沿第十批 X3 先例），不得为了绿而改断言、改产品代码或删用例。
- (f) **全部裁判输出落 `_bmad-output/审查/evidence-g69/`**（pytest `-rA` 汇总 / launchctl list / 日志尾 / blocked 计数，带时间戳 + 末行 `rc=`）；验收单只引用路径与末行，不自述数字。
- (g) **一轮 Codex**（gpt-6-astra ultra），审查面 = 新测试文件；已裁决：不改产品代码；不做 G6-9b 徽标；不触发 launchd。存档首部按协议 §2.1。
- (h) **「本卡未证明什么」必填**：未改任何产品代码（因此未修任何发现的分叉）；未做 UI degraded 徽标（G6-9b）；未在真实 launchd 档位触发补跑（只读日志）；未覆盖非 macOS；未做万节点规模；(a) 全绿也只证明「本机 tzdata 下这 ≥ 3 个时区」。**「台账待登记条目」必填**：G6-9 拆为 9a / 9b，9b 本批不排；TZ 矩阵结论（分叉 / 不分叉逐条）；「推送失败 UI 不可见」开放面；live generated_at 11:08:38 = 预期的书面结论；Codex 结论原文与模型名。

## 二 裁判命令
0. 第 0 分钟：`cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z5-canary && git log --oneline -1`（Y3-A 的 commit 在顶）`; git status --porcelain | wc -l`（= 0）`; BASE=$(git rev-parse HEAD); echo $BASE`；`PYTEST=$(pwd)/backend/.venv/bin/pytest`；`mkdir -p _bmad-output/审查/evidence-g69`；`shasum -a 256 /Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault/outputs/今日复习.json /Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault/outputs/今日复习.md | tee _bmad-output/审查/evidence-g69/live-outputs-sha-before.txt`。
1. `cd backend && set -o pipefail; PYTHONDONTWRITEBYTECODE=1 $PYTEST -q -p no:cacheprovider -rA tests/regression/test_g6_9_boundary_matrix.py 2>&1 | tee ../_bmad-output/审查/evidence-g69/matrix-$(date +%Y%m%dT%H%M%S).txt; echo rc=$?` → 收集数 ≥ 3 × TZ 参数 + 午夜 1 + 补跑 3 + Bark 1；红的逐条 nodeid 贴验收单并定性；末行 `blocked=0`。
2. `… $PYTEST -q -p no:cacheprovider tests/regression/test_daily_review_pick.py tests/regression/test_daily_review_run.py 2>&1 | tail -3` → 74 + 32 不回退。
3. `git diff --stat $BASE HEAD -- backend/app backend/lib scripts canvas-vault | wc -l` → 0。
4. `shasum -a 256 <同上两文件> | diff - _bmad-output/审查/evidence-g69/live-outputs-sha-before.txt` → 空；`git status --porcelain -- canvas-vault/ | wc -l` → 0（live vault 不在 git 内的文件以 sha 对账为准）。
5. `launchctl list | grep com.canvas.daily-review | tee _bmad-output/审查/evidence-g69/launchctl-list-$(date +%Y%m%dT%H%M%S).txt`（只读）；`tail -n 200 /Users/Heishing/Library/Logs/canvas-daily-review.log | tee _bmad-output/审查/evidence-g69/launchd-log-tail-$(date +%Y%m%dT%H%M%S).txt`（只读）。

## 三 禁改与隔离
- 禁 `launchctl kickstart` / `launchctl start` / `launchctl unload` / `launchctl bootout`；禁直接跑 `scripts/launchd/daily-review-wrapper.sh` 或 `daily_review_run.py --vault <live>`（真跑一档 = live vault 写 + 真发推 = 阻断级）；只允许 `launchctl list` 与读日志文件。
- 禁真调 `send_bark.send`（必须 monkeypatch）；禁调 `osascript`（弹系统通知）；跑 runner 用例前确认 `send` 已被替换。
- 禁改 `backend/app/**` / `backend/lib/**` / `scripts/**` / `canvas-vault/**` 任何既有文件（本卡零产品代码）；新增只允许一个测试文件。
- 禁改 `review_app.py` / `review_overview.py` / `test_review_app.py` / `test_review_overview.py`（Y2）；禁改 `daily_review_pick.py` / `daily_review_run.py`（Y2-B 加性面）；禁改 `fsrs_bridge.py` / `decay_beta.py`（Y1-A + wrapper cmp 门）。
- 禁改 `backend/tests/support/live_port_guard.py` / `backend/tests/conftest.py`（Y7-A）；禁改 `lefthook.yml`（Y4）。
- 禁连 7691 / 7687；台账只有主 session 改；不 push；`*.stderr*` 不入库。D-14：本卡不改 `backend/app/**`，若 pyright 拦在**非本卡文件**允许带存档的 `LEFTHOOK_EXCLUDE=python-typecheck` 并贴原始输出。

## 四 Codex / 验收单
命令同协议 §2；prompt `_bmad-output/审查/prompts/codex-prompt-CARD-G6-9a.md`（五分节：一 背景 + 最小读取面写死 = 新测试 / `daily_review_run.py` :124-183、:202-262 / `daily_review_pick.py` :236-243、:1023 / `review_overview.py` :83-88、:340-346；二 作者自述请独立核对；三 按重要性排序的问题：① TZ 用例是否真改变了 runner 看到的本地时区（不是只改传参）② 补跑用例②是否证明「只补推送不重生成」而非只证「没崩」③ Bark 注入是否绑定 :258-259 那两条落账且落盘顺序断言真承重 ④ 零产品代码断言是否覆盖 backend/lib 与 scripts ⑤ 红用例若有，定性是否与断言消息一致；四 输出格式；五 边界 + 已裁决）。存档 `_bmad-output/审查/codex-review-CARD-G6-9a.md` 首部按协议 §2.1；顺序固定「测试定稿 → 跑全部裁判 → 送 Codex → 之后只改 _bmad-output」，审后再改测试 = 失绑须登记。验收单 `_bmad-output/验收单/UAT-CARD-G6-9a-<日期>.md`：DoD-3 双段（4-B 零技术词）；4-B「无论电脑时区怎么设，早上那条复习提醒算的『今天』和网页上的『今天』是同一天；半夜生成的也不会错日；电脑睡醒后只补发提醒、不重新算一遍」+ felt-sense；「本卡未证明什么」「台账待登记条目」必填。commit header ≤100 含批次标记，body 行 ≤100（`wc -m`）；不 push；跑完说「复核第十二批 Y3」。
