你是独立复核者。仓库树（只读）：
`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool`

# 被审对象

批次 `BATCH-2026-09-05-第十二批` / 卡 `CARD-TOOL-residue-newline`，一次提交，只动 `lefthook.yml`
的 pre-commit 命令块 `mutant-residue-scan`（该块在修后位于第 345-405 行）。

读取面（请只看这些）：
1. `git diff HEAD~1 HEAD -- lefthook.yml`
2. 修后块全文：`awk 'NR>=345 && NR<=405 {print NR": "$0}' lefthook.yml`
3. 修前块全文：`git show HEAD~1:lefthook.yml | awk 'NR>=345 && NR<=393 {print NR": "$0}'`
4. 实测 transcript 目录 `_bmad-output/审查/evidence-residue-newline/`（每份末行是 rc；
   文件名里的 `b*` 是承重探针，`c*` 是既有防御复测，`a-shell-probe-*` 是解释器实测，`g-syntax-*` 是语法核）
5. 验收单 `_bmad-output/验收单/UAT-CARD-TOOL-residue-newline-2026-09-06.md`

# 这块门是干什么的

pre-commit 阶段扫描**本次暂存的新增行**，若某行带有变异实验的残留标记（块内用
`MARKER="MUT""ANT"` 两段拼接得到，避免 lefthook.yml 自己被自己拦下），就 exit 1 阻断提交。
它自称 fail-closed：扫描没跑完也要阻断，而不是当成"没发现"。

# 修了什么

修前：`git ... --name-only -z > names` 之后，用 `tr '\000' '\n' < names > list` 把 NUL 分隔转成换行分隔，
再 `while IFS= read -r f ... done < list` 逐行读。文件名本身含换行时，`tr` 把它拆成两条记录，
两半各自被当作路径去 `git diff --cached -- "$半"`，git 对不存在的路径返回 rc=0 且无输出，
于是不置 FAILED、awk 无输入、门打印 OK 退出 0 —— 这类文件名属于**未被拦下的输入**。

修后（四处）：
- 删掉 `tr` 中转；
- `while IFS= read -r -d '' f` 直接按 NUL 消费 `-z` 输出，`done < "$TMPD/names"`；
- 新增一段 NUL 读法自证：`printf 'a\000b\000'` 写入探针文件，必须读出恰好 2 条记录，
  否则打印 FAILED 并 exit 1（`read -d` 是 bash 扩展，本卡实测本机 lefthook 2.1.6 起 `sh -c`
  且该 sh 是 bash 3.2.57 posix 模式可用；在真 POSIX sh 下 `read -d` 会报 Illegal option
  且循环体一次都不跑，整体 rc 仍为 0 —— 那属于**门未覆盖的路径**，故加自证）；
- 文件名从 `awk -v F="$f"` 改为环境变量 + `BEGIN { F = ENVIRON["F"] }`（`awk -v` 对赋值做转义处理，
  含换行的名字让 macOS awk 直接报错，含反斜杠的名字被改写，门报出的路径与真实路径不一致）。

# 请回答（按重要性排序，逐条给出你实际跑过的命令与输出）

1. **NUL 读法是否覆盖全部合法文件名字节。** git 路径可以含除 NUL 与 `/` 以外的任何字节。
   现在这条读法（`IFS=` + `read -r -d ''`）对换行、TAB、回车、反斜杠、引号、前导 `-`、
   `./` 前缀、非 ASCII、超长名、名字末尾空白，是否都能原样取到并送进 `git diff -- "$f"`？
   有没有哪一类会在**读取环节**就丢失或变形？

2. **FAILED 位有没有任何路径退化。** 请把修前修后两版逐条对照，列出所有"扫描没有完整跑完"的分支
   及其最终退出码。特别是：`>> "$TMPD/hits"` 重定向失败时 `||` 绑定的是谁的退出码；
   一个文件 awk 失败、另一个成功时 FAILED 是否仍然生效；`done < file` 形态下 FAILED 与 PROBED
   的赋值是否留在当前 shell。删掉的那条"文件名解码失败"分支是不是真的随 `tr` 一起消失、
   而不是被放宽。

3. **还有没有门未覆盖的输入形态。** 排除名单是 `case "$f" in` 的三条 glob
   （`backend/scripts/g32b_mutation_gates.py`、`backend/scripts/g32cb_mutation_gates.py`、`_bmad-output/*`）。
   请判断：`./` 前缀路径、子模块内路径、符号链接、以及路径写法上与排除名单相近但语义不同的形态
   （例如把敏感内容放在名字里带 `_bmad-output` 字样但并不在该目录下的路径），
   在当前实现下会走到哪个分支。哪些属于该扫而没扫、哪些属于设计内的豁免。

4. **解释器判定的证据是否充分。** `_bmad-output/审查/evidence-residue-newline/a-shell-probe-*.txt`
   记录了 lefthook 2.1.6 在本机起的是 `sh -c`、该 sh 报 `BASH_VERSION=3.2.57`、
   并在真 hook 环境里读出 2 条 NUL 记录。这份证据能支撑到什么范围？
   新加的自证块在非 bash 的 sh 下是否真的会落到 fail-closed 分支
   （请特别检查 `printf 'a\000b\000'` 在别的 sh 实现下的产出，以及 `PROBED` 为 0 时
   `[ "$PROBED" -ne 2 ]` 的判断）。自证块的期望值 2 是独立字面量还是与被测量同源。

5. **卡文符合性与越界。** 卡文在
   `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第十二批-goals/Y4-C.md`。
   §三 硬边界要求：只改该块、不改命令名、不加 `priority:`、不扩宽排除名单、
   lefthook.yml 里不得出现标记字面量、不得做成 warning。卡文给的修法草案只有三处改动，
   本卡实际做了四处（多了自证块与 ENVIRON）。请判断这两处额外改动是否越界，
   以及 `git diff HEAD~1 HEAD -U0 -- lefthook.yml` 的 hunk 是否全部落在原第 345-399 行区间内。

6. **transcript 的可信度。** 修前 lefthook.yml 的 sha256 是
   `f3aa7fecde1dd4b4310aad8cdb6fccae5cba9857e214f163206cb03ac3f28377`，
   修后是 `cf1346a24e851868fee69a15d4dae8299e15c28d9cbb4f6c0a55192e2f0093e3`。
   请核对 `evidence-residue-newline/` 下每一份 transcript 头部记录的 sha 与它自称的
   "修前 / 修后"是否一致；有没有哪份标称修后却跑在修前文件上。

# 输出

按上面 6 问逐条作答。每条给：结论（成立 / 部分成立 / 不成立）+ 你实际跑的命令 + 关键输出行 + 行号引用。
发现的问题按 BLOCKER / HIGH / MEDIUM / LOW 分级，每条写清楚"什么输入下会出错、错成什么样"。
如果某一问你无法在只读沙箱里验证，直接说明无法验证，不要给推测结论。
