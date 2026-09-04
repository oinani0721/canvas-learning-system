审查锚点：`HEAD=cee863a03628817af12095e141d4e26cebe14b66`。审查期间工作树持续被 OBS/DEBT-8 会话改动；以下生产反例均在 `nodes.py` 稳定字节下复核，本轮未修改文件。

1. **BLOCKER — 默认组/裸表旁路仍真实可达**

   - `retrieve_lancedb` 检索后固定用裸 `vault_notes` 做邻居扩展：`backend/lib/agentic_rag/nodes.py:397-415`；客户端直接打开该表，未走作用域解析：`backend/lib/agentic_rag/clients/lancedb_client.py:2203-2243`。
   - 真实 tmp LanceDB 中，A 的前缀表包含链接、裸 `vault_notes` 仅放 B secret；以 `vault:vault_a` 执行生产节点，结果仍返回 `lancedb_b_neighbor`，且 `channel_errors={}`。
   - 当前 vault 前缀表缺失时还会兼容回退裸 `canvas_nodes`：`lancedb_client.py:732-759`。同样以 A scope 实测读到只存在裸表中的 B 内容。
   - grep 三文件零命中只能判语法门 PASS，不能证明语义隔离。
   - 另有 HIGH 子项：Graphiti 节点先生成 legacy subject/canvas 值，生产客户端又从进程级 vault 重建物理组：`nodes.py:238-256`、`graphiti_client.py:381-420`。新增测试只截获 stub 前参数：`test_agentic_rag_vault_scope.py:189-217`，证明不了真实组一致性。此处实证为二级组错桶，不扩大声称为 `/rag/query` 跨 vault 泄漏。

2. **HIGH — 非空 409 语义正确，但空白值绕过 422**

   - 三别名和唯一解析点本身 PASS：`rag.py@HEAD:304-308`、`backend/app/core/vault_scope.py:103-182`。稳定 ID、环境别名、目录 basename 均实测 200，foreign vault 为 409，没有二次解析。
   - 但请求模型只有长度约束：`rag.py@HEAD:51-58`；解析器把纯空白当成缺失并推导 active vault：`vault_scope.py:162,191-204`。
   - 真实路由结果：缺字段/空串为 422，但 `"   "`、制表符加换行均为 200，且进入了 RAG 服务。现有 API 测试只覆盖空串：`test_rag_vault_scope_api.py:119-123`。
   - 因而验收单“不带库名被拒”声明不成立：`UAT...md:40-43`。

3. **BLOCKER — 双 vault fixture 不是同组假绿，但不能证明 full RAG 隔离**

   - 局部 fixture 设计 PASS：同一 tmp 库创建 `vault_a_canvas_nodes`、`vault_b_canvas_nodes`，表名符合 `DEFAULT_TABLES=["canvas_nodes"]`：`test_agentic_rag_vault_scope.py:303-352`、`lancedb_client.py:581-584`。
   - B 独有、A 正向、同名异内容、反向检查都存在：`test_agentic_rag_vault_scope.py:395-447`。
   - 但 fixture 没有裸 legacy 表，也没有 wiki-link，所以上述两条生产旁路不会变红。当前 15 API + 15 unit 虽为 `30 passed`，仍与真实跨库反例同时成立。
   - 因此测试本身不是假 fixture；`UAT...md:28-34,56` 将其提升为“杜绝 A 查到 B”的全链结论，属于 BLOCKER 级过度声明。

4. **HIGH — agents 偏离披露显著，但理由和覆盖声明不实**

   - 双缺失推导 active vault 确实在显著位置披露，且模型仍 Optional：`UAT...md:9-22,92-95`、`backend/app/core/vault_scope.py:191-208`。这一子项 PASS。
   - “插件 agents/dialog 依赖”被仓库事实反证：插件明确记录该命令及不存在的端点已删除：`frontend/obsidian-plugin/src/main.ts:360-366`。
   - 实际只有 7 个 resolver/header 调用点，不是验收单声称的 8 个；12 个公开 POST handler 注入 Response 则成立：`agents.py:790-795,908-913,1029-1034,1180-1185,1705-1710,1830-1835,2078-2083`，对照 `UAT...md:113`。
   - “每个 agents 请求都有头”也过宽：health 无该机制：`agents.py:267-283`；409 明确没有头：`test_rag_vault_scope_api.py:398-402`。
   - 签名适配漏掉 tracked 测试：`agents.py:2043-2047` 对比 `test_recommend_action.py:270,289,305,328,351,367,391,418,447,472`。独立复跑结果为 **10 failed, 30 passed**，均是旧二参数直调错误；裁判 2 的 `-k 'rag or agents'` 没选中该文件。

5. **HIGH — 三处“与卡文偏差”披露不完整**

   - **a. HIGH：**运行时确为响应头而非响应体：`agents.py:760-795`；实际映射也正确：`explicit→request-vault`、`legacy_group_id→legacy-group`、`derived_active→active-vault`，见 `test_rag_vault_scope_api.py:349-396`。但验收单没有“与卡文偏差”段，没有逐对映射，也没有说明该 header 未进入响应 schema/OpenAPI 契约；`UAT...md:84-120` 直接跨过了这些说明。
   - **b. PASS：**`current_vault_id()` 对 `vault:default` 返回 `default` 而不抛：`vault_scope.py:294-318`；测试和验收单均如实锁定：`test_agentic_rag_vault_scope.py:168-186`、`UAT...md:140-144`。
   - **c. HIGH：**两处点名适配本身是最小机械修改：`test_rag_four_state_api.py:31-43,93,417`、`test_agents_learning_event.py:25,348,386,435,471,506,581`。但 `UAT...md:114-115` 只列文件，未按偏差说明；且适配集合并不完整，`test_recommend_action.py` 已产生 10 条回归。

6. **HIGH — OBS 失败排除成立，但并发声明和交付状态不成立**

   - 排除 `test_nothrow_logging_api.py` 后零新增失败可复算：`baseline-judge2.txt:556` 为 77 passed；`after-judge2-v2.txt:745-748` 只有该 OBS 文件 3 fail，其余 92 passed。此子项 PASS。
   - 但 OBS 卡要求 G4-4 独立提交后且工作树干净才开工：`W8-3.md:4-10`；当前证据显示其测试已在 G4 收官裁判中被收集：`after-judge2-v2.txt:13`。
   - `UAT...md:59-63` 承认并发，`:151-153` 又称 OBS 将按排程后开；`:60` 还把 `d6a5e697` 错归 OBS，实际该提交是 CARD-DEBT-8。
   - 当前 HEAD 不含 `test_rag_vault_scope_api.py` 和 G4-4 UAT，两者仍为 untracked；这与卡文交付要求 `W8-2.md:46-47,69-76` 及 `UAT...md:5,116` 的“本验收单 commit”冲突。clean HEAD 无法重放完整验收。

另有 **HIGH 证据缺陷**：`mutation-run.txt:10` 的 M5 是 pytest `exit=4`（usage error），不是指定测试红；脚本丢弃 stdout/stderr并把任意非零当作 kill：`g44_mutations.py:22-31,106-115`。而且 M5 只改告警文本，没有把 warning 降为 debug：`g44_mutations.py:97-104`。`UAT...md:55` 声称另有 exit=1 复跑，但没有归档证据。因此“5/5 各杀指定门”不成立。

总结论：**REJECT**（存在两条可复现的生产跨 vault BLOCKER，另有多项 HIGH 契约、回归与证据完整性问题）。


