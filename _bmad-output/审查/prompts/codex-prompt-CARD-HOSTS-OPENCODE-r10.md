# 独立复核请求 — CARD-HOSTS-OPENCODE（BATCH-2026-09-11-第十四批 / 车道 card-t2-deploy）

你是独立审查者。只读，不改文件，不连任何数据库，不跑 OpenCode / Codex 模型。

---

## ① 背景

仓：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy`（分支 `card/t2-deploy`）。

本卡给部署脚本 `scripts/deploy-vault.sh` 加 `--hosts opencode` 支持。OpenCode 是第二家宿主。
它只需要**静态绑定件**（纯文件树，不跑模型、不配 provider 凭据）：

1. `$VAULT/.agents/skills/<name>` —— **条目级**软链，目标是相对路径 `../../.claude/skills/<name>`
2. `$VAULT/AGENTS.md` —— 技能清单 + OpenCode 项目级 MCP 接线指引文案

生成发生在步 3（`step3_postprocess`）的 Phase B，**只在 `--apply` 态**；不传 `--apply` 时脚本契约是
「零写」，此时只打印意图。`--hosts claude` 单宿主不得落下任何 opencode 绑定件。

同时本卡在 `scripts/cls_forbidden_paths.py` 给 D-26(i)（`$HOME/.config/opencode` 硬禁面）补了
显式回归断言与注释点名，并在 `scripts/vault-install-manifest.json` 登记了上面两件。

改动前 HEAD（对照基准，下称 PREV）= `7e1d6b53bab9abd9b26711bc2c60724d3afb496f`。

---

## ② 作者自述，请独立核对（不要默认我说的成立）

1. **`--hosts` 语义**：`opencode` 被接受并与 `claude` 可并存；`codex` / `dsh` / 其它值仍 rc 64（E-1）。
   `--hosts claude` 单宿主的行为与 PREV **逐字相同**（我做了两版 dry 跑 diff，声称为空）。
2. **条目级软链**：`.agents/skills/<name>` 是软链且目标为 `../../.claude/skills/<name>`，解析后
   落在 `$VAULT/.claude/skills/<name>`；`.agents` 与 `.agents/skills` 本身**不是**软链
   （即不是整目录级一根软链）。
3. **AGENTS.md**：只含指引文案，不写任何用户级配置；首行带生成标记，缺标记的同名文件
   （疑为用户手写）拒绝覆盖。
4. **两条既有门更新后仍有牙齿**：`test_second_tier_hosts_rejected_with_e1` 去掉 `opencode`
   后对 `codex` / `dsh` / `claude,codex` 仍断言 rc 64；`test_second_tier_hosts_not_implemented_anywhere`
   去掉 `AGENTS.md` 后对 `.codex/config.toml` / `opencode.json` / `.dsh/` 仍拦。
5. **D-26(i) 承重**：`cls_forbidden_paths.py` 的 `build_targets` 里
   `raw.append(os.path.join(home, ".config", "opencode"))` 那一行是唯一承重点 —— 我做了负控
   （临时删该行 ⇒ `opencode.jsonc` 与 `.gitignore` 从被拒变成被放行），声称该行承重。
6. **dry 零写**：不传 `--apply` 时，`$VAULT` 乃至整个 tmp 根下不产生任何文件。
7. **写入面登记**：新写对象进了步 1 的单一清单 `PENDING_WRITES`；叶子软链（条目名在步 1 时
   还不知道）在 `write_opencode_binding` 里过同一份判据 `check_forbidden_paths --outputs`。

---

## ③ 最小读取面（写死，不要扩散到别处）

```
git --no-pager diff 7e1d6b53bab9abd9b26711bc2c60724d3afb496f d86f0bc4 -- . ':(exclude)_bmad-output'
```

改后文件里重点看这些范围：

- `scripts/deploy-vault.sh`
  - `:19` / `:31-35`（头注 rc 表与 `--hosts` 说明；`usage()` 动态取头注）
  - `:131` / `:135-136`（`HOSTS` 缺省与 `HOST_CLAUDE` / `HOST_OPENCODE` 开关）
  - `:329-348`（`--hosts` 切分与校验块，含 E-1 分支）
  - `:564-...` 的 `step1_preflight` 内 `:579-640`（`PENDING_WRITES` 单一清单 + 条件 append + 逐项复查）
  - `:969-1050` `write_opencode_binding()`、`:1052-1079` `write_agents_md()`
  - `:1081-1095` 步 3 dry 分支、`:1314-1320` Phase B 的 B4b 调用点、步 3 末尾 `STEP_MSG`
- `backend/tests/unit/test_deploy_vault_sh.py` —— 本卡新增/修改的全部测试（文件尾部
  `CARD-HOSTS-OPENCODE` 段，以及 `test_second_tier_hosts_rejected_with_e1`、
  `test_second_tier_hosts_not_implemented_anywhere`、`test_g2_8_activate_tx_opens_no_new_write_surface`）
- `scripts/cls_forbidden_paths.py` `:231-242`（`under()`）、`:265-282`（`build_targets` 与本卡注释）、
  `:560-606`（`main()` 的累加与 rc 语义）
- `scripts/vault-install-manifest.json` 的两个新 item 与 description 里的 origin 例外说明
- `backend/tests/unit/test_vault_install_manifest.py` 的 4 处登记性常量更新

---

## ④ 请按重要性排序回答的问题

0. **条目级软链在 OpenCode 的发现语义下是否真的成立**：OpenCode 会读多处技能根并按
   frontmatter `name` 去重。条目级软链让 `.agents/skills/<n>` 与 `.claude/skills/<n>` 解析到
   **同一个** SKILL.md。请对照输入检查：同名条目是否会被读成两份、
   或因软链而被某一侧忽略？（只从静态文件树与去重语义推，不要求你运行 OpenCode。）
1. **dry 态是否真零写**：有没有**未被拦下的路径**在判据生效之前就写了东西（例如 here-string /
   heredoc 在 `$TMPDIR` 建临时文件、`mkdir -p` 的中间段、`$(...)` 子进程的副作用）？
   注意脚本此前专门修过 Bash 3.2 的 `<<<` 会建临时文件这一类。
2. **子串约束**：`scripts/deploy-vault.sh` 的**非注释行**里是否仍有字面 `opencode.json`？
   注意 `opencode.jsonc` 是它的超串。我用 `OPENCODE_CFG_EXT="jsonc"` 做运行期拼接来避开 ——
   这是**门未覆盖的路径**吗（例如别处又把完整文件名拼成了字面量）？这个规避本身是否恰当？
3. **D-26(i) 是否仅此一处承重**：删掉 `build_targets` 里那一行之后，还有没有别的规则会拦下
   `$HOME/.config/opencode/**`？`under()` 在保护目标解析成根（`/`）时的退化路径有没有旁路？
4. **AGENTS.md 文案**：会不会诱导用户去写硬禁面（`~/.config` 下的用户级配置）？
   文案为了避开上面第 2 条的子串约束做了绕述，是否反而讲不清楚 / 讲错了？
5. **相对软链的落点**：`../../.claude/skills/<n>` 在 live vault（`.git` 是目录的祖先）与
   worktree（`.git` 是文件）下落点是否一致？本卡只在 tmp vault 上验过。
6. **写入面登记是否完整**：`PENDING_WRITES` 的条件 append 与叶子软链的分层判据，有没有
   哪个实际写对象两层都没覆盖到？`AGENTS.md.tmp` → `mv` 的发布路径有没有 TOCTOU 面？
7. **两条既有门 + 一条写面门的更新**：`test_g2_8_activate_tx_opens_no_new_write_surface` 是
   精确集合门，本卡往里补了 3 个 label。这个更新是「按门的立意登记」还是「把门改松了」？

---

## ⑤ 输出格式与边界

- 输出按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给 `file:line` 与**一句**复现思路。
- 没有问题就明说「本轮 BLOCKER=0 HIGH=0」，不要为凑数编造。
- 边界：只读；不连 7691 / 7687 / 任何数据库；不跑 OpenCode 或 Codex 模型；
  不评价 `~/.config/opencode` 这个目录**该不该**被保护（那是已裁定的决策，不在本卡范围）；
  不评价第十四批的排批与合并流程本身。

---

## ⑥ round-10：绑最终 HEAD `d86f0bc4`，r9 的 MEDIUM 已整改

轮次链（**零驳回**，前九轮 38 条 findings 全部采纳）。近四轮都是 **BLOCKER=0 HIGH=0**：
r6 `d9f68261` M4/L2 → r7 `5af9c7ff` M1 → r8 `9df308be` M2 → r9 `d102b847` M1 → 本轮 **`d86f0bc4`**。
本轮面 = `git diff d102b847 d86f0bc4`（两个 commit）。

### `e8bdd4bd` —— 你 B3 指出的措辞不实（我在你出报告前已自查修掉）

B1 自查时我枚举了六种「能让绑定落到 vault 外」的形态逐个实测
（源条目外链 / `.claude/skills` 是软链 / `.claude` 是软链 / 源目录内 `SKILL.md` 是外链 /
源条目指向 vault 内别处 / 正常真目录），结论是**落到 vault 外的形态 0 个**。
但那一跑也暴露：指向 **vault 内**别处的软链同样被拒，而消息说「落点会在 vault 之外」
—— 对那一类输入是假话。⇒ 改成「本脚本不跟随（请用真目录）」，并在注释里如实写明
这里**刻意从严**：判断「软链解完还在不在 vault 内」要再引入一次路径解析，
而那正是本卡反复出问题的地方。门里加了 `"vault 之外" not in stdout` 钉住措辞。

### `d86f0bc4` —— 你 r9 那条 MEDIUM（源检查后的替换窗口）

**你是对的。** 我实测复现了：注入「资格检查通过后、建首条链前把源换成外部软链」，
旧代码**拒绝了但残链落在 vault 外**。修法两件：

1. **源身份钉到 fd 上** —— 资格检查通过时当场 `O_NOFOLLOW|O_DIRECTORY` 打开并留住，
   后核的期望值改用 `os.fstat(src_fds[name])`，不再 `os.stat(".claude/skills/<n>", dir_fd=vfd)`。
   fd 钉死的是 inode，路径之后被换掉也影响不到。
2. **失败时清掉本次建的链** —— 这是真正的 TOCTOU（源是运行中途被换的，建之前无从知道），
   后核能拒但链已经建出去了，「拒绝而留残链」与 r5 HIGH-1 同型。
   ⇒ `finally` 里清 `made` 里的那批（**只清本次真建的**，幂等跳过的已有链不动），
   全程 `dir_fd=sfd`，删前核「它还是软链、目标还是我写的那个串」。

实测（存档 `evidence-hosts-opencode/probe-r9-swap-window-*.txt`）：
修前 = 拒绝但残链在 vault 外；**修后 = 拒绝且零残链**。

### round-10 请回答

- C1. 这个窗口现在闭合了吗？`os.fstat(src_fds[name])` 作期望值是否真的钉住了
  「当初通过检查的那个 inode」？源被换掉后 fd 仍指向旧 inode —— 这个前提成立吗
  （旧目录被删除/被 rename 时 fd 的行为）？
- C2. 失败清理那段自身安全吗？`made` 里的条目在清理时若已被别人换成**同名但不同**的软链
  （目标串碰巧也一样），会被误删吗？删前那两条核够不够？
- C3. `src_fds` 的 fd 数量随技能条目数增长（实测 vault 有 11 条）。
  有没有 fd 耗尽的风险？`finally` 里关闭是否覆盖所有退出路径（含 `die()` 的 `sys.exit`）？
- C4. 终审：绑 `d86f0bc4`，`--hosts opencode` 路径上还剩什么？
  若只剩两个已登记窗口（清理分支 `fstat`→`ftruncate` TOCTOU、打开 vault 前的祖先替换），
  请明说 **BLOCKER=0 HIGH=0 MEDIUM=0**，并说明这两个是否需要在本卡内处理。
