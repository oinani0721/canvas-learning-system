# UAT — CARD-DEPLOY-TIMEOUT：步 1 `npm run build` 墙钟上限 + 16 处裸 `subprocess.run` 加 `timeout=`

> 批次 `[BATCH-2026-09-11-第十四批 / CARD-DEPLOY-TIMEOUT]` · 车道 T2-A（首卡）
> 树：`.claude/worktrees/card-t2-deploy`（分支 `card/t2-deploy`，基线 `08100483` = B14_BASE）
> 代码 commit：`7413283a`（r1 审）→ `71a85acf`（r1 整改 = r2 审）→ `25f56065`（r2 整改 = **r3 审 = 最终代码 HEAD**）
> Codex 三轮：HIGH 1 → HIGH 1（换面）→ **BLOCKER 0 / HIGH 0 / MEDIUM 0 / LOW 3 ⇒ D-15 达标**（上限 5，用 3）
> 承接：集成期裁定 **R-15**（候选树跑 `tests/unit` 时 `test_deploy_vault_sh.py` 真跑 DEPLOY_SH 的
> 用例逐个无限挂起）。集成修复 `3966ddad` 的 `timeout=600` 单点补丁**保留不撤**，本卡补齐其余 15 + 1。
> 证据全部在 `_bmad-output/审查/evidence-deploy-timeout/`（引用一律写全文件名，不用 glob）。

---

## 一 第 0 分钟自证 + 「卡文 → 实测」行号位移

### 1.1 开工核（`manual-scope-20260914T194807.txt` / `open-facts-A-20260914T194826.txt` / `open-facts-B-20260914T194837.txt`）

| 项 | 实测 | 期望 | 结论 |
|---|---|---|---|
| `pwd` | `…/worktrees/card-t2-deploy` | 同 | ✅ |
| 分支 | `card/t2-deploy` | 同 | ✅ |
| `git rev-parse --short=8 HEAD` | `08100483` | `08100483` | ✅ |
| `git status --porcelain \| wc -l` | `0` | 0 | ✅ |
| `backend/.venv/bin/pytest` / `backend/.env` / `backend/.venv/bin/pyright` | 三者都在 | 都在 | ✅ |
| 基线 `unit-red-baseline-08100483.txt` `grep -vc '^#'` | **64** | 64 | ✅ |
| `command -v timeout` / `gtimeout` | 两者 **ABSENT** | ABSENT | ✅（⇒ 上限不得用 `timeout` 命令） |
| `perl -e 'alarm 1;print"ok"'` | `perl-alarm-ok`（`/usr/bin/perl`） | 可用 | ✅ |
| 本树 `canvas-vault/.obsidian/plugins/canvas-learning-system/main.js` | **ABSENT** | 卡文预判「大概率 ABSENT」 | ✅ 如实记 |
| 两地盘文件 `git diff --stat 08100483 HEAD` | 空（0 行） | 空 | ✅ 代码基线冻结 |
| 文件行数 | `test_deploy_vault_sh.py` 2596 / `deploy-vault.sh` 1238 | 2596 / 1238 | ✅ |

**手册地盘对齐核**（卡文 (a)，钉身份不钉总行数）：手册 `:59`「只 T2」行逐字点名本卡两文件 ——

```
59:- **只 T2**：`scripts/deploy-vault.sh`、`backend/tests/unit/test_deploy_vault_sh.py`、
`scripts/vault-install-manifest.json`、`.claude/skills/deploy-vault/SKILL.md`（⚠️ 排批稿误写
`canvas-vault/…`，实测在仓根；R-B14-8）、`scripts/cls_forbidden_paths.py`、
`backend/tests/unit/test_docker_compose_config.py`。
```

命中 ⇒ 按手册地盘执行。（同命令的「总行数」当日实测 **54**，卡文写 41/47/54 三个数都是不同时点的
快照 —— 本判据不钉它。）

### 1.2 §〇 事实逐条复核（全部成立，无一条需要改卡）

- `subprocess.run` 共 **20** 处、带 `timeout=` **4** 处（`77/462/1873/2447`）、裸跑 **16** 处
  （`96/486/495/675/882/940/1010/1270/1635/1684/1927/1930/1932/1965/1967/2324`）—— 与卡文逐字同。
- `grep -c 'timeout='` = **5**（`83/476/603/1888/2467`），第 5 处 `:603` 确是 `_run(..., timeout=timeout)`
  的 helper kwarg（`def _run` 在 `:65`，`:77` 才转发给 `subprocess.run`）⇒ **判据只能用 AST**。
- 脚本侧：`step1_preflight :389`、`npm run build :549`（`550`/`554` 是文案）、无上限无离线标志；
  步 5 `curl -m 10` 在 `:1139`、`up -d backend` 在 `:1122`；`run_step :373` + 六 def + 六调用 `1230-1235`；
  `bash -n` rc=0。全部与卡文同值。
- 既有「假命令置 PATH 最前」惯例（假 `lsof`）在 `:2220` —— 本卡的假 npm 沿用该手法。

### 1.3 行号位移（卡文 :X → 改后 :Y，**不改卡文本体**）

本卡两次整体位移：① 新增 `import signal`（+1）；② 新增 11 行 `_SUBPROCESS_TIMEOUT` 常量与注释 +
`ruff format` 对 6 条过长行重排（+若干）。16 处裸跑的最终对照：

```
96→108 / 486→498 / 495→508 / 675→689 / 882→898 / 940→958 / 1010→1029 / 1270→1289
1635→1654 / 1684→1704 / 1927→1948 / 1930→1953 / 1932→1961 / 1965→1995 / 1967→1999 / 2324→2358
```

既有 4 处（**本卡一字未动**，值也未动）：`77→89`（`timeout=timeout`）/ `462→474`（120）/
`1873→1894`（600，= 集成修复 `3966ddad`）/ `2447→2482`（120）。

脚本侧（**r1 整改后的终值**）：`step1_preflight 389→414`（函数体 `:414-651`）、本卡改动集中在
`:569-638` 的 build 段（`perl -e` 在 `:603`、`npm_config_offline` 在 `:601`）、缺省赋值 `:99-100`、
头注文档 `:63-84`；步 5 `1060→1144`（`:1144-1240`）、步 6 `1159→1243`（`:1243-1305`）——
**步 5/6 位移纯粹是步 1 变长带来的，内容逐字节未动**（sha256 对照见 4-A 判据 6b）。

---

## 二 做了什么（两文件，其余只读）

### 2.1 `scripts/deploy-vault.sh`（**只动步 1**）

1. **墙钟上限**：`npm run build` 包进 `/usr/bin/perl` 的 `alarm` —— `fork` 一个 `setpgrp(0,0)`
   **自成进程组**的子进程 `exec npm`，到点对该进程组发 `TERM`、隔 2s 再 `KILL`（组信号失败则退回
   单进程信号，覆盖 `fork → setpgrp` 窗口）。本机 `timeout(1)`/`gtimeout` 都缺席，故不用该命令。
   超时以**带外标记**回报（见下第 6 条；初版用 rc 124，被 Codex r1 MEDIUM-2 证明会与 npm 自己
   `exit 124` 撞车）。
   > 只杀壳不杀组的话，npm fork 出来的后代会变成还在跑的孤儿 —— 本卡用「假 npm 额外 fork 一个
   > `sleep 3600` 后代」把这件事做成了**可断言**的判据（见 §三 4-A 判据 4）。
   > ⚠️ 后代若自己 `setsid()` 则脱离该组、杀不到（Codex r1 MEDIUM-1 实测，已写进头注与 §五.3）。
2. **可配置 + 文档化**：`CLS_NPM_BUILD_TIMEOUT`（缺省 **300s**）与 `CLS_NPM_BUILD_OFFLINE`（缺省 **true**）
   在头注「环境开关」段有文档（该段就是 `--help` 输出，`usage()` 打 `sed -n '2,/^[^#]/p'`），
   缺省赋值紧跟既有 `CLS_MIN_SKILLS`（`set -u` 要求）。
   **300 的依据**：裁判侧兜底是 600（`_SUBPROCESS_TIMEOUT`），脚本取其一半 ⇒ **脚本自己的超时文案
   必定先于裁判超时出现**，用户看到的是「哪一步超时」而不是一个没有解释的挂死。
3. **离线标志**：`npm_config_offline="$CLS_NPM_BUILD_OFFLINE"` 写在真正的 env 段里（终值 `:601`，
   与既有 `npm_config_cache`/`npm_config_logs_dir`/`npm_config_update_notifier` 同段），不是写在
   注释里；且**有判据钉着**（假 npm 落盘它收到的值，正向对照用例断言 `=true`）。
4. **超时专属文案**：`npm run build 超时（墙钟上限 ${_cap}s, 已杀 npm 所在进程组）: …`
   与既有「`npm run build 失败（…）`」**分开报**（既有文案一字未动）。
5. **取值校验（r1 整改后收紧）**：`CLS_NPM_BUILD_TIMEOUT` 必须是 **1..86400** 的整数秒 ——
   `0` / `000` / 超 uint32 的值在 Perl 里等于 `alarm 0` = **取消闹钟**，只判「非负整数」会放行，
   等于把保护静默关掉（Codex r1 HIGH-1）。实现上先判数字、再剥前导零、**先按长度拦再比大小**
   （`[ -gt ]` 比一个 30 位数字会 rc=2、`if` 判假 ⇒ 反而放行）。
6. **超时信号走带外标记（r1 整改）**：npm 自己 `exit 124` 与「上限到点」在退出码上无法区分
   （Codex r1 MEDIUM-2）。改为 shell 生成 `CLS-NPM-BUILD-TIMEDOUT-$$-$TS` 传给 perl（单一来源），
   子进程 `exec` 前把 stdout/stderr 改到 `/dev/null`，父进程仅在闹钟触发时打印该标记；
   bash 侧按标记判定，不再看退出码。
7. **杀信号补窗口（r1 整改）**：`kill(-15,$pid) or kill(15,$pid)`（KILL 同形）——
   覆盖 `fork → setpgrp` 之间子进程尚未自成组的窗口。

### 2.2 `backend/tests/unit/test_deploy_vault_sh.py`

1. 模块级 `_SUBPROCESS_TIMEOUT = 600`（依据写在常量上方注释里），16 处裸跑逐个加
   `timeout=_SUBPROCESS_TIMEOUT`；既有 4 处与 `:603` helper 转发**未动**。
2. 新增 6 条用例（4 个 def，含两个 parametrize）+ 一套假 harness / 假 npm 辅助
   （`_npm_cap_harness` / `_npm_cap_env` / `_npm_cap_run` / `_npm_was_invoked` / `_pid_gone` / `_reap`），
   **零新增 `subprocess.run`**（全部经既有 `_run`）⇒ AST 总数仍 20。
   - `test_preflight_npm_build_is_walltime_capped`（承重，先红后绿；含「同组后代一并消失」断言）
   - `test_preflight_npm_build_cap_does_not_kill_a_fast_build`（正向对照 = 负控②；
     **并断言 `npm_config_offline=true` 真的到了 npm 手里** —— r1 LOW-1 后半）
   - `test_preflight_npm_build_failure_is_not_reported_as_timeout[fail]` / `[rc124]`
     （文案可分辨 = 负控③；`rc124` 是 r1 MEDIUM-2 的回归门）
   - `test_preflight_rejects_cap_values_that_would_silently_disable_it[0 / 000 / 4294967296 / abc]`
     （r1 HIGH-1 的回归门，并断言「拒在调 npm 之前」）
   - `test_preflight_accepts_leading_zero_cap`（控制组：`005` = 合法 5 秒，不能被误拒）
   每条都先断言 `_npm_was_invoked(pids)`，把「没走到 build 分支」与「上限没生效」分开诊断。
3. 假 harness 是**自洽**的：四个必需文件 + 9 个含 `SKILL.md` 的目录（缺省 `CLS_MIN_SKILLS=9` 零余量）
   + 指向 `sys.executable` 的 venv python + 两个恒等命名函数（不动点判据）+ 空的前端插件目录
   （**恒无 `main.js` ⇒ 恒走 build 分支**）。`install-vault.sh` 是恒 rc=1 的桩 ⇒ build 过关后整跑停在步 2。
   ⇒ 三条用例**不加**既有那条 `main.js` skipif，也**不联网、不跑真 build、不依赖本机树状态**。

---

## 三 DoD-3

### 4-A Claude 已代验（裁判逐条，全部当场跑、全部落盘）

| # | 判据 | 结果 | 存档 |
|---|---|---|---|
| 1 | 状态 + §〇 逐字核 + `timeout` 命令 ABSENT | 全绿（见 §一） | `manual-scope-…194807.txt` / `open-facts-A-…194826.txt` / `open-facts-B-…194837.txt` |
| 2a | **先红①** AST（改前） | `total 20 with 4 [77, 462, 1873, 2447] WITHOUT 16 […]`；**验伪锚命中**（探针能识别已带 `timeout=` 的 4 处） | `ast-open-20260914T194902.txt` |
| 2b | **改后绿** AST | `total 20 with 20 […] WITHOUT 0 []`；既有 4 处值仍为 `timeout`/`120`/`600`/`120` | `ast-close-20260914T195612.txt` |
| 3 | 脚本 wrapper 静态核 | `bash -n` rc=0；`npm_config_offline` 在 env 段 `:574`；`perl/alarm/kill/…` 改前 0 → 改后 12 命中（锚 `npm` 14→20）〔该行行号为 r1 时点值，终值见判据 15〕 | `script-grep-open-20260914T194847.txt` / `script-grep-close-20260914T195804.txt` |
| 4a | **先红②** 行为（改前） | `subprocess.TimeoutExpired … timed out after 45 seconds`，**耗时 45.59s** = 无限挂起 | `script-open-20260914T195329.txt` |
| 4b | **改后绿** 行为 | 3 passed，承重那条 **8.27s**（cap 5s + TERM→KILL 2s + 开销）；rc=71 + 超时专属文案；**假 npm 与其孙子进程都已消失**（进程组全杀） | `script-close-20260914T195516.txt` |
| 5 | 负控三段 + 跑前跑后 `shasum` | ① 变异（删一处 `timeout=`）→ `WITHOUT 0→1 [498]` → 还原后 sha256 **逐字节同**；② 秒级假 npm → `[1/6] preflight: OK … main.js 已 build 并就位`；③ `CLS_NPM_BUILD_TIMEOUT=1` 挂起 → 超时文案 / 立刻 rc=1 → 「失败」文案且**不含「超时」** | `negctl-20260914T195738.txt` |
| 6 | 地盘门 | 改动集合 = `{scripts/deploy-vault.sh, backend/tests/unit/test_deploy_vault_sh.py}`；`backend/app` 改动 **0**；`fsrs_bridge`/`decay_beta` **0 命中**（锚 3 / 10） | `scope-gate-20260914T195832.txt` |
| 6b | **步 5/6 未动（逐字节）** | `step2_install` 到文件尾：基线与改后 sha256 同为 `96d10556a71e71c3…`（33631 bytes）⇒ 步 2-6 + 主流程零改动；验伪锚：头部（本卡确实改过）两 sha **不同** | 同上 |
| 7 | ruff（zsh 数组） | `ruff check` / `ruff format --check` 均绿；三条验伪锚 **F821 / E9 / format 各 rc=1** | `ruff-20260914T195908.txt`（`ruff-live-…195843.txt` 是被推翻的首版，见 §六.2） |
| 8 | `tests/unit` 目录级（同口径 `--ignore tests/unit/…` 相对路径，R-B14-3） | `35 failed / 5077 passed / 48 skipped / 23 xfailed / 29 errors`；nodeid 口径 **64 vs 64，diff 完全一致**（0 行）；验伪锚 `diff` rc=1 | `unit-close-20260914T200536.txt` / `unit-diff-20260914T201203.txt` / `unit-diff-falsifier-20260914T201210.txt` |
| 9 | 文件级全绿 + 墙钟上限 | **139 passed / 9 skipped / 0 failed**，pytest 28.35s（含启动墙钟 42s）；9 条 skip 全是「树上无 `main.js`」那族 | `deploy-file-20260914T195639.txt` |
| 10 | 现网只读 | live vault `find -newer <第 0 分钟证据>` = **0**；验伪锚：同尺子对本卡 evidence 目录 = 12 | `ruff-live-20260914T195843.txt` |

**r1 整改后全部重跑**（代码改了就不能引用旧存档 —— 「绑定仍成立 ≠ 门还绿」）：

| # | 判据 | 结果 | 存档 |
|---|---|---|---|
| 11 | 定向 9 条（新旧用例全体） | **9 passed**（收集数 9，非零收集）；承重那条 8.52s | `r1fix-targeted-20260914T202156.txt` |
| 12 | **负控第四段：三处整改的变异杀伤力** | m1 撤回取值范围 → `cap_values` **3 failed / 1 passed**（`abc` 仍被数字判据拦下，符合变异面）且承重那条仍绿（变异是定向的）；m2 超时改回看退出码 → **`[rc124]` 变体 FAILED**、`[fail]` 仍绿；m3 删掉 `npm_config_offline` 注入 → 正向对照那条 **FAILED**；还原后两文件 shasum **逐字节同**、指定门 7 passed | `negctl2-20260914T202240.txt` |
| 13 | 文件级（整改后） | **145 passed / 9 skipped / 0 failed**，29.33s（墙钟 41s） | `deploy-file-r1fix-20260914T202625.txt` |
| 14 | `tests/unit` 目录级（整改后，同口径） | `35 failed / 5077 passed / 29 errors`；nodeid **64 vs 64，diff rc=0 完全一致** | `unit-close-r1fix-20260914T202713.txt` |
| 16 | **负控第五段（r2 整改后重跑，驱动已按 r2 LOW-2 重写）** | 七例全 **MATCH**、**MISMATCH=0**：n1 撤回 locale 修复 → `[ar_EG.UTF-8]` 红（断言正文：`'٠٥' 被放行 ⇒ 假 npm 挂住了整跑`）、`[C]` 对照绿；m1 撤范围校验 → `0`/`000`/`4294967296` 红、`abc` 仍绿（该变异只撤范围不撤字符集）；m2 → `[rc124]` 红；m3 → 离线断言红（`offline=<unset>` vs `offline=true`）；还原后 shasum 逐字节同、11 passed | `negctl3-20260914T205017.txt` + 七份逐例全量日志 `negctl3-n1-locale-205017.txt` / `negctl3-n1-ctrl-legal-205117.txt` / `negctl3-m1-range-205135.txt` / `negctl3-m1-ctrl-hang-205406.txt` / `negctl3-m2-rc124-205427.txt` / `negctl3-m3-offline-205444.txt` / `negctl3-restore-all-205500.txt` |
| 17 | 终态文件级 + `tests/unit` + 静态门 | **147 passed / 9 skipped / 0 failed**（35.13s，墙钟 48s）；nodeid **64 vs 64 diff rc=0**（两个集合本身已落盘，可独立重算）；静态门全套绿 | `deploy-file-r2fix-20260914T205549.txt` / `unit-close-r2fix-20260914T205645.txt` / `unit-nodeids-r2fix-20260914T205645.txt` / `gates-r2fix-20260914T210350.txt` |
| 18 | **收尾核验（最终 HEAD `36bf9544`）** | 末轮绑定成立（对 r3 审 SHA 只有纯注释差异）；地盘仍两文件（验伪锚 -z 口径 43 → 0）；`backend/app` 0；入库 `*.stderr` **0**（锚 3 证明尺子会命中）；4 条 commit 全含卡号、header 98/97/91/94 均 ≤100；**origin 无该分支 ⇒ 从未 push** | `final-close-20260914T211431.txt` |
| 19 | **D-32 等价核** | 审后唯一代码改动 = 纯注释：剥注释后两端各 **960 行 sha256 `ad4f36b3…` 相同**，验伪锚（含注释全文 sha 不同）证明尺子会动，`bash -n` rc=0，定向 11 条绿 | `d32-comment-equivalence-20260914T211237.txt` |
| 15 | 静态门全套（整改后） | `bash -n` rc=0；AST `with 20 / WITHOUT 0`；`npm_config_offline` 在 env 段 `:601`；`timeout` 非注释行计数 **0**（锚 perl=1）；`step2_install`..EOF sha256 仍 `96d10556…`；地盘仍两文件；`backend/app` 0；`fsrs_bridge`/`decay_beta` 0 命中；ruff check/format 绿；live vault `-newer` **0**（锚 21） | `gates-r1fix-20260914T203249.txt` |

### 4-B 你来验（零技术词）

> 我按一键部署的第一步往下走，碰到卡住的环节它会在几秒内自己停下来并告诉我哪一步超时，
> 而不是一直转圈等下去——我感觉这一步终于不会把我晾在那儿了。

**felt-sense**：以前如果第一步要现场编译插件、而编译卡住了（等网、等锁），整条部署会**一声不吭地
停在那儿**，你只能自己去猜是不是死了、要不要 Ctrl-C。现在最多等 5 分钟（可以改），到点它会自己
收手，并明说「这一步超时了」。编译正常时（几秒就完事）你**不会有任何感觉**——一切照旧。

**如果你注意到：本来能装好的 vault 现在装不上了、或第一步报了以前没见过的错，那就是我做错了，
请告诉我。**

---

## 四 只核不改（写明理由）

| 对象 | 为什么不改 | 核对结果 |
|---|---|---|
| `deploy-vault.sh` 步 5 `step5_activate` / 步 6 `step6_evidence` / `run_step` 六次调用 | 是 **T2-B CARD-G2-8** 的面 | `step2_install`..EOF 逐字节相同（sha256 `96d10556…`） |
| `scripts/cls_forbidden_paths.py` | 禁写面负控本体，保持不变 | 零改动（地盘门） |
| `scripts/vault-install-manifest.json` / `.claude/skills/deploy-vault/SKILL.md` / `docker-compose*.yml` / `backend/tests/unit/test_docker_compose_config.py` | 属 T2-B..E 及其它卡 | 零改动（地盘门） |
| `backend/app/**` | 本卡零生产改动 ⇒ `python-typecheck` 不触发，候选树 `pyright app = 0` 不受影响 | `git diff --name-only 08100483 -- backend/app` = 0 行 |
| `canvas-vault/.claude/scripts/fsrs_bridge.py` / `decay_beta.py` | 本批**零写者**（碰它 = 触发 live 部署铁律） | 两文件 0 命中（锚 3/10 证明尺子会命中） |
| live vault / 7691 / 7687 / 现网 LanceDB | 只读 | `-newer` 计数 0；全程未起任何容器、未连任何端口 |

---

## 五 本卡未证明什么（⚠️ 逐条如实）

1. **未证明离线标志能在缓存 / `node_modules` 缺失时离线产出 `main.js`**。本树 `main.js` 与前端
   依赖都不在，本卡只验证「超时形态 + 假 npm 先红后绿」。真 build × 离线的全绿，须由主 session
   在 `main.js`（及 `node_modules`）就位的候选树上撤 `--ignore` 后复跑核。
2. **未证明 npm 的完整写入集合 / 是否还有别的等网路径**。脚本 `:539-540` 原有的如实声明
   （「只约束了 npm 配置层能约束的部分，完整写入集合未证明」）在本卡后**依然成立** —— 本卡只加了
   上限与离线开关，没有读 npm 实现。
3. **「杀到整个进程组」只证到了同组后代这一层**。判据是「假 npm（组长）+ 它 fork 的一个 `sleep`
   后代在上限到点后都消失」。**没有**证明更深层级、也**明确不**声称能杀干净进程树 ——
   Codex r1 MEDIUM-1 用独立探针实测：后代若自己 `setsid()`（Node 的 `detached: true` 即可做到），
   它会脱离被杀的进程组、在 wrapper 已返回 124 之后继续存活。本上限保证的是**本步骤按时返回**，
   不是「进程树一定清空」；该边界已写进脚本头注（= `--help` 输出），不藏在验收单里。
4. **未逐跑实测 16 处各自的最坏耗时**。600 是保守上限（取脚本上限的 2 倍 + 与 `3966ddad` 同值），
   不是紧界；对 `bash -n` / `git log` 这类毫秒级的跑显然过松，本卡只保证「有界」不保证「紧」。
5. **未复现候选树上的真·build 挂起**。本树 `main.js` 缺席 ⇒ 那族用例 skip（9 条），本卡靠假 npm
   代偿。R-15 描述的现场本身是**时点性**的，本卡没有在那个现场重放。
6. **未定位挂起是否确由网络引起**。本卡给的是旁证（离线开关 + 假 npm 反证），**不是** npm 源码级
   的因果证明。「挂起根因」小节（§六.1）只声称到证据支持的程度。
7. ~~lefthook 没跑 / 命中面未知~~ —— **此条已被实测推翻两次，最终结论见 §六.5**：lefthook 2.1.6
   确实执行（pre-commit / commit-msg / post-commit 三个钩子都打印），且 `python-lint` **覆盖**本卡的
   `backend/tests/unit/*.py`（实测它跑了），`python-typecheck` 恒 skip（glob `backend/app/*.py`，
   本卡零改动）。全程未用任何 `LEFTHOOK_EXCLUDE`。⇒ 这条不再属于「未证明」，保留编号只为让
   §六.5 的订正链有锚点。
8. **300:600 的先后顺序只是「通常」不是保证**（Codex r1 LOW-2，已认）：alarm 只覆盖 build 本身，
   步 1 前段的判据另计时，到点后还有 2s 清理宽限；用户把 `CLS_NPM_BUILD_TIMEOUT` 调到 >600
   时顺序必然反过来。头注已按此改写。
9. **离线开关不是网络隔离**（Codex r1 LOW-1，已认）：`npm_config_offline` 只约束 npm 自己的取包
   路径；`npm run build` 跑的 package.json 脚本自己发的请求（curl / fetch / 下载 binary）不受它
   约束 —— 真正兜住那类等待的是墙钟上限。本卡**没有**验证过真实 build 脚本的网络行为。
10. **locale 回归门的可移植性未证明**（Codex r3 ② 指出）：`[ar_EG.UTF-8]` 那条**承重**，
    `[C]` 只是对照（旧实现本来就拒）。用例**没有断言** `ar_EG.UTF-8` 在本机可用 —— 换一台没有
    该 locale 的机器，两条都会绿，但那时它证明的**不是**「旧缺陷被修」。本机已单独实测前提成立
    （§八 Round 2 四条），但那是**这台机器这一天**的结论，不是用例自带的不变量。
11. **`_reap` 的 PID 复用窗口没有消除**（Codex r2/r3 LOW-1）：只做到「先探活再发信号 + 只发一次
    KILL」，没有进程身份校验（无可移植手段）。极低概率下会把信号发给复用了该 PID 的无关进程。
12. **负控驱动的 rc 不承重**（Codex r3 LOW-2）：`negctl3` 在 MISMATCH≠0 时末行仍是 `echo`、
    整体 rc 恒 0；`mutate` 失败时直接跳过且不计入 MISMATCH。本轮七例齐全且全 MATCH（有全量日志
    可逐条核），但**该驱动本身不是一个会失败的门** —— 复用模板前必须照 §七.11 改。
13. **`ruff check` 绿的含金量有限**：本仓生效配置 `backend/ruff.toml` 的 `select` 只有
   `["E9","F63","F7","F82"]`（语法错 + 少量真错），不含 F401 之类风格规则。真正承重的是
   `ruff format --check` 与 pytest。

---

## 六 本卡执行中被推翻 / 订正的判据（3 条，都在证据里留了痕）

### 6.1 §二.3「命中行全部落在步 1 `:387-567` 区间内」—— **在正确实现下不可能成立**

完成条件 (e) 同时要求上限是「**可配置 env 变量 + 文档化默认值**」。文档在头注（= `--help` 输出）、
缺省赋值必须在 `set -euo pipefail` 之后与 `CLS_MIN_SKILLS` 同处 —— 两者都必然落在步 1 之外。
⇒ 按该判据的**意图**（步 1 之外零代码改动）加固为两条：① 命中逐条分类（注释 `:63/:70/:559` /
缺省赋值 `:87` / 步 1 体内其余全部）；② **`step2_install`..EOF 逐字节 sha256 对照**（比行号区间强：
它对行号位移免疫，且能证明步 2-6 与主流程一个字节都没动）。证据 `script-grep-close-…195804.txt`
与 `scope-gate-…195832.txt`。

### 6.2 §二.7 的 ruff 验伪锚（F401）在本仓**恒不成立** —— 首版锚失败，已换

首版按卡文喂了一个只含 `import os` 的文件，`ruff check` 报 `All checks passed!` rc=0
（`ruff-live-20260914T195843.txt` 里留着这次失败）。根因**不是**尺子坏了，而是：① 本仓 lint
`select` 不含 F401；② 探针放在 scratchpad，生效的是仓根 `ruff.toml`（`select = []`）而不是文件
真正适用的 `backend/ruff.toml`。改成**同一份 `--config backend/ruff.toml`** + 换用真被启用的规则：
F821（未定义名）rc=1、E9（语法错）rc=1、`format --check` rc=1 —— 三条锚全部出声
（`ruff-20260914T195908.txt`）。

### 6.3 `diff` 验伪锚的 rc 被 `head` 吃掉（与协议「`| tail -1` 取汇总行」同族）

`diff a b | head -3; echo $?` 取到的是 `head` 的 rc（恒 0）。虽然该锚的**输出**（`1d0 < ERROR …`）
已足以证明尺子会出声，仍当场重测：`diff … > /dev/null; echo $?` → 锚 **rc=1**、真判据 **rc=0**
（`unit-diff-falsifier-20260914T201210.txt`）。

### 6.4 顺带：一份被 `tail -40` 截断的 `tests/unit` 存档**未入库**

首跑误写 `| tail -40 | tee`，存档只剩末 40 行、FAILED 清单不全，无法支撑 nodeid 级 diff。
该文件已移出 evidence 目录（不入库），`tests/unit` **全量重跑**一次并全量落盘
（`unit-close-20260914T200536.txt`，1181 行 / 110935 bytes）。

### 6.5 ⚠️ 自述订正（两轮）：lefthook 不但在跑，而且**覆盖**本卡的测试文件

- **初版说法（错）**：首次 commit 打印了一串 `core.hooksPath` 提示，我据此写「lefthook 在本机没有
  真正执行」。
- **第一次订正（仍不完整）**：第二次 commit 输出里有 `✔️ spec-reference` ⇒ lefthook 是跑的；
  但我把「`python-lint` 的 glob `{backend,src,scripts}/*.py` 是否命中更深一层的
  `backend/tests/unit/*.py`」留成了「未确认」。
- **第二次订正（实测定案，`lefthook-coverage2-20260914T211543.txt`）**：把本卡文件真正暂存后跑
  `/opt/homebrew/bin/lefthook run pre-commit`，逐 job 的命中/跳过理由自带锚 ——
  `python-lint ❯`（**跑了**）、`python-typecheck (skip) no files for inspection`、
  其余 5 个 `(skip) no matching staged files`。⇒ **本卡文件在 python-lint 覆盖面内**。
- 那次探针跑里 python-lint `exit status 1`，已归因：是**探针追加的那一行**让 `ruff format --check`
  判要重排（同一命令对真实内容是 `All checks passed!` + `1 file already formatted`）。
  旁证：本卡 5 条 commit 全部成功落地，而 pre-commit 非零会中止 commit（commitlint 拦下
  `body-max-line-length` 那次就是实测）⇒ python-lint 在每次真实提交时都跑过且通过。
- **顺带一条工具坑**：第一版探针用 `lefthook run pre-commit --files <path>`，lefthook 2.1.6 报
  `flag provided but not defined: -files` —— 目标跑与验伪锚跑**都**因此无输出，锚没响 ⇒ 当时不能
  从目标的沉默下任何结论（与 R-B14-1「`--no-auto-install` 是 lefthook 1.x 的 flag」同族）。
  该版判据已作废，并如实写在 `lefthook-coverage2-…txt` 的抬头。

### 6.6 「挂起根因」小节（本卡能声称到哪一步）

- **可断言**：步 1 的 `npm run build` 原先**没有任何墙钟上限** —— 只要 npm 不返回，整条部署与调它的
  单测就永远不返回。先红那跑（45.59s 挂到裁判上限、脚本自身零反应）是这条的直接证据。
- **可断言**：加上限后，同一输入下步 1 在上限 + 2s 内以 rc 71 + 超时文案返回（8.27s / 3.3s 两跑）。
- **不可断言**：npm 在真实场景里到底是**等网**还是等锁 / 等别的资源。本卡加了 `npm_config_offline`
  这条「不等网」的路，但**没有**在真 build 上对照测过（本树无 `node_modules`）⇒ 归 §五.1/§五.6。

---

## 七 台账待登记条目（车道不改台账，只登记）

1. **本卡修复 sha**：代码 + 证据 `7413283a`（收尾文档另一 commit，纯 `_bmad-output`）。
   关键 nodeid 三条：`test_preflight_npm_build_is_walltime_capped` /
   `…_cap_does_not_kill_a_fast_build` / `…_failure_is_not_reported_as_timeout`；
   AST `WITHOUT 16 → 0` 证据 `ast-open-20260914T194902.txt` → `ast-close-20260914T195612.txt`。
2. **16 处裸跑加 `timeout=` 的行清单**（改后）：`108/498/508/689/898/958/1029/1289/1654/1704/
   1948/1953/1961/1995/1999/2358`，常量 `_SUBPROCESS_TIMEOUT = 600`（依据：与 `3966ddad` 的
   `:1894 timeout=600` 同值 + 脚本上限 300 的 2 倍）。既有 4 处 `89/474/1894/2482` 未动。
3. **步 1 超时形态**：`perl alarm` + `setpgrp(0,0)` + 对进程组 `TERM`→2s→`KILL`，rc 124；
   env 开关 `CLS_NPM_BUILD_TIMEOUT`（缺省 300s）/ `CLS_NPM_BUILD_OFFLINE`（缺省 true →
   `npm_config_offline` 进 env 段 `:574`）。
4. **R-15 承接闭环**：集成修复 `3966ddad` 的单点 `timeout=600` **保留不撤**，本卡补齐其余 15 + 脚本侧
   1 处。⇒ **主 session 合入本卡后，撤 `--ignore tests/unit/test_deploy_vault_sh.py` 重取 unit 基线**
   （64 → 新值；本卡在候选树的 139 passed / 9 skipped 会随 `main.js` 是否在位而变，见第 6 条）。
5. **挂起根因结论**：只到「无上限 ⇒ 不返回」这一步；「是否等网」未证（§六.5 / §五.6）。
   证据 `script-open-20260914T195329.txt`（45.59s）/ `script-close-20260914T195516.txt`（8.27s）/
   `negctl-20260914T195738.txt`。
6. **离线 × 真 build 的复跑移交**：需在 `main.js` 与 `node_modules` 就位的候选树上，跑
   `test_deploy_vault_sh.py` 全量（那 9 条 skip 会变成真跑）并观察 `CLS_NPM_BUILD_OFFLINE=true` 下
   build 能否产出 `main.js`。若不能 ⇒ 需要在部署文档里写明「首次部署需联网预热 npm 缓存」或把缺省
   改成 false（本卡把开关留出来了，改缺省是一行）。
7. **Codex 各轮**：见 §八（存档路径 / 绑定 SHA / B·H·M·L 计数）。
8. **口径更正三条**（本卡实测）：① 卡文 §二.3「`perl/alarm/…` 命中全在步 1 区间」不可能成立，已按
   意图加固（§六.1）；② 卡文 §二.7 的 F401 验伪锚在本仓恒不成立，已换 F821/E9/format（§六.2）；
   ③ `grep -c 'timeout='`=5 的第 5 处在 `:603`（helper kwarg）—— 卡文已记，本卡复测确认。
9. **lefthook 与 `core.hooksPath`**：首次 commit 打印 hooksPath 提示、第二次 commit 出现
   `✔️ spec-reference` ⇒ lefthook 在跑；未确认的是 `python-lint` 的 glob `{backend,src,scripts}/*.py`
   是否命中 `backend/tests/unit/*.py`（更深一层）。若这是全批共性，值得主 session 统一裁一次（§五.7、§六.5）。
10. **⛔ 值得进全批纪律的一条新坑（locale 依赖的字符类）**：shell `case`/`[[ ]]` 里的
    `[0-9]`、`[a-z]` 等**区间**由 locale 的排序决定 —— `LC_ALL=ar_EG.UTF-8` 下阿拉伯数字 `٠٥`
    会被 `[0-9]` 当成数字放行。凡是「校验用户可控取值是不是数字」的地方都应写**逐字符枚举**
    `[!0123456789]`。配套的第二条：`if [ "$x" -lt 1 ]` 在 `$x` 非数字时 rc=2，`if` 判假 ⇒
    **fail-open**；数值比较必须放在「已确认是纯 ASCII 数字」之后。本卡两条都被 Codex r2 抓到，
    建议主 session 扫一遍全仓同形写法（`grep -n '\[0-9\]' scripts/ backend/`）。
11. **⛔ 第二条新坑（判据驱动自身的红绿判定）**：负控驱动若把 `rc` 取来不用、或用 `tail -N`
    取汇总，会得到「看起来跑了其实没判」的存档（Codex r2 LOW-2）。本卡重写为「红绿由 pytest
    汇总行判定 + 预期值参与比对打印 MATCH/MISMATCH + 保留失败断言正文 + 每例留全量日志」，
    驱动模板可复用（`negctl3` 源码逐字在 `negctl3-20260914T205017.txt` 里）。
12. **本卡自己踩的 `$VAR` 紧跟全角括号坑**：负控驱动末行写 `$MISMATCH（必须为 0）` ⇒
    被当成变量名 `MISMATCH（` → unbound variable。这正是被测脚本 `test_no_var_ref_followed_by_non_ascii`
    守的那个坑，但**判据脚本自己不在那道门的覆盖面内**。那一版存档未入库，已改 `${VAR}` 重跑。

---

## 八 Codex 复核（D-15：多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0，上限 5）

命令固定：`codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra"`（codex-cli 0.153.3）。
每份存档首部六行 blockquote（协议 §2.1），会话头自证抄 `.stderr` 里含版本行 + `model:` 行 +
`reasoning effort` 行的三行并括注行号；`.stderr` 本身不入库（`.gitignore:264` 覆盖，已 `git check-ignore` 实测）。

### Round 1（审 SHA `7413283a`）：**BLOCKER 0 / HIGH 1 / MEDIUM 2 / LOW 3** ⇒ 未达标，已整改

存档 `_bmad-output/审查/codex-review-CARD-DEPLOY-TIMEOUT.md`；prompt `prompts/codex-prompt-CARD-DEPLOY-TIMEOUT.md`。

| 编号 | 结论 | 车道处置 |
|---|---|---|
| HIGH-1 | `CLS_NPM_BUILD_TIMEOUT=0` / `000` / `4294967296` 能过旧校验，但 Perl 里 `alarm 0` = **取消闹钟**（`4294967297` 截成 1s）⇒ 保护静默消失 | **认，已修**：改 1..86400 有界正整数，长度先拦再比大小；4 条参数化回归门 |
| MEDIUM-1 | 组信号语义正确；但后代自己 `setsid()` 会脱离被杀的组（独立探针实测 wrapper 返回 124 后孙进程仍存活）；`fork→setpgrp` 窗口信号未检查 | **部分修 + 如实登记**：`kill(-15,$pid) or kill(15,$pid)` 补窗口；「脱组后代」写进头注与 §五.3，**不声称**清空进程树 |
| MEDIUM-2 | 假 npm 立刻 `exit 124` 会被误报成超时（退出码碰撞） | **认，已修**：超时改走带外标记；新增 `rc124` 回归门 |
| LOW-1 | 「整个 build 不等网」说法过强；且三条用例都没断言该开关 —— 删掉注入行也不会变红 | **认，已修**：头注收回说法；假 npm 落盘收到的 `npm_config_offline`，用例断言 `=true` |
| LOW-2 | 300:600 不能保证脚本超时「必定」先于裁判超时 | **认，改文案**为「通常」+ 三个例外 |
| LOW-3 | 目录级 diff 的负控存档记了 `probe_diff_rc=0`（预期 1） | **认**：当场已重测（§六.3），r2 prompt 指向该文件 |

### Round 2（审 SHA `71a85acf`）：**BLOCKER 0 / HIGH 1 / MEDIUM 0 / LOW 3** ⇒ 仍未达标，已整改

存档 `_bmad-output/审查/codex-review-CARD-DEPLOY-TIMEOUT-r2.md`；prompt `prompts/codex-prompt-CARD-DEPLOY-TIMEOUT-r2.md`。
r1 的 MEDIUM-2 判定已关闭；**HIGH 换了一个面**（不是同一条没修好）：

| 编号 | 结论 | 车道处置 |
|---|---|---|
| HIGH-1 | `[!0-9]` 的**区间**由 locale 排序决定：`LC_ALL=ar_EG.UTF-8` 下 `٠٥` 过数字门 → `[ -lt ]` 报错 rc=2 → `if` 判假 → **放行** → `alarm '٠٥'` = alarm 0 | **认，已修**：逐字符枚举 `[!0123456789]`（剥零前后各一次）+ 数值比较挪到「已确认 1-5 位纯 ASCII 数字」之后 + 原串 >20 位直接拒；新增 2 条 locale 回归门 |
| LOW-1 | `_reap` 按裸 PID 杀，PID 复用时可能误杀 | **收窄 + 登记**：先探活再发信号、直接 KILL 少一个窗口；窗口不为零写进 docstring 与 §五 |
| LOW-2 | 负控驱动的 rc「取得后弃用」、预期参数 `$3` 没参与判定、`tail -3` 不足以排除「红于别的原因」 | **认，已重写**（§三 4-A 判据 16） |
| LOW-3 | 头注三处超出实现：固定 `/usr/bin/perl` / 「超 uint32 一律取消闹钟」/「本步骤按时返回」 | **认，三处全改**（perl 走 PATH；截断的两种后果分别写；改成「这条 build 不会无限等下去」） |

**本机对 r2 HIGH-1 的四条前提复测**（控制组必须成立，否则回归门是假的）：
`locale -a` 有 `ar_EG.UTF-8` ✅；旧写法对 `٠٥` **通过（被骗）**、新写法**拒绝** ✅；
`[ '٠٥' -lt 1 ]` 报 `integer expression expected` ✅；`perl -e 'alarm "٠٥"'` 剩余 **0** ✅。

### Round 3（审 SHA `25f56065` = **最终代码 HEAD**）：**BLOCKER 0 / HIGH 0 / MEDIUM 0 / LOW 3** ✅ 达标

存档 `_bmad-output/审查/codex-review-CARD-DEPLOY-TIMEOUT-r3.md`；prompt `prompts/codex-prompt-CARD-DEPLOY-TIMEOUT-r3.md`。
Codex 明写「r2 HIGH-1 的 locale 问题已修复」，并**独立重算**了三件事：① 两个 nodeid 集合各 64 条、
双向差集为空（r2「无法独立重算」那条限制解除）；② `step2_install` 到 EOF = 33,631 bytes、
SHA-256 `96d10556…` 两端相同 ⇒ 步 5/6 与主流程逐字节未动；③ 自己跑内存探针复现了旧代码在
阿拉伯 locale 下放行 `٠٥`、比较报错、Perl 最终 alarm 0，以及新代码在两个 locale 各 34 个边界输入
全部符合预期。

三条 LOW **登记不阻断**：

| 编号 | 结论 | 车道处置 |
|---|---|---|
| LOW-1 | `_reap` 仍可能误杀复用 PID 的无关进程（r2 LOW-1 只是缓解，不是消除） | **登记**：这是测试侧收尸辅助的固有局限（无可移植的进程身份校验），已写进 docstring 与 §五 |
| LOW-2 | 负控驱动：`mutate` 失败时直接跳过且不计 MISMATCH；MISMATCH≠0 时末行仍 `echo`、**rc 恒 0** | **登记不改存档**：Codex 同时确认「本轮七例齐全且全部匹配，不推翻本轮结果」；改驱动 ⇒ 存档与被审对象不一致，故保留原样，修法写进 §七.11 供后人复用模板时照改 |
| LOW-3 | 头注漏写新增的「原串最多 20 位」约束（20 个前导零 + `1` 数值在 1..86400 内但会被拒） | **认，已补**——**纯注释**改动，按 **D-32** 不重置轮次；等价核见下 |

**D-32 等价核（审后唯一的代码文件改动 = 纯注释）**：`evidence-deploy-timeout/d32-comment-equivalence-20260914T211237.txt`
—— 剥掉全部注释行后，审 SHA 与工作树都是 **960 行、sha256 `ad4f36b3…` 完全相同**；
验伪锚（含注释全文 sha 不同）证明尺子会动；`bash -n` rc=0；定向 11 条仍全绿。
⇒ 末轮绑定成立：**`git diff 25f56065 HEAD -- . ':(exclude)_bmad-output'` 的非注释面为空**。

**轮次统计**：3 轮（上限 5）。r1 HIGH 1 → r2 HIGH 1（换面，非同条未修好）→ r3 HIGH 0。
