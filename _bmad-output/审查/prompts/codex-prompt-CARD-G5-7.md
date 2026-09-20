# CARD-G5-7 独立复核 —— clear-inbox 执行侧（inbox_apply.py + undo_journal.py）

## ① 背景与最小读取面（请只读下面列出的东西，不要漫游全仓）

仓根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x`

这是一个本地 Obsidian vault 的「待处理收件箱清仓」工具链。上一张卡（G5-6）做了
**只读**的盘点提名 preview；本卡（G5-7）补执行侧：读 preview 的 JSON + 用户逐条
拍板的 decisions，把材料 copy / 硬链接 / move / 移入回收目录 / 留原地，并落一本
可一键撤销的账。

本卡新增恰三份文件，全文请看：

```
git --no-pager diff --no-color 9c4e7e82 HEAD -- . ':(exclude)_bmad-output'
```

即：
- `canvas-vault/.claude/scripts/undo_journal.py`（NEW，共用模块）
- `canvas-vault/.claude/skills/clear-inbox/scripts/inbox_apply.py`（NEW，执行侧 CLI）
- `backend/tests/skills/test_g5_7_inbox_apply.py`（NEW，29 个承重行为用例）

为读懂契约，还需要看这些**既有**文件的片段（本卡只读、零改动）：

- `canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py`
  - `:266-292`（兄弟模块加载器 + `sys.dont_write_bytecode`）
  - `:300-330`（常量：`SCHEMA_VERSION` / `DEFAULT_INBOX_NAME` / `BATCH_MAX` /
    `CORPUS_EXCLUDED_DIR_NAMES`）
  - `:385-396`（verdict 词表，含 `human_only`）
  - `:1876-1914`（提名字段 `_fill`）
  - `:1917-1983`（`list_inbox`：每件 item 的键，含 `stable_id` / `rel_path` /
    `size_bytes` / `mtime_utc`；symlink / 子目录 / 非普通文件的跳过口径）
  - `:2143-2186`（preview JSON 顶层键，含 `vault_fingerprint` 的算式）
  - `:2395-2479`（`main` 的准入次序铁律：全部守卫跑完再碰 out-dir）
- `canvas-vault/.claude/skills/board-split/scripts/split_preview.py` `:1734-1860`
  （写侧物理原语：`assert_symlink_free` / `safe_open_checked` /
  `write_pair_atomically_checked` / `safe_write_text` / `prepare_out_dir`）

另外请顺带复核一段**历史**生产改动（上一张卡留下的、当时未做独立复核的三处）：

```
git --no-pager diff --no-color ac949f6f 69fce02c -- canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py
```

（+14/-5，把三处残留的 Unicode 语义 `.strip()` 收窄到 ASCII。）请单独给结论。

## ② 作者自述 —— 请独立核对，不要采信

1. **默认路径 0 物理删除**：两份新文件里没有任何 `os.remove` / `os.unlink` /
   `Path.unlink` / `shutil.rmtree` / `os.rmdir` / `send2trash` 的调用。「删」= 移进
   `<work-dir>/<batch_id>/recycle/` 留痕。撤销 copy/link 时产物移进
   `recycle/undone/`，写失败的 `.tmp` 挪进 `stale/`。
2. **双重显式确认**：`recycle` 需要整批 `--confirm-recycle` **且**该条
   `confirm is True`（严格布尔，不认真值），缺一即整批拒绝且连 `outputs/` 这一级
   都不建出来。
3. **准入次序**：全部守卫（vault / preview schema 与指纹 / decisions schema /
   stable_id 已知且不重复 / 实盘 size 与 mtime 对得上 preview / 源非 symlink 且是
   普通文件 / target 白名单 / 落点未被占 / recycle 双确认）跑完**再**创建工作目录。
4. **undo 全树逐字节**：撤销后 vault 树（排除工作目录）的 sha256 + `st_mtime_ns` +
   `st_mode` 与执行前逐项相等，目录的 mtime 也还原。
5. **中断重跑幂等**：`batch_id = sha256(vault 指纹 + preview 文件 sha + decisions
   文件 sha)[:12]`，同输入落同一本账，`done` 行复核后跳过，`planned` 未 `done` 的
   从主动作起重跑；每一步（copyfile 覆写 / os.replace / provenance 整键替换 /
   utime）都写成可重入的。
6. **执行侧对自由文本零消费**：不读 `basis` / `ask` / `uncertain_reason` /
   `criterion` / `near_duplicates` / `conflicts` / `exact_duplicate_others`。
7. **不加 SKILL.md**，不改 `inbox_preview.py` / `split_preview.py` /
   `skill_portability_lint.py` / `test_g5_6_clear_inbox.py`。

## ③ 按重要性排序的问题

0. `recycle` 的双确认能不能被一份精心构造的 decisions 文件绕过？`confirm` 的
   类型与真值判定是否严格？`--confirm-recycle` 与逐件 `confirm` 是否真的缺一即拒、
   且拒绝时零写？
1. `undo()` 逆序还原时，如果同一批里既 `move` 又 `recycle` 了同一个路径、或者
   落点在执行之后被用户改动过 / 原路径被用户放了新文件，会不会覆盖用户的新内容？
   （作者声称比 sha 后拒绝——请核对每条分支。）目录 mtime 的还原会不会掩盖用户
   在此期间对该目录做的别的改动？
2. journal 的单行原子追加，在写到一半掉电留下半行时，重跑怎么识别？
   （作者声称：末尾解析失败的那一行按截断处理并补一个换行 + 哨兵行封口；中间
   解析失败一律拒绝。）封口后的哨兵行在下一次重跑时会不会被判成「中间损坏」？
3. `batch_id` 由三份输入的 sha 派生。如果用户用**同样的** `--now` 重新生成了一份
   内容相同、路径相同的 preview，是否仍然幂等？如果换了 `--now` 呢（作者声称会被
   「落点已被占」那道守卫拦下）？
4. provenance frontmatter 的插入，对「没有 frontmatter」/「非 UTF-8」/「CRLF」/
   「已经有同名键」/「frontmatter 没有收尾 `---`」这些输入分别怎么处理？会不会
   把 CRLF 归一成 LF？会不会在编码失败时留下一个被截断的原件？
5. `link` 走 `os.link` 硬链接，跨文件系统会拿到 `EXDEV`。回执是否精确？会不会
   留下半态（账上记了但盘上没有，或反过来）？
6. target 白名单：是否真的用 realpath 判边界、且拒绝祖先目录是 symlink 的情形？
   （`O_NOFOLLOW` 只管路径末段。）`..` / 绝对路径 / 指回收件箱 / 指向工作目录 /
   首段是 `.claude` `.obsidian` `outputs` 这些情形是否都拦住了？
7. 上面 ① 里那段历史 diff（`ac949f6f..69fce02c`，+14/-5）本身是否引入缺陷？
8. 两份新文件复用了 `split_preview.write_pair_atomically_checked` 来成对发布回执，
   而那个函数内部含一处 `os.unlink`（回滚它自己刚 `O_CREAT` 出来的 0 字节文件）。
   作者的「0 物理删除」主张只覆盖本卡这两份文件。这个边界声明是否站得住？有没有
   办法让那处 unlink 碰到用户的既有文件？

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
- 不要评价 `undo_journal.py` 将来被 G5-10 复用时的白板派生语义（那是下一张卡），
  也不要评价 G8-2c 的变异复跑。
- 不要建议给 clear-inbox 加 `SKILL.md`（那会触发另一套基线漂移，属别人的地盘）。
- `backend/tests/skills/skill_portability_lint.py` 的两条基线（`SCRIPTS_BASELINE` /
  `MANAGED_FILE_DIGESTS`）目前**不含**这两份新脚本，因此 `tests/skills` 有 4 条
  预期红，全部是同一根因（新文件未登记）。这是已知且已登记的，不必作为发现提出。
