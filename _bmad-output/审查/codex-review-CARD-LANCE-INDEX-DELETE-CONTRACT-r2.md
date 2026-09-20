> 批次: BATCH-2026-09-18-第十五批 · 车道 card-p1-storage · 卡 CARD-LANCE-INDEX-DELETE-CONTRACT round-2
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-LANCE-INDEX-DELETE-CONTRACT-r2.md)"`
> 审查绑定: `4ce4b819`（该轮送审时的 HEAD；后续整改使其失绑，见验收单 §八 轮次表）
> 会话头自证（抄自 .stderr，括注行号；stderr 本身不入库）:
> `L2: OpenAI Codex v0.153.3` / `L5: model: gpt-6-astra` / `L9: reasoning effort: ultra`

---

结论：**仍有 2 个 HIGH 未闭合**。r1 的追加重试、旧 schema 保留、瞬时枚举门、207 脱敏和五态 int 包装均有实质修复，下面不重复原问题。

复核绑定 `4ce4b81908a22c8f5dd4a2c9e080f2b499ece1e7`。全程只读，未连接数据库或网络，未运行 pytest／pyright；以下复现均为代码路径推导。

**[HIGH] r1 HIGH-1 修得不彻底：追加重试已修好，但 `rebuild_index` 可以拆掉归属保护，且不再触发补建钩子。**  
[backend/lib/agentic_rag/clients/lancedb_client.py:2129](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/lib/agentic_rag/clients/lancedb_client.py:2129)、`:2136`、`:2637`  
复现思路：目录来源只能发现 `a`，让新 vault `a_canvas` 通过 `add_documents("nodes", …)` 建成内容表和指纹表，再对其只有 canvas、没有 Markdown 的目录执行默认 `rebuild_index()`。

重建先删除指纹表，只删除指定的 `a_canvas_vault_notes`；无 Markdown 时直接返回，留下 `a_canvas_nodes`，却没有指纹表。随后：

- `drop_vault_tables_report("a")` 会认领它，余名 `canvas_nodes` 又能通过规范逻辑名检查。
- `a` 的 `_cache_tables()` 在维度不同时同样会删除它。

这不需要并发或故障注入，也不是 D-41 排除的旧存量数据。门⑨在写入后直接测试删除、自愈，没有插入重建生命周期。

**[HIGH] 内容表占用精确指纹表名时，“存在即早退”与形态核互相抵消，可导致跨 vault 自愈删表。**  
[backend/lib/agentic_rag/clients/lancedb_client.py:2017](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/lib/agentic_rag/clients/lancedb_client.py:2017)、`:1134`、`:1785`  
复现思路：`a_canvas` 先通过生产写入方法以逻辑名 `file_fingerprints` 写入向量内容，再写逻辑名 `nodes`；目录来源看不见它时，让短 vault `a` 以不同维度执行 `_cache_tables()`。

第一笔写入产生带 `vector` 的 `a_canvas_file_fingerprints`。补建钩子只检查名字存在，因此此后每次都早退；形态核却把这张表排除，`a_canvas` 不进入短 vault 的 V。自愈跳过指纹后缀表，却会把 `a_canvas_nodes` 当作自己的规范内容表删除。

这是生产 `add_documents` 可以接受的参数序列，`index_canvas` 也透传其 `table_name`。改前纯后缀反推会保留这里真实存在的 `a_canvas`，新增形态核才移除了这层保护。**已接受的配置错误终态不包含跨 vault 丢数据。**

此处仅确认自愈路径：短 vault 的显式删除可能被指纹同名表触发的模糊名闸拦住。它也不是重提 r1 HIGH-2 的缺列问题。

**[LOW] r1 的说明更正没有同步到生产注释和日志。**  
[backend/lib/agentic_rag/clients/lancedb_client.py:1120](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/lib/agentic_rag/clients/lancedb_client.py:1120)、`:1182`、`:1988`  
复现思路：输入缺列真指纹表，实际保留但 docstring 仍称缺列排除；配置恰为 `file_fingerprints`，可能正常删除，日志却仍声称必然 HTTP 409。

`_ensure` 的“首次建表”说明也落后于现在每次成功写入都补建的实现。

**[LOW] 既有诊断字段“完整原文不变”的门仍可被截断文案绕过。**  
[backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py:1642](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage/backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py:1642)  
复现思路：把 `_last_drop_failures` 中的原文替换成 `"RuntimeError: [redacted]"`，现有子串断言仍通过。

当前生产实现没有这种回归：基线与 HEAD 的诊断赋值、格式和拒绝文案一致。这是门未覆盖的性质。

r1 各项处置的独立结论：

| 项目 | 结论 |
|---|---|
| HIGH-1 后续追加重试 | **原缺陷已修**；钩子位于两个分支之外，门检查最终累计 4 行。但生命周期保护仍有上述 HIGH。 |
| HIGH-2 缺列误排 | **已修**；空表、缺列、列名大小写差异、类型差异本身均不会导致排除，打不开也保留。唯一排除条件是存在小写 `vector` 列。 |
| MEDIUM-3 瞬时枚举 | **已修**；c101:517 明确断言刷新枚举次数 `>= 1`，变成零会失败；另断未降级及 `listing_failed`。 |
| MEDIUM-4 相等配置空洞 | **已如实区分，且实际多补了一条有效断言**：g29f1:1826 直接检查 helper，删除相等分支会失败。原集合相等断言可保留为结果契约，但没有证明日志确实产生。 |
| MEDIUM-5 207 脱敏 | **已修**；207 进入共同脱敏断言，并有状态码和 `error_type` 正向对照。 |
| MEDIUM-6 int 包装 | **已修**；五格全部建立两个等价库，实际调用包装。 |
| 原三项 LOW | **维持 LOW**；异常类型硬编码负控、直接 `collision → 409`、独立冷启动覆盖仍不足，未发现升级依据。 |

其余重点核对结果：

- **五态、四闸及 int：**正常产出的回执五态互斥完备；包装仍返回实删数，四闸条件和顺序不变。三个归属函数及 `_cache_tables` 在指定 diff 中零改动。但五态不是整个操作的异常全集：`:1607` 再次枚举待删列表若瞬时失败，会直接抛出而不产生回执。这是既有边界。
- **脱敏：**未找到把普通异常 message 或完整 refusal 带入所审查的 409／500／207 响应体的输入。失败值取 `type(e).__name__`；表名和 vault_id 仍按契约回显。
- **写入结果：**补建 `create_table` 抛错会被钩子捕获，已完成的内容写入仍返回实际行数，未被伪装成失败。`index_image_content` 经 `add_documents` 写入；该文件三个 `create_table` 站点分别是内容写入、指纹更新和空指纹补建，没有发现另一条直接创建内容表的旁路。
- **初始化时序：**`initialize()` 确实先运行 `_cache_tables()`，早于后续写入钩子。因此不能无条件声称“任何破坏性路径之前，指纹表必已建成”。正常成功补建后的两条路径受保护，上述生命周期和同名占位输入除外。
- **旧 schema 放宽与伪 vault：**所读生产内容写入固定包含 `vector`，未发现生产方法生成“无 vector 的普通后缀内容表”的路径。不能仅用人工构造的无 vector 表证明 r5-M2 已重新打开。
- **快照及分页：**接住漂移守卫返回值的修法正确；回归门检查重建后的 3 行和新维度。在读取范围内未发现另一个同类快照回归。分页翻正门既验证目标位于默认页外，又检查两行、两个原始 `doc_id` 和同一 `edge_id`，保留了第一条不被静默毁掉的性质。
- **wave5：**改写确实维持 ContextVar 注入、原始 vault 参数透传及 503；真删除契约由 c101 承担，职责描述成立。
- **性能：**候选数是所有后缀匹配表数，不能严格等同 vault 数。启动已有全库开表，新增形态核再开候选表；每次成功写入还新增整库存在性枚举，TTL 到期时可能刷新 V。没有耗时证据，不能认定已成为瓶颈，也不能确认代价可忽略。

本卡**没有新增 `# pyright: ignore`**。范围内两处既有抑制分别是 `index.py:274` 的 503 `JSONResponse` 返回类型，以及 `test_edge_rationale_fallback.py:514` 故意返回错误类型的负控，均有具体理由；本轮未运行 pyright，不能独立确认“0 诊断”。

另外两个具体的门对照输入仍值得保留：把失败类型固定成 `"RuntimeError"`，现有异常类型门仍会通过；把 `dropped`／`partial` 标签互换，门⑨的整数映射因两格均为 2 可能仍通过，但 c101 的 200／207 检查能够补拦。
