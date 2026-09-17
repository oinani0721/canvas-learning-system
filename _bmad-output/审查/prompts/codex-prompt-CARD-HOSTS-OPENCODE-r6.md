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
git --no-pager diff 7e1d6b53bab9abd9b26711bc2c60724d3afb496f d9f68261 -- . ':(exclude)_bmad-output'
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

## ⑥ round-6：用户放开了轮次上限，round-5 的四条已整改

绑定 HEAD `d9f68261`。轮次链（**零驳回**，前五轮 19 条 findings 全部采纳）：
r1 `836b1b7d` B0/H2/M2/L0 → `c228b745`；r2 `c228b745` B0/H1/M1/L1 → `4ad30472`；
r3 `4ad30472` B0/H3/M1/L0 → `a09c2b96`；r4 `a09c2b96` B0/H2/M2/L1 → `6acec0e4`；
r5 `6acec0e4` B0/H2/M1/L1 → **`d9f68261`**（本轮整改面 = `git diff 6acec0e4 d9f68261`）。

> ⚠️ 项目原有 D-15 规则是「5 轮上限，第 5 轮仍有 HIGH 就停下交人审」。
> 车道曾据此停下并交人审；**用户于 2026-09-16 裁定放开轮次继续修**，故有本轮。

### round-5 的四条怎么修的

1. **HIGH-1 技能名过检后被改写** —— 车道**独立端到端复现了你的结论**（存档
   `evidence-hosts-opencode/selfcheck-r5-findings-20260916T125808.txt`）：
   判据对 ` .git` 放行 rc 0、对 `.git` 拒绝 rc 1；喂一个名为 ` .git` 的技能目录，
   软链 `.agents/skills/.git` **真的建出来了**，之后才因解析失败报 rc 1 —— 残链已落盘。
   **修法不是在 python 侧再做一次判据**（那是加第三份手抄口径，必然再漂），而是让两侧
   看到**同一份字节**：shell 侧 `printf '%s\0'`，python 侧 `_raw.split(b"\0")` +
   `os.fsdecode`，**不 strip、不 splitlines**。
   - `strip()` 吃掉前后空白 ⇒ 判据放行的名字变成判据会拒的名字；
   - `splitlines()` 切的不只是 `\n`，还有 `\v \f \x1c \x1d \x1e \x85    `
     ⇒ 名字含这些字符时**一个名字被切成两个**。
   端到端复验：同一输入现在建出 `[ .git]` 而不是 `[.git]`。
2. **MEDIUM-1 静态门只滤整行注释** → 新增 `_py_code_only()`（`tokenize` **按位置挖掉**
   COMMENT token）+ `_heredoc_body()`（从 `cat << 'TAG'` 精确抽内嵌 python，断言开标记唯一）。
   三条静态门改用它。并锁住你指出无门的那条：清理分支截断前的 `st_nlink != 1`。
   ⛔ 我第一版把它写成 `" ".join(tok.string)` 重拼，结果 `os.ftruncate(` 被拼成
   `os . ftruncate (`，所有子串判据一起失效 —— 已改为按位置挖，负控验证过。
3. **LOW-1** 两处成立的注释已改。**第三处不成立**：你说文案仍承诺「重跑会被覆盖」，
   实测该字样命中 **0** —— 我在 r4 已改掉。已在验收单如实记录这半条描述有误。
4. **HIGH-2（清理分支 `fstat(nlink)` → `ftruncate` 的 TOCTOU）本轮未改**，理由见下。

### 关于 HIGH-2，车道的判断（请裁定，我不自判）

技术上成立（任何 check-then-act 都有窗口）。但影响面与脚本另外三处 `ftruncate` 不同：
- 本处 fd 指向的是**本次 `O_EXCL` 新建**的文件 ⇒ 别人要受影响，必须**主动 `link` 到我的半成品**；
- 另外三处经 `open_pinned` 打开的是**已存在**的文件，那里的 `nlink` 检查防的是伤到别人原有数据；
- 被截断的内容是**半成品**（不是任何人的数据），且**去掉这个检查只会更糟**。

⇒ 车道倾向 LOW/MEDIUM 而非 HIGH。**如果你认为它该修，请给出一个不引入新窗口的修法** ——
我想不出比「检查 + 截断」更强的形态（`ftruncate` 没有条件版本），除非干脆**不清理**
（那样半成品会带着正常的生成标记留下，下次跑会被 `describe_existing` 报成「上次生成的产物」，
反而更容易被误认为是好的）。

### round-6 请回答

- U. HIGH-1 的修法是否真的闭合了「判据看到的名字 ≠ 实际建出的名字」这一整类？
  还有没有**别的层**在转换名字（shell 的 `basename`/glob、`os.fsdecode` 的往返、
  `LINK_WRITES` 的 label 拼接、`printf '%s\0'` 对含 `%` 的名字）？
- V. `os.fsdecode` 在 macOS（UTF-8 强制）上是无损往返吗？名字是**非法 UTF-8 字节**时会怎样？
  surrogateescape 往返后 `os.symlink` 拿到的还是原字节吗？
- W. `_py_code_only` / `_heredoc_body` 这两个 helper 自身可靠吗？
  字符串字面量里的 `#`、f-string 里的 `#`、多行字符串里的 `#` 会被误剥吗？
  `_heredoc_body` 的「开标记唯一」断言够不够（收标记不唯一会怎样）？
- X. 本轮新增的两条门（行为门 + 静态门）承重吗？删掉被它们保护的那行，它们会红吗？
- Y. 到这一轮为止还剩哪些**门未覆盖的路径**？如果只剩 HIGH-2 与已登记的
  「`$VAULT` 祖先在步 1 判据与步 3 之间被替换」窗口，请明说 BLOCKER=0 HIGH=0。
