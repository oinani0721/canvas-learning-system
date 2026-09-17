# 只读复核请求 — CARD-TOOL-residue-fail-open（round-2）

## 一 背景 + 最小读取面

仓库：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools`
分支 `card/t8-tools`。基线 `08100483`（B14_BASE）→ round-1 `cd31cffd` → **round-2 `f9e31034`（当前 HEAD）**。

`lefthook.yml` 的 pre-commit 命令 `mutant-residue-scan` 在 commit 前扫暂存区的新增行，命中变异
残留标记就 exit 1。标记串在块内由两段拼出，使本文件自身不含该字面量；本 prompt 同样不写它。

**round-1 你给出 BLOCKER=0 / HIGH=1 / MEDIUM=2 / LOW=1。四条全部被实测坐实并整改，本轮请复核整改本身。**

**最小读取面**：

1. `git diff cd31cffd f9e31034 -- lefthook.yml`（round-2 的全部代码改动 = 本轮主体）
2. `git diff 08100483 f9e31034 -- lefthook.yml`（本卡全部代码改动）
3. `lefthook.yml` 当前版本的 `mutant-residue-scan` 块与其上方注释段。锚点：含
   `--- Mutant residue scan` 的行 / 含 `mutant-residue-scan:` 的行（唯一）/ 含 `Mutant-Scan] OK` 的行（唯一）
4. `_bmad-output/审查/codex-review-CARD-TOOL-residue-fail-open.md`（你 round-1 的存档）
5. 对照脚本与输出：`_bmad-output/审查/evidence-residue-fo/case-*.sh` 与 `r2-out-case-*.txt`
6. 真 hook 三控：`_bmad-output/审查/evidence-residue-fo/r2-h-controls-*.txt`

## 二 作者自述（请独立核对，不要采信本节）

### 2.1 四条整改

| round-1 级别 | 整改 | 佐证 |
|---|---|---|
| HIGH `--text` 后仍漏同行 NUL 之后的标记 | 喂 awk 之前加 `LC_ALL=C tr '\000' '?'` 等长归一化，`awk` 改读 `$TMPD/dn` | 新对照 `case-h1-nul-before-marker.sh`（旧版 = **round-1 的 `cd31cffd`**，不是 B14_BASE，因为要证的是「已经有 --text 之后仍然漏」）；真 hook 负控 B |
| MEDIUM-1 计数管道吞上游失败 + locale | 字节处理一律 `LC_ALL=C`；`tail`/`tr` 拆成各自核 rc 的步骤；`EXPECTED` 由 `wc -c < $TMPD/nuls` 取 | 本机 `LANG=en_US.UTF-8` 实测：`tr -dc '\000'` 对 `a\0b\xff\0` 在 C 下得 2、在 UTF-8 下得 1 且整链 rc=0 |
| MEDIUM-2 空清单下 `SEEN==EXPECTED==0` 仍通过 | 追加结束哨兵 `/__mutant-scan-eof__`（git 路径不以 `/` 开头），主循环必须真读到它，否则阻断 | 新对照 `case-m2-empty-read-error.sh`（旧版同样 = `cd31cffd`） |
| LOW sh 的来源描述不准 | 注释改为「lefthook 2.1.6 起 `sh -c`，该 `sh` 由进程 PATH 查找，非硬编码 `/bin/sh`；本机当前解析到 `/bin/sh` = bash 3.2.57」 | — |

### 2.2 对照套件改为两种解释器都跑

`_lib.sh` 的 `run_both` 对每条对照跑 `bash`（普通模式）与 `sh`（本机解析到 bash 的 POSIX 模式，
也就是 lefthook `sh -c` 真正会用的那个）。结果：

- 11 条 `bash=SEALED sh=SEALED`
- **6-5 `bash=SEALED sh=NOT-SEALED`** —— 如实降级：`:` 是 POSIX 特殊内建，`sh` 下重定向失败
  本来就会退出 shell（旧版 rc=1，只打一句 Permission denied）。所以那条守卫在真实 runner 下的
  收益是「把静默退出变成有诊断的阻断」，不是「把放行变成阻断」。这一点已写进块内注释。

### 2.3 未变部分

允许名单（6 项 + `_bmad-output/**`）、注释计数（151 / 11 / 11 / 2 / 13）、命令名、`priority`、
dash 自证块的判定逻辑、`python-typecheck` 块与 `HONESTY CONTRACT (CARD-DEBT-hook-pyright …)`
注释段（归 T8-G）——round-2 均未动；已用逐字节比对自证后两者与 `08100483` 相同。

## 三 请按重要性回答的问题

1. `tr '\000' '?'` 归一化会不会引入**新的漏检或误报**？例如：某种 diff 正文里 `?` 与标记相邻
   产生歧义；`tr` 在极大文件上的行为；等长替换是否真的保住了行号推进与 `^\+` / `^@@` /
   `^diff --git ` 三个锚点；`$TMPD/dn` 与 `$TMPD/d` 两个文件是否有清理或复用上的问题。
2. 结束哨兵 `/__mutant-scan-eof__` 是否可能与真实暂存路径相撞？`printf '%s\000' >> names`
   追加失败时的处置是否够？哨兵参与 `EXPECTED` 计数的方式是否自洽（`SEEN` 把哨兵也计入）？
   有没有办法让主循环「读到哨兵」但中间仍漏掉记录？
3. `LC_ALL=C` + 逐段核 rc 是否**覆盖完整**？块里还有哪些字节处理仍在管道里、rc 仍被吞？
   （请逐条点名。）
4. round-1 的三条 MEDIUM/HIGH 整改有没有**改坏原有行为**：允许名单、命中输出格式
   （`  <路径>:<行号>: <正文>`）、行号推进、`--text` 之下的正常文本文件路径。
5. 6-5 的降级声明是否准确？在 `sh` 下 `: >` 失败究竟是「退出 shell」还是「命令返回非零且
   继续」？本卡实测是前者（`sh -c ': > <只读文件>; echo 继续'` 不打「继续」且 rc=1）。
6. 还有没有**没被这 12 条对照覆盖**的失败路径？特别是：`trap` 清理、`mktemp` 之后到第一个
   守卫之间的窗口、`git` 本身被换掉的情形、`$TMPD` 位于只读文件系统。

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
