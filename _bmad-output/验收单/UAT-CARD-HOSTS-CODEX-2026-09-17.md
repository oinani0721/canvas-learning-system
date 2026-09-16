# UAT — CARD-HOSTS-CODEX（`deploy-vault.sh --hosts codex`）

> 批次：`[BATCH-2026-09-11-第十四批 / CARD-HOSTS-CODEX]`（车道 `card-t2-deploy`，本车道第 4/5 张）
> 卡文：`.../第十四批-goals/T2-D.md`　协议：`card-batch-protocol.md`　用户裁定：**D-33** + **D-26(i) 不放宽**
> 证据目录：`_bmad-output/审查/evidence-hosts-codex/`

---

## 1. 🎯 一句话目标

部署一门课的时候可以顺带勾上 **Codex** 这个助手，脚本会在这门课的资料库里放好「给 Codex 看的说明」和「连接模板」，
但**绝不动你电脑上 Codex 自己的那份个人设置**。

---

## 2. 📖 你的视角

作为一个用这套系统学一门课的人，
我想**在装课的时候就把可选的助手一起选上**，
以便我之后想用哪个助手都有现成的入口，而不用担心它偷偷改了我电脑上别的东西。

---

## 3. 🖥️ 交互流程

```
你装一门课时，在选助手那一步多勾一个 Codex
        ↓
装完，这门课的资料库里多出两样东西：
   · 一份「Codex 连接模板」（放在资料库的 .codex 文件夹里）
   · 资料库入口说明文件的末尾多了一段「Codex」
        ↓
那段说明会告诉你：光放着是连不上的，要连就自己跑一句话；
以及「这个脚本不会改你 Codex 的个人设置」
        ↓
你电脑上 Codex 的个人设置：一个字都没变
```

---

## 4-A. 🤖 Claude 已代验（技术断言全在这段）

### (a) 第 0 分钟核

| 项 | 实测 |
|---|---|
| `pwd` / 分支 | `…/worktrees/card-t2-deploy` / `card/t2-deploy` ✅ |
| `PREV`（= T2-C tip，串行绑定基准） | `7a8d50e2b92d002700b64837a8b518a2ac5facc1` ✅ |
| 前提：T2-C 已独立 commit | `git log --oneline -1` 命中 `CARD-HOSTS-OPENCODE` ✅ |
| 工作树干净 | `git status --porcelain \| wc -l` = **0** ✅ |
| venv / .env | `backend/.venv/bin/pytest` + `backend/.env` 均在位 ✅ |
| `codex --version` | `codex-cli 0.153.3` ✅（与卡文一致） |
| 红基线自证 | `grep -vc '^#' $BASE` = **64** ✅（R-B14-2 口径） |
| 开工 sha 锚 | `579fc8ed7545bafb1055e689ee9adc0cca00aa3070b6ed8ca825e86cff7f149f`（存档 `codex-config-sha-open-20260917T024848.txt`） |

### ⚠️ 卡文事实校正（实测 ≠ 卡文，逐条登记）

| # | 卡文写的 | 实测 | 处置 |
|---|---|---|---|
| 1 | `deploy-vault.sh` 1238 行；`:284` 校验循环 / `:697` A1 / `:1232` run_step 3 | 前提树（含 T2-A/B/C）已是 **2452 行**；校验循环 `:346` 区 / A1 `:1601` / `run_step 3` `:2446` | 卡文 §二.1 已预告「按内容锚点重测、漂移只登记」⇒ 只登记 |
| 2 | test 文件 2596 行 / 111 个 `def test_` | 前提树 **4860 行 / 170 个** | 同上，只登记 |
| 3 | 门① parametrize 为 `["codex","opencode","dsh","claude,codex"]` | T2-C 已移出 opencode，实测 `["codex","dsh","claude,codex"]` | 按实测改 |
| 4 | 模板写 `type = "http"` + `url` | **实测 `codex mcp add --url` 生成的规范形态只有 `url` 一行**；带 `type` 的写法 `codex mcp list` 也能解析，但该键**被静默忽略** | 取规范形态（只写 `url`）。写一个不起作用的键 = 名实不一致（DD-13）。存档 `codex-toml-schema-probe-20260917T025209.txt` |
| 5 | (c).3「**A1** 绑定校验加 `.codex/config.toml` 存在性」 | A1 在步 3 的 **Phase A（生成之前）**，而该文件正是步 3 自己生成的 ⇒ 放进 A1 **首跑必然 rc 73** | 落点改为「生成之后」，判据形态与 A1 三件逐字同款，与 opencode 的「③ 生成后在位判」同址同律。代码注释已写明 |
| 6 | (e) manifest 二选一：optional generate 项 / `extra_allow` | **两个选项都会打红本卡地盘外文件里的钉死门**（实测，见下） | 取第三条：登成 `exclude` 项。理由与实测见 (e) |
| 7 | 卡文只点了**两门**需要改 | 实测还有**第三门** `test_hosts_strips_all_whitespace_like_tr`（`:2056` 用 `--hosts claude,codex` 断言 rc 64） | 一并改：换成仍未实现的 `claude,dsh`，对照的**性质**逐字保住 |
| 8 | 裁判命令用 `timeout 900` | 本机**没有** `timeout` 也没有 `gtimeout`（批中禁装工具） | 改用 `perl -e alarm` 包装器；包装器自证 `rc=0`（正例）/ `rc=124`（超时例） |

### (b) 先红（改前，`deploy-vault.sh` 一个字未动）— 存档 `red-20260917T025305.txt`

| 门 | 改前 | 红的**原因** |
|---|---|---|
| ① 新门 `test_codex_host_generates_binding` | **FAILED**（rc=1）✅ | `AssertionError: rc=64` + stderr `❌ 用法错: --hosts 含未实现的宿主 codex` —— 红在「codex 未被接受」，不是 import/夹具错 |
| ② 既有门① `test_second_tier_hosts_rejected_with_e1 -k codex` | **2 passed** ✅ | 证明「改代码后不改测试必红」的方向对 |
| ③ 既有门② `test_second_tier_hosts_not_implemented_anywhere` | **1 passed** ✅ | 同上 |
| ④ 第三门 `test_hosts_strips_all_whitespace_like_tr`（卡文未点名） | **1 passed** ✅ | 同上 |

### (c) 实现（只碰 `scripts/deploy-vault.sh`）

1. `--hosts` 校验循环加 `codex) HOST_CODEX=1 ;;`；E-1 文案同步去掉 codex（DD-13：名单必须与 case 分支同步）。
2. 头注改一处即同步 `--help`（`usage()` 取头注切片，不写死行号）—— 实测 `--help` 已显示 codex 段。
3. 步 3 新增 **B4c**（排在 B4b **之后**：两家同写 AGENTS.md，opencode 负责建、codex 只追加；反过来排会让同时选两家直接 rc 73）：
   - `publish_codex_config` 生成 `$VAULT/.codex/config.toml`（已存在则**一律不动**，与 A4 key「已存在则不重生」同口径）；
   - `publish_codex_agents_section` 往 `$VAULT/AGENTS.md` **追加** `## Codex` 段。
4. **生成后在位判** fail-closed（见校正 #5）。
5. dry 态 STEP_MSG 补 codex 生成描述（含「不写用户级配置/信任表」），**零写**。
6. 步 1 写入面清单登记 3 条：`codex-config-dir` / `codex-config-toml` / `codex-agents-md`
   （最后一条只在没同时选 opencode 时登记 —— 同一路径登两条不会更安全，只会让清单说谎）。

#### ⛔ 为什么不复用 T2-C 的 `publish_agents_md`

它是 **create-only**（`O_CREAT|O_EXCL|O_NOFOLLOW`，存在即拒），整套安全论证建立在「绝不覆盖、绝不 unlink」上。
「往一个已存在的文件末尾加一段」是它刻意回避的形态，所以另写一条并把判据补齐，**而不是把它那条放宽**：

- 一次 `O_RDWR|O_APPEND|O_NOFOLLOW|O_NONBLOCK` 打开就把读和写都办了，**不重开第二次**；
- `fstat` 判 `S_ISREG` + `nlink == 1`（追加到有第二个名字的 inode 会改到别人的文件）+ 文件大小上限；
- 首行**精确相等**判生成标记，手写文件一律不动（与 T2-C 同一条不变量）；
- 幂等判**首锚 + 尾锚**：只认首锚的话，上次写到一半的半截段会被读成「已经有了」，那半截永远没人修；
- 失败清理**只截断本次新建的那一份**；追加失败的那一支绝不截断（那是用户已有的内容）。

### (d) 改后绿 + 三门更新

| 门 | 改法 | 结果 |
|---|---|---|
| 门① parametrize | `["codex","dsh","claude,codex"]` → `["dsh","claude,dsh"]` | ✅ 保住**两个形状**：单值 + 「合法值 + 未实现值」组合。只留单值的话，`claude,dsh` 被放行不会有门红 |
| 门② artifacts | 去掉 `.codex/config.toml`（留 `opencode.json` / `.dsh/`） | ✅ 移出的**只是项目级**那一份；用户级仍由新增两门接管 |
| 第三门对照输入 | `claude,codex` → `claude,dsh` | ✅ 对照的性质逐字保住 |

### (e) manifest 登记 —— 三条路径的**实测**对照（存档 `manifest-option-probe-20260917T030010.txt`）

跑的是隔壁 `test_vault_install_manifest.py` **整文件 175 条**：

| 候选 | 结果 | 要变绿得改谁 |
|---|---|---|
| 基线（不改） | 175 passed | — |
| A：加进 `extra_allow`（**卡文选项二**） | **1 failed** — `test_manifest_ships_the_five_ruled_extra_allow_entries`（那 5 条是逐字钉死的裁定表） | `test_vault_install_manifest.py`（本卡地盘外） |
| B：加进 `items` 作 optional generate（**卡文选项一**） | **3 failed** — generate 集要求 `install-vault.sh` 清理段有对应锚行 | `test_vault_install_manifest.py` + `install-vault.sh`（都在地盘外） |
| **C：登成 `exclude` 项（本卡自拟）** | **175 passed** ✅ | — |

⇒ 取 C。语义上 `exclude` 也正是卡文那句「别把它当 rogue extra」的**机制本身**（`is_excluded(rel)` 在 extra 扫描里短路掉它）。
⚠️ **如实声明**：今天这层防护是**潜在**的 —— `extra_scan` 只覆盖 `.claude` / `.obsidian` / `.obsidian/plugins` 三个根，
够不到 `.codex/`，所以它此刻本来也不会被报成 extra；哪天 `.codex` 进扫描面，这条立刻生效。
还原核：三次候选跑完后 manifest sha256 与原值逐字相同（`RESTORE_OK`）。

### (f) read-only 负控（承重，D-33 的核心交付）

#### ⛔ 第一趟是**空判据**，已作废并留档（`codex-readonly-negctl-20260917T030813.txt` 尾部有更正）

`rc=1`、`events.jsonl` **0 行**、**0 个** `command_execution`。stderr（复现后拿到）：

```
Not inside a trusted directory and --skip-git-repo-check was not specified.
```

即 codex 在「非受信且非 git」的全新临时目录里**直接拒跑**。一次没发生的运行当然不会改配置 ——
那条 sha-equal 什么也没证明。**「没跑完的探针不产出阴性结论」**。

#### 有效的那一份（`codex-readonly-negctl-20260917T030951.txt`）

| 项 | 实测 |
|---|---|
| 目录 | `mktemp -d` 全新目录，跑前在信任表里命中 **0** 次（验伪锚，防「已受信 ⇒ 空判据」） |
| 命令 | `codex exec -C $D --sandbox read-only --skip-git-repo-check --json …` |
| **前提核** | `rc=0` 且**有 1 条已完成的** `command_execution`（`/bin/zsh -lc 'ls -la'`，`exit_code=0`）⇒ 它**真的跑了** |
| **承重 ①** | sha before == after，逐字相同 `579fc8ed…f149f` ✅ |
| **承重 ②** | `$D` 跑后仍**未**进信任表（命中 0）✅ |
| **承重 ③** | 信任表段总数 **17 → 17** 不变 ✅ |
| 凭据口径 | 只取 `--json` 事件流的 `item.type == "command_execution"`；模型文本自述不作凭据 |

探针**自带**前提核：事件数为 0 时只报「未测出」，不报「没写」。

### (g) 脚本自测 — 存档 `file-level-final-20260917T031555.txt`

- `bash -n scripts/deploy-vault.sh` → **rc=0**
- `test_deploy_vault_sh.py` 文件级 → **226 passed, 9 skipped, 0 failed**，`rc=0`（269.94s，墙钟上限 900s 未触发）

> ⚠️ 中途有一跑 **2 failed**，是两条**设计上就要你来登记**的结构门抓到的（不是回归）：
> `test_g2_8_activate_tx_opens_no_new_write_surface`（新写面标签必须来这份清单登记）与
> `test_every_bash_write_site_has_a_prewrite_recheck`（`write_all` 5→8、`ftruncate` 4→6）。
> 两条门的 docstring 明写「再加写入点仍要同步改这几个数」—— 改法即登记，已同步。

### (h) tests/unit 目录级不回退

*（见文末「收工核验」段，与基线 64 的 nodeid diff）*

### (i) 禁写面不回退 — 存档 `forbidden-gate-20260917T031043.txt`

| 输入 | 实测 |
|---|---|
| `--vault:$HOME/.codex/probe` | `HIT --vault …/.codex（mkdir -p 会创建的中间段 …）` + **rc=1** ✅ |
| **验伪锚**（另起一跑）`--vault:$(mktemp -d)/v` | `OK --vault` + **rc=0** ✅（证判据不是恒拒） |
| 附加：`$(mktemp -d)/course/.codex/config.toml`（本卡生成物落点） | `OK --vault` + rc=0 ✅（否则部署自己过不去） |
| `cls_forbidden_paths.py` 本卡改动 | diff 行数 **0**（未改） |

### 硬边界自证 — 存档 `hard-boundaries-*.txt` + `hard-boundaries-codex-attribution-*.txt`

| 边界 | 实测 |
|---|---|
| Codex 用户级 `config.toml` | 开工 sha == 收工 sha，逐字相同 ✅（**这就是 D-33 要的那条结论**） |
| live vault | 对 HEAD diff = 0 行 ✅ |
| `fsrs_bridge.py` / `decay_beta.py` | 对 HEAD diff = 0 行 ✅（零写者） |
| 7691 / 7687 | 全部裁判跑都打印 `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0` ✅ |
| 禁改文件（`cls_forbidden_paths.py` / `verify_vault_install.py` / `SKILL.md` / `install-vault.sh` / `test_vault_install_manifest.py`） | diff 全 **0** 行 ✅ |

#### ⚠️ `~/.codex` 下确实多了东西 —— **归因，不报「0」**

> ⛔ 我第一版写的是「全部落在 `sessions/**`」，**那是错的**：我先写了结论才去数。
> 实测被写过的子树有 **22 个**（`skills/.system` 60 个文件、`sessions/2026` 13 个、`plugins/cache`、
> `thread-writer-locks`、若干 sqlite-wal 等）。已更正，逐条归因如下。

- `sessions/2026/09/17/**` = codex 每跑一次写一份会话文件 —— 本卡的负控探针与模板探针跑出来的。
- `skills/.system/**` = **codex 自己启动时**重装内建 skills（探针 stderr 实测报了这条）。与本卡生成物无关。
- 两者都属卡文 (f).7 的 **(ii) 运行期状态面**，登记不阻断；本卡不读其内容。
- ⛔ **承重面 `config.toml` 不在其中**（`find -name config.toml -maxdepth 1` = **0**）。

**关键区分（别把两件事混成一件）**：

- **交付物 `deploy-vault.sh`** 对 Codex 用户级配置是零写者 —— 三条判据：词法门
  `test_deploy_sh_never_writes_codex_user_config`、运行期判据 `cls_forbidden_paths`（HIT + rc=1）、
  以及它**从不调用 codex 可执行文件**（脚本里没有任何 `codex …` 调用，文案里那句是 printf 给用户看的字符串）。
- **本卡的探针**（测试脚手架，不是交付物）确实跑了 codex，于是 codex 写了它自己的运行期状态。

### 额外做的两件（卡文没要求，但直接回答审查问题 ③）

1. **模板键取舍有实测依据**：`codex mcp add --url` 生成的规范形态只有 `url`；`type` 键被静默忽略。
2. **生成物被 codex 自己解析通过**（`template-accepted-by-codex-20260917T031205.txt`）：
   把生成的原件逐字节拷进一个重定向的配置目录后 `codex mcp list` 列出
   `canvas-learning-mcp  http://127.0.0.1:8299/mcp`，rc=0；全程 `~/.codex/config.toml` sha 未变。
   端口 **8299**（`--port` 传进去的值）两处都对，`:8011` 零残留。

### 🐞 本卡顺带修掉的一个真缺陷（是新门抓到的）

dry 态 `--hosts claude,codex` 时 stderr 出现 **被截断在字符中间的 UTF-8**：

```
deploy-vault.sh: line 1984: PORT\xef: unbound variable
```

根因不是「文案写得随意」，是 **bash 的变量名扫描按 locale 判「字母」**：
UTF-8 locale 下 `）`（U+FF09 = `EF BC 89`）的首字节 `\xef` 被当成标识符字节吞进变量名，
`:$PORT）` 于是被读成变量 `PORT\xef`，配上 `set -u` 当场 `unbound variable`。

⚠️ 它**只在继承了宿主 locale 时显形** —— 我第一次用最小环境复现时 stderr 是空的，差点把它读成偶发。
⇒ 修成 `${PORT}`，并加一条**整片**的词法门 `test_no_bare_var_before_multibyte`（带正反两向验伪锚）。
全文件扫描确认：非注释行只有这一处（我自己写的），其余 5 处都在注释里（bash 不展开），**无既有缺陷**。

---

## 4-B. 👤 你来验（3 分钟，全在资料库里完成）

- [ ] 我装一门新课的时候，在选助手那一步**多勾一个 Codex** → 我看到装完照样是成功的，没有报错 → 我感觉**顺手**，多一个选择不用付出额外代价
- [ ] 我打开这门课的资料库，看它的入口说明文件 → 我看到末尾多了一段标题叫「Codex」的说明 → 我感觉**清楚**，它明确告诉我「光放着是连不上的，要连就照着这一句自己跑一次」，没有夸大
- [ ] 我照那段说明里的那一句去连 → 我看到 Codex 那边确实认出了这门课的连接方式 → 我感觉**踏实**，说明里写的和实际发生的一致
- [ ] 我回头看我电脑上 Codex 自己的那份个人设置 → 我看到它**一个字都没变** → 我感觉**放心**：这套东西没有背着我改我别的地方
- [ ] 我装课时**不勾** Codex → 我看到资料库里不会多出任何跟 Codex 有关的东西 → 我感觉**可控**，勾了才有，没勾就没有
- [ ] 我把那份连接模板按自己的需要改过之后再装一次 → 我看到**我改的内容还在**，没有被悄悄覆盖 → 我感觉**被尊重**

---

## 5. 🚦 验收结果

- 6 条都打勾 → 回一句「T2-D 通过」。
- 任何一条不对劲 → 在下面批注区写一句「我做了什么 / 我看到什么 / 我期待什么」，不用写技术细节。

---

## 6. 📝 批注区

> [!question]+ 我的疑问
>

> [!error]+ 我发现的问题
>

---

## 7. 🔗 技术 spec 引用

- 卡文：`_bmad-output/implementation-artifacts/goal-cards/第十四批-goals/T2-D.md`
- 代码：`scripts/deploy-vault.sh`（搜 `CARD-HOSTS-CODEX` / `write_codex_binding`）
- 门：`backend/tests/unit/test_deploy_vault_sh.py`（搜 `CARD-HOSTS-CODEX`）
- 清单：`scripts/vault-install-manifest.json`（`.codex/config.toml` 项）
- 证据：`_bmad-output/审查/evidence-hosts-codex/`

---

## 本卡未证明什么

1. **未证明 Codex 模型侧真能用上这份项目级模板连上学习后端** —— 已知事实是项目级条目零出现在 `codex mcp list`；
   本卡只生成模板 + 让用户自己接线的说明，**不声称**自动接线。真连通性归后续宿主卡 / U4 族。
2. **未证明 `codex exec --sandbox read-only` 在所有提示与模型配置下都不写用户级配置** ——
   只证「本机 codex-cli 0.153.3 + 全新且跑前缺席的目录 + 本卡那条只读提示」这**一组**组合。
3. **未重跑可写沙箱正控**（D-33 / D-26(i) 禁写信任表）—— 验伪锚靠「既有正控（首次遇新目录会追加记录、sha 变）」
   + 「本卡证该目录跑前缺席」两条**合成**，不是本卡自己跑出来的正控。
4. **未证明 `~/.codex/sessions/**` 与 `skills/.system/**` 的内容不含敏感信息** —— 只记路径与归因，不读内容。
5. **未证明 AGENTS.md 里那段手动接线说明会被用户正确执行**（文档类，不可测）。
6. **未证明 `.claude/skills/deploy-vault/SKILL.md` 的 `--hosts` 文案与脚本接受列表一致** —— 本卡不改该文档（§三），只登记。
7. **未证明「模板已存在则不动」在端口改变时是对的取舍** —— 重跑时若 `--port` 换了而模板已在，模板里的端口是**旧值**；
   脚本如实把动作词 `kept` 打进步 3 的那行消息，但**不会**提示端口已不一致。这是「不覆盖用户改动」的代价，登记。
8. **未证明 `$VAULT` 的祖先被换成软链时生成路径仍安全** —— `O_NOFOLLOW` 只挡末段；
   要闭合它得让步 1 的 fd 一路传到步 3，而步 1 是别的卡的定稿面。与 T2-C 的 `publish_agents_md` 是同一条残留窗口。
9. **未证明 manifest 那条 `exclude` 登记此刻真的拦得住什么** —— 见 (e)：`extra_scan` 够不到 `.codex/`，防护是**潜在**的。

---

## 台账待登记条目（主 session 写台账，本卡只列）

1. **Codex 转正为二线宿主**（read-only 形态，D-33）—— `deploy-vault.sh` 步 3 B4c 生成面 + 三门先红后绿 nodeid。
2. **`codex exec --sandbox read-only` 不写用户级信任表**的负控结论（sha before==after + 目录跑前跑后均缺席 + 信任表段数 17→17），
   以及「仅首次遇目录才写」这个**验伪陷阱**；⛔ 外加本卡实测的**第二个**空判据陷阱：
   **不带 `--skip-git-repo-check` 时 codex 在全新临时目录里直接拒跑（rc=1 / 零事件）**，那一趟的 sha-equal 同样什么都没证明。
3. **`.codex/config.toml` 是项目级模板、Codex 不自动读项目级 MCP** ⇒ 真连通性移交后续宿主卡 / U4 族。
4. **manifest 归属订正**：`.codex/config.toml` 本该与 `.agents/skills` / `AGENTS.md` 同族登成 `generate` 项，
   但那会打红 `test_vault_install_manifest.py` 的三条钉死门（generate 集要求 `install-vault.sh` 清理段有锚行），
   两个文件都在本卡地盘外 ⇒ 本卡登成 `exclude`，**归属订正移交** T7-D / 主 session。
   顺带：`extra_scan` 是否该纳入 `.codex/`（否则该登记恒为潜在）一并移交。
5. **D-26(i) 的 opencode 用户级配置覆盖面问题归 T2-C**，本卡只用既有 `$HOME/.codex` 保护，未改判据文件。
6. **Codex 各轮存档路径 / 绑定 SHA / B-H-M-L 计数**（见收工核验段）。
7. **`tests/unit` 目录级 diff 结果**（见收工核验段）。
8. **本卡顺带修掉的 locale 类缺陷**：`$VAR` 紧跟多字节字符会被 bash 把首字节吞进变量名（`set -u` 下 `unbound variable`）。
   已加整片词法门 `test_no_bare_var_before_multibyte`。⚠️ **这条值得推广**：本仓脚本大量中文文案，
   同型隐患在别的 shell 脚本里可能还有（本卡只扫了 `deploy-vault.sh`）。
9. **`.claude/skills/deploy-vault/SKILL.md`（仓根真名，R-B14-8）的 `--hosts` 文案在 codex 转正后过时**
   （`:40` 示例 `--hosts claude` / `:45`「本版只支持 claude」）—— 本卡不改、交 T2-B / 主 session 裁归口；
   同车道两卡说法不一（T2-B 卡文 `:117` vs T2-C 卡文 `:63`），需主 session 定写者。
10. **卡文 (c).3 的 A1 落点**：卡文写 Phase A，实测放那里首跑必失败 ⇒ 已落「生成后在位判」。
    若后续卡要真正的 Phase A 前置判据，需要另立（本卡不发明新判据形状）。
11. **本机无 `timeout` / `gtimeout`**（批中禁装工具）⇒ 墙钟上限统一用 `perl -e alarm` 包装器。
    建议写进手册，免得后续卡照抄卡文的 `timeout 900` 撞 `command not found: timeout`（rc=127，**看起来像判据跑过了**）。

---

## 收工核验

*（(h) 目录级 / (j) 地盘门 / (k) Codex 轮次与终审绑定 —— 见下方续写）*
