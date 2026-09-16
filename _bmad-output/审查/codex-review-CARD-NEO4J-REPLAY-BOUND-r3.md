> 批次: BATCH-2026-09-11-第十四批 · 车道 T6 · 卡 CARD-NEO4J-REPLAY-BOUND round-3
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-NEO4J-REPLAY-BOUND-r3.md)"`
> 审查绑定: `26bf4a2e..11caca05`（前一轮：r2 审 b8cd3a82）
> 会话头自证（抄 .stderr，stderr 本身不入库）:
> `stderr:2 OpenAI Codex v0.153.3` / `stderr:5 model: gpt-6-astra` / `stderr:9 reasoning effort: ultra`

---

审查绑定 **`11caca051db1568147c11963d825863c57f2b479`**，结束时 HEAD 未变。结论：**BLOCKER 0 / HIGH 2 / MEDIUM 1 / LOW 4**。round-2 的正常游标交错已修复，但“全部收口”不成立。

1. **HIGH：checkpoint 编码异常会导致合法待写批次丢失。**  
   [failed_writes_constants.py:132](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/core/failed_writes_constants.py:132) 及 `:142` 没有捕获 `UnicodeDecodeError`／`UnicodeEncodeError`。对照输入：活动文件达到上限，pending 是合法记录，checkpoint 内容为 `b'\xff'`；新增前置动作在追加前抛错，[memory_service.py:2883](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/services/memory_service.py:2883) 随后捕获 `ValueError` 并在 `finally` 清空 pending。**内存执行实际函数链，结果为追加调用 0 次、pending 变空**；单条 outbox 路径则让异常逃逸。其他 checkpoint 键含合法 JSON `"\ud800"` 也能触发编码异常。原失败门把整个前置动作替换成 `lambda: False`，没有覆盖此路径。

2. **HIGH：普通测试会操作真实 checkpoint，临时文件隔离不完整。**  
   [test_dead_letter_bounded_t6c.py:216](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/tests/unit/test_dead_letter_bounded_t6c.py:216) 只隔离上限和 `ms.FAILED_WRITES_FILE`，没有隔离新增副作用使用的 `fss.SYNC_CHECKPOINT_FILE`。`:232` 的测试写第六条时就会触发它；真实 `backend/data/sync_checkpoint.json` 若含 `failed_writes` 键，会被删除或改写。checkpoint 不存在时测试照样绿，因此结果依赖真实磁盘状态。两级 conftest 也没有补上该隔离。

3. **MEDIUM：M3 预算仍未限制实际读取量，而且计算的是字符数。**  
   [traces.py:223](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/api/v1/endpoints/traces.py:223) 仍先用 `for line in f` 读完整行，再扣 `len(line)`。复用新版测试输入，预算 100 时，流已返回 **37、5038 字符**两行，而测试三条断言全部通过。另一对照为含 30 个 😀 的 timestamp：48 字符、138 字节，开扫 stat 报小尺寸时，预算 100 仍返回 `reason=None`。[测试 :561](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/tests/unit/test_traces_backlog_t6c.py:561) 现在确实进入循环，但只证明“未解析长记录”，没有证明“未整行读取”；超长行内存风险仍在。

4. **LOW：根锚测试仍被深度保护遮蔽。**  
   [test_traces_backlog_t6c.py:415](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/tests/unit/test_traces_backlog_t6c.py:415) 虽然真的传入 `/`，但常规 `tmp_path` 超过三段。内存负控删除根锚检查后，深度检查仍让原测试通过。改用 `anchor="/"`、`path="/secret.jsonl"`，返回值才会从 `secret.jsonl` 翻转为 `backend/secret.jsonl`，独立检验根锚保护。

5. **LOW：“观测失败仍退回有界”的门没有验证最终行为。**  
   [test_dead_letter_bounded_t6c.py:508](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/tests/unit/test_dead_letter_bounded_t6c.py:508) 只断言 `_replay_in_flight() is False`。同一个导入失败会使新增 checkpoint 前置动作返回 False，之后满额追加一直不轮转；该门仍绿，源码 `failed_writes_constants.py:70` 的相应声明也已失真。持续权限故障同样可能让越限无限持续。

6. **LOW：批量 flush 的守恒门只数行，不验条目身份。**  
   [test_dead_letter_bounded_t6c.py:261](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/tests/unit/test_dead_letter_bounded_t6c.py:261) 的内存负控把每段写入改为重复 `chunk[0]`，输出变成 `ep0×5、ep5×3`，原测试仍通过。dead-letter 链的身份检查没有覆盖这条批量链。这是测试缺口，当前生产代码未观察到该重复行为。

7. **LOW：并发原子性缺少回归门。**  
   [test_dead_letter_bounded_t6c.py:454](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/tests/unit/test_dead_letter_bounded_t6c.py:454) 只在持有回灌锁时顺序追加；全部 60 门没有并发写者交错，不能验证两个写者同时跨越阈值时的条目守恒和轮转次数。此项是验证缺口，**不是已证实的生产竞态**。

其余问题的核对结果：

- **原子性／死锁：** 当前生产调用中，两处 memory 写者及 agent 旁路使用同一 `failed_writes_lock`；dead-letter 的核数、轮转、追加完整处于其 IO 锁内。新增锁序为 `failed_writes_lock → _checkpoint_lock`，与 finalize 同向，未发现重入或反序。正常 checkpoint 下，先作废再轮转覆盖了原 H1；跨进程非原子已有明确披露。
- **目录：** `audit` 已对齐实际 `backend/logs`；`bug_log` 仍取决于 cwd，源码已说明仅 cwd=backend 时对齐。未发现 `request_id` 能改变固定待读路径。
- **backlog：** 非 JSONL 三字段保持 null；普通坏行、空文件、权限故障有相应处理。`_safe_backlog_entry` 会标记 `error/partial/incomplete`，未发现已捕获异常被包装成完整成功；超大文件的读取保障仍受第 3 项影响。
- **env：** 无效值、负数及超长数字探针未出现 `ValueError` 逃逸；可解析的大正整数被接受，没有最大值钳制。**env 行数设 0 会退回默认值**，直接 helper 参数 `<=0` 才关闭上限；保留数 0 表示全删，语义明确。
- **已披露限制：** overflow 无回灌方、超过保留数删除，以及 agent 单独写入可无限增长，源码均明确记录。请求摘要中的“暂时越限”比源码实际保证更强。
- **有效的指定门：** `max_rotations==0` 错切片负控确实转红；三条 early-return 都有输入覆盖；`_display_path` 的正常分支和异常 fallback 有有效断言。

本次为源码交叉复核及内存 AST 探针，**没有运行完整 pytest、修改文件或连接数据库**；第 2 项也是不能直接原样运行这些测试的具体原因。


