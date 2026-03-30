# S33 Session 提示词 — 继续 Phase 1 Step 3: 测试迁移

## 上下文

S32 完成了规范驱动开发诊断和 Phase 1 基础设施搭建。现在需要继续未完成的 Step 3。

### S32 已完成

1. **3 份 Gemini Deep Research 报告**（保存在 `_decisions/`）：
   - `deep-research-ssd-web-improvements.md` — 整合方案（SSD工作流+记忆架构+技术债）
   - `deep-research-ssd-code-diagnosis.md` — 代码诊断（6维根因：门面工程）
   - `deep-research-anti-facade-deployment.md` — 部署计划（5层防御差距分析）

2. **用户确认的决策**：
   - 新工作流：Delta Spec + TDD 4步（选任务→写测试→写代码→验收），替代 BMAD 6步
   - 记忆架构：开发记忆→MEMORY.md / 产品记忆→保留 Graphiti+KA-RAG
   - 测试隔离：方案A — docker-compose 专用测试 Neo4j 容器（端口 7692）
   - Graphiti 两个都保留：7689=开发记忆, 7691=产品数据, 7692=测试专用

3. **Phase 1 已实施（commits: 3a167e9, 0cb8cf8）**：
   - Step 0: docker-compose 添加 `neo4j-test` 容器（端口 7692, profiles: [test]）
   - Step 1: conftest.py 修复（NEO4J_TEST_URI=bolt://localhost:7692 + neo4j_available + neo4j_test_session）
   - Step 2: DD-03 hard hook (`mock-import-guard.js`)，阻断 backend/app/ 中的 mock 导入

### S33 需要做的

**Step 3: 迁移 Tier 1 前 3 个测试文件（从 MagicMock → real_neo4j_client）**

迁移目标和优先级：

| # | 文件 | Mock 点 | 说明 |
|---|------|---------|------|
| 1 | `backend/tests/unit/test_neo4j_client.py` | 27 | 测 Neo4j client 自身，用 mock driver |
| 2 | `backend/tests/unit/test_graphiti_client.py` | 18 | 测假命名 GraphitiEdgeClient |
| 3 | `backend/tests/integration/test_memory_persistence.py` | ~10 | 标称 integration 但实际用 mock |

**迁移步骤（每个文件）**：
1. 读现有测试，理解每个 test case 在验证什么
2. 创建 `test_<name>_real.py` 并行版本，使用 `neo4j_test_session` fixture
3. 添加 `@pytest.mark.integration` 标记
4. 运行：`docker compose --profile test up -d neo4j-test`（如果没启动）
5. 运行：`cd backend && .venv/Scripts/python.exe -m pytest tests/unit/test_neo4j_client_real.py -v -m integration`
6. 对比 mock vs real 结果——mock 通过但 real 失败 = 发现隐藏 bug

**前置条件**：
- Docker Desktop 运行中
- `docker compose --profile test up -d neo4j-test`（启动测试容器）
- 验证：`bolt://localhost:7692` 可连接

**Step 4: 验证**
- 运行所有集成测试：`pytest backend/tests/ -m integration -x`
- 运行所有单元测试：`pytest backend/tests/ -m "not integration"`
- 覆盖率不降：`pytest backend/tests/ --cov=app --cov-fail-under=85`

## 新工作流提醒

⛔ **不要使用 BMAD 全流程**。直接用 Delta Spec + TDD：
- 一句话描述任务
- 先写/迁移测试
- 再实现/修改代码
- 运行验证

## 关键文件

- Plan: `.claude/plans/piped-giggling-falcon.md`
- conftest fixtures: `backend/tests/conftest.py`（line 592-680: neo4j_available, real_neo4j_client, neo4j_test_session）
- DD-03 hook: `.claude/hooks/mock-import-guard.js`
- 已知问题: `docs/known-gotchas.md`（20条，12待修）
- 决策索引: `_decisions/decision-log.md`
