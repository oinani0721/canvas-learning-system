# 只读复核请求 — CARD-TOOL-residue-fail-open（round-5，收口轮）

## 一 背景 + 最小读取面

仓库：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools`
分支 `card/t8-tools`。`08100483`（B14_BASE）→ r1 `cd31cffd` → r2 `f9e31034` → r3 `9020a1a5`
→ r4 `158e5a60` → **r5 `b09e85e3`（当前 HEAD）**。

`lefthook.yml` 的 pre-commit 命令 `mutant-residue-scan` 在 commit 前扫暂存区的新增行，命中变异
残留标记就 exit 1。标记串在块内由两段拼出，本文件与本 prompt 都不含该字面量。

round-4 你给出 BLOCKER=0 / HIGH=0 / MEDIUM=0 / LOW=1，并明确「没有发现必须继续修改可执行代码
才能封住的项」。**本轮只清那条 LOW 与它点名的三处证据缺口；`lefthook.yml` 的改动是纯注释。**

**最小读取面**：

1. `git diff 158e5a60 b09e85e3 -- lefthook.yml`（本轮对代码树的全部改动 —— 作者主张它是纯注释）
2. `git diff 08100483 b09e85e3 -- lefthook.yml`（本卡全部代码改动）
3. `lefthook.yml` 当前版本的 `mutant-residue-scan` 块与其上方注释段。锚点：含
   `--- Mutant residue scan` 的行 / 含 `mutant-residue-scan:` 的行（唯一）/ 含 `Mutant-Scan] OK` 的行（唯一）
4. `_bmad-output/审查/codex-review-CARD-TOOL-residue-fail-open-r4.md`（你 round-4 的存档）
5. `_bmad-output/审查/evidence-residue-fo/run-hook-controls.sh` 与 `r5-hook-controls-*.txt`
6. `_bmad-output/审查/evidence-residue-fo/_lib.sh`、`case-e-allowlist.sh`、`r5-out-case-*.txt`

## 二 作者自述（请独立核对，不要采信本节）

### 2.1 LOW（注释）—— 你 round-4 逐条点名的四处

| round-4 指出 | round-5 的写法 |
|---|---|
| 未核 rc 清单漏了 `trap` 体里的 `rm`、命中分支的 `cat` | 已补进清单 |
| 已核清单漏了 hits 初始化那个 `:`（确有 `\|\|` 守卫） | 已补进「核了 rc 的」 |
| 需界定 `read` 与固定 shell 操作的范围 | 未核清单里加「两处 `read`（不区分 EOF 与读错误 —— 那正是结束哨兵与 SEEN/EXPECTED 要补的位）」，另起一行「不另立守卫的固定操作 —— `set -u`、纯赋值、算术展开、`continue`」 |
| 「期望值那个 `$(printf …)`、两次 probe 的 printf」重复计同一次调用 | 改为「probe 载荷那条 printf、probe 期望值那个 `$(printf …)`」 |

### 2.2 证据（你 round-4 点名的三处缺口）

- **8-2 / M2 注入后的执行字节**：`_lib.sh::inject_before_loop` 现在在注入之后补打 `old.sh` /
  `new.sh` 的 sha256。注入会覆写脚本，此前 `prepare_blocks` 打的摘要对实际执行的字节不成立。
- **`case-e` 只跑 bash**：脚本开头已如实声明，并说明为何未跑双解释器（允许名单的匹配是
  `case` 语句语义，与解释器无关），且声明「不当双解释器证据」。
- **真 hook 三控的完整绑定**：改由 `run-hook-controls.sh` 落档，每一控记录本次 `lefthook.yml`
  的 sha256 与 HEAD、工作树相对 HEAD 的差异、探针路径 / 字节 `od` / **blob OID**、lefthook 的
  绝对路径与软链目标与 `version`、**完整输出**、`rc`、以及撤销后的残留计数。
  ⚠️ 输出里的 NUL 字节等长换成 `?` 再落盘并写明理由：负控 B 的探针含 NUL，`ruff` 报语法错误
  时会把那个字节原样回显；含 NUL 的文档会被 git 判成二进制、diff 里看不到内容（实测原先的
  存档里有 3 个 NUL，已清）。除该字节外逐字节原样，不是摘录。

### 2.3 结论汇总（如实，未变）

16 个 CASE 结果（14 条对照脚本）：15 个 `bash=SEALED sh=SEALED`；**6-5 `bash=SEALED
sh=NOT-SEALED`**（`:` 是 POSIX 特殊内建，`sh` 下重定向失败本来就会退出 shell，那条守卫在真实
runner 下的收益是把静默退出变成有诊断的阻断）。允许名单、注释计数（151 / 11 / 11 / 2 / 13）、
命令名、`priority`、dash 自证块的判定逻辑、`python-typecheck` 块与 `HONESTY CONTRACT
(CARD-DEBT-hook-pyright …)` 注释段：本轮均未动。

## 三 请按重要性回答的问题

1. **`git diff 158e5a60 b09e85e3 -- lefthook.yml` 是否真的只含注释行？** 请逐 hunk 核，明确
   说出有没有任何一行可执行语句被改动。作者的判据是「增删行里非 `#` 开头的 = 0」——这条判据
   本身够不够（例如续行、行内注释、YAML 缩进变化会不会被它漏过）？
2. **「rc 覆盖面」清单这次是否终于完整且无失实？** 请再逐条核一遍：已核清单每一项是否真有
   守卫；未核清单是否**完整**；`read` 与固定操作的界定是否准确。若仍有遗漏请逐条点名。
3. 三处证据补强是否**确实**回应了你 round-4 的意见？还剩哪些绑定缺口？特别是：NUL → `?` 的
   落盘处理会不会让存档失去证明力（它替换的是哪一类字节、有没有可能替换掉本该看见的内容）。
4. 本卡至此，`mutant-residue-scan` 块还剩哪些**能被只读论证出来**的放行路径？请按所需前提
   排序，并区分「本块自身的缺口」与「工具或临时对象被预置/替换后任何检查都无能为力」。
5. **本卡是否可以收口？** 如果可以请明确说出来。如果不能，请只列「改了才算封住」的项，
   不要把「可以更好」与「不改就不成立」混在一起。

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
