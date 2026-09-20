# 对抗性代码复核 — CARD-STAGING-WRITERS-BOUNDED（BATCH-2026-09-18-第十五批 / P2-B）

## ① 背景与最小读取面（只读这些，不要全仓扫）

本仓是 Tauri + React + FastAPI 的桌面学习系统。本次改动的主题是「暂存 JSONL 的剩余无界写者收口」：
Neo4j 长时间不可用时，系统把失败的写入攒进几个本地 JSONL；上一张卡（T6-C）已经给其中 3 个文件加了
「核行数 → 轮转成 `.overflow.<ts>` → 按保留上限删最老」的有界追加，本卡收口**剩下的写者**。

审查绑定：`PREV = ac0993b4`，`审SHA = 80295391`（= 当前 HEAD）。

最小读取面（逐条，不要超出）：

1. `git --no-pager diff --no-color ac0993b4 80295391 -- . ':(exclude)_bmad-output'` —— 本卡全部代码改动
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


## ⑥ round-5（末轮）：r4 之后改了什么

r4 给出 BLOCKER 0 / HIGH 2 / MEDIUM 3 / LOW 1。逐条处置：

1. **r4 MEDIUM（「探测失败 + 实际半行 + 追加成功」仍粘连）** → **已修**。
   `ensure_line_boundary` 的返回值语义再收窄一次，现在是「**知不知道**」而不是「要不要写」：
   - `True` = **已知**落在行边界上（不存在 / 空 / 以换行结尾 / 刚补上）；
   - `False` = **不能确定**（已确认有半行但补不上 **或** 探测本身失败）。
   调用方据此只决定**加不加分隔符**，**绝不据此拒写**。代价是探测失败时多写一个空行
   （读侧按行解析时跳过），换来的是**任何情况下都不粘连**。
   新增门 `test_no_glue_when_probe_fails_on_a_dangling_tail`（负控段 11 把探测失败改回
   `return True` 即红，失败正文就是粘连串）。
   r4 指出「该缺陷 PREV 也存在，应称修复遗漏而非新增回归」—— 已按此措辞登记。

2. **r4 LOW（补换行失败后若成功轮转，遗留 sep 会往新空文件多写一行）** → **已修**：
   `rotate_if_over_limit` 返回 True（真轮转过）时把 `sep` 清空。
   新增门 `test_sep_is_dropped_after_a_real_rotation`（负控段 12 删掉这行即红，
   失败正文 `首段 2 行 > 上限 1`）。

3. **r4 MEDIUM（时间戳门证不了「赋值在取锁之后」）** → **已修**：新增
   `test_started_at_is_not_stamped_while_waiting_for_the_lock` —— 先由测试占住锁，
   再启动 `sync_all_fallbacks`，断言**等锁期间时间戳一动不动**（哨兵值不变），
   放锁后才被打上、退出后清空。这正是 r4 给的对照输入。

4. **r4 更正我的注释方向**（`time.time()` 会让 elapsed 变成巨大**负数** ⇒ **恒不超时**，
   而不是「恒判超时」）→ 已改；断言本身不变。

5. **r4 MEDIUM（验收单 4-B 承诺过强 + 提交内登记落后）** → 验收单已整体更新并随本 commit 提交：
   4-B 去掉「三样都拦住」「强退不会整批不见」这类绝对化说法，改成有条件的表述；
   §四 / §五 补入游标复活、无并发门、`count()` 全文件扫描等条目。

6. **r4 两条 HIGH（超时放行轮转 → finalize 覆盖 / 游标复活）** → **仍未修，车道不自判通过**。
   理由同前几轮：卡文 §一(d) 明确规定超时分支返回 False（允许轮转），改它属**改变卡的决定**，
   按协议交主 session / 用户裁定。两条都已写进 `_replay_in_flight` 的 docstring 与验收单，
   并按 r4 的要求补了限定（「重新保存 checkpoint 不是必然的，还要满足连续成功前缀推进」；
   「新代行数 ≤ 复活游标时才是整份跳过」）。
   请核：**这两段登记是否还有声称过强之处**。

7. **r4 指出「两条新有界链」自述过时** → 已改（e3 撤回后只剩一条新有界链）。

其它：负控现为**十二段**，全部在当前 HEAD 重跑，每段 `before=` / `restored=` 逐段相同，
跑完 7 个源文件均与 HEAD 逐字节一致；新门 **26 条**（AST 计数 = `passed` 数）。
