> ⚠️ 本文件是 CARD-U6C-HANDOVER 的完整卡文——车道开工后必读并逐条执行；它不是 /goal 粘贴文本。/goal 在第十四批手册 §三 T3-D 块。
> 批次标记 `[BATCH-2026-09-11-第十四批 / CARD-U6C-HANDOVER]`。车道：`card-t3-review`（分支 `card/t3-review`，NEW @ `08100483`，venv symlink 已建、`backend/.env` 在），本卡 T3 第 4/4 张，**前提 = 前一卡 T3-C CARD-G6-9b 已独立 commit 且 `git status --porcelain` 空**（串行：T3-A G6-9c-R2 → T3-B G6-8 → T3-C G6-9b → 本卡）。用户已裁：**D-10**（U6-C 的 `due_crossed` 缺判型这类行为面修复**不得归 U1/U2**——两卡是纯 pyright 卡、明写「禁顺手修存量」——必须另立卡，即本卡）；**D-37**（U6-C 三个产品口径「20:00 今晚阈值 / 全板推迟退化恒等 / done+snooze 顺序」按现状确认**不改**，本卡禁碰）；**D-15**（有代码改动的卡 Codex 多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0）。勘探 2026-09-11（recon A §B.4「U6-C 移交面（3 项）」+ §D-10 + §C-5；recon C 无 T3-D 专节，本卡锚点全部主 session 开批当日在主干树实测）于主干 `08100483`。协议（⛔ 必须读 **feature 主干树 `--add-dir` 那份**：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/.claude/rules/card-batch-protocol.md` —— §1 合并门 + D-15 轮次 / §2.1 存档首部 / §2.2 裁判落盘 + --no-color + ruff zsh 数组 + pyright 绝对路径 / §3 最低覆盖；**车道树自己的 `.claude/rules/card-batch-protocol.md` 是 `08100483` 版，本批三处回写只在 `--add-dir` 那份、不在车道树里**，别读车道树那份）。手册同理只读主干树那份：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/2026-09-11-第十四批开跑手册-10车道43卡.md`（§零 / §一 / §三 T3-D 块）。**排批期裁定（最高优先，与本卡文冲突时以裁定为准，开工必读全文）**：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/2026-09-14-第十四批排批期裁定-R-B14.md` —— 与本卡相关的三条：**R-B14-4 已批准把 `scripts/daily_review_run.py` 扩进本卡地盘**（附加约束「只改 `due_crossed` 判型与父子墙钟传参段」）、R-B14-2（`tests/unit` 红基线自证唯一口径 `grep -vc '^#' "$BASE"` = **64**）、R-B14-3（`cd backend` 之后 `--ignore` 必须写相对路径 `tests/unit/test_deploy_vault_sh.py`）。

# CARD-U6C-HANDOVER — U6-C 四条移交面收口：runner `due_crossed` 判型 / overview 刷新父子读钟跨午夜统一 / `snoozeKey`·`doneKey` NUL 反向碰撞定性 / 3 颗既有定时哑弹逐条处置

## 〇 事实

| 事实 | 位置 / 实测命令 |
|---|---|
| **口径更正①（地盘缺口已由 R-B14-4 裁定补齐）**：recon A §B.4 把 item ① 的代码面写成「`review_overview.py` / `daily_review_pick.py`」，**实测 `due_crossed` 只在 `scripts/daily_review_run.py`**（`review_overview.py`/`daily_review_pick.py` 里 `grep -F due_crossed` 均 0 命中）。该文件原不在设计稿 §3 T3 逐文件清单（§3 只列其测试 `backend/tests/regression/test_daily_review_run.py`）⇒ 主 session **裁定 R-B14-4 已批准把它扩进 T3-D 地盘**（依据：T4 只拥有 `daily_review_pick.py`，本体全批无其他写者 ⇒ 零冲突），**附加约束：只改 `due_crossed` 判型与父子墙钟传参段**；手册 §一「地盘扩充（裁定 R-B14-4…）」行已同步补齐 ⇒ **item ① 照常交付，不再有闸门**，(b) 降为一次自证 | `grep -rnF 'due_crossed' backend/app scripts canvas-vault/.claude/skills`；`sed -n '588p;598,601p' scripts/daily_review_run.py`；`grep -nF 'T3-D +' <手册>`（命中「地盘扩充（裁定 R-B14-4…）」行） |
| **item ①（`due_crossed` 缺判型）**：`scripts/daily_review_run.py:588` `due_crossed = bool(st.get("next_due_utc")) and st["next_due_utc"] <= now_z` —— **无 `isinstance` 判型**；并列的 `wake_crossed`（`:598` `isinstance(_wake, str) and bool(_wake) and _wake <= now_z`）**有**判型（Codex round-1 MEDIUM-4 已补）。`due_crossed` 在 `:588` **先于** `wake_crossed`（`:598`）求值，且两者同在 `:599` 的 `if not due_crossed and not wake_crossed …` 里。`st` 是外部 state 文件 ⇒ 一个 `{"next_due_utc": 1}` 会让 `1 <= "…Z"` 抛 `TypeError`；而 `:601` 的 `except (json.JSONDecodeError, OSError)` **不接 TypeError** ⇒ 整轮 runner 带 traceback 退出（连推送都不跑），而非「当没有到期点、照常重扫」 | `sed -n '585,601p' scripts/daily_review_run.py` 原文逐字 |
| **口径更正②（机制，item ② 可全在 T3 地盘修）**：recon A §B.4 / 设计稿 §4 写 item ② 的做法是「统一由父进程传 `--now`/`--today`」。**实测 `daily_review_pick.py` 早已接受 `--now`**（`:1287` `ap.add_argument("--now", …)`，`:1293-1305` 解析成 `now`，`:1340` 附近 `build_payload(vault, now, …)` 喂进去）；**没有 `--today` 参数**，载体是 `--now`。真正缺的是 **`review_overview._run_pick` 不传 `--now`**（`:1887` `argv = [sys.executable, str(script), "--vault", str(vault_dir), "--write"]`——勘探/前稿写 `:1886`，主干冻结态实测 `:1887`，以 §二 `grep -nF` 锚点为准；只按 `state_file` 追加 `--state`）。⇒ item ② 的修面**只在 `review_overview.py`（T3 地盘）**：让 `_run_pick` 把父进程那一刻的 `now` 以 `--now <iso>` 传给子进程；**不必改 T4 地盘的 `daily_review_pick.py`** | `grep -nE "add_argument\\('--now'|--now" scripts/daily_review_pick.py`；`sed -n '1876,1894p' backend/app/api/v1/endpoints/review_overview.py` |
| **item ②（父子读钟跨午夜分日）**：overview 刷新路径里，父进程 `review_overview._display_today(now)`（`:398` 定义，`:1113` `today_local = _display_today(now)`——写 `board_done` 日历键、页面归日）与子进程 `daily_review_pick.build_payload`（`:971`）内 `now.astimezone(_DISPLAY_TZ).date()`（`:1010` / `:1121`）是**两次独立读钟**，相隔一次 `subprocess.run`（`_run_pick:1890`，0.1–2s）。当地午夜前后这两次可能落在不同的一天 ⇒ 23:59:59 标完成、子进程 00:00:00.2 判「不是今天完成的」⇒ 让位不发生。严重度 LOW（窗口 ≈ Δ/86400，下一次 refresh 自愈） | `sed -n '398,408p;1113p;1876,1894p' backend/app/api/v1/endpoints/review_overview.py`；`sed -n '1010p;1121p' scripts/daily_review_pick.py` |
| **口径更正③（item ② 范围，U6-C 验收单 §八.10 round-6）**：传 `--now` **只合 `_run_pick` 这一道缝**（单次刷新内的父子），**不消除**「写推迟账那次请求 / 刷新那次请求 / 之后 GET 渲染那次」三次独立读钟；且 **launchd runner 路径不起 picker 子进程**——`daily_review_run.py` 在 `import daily_review_pick as picker` 后进程内直调 `picker.build_payload(VAULT, now, …)`（`:604` import、`:615` 附近调用），**已在传自己的参照时刻**，不受 item ② 影响。本卡 item ② 范围 = 合上刷新路径那道缝，残留三读钟如实登记 | `sed -n '604p;615,618p' scripts/daily_review_run.py`；UAT-CARD-G6-6-2026-09-09.md §八.10 |
| **item ③（`snoozeKey`/`doneKey` NUL 反向碰撞）**：二者是 `review_app.py`（T3 地盘）里的 JS 键函数——`doneKey` `:202`、`snoozeKey` `:209`。**正向**（snoozeKey 输出撞 doneKey 值域）已在 U6-C round-5 修掉：`snoozeKey` 改为 `"snooze|" + esc(v) + "|" + esc(b)`、`esc` 把 `% | NUL` 三者百分号转义 ⇒ 输出恒不含 NUL ⇒ 与 `doneKey(v,b)=v+NUL+b`（值域恒含 ≥1 个 NUL）不相交（`:217-225` 注释原文）。**残留 = 反向 / `doneKey` 自身同款**：`doneKey` 仍用裸 NUL 作分隔符，其自撞需**库名或板名含 NUL**，而 vault/board 名经 `read_text→frontmatter 正则→_fm_str` 取自 POSIX 文件名/目录名（造不出含 NUL 的）⇒ 现状不可达。本卡对反向方向**逐条定性 + 负控证不可达或收口** | `grep -nE 'function (done|snooze)Key' backend/app/api/v1/endpoints/review_app.py`；`sed -n '202,226p' backend/app/api/v1/endpoints/review_app.py` |
| **item ④（3 颗既有定时哑弹，行号漂移）**：U6-C 验收单（§七32 / §八.10）按更早 SHA 点名 `test_review_overview.py:1365/:3533/:1093`——那是 **assert 行**，主干 `08100483` 上 **def 行已漂**：① `def test_refresh_rebuilds_projection_and_response_matches_disk` 实测 **:1353**（引信 assert `due_nodes == 0` 在 **:1374**，真实时间过 `2099-01-01T00:00Z` 后两「未来」节点到期 ⇒ 实为 2）；② `def test_g67r_refresh_passes_state_and_done_board_yields_top` 实测 **:3509**（让位 assert 在 **:3542**，父写完成日后跨当地午夜、子进程按次日匹配 ⇒ 让位失败，与 item ② 同根）；③ `def test_buckets_gate_accepts_real_producer_payload` 实测 **:1060**（`status == "ok"` assert 在 **:1128**，夹具取日后 / GET 前跨午夜 ⇒ 投影成 `stale`） | `grep -nF 'def test_refresh_rebuilds_projection_and_response_matches_disk' backend/tests/unit/test_review_overview.py` 等三条；`sed -n '1374p;3542p;1128p' …` |
| **这仨都在 T3 地盘**（`backend/tests/unit/test_review_overview.py`）；item ④ = 逐条定性「引信是什么 / 是否可达 / 修或登记」，能在本卡面内用「钉钟 / `--now` 覆盖」拆掉的修掉，其余带精确理由登记 | 同上 |
| **review_overview.py / review_app.py 均在 `backend/app/api/v1/endpoints/`** ⇒ 触发 lefthook `python-typecheck`（glob 覆盖 `backend/app/**`）⇒ ★app ⇒ 本卡**必须 pyright 保持 0**；`scripts/daily_review_run.py` 在 `scripts/` 不触发 typecheck，但触发 `python-lint`（ruff，glob 覆盖 `{backend,src,scripts}/*.py`） | `ls backend/app/api/v1/endpoints/review_*.py` |
| **pyright 基线 = 0 errors / 81 warnings**（`08100483` 上 `pyright app`，rc=0） | `_bmad-output/审查/evidence-b14/pyright-app-after-u2-20260911T094407.txt` 末行 `0 errors, 81 warnings, 0 informations` |
| **tests/unit 红基线**（nodeid 口径，带 `--ignore tests/unit/test_deploy_vault_sh.py`，差集只许 `<`） | `_bmad-output/审查/evidence-b14/unit-red-baseline-08100483.txt`（该文件即权威基线，以它为准；主干树 `--add-dir` 那份） |
| **tests/regression 基线 = 1674 passed**（`test_daily_review_run.py` 在其中） | 设计稿 §0.1 / `evidence-b14/reg-integ-*.txt` |
| HEAD 实测：主干树 HEAD = `e58d5c5c`（= `08100483` + 1 个纯文档/协议 commit；它只改 `.claude/rules/card-batch-protocol.md` 与 `_bmad-output/**`，**未碰任何本卡代码文件**）。本卡车道树 NEW @ `08100483`，经 T3-A/B/C 串行后 HEAD 已前进——**开工先 `sed -n` 复核 §〇 全部 file:line**（T3-A/B/C 改过 `review_overview.py`/`review_app.py` ⇒ 行号很可能已漂，引用一律以 `grep -nF '<符号/原文>'` 锚点为准，行号只作线索） | `git --no-pager log --oneline -2`；`git show --stat e58d5c5c` |
| **本批纪律**（§三逐条执行）：pyright 保持 0（★app，hook `python-typecheck` 正常拦，本卡新增 error 自己清、ignore 带 `# pyright: ignore[rule]  # 一行理由`，**不得 `LEFTHOOK_EXCLUDE=python-typecheck`**）；判据 grep git 输出一律 `--no-color` + 同次验伪锚；evidence 用 `.txt` 不 `.log`；承重裁判末行 `rc=$pipestatus[1]`（zsh）；ruff 判据用 zsh 数组（§二）；批中禁装/升任何包；`fsrs_bridge.py`/`decay_beta.py` 零写者；live vault / 7691 / 7687 / 现网 LanceDB 只读 | 见 §二 / §三 |

## 一 完成条件（AND）

- **(a) 第 0 分钟**：`pwd` = `…/worktrees/card-t3-review`、分支 `card/t3-review`、`git status --porcelain` 空（前提 = T3-C 已独立 commit 且干净；不空先停下报主 session）；`test -x backend/.venv/bin/pytest && test -e backend/.env`；pyright 自证 `test -x /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/.venv/bin/pyright`。**开工基线自证（落档）**：①`P=…/card-v5-lance/backend/.venv/bin/pyright; cd backend; "$P" app 2>&1 | grep -E '^[0-9]+ errors?, '` → `0 errors, 81 warnings`（非 0 errors 或 pyright 缺席 ⇒ 停下报主 session）；②`BASE=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/evidence-b14/unit-red-baseline-08100483.txt; test -f "$BASE" && grep -vc '^#' "$BASE"` → **必须 = 64**（R-B14-2 定死的唯一口径：该基线 67 行 = 3 行 `#` 注释 + 64 条真 nodeid，其中一行注释里逐字引用了一条 flaky nodeid ⇒ ⛔ 不得改用「含 `::` 的行数」这种把注释也算进去的计数，那会得 65）；基线在 **feature 主干树**，不在本车道树；文件不在或计数 ≠ 64 ⇒ 停下报主 session。**开工先 `sed -n`/`grep -nF` 逐条复核 §〇 file:line**，漂移即在验收单写「卡文 :X → 实测 :Y」，引用改用符号锚点。
- **(b) 地盘扩充自证（R-B14-4 已批准，不再是闸门）**：item ① 的生产文件 `scripts/daily_review_run.py` 原不在设计稿 §3 T3 逐文件清单，主 session 裁定 **R-B14-4 已批准把它扩入 T3-D 地盘**。开工跑 `grep -nF 'T3-D +' <手册绝对路径>`（手册 = feature 主干树 `--add-dir` 那份），**必须命中**那条含 `scripts/daily_review_run.py` 的「地盘扩充（裁定 R-B14-4…）」行，把该行原文逐字抄进验收单；**同次带验伪锚**——`grep -nF 'T8-F +' <同一手册>` 也必须命中（证这条 grep 在本文件上真能命中扩充行，不是恒空的假绿）。命中 ⇒ **item ① 照常做**，但 ⛔ **只准改 `due_crossed` 判型与父子墙钟传参段**（R-B14-4 附加约束，逐字抄进验收单），该文件其余行一字不动。**未命中（读错树 / 手册被回退）⇒ 停下报主 session**：⛔ 不得自行改手册、不得擅自扩地盘，也不得据此私自把 item ① 删掉。
- **(c) item ① 先红后绿（`due_crossed` 判型；(b) 自证命中即做）**：在 `test_daily_review_run.py`（或其新增用例）里造一个 `next_due_utc` 为非字符串（如 `1`）的 state，**改前跑必红**且红在「整轮 runner 抛 `TypeError` 退出」（不是夹具/import 错）；修法 = `grep -nF 'due_crossed =' scripts/daily_review_run.py` 命中行（冻结态实测 `:588`，行号会漂、以 grep 锚点为准）的 `due_crossed` 与 `wake_crossed` 同律加 `isinstance(…, str)` 判型（`due_crossed = isinstance(_due := st.get("next_due_utc"), str) and bool(_due) and _due <= now_z` 形态，符号名以实测为准）；**改后**同例绿（错型 `next_due_utc` 被当作「无到期点、照常重扫」，不再崩）；tee `due-crossed-<ts>.txt`，末行 `rc=$pipestatus[1]`。
- **(d) item ② 先红后绿（刷新路径父子读钟，钉钟两侧）**：在 `test_review_overview.py` 新增一条门——**钉父进程 `now` 在当地 `23:59:59.x`、让子进程若自读墙钟会落到次日 `00:00:00.x`**（用 monkeypatch 固定父侧时钟 + 观察 `_run_pick` 传给子进程的 argv）。**改前**（`_run_pick` 不传 `--now`）必红（子进程归日 ≠ 父进程归日 / argv 无 `--now`）；**修法** = `_run_pick` 新增携带父侧 `now` 的形参，argv 追加 `--now <now.isoformat()>`（子进程 `daily_review_pick.py` 已接受 `--now`，**不改它**），调用点把 `_display_today` 用的同一个 `now` 透传下去；**改后**绿（argv 含 `--now`、父子归日一致）。⛔ **不得改 `daily_review_pick.py`（T4 地盘）**；若发现非改它不可，停下在验收单登记并报主 session（地盘交集）。tee `parent-child-clock-<ts>.txt`。
- **(e) item ③ 定性 + 负控（`snoozeKey`/`doneKey` 反向 NUL）**：对反向方向（`doneKey` 产出撞 `snoozeKey` 值域 / `doneKey` 自撞）给**逐条定性**：`snoozeKey` 输出恒不含 NUL（round-5 已立），`doneKey` 自撞需库名/板名含 NUL（POSIX 不可达）。**负控（承重）**：在 `test_review_app.py` 的 JS 沙箱里造一个「`doneKey` 的输入含 NUL」的对照输入，断言它无法反推出一个合法 `snoozeKey` 值（或如实证明该输入在生产取名链上不可达）；验伪锚——先喂一个**已知会撞**的退化 `snoozeKey` 实现（round-5 被打回的 NUL 前缀版）证明该门能变红。能收口则收口（同「值域不相交」原理判据），不可达则带证据登记。tee `key-collision-<ts>.txt`。
- **(f) item ④ 三颗哑弹逐条定性修或登记**：先 `grep -nF 'def test_…'` 复核三条实测 def 行（§〇 已给 1353/3509/1060，必再测）；逐条写「引信 / 可达性 / 处置」：②（`:3509`/assert `:3542`）与 item ② 同根——item ② 的 `--now` 修法应使它可钉钟稳定，**修**（钉父子同一 `now`）；①（`:1353`/assert `:1374`，`2099` 硬编码未来到期）与 ③（`:1060`/assert `:1128`，取日后跨午夜 stale）用测试侧钉钟（固定时钟 / `--now` 覆盖）**修**，若某条修法会溢出本卡面或改既有语义则带精确理由**登记**。每条处置落验收单，修掉的给先红后绿对照。
- **(g) 负控 / 验伪锚汇总（承重）**：(c)(d)(e)(f) 每条修法都配一个「把修法还原成缺陷态、指定那道门必红」的负控；还原一律用 `git show HEAD:<path> > <tmp>` 比对 + EXIT trap 无条件还原 + 全文件 `shasum -a 256` 前后逐字相同（⛔ 禁 `git stash` / 禁 `git checkout HEAD -- <file>`）；判据旁必带同次验伪锚（先证该门能命中一条已知正例/反例）。
- **(h) 地盘核**：`git --no-pager diff --stat --no-color <前提 commit=T3-C 末 commit> HEAD -- . ':(exclude)_bmad-output'` 列出的文件**必须是 §三 允许面的子集**（`backend/app/api/v1/endpoints/review_overview.py`、`backend/app/api/v1/endpoints/review_app.py`、`backend/tests/unit/test_review_overview.py`、`backend/tests/unit/test_review_app.py`、`backend/tests/regression/test_daily_review_run.py`，以及 R-B14-4 扩入的 `scripts/daily_review_run.py`——后者的 diff 还必须**逐 hunk 自证只落在 `due_crossed` 判型与父子墙钟传参段**，越出该约束面即便文件在允许名单里也是违规）；越出 = 阻断。⛔ pathspec 写 `':(exclude)…'`（`':!…'` 在本机 git/zsh 下 rc=128），同次带验伪锚（先证能列出一条已知改过的文件）。
- **(i) tests/unit + tests/regression 目录级**：收工各跑一次。跑法与基线文件头逐字一致——`cd backend` **之后**写相对路径 `--ignore tests/unit/test_deploy_vault_sh.py`（R-B14-3：`cd backend` 后写 `backend/tests/unit/...` 不匹配任何被收集文件 = 空操作，那个重型文件会真跑并挂住）。`tests/unit` nodeid 口径与 `$BASE`（64 条）diff **只允许 `<` 行**（新门不在红集；任何 `>` = 阻断；rc 与汇总行都在；⛔ 禁 `wc -l` 当判据）；`tests/regression`（含 `test_daily_review_run.py`）**1674 passed** 不回退（先 `test_daily_review_run.py` 文件级先红后绿，再目录级）。无 W4 门的树禁目录级 pytest——本树经 T3-A/B/C 已含门可跑，但 `tests/integration`/`tests/e2e` 走 advisory 仍会真连，**不跑**。
- **(j) pyright 保持 0**：改完 `review_overview.py`/`review_app.py` 后 `pyright app`（绝对路径 + `test -x`，§二）必须仍 `0 errors`；本卡新增的 error 由本卡自己清（ignore 带 `# pyright: ignore[rule]  # 一行理由`）；⛔ **不得 `LEFTHOOK_EXCLUDE=python-typecheck`** 提交改 `backend/app/**` 的卡。`scripts/daily_review_run.py` 不触发 typecheck 但触发 ruff（§二 数组判据覆盖 `scripts/`）。
- **(k) Codex 多轮**：顺序固定「代码与门全部定稿 → 跑全部裁判 → 送 Codex → 之后只改 `_bmad-output`」；**Codex gpt-6-astra ultra 多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0**（本卡有代码改动 ⇒ 多轮，上限 5 轮；第 5 轮仍有 HIGH → 停下交主 session 人审）；prompt 五分节 + 最小读取面写死；prompt 与存档不得出现协议 §2 的四个禁用措辞（见 §四）。
- **(l) 提交**：单独 commit（header ≤100 含 `[BATCH-2026-09-11-第十四批 / CARD-U6C-HANDOVER]` 且含卡号 `CARD-U6C-HANDOVER`，body 行 ≤100，`wc -m` 计字符）；`*.stderr*` 不入库；**不 push**；不改台账（只在验收单写「台账待登记条目」）。ruff `python-lint` 若因主干既有 ruff-format 漂移红，按协议 §2.3 过渡条款处置（只对本卡 diff 文件 `ruff format --check`、贴被跳过门原始输出 + 「漂移不在本卡改动行」证明；`backend/app` 的 `python-typecheck` **不享此过渡**、必须 0）。
- **(m)「本卡未证明什么」必填（≥4，见 §四）** + **「台账待登记条目」必填（≥4，见 §四）**。

## 二 裁判命令

> 树根先 `cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review`；`PYTEST=$(pwd)/backend/.venv/bin/pytest`；`EV=$(pwd)/_bmad-output/审查/evidence-u6c-handover`（**绝对路径**——承重裁判带 `cd backend`，相对会落到不存在的 `backend/_bmad-output/…`）；`mkdir -p "$EV"`；`BASE=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/evidence-b14/unit-red-baseline-08100483.txt`（**feature 主干树绝对路径**，本车道树没有这个目录）。承重裁判 `2>&1 | tee "$EV/<name>-$(date +%Y%m%dT%H%M%S).txt"; echo rc=$pipestatus[1]`（zsh；`.txt` 不 `.log`）。前提 commit：`PREV=$(git rev-parse HEAD)` 在开工第 0 分钟取（= T3-C 末 commit），地盘核 (h) 用它。

```bash
# 0. 第 0 分钟
git rev-parse --abbrev-ref HEAD            # card/t3-review
git status --porcelain | wc -l             # 0
PREV=$(git rev-parse HEAD); echo "PREV=$PREV"
test -x backend/.venv/bin/pytest && test -e backend/.env && echo env-ok
# pyright 基线自证（绝对路径 + test -x；⛔ 禁 | tail -1）
P=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/.venv/bin/pyright
test -x "$P" || { echo "pyright 缺席"; exit 1; }
( cd backend && "$P" app 2>&1 | grep -E '^[0-9]+ errors?, ' )   # 0 errors, 81 warnings
test -f "$BASE" && grep -vc '^#' "$BASE"   # 必须 = 64（R-B14-2 唯一口径；⛔ 不得改用含 '::' 的行数，注释里那条 nodeid 会让它变 65）

# 1. §〇 行号复核（行号会漂，以符号锚点为准）
grep -nF 'due_crossed =' scripts/daily_review_run.py
grep -nE 'function (done|snooze)Key' backend/app/api/v1/endpoints/review_app.py
grep -nF "argv = [sys.executable, str(script)" backend/app/api/v1/endpoints/review_overview.py
for t in test_refresh_rebuilds_projection_and_response_matches_disk \
         test_g67r_refresh_passes_state_and_done_board_yields_top \
         test_buckets_gate_accepts_real_producer_payload; do
  grep -nF "def $t(" backend/tests/unit/test_review_overview.py; done

# 2. item ① 先红后绿（地盘 R-B14-4 已批准，直接做）
( cd backend && PYTHONDONTWRITEBYTECODE=1 $PYTEST -q -p no:cacheprovider \
    tests/regression/test_daily_review_run.py ) 2>&1 | tee "$EV/due-crossed-$(date +%Y%m%dT%H%M%S).txt"; echo rc=$pipestatus[1]

# 3. item ②/④ 先红后绿（钉钟两侧）
( cd backend && PYTHONDONTWRITEBYTECODE=1 $PYTEST -q -p no:cacheprovider \
    tests/unit/test_review_overview.py ) 2>&1 | tee "$EV/parent-child-clock-$(date +%Y%m%dT%H%M%S).txt"; echo rc=$pipestatus[1]

# 4. item ③ 反向碰撞负控
( cd backend && PYTHONDONTWRITEBYTECODE=1 $PYTEST -q -p no:cacheprovider \
    tests/unit/test_review_app.py ) 2>&1 | tee "$EV/key-collision-$(date +%Y%m%dT%H%M%S).txt"; echo rc=$pipestatus[1]

# 5. pyright 保持 0（改后）
( cd backend && "$P" app 2>&1 | grep -E '^[0-9]+ errors?, ' ) 2>&1 | tee "$EV/pyright-$(date +%Y%m%dT%H%M%S).txt"; echo rc=$pipestatus[1]

# 6. ruff（zsh 数组；覆盖 backend + scripts 改动文件；验伪锚见注）
R=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/.venv/bin/ruff
F=(${(f)"$(git --no-pager diff --name-only --no-color --diff-filter=AM $PREV HEAD -- 'backend/**/*.py' 'scripts/**/*.py')"})
print -r -- "files=${#F}"; (( ${#F} )) || exit 1
"$R" check -- "${F[@]}"; echo rc=$?
"$R" format --check -- "${F[@]}"; echo rc=$?
# ⛔ 验伪锚：单独喂一个已知含 F401 的临时文件给 "$R" check，必须 rc=1（证 ruff 判据有牙）

# 7. 目录级收工
( cd backend && PYTHONDONTWRITEBYTECODE=1 $PYTEST -q -p no:cacheprovider --ignore tests/unit/test_deploy_vault_sh.py tests/unit ) \
    2>&1 | tee "$EV/unit-closing-$(date +%Y%m%dT%H%M%S).txt"; echo rc=$pipestatus[1]
#   → 收集 nodeid 与 $BASE diff：只许 < 行（任何 > = 阻断）
( cd backend && PYTHONDONTWRITEBYTECODE=1 $PYTEST -q -p no:cacheprovider tests/regression ) \
    2>&1 | tee "$EV/reg-closing-$(date +%Y%m%dT%H%M%S).txt"; echo rc=$pipestatus[1]   # 1674 passed 不回退

# 8. 地盘核（--no-color；pathspec 用 ':(exclude)'）
git --no-pager diff --stat --no-color $PREV HEAD -- . ':(exclude)_bmad-output'
#   → 文件必须 ⊆ §三 允许面；验伪锚：先证它能列出一条已知改过的文件
```

## 三 禁改与隔离

**本卡地盘（只允许改的文件，逐文件；= 设计稿 §3 T3 行 + R-B14-4 批准扩充 1 处）**：
- `backend/app/api/v1/endpoints/review_overview.py` —— item ② 的 `_run_pick` 传 `--now`（★app ⇒ pyright 保持 0）。
- `backend/app/api/v1/endpoints/review_app.py` —— item ③ 反向碰撞定性/负控（★app ⇒ pyright 保持 0）。
- `backend/tests/unit/test_review_overview.py` —— item ②（钉钟门）+ item ④（三颗哑弹处置）。
- `backend/tests/unit/test_review_app.py` —— item ③ 负控门。
- `backend/tests/regression/test_daily_review_run.py` —— item ① 门。
- `scripts/daily_review_run.py`（item ① 生产面）—— 设计稿 §3 T3 行原只列它的测试、未列本体；**主 session 裁定 R-B14-4 已批准把本体扩入 T3-D 地盘**（无冲突依据：T4 只拥有 `daily_review_pick.py`，本体全批无其他写者；手册 §一「地盘扩充（裁定 R-B14-4…）」行已同步补齐，(b) 自证即抄该行）。⛔ **附加约束（R-B14-4 原文，逐字遵守）：只改 `due_crossed` 判型与父子墙钟传参段**——该文件其余行（推送 / state 落盘 / `payload_sha256` 校验 / `_nodes_max_mtime` 缓存分支 / `wake_crossed` 既有判型）一字不动；(h) 地盘核对本文件按 hunk 自证。⛔ 未列入 R-B14-4 扩充表的其它扩面仍属越界，一律停下报主 session。

**禁改面**：
- `scripts/daily_review_pick.py`（**T4 地盘**）—— item ② 的 `--now` 子进程已支持，**不改它**；若发现非改不可，停下登记并报主 session（地盘交集，串行序由主 session 裁）。
- `backend/app/core/display_tz.py`、`scripts/local_tz.py`、两 skill 脚本（`recap_exam_build.py` / `inbox_preview.py`）—— T3 前序卡（T3-A/B/C）面，本卡不碰。
- `backend/app/models/**` 零写者；`backend/openapi.json` 本卡不应变（item ①②③④ 不改 API schema；若实测变了，停下核是否 item ② 误触端点签名）。
- **D-37：U6-C 三个产品口径（20:00「今晚」阈值 `_SNOOZE_TONIGHT_HOUR` / 全板推迟退化恒等 / 同板 done+snooze 顺序）按现状确认不改，本卡禁碰**。
- **禁顺手修存量**：本卡只做点名的四条移交面；其余 `review_overview.py`/`review_app.py` 既有缺陷（如 §六12 的其它时钟读取点）不顺手改。

**硬边界**：禁写 live vault；禁连 Neo4j 7691 / 7687；禁碰 `canvas-vault/.claude/scripts/fsrs_bridge.py` 与 `decay_beta.py`（零写者）；禁现网 LanceDB 写；禁 `git stash` / `git stash pop`（栈跨 worktree 共享）；不跑变异 harness；批中禁装/升任何包（往共享 venv 装 = 批级事件，需协议 §2.3 通告）；不改台账；不 push。

## 四 Codex / 验收单

**Codex 命令**（协议 §2 固定）：
```bash
codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" \
  "$(cat <车道树>/_bmad-output/审查/prompts/codex-prompt-CARD-U6C-HANDOVER.md)" \
  > <车道树>/_bmad-output/审查/codex-review-CARD-U6C-HANDOVER-r1.md \
  2> <车道树>/_bmad-output/审查/codex-review-CARD-U6C-HANDOVER-r1.stderr </dev/null
```
- 模型固定 `gpt-6-astra` + `ultra`；`.stderr*` **永不入库**（`.gitignore` 已覆盖）。
- **prompt 五分节**：① 背景（U6-C 四条移交面 + D-10 归属 + D-37 不改产品口径）；② 审查面（本卡 diff 的五个文件，逐 item 对应）；③ 四条 item 的判据与负控；④ 要审的风险（item ① 判型是否真覆盖「读法空间」而非只覆盖 `1`；item ② 传 `--now` 是否真合上刷新那道缝、残留三读钟是否如实登记；item ③ 反向方向定性是否可达；item ④ 三条处置是否各自对；pyright 保持 0）；⑤ 最小读取面（列出本卡改的五个文件 + §〇 锚点，**不要求**它读别的）。
- ⛔ **prompt 与存档禁用协议 §2 的四个措辞**（cyber 拦在任务边界，不在措辞）——一律改说「负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径」。
- **存档首部**（协议 §2.1，每份 `codex-review-CARD-U6C-HANDOVER-rN.md` 首部必须是 blockquote，随后 `---` 再接正文）：抄批次/车道/卡/round、**模型行 `gpt-6-astra` · reasoning_effort `ultra` · codex 版本行（`codex --version` 实测值，写明行号）**、审查绑定 SHA（末轮必须绑最终 HEAD）、会话头自证（抄 `.stderr` 前三行含 model 行，括注行号；stderr 本身不入库）。缺模型/reasoning/codex 任一字段 ⇒ 该轮不计轮次配额。
- **D-15**：`Codex gpt-6-astra ultra 多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0`（上限 5 轮；审后再改代码 ⇒ 必再送一轮，只改 `_bmad-output` 不算；第 5 轮仍有 HIGH → 停下交主 session 人审）。本卡有代码改动 ⇒ 多轮（非零代码卡的 1 轮）。

**验收单**（DoD-3 双段）：
- 文件名 `UAT-CARD-U6C-HANDOVER-<日期>.md`，ship 到 `_bmad-output/验收单/`，结构照 `_bmad-output/templates/uat-sheet-template.md`（7 段，段 4-A Claude 已代验 / 段 4-B 你来验）。
- 段 4-B 跑禁词 grep（`curl|docker|HTTP|JSON|端口|.env|endpoint|pytest|容器|daemon|git|DevTools|requestUrl|vault.create|obsidiantools`）= 0 命中 [D3-A]；每条 checkbox「60 岁在 Obsidian/浏览器照做」[D3-B]；段 4-A 全 ✅ 带证据（Claude 自跑）[D3-C]；段 3 画用户屏幕变化 [D3-D]；段 4-B 用「我做 X → 我看到 Y → 我感觉 Z」+ felt-sense [D3-E]。
- **「本卡未证明什么」≥4** 与 **「台账待登记条目」≥4** 必填，数字与命令输出一致（`wc -m` 计字符）。**本卡未证明什么至少含**：① item ② 的 `--now` 修法只合 `_run_pick` 这一道缝，残留「写推迟账 / 刷新 / 之后 GET 渲染」三次独立读钟**未消除**、在真实刷新链上的跨午夜行为未验（如实登记，非本卡面）；② item ③ 反向方向「不可达」的前提（vault/board 名经 `read_text→frontmatter→_fm_str` 取自 POSIX 文件名/目录名、恒不含 NUL）是**取名链快照**而非代码不变量（未来引入非 POSIX 取名源即可打破）；③ item ① 的 `isinstance(…, str)` 判型只覆盖 `next_due_utc` 这一个键，**未证明** `st` 里其余外部可控字段（`payload_sha256` / `board_last_recommended` / `board_done` / `snoozed` / `snooze_wake_utc` 之外的键）错型时不会在同一 `try` 外抛出 `except (json.JSONDecodeError, OSError)` 接不住的异常——本卡「禁顺手修存量」，该面如实登记不做；④ `pyright app` = 0 errors 仅**静态类型核**，不证本卡改动运行期无缺陷（运行期由 (c)(d)(f) 先红后绿门覆盖，非 pyright 职责）；⑤ launchd runner 进程内直调 `picker.build_payload`（不起 picker 子进程）不受 item ② 影响系**本卡静态核结论**，未对真实 launchd :05 档跑一次验证。**台账待登记至少含**：① **item ① 地盘扩充的约束面自证**（`scripts/daily_review_run.py` 依 R-B14-4 扩入 T3-D，附加约束「只改 `due_crossed` 判型与父子墙钟传参段」——登记本卡对该文件的 diff 是否确实只落在约束面，供集成期主 session 复核；同时登记设计稿 §3 T3 行本身尚未回填本体，待归档时同步）；② item ② 残留「三次独立读钟」未全消、runner 路径不受影响；③ item ③ 反向方向若判不可达，其前提（POSIX 名不含 NUL）是快照而非不变量；④ item ④ 三条哑弹各自的修/登记结论 + 行号漂移记录（勘探 :1365/:3533/:1093 → 实测 def :1353/:3509/:1060）。
- **commit header ≤100 含批次标记且含卡号**；`*.stderr*` 不入库；不 push；跑完（本卡收工 + 验收单 ship）说「**复核第十四批 T3**」。
