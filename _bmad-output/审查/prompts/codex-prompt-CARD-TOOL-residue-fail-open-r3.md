# 只读复核请求 — CARD-TOOL-residue-fail-open（round-3）

## 一 背景 + 最小读取面

仓库：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools`
分支 `card/t8-tools`。`08100483`（B14_BASE）→ r1 `cd31cffd` → r2 `f9e31034` → **r3 `9020a1a5`（当前 HEAD）**。

`lefthook.yml` 的 pre-commit 命令 `mutant-residue-scan` 在 commit 前扫暂存区的新增行，命中变异
残留标记就 exit 1。标记串在块内由两段拼出，本文件与本 prompt 都不含该字面量。

round-2 你给出 BLOCKER=0 / HIGH=0 / MEDIUM=2 / LOW=1。三条按批次规则只需登记，但作者选择全部
整改（两条 MEDIUM 各一两行；LOW 是注释说得比代码多，属名实一致问题）。**本轮请复核整改本身。**

**最小读取面**：

1. `git diff f9e31034 9020a1a5 -- lefthook.yml`（round-3 的全部代码改动 = 本轮主体）
2. `git diff 08100483 9020a1a5 -- lefthook.yml`（本卡全部代码改动）
3. `lefthook.yml` 当前版本的 `mutant-residue-scan` 块与其上方注释段。锚点：含
   `--- Mutant residue scan` 的行 / 含 `mutant-residue-scan:` 的行（唯一）/ 含 `Mutant-Scan] OK` 的行（唯一）
4. `_bmad-output/审查/codex-review-CARD-TOOL-residue-fail-open-r2.md`（你 round-2 的存档）
5. 新对照 `_bmad-output/审查/evidence-residue-fo/case-m3-dn-dev-null.sh` 与 `r3-out-case-m3-*.txt`
6. 其余对照与三控：同目录 `r3-out-case-*.txt` 与 `r3-controls-judges-*.txt`

## 二 作者自述（请独立核对，不要采信本节）

### 2.1 三条整改

| round-2 级别 | 整改 | 佐证 |
|---|---|---|
| MEDIUM `dn`（及 `d`）未核文件类型 | 两处写入之后各加「必须是可读的普通文件」检查，不满足即置 FAILED 并跳过该文件 | 新对照 `case-m3-dn-dev-null.sh`：`d` 与 `dn` 两个变体，旧版绑 **`f9e31034`**，两解释器均 SEALED |
| MEDIUM 循环内 git 共享记录流 stdin | 循环内的 git 加 `</dev/null` | 注释里写明了为什么哨兵与计数抓不到这一类（空记录照样计入 SEEN、照样被跳过） |
| LOW 「一律 C、逐段核 rc」说宽了 | 补 `od` 与 `wc` 两段的 rc 检查、给 awk 钉 `LC_ALL=C`；注释改写为**确切范围**：逐段核过 rc 的是哪几条、仍留在 `$( )` 里的是哪两处、另有哪些命令（两次 probe `printf`、两个 `while` 的终止状态、`trap` 里的 `rm`、命中分支的 `cat`）的 rc 没单独核以及为什么不影响「放行 / 阻断」这个判断 | — |

### 2.2 存档可绑定性

`_lib.sh` 的 `prepare_blocks` 现在打印：新旧两段抽出块各自的 sha256、工作树 `lefthook.yml` 的
sha256、当时的 HEAD 短 sha 以及工作树相对 HEAD 的 `--stat`。这是对 round-2 末段「历史运行与
最终提交字节的严格绑定未验证」的回应。

### 2.3 结论汇总（如实）

13 条对照，每条跑 `bash` 与 `sh`（后者是 lefthook `sh -c` 真正会用的那个）：

- 12 条 `bash=SEALED sh=SEALED`
- **6-5 `bash=SEALED sh=NOT-SEALED`** —— `:` 是 POSIX 特殊内建，`sh` 下重定向失败本来就会退出
  shell，所以那条守卫在真实 runner 下的收益是「把静默退出变成有诊断的阻断」。已写进注释。

真 hook 三控：正控 OK rc=0；负控 A（普通标记）BLOCKED rc=1；负控 B（同一行内 NUL 在标记之前）
BLOCKED rc=1。允许名单、注释计数（151 / 11 / 11 / 2 / 13）、命令名、`priority`、dash 自证块的
判定逻辑、`python-typecheck` 块与 `HONESTY CONTRACT (CARD-DEBT-hook-pyright …)` 注释段：round-3
均未动，后两者已用逐字节比对自证与 `08100483` 相同。

## 三 请按重要性回答的问题

1. 新加的两处「可读普通文件」检查位置是否正确、是否可能把**正常**情形误判成失败？
   例如空 diff（`d` 为 0 字节普通文件）、`$TMPD` 在某些文件系统上的行为、`[ -f ]` 跟随符号
   链接的语义是否确如作者所设想。
2. `</dev/null` 是否放在了**所有**会在循环内读 stdin 的位置？循环体里还有哪些命令继承了
   记录流的 stdin（请逐条点名）？`tr` 与 `awk` 都用了显式 `<` 重定向，这是否足够？
3. LOW 的注释改写是否**确实**与实现一一对上？请逐条核：注释声称「逐段核过 rc」的那几条是否
   真的核了；注释声称「仍留在 `$( )` 里的只有两处」是否属实；注释列出的「没单独核 rc 的命令」
   清单是否完整（有没有漏掉的）。这一条是本轮最重要的问题——注释若仍说宽，等同于没修。
4. 给 awk 钉 `LC_ALL=C` 有没有副作用？本块的 awk 只用 `index()` / `split()` / `printf`，
   标记是纯 ASCII；在 C locale 下处理含高位字节的 diff 正文是否仍逐字节安全。
5. round-3 有没有**改坏**已封住的任何一条？特别是：`EXPECTED` 的取值路径变了（先 `wc -c`
   写文件再 `tr -d`），哨兵与计数的自洽是否仍成立；`d`/`dn` 的新检查会不会让某些原本能扫到
   的文件被跳过。
6. 到此为止，这个块还剩哪些**能被只读论证出来**的放行路径？请按「需要什么前提才能发生」排序，
   并明确区分「本块自身的缺口」与「工具本身被换掉之后任何检查都无能为力」这两类。

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
