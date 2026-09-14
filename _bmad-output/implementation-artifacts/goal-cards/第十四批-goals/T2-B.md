> ⚠️ 本文件是 CARD-G2-8 的完整卡文——车道开工后必读并逐条执行；它不是 /goal 粘贴文本。/goal 在第十四批手册 §三 T2-B 块。
> 批次标记 `[BATCH-2026-09-11-第十四批 / CARD-G2-8]`。车道：`card-t2-deploy`（分支 `card/t2-deploy`，NEW @ `08100483`，`backend/.venv` 目录级 symlink 已建、`backend/.env` 已拷），本车道第 2/5 张；**前提 = 前一卡 T2-A CARD-DEPLOY-TIMEOUT 已独立 commit 且 `git status --porcelain` 空**，之后串 T2-C CARD-HOSTS-OPENCODE。用户已裁：D-15 多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH=0；**本批唯一真部署卡 = 本卡，真 `docker compose up -d` 需用户当次授权，未授权即 SKIP 并如实登记「真 activate 未执行」**；`/vault/switch` 已 410（运行时切换不存在，决策页 §一）。勘探 2026-09-11 于主干 `08100483`（B14_BASE）：设计稿 §4 T2-B / recon B §A+§D / recon C §13 / UAT-CARD-G2-7b-2026-09-09.md（名口径 + also-push + 真 up -d 归属）。协议（⛔ 只读 **feature 主干树 `--add-dir` 那份**）：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/.claude/rules/card-batch-protocol.md`（§1 合并门 + 绑定口径 / §2 Codex 命令 / §2.1 存档首部 / §2.2 裁判落盘 + --no-color / §5 排批）；手册同理只读主干树那份：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/2026-09-11-第十四批开跑手册-10车道43卡.md`（§零 / §一 / §四）。⚠️ **车道树自己的 `.claude/rules/card-batch-protocol.md` 是 `08100483` 版，本批三处回写（§2.1 首部改「抄含版本行+model 行+reasoning 行」/ §2.2 ruff zsh 数组 + 禁 `| tail -1` / §2.3 过渡条款）只在 `--add-dir` 那份——别读车道树那份，按主干树的读。**

# CARD-G2-8 — 部署激活事务化：真 `up -d` 起/重建本 vault 的 `cls-<vault>` 实例 + 健康断言失败只拆本实例（别的 vault 一动不动）+ index journal 隔离 / Lance 首索引计时 / Graphiti readiness `skipped-with-reason` + 实现 `--also-push`（追加 `DAILY_REVIEW_VAULTS` 去重、不动 `ACTIVE_VAULT`）

## 〇 事实

| 事实 | 位置 / 实测命令 |
|---|---|
| **语义定调（recon B §D 整段照抄，逐字遵守）**：总账原卡文 `2026-08-28-主goal全量分goal总账-v2.md:600-605` 写的「preflight→journal 隔离→backend recreate→health→Lance 首索引→Graphiti 回填钩子→UAT 提示；任一阶段失败**自动恢复旧 `ACTIVE_VAULT`**；同进程只服务一个 active vault」这套「切换 + 回滚旧 vault」语义**已被决策页 §一作废**（`/vault/switch` 已 410，运行时切换不存在）。正确语义：部署单元 =（vault, 它绑定的后端实例）；**激活 = 起/重建该 vault 自己的 `cls-<vault>` 实例，不顶掉别的 vault**；**失败回滚 = 把本 vault 这一个 compose 项目 `cls-<vault>` 拆掉/回上一版，别的 vault 实例一动不动**（不是「恢复旧 `ACTIVE_VAULT`」）。本卡只取原卡文的**结构**（阶段 / journal / Lance 计时 / Graphiti readiness / UAT 提示），语义按上面替换 | recon B §D；决策页 §一 |
| **步 1~4 只复用不重写**：它们是 G2-7b 的交付面（12 轮 Codex + 禁写面对抗测试背书）。G2-8 只**包裹步 5 `step5_activate` 与步 6 `step6_evidence`** + 实现 `--also-push` + 收 canvas-vault 名口径缺口 | recon B §D |
| **路径/树**：`scripts/deploy-vault.sh` 在 B14_BASE 与当前主干树工作副本**逐字节同**（`git diff --stat --no-color 08100483 -- scripts/deploy-vault.sh backend/tests/unit/test_deploy_vault_sh.py scripts/cls_forbidden_paths.py` 输出空，波 0 三笔 commit 未碰 `scripts/**`）；`wc -l scripts/deploy-vault.sh` = **1238** | `git diff --stat --no-color`；`wc -l`（本次写卡实测于主干树） |
| **六步锚（B14_BASE 实测，仅作线索，⚠️ 开工前必在 T2-A tip 重定位——见下一行）**：`step1_preflight()` **389**、`step2_install()` **639**、`step3_postprocess()` **684**、`step4_verify()` **969**、`step5_activate()` **1060**（函数体止于 `}` 行 **1156**）、`step6_evidence()` **1159**（止 **1221**）；`run_step()` 定义 **373**；六次调用 **1230-1235**（`run_step 1 preflight step1_preflight` … `run_step 6 evidence step6_evidence`） | `grep -nE -e '^step[0-9]_' -e '^run_step' scripts/deploy-vault.sh` → **13 行**（B14_BASE：6 个 `stepN_` 定义 + `run_step()` 定义 :373 + 6 次调用 :1230-1235；原写法以反斜杠竖线作 ERE 交替恒 0、且 `^run_step ` 尾空格漏掉 :373，2026-09-14 改 `-e` 多模式 + 去尾空格后实测 13） |
| ⛔ **串行行号漂移（承重，开工第一件事）**：前提 T2-A CARD-DEPLOY-TIMEOUT **已改 `step1_preflight`**（在 `npm run build` 处加超时 + 离线标志，位于本卡面之前）**与 `test_deploy_vault_sh.py`**（16 处裸 `subprocess.run` 加 `timeout=`）。⇒ 在 T2-A tip 上，`scripts/deploy-vault.sh` 步 5 以后所有行号**已整体下移**。§〇 的 `:1060`/`:1118`/`:1121`/`:1139` 等是 **B14_BASE 锚点线索，不是 T2-A tip 实值**。开工必须用 `grep -nF '<签名串>'`/函数名/AST 在**本车道树当前 HEAD**重新定位，行号漂移在验收单写「卡文 :X → 实测 :Y」 | `git diff --stat 08100483 HEAD -- scripts/deploy-vault.sh`（开工实测必非空，T2-A 改过） |
| **激活闸门**：`if [ "$CLS_DEPLOY_ALLOW_DOCKER_UP" != 1 ]; then` 在 B14_BASE **:1114**，缺省分支 `STEP_MSG="config 断言过…未设 CLS_DEPLOY_ALLOW_DOCKER_UP=1 ⇒ 不执行 up -d（缺省即不做, 需用户当次授权）"` **:1115** → `return 2` **:1116**（SKIP）→ `fi` **:1117**；默认值 `CLS_DEPLOY_ALLOW_DOCKER_UP="${CLS_DEPLOY_ALLOW_DOCKER_UP:-0}"` **:74**；头注 **:60-61** | `grep -nF 'CLS_DEPLOY_ALLOW_DOCKER_UP'`（本次写卡实测） |
| **口径更正①**：UAT-CARD-G2-7b-2026-09-09.md §3.2 写「真 `up -d`…（`CLS_DEPLOY_NO_DOCKER_UP=1` 后 SKIP）」，**主干实测闸门变量名是 `CLS_DEPLOY_ALLOW_DOCKER_UP`（缺省 0 = SKIP，显式 =1 才真跑）**，不是 `CLS_DEPLOY_NO_DOCKER_UP`。卡文与实现一律用 `CLS_DEPLOY_ALLOW_DOCKER_UP` | 本次写卡 `grep -nF` 实测 |
| **真 activate 桩（G2-8 面「写好未跑」，本卡要跑起来）**：闸门后注释 `# 真 activate（G2-8 面）：起/重建该 vault 的绑定实例 + 健康断言 + 失败回滚。` **:1118** / `# 需用户当次授权；车道禁跑（见头注与 §三）。` **:1119**；`docker compose … config` 结构化断言命令起 **:1073**（`-p "cls-$VAULT_NAME" … config` **:1074**）；真起实例命令起 **:1121**（`-p "cls-$VAULT_NAME" --project-directory "$HARNESS" up -d backend` 在 **:1122**）；`up -d` 失败回滚命令起 **:1126**（`… down` 在 **:1127**），`# ⛔ down 失败时不得仍声称「已回滚」（Codex r1 HIGH-3）` **:1128**，STEP_MSG 分叉 **:1130**（已回滚）/ **:1132**（down 也失败，需人工处置）；健康断言 `cur="$(curl -sS --fail -m 10 "http://127.0.0.1:$PORT/api/v1/vault/current" 2> /dev/null)" \|\| curl_rc=$?` **:1139**（curl rc 单独判，Codex r1 HIGH-3 注释 **:1136-1137**）；未报告 vault 名时第二次回滚命令起 **:1145**（`… down` 在 **:1146**）；成功 `STEP_MSG="实例 cls-$VAULT_NAME 已起, /vault/current 报告 $VAULT_NAME"` **:1154**；`return 0` **:1155**，`}` **:1156** | `sed -n '1114,1156p'`（1156 = 闭合 `}`，1157 是空行）；`grep -nE -e 'up -d backend' -e 'curl.*-m ' -e 'compose.*down' -e '-p "cls-' scripts/deploy-vault.sh` → **7 行**（B14_BASE：1074/1122/1127/1130/1132/1139/1146，行内所列锚全在集内；原写法以反斜杠竖线作 ERE 交替恒 0，2026-09-14 改 `-e` 多模式后实测 7） |
| **三段新增确证（不是改写既有）**：`grep -niE -e 'journal' -e 'lance' -e 'graphiti' -e 'readiness' -e '首索引' -e 'skipped-with-reason' -e '回填' scripts/deploy-vault.sh` = **0 命中** ⇒ index journal 隔离 / Lance 首索引计时 / Graphiti readiness 三段脚本里**完全不存在**，本卡**新增**（登记为行为变化，不是既有 bug 修复） | `grep -niE -e …`（原写法以反斜杠竖线作 ERE 交替恒 0 = 假阴性、证明不了任何事；2026-09-14 改 `-e` 多模式后于 B14_BASE 实测**仍 0**，本行「0 命中」自此有真依据；§二 第 2 条与 (e) 的裸竖线六选一写法本机同为 0） |
| **step6_evidence 现状**：`step6_evidence()` 体已有 dry-run 零写守卫（`APPLY != 1` → `return 2`）、evidence 落盘（`deploy-$TS.txt`）、六行状态 `for t in "${STEP_LINES[@]}"`、文件 sha256 段（密钥件只 sha）；evidence 头 `printf '# CARD-G2-7b deploy-vault.sh — %s\n'`；参数行含 `printf '  activate=%s also_push=%s(未实现,登记 G2-8) evidence_dir=%s env_dir=%s\n'` 在 **:1175** | `sed -n '1159,1200p'`（本次写卡实测） |
| **`--also-push` 现状（只解析不实现）**：头注 **:16**（rc 64 触发项含 `--also-push 越界`）/ **:32**（`本版**只解析不实现**（登记 G2-8）`）；`FEATURE_TREE="…/feature-obsidian-hybrid-dev"` **:76**；`ALSO_PUSH=0` **:85**；解析 `--also-push) ALSO_PUSH=1; shift ;;` **:244**；harness 守卫 `if [ "$ALSO_PUSH" = 1 ]; then` **:361** → `[ "$_hr" = "$_ft" ] \|\| die64 "--also-push 只允许 harness == ${FEATURE_TREE}（实测 ${HARNESS}）"` **:364**；`grep -cF '未实现,登记 G2-8' scripts/deploy-vault.sh` = **1**（本卡实现后应为 0） | `grep -nE -e 'also-push' -e 'also_push' -e 'FEATURE_TREE' -e 'ALSO_PUSH' scripts/deploy-vault.sh` → **10 行**（B14_BASE：16/32/76/85/244/361/363/364/1175/1176，行内所列锚全在集内；原写法以反斜杠竖线作 ERE 交替恒 0，2026-09-14 改 `-e` 多模式后实测 10）；`grep -cF '未实现,登记 G2-8' scripts/deploy-vault.sh` → **1**（2026-09-14 复测） |
| **`DAILY_REVIEW_VAULTS` 写点（`--also-push` 目标面）**：step2 生成 `.env.<vault>` 时写 `"DAILY_REVIEW_VAULTS="`（空值）于 **:624**，键清单 `:630`；`--also-push` 语义 = 把新 vault 名**追加进 harness（feature 主干树）自己的 daily-review vault 清单去重、不动 `ACTIVE_VAULT`**（实际写点以开工 `grep -nE -e 'DAILY_REVIEW_VAULTS' -e 'ACTIVE_VAULT' scripts/deploy-vault.sh` + harness `.env` 实测为准） | `grep -nE -e 'DAILY_REVIEW_VAULTS' -e 'ACTIVE_VAULT' scripts/deploy-vault.sh` → **8 行**（B14_BASE：480/485/487 是 harness `.env*` 的 `ACTIVE_VAULT` 碰撞检查（只读）、619/624/630 是 `.env` 固定字段写入 + 回读校验、715/720 是 `.env` 键校验；原写法以反斜杠竖线作 ERE 交替恒 0，2026-09-14 改 `-e` 多模式后实测 8） |
| **canvas-vault 名口径缺口（UAT-G2-7b §3.1，归 G2-8/G4 收口）**：`VAULT_NAME="${VAULT##*/}"` 派生 **:337**；step1_preflight 的「vault 名 = `sanitize_vault_id` 与 `vault_key` 的**共同不动点**」preflight 在 **:458-476**（不动点检查 python 段 `:468-473`，拒绝 `STEP_MSG="vault 名 '$VAULT_NAME' 不是 sanitize_vault_id/vault_key 的共同不动点…"` **:476**）。连字符名 `canvas-vault` 非不动点（`sanitize_vault_id` 产 `canvas_vault` 下划线）⇒ 被 preflight 拒；UAT-G2-7b §3.1 逐字「**现网 live 的 `canvas-vault` 这个名字本身过不了这道 preflight…本脚本不能用来重建一个叫 `canvas-vault` 的库（新库须用下划线名）。归 G2-8 / G4 收口。**」⚠️ **preflight 在步 1，本卡只复用不重写步 1 逻辑**；收口 = 文档/决策落定（evidence + 验收单写清 G4 口径「live canvas-vault 不经本脚本重建、新库须下划线名」）+ 一条测试钉住「连字符名被 preflight 拒」的现状 | UAT-CARD-G2-7b-2026-09-09.md §3.1；`grep -nE -e 'VAULT_NAME' -e '不动点' scripts/deploy-vault.sh` → **31 行**（B14_BASE：`VAULT_NAME` 25 行 + `不动点` 7 行，:476 双命中；:337/:458/:476 全在集内；原写法以反斜杠竖线作 ERE 交替恒 0，2026-09-14 改 `-e` 多模式后实测 31） |
| **禁触红的既有门**：`test_second_tier_hosts_not_implemented_anywhere()` 在 `backend/tests/unit/test_deploy_vault_sh.py` **:851**，断言「非注释行不得提到 `AGENTS.md` / `.codex/config.toml` / `opencode.json` / `.dsh/*.yml`」⇒ **本卡不得碰步 3 宿主绑定件（那是 T2-C/T2-D 面）**，否则该门变红 | `grep -nF 'test_second_tier_hosts_not_implemented_anywhere'`（本次写卡实测） |
| **禁写面负控不变**：`scripts/cls_forbidden_paths.py` **609** 行（禁写面判定本体，不在 bash 里做，Codex r2 BLOCKER-1）；本卡**不碰**，收工 `shasum -a 256` 与开工同 | `wc -l`（本次写卡实测） |
| **测试文件 / compose**：`backend/tests/unit/test_deploy_vault_sh.py` B14_BASE **2596** 行（T2-A 会改其 16 处裸 `subprocess.run`，本卡在 **T2-A tip** 的基础上加新测试）；`docker-compose.yml` 存在（只读核，改动须登记）；本卡新测试全部走**桩** `docker`/`curl`（PATH 注入假二进制，与 test 文件既有桩同法 —— 实测既有桩命名是 `fake_bin = tmp_path / "bin"` + `fake_lsof = fake_bin / "lsof"` **:2226-2228/:2254-2256** + `"PATH": f"{fake_bin}:…"` **:2244/:2272**；⛔ 本文件 `stub` 字样 **0** 命中，新桩必须沿用 `fake_bin / "docker"` / `fake_bin / "curl"` 命名，否则 §二 第 8 条判据锚不上），**不真连 docker daemon / 7691 / 现网** | `wc -l`；`ls docker-compose*.yml`（本次写卡实测） |
| **基线**：`tests/unit` 红基线 = `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/evidence-b14/unit-red-baseline-08100483.txt` = **64 条**（nodeid 口径，带 `--ignore tests/unit/test_deploy_vault_sh.py`）。⚠️ 基线既带 `--ignore` 本卡主改文件，本卡**不以整目录 diff 为 `test_deploy_vault_sh.py` 的裁判**，而对该文件做**文件级单跑全绿**（T2-A 合入后由主 session 撤 `--ignore` 重取基线） | `test -f $BASE && grep -vc '^#' $BASE`（开工自证 = 64） |
| **本批纪律**：判据 grep git 输出一律 `--no-color` + 同次验伪锚；evidence `.txt` 不 `.log`（仓根 `.gitignore` 吞 `*.log`）；承重裁判末行 `rc=$pipestatus[1]`（zsh，`tee` 吞退出码）；ruff 判据用 zsh 数组写法；**批中禁装/升任何包**（不往共享 venv 装）；`fsrs_bridge.py` / `decay_beta.py` ⛔ 零写者（碰 = 触 live 部署铁律，停下报主 session）；live vault / 7691 / 7687 / 现网 LanceDB **只读**；**真 `up -d` 需用户当次授权，未授权 SKIP 并登记**。本卡**不触及 `backend/app`** ⇒ `python-typecheck`（glob `backend/app/*.py`）不触发；若 diff 出现 `backend/app` 文件 = 地盘越界，停下报主 session | 手册 §零 / 协议 §2.2 |

## 一 完成条件（AND）

- (a) **第 0 分钟**：`pwd` = `…/worktrees/card-t2-deploy`、`git branch --show-current` = `card/t2-deploy`、`git log --oneline -1` 含 T2-A 的 `CARD-DEPLOY-TIMEOUT`（前提 T2-A 已独立 commit）、`git status --porcelain | wc -l` → **0**；`test -e backend/.venv/bin/pytest && test -e backend/.env`。**开工基线自证**：`BASE=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/evidence-b14/unit-red-baseline-08100483.txt`；`test -f "$BASE" && grep -vc '^#' "$BASE"` → **64**（不是 64 或文件不在 ⇒ 停下报主 session）。⛔ **第二件事（承重，见 §〇 串行漂移行）**：T2-A 已改 `scripts/deploy-vault.sh` 步 1，步 5/6 行号已下移；逐条 `grep -nF` 重定位 §〇 的真 activate 桩 / 闸门 / `--also-push` / step6 所有锚，在验收单 §〇 核对段写「卡文 :X → T2-A tip 实测 :Y」（全部漂移都要写）；设计稿列出的口径更正①（`CLS_DEPLOY_ALLOW_DOCKER_UP` 非 `CLS_DEPLOY_NO_DOCKER_UP`）与语义替换（起/重建本实例、非切换回滚旧 vault）必须落进验收单 §〇。
- (b) **先红**（改前跑，必红且红在「功能不存在」断言，不是 import/桩错；tee `red-$TS.txt`）：在 `backend/tests/unit/test_deploy_vault_sh.py`（T2-A tip 上）新增测试，覆盖本卡五件新增能力，**每件至少一条改前必红的门**：① 真 activate 分阶段可审计日志（`CLS_DEPLOY_ALLOW_DOCKER_UP=1` + 桩 docker 成功 → STEP_MSG/journal 含分阶段 `rc=` 行）；② 健康断言失败只拆本实例（桩 curl 超时 → `cls-<vault>` 被 `down`，另一「已在跑实例」端口桩仍 200）；③ index journal 隔离；④ Lance 首索引计时含进度字段；⑤ Graphiti readiness 输出 `skipped-with-reason`（readiness 探测失败时）。改前这些门必红（功能未实现）。**桩 docker/curl 两态**：dry/桩态覆盖全部逻辑；真态仅用户授权后跑（见 (c)）。
- (c) **真 activate 事务化（把「写着没跑」变「跑过且有分阶段可审计日志」）**：只改 `step5_activate` 闸门**之后**那段（真起实例 → 健康断言 → 失败回滚）与 `step6_evidence` 的状态记账，使每阶段落 `rc=`（起实例 / health / 回滚各一行可审计）。语义**严格照 §〇**：激活 = 起/重建**本 vault 的** `cls-<vault>` 实例，**不顶别的 vault**。**真态（`CLS_DEPLOY_ALLOW_DOCKER_UP=1` + `--apply --activate` 真 `docker compose up -d`）需用户当次授权**：主 session 在用户当次显式授权后陪跑落证据；**未授权即 SKIP**（桩态全绿即可完成本卡），SKIP **不算失败**，但验收单段 4-A 必须标「**真 activate 未执行（用户未授权），仅桩态验证**」。⛔ 步 1~4 逻辑一行不改。
- (d) **失败回滚只拆本实例（承重，桩两态对照）**：注入 health 超时（桩 curl rc≠0）后，`cls-<vault>` 项目被 `down` 干净 **且** 另一个「已在跑实例」的端口（桩）仍 200；`down` 也失败时 STEP_MSG **不得**声称「已回滚」（Codex r1 HIGH-3 既有分叉，本卡钉住不得退化）；状态文件要么旧要么新，无半激活态。门断言消息写死「失败只拆 cls-<vault>，兄弟实例不受影响」。
- (e) **三段新增（grep 确证改前 0 命中）**：① **index journal 隔离** = G2-5 的 episode/index journal 命名空间化在部署期的落地（本 vault 的 journal 不与别的 vault 串）；② **Lance 首索引单独计时 + 进度**（阶段耗时 + 进度字段落 evidence）；③ **Graphiti 回填 readiness 校验 + 显式 `skipped-with-reason`** —— ⛔ **禁假成功**：readiness 探测不可达/失败时必须落 `skipped-with-reason=<原因>`，**不得**报 success。三段落点在 step 5/6；改前 `grep -niE 'journal|lance|graphiti|readiness|首索引|skipped-with-reason' scripts/deploy-vault.sh` = 0，改后对应字符串出现且由 (b) 的门覆盖。
- (f) **实现 `--also-push`**：`ALSO_PUSH=1` + `--apply` 时，把新 vault 名**追加进 harness（feature 主干树）的 daily-review vault 清单（`DAILY_REVIEW_VAULTS`）去重**、**不动 `ACTIVE_VAULT`**；harness 守卫（限 `harness == FEATURE_TREE`，否则 `die64`）**保留不动**；step6 的 `printf` 从 `also_push=%s(未实现,登记 G2-8)` 改为实现态文案 ⇒ `grep -cF '未实现,登记 G2-8' scripts/deploy-vault.sh` 从 **1 → 0**。去重 = 同 vault 名已在清单则不重复追加；`ACTIVE_VAULT` 行改前改后逐字节同（负控 (h)③ 钉住）。
- (g) **canvas-vault 名口径收口**：确认 step1_preflight 的不动点 preflight **正确拒连字符名**（`canvas-vault` 非 `sanitize_vault_id`/`vault_key` 共同不动点）；evidence 与验收单落定 G4 口径「**live `canvas-vault` 不经本脚本重建，新库须用下划线名**」；加一条测试钉住「连字符名被 preflight 拒（rc 64 或 STEP_MSG 含『不是…共同不动点』）」的现状。⛔ **步 1 只复用不重写逻辑**；若实测发现收口**必须改步 1 preflight 逻辑**，停下在验收单 notes 写明、报主 session 裁定，不自作主张扩面。
- (h) **负控输入（承重，各一段；EXIT trap 无条件还原 + 全文件 `shasum -a 256` 前后逐字同；⛔ 禁 `git stash`、禁 `git checkout` 还原，用 `git show HEAD:<path> > <tmp>` 比对）**：① **Graphiti readiness 假成功变异** = 把 (e)③ 的 `skipped-with-reason` 分支临时改成恒报 success → (b)⑤ 的门必红；② **`--also-push` 去重变异** = 去掉去重 → 重复 vault 名门必红；③ **`ACTIVE_VAULT` 被动变异** = 让 `--also-push` 误写 `ACTIVE_VAULT` → 「`ACTIVE_VAULT` 不变」门必红；④ **禁写面负控** = `shasum -a 256 scripts/cls_forbidden_paths.py` 开工/收工两行逐字同（本卡不碰禁写面）。每段只拆一层防线，失败正文含指定断言消息。
- (i) **既有不回退**：`bash -n scripts/deploy-vault.sh; echo rc=$?` → **0**；`test_second_tier_hosts_not_implemented_anywhere` 仍绿（本卡不碰宿主绑定件）；`backend/tests/unit/test_deploy_vault_sh.py` **文件级单跑全绿**（开工在 T2-A tip 跑一次记 passed 数，收工再跑对比）；`step6_evidence` 的 dry-run 零写守卫不破（`--apply` 未传时零落盘）。
- (j) **现网只读**：⛔ 禁写 live vault `/Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault/**`；禁连 7691/7687；`docker-compose*.yml` 只读（改动须登记）；除用户当次授权的真 activate 外，不真 `docker compose up -d`；新测试的 `docker`/`curl` 全走桩（PATH 注入，命名沿用 `fake_bin / "<bin>"`，见 §〇 与 §二 第 8 条的可翻转判据 + 验伪锚），贴进验收单；开工 `touch $EV/sentinel`、收工对现网 LanceDB 目录与 live vault `find <dir> -type f -newer $EV/sentinel | wc -l` → **0**。
- (k) **Codex**：顺序固定「代码与门全部定稿 → 跑全部裁判 → 送 Codex → 之后只改 `_bmad-output`」；**Codex gpt-6-astra ultra 多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0**（本卡有代码改动 ⇒ 多轮，上限 5 轮；第 5 轮仍有 HIGH 停下交主 session；审后再改代码必再送一轮；车道对 HIGH 的驳回写理由但不自判通过）；prompt 五分节 + 最小读取面写死；prompt 与存档不得出现协议 §2 的四个禁用措辞。
- (l) **提交**：单独 commit（T2-C 开工前工作树必须干净）；header ≤100 **含 `[BATCH-2026-09-11-第十四批 / CARD-G2-8]`**，body 行 ≤100（`wc -m` 计字符）；`*.stderr*` 不入库；**不 push**；每卡 commit 带卡号。
- (m) **「本卡未证明什么」必填**（≥4，见 §四）+ **「台账待登记条目」必填**（≥4，见 §四）。

## 二 裁判命令

> 一律在**车道树** `cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy` 下跑；`PYTEST=$(pwd)/backend/.venv/bin/pytest`；`EV=$(pwd)/_bmad-output/审查/evidence-g2-8`（绝对路径，承重裁判带 `cd backend` 时相对 `EV` 会落到不存在的 `backend/_bmad-output/…`）；`mkdir -p $EV`；承重裁判 `2>&1 | tee $EV/<name>-$(date +%Y%m%dT%H%M%S).txt; echo rc=$pipestatus[1]`（zsh；`.txt` 不 `.log`）。基线 `BASE` 见 (a)，在 **feature 主干树**绝对路径（车道树没有 `evidence-b14/`，写成 `$(pwd)/…` 会 No such file）。

```zsh
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy
PYTEST=$(pwd)/backend/.venv/bin/pytest
EV=$(pwd)/_bmad-output/审查/evidence-g2-8; mkdir -p "$EV"
BASE=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/evidence-b14/unit-red-baseline-08100483.txt

# 1. 第 0 分钟
git branch --show-current            # card/t2-deploy
git log --oneline -1                 # 含 CARD-DEPLOY-TIMEOUT（T2-A）
git status --porcelain | wc -l       # 0
test -f "$BASE" && grep -vc '^#' "$BASE"   # 64
# 串行漂移重定位（承重；行号以此输出为准，写进验收单「卡文:X→实测:Y」）
grep -nF 'CLS_DEPLOY_ALLOW_DOCKER_UP' scripts/deploy-vault.sh
grep -nE 'up -d backend|curl .*-m |compose .*down|-p "cls-' scripts/deploy-vault.sh
grep -nF '未实现,登记 G2-8' scripts/deploy-vault.sh        # 改前 1
git diff --stat 08100483 HEAD -- scripts/deploy-vault.sh   # 非空（T2-A 改过步 1）

# 2. 三段新增改前 0 命中（先红的静态前置）
grep -niEc 'journal|lance|graphiti|readiness|首索引|skipped-with-reason' scripts/deploy-vault.sh  # 改前 0

# 3. 先红（改前跑新门，必红在「功能不存在」断言）
cd backend && $PYTEST -q -p no:cacheprovider tests/unit/test_deploy_vault_sh.py -k "g2_8 or activate_tx or readiness or also_push or journal or first_index" 2>&1 | tee "$EV/red-$(date +%Y%m%dT%H%M%S).txt"; echo rc=$pipestatus[1]

# 4.（实现后）文件级单跑全绿 + bash -n + also-push 文案翻转
cd .. && bash -n scripts/deploy-vault.sh; echo rc=$?
grep -cF '未实现,登记 G2-8' scripts/deploy-vault.sh        # 收工 0
cd backend && $PYTEST -q -p no:cacheprovider tests/unit/test_deploy_vault_sh.py 2>&1 | tee "$EV/unit-deploy-close-$(date +%Y%m%dT%H%M%S).txt"; echo rc=$pipestatus[1]

# 5. 既有门不触红
cd .. && grep -nF 'test_second_tier_hosts_not_implemented_anywhere' backend/tests/unit/test_deploy_vault_sh.py
cd backend && $PYTEST -q -p no:cacheprovider "tests/unit/test_deploy_vault_sh.py::test_second_tier_hosts_not_implemented_anywhere"; echo rc=$?

# 6. 负控四段（每段 EXIT trap 还原 + 前后 shasum 逐字同；下面是骨架，正文断言见 (h)）
cd ..
for seg in readiness-fakesuccess alsopush-nodedup active-vault-mutated; do
  B=$(shasum -a 256 scripts/deploy-vault.sh | cut -d' ' -f1)
  # …按 (h) 对应变异改 scripts/deploy-vault.sh，跑对应门必红，tee "$EV/negctl-$seg-<ts>.txt"…
  git show HEAD:scripts/deploy-vault.sh > /tmp/t2b-restore.sh && cp /tmp/t2b-restore.sh scripts/deploy-vault.sh
  A=$(shasum -a 256 scripts/deploy-vault.sh | cut -d' ' -f1); echo "$seg $B $A"   # B==A
done
shasum -a 256 scripts/cls_forbidden_paths.py   # 禁写面负控：开工/收工同行

# 7. 地盘门（只列允许面；验伪锚：去掉 exclude 应多出 _bmad-output/ 路径）
git diff --stat --no-color <前提 T2-A commit SHA> HEAD -- . ':(exclude)_bmad-output'
#   期望 ⊆ { scripts/deploy-vault.sh, backend/tests/unit/test_deploy_vault_sh.py }

# 8. 现网只读哨兵（(j)）
touch "$EV/sentinel"   # 开工
# 新测试走桩（⚠️ 可翻转判据：本文件 2596 行里 `stub` 字样 **0** 命中、`fake` 67 命中，既有桩命名一律
#   `fake_bin / "<bin>"` + PATH 注入 ⇒ 旧写法 `| grep -i stub` 恒空 = 证明不了任何事，已替换）
grep -cE 'fake_bin */ *"(docker|curl)"' backend/tests/unit/test_deploy_vault_sh.py   # 改前 0 → 收工 ≥2
grep -nE 'fake_bin */ *"lsof"' backend/tests/unit/test_deploy_vault_sh.py            # 验伪锚: 同次必非空（既有 fake_lsof :2228/:2256）
find /Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault -type f -newer "$EV/sentinel" | wc -l   # 收工 0

# 9. Codex 后绑定核
git diff --stat --no-color <审SHA> HEAD -- . ':(exclude)_bmad-output'   # 空即仍绑定
```

- 地盘门第 7 条的 `<前提 T2-A commit SHA>` = T2-A 独立 commit 的 SHA（开工 `git log` 取）；验伪锚必跑（去掉 `':(exclude)_bmad-output'` 必多出 `_bmad-output/` 路径，证明 grep/pathspec 真在过滤）。
- 真 activate 若获用户授权，真态单跑另落 `$EV/activate-real-<ts>.txt` 末行 `rc=`，由主 session 陪跑；未授权则此档缺席，验收单标「真 activate 未执行」。

## 三 禁改与隔离

- **本卡地盘（只允许改这两个文件）**：
  - `scripts/deploy-vault.sh` —— 只改 `step5_activate` 闸门**之后**那段（真起实例 / 健康断言 / 失败回滚的记账）+ `step6_evidence` 的状态/参数行（`--also-push` 文案翻转）+ `--also-push` 实现（`DAILY_REVIEW_VAULTS` 追加去重）。
  - `backend/tests/unit/test_deploy_vault_sh.py` —— 新增本卡五件能力 + 名口径 + 负控的门（桩 docker/curl）。
- **禁改面**：
  - `scripts/deploy-vault.sh` 的**步 1~4 逻辑**（`step1_preflight`/`step2_install`/`step3_postprocess`/`step4_verify`，G2-7b 交付面，只复用不重写；含 canvas-vault 名不动点 preflight —— (g) 收口是文档/决策 + 钉现状，不改其逻辑）；`--also-push` 的 harness 守卫（限 `FEATURE_TREE`，保留）。
  - `scripts/cls_forbidden_paths.py`（禁写面判定本体，负控 (h)④ 钉 sha 不变）、`scripts/vault-install-manifest.json`、`.claude/skills/deploy-vault/SKILL.md`（仓根真名，R-B14-8；本卡只读；`--hosts` 文案同步归口 T2-C，见台账）、`backend/tests/unit/test_docker_compose_config.py`、`docker-compose*.yml`（只读核，改动须登记）。
  - 步 3 的**宿主绑定件**（`AGENTS.md` / `.agents/skills` / `.codex/*` / `opencode.json*` / `.dsh/*`）—— **T2-C/T2-D 面**；本卡一个字不碰（否则 `test_second_tier_hosts_not_implemented_anywhere` 变红）。
  - `backend/app/**` 零文件（本卡不触及 → `python-typecheck` 不触发；若 diff 出现 = 越界，停下报主 session）；`backend/app/models/**` 零写者。
- **硬边界**：⛔ 禁写 live vault `/Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault/**`；⛔ 禁连 Neo4j 7691 / 7687；⛔ 禁碰 `canvas-vault/.claude/scripts/fsrs_bridge.py` / `decay_beta.py`（本卡零关联，`grep -rn -e 'fsrs_bridge' -e 'decay_beta' scripts/deploy-vault.sh backend/tests/unit/test_deploy_vault_sh.py` 应 0 命中（B14_BASE 实测 0；原 BRE 写法在本机 BSD grep / ugrep 下确为交替、非假阴性，2026-09-14 仅为统一改 `-e`））；⛔ 现网 LanceDB 目录只读；⛔ **真 `docker compose up -d` 仅在用户当次显式授权后、由主 session 陪跑**，未授权即 SKIP 并登记；⛔ 禁改 `ACTIVE_VAULT`（`--also-push` 只追加 `DAILY_REVIEW_VAULTS`）；⛔ 禁 `git stash`；不改台账（台账只主 session 改，卡在验收单写「台账待登记条目」）；不 push；`*.stderr*` 不入库；`.log` 后缀不用；批中禁装/升任何包。

## 四 Codex / 验收单

**命令**（协议 §2）：
```zsh
codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" \
  "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G2-8[-rN].md)" \
  > _bmad-output/审查/codex-review-CARD-G2-8[-rN].md \
  2> _bmad-output/审查/codex-review-CARD-G2-8[-rN].stderr </dev/null
```
**轮次**：**Codex gpt-6-astra ultra 多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0**（本卡有代码改动 ⇒ 多轮，上限 5 轮；第 5 轮仍有 HIGH 停下交主 session；审后再改代码必再送一轮；0 字节存档重发一次，再 0 字节 → 主 session 人审）。模型固定 `gpt-6-astra` + `ultra`（协议 §2；禁任何旧复核模型名）。

**prompt 五分节**：
1. **背景**：G2-8 包裹 `deploy-vault.sh` 步 5/6 —— 真 activate 事务化（起/重建本 vault `cls-<vault>` 实例，不顶别的 vault）、失败只拆本实例、三段新增（index journal 隔离 / Lance 首索引计时 / Graphiti readiness `skipped-with-reason`）、实现 `--also-push`（追加 `DAILY_REVIEW_VAULTS` 去重、不动 `ACTIVE_VAULT`）、收 canvas-vault 名口径缺口。
2. **最小读取面写死**：`git diff <前提 T2-A SHA> <审SHA> -- . ':(exclude)_bmad-output'` + `scripts/deploy-vault.sh` 的 `step5_activate` / `step6_evidence` / `--also-push` 实现段（以审 SHA 实测范围）+ `backend/tests/unit/test_deploy_vault_sh.py` 新增门全文 + UAT-CARD-G2-7b-2026-09-09.md §3.1/§3.2。
3. **作者自述请独立核对**：① 失败回滚**只**拆 `cls-<vault>`、兄弟实例端口仍 200（桩态证据是否覆盖「另一实例存活」这一断言）；② Graphiti readiness 在探测失败时是否**恒**落 `skipped-with-reason`（有没有某条路径仍悄悄报 success）；③ `--also-push` 去重是否真去重、`ACTIVE_VAULT` 是否逐字节不变；④ 真 activate 未授权走 SKIP 时是否被如实标记、SKIP 不被当成功；⑤ 步 1~4 是否一行未改（名口径收口是否误动了 preflight 逻辑）。
4. **按重要性排序的问题**（BLOCKER/HIGH/MEDIUM/LOW + file:line + 一句复现思路；复现思路只描述**负控输入 / 对照输入 / 门未覆盖的路径**，不得出现协议 §2 的四个禁用措辞）。
5. **边界**：只读、不连 docker/7691、不评真 activate 的真态（未授权未跑）、不评步 1~4 既有逻辑、不评 T2-A 的超时改动。

**存档首部**（协议 §2.1，本批改为「抄含版本行 + model 行 + reasoning 行」）：每份 `codex-review-CARD-G2-8[-rN].md` 首部 blockquote 必含——批次/车道/卡 round；`模型: gpt-6-astra · reasoning_effort: ultra · codex: <codex --version 实测值>`；命令行；审查绑定 SHA（HEAD 若不同须如实写）；**会话头自证**抄 `.stderr` 中含 codex 版本行 + model 行 + reasoning 行的三行（**不假定其为前三行、行号不限**——codex 版本/model/reasoning 行不保证落在前三行，**各写明其在 `.stderr` 的行号**；`.stderr` 本身不入库）。缺 `模型 / reasoning_effort / codex` 任一字段该轮不计配额。

**验收单** `_bmad-output/验收单/UAT-CARD-G2-8-<日期>.md`（DoD-3 双段）：
- 段 4-A「🤖 Claude 已代验」（技术 assert 全归此段，带证据）：桩态真 activate 分阶段 `rc=` 日志、失败只拆本实例 + 兄弟实例 200、三段新增门、`--also-push` 去重 + `ACTIVE_VAULT` 不变、名口径钉现状、四段负控、文件级单跑全绿、地盘门、bash -n、**真 activate 是否授权执行（未授权写「真 activate 未执行，仅桩态」）**。
- 段 4-B「👤 你来验」（零技术词，「我做 X → 我看到 Y → 我感觉 Z」+ felt-sense）：一句「我给一门新课做一键上线，它自己起一套后台；万一这次没起成功，它只把这门课的后台收回去，我另一门课正在用的东西**一点没受影响**——我感觉可以放心给每门课各来一套，互不打架」。
- **本卡未证明什么（≥4）**：① 未证明真 activate 真态（用户未授权 ⇒ 真 `docker compose up -d`/health/回滚只在桩态验证，真 docker daemon 行为未跑）；② 未证明多实例端口真并发时的抢占/残留（桩态下「兄弟实例 200」是桩返回，非真容器）；③ 未证明 Graphiti 回填在真 7691 上的 readiness 时序（只读，未连库）；④ 未证明 Lance 首索引计时在真 bge-m3 + 真库下的量级（桩态计时）；⑤ 未证明 canvas-vault 名缺口的 G4 侧最终处置（本卡只钉现状 + 落口径，改库名规则属 G4）；⑥ 未证明 `--also-push` 对 daily-review 调度链（现网 `DAILY_REVIEW_VAULTS` 消费方）的端到端影响（只改写点、未跑调度）。
- **台账待登记条目（≥4）**：① G2-8 交付 = 真 activate 事务化 + 三段新增 + `--also-push` 实现的 commit SHA + 门 nodeid；② `--also-push` 从「只解析不实现」转「实现」的行为变化（`未实现,登记 G2-8` 字符串 1→0）；③ 真 activate 真态**未授权未跑**、SKIP 登记（授权执行则补登证据路径）；④ canvas-vault 名口径缺口收口 = 文档/决策落定 + 钉现状测试，G4 侧改库名规则移交；⑤ 串行行号漂移（T2-A tip 上步 5/6 的「卡文 :X → 实测 :Y」对照表）；⑥ Codex 各轮存档路径 / 绑定 SHA / B·H·M·L 计数；⑦ `test_deploy_vault_sh.py` 文件级单跑 passed 数（开工/收工对比），及「基线带 `--ignore` 本文件、T2-A 合入后主 session 撤 `--ignore` 重取」的交接。

commit header ≤100 含批次标记；不 push；**独立 commit 后同车道继续 T2-C**；跑完说「**复核第十四批 T2**」。
