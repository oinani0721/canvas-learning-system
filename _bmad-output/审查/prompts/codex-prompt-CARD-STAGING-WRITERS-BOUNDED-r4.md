# 对抗性代码复核 — CARD-STAGING-WRITERS-BOUNDED（BATCH-2026-09-18-第十五批 / P2-B）

## ① 背景与最小读取面（只读这些，不要全仓扫）

本仓是 Tauri + React + FastAPI 的桌面学习系统。本次改动的主题是「暂存 JSONL 的剩余无界写者收口」：
Neo4j 长时间不可用时，系统把失败的写入攒进几个本地 JSONL；上一张卡（T6-C）已经给其中 3 个文件加了
「核行数 → 轮转成 `.overflow.<ts>` → 按保留上限删最老」的有界追加，本卡收口**剩下的写者**。

审查绑定：`PREV = ac0993b4`，`审SHA = 732d2a96`（= 当前 HEAD）。

最小读取面（逐条，不要超出）：

1. `git --no-pager diff --no-color ac0993b4 732d2a96 -- . ':(exclude)_bmad-output'` —— 本卡全部代码改动
2. `backend/app/services/agent_service.py:102-147`（`_record_failed_write`）
3. `backend/app/core/failed_writes_constants.py:1-140`（模块头 + 常量 + `_replay_in_flight`）与 `:247-347`（`append_failed_writes_bounded`）
4. `backend/app/core/failure_counters.py:61-262`（`bound_from_env` / `count_lines` / `overflow_siblings` / `_unique_overflow_target` / `_prune_overflow` / `rotate_if_over_limit`）
5. `backend/app/services/fallback_sync_service.py:83-186`（模块级 `_sync_all_lock` / `_sync_all_started_at`、`sync_all_fallbacks`、`_sync_all_fallbacks_locked`）
   与 `:294-448`（`_sync_failed_writes`；其中 `:386` 是 finalize 的「只增不减」判据 `if len(current_lines) > len(lines):`，供审「超时后的误判面是否如实登记」）
6. `backend/app/services/memory_service.py:1380-1478`（`record_batch_learning_events` 的 Neo4j 失败分支与本卡新增的即时刷盘）与 `:2840-2900`（`cleanup` / `_flush_pending_failed_writes`）
7. `backend/app/services/episode_worker.py:201-303`（`DeadLetterStore`）
8. `backend/app/services/event_bus.py:40-70`（模块级 outbox 常量与锁）与 `:357-438`（`_write_outbox` / `recover_outbox`）
9. `backend/tests/unit/test_staging_writers_bounded.py` 全文（620 行，本卡新门）
10. `backend/tests/unit/test_dead_letter_bounded_t6c.py:212-241`（既有 fixture 口径）、`:474-499`（既有**真锁**门）、`:898-930`（既有文件本地 AST 常驻门）
11. 裁定书 `_bmad-output/审查/2026-09-15-第十四批复核裁定与待裁决登记.md` §二 的 T6-C 行（`:158`）与 §三.3（`:186`）
12. T6-C 验收单 `_bmad-output/验收单/UAT-CARD-NEO4J-REPLAY-BOUND-2026-09-15.md` 的「台账待登记条目」段（`:217` 起）

## ② 作者自述 —— 请独立核对，不要采信

1. **第三写者切了有界 helper，且仍读 `agent_service` 模块级路径**：`_record_failed_write` 原先在
   `with failed_writes_lock:` 里裸 `open(FAILED_WRITES_FILE, "a")`，现改调
   `append_failed_writes_bounded(FAILED_WRITES_FILE, [...])`。路径**故意**继续用 `agent_service` 自己的
   模块级绑定副本（不是 `failed_writes_constants` 的全局），因为既有 12 处测试打桩的是前者。
2. **回灌窗口守卫的超时是三态**：未 locked → False；locked 但 `_sync_all_started_at is None`
   （直接持锁者，例如既有真锁门 `test_no_rotation_while_replay_window_open`）→ True；
   locked 且已超 `REPLAY_WINDOW_MAX_SECONDS`（默认 1800，`CLS_REPLAY_WINDOW_MAX_SECONDS` 可调）→
   `logger.error` + False。时间戳由 `sync_all_fallbacks` 在**取到锁之后**打、`finally` 清。
3. **即时刷盘没有在 append 与 clear 之间引入 await**：`_flush_pending_failed_writes` 是同步方法，
   新调用点紧跟 `for i, err in enumerate(neo4j_errors):` 循环之后，`cleanup()` 里那次保留为第二道防线。
4. **两条新有界链复用同一个原语，回灌侧零改动**：`DeadLetterStore.store` 与 `EventBus._write_outbox`
   都走 `failure_counters.rotate_if_over_limit`，各自带一把只护「核行数 → 轮转 → 追加」的锁；
   `event_bus.recover_outbox` 与 `fallback_sync_service` 的回灌算法一行未动。
5. **3 处 `Path.exists` 改 stat/iterdir 分流，回灌侧 9 处未动**：`failure_counters.overflow_siblings`、
   `failure_counters._unique_overflow_target`、`episode_worker.DeadLetterStore.count`。
   `fallback_sync_service` 的 9 处 `.exists()` 与 `event_bus.recover_outbox` 的 1 处按卡文属下一张卡的面，未动。

## ③ 请回答的问题（按重要性排序）

- **⓪** 超时到期后守卫放行轮转：若回灌**确实**还在跑（只是慢，不是挂住），
  `fallback_sync_service._sync_failed_writes` 在 `:386` 的「只增不减」finalize 判据仍会误判窗口内新写的条目。
  本卡是否**如实**把它登记为下一张卡（REPLAY-REWRITE）的前置，而不是声称已经解决？
  作者自述见 `failed_writes_constants._replay_in_flight` 的 docstring 与本卡验收单「本卡未证明什么」①。
  请指出任何**声称过强**之处。
- **①** 即时刷盘放在 `record_batch_learning_events` 内：是否引入了阻塞事件循环的同步 IO 新面？
  是否改变了该方法 `errors` / `failed` / `episode_ids` 的返回语义？异常路径下会不会重复落盘或漏落盘？
- **②** `DeadLetterStore.store` 取的 `failure_counters._dead_letter_io_lock` 与
  `EventBus._write_outbox` 取的 `_outbox_io_lock`：在各自调用链上是否与既有的锁形成反序嵌套？
  （特别是 `failed_writes_lock` → `_dead_letter_io_lock` 是否存在两个方向的取锁顺序。）
- **③** 三条 `exists` 门是否真测到了「吞异常」那条路径？注入点是 `os.stat` / `os.scandir` 而不是
  `type(path).stat`，理由写在测试文件的注释里（Python 3.14 的 `Path.exists()` 走
  `os.path.exists` → `os.stat`，`genericpath.exists` 的 `except OSError` 才是吞异常的地方）。
  请核对：改动前的代码是否**确实**会在该注入下给出错误答案；有没有**门未覆盖的路径**。
- **④** 新增的两族 env 上限常量（`CLS_REPLAY_WINDOW_MAX_SECONDS`、`CLS_OUTBOX_MAX_LINES/ROTATIONS`）
  是否都经 `bound_from_env` 而不是裸 `int()`？坏值是否会在模块导入期让进程起不来？
- **⑤** `pyright app` 报 0 errors 是不是靠 `# pyright: ignore` 掩盖的？本卡新增了几条 ignore？

## ④ 输出格式

逐条给：

```
[BLOCKER|HIGH|MEDIUM|LOW] <file>:<line> — <一句话结论>
  复现思路：<一句，用下列措辞>
```

措辞请用：**负控输入**（把某处改回旧写法后哪条门会红）、**对照输入**（同族里必须仍绿的那条）、
**未被拦下的输入**（某个取值/顺序/时序没有被现有判据挡住）、**门未覆盖的路径**（代码里没有任何门经过的分支）。

## ⑤ 边界

- **只读**。不要修改任何文件，不要提出需要运行服务或连接数据库的验证步骤。
- 本卡零连库：不要评估任何 Neo4j / LanceDB 连接面。
- **不在本卡范围，请不要作为发现提出**：回灌算法本身（`fallback_sync_service` `:294` 起的重放与 finalize 实现）、
  `.overflow.*` 代际的扫回策略、outbox 的幂等 ID 与 vault 命名空间 —— 这三项分别归后续两张卡。
  若你认为本卡的改动**让这三项变得更糟**，那属于本卡范围，请明确说出因果链。
- `DEAD_LETTER_STORE_FULL_BODY` 的默认值、`backend/data/` 下真实文件的保留期，本卡按用户裁定不得改动。


## ⑥ round-4：r3 之后改了什么（请重点复核这一段）

r3 给出 BLOCKER 0 / HIGH 2 / MEDIUM 3 / LOW 0。此外车道另跑了一轮**五视角对抗自审**
（正确性 / 并发与锁 / 门的有效性 / 契约与调用方 / 文档诚实性，每条发现再派一个以反驳为默认
立场的验伪 agent），26 条发现里 16 条存活。两边合并后的处置如下：

1. **r3 HIGH（`ensure_line_boundary` 返回值被忽略）+ 自审 MEDIUM（同一处的反面）** → **重新设计**。
   r3 之后我先加了「返回 False 就不写、留待重试」，自审随即证明那是**新的回归**：
   活动文件**可写但不可读**（`chmod 0222` / ACL / EIO）时探测恒失败，于是
   `_flush_pending_failed_writes` **永远**刷不出去、`_pending_failed_writes` 无界增长、
   连 `cleanup()` 也再写不掉 —— 而**改动前**同样的批次是能落盘的（下层
   `rotate_if_over_limit` 与 room 计算都刻意吞掉那次读失败，注释写着「宁可暂时越限，也不丢死信」）。
   现在的设计是：
   - `ensure_line_boundary` 返回 **False 只代表「已确认有半行、且补换行失败」**；
     **探测本身失败返回 True**（「不知道」≠「知道有半行」，退回改动前的行为）。
   - `append_failed_writes_bounded` 入口拿这个布尔值决定 `sep`：False 时把分隔符
     **并进本次写入的第一行**（一次 open 写完），而不是拒写 —— 那两个写者没有重试缓冲，拒写 = 直接丢。
   - `_flush_pending_failed_writes` **不再**自己检查返回值后拒写。
   新增门：`test_flush_does_not_glue_when_boundary_repair_fails`、
   `test_flush_still_writes_when_boundary_probe_is_unreadable`；负控段 7b/9 分别恢复拒写分支、
   删 sep 机制，各红在指定断言。
   请核：这个三态划分是否还有未覆盖的组合；`sep` 只加在第一行是否对 `_replay_in_flight` 那条
   「只追加不轮转」分支同样成立。

2. **自审 HIGH（既有常驻门被我的 import 改名架空）** → **已改回**。
   我曾把 `_replay_in_flight` 的 import 从 `from app.services.fallback_sync_service import _sync_all_lock`
   改成 `from app.services import fallback_sync_service as _fss`；而 t6c 的两条常驻门是靠
   `builtins.__import__` 拦 `name == "app.services.fallback_sync_service"` 来模拟「观测不到回灌状态」的，
   改名后 `name` 变成 `"app.services"`，拦不住了 —— 那两条门照样绿，但绿在「锁本来就没被占」这条
   完全不同的判据上。现已改回点分形式，并新增一条**在真持锁前提下**验「观测不到 ⇒ False」的门
   `test_unobservable_replay_state_is_false_even_while_locked`（负控段 10 把 import 改回去即红）。

3. **自审 HIGH（时间戳门只验 `isinstance(float)`）** → 已加强：同时断言
   ①打戳时 `_sync_all_lock.locked()` 为真（戳打在取锁之后）②戳与当下 `time.monotonic()`
   相差 < 5 秒（**同一口时钟**；换成 `time.time()` 会差数十年 ⇒ 守卫恒判超时）③退出后清空。

4. **自审 HIGH（窗口内「只追加不轮转」分支从没被喂过多行批次）** → 新增
   `test_replay_window_open_keeps_whole_multiline_batch_unrotated`：窗口开着时一次交来
   `MAX_LINES+3` 条，断言不轮转且按身份一条不丢。

5. **自审 LOW（超时的 `logger.error` 零覆盖）** → 新增
   `test_replay_guard_logs_error_when_window_times_out`（caplog 断言 `[C2-01]`）。

6. **自审 doc-honesty 五条** → 逐条改：
   - `_replay_in_flight` docstring 里 `fallback_sync_service.py:NNN` 行号被本卡自己插入的 26 行整体顶掉
     ⇒ 全部改成**按符号名**指位；
   - `_sync_all_started_at` 注释里「`None` 的含义①：没人持锁」是错的（没人持锁时守卫更早就
     `return False` 了，根本读不到该变量）⇒ 已更正；
   - 两处仍说 `_flush_pending_failed_writes` 有 `finally: clear()`（本卡已删）⇒ 已更正；
   - `DeadLetterStore.count()` docstring 称旧实现会在 U+2028/U+2029 上漂 ⇒ 失实（旧实现是文本模式
     逐行迭代，只按 `\n` 切）⇒ 已更正，并如实登记新实现「每写一条先全文件扫一遍」的代价；
   - `agent_service` 注释「等 5 处」数错 ⇒ 实测既有打桩 **12 处 / 4 个既有文件**，已更正（`grep -c` 自证）。

7. **r3 HIGH（超时放行轮转破坏健康慢回灌）+ 自审 HIGH（游标复活）** → **仍未修，车道不自判通过**。
   前者理由同 r3（卡文 §一(d) 规定该分支返回 False，改它属改变卡的决定）。
   后者是自审新发现的**另一条因果链**，一并登记：轮转发生后，仍在跑的重放循环会在下一个
   checkpoint 间隔重新 `_save_checkpoint`，把属于**上一代文件**的下标重新绑到新一代活动文件上；
   若进程在 finalize 的 `_clear_checkpoint` 之前退出，重启后整份新一代 `failed_writes.jsonl`
   会被 `if i < checkpoint_idx: continue` 全部跳过，还因 still_pending 为空而被改名成 `.synced.`。
   写侧挡不住（游标是回灌侧自己写回的），修法在下一张卡。两条都已写进
   `_replay_in_flight` 的 docstring 与验收单。
   请核：**这两段登记是否仍有声称过强之处**。

8. **自审 LOW（无并发门）/ LOW（`DeadLetterStore.store` 每写一条全文件扫描）** → 如实登记，未加门 / 未优化。

其它：验收单已整体重写（r3 MEDIUM 指出它落后）；负控现为**十段**，全部在当前 HEAD 重跑，
每段 `before=` / `restored=` sha256 逐段相同。新门 **23 条**（AST 计数与 `passed` 数相等）。
