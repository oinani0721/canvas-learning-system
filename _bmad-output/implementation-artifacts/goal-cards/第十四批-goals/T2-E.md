> ⚠️ 本文件是 CARD-G2-7b-TAIL 的完整卡文——车道开工后必读并逐条执行；它不是 /goal 粘贴文本。/goal 在第十四批手册 §三 T2-E 块。
> 批次标记 `[BATCH-2026-09-11-第十四批 / CARD-G2-7b-TAIL]`。车道：`card-t2-deploy`（分支 `card/t2-deploy`，NEW @ B14_BASE `081004834e37b1b0253cf81dc7b44e784646c934`，venv 目录级 symlink → `card-v5-lance/backend/.venv` 已建、`backend/.env` 已拷），本车道第 **5/5** 张（A CARD-DEPLOY-TIMEOUT → B CARD-G2-8 → C CARD-HOSTS-OPENCODE → D CARD-HOSTS-CODEX → **E 本卡**）。**前提**：T2-D CARD-HOSTS-CODEX 已独立 commit 且 `git status --porcelain` 空。用户已裁：D-15 有代码改动的卡 Codex 多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0（本卡有代码改动 ⇒ 多轮、上限 5）；T2-E 工时 3h、T2 超时整车道可退第十五批（退则本卡整条不合，不拆分）。勘探 2026-09-12 于主干树（代码 = B14_BASE）：recon A §B.5「G2-7b 转下一卡（5 项）」+ UAT-CARD-G2-7b-2026-09-09.md §十一 第 14/15/17/18/19 条与「22-29 条整改后的残留」H-1；recon C §6 / §13（deploy-vault.sh 锚点）；设计稿 §4 T2-E。协议（⛔ 必须读 **feature 主干树 `--add-dir` 那份**，车道树自己的 `.claude/rules/card-batch-protocol.md` 是 B14_BASE `08100483` 版、不含本批回写，别读那份）：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/.claude/rules/card-batch-protocol.md`（§1 合并门 + D-15 轮次 / §2.1 存档首部 / §2.2 裁判落盘 + --no-color + ruff zsh 数组 + pyright 绝对路径 / §2.3 过渡 / §3 最低覆盖）。手册同理只读主干树那份：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/2026-09-11-第十四批开跑手册-10车道43卡.md`（§零 / §一 / §四）。

# CARD-G2-7b-TAIL — deploy-vault.sh 尾巴 5 项：目标漂移负控 + 六写点 mktemp/O_EXCL/rename + rc 表主张补全（rc75/76 入口负控 + 六行状态落盘前五行）+ ancestor_symlink_hits 独立门 + M-1/M-2/M-3/M-5

## 〇 事实

| 事实 | 位置 / 实测命令 |
|---|---|
| **树口径更正**：勘探 recon C 在主干 `286178d8`、设计稿 B14_BASE = `08100483`；写卡时实测主干树 HEAD = **`e58d5c5c`**、本次修卡（2026-09-14）复测已前进到 **`b00b3766`**（两个都只是 B14_BASE 之上的纯文档 commit）。**本卡三个地盘文件在 B14_BASE→HEAD 逐字节相同**（`git diff --stat 08100483 HEAD -- scripts/deploy-vault.sh backend/tests/unit/test_deploy_vault_sh.py scripts/cls_forbidden_paths.py` = **空**），故下列 file:line 直接在 HEAD 测得即 = B14_BASE。车道 NEW @ B14_BASE，开工 HEAD = T2-D 末 commit | `git merge-base --is-ancestor 08100483 HEAD`（YES）；`git diff --stat 08100483 HEAD -- <三文件>`（空） |
| **规模**：`scripts/deploy-vault.sh` **1238** 行 / `backend/tests/unit/test_deploy_vault_sh.py` **2596** 行 / `scripts/cls_forbidden_paths.py` **609** 行；`bash -n scripts/deploy-vault.sh` rc=0 | `wc -l`；`bash -n` |
| **① 目标漂移负控（UAT §十一.15）**：`src="$SRC_MIRROR"` 在全文唯一 `deploy-vault.sh:1036`，位于 `step4_verify()` **:969-1057** 内（:969 是函数首行、**:1057 是闭合花括号**、:1058 为空行——⛔ 别写 :969-1058，逐条核锚时会对到空行上；`:1037 basis=...`）。**content-drift 轴由 `verify_vault_install.py` 计算（T7-D 地盘，本卡只读，禁改）**：`verify_vault_install.py:973` docstring「source_dir 给了才评 content-drift」、:778/:794 drift 细节。既有门 `test_step4_actually_evaluates_content_drift_when_port_differs`（test:**2177**，用 `--port 8189` 非缺省）只断言报告里 `content-drift:0` + `match>0`，**未对 `src="$SRC_MIRROR"→src="$VAULT"` 这条突变做负控**；Codex r3 静态推导「改成 `src="$VAULT"` 保留文案仍 `content-drift=0`」未被运行时证伪或证实 | `grep -nF 'src="$SRC_MIRROR"' scripts/deploy-vault.sh`（:1036，唯一）；`grep -nF 'step4_verify()' scripts/deploy-vault.sh`（:969）；`sed -n '2177,2205p' backend/tests/unit/test_deploy_vault_sh.py` |
| **② 六写点 mktemp/O_EXCL/rename（UAT §十一.19 + H-1 残留）**：deploy-vault.sh 内 bash `>`/`: >` 写点 = env tmp `:584`（`: > "$ENV_FILE.tmp"`）/`:586/:606/:625`（`>> "$ENV_FILE.tmp"`）、install 日志 `:667`（`: > "$ilog"`）、key tmp `:927`（`> "$keyfile.tmp"`）、compose-config `:1075`（`| redact_secrets > "$cfg"`）、deploy 报告 tmp `:1200`（`} > "$out.tmp"`）/`:1207/:1216`（`>> "$out.tmp"`）；**verify 报告 `$rep` 由 T7 的 `verify_vault_install.py` 写（:1040 `local rep=` / :1041 写前复查 / :1042-1045 python 调用，`--report "$rep"` 落在 :1045），不是 bash redirect**。当前注释 **:199-200** 已承认「bash 重定向做不到 open(O_NOFOLLOW) 原子性，残留窗口不为零」；两处 python 写已走 `open_pinned`（O_NOFOLLOW+nlink）:820-828（data.json）/:873-879（.env） | `grep -nE '(: )?>>? *"\$[A-Za-z_]+(\.tmp)?"' scripts/deploy-vault.sh`（实测 **14** 命中 = 五面写点 **10** 行 :584/:586/:606/:625 env tmp、:667 install 日志、:927 key tmp、:1075 compose-config、:1200/:1207/:1216 报告 tmp，**+ 4 行同目标的日志追加** :673 ilog、:1123/:1127/:1146 cfg——后 4 行是 install/compose 的输出重定向、不新建终路径，本卡不改）；`grep -nF 'assert_writable_now' scripts/deploy-vault.sh`（全 9 命中 :201 def / :455 符号链接待写守卫 / :581 / :666 / :926 / :1020 镜像待写目标守卫 / :1041 / :1072 / :1169；其中六写点守卫 = :581/:666/:926/:1041/:1072/:1169） |
| **③ rc 表主张（UAT §十一.17/.18）**：rc 表头注 **:14-19**（`71` 步1…`76` 步6）；`run_step()` **:373-385** 把 FAIL 映射成 `exit $((70 + n))`（:382）；step5 :1060 / step6 :1159；六行状态循环 **:1179** `for t in "${STEP_LINES[@]}"; do printf '  %s\n' "$t"; done`，`emit()` :371 把每步行 append 进 `STEP_LINES`——**step6 在自己那行被 run_step `emit` 之前就写盘**，故落盘的「## 六行状态」实际只有前五行（步6 行 run_step 在 step6_evidence return 之后才 emit）。rc 75/76 现有覆盖仅 test:126 断言 `--help` rc 表**文字**含 "75"/"76"，**无从部署入口真跑出 75/76 的负控** | `sed -n '14,19p;371,385p;1179p' scripts/deploy-vault.sh`；`sed -n '118,128p' backend/tests/unit/test_deploy_vault_sh.py` |
| **④ ancestor_symlink_hits 独立门（UAT §十一.14）**：`cls_forbidden_paths.py:426` `def ancestor_symlink_hits(...)`；`check_forbidden_paths` 末 **:539** `return ancestor_symlink_hits(raw_path, targets, claude_prefixes)`；承重注释 **:527-538**；`backend/tests/unit/test_deploy_vault_sh.py` 全文 `ancestor_symlink_hits` **0 命中**（无任何独立门，Codex r3「删掉它现有样本仍全绿」） | `grep -nF 'ancestor_symlink_hits' scripts/cls_forbidden_paths.py`（实测 **6** 命中：:426 def / :529·:531·:532·:538 注释 / :539 return）；`grep -cF 'ancestor_symlink_hits' backend/tests/unit/test_deploy_vault_sh.py`（0） |
| **⑤ M-1 nlink（UAT §十一.29）**：`assert_writable_now()` **:201-230**（:229 `return 0` / :230 `}`），`:225 if [ "$nlink" -gt 1 ]`；`case` **:219-224** 只拦 `''` 与 `*[!0-9]*`——**不拦 `0`**（`[ 0 -gt 1 ]` 假 ⇒ 放行），**不拦整数溢出**（超 64 位的纯数字串仍过 case，`[ "$huge" -gt 1 ]` 报错 rc=2 ⇒ `if` 判假 ⇒ fail-open）；python 取 nlink :212-216（`2> /dev/null` 在 :216 吞掉 python 的 rc），未单独判 python 退出码 | `sed -n '201,230p' scripts/deploy-vault.sh` |
| **⑥ M-2 源码门其余两处（UAT §十一.29）**：test 内源码门用 `src.count(...)` 计数形态——`:1194` `count("local -a PENDING_WRITES=(")==1`（清单元素被替换：计数挡不住等长替换）、`:1225/:1228/:1234` `count("open_pinned(")==2`/`count("write_all(fd, ")==2`/`count("os.ftruncate(fd, 0)")==2`（ftruncate 前置顺序 / 数组丢引号：计数不查语义/顺序）。三退化里 M-4 已回应，**其余两处（ftruncate 前置顺序 + 数组丢引号 或 清单元素等长替换）计数门仍可存活** | `sed -n '1190,1236p' backend/tests/unit/test_deploy_vault_sh.py` |
| **⑦ M-3 tr -d（UAT §十一.29）**：`:736` `have="$(printf '%s' "$line" \| cut -d= -f2- \| tr -d '"'"'" \| tr -d '\r')"`——`tr -d` 删**值内全部** `"` 与 `'`，含 `O'Brien` 的合法父路径（如 `VAULTS_ROOT=/Users/O'Brien/vaults`）会被剥成 `/Users/OBrien/vaults` ⇒ `have != v` ⇒ A3「已有 .env 与参数矛盾」误拒 rc 73（:737-739 `STEP_MSG`） | `sed -n '734,739p' scripts/deploy-vault.sh` |
| **⑧ M-5 变异存档方法学（UAT §十一.29）**：「红集总量相同不证明事件来源相同」——负控/变异存档须每条绑 nodeid + 断言消息片段 + 变异前 `sha256` + 逐字节还原核对（不能只贴摘要与红集总数）。既有「车道负控」承担端到端（test:1528 注释「端到端由车道负控承担，不在 pytest 里」） | `sed -n '1525,1532p' backend/tests/unit/test_deploy_vault_sh.py` |
| **本批纪律**：本卡**不触及 `backend/app`**（改的是 `scripts/**` 与 `backend/tests/unit/**`）⇒ **不跑 pyright、不在 pyright `app`=0 门面内**；`python-typecheck` hook glob 仅覆盖 `backend/app`，若异常触发本卡改的 .py 报错 = 按本卡自己清（不得 `LEFTHOOK_EXCLUDE`）。改了 `backend/tests/unit/test_deploy_vault_sh.py`（.py）⇒ lefthook `python-lint`（ruff）会跑：判据用 **zsh 数组写法**（§二.5）；**若本卡也改 `scripts/cls_forbidden_paths.py`**（④ 条件性），`python-lint` glob `{backend,src,scripts}/*.py` 同样对它跑 `ruff check` + **`ruff format --check`**（scripts/ 的 ruff.toml `select=[]`，真门是 `ruff format --check`）——ruff 判据 pathspec 须同时覆盖 `backend/**/*.py` 与 `scripts/*.py`（§二.5）。判据里 **git** 输出一律 `git --no-pager <cmd> --no-color` + 同次验伪锚（`--no-color` 是 **git** 的 flag、不是 grep 的，写成 `grep --no-color` = grep 报错退出 = 假绿/假红，R-B14-11a）；含 `exit 1` 的判据块一律包进 `( … )` 子 shell（R-B14-11b，见 §二.5）；evidence 用 **`.txt` 不 `.log`**（仓根 `.gitignore` 吞 `*.log`）；承重裁判末行 **`rc=$pipestatus[1]`**（zsh）。**批中禁装/升任何工具**（不碰共享 venv、不升 lefthook）。`fsrs_bridge.py` / `decay_beta.py` ⛔ 零写者；live vault `canvas-vault/**` / 7691 / 7687 / 现网 LanceDB 只读 | 手册 §零；协议 §2.2 |

## 一 完成条件（AND）

- **(a) 第 0 分钟**：`pwd` = `…/worktrees/card-t2-deploy`、分支 `card/t2-deploy`、HEAD = **T2-D CARD-HOSTS-CODEX 末 commit**（`git log -1 --oneline` 应含 `CARD-HOSTS-CODEX`；**前提不成立**——HEAD 不是 T2-D、或 `git status --porcelain` 非空——即停下报主 session，不开工）；`test -x backend/.venv/bin/pytest && test -f backend/.env`。开工先 `sed -n`/`grep -nF` 逐条核 §〇 每个 file:line（漂移则在验收单写「卡文 :X → 实测 :Y」）。**基线自证（⛔ 基线在 feature 主干树且 untracked，本车道树没有这个目录）**：`BASE=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/evidence-b14/unit-red-baseline-08100483.txt`；**唯一口径（主 session 裁定 R-B14-2）** `test -f "$BASE" && grep -vc '^#' "$BASE"` → **64**（该文件 67 行 = 3 行 `#` 注释 + 64 条真 nodeid；交叉核 `grep -cE '^(ERROR|FAILED)' "$BASE"` 同为 **64**，两数都得是 64）。⛔ **禁写 `grep -c '::'`**（那是 **65**：第 3 行注释里逐字引了一条 flaky nodeid，也带 `::`），也别拿 `grep -vc 'test_deploy_vault_sh'` 当过滤器（基线本就是带 `--ignore` 生成的，该 filter 对本基线是空操作、挡不住那条注释行）。不是 64 或文件不在 ⇒ 停下报主 session。
- **(b) 目标漂移负控（①；先红后绿）**：在 `backend/tests/unit/test_deploy_vault_sh.py` 新增一条负控 `test_step4_src_drift_negctl_*`——把 `deploy-vault.sh` **:1036** `src="$SRC_MIRROR"` 突变为 `src="$VAULT"`（突变走**副本**：`cp deploy-vault.sh → tmp`，`sed` 改 tmp，用 tmp 跑 `--apply --port 8189`；或 fixture 级 EXIT/`try...finally` 还原 + 跑前跑后 `shasum -a 256 scripts/deploy-vault.sh` 逐字节同，**禁 `git stash`/`git checkout`**），断言该突变被抓住（verify 步 FAIL / 报告 `content-drift` ≠ 0 / 部署 rc≠0）。**先红后绿对照**：突变态下新负控**必红（抓住）**，clean 态下**必绿**（真 `src=$SRC_MIRROR` 时 content-drift=0、deploy rc=0）。⛔ **若运行时实测突变仍存活**（`src="$VAULT"` 时 content-drift 仍 =0、deploy 仍 rc=0）**且修复需要改 `verify_vault_install.py`（T7 地盘）或 `backend/app`** → **停下，在验收单「本卡未证明什么」与 notes 写明「目标漂移实证突变存活，修复面落在 T7 `verify_vault_install.py` content-drift 语义，本卡不扩面」**，本项登记为「已建负控、缺陷移交」不算未完成——**不得自行改 T7/app 代码**。
- **(c) 六写点 mktemp/O_EXCL/rename（②；先红后绿）**：开工先 `grep -nE`/AST 把 deploy-vault.sh 的 bash `>`/`: >` 写点**逐一枚举落档**（§〇 列的 env tmp / install 日志 / key tmp / compose-config / deploy 报告 tmp 五面；verify 报告 `$rep` 由 T7 python 写，**本卡不碰**，在验收单如实声明「第六处落在 T7 `verify_vault_install.py --report`，本卡不扩面」）。把五面改为**先在同目录 `mktemp` 原子建临时文件（O_EXCL 语义，不跟随预置软链/硬链接）→ 写入 → `mv`/`rename` 到位**（bash 做不到真 O_EXCL 的，把该写入搬进既有 `open_pinned` python helper，形态照 :820-828/:873-879，**不新造 python 写法**）。**先红后绿**：① 源码门（test 内）断言这五面不再是「裸 `>` 写可预先命名的终路径」→ 改前红、改后绿；② 运行时负控：在一个写点的 tmp 目标上**预置软链/硬链接**，跑对应步骤 → 写入必被拒（不穿链）、改前若能穿则红。`bash -n` rc=0。
- **(d) rc 表主张补全（③；两子项，各先红后绿）**：
  - (d-i) **rc 75/76 入口级负控**：新增两条从**部署入口**真跑出 rc 的负控——注入 step5 activate 失败（如健康断言/桩失败）→ 进程 rc **75**；注入 step6 evidence 失败（如 evidence 目录不可写 / shasum 失败）→ 进程 rc **76**；并证明**顶层失败（run_step 之外，如参数解析 / seed 阶段 `exit`）仍归 `70+n` 映射、不退化成裸 rc=1**（形态照 :613-616 注释钉的那类回归）。改前无此负控（新增即绿）；配一个反向负控：临时破坏 `run_step` 的 `exit $((70+n))` 映射 → 入口负控必红。
  - (d-ii) **六行状态落盘前五行**：修 step6_evidence 使落盘「## 六行状态」含**全部六行**（步6 自己那行由 step6 合成写入，或把落盘时机挪到六步 emit 齐之后；不得靠 run_step 事后改文件）。**先红**：新增一条断言「`--apply` 成功后 `deploy-<ts>.txt` 的步骤行恰 6 条且含 `[6/6] evidence`」→ 改前红（只 5 条）、改后绿。禁把失败路径的「只打印已执行前缀」改坏（失败入口仍只列已跑步骤）。
- **(e) ancestor_symlink_hits 独立门（④；先红后绿）**：给 `ancestor_symlink_hits` 一条**独立**负控——做出一个**只有 `ancestor_symlink_hits` 能命中、逐段 walker 命不中**的祖先软链拓扑样本，断言 `check_forbidden_paths` 仍拦下；并用变异证明其承重：临时把 `:539` 的 `return ancestor_symlink_hits(...)` 换成返回 `None`（或删该调用）→ 该负控**必红**（现状「删掉它样本仍全绿」= 改前红在「没有独立门」这件事上：先证 clean 态该样本被拦、再证去掉 ancestor_symlink_hits 后样本漏放，两跑对照）。变异走 EXIT/`try...finally` 无条件还原 + `cls_forbidden_paths.py` 跑前跑后 `shasum -a 256` 逐字节同。若实测逐段 walker 已涵盖所有可做出的样本（真做不出「只它能命中」的拓扑）→ 停下如实登记「ancestor_symlink_hits 做不出独立承重样本，保留作防御深度，如实标注无独立门」，**不强造假门**。
- **(f) M-1/M-2/M-3/M-5（⑤⑥⑦⑧；各先红后绿）**：
  - M-1（`deploy-vault.sh:201-230`）：`assert_writable_now` 的 nlink 判据补 `0`（fail-closed）与整数溢出（超长纯数字串 fail-closed，如按位数上限判）两态，并显式判 python 取值 rc。负控：喂 `nlink="0"` 与一个超 64 位的纯数字串 → 改前放行（fail-open）改后拒（fail-closed）。
  - M-2（`test_deploy_vault_sh.py:1190-1236`）：把「清单元素被替换（等长）/ ftruncate 前置顺序 / 数组丢引号」里**其余两处**从纯 `count()` 收窄为查语义/顺序（如断言 fstat 出现在 ftruncate 之前、PENDING_WRITES 每项带引号且值正确）。负控：对 deploy-vault.sh 副本做对应等长替换/去引号/换序 → 改前源码门仍绿（存活）改后红。
  - M-3（`deploy-vault.sh:736`）：改为**只剥首尾引号、保留值内引号**（不用 `tr -d` 无差别删）。负控：备一份 `.env.<vault>`，其中 `VAULTS_ROOT=/Users/O'Brien/vaults` + 同参数二次 `--apply` → 改前 A3 误拒 rc 73、改后不误拒。
  - M-5：本卡所有变异/负控存档每条绑 nodeid + 断言消息片段 + 变异前 `sha256` + 逐字节还原核对（落 `evidence-g27b-tail/`），验收单只引用路径与末行 rc、不自述数字。
- **(g) 收尾裁判（见 §二）**：`bash -n scripts/deploy-vault.sh` rc=0；`test_deploy_vault_sh.py` **文件级单跑全绿**（本卡新增门全过，含 b/c/d/e/f 的「改后绿」那一跑）；**地盘核** `git diff --stat --no-color <T2-D 末 commit> HEAD -- . ':(exclude)_bmad-output'` ⊆ {`scripts/deploy-vault.sh`, `backend/tests/unit/test_deploy_vault_sh.py`, `scripts/cls_forbidden_paths.py`}（验伪锚：去掉 exclude 应多出 `_bmad-output/` 路径）；**tests/unit 目录级 diff 只许 `<`**（基线 `$BASE` 64 条，跑法带 `--ignore tests/unit/test_deploy_vault_sh.py`——与基线同口径；本卡改的正是被 --ignore 的那个文件，故它走文件级单跑，其余 unit 与基线 diff 不得出现任何 `>`）；Codex 多轮 D-15 固定串「Codex gpt-6-astra ultra 多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0」（上限 5 轮；见 §四）。
- **(h) 两清单必填**：「本卡未证明什么」≥4、「台账待登记条目」≥4（见 §四）。

## 二 裁判命令

```zsh
# —— 树根变量（EV 必须绝对路径：承重裁判带 cd backend 时相对 EV 会落到不存在的 backend/_bmad-output）——
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy
PYTEST=$(pwd)/backend/.venv/bin/pytest
EV=$(pwd)/_bmad-output/审查/evidence-g27b-tail ; mkdir -p "$EV"
BASE=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/evidence-b14/unit-red-baseline-08100483.txt
T2D=$(git rev-parse HEAD)   # 开工即 T2-D 末 commit；收工地盘核用它

# 0) 第 0 分钟自证
git rev-parse --abbrev-ref HEAD            # card/t2-deploy
git log -1 --oneline | grep -F CARD-HOSTS-CODEX   # 前提：HEAD = T2-D
git status --porcelain | wc -l             # 0
test -f "$BASE" && grep -vc '^#' "$BASE"     # 64 —— R-B14-2 唯一口径（⛔ 禁 grep -c '::'：那是 65，注释行引了 1 条 flaky nodeid）
grep -cE '^(ERROR|FAILED)' "$BASE"            # 64 —— 交叉核，两数必须都是 64

# 1) bash 语法 + §〇 锚逐字核
bash -n scripts/deploy-vault.sh; echo rc=$?                        # 0
grep -nF 'src="$SRC_MIRROR"' scripts/deploy-vault.sh              # 1036，唯一
grep -nF 'ancestor_symlink_hits' scripts/cls_forbidden_paths.py   # 6 命中：:426 def / :529·:531·:532·:538 注释 / :539 return

# 2) 承重裁判（tee + rc=$pipestatus[1]）——以「改后绿」那一跑为终判，先红跑也各留一份
cd backend && PYTHONDONTWRITEBYTECODE=1 $PYTEST -q -p no:cacheprovider tests/unit/test_deploy_vault_sh.py \
  2>&1 | tee "$EV/deploytest-close-$(date +%Y%m%dT%H%M%S).txt"; echo rc=$pipestatus[1]
# 期望：全 passed，rc=0（含 b/c/d/e/f 的改后门）

# 3) rc 75/76 入口负控末行（从本卡新增的入口负控存档里引用，示意）
#    验收单只引用存档路径 + 末行 rc，不自述数字（M-5）

# 4) 目录级 tests/unit（与基线同口径：--ignore tests/unit/test_deploy_vault_sh.py —— R-B14-3：cd backend 之后必须写相对路径，写 backend/tests/... 是空操作），diff 只许 '<'
cd "$(git rev-parse --show-toplevel)"/backend 2>/dev/null || cd backend
TS=$(date +%Y%m%dT%H%M%S); RUN="$EV/unit-close-$TS.txt"
PYTHONDONTWRITEBYTECODE=1 $PYTEST tests/unit --ignore tests/unit/test_deploy_vault_sh.py -q -p no:cacheprovider \
  2>&1 | tee "$RUN"; echo rc=$pipestatus[1] | tee -a "$RUN"
grep -E '^(FAILED|ERROR) tests/' "$RUN" | sed 's/ - .*//' | sed 's/^[A-Z]* //' | sort -u > "$EV/close.nodeids"
grep -v '^#' "$BASE" | sed 's/^[A-Z]* //' | sort -u > "$EV/base.nodeids"
# base 侧 grep -v '^#' 剔 3 行注释（否则注释里那条 flaky nodeid 会进 base 成假 '<'）；两侧都 sed 's/^[A-Z]* //' 剥掉 ERROR/FAILED 前缀 ⇒ 裸 nodeid 同口径可比（基线行内无 ' - 消息' 尾巴，实测 grep -c ' - ' = 0，故 base 侧不需要 sed 's/ - .*//'）。base 应 64 条（clean 态）
diff "$EV/base.nodeids" "$EV/close.nodeids"   # 只允许 '<' 行；任何 '>' = 阻断
# ⛔ 禁用写法：grep … $EV/unit-close-*.txt（多份存档时 grep 会加文件名前缀，整份作废、diff 全变 '>' 假阻断）

# 5) ruff（zsh 数组写法；本卡改 test .py，条件性改 scripts/cls_forbidden_paths.py）——协议 §2.2 + lefthook python-lint glob {backend,src,scripts}/*.py
cd "$(git rev-parse --show-toplevel)"   # ruff 用相对 venv 路径，回 worktree 根（gate4 的 cd backend 带偏会 fail-closed）；cd 留在子 shell 外，后面 6)/8) 的相对路径靠它
# ⛔ R-B14-11b：含 `exit 1` 的判据块一律包进 ( … ) 子 shell——交互 zsh 里裸 `|| { …; exit 1; }` 会直接关掉车道自己的 shell；exit 只退子 shell，父 shell 的 $EV/$BASE/$T2D 不受影响
(
  F=(${(f)"$(git diff --name-only --diff-filter=AM "$T2D" HEAD -- 'backend/**/*.py' 'scripts/*.py')"})
  print -r -- "files=${#F}"; (( ${#F} )) || { echo "零文件 ⇒ fail-closed"; exit 1; }
  backend/.venv/bin/ruff check -- "${F[@]}"; echo "check_rc=$?"
  backend/.venv/bin/ruff format --check -- "${F[@]}"; echo "format_rc=$?"   # scripts/ 的真门是 format --check（lefthook 同跑），ruff check 对 scripts/ 近空操作（ruff.toml select=[]）
  # 验伪锚（承重）：喂一个已知含 F401 的文件必 check_rc=1
  # backend/.venv/bin/ruff check -- <known-F401-file>; echo "falsify_rc=$?"   # 1
); echo "ruff_block_rc=$?"   # 1 = 零文件 fail-closed 触发；0 只表示块跑完，ruff 结论看上面 check_rc / format_rc 两行

# 6) 地盘门（--no-color + 验伪锚）
git diff --stat --no-color "$T2D" HEAD -- . ':(exclude)_bmad-output'
#   ⊆ {scripts/deploy-vault.sh, backend/tests/unit/test_deploy_vault_sh.py, scripts/cls_forbidden_paths.py}
git diff --stat --no-color "$T2D" HEAD -- .   # 验伪锚：应多出 _bmad-output/ 路径

# 7) 现网只读哨兵
touch "$EV/sentinel"
# …收工：find <现网 LanceDB 目录> -type f -newer "$EV/sentinel" | wc -l → 0（只 ls -la，不 connect）

# 8) Codex 后：绑最终 HEAD
git diff --stat --no-color <审SHA> HEAD -- . ':(exclude)_bmad-output'   # 空
# ⛔ 逐份数、别一条 grep -c 打多份：多文件时 grep -c 输出是 `<文件>:<数>` 而不是一个数，
#    且 glob 必须写 `…TAIL*.md`（round-1 存档可能就叫 codex-review-CARD-G2-7b-TAIL.md、无 -rN 后缀，
#    写 `…TAIL-*.md` 会一份都不匹配 ⇒ rc=2 且无输出，「≥1」这条判据等于没跑成）
for f in _bmad-output/审查/codex-review-CARD-G2-7b-TAIL*.md; do
  printf '%s model=%s\n' "$f" "$(grep -cF 'gpt-6-astra' "$f")"
done   # 每一份各 ≥1（协议 §2.1 首部 model 行；缺 = 该轮不计配额）；不写旧模型名字面量，避长度门 ⑪
# 验伪锚：`printf 'x\n' > /tmp/no-model.md; grep -cF 'gpt-6-astra' /tmp/no-model.md` → 0（证这条真能出 0）
```

- ⛔ `':(exclude)_bmad-output'` 写法（`':!…'` 在 zsh / git 2.50 下报 `Unimplemented pathspec magic`、rc=128、stdout 空 ⇒「为空即绑定」会把没跑成读成绿，协议 §1）。
- 承重裁判一律 `2>&1 | tee $EV/<name>-$(date +%Y%m%dT%H%M%S).txt; echo rc=$pipestatus[1]`；`.txt` 不 `.log`。
- ⛔ 任何 `|| { …; exit 1; }` 形态的 fail-closed 判据（§二.5 ruff 块，以及车道自己照协议模板新写的）都必须整块包进 `( … )` 子 shell 再跑——裸写会在交互 zsh 里把车道的 shell 关掉（R-B14-11b，T2-E 修正者实测）。
- 变异/负控（b/c/e/f）每段：跑前跑后全文件 `shasum -a 256` 两行逐字节同；EXIT/`try...finally` 无条件还原；**禁 `git stash` / 禁 `git checkout HEAD -- <path>`**（用副本或 `git show HEAD:<path> > <tmp>` 比对）。

## 三 禁改与隔离

- **本卡地盘（只允许改这三个文件）**：
  1. `scripts/deploy-vault.sh`（② 六写点 mktemp/O_EXCL/rename、③ rc 表主张、⑤ M-1 nlink、⑦ M-3 tr -d）；
  2. `backend/tests/unit/test_deploy_vault_sh.py`（① 目标漂移负控、③ 六行状态门、④ ancestor_symlink_hits 独立门的测试侧、⑥ M-2 源码门收窄、各项先红后绿）；
  3. `scripts/cls_forbidden_paths.py`（④ ancestor_symlink_hits 若需生产侧配合独立门）。
  与设计稿 §3「只 T2」一致。
- **禁改面**：`scripts/verify_vault_install.py`（**T7-D 地盘**，content-drift 计算在此，本卡只读；(b) 若缺陷落此则移交，不扩面）；`scripts/vault-install-manifest.json`、`.claude/skills/deploy-vault/SKILL.md`（仓根真名，R-B14-8）、`docker-compose*.yml`（T2 其它卡已处置，本卡不动）；`backend/tests/conftest.py` / `tests/unit/conftest.py`（U7/T9、T10 地盘）；T2-A/B/C/D 已 commit 的改动（本卡叠在其上，只 append/改本卡面，不回滚前卡）。
- **硬边界**：⛔ 禁写 live vault `/Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault/**`；⛔ 禁连 7691 / 7687；⛔ 禁碰 `canvas-vault/.claude/scripts/fsrs_bridge.py` / `decay_beta.py`（本卡零关联，三改动文件 `grep -rn fsrs_bridge` 应 0 命中）；⛔ 现网 LanceDB 目录只读（不 connect、不 initialize）；⛔ 不触 `backend/app/**`（若 diff 出现 app 文件 = 越界，停下）；⛔ 禁 `git stash`（共享栈）；不改台账（只主 session 改，卡在验收单写「台账待登记条目」）；不 push；**批中禁装/升任何工具**（不碰共享 venv、不升 lefthook）；`*.stderr*` 不入库（`.gitignore` 已覆盖）。
- **禁放宽判据**：(b)/(e) 的负控必须真做突变对照，不得改成「源码里有某字样即绿」的纯文本门（Codex r2/r3 已两次指出源码门不承重）；(d-i) 必须从**部署入口**跑出 rc，不得只证「辅助逻辑返回 1」；(d-ii) 落盘六行不得靠 run_step 事后改文件伪装。

## 四 Codex / 验收单

- **命令**（协议 §2 固定）：`codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G2-7b-TAIL[-rN].md)" > _bmad-output/审查/codex-review-CARD-G2-7b-TAIL[-rN].md 2> _bmad-output/审查/codex-review-CARD-G2-7b-TAIL[-rN].stderr </dev/null`
- **轮次**：**Codex gpt-6-astra ultra 多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0**（本卡有代码改动 ⇒ 多轮、上限 5；第 5 轮仍有 HIGH 停下交主 session；审后再改代码必再送一轮、存档带 `-rN`；车道对 HIGH 的驳回写理由但不能自判通过；0 字节存档重发一次，再 0 字节 → 主 session 人审替代，不等配额）。
- **prompt 五分节**：①背景（deploy-vault.sh G2-7b 尾巴 5 项）；②作者自述请独立核对（目标漂移负控是否真抓住 src 突变、六写点 O_EXCL/rename 是否真原子且不跟随预置链、rc 75/76 是否从入口跑出、六行状态落盘是否六行、ancestor_symlink_hits 独立门是否承重、M-1/M-2/M-3 各负控方向）；③按重要性排序的问题（file:line + 一句核验路径）；④输出格式（BLOCKER/HIGH/MEDIUM/LOW + file:line）；⑤边界（只读、不跑 hook、不连库、不评 T7 `verify_vault_install.py` 的 content-drift 语义）。
- **最小读取面写死**：`git diff <T2-D 末 commit> <审SHA> -- . ':(exclude)_bmad-output'` + `deploy-vault.sh` `:199-230`/`:373-385`/`:969-1057`/`:1159-1228`/`:730-740`、`cls_forbidden_paths.py:420-540`、新/改测试全文、本卡负控存档末行 rc。
- **禁用四措辞**（见协议 §2）：prompt 与存档改说「负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径」。
- **存档首部**（协议 §2.1，六行 blockquote + `---`）：批次/车道/卡/round；`模型 gpt-6-astra · reasoning_effort ultra · codex <--version 实测>`（抄 `.stderr` 中含 codex 版本行 + `model:` 行 + reasoning 行的那三行，**行号不限、括注所抄行号**——协议 §2.1：codex 0.153.3 把 `model:` 排在会话头第 5 行，字面抄前三行会漏自证字段；`.stderr` 本身不入库）；审查绑定 SHA（HEAD 若不同须如实写）。⚠️ 缺 `模型 / reasoning_effort / codex` 任一字段 = 该轮不计配额。
- **验收单** `_bmad-output/验收单/UAT-CARD-G2-7b-TAIL-<日期>.md`：DoD-3 双段——4-A Claude 已代验（贴 bash -n / test 文件级全绿 / rc 75/76 入口存档 / 地盘 diff / tests/unit diff / ruff / 各负控存档路径与末行 rc）；4-B 零技术词（一句「我一键部署一门课时，就算脚本被人动了手脚想把别处的文件当成我的课来比对、或写到不该写的地方，它都会当场停下并如实报错；部署成功后那份记录里六步都在、不缺最后一步——我感觉这套部署终于对得起『安全一键』这四个字」+ felt-sense）。
- **本卡未证明什么**（≥4）：① 未证明目标漂移突变在所有端口/源布局下都被抓（只造了非缺省端口一例；若实测存活则缺陷移交 T7 `verify_vault_install.py`）；② 未证明 mktemp/O_EXCL/rename 后残留 TOCTOU 窗口为**零**（bash 仍非 `openat` 原子，彻底消除需全搬 python，本卡只收最窄 + 负控覆盖能造出的预置链）；③ verify 报告 `$rep` 的第六处写点落在 T7 `verify_vault_install.py --report`，本卡未改、未证其原子性；④ ancestor_symlink_hits 独立门只在能造出的祖先软链拓扑上承重，未覆盖逐段 walker 与它的**全部**交集；⑤ M-1 整数溢出只按位数上限 fail-closed，未枚举所有非常规 nlink 值；⑥ 未跑真 `docker compose up -d`（T2-B 面，需授权），rc 75 入口负控走桩/注入失败路径、非真 activate 失败。
- **台账待登记条目**（≥4）：① deploy-vault.sh 六写点 O_EXCL/rename 改动 sha + 负控 nodeid；② 目标漂移负控结论（突变被抓 / 存活移交 T7，二选一如实）+ content-drift 语义落在 `verify_vault_install.py`（T7）的边界；③ rc 75/76 入口负控 + 六行状态落盘修复的门 nodeid；④ ancestor_symlink_hits 独立门结论（承重 / 做不出独立样本，二选一）；⑤ M-1/M-2/M-3 各修复 + 负控 nodeid；⑥ Codex 各轮存档路径、绑定 SHA、B/H/M/L 计数；⑦ tests/unit 目录级 diff 结果（与基线 64 同口径）；⑧ 第十四批红基线在 feature 主干树且 untracked，车道引用须用主干绝对路径 + 开工自证（建议主 session 收进手册 §零）。
- commit：单独 commit（同车道已无后续卡，但仍须工作树干净收尾）；**commit message 含 `CARD-G2-7b-TAIL`**；header ≤100 含批次标记 `[BATCH-2026-09-11-第十四批 / CARD-G2-7b-TAIL]`，body 行 ≤100（`wc -m`）；`*.stderr*` 不入库；不 push；跑完说「**复核第十四批 T2**」。
