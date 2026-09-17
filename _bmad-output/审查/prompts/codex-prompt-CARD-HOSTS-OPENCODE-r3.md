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
git --no-pager diff 7e1d6b53bab9abd9b26711bc2c60724d3afb496f 4ad30472 -- . ':(exclude)_bmad-output'
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

## ⑥ round-3：round-1 四条 + round-2 三条均已整改，请独立复核整改本身

绑定 HEAD `4ad30472`。round-1 审 `836b1b7d`（B0/H2/M2/L0，四条全采纳，整改在 `c228b745`）；
round-2 审 `c228b745`（B0/H1/M1/L1，三条全采纳，整改在 `4ad30472`）。
`git diff c228b745 4ad30472` 就是本轮整改面。

### round-2 的三条怎么修的

1. **HIGH「发布仍未绑定检查过的文件身份」** → 换掉发布机制本身，不再只是压短窗口：
   - 先 `os.open(vault, O_RDONLY|O_DIRECTORY)` 拿父目录 fd，之后 `stat` / `open` / `link` /
     `unlink` 全部 `dir_fd=` 相对它做 —— 父目录在这之后被换掉也影响不到。
   - 发布由 `os.replace` 改为 **`os.link`**：目标已存在时 link 原子失败（EEXIST），而
     replace 无条件覆盖。「不覆盖任何已存在的东西」于是由内核保证。
     （实测 `os.replace in os.supports_dir_fd` 为 False，它既钉不住父目录也没有条件性。）
   - 目标已存在且带我们标记时走 `unlink` → `link`：这中间若有人抢先建同名文件，
     link 会 EEXIST 而**不覆盖**它。代价（已在注释里声明）：两步之间进程被杀会让
     AGENTS.md 暂时消失，它是可重新生成的派生件。
   - tmp 身份：`os.fstat(tfd)` 与 `os.stat(tmp, dir_fd=…, follow_symlinks=False)`
     **各自**要求 `nlink == 1`，再要求 `(dev, ino)` 相同。
   - `finally` 里总是清掉 tmp（残片会让下次跑在 `O_EXCL` 上永久失败 —— 这也回应了你
     round-2 B 条说的人工恢复成本）。
   - 空正文一律拒。
2. **MEDIUM「快照未覆盖实际 `$TMPDIR`」** → 新增 `_oc_tmpdir()` 单一来源，把测试的
   `TMPDIR` 钉进 `tmp_path`，并要求零写门在拍 before 快照**之前**先调它。
   负控对照已跑：同一个「往 `$TMPDIR` 留文件」的变异，钉了 TMPDIR 的判据 1 failed，
   拆掉钉子回到 round-2 之前的写法 1 passed。
3. **LOW「源码捕获失败被空 Python 程序吞掉」** → `src="$(cat …)" || srcrc=$?`，
   随后 `[ "$srcrc" != 0 ] || [ -z "$src" ]` 即 `return 1`。

另外采纳了你 round-2 E 条的建议：快照补 `mode` / `nlink` / `ino`，根目录自身也入判据；
`atime` **刻意不入**（拍快照本身会改它）。并在 docstring 里如实写明本判据看不见什么。

### 我对自己负控的一处更正（请核对这个更正对不对）

round-2 你指出「只删前置后仍 rc 73，不代表仍保住外部零污染 —— 此时 mkdir、软链及
AGENTS 发布已经可能发生」。我接受：我此前把那次负控写成「两层都承重」，措辞过强。
另外 round-2 我做的一个负控（把 `src=""` 塞在守卫**之后**）实际证明的是「守卫万一失效
下游门仍会红」，**不是**「守卫本身承重」—— 这一条也已按实际测到的内容改写。

### round-3 请额外回答

- F. `os.link` 发布路径：`unlink` → `link` 这两步之间的空窗，以及「link 成功后
  `finally` 里 unlink tmp」的顺序，有没有哪条失败路径会留下**既没有 AGENTS.md
  也没有 tmp**、或者留下一个内容不完整的 AGENTS.md？
- G. 父目录 fd 打开时**刻意没加** `O_NOFOLLOW`（末段就是 `$VAULT` 自己，由步 1 判据
  物理解析过）。这个取舍成立吗，还是应该加上？
- H. `write_agents_md | publish_agents_md` 管道在 `pipefail` 下的 rc 传播，以及
  `perr="$( … 2>&1)"` 捕获 stderr 的做法，有没有让某类失败静默？
- I. 快照判据把 `ino` 入判据后，会不会在正常重跑里产生假红（例如某些文件系统上
  同一文件的 ino 会变）？`nlink` 入判据是否有同类风险？
- J. 到这一轮为止，`--hosts opencode` 这条路径上还有哪一处是「门未覆盖的路径」？
  如果没有，请明说 BLOCKER=0 HIGH=0。
