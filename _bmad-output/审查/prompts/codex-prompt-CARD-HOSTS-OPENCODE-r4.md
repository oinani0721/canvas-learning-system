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
git --no-pager diff 7e1d6b53bab9abd9b26711bc2c60724d3afb496f a09c2b96 -- . ':(exclude)_bmad-output'
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

## ⑥ round-4：前三轮共 10 条 findings 全部采纳，请复核本轮整改

绑定 HEAD `a09c2b96`。轮次链：
r1 审 `836b1b7d`（B0/H2/M2/L0）→ 整改 `c228b745`；
r2 审 `c228b745`（B0/H1/M1/L1）→ 整改 `4ad30472`；
r3 审 `4ad30472`（B0/H3/M1/L0）→ 整改 `a09c2b96`。
`git diff 4ad30472 a09c2b96` 是本轮整改面。**零驳回。**

### round-3 的四条怎么修的：不是修竞态，是去掉制造竞态的那个机制

你指出的 H1 / H2 / M1 **三条全部长在「写 tmp → 改名发布」这套机制上**。所以这轮直接
把它整个拿掉，改成**以 `O_CREAT|O_EXCL|O_NOFOLLOW` 建目标本身并写进去**：

- `O_EXCL` ⇒「绝不覆盖任何已存在的东西」由内核保证，不靠「检查完祈祷没人插队」；
- 全程持有同一个 fd ⇒ 没有任何一步「按名字再找一次」（H2 消失）；
- 没有 tmp ⇒ 没有 EEXIST 分支、没有 `unlink`、没有 tmp 残片（H1 / M1 整类消失）；
- **目标已存在一律拒绝**并说清它是什么（手写 / 上次的产物），**不再替换**。
  理由：替换必然要先 `unlink`，而那正是 H1；而整脚本重跑本就被步 2 的防覆盖闸门
  拦成 rc 72、到不了步 3 ⇒ 为一个走不到的分支保留 `unlink`，换来的是一整类竞态。
- 代价（已在注释与验收单声明）：写到一半失败会留下内容不完整的目标 ——
  按 fd 侧 / 路径侧身份核对后清理**自己建的那个**，身份对不上就原样留下并说出来。
- **H3**：补了 `O_NOFOLLOW`。但**祖先替换窗口仍在**：闭合它需要步 1 打开 fd 一路传到
  步 3，而步 1 是别的卡的定稿面（本卡禁改）⇒ 已登记为移交项，没有假装它不存在。

随机制退场的死登记也一并清了：`PENDING_WRITES` 与 `check_forbidden_paths` 里的
`AGENTS.md.tmp`（写面清单只登记真正会被写的对象，多留一条只会让清单开始说谎）。

### 我接受并更正的一处事实错误（你 round-3 G 条）

我 round-2 写过「实测 `os.replace` 在本平台不支持 dir_fd」。**这是错的**，已实测更正：
`os.replace` 不在 `os.supports_dir_fd` 集合里，但带 `src_dir_fd`/`dst_dir_fd`
**实际调用成功**。我当时只查了集合没真去调，把「集合里没有」当成了「不支持」。
（本轮已不再使用 `os.replace`，但错误结论必须更正。）

### round-4 请回答

- K. 「直写目标 + 存在即拒」这个形态，在 `publish_agents_md` 内部还剩哪些
  **未被拦下的输入**或竞态？特别是：`os.open(..., dir_fd=dfd)` 与后面
  `os.fstat(fd)` / `os.stat(base, dir_fd=dfd)` 之间，以及失败清理那一段。
- L. 「存在即拒」让 `--hosts opencode` 变成**不可重入**（第二次 apply 到同一个 vault
  必然 rc 73）。考虑到整脚本重跑本就被步 2 拦成 rc 72，这个取舍成立吗？
  有没有我没想到的、能走到步 3 而目标已存在的路径？
- M. 失败清理那段（`finally` 里按身份核对后 `unlink`）自身有没有引入新的窗口？
  身份核不上时「原样留下并报告」是对的处置吗？
- N. 新增的静态门 `test_deploy_sh_publishes_agents_md_without_a_temp_file` 取的是
  `publish_agents_md() {` 到 `\nPYPUB\n` 这段文本。这个取名面稳吗（会不会因为
  别处也出现 `PYPUB` 而截错）？它禁的三个串够不够？
- O. 到这一轮为止，`--hosts opencode` 这条路径上还剩哪些**门未覆盖的路径**？
  如果只剩已登记为移交项的那个祖先替换窗口，请明说 BLOCKER=0 HIGH=0。
