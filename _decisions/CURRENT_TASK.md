# CURRENT_TASK — 当前任务状态（唯一真相源）

> 每个 session 启动时自动注入此文件。AI 根据此文件确定"做到哪了，下一步是什么"。
> 完成一步后立即更新对应的 checkbox。

## 活跃计划（2026-04-07 更新 — Stage 1 archive 收栈完成 → Stage 2 structlog 主线）

### 已闭合 OpenSpec Changes（archived）
- [x] **fix-rag-faithfulness-and-add-crag-quality-loop** — archived 2026-04-07
  - 3 个新 contract 合并进 `openspec/specs/algo-rag/spec.md`（Faithfulness/Fusion/CRAG）
  - 88/88 测试绿（85 baseline + 3 surrogate）
- [x] **fix-rag-transform-and-episode-isolation** — archived 2026-04-07
  - 4 个新 algo-memory + 3 个新 algo-rag requirements 合并进主 spec
  - 64/69 tasks 完成（5 个 deferred 为手动 e2e/压测/doc-review，依据 plan 决策 2 不阻塞 archive）
  - 17 个新单元测试通过，零回归
- [x] **fix-fr-kg-04-schema-drift-and-sync-hardening** — archived 2026-04-07
  - 25 个新 requirements 合并进 5 个新主 spec：algo-question(5) / algo-scoring(1) / canvas-sync(12) / llm-safety(5) / verification-service(2)
  - 127/160 tasks 完成（33 个 deferred 为手动 e2e/前端 smoke）
  - 同批 `git rm -r openspec/changes/fr-kg-04-sync-pipeline-fix/`（SUPERSEDED）

### 当前主线（Phase 2 — structlog/caplog 修复）

**目标**：完成 `fix-structlog-caplog-compat` change（9 个 task），消除 ~107 个测试失败（根因 B = structlog API 漂移 ~70F+20E + 根因 C = caplog 不捕获 structlog ~37F），通过引入统一的 `configure_logging()` 入口 + structlog ↔ stdlib 双向 bridge。

预期 baseline 变化：
- pre-Stage2: 202 failed / 87 errors / 2410 passed
- post-Stage2: ~95 failed / ~67 errors / ~2517 passed

详见 plan：本 session 执行计划

### 仍进行中的 OpenSpec Changes
- `fix-structlog-caplog-compat` ← **当前主线**
- `review-enrichment-signal-fix` — Phase 1 partial (G-SILENT-001 待修，71% 完成度)
- `fr-kg-04-isolation-and-retrieval-tightening` — schema-drift archive 后已解锁
- `fr-kg-04-prompt-injection-and-auth-completion` — schema-drift archive 后已解锁
- `agentic-rag-l1-llm-router` — 0/56 工作量大，独立排期
- `trackpad-pan-support` — legacy spec 缺失 debt

### 唯一待修 known-gotcha
- **G-SILENT-001** endpoint wiring：`backend/app/api/v1/endpoints/review.py:788` `generate_verification_canvas` 需内联 enrichment_available

### 已修复统计（2026-04-07 截止）
- known-gotchas: 37 总 / 32 已修 / 4 保留 / 1 待修
- 主 spec capabilities: 9 个（archive 收栈后从 5 → 9，新增 algo-memory/algo-question/canvas-sync/llm-safety/verification-service）
- real Neo4j 集成测试: 86 个

## 历史活跃计划（已完成或停滞，留作参考）

### 历史 Phase 1 — MagicMock → 真实数据库测试（已结束）

**结束状态**：基础设施全部就位，原始 Step 3 目标文件已被后续 PR 重命名/重构。详见：
- [x] Step 0: docker-compose 添加 neo4j-test 容器（端口 7692）— commit 3a167e9
- [x] Step 1: conftest.py 修复端口 + neo4j_available + neo4j_test_session — commit 3a167e9
- [x] Step 2: DD-03 hard hook (mock-import-guard.js) — commit 0cb8cf8
- [-] Step 3: 原计划的 test_neo4j_client.py / test_graphiti_client.py / test_memory_persistence.py 已被 fix-fr-kg-04 系列 PR 吸收/重命名，不再有独立目标
- 158 个 unit test 文件中 104 个仍在 mock，留给后续根因 A 清理 change（MagicMock → AsyncMock sweep）

## 后续 Phases（不在当前范围）
- Phase 3: MagicMock → AsyncMock sweep（根因 A，~30 min sed 可解决 ~85F+60E）
- Phase 4: pytest-mock 缺失（根因 D，trivial）
- Phase 5: 修复 6 条断裂管道（G-PIPE）
- Phase 6: 功能质量提升（假评分→真 LLM、异常精确化）
- Phase 7: 产品记忆 KA-RAG 接通
