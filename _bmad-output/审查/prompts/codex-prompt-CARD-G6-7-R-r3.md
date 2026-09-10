# 代码审查请求 — CARD-G6-7-R **round-3**（批次 BATCH-2026-09-07-第十三批）

> **本轮是 round-3。** 前两轮结论与整改：
> - round-1（`_bmad-output/审查/codex-review-CARD-G6-7-R.md`）：3 HIGH + 3 MEDIUM，全部已改，
>   commit `9e264201`。
> - round-2（`_bmad-output/审查/codex-review-CARD-G6-7-R-r2.md`）：2 HIGH + 1 MEDIUM + 3 LOW，
>   全部已改，commit `f3546d29`。
>
> round-2 六条的整改要点（**请独立复核，不要因为「上一轮提的」就默认改对了**）：
> - **H1（隔离用过期判断）**：`load_state` 的「读 + 判断 + 隔离改名」整段收进 `state_locked`，
>   并在隔离前**锁内再读一次**。解析/校验与归一化拆成 `_parse_state_file` / `_normalize_state`。
>   请核：重读一次是否真的把那个时序堵住了？它自己有没有引入新的窗口（例如两次读之间文件又变）？
>   `load_state` 现在会取锁并因此**创建锁文件** —— 这会不会让某条只读路径开始写盘？
>   （作者主张 GET 路径走 `_read_board_done`，不调 `load_state`。）
> - **H2（硬链接）**：取锁后 `os.fstat` 校验 `st_nlink != 1` 即拒。请核：这条判断放在
>   `lockf` 之前是否正确？失败路径的 fd 与 RLock 是否都释放了？`st_nlink` 之外还有没有别的
>   共享 inode 的形态？正常运行中会不会出现 `st_nlink != 1` 的假阳性（例如备份工具）？
> - **M1（时间门握手）**：子进程先对同一个锁文件做一次真实的非阻塞取锁，把 `blocked`/`free`
>   写进握手标记，父进程断言标记**内容**。请核：这是否真的把「ready 之后又停顿」这个解释排除了？
>   探测用的那次 `open`+`close` 会不会影响子进程随后的阻塞取锁？
> - **L1**：版本单调门补了 `mine=2 / theirs=1` 这个真正需要 `max` 特判的方向。
> - **L2**：三处 docstring 与实现对齐，并写明快照按**路径**而非按对象绑定。
> - **L3**：`state_passed` 改由 `_rebuild_projection` 如实填（debounced / in_progress 一律 false）。
>
> 作者另跑了逐条回退的负控（`_bmad-output/审查/evidence-g67r/neg-r2-*.txt`）：R2H1 / R2H2 /
> MAX / M1 / L3 五条变异各自精确打红对应的那道门，还原 sha 逐字节相同。**请独立判断这个负控
> 是否充分**，尤其是有没有哪条新门即使把对应修法退回去也仍然绿。

## 一 背景与最小读取面

树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime`
基线 `BASE = 709beb0bfa63348394f49f2b7fc6fa829c40b947`，审查对象 `HEAD = f3546d290da0065c7bad910a939a6ae83a86307f`。

本卡收口一张前序卡（Y2-B / CARD-G6-7）留下的六条残留。系统是一个本地桌面学习应用：
一个 launchd 定时任务（runner，`scripts/daily_review_run.py`）每小时跑一次，扫节点、算出「今天先复习哪块白板」
并推送；一个本地后端网页（`review_overview.py` / `review_app.py`）显示同一份结果，并让用户点
「这板做完了」。两者**读写同一个 JSON 状态文件** `backups/daily-review.<vault_key>.state.json`。

请只读以下范围（按重要性排序）：

1. **全量改动**：`_bmad-output/审查/evidence-g67r/diff-BASE-to-f3546d290da0065c7bad910a939a6ae83a86307f.txt`
   （等价于 `git diff BASE HEAD -- . ':(exclude)_bmad-output'`）
2. `scripts/daily_review_run.py` 全文，重点：
   - `load_state` :84-146（base 快照记录点）
   - `state_lock_path` :148 / `_state_lock_key` :158 / `_held_locks` :164 / `_state_lock_held` :170
   - `state_locked` :176-235（可重入上下文管理器）
   - `_merge_state_with_disk` :237-281（三方合并律）
   - `_state_tmp_path` :283-292 与 `save_state` :294-330（**前序卡审后重写的那一段**：唯一名 tmp +
     `O_EXCL|O_NOFOLLOW` + 失败 unlink + `os.replace`；本卡在其外叠加了锁与合并）
3. `backend/app/api/v1/endpoints/review_overview.py`：
   `_board_table_html` :1239 / `_board_undone_form_html` :1356 / `_boards_split_html` :1381 /
   `_run_pick` :1682 / `_rebuild_projection` :1819（写侧承诺 ①②）/ `_refresh_state_file` :2073 /
   `_write_board_done` :2244 / `_write_board_undone` :2322 / `review_overview_refresh` :2505 /
   `review_overview_board_done` :2606 / `review_overview_board_undone` :2684
4. `backend/app/api/v1/endpoints/review_app.py`（单文件零依赖网页）：
   `boardUndoneBtnHtml` :318 / `boardsSplitHtml` :325 / `boardTableHtml` :340 /
   `renderBoardUndoneResult` :472 / `onBoardDoneClick` :681 / `undoButtons` :724 /
   `onBoardUndoneClick` :728 / 事件挂载 :764-766 / URL 表（文件末尾 `review_overview_app`）
5. `scripts/daily_review_pick.py::main` :1205-1275（`--state` 读两个键）
6. 本卡新增/改动的门：
   - `backend/tests/regression/test_daily_review_run.py` 尾部 `test_g67r_*` 六条（锁门与升版行为门）
   - `backend/tests/unit/test_review_overview.py`：`_tree` :1321、
     `test_g67_board_done_writes_only_state_and_never_touches_fsrs` :2875（**本卡把写面允许集从两项
     扩到三项并加了两条钉住断言**）、`test_g67_fsrs_gate_reddens_under_contaminating_write_point` :2946、
     文件尾部 `test_g67r_*` 九条
   - `backend/tests/unit/test_review_app.py` 尾部 `test_js_g67r_*` 两条
   - `backend/tests/regression/test_daily_review_pick.py` 尾部 `test_g67r_*` 两条
7. 参考既有语义门（本卡未改，须仍成立）：`test_review_overview.py` 中
   `test_g67_board_done_survives_symlinked_tmp` 一族三条（tmp 软链 / 陈旧残渣 / 旧固定名）。

## 二 作者自述（请独立核对，不要采信）

1. **手动刷新带完成账**：`_run_pick` / `_rebuild_projection` 加了可选 `state_file`，非 None 时 argv
   追加 `--state <path>`；`review_overview_refresh` 用 `_refresh_state_file` 取 runner 的 state 路径
   （runner 不可达 → 不传，响应加性字段 `state_passed: false`，**不** 503）；`pick.main` 从**同一次**
   JSON 解析里取 `board_last_recommended` 与 `board_done`。顺带修掉「`--state` 指向顶层非 dict 的
   JSON（如 `[]`）会让 `.get` 抛 AttributeError、整轮生成崩掉」的既有缺陷。
2. **跨进程锁 + 锁内三方合并**：新增文件锁 `backups/daily-review.<key>.state.lock`（`fcntl.lockf`
   `LOCK_EX` 阻塞式）。合并律：`load_state` 把**归一化前**的磁盘内容深拷贝为 `base`；`save_state`
   锁内重读磁盘为 `theirs`；某个顶层键 `mine` 与 `base` 不同（含被删）⇒ 写 `mine`，相同 ⇒ 写
   `theirs`；`base` 缺席或 `theirs` 读不出 ⇒ 整写 `mine`（= 本卡之前的行为）。
   锁可重入：进程内 `(resolve 后路径 → [fd, depth])` 登记表 + per-path `RLock` + `threading.local`
   记本线程持有；`save_state` 检测到本线程已持锁就复用那把 fd，**不再 open/close 锁文件**。
   `save_state` 未持锁时先取锁再自调一次（而不是把主体包进 `with`），目的是让
   `O_EXCL|O_NOFOLLOW` 的 `os.open` 与 `os.replace` 两行连缩进都不变。
3. **取消完成入口**：`POST /overview/board-undone`，复用同源门 / 容纳门 / 板名长度门（三个函数各
   仍只定义一次）；键不存在 ⇒ 幂等 200 `already_undone: true` 且**不落盘**；零 JS 表单进「已完成」
   折叠区每行，交互壳撤销钮用 `data-undo-*` 属性（与完成钮的 `data-done-*` 分开），共享
   `doneInflight` 在飞表；`method: "POST"` 全页 3 处，都在点击处理器体内。
4. **v1→v2 升版三条行为门**（落盘面而非内存面）：值不变 / 二次落盘字节幂等 / 错型隔离时
   `.corrupt-*` 字节 == 原文件。不新建迁移器 —— 加性升版本来就由 `load_state` 完成，
   `migrate_daily_review_state.py` 是另一件事（命名空间迁移）。
5. **写面允许集由两项扩为三项**：`_tree` 的全树指纹差集断言原本是
   `{"backups", f"backups/{state_file.name}"}`，锁文件必然落在 `backups/` 里，故扩为三项，
   并新增两条钉住断言：锁文件字节长度恒 0、锁文件不在 vault 内。作者主张这不是放宽。
6. 另有一处既有门改动：「已完成板不该再带完成钮」原判据是数 `name="board"` 出现次数（撤销表单的
   hidden input 同名，计数不再表达那个意图），改为按 `action=` 归属判定。

## 三 请按重要性排序回答的问题

1. 前序卡审后重写的 `save_state`（唯一名 tmp + `O_EXCL|O_NOFOLLOW` + 失败 unlink + `os.replace`）
   叠加本卡的锁与合并之后，下面四条是否仍然成立：tmp 不跟随符号链接、写失败时 unlink 掉 tmp、
   `os.replace` 的原子发布语义、以及**锁 fd 不会被 tmp 的 open/close 连带释放**？
2. 合并律「我没改的键不许被我覆盖」有没有反例，能让本卡那两条方向相反的门（runner 向 / Web 向）
   都绿、而真实并发下仍丢字段？特别请检查：`base` 快照取的时刻是否正确、归一化产生的键
   （`schema_version` 升版、`board_done` setdefault）归属是否讲得通、缺文件与损坏两个分支、
   以及模块级快照表在多线程下会不会被同一 vault 的另一个请求覆盖。
3. 锁门（`test_g67r_state_lock_blocks_other_process_until_released`）的时间戳判据能否被「子进程
   其实没做事」满足？其中的对照组（不持锁时子进程很快完成）是否真的承重？
4. `refresh` 传 `--state` 之后，生产器是否存在任何路径会**写** state 文件？（`_rebuild_projection`
   的写侧承诺 ① 声称写面只有 `outputs/今日复习.{md,json}`，②声称不碰 state，这两条是否仍成立？）
5. 撤销端点是否真的复用了那三道门（而不是复制了一份）？幂等 200 会不会掩盖「板名根本不在账里」
   这种输入错误，`already_undone` 字段是否足以让调用方分辨？
6. 三条 POST 路径里，有没有任何一条可能被定时轮询或 `visibilitychange` 触发？
7. 三条升版行为门是否真能区分「`load_state` 完成了加性升版」与「没升版但测试自己补了键」？
8. 写面允许集扩到三项之后是否**实质变松**？两条钉住断言（锁文件 0 字节、锁文件不在 vault 内）
   能否被「往锁文件里写内容」或「把锁放进 vault」这两种改法照出来？`_tree` 的「key 集合本身进
   指纹」这条语义有没有在扩集时被削弱？另外三处用 `_tree` 的用例（:1419/:1421、:1610/:1616、
   :3137/:3140，作者称都不走 `save_state`、本卡应零变化）是否真的没被顺手改松？
9. 锁的重入登记表（`(resolve 后路径 → [fd, depth])` + `save_state` 的复用分支）是否真的做到了
   「持锁期间不对锁文件再 open/close」？有没有任何路径 —— 异常回滚、多线程、嵌套三层以上、
   同一文件的两种路径写法 —— 会让 `depth` 泄漏，或让内层的 `close` 把外层的锁一起释放？
   本卡的重入门（`with` 体内非阻塞探测必失败 / 退出后必成功）两半是否都承重？
10. `save_state` 用「未持锁则先取锁再自调一次」这种自调用写法（目的是不改那两行的缩进），
    有没有可能出现不终止的自调用，或在异常路径下把锁留着不放？

## 四 输出格式

按 BLOCKER / HIGH / MEDIUM / LOW 四级分类，每条给出 `file:line`、问题陈述、以及一个具体的
失败情形（什么输入或时序 → 什么错误结果）。没有问题的级别请明确写「无」。

## 五 边界

- 只读审查，不要修改任何文件。
- 不要连接数据库（本机 7691 / 7687 端口），本卡没有数据库面。
- 推迟（snooze）功能**不在本卡范围**，归后续卡；请不要把「没有 snooze」当成缺陷。
- `scripts/daily-review-push.sh`、`scripts/launchd/*`、`scripts/migrate_daily_review_state.py`
  是本卡的禁改面，只作为上下文参考。
- `canvas-vault/.claude/scripts/fsrs_bridge.py` 与 `decay_beta.py` 本卡零写入。
