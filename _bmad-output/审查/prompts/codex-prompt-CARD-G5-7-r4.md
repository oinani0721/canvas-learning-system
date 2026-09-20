# CARD-G5-7 独立复核 round-4 —— clear-inbox 执行侧

## ① 背景与最小读取面（请只读下面列出的东西，不要漫游全仓）

仓根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x`

本地 Obsidian vault 的「待处理收件箱清仓」工具链。上一张卡做了**只读**的盘点提名
preview；本卡补执行侧：读 preview 的 JSON + 用户逐条拍板的 decisions，把材料
copy / 硬链接 / move / 移入回收目录 / 留原地，并落一本可一键撤销的账。

- round-1（绑 `1d3e75b3`）：12 HIGH + 3 MEDIUM
- round-2（绑 `a159bdcf`）：9 HIGH + 7 MEDIUM + 2 LOW
- round-3（绑 `421afe85`）：9 HIGH + 3 MEDIUM + 2 LOW

**三轮共 47 条，作者全部认定为真、全部整改，无一驳回。** 本轮请在整改之后重新判，
并特别检查整改本身有没有引入新问题（round-3 的 H5 就是 round-2 整改引入的回归）。

本卡新增恰三份文件，全文请看：

```
git --no-pager diff --no-color 9c4e7e82 HEAD -- . ':(exclude)_bmad-output'
```

- `canvas-vault/.claude/scripts/undo_journal.py`（NEW，共用模块）
- `canvas-vault/.claude/skills/clear-inbox/scripts/inbox_apply.py`（NEW，执行侧 CLI）
- `backend/tests/skills/test_g5_7_inbox_apply.py`（NEW，77 个承重行为用例）

round-3 → round-4 的改动面：

```
git --no-pager diff --no-color 421afe85 HEAD -- . ':(exclude)_bmad-output'
```

契约面（本卡只读、零改动）：`inbox_preview.py` 的 `:266-292` / `:300-330` /
`:385-396` / `:1917-1983` / `:2143-2186` / `:2395-2479`；
`board-split/scripts/split_preview.py` `:1734-1860`（本卡只复用其中的
`assert_symlink_free`）。

## ② round-3 十四条的整改

| # | round-3 意见 | 整改 |
|---|---|---|
| H1 | `_finish_restore` 先 chmod/utime 再验源 | 该函数开头先验「源是普通文件且 sha == `sha256_before`」，不过就抛，之后才 chmod/utime；copy/link 分支在搬产物**之前**也先验一次源 |
| H2 | `sha256_before` 相等无法区分「未执行的 planned」与「用户放的同字节文件」 | **新增 `acting` 状态**：主动作之前先落一条 `acting` 行。`owned_product` 对 `planned` 行**一律不认领**落点；只有 `acting` / `done` 才用那两条等式。`build_plans` 的 `resumable` 也改成只认 `acting` |
| H3 | 备份落点上的独立用户文件仍被 `os.replace` 换掉 | `backup()` 先判归属：与源逐字节相同 ⇒ 沿用；否则先挪进 `stale/` 留痕再写 |
| H4 | `_park_stale` 没有 symlink 检查 | 加 `is_symlink` + `assert_symlink_free`；**守卫不过就就地留着不动**（异常处理路径，再抛新异常会盖掉真正的失败原因） |
| H5 | M2 整改引入回归：封口过的坏行在后面又有记录时变「中间损坏」 | 判据改成：坏行后面紧跟一条 `tail_sealed` 哨兵即**永远**容忍；后面全是坏行/没有了也容忍。只有「后面还有正常记录且没有哨兵」才算中间损坏 |
| H6 | 续跑用本次 `applied_at` 重算 meta，与账上期望不符 | `perform` 改用 `entry["prov_meta"]`（plan 时落账的那一份），只有账上没有时才回退到重算 |
| H7 | planned move 的撤销只认 `sha256_after`，而 planned 没有该字段 | 抽出 `looks_like_our_product()`（`sha256_after` / `sha256_before` / `expected_after_provenance` 三条等式），dst 缺席分支改走它 |
| H8 | 两处 `copyfile` 非原子，失败留半截文件 | 两处都改走 `copy_file_atomically`（唯一名 tmp → `os.replace`）。顺带解决 0444 写不进去——`os.replace` 要的是目录写权限 |
| H9 | `_assert_bound_to` 没接进 apply | `run_apply` 读完账立刻调用它 |
| M10 | 写 `at_act`/`post` 时盲取 `chain[rel][-1]` | 改成按 `seq` 找/建环（`_slot`）；并加「`pre` 缺失即不回填」 |
| M11 | 目录链测试没走到它声称的路径 | 两件改成落**不同**目录（seq1→`归档` 成功、seq2→`节点` 被挡），共同触碰 `_待处理`；加实盘 mtime 断言 + 「第一件确实成功了」的前提断言 |
| M12 | `write_provenance` 先 `read_bytes` 再判后缀 | 后缀判断提到读文件之前 |
| L13 | 第一份就位失败时其余 tmp 留在正式目录 | 发布循环失败时把剩下的 tmp 一并停放 |
| L14 | 第二次 undo 清空 `created_dirs` | 改为从**全部**行汇总（`undone` 行不带该字段） |

**门的覆盖**：13 道新门喂给整改前的 `421afe85` ⇒ **13 条全部变红**，其余 64 条仍绿
（存档 `evidence-g57/newgates-vs-prefix-r3-*.txt`）；当前 HEAD 上 77 条全绿。

## ③ 按重要性排序的问题

0. 上表 14 条整改，逐条核对是否真的堵上；有没有哪一条把缺陷挪了位置或引入新回归。
1. 新增的 `acting` 状态让状态机变成 planned → acting → done → undone。四种状态在
   apply 与 undo 两侧的解读是否一致？有没有状态组合（含乱序、重复、缺失）会导致
   重复执行、静默跳过、或把「没执行过」误判成「已执行」？
2. `read_rows` 的新容忍规则（坏行后紧跟哨兵即永远容忍）有没有让真正的中间损坏被放行？
   连续多次中断 + 多次封口之后的账本，解读是否仍然唯一？
3. `looks_like_our_product` 的三条等式合起来，还有没有输入能让**不属于本批次**的
   文件被认领？`backup()` 的新归属判定（与源逐字节相同即沿用）有没有同类问题？
4. `copy_file_atomically` 现在用在四个地方（备份 / copy 主动作 / 备份回写 / 回执）。
   它的失败路径、权限位、mtime 语义在这四处是否都正确？有没有哪一处因为换了 inode
   而破坏了别的假设（例如硬链接关系、`st_ino` 判据）？
5. `_park_stale` 在守卫不过时「就地留着」——这会不会让某些失败路径把 tmp 永久留在
   正式目录里？调用方能否察觉？
6. 目录时间的链式判据现在有四种「不回填」的理由。有没有序列会让它**该拒却回填**？
7. 77 个用例里有没有哪一条**断言不了它声称断言的事**（绿在更早的一道判据上）？

## ④ 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给：
- `file:line`
- 一句话说明缺陷是什么
- 一句复现思路：**哪一个输入没有被拦下** / 用**哪一个对照输入**能看出差别 /
  **门没有覆盖到哪一条路径** / 如果把某处改坏了、**哪一条判据应该变红而实际不会**

请不要使用「构造攻击载荷 / 可复现的利用片段 / 打穿 / 绕过防护」这类措辞，
本审查的边界是代码正确性与数据安全，不是攻防演练。

## ⑤ 边界

- **只读**。不要修改任何文件，不要运行会写盘的命令。
- 不要连接任何数据库或网络服务（本卡零外部依赖）。
- 不要评价 `undo_journal.py` 将来被 G5-10 复用时的白板派生语义（那是下一张卡）。
- 不要建议给 clear-inbox 加 `SKILL.md`（属别人的地盘）。
- `backend/tests/skills/skill_portability_lint.py` 的两条基线不含这两份新脚本，
  因此 `tests/skills` 有 4 条预期红（同一根因：新文件未登记）。已登记，不必提出。
- `split_preview.py` 是别的车道的地盘，本卡只读；对它内部实现的意见请标注「移交」。
- 历史 `ac949f6f..69fce02c` 前两轮均判 PASS，本轮不必复核。
- 作者已如实登记的边界（跨进程并发未测；「内容恰好相同的独立文件」在 `acting` 阶段
  仍会被认领；撤销留下自建空目录）不必重复提出，除非发现它们比声明的更严重。
