> ⚠️ 本文件是 CARD-TOOL-residue-newline 的完整卡文——车道开工后必读并逐条执行；它不是 /goal 粘贴文本。/goal 在第十二批手册 §三 Y4-C 块。
> 批次标记 `[BATCH-2026-09-05-第十二批 / CARD-TOOL-residue-newline]`。车道：`card-z7-tool`（分支 `card/z7-tool`，HEAD `df39bf21` 起，主 session 已预合主干 03ac8bf8，venv symlink 已建），**前提 Y4-B 已独立 commit 且工作树干净**。开工先 `L=$(grep -n '^    mutant-residue-scan:' lefthook.yml | cut -d: -f1)` 取块头行（03ac8bf8 上 L=286；Y4-B 若加了 N 行注释则 L=286+N）——本卡文所有 `:286-340` 行锚均为 03ac8bf8 口径，实际行 = 原行号 + (L−286)。勘探 2026-09-05 于主干 03ac8bf8。协议：`.claude/rules/card-batch-protocol.md`（§2.1 存档首部 / §2.2 裁判落盘 / §2.3 环境通告）。

# CARD-TOOL-residue-newline — 残留扫描门换行文件名残孔：NUL 直接消费 + 正向漏检探针（让自称 fail-closed 的门对换行文件名也 fail-closed）

## 〇 事实
| 事实 | 位置 |
|---|---|
| 块锚（03ac8bf8）：:286 块头 / :288 `set -u` / :289 `MARKER="MUT""ANT"` 两段拼接（自指规避）/ :290-292 `mktemp -d` 0700 + trap / :293 `FAILED=0` / :294-295 `git … --name-only --diff-filter=AM -z > "$TMPD/names"` / **:298-299 `tr '\000' '\n' < names > list`（残孔源头）** / :300 `: > hits` / :301 `while IFS= read -r f` / :302 空名 continue / :303-307 排除名单 g32b / g32cb / `_bmad-output/*` / :308-309 `--literal-pathspecs diff --cached --no-color --no-renames -U0 --diff-filter=AM -- "$f"` / :310 取 diff 失败 FAILED=1 / :312-319 awk（`-v F="$f" -v M="$MARKER"`）/ :320 `done < "$TMPD/list"` / :321-324 FAILED 出口 / :325-333 hits 出口 / :334 OK | `awk 'NR>=286 && NR<=334 {print NR": "$0}' lefthook.yml` |
| 残孔链（Y4-A (c) 已定**登记级**）：文件名含 `\n` → :298 拆两段 → :301 逐段读、:302 两段非空 → :308 对不存在路径 `git diff` **rc=0 无输出**（只读探针实证 `git --literal-pathspecs diff --cached -- "$(printf 'no/such\nfile')"; echo rc=$?` = 0）→ :310/:319 不置位、awk 无输入 → :334 OK。fail-open，与块自称 fail-closed 矛盾 | 复核报告 §五.7；本机实测 |
| 防御注释 :269-285 六项 + mktemp：`-z + tr`（:269-271，修后此三行措辞过时——在 :286-340 **之外**，本卡不改，登记）/ `--literal-pathspecs` :272 / `--no-color` :273-276 / `--no-renames` :277-278 / awk inhunk :279-281 / FAILED :282 / mktemp :283 | `sed -n '269,285p' lefthook.yml` |
| 执行次序 :259-268：命令名字母序；任何 `priority` 排最前 ⇒ 禁改名、禁加 priority（`grep -nE '^\s+priority:' lefthook.yml` 现 = 0；`grep -c 'priority:'` = 1 是 :266 注释） | `sed -n '259,268p'`；`grep` |
| `lefthook.yml` 现不含 `MUTANT` 字面量（`grep -c MUTANT lefthook.yml` = 0）——修后必须仍为 0 | `grep` |
| 解释器**未定**：lefthook 2.1.6 `run:` 块用 sh 还是 bash 须实测。本机 `/bin/sh` 是 bash 3.2.57 的 posix 模式（`/bin/sh -c 'echo $BASH_VERSION'` = 3.2.57(1)-release），`read -r -d ''` 在 `/bin/sh` 与 `bash` 下**都**能按 NUL 切分（本机实测 `printf "a\nb\0c\0"` → `[a` `b]` `[c]` 两条记录）；但 `BASH_VERSION` 非空不等于「lefthook 调的是 bash」，须看 `$0` / `ps -o comm= -p $$` | 本机实测 |
| 修法草案（Y4-A 输入）：删 :298-299；:301 → `while IFS= read -r -d '' f; do`；:320 → `done < "$TMPD/names"`；`$TMPD/list` 不再产生。管道 `cmd \| while` 会让 FAILED 在子 shell 里丢失——必须保留 `done <` 文件重定向形态 | — |
| 排除名单对本卡的意义：`_bmad-output/*` 被排除 ⇒ evidence transcript 里的标记字面量不会被门扫到；但**车道树**暂存区禁放含标记的文件，探针一律在 scratch worktree 做 | :306 |

## 一 完成条件（AND）
- (a) 解释器判定有实测证据：scratch worktree（`git worktree add --detach <scratchpad>/y4c-probe HEAD`）的 lefthook.yml 里临时加一条 `shell-probe:` 命令 `run: 'echo "0=$0 BASH_VERSION=${BASH_VERSION:-none}"; ps -o comm= -p $$'`，`/opt/homebrew/bin/lefthook run pre-commit --command shell-probe --force --no-auto-install` → transcript 落 evidence；据此选写法：bash 或 bash-as-sh ⇒ `while IFS= read -r -d '' f; do … done < "$TMPD/names"`；若是非 bash 的 sh ⇒ 改 `xargs -0` 或逐文件管线，且 FAILED 位必须经**文件**（如 `touch "$TMPD/failed"`）传出子进程，不得因子 shell 丢失。shell-probe 只在 scratch，不进 commit。
- (b) 正向漏检探针（承重）：scratch 里 `f="$(printf 'nl\nname.txt')"; printf 'x = 1  # %s\n' "MUT""ANT" > "$f"; git add -- "$f"`。**修前**（scratch 仍是 Y4-B 后的 lefthook.yml）跑 `/opt/homebrew/bin/lefthook run pre-commit --command mutant-residue-scan --no-auto-install; echo rc=$?` → `[Mutant-Scan] OK`、rc=0（漏检成立）；对照输入：同内容普通文件名 `nl_name.txt` → BLOCKED、rc=1（门对正常名有效，漏的只是换行）。**修后**把新块拷进 scratch 再跑同一暂存面 → BLOCKED、rc=1、hits 列出该文件（文件名含换行会跨两行显示，如实即可）；再跑 (i) 空暂存 → OK rc=0，(ii) 一个正常提交面（不含标记的 .py 改动 + `_bmad-output/` 文件）→ OK rc=0。四份 transcript（修前漏检 / 修前对照 / 修后拦下 / 修后正常）落 `_bmad-output/审查/evidence-residue-newline/`，每份末行 rc；跑前跑后 `shasum -a 256 lefthook.yml` 对账。
- (c) 六项既有防御逐条给「修后仍成立」的命令与结果（scratch，各一份 transcript）：① `--literal-pathspecs`：文件名含 `*` / `?` / `:` 的标记文件 → BLOCKED；② `--no-color`：scratch 里 `git config color.ui always; git config color.diff always` 后标记文件 → 仍 BLOCKED、hits 计数不变；③ `--no-renames`：`git mv` 一个已跟踪文件并加标记行 → BLOCKED（R 变 A 进扫描面）；④ `--diff-filter=AM`：删除（D）不进扫描面、新增（A）与修改（M）进；⑤ `mktemp -d`：`TMPDIR=/nonexistent` 跑门 → `[Mutant-Scan] FAILED: 无法创建临时目录`、rc=1；⑥ awk 文件头：新增行以 `++` 开头且带标记 → 命中且行号与 `git diff --cached -U0` 的 `@@` 对上。原 `-z` 面补一条：含 TAB 的文件名 + 标记 → BLOCKED。
- (d) 排除名单 :303-307 与 :289 两段拼接**一字不改**；`grep -c MUTANT lefthook.yml` 修后仍 = 0；`grep -nE '^\s+priority:' lefthook.yml` = 0；命令名不变。
- (e) FAILED 位语义不变：扫描没跑完 = 阻断。修后逐条核：:291（mktemp 失败 exit 1）、:296（枚举失败 exit 1）、:310（取 diff 失败 FAILED=1）、:319（awk 失败 FAILED=1）、:321-324（FAILED≠0 exit 1）都还在；删掉的只有 :298-299 那条「解码失败」路径（`tr` 不再存在，不是放宽）。任一失败路径不得退化成 rc=0。
- (f) 变更行全部落在块内：`git diff HEAD~1 HEAD -U0 -- lefthook.yml | grep -E '^@@'` 的每个 hunk 起止都在 L..L+54（03ac8bf8 口径 :286-340）；块外一字不改（:269-271 过时措辞只登记）。块内可加一行 `# CARD-TOOL-residue-newline: NUL 直接消费, 不经 tr` 注释。
- (g) 语法核：`awk -v L=$L 'NR>=L+2 && NR<=L+48' lefthook.yml | sed 's/^        //' > <scratchpad>/blk.sh; bash -n <scratchpad>/blk.sh; /bin/sh -n <scratchpad>/blk.sh` 均 rc=0（以 (a) 判定的解释器为准，另一个作参考）。
- (h) Codex 一轮：prompt `codex-prompt-CARD-TOOL-residue-newline.md`，读取面 = `git diff HEAD~1 HEAD -- lefthook.yml` + 新块全文 + (b)(c) 十一份 transcript 路径 + (a) 解释器证据；问题按重要性：NUL 读法是否覆盖全部文件名字节（`\n` / TAB / `"` / `\` / 前导 `-` / 空名）/ FAILED 是否有任何路径退化 / 是否还有未被拦下的输入形态（`./` 前缀、子模块路径、符号链接）/ 解释器判定证据是否充分。措辞用「负控输入 / 未被拦下的输入 / 门未覆盖的路径」。存档首部按协议 §2.1。
- (i) 「本卡未证明什么」必填：不检测不带标记字样的残留（唯一可靠锚点仍是全文件 sha 基线）；未在非 macOS / 非 bash-sh 环境验证；:269-271 注释措辞过时未改；含换行文件名对同 hook 其他命令（commitlint / spec-sync 的 `git add openapi.json`）的行为未测；子模块 / 符号链接路径未测。「台账待登记条目」必填：§五.7 残孔「已修 <sha>」；:269-271 措辞过时；Y4-B 行锚偏移 N；lefthook 三版本统一仍在第十三批。

## 二 裁判命令
（车道树；承重 `2>&1 | tee _bmad-output/审查/evidence-residue-newline/<name>-$(date +%Y%m%dT%H%M%S).txt`，末行 rc）
1. `L=$(grep -n '^    mutant-residue-scan:' lefthook.yml | cut -d: -f1); echo L=$L; awk -v L=$L 'NR>=L && NR<=L+48 {print NR": "$0}' lefthook.yml` → 修前对得上 〇 的块锚（+N 偏移）。
2. (a) shell-probe transcript（scratch）。
3. (b) 四份 transcript：修前漏检 rc=0 / 修前对照 rc=1 / 修后拦下 rc=1 且 hits 含该文件 / 修后正常 rc=0；配 `shasum -a 256 lefthook.yml` 跑前跑后。
4. (c) 七份防御 transcript（六项 + `-z` TAB 名）。
5. `git diff HEAD~1 HEAD -U0 -- lefthook.yml | grep -E '^@@'` → 全部 hunk 在 L..L+54；`grep -c MUTANT lefthook.yml` = 0；`grep -nE '^\s+priority:' lefthook.yml` 空；`diff <(git show HEAD~1:lefthook.yml | grep -E '^    [a-z-]+:$') <(grep -E '^    [a-z-]+:$' lefthook.yml)` 空。
6. (g) `bash -n` / `sh -n` rc=0。
7. 车道树正常提交面：本卡 commit 时 hook 真跑，lefthook 摘要 + rc 贴验收单（mutant-residue-scan 必须 ✔️——它扫的是本次暂存的 lefthook.yml 自身；若把自己拦了 = 自指，回到 (d)）。
8. scratch 收尾：`git worktree remove --force <scratchpad>/y4c-probe`；`git worktree list | grep -c y4c-probe` = 0；车道 `git status --porcelain` 空。

## 三 禁改与隔离
- 只改 `lefthook.yml` L..L+54（03ac8bf8 :286-340）；禁改 :147 glob（Y4-B 已落）/ `python-lint` / `spec-sync-*` / `cypher-vault-filter-lint` / `readme-claims-lint` / pre-push 两命令（Y4-D 面）/ :250-285 注释；`lefthook.yml` 本批只 Y4 写，:147 / :286-340 / pre-push 三段互斥。
- 禁改命令名、禁加 `priority:`（任何值都把本块排到最前）；禁扩宽排除名单；禁把标记字面量写进 `lefthook.yml`（自指）；禁做成 warning；禁让任一 FAILED 路径退化 rc=0。
- 禁在车道树暂存区放含标记的文件（全部在 scratch worktree）；scratch 建在 scratchpad 目录下、收尾必删；禁 `npx lefthook`（1.13.6 flag 不兼容且 `run` 隐式重装共享 `.git/hooks`）。
- 设计稿 §0 的 D-14 pyright 绕过口径对本车道**不适用**：commit 不得 `LEFTHOOK_EXCLUDE`；hook 真跑贴 rc 与每个 command 的 SKIP/PASS。
- live vault 只读；禁连 7691/7687；本卡不跑 pytest；别人的地盘（设计稿 §5）不碰；台账不改；`*.stderr*` 不入库；不 push。

## 四 Codex / 验收单
命令同协议 §2，1 轮（`codex-prompt-CARD-TOOL-residue-newline.md` → `codex-review-CARD-TOOL-residue-newline.md`，首部按协议 §2.1，绑定 = 本卡 commit sha）。顺序：门定稿 → 全部裁判 → Codex → 之后只改 `_bmad-output`；审后若按意见再改块 = 失绑须登记（协议 §1）。验收单 `_bmad-output/验收单/UAT-CARD-TOOL-residue-newline-<日期>.md`：DoD-3 双段；4-B「无变化（提交前那道「有没有把实验残片留在代码里」的检查，之前对一种极端文件名会放过去，现在会拦下；正常提交不受影响）」零技术词；(b)(c) 结果表必贴；「本卡未证明什么」「台账待登记条目」按 (i)。commit header ≤100 含 `[BATCH-2026-09-05-第十二批 / CARD-TOOL-residue-newline]`，body 行 ≤100（`wc -m`）；不 push；跑完说「复核第十二批 Y4」。**独立 commit 后同车道继续 Y4-D。**
