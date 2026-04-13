---
active_plan: "BMAD-V6-WORKFLOW-ENHANCE"
active_plan_file: ""
prd_sections: []
current_step: "BMAD-V6-WORKFLOW-ENHANCE 全部 5 步完成（第二轮批注回应 + FSRS 后端驱动）"
plan_kind: "bmad-implementation"
active_phase: "workflow-enhance-done"
last_updated: "2026-04-13T12:00:00Z"
commit_rule: "代码 commit 必须包含 PLAN-NNN 或 FR-XXX-NN"
---

# CURRENT_TASK — 当前任务状态（唯一真相源）

> 每个 session 启动时自动注入此文件。frontmatter 包含 Plan 锚定，正文包含进度详情。
> 完成一步后立即更新对应的 checkbox。

## 活跃计划（2026-04-07 更新 — Stage 1+2 已 commit + Trivial Sweep 完成 → 等待下一中型任务）

### 已闭合 OpenSpec Changes（archived 2026-04-07）
- [x] **fix-rag-faithfulness-and-add-crag-quality-loop**
  - 3 个新 contract 合并进 `openspec/specs/algo-rag/spec.md`（Faithfulness/Fusion/CRAG）
  - 88/88 测试绿（85 baseline + 3 surrogate）
- [x] **fix-rag-transform-and-episode-isolation**
  - 4 个新 algo-memory + 3 个新 algo-rag requirements 合并进主 spec
  - 64/69 tasks（5 deferred 手动 e2e/压测/doc-review）
  - 17 个新单元测试通过，零回归
- [x] **fix-fr-kg-04-schema-drift-and-sync-hardening**
  - 25 个新 requirements 合并进 5 个新主 spec：algo-question(5) / algo-scoring(1) / canvas-sync(12) / llm-safety(5) / verification-service(2)
  - 127/160 tasks（33 deferred 手动 e2e/前端 smoke）
  - 同批 `git rm -r openspec/changes/fr-kg-04-sync-pipeline-fix/`（SUPERSEDED）
- [x] **fix-structlog-caplog-compat**
  - 6 个新 requirements 合并进新主 spec backend-logging
  - structlog ↔ stdlib 双向 bridge 落地，消除 196 个测试失败/error
- [x] **fr-kg-04-isolation-and-retrieval-tightening**（commit e6971d7）
  - 4 reqs added to algo-rag + 1 req to new repo-compliance capability
  - FR-KG-04 读端闭环：Cypher group_id 隔离 + cache key + cross_canvas fail-soft + vault_notes 多 vault + LICENSE 合规
  - 41/43 tasks（2 deferred docs/smoke）
- [x] **fr-kg-04-prompt-injection-and-auth-completion**（commit e6971d7）
  - 3 reqs added to llm-safety
  - LLM 安全闭环：API key 鉴权扩展 + context 降权 + meta 规则 + 50 case 对抗性测试
  - 37/39 tasks（2 deferred commit/PR），6 LLM 安全风险全闭环
- [x] **agentic-rag-l1-llm-router**（commit e6971d7）
  - 创建新 capability agentic-rag（3 reqs）
  - L1 路由 LLM 化：rule-based → Gemini Flash
  - 45/52 tasks（7 deferred 手动 GEMINI_API_KEY 验证）
  - 核心代码已在 commit 3b96e49 落地
  - Archive 时修正 delta header bug：`## MODIFIED → ## ADDED Requirements`

### 仍进行中的 OpenSpec Changes（仅 2 个）
- `review-enrichment-signal-fix` — 3/4 artifacts（缺 design.md），endpoint wiring 是死代码路径需独立 follow-up change
- `trackpad-pan-support` — 3/4 artifacts，specs/ 缺 delta 定义（OpenSpec validation fail），需补 delta

### 唯一待修 known-gotcha
- **G-SILENT-001** endpoint wiring：`backend/app/api/v1/endpoints/review.py:788` `generate_verification_canvas` 需内联 enrichment_available

### 已修复统计（2026-04-07 截止）
- 本 session 累计 commits：51f2057（structlog bridge）+ 0b477f0（archive 3）+ 74a09f3（spec consolidation）+ b50a089/19a111e/221d8a7（test/docs/gitignore）+ e6971d7（archive 3 ready changes）
- 主 spec capabilities：5 → 14（+9 个新 capability：algo-memory / algo-question / algo-scoring / canvas-sync / llm-safety / verification-service / backend-logging / agentic-rag / repo-compliance）
- 测试基线（Stage 2 完成时）：137 failed / 17 errors / 2471 passed（vs pre 202F/87E/2410P，净 +196 改善）
- known-gotchas: 37 总 / 32 已修 / 4 保留 / 1 待修

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
