# 内部对抗性复核（Workflow）— CARD-NEO4J-REPLAY-BOUND

> **这不是 Codex 轮次，不计入卡族轮次配额。** 协议 §五.5 要求「不入库的复核不作依据」，
> 故把该次复核的完整结论落盘，供主 session 复核时逐条对照。
>
> - 形态：5 个维度并行找缺陷（concurrency / data-loss / endpoint / gate-strength /
>   config-and-compat）→ 每条发现由 3 个不同镜头（correctness / exploitability /
>   reproducibility）**独立尝试证伪** → 多数证伪则判死。
> - **审查绑定：`47075cbe`**（= Codex round-1 审的同一版）。
> - ⚠️ **审查对象在复核期间未冻结**：主 session 在它运行时已经在收口 Codex round-1 的意见。
>   所以下列每条都必须对**当前 HEAD**（`b8cd3a82`）复核后才能采信，不能照搬。
> - ⚠️ **验证覆盖不完整**：26 个 verify agent 因 API/证书错误未跑成（另有 1 个 parallel
>   分支 stall），部分发现票数少于 3（下表 votes 列如实标注）；1 票的证据强度弱于 3 票。
> - 规模：119 agents（93 完成 / 26 报错），1821 次工具调用，约 71 分钟。

## 计数

总发现 **38** 条；存活 **20**、被证伪 **18**。

存活分级：BLOCKER **1** / HIGH **5** / MEDIUM **10** / LOW **4**。

## 存活发现（逐条原文）

### 1. [BLOCKER] 轮转让 failed_writes.jsonl 在回灌窗口内「变短」，_sync_failed_writes 的 finalize 因此把窗口内新追加的条目整份抹掉

- 维度 `data-loss` · 位置 `failed_writes_constants.py:76` · 独立证伪票数 **2**

本卡第一次让 `failed_writes.jsonl` 会在写侧**缩短**。而它的唯一回灌方 `fallback_sync_service._sync_failed_writes`（本卡未改）检测「回灌期间有没有新追加」用的是**长度比较 + 位置切片**：

  fallback_sync_service.py:365-366  `if len(current_lines) > len(lines): new_lines = current_lines[len(lines):]`

该判据只在「文件单调增长、前 len(lines) 行仍是那份快照」时成立。回灌链的锁窗是：283-289 持锁读快照 → 323-353 **不持锁**逐条 await 重放 → 357 重新持锁 finalize。在 323-353 这个窗口里，`_record_structured_outbox`（memory_service.py:515-518）/`_flush_pending_failed_writes`（:2872-2878）拿到 `failed_writes_lock` 后经本行 `rotate_if_over_limit` 轮转：活动文件被 rename 成 `.overflow.<ts>`，新建的活动文件只剩刚写的 k 条。

finalize 于是看到 `len(current_lines)=k < len(lines)=N` ⇒ `new_lines=[]` ⇒ `merged = still_pending`：
- merged 非空 → :416 `_atomic_write_file` 整份覆盖，**窗口内新写的 k 条被销毁**；
- merged 为空（本轮全部重放成功）→ :421 `_rotate_file` 把这 k 条从未重放的条目改名成 `failed_writes.synced.<ts>`（= 语义上「已回灌」），随后被 `_cleanup_old_synced_files` 按 30 天 retention 删除 —— **静默永久丢失**。

触发门槛很低，不是理论race：回灌开始时文件若已达 `FAILED_WRITES_MAX_LINES`（正是「回灌慢 ⇒ 窗口长」的那种情形，默认 10000），窗口内**第一次**经本函数的追加就必然触发轮转（rotate 的判据是 `count_lines(path) >= max_lines`，而回灌期间文件一直保持整份快照）。

另有一个更隐蔽的变体：若窗口内追加条数 k > N，则 `current_lines[N:]` 按一个已不存在的公共前缀切片，**丢掉前 N 条新条目、保留后面的**，且不报任何错。

注：`rotate_if_over_limit` 的 docstring（failure_counters.py:168-170）只声明了「被轮转走的条目没有回灌方」，**没有**声明轮转会破坏回灌侧的 append 检测、进而毁掉**留在活动文件里**的条目。这一条与 worktree 里的 round-1 整改无关，整改后仍在。

**观察方式**：对照输入：`CLS_FAILED_WRITES_MAX_LINES=3`，预置 failed_writes.jsonl 3 条 → 起 `_sync_failed_writes`，在其 await 窗口内调一次 `_record_structured_outbox({...})`（会轮转 + 写 1 条）→ finalize 后 `failed_writes.jsonl` 里查不到那条新条目，且 `.overflow.*` 里也没有它；若本轮 3 条全部重放成功，该条目还会以 `failed_writes.synced.<ts>` 的名字存在（= 谎称已回灌）。把 MAX_LINES 提到 4（不触发轮转）则同一条目原样保留 —— 断言翻转的唯一变量就是本行的轮转。

### 2. [HIGH] 写侧轮转打破回灌 finalize 的「文件只增不减」前提 ⇒ 重放窗口内新追加的条目被静默覆盖

- 维度 `concurrency` · 位置 `failed_writes_constants.py:76` · 独立证伪票数 **3**

`_sync_failed_writes` (backend/app/services/fallback_sync_service.py:283-417) 的协议是：持 `failed_writes_lock` 快照 `lines` → 放锁 → 逐条 `await _replay_scoring_entry_to_neo4j` → 再持锁 finalize，用 `if len(current_lines) > len(lines): new_lines = current_lines[len(lines):]`（:355-360）检测「重放期间有没有新追加」，把新条目并进 `merged` 保住。这条检测的前提是**活动文件在窗口内只会变长**。本卡把 `rotate_if_over_limit` 接进 `append_failed_writes_bounded`（本行）后，窗口内的任意一次追加都可能把活动文件整体 rename 走并新建一个近乎空的文件，`len(current_lines) < len(lines)`，检测恒假 ⇒ `merged = still_pending`，随后 `_atomic_write_file`(:415) 无条件覆盖，或 `merged` 为空时 `_rotate_file`(:418) 把它改名成 `.synced.<ts>`（= 谎称已回灌，30 天 retention 后删）。锁本身没写错——两端都正确持锁；错的是锁盖不住中间的 await 窗口，而这个窗口原先靠「只增不减」补住，本卡把它拆了。触发不需要多线程：`_record_structured_outbox`(memory_service.py:502→518) 由 async 的 `record_knowledge_entity`(:1666) 调用，在同一事件循环的 await 点即可插进来；`_flush_pending_failed_writes`(:2872) 同理。两个新增测试文件里**没有任何并发/重放交叉用例**，作者自述的「对进程内并发写者原子」这条关键约束零门覆盖。`rotate_if_over_limit` 的 docstring(failure_counters.py:168-170) 只声明了「被轮转走的条目没有回灌方」，**没有**声明轮转会让回灌侧覆盖掉未重放的新条目——这是另一件事。

**观察方式**：对照输入：活动文件已达 FAILED_WRITES_MAX_LINES（默认 10000，正是本卡针对的 Neo4j 长期离线场景）时调用 `/traces/replay-fallbacks`；重放 await 期间任一次 `_record_structured_outbox` 触发轮转（count_lines==10000，`10000 < 10000` 为假 ⇒ 立即 rename）并写入 1 条新条目。finalize 处 `len(current_lines)=1 > len(lines)=10000` 翻为 False，fallback_sync_service.py:358 的「保住并发追加」断言失效，:415 覆盖掉那条从未重放的记录（still_pending 为空时走 :418 改名 `.synced.`，更坏）。改前同一交错下该条目会被 `new_lines` 接住。

### 3. [HIGH] 把「死信坟场」的保留策略套到 failed_writes.jsonl 这条**有回灌方**的 outbox 上，轮转即等于把待回灌写入移出唯一重放路径并最终删除

- 维度 `data-loss` · 位置 `failed_writes_constants.py:28` · 独立证伪票数 **1**

卡文与 `rotate_if_over_limit` 的 docstring 把三个 JSONL 一视同仁当「死信坟场」。但三者语义不同：
- `failed_edge_syncs.jsonl` / `failed_dual_writes.jsonl` 确实只供事后分析（`scripts/generate_regression_tests.py` 只读）；
- `failed_writes.jsonl` 是 **outbox**，`memory_service._record_structured_outbox` 的 docstring 写明「条目带 kind='knowledge_entity' 判别符, recover_failed_writes 据此重放」，T6-B 刚给它接上 `_sync_failed_writes` + `/traces/replay-fallbacks`，端点文案自己说「entries are removed from their file once replayed」。

对这条链，轮转不是「归档旧日志」，而是把**尚未写进 Neo4j 的用户学习写入**搬到一个谁都不会读的文件里（`fallback_sync_service` 全文无 glob，只读 `FAILED_WRITES_FILE`），再由 `_prune_overflow` 在第 MAX_ROTATIONS+1 次轮转时删掉。默认值下 = 满 10000 条搬走一次，搬走 5 次后最早那批 10000 条用户写入**永久消失**，且 Neo4j 恢复后也再也回灌不回来。

这一点在 failure_counters.py:168-170 的 docstring 里被写成「这是『有界』换来的代价，不是缺陷」，但该判断建立在「死信文件 = 只供事后分析」的前提上，对 failed_writes 不成立。新增的 `/traces/dead-letter-backlog` 报了 `overflow_files`/`overflow_bytes`，却没有任何字段告诉运维「这些是回灌不掉的」。

**观察方式**：对照输入：`CLS_FAILED_WRITES_MAX_LINES=2`、`CLS_FAILED_WRITES_MAX_ROTATIONS=0`，Neo4j 离线时连写 6 条 outbox 条目，恢复后调 `POST /traces/replay-fallbacks` → `recovered` 最多 2（活动文件里剩的那些），另外 4 条既不在活动文件也不在磁盘上。若把同样 6 条写进一个不做轮转的文件，`recovered=6`。

### 4. [HIGH] _prune_overflow 的 max_rotations==0 特例零覆盖，删掉后两个测试文件全绿 —— 「有界」可静默变回无界

- 维度 `gate-strength` · 位置 `failure_counters.py:140` · 独立证伪票数 **3**

`victims = siblings if max_rotations == 0 else siblings[:-max_rotations]` 里的 `== 0` 特例是防 `[:-0] == [:0]` 这个语言陷阱的唯一一道防线。实测（scratch 目录）：`_prune_overflow(p, 0)` 正确删光 3 个 overflow；去掉特例后 `siblings[:-0]` 返回 `[]`，一个也不删。`max_rotations=0` 不是理论值——`bound_from_env("CLS_DEAD_LETTER_MAX_ROTATIONS", 5, minimum=0)`（:67）与 `CLS_FAILED_WRITES_MAX_ROTATIONS`（failed_writes_constants.py:29）都显式允许 0，docstring（:159）也写明「0 = 轮转后立即全删」。两个新测试文件里 max_rotations 只取过 99 / 3 / 2 / 1，从无 0。同理 `:137` 的 `if max_rotations < 0: return` 也零覆盖。

**观察方式**：对照输入：`fc.write_dead_letter` 在 `DEAD_LETTER_MAX_ROTATIONS=0` 下连写 6 条（MAX_LINES=1），断言 `_overflow_siblings(path) == []`。当前实现绿，把 :140 改成 `victims = siblings[:-max_rotations]` 后该断言会红——而现有 test_dead_letter_bounded_t6c.py / test_traces_backlog_t6c.py 的全部 17 条断言在这个改动下一条都不翻。

### 5. [HIGH] _display_path 只被 fallback 分支覆盖，唯一断言对 `return path.name` 恒真 = 门面

- 维度 `gate-strength` · 位置 `traces.py:103` · 独立证伪票数 **3**

`test_backlog_path_field_is_not_absolute`（test_traces_backlog_t6c.py:239）是唯一碰 `path` 字段的门，它把 BACKLOG_FILES 打桩到 `tmp_path`（macOS 下 `/private/var/folders/...`，必然在 `_REPO_ROOT` 之外）⇒ `path.resolve().relative_to(_REPO_ROOT)` 必抛 ValueError ⇒ 每次都走 `:112` 的 fallback `return path.name`。于是：①「相对仓根的路径」这条主张（:104 docstring）零覆盖；②断言 `not entry["path"].startswith("/")` 对 `path.name` 的任何取值恒真（文件名不可能以 / 开头），把 `_display_path` 整个函数体替换成 `return path.name` 全绿。③ `_REPO_ROOT = parents[5]`（:45）没有任何常量级断言——而同一文件的 DATA_DIR/LOGS_DIR 恰恰是靠 `parts[-2:]` 常量断言（:59/:64）抓出本卡那个 off-by-one 的，同一个修法没有施加到 _REPO_ROOT 上：它再错一层只会让所有 path 退化成纯文件名，全部门仍绿。

**观察方式**：对照输入：把 BACKLOG_FILES 打桩到仓内真实路径（例如 `traces.DATA_DIR / "failed_writes.jsonl"` 之类仓内路径，或直接对 `_display_path(Path(__file__))` 做单元断言 `== "backend/app/api/v1/endpoints/traces.py"`），success 分支才会被执行；把 `_REPO_ROOT` 改成 `parents[4]` 或 `parents[6]`、或把函数体换成 `return path.name`，现有 246 行测试文件里没有一条断言会翻。

### 6. [HIGH] bound_from_env 全函数零覆盖：tests/ 里 0 处引用、CLS_* 环境变量 0 处设置

- 维度 `gate-strength` · 位置 `failure_counters.py:40` · 独立证伪票数 **3**

`grep -rn bound_from_env tests/` = 0 行；`grep -rn -e CLS_DEAD_LETTER -e CLS_FAILED_WRITES tests/` = 0 行。该函数是**两个模块四个上限常量**的唯一入口（failure_counters.py:66/67、failed_writes_constants.py:28/29），且被声明为「上限值坏掉不该让服务死掉」的保护（:41-45，导入期求值 ⇒ 抛异常等于后端起不来）。四条分支——`raw is None`、`raw.strip()==""`、`ValueError`、`value < minimum`——一条都没有门。实测这四条当前行为都正确（`abc`→10、`0`(min=1)→10、`" 7 "`→7），但把整个函数体换成 `return default`、或删掉 `:55-57` 的 minimum 校验，两个新测试文件全绿。副作用：删掉 minimum 校验后 `CLS_DEAD_LETTER_MAX_ROTATIONS=-1` 会进 `_prune_overflow`，落到同样零覆盖的 `:137` 负数分支。

**观察方式**：对照输入：`monkeypatch.setenv("CLS_DEAD_LETTER_MAX_LINES", "abc")` + `importlib.reload` 或直接 `bound_from_env("X", 10, minimum=1)` 的参数化四例。当前零测试 ⇒ 删掉 :50-57 整段 try/except + minimum 校验后，test_dead_letter_bounded_t6c.py 与 test_traces_backlog_t6c.py 仍全绿。

### 7. [MEDIUM] 每次追加都在锁内全文件扫描：O(1) 追加退化成 O(文件大小)，且在事件循环线程上同步进行

- 维度 `concurrency` · 位置 `failure_counters.py:175` · 独立证伪票数 **3**

`rotate_if_over_limit` 在每次追加前调 `count_lines(path)`，而 `count_lines`(:81-98) 是整文件 64KB 分块读。默认上限 10000 行下，dead-letter 文件 ~2-4 MB、failed_writes ~10 MB —— 也就是**每写一条死信就整份读一遍**，全程持锁。`append_failed_writes_bounded`(failed_writes_constants.py:76-77) 更是每轮扫**两次**（`rotate_if_over_limit` 内一次，紧接着 `room = limit - count_lines(file_path)` 又一次），而 `rotate_if_over_limit` 明明刚数过却不回传计数。这三条路径全部跑在事件循环线程（`canvas_service._sync_edge_to_neo4j` 异常分支、`record_knowledge_entity`、`cleanup`），没有 `asyncio.to_thread` 包装，所以锁持有时间 = 事件循环阻塞时间。write_dead_letter 紧贴锁上方的既有注释(:287-289)仍写着「single-line JSONL append is fast enough (~μs)」——本卡之后这句已不成立，注释未同步更新。

**观察方式**：对照输入：`sync_all_edges_to_neo4j` 在 Neo4j 不可达时对 N 条边逐条走失败分支，每条调一次 `write_dead_letter`；活动文件接近 10000 行时，N 次追加 = N 次整文件读 + N 次持锁，事件循环被串行阻塞 N×(文件大小/磁盘带宽)。把 failed_writes 的规模代进去（单条 ~1 KB × 10000 行 = 10 MB，每次追加读 2 遍 = 20 MB）即可让「~μs」这句注释翻转。

### 8. [MEDIUM] 无鉴权的 backlog 端点在事件循环里做同步全文件扫描，无线程卸载、无大小上限

- 维度 `concurrency` · 位置 `traces.py:245` · 独立证伪票数 **3**

`get_dead_letter_backlog` 是 `async def`，但 `_safe_backlog_entry → _backlog_entry` 对每条 JSONL 链做**两遍**整文件读：`count_lines(path)`(:193) 一遍，`_first_last_timestamp(path)`(:194) 又一遍（后者只为取首/末条 timestamp 却要读到文件尾），再加 `overflow_siblings` 的 `iterdir` + 每个兄弟 `stat`。7 条链、5 条是 JSONL，全部同步执行、无 `asyncio.to_thread`、无 size 上限。该路由挂在裸 `APIRouter()` 上且 `api/v1/router.py:223-227` 的 `include_router` 没有路由级依赖，`_display_path` 的 docstring(:106-107) 也明确写了「本路由…无鉴权」——兄弟端点 `/traces/replay-fallbacks` 有 `require_internal_api_key`，本端点没有。于是任何能打到端口的调用方可以反复拉满事件循环。

**观察方式**：对照输入：failed_writes.jsonl 积到默认上限（10000 行 ≈ 10 MB）时连续 GET /api/v1/traces/dead-letter-backlog —— 每次请求同步读 ≥20 MB（两遍）并阻塞事件循环，其余所有 async 请求排队。端点 docstring 自称 "Purely read-only"(:242) 成立，但「只读」不等于「无副作用」：它对并发吞吐的副作用未被任何断言或限流拦下。

### 9. [MEDIUM] count_lines 的 OSError 在 rotate_if_over_limit 里被吞、在本行却直接抛出，配合 _flush_pending_failed_writes 的 finally clear() 会整批丢条目

- 维度 `data-loss` · 位置 `failed_writes_constants.py:77` · 独立证伪票数 **3**

`rotate_if_over_limit`（failure_counters.py:177-179）对 `count_lines` 的 OSError 是 fail-open：记 warning、返回 False、调用方继续追加。但本行第二次调 `count_lines(file_path)` **没有任何 try**，同一个异常会直接穿出 `append_failed_writes_bounded`。

两个写者的后果不同：
- `_record_structured_outbox`（memory_service.py:520-522）接住 OSError、返回 False —— 诚实失败，可接受；
- `_flush_pending_failed_writes`（memory_service.py:2883-2886）接住后 `finally: self._pending_failed_writes.clear()` —— **整批 pending 条目一条都没落盘就被清空**。

这是本卡引入的**新**失败面：改动前那里是裸 `open(..., "a")` + write，只要文件可写就成功；现在多了一次「必须可读」的前置。实测（pinned 47075cbe）：活动文件 chmod 0o222（可写不可读）时，裸追加成功，而 `append_failed_writes_bounded` 抛 PermissionError、追加根本没发生。真实触发面包括只写权限、文件被换成目录、以及 ACL/沙箱限制。

（worktree 已按 Codex round-1 M1 把这里包成 try/except 并退化为「一次写完」；commit 47075cbe 尚无。）

**观察方式**：对照输入：`p.write_text('{"old":1}\n'); os.chmod(p, 0o222)` 后 `append_failed_writes_bounded(p, ['{"new":1}'], max_lines=5, max_rotations=3)` → 抛 PermissionError（实测）。把 chmod 改成 0o644，同一调用正常追加。对应到生产：同一状态下 `_flush_pending_failed_writes` 返回后 `_pending_failed_writes == []` 而文件内容未变。

### 10. [MEDIUM] parents[4] 只修好 LOG_FILES 四源中的两源：bug_log 与 dead_letter_episodes 的写侧是 cwd 相对，注释却按「全部」表述

- 维度 `endpoint` · 位置 `traces.py:36` · 独立证伪票数 **1**

:36-43 的注释给 parents[4] 的依据是「全部死信文件写在 backend/data（写侧 failure_counters.py / failed_writes_constants.py 从 backend/app/core/ 走 3 层 .parent 恰好到 backend）」。这条依据只覆盖 LOG_FILES 四源里的 failed_edge_syncs 一源（EDGE_SYNC_DEAD_LETTER_PATH，failure_counters.py:32）。另两源是 **cwd 相对**：bug_log 由 bug_tracker.py:89 `def __init__(self, log_path: str = "data/bug_log.jsonl")` + :257 的模块级单例 `bug_tracker = BugTracker()` 写出；dead_letter_episodes 由 episode_worker.py:306 的默认参数 `dead_letter_path: str = "data/dead_letter_episodes.jsonl"`（:291 / :672 都用默认值构造 GraphitiEpisodeWorker）写出。二者都不吃任何 .parent 锚点。BACKLOG_FILES 的注释（:66-69）对 dead_letter_episodes 如实写了 cwd caveat，但 LOG_FILES 这一处、以及模块 docstring :3-4「aggregate all events from bug_log, audit, failed_edge_syncs, and dead_letter」都按「四源都修好了」表述 —— 名实不一致。
实际影响取决于启动 cwd：Docker 里 WORKDIR=/app 且 backend/Dockerfile 用 `COPY . .`（context=./backend），cwd 恰好 == backend，成立；但 backend/start_server.py 全程不 os.chdir（:28-30 只 sys.path.insert），文档里既有 `cd backend && python start_server.py` 也有 `python start_server.py` 两种写法。从仓根启动时 bug_log 落 <root>/data/bug_log.jsonl，而 traces 读 backend/data/bug_log.jsonl —— 四源里最重要的那源仍然恒查不到，本卡宣称修掉的 DD-13 只修掉一半。现网佐证：backend/data/ 今天仍在被写（failed_writes.jsonl / failed_edge_syncs.jsonl mtime 09-15 12:10），但**没有** bug_log.jsonl / dead_letter_episodes.jsonl；同时 worktree 仓根的 data/ 里躺着 lancedb / review_data.db 这类 cwd 相对产物，说明两种 cwd 在本机都真实发生过。

**观察方式**：对照输入：以 cwd=仓根启动后端（`python backend/start_server.py`），制造一次 500（记下响应头 X-Request-ID），再 GET /api/v1/traces/<该 id>。bug_log 条目写到 <root>/data/bug_log.jsonl，端点读 backend/data/bug_log.jsonl ⇒ 仍返回 total_events=0。现有测试抓不到：test_traces_backlog_t6c.py:57-73 只断言 DATA_DIR 的路径分段与 EDGE_SYNC_DEAD_LETTER_PATH.parent 相等，从不比对 bug_log / dead_letter_episodes 的写侧。

### 11. [MEDIUM] _first_last_timestamp 的 `if ts is None: continue` 删掉后全绿：唯一能抓它的测试不断言 newest

- 维度 `gate-strength` · 位置 `traces.py:136` · 独立证伪票数 **3**

`test_backlog_survives_corrupt_and_blank_lines`（test_traces_backlog_t6c.py:166）写的四行里最后一行正是 `{"no_timestamp": 1}`，但该测试只断言 `backlog == 4` 与 `oldest == "2026-09-05T00:00:00Z"`，**不断言 newest**。删掉 `:136-137` 的 `if ts is None: continue` 后：`first` 已在第三行被赋值不受影响 ⇒ oldest 断言仍绿；`last` 变成字符串 `"None"` ⇒ 端点会把 `newest: "None"` 返回给客户端而无人发现。另一条 `test_backlog_counts_lines_and_reports_oldest_and_newest` 的三条数据全带 timestamp，也抓不到。同函数 `:133` 的 `if not isinstance(entry, dict): continue` 同样零覆盖——两个测试文件里没有任何一行是「合法 JSON 但不是 dict」（如 `123` / `"x"`），删掉后该行会抛 AttributeError（不在 `:141` 的 `except OSError` 里），被 `_safe_backlog_entry` 的宽 except 静默压成 error 条目。

**观察方式**：对照输入：在 corrupt 测试的四行数据后加一行 `123`、并补一条 `assert entry["newest"] == "2026-09-05T00:00:00Z"`。当前实现绿；删掉 :136-137 后 newest 断言红，删掉 :133 后该链降级成 `{"error": "AttributeError"}`。现状下这两处删除全绿。

### 12. [MEDIUM] _safe_backlog_entry 的降级分支零覆盖，连「只回 type(e).__name__ 不回 str(e)」这条安全主张也是纯散文

- 维度 `gate-strength` · 位置 `traces.py:198` · 独立证伪票数 **3**

`grep -rn _safe_backlog_entry tests/` = 0 行，且没有任何测试构造出让 `_backlog_entry` 抛异常的输入。于是：①「一条链读失败不得让另外六条也看不见」（:199）零验证——把 `:247` 改成直接调 `_backlog_entry` 全绿；②「不回 `str(e)`，因为本路由无鉴权而 OSError 消息内嵌绝对路径」（:201-204）这条安全口径零验证——把 `:222` 的 `type(e).__name__` 改成 `str(e)` 全绿，绝对路径会随 200 响应回给任何能打到端口的人。注意 `test_backlog_counts_lines_and_reports_oldest_and_newest:129` 反而显式断言 `"error" not in entry`，说明作者知道降级会盖住异常，但只在顺利路径上加了哨兵，没在失败路径上加门。同理 `_backlog_entry:176` 的 `except OSError`（stat overflow 兄弟失败）也零覆盖。

**观察方式**：对照输入：把 BACKLOG_FILES 里某一条指向一个会让 `path.stat()` 抛 OSError 的路径（或 monkeypatch `traces.count_lines` 抛 OSError），断言响应 200、该条 `error == "OSError"`、其余条目正常、且 `"/" not in entry["error"]`。当前零覆盖 ⇒ 把 :222 换成 `str(e)`、或把 :247 换成 `_backlog_entry(...)`，两个新测试文件一条断言都不翻。

### 13. [MEDIUM] rotate_if_over_limit 三条 early-return 只覆盖一条；「best-effort 不变量」的全部依据都无门

- 维度 `gate-strength` · 位置 `failure_counters.py:172` · 独立证伪票数 **3**

`grep -rn rotate_if_over_limit tests/` = 0 行（只经 write_dead_letter / append_failed_writes_bounded 间接触达）。三条 early-return 中只有 `:175` 的 `count_lines(path) < max_lines` 被 `test_no_rotation_below_limit` 覆盖。零覆盖的是：①`:172` `max_lines <= 0`（关闭上限；实测 `rotate_if_over_limit(r, 0, 5)` 走的正是这条，返回 False 且不轮转——删掉它会变成每次追加都轮转，把活动文件反复 rename 成空 overflow）；②`:177` count_lines 抛 OSError 时「跳过轮转」；③`:184` rename 失败时「继续追加到活动文件、返回 False」——而这条正是 docstring :164-166 宣称的「活动文件 ≤ max_lines 是 best-effort 不变量」的唯一依据。函数的 bool 返回值在两个测试文件里也 0 次被断言。连带：failed_writes_constants.py:78 的 `if room <= 0: room = len(pending)`（防「轮转没腾出空间 ⇒ 每轮只写一行的死循环」）只在 rotate 失败或 limit<=0 时可达，同样零覆盖；实测 `append_failed_writes_bounded(s, 3 lines, max_lines=0)` 走的是 `:77` 的 `else len(pending)` 而不是 `:78`。

**观察方式**：对照输入：(a) `rotate_if_over_limit(tmp/"x.jsonl", 0, 5)` 断言 False 且无 overflow 产出；(b) monkeypatch `fc.count_lines` 抛 OSError、断言返回 False 且文件未被 rename；(c) monkeypatch `Path.rename` 抛 PermissionError、断言返回 False 且随后的 append 仍写进活动文件、条目不丢。当前三条全无 ⇒ 删掉 :172 整条 if、或把 :185 的 `return False` 改成 `raise`，现有测试全绿（后者会让 write_dead_letter 的 `except OSError` 静默吞掉整条死信）。

### 14. [MEDIUM] failed_writes 链的 retention（保留 N 个 / 删最老）零覆盖，且 raising=False 让常量改名无感

- 维度 `gate-strength` · 位置 `test_dead_letter_bounded_t6c.py:216` · 独立证伪票数 **3**

(c) 组两条测试（:232 `test_record_structured_outbox_is_bounded`、:246 `test_flush_pending_failed_writes_is_bounded`）都是 8 条 / 上限 5 ⇒ 恰好只发生 **1 次轮转**，MAX_ROTATIONS=3 永远不被逼到 ⇒ `append_failed_writes_bounded:68` 的 `keep` 参数从未影响过任何断言。dead-letter 链有 `test_retention_drops_the_oldest_overflow` 做身份判据，failed_writes 链一条都没有。叠加 `:216-217` 的 `raising=False`：`FAILED_WRITES_MAX_ROTATIONS` 一旦改名/删除，monkeypatch 会静默创建一个没人读的新属性，生产落回默认 5，两条测试照绿。（该 `raising=False` 的理由写在 dead-letter fixture 的 :56-59，说的是「改前属性还不存在」——合并后这个理由已失效，只剩削弱门的副作用。）

**观察方式**：对照输入：让 flush 交 20 条、limit=2、MAX_ROTATIONS=2，断言 `len(_overflow_siblings(path)) == 2` 且最老那批条目（"ep0"）已不在任何文件里。当前无此门 ⇒ 把 `keep` 硬写成 999、或把 :217 的常量名拼错成 `FAILED_WRITES_MAX_ROTATION`，两条 (c) 测试都不翻。

### 15. [MEDIUM] 轮转产物 .overflow.* 不被任何 .gitignore 规则覆盖（.jsonl 后缀被 with_suffix 吃掉）

- 维度 `config-and-compat` · 位置 `failure_counters.py:120` · 独立证伪票数 **3**

`_unique_overflow_target` 用 `path.with_suffix(f"{OVERFLOW_SUFFIX}{stamp}")` 生成轮转名。`Path.with_suffix` 是**替换**最后一个后缀，实测 `Path('failed_writes.jsonl').with_suffix('.overflow.2026-09-15-120000000000')` == `failed_writes.overflow.2026-09-15-120000000000` —— 产物既没有 `.jsonl` 也没有 `.synced.`。

而 `backend/data/.gitignore` 的全部规则是 `*.jsonl` / `*_memory.json` / `*.db` / `fsrs_card_states.json` / `*.synced.*`；根 `.gitignore:120` 另有 `backend/data/failed_writes.synced.*`。也就是说：回灌侧 `fallback_sync_service._rotate_file` 产出的 `.synced.` 轮转形态**当初专门补过 ignore 规则**（`backend/data/.gitignore:11`），本卡新引入的同类轮转形态没有补。

后果：写侧上限一旦在开发树 / live 树触发一次，`backend/data/` 就会出现未被忽略的未跟踪文件。第十四批合并程序（`.claude/rules/card-batch-protocol.md` §4.1「每步剔 *.stderr* + 断言干净」）在这棵树上跑；更糟的是 `git add -A` 会把死信正文（`error` 串、`canvas_name`、`episode_id`、对话相关的 `reason`）提交进仓库。

修法是补 `backend/data/.gitignore` 一行 `*.overflow.*`（与既有 `*.synced.*` 同形），本卡未做。

**观察方式**：实测 `git check-ignore -v --no-index`：`backend/data/failed_writes.overflow.2026-09-15-120000000000` / `failed_edge_syncs.overflow.…` / `failed_dual_writes.overflow.…` 三条全部 rc=1（NOT-IGNORED，无匹配规则输出）；作为对照，同目录的 `failed_writes.jsonl` 命中 `backend/data/.gitignore:5:*.jsonl`、`failed_writes.synced.2026-09-15-120000` 命中 `backend/data/.gitignore:11:*.synced.*`。触发输入：`CLS_DEAD_LETTER_MAX_LINES=1` 下连写两条 `write_dead_letter`，或默认 10000 行下一次足够长的 Neo4j 离线（现网 `failed_edge_syncs.jsonl` 今日已 68 行）。

### 16. [MEDIUM] _REPO_ROOT=parents[5] 依赖部署布局：容器里等于 /，_display_path 退化成回完整绝对路径，而现有门仍绿

- 维度 `config-and-compat` · 位置 `traces.py:45` · 独立证伪票数 **2**

`_BACKEND_DIR = parents[4]` 与 `_REPO_ROOT = parents[5]` 是同一个字面深度假设的两半，但只有前者在两种布局下都对。

`backend/Dockerfile` 是 `WORKDIR /app` + `COPY . .`（backend/ 的内容拷进 /app），`docker-compose.yml:208` 是 `./backend:/app`。于是容器里 traces.py 的绝对路径是 `/app/app/api/v1/endpoints/traces.py`：`parents[4] == /app`（= backend，DATA_DIR/LOGS_DIR 修得对），但 `parents[5] == /`。

`_display_path` 的 docstring 写「本路由与兄弟 `/traces/{request_id}` 一样**无鉴权**，所以不回绝对路径（那会把文件系统布局暴露给任何能打到端口的人）」。`relative_to('/')` 对任何绝对路径都成功，只剥掉开头那个斜杠 ⇒ 返回值就是完整容器路径本身（`app/data/failed_writes.jsonl`），fallback 到 `path.name` 的分支永不执行，声明的防护在容器部署下等于不存在。

同一根因的第二个面：任何让 app 包位于文件系统根下 ≤4 层的布局会让 `parents[5]` 在**模块导入期**抛 IndexError（整个 traces router 起不来）。我在本仓的 Dockerfile / compose / 主机 worktree 三种已配置布局里都无法构造出这种深度，如实声明为不可达，不据此定级。

**观察方式**：实测路径算术（PurePosixPath，容器布局）：`PurePosixPath('/app/app/api/v1/endpoints/traces.py').parents` == ['/app/app/api/v1/endpoints','/app/app/api/v1','/app/app/api','/app/app','/app','/']，即 `_REPO_ROOT == '/'`；`PurePosixPath('/app/data/failed_writes.jsonl').relative_to('/')` == `app/data/failed_writes.jsonl`，`str(...).startswith('/')` 为 **False**。⇒ `test_backlog_path_field_is_not_absolute`（tests/unit/test_traces_backlog_t6c.py:239-245，判据就是 `not startswith('/')`）在容器布局下照样绿，而端点回的正是完整绝对路径。主机 worktree 下 `_REPO_ROOT` 是 worktree 根、行为符合预期 —— 两种布局结论相反，判据只覆盖了对的那一种。

### 17. [LOW] overflow_bytes 的 exists()→stat() TOCTOU：被并发 retention 删掉一个兄弟就整块归 0

- 维度 `concurrency` · 位置 `traces.py:175` · 独立证伪票数 **3**

`entry["overflow_bytes"] = sum(p.stat().st_size for p in siblings if p.exists())` 是典型 TOCTOU：`p.exists()` 与 `p.stat()` 之间，写侧 `_prune_overflow`(failure_counters.py:132-146) 可能 `unlink` 掉该兄弟，`stat` 抛 `FileNotFoundError`（⊂ `OSError`），被 :176 的 `except OSError` 接住。此时 `overflow_files` 已在 :174 赋成 N，而 `overflow_bytes` 的赋值语句整体没执行完 ⇒ 保持初始值 0。端点返回 `overflow_files=N, overflow_bytes=0`，读的人会以为 N 个溢出文件都是空的。这条路径只记一行 warning，响应里没有任何降级标记（不像 `_safe_backlog_entry` 会带 `error` 字段）。

**观察方式**：对照输入：MAX_ROTATIONS 已满、写侧正在 `_prune_overflow` 删最老兄弟的同时调 backlog。`sum()` 生成器在删掉的那个上抛 FileNotFoundError ⇒ 响应 `overflow_files=5, overflow_bytes=0`，与 test_backlog_reports_overflow_siblings(test_traces_backlog_t6c.py:146) 的 `assert entry["overflow_bytes"] > 0` 相反，而该测试是串行的、抓不到这个窗口。

### 18. [LOW] BACKLOG_FILES 里的 failed_dual_writes.jsonl 无任何生产写侧，「七条链」集合把死链算进、把活链（outbox）排除

- 维度 `endpoint` · 位置 `traces.py:73` · 独立证伪票数 **3**

对 backend/ 全树 grep `DUAL_WRITE_DEAD_LETTER_PATH`，命中只有三类：failure_counters.py:35 的定义本身、traces.py:22/:75 的 import 与表项、以及测试（test_failure_observability.py:338 / test_dead_letter_bounded_t6c.py:66,93 / test_epic36_integration.py:332-339）。全仓唯一的 `write_dead_letter(` 生产调用点是 canvas_service.py:508，传的是 EDGE_SYNC_DEAD_LETTER_PATH；memory_service.py 里连 "dead_letter" 字样都没有（grep 零命中），而 test_failure_observability.py:338 却 patch `app.services.memory_service.DUAL_WRITE_DEAD_LETTER_PATH`。结论：failed_dual_writes.jsonl 在生产里**恒不被写**，该条目恒报 exists=false / backlog=0。
本身无害，但它和上面 outbox 缺席合起来说明 test_backlog_covers_every_staging_chain（test_traces_backlog_t6c.py:203-213）的「七条一条不漏」并不是对「真实暂存链集合」的断言 —— 它把实现里的那七个键原样抄成期望集合，因此既挡不住多一条死链，也挡不住少一条活链。

**观察方式**：对照输入：从 BACKLOG_FILES 里删掉 failed_dual_writes.jsonl、加上 outbox/events.jsonl（即改成与真实写侧一致），test_backlog_covers_every_staging_chain 立刻变红；反过来，保持现状而生产里 failed_dual_writes 永远为空、outbox 一直在涨，该测试恒绿。判定「链集合是否正确」的唯一判据是这份手抄集合，不是写侧代码。

### 19. [LOW] _unique_overflow_target 的防撞段（exists 检查 + 100 次重试 + uuid4 兜底）零覆盖，标题所声称的验证内容与实际判据不符

- 维度 `gate-strength` · 位置 `failure_counters.py:121` · 独立证伪票数 **2**

`test_rotation_preserves_every_entry`（test_dead_letter_bounded_t6c.py:134）的 docstring 声称验的是「同一秒内多次轮转不得静默互相覆盖」。实际上在微秒戳（:119 `%Y-%m-%d-%H%M%S%f`）下测试里不可能撞名，所以它只能证明「戳的精度够」，证不到 `:121-129` 这段防撞逻辑本身：把 `:121-129` 整段删掉、只留 `return target`，该测试与其余全部测试仍绿。该段在文档里被当成跨进程同微秒撞名的最后防线（:117），也是「牺牲可排序性也不覆盖数据」的唯一实现。附带：`:129` 的 uuid4 后缀会破坏 retention 的「字典序 == 时序」前提（比定宽戳长、排序位置不确定），这个副作用同样无门。

**观察方式**：对照输入：monkeypatch `fc.datetime` 让 `now().strftime` 恒返回同一个戳（模拟跨进程同微秒），连写 3 次触发 3 次轮转，断言 3 份 overflow 都在、条目守恒。当前实现绿，删掉 :121-129 后该断言会红（后两次 rename 静默覆盖）——而现有测试在这个删除下一条都不翻。

### 20. [LOW] 端点两个汇总字段 total_backlog / total_overflow_files 零断言，且「未知」被静默压成「空」

- 维度 `gate-strength` · 位置 `traces.py:253` · 独立证伪票数 **3**

`grep -rn -e total_backlog -e total_overflow_files tests/` = 0 行。响应里这两个字段是运维实际会看的聚合值，却没有任何门：把 `:253` 改成 `sum(...)` 之外的任何值（含恒 0）全绿。语义上还有一处未被门覆盖的口径问题：注释（:251-252）声称「None 跳过而不是当 0」，但 `sum(f["backlog"] or 0 for f in files)` 对**降级链**（`_safe_backlog_entry` 返回 `backlog=None`）的效果就是按 0 计入总数——与兄弟端点 `/traces/replay-fallbacks` 对 `pending=-1` 明确要求「调用方必须跳过负值」（:298-301）的口径不一致：那里「未知」是可辨识的，这里「未知」和「空」在 total 里不可区分，且响应顶层没有任何 degraded 标志。

**观察方式**：对照输入：BACKLOG_FILES 打桩成两条链（一条 3 行 JSONL、一条读取会抛异常的），断言 `total_backlog == 3` 且顶层带有可辨识的降级计数。当前零断言 ⇒ 把 :253 改成 `0`、或把 :254 改成 `len(files)`，两个测试文件全绿。

## 被证伪的发现（保留原文，供复核反查是否误杀）

| 级别 | 维度 | 位置 | 标题 |
|---|---|---|---|
| MEDIUM | concurrency | `traces.py:173` | backlog 先读 overflow 快照再数活动文件且全程不持锁：中间发生一次轮转 ⇒ 整代积压两边都数不到 |
| LOW | concurrency | `failure_counters.py:233` | 共享原语的锁契约绑在模块而不是文件上：write_dead_letter 收任意路径，两把锁护同一文件不会被任何断言拦下 |
| MEDIUM | data-loss | `failed_writes_constants.py:73` | 分批写循环会在同一次调用里删掉自己刚写下的段；「且一条不丢」的注释不成立，keep=0 是被显式允许的配置 |
| LOW | data-loss | `failure_counters.py:137` | _prune_overflow 对负 max_rotations 直接 return，行为（全保留）与 docstring（只保留最新 N 个）相反，且静默关掉「有界」保证 |
| LOW | data-loss | `failure_counters.py:129` | _unique_overflow_target 的退化分支既不做存在性检查，也破坏 _prune_overflow 依赖的「定宽 ⇒ 字典序==时序」不变量 |
| LOW | data-loss | `traces.py:194` | backlog 的 oldest 只扫活动文件，轮转一次积压就「变年轻」——与被显式加了 active-only 限定的 backlog 字段口径不一致 |
| HIGH | endpoint | `traces.py:258` | DATA_DIR/LOGS_DIR 修对目录后，无鉴权的 GET /traces/{request_id} 从「恒空」变成真回 stack_trace + request_params |
| MEDIUM | endpoint | `traces.py:70` | BACKLOG_FILES 漏掉一条活着的暂存链：backend/data/outbox/events.jsonl（端点自称覆盖「every staging file」） |
| MEDIUM | endpoint | `traces.py:253` | total_backlog 把「未知」压成 0，且顶层无 error/unknown 计数 —— 注释声称的口径与代码相反 |
| MEDIUM | endpoint | `traces.py:240` | description 称「rotated entries 由 overflow_files/overflow_bytes 计数」，但两者是文件数与字节数，且被 retention 删掉的溢出完全不计 |
| MEDIUM | endpoint | `traces.py:245` | 新增的无鉴权 GET 在 async 处理器里做无上限阻塞式全文件读（每条 JSONL 读两遍），dead_letter_episodes / outbox 本卡未加上限 |
| LOW | endpoint | `traces.py:103` | _display_path 的脱敏随部署布局退化（容器里 _REPO_ROOT == "/"），且唯一那条测试走的是 except 分支、判据无法失败 |
| MEDIUM | gate-strength | `test_traces_backlog_t6c.py:105` | BACKLOG_FILES 用 raising=False 打桩：常量改名后打桩静默失效，端点转去读现网 backend/data 且部分测试仍绿 |
| LOW | gate-strength | `test_dead_letter_bounded_t6c.py:11` | 「_nlines 与生产 count_lines 逐字节同口径」的自述不成立，且 count_lines 的两条差异点都零覆盖 |
| LOW | gate-strength | `test_dead_letter_bounded_t6c.py:38` | 测试本地 _overflow_siblings 是生产 overflow_siblings 的更宽再实现；写侧命名与读侧发现之间没有端到端门 |
| MEDIUM | config-and-compat | `failure_counters.py:55` | bound_from_env 只卡下限不卡上限，且超大值零告警 —— 一个多打的 0 就静默关掉本卡的写侧有界 |
| LOW | config-and-compat | `failure_counters.py:67` | max_lines<=0「关闭上限」在 env 侧不可达，而 max_rotations==0「轮转后立即全删」可达 —— 三种语义只暴露了破坏性的那一种 |
| LOW | config-and-compat | `memory_service.py:2877` | 批量序列化被提到写循环之外：序列化失败时从「前缀已落盘」变成「整批不落盘」（当前入口不可达，如实声明） |
