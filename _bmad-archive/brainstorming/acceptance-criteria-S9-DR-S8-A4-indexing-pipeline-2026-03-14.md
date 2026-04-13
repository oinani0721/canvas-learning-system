# S8 A4 索引管道 — 验收标准档案

**Review Session:** S9-Review-S8
**审查对象:** S8-Brainstorming（brainstorming-session-S8-A4-indexing-pipeline-2026-03-13.md）
**审查方法:** 5 个独立 Agent 并行对抗性审查（4 代码审查 + 1 社区验证）
**日期:** 2026-03-14

---

## 一、审查总结

| DR | S8 声称问题数 | 确认 | 部分确认 | 额外发现 | 总评 |
|----|-------------|------|---------|---------|------|
| DR-S8-1 增量索引 | 6 | 6/6 | 0 | +4 | ✅ 决策正确 |
| DR-S8-2 Context Enrichment | 7 | 6/7 | 1 | +2 | ✅ 决策正确，预算需调整 |
| DR-S8-3 触发时机 | 5 | 4/5 | 1 | +2 | ✅ 决策正确 |
| DR-S8-4 记忆系统 | 5 | 5/5 | 0 | +1 | ✅ 决策正确 |
| 社区验证 | 4 假设 | 4/4 | 0 | +2 补充 | ✅ 全部通过 |

**S8 共声称 23 个问题，21 个完全确认，2 个部分确认，0 个否认。另发现 9 个额外问题。**
**S8 的 4 项关键技术假设全部通过社区验证。**

---

## 二、S9 审查修正（vs S8 原方案）

| # | S8 原方案 | S9 修正 | 理由 |
|---|---------|---------|------|
| 1 | merge_insert 统一用于 canvas 和 vault notes | **区分两种策略**：canvas 用 merge_insert（doc_id 已稳定），vault notes 用 delete-by-file + insert（content 变化时 doc_id 也变） | vault notes 的 MD5 doc_id 不稳定 |
| 2 | 全局 context 预算 500-600 tokens | **调整为 2000-3000 tokens** | 500 tokens 约 1500 字符，adjacent nodes 10×300=3000 字符已超标，太激进 |
| 3 | 并发限制为 MEDIUM 优先级 | **降级为 LOW** | 20 canvas 同时编辑场景不现实 |
| 4 | Graphiti 双注入简单去掉一个 | **需先确认两个注入点是否查不同数据源** | context_enrichment_service 用 Graphiti client，agent_service 用 Neo4j client |
| 5 | — | **补充：merge_insert 后定期 create_fts_index()** | FTS 索引不自动跟随 merge_insert 更新 |
| 6 | — | **补充：filter 中 path 需 SQL 转义** | `path.replace("'", "''")` 防注入 |

---

## 三、验收 Checklist

### DR-S8-1：增量索引（7 条）

| AC | 优先级 | 测试条件 | PASS 判定 | FAIL 判定 |
|----|--------|---------|-----------|-----------|
| AC-DR1-1 | **P0** | 对同一 canvas 连续调用 `index_canvas()` 3 次 | 表中该 canvas 文档数量不变（无重复行） | 文档数量随调用次数线性增长 |
| AC-DR1-2 | **P1** | 修改 canvas 中 1/10 个节点后重新索引 | 只有 1 个 chunk 重新 embedding，其余 9 个 hash 匹配跳过 | 10 个 chunk 全部重新 embedding |
| AC-DR1-3 | **P1** | merge_insert 后立即执行 hybrid search | 新增/更新的文档可通过 FTS 分支命中 | FTS 搜不到新文档 |
| AC-DR1-4 | **P1** | 删除 canvas 中 1 个节点后重新索引 | 该节点的 chunk 从 LanceDB 中消失 | 已删除节点的 chunk 仍存在 |
| AC-DR1-5 | **P1** | 文件路径含单引号（如 "note's.md"） | merge_insert 正常执行不报错 | SQL 语法错误 |
| AC-DR1-6 | **P2** | 500+ 笔记的 vault 增量索引 1 个文件 | 耗时 < 5s（不含 embedding） | 耗时 > 10s 或内存溢出 |
| AC-DR1-7 | **P2** | 编辑 canvas（通过 backend API） | 后端日志只出现 1 次索引调用 | 同一编辑产生 2+ 次索引调用 |

### DR-S8-2：Context Enrichment（8 条）

| AC | 优先级 | 测试条件 | PASS 判定 | FAIL 判定 |
|----|--------|---------|-----------|-----------|
| AC-DR2-1 | **P0** | FILE 节点指向 50K 字符文件 | enriched_context 中目标节点部分 ≤ 2000 字符 | 超过 2000 字符 |
| AC-DR2-2 | **P0** | 调用 decompose_basic 端点 | LLM prompt 中目标节点内容只出现 1 次 | 目标节点内容出现 2 次 |
| AC-DR2-3 | **P0** | 任意端点的 LLM 调用 | Graphiti memories 只出现 1 次 | 同一 prompt 中 Graphiti memories 出现 2 次 |
| AC-DR2-4 | **P0** | 调用 `_get_color_description("4")` | 返回含 "Red" 或 "未理解" | 返回 "Green" 或 "已掌握" |
| AC-DR2-5 | **P1** | hub 节点（连接 50+ 邻居） | adjacent nodes 数量 ≤ 10 | 返回所有 50+ 邻居 |
| AC-DR2-6 | **P1** | 任意场景 | enriched_context 总长度 ≤ 预算上限（2000-3000 tokens） | 超过预算上限 |
| AC-DR2-7 | **P1** | FILE 节点的 textbook/Graphiti 搜索 | 搜索 query 使用实际内容前 200 字符 | 搜索 query 为空字符串 |
| AC-DR2-8 | **P1** | 有 heading 结构 + 无 heading 结构的笔记 | 有 heading→chunk 含 "文件名 > H1 > H2" 前缀；无 heading→含 "文件名" 前缀 | 无 heading 笔记报错或前缀为空 |

### DR-S8-3：触发时机（5 条）

| AC | 优先级 | 测试条件 | PASS 判定 | FAIL 判定 |
|----|--------|---------|-----------|-----------|
| AC-DR3-1 | **P0** | 编辑 .md 文件后观察索引触发时间 | ~2.3s 内触发索引（日志可见 resolved→flush） | 索引触发时间 > 5s |
| AC-DR3-2 | **P0** | 通过 backend API 编辑 canvas 节点 | 只有 backend Path B 触发索引 | 前端 Path A 也独立触发 |
| AC-DR3-3 | **P0** | 禁用/卸载插件 | 无 console 错误，无 apiClient 异常 | 卸载后出现异常 |
| AC-DR3-4 | **P1** | 在 Obsidian 中直接编辑 .canvas 文件 | 编辑后仍能触发索引（vault.on('modify') 保持） | .canvas 编辑后不触发索引 |
| AC-DR3-5 | **P1** | 重命名 .md 文件 | 旧 doc_id chunks 被清理 + 新 doc_id chunks 被索引 | 旧 chunks 残留 |

### DR-S8-4：记忆系统交叉（5 条）

| AC | 优先级 | 测试条件 | PASS 判定 | FAIL 判定 |
|----|--------|---------|-----------|-----------|
| AC-DR4-1 | **P0** | 调用 `_bridge_to_graphiti()` | 无 AttributeError + Graphiti 中出现学习事件 episode | AttributeError 或 Graphiti 无新 episode |
| AC-DR4-2 | **P1** | 同一 concept：scoring 流程 + /review/record + /review/fsrs-state | 三者返回一致的 FSRS 状态（stability/difficulty 相同） | 三者返回不同 FSRS 状态 |
| AC-DR4-3 | **P1** | 调用 `generate_review_canvas()` | 返回的 nodes[] 包含实际问题节点（≥1 个） | nodes[] 仍为空数组 |
| AC-DR4-4 | **P2** | 搜索概念相关内容 | retrievability 低的概念排序靠前（弱点优先） | 排序与 retrievability 无关 |
| AC-DR4-5 | **P3** | 用户答题完成 | FSRS/Graphiti/RAG 三个 Handler 均被调用（日志可见） | 任何一个 Handler 未触发 |

---

## 四、优先级汇总

### P0 — 必须立即修复（9 条）
- AC-DR1-1: merge_insert 去重
- AC-DR2-1: Target 截断 2000 字符
- AC-DR2-2: decompose 重复拼接修复
- AC-DR2-3: Graphiti 双注入修复
- AC-DR2-4: 颜色映射修复
- AC-DR3-1: changed+resolved 模式
- AC-DR3-2: 前后端去重
- AC-DR3-3: onunload 清理
- AC-DR4-1: Bridge 变量名修复（1 行）

### P1 — 高优先级增强（11 条）
- AC-DR1-2 ~ AC-DR1-5
- AC-DR2-5 ~ AC-DR2-8
- AC-DR3-4 ~ AC-DR3-5
- AC-DR4-2 ~ AC-DR4-3

### P2 — 中优先级优化（3 条）
- AC-DR1-6, AC-DR1-7, AC-DR4-4

### P3 — 长期增强（1 条）
- AC-DR4-5

---

## 五、代码审查发现的额外问题（S8 未提及）

| # | 来源 | 严重性 | 问题 | 建议 |
|---|------|--------|------|------|
| A1 | DR1 | MEDIUM | `index_vault_notes()` 每次 drop 全表重建（浪费） | content_hash 跳过优化后自然解决 |
| A2 | DR1 | HIGH | 删除 Canvas 节点后旧 entry 无清理机制 | merge_insert with `when_not_matched_by_source_delete` 解决 |
| A3 | DR1 | MEDIUM | 前后端索引存在 race condition（不同 client 实例） | 消除前端 Path A 后自然解决 |
| A4 | DR1 | MEDIUM | `count_documents_by_canvas()` 加载整个表到 pandas | 改用 `table.count_rows(filter=...)` |
| A5 | DR2 | MEDIUM | 端点间内容处理不一致（decompose vs explain 不同模式） | 统一为 explain 的分离模式 |
| A6 | DR2 | LOW | `_build_enriched_context` 方法名误导（含 target node） | 重命名或拆分 |
| A7 | DR3 | MEDIUM | `write_canvas()` 不触发 LanceDB 索引 | 添加触发或文档说明 |
| A8 | DR3 | LOW | setTimeout 与 registerEvent 的 race condition | onunload 清理修复后缓解 |
| A9 | DR4 | LOW | `get_graphiti_bridge()` 单例 first-call-wins 问题 | 修复 line 660 后自然解决 |

---

## 六、模块质量评级汇总

| 模块 | 评级 | 说明 |
|------|------|------|
| `lancedb_client.py::search()` | ✅ 可复用 | clean hybrid search + RRF |
| `lancedb_client.py::index_vault_notes()` | ✅ 可复用 | 有 drop_table 去重 + FTS |
| `canvas_service.py::_trigger_lancedb_index()` | ✅ 可复用 | clean fire-and-forget |
| `lancedb_index_service.py` | ✅ 可复用 | singleton + debounce + retry + JSONL |
| `MasteryEngine` | ✅ 可复用 | BKT+FSRS hybrid，数学正确 |
| `MasteryStore` | ✅ 可复用 | clean Neo4j CRUD |
| `GraphitiBridgeService` | ✅ 可复用 | clean Cypher，修好调用方即可 |
| `COLOR_PRIORITY_SCORES` | ✅ 可复用 | 与 canvas_utils.py 一致 |
| explain 端点 | ✅ 可复用 | 正确的分离 content/context 模式 |
| `lancedb_client.py::add_documents()` | ⚠️ 需修复 | 纯 append 无去重 |
| `lancedb_client.py::index_canvas()` | ⚠️ 需修复 | 无 delete-before-insert |
| `lancedb_client.py::index_single_file()` | ⚠️ 需修复 | 同上 + 无 FTS 重建 |
| `metadata.py::get_lancedb_client()` | ⚠️ 需修复 | 无 singleton |
| `context_enrichment_service.py` | ⚠️ 需修复 | 无截断/颜色颠倒/无预算 |
| `ReviewService` | ⚠️ 需修复 | 独立 FSRS 状态 + STUB |
| `MemoryService:660` | ⚠️ 需修复 | 仅 1 行变量名 |
| `main.ts` 前端索引 | ⚠️ 需修复 | 双触发 + 无错误恢复 |
| `_get_color_description()` | ❌ 需重写 | 颜色映射完全颠倒 |
| `SSEConnectionManager` | ❌ 需重写 | 完整 stub，sse_manager.py 不存在 |

---

## Graphiti 记录

本 Review Session (S9) 共记录：
- `[Session-Start]` S9-Review-S8
- `[Progress]` 启动 5 个审查 Agent
- `[Code-Review]` × 4（DR-S8-1/2/3/4）
- `[Research-Tech]` × 1（社区验证 4/4 通过）
- `[Acceptance-Criteria]` × 4（本文档，25 条验收标准）
- `[Session-End]` S9-Review-S8 完成
