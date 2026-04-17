---
active_plan: "OBSIDIAN-QA-ROUND11-2026-04-16"
active_plan_file: "/Users/Heishing/.claude/plans/squishy-purring-hoare.md"
prd_sections: ["Q1-Q8 整体推荐矩阵", "BKT/MCP 认证/Exam/FSRS 实施", "Claude Code 压缩算法", "ZOMBIE 归档执行", "Graphiti 部署适配 Obsidian"]
current_step: "Round 11 补答完成（3 个 R11-Q section：R11-Q1 vault 父目录挂载方案 + R11-Q2 MCP 4 证据链 + R11-Q3 ChatGPT 对抗性审查 prompt；Round 10 4 处 [A12] 追加；全量 git push 完成）等待 ChatGPT Deep Research 审计结果 → Round 12 回应"
plan_kind: "bmad-planning"
active_phase: "obsidian-scheme-v2-qa-round11-answered"
round: 11
last_updated: "2026-04-16T05:00:00Z"
round10_key_finding: "推荐选项 1 用户手动 docker-compose up + Obsidian Plugin 健康检查（0 代码，符合 Smart Connections/Khoj/Copilot 社区主流）+ 可选选项 2 Claudian MCP tool check_backend_health 自动协调（~50 行 Python）。关键证据：tauri.conf.json 无 sidecar 配置（Tauri 原本也未自动启动），Electron 沙箱禁止 Plugin spawn subprocess，Claudian 是唯一合法自动启动通道"
round9_key_finding: "推荐保留 Graphiti 做错误/学习事件检索 — 时序+关系查询天然匹配 Episode 模型；数据量小（20-50MB）；启动 Docker 2 分钟；Zep AI 社区源码 https://github.com/getzep/graphiti"
round8_key_findings:
  - "LanceDB 6 张表（非仅 canvas_nodes）— vault_notes 就是用户期待的笔记分块检索，R7-Q2 严重遗漏"
  - "Graphiti 4 个读端触发点（retrieve_graphiti / search_memories 3 层融合），R7-Q3 只审了写端"
  - "3 套检索系统: Graphiti + LanceDB + Neo4j Tier-2 全文备用，R7-Q3 遗漏第 3 套"
  - "LanceDB vs Graphiti 分工矩阵（6 场景）基于代码实读，非凭记忆"
round7_key_findings:
  - "Bash 实证: Graphiti 当前未连接（所有 Neo4j 端口 closed）— IQ-1 答 B"
  - "LanceDB 实际存 Canvas 节点对象，非笔记片段（纠正用户假设）"
  - "社区无向量存储熟练度专门方案，推荐 Obsidian frontmatter + Dataview"
  - "Graphiti 存学习事件（对话内容），不存 md 节点内容"
next_round_trigger: "用户粘回 ChatGPT Deep Research 对抗性审计结果 → Round 12 回应（修改方案 / 补充证据 / 关闭决策 D1-D5）"
commit_rule: "文档 commit 必须包含 PLAN-OBSIDIAN-QA-ROUND11-2026-04-16"
round11_main_file: "[[obsidian-qa-round11-claude-answers-2026-04-16]]"
round10_main_file: "[[obsidian-qa-round10-claude-answers-2026-04-16]]"
round9_main_file: "[[obsidian-qa-round9-claude-answers-2026-04-15]]"
round8_main_file: "[[obsidian-qa-round8-claude-answers-2026-04-15]]"
round7_main_file: "[[obsidian-qa-round7-claude-answers-2026-04-15]]"
round6_main_file: "[[obsidian-qa-round6-claude-answers-2026-04-15]]"
round5_main_file: "[[obsidian-qa-round5-claude-answers-2026-04-15]]"
round4_main_file: "[[obsidian-qa-round4-claude-answers-2026-04-14]]"
round3_main_file: "[[obsidian-qa-round3-claude-answers-2026-04-14]]"
round2_main_file: "[[obsidian-qa-round2-claude-answers-2026-04-14]]"
original_qa_file: "[[obsidian-translation-qa-2026-04-14]]"
round4_character: "从 UX 翻译升级到后端硬核审计 + 增量提问（非直出方案）"
round5_character: "决策 Close-out + 非技术用户通俗化 + Claude Code 压缩算法调研"
round4_agents:
  - "Agent X: 后端功能降级利用率（28 ALIVE / 3 ZOMBIE / 精简 4）"
  - "Agent Y: 检验白板 15 步 + Hot/Warm/Cold 三存储双触发链"
  - "Agent Z: 四路搜索三级分类（L1❌/L2✅/L3🟡/L4🔴）"
round5_agents:
  - "Agent A: Claude Code /compact + 5 方案 SOTA 对比（KVzip/LLMLingua/ACON/RMT/MemGPT）"
  - "Agent B: Q1-Q8 实施方案 + alert_manager 纠正（ACTIVE）+ 3 ZOMBIE 归档脚本"
  - "Agent C: Q4/Q7/Q10 通俗化（账本-图书馆-日记 / 搬家 / 快递驿站登记本）"
integrity_rules_latest: "IC-8（Round 5 新增）— 通俗解释必须具体日常类比 + 外部算法必须 arxiv/官方 URL + 选项答复必须展开实施方案"
evidence_sources_used:
  - "backend/app/services/ 全目录扫描（40+ 文件）"
  - "backend/app/mcp/tools/（MCP 工具集）"
  - "docker-compose.yml + backend/Dockerfile"
  - "docs/known-gotchas.md（32/37 已修，86%）"
  - "backend/tests/（13 检索文件 / 207 test 函数）"
  - "_bmad-output/planning-artifacts/recovered/prd-tauri-original-2ae5897.md"
  - "openspec/specs/agentic-rag + archive"
round3_corrections_count: 7
round3_r3_sections: 18
round4_r4_sections: 4
round4_incremental_questions: 8
round5_r5_sections: 10
round5_user_annotations: 10
round5_key_correction: "alert_manager.py 被 Round 4 误判为 ZOMBIE；Agent B 复核实际 ACTIVE（9 调用方）；真 ZOMBIE 是 fallback_sync_service + extraction_validator + react_agent（2039 行）"
deprecated_docs:
  - "[[canvas-crossdiscipline-tags-v1]]"
  - "[[canvas-index-md-spec-v1]]"
previous_plans:
  - "DASHBOARD-UI-DECISION-v1 (closed 2026-04-13)"
  - "STORY-1-3-PARADIGM-SHIFT-v1 (closed 2026-04-13 commit beb93d0)"
  - "OBSIDIAN-QA-ROUND2-2026-04-14 (closed 2026-04-14, 5 处偏离 Round 3 已纠正)"
  - "OBSIDIAN-QA-ROUND3-2026-04-14 (closed 2026-04-14, 18 R3-Qn section + 18 [A4] 简答完成)"
  - "OBSIDIAN-QA-ROUND4-2026-04-14 (closed 2026-04-15, 4 R4-Qn section + 4 [A5] 追加 + 8 增量提问)"
next_round_trigger: "用户审计 Round 5 后，可能触发 Round 6：(1) Q4 Mastery Store 明示 A/B/C；(2) Q5 是否接受 Claude 推 A 覆盖用户选 B；(3) 批准 KVzip+ACON 压缩迁移；(4) 批准 ZOMBIE 归档脚本执行"
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
