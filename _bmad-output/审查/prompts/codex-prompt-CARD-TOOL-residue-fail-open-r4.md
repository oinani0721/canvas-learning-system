# 只读复核请求 — CARD-TOOL-residue-fail-open（round-4，末轮）

## 一 背景 + 最小读取面

仓库：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools`
分支 `card/t8-tools`。`08100483`（B14_BASE）→ r1 `cd31cffd` → r2 `f9e31034` → r3 `9020a1a5`
→ **r4 `158e5a60`（当前 HEAD）**。

`lefthook.yml` 的 pre-commit 命令 `mutant-residue-scan` 在 commit 前扫暂存区的新增行，命中变异
残留标记就 exit 1。标记串在块内由两段拼出，本文件与本 prompt 都不含该字面量。

round-3 你给出 BLOCKER=0 / HIGH=0 / MEDIUM=1 / LOW=1。两条都已整改。**本轮请复核整改本身。**

**最小读取面**：

1. `git diff 9020a1a5 158e5a60 -- lefthook.yml`（round-4 的全部代码改动 = 本轮主体）
2. `git diff 08100483 158e5a60 -- lefthook.yml`（本卡全部代码改动）
3. `lefthook.yml` 当前版本的 `mutant-residue-scan` 块与其上方注释段。锚点：含
   `--- Mutant residue scan` 的行 / 含 `mutant-residue-scan:` 的行（唯一）/ 含 `Mutant-Scan] OK` 的行（唯一）
4. `_bmad-output/审查/codex-review-CARD-TOOL-residue-fail-open-r3.md`（你 round-3 的存档）
5. 新对照 `_bmad-output/审查/evidence-residue-fo/case-m4-d-dn-same-inode.sh` 与 `r4-out-case-m4-*.txt`
6. 其余对照与三控：同目录 `r4-out-case-*.txt` 与 `r4-controls-judges-*.txt`

## 二 作者自述（请独立核对，不要采信本节）

### 2.1 两条整改

**MEDIUM（`d` 与 `dn` 同 inode）** —— 在两处类型检查之后加一条 `[ "$TMPD/d" -ef "$TMPD/dn" ]`，
命中即置 `FAILED=1; continue`。`-ef` 比的是 inode，符号链接与硬链接都认得出；`-f` 跟随符号
链接所以看不出来。新对照 `case-m4-d-dn-same-inode.sh` 跑 `symlink` 与 `hardlink` 两个变体，
旧版绑 **`9020a1a5`**，两变体 × 两解释器全部 SEALED。本机 `bash` 与 `sh` 均实测支持 `-ef`。

**LOW（注释仍失实）** —— 你逐条核出的四处全部改掉：

| round-3 指出的失实 | round-4 的写法 |
|---|---|
| 「仍留在 `$( )` 里的只有两处」漏了 probe 期望值的 `$(printf …)` | 改为列出「没单独核 rc 的」完整清单：两处 `$(tr -d …)`、probe 期望值的 `$(printf …)`、两次 probe 的 `printf`、`trap` 注册本身、全部 `echo`（含末尾那条）、两个 `while` 的终止状态、全部 `[` |
| 「tr 失败只会给出空串或非数字」 | 删除该保证，改写为「tr 是先输出后报错的，完全可能既给出有效数字又非零退出；真正的兜底是 `!= "0"`、EXPECTED 的 case 校验与末尾 SEEN/EXPECTED 比较，那是**部分**兜底，不是与核 rc 等价的保证」 |
| 未核 rc 清单漏了 `trap` 注册与各处 `echo` | 已补进清单，并特别标出末尾那条 `echo` 直接决定本块的正常退出状态 |
| 「三个临时文件都在用之前核类型」 | 改为：`d`/`dn` 是**写后、用前**各核一次 + 一条 `-ef`；`hits` **只有末尾那一次**复核，写入与命中读取都在它之前 |

另去掉块内两处无例外措辞（原「下面每一段字节处理都逐段核 rc」「只剩这一步用 `$( )`……失败也只会
给出空串或非数字」）。

### 2.2 结论汇总（如实）

14 条对照脚本、16 个 CASE 结果，每个都跑 `bash` 与 `sh`（后者是 lefthook `sh -c` 真正会用的）：

- 15 个 `bash=SEALED sh=SEALED`
- **6-5 `bash=SEALED sh=NOT-SEALED`** —— `:` 是 POSIX 特殊内建，`sh` 下重定向失败本来就会退出
  shell。那条守卫在真实 runner 下的收益是「把静默退出变成有诊断的阻断」。已写进注释。

真 hook 三控（本轮存档同时记录了每次的暂存清单）：正控 OK rc=0；负控 A（普通标记）BLOCKED rc=1；
负控 B（同一行内 NUL 在标记之前）BLOCKED rc=1。

允许名单、注释计数（151 / 11 / 11 / 2 / 13）、命令名、`priority`、dash 自证块的判定逻辑、
`python-typecheck` 块与 `HONESTY CONTRACT (CARD-DEBT-hook-pyright …)` 注释段：round-4 均未动，
后两者已用逐字节比对自证与 `08100483` 相同。

## 三 请按重要性回答的问题

1. **注释是否终于与实现逐条对上？** 这是本轮最重要的问题。请像 round-3 那样逐条核「rc 覆盖面」
   清单：声称核了 rc 的那几条是否真的核了；声称没核的清单是否**完整**（还有没有漏掉的命令）；
   「`d`/`dn` 写后用前核、`hits` 末尾复核」的描述是否准确。若仍有失实，请逐条点名。
2. `-ef` 这条检查的位置是否正确？会不会把**正常**情形误判（例如 `d` 与 `dn` 都不存在、
   某些文件系统的 inode 语义、`$TMPD` 本身经过符号链接）？`-ef` 在 POSIX `sh` 下是否可依赖？
3. round-4 有没有**改坏**已封住的任何一条？特别是循环内的控制流：新加的 `continue` 分支是否
   会让某些本该被扫的文件被跳过而 `FAILED` 又没被置上。
4. 到此为止，这个块还剩哪些**能被只读论证出来**的放行路径？请按「需要什么前提才能发生」排序，
   并明确区分「本块自身的缺口」与「工具或临时对象被预置/替换之后任何检查都无能为力」两类。
5. 证据层面：本轮存档是否足以把「跑过的那些字节」绑回 `158e5a60`？还缺什么？
6. 如果你认为本卡到此可以收口，请明确说出来；如果还有必须再改的，请只列那些**改了才算封住**
   的，不要把「可以更好」与「不改就不成立」混在一起。

## 四 输出格式

每条发现写成：

```
[级别 BLOCKER/HIGH/MEDIUM/LOW] <一句话结论>
  文件:行  <锚点>
  依据    <你从只读材料里看到的具体事实>
  建议    <最小改法>
```

只读判定不了的写「未验证」并说明需要什么才能判定。最后给一行
`BLOCKER=n HIGH=n MEDIUM=n LOW=n`。

## 五 边界

- **只读**。不要跑 hook、不要暂存任何文件、不要修改任何文件。
- `python-typecheck` 块与 `HONESTY CONTRACT (CARD-DEBT-hook-pyright …)` 注释段归 T8-G，不在本卡面内。
- `backend/scripts/mutation_kill_identity.py` 与四套变异 harness（g32b / g32cb / g32ccr1 / g33）归 T8-B / T8-C。
- `backend/scripts/lifespan_isolation_negative_control.py` 与 `lifespan_isolation_guard_probes.py` 归 T8-D。
- `backend/tests/**` 归 T9 / T10。
- 本卡地盘只有 `lefthook.yml` 一个文件（外加 `_bmad-output/` 下的存档）。
