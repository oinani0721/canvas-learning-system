# CARD-HOST-PROBE — 三家二线宿主 + Claude Code + 后端 `/mcp` 宿主实测表

> **批次**：`[BATCH-2026-09-07-第十三批 / CARD-HOST-PROBE]` · 车道 `card-u4-hosts`（分支 `card/u4-hosts`）
> **开工**：2026-09-08 06:43 CST · **收工**：2026-09-08 07:18 CST · **绑定**：`da690bf8`（本卡零代码，HEAD 与 `da690bf8` 只差 `_bmad-output/**`）
> **证据根**：`_bmad-output/审查/evidence-host-probe/`（49 份，每条探针 `2>&1 | tee` + 末行 `rc=`）
> **探针 vault**：`$PV = <session scratchpad>/host-probe/probe-vault`（无 `.git` 祖先，不入库；目录清单见 `evidence-host-probe/P0-skeleton-20260908T065021.txt`）
> **遮蔽约定**：`claude mcp list` / `codex mcp list` 的输出含用户级配置内容，evidence 中非本卡自建条目的 command/args/URL 一律替换为 `<redacted-user-scope>`，原始输出留 session scratchpad 不入库；本表只引条目**计数**与本卡自建条目。

---

## 〇 开工快照（完成条件 (a)）

| 项 | 勘探值（卡文 §〇） | 实测值 | 证据 |
|---|---|---|---|
| `dsh` | 0.1.1-rc.2 | **0.1.1-rc.2** | `evidence-host-probe/versions-20260908T064311.txt:8` |
| `codex` | codex-cli 0.153.3 | **codex-cli 0.153.3** | `evidence-host-probe/versions-20260908T064311.txt:10` |
| `opencode` | 1.18.27 | **1.18.27** | `evidence-host-probe/versions-20260908T064311.txt:12` |
| `claude` | 2.1.263 | **2.1.263 (Claude Code)** | `evidence-host-probe/versions-20260908T064311.txt:14` |
| 车道树身份 | — | `pwd` 正确 / 分支 `card/u4-hosts` / HEAD `da690bf8` / `git status --porcelain` = 0 行 / `backend/.venv/bin/pytest` 与 `backend/.env` 均在 | 本表 §五 台账 ① |
| 后端 `/api/v1/health` | 未知 | **200**（docker 容器 LISTEN 127.0.0.1:8011） | `evidence-host-probe/backend-health-20260908T064311.txt:2` |
| 配置面 (i) 五行 sha | — | 4 sha + 1 `ABSENT`（`~/.config/opencode/opencode.json` 不存在） | `evidence-host-probe/userconf-sha-before.txt` |
| 运行期状态面 (ii) | — | 3194 行，含 `~/.config/opencode`（空目录）/ `~/.codex/sessions` / `~/.claude.json` / `~/.claude/projects` 四类 | `evidence-host-probe/runtime-state-open-20260908T064311.txt` |

**四家版本与勘探值逐字一致，无偏差。** 后端在跑 ⇒ P2 / P5 / P7 / P9 的运行期面**可测**（无 NOT-RUN 因后端不在跑而产生）。

---

## 一 表 A — 宿主 × 能力维度

> 「认哪个根」列的对照基准：`$PV`（无 `.git` 祖先）与 `<车道树>/canvas-vault/`（祖先 = worktree 的 `.git` **文件**）。

| 维度 | **Claude Code** 2.1.263 | **Codex** 0.153.3 | **OpenCode** 1.18.27 | **dsh** 0.1.1-rc.2（`--profile web`） |
|---|---|---|---|---|
| **认哪个根** | cwd 级 **+ git 根级**两个根；`.git` 为 worktree **文件**时同样识别。`$PV` 无 git 祖先 ⇒ 只认 cwd 一层<br>`evidence-host-probe/P10c-claude-root-20260908T071420.txt:10` / `evidence-host-probe/P4a2-claude-skills-debug-20260908T070258.txt:5` | **无内建根解析可观测**——模型自行 `rg --files --hidden` 遍历 cwd 子树<br>`evidence-host-probe/P6a-codex-readonly-20260908T070528.txt:9` / `evidence-host-probe/P10b-root-detection-dsh-codex-20260908T071333.txt:20` | cwd 级 **+ git 根级**，与 Claude Code 同（条目数交叉吻合，见下）<br>`evidence-host-probe/P10a-root-detection-vault-20260908T071259.txt:18` | 包文档称 projectRoot = 最近含 `.git` 的祖先、否则 cwd（`dsh-skill-filesystem/README.md:41,:72`）；**运行期未实测**——`--dump-config` 在 `$PV` 与 `canvas-vault` 下**逐字节相同**，不含已解析路径<br>`evidence-host-probe/P10b-root-detection-dsh-codex-20260908T071333.txt:8` |
| **读哪些 skills 目录** | `managed` + `user=~/.claude/skills` + `project=[cwd/.claude/skills, gitroot/.claude/skills]`<br>`evidence-host-probe/P4a2-claude-skills-debug-20260908T070258.txt:5` | **无 skills 发现机制**（0.153.3 未展示）；「能列出」= 模型用 shell 工具读目录<br>`evidence-host-probe/P6a-codex-readonly-20260908T070528.txt:9` | built-in + `~/.claude/skills` + 项目级 `.agents/skills`、`.claude/skills`、`.opencode/skills` **三处**（二进制常量与 location 双证）<br>`evidence-host-probe/P8-opencode-20260908T071157.txt:29-31` | `skill-filesystem` 在 web profile 下 **`disabled: true`**（被 `dsh-web-app` bundle 关掉）⇒ 该形态下**不读任何 skills 目录**<br>`evidence-host-probe/P1b-dsh-sandbox-skills-20260908T065245.txt:33-35` |
| **软链形态** | **整目录软链**与**条目级软链**均被扫；计数精确对应（3 / 1）<br>`evidence-host-probe/P4a2-claude-skills-debug-20260908T070258.txt:8` vs `evidence-host-probe/P4b-claude-skills-symlink-entry-20260908T070335.txt:15` | n/a（无发现机制） | 整目录软链被解析（location 落到 `.agents/skills/…` 与 `.claude/skills/…`）<br>`evidence-host-probe/P8-opencode-20260908T071157.txt:29-31` | 未测（插件禁用） |
| **skill 命名口径** | 用**目录名**；不校验 frontmatter `name` 是否 kebab-case<br>`evidence-host-probe/P4a2-claude-skills-debug-20260908T070258.txt:18-21` | n/a | 用 **frontmatter `name`**；同样不校验 kebab-case<br>`evidence-host-probe/P8-opencode-20260908T071157.txt:41-45` | 包文档要求 frontmatter `name` kebab-case（`README.md:55`）；未运行期实测 |
| **MCP 怎么绑**（＝怎么连上学习后端） | 项目级 `.mcp.json`（`type:"http"`）**被读到**，但状态 **`⏸ Pending approval`**，不自动启用<br>`evidence-host-probe/P5-claude-mcp-list-20260908T070048.txt:28` | **项目级 `.codex/config.toml` 未被读取**：`codex mcp list` 条目数 8 == `~/.codex/config.toml` 段数 8，本卡自建条目**零出现**<br>`evidence-host-probe/P7-codex-mcp-list-20260908T070457.txt:20-22` | 项目级 `opencode.json` 被读且**自动连上**（`✓ connected`），无需批准<br>`evidence-host-probe/P8-opencode-20260908T071157.txt:9` | `--patch` 的 `- insert:` 层可注入 MCP 条目并真连（见表 B P2）<br>`evidence-host-probe/P1a-dsh-dumpconfig-r2-20260908T065219.txt:15-20` |
| **沙箱缺省** | 未测（非本卡范围） | `--sandbox` 显式传入；两模式行为已分层验证（见表 B P6） | 未测（`--auto` 未启用，模型侧 NOT-RUN） | **composed tree 实测 = `DSH_PERMISSION_MODE ?? 'workspace-write'`**，与包文档 `README.md:13` 的「Default `read-only` (fail-safe)」**不一致**<br>`evidence-host-probe/P1b-dsh-sandbox-skills-20260908T065245.txt:8` vs `evidence-host-probe/P1b-dsh-sandbox-skills-20260908T065245.txt:52` |
| **写 vault 是否弹审批** | 未测 | 无审批层，直接由沙箱裁决（`operation not permitted`） | 未测 | 配置面 `approval.policy` = `(… ?? 'workspace-write') === 'danger-full-access' ? 'never' : 'ask'` ⇒ **workspace-write 下仍是 `ask`**；运行期 NOT-RUN<br>`evidence-host-probe/P3-dsh-write-approval-20260908T071227.txt:25-33` |
| **宿主副作用** | 每跑一次在 `~/.claude/projects/**` 落会话记录（(ii) 面，预期内） | **`--sandbox workspace-write` 会写 `~/.codex/config.toml` 的 `[projects]` trust 表**（read-only 不写）——命中 D-26 (i) 硬禁写面，见 §三.7<br>`evidence-host-probe/causal-codex-writes-config-r2-20260908T071710.txt:20-22` | `~/.codex/sessions` 无关；本卡窗口内未见 `~/.config/opencode` 新建物（收工仍 `ABSENT`） | **每次启动（含 `--dump-config`）原样重写 `~/.dsh/profiles/web/cordis.yml`**：mtime 变、sha 不变<br>`evidence-host-probe/P2d-dsh-side-effects-20260908T065658.txt:5-11` |

### 交叉印证
在 `<车道树>/canvas-vault/` 同一位置，Claude Code 报 `project: 15`、OpenCode 报「来自车道树的条目数 = 15」——两家**独立实现**给出**同一数字**（`canvas-vault/.claude/skills` 9 份 + 车道树根 `.claude/skills` 6 份），互为佐证。
`evidence-host-probe/P10c-claude-root-20260908T071420.txt:11` / `evidence-host-probe/P10a-root-detection-vault-20260908T071259.txt:18`

---

## 二 表 B — P0~P10 逐条三态

| # | 探针 | 关键观测 | 三态 | 证据 |
|---|---|---|---|---|
| **P0** | 探针 vault 无 `.git` 祖先 | `fatal: not a git repository`，**rc=128**；正控：车道树同命令 rc=0 ⇒ 判据非恒真 | **CONFIRMED** | `evidence-host-probe/P0-skeleton-20260908T065021.txt:5,8` |
| **P1** | dsh 列 skills + 认根 | ① `--patch` 的 `- insert:` 语法生效：`id: mcp-cls` / `url…8011` / `failOnStartupError: true` 各命中 1，无 patch 态命中 0，8999 态命中 8999 ⇒ 四态判据全绑字面量<br>② `skill-filesystem` 在 web profile 下 `disabled: true` ⇒ **该形态不读 skills**<br>③ `--dump-config` **不建立 MCP 连接**（死端口 + `true` 仍 rc=0；命中数与端口存活无关，经验伪锚排除自匹配） | ①**CONFIRMED** ②**CONFIRMED** ③**CONFIRMED**<br>「运行期列出 skill 名」**NOT-RUN**（web profile 无问答通道，见 P3 (1)） | `evidence-host-probe/P1a-dsh-dumpconfig-r2-20260908T065219.txt:15-20` / `evidence-host-probe/P1b-dsh-sandbox-skills-20260908T065245.txt:33-35` / `evidence-host-probe/P1c-dumpconfig-no-mcp-connect-20260908T065401.txt:28` |
| **P2** | dsh `--patch` 连 `/mcp` + `failOnStartupError` | 三态：8011+`true` ⇒ `dsh web: …:55326`、rc=142(被闹钟终止)；8999+`true` ⇒ **rc=1 自行退出**、`ECONNREFUSED 127.0.0.1:8999`、错误链落到 `dsh-mcp-client/lib/index.js:782`、**无** web 行；8999+缺省 ⇒ `dsh web: …:55546`、rc=142。<br>工具面：`tools/list` 返回 6 个只读工具含 `check_backend_health`；白名单工具实调 `isError=False`、1 个 content 块 | **CONFIRMED**（含断连对照与假绿面实证） | `evidence-host-probe/P2a-dsh-mcp-8011-20260908T065433.txt:6` / `evidence-host-probe/P2b-dsh-mcp-8999-failtrue-20260908T065518.txt:11` / `evidence-host-probe/P2c-dsh-mcp-8999-faildefault-20260908T065544.txt:5` / `evidence-host-probe/P2e-mcp-tools-list-20260908T065850.txt:15` / `evidence-host-probe/P2f-mcp-health-call-20260908T065913.txt:9` |
| **P3** | dsh workspace-write 写 vault / 审批 | 运行期不可达：`--profile web` 只 serve 浏览器 UI（flags 仅 `--host/--no-open/--port/--trusted-host`），无一问一答通道；`--profile headless` 所需 profile 目录在 `~/.dsh/profiles` **不存在**，新建 = 写 (i) 配置面 ⇒ 不做。<br>配置面：`approval` 在 workspace-write 下 = `ask`（只有 `danger-full-access` 才 `never`） | 运行期 **NOT-RUN**（web profile 无问答通道 / headless profile 需写用户级配置）<br>卡文期望「workspace-write 不弹审批」**REFUTED**（配置面口径） | `evidence-host-probe/P3-dsh-write-approval-20260908T071227.txt:3,25-33` / `evidence-host-probe/helpcheck-dsh-web-20260908T064500.txt` |
| **P4** | Claude Code 软链是否被扫 | 整目录软链：`project: 3`，模型列出 `probe-skill` / `bad-name` / `bad skill`；条目级软链：`project: 1`，只列 `probe-skill`。两态计数与模型输出双向一致。<br>反假阳性：文件工具全禁、`permission_denials: []`、`num_turns: 1` ⇒ 名单来自系统注入而非模型读目录 | **CONFIRMED**（两态均成立） | `evidence-host-probe/P4a2-claude-skills-debug-20260908T070258.txt:5,8` / `evidence-host-probe/P4b-claude-skills-symlink-entry-20260908T070335.txt:15` / `evidence-host-probe/P4a-claude-skills-symlink-dir-20260908T070137.txt` |
| **P5** | Claude Code 项目级 `.mcp.json` | 条目出现、url 与 type 正确识别为 HTTP，状态 `⏸ Pending approval (run \`claude\` to approve)`；负控：未配置的假名零出现 | **CONFIRMED**（读到但不自动启用） | `evidence-host-probe/P5-claude-mcp-list-20260908T070048.txt:28,31-33` |
| **P6** | Codex 认根 + 沙箱 | 2×2 矩阵：<br>read-only × `outputs/`（普通）→ **拒**；read-only × `.agents/`（隐藏）→ 拒；workspace-write × `outputs/` → **成功**；workspace-write × `.agents/` → 拒。<br>拒因串四格逐字相同（`zsh:1: operation not permitted`），但唯一成功格把两层分开：**沙箱模式层**与 **dot-directory 路径规则层**各自独立成立。文件系统独立判据（EXISTS/ABSENT）与模型自述一致 | **CONFIRMED**（两层均归位） | `evidence-host-probe/P6a-codex-readonly-20260908T070528.txt:15` / `P6b-…` / `evidence-host-probe/P6c-codex-write-target-layer-20260908T070744.txt:19` / `evidence-host-probe/P6d-codex-readonly-plaindir-20260908T070851.txt:12` |
| **P7** | Codex MCP 项目级 vs 用户级 | `codex mcp list` 条目数 **8** == `~/.codex/config.toml` 的 `[mcp_servers.*]` 段数 **8**；本卡自建的项目级条目**零出现** | **CONFIRMED**（比「回落」更强：项目级根本未被读取） | `evidence-host-probe/P7-codex-mcp-list-20260908T070457.txt:20-22` |
| **P8** | OpenCode 双位置是否重复 | `probe-skill` 同时存在于 `.opencode/skills/` 与 `.claude/skills/`(→`.agents/skills/`)，`opencode debug skill` 中**只出现 1 次** ⇒ **不重复**。<br>MCP：`✓ canvas-learning-mcp connected` 与 `✗ probe-dead-mcp failed`（8999 负控）两状态不同 ⇒ `mcp list` 是真去连而非回显配置 | 「是否重复」**REFUTED（不重复）**<br>MCP 绑定 **CONFIRMED**<br>模型侧「能否使用 skill」**NOT-RUN**（本机 OpenCode 未配置 provider 凭据，配置它 = 写 (i) 配置面） | `evidence-host-probe/P8-opencode-20260908T071157.txt:9,36,49-51` |
| **P9** | 后端 `/mcp` HTTP vs SSE | POST `initialize` = **200**，返回会话标识与 `serverInfo.name=canvas-learning-mcp`；GET `/mcp` 无会话标识 = **400 `Missing session ID`**，带会话标识 = 6s 内零字节 rc=28（流保持打开，**非拒绝**）；旧式 SSE transport 端点 `/sse`、`/mcp/sse`、`/messages` 全 **404** | **CONFIRMED**（但结论须分两层，见 §三.6） | `evidence-host-probe/P9-backend-mcp-http-vs-sse-20260908T065732.txt:7,29` / `evidence-host-probe/P9b-sse-rejection-layer-20260908T065803.txt:15,19-22` |
| **P10** | 三家认根对照 | `$PV`（无 git 祖先）：Claude Code `project` 1 个根；OpenCode 只认 cwd 层。<br>`canvas-vault`（`.git` 是 worktree **文件**）：Claude Code `project` **2 个根**、15 条；OpenCode 同样跨 cwd 级与 git 根级、15 条；Codex 仍靠模型 `rg`；dsh dump 两处**逐字节相同**。<br>跑后 `git status --porcelain -- canvas-vault/` = **0 行** | **CONFIRMED**（含「`.git` 文件被当祖先」观测）<br>⚠️ **偏离登记**：用车道树 vault 替代 live（卡文 §一(c) 授权） | `evidence-host-probe/P10a-root-detection-vault-20260908T071259.txt:18` / `evidence-host-probe/P10b-root-detection-dsh-codex-20260908T071333.txt:8,20` / `evidence-host-probe/P10c-claude-root-20260908T071420.txt:10-11` / `evidence-host-probe/P10d-post-check-20260908T071449.txt:4` |

**三态计数**：CONFIRMED **11**（P0/P1×3/P2/P4/P5/P6/P7/P9/P10） · REFUTED **3**（P3 审批期望 / P8 重复 / 另见 §三.1） · NOT-RUN **4**（P1 运行期列 skill / P3 运行期 / P8 模型侧 / dsh 认根运行期）。

---

## 三 决策页 §三 更正清单

| # | 决策页/卡文原表述 | 实测 | 判定 |
|---|---|---|---|
| 1 | dsh 沙箱「workspace-write(默认)」；卡文 §〇 据包文档更正为 **read-only** | composed profile tree 实测 `mode: !!js process.env.DSH_PERMISSION_MODE ?? 'workspace-write'`。**包文档缺省（read-only）≠ 产品缺省**——`dsh-base` bundle 显式把它设成 workspace-write | **决策页原文 CONFIRMED；卡文 §〇 的「更正」本身 REFUTED**（更正是对包文档而非对产品形态） |
| 2 | §三 未提 `failOnStartupError` 缺省 false 的假绿面 | 三态实证：8999+缺省与 8011+`true` 的**外部可观测行为逐字同形**（都打印 `dsh web: http://…`、都 rc=142），但前者 MCP 未连上；8999+`true` 则 rc=1 并明确报 `ECONNREFUSED` | **CONFIRMED（假绿面真实存在）** — 决策页应补记；另：patch 写错 id 时 dsh 只 `warn` 且 **rc 仍为 0**，是第二重静默 |
| 3 | Claude Code「整目录软链未验」 | 整目录 `project: 3` / 条目级 `project: 1`，两态均被扫，计数精确 | **CONFIRMED（两种软链形态都支持）** |
| 4 | Codex「未受信回落用户级」 | `codex mcp list` 只列用户级 8 条，项目级零出现 | **CONFIRMED**，且表述可加强为「项目级 `.codex/config.toml` 未被读取」 |
| 5 | OpenCode「三处都读 → 是否重复」 | 三处都读（二进制常量 + location 双证），但同名 skill **按 name 去重**，`probe-skill` 只出现 1 次 | **「三处都读」CONFIRMED；「会重复」REFUTED** |
| 6 | `.claude/mcp.json` `_doc` 说 SSE → 后端只 HTTP | 需分两层：**旧式 HTTP+SSE transport（独立 `/sse` + `/messages` 端点）确实未挂载**（三个端点全 404）⇒ `type:"sse"` 死配置结论成立；但 **streamable-http 的 GET `/mcp` 上行流端点是存在的**（无会话标识 400、带会话标识则保持流），并非「GET 必然非 200」 | **CONFIRMED（死配置结论成立）**，但卡文「GET SSE ≠ 200（预期 405/404）」的**静态推断口径需更正** |
| 7 | *（本卡新增）* D-26 (i) 把 `~/.codex/config.toml` 列为硬禁写 | `codex exec --sandbox workspace-write` **必然**在其中追加 `[projects."<dir>"]` trust 记录（正控 r2 写入 / 负控 r1 read-only 不写 / 对照 `[mcp_servers.*]` 恒 8） | **D-26 (i) 该项与宿主行为冲突**：任何用 codex workspace-write 的卡都会触发该阻断（假阻断）。**提请主 session 裁定**，本卡不自判放宽 |
| 8 | *（本卡新增）* 卡文 §三 废弃「整目录 `ls -laR`」口径的理由 | dsh **每次启动（含 `--dump-config`）都原样重写** `~/.dsh/profiles/web/cordis.yml`：mtime 06:52→06:55，**sha 逐字节未变** | **卡文该决定 CONFIRMED**：mtime/整目录口径会把它判成配置被改（假阻断），sha 口径正确判为未变 |

---

## 四 二线转正建议（**不裁**，供下一批 `--hosts` 排卡）

| 宿主 | 建议 | 依据与前置条件 |
|---|---|---|
| **OpenCode** | **可**（三家中最接近开箱可用） | 项目级 `opencode.json` 的 MCP **自动连上**、无需批准（`evidence-host-probe/P8-opencode-20260908T071157.txt:9`）；skills 三处都读且按 name 去重（`evidence-host-probe/P8-opencode-20260908T071157.txt:36`）。⚠️ 前置：本机**未配置 provider 凭据**，模型侧完全未验（`evidence-host-probe/P8-opencode-20260908T071157.txt:49-51`）；且命名口径用 frontmatter `name`，与 Claude Code 的目录名口径**不同** ⇒ 需 U4-B lint 先收口 |
| **Codex** | **待**（可用于只读审查，不宜作 skills 宿主） | 无 skills 发现机制，「能列出」全靠模型 `rg`（`evidence-host-probe/P6a-codex-readonly-20260908T070528.txt:9`）；项目级 MCP 配置不被读取（`evidence-host-probe/P7-codex-mcp-list-20260908T070457.txt:20-22`）；受信路径需改 `~/.codex/config.toml` = (i) 禁写面，**本卡未验**。⚠️ 且 workspace-write 会写用户级 config 的 trust 表（§三.7） |
| **dsh** | **待**（当前 D-24 形态不成立） | `--profile web` 下 `skill-filesystem`/`tool-skill`/`skill-badge` 全部 `disabled: true`（`evidence-host-probe/P1b-dsh-sandbox-skills-20260908T065245.txt:33-41`）⇒ **该形态根本不读 skills**；且 web profile 无一问一答通道 ⇒ P3 全程 NOT-RUN。MCP 侧则**可用**且 `failOnStartupError: true` 能说话（`evidence-host-probe/P2b-dsh-mcp-8999-failtrue-20260908T065518.txt:11`）。**下一批需先裁 headless profile 形态**（新建 profile 目录属用户级配置面，须用户授权） |

---

## 五 本卡未证明什么

1. **不证明** Codex / OpenCode 在**受信**项目下的行为——受信需改用户级配置（(i) 禁写面），本卡不做。
2. **不证明** dsh `web` profile 之外（`tui` / `headless` 等）的发现规则；`~/.dsh/profiles` 本机只有 `web`。
3. **不证明** dsh 的 **认根**（projectRoot 解析）——`--dump-config` 在 `$PV` 与 `canvas-vault` 下逐字节相同、不含已解析路径，且 web profile 下 skills 插件被禁用，认根无实际效果。仅有包文档 `README.md:41,:72` 的说法。
4. **不证明** dsh 的 read-only 与 workspace-write **拒因是否可区分**——P3 运行期 NOT-RUN。Codex 侧的 2×2 分层结论**不能外推到 dsh**。
5. **不证明** P3「workspace-write 写 vault 弹审批」的**运行期**行为——§三 的 REFUTED 仅基于配置面表达式求值。
6. **不证明** dsh 侧公开工具名 `mcp__canvas-learning-mcp__check_backend_health` **确实被注册**——该名由包文档规则（`README.md:5,:55`）+ 后端返回的原始工具名**推导**得出；dsh web UI 内的工具清单未观测。已证的是：激活成功（P2-a，由 P2-b 的 rc=1 反证其强度）+ 激活流程含 `listTools()`（P2-b 错误文本）+ 后端确实提供该工具（P2-e/P2-f）。
7. **不证明** ChatGPT 桌面端 primary folder 发现（E-5 L1，不在本卡范围）。
8. **不证明** live vault（主仓 `.git` **目录**祖先）下的行为——P10 用车道树（`.git` **文件**）替代，已登记为偏离。
9. **不证明** OpenCode「模型能否**使用** skill」——provider 凭据缺失，模型侧 NOT-RUN；只证「宿主能发现」。
10. **不证明** 真 skill（9 份，含 `allowed-tools` 等）在二线宿主里**能跑**，只证「能被列出」（可跑性是 U4-B 与下一批 `--hosts` 卡的面）。
11. **不证明** 探针 vault 的观测对「有 `.git` 祖先的用户 vault」全部成立——P10 只覆盖了 skills 发现与认根两维。
12. **不证明** (ii) 运行期状态面的新增文件里没有敏感内容——**只记路径名与时刻，不读内容**。
13. **不证明** OpenCode 的向上遍历边界**就是** git 根——已知 `$PV`（无 git 祖先）只认 cwd 一层、`canvas-vault` 认到车道树根，两点与「git 根为界」一致，但未构造「有 git 祖先但更深层次」的第三个对照。

---

## 六 台账待登记条目

1. **实测表**：`_bmad-output/研究/2026-09-08-HOST-PROBE-宿主实测表.md`；表 A 8 行 × 4 宿主，表 B 11 行；三态计数 **CONFIRMED 11 / REFUTED 3 / NOT-RUN 4**（NOT-RUN 原因均为宿主形态限制或凭据缺失，**无一条**因后端不在跑）。
2. **决策页 §三 更正清单 8 条**（§三）——其中 **#1 反转**：dsh 沙箱缺省，决策页原文「workspace-write(默认)」**正确**，卡文 §〇 据包文档做的「更正为 read-only」**不成立**（包文档缺省 ≠ 产品 composed tree 的显式值）。
3. **二线转正建议三行（不裁）**：OpenCode = 可（附 provider 凭据与命名口径两个前置）；Codex = 待（无 skills 机制 / 项目级 MCP 不读）；dsh = 待（web profile 下 skills 全禁 + 无问答通道，需先裁 headless 形态）。
4. **四家版本实测值**与勘探值逐字一致；**D-24 形态部分不成立**——`--profile web` 可用于 MCP 面（P1/P2 成立），但**不能**用于 skills 面与写入面（P1 skills / P3 全 NOT-RUN）。
5. **P10 偏离**（车道树替代 live）+ 「`.git` **文件**（worktree）被 Claude Code 与 OpenCode 当作项目根边界」观测；两家在同位置条目数同为 **15**，交叉印证。
6. **宿主副作用清单**：① dsh 每次启动（含 `--dump-config`）原样重写 `~/.dsh/profiles/web/cordis.yml`（mtime 变、sha 不变）；② `codex exec --sandbox workspace-write` 追加 `~/.codex/config.toml` 的 `[projects]` trust 记录；③ Claude Code 每跑一次在 `~/.claude/projects/**` 落会话记录；④ `~/.codex/sessions/2026/09/08/` 新增 rollout 文件若干（(ii) 面，差集 86 行已落 `evidence-host-probe/closeout-final-20260908T071818.txt`）。
7. **Codex 存档**：路径 / 绑定 SHA / B-H-M-L 计数 —— 见验收单（Codex 轮次完成后回填）。
8. **后端在跑**（health 200，docker LISTEN 8011）⇒ 本卡无「因后端不在跑」的 NOT-RUN；`/mcp` 暴露 **6 个只读工具**（search_memories / search_notes / get_neighbors / read_note / check_backend_health / get_board_manifest）。
9. **只读 MCP 工具白名单**：全卡唯一一次 `tools/call` 是 `check_backend_health`（`P2f-…`）；`tools/list` 为列举非调用。理由：现网后端绑 live vault + 7691，经 `/mcp` 调写类工具 = 隔着后端写 live。各条探针提示词逐字落盘于 `evidence-host-probe/prompt-P*.txt`（5 份）。
10. **`dsh-mcp-client/README.md` 引用更正确认**：`failOnStartupError` 缺省 false 在 **`:47`**（参数表）与 **`:64`**（行为说明），**不在** `:9-27`（后者只是服务器条目形态）。卡文 §〇 的更正**成立**。
11. **⛔ D-26 (i) 阻断项（需主 session 裁定）**：`~/.codex/config.toml` sha 由 `5636da37…` 变为 `b221897c…`。根因 = `codex exec --sandbox workspace-write` 追加 `[projects]` trust 记录（正负控见 `causal-codex-writes-config-*`），**非本卡编辑**；`[mcp_servers.*]` 段数全程恒 8（配置语义面未变）。本卡在其中留下 2 条记录（`$PV` 与 `causal-probe-ws`），**未做恢复**（手工删条目 = 更重的写入）。建议：把该文件的 `[projects]` 表移入 (ii)，或把 (i) 判据从整文件 sha 改为语义段结构口径。另需主 session 落实 D-26 已裁的「同步修订设计稿 §9.B.5 与任务书 W2 的单层表述」。
12. **P3 命令写法更正确认**：卡文已把 `$PV` 从单引号中移出（改「先 `cd` 到 vault 用相对路径」）是**必要的**；本卡 P6 的 Codex 侧同类写法未踩该坑，两态拒因虽逐字相同，但经 2×2 矩阵的唯一成功格分层成功（§二 P6），**未落入「两类拒因串相同 ⇒ 判据废掉」的情形**。
13. **禁写面 (i)/(ii) 两层口径出处 = 手册 §四.5 D-26**；(i) 五项与 (ii) 四类的开工/收工实测已分别落 `userconf-sha-before/after.txt` 与 `runtime-state-open/close-*.txt`。
14. **其它硬判据全绿**：live vault `find -newer` = **0**；车道树 `git status -- canvas-vault/` = **0**；零代码门 `git diff --stat --no-color da690bf8 HEAD -- . ':(exclude)_bmad-output'` = **0 行**（⛔ 用 `':(exclude)…'`，`':!…'` 在 zsh 下 rc=128 假绿）。
15. **意外面（登记，非本卡范围）**：用户级 `~/.claude/skills/zero-hallucination-research/SKILL.md` 及其 `sub-skills/zhr-run.md` 的 YAML frontmatter **解析失败并被忽略**（Claude Code debug 日志 WARN/ERROR）；既有问题，本卡不改用户级。
