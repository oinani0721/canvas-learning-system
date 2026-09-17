> 批次: BATCH-2026-09-11-第十四批 · 车道 T1 · 卡 CARD-G2-9-F2 round-3
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G2-9-F2-r3.md)"`
> 审查绑定: `08100483..8583c6b2`（该轮送审时的 HEAD；本卡末轮 r5 绑最终 HEAD `647ef77f`）
> 会话头自证（抄 .stderr 中含 codex 版本行 + `model:` 行 + `reasoning effort` 行的三行，括注行号；stderr 本身不入库）:
> `L2: OpenAI Codex v0.153.3` / `L5: model: gpt-6-astra` / `L9: reasoning effort: ultra`

---

**结论：r2-HIGH-1 的局部整改成立；r2-HIGH-2、r2-HIGH-3 尚未闭合。**

审查绑定 `08100483..8583c6b2`，结束时 HEAD 及两个目标文件仍与末端提交一致。以下依据只读源码、调用链及纯内存归属运算；未修改文件、运行 pytest、连接数据库或网络服务。

BLOCKER：该级别无。

[HIGH] 指纹拒绝闸将枚举异常当成“指纹不存在”，能够重现内容已删、基线遗留。
  [lancedb_client.py:1289](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-lance/backend/lib/agentic_rag/clients/lancedb_client.py:1289)
  复现思路：健康缓存 `V={a,a_file}`，已有 `a_vault_notes`、`a_file_fingerprints`；前置检查的枚举暂时抛错，随后 `list_vault_tables` 枚举恢复，即跳过拒绝、只删除内容表。

这里把“无法确认”转换成空集，后续却再次枚举并执行删除。留下的指纹仍会使未变文件跳过索引。**这是本轮新增前置闸的失败分支漏洞，r2-HIGH-3 未闭合。**

[HIGH] 未标记降级的缺项集合仍会缓存，来源恢复后也可能继续跨 vault 认领。
  [lancedb_client.py:1013](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-lance/backend/lib/agentic_rag/clients/lancedb_client.py:1013)、同文件 `1035–1063`
  复现思路：`a_b` 目录已移走但内容、指纹表都在；首次指纹来源枚举失败，缓存 `{a}`，枚举恢复后在 TTL 内调用 `drop_vault_tables("a")`，仍会把两张 `a_b` 表纳入删除集合。

指纹来源失败只返回空集，没有置降级，故“不缓存降级结果”没有覆盖它。

另有**完全不报错**的到达方式：成功扫描时 `a_b/.obsidian` 暂缺且无指纹，缓存 `{a}`；恢复 `.obsidian` 后立即删 `a`，仍沿用旧集合。表早已存在，无需等待索引，直接否定“五秒内物理上不可能”的理由。**r2-HIGH-2 未闭合。**

[MEDIUM] 指纹专用拒绝闸没有防住内容表之间的拆分，删索引可以返回成功却留下自己的内容。
  [lancedb_client.py:1286](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-lance/backend/lib/agentic_rag/clients/lancedb_client.py:1286)、同文件 `1301`
  复现思路：`V={a,a_vault}`，`a` 已有 `a_canvas_nodes`、`a_vault_notes`、`a_file_fingerprints`；删除 `a` 会通过指纹闸、返回 2，却留下实际由 `a` 写出的 `a_vault_notes`。

这证明“只减少认领别人的表、不减少认领自己的表”不成立。这里确认的是**新增漏删及集合拆分**，没有把它扩大为已证明的永久内容丢失。

两文件内可考虑增加规范内容表的碰撞预检，同时保留现有全量删除集合；这不等于把删除面限制成逻辑表名白名单，不会因此必然打红漂移表正向对照。真正解决非唯一命名仍需额外归属证据。

[MEDIUM] 现有门不能单独证明本轮“目录降级结果不缓存”的整改。
  [test_lancedb_cross_vault_drop_g29f1.py:944](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-lance/backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py:944)、同文件 `1024`
  复现思路：仅撤去生产代码 `1050` 的 `or self._vault_registry_degraded`，连接门仍受 `_db is None` 和连接身份失效保护，拒绝门也没有在同连接、TTL 内恢复目录后再次判断。

因此，这两条门的绿色不能证明该新增分支不可退化。

[MEDIUM] 删除拒绝、全部失败和没有表仍被消费端混为同一个 404。
  [index.py:107](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-lance/backend/app/api/v1/endpoints/index.py:107)
  复现思路：触发任一拒绝闸，API 仍返回 `No tables found`；部分删除失败则仍返回 200，只带成功计数。

直接生产／脚本消费方只找到此处与 `g29_dual_vault_canary.py:783`。`int` 类型兼容，但 `_last_drop_refusal`、`_last_drop_failures` 没有生产消费方。**按本卡边界，这是消费端移交项。**

[LOW] 新拒绝闸对 default 使用了错误的规范指纹名。
  [lancedb_client.py:1286](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-lance/backend/lib/agentic_rag/clients/lancedb_client.py:1286)
  复现思路：库中有裸 `notes`、`file_fingerprints`，另有存量 `default_file_fingerprints`；删除 default 会因后者归属检查而拒绝，尽管真正的 default 基线是裸表。

该反例需要上述存量表；未确认当前固定生产逻辑名会常规生成它，故仅列 LOW。

[LOW] 两文件仍把已删除的等名分支写成现行规则。
  [lancedb_client.py:1181](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-lance/backend/lib/agentic_rag/clients/lancedb_client.py:1181)、测试文件 `43、612`
  复现思路：按文字恢复 `name == vault_id`，会与当前等名防回归门冲突；实际 `_table_owner` 只匹配 `v + "_"`。

其余问题的核对结果：

- **V 的来源边界**：有效 YAML 显式 ID 的优先级和清洗与 `Settings.vault_id` 一致；合格空 vault 不需要任何表即可被目录发现。移走、隐藏、缺 `.obsidian` 的目录会被排除，有指纹才能补回；没有指纹时确与 B14 旧缺陷同态。YAML 读取／解析失败会静默退回目录名，导入配置失败也未设置降级，均可能形成缺项。
- **r2-HIGH-1 局部闭合**：新鲜扫描发现根目录无效或枚举抛错，会阻止显式 drop。启动自愈仍不消费降级标志，不能外推为整个删除面已受保护。对于“从未被发现、又无指纹”的 vault，仅凭表名无法完整消歧；操作前刷新、来源失败拒绝及固定本次候选集可以处理暂态窗口，完整闭合需要额外登记或表归属元数据。
- **误报安全性**：新认领集合是旧前缀集合的子集，但这只能证明“少认领”，不能证明“只少认领别人的表”。内容与指纹可能被拆开，因此“不丢数据”的普遍不对称主张不成立。
- **default 三态与 resolve**：三态本身没有变成全表可见或恒空；`default_*` 无人认领的既有边界不是本卡新增。当前 resolve 已保留纯前缀守卫，存量已解析名不会因最长归属再次加前缀。生产确有 `index_vault_notes → add_documents` 二次解析，当前整改覆盖了它。
- **碰撞拒绝的出路**：`a_file` 碰撞存在时，反复重试不会解除拒绝；需解除 ID 冲突。移除空冲突 vault 可以解除此例，已有数据的 ID 变更则不能把日志里的“改名”直接视为完整迁移方案。

分页与负控的首个失败点如下，均为按当前断言顺序推导，**不是本轮变异测试实跑结果**：

| 退化输入 | 首个失败点及证明范围 |
|---|---|
| `list_vault_tables` 退回默认十张 | page-outer 的 `a_10/a_11` 留下，测试 **681** 首红；整改有效 |
| 指纹存在性检查退回默认十张 | 独立门⑨ **1011** 首红；整改有效 |
| ① 退回朴素前缀 | 门⑤ **618**；门⑥前提通过后在 **753** 红 |
| ② V 只剩 active | 门⑤同样 **618**；门⑥先在 **744** 红，尚未执行删除 |
| ③ 恢复吞异常并返回尝试数 | 门⑦先在 **862** 红；只有保留实删数、单独移除记账时才在 **867** 红 |

所以，三项负控**可以借不同断言定位，但并非各自首红都证明了完整声称层次**。另外，门⑨证明指纹读取分页，不能替代来源③反推 V 的分页覆盖。

互前缀门中的双向正向对照确实同时约束“对方留下、自己被处理”。新增日志现场为 **6 处旧格式整改＋2 处拒绝日志**，均兼容 loguru 和标准 logging 后备分支。AST 调用方判据也成立，但它不能证明 V 完整或命名无碰撞。


