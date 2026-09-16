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

### (h) tests/unit 目录级 — 存档 `unit-close-20260917T032226.txt` + `unit-diff-20260917T032756.txt`

跑法（与基线**同口径**）：`cd backend && pytest tests/unit -q -p no:cacheprovider --ignore tests/unit/test_deploy_vault_sh.py`
⛔ `--ignore` 写**相对**路径（R-B14-3：已 `cd backend`，写绝对前缀 = 空操作，那个重型文件仍会真跑）。

| 项 | 实测 |
|---|---|
| 汇总 | 35 failed, 5077 passed, 48 skipped, 23 xfailed, 29 errors（290.40s） |
| `close.nodeids` 行数 | **64** |
| `base.nodeids` 行数（基线） | **64** |
| `diff base close` | **完全为空**（`diff_rc=0`） |
| `<` 行（基线有、本次没有） | **0** |
| `>` 行（本次新增 = 阻断） | **0** ✅ |

**两个验伪锚**（缺一不可，否则「零命中」可能只是 grep 没跑成）：

1. ⛔ grep 侧关色彩的 flag 是 `--color=never`，**不是** `--no-color`（后者只是 git 的 flag，
   `/usr/bin/grep` 不认 ⇒ rc=2 + stdout 空 ⇒ `close.nodeids` 写成空文件 ⇒ diff 只剩 `<` ⇒ **恒绿假绿**）。
   锚：`printf 'FAILED tests/unit/__probe__.py::t - X\n' | grep --color=never -E '^(FAILED|ERROR) tests/'`
   → 原样回显该行 + `rc=0` ✅
2. `test -s close.nodeids` → `rc=0`（非空）✅ —— 空 = 64 条既有红一次全消失，实务上等于 grep 没跑成。

### (j) 地盘门 — 存档 `territory-final-20260917T033*.txt`

```
PREV = 7a8d50e2b92d002700b64837a8b518a2ac5facc1   (T2-C tip)
HEAD = ef0cf1a9ff7bb8abee3485ca2981b2948dafa488
```

| 项 | 实测 |
|---|---|
| 代码面（`-- . ':(exclude)_bmad-output'`） | `scripts/deploy-vault.sh` / `backend/tests/unit/test_deploy_vault_sh.py` / `scripts/vault-install-manifest.json` —— **恰 3 件** |
| 越界文件数 | **0** ✅ |
| **验伪锚 ①** 去掉 exclude | 全部 25 − 代码面 3 = **22** 个 `_bmad-output/` 路径被排除 ⇒ pathspec 真的在工作 ✅ |
| **验伪锚 ②** 子集 grep | 喂一个已知越界名 `scripts/install-vault.sh` → 被列出来 + rc=0 ⇒ 判据不是恒空 ✅ |
| pathspec 写法 | `':(exclude)_bmad-output'`（**不是** `':!…'`，协议 §1：zsh + git 2.50 下后者 rc=128 假绿） |

> ⛔ **第一次跑这条判据我自己写错了**：`-c core.quotepath=false` 放在了 `diff` **之后**，
> git 当场 `fatal: bad revision 'core.quotepath=false'`，锚算出 `全部=0 / 差=-3`。
> 那一份（`territory-20260917T033*.txt`，无 `-final`）**作废**。
> 它恰好演示了验伪锚存在的理由：**没有锚，fatal 之后的空输出会被读成「干净」**。

### 提交

```
ef0cf1a9  feat(deploy): codex 转正为二线宿主, 步 3 生成项目级绑定件 [BATCH-2026-09-11-第十四批 / CARD-HOSTS-CODEX]
```

- header **84 字符**（`wc -m`）≤ 100，含批次标记 ✅ 含卡号 ✅
- 单独 commit，提交后 `git status --porcelain` = **0**（T2-E 开工前工作树干净）✅
- lefthook：`python-lint` ruff 全过 + format OK；`mutant-residue-scan` OK；`ghost-files` OK；
  `commitlint` 0 problems / 1 warning（`subject-case`，中文主题的既有告警，非阻断）
- `*.stderr*` / `*.log` 入库数 = **0** ✅　未 push ✅

### (k) Codex 复核

#### round-1 —— 绑定 `ef0cf1a9`，**BLOCKER 1 / HIGH 1 / MEDIUM 3 / LOW 0**

存档 `_bmad-output/审查/codex-review-CARD-HOSTS-CODEX.md`。逐条处置（**无一条驳回**）：

| # | 级别 | 意见 | 处置 |
|---|---|---|---|
| 1 | **BLOCKER** | 两处新目录打开 `os.open(vault/ddir, …\|O_NOFOLLOW)` 只挡末段；祖先在步 1 判据与步 3 之间被换成指向保护目录的软链时照样穿过去 | **已修**：改走仓内既有原语 `open_pinned`（① realpath 父目录后当场过 `hits()` 判据 ② 沿已校验物理串逐级 `O_DIRECTORY\|O_NOFOLLOW`）。不新发明判据形状，与脚本另外 3 处 python 写入同一来源 |
| 2 | **HIGH** | 探针为了证明结论**真的跑了 codex**，于是 codex 自己往 `$HOME/.codex` 写了 `sessions/**` 与 `skills/.system/**`；卡文 (f).7 只授权了 `sessions/**` | **已改**：探针改用 `CODEX_HOME` 重定向到 scratchpad（auth 用**软链**指向真文件，不复制密钥字节）⇒ `$HOME/.codex` **零写**。见下方「意外收获」 |
| 3 | **MEDIUM** | manifest 的 `exclude` 登记让**形态错误**逃过独立校验（generate 项会查「在位且是普通文件」） | **接受并更正措辞**：我原来把差异说成「只是三条测试会红」，**把损失说小了**。已在 manifest note 与测试 docstring 里如实写明放弃了哪条判据；归属订正仍是移交项（改不了，地盘外） |
| 4 | **MEDIUM** | 模板写入失败后截成 0 字节，下次跑走「已存在 ⇒ `kept`」，空模板被当成正常产物 | **已修**：失败时写 `INCOMPLETE` 标记；`kept` 分支先排除「空文件 / 带半成品标记」。加两条门 |
| 5 | **MEDIUM** | AGENTS.md 追加在**首锚写完整之前**失败，残件下次跑认不出来（找不到完整首锚 ⇒ 再追加一段并报成功） | **已修**：追加前记 `keep_size`，失败时 `ftruncate(fd, keep_size)` **回滚**到追加前的长度（O_APPEND 只往末尾写 ⇒ 截回去 = 逐字节恢复原状）。原来「不截断」的理由只对「截到 0」成立 |

#### ⛔ 我自己造了一条假门，并用敏感性负控抓了出来（存档 `gate-sensitivity-*.txt`）

为 BLOCKER 写的第一版是**行为门**（断言「rc 非 0 + 保护面零 `.codex`」）。
把 `open_pinned` 变回裸 `os.open` 之后，它**照样绿**：

- 真因：那一跑先撞步 3 A1「宿主绑定件缺失」（祖先被换掉后 `$VAULT/CLAUDE.md` 找不到），**根本没走到 codex 段**；
- 改造场景让 vault 可达之后，又被**更早**的 B3（写 `data.json`，同样走 `open_pinned`）先拒成 rc 73；
- ⇒ 该 TOCTOU（shell 侧复查 ↔ python 侧打开之间）**端到端不可确定性复现**。

处置：删掉假门，换成
1. **结构门** `test_codex_publishers_open_dirs_through_open_pinned` —— 禁止**按路径**的目录 `os.open`
   （相对已钉住 fd 的 `openat` 放行，两向验伪锚都在）。
   敏感性实测：**绿 → 变异后红（失败信息点名那两行）→ 还原后绿**，还原 sha256 与变异前逐字节相同。
2. **纵深门** `test_vault_under_protected_surface_is_refused_before_codex_stage` —— 如实标注它证的是
   「更早的判据先拒了」，不是本卡这个修复。

#### 🎁 整改 HIGH 时的意外收获：原「未证明 ③」被关掉了

原来因为 D-33 / D-26(i) 禁写用户级信任表，**正控跑不了**，验伪锚只能靠引用既有正控「合成」。
改用 `CODEX_HOME` 重定向之后，workspace-write 写的是 scratch 里那张表 —— 红线不破，正控变成本卡实测：

| 沙箱 | exec rc | 重定向 home 的 `[projects]` 段数 | 该目录是否进表 |
|---|---|---|---|
| `read-only` | 0 | **0 → 0（不变）** | 否 |
| `workspace-write` | 0 | **0 → 1（新增）** | 是，`trust_level = "trusted"` |

两臂都有 1 条已完成的 `command_execution`（`exit_code=0`）⇒ 前提成立，不是空判据。
全程真 `$HOME/.codex/config.toml` sha 与开工锚逐字相同。存档 `codex-sandbox-2x2-*.txt`。

⇒ 上面「本卡未证明什么 ③」应读作：**已由本卡实测关闭**（保留原文并在此标注，不改写历史）。

#### round-2 —— 绑定 `532cfed7`，**BLOCKER 1 / HIGH 1 / MEDIUM 2 / LOW 0**

存档 `codex-review-CARD-HOSTS-CODEX-r2.md`。r1 的整改**没有全部闭合**，逐条处置（仍无一条驳回）：

| # | 级别 | 意见 | 处置 |
|---|---|---|---|
| 1 | **BLOCKER** | r1 的修复只判到**父目录**：`HOME=/home/alice`、vault=`/safe/redirect/alice`，把祖先 `redirect` 换成指向 `/home` 的软链 ⇒ 父目录解析成 `/home`（不是保护目标）⇒ `open_pinned` 放行，而随后相对该 fd 建的 `.codex` 就是 `$HOME/.codex`。**「父目录允许」不蕴含「子路径允许」** | **已修**：新增 fd 落点守卫 —— 用 `F_GETPATH`（Linux 回退 `/proc/self/fd`，都拿不到就 fail-closed）取**已打开 fd 的物理路径**，再对「接下来真要写的每个名字」（`.codex` / `.codex/config.toml` / `AGENTS.md`）跑同一份 `hits()` 判据 |
| 2 | **HIGH** | 追加回滚没有互斥：采样长度后别人追加、本次失败回滚会**连对方的正文一起截掉**；两个写者也能各追加一段 | **已修**：① 取 `flock(LOCK_EX)` 把「读→判段→追加→回滚」整条串起来；② 回滚前判增量 —— `grown > append_len` 时**拒绝回滚**（多出来的只可能是别人写的，宁可留半截也不删别人的东西）。⚠️ flock 是协作式的，挡不住不取锁的进程，已登记 |
| 3 | **MEDIUM** | 清理**本身**也可能写到一半：只落下 `# <!-- I` 时既非空、也不 `startswith` 完整标记 ⇒ `kept` 分支放行 | **已修**：两向都判 —— 以完整标记开头 **或** 首行是标记的一段前缀，都认成残件 |
| 4 | **MEDIUM** | manifest `exclude` 仍放弃形态校验；「移交记录可解释为何未修，但不能视为关闭」 | **接受，保持开放**：本卡改不了（要动的两个文件在地盘外），作为移交项**不关闭**。协议对 MEDIUM 是登记不阻断 |

##### 两份手抄判据的处理

判据模块 `cls_forbidden_paths.py` 本卡禁改 ⇒ fd 落点守卫只能在两个 heredoc 里各抄一份。
「两份手抄的判据必然漂移」是本仓旧账，所以把**「两份必须逐字相同」做成门**
（`test_codex_fd_guard_copies_are_identical`，带恒真锚）。

##### round-2 三条新门的敏感性 —— 每条都实测过（存档 `gate-sensitivity-r3-*.txt`）

| 门 | 变异 | 绿 → 变异 → 还原 |
|---|---|---|
| `test_codex_publishers_judge_the_real_write_target` | 去掉模板发布器传入的落点名 | 绿 → **FAILED** → 绿 ✅ |
| `test_agents_append_takes_an_exclusive_lock` | 去掉排他锁 | 绿 → **FAILED** → 绿 ✅ |
| `test_codex_fd_guard_copies_are_identical` | 把其中一份守卫改一个字符（半角逗号→全角） | 绿 → **FAILED** → 绿 ✅ |

每轮还原后 `deploy-vault.sh` sha256 与变异前逐字节相同。

> ⛔ 顺带：`test_codex_publishers_judge_the_real_write_target` 第一版又踩了一次「判据自己没取全」——
> 正则写 `[^)]*` 在第一个 `)` 处截断，`(base,)` 被切成 `(base,`，门当场自红。
> 改成锚到完整参数尾 `, live, die)`，并补了两向验伪锚（对已知调用取得全 / 对函数定义行不命中）。

#### round-3 —— 绑定 `41ddf0d0`，**BLOCKER 1 / HIGH 2 / MEDIUM 3 / LOW 0**

存档 `codex-review-CARD-HOSTS-CODEX-r3.md`。逐条处置（**一条部分驳回并上交裁定，其余全接受**）：

| # | 级别 | 意见 | 处置 |
|---|---|---|---|
| 1 | **BLOCKER** | fd 守卫通过后，把 `.codex` 目录**改名**搬成 `$HOME/.codex`（同文件系统），后续相对 `cfd` 的写入就落进用户级配置；`F_GETPATH` 只是当次查询，冻结不了之后的位置 | **部分闭合 + 上交裁定**（见下） |
| 2 | **HIGH** | 探针把 `auth.json` 软链到真文件 —— 0.153.3 刷新令牌时会**沿软链截写**真实凭据；只核 `config.toml` 的 sha 看不到 | **已修**：改用 0600 **副本**，跑完当场清零；真 `auth.json` 与 `config.toml` 跑前跑后 sha 都核，均逐字相同 |
| 3 | **HIGH** | AGENTS.md **新建分支没参与互斥**：A 新建短写 → B 走已有文件分支取锁追加成功 → A 清理截零，把 B 的正文一起删掉 | **已修**：新建的那一份**从建出来就上锁**，B 的 `flock` 会等到 A 处理完（含清理）才拿到 |
| 4 | **MEDIUM** | 模板「正文只写到一半、清理也失败」仍会被当正常文件 `kept` | **已修**：`kept` 分支改**正向白名单** —— 完整模板必含 `[mcp_servers.` 段头，不含即残件。黑名单永远数不完 |
| 5 | **MEDIUM** | AGENTS.md 末尾的**半截段首**（`\n<!-- cls-codex`）连 `sec_mark` 都不命中 ⇒ 下次直接再追加一整段 | **已修**：判「末尾是否为 `\n`+首锚 的一段真前缀」 |
| 6 | **MEDIUM** | 三条结构门**把注释当真实调用** —— 换成 `pass  # 原调用` 之后全部照样绿（Codex 已实测） | **已修**：加 `_decomment()`（剥**行内**注释）并在它上面判。⚠️ 这是**真的假绿**，不是误报 |

##### 关于 BLOCKER 的部分驳回（车道不自判，交主 session 裁定）

**已做的收窄**：在建 `config.toml` **之前**对 `cfd` 自己再判一次（原来只判了 `vfd`），
把窗口压到「判 cfd → openat 叶子」这一小段。

**关不死的部分，如实说明**：
- 目录 fd 跟着 **inode** 走，`rename` 不换 inode ⇒ 任何「先判再用」的写法都挡不住
  「我手里这个目录在两步之间被搬走」。`F_GETPATH` 是当次查询，不是租约。
- 这**正是**判据模块 `open_pinned` 自己 docstring 里已登记为**未闭合**的那一类：
  「祖先被换成指向另一个非保护目录、或把祖先**改名/替换成真目录**仍可绕过
  （需要目录 fd 的稳定性前提或权限隔离）」。脚本另外**三处** python 写入同样暴露 ——
  这不是本卡引入的新洞，是本卡继承的既有面。
- 触发它需要攻击者能在 `$HOME` 里 `rename` 出 `$HOME/.codex`；**具备这个能力的人本来就能直接写那个文件**，
  所以该窗口不给攻击者任何新能力。
- 真正闭合它要么改判据模块（本卡禁改），要么给部署一个独立的挂载/权限隔离面 —— 都超出本卡范围。

⇒ 按协议「车道对 BLOCKER/HIGH 的驳回要写理由但**不能自判通过**」，此条**上交主 session 裁定**，
并作为移交项登记（连带 `open_pinned` 那条既有声明）。

##### round-3 新门与敏感性（存档 `gate-sensitivity-r4-comment-mutation-*.txt`）

用 **Codex 点名的那条注释变异**（`pass  # 原调用`，程序块语法仍有效、真实调用数归零）实测：

| | 结果 |
|---|---|
| 还原态 | 绿 |
| 注释变异后 | `test_codex_publishers_judge_the_real_write_target` **FAILED** + `test_agents_append_takes_an_exclusive_lock` **FAILED** ✅ |
| `bash -n` 变异态 | rc=0（证明变异真的生效，不是语法错顺带打红） |
| 还原后 | 绿，sha256 与变异前逐字节相同 |

新增行为门：`test_agents_refuses_truncated_section_head`（半截段首）、
`test_agents_normal_trailing_newline_is_not_a_residue`（**控制组** —— 没有它，把阈值写成 1 的版本
会「全都拒」却看起来很安全；本判据第一版正是这么把一条既有门打红的）、
`test_codex_template_rejects_body_without_section_header`、`test_structural_gates_are_not_fooled_by_comments`。

#### round-4 —— 绑定 `1d2d4b5b`，**BLOCKER 1 / HIGH 1 / MEDIUM 3 / LOW 1**

| # | 级别 | 意见 | 处置 |
|---|---|---|---|
| 1 | **BLOCKER** | 守卫过后把 `.codex` **改名搬走**，经旧 `cfd` 的写仍落进用户级配置 | **实质收窄**（见下「可落地性实测」） |
| 2 | **HIGH** | opencode 侧 `publish_agents_md` 不取锁 ⇒ 它短写暂停时 codex 侧追加成功，它的清理会把对方正文截掉 | **已修**：在它的新建路径加同一把 `flock`，**只加锁、不改它任何逻辑** |
| 3 | **MEDIUM** | `[mcp_servers.` 子串证不了完整（截断停在段头、或段头之后 url 之前） | **已修**：三条齐 —— 段头 + `url = "http://127.0.0.1:` 行 + 末尾换行 |
| 4 | **MEDIUM** | 结构门被**字符串字面量**骗过（`_decomment` 管不了字符串） | **已修**：判据改 **AST** 数真实 `Call` 节点 |
| 5 | **MEDIUM** | manifest `exclude` 仍放弃形态校验 | 保持开放，跨卡移交 |
| 6 | **LOW** | 半截段首阈值 5 漏掉 `\n<` / `\n<!` / `\n<!-` | **已修**：收到 **2**（能与「正常末尾换行」长度 1 区分的最小值） |

##### BLOCKER 的可落地性实测（存档 `resolve-beneath-probe-*.txt`）

Codex 说「未验证到可在本卡直接落地的闭合方案」。我没停在这句上，实测了两条候选：

| 候选 | 结果 |
|---|---|
| A：`O_RESOLVE_BENEATH`（若内核支持则保证解析不逃出 fd） | ⛔ 本机**静默忽略** —— 带不带它，逃出去的软链都照写不误 ⇒ **不可用**（写上去只是个不起作用的 flag，DD-13） |
| B：**不跨写入持有 `.codex` 的目录 fd**，叶子按 `.codex/config.toml` 相对 `vfd` 打开 | ✅ **有效** —— 同一「目录被搬走」场景下，旧 fd 写成功、按路径打开变 `ENOENT` |

采用 B，另补「写第一个字节之前判一次那个**文件 fd** 的物理路径」（三处）。
⚠️ 去掉目录 fd 会丢掉「`.codex` 是软链 ⇒ ELOOP」这条**已有**性质 ⇒ 用显式 `lstat` 判回来
（不拿新修复换掉一条旧规则 —— 这是本仓的旧账）。

#### round-5（协议轮次上限）—— 绑定 `afacca52`，**BLOCKER 2 / HIGH 0 / MEDIUM 2 / LOW 0**

| # | 级别 | 意见 | 处置 |
|---|---|---|---|
| 1 | **BLOCKER** | ① 多段路径的 `O_NOFOLLOW` **只管末段** —— `.codex` 是指向保护面的软链时文件会被建进去；② 守卫**拒绝之后** `finally` 仍执行截断 + 写 INCOMPLETE 标记。Codex 明确标注「**本卡内可修**」并给了写法 | **已修**（见下） |
| 2 | **BLOCKER** | 文件打开**之后**目录再被搬走，fd 仍指原 inode ⇒ 下一次写落在禁写面。Codex：「任意并发搬移仍缺少本卡内已验证的闭合方案，**需要主 session 裁定**」 | **交主 session 人裁**（车道不自判） |
| 3 | **MEDIUM** | AST 门把 `if False:` 里的调用也算数；另有 `getattr` 间接写不被发现 | **前半已修**（常量假分支整棵剪掉并做成反例）；后半（一般可达性 / 间接调用检测）**登记移交** |
| 4 | **MEDIUM** | manifest `exclude` 形态校验缺口 | 保持开放，跨卡移交 |

##### BLOCKER-1 的处置：先独立实测，再采信

⛔ 没有直接照搬 Codex 的写法 —— 先自己跑了隔离探针（`nofollow-any-probe-*.txt`）：

| 场景 | 只带 `O_NOFOLLOW` | 带 `O_NOFOLLOW_ANY` | 两个同时带 |
|---|---|---|---|
| `.codex` 是指向保护面的软链（**中间段**） | ⛔ **文件被建进保护面** | ✅ `ELOOP` | `EINVAL` |
| 正常非软链路径（控制组） | 建出来 | ✅ 建出来（不误拒） | — |
| **叶子**本身是软链 | `ELOOP` | ✅ `ELOOP`（是 `O_NOFOLLOW` 的超集） | — |

⇒ Codex 的诊断与修法都成立，且「两个 flag 不能叠加」这条细节也复现了。已把四处多段路径 open
换成 `_NOFOLLOW_ANY`（Darwin 专有，非 Darwin 退回 `O_NOFOLLOW` 并如实写明退化面）。
后半（拒绝后仍写）加 `refused` 标志，两个发布器的失败清理都先判它。

##### ⛔ 第三次栽在同一件事上，写死在这里

为 BLOCKER-1 写的**行为门**（`.codex` 静态就是指向保护面的软链）在变异下**照样绿** ——
因为那种静态形态会被**步 1 的 `check_forbidden_paths` 先拒**，走不到步 3。
已把它如实降级标注为**纵深门**；本修复的敏感性由**结构门**
`test_codex_publishers_use_nofollow_any_for_multiseg_paths` 承担，实测绿 → 变异后红 → 还原后绿。

本卡三次同型：祖先软链门、保护面纵深门、中间段软链门 —— 都是「行为门绿在更早那道判据上」。
教训已写进门的 docstring 与 `gate-sensitivity-r6-*.txt` 的归因段。

##### 轮次结算（协议 D-15）

| 轮 | 绑定 | B | H | M | L |
|---|---|---|---|---|---|
| r1 | `ef0cf1a9` | 1 | 1 | 3 | 0 |
| r2 | `532cfed7` | 1 | 1 | 2 | 0 |
| r3 | `41ddf0d0` | 1 | 2 | 3 | 0 |
| r4 | `1d2d4b5b` | 1 | 1 | 3 | 1 |
| r5 | `afacca52` | 2 | **0** | 2 | 0 |

⛔ **协议轮次上限 = 5，已用尽 ⇒ 不再发起第 6 轮。** r5 之后仍做了整改（BLOCKER-1 已修、
MEDIUM-1 前半已修），所以**最后一轮存档不绑最终 HEAD** —— 这一条如实登记，
按协议交**主 session 人审**，连同下面这条待裁项。

##### ⛔ 待主 session 裁定（车道不自判）

**r5 BLOCKER-2：文件打开之后目录被并发搬走。** 双方的事实陈述已收敛，分歧只在「怎么处置」：

- 本卡做到的：候选 B 消掉了「打开前目录已搬走」那条路径；`_NOFOLLOW_ANY` 消掉了软链解析那条；
  写前三处 fd 物理路径判据把窗口压到最小；拒绝后零写。
- 关不死的：`rename` 不换 inode，「判据 → 下一次 write」之间没有可用内核原语
  （`O_RESOLVE_BENEATH` 本机实测被忽略）。**Codex 自己也说未验证到本卡内可落地的闭合方案。**
- 同源既有面：判据模块 `open_pinned` 的 docstring 早已把这一类登记为**未闭合**，
  脚本另外三处 python 写入同样暴露 —— 但 ⚠️ Codex 的反驳也成立：**本卡新增了受其影响的写入路径**，
  「既有面」不能当免责。
- 触发它需要攻击者能在 `$HOME` 里并发 `rename`；具备该能力者本来就能直接写那个文件。

⇒ 请主 session 在「按残留面登记合入」与「扩大到隔离/权限整改（超出本卡范围）」之间裁定。
