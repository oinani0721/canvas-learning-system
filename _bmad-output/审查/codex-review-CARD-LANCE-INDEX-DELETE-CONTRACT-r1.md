> 批次: BATCH-2026-09-18-第十五批 · 车道 card-p1-storage · 卡 CARD-LANCE-INDEX-DELETE-CONTRACT round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-LANCE-INDEX-DELETE-CONTRACT.md)"`
> 审查绑定: `3c45f9ad`（该轮送审时的 HEAD；后续整改使其失绑，见验收单 §八 轮次表）
> 会话头自证（抄自 .stderr，括注行号；stderr 本身不入库）:
> `L4: OpenAI Codex v0.153.3` / `L7: model: gpt-6-astra` / `L11: reasoning effort: ultra`

---

**不能认定 (e1) 已完全关闭 r7 的两条误删路径。** 已核对 HEAD=`3c45f9ad`；以下为只读源码复核，未修改文件、未运行测试或 pyright、未连接数据库或网络。

**[HIGH] 指纹表创建失败后，新建内容表仍可能长期缺少归属保护。**  
[lancedb_client.py:2022](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/lib/agentic_rag/clients/lancedb_client.py:2022)、[lancedb_client.py:4695](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/lib/agentic_rag/clients/lancedb_client.py:4695)  
复现思路：目录只能发现 `a`，新 vault `a_canvas` 首次写入 `nodes` 成功，但指纹表创建失败一次；后续追加走已有表分支，不再补指纹，短 vault `a` 的删除或维度自愈仍能误处理 `a_canvas_nodes`。

这属于**本卡之后的新写入**，不属于排除的改前存量。内容先建、指纹后建，也没有消除二者之间的跨连接操作窗口。现有 r7 门只覆盖指纹成功建立后的情况。返回实写行数本身没有伪装成功——内容确实写入；缺陷是安全前提未建立，却未阻止后续破坏性操作。

**[HIGH] 可打开但缺列的真实指纹表会被排除，条件成立时自愈侧仍可能误删。**  
[lancedb_client.py:1134](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/lib/agentic_rag/clients/lancedb_client.py:1134)、[lancedb_client.py:1773](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/lib/agentic_rag/clients/lancedb_client.py:1773)  
复现思路：保留真实 `a_canvas_file_fingerprints`，但其 schema 缺 `chunk_count`，目录只能发现 `a`；形态核排除 `a_canvas` 且不置降级，自愈随后把漂移的 `a_canvas_nodes` 判给 `a` 并删除。

边界必须说清：

- 标准 schema 的空表会保留；列类型不同也会保留，因为没有检查类型。
- 必需列大小写变化会被当成缺列；出现精确小写 `vector` 也会被排除。
- **删除侧通常会被残留指纹表触发的 `ambiguous` 闸挡住，不能把此项说成两侧都会误删。**
- 当前两条写侧都生成标准四列；限定读取面没有证明线上实际存在这种历史 schema。这是明确的未被拦下输入，不是线上事故断言。

**[MEDIUM] “`listing_failed` 只在裸表口径可达”的推理不成立。**  
[lancedb_client.py:1560](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/lib/agentic_rag/clients/lancedb_client.py:1560)、[test_index_delete_contract_c101.py:403](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/tests/unit/test_index_delete_contract_c101.py:403)  
复现思路：scoped vault `a` 在刷新 V 时第一次枚举成功，碰撞预检的第二次枚举才失败，此时闸①已通过，直接返回 `listing_failed`。

现有恒抛输入只能证明**持续故障时**闸①优先，证明不了“only bare”。当前生产分支对此输入能安全拒绝，错误在可达性声明和门的覆盖范围。

**[MEDIUM] 配置恰为 `file_fingerprints` 时，声明的配置冲突终态 409 没有实现。**  
[lancedb_client.py:1177](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/lib/agentic_rag/clients/lancedb_client.py:1177)、[test_lancedb_cross_vault_drop_g29f1.py:1794](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py:1794)  
复现思路：配置 `LANCEDB_INDEX_TABLE_NAME=file_fingerprints`，V 只有 `a`，`a_file_fingerprints` 是普通向量表；该名字虽然被配置守卫判为冲突，却始终存在于 builtin 集合，最终可以删除并返回 200。

相等分支的门只断“结果等于 builtin”，移除该配置守卫分支仍会通过。对于作者举出的 **`custom_file_fingerprints`**，排除伪 vault、随后 `ambiguous` 拒绝的实现与记录则相符。

**[MEDIUM] 207 脱敏门不能拦住携带异常原文的额外响应字段。**  
[test_index_delete_contract_c101.py:271](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/tests/unit/test_index_delete_contract_c101.py:271)、[test_index_delete_contract_c101.py:460](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/tests/unit/test_index_delete_contract_c101.py:460)  
复现思路：负控实现给 207 增加 `debug=client._last_drop_failures`，现有逐字段断言仍成立，而专门脱敏门只检查 409/500，库路径和异常原文便可泄漏而门仍绿。

**当前实现没有这个泄漏字段。** 在现有结构化分支内，未找到普通异常 message 进入 409/500/207 响应体的输入。

**[MEDIUM] 新五态门没有真正验证成功和部分成功时的 `int` 包装返回值。**  
[test_lancedb_cross_vault_drop_g29f1.py:1577](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py:1577)、[test_lancedb_cross_vault_drop_g29f1.py:1598](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py:1598)  
复现思路：负控实现让 `drop_vault_tables` 先执行 report 再恒回 `0`；该门成功、部分成功两格读取的是 `len(report.dropped)`，只有零结果场景调用包装，因此所谓“int 实删数”断言仍通过。

此结论限于新增门⑨，不等于此前全部测试都会通过。

**[LOW] 部分新增断言仍可被丢失诊断内容或记录身份的实现绕过。**  
[test_index_delete_contract_c101.py:275](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/tests/unit/test_index_delete_contract_c101.py:275)、[test_lancedb_cross_vault_drop_g29f1.py:1595](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py:1595)、[test_lancedb_cross_vault_drop_g29f1.py:1912](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py:1912)  
复现思路：分别将失败类型硬编码为 `RuntimeError`、诊断字符串缩成纯类型名、漂移重建改为首条新记录重复三份，对应断言仍会通过；负控应分别使用 `PermissionError`、核对异常原文、核对三个新 `doc_id`。

此外，C101 未直接覆盖 `collision → HTTP 409`；g29 新门覆盖的是 report 层。r7 自愈门又在同一客户端执行 drop 和显式刷新 V 后才运行，未独立覆盖冷启动路径。

**[LOW] “候选数等于 vault 数、启动代价可忽略”超过了源码能支持的结论。**  
[lancedb_client.py:1093](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/lib/agentic_rag/clients/lancedb_client.py:1093)、[lancedb_client.py:1751](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/lib/agentic_rag/clients/lancedb_client.py:1751)  
复现思路：单个 vault 留下多个以指纹后缀结尾的历史配置表，候选数便大于 vault 数；启动先打开全部 T 张表，再刷新 V 重复打开 K 张候选表。

新增成本是每次 V 刷新 **K 次 `open_table + schema`**；普通 TTL 到期也会刷新。正常每次 drop／自愈各强刷一次成立，但是否构成启动瓶颈需要测量，本次没有性能实测。

**[LOW] 五态完备性适用于返回的回执，不能扩大为操作所有异常都得到回执。**  
[lancedb_client.py:1595](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/lib/agentic_rag/clients/lancedb_client.py:1595)  
复现思路：前两次枚举成功，第三次 `list_vault_tables` 枚举失败，异常直接逃出，未转换为五态。

这是基线既有边界。是否经全局异常处理泄漏原文，限定读取面不足以判断。

其余核对结果：

- **五态分类正确**：对生产代码正常返回的回执，互斥且完备；当前 `int` 包装仍返回实删计数。四闸的条件文本、顺序、完整诊断字符串保持不变；但上游 V 和逻辑名集合变了，不能据此宣称实际拒绝集合不变。
- **归属规则零改动属实**；default／空 scope 的新增建指纹钩子确为 no-op。指纹成功建立且被识别后，r7 两侧都受到保护。
- **漂移快照修法有效**：接住守卫返回值后走重建；门断返回数、落盘行数和维度，足以锁住本次“打开刚删掉的表→回 0”缺陷。允许读取段内未发现第二处同族内部状态变更问题。
- **分页翻正有效**：默认页大小、目标在页外、两行及精确两个 `doc_id`、同一 `edge_id` 均有断言，首次记录保留性质没有丢失。
- **Wave5 改写仍有意义**：保留 ContextVar、原始 vault id 转发和状态映射断言；没有冒充实删契约门。
- **没有新增 `pyright: ignore` 或 `type: ignore`**。唯一新增抑制是 [C101:53](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/tests/unit/test_index_delete_contract_c101.py:53) 的 `noqa: E402`，用于先设置 `sys.path` 再导入，理由成立；它不抑制 pyright。未复跑，不能独立确认“pyright 0”。
- 指定裁定文件当前只有 **111 行**，且无 `T1-A` 命中，无法核实所指 `:136` 裁定。
