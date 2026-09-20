# 独立复核 round-4：CARD-CARD-STATES-ATOMIC-WRITE（BATCH-2026-09-18-第十五批 / 车道 P4）

## ① 背景与最小读取面

r1: B0/H1/M3/L1 → r2: B0/H1/M5/L0 → r3: B0/H1/M3/L1。本轮针对 r3 的 HIGH
（「被取消的旧快照可以晚于新快照发布」）整改。**本卡轮次上限 5**，请务必把仍然成立的
问题一次列全，并明确区分「本卡引入」与「既有/超出本卡地盘」。

只读：

1. 全量 diff：`git --no-pager diff --no-color 9c4e7e82 5d69728a1c7964e9f8e09f0c908b59e5fca7ac2a -- . ':(exclude)_bmad-output'`（恰 3 文件）
2. 相对 r3 的增量：`git --no-pager diff --no-color b173eb4480d8ca00b98474d576c3c4c723fe32b3 5d69728a1c7964e9f8e09f0c908b59e5fca7ac2a -- . ':(exclude)_bmad-output'`
3. `backend/app/services/review_service.py`：`:58-72`（import 段）、`:655-745`
   （`_card_states_file_lock` / `_card_states_seq` / `_card_states_published_seq` /
   `_persist_card_states_bytes`）、`:995-1085`（`_save_card_states` 全貌与两个异常分支）
4. `openspec/specs/concept-identity/spec.md` 改后全文（7 个 Scenario）
5. `backend/tests/regression/test_g3_7_truth_source.py`：`:74-135`（既有 fixtures）与
   `:685` 到文件末尾（本卡新增段，14 个 `concept_identity` 门）
6. 本轮裁判存档（`_bmad-output/审查/evidence-card-states-atomic/`）：
   - `negctl-final-{1,2,4,5,6,7,8}-*` —— 七段负控输入（含 `-sha-before/-after` 与 `-mutant-diff-`）
   - `suites-v2-*.txt` / `dir-regression-v2-*.txt` / `unit-v2-*.txt` —— 绑本 HEAD 的目录级，
     首部含 **完整 argv** + 跑前两源码 sha256，末尾含收工时刻 + 收工两源码 sha256
   - `redbind-v2-*.txt` —— 把实现整体换回 `9c4e7e82` 形态的对照输入
   - `ast-v2-*.txt`（含对 base 副本的验伪锚）/ `pyright-v2-*.txt` / `territory-ruff-v2-*.txt`
   - `probe-cancel-thread-*.txt` —— 取消/线程前提实测
   - ⛔ `unit-r2-*.txt` 首部已标注**作废**（跑期间源码被改，已中止），勿采信

## ② 本轮整改自述（请独立核对）

1. **r3 HIGH 已修**：`_card_states_seq = itertools.count(1)`（模块级）；`_save_card_states`
   在**派发线程之前**取 `seq = next(_card_states_seq)`；helper 持 `_card_states_file_lock` 后
   先判 `if seq <= _card_states_published_seq: return`（过期写直接丢弃），`os.replace` 成功后
   才 `_card_states_published_seq = seq`。理由：每次写的都是**全量快照**，更新的那份天然
   包含本次内容，因此丢弃不丢数据、返回成功是诚实的。
2. **新增门** `…s6_stale_publish_is_discarded`：先用较大 seq 发布，再用较小 seq 尝试发布 ⇒
   目标不变、无 tmp；末尾带**探针存活锚**（更大的 seq 必须真的落盘）。负控输入
   `negctl-final-7`（拆守卫）与 `-8`（不记录已发布 seq）各让它且只让它变红。
3. **r3 MEDIUM-3 已补两处**：并发门的临界区从「replace 返回」延到 **`finally` 的 unlink 返回**
   （改 patch `pathlib.Path.unlink` 做 drain 点）；终态文档断言从 `keys() <= {...}` 收紧为
   **「恰好一个键且属于四者之一」**。另新增 `…s6_cleanup_failure_is_normalized_not_swallowed`
   （`unlink` 抛 `OSError` ⇒ 归一为 `False` + 脏标记；目标其实已是新快照，如实断言）。
4. **r3 MEDIUM-5（存档缺完整命令/绑定）已补**：三份目录级存档首部含完整 argv 与跑前 sha256，
   末尾含收工 sha256；`pyright-v2` / `territory-ruff-v2` / `ast-v2` 均带 HEAD + 命令。
5. **r3 MEDIUM-2（线程池饥饿）未修，登记**：持锁线程卡在慢 I/O 时，后续被取消的 worker 仍会
   阻塞在 `Lock.acquire()`。本卡不改线程池配置（不在地盘），已写进验收单「本卡未证明什么」。
6. **r3 MEDIUM-4（spec「successful replace 必须 clear」失真）未改，登记**：该句落在卡文规定的
   **一字不动**区间（原 `:34-57`，T4-C 收窄结论），本卡无权改动；已由目录 fsync 门做成可观测。
7. **仍未做（卡文硬边界）**：不换随机 tmp 名、不加跨进程锁 ⇒ 跨进程/多 worker 不在保护范围。
8. **如实声明一处判据耦合**：并发门的 drain 点是 `unlink`，所以负控输入 `negctl-final-1`
   （拆掉清理动作）也会让并发门变红（`active` 永不排空）。它不是「并发真的坏了」，
   而是该门与清理动作存在结构耦合。

## ③ 请按重要性回答

0. 过期写丢弃是否**真的**消除了 lost update？还有没有**未被拦下的输入**能让一份较旧的
   全量快照最终留在盘上？`seq` 在 `_card_states_lock` 内取号、在线程内比较，这个
   happens-before 关系是否成立？`_card_states_published_seq` 的读写是否都在锁内？
1. 「丢弃过期写但仍返回成功」这个语义是否在所有路径上都成立？有没有一种情形，更新的
   那份快照**不包含**被丢弃那次的内容（例如回滚、pop、或两个 ReviewService 实例）？
2. 模块级 `_card_states_published_seq` 跨测试/跨事件循环单调递增，会不会在某条路径上
   让**本该发布**的写被误丢（假阴性）？
3. 七段负控输入是否各只拆一层？有没有**门未覆盖的路径**：某个变异体能让 14 条全绿？
   （r3 你指出的两个：给 unlink 加 `except OSError: pass`、把 `to_thread` 换成同步直调——
   前者现在有 `…cleanup_failure…` 门，后者仍只由 AST 门覆盖，请确认。）
4. spec 改后的 Requirement 有没有仍然超出实现的承诺？请逐句对照。
5. 14 条门里哪几条在**对照输入**（整体换回 `9c4e7e82`）下仍绿、哪几条因签名变化而
   报错而非行为红？后者是否应当被视为「没有绑住行为」？
6. 存档现在能否闭合「三个目录级确实在本 HEAD 上跑完且跑期间源码未变」？还缺什么？

## ④ 输出格式

逐条列 `BLOCKER / HIGH / MEDIUM / LOW`，每条给 `file:line` + 一句复现思路。
措辞统一用「负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径」。
最后给一行：`BLOCKER=n HIGH=n MEDIUM=n LOW=n`。

## ⑤ 边界

只读，不写任何文件；不连数据库；不评 `next_review` 迁移（P4-B）；不评
`backend/app/utils/atomic_io.py` 该怎么修；不评 `tests/unit` 的隔离问题；不评
`backend/app/models/**`；不评那段被卡文锁死的 spec 文字**该不该**改（只可指出其失真）；
不评线程池/worker 配置该怎么改（不在本卡地盘）。
