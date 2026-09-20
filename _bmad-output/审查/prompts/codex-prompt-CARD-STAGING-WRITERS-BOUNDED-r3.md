# 对抗性代码复核 — CARD-STAGING-WRITERS-BOUNDED（BATCH-2026-09-18-第十五批 / P2-B）

## ① 背景与最小读取面（只读这些，不要全仓扫）

本仓是 Tauri + React + FastAPI 的桌面学习系统。本次改动的主题是「暂存 JSONL 的剩余无界写者收口」：
Neo4j 长时间不可用时，系统把失败的写入攒进几个本地 JSONL；上一张卡（T6-C）已经给其中 3 个文件加了
「核行数 → 轮转成 `.overflow.<ts>` → 按保留上限删最老」的有界追加，本卡收口**剩下的写者**。

审查绑定：`PREV = ac0993b4`，`审SHA = 5bb52629`（= 当前 HEAD）。

最小读取面（逐条，不要超出）：

1. `git --no-pager diff --no-color ac0993b4 5bb52629 -- . ':(exclude)_bmad-output'` —— 本卡全部代码改动
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


## ⑥ round-3：r2 之后改了什么（请重点复核这一段）

r2 给出 BLOCKER 0 / HIGH 2 / MEDIUM 3 / LOW 0。逐条处置：

1. **r2 HIGH `memory_service.py:2927`（半行写入失败后重试会被粘连吞掉）** → **已修**。
   新增 `failed_writes_constants.ensure_line_boundary(path)`：活动文件若以非换行字节结尾，
   先补一个换行再让调用方追加；探测失败（权限 / EIO）只告警、不阻断追加。
   `_flush_pending_failed_writes` 在持 `failed_writes_lock` 后、调
   `append_failed_writes_bounded` 前调用它。
   新增门 `test_flush_repairs_dangling_tail_before_retry`：写入残缺尾巴，刷盘后断言
   ①残缺尾巴**自成一行** ②重试记录是一条可解析的行。
   负控段⑤（删掉该调用）实测红在「残缺尾巴没有自成一行」，失败正文即粘连串。
   请核：补换行本身会不会在别的路径上造成空行 / 行数口径漂移；
   `ensure_line_boundary` 的失败分支是否仍然安全；以及 `agent_service._record_failed_write`
   与 `_record_structured_outbox` 这两个**未**调用它的写者是不是应该一并接上
   （作者的判断：它们不重试，粘连只会来自别的写者留下的半行，属既有面，本卡未扩大）。

2. **r2 MEDIUM（混合批次里一条坏条目会让整批被丢）** → **已修**：序列化改成逐条
   try/except，只丢坏的那条，其余照常落盘；OSError 分支保留整批（含坏条目）重试。
   新增门 `test_flush_keeps_good_entries_when_one_is_unserializable` + 负控段⑥。

3. **r2 HIGH `failed_writes_constants.py:145`（超时放行轮转仍会破坏正在进行的回灌）**
   → **仍未修，车道不自判通过，理由如下请一并复核**：
   卡文 §一(d) 明确规定超时分支「logger.error(...) 并**返回 False**（允许轮转）」，
   这是卡的既定规格；r2 建议的「超时后仍返回 True」与该规格相反，等于把本卡的
   主修目标（写侧上限不再无限期关闭）整段撤回 —— 这属于**改变卡的决定**，
   按协议要由主 session / 用户裁定，不是车道能自判的。
   作者已按 r2 的措辞把它写成「本卡引入的安全退化」并移交下一张卡，
   同时把 r2 提出的这条替代方案原样登记进验收单，供裁定时直接采用。
   请核：**登记是否仍有声称过强之处**，以及这个「不自判通过、交裁定」的处置本身是否得当。

4. **r2 MEDIUM（「至多失效 N 秒」没清干净；竞态安全声明不适用超时分支）**
   → 两处都已改：`_replay_in_flight` docstring 的竞态那条现在明写「**非超时**分支下……
   超时分支不适用这条」；`append_failed_writes_bounded` docstring 限定 1 改成
   「越限**仍可无限持续**」并逐条列出三条没有时间上限的路径。
   验收单里 r2 指出的那两处也已改写（r2 当时读到的是尚未提交的旧稿）。

5. **r2 MEDIUM（AST 门漏嵌套 TestOuter.TestInner；「空 git status 是兜底」失实）**
   → 扫描改成**递归**进嵌套 `Test*` 类，验伪锚补了一段嵌套类违规；
   docstring 已更正为「`backend/data/.gitignore` 的 `*.jsonl` 让普通 status 看不见这些写入，
   真正能看见的兜底是对 `backend/data/` 做跑前/跑后 sha256 快照」，该快照已作为裁判落档。

6. **r2 MEDIUM（请求期同步 IO / 同步等锁）** → 未做异步化，只在 docstring 与验收单登记。

另：r2 提到「验收单存在未提交改稿」——本轮所有 `_bmad-output` 内容均已随 `5bb52629` 提交。
