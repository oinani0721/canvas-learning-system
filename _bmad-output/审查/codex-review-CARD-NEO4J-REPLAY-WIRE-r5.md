> 批次: BATCH-2026-09-11-第十四批 · 车道 T6 · 卡 CARD-NEO4J-REPLAY-WIRE round-5
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-NEO4J-REPLAY-WIRE-r5.md)"`
> 审查绑定: `ccb1d1015c8430914498ad633afc0081b7c33011`（= 最终 HEAD；该轮仍报 HIGH 1 ⇒ 配额 5/5 用满，按 D-15 停车交主 session 人审）
> 会话头自证（抄 .stderr 第 4/7/11 行含 model 行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`

---

**本轮发现 HIGH 1：应按 D-15 停下车道，交主 session 人审。** r4 的分行错位路径已关闭，但回填与回灌的依赖仍未解除。

审查绑定 `ccb1d1015c8430914498ad633afc0081b7c33011`；结束时 HEAD 未变，四个受审文件与该提交一致。仅做源码复核和 Python 纯内存实验，未修改文件、未连接数据库。

1. **HIGH — checkpoint 将“已尝试”当成“已成功”，重启跳过失败记录。**  
   [fallback_sync_service.py:282](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/services/fallback_sync_service.py:282)，关联 `:259–261、:275、:278、:660–661`。  
   **负控输入／复现思路：**51 条合法记录，第 1 条失败、第 2–50 条成功；保存 `index=50` 后，在第 51 条的 `await` 期间中断。第 1 条仅留在内存 `still_pending`，重启接受带新标记的 checkpoint，直接跳过它。纯内存结果：`重启尝试=[51]，从未成功却被跳过=[1]`。**对照输入：**前 50 条全部成功，此时游标才安全。  
   这是**本卡新增生产接线暴露的既有算法缺陷，非 r5 新引入**。当前单条成功记录门未覆盖“部分失败＋中断＋恢复”。本轮独立证实漏回灌，未实测最终轮转删除。

   **最小改法及边界：**checkpoint 只能推进到连续成功前缀，不能越过最早失败或畸形行；仅增加“当前条成功才保存”仍不够。还需增加进度语义版本，处理包括当前 `split-lf` 在内、无法证明前缀成功的历史游标。范围为回灌与 checkpoint 恢复逻辑；旧游标回退可能重复评分 Episode，须由主 session 裁定迁移取舍。

2. **MEDIUM — `_worker_online` 仍依赖回填成功，r4 MEDIUM-3 未关闭。**  
   [main.py:410](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/main.py:410)，关联 `:398、:427、:464`。  
   **负控输入／复现思路：**已取得非空 `_worker_graphiti`，但 `backfill_vault()` 抛异常；`:410` 不执行，独立回灌块仍走离线计数。回填结果日志取键失败也一样。  
   最小改法是在确认 `_worker_graphiti is not None` 后、构造回填参数和执行回填之前设置状态。取到 worker 之前失败时保留默认 `False`，可作为保守策略。现门不运行 lifespan，故这仍是**门未覆盖的路径**。

3. **MEDIUM — 门只验证 group 格式，错误 vault 仍可假绿。**  
   [test_neo4j_replay_wire_t6b.py:429](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/tests/integration/test_neo4j_replay_wire_t6b.py:429)，关联 `:430–435、:325–345`。  
   **负控输入／复现思路：**Concept 和 LEARNED 都落入错误的非默认组 `vault__other__wrong`，评分、时间戳和节点数量保持正确，当前所有归属断言仍通过。  
   最小改法是明确测试 vault，并用独立预期值核验实际 group；直接复用被测 `_build_group_id_from_canvas()` 计算期望值，仍可能同错同绿。这证明门存在缺口，不代表已证实生产跨 vault 写错。

其余指定问题：

- **⓪(a) 分行长度判据在当前调用前提下可靠。** `read_text()` 统一 CR，随后 `strip()` 去掉尾部分隔；此后 `splitlines()` 只能增加 LF 之外的切点。一般字符串 `a\u2028b\n` 确有“等长但切片不同”，但生产预处理排除了它。纯内存枚举得到 4,714 组等长输入，切片不同为零；r4 U+2028 负控回退 0，普通对照保留 50。
- **⓪(b) 重新计算没有重新读取暂存文件。** loader 使用同一不可变 `raw`，初读至加载 checkpoint 之间无 `await`，未发现新增的同事件循环竞态。这不能扩大为跨线程、跨进程的整体同步保证。
- **⓪(c) 两条 JSON 链不能在指定读取面内完整核实。** 实际解析和 loader 调用主体未包含其中；只能确认 `raw=None` 会沿用下标，不能把作者注释当成独立证据。
- **① 异常覆盖和顺序未见新增回归。** 新 `try` 覆盖 import、工厂调用、回灌与统计；成功路径仍先回填再回灌。明确问题是上述状态赋值位置。
- **② run ID 整改有效。** 未发现清理或计数遗漏旧固定身份。独立进程／xdist worker 各自生成 ID；同进程常规顺序重复执行有逐用例清理和独立 seed UUID，不能仅凭模块常量复用判为缺陷。标签绑定与读取失败 warning 两项 r4 LOW 已关闭。

**计数汇总：BLOCKER 0 / HIGH 1 / MEDIUM 2 / LOW 0。**


