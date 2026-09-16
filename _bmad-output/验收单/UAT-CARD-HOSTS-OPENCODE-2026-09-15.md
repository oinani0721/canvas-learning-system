# UAT — CARD-HOSTS-OPENCODE（`deploy-vault.sh --hosts opencode`）

> 批次 `[BATCH-2026-09-11-第十四批 / CARD-HOSTS-OPENCODE]` · 车道 `card-t2-deploy`（分支 `card/t2-deploy`，本车道第 3/5 张）
> PREV（T2-B tip，地盘核基准）= `7e1d6b53bab9abd9b26711bc2c60724d3afb496f`
> 证据目录 `_bmad-output/审查/evidence-hosts-opencode/`（全部 `.txt`；`*.stderr*` 不入库）
> 日期 2026-09-15（机器本地时区，D-18）

---

## 〇 第 0 分钟核 + 卡文事实校正

| 项 | 实测 |
|---|---|
| `pwd` | `…/worktrees/card-t2-deploy` ✅ |
| `git branch --show-current` | `card/t2-deploy` ✅ |
| 前提：T2-B 已独立 commit | `git log --oneline -1` = `7e1d6b53 docs(deploy): CARD-G2-8 验收单定稿…` 含 `CARD-G2-8` ✅ |
| 前提：树干净 | session 起始 `git status --porcelain` **空** ✅（随后唯一一条 `??` 是本会话 `mkdir` 的 evidence 目录） |
| venv / env | `backend/.venv/bin/pytest` 在、`backend/.env` 在 ✅ |
| 开工基线自证 | `grep -vc '^#' <feature 主干树>/evidence-b14/unit-red-baseline-08100483.txt` = **64** ✅ |
| 运行期 skill 清单（软链目标池，实测不写死） | `ls -1 canvas-vault/.claude/skills/` = **11** 条：`ai-linked-doc board-recap board-split chat-with-context clear-inbox configure-whiteboard exam-quick node-chat quiz-answer start-exam-board study-question` |
| deploy-vault SKILL.md 真名（R-B14-8） | `find . -name SKILL.md -path '*deploy-vault*'` 唯一命中 `./.claude/skills/deploy-vault/SKILL.md`（第 0 分钟 **75** 行；本卡改后 **79** 行 —— 这一栏记的是开工态，别拿它当收工数）✅ |

### ⚠️ 卡文 §〇 行号全面漂移（卡文 :X → 实测 :Y）

卡文 §〇 的行号是**写卡时在切点 `08100483` 主干上实测**的；本车道 T2-A / T2-B 两卡已先后改过
`scripts/deploy-vault.sh`（`wc -l` 卡文 **1238** → 实测 **1775**）。按卡文 (a) 要求逐条重取，
**判据方向一律不因行号漂移而改**：

| 锚 | 卡文 | 改前实测 | 取法 |
|---|---|---|---|
| `HOSTS="claude"` 缺省 | `:81` | `:127` | `grep -nE '^HOSTS='` |
| `APPLY=0` | `:83` | `:129` | `grep -nE '^APPLY='` |
| `--apply) APPLY=1` | `:242` | `:290` | 同上 |
| `MODE="dry-run"` / `="apply"` | `:367-368` | `:415-416` | `grep -nE 'MODE="'` |
| `--hosts` 切分校验块 | `:273-290` | `:315-338` | `grep -n '_rest'` |
| `if [ "$_h" != "claude" ]` | `:284` | `:332` | 同块内 |
| E-1 printf 二线名单 | `:286` | `:334` | `grep -nF 'E-1'` |
| `exit 64` | `:287` | `:335` | 同块内 |
| 头注 rc 表「`--hosts` 含二线宿主」 | `:16` | `:19` | `grep -nE '^#.*rc 64'` |
| 头注 `--hosts` 行 | `:28` | `:31` | `grep -nE '^#.*--hosts'` |
| 头注 `--apply`「零写」行 | `:30` | `:33` | 同上 |
| `step3_postprocess` | `:684` | `:921` | `grep -nE '^step3_postprocess'` |
| 步 3 dry 分支 `return 2` | `:687-690` | `:924-927` | 同函数内 |
| A1 宿主绑定件在位判 | `:697-701` | `:934-938` | 同函数内 |
| `cls_forbidden_paths.py` `build_targets` | `:265` | `:265` ✅ 未漂 | — |
| `~/.config/opencode` 入 targets | `:270` | **`:270` ✅ 未漂** | `grep -nF 'os.path.join(home, ".config", "opencode")`，**唯一命中** |
| `under()` | `:231-242` | `:231-242` ✅ 未漂 | — |
| `test_second_tier_hosts_rejected_with_e1` | `:164` | `:177` | `grep -nE '^def test_'` |
| `test_second_tier_hosts_not_implemented_anywhere` | `:851` | `:867` | 同上 |
| manifest `.claude/skills` item | `:65` | `:65` ✅ 未漂 | — |
| manifest `grep -cF 'AGENTS' / '.agents' / 'opencode'` | 各 0 | 各 **0** ✅ | 与卡文一致 |

> ⚠️ `scripts/cls_forbidden_paths.py`（609 行）与 `scripts/vault-install-manifest.json`（391 行）
> 本车道前两卡未碰，故行号与卡文一致。本卡给 `cls_forbidden_paths.py` 加的注释**一律加在 `:270` 下方**，
> `:270` 因此没有被推走；负控仍按内容 `grep -nF` 重取并断言唯一命中（见 §四）。

---

## 一 完成条件逐条

### (b) 先红（改前）

| 红 | 结果 | 存档 |
|---|---|---|
| ① `--hosts claude,opencode`（真 CLI，dry） | **rc 64**，正文含 `E-1` | `red-e1-20260915T115021.txt` |
| ② 新门 `test_hosts_opencode_generates_binding_files` | **FAILED**，红因 = `assert 64 == 0`（opencode 被 E-1 拒） | `red-newgates-20260915T115208.txt` |
| ② 同批 `test_hosts_opencode_dry_run_writes_nothing` | **FAILED**，红因同上 | 同上 |

> 红因均为「opencode 被 E-1 拒」，**不是** import / 夹具错。
> 同批的 3 条 D-26(i) / 零写者门改前即 **PASSED** —— 它们是**补覆盖面**（此前零断言），不是 feature 红。

### (c) 实现

> ⚠️ 本表记的是**最终态**（HEAD）。`publish_agents_md` 经过三轮整改换过两次机制，
> 中间形态与被换掉的理由见 §六.1 —— 那段演进本身是本卡最值钱的部分，不要只看结论。

| 面 | 改动 |
|---|---|
| `scripts/deploy-vault.sh` 头注 | rc 表「含二线宿主」→「含未实现宿主」；`--hosts` 行改写为「支持 claude / opencode（逗号分隔，可并存）」+ 4 行说明生成物与「对 `~/.config` 零写者」。`usage()` 动态取头注 ⇒ `--help` 自动同步 |
| `--hosts` 解析 | 新增 `HOST_CLAUDE` / `HOST_OPENCODE` 两个开关（单一来源 = 切分循环）；`if != claude` 改 `case`，`claude` / `opencode` 各置位，其余仍 `exit 64`；**E-1 文案去掉 `opencode`**（留 `codex / dsh 等`，DD-13 名实一致） |
| 步 1 `PENDING_WRITES` | `HOST_OPENCODE=1` 时条件 append **2 项**（`.agents/skills` 根 / `AGENTS.md`）。⛔ 进的是**同一份清单**，不另开判据。⚠️ 初版还有第 3 项 `AGENTS.md.tmp`，随 r3 整改去掉 tmp 机制一并退场 —— 写面清单只登记真正会被写的对象 |
| 步 3 dry 分支 | `will:` 追加「生成 opencode 绑定件 …」；**零写不变** |
| 步 3 Phase B **B4b** | `HOST_OPENCODE=1` 时调 `write_opencode_binding`。⚠️ 放在 **B5 之前**，保住「key 文件落盘是 Phase B 最后一步」那条既有不变量 |
| 新 `write_opencode_binding()` | 枚举 `$VAULT/.claude/skills/*/` → 每个叶子落点先过 `check_forbidden_paths --outputs`（与步 4 源镜像 `MIRROR_WRITES` 同律）→ `ln -s ../../.claude/skills/<n>`；已在位且指向相同则幂等跳过，指向别处 / 非软链一律 fail-closed 不覆盖；末尾**生成后就地在位判** |
| 新 `write_agents_md()` | 只负责把正文写 **stdout**（生成标记 + 技能清单 + 完整 MCP 端点接线指引），落盘交给 `publish_agents_md` |
| 新 `publish_agents_md()` | **最终态**：直接以 `O_CREAT\|O_EXCL\|O_NOFOLLOW` 建目标本身并写入，全程持有同一个 fd；目标已存在**一律拒绝**并说清它是什么；写完核 fd 侧 / 路径侧身份（各自 `nlink==1` + 同 inode）；失败时按身份清理**自己建的**那个，身份对不上就原样留下并报告。⚠️ 这个形态是三轮 Codex 逼出来的，演进与理由见 §六.1 |
| `vault-install-manifest.json` | 新增 `.agents/skills` + `AGENTS.md` 两 item（`action: generate`、`role: opencode-binding`、`optional: true`、`note` 注明 hosts 条件）；description 追加 **origin 约定破例**说明 |
| `cls_forbidden_paths.py` | `:270` **下方**加注释点名 `opencode.jsonc` / `.gitignore` + 承重声明 + 回归断言指路 + 「别把新目标插在这一行上面」告警。⛔ `build_targets` / `under` / `chain_resolvable` 的既有逻辑一字未动 |
| `.claude/skills/deploy-vault/SKILL.md`（可选地盘，**做了**） | `--hosts` 文案同步：支持 claude / opencode，说明两件生成物与「不跑模型、不碰 `~/.config`」 |

### (d) 后绿 + 静态判据

| 判据 | 结果 | 存档 |
|---|---|---|
| ① 真 CLI `--hosts claude,opencode`（dry） | **rc 0**（⚠️ 见下「端口环境因」） | `green-dry-hosts-20260915T115422.txt` |
| ① `--apply` 对 tmp vault | **rc 0** | `judge3-apply-artifacts-20260915T115438.txt` |
| 条目级软链 `test -L` + `readlink` | 3/3 `-L=yes`，`readlink` 全 = `../../.claude/skills/<n>`，`realpath` 全落在 `$VAULT/.claude/skills/<n>` 且存在 | 同上 |
| **条目级不是整目录级** | `.agents/skills -L = NO`、`.agents -L = NO` | 同上 |
| ② frontmatter `name` == 条目名（SKILL-PORT-LINT 层 1 口径） | 3/3 `name: <条目名>`，且过 `^[a-z0-9]+(-[a-z0-9]+)*$` | 同上 |
| `AGENTS.md` 在位且含技能清单 | 1296 字节，3 条技能全列出，首行带生成标记 | 同上（含全文） |
| ③ dry 零写 | `find $TMP -name '.agents'` = 0、`-name 'AGENTS.md'` = 0、`find $TMP \| wc -l` = **1**（只有 TMP 自身） | `green-dry-hosts-…` / `judge-g-claude-only-regression-…` |
| ④ `test_deploy_vault_sh.py` 文件级 | **201 passed / 9 skipped / 0 failed**（153s） | `judge6-filelevel-20260915T120035.txt` |
| 不跑 OpenCode 模型 | 全程零 provider 调用（见「本卡未证明什么」①） | — |

> ⚠️ **端口环境因（卡文裁判 2 的 rc 71 口径）**：本机现网 docker 栈**实测占用 8011**
> （`lsof -nP -iTCP:8011 -sTCP:LISTEN` → `com.docke 80419 … (LISTEN)`）。
> 若按缺省端口跑，步 1 preflight 会因端口被占落 **rc 71**，而 rc 71 **不算通过**。
> 处置：换 `--port 8099`（实测空闲，且避开 7691 / 7692 / 7478 / 11434）复跑到 **rc 0**。
> 未腾开 8011（那是现网栈，本卡硬边界「现网只读」）。

### (e) D-26(i) 覆盖断言 + 负控 + 用户级 sha

见 §四。

### (f) 地盘核

见 §三。⚠️ **实测 6 文件，超卡文清单的 5 项** —— 处置与裁决见 §三。

### (g) 既有套件不回退

| 判据 | 结果 | 存档 |
|---|---|---|
| `test_deploy_vault_sh.py` 文件级 0 failed | ✅ 201 passed | `judge6-filelevel-20260915T120035.txt` |
| 更新后 E-1 门对 `codex` / `dsh` / `claude,codex` 仍 rc 64 | ✅（参数表内 3 条全绿） | 同上 |
| 更新后禁件门对 `.codex/config.toml` / `opencode.json` / `.dsh/` 仍拦 | ✅ | 同上 |
| **`--hosts claude` 单宿主与 T2-B 态逐字同行为** | 两版输出 `diff` **rc 0（空）**；验伪锚：同两版跑 `--hosts claude,opencode` 有差（prev rc 64 / head rc 0，`diff` rc 1）⇒ diff 不是恒空 | `judge-g-claude-only-regression-20260915T120403.txt` |
| `bash -n scripts/deploy-vault.sh` | rc 0 | `judge6-opencodejson-20260915T115522.txt` |
| `ruff check` / `ruff format --check`（本卡 diff 文件） | 全过；验伪锚（喂刻意错排文件）rc 1 ⇒ 不是恒绿 | `judge-ruff-20260915T120501.txt` |

### (h) tests/unit 目录级

见 §五。

---

## 二 裁判 6：非注释行 `opencode.json` 子串约束

存档 `judge6-opencodejson-20260915T115522.txt`：

```
非注释行命中数 = 0          ← 主判据
含注释在内的全部命中数 = 2   ← 对照：证明过滤器真在滤注释，不是「文件里根本没有」
验伪锚（正确过滤器）= 1      ← 非注释行留得住
反面验伪锚（错写法 grep -v '^\s*#'）= 2  ← 卡文点名的空操作，实证复现
```

实现方式：`OPENCODE_CFG_EXT="jsonc"` + 运行期拼接 `"opencode.$OPENCODE_CFG_EXT"`。
源码里出现的字面串是 `opencode.$OPENCODE_CFG_EXT`，不含 `opencode.json`。
理由写在该常量上方的注释里（既有门对**非注释行**做 substring 匹配，禁件清单含 `opencode.json`，
而实际文件名 `opencode.jsonc` 是它的超串）。

---

## 三 地盘核

```
git --no-pager diff --stat --no-color 7e1d6b53… HEAD -- . ':(exclude)_bmad-output'
```

（结果见 §六「收工核验」段。）

### ⚠️ 地盘从 5 文件扩到 6 —— 卡文未预见，已报主 session 并获裁决

卡文 §三 列的地盘是 5 个文件。实测 `scripts/vault-install-manifest.json` 加两 item 后，
**`backend/tests/unit/test_vault_install_manifest.py` 必红 3 条**（目录级 diff 出现 3 行 `>`）：

| 门 | 红因 | 性质 |
|---|---|---|
| `test_declared_paths_has_a_single_source_of_truth` | `len(declared_paths) == 35` → 实测 37；集合差断言少 2 项 | 手抄常量，需登记 |
| `test_manifest_covers_implicit_and_generated_semantics` | `generated == [5 项]` → 实测 7 项；`gen_opt == 4` → 实测 6 | 手抄常量，需登记 |
| `test_generate_section_covers_exactly_the_generate_items` | 「脚本生成段与 manifest generate 集漂移：脚本漏了 `['.agents/skills','AGENTS.md']`」 | **语义归属**问题 |

第 3 条不是手抄清单问题：它把 manifest 的 `generate` 集与 **install-vault.sh 生成段**的 `rm`
操作数做精确比对，并已备有 `OUTSOURCED` 集合表达「归属在别处」的 generate 项 ——
先例 `.obsidian/cls-internal-key.txt` 正是**由 deploy-vault.sh 生成、install-vault.sh 不清不生成**，
与本卡两件同一类。

进一步实测出的**约定破例**：全部既有 `generate` 项的 `origin` 都写成 `install-vault.sh:<行号>`
（连 `cls-internal-key.txt` 都借了 install-vault.sh `:194` 的自检反向判做锚）。本卡两件在
install-vault.sh 里**没有任何锚行**（该脚本完全不知道 opencode），故 origin 只能写
`deploy-vault.sh step3 B4b (CARD-HOSTS-OPENCODE)` —— manifest 因此不再是 install-vault.sh 的
**纯**投影。这一点已写进 manifest 顶部 `description`，不藏。

**裁决（主 session，2026-09-15）**：扩面改配套测试，地盘 5 → 6 文件。
改动全部是**登记性常量**（`==35`→`==37`、集合差 +2、`generated` 列表 +2、`gen_opt` `==4`→`==6`、
`OUTSOURCED` +2），**零逻辑改动**；门的「逼人登记」立意完整保留。

> ⛔ 明确拒绝的两个「更省事」做法（登记在此以免后人重走）：
> 1. 把 manifest 两 item 的 `action` 改成不触发门的值 —— 语义错，且 `declared_paths` 对
>    `copy`/`skeleton`/`generate` 一视同仁，换哪个都照红；
> 2. 把 `PENDING_WRITES+=(...)` 挪出 `test_g2_8_activate_tx_opens_no_new_write_surface` 的
>    文本取名面 —— 运行期行为一模一样而门当场变绿，那不是修好，是**把门弄瞎**。
>    已在该门 docstring 里加了反向断言 `assert "PENDING_WRITES+=(" in block` 钉死这一点。

---

## 四 D-26(i) 覆盖面 + 负控（承重）

### ① 显式断言（存档 `judge4a-d26i-hit-20260915T115533.txt`）

两种口径都拒，rc 均 1：

```
strict  : HIT o1 /Users/Heishing/.config/opencode（mkdir -p 会创建的中间段 …）
          HIT o2 /Users/Heishing/.config/opencode（…）           rc=1
--outputs: HIT o1 … / HIT o2 …                                   rc=1
```

命中理由指向的是**目录**而不是文件名 ⇒ 实证「运行期口径是整目录保护，不按文件名枚举」。

### 验伪锚（**另起一跑**，存档 `judge4a-d26i-falsify-20260915T115533.txt`）

```
OK ok    rc=0
```

⛔ 不得塞进上一跑：`main()` 对全部 item 累加 `bad` 后 `return 1 if bad else 0`（实测 `:560-606`），
同跑 rc **恒 1**，锚会恒假。

### ② 负控（存档 `d26i-negctl-20260915T115545.txt`）

```
跑前 sha      = 392ae1e8…
按内容取行号   = [270]，命中条数 = 1（唯一命中，才允许删）
被删原文      = raw.append(os.path.join(home, ".config", "opencode"))
删后重跑      = OK o1 / OK o2     rc=0      ← 从拒变放行 ⇒ 该行承重 ✅
同跑验伪      = HIT c1 ~/.codex   rc=1      ← 判据本身没坏，不是「整体失效」
还原后 sha    = 392ae1e8…（与跑前逐字相同）✅
还原后命中数   = 1 ✅
```

⛔ 还原基准用的是**变异前的工作树副本**，不是 `git show HEAD:…` —— 本卡已给同一文件加过注释，
用 HEAD 还原会把本卡改动一起抹掉。禁 `git stash` / `git checkout` 已遵守。
卡文 `:270` → 实测 `:270`（未漂，因注释加在下方）。

### ③ 跑前跑后用户级配置 sha（存档 `judge4c-userconfig-sha-20260915T115556.txt`）

被观测的那一跑 = `--hosts claude,opencode --apply`（tmp vault）。

| 文件 | 跑前 | 跑后 |
|---|---|---|
| `~/.codex/config.toml` | `94aae2fc…` | `94aae2fc…` ✅ |
| `~/.config/opencode/opencode.jsonc` | `4e901f9e…` | `4e901f9e…` ✅ |
| `~/.config/opencode/.gitignore` | `663a068e…` | `663a068e…` ✅ |
| `~/.config/opencode/` 目录列表 | `. .. .gitignore opencode.jsonc` | 同 ✅ |

前后两段逐行 `diff` **为空**。
(i) sentinel：`find ~/.config/opencode -type f -newer $EV/sentinel \| wc -l` = **0** ✅

> 💡 **顺带实证了 D-26(i) 的文档缺陷**：`~/.config/opencode/` 实际只有 `opencode.jsonc` 与
> `.gitignore` 两个文件，**决策文档 D-26(i) 枚举的 `opencode.json` 根本不存在**。
> 运行期（整目录保护）没漏，漏的是文档枚举 —— 文档侧更正是移交项（见 §七）。

---

## 五 tests/unit 目录级

跑法与基线文件头记录的**逐字一致**（`cd backend` + `--ignore` 写**相对路径**，R-B14-3；
写成 `backend/tests/…` 是空操作，那份重型文件仍会被收集并真跑）：

```
cd backend && PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/unit \
    --ignore tests/unit/test_deploy_vault_sh.py -q -p no:cacheprovider
```

| 跑 | 汇总 | nodeid 集合 | 对基线 diff |
|---|---|---|---|
| 首跑 `unit-close-20260915T120517.txt` | 38 failed / 5074 passed / 29 errors（581s） | 67 | **3 行 `>`** ← manifest 两 item 引出的 3 条（见 §三） |
| **终跑** `unit-close-final-20260915T234347.txt` | 35 failed / 5077 passed / 29 errors（646s） | **64** | **完全为空**（`diff` rc 0，零 `>` 零 `<`）✅ |

**验伪锚**：拿首跑那份 nodeid 集合与同一基线比，`grep -c '^>'` = **3** ⇒ 该 diff 判据不是恒空。

> ⚠️ 判据里只出现 `$RUN` 与 `$BASE` 两个**固定文件名变量**，禁 glob（≥2 份 `*.txt` 时 grep 会加
> 文件名前缀，作废 nodeid 集）。未用 `wc -l` 当判据。
> `tests/unit/test_vault_doc_roles.py::test_live_vault_enforce_clean` 那条红**在基线里就有**
> （主干既有），且它测的是 `backend/scripts/vault_doc_roles.yaml`，与本卡 manifest 的 `role` 字段无关。

**另跑文件级**（两份被本卡碰过的测试文件）：
`judge-filelevel-final-20260915T235740.txt` → **376 passed / 9 skipped / 0 failed**（249s）✅

---

## 六 收工核验

**代码 commit** = `836b1b7d`（`feat(deploy): --hosts opencode 生成静态绑定件 [BATCH-2026-09-11-第十四批 / CARD-HOSTS-OPENCODE]`）
header `wc -m` = **84**（限 100），含批次标记与卡号；body 无超 100 字符行。
lefthook 全绿（`commitlint` ✔ / `spec-reference` ✔；`backend/app/**` 系的 4 个 job 不触发）。

### 裁判 5 地盘核（存档 `judge5-territory-20260916T001019.txt`）

```
git --no-pager diff --stat --no-color 7e1d6b53… 836b1b7d -- . ':(exclude)_bmad-output'
 .claude/skills/deploy-vault/SKILL.md              |   6 +-
 backend/tests/unit/test_deploy_vault_sh.py        | 253 +++++++++++++++++++++-
 backend/tests/unit/test_vault_install_manifest.py |  24 +-
 scripts/cls_forbidden_paths.py                    |  11 +
 scripts/deploy-vault.sh                           | 190 +++++++++++++++-
 scripts/vault-install-manifest.json               |  18 +-
 6 files changed, 482 insertions(+), 20 deletions(-)

文件数 = 6            ← 卡文 5 项 + 主 session 裁决扩的 test_vault_install_manifest.py
backend/app/** = 0    ← 零越界 ✅
```

> ⚠️ **验伪锚在代码 commit 这一刻不成立，如实记录**：去掉 `':(exclude)_bmad-output'` 后
> `_bmad-output/` 命中 **0** —— 不是 exclude 失效，而是此刻 `_bmad-output` 下的改动**全是未追踪的**，
> 根本不在 `PREV..HEAD` 区间内。锚要成立必须等本验收单与存档进 docs commit 之后。
> **docs commit 后的补跑结果见下方**。

### 裁判 7 目录级**终跑**（存档 `unit-close-r5-20260916T125746.txt`）

| 跑 | 汇总 | nodeid | 对基线 diff |
|---|---|---|---|
| 首跑（manifest 两 item 引出 3 条） | 38 failed / 29 errors | 67 | 3 行 `>` |
| 中跑（扩面修好后） | 35 failed / 29 errors | 64 | 空 |
| **终跑**（r4 整改后，绑最终 HEAD） | 35 failed / 5077 passed / 29 errors（333s） | **64** | **完全为空**（`diff` rc 0，零 `>` 零 `<`）✅ |

### ⚠️ 硬边界自证：`~/.codex` 下有 357 个新文件 —— 归因，不报「0」

（存档 `closeout-20260916T130510.txt`）

开工 sentinel 之后：`~/.config/opencode` 新文件 **0** ✅；但 `~/.codex` 新文件 **357**，
且 `config.toml` 的 sha 与开工时**不同**（`94aae2fc…` → `5d7a6dcf…`）。
⛔ 不能把这一条含糊成「0」。归因如下：

| 证据 | 结论 |
|---|---|
| 357 个文件的分布：`sessions/` **206** · `memories/` **108** · `thread-writer-locks/` 8 · `plugins/` · `cache/` · `tmp/` · `thread_history_*.sqlite*` · `state_*.sqlite*` · `history.jsonl` · `models_cache.json` … | 全是 **`codex exec` 自身的会话记录与状态**，不是部署脚本的产物 |
| `deploy-vault.sh` 非注释行引用 `.codex` = **0**、`.config/opencode` = **0** | 脚本对两者是**词法零写者** |
| **隔离观测**（`judge4c-userconfig-sha-*.txt`）：对 `--hosts claude,opencode --apply` 那一跑，跑前跑后 `~/.codex/config.toml` / `opencode.jsonc` / `.gitignore` 三者 sha **逐字相同**（config.toml 两侧都是 `94aae2fc…`） | **运行期零写**，裁判 4③ 成立 |

⇒ **硬边界「禁写 `~/.codex/**`」在本卡代码与本卡操作层面成立**；那 357 个文件是协议 §2
明文规定的审查命令 `codex exec` 跑 **5 轮**留下的自身记录。如实登记，供主 session 知悉。

### 其余硬边界自证

| 项 | 实测 |
|---|---|
| live vault `canvas-vault/` 开工后新文件 | **0** ✅ |
| 改动文件里 `fsrs_bridge` / `decay_beta` 命中 | **0** ✅ |
| 本卡新增测试段 `tmp_path` 出现 / 绝对路径硬编码 | 66 / **0** ✅（落点全部 tmp 派生） |
| 禁连 7691 / 7687 | 每次 pytest 收尾行 `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)` ✅ |
| `*.stderr*` 入库 | `git check-ignore` 实测被 `.gitignore:264` 覆盖 ✅ |
| 禁 `git stash` / 批中装包 / 改台账 / push | 全程零 ✅（负控还原一律用「变异前工作树副本 + EXIT trap」） |

### 终审绑定

```
git --no-pager diff --stat --no-color 6acec0e4 HEAD -- . ':(exclude)_bmad-output'
（空）
```
⇒ **r5 的审查 SHA 就是最终 HEAD 的代码面**，绑定成立。

### 各轮整改的验证存档索引（补全，免得「证据落盘了却指不到」）

| 存档 | 内容 |
|---|---|
| `red-e1-20260915T115021.txt` / `red-newgates-20260915T115208.txt` | (b) 先红①②（rc 64 / 新门 FAILED） |
| `tmpdir-red.txt` | 先红①用的 tmp 目录记录 |
| `green-dry-hosts-20260915T115422.txt` | 改后 dry rc 0 + 零写 |
| `judge3-apply-artifacts-20260915T115438.txt` | 生成物实物（软链 / readlink / frontmatter / AGENTS.md 全文） |
| `judge4a-d26i-hit-…` / `judge4a-d26i-falsify-…` / `d26i-negctl-20260915T115545.txt` | D-26(i) 断言 + 验伪锚（另跑）+ 负控删 `:270` |
| `judge4c-userconfig-sha-20260915T115556.txt` | 用户级配置隔离观测（跑前跑后 sha） |
| `judge6-opencodejson-20260915T115522.txt` | 非注释行子串约束 + 双向验伪锚 |
| `judge-g-claude-only-regression-20260915T120403.txt` | `--hosts claude` 与 PREV 逐字 diff + 验伪锚 |
| `judge-ruff-20260915T120501.txt` | ruff check/format + 验伪锚 |
| `judge-manifest-20260915T234259.txt` | manifest 门扩面后 175 passed |
| `judge6-filelevel-20260915T115637.txt`（首跑，1 failed）→ `…120035.txt`（201 passed） | 写面门被逼登记前后 |
| `judge-filelevel-final-20260915T235740.txt` | 两份测试文件 376 passed |
| **`negctl-r1-gates-20260916T011111.txt`** | r1 整改负控（M2 对照输入 / H1 删前置） |
| `judge-filelevel-r1fix-20260916T011331.txt` | r1 整改后 204 passed |
| `negctl-r2-gates-20260916T013203.txt` | **r2 负控对照**：钉 TMPDIR 判据红 / 拆钉子同一变异绿 |
| `judge-filelevel-r2fix-20260916T013305.txt` | r2 整改后 204 passed |
| `judge-filelevel-r3fix-20260916T014855.txt` | r3 整改后 206 passed |
| **`negctl-r4-gates-20260916T020500.txt`** | r4 三条负控（换回 `ln -s` / 换回按路径 unlink / `O_EXCL` 挪进注释） |
| `judge-filelevel-r4fix-20260916T020604.txt`（1 failed，既有门抓到裸 `os.write`）→ `judge-filelevel-r4fix2-20260916T021208.txt`（**207 passed**） | 既有门抓到本轮整改的缺陷、修好 |
| `unit-close-20260915T120517.txt` → `unit-close-final-20260915T234347.txt` → **`unit-close-r5-20260916T125746.txt`** | tests/unit 目录级三跑（67 → 64 → **64**） |
| **`selfcheck-r5-findings-20260916T125808.txt`** | 车道对 r5 四条 findings 的独立核验实证 |
| **`closeout-20260916T130510.txt`** | 收工核验（硬边界自证 + 终审绑定） |

### 裁判 5 地盘核 + 验伪锚（docs commit 之后补跑，存档 `judge5-territory-final-20260916T131204.txt`）

```
git --no-pager diff --stat --no-color 7e1d6b53 HEAD -- . ':(exclude)_bmad-output'
 .claude/skills/deploy-vault/SKILL.md              |   6 +-
 backend/tests/unit/test_deploy_vault_sh.py        | 495 +++++++++++++++++-
 backend/tests/unit/test_vault_install_manifest.py |  24 +-
 scripts/cls_forbidden_paths.py                    |  11 +
 scripts/deploy-vault.sh                           | 512 ++++++++++++++++++-
 scripts/vault-install-manifest.json               |  18 +-
 6 files changed, 1043 insertions(+), 23 deletions(-)
文件数 = 6 ; backend/app 越界 = 0 ✅
```

**验伪锚：46 vs 0** —— 去掉 `':(exclude)_bmad-output'` 后 `_bmad-output/` 命中 **46**，
带 exclude 时命中 **0** ⇒ exclude 真在起作用，主判据不是恒空。✅

> ⛔ **这条锚本身踩了两个坑，都留档**（前两版存档 `…T130917.txt` / `…T130935.txt` 刻意保留，
> 删掉就看不出判据是怎么被修对的）：
>
> **坑①**：锚第一版写成 `git diff --name-only | grep -c '^_bmad-output/'` → 读出 **0**，
> 我差点据此误判成「exclude 失效」。实为 **git 默认对非 ASCII 路径做 C 引号化** ——
> 输出是 `"_bmad-output/\345\256\241\346\237\245/…"`，**行首是引号**，行首锚永远匹配不到。
> 修法：`-c core.quotepath=false`（**是 git 的 flag，不是 grep 的** —— 与 R-B14-11 说的 `--no-color` 同族）。
> ⇒ 已记入工程坑 memory（`reference_git_quotepath_breaks_line_anchors`）。
>
> **坑②**：我在修正后的**同一份存档里**，把对照数**手打**成「43 vs 0」，实测是 **46**。
> ⇒「关于证据的断言必须先数一遍再写」。终版里所有数字都由命令算出、不手打。

### ⚠️ 残留面扫描（加分项）未完成 —— 如实登记

收尾阶段另起了一个只读扫描（三路并行：HIGH-1 同型面有多宽 / 静态门同型漏面 / 5 轮都漏了什么），
目的是给**修复卡**一个准确的范围。**三路各重启 3 次仍未产出**（本机 API 当时不稳，
主 session 自己的工具调用也在超时），已主动停掉，**不拖延交付**。

⇒ 这意味着 §七 的第 16 条（HIGH-1 同型面有多宽）与第 19 条（其余静态门有无同型漏面）
**至今仍是未知数**，不能因为「扫过了」而降级。修复卡需要自己把这个面量全。

---

## 六.1 Codex 各轮

模型 `gpt-6-astra` · `reasoning_effort: ultra` · `codex-cli 0.153.3`（协议 §2 固定）。
每份存档首部按协议 §2.1 带六行 blockquote；会话头自证抄的是 `.stderr` 里
**含 codex 版本 / `model:` / `reasoning effort` 的那三行并括注实测行号**（L2 / L5 / L9）——
⚠️ 本卡实测印证了新口径的必要性：`model:` 在**第 5 行**，字面抄「前三行」会漏掉它。

| 轮 | 绑定 SHA | B / H / M / L | 存档 | 整改 commit |
|---|---|---|---|---|
| r1 | `836b1b7d` | 0 / **2** / 2 / 0 | `codex-review-CARD-HOSTS-OPENCODE.md` | `c228b745` |
| r2 | `c228b745` | 0 / **1** / 1 / 1 | `codex-review-CARD-HOSTS-OPENCODE-r2.md` | `4ad30472` |
| r3 | `4ad30472` | 0 / **3** / 1 / 0 | `codex-review-CARD-HOSTS-OPENCODE-r3.md` | `a09c2b96` |
| r4 | `a09c2b96` | 0 / **2** / 2 / 1 | `codex-review-CARD-HOSTS-OPENCODE-r4.md` | `6acec0e4` |
| **r5** | **`6acec0e4`**（最终 HEAD） | 0 / **2** / 1 / 1 | `codex-review-CARD-HOSTS-OPENCODE-r5.md` | **未整改 —— 见下** |

前四轮 **15 条 findings 全部采纳，零驳回**。

## ⛔⛔ 六.2 轮次用满且仍有 HIGH ⇒ 按 D-15 停下交主 session 人审

> **协议 D-15 原文**：「轮次上限 5，第 5 轮仍有 HIGH → 停下交主 session 人审」
> 「车道对 HIGH 的驳回要写理由但**不能自判通过**，由主 session 复核时裁定，裁定前该卡按未完成」

**车道不自判通过。** 代码自 `6acec0e4` 起**一行未改** —— 5 轮用满后再改代码，最终 HEAD
就没有任何一轮审查绑定它（`git diff --stat 6acec0e4 HEAD -- . ':(exclude)_bmad-output'` 实测为**空**，
绑定成立）。以下四条连同车道的**独立核验实证**一并移交。

### 车道独立核验（只读，存档 `evidence-hosts-opencode/selfcheck-r5-findings-20260916T125808.txt`）

> ⛔ 不默认 Codex 对，也不默认它错 —— 本卡已经自己错过两次（`os.replace` 那个断言、负控措辞），
> 所以每条都去实测，而不是靠推理代替实测。

| # | Codex 结论 | **车道实测裁定** | 依据 |
|---|---|---|---|
| **HIGH-1** 技能名过检后被改写，能生成禁写的 `.git` 条目 | HIGH | ✅ **CONFIRMED，是真缺陷** | 判据实测：`' .git'` → `OK` rc 0（放行）／`'.git'` → `HIT .git 目录内` rc 1（拒绝）。**端到端实测**：源目录 ` .git` ⇒ shell `basename` 得 `[ .git]` 用它过判据放行 ⇒ python `splitlines()+strip()` 变 `.git` ⇒ **软链真建出来了**（`readlink` = `../../.claude/skills/.git`），之后才因解析失败报 rc 1，**残链已落盘**。零竞态、纯确定性输入 |
| **HIGH-2** 清理分支 `fstat(nlink)` → `ftruncate` 的 TOCTOU | HIGH | ⚠️ **技术成立，但严重度存疑（车道倾向 LOW/MEDIUM）** | 见下「对 HIGH-2 的理由」 |
| **MEDIUM-1** 静态门「去注释」只滤整行，行尾注释仍参与 flags 检查 | MEDIUM | ✅ **CONFIRMED，两个负控都复现** | 内存负控：真实 `O_EXCL` 删掉、**行尾注释**留该词 ⇒ 门仍 **PASS**（假绿）；删掉清理分支的 `nlink` 检查 ⇒ 两个门仍 **PASS**（该检查无门锁住） |
| **LOW-1** 已接受的裁定更正仍有注释未落实 | LOW | ⚠️ **两处成立、一处不成立** | ① `deploy-vault.sh:1305` 仍写「拦成 rc 72…走不到的分支」**成立**；② `test_deploy_vault_sh.py:3712` docstring 仍写「补进 3 项…（+ 其 `.tmp`）」而同一 docstring 下方又说 `.tmp` 已退场，**自相矛盾、成立**；③ Codex 说文案仍承诺「重跑会被覆盖」—— 实测该字样命中 **0**，我在 r4 已改掉，**这半条不成立** |

### 对 HIGH-2 的理由（按 D-15 写理由，**不自判通过**，裁定权在主 session）

技术上当然成立 —— 任何 `check-then-act` 都有窗口。但影响面与脚本里另外三处 `ftruncate` **不同**：

- 本处 fd 指向的是**本次 `O_EXCL` 新建**的文件 ⇒ 别人要受影响，必须**主动 `link` 到我的半成品**；
- 另外三处经 `open_pinned` 打开的是**已存在**的文件，那里的 `nlink` 检查防的是「伤到别人原有的数据」；
- 被截断的内容是**半成品**（不是任何人的数据），且**去掉这个检查只会更糟**。

⇒ 车道认为该条严重度应低于 HIGH。**但这只是理由，不是裁定** —— 按 D-15 由主 session 复核时定夺。

### 合并门口径下的车道判断（供主 session 参考，非裁定）

项目合并门：**阻断级 = 数据丢失 / 写 live vault 或 Neo4j 7691 / 安全 / 指定裁判红 / 负控假绿**，
其余 BLOCKER/HIGH/MEDIUM/LOW **登记不阻断**。

上述四条**均不落在阻断级**：HIGH-1 的写入限于**部署目标 vault 内**（不碰 live vault、不碰 7691），
触发需要 harness 的 `canvas-vault/.claude/skills/` 里先有一个名字带前导空白的目录；
MEDIUM-1 是**判据强度**不足（不是负控假绿 —— 负控本身没有谎报 PASS，是我用它验的那个门太弱）；
LOW-1 是文档残留。⇒ 车道读到的是「**登记不阻断**」，但 HIGH-1 是**真缺陷、下批必修**。

### r1 → r2 整改（四条）

| r1 | 整改 | 负控 |
|---|---|---|
| H1 `.agents` 祖先软链使落点整体偏移 | 前置逐级 fail-closed + 后置改核**物理**落点（`pwd -P`；前缀比较用 `${var#"$prefix"}` 而非 `case`，免得 vault 路径里的 `[` `*` `?` 被当通配） | 删前置 → H1 门变红 |
| H2 tmp 写入与 `mv` 的三个替换窗口 | `publish_agents_md`：`O_EXCL\|O_NOFOLLOW` 建 tmp → `fsync` → 紧邻 `os.replace` 前复核；标记判据收敛为单一 `refuse_reason()`，并按 Codex 更正改为**首行精确相等** | （r2 判定未闭合，见下） |
| M1 MCP 端点缺 `/mcp` | 文案给完整端点 + remote 类型说明 | 新门断言完整端点在正文里 |
| M2 dry 零写门只按名字找文件 | 改为**整棵树快照**比对 | 用 Codex 给的对照输入实测：旧判据绿、新判据**红** ✅ |

### r2 → r3 整改（三条）

| r2 | 整改 | 负控 |
|---|---|---|
| **HIGH** 发布仍未绑定检查过的文件身份（`os.replace` 按路径重找 tmp / 末次检查与替换之间 / 父目录未固定） | 换掉发布机制本身：① 父目录 fd（`O_DIRECTORY`）钉死 inode，其后 `stat`/`open`/`link`/`unlink` 全走 `dir_fd=`；② **`os.replace` → `os.link`** —— 目标已存在时 link **原子失败**(EEXIST)，replace 则无条件覆盖，「不覆盖任何已存在的东西」于是由内核保证；③ 目标已存在且带标记时走 `unlink`→`link`，中途被抢建则 EEXIST **不覆盖**；④ tmp 身份 fd 侧与路径侧**各自**要求 `nlink==1` 再比 `(dev, ino)`；⑤ `finally` 总清 tmp（残片会让下次跑在 `O_EXCL` 上永久失败）；⑥ 空正文一律拒 | — |
| **MEDIUM** 快照未覆盖真正的 `$TMPDIR` | `_oc_tmpdir()` 单一来源把 TMPDIR 钉进 `tmp_path`，且零写门须在拍 before 快照**之前**先调它 | **对照实验**：同一个「往 `$TMPDIR` 留文件」的变异 —— 钉了 TMPDIR **1 failed**（抓到 `tmpdir/oc-stray.txt`）；拆掉钉子回到 r2 前写法 **1 passed**（完全看不见）。存档 `negctl-r2-gates-20260916T013203.txt` |
| **LOW** `src="$(cat …)"` 未判 rc，空 src 下 `python3 -c ""` 返回 0 | `\|\| srcrc=$?` + `[ "$srcrc" != 0 ] \|\| [ -z "$src" ]` 即 `return 1` | 见下「负控口径更正」 |

> ⛔ **上面这段曾写成「实测 `os.replace` 不支持 `dir_fd`」——那是错的，已由 Codex r3 G 条
> 更正并实测复核**：`os.replace` 确实不在 `os.supports_dir_fd` 集合里，但带
> `src_dir_fd`/`dst_dir_fd` **实际调用成功**（scratchpad 实测：`os.replace(a, b,
> src_dir_fd=d, dst_dir_fd=d)` → 成功，`b.txt` 在、`a.txt` 不在）。
> 我当时**只查了集合、没真去调**，把「集合里没有」当成了「不支持」——
> 这是「能力存在 ≠ 能力接上」的同型错误，判据取在了一个不等价的代理量上。
> （r3 之后已不再使用 `os.replace`，但错误结论必须留档更正，不能因为"反正不用了"而略过。）

### r3 → r4 整改：不是修竞态，是**去掉制造竞态的那个机制**

r3 的 H1 / H2 / M1 **三条全部长在「写 tmp → 改名发布」这套机制上**：

| r3 | 内容 |
|---|---|
| **H1** | EEXIST 分支无条件 `unlink` —— EEXIST 只证明「此刻有东西」，不证明「是我刚检查过的那个」⇒ 会删掉检查之后才出现的手写文件。⚠️ **这是我 r2 整改自己引入的新缺陷** |
| **H2** | `os.link(tmpbase, …)` 按**名字**重找源，fd 身份检查绑不住实际发布的那个 inode |
| **H3** | 父目录 fd 可能固定到「步 1 判据之后已被重定向」的目录 |
| **M1** | tmp 清理失败被静默吞掉，残片让下次跑在 `O_EXCL` 上永久失败 |

整改 = **直接以 `O_CREAT|O_EXCL|O_NOFOLLOW` 建目标本身并写进去**：

- `O_EXCL` ⇒「绝不覆盖任何已存在的东西」由**内核**保证，不靠「检查完祈祷没人插队」
- 全程持有同一个 fd ⇒ 没有任何一步「按名字再找一次」（H2 消失）
- 没有 tmp ⇒ 没有 EEXIST 分支、没有 `unlink`、没有残片（H1 / M1 **整类**消失）
- **目标已存在一律拒绝**并说清它是什么，**不再替换**：替换必然要先 `unlink`，那正是 H1；
  而整脚本重跑本就被步 2 的防覆盖闸门拦成 rc 72、到不了步 3 ⇒
  为一个**走不到的分支**保留 `unlink`，换来的是一整类竞态
- **H3 只做到一半，如实声明**：补了 `O_NOFOLLOW`（我 r2 说「刻意不加」的理由已被指出不成立），
  但**祖先替换窗口仍在** —— 闭合它需要步 1 打开 fd 一路传到步 3，而步 1 是别的卡的定稿面
  （本卡禁改）⇒ 登记为移交项，见 §八

随机制退场的**死登记**也一并清了：`PENDING_WRITES` 与 `check_forbidden_paths` 里的
`AGENTS.md.tmp`。写面清单只登记真正会被写的对象 —— 多留一条不会更安全，只会让清单说谎（DD-13）。

新增门 2 条：
- `test_hosts_opencode_refuses_to_replace_even_its_own_previous_output` —— 锁住「存在即拒」
  这个**刻意取舍**，免得后人当 bug 顺手改回去
- `test_deploy_sh_publishes_agents_md_without_a_temp_file` —— 静态门，发布段不得再出现
  `os.replace` / `os.link` / `os.rename`。**负控实测**：把 `os.link` 加回该段，门变红

### r4 → r5 整改（五条 + 两条既有门抓到的）

| r4 | 整改 | 负控 |
|---|---|---|
| **HIGH-2** `ln -s` 的**目录语义**可绕过已登记叶子 —— 检查后落点若变成目录（或指向目录的软链），`ln -s "$tgt" "$link"` 会把它当**目标目录**，实际在 `$link/<name>` 里建，那个写对象从没过判据 | 新增 `bind_opencode_skills`：整条 `mkdir` + `symlink` 链钉在目录 fd 上（逐级 `O_DIRECTORY\|O_NOFOLLOW` 打开、全程 `dir_fd=`），建软链走 **`symlink(2)`**。**本机实测**：落点是目录时 `os.symlink` 返回 **EEXIST 且该目录内容为空** —— 没有 `ln(1)` 那个便利语义 | 换回 `ln -s` → 新门变红 |
| **HIGH-1** 失败清理 `stat → unlink(name)` 两步，钉不住叶子名字 | 改为对**同一个 fd** `ftruncate` + 写自解释的半成品标记，**零路径解析**；下次跑由 `describe_existing` 认出并报「内容不完整，请删掉再重跑」 | 换回按路径 `unlink` → 门变红 |
| **MEDIUM-1** `describe_existing` 的 open 会被 FIFO **卡死**（连 rc 73 都返回不了）+ 无界 `readline` | 补 `O_NONBLOCK` + 打开后按 fd 再确认 `S_ISREG` + 定长读 | — |
| **MEDIUM-2** 静态门取名面不含函数尾部、flags 在**含注释**的文本里判 | 取名面扩到整个函数；flags 改在**去注释的代码**里判；禁串补 `os.renames` / `shutil.move` / `.rename(` 与三个按路径删除 | 把 `O_EXCL` 挪进注释 → 旧门放行、**新门变红** |
| **LOW-1** 文案仍承诺「重跑会被覆盖」，与「存在即拒」矛盾 | 文案改为「脚本不会覆盖已存在的这份文件」 | — |

> ⛔ **两条既有门抓到了本轮整改自己的缺陷**（这正是它们存在的理由）：
> ① 裸 `os.write` 会**短写** ⇒ 两处写入改走 `write_all`（脚本既有铁律，原语在
> `cls_forbidden_paths.py`）；② `ftruncate` 前必须先 `fstat` 查 `nlink`
> （`O_EXCL` 只保证**新建**，写入期间仍可能被 `link` 出第二个名字，那时截断改的是共享 inode）。
>
> 顺带**加固了这两条门**：计数从**全文**改到**去注释的代码**上做 ——
> 我写整改说明时在注释里写出了被计数的字面量，于是**注释自己被数了一次**。
> 判据分不清代码和注释 = 判据在说谎。⚠️ 而且这与我在同一轮里修 MEDIUM-2 的理由
> **完全同型**（flags 写在注释里也算），我刚修完一处、转头在另一处又制造了一次。

### ⚠️ 我接受的两处裁定更正（Codex r4 L 条）

1. **「已有目标分支走不到」过强**：installer 成功返回前留下 `AGENTS.md`、或并发创建，
   都能让步 3 遇到已有目标（我的预置文件门正覆盖前一种）。注释已改。
2. **「第二次必然 rc 73/72」不准确**：默认 env 目录下重跑可能先被 `ACTIVE_VAULT`
   碰撞检查拦成 **71**。

### ⚠️ 负控口径更正（两处，我此前措辞过强）

1. **「删前置后两层都承重」→ 措辞收窄**。Codex r2 A 条指出：只删前置后**仍 rc 73**
   不代表仍保住外部零污染 —— 那时 `mkdir`、软链与 AGENTS 发布**已经可能发生**。
   实际成立的说法是：后置物理落点核**不是死代码**（它能把错误落点变成失败），
   但它拦不住「已经写出去」这件事。前置检查才是防外部写入的那一层。
2. **r2 的一个负控实际测到的不是「守卫承重」**。我把 `src=""` 塞在守卫**之后**，
   于是证明的是「守卫万一失效，下游门仍会红」（防御深度），**不是**守卫本身承重。
   Codex 描述的假绿场景需要「已有带标记的 AGENTS.md + src 捕获失败」同时发生，
   本卡**未造出**该场景 —— 记入「本卡未证明什么」。

---

## 七 本卡未证明什么（≥4）

1. **未跑 OpenCode 模型**（本机无 provider 凭据；配凭据 = 写 `~/.config/opencode` 硬禁面，须用户当次授权）
   ⇒ **未证**生成的 `.agents/skills` 软链与 `AGENTS.md` 在真实 OpenCode 会话里被正确发现和使用。
   本卡只做静态文件树 + `readlink` 目标 + frontmatter `name` 核。
2. **未证相对软链在 live vault 下的落点与 tmp vault 一致**。本卡全部生成落点都在 `tmp_path` 派生目录，
   live vault（`.git` 为目录的祖先）与 worktree（`.git` 为文件）下的差异沿用 HOST-PROBE §五.8 登记的
   P10 偏离，**未消除**。
3. **未证 OpenCode「同名按 frontmatter `name` 去重」在三根（`.agents` / `.claude` / `.opencode`）并存时的
   实际去重顺序**。条目级软链的设计依据是只读静态表结论，**未做运行期复验**；本卡也没有造出
   `.opencode` 这第三根来观察三方并存。
4. **D-26(i) 覆盖面只证了 `opencode.jsonc` 与 `.gitignore` 两个文件被 `:270` 的整目录保护拦下**，
   **未枚举** OpenCode 可能写的其它用户级文件（本机当前只有这两个，那是**一次观测不是不变量** ——
   OpenCode 升级后多写一个文件，目录保护仍然覆盖，但本卡的断言不会自动覆盖到它）。
5. **未证 `AGENTS.md` 的指引文案不会诱导用户手写 `~/.config` 下的用户级配置**。文案里有一句明确劝阻，
   但那是**文案评审**，不是运行期验证；且该句为避开子串约束做了绕述（写成「`~/.config/` 下 OpenCode 的
   用户级配置目录」而非全名），可读性有损。
6. **未实现 / 未验 `--hosts` 同时带 `codex`**（T2-D 的面）。本卡对 `codex` / `dsh` 仍是 rc 64。
7. **未证 `AGENTS.md.tmp` → `mv` 发布路径没有 TOCTOU 窗口**。写前过了 `assert_writable_now`，
   但「复查之后、`mv` 之前」被掉包这一类，本卡**没有**像 T2-B 对阶段账那样做 fd 钉 inode 的加固。
8. **未证 `.agents/skills` 下已有条目时的幂等/拒覆盖分支在真实重跑里被走到**。那两个分支
   （指向相同 ⇒ 跳过 / 指向别处 ⇒ fail-closed）有代码，但**没有对应的门**；整脚本重跑会先被步 2 的
   防覆盖闸门拦成 rc 72，到不了步 3。
9. **本卡不做「陈旧软链清理」，如实声明**：若 `$VAULT/.claude/skills` 里某条技能被删掉，
   `.agents/skills` 下对应的软链会变成悬空链而**不会被清掉**（本函数只增不删）。
   这在当前入口下走不到（重跑被步 2 拦成 rc 72），真正的收敛需要 adopt 语义（归 CARD-G2-7c）。
   ⛔ 本卡**刻意不加删除逻辑** —— 在一个「拒绝覆盖别人的东西」的函数里加 `rm`，需要先有
   「哪些是我建的」的可靠判据，那比本卡的面大。
10. **隐藏目录形态的技能条目不在覆盖面内**：枚举用 `for d in "$src_root"/*/`，bash 的 glob
    默认不匹配 `.` 开头的名字。实测 11 条运行期技能无一以 `.` 开头，但这是**一次观测不是不变量**。
11. **未造出「已有带标记的 AGENTS.md + `src` 捕获失败」这个组合场景**（Codex r2 LOW 描述的
    假绿路径）。守卫（`srcrc` + 非空判）是显然正确的，但本卡的负控把 `src=""` 塞在守卫
    **之后**，实际证明的是「守卫万一失效下游门仍会红」，**不是**守卫本身承重。
12. **`unlink` → `link` 这个替换序列的失败中段未做故障注入**：两步之间进程被杀会让
    AGENTS.md 暂时消失（代码注释已如实声明，它是可重新生成的派生件），但**没有**用
    信号注入实测过这条路径。
13. **前后快照证不了「中途完全没有写过」**（Codex r2 E 条）：建完又删的临时文件、
    内容相同的重写，两个时刻都看不出来。真正管住这些的是脚本「不传 `--apply` 就不走
    写分支」的控制流，本判据不宣称覆盖它。
14. **未在真实 OpenCode 里验证「双读」的后果**：Codex r2 独立查了官方 v1.18.31 源码，
    结论是两条别名路径会**分别解析**、再按 frontmatter `name` 覆盖登记，最终一个条目，
    **可能出现重名警告**。本卡设计依据的「三处都读 + 按 name 去重」成立，
    但「只解析一次」这个说法**不成立**，且那条警告本卡没见过也没消除。

15. **r5 的四条一条都没修**（5 轮用满，改代码会让最终 HEAD 失去审查绑定）。
    其中 **HIGH-1 是已实证的真缺陷**，不是「理论上可能」：车道端到端跑出了那条残链。
16. **HIGH-1 的同型面未全扫**：本卡只证明了「前导空白 + `.git`」这一个组合。
    `strip()` 还会改写**尾随空白 / `\r` / 制表符**的名字；而 `splitlines()` 对**名字里含换行**的目录
    会把一个名字**切成两个** —— 这两类本卡**未实测**，同型面有多宽是未知的。
17. **HIGH-2 的窗口未做真实竞态实测**：车道的严重度判断（限于本次新建 inode）是**推理**，
    不是文件系统层的实测。Codex 那侧也声明了「未在真实文件系统实施竞态」。
18. **Codex r5 的 P 条另指出一处本卡未处理的形态**：`fd` 钉死的是 **inode**，不保证那个目录
    **一直留在原位置** —— 拿到 `.agents` 的 fd 之后把该目录**搬走**，后续
    `mkdir("skills", dir_fd=afd)` 仍写进被搬走的那个目录。Codex 说既有
    `cls_forbidden_paths.py:131` 已登记过同类残余、本轮不重复计 HIGH，
    但本卡**未独立核验**这个说法，也未处理该形态。
19. **MEDIUM-1 暴露的是「判据分不清代码和注释」**，而本卡在**同一轮内**栽了两次
    （r4 修了整行注释、自己又在注释里写出被计数的字面量；r5 发现行尾注释仍能让 flags 门假绿）。
    ⇒ **未证明**本卡其余静态门没有同型漏面 —— 只证明了被点名的那两条。

---

## 八 台账待登记条目（≥4）

1. **`--hosts opencode` 转正（静态绑定件面）= 一键部署四件套 ④ 的第二家宿主落地**。
   改动文件 6 个（见 §三）；新门 nodeid：
   `tests/unit/test_deploy_vault_sh.py::test_hosts_opencode_generates_binding_files`
   / `::test_hosts_opencode_dry_run_writes_nothing`
   / `::test_hosts_claude_only_generates_no_opencode_binding`
   / `::test_d26i_opencode_user_config_files_are_refused`
   / `::test_d26i_falsification_anchor_ordinary_path_is_allowed`
   / `::test_deploy_sh_never_writes_opencode_user_config`
2. **三条既有门口径变更，后人加第三家宿主前必读**：
   - `test_second_tier_hosts_rejected_with_e1` —— 参数表去 `opencode`（`codex` 归 T2-D，届时同法移出）
   - `test_second_tier_hosts_not_implemented_anywhere` —— 禁件去 `AGENTS.md`；
     **`opencode.json` 刻意保留**（它同时锁住「非注释行不得出现该串」的子串约束）
   - `test_g2_8_activate_tx_opens_no_new_write_surface`（**卡文未预见的第三条**）—— 精确集合门，
     补进 3 个 label，并新加反向断言钉死「条件 append 必须留在取名面内」
3. **D-26(i) 文档枚举漏洞 = 移交项**：决策文档列 `opencode.json`，OpenCode 实写 `opencode.jsonc` +
   `.gitignore`（本卡在本机实测确认）。**运行期整目录保护已覆盖、无缺陷**；
   需改的是文档真相源（手册 §四.5 / HOST-PROBE §六.13），**由主 session 改，本卡不碰**。
4. **manifest 地盘扩面 + origin 约定破例（本卡最大的口径变更）**：
   `backend/tests/unit/test_vault_install_manifest.py` 加入本卡地盘（5 → 6 文件），
   4 处登记性常量更新；manifest 不再是 install-vault.sh 的**纯**投影（两件 origin 指向 deploy-vault.sh），
   已写进 manifest `description`。**下批若再加宿主，这两处都会再动。**
5. **deploy-vault SKILL.md（仓根 `.claude/skills/deploy-vault/SKILL.md`，R-B14-8）已随本卡更新**
   `--hosts` 文案（`:45` 那段）。T2-D 加 `codex` 时**需在同一处再改一次**。
6. **OpenCode 模型侧完整验收 = 移交**（需 provider 凭据 + 用户当次授权写 `~/.config/opencode`，
   第十五批候选）。与之配套的还有「三根并存去重顺序」的运行期复验。
7. **端口环境因**：本机现网 docker 栈长期占用 **8011**，`deploy-vault.sh` 的缺省端口跑会落 rc 71。
   本批后续凡跑真 CLI 的卡一律显式 `--port <空闲口>`（本卡用 8099；避开 7691 / 7692 / 7478 / 11434）。
8. **Codex 各轮存档路径、绑定 SHA、B/H/M/L 计数**（见 §六回填）。
9. **tests/unit 目录级 diff 结果**（带 `--ignore test_deploy_vault_sh.py` 口径，基线 64 条）见 §六。
10. ⛔⛔ **本卡按 D-15 停在「未完成」态，交主 session 人审**：5 轮用满、r5 仍 HIGH=2。
    代码定格 `6acec0e4`，终审绑定成立（审 SHA → HEAD 代码面 diff 为空）。
    **需要主 session 裁定三件事**：① HIGH-1 是否阻断合并（车道判：真缺陷但非阻断级，下批必修）；
    ② HIGH-2 的严重度（车道给了理由但不自判）；③ 是否开一张修复卡带着 r5 的四条一起进下一批。
11. ⛔ **HIGH-1 的修复方向（供修复卡参考，本卡未实施）**：根因是**同一个名字被两侧各自解释** ——
    shell 侧 `basename` 拿原名去过判据，python 侧 `splitlines()+strip()` 重新解释后才真建。
    修法不是「在 python 侧也做一次判据」（那是加第三份手抄口径，必然再漂），而是让两侧**看到同一个字节串**：
    改用 `\0` 分隔传递 + python 侧按 `\0` 切且**不 strip**；或在 shell 侧就拒绝含空白/换行的技能名。
    ⚠️ 同批要扫 `splitlines()` 把「一个名字切成两个」的形态。
12. ⛔ **MEDIUM-1 的修复方向**：静态门的「去注释」要能处理**行尾注释**。
    ⚠️ 但这是 shell 里嵌的 python heredoc，做真 AST 解析的前提是先把 heredoc 抽出来 ——
    抽取本身又是一道词法判据。修复卡需要先裁定「判据强度做到哪一层就够」。
13. **本卡三次踩「判据分不清代码和注释」**（r4 两次 + r5 一次）。这不是知识问题，是
    **修完一处不回头扫同型**的纪律问题 —— 建议进工程坑索引。

---

## 九 DoD-3 双段

### 4-A｜Claude 已代验（技术证据）

| # | 主张 | 证据 |
|---|---|---|
| 1 | 改前 opencode 被拒、改后被接受 | rc 64 → rc 0，`red-e1-…` / `green-dry-hosts-…` |
| 2 | 生成的是**条目级**软链、目标解得到、指向同一份 SKILL.md | `judge3-apply-artifacts-…`（3/3 `-L=yes` + `readlink` + `realpath` + `.agents/skills -L = NO`） |
| 3 | 技能名与 frontmatter 一致（层 1 口径） | 同上（3/3 `name: <条目名>`，过 kebab 正则） |
| 4 | dry 态零写 | `find $TMP \| wc -l` = 1 |
| 5 | 单宿主 claude 行为一字未动 | 两版逐字 `diff` 空 + 验伪锚有差 |
| 6 | 用户级配置零触碰 | 三文件 sha 跑前跑后逐字相同 + sentinel 0 |
| 7 | D-26(i) 的保护真的靠那一行 | 负控：删行后从拒变放行，还原后 sha 逐字相同 |
| 8 | 非注释行无 `opencode.json` 子串 | 命中 0，含注释对照 2，双向验伪锚 |

### 4-B｜你来验（产品体验，零技术词；全程在 Obsidian 与访达里完成，约 3 分钟）

- [ ] **我做**：装一门新课的资料库时，勾上「也给 OpenCode 用」。
      **我看到**：装完打开资料库文件夹，多了一个叫 `AGENTS.md` 的说明文件。
      **我感觉**：它像一张写给另一个助手的入门便条，一眼能看懂，不是一堆看不懂的代码。

- [ ] **我做**：打开那张 `AGENTS.md` 便条读一遍。
      **我看到**：里面按名字列全了我这门课能用的技能，和我在原来那边看到的一模一样、一条不多一条不少。
      **我感觉**：踏实 —— 两边看到的是同一套东西，不用担心哪天对不上。

- [ ] **我做**：改动其中一条技能的说明文字，然后从另一个助手那边再看一眼这条技能。
      **我看到**：改动立刻就在，不用改第二遍。
      **我感觉**：像是给同一套书配了第二把钥匙，而不是把书又抄了一遍。省心。

- [ ] **我做**：回头看看我电脑上原来给 OpenCode 做的那些个人设置。
      **我看到**：一个字都没被动过。
      **我感觉**：放心 —— 装一门新课不会把我别处的东西弄乱。

- [ ] **我做**：换一门课，这次**不勾**「也给 OpenCode 用」。
      **我看到**：装出来的东西跟我以前熟悉的一模一样，没多出那张便条，也没多出别的。
      **我感觉**：没有被强塞东西，要不要用是我自己说了算。

> **整体 felt-sense**：不用再记「这条技能我到底改的是哪一份」——这件事从需要惦记，变成了不用想。

---

## 十 硬边界遵守自证

| 边界 | 自证 |
|---|---|
| 禁写 live vault | 全程未写 `canvas-vault/**`；`cls_forbidden_paths.py` 的 `<live_vault>` 只作**位置参数**（纯词法判路径 + 只读枚举 `$HOME`，CLI 不写文件） |
| 禁写 `~/.config/opencode/**` / `~/.codex/**` | sha 前后逐字相同 + sentinel 计数 0 |
| 禁连 7691 / 7687 | 每次 pytest 收尾行 `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)` |
| 禁碰 `fsrs_bridge.py` / `decay_beta.py` | 改动文件 `grep -rn fsrs_bridge` = 0 命中（见 §六） |
| 现网 LanceDB 只读 | 本卡零 LanceDB 调用 |
| 禁改 `backend/app` | 地盘核零 `backend/app/**`（见 §六）；`python-typecheck`（glob `backend/app/*.py`）不触发 |
| 禁 `git stash` | 负控还原用「变异前工作树副本 + EXIT trap」，零 stash / 零 checkout |
| 批中禁装包 | 未装 / 未升任何包；ruff 用 `card-v5-lance` 共享 venv 里既有的那份 |
| evidence 存 `.txt` | 全部 `.txt`（仓根 `.gitignore` 有全局 `*.log`） |
| `*.stderr*` 不入库 | 见 §六 `ls-tree` 实数核 |
| 不改台账 | 台账条目写在 §八，**未改** `未合卡追踪台账.md` |
| 不 push | 见 §六 |
