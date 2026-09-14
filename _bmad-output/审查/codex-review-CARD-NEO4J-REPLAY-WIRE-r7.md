> 批次: BATCH-2026-09-11-第十四批 · 车道 T6 · 卡 CARD-NEO4J-REPLAY-WIRE round-7
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-NEO4J-REPLAY-WIRE-r7.md)"`
> 审查绑定: `1028bea72c66d873f98cc34038ec2ab285ae9b21`（= 最终 HEAD；审查始末 HEAD 未变，车道全程未改代码）
> 会话头自证（抄 .stderr 第 4/7/11 行含 model 行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`

---

**`1028bea7` 仍不能判定闭环。** 本轮确认四项 HIGH，另有一项源码已登记移交 G2-2 的既知跨 vault HIGH 风险。

审查始末 HEAD 均为 `1028bea72c66d873f98cc34038ec2ab285ae9b21`，分支为 `card/t6-neo4j`，所审代码未变化。证据来自指定读取面、并行交叉复核与纯内存 AST／并发负控；未改文件、未连接数据库，未运行实库测试。

1. **HIGH — `canvas_events` 的位置游标没有绑定快照，换代或重新排序后会跳过未成功事件。**  
   [fallback_sync_service.py:416](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/services/fallback_sync_service.py:416)，关联 `:418、:428、:451–458`。

   **负控输入一：**前 50 条成功、第 51 条失败，压缩为仅剩第 51 条后，清 checkpoint 失败或进程中断。重启仍接受 `index=50`，实测不尝试任何记录，直接轮转唯一失败条目。

   **负控输入二：**保存连续成功前缀 50 后中断，随后追加时间戳更早的 z。重启先排序，z 被移入游标之前，未重放却随 finalize 退出队列。这个路径不需要旧版本，也不需要发生压缩。

   **最小改法：**临时禁用 canvas 的位置 checkpoint，接受重复重放；若保留续跑，必须绑定稳定快照及排序，并在换代前可靠作废游标。**仅前移 `_clear_checkpoint` 或检查下标范围不够。**

2. **HIGH — canvas 推进规则已改，但旧“已尝试”游标仍带当前版本，被升级后的代码接受。**  
   [fallback_sync_service.py:57](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/services/fallback_sync_service.py:57)，关联 `:446–447、:755–756、:782`。

   **负控输入：**`962d86c6` 中 canvas 第一条失败、2–50 成功，保存 `index=50, progress_version="split-lf+contiguous"` 后中断，再升级至本轮。整改 diff 证明旧 canvas 按 `i+1` 保存，但共享保存器已经使用这个标记；当前代码实测只尝试第 51 条，第一条失败记录被轮转。

   **最小改法：**为改动过语义的链更新版本、拒绝旧标记；learning 的旧标记也应作废。第 1 项若直接禁用 canvas checkpoint，可以同时止住此路径。此项与第 1 项分别涉及**历史语义迁移**和**当前快照身份**，修复验收应保留两组负控。

3. **HIGH — canvas finalize 完全不重读，单次回灌即可覆盖期间新增事件。**  
   [fallback_sync_service.py:449](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/services/fallback_sync_service.py:449)，关联 `:433、:451–456`。

   **负控输入：**初读 `[x,y]`，重放期间追加 z，x 成功、y 失败；实测最终只写回 `[y]`，z 被删除。全部成功时，尚未重放的 z 也可能被一起轮转。

   这是 HIGH-3 的同型数据保留问题，甚至无需注入读取异常。模块锁只串行化回灌调用，不能阻止正常写入。

   **最小改法：**在与写入方协调的边界内核对当前内容、保留未处理记录；重读失败或无法证明快照关系时放弃破坏性 finalize。临时止血可以保留 canvas 源文件并接受重复重放。**不能直接照搬按长度截取追加后缀，因为该链会排序。**

4. **HIGH — 评分历史写入失败，整条记录仍被确认恢复并退出回灌队列。**  
   [fallback_sync_service.py:604](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/services/fallback_sync_service.py:604)，关联 `:607、:314–317、:382–388`。

   **负控输入：**LEARNED 写入成功，随后 `record_score_history()` 抛 `ConnectionError`。源码控制流实测仍返回 `True`，与两次写入均成功的**对照输入**相同；调用方据此移除／轮转记录，缺失的评分历史不再自动重试。

   **最小改法：**历史写入异常返回 `False`，保留 pending；若客户端还通过返回值表达失败，也应检查其正式契约。边界是数据库提交结果不确定时可能重复 Episode，可靠去重需要稳定记录身份。此项是既有算法缺陷，当前集成门只覆盖正常写入。

5. **HIGH〔既知 G2-2 移交风险，非本轮新增〕— 重放使用当前 vault，不能证明条目的来源 vault。**  
   [fallback_sync_service.py:907](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/services/fallback_sync_service.py:907)，关联 `:549–550、:922–928`。

   **负控输入：**vault A 留下暂存条目，切到 B 后触发回灌；归属从当前 ContextVar／active vault 构造，未读取条目来源，因而会写入 B。源码已经明确承认并移交此风险。

   **最小止血边界：**来源无法证明的历史条目保留待处理；完整修复交 G2-2 持久化来源身份并按该身份重放。单 active vault 约束不能排除先后切换。这里登记的是源码路径，未声称观察到实际数据库污染。

6. **MEDIUM — 模块级 `asyncio.Lock` 跨事件循环复用可报错或等待不被唤醒。**  
   [fallback_sync_service.py:74](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/services/fallback_sync_service.py:74)，关联 `:100`。

   **负控输入：**同一进程先在 loop A 发生锁竞争，再在 loop B 竞争；纯内存实测第二个循环抛 `bound to a different event loop`。跨线程双循环负控还观察到释放后等待者未被及时唤醒。

   **对照输入：**同一循环内正确串行化，持锁任务或等待者取消后可以重新取得锁。因此这是多循环条件 MEDIUM，不能据此宣称通常单 ASGI worker 会死锁。

   **最小改法：**限定服务与锁属于一个生命周期／循环并拒绝跨循环调用；若必须支持多循环，可用非阻塞的进程内互斥入口，竞争时明确返回 busy。不能每个循环各建一把锁，否则恢复原来的并发覆盖路径。

7. **MEDIUM — 新增 finalize 提前返回缺少错误状态，启动汇总仍可能报正常完成、零待回灌。**  
   [fallback_sync_service.py:360](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/services/fallback_sync_service.py:360)，关联 `:380`、[main.py:438](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/main.py:438)。

   **负控输入：**51 条全部成功，期间追加第 52 条，finalize 重读抛 `OSError`；实测返回 `{"recovered":51,"pending":0}`，文件仍保留全部 52 条。返回没有 `error`，启动聚合遂进入正常完成分支。清游标失败的提前返回也有同样问题。

   **最小改法：**返回明确的 finalize 失败状态并让消费者识别；无法读取新增记录时，待处理总数应表示未知，不能把它确认为零。

8. **MEDIUM — r6 的错误 vault 归属门仍可假绿。**  
   [test_neo4j_replay_wire_t6b.py:429](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/tests/integration/test_neo4j_replay_wire_t6b.py:429)，关联 `:430–435`。

   **未被拦下的输入：**Concept 与 LEARNED 同时属于错误非默认组 `vault__other__wrong`，其余字段和数量正确，全部归属断言通过。

   **最小改法：**夹具明确来源 vault，独立构造预期物理组并精确比较；不能调用被测归属函数计算期望值。

对问题 ⓪ 的直接结论：

| r6 修复 | 本轮核验 |
|---|---|
| HIGH-2：整次回灌互斥 | **同一事件循环内原路径关闭。** 多循环见第 6 项，跨进程仍未覆盖。 |
| HIGH-3：重读失败提前返回 | **原 `failed_writes` 数据删除路径关闭。** 保留 checkpoint 合理；跳过旧归档 cleanup 只延后清理。返回状态缺陷见第 7 项。 |
| HIGH-1：先清游标再改写 | **原 `failed_writes` 换代窗口关闭。** 清成功、替换失败时，实测原文件保留且游标已清，下轮从零重放；代价是可能重复 Episode，数据保留方向比原先更安全。 |

另外，`_clear_checkpoint` 读取失败时会尝试删除**整份** checkpoint；删除成功可能让其他链也重新重放，删除失败则上抛。`learning_memories` 不写回、不轮转，**没有 canvas 的同型 finalize 删除路径**；旧游标／排序可能导致某轮漏重放，但文件仍保留。

**建议独立排 Story 38.8 回灌算法重写卡。** 当前问题已经涉及可变快照、位置游标、排序、并发追加、数据库部分成功和确认删除，继续逐处补丁难以建立统一的数据保留保证。独立卡应明确稳定记录身份、来源 vault、成功确认条件和崩溃恢复协议；本接线卡由主 session 裁定止血范围与停车版本。现有门不运行 lifespan，也未覆盖上述故障路径，不能据正常输入通过推定整体安全。

本轮已超过五轮上限；**此复核不撤销 r5 停车裁定，也不替主 session 决定继续整改。**

**计数汇总：BLOCKER 0 / HIGH 5（含既知 G2-2 移交项 1）/ MEDIUM 3 / LOW 0。**


