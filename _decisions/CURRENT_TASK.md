# CURRENT_TASK — 当前任务状态（唯一真相源）

> 每个 session 启动时自动注入此文件。AI 根据此文件确定"做到哪了，下一步是什么"。
> 完成一步后立即更新对应的 checkbox。

## 活跃计划：Phase 1 — 从 MagicMock 迁移到真实数据库测试

### 已完成
- [x] Step 0: docker-compose 添加 neo4j-test 容器（端口 7692）— commit 3a167e9
- [x] Step 1: conftest.py 修复端口 + neo4j_available + neo4j_test_session — commit 3a167e9
- [x] Step 2: DD-03 hard hook (mock-import-guard.js) — commit 0cb8cf8

### 当前步骤
- [ ] Step 3: 迁移 Tier 1 测试文件（3 个）
  - [ ] test_neo4j_client.py → mock driver → real neo4j-test:7692
  - [ ] test_graphiti_client.py → mock Neo4jClient → real
  - [ ] test_memory_persistence.py → relabel as real integration

### 待做
- [ ] Step 4: 迁移 Tier 2 测试文件（8 个）
- [ ] Step 5: 验证全部集成测试通过 + 覆盖率 ≥85%

## 后续 Phases（不在当前范围）
- Phase 2: 修复 6 条断裂管道（G-PIPE）
- Phase 3: 功能质量提升（假评分→真 LLM、异常精确化）
- Phase 4: 产品记忆 KA-RAG 接通

## 前置条件
- Docker Desktop 运行中
- `docker compose --profile test up -d neo4j-test`（启动测试容器）
- bolt://localhost:7692 可连接
