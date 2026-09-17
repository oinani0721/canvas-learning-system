> 批次: BATCH-2026-09-11-第十四批 · 车道 T1 · 卡 CARD-G2-9-F2 round-4
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G2-9-F2-r4.md)"`
> 审查绑定: `08100483..04eec9e9`（该轮送审时的 HEAD；本卡末轮 r5 绑最终 HEAD `647ef77f`）
> 会话头自证（抄 .stderr 中含 codex 版本行 + `model:` 行 + `reasoning effort` 行的三行，括注行号；stderr 本身不入库）:
> `L2: OpenAI Codex v0.153.3` / `L5: model: gpt-6-astra` / `L9: reasoning effort: ultra`

---

结论：**仍有 3 HIGH，不能判定 F2 已闭合。** 审查绑定 `08100483..04eec9e977ad932b86a6431fc3b0f862e6eb9ad1`，结束时两文件仍与该提交一致。全程只读；进行了静态核验和纯内存控制流推演，未运行 pytest、真实库负控或连接数据库、网络服务。

BLOCKER：该级别无。

[HIGH] H1：目录或配置局部失效会产生“不降级的缺项 V”，强制刷新仍可放行跨 vault 删除。  
定位：[lancedb_client.py:963](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-lance/backend/lib/agentic_rag/clients/lancedb_client.py:963)，另见 `:925`、`:1063`、`:1295`。  
复现思路：`a_b` 只有 `a_b_canvas_nodes`、没有指纹表，暂时移走它的目录或 `.obsidian`；根目录扫描正常完成，V 缺少 `a_b` 且降级标志为假，删 `a` 会把该表一起删除。目录名与 YAML 显式 ID 不同时，YAML 读取失败后静默回退目录名，也能遗漏历史表使用的 ID。

[HIGH] H2：启动自愈强制刷新后未检查降级状态，仍会处理外 vault 的漂移表。  
定位：[lancedb_client.py:1447](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-lance/backend/lib/agentic_rag/clients/lancedb_client.py:1447)。  
复现思路：让 `VAULTS_ROOT` 持续不可达，库中保留无指纹表的 `a_b_canvas_nodes`；`a` 启动时虽得到 `_vault_registry_degraded=True`，仍在 `:1451–1454` 将该表送入维度自愈。纯内存推演确认了这个传入路径，未执行自愈内部删除。

[HIGH] H3：删表入口的降级检查通过后，TTL 重算可以再次产生缺项集合并绕过拒绝。  
定位：[lancedb_client.py:1121](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-lance/backend/lib/agentic_rag/clients/lancedb_client.py:1121)，关联 `:1050`、`:1295`、`:1323`、`:1334`。  
复现思路：入口刷新得到完整 `{a,a_b}`，碰撞预检枚举耗时超过 5 秒，随后目录来源失效且 `a_b` 无指纹；后续 `_table_owner` 重新计算 V 并置降级，但删除流程不再检查，仍删除 `a_b_canvas_nodes`。纯内存推演得到：请求删除两张 canvas 表、返回 `2`、最终降级为真、拒绝原因仍为 `None`。

[MEDIUM] M1：三个规范表名不是生产闭集，自定义内容表仍会被拆开删除。  
定位：[lancedb_client.py:1319](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-lance/backend/lib/agentic_rag/clients/lancedb_client.py:1319)，另见 `:1472`。  
复现思路：V 为 `{a,a_custom}`，通过 `LANCEDB_INDEX_TABLE_NAME=custom_nodes` 为 `a` 创建 `a_custom_nodes`，另有其 notes、指纹表；删 `a` 时预检通过，删除后两张并返回 `2`，却留下确由 `a` 写出的自定义内容表。

生产证据是 `config.py:508` 的字符串配置，经 `lancedb_index_service.py:477` 传入 `index_canvas`，再经客户端 `:2086 → :2148 → :4226 → :4300` 解析、建表。只搜索 `resolve_table_name("…")` 的字面量不能证明闭集。

[MEDIUM] M2：替代门未覆盖“降级结果不缓存”，r3-MEDIUM-2 的证据缺口仍在。  
定位：[test_lancedb_cross_vault_drop_g29f1.py:1205](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-lance/backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py:1205)。  
复现思路：仅让客户端 `:1063` 允许缓存降级结果，保留 `force_refresh`；该门仍会通过，因为首次扫描正常、只是缺少 `a_b`，从未进入降级分支，随后删除又强制刷新。它证明了目录恢复后的删除行为，不能替代原性质的验证。

[MEDIUM] M3（消费端移交）：拒绝、全失败和无表仍被 API 混为同一个 404。  
定位：[index.py:107](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-lance/backend/app/api/v1/endpoints/index.py:107)。  
复现思路：触发拒绝或令全部删除失败，均返回 `0` 并进入“No tables found”；部分失败则仍返回 200 和成功计数。此项保留移交，不作为要求扩大本卡修改范围的理由。

[LOW] L1：TTL 常量旁仍保留已被本轮整改推翻的安全论证。  
定位：[lancedb_client.py:593](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-lance/backend/lib/agentic_rag/clients/lancedb_client.py:593)。  
复现思路：对照同文件 `:1038` 及 stale-registry 测试，已有表在目录暂时不可见后恢复即可进入窗口，无须新建表；“5 秒内物理上不可能有表”的说明仍未同步删除。

round-3 各条核对结果如下：

| 条目 | 结论 |
|---|---|
| HIGH-1：预检枚举失败 | **闭合。** `fail_on=2` 落在碰撞预检；测试 `:1152` 的唯一文案和 `:1155` 的非降级断言排除了旧假绿。 |
| HIGH-2：缺项缓存／TTL | **部分闭合。** 两入口强刷、指纹枚举失败置降级均已实现；上述 H1–H3 仍存在。 |
| MEDIUM-1：内容表拆分 | **部分闭合。** 两种默认内容表已覆盖，自定义表未覆盖。 |
| LOW-1：default 指纹预检 | **闭合。** 空值和 `"default"` 跳过规范前缀碰撞检查。 |
| LOW-2：等名支文案 | **闭合。** 两文件相关规则说明均已去掉 `t == v`。 |
| MEDIUM-2：降级不缓存无门 | **未闭合。** 见 M2。 |
| MEDIUM-3：API 契约 | **移交判断成立，消费端尚未处理。** |

其余问题的直接回答：

- **V 的来源边界：**正常可读的 YAML 显式 ID 已正确纳入；符合目录候选规则的空 vault 即使零表也会纳入。目录移走后，有指纹表可补回，无指纹则遗漏。根目录不可达或指纹枚举失败会置降级，但只保证删表入口当时拒绝，不能覆盖 H2、H3。
- **“只减少认领自己的表之外的表”不成立。** 并入被问 ID 只保证它参与竞争；`a` 真实写出的 `a_vault_notes` 仍会输给 `a_vault`。固定 vault 的认领集合是旧前缀集合的子集，不等于真实归属正确，也不等于全局不会丢数据。
- **default 没有本卡新增的全可见／恒空回归。** 三态分支保持原样；含下划线裸表 `canvas_nodes`、`vault_notes` 不归 default 是既有边界。未发现跳过 `"default"` 新增可达的孤儿表问题。
- **`resolve_table_name` 的问题前提现已过时。** 当前 `:845` 已恢复纯前缀幂等守卫。生产确有 `index_canvas/index_vault_notes → add_documents` 二次解析，当前不会因此新增双前缀或漏前缀。
- **碰撞预检存在保守误拒。** 例如长 vault `a_canvas` 用逻辑名 `nodes` 真正创建 `a_canvas_nodes`，删短 vault `a` 时仍会被视作其规范表碰撞而拒绝；表名本身无法区分创建者。
- **分页门有效。** 测试读回显式使用 `limit=10000`，当前夹具最多 13 张；页外自有表删除断言和独立指纹分页门补上了前十张盲区。正向对照能排除整体未运行、归属恒假，但不能单独排除某张外表恰好删除失败。
- **其他破坏性调用确实存在**，如 `rebuild_index` 的单表删除；它们按已解析名称操作，不经 V 枚举，不能仅因未强刷就认定为本轮遗漏。生产 `drop_vault_tables` 消费方只找到 API 和指定 canary；两个诊断字段没有生产消费方。“实删数”严格而言是 `drop_table(ignore_missing=True)` 未抛异常的次数。

三段负控的首红位置，以下是**按当前代码推导，非本轮复跑结果**：

| 负控 | 首红断言及证明范围 |
|---|---|
| ① `_owns_table` 退回朴素前缀 | 双向主门 `:753`：外 vault 内容表被删。 |
| ② V 打空／仅 active | 双向主门先红于 `:744`：发现前提失败，后面四个消费场景尚未执行；须看独立启动门 `:641`、删除门 `:674` 才证明删除后果。 |
| ③ 恢复吞异常并返回尝试数 | 记账门先红于 `:862`：返回 `3` 而非 `2`；失败记录断言尚未执行，日志也没有独立断言。 |

因此，**三个首红位置可区分，但不能把它们解释成三个层次都已分别获得完整负控证明**。变异还必须保留当前 `force_refresh` 参数，否则可能只是签名错误先报红。


