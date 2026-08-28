总裁定：**FAIL，当前 census 报告与两处新注释不可验收。**  
但目标 diff 确认是纯注释，`exam_board/whiteboard` 隔离代码没有改动，0 行业务行为改动成立。

审查锚点：`card/s5-census` @ `37387a8662e9dd646fad5628841679d777cb7eae`。

## BLOCKER

无。

## HIGH

1. **遗漏真实生产消费方。**

   报告称 `doc_type` “下游生产代码 0 读取方”([报告:43](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-16-doc-type-census-2026-08-28.md:43))，新注释也重复该断言([supplementary_search_service.py:1046](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/app/services/supplementary_search_service.py:1046))。

   实际上 MCP 默认 fast/fallback 路径调用 `_material_to_item`，clean 分支读取 `m["doc_type"]` 并外带到 `NoteResultItem.metadata`：[note_search_tools.py:289](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/app/mcp/tools/note_search_tools.py:289)、[note_search_tools.py:385](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/app/mcp/tools/note_search_tools.py:385)。这是生产消费/对外透传，不是仅测试预留。

2. **`exam_board live=0` 的目录黑名单归因错误。**

   报告称 0 行是“第一层目录黑名单先行拦截”([报告:53](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-16-doc-type-census-2026-08-28.md:53))。但正式插件把考察文件写到可索引的 `节点/考察-*.md`：[exam-quick.ts:39](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/frontend/obsidian-plugin/src/exam-quick.ts:39)、[exam-quick.ts:75](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/frontend/obsidian-plugin/src/exam-quick.ts:75)。后端据 `exam_question_id` 推断 `exam_board`，且回归测试明确要求该路径产 chunk：[lancedb_client.py:2740](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/lib/agentic_rag/clients/lancedb_client.py:2740)、[test_rag_stage2_chunk_contracts.py:43](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/tests/regression/test_rag_stage2_chunk_contracts.py:43)。

   因此 live 0 的原因仍是 **UNVERIFIED**，不能裁成“预期由目录层拦截”。

3. **六值表再次混同 `doc_type` 与 `source_type`。**

   报告关于 concept/空串自由值的行为结论不成立([报告:54](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-16-doc-type-census-2026-08-28.md:54))：

   - `/videos/` 下 `type: concept` 会得到 `doc_type=concept`、`source_type=video_transcript`，不一定命中 note 权重。
   - 任意 `type: foo` 在普通路径上仍是 `source_type=note`，不会落 `DEFAULT_TYPE_WEIGHT`。
   - image OCR 缺 `doc_type`，但写 `source_type=image_ocr`，命中 0.6 而非默认 0.5：[lancedb_client.py:1270](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/lib/agentic_rag/clients/lancedb_client.py:1270)、[lancedb_client.py:1787](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/lib/agentic_rag/clients/lancedb_client.py:1787)。

4. **“全仓/六值全集”范围漏掉根目录脚本。**

   [migrate_story_frontmatter.py:60](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/scripts/migrate_story_frontmatter.py:60) 写 `doc_type: story`；[sync_links.py:58](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/scripts/sync_links.py:58) 消费 `story/epic`。

   这是 BMAD frontmatter 的另一个命名空间，不是 LanceDB `vault_notes` 字段；它不推翻狭义双生产者结论，但推翻报告的“全仓仅……”和无范围限定的六值全集表述。按用户指定的遗漏写点/消费点口径列 HIGH。

## MEDIUM

1. **`TYPE_WEIGHTS["concept"]` 不是绝对死键。**

   当前 vault-note `source_type` lookup 确实不可达 concept；但 `get_filter_threshold()` 会消费整个 `TYPE_WEIGHTS.values()`，且生产 chat 路径调用它：[supplementary_reranker.py:112](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/app/services/supplementary_reranker.py:112)、[chat.py:428](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/app/api/v1/endpoints/chat.py:428)。当前 concept=1.0 不是最小值，因此删键暂不改变阈值；准确裁定应是“直接 lookup 不可达、聚合可达但当前非决定项”。

2. **新注释写错真实调用链。**

   加权生产路径调用 `rerank()`，其直接执行 `weights.get(source_type, ...)`：[supplementary_reranker.py:171](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/app/services/supplementary_reranker.py:171)。`get_type_weight()` 没有生产调用，仅测试调用。因此“走 `get_type_weight`”不实。

3. **“双路径唯一”需区分生产者与通用 sink。**

   batch/single 确为当前 `vault_notes` 两个显式值生产者；但公共 `add_documents()` 可无校验透传任意顶层 `doc_type`、`source_type` 或 `metadata_json`：[lancedb_client.py:3615](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/lib/agentic_rag/clients/lancedb_client.py:3615)。Chroma 迁移脚本也会把任意输入 metadata 内嵌进 `metadata_json`：[migrate_chromadb_to_lancedb.py:300](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/scripts/migrate_chromadb_to_lancedb.py:300)。未静态证明它们当前向 `vault_notes` 写第三种 doc_type，故应表述为“两生产者 + 通用 sink”。

4. **legacy Tier-2 条件路径绕过 doc_type 排除。**

   默认关闭，故不是默认生产泄漏；但启用 `ENABLE_LANCEDB_TIER2_FALLBACK` 后会直接查询裸 `vault_notes`，没有 `doc_type WHERE`：[supplementary_search_service.py:863](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/app/services/supplementary_search_service.py:863)。所以 whiteboard/exam_board“在库但检索不可见”只能限定于默认 Tier-1 路径。

5. **grep 与测试证据可复验性不足。**

   - Git 对象上复算确为 **18 文件/146 行**，证据清单与 `git grep` 的排序后 `path:line` 哈希均为 `a00e20a…`。
   - 但报告原样 `grep -rn ... backend` 在当前工作树会扫入 `backend/.venv`，实得 **30 文件/198 行**；应改用 pinned `git grep`。
   - before/after 各只有 9 个失败节点和摘要：[baseline](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-16-evidence/baseline-before-edits.txt:1)、[after](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-16-evidence/after-edits.txt:1)。失败集合与计数相同，但文件并非逐字节全等（仅耗时 `0.47s`/`0.48s` 不同），且缺 pytest 命令、traceback、环境与源码 digest。

## LOW

1. `whiteboard` 不是在 `:2767` “推断”；真正来源是 `frontmatter.type` 于 `:2740` 直通。`:2767` 只是消费该值进行白板样板剥离：[lancedb_client.py:2767](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/lib/agentic_rag/clients/lancedb_client.py:2767)。

## 六取值与测试汇总

| 项 | 裁定 |
|---|---|
| `note` | PASS |
| `video_transcript` | PARTIAL：接线，但权重只由 `source_type` 驱动 |
| `whiteboard` | PARTIAL：Tier-1 隔离成立；引用与 Tier-2 限制遗漏 |
| `exam_board` | PARTIAL：推断/Tier-1 排除成立；live 0 原因 FAIL |
| `concept` | PARTIAL：存储及 MCP 透传成立；“总命中 note/绝对死键”不成立 |
| 空串/自由值 | PARTIAL：值域未闭合成立；DEFAULT 权重结论错误 |
| `doc_type` / `source_type` 正交性 | PARTIAL：字段职责和赋值链分离，但生产规则部分共享路径启发；未发现 `doc_type → source_type` 复制 |
| 两处 0 行行为改动 | PASS：两文件与 HEAD 的无属性 AST 均完全相等 |
| “零新增失败” | PARTIAL：所记录失败节点/计数相同；原始测试运行绑定不足 |
| 9 条失败根因方向 | PASS：`fcd34953` 翻转 note/video 权重但未同步 reranker 测试；floor 用例仍依赖旧 `0.5×0.7<0.42`。安全类 floor 测试应调整输入以继续触发 floor，不应简单放宽预期 |

限制：未读取 raw vault，未复扫 live LanceDB，因此 117 条 concept 的 `doc_type × source_type` 联合分布及历史迁移行仍不可验证。当前环境未暴露 `graphiti-canvas/search_memory_facts`，未以其他工具冒充该检索。本轮未修改任何文件。


