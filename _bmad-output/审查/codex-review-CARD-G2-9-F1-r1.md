已完成只读静态审查，未执行测试、连接数据库或网络。三份工作区文件均与 `a78b49b7` 对应 blob 一致。以下区分实际风险、覆盖缺口与未核实项。

1. **[HIGH] [lancedb_client.py:876](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance/backend/lib/agentic_rag/clients/lancedb_client.py:876) — 条件性残留风险（问题⑥）。** 若允许 `a` 与 `a_b` 两个 vault 并存，`a_b_canvas_nodes.startswith("a_")` 为真，A 的启动检查仍可能删除 B 的漂移表；四门均未覆盖这种前缀重叠。给定读取面没有排除此命名组合的约束，因此不能认定隔离缺陷已全面闭合。

2. **[MEDIUM] [lancedb_client.py:3708](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance/backend/lib/agentic_rag/clients/lancedb_client.py:3708) — A1：启动路径未发现问题，另一调用方未核实。** 改动确有必要，否则页外表仍被存在性检查挡回；但它也使 `add_documents` 针对页外表开始执行既有删除条件，不能声称行为不变。实际调用点约在 `3822`，超出指定范围，无法核实其表名绑定及后续处理是否安全。

3. **[MEDIUM] [lancedb_client.py:839](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance/backend/lib/agentic_rag/clients/lancedb_client.py:839) — 问题②存在枚举边界。** 无 `list_tables` 且库超过 10,000 张表时，fallback 仍会截断，不能称任意规模的“全量”；这是既有 helper 的限制。`list_tables(limit=None)` 的 SDK 实现，以及 `drop_vault_tables` 主体和调用方均不在指定读取面，故“0.30.2 两分支均安全”和“没有调用方依赖旧分页行为”均未核实。

4. **[LOW] [test_rag_stage1_index_contracts.py:222](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance/backend/tests/regression/test_rag_stage1_index_contracts.py:222) — 问题⑤：源码门确实不证明语义。** 两个字符串出现在注释里也能通过，不能证明实际执行了后缀排除；不过本次生产表达式仍实际执行 `not t.endswith(self.FINGERPRINT_TABLE)`，**未发现这项语义被改坏**。

5. **[LOW] [g29_dual_vault_canary.py:1451](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance/backend/scripts/g29_dual_vault_canary.py:1451) — A3：调用计数仍不承重。** 即使收紧到 `report.get ≥ 2`，删除返回失败的分支也能满足计数；真正承重的是：存在非 PASS 探针结果时返回 `EXIT_ISOLATION_FAILED`，关闭探针时缺键不报错。新增分支符合这一静态控制流；开工计数为 1 的自述未独立核实。

6. **[LOW] [lancedb_client.py:873](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance/backend/lib/agentic_rag/clients/lancedb_client.py:873) — 问题⓪：未发现问题。** `_UNSET = object()` 配合身份判断确实区分省略参数与显式 `None`；`list_vault_tables` 显式透传参数，因此非空 active vault 上的 `list_vault_tables(None)` 仍取裸表口径。门④与既有 `489–490` 契约一致，并增加了正向成员断言。

7. **[LOW] [lancedb_client.py:874](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance/backend/lib/agentic_rag/clients/lancedb_client.py:874) — 问题①／A2：未发现问题。** default 判据与旧实现同语义，没有新增全归或恒空路径；`canvas_nodes` 不归 default 的读法正确。门②保留其存活断言，并新增 `notes` 必须被删除的断言，未因此放宽既有口径。

8. **[LOW] [test_lancedb_cross_vault_drop_g29f1.py:218](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance/backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py:218) — 问题③：未发现问题。** 门③明确断言共有 12 张、默认枚举只有 10 张、`a_t11` 不在默认页内；最终读回使用显式 `limit=10_000`，没有同一分页盲区造成的假绿。

9. **[LOW] [test_lancedb_cross_vault_drop_g29f1.py:134](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance/backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py:134) — 问题④：未发现问题。** A 表按夹具代码具有 `doc_type`、向量为 16 维，客户端期望为 8 维；已读路径没有另一处删除动作解释其消失，因此正向对照支持本 vault 的漂移删除仍会执行，证明范围止于删除，不包括重建完成。

10. **[LOW] [test_lancedb_cross_vault_drop_g29f1.py:246](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance/backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py:246) — 问题⑥：门④在原缺陷存在时确实会绿。** 它承担的是 `None` 兼容契约，不能单独证明隔离修复；门①至③则分别能卡住原始全表删除、default 越界和分页漏检。各门有前提检查，但未全部独立读回 schema；三段负控的实际失败位置及运行前后 SHA 均未提供可核实记录。

11. **[LOW] [g29_dual_vault_canary.py:1245](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance/backend/scripts/g29_dual_vault_canary.py:1245) — A4：未发现问题。** 探针结果参与退出码后，更正“不做判据”的 docstring 恰当；指定 diff 中脚本仅有这三处改动，未发现夹带。

12. **[LOW] [lancedb_client.py:1000](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance/backend/lib/agentic_rag/clients/lancedb_client.py:1000) — 缓存自述部分成立。** 装载循环未改、枚举集合扩大可以直接确认；两个输出读者及“10→12”的实测记录不在读取面，不能独立确认该部分运行结果。

总体判断：已覆盖场景中的修复逻辑成立，但前缀重叠风险尚未排除，A1 的另一调用链及删除调用方尚未核实，不能给出无条件通过结论。
