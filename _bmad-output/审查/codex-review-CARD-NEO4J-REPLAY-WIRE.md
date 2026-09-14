> 批次: BATCH-2026-09-11-第十四批 · 车道 T6 · 卡 CARD-NEO4J-REPLAY-WIRE round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-NEO4J-REPLAY-WIRE.md)"`
> 审查绑定: `cd1b5ae91519f86ea1ce83f813d4f8a64fd11f59`（该轮的 HEAD；本卡随后按本轮意见整改，最终 HEAD 为 `d9fa0774`，见 round-2 存档）
> 会话头自证（抄 .stderr 第 2 / 5 / 9 行含 model 行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`

---

**结论：指定读取面内发现 5 项问题，暂不能签署整卡通过。** 已锁定 `cd1b5ae91519f86ea1ce83f813d4f8a64fd11f59`；未改文件、未运行测试、未连接数据库。负控实测采用你提供的结果，本次独立核对源码因果关系。

- **⓪ MEDIUM — 门未覆盖启动与生产单例装配。**  
  [test_neo4j_replay_wire_t6b.py:186](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/tests/integration/test_neo4j_replay_wire_t6b.py:186)、`:197`、`:224`。夹具只清图、写隔离暂存文件；`:293` 先查空，`:302` 再查回灌结果。因此，负控输入②足以排除**该管理端点评分路径在验夹具预置图或只验 stats**。但客户端预先初始化、单例被替换，且不运行 lifespan。  
  **复现思路：**负控输入只摘掉 `main.py` 的启动调用、保留端点，当前新测试仍可全部通过。其他门未覆盖的路径包括真实离线写侧、断连恢复、另外两种暂存文件，以及普查登记的结构化条目与跨 vault 归属。

- **① MEDIUM — 首轮 Episode 数没有锁定，重复数据可以成为比较基准。**  
  [test_neo4j_replay_wire_t6b.py:354](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/tests/integration/test_neo4j_replay_wire_t6b.py:354)、`:365`。首轮只要求 `Concept == 1`，没有要求 `Episode == 1`；第二轮仅比较计数是否相同。它能挡住第二轮新增的、连接门 Node 的 Episode，但不能证明首轮没有重复。  
  **复现思路：**按作者所述 `CREATE` 行为，对照输入让首轮同一条评分写两次历史、仍报告 `recovered=1` 并轮转，会形成 `Episode 2 → 2` 而通过。**“防重复靠轮转而非 checkpoint”的判断尚未独立核实**，相关实现不在获准读取片段内。

- **② MEDIUM — 内层异常处理没有识别“以返回值表示失败”的路径。**  
  [main.py:420](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/main.py:420)、[fallback_sync_service.py:83](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/services/fallback_sync_service.py:83)。子同步异常被转成 `error` 加 `recovered=0,pending=0`，启动摘要忽略 `error`，仍输出“启动已恢复……0 条待回灌”。底层 warning 存在，但最后摘要会误导。  
  **复现思路：**对照输入令任一子同步抛出其外层捕获的 `OSError`，检查最后摘要是否仍显示零待回灌。另，`:392` 回填抛异常时根本到不了回灌；`:410` 的 import 和离线计数也在内层保护之外。并发、单例装配次序尚未核实。

- **③ MEDIUM — “仅计数、不返回路径或内容”的承诺不成立。**  
  [traces.py:123](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/api/v1/endpoints/traces.py:123)、`:127`；`fallback_sync_service.py:71,83,90,100`。端点原样返回 `error=str(e)`，健康检查的 `reason` 也拼接异常文本；没有字段过滤或脱敏。鉴权限制了接收者，但没有限制异常文本内容。  
  **复现思路：**对照输入使被捕获的异常携带绝对路径，检查响应 `error`／`reason` 是否原样包含该路径。源码证明存在外带通道，本次没有验证真实敏感条目是否曾被带出。

- **④ LOW — 非 UTF-8 文件会让离线登记被误报为回填失败。**  
  [fallback_sync_service.py:151](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/services/fallback_sync_service.py:151)、`:168`；`main.py:445`。`UnicodeDecodeError` 不在两个计数函数的捕获集合内，会逃到外层“启动回填 failed”。  
  **复现思路：**对照输入在隔离暂存文件放入非法 UTF-8 字节，进入离线计数分支，检查登记日志是否缺失、异常是否被错误归类。  
  计数方法本身没有调用 Neo4j；生产运行时**确实会读取部署树的真实暂存文件**。已核实两条路径为 `backend/app/data/canvas_events_fallback.json`、`backend/data/learning_memories.json`；`FAILED_WRITES_FILE` 的定义及客户端构造器仍未获准追加读取。

- **⑤ 源码核对通过，不计缺陷。**  
  [main.py:420](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/main.py:420)、[fallback_sync_service.py:179](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/services/fallback_sync_service.py:179)。新增 diff 没有 `pyright: ignore`；`.get()` 前的 `dict` 判断和 `len()` 前的 `list` 判断正确。未发现所问的类型错误；本次未独立复跑“0 errors”。

- **⑥ 隔离设计成立，工厂绑定尚待核实，不计缺陷。**  
  [test_neo4j_replay_wire_t6b.py:193](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/tests/integration/test_neo4j_replay_wire_t6b.py:193)、`:197`、`:387`、`:395`、`:403`。三个拒绝用例都装配了隔离文件和服务实例；**若工厂按约定返回该单例**，负控输入①移除鉴权后，未被拦下的输入仍落到测试实例。正常鉴权复用了原依赖，`security.py` 未改。仅凭当前片段，不能独立确认未装夹具时必然连接 7691。

另已确认：`main.py` 两个 hunk 均为所述纯插入。追加读取尚未获得答复，因此保留原读取边界；未核实项来自本次提示中的“只读这些”限制。

**计数汇总：BLOCKER 0 / HIGH 0 / MEDIUM 4 / LOW 1。**


