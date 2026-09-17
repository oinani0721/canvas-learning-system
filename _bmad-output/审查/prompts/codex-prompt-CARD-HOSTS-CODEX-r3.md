# 代码审查请求 — CARD-HOSTS-CODEX（第十四批 T2-D）**round-3**

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

**请读这些**（起点 `7a8d50e2`，送审 commit `41ddf0d0`）：

```
git diff 7a8d50e2b92d002700b64837a8b518a2ac5facc1 41ddf0d03714f3c77ac798bc069ef8acba894bc4 -- . ':(exclude)_bmad-output'
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

## 一之二 前两轮的意见与本轮处置（请核对整改是否真的成立，不要默认）

round-1（B1/H1/M3）与 round-2（B1/H1/M2）**全部接受、无一条驳回**。本轮要核的是 round-2 的整改：

1. **round-2 BLOCKER（只判到父目录）** → 新增 fd 落点守卫：用 `F_GETPATH`
   （Linux 回退 `/proc/self/fd`，两者都拿不到就 fail-closed）取**已打开 fd 的物理路径**，
   再对「接下来真要写的每个名字」（`.codex`、`.codex/config.toml`、`AGENTS.md`）跑同一份
   `hits()` 判据。搜 `CLS-FDGUARD`。
   ⚠️ 请特别核：
   · 这个守卫放的位置对吗？它与随后那些相对 fd 的操作之间还有窗口吗？
   · `F_GETPATH` 返回的路径可信吗（文件/目录被改名之后它给什么）？
   · 判据模块本卡禁改 ⇒ 守卫在两个程序块里各抄了一份，用一条「两份逐字相同」的门钉住。
     这个处理够不够？
2. **round-2 HIGH（追加回滚没有互斥）** → ① `flock(LOCK_EX)` 把「读→判段→追加→回滚」
   整条串起来；② 回滚前判增量，`grown > append_len` 时**拒绝回滚**。
   ⚠️ 请核：这两条合起来够不够？`flock` 的协作式边界是否已如实声明？还有别的窗口吗？
3. **round-2 MEDIUM（半截清理标记被 `kept` 接受）** → 两向都判：以完整标记开头，
   **或**首行是标记的一段前缀。⚠️ 请核还有没有第三种形态漏掉。
4. **round-2 MEDIUM（manifest `exclude` 放弃形态校验）** → 接受意见，**保持开放不关闭**
   （要改的文件在本卡范围外）。本轮不必重复提，除非发现它造成了新的后果。

另：作者对每条新门都跑了敏感性负控（变异注入 → 该门必须变红 → 还原并核 sha），
存档在 `evidence-hosts-codex/gate-sensitivity-r3-*.txt`。
⚠️ 请核这些门是不是**又**是假门 —— round-1 时作者自己就造过一条（变异后照样绿）。

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
