> 批次: BATCH-2026-09-11-第十四批 · 车道 T1 · 卡 CARD-G2-9-F2 round-6
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G2-9-F2-r6.md)"`
> 审查绑定: `08100483..675bfd70`（= 本卡最终 HEAD 的代码树；主 session 2026-09-14 在 D-15 上限之外额外授权本轮，专修 r5-HIGH-1）
> 会话头自证（抄 .stderr 中含 codex 版本行 + `model:` 行 + `reasoning effort` 行的三行，括注行号；stderr 本身不入库）:
> `L4: OpenAI Codex v0.153.3` / `L7: model: gpt-6-astra` / `L11: reasoning effort: ultra`

---

**r5-HIGH-1 在本轮目标形态上已闭合；未发现本卡新增 HIGH。** 仍有基线既有的 HIGH 边界，以及以下 MEDIUM／LOW。

审查绑定 `08100483..675bfd70`，结束时 HEAD 及两个被审文件仍与目标提交一致。仅做源码审查和抽取表达式的内存运算；未修改文件、未连接数据库或网络、未运行 pytest，因此不将作者的 NC18 记录视为本轮实测结果。

[BLOCKER] 该级别无。

[HIGH] 余名恰为规范逻辑名时仍可能误删，但与基线同态，属于已登记边界。
  [lancedb_client.py:1547](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-lance/backend/lib/agentic_rag/clients/lancedb_client.py:1547)、[lancedb_client.py:1401](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-lance/backend/lib/agentic_rag/clients/lancedb_client.py:1401)
  复现思路：`a_canvas` 的目录不可见、没有指纹表，其逻辑表 `nodes` 形成 `a_canvas_nodes`；查询 vault `a` 时，余名 `canvas_nodes` 正好放行，自愈和删索引均可能处理该表。
  **非本卡回归。** 扩大拒绝范围可以阻止此例，但会同时拒绝合法的 `a/canvas_nodes`；要可靠区分，需要表级归属或权威登记信息。

[MEDIUM] r6 新闸会持续跳过真实属于本 vault 的历史自定义表。
  [lancedb_client.py:1540](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-lance/backend/lib/agentic_rag/clients/lancedb_client.py:1540)、[test_lancedb_cross_vault_drop_g29f1.py:1419](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-lance/backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py:1419)
  复现思路：vault `a` 可正常发现，保留此前配置产生的漂移表 `a_legacy_nodes`，当前配置已改回 `canvas_nodes`；每次启动均跳过该表，即使 V 完整也不会恢复自愈。
  **这是 r6 新增的可用性回归。** 新门只证明当前规范名 `canvas_nodes` 仍被处理，不能覆盖历史名。准确后果是“持续失去启动自愈”，不是所有修复入口都永久失效。

[MEDIUM] default 的裸表归属不依赖 V，却被清单降级闸停止自愈和清理。
  [lancedb_client.py:1526](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-lance/backend/lib/agentic_rag/clients/lancedb_client.py:1526)、[lancedb_client.py:1350](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-lance/backend/lib/agentic_rag/clients/lancedb_client.py:1350)
  复现思路：正常数据库含漂移裸表 `notes` 和 `file_fingerprints`，客户端为 `"default"`，但配置的 `VAULTS_ROOT` 不可达；列表仍返回裸表，自愈却全部跳过，删除返回 0。
  **相对 B14_BASE 新增，非 r6 新增。** 这是操作被拒绝，不是归属恒空；当前 default 测试提供有效 root，未覆盖此组合。

[MEDIUM] 指纹后缀反推仍能被配置表名制造出的伪 vault 干扰。
  [lancedb_client.py:1026](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-lance/backend/lib/agentic_rag/clients/lancedb_client.py:1026)
  复现思路：vault `a` 配置逻辑表名 `x_file_fingerprints`，产生 `a_x_file_fingerprints`；来源③反推出不存在的 `a_x`，最长前缀将该表判离 `a`，删除碰撞预检随即拒绝。
  r5-M2 仍未闭合，维持移交。显式并入被查询 vault 只能保证认领集合不超出朴素前缀，**不能保证真实属于自己的表不会失去认领**。

[MEDIUM] API 仍混淆拒绝、全部失败与无表，部分失败也不返回失败明细。
  [index.py:107](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-lance/backend/app/api/v1/endpoints/index.py:107)
  复现思路：全部删除抛错或触发整次拒绝，均得到 “No tables found” 的 404；部分成功则返回 200，但不带 `_last_drop_failures`。
  按本轮边界，这是**消费端移交项**。实际调用方仍仅该 API 和 canary；canary 的 `lancedb_drop_attempted` 字段名称也已落后于返回语义。

[LOW] r6 后，测试说明中的“前提门与隔离门一起红”不再成立。
  [test_lancedb_cross_vault_drop_g29f1.py:591](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-lance/backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py:591)
  复现思路：退回朴素前缀或打空 V，归属前提变红，但模糊名闸仍能保住 `a_b_canvas_nodes`，cache 隔离断言可以继续通过。

三段负控按当前代码的**静态红点**如下，不能混称为同一层证据：

| 负控 | 首个关键红点及其含义 |
|---|---|
| 退回朴素前缀，保留完整 V | 前提门 `:618` 红；双向门可到 `:783`，因整次拒绝导致自己的表未删而红 |
| V 打空／仅留 active | 双向门在 `:744` 的集合前提先红，尚未执行四个行为场景 |
| 恢复吞错＋返回尝试数 | 记账门在 `:862` 的返回值断言先红；`:867` 的失败记录断言尚未执行 |

因此三者可按位置区分，但第三段的红点不能独立证明失败记录断言有效。仅删除 r6 新条件，按控制流会使新门 `:1415` 的长 vault 表保留断言变红。

其余问题的核对结果：

- **r4-H1／H2／H3：**常见缺项形态现已覆盖两个入口；降级时两个入口均停止破坏操作；正常操作强刷并钉住 V，TTL 不再在中段重算。r6 自愈与 drop 的模糊名判据语义一致，分别采用“跳过该表”和“整次拒绝”。
- **V 仍不保证完整：**目录移走、`.obsidian` 消失、嵌套或根外目录、YAML 读取失败后回退目录名，都可能扫描成功却缺项。正常 YAML 显式 id 已与 Settings 对齐；空 vault 只要目录合格便进入 V。根目录或指纹枚举失败会降级；没有指纹表的 vault 无第三来源兜底。
- **TTL：**旧 vault 的目录或标记恢复、挂载恢复即可形成陈旧窗口，无需等待新索引。读侧仍有五秒窗口；当前破坏路径已强刷，源码也已撤回“五秒内不可能有表”的论证。
- **default／命名：**三态归属保持基线；裸 `canvas_nodes`、`default_nodes` 无人认领是既有规则。`resolve_table_name` 当前仍用纯前缀幂等守卫，生产确有二次解析，但没有本卡新增双前缀。
- **其他修复入口：**启动路径没有第二个绕过选表循环的入口；`add_documents:4383` 仍直接调用维度修复，不受新闸控制。这条写入入口与基线同态。
- **分页与正向对照：**读回使用显式大分页；生产优先全量枚举。页外自家表删除对照能够发现回退默认十张的问题。r6 自家漂移表消失、长 vault 表及句柄保留的组合，能排除“整段自愈没执行”的假绿，但不覆盖历史逻辑名。
