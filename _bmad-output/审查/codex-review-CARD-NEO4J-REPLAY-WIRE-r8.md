> 批次: BATCH-2026-09-11-第十四批 · 车道 T6 · 卡 CARD-NEO4J-REPLAY-WIRE round-8
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-NEO4J-REPLAY-WIRE-r8.md)"`
> 审查绑定: `a66316dffd70779645842ebd68f2e2ce761537d7`（本轮首次按来源分类计数：本卡修复遗漏 1 / 既有算法重写项 1 / 既知 G2-2 移交 1）
> 会话头自证（抄 .stderr 第 2/5/9 行含 model 行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`

---

**`a66316df` 仍不能判为 `HIGH = 0`：确认 HIGH 3 条，其中本卡修复遗漏 1 条、既有算法重写项 1 条、既知 G2-2 移交项 1 条。**

审查始末 HEAD 均为 `a66316dffd70779645842ebd68f2e2ce761537d7`，分支为 `card/t6-neo4j`，所审代码未变化。依据限定读取面、并行交叉复核及纯内存 AST／锁竞争核验；未改文件、未连接数据库。

1. **HIGH〔本卡修复遗漏〕— 评分“成功条件”改变，但旧 checkpoint 仍被接受。**  
   [fallback_sync_service.py:796](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/services/fallback_sync_service.py:796)，关联 `:57、:302–304、:330–331、:636–646`。

   **负控输入：**r7 前 50 条 LEARNED 成功，其中一条评分历史失败仍返回 `True`；保存 `index=50, progress_version="split-lf+contiguous"` 后，在第 51 条中断。升级 r8 后，该标记仍有效，缺历史的条目被跳过，最终随文件轮转退出回灌队列。

   原版本判断和跳过分支的 AST 核验结果是：**仅尝试第 51 条**；使用不兼容标记的**对照输入**则从第 1 条开始。新的 `False` 分支修好了重新执行的记录，覆盖不到已被旧游标跳过的记录。

   **最小止血：**作废按旧评分成功条件生成的 `failed_writes` checkpoint。此项不需要等待整套算法重写。

2. **HIGH〔既有算法，应归独立重写卡〕— 缺 timestamp 的旧记录重试时获得当前时间，可以覆盖新评分。**  
   [fallback_sync_service.py:566](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/services/fallback_sync_service.py:566)，关联 `:593–596`；learning 同型位置为 `:703、:727–731`。

   **负控输入：**旧条目 `score=10` 缺少 timestamp，首次 LEARNED 成功、评分历史失败而保留 pending；期间线上写入较新的 `score=90`；重试旧条目时重新取 `now()`，通过 `<=` 更新条件，将 90 覆盖为 10。

   **对照输入：**提供固定的真实旧 timestamp，较新的数据库评分受到保护。`learning_memories` 保留源文件，重复回灌无 timestamp 条目也有同型覆盖路径。

   这是既有默认时间与冲突处理算法的问题，由本卡接线及重试路径暴露；**不应撤回历史失败返回 `False` 的修复**。上述为源码表达式与更新条件核验，未声称观察到实库覆盖。

3. **HIGH〔既知 G2-2 移交〕— 回灌归属仍取当前 vault，不能证明来源 vault。**  
   [fallback_sync_service.py:963](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/services/fallback_sync_service.py:963)，关联 `:573、:659、:708、:948–950`。

   **负控输入：**A 留下暂存条目后切到 B，再触发回灌；归属由当前 ContextVar／active vault 构造，条目来源不参与判断，因而可能写入 B。

   与 r7 相同，属于已明确移交的风险，非本轮新增。

4. **MEDIUM〔既知移交，本轮扩展同型路径〕— finalize 返回值仍可能把剩余记录报告成零。**  
   [fallback_sync_service.py:477](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/services/fallback_sync_service.py:477)，关联 `:360、:380、:460、:462–463`及 [main.py:438](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/main.py:438)。

   **负控输入：**x 全部成功，重放期间追加 z；本轮 finalize 正确保留 `[z]`，却返回 `recovered=1,pending=0`，因为 pending 没有计入 appended。纯内存核验已得到该结果。

   重读失败提前返回缺少 `error` 的既知路径也仍存在。这是状态报告缺陷，与第 1 项的实际遗漏分别计级。

5. **MEDIUM〔既知移交〕— 模块锁跨事件循环复用仍会失败。**  
   [fallback_sync_service.py:74](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/services/fallback_sync_service.py:74)，关联 `:100`。

   **负控输入：**同进程先在 loop A 发生锁竞争，再在 loop B 竞争；本轮纯内存实测第二个循环报 `bound to a different event loop`。同一循环的**对照输入**正常，不据此推定通常单循环部署会死锁。

6. **MEDIUM〔既知移交〕— 错误非默认 vault 的归属门仍可假绿。**  
   [test_neo4j_replay_wire_t6b.py:429](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/tests/integration/test_neo4j_replay_wire_t6b.py:429)，关联 `:430–435`。

   **未被拦下的输入：**Concept 和 LEARNED 同时属于错误非默认组 `vault__other__wrong`，其余字段、数量正确；现有归属断言全部通过。仍需独立确定预期来源组并精确比较。

对前四条修复及具体问题的结论：

| 核验对象 | 结论 |
|---|---|
| r7 HIGH-1：canvas 位置与快照失配 | **原路径关闭。** canvas 已没有 checkpoint 调用。 |
| r7 HIGH-2：接受旧 canvas 游标 | **原路径关闭。** 旧标记和下标不再影响该链。 |
| r7 HIGH-3：覆盖重放期间新增事件 | **所述追加路径关闭。** 初读 `[x,y]`、x 成功、y 失败、追加更早时间的 z，核验保留 `['y','z']`；重读失败在改写前返回。 |
| r7 HIGH-4：评分历史失败仍出队 | **新执行路径关闭，升级路径未关闭。** 捕获异常及明确返回 `False` 均保留 pending；旧 checkpoint 漏口见第 1 项。 |

- **接近 10,000 条的重启重放：**增加重复数据库操作及启动等待；反复崩溃会反复执行前缀。限定源码未显示由禁用游标新增的删除路径，但本轮没有实测 10,000 条耗时，也没有独立核验读取面外的写侧上限。
- **完全相同事件的指纹：**初读快照中的两份仍会各重放一次；指纹只影响追加判定。成功 x 后追加相同 x，会消去新增副本；失败 x 后追加相同 x，会保留一份。对恢复相同图身份状态的语义，这不足以构成新的丢失 HIGH；它不保证逐份事件次数或审计历史。客户端 MERGE 实现不在允许读取面，不能据作者注释认证全部数据库幂等行为。
- **LEARNED 重试：**固定 group、timestamp、score 时，所示查询具备重复执行的幂等性；不能无条件声称幂等，缺 timestamp 的反例见第 2 项。
- **`learning_memories`：**仍不写回、不轮转源数据，**没有 canvas 同型 finalize 删除路径**。排序与旧位置游标仍可能造成当轮漏重放；正常清游标后，下轮可以重新处理保留文件。第 2 项属于图内评分覆盖问题。

canvas 重读至改写之间没有 `await`，因此未把未经证明的线程／跨进程竞争新增为 HIGH。现有集成门不运行 lifespan，第二次调用又依赖首次文件已轮转；这些属于**门未覆盖的路径**，不能证明启动、崩溃恢复及部分成功重试安全。

本轮已超过五轮上限；此复核不撤销此前停车裁定，也不替主 session 决定继续整改。

**计数汇总：BLOCKER 0 / HIGH 3 / MEDIUM 3 / LOW 0。**  
**其中：既知移交项 4 条（HIGH 1、MEDIUM 3）；既有算法应归独立重写卡 1 条（HIGH）；其余为本卡修复遗漏 1 条（HIGH）。**
