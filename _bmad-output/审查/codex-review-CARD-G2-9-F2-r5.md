> 批次: BATCH-2026-09-11-第十四批 · 车道 T1 · 卡 CARD-G2-9-F2 round-5
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G2-9-F2-r5.md)"`
> 审查绑定: `08100483..647ef77f`（该轮送审时的 HEAD；本卡末轮 r5 绑最终 HEAD `647ef77f`）
> 会话头自证（抄 .stderr 中含 codex 版本行 + `model:` 行 + `reasoning effort` 行的三行，括注行号；stderr 本身不入库）:
> `L2: OpenAI Codex v0.153.3` / `L5: model: gpt-6-astra` / `L9: reasoning effort: ultra`

---

复核绑定 `08100483..647ef77f`；结束时 HEAD 仍为 `647ef77fdd9328673364a163228ac7fee9c46ebe`，两个目标文件无工作区差异。全程只读，未连接数据库或网络，未运行会写临时库的测试。以下复现与负控结果均为代码路径推导。

**BLOCKER：该级别无。仍有两项 HIGH，均与 B14_BASE 同态，属于既有误删边界；未发现本卡新增 HIGH 回归。**

[HIGH] 目录局部缺项时，启动自愈仍可能误删长 vault 的漂移表；r4-H1 未覆盖此入口。
  定位：`backend/lib/agentic_rag/clients/lancedb_client.py:970`、`:1526`、`:1538`
  复现思路：根目录正常，仅 `a` 可被发现，`a_b` 目录不可见且没有指纹表；让 `a_b_canvas_nodes` 存在维度漂移，调用 `a._cache_tables()`，此时 `degraded=False`，该表仍被送入维度修复。
  **归类：基线既有边界。** 新模糊表名拒绝只在 drop 路径；新增 H1 门也只调用 drop，H2 门则制造整个根目录失效，均未覆盖这个组合。

[HIGH] 长 vault 表的余名恰好是内置逻辑名时，可以绕过新增的模糊表名拒绝。
  定位：`backend/lib/agentic_rag/clients/lancedb_client.py:1378`、`:1401`、`:1558`
  复现思路：配置索引逻辑名为 `nodes`，vault `a_canvas` 经 canvas 索引产生 `a_canvas_nodes`；其目录消失且无指纹后，删除 `a` 时，余名 `canvas_nodes` 命中内置集合，两道预检均放行。
  **归类：基线既有边界。** `08100483` 的朴素 `a_` 前缀同样会删除此表；本轮只挡住了部分缺项形态。

[MEDIUM] 只收集当前配置的逻辑名，会使合法历史表被整次拒删，或绕过碰撞预检后残留。
  定位：`backend/lib/agentic_rag/clients/lancedb_client.py:1044`、`:1374`、`:1401`
  复现思路：`a` 曾用配置 `custom_nodes` 生成 `a_custom_nodes`，后来改回 `canvas_nodes`；V 完整且只有 `a` 时，drop 整次拒绝；若 V 另有 `a_custom`，旧表反而被排除，drop 可删除其余 notes／指纹表并返回成功计数，却留下旧表。
  **归类：本卡新增的删除行为变化。** r4-M1 的当前配置链已覆盖，但历史名称未覆盖；“配置取不到只会更保守”也不成立，因为碰撞预检可能因此少检查一个名称。

[MEDIUM] 可配置的普通索引表能被误识别为指纹表来源，制造不存在的 vault 并阻止合法删除。
  定位：`backend/lib/agentic_rag/clients/lancedb_client.py:1026`、`:1378`
  复现思路：配置 `LANCEDB_INDEX_TABLE_NAME=custom_file_fingerprints`，由真实 vault `a` 索引生成普通向量表 `a_custom_file_fingerprints`；反推逻辑会添加伪 vault `a_custom`，随后删除 `a` 被碰撞预检整次拒绝。
  **归类：本卡新增的可用性回归。** 配置字段没有限制该后缀，因此“普通表不存在此产出路径”的说明不能成立；此例没有新增物理数据丢失。

[MEDIUM] API 仍把拒绝、全部失败、无表混成 404，部分失败仍返回成功；维持 r4-M3 移交。
  定位：`backend/app/api/v1/endpoints/index.py:107`
  复现思路：drop 拒绝或全部删除失败均返回 0，端点随即回复 “No tables found”；若只删成部分表，则返回成功计数，不消费失败记录。
  **归类：范围外移交建议。** 实际消费方仍只有此端点和 `backend/scripts/g29_dual_vault_canary.py:783`，没有找到第三个生产消费方。

[LOW] 钉住上下文不支持嵌套，内层退出会提前解除外层的固定集合。
  定位：`backend/lib/agentic_rag/clients/lancedb_client.py:1061`
  复现思路：同一实例嵌套进入 `_pinned_vault_ids()`，内层入口覆盖集合，内层退出直接置 `None`；外层仍运行时令 TTL 过期，普通查询即可重新枚举。
  单层异常退出的 `finally` 正确。**未找到生产中同实例并发进入破坏性操作的调用链**；现有两个入口在钉住区间均无 `await`，故不升级为生产并发 HIGH。

[LOW] 三段负控的可区分性有范围限制，复合负控不能单独证明失败记录层。
  定位：`backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py:591`、`:744`、`:862`
  复现思路：按所述变异，①、②在整个文件中都会先触发 `:618` 的归属断言；③恢复“吞异常＋返回尝试数”时先在 `:862` 失败，尚未执行 `:867` 的失败记录断言。
  新拒绝闸还会使①、②的部分 `page-inner` drop 用例保持绿色：整次拒绝后，外表保留、返回 0，恰好满足该夹具断言。

round-4 各项处置核对如下：

| 项目 | 本轮结论 |
|---|---|
| H1 局部缺项 V | **部分闭合**：指定 `a_b_canvas_nodes` 的 drop 例被挡住；上述两条既有 HIGH 仍在。 |
| H2 降级时启动自愈 | **已闭合已置 degraded 的分支**：跳过修复，句柄继续装载。 |
| H3 流程中段 TTL 重算 | **原单层复现已闭合**；嵌套边界见 LOW。 |
| M1 逻辑名非闭集 | **部分闭合**：当前配置已并入，历史名称及指纹后缀误识别仍有问题。 |
| M2 降级不缓存缺门 | **已补有效断言**：恢复来源后用普通查询，错误缓存会在 `:1377` 红。 |
| L1 五秒安全论证 | **已修正**：破坏性入口刷新并固定集合，TTL 服务普通查询。 |
| M3 API 混淆结果 | **仍为移交项**，没有在本卡闭合。 |

其余问题的核对结果：

- **V 的来源**：目录候选规则与两处参考入口一致。可读取的 YAML 显式 id 优先级正确；无表 vault 只要目录符合候选规则也会进入 V。根整体不可达、目录枚举异常、指纹枚举异常会置降级；目录被移走、`.obsidian` 缺失、YAML 读取失败后退回目录名，以及配置导入失败，仍可能造成**不降级的缺项**。指纹来源只能补有对应表的 vault，补不了 canvas-only vault。
- **不对称主张**：能证明的是每个显式 vault 的新认领集合不超出旧前缀集合；不能证明减少的全部是“别人的表”。例如 `a` 自己生成的 `a_vault_notes`，在 V 含 `a_vault` 时仍会失去归属。缺项漏报仍可误删；误报则可造成漏认领与拒删。
- **default 与命名**：三态裸表分支未变，既非全表可见，也非恒空。裸 `canvas_nodes` 等含下划线名称不归 default 是既有边界。当前实现已经删除 `t == v` 分支；`resolve_table_name:850` 也已恢复纯前缀幂等守卫，背景中所述“改成归属守卫”已过时。生产确有 `index_canvas/index_vault_notes → add_documents` 的二次解析，当前没有发现新增双前缀或漏前缀。
- **分页与正向对照**：结果读回统一用 `limit=10_000`，默认十张分页仅用于前提检查；页外自表删除断言和独立指纹分页门有效。双向独立库同时验证自己的漂移表被处理、对方表保留，能排除“全部不处理”的假隔离。
- **钉住门**：移除 pinned 查询分支，会在过期后的 `:1304` 红；取消 drop 的钉住包装，会在 `:1345` 红。机制门末尾的 `force_refresh=True` 本身不能证明已经解钉，但另一门 `:1348` 检查了正常 drop 的解钉状态；异常、嵌套及启动自愈的实际钉住状态没有对应行为门。

若仅看指定用例，三段负控的首红点确实不同：①双向隔离门 `:753`；②同门的 V 前提 `:744`；③记账门 `:862`。但②尚未进入破坏性行为场景，③尚未检查失败记录，不能把这些红点扩大解释为三层机制均已分别实证。


