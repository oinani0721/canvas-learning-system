> 批次: BATCH-2026-09-18-第十五批 · 车道 card-p1-storage · 卡 CARD-LANCE-INDEX-DELETE-CONTRACT round-3
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-LANCE-INDEX-DELETE-CONTRACT-r3.md)"`
> 审查绑定: `1610f01b`（该轮送审时的 HEAD；后续整改使其失绑，见验收单 §八 轮次表）
> 会话头自证（抄自 .stderr，括注行号；stderr 本身不入库）:
> `L2: OpenAI Codex v0.153.3` / `L5: model: gpt-6-astra` / `L9: reasoning effort: ultra`

---

**结论：仍有 1 条 HIGH——r2 HIGH-A 修得不彻底；r2 HIGH-B 的保护修复成立。另有 3 条 LOW。未发现 BLOCKER 或新的 MEDIUM 实现缺陷。**

复核绑定 `1610f01b1c769e0082e6f424bbb533311f3205e6`；六个变更文件与该提交一致。全程只读，未运行测试、未连接数据库或网络。以下复现与负控均为静态代码推演。

**[HIGH] r2 HIGH-A 修得不彻底：重建异常或取消仍会拆掉指纹保护，正常返回后的补建覆盖不到。**  
[lancedb_client.py:2192](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/lib/agentic_rag/clients/lancedb_client.py:2192)，同文件 `:2176`、`:2212`、`:2753`。  
复现思路：让不可发现的 `a_canvas` 已有生产写入生成的 `a_canvas_nodes` 与指纹表，重建含一篇 Markdown 的目录并传入抛 `RuntimeError` 的 `progress_callback`；指纹表已在 `:2176` 删除，回调在 `:2753` 抛出后直接越过 `:2212` 补建，随后短 vault `a` 的 drop 或维度自愈便能认领遗留内容表。

这是**门未覆盖的新输入**，不是重提已修好的“空目录正常返回”。[新增门:2143](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py:2143) 只检查正常返回后的状态。实际向量化等待点 `:2779`、`:2791` 也位于补建之前，因此取消及重建等待期间的另一客户端操作同样存在缺口；仅补异常退出处理也不能证明等待期间安全。

**[LOW] r2 LOW-1 的说明同步仍不完整，部分刚更新的说明又被 HIGH-B 的修法改变了。**  
[lancedb_client.py:1125](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/lib/agentic_rag/clients/lancedb_client.py:1125)、[test_lancedb_cross_vault_drop_g29f1.py:1775](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py:1775)。  
复现思路：配置恰为 `file_fingerprints`，通过生产写入生成带 `vector` 的 `a_file_fingerprints`，当前代码仍会降级并回 409，不能按客户端 `:1203–1204`、测试 `:1827–1828` 所写无条件预期 200。

其他未同步处：

- 客户端 `:1125` 仍写“缺判别列 ⇒ 排除”，实际保留。
- M2 门 `:1775` 仍写闸④终态，同门 `:1802` 已断言闸①。
- 客户端 `:1210` 日志仍统一说“模糊表名闸拒绝”。
- 客户端 `:1066–1073` 仍称 canvas-only vault 看不到指纹，未区分新增补建与历史边界。
- 重试门 `:1989–1990` 仍称已有指纹时仅一次枚举，漏掉 schema 读取。
- `DropVaultReport` 的 `:614–616` 仍称端点消费方“零改动”，实际已经改调 report。

**[LOW] 新门仍有可被具体负控绕过的覆盖面，不能把绿色结果扩大为完整契约证明。**  
[test_lancedb_cross_vault_drop_g29f1.py:1615](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py:1615)、[test_index_delete_contract_c101.py:325](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/tests/unit/test_index_delete_contract_c101.py:325)。  
复现思路：保持真实删除和成功数量不变，只把回执中非空 `attempted`、`dropped` 的表名换成占位字符串，当前相关门仍能通过。

其他具体负控如下，**当前实现没有这些错误**：

| 门未覆盖的路径 | 会让相关新增门仍然通过的负控 |
|---|---|
| `collision → HTTP 409` | 端点仅对 `collision` 改回 404；g29f1 `:1736` 只验证 report，c101 没有对应端点输入。 |
| 页外表同时发生 schema 漂移 | 仅把漂移守卫的存在性检查退回默认分页，后续追加分支仍用全量枚举；`:1897` 的页外表无漂移，`:1945` 的漂移表在第一页。 |
| 指纹候选打不开 | 把形态核异常分支改成排除；现有新增形态门使用可打开的表，未覆盖这一危险方向。 |
| HIGH-B 两项修改分别有效 | 把 `_ensure` 恢复成“名字存在即早退”，保留来源扫描置降级；`:2096` 的强制刷新仍会使保护门通过。它证明数据保护结果，但没有分别锁住早退调整。 |

已登记的“诊断原文被截断仍可过门”不另算新发现。

**[LOW／基线既有边界] 删表站点枚举漏掉了 partial 的终态，“整删”仍可能删掉指纹而留下内容。**  
[lancedb_client.py:1672](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/lib/agentic_rag/clients/lancedb_client.py:1672)、[test_index_delete_contract_c101.py:278](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/tests/unit/test_index_delete_contract_c101.py:278)。  
复现思路：删除 `a_canvas` 时让指纹表成功删除、`a_canvas_nodes` 删除失败；207 返回后，目录不可发现的该 vault 再次成为“有内容、无指纹”，后续短 vault 操作可认领它。

这是**基线已有的部分失败行为，不作为本卡新 HIGH**；但它否定了 `:2209–2210` 的完整性说明。正常真指纹没有 `vector`，漂移守卫会在 `:4620–4622` 返回；metadata 的 force-rebuild 删除 `vault_notes`，归档器正常 census 流程也会排除 `vault_scoped` 指纹表。任意外部工具删表不受这里的补建机制保证。

其余问题的独立核对结果：

- **r2 HIGH-B：通过。** 同轮 `_known_vault_ids` 在 `:1280` 清零后，先目录来源、后指纹来源；没有后续来源把形态核置上的降级覆盖掉。所有 **scoped** vault 的删除、自愈会停；default／空口径仍跳过降级闸，“所有 vault 都停”不够精确。
- **真指纹误排：所列输入已挡住。** 空表、少列、列类型或大小写不同、打不开都保留候选。精确含小写 `vector` 时排除并降级，破坏性路径不会在漏掉该候选后继续执行。
- **归属与删除契约：通过。** 三个归属函数本卡零修改；四闸本体顺序、判据及原 refusal 文案保留。`int` 仍取成功删除数，两项诊断字段赋值格式未变。五态对正常生成的回执互斥完备；不是操作异常全集，这项已接受边界不重报。
- **`listing_failed`：旧主张不成立，但已修正并补门。** scoped 的“刷新 V 成功、随后预检枚举失败”能到闸②；c101 `:494` 已覆盖。持续失败才由闸①抢先。
- **207／500／409 脱敏：未找到普通异常 message 进入这些新增响应分支的输入。** 回执只保存异常类型名，端点不转发完整 refusal；含路径或凭据的异常原文不会因此进入响应体。此结论不外推到未审查的全局异常处理。
- **写入返回值与分页修复：通过。** 指纹 `create_table` 失败被内部捕获，内容写入仍返回实写数量，后续写入会重试。漂移门确实检查返回 3、落盘 3 行及 8 维；限定范围内未发现另一处本卡引入的同族旧快照缺陷。
- **edge 翻正：有效。** 默认分页数量、目标页外前提有区分力；最终同时检查两个 `doc_id`、两行和同一 `edge_id`，保留了“第一条未被毁掉”的性质。
- **wave5：定位合理。** 它继续证明 ContextVar 注入、原始参数转发及 503；物理删表契约由 c101 承担，没有把 mock 结果当成真删证据。

性能代价需要比“多一次 schema”说得更完整：健康且 TTL 命中时，每次 scoped 成功写入的 `_ensure` 增加一次全量表名枚举和一次指纹 `open_table/schema`。降级结果不缓存，两次指纹表名求值又可能各自重扫目录及全部候选。启动原本就打开全部表，现在还会额外检查全部后缀候选；**不能凭源码断言代价可忽略，也没有本轮实测支持“已成为瓶颈”。**

受检默认内置内容表名不会自然制造占名表，但受支持的自定义配置、生产 `add_documents("file_fingerprints", …)` 可以。**只改回配置不会移除已有占名表，降级会持续。**

关于 pyright：**本 diff 没有新增 ignore，不能说本卡靠新增抑制获得 0；本轮也没有重跑确认 0。** 六个变更文件仅有两处既有抑制：

- [index.py:274](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/app/api/v1/endpoints/index.py:274)：另一端点注解与 `JSONResponse` 返回类型不一致；局部运行时用途合理，与新 DELETE 无关。
- [test_edge_rationale_fallback.py:514](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/tests/unit/test_edge_rationale_fallback.py:514)：故意返回错误类型的故障输入，理由成立。


