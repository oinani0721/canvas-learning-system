# CURRENT_TASK — 当前任务状态（唯一真相源）

> 每个 session 启动时自动注入此文件。AI 根据此文件确定"做到哪了，下一步是什么"。
> 完成一步后立即更新对应的 checkbox。

## 活跃计划（2026-04-07 更新 — S35 follow-up archive 完成）

### 已闭合 OpenSpec Changes（archived）
- [x] **fix-rag-faithfulness-and-add-crag-quality-loop** — archived 2026-04-07
  - Phase 1-4 实现已落地 (commits d79d5b9 / c363c3c / 2303b6b / 08f3499)
  - Phase 5 文档 + surrogate e2e (commits 4500ca1 / c229291 / 本次 commit)
  - 3 个新 contract 合并进 `openspec/specs/algo-rag/spec.md`：
    - Faithfulness Not-Applicable Contract (7 scenarios)
    - Fusion and Reranking Observability Contract (7 scenarios)
    - One-Shot CRAG Deep Research Fallback Contract (8 scenarios)
  - 88/88 测试绿（85 baseline + 3 surrogate）

### 仍进行中的 OpenSpec Changes
- `fix-fr-kg-04-schema-drift-and-sync-hardening` — Phase 17+ (sync engine 错误分类前端)
- `fix-rag-transform-and-episode-isolation` — Phase 5+ (BKT-driven common_mistakes 已完成)
- `review-enrichment-signal-fix` — Phase 1 partial (G-SILENT-001 待修)
- `fr-kg-04-isolation-and-retrieval-tightening`
- `fr-kg-04-prompt-injection-and-auth-completion`
- `fr-kg-04-sync-pipeline-fix`
- `fr-kg-05-recommendation-mvp` (legacy CLI debt)
- `agentic-rag-l1-llm-router`
- `fix-structlog-caplog-compat`
- `trackpad-pan-support`

### 唯一待修 known-gotcha
- **G-SILENT-001** endpoint wiring：`backend/app/api/v1/endpoints/review.py:788` `generate_verification_canvas` 需内联 enrichment_available

### 已修复统计（2026-04-07 截止）
- known-gotchas: 37 总 / 32 已修 / 4 保留 / 1 待修
- Phase 1-5 fix-rag-faithfulness 测试覆盖：88 个全绿
- real Neo4j 集成测试: 86 个

## 历史活跃计划（已完成或停滞，留作参考）

### 历史 Phase 1 — MagicMock → 真实数据库测试
- [x] Step 0: docker-compose 添加 neo4j-test 容器（端口 7692）— commit 3a167e9
- [x] Step 1: conftest.py 修复端口 + neo4j_available + neo4j_test_session — commit 3a167e9
- [x] Step 2: DD-03 hard hook (mock-import-guard.js) — commit 0cb8cf8
- Step 3-5: 大部分由 fix-fr-kg-04 系列 PR 吸收实施

## 后续 Phases（不在当前范围）
- Phase 2: 修复 6 条断裂管道（G-PIPE）
- Phase 3: 功能质量提升（假评分→真 LLM、异常精确化）
- Phase 4: 产品记忆 KA-RAG 接通
