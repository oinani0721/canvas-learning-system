总裁定：**仍阻断，不可验收。**  
开发方“10/10 整改”不成立：原 10 项为 **7 CLOSED / 3 NOT-CLOSED**。未闭合的是 **HIGH-3、MEDIUM-3、MEDIUM-5**。

| Round-1 项 | 复审裁定 | 核验结果 |
|---|---|---|
| HIGH-1 | **CLOSED** | [报告:45](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-16-doc-type-census-2026-08-28.md:45) 与 [search service:1044](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/app/services/supplementary_search_service.py:1044) 已承认 MCP 生产透传。真实 clean 链为 [note_search_tools:289](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/app/mcp/tools/note_search_tools.py:289) → metadata → [:385](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/app/mcp/tools/note_search_tools.py:385)/`:389`。 |
| HIGH-2 | **CLOSED** | 对 `feature-obsidian-hybrid-dev` @ `5b9c00cf…` 的 live vault 只读 `find`：`节点/考察-*.md` 直接及递归均 **0**；`检验白板/` 恰 **1** 个普通 `.md`。目录属于不可撤销黑名单；`节点/` 不被拦。未读取正文。 |
| HIGH-3 | **NOT-CLOSED** | [报告:56](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-16-doc-type-census-2026-08-28.md:56) 的 concept、image OCR、阈值结论正确；但 [报告:57](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-16-doc-type-census-2026-08-28.md:57) 仍无条件写“自由值→note 1.0”。反例：`/videos/...` 下 `type: foo` 保留 `doc_type=foo`，但 [source_type 按路径变成 video_transcript](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/lib/agentic_rag/clients/lancedb_client.py:1787)，权重为 `0.75`；只有普通路径才是 `note/1.0`。 |
| HIGH-4 | **CLOSED** | [§1:15](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-16-doc-type-census-2026-08-28.md:15) 已登记根 `scripts/` 的 BMAD frontmatter 同名异物，并限定 census 为 `backend/*.py` 的 LanceDB 字段。 |
| MEDIUM-1 | **CLOSED** | 直接 lookup 不可达、`get_filter_threshold()` 聚合可达但当前非决定的区分已写入报告、注释及 FU-1；实际阈值仍为 `0.42`。 |
| MEDIUM-2 | **CLOSED** | 生产加权确为 [rerank 内 weights.get](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/app/services/supplementary_reranker.py:182)；`get_type_weight()` 仅测试调用。 |
| MEDIUM-3 | **NOT-CLOSED** | [§1:31](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-16-doc-type-census-2026-08-28.md:31) 已正确写“两显式生产者 + 无校验通用 sink”，但 [§8:89](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-16-doc-type-census-2026-08-28.md:89) 又退回“写入方唯一（双路径）”，移交摘要内部矛盾。 |
| MEDIUM-4 | **CLOSED** | [§3:43](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-16-doc-type-census-2026-08-28.md:43) 已限定 Tier-1；[FU-5:85](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-16-doc-type-census-2026-08-28.md:85) 登记 Tier-2 裸表旁路。 |
| MEDIUM-5 | **NOT-CLOSED** | pinned grep 已闭合：精确重放为 **18 文件/146 行**，与 [清单](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-16-evidence/doc_type-146-occurrences@37387a86.txt:1) 逐字节相等。但 [metadata:2](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-16-evidence/test-run-metadata.txt:2) 仍无两次完整 stdout/traceback、exit code、时间戳、before/after 源 blob/digest。结合 [pytest.ini:19](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/pytest.ini:19)，所列命令不会直接产生现有仅 10 行的摘要，过滤过程也未记录。 |
| LOW-1 | **CLOSED** | 已正确区分 [frontmatter 直通:2740](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/lib/agentic_rag/clients/lancedb_client.py:2740) 与 [whiteboard 消费:2767](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/lib/agentic_rag/clients/lancedb_client.py:2767)。 |

铁律与落点测试：

- **CLOSED**：`e7a480eb^ → e7a480eb` 两个 Python 文件均为无属性 AST 全等，diff 只有 `#` 注释。
- **CLOSED**：隔离相关文件零改动；search service 的 `exclude_doc_types` 与 Tier-2 代码也未变。
- **CLOSED**：[baseline](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-16-evidence/baseline-before-edits.txt:1) 与 [after](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-16-evidence/after-edits.txt:1) 的 9 个失败节点顺序及集合完全相同；仅耗时 `0.47s/0.50s` 不同。
- 当前 HEAD 独立复跑仍为同一 **9 failed / 102 passed / 10 warnings**。这证明当前“零新增失败”，但不能补造两次历史运行的 provenance。

新发现：

- **MEDIUM**：[§8:89](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-16-doc-type-census-2026-08-28.md:89) 称 `source_type`“纯路径启发”不实；`image_ocr` 是显式赋值，`neighbor_expansion` 也是运行期赋值。
- **MEDIUM**：[reranker:196](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/backend/app/services/supplementary_reranker.py:196) 仍写旧行为 `note=0.7、0.5×0.7=0.35`，而当前 `note=1.0`。
- **MEDIUM**：[live-distribution-and-value-grep:5](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/_bmad-output/审查/G4-16-evidence/live-distribution-and-value-grep.txt:5) 无生成命令/SHA，且输出含 `"doc_type"`、`"file_path"` 假阳性，不能作为“取值字面量全集”证据。
- **LOW**：§1 根脚本引用行号不准；pinned SHA 下实际为 [migrate:62](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/scripts/migrate_story_frontmatter.py:62)、[sync story:63](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/scripts/sync_links.py:63)、[sync epic:85](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census/scripts/sync_links.py:85)。

限制：未读取 live vault 正文、未复扫 live LanceDB；当前环境未暴露 `graphiti-canvas`，未用其他工具冒充。本轮未修改工作树。


