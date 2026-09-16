# 代码审查请求 — CARD-HOSTS-CODEX（第十四批 T2-D）**round-5（协议轮次上限）**

你是独立审查者。请**只读**地审下面这一段增量，按重要性排序给出问题。不要修改任何文件。

---

## 一 背景与最小读取面

仓：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy`（分支 `card/t2-deploy`）。

这是一个把 **Codex 转正为二线宿主**的增量：部署脚本 `scripts/deploy-vault.sh` 的 `--hosts` 参数
此前接受 `claude` / `opencode`，本卡再加 `codex`；`--hosts` 含 codex 时，步 3 在 vault 里生成
两件**纯静态**产物 —— `<vault>/.codex/config.toml`（Codex 的**项目级** MCP 模板）与
`<vault>/AGENTS.md` 里追加的一个 `## Codex` 段。

**用户已裁定的两条硬约束（审查时请以它们为准）**：
- **D-33**：Codex 的运行形态固定为 `codex exec --sandbox read-only`；部署脚本**不写** Codex 的
  用户级配置（含它记录「这个目录可信」的那张表）。
- **D-26(i) 不放宽**：`$HOME` 下 Codex 的那个点目录是硬禁写面。

**请读这些**（起点 `7a8d50e2`，送审 commit `afacca52`）：

```
git diff 7a8d50e2b92d002700b64837a8b518a2ac5facc1 afacca5277a087ffc3da3b1f899d39e51a91755e -- . ':(exclude)_bmad-output'
```

增量落在三个文件：
1. `scripts/deploy-vault.sh`
   - `--hosts` 校验循环（搜 `case "$_h" in` 与 `E-1`）
   - codex 绑定段（搜 `write_codex_binding`、`publish_codex_config`、
     `publish_codex_agents_section`、`write_codex_config_toml`、`write_codex_agents_section`）
   - 步 1 写入面清单（搜 `codex-config-dir`）
   - 步 3 调用点（搜 `B4c codex 绑定件`）与 dry 文案（搜 `生成 codex 绑定件`）
2. `backend/tests/unit/test_deploy_vault_sh.py`（新门 + 三门改例，搜 `CARD-HOSTS-CODEX`）
3. `scripts/vault-install-manifest.json`（`.codex/config.toml` 的登记项）

**外部事实**（来自本项目此前的宿主实测表，审查时可当已知条件）：
- Codex **不会**自动读项目级 MCP 配置：项目级条目零出现在 `codex mcp list`。所以本卡生成的
  是「模板 + 让用户自己接线的说明」，**不**声称自动接线。
- 用可写沙箱跑 Codex 时，它**首次**遇到一个新目录会往用户级配置追加一条 trust 记录；
  但**同一个目录重复跑**时就不再写 —— 所以「跑前跑后 sha 相同」这条判据若用一个**已经受信**
  的目录去做，是个空判据。
- Codex 会在**零执行事件**的情况下编造命令输出，所以「它是否真的执行了」只能取 `--json`
  事件流里的执行事件，不取模型自述。

**本卡的证据**（在 `_bmad-output/审查/evidence-hosts-codex/` 下，可直接读）：
- `codex-readonly-negctl-*.txt` — read-only 负控（sha before/after、目录跑前跑后是否进 trust 表、
  事件流解析）。⚠️ 其中 `…030813.txt` 是一次**失败的**负控，文件尾部有更正说明，请一并读。
- `codex-toml-schema-probe-*.txt` — 生成模板的键取舍依据（实测）。
- `template-accepted-by-codex-*.txt` — 生成物被 Codex 自己解析的实测。
- `manifest-option-probe-*.txt` — manifest 三种登记方式的实测对照。
- `forbidden-gate-*.txt`、`hard-boundaries-*.txt`、`file-level-final-*.txt`、`unit-close-*.txt`。

---

## 一之二 前四轮与本轮处置

r1(B1/H1/M3)、r2(B1/H1/M2)、r3(B1/H2/M3)、r4(B1/H1/M3/L1) 的意见**全部处理**，无一条无理由驳回。
本轮要核 r4 的整改：

1. **r4 BLOCKER（守卫过后目录被改名搬走）** → 先做了**可落地性实测**（证据
   `evidence-hosts-codex/resolve-beneath-probe-*.txt`）：
   · 候选 A `O_RESOLVE_BENEATH`：本机**静默忽略**（带不带它，逃出 vfd 的软链都照写不误）⇒ 不可用；
   · 候选 B 不跨写入持有 `.codex` 的目录 fd、叶子按 `.codex/config.toml` 相对 `vfd` 打开：
     同一场景下旧 fd 写成功、按路径打开变 `ENOENT` ⇒ **采用**。
   另补：**写第一个字节之前**判一次刚拿到的那个**文件 fd** 的物理路径（三处）。
   去掉目录 fd 会丢掉「`.codex` 是软链 ⇒ ELOOP」这条已有性质，已用显式 `lstat` 判回来。
   ⚠️ 请核：① 候选 B 是否真的消掉了你说的那条路径；② 显式 `lstat` 是否把丢掉的性质补齐了；
   ③ 「check-then-act 之间本机没有可用原语」这个判断对不对 —— 你上轮也说未验证到可落地的闭合方案，
   若你现在想到了**在本卡范围内**（不改判据模块、不改步 1/2/4/5/6）可行的写法，请直接给出。
2. **r4 HIGH（opencode 发布器不取锁）** → 在它的新建路径上加了同一把 `flock`，
   **只加锁，不改该函数任何逻辑**。⚠️ 请核这样是否足够、有没有把它原有性质改坏。
3. **r4 MEDIUM-1（段头子串证不了完整）** → 改成三条齐：段头 + `url = "http://127.0.0.1:` 行 + 末尾换行。
4. **r4 MEDIUM-2（结构门被字符串字面量骗过）** → 判据改用 **AST** 数真实 `Call` 节点，
   并把注释变异与字符串变异**都**做成反例，另加控制组（字符串反例必须能骗过词法判据）。
   实测：字符串变异注入 6 处、`bash -n` rc=0、python 块语法有效，两条门同时变红。
   ⚠️ 请核：AST 计数还有没有别的绕法（例如 `getattr`、间接调用、`exec`）。
5. **r4 MEDIUM-3（manifest exclude）** → 保持开放不关闭（要改的文件在本卡范围外）。
6. **r4 LOW（阈值 5）** → 收到 **2**（`\n<` 也能与正常末尾换行区分）。

⚠️ 本轮是协议的**轮次上限**。若仍有 BLOCKER/HIGH，请把「哪一条是本卡范围内可修的、
哪一条只能交人裁」分清楚说，便于主 session 裁定。

---

## 二 作者自述（请独立核对，不要默认它们成立）

1. `<vault>/.codex/config.toml` 是**项目级模板**；AGENTS.md 的 Codex 段明写了「Codex 不会自动读
   它」「要接上得自己跑一条命令」「本脚本不写你的用户级配置」。
2. read-only 负控用的是一个**全新的、跑前不在 trust 表里**的临时目录；跑完 sha 逐字相同，
   该目录跑前跑后都不在 trust 表里。
3. 执行凭据只取 `--json` 事件流（`item.type == "command_execution"` 且 `item.completed`），
   不取模型文本自述；且加了一道前提 —— 事件数为 0 时只报「未测出」，不报「没写」。
4. 三条既有门里被移除的 codex 例，方向是对的（codex 已转正），且移除时**保住了原有形状**
   （单值 + 「合法值 + 未实现值」组合，换成仍未实现的宿主名）。
5. `deploy-vault.sh` 的**任何**路径都不写 Codex 的用户级配置，也从不调用 codex 可执行文件。

---

## 三 请按重要性回答这些问题

0. **（最高）** 生成路径或探针里，是否存在**任何**能写到 Codex 用户级配置（trust 表 / MCP 段）
   的路径？包括间接路径：沿软链穿过去、`mkdir -p` 穿过某一段、把用户级路径拼进某个写操作、
   或让脚本去调用一个会写它的命令。
1. read-only 负控的「sha 相同」会不会其实是个空判据（例如那个目录本来就受信、或那一趟根本
   没跑起来）？作者声称的验伪锚是否**真的**落实到了判据里？
2. `--json` 事件解析有没有把模型自述当成执行凭据？事件数为 0 时的处置对不对？
3. `.codex/config.toml` 里的端口模板化，与 claude 那份 `.mcp.json` 是不是同一口径？有没有可能
   把缺省的 `:8011` 漏改成 `--port` 指定的值？
4. codex 绑定件生成之后的在位判是不是 fail-closed？注意作者把它放在**生成之后**而不是卡文说的
   Phase A（理由写在代码注释里），这个改动的落点对不对？
5. AGENTS.md 的「追加」路径：它会不会改到用户手写的文件、沿软链写出去、改到一个有多个硬链接
   的 inode、或者在重复跑时把同一段追加两次？追加写到一半失败时留下的东西，下次跑能不能被
   认出来并说清楚？
6. manifest 把 `.codex/config.toml` 登成 `exclude` 而不是 `generate`（作者给的理由是：登成
   generate 会让另外三条门变红，而那些门所在的文件不在本卡可改范围内）—— 这个取舍是否掩盖了
   什么真问题？
7. 步 1 的写入面清单登记是否与脚本**实际**会写的对象一一对应（多登一条或少登一条都算问题）。

---

## 四 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条给：
- 一句话结论
- `file:line`
- 一句「怎么看出来的」（一个具体的输入或场景即可）

没有问题的级别写「无」。

---

## 五 边界

- **只读**：不要修改、不要运行会写盘的命令。
- 不要连任何数据库（本项目的 7691 / 7687 一律不碰）。
- 不要写 Codex 的用户级配置目录。
- **不要评判** Codex 模型侧能不能真的用上这个 MCP —— 那是本卡明确未证的面，不在审查范围。
- 本卡不改这几个文件，它们的现状不算本卡的问题：`scripts/cls_forbidden_paths.py`、
  `scripts/verify_vault_install.py`、`scripts/install-vault.sh`、
  `backend/tests/unit/test_vault_install_manifest.py`、`.claude/skills/deploy-vault/SKILL.md`。
