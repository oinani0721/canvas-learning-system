# ZCode 补审 prompt — CARD-STAGING-WRITERS-BOUNDED（r6 · GLM-5.3 · 协议 §2.4.2）

> 批次 `BATCH-2026-09-18-第十五批` · 车道 `card-p2-outbox` · 卡 `CARD-STAGING-WRITERS-BOUNDED`（暂存 JSONL 写侧有界化）
> 补审通道（协议 §2.4.2）：GLM-5.3 × ZCode CLI · `--mode build`（只读：Bash / Write 被阻断，Read 可用）
> 轮次：r6（补审通道；接 Codex r1–r5 与 r5 两次 0 字节失败档）
> 审查绑定：`d2ebf694`（= 本卡末次改动 commit = 当前 HEAD；`git --no-pager diff --stat --no-color d2ebf694 HEAD -- <7 文件>` = 空）
> 送审时间：2026-09-19 · 生成：车道 card-p2-outbox（自动生成，供只读评审）

（本文件为自包含送审包：五节指令 + 末尾内嵌完整变更集。你的运行环境对 Bash / Write 有阻断 —— 一切 git 输出以附录 A 为准，不需要、也不要尝试运行 git。）

---

## ① 背景 + 最小读取面（写死）

**卡要解决的问题**：Neo4j 长时间不可用时，系统把失败的写入攒进几个本地 JSONL；上一张卡（T6-C）已给其中 3 个文件加了「核行数 → 轮转成 `.overflow.<ts>` → 按保留上限删最老」的有界追加，本卡收口**剩下的写者**（暂存 JSONL 写侧有界化）：

1. **第三写者收口**：`agent_service._record_failed_write`（`failed_writes.jsonl`）从 `with failed_writes_lock:` 内裸 `open(..., "a")` 改为调 `append_failed_writes_bounded(...)`；路径**故意**继续读 `agent_service` 模块级 `FAILED_WRITES_FILE`（既有 5 处测试打桩的正是这一侧；改读全局常量会让那些测试静默写进现网文件）。
2. **回灌窗口守卫加超时**：`failed_writes_constants._replay_in_flight` 从「只看锁着没」加时间维度；`fallback_sync_service` 新增模块级 `_sync_all_started_at`，`sync_all_fallbacks` 持锁期间打戳、`finally` 清空；新 env `CLS_REPLAY_WINDOW_MAX_SECONDS`（默认 1800）。
3. **批次失败即时落盘**：`memory_service._pending_failed_writes` 从「仅 `cleanup()` 刷盘」改为「`record_batch_learning_events` 失败分支即时刷盘 + `cleanup()` 兜底」。
4. **`dead_letter_episodes.jsonl` 写侧有界**：`episode_worker.DeadLetterStore.store` 复用 `failure_counters` 的轮转原语（`_dead_letter_io_lock` + `rotate_if_over_limit`）。**e3（`outbox/events.jsonl` 有界）按卡文「可退子项」整段退回第十六批**（r1-HIGH-3：轮转与 `recover_outbox` 的读-改-写窗口互撞，修它要动下一张卡的地盘）⇒ `event_bus.py` 逐字节同 PREV、不在变更集内。
5. **`Path.exists` 吞异常残余 3 处**改为 `stat` / `iterdir` 显式分流（Python 3.14 的 `Path.exists()` 走 `os.path.exists` → `os.stat`，`PermissionError` 被 `genericpath.exists` 吞掉）。
6. **末段整改（r2–r5 轮的发现，全部带负控）**：新增 `ensure_line_boundary`（防「半行尾巴吞掉下一条记录」）；`_flush_pending_failed_writes` 失败语义分流（磁盘故障保留重试 / 序列化与编码失败逐条丢弃）；「真轮转后清 `sep`」；等。

**终态改动（= 本 prompt 附录 A 的变更集）**：7 文件，+1478/−55 行；新门文件 `backend/tests/unit/test_staging_writers_bounded.py`（1072 行，26 条）。

**最小读取面（写死；只读，不修改）**：

- （A）**内嵌变更集**：附录 A = `git --no-pager diff --no-color ac0993b4 d2ebf694 -- backend/app/core/failed_writes_constants.py backend/app/core/failure_counters.py backend/app/services/agent_service.py backend/app/services/episode_worker.py backend/app/services/fallback_sync_service.py backend/app/services/memory_service.py backend/tests/unit/test_staging_writers_bounded.py` 全文（1,759 行，未经删改）。
- （B）树内文件（用 Read；路径相对 cwd；行号为送审时实测，若漂移以符号名为准）：
  1. `backend/app/core/failed_writes_constants.py` 全文件（473 行；重点：常量 :33-43、`_replay_in_flight` :46-189、`ensure_line_boundary` :296-351、`append_failed_writes_bounded` :354-473）
  2. `backend/app/core/failure_counters.py`（`bound_from_env` :51-69、`count_lines` :92-115、`overflow_siblings` :118-135、`_unique_overflow_target` :138-181、`_prune_overflow` :184-205、`rotate_if_over_limit` :208-262）
  3. `backend/app/services/agent_service.py:102-149`（`_record_failed_write` 全函数）
  4. `backend/app/services/fallback_sync_service.py:100-150`（`_sync_all_started_at` :105、`sync_all_fallbacks` :114-140、`_sync_all_fallbacks_locked` :142-194 —— 后者本卡**一行未改**）与 `:300-460`（`_sync_failed_writes` :302-456；finalize 的「只增不减」判据 `len(current_lines) > len(lines)` :394，供审「超时后的误判面是否如实登记」）
  5. `backend/app/services/memory_service.py:1286-1478`（`record_batch_learning_events`；失败分支与即时刷盘 :1423-1437）与 `:2840-2953`（`cleanup` :2840-2861 / `_flush_pending_failed_writes` :2863-2953）
  6. `backend/app/services/episode_worker.py:201-312`（`DeadLetterStore`：`store` :239、`count` :288）
  7. `backend/tests/unit/test_staging_writers_bounded.py` 全文（26 条门）
  8. `backend/tests/unit/test_dead_letter_bounded_t6c.py`（既有门范式，按符号名检索：fixture `bounded_failed_writes` :212 起、真锁门 `test_no_rotation_while_replay_window_open` :474 与对照 :495、`test_count_lines_does_not_swallow_permission_error` :669、文件本地 AST 常驻门 :898）
  9. 判定上下文（只读引用）：裁定书 `_bmad-output/审查/2026-09-15-第十四批复核裁定与待裁决登记.md` §二 T6-C 行与 §三.3（⚠️ 卡文引 `:158/:186`，但该文件在本 checkout 实为 111 行、行号不成立——系卡文引用未随文件更新，**不要作为发现上报**）；T6-C 验收单 `_bmad-output/验收单/UAT-CARD-NEO4J-REPLAY-BOUND-2026-09-15.md`「台账待登记条目」段（:217 起）。
- 不要求读其它 `_bmad-output/` 文档或路径。
- ⛔ 本通道 `--mode build` 已阻断 Bash / Write：不要运行任何命令；git 输出已全部内嵌；读文件 + 内嵌文本足以完成本轮审查。

## ② 作者自述（请独立核对，勿直接采信）

逐条给出：成立 / 不成立（附 file:line）/ 范围过宽（说明差在哪）。

1. **第三写者已切 helper，且仍读 `agent_service` 模块级路径**（理由：5 处既有测试打桩 `app.services.agent_service.FAILED_WRITES_FILE`）。
2. **守卫超时是三态**：未 locked → False；locked 且 `_sync_all_started_at is None`（直接持锁者，例如既有真锁门 :474）→ **True（保持原语义、不受超时约束）**；locked 且 `time.monotonic() - started_at > REPLAY_WINDOW_MAX_SECONDS` → `logger.error` + **False**（允许轮转）。时间戳由 `sync_all_fallbacks` 在**取到锁之后**打、`finally` 清。
3. **即时刷盘没有在 append 与 clear 之间引入 `await`**：`_flush_pending_failed_writes` 是同步方法，新调用点紧跟 Neo4j 失败循环之后，`cleanup()` 里那次保留为第二道防线。
4. ⚠️ **终态更正（必须核实）**：e3（outbox 有界）**整段退回**（见 ①.4），落地的新有界链**只有 `dead_letter_episodes.jsonl` 一条**（复用锁 + 轮转原语，上限调用时读模块属性以便 monkeypatch）；回灌侧零改动。可核证据：`event_bus.py` 不在变更集内。
5. **3 处 `Path.exists` 改 `stat`/`iterdir` 分流**（`failure_counters.py` ×2、`episode_worker.py` ×1），回灌侧 `fallback_sync_service` 9 处与 `event_bus.recover_outbox` 1 处**未动**（按卡文属下一张卡）。
6. ⚠️ **末段整改（r2–r5，必须核实）**：`ensure_line_boundary` 的返回值语义 = 「**知不知道**落在行边界」（True=已知在边界 / 刚补上；False=不能确定），调用方只据此决定**加不加分隔符**、绝不据此拒写；`_flush_pending_failed_writes` 失败语义 = OSError 保留重试 / `TypeError`·`ValueError` 逐条丢弃 / 成功只删本批；「真轮转后清 `sep`」。三者各有专属负控段（⑪ ⑫ 等）。

## ③ 按重要性排序的问题（逐项给结论）

- **⓪** 超时到期后守卫放行轮转：若回灌**确实**还在跑（只是慢，不是挂住），`_sync_failed_writes` 的 finalize「只增不减」判据（:394）仍会误判窗口内新写的条目。本卡是否**如实**把它登记为下一张卡（P2-C REPLAY-REWRITE）的前置，而不是声称已经解决？请指出任何**声称过强**之处。
- **①** 即时刷盘放在 `record_batch_learning_events` 内：是否引入了阻塞事件循环的同步 IO 新面？是否改变了该方法 `errors` / `failed` / `episode_ids` 的返回语义？异常路径下会不会重复落盘或漏落盘？
- **②** `DeadLetterStore.store` 取的 `_dead_letter_io_lock` 是否与既有锁形成反序嵌套？（特别是 `failed_writes_lock` → `_dead_letter_io_lock` 是否存在两个方向的取锁顺序。e3 已退，`_write_outbox` 不在本卡改动面。）
- **③** 三条 `exists` 门是否真测到「吞异常」那条路径？注入点是 `os.stat` / `os.scandir`（**卡文原稿给的是 `type(path).stat`，经实测无效已更正** —— 见变更集里测试文件注释与验收单登记）。请核对：注入是否命中被测那次调用；有没有**门未覆盖的路径**。
- **④** 新增的 env 上限常量（`CLS_REPLAY_WINDOW_MAX_SECONDS` 等）是否都经 `bound_from_env` 而不是裸 `int()`？坏值是否会在模块导入期让进程起不来？
- **⑤** `pyright app` 报 0 errors 是不是靠 `# pyright: ignore` 掩盖的？本卡新增了几条 ignore？
- **⑥** 若发现其它真问题，按 §④ 格式照报。

## ④ 输出格式

- 发现清单，每条：`[BLOCKER|HIGH|MEDIUM|LOW] <file>:<line> — <一句话说明>；<一句复现思路>`；
- 复现思路的措辞必须用：**负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径**（不要用攻防演练类措辞 —— 本审查的边界是代码正确性与数据安全）；
- 末尾必须有一行自检汇总：`BLOCKER=<n> HIGH=<n> MEDIUM=<n> LOW=<n>`（某级为 0 也写；无发现时写全 0）；
- 用中文输出；结论先行（一两句裁决），再列发现。

## ⑤ 边界

- **只读**：不得修改任何文件（`--mode build` 已阻断 Bash/Write；如遇权限阻断属预期，不是缺陷）；不要提出需要运行服务或连接数据库的验证步骤。
- **不连库**：不连 7691 / 7687 / 7692；本卡零连库 —— 不要评估任何 Neo4j / LanceDB 连接面。
- **不评**（本卡范围外）：回灌算法本身（`fallback_sync_service._sync_failed_writes` 的重放与 finalize 实现）、`.overflow.*` 代际的扫回策略、outbox 的幂等 ID 与 vault 命名空间（G4-6）、e3 已退回的 outbox 有界 / `recover_outbox` 读-改-写窗口 —— 分别归后续卡。若你认为本卡的改动**让这些变得更糟**，那属于本卡范围，请明确说出因果链。
- `DEAD_LETTER_STORE_FULL_BODY` 的默认值、`backend/data/` 下真实文件的保留期，按用户裁定不得改动（也不要作为发现提）。
- 前轮（Codex r1–r5）已处置且带负控的修复不必重复举证；除非你发现终态与所述不符。
- 本轮只审 `d2ebf694` 所钉代码终态（7 文件）；`_bmad-output/` 文档面不审（除 ⓪ 的「如实登记」口径需要）。

---

## 附录 A：变更集全文（git diff --no-pager --no-color ac0993b4 d2ebf694，7 文件）

以下 = 上述命令的**完整输出**（未经删改）：

=== 附录A 开始 ===
diff --git a/backend/app/core/failed_writes_constants.py b/backend/app/core/failed_writes_constants.py
index 8d932811..f1b19170 100644
--- a/backend/app/core/failed_writes_constants.py
+++ b/backend/app/core/failed_writes_constants.py
@@ -7,6 +7,7 @@
 import json
 import logging
 import threading
+import time
 from pathlib import Path
 from typing import Optional, Sequence
 
@@ -32,6 +33,15 @@ failed_writes_lock = threading.Lock()
 FAILED_WRITES_MAX_LINES: int = bound_from_env("CLS_FAILED_WRITES_MAX_LINES", 10000, minimum=1)
 FAILED_WRITES_MAX_ROTATIONS: int = bound_from_env("CLS_FAILED_WRITES_MAX_ROTATIONS", 5, minimum=0)
 
+# --- 回灌窗口上限（CARD-STAGING-WRITERS-BOUNDED / P2-B）---
+#
+# 回灌窗口开着时写侧不轮转（见 _replay_in_flight）。原先这个「开着」没有时间
+# 上限：回灌协程被 cancel 不干净 / 某条 await 永不返回 ⇒ 锁恒 locked ⇒ 写侧上限
+# **无限期**关闭。30 分钟是按 failed_writes 的 10000 行上限逐条 await 重放的量级
+# 估的（⚠️ 未在现网实测，见本卡验收单「本卡未证明什么」）；要改用 env 调，
+# 不改代码。坏值经 bound_from_env 退回默认并告警，不让进程导入期崩。
+REPLAY_WINDOW_MAX_SECONDS: int = bound_from_env("CLS_REPLAY_WINDOW_MAX_SECONDS", 1800, minimum=1)
+
 
 def _replay_in_flight() -> bool:
     """回灌窗口是否开着（开着就**不许轮转**）。
@@ -40,33 +50,42 @@ def _replay_in_flight() -> bool:
     Codex round-1 未发现）实地复现：
 
     ``fallback_sync_service._sync_failed_writes`` 的链是
-    「持 ``failed_writes_lock`` 读快照(:284) → **放锁** 逐条 await 重放(:337)
-    → 重新持锁 finalize(:358)」，而 finalize 判断「重放期间有没有新追加」用的是
+    「持 ``failed_writes_lock`` 读快照 → **放锁** 逐条 await 重放
+    → 重新持锁 finalize」，而 finalize 判断「重放期间有没有新追加」用的是
     **长度比较 + 位置切片**::
 
-        fallback_sync_service.py:366-367
+        # fallback_sync_service._sync_failed_writes 的 finalize 段
         if len(current_lines) > len(lines):
             new_lines = current_lines[len(lines):]
 
-    该判据的前提是**活动文件只增不减**（那个文件 :307 的注释自己写着这条契约）。
+    ⚠️ 本段一律**按符号名**指位，不写 ``fallback_sync_service.py:NNN``
+    （车道自审 2026-09-19）：本卡自己往那个文件插了 26 行，旧 docstring 里的
+    行号已整体顶掉、逐条指向不相干的代码。
+
+    该判据的前提是**活动文件只增不减**（``_sync_failed_writes`` 自己的注释写着这条契约）。
     本卡是第一个让它**变短**的写者：窗口内一旦轮转，活动文件被 rename 走、
     新文件只剩刚写的 k 条 ⇒ ``len(current) < len(lines)`` ⇒ ``new_lines=[]`` ⇒
-    窗口内新写的条目要么被 :417 ``_atomic_write_file`` 整份覆盖销毁，要么在
-    merged 为空时被 :422 ``_rotate_file`` 改名成 ``.synced.<ts>``——**谎称已回灌**，
+    窗口内新写的条目要么被 ``_atomic_write_file`` 整份覆盖销毁，要么在
+    merged 为空时被 ``_rotate_file`` 改名成 ``.synced.<ts>``——**谎称已回灌**，
     再由 30 天 retention 删掉。触发不需要多线程：``_record_structured_outbox``
-    的调用方是 async 的 ``record_knowledge_entity``，:337 的 await 就是交错点。
+    的调用方是 async 的 ``record_knowledge_entity``，重放循环里的 await 就是交错点。
 
-    ``fallback_sync_service.py`` 在本卡是**禁改**面，所以修在写侧：回灌窗口
-    开着就跳过轮转。上限因此是 best-effort（回灌期间可越限），但**不丢数据**
-    —— 这个取舍的方向不可反转。
+    ``fallback_sync_service.py`` 在 T6-C 是**禁改**面，所以修在写侧：回灌窗口
+    开着就跳过轮转。上限因此是 best-effort（回灌期间可越限）。
+    ⚠️ **「但不丢数据」这句在 P2-B 之后不再无条件成立**（Codex r3 更正）：
+    本函数新增的超时分支到期后会放行轮转，那条路径上窗口内的新条目仍可能被
+    finalize 覆盖或错标 —— 见下面「超时放行轮转本身带回了一条丢记录的路径」那条 ⚠️。
+    没有超时到期时，原来的判断仍然成立。
 
     实现说明：
     - 惰性 import —— ``fallback_sync_service:22`` 模块级 import 本模块，
       顶层反向 import 会成环。
     - ``asyncio.Lock.locked()`` 只读一个 bool，同步代码里调用不 await、不死锁。
-    - 读到 True/False 的任一竞态都安全：调用方全程持 ``failed_writes_lock``，
-      而回灌取快照也要先拿这把锁 ⇒ 「看到 False 于是轮转」时窗口必然尚未打开
-      或已关闭，没有可被破坏的快照。
+    - **非超时**分支下读到 True/False 的任一竞态都安全：调用方全程持
+      ``failed_writes_lock``，而回灌取快照也要先拿这把锁 ⇒ 「看到 False 于是轮转」
+      时窗口必然尚未打开或已关闭，没有可被破坏的快照。
+      ⚠️ **超时分支不适用这条**（Codex r2 MEDIUM）：那里返回 False 的含义是
+      「窗口开着，但开得太久，按挂住处理」—— 快照可能正活着，见下面那条 ⚠️。
     - import 不到 / 属性不在（精简部署、测试替身）⇒ 本函数视作「没有回灌」。
       ⚠️ 但**净效果不是「退回有界行为」**（Codex round-3 LOW-5 指出初版这句
       失真，已更正）：同一个 import 失败会让
@@ -74,16 +93,101 @@ def _replay_in_flight() -> bool:
       于是实际结果是**永不轮转**（满额后一直裸追加）。方向仍然安全——
       宁可越限也不丢数据——但它是「停掉上限」而不是「维持上限」，
       别按字面理解成后者。持续的权限故障同样会让越限无限持续。
+
+    超时语义（CARD-STAGING-WRITERS-BOUNDED / P2-B）—— 三态：
+
+    ===================================  ==========================================
+    ``_sync_all_lock`` / 时间戳           返回
+    ===================================  ==========================================
+    未 locked                             ``False``（窗口关着，照常轮转）
+    locked 且时间戳为 ``None``             ``True``（**直接**持锁者，无时长可比 ⇒ 保守）
+    locked 且已超 REPLAY_WINDOW_MAX_SECONDS  ``False`` + ``logger.error``（视作挂住）
+    locked 且未超上限                      ``True``
+    ===================================  ==========================================
+
+    改前只有 ``locked()`` 这一个布尔位、**没有时间维度**：回灌协程被 cancel 不
+    干净、事件循环挂起、某条 ``await`` 永不返回 ⇒ 锁永远 locked ⇒ 每次追加都走
+    「只追加不轮转」分支 ⇒ 写侧上限**无限期**关闭。超时给这个布尔位补上时间维度。
+
+    ⚠️ **不要把它读成「上限至多失效 N 秒」**（Codex r1 MEDIUM 指出初版这句过强）。
+    超时只覆盖「经 :meth:`sync_all_fallbacks` 打过时间戳」这一种持锁。其余三条
+    路径上越限仍可无限持续：① 直接持锁者（时间戳为 ``None``）无论持续多久都判
+    窗口开着；② 轮转本身持续失败（权限等）时调用方仍会继续追加；
+    ③ import 不到本模块依赖时 :func:`_invalidate_replay_checkpoint` 同样返回 False，
+    净效果是**永不轮转**（见上一段）。
+
+    ⚠️ **超时放行轮转本身带回了一条丢记录的路径**（Codex r1 HIGH，如实登记，
+    移交 P2-C REPLAY-REWRITE）：超时到期后本函数放行轮转，而此时回灌若**确实**
+    还在跑（只是慢，不是挂住），``fallback_sync_service._sync_failed_writes``
+    finalize 的「只增不减」判据（``if len(current_lines) > len(lines)``）会因为
+    活动文件**变短**而算出 ``new_lines=[]``，于是窗口内新写的条目要么被
+    ``_atomic_write_file`` 整份覆盖，要么在 merged 为空时被 ``_rotate_file`` 改名
+    成 ``.synced.``（谎称已回灌）。改前的「锁着就永不轮转」把这条路径堵死了，
+    本函数为了换回「有界」把它重新打开了一条缝 —— 这是**本卡引入的取舍**，
+    不是回灌算法的旧账。``_invalidate_replay_checkpoint`` 只作废游标，**挡不住**
+    这次 finalize。真正的修法是让 finalize 变成 generation-aware（或让超时路径把
+    新条目写进旁路文件而不缩短活动文件），两者都要动回灌侧，是 P2-C 的面。
+    在 P2-C 落地前，调高 ``CLS_REPLAY_WINDOW_MAX_SECONDS`` 可以缩小这条缝。
+
+    ⚠️ **超时还带回了第二条、后果更重的路径：游标复活**（车道自审 2026-09-19，
+    与上面那条是**不同**的因果链，一并移交 P2-C）。轮转的前置动作
+    :func:`_invalidate_replay_checkpoint` 作废游标，靠的是「换代与游标失效同生共死」
+    这条不变量；而改前 ``_replay_in_flight`` 在整次回灌期间恒 True，轮转根本
+    不可能与重放循环重叠 —— 这条不变量是**靠构造**保证的。超时把这个前提拿掉了：
+    轮转发生后，仍在跑的重放循环**可能**在下一个 checkpoint 间隔重新 ``_save_checkpoint``，
+    把一个属于**上一代文件**的下标重新绑到新一代活动文件上。
+    ⚠️ 两处限定（Codex r4 更正初版表述过强）：① 重新保存**不是必然**的 ——
+    还要满足「连续成功前缀推进过」这个条件；② 若进程在 finalize 的
+    ``_clear_checkpoint`` 之前退出（本函数 docstring 自己列为动机的 kill 场景），
+    重启后新一代 ``failed_writes.jsonl`` 里**下标小于复活游标**的那些会被
+    ``if i < checkpoint_idx: continue`` 跳过 —— 新代行数 ≤ 复活游标时就是**整份**跳过，
+    此时还会因 still_pending 为空而被 ``_rotate_file`` 改名成 ``.synced.``。
+    写侧挡不住它（游标是回灌侧自己写回的），修法同样在 P2-C。
+
+    ⚠️ 时间戳只有走 :meth:`fallback_sync_service.FallbackSyncService.sync_all_fallbacks`
+    才会被打上。直接 ``async with _sync_all_lock:`` 的持锁者（既有真锁门
+    test_dead_letter_bounded_t6c.py::test_no_rotation_while_replay_window_open、
+    测试替身）看到的是 ``None``，按上表仍判「窗口开着」—— 超时不得把它翻红。
     """
+    # ⚠️ 这两处必须写成 ``from app.services.fallback_sync_service import X`` 这种
+    # **点分模块名**形式（车道自审 2026-09-19）：既有两条常驻门
+    # （test_dead_letter_bounded_t6c.py 的 test_replay_probe_falls_back_to_bounded_when_unobservable
+    # 与 test_unobservable_replay_state_stops_rotation_not_bounding_claim）
+    # 是靠 ``builtins.__import__`` 拦 ``name == "app.services.fallback_sync_service"``
+    # 来模拟「观测不到回灌状态」的。改成 ``from app.services import fallback_sync_service``
+    # 之后 ``name`` 变成 ``"app.services"``，两条门就拦不住了 —— 它们会照常变绿，
+    # 但绿在「锁本来就没被占」这条完全不同的判据上。
     try:
         from app.services.fallback_sync_service import _sync_all_lock
-    except Exception:  # noqa: BLE001 — 观测不到回灌状态时退回有界行为
+    except Exception:  # noqa: BLE001 — 观测不到回灌状态时返回 False；净效果见 docstring
         return False
     try:
-        return bool(_sync_all_lock.locked())
+        if not _sync_all_lock.locked():
+            return False
     except Exception:  # noqa: BLE001 — 同上
         return False
 
+    # 锁着 —— 再问「占了多久」。属性不在（精简部署 / 测试替身）当作 None 处理：
+    # 没有时间戳就没有「超时」可言，只能保守地认为窗口开着。
+    try:
+        from app.services.fallback_sync_service import _sync_all_started_at
+    except Exception:  # noqa: BLE001 — 属性/模块不在 ⇒ 当作没有时间戳
+        started_at = None
+    else:
+        started_at = _sync_all_started_at
+    if started_at is None:
+        return True
+
+    elapsed = time.monotonic() - started_at
+    if elapsed > REPLAY_WINDOW_MAX_SECONDS:
+        logger.error(
+            "[C2-01] 回灌窗口已持锁 %.0f s 超过上限 %d s, 视作挂住, 恢复写侧上限",
+            elapsed,
+            REPLAY_WINDOW_MAX_SECONDS,
+        )
+        return False
+    return True
+
 
 def _invalidate_replay_checkpoint() -> bool:
     """把 ``failed_writes`` 的回灌游标作废。成功（含本来就没有）返回 True。
@@ -189,6 +293,64 @@ def _invalidate_replay_checkpoint() -> bool:
         return False
 
 
+def ensure_line_boundary(file_path: Path) -> bool:
+    """活动文件若以**半行**结尾，补一个换行。补过（或本来就不需要）返回 True。
+
+    CARD-STAGING-WRITERS-BOUNDED (P2-B, Codex r2 HIGH)：追加式 JSONL 在
+    ``ENOSPC`` / ``EIO`` 下可能写到一半就抛出去，活动文件因此以残缺 JSON 结尾
+    （如 ``{"episo``）。调用方随后**重试**同一批时，新记录会直接接在残缺尾巴
+    后面，粘成 ``{"episo{"episode_id":"A"}`` 这样一行 —— 重试的那条记录被吞掉，
+    而调用方看到「这次成功了」于是把它从 pending 里删掉：**表面重试成功、实则丢失**。
+    先补一个 ``\n``，残缺尾巴就自成一行（回灌侧按行解析时跳过它），重试的记录
+    落在下一行、完好可读。
+
+    ⚠️ 调用方必须已持 ``failed_writes_lock``（与 :func:`append_failed_writes_bounded`
+    同口径，本函数不取锁）。
+
+    ⚠️ **返回值的含义是「知不知道」，不是「要不要写」**：
+
+    - ``True``  = **已知**落在行边界上（文件不存在 / 空 / 以 ``\n`` 结尾 / 刚补上）。
+    - ``False`` = **不能确定**落在行边界上 —— 包含两种：已确认有半行但补不上，
+      以及**探测本身失败**（权限 / EIO，此时根本不知道有没有半行）。
+
+    调用方据此只决定**要不要加分隔符**，**绝不据此拒写**（Codex r4 MEDIUM）：
+    探测失败时若拒写，活动文件**可写但不可读**（``chmod 0222`` / ACL / EIO）就会让
+    ``_flush_pending_failed_writes`` **永远**刷不出去、``_pending_failed_writes``
+    无界增长、连 ``cleanup()`` 也再写不掉 —— 而**改动前**同样的批次是能落盘的
+    （``rotate_if_over_limit`` 与 ``append_failed_writes_bounded`` 都刻意吞掉了那次读失败，
+    见本文件 room 计算处的注释「宁可暂时越限，也不丢死信」）。
+    代价是：探测失败时会多写一个空行（读侧按行解析时跳过），换来的是**任何情况下都不粘连**。
+
+    行数口径不受影响：:func:`failure_counters.count_lines` 对「末行没有换行符」本来就按一行计。
+    """
+    try:
+        with open(file_path, "rb") as fh:
+            fh.seek(0, 2)
+            if fh.tell() == 0:
+                return True
+            fh.seek(-1, 2)
+            if fh.read(1) == b"\n":
+                return True
+    except FileNotFoundError:
+        return True
+    except OSError as e:
+        # 探不出来 ⇒ 返回 False（= 「不能确定在行边界上」）。调用方会加一个分隔符，
+        # 但**照常追加** —— 不拒写。Codex r4 MEDIUM：初版在这里返回 True，于是
+        # 「探测失败 + 实际有半行 + 追加成功」这条路径仍会粘连（该缺陷 PREV 也有，
+        # 属修复遗漏，不是新增回归）。
+        logger.warning("[P2-B] 探测半行尾巴失败, 本次加分隔符后照常追加 %s: %s", file_path, e)
+        return False
+
+    try:
+        with open(file_path, "a", encoding="utf-8") as fh:
+            fh.write("\n")
+    except OSError as e:
+        logger.warning("[P2-B] 补换行失败, 本次照常追加 %s: %s", file_path, e)
+        return False
+    logger.warning("[P2-B] 活动文件以半行结尾（上次追加中途失败）, 已补换行: %s", file_path)
+    return True
+
+
 def append_failed_writes_bounded(
     file_path: Path,
     lines: Sequence[str],
@@ -201,7 +363,9 @@ def append_failed_writes_bounded(
     ⛔ **本函数不取任何锁**，调用方必须已持 ``failed_writes_lock``。
     ``threading.Lock`` 非重入，在已持锁的调用方里再取同一把 = 死锁。
     实测三个写者都在 ``with failed_writes_lock:`` 里追加
-    （memory_service:515 / memory_service:2871 / agent_service:131），
+    （``memory_service._record_structured_outbox`` /
+    ``memory_service._flush_pending_failed_writes`` /
+    ``agent_service._record_failed_write``），
     所以「核行数 → 轮转 → 追加」对**进程内**全部写者原子。
 
     ⚠️ ``file_path`` 是**显式入参**而不是读本模块的 ``FAILED_WRITES_FILE``
@@ -211,13 +375,22 @@ def append_failed_writes_bounded(
     若这里改读本模块全局，那些打桩会全部失效 —— 测试会把条目写进现网
     ``backend/data/failed_writes.jsonl``，而且多半仍然显示绿（假绿）。
 
-    ⚠️ ``agent_service:130`` 这个第三写者**不经本函数**，它只持锁、不核上限。
-    所以不变量的准确表述是「经本函数的追加，追加后活动文件 ≤ max_lines」，
-    **不是**「failed_writes.jsonl 恒 ≤ max_lines」。三条限定（Codex round-1 L1
-    指出初版表述过强，这里逐条收紧）：
+    ⚠️ CARD-STAGING-WRITERS-BOUNDED（P2-B）起，``agent_service._record_failed_write``
+    这个第三写者**也经本函数**了（T6-C 时它还是裸追加，只持锁、不核上限）。
+    ``failed_writes.jsonl`` 的进程内写者因此全部有界。但不变量的准确表述仍然是
+    「经本函数的追加，追加后活动文件 ≤ max_lines」，**不是**
+    「failed_writes.jsonl 恒 ≤ max_lines」。三条限定（Codex round-1 L1 指出初版
+    表述过强，这里逐条收紧；第 1 条在 P2-B 按新事实重述）：
 
-    1. 若**始终**只有 agent_service 写入、再没有经本函数的追加，越限可以
-       **无限持续** —— 不是「暂时」。
+    1. 越限**仍可无限持续**（Codex r2 MEDIUM 更正：初版写「只是不再无限期」过强）——
+       超时只覆盖三条路径里的第一条，另外两条没有任何时间上限：
+       ① 回灌窗口开着时本函数**只追加不轮转**（见 ``_replay_in_flight``）。
+       只有「经 ``sync_all_fallbacks`` 打过时间戳」的那种持锁才受
+       ``REPLAY_WINDOW_MAX_SECONDS`` 约束；**直接持锁者**（时间戳为 ``None``，
+       如测试替身或未来新增的直接持锁点）无论持续多久都判窗口开着；
+       ② 轮转失败（权限等）时调用方仍会继续追加（见
+       ``failure_counters.rotate_if_over_limit`` 的 Returns 段）；
+       ③ **跨进程**并发写同一文件不在本锁覆盖面内（进程内锁盖不住多进程部署）。
     2. 「每个 ``.overflow.*`` 都 ≤ max_lines」**不成立**：活动文件在进入本函数
        前就已超限时（旁路突发），被**整体**轮转走的那一份就 > max_lines。
        成立的是「本函数**自己写出**的每一段 ≤ max_lines」。
@@ -237,6 +410,15 @@ def append_failed_writes_bounded(
         max_lines / max_rotations: 省略则取模块级常量（**调用时**读取，
             因此 ``monkeypatch.setattr`` 本模块常量对本函数生效）。
     """
+    # Codex r3 HIGH: 在**三个写者共用的入口**补行边界，而不是只在会重试的那个调用方
+    # 里补 —— 否则「A 写到半行失败 → B（agent_service / _record_structured_outbox，
+    # 都不重试）追加」这条路径上，B 的记录会粘在 A 的残缺尾巴后面。
+    #
+    # 返回 False = 「**不能确定**落在行边界上」（确认有半行且补不上，或探测本身失败）。
+    # 此时**不能拒写**（那两个写者没有重试缓冲，拒写 = 直接丢），改成把分隔符并进本次写入
+    # 的**第一行** —— 一次 open 写完，既不多一次 IO，也不会粘连。
+    sep = "" if ensure_line_boundary(file_path) else "\n"
+
     limit = FAILED_WRITES_MAX_LINES if max_lines is None else max_lines
     keep = FAILED_WRITES_MAX_ROTATIONS if max_rotations is None else max_rotations
 
@@ -250,7 +432,8 @@ def append_failed_writes_bounded(
         )
         with open(file_path, "a", encoding="utf-8") as f:
             for line in lines:
-                f.write(line + "\n")
+                f.write(sep + line + "\n")
+                sep = ""
         return
 
     # 分批写。``_flush_pending_failed_writes`` 一次可以交来**比上限还多**的条目，
@@ -259,7 +442,11 @@ def append_failed_writes_bounded(
     # 再接着写下一段 —— 本函数写出的每一段都 ≤ limit（限定见 docstring 三条）。
     pending = list(lines)
     while pending:
-        rotate_if_over_limit(file_path, limit, keep, before_rotate=_invalidate_replay_checkpoint)
+        if rotate_if_over_limit(file_path, limit, keep, before_rotate=_invalidate_replay_checkpoint):
+            # Codex r4 LOW: 真轮转过 ⇒ 新活动文件是**空的**，分隔符必须清掉。
+            # 否则「补换行失败 + 随后轮转成功」这条组合会往新文件先写一个空行，
+            # 首段变成 max_lines + 1 行。
+            sep = ""
         room = len(pending)
         if limit > 0:
             try:
@@ -269,8 +456,9 @@ def append_failed_writes_bounded(
                 # 不可读），rotate_if_over_limit 已经吞下了它那次读失败并返回
                 # False，若这里再让 count_lines 抛出去，追加就整个不发生 ——
                 # 比改动前的裸追加更糟，而且批量路径
-                # (_flush_pending_failed_writes) 的 finally 会 clear() 掉
-                # pending，条目直接消失。数不出行数就退化成「一次写完」：
+                # (_flush_pending_failed_writes) 会在成功后删掉本批 pending
+                # （P2-B 前是无条件 finally clear()），条目直接消失。
+                # 数不出行数就退化成「一次写完」：
                 # 宁可暂时越限，也不丢死信。
                 logger.warning("[T6-C] 数行失败, 本次不设上限直接追加 %s: %s", file_path, e)
                 room = len(pending)
@@ -281,4 +469,5 @@ def append_failed_writes_bounded(
         chunk, pending = pending[:room], pending[room:]
         with open(file_path, "a", encoding="utf-8") as f:
             for line in chunk:
-                f.write(line + "\n")
+                f.write(sep + line + "\n")
+                sep = ""
diff --git a/backend/app/core/failure_counters.py b/backend/app/core/failure_counters.py
index aefa3973..59426713 100644
--- a/backend/app/core/failure_counters.py
+++ b/backend/app/core/failure_counters.py
@@ -116,12 +116,23 @@ def count_lines(path: Path) -> int:
 
 
 def overflow_siblings(path: Path) -> List[Path]:
-    """活动文件轮转出去的 ``<stem>.overflow.<ts>`` 兄弟，按名字（== 按时间）升序。"""
+    """活动文件轮转出去的 ``<stem>.overflow.<ts>`` 兄弟，按名字（== 按时间）升序。
+
+    ⚠️ 不用 ``parent.exists()``（CARD-STAGING-WRITERS-BOUNDED / P2-B，与
+    ``count_lines`` 同型）：Python 3.14 的 ``Path.exists()`` 走
+    ``os.path.exists`` → ``os.stat``，而 ``genericpath.exists`` 的
+    ``except OSError`` 把 ``PermissionError`` **吞成 False** ⇒ 「目录读不到」被压成
+    「没有兄弟」，``_prune_overflow`` 于是认为无档可删，retention 静默失效。
+    直接 ``iterdir()`` 显式分流：目录真的不在 ⇒ 空列表；其余 OSError 上抛，由
+    调用方 ``_prune_overflow``（已 ``except OSError``）接住并跳过清理。
+    """
     parent = path.parent
-    if not parent.exists():
+    try:
+        entries = list(parent.iterdir())
+    except FileNotFoundError:
         return []
     prefix = path.stem + OVERFLOW_SUFFIX
-    return sorted((p for p in parent.iterdir() if p.name.startswith(prefix)), key=lambda p: p.name)
+    return sorted((p for p in entries if p.name.startswith(prefix)), key=lambda p: p.name)
 
 
 def _unique_overflow_target(path: Path) -> Path:
@@ -150,8 +161,17 @@ def _unique_overflow_target(path: Path) -> Path:
     # 所有名字同形之后，同微秒内按 `-NN` 递增、跨微秒由时间戳主导，两级都对。
     for n in range(100):
         candidate = path.with_suffix(f"{OVERFLOW_SUFFIX}{stamp}-{n:02d}{tail}")
-        if not candidate.exists():
+        # ⚠️ 不用 candidate.exists()（CARD-STAGING-WRITERS-BOUNDED / P2-B，同上）：
+        # 探测被 PermissionError 拦下时 exists() 压成 False ⇒ 交出一个**可能已被
+        # 占用**的名字 ⇒ 上面 docstring 说的 rename 静默覆盖会丢整份 overflow。
+        # stat 显式分流：确认不在才用；探不出来就当作已占用、换下一个序号
+        # （宁可跳号，也不冒覆盖数据的风险）。
+        try:
+            candidate.stat()
+        except FileNotFoundError:
             return candidate
+        except OSError:
+            continue
     # 同一微秒连撞 100 次基本不可能；真发生了宁可牺牲族内有序也不覆盖数据。
     # ⚠️ 分隔符用 `~`(0x7E) 不用 `-`(0x2D)：`-` < `.`(0x2E) 会让 `-99-<uuid>.jsonl`
     # 排在 `-99.jsonl` **之前**，于是「删最老」会去删这个最新的兜底档
diff --git a/backend/app/services/agent_service.py b/backend/app/services/agent_service.py
index 03c3d8b4..df1b02dc 100644
--- a/backend/app/services/agent_service.py
+++ b/backend/app/services/agent_service.py
@@ -28,7 +28,11 @@ from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple
 
 from cachetools import TTLCache
 
-from app.core.failed_writes_constants import FAILED_WRITES_FILE, failed_writes_lock
+from app.core.failed_writes_constants import (
+    FAILED_WRITES_FILE,
+    append_failed_writes_bounded,
+    failed_writes_lock,
+)
 from app.middleware.prompt_injection_guard import (
     SAFETY_BLOCK_INPUT_MESSAGE,
     check_input,
@@ -127,8 +131,17 @@ def _record_failed_write(
         }
         FAILED_WRITES_FILE.parent.mkdir(parents=True, exist_ok=True)
         with failed_writes_lock:
-            with open(FAILED_WRITES_FILE, "a", encoding="utf-8") as f:
-                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
+            # CARD-STAGING-WRITERS-BOUNDED: 第三写者切有界追加 —— 超
+            # FAILED_WRITES_MAX_LINES 先轮转成 .overflow.<ts>。helper 不自持锁
+            # （外层这把是非重入的），与 memory_service:515-518 逐字同形。
+            # ⚠️ 路径继续用本模块级的 FAILED_WRITES_FILE 绑定副本：既有测试打桩的
+            # 正是这一侧（实测 12 处，分布在 test_story_38_7_ac4_degraded_mode.py /
+            # test_story_38_7_qa_supplement.py / test_qa_38_6_scoring_reliability_extra.py /
+            # test_story_38_6_scoring_reliability.py 四个既有文件），改读
+            # failed_writes_constants 的全局会让那些测试静默写进现网数据文件且仍绿。
+            # 序列化留在调用方，json.dumps 的 TypeError/ValueError 仍由下面既有的
+            # except 元组接住，异常语义不变。
+            append_failed_writes_bounded(FAILED_WRITES_FILE, [json.dumps(entry, ensure_ascii=False)])
         logger.warning(
             f"[Story 38.6] Score write failed after retries, saved to fallback: {concept_id}"
         )
diff --git a/backend/app/services/episode_worker.py b/backend/app/services/episode_worker.py
index 27537113..112b1776 100644
--- a/backend/app/services/episode_worker.py
+++ b/backend/app/services/episode_worker.py
@@ -30,6 +30,7 @@ from datetime import datetime, timezone
 from pathlib import Path
 from typing import Any, Optional
 
+import app.core.failure_counters as _fc
 from app.core.failure_counters import DEAD_LETTER_EPISODES_PATH
 from graphiti_core import Graphiti
 
@@ -260,8 +261,20 @@ class DeadLetterStore:
         if request_id is not None:
             record["request_id"] = request_id
 
-        with open(self._file_path, "a", encoding="utf-8") as f:
-            f.write(json.dumps(record, ensure_ascii=False) + "\n")
+        # CARD-STAGING-WRITERS-BOUNDED (P2-B): 写侧有界 —— 超上限先轮转成
+        # ``<stem>.overflow.<ts>`` 再追加，Neo4j 永久离线时这份 JSONL 不再单调
+        # 增长到占满磁盘。上限在**调用时**读模块属性（``monkeypatch`` 对它生效）；
+        # 复用 ``CLS_DEAD_LETTER_MAX_LINES/ROTATIONS`` 族，不另立 env。
+        # ``rotate_if_over_limit`` 不自持锁 ⇒ 这里要拿 failure_counters 的
+        # ``_dead_letter_io_lock``（与本文件既有的任何锁都不嵌套，无死锁面）。
+        with _fc._dead_letter_io_lock:
+            _fc.rotate_if_over_limit(
+                self._file_path,
+                _fc.DEAD_LETTER_MAX_LINES,
+                _fc.DEAD_LETTER_MAX_ROTATIONS,
+            )
+            with open(self._file_path, "a", encoding="utf-8") as f:
+                f.write(json.dumps(record, ensure_ascii=False) + "\n")
 
         # audit-2026-04-07/p1-1: scrub error from logger interpolation. Type
         # name only — full message is in the JSONL record (already redacted).
@@ -273,10 +286,30 @@ class DeadLetterStore:
         )
 
     def count(self) -> int:
-        if not self._file_path.exists():
-            return 0
-        with open(self._file_path, "r", encoding="utf-8") as f:
-            return sum(1 for _ in f)
+        """死信条数。
+
+        CARD-STAGING-WRITERS-BOUNDED (P2-B): 改走 ``failure_counters.count_lines``：
+
+        ① 口径与写侧上限判定统一 —— 与 ``rotate_if_over_limit`` 数的是同一个数
+           （都按 ``b"\\n"``）。⚠️ 不是「旧实现会在 U+2028/U+2029 上漂」
+           （车道自审 2026-09-19 更正初版这句失实）：旧实现
+           ``for _ in open(path, "r", encoding="utf-8")`` 是**文本模式逐行迭代**，
+           只按 ``\\n`` 切、不把 U+2028/U+2029 当行分隔符，计数本来就一致。
+           真正的差别是下面 ② 的异常语义，以及「和上限判定共用同一实现」这件事本身；
+        ② ``Path.exists()`` 在 Python 3.14 走 ``os.path.exists`` → ``os.stat``，
+           而 ``genericpath.exists`` 的 ``except OSError`` 会把 ``PermissionError``
+           **吞成 False** —— 于是「读不到」和「文件不存在」都返回 0，调用方无从
+           分辨。``count_lines`` 用 ``stat()`` 显式分流：``FileNotFoundError`` → 0，
+           其余 ``OSError`` 上抛。
+
+        （``backend/app`` 内本方法**零调用方**，口径变更无下游语义影响。）
+
+        ⚠️ **代价，如实登记**（车道自审 2026-09-19）：``count_lines`` 会把整份文件
+        读一遍。``store()`` 现在每写一条都先经 ``rotate_if_over_limit`` 扫一次全文件，
+        而这段同步 IO 跑在事件循环上、且持 ``_dead_letter_io_lock``。
+        死信量大时这是一笔新的按文件大小线性增长的开销（本卡未做增量计数优化）。
+        """
+        return _fc.count_lines(self._file_path)
 
 
 # ═══════════════════════════════════════════════════════════════════════════════
diff --git a/backend/app/services/fallback_sync_service.py b/backend/app/services/fallback_sync_service.py
index 7c543ee1..713a69d1 100644
--- a/backend/app/services/fallback_sync_service.py
+++ b/backend/app/services/fallback_sync_service.py
@@ -83,6 +83,27 @@ _PROGRESS_VERSION = "split-lf+contiguous+history"
 #: 单飞标志），已如实登记，不在本卡范围。
 _sync_all_lock = asyncio.Lock()
 
+#: CARD-STAGING-WRITERS-BOUNDED: 本轮回灌的开始时刻（``time.monotonic()``）。
+#:
+#: 写侧守卫 ``failed_writes_constants._replay_in_flight`` 原先只读
+#: ``_sync_all_lock.locked()`` —— **没有时间维度**。回灌协程被 cancel 不干净、
+#: 事件循环挂起、或某条 ``await`` 永不返回时，这把锁会**永远** locked，于是写侧
+#: 上限被**无限期**关闭（每次追加都走裸追加分支）。有了开始时刻，守卫至少能问出
+#: 「这把锁被占了多久」。
+#:
+#: ⚠️ 时间戳量的是**耗时**，不是存活性（Codex r1 MEDIUM）：一次又慢又健康的回灌
+#: 和一次挂死的回灌在这里长得一模一样。超时只是「久到该按挂住处理」的工程取舍，
+#: 不是「区分正在回灌与挂住」的判据 —— 它误判健康长回灌的后果见
+#: ``failed_writes_constants._replay_in_flight`` 的 docstring（已移交 P2-C）。
+#:
+#: ⚠️ ``None`` 本身**不**决定守卫的答案（车道自审 2026-09-19 更正初版这句失实）：
+#: 守卫先读 ``_sync_all_lock.locked()``，**没人持锁时直接返回 False（窗口关着）**，
+#: 根本读不到这个变量。只有在**已经确认锁被占着**之后，``None`` 才有含义 ——
+#: 它表示持锁者是**直接** ``async with _sync_all_lock:`` 的那种（测试替身、
+#: 或未经 :meth:`sync_all_fallbacks` 的新持锁点），没有时间戳可比，
+#: 于是保守地判「窗口开着」—— 宁可越限也不丢数据。
+_sync_all_started_at: Optional[float] = None
+
 
 class FallbackSyncService:
     """Syncs JSON fallback files back to Neo4j when it recovers."""
@@ -107,8 +128,16 @@ class FallbackSyncService:
         Returns:
             Dict with per-file stats or {"skipped": True, "reason": "..."}
         """
+        # CARD-STAGING-WRITERS-BOUNDED: 打上开始时刻，写侧守卫据此判「挂住了没」。
+        # 必须在**取到锁之后**打、在 finally 里清 —— 排队等锁的那段不算窗口时长，
+        # 否则高并发下第二个等待者会把第一个的时间戳冲掉。
+        global _sync_all_started_at
         async with _sync_all_lock:
-            return await self._sync_all_fallbacks_locked()
+            _sync_all_started_at = time.monotonic()
+            try:
+                return await self._sync_all_fallbacks_locked()
+            finally:
+                _sync_all_started_at = None
 
     async def _sync_all_fallbacks_locked(self) -> Dict[str, Any]:
         """:meth:`sync_all_fallbacks` 的实际实现（调用方须已持有 :data:`_sync_all_lock`）."""
diff --git a/backend/app/services/memory_service.py b/backend/app/services/memory_service.py
index f865d1e9..78fc262f 100644
--- a/backend/app/services/memory_service.py
+++ b/backend/app/services/memory_service.py
@@ -1428,6 +1428,14 @@ class MemoryService:
                         }
                     )
 
+                # CARD-STAGING-WRITERS-BOUNDED (P2-B): 批次失败**即时**落盘。
+                # 改前只有 cleanup() 会刷盘 —— 进程被 kill / 崩溃 = 从未调过
+                # cleanup = 整批失败记录消失（T6-A「链3 写者3」）。
+                # 同步方法、append 与 clear 之间没有 await，
+                # _flush_pending_failed_writes 自述的那条不变量仍成立。
+                # cleanup() 里的那次刷盘保留为第二道防线（正常路径下已是 no-op）。
+                self._flush_pending_failed_writes()
+
         # ── Phase 2: Enqueue batch events to GraphitiEpisodeWorker ──
         for record in valid_records:
             p = record["payload"]
@@ -2857,6 +2865,23 @@ class MemoryService:
         Story 30.24 AC-30.24.4: Persist pending batch write failures to
         data/failed_writes.jsonl so they survive shutdown.
 
+        CARD-STAGING-WRITERS-BOUNDED (P2-B): 调用时机从「仅 cleanup()」改成
+        「批次失败即时 + cleanup() 兜底」—— 进程被 kill 或崩溃时永远不会走到
+        cleanup()，只等它刷盘等于整批丢失。record_batch_learning_events 在写完
+        _pending_failed_writes 后立刻调本方法；cleanup() 那次保留为第二道防线
+        （正常路径下 _pending_failed_writes 已空，是 no-op）。
+
+        失败语义随之分流（Codex r1 HIGH-2）：**OSError 不清空** —— 磁盘故障可恢复，
+        留给下一批次或 cleanup() 重试（代价：部分写入后重试会产生重复条目，
+        死信文件里重复远比丢失轻）；**TypeError / ValueError 丢弃** —— 序列化失败是
+        确定性的，留着只会让 pending 无限增长。成功路径只删**本批**条目，
+        不再 clear() 整个列表。
+
+        ⚠️ 本方法的文件 IO 是**同步**的，而新调用点在 async 的
+        record_batch_learning_events 里：数行 / 轮转 / 追加期间事件循环不调度别的
+        协程（若另一线程持 failed_writes_lock，还会同步等锁）。cleanup() 路径原本
+        就是同一段同步 IO，本卡把它的发生时机提前到了请求期 —— 如实登记，未做异步化。
+
         Thread-safe via failed_writes_lock (shared with agent_service).
 
         Note: This is a synchronous method called from async cleanup().
@@ -2867,23 +2892,65 @@ class MemoryService:
         if not self._pending_failed_writes:
             return
 
+        batch = list(self._pending_failed_writes)
+
+        # 逐条序列化（Codex r2 MEDIUM）：原先是一句列表推导，任何**一条**坏条目都会
+        # 让整批走进 TypeError 分支被丢掉，好条目跟着陪葬。序列化失败是确定性的
+        # （同一条重试多少次都失败），所以只丢那一条、其余照常落盘。
+        lines: List[str] = []
+        for entry in batch:
+            try:
+                line = json.dumps(entry, ensure_ascii=False)
+                # Codex r3 MEDIUM: 提前验 UTF-8 可编码性。json.dumps(ensure_ascii=False)
+                # 对孤立代理（如 "\ud800"）会**成功**，真正炸的是写盘那一刻的
+                # UnicodeEncodeError —— 它是 ValueError 不是 OSError，会从本方法逃出去，
+                # 改变 record_batch_learning_events 的返回语义。在这里就把它归成坏条目。
+                line.encode("utf-8")
+                lines.append(line)
+            except (TypeError, ValueError) as e:
+                logger.error(f"[Story 30.24] Dropping one unserializable pending write: {e}")
+
+        if not lines:
+            del self._pending_failed_writes[: len(batch)]
+            return
+
         try:
             FAILED_WRITES_FILE.parent.mkdir(parents=True, exist_ok=True)
             with failed_writes_lock:
-                # T6-C: 有界追加（同上）。序列化留在这里，json.dumps 的
-                # TypeError/ValueError 仍由下面既有的 except 元组接住。
-                append_failed_writes_bounded(
-                    FAILED_WRITES_FILE,
-                    [json.dumps(entry, ensure_ascii=False) for entry in self._pending_failed_writes],
-                )
-            logger.warning(
-                f"[Story 30.24] Flushed {len(self._pending_failed_writes)} "
-                f"pending failed writes to {FAILED_WRITES_FILE}"
-            )
-        except (OSError, TypeError, ValueError) as e:
-            logger.error(f"[Story 30.24] Failed to flush pending writes: {e}")
-        finally:
-            self._pending_failed_writes.clear()
+                # Codex r2 HIGH: 上一次可能写到**半行**就抛了 OSError，活动文件以残缺
+                # JSON 结尾。不先补换行的话，这次重试的记录会直接接在残缺尾巴后面粘成
+                # 一行 —— 重试记录被吞掉，而下面还会把它从 pending 里删掉，等于
+                # 「看起来重试成功了，实际丢了」。
+                # T6-C: 有界追加 —— 超 FAILED_WRITES_MAX_LINES 先轮转成 .overflow.<ts>。
+                # 半行尾巴由 append_failed_writes_bounded 入口的 ensure_line_boundary 处理：
+                # 补得上就补，补不上就把分隔符并进它写出的第一行。这里**不再**自己检查返回值
+                # 后拒写 —— 那个写法在「文件可写但不可读」时会让本方法永远刷不出去、
+                # pending 无界增长，比改动前更坏（车道自审 2026-09-19）。
+                append_failed_writes_bounded(FAILED_WRITES_FILE, lines)
+            logger.warning(f"[Story 30.24] Flushed {len(lines)} pending failed writes to {FAILED_WRITES_FILE}")
+        except OSError as e:
+            # CARD-STAGING-WRITERS-BOUNDED (P2-B, Codex r1 HIGH-2): **失败不清空**。
+            # 原先是 `finally: clear()` —— 无条件清。在「只有 cleanup() 会刷盘」的
+            # 年代那还只是进程退出时的最后一搏；本卡把刷盘提前到**每个失败批次**之后，
+            # 无条件清就变成「请求期间一次瞬时 IO 故障（盘满 / 权限 / EIO）= 这批记录
+            # 永久消失」，而且 cleanup() 那道兜底也再没有内容可写。
+            # 磁盘故障是可恢复的 ⇒ 留在 pending 里，下一批次或 cleanup() 重试。
+            # ⚠️ 若 append 已写进一部分**完整行**才失败，重试会产生**重复**条目 ——
+            # 死信文件里重复远比丢失轻，这个方向不可反转。写到**半行**的情况由
+            # ensure_line_boundary 在下次重试前补齐边界（Codex r2 HIGH）。
+            # ⚠️ 坏条目也一并留着，下次重试会再逐条丢弃一次；列表不会因此增长。
+            logger.error(f"[Story 30.24] Failed to flush pending writes, kept for retry: {e}")
+            return
+        except ValueError as e:
+            # Codex r3 MEDIUM: 编码类失败是**确定性**的（序列化阶段已预验，这里是纵深）。
+            # 不能让它逃出本方法 —— 那会把 record_batch_learning_events 的返回语义
+            # 从「返回 errors/failed/episode_ids」变成「整个请求抛异常」。丢弃本批并 error。
+            logger.error(f"[Story 30.24] Dropping {len(lines)} pending writes (encoding failure): {e}")
+
+        # 只清掉**本批**（含已丢弃的坏条目），而不是 clear() 整个列表：刷盘期间若有
+        # 新条目追加进来（本方法同步、中间无 await，单事件循环下不会发生；多线程调用方
+        # 则可能），不该被连坐清掉。
+        del self._pending_failed_writes[: len(batch)]
 
 
 # Singleton instance — the ONLY MemoryService singleton entry point for the entire project.
diff --git a/backend/tests/unit/test_staging_writers_bounded.py b/backend/tests/unit/test_staging_writers_bounded.py
new file mode 100644
index 00000000..7bb9069c
--- /dev/null
+++ b/backend/tests/unit/test_staging_writers_bounded.py
@@ -0,0 +1,1072 @@
+"""CARD-STAGING-WRITERS-BOUNDED (P2-B, BATCH-2026-09-18-第十五批) — 暂存 JSONL 剩余无界写者收口。
+
+先红后绿门。改前的五个缺陷面：
+
+1. ``agent_service._record_failed_write`` 是 ``failed_writes.jsonl`` 的**第三个**写者，
+   裸 ``open(..., "a")`` 追加，不经 ``append_failed_writes_bounded``（T6-C 只切了
+   memory_service 两处）⇒ 只要这条路径在写，上限就形同虚设。
+2. ``failed_writes_constants._replay_in_flight`` 只读 ``_sync_all_lock.locked()``，
+   **无时间维度** ⇒ 回灌协程被 cancel 不干净 / 某条 await 永不返回时，锁恒 locked，
+   写侧上限**无限期**关闭。
+3. ``MemoryService._pending_failed_writes`` 只在 ``cleanup()`` 刷盘 ⇒ 进程被 kill
+   或崩溃 = 从未调 cleanup = 整批失败记录消失。
+4. ``DeadLetterStore.store`` 裸追加 ⇒ 无上限、无轮转。（``EventBus._write_outbox``
+   同型，但 e3 子项已按卡文退回第十六批，见本卡验收单；本文件不再覆盖它。）
+5. ``Path.exists()`` 在 Python 3.14 把 ``PermissionError`` **吞成 False** ⇒
+   「读不到」与「不存在」不可区分：``overflow_siblings`` 静默返回空、
+   ``_unique_overflow_target`` 交出一个可能已被占用的名字（``rename`` POSIX 下静默
+   覆盖 = 丢整份 overflow）、``DeadLetterStore.count`` 把读不到压成 0。
+
+⛔ 硬边界：本文件**所有**路径一律 ``monkeypatch`` / ``tmp_path``，不触碰现网
+``backend/data/**``，不连 7691/7687（本文件零连库）。**被测写者本身不打桩**（DD-03）
+—— 唯一的替身在 Neo4j 客户端边界（``record_episode``），被测对象是刷盘时机与文件 IO。
+
+⚠️ 计数口径：本文件数行一律 ``read_bytes().count(b"\\n")``，与生产 ``count_lines``
+逐字节同口径。**不用 ``splitlines()``** —— 它会在 U+2028 / U+2029 处额外切行，
+与生产计数不同口径，会让门的真值随条目内容漂移。
+"""
+
+from __future__ import annotations
+
+import ast
+import json
+import os
+import pathlib
+import time
+from typing import Any, Dict, List, Set
+from unittest.mock import AsyncMock, MagicMock
+
+import pytest
+
+import app.core.failed_writes_constants as fwc
+import app.core.failure_counters as fc
+
+# 与生产默认值无关的小值：门只验「阈值触发」这个行为，不验具体默认值。
+MAX_LINES = 5
+MAX_ROTATIONS = 3
+# 守卫超时门用的窗口上限（秒）。同样与生产默认 1800 无关。
+REPLAY_WINDOW = 60
+
+
+# ═══════════════════════════════════════════════════════════════════════════
+# 计数 / 枚举工具（与生产同口径）
+# ═══════════════════════════════════════════════════════════════════════════
+
+
+def _nlines(path) -> int:
+    """按 b"\\n" 数行——与生产 ``count_lines`` 同口径。"""
+    if not path.exists():
+        return 0
+    return path.read_bytes().count(b"\n")
+
+
+def _overflow_siblings(path):
+    """活动文件的 ``.overflow.*`` 兄弟（按名字排序 == 按时间排序）。"""
+    if not path.parent.exists():
+        return []
+    return sorted(p for p in path.parent.iterdir() if p.name.startswith(path.stem) and ".overflow." in p.name)
+
+
+def _records(path) -> List[Dict[str, Any]]:
+    """读一份 JSONL 的全部记录（文件不在 ⇒ 空）。"""
+    if not path.exists():
+        return []
+    out: List[Dict[str, Any]] = []
+    for raw in path.read_bytes().decode("utf-8").split("\n"):
+        if raw.strip():
+            out.append(json.loads(raw))
+    return out
+
+
+def _identity_union(path, field: str) -> Set[str]:
+    """活动文件 + 全部 overflow 兄弟里该字段的取值并集。
+
+    ⚠️ 有界门必须按**身份**判「一条不丢」，不是按数量：等长替换（丢一条、
+    重复另一条）在数量判据下恒绿。
+    """
+    seen: Set[str] = set()
+    for f in [path, *_overflow_siblings(path)]:
+        for rec in _records(f):
+            seen.add(str(rec[field]))
+    return seen
+
+
+# ═══════════════════════════════════════════════════════════════════════════
+# fixtures —— 每条链各自把路径与上限指向 tmp_path
+# ═══════════════════════════════════════════════════════════════════════════
+
+
+def _isolate_live_checkpoint(monkeypatch, tmp_path):
+    """⛔ 隔离现网回灌 checkpoint。
+
+    failed_writes 轮转的**前置动作**（``_invalidate_replay_checkpoint``）会
+    删/改 ``SYNC_CHECKPOINT_FILE``。只隔离数据文件的话，任何触发轮转的用例都会
+    去动现网 ``backend/data/sync_checkpoint.json``，而且该文件不存在时测试照样绿
+    —— 结果悄悄依赖真实磁盘状态（T6-C Codex round-3 HIGH-2 的同型坑）。
+    """
+    import app.services.fallback_sync_service as _fss
+
+    monkeypatch.setattr(_fss, "SYNC_CHECKPOINT_FILE", tmp_path / "sync_checkpoint.json")
+
+
+@pytest.fixture
+def bounded_agent_writes(monkeypatch, tmp_path):
+    """第三写者（agent_service）侧的上限与路径全指向 tmp_path。
+
+    ⚠️ 打桩 ``app.services.agent_service.FAILED_WRITES_FILE``（**导入方**的模块级
+    绑定副本）而不是 ``fwc.FAILED_WRITES_FILE``：既有测试
+    （test_story_38_7_ac4_degraded_mode.py:95 / test_story_38_7_qa_supplement.py:233,275
+    / test_qa_38_6_scoring_reliability_extra.py:58,83）打的就是这一侧，生产实现必须
+    继续从这一侧取路径，否则那些测试会静默写进现网 backend/data/failed_writes.jsonl
+    且仍然显示绿（假绿）。
+
+    ``raising=False`` 用于上限常量：让改前的红落在行为断言上，而不是 AttributeError
+    （否则负控把实现改回裸追加时会红在同一个 AttributeError 上，负控失去鉴别力）。
+    """
+    import app.services.agent_service as _ags
+
+    monkeypatch.setattr(fwc, "FAILED_WRITES_MAX_LINES", MAX_LINES, raising=False)
+    monkeypatch.setattr(fwc, "FAILED_WRITES_MAX_ROTATIONS", MAX_ROTATIONS, raising=False)
+    path = tmp_path / "failed_writes.jsonl"
+    monkeypatch.setattr(_ags, "FAILED_WRITES_FILE", path)
+    _isolate_live_checkpoint(monkeypatch, tmp_path)
+    return path
+
+
+@pytest.fixture
+def bounded_memory_writes(monkeypatch, tmp_path):
+    """memory_service 侧的 failed_writes 上限与路径指向 tmp_path（同 T6-C 口径）。"""
+    import app.services.memory_service as _ms
+
+    monkeypatch.setattr(fwc, "FAILED_WRITES_MAX_LINES", MAX_LINES, raising=False)
+    monkeypatch.setattr(fwc, "FAILED_WRITES_MAX_ROTATIONS", MAX_ROTATIONS, raising=False)
+    path = tmp_path / "failed_writes.jsonl"
+    monkeypatch.setattr(_ms, "FAILED_WRITES_FILE", path)
+    _isolate_live_checkpoint(monkeypatch, tmp_path)
+    return path
+
+
+@pytest.fixture
+def bounded_dead_letter_episodes(monkeypatch, tmp_path):
+    """episode 死信上限指向小值，路径由调用方显式传 tmp_path。"""
+    monkeypatch.setattr(fc, "DEAD_LETTER_MAX_LINES", MAX_LINES, raising=False)
+    monkeypatch.setattr(fc, "DEAD_LETTER_MAX_ROTATIONS", MAX_ROTATIONS, raising=False)
+    _isolate_live_checkpoint(monkeypatch, tmp_path)
+    return tmp_path / "dead_letter_episodes.jsonl"
+
+
+@pytest.fixture
+def service():
+    """不跑 ``__init__`` 的 MemoryService 壳 —— 只用来驱动同步写者（同 T6-C）。"""
+    import app.services.memory_service as _ms
+
+    svc = _ms.MemoryService.__new__(_ms.MemoryService)
+    svc._initialized = True
+    svc._episodes = []
+    svc._pending_failed_writes = []
+    return svc
+
+
+# ═══════════════════════════════════════════════════════════════════════════
+# (c) 第三写者 —— agent_service._record_failed_write 切有界 helper
+# ═══════════════════════════════════════════════════════════════════════════
+
+
+def test_agent_service_third_writer_is_bounded(bounded_agent_writes):
+    """改前必红：agent_service 裸追加 ⇒ 活动文件 8 行、零 overflow。
+
+    断言按**身份**核「一条不丢」：8 个 concept_id 必须全部在
+    「活动文件 ∪ overflow 兄弟」里。
+    """
+    import app.services.agent_service as _ags
+
+    path = bounded_agent_writes
+    total = MAX_LINES + 3
+
+    for i in range(total):
+        _ags._record_failed_write(
+            event_type="score_recorded",
+            concept_id=f"c{i}",
+            canvas_name="Math/test.canvas",
+            score=float(i),
+            error_reason="neo4j down",
+        )
+
+    assert _nlines(path) <= MAX_LINES, (
+        f"活动文件超行数：{_nlines(path)} > {MAX_LINES} —— 第三写者仍是裸追加，写侧上限对它无效"
+    )
+    assert _overflow_siblings(path), "没有 .overflow.* —— 从未发生轮转"
+    assert _identity_union(path, "concept_id") == {f"c{i}" for i in range(total)}, "轮转丢了条目"
+
+
+def test_third_writer_does_not_concatenate_onto_dangling_tail(bounded_agent_writes):
+    """别人留下的半行不得把**第三写者**的新记录吞掉（Codex r3 HIGH 的第二半）。
+
+    ``agent_service._record_failed_write`` 没有重试缓冲：它写出去就删不回来，
+    所以粘连对它等于**直接丢**。行边界修复必须在三个写者共用的入口
+    （``append_failed_writes_bounded``）上，而不是只在会重试的那个调用方里。
+    """
+    import app.services.agent_service as _ags
+
+    path = bounded_agent_writes
+    path.write_bytes(b'{"episo')  # 上一个写者写到一半就失败了
+
+    _ags._record_failed_write(
+        event_type="score_recorded",
+        concept_id="after-dangling",
+        canvas_name="Math/test.canvas",
+        score=1.0,
+        error_reason="neo4j down",
+    )
+
+    raw_lines = [ln for ln in path.read_bytes().decode("utf-8").split("\n") if ln.strip()]
+    parsed = []
+    for ln in raw_lines:
+        try:
+            parsed.append(json.loads(ln))
+        except json.JSONDecodeError:
+            pass
+
+    assert raw_lines[0] == '{"episo', f"残缺尾巴没有自成一行 —— 和第三写者的新记录粘在一起了: {raw_lines[0]!r}"
+    assert any(r.get("concept_id") == "after-dangling" for r in parsed), (
+        f"第三写者的记录被半行尾巴吞掉了（它没有重试缓冲 = 直接丢）: {path.read_bytes()!r}"
+    )
+
+
+# ═══════════════════════════════════════════════════════════════════════════
+# (d) 回灌窗口守卫超时 —— 三态：unlocked / 直接持锁(None) / stale
+#
+# 全部用**真实的** ``_sync_all_lock``，不打桩 ``locked()`` —— 打桩只能证明
+# 「我写的判断会被调用」，证明不了它读的是回灌侧真正在用的那把锁。
+# 驱动写者用 ``_record_structured_outbox``（memory_service 侧，T6-C 已切 helper），
+# 这样负控①（把 agent_service 换回裸追加）对这三条门**不产生影响**，
+# 负控①的鉴别力才只绑第三写者。
+# ═══════════════════════════════════════════════════════════════════════════
+
+
+async def test_replay_guard_times_out_when_lock_stuck(service, bounded_memory_writes, monkeypatch):
+    """改前必红：锁被挂住（持锁时刻远早于上限）时仍判「窗口开着」⇒ 永不轮转。
+
+    ``raising=False``：改前 ``REPLAY_WINDOW_MAX_SECONDS`` / ``_sync_all_started_at``
+    都还不存在，先设上去，红才会落在「未轮转」这个行为断言而不是 AttributeError。
+    """
+    import app.services.fallback_sync_service as fss
+
+    path = bounded_memory_writes
+    monkeypatch.setattr(fwc, "REPLAY_WINDOW_MAX_SECONDS", REPLAY_WINDOW, raising=False)
+
+    async with fss._sync_all_lock:
+        monkeypatch.setattr(
+            fss,
+            "_sync_all_started_at",
+            time.monotonic() - (fwc.REPLAY_WINDOW_MAX_SECONDS + 5),
+            raising=False,
+        )
+        for i in range(MAX_LINES + 3):
+            assert service._record_structured_outbox({"kind": "knowledge_entity", "i": i})
+
+    assert _overflow_siblings(path), "锁挂住超过上限后仍未轮转 —— 守卫没有时间维度，写侧上限被无限期关闭"
+
+
+async def test_replay_guard_respects_fresh_window(service, bounded_memory_writes, monkeypatch):
+    """对照输入：同样持锁，但持锁时刻是**刚刚** ⇒ 仍在窗口内，绝不轮转。
+
+    没有这条，上面那条门用「永远轮转」也能变绿。
+    """
+    import app.services.fallback_sync_service as fss
+
+    path = bounded_memory_writes
+    total = MAX_LINES + 3
+    monkeypatch.setattr(fwc, "REPLAY_WINDOW_MAX_SECONDS", REPLAY_WINDOW, raising=False)
+
+    async with fss._sync_all_lock:
+        monkeypatch.setattr(fss, "_sync_all_started_at", time.monotonic(), raising=False)
+        for i in range(total):
+            assert service._record_structured_outbox({"kind": "knowledge_entity", "i": i})
+
+    assert _overflow_siblings(path) == [], "窗口新鲜却发生了轮转 —— finalize 的「只增不减」判据会被打破"
+    assert _nlines(path) == total, "窗口内的条目丢了"
+
+
+async def test_replay_guard_treats_direct_lock_holder_as_in_flight(service, bounded_memory_writes, monkeypatch):
+    """对照输入：**直接持锁**（没有经过 ``sync_all_fallbacks``，无时间戳）仍判窗口内。
+
+    这是既有真锁门 test_dead_letter_bounded_t6c.py::test_no_rotation_while_replay_window_open
+    的语义 —— 超时设计不得把它翻红：没有时间戳就没有「超时」可言，只能保守地
+    认为窗口开着（宁可越限也不丢数据，方向不可反转）。
+    """
+    import app.services.fallback_sync_service as fss
+
+    path = bounded_memory_writes
+    total = MAX_LINES + 3
+    monkeypatch.setattr(fwc, "REPLAY_WINDOW_MAX_SECONDS", REPLAY_WINDOW, raising=False)
+    monkeypatch.setattr(fss, "_sync_all_started_at", None, raising=False)
+
+    async with fss._sync_all_lock:
+        for i in range(total):
+            assert service._record_structured_outbox({"kind": "knowledge_entity", "i": i})
+
+    assert _overflow_siblings(path) == [], "直接持锁者被误判成超时 —— 既有真锁门会随之翻红"
+    assert _nlines(path) == total, "窗口内的条目丢了"
+
+
+async def test_sync_all_fallbacks_stamps_and_clears_started_at(monkeypatch):
+    """``sync_all_fallbacks`` 必须在**持锁期间**打上时间戳、退出时清空，且用的是
+    **守卫读的那口时钟**。
+
+    只测守卫读的那一侧不够：时间戳如果没人写，超时分支永远等不到 stale 值，
+    整条超时语义在生产路径上是死的（门绿在「另一条路径」上）。
+
+    ⚠️ 只断言 ``isinstance(float)`` 不够：``time.time()`` 同样是 float，但它与守卫用的
+    ``time.monotonic()`` **不是同一口时钟**（在本机相差数十年）。写侧一旦换成 ``time.time()``，
+    守卫算出的 ``elapsed = monotonic() - stamp`` 会变成一个巨大的**负数** ⇒ **恒不超时**，
+    超时分支彻底变成死代码（Codex r4 更正：初版注释把方向写反成「恒判超时」）。
+    所以要把戳和**当下的 monotonic** 对一次。
+    """
+    import app.services.fallback_sync_service as fss
+
+    seen: List[Any] = []
+
+    class _Neo4j:
+        is_fallback_mode = True
+
+    svc = fss.FallbackSyncService.__new__(fss.FallbackSyncService)
+    svc._neo4j = _Neo4j()
+
+    real_locked = fss.FallbackSyncService._sync_all_fallbacks_locked
+
+    async def _spy(self):
+        seen.append(
+            {
+                "stamp": getattr(fss, "_sync_all_started_at", "missing"),
+                "locked": fss._sync_all_lock.locked(),
+                "now": time.monotonic(),
+            }
+        )
+        return await real_locked(self)
+
+    monkeypatch.setattr(fss.FallbackSyncService, "_sync_all_fallbacks_locked", _spy)
+    await svc.sync_all_fallbacks()
+
+    assert seen, "spy 没被调到"
+    rec = seen[0]
+    assert isinstance(rec["stamp"], float), f"持锁期间没有打时间戳: {rec['stamp']!r}"
+    assert rec["locked"] is True, "打戳时锁并没有被持有 —— 戳可能打在取锁之前"
+    # 同一口时钟：与当下 monotonic 的差必须是「刚刚」量级。换成 time.time() 会差数十年。
+    assert abs(rec["now"] - rec["stamp"]) < 5.0, (
+        f"时间戳与守卫用的 time.monotonic() 不是同一口时钟: 差 {rec['now'] - rec['stamp']:.0f} s"
+    )
+    assert getattr(fss, "_sync_all_started_at", "missing") is None, "退出后时间戳没清空"
+
+
+async def test_started_at_is_not_stamped_while_waiting_for_the_lock(monkeypatch):
+    """时间戳必须在**取到锁之后**才打（Codex r4 MEDIUM 指出上一条门证不了这件事）。
+
+    上一条门的 spy 跑在 ``_sync_all_fallbacks_locked`` **内部** —— 那时锁必然已经到手，
+    所以「float / locked / 同一口时钟 / 退出清空」四项在「赋值被挪到 ``async with`` **之前**」
+    的实现下**照样全绿**。这条门把前提反过来：先由别人占住锁，再启动调用，
+    正确实现应当在**等锁期间一动不动**。
+
+    这不是吹毛求疵：排队等锁的那段若也算进窗口时长，高并发下第二个等待者会把第一个的
+    时间戳冲掉，守卫读到的就是一个偏早的时刻 ⇒ 提前判超时 ⇒ 提前放行轮转。
+    """
+    import asyncio
+
+    import app.services.fallback_sync_service as fss
+
+    class _Neo4j:
+        is_fallback_mode = True
+
+    svc = fss.FallbackSyncService.__new__(fss.FallbackSyncService)
+    svc._neo4j = _Neo4j()
+
+    SENTINEL = -12345.0
+    monkeypatch.setattr(fss, "_sync_all_started_at", SENTINEL, raising=False)
+
+    async with fss._sync_all_lock:
+        task = asyncio.create_task(svc.sync_all_fallbacks())
+        # 让它真的排到「等锁」这一步上
+        for _ in range(20):
+            await asyncio.sleep(0)
+        await asyncio.sleep(0.05)
+        assert fss._sync_all_started_at == SENTINEL, (
+            f"等锁期间时间戳就被改了 —— 赋值发生在取锁之前: {fss._sync_all_started_at!r}"
+        )
+
+    await task
+    assert fss._sync_all_started_at is None, "退出后时间戳没清空"
+
+
+def test_no_glue_when_probe_fails_on_a_dangling_tail(service, bounded_memory_writes, monkeypatch):
+    """**探测读不出来 + 实际有半行 + 追加成功** 这条组合也不得粘连（Codex r4 MEDIUM）。
+
+    这是「不知道有没有半行」的那一支：探测失败时若按「没有半行」处理（sep 为空），
+    记录就直接接在残缺尾巴后面。正确做法是按「不能确定」处理 —— 加上分隔符再写，
+    代价只是文件可读时会多一个空行（读侧按行解析时跳过）。
+
+    注入：只让该路径的**读**失败（``"b"`` 模式），写照常成功。
+    """
+    import app.core.failed_writes_constants as _fwc
+
+    path = bounded_memory_writes
+    path.write_bytes(b'{"episo')  # 实际有半行，但探测读不出来
+
+    real_open = open
+    probed = []
+
+    def _boom(file, mode="r", *a, **kw):
+        if str(file) == str(path) and "b" in mode:
+            probed.append(1)
+            raise PermissionError("EACCES")
+        return real_open(file, mode, *a, **kw)
+
+    monkeypatch.setattr(_fwc, "open", _boom, raising=False)
+
+    service._pending_failed_writes = [{"episode_id": "blind-glue-A"}]
+    service._flush_pending_failed_writes()
+
+    assert probed, "前置不成立：探测那次读没有被注入失败"
+    raw_lines = [ln for ln in path.read_bytes().decode("utf-8").split("\n") if ln.strip()]
+    parsed = []
+    for ln in raw_lines:
+        try:
+            parsed.append(json.loads(ln))
+        except json.JSONDecodeError:
+            pass
+
+    assert raw_lines[0] == '{"episo', f"探测读不出来时把记录粘在了残缺尾巴上: {raw_lines[0]!r}"
+    assert any(r.get("episode_id") == "blind-glue-A" for r in parsed), (
+        f"记录没有成为一条可解析的行: {path.read_bytes()!r}"
+    )
+
+
+def test_sep_is_dropped_after_a_real_rotation(service, monkeypatch, tmp_path):
+    """补换行失败后若**真的轮转了**，遗留的分隔符不得写进新空文件（Codex r4 LOW）。
+
+    新活动文件是空的，不需要任何分隔符；不清掉的话首段会变成 ``max_lines + 1`` 行
+    （多一个空行），有界的那条不变量就差一行。
+    """
+    import app.core.failed_writes_constants as _fwc
+    import app.services.fallback_sync_service as _fss
+    import app.services.memory_service as _ms
+
+    monkeypatch.setattr(fwc, "FAILED_WRITES_MAX_LINES", 1, raising=False)
+    monkeypatch.setattr(fwc, "FAILED_WRITES_MAX_ROTATIONS", 3, raising=False)
+    path = tmp_path / "failed_writes.jsonl"
+    monkeypatch.setattr(_ms, "FAILED_WRITES_FILE", path)
+    monkeypatch.setattr(_fss, "SYNC_CHECKPOINT_FILE", tmp_path / "sync_checkpoint.json")
+    path.write_bytes(b'{"episo')  # 1 行（按 b"\n" 口径，末行无换行也算一行）⇒ 达到上限 1
+
+    real_open = open
+    failed_once = []
+
+    def _boom(file, mode="r", *a, **kw):
+        # 只让补换行那次追加失败 ⇒ sep 变成 "\n"；随后的轮转与追加照常成功
+        if str(file) == str(path) and "a" in mode and not failed_once:
+            failed_once.append(1)
+            raise OSError("EIO")
+        return real_open(file, mode, *a, **kw)
+
+    monkeypatch.setattr(_fwc, "open", _boom, raising=False)
+
+    service._pending_failed_writes = [{"episode_id": "after-rot-A"}]
+    service._flush_pending_failed_writes()
+
+    assert failed_once, "前置不成立：补换行那次写没有被注入失败"
+    assert _overflow_siblings(path), "前置不成立：没有发生轮转"
+    assert _nlines(path) <= 1, f"轮转后的新文件多了一个空行 —— 首段 {_nlines(path)} 行 > 上限 1: {path.read_bytes()!r}"
+    assert any(r.get("episode_id") == "after-rot-A" for r in _records(path)), "记录没落进新文件"
+
+
+async def test_replay_window_open_keeps_whole_multiline_batch_unrotated(service, bounded_memory_writes, monkeypatch):
+    """窗口开着时，**一次多行**的批次也必须整批落盘且不轮转（车道自审 2026-09-19）。
+
+    覆盖 ``append_failed_writes_bounded`` 的「窗口开着 ⇒ 只追加不轮转」分支里的
+    ``for line in lines`` 循环。既有三条门（含 T6-C 的真锁门）都是一次一行地调
+    ``_record_structured_outbox``，那个循环从没被喂过多行批次 —— 判据只要
+    「行数 == 总数」，一次写一行和一次写 N 行分不出来。
+    """
+    import app.services.fallback_sync_service as fss
+
+    path = bounded_memory_writes
+    total = MAX_LINES + 3
+    monkeypatch.setattr(fwc, "REPLAY_WINDOW_MAX_SECONDS", REPLAY_WINDOW, raising=False)
+
+    async with fss._sync_all_lock:
+        monkeypatch.setattr(fss, "_sync_all_started_at", time.monotonic(), raising=False)
+        # 一次交来 total 条（> 上限），走的是批量路径而不是逐条路径
+        service._pending_failed_writes = [{"episode_id": f"batch-{i}"} for i in range(total)]
+        service._flush_pending_failed_writes()
+
+    assert _overflow_siblings(path) == [], "窗口开着却轮转了 —— finalize 的「只增不减」判据会被打破"
+    assert _identity_union(path, "episode_id") == {f"batch-{i}" for i in range(total)}, "窗口内的多行批次没有整批落盘"
+    assert service._pending_failed_writes == [], "落盘后 pending 没清"
+
+
+async def test_unobservable_replay_state_is_false_even_while_locked(monkeypatch):
+    """观测不到回灌状态时判 False —— 而且要在**锁确实被占着**时验（车道自审 2026-09-19）。
+
+    既有两条常驻门（t6c 的 ``test_replay_probe_falls_back_to_bounded_when_unobservable``
+    与 ``test_unobservable_replay_state_stops_rotation_not_bounding_claim``）靠拦
+    ``builtins.__import__`` 里 ``name == "app.services.fallback_sync_service"`` 来模拟
+    「观测不到」。它们在**锁没被占**的前提下跑，所以守卫无论走哪条分支都返回 False ——
+    一旦生产侧把 import 改成 ``from app.services import fallback_sync_service``
+    （``name`` 变成 ``"app.services"``，拦不住了），那两条门照样绿，只是绿在
+    「锁本来就没被占」这条完全不同的判据上。
+
+    这条门把前提反过来：**先真持锁**（此时正常路径必然返回 True），再断言
+    「观测不到 ⇒ False」。只有拦截真的生效，它才可能绿。
+    """
+    import builtins
+
+    import app.services.fallback_sync_service as fss
+
+    real_import = builtins.__import__
+
+    def _no_fss(name, *a, **kw):
+        if name == "app.services.fallback_sync_service":
+            raise ImportError("simulated")
+        return real_import(name, *a, **kw)
+
+    async with fss._sync_all_lock:
+        assert fss._sync_all_lock.locked(), "前置不成立：锁没拿到"
+        # 不打桩时：锁被占 + 无时间戳 ⇒ True（保守判窗口开着）
+        monkeypatch.setattr(fss, "_sync_all_started_at", None, raising=False)
+        assert fwc._replay_in_flight() is True, "前置不成立：正常路径下应判窗口开着"
+
+        monkeypatch.setattr(builtins, "__import__", _no_fss)
+        assert fwc._replay_in_flight() is False, (
+            "观测不到回灌状态却没判 False —— 生产侧的 import 形式可能已让既有拦截失效"
+        )
+
+
+async def test_replay_guard_logs_error_when_window_times_out(service, bounded_memory_writes, monkeypatch, caplog):
+    """超时分支必须**留下 error 日志**（卡文 (d) 三态规格里写明的那一半）。
+
+    三条守卫门原先只验「返回值导致的轮转行为」，没有一条断言这条 error ——
+    而它是运维唯一能看见「窗口被判挂住」的信号。
+    """
+    import app.services.fallback_sync_service as fss
+
+    monkeypatch.setattr(fwc, "REPLAY_WINDOW_MAX_SECONDS", REPLAY_WINDOW, raising=False)
+
+    with caplog.at_level("ERROR", logger="app.core.failed_writes_constants"):
+        async with fss._sync_all_lock:
+            monkeypatch.setattr(
+                fss,
+                "_sync_all_started_at",
+                time.monotonic() - (fwc.REPLAY_WINDOW_MAX_SECONDS + 5),
+                raising=False,
+            )
+            assert fwc._replay_in_flight() is False
+
+    assert any("[C2-01]" in r.getMessage() for r in caplog.records), (
+        f"超时判定没有留下 [C2-01] error 日志: {[r.getMessage() for r in caplog.records]}"
+    )
+
+
+# ═══════════════════════════════════════════════════════════════════════════
+# (e1) _pending_failed_writes 批次失败即时落盘
+# ═══════════════════════════════════════════════════════════════════════════
+
+
+async def test_batch_failed_writes_hit_disk_before_cleanup(bounded_memory_writes):
+    """改前必红：批次 Neo4j 写失败后条目只留在内存，不调 ``cleanup()`` 就不落盘。
+
+    Neo4j 客户端是**边界替身**（``record_episode`` 抛 RuntimeError）—— 被测对象是
+    刷盘时机与文件 IO，两者全真。
+    """
+    import app.services.memory_service as _ms
+
+    path = bounded_memory_writes
+
+    neo4j = MagicMock()
+    neo4j.initialize = AsyncMock()
+    neo4j.stats = {"initialized": True, "connected": True}
+    neo4j.record_episode = AsyncMock(side_effect=RuntimeError("neo4j down"))
+    neo4j.get_all_recent_episodes = AsyncMock(return_value=[])
+
+    svc = _ms.MemoryService(neo4j_client=neo4j)
+    await svc.initialize()
+
+    result = await svc.record_batch_learning_events(
+        [
+            {
+                "event_type": "color_changed",
+                "timestamp": "2026-01-20T10:00:00Z",
+                "canvas_path": "Math/test.canvas",
+                "node_id": "node_001",
+                "metadata": {"concept": "导数"},
+            }
+        ]
+    )
+
+    episode_ids = result["episode_ids"]
+    assert episode_ids, "前置不成立：批次没有产出 episode_id"
+
+    on_disk = "\n".join(json.dumps(r, ensure_ascii=False) for r in _records(path))
+    assert episode_ids[0] in on_disk, (
+        "未调 cleanup() 前文件里找不到该 episode_id —— 批次失败只攒在内存，进程被 kill 就整批丢失"
+    )
+    assert svc._pending_failed_writes == [], "刷盘后 pending 没清空"
+
+
+def test_flush_keeps_pending_when_disk_write_fails(service, monkeypatch, tmp_path):
+    """磁盘写失败时**不清空** pending —— 请求期一次瞬时 IO 故障不得等于永久丢记录。
+
+    改前是 ``finally: clear()`` 无条件清。在「只有 cleanup() 刷盘」的年代那只是
+    进程退出时的最后一搏；本卡把刷盘提前到每个失败批次之后，无条件清就变成
+    「请求期间盘一抖，这批记录永久消失，cleanup() 兜底也没内容可写」。
+
+    故障是**真的**：把 ``FAILED_WRITES_FILE`` 的父目录指向一个普通文件，
+    ``parent.mkdir(parents=True, exist_ok=True)`` 抛 ``FileExistsError``（OSError 子类）。
+    不打桩被测方法，也不打桩 append helper（DD-03）。
+    """
+    import app.services.memory_service as _ms
+
+    blocker = tmp_path / "blocker"
+    blocker.write_bytes(b"not a directory\n")
+    monkeypatch.setattr(_ms, "FAILED_WRITES_FILE", blocker / "failed_writes.jsonl")
+    monkeypatch.setattr(fwc, "FAILED_WRITES_MAX_LINES", MAX_LINES, raising=False)
+    _isolate_live_checkpoint(monkeypatch, tmp_path)
+
+    service._pending_failed_writes = [{"episode_id": "e1"}, {"episode_id": "e2"}]
+    service._flush_pending_failed_writes()
+
+    assert [e["episode_id"] for e in service._pending_failed_writes] == ["e1", "e2"], (
+        "磁盘写失败后 pending 被清空 —— 这批记录再也没有第二次机会落盘"
+    )
+
+
+def test_flush_drops_unserializable_pending_writes(service, bounded_memory_writes):
+    """序列化失败时**丢弃** —— 它是确定性的，留着只会让 pending 无限增长。
+
+    与上一条成对：两类失败必须分流，任何一边写反都会退化成「丢数据」或「内存泄漏」。
+    """
+    service._pending_failed_writes = [{"episode_id": "e1", "reason": object()}]
+    service._flush_pending_failed_writes()
+
+    assert service._pending_failed_writes == [], "不可序列化的条目被留在 pending ⇒ 每个批次都会重试同一条、列表只增不减"
+
+
+def test_flush_repairs_dangling_tail_before_retry(service, bounded_memory_writes):
+    """半行尾巴不得吞掉重试的记录（Codex r2 HIGH）。
+
+    场景：上一次追加写到一半就抛了 ``OSError``，活动文件以残缺 JSON 结尾。
+    若重试时直接追加，新记录会和残缺尾巴粘成一行 —— 记录被吞掉，而调用方以为
+    「这次成功了」并把它从 pending 里删掉 = **表面重试成功、实则丢失**。
+    """
+    path = bounded_memory_writes
+    path.write_bytes(b'{"episo')  # 上一次写到一半
+
+    service._pending_failed_writes = [{"episode_id": "retried-A"}]
+    service._flush_pending_failed_writes()
+
+    # 按行宽容解析：残缺尾巴本身解析不了（回灌侧同样会跳过它），
+    # 判据是**重试的那条**必须自成一条可解析的行。
+    raw_lines = [ln for ln in path.read_bytes().decode("utf-8").split("\n") if ln.strip()]
+    parsed = []
+    for ln in raw_lines:
+        try:
+            parsed.append(json.loads(ln))
+        except json.JSONDecodeError:
+            pass
+
+    assert raw_lines[0] == '{"episo', f"残缺尾巴没有自成一行 —— 和重试记录粘在一起了: {raw_lines[0]!r}"
+    assert any(r.get("episode_id") == "retried-A" for r in parsed), (
+        f"重试的记录没有成为一条可解析的行 —— 被半行尾巴吞掉了: {path.read_bytes()!r}"
+    )
+    assert service._pending_failed_writes == [], "落盘成功后 pending 没清"
+
+
+def test_flush_keeps_good_entries_when_one_is_unserializable(service, bounded_memory_writes):
+    """混合批次里只丢坏的那条，好条目照常落盘（Codex r2 MEDIUM）。
+
+    改前是一句列表推导：任何一条坏条目都会让整批走进 TypeError 分支被丢掉。
+    """
+    path = bounded_memory_writes
+    service._pending_failed_writes = [
+        {"episode_id": "good-1"},
+        {"episode_id": "bad", "reason": object()},
+        {"episode_id": "good-2"},
+    ]
+    service._flush_pending_failed_writes()
+
+    ids = {r.get("episode_id") for r in _records(path)}
+    assert {"good-1", "good-2"} <= ids, f"好条目跟着坏条目一起被丢了: {ids}"
+    assert "bad" not in ids, "不可序列化的条目不该出现在文件里"
+    assert service._pending_failed_writes == [], "本批应已处理完"
+
+
+def test_flush_does_not_glue_when_boundary_repair_fails(service, bounded_memory_writes, monkeypatch):
+    """补换行那次写**失败**时也不得粘连（车道自审 2026-09-19）。
+
+    ``ensure_line_boundary`` 返回 False 只代表「确认有半行、且补不上」。此时**不能拒写**
+    （agent_service / _record_structured_outbox 没有重试缓冲，拒写 = 直接丢），
+    正确做法是把分隔符并进本次写入的第一行 —— 一次 open 写完，不粘连。
+
+    注入只让**第一次**追加（= 补换行那次）失败，之后的追加照常成功。
+    """
+    import app.core.failed_writes_constants as _fwc
+
+    path = bounded_memory_writes
+    path.write_bytes(b'{"episo')  # 半行尾巴 ⇒ 必然触发补换行
+
+    real_open = open
+    failed_once = []
+
+    def _boom(file, mode="r", *a, **kw):
+        if str(file) == str(path) and "a" in mode and not failed_once:
+            failed_once.append(1)
+            raise OSError("EIO")
+        return real_open(file, mode, *a, **kw)
+
+    monkeypatch.setattr(_fwc, "open", _boom, raising=False)
+
+    service._pending_failed_writes = [{"episode_id": "sep-A"}]
+    service._flush_pending_failed_writes()
+
+    assert failed_once, "前置不成立：补换行那次写没有被注入失败"
+    raw_lines = [ln for ln in path.read_bytes().decode("utf-8").split("\n") if ln.strip()]
+    parsed = []
+    for ln in raw_lines:
+        try:
+            parsed.append(json.loads(ln))
+        except json.JSONDecodeError:
+            pass
+
+    assert raw_lines[0] == '{"episo', f"补换行失败后记录粘在了残缺尾巴上: {raw_lines[0]!r}"
+    assert any(r.get("episode_id") == "sep-A" for r in parsed), f"记录没有成为一条可解析的行: {path.read_bytes()!r}"
+    assert service._pending_failed_writes == [], "已落盘却没清 pending"
+
+
+def test_flush_still_writes_when_boundary_probe_is_unreadable(service, bounded_memory_writes, monkeypatch):
+    """探测**读不出来**时必须照常落盘 —— 「不知道有没有半行」不等于「有半行」。
+
+    活动文件可写但不可读（``chmod 0222`` / ACL / EIO）时 ``ensure_line_boundary`` 的
+    探测恒失败。若把它当作「有半行且补不上」并据此拒写，本方法就会**永远**刷不出去、
+    ``_pending_failed_writes`` 无界增长、连 ``cleanup()`` 也再写不掉 —— 而**改动前**
+    同样的批次是能落盘的（下层 ``rotate_if_over_limit`` / room 计算都刻意吞掉那次读失败）。
+    不能为了防一个假想的粘连，把一条本来能落盘的路径改成永不落盘。
+    """
+    import app.core.failed_writes_constants as _fwc
+
+    path = bounded_memory_writes
+    path.write_bytes(b'{"ok": 1}\n')  # 正常收尾，没有半行
+
+    real_open = open
+    probed = []
+
+    def _boom(file, mode="r", *a, **kw):
+        if str(file) == str(path) and "b" in mode:
+            probed.append(1)
+            raise PermissionError("EACCES")  # 可写不可读
+        return real_open(file, mode, *a, **kw)
+
+    monkeypatch.setattr(_fwc, "open", _boom, raising=False)
+
+    service._pending_failed_writes = [{"episode_id": "probe-blind-A"}]
+    service._flush_pending_failed_writes()
+
+    assert probed, "前置不成立：探测那次读没有被注入失败"
+    ids = {r.get("episode_id") for r in _records(path)}
+    assert "probe-blind-A" in ids, f"探测读不出来就拒写了 —— 这批记录永远刷不出去、pending 会无界增长: {ids}"
+    assert service._pending_failed_writes == [], "已落盘却没清 pending"
+
+
+def test_flush_drops_unencodable_entry_without_raising(service, bounded_memory_writes):
+    """孤立代理这类**编码**失败不得逃出本方法（Codex r3 MEDIUM）。
+
+    ``json.dumps(ensure_ascii=False)`` 对 ``"\\ud800"`` 会成功，真正炸的是写盘那一刻的
+    ``UnicodeEncodeError``（属 ``ValueError`` 不属 ``OSError``）。它若逃出去，
+    ``record_batch_learning_events`` 就从「返回 errors/failed」变成「整个请求抛异常」。
+    """
+    path = bounded_memory_writes
+    # ⚠️ 坏条目必须排在**前面**：排在后面时好条目已经在异常抛出前落了盘，
+    # 「删掉预验」这个负控输入就分不出差别（实测段⑧ SURVIVED 即因此）。
+    service._pending_failed_writes = [
+        # 用 chr() 在运行期造孤立代理：写成源码字面量会让读取/重写这份源文件的工具
+        # （pytest 的断言改写、ruff 等）自己在 UTF-8 编码时炸掉。
+        {"episode_id": "surrogate", "reason": chr(0xD800)},
+        {"episode_id": "ok-1"},
+    ]
+
+    service._flush_pending_failed_writes()  # 不得抛
+
+    ids = {r.get("episode_id") for r in _records(path)}
+    assert "ok-1" in ids, f"好条目没落盘: {ids}"
+    assert "surrogate" not in ids, "不可编码的条目不该出现在文件里"
+    assert service._pending_failed_writes == [], "本批应已处理完"
+
+
+# ═══════════════════════════════════════════════════════════════════════════
+# (e2) 新有界链 —— dead_letter_episodes.jsonl（e3 outbox 子项已退，见验收单）
+# ═══════════════════════════════════════════════════════════════════════════
+
+
+def _episode_task(i: int):
+    import app.services.episode_worker as _ew
+
+    return _ew.EpisodeTask(
+        name=f"batch_learning:concept-{i}",
+        episode_body=f"episode body #{i}",
+        group_id="vault__test",
+        source_description="canvas_batch:test",
+    )
+
+
+def test_dead_letter_episodes_is_bounded(bounded_dead_letter_episodes):
+    """改前必红：``DeadLetterStore.store`` 裸追加 ⇒ 活动文件 8 行、零 overflow。"""
+    import app.services.episode_worker as _ew
+
+    path = bounded_dead_letter_episodes
+    total = MAX_LINES + 3
+    store = _ew.DeadLetterStore(str(path))
+
+    for i in range(total):
+        store.store(_episode_task(i), RuntimeError(f"boom-{i}"))
+
+    assert _nlines(path) <= MAX_LINES, (
+        f"活动文件超行数：{_nlines(path)} > {MAX_LINES} —— dead_letter_episodes.jsonl 仍无界"
+    )
+    assert _overflow_siblings(path), "没有 .overflow.* —— 从未发生轮转"
+    assert len(_identity_union(path, "episode_body_sha256")) == total, "轮转丢了死信条目"
+
+
+# ═══════════════════════════════════════════════════════════════════════════
+# (e4) Path.exists 吞异常残余 3 处 —— 「读不到」不得被压成「不存在」
+#
+# ⚠️ 注入点必须是 ``os.stat``，**不是** ``type(path).stat``（2026-09-18 于本车道
+# Python 3.14.4 实测）：
+#
+#     pathlib.Path.exists()  →  os.path.exists(self)  →  genericpath.exists
+#         →  try: os.stat(path) / except (OSError, ValueError): return False
+#
+# 3.14 的 ``Path.exists()`` **不经过** ``Path.stat()``，所以打桩 ``type(path).stat``
+# 对它完全无效 —— 那样注入的故障改前代码根本看不见，门的红绿都不是它声称的原因
+# （T6-C::test_count_lines_does_not_swallow_permission_error 打 ``type(path).stat``
+# 是对的，因为 ``count_lines`` 调的就是 ``path.stat()``；这里被测的是 ``exists()``，
+# 层不同）。吞异常发生在 ``genericpath.exists`` 的 ``except OSError`` 里。
+# 打 ``os.stat`` 一次即同时喂到改前（``exists()`` → False）与改后
+# （``Path.stat()`` → 上抛）两条路径；``Path.iterdir()`` 用 ``os.scandir``，另打。
+# 一律**不打桩被测函数本身**（DD-03）。
+# ═══════════════════════════════════════════════════════════════════════════
+
+
+def _deny_os_stat(monkeypatch, denied, exc=PermissionError("no access")):
+    """让 ``os.stat`` 对 ``denied(path)`` 为真的路径抛 ``exc``，其余原样放行。"""
+    real_stat = os.stat
+
+    def _stat(path, *a, **kw):
+        if denied(str(path)):
+            raise exc
+        return real_stat(path, *a, **kw)
+
+    monkeypatch.setattr(os, "stat", _stat)
+
+
+def test_overflow_siblings_does_not_swallow_permission_error(monkeypatch, tmp_path):
+    """``overflow_siblings`` 不得把「目录读不到」压成「没有兄弟」。
+
+    压成空列表 ⇒ ``_prune_overflow`` 认为没有可删的档案，retention 静默失效。
+    父目录既 stat 不到也列不出 = 真实的 EACCES 形态（父目录的父目录缺 +x）。
+    """
+    parent = tmp_path / "data"
+    parent.mkdir()
+    path = parent / "failed_writes.jsonl"
+    path.write_bytes(b'{"a":1}\n')
+
+    _deny_os_stat(monkeypatch, lambda p: p == str(parent))
+    real_scandir = os.scandir
+
+    def _scandir(p=".", *a, **kw):
+        if str(p) == str(parent):
+            raise PermissionError("no access")
+        return real_scandir(p, *a, **kw)
+
+    monkeypatch.setattr(os, "scandir", _scandir)
+
+    try:
+        result = fc.overflow_siblings(path)
+    except PermissionError:
+        return
+    raise AssertionError(f"权限错误被吞成了空列表: {result!r}")
+
+
+def test_unique_overflow_target_does_not_swallow_stat_error(monkeypatch, tmp_path):
+    """``_unique_overflow_target`` 不得交出一个「探测不出来」的名字。
+
+    ``Path.rename`` 在 POSIX 下静默覆盖已存在的目标 —— 探测被 PermissionError
+    拦下时若当作「不存在」，轮转就会吃掉整份 overflow。正确反应是换下一个序号。
+    只拦 ``-00`` 那一个候选名：改前 ``exists()`` 把它压成 False 于是照交不误，
+    改后 ``stat()`` 上抛被 ``except OSError: continue`` 接住，换到 ``-01``。
+    """
+    path = tmp_path / "failed_writes.jsonl"
+    path.write_bytes(b'{"a":1}\n')
+
+    # ⚠️ 只能按「序号后缀」精确匹配，不能写 `"-00" in name`（Codex r1 LOW）：
+    # 时间戳是 `%Y-%m-%d-%H%M%S%f`，UTC 0 点（`00xxxx`）时 `-00` 会命中时间戳本身
+    # ⇒ 100 个候选**全部**被注入权限错误 ⇒ 正确实现也拿不到名字 = 门按时刻随机误红。
+    serial_00 = f"-00{path.suffix}"
+
+    def _denied(p: str) -> bool:
+        name = p.rsplit("/", 1)[-1]
+        return fc.OVERFLOW_SUFFIX in name and name.endswith(serial_00)
+
+    _deny_os_stat(monkeypatch, _denied, PermissionError("probe blocked"))
+
+    target = fc._unique_overflow_target(path)
+    assert not target.name.endswith(serial_00), (
+        f"探测被权限错误拦下的名字仍被交了出去: {target.name} —— rename 会静默覆盖它"
+    )
+
+
+def test_dead_letter_store_count_does_not_swallow_permission_error(monkeypatch, tmp_path):
+    """``DeadLetterStore.count`` 不得把「读不到」压成「0 条」。"""
+    import app.services.episode_worker as _ew
+
+    path = tmp_path / "dead_letter_episodes.jsonl"
+    path.write_bytes(b'{"a":1}\n')
+    store = _ew.DeadLetterStore(str(path))
+
+    _deny_os_stat(monkeypatch, lambda p: p == str(path))
+
+    try:
+        result = store.count()
+    except PermissionError:
+        return
+    raise AssertionError(f"权限错误被吞成了行数: {result!r}")
+
+
+# ═══════════════════════════════════════════════════════════════════════════
+# 常驻硬边界门（文件本地 AST）—— 新增测试忘了隔离现网文件就当场红
+# ═══════════════════════════════════════════════════════════════════════════
+
+#: 触到这些名字 = 会走到 failed_writes 链（轮转前置动作会删/改现网 checkpoint）
+_FAILED_WRITES_CHAIN = {
+    "_record_failed_write",
+    "_record_structured_outbox",
+    "_flush_pending_failed_writes",
+    "append_failed_writes_bounded",
+    "record_batch_learning_events",
+}
+_OUTBOX_CHAIN = {"_write_outbox"}
+_DEAD_LETTER_CHAIN = {"DeadLetterStore"}
+
+#: fixture / helper 名 → 它已经替调用方隔离掉的东西
+_ISOLATORS = {
+    "bounded_agent_writes": {"FAILED_WRITES_FILE", "SYNC_CHECKPOINT_FILE", "tmp_path"},
+    "bounded_memory_writes": {"FAILED_WRITES_FILE", "SYNC_CHECKPOINT_FILE", "tmp_path"},
+    "bounded_dead_letter_episodes": {"SYNC_CHECKPOINT_FILE", "tmp_path"},
+    "_isolate_live_checkpoint": {"SYNC_CHECKPOINT_FILE"},
+}
+
+
+def _iter_test_defs(tree):
+    """产出 (函数节点, 展示名)：模块级 ``test_*`` **与** ``Test*`` 类里的方法。
+
+    ⚠️ 必须连类方法一起扫（Codex r1 MEDIUM）：``pytest.ini`` 的
+    ``python_classes = Test*`` 意味着类里的 ``test_*`` 方法同样会被收集执行，
+    只扫模块级 = 把「写进类里」变成一条**门未覆盖的路径**。
+    """
+
+    def _walk(body, prefix: str):
+        for node in body:
+            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
+                if node.name.startswith("test_"):
+                    yield node, f"{prefix}{node.name}"
+            elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
+                # ⚠️ 递归，不是只看一层（Codex r2 MEDIUM）：``TestOuter.TestInner`` 这种
+                # 嵌套类里的 ``test_*`` 同样会被 pytest 收集，只扫一层 = 留一条门未覆盖的路径。
+                yield from _walk(node.body, f"{prefix}{node.name}::")
+
+    yield from _walk(tree.body, "")
+
+
+def _isolation_offenders(src: str) -> List[str]:
+    """扫一份测试源码，返回「碰了现网链却没隔离」的 ``test_`` 函数名。
+
+    ⚠️ 「碰了什么」只数 **Name / Attribute 标识符**，不数字符串字面量 ——
+    否则本函数自己的这几个名单常量（纯字符串）会把自己判成违规，门就得靠
+    「恰好也提到 SYNC_CHECKPOINT_FILE」这种巧合豁免自己（不可靠）。
+    「有没有隔离」则必须连字符串字面量一起看：``monkeypatch.setattr(m, "X", …)``
+    里的 X 本来就是字符串。
+
+    ⚠️ **这是名字层的必要条件，不是充分条件**（Codex r1 MEDIUM，如实登记）：
+    它只能证明「该出现的隔离名字出现了」，证明不了路径**真的**指向了 ``tmp_path``。
+    例如 ``def test_x(tmp_path): DeadLetterStore().store(...)``（拿了 tmp_path 却
+    没把它传给被测对象）本门放行；经 fixture / helper 间接写入同样看不出来。
+    ⚠️ 兜底也**不能**用 ``git status --porcelain backend/data/``（Codex r2 更正初版
+    这句失实）：``backend/data/.gitignore`` 的 ``*.jsonl`` 把这些文件连同
+    ``*.overflow.*.jsonl`` 一起忽略，普通 status 根本看不见它们被写过。
+    真正能看见的兜底是对 ``backend/data/`` 做**跑前 / 跑后 sha256 快照**逐行比对
+    （见本卡验收单 (m)）。本门的作用是把「整类忘记」在写的时候就挡住，不替代那道兜底。
+    """
+    offenders: List[str] = []
+    for node, label in _iter_test_defs(ast.parse(src)):
+        identifiers: Set[str] = set()
+        literals: Set[str] = set()
+        for sub in ast.walk(node):
+            if isinstance(sub, ast.Name):
+                identifiers.add(sub.id)
+            elif isinstance(sub, ast.Attribute):
+                identifiers.add(sub.attr)
+            elif isinstance(sub, ast.Constant) and isinstance(sub.value, str):
+                literals.add(sub.value)
+
+        args = {a.arg for a in node.args.args}
+        evidence = literals | identifiers | args
+        for name in args | identifiers:
+            evidence |= _ISOLATORS.get(name, set())
+
+        required: Set[str] = set()
+        if identifiers & _FAILED_WRITES_CHAIN:
+            required |= {"FAILED_WRITES_FILE", "SYNC_CHECKPOINT_FILE"}
+        if identifiers & _OUTBOX_CHAIN:
+            required |= {"OUTBOX_FILE"}
+        if identifiers & _DEAD_LETTER_CHAIN:
+            required |= {"tmp_path"}
+
+        missing = sorted(required - evidence)
+        if missing:
+            offenders.append(f"{label} (:{node.lineno}) 缺 {missing}")
+    return offenders
+
+
+def test_every_staging_test_isolates_live_files():
+    """⛔ 常驻硬边界门：本文件里任何碰到落盘链的测试都必须把路径指向 tmp_path。
+
+    逐条等审查告诉我「这条忘了隔离」是不可收敛的（T6-C 被 Codex 两轮各抓一条
+    同型漏网）—— 把规则本身钉成 AST 门，新增测试忘了隔离就当场红。
+    """
+    src = pathlib.Path(__file__).read_text(encoding="utf-8")
+    offenders = _isolation_offenders(src)
+    assert not offenders, "这些测试会碰到现网落盘链却没隔离：\n  " + "\n  ".join(offenders)
+
+
+def test_isolation_scanner_can_actually_detect_an_offender():
+    """验伪锚：上面那条扫描器必须真能抓到人，否则它是个恒绿的摆设。
+
+    三类各喂一段「碰了链但没隔离」的源码，再喂一段合规的 —— 前三段必须命中、
+    第四段必须放行。只验「扫出 0 个」的门自己永远绿。
+    """
+    bad_failed_writes = "def test_x(service):\n    service._record_structured_outbox({'a': 1})\n"
+    bad_outbox = "def test_y(bus):\n    bus._write_outbox(e, 'h', 'r')\n"
+    bad_dead_letter = "def test_z():\n    store = DeadLetterStore('/live/dl.jsonl')\n"
+    bad_in_class = (
+        "class TestSomething:\n    def test_m(self, service):\n        service._record_structured_outbox({'a': 1})\n"
+    )
+    good = "def test_ok(bounded_memory_writes, service):\n    service._record_structured_outbox({'a': 1})\n"
+
+    assert _isolation_offenders(bad_failed_writes), "扫描器漏掉了 failed_writes 链的违规"
+    assert _isolation_offenders(bad_outbox), "扫描器漏掉了 outbox 链的违规"
+    assert _isolation_offenders(bad_dead_letter), "扫描器漏掉了 dead-letter 链的违规"
+    assert _isolation_offenders(bad_in_class), "扫描器漏掉了 Test* 类方法里的违规"
+    bad_nested = (
+        "class TestOuter:\n"
+        "    class TestInner:\n"
+        "        def test_n(self, service):\n"
+        "            service._record_structured_outbox({'a': 1})\n"
+    )
+    assert _isolation_offenders(bad_nested), "扫描器漏掉了嵌套 Test* 类里的违规"
+    assert _isolation_offenders(good) == [], "扫描器把合规用例误判成违规"

=== 附录A 结束 ===
