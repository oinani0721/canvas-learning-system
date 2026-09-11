# 代码审查请求 — CARD-G6-7-R **round-6**（批次 BATCH-2026-09-07-第十三批）

> **本轮是 round-6，超出本项目的 5 轮上限，理由如下，需要你据此给出判断。**
>
> round-5（`codex-review-CARD-G6-7-R-r5.md`，绑 `685e5552`）已给出 **BLOCKER = 0、HIGH = 0**，
> 只剩 2 MEDIUM + 1 LOW，且你当时明确写了「这是测试覆盖问题，当前生产 `LOCK_EX` 没有上述错误」
> 与「当前生产外层锁正确；未闭合的是测试判别力」。按规矩那一轮就该收口。
>
> **收口前的自查发现了一处本卡自己造成的硬边界违规**，必须修，于是多出这一轮：
> - 两条新门用了 `monkeypatch.undo()`。它撤销的是整个 fixture 的**全部**补丁，包括
>   `_patch_runner` 设的 `BACKUPS` —— 之后那句 `save_state` 落到了**真实仓库**的 `backups/`，
>   留下 `daily-review.vault.state.json` 与同名 `.lock`，内容正是那两条门的测试数据。
>   卡文明写「禁写 live backups/（只读）」。
> - 实测影响面：生产 state（`daily-review.canvas-vault.state.json`）与投影的 sha256
>   开工/收工相同，未被动；污染物用的是测试 vault key，生产 runner 读的是另一个 key。
>   污染物**未自行删除**（删除也是一次写 live），处置交人工裁定。
> - 修法两层：① 两处改用 `pytest.MonkeyPatch.context()`，只撤自己的补丁；
>   ② 新增 autouse 护栏 `_forbid_live_backups_writes`，每个用例前后对真实 `backups/` 取
>   （文件名, 大小, mtime）快照比差集，白名单只放行生产 launchd 每小时真的会动的那几个。
>   ⛔ 护栏初版只比**文件名集合**，而上一次污染留下的文件已经在 before 里，
>   于是把缺陷改回去、让它再写一次同名文件，门照样绿（实测）。已强化为三元组，
>   负控把 `undo()` 改回去后红在「用例动了真实仓库的 backups/」那条断言。
>
> **生产代码相对 round-5 那次审查的 `685e5552` 零 diff** ——
> `git diff --stat 685e5552 HEAD -- scripts/ backend/app/ backend/openapi.json` 为空，
> 本轮唯一改动是 `backend/tests/regression/test_daily_review_run.py`（+54 −6）。
>
> **本轮请回答三件事**（其余分节仍请独立复核）：
> 1. 这个护栏本身是否可靠？白名单会不会把真实的越界也一起放行？
>    `mtime` 做判据在这台机器的文件系统上够不够（同秒内两次写会不会看不出来）？
>    还有没有别的 live 写面（vault 目录、outputs、learning_events 账本）没有被护栏覆盖？
> 2. 除了那两处 `undo()`，本卡的测试里还有没有别的路径可能写到真实仓库或 live vault？
>    （子进程走 `CANVAS_REPO`，父进程走 `_patch_runner`；`review_overview` 侧走
>    `board_done_env`，它自带一条 `probe.is_relative_to(root)` 的当场断言。）
> 3. round-5 留下的 2 MEDIUM + 1 LOW 本卡决定**登记不修**（轮次已到上限，且你判定它们是
>    测试判别力与报文措辞问题、生产行为正确）。这个处置是否合理？如果你认为其中哪一条
>    必须在本卡内修，请明说，并给出它在当前实现下的真实触发前提有多苛刻。

## 一 背景与最小读取面

树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime`
基线 `BASE = 709beb0bfa63348394f49f2b7fc6fa829c40b947`，审查对象 `HEAD = 756180ec7c4ea08637d3d2964ed5e2579be86d15`。

本卡收口一张前序卡（Y2-B / CARD-G6-7）留下的六条残留。系统是一个本地桌面学习应用：
一个 launchd 定时任务（runner，`scripts/daily_review_run.py`）每小时跑一次，扫节点、算出「今天先复习哪块白板」
并推送；一个本地后端网页（`review_overview.py` / `review_app.py`）显示同一份结果，并让用户点
「这板做完了」。两者**读写同一个 JSON 状态文件** `backups/daily-review.<vault_key>.state.json`。

请只读以下范围（按重要性排序）：

1. **全量改动**：`_bmad-output/审查/evidence-g67r/diff-BASE-to-756180ec7c4ea08637d3d2964ed5e2579be86d15.txt`
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
