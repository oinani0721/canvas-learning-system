# CARD-G5-7 独立复核 round-2 —— clear-inbox 执行侧

## ① 背景与最小读取面（请只读下面列出的东西，不要漫游全仓）

仓根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x`

本地 Obsidian vault 的「待处理收件箱清仓」工具链。上一张卡做了**只读**的盘点提名
preview；本卡补执行侧：读 preview 的 JSON + 用户逐条拍板的 decisions，把材料
copy / 硬链接 / move / 移入回收目录 / 留原地，并落一本可一键撤销的账。

**round-1 已提出 12 条 HIGH + 3 条 MEDIUM，作者逐条认定为真并全部整改。**
本轮请在整改之后的代码上重新判，并特别检查整改本身有没有引入新问题。

本卡新增恰三份文件，全文请看：

```
git --no-pager diff --no-color 9c4e7e82 HEAD -- . ':(exclude)_bmad-output'
```

即：
- `canvas-vault/.claude/scripts/undo_journal.py`（NEW，共用模块）
- `canvas-vault/.claude/skills/clear-inbox/scripts/inbox_apply.py`（NEW，执行侧 CLI）
- `backend/tests/skills/test_g5_7_inbox_apply.py`（NEW，48 个承重行为用例）

round-1 → round-2 的改动面（只看这一段即可知道改了什么）：

```
git --no-pager diff --no-color 1d3e75b3 HEAD -- . ':(exclude)_bmad-output'
```

为读懂契约，还需要看这些**既有**文件的片段（本卡只读、零改动）：

- `canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py`
  `:266-292`（加载器）/ `:300-330`（常量）/ `:385-396`（verdict 词表）/
  `:1876-1914`（提名字段）/ `:1917-1983`（item 键与跳过口径）/
  `:2143-2186`（JSON 顶层键与 `vault_fingerprint` 算式）/ `:2395-2479`（准入次序）
- `canvas-vault/.claude/skills/board-split/scripts/split_preview.py` `:1734-1860`
  （写侧物理原语；本卡现在只复用其中的 `assert_symlink_free`）

另外请顺带复核一段**历史**生产改动（round-1 已判 PASS，本轮如无新意见可一句带过）：

```
git --no-pager diff --no-color ac949f6f 69fce02c -- canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py
```

## ② round-1 十五条的整改（请逐条独立核对是否真的堵上，以及有没有堵出新洞）

| # | round-1 意见 | 整改 |
|---|---|---|
| 1 | `planned` 行被当成落点归属证明 | `check_destinations_free` 改为：落点已存在时，必须 `owned_product()` 为真才放行——`done` 行按 `sha256_after` 认，`planned` 行按「与源逐字节相同」或「自带本批次的溯源印记（`batch_id`）」认 |
| 2 | recycle 跳过落点占用检查 | 同上，recycle 的落点也进同一道门；`dst_abs` 对 recycle 也计算 |
| 3 | 固定名 `.undo-journal.tmp` + `O_TRUNC` | 改唯一名 `.{name}.{pid}-{uuid8}.undo-journal-tmp` + `O_EXCL | O_NOFOLLOW`；写失败的 tmp 挪进 `stale/` |
| 4 | 只查源末段；undo 缺祖先/末段/跟随 symlink | 新增 `source_path()` 对源父目录 `assert_symlink_free`；undo 对 `dst` 查 `islink`、对 `dst.parent` 与 `src.parent` 查祖先链 |
| 5 | undo 不核对账本与 `--vault` 的绑定 | 每条 journal 行带 `vault_fingerprint`；`undo()` 收 `fingerprint` 参数，`_assert_bound_to` 不符即拒（在任何搬动之前） |
| 6 | copy/link 撤销不比 sha 就搬走 | 搬动**之前**统一走 `owned_product()`；不符即拒且不搬 |
| 7 | `build_plans` 无条件查源存在 → move/recycle 无法重跑 | `build_plans` 现在收 journal 的既有行：`settled`（已 done）与 `resumable`（planned + 源不在 + 落点在）两种情况跳过新鲜度检查 |
| 8 | 撤销状态机忽略「已动盘未 done」的 planned；也无法在「已搬回未写 undone」后续跑 | `_entries_to_undo` 把这类 planned 一并纳入；`_undo_one` 先识别「上一次已还原、只是没记账」并补记 |
| 9 | 尾行 JSON 完整但缺最后一个 LF 时不封口 | `read_rows` 另记 `_tail_unterminated`；`seal_tail_if_needed` 对这种情况只补一个换行 |
| 10 | undo 读到坏尾行后不封口就追加 | `undo()` 改走 `load()`（= `read_rows` + 封口 + 重读） |
| 11 | provenance 换 inode，`st_mode` 不保 | `atomic_write_bytes` 收 `mode` 参数并在就位前 chmod；journal 记 `mode_before`；执行与撤销都回写；`_verify_restored` 增加权限位断言 |
| 12 | 复用件的回执回滚按路径 unlink（需并发） | 不再复用 `write_pair_atomically_checked`；改用自带的 `write_pair_atomically`：两份都写好唯一名 tmp 再双双 `os.replace`，不预建 0 字节产物、全程零 unlink |
| 13 | 目录 mtime 无条件回写会掩盖用户改动 | `commit` 记 `dir_mtimes_after`；撤销时只有「实盘现值 == 批后记录值」才回写批前值，否则跳过并在回执里写明原因 |
| 14 | 新建目标目录不会被撤回 | `missing_dirs()` 记录本批新建的目录，进 journal 与两份回执（`created_dirs` / `dirs_left_behind`），明说撤销后会留成空目录 |
| 15 | 旧 provenance 块的剥离在空行处提前结束；引号键留重复 | `strip_provenance_block` 改为空行向前看（下一个非空行仍缩进则仍在块内）；键行认裸键 / 双引号 / 单引号三种写法 |

作者另外自查修了两处（round-1 未提）：`---` 开头但没有收尾 `---` 的 `.md` 现在
**不碰**并在账上记 `skipped:unterminated-frontmatter`；`--work-dir` 落在收件箱内
现在拒绝。

**门的覆盖**：上述每一条都配了一道行为门。作者把这 19 道新门喂给整改**之前**的
那个 commit（`1d3e75b3`，脚本 sha 分别是 `3d1c3efc…` / `98ca1cb2…`），**19 条全部
变红**；在当前 HEAD 上 48 条全绿。存档
`_bmad-output/审查/evidence-g57/newgates-vs-prefix-*.txt`。

## ③ 按重要性排序的问题

0. 上表 15 条整改，逐条核对是否真的堵上了 round-1 描述的那条路径；有没有哪一条只是
   把缺陷挪了个位置。
1. `owned_product()` 这套「落点归属」判定本身能不能被绕过？它用 `sha256_after` /
   `sha256_before` / 溯源印记三种依据，有没有哪种输入让一份**不属于本批次**的文件
   被判成自家产物（例如内容恰好相同、或用户自己写了一段带相同 `batch_id` 的
   frontmatter）？这种误判会导致什么后果？
2. `build_plans` 的 `settled` / `resumable` 两条旁路跳过了源材料新鲜度检查。有没有
   某种世界状态能让一条**本该被拒**的决策走进这两条旁路？
3. 撤销的状态机现在有四种入口（done / 已动盘未 done 的 planned / 已还原未记账 /
   已记 undone）。有没有状态组合会导致重复还原、或某一件被静默跳过？
4. `dir_mtimes_after` 的「实盘现值 == 批后记录值才回写」判据，在同一个目录被本批
   多条记录触碰时，取的是最大 seq 的记录值。这个取法对吗？有没有会误判的序列？
5. `seal_tail_if_needed` 现在有两种封口（坏尾行补换行 + 哨兵；完整尾行只补换行）。
   连续多次中断后的 journal 还能被正确读回吗？
6. `write_pair_atomically` 放弃了「预建两个目标再回滚」的做法，代价是两次
   `os.replace` 之间被杀仍可能只就位一份。这个取舍在本场景下站得住吗？
7. `atomic_write_bytes` 的 `O_EXCL` 唯一名方案，在同一进程内对同一目标连续写两次
   （例如重跑）时会不会撞名或留残片？
8. 48 个用例里有没有哪一条**断言不了它声称断言的事**（比如绿在更早的一道判据上）？

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
- 不要建议给 clear-inbox 加 `SKILL.md`（那会触发另一套基线漂移，属别人的地盘）。
- `backend/tests/skills/skill_portability_lint.py` 的两条基线目前**不含**这两份新
  脚本，因此 `tests/skills` 有 4 条预期红，全部是同一根因（新文件未登记）。这是已知
  且已登记的，不必作为发现提出。
- `split_preview.py` 是别的车道的地盘，本卡只读；对它内部实现的意见请标注为
  「移交」而不是本卡的 BLOCKER/HIGH。
