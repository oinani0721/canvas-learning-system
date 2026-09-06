# 部署形态决策：多 vault × 多 harness 的一键部署（2026-09-07）

> **状态**：决策页 v2（2026-09-07 07:40 更新：E-1~E-5 **已裁**，见 §九；新增 §零 用户原意四件套 + §三 DeepSeek Harness(dsh) 本机查证）。v1 = 主 session 起草含 5 项待裁。依据 = 你 2026-09-07 的三条陈述 + 4 路只读勘探 + 1 路 critic（`wf_c99a61ac-7e0`，全部 file:line 取自主干 `59523f03`）+ 官方文档查证（末尾来源）。
> **硬需求（你的原话）**：「关于之后我们在哪个 vault 使用这套 Canvas Learning System，以及部署到哪一个 harness，这是我们的脚本需要搞定的，这样我们才可以不冲突地使用。」
> **前提（你已定）**：① 数据形态 = Obsidian vault，作为项目路径供各种 Agent 编辑；② AI 场景跑在各 harness 上（Claude Code / Codex / OpenCode / Deep Code(DeepSeek) / pi …），**已弃 Claudian**；③ 规划 (a) 一键部署到各 harness，(b) 是否适配 ChatGPT 桌面端未定。

---

## 零、用户原意（2026-09-07 裁定原话，本页一切以此为准）

> 「我这里的 vault 是指 Obsidian 的 vault，本质上就是我开不同 Obsidian 的仓库，就是开不同的 vault。我们的 Canvas Learning System 就是一键给我们新开的 vault 部署以下内容：1. 部署 Canvas Learning System 插件里的任何东西；2. 部署 Obsidian 的快捷键；3. 部署各个文件夹、原白板、检验白板的格式；4. 绑定好不同的 harness。完成上述步骤后，就可以使用我们的 Canvas Learning System。」

四件套对照今天的脚本（主干 `fceac100` 实测 `scripts/install-vault.sh` + `scripts/vault-install-manifest.json`）：

| # | 用户要的 | 今天已有 | 缺口（进第十三批哪张卡） |
|---|---|---|---|
| ① | CLS 插件里的任何东西 | `install-vault.sh:93` 复制 `.obsidian/plugins/canvas-learning-system/`（`main.js` 是 gitignored 构建产物，来源只能是 live vault 或先 `npm run build`）；`:121` 校验 main.js 与模板源字节一致 | 插件 `data.json`（用户设置）不在清单 → G2-7a 补；模板源改从 `<harness>/canvas-vault/` 时 main.js 须先构建 → G2-7b 的 preflight 加「无 main.js 则 build」 |
| ② | Obsidian 快捷键 | `install-vault.sh:65` `OBSIDIAN_FILES` 含 `hotkeys.json` + `community-plugins.json`；`:122` 校验存在 | 只校验「文件在」不校验「绑定的命令 id 在插件里存在」→ RV-G2-6 加一条 hotkeys↔plugin 命令 id 交叉核 |
| ③ | 各文件夹、原白板、检验白板的格式 | `install-vault.sh:63` `SKELETON_DIRS=(原白板 检验白板 节点 outputs raw templates)` + `templates/{concept,exam-board}.md`（git 追踪）；`.canvas-config.yaml` | 「格式」= 模板 + frontmatter 约定，目前只复制 2 份模板，**Templater 模板与 dashboard 未进清单** → G2-7a 清单补齐并给每份模板一条「新 vault 建板后 frontmatter 字段齐全」的门 |
| ④ | 绑定好不同的 harness | **没有**：根级 `.mcp.json` 从未被复制；Codex `.codex/config.toml` / OpenCode `opencode.json` / dsh patch 都不生成；后端实例与 vault 的绑定靠手改 `.env` | 这是本页 §五 `deploy-vault.sh --hosts` 的全部内容 → G2-7b（一线 Claude Code）+ HOST-PROBE（二线三家探针） |

**推论**：①②③ 是「把一份 vault 骨架复制对」，今天已有七成；④ 是新工作，也是本页存在的理由。「绑定 harness」在实现上 = 在 vault 里落该宿主的 skills 目录 + MCP 注册文件 + 说明文件（§三 表），并把这个 vault 指向它自己的后端实例（§一 部署单元）。

---

## 一、结论（一句话）

**部署单元 = (vault, 它绑定的后端实例)**，不是 vault 本身。「部署到哪个 harness」拆成两个正交维度：**运行时**（代码树 + compose 项目 + 端口 + LanceDB 卷）用 `--harness` 指定；**宿主**（Claude Code / Codex / OpenCode / …）用 `--hosts` 指定，只决定 vault 内放哪些适配文件。脚本只写目标 vault 子树与该运行时自己的 `.env.<vault>` / compose 参数，其余一律禁写。**运行时切换不存在**（`/vault/switch` 已 410），「激活」= 起 / 重建该 vault 的绑定实例，不顶掉别的 vault。

## 二、为什么不能是「一个后端 + 切换 vault」（勘探实证）

| # | 绑定面 | 证据 |
|---|---|---|
| G1 | 后端进程 = 单 `ACTIVE_VAULT`：`get_settings()` 是 `lru_cache`，40 个文件直用 `CANVAS_BASE_PATH`，`memory_service._episodes_recovered` 一次装载后其它 vault 历史永远装不进来 | `backend/app/config.py:948-964`；`grep -rln CANVAS_BASE_PATH backend/app` = 40；`memory_service.py:247,331-345`；`vault.py:68-108`（switch 410，注释「split-brain」） |
| G2 | 宿主端口 8011 单一；5 份 compose 的 `container_name` 全是常量，任何一棵树 `compose up` 都顶替现网容器 | `docker-compose.yml:22,104,146`；`.env:28` |
| G3 | LanceDB 单 volume 共用，`_cache_tables` 对**全部**表跑维度检查并 drop —— 以 vault A 启动可删 vault B 的表（= **G2-9-F1，数据丢失面，D-17 必排**） | `backend/lib/agentic_rag/clients/lancedb_client.py:955-968` |
| G4 | vault 名两套口径：后端 `sanitize_vault_id`（`canvas_vault`）vs 推送链 `send_bark.vault_key`（`canvas-vault`）；`CS 61B` 与 `cs-61b` 会在后端串桶 | `vault_state_paths.py:55-58`；`send_bark.py:47-66` |
| G5 | launchd 单 wrapper，`WT` 写死 `feature-obsidian-hybrid-dev`，从它的 `.env` 读推送清单；`install-vault.sh --activate` 改一行就让旧 vault 停推；每个 vault 的 `decay_beta/fsrs_bridge` 必须与**同一份**树副本逐字节相同，否则整体 exit 78（09-05 已发生） | wrapper `:16-17,:26-36,:99-107` |
| G7 | 三处扫描把「含 `.obsidian`」当 vault：主仓根下 `test-vault` 与 `_bmad-output`（开发会话目录）都被当成可推送 / 可写投影的 vault | `vault.py:125-133`；`chat.py:784-789`；`review_overview.py:974-1021` |
| G8 | vault 身份三份副本（根 `.env` / `backend/.env:30-33` / compose 拼接）没有任何 validator 绑定一致 | `config.py` 仅 `:233/:274` 两个 validator |

结论：单进程多 vault 在现有代码上没有安全路径；**一 vault 一后端实例**是唯一不改内核的形态。

## 三、宿主约定（2026-09-07 官方文档查证）

| 宿主 | skills 目录（项目级） | MCP 注册（项目级） | 说明文件 | 本机状态 |
|---|---|---|---|---|
| Claude Code | `.claude/skills/`（不读 `.agents`）；条目级软链有文档背书，整目录软链未验 | 仓根 `.mcp.json`（首次需批准）；http(streamable) / stdio；SSE 已弃用 | `CLAUDE.md`（不读 AGENTS.md，官方桥：`@AGENTS.md` 或软链） | 在用 |
| Codex / ChatGPT 桌面端本地对话 | `.agents/skills/`（cwd 向上到仓根）+ `~/.agents/skills`；支持软链 | `.codex/config.toml`（仅受信项目；未受信回落用户级 `~/.codex/config.toml`）；stdio + streamable http | `AGENTS.md`；桌面端只对 local project 的 **primary folder** 做发现 | codex-cli 0.153.3 |
| OpenCode | `.opencode/skills`、`.claude/skills`、`.agents/skills` 三处都读 | `opencode.json`（项目根） | `AGENTS.md`，无则回退 `CLAUDE.md` | 1.18.27 |
| pi | `.pi/skills`、`.agents/skills`（项目需先信任） | **无 MCP**（官方立场） | `AGENTS.md` 或 `CLAUDE.md` | 未装 |
| Deep Code（第三方产品，**不是** DeepSeek 官方 harness） | `.deepcode/skills` > `.agents/skills` | `.deepcode/settings.json`（文档只有 stdio） | `AGENTS.md` | 未装；与下一行勿混 |
| **DeepSeek Harness `dsh`**（官方 `@deepseek-ai/dsh` 0.1.1-rc.2，本机已装） | `<projectRoot>/.dsh/skills`(rank100) > `.agents/skills`(200) > 自定义 > `~/.dsh/skills` > `~/.agents/skills`；读 `SKILL.md` 或扁平 md；**projectRoot = 最近含 `.git` 的祖先，没有才用 cwd** | **无项目级文件**：MCP 是 profile 层插件实例（`~/.dsh/profiles/<name>/cordis.yml` 每服务器一条 `@deepseek-ai/dsh-mcp-client`，`stdio` / `streamable-http`），或启动时 `dsh --profile web --patch <文件>.yml` 叠加；工具名 `mcp__<server>__<tool>` | `~/.dsh/AGENTS.md`（用户级）+ 项目 `AGENTS.md` / `CLAUDE.md`（默认候选就是这两个，同目录字节相同才去重）逐目录嵌套 | 已装（nvm node 24，仅 `web` profile）；沙箱 `DSH_PERMISSION_MODE` = read-only / workspace-write(默认) / danger-full-access，macOS 走 Seatbelt(`sandbox-exec`)，写出 workspace 走 `ask` 审批 |
| Gemini CLI | `.gemini/skills` 或别名 `.agents/skills` | `.gemini/settings.json`（文件夹未受信则不加载） | `GEMINI.md`（可配成读 AGENTS.md） | 未装 |

推论：`.agents/skills/` 被 Codex / OpenCode / pi / dsh / Deep Code / Gemini 六家原生读取，Claude Code 需条目级软链。

**dsh 专项结论（2026-09-07 本机包内 README + `cordis.patch.yml` 实读，非网页转述）**：
- skills 与说明文件**零改造**可用：`.agents/skills/` + `AGENTS.md`（或现有 `CLAUDE.md`）即被发现。
- ⚠️ **projectRoot 取最近 `.git` 祖先**：live `canvas-vault/` 与 `<harness>/canvas-vault/` 都**没有**自己的 `.git`（实测），所以在这两个 vault 里起 dsh，skills 会去 `canvas-learning-system/.agents/skills` 找而不是 vault 里 → 用户新开的独立 vault（无 `.git` 祖先）反而没这个问题；Codex 的「cwd 向上到仓根」同理。deploy 脚本的 verify 步须按宿主算一次「它会认哪个根」。
- ⚠️ **MCP 绑定不在 vault 里**：dsh 没有任何按目录发现的 MCP 配置文件，绑定只能 (a) 写进用户级 profile（多 vault 会串，正是用户要避免的）或 (b) 每个 vault 生成一份 patch（如 `<vault>/.dsh/cls-mcp.yml`，内容 = 一条 `dsh-mcp-client` 指向该 vault 绑定实例的 `http://localhost:<port>/mcp`）并用 `dsh --profile web --patch <vault>/.dsh/cls-mcp.yml` 启动。选 (b)，`--hosts dsh` 就是生成这份 patch + 一条启动命令写进 vault 的 `AGENTS.md`。
- 版本是 **rc**，且用户 profile 里目前没有任何 MCP 条目、模型走本地 provider（设置文件含密钥，本页不引）→ 定为**二线**，与 Codex / OpenCode 同一张探针卡（HOST-PROBE）验三件事：`.agents/skills` 在无 `.git` 的新 vault 里被列出、`--patch` 的 streamable-http 能连上后端 `/mcp`、workspace-write 下 skill 脚本写 vault 内文件不触发审批。**没有任何宿主是「只能用户级注册 MCP」**，多 vault 串的真实风险来自 Codex 未受信项目回落用户级配置。

## 四、我们的 skill 今天能不能跨宿主跑（9 份 SKILL.md 审计）

- 合规面：9/9 的 `name`/`description` 符合 Agent Skills 规范；无绝对路径。
- 不合规面（会让「能被发现」≠「能跑」）：`AskUserQuestion`（Claude 专属）30 处 / 5 份；`mcp__canvas-learning-mcp__*` 命名 32 处；依赖 Claude Code `UserPromptSubmit` hook 注入 26 行（chat-with-context / study-question）；`.claude/skills/<name>/…` 与 `.claude/scripts/…` 这类 vault 相对路径 12 处（搬到 `.agents/skills` 全部失效）；固定 `/tmp/*.json` 9 处（跨会话串料，board-recap:139 自己已警告）；frontmatter 带非标字段 `argument-hint`/`model`、`allowed-tools` 用列表形态；quiz-answer 正文 3062 行（规范建议 <500）。
- **最难移植一处**：quiz-answer `:334-344` 从 vault 上级目录 `REPO/backend/scripts` import 校验器，失败即 fail-closed 拒写 —— vault 离开本仓布局零可用。

## 五、脚本定义（`scripts/deploy-vault.sh`；`install-vault.sh` 与 `/deploy-vault` 降为薄壳）

参数：`--vault <name>`（必填）· `--harness <tree>`（缺省 = `docker compose ls` 唯一 running 项目的 config 目录，否则拒绝）· `--port <n>`（缺省自动分配，拒绝 8011 冲突）· `--hosts <list>`（一线 `claude-code`；二线 `codex`,`opencode` 探针后启用）· `--activate` · `--also-push`（仅 harness == live 树）· `--dry-run` 默认开、`--apply` 才写。

六步：
1. **preflight**：树完整性；vault 名是 `sanitize_vault_id` 与 `send_bark.vault_key` 的不动点且与现有 `vault_id` 不碰撞（G4）；预演 wrapper 的 cmp 门；模板源健康（`.claude/agents` 非空、skills ≥ 9）。
2. **install**：调 `install-vault.sh --env-file <harness>/.env.<vault> --source <harness>/canvas-vault`，不激活；复制清单补根级 `.mcp.json`（现在**漏了**——只复制 Claudian 用的 `.claude/mcp.json`，Claude Code CLI 那份从没进过新 vault）。
3. **后处理**：不复制 `cls-internal-key.txt` / 插件 `data.json` 的 `internalApiKey`（按实例重生）；`settings.local.json` 改为生成、只含 `canvas-learning-mcp` 的批准；按 `--hosts` 生成 `AGENTS.md`（`CLAUDE.md` 首行 `@AGENTS.md`）、`.codex/config.toml`、`opencode.json`；6 处写死 8011 / 树名的文件按 `.canvas-config.yaml` 模板化（schema 2.0 → 2.1 增 `backend_url` / `harness_tree` / `push_enabled`）。
4. **verify**：`verify_vault_install.py --vault <new> --source <模板源>`；判据 = missing / content-drift / unreadable = 0 且 extra 全落 `extra_allow`（现在 rc=1 对用过的 vault 恒真，不能直接当门 → RV-G2-6）。
5. **activate**（仅 `--activate` 且 4 过门）：备份 `.env.<vault>` → 写 `ACTIVE_VAULT / API_PORT / BACKEND_CONTAINER` → `docker compose -p cls-<vault> up -d backend`（只起 backend，Neo4j / Ollama 复用现网）→ `curl :<port>/api/v1/vault/current` 断言 → 失败还原。`--also-push` 把 vault 追加进 `DAILY_REVIEW_VAULTS`（去重，不动 `ACTIVE_VAULT`）。
6. **evidence**：`_bmad-output/审查/evidence-deploy-<vault>/`，末行 `rc=`。

幂等判据：同参数再跑一次 diff 为空。

**禁写面**（配对抗测试）：live vault；`~/Library`（plist / wrapper）；`~/.claude*`、`~/.codex`、`~/.pi`、`~/.gemini`、`~/.deepcode`、`~/.config/opencode`；其它树的 `.env` / compose；主仓 `.git`；vault 内学习数据（原白板 / 节点 / 检验白板 / `learning_events.jsonl` / `backups` / `outputs`）；不 cp SKILL.md / fsrs_bridge 到 live；不起第二个 Neo4j / Ollama；不改 `push.sh` / wrapper。

## 六、ChatGPT 桌面端怎么接（对应你的规划 (b)）

- **L1（零开发）**：ChatGPT 桌面端「本地对话」= Codex；把 vault 建成 local project 并设为 **primary folder**，它就按 Codex 规则读 `.agents/skills` 与 `AGENTS.md`（secondary folder 只能读写文件、不做发现）。前提：你的计划要有 Skills（目前查到 Business / Enterprise / Edu 正式开放，Plus / Pro 未见）。
- **L2**：后端 MCP 经 OpenAI **Secure MCP Tunnel**（`openai/tunnel-client`，出站 HTTPS，不暴露端口）私接给 ChatGPT / Codex，需 developer-mode 权限 + Platform 组织隧道角色，只能私用。
- **不建议 L3**（公开插件）：要求后端上公网 HTTPS，与「本地 vault 是真相源」冲突。

## 七、与 G2 链的关系

- G2-6（已合）：校验器保留为第 4 步判据来源，rc 由 RV-G2-6 加 `extra_allow` 分级后才作门。
- G2-7 拆两张：**G2-7a** 密钥件与绑定件处置 + yaml 2.1 + manifest 补 `.mcp.json` / `data.json`；**G2-7b** = `deploy-vault.sh`（new + activate + 最小回滚）；adopt / upgrade 留 G2-7c。
- G2-8：「activate」语义改为「起 / 重建该 vault 的实例」，卡文须按此改写再开工。
- G2-9-F1：两实例共用 LanceDB 卷的前置；未合前每实例独占卷。

## 八、第十三批候选卡（进必排清单）

| 卡 | 一句话 | 依赖 | 估时 |
|---|---|---|---|
| G2-9-F1 | LanceDB 扫删只限本 vault 前缀 + 真库门「以 a 初始化后 b 表仍在」 | 无（D-17） | 3h |
| RV-G2-6 | 校验器 c4e6b165 复审 + `extra_allow` + rc 分级 + 翻转用例 | 无 | 3h |
| G2-7a | 密钥件 / 绑定件处置 + `.canvas-config.yaml` 2.1 + manifest 补 `.mcp.json`、`data.json` | G2-6 | 4h |
| G2-7b | `deploy-vault.sh --vault --harness --port --hosts` 六步 + compose 参数化 + 禁写面对抗测试 | G2-7a, RV-G2-6 | 6h |
| HOST-PROBE | 宿主探针（scratchpad 临时 vault，**无 `.git` 祖先**）：Claude 整目录软链是否被扫、OpenCode 双位置是否重复、后端 `/mcp` 对 http 与 SSE 的实际支持、Codex 沙箱 `.agents` 只读对 skill 脚本的影响、**dsh 三件事**（`.agents/skills` 被列出 / `--patch` streamable-http 连通 `/mcp` / workspace-write 写 vault 不弹审批）；产出 = 每家一份「认哪个根 / 读哪些目录 / MCP 怎么绑」实测表，二线宿主凭它转正 | 无 | 5h |
| SKILL-PORT-LINT | `tests/skills/test_skill_portability_lint.py`：frontmatter / 正文 grep / scripts 三层基线断言（新增命中即红）+ 最小整改（非标字段挪 `metadata`、`allowed-tools` 改字符串、`/tmp` 改 `tempfile`、`.claude/skills` 相对路径改 skill 根相对） | 无 | 5h |

## 九、裁定结果（用户 2026-09-07 裁定；「按默认」= 用户明示其余按默认）

| # | 裁决 | 结果 | 落地口径 |
|---|---|---|---|
| E-1 | 宿主分层 | **用户裁**：一线 **Claude Code 现在就承诺**；二线 **Codex + OpenCode + dsh**（用户点名本机 dsh 需查看，本页 §三 已查，定二线）**先跑一张探针卡**；三线 pi / Deep Code / Gemini 只写文档 | G2-7b 只实现 `--hosts claude`；HOST-PROBE 出实测表后下一批再开 `--hosts codex,opencode,dsh` |
| E-2 | quiz-answer 校验器 import | 默认：改为从 `.canvas-config.yaml harness_tree` 解析，缺省回退当前 `REPO/backend/scripts` | SKILL-PORT-LINT 顺带；新增「yaml 指向不存在的树 → 仍 fail-closed」翻转用例 |
| E-3 | 新 vault 内部密钥 | 默认：从绑定实例**重生**（各 vault 各 key） | G2-7a：`cls-internal-key.txt` 不再复制，改由 deploy 的 activate 步生成并同步进 `.env.<vault>` |
| E-4 | 模板源系统件 | 默认：改从 `<harness>/canvas-vault/`（git 追踪，与 wrapper cmp 门同源） | G2-7b preflight：`main.js` 缺则先 `npm run build`；3 份 live≠HEAD 的 SKILL.md 以 HEAD 为准并登记差异 |
| E-5 | ChatGPT 桌面端 | 默认：只 L1（写文档 + 验证 vault 作 primary folder 能发现 `.agents/skills`） | 不做隧道；L2 另立卡 |

补充裁定（同一条消息）：vault 的定义与四件套见 §零；四件套的缺口已分别指到 G2-7a / G2-7b / RV-G2-6 / HOST-PROBE。

## 来源
- Agent Skills 规范与采用者：https://agentskills.io ；https://agentskills.io/specification
- Claude Code skills / MCP / memory：https://code.claude.com/docs/en/skills ；https://code.claude.com/docs/en/mcp ；https://code.claude.com/docs/en/memory
- Codex / ChatGPT skills、MCP、projects、sandbox：https://learn.chatgpt.com/docs/build-skills ；https://learn.chatgpt.com/docs/extend/mcp ；https://learn.chatgpt.com/docs/projects ；https://learn.chatgpt.com/docs/sandboxing
- OpenCode：https://opencode.ai/docs/skills/ ；pi：https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/docs/skills.md ；Deep Code：https://deepcode.vegamo.cn/en/docs/configuration/agent-skills ；Gemini CLI：https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/skills.md
- DeepSeek Harness（本机包内文档，`$(npm root -g)/@deepseek-ai/dsh/node_modules/@deepseek-ai/{dsh-skill-filesystem,dsh-agent-instructions,dsh-mcp-client,dsh-sandbox-policy,dsh-base}/README.md` 与 `dsh-base/cordis.patch.yml`；仓库 https://github.com/deepseek-ai/deepseek-harness ）
- Secure MCP Tunnel：https://developers.openai.com/api/docs/guides/secure-mcp-tunnels ；https://github.com/openai/tunnel-client
- ChatGPT Skills 计划覆盖（第三方汇总）：https://www.aiagentslibrary.com/blog/chatgpt-skills-availability/
