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
git --no-pager diff 7e1d6b53bab9abd9b26711bc2c60724d3afb496f c228b745 -- . ':(exclude)_bmad-output'
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

## ⑥ round-2 补充：round-1 的四条已整改，请**独立复核整改本身**

绑定 HEAD 变为 `c228b745`（round-1 审的是 `836b1b7d`；`git diff 836b1b7d c228b745` 就是整改面）。

round-1 结论是 BLOCKER=0 / HIGH=2 / MEDIUM=2。四条**全部采纳**，无驳回。整改如下，请核对
「是否真修好」以及「整改**本身**有没有引入新问题」：

1. **H1 祖先软链** → ① `write_opencode_binding` 里 `mkdir -p` 之前逐级 fail-closed
   （`.agents` / `.agents/skills` 是软链或已存在但非目录一律拒）；② 生成后的在位判从
   `[ -L ]` 改为核**物理**落点（`cd … && pwd -P`）——软链自身必须在 `$VAULT` 物理路径下，
   解出的目标必须**恰等于** `$VAULT/.claude/skills/<name>`。前缀比较用 `${var#"$prefix"}`
   而非 `case` 模式（vault 路径含 `[` `*` `?` 时 case 会当通配）。
2. **H2 发布窗口** → 新增 `publish_agents_md`：`O_CREAT|O_EXCL|O_NOFOLLOW` 建 tmp、
   写完 `fsync`、**紧邻** `os.replace` 前再核一次目标身份与标记、失败即 `unlink` tmp。
   标记判据收敛成单一函数 `refuse_reason()`（前后两次调同一个），shell 侧不再手抄 grep。
   标记检查由全文子串改为**首行精确相等**（采纳你的事实更正）。
3. **M1** → AGENTS.md 文案改为给完整端点 `http://127.0.0.1:<port>/mcp`，并说明 OpenCode
   侧需要 remote 类型 + 完整 URL（点明「少了 `/mcp` 连不上」）。
4. **M2** → dry 零写门改为**整棵 tmp 树的快照**比对（路径 + 类型 + 内容 sha / 软链目标）。
   已用你给的对照输入实测：在 dry 分支塞一句写 `$HARNESS/stray.txt`，旧判据绿、新判据红。

**整改期间自己踩中并已修掉的一处**（请确认修法正确、且没有同型残留）：初版把发布写成
`python3 - "$1" "$2" << 'PYPUB'`，而 `python3 -` 就是「从 stdin 读程序」——heredoc 占了
stdin，管道送来的正文读成空串，脚本 rc 仍为 0，只落下一个 **0 字节**的 AGENTS.md。
现改为 `python3 -c "$src"`，且 heredoc 放在**函数体内**（放文件顶层会在参数解析与
preflight 之前就往 `$TMPDIR` 写一次，正是此前删掉 `<<<` 所修的那一类）。

新增回归门 3 条：`test_hosts_opencode_refuses_when_agents_root_is_a_symlink`、
`test_hosts_opencode_refuses_to_clobber_handwritten_agents_md`、
`test_hosts_opencode_agents_md_is_nonempty_and_marked`。

### round-2 请额外回答

- A. 祖先软链的两层（前置 fail-closed + 后置物理落点核）是否都承重？负控实测显示只删前置时
  后置仍拦成 rc 73 —— 这个「防御深度」的说法成立吗，还是其中一层其实是死代码？
- B. `publish_agents_md` 的 `O_EXCL` 会让「上一次跑留下的 `AGENTS.md.tmp` 残片」导致永久失败吗？
  这是可接受的 fail-closed 还是一个可用性缺陷？
- C. `write_agents_md | publish_agents_md` 这条管道：`perr="$(… | … 2>&1)" || prc=$?` 取到的
  是哪一段的 rc？`write_agents_md` 若失败（理论上只有 printf 失败）会被吞掉吗？
- D. 新的物理落点核用了 `cd "$dst_root/$name" && pwd -P`——对**指向文件而非目录**的软链、
  或权限不足的目录，这个判据的三态（成功/失败/判不出来）分别落到哪个分支？有没有把
  「问不出来」压成「没问题」？
- E. 整棵树快照判据本身有没有漏面（例如权限位、mtime、硬链接数、空目录）？漏掉的那些
  是否有必要补，还是刻意不入判据？
