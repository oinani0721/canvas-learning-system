# S34 Session 提示词 — "清地雷"：G-FAKE-001 假命名函数批量重命名

## 上下文

S33 完成了反门面工程测试基础设施建设，现在有 32 个 real Neo4j 集成测试保驾护航。下一步是最大的技术债清理。

### S33 已完成

1. **32 个 real Neo4j 集成测试**（全部 PASSED）：
   - Tier1: test_neo4j_client_real.py (5), test_graphiti_client_real.py (7), test_memory_persistence_real.py (6)
   - Tier2: test_mastery_store_real.py (14)

2. **3 个 production bugs 修复**：
   - G-PARAM-001: search_nodes() $query 参数冲突 + 双 WHERE（graphiti_client.py）
   - G-PARAM-002: MemoryService DateTime vs str 排序 TypeError（memory_service.py）
   - G-PARAM-003: conftest neo4j_test_session cleanup TypeError

3. **G-FAKE-003 诊断纠正**：Memory API 7 个端点全部真实实现，DI 正确接线

4. **known-gotchas 更新**：20 -> 25 条，8 -> 12 已修复。新增 G-SILENT、G-PARAM 分类

5. **Commits**: cc66b3e, d146ce2, f3437d0, 617a761, 2f338dd

### S34 需要做的

**G-FAKE-001：42+ 假命名函数批量重命名**（12 CRITICAL + 13 HIGH）

这是 S24 GDA 审计发现的最大技术债：42+ 函数名含 "graphiti" 但从未 import graphiti-core，实际调用 Neo4j Cypher。

**为什么重要**：
- DD-13 hook（name-body-coherence.js）已就绪，会阻止新增假命名
- 但 42+ 个已有的假命名函数是"知识图谱投毒"——后续 session 看到函数名含 graphiti 就以为集成完成了
- S33 的 32 个 real tests 提供安全网，确保重命名不会破坏功能

**推荐策略**：
1. 先 `grep -r "def.*graphiti" backend/app/` 获取完整清单
2. 分批重命名（每批 5-10 个相关函数）：
   - 含 "graphiti" 但实际调 Neo4j → 改为 "neo4j" 或更准确的名称
   - 含 "graphiti" 且是死代码（调用不存在方法） → 删除
3. 每批重命名后运行 32 个 real tests + 原有单元测试验证
4. 最后运行 DD-13 hook 确认无剩余违规

**前置条件**：
- Docker Desktop 运行中
- `docker compose --profile test up -d neo4j-test`（启动测试容器）

**备选方向**（如果不想做 G-FAKE-001）：
- G-PIPE-001: 将 FSRS 权重计算器接入 MasteryStore 评分管道（MasteryStore 测试已就绪）
- G-PIPE-003: Graphiti Bridge 真实接入（Phase2 记忆管道打通）

## 新工作流提醒

⛔ **Delta Spec + TDD 4 步**：
- 一句话描述任务
- 先写/运行测试
- 再修改代码
- 运行验证

## 关键文件

- known-gotchas: `docs/known-gotchas.md`（25 条，13 待修）
- DD-13 hook: `.claude/hooks/pretool-guard.js`（name-body-coherence 检测）
- Real tests: `backend/tests/integration/test_*_real.py`（32 个安全网测试）
- 决策索引: `_decisions/decision-log.md`
- GDA 审计结果: Graphiti `search_memory_facts("GDA 假命名 42")`
