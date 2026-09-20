> 批次: BATCH-2026-09-18-第十五批 · 车道 P4 · 卡 CARD-CARD-STATES-ATOMIC-WRITE · **代 Codex round-5 的功能**
> 审查者: **Claude 独立 agent（全新上下文，无本卡历史）** —— ⛔ **不是 Codex，不冒充 Codex 判定**
> 依据: 项目 `CLAUDE.md` 铁律 #3「代码审查必须独立 Agent —— 记录 `[Code-Review]`」；
>       Codex 末轮因鉴权失效未能取得（见 `codex-review-CARD-CARD-STATES-ATOMIC-WRITE-r5.md`），
>       协议对「再 0 字节」的兜底口径是主 session 人审替代，本报告供其裁定。
> 审查绑定: 代码树等同 `d317b2ee7dd6cad8b68da913642d78cdd25a9e5d`
>       （审查者自核：`git diff --stat d317b2ee HEAD -- . ':(exclude)_bmad-output'` = 空）
> 读取面: 与 `prompts/codex-prompt-CARD-CARD-STATES-ATOMIC-WRITE-r5.md` 同（只读，未连库，未跑写盘命令）
> 判定: **BLOCKER=0 HIGH=0 MEDIUM=3 LOW=5**（只计本轮新发现：`B0 H0 M1 L5`）

---

## 审查者自核的绑定（不采信作者自述）

| 判据 | 实测 |
|---|---|
| `git diff --stat 5d69728a HEAD -- backend/app/services/review_service.py` | **空** ⇒ 生产代码与 r4 所审逐字节相同 |
| `git diff --stat 5d69728a HEAD -- . ':(exclude)_bmad-output'` | 2 文件（测试 +115/−56、spec） |
| `git diff --stat 9c4e7e82 HEAD -- . ':(exclude)_bmad-output'` | **恰 3 文件**，1 个 commit |
| r4 SHA 与 HEAD 关系 | `merge-base --is-ancestor` = **否**：`5d69728a` 是被 amend 掉的兄弟 commit，父同为 `9c4e7e82`；diff 对照仍有效 |
| 存档自证 | r5 系列存档记 `HEAD=d317b2ee`，其 `review_service.py sha256=14018aa4…` / `test_g3_7…=ff24999b…` 与当前工作树实测**逐字相同** |
| AST 测试集合比对（r4 → HEAD） | 35 → 37，**REMOVED=[]**，ADDED = 恰那两条新门 ⇒ 本轮**没有静默删掉任何测试** |
| `pyright app` | `0 errors, 80 warnings` |
| 工作树 | `git status --porcelain` 空 |

## 逐条发现

### MEDIUM-1（本轮新增）· 门未覆盖的路径：`seq` 取号移出 asyncio 锁
`review_service.py:1033,1059` · 门 `test_g3_7_truth_source.py:1348`

把 `seq = next(_card_states_seq)`（:1059）从 `async with _card_states_lock:`（:1033）内提到方法首行，
`args[2]` 仍是 int、两次**顺序**调用的 seq 仍严格递增 ⇒ `…s7_seq_is_allocated_before_dispatch` 全绿；
`…stale_publish_is_discarded` 手工取号、不经生产调用方，也绿。行为却坏了：A 取 seq=1 后阻塞在
asyncio 锁 → B 取 seq=2 先进锁并发布 → A 随后带着**更全**的快照（同一容器，含 A+B 两份 mutation）
以 seq=1 进 helper ⇒ 被判过期丢弃，且返回 `True`。当前代码把取号放在 `json.dumps` **之后**、锁
**之内**，seq 单调性与快照新旧严格同向——这个不变量没有任何门钉住。

这是 r4 MEDIUM-1 家族里**未被本轮关掉的第四个变体**（r4 点名的 lambda / 记账 / 同步直调三项已关闭）。
**未证实**：只读判断，未跑该负控输入。
建议（登记，不阻断）：在门里加一条「取号点在锁内、且在 `json.dumps` 之后」的 AST 结构断言。

### MEDIUM-2 · r4 MEDIUM-3 仍成立、已登记 · 线程池饥饿
`review_service.py:722,1060`。过期判断（:723）在阻塞式 `Lock.acquire()` **之后**，取消不能提前释放
等待锁的 worker。按边界不评修法。登记见验收单 §五.3 / §六.10。

### MEDIUM-3 · r4 MEDIUM-4 仍成立、已登记 · `spec.md:78` 与实现失真
「On a successful replace the method MUST clear …」——目录 fsync / `unlink` 失败时 replace 其实已成功，
实现却返回 `False` 且不 `clear()`。两条门已把该失真做成可观测。该段落在卡文锁死区间，只指出失真。

### LOW-1 · 负控 4 的 KILLED 落在 `errors == []`，不是声称的重叠检测
`test_g3_7_truth_source.py:1233` vs `:1236`

`negctl-r5-4`（拆线程锁 → `nullcontext`）实际失败正文是
`AssertionError: 串行落盘不得抛异常，实得 [('t0', "FileNotFoundError(2, …)"), …]` ——
`errors` 先红，`overlaps` **根本没被求值**（拆锁后线程必然先因 tmp 被别人 replace 走而抛
`FileNotFoundError`）。因此该门 docstring 那句「重叠检测直接测的就是互斥本身」**未证实**。
护栏本身不空（`entered`/`errors` 确实绑住了拆锁），但承重的是另一条判据。
建议（登记）：把 `overlaps` 的断言排在 `errors` 之前，或补一个「互斥失效但 I/O 不冲突」的负控输入。

### LOW-2 · 负控 11 的 KILLED 落在 `FileNotFoundError`，不是水位断言
`test_g3_7_truth_source.py:1310`（读取点 `:1339`）

该门不预置目标文件：大 seq 发布在 replace 处失败 ⇒ 文件从未创建，小 seq 又被误丢 ⇒
`target.read_text()` 直接抛。门红了、变异被杀，但它**分不清「被误丢」与「根本没写」**。
建议（登记）：跑前先给 `target` 写一份已知内容。

### LOW-3 · r4 LOW-6（全局水位未绑定目标文件）既未修，也未登记
`review_service.py:678,723`。验收单全文对该条 **0 命中**；§五.12 登记的是多实例容器缺口，
§六.12 登记的是「新调用方须自己取号」，都不是它。协议对 LOW 是登记不阻断，但这一条连登记都没有。

### LOW-4 · 验收单内部数字互相矛盾，且与命令输出不一致
`:131`「14 条门（21 → 35 test）」与 §六.7「7 Scenario / 14 门」**错**（实测 16 门 / 37 test）；
§五.10「『同步直调』只由 AST 门覆盖，14 条行为门里没有一条」**已被 `negctl-r5-10` 推翻**
（该存档失败正文正是派发门的断言）。该条后半句「没有一条检查事件循环是否被阻塞」仍成立。

### LOW-5 · spec 改后仍有两处超出实现
- `:166`「and no `.json.tmp` is left behind」：丢弃分支在 `:723` 于 try/finally **之前** `return`，
  **不清理任何既有 tmp**。只在「本次不产生」的意义上成立，与 `:21-26` 刚被 r4 LOW-5 改精确的
  「attempt vs guarantee」口径不一致。
- `:44`「the call therefore still reports success」：丢弃**只在派发协程被取消时可达**，而被取消的
  协程抛 `CancelledError`、永不 `return True` ⇒ 这句描述的返回值**没有任何调用方能观测到**。

## 对六个问题的回答（摘要）

0. **没有削弱任何门**。AST 集合比对证明零删除。`_TrackingLock` 的加锁/记账顺序使记录区间 **⊆**
   真实持有区间 ⇒ **只会漏判、不会误判**；配 50 ms 窗口，漏判实践上不可能。`entered == 4`
   **确定性**（过期丢弃的 `return` 在锁**内**，照样触发 `__exit__`）。旧锚顺带证明的「tmp 真被写过」
   已由 S1 接住，不是缺口。但见 LOW-1。
1. 有一条门未覆盖的路径 = MEDIUM-1；另 LOW-2 是水位门的失败归因不精确。
   常量 seq 被 `seqs[0] < seqs[1]` 挡住、`next()` 挪进 helper 被 stale 门挡住。
2. **十段负控各只拆一层**（逐份读 `*-mutant-diff-*` 确认单一语义层），每段只让声称的那条门红
   （1→4 条残留族、2→3 条、其余各 1 条），与 16 条总数自洽；十段 `sha-before`/`sha-after`
   **全部等于 `14018aa4…`**，还原逐字节干净。缺口：负控 3 不在 r5 集（只存在于 r2）；
   未被拦下的输入 = MEDIUM-1。
3. 仍超出实现的两处 = LOW-5；另 `:78` 那句（MEDIUM-3）。其余各段与实现相符。
4. 对照输入 = **5 绿 + 8 行为红 + 3 接口错误**。接口错误三条（并发门 / stale 门 / 水位门）
   在对照输入下**确实没有绑住行为**，只证明符号存在；其行为绑定来自负控 4 / 7·8 / 11，
   而其中两条又落在非声称断言上（LOW-1 / LOW-2）⇒ 这三条门的绑定链**比另外 8 条弱一档**，属实。
5. **unit 新红归因成立**。四条独立佐证：① `diff r5.nodeids r5b.nodeids` 恰一行 `<`，无 `>`；
   ② 失败正文是 `npm run build 超时（墙钟上限 5s）`，断言是 `_npm_was_invoked(pids)`；
   ③ `grep -c -E "review_service|card_states|fsrs"` 对该测试文件与 `scripts/deploy-vault.sh`
   **都 = 0**；④ 墙钟佐证负载：unit-r5 2639 s vs unit-r5b 1106 s（2.4×）。
   **没有任何证据指向本卡三文件。**
6. **可以收官**。BLOCKER=0 且 HIGH=0，**没有必须在本卡内解决的条目**。r4 的 MEDIUM-1（三子项）、
   MEDIUM-2、LOW-5、LOW-7 逐条验证**确已关闭**；其余按协议登记不阻断。

## 审查者另指出（影响轮次记账）

`codex-review-CARD-CARD-STATES-ATOMIC-WRITE-r5.md` 称「两次尝试…另一 request id」，但
`.stderr` 里 `grep -oE "request id: req_[a-f0-9]+" | sort -u` **只有 1 个**——第二次的 stderr
被 `2>` 覆盖了，「两次」这一点在**存档内不可自证**。已按此更正该存档。

`BLOCKER=0 HIGH=0 MEDIUM=3 LOW=5`
