> 批次: BATCH-2026-09-11-第十四批 · 车道 T6 · 卡 CARD-NEO4J-REPLAY-WIRE round-6
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-NEO4J-REPLAY-WIRE-r6.md)"`
> 审查绑定: `962d86c698e21950cb1df3e81d94150b3322ae0a`（⚠️ **已对最终 HEAD 失绑**：审查期间车道提交了 `c667b1eb`，本轮结论仅作参考）
> 会话头自证（抄 .stderr 第 2/5/9 行含 model 行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`

---

**`962d86c6` 仍有 HIGH，不能判定闭环。** r5 的连续前缀负控与回填异常阻断已修复，但另有三条数据丢失路径。

审查绑定 `962d86c698e21950cb1df3e81d94150b3322ae0a`；期间 HEAD 已推进至 `c667b1eb`，以下结论不覆盖新提交。证据为源码复核与纯内存 AST 状态推演，未改文件、未连接数据库。

1. **HIGH — 压缩文件后，旧 checkpoint 可跳过尚未成功的记录。**  
   [fallback_sync_service.py:323](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/services/fallback_sync_service.py:323)，关联 `:330、:675–676、:273–275`。

   **负控输入：**前 50 条成功、第 51 条失败；保存 `index=50` 后，将文件压缩为仅剩第 51 条，在清除 checkpoint 前中断。重启接受当前版本的旧游标，跳过唯一记录并进入轮转。**对照输入：**清除 checkpoint 后重启，会重试该记录。

   连续前缀只证明原快照中的下标，版本标记没有绑定文件代际。最小修法是在压缩／轮转前可靠持久化游标重置，重置失败则停止改写。仅增加下标范围检查不足以解决所有文件代际错配。

2. **HIGH — 并发回灌的旧快照可覆盖新追加记录。**  
   [fallback_sync_service.py:314](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/services/fallback_sync_service.py:314)，关联 `:233、:306、:321–326`。

   **负控输入：**A、B 均初读 `[x,y]`；A 成功处理 x、保留失败 y，写回 `[y]`；随后追加 z，文件成为 `[y,z]`。B 仍使用旧快照 `[x,y]`，因两边长度同为 2，判断没有追加，写回 `[y]`，z 从未重放却被删除。**对照输入：**串行执行时，新追加的 z 能被读取或保留。

   新端点允许调用服务，整次回灌没有互斥；两个局部文件锁未覆盖 `await` 窗口。最小改法是在服务层串行化完整回灌过程。此项不依赖 checkpoint 或进程中断。

3. **HIGH — finalize 重读失败后继续覆盖，可能删除未知追加记录。**  
   [fallback_sync_service.py:318](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/services/fallback_sync_service.py:318)，关联 `:321–326`。

   **负控输入：**初始 `[x,y]`，x 成功、y 失败，重放期间追加 z；末尾重读抛 `OSError`，但后续文件替换成功。异常分支留下 `new_lines=[]`，最终写回 `[y]`，z 消失。**对照输入：**重读成功则保留 `[y,z]`。

   单次回灌即可触发，独立于前两项。最小改法是重读失败立即终止 finalize，保留原文件与 checkpoint。这属于回灌侧的数据保留逻辑。

4. **MEDIUM — 错误 vault 仍可让归属门假绿，r5 登记项未关闭。**  
   [test_neo4j_replay_wire_t6b.py:429](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/tests/integration/test_neo4j_replay_wire_t6b.py:429)，关联 `:430–435`。

   **未被拦下的输入：**Concept 与 LEARNED 同时落入错误的非默认组 `vault__other__wrong`，评分、时间戳和数量正确，现有归属断言全部通过。**对照输入：**两者精确等于测试指定 vault 对应的物理组。

   可以作为**开放 MEDIUM**交主 session 裁定，但不能当作正确 vault 归属已验收。若要证明该性质，最小修改仅涉及本测试及配置夹具：明确测试 vault，独立构造预期 group，作精确相等断言；不要复用被测 `_build_group_id_from_canvas()` 计算期望值。

对指定问题的其余结论：

- **⓪ 循环内不变式成立。** `contiguous_end == i` 对非零续跑起点正确；畸形行、返回 `False`、捕获异常均卡住前缀。保存守卫没有新增漏存问题；不足 50 条时中断、以及失败点之后的成功条目，仍可能重复处理。r5 原负控得到 `saved=[]`，但不能覆盖第 1 项持久化窗口。
- **① 旧标记回退有效，但完整安全性未确认。** 无标记、旧 `line_split`、`progress_version="split-lf"` 均回退 0；当前标记仍放行第 1 项中的合法旧游标。另两条 JSON 链的循环体不在原允许读取面内，补读请求尚未获回复，因此不能确认其历史推进语义或整体重放安全性。
- **② 普通回填异常已解耦。** [main.py:396](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/main.py:396) 的内层 try 覆盖参数构造、回填调用和结果日志；异常处理正常返回后继续到 `:423` 回灌。`CancelledError`、`SystemExit` 等退出／取消异常不被捕获，属于合理传播。
- **门未覆盖的路径：**现有 checkpoint 测试没有覆盖压缩与清游标之间中断；集成门没有覆盖上述并发、重读故障，也不运行 lifespan。前三项均为本卡生产接线暴露的既有缺陷，并非全部由 r6 新增。

本轮超过五轮上限的事实不变；此复核不替主 session 撤销 r5 停车裁定。

**计数汇总：BLOCKER 0 / HIGH 3 / MEDIUM 1 / LOW 0。**


