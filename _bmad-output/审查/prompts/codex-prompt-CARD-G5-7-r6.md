# CARD-G5-7 独立复核 round-6（绑**最终 HEAD**）—— clear-inbox 执行侧

## ① 背景与最小读取面（请只读下面列出的东西，不要漫游全仓）

仓根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x`
本轮审查绑定：**`242026f5e16dcb4af263a64fdb6d6713c22625c2`（= 当前 HEAD，工作树干净）**

本地 Obsidian vault 的「待处理收件箱清仓」工具链。上一张卡做了**只读**的盘点提名
preview；本卡补执行侧：读 preview 的 JSON + 用户逐条拍板的 decisions，把材料
copy / 硬链接 / move / 移入回收目录 / 留原地，并落一本可一键撤销的账。
**默认路径 0 物理删除**是本卡的核心不变量（AST 门数 `Call` 节点，不数文本）。
在本卡语境里「覆盖」与「删除」同等严重 —— 用户的文件被无声换掉就是弄丢。

本卡新增恰三份文件，全文：

```
git --no-pager diff --no-color 9c4e7e82 HEAD -- . ':(exclude)_bmad-output'
```

即：
- `canvas-vault/.claude/scripts/undo_journal.py`（NEW，1316 行，共用模块）
- `canvas-vault/.claude/skills/clear-inbox/scripts/inbox_apply.py`（NEW，965 行，执行侧 CLI）
- `backend/tests/skills/test_g5_7_inbox_apply.py`（NEW，103 个承重行为用例）

**本轮的重点读取面**（round-5 绑定 `293f8d6a` 之后的全部改动，约 1400 行）：

```
git --no-pager diff --no-color 293f8d6a HEAD -- . ':(exclude)_bmad-output'
```

其中**最新、被看过最少**的是最后两段：

```
git --no-pager diff --no-color 9ad71fe9 67951095 -- . ':(exclude)_bmad-output'   # 独立复核 r1 的整改
git --no-pager diff --no-color 67951095 HEAD     -- . ':(exclude)_bmad-output'   # 独立复核 r2 的整改
```

为读懂契约，还需要看这些**既有**文件的片段（本卡只读、零改动）：

- `canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py`
  `:266-292`（加载器）/ `:300-330`（常量）/ `:385-396`（verdict 词表）/
  `:1876-1914`（提名字段）/ `:1917-1983`（item 键与跳过口径）/
  `:2143-2186`（JSON 顶层键与 `vault_fingerprint` 算式）/ `:2395-2479`（准入次序）
- `canvas-vault/.claude/skills/board-split/scripts/split_preview.py` `:1734-1860`
  （写侧物理原语；本卡只复用其中的 `assert_symlink_free`）

另有一段**历史**生产改动，round-1 已判 PASS，本轮如无新意见可一句带过：

```
git --no-pager diff --no-color ac949f6f 69fce02c -- canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py
```

## ② 这一卡到现在为止被审过几次、每次改了什么（请当成**待验证的命题**，不是事实）

- **Codex round-1..5**（绑定依次 `1d3e75b3` / `a159bdcf` / `421afe85` / `14fe7703` / `293f8d6a`）：
  共 69 条，作者逐条认定为真并全部整改。round-5 收尾时 BLOCKER 0 / HIGH 3，
  按 D-15「上限 5」停下交主 session。**五轮里没有任何一轮绑着最终 HEAD。**
- **其后作者又做了两轮独立 Agent 对抗性复核**（Codex 轮次已用尽，故换成 Agent）：
  - **r1**（读 `293f8d6a..9ad71fe9`）：HIGH 1 / MEDIUM 3 / LOW 5。
    HIGH-1 = 回执落点的「自家产物」判据原先是 `batch_id in 文件字节` 的**子串启发式**
    （与模块自己写在 docstring 里的「判据是可计算的等式」铁律正面冲突）⇒ 改成 sha256
    等式，账本新增 `receipt_sha` 行记「上一次往该落点写下去的内容的 sha」。
    MEDIUM-1 = `write_pair_atomically` 原先在同一个循环里先校验再「停放」(会动盘)
    ⇒ 拆成「只读校验段 + 动盘段」。MEDIUM-2 = 无计数封口哨兵原先跨整段坏行
    ⇒ 收回成只覆盖紧邻一条。MEDIUM-3 = 残片位置挂在 `__notes__` 上但调用方只打印
    `str(e)` ⇒ 打印时带上。LOW-1 TOCTOU **登记未修**。
  - **r2**（读 `9ad71fe9..67951095`，即 r1 整改自己）：存活 3 个真缺陷，
    **其中两个是 r1 整改自己引入的回退**：
    - **D-1**：两段式只在 `stale_dir is None` 时于校验段拒绝；它有值但**不可用**
      （被占成普通文件 / symlink / 祖先链含 symlink）时校验段放行，真正的拒绝被推迟到
      逐条 `os.replace` 的循环里 —— 第一份已经就位之后第二份才说「留不住」，发布出去的
      一对回执互相矛盾。同一条输入在两段式**之前**是零写的。
      修法：新增 `assert_stale_dir_usable` 在校验段先证留痕可行；并把**全部留痕做完**
      再做**任何一次** replace（第二段 park-all / 第三段 replace-all）。
    - **D-2**：`record_receipt_shas` 是全模块唯一可能在 `load()` 自己抛过之后仍被调用到的
      `_append` 点（撤销失败 → 写失败回执 → 落账），不封口直接 `O_APPEND` 会把账尾
      「完整但缺结尾换行」的那条记录粘成一条烂行。
      修法：先 `read_rows()` + `seal_tail_if_needed()`；`read_rows()` 抛 ⇒ 一个字节都不写。
    - **D-3**：残片位置报的是**停放之前**的路径（`_replace_or_park` 丢掉了 `_park_stale`
      的返回值）。修法：把停放后的真实位置挂到异常的 `_uj_residue` 上。
  - r2 另补一道**补覆盖**门：D-1 的前置门把既有门
    `test_receipt_refuses_when_the_foreign_file_cannot_be_parked` 的覆盖面吃掉了
    （它现在在第一段就被拒），于是动盘段那一支无人看管；新门用「真目录但 `chmod 0o500`」
    的 stale/ 把第二段重新盖上。

**门的覆盖**：r1 的 5 道新门喂给 `9ad71fe9` 归档树 → 7 红 / 92 绿；r2 的 3 道新门喂给
`67951095` 归档树 → **3 红 / 99 绿**（99 条旧门全绿）。负控四段（拆 `--confirm-recycle`
/ 拆撤销的 `os.utime` / 源新鲜度 `lstat`→`stat` / 拆动盘段的拒绝分支）各自只有点名的那道门变红。

## ③ 按重要性排序的问题

0. **本轮请特别盯 r2 的三处整改**（`67951095..HEAD`，`undo_journal.py` +76/-12）——
   它们是全卡最新、也是被独立意见看过最少的一段。r1 的整改已经被证明引入过回退，
   r2 的整改会不会重演同一件事？
1. `write_pair_atomically` 现在是**三段**（只读校验 / park-all / replace-all）。
   - 第一段真的一个字节都不动盘吗？`assert_stale_dir_usable` 自己会不会动盘
     （`_park_stale` 里有 `os.makedirs`，但那是第二段才走到的路径 —— 请核）？
   - park-all 与 replace-all 之间、以及两次 replace 之间被中断，各会留下什么状态？
     账本能不能表示「只就位了一份」？作者如实声明了哪些、漏掉了哪些？
   - 把「先停旧的、再放新的」拆开之后，是否重新打开了 round-5 HIGH-2 那个
     「正式路径两头都不在」的窗口？作用域是否仍然只到回执落点、没碰业务文件？
2. `assert_stale_dir_usable` 的判定面：`None` / symlink / 存在但非目录 / 祖先链含 symlink。
   有没有哪种**静态可判**的不可用情形漏在外面？它把 `SystemExit` 统一成 `JournalError`，
   这个转换会不会吞掉某类本该往上冒的失败？
3. `record_receipt_shas` 现在先 `read_rows()` 再 `seal_tail_if_needed()` 再 `_append`。
   - 这条路径本身会不会在某种账本形态上**写坏**账（比如封口哨兵自己写到一半）？
   - 它对 `_tail_unterminated` / `_tail_malformed` 这两个实例状态的读写时序，与
     `run_apply` 那条正常路径（`load()` 之后一路 `_append`）是否相容？同一个
     `BatchJournal` 对象在一次进程里被这两条路径交替使用时呢？
   - 「账读不回来就不写」的代价是下一次重跑把自家上一版回执当外来文件挪进 `stale/`。
     这个降级方向对吗？
4. `_replace_or_park` 往异常上挂 `_uj_residue`。挂属性对某些内建异常会失败（已 try 住），
   但**属性会随异常一路往上传**——有没有哪个上层 `except` 会拿到一个语义已经不适用的
   `_uj_residue`？`residues` 的第一项与其余项现在是同一口径了吗？
5. `receipt_sha` 这条新 state 进了 `KNOWN_STATES`。所有**读**账本的地方
   （`latest_by_seq` / `_entries_to_undo` / `read_rows` 的坏行判定与封口回溯 /
   `_assert_bound_to` / 撤销的四种入口）有没有哪一处会把这条非业务行当业务行、
   或者被它挤掉覆盖面？`SCHEMA_VERSION` 没升，有影响吗？
6. 103 个用例里有没有哪一条**断言不了它声称断言的事**（比如绿在更早的一道判据上、
   夹具在断言前就抛了、只断言 rc）？特别是 r1/r2 新增的那 8 条。
7. 默认路径 0 物理删除这条不变量，在 `9c4e7e82..HEAD` 全量上还成立吗？
   有没有哪条路径能让用户的文件在**没有留痕**的情况下被换掉或清空？

## ④ 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给：
- `file:line`
- 一句话说明缺陷是什么
- 一句复现思路：**哪一个输入没有被拦下** / 用**哪一个对照输入**能看出差别 /
  **门没有覆盖到哪一条路径** / 如果把某处改坏了、**哪一条判据应该变红而实际不会**

没找到问题就明说「无」——「没找到」是有价值的结论，凑数不是。

请不要使用「构造攻击载荷 / 可复现的利用片段 / 打穿 / 绕过防护」这类措辞，
本审查的边界是代码正确性与数据安全，不是攻防演练。

## ⑤ 边界

- **只读**。不要修改任何文件，不要运行会写盘的命令。
- 不要连接任何数据库或网络服务（本卡零外部依赖）。
- 不要评价 `undo_journal.py` 将来被 G5-10 复用时的白板派生语义（那是下一张卡）。
- 不要建议给 clear-inbox 加 `SKILL.md`（那会触发另一套基线漂移，属别人的地盘）。
- `backend/tests/skills/skill_portability_lint.py` 的两条基线目前**不含**这两份新脚本，
  因此 `tests/skills` 有 4 条预期红，全部是同一根因（新文件未登记）。已知且已登记，
  不必作为发现提出。
- `split_preview.py` / `inbox_preview.py` 是别的车道的地盘，本卡只读；对它们内部实现的
  意见请标注为「移交」而不是本卡的 BLOCKER/HIGH。
- 以下几条**已登记未修**，不必重复提出：LOW-1 TOCTOU（`check_destinations_free` 与实际
  搬动之间的窗口）、`st_nlink != 1` 在异种文件系统上未实测、跨进程并发无行为门、
  撤销不删自己造出的空目录、`rel_path` 的 NFC/NFD 等价未判定、
  `record_receipt_shas` 落账失败是尽力而为。
