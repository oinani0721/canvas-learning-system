> 批次: BATCH-2026-09-11-第十四批 · 车道 T6 · 卡 CARD-NEO4J-REPLAY-WIRE round-9
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-NEO4J-REPLAY-WIRE-r9.md)"`
> 审查绑定: `97bf36725073956999c8fddd5915e09c2ae68a18`（判定「本卡新增/遗漏 HIGH 已降为 0」）
> 会话头自证（抄 .stderr 第 2/5/9 行含 model 行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`

---

**`97bf3672` 的本卡新增／遗漏 HIGH 已降为 0；全量仍有 HIGH 2 条。旧游标漏口关闭，pending 修复仅部分闭环。**

审查始末实际 HEAD 均为 `acc11c05`，它比指定版本多一次文档归档，代码无差异。本结论绑定 `97bf36725073956999c8fddd5915e09c2ae68a18`。完成限定源码、相关消费点及全卡差分交叉复核；未改文件、未连接数据库。验证采用源码条件／AST 表达式及标准库锁竞争，未运行实库集成门。

1. **HIGH〔既有算法，应归独立重写卡〕— 缺 timestamp 的旧评分仍能覆盖新评分。**  
   [fallback_sync_service.py:602](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/services/fallback_sync_service.py:602)，关联 `:629–632、:739、:763–767`。

   **负控输入：**旧 `score=10` 条目缺 timestamp，期间线上写入 `score=90`，再次重放时旧条目取得新的 `now()`，通过更新条件覆盖 90。固定真实旧 timestamp 的**对照输入**受到保护。已核对 `310eef31` 存在相同算法，本轮不新增计数。

2. **HIGH〔既知 G2-2 移交〕— 旧记录归属仍由当前 vault 决定。**  
   [fallback_sync_service.py:999](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/services/fallback_sync_service.py:999)，关联 `:1002–1005、:609、:695、:744`。

   **负控输入：**A 留下暂存记录，切到 B 后回灌；归属取当前 ContextVar／active vault，未比较来源 vault，仍可能写入 B。与 r8 相同。

3. **MEDIUM〔既知移交，r8 MEDIUM-4 部分修复〕— 剩余量和失败状态仍有失真分支。**  
   [fallback_sync_service.py:406](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/services/fallback_sync_service.py:406)，关联 `:288、:438、:542、:374–379、:482–486、:917–921`。

   **负控输入：**全部成功、无追加，但清 checkpoint 失败，原文件保留而返回 `pending=0,error=...`；轮转连续三次 `PermissionError` 时，甚至返回 `pending=0` 且没有 `error`。这不符合新增的“文件实际剩余”口径。

   同根的**门未覆盖的路径**还有：三链初读／解析失败仍返回 `0/0` 且无 `error`，启动汇总可报正常完成；外层捕获异常仍使用 `pending=0`；finalize 重读失败的局部日志仍打印 `len(still_pending)`，可与正确的 `unknown` 汇总矛盾。**以上合并一条，不按分支重复计数，也不据状态失真认定数据删除 HIGH。**

4. **MEDIUM〔既知移交〕— 模块锁跨事件循环复用仍会失败。**  
   [fallback_sync_service.py:84](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/services/fallback_sync_service.py:84)，关联 `:110`。

   **负控输入：**同进程 loop A 先发生锁竞争，再在 loop B 竞争；本轮纯内存核验仍报 `bound to a different event loop`。同一循环的**对照输入**正常。

5. **MEDIUM〔既知移交〕— 错误非默认 vault 的归属门仍可假绿。**  
   [test_neo4j_replay_wire_t6b.py:429](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/tests/integration/test_neo4j_replay_wire_t6b.py:429)，关联 `:430–435`。

   **未被拦下的输入：**Concept 与 LEARNED 同属错误组 `vault__other__wrong`，其余字段和数量正确；现有断言仍通过，因为没有独立确定并精确比较预期来源组。维持 r8 的 MEDIUM。

6. **LOW〔本轮新增语义的文档遗漏〕— 管理端点未解释 `pending=-1`。**  
   [traces.py:124](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/api/v1/endpoints/traces.py:124)，关联 `:109、:139`。

   **负控输入：**finalize 重读失败，端点返回 `pending=-1,error="finalize..."`，但端点说明只列 `pending:int`，没有说明负值代表未知。这是对外语义说明遗漏，**未证实现有调用方故障或响应校验破坏**。

两条整改及具体问题的结论：

| 核验对象 | 结论 |
|---|---|
| 旧评分 checkpoint | **原路径关闭。** 旧标记 `index=50` 经实际源码条件核验回退 0；51 条记录的循环边界投影覆盖全部 51 条、包含 `c0`。新标记对照保留游标。 |
| 全部成功、无追加 | **正常 finalize 后仍为 0。** `merged=[]`；追加 z 的对照返回 1。异常 finalize 的例外见第 3 项。 |
| `-1` 的数值消费 | 服务与 [main.py:427](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/main.py:427) 均已处理。源码表达式核验 `[-1,2,0]` 得“≥2＋未知链”，没有发现第三次数值累加。 |
| 日志及对外出口 | `traces.py:138–139` 是额外的展示／序列化出口，原样保留 stats；因此“无第三处消费点”应收窄为“无第三处数值聚合”。局部错误日志仍有第 3 项遗漏。 |
| canvas 历史 checkpoint | **没有一并回退的副作用：该链已完全不消费 checkpoint。** |
| learning 历史 checkpoint | 会从头重放旧前缀，增加工作量；源文件不改写、不轮转，未发现新增删除路径。缺 timestamp 时会再次触发第 1 项，不能无条件宣称幂等。 |

**管理端点未形成已证实的新契约校验破坏或新的信息暴露边界。** 返回标注是 `Dict[str, Any]`，没有非负字段约束；`-1` 和字符串可以序列化。原始异常可能包含绝对路径、host/port，但 `error/reason` 透传及其披露在 r8 已存在，r9 增加了产生错误文本的分支，没有扩大访问受众。新增问题限于第 6 项的哨兵语义说明。

在本次读取面及全卡差分内，**未确认额外的数据丢失／跨 vault 污染／门假绿 HIGH**。现有集成门仍不能证明 lifespan、崩溃恢复和部分成功重试安全，这些属于**门未覆盖的路径**。

超过五轮上限的事实不变；是否止于此版仍由主 session 裁定。

**计数汇总：BLOCKER 0 / HIGH 2 / MEDIUM 3 / LOW 1。**

| 分类（互斥计数） | 条数 |
|---|---:|
| 本卡引入或遗漏，扣除下列既知项 | **1：LOW 1；HIGH 0** |
| 既有算法，应归独立重写卡 | **1：HIGH 1** |
| 既知移交项，含 MEDIUM-4 未完全关闭 | **4：HIGH 1、MEDIUM 3** |


