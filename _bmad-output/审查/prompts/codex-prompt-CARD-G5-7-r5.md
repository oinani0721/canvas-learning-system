# CARD-G5-7 独立复核 round-5（末轮）—— clear-inbox 执行侧

## ① 背景与最小读取面（请只读下面列出的东西，不要漫游全仓）

仓根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x`

本地 Obsidian vault 的「待处理收件箱清仓」工具链。上一张卡做了**只读**的盘点提名
preview；本卡补执行侧：读 preview 的 JSON + 用户逐条拍板的 decisions，把材料
copy / 硬链接 / move / 移入回收目录 / 留原地，并落一本可一键撤销的账。

- round-1（绑 `1d3e75b3`）：12 HIGH + 3 MEDIUM
- round-2（绑 `a159bdcf`）：9 HIGH + 7 MEDIUM + 2 LOW
- round-3（绑 `421afe85`）：9 HIGH + 3 MEDIUM + 2 LOW
- round-4（绑 `14fe7703`）：6 HIGH + 7 MEDIUM + 1 LOW

**四轮共 61 条，作者全部认定为真、全部整改，无一驳回。** 本轮是本卡的**末轮**。

本卡新增恰三份文件，全文请看：

```
git --no-pager diff --no-color 9c4e7e82 HEAD -- . ':(exclude)_bmad-output'
```

- `canvas-vault/.claude/scripts/undo_journal.py`（NEW，共用模块）
- `canvas-vault/.claude/skills/clear-inbox/scripts/inbox_apply.py`（NEW，执行侧 CLI）
- `backend/tests/skills/test_g5_7_inbox_apply.py`（NEW，88 个承重行为用例）

round-4 → round-5 的改动面：

```
git --no-pager diff --no-color 14fe7703 HEAD -- . ':(exclude)_bmad-output'
```

契约面（本卡只读、零改动）：`inbox_preview.py` 的 `:266-292` / `:300-330` /
`:1917-1983` / `:2143-2186` / `:2395-2479`；`split_preview.py` `:1734-1860`
（本卡只复用其中的 `assert_symlink_free`）。

## ② round-4 十四条的整改

| # | round-4 意见 | 整改 |
|---|---|---|
| H1 | 复用旧 entry 时不核 `sha256_before`，等长改写 + 保持 mtime 可穿过 | `build_plans` 在复用 planned/acting 记录且源仍在时，拿账上的 `sha256_before` 核当前源，不符即拒并提示「另起一批」 |
| H2 | 同字节备份沿用共享 inode | 沿用既有备份追加 `st_nlink == 1` 条件；不满足就挪进 `stale/` 再写新的独立快照 |
| H3 | 封口哨兵跨过任意连续坏行找覆盖 | 哨兵落账时写 `sealed_bad_count`；读侧按该条数**精确覆盖**它前面那几行，其余坏行只有落在末尾连续坏行段里才容忍 |
| H4 | `check_destinations_free` 漏收 `acting` | 收进来（加新状态时漏接的一处） |
| H5 | 绑定只核 vault，不核批次 | `_assert_bound_to` 同时要求每行 `batch_id == self.batch_id` |
| H6 | 回执发布无留痕覆盖独立用户文件 | 新增 `_preserve_existing`：就位前把落点上已有的普通文件挪进 `stale/` 留痕 |
| M1 | 未知 `state` 被静默忽略 | 新增 `KNOWN_STATES`；认不出来的 state 一律按损坏处理 |
| M2 | `--undo` 只取父目录 | 要求传入路径的文件名 == `journal.jsonl`，否则拒绝 |
| M3 | backup/记账失败不走失败回执 | 抽出 `_do_one()`（备份 → plan → acting → perform → commit），整段被调用方的失败处理接住 |
| M4 | 「只有 planned」的夹具其实留着 acting | 夹具改成连 acting 一起删，并把该件的产物挪走（既然「没执行过」） |
| M5 | H8 门只验拼写 | 加行为断言：原子替换必然换 inode（截断式复制不会） |
| M6 | 跨环断裂没有独立门 | 新增手造 rows 的单元门（`pre == at_act` 不触发、只让跨环比较说话）；**如实标注它是补覆盖的门，旧码上本就绿** |
| M7 | H1 门没验「搬产物之前拒绝」 | 加断言：copy 产物仍在原落点、`recycle/undone/` 未被创建 |
| L1 | 停放失败的残片不可追踪 | `_park_stale` 返回残片最终位置；`write_pair_atomically` 失败时用 `add_note` 挂上「残片位置」 |

**门的覆盖**：12 道新门（含 3 处对既有门的加强）喂给整改前的 `14fe7703` ⇒
**10 条变红**；其余 2 条是**补覆盖**的门（`test_dir_retime_rejects_a_broken_ring_chain`
与加强后的 `test_no_raw_copyfile_on_production_paths`），对应行为在旧码上本就正确，
因此不可能变红 —— 已在各自 docstring 里写明。存档
`evidence-g57/newgates-vs-prefix-r4-*.txt`；当前 HEAD 上 88 条全绿。

## ③ 按重要性排序的问题

0. 上表 14 条整改，逐条核对是否真的堵上；有没有哪一条把缺陷挪了位置或引入新回归
   （round-3 的 H5、round-4 的 H4 都是前一轮整改自己引入的）。
1. `_preserve_existing` 现在会在**每次**回执就位前把既有文件挪进 `stale/`。正常重跑
   会不会因此不断累积？有没有路径会把**刚写好的**那一份也挪走？
2. `sealed_bad_count` 的精确覆盖：多次中断 + 多次封口交替之后，覆盖面还对得上吗？
   有没有序列会让一条真正的中间损坏落进某个哨兵的覆盖面？
3. `KNOWN_STATES` 把未知 state 判成损坏 —— 这会不会让某些**本该可读**的账本变得
   读不回来（例如同一批被两个版本的脚本写过）？
4. `_do_one` 把备份/记账都纳入失败处理后，失败回执自身的写入若再失败会怎样？
   `write_receipt` 现在也会 `_preserve_existing`，这会不会在失败路径上再制造失败？
5. `st_nlink == 1` 这个新条件在什么情况下会误伤（例如文件系统本身不报 nlink）？
6. 88 个用例里有没有哪一条**断言不了它声称断言的事**（绿在更早的一道判据上）？
7. 若本轮仍有 HIGH，请**按严重性明确排序**并指出哪几条属于「必须在合入前修」、
   哪几条可以作为登记项移交 —— 本卡是末轮，作者需要据此决定交接内容。

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
- `split_preview.py` 是别的车道的地盘，本卡只读；对它的意见请标注「移交」。
- 历史 `ac949f6f..69fce02c` 已判 PASS，不必复核。
- 作者已如实登记的边界不必重复提出，除非发现它们比声明的更严重：跨进程并发未测；
  「内容恰好相同的独立文件」在 `acting` 阶段仍会被认领；撤销留下自建空目录；
  `rel_path` 的 NFC/NFD 等价未判定。
