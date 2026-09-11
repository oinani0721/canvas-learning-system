# 代码审查请求 — CARD-G6-7-R **round-2**（批次 BATCH-2026-09-07-第十三批）

> **本轮是 round-2。** round-1 你给出 3 条 HIGH（H1 升版空账覆盖窗口内写入 /
> H2 base 缺席分支不读磁盘就整写 / H3 锁文件跟随软链）与 3 条 MEDIUM
> （M1 取锁异常逃逸成 500 / M2 非 UTF-8 state 打死刷新 / M3 锁时间门可被启动延迟满足），
> 并在第 5 问指出板名门是复制而非复用。**六条全部已整改**，另按你的指正把板名门抽成
> `_assert_board_name`、把 `already_undone` 的前端文案单独成句。
> round-1 报告原文：`_bmad-output/审查/codex-review-CARD-G6-7-R.md`。
> 整改的 commit：`9e264201`（`git show 9e264201` 可看逐行）。
>
> **本轮请重点核对**（其余分节沿用，仍请独立复核，不要因为「上一轮说过」就放行）：
> - H1 的修法是把 base 快照从归一化之前挪到之后，并给 `schema_version` 加了单调取大的
>   特判。这个特判是否引入了新的丢失面？（例如磁盘上被人写成一个更大的假版本号之后，
>   本进程再也推不动形态？或者 `schema_version` 缺席 / 非 int 时的行为？）
> - H2 的修法是把「文件不存在」「损坏隔离重建」两个分支的 base 记成**那份默认空账本身**。
>   真正无快照（`st` 不是本进程 `load_state` 来的）仍走整写。这两条路的分界是否讲得通？
>   既有的「改了就写」语义（`test_g67_state_path_takes_explicit_vault_without_touching_global`
>   一族）是否仍成立？
> - H3 加了 `O_NOFOLLOW`。取锁失败之后的清理路径是否完整（fd 泄漏、登记表残留、
>   per-path RLock 是否被正确释放）？`ELOOP` 之外还有没有别的软链形态会让这道判断失效？
> - M1 把 `state_locked` 纳入 `try` 之后，`_write_board_undone` 的**幂等 early return**
>   （`return state_file, True`，写在 `with` 体内、`try` 内）是否仍正确释放锁？
> - M3 的就绪握手是否真的把「启动延迟」这个解释排除掉了？握手标记到真正 `lockf` 之间
>   仍有一小段窗口，这段窗口会不会让门重新变得可被满足？
> - 新补的五条门（`test_g67r_state_lock_refuses_symlinked_lock_path`、
>   `..._fresh_state_does_not_clobber_account_created_in_the_window`、
>   `..._upgrade_default_account_does_not_clobber_window_write`、
>   `..._schema_version_never_goes_backwards_on_merge`、
>   `..._lock_acquisition_failure_is_503_not_500`）是否都承重？有没有哪一条即使把对应
>   修法退回去也仍然绿？（作者已跑过逐条回退的负控，结果是三条修法各自精确打红对应的
>   那一道门；请独立判断这个负控本身是否充分。）

## 一 背景与最小读取面

树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime`
基线 `BASE = 709beb0bfa63348394f49f2b7fc6fa829c40b947`，审查对象 `HEAD = 9e264201d6f97a237a74d7c9a11be406cc0cdac8`。

本卡收口一张前序卡（Y2-B / CARD-G6-7）留下的六条残留。系统是一个本地桌面学习应用：
一个 launchd 定时任务（runner，`scripts/daily_review_run.py`）每小时跑一次，扫节点、算出「今天先复习哪块白板」
并推送；一个本地后端网页（`review_overview.py` / `review_app.py`）显示同一份结果，并让用户点
「这板做完了」。两者**读写同一个 JSON 状态文件** `backups/daily-review.<vault_key>.state.json`。

请只读以下范围（按重要性排序）：

1. **全量改动**：`_bmad-output/审查/evidence-g67r/diff-BASE-to-9e264201d6f97a237a74d7c9a11be406cc0cdac8.txt`
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
