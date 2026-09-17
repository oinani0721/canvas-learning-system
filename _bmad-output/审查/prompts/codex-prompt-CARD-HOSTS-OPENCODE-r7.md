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
git --no-pager diff 7e1d6b53bab9abd9b26711bc2c60724d3afb496f 5af9c7ff -- . ':(exclude)_bmad-output'
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

## ⑥ round-7：round-6 的六条已整改，请绑**最终 HEAD** 复核

绑定 HEAD `5af9c7ff`。轮次链（**零驳回**，前六轮 25 条 findings 全部采纳）：
r1 `836b1b7d` B0/H2/M2/L0 → r2 `c228b745` B0/H1/M1/L1 → r3 `4ad30472` B0/H3/M1/L0 →
r4 `a09c2b96` B0/H2/M2/L1 → r5 `6acec0e4` B0/H2/M1/L1 → **r6 `d9f68261` B0/H0/M4/L2**
→ 本轮整改面 = `git diff d9f68261 5af9c7ff`。

> round-6 已经是 **BLOCKER=0 / HIGH=0**，且你主动把原 HIGH-2 降级为 LOW
>（「同意车道的影响面区分，本轮不维持 HIGH」）。本轮是因为**审后又改了代码**
> （项目规则：改代码必再送一轮，最后一轮必须绑最终 HEAD），不是因为还有 HIGH。

### round-6 六条怎么修的（每条都跑了你给的对照输入）

1. **MEDIUM-1 label 嵌名字 ⇒ 判据检查另一条路径** → label 改用**序号**
   （`opencode-skill-link-$_i:`），名字只进 path。
   实测复现过你的结论：`a:~` 让 `partition(":")` 拆出 `~:/…/a:~`。
2. **MEDIUM-2 `$(basename)` 吃掉尾随 LF** → 改参数展开 `${d%/}` + `${_p##*/}`。
   本机对照实测：`$(basename)` → `alpha`；参数展开 → `alpha`+LF。
   ⚠️ 上一轮那条「含换行」行为门**盖不住这一类** —— 它用的是**中间**换行，
   命令替换只剥**尾随**的。实测退回 `$(basename)` 后那条门仍绿 ⇒ 另补了尾随 LF 行为门。
3. **MEDIUM-3 静态门仍能被注释满足（两处）** →
   ① `_py_code_only` 的行界从 `splitlines()` 改为 `split("\n")`，与 tokenize 的行号口径一致；
   ② shell 尾部不再并入 flags **必要条件**（只参与禁串检查）——
   必要条件只由对应的 Python 代码满足。
4. **MEDIUM-4 清理 guard 断言不承重** → 取名面收窄到
   `if not ok:` … `os.close(dfd)` 之间，并加断言「检查必须在 `ftruncate` **之前**」。
5. **LOW-1（原 HIGH-2 降级）** —— 接受你的定级，**未改**。
6. **LOW-2 两处注释** → 已同步。

新增门 2 条（都是行为门抓不到、必须静态锁的）：
`test_deploy_sh_takes_skill_names_without_command_substitution`、
`test_hosts_opencode_name_with_trailing_newline_is_preserved`。
负控 J/K/L/M **四条全部变红**（存档 `evidence-hosts-opencode/negctl-r6-gates*.txt`）。

### round-7 请回答

- Z1. 这四条 MEDIUM 是否**真的闭合**？特别是：`${_p##*/}` 对名字里含 `/` 以外的
  任何字节是否都保真？序号 label 有没有引入新问题（比如序号与 path 的对应关系断裂）？
- Z2. `_py_code_only` 改 `split("\n")` 之后，与 `tokenize` 的行/列坐标**完全对齐**了吗？
  列坐标呢（tokenize 的 col 是按什么单位算的）？
- Z3. 「必要条件只看 Python 代码、禁串两边都看」这个拆分对吗？
  有没有哪个禁串**只在 shell 尾部出现**才有害、或反过来？
- Z4. 清理 guard 的取名面 `code.index("if not ok:")` … `code.index("os.close(dfd)")`
  稳吗？这两个锚在函数里各出现几次？
- Z5. 到这一轮为止，`--hosts opencode` 路径上还剩什么？
  如果只剩已登记的两个窗口（清理分支 TOCTOU、`$VAULT` 祖先替换），请明说 **BLOCKER=0 HIGH=0**。
