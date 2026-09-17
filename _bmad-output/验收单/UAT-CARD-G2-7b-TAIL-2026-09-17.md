# UAT — CARD-G2-7b-TAIL（deploy-vault.sh G2-7b 尾巴 5 项）

> 批次 `[BATCH-2026-09-11-第十四批 / CARD-G2-7b-TAIL]` · 车道 `card-t2-deploy`（T2-E，本车道 5/5）
> 开工 HEAD（T2-D 末 commit）`37b89ce07ade0d470e33847df46aca419d27e5af`
> 代码终审绑定 `70b9203a` · 未 push · 日期 2026-09-17

## 〇 第 0 分钟与前提

| 项 | 实测 |
|---|---|
| pwd / 分支 | `…/worktrees/card-t2-deploy` · `card/t2-deploy` |
| HEAD 含 CARD-HOSTS-CODEX | `37b89ce0 docs(deploy): r9/r10 结算 …[… / CARD-HOSTS-CODEX]` ✅ |
| `git status --porcelain` | 空 ✅ |
| `test -x backend/.venv/bin/pytest` | rc=0 ✅（venv 是指向 `card-v5-lance/backend/.venv` 的目录级 symlink） |
| 基线自证（R-B14-2 唯一口径） | `grep -vc '^#' $BASE` = **64**；交叉核 `grep -cE '^(ERROR\|FAILED)'` = **64** ✅ |
| 被禁口径（如实记录，未采用） | `grep -c '::' $BASE` = 65（第 3 行注释里逐字引了一条 flaky nodeid） |
| `$BASE` sha256 | `296b301b656fad768c7bf892d3e8122a220ca158272e8077ccdbf1e6d2710045` |

## 〇bis 卡文锚点漂移（⛔ 全表失效，逐条重映射）

卡文 §〇 的 file:line 是在**主干树**（代码 = B14_BASE）上测的，并声称「本卡三个地盘文件在
B14_BASE→HEAD 逐字节相同」。该结论对**本车道树不成立**：T2-A~T2-D 四张前卡已大改这三个文件
（`git diff --stat 08100483 HEAD -- <三文件>` = 5135 insertions / 58 deletions）。

| 卡文 | 实测（开工 HEAD `37b89ce0`） |
|---|---|
| deploy-vault.sh 1238 行 | **3224** 行 |
| test_deploy_vault_sh.py 2596 行 | **5676** 行 |
| cls_forbidden_paths.py 609 行 | **620** 行 |
| `src="$SRC_MIRROR"` :1036 | **:2722** |
| `step4_verify()` :969 | **:2655** |
| `run_step()` :373-385 / `exit $((70+n))` :382 | **:562-574** / **:571** |
| 六行状态循环 :1179 | **:3139** |
| `assert_writable_now()` :201-230 | **:265-295** |
| A3 `tr -d` :736 | **:2503** |
| env tmp :584/:586/:606/:625 | **:878/:880/:900/:919** |
| install 日志 :667 | **:961** |
| key tmp :927 | **:2603** |
| compose-config :1075 | **:2761** |
| deploy 报告 tmp :1200/:1207/:1216 | **:3166/:3173/:3193/:3202**（实为 4 处，卡文少列一处） |
| `ancestor_symlink_hits` def :426 / return :539 | **:437** / **:550** |
| 既有 content-drift 门 test:2177 | **test:2294** |
| M-2 三条 count 门 :1194/:1225/:1228/:1234 | **:1258**（PENDING_WRITES）/ **:1302**（open_pinned==5）/ **:1316**（write_all==9）/ **:1329**（ftruncate==6）——数值也全变了 |

## 一 逐条完成条件

### (a) 第 0 分钟 + 前提 + 基线 64 ✅ 见 §〇

### (b) 目标漂移负控 —— 先红后绿 ✅（缺陷**未**移交 T7）

实测（存档 `evidence-g27b-tail/before-after-20260917T093413.txt`）：

- **改前**（`git show 37b89ce0:scripts/deploy-vault.sh` + 整行突变 `src="$SRC_MIRROR"` → `src="$VAULT"`）：
  整跑 **rc=0**，报告 `content-drift : 0`、`match : 26`，步 4 消息仍写「基准=源镜像」。
  既有门 `test_step4_actually_evaluates_content_drift_when_port_differs` 的三条断言**一条都没红** ⇒ 突变完全存活。
- **改后**：同一突变 **rc=74**，步 4 FAIL 并点名「校验器把**目标 vault 自己**当成了基准」。

⚠️ 卡文 (b) 预留了「若突变存活且修复需改 T7/backend/app 则移交」。**实测不需要移交**：
突变留下的可观测差异在校验器**报告头的 `# source` 行**上，而那是「deploy-vault.sh 传了什么」的回执，
不是 T7 的 drift 语义。修复因此整条落在 `deploy-vault.sh:2864-2905`，`verify_vault_install.py` 一个字节未改。

承重证明：`test_step4_drift_negctl_would_pass_without_the_receipt_check` —— 把期望值退回成 `_want_src="$src"`
（拿被改的变量核对它自己）后整跑重新 rc=0，说明拦住漂移的确实是「独立算一遍期望值」那一步。

### (c) 五处写点 mktemp/O_EXCL/rename + 预置链负控 ✅

五面：env tmp / install 日志 / key tmp / compose-config / deploy 报告 tmp。
第六处（verify 报告 `$rep`）由 T7 的 `verify_vault_install.py --report` 写 ——
**本卡不扩面、未改、未证其原子性**（如实声明，见 §三）。

- 源码门 `test_five_bash_write_sites_no_longer_redirect_into_predictable_paths`：
  去注释代码里 `: > "$ENV_FILE.tmp"` / `> "$keyfile.tmp"` / `> "$out.tmp"` / `: > "$ilog"` / `> "$cfg"`
  各 **0** 次命中；五处 `mk_tmp_beside` + 五处 `mv` 各在位。
- 运行时负控（`.env.<vault>.tmp` 上预置软链 / 硬链接两种）：
  **改前 rc=71**（部署被一个外人放的文件卡死 = 拒绝服务），**改后 rc=0** 且受害文件逐字节原样。
- 负控的承重点：`test_preplaced_link_negctl_old_fixed_name_write_is_blocked` —— 把固定名登记塞回
  `PENDING_WRITES` 后 rc 重新变成 71。

### (d) rc 表主张补全 ✅

- **(d-i)** 从部署入口真跑出：`rc=75`（PATH 前置恒失败的假 `docker`，步 5 FAIL「未起任何容器」）；
  `rc=76`（假 `shasum`，步 6 FAIL 且报告含 `SHASUM-FAILED`）。顶层不退化：`--env-dir` 落在只读父目录下
  ⇒ **rc=72** + `[2/6] install: FAIL`（⚠️ 卡文说这条落在步 3，实测 `seed_env_file` 由 `step2_install` 调用，
  故是 72 不是 73 —— 已按实测写死期望值）。
  反向负控：`exit $((70 + n))` → `exit 1` 后同一注入得到 **rc=1** ⇒ 75/76 两条门承重在 7N 映射上。
- **(d-ii)** 「## 六行状态」**改前 5 行、改后 6 行**（同上存档 ③ 段）。第 6 行由 `step6_evidence`
  在落盘前合成，且与 `run_step` 事后 emit 的那一行**逐字相同**（门直接比较两者）。
  失败态也覆盖：假 `shasum` ⇒ 第 6 行写 `FAIL`、报告末尾 `rc=76`，与进程返回码不矛盾。

### (e) ancestor_symlink_hits ✅（如实登记「造不出独立样本」，但把纵深做成了可测）

- 穷举实测：7 类软链 × 12 种尾巴 + 一层反向嵌套 = **96 种组合**，
  「只有祖先轴命中」= **0** 个；「只有 walker 命中」= 1 个。
  结构解释：`walk_visited` 每跟一条软链就把**目标**记进 visited，而 `ancestor_symlink_hits`
  用 `k(祖先)` 得到的落点必然是其中之一 ⇒ 被覆盖。与函数 docstring 里 r6 探针的结论一致。
- 按卡文兜底口径**不强造假门**。改为两跑对照把「保留作纵深」做成可测：
  中和 `chain_hits` ⇒ 样本仍全被拦（祖先轴顶上）；两条轴一起中和 ⇒ 全漏。
- ⛔ **本卡自己造过一次假绿并抓了回来**：第一版样本用 `L_direct/x` 这类尾巴，
  整条路径的物理键落在保护目标**之内** ⇒ 规则 3 当场命中，两条软链轴根本没被调用到。
  是「两条轴都中和仍全 HIT」这条验伪锚把它打红的。样本已改为带 `..` 逃出目标之外的形态，
  并把该验伪锚**留作常驻断言**。
- 结论修订：r6 那句「本函数在现有用例下零承重」在**带 `..` 的样本族**上不成立 ——
  它在 walker 失效的配置下确实是最后一道。生产侧未改（`cls_forbidden_paths.py` 本卡零改动）。

### (f) M-1 / M-2 / M-3 / M-5 ✅

- **M-1**：改前两个 fail-open 均实测复现 —— `nlink="0"` ⇒ `[ 0 -gt 1 ]` 为假**放行**；
  23 位数字串 ⇒ `[: integer expression expected`、rc=2、`if` 判假**放行**。
  改后三条负控 + 一条控制组（合法 `1` 必须放行）全绿；另补「探针非零退出也算问不出来」一条。
  字符集从 `[!0-9]` 改逐字符枚举 `[!0123456789]`（locale 无关），顺序门钉死
  「字符集 → 位数上限 → 数值比较」。
- **M-2**：`count("os.ftruncate(fd, 0)")` → **顺序门**（截断之前必须出现过链接数检查）；
  `count("local -a PENDING_WRITES=(")` → **引号门**（每项必须整体带引号）。
  两条各配负控，且负控**先证纯 count 门对该变异毫无反应**，再证收窄后的门变红。
  身份（哪些 label、对应哪个路径表达式）仍由既有精确集合门管 —— 这里**不再抄第二份清单**。
- **M-3**：改前 `/Users/O'Brien/vaults` 被 `tr -d` 剥成 `OBrien` ⇒ A3 误判「已有 .env 与参数矛盾」
  并 rc 73 拒绝（消息里写的原因是错的）。改后同一输入 rc=0；负控把那一行换回 `tr -d` 形态
  ⇒ 重新 rc=73 且消息含 `OBrien`。另配两条控制组：真矛盾仍拒；配对双引号仍剥。
- **M-5**：`evidence-g27b-tail/mutation-ledger-20260917T093141.txt` —— 9 条负控各绑
  nodeid + 变异描述 + 断言消息片段 + 期望值，逐条单跑落 rc，并附三个地盘文件的
  跑前/跑后 `sha256`（**逐字节相同**，变异一律走副本，全程未用 `git stash` / `git checkout`）。

### (g) 收尾裁判

| 裁判 | 存档 | 结果 |
|---|---|---|
| `bash -n scripts/deploy-vault.sh` | 见下文命令 | **rc=0** |
| `test_deploy_vault_sh.py` 文件级单跑 | `evidence-g27b-tail/deploytest-close-20260917T091845.txt` | **274 passed / 9 skipped**，末行 `rc=0` |
| rc 75/76 入口负控 | 同上（nodeid 见 mutation-ledger） | 从部署入口真跑出 75 / 76 |
| tests/unit 目录级（带 `--ignore`） | `evidence-g27b-tail/unit-close-20260917T092218.txt` | 末行 `rc=1`（既有红），nodeid 集与基线 **diff 为空**，`>` 行 = **0** |
| ruff check / format + 验伪锚 | `evidence-g27b-tail/ruff-close-20260917T092749.txt` | `check_rc=0` / `format_rc=0` / `falsify_rc=1` |
| 地盘门 | 见 §四 | ⊆ {deploy-vault.sh, test_deploy_vault_sh.py}（第三个允许文件本卡未改） |

⚠️ **9 skipped 与本卡无关**：都是既有的「树上无 gitignored main.js ⇒ apply 会触发 npm build」那条 skipif。
本卡新增的真跑 `--apply` 用例**一条都没挂那条 skipif** —— 它们由 `harness_main_js` 夹具
补一个由 `hotkeys.json` 派生的 main.js 桩再无条件还原。这是刻意的：挂上 skipif 的话，
本车道树上这组负控会**整组静默跳过**，「全绿」就绿在「一条都没跑」上。

### (h) 两清单 见 §三 / §五（各 ≥4）

## 二 DoD-3

### 4-A Claude 已代验（技术）

```zsh
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy
EV=$(pwd)/_bmad-output/审查/evidence-g27b-tail
BASE=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/evidence-b14/unit-red-baseline-08100483.txt

bash -n scripts/deploy-vault.sh; echo rc=$?                       # 0
cd backend && ./.venv/bin/pytest -q -p no:cacheprovider tests/unit/test_deploy_vault_sh.py   # 274 passed / 9 skipped
./.venv/bin/pytest tests/unit --ignore tests/unit/test_deploy_vault_sh.py -q -p no:cacheprovider
diff "$EV/base.nodeids" "$EV/close.nodeids"                       # 空（只许 '<'，实测一条都没有）
cd .. && git --no-pager diff --stat --no-color 37b89ce0 HEAD -- . ':(exclude)_bmad-output'
```

逐条存档路径与末行 rc 见 §一(g) 表；负控逐条 nodeid 见 `mutation-ledger-20260917T093141.txt`
（验收单只引用路径与末行，不自述数字）。

### 4-B 用户视角（零技术词）

我一键部署一门课的时候，就算有人事先在它要用的地方动了手脚——想让它把**别处的文件**
当成我的课来比对、或者写到**不该写的地方**——它都会当场停下并如实告诉我是哪一步、为什么。
更重要的是，反过来也成立：别人随手放一个同名文件，**卡不住**我的部署了，它照样跑完。
部署成功以后那份记录里，六个步骤**一个不少**（以前最后一步总是不在），
最后一行写的结果和它实际的成败也对得上。

**felt-sense**：以前看那份记录，总觉得「最后一步去哪了」，心里有个说不清的空当；
现在六行齐齐整整，我不用再去回想它到底做没做完 —— 这套部署第一次让我觉得
「安全一键」这四个字是它自己挣来的，不是我替它说的。

## 三 本卡未证明什么

1. **未证明目标漂移突变在所有端口 / 源布局下都被抓**：只造了 `--port 8189`（非缺省，会建源镜像）
   一例。缺省 8011 那一支不建镜像，期望值退回 `$HARNESS/canvas-vault`，该支**未跑运行时负控**
   （只有源码路径覆盖）。
2. **未证明 mktemp/O_EXCL/rename 之后残留 TOCTOU 窗口为零**：临时件建出来之后的 `>>` 仍是
   **按路径**重定向，bash 做不到 `openat` 原子写。本卡只把「名字可预先算出」这一类关掉，
   并把负控覆盖到能造出的预置链；彻底消除需要把这五处全搬进 python，不在本卡范围。
3. **verify 报告 `$rep` 的第六处写点落在 T7 `verify_vault_install.py --report`**，本卡未改、
   未证其原子性，也未证它不会被预置链影响。
4. **步 4 回执核对依赖 T7 报告头里的 `# source` 行**。T7 若改报告格式，本步会 fail-closed
   （方向是安全的，但会把正常部署拦下）。这条跨文件耦合本卡只做了 fail-closed，**未与 T7 约定契约**。
5. **`ancestor_symlink_hits` 的独立样本只证明了「在可枚举的 96 种拓扑族里没有」**，不是「不存在」。
   覆盖面 = 4~7 类软链 × 6~12 种尾巴，未覆盖跨文件系统、大小写不敏感归一、`readlink` 失败等轴。
6. **顺序门的分辨力上限已如实写进判据 docstring**：它只判「该块内截断之前是否**出现过** st_nlink」，
   分不清那个守卫护的是不是**这一个 fd**。同块内若另有无关的 st_nlink 早于截断，把真守卫挪走它不会红。
7. **M-1 的位数上限取 10 位**（覆盖 uint32 的 4294967295），未枚举所有非常规 nlink 取值；
   `0` 这一态的判据依赖「`[ -e ]` 刚判过存在」这个前提，该前提由紧邻的两行代码保证，未加门钉住。
8. **未跑真 `docker compose up -d`**（T2-B 面，需用户当次授权）。rc 75 入口负控走的是
   「`docker compose config` 失败」这条路径，**不是**真 activate 失败或健康断言失败。
9. **未证明 `harness_main_js` 夹具对并行跑的用例无副作用**：它在仓内写一个 gitignored 的
   `main.js` 桩。本卡只在**串行**单文件跑法下验过（写入前先判存在、跑完无条件还原、
   收工 `git status --porcelain` 干净）；`pytest -n` 并行下未验。
10. **既有 9 条 skipif 用例本卡未解除**（它们仍因树上无 main.js 而跳过），
    即 `--apply` 真跑路径在**那 9 条**上仍无覆盖。

## 四 地盘核与终审绑定

```
git --no-pager diff --stat --no-color 37b89ce0 70b9203a -- . ':(exclude)_bmad-output'
 backend/tests/unit/test_deploy_vault_sh.py | 931 +++++++++++++++++++++++++++-
 scripts/deploy-vault.sh                    | 376 +++++++++---
 2 files changed, 1213 insertions(+), 94 deletions(-)
```

⊆ 允许的三文件 {`scripts/deploy-vault.sh`, `backend/tests/unit/test_deploy_vault_sh.py`,
`scripts/cls_forbidden_paths.py`} —— 第三个本卡**零改动**（(e) 的变异全部走副本）。

⛔ **验伪锚在 `70b9203a` 那一刻是空洞的**：去掉 `':(exclude)_bmad-output'` 后输出与带它时**完全相同**，
因为 evidence 目录当时还是 untracked，而 `git diff` 不显示未跟踪文件（已知坑）。
验伪锚在存档 commit 之后重跑并落档，见 §六。

## 五 台账待登记条目（主 session 写台账，本卡不改）

1. **T2-E 完成，代码终审绑定 `70b9203a`**；本车道 A→E 五张卡全部完成，**均未 push**。
2. **卡文 T2-E §〇 的 file:line 全表对本车道树失效**（它在主干树上测、按 B14_BASE 的代码），
   逐条重映射见本验收单 §〇bis。后续复用该卡文前必须重验。
3. **移交 T7（CARD-T7-*，`verify_vault_install.py` 地盘）**：步 4 现在依赖报告头 `# source` 行
   作为回执。建议把该行写进 T7 的报告契约（或给出一个稳定的机器可读回执），
   否则 T7 改格式会让步 4 fail-closed 拦下正常部署。
4. **移交 / 登记**：verify 报告 `$rep` 是 deploy 链上**最后一个**非原子写点（T7 python 侧），
   本卡未处置；若要收口需 T7 侧把 `--report` 改成 mktemp+rename。
5. **登记（不阻断）**：既有 9 条 `--apply` 用例仍挂 `main.js` skipif。本卡已给出可复用解法
   （`harness_main_js` 夹具，由 hotkeys.json 派生桩），是否推广到那 9 条由主 session 裁。
6. **登记（不阻断）**：`test_outputs_mode_allows_the_scripts_own_env_files` 的参数
   `.env.probe_x.tmp` 已不再对应任何脚本会产出的文件（该固定名随本卡退场）。
   它仍是判据的合法输入形状，本卡**未动**，如实记此名实偏差。
7. **登记（不阻断）**：`_npm_cap_harness`（test:2789 附近）里的 `verify_vault_install.py` 仍是空桩。
   那组用例停在步 1/2、到不了步 4，故本卡只改了 tx-harness 的桩；两处桩口径不一致，登记。
8. **工具链实测两条**（可进工程坑索引）：
   ① `_decomment` 按第一个 `#` 截断整行 ⇒ 会把 bash 的 `${#var}`（取长度）整条吃掉，
      在含参数展开的代码上做判据必须换只剥整行注释的剥法；
   ② ruff 验伪锚必须放在**仓内**：放到仓外（scratchpad）时走的是另一套配置，
      F821 未启用 ⇒ 锚恒 rc=0 = 空洞锚（本卡第一次就这么跑的）。
9. **登记**：地盘门验伪锚在存档 commit 之前恒空洞（`git diff` 看不见 untracked），
   必须 post-commit 跑 —— 本卡照此补跑，见 §六。
