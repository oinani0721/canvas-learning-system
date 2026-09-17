# 独立复核请求 — CARD-NEO4J-REPLAY-BOUND（T6-C，BATCH-2026-09-11-第十四批）

## ① 背景与最小读取面

仓库树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j`
（分支 `card/t6-neo4j`）。审查基准：`T6B_TIP=26bf4a2e26c0a7e1e80ba1cf599959f0e9564632`，
审 SHA = **`b8cd3a82`**（= 当前 HEAD；`47075cbe` 是 round-1 审过的前一版）。

Neo4j 离线降级时，后端把写不进图的记录暂存到几个 JSONL/JSON 文件。前一张卡（T6-B）已经把
回灌器接进真实路径，但这些暂存文件**写侧没有任何上限**：永久离线时它们单调增长直到占满磁盘。
本卡只做两件事：(1) 给 T6 地盘内的 3 个 JSONL 加写侧上限 + 轮转 + 保留上限；
(2) 修 `traces.py` 的 `DATA_DIR`/`LOGS_DIR` 指错目录，并新增一个**只读**的积压快照路由。

**最小读取面（只需读这些，不必通读全仓）**：

1. `git --no-pager diff 26bf4a2e b8cd3a82 -- . ':(exclude)_bmad-output'`（round-1→2 的增量单独看：`git --no-pager diff 47075cbe b8cd3a82`）
2. `backend/app/core/failure_counters.py` 全文（295 行）
3. `backend/app/core/failed_writes_constants.py` 全文（85 行）
4. `backend/app/services/memory_service.py` 的 `:495-530` 与 `:2855-2895` 两段
5. `backend/app/api/v1/endpoints/traces.py` 全文（354 行）
6. `backend/tests/unit/test_dead_letter_bounded_t6c.py` 全文（276 行）
7. `backend/tests/unit/test_traces_backlog_t6c.py` 全文（245 行）

参考（只读，本卡未改）：`backend/app/services/fallback_sync_service.py` 的
`_rotate_file` / `_cleanup_old_synced_files`（`:913-955`）—— 回灌侧既有的 `.synced.` 轮转。

## ② 作者自述（请独立核对，不要默认成立）

- **锁不重入**：`append_failed_writes_bounded` 与 `rotate_if_over_limit` **都不自取锁**。
  三个 failed_writes 写者（`memory_service:517` / `memory_service:2874` / `agent_service:131`）
  都在 `with failed_writes_lock:` 里调用；`write_dead_letter` 自己用另一把
  `_dead_letter_io_lock`，且它不调 `increment_*`（后者用 `_counter_lock`），故两把锁不嵌套。
- **后缀隔离**：写侧轮转后缀 `.overflow.`，与回灌侧 `.synced.` 相异；本卡 retention 只清
  `<stem>.overflow.` 前缀的兄弟。
- **保留上限删最老**：轮转名带定宽微秒时间戳，字典序 == 时序，`_prune_overflow` 保留末 N 个。
- **轮转目标唯一**：`_unique_overflow_target` 用微秒戳 + 存在性防撞，避免 `rename` 静默覆盖。
- **单批超限**：`append_failed_writes_bounded` 分批写（`_flush_pending_failed_writes` 可能一次
  交来比上限还多的条目，只在追加前核一次行数挡不住）。
- **backlog `oldest`** = 首条**可解析且带 `timestamp`** 的条目的 `timestamp`，不是文件 mtime；
  非 JSONL 链一律 `backlog/oldest/newest = null`。
- **新路由声明在动态段 `/traces/{request_id}` 之前**。
- **常量未进 `config.py`/`Settings`**，落在 T6 自有模块，env 可覆盖。
- **已知且故意的限制**（请判断作者是否如实且充分地记录了它们，而不是判断它们该不该存在）：
  被轮转走的 `.overflow.*` 条目**没有任何回灌方**，超保留上限后被删除；
  `agent_service:130` 第三写者不经 helper，纯它的突发可暂时越限。

## ③ 请按重要性排序回答的问题

0. **轮转原子性**：并发写者下会不会丢条目或重复轮转？进程内锁的覆盖面是否真的盖住了
   「核行数 → 轮转 → 追加」全段？跨进程的缺口作者是否如实声明？
1. **死锁面**：`threading.Lock` 是否存在二次获取路径？（含异常路径、helper 被别处复用的路径）
2. **DATA_DIR 改动的连带影响**：`/traces/{request_id}` 的其他源（`audit` / `bug_log`）
   在改后是否指向了正确位置？有没有因此读到本不该读的文件？
3. **backlog 对非 JSONL 与坏输入的稳健性**：坏 JSON / 空文件 / 权限不足 / 超大文件，
   端点是否仍返回 200；`_safe_backlog_entry` 的降级是否可能把真实缺陷盖成 200 假绿？
4. **env 覆盖的解析**：`bound_from_env` 对无效值 / 负数 / 超大值的处理是否有
   `ValueError` 逃逸或导入期崩溃面？`max_lines<=0` / `max_rotations==0` 的语义是否自洽？
5. **`agent_service` 旁路写者**使 failed_writes 有界不完备的风险面有多大，作者的表述是否过强？
6. **门的强度**：两个新测试里是否有**门未覆盖的路径**，或者某条断言其实恒真？
   特别是：`_prune_overflow` 的 `siblings[:-max_rotations]` 在 `max_rotations==0` 时的分支、
   `_display_path` 的 fallback 分支、`rotate_if_over_limit` 的三条 early-return。

## ④ 输出格式

`BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给 `file:line` + 一句话说明如何观察到该问题
（例如：哪个**对照输入**会让哪条断言翻转，或哪条**未被拦下的输入**会走到哪个分支）。
无问题的分级请显式写 `0`。

## ⑤ 边界

- **只读**。不要修改任何文件，不要连接数据库（7691/7687 都不要碰），不要跑会写现网
  `backend/data/**` 的命令。
- 不评 T6-B 的回灌正确性（`fallback_sync_service` / `main.py` 不在本卡改动面）。
- 不评其他地盘的写侧有界（`neo4j_client` / `episode_worker` / `canvas_service` /
  `agent_service` 本卡不改）。
- 不评 `backend/openapi.json`（本卡刻意不提交，由主 session 统一再生）。
- 不评 `ruff format` 的存量漂移（主干既有债，本卡已证新增 0 行）。

## ⑥ round-1 之后改了什么（请重点核这些是否引入了新问题）

round-1 给出 BLOCKER 0 / HIGH 0 / MEDIUM 3 / LOW 3；另有一轮内部对抗复核（多 agent，
独立于你）在 `47075cbe` 上报出一条阻断级。两边的意见都已收口，改动集中在：

1. **回灌窗口守卫**（`failed_writes_constants._replay_in_flight`）：写侧轮转让
   `failed_writes.jsonl` 在回灌窗口内变短，而 `fallback_sync_service._sync_failed_writes`
   的 finalize 用「长度比较 + 位置切片」（`:366-367`）判断重放期间有没有新追加，前提是
   文件只增不减。现在窗口开着就跳过轮转。`fallback_sync_service.py` 是本卡禁改面。
   **请独立判断这个守卫本身是否正确、是否有它盖不住的交错。**
2. `count_lines` 与 `overflow_siblings` 的失败不再阻断追加（round-1 M1）。
3. backlog 的每处降级留 `partial` + `degraded` 机器可读原因，顶层 `incomplete` /
   `degraded_chains`（round-1 M2）。
4. backlog 整段 I/O 走 `asyncio.to_thread` + `CLS_BACKLOG_SCAN_MAX_BYTES` 尺寸闸（round-1 M3）。
5. `_display_path` 捕获面放宽到 `Exception`，锚点从仓根改为 `_BACKEND_DIR`（round-1 L2 + 布局退化）。
6. 轮转名保留 `.jsonl` 结尾（否则 `backend/data/.gitignore` 盖不住），序号 `-NN` 恒存在
   （`-` < `.` 会打破 `_prune_overflow` 赖以「删最老」的字典序==时序不变量）。
7. backlog 补上 `event_bus.OUTBOX_FILE`。
8. 三处过强表述与 DATA_DIR 注释已收紧。
9. 两个测试文件从 23 条扩到 48 条。

**请特别核**：(a) 第 1 条守卫的正确性与它的失效模式（比如回灌挂住不放锁会怎样）；
(b) 第 6 条命名改动有没有破坏既有的 `.synced.` 清理或 backlog 的兄弟发现；
(c) 新增的 48 条门里有没有**恒真**断言或仍然**门未覆盖的路径**。
