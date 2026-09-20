# CARD-G5-7 独立复核 round-3 —— clear-inbox 执行侧

## ① 背景与最小读取面（请只读下面列出的东西，不要漫游全仓）

仓根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x`

本地 Obsidian vault 的「待处理收件箱清仓」工具链。上一张卡做了**只读**的盘点提名
preview；本卡补执行侧：读 preview 的 JSON + 用户逐条拍板的 decisions，把材料
copy / 硬链接 / move / 移入回收目录 / 留原地，并落一本可一键撤销的账。

- round-1（绑 `1d3e75b3`）：12 HIGH + 3 MEDIUM，作者全部认定为真、全部整改。
- round-2（绑 `a159bdcf`）：9 HIGH + 7 MEDIUM + 2 LOW，作者**同样全部认定为真、全部
  整改**，无一驳回。本轮请在整改之后重新判，并特别检查整改本身有没有引入新问题。

本卡新增恰三份文件，全文请看：

```
git --no-pager diff --no-color 9c4e7e82 HEAD -- . ':(exclude)_bmad-output'
```

- `canvas-vault/.claude/scripts/undo_journal.py`（NEW，共用模块）
- `canvas-vault/.claude/skills/clear-inbox/scripts/inbox_apply.py`（NEW，执行侧 CLI）
- `backend/tests/skills/test_g5_7_inbox_apply.py`（NEW，64 个承重行为用例）

round-2 → round-3 的改动面：

```
git --no-pager diff --no-color a159bdcf HEAD -- . ':(exclude)_bmad-output'
```

契约面（本卡只读、零改动）：`inbox_preview.py` 的 `:266-292` / `:300-330` /
`:385-396` / `:1876-1914` / `:1917-1983` / `:2143-2186` / `:2395-2479`；
`board-split/scripts/split_preview.py` `:1734-1860`（本卡现在只复用其中的
`assert_symlink_free`）。

## ② round-2 十八条的整改

| # | round-2 意见 | 整改 |
|---|---|---|
| H1 | 归属判定靠「全文包含 batch_id 子串」的启发式 | 改成**可计算的等式**：`done` 行比 `sha256_after`；`planned` 行比「与备份逐字节相同」或「等于 `expected_after_provenance(备份字节, 后缀, 账上记的 prov_meta)`」。`prov_meta`（含 `applied_at_utc`）在 plan 时就落账，于是期望值完全确定。`carries_batch_marker` 已整个移除 |
| H2 | 撤销的多个中断窗口无法续跑 | `_undo_one` 重构：落点不在时统一走「把原路径收尾到批前态」——覆盖「没执行过」「已还原未记账」「还原到一半（字节回来了、时间/权限没盖回）」三种；原路径上若是本批产物（`sha256_after`）则用备份抹掉溯源 |
| H3 | 历史 `undone` 屏蔽重新执行后的新 `done` | 新增 `latest_by_seq()`：按**同一 seq 的最后一条**业务记录判，不按「出现过没有」。apply 与 undo 两侧都换成它 |
| H4 | 只读（0444）Markdown 搬得动撤不回 | `_rewrite_from_backup` 先 `chmod 0o600` 再写，写完由 `_finish_restore` 按账上的 `mode_before` 盖回 |
| H5 | `recycle/undone/` 这个新落点漏了 symlink 检查 | `_park_product` 对 `undone_root` 与最终落点都过 `assert_symlink_free` / `assert_path_safe` |
| H6 | 先用备份覆盖、事后才验备份 | `_assert_backup_trustworthy` 在**任何搬动之前**调用（存在性 / 普通文件 / 祖先链 / `sha256_before` 相符） |
| H7 | 备份落点可截断不属于本批的文件及其硬链接 | 新增 `copy_file_atomically`：唯一名 tmp → `os.replace`，旧 inode 的其它硬链接原样不动。`backup()` 改走它 |
| H8 | 绑定判据是「指纹出现在集合里」，缺失/混合都放行 | 改成**每一条**业务记录都必须绑当前 vault，任一条缺失或不符即拒 |
| H9 | 被改过的 preview 可指定 vault 外的源 | `source_path` 卡 `rel_path` 形状：相对、无 `..`、恰两段、首段 == 收件箱名、末段 == `name`、realpath 的父目录 == 收件箱 |
| M1 | 没动过盘的 `planned` 阻断前面已完成项的撤销 | 并入 H2 的统一分支：落点不在且原路径完好 ⇒ 收尾 + 记账，不再报错 |
| M2 | 封口本身再中断会形成读不回的 journal | `read_rows` 改为从尾部回扫：坏行与封口哨兵构成的**整段**都算「没写完的尾巴」 |
| M3 | 最大 seq 的目录时间会吸收批中改动 | 目录时间改为**链式**判据：每一步记 `pre` / `at_act` / `post`，要求 `pre == at_act`（排期后动手前没被动过）、`post[k-1] == pre[k]`（两步之间没被动过）、且现值 == 最后一环。`at_act` 在**动手那一刻**重读，专治续跑时 `pre` 是陈旧读数 |
| M4 | YAML 顶格注释让旧 provenance 剥离提前结束 | `_is_block_neutral` 把空行与顶格注释一视同仁，都要向前看下一个有内容的行还缩不缩进 |
| M5 | 跨 vault 测试绿在内容守卫上 | 已把 B 的源与落点都造成与 A 逐字节同；**如实声明**：即便如此，删掉 `_assert_bound_to` 本门仍绿（另一道「创建上界」守卫也会拒），已写进该用例 docstring，`_assert_bound_to` 的承重证明改由 `test_journal_without_fingerprint_is_refused` 承担（删调用即红，已实测） |
| M6 | 目录时间测试只查回执不查实盘 | 加了实盘断言（撤销后该目录的 mtime ≠ 批前值），并用「让跳过分支照样回填」的变异实测该门变红 |
| M7 | `settled` 的 link 在硬链接关系已断时报完成 | `verify_done` 对 `link` 增加「源仍是普通文件」与「`st_ino` 相等」两项 |
| L1 | 最终 `os.replace` 失败时 tmp 不进 `stale/` | 新增 `_replace_or_park`，三处就位全部走它 |
| L2 | 成功重跑清空回执的 `created_dirs` | 已完成分支也汇总旧账上的 `created_dirs` |

**门的覆盖**：上述每条都配了门。把这 16 道新门喂给整改**之前**的 `a159bdcf`，
**16 条全部变红**，其余 48 条仍绿（存档 `evidence-g57/newgates-vs-prefix-r2-*.txt`）；
当前 HEAD 上 64 条全绿。M5/M6 两条是「加强既有门」，各自用点名的变异单独验过。

## ③ 按重要性排序的问题

0. 上表 18 条整改，逐条核对是否真的堵上了 round-2 描述的那条路径；有没有哪一条只是
   把缺陷挪了个位置，或者堵住实例而没堵住同族。
1. `owned_product()` 现在的三条等式（`sha256_after` / `sha256_before` /
   `expected_after_provenance`）还有没有输入能让**不属于本批次**的文件被判成自家产物？
   `expected_after_provenance` 与 `write_provenance` 的分支条件是否真的逐条一致
   （非 .md / 非 UTF-8 / 未闭合 frontmatter / 已是目标形态）？
2. `_undo_one` 现在的分支（落点不在 ×3 种成因、落点还在 ×2 类动作）有没有状态组合
   会导致重复还原、静默跳过、或把「没执行过」误判成「已还原」？
3. 目录时间的链式判据（`pre` / `at_act` / `post`）有没有序列能让它误判为「链没断」？
   `at_act` 只在 `commit` 时写入，`planned` 行没有它 —— 这个不对称会不会出问题？
4. `latest_by_seq` 把「最后一条业务记录」当权威。若同一 seq 在账上出现
   `done → undone → planned` 或更怪的顺序，apply 与 undo 两侧的解读是否仍一致？
5. `copy_file_atomically` / `atomic_write_bytes` / `write_pair_atomically` 三处
   `os.replace` 的失败路径，会不会留下既不在目标、也不在 `stale/` 的残片？
6. `source_path` 的 `rel_path` 形状校验，对 NFC/NFD 不同规范化形式、或路径里含
   `.`、多余斜杠等写法，会不会有漏网或误伤？
7. 64 个用例里有没有哪一条**断言不了它声称断言的事**（绿在更早的一道判据上）？

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
- `split_preview.py` 是别的车道的地盘，本卡只读；对它内部实现的意见请标注为
  「移交」而不是本卡的 BLOCKER/HIGH。
- 历史 `ac949f6f..69fce02c` 前两轮均判 PASS，本轮不必重复复核。
