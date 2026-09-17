# 独立复核请求 — CARD-NEO4J-REPLAY-BOUND（T6-C，BATCH-2026-09-11-第十四批）

## ① 背景与最小读取面

仓库树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j`
（分支 `card/t6-neo4j`）。审查基准：`T6B_TIP=26bf4a2e26c0a7e1e80ba1cf599959f0e9564632`，
审 SHA = **`09d6da33`**（= 当前 HEAD；r1 `47075cbe` / r2 `b8cd3a82` / r3 `11caca05`）。

Neo4j 离线降级时，后端把写不进图的记录暂存到几个 JSONL/JSON 文件。前一张卡（T6-B）已经把
回灌器接进真实路径，但这些暂存文件**写侧没有任何上限**：永久离线时它们单调增长直到占满磁盘。
本卡只做两件事：(1) 给 T6 地盘内的 3 个 JSONL 加写侧上限 + 轮转 + 保留上限；
(2) 修 `traces.py` 的 `DATA_DIR`/`LOGS_DIR` 指错目录，并新增一个**只读**的积压快照路由。

**最小读取面（只需读这些，不必通读全仓）**：

1. `git --no-pager diff 26bf4a2e 09d6da33 -- . ':(exclude)_bmad-output'`（round-3→4 的增量单独看：`git --no-pager diff 11caca05 09d6da33`）
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

## ⑥ round-3 之后改了什么（请重点核这些）

round-3 给出 BLOCKER 0 / HIGH 2 / MEDIUM 1 / LOW 4，全部已收口：

1. **HIGH-1 编码异常致整批丢失**：`_invalidate_replay_checkpoint` 的捕获面漏了
   `UnicodeDecodeError` / `UnicodeEncodeError`（二者是 `ValueError` 子类，**既不是**
   `OSError` **也不是** `JSONDecodeError`）。现在：读侧加 `UnicodeDecodeError`（坏文件整删）；
   写侧 `ensure_ascii=False` → 失败退回 `ensure_ascii=True`（保住其余链的游标）→ 再失败才整删；
   外层兜底改 `except Exception`（本函数在追加路径上，绝不能抛）。
2. **HIGH-2 现网文件隔离**：两个 fixture 补上 `fss.SYNC_CHECKPOINT_FILE` 隔离，
   并加一条直接盯指针的硬边界门。
3. **MEDIUM 扫描边界**：改为二进制一次 `read(max_bytes + 1)`，内存上界就是 `max_bytes`；
   切行用 `split("\n")` 不用 `splitlines()`。
4. **LOW-4 / LOW-5 / LOW-6**：根锚门改用 `/` + `/secret.jsonl`；更正 docstring 里
   「import 失败退回有界行为」这句失真表述（净效果是**永不轮转**）；批量 flush 守恒门补身份断言。
5. 门 60 → 66。

⚠️ **作者自曝：round-3 的三条门初版全是空壳**（H1a/H1b/H2 的负控**都没红**）。
原因分别是：断言「不丢批」而外层兜底让修与不修都成立；内外两层互相掩盖；
现网文件恰好不存在所以打不打桩都一样。判据已改为盯「只有该层能产生的可观测差异」，
负控⑥复跑六段全红。

**请核**：(a) HIGH-1 的新捕获面有没有仍然能逃出去的异常类型，以及
`ensure_ascii=True` 退路本身的失效面；(b) 二进制读那段的截断处理（尾部半行、
多字节字符被切断、`split("\n")` 与 `count_lines` 的口径是否仍一致）；
(c) 新增/重做的 66 条门里还有没有同型的「断言写错了对象」或**门未覆盖的路径**。
