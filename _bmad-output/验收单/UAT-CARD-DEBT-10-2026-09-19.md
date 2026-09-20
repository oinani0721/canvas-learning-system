# UAT — CARD-DEBT-10 `~/Library` 机器级安装副本 manifest 化

> 批次 `[BATCH-2026-09-18-第十五批 / CARD-DEBT-10]` · 车道 `card-p3-deploy`（分支 `card/p3-deploy`，本车道第 2/3 张）
> 卡文 `_bmad-output/implementation-artifacts/goal-cards/第十五批-goals/P3-B.md`

## 终态字段

| 字段 | 值 |
|---|---|
| 起点 `PREV` | `4cc6a78c`（P3-A CARD-G2-11 末 commit） |
| 最终代码 SHA | **`8fe610bd`** |
| 代码 commit 数 | **1**（卡文 (o)：代码单独一个 commit；四次 amend 收敛，中间 SHA 只在 reflog） |
| 改动面 | 4 个文件 / 3221 行纯新增 / **0 删除** |
| Codex 轮次 | r1 绑 `390f25cf`（4 HIGH + 6 MEDIUM，全部整改）；**r2 配额阻断 ⇒ 末轮未绑最终 HEAD，移交主 session**（详见 §9） |
| 内部对抗复核 | 两轮：38/26 确认、28/21 确认，**全部整改**，均有落盘 journal（详见 §5 / §9） |
| 负控 | 10 段，9 击杀 / 1 存活（已验伪归类，详见 §11） |
| 真机 `--apply` | **SKIP（未授权）** —— 用户未说「DEBT-10 授权重装」，且真机 DRIFT = 0，无事可做 |

> ⛔ **给主 session 的一句话**：代码面全绿（零写双门 PASS、281 passed、真机只读 rc 0、地盘 0 越界、
> 负控 9/10 击杀），但 **Codex 末轮没能绑最终 HEAD**（外部配额耗尽，两次 0 字节，`codex login status`
> 已排除鉴权因素）。按 D-15 这不算「通过」，我不自判，交主 session 裁。替代证据是两轮落盘的内部对抗
> 复核，其中第二轮抓出并修掉了我自己整改时引入的一条 HIGH。

## 1 做了什么（一句话）

这台 Mac 上有 6 件「定时任务」的安装副本（5 个 launchd plist + 1 个复习链入口脚本），
此前仓库里没有任何东西记着它们该长什么样 —— 改了仓内源却忘了重装 = 复习链静默停摆
（2026-09-05 真的发生过一次）。本卡给这 6 件建了一张清单，配了一个只读体检程序，
外加一个会先把打算做的事列出来给人看的幂等重装。

## 2 完成条件逐条

### (a) 第 0 分钟 + §〇 核对 + 机器面快照

| 项 | 实测 |
|---|---|
| `pwd` | `…/worktrees/card-p3-deploy` ✅ |
| `git branch --show-current` | `card/p3-deploy` ✅ |
| `PREV=$(git rev-parse HEAD)` | `4cc6a78c…`，`log -1 --format=%s` 含 `CARD-G2-11` ✅ |
| `git merge-base --is-ancestor 9c4e7e82 HEAD` | TRUE ✅ |
| `git status --porcelain` | 0 行 ✅ |
| `backend/.venv/bin/pytest` / `backend/.env` | 均在位 ✅ |
| pyright 绝对路径 `test -x` | `EXEC_OK` ✅（本卡不改 `backend/app`，自证只为环境完整） |
| 红基线 `grep -vc '^#' $BASE` | **33** ✅ |
| 开工 `tests/unit` 目录级 | 32 failed / 5740 passed，`diff base open` 只有 `<`（少 `test_accept_candidate_already_accepted_returns_422`）—— 这是已登记的 W4 哨兵 nodeid 翻转（R-08/R-10），协议只允许 `<`，合规 |
| §〇 每条 `file:line` | **零漂移**（`:79-82` 四档退出码 / `:96` / `:100-101` / `:109` / `load_manifest:274-391` / `_write_report:916-961` / 三条门 `:174 :251 :261` / `deploy-vault.sh:59` / items 55 / version 2 / 132 + 244 个 test）✅ |
| 机器面只读快照 | `machine-inventory-open-20260918T223533.txt`，6 件 `ls -la` + `shasum` |

§〇 的两处「实测更正」复证成立：`ls ~/CanvasReview/bin` → `No such file or directory`（清单/总账
`:904` 的路径失实）；wrapper 真实安装根是 `~/Library/Application Support/CanvasReview/bin`。

### (b) 先红（改代码前落档，`structural-before-20260918T224145.txt`）

| 判据 | 改前 |
|---|---|
| `verify_vault_install.py --help \| grep -c -i -e launch -e machine -e Library` | **0** |
| `'machine_items' in manifest` | **False** |
| `grep -c Library scripts/vault-install-manifest.json` | **0** |
| `test -e scripts/verify_install_manifest.py` | `rc=1` |

### (c) manifest 6 件全登

顶层新键 `machine_items`，**纯追加 61 行 / 0 删除**；`items` 区逐字节不变（前缀实证
`prefix_len=15128`，`new.startswith(old_prefix)` = True）。2 件 `managed:repo` + 4 件
`managed:external`。`install` 一律 `~/` 开头（`:251` 门），条目不带 sha（`:261` 门）。

### (d) 4 个无源 plist 逐件裁定表

| Label | 已装路径 | `ProgramArguments[1]` 指向 | 触发 | 车道建议 | **用户裁定（2026-09-18）** |
|---|---|---|---|---|---|
| `com.canvas.memory-health` | `~/Library/LaunchAgents/com.canvas.memory-health.plist`（876 B） | `…/feature-obsidian-hybrid-dev/scripts/memory-health.sh`（tracked，151 行，原地执行） | RunAtLoad + 每天 9:00 | external | **登 external-managed** |
| `com.canvas.neo4j-backup` | `…/com.canvas.neo4j-backup.plist`（942 B） | `…/scripts/backup-neo4j.sh`（tracked，53 行） | 每天 4:30（无 RunAtLoad） | external | **登 external-managed** |
| `com.canvas.qwen-graphiti` | `…/com.canvas.qwen-graphiti.plist`（987 B） | `…/scripts/local-llm/start-qwen-graphiti.sh`（tracked，37 行） | RunAtLoad + KeepAlive{SuccessfulExit:false} + Throttle 30 | external | **登 external-managed** |
| `com.canvas.reranker-graphiti` | `…/com.canvas.reranker-graphiti.plist`（1003 B） | `…/scripts/local-llm/start-reranker-graphiti.sh`（tracked，26 行） | 同上 | external | **登 external-managed** |

裁定依据（已向用户完整解释并经其确认）：这 4 份 plist 里写死的是一条**开发用临时工作区**的
绝对路径，目录改名即失效；把它抄进仓库等于把「今天这台机器的临时状态」当成标准答案存起来。
相比之下 `com.canvas.daily-review.plist` 指的是固定不动的 `~/Library/Application Support/CanvasReview/bin/`
（wrapper 源 `:2-5` 白纸黑字说这是 memory-health 停摆 6 天的结构性修复）。
⇒ **仓库未新建任何 `scripts/launchd/*.plist`**（`--diff-filter=A` 实测 0）。

### (e) 校验器 + dry-run + apply 幂等 + 不调 launchctl

`scripts/verify_install_manifest.py`（NEW）。四档退出码与 `verify_vault_install.py:79-82` 同口径。
`imports = ['__future__','argparse','dataclasses','hashlib','json','os','pathlib','plistlib','stat','sys']`
—— **不 import subprocess**，AST 断言无 `system/popen/exec*/spawn*/eval/exec`，所以它**起不了任何外部程序**，
`launchctl` 自然也起不了。钉的是「能力」不是「名字」：名字判据换个拼法就绕开了。

### (f) 结构判据成对（`structural-before-*` / `structural-after-*`）

| 判据 | 改前 | 改后 |
|---|---|---|
| `len(machine_items)` | 0 | **6** |
| `grep -c '"label"'` | 0 | **6**（与上行同数，两口径互为验伪） |
| `grep -c '/Users/'` | 0 | **0**（验伪锚：同一判据喂已知正例命中 1） |
| `len(items)` / `version` | `55 2` | `55 2` |
| 零写 AST 门 | — | 10 个写调用，owner 集合 `{_apply_reinstall, _write_report}`，差集 ∅，输入面非空 → **PASS** |

### (g) 承重行为门 + 真机只读实跑

- `tests/unit/test_verify_install_manifest.py` + `tests/unit/test_vault_install_manifest.py`：
  `collected 244 items` / **244 passed** / rc=0（132 既有函数 + 2 追加 + 新文件；参数化后 244 例）。
- fixture 是 **hermetic** 的：tmp home + tmp harness，连 `com.canvas.daily-review.plist` 里那条指向
  真机 wrapper 的绝对路径也被改写进 tmp 树 —— 否则测试的真值会跟着这台机器的实际状态翻转
  （那是把环境当断言）。真文件、真 `plistlib`、真 sha256、真子进程，无 mock（DD-03）。
- **真机只读实跑**：`machine-verify-*.txt` / `machine-drift-*.txt`，
  `MATCH=2 / EXTERNAL-PRESENT=4 / PROGRAM-MATCH=5`，**rc=0**。
  sha 与 §〇 写卡时点逐字同（wrapper `d78d16be…f303`、plist `b673233c…924e`）。
  报告打出了每件程序体**实际指向哪棵树**（`…/feature-obsidian-hybrid-dev/…`）与**用了哪条取值规则**
  （`program_rule=interpreter+ProgramArguments[1]`）。
- `--reinstall --dry-run`（真机）：`PLAN 空` + `DRY-RUN 未写入任何字节`，rc=0。

### (h) pyright 不适用

本卡 `git diff --stat $PREV HEAD` 里 `backend/app/**` = 0 个文件，pyright 不触发；未用
`LEFTHOOK_EXCLUDE=python-typecheck`（lefthook 实测 `python-typecheck (skip) no files for inspection`）。

### (i) 既有套件不回退

- 点名套件 `test_vault_install_manifest.py` + `test_deploy_vault_sh.py` + `test_verify_install_manifest.py`：
  `collected 581` / **581 passed** / rc=0（最终 HEAD `8fe610bd`）。
- `tests/unit` 目录级（跑法与基线头第 3 行逐字同，不带 `--ignore`）：
  - 开工：32 failed / 5740 passed / 35 skipped / 13 xfailed
  - 收工：32 failed / **5845 passed** / 35 skipped / 13 xfailed（+105 = 本卡新增 103 + 追加 2）
  - `diff base.nodeids close.nodeids` → **只有 `<`**（少 `test_accept_candidate_already_accepted_returns_422`），
    即已登记的 W4 哨兵 nodeid 翻转（R-08/R-10）。协议只允许 `<` ⇒ 合规，**本卡零新增红**。
  - ⚠️ `rc=1` 是 `diff` 命令对「非空差异」的退出码，不是测试失败。

### (j) 不改端点

`grep -c openapi.json` 于 `$PREV..HEAD` 全量 diff = **0**；lefthook `spec-sync-flat` / `spec-sync-root` 实测均 skip。

### (k) 负控（6 段，每段只拆一层，`git show HEAD:<path>` 还原，跑前跑后 sha 四行逐字同）

| 段 | 拆掉的那一层 | 红在哪条**指定断言** | 结果 |
|---|---|---|---|
| ① | 「installed sha ≠ source sha ⇒ DRIFT」改恒 MATCH | `test_single_byte_flip_is_drift_on_exactly_that_label` `:524` `assert 'MATCH' == 'DRIFT'`（status 断言，非 rc） | 5 FAILED ✅ |
| ② | `--reinstall --dry-run` 改成真复制 | `test_dry_run_writes_nothing_and_prints_the_plan` `:648`「dry-run 动了 --home 树」（快照相等断言） | 2 FAILED ✅ |
| ③ | 在 `verify()` 体内植入 `Path("…").open("w")`（**绑定形态**，正是整改前漏报的那一族） | AST 门 `owners - allowed = ['verify']` → GATE **FAIL**；pytest 门 `:896`「写调用逃出允许名单」 | ✅ |
| ④ | `_apply_reinstall` 里 `source`/`dest` 对调 | 被**包含守卫**（更早的一层）拦下：「安装目录物理位置在 --home 之外」 | 5 FAILED ✅ |
| ⑤ | apply 期间顺手改仓内源权限位（**通过**包含守卫与 `status==MATCH`） | `test_apply_fixes_drift_and_is_idempotent` `:692`「apply 写到了 harness 树」 | **恰 1** FAILED ✅ |
| ⑥ | 真实 HOME 判定退回字符串比较 | `test_case_variant_home_still_requires_confirmation` | **恰 1** FAILED ✅ |

> **为什么有 ⑤**：④ 的变异被包含守卫杀掉了，于是「harness 整树零改动」这条断言在那一段里
> 一次都没被走到 —— 更强的门吃掉了弱门的测试面。⑤ 专门构造一个**能通过第一层**的变异，
> 才证明那条断言自己有牙。
>
> **作废登记**：`VOID-negctl-4-变异未套上-空跑不作证据.txt` —— 首次跑 ④ 时变异字符串在文件里
> 出现 2 次（`_apply_reinstall` 与 `render_report` 各一处），`assert count==1` 先失败、变异根本
> 没套上，而门照常打印 `66 passed`。**那个 66 passed 是空跑不是证据**，如实留档作废，重跑时
> 改用「先定位 `def _apply_reinstall` 再在其后取第一处」并加了「变异确实落在 `_apply_reinstall` 内
> + `render_report` 那处未动」的双向验伪锚。

### (l) 地盘门

`git --no-pager diff --stat --no-color $PREV HEAD -- . ':(exclude)_bmad-output'` = 恰 4 个文件：
`scripts/vault-install-manifest.json` / `scripts/verify_install_manifest.py`(NEW) /
`backend/tests/unit/test_verify_install_manifest.py`(NEW) / `backend/tests/unit/test_vault_install_manifest.py`(只追加)。
**名单外文件 = 0**。`test_vault_install_manifest.py` 删改行 = **0**；既有 132 个 test 函数名集合
AST 比对 `132 → 134`，`old ⊆ new`，`lost = ∅`。
`grep -rn -e fsrs_bridge -e decay_beta <本卡改动文件>` = **0**。未建任何 `scripts/launchd/*.plist`。

> ⚠️ **验伪锚在代码 commit 时点是空洞的**：`with_exclude_n == without_exclude_n == 4`，
> 「多出 `_bmad-output/` 路径」为空 —— 因为 evidence 目录当时还是**未跟踪**状态，`git diff`
> 根本看不见它，带不带 `exclude` 输出相同。该锚只有在 evidence commit 之后才有意义，见 §11 补跑。

### (m) 现网只读

- 未写 live vault，未连 7691/7687（本卡不连库），未碰 `fsrs_bridge.py` / `decay_beta.py`。
- **真实 `~/Library/**` 只读**：全程只 `stat` / 读 / `shasum`；`--apply` 只在 tmp HOME 跑；
  未执行任何 `launchctl` 子命令。
- **开工/收工快照**：见下方「§3 一处必须如实说明的事」。

### (n)/(o)/(p)

见 §9（Codex）、§终态字段（单 commit）、§7 / §8。

## 3 一处必须如实说明的事 —— 收工快照 `diff` 非空

卡文 (m) 要求「开工/收工 `machine-inventory` 两份 `diff` 为空，`ls -la` 的 mtime 列都不得变」。
**实测非空**：6 条 `ls -la` 行全不同，6 条 `sha256` 行全相同。

归因落档 `machine-snapshot-attribution-*.txt`，三条合起来才排除「有人改了文件」：

1. **位移完全一致** —— 独立位移值个数 = **1**（恰 `15:00:00`）。被改写的文件 mtime 会跳到「现在」，
   不会跟别人一起整体平移。
2. **位移量恰等于时区差** —— 开工存档自带时刻 `2026-09-18T22:41:45+08:00`；当前
   `/etc/localtime -> America/Los_Angeles`（PDT `-0700`）。`+08:00 → -07:00` = 15 小时，逐字相符。
3. **内容与权限位一位未变** —— 6 条 sha256 行 `diff` 为空；epoch mtime + size + mode 三元组落档。

⇒ 裁定：6 件在本卡作业期间**未被写入**。卡文那条判据字面不成立，是因为 `ls -la` 打的是**本地时间**，
而机器时区在作业期间随用户所在地变了（记忆 `user_timezone_follows_location` / D-18）。
本卡把承重判据换成**时区无关**的四元组（epoch mtime + size + mode + sha256）。
⚠️ **同批其它车道若也用 `ls -la` 文本 diff 做快照判据，今天会同样假红。**

**最终 HEAD 的收工快照**（`machine-inventory-close-20260919T0407*.txt`）：四元组与归因档里的值逐字相同
（`1787600636 / 1785514698 / 1785514767 / 1785514768 / 1785514769 / 1787780243`），
`diff open.shas close.shas` → **空（6/6 逐字同）**。全程只 `stat` / 读 / `shasum`，
未执行 `launchctl`，未对真实 HOME 跑过 `--apply`。

> ⚠️ 一处必须说明的副作用：负控③⑨往 `verify()` 里植入的是**可执行**的写调用，pytest 全量跑会
> 真的执行它们，在 `backend/` 下留下 `_negctl3_planted`（0 B）与 `x`（3 B）两个未跟踪文件。
> 已删除并复核：两者都落在 `backend/` 下，**没有碰 `~/Library`，也没有碰 live vault**；
> 删除后 `git status` 干净、真机 6 件 sha 不变。教训：植入可执行写调用的负控，要么只跑 AST 门，
> 要么跑完立刻查残留 —— 头两次我只跑了 AST 门和单条 nodeid，所以没暴露；改成全量跑之后才看见。

## 4 DoD-3 双段

### 4-A Claude 已代验（技术面，附证据路径）

| 项 | 结果 | 证据 |
|---|---|---|
| 结构判据成对 | 0→6 / label 6 / `/Users/` 0 / items 55 不变 | `structural-before-*.txt`、`structural-after-*.txt` |
| 零写 AST 门 | 10 个写调用全在 2 个允许函数内，差集 ∅ | `structural-after-*.txt` |
| 行为门 | `collected 244` / 244 passed / rc=0 | `behavior-*.txt` |
| 真机只读 | `MATCH=2 / EXTERNAL-PRESENT=4 / PROGRAM-MATCH=5`，rc=0，6 件 sha 未变 | `machine-verify-*.txt`、`machine-drift-*.txt` |
| 负控 6 段 | 每段红在指定断言，还原后 sha 逐字同 | `negctl-{1..6}-*.txt` |
| 地盘门 | 4 文件，名单外 0，删改行 0 | `ruff-territory-*.txt` |
| ruff | 3 文件 rc=0；F821 锚 rc=1；F401 反向锚 rc=0（证明 F401 未启用，用它当锚会是空洞判据） | `ruff-territory-*.txt` |
| 机器面快照 | 见 §3（时区归因，内容零变化） | `machine-snapshot-attribution-*.txt` |

### 4-B 给用户看的（零技术词）

> 电脑里那几份「定时任务」的安装副本，现在有一张清单说得清每一份从哪来、装在哪、有没有悄悄变样；
> 我看一眼报告就知道要不要重装，重装前它会先把打算做的事列给我看 —— 我感觉「改了仓库忘了装」
> 这种暗坑终于有人盯着了。

**felt-sense**：以前这 6 份东西是「装过一次就没人再看」的状态，出问题只能等复习推送不响了才发现
（已经这样丢过 6 天）。现在它变成一个随时可以问一句「都还对吗」的东西，而且它回答得很具体 ——
哪一份、从哪来、指到哪棵树去了。另外那 4 份仓库不保管的，它也照样说得出在不在、要跑的脚本有没有被改。

## 5 内部对抗复核（落盘，可作依据）

协议 §五.5：「没有入库 journal 的复核不作依据」。本卡这一轮**有**落盘 journal，故可引用。

- 形态：5 个独立视角（零写 / 退出码 / 写路径安全 / program_source 与 plist 解析 / 门是否名实相符）
  并行提出 → 每条 finding 再派一个**以反驳为目标**的验证 agent 去读真代码、在 `/private/tmp` 里跑复现。
- 结果：**38 条提出 / 26 条确认（3 HIGH + 16 MEDIUM + 7 LOW）/ 12 条被反驳**。
- journal：`…/subagents/workflows/wf_2b11aa49-66f/journal.jsonl`（43 条 `result` 记录，每条带完整返回值）。

### 三条 HIGH 与整改

| # | 确认的缺陷 | 为什么两把锁都没拦住 | 整改 | 对照输入 |
|---|---|---|---|---|
| H1 | 真实 HOME 的确认门是**路径字符串**比较；`/users/x`、`/USERS/X`、`/Users/heishing`、`/System/Volumes/Data/Users/x` 四种拼法是同一个目录（`samefile=True`）却四个不同字符串，**全部写穿**（沙箱实测 rc 0 + wrapper sha 翻转） | `Path.resolve()` 展开软链但**不折叠大小写**，macOS 启动卷默认大小写不敏感；firmlink 拼法正是 `df` / Time Machine 打印的那个 | 改按 **inode 身份**（`st_dev, st_ino`）判，stat 不到时退回字符串比较（宁可多要一次确认） | 负控⑥ |
| H2 | AST 零写门漏掉 `Path.open("w")` 整族：`_mode_is_write` 从 `args[1]` 取 mode，那是内建 `open(file, mode)` 的位置，绑定形态的 mode 在 `args[0]` | 植入 `Path(...).open('w')` 后 detections 仍是 10、`escaped=[]`，门保持绿；同时 `--reinstall --dry-run` 打印「未写入任何字节」却真的创建了文件。快照门只看 `--home` 子树，看不见写在树外 | mode 按绑定/非绑定分别取；`*args` / `**kwargs` 判不出 mode 时**保守判为写**；认 `import os as o` / `from os import replace` 改名；词表补 `os.pwrite/writev/ftruncate/fchmod/chflags`、`shutil.copyfileobj/unpack_archive`、`tempfile.*`、`.write` | 负控③ + 10 条参数化对照输入 |
| H3 | apply 的**复制方向**没有任何断言锁住：把 `source`/`dest` 对调后全文件 39 passed 照旧 | `MATCH` 是**对称**相等（`installed_sha == source_sha`），「两边一起坏掉」与「修好了」是同一个字符串；AST 门只看谁在写、快照门只看 `--home`，两把锁锚在同一侧 | 加「harness 整树跑前跑后逐项相同」+「安装副本等于**事先取下的**源字节」；另加物理包含守卫 | 负控④（被包含守卫拦下）+ 负控⑤（专门通过第一层） |

### MEDIUM / LOW 整改摘要（每条都配了对照输入）

- `install` 余段未要求相对：`~//Library/x` 的余段是绝对路径，`home / "/Library/x"` 在 pathlib 里
  **丢掉左操作数**，读写双双脱离 `--home`（端到端实测 rc 0 且文件落在树外）→ load 期拒绝 + `expand_install` 再做一次包含断言。
- 写入只查叶子软链，挡不住 `<home>/Library` 整个是软链 → 加**物理**包含判定。
  ⚠️ 禁止性判定（报告落点）方向相反，取「字面 ∪ 物理」并集；**两个谓词刻意不共用**。
- 报告落点门只 resolve 一侧，受管根自身是软链时两边对不上 → 双形态并集。
- 无写端 FIFO 让 `read_bytes()` 在内核里**永久阻塞**（实测 25 秒无输出无退出码）→ 读之前先问是不是普通文件。
- `ProgramArguments[1]` 写死：launchd 的规则是 `Program` 优先、否则 `ProgramArguments[0]` → 改按真实规则取，
  并把用了哪条规则打进报告（`program_rule=`）。
- 相对的程序路径被拿**进程 cwd** 补全：同样的磁盘内容换个目录就从 MATCH 翻成 DANGLING → 归 DANGLING 并写明理由。
- `_apply_reinstall` 里四个 `OSError` 可抛的调用在 `try` 之外 → 裸 `OSError` 穿过 `main` 让解释器退 **1**，
  而契约承诺 `EXIT_MISMATCH=2` → 收进 `try`。
- 重复 `install` 按**原始字符串**去重，下游按规范化路径 → 键不一致；改按规范化去重，并拒绝 `.` 段。
- NUL / 不可编码值让 `Path(value).parts` 抛裸 `ValueError` → 归 manifest 错档。
- `source_blob=` 只断标签不断值（`source_blob=-` 一样满足）→ 改断 40 位实际值。
- `"PLAN 空"` 被 `"POST-PLAN 空（…）"` 满足、`"EXTERNAL-MISSING=4"` 是 `"⚠️ EXTERNAL-MISSING=4"` 的子串
  → 两组断言各自塌成一条；改按**整行**比。
- `_statuses()` 解析不到任何 label 时返回 `{}`，让 `_statuses(a) == _statuses(b)` 退化成 `{} == {}` → 空即报错。
- 真实 HOME 那条确认测试**在这台机器上恒为空计划**（两件 repo 管理的都是 MATCH），
  「前后 sha 不变」不论守卫在不在都成立 = 空洞断言 → 新增一条把子进程 `HOME` 指到 tmp 树的非空洞版本，
  并在断言前先证「计划非空」。
- `--apply` 对 **MISSING** 件此前一条对照输入都没有（四条 apply 测试全是 DRIFT 件）→ 补两条。

## 6 本卡的口径取舍（自报，请复核者重点看）

**卡文 (e) 原话是「`--report` 落点不得在 `--home` 树内」。字面实现会让本卡自己那条
`--report <仓内 evidence 目录>` 恒判用法错** —— 本仓所有 evidence 落点都在 `/Users/Heishing/` 即 HOME 之下，
而卡文 §二.6 又要求跑那条命令并期望 rc 0/2。两条要求互斥。

实现取「不得落在 **manifest 声明的安装根**内」= 受管面（从清单推出来的 `<home>/Library`，加 `<harness>/scripts`），
理由是这条门要防的是「往被审计的目录里写东西污染审计本身」，而不是「不许写 home」。
受管根**从 manifest 推导**而非硬编码。证据：`test_report_inside_managed_home_root_is_rejected` /
`test_report_inside_harness_scripts_is_rejected` / `test_report_outside_managed_surface_is_written` /
`test_report_location_guard_resolves_symlinks` / `test_report_guard_holds_when_managed_root_is_a_symlink`。

**重装的权限位口径与手工 `cp` 一致**：目标已在则保留它原有的权限位，不在则取仓内源的。
仓内源是 `0644` 而已装 wrapper 是 `0755`，所以**首次**安装会得到 `0644` —— 这与目前「人工 `cp`」
的行为完全相同（`cp` 到不存在的目标取源的 mode），今天那个 `0755` 来自历史上的一次 `chmod`，
本工具不复现它。已登记进「本卡未证明什么」。

## 7 本卡未证明什么

1. **未证明真实 `~/Library` 的 `--apply` 在真机正确** —— 只在 tmp HOME 验；真机 apply 需用户当次
   显式授权（「DEBT-10 授权重装」），本次**未授权 ⇒ SKIP**，且真机 DRIFT = 0 本就无事可做。
2. **未证明 4 个 external plist 的内容与其程序体行为正确** —— 只登记「在位 + sha + 程序体按内容比」，
   不评 `KeepAlive` / 触发时刻 / `PATH` 这些语义。
3. **未证明 launchctl 加载状态与清单一致** —— 本脚本刻意不调 `launchctl`（连起外部程序的能力都没有）；
   重装之后的重载是人的动作，已登记移交。
4. **未证明跨机器 / 跨用户 HOME 的可移植性** —— `~/` 展开、大小写不敏感、firmlink 这些都只在本机验过；
   大小写变体那条测试在区分大小写的文件系统上会 `skip`（如实标注，不是通过）。
5. **未证明 in-place 程序体指向「另一棵树」时的口径完备** —— 已装 plist 指主干树而校验器跑在车道树，
   本卡按**内容**比 + 报告打出实际指向。若主干树与车道树版本不同会报 `PROGRAM-DRIFT`，
   那是真实状态不是假红，但**需要人读**才能分辨「哪一棵树才是对的」。
6. **未证明与 DEBT-15 hook 签名扫描的一致性** —— `collect_hook_signatures.py` 也解析 plist，
   两者无共享 helper，口径可能漂移（本卡对它只读）。
7. **未证明首次安装的权限位符合运行期需要** —— 见 §6：首装会得到源的 `0644` 而非现网的 `0755`。
   launchd 经 `/bin/bash <脚本>` 调用不需要可执行位，但这一条**没有在真机验过**。
8. **未证明 AST 零写门的词表已完备** —— 词表是手写的，天然不完备。本卡把它从「只认 3 类」扩到
   「48 个 dotted + 15 个方法 + 绑定形态 + 星号参数 + import/变量改名 + `os.open` 按 flags 判」，
   并配了十几条对照输入，但**不能声称没有下一种写法**。兜底有两条：调用图门（不认名字只认可达性）、
   以及「脚本不 import subprocess、起不了外部程序」这条能力判据。
9. **未证明 `_apply_reinstall` 的目录身份钉死在并发场景下真的更强** —— 负控⑩（把 fd 上溯退回路径比较）
   **存活**：一切静态场景两种写法都拦得住，差别只在「检查与写入之间有人换掉目录」这一个并发窗口，
   而我做不出确定性的并发对照输入。保留 fd 上溯的理由是机理（不再依赖任何一次事后的路径解析），
   不是实测更强。残余窗口（`open` 之前那一瞬）在脚本 docstring 里已如实声明；macOS 无
   `openat2(RESOLVE_BENEATH)`，要降到零得换平台原语。
10. **未证明 Codex 对最终 HEAD 的判断** —— r1 绑的是 `390f25cf`，之后又整改了两轮；r2 因外部配额
    未能产出。末轮**没有**绑最终 HEAD，按 D-15 不构成通过。替代证据是两轮落盘的内部对抗复核，
    但它们与 Codex 是不同的审查者，**不能代替**协议要求的那一轮。
11. **未证明报告在超长 / 异常 plist 上的全部表现** —— 已覆盖 NUL、非 UTF-8 软链目标、非法元素类型、
    超上限文件、FIFO、binary plist；但 plist 格式空间远不止这些，只能说「这几类有档位」。

## 8 台账待登记条目

1. **`machine_items` 6 件 + 校验器 + 真机只读报告**：报告路径 `evidence-debt-10/machine-drift-*.txt`，
   rc=0；6 件 sha256（wrapper `d78d16be…f303` / daily-review plist `b673233c…924e` /
   memory-health `c198f01d…` / neo4j-backup `40786196…` / qwen `1680bdde…` / reranker `58a10e97…`）。
2. **4 个无源 plist 逐件裁定**：用户 2026-09-18 裁定**全部登 external-managed**；
   仓库**未新建**任何 `scripts/launchd/*.plist`（`--diff-filter=A` 实测 0）。
3. **真机 `--apply`：未执行（未授权 SKIP）**。真机 DRIFT = 0，当前无事可做；
   将来授权重装时须先 `--reinstall --dry-run` 看计划，重装后**还要人工重载 launchctl**（本工具不做）。
4. **路径失实更正**：草案 §三 / 总账 `:904` / manifest touchpoint 写的 `~/CanvasReview/bin` **实测不存在**，
   真实安装根是 `~/Library/Application Support/CanvasReview/bin`。**文案待主 session 改**。
5. **Codex 各轮存档路径、绑定 SHA、B/H/M/L 计数** —— 见 §9。
6. **移交另立卡**：① launchctl 重载步骤；② 4 个 in-place 程序体是否也该像 wrapper 那样 `cp` 到一个
   固定位置（wrapper 源 `:3-5` 的「memory-health 停摆 6 天」教训至今只修了 wrapper 一件，
   而 memory-health 自己还指着一条会腐烂的 worktree 路径）。
7. **C2-11**（`verify_vault_install.py` 零写门重设计）同 manifest 面，下批同车道。
8. **⚠️ 批级提醒**：机器时区在本卡作业期间从 `+08:00` 变为 `America/Los_Angeles`（`-0700`）。
   任何用 `ls -la` 文本 diff 做「文件没被动过」判据的车道，**今天都会假红**；判据应换成
   epoch mtime + size + sha256 这类时区无关的三元组。见 §3。
9. **本卡代码 commit 经四次 amend 收敛为一个**：`13a80be8` → `390f25cf` → `e64fc5c5` → `2726815d` → **`8fe610bd`**。
   每次都是复核确认缺陷后的整改，而卡文 (o) 要求「代码单独一个 commit」。每一次整改后都按协议 :73
   在**新 HEAD 重跑全套承重裁判**（负控整套 + 结构 + 零写双门 + ruff + 地盘 + 行为门 + 真机只读）。
   中间四个 SHA 只存在于 reflog，未 push。
10. **⚠️ 批级事件：Codex 配额耗尽**。`codex exec` 报
    `You've hit your usage limit … try again at Sep 23rd, 2026 11:05 AM`，
    `codex login status` = `Logged in using ChatGPT`（**确认是配额不是鉴权**，两者同形但处置相反）。
    两次重发均 0 字节。**同批其它车道今天送不出 Codex**，排批需据此调整。

## 9 Codex 轮次

| 轮 | 绑定 SHA | 存档 | 结果 |
|---|---|---|---|
| r1 | `390f25cf`（`git diff 4cc6a78c 390f25cf -- . ':(exclude)_bmad-output'`） | `_bmad-output/审查/codex-review-CARD-DEBT-10.md`（7033 B） | **4 HIGH + 6 MEDIUM**，全部采纳整改，无一条驳回 |
| r2 | 拟绑 `e64fc5c5` | **未产出**（0 字节 ×2） | 配额耗尽，按协议 §1「再 0 字节 → 主 session 人审替代，不等配额」 |

**r1 存档首部自证**（协议 §2.1，`.stderr` 本身不入库）：

> 批次: BATCH-2026-09-18-第十五批 · 车道 P3 · 卡 CARD-DEBT-10 round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-DEBT-10.md)"`
> 审查绑定: `4cc6a78c..390f25cf`（⚠️ **不绑最终 HEAD** —— r1 之后又整改了两轮）
> 会话头自证（抄 `.stderr`，括注行号）：
> `(:2) OpenAI Codex v0.153.3` / `(:5) model: gpt-6-astra` / `(:9) reasoning effort: ultra`
> （⚠️ codex 0.153.3 把 `model:` 排在第 5 行，字面抄前三行会漏掉自证字段 —— 协议 §2.1 记过这个坑，实测确认。）

**0 字节文件未入库**：`find _bmad-output/审查 -name 'codex-review-CARD-DEBT-10*' -size 0` → 空。

### ⛔ 移交主 session：末轮未绑最终 HEAD

卡文 (n) / D-15 要求「多轮直到**绑最终 HEAD 的那一轮** BLOCKER/HIGH = 0」。本卡做不到，原因是外部配额，
不是审查结论。如实登记，**不自判通过**：

- 最后一次 Codex 审查绑的是 `390f25cf`，而最终 HEAD 是 `8fe610bd`；
  `git --no-pager diff --stat --no-color 390f25cf 8fe610bd -- . ':(exclude)_bmad-output'` **非空**（两轮整改）。
- 替代证据（落盘、可引用）：两轮**内部对抗复核**，形态为「N 个独立视角并行提出 → 每条 finding 派一个
  以反驳为目标的验证 agent 去读真代码并在 `/private/tmp` 跑复现」：
  - 轮 A（绑 `13a80be8`，Codex r1 之前）：38 提出 / **26 确认**（3 HIGH + 16 MEDIUM + 7 LOW）/ 12 被反驳。
    journal `…/workflows/wf_2b11aa49-66f/journal.jsonl`。
  - 轮 B（绑 `e64fc5c5`，Codex r2 的替代）：28 提出 / **21 确认**（2 HIGH + 11 MEDIUM + 8 LOW）/ 7 被反驳。
    journal `…/workflows/wf_3ba03b9d-18e/journal.jsonl`。
  - 两轮确认项**全部整改**，每条配了一个「改之前会绿、改之后才红」的对照输入。
- 轮 B 的头号 HIGH 是我自己整改时犯的：`main` 里那道「写目标是否落在真实 HOME 内」的**禁止性**判定
  用了**允许性**谓词 —— 我在 docstring 里写了「两个方向相反、不能共用」，却在第三个调用点用反。
  复核端到端复现出真实写穿（rc 0 + sha 翻转）。现已修正，并新增一条门 `test_helper_predicates_are_used_in_the_right_direction`
  逐个调用点查方向 —— **写下规则不等于遵守规则，得有门去查**。

## 10 evidence 清单

目录 `_bmad-output/审查/evidence-debt-10/`：

| 文件 | 内容 |
|---|---|
| `machine-inventory-open-*.txt` | 开工机器面只读快照（6 件 `ls -la` + `shasum`，末行 `~/CanvasReview/bin` 不存在的实证） |
| `machine-inventory-close-*.txt` | 收工快照：**时区无关三元组**（epoch mtime + size + mode + sha256）+ `ls -la` 原样留档 |
| `machine-snapshot-attribution-*.txt` | 收工 `ls -la` diff 非空的决定性归因（位移唯一值 = 1 恰 15:00:00 / 时区差吻合 / sha diff 空） |
| `structural-before-*.txt` | 先红四项（help 0 命中 / `machine_items` False / `Library` 0 / 脚本不存在 rc=1） |
| `final-judges-*.txt` | 最终 HEAD 的结构判据 + 零写**双门** + ruff（含 F821 锚与 F401 反向锚）+ 地盘门 |
| `behavior-*.txt` / `named-close-*.txt` | 行为门与点名套件 |
| `unit-open-*.txt` / `unit-close-*.txt` / `base.nodeids` / `open.nodeids` / `close.nodeids` | 目录级开工/收工与 nodeid 口径 diff |
| `machine-verify-*.txt` / `machine-drift-*.txt` / `machine-dryrun-*.txt` | 真机只读实跑、报告正文、dry-run |
| `negctl-{1..10}-*.txt` | 最终 HEAD 的十段负控 |
| `negctl-superseded/` | 中间 HEAD 上跑过、已被最终 HEAD 重跑取代的负控（**留档不删**，含一份作废声明） |
| `VOID-negctl-4-变异未套上-空跑不作证据.txt` | 变异字符串在文件里出现 2 次、`assert count==1` 先失败 ⇒ 变异没套上而门照打 `66 passed`。**那个 66 passed 是空跑不是证据**，如实作废 |

## 11 最终数字（收工重算）

| 项 | 值 |
|---|---|
| 最终代码 SHA | **`8fe610bd`** |
| 代码 commit 数 | **1**（四次 amend 收敛） |
| 改动面 | 4 个文件 / **3221 行纯新增 / 0 删除** |
| 零写：调用点门 | 10 个写调用，owner 集合 = `{def:_apply_reinstall, def:_write_report}`，差集 ∅ → **PASS** |
| 零写：调用图门 | `verify` / `_verify_one` / `_verify_program` / `plan_reinstall` 四个入口可达写者 = ∅ → **PASS** |
| 行为门 | `collected 281` / **281 passed** / rc 0 |
| 点名套件 | `collected 581` / **581 passed** / rc 0 |
| `tests/unit` 目录级 | 开工 5740 passed → 收工 **5845 passed**（+105）；红 32 ↔ 32，`diff` **只有 `<`** ⇒ 零新增红 |
| 真机只读 | `MATCH=2 / EXTERNAL-PRESENT=4 / PROGRAM-MATCH=5`，rc **0**；`--reinstall --dry-run` → `PLAN 空` + `DRY-RUN 未写入任何字节`，rc 0 |
| 真机 6 件 | epoch mtime + size + mode + sha256 四元组与开工逐字同；`sha diff` 空 |
| 负控 | 10 段，**9 段击杀**（各红在指定断言），1 段存活（已验伪归类，见下） |
| ruff | 3 文件 rc 0；F821 锚 rc 1；F401 反向锚 rc 0 |
| 地盘门 | 4 文件，名单外 **0**，`test_vault_install_manifest.py` 删改行 **0**，既有 132 个 test 函数名 `old ⊆ new`、`lost = ∅` |
| 复核 | 内部对抗 ×2（26 + 21 确认，全部整改）+ Codex r1（4H+6M，全部整改）；r2 配额阻断 |

### 负控⑩ 存活的归类（SURVIVED 必须验伪，不能当没看见）

把 `_apply_reinstall` 的目录身份判定从「沿 fd 用 `os.open("..", dir_fd=)` 上溯」退回
「`_under(_resolve_lenient(parent), _resolve_lenient(home))`」之后，**103 passed 全绿**。

三种可能里排除了两种：变异确实套上了（diff 入档）、判定方向没写反（其余九段都按预期红）。
剩下的是第三种：**fd 上溯相对路径比较的优势，只在「检查与写入之间有人把目录换掉」这一个并发场景里
才显形**；一切静态场景（`<home>/Library` 本来就是软链、指向树外、大小写别名）两种写法都拦得住，
所以现有对照输入区分不开它们。我做不出一个确定性的并发对照输入，如实登记进「本卡未证明什么」。

保留 fd 上溯的理由不是「测出来更强」，而是**它不再依赖任何一次事后的路径解析** —— 拿 `fstat(fd)`
去比 `stat(同一个路径)` 是两次都发生在检查之后的观测，中间被换掉两边会一起变，那种比法看着严谨
其实什么也没钉住。

### 负控⑥ 一度存活，已补上隔离点

第一次跑时负控⑥（把真实 HOME 判定退回字符串比较）**103 passed 存活** —— 因为第二道门
（写目标是否落在真实 HOME 内）替第一道门挡住了同一个输入，**更强的门吃掉了弱门的测试面**。
补法是让 `test_case_variant_home_still_requires_confirmation` 断言 **第一道门自己的那句话**
（`--apply 指向真实 HOME`），并断言第二道门的话**没有**出现。重跑后该段恰 1 条红，正是该用例。
